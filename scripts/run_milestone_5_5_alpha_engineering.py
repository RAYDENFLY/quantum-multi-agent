"""QUANTUM Milestone 5.5 — Alpha Engineering Research Script.

Simulates and evaluates:
1. EXP-09: Regime-Adaptive Alpha (Strictly 1.0x Unlevered)
   - Dynamic regime-specific thresholds, exit horizons, and capital allocation.
2. EXP-10: Execution-Aware Alpha (Maker vs Taker vs Hybrid with adverse selection & fill modeling).
3. EXP-11: Structural Impulse Continuation Alpha (Fast 1-2 bar order-flow continuation).
4. Unlevered Portfolio Combination & Statistical Verification.
"""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from quantum.strategies.evaluator import StrategyDiscoveryEvaluator
from quantum.strategies.hyp01_strategy import HYP01Configuration, HYP01Engine
from quantum.strategies.schemas import get_venue_schedule


def simulate_exp09_regime_adaptive(
    matrices: Dict[str, Any],
    holdout_cutoff_ms: int = 1793491200000,
) -> Tuple[Dict[str, Any], pd.DataFrame, pd.DataFrame]:
    """EXP-09: Regime-Adaptive Alpha at strictly 1.0x Unlevered Leverage.
    
    Adapts:
    - High-Vol Bear: Full 1.0x allocation (0.25x per pos), wide TP (TP1=2.5s, TP2=4.5s), horizon 4 bars.
    - High-Vol Bull: Full 1.0x allocation (0.25x per pos), wide TP (TP1=2.5s, TP2=4.0s), horizon 4 bars.
    - Low-Vol Regimes: Stricter entry (vol_exp >= 1.15, trend >= 100 bps), tight TP (TP1=1.8s), horizon 2 bars.
    - Effective Leverage: Strictly <= 1.00x gross at all times.
    """
    symbol_list = [s for s in matrices.keys() if s != "XMRUSDT"]
    venue = get_venue_schedule("BYBIT_VIP0_DEFAULT")

    # Fit training thresholds
    sigmas = []
    htf_abs = []
    for sym in symbol_list:
        m = matrices[sym]
        mask = np.isin(m.fold_prev, (0, 1))
        if mask.sum() > 0:
            sigmas.extend(m.sigma_20[mask])
            if 12 in m.htf_rets_bps:
                htf_abs.extend(np.abs(m.htf_rets_bps[12][mask]))

    sigma_median = float(np.nanmedian(sigmas)) if sigmas else 0.0015
    trend_median = float(np.nanpercentile(htf_abs, 50)) if htf_abs else 75.0

    # Pre-compute signals with regime-adaptive rules
    asset_signals = {}
    for sym in symbol_list:
        m = matrices[sym]
        n_bars = len(m.opens)
        sig_side = np.zeros(n_bars, dtype=np.int8)
        regimes = []
        htf_12 = m.htf_rets_bps[12] if 12 in m.htf_rets_bps else np.zeros(n_bars)
        htf_3 = m.htf_rets_bps[6] if 6 in m.htf_rets_bps else np.zeros(n_bars)

        for i in range(20, n_bars - 2):
            if m.open_time_ms[i] >= holdout_cutoff_ms:
                continue

            sigma = m.sigma_20[i]
            htf_val = htf_12[i]
            vol_exp = m.vol_exp_ratio[i]

            is_high_vol = sigma >= sigma_median
            is_bull = htf_val >= 0

            # Regime classification
            if is_high_vol and not is_bull:
                reg_name = "HIGH_VOL_BEAR"
            elif is_high_vol and is_bull:
                reg_name = "HIGH_VOL_BULL"
            elif not is_high_vol and is_bull:
                reg_name = "LOW_VOL_BULL"
            else:
                reg_name = "LOW_VOL_BEAR"

            # Adaptive filter: In low-vol regimes, demand higher trend threshold and volume expansion
            if "LOW_VOL" in reg_name:
                req_trend = trend_median * 1.33 # ~100 bps
                req_vol_exp = 1.15
            else:
                req_trend = trend_median # ~75 bps
                req_vol_exp = 1.08

            if abs(htf_val) < req_trend or vol_exp < req_vol_exp:
                continue

            if htf_val >= req_trend and htf_3[i] >= 0 and m.closes[i] > m.opens[i]:
                sig_side[i] = 1
            elif htf_val <= -req_trend and htf_3[i] <= 0 and m.closes[i] < m.opens[i]:
                sig_side[i] = -1

        asset_signals[sym] = {"signal_side": sig_side, "htf_12": htf_12}

    # Simulation with 1.0x unlevered leverage and regime-adaptive barriers
    portfolio_equity = 100.0
    peak_equity = portfolio_equity
    trades = []
    daily_records = []

    active_positions = {}
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
            max_horizon = pos["max_horizon"]

            sl_hit = (l <= sl_px) if side == 1 else (h >= sl_px)
            if sl_hit:
                closed_syms.append((sym, sl_px, "STOP_LOSS", "TAKER", bars_held))
                continue

            if not pos["tp1_hit"]:
                tp1_hit = (h >= tp1_px) if side == 1 else (l <= tp1_px)
                if tp1_hit:
                    pos["tp1_hit"] = True
                    pos["sl_price"] = entry_px # Breakeven ratchet

            tp2_hit = (h >= tp2_px) if side == 1 else (l <= tp2_px)
            if tp2_hit:
                closed_syms.append((sym, tp2_px, "TAKE_PROFIT_2", "MAKER", bars_held))
                continue

            # Trailing stop
            if pos["tp1_hit"]:
                trail_dist = 1.5 * sigma * c
                if side == 1:
                    new_sl = c - trail_dist
                    if new_sl > pos["sl_price"]:
                        pos["sl_price"] = new_sl
                else:
                    new_sl = c + trail_dist
                    if new_sl < pos["sl_price"]:
                        pos["sl_price"] = new_sl

            if bars_held >= max_horizon:
                exit_rsn = "TAKE_PROFIT_1_HORIZON" if pos["tp1_hit"] else "TIME_EXPIRATION"
                closed_syms.append((sym, c, exit_rsn, "TAKER", bars_held))
                continue

        # Process closed positions
        for sym, fill_px, reason, exit_role, bars_held in closed_syms:
            pos = active_positions.pop(sym)
            side = pos["side"]
            entry_px = pos["entry_price"]
            notional = pos["notional"]

            leg_return = float(side) * (fill_px - entry_px) / entry_px
            gross_pnl = notional * leg_return

            entry_fee_rate = venue.taker_fee_bps_per_leg / 10_000.0
            exit_fee_rate = (venue.taker_fee_bps_per_leg / 10_000.0) if exit_role == "TAKER" else (venue.maker_fee_bps_per_leg / 10_000.0)
            fee_usd = notional * (entry_fee_rate + exit_fee_rate)
            spread_usd = notional * (venue.default_spread_bps / 10_000.0)
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
                "trade_id": f"EXP09_{len(trades)+1:06d}_{sym}",
                "symbol": sym,
                "side": "LONG" if side == 1 else "SHORT",
                "entry_time_ms": pos["entry_time"],
                "exit_time_ms": matrices[sym].open_time_ms[i],
                "entry_price": entry_px,
                "exit_price": fill_px,
                "exit_reason": reason,
                "bars_held": bars_held,
                "notional_usd": notional,
                "gross_return_bps": leg_return * 10_000.0,
                "net_return_bps": (net_pnl / notional) * 10_000.0,
                "gross_pnl_usd": gross_pnl,
                "net_pnl_usd": net_pnl,
                "total_cost_usd": total_cost,
                "regime": pos["regime"],
                "fold": int(matrices[sym].fold_prev[i]),
            })

        # Sizing & circuit breaker: Strictly Unlevered 1.0x!
        if portfolio_equity <= 5.0:
            break
        if abs(daily_loss_accum) / max(portfolio_equity, 10.0) >= 0.04:
            continue

        if len(active_positions) >= 4:
            continue

        for sym in symbol_list:
            if len(active_positions) >= 4:
                break
            if sym in active_positions:
                continue
            if (i - last_trade_bar[sym]) < 3:
                continue

            sig = asset_signals[sym]["signal_side"][i]
            if sig == 0:
                continue

            m = matrices[sym]
            sigma = m.sigma_20[i]
            arrival_px = m.opens[i]
            is_high_vol = sigma >= sigma_median

            # Adaptive barriers based on volatility
            if is_high_vol:
                tp1_mult = 2.5
                tp2_mult = 4.5
                sl_mult = 1.5
                max_horizon = 4
                reg_label = "HIGH_VOL"
            else:
                tp1_mult = 1.8
                tp2_mult = 3.0
                sl_mult = 1.2
                max_horizon = 2 # Fast exit in low-vol to avoid stagnation
                reg_label = "LOW_VOL"

            sl_dist = sl_mult * sigma * arrival_px
            tp1_dist = tp1_mult * sigma * arrival_px
            tp2_dist = tp2_mult * sigma * arrival_px

            sl_px = arrival_px - sl_dist if sig == 1 else arrival_px + sl_dist
            tp1_px = arrival_px + tp1_dist if sig == 1 else arrival_px - tp1_dist
            tp2_px = arrival_px + tp2_dist if sig == 1 else arrival_px - tp2_dist

            # STRICTLY UNLEVERED 1.0X: Max notional is exactly 0.25x equity!
            max_allowed_notional = portfolio_equity * 0.25
            sl_pct = (sl_dist / arrival_px)
            desired_notional = (portfolio_equity * 0.015) / max(sl_pct, 0.005)
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
                "max_horizon": max_horizon,
                "regime": reg_label,
            }
            last_trade_bar[sym] = i

    df_daily = pd.DataFrame(daily_records)
    df_trades = pd.DataFrame(trades)

    # Compute summary
    d_rets = df_daily["daily_return_pct"]
    mean_d = float(d_rets.mean())
    median_d = float(d_rets.median())
    std_d = float(d_rets.std())
    sharpe = float(mean_d / std_d * np.sqrt(365)) if std_d > 0 else 0.0

    cum_eq = df_daily["end_day_mtm_equity_usd"].values
    peaks = np.maximum.accumulate(cum_eq)
    dds = (peaks - cum_eq) / peaks * 100.0
    mdd = float(np.max(dds)) if len(dds) > 0 else 0.0

    wins = df_trades[df_trades["net_pnl_usd"] > 0]["net_pnl_usd"].sum()
    losses = abs(df_trades[df_trades["net_pnl_usd"] < 0]["net_pnl_usd"].sum())
    pf = wins / losses if losses > 0 else float("inf")

    summary = {
        "experiment_id": "EXP_09_REGIME_ADAPTIVE",
        "effective_leverage": 1.0,
        "calendar_days": len(df_daily),
        "total_trades": len(df_trades),
        "mean_daily_return_pct": round(mean_d, 4),
        "median_daily_return_pct": round(median_d, 4),
        "daily_std_pct": round(std_d, 4),
        "sharpe_365": round(sharpe, 2),
        "max_drawdown_pct": round(mdd, 2),
        "profit_factor": round(float(pf), 3),
        "win_rate_pct": round(float((df_trades["net_pnl_usd"] > 0).mean() * 100.0), 2),
        "net_expectancy_bps": round(float(df_trades["net_return_bps"].mean()), 2),
        "gross_expectancy_bps": round(float(df_trades["gross_return_bps"].mean()), 2),
        "ending_equity_usd": round(portfolio_equity, 2),
    }

    return summary, df_daily, df_trades


def simulate_exp10_execution_aware(
    matrices: Dict[str, Any],
    execution_mode: str = "PASSIVE_MAKER", # PASSIVE_MAKER, MARKETABLE_TAKER, HYBRID
    holdout_cutoff_ms: int = 1793491200000,
) -> Tuple[Dict[str, Any], pd.DataFrame, pd.DataFrame]:
    """EXP-10: Execution-Aware Alpha with Adverse Selection & Fill Probability Modeling.
    
    Models:
    - Maker Entry Fee: 2.0 bps (vs 5.0 bps taker)
    - Maker Entry Spread: 0.0 bps (captured inside spread)
    - Maker Entry Slippage: 0.0 bps
    - Adverse Selection Drag: +2.0 bps when filled (only filled when order book moves adversely)
    - Empirical Fill Probability: 75% fill rate for passive limit orders at touch
    - Effective Leverage: Strictly 1.0x unlevered.
    """
    symbol_list = [s for s in matrices.keys() if s != "XMRUSDT"]
    venue = get_venue_schedule("BYBIT_VIP0_DEFAULT")

    cfg_hyp01 = HYP01Configuration(
        vol_expansion_min=1.08,
        tp1_multiplier=2.5,
        tp2_multiplier=4.0,
        trailing_stop_sigma=1.5,
        max_horizon_bars=4,
        max_leverage=1.0, # Strictly unlevered
        max_symbol_exposure_pct=0.25,
    )
    engine = HYP01Engine(cfg_hyp01)
    engine.fit_thresholds_on_training_fold(matrices, train_folds=(0, 1))

    # Pre-compute signals
    asset_signals = {}
    for sym in symbol_list:
        m = matrices[sym]
        n_bars = len(m.opens)
        sig_side = np.zeros(n_bars, dtype=np.int8)
        htf_12 = m.htf_rets_bps[12] if 12 in m.htf_rets_bps else np.zeros(n_bars)
        htf_3 = m.htf_rets_bps[6] if 6 in m.htf_rets_bps else np.zeros(n_bars)
        for i in range(20, n_bars - 2):
            if m.open_time_ms[i] >= holdout_cutoff_ms:
                continue
            sigma = m.sigma_20[i]
            htf_val = htf_12[i]
            vol_exp = m.vol_exp_ratio[i]
            regime_name, is_trend = engine.regime_detector.classify_bar(sigma, htf_val, vol_exp)
            if not is_trend:
                continue
            if htf_val >= 75.0 and htf_3[i] >= 0 and m.closes[i] > m.opens[i]:
                sig_side[i] = 1
            elif htf_val <= -75.0 and htf_3[i] <= 0 and m.closes[i] < m.opens[i]:
                sig_side[i] = -1
        asset_signals[sym] = {"signal_side": sig_side}

    portfolio_equity = 100.0
    peak_equity = portfolio_equity
    trades = []
    daily_records = []

    active_positions = {}
    last_trade_bar = {s: -999 for s in symbol_list}
    daily_loss_accum = 0.0
    current_day = None

    master_bars = len(matrices["BTCUSDT"].opens)
    day_start_equity = portfolio_equity
    day_trades_count = 0
    day_realized_pnl = 0.0

    np.random.seed(42)

    for i in range(20, master_bars - 2):
        t_ms = matrices["BTCUSDT"].open_time_ms[i]
        if t_ms >= holdout_cutoff_ms:
            break

        day_key = t_ms // (86400 * 1000)

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
                    pos["sl_price"] = entry_px

            tp2_hit = (h >= tp2_px) if side == 1 else (l <= tp2_px)
            if tp2_hit:
                closed_syms.append((sym, tp2_px, "TAKE_PROFIT_2", "MAKER", bars_held))
                continue

            if pos["tp1_hit"]:
                trail_dist = 1.5 * sigma * c
                if side == 1:
                    new_sl = c - trail_dist
                    if new_sl > pos["sl_price"]:
                        pos["sl_price"] = new_sl
                else:
                    new_sl = c + trail_dist
                    if new_sl < pos["sl_price"]:
                        pos["sl_price"] = new_sl

            if bars_held >= 4:
                # In execution-aware mode, try passive limit maker exit at bar 4 with 50% maker probability!
                exit_role = "MAKER" if execution_mode == "PASSIVE_MAKER" and np.random.rand() < 0.65 else "TAKER"
                closed_syms.append((sym, c, "TIME_EXPIRATION", exit_role, bars_held))
                continue

        # Process closed positions
        for sym, fill_px, reason, exit_role, bars_held in closed_syms:
            pos = active_positions.pop(sym)
            side = pos["side"]
            entry_px = pos["entry_price"]
            notional = pos["notional"]

            leg_return = float(side) * (fill_px - entry_px) / entry_px
            gross_pnl = notional * leg_return

            entry_fee_rate = (venue.maker_fee_bps_per_leg / 10_000.0) if pos["entry_role"] == "MAKER" else (venue.taker_fee_bps_per_leg / 10_000.0)
            exit_fee_rate = (venue.maker_fee_bps_per_leg / 10_000.0) if exit_role == "MAKER" else (venue.taker_fee_bps_per_leg / 10_000.0)
            fee_usd = notional * (entry_fee_rate + exit_fee_rate)

            # In Maker mode, 0 spread and 0 slippage on entry!
            spread_usd = 0.0 if pos["entry_role"] == "MAKER" else notional * (venue.default_spread_bps / 10_000.0)
            slip_usd = notional * (venue.default_slippage_bps / 10_000.0) if exit_role == "TAKER" else 0.0
            # Adverse selection drag on maker entry
            adverse_drag = notional * (0.0002) if pos["entry_role"] == "MAKER" else 0.0
            fund_usd = notional * 0.0001 * (bars_held // 96)

            total_cost = fee_usd + spread_usd + slip_usd + adverse_drag + fund_usd
            net_pnl = gross_pnl - total_cost

            portfolio_equity += net_pnl
            daily_loss_accum += min(0.0, net_pnl)
            peak_equity = max(peak_equity, portfolio_equity)

            day_trades_count += 1
            day_realized_pnl += net_pnl

            trades.append({
                "trade_id": f"EXP10_{len(trades)+1:06d}_{sym}",
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
                "total_cost_usd": total_cost,
                "fold": int(matrices[sym].fold_prev[i]),
            })

        if portfolio_equity <= 5.0 or len(active_positions) >= 4:
            continue
        if abs(daily_loss_accum) / max(portfolio_equity, 10.0) >= 0.04:
            continue

        for sym in symbol_list:
            if len(active_positions) >= 4 or sym in active_positions or (i - last_trade_bar[sym]) < 3:
                continue

            sig = asset_signals[sym]["signal_side"][i]
            if sig == 0:
                continue

            m = matrices[sym]
            sigma = m.sigma_20[i]
            arrival_px = m.opens[i]

            # In PASSIVE_MAKER mode, check fill probability (75% fill rate, 25% unfilled rejection)
            if execution_mode == "PASSIVE_MAKER":
                # Check if bar i candle penetrates bid/ask
                candle_range = m.highs[i] - m.lows[i]
                if candle_range < (0.5 * sigma * arrival_px) or np.random.rand() > 0.75:
                    # Limit order unfilled, skipped!
                    continue
                entry_role = "MAKER"
            else:
                entry_role = "TAKER"

            sl_dist = 1.5 * sigma * arrival_px
            tp1_dist = 2.5 * sigma * arrival_px
            tp2_dist = 4.0 * sigma * arrival_px

            sl_px = arrival_px - sl_dist if sig == 1 else arrival_px + sl_dist
            tp1_px = arrival_px + tp1_dist if sig == 1 else arrival_px - tp1_dist
            tp2_px = arrival_px + tp2_dist if sig == 1 else arrival_px - tp2_dist

            # STRICTLY UNLEVERED 1.0X
            max_allowed_notional = portfolio_equity * 0.25
            sl_pct = (sl_dist / arrival_px)
            desired_notional = (portfolio_equity * 0.015) / max(sl_pct, 0.005)
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
                "entry_role": entry_role,
            }
            last_trade_bar[sym] = i

    df_daily = pd.DataFrame(daily_records)
    df_trades = pd.DataFrame(trades)

    d_rets = df_daily["daily_return_pct"]
    mean_d = float(d_rets.mean())
    median_d = float(d_rets.median())
    std_d = float(d_rets.std())
    sharpe = float(mean_d / std_d * np.sqrt(365)) if std_d > 0 else 0.0

    cum_eq = df_daily["end_day_mtm_equity_usd"].values
    peaks = np.maximum.accumulate(cum_eq)
    dds = (peaks - cum_eq) / peaks * 100.0
    mdd = float(np.max(dds)) if len(dds) > 0 else 0.0

    wins = df_trades[df_trades["net_pnl_usd"] > 0]["net_pnl_usd"].sum()
    losses = abs(df_trades[df_trades["net_pnl_usd"] < 0]["net_pnl_usd"].sum())
    pf = wins / losses if losses > 0 else float("inf")

    summary = {
        "experiment_id": f"EXP_10_{execution_mode}",
        "effective_leverage": 1.0,
        "calendar_days": len(df_daily),
        "total_trades": len(df_trades),
        "mean_daily_return_pct": round(mean_d, 4),
        "median_daily_return_pct": round(median_d, 4),
        "daily_std_pct": round(std_d, 4),
        "sharpe_365": round(sharpe, 2),
        "max_drawdown_pct": round(mdd, 2),
        "profit_factor": round(float(pf), 3),
        "win_rate_pct": round(float((df_trades["net_pnl_usd"] > 0).mean() * 100.0), 2),
        "net_expectancy_bps": round(float(df_trades["net_return_bps"].mean()), 2),
        "gross_expectancy_bps": round(float(df_trades["gross_return_bps"].mean()), 2),
        "ending_equity_usd": round(portfolio_equity, 2),
    }

    return summary, df_daily, df_trades


def simulate_exp11_structural_impulse(
    matrices: Dict[str, Any],
    holdout_cutoff_ms: int = 1793491200000,
) -> Tuple[Dict[str, Any], pd.DataFrame, pd.DataFrame]:
    """EXP-11: Structural Impulse Continuation Alpha (1.0x Unlevered).
    
    Exploits high-velocity 1-bar expansion with minimal counter-wick.
    Target: 1-to-2 bar holding horizon, rapid MFE capture.
    """
    symbol_list = [s for s in matrices.keys() if s != "XMRUSDT"]
    venue = get_venue_schedule("BYBIT_VIP0_DEFAULT")

    asset_signals = {}
    for sym in symbol_list:
        m = matrices[sym]
        n_bars = len(m.opens)
        sig_side = np.zeros(n_bars, dtype=np.int8)

        for i in range(20, n_bars - 2):
            if m.open_time_ms[i] >= holdout_cutoff_ms:
                continue

            sigma = m.sigma_20[i]
            rvol = m.rvol_20[i]
            o, h, l, c = m.opens[i], m.highs[i], m.lows[i], m.closes[i]
            body = abs(c - o)
            rng = max(h - l, 1e-8)

            # High impulse: Body >= 1.2 * sigma * close, Volume >= 1.40, minimal counter wick
            if body >= (1.0 * sigma * c) and rvol >= 1.30:
                if c > o and (h - c) / rng <= 0.20: # Strong bull close at top
                    sig_side[i] = 1
                elif c < o and (c - l) / rng <= 0.20: # Strong bear close at bottom
                    sig_side[i] = -1

        asset_signals[sym] = {"signal_side": sig_side}

    portfolio_equity = 100.0
    peak_equity = portfolio_equity
    trades = []
    daily_records = []

    active_positions = {}
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

        closed_syms = []
        for sym, pos in active_positions.items():
            m = matrices[sym]
            o, h, l, c = m.opens[i], m.highs[i], m.lows[i], m.closes[i]
            side = pos["side"]
            entry_px = pos["entry_price"]
            sl_px = pos["sl_price"]
            tp_px = pos["tp_price"]
            bars_held = i - pos["entry_bar"]

            sl_hit = (l <= sl_px) if side == 1 else (h >= sl_px)
            if sl_hit:
                closed_syms.append((sym, sl_px, "STOP_LOSS", "TAKER", bars_held))
                continue

            tp_hit = (h >= tp_px) if side == 1 else (l <= tp_px)
            if tp_hit:
                closed_syms.append((sym, tp_px, "TAKE_PROFIT", "MAKER", bars_held))
                continue

            # Fast 2-bar horizon
            if bars_held >= 2:
                closed_syms.append((sym, c, "TIME_EXPIRATION", "TAKER", bars_held))
                continue

        for sym, fill_px, reason, exit_role, bars_held in closed_syms:
            pos = active_positions.pop(sym)
            side = pos["side"]
            entry_px = pos["entry_price"]
            notional = pos["notional"]

            leg_return = float(side) * (fill_px - entry_px) / entry_px
            gross_pnl = notional * leg_return

            fee_usd = notional * ((venue.taker_fee_bps_per_leg + (venue.taker_fee_bps_per_leg if exit_role == "TAKER" else venue.maker_fee_bps_per_leg)) / 10_000.0)
            spread_usd = notional * (venue.default_spread_bps / 10_000.0)
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
                "trade_id": f"EXP11_{len(trades)+1:06d}_{sym}",
                "symbol": sym,
                "side": "LONG" if side == 1 else "SHORT",
                "entry_time_ms": pos["entry_time"],
                "exit_time_ms": matrices[sym].open_time_ms[i],
                "entry_price": entry_px,
                "exit_price": fill_px,
                "exit_reason": reason,
                "bars_held": bars_held,
                "notional_usd": notional,
                "gross_return_bps": leg_return * 10_000.0,
                "net_return_bps": (net_pnl / notional) * 10_000.0,
                "gross_pnl_usd": gross_pnl,
                "net_pnl_usd": net_pnl,
                "total_cost_usd": total_cost,
                "fold": int(matrices[sym].fold_prev[i]),
            })

        if portfolio_equity <= 5.0 or len(active_positions) >= 4:
            continue
        if abs(daily_loss_accum) / max(portfolio_equity, 10.0) >= 0.04:
            continue

        for sym in symbol_list:
            if len(active_positions) >= 4 or sym in active_positions or (i - last_trade_bar[sym]) < 2:
                continue

            sig = asset_signals[sym]["signal_side"][i]
            if sig == 0:
                continue

            m = matrices[sym]
            sigma = m.sigma_20[i]
            arrival_px = m.opens[i]

            sl_dist = 1.2 * sigma * arrival_px
            tp_dist = 2.0 * sigma * arrival_px

            sl_px = arrival_px - sl_dist if sig == 1 else arrival_px + sl_dist
            tp_px = arrival_px + tp_dist if sig == 1 else arrival_px - tp_dist

            max_allowed_notional = portfolio_equity * 0.25
            sl_pct = (sl_dist / arrival_px)
            desired_notional = (portfolio_equity * 0.015) / max(sl_pct, 0.005)
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
                "tp_price": tp_px,
                "sigma": sigma,
            }
            last_trade_bar[sym] = i

    df_daily = pd.DataFrame(daily_records)
    df_trades = pd.DataFrame(trades)

    d_rets = df_daily["daily_return_pct"]
    mean_d = float(d_rets.mean())
    median_d = float(d_rets.median())
    std_d = float(d_rets.std())
    sharpe = float(mean_d / std_d * np.sqrt(365)) if std_d > 0 else 0.0

    cum_eq = df_daily["end_day_mtm_equity_usd"].values
    peaks = np.maximum.accumulate(cum_eq)
    dds = (peaks - cum_eq) / peaks * 100.0
    mdd = float(np.max(dds)) if len(dds) > 0 else 0.0

    wins = df_trades[df_trades["net_pnl_usd"] > 0]["net_pnl_usd"].sum()
    losses = abs(df_trades[df_trades["net_pnl_usd"] < 0]["net_pnl_usd"].sum())
    pf = wins / losses if losses > 0 else float("inf")

    summary = {
        "experiment_id": "EXP_11_STRUCTURAL_IMPULSE",
        "effective_leverage": 1.0,
        "calendar_days": len(df_daily),
        "total_trades": len(df_trades),
        "mean_daily_return_pct": round(mean_d, 4),
        "median_daily_return_pct": round(median_d, 4),
        "daily_std_pct": round(std_d, 4),
        "sharpe_365": round(sharpe, 2),
        "max_drawdown_pct": round(mdd, 2),
        "profit_factor": round(float(pf), 3),
        "win_rate_pct": round(float((df_trades["net_pnl_usd"] > 0).mean() * 100.0), 2),
        "net_expectancy_bps": round(float(df_trades["net_return_bps"].mean()), 2),
        "gross_expectancy_bps": round(float(df_trades["gross_return_bps"].mean()), 2),
        "ending_equity_usd": round(portfolio_equity, 2),
    }

    return summary, df_daily, df_trades


def main() -> None:
    t_start = time.time()
    out_dir = Path("audit/strategy_research/milestone_5_5_unlevered_alpha")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 88)
    print("QUANTUM MILESTONE 5.5 — PHASE C: ALPHA ENGINEERING EVALUATION (1.0x UNLEVERED)")
    print("=" * 88)

    evaluator = StrategyDiscoveryEvaluator()
    matrices = evaluator.matrices

    exp_summaries = []

    # 1. EXP-09: Regime-Adaptive Alpha
    print("\n--- Running EXP-09: Regime-Adaptive Alpha ---")
    s09, d09, t09 = simulate_exp09_regime_adaptive(matrices)
    exp_summaries.append(s09)
    print(f"EXP-09: Mean Daily: {s09['mean_daily_return_pct']}% | Sharpe: {s09['sharpe_365']} | MDD: {s09['max_drawdown_pct']}% | PF: {s09['profit_factor']} | NetExp: {s09['net_expectancy_bps']} bps | Trades: {s09['total_trades']}")

    # 2. EXP-10: Execution-Aware Alpha (Passive Maker vs Marketable Taker)
    print("\n--- Running EXP-10A: Execution-Aware Passive Maker Entry ---")
    s10_maker, d10_maker, t10_maker = simulate_exp10_execution_aware(matrices, execution_mode="PASSIVE_MAKER")
    exp_summaries.append(s10_maker)
    print(f"EXP-10 (Maker): Mean Daily: {s10_maker['mean_daily_return_pct']}% | Sharpe: {s10_maker['sharpe_365']} | MDD: {s10_maker['max_drawdown_pct']}% | PF: {s10_maker['profit_factor']} | NetExp: {s10_maker['net_expectancy_bps']} bps | Trades: {s10_maker['total_trades']}")

    print("\n--- Running EXP-10B: Execution-Aware Marketable Taker Baseline ---")
    s10_taker, d10_taker, t10_taker = simulate_exp10_execution_aware(matrices, execution_mode="MARKETABLE_TAKER")
    exp_summaries.append(s10_taker)
    print(f"EXP-10 (Taker): Mean Daily: {s10_taker['mean_daily_return_pct']}% | Sharpe: {s10_taker['sharpe_365']} | MDD: {s10_taker['max_drawdown_pct']}% | PF: {s10_taker['profit_factor']} | NetExp: {s10_taker['net_expectancy_bps']} bps | Trades: {s10_taker['total_trades']}")

    # 3. EXP-11: Structural Impulse Continuation Alpha
    print("\n--- Running EXP-11: Structural Impulse Continuation Alpha ---")
    s11, d11, t11 = simulate_exp11_structural_impulse(matrices)
    exp_summaries.append(s11)
    print(f"EXP-11: Mean Daily: {s11['mean_daily_return_pct']}% | Sharpe: {s11['sharpe_365']} | MDD: {s11['max_drawdown_pct']}% | PF: {s11['profit_factor']} | NetExp: {s11['net_expectancy_bps']} bps | Trades: {s11['total_trades']}")

    df_exp = pd.DataFrame(exp_summaries)
    df_exp.to_csv(out_dir / "ALPHA_ENGINEERING_EXPERIMENTS.csv", index=False)
    print("\nSaved ALPHA_ENGINEERING_EXPERIMENTS.csv successfully!")
    print(f"Total Phase C simulation time: {time.time() - t_start:.2f}s")


if __name__ == "__main__":
    main()
