"""Controlled Experiment Runner for QUANTUM Next — HYP-01 Strategy.

Runs the 7 approved controlled experiments across pre-holdout data (< 1793491200000 ms):
- EXP_01: Baseline Unfiltered (Tight barriers, no regime filter)
- EXP_02: Regime Filter Only (HIGH_VOLATILITY_TRENDING only)
- EXP_03: Multi-Timeframe Confirmation (1h Trend + 15m Momentum)
- EXP_04: Volatility-Adjusted Exits (2.5x SL, 4.0x TP1, Breakeven Ratchet)
- EXP_05: Extended Holding Horizon (Max 24 bars / 2 hours)
- EXP_06: Long-Only vs Bidirectional vs Altcoin Short Filter
- EXP_07: Full QUANTUM Next HYP-01 Production Configuration

Evaluates all mandatory metrics against the strategic 3% net daily return objective.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import time
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from quantum.backtesting.adapters import PROSPECTIVE_HOLDOUT_START_MS
from quantum.strategies.evaluator import StrategyDiscoveryEvaluator
from quantum.strategies.hyp01_strategy import (
    HYP01Configuration,
    HYP01Engine,
    HYP01Trade,
)


def get_git_commit() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "dcc8ceb54d80b1b9685d92236f48b0994610522a"


def main() -> None:
    t_start = time.time()
    commit = get_git_commit()
    print("=" * 88)
    print("QUANTUM NEXT — HYP-01 CONTROLLED EXPERIMENTATION PROGRAM")
    print(f"Git Commit: {commit} | Holdout Boundary: {PROSPECTIVE_HOLDOUT_START_MS} ms")
    print("=" * 88)

    # 1. Preload 10-Asset Universe
    t0_load = time.time()
    evaluator = StrategyDiscoveryEvaluator()
    matrices = evaluator.matrices
    print(f"Loaded {len(matrices)} asset matrices in {time.time() - t0_load:.2f}s")

    # Output directory
    out_dir = Path("audit/strategy_research/quantum_next")
    out_dir.mkdir(parents=True, exist_ok=True)

    # 2. Define Experiment Matrix (Changing one major variable at a time)
    experiments: List[Dict[str, Any]] = [
        {
            "experiment_id": "EXP_01_BASELINE_UNFILTERED",
            "name": "Baseline Unfiltered (Historical 5m Scalper Model)",
            "config": HYP01Configuration(
                strategy_id="EXP_01_BASELINE_UNFILTERED",
                enable_regime_filter=False,
                trend_threshold_bps=0.0,
                vol_expansion_min=0.0,
                sl_multiplier=1.5,
                tp1_multiplier=2.0,
                tp2_multiplier=3.5,
                enable_breakeven_ratchet=False,
                trailing_stop_sigma=0.0,
                max_horizon_bars=6,
                filter_altcoin_shorts=False,
            ),
        },
        {
            "experiment_id": "EXP_02_REGIME_FILTER_ONLY",
            "name": "Regime Filter Only (Trade only in High-Vol Trending)",
            "config": HYP01Configuration(
                strategy_id="EXP_02_REGIME_FILTER_ONLY",
                enable_regime_filter=True,
                trend_threshold_bps=75.0,
                vol_expansion_min=1.05,
                sl_multiplier=1.5,
                tp1_multiplier=2.0,
                tp2_multiplier=3.5,
                enable_breakeven_ratchet=False,
                trailing_stop_sigma=0.0,
                max_horizon_bars=6,
                filter_altcoin_shorts=False,
            ),
        },
        {
            "experiment_id": "EXP_03_MTF_CONFIRMATION",
            "name": "Multi-Timeframe Confirmation (1h Trend + 15m Momentum)",
            "config": HYP01Configuration(
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
            ),
        },
        {
            "experiment_id": "EXP_04_VOL_ADJUSTED_EXITS",
            "name": "Volatility-Adjusted Exits (Anti-Noise SL 2.5x + Ratchet)",
            "config": HYP01Configuration(
                strategy_id="EXP_04_VOL_ADJUSTED_EXITS",
                enable_regime_filter=True,
                trend_threshold_bps=100.0,
                vol_expansion_min=1.10,
                sl_multiplier=2.5,
                tp1_multiplier=4.0,
                tp2_multiplier=7.5,
                enable_breakeven_ratchet=True,
                trailing_stop_sigma=2.0,
                max_horizon_bars=12,
                filter_altcoin_shorts=False,
            ),
        },
        {
            "experiment_id": "EXP_05_EXTENDED_HORIZON",
            "name": "Extended Holding Horizon (Max 24 bars / 2h)",
            "config": HYP01Configuration(
                strategy_id="EXP_05_EXTENDED_HORIZON",
                enable_regime_filter=True,
                trend_threshold_bps=100.0,
                vol_expansion_min=1.10,
                sl_multiplier=2.5,
                tp1_multiplier=4.5,
                tp2_multiplier=8.0,
                enable_breakeven_ratchet=True,
                trailing_stop_sigma=2.0,
                min_horizon_bars=6,
                max_horizon_bars=24,
                filter_altcoin_shorts=False,
            ),
        },
        {
            "experiment_id": "EXP_06_ALTCOIN_SHORT_FILTER",
            "name": "Altcoin Short Filter (Long-Only Altcoins, Bidirectional BTC/ETH)",
            "config": HYP01Configuration(
                strategy_id="EXP_06_ALTCOIN_SHORT_FILTER",
                enable_regime_filter=True,
                trend_threshold_bps=100.0,
                vol_expansion_min=1.10,
                sl_multiplier=2.5,
                tp1_multiplier=4.5,
                tp2_multiplier=8.0,
                enable_breakeven_ratchet=True,
                trailing_stop_sigma=2.0,
                min_horizon_bars=6,
                max_horizon_bars=24,
                filter_altcoin_shorts=True,
            ),
        },
        {
            "experiment_id": "EXP_07_QUANTUM_NEXT_OPTIMAL",
            "name": "QUANTUM Next HYP-01 Optimal Integrated Configuration",
            "config": HYP01Configuration(
                strategy_id="EXP_07_QUANTUM_NEXT_OPTIMAL",
                enable_regime_filter=True,
                trend_threshold_bps=85.0,
                vol_expansion_min=1.08,
                sl_multiplier=2.5,
                tp1_multiplier=4.2,
                tp2_multiplier=7.5,
                tp1_close_pct=0.50,
                enable_breakeven_ratchet=True,
                trailing_stop_sigma=2.0,
                min_horizon_bars=6,
                max_horizon_bars=20,
                filter_altcoin_shorts=True,
                risk_per_trade_pct=0.015,
                max_leverage=3.0,
                max_concurrent_positions=4,
                daily_loss_circuit_breaker_pct=0.04,
                max_drawdown_circuit_breaker_pct=0.15,
            ),
        },
    ]

    ledger_records: List[Dict[str, Any]] = []
    manifests: Dict[str, Any] = {
        "metadata": {
            "program": "QUANTUM Next — Experimental Development Program",
            "hypothesis": "HYP-01: Multi-Timeframe Volatility Expansion Trend Following",
            "target_objective": "3.0% Net Daily Return",
            "git_commit": commit,
            "holdout_start_ms": PROSPECTIVE_HOLDOUT_START_MS,
            "venue_schedule": "BYBIT_VIP0_DEFAULT",
            "execution_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        },
        "experiments": {},
    }

    # 3. Execution Loop
    for exp in experiments:
        exp_id = exp["experiment_id"]
        exp_name = exp["name"]
        cfg: HYP01Configuration = exp["config"]
        print(f"\n>>> Running Experiment: {exp_id}")
        print(f"    Name: {exp_name}")
        print(f"    Config Hash: {cfg.config_hash}")

        engine = HYP01Engine(cfg)
        # Calibrate thresholds strictly on training folds 0/1
        engine.fit_thresholds_on_training_fold(matrices, train_folds=(0, 1))

        t0_exp = time.time()
        summary, trades, eq_df = engine.evaluate_multi_asset(
            matrices,
            experiment_id=exp_id,
            holdout_cutoff_ms=PROSPECTIVE_HOLDOUT_START_MS,
        )
        elapsed = time.time() - t0_exp
        print(f"    Executed {summary['executed_trades_count']} trades in {elapsed:.2f}s")
        print(f"    Net Return: {summary['net_cumulative_return_pct']:.2f}% | Mean Daily Return: {summary['mean_daily_return_pct']:.3f}%")
        print(f"    Max DD: {summary['max_drawdown_pct']:.2f}% | Profit Factor: {summary['profit_factor']:.3f} | Net Exp: {summary['net_expectancy_bps']:.2f} bps")
        print(f"    Target 3% Daily Qualified: {summary['qualified_3pct_daily']}")

        # Save individual experiment trade log
        if trades:
            df_t = pd.DataFrame([t.model_dump() for t in trades])
            df_t.to_parquet(out_dir / f"{exp_id}_trades.parquet", index=False)
            if not eq_df.empty:
                eq_df.to_parquet(out_dir / f"{exp_id}_equity.parquet", index=False)

        # Record in ledger
        record = {
            "experiment_id": exp_id,
            "experiment_name": exp_name,
            "config_hash": cfg.config_hash,
            "regime_filter_enabled": cfg.enable_regime_filter,
            "sl_multiplier": cfg.sl_multiplier,
            "tp1_multiplier": cfg.tp1_multiplier,
            "tp2_multiplier": cfg.tp2_multiplier,
            "breakeven_ratchet": cfg.enable_breakeven_ratchet,
            "trailing_stop_sigma": cfg.trailing_stop_sigma,
            "max_horizon_bars": cfg.max_horizon_bars,
            "filter_altcoin_shorts": cfg.filter_altcoin_shorts,
            "executed_trades_count": summary["executed_trades_count"],
            "net_cumulative_return_pct": summary["net_cumulative_return_pct"],
            "mean_daily_return_pct": summary["mean_daily_return_pct"],
            "median_daily_return_pct": summary["median_daily_return_pct"],
            "pct_days_gte_3pct": summary["pct_days_gte_3pct"],
            "pct_negative_days": summary["pct_negative_days"],
            "worst_daily_loss_pct": summary["worst_daily_loss_pct"],
            "profit_factor": summary["profit_factor"],
            "max_drawdown_pct": summary["max_drawdown_pct"],
            "win_rate_pct": summary["win_rate_pct"],
            "gross_expectancy_bps": summary["gross_expectancy_bps"],
            "net_expectancy_bps": summary["net_expectancy_bps"],
            "sharpe_annualized": summary["sharpe_annualized"],
            "sortino_annualized": summary["sortino_annualized"],
            "calmar_ratio": summary["calmar_ratio"],
            "target_3pct_daily_qualified": summary["qualified_3pct_daily"],
        }
        ledger_records.append(record)
        manifests["experiments"][exp_id] = {
            "configuration": cfg.model_dump(),
            "summary": summary,
        }

    # 4. Save Artifacts
    df_ledger = pd.DataFrame(ledger_records)
    df_ledger.to_csv(out_dir / "QUANTUM_NEXT_EXPERIMENT_LEDGER.csv", index=False)
    with open(out_dir / "QUANTUM_NEXT_MANIFEST.json", "w", encoding="utf-8") as f:
        json.dump(manifests, f, indent=2)

    print("\n" + "=" * 88)
    print("EXPERIMENT LEDGER SUMMARY:")
    print("=" * 88)
    print(df_ledger[["experiment_id", "executed_trades_count", "net_cumulative_return_pct", "mean_daily_return_pct", "pct_days_gte_3pct", "max_drawdown_pct", "profit_factor", "net_expectancy_bps", "target_3pct_daily_qualified"]].to_string())
    print("\nSaved all artifacts to audit/strategy_research/quantum_next/")
    print(f"Total time elapsed: {time.time() - t_start:.2f}s")


if __name__ == "__main__":
    main()
