"""Phase 5.2.1 Audit Script: Exact Partition-Level Scope and Label Accounting.

Audits actual 5m canonical datasets and label generation outputs across:
1. Pre-Development Warm-Up (< 2023-11-01 00:00:00 UTC)
2. Development (2023-11-01 00:00:00.000 to 2025-10-31 23:59:59.999 UTC)
3. Validation (2025-11-01 00:00:00.000 to 2026-04-30 23:59:59.999 UTC)
4. Final Holdout (2026-05-01 00:00:00.000 to 2026-10-31 23:59:59.999 UTC)
5. Out of bounds (> 2026-10-31 23:59:59.999 UTC)

Produces exact row counts, label distribution, ambiguous touches, and exclusions.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd

from quantum.domain.enums import Exchange, Timeframe
from quantum.features.labeling import BarrierOutcome, TripleBarrierLabelGenerator
from quantum.features.temporal_split import (
    DEVELOPMENT_END_MS,
    DEVELOPMENT_START_MS,
    FINAL_HOLDOUT_END_MS,
    FINAL_HOLDOUT_START_MS,
    VALIDATION_END_MS,
    VALIDATION_START_MS,
)
from quantum.historical.storage import ParquetStorageManager

BASE_DIR = Path("data/historical")
EXCHANGE = Exchange.ASTER
SYMBOLS = [
    "ADAUSDT", "XRPUSDT", "BTCUSDT", "BNBUSDT", "ETHUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "XMRUSDT", "DOGEUSDT", "LTCUSDT"
]
TIMEFRAME = Timeframe.M5

PARTITION_RANGES = {
    "PRE_DEVELOPMENT": (-float("inf"), DEVELOPMENT_START_MS - 1),
    "DEVELOPMENT": (DEVELOPMENT_START_MS, DEVELOPMENT_END_MS),
    "VALIDATION": (VALIDATION_START_MS, VALIDATION_END_MS),
    "FINAL_HOLDOUT": (FINAL_HOLDOUT_START_MS, FINAL_HOLDOUT_END_MS),
    "POST_HOLDOUT": (FINAL_HOLDOUT_END_MS + 1, float("inf")),
}


def audit_symbol(symbol: str, storage: ParquetStorageManager) -> dict:
    df_can = storage.read_canonical(EXCHANGE, symbol, TIMEFRAME)
    if df_can.empty:
        return {}

    # Run Candidate Label Generator (Multiplier 1.5) exactly as Phase 5.2 ran
    gen = TripleBarrierLabelGenerator(
        horizon_bars=12,
        volatility_lookback=20,
        barrier_multiplier=1.5,
        timeframe_ms=300_000,
    )
    labeled = gen.generate_labels(df_can, enforce_partition_boundaries=True)

    ts = labeled["open_time_ms"].to_numpy()
    labels = labeled["label"].to_numpy()
    reasons = labeled["exclusion_reason"].to_numpy()

    part_audit = {}

    for part_name, (start_ms, end_ms) in PARTITION_RANGES.items():
        mask = (ts >= start_ms) & (ts <= end_ms)
        p_count = int(mask.sum())
        if p_count == 0:
            part_audit[part_name] = {
                "input_candles": 0,
                "eligible_samples": 0,
                "tp_count": 0,
                "tp_pct": 0.0,
                "sl_count": 0,
                "sl_pct": 0.0,
                "exp_count": 0,
                "exp_pct": 0.0,
                "ambiguous_count": 0,
                "ambiguous_pct": 0.0,
                "warmup_exclusions": 0,
                "boundary_exclusions": 0,
                "gap_exclusions": 0,
                "horizon_exclusions": 0,
                "total_exclusions": 0,
            }
            continue

        p_labels = labels[mask]
        p_reasons = reasons[mask]

        tp_cnt = int((p_labels == BarrierOutcome.TP.value).sum())
        sl_cnt = int((p_labels == BarrierOutcome.SL.value).sum())
        exp_cnt = int((p_labels == BarrierOutcome.TIME_EXPIRATION.value).sum())
        amb_cnt = int((p_labels == BarrierOutcome.AMBIGUOUS.value).sum())

        eligible_cnt = tp_cnt + sl_cnt + exp_cnt

        tp_pct = round(tp_cnt / eligible_cnt * 100.0, 2) if eligible_cnt > 0 else 0.0
        sl_pct = round(sl_cnt / eligible_cnt * 100.0, 2) if eligible_cnt > 0 else 0.0
        exp_pct = round(exp_cnt / eligible_cnt * 100.0, 2) if eligible_cnt > 0 else 0.0
        amb_pct = round(amb_cnt / p_count * 100.0, 4) if p_count > 0 else 0.0

        # Detailed exclusions
        warmup_ex = int((p_reasons == "WARMUP_INSUFFICIENT_LOOKBACK").sum())
        bound_ex = int((p_reasons == "PARTITION_BOUNDARY_OVERFLOW").sum())
        gap_ex = int((p_reasons == "MISSING_FUTURE_CANDLE_GAP").sum())
        horiz_ex = int((p_reasons == "INSUFFICIENT_FUTURE_HORIZON").sum())
        tot_ex = warmup_ex + bound_ex + gap_ex + horiz_ex

        part_audit[part_name] = {
            "input_candles": p_count,
            "eligible_samples": eligible_cnt,
            "tp_count": tp_cnt,
            "tp_pct": tp_pct,
            "sl_count": sl_cnt,
            "sl_pct": sl_pct,
            "exp_count": exp_cnt,
            "exp_pct": exp_pct,
            "ambiguous_count": amb_cnt,
            "ambiguous_pct": amb_pct,
            "warmup_exclusions": warmup_ex,
            "boundary_exclusions": bound_ex,
            "gap_exclusions": gap_ex,
            "horizon_exclusions": horiz_ex,
            "total_exclusions": tot_ex,
        }

    return part_audit


def main():
    print("=" * 80)
    print("QUANTUM PHASE 5.2.1: EXACT PARTITION-LEVEL SCOPE & LABEL AUDIT")
    print("=" * 80)

    storage = ParquetStorageManager(BASE_DIR)
    results = {}

    for sym in SYMBOLS:
        print(f"Auditing {sym} 5m ...", end="", flush=True)
        results[sym] = audit_symbol(sym, storage)
        print(" DONE")

    # Aggregate by partition across all 11 instruments
    agg_by_part = {}
    for part_name in PARTITION_RANGES:
        agg_by_part[part_name] = {
            "input_candles": sum(results[s][part_name]["input_candles"] for s in SYMBOLS),
            "eligible_samples": sum(results[s][part_name]["eligible_samples"] for s in SYMBOLS),
            "tp_count": sum(results[s][part_name]["tp_count"] for s in SYMBOLS),
            "sl_count": sum(results[s][part_name]["sl_count"] for s in SYMBOLS),
            "exp_count": sum(results[s][part_name]["exp_count"] for s in SYMBOLS),
            "ambiguous_count": sum(results[s][part_name]["ambiguous_count"] for s in SYMBOLS),
            "warmup_exclusions": sum(results[s][part_name]["warmup_exclusions"] for s in SYMBOLS),
            "boundary_exclusions": sum(results[s][part_name]["boundary_exclusions"] for s in SYMBOLS),
            "gap_exclusions": sum(results[s][part_name]["gap_exclusions"] for s in SYMBOLS),
            "horizon_exclusions": sum(results[s][part_name]["horizon_exclusions"] for s in SYMBOLS),
            "total_exclusions": sum(results[s][part_name]["total_exclusions"] for s in SYMBOLS),
        }
        el = agg_by_part[part_name]["eligible_samples"]
        inp = agg_by_part[part_name]["input_candles"]
        agg_by_part[part_name]["tp_pct"] = round(agg_by_part[part_name]["tp_count"] / el * 100.0, 2) if el > 0 else 0.0
        agg_by_part[part_name]["sl_pct"] = round(agg_by_part[part_name]["sl_count"] / el * 100.0, 2) if el > 0 else 0.0
        agg_by_part[part_name]["exp_pct"] = round(agg_by_part[part_name]["exp_count"] / el * 100.0, 2) if el > 0 else 0.0
        agg_by_part[part_name]["ambiguous_pct"] = round(agg_by_part[part_name]["ambiguous_count"] / inp * 100.0, 4) if inp > 0 else 0.0

    print("\n" + "=" * 80)
    print("AGGREGATE PARTITION-LEVEL SCOPE ACCOUNTING")
    print("=" * 80)
    for p_name, p_data in agg_by_part.items():
        print(f"[{p_name}]")
        print(f"  Input Candles:       {p_data['input_candles']:,}")
        print(f"  Eligible Samples:    {p_data['eligible_samples']:,} (TP={p_data['tp_pct']}%, SL={p_data['sl_pct']}%, Exp={p_data['exp_pct']}%)")
        print(f"  TP Count:            {p_data['tp_count']:,}")
        print(f"  SL Count:            {p_data['sl_count']:,}")
        print(f"  Exp Count:           {p_data['exp_count']:,}")
        print(f"  Ambiguous Count:     {p_data['ambiguous_count']:,} ({p_data['ambiguous_pct']}%)")
        print(f"  Exclusions:          Total={p_data['total_exclusions']:,} (Warmup={p_data['warmup_exclusions']}, Boundary={p_data['boundary_exclusions']}, Gap={p_data['gap_exclusions']}, Horizon={p_data['horizon_exclusions']})")

    total_all_input = sum(agg_by_part[p]["input_candles"] for p in agg_by_part)
    total_all_eligible = sum(agg_by_part[p]["eligible_samples"] for p in agg_by_part)
    total_all_amb = sum(agg_by_part[p]["ambiguous_count"] for p in agg_by_part)
    total_all_exc = sum(agg_by_part[p]["total_exclusions"] for p in agg_by_part)

    print("\n" + "=" * 80)
    print("GLOBAL TOTALS ACROSS ALL PARTITIONS:")
    print(f"  Total Input Candles:     {total_all_input:,}")
    print(f"  Total Eligible Samples:  {total_all_eligible:,}")
    print(f"  Total Ambiguous Touches: {total_all_amb:,}")
    print(f"  Total Pipeline Excl:     {total_all_exc:,}")
    print(f"  Reconciliation Check:    {total_all_eligible} + {total_all_amb} + {total_all_exc} = {total_all_eligible + total_all_amb + total_all_exc} (Expected: {total_all_input})")
    print("=" * 80)

    # Save exact audit JSON
    audit_output = {
        "aggregate_by_partition": agg_by_part,
        "per_symbol": results,
    }
    out_file = BASE_DIR / "phase5_2_1_holdout_audit.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(audit_output, f, indent=2)
    print(f"Saved complete audit output to {out_file}")


if __name__ == "__main__":
    main()
