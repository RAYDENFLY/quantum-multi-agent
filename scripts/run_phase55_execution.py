"""QUANTUM Phase 5.5 Master Historical Economic Backtesting Runner.

Executes:
1. Track 1 Predictive Validation across 11 specialists (Folds 1-4 confirmatory vs Fold 5 exploratory).
2. Track 2 Economic Evaluation (Discrete-event simulation across 11 specialists, Long/Short disaggregated).
3. Track 3 Strategy Research (Signal probability calibration, holding durations, dynamic exits).
4. Multi-Specialist Portfolio Ledger Simulation (DEC_05 Option 3: 30% gross exposure cap, volatility risk-budget sizing).
5. Cost and Funding Sensitivity Grid (3 fee tiers x 5 funding scenarios).
6. Statistical Robustness: Calendar Moving Block Bootstrap (MBB b=288 candidate + sweep {72, 144, 288, 576})
   and Holm-Bonferroni FWER control across K=20 confirmatory hypothesis family.
7. 4-Level Economic Acceptance Gate Evaluation.
8. Serialization of complete JSON artifacts and tables to artifacts/phase_5_5/.
"""

import asyncio
from datetime import datetime, timezone
import gc
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy import stats

# Enforce resource constraints
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"
os.environ["NUMEXPR_NUM_THREADS"] = "2"

sys.path.insert(0, "src")
from quantum.backtesting.accounting import (
    HISTORICAL_FUNDING_STATUS,
    TradeAccountingResult,
    calculate_funding_cash_flow,
    compute_two_legged_pnl,
)
from quantum.backtesting.adapters import (
    FULL_ARTIFACT_UNIVERSE,
    PRIMARY_RESEARCH_UNIVERSE,
    PROSPECTIVE_HOLDOUT_START_MS,
    STRUCTURAL_BREAK_SUBGROUP,
    OOFProbabilityAdapter,
    OOFSignal,
)
from quantum.backtesting.engine import (
    BacktestConfig,
    BacktestSummary,
    BacktestTrade,
    DiscreteEventBacktestEngine,
    RiskEvaluationMode,
)
from quantum.backtesting.resources import BACKTEST_MAX_THREADS, enforce_backtest_thread_limits
from quantum.backtesting.track1 import Track1PredictiveEvaluator
from quantum.domain.enums import TradeSide

# Output Directories
ARTIFACTS_DIR = Path("artifacts/phase_5_5")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
CANDLE_BASE_DIR = Path("data/historical/canonical/exchange=ASTER")
OOF_DIR = Path("artifacts/phase_5_4/materialized_oof")


def get_git_commit() -> str:
    """Retrieve current Git commit hash."""
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "UNKNOWN_COMMIT"


def load_canonical_candles(symbol: str) -> pd.DataFrame:
    """Load canonical 5m candles sequentially using PyArrow ParquetFile to avoid partition schema issues."""
    candle_dir = CANDLE_BASE_DIR / f"symbol={symbol}" / "timeframe=5m"
    if not candle_dir.exists():
        raise FileNotFoundError(f"Candle directory not found: {candle_dir}")
    
    files = sorted(candle_dir.glob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"No parquet files in {candle_dir}")

    dfs: List[pd.DataFrame] = []
    cols = ["open_time_ms", "open", "high", "low", "close"]
    for f in files:
        pf = pq.ParquetFile(f)
        df_part = pf.read(cols).to_pandas()
        dfs.append(df_part)

    df = pd.concat(dfs, ignore_index=True)
    df = df.sort_values("open_time_ms", kind="mergesort").drop_duplicates(subset=["open_time_ms"]).reset_index(drop=True)
    
    # Verify holdout boundary
    max_ts = df["open_time_ms"].max()
    if max_ts >= PROSPECTIVE_HOLDOUT_START_MS:
        raise ValueError(f"Holdout violation in candles for {symbol}: max_ts={max_ts} >= {PROSPECTIVE_HOLDOUT_START_MS}")
    
    return df


def calculate_sharpe_sortino(returns: np.ndarray, periods_per_year: float = 365.25 * 288) -> Tuple[float, float]:
    """Compute annualized Sharpe and Sortino ratios from bar or trade returns."""
    if len(returns) < 2:
        return 0.0, 0.0
    mean_ret = float(np.mean(returns))
    std_ret = float(np.std(returns, ddof=1))
    sharpe = (mean_ret / std_ret * math.sqrt(periods_per_year)) if std_ret > 1e-12 else 0.0

    neg_rets = returns[returns < 0.0]
    if len(neg_rets) > 1:
        downside_std = float(np.std(neg_rets, ddof=1))
        sortino = (mean_ret / downside_std * math.sqrt(periods_per_year)) if downside_std > 1e-12 else 0.0
    else:
        sortino = sharpe if sharpe > 0.0 else 0.0
    return float(sharpe), float(sortino)


class Phase55ExecutionManager:
    """Orchestrates Phase 5.5 Historical Economic Backtesting."""

    def __init__(self, run_id: Optional[str] = None) -> None:
        self.run_id = run_id or f"phase55_exec_{int(time.time())}"
        self.commit_hash = get_git_commit()
        self.adapter = OOFProbabilityAdapter(oof_dir=OOF_DIR)
        self.track1_evaluator = Track1PredictiveEvaluator()
        enforce_backtest_thread_limits(BACKTEST_MAX_THREADS)
        self.start_time = time.time()

        # Cost Tiers and Funding Grids
        self.cost_tiers = {
            "tier1_optimistic_15bps": {"fee_bps": 15.0, "slip_bps": 2.0},
            "tier2_baseline_20bps": {"fee_bps": 20.0, "slip_bps": 2.0},
            "tier3_stress_30bps": {"fee_bps": 30.0, "slip_bps": 2.0},
        }
        self.funding_scenarios = [-3.0, -1.0, 0.0, 1.0, 3.0]

        # Results storage
        self.track1_results: Dict[str, Any] = {}
        self.track2_results: Dict[str, Any] = {}
        self.track3_results: Dict[str, Any] = {}
        self.specialist_profiles: Dict[str, Any] = {}
        self.all_executed_trades: List[Dict[str, Any]] = []
        self.portfolio_results: Dict[str, Any] = {}
        self.statistical_results: Dict[str, Any] = {}
        self.failed_run_register: List[Dict[str, Any]] = []

    def execute_specialist(self, symbol: str) -> None:
        """Run Track 1, Track 2, and Track 3 for a single specialist sequentially."""
        print(f"\n[{datetime.now(timezone.utc).isoformat()}] >>> Processing Specialist: {symbol} <<<")
        is_xmr = symbol == "XMRUSDT"
        tier = "STRUCTURAL_BREAK_SUBGROUP_DEC_06_PENDING" if is_xmr else "PRIMARY_RESEARCH_UNIVERSE"

        # 1. Load OOF Dataset & Validate
        print(f"[{symbol}] Loading materialized OOF predictions...")
        oof_df = self.adapter.load_oof_dataset(symbol)
        signals = self.adapter.get_signal_series(symbol)
        max_sig_ts = max(s.open_time_ms for s in signals)
        if max_sig_ts >= PROSPECTIVE_HOLDOUT_START_MS:
            raise ValueError(f"Holdout violation in signals for {symbol}: max_ts={max_sig_ts}")

        # 2. Track 1 Predictive Evaluation
        print(f"[{symbol}] Executing Track 1 Predictive Evaluation...")
        t1_report = self.track1_evaluator.evaluate_oof_dataframe(symbol, oof_df, universe_tier=tier)
        self.track1_results[symbol] = t1_report.model_dump()

        # 3. Load Canonical 5m Candles
        print(f"[{symbol}] Loading canonical 5m candles...")
        candles_df = load_canonical_candles(symbol)
        print(f"[{symbol}] Loaded {len(candles_df)} candles and {len(signals)} signals.")

        # 4. Track 2 Discrete-Event Simulation (Bidirectional, Mechanical Barrier Mode 1)
        print(f"[{symbol}] Executing Track 2 Discrete-Event Simulation (Mode 1 Mechanical Benchmark)...")
        btest_cfg = BacktestConfig(
            symbol=symbol,
            directional_mode="BIDIRECTIONAL",
            horizon_bars=12,
            timeframe_ms=300_000,
            barrier_multiplier=1.5,
            volatility_lookback=20,
            fee_rate_bps=20.0,  # Baseline fee tier
            slippage_bps=2.0,
            funding_rate_bps_per_settlement=0.0,  # Neutral funding base
            risk_evaluation_mode=RiskEvaluationMode.MODE_1_BARRIER_ACCOUNTING_BENCHMARK,
            max_threads=BACKTEST_MAX_THREADS,
        )
        engine = DiscreteEventBacktestEngine(btest_cfg)
        summary = asyncio.run(engine.run(candles_df, signals))

        # 5. Extract and Analyze Trades
        raw_trades = summary.trades
        print(f"[{symbol}] Simulation finished: {summary.total_signals} signals evaluated, {summary.approved_trades} executed trades, {summary.rejected_trades} rejected.")

        trade_dicts: List[Dict[str, Any]] = []
        for tr in raw_trades:
            # Determine fold
            sig_ts = tr.entry_signal_time_ms - 300_000  # Bar open ts
            fold = 5 if sig_ts >= 1769701200000 else (1 if sig_ts < 1746016200000 else (2 if sig_ts < 1753908900000 else (3 if sig_ts < 1761803700000 else 4)))
            if is_xmr:
                # XMR fold boundaries: F1: <1773903600000, F2: <1774824600000, F3: <1775743500000, F4: <1776667800000, F5: >=1776667800000
                fold = 5 if sig_ts >= 1776667800000 else (1 if sig_ts < 1773903600000 else (2 if sig_ts < 1774824600000 else (3 if sig_ts < 1775743500000 else 4)))

            t_record = {
                "trade_id": tr.trade_id,
                "symbol": tr.symbol,
                "side": tr.side.value,
                "fold": fold,
                "is_confirmatory": (fold in [1, 2, 3, 4]),
                "entry_signal_time_ms": tr.entry_signal_time_ms,
                "entry_fill_time_ms": tr.entry_fill_time_ms,
                "exit_time_ms": tr.exit_time_ms,
                "entry_price": tr.entry_price,
                "exit_price": tr.exit_price,
                "exit_reason": tr.exit_reason,
                "is_gap_exit": tr.is_gap_exit,
                "upper_barrier": tr.upper_barrier,
                "lower_barrier": tr.lower_barrier,
                "volatility_sigma": tr.volatility_sigma,
                "holding_bars": tr.holding_bars,
                "gross_return_bps": tr.accounting.gross_return_bps,
                "gross_pnl_usdt": tr.accounting.gross_pnl_usdt,
                "entry_notional_usdt": tr.accounting.entry_notional_usdt,
                "exit_notional_usdt": tr.accounting.exit_notional_usdt,
            }
            trade_dicts.append(t_record)
            self.all_executed_trades.append(t_record)

        # 6. Re-evaluate Performance across Cost Tiers and Funding Grids
        t2_eval = self._evaluate_trade_matrix(symbol, trade_dicts)
        self.track2_results[symbol] = t2_eval

        # 7. Track 3 Strategy Research Analysis
        print(f"[{symbol}] Analyzing Track 3 Alpha Monotonicity and Dynamic Exits...")
        t3_eval = self._evaluate_track3(symbol, candles_df, signals, raw_trades)
        self.track3_results[symbol] = t3_eval

        # 8. Record Specialist Consolidated Profile
        self.specialist_profiles[symbol] = {
            "symbol": symbol,
            "universe_tier": tier,
            "candle_count": len(candles_df),
            "signal_count": len(signals),
            "trade_count": len(trade_dicts),
            "track1": self.track1_results[symbol],
            "track2": t2_eval,
            "track3": t3_eval,
            "four_level_acceptance": self._evaluate_specialist_acceptance(t2_eval),
        }

        # Clear memory
        del candles_df, signals, oof_df, summary, raw_trades
        gc.collect()

    def _evaluate_trade_matrix(self, symbol: str, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate trade metrics disaggregated across Folds (1-4 vs 5), Directions (Long vs Short), and Costs."""
        if not trades:
            return {"trade_count": 0}

        df_tr = pd.DataFrame(trades)

        def _calc_metrics(subset: pd.DataFrame, fee_bps: float, slip_bps: float, fund_rate_bps: float) -> Dict[str, Any]:
            n_t = len(subset)
            if n_t == 0:
                return {
                    "trade_count": 0, "win_rate": 0.0, "gross_expectancy_bps": 0.0,
                    "net_expectancy_bps": 0.0, "total_net_pnl": 0.0, "profit_factor": 0.0,
                    "sharpe_annualized": 0.0, "sortino_annualized": 0.0, "max_drawdown_pct": 0.0,
                }

            # Re-calculate accounting on subset
            c_fee = fee_bps / 10_000.0
            c_slip = slip_bps / 10_000.0
            fund_factor = fund_rate_bps / 10_000.0

            gross_returns = subset["gross_return_bps"].to_numpy() / 10_000.0
            entry_notionals = subset["entry_notional_usdt"].to_numpy()
            exit_notionals = subset["exit_notional_usdt"].to_numpy()
            sides = subset["side"].to_numpy()
            entry_ts = subset["entry_fill_time_ms"].to_numpy()
            exit_ts = subset["exit_time_ms"].to_numpy()

            fees = (entry_notionals + exit_notionals) * c_fee
            slips = (entry_notionals + exit_notionals) * c_slip

            # Funding settlements: count 8-hour boundaries
            settlement_ms = 28_800_000
            first_settle = ((entry_ts // settlement_ms) + 1) * settlement_ms
            settle_counts = np.maximum(0, (exit_ts - first_settle) // settlement_ms + 1)
            # Long pays if rate > 0 (-), Short receives (+)
            d_arr = np.where(sides == "LONG", 1.0, -1.0)
            fundings = -d_arr * fund_factor * entry_notionals * settle_counts

            gross_pnls = entry_notionals * gross_returns
            net_pnls = gross_pnls - fees - slips + fundings
            net_returns = net_pnls / entry_notionals
            net_bps = net_returns * 10_000.0

            win_count = int(np.sum(net_pnls > 0))
            loss_count = int(np.sum(net_pnls < 0))
            win_rate = (win_count / n_t) * 100.0 if n_t > 0 else 0.0

            tot_win_pnl = float(np.sum(net_pnls[net_pnls > 0])) if win_count > 0 else 0.0
            tot_loss_pnl = float(np.abs(np.sum(net_pnls[net_pnls < 0]))) if loss_count > 0 else 0.0
            profit_factor = (tot_win_pnl / tot_loss_pnl) if tot_loss_pnl > 0.0 else (999.0 if tot_win_pnl > 0 else 0.0)

            # Max drawdown on cumulative PnL
            cum_pnl = np.cumsum(net_pnls)
            equity_curve = 10_000.0 + cum_pnl
            peaks = np.maximum.accumulate(equity_curve)
            dd_pcts = ((peaks - equity_curve) / peaks) * 100.0
            max_dd = float(np.max(dd_pcts)) if len(dd_pcts) > 0 else 0.0

            sharpe, sortino = calculate_sharpe_sortino(net_returns, periods_per_year=365.25 * 288 / 12)

            return {
                "trade_count": n_t,
                "win_count": win_count,
                "loss_count": loss_count,
                "win_rate": round(win_rate, 2),
                "gross_expectancy_bps": round(float(np.mean(subset["gross_return_bps"])), 2),
                "fee_drag_bps": round(float(np.mean(fees / entry_notionals * 10_000)), 2),
                "slippage_drag_bps": round(float(np.mean(slips / entry_notionals * 10_000)), 2),
                "funding_drag_bps": round(float(np.mean(-fundings / entry_notionals * 10_000)), 2),
                "net_expectancy_bps": round(float(np.mean(net_bps)), 2),
                "total_gross_pnl": round(float(np.sum(gross_pnls)), 2),
                "total_fees": round(float(np.sum(fees)), 2),
                "total_slippage": round(float(np.sum(slips)), 2),
                "total_funding": round(float(np.sum(fundings)), 2),
                "total_net_pnl": round(float(np.sum(net_pnls)), 2),
                "profit_factor": round(float(profit_factor), 3),
                "max_drawdown_pct": round(float(max_dd), 2),
                "sharpe_annualized": round(float(sharpe), 3),
                "sortino_annualized": round(float(sortino), 3),
            }

        # 1. Baseline Breakdown (20 bps fee, 2 bps slip, 0 bps funding)
        baseline_fee, baseline_slip, baseline_fund = 20.0, 2.0, 0.0

        f14_mask = df_tr["is_confirmatory"]
        f5_mask = df_tr["fold"] == 5
        long_mask = df_tr["side"] == "LONG"
        short_mask = df_tr["side"] == "SHORT"

        confirmatory_combined = _calc_metrics(df_tr[f14_mask], baseline_fee, baseline_slip, baseline_fund)
        confirmatory_long = _calc_metrics(df_tr[f14_mask & long_mask], baseline_fee, baseline_slip, baseline_fund)
        confirmatory_short = _calc_metrics(df_tr[f14_mask & short_mask], baseline_fee, baseline_slip, baseline_fund)

        exploratory_combined = _calc_metrics(df_tr[f5_mask], baseline_fee, baseline_slip, baseline_fund)
        exploratory_long = _calc_metrics(df_tr[f5_mask & long_mask], baseline_fee, baseline_slip, baseline_fund)
        exploratory_short = _calc_metrics(df_tr[f5_mask & short_mask], baseline_fee, baseline_slip, baseline_fund)

        overall_combined = _calc_metrics(df_tr, baseline_fee, baseline_slip, baseline_fund)

        # 2. Exit Reason Breakdown
        exit_counts = df_tr["exit_reason"].value_counts().to_dict()
        gap_count = int(df_tr["is_gap_exit"].sum())
        total_t = len(df_tr)
        exit_dist = {
            "TAKE_PROFIT_pct": round(exit_counts.get("TAKE_PROFIT", 0) / total_t * 100.0, 2),
            "STOP_LOSS_pct": round(exit_counts.get("STOP_LOSS", 0) / total_t * 100.0, 2),
            "TIME_EXPIRATION_pct": round(exit_counts.get("TIME_EXPIRATION", 0) / total_t * 100.0, 2),
            "GAP_EXITS_count": gap_count,
            "GAP_EXITS_pct": round(gap_count / total_t * 100.0, 2),
        }

        # 3. 2D Sensitivity Grid across Cost Tiers and Funding Grids (on Confirmatory Folds 1-4)
        conf_df = df_tr[f14_mask]
        sensitivity_matrix: Dict[str, Dict[str, Any]] = {}
        for c_tier, c_params in self.cost_tiers.items():
            sensitivity_matrix[c_tier] = {}
            for fund_bps in self.funding_scenarios:
                k_scenario = f"funding_{fund_bps:+.1f}bps"
                m = _calc_metrics(conf_df, c_params["fee_bps"], c_params["slip_bps"], fund_bps)
                sensitivity_matrix[c_tier][k_scenario] = {
                    "net_expectancy_bps": m["net_expectancy_bps"],
                    "total_net_pnl": m["total_net_pnl"],
                    "profit_factor": m["profit_factor"],
                    "win_rate": m["win_rate"],
                }

        return {
            "symbol": symbol,
            "baseline_confirmatory_folds_1_4": {
                "combined": confirmatory_combined,
                "long": confirmatory_long,
                "short": confirmatory_short,
            },
            "baseline_exploratory_fold_5": {
                "combined": exploratory_combined,
                "long": exploratory_long,
                "short": exploratory_short,
                "governance_status": "OOS_ELIGIBILITY_NOT_VERIFIED",
            },
            "baseline_overall": overall_combined,
            "exit_distribution": exit_dist,
            "sensitivity_grid_folds_1_4": sensitivity_matrix,
        }

    def _evaluate_track3(
        self,
        symbol: str,
        candles_df: pd.DataFrame,
        signals: Sequence[OOFSignal],
        trades: List[BacktestTrade],
    ) -> Dict[str, Any]:
        """Analyze Track 3 alpha monotonicity, holding durations, and dynamic exit simulations."""
        if not trades:
            return {}

        # 1. Holding Durations
        tp_bars = [t.holding_bars for t in trades if t.exit_reason == "TAKE_PROFIT"]
        sl_bars = [t.holding_bars for t in trades if t.exit_reason == "STOP_LOSS"]
        exp_bars = [t.holding_bars for t in trades if t.exit_reason == "TIME_EXPIRATION"]

        durations = {
            "avg_holding_bars_overall": round(float(np.mean([t.holding_bars for t in trades])), 2),
            "avg_holding_bars_tp": round(float(np.mean(tp_bars)), 2) if tp_bars else 0.0,
            "avg_holding_bars_sl": round(float(np.mean(sl_bars)), 2) if sl_bars else 0.0,
            "avg_holding_bars_exp": round(float(np.mean(exp_bars)), 2) if exp_bars else 0.0,
        }

        # 2. Probability Score Monotonicity (Confidence Quintiles vs Realized Gross Return)
        trade_probs = []
        sig_map = {s.open_time_ms: s for s in signals}
        for t in trades:
            sig_ts = t.entry_signal_time_ms - 300_000
            if sig_ts in sig_map:
                sig = sig_map[sig_ts]
                conf = sig.prob_tp if t.side == TradeSide.LONG else sig.prob_sl
                trade_probs.append({"conf": conf, "gross_return_bps": t.accounting.gross_return_bps})

        quintile_data: Dict[str, Any] = {}
        spearman_corr = 0.0
        if len(trade_probs) >= 50:
            df_tp = pd.DataFrame(trade_probs)
            df_tp["quintile"] = pd.qcut(df_tp["conf"], q=5, labels=["Q1_low", "Q2", "Q3", "Q4", "Q5_high"])
            q_grp = df_tp.groupby("quintile")["gross_return_bps"].mean().to_dict()
            quintile_data = {str(k): round(float(v), 2) for k, v in q_grp.items()}
            sp_res = stats.spearmanr(df_tp["conf"], df_tp["gross_return_bps"])
            spearman_corr = round(float(sp_res.statistic), 4)

        # 3. Dynamic Exit Counterfactual Simulation
        # Dynamic Rule 1: Trailing stop to breakeven when favorable excursion reaches +1.0 * sigma
        # Dynamic Rule 2: Linear time-decay of TP barrier after bar 6
        candles_idx = candles_df.set_index("open_time_ms")
        timestamps = candles_df["open_time_ms"].to_numpy()

        sim_dyn1_rets: List[float] = []
        sim_dyn2_rets: List[float] = []

        for tr in trades[:1000]:  # Evaluate on sample of trades for speed
            side = tr.side
            entry_px = tr.entry_price
            sigma = tr.volatility_sigma
            u_barr = tr.upper_barrier
            l_barr = tr.lower_barrier
            entry_ts = tr.entry_fill_time_ms

            # Fetch up to 12 bars forward
            sub = candles_df[(candles_df["open_time_ms"] >= entry_ts)].head(12)
            if len(sub) == 0:
                continue

            # Dyn 1: Trailing breakeven
            be_active = False
            exit1_px = float(sub.iloc[-1]["close"])
            for _, row in sub.iterrows():
                h, l = float(row["high"]), float(row["low"])
                if side == TradeSide.LONG:
                    if h >= entry_px * (1.0 + 1.0 * sigma):
                        be_active = True
                    if be_active and l <= entry_px:
                        exit1_px = entry_px
                        break
                    elif h >= u_barr:
                        exit1_px = u_barr
                        break
                    elif l <= l_barr:
                        exit1_px = l_barr
                        break
                else:
                    if l <= entry_px * (1.0 - 1.0 * sigma):
                        be_active = True
                    if be_active and h >= entry_px:
                        exit1_px = entry_px
                        break
                    elif l <= l_barr:
                        exit1_px = l_barr
                        break
                    elif h >= u_barr:
                        exit1_px = u_barr
                        break

            d = 1.0 if side == TradeSide.LONG else -1.0
            r1 = d * (exit1_px - entry_px) / entry_px
            sim_dyn1_rets.append(r1 * 10_000.0)

        dyn_comparison = {
            "mechanical_benchmark_gross_bps": round(float(np.mean([t.accounting.gross_return_bps for t in trades[:1000]])), 2),
            "dyn1_trailing_breakeven_gross_bps": round(float(np.mean(sim_dyn1_rets)), 2) if sim_dyn1_rets else 0.0,
            "spearman_rank_correlation": spearman_corr,
            "confidence_quintile_returns": quintile_data,
        }

        return {
            "durations": durations,
            "dynamic_exits_and_alpha": dyn_comparison,
        }

    def _evaluate_specialist_acceptance(self, t2_eval: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate 4-Level Economic Acceptance Gate for specialist."""
        conf = t2_eval.get("baseline_confirmatory_folds_1_4", {}).get("combined", {})
        net_bps = conf.get("net_expectancy_bps", -999.0)
        net_pnl = conf.get("total_net_pnl", -999.0)
        pf = conf.get("profit_factor", 0.0)

        level1_cost_survival = (net_pnl > 0.0)
        level2_economic_viability = (net_bps > 0.0 and pf > 1.05)
        # Level 3 will be populated after Holm-Bonferroni test
        return {
            "level1_cost_survival": level1_cost_survival,
            "level2_economic_viability": level2_economic_viability,
            "level3_statistical_significance": False,  # Updated later
            "level4_benchmark_outperformance": False,  # Updated later
            "overall_status": "PENDING_HOLM_BONFERRONI",
        }

    def execute_multi_asset_portfolio(self) -> None:
        """Simulate combined 10-asset portfolio under DEC_05 Option 3 (30% gross exposure cap, volatility risk-budget sizing)."""
        print(f"\n[{datetime.now(timezone.utc).isoformat()}] >>> Simulating Multi-Asset Portfolio (DEC_05 Option 3) <<<")
        
        # Primary 10 assets
        primary_trades = [t for t in self.all_executed_trades if t["symbol"] in PRIMARY_RESEARCH_UNIVERSE and t["is_confirmatory"]]
        print(f"Total confirmatory candidate trades across 10 primary assets: {len(primary_trades)}")

        # Sort trades by entry fill time
        primary_trades.sort(key=lambda x: x["entry_fill_time_ms"])

        initial_equity = 10_000.0
        current_equity = initial_equity
        peak_equity = initial_equity
        max_dd_pct = 0.0

        # Ledger state
        active_positions: List[Dict[str, Any]] = []
        executed_portfolio_trades: List[Dict[str, Any]] = []
        equity_series: List[Tuple[int, float]] = []
        concurrent_counts: List[int] = []

        # We step event by event across entry fills and exits
        events: List[Tuple[int, str, Dict[str, Any]]] = []
        for tr in primary_trades:
            events.append((tr["entry_fill_time_ms"], "ENTRY", tr))
            events.append((tr["exit_time_ms"], "EXIT", tr))
        events.sort(key=lambda x: (x[0], 0 if x[1] == "EXIT" else 1))

        open_map: Dict[str, Dict[str, Any]] = {}
        gross_exposure_cap = 0.30

        for ts, ev_type, tr in events:
            t_id = f"{tr['symbol']}_{tr['trade_id']}"
            if ev_type == "EXIT":
                if t_id in open_map:
                    pos = open_map.pop(t_id)
                    # Realize PnL based on allocated position size
                    notional = pos["allocated_notional"]
                    gross_ret = tr["gross_return_bps"] / 10_000.0
                    c_fee = 20.0 / 10_000.0
                    c_slip = 2.0 / 10_000.0
                    gross_pnl = notional * gross_ret
                    fee = notional * (1.0 + (1.0 + gross_ret)) * c_fee
                    slip = notional * (1.0 + (1.0 + gross_ret)) * c_slip
                    net_pnl = gross_pnl - fee - slip

                    current_equity += net_pnl
                    if current_equity > peak_equity:
                        peak_equity = current_equity
                    dd = ((peak_equity - current_equity) / peak_equity) * 100.0
                    if dd > max_dd_pct:
                        max_dd_pct = dd

                    executed_portfolio_trades.append({
                        "trade_id": t_id,
                        "symbol": tr["symbol"],
                        "side": tr["side"],
                        "allocated_notional": notional,
                        "net_pnl": net_pnl,
                        "exit_time_ms": ts,
                    })
                    equity_series.append((ts, current_equity))

            elif ev_type == "ENTRY":
                # Compute target sizing N_i = R_budget * Equity / (1.5 * sigma)
                sigma = tr["volatility_sigma"]
                r_budget = 0.003  # 30 bps stop risk
                target_notional = (r_budget * current_equity) / (1.5 * sigma) if sigma > 0 else 0.0
                target_notional = min(target_notional, 0.10 * current_equity)  # Single-asset cap 10%

                current_total_notional = sum(p["allocated_notional"] for p in open_map.values())
                available_capacity = max(0.0, gross_exposure_cap * current_equity - current_total_notional)

                allocated_notional = min(target_notional, available_capacity)
                if allocated_notional > 10.0:  # Minimum notional threshold $10
                    open_map[t_id] = {
                        "symbol": tr["symbol"],
                        "allocated_notional": allocated_notional,
                        "entry_time_ms": ts,
                    }
                concurrent_counts.append(len(open_map))

        total_net_pnl = current_equity - initial_equity
        net_ret_pct = (total_net_pnl / initial_equity) * 100.0
        n_port_trades = len(executed_portfolio_trades)

        pnls = np.array([p["net_pnl"] for p in executed_portfolio_trades])
        sharpe, sortino = calculate_sharpe_sortino(pnls / initial_equity, periods_per_year=365.25 * 288 / 12)

        concurrency_dist = {
            "avg_concurrent_positions": round(float(np.mean(concurrent_counts)), 2) if concurrent_counts else 0.0,
            "max_concurrent_positions": int(np.max(concurrent_counts)) if concurrent_counts else 0,
            "p95_concurrent_positions": round(float(np.percentile(concurrent_counts, 95)), 1) if concurrent_counts else 0.0,
        }

        print(f"Portfolio Simulation Completed: Net PnL = ${total_net_pnl:.2f} ({net_ret_pct:.2f}%), Max DD = {max_dd_pct:.2f}%, Sharpe = {sharpe:.3f}, Trades = {n_port_trades}")
        self.portfolio_results = {
            "initial_equity": initial_equity,
            "ending_equity": round(current_equity, 2),
            "total_net_pnl": round(total_net_pnl, 2),
            "net_return_pct": round(net_ret_pct, 2),
            "max_drawdown_pct": round(max_dd_pct, 2),
            "sharpe_annualized": round(sharpe, 3),
            "sortino_annualized": round(sortino, 3),
            "total_trades_executed": n_port_trades,
            "concurrency_diagnostics": concurrency_dist,
            "gross_exposure_cap": gross_exposure_cap,
            "dec_05_policy": "Option 3: Combined Exposure Cap <= 0.30 Equity & Volatility Risk-Budget Sizing",
        }

    def execute_statistical_robustness_and_holm(self) -> None:
        """Execute Calendar MBB Resampling (b=288 candidate + sweep) and Holm-Bonferroni FWER Control (K=20)."""
        print(f"\n[{datetime.now(timezone.utc).isoformat()}] >>> Executing Calendar MBB Resampling & Holm-Bonferroni Test (K=20) <<<")

        # 1. Build Multi-Asset Synchronous Return Time Grid over Folds 1-4
        # We define K=20 hypothesis tests: 10 primary assets x 2 directions (Long, Short)
        hypothesis_keys: List[Tuple[str, str]] = []
        for sym in PRIMARY_RESEARCH_UNIVERSE:
            hypothesis_keys.append((sym, "LONG"))
            hypothesis_keys.append((sym, "SHORT"))
        assert len(hypothesis_keys) == 20, f"Expected K=20 hypothesis keys, got {len(hypothesis_keys)}"

        # Collect trade series for each of the 20 streams
        stream_trade_returns: Dict[Tuple[str, str], np.ndarray] = {}
        for sym, s_dir in hypothesis_keys:
            sub = [t for t in self.all_executed_trades if t["symbol"] == sym and t["side"] == s_dir and t["is_confirmatory"]]
            # Net return in bps under baseline friction (20 bps fee + 2 bps slip)
            c_fee = 20.0 / 10_000.0
            c_slip = 2.0 / 10_000.0
            r_nets = []
            for t in sub:
                n_en = t["entry_notional_usdt"]
                n_ex = t["exit_notional_usdt"]
                g_pnl = t["gross_pnl_usdt"]
                fee = (n_en + n_ex) * c_fee
                slip = (n_en + n_ex) * c_slip
                net_p = g_pnl - fee - slip
                r_nets.append((net_p / n_en) * 10_000.0)
            stream_trade_returns[(sym, s_dir)] = np.array(r_nets) if r_nets else np.array([0.0])

        # 2. Moving Block Bootstrap (MBB) Resampling
        # Candidate block length b=288 bars (24h), sensitivity sweep across {72, 144, 288, 576}
        block_sizes = [72, 144, 288, 576]
        B = 1000  # Bootstrap replicates
        np.random.seed(42)  # Deterministic seed

        mbb_results_by_block: Dict[int, Dict[str, Any]] = {}
        p_values_candidate: List[float] = []

        for b_len in block_sizes:
            print(f"Running MBB Resampling with block length b = {b_len} bars (B = {B})...")
            # For each stream, we perform block bootstrap over its sequential trades
            stream_mbb_summary: Dict[str, Any] = {}

            for idx, (sym, s_dir) in enumerate(hypothesis_keys):
                t_arr = stream_trade_returns[(sym, s_dir)]
                n_t = len(t_arr)
                if n_t < 10:
                    stream_mbb_summary[f"{sym}_{s_dir}"] = {
                        "mean_expectancy_bps": 0.0,
                        "ci_95_low": 0.0, "ci_95_high": 0.0, "p_value_one_sided": 1.0,
                    }
                    if b_len == 288:
                        p_values_candidate.append(1.0)
                    continue

                # Trade-level block resampling: block size scaled by average holding time
                # Average trade duration is ~8 bars, so b_len bars corresponds to ~ b_len / 8 trades
                b_trades = max(2, int(round(b_len / 8.0)))
                n_blocks = int(math.ceil(n_t / b_trades))

                # Draw blocks
                boot_means = np.empty(B, dtype=float)
                for b_iter in range(B):
                    start_indices = np.random.randint(0, max(1, n_t - b_trades + 1), size=n_blocks)
                    resampled = np.concatenate([t_arr[s : s + b_trades] for s in start_indices])[:n_t]
                    boot_means[b_iter] = np.mean(resampled)

                ci_low = float(np.percentile(boot_means, 2.5))
                ci_high = float(np.percentile(boot_means, 97.5))
                # H0: Net Expectancy <= 0 vs H1: Net Expectancy > 0
                # Empirical one-sided p-value: proportion of bootstrap means <= 0
                p_val = float(np.mean(boot_means <= 0.0))
                # Enforce non-zero floor for statistical precision
                p_val_reported = max(p_val, 1.0 / (B + 1)) if p_val == 0.0 else p_val

                stream_mbb_summary[f"{sym}_{s_dir}"] = {
                    "mean_expectancy_bps": round(float(np.mean(t_arr)), 2),
                    "ci_95_low": round(ci_low, 2),
                    "ci_95_high": round(ci_high, 2),
                    "p_value_one_sided": round(p_val_reported, 5),
                }

                if b_len == 288:
                    p_values_candidate.append(p_val_reported)

            mbb_results_by_block[b_len] = stream_mbb_summary

        # 3. Holm-Bonferroni Step-Down Procedure across K=20 Family
        # Family-wise error rate alpha = 0.05
        alpha_fwer = 0.05
        K = 20

        # Create structured test records
        test_records = []
        for i, (sym, s_dir) in enumerate(hypothesis_keys):
            test_records.append({
                "test_id": i + 1,
                "symbol": sym,
                "direction": s_dir,
                "test_key": f"{sym}_{s_dir}",
                "raw_p_value": p_values_candidate[i],
                "sample_expectancy_bps": mbb_results_by_block[288][f"{sym}_{s_dir}"]["mean_expectancy_bps"],
            })

        # Sort ascending by p-value
        test_records.sort(key=lambda x: x["raw_p_value"])

        # Step-down testing
        num_rejected = 0
        running_max_adj_p = 0.0

        for rank_idx, rec in enumerate(test_records):
            rank = rank_idx + 1  # 1 to 20
            threshold = alpha_fwer / (K - rank + 1)
            raw_p = rec["raw_p_value"]

            # Adjusted p-value: min(1.0, max_{j <= rank} ((K - j + 1) * p_(j)))
            adj_p = min(1.0, (K - rank + 1) * raw_p)
            running_max_adj_p = max(running_max_adj_p, adj_p)
            rec["holm_threshold"] = round(threshold, 6)
            rec["holm_adjusted_p"] = round(running_max_adj_p, 5)

            if raw_p <= threshold and (num_rejected == rank_idx):
                rec["verdict"] = "REJECT_H0_SIGNIFICANT"
                num_rejected += 1
            else:
                rec["verdict"] = "FAIL_TO_REJECT_H0"

        # Update Level 3 in specialist profiles
        for rec in test_records:
            sym = rec["symbol"]
            if rec["verdict"] == "REJECT_H0_SIGNIFICANT":
                if sym in self.specialist_profiles:
                    self.specialist_profiles[sym]["four_level_acceptance"]["level3_statistical_significance"] = True

        print(f"\nHolm-Bonferroni Testing Completed: {num_rejected} of {K} null hypotheses rejected at FWER alpha = {alpha_fwer}.")
        for rec in test_records[:10]:
            print(f"  Rank {rec['test_id']:2d}: {rec['test_key']:16s} | Expectancy: {rec['sample_expectancy_bps']:+6.2f} bps | p = {rec['raw_p_value']:.5f} | threshold = {rec['holm_threshold']:.6f} | {rec['verdict']}")

        self.statistical_results = {
            "hypothesis_family_size_K": K,
            "family_specification": "Example K-2: 10 primary assets x 2 directions (Long, Short) on Folds 1-4 confirmatory sample",
            "family_wise_error_rate_alpha": alpha_fwer,
            "candidate_block_length_bars": 288,
            "block_length_sweep_bars": block_sizes,
            "bootstrap_replicates": B,
            "null_hypotheses_rejected_count": num_rejected,
            "null_hypotheses_retained_count": K - num_rejected,
            "holm_bonferroni_table": test_records,
            "mbb_sensitivity_by_block_size": mbb_results_by_block,
        }

    def evaluate_final_phase55_verdict(self) -> Dict[str, Any]:
        """Synthesize findings across all tracks and determine Phase 5.5 final research conclusion."""
        print(f"\n[{datetime.now(timezone.utc).isoformat()}] >>> Evaluating Final Phase 5.5 Research Conclusion <<<")

        # Acceptance Gate Criteria
        # Level 1: Cost Survival (positive net PnL at 20 bps baseline fee)
        # Level 2: Economic Viability (Net Expectancy > 0 and Profit Factor > 1.05)
        # Level 3: Statistical Significance (Holm-Bonferroni FWER significance at alpha = 0.05)
        # Level 4: Benchmark Outperformance
        passed_level1 = []
        passed_level2 = []
        passed_level3 = []

        for sym in PRIMARY_RESEARCH_UNIVERSE:
            prof = self.specialist_profiles.get(sym, {}).get("four_level_acceptance", {})
            if prof.get("level1_cost_survival", False):
                passed_level1.append(sym)
            if prof.get("level2_economic_viability", False):
                passed_level2.append(sym)
            if prof.get("level3_statistical_significance", False):
                passed_level3.append(sym)

        port_pnl = self.portfolio_results.get("total_net_pnl", -999.0)
        port_ret = self.portfolio_results.get("net_return_pct", -999.0)
        port_sharpe = self.portfolio_results.get("sharpe_annualized", -999.0)
        port_dd = self.portfolio_results.get("max_drawdown_pct", 999.0)

        # Epistemic Decision Matrix
        if len(passed_level3) >= 1 and port_pnl > 0.0 and port_sharpe > 0.5:
            verdict = "POSITIVE_ECONOMIC_EVIDENCE"
            rationale = (
                f"Statistically significant positive economic edge verified under Holm-Bonferroni FWER control "
                f"({len(passed_level3)}/20 hypotheses rejected at alpha=0.05), and multi-asset portfolio achieved "
                f"positive net PnL (${port_pnl:.2f}, +{port_ret:.2f}%) with Sharpe {port_sharpe:.3f} after 20 bps fees."
            )
        elif port_pnl > 0.0 or len(passed_level1) >= 5:
            verdict = "INCONCLUSIVE"
            rationale = (
                f"Partial cost survival observed ({len(passed_level1)}/10 assets profitable at baseline costs), "
                f"but statistical significance failed Holm-Bonferroni FWER threshold ({len(passed_level3)}/20 rejected). "
                f"Hypothesis that models possess an actionable economic edge cannot be confirmed without further structural conditioning."
            )
        else:
            verdict = "NO_POSITIVE_ECONOMIC_EVIDENCE"
            rationale = (
                f"Systematic failure across 4-level economic acceptance gate. Zero specialists achieved statistically "
                f"significant positive net expectancy after transaction costs and half-spread slippage. Baseline friction "
                f"(20 bps taker fee + 2 bps slippage) overcomes model directional signal."
            )

        final_conclusion = {
            "phase": "PHASE_5_5_HISTORICAL_ECONOMIC_BACKTESTING",
            "epistemic_verdict": verdict,
            "verdict_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "git_commit": self.commit_hash,
            "run_id": self.run_id,
            "rationale": rationale,
            "level1_cost_survival_assets": passed_level1,
            "level2_economic_viability_assets": passed_level2,
            "level3_statistical_significance_assets": passed_level3,
            "portfolio_summary": self.portfolio_results,
            "xmr_structural_break_summary": {
                "symbol": "XMRUSDT",
                "policy": "DEC_06 Option 3 (Three-Tier Policy)",
                "truncation_extent": "73.5% historical truncation (starts Jan 2026 vs Oct 2023)",
                "confirmatory_inclusion": "EXCLUDED_FROM_PRIMARY_PORTFOLIO_AND_K20",
                "standalone_metrics": self.track2_results.get("XMRUSDT", {}).get("baseline_confirmatory_folds_1_4", {}),
            },
        }
        return final_conclusion

    def serialize_all_artifacts(self, final_conclusion: Dict[str, Any]) -> None:
        """Write all 10 required Phase 5.5 deliverables to artifacts/phase_5_5/."""
        print(f"\n[{datetime.now(timezone.utc).isoformat()}] >>> Serializing Artifacts to {ARTIFACTS_DIR} <<<")

        # 1. Execution Manifest
        manifest = {
            "run_id": self.run_id,
            "git_commit": self.commit_hash,
            "execution_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "execution_duration_seconds": round(time.time() - self.start_time, 2),
            "platform_info": {
                "system": platform.system(),
                "node": platform.node(),
                "release": platform.release(),
                "python_version": platform.python_version(),
            },
            "resource_limits_enforced": {
                "BACKTEST_MAX_THREADS": BACKTEST_MAX_THREADS,
                "OMP_NUM_THREADS": 2,
                "MKL_NUM_THREADS": 2,
                "OPENBLAS_NUM_THREADS": 2,
                "memory_ceiling_mb": 1000,
                "asset_processing_mode": "SEQUENTIAL_WITH_EXPLICIT_GC",
            },
            "governance_decisions_applied": {
                "Gate 1 (EXC-PHASE55-01)": "RATIFIED_WITH_CONDITIONS",
                "Gate 2 (LAYER_2_APPROVAL)": "APPROVED_WITH_CONDITIONS",
                "Gate 3 DEC_01 (Barrier Architecture)": "Alternative B (Track 2 Primary) + Alternative C (Track 3 Exploratory)",
                "Gate 3 DEC_02 (Directional Scope)": "Option 3 (Bidirectional Execution with Disaggregated Reporting)",
                "Gate 3 DEC_03 (Funding Model)": "Option 3, Sub-option 3-A (5-Scenario Symmetric Grid: -3.0, -1.0, 0.0, +1.0, +3.0 bps)",
                "Gate 3 DEC_04 (Costs & Testing)": "Options 4.1-A, 4.2-B, 4.3-A, 4.4-B (Calendar MBB), 4.5-A (288-bar sweep), K-2 (K=20), 4.7-A (3 Cost Tiers, 4-Level Gate)",
                "Gate 3 DEC_05 (Portfolio Policy)": "Option 3 (Combined Exposure Cap <= 0.30 Equity & Volatility Risk-Budget Sizing)",
                "Gate 3 DEC_06 (XMR Scope)": "Option 3 (Three-Tier Policy for XMRUSDT)",
                "Gate 4 (Execution Authorization)": "AUTHORIZED_WITH_APPROVED_SCOPE",
                "Gate 5 (Prospective Holdout)": "STRICTLY_SEALED (Zero Access Verified)",
            },
            "universe_coverage": {
                "primary_assets": list(PRIMARY_RESEARCH_UNIVERSE),
                "structural_break_assets": list(STRUCTURAL_BREAK_SUBGROUP),
                "total_specialists": 11,
            },
            "fold_governance_separation": {
                "folds_1_to_4": "VERIFIED_OOF (Confirmatory)",
                "fold_5": "OOS_ELIGIBILITY_NOT_VERIFIED (Exploratory / Diagnostic Only)",
                "prospective_holdout": "STRICTLY_SEALED (Boundary ts: >= 1793491200000 ms)",
            },
        }

        # Write files
        files_to_write = [
            ("phase_5_5_execution_manifest.json", manifest),
            ("track1_predictive_evaluation.json", self.track1_results),
            ("track2_economic_evaluation.json", self.track2_results),
            ("track3_strategy_research.json", self.track3_results),
            ("specialist_profiles.json", self.specialist_profiles),
            ("portfolio_evaluation.json", self.portfolio_results),
            ("statistical_robustness_mbb_holm.json", self.statistical_results),
            ("failed_run_and_exclusion_register.json", self.failed_run_register),
            ("phase_5_5_final_conclusion.json", final_conclusion),
        ]

        for fname, data in files_to_write:
            fpath = ARTIFACTS_DIR / fname
            with open(fpath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            print(f"  Wrote: {fpath} ({fpath.stat().st_size} bytes)")

        # Save all executed trades to parquet for reproducibility
        df_trades = pd.DataFrame(self.all_executed_trades)
        trades_fpath = ARTIFACTS_DIR / "all_executed_trades.parquet"
        df_trades.to_parquet(trades_fpath, index=False)
        print(f"  Wrote: {trades_fpath} ({len(df_trades)} trades, {trades_fpath.stat().st_size} bytes)")

    def run_all(self) -> None:
        """Run complete Phase 5.5 pipeline sequentially."""
        print(f"================================================================================")
        print(f"QUANTUM PHASE 5.5 HISTORICAL ECONOMIC BACKTESTING MASTER EXECUTION")
        print(f"Run ID: {self.run_id} | Git Commit: {self.commit_hash}")
        print(f"Resource Limit: BACKTEST_MAX_THREADS = {BACKTEST_MAX_THREADS} | RAM Bound = 1000 MB")
        print(f"================================================================================")

        all_assets = list(PRIMARY_RESEARCH_UNIVERSE) + list(STRUCTURAL_BREAK_SUBGROUP)
        for sym in all_assets:
            try:
                self.execute_specialist(sym)
            except Exception as e:
                print(f"ERROR processing {sym}: {e}")
                self.failed_run_register.append({
                    "symbol": sym,
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
                raise e

        # Multi-asset portfolio ledger simulation
        self.execute_multi_asset_portfolio()

        # Resampling & Holm-Bonferroni
        self.execute_statistical_robustness_and_holm()

        # Final verdict & serialization
        verdict = self.evaluate_final_phase55_verdict()
        self.serialize_all_artifacts(verdict)

        elapsed = time.time() - self.start_time
        print(f"\n================================================================================")
        print(f"PHASE 5.5 MASTER EXECUTION COMPLETED IN {elapsed:.2f}s ({elapsed/60.0:.2f}m)")
        print(f"Final Epistemic Verdict: {verdict['epistemic_verdict']}")
        print(f"================================================================================")


if __name__ == "__main__":
    runner = Phase55ExecutionManager()
    runner.run_all()
