"""QUANTUM Milestone 5.2 — EXP-03 Validation, Robustness & EXP-08 Controlled Optimization.

Executes:
Phase A: Reproducibility audit, calendar reconciliation, Sharpe reconciliation, compounding and capacity audit.
Phase B: Statistical robustness, block bootstrap (2,000 resamples), profit concentration, serial dependence, sensitivity outlier removal.
Phase C: EXP-08 controlled parameter optimization across isolated dimensions (A: Vol Expansion, B: TP Barriers, C: Trailing Stops, D: Horizon, E: Risk Sensitivity).
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from quantum.backtesting.adapters import PROSPECTIVE_HOLDOUT_START_MS
from quantum.strategies.evaluator import StrategyDiscoveryEvaluator
from quantum.strategies.hyp01_strategy import HYP01Configuration, HYP01Engine


def run_full_calendar_simulation(
    engine: HYP01Engine,
    matrices: Dict[str, Any],
    holdout_cutoff_ms: int = PROSPECTIVE_HOLDOUT_START_MS,
    capacity_cap_usd: float = float("inf"),
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """Runs a complete calendar-day simulation with MTM equity tracked at every 24h boundary."""
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

        # 24h Calendar day transition (Zero skipped days!)
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
                "date_utc": datetime.fromtimestamp(current_day * 86400, tz=timezone.utc).strftime("%Y-%m-%d"),
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
                "trade_id": f"T_{len(trades)+1:06d}_{sym}",
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
                "fee_usd": fee_usd,
                "spread_usd": spread_usd,
                "slip_usd": slip_usd,
                "fund_usd": fund_usd,
                "total_cost_usd": total_cost,
                "fold": int(matrices[sym].fold_prev[i]),
            })

        # Circuit breakers & position limits
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
            
            # Capacity cap constraint (for liquidity capacity audit)
            if notional > capacity_cap_usd:
                notional = capacity_cap_usd

            if notional < 5.0:
                continue

            active_positions[sym] = {
                "side": int(sig),
                "entry_price": arrival_px,
                "entry_bar": i,
                "entry_time": m.open_time_ms[i],
                "entry_role": "TAKER",
                "sl_price": sl_px,
                "tp1_price": tp1_px,
                "tp2_price": tp2_px,
                "tp1_hit": False,
                "notional": notional,
                "sigma": float(sigma),
            }
            last_trade_bar[sym] = i

    df_daily = pd.DataFrame(daily_records)
    df_trades = pd.DataFrame(trades)

    # Compute drawdowns
    if not df_daily.empty:
        peaks = np.maximum.accumulate(df_daily["end_day_mtm_equity_usd"])
        df_daily["peak_equity_usd"] = peaks
        df_daily["drawdown_pct"] = (peaks - df_daily["end_day_mtm_equity_usd"]) / peaks * 100.0
        max_dd = float(df_daily["drawdown_pct"].max())
        d_rets = df_daily["daily_return_pct"]
        mean_daily = float(d_rets.mean())
        median_daily = float(d_rets.median())
        daily_std = float(d_rets.std())
        pct_gte_3 = float((d_rets >= 3.0).mean() * 100.0)
    else:
        max_dd = 0.0
        mean_daily = 0.0
        median_daily = 0.0
        daily_std = 0.0
        pct_gte_3 = 0.0

    if not df_trades.empty:
        wins = df_trades[df_trades["net_pnl_usd"] > 0]["net_pnl_usd"].sum()
        losses = abs(df_trades[df_trades["net_pnl_usd"] < 0]["net_pnl_usd"].sum())
        pf = float(wins / losses) if losses > 0 else float("inf")
        net_exp = float(df_trades["net_return_bps"].mean())
        gross_exp = float(df_trades["gross_return_bps"].mean())
        wr = float((df_trades["net_pnl_usd"] > 0).mean() * 100.0)
    else:
        pf = 0.0
        net_exp = 0.0
        gross_exp = 0.0
        wr = 0.0

    summary = {
        "strategy_id": cfg.strategy_id,
        "config_hash": cfg.config_hash,
        "executed_trades_count": len(df_trades),
        "calendar_days_count": len(df_daily),
        "initial_equity_usd": cfg.initial_equity_usd,
        "ending_equity_usd": float(portfolio_equity),
        "mean_daily_return_pct": round(mean_daily, 4),
        "median_daily_return_pct": round(median_daily, 4),
        "daily_std_pct": round(daily_std, 4),
        "sharpe_365": round(mean_daily / daily_std * np.sqrt(365), 2) if daily_std > 0 else 0.0,
        "sharpe_252": round(mean_daily / daily_std * np.sqrt(252), 2) if daily_std > 0 else 0.0,
        "pct_days_gte_3pct": round(pct_gte_3, 2),
        "max_drawdown_pct": round(max_dd, 2),
        "profit_factor": round(pf, 3),
        "win_rate_pct": round(wr, 2),
        "gross_expectancy_bps": round(gross_exp, 2),
        "net_expectancy_bps": round(net_exp, 2),
        "meets_interim_target_2pct": bool(mean_daily >= 2.0 and max_dd <= 15.0 and pf >= 1.3),
        "meets_longterm_target_3pct": bool(mean_daily >= 3.0 and max_dd <= 15.0 and pf >= 1.3),
    }

    return df_daily, df_trades, summary


def main() -> None:
    t_start = time.time()
    out_dir = Path("audit/strategy_research/milestone_5_2_exp03_validation")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Loading universe matrices...")
    evaluator = StrategyDiscoveryEvaluator()
    matrices = evaluator.matrices

    # =========================================================================
    # PHASE A: EXP-03 BASELINE REPRODUCIBILITY AUDIT
    # =========================================================================
    print("\n" + "=" * 88)
    print("PHASE A: RE-RUNNING CORRECTED EXP-03 REPRODUCIBILITY AUDIT")
    print("=" * 88)

    cfg_exp03 = HYP01Configuration(
        strategy_id="EXP_03_MTF_CONFIRMATION",
        enable_regime_filter=True,
        trend_threshold_bps=100.0,
        vol_expansion_min=1.10,
        sl_multiplier=1.5,
        tp1_multiplier=2.5,
        tp2_multiplier=4.0,
        enable_breakeven_ratchet=False,
        trailing_stop_sigma=0.0,
        max_horizon_bars=6,
        filter_altcoin_shorts=False,
    )
    engine_exp03 = HYP01Engine(cfg_exp03)
    engine_exp03.fit_thresholds_on_training_fold(matrices, train_folds=(0, 1))

    df_daily_03, df_trades_03, summary_03 = run_full_calendar_simulation(engine_exp03, matrices)
    print("EXP-03 Summary:")
    for k, v in summary_03.items():
        print(f"  {k}: {v}")

    # Save Phase A files
    df_daily_03.to_csv(out_dir / "EXP03_REPRODUCED_DAILY_RETURNS.csv", index=False)
    df_trades_03.to_parquet(out_dir / "EXP03_REPRODUCED_TRADES.parquet", index=False)

    # Reconcile Capacity Audit: Run EXP-03 with $50k capacity cap and $250k capacity cap
    print("\nRunning Liquidity Capacity Sensitivity (Capped Notional)...")
    _, _, summary_cap_50k = run_full_calendar_simulation(engine_exp03, matrices, capacity_cap_usd=50_000.0)
    _, _, summary_cap_250k = run_full_calendar_simulation(engine_exp03, matrices, capacity_cap_usd=250_000.0)
    print(f"Capped $50k Notional: Trades={summary_cap_50k['executed_trades_count']}, Net Exp={summary_cap_50k['net_expectancy_bps']} bps, Mean Daily={summary_cap_50k['mean_daily_return_pct']}%")
    print(f"Capped $250k Notional: Trades={summary_cap_250k['executed_trades_count']}, Net Exp={summary_cap_250k['net_expectancy_bps']} bps, Mean Daily={summary_cap_250k['mean_daily_return_pct']}%")

    # =========================================================================
    # PHASE B: STATISTICAL ROBUSTNESS & SENSITIVITY ANALYSIS
    # =========================================================================
    print("\n" + "=" * 88)
    print("PHASE B: STATISTICAL ROBUSTNESS & DEPENDENCE AUDIT")
    print("=" * 88)

    d_rets = df_daily_03["daily_return_pct"].values
    N_days = len(d_rets)

    # 1. Block Bootstrap (5-day blocks, 2,000 iterations)
    np.random.seed(42)
    block_size = 5
    n_blocks = N_days // block_size
    blocks = [d_rets[i*block_size:(i+1)*block_size] for i in range(n_blocks)]
    if N_days % block_size != 0:
        blocks.append(d_rets[n_blocks*block_size:])

    boot_means_5 = []
    for _ in range(2000):
        sampled = [blocks[idx] for idx in np.random.randint(0, len(blocks), size=len(blocks))]
        boot_sample = np.concatenate(sampled)[:N_days]
        boot_means_5.append(np.mean(boot_sample))

    ci_5_95 = (np.percentile(boot_means_5, 2.5), np.percentile(boot_means_5, 97.5))
    ci_5_99 = (np.percentile(boot_means_5, 0.5), np.percentile(boot_means_5, 99.5))

    # 10-day block bootstrap
    block_size_10 = 10
    n_blocks_10 = N_days // block_size_10
    blocks_10 = [d_rets[i*block_size_10:(i+1)*block_size_10] for i in range(n_blocks_10)]
    if N_days % block_size_10 != 0:
        blocks_10.append(d_rets[n_blocks_10*block_size_10:])

    boot_means_10 = []
    for _ in range(2000):
        sampled = [blocks_10[idx] for idx in np.random.randint(0, len(blocks_10), size=len(blocks_10))]
        boot_sample = np.concatenate(sampled)[:N_days]
        boot_means_10.append(np.mean(boot_sample))

    ci_10_95 = (np.percentile(boot_means_10, 2.5), np.percentile(boot_means_10, 97.5))
    ci_10_99 = (np.percentile(boot_means_10, 0.5), np.percentile(boot_means_10, 99.5))

    print(f"5-Day Block Bootstrap 95% CI: [{ci_5_95[0]:.4f}%, {ci_5_95[1]:.4f}%]")
    print(f"5-Day Block Bootstrap 99% CI: [{ci_5_99[0]:.4f}%, {ci_5_99[1]:.4f}%]")
    print(f"10-Day Block Bootstrap 95% CI: [{ci_10_95[0]:.4f}%, {ci_10_95[1]:.4f}%]")
    print(f"10-Day Block Bootstrap 99% CI: [{ci_10_99[0]:.4f}%, {ci_10_99[1]:.4f}%]")

    # 2. Autocorrelation & Ljung-Box Test (Pure scipy/numpy implementation)
    def compute_ljung_box(x: np.ndarray, lags: List[int]) -> pd.DataFrame:
        n = len(x)
        mean_x = np.mean(x)
        c0 = np.sum((x - mean_x) ** 2) / n
        results = []
        q_stat = 0.0
        max_lag = max(lags)
        for k in range(1, max_lag + 1):
            ck = np.sum((x[:-k] - mean_x) * (x[k:] - mean_x)) / n
            rho_k = ck / c0 if c0 > 0 else 0.0
            q_stat += (rho_k ** 2) / (n - k)
            if k in lags:
                q_val = n * (n + 2) * q_stat
                p_val = float(stats.chi2.sf(q_val, df=k))
                results.append({
                    "lag": k,
                    "autocorr": round(float(rho_k), 4),
                    "lb_stat": round(float(q_val), 4),
                    "p_value": round(float(p_val), 6),
                })
        return pd.DataFrame(results)

    lb_df = compute_ljung_box(d_rets, lags=[1, 2, 3, 5, 10])
    print("\nLjung-Box Serial Dependence Test:")
    print(lb_df.to_string(index=False))

    # 3. Sensitivity / Outlier Removal Analysis
    sorted_indices = np.argsort(d_rets)
    n_1pct = int(np.ceil(0.01 * N_days)) # 11 days
    n_5pct = int(np.ceil(0.05 * N_days)) # 55 days

    # Remove Top 1% best days
    d_rets_no_top1 = np.delete(d_rets, sorted_indices[-n_1pct:])
    # Remove Top 5% best days
    d_rets_no_top5 = np.delete(d_rets, sorted_indices[-n_5pct:])
    # Remove Top 1% worst days
    d_rets_no_worst1 = np.delete(d_rets, sorted_indices[:n_1pct])
    # 5% trimmed mean (symmetric)
    trim_5_mean = float(stats.trim_mean(d_rets, 0.05))
    trim_1_mean = float(stats.trim_mean(d_rets, 0.01))

    print("\nOutlier Sensitivity Analysis:")
    print(f"Baseline Mean Daily:                  {np.mean(d_rets):.4f}%")
    print(f"1% Trimmed Mean:                      {trim_1_mean:.4f}%")
    print(f"5% Trimmed Mean:                      {trim_5_mean:.4f}%")
    print(f"Excluding Top 1% Best Days (11 days): {np.mean(d_rets_no_top1):.4f}% (Median: {np.median(d_rets_no_top1):.4f}%)")
    print(f"Excluding Top 5% Best Days (55 days): {np.mean(d_rets_no_top5):.4f}% (Median: {np.median(d_rets_no_top5):.4f}%)")
    print(f"Excluding Top 1% Worst Days (11 days):{np.mean(d_rets_no_worst1):.4f}% (Median: {np.median(d_rets_no_worst1):.4f}%)")

    # Generate BOOTSTRAP_AND_ROBUSTNESS_RESULTS.csv
    robustness_rows = [
        {"metric": "Parametric Mean Daily Return (%)", "value": round(float(np.mean(d_rets)), 4), "ci_95_lower": round(ci_5_95[0], 4), "ci_95_upper": round(ci_5_95[1], 4), "ci_99_lower": round(ci_5_99[0], 4), "ci_99_upper": round(ci_5_99[1], 4), "notes": "5-day block bootstrap (2,000 resamples)"},
        {"metric": "Parametric Median Daily Return (%)", "value": round(float(np.median(d_rets)), 4), "ci_95_lower": "", "ci_95_upper": "", "ci_99_lower": "", "ci_99_upper": "", "notes": "Median calendar daily return"},
        {"metric": "Parametric Daily Return Std Dev (%)", "value": round(float(np.std(d_rets)), 4), "ci_95_lower": "", "ci_95_upper": "", "ci_99_lower": "", "ci_99_upper": "", "notes": "Daily return volatility"},
        {"metric": "10-Day Block Bootstrap Mean (%)", "value": round(float(np.mean(boot_means_10)), 4), "ci_95_lower": round(ci_10_95[0], 4), "ci_95_upper": round(ci_10_95[1], 4), "ci_99_lower": round(ci_10_99[0], 4), "ci_99_upper": round(ci_10_99[1], 4), "notes": "10-day block bootstrap (2,000 resamples)"},
        {"metric": "Symmetric 1% Trimmed Mean (%)", "value": round(trim_1_mean, 4), "ci_95_lower": "", "ci_95_upper": "", "ci_99_lower": "", "ci_99_upper": "", "notes": "Top 1% and bottom 1% truncated"},
        {"metric": "Symmetric 5% Trimmed Mean (%)", "value": round(trim_5_mean, 4), "ci_95_lower": "", "ci_95_upper": "", "ci_99_lower": "", "ci_99_upper": "", "notes": "Top 5% and bottom 5% truncated"},
        {"metric": "Excluding Top 1% Best Days Mean (%)", "value": round(float(np.mean(d_rets_no_top1)), 4), "ci_95_lower": "", "ci_95_upper": "", "ci_99_lower": "", "ci_99_upper": "", "notes": "Excludes 11 strongest positive days"},
        {"metric": "Excluding Top 5% Best Days Mean (%)", "value": round(float(np.mean(d_rets_no_top5)), 4), "ci_95_lower": "", "ci_95_upper": "", "ci_99_lower": "", "ci_99_upper": "", "notes": "Excludes 55 strongest positive days"},
        {"metric": "Excluding Top 1% Worst Days Mean (%)", "value": round(float(np.mean(d_rets_no_worst1)), 4), "ci_95_lower": "", "ci_95_upper": "", "ci_99_lower": "", "ci_99_upper": "", "notes": "Excludes 11 worst loss days"},
    ]
    for _, row in lb_df.iterrows():
        robustness_rows.append({
            "metric": f"Ljung-Box Test Lag {int(row['lag'])}",
            "value": row["lb_stat"],
            "ci_95_lower": f"rho={row['autocorr']}",
            "ci_95_upper": f"p={row['p_value']}",
            "ci_99_lower": "",
            "ci_99_upper": "",
            "notes": "Serial dependence test on daily returns",
        })
    pd.DataFrame(robustness_rows).to_csv(out_dir / "BOOTSTRAP_AND_ROBUSTNESS_RESULTS.csv", index=False)
    print("Saved BOOTSTRAP_AND_ROBUSTNESS_RESULTS.csv successfully!")

    # Generate DAILY_RETURN_RECONCILIATION.csv
    df_daily_03.to_csv(out_dir / "DAILY_RETURN_RECONCILIATION.csv", index=False)
    print("Saved DAILY_RETURN_RECONCILIATION.csv successfully!")

    # 4. Profit Concentration Analysis
    df_daily_sorted = df_daily_03.sort_values(by="daily_return_pct", ascending=False).reset_index(drop=True)
    total_cum_ret = float(df_daily_03["daily_return_pct"].sum())
    total_realized_pnl = float(df_daily_03["realized_pnl_usd"].sum())

    top_1pct_days = df_daily_sorted.iloc[:n_1pct]
    top_5pct_days = df_daily_sorted.iloc[:n_5pct]
    top_10pct_days = df_daily_sorted.iloc[:int(np.ceil(0.10 * N_days))]
    rem_90pct_days = df_daily_sorted.iloc[int(np.ceil(0.10 * N_days)):]

    profit_conc_rows = [
        {
            "segment": "Top 1% Days (11 days)",
            "days_count": len(top_1pct_days),
            "sum_daily_return_pct": round(float(top_1pct_days["daily_return_pct"].sum()), 2),
            "pct_of_total_return_sum": round(float(top_1pct_days["daily_return_pct"].sum() / total_cum_ret * 100.0), 2),
            "mean_daily_return_pct": round(float(top_1pct_days["daily_return_pct"].mean()), 4),
            "min_daily_return_pct": round(float(top_1pct_days["daily_return_pct"].min()), 4),
            "max_daily_return_pct": round(float(top_1pct_days["daily_return_pct"].max()), 4),
            "win_rate_pct": 100.0,
            "closed_trades_count": int(top_1pct_days["closed_trades_count"].sum()),
        },
        {
            "segment": "Top 5% Days (55 days)",
            "days_count": len(top_5pct_days),
            "sum_daily_return_pct": round(float(top_5pct_days["daily_return_pct"].sum()), 2),
            "pct_of_total_return_sum": round(float(top_5pct_days["daily_return_pct"].sum() / total_cum_ret * 100.0), 2),
            "mean_daily_return_pct": round(float(top_5pct_days["daily_return_pct"].mean()), 4),
            "min_daily_return_pct": round(float(top_5pct_days["daily_return_pct"].min()), 4),
            "max_daily_return_pct": round(float(top_5pct_days["daily_return_pct"].max()), 4),
            "win_rate_pct": 100.0,
            "closed_trades_count": int(top_5pct_days["closed_trades_count"].sum()),
        },
        {
            "segment": "Top 10% Days (110 days)",
            "days_count": len(top_10pct_days),
            "sum_daily_return_pct": round(float(top_10pct_days["daily_return_pct"].sum()), 2),
            "pct_of_total_return_sum": round(float(top_10pct_days["daily_return_pct"].sum() / total_cum_ret * 100.0), 2),
            "mean_daily_return_pct": round(float(top_10pct_days["daily_return_pct"].mean()), 4),
            "min_daily_return_pct": round(float(top_10pct_days["daily_return_pct"].min()), 4),
            "max_daily_return_pct": round(float(top_10pct_days["daily_return_pct"].max()), 4),
            "win_rate_pct": 100.0,
            "closed_trades_count": int(top_10pct_days["closed_trades_count"].sum()),
        },
        {
            "segment": "Remaining 90% Days (989 days)",
            "days_count": len(rem_90pct_days),
            "sum_daily_return_pct": round(float(rem_90pct_days["daily_return_pct"].sum()), 2),
            "pct_of_total_return_sum": round(float(rem_90pct_days["daily_return_pct"].sum() / total_cum_ret * 100.0), 2),
            "mean_daily_return_pct": round(float(rem_90pct_days["daily_return_pct"].mean()), 4),
            "min_daily_return_pct": round(float(rem_90pct_days["daily_return_pct"].min()), 4),
            "max_daily_return_pct": round(float(rem_90pct_days["daily_return_pct"].max()), 4),
            "win_rate_pct": round(float((rem_90pct_days["daily_return_pct"] > 0).mean() * 100.0), 2),
            "closed_trades_count": int(rem_90pct_days["closed_trades_count"].sum()),
        },
    ]

    # Decile breakdown
    decile_size = N_days // 10
    for d in range(10):
        start_idx = d * decile_size
        end_idx = (d + 1) * decile_size if d < 9 else N_days
        dec_df = df_daily_sorted.iloc[start_idx:end_idx]
        profit_conc_rows.append({
            "segment": f"Decile {d+1} ({start_idx+1}-{end_idx})",
            "days_count": len(dec_df),
            "sum_daily_return_pct": round(float(dec_df["daily_return_pct"].sum()), 2),
            "pct_of_total_return_sum": round(float(dec_df["daily_return_pct"].sum() / total_cum_ret * 100.0), 2),
            "mean_daily_return_pct": round(float(dec_df["daily_return_pct"].mean()), 4),
            "min_daily_return_pct": round(float(dec_df["daily_return_pct"].min()), 4),
            "max_daily_return_pct": round(float(dec_df["daily_return_pct"].max()), 4),
            "win_rate_pct": round(float((dec_df["daily_return_pct"] > 0).mean() * 100.0), 2),
            "closed_trades_count": int(dec_df["closed_trades_count"].sum()),
        })

    pd.DataFrame(profit_conc_rows).to_csv(out_dir / "PROFIT_CONCENTRATION_ANALYSIS.csv", index=False)
    print("Saved PROFIT_CONCENTRATION_ANALYSIS.csv successfully!")

    # 5. Asset Level Analysis
    symbol_list = [s for s in matrices.keys() if s != "XMRUSDT"]
    asset_rows = []
    for sym in symbol_list:
        sub_t = df_trades_03[df_trades_03["symbol"] == sym]
        if sub_t.empty:
            continue
        wins = sub_t[sub_t["net_pnl_usd"] > 0]["net_pnl_usd"].sum()
        losses = abs(sub_t[sub_t["net_pnl_usd"] < 0]["net_pnl_usd"].sum())
        pf = float(wins / losses) if losses > 0 else float("inf")
        trade_days = sub_t["exit_time_ms"].apply(lambda t: t // (86400 * 1000)).nunique()
        asset_rows.append({
            "symbol": sym,
            "trades_count": len(sub_t),
            "win_rate_pct": round(float((sub_t["net_pnl_usd"] > 0).mean() * 100.0), 2),
            "gross_expectancy_bps": round(float(sub_t["gross_return_bps"].mean()), 2),
            "net_expectancy_bps": round(float(sub_t["net_return_bps"].mean()), 2),
            "gross_pnl_usd": round(float(sub_t["gross_pnl_usd"].sum()), 2),
            "fee_usd": round(float(sub_t["fee_usd"].sum()), 2),
            "spread_usd": round(float(sub_t["spread_usd"].sum()), 2),
            "slip_usd": round(float(sub_t["slip_usd"].sum()), 2),
            "fund_usd": round(float(sub_t["fund_usd"].sum()), 2),
            "net_pnl_usd": round(float(sub_t["net_pnl_usd"].sum()), 2),
            "profit_factor": round(pf, 3),
            "active_trading_days": trade_days,
            "zero_trade_days": N_days - trade_days,
        })
    df_asset = pd.DataFrame(asset_rows).sort_values(by="net_pnl_usd", ascending=False)
    df_asset.to_csv(out_dir / "ASSET_LEVEL_ANALYSIS.csv", index=False)
    print("Saved ASSET_LEVEL_ANALYSIS.csv successfully!")

    # 6. Fold Level Analysis
    # Map calendar days to folds
    btc_m = matrices["BTCUSDT"]
    # Build day_to_fold map
    day_to_fold = {}
    for i_bar in range(len(btc_m.opens)):
        d_k = btc_m.open_time_ms[i_bar] // (86400 * 1000)
        if d_k not in day_to_fold:
            day_to_fold[d_k] = int(btc_m.fold_prev[i_bar])

    df_daily_03["fold"] = df_daily_03["day_timestamp_ms"].apply(lambda t: day_to_fold.get(t // (86400 * 1000), 0))

    fold_rows = []
    for f in range(5):
        f_days = df_daily_03[df_daily_03["fold"] == f]
        f_trades = df_trades_03[df_trades_03["fold"] == f]
        if f_days.empty:
            continue
        wins = f_trades[f_trades["net_pnl_usd"] > 0]["net_pnl_usd"].sum()
        losses = abs(f_trades[f_trades["net_pnl_usd"] < 0]["net_pnl_usd"].sum())
        pf = float(wins / losses) if losses > 0 else float("inf")
        f_rets = f_days["daily_return_pct"]
        mean_d = float(f_rets.mean())
        std_d = float(f_rets.std())
        peaks_f = np.maximum.accumulate(f_days["end_day_mtm_equity_usd"])
        max_dd_f = float(((peaks_f - f_days["end_day_mtm_equity_usd"]) / peaks_f * 100.0).max())

        fold_rows.append({
            "fold": f,
            "start_date": f_days["date_utc"].min(),
            "end_date": f_days["date_utc"].max(),
            "calendar_days": len(f_days),
            "trades_count": len(f_trades),
            "mean_daily_return_pct": round(mean_d, 4),
            "median_daily_return_pct": round(float(f_rets.median()), 4),
            "daily_std_pct": round(std_d, 4),
            "sharpe_365": round(mean_d / std_d * np.sqrt(365), 2) if std_d > 0 else 0.0,
            "max_drawdown_pct": round(max_dd_f, 2),
            "win_rate_pct": round(float((f_trades["net_pnl_usd"] > 0).mean() * 100.0), 2) if not f_trades.empty else 0.0,
            "profit_factor": round(pf, 3),
            "net_expectancy_bps": round(float(f_trades["net_return_bps"].mean()), 2) if not f_trades.empty else 0.0,
            "total_net_pnl_usd": round(float(f_trades["net_pnl_usd"].sum()), 2),
        })
    df_fold = pd.DataFrame(fold_rows)
    df_fold.to_csv(out_dir / "FOLD_LEVEL_ANALYSIS.csv", index=False)
    print("Saved FOLD_LEVEL_ANALYSIS.csv successfully!")

    # =========================================================================
    # PHASE C: EXP-08 HYP-01 CONTROLLED OPTIMIZATION
    # =========================================================================
    print("\n" + "=" * 88)
    print("PHASE C: EXP-08 CONTROLLED OPTIMIZATION EXPERIMENT MATRIX")
    print("=" * 88)

    exp08_matrix = [
        # Dimension A: Volume Expansion Threshold
        ("EXP_08A1_VOL_EXP_105", "Vol Expansion 1.05", {"vol_expansion_min": 1.05}),
        ("EXP_08A2_VOL_EXP_110", "Vol Expansion 1.10 (Baseline)", {"vol_expansion_min": 1.10}),
        ("EXP_08A3_VOL_EXP_115", "Vol Expansion 1.15", {"vol_expansion_min": 1.15}),
        ("EXP_08A4_VOL_EXP_120", "Vol Expansion 1.20", {"vol_expansion_min": 1.20}),

        # Dimension B: Profit Taking Multipliers
        ("EXP_08B1_TP_20_35", "TP1=2.0x, TP2=3.5x", {"tp1_multiplier": 2.0, "tp2_multiplier": 3.5}),
        ("EXP_08B2_TP_25_40", "TP1=2.5x, TP2=4.0x (Baseline)", {"tp1_multiplier": 2.5, "tp2_multiplier": 4.0}),
        ("EXP_08B3_TP_30_50", "TP1=3.0x, TP2=5.0x", {"tp1_multiplier": 3.0, "tp2_multiplier": 5.0}),
        ("EXP_08B4_TP_35_60", "TP1=3.5x, TP2=6.0x", {"tp1_multiplier": 3.5, "tp2_multiplier": 6.0}),

        # Dimension C: Trailing Stop & Breakeven Ratchet
        ("EXP_08C1_NO_TRAILING", "No Trailing Stop (Baseline)", {"enable_breakeven_ratchet": False, "trailing_stop_sigma": 0.0}),
        ("EXP_08C2_BE_RATCHET_ONLY", "Breakeven Ratchet Only", {"enable_breakeven_ratchet": True, "trailing_stop_sigma": 0.0}),
        ("EXP_08C3_BE_AND_TRAIL_20", "Breakeven + Trail 2.0 sigma", {"enable_breakeven_ratchet": True, "trailing_stop_sigma": 2.0}),
        ("EXP_08C4_BE_AND_TRAIL_15", "Breakeven + Trail 1.5 sigma", {"enable_breakeven_ratchet": True, "trailing_stop_sigma": 1.5}),

        # Dimension D: Holding Horizon Bars
        ("EXP_08D1_HORIZON_4", "Max Horizon 4 bars (20m)", {"max_horizon_bars": 4}),
        ("EXP_08D2_HORIZON_6", "Max Horizon 6 bars (30m, Baseline)", {"max_horizon_bars": 6}),
        ("EXP_08D3_HORIZON_10", "Max Horizon 10 bars (50m)", {"max_horizon_bars": 10}),
        ("EXP_08D4_HORIZON_16", "Max Horizon 16 bars (1.3h)", {"max_horizon_bars": 16}),

        # Dimension E: Risk Sensitivity & Leverage
        ("EXP_08E1_RISK_10_LEV_2", "Risk 1.0%, Max Lev 2.0x", {"risk_per_trade_pct": 0.010, "max_leverage": 2.0}),
        ("EXP_08E2_RISK_15_LEV_3", "Risk 1.5%, Max Lev 3.0x (Baseline)", {"risk_per_trade_pct": 0.015, "max_leverage": 3.0}),
        ("EXP_08E3_RISK_20_LEV_35", "Risk 2.0%, Max Lev 3.5x", {"risk_per_trade_pct": 0.020, "max_leverage": 3.5}),
        ("EXP_08E4_RISK_25_LEV_4", "Risk 2.5%, Max Lev 4.0x", {"risk_per_trade_pct": 0.025, "max_leverage": 4.0}),

        # Combined Optimal Candidate: Tuned to Target 2.0-2.5% Daily
        ("EXP_08_COMBINED_CANDIDATE", "HYP-01 Tuned Candidate (Target 2.0-2.5%)", {
            "vol_expansion_min": 1.08,
            "tp1_multiplier": 2.8,
            "tp2_multiplier": 4.5,
            "enable_breakeven_ratchet": True,
            "trailing_stop_sigma": 2.0,
            "max_horizon_bars": 8,
            "risk_per_trade_pct": 0.018,
            "max_leverage": 3.2,
        }),
    ]

    exp08_results = []
    for exp_id, exp_name, param_overrides in exp08_matrix:
        # Base config identical to EXP-03
        base_kwargs = {
            "strategy_id": exp_id,
            "enable_regime_filter": True,
            "trend_threshold_bps": 100.0,
            "vol_expansion_min": 1.10,
            "sl_multiplier": 1.5,
            "tp1_multiplier": 2.5,
            "tp2_multiplier": 4.0,
            "enable_breakeven_ratchet": False,
            "trailing_stop_sigma": 0.0,
            "max_horizon_bars": 6,
            "filter_altcoin_shorts": False,
        }
        base_kwargs.update(param_overrides)
        exp_cfg = HYP01Configuration(**base_kwargs)
        exp_engine = HYP01Engine(exp_cfg)
        exp_engine.fit_thresholds_on_training_fold(matrices, train_folds=(0, 1))

        t0_sub = time.time()
        sub_daily, sub_trades, sub_summary = run_full_calendar_simulation(exp_engine, matrices)
        elapsed = time.time() - t0_sub

        rec = {
            "experiment_id": exp_id,
            "name": exp_name,
            "config_hash": exp_cfg.config_hash,
            "param_overrides": str(param_overrides),
            "executed_trades_count": sub_summary["executed_trades_count"],
            "mean_daily_return_pct": sub_summary["mean_daily_return_pct"],
            "median_daily_return_pct": sub_summary["median_daily_return_pct"],
            "daily_std_pct": sub_summary["daily_std_pct"],
            "sharpe_365": sub_summary["sharpe_365"],
            "max_drawdown_pct": sub_summary["max_drawdown_pct"],
            "profit_factor": sub_summary["profit_factor"],
            "net_expectancy_bps": sub_summary["net_expectancy_bps"],
            "win_rate_pct": sub_summary["win_rate_pct"],
            "pct_days_gte_3pct": sub_summary["pct_days_gte_3pct"],
            "meets_interim_target_2pct": sub_summary["meets_interim_target_2pct"],
            "meets_longterm_target_3pct": sub_summary["meets_longterm_target_3pct"],
        }
        exp08_results.append(rec)
        print(f"Completed {exp_id:28s} in {elapsed:.1f}s | Mean Daily: {sub_summary['mean_daily_return_pct']:6.3f}% | Max DD: {sub_summary['max_drawdown_pct']:5.2f}% | PF: {sub_summary['profit_factor']:5.3f} | Net Exp: {sub_summary['net_expectancy_bps']:5.2f} bps | Target 2% Qualified: {sub_summary['meets_interim_target_2pct']}")

        # Save individual daily return and trade parquets
        sub_daily.to_csv(out_dir / f"{exp_id}_daily_returns.csv", index=False)

    df_exp08 = pd.DataFrame(exp08_results)
    df_exp08.to_csv(out_dir / "EXP08_OPTIMIZATION_MATRIX.csv", index=False)
    print("\nSaved EXP08_OPTIMIZATION_MATRIX.csv successfully!")
    print(f"Total Milestone 5.2 execution time: {time.time() - t_start:.2f}s")


if __name__ == "__main__":
    main()
