"""QUANTUM Milestone 5.4 — HYP-02: Liquidity Sweep & Reclaim Strategy.

Implements the institutional liquidity sweep alpha hypothesis:
1. Trailing Swing High / Swing Low Liquidity Pools (1h context on 5m execution).
2. Stop-Loss Cluster Penetration & Wick Rejection Confirmation.
3. Level Reclaim & Volume Expansion Filter.
4. Higher-Timeframe Trend Compatibility Check.
5. Banker High-Fidelity Execution Simulator (Bybit VIP0 fee tier, non-conflated maker/taker accounting).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from quantum.strategies.schemas import get_venue_schedule


class HYP02Configuration(BaseModel):
    """Full declarative configuration for HYP-02 strategy."""

    strategy_id: str = "HYP02_LIQUIDITY_SWEEP_V1"
    version: str = "1.0.0"

    # Liquidity Sweep Parameters
    sweep_lookback_bars: int = Field(default=12, description="Lookback bars on 5m to define swing high/low (12 bars = 1 hour)")
    min_wick_ratio: float = Field(default=0.35, description="Minimum wick fraction (lower wick for long, upper wick for short)")
    min_rvol: float = Field(default=1.10, description="Minimum relative volume ratio on sweep candle")
    htf_trend_max_adverse_bps: float = Field(default=150.0, description="Maximum adverse 1h trend in bps to avoid counter-trend freight trains")
    
    # Entry & Execution Timing
    order_type: str = Field(default="MARKET", description="MARKET or LIMIT")
    cooldown_bars: int = Field(default=3, description="Cooldown between successive trades on same symbol")

    # Volatility-Adjusted Exit Engine
    sl_multiplier: float = Field(default=1.5, description="Initial Stop-Loss in sigmas beyond sweep extreme")
    tp1_multiplier: float = Field(default=2.5, description="Take-Profit 1 in sigmas (~1.67x Risk)")
    tp2_multiplier: float = Field(default=4.0, description="Take-Profit 2 in sigmas (~2.67x Risk)")
    tp1_close_pct: float = Field(default=0.50, description="Fraction closed at TP1")
    enable_breakeven_ratchet: bool = Field(default=True, description="Move SL to entry price once TP1 is hit")
    trailing_stop_sigma: float = Field(default=1.5, description="Trailing stop distance in sigmas active after TP1")
    max_horizon_bars: int = Field(default=6, description="Maximum holding duration before time expiration (30 minutes)")

    # Risk Management Parameters
    risk_per_trade_pct: float = Field(default=0.015, description="Risk budget per trade (1.5% of equity)")
    max_leverage: float = Field(default=3.0, description="Hard cap on position leverage (max 3x)")
    max_concurrent_positions: int = Field(default=4, description="Maximum concurrent active positions across universe")
    max_symbol_exposure_pct: float = Field(default=0.25, description="Maximum capital allocated to any single symbol")
    daily_loss_circuit_breaker_pct: float = Field(default=0.04, description="Halts trading for 24h if daily loss hits 4%")
    max_drawdown_circuit_breaker_pct: float = Field(default=0.15, description="Halves position sizing if drawdown exceeds 15%")
    initial_equity_usd: float = Field(default=100.0, description="Starting portfolio equity")

    # Execution Venue
    fee_tier: str = Field(default="BYBIT_VIP0_DEFAULT", description="Execution venue fee schedule key")

    @property
    def config_hash(self) -> str:
        """Deterministic SHA-256 hash of configuration parameters."""
        data_str = json.dumps(self.model_dump(), sort_keys=True)
        return hashlib.sha256(data_str.encode("utf-8")).hexdigest()[:16]


class HYP02Engine:
    """Simulation engine for HYP-02 Liquidity Sweep & Reclaim."""

    def __init__(self, config: HYP02Configuration) -> None:
        self.config = config
        self.venue = get_venue_schedule(config.fee_tier)

    def generate_asset_signals(
        self,
        matrices: Dict[str, Any],
        holdout_cutoff_ms: int = 1793491200000,
    ) -> Dict[str, Dict[str, np.ndarray]]:
        """Precomputes causal HYP-02 signals per asset."""
        cfg = self.config
        symbol_list = [s for s in matrices.keys() if s != "XMRUSDT"]
        asset_signals = {}

        for sym in symbol_list:
            m = matrices[sym]
            n_bars = len(m.opens)
            highs_s = pd.Series(m.highs)
            lows_s = pd.Series(m.lows)
            
            # Causal trailing swing high/low (strictly shift by 1 to exclude current bar)
            lb = cfg.sweep_lookback_bars
            swing_high = highs_s.rolling(lb, min_periods=lb).max().shift(1).to_numpy()
            swing_low = lows_s.rolling(lb, min_periods=lb).min().shift(1).to_numpy()

            sig_side = np.zeros(n_bars, dtype=np.int8)
            htf_12 = m.htf_rets_bps[12] if 12 in m.htf_rets_bps else np.zeros(n_bars)
            rvol = m.rvol_20
            lw = m.lower_wick
            uw = m.upper_wick

            for i in range(lb + 5, n_bars - 2):
                if m.open_time_ms[i] >= holdout_cutoff_ms:
                    continue

                sh = swing_high[i]
                sl = swing_low[i]
                if np.isnan(sh) or np.isnan(sl):
                    continue

                # Bullish Sweep & Reclaim (Long Signal)
                # 1. Low penetrated prior swing low
                # 2. Close reclaimed back above swing low
                # 3. Lower wick ratio >= min_wick_ratio
                # 4. Volume expansion >= min_rvol
                # 5. HTF 1h return not dumping vertically (> -htf_trend_max_adverse_bps)
                if (
                    m.lows[i] < sl
                    and m.closes[i] > sl
                    and lw[i] >= cfg.min_wick_ratio
                    and rvol[i] >= cfg.min_rvol
                    and htf_12[i] >= -cfg.htf_trend_max_adverse_bps
                    and m.closes[i] > m.opens[i]  # Reclaim green candle
                ):
                    sig_side[i] = 1

                # Bearish Sweep & Reclaim (Short Signal)
                # 1. High penetrated prior swing high
                # 2. Close reclaimed back below swing high
                # 3. Upper wick ratio >= min_wick_ratio
                # 4. Volume expansion >= min_rvol
                # 5. HTF 1h return not pumping vertically (< +htf_trend_max_adverse_bps)
                elif (
                    m.highs[i] > sh
                    and m.closes[i] < sh
                    and uw[i] >= cfg.min_wick_ratio
                    and rvol[i] >= cfg.min_rvol
                    and htf_12[i] <= cfg.htf_trend_max_adverse_bps
                    and m.closes[i] < m.opens[i]  # Reclaim red candle
                ):
                    sig_side[i] = -1

            asset_signals[sym] = {
                "signal_side": sig_side,
                "swing_high": swing_high,
                "swing_low": swing_low,
            }

        return asset_signals

    def evaluate_multi_asset(
        self,
        matrices: Dict[str, Any],
        holdout_cutoff_ms: int = 1793491200000,
        fixed_notional_usd: float = 0.0,
    ) -> Tuple[Dict[str, Any], pd.DataFrame, pd.DataFrame]:
        """Runs full multi-asset portfolio simulation across 1,099 calendar days."""
        cfg = self.config
        venue = self.venue
        symbol_list = [s for s in matrices.keys() if s != "XMRUSDT"]

        asset_signals = self.generate_asset_signals(matrices, holdout_cutoff_ms)

        portfolio_equity = float(cfg.initial_equity_usd) if fixed_notional_usd == 0.0 else float(fixed_notional_usd * 10.0)
        peak_equity = portfolio_equity
        trades = []
        daily_records = []

        active_positions: Dict[str, Dict[str, Any]] = {}
        last_trade_bar = {s: -999 for s in symbol_list}
        daily_loss_accum = 0.0
        current_day = None

        master_bars = len(matrices["BTCUSDT"].opens)
        day_start_equity = portfolio_equity
        day_trades_count = 0
        day_realized_pnl = 0.0

        for i in range(20, master_bars - 2):
            t_ms = matrices["BTCUSDT"].open_time_ms[i]
            if t_ms >= holdout_cutoff_ms:
                break

            day_key = t_ms // (86400 * 1000)

            # 24h Calendar day boundary
            if current_day is not None and day_key != current_day:
                unrealized_pnl = 0.0
                for sym, pos in active_positions.items():
                    curr_c = matrices[sym].closes[i - 1]
                    unrealized_pnl += pos["notional"] * pos["side"] * (curr_c - pos["entry_price"]) / pos["entry_price"]

                eod_equity = portfolio_equity + unrealized_pnl
                daily_ret = (eod_equity / day_start_equity - 1.0) * 100.0

                daily_records.append({
                    "day_index": len(daily_records) + 1,
                    "day_timestamp_ms": current_day * 86400 * 1000,
                    "date_utc": pd.to_datetime(current_day * 86400 * 1000, unit="ms", utc=True).strftime("%Y-%m-%d"),
                    "start_day_equity_usd": day_start_equity,
                    "end_day_cash_equity_usd": portfolio_equity,
                    "unrealized_pnl_usd": unrealized_pnl,
                    "end_day_mtm_equity_usd": eod_equity,
                    "daily_return_pct": daily_ret,
                    "realized_pnl_usd": day_realized_pnl,
                    "closed_trades_count": day_trades_count,
                    "active_positions_count": len(active_positions),
                })

                day_start_equity = eod_equity
                daily_loss_accum = 0.0
                day_trades_count = 0
                day_realized_pnl = 0.0

            current_day = day_key

            # Update active positions
            closed_syms = []
            for sym, pos in active_positions.items():
                m = matrices[sym]
                o, h, l, c = m.opens[i], m.highs[i], m.lows[i], m.closes[i]
                side = pos["side"]
                entry_px = pos["entry_price"]
                sl_px = pos["sl_price"]
                tp1_px = pos["tp1_price"]
                tp2_px = pos["tp2_price"]
                bars_held = i - pos["entry_bar"]
                sigma = pos["sigma"]

                sl_hit = (l <= sl_px) if side == 1 else (h >= sl_px)
                if sl_hit:
                    closed_syms.append((sym, sl_px, "STOP_LOSS", "TAKER", bars_held))
                    continue

                if not pos["tp1_hit"]:
                    tp1_hit = (h >= tp1_px) if side == 1 else (l <= tp1_px)
                    if tp1_hit:
                        pos["tp1_hit"] = True
                        if cfg.enable_breakeven_ratchet:
                            pos["sl_price"] = entry_px

                tp2_hit = (h >= tp2_px) if side == 1 else (l <= tp2_px)
                if tp2_hit:
                    closed_syms.append((sym, tp2_px, "TAKE_PROFIT", "MAKER", bars_held))
                    continue

                # Trailing stop
                if pos["tp1_hit"] and cfg.trailing_stop_sigma > 0:
                    trail_dist = cfg.trailing_stop_sigma * sigma * c
                    if side == 1:
                        new_sl = c - trail_dist
                        if new_sl > pos["sl_price"]:
                            pos["sl_price"] = new_sl
                    else:
                        new_sl = c + trail_dist
                        if new_sl < pos["sl_price"]:
                            pos["sl_price"] = new_sl

                if bars_held >= cfg.max_horizon_bars:
                    closed_syms.append((sym, c, "TIME_EXPIRATION", "TAKER", bars_held))
                    continue

            # Process closed positions
            for sym, fill_px, reason, exit_role, bars_held in closed_syms:
                pos = active_positions.pop(sym)
                side = pos["side"]
                entry_px = pos["entry_price"]
                notional = pos["notional"]

                leg_return = float(side) * (fill_px - entry_px) / entry_px
                gross_pnl = notional * leg_return

                entry_fee_rate = (venue.taker_fee_bps_per_leg / 10_000.0) if pos["entry_role"] == "TAKER" else (venue.maker_fee_bps_per_leg / 10_000.0)
                exit_fee_rate = (venue.taker_fee_bps_per_leg / 10_000.0) if exit_role == "TAKER" else (venue.maker_fee_bps_per_leg / 10_000.0)
                fee_usd = notional * (entry_fee_rate + exit_fee_rate)
                spread_usd = notional * (venue.default_spread_bps / 10_000.0) if pos["entry_role"] == "TAKER" else 0.0
                slip_usd = notional * (venue.default_slippage_bps / 10_000.0)
                fund_usd = notional * 0.0001 * (bars_held // 96)

                total_cost = fee_usd + spread_usd + slip_usd + fund_usd
                net_pnl = gross_pnl - total_cost

                portfolio_equity += net_pnl
                daily_loss_accum += min(0.0, net_pnl)
                peak_equity = max(peak_equity, portfolio_equity)

                day_trades_count += 1
                day_realized_pnl += net_pnl

                trades.append({
                    "trade_id": f"HYP02_{len(trades)+1:06d}_{sym}",
                    "strategy_id": "HYP-02",
                    "symbol": sym,
                    "side": "LONG" if side == 1 else "SHORT",
                    "entry_time_ms": pos["entry_time"],
                    "exit_time_ms": matrices[sym].open_time_ms[i],
                    "entry_price": entry_px,
                    "exit_price": fill_px,
                    "exit_reason": reason,
                    "entry_role": pos["entry_role"],
                    "exit_role": exit_role,
                    "bars_held": bars_held,
                    "notional_usd": notional,
                    "gross_return_bps": leg_return * 10_000.0,
                    "net_return_bps": (net_pnl / notional) * 10_000.0,
                    "gross_pnl_usd": gross_pnl,
                    "net_pnl_usd": net_pnl,
                    "fee_usd": fee_usd,
                    "spread_usd": spread_usd,
                    "slip_usd": slip_usd,
                    "fund_usd": fund_usd,
                    "total_cost_usd": total_cost,
                    "fold": int(matrices[sym].fold_prev[i]),
                })

            # Check circuit breaker
            if portfolio_equity <= 5.0:
                break
            if abs(daily_loss_accum) / max(portfolio_equity, 10.0) >= cfg.daily_loss_circuit_breaker_pct:
                continue

            dd_pct = (peak_equity - portfolio_equity) / peak_equity
            leverage_mult = 0.5 if dd_pct >= cfg.max_drawdown_circuit_breaker_pct else 1.0

            if len(active_positions) >= cfg.max_concurrent_positions:
                continue

            # Scan new entries
            for sym in symbol_list:
                if len(active_positions) >= cfg.max_concurrent_positions:
                    break
                if sym in active_positions:
                    continue
                if (i - last_trade_bar[sym]) < cfg.cooldown_bars:
                    continue

                sig = asset_signals[sym]["signal_side"][i]
                if sig == 0:
                    continue

                m = matrices[sym]
                sigma = m.sigma_20[i]
                arrival_px = m.opens[i]

                sl_dist = cfg.sl_multiplier * sigma * arrival_px
                tp1_dist = cfg.tp1_multiplier * sigma * arrival_px
                tp2_dist = cfg.tp2_multiplier * sigma * arrival_px

                sl_px = arrival_px - sl_dist if sig == 1 else arrival_px + sl_dist
                tp1_px = arrival_px + tp1_dist if sig == 1 else arrival_px - tp1_dist
                tp2_px = arrival_px + tp2_dist if sig == 1 else arrival_px - tp2_dist

                if fixed_notional_usd > 0.0:
                    notional = fixed_notional_usd
                else:
                    sl_pct = (sl_dist / arrival_px)
                    risk_budget = portfolio_equity * cfg.risk_per_trade_pct
                    desired_notional = risk_budget / max(sl_pct, 0.005)
                    max_allowed_notional = portfolio_equity * cfg.max_leverage * leverage_mult * cfg.max_symbol_exposure_pct
                    notional = min(desired_notional, max_allowed_notional)
                    if notional < 5.0:
                        continue

                active_positions[sym] = {
                    "side": sig,
                    "entry_price": arrival_px,
                    "entry_bar": i,
                    "entry_time": m.open_time_ms[i],
                    "notional": notional,
                    "sl_price": sl_px,
                    "tp1_price": tp1_px,
                    "tp2_price": tp2_px,
                    "tp1_hit": False,
                    "sigma": sigma,
                    "entry_role": "TAKER",
                }
                last_trade_bar[sym] = i

        df_daily = pd.DataFrame(daily_records)
        df_trades = pd.DataFrame(trades)

        summary = self._compute_summary(df_daily, df_trades, portfolio_equity)
        return summary, df_daily, df_trades

    def _compute_summary(
        self,
        df_daily: pd.DataFrame,
        df_trades: pd.DataFrame,
        ending_equity: float,
    ) -> Dict[str, Any]:
        """Calculates canonical performance summary metrics."""
        if df_daily.empty or df_trades.empty:
            return {"error": "No trades executed"}

        d_rets = df_daily["daily_return_pct"]
        mean_d = float(d_rets.mean())
        median_d = float(d_rets.median())
        std_d = float(d_rets.std())
        sharpe_365 = float(mean_d / std_d * np.sqrt(365)) if std_d > 0 else 0.0

        cum_eq = df_daily["end_day_mtm_equity_usd"].values
        peaks = np.maximum.accumulate(cum_eq)
        dds = (peaks - cum_eq) / peaks * 100.0
        mdd = float(np.max(dds)) if len(dds) > 0 else 0.0

        wins = df_trades[df_trades["net_pnl_usd"] > 0]["net_pnl_usd"].sum()
        losses = abs(df_trades[df_trades["net_pnl_usd"] < 0]["net_pnl_usd"].sum())
        pf = float(wins / losses) if losses > 0 else float("inf")
        wr = float((df_trades["net_pnl_usd"] > 0).mean() * 100.0)
        net_exp = float(df_trades["net_return_bps"].mean())
        gross_exp = float(df_trades["gross_return_bps"].mean())

        return {
            "strategy_id": self.config.strategy_id,
            "calendar_days_count": len(df_daily),
            "executed_trades_count": len(df_trades),
            "ending_equity_usd": ending_equity,
            "mean_daily_return_pct": round(mean_d, 4),
            "median_daily_return_pct": round(median_d, 4),
            "daily_std_pct": round(std_d, 4),
            "sharpe_365": round(sharpe_365, 2),
            "max_drawdown_pct": round(mdd, 2),
            "profit_factor": round(pf, 3),
            "win_rate_pct": round(wr, 2),
            "net_expectancy_bps": round(net_exp, 2),
            "gross_expectancy_bps": round(gross_exp, 2),
            "pct_days_gte_3pct": round(float((d_rets >= 3.0).mean() * 100.0), 2),
            "pct_negative_days": round(float((d_rets < 0.0).mean() * 100.0), 2),
            "zero_trade_days_count": int((df_daily["closed_trades_count"] == 0).sum()),
        }
