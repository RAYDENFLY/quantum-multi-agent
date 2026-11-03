"""QUANTUM Phase 5.6 Alpha Overlay Counterfactual & Optimization Runner.

Executes Phase 5.6 execution overlay counterfactual evaluation:
1. Volatility Regime Filter: Sweep 1.5 * sigma_t >= {80, 120, 160, 200} bps.
2. Probability Margin Gate: Sweep max(p_long, p_short) - p_neutral >= {0.10, 0.20, 0.30}.
3. Asymmetric Barrier Grid: TP = 2.5 * sigma_t, SL = 1.0 * sigma_t over a 24-bar (120m) horizon.
4. Fee Tiers: Maker-Passive (8.0 bps round-trip), Hybrid (15.0 bps round-trip), Baseline Taker (44.0 bps round-trip).
5. Multi-Asset Portfolio Ledger Simulation under DEC_05 Option 3 (30% gross exposure cap).
6. Preserves Prospective Holdout (>= 1793491200000 ms) strictly sealed; evaluates Folds 1-4 confirmatory sample.
7. Serializes overlay_validation_report.json to artifacts/phase_5_6/.
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

# Enforce resource constraints
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"
os.environ["NUMEXPR_NUM_THREADS"] = "2"

sys.path.insert(0, "src")
from quantum.backtesting.adapters import (
    PRIMARY_RESEARCH_UNIVERSE,
    PROSPECTIVE_HOLDOUT_START_MS,
    STRUCTURAL_BREAK_SUBGROUP,
)
from quantum.backtesting.resources import BACKTEST_MAX_THREADS, enforce_backtest_thread_limits

# Directories
ARTIFACTS_DIR = Path("artifacts/phase_5_6")
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
CANDLE_BASE_DIR = Path("data/historical/canonical/exchange=ASTER")
OOF_DIR = Path("artifacts/phase_5_4/materialized_oof")


def get_git_commit() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "UNKNOWN_COMMIT"


def load_canonical_candles(symbol: str) -> pd.DataFrame:
    candle_dir = CANDLE_BASE_DIR / f"symbol={symbol}" / "timeframe=5m"
    if not candle_dir.exists():
        raise FileNotFoundError(f"Candle directory not found: {candle_dir}")
    files = sorted(candle_dir.glob("*.parquet"))
    dfs = []
    cols = ["open_time_ms", "open", "high", "low", "close"]
    for f in files:
        pf = pq.ParquetFile(f)
        dfs.append(pf.read(cols).to_pandas())
    df = pd.concat(dfs, ignore_index=True)
    df = df.sort_values("open_time_ms", kind="mergesort").drop_duplicates(subset=["open_time_ms"]).reset_index(drop=True)
    
    if df["open_time_ms"].max() >= PROSPECTIVE_HOLDOUT_START_MS:
        raise ValueError(f"Holdout violation in {symbol}: max_ts >= {PROSPECTIVE_HOLDOUT_START_MS}")
    return df


def calculate_sharpe_sortino(returns: np.ndarray, periods_per_year: float = 365.25 * 288 / 24) -> Tuple[float, float]:
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


class OverlaySimulationEngine:
    """Simulates Asymmetric Barriers with Volatility and Probability Margin Overlays."""

    def __init__(self) -> None:
        enforce_backtest_thread_limits(BACKTEST_MAX_THREADS)
        self.commit_hash = get_git_commit()
        self.vol_thresholds_bps = [80.0, 120.0, 160.0, 200.0]
        self.prob_margins = [0.10, 0.20, 0.30]
        self.tp_multiplier = 2.5
        self.sl_multiplier = 1.0
        self.horizon_bars = 24  # 120 minutes on 5m candles

        self.fee_tiers = {
            "maker_passive": {"round_trip_fee_bps": 8.0, "round_trip_slip_bps": 0.0, "total_round_trip_bps": 8.0},
            "hybrid_tier": {"round_trip_fee_bps": 15.0, "round_trip_slip_bps": 0.0, "total_round_trip_bps": 15.0},
            "baseline_taker": {"round_trip_fee_bps": 40.0, "round_trip_slip_bps": 4.0, "total_round_trip_bps": 44.0},
        }

    def simulate_specialist_overlay(
        self,
        symbol: str,
        df_candles: pd.DataFrame,
        df_oof_f14: pd.DataFrame,
        vol_thresh_bps: float,
        prob_margin: float,
    ) -> List[Dict[str, Any]]:
        """Run single specialist simulation under specific overlay thresholds."""
        ret = df_candles["close"].pct_change()
        vol_series = ret.rolling(20, min_periods=20).std(ddof=1).clip(lower=1e-4).fillna(0.0).to_numpy()

        # Build signal lookup map: open_time_ms -> (p_m1, p_0, p_p1)
        oof_map = {}
        for r in df_oof_f14.itertuples():
            oof_map[r.open_time_ms] = (float(r.raw_prob_m1), float(r.raw_prob_0), float(r.raw_prob_p1))

        c_opens = df_candles["open"].to_numpy(dtype=float)
        c_highs = df_candles["high"].to_numpy(dtype=float)
        c_lows = df_candles["low"].to_numpy(dtype=float)
        c_closes = df_candles["close"].to_numpy(dtype=float)
        c_ts = df_candles["open_time_ms"].to_numpy(dtype=int)
        n = len(df_candles)

        trades: List[Dict[str, Any]] = []
        active = False
        entry_bar = 0
        side = 0
        u_barr = 0.0
        l_barr = 0.0
        entry_px = 0.0
        entry_ts = 0
        sigma_val = 0.0

        vol_floor = vol_thresh_bps / 10_000.0

        for i in range(20, n):
            prev_ts = int(c_ts[i - 1])

            # 1. Check Exit for Active Position
            if active:
                bars_held = (i - entry_bar) + 1
                o, h, l, c = c_opens[i], c_highs[i], c_lows[i], c_closes[i]
                exit_trig = False
                exit_px = 0.0
                reason = ""
                is_gap = False

                # Opening gap on bars i > entry_bar
                if i > entry_bar:
                    if side == 1:
                        if o <= l_barr:
                            exit_px = o; reason = "STOP_LOSS"; is_gap = True; exit_trig = True
                        elif o >= u_barr:
                            exit_px = o; reason = "TAKE_PROFIT"; is_gap = True; exit_trig = True
                    else:
                        if o >= u_barr:
                            exit_px = o; reason = "STOP_LOSS"; is_gap = True; exit_trig = True
                        elif o <= l_barr:
                            exit_px = o; reason = "TAKE_PROFIT"; is_gap = True; exit_trig = True

                # Intrabar touches
                if not exit_trig:
                    upper_touch = (h >= u_barr)
                    lower_touch = (l <= l_barr)
                    if upper_touch and lower_touch:
                        # Conservative SL first
                        exit_px = l_barr if side == 1 else u_barr
                        reason = "STOP_LOSS"
                        exit_trig = True
                    elif (side == 1 and upper_touch) or (side == -1 and lower_touch):
                        exit_px = u_barr if side == 1 else l_barr
                        reason = "TAKE_PROFIT"
                        exit_trig = True
                    elif (side == 1 and lower_touch) or (side == -1 and upper_touch):
                        exit_px = l_barr if side == 1 else u_barr
                        reason = "STOP_LOSS"
                        exit_trig = True
                    elif bars_held >= self.horizon_bars:
                        exit_px = c
                        reason = "TIME_EXPIRATION"
                        exit_trig = True

                if exit_trig:
                    exit_ts = int(c_ts[i]) if is_gap else int(c_ts[i]) + 300_000
                    d = float(side)
                    gross_ret_bps = d * (exit_px - entry_px) / entry_px * 10_000.0
                    trades.append({
                        "symbol": symbol,
                        "side": "LONG" if side == 1 else "SHORT",
                        "entry_time_ms": entry_ts,
                        "exit_time_ms": exit_ts,
                        "entry_price": entry_px,
                        "exit_price": exit_px,
                        "exit_reason": reason,
                        "is_gap": is_gap,
                        "bars_held": bars_held,
                        "volatility_sigma": sigma_val,
                        "gross_return_bps": gross_ret_bps,
                    })
                    active = False

            # 2. Check Entry for Idle Position
            if not active and prev_ts in oof_map:
                pm1, p0, pp1 = oof_map[prev_ts]
                sigma = float(vol_series[i - 1])

                # Overlay Filter 1: Volatility Regime Filter (1.5 * sigma_t >= vol_threshold_bps)
                if 1.5 * sigma >= vol_floor:
                    # Overlay Filter 2: Probability Margin Gate (max(p_long, p_short) - p_neutral >= prob_margin)
                    diff = max(pp1, pm1) - p0
                    if diff >= prob_margin:
                        side = 1 if pp1 > pm1 else -1
                        entry_px = c_opens[i]
                        entry_ts = int(c_ts[i])
                        entry_bar = i
                        sigma_val = sigma

                        # Asymmetric Barriers: TP = 2.5 * sigma, SL = 1.0 * sigma
                        if side == 1:
                            u_barr = entry_px * (1.0 + self.tp_multiplier * sigma)
                            l_barr = entry_px * (1.0 - self.sl_multiplier * sigma)
                        else:
                            u_barr = entry_px * (1.0 + self.sl_multiplier * sigma)
                            l_barr = entry_px * (1.0 - self.tp_multiplier * sigma)
                        active = True

        return trades

    def evaluate_trades(self, trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute performance metrics across fee tiers for a set of trades."""
        n_t = len(trades)
        if n_t == 0:
            return {
                "trade_count": 0, "win_rate": 0.0, "gross_expectancy_bps": 0.0,
                "maker_passive": {"net_expectancy_bps": 0.0, "profit_factor": 0.0, "sharpe": 0.0},
                "hybrid_tier": {"net_expectancy_bps": 0.0, "profit_factor": 0.0, "sharpe": 0.0},
                "baseline_taker": {"net_expectancy_bps": 0.0, "profit_factor": 0.0, "sharpe": 0.0},
            }

        gross_rets = np.array([t["gross_return_bps"] for t in trades], dtype=float)
        mean_gross = float(np.mean(gross_rets))

        tp_count = sum(1 for t in trades if t["exit_reason"] == "TAKE_PROFIT")
        sl_count = sum(1 for t in trades if t["exit_reason"] == "STOP_LOSS")
        exp_count = sum(1 for t in trades if t["exit_reason"] == "TIME_EXPIRATION")

        tier_metrics = {}
        for tier_name, t_cfg in self.fee_tiers.items():
            friction_bps = t_cfg["total_round_trip_bps"]
            net_rets = gross_rets - friction_bps
            mean_net = float(np.mean(net_rets))

            wins = net_rets[net_rets > 0.0]
            losses = np.abs(net_rets[net_rets < 0.0])
            tot_win = float(np.sum(wins)) if len(wins) > 0 else 0.0
            tot_loss = float(np.sum(losses)) if len(losses) > 0 else 0.0
            pf = (tot_win / tot_loss) if tot_loss > 0.0 else (999.0 if tot_win > 0 else 0.0)
            win_rate = (len(wins) / n_t) * 100.0

            sharpe, sortino = calculate_sharpe_sortino(net_rets / 10_000.0)

            tier_metrics[tier_name] = {
                "friction_bps": friction_bps,
                "net_expectancy_bps": round(mean_net, 2),
                "profit_factor": round(pf, 3),
                "win_rate_pct": round(win_rate, 2),
                "sharpe_annualized": round(sharpe, 3),
                "sortino_annualized": round(sortino, 3),
            }

        return {
            "trade_count": n_t,
            "win_rate_gross_pct": round(tp_count / n_t * 100.0, 2),
            "tp_count": tp_count,
            "sl_count": sl_count,
            "exp_count": exp_count,
            "gross_expectancy_bps": round(mean_gross, 2),
            "maker_passive": tier_metrics["maker_passive"],
            "hybrid_tier": tier_metrics["hybrid_tier"],
            "baseline_taker": tier_metrics["baseline_taker"],
        }

    def simulate_multi_asset_portfolio(
        self,
        all_overlay_trades: List[Dict[str, Any]],
        fee_tier_name: str = "maker_passive",
    ) -> Dict[str, Any]:
        """Simulate DEC_05 Option 3 portfolio ledger from filtered trades."""
        if not all_overlay_trades:
            return {"total_trades": 0, "net_pnl": 0.0}

        sorted_trades = sorted(all_overlay_trades, key=lambda x: x["entry_time_ms"])
        friction_bps = self.fee_tiers[fee_tier_name]["total_round_trip_bps"]

        initial_equity = 10_000.0
        current_equity = initial_equity
        peak_equity = initial_equity
        max_dd = 0.0

        events = []
        for tr in sorted_trades:
            events.append((tr["entry_time_ms"], "ENTRY", tr))
            events.append((tr["exit_time_ms"], "EXIT", tr))
        events.sort(key=lambda x: (x[0], 0 if x[1] == "EXIT" else 1))

        open_map = {}
        gross_exposure_cap = 0.30
        executed_port_trades = []
        equity_curve = [(sorted_trades[0]["entry_time_ms"], initial_equity)]
        concurrent_counts = []

        for ts, ev_type, tr in events:
            t_id = f"{tr['symbol']}_{tr['entry_time_ms']}"
            if ev_type == "EXIT":
                if t_id in open_map:
                    pos = open_map.pop(t_id)
                    notional = pos["allocated_notional"]
                    gross_ret = tr["gross_return_bps"] / 10_000.0
                    fric_rate = friction_bps / 10_000.0
                    net_pnl = notional * (gross_ret - fric_rate)

                    current_equity += net_pnl
                    if current_equity > peak_equity:
                        peak_equity = current_equity
                    dd = ((peak_equity - current_equity) / peak_equity) * 100.0 if peak_equity > 0 else 0.0
                    if dd > max_dd:
                        max_dd = dd

                    executed_port_trades.append({
                        "trade_id": t_id,
                        "symbol": tr["symbol"],
                        "side": tr["side"],
                        "allocated_notional": notional,
                        "net_pnl": net_pnl,
                        "exit_time_ms": ts,
                    })
                    equity_curve.append((ts, round(current_equity, 2)))

            elif ev_type == "ENTRY":
                sigma = tr["volatility_sigma"]
                r_budget = 0.005  # 50 bps risk per trade
                target_notional = (r_budget * current_equity) / (1.0 * sigma) if sigma > 0 else 0.0
                target_notional = min(target_notional, 0.10 * current_equity)

                cur_total = sum(p["allocated_notional"] for p in open_map.values())
                capacity = max(0.0, gross_exposure_cap * current_equity - cur_total)
                allocated = min(target_notional, capacity)

                if allocated > 10.0:
                    open_map[t_id] = {
                        "allocated_notional": allocated,
                        "entry_time_ms": ts,
                    }
                concurrent_counts.append(len(open_map))

        total_pnl = current_equity - initial_equity
        ret_pct = (total_pnl / initial_equity) * 100.0
        n_trades = len(executed_port_trades)
        pnls = np.array([p["net_pnl"] for p in executed_port_trades])
        sharpe, sortino = calculate_sharpe_sortino(pnls / initial_equity)

        # Downsample equity curve to 50 points for JSON readability
        step = max(1, len(equity_curve) // 50)
        downsampled_curve = equity_curve[::step]
        if equity_curve[-1] not in downsampled_curve:
            downsampled_curve.append(equity_curve[-1])

        return {
            "fee_tier": fee_tier_name,
            "initial_equity": initial_equity,
            "ending_equity": round(current_equity, 2),
            "total_net_pnl": round(total_pnl, 2),
            "net_return_pct": round(ret_pct, 2),
            "max_drawdown_pct": round(max_dd, 2),
            "sharpe_annualized": round(sharpe, 3),
            "sortino_annualized": round(sortino, 3),
            "total_portfolio_trades": n_trades,
            "avg_concurrency": round(float(np.mean(concurrent_counts)), 2) if concurrent_counts else 0.0,
            "equity_curve": [{"timestamp_ms": ts, "equity_usdt": eq} for ts, eq in downsampled_curve],
        }


def run_phase56_optimization() -> None:
    t_start = time.time()
    print("================================================================================")
    print("QUANTUM PHASE 5.6 ALPHA OVERLAY COUNTERFACTUAL & OPTIMIZATION")
    print("Evaluation Scope: Folds 1-4 Confirmatory Sample | Prospective Holdout Sealed")
    print("================================================================================")

    engine = OverlaySimulationEngine()

    # Preload all candle data and OOF datasets for Folds 1-4
    symbols = list(PRIMARY_RESEARCH_UNIVERSE) + list(STRUCTURAL_BREAK_SUBGROUP)
    candle_store = {}
    oof_store = {}

    print("\nLoading datasets for 11 specialists...")
    for sym in symbols:
        df_c = load_canonical_candles(sym)
        oof = pq.read_table(OOF_DIR / f"{sym}_oof.parquet").to_pandas()
        oof_f14 = oof[oof["fold"].isin([1, 2, 3, 4])].sort_values("open_time_ms").reset_index(drop=True)
        candle_store[sym] = df_c
        oof_store[sym] = oof_f14
        print(f"  {sym:8s}: {len(df_c)} candles, {len(oof_f14)} confirmatory OOF signals")

    # Grid Sweep across 4 Volatility Thresholds x 3 Probability Margins = 12 configurations
    grid_results = {}
    best_config_trades = {}

    print("\nExecuting Grid Optimization across 12 Overlay Configurations...")
    for vol_th in engine.vol_thresholds_bps:
        for p_m in engine.prob_margins:
            cfg_key = f"vol_{int(vol_th)}bps_margin_{int(p_m*100)}pct"
            print(f"\n>>> Running Grid Configuration: {cfg_key} (Vol >= {vol_th} bps, Margin >= {p_m}) <<<")

            all_trades_for_cfg = []
            asset_metrics = {}

            for sym in PRIMARY_RESEARCH_UNIVERSE:
                tr_list = engine.simulate_specialist_overlay(
                    symbol=sym,
                    df_candles=candle_store[sym],
                    df_oof_f14=oof_store[sym],
                    vol_thresh_bps=vol_th,
                    prob_margin=p_m,
                )
                m = engine.evaluate_trades(tr_list)
                asset_metrics[sym] = m
                all_trades_for_cfg.extend(tr_list)

            # Combined across 10 primary assets
            comb_m = engine.evaluate_trades(all_trades_for_cfg)
            print(f"  [Combined 10 Assets] Trades: {comb_m['trade_count']} | Gross Exp: {comb_m['gross_expectancy_bps']:+.2f} bps")
            print(f"    Maker-Passive (8 bps): Net Exp = {comb_m['maker_passive']['net_expectancy_bps']:+.2f} bps | PF = {comb_m['maker_passive']['profit_factor']:.3f} | WinRate = {comb_m['maker_passive']['win_rate_pct']:.1f}%")
            print(f"    Hybrid Tier  (15 bps): Net Exp = {comb_m['hybrid_tier']['net_expectancy_bps']:+.2f} bps | PF = {comb_m['hybrid_tier']['profit_factor']:.3f}")
            print(f"    Baseline Taker(44 bps): Net Exp = {comb_m['baseline_taker']['net_expectancy_bps']:+.2f} bps | PF = {comb_m['baseline_taker']['profit_factor']:.3f}")

            # Simulate Multi-Asset Portfolio under Maker-Passive & Hybrid
            port_maker = engine.simulate_multi_asset_portfolio(all_trades_for_cfg, "maker_passive")
            port_hybrid = engine.simulate_multi_asset_portfolio(all_trades_for_cfg, "hybrid_tier")

            grid_results[cfg_key] = {
                "vol_threshold_bps": vol_th,
                "prob_margin": p_m,
                "combined_primary_metrics": comb_m,
                "per_asset_metrics": asset_metrics,
                "portfolio_maker_passive": port_maker,
                "portfolio_hybrid": port_hybrid,
            }

            best_config_trades[cfg_key] = all_trades_for_cfg

    # Dedicated Evaluation for XMRUSDT under Standalone Tier 2 Policy
    print("\n>>> Evaluating XMRUSDT Standalone Appendix across Grid <<<")
    xmr_grid = {}
    for vol_th in engine.vol_thresholds_bps:
        for p_m in engine.prob_margins:
            cfg_key = f"vol_{int(vol_th)}bps_margin_{int(p_m*100)}pct"
            tr_xmr = engine.simulate_specialist_overlay(
                symbol="XMRUSDT",
                df_candles=candle_store["XMRUSDT"],
                df_oof_f14=oof_store["XMRUSDT"],
                vol_thresh_bps=vol_th,
                prob_margin=p_m,
            )
            xmr_grid[cfg_key] = engine.evaluate_trades(tr_xmr)

    # Identify Optimal Overlay Configuration
    best_key = max(grid_results.keys(), key=lambda k: grid_results[k]["portfolio_maker_passive"]["total_net_pnl"])
    best_cfg = grid_results[best_key]

    print(f"\n================================================================================")
    print(f"OPTIMAL OVERLAY CONFIGURATION IDENTIFIED: {best_key}")
    print(f"  Vol Filter: 1.5 * sigma >= {best_cfg['vol_threshold_bps']} bps")
    print(f"  Prob Margin: max(p_long, p_short) - p_0 >= {best_cfg['prob_margin']}")
    print(f"  Asymmetric Barriers: TP = 2.5 * sigma, SL = 1.0 * sigma, Horizon = 24 bars")
    print(f"  Maker-Passive Net Return: {best_cfg['portfolio_maker_passive']['net_return_pct']:+.2f}% (${best_cfg['portfolio_maker_passive']['total_net_pnl']:+.2f})")
    print(f"  Maker-Passive Sharpe: {best_cfg['portfolio_maker_passive']['sharpe_annualized']:.3f} | Max DD: {best_cfg['portfolio_maker_passive']['max_drawdown_pct']:.2f}%")
    print(f"  Hybrid Tier Net Return: {best_cfg['portfolio_hybrid']['net_return_pct']:+.2f}% (${best_cfg['portfolio_hybrid']['total_net_pnl']:+.2f})")
    print(f"================================================================================")

    # Serialize Consolidated Validation Report
    report = {
        "report_title": "QUANTUM Phase 5.6 Alpha Overlay Counterfactual & Optimization Report",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": engine.commit_hash,
        "runtime_seconds": round(time.time() - t_start, 2),
        "target_universe": list(PRIMARY_RESEARCH_UNIVERSE),
        "standalone_universe": list(STRUCTURAL_BREAK_SUBGROUP),
        "asymmetric_barrier_spec": {
            "tp_multiplier": engine.tp_multiplier,
            "sl_multiplier": engine.sl_multiplier,
            "payoff_ratio": "2.5:1.0",
            "horizon_bars": engine.horizon_bars,
            "horizon_minutes": 120,
        },
        "fee_tiers_evaluated": engine.fee_tiers,
        "optimal_configuration_key": best_key,
        "optimal_configuration": best_cfg,
        "full_grid_results": grid_results,
        "xmr_standalone_grid_results": xmr_grid,
    }

    out_file = ARTIFACTS_DIR / "overlay_validation_report.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\nWrote full report to: {out_file} ({out_file.stat().st_size} bytes)")


if __name__ == "__main__":
    run_phase56_optimization()
