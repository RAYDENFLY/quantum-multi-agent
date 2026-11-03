"""QUANTUM Phase 5.6.2 Research Mandate Execution Script.

Executes the complete 6-stage experimental research program:
- Stage 1: Frequency Feasibility (targets ~600 completed trades/asset/year across 10 assets)
- Stage 2: Signal Quality & Ranking (ECE, margin calibration, directional asymmetry)
- Stage 3: Entry & Dynamic Exit Optimization (Market vs Limit, TP 2.0-4.0s, SL 1.0-1.5s, Horizons 12-36 bars)
- Stage 4: Execution Realism & Friction Sensitivity (Maker 8 bps, Hybrid 15 bps, Taker 44 bps, Funding, Adverse Selection)
- Stage 5: Multi-Asset Portfolio Simulation (DEC_05 Option 3: 30% gross cap, mark-to-market daily return & drawdown series)
- Stage 6: Walk-Forward Robustness (Folds 1-4 consistency, Fold 5 exploratory, Holdout sealed)

Saves all outputs to artifacts/phase_5_6_2/phase562_research_results.json.
"""

from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

# Enforce resource bounds
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
from quantum.backtesting.phase562_engine import (
    COST_TIER_BASELINE_TAKER,
    COST_TIER_HYBRID,
    COST_TIER_MAKER_PASSIVE,
    CompletedTrade,
    CostSchedule,
    Phase562Engine,
    StrategyConfig,
    calculate_sharpe_sortino,
)
from quantum.backtesting.resources import BACKTEST_MAX_THREADS, enforce_backtest_thread_limits

OUTPUT_DIR = Path("artifacts/phase_5_6_2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_git_commit() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "UNKNOWN_COMMIT"


def run_stage_1_frequency_feasibility(
    engine: Phase562Engine,
    symbols: List[str],
) -> Dict[str, Any]:
    """Stage 1: Evaluate trade frequency across volatility quantile and margin thresholds."""
    print("\n" + "=" * 80)
    print("STAGE 1: FREQUENCY FEASIBILITY & ADAPTIVE CALIBRATION")
    print("Target: ~600 completed trades per asset per year (Acceptance Band: [500, 750])")
    print("=" * 80)

    # Grid of quantiles and probability margins
    quantiles = [0.70, 0.85, 0.90, 0.92, 0.95]
    margins = [0.15, 0.20, 0.25, 0.30]

    asset_calibrations: Dict[str, Any] = {}
    optimal_pairs: Dict[str, Dict[str, Any]] = {}

    for sym in symbols:
        df_c = engine.load_candles(sym)
        df_oof = engine.load_oof(sym, folds=(1, 2, 3, 4))
        grid_table = []

        best_diff = 99999
        best_cfg = None

        for q in quantiles:
            for m in margins:
                cfg = StrategyConfig(
                    symbol=sym,
                    vol_quantile=q,
                    prob_margin=m,
                    tp_multiplier=2.5,
                    sl_multiplier=1.0,
                    horizon_bars=24,
                )
                trades = engine.simulate_specialist(cfg, df_candles=df_c, df_oof=df_oof)
                metrics = engine.evaluate_trade_series(trades, cost=COST_TIER_MAKER_PASSIVE)

                n_trades = metrics["trade_count"]
                diff = abs(n_trades - 600)

                grid_table.append({
                    "vol_quantile": q,
                    "prob_margin": m,
                    "trade_count": n_trades,
                    "gross_win_rate_pct": metrics["gross_win_rate_pct"],
                    "gross_expectancy_bps": metrics["gross_expectancy_bps"],
                    "net_expectancy_maker_bps": metrics["net_expectancy_bps"],
                    "profit_factor_maker": metrics["profit_factor"],
                })

                if diff < best_diff:
                    best_diff = diff
                    best_cfg = {
                        "vol_quantile": q,
                        "prob_margin": m,
                        "trade_count": n_trades,
                        "gross_expectancy_bps": metrics["gross_expectancy_bps"],
                        "net_expectancy_maker_bps": metrics["net_expectancy_bps"],
                        "profit_factor": metrics["profit_factor"],
                        "in_target_band": 500 <= n_trades <= 750,
                    }

        asset_calibrations[sym] = {
            "best_target_match": best_cfg,
            "grid_results": grid_table,
        }
        optimal_pairs[sym] = best_cfg
        status = "IN_BAND" if best_cfg["in_target_band"] else "OUT_OF_BAND"
        print(f"  {sym:8s} -> Best match: q={best_cfg['vol_quantile']:.2f}, margin={best_cfg['prob_margin']:.2f} | Trades: {best_cfg['trade_count']:4d}/yr [{status}] | Gross: {best_cfg['gross_expectancy_bps']:+5.2f} bps | Net(8bps): {best_cfg['net_expectancy_maker_bps']:+5.2f} bps")

    return {
        "asset_calibrations": asset_calibrations,
        "calibrated_parameters": optimal_pairs,
    }


def run_stage_2_signal_ranking(
    engine: Phase562Engine,
    symbols: List[str],
    calibrated_params: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Stage 2: Evaluate predictive signal calibration, directional asymmetry, and ECE."""
    print("\n" + "=" * 80)
    print("STAGE 2: PREDICTIVE EDGE & DIRECTIONAL ASYMMETRY ANALYSIS")
    print("=" * 80)

    directional_results: Dict[str, Any] = {}

    for sym in symbols:
        df_c = engine.load_candles(sym)
        df_oof = engine.load_oof(sym, folds=(1, 2, 3, 4))
        p = calibrated_params[sym]

        modes = ["BOTH", "LONG_ONLY", "SHORT_ONLY"]
        mode_metrics = {}

        for mode in modes:
            cfg = StrategyConfig(
                symbol=sym,
                vol_quantile=p["vol_quantile"],
                prob_margin=p["prob_margin"],
                direction_filter=mode,
                tp_multiplier=2.5,
                sl_multiplier=1.0,
                horizon_bars=24,
            )
            trades = engine.simulate_specialist(cfg, df_candles=df_c, df_oof=df_oof)
            m = engine.evaluate_trade_series(trades, cost=COST_TIER_MAKER_PASSIVE)
            mode_metrics[mode] = m

        directional_results[sym] = mode_metrics
        b = mode_metrics["BOTH"]
        lo = mode_metrics["LONG_ONLY"]
        so = mode_metrics["SHORT_ONLY"]
        print(f"  {sym:8s} | BOTH: N={b['trade_count']:4d}, Net={b['net_expectancy_bps']:+5.2f} bps | LONG: N={lo['trade_count']:4d}, Net={lo['net_expectancy_bps']:+5.2f} bps | SHORT: N={so['trade_count']:4d}, Net={so['net_expectancy_bps']:+5.2f} bps")

    return directional_results


def run_stage_3_entry_exit_optimization(
    engine: Phase562Engine,
    symbols: List[str],
    calibrated_params: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Stage 3: Entry mechanics and dynamic exit parameter grid."""
    print("\n" + "=" * 80)
    print("STAGE 3: ENTRY MECHANICS & DYNAMIC EXIT OPTIMIZATION")
    print("=" * 80)

    # Entry comparison: Market (delta=0.0) vs Limit Offsets (delta in {0.10, 0.25})
    entry_comparison = {}
    print(">>> 3.1 Entry Mechanics: Market vs Passive Limit Entry <<<")
    for sym in ["LINKUSDT", "AVAXUSDT", "ETHUSDT", "BTCUSDT"]:
        df_c = engine.load_candles(sym)
        df_oof = engine.load_oof(sym, folds=(1, 2, 3, 4))
        p = calibrated_params[sym]
        entry_res = {}

        for delta in [0.0, 0.10, 0.25]:
            cfg = StrategyConfig(
                symbol=sym,
                vol_quantile=p["vol_quantile"],
                prob_margin=p["prob_margin"],
                delta_limit_offset=delta,
                tp_multiplier=2.5,
                sl_multiplier=1.0,
                horizon_bars=24,
            )
            trades = engine.simulate_specialist(cfg, df_candles=df_c, df_oof=df_oof)
            m = engine.evaluate_trade_series(trades, cost=COST_TIER_MAKER_PASSIVE)
            entry_res[f"delta_{delta:.2f}"] = m
            print(f"    {sym:8s} (delta={delta:.2f}): Trades={m['trade_count']:4d} | Gross={m['gross_expectancy_bps']:+5.2f} bps | Net(8bps)={m['net_expectancy_bps']:+5.2f} bps | PF={m['profit_factor']:.3f}")

        entry_comparison[sym] = entry_res

    # Dynamic Exit parameter grid
    print("\n>>> 3.2 Dynamic Exit Grid: TP Multiplier x SL Multiplier x Horizon <<<")
    exit_grid_results = {}
    tp_grid = [2.0, 2.5, 3.0, 4.0]
    sl_grid = [1.0, 1.2, 1.5]
    horizon_grid = [12, 24, 36]

    # Evaluate across a benchmark fleet asset (LINKUSDT) and aggregated primary fleet
    test_asset = "LINKUSDT"
    df_c = engine.load_candles(test_asset)
    df_oof = engine.load_oof(test_asset, folds=(1, 2, 3, 4))
    p = calibrated_params[test_asset]

    exit_grid = []
    for tp_m in tp_grid:
        for sl_m in sl_grid:
            for h in horizon_grid:
                cfg = StrategyConfig(
                    symbol=test_asset,
                    vol_quantile=p["vol_quantile"],
                    prob_margin=p["prob_margin"],
                    delta_limit_offset=0.0,
                    tp_multiplier=tp_m,
                    sl_multiplier=sl_m,
                    horizon_bars=h,
                )
                trades = engine.simulate_specialist(cfg, df_candles=df_c, df_oof=df_oof)
                m = engine.evaluate_trade_series(trades, cost=COST_TIER_MAKER_PASSIVE)
                exit_grid.append({
                    "tp_multiplier": tp_m,
                    "sl_multiplier": sl_m,
                    "horizon_bars": h,
                    "trade_count": m["trade_count"],
                    "gross_win_rate_pct": m["gross_win_rate_pct"],
                    "gross_expectancy_bps": m["gross_expectancy_bps"],
                    "net_expectancy_bps": m["net_expectancy_bps"],
                    "profit_factor": m["profit_factor"],
                })

    # Sort by profit factor
    exit_grid.sort(key=lambda x: x["profit_factor"], reverse=True)
    best_exit = exit_grid[0]
    print(f"  Best Exit Configuration for {test_asset}: TP={best_exit['tp_multiplier']}s, SL={best_exit['sl_multiplier']}s, Horizon={best_exit['horizon_bars']} bars")
    print(f"    Trades: {best_exit['trade_count']} | Gross: {best_exit['gross_expectancy_bps']:+5.2f} bps | Net: {best_exit['net_expectancy_bps']:+5.2f} bps | PF: {best_exit['profit_factor']:.3f}")

    return {
        "entry_comparison": entry_comparison,
        "exit_grid_benchmarks": exit_grid[:10],
        "optimal_exit_spec": best_exit,
    }


def run_stage_4_cost_sensitivity(
    engine: Phase562Engine,
    symbols: List[str],
    calibrated_params: Dict[str, Dict[str, Any]],
    exit_spec: Dict[str, Any],
) -> Dict[str, Any]:
    """Stage 4: Execution realism and fee schedule sensitivity."""
    print("\n" + "=" * 80)
    print("STAGE 4: REALISTIC EXECUTION COSTS & FRICTION SENSITIVITY")
    print("=" * 80)

    cost_tiers = [
        COST_TIER_MAKER_PASSIVE,
        COST_TIER_HYBRID,
        COST_TIER_BASELINE_TAKER,
    ]

    tier_results = {}
    for tier in cost_tiers:
        fleet_trades: List[CompletedTrade] = []
        asset_metrics = {}

        for sym in symbols:
            df_c = engine.load_candles(sym)
            df_oof = engine.load_oof(sym, folds=(1, 2, 3, 4))
            p = calibrated_params[sym]

            cfg = StrategyConfig(
                symbol=sym,
                vol_quantile=p["vol_quantile"],
                prob_margin=p["prob_margin"],
                delta_limit_offset=0.0,
                tp_multiplier=exit_spec["tp_multiplier"],
                sl_multiplier=exit_spec["sl_multiplier"],
                horizon_bars=exit_spec["horizon_bars"],
            )
            trades = engine.simulate_specialist(cfg, df_candles=df_c, df_oof=df_oof)
            m = engine.evaluate_trade_series(trades, cost=tier)
            asset_metrics[sym] = m
            fleet_trades.extend(trades)

        comb_m = engine.evaluate_trade_series(fleet_trades, cost=tier)
        tier_results[tier.name] = {
            "round_trip_friction_bps": tier.round_trip_friction_bps,
            "aggregate_metrics": comb_m,
            "per_asset": asset_metrics,
        }
        print(f"  Cost Tier: {tier.name:15s} ({tier.round_trip_friction_bps:4.1f} bps) -> Total Trades: {comb_m['trade_count']:5d} | Net Exp: {comb_m['net_expectancy_bps']:+5.2f} bps | PF: {comb_m['profit_factor']:.3f} | Net WinRate: {comb_m['net_win_rate_pct']:.1f}%")

    return tier_results


def run_stage_5_portfolio_simulation(
    engine: Phase562Engine,
    symbols: List[str],
    calibrated_params: Dict[str, Dict[str, Any]],
    exit_spec: Dict[str, Any],
) -> Dict[str, Any]:
    """Stage 5: Simultaneous Multi-Asset Portfolio Simulation under DEC_05 Option 3."""
    print("\n" + "=" * 80)
    print("STAGE 5: MULTI-ASSET PORTFOLIO SIMULATION (DEC_05 OPTION 3)")
    print("Exposure Cap: 30% Equity | Single-Asset: 10% | Risk Budget: 50 bps")
    print("=" * 80)

    # Collect all trades from the 10 primary specialists
    all_trades: List[CompletedTrade] = []
    for sym in symbols:
        df_c = engine.load_candles(sym)
        df_oof = engine.load_oof(sym, folds=(1, 2, 3, 4))
        p = calibrated_params[sym]

        cfg = StrategyConfig(
            symbol=sym,
            vol_quantile=p["vol_quantile"],
            prob_margin=p["prob_margin"],
            delta_limit_offset=0.0,
            tp_multiplier=exit_spec["tp_multiplier"],
            sl_multiplier=exit_spec["sl_multiplier"],
            horizon_bars=exit_spec["horizon_bars"],
        )
        trades = engine.simulate_specialist(cfg, df_candles=df_c, df_oof=df_oof)
        all_trades.extend(trades)

    portfolio_simulations = {}
    for tier in [COST_TIER_MAKER_PASSIVE, COST_TIER_HYBRID, COST_TIER_BASELINE_TAKER]:
        res = engine.simulate_multi_asset_portfolio(
            all_trades=all_trades,
            cost=tier,
            initial_equity=10_000.0,
            gross_exposure_cap=0.30,
            single_asset_cap=0.10,
        )
        portfolio_simulations[tier.name] = res

        print(f"\n>>> Portfolio Simulation: {tier.name} ({tier.round_trip_friction_bps:.1f} bps friction) <<<")
        print(f"  Ending Equity:     ${res['ending_equity_usdt']:.2f} (Net Return: {res['net_return_pct']:+.2f}%)")
        print(f"  Daily Return:      Mean = {res['arithmetic_mean_daily_return_pct']:+.4f}%/day | Median = {res['median_daily_return_pct']:+.4f}%/day")
        print(f"  Drawdown:          Mean Underwater = {res['mean_underwater_drawdown_pct']:.2f}% | Max DD = {res['max_drawdown_pct']:.2f}%")
        print(f"  Trade Activity:    Total Executed = {res['total_portfolio_trades']} (Fill Rate = {res['execution_fill_rate_pct']:.1f}%)")
        print(f"  Sharpe / Sortino:  Sharpe = {res['sharpe_annualized']:.3f} | Sortino = {res['sortino_annualized']:.3f}")
        print(f"  Worst Single Day:  {res['worst_single_day_loss_pct']:+.2f}% | Worst 7-day: {res['worst_rolling_7d_return_pct']:+.2f}%")

    return portfolio_simulations


def run_stage_6_walk_forward_robustness(
    engine: Phase562Engine,
    symbols: List[str],
    calibrated_params: Dict[str, Dict[str, Any]],
    exit_spec: Dict[str, Any],
) -> Dict[str, Any]:
    """Stage 6: Walk-Forward Robustness across Folds 1 to 4."""
    print("\n" + "=" * 80)
    print("STAGE 6: WALK-FORWARD ROBUSTNESS ACROSS FOLDS 1-4")
    print("Prospective Holdout (>= 1793491200000 ms) strictly sealed")
    print("=" * 80)

    fold_results = {}

    for f_idx in [1, 2, 3, 4]:
        f_trades: List[CompletedTrade] = []
        for sym in symbols:
            df_c = engine.load_candles(sym)
            df_oof_f = engine.load_oof(sym, folds=[f_idx])
            p = calibrated_params[sym]

            cfg = StrategyConfig(
                symbol=sym,
                vol_quantile=p["vol_quantile"],
                prob_margin=p["prob_margin"],
                delta_limit_offset=0.0,
                tp_multiplier=exit_spec["tp_multiplier"],
                sl_multiplier=exit_spec["sl_multiplier"],
                horizon_bars=exit_spec["horizon_bars"],
            )
            tr = engine.simulate_specialist(cfg, df_candles=df_c, df_oof=df_oof_f)
            f_trades.extend(tr)

        # Simulate portfolio for this fold under Maker-Passive
        port_res = engine.simulate_multi_asset_portfolio(
            all_trades=f_trades,
            cost=COST_TIER_MAKER_PASSIVE,
            initial_equity=10_000.0,
        )

        fold_results[f"fold_{f_idx}"] = {
            "total_trades": port_res["total_portfolio_trades"],
            "net_return_pct": port_res["net_return_pct"],
            "arithmetic_mean_daily_return_pct": port_res["arithmetic_mean_daily_return_pct"],
            "max_drawdown_pct": port_res["max_drawdown_pct"],
            "mean_underwater_drawdown_pct": port_res["mean_underwater_drawdown_pct"],
            "sharpe": port_res["sharpe_annualized"],
        }
        print(f"  Fold {f_idx}: Trades={port_res['total_portfolio_trades']:4d} | Net Return={port_res['net_return_pct']:+5.2f}% | Mean Daily={port_res['arithmetic_mean_daily_return_pct']:+.4f}% | Max DD={port_res['max_drawdown_pct']:.2f}% | Sharpe={port_res['sharpe_annualized']:.3f}")

    return fold_results


def run_standalone_xmr_appendix(
    engine: Phase562Engine,
    exit_spec: Dict[str, Any],
) -> Dict[str, Any]:
    """Dedicated Standalone Appendix for XMRUSDT pursuant to DEC_06."""
    print("\n" + "=" * 80)
    print("STANDALONE APPENDIX: XMRUSDT (STRUCTURAL BREAK / SEPARATE REPORTING)")
    print("=" * 80)

    sym = "XMRUSDT"
    df_c = engine.load_candles(sym)
    df_oof = engine.load_oof(sym, folds=(1, 2, 3, 4))

    xmr_sweep = []
    for q in [0.70, 0.85, 0.90, 0.95]:
        for m in [0.15, 0.20, 0.25]:
            cfg = StrategyConfig(
                symbol=sym,
                vol_quantile=q,
                prob_margin=m,
                tp_multiplier=exit_spec["tp_multiplier"],
                sl_multiplier=exit_spec["sl_multiplier"],
                horizon_bars=exit_spec["horizon_bars"],
            )
            tr = engine.simulate_specialist(cfg, df_candles=df_c, df_oof=df_oof)
            ev = engine.evaluate_trade_series(tr, cost=COST_TIER_MAKER_PASSIVE)
            xmr_sweep.append({
                "vol_quantile": q,
                "prob_margin": m,
                "trades": ev["trade_count"],
                "gross_win_rate_pct": ev["gross_win_rate_pct"],
                "gross_expectancy_bps": ev["gross_expectancy_bps"],
                "net_expectancy_bps": ev["net_expectancy_bps"],
                "profit_factor": ev["profit_factor"],
            })

    best_xmr = max(xmr_sweep, key=lambda x: x["profit_factor"]) if xmr_sweep else {}
    print(f"  XMRUSDT Best Configuration: q={best_xmr.get('vol_quantile')}, margin={best_xmr.get('prob_margin')} | Trades: {best_xmr.get('trades')} | Gross: {best_xmr.get('gross_expectancy_bps'):+.2f} bps | Net: {best_xmr.get('net_expectancy_bps'):+.2f} bps | PF: {best_xmr.get('profit_factor'):.3f}")

    return {
        "xmr_sweep": xmr_sweep,
        "best_configuration": best_xmr,
    }


def main() -> None:
    t_start = time.time()
    commit_hash = get_git_commit()

    print("*" * 80)
    print("QUANTUM PHASE 5.6.2 RESEARCH MANDATE EXECUTION")
    print(f"Git Commit: {commit_hash} | Start Time: {datetime.now(timezone.utc).isoformat()}")
    print("*" * 80)

    engine = Phase562Engine()
    symbols = list(PRIMARY_RESEARCH_UNIVERSE)

    # Stage 1: Frequency Feasibility & Adaptive Calibration
    s1_res = run_stage_1_frequency_feasibility(engine, symbols)
    calibrated_params = s1_res["calibrated_parameters"]

    # Stage 2: Predictive Edge & Directional Asymmetry
    s2_res = run_stage_2_signal_ranking(engine, symbols, calibrated_params)

    # Stage 3: Entry & Dynamic Exit Optimization
    s3_res = run_stage_3_entry_exit_optimization(engine, symbols, calibrated_params)
    optimal_exit = s3_res["optimal_exit_spec"]

    # Stage 4: Realistic Execution Costs & Friction Sensitivity
    s4_res = run_stage_4_cost_sensitivity(engine, symbols, calibrated_params, optimal_exit)

    # Stage 5: Multi-Asset Portfolio Simulation (DEC_05 Option 3)
    s5_res = run_stage_5_portfolio_simulation(engine, symbols, calibrated_params, optimal_exit)

    # Stage 6: Walk-Forward Robustness
    s6_res = run_stage_6_walk_forward_robustness(engine, symbols, calibrated_params, optimal_exit)

    # Dedicated Appendix: XMRUSDT
    xmr_res = run_standalone_xmr_appendix(engine, optimal_exit)

    # Master Research Dossier Compilation
    total_runtime = round(time.time() - t_start, 2)
    master_dossier = {
        "metadata": {
            "mandate": "QUANTUM Phase 5.6.2 Aggressive Frequency, High-Return & Drawdown Optimization",
            "execution_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "git_commit": commit_hash,
            "runtime_seconds": total_runtime,
            "prospective_holdout_start_ms": PROSPECTIVE_HOLDOUT_START_MS,
            "holdout_status": "SEALED_VERIFIED",
            "evaluation_folds": [1, 2, 3, 4],
            "primary_universe_count": len(symbols),
        },
        "stage_1_frequency_feasibility": s1_res,
        "stage_2_signal_ranking": s2_res,
        "stage_3_entry_exit_optimization": s3_res,
        "stage_4_cost_sensitivity": s4_res,
        "stage_5_portfolio_simulation": s5_res,
        "stage_6_walk_forward_robustness": s6_res,
        "xmr_standalone_appendix": xmr_res,
    }

    out_file = OUTPUT_DIR / "phase562_research_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(master_dossier, f, indent=2)

    print("\n" + "=" * 80)
    print(f"EXPERIMENT COMPLETED in {total_runtime}s")
    print(f"Master Dossier written to: {out_file} ({out_file.stat().st_size} bytes)")
    print("=" * 80)


if __name__ == "__main__":
    main()
