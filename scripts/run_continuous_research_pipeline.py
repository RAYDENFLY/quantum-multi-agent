"""Continuous Research Pipeline Demonstration & Benchmark Runner.

Demonstrates:
1. Strict dataset partitioning: TRAIN, VALIDATION, ROLLING_OOS with 288-bar embargo.
2. Sealed holdout isolation (all timestamps < 1,793,491,200,000 ms).
3. Priority-based asynchronous experiment queue.
4. Parallel execution across workers.
5. Reproducible intermediate feature caching.
6. Deduplication and redundant experiment skipping.
7. Automated rejection gate inspection and zero-survivorship-bias ledger recording.
8. Independent prospective OOS collection simulation.
"""

from datetime import datetime, timezone
from pathlib import Path
import time
import pandas as pd
import pyarrow.parquet as pq

from quantum.domain.research_contract import (
    ResearchExperimentContract,
    ExperimentCategory,
    ExecutionTimeframe,
    ASTER_DEX_RETAIL_CONFIG,
)
from quantum.research import (
    ContinuousExperimentConfig,
    ContinuousResearchOrchestrator,
    ContinuousResearchPartitioner,
    DatasetPartitionType,
    ExperimentPriority,
    IntermediateFeatureCache,
)

ROOT = Path(__file__).resolve().parent.parent
CANONICAL_DIR = ROOT / "data" / "historical" / "canonical" / "exchange=ASTER"
AUDIT_DIR = ROOT / "audit" / "strategy_research" / "continuous_research_orchestration"


def load_canonical_data(symbol: str, n_bars: int = 10_000) -> pd.DataFrame:
    """Loads historical 5m bars up to n_bars strictly prior to holdout cutoff."""
    s_dir = CANONICAL_DIR / f"symbol={symbol}" / "timeframe=5m"
    files = sorted(s_dir.glob("*.parquet"))
    dfs = []
    for f in files:
        tbl = pq.ParquetFile(str(f)).read(
            columns=["open_time_ms", "close_time_ms", "open", "high", "low", "close", "volume"]
        )
        dfs.append(tbl.to_pandas())
    df = pd.concat(dfs, ignore_index=True).sort_values("open_time_ms").reset_index(drop=True)
    return df.iloc[:n_bars].copy()


def main():
    print("=" * 80)
    print("QUANTUM CONTINUOUS RESEARCH MODE PIPELINE RUNNER")
    print("=" * 80)

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    partitioner = ContinuousResearchPartitioner(embargo_bars=288, train_ratio=0.50, val_ratio=0.25, rolling_oos_ratio=0.25)
    cache = IntermediateFeatureCache(disk_cache_dir=AUDIT_DIR / ".cache")
    orchestrator = ContinuousResearchOrchestrator(
        ledger_dir=AUDIT_DIR,
        max_workers=4,
        feature_cache=cache,
        partitioner=partitioner,
    )

    # 1. Load Data for Primary Research Assets
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    partitions_by_symbol = {}

    print(f"\n[1/5] Partitioning datasets with 24h embargo buffers...")
    for sym in symbols:
        df_raw = load_canonical_data(sym, n_bars=8_000)
        parts = partitioner.partition_pre_holdout_series(df_raw, symbol=sym, timeframe="5m")
        partitions_by_symbol[sym] = parts
        print(f"  • {sym}: TRAIN={len(parts[DatasetPartitionType.TRAIN].df)} bars, "
              f"VAL={len(parts[DatasetPartitionType.VALIDATION].df)} bars, "
              f"OOS={len(parts[DatasetPartitionType.ROLLING_OOS].df)} bars")

    # 2. Build Authoritative Contract
    contract = ResearchExperimentContract(
        experiment_id="EXP-CONT-DEMO",
        experiment_name="Continuous Alpha Discovery Run",
        experiment_category=ExperimentCategory.HIGH_FREQUENCY_INTRADAY,
        execution_timeframe=ExecutionTimeframe.TF_5M,
        maximum_holding_horizon_minutes=240,
        allow_overnight_holding=False,
        maximum_gross_exposure=1.0000,
        initial_equity_usd=100.0,
        mandatory_profitability_gate_daily_pct=3.0000,
        exchange_cost_config=ASTER_DEX_RETAIL_CONFIG,
    )

    # 3. Enqueue Parallel Hypotheses across TRAIN, VALIDATION, and ROLLING_OOS
    print("\n[2/5] Enqueuing multi-hypothesis experiments with priority scoring...")
    hypotheses = ["HYP-01", "HYP-02", "HYP-04", "HYP-05"]

    exp_counter = 1
    # Priority: TRAIN higher priority than VAL, VAL higher than OOS
    for sym in symbols:
        for hyp_id in hypotheses:
            for p_type, prio_gain in [
                (DatasetPartitionType.TRAIN, 0.9),
                (DatasetPartitionType.VALIDATION, 0.7),
                (DatasetPartitionType.ROLLING_OOS, 0.5),
            ]:
                cfg = ContinuousExperimentConfig(
                    experiment_id=f"EXP-C{exp_counter:03d}",
                    hypothesis_id=hyp_id,
                    partition_type=p_type,
                    symbol=sym,
                    contract=contract,
                    priority=ExperimentPriority(
                        expected_information_gain=prio_gain,
                        estimated_compute_cost=1.0,
                    ),
                )
                orchestrator.enqueue_experiment(cfg)
                exp_counter += 1

    print(f"  Enqueued {len(orchestrator._queue)} experiments.")

    # 4. Execute Parallel Batch 1
    print("\n[3/5] Executing parallel experiment batch (with feature caching)...")
    t0 = time.perf_counter()
    records_1 = orchestrator.run_queued_experiments(partitions_by_symbol)
    elapsed_1 = time.perf_counter() - t0
    print(f"  Batch 1 completed in {elapsed_1:.2f} seconds ({len(records_1)} experiments).")
    print(f"  Cache Stats: Hits={cache.hits}, Misses={cache.misses}, Saved ~{cache.compute_seconds_saved:.1f}s.")

    # 5. Enqueue Duplicate / Redundant Experiment to Test Deduplication
    print("\n[4/5] Enqueuing duplicate experiment to verify automatic redundancy detection...")
    dup_cfg = ContinuousExperimentConfig(
        experiment_id="EXP-DUP-001",
        hypothesis_id="HYP-01",
        partition_type=DatasetPartitionType.TRAIN,
        symbol="BTCUSDT",
        contract=contract,
        priority=ExperimentPriority(expected_information_gain=0.1, estimated_compute_cost=1.0),
    )
    orchestrator.enqueue_experiment(dup_cfg)
    records_2 = orchestrator.run_queued_experiments(partitions_by_symbol)
    assert len(records_2) == 1
    assert records_2[0].rejection_category == "REDUNDANT_CONFIGURATION"
    print(f"  Duplicate correctly caught and logged: {records_2[0].rejection_reasons}")

    # 6. Simulate Independent Prospective OOS Collector Tick
    print("\n[5/5] Testing independent unblocked prospective OOS collector...")
    tick_res = orchestrator.run_prospective_oos_collector_tick(
        new_candle_timestamp_ms=1_793_491_500_000,  # Just past holdout boundary
        symbol="BTCUSDT",
        price=71250.0,
    )
    print(f"  Collector Tick Status: {tick_res['status']} (Partition: {tick_res['partition']})")

    # Print Summary Telemetry
    print("\n" + "=" * 80)
    print("CONTINUOUS RESEARCH TELEMETRY SUMMARY")
    print("=" * 80)
    print(f"Total Dispatched Experiments : {orchestrator.total_dispatched}")
    print(f"Total Completed & Recorded  : {orchestrator.total_completed}")
    print(f"Accepted Experiments        : {orchestrator.total_accepted}")
    print(f"Rejected Experiments        : {orchestrator.total_rejected}")
    print(f"Redundant Skipped           : {orchestrator.total_redundant_skipped}")
    print(f"Feature Cache Hits          : {cache.hits} (saved ~{cache.compute_seconds_saved:.1f}s compute)")
    print(f"Experiment Ledger CSV       : {orchestrator.ledger_csv_path}")
    print(f"Experiment Ledger JSONL     : {orchestrator.ledger_jsonl_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
