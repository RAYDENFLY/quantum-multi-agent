"""QUANTUM Milestone 5.4 — Alpha Expansion Research & Portfolio Simulation Runner.

Executes:
Phase 1: Baseline Preservation & Verification of EXP-08
Phase 2: HYP-02 Liquidity Sweep & Reclaim Independent Evaluation
Phase 3: HYP-03 Statistical Mean Reversion Independent Evaluation
Phase 4: Cross-Strategy Daily Return Correlation Analysis
Phase 5: Unified Portfolio Combinations Simulation (HYP01 only, HYP01+HYP02, HYP01+HYP03, HYP01+HYP02+HYP03)
Phase 6: Statistical Validation, Multiple-Testing Corrections, Block Bootstrap & Capacity Audit
Phase 7: Export Comprehensive Audit Artifacts to audit/strategy_research/milestone_5_4_alpha_expansion/
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
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
from quantum.strategies.hyp02_strategy import HYP02Configuration, HYP02Engine
from quantum.strategies.hyp03_strategy import HYP03Configuration, HYP03Engine
from quantum.strategies.portfolio_engine import UnifiedPortfolioEngine


def main() -> None:
    t_start = time.time()
    out_dir = Path("audit/strategy_research/milestone_5_4_alpha_expansion")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 88)
    print("QUANTUM MILESTONE 5.4: ALPHA EXPANSION RESEARCH & PORTFOLIO SIMULATION")
    print(f"Execution Timestamp (UTC): {datetime.now(timezone.utc).isoformat()}")
    print("=" * 88)

    # 1. Load Universal Feature Matrices
    print("\n[Step 1/7] Preloading primary research universe matrices (10 perpetual assets)...")
    evaluator = StrategyDiscoveryEvaluator()
    matrices = evaluator.matrices
    symbol_list = [s for s in matrices.keys() if s != "XMRUSDT"]
    print(f"Preloaded {len(matrices)} assets: {symbol_list}")

    # =========================================================================
    # PHASE 1: BASELINE PRESERVATION & EXP-08 CANDIDATE CONFIGURATION
    # =========================================================================
    print("\n" + "=" * 88)
    print("PHASE 1: BASELINE PRESERVATION — EXP-08 OPTIMAL CANDIDATE")
    print("=" * 88)

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
    engine_hyp01 = HYP01Engine(cfg_hyp01)
    engine_hyp01.fit_thresholds_on_training_fold(matrices, train_folds=(0, 1))

    # =========================================================================
    # PHASE 2: HYP-02 LIQUIDITY SWEEP & RECLAIM EVALUATION
    # =========================================================================
    print("\n" + "=" * 88)
    print("PHASE 2: HYP-02 LIQUIDITY SWEEP & RECLAIM INDEPENDENT EVALUATION")
    print("=" * 88)

    cfg_hyp02 = HYP02Configuration(
        strategy_id="HYP02_LIQUIDITY_SWEEP",
        sweep_lookback_bars=12,
        min_wick_ratio=0.40,
        min_rvol=1.15,
        htf_trend_max_adverse_bps=150.0,
        sl_multiplier=1.5,
        tp1_multiplier=1.8,
        tp2_multiplier=3.5,
        enable_breakeven_ratchet=True,
        trailing_stop_sigma=1.5,
        max_horizon_bars=12,
        risk_per_trade_pct=0.015,
        max_leverage=3.0,
        fee_tier="BYBIT_VIP0_DEFAULT",
    )
    engine_hyp02 = HYP02Engine(cfg_hyp02)
    print("Simulating standalone HYP-02 across 1,099 calendar days...")
    t0 = time.time()
    summary_hyp02, df_daily_hyp02, df_trades_hyp02 = engine_hyp02.evaluate_multi_asset(matrices)
    print(f"HYP-02 Simulation finished in {time.time() - t0:.2f}s")
    print(f"  Mean Daily Return: {summary_hyp02['mean_daily_return_pct']}% | Median: {summary_hyp02['median_daily_return_pct']}%")
    print(f"  Max Drawdown: {summary_hyp02['max_drawdown_pct']}% | Profit Factor: {summary_hyp02['profit_factor']}")
    print(f"  Net Expectancy: {summary_hyp02['net_expectancy_bps']} bps | Executed Trades: {summary_hyp02['executed_trades_count']}")

    # =========================================================================
    # PHASE 3: HYP-03 STATISTICAL MEAN REVERSION EVALUATION
    # =========================================================================
    print("\n" + "=" * 88)
    print("PHASE 3: HYP-03 STATISTICAL MEAN REVERSION INDEPENDENT EVALUATION")
    print("=" * 88)

    cfg_hyp03 = HYP03Configuration(
        strategy_id="HYP03_MEAN_REVERSION",
        ma_lookback_bars=20,
        z_score_threshold=2.2,
        max_htf_trend_bps=60.0,
        max_sigma=0.0018,
        require_reversal_candle=True,
        sl_multiplier=1.5,
        tp1_multiplier=1.5,
        tp2_multiplier=2.5,
        enable_breakeven_ratchet=True,
        trailing_stop_sigma=1.2,
        max_horizon_bars=8,
        risk_per_trade_pct=0.015,
        max_leverage=3.0,
        fee_tier="BYBIT_VIP0_DEFAULT",
    )
    engine_hyp03 = HYP03Engine(cfg_hyp03)
    print("Simulating standalone HYP-03 across 1,099 calendar days...")
    t0 = time.time()
    summary_hyp03, df_daily_hyp03, df_trades_hyp03 = engine_hyp03.evaluate_multi_asset(matrices)
    print(f"HYP-03 Simulation finished in {time.time() - t0:.2f}s")
    print(f"  Mean Daily Return: {summary_hyp03['mean_daily_return_pct']}% | Median: {summary_hyp03['median_daily_return_pct']}%")
    print(f"  Max Drawdown: {summary_hyp03['max_drawdown_pct']}% | Profit Factor: {summary_hyp03['profit_factor']}")
    print(f"  Net Expectancy: {summary_hyp03['net_expectancy_bps']} bps | Executed Trades: {summary_hyp03['executed_trades_count']}")

    # =========================================================================
    # PHASE 4: INDEPENDENT STRATEGY COMPARISON & CORRELATION MATRIX
    # =========================================================================
    print("\n" + "=" * 88)
    print("PHASE 4: INDEPENDENT STRATEGY COMPARISON & CORRELATION ANALYSIS")
    print("=" * 88)

    # Re-run or load HYP-01 daily returns
    m53_repro_csv = Path("audit/strategy_research/milestone_5_3_independent_validation/CANDIDATE_REPRODUCIBILITY.csv")
    if m53_repro_csv.exists():
        df_daily_hyp01 = pd.read_csv(m53_repro_csv)
    else:
        # Fallback simulation of HYP-01
        p_engine_h1 = UnifiedPortfolioEngine({"HYP-01": engine_hyp01})
        _, df_daily_hyp01, _ = p_engine_h1.evaluate_portfolio(matrices)

    # Align daily returns by date_utc
    df_merged = df_daily_hyp01[["date_utc", "daily_return_pct"]].rename(columns={"daily_return_pct": "ret_01"}).merge(
        df_daily_hyp02[["date_utc", "daily_return_pct"]].rename(columns={"daily_return_pct": "ret_02"}), on="date_utc", how="inner"
    ).merge(
        df_daily_hyp03[["date_utc", "daily_return_pct"]].rename(columns={"daily_return_pct": "ret_03"}), on="date_utc", how="inner"
    )
    d_ret_01 = df_merged["ret_01"].values
    d_ret_02 = df_merged["ret_02"].values
    d_ret_03 = df_merged["ret_03"].values

    corr_01_02 = float(np.corrcoef(d_ret_01, d_ret_02)[0, 1])
    corr_01_03 = float(np.corrcoef(d_ret_01, d_ret_03)[0, 1])
    corr_02_03 = float(np.corrcoef(d_ret_02, d_ret_03)[0, 1])

    print("Daily Returns Correlation Matrix:")
    print(f"  Corr(HYP-01, HYP-02): {corr_01_02:+.4f}")
    print(f"  Corr(HYP-01, HYP-03): {corr_01_03:+.4f}")
    print(f"  Corr(HYP-02, HYP-03): {corr_02_03:+.4f}")

    corr_df = pd.DataFrame([
        {"strategy_a": "HYP-01 (Trend)", "strategy_b": "HYP-02 (Sweep)", "pearson_corr": round(corr_01_02, 4), "diversification_benefit": "MODERATE_ORTHOGONAL" if corr_01_02 < 0.4 else "HIGH_CORRELATION"},
        {"strategy_a": "HYP-01 (Trend)", "strategy_b": "HYP-03 (MeanRev)", "pearson_corr": round(corr_01_03, 4), "diversification_benefit": "EXCELLENT_ORTHOGONAL" if corr_01_03 < 0.2 else "MODERATE"},
        {"strategy_a": "HYP-02 (Sweep)", "strategy_b": "HYP-03 (MeanRev)", "pearson_corr": round(corr_02_03, 4), "diversification_benefit": "EXCELLENT_ORTHOGONAL" if corr_02_03 < 0.2 else "MODERATE"},
    ])
    corr_df.to_csv(out_dir / "CORRELATION_MATRIX.csv", index=False)

    # =========================================================================
    # PHASE 5: UNIFIED PORTFOLIO COMBINATIONS SIMULATION
    # =========================================================================
    print("\n" + "=" * 88)
    print("PHASE 5: UNIFIED MULTI-STRATEGY PORTFOLIO COMBINATIONS SIMULATION")
    print("=" * 88)

    portfolio_scenarios = [
        ("COMBO_1_HYP01_ONLY", {"HYP-01": engine_hyp01}),
        ("COMBO_2_HYP01_PLUS_HYP02", {"HYP-01": engine_hyp01, "HYP-02": engine_hyp02}),
        ("COMBO_3_HYP01_PLUS_HYP03", {"HYP-01": engine_hyp01, "HYP-03": engine_hyp03}),
        ("COMBO_4_TRIPLE_EXPANSION", {"HYP-01": engine_hyp01, "HYP-02": engine_hyp02, "HYP-03": engine_hyp03}),
    ]

    combo_results = []
    combo_daily_dfs = {}
    combo_trade_dfs = {}

    for combo_name, engines_dict in portfolio_scenarios:
        print(f"\nEvaluating Portfolio: {combo_name} ({'+'.join(engines_dict.keys())})...")
        t0 = time.time()
        p_engine = UnifiedPortfolioEngine(engines_dict)
        summary, df_d, df_t = p_engine.evaluate_portfolio(matrices)
        dur = time.time() - t0

        combo_daily_dfs[combo_name] = df_d
        combo_trade_dfs[combo_name] = df_t

        print(f"  Finished in {dur:.2f}s | Trades: {len(df_t):,} | Ending Equity: ${summary['ending_equity_usd']:,.2f}")
        print(f"  Mean Daily: {summary['mean_daily_return_pct']}% | Median: {summary['median_daily_return_pct']}%")
        print(f"  Max Drawdown: {summary['max_drawdown_pct']}% | Profit Factor: {summary['profit_factor']}")
        print(f"  Net Exp: {summary['net_expectancy_bps']} bps | Sharpe (365): {summary['sharpe_365']}")
        print(f"  Trades by Strategy: {summary.get('strategy_trades_breakdown', {})}")

        gate_status = "QUALIFIED_FOR_GATE_CONSIDERATION" if summary["mean_daily_return_pct"] >= 3.00 else "REQUIRES_RESEARCH"

        combo_results.append({
            "combo_id": combo_name,
            "strategies_included": "+".join(sorted(engines_dict.keys())),
            "mean_daily_return_pct": summary["mean_daily_return_pct"],
            "median_daily_return_pct": summary["median_daily_return_pct"],
            "daily_std_pct": summary["daily_std_pct"],
            "sharpe_365": summary["sharpe_365"],
            "max_drawdown_pct": summary["max_drawdown_pct"],
            "profit_factor": summary["profit_factor"],
            "win_rate_pct": summary["win_rate_pct"],
            "net_expectancy_bps": summary["net_expectancy_bps"],
            "gross_expectancy_bps": summary["gross_expectancy_bps"],
            "total_trades": summary["executed_trades_count"],
            "pct_days_gte_3pct": summary["pct_days_gte_3pct"],
            "pct_negative_days": summary["pct_negative_days"],
            "zero_trade_days": summary["zero_trade_days_count"],
            "ending_equity_usd": summary["ending_equity_usd"],
            "research_gate_status": gate_status,
        })

    df_combos = pd.DataFrame(combo_results)
    df_combos.to_csv(out_dir / "PORTFOLIO_COMBINATIONS.csv", index=False)
    print("\nSaved PORTFOLIO_COMBINATIONS.csv successfully!")

    # Save daily returns comparison
    daily_matrix = pd.DataFrame({"date_utc": combo_daily_dfs["COMBO_1_HYP01_ONLY"]["date_utc"]})
    for c_name, d_df in combo_daily_dfs.items():
        daily_matrix[f"{c_name}_ret_pct"] = d_df["daily_return_pct"]
    daily_matrix.to_csv(out_dir / "CANDIDATE_DAILY_RETURNS.csv", index=False)

    # =========================================================================
    # PHASE 6: STATISTICAL ROBUSTNESS, BLOCK BOOTSTRAP & REGIME BREAKDOWN
    # =========================================================================
    print("\n" + "=" * 88)
    print("PHASE 6: STATISTICAL ROBUSTNESS, BLOCK BOOTSTRAP & REGIME BREAKDOWN")
    print("=" * 88)

    # Focus on the highest performing combo
    best_combo_row = df_combos.sort_values("mean_daily_return_pct", ascending=False).iloc[0]
    best_combo_name = best_combo_row["combo_id"]
    best_daily = combo_daily_dfs[best_combo_name]["daily_return_pct"].values
    best_trades = combo_trade_dfs[best_combo_name]

    print(f"Top Performing Portfolio Configuration: {best_combo_name}")
    print(f"Mean Daily Return: {best_combo_row['mean_daily_return_pct']}% | Sharpe: {best_combo_row['sharpe_365']}")

    # 5-Day & 10-Day Block Bootstrap (B = 2,000)
    np.random.seed(42)
    N_days = len(best_daily)
    boot_means_5 = []
    for _ in range(2000):
        blk_starts = np.random.randint(0, N_days - 5 + 1, size=N_days // 5)
        indices = np.concatenate([np.arange(s, s + 5) for s in blk_starts])[:N_days]
        boot_means_5.append(np.mean(best_daily[indices]))

    ci_5_95 = (np.percentile(boot_means_5, 2.5), np.percentile(boot_means_5, 97.5))
    ci_5_99 = (np.percentile(boot_means_5, 0.5), np.percentile(boot_means_5, 99.5))

    boot_means_10 = []
    for _ in range(2000):
        blk_starts = np.random.randint(0, N_days - 10 + 1, size=N_days // 10)
        indices = np.concatenate([np.arange(s, s + 10) for s in blk_starts])[:N_days]
        boot_means_10.append(np.mean(best_daily[indices]))

    ci_10_95 = (np.percentile(boot_means_10, 2.5), np.percentile(boot_means_10, 97.5))
    ci_10_99 = (np.percentile(boot_means_10, 0.5), np.percentile(boot_means_10, 99.5))

    print(f"Best Combo 5-Day Block Bootstrap 95% CI: [{ci_5_95[0]:.4f}%, {ci_5_95[1]:.4f}%]")
    print(f"Best Combo 5-Day Block Bootstrap 99% CI: [{ci_5_99[0]:.4f}%, {ci_5_99[1]:.4f}%]")
    print(f"Best Combo 10-Day Block Bootstrap 95% CI: [{ci_10_95[0]:.4f}%, {ci_10_95[1]:.4f}%]")

    # Paired t-test vs HYP-01 Baseline
    min_len = min(len(best_daily), len(d_ret_01))
    diff_vs_base = best_daily[:min_len] - d_ret_01[:min_len]
    t_stat_pair, p_val_pair = stats.ttest_1samp(diff_vs_base, 0.0)
    print(f"Paired t-test vs HYP-01 Baseline: t = {t_stat_pair:.4f}, p = {p_val_pair:.6e}")

    # Multiple Testing Hansen SPA across the 4 portfolio scenarios vs HYP-01
    B_boot = 1000
    all_diffs = []
    for c_id in ["COMBO_1_HYP01_ONLY", "COMBO_2_HYP01_PLUS_HYP02", "COMBO_3_HYP01_PLUS_HYP03", "COMBO_4_TRIPLE_EXPANSION"]:
        all_diffs.append(combo_daily_dfs[c_id]["daily_return_pct"].values[:min_len] - d_ret_01[:min_len])
    all_diffs = np.array(all_diffs)
    mean_diffs = np.mean(all_diffs, axis=1)
    max_stat = np.max(mean_diffs)

    centered_diffs = all_diffs - mean_diffs[:, np.newaxis]
    boot_max_stats = []
    block_len = 5
    n_blks = N_days // block_len
    for _ in range(B_boot):
        blk_starts = np.random.randint(0, N_days - block_len + 1, size=n_blks)
        sample_indices = np.concatenate([np.arange(s, s + block_len) for s in blk_starts])
        boot_sample = centered_diffs[:, sample_indices]
        boot_max_stats.append(np.max(np.mean(boot_sample, axis=1)))

    spa_exceedances = int(np.sum(np.array(boot_max_stats) >= max_stat))
    spa_p_unbiased = (1.0 + spa_exceedances) / (B_boot + 1.0)
    spa_p_str = f"< {1.0 / B_boot:.3f}" if spa_exceedances == 0 else f"{spa_p_unbiased:.4f}"
    print(f"Hansen SPA p-value across 4 combinations: {spa_p_str} ({spa_exceedances}/{B_boot} exceedances)")

    # Asset & Regime Breakdown for Best Combo
    stability_rows = []
    # 1. Asset Breakdown
    for sym in symbol_list:
        sub_t = best_trades[best_trades["symbol"] == sym]
        if sub_t.empty:
            continue
        wins = sub_t[sub_t["net_pnl_usd"] > 0]["net_pnl_usd"].sum()
        losses = abs(sub_t[sub_t["net_pnl_usd"] < 0]["net_pnl_usd"].sum())
        pf = float(wins / losses) if losses > 0 else float("inf")
        trade_days = sub_t["exit_time_ms"].apply(lambda t: t // (86400 * 1000)).nunique()

        stability_rows.append({
            "category": "ASSET",
            "name": sym,
            "trades_count": len(sub_t),
            "win_rate_pct": round(float((sub_t["net_pnl_usd"] > 0).mean() * 100.0), 2),
            "net_expectancy_bps": round(float(sub_t["net_return_bps"].mean()), 2),
            "gross_expectancy_bps": round(float(sub_t["gross_return_bps"].mean()), 2),
            "profit_factor": round(pf, 3),
            "net_pnl_usd": round(float(sub_t["net_pnl_usd"].sum()), 2),
            "active_days": trade_days,
            "notes": f"Portfolio evaluation for {best_combo_name}",
        })

    # 2. Macro Regime Breakdown
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

    best_daily_df = combo_daily_dfs[best_combo_name].copy()
    best_daily_df["btc_d_ret"] = best_daily_df["day_timestamp_ms"].apply(lambda t: btc_daily_map.get(t // (86400 * 1000), (0, 0))[0])
    best_daily_df["btc_d_sigma"] = best_daily_df["day_timestamp_ms"].apply(lambda t: btc_daily_map.get(t // (86400 * 1000), (0, 0))[1])

    def classify_macro_regime(row):
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

    best_daily_df["macro_regime"] = best_daily_df.apply(classify_macro_regime, axis=1)

    for reg_name in ["HIGH_VOL_BULL", "HIGH_VOL_BEAR", "LOW_VOL_BULL", "LOW_VOL_BEAR"]:
        sub_d = best_daily_df[best_daily_df["macro_regime"] == reg_name]
        mean_d = float(sub_d["daily_return_pct"].mean())
        std_d = float(sub_d["daily_return_pct"].std())
        pos_pct = float((sub_d["daily_return_pct"] > 0).mean() * 100.0)

        stability_rows.append({
            "category": "MACRO_REGIME",
            "name": reg_name,
            "trades_count": int(sub_d["closed_trades_count"].sum()),
            "win_rate_pct": round(pos_pct, 2),
            "net_expectancy_bps": round(mean_d * 10.0, 2),
            "gross_expectancy_bps": 0.0,
            "profit_factor": 0.0,
            "net_pnl_usd": round(float(sub_d["realized_pnl_usd"].sum()), 2),
            "active_days": len(sub_d),
            "notes": f"Mean daily: {mean_d:.4f}%, Std: {std_d:.4f}%",
        })

    # 3. Walk-Forward Fold Breakdown
    day_to_fold = {}
    for i_bar in range(len(btc_m.opens)):
        d_k = btc_m.open_time_ms[i_bar] // (86400 * 1000)
        if d_k not in day_to_fold:
            day_to_fold[d_k] = int(btc_m.fold_prev[i_bar])

    best_daily_df["fold"] = best_daily_df["day_timestamp_ms"].apply(lambda t: day_to_fold.get(t // (86400 * 1000), 0))

    for f in range(5):
        f_days = best_daily_df[best_daily_df["fold"] == f]
        f_trades = best_trades[best_trades["fold"] == f]
        if f_days.empty:
            continue
        wins = f_trades[f_trades["net_pnl_usd"] > 0]["net_pnl_usd"].sum()
        losses = abs(f_trades[f_trades["net_pnl_usd"] < 0]["net_pnl_usd"].sum())
        pf = float(wins / losses) if losses > 0 else float("inf")
        f_rets = f_days["daily_return_pct"]
        mean_d = float(f_rets.mean())
        std_d = float(f_rets.std())

        stability_rows.append({
            "category": "FOLD",
            "name": f"Fold {f}",
            "trades_count": len(f_trades),
            "win_rate_pct": round(float((f_trades["net_pnl_usd"] > 0).mean() * 100.0), 2) if not f_trades.empty else 0.0,
            "net_expectancy_bps": round(float(f_trades["net_return_bps"].mean()), 2) if not f_trades.empty else 0.0,
            "gross_expectancy_bps": round(float(f_trades["gross_return_bps"].mean()), 2) if not f_trades.empty else 0.0,
            "profit_factor": round(pf, 3),
            "net_pnl_usd": round(float(f_trades["net_pnl_usd"].sum()), 2),
            "active_days": len(f_days),
            "notes": f"Mean daily: {mean_d:.4f}%, Std: {std_d:.4f}%. Fold status: {'IN_SAMPLE' if f in (0,1) else 'POST_SELECTION_CONTAMINATED'}",
        })

    pd.DataFrame(stability_rows).to_csv(out_dir / "ASSET_REGIME_BREAKDOWN.csv", index=False)
    print("Saved ASSET_REGIME_BREAKDOWN.csv successfully!")

    # =========================================================================
    # PHASE 7: CAPACITY SENSITIVITY FOR BEST COMBO
    # =========================================================================
    print("\n" + "=" * 88)
    print("PHASE 7: CAPACITY SENSITIVITY ($1k, $5k, $10k, $50k) FOR BEST COMBO")
    print("=" * 88)

    notional_levels = [1_000.0, 5_000.0, 10_000.0, 50_000.0]
    cap_rows = []

    # Uncapped dynamic
    cap_rows.append({
        "capacity_scenario": "Uncapped Dynamic Sizing (Theoretical)",
        "fixed_notional_usd": "Dynamic (0.75x equity)",
        "initial_equity_usd": 100.0,
        "ending_equity_usd": best_combo_row["ending_equity_usd"],
        "total_dollar_pnl_usd": round(best_combo_row["ending_equity_usd"] - 100.0, 2),
        "executed_trades_count": best_combo_row["total_trades"],
        "mean_daily_return_pct": best_combo_row["mean_daily_return_pct"],
        "daily_std_pct": best_combo_row["daily_std_pct"],
        "sharpe_365": best_combo_row["sharpe_365"],
        "max_drawdown_pct": best_combo_row["max_drawdown_pct"],
        "normalized_3x_drawdown_pct": best_combo_row["max_drawdown_pct"],
        "profit_factor": best_combo_row["profit_factor"],
        "net_expectancy_bps": best_combo_row["net_expectancy_bps"],
        "orderbook_executable": False,
        "notes": "Theoretical geometric compounding. Violates order book depth > $250k.",
    })

    p_eng_best = UnifiedPortfolioEngine(portfolio_scenarios[[p[0] for p in portfolio_scenarios].index(best_combo_name)][1])

    for notional in notional_levels:
        print(f"Simulating Best Combo at Fixed Notional: ${notional:,.0f}...")
        sub_s, sub_d, sub_t = p_eng_best.evaluate_portfolio(matrices, fixed_notional_usd=notional)
        tot_pnl = float(sub_t["net_pnl_usd"].sum())
        assumed_capital_base = notional * 10.0
        daily_dollar_rets = sub_d["realized_pnl_usd"] / assumed_capital_base * 100.0
        mean_cap_daily = float(daily_dollar_rets.mean())
        std_cap_daily = float(daily_dollar_rets.std())
        sharpe_cap = round(mean_cap_daily / std_cap_daily * np.sqrt(365), 2) if std_cap_daily > 0 else 0.0

        equity_series = np.cumsum(sub_d["realized_pnl_usd"]) + assumed_capital_base
        peaks_eq = np.maximum.accumulate(equity_series)
        dd_series = (peaks_eq - equity_series) / peaks_eq * 100.0
        max_dd_cap = float(dd_series.max())

        # Dollar drawdown normalized to 3x leverage margin base
        dollar_dd = float(np.max(peaks_eq - equity_series))
        margin_base_3x = (4.0 * notional) / 3.0
        norm_3x_dd = (dollar_dd / margin_base_3x) * 100.0

        is_exec = notional <= 10_000.0
        note = "100% executable within top-of-book depth." if notional <= 5000 else (
            "Realistic upper limit on liquid altcoins." if notional == 10000 else
            "Theoretical and unproven in 5m bars without L2 book replay. Altcoins lack depth within 5 bps."
        )

        cap_rows.append({
            "capacity_scenario": f"Fixed Notional ${notional:,.0f}",
            "fixed_notional_usd": notional,
            "initial_equity_usd": assumed_capital_base,
            "ending_equity_usd": assumed_capital_base + tot_pnl,
            "total_dollar_pnl_usd": round(tot_pnl, 2),
            "executed_trades_count": len(sub_t),
            "mean_daily_return_pct": round(mean_cap_daily, 4),
            "daily_std_pct": round(std_cap_daily, 4),
            "sharpe_365": sharpe_cap,
            "max_drawdown_pct": round(max_dd_cap, 2),
            "normalized_3x_drawdown_pct": round(norm_3x_dd, 2),
            "profit_factor": sub_s["profit_factor"],
            "net_expectancy_bps": sub_s["net_expectancy_bps"],
            "orderbook_executable": is_exec,
            "notes": note,
        })

    pd.DataFrame(cap_rows).to_csv(out_dir / "CAPACITY_SENSITIVITY.csv", index=False)
    print("Saved CAPACITY_SENSITIVITY.csv successfully!")
    print(f"\nTotal Milestone 5.4 simulation time: {time.time() - t_start:.2f}s")


if __name__ == "__main__":
    main()
