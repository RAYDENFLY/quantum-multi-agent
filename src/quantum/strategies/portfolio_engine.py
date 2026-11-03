"""QUANTUM Milestone 5.4 — Unified Multi-Strategy Portfolio Engine.

Simulates simultaneous interleaved execution of multiple alpha strategies (HYP-01, HYP-02, HYP-03)
on a shared capital base with strict risk, concurrency, and conflict resolution controls:
1. Signal Conflict Resolution: Contradictory signals on the same symbol cancel each other.
2. Symbol Exclusivity: Only one active position per symbol across all strategies.
3. Global Concurrency Cap: Max 4 concurrent positions across the entire portfolio.
4. Shared Capital & Dynamic Compounding: All strategies trade against the shared margin equity pool.
5. Circuit Breaker Integration: 4% daily portfolio loss circuit breaker and 15% drawdown scaler.
6. 100% Full-Calendar-Day Accounting: 1,099 calendar days with daily MTM mark-to-market.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from quantum.strategies.schemas import get_venue_schedule


class UnifiedPortfolioEngine:
    """Multi-Strategy Portfolio Orchestrator."""

    def __init__(
        self,
        strategy_engines: Dict[str, Any],
        max_concurrent_positions: int = 4,
        max_symbol_exposure_pct: float = 0.25,
        risk_per_trade_pct: float = 0.015,
        max_leverage: float = 3.0,
        daily_loss_circuit_breaker_pct: float = 0.04,
        max_drawdown_circuit_breaker_pct: float = 0.15,
        initial_equity_usd: float = 100.0,
        fee_tier: str = "BYBIT_VIP0_DEFAULT",
    ) -> None:
        self.strategy_engines = strategy_engines
        self.max_concurrent_positions = max_concurrent_positions
        self.max_symbol_exposure_pct = max_symbol_exposure_pct
        self.risk_per_trade_pct = risk_per_trade_pct
        self.max_leverage = max_leverage
        self.daily_loss_circuit_breaker_pct = daily_loss_circuit_breaker_pct
        self.max_drawdown_circuit_breaker_pct = max_drawdown_circuit_breaker_pct
        self.initial_equity_usd = initial_equity_usd
        self.venue = get_venue_schedule(fee_tier)

    def evaluate_portfolio(
        self,
        matrices: Dict[str, Any],
        holdout_cutoff_ms: int = 1793491200000,
        fixed_notional_usd: float = 0.0,
    ) -> Tuple[Dict[str, Any], pd.DataFrame, pd.DataFrame]:
        """Runs the complete multi-strategy portfolio simulation chronologically."""
        venue = self.venue
        symbol_list = [s for s in matrices.keys() if s != "XMRUSDT"]

        # Pre-compute signals for each active strategy
        strategy_signals: Dict[str, Dict[str, Dict[str, np.ndarray]]] = {}
        for strat_name, eng in self.strategy_engines.items():
            if hasattr(eng, "generate_asset_signals"):
                strategy_signals[strat_name] = eng.generate_asset_signals(matrices, holdout_cutoff_ms)
            elif hasattr(eng, "evaluate_multi_asset"):
                # For HYP01Engine, extract signal generator
                strat_sigs = {}
                cfg = eng.config
                for sym in symbol_list:
                    m = matrices[sym]
                    n_bars = len(m.opens)
                    sig_side = np.zeros(n_bars, dtype=np.int8)
                    htf_12 = m.htf_rets_bps[12] if 12 in m.htf_rets_bps else np.zeros(n_bars)
                    htf_3 = m.htf_rets_bps[6] if 6 in m.htf_rets_bps else np.zeros(n_bars)
                    for i_b in range(20, n_bars - 2):
                        if m.open_time_ms[i_b] >= holdout_cutoff_ms:
                            continue
                        sigma = m.sigma_20[i_b]
                        htf_val = htf_12[i_b]
                        vol_exp = m.vol_exp_ratio[i_b]
                        regime_name, is_trend = eng.regime_detector.classify_bar(sigma, htf_val, vol_exp)
                        if cfg.enable_regime_filter and not is_trend:
                            continue
                        if cfg.allow_long_entries and htf_val >= cfg.trend_threshold_bps and htf_3[i_b] >= 0 and m.closes[i_b] > m.opens[i_b]:
                            sig_side[i_b] = 1
                        elif cfg.allow_short_entries and htf_val <= -cfg.trend_threshold_bps and htf_3[i_b] <= 0 and m.closes[i_b] < m.opens[i_b]:
                            if cfg.filter_altcoin_shorts and sym not in ("BTCUSDT", "ETHUSDT"):
                                continue
                            sig_side[i_b] = -1
                    strat_sigs[sym] = {"signal_side": sig_side}
                strategy_signals[strat_name] = strat_sigs

        portfolio_equity = float(self.initial_equity_usd) if fixed_notional_usd == 0.0 else float(fixed_notional_usd * 10.0)
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

            # 24h Calendar day transition
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

            # 1. Update & Manage Active Positions
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
                strat_cfg = pos["strat_config"]

                sl_hit = (l <= sl_px) if side == 1 else (h >= sl_px)
                if sl_hit:
                    closed_syms.append((sym, sl_px, "STOP_LOSS", "TAKER", bars_held))
                    continue

                if not pos["tp1_hit"]:
                    tp1_hit = (h >= tp1_px) if side == 1 else (l <= tp1_px)
                    if tp1_hit:
                        pos["tp1_hit"] = True
                        if strat_cfg.enable_breakeven_ratchet:
                            pos["sl_price"] = entry_px

                tp2_hit = (h >= tp2_px) if side == 1 else (l <= tp2_px)
                if tp2_hit:
                    closed_syms.append((sym, tp2_px, "TAKE_PROFIT", "MAKER", bars_held))
                    continue

                # Trailing stop
                if pos["tp1_hit"] and strat_cfg.trailing_stop_sigma > 0:
                    trail_dist = strat_cfg.trailing_stop_sigma * sigma * c
                    if side == 1:
                        new_sl = c - trail_dist
                        if new_sl > pos["sl_price"]:
                            pos["sl_price"] = new_sl
                    else:
                        new_sl = c + trail_dist
                        if new_sl < pos["sl_price"]:
                            pos["sl_price"] = new_sl

                if bars_held >= strat_cfg.max_horizon_bars:
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
                    "trade_id": f"PF_{len(trades)+1:06d}_{sym}",
                    "strategy_origin": pos["strategy_origin"],
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

            # Check circuit breaker & drawdown scaling
            if portfolio_equity <= 5.0:
                break
            if abs(daily_loss_accum) / max(portfolio_equity, 10.0) >= self.daily_loss_circuit_breaker_pct:
                continue

            dd_pct = (peak_equity - portfolio_equity) / peak_equity
            leverage_mult = 0.5 if dd_pct >= self.max_drawdown_circuit_breaker_pct else 1.0

            if len(active_positions) >= self.max_concurrent_positions:
                continue

            # 2. Interleave Strategy Signals with Conflict Resolution
            for sym in symbol_list:
                if len(active_positions) >= self.max_concurrent_positions:
                    break
                if sym in active_positions:
                    continue
                if (i - last_trade_bar[sym]) < 3:
                    continue

                # Collect candidate signals for this symbol at bar i
                signals_at_bar = {}
                for strat_name, sig_dict in strategy_signals.items():
                    side_val = int(sig_dict[sym]["signal_side"][i])
                    if side_val != 0:
                        signals_at_bar[strat_name] = side_val

                if not signals_at_bar:
                    continue

                # Conflict resolution:
                # If opposing signals exist (both LONG and SHORT requested), cancel out!
                sides = set(signals_at_bar.values())
                if len(sides) > 1:
                    # Conflicting signals -> Net exposure 0, cancel
                    continue

                # If unanimous or single signal, select dominant strategy
                # Priority: HYP-01 (Trend momentum) > HYP-02 (Sweep reclaim) > HYP-03 (Mean reversion)
                chosen_strat = None
                for pref in ["HYP-01", "HYP-02", "HYP-03"]:
                    if pref in signals_at_bar:
                        chosen_strat = pref
                        break
                if chosen_strat is None:
                    chosen_strat = list(signals_at_bar.keys())[0]

                sig_side = signals_at_bar[chosen_strat]
                strat_eng = self.strategy_engines[chosen_strat]
                strat_cfg = strat_eng.config

                m = matrices[sym]
                sigma = m.sigma_20[i]
                arrival_px = m.opens[i]

                sl_dist = strat_cfg.sl_multiplier * sigma * arrival_px
                tp1_dist = strat_cfg.tp1_multiplier * sigma * arrival_px
                tp2_dist = strat_cfg.tp2_multiplier * sigma * arrival_px

                sl_px = arrival_px - sl_dist if sig_side == 1 else arrival_px + sl_dist
                tp1_px = arrival_px + tp1_dist if sig_side == 1 else arrival_px - tp1_dist
                tp2_px = arrival_px + tp2_dist if sig_side == 1 else arrival_px - tp2_dist

                if fixed_notional_usd > 0.0:
                    notional = fixed_notional_usd
                else:
                    sl_pct = (sl_dist / arrival_px)
                    risk_budget = portfolio_equity * self.risk_per_trade_pct
                    desired_notional = risk_budget / max(sl_pct, 0.005)
                    max_allowed_notional = portfolio_equity * self.max_leverage * leverage_mult * self.max_symbol_exposure_pct
                    notional = min(desired_notional, max_allowed_notional)
                    if notional < 5.0:
                        continue

                active_positions[sym] = {
                    "strategy_origin": chosen_strat,
                    "strat_config": strat_cfg,
                    "side": sig_side,
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
        """Calculates portfolio summary metrics."""
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

        # Strategy origin breakdown
        strat_counts = df_trades["strategy_origin"].value_counts().to_dict()

        return {
            "portfolio_configuration": "+".join(sorted(self.strategy_engines.keys())),
            "calendar_days_count": len(df_daily),
            "executed_trades_count": len(df_trades),
            "strategy_trades_breakdown": strat_counts,
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
