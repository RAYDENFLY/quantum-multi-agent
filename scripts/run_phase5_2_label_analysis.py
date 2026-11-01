"""Phase 5.2 Label Quality Analysis and Robustness Sensitivity Script.

Evaluates 5m canonical datasets for all 11 target instruments:
- Candidate multiplier 1.5 (primary analysis)
- Sensitivity multipliers 1.0, 1.5, 2.0
- Breakdown by instrument, by year, by market regime
- Exports detailed summary metrics for documentation deliverables.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import time
import numpy as np
import pandas as pd

from quantum.domain.enums import Exchange, Timeframe
from quantum.features.engine import FeatureEngine
from quantum.features.labeling import BarrierOutcome, TripleBarrierLabelGenerator
from quantum.features.temporal_split import (
    DEVELOPMENT_END_MS,
    DEVELOPMENT_START_MS,
    FINAL_HOLDOUT_END_MS,
    FINAL_HOLDOUT_START_MS,
    VALIDATION_END_MS,
    VALIDATION_START_MS,
    TemporalPartition,
    TemporalPartitionManager,
)
from quantum.historical.storage import ParquetStorageManager

BASE_DIR = Path("data/historical")
EXCHANGE = Exchange.ASTER
SYMBOLS = [
    "ADAUSDT", "XRPUSDT", "BTCUSDT", "BNBUSDT", "ETHUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "XMRUSDT", "DOGEUSDT", "LTCUSDT"
]
TIMEFRAME = Timeframe.M5
MULTIPLIERS = [1.0, 1.5, 2.0]


def profile_labels(labeled_df: pd.DataFrame, trend_series: pd.Series) -> dict:
    """Compute detailed quality and distribution metrics from labeled DataFrame."""
    total_samples = len(labeled_df)
    
    # Class counts
    tp_mask = labeled_df["label"] == BarrierOutcome.TP.value
    sl_mask = labeled_df["label"] == BarrierOutcome.SL.value
    exp_mask = labeled_df["label"] == BarrierOutcome.TIME_EXPIRATION.value
    amb_mask = labeled_df["label"] == BarrierOutcome.AMBIGUOUS.value
    exc_mask = labeled_df["label"] == BarrierOutcome.EXCLUDED.value
    
    tp_count = int(tp_mask.sum())
    sl_count = int(sl_mask.sum())
    exp_count = int(exp_mask.sum())
    amb_count = int(amb_mask.sum())
    exc_count = int(exc_mask.sum())
    
    # Eligible samples = TP + SL + EXP
    eligible_count = tp_count + sl_count + exp_count
    
    tp_pct = (tp_count / eligible_count * 100.0) if eligible_count > 0 else 0.0
    sl_pct = (sl_count / eligible_count * 100.0) if eligible_count > 0 else 0.0
    exp_pct = (exp_count / eligible_count * 100.0) if eligible_count > 0 else 0.0
    amb_pct = (amb_count / total_samples * 100.0) if total_samples > 0 else 0.0
    exc_pct = (exc_count / total_samples * 100.0) if total_samples > 0 else 0.0

    # Year breakdown on eligible samples
    dts = pd.to_datetime(labeled_df["open_time_ms"], unit="ms", utc=True)
    years = dts.dt.year.to_numpy()
    year_stats = {}
    for y in sorted(list(set(years))):
        y_mask = (years == y) & (tp_mask | sl_mask | exp_mask)
        y_eligible = int(y_mask.sum())
        if y_eligible > 0:
            y_tp = int((tp_mask & (years == y)).sum())
            y_sl = int((sl_mask & (years == y)).sum())
            y_exp = int((exp_mask & (years == y)).sum())
            year_stats[str(y)] = {
                "eligible": y_eligible,
                "tp_count": y_tp,
                "tp_pct": round(y_tp / y_eligible * 100.0, 2),
                "sl_count": y_sl,
                "sl_pct": round(y_sl / y_eligible * 100.0, 2),
                "exp_count": y_exp,
                "exp_pct": round(y_exp / y_eligible * 100.0, 2),
            }

    # Partition breakdown (Development, Validation, Final Holdout)
    partition_stats = {}
    timestamps = labeled_df["open_time_ms"].to_numpy()
    for part, (start_ms, end_ms) in [
        ("DEVELOPMENT", (DEVELOPMENT_START_MS, DEVELOPMENT_END_MS)),
        ("VALIDATION", (VALIDATION_START_MS, VALIDATION_END_MS)),
        ("FINAL_HOLDOUT", (FINAL_HOLDOUT_START_MS, FINAL_HOLDOUT_END_MS)),
    ]:
        p_mask = (timestamps >= start_ms) & (timestamps <= end_ms) & (tp_mask | sl_mask | exp_mask)
        p_eligible = int(p_mask.sum())
        if p_eligible > 0:
            p_tp = int((tp_mask & (timestamps >= start_ms) & (timestamps <= end_ms)).sum())
            p_sl = int((sl_mask & (timestamps >= start_ms) & (timestamps <= end_ms)).sum())
            p_exp = int((exp_mask & (timestamps >= start_ms) & (timestamps <= end_ms)).sum())
            partition_stats[part] = {
                "eligible": p_eligible,
                "tp_count": p_tp,
                "tp_pct": round(p_tp / p_eligible * 100.0, 2),
                "sl_count": p_sl,
                "sl_pct": round(p_sl / p_eligible * 100.0, 2),
                "exp_count": p_exp,
                "exp_pct": round(p_exp / p_eligible * 100.0, 2),
            }

    # Regime breakdown (Bullish vs Bearish vs Neutral)
    regime_stats = {}
    if trend_series is not None and not trend_series.empty:
        trend_vals = trend_series.to_numpy()
        for reg_name, reg_val in [("BULLISH", 1.0), ("BEARISH", -1.0), ("NEUTRAL", 0.0)]:
            r_mask = (trend_vals == reg_val) & (tp_mask | sl_mask | exp_mask)
            r_eligible = int(r_mask.sum())
            if r_eligible > 0:
                r_tp = int((tp_mask & (trend_vals == reg_val)).sum())
                r_sl = int((sl_mask & (trend_vals == reg_val)).sum())
                r_exp = int((exp_mask & (trend_vals == reg_val)).sum())
                regime_stats[reg_name] = {
                    "eligible": r_eligible,
                    "tp_count": r_tp,
                    "tp_pct": round(r_tp / r_eligible * 100.0, 2),
                    "sl_count": r_sl,
                    "sl_pct": round(r_sl / r_eligible * 100.0, 2),
                    "exp_count": r_exp,
                    "exp_pct": round(r_exp / r_eligible * 100.0, 2),
                }

    # Exclusion reason counts
    exc_reasons = labeled_df["exclusion_reason"].value_counts().to_dict()

    return {
        "total_samples": total_samples,
        "eligible_samples": eligible_count,
        "tp_count": tp_count,
        "tp_pct": round(tp_pct, 2),
        "sl_count": sl_count,
        "sl_pct": round(sl_pct, 2),
        "exp_count": exp_count,
        "exp_pct": round(exp_pct, 2),
        "ambiguous_count": amb_count,
        "ambiguous_pct": round(amb_pct, 4),
        "excluded_count": exc_count,
        "excluded_pct": round(exc_pct, 2),
        "year_stats": year_stats,
        "partition_stats": partition_stats,
        "regime_stats": regime_stats,
        "exclusion_reasons": exc_reasons,
    }


def main():
    print("=" * 80)
    print("QUANTUM PHASE 5.2: TRIPLE-BARRIER LABELING & SENSITIVITY ANALYSIS")
    print(f"Timeframe: 5m | Horizon: 12 bars (60 min) | Volatility Lookback: 20 bars")
    print(f"Candidate Multiplier: 1.5 | Sensitivity Multipliers: {MULTIPLIERS}")
    print("=" * 80)

    storage = ParquetStorageManager(BASE_DIR)
    feature_engine = FeatureEngine()

    candidate_results = {}
    sensitivity_results = {m: {} for m in MULTIPLIERS}

    for idx, symbol in enumerate(SYMBOLS, 1):
        print(f"\n[{idx}/{len(SYMBOLS)}] Processing {symbol} 5m ...", flush=True)
        t0 = time.time()
        
        # Read canonical 5m candles
        df_can = storage.read_canonical(EXCHANGE, symbol, TIMEFRAME)
        if df_can.empty:
            print(f"  WARNING: No canonical candles found for {symbol} 5m")
            continue

        # Extract or compute trend_state for regime profiling
        # Using feature engine on canonical
        feats = feature_engine.compute_features(df_can)
        trend_series = feats["trend_state"]

        # Run primary candidate (1.5)
        gen_15 = TripleBarrierLabelGenerator(
            horizon_bars=12,
            volatility_lookback=20,
            barrier_multiplier=1.5,
            timeframe_ms=300_000,
        )
        labeled_15 = gen_15.generate_labels(df_can, enforce_partition_boundaries=True)
        stats_15 = profile_labels(labeled_15, trend_series)
        candidate_results[symbol] = stats_15
        sensitivity_results[1.5][symbol] = stats_15

        print(f"  Multiplier 1.5: Eligible={stats_15['eligible_samples']:,} | TP={stats_15['tp_pct']}% | SL={stats_15['sl_pct']}% | Exp={stats_15['exp_pct']}% | Amb={stats_15['ambiguous_count']}")

        # Run sensitivity multipliers (1.0 and 2.0)
        for m in [1.0, 2.0]:
            gen_m = TripleBarrierLabelGenerator(
                horizon_bars=12,
                volatility_lookback=20,
                barrier_multiplier=m,
                timeframe_ms=300_000,
            )
            labeled_m = gen_m.generate_labels(df_can, enforce_partition_boundaries=True)
            stats_m = profile_labels(labeled_m, trend_series)
            sensitivity_results[m][symbol] = stats_m
            print(f"  Multiplier {m}: Eligible={stats_m['eligible_samples']:,} | TP={stats_m['tp_pct']}% | SL={stats_m['sl_pct']}% | Exp={stats_m['exp_pct']}% | Amb={stats_m['ambiguous_count']}")

        dt = time.time() - t0
        print(f"  Completed in {dt:.2f}s")

    # Aggregate summaries across all 11 instruments
    print("\n" + "=" * 80)
    print("AGGREGATE LABEL DISTRIBUTION SUMMARY (Candidate Multiplier: 1.5)")
    print("=" * 80)

    total_eligible = sum(candidate_results[s]["eligible_samples"] for s in candidate_results)
    total_tp = sum(candidate_results[s]["tp_count"] for s in candidate_results)
    total_sl = sum(candidate_results[s]["sl_count"] for s in candidate_results)
    total_exp = sum(candidate_results[s]["exp_count"] for s in candidate_results)
    total_amb = sum(candidate_results[s]["ambiguous_count"] for s in candidate_results)
    total_exc = sum(candidate_results[s]["excluded_count"] for s in candidate_results)

    agg_tp_pct = round(total_tp / total_eligible * 100.0, 2)
    agg_sl_pct = round(total_sl / total_eligible * 100.0, 2)
    agg_exp_pct = round(total_exp / total_eligible * 100.0, 2)

    print(f"Total Eligible Samples: {total_eligible:,}")
    print(f"Aggregate TP:           {total_tp:,} ({agg_tp_pct}%)")
    print(f"Aggregate SL:           {total_sl:,} ({agg_sl_pct}%)")
    print(f"Aggregate Expiration:   {total_exp:,} ({agg_exp_pct}%)")
    print(f"Aggregate Ambiguous:    {total_amb:,}")
    print(f"Aggregate Excluded:     {total_exc:,}")

    # Save to JSON
    output_data = {
        "metadata": {
            "timeframe": "5m",
            "horizon_bars": 12,
            "horizon_minutes": 60,
            "volatility_lookback": 20,
            "candidate_multiplier": 1.5,
            "sensitivity_multipliers": MULTIPLIERS,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        },
        "aggregate_candidate": {
            "total_eligible": total_eligible,
            "total_tp": total_tp,
            "tp_pct": agg_tp_pct,
            "total_sl": total_sl,
            "sl_pct": agg_sl_pct,
            "total_exp": total_exp,
            "exp_pct": agg_exp_pct,
            "total_amb": total_amb,
            "total_exc": total_exc,
        },
        "per_symbol_candidate": candidate_results,
        "sensitivity": sensitivity_results,
    }

    out_json_path = BASE_DIR / "phase5_2_label_analysis.json"
    with open(out_json_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
    print(f"\nSaved analysis results to {out_json_path}")


if __name__ == "__main__":
    main()
