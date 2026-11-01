"""QUANTUM Phase 5.1 Historical Backfill & Dataset Materialization Runner.

Downloads and materializes 11 target USDT perpetual instruments across 3 timeframes (1h, 15m, 5m)
from AsterDEX for the window 2023-11-01 00:00:00 UTC to 2026-11-01 00:00:00 UTC.
Year-partitioned Parquet storage, SQLite WAL metadata, zero future leakage.
"""

import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional
import pandas as pd
import psutil

from quantum.core.logging import get_logger
from quantum.domain.enums import Exchange, Timeframe
from quantum.exchanges.aster.adapter import AsterExchangeAdapter
from quantum.features.engine import FeatureEngine
from quantum.historical.downloader import HistoricalCandleDownloader
from quantum.historical.models import (
    CanonicalCandle,
    CollectionJobStatus,
    DataQualityReport,
    DatasetManifest,
    HistoricalCollectionJob,
    ValidationStatus,
)
from quantum.historical.service import HistoricalDataService
from quantum.historical.storage import ParquetStorageManager
from quantum.historical.validator import TIMEFRAME_INTERVAL_MS, DataQualityValidator
from quantum.storage.database import DatabaseManager
from quantum.storage.historical_repository import HistoricalRepository

logger = get_logger("backfill.phase5_1")

TARGET_SYMBOLS: List[str] = [
    "ADAUSDT",
    "XRPUSDT",
    "BTCUSDT",
    "BNBUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "AVAXUSDT",
    "LINKUSDT",
    "XMRUSDT",
    "DOGEUSDT",
    "LTCUSDT",
]

TARGET_TIMEFRAMES: List[Timeframe] = [
    Timeframe.H1,
    Timeframe.M15,
    Timeframe.M5,
]

WINDOW_START_MS: int = 1698796800000  # 2023-11-01 00:00:00 UTC
WINDOW_END_MS: int = 1793491200000    # 2026-11-01 00:00:00 UTC

HOLDOUT_START_MS: int = 1777593600000  # 2026-05-01 00:00:00 UTC
HOLDOUT_END_MS: int = 1793491199000    # 2026-10-31 23:59:59 UTC
VALIDATION_START_MS: int = 1761955200000  # 2025-11-01 00:00:00 UTC
VALIDATION_END_MS: int = 1777593599000    # 2026-04-30 23:59:59 UTC
DEV_START_MS: int = 1698796800000         # 2023-11-01 00:00:00 UTC
DEV_END_MS: int = 1761955199000           # 2025-10-31 23:59:59 UTC


def compute_file_sha256(path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def compute_dir_sha256(directory: Path) -> str:
    """Calculate combined SHA-256 checksum of all parquet files in a directory."""
    if not directory.exists():
        return ""
    h = hashlib.sha256()
    files = sorted(directory.glob("*.parquet"))
    for file_path in files:
        if file_path.name.startswith(".") or ".tmp." in file_path.name or file_path.name == "conflicts.parquet":
            continue
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
    return h.hexdigest()


async def run_backfill() -> None:
    """Execute complete Phase 5.1 historical backfill and feature materialization."""
    process = psutil.Process(os.getpid())
    base_dir = Path("data/historical").resolve()
    base_dir.mkdir(parents=True, exist_ok=True)
    db_path = base_dir / "historical.db"

    db_mgr = DatabaseManager(db_path)
    await db_mgr.initialize()
    conn = await db_mgr.connect()

    repo = HistoricalRepository(conn)
    storage = ParquetStorageManager(base_dir)
    validator = DataQualityValidator(feature_version="FEATURE_V1", dataset_version="DATASET_V1")
    downloader = HistoricalCandleDownloader(storage_manager=storage, repository=repo, validator=validator)
    feature_engine = FeatureEngine(schema_version="FEATURE_V1")
    adapter = AsterExchangeAdapter()

    logger.info("Discovering instruments on AsterDEX...")
    raw_instruments = await adapter.fetch_instruments()
    onboard_map: Dict[str, int] = {}
    for inst in raw_instruments:
        onboard_map[inst.symbol.upper()] = inst.onboard_timestamp_ms

    results: List[Dict[str, Any]] = []
    total_start_time = time.time()

    print("=" * 80)
    print("QUANTUM PHASE 5.1: HISTORICAL BACKFILL & DATASET MATERIALIZATION")
    print(f"Target Window: 2023-11-01 00:00:00 UTC to 2026-11-01 00:00:00 UTC")
    print(f"Target Instruments ({len(TARGET_SYMBOLS)}): {', '.join(TARGET_SYMBOLS)}")
    print(f"Target Timeframes ({len(TARGET_TIMEFRAMES)}): {[t.value for t in TARGET_TIMEFRAMES]}")
    print("=" * 80)

    workload_idx = 0
    total_workloads = len(TARGET_SYMBOLS) * len(TARGET_TIMEFRAMES)

    for symbol in TARGET_SYMBOLS:
        onboard_ms = onboard_map.get(symbol, 0)
        onboard_dt_str = datetime.fromtimestamp(onboard_ms / 1000, tz=timezone.utc).isoformat() if onboard_ms else "N/A"
        print(f"\n[INSTRUMENT] {symbol} (Exchange Onboard: {onboard_dt_str})")

        for timeframe in TARGET_TIMEFRAMES:
            workload_idx += 1
            workload_start = time.time()
            mem_before_mb = process.memory_info().rss / (1024 * 1024)

            interval_ms = TIMEFRAME_INTERVAL_MS.get(timeframe, 300_000)
            effective_start_ms = max(WINDOW_START_MS, onboard_ms) if onboard_ms > WINDOW_START_MS else WINDOW_START_MS

            job_id = f"JOB-ASTER-{symbol}-{timeframe.value}-PHASE51"
            existing_job = await repo.get_job(job_id)
            df_existing = storage.read_canonical(Exchange.ASTER, symbol, timeframe)
            already_done = (
                existing_job is not None
                and existing_job.status == CollectionJobStatus.COMPLETED
                and not df_existing.empty
                and df_existing["open_time_ms"].min() <= effective_start_ms + interval_ms
            )

            if already_done:
                print(f"  [{workload_idx}/{total_workloads}] Reusing verified {symbol} {timeframe.value} ...", end="", flush=True)
                dl_start = time.time()
                valid_candles = []
                for _, row in df_existing.iterrows():
                    valid_candles.append(
                        CanonicalCandle(
                            exchange=Exchange.ASTER,
                            symbol=symbol,
                            market_type="PERPETUAL",
                            timeframe=timeframe,
                            open_time_ms=int(row["open_time_ms"]),
                            close_time_ms=int(row["close_time_ms"]),
                            open=float(row["open"]),
                            high=float(row["high"]),
                            low=float(row["low"]),
                            close=float(row["close"]),
                            volume=float(row["volume"]),
                            quote_volume=float(row["quote_volume"]) if pd.notna(row["quote_volume"]) else None,
                            trade_count=int(row["trade_count"]) if pd.notna(row["trade_count"]) else None,
                            taker_buy_volume=float(row["taker_buy_volume"]) if pd.notna(row["taker_buy_volume"]) else None,
                            taker_buy_quote_volume=float(row["taker_buy_quote_volume"]) if pd.notna(row["taker_buy_quote_volume"]) else None,
                            ingestion_time_ms=int(row["ingestion_time_ms"]),
                            source_run_id=str(row["source_run_id"]),
                        )
                    )
                _, quality_report = validator.validate_dataset(
                    candles=valid_candles,
                    exchange=Exchange.ASTER,
                    symbol=symbol,
                    timeframe=timeframe,
                    requested_start_ms=effective_start_ms,
                    requested_end_ms=WINDOW_END_MS,
                    run_id=job_id,
                    listing_start_time_ms=onboard_ms,
                )
                dl_duration = max(0.001, time.time() - dl_start)
                dl_throughput = len(valid_candles) / dl_duration
                print(f" REUSED: {len(valid_candles):,} candles")
            else:
                job = HistoricalCollectionJob(
                    job_id=job_id,
                    exchange=Exchange.ASTER,
                    symbol=symbol,
                    timeframe=timeframe,
                    requested_start_ms=effective_start_ms,
                    requested_end_ms=WINDOW_END_MS,
                    status=CollectionJobStatus.PENDING,
                )
                await repo.save_job(job)

                print(f"  [{workload_idx}/{total_workloads}] Downloading {symbol} {timeframe.value} ...", end="", flush=True)

                dl_start = time.time()
                valid_candles, quality_report = await downloader.download(
                    job=job,
                    adapter=adapter,
                    page_limit=1500,
                    max_retries=4,
                    backoff_base_s=0.5,
                    use_year_partitioning=True,
                    listing_start_time_ms=onboard_ms,
                )
                dl_duration = max(0.001, time.time() - dl_start)
                dl_throughput = len(valid_candles) / dl_duration

                print(f" DONE: {len(valid_candles):,} candles in {dl_duration:.2f}s ({dl_throughput:.1f} c/s)")

            # Compute features
            print(f"       Materializing features ...", end="", flush=True)
            feat_start = time.time()

            df_canonical = storage.read_canonical(Exchange.ASTER, symbol, timeframe)
            df_features = feature_engine.compute_features(df_canonical)
            storage.write_features_partitioned_by_year(
                df_features, Exchange.ASTER, symbol, timeframe, layer="features"
            )

            # Materialize stationary research-ready features
            df_research = feature_engine.filter_research_features(df_features, warmup_bars=200)
            storage.write_features_partitioned_by_year(
                df_research, Exchange.ASTER, symbol, timeframe, layer="features_research"
            )

            feat_duration = max(0.001, time.time() - feat_start)
            feat_throughput = len(df_canonical) / feat_duration
            print(f" DONE: {len(df_research):,} research rows in {feat_duration:.2f}s ({feat_throughput:.1f} r/s)")

            mem_after_mb = process.memory_info().rss / (1024 * 1024)

            # Measure disk footprint
            canon_dir = storage.get_partition_dir("canonical", Exchange.ASTER, symbol, timeframe)
            feat_dir = storage.get_partition_dir("features", Exchange.ASTER, symbol, timeframe)
            res_dir = storage.get_partition_dir("features_research", Exchange.ASTER, symbol, timeframe)
            raw_dir = storage.get_partition_dir("raw", Exchange.ASTER, symbol, timeframe)

            canon_bytes = sum(f.stat().st_size for f in canon_dir.glob("*.parquet"))
            feat_bytes = sum(f.stat().st_size for f in feat_dir.glob("*.parquet"))
            res_bytes = sum(f.stat().st_size for f in res_dir.glob("*.parquet"))
            raw_bytes = sum(f.stat().st_size for f in raw_dir.glob("*.parquet"))

            canon_hash = compute_dir_sha256(canon_dir)
            feat_hash = compute_dir_sha256(feat_dir)
            res_hash = compute_dir_sha256(res_dir)

            first_ts = valid_candles[0].open_time_ms if valid_candles else 0
            last_ts = valid_candles[-1].open_time_ms if valid_candles else 0

            # Holdout partition count
            holdout_rows = int(df_research[(df_research["open_time_ms"] >= HOLDOUT_START_MS) & (df_research["open_time_ms"] <= HOLDOUT_END_MS)].shape[0])
            val_rows = int(df_research[(df_research["open_time_ms"] >= VALIDATION_START_MS) & (df_research["open_time_ms"] <= VALIDATION_END_MS)].shape[0])
            dev_rows = int(df_research[(df_research["open_time_ms"] >= DEV_START_MS) & (df_research["open_time_ms"] <= DEV_END_MS)].shape[0])

            record = {
                "workload_id": workload_idx,
                "exchange": "ASTER",
                "symbol": symbol,
                "timeframe": timeframe.value,
                "onboard_timestamp_ms": onboard_ms,
                "onboard_dt_utc": onboard_dt_str,
                "requested_start_ms": effective_start_ms,
                "requested_end_ms": WINDOW_END_MS,
                "first_timestamp_ms": first_ts,
                "first_dt_utc": datetime.fromtimestamp(first_ts / 1000, tz=timezone.utc).isoformat() if first_ts else "N/A",
                "last_timestamp_ms": last_ts,
                "last_dt_utc": datetime.fromtimestamp(last_ts / 1000, tz=timezone.utc).isoformat() if last_ts else "N/A",
                "expected_candle_count": quality_report.expected_count,
                "actual_candle_count": quality_report.observed_count,
                "missing_candle_count": quality_report.missing_count,
                "coverage_pct": round(quality_report.coverage_pct, 4),
                "duplicate_candle_count": quality_report.duplicate_count,
                "conflicting_candle_count": quality_report.conflicting_duplicate_count,
                "invalid_ohlc_count": quality_report.invalid_ohlc_count,
                "incomplete_candle_count": quality_report.incomplete_candle_count,
                "feature_total_rows": len(df_features),
                "feature_research_rows": len(df_research),
                "warmup_rows_removed": len(df_features) - len(df_research),
                "remaining_nan_count": int(df_research.isna().sum().sum()),
                "infinite_value_count": int((df_research.select_dtypes(include="number") == float("inf")).sum().sum()) + int((df_research.select_dtypes(include="number") == float("-inf")).sum().sum()),
                "validation_status": quality_report.validation_status.value,
                "canonical_sha256": canon_hash,
                "features_sha256": feat_hash,
                "features_research_sha256": res_hash,
                "canonical_storage_path": str(canon_dir.relative_to(Path.cwd())),
                "features_storage_path": str(feat_dir.relative_to(Path.cwd())),
                "features_research_storage_path": str(res_dir.relative_to(Path.cwd())),
                "canonical_bytes": canon_bytes,
                "features_bytes": feat_bytes,
                "features_research_bytes": res_bytes,
                "raw_bytes": raw_bytes,
                "dev_rows": dev_rows,
                "val_rows": val_rows,
                "holdout_rows": holdout_rows,
                "dl_duration_s": round(dl_duration, 2),
                "dl_throughput_cps": round(dl_throughput, 1),
                "feat_duration_s": round(feat_duration, 2),
                "feat_throughput_rps": round(feat_throughput, 1),
                "workload_duration_s": round(time.time() - workload_start, 2),
                "rss_mem_before_mb": round(mem_before_mb, 1),
                "rss_mem_after_mb": round(mem_after_mb, 1),
            }
            results.append(record)

    total_duration_s = time.time() - total_start_time
    await adapter.rest.close()

    summary_file = base_dir / "phase5_1_backfill_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "total_workloads": len(results),
                "total_duration_s": round(total_duration_s, 2),
                "total_canonical_candles": sum(r["actual_candle_count"] for r in results),
                "total_canonical_bytes": sum(r["canonical_bytes"] for r in results),
                "total_features_bytes": sum(r["features_bytes"] for r in results),
                "total_features_research_bytes": sum(r["features_research_bytes"] for r in results),
                "workloads": results,
            },
            f,
            indent=2,
        )

    print("\n" + "=" * 80)
    print(f"PHASE 5.1 BACKFILL COMPLETED SUCCESSFULLY IN {total_duration_s:.1f}s ({total_duration_s/60:.1f} min)")
    print(f"Summary written to {summary_file}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(run_backfill())
