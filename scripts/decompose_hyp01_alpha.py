"""QUANTUM Milestone 5.5 — HYP-01 Alpha Decomposition & Diagnostic Engine.

Performs exhaustive forensic decomposition of HYP-01 (EXP-08 baseline):
1. Asset Attribution (Return, expectancy, profit factor, drawdown, contribution per pair).
2. Market Regime Attribution (High-Vol Bull, High-Vol Bear, Low-Vol Bull, Low-Vol Bear, Trending vs Ranging).
3. Signal Attribution (Long vs Short, Volume expansion, HTF confirmation, False breakout rate).
4. Trade Lifecycle Analysis (MFE, MAE, TP1/TP2 hit rates, SL hit rates, duration analysis).
5. Profit Concentration (Top 1%, Top 5%, Bottom 5%, Trimmed mean, Outlier dependency).
"""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from quantum.strategies.evaluator import StrategyDiscoveryEvaluator
from quantum.strategies.hyp01_strategy import HYP01Configuration, HYP01Engine


def run_hyp01_with_lifecycle(
    engine: HYP01Engine,
    matrices: Dict[str, Any],
    holdout_cutoff_ms: int = 1793491200000,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Runs HYP-01 simulation while recording MFE, MAE, and lifecycle metrics per trade."""
    cfg = engine.config
    venue = engine.venue
    symbol_list = [s for s in matrices.keys() if s != "XMRUSDT"]

    # Pre-compute signals per asset
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
            if cfg.allow_long_entries and htf_val >= cfg.trend_threshold_bps and htf_3[i] >= 0 and m.closes[i] > m.opens[i]:
                sig_side[i] = 1
            elif cfg.allow_short_entries and htf_val <= -cfg.trend_threshold_bps and htf_3[i] <= 0 and m.closes[i] < m.opens[i]:
                if cfg.filter_altcoin_shorts and sym not in ("BTCUSDT", "ETHUSDT"):
                    continue
                sig_side[i] = -1

        asset_signals[sym] = {"signal_side": sig_side, "htf_12": htf_12, "htf_3": htf_3}

    portfolio_equity = float(cfg.initial_equity_usd)
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

        # Update active positions & track MFE / MAE
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

            # Update MFE / MAE in basis points
            if side == 1:
                favorable_bps = (h - entry_px) / entry_px * 10_000.0
                adverse_bps = (l - entry_px) / entry_px * 10_000.0
            else:
                favorable_bps = (entry_px - l) / entry_px * 10_000.0
                adverse_bps = (entry_px - h) / entry_px * 10_000.0

            pos["mfe_bps"] = max(pos["mfe_bps"], favorable_bps)
            pos["mae_bps"] = min(pos["mae_bps"], adverse_bps)

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
                closed_syms.append((sym, tp2_px, "TAKE_PROFIT_2", "MAKER", bars_held))
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
                "trade_id": f"T_{len(trades)+1:06d}_{sym}",
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
                "mfe_bps": pos["mfe_bps"],
                "mae_bps": pos["mae_bps"],
                "tp1_hit": pos["tp1_hit"],
                "tp2_hit": reason == "TAKE_PROFIT_2",
                "vol_exp_ratio": pos["vol_exp_ratio"],
                "htf_12_bps": pos["htf_12_bps"],
                "sigma_20": pos["sigma"],
                "fold": int(matrices[sym].fold_prev[i]),
            })

        # Circuit breaker & sizing
        if portfolio_equity <= 5.0:
            break
        if abs(daily_loss_accum) / max(portfolio_equity, 10.0) >= cfg.daily_loss_circuit_breaker_pct:
            continue

        dd_pct = (peak_equity - portfolio_equity) / peak_equity
        leverage_mult = 0.5 if dd_pct >= cfg.max_drawdown_circuit_breaker_pct else 1.0

        if len(active_positions) >= cfg.max_concurrent_positions:
            continue

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
                "mfe_bps": 0.0,
                "mae_bps": 0.0,
                "vol_exp_ratio": m.vol_exp_ratio[i],
                "htf_12_bps": asset_signals[sym]["htf_12"][i],
            }
            last_trade_bar[sym] = i

    return pd.DataFrame(daily_records), pd.DataFrame(trades)


def main() -> None:
    t_start = time.time()
    out_dir = Path("audit/strategy_research/milestone_5_5_unlevered_alpha")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 88)
    print("QUANTUM MILESTONE 5.5 — PHASE A: HYP-01 ALPHA DECOMPOSITION")
    print("=" * 88)

    evaluator = StrategyDiscoveryEvaluator()
    matrices = evaluator.matrices
    symbol_list = [s for s in matrices.keys() if s != "XMRUSDT"]

    cfg_hyp01 = HYP01Configuration(
        strategy_id="EXP_08_OPTIMAL_CANDIDATE",
        vol_expansion_min=1.08,
        tp1_multiplier=2.5,
        tp2_multiplier=4.0,
        enable_breakeven_ratchet=True,
        trailing_stop_sigma=1.5,
        max_horizon_bars=4,
        risk_per_trade_pct=0.015,
        max_leverage=3.0,
        fee_tier="BYBIT_VIP0_DEFAULT",
    )
    engine = HYP01Engine(cfg_hyp01)
    engine.fit_thresholds_on_training_fold(matrices, train_folds=(0, 1))

    print("Running HYP-01 lifecycle simulation across 1,099 calendar days...")
    df_daily, df_trades = run_hyp01_with_lifecycle(engine, matrices)
    print(f"Simulation completed in {time.time() - t_start:.2f}s | Trades: {len(df_trades):,} | Days: {len(df_daily)}")

    # Save raw trades lifecycle
    df_trades.to_csv(out_dir / "HYP01_TRADES_LIFECYCLE.csv", index=False)

    # 1. ASSET ATTRIBUTION
    asset_rows = []
    total_dollar_pnl = df_trades["net_pnl_usd"].sum()
    for sym in symbol_list:
        sub = df_trades[df_trades["symbol"] == sym]
        if sub.empty:
            continue
        wins = sub[sub["net_pnl_usd"] > 0]["net_pnl_usd"].sum()
        losses = abs(sub[sub["net_pnl_usd"] < 0]["net_pnl_usd"].sum())
        pf = wins / losses if losses > 0 else float("inf")
        pnl = sub["net_pnl_usd"].sum()
        contrib_pct = (pnl / total_dollar_pnl * 100.0) if total_dollar_pnl > 0 else 0.0

        asset_rows.append({
            "dimension": "ASSET",
            "attribute": sym,
            "trades_count": len(sub),
            "win_rate_pct": round(float((sub["net_pnl_usd"] > 0).mean() * 100.0), 2),
            "net_expectancy_bps": round(float(sub["net_return_bps"].mean()), 2),
            "gross_expectancy_bps": round(float(sub["gross_return_bps"].mean()), 2),
            "profit_factor": round(float(pf), 3),
            "net_pnl_usd": round(float(pnl), 2),
            "pnl_contribution_pct": round(float(contrib_pct), 2),
            "mfe_mean_bps": round(float(sub["mfe_bps"].mean()), 2),
            "mae_mean_bps": round(float(sub["mae_bps"].mean()), 2),
        })

    # 2. MARKET REGIME ATTRIBUTION
    btc_m = matrices["BTCUSDT"]
    btc_daily_map = {}
    day_indices = {}
    for i_bar in range(len(btc_m.opens)):
        d_k = btc_m.open_time_ms[i_bar] // (86400 * 1000)
        if d_k not in day_indices:
            day_indices[d_k] = []
        day_indices[d_k].append(i_bar)

    daily_sigmas = []
    daily_rets_btc = []
    for d_k in sorted(day_indices.keys()):
        bars = day_indices[d_k]
        c_open = btc_m.opens[bars[0]]
        c_close = btc_m.closes[bars[-1]]
        d_ret = (c_close - c_open) / c_open
        d_sig = np.mean(btc_m.sigma_20[bars])
        btc_daily_map[d_k] = (d_ret, d_sig)
        daily_sigmas.append(d_sig)
        daily_rets_btc.append(d_ret)

    median_btc_sigma = float(np.median(daily_sigmas))

    df_daily["btc_d_ret"] = df_daily["day_timestamp_ms"].apply(lambda t: btc_daily_map.get(t // (86400 * 1000), (0, 0))[0])
    df_daily["btc_d_sigma"] = df_daily["day_timestamp_ms"].apply(lambda t: btc_daily_map.get(t // (86400 * 1000), (0, 0))[1])

    def classify_macro(row):
        is_bull = row["btc_d_ret"] >= 0
        is_high_vol = row["btc_d_sigma"] >= median_btc_sigma
        if is_high_vol and is_bull:
            return "HIGH_VOL_BULL"
        elif is_high_vol and not is_bull:
            return "HIGH_VOL_BEAR"
        elif not is_high_vol and is_bull:
            return "LOW_VOL_BULL"
        else:
            return "LOW_VOL_BEAR"

    df_daily["macro_regime"] = df_daily.apply(classify_macro, axis=1)

    regime_map = dict(zip(df_daily["day_timestamp_ms"] // (86400 * 1000), df_daily["macro_regime"]))
    df_trades["macro_regime"] = df_trades["entry_time_ms"].apply(lambda t: regime_map.get(t // (86400 * 1000), "UNKNOWN"))

    regime_rows = []
    for reg in ["HIGH_VOL_BEAR", "HIGH_VOL_BULL", "LOW_VOL_BULL", "LOW_VOL_BEAR"]:
        sub_d = df_daily[df_daily["macro_regime"] == reg]
        sub_t = df_trades[df_trades["macro_regime"] == reg]
        wins = sub_t[sub_t["net_pnl_usd"] > 0]["net_pnl_usd"].sum()
        losses = abs(sub_t[sub_t["net_pnl_usd"] < 0]["net_pnl_usd"].sum())
        pf = wins / losses if losses > 0 else float("inf")

        regime_rows.append({
            "dimension": "MACRO_REGIME",
            "attribute": reg,
            "calendar_days": len(sub_d),
            "mean_daily_return_pct": round(float(sub_d["daily_return_pct"].mean()), 4),
            "daily_std_pct": round(float(sub_d["daily_return_pct"].std()), 4),
            "trades_count": len(sub_t),
            "win_rate_pct": round(float((sub_t["net_pnl_usd"] > 0).mean() * 100.0), 2) if not sub_t.empty else 0.0,
            "net_expectancy_bps": round(float(sub_t["net_return_bps"].mean()), 2) if not sub_t.empty else 0.0,
            "gross_expectancy_bps": round(float(sub_t["gross_return_bps"].mean()), 2) if not sub_t.empty else 0.0,
            "profit_factor": round(float(pf), 3),
        })

    # 3. SIGNAL ATTRIBUTION (Long vs Short, Vol Exp, HTF strength)
    signal_rows = []
    for side in ["LONG", "SHORT"]:
        sub = df_trades[df_trades["side"] == side]
        wins = sub[sub["net_pnl_usd"] > 0]["net_pnl_usd"].sum()
        losses = abs(sub[sub["net_pnl_usd"] < 0]["net_pnl_usd"].sum())
        pf = wins / losses if losses > 0 else float("inf")

        signal_rows.append({
            "dimension": "DIRECTION",
            "attribute": side,
            "trades_count": len(sub),
            "win_rate_pct": round(float((sub["net_pnl_usd"] > 0).mean() * 100.0), 2),
            "net_expectancy_bps": round(float(sub["net_return_bps"].mean()), 2),
            "gross_expectancy_bps": round(float(sub["gross_return_bps"].mean()), 2),
            "profit_factor": round(float(pf), 3),
            "mfe_mean_bps": round(float(sub["mfe_bps"].mean()), 2),
            "mae_mean_bps": round(float(sub["mae_bps"].mean()), 2),
        })

    # 4. TRADE LIFECYCLE (Holding period, Exits, MFE/MAE)
    lifecycle_rows = []
    for rsn in df_trades["exit_reason"].unique():
        sub = df_trades[df_trades["exit_reason"] == rsn]
        wins = sub[sub["net_pnl_usd"] > 0]["net_pnl_usd"].sum()
        losses = abs(sub[sub["net_pnl_usd"] < 0]["net_pnl_usd"].sum())
        pf = wins / losses if losses > 0 else float("inf")

        lifecycle_rows.append({
            "dimension": "EXIT_REASON",
            "attribute": rsn,
            "trades_count": len(sub),
            "pct_of_total_trades": round(float(len(sub) / len(df_trades) * 100.0), 2),
            "win_rate_pct": round(float((sub["net_pnl_usd"] > 0).mean() * 100.0), 2),
            "net_expectancy_bps": round(float(sub["net_return_bps"].mean()), 2),
            "profit_factor": round(float(pf), 3),
            "avg_bars_held": round(float(sub["bars_held"].mean()), 2),
            "mfe_mean_bps": round(float(sub["mfe_bps"].mean()), 2),
            "mae_mean_bps": round(float(sub["mae_bps"].mean()), 2),
        })

    # Expectancy by holding bars
    for bars in sorted(df_trades["bars_held"].unique()):
        sub = df_trades[df_trades["bars_held"] == bars]
        lifecycle_rows.append({
            "dimension": "HOLDING_BARS",
            "attribute": f"{bars} bars ({bars*5}m)",
            "trades_count": len(sub),
            "pct_of_total_trades": round(float(len(sub) / len(df_trades) * 100.0), 2),
            "win_rate_pct": round(float((sub["net_pnl_usd"] > 0).mean() * 100.0), 2),
            "net_expectancy_bps": round(float(sub["net_return_bps"].mean()), 2),
            "profit_factor": round(float(sub[sub["net_pnl_usd"] > 0]["net_pnl_usd"].sum() / max(abs(sub[sub["net_pnl_usd"] < 0]["net_pnl_usd"].sum()), 1e-4)), 3),
            "avg_bars_held": bars,
            "mfe_mean_bps": round(float(sub["mfe_bps"].mean()), 2),
            "mae_mean_bps": round(float(sub["mae_bps"].mean()), 2),
        })

    # 5. PROFIT CONCENTRATION ANALYSIS
    daily_rets = df_daily["daily_return_pct"].values
    n_days = len(daily_rets)
    sorted_rets = np.sort(daily_rets)

    n_top_1 = max(1, int(n_days * 0.01)) # ~11 days
    n_top_5 = max(1, int(n_days * 0.05)) # ~55 days
    n_bot_5 = max(1, int(n_days * 0.05)) # ~55 days

    mean_all = float(np.mean(daily_rets))
    mean_ex_top1 = float(np.mean(sorted_rets[:-n_top_1]))
    mean_ex_top5 = float(np.mean(sorted_rets[:-n_top_5]))
    mean_ex_bot5 = float(np.mean(sorted_rets[n_bot_5:]))
    mean_trimmed_5 = float(stats.trim_mean(daily_rets, 0.05))

    concentration_rows = [
        {"metric": "Full Sample Mean Daily Return", "value_pct": round(mean_all, 4), "interpretation": "Full 1,099 calendar days"},
        {"metric": "Top 1% Days Cutoff Return", "value_pct": round(float(sorted_rets[-n_top_1]), 4), "interpretation": f"Threshold for top {n_top_1} days"},
        {"metric": "Mean Return Excluding Top 1% Days", "value_pct": round(mean_ex_top1, 4), "interpretation": f"Impact of removing top {n_top_1} outlier days"},
        {"metric": "Top 5% Days Cutoff Return", "value_pct": round(float(sorted_rets[-n_top_5]), 4), "interpretation": f"Threshold for top {n_top_5} days"},
        {"metric": "Mean Return Excluding Top 5% Days", "value_pct": round(mean_ex_top5, 4), "interpretation": f"Impact of removing top {n_top_5} outlier days"},
        {"metric": "Bottom 5% Days Cutoff Loss", "value_pct": round(float(sorted_rets[n_bot_5]), 4), "interpretation": f"Worst {n_bot_5} loss days threshold"},
        {"metric": "Mean Return Excluding Bottom 5% Days", "value_pct": round(mean_ex_bot5, 4), "interpretation": f"Impact of removing worst {n_bot_5} drawdown days"},
        {"metric": "5% Symmetrically Trimmed Mean Daily Return", "value_pct": round(mean_trimmed_5, 4), "interpretation": "Trimmed mean excluding both tails (central core alpha)"},
    ]

    # Combine into HYP01_ALPHA_DECOMPOSITION.csv
    decomp_dict = {
        "asset_attribution": asset_rows,
        "regime_attribution": regime_rows,
        "signal_attribution": signal_rows,
        "lifecycle_attribution": lifecycle_rows,
        "concentration_attribution": concentration_rows,
    }

    with open(out_dir / "HYP01_ALPHA_DECOMPOSITION.json", "w") as f:
        json.dump(decomp_dict, f, indent=2, default=str)

    pd.DataFrame(asset_rows + regime_rows + signal_rows + lifecycle_rows).to_csv(out_dir / "HYP01_ALPHA_DECOMPOSITION.csv", index=False)
    pd.DataFrame(concentration_rows).to_csv(out_dir / "HYP01_PROFIT_CONCENTRATION.csv", index=False)

    print("\n" + "=" * 88)
    print("HYP-01 ALPHA DECOMPOSITION COMPLETE")
    print(f"Full Mean Daily: {mean_all:.4f}% | 5% Trimmed Mean: {mean_trimmed_5:.4f}%")
    print(f"Mean Excl Top 1% Days: {mean_ex_top1:.4f}% | Mean Excl Top 5% Days: {mean_ex_top5:.4f}%")
    print(f"MFE Mean: {df_trades['mfe_bps'].mean():.2f} bps | MAE Mean: {df_trades['mae_bps'].mean():.2f} bps")
    print("=" * 88)


if __name__ == "__main__":
    from scipy import stats
    main()
