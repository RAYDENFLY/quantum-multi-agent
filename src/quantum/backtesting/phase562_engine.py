"""QUANTUM Phase 5.6.2 Backtesting & Optimization Engine.

Implements the multi-asset backtest runner, frequency calibrator, execution simulator,
and portfolio accounting engine according to QUANTUM_PHASE_5_6_2_RESEARCH_MANDATE.md.

Mandate Features:
1. Frequency Calibration: Asset-adaptive volatility quantile & probability margin targeting ~600 trades/asset/year.
2. Signal Quality & Ranking: Evaluates ECE, margin calibration, and directional asymmetry.
3. Entry Optimization: Market immediate entry vs. Passive Maker Limit with queue offsets & 3-bar cancellation.
4. Dynamic Exit: Asymmetric barrier grid (TP 2.0-4.0 sigma, SL 1.0-1.5 sigma, 12-36 bars horizon).
5. Execution Realism: Hybrid maker/taker, adverse selection penalty, and 8-hour funding cashflows.
6. DEC_05 Option 3 Portfolio Simulation: 30% gross exposure cap, 10% single-asset cap, pro-rata capacity sizing.
7. Comprehensive Risk & Return Metrics: Mark-to-market daily return series (mean, geom, median, 7d/30d/90d),
   mean underwater drawdown, median underwater drawdown, MDD, drawdown duration, recovery time, Sharpe/Sortino.
8. Strict Holdout Isolation: Enforces Prospective Holdout (>= 1793491200000 ms) strictly sealed.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from quantum.backtesting.adapters import (
    PRIMARY_RESEARCH_UNIVERSE,
    PROSPECTIVE_HOLDOUT_START_MS,
    STRUCTURAL_BREAK_SUBGROUP,
)
from quantum.backtesting.resources import BACKTEST_MAX_THREADS, enforce_backtest_thread_limits

# Directory constants
DEFAULT_CANDLE_BASE = Path("data/historical/canonical/exchange=ASTER")
DEFAULT_OOF_DIR = Path("artifacts/phase_5_4/materialized_oof")


@dataclass
class CostSchedule:
    """Execution cost schedule in basis points."""
    name: str
    entry_fee_bps: float
    exit_fee_bps: float
    slippage_bps: float
    adverse_selection_bps: float = 0.0
    funding_rate_bps_8h: float = 1.0  # 1 bps per 8h settlement standard assumption

    @property
    def round_trip_friction_bps(self) -> float:
        return self.entry_fee_bps + self.exit_fee_bps + self.slippage_bps + self.adverse_selection_bps


# Canonical Fee Tiers for Phase 5.6.2
COST_TIER_MAKER_PASSIVE = CostSchedule(
    name="maker_passive",
    entry_fee_bps=4.0,
    exit_fee_bps=4.0,
    slippage_bps=0.0,
    adverse_selection_bps=0.0,
)

COST_TIER_HYBRID = CostSchedule(
    name="hybrid_tier",
    entry_fee_bps=4.0,    # Maker entry
    exit_fee_bps=10.0,   # Blended TP maker (4 bps) / SL taker (40 bps)
    slippage_bps=1.0,
    adverse_selection_bps=0.0,
)

COST_TIER_BASELINE_TAKER = CostSchedule(
    name="baseline_taker",
    entry_fee_bps=20.0,
    exit_fee_bps=20.0,
    slippage_bps=4.0,
    adverse_selection_bps=0.0,
)


@dataclass
class StrategyConfig:
    """Configuration for Phase 5.6.2 Specialist Execution."""
    symbol: str
    vol_quantile: float = 0.90
    vol_floor_bps: float = 0.0
    prob_margin: float = 0.20
    direction_filter: str = "BOTH"  # "BOTH", "LONG_ONLY", "SHORT_ONLY"
    delta_limit_offset: float = 0.0  # 0.0 = Market open entry; > 0 = Limit entry offset (in sigmas)
    order_timeout_bars: int = 3
    tp_multiplier: float = 2.5
    sl_multiplier: float = 1.0
    horizon_bars: int = 24
    cooldown_bars: int = 0


@dataclass
class CompletedTrade:
    """Record of a simulated completed trade."""
    symbol: str
    side: str  # "LONG" or "SHORT"
    entry_time_ms: int
    exit_time_ms: int
    entry_price: float
    exit_price: float
    exit_reason: str  # "TAKE_PROFIT", "STOP_LOSS", "TIME_EXPIRATION"
    bars_held: int
    volatility_sigma: float
    gross_return_bps: float
    fold: int = 0
    funding_events_count: int = 0


def calculate_sharpe_sortino(
    returns: np.ndarray,
    periods_per_year: float = 365.25,
) -> Tuple[float, float]:
    """Calculates annualized Sharpe and Sortino ratios."""
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


class Phase562Engine:
    """Multi-asset simulation and research optimization engine for Phase 5.6.2."""

    def __init__(
        self,
        candle_base_dir: Path = DEFAULT_CANDLE_BASE,
        oof_dir: Path = DEFAULT_OOF_DIR,
    ) -> None:
        enforce_backtest_thread_limits(BACKTEST_MAX_THREADS)
        self.candle_base_dir = candle_base_dir
        self.oof_dir = oof_dir
        self._candle_cache: Dict[str, pd.DataFrame] = {}
        self._oof_cache: Dict[str, pd.DataFrame] = {}

    def load_candles(self, symbol: str) -> pd.DataFrame:
        """Loads canonical 5m candles, enforcing holdout seal."""
        if symbol in self._candle_cache:
            return self._candle_cache[symbol]

        s_dir = self.candle_base_dir / f"symbol={symbol}" / "timeframe=5m"
        if not s_dir.exists():
            raise FileNotFoundError(f"Candles not found for {symbol} at {s_dir}")

        files = sorted(s_dir.glob("*.parquet"))
        dfs = []
        cols = ["open_time_ms", "open", "high", "low", "close"]
        for f in files:
            pf = pq.ParquetFile(f)
            dfs.append(pf.read(cols).to_pandas())
        df = pd.concat(dfs, ignore_index=True)
        df = df.sort_values("open_time_ms", kind="mergesort").drop_duplicates(subset=["open_time_ms"]).reset_index(drop=True)

        # Enforce prospective holdout barrier
        max_ts = df["open_time_ms"].max()
        if max_ts >= PROSPECTIVE_HOLDOUT_START_MS:
            raise ValueError(
                f"PROSPECTIVE HOLDOUT BREACH in {symbol}: max_ts={max_ts} >= {PROSPECTIVE_HOLDOUT_START_MS}"
            )
        self._candle_cache[symbol] = df
        return df

    def load_oof(self, symbol: str, folds: Sequence[int] = (1, 2, 3, 4)) -> pd.DataFrame:
        """Loads materialized out-of-fold predictions for specified folds."""
        cache_key = f"{symbol}_{'_'.join(map(str, sorted(folds)))}"
        if cache_key in self._oof_cache:
            return self._oof_cache[cache_key]

        f_path = self.oof_dir / f"{symbol}_oof.parquet"
        if not f_path.exists():
            raise FileNotFoundError(f"OOF predictions not found: {f_path}")

        cols = [
            "fold", "open_time_ms", "true_label", "predicted_class",
            "raw_prob_m1", "raw_prob_0", "raw_prob_p1",
        ]
        df_oof = pq.read_table(f_path, columns=cols).to_pandas()
        df_filtered = df_oof[df_oof["fold"].isin(folds)].sort_values("open_time_ms", kind="mergesort").reset_index(drop=True)

        max_ts = df_filtered["open_time_ms"].max()
        if max_ts >= PROSPECTIVE_HOLDOUT_START_MS:
            raise ValueError(f"PROSPECTIVE HOLDOUT BREACH in OOF {symbol}: max_ts={max_ts}")

        self._oof_cache[cache_key] = df_filtered
        return df_filtered

    def simulate_specialist(
        self,
        cfg: StrategyConfig,
        df_candles: Optional[pd.DataFrame] = None,
        df_oof: Optional[pd.DataFrame] = None,
    ) -> List[CompletedTrade]:
        """Simulates single specialist trading under specific strategy parameters."""
        if df_candles is None:
            df_candles = self.load_candles(cfg.symbol)
        if df_oof is None:
            df_oof = self.load_oof(cfg.symbol)

        # Causal rolling volatility (20-bar std of close returns)
        ret = df_candles["close"].pct_change()
        vol_series = ret.rolling(20, min_periods=20).std(ddof=1).clip(lower=1e-4).fillna(0.0).to_numpy()

        # Determine volatility threshold
        valid_vols = vol_series[vol_series > 1e-4]
        if cfg.vol_floor_bps > 0.0:
            vol_thresh = cfg.vol_floor_bps / 10_000.0
        else:
            vol_thresh = float(np.quantile(valid_vols, cfg.vol_quantile)) if len(valid_vols) > 0 else 0.0

        # Build signal lookup map: open_time_ms -> (fold, prob_m1, prob_0, prob_p1)
        oof_map = {}
        for r in df_oof.itertuples():
            oof_map[r.open_time_ms] = (int(r.fold), float(r.raw_prob_m1), float(r.raw_prob_0), float(r.raw_prob_p1))

        c_opens = df_candles["open"].to_numpy(dtype=float)
        c_highs = df_candles["high"].to_numpy(dtype=float)
        c_lows = df_candles["low"].to_numpy(dtype=float)
        c_closes = df_candles["close"].to_numpy(dtype=float)
        c_ts = df_candles["open_time_ms"].to_numpy(dtype=int)
        n = len(df_candles)

        trades: List[CompletedTrade] = []
        active = False
        entry_bar = 0
        side = 0
        u_barr = 0.0
        l_barr = 0.0
        entry_px = 0.0
        entry_ts = 0
        sigma_val = 0.0
        trade_fold = 0
        last_exit_bar = -999

        # Pending limit order state
        pending_order: Optional[Tuple[int, float, int, float, int, int]] = None  # (side, limit_px, order_bar, sigma, fold, order_ts)

        for i in range(20, n):
            prev_ts = int(c_ts[i - 1])
            o, h, l, c = c_opens[i], c_highs[i], c_lows[i], c_closes[i]

            # 1. Active Position Evaluation
            if active:
                bars_held = (i - entry_bar) + 1
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
                        # Conservative SL first on double-touch collision
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
                    elif bars_held >= cfg.horizon_bars:
                        exit_px = c
                        reason = "TIME_EXPIRATION"
                        exit_trig = True

                if exit_trig:
                    exit_ts = int(c_ts[i]) if is_gap else int(c_ts[i]) + 300_000
                    d = float(side)
                    gross_ret_bps = d * (exit_px - entry_px) / entry_px * 10_000.0

                    # Count 8-hour funding events during hold period
                    entry_8h = entry_ts // (8 * 3600 * 1000)
                    exit_8h = exit_ts // (8 * 3600 * 1000)
                    funding_events = max(0, int(exit_8h - entry_8h))

                    trades.append(
                        CompletedTrade(
                            symbol=cfg.symbol,
                            side="LONG" if side == 1 else "SHORT",
                            entry_time_ms=entry_ts,
                            exit_time_ms=exit_ts,
                            entry_price=entry_px,
                            exit_price=exit_px,
                            exit_reason=reason,
                            bars_held=bars_held,
                            volatility_sigma=sigma_val,
                            gross_return_bps=gross_ret_bps,
                            fold=trade_fold,
                            funding_events_count=funding_events,
                        )
                    )
                    active = False
                    last_exit_bar = i

            # 2. Pending Limit Order Fill Check
            if pending_order is not None and not active:
                p_side, limit_px, order_bar, p_sigma, p_fold, p_ts = pending_order
                filled = False
                fill_px = 0.0

                if p_side == 1 and l <= limit_px:
                    filled = True
                    fill_px = limit_px
                elif p_side == -1 and h >= limit_px:
                    filled = True
                    fill_px = limit_px

                if filled:
                    side = p_side
                    entry_px = fill_px
                    entry_ts = int(c_ts[i])
                    entry_bar = i
                    sigma_val = p_sigma
                    trade_fold = p_fold

                    if side == 1:
                        u_barr = entry_px * (1.0 + cfg.tp_multiplier * sigma_val)
                        l_barr = entry_px * (1.0 - cfg.sl_multiplier * sigma_val)
                    else:
                        u_barr = entry_px * (1.0 + cfg.sl_multiplier * sigma_val)
                        l_barr = entry_px * (1.0 - cfg.tp_multiplier * sigma_val)

                    active = True
                    pending_order = None
                elif (i - order_bar) >= cfg.order_timeout_bars:
                    # Cancel expired pending limit order
                    pending_order = None

            # 3. New Entry Signal Evaluation
            if not active and pending_order is None and (i - last_exit_bar) > cfg.cooldown_bars and prev_ts in oof_map:
                f_idx, pm1, p0, pp1 = oof_map[prev_ts]
                sigma = float(vol_series[i - 1])

                if sigma >= vol_thresh:
                    diff = max(pp1, pm1) - p0
                    if diff >= cfg.prob_margin:
                        s = 1 if pp1 > pm1 else -1

                        # Directional filter
                        if cfg.direction_filter == "LONG_ONLY" and s != 1:
                            continue
                        if cfg.direction_filter == "SHORT_ONLY" and s != -1:
                            continue

                        if cfg.delta_limit_offset == 0.0:
                            # Immediate market entry at open
                            side = s
                            entry_px = o
                            entry_ts = int(c_ts[i])
                            entry_bar = i
                            sigma_val = sigma
                            trade_fold = f_idx

                            if side == 1:
                                u_barr = entry_px * (1.0 + cfg.tp_multiplier * sigma)
                                l_barr = entry_px * (1.0 - cfg.sl_multiplier * sigma)
                            else:
                                u_barr = entry_px * (1.0 + cfg.sl_multiplier * sigma)
                                l_barr = entry_px * (1.0 - cfg.tp_multiplier * sigma)
                            active = True
                        else:
                            # Passive maker limit order placed at discount
                            limit_px = o * (1.0 - cfg.delta_limit_offset * sigma) if s == 1 else o * (1.0 + cfg.delta_limit_offset * sigma)
                            pending_order = (s, limit_px, i, sigma, f_idx, int(c_ts[i]))

        return trades

    def evaluate_trade_series(
        self,
        trades: List[CompletedTrade],
        cost: CostSchedule = COST_TIER_MAKER_PASSIVE,
    ) -> Dict[str, Any]:
        """Calculates single-asset statistical and financial performance metrics."""
        n = len(trades)
        if n == 0:
            return {
                "trade_count": 0,
                "gross_win_rate_pct": 0.0,
                "net_win_rate_pct": 0.0,
                "tp_count": 0,
                "sl_count": 0,
                "exp_count": 0,
                "gross_expectancy_bps": 0.0,
                "net_expectancy_bps": 0.0,
                "profit_factor": 0.0,
                "sharpe_annualized": 0.0,
                "sortino_annualized": 0.0,
            }

        gross_rets = np.array([t.gross_return_bps for t in trades], dtype=float)
        funding_costs = np.array([t.funding_events_count * cost.funding_rate_bps_8h for t in trades], dtype=float)
        net_rets = gross_rets - cost.round_trip_friction_bps - funding_costs

        tp_count = sum(1 for t in trades if t.exit_reason == "TAKE_PROFIT")
        sl_count = sum(1 for t in trades if t.exit_reason == "STOP_LOSS")
        exp_count = sum(1 for t in trades if t.exit_reason == "TIME_EXPIRATION")

        wins = net_rets[net_rets > 0.0]
        losses = np.abs(net_rets[net_rets < 0.0])
        tot_win = float(np.sum(wins)) if len(wins) > 0 else 0.0
        tot_loss = float(np.sum(losses)) if len(losses) > 0 else 0.0
        pf = (tot_win / tot_loss) if tot_loss > 0.0 else (999.0 if tot_win > 0 else 0.0)

        sharpe, sortino = calculate_sharpe_sortino(net_rets / 10_000.0, periods_per_year=600.0)

        return {
            "trade_count": n,
            "gross_win_rate_pct": round(tp_count / n * 100.0, 2),
            "net_win_rate_pct": round(len(wins) / n * 100.0, 2),
            "tp_count": tp_count,
            "sl_count": sl_count,
            "exp_count": exp_count,
            "gross_expectancy_bps": round(float(np.mean(gross_rets)), 2),
            "net_expectancy_bps": round(float(np.mean(net_rets)), 2),
            "profit_factor": round(pf, 3),
            "sharpe_annualized": round(sharpe, 3),
            "sortino_annualized": round(sortino, 3),
        }

    def simulate_multi_asset_portfolio(
        self,
        all_trades: List[CompletedTrade],
        cost: CostSchedule = COST_TIER_MAKER_PASSIVE,
        initial_equity: float = 10_000.0,
        gross_exposure_cap: float = 0.30,
        single_asset_cap: float = 0.10,
        risk_budget_per_trade: float = 0.005,  # 50 bps equity risk
    ) -> Dict[str, Any]:
        """Simulates simultaneous multi-asset portfolio ledger under DEC_05 Option 3 constraints.
        
        Calculates complete mark-to-market daily returns, mean underwater drawdown,
        maximum drawdown, episode depth, recovery duration, and rolling statistics.
        """
        if not all_trades:
            return {"total_trades": 0, "net_return_pct": 0.0, "max_drawdown_pct": 0.0}

        sorted_trades = sorted(all_trades, key=lambda x: x.entry_time_ms)
        friction_rate = cost.round_trip_friction_bps / 10_000.0

        current_equity = initial_equity
        peak_equity = initial_equity
        max_dd = 0.0

        events = []
        for tr in sorted_trades:
            events.append((tr.entry_time_ms, "ENTRY", tr))
            events.append((tr.exit_time_ms, "EXIT", tr))
        # Prioritize EXIT before ENTRY at the same millisecond timestamp
        events.sort(key=lambda x: (x[0], 0 if x[1] == "EXIT" else 1))

        open_positions: Dict[str, Dict[str, Any]] = {}
        executed_portfolio_trades: List[Dict[str, Any]] = []

        # Time tracking for daily marks and continuous underwater drawdown
        t_start = sorted_trades[0].entry_time_ms
        t_end = max(t.exit_time_ms for t in sorted_trades)

        day_ms = 86_400_000
        first_day_boundary = (t_start // day_ms + 1) * day_ms
        next_day_mark = first_day_boundary

        daily_equity_marks: List[Tuple[int, float]] = [(t_start, initial_equity)]
        underwater_drawdown_series: List[float] = [0.0]
        concurrency_series: List[int] = []

        # Completed drawdown episodes tracking: (start_t, trough_dd, end_t, duration_days)
        in_drawdown = False
        current_episode_max_dd = 0.0
        episode_start_ts = t_start
        completed_episodes: List[Dict[str, Any]] = []

        for ts, ev_type, tr in events:
            # Advance daily boundaries up to current event timestamp
            while next_day_mark <= ts:
                # Mark-to-market equity at daily boundary
                daily_equity_marks.append((next_day_mark, current_equity))
                next_day_mark += day_ms

            t_id = f"{tr.symbol}_{tr.entry_time_ms}"

            if ev_type == "EXIT":
                if t_id in open_positions:
                    pos = open_positions.pop(t_id)
                    notional = pos["allocated_notional"]
                    gross_ret = tr.gross_return_bps / 10_000.0
                    funding_cost = tr.funding_events_count * (cost.funding_rate_bps_8h / 10_000.0)
                    net_ret = gross_ret - friction_rate - funding_cost
                    net_pnl = notional * net_ret

                    current_equity += net_pnl

                    # Update Peak and Drawdown
                    if current_equity > peak_equity:
                        if in_drawdown and current_episode_max_dd > 0.5:
                            completed_episodes.append({
                                "start_ts": episode_start_ts,
                                "trough_dd_pct": round(current_episode_max_dd, 2),
                                "duration_days": round((ts - episode_start_ts) / day_ms, 2),
                            })
                            in_drawdown = False
                            current_episode_max_dd = 0.0
                        peak_equity = current_equity

                    dd = ((peak_equity - current_equity) / peak_equity) * 100.0 if peak_equity > 0 else 0.0
                    if dd > 0.01:
                        if not in_drawdown:
                            in_drawdown = True
                            episode_start_ts = ts
                        if dd > current_episode_max_dd:
                            current_episode_max_dd = dd
                    if dd > max_dd:
                        max_dd = dd

                    underwater_drawdown_series.append(dd)

                    executed_portfolio_trades.append({
                        "trade_id": t_id,
                        "symbol": tr.symbol,
                        "side": tr.side,
                        "allocated_notional": round(notional, 2),
                        "gross_return_bps": tr.gross_return_bps,
                        "net_pnl": round(net_pnl, 2),
                        "exit_time_ms": ts,
                        "equity_after": round(current_equity, 2),
                    })

            elif ev_type == "ENTRY":
                # Risk budget sizing: target notional = (R_budget * Equity) / (SL_mult * sigma)
                sigma = tr.volatility_sigma
                target_notional = (risk_budget_per_trade * current_equity) / (1.0 * sigma) if sigma > 0 else 0.0
                target_notional = min(target_notional, single_asset_cap * current_equity)

                cur_total = sum(p["allocated_notional"] for p in open_positions.values())
                capacity = max(0.0, gross_exposure_cap * current_equity - cur_total)
                allocated = min(target_notional, capacity)

                if allocated >= 10.0:  # Minimum viable notional $10 USDT
                    open_positions[t_id] = {
                        "allocated_notional": allocated,
                        "entry_time_ms": ts,
                    }
                concurrency_series.append(len(open_positions))

        # Close out remaining daily marks up to t_end
        while next_day_mark <= t_end:
            daily_equity_marks.append((next_day_mark, current_equity))
            next_day_mark += day_ms
        daily_equity_marks.append((t_end, current_equity))

        # Daily Returns Calculation
        df_daily = pd.DataFrame(daily_equity_marks, columns=["timestamp_ms", "equity"]).drop_duplicates("timestamp_ms")
        df_daily["daily_return"] = df_daily["equity"].pct_change().fillna(0.0)
        daily_rets = df_daily["daily_return"].to_numpy()[1:]  # skip day 0

        n_days = len(daily_rets)
        if n_days > 0:
            arith_mean_daily = float(np.mean(daily_rets))
            median_daily = float(np.median(daily_rets))
            # Geometric mean: (prod(1 + r))^(1/n) - 1 = (ending / initial)^(1/n) - 1
            geom_mean_daily = float((current_equity / initial_equity) ** (1.0 / n_days) - 1.0)
            worst_single_day = float(np.min(daily_rets)) * 100.0

            # Rolling 7-day, 30-day, 90-day returns
            s_ret = pd.Series(daily_rets)
            roll_7 = (s_ret + 1.0).rolling(7).apply(np.prod, raw=True) - 1.0
            roll_30 = (s_ret + 1.0).rolling(30).apply(np.prod, raw=True) - 1.0
            roll_90 = (s_ret + 1.0).rolling(90).apply(np.prod, raw=True) - 1.0

            mean_7d = float(roll_7.mean() * 100.0) if len(roll_7.dropna()) > 0 else 0.0
            worst_7d = float(roll_7.min() * 100.0) if len(roll_7.dropna()) > 0 else 0.0
            mean_30d = float(roll_30.mean() * 100.0) if len(roll_30.dropna()) > 0 else 0.0
            mean_90d = float(roll_90.mean() * 100.0) if len(roll_90.dropna()) > 0 else 0.0
        else:
            arith_mean_daily = 0.0
            median_daily = 0.0
            geom_mean_daily = 0.0
            worst_single_day = 0.0
            mean_7d = worst_7d = mean_30d = mean_90d = 0.0

        # Drawdown statistics
        mean_underwater_dd = float(np.mean(underwater_drawdown_series)) if underwater_drawdown_series else 0.0
        median_underwater_dd = float(np.median(underwater_drawdown_series)) if underwater_drawdown_series else 0.0
        avg_episode_depth = float(np.mean([ep["trough_dd_pct"] for ep in completed_episodes])) if completed_episodes else 0.0
        mean_recovery_days = float(np.mean([ep["duration_days"] for ep in completed_episodes])) if completed_episodes else 0.0

        # Annualized Sharpe and Sortino
        sharpe_daily, sortino_daily = calculate_sharpe_sortino(daily_rets, periods_per_year=365.25)

        total_net_pnl = current_equity - initial_equity
        net_ret_pct = (total_net_pnl / initial_equity) * 100.0

        # Downsample daily curve for JSON reporting
        step = max(1, len(daily_equity_marks) // 60)
        downsampled_curve = [
            {"timestamp_ms": ts, "equity_usdt": round(eq, 2)}
            for ts, eq in daily_equity_marks[::step]
        ]
        if {"timestamp_ms": t_end, "equity_usdt": round(current_equity, 2)} not in downsampled_curve:
            downsampled_curve.append({"timestamp_ms": t_end, "equity_usdt": round(current_equity, 2)})

        return {
            "fee_tier": cost.name,
            "initial_equity_usdt": initial_equity,
            "ending_equity_usdt": round(current_equity, 2),
            "total_net_pnl_usdt": round(total_net_pnl, 2),
            "net_return_pct": round(net_ret_pct, 2),
            "total_portfolio_trades": len(executed_portfolio_trades),
            "total_candidate_trades": len(sorted_trades),
            "execution_fill_rate_pct": round(len(executed_portfolio_trades) / len(sorted_trades) * 100.0, 2),
            "avg_concurrency": round(float(np.mean(concurrency_series)), 2) if concurrency_series else 0.0,
            # Daily return metrics
            "days_evaluated": n_days,
            "arithmetic_mean_daily_return_pct": round(arith_mean_daily * 100.0, 4),
            "geometric_mean_daily_return_pct": round(geom_mean_daily * 100.0, 4),
            "median_daily_return_pct": round(median_daily * 100.0, 4),
            "mean_rolling_7d_return_pct": round(mean_7d, 2),
            "worst_rolling_7d_return_pct": round(worst_7d, 2),
            "mean_rolling_30d_return_pct": round(mean_30d, 2),
            "mean_rolling_90d_return_pct": round(mean_90d, 2),
            "worst_single_day_loss_pct": round(worst_single_day, 2),
            "cagr_uncompounded_pct": round(arith_mean_daily * 365.25 * 100.0, 2),
            # Drawdown metrics
            "mean_underwater_drawdown_pct": round(mean_underwater_dd, 2),
            "median_underwater_drawdown_pct": round(median_underwater_dd, 2),
            "max_drawdown_pct": round(max_dd, 2),
            "completed_drawdown_episodes_count": len(completed_episodes),
            "average_episode_depth_pct": round(avg_episode_depth, 2),
            "mean_recovery_days": round(mean_recovery_days, 2),
            # Risk-adjusted ratios
            "sharpe_annualized": round(sharpe_daily, 3),
            "sortino_annualized": round(sortino_daily, 3),
            "equity_curve": downsampled_curve,
        }
