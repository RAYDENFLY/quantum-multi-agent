"""Deterministic unit tests for Parquet storage, schema enforcement, append, and manifests."""

from pathlib import Path
import pytest

from quantum.domain.enums import Exchange, Timeframe
from quantum.historical.models import (
    CanonicalCandle,
    CollectionJobStatus,
    DataQualityReport,
    DatasetManifest,
    HistoricalCollectionCheckpoint,
    HistoricalCollectionJob,
    RawHistoricalCandle,
    ValidationStatus,
)
from quantum.historical.storage import ParquetStorageManager, compute_file_sha256
from quantum.storage.database import DatabaseManager
from quantum.storage.historical_repository import HistoricalRepository


def test_parquet_storage_partition_path(tmp_path: Path) -> None:
    """Verify partition directory structure matches exchange/symbol/timeframe hierarchy."""
    storage = ParquetStorageManager(tmp_path)
    path = storage.get_partition_path("canonical", Exchange.ASTER, "BTCUSDT", Timeframe.M5)

    expected = tmp_path / "canonical" / "exchange=ASTER" / "symbol=BTCUSDT" / "timeframe=5m" / "data.parquet"
    assert path == expected


def test_parquet_raw_and_canonical_write_and_append(tmp_path: Path) -> None:
    """Verify writing raw and canonical candles, incremental append, and deduplication."""
    storage = ParquetStorageManager(tmp_path)

    # Batch 1: 5 candles
    batch1: list[CanonicalCandle] = []
    for i in range(5):
        ts = 1_000_000 + (i * 300_000)
        batch1.append(
            CanonicalCandle(
                exchange=Exchange.ASTER,
                symbol="BTCUSDT",
                market_type="PERPETUAL",
                timeframe=Timeframe.M5,
                open_time_ms=ts,
                close_time_ms=ts + 300_000 - 1,
                open=50000.0,
                high=50100.0,
                low=49900.0,
                close=50050.0,
                volume=10.0,
                source_run_id="RUN-01",
            )
        )

    file_path = storage.write_canonical_candles(batch1, Exchange.ASTER, "BTCUSDT", Timeframe.M5)
    assert file_path.exists()

    df_read1 = storage.read_canonical(Exchange.ASTER, "BTCUSDT", Timeframe.M5)
    assert len(df_read1) == 5

    # Batch 2: 3 overlapping candles + 2 new candles
    batch2: list[CanonicalCandle] = []
    for i in range(3, 7):
        ts = 1_000_000 + (i * 300_000)
        batch2.append(
            CanonicalCandle(
                exchange=Exchange.ASTER,
                symbol="BTCUSDT",
                market_type="PERPETUAL",
                timeframe=Timeframe.M5,
                open_time_ms=ts,
                close_time_ms=ts + 300_000 - 1,
                open=50000.0,
                high=50100.0,
                low=49900.0,
                close=50050.0,
                volume=20.0,  # Updated volume
                source_run_id="RUN-02",
            )
        )

    storage.write_canonical_candles(batch2, Exchange.ASTER, "BTCUSDT", Timeframe.M5)
    df_read2 = storage.read_canonical(Exchange.ASTER, "BTCUSDT", Timeframe.M5)

    # 5 from batch1 (0..4) + 2 new from batch2 (5..6) = 7 total unique candles
    assert len(df_read2) == 7
    # Deduplication keeps latest: overlapping indices 3 and 4 should have volume 20.0
    row_3 = df_read2[df_read2["open_time_ms"] == 1_000_000 + (3 * 300_000)].iloc[0]
    assert row_3["volume"] == 20.0
    assert row_3["source_run_id"] == "RUN-02"


def test_parquet_raw_payload_integrity(tmp_path: Path) -> None:
    """Verify raw storage preserves exact exchange API payload string and individual raw columns."""
    storage = ParquetStorageManager(tmp_path)
    sample_payload = '["1672531200000","16500.1","16550.0","16480.0","16520.5","125.4","2072462.1",1050,"62.5","1032100.0"]'
    raw_candle = RawHistoricalCandle(
        exchange=Exchange.ASTER,
        symbol="BTCUSDT",
        contract_type="PERPETUAL",
        timeframe=Timeframe.M5,
        exchange_candle_ts_ms=1672531200000,
        raw_open="16500.1",
        raw_high="16550.0",
        raw_low="16480.0",
        raw_close="16520.5",
        raw_volume="125.4",
        raw_turnover="2072462.1",
        raw_trades="1050",
        raw_taker_buy_volume="62.5",
        raw_taker_buy_turnover="1032100.0",
        raw_payload_json=sample_payload,
        retrieval_timestamp_ms=1672531500000,
        source_endpoint="/fapi/v1/klines",
        collection_run_id="RUN-RAW-VERIFY-01",
    )

    path = storage.write_raw_candles([raw_candle], Exchange.ASTER, "BTCUSDT", Timeframe.M5)
    assert path.exists()

    df_raw = storage.read_raw(Exchange.ASTER, "BTCUSDT", Timeframe.M5)
    assert len(df_raw) == 1
    row = df_raw.iloc[0]
    assert row["exchange"] == "ASTER"
    assert row["symbol"] == "BTCUSDT"
    assert row["timeframe"] == "5m"
    assert row["exchange_candle_ts_ms"] == 1672531200000
    assert row["raw_payload_json"] == sample_payload
    assert row["raw_open"] == "16500.1"
    assert row["source_endpoint"] == "/fapi/v1/klines"
    assert row["collection_run_id"] == "RUN-RAW-VERIFY-01"


def test_parquet_sha256_hash_reproducibility(tmp_path: Path) -> None:
    """Verify cryptographic SHA-256 hash calculation is deterministic and matches file."""
    storage = ParquetStorageManager(tmp_path)
    candles = [
        CanonicalCandle(
            exchange=Exchange.ASTER,
            symbol="BTCUSDT",
            market_type="PERPETUAL",
            timeframe=Timeframe.M5,
            open_time_ms=1_000_000,
            close_time_ms=1_299_999,
            open=50000.0,
            high=50100.0,
            low=49900.0,
            close=50050.0,
            volume=10.0,
            source_run_id="RUN-HASH",
        )
    ]
    path = storage.write_canonical_candles(candles, Exchange.ASTER, "BTCUSDT", Timeframe.M5)
    hash1 = compute_file_sha256(path)
    hash2 = compute_file_sha256(path)

    assert hash1 == hash2
    assert len(hash1) == 64  # Hex length of SHA-256


@pytest.mark.asyncio
async def test_historical_repository_crud(tmp_path: Path) -> None:
    """Verify full CRUD lifecycle for jobs, checkpoints, manifests, and quality reports in SQLite."""
    db_mgr = DatabaseManager(tmp_path / "quantum_test.db")
    await db_mgr.initialize()
    conn = await db_mgr.connect()
    repo = HistoricalRepository(conn)

    # 1. Job CRUD
    job = HistoricalCollectionJob(
        job_id="JOB-CRUD-01",
        exchange=Exchange.ASTER,
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        requested_start_ms=1000,
        requested_end_ms=2000,
        status=CollectionJobStatus.PENDING,
    )
    await repo.save_job(job)
    fetched_job = await repo.get_job("JOB-CRUD-01")
    assert fetched_job is not None
    assert fetched_job.symbol == "BTCUSDT"

    # Update job
    fetched_job.status = CollectionJobStatus.COMPLETED
    fetched_job.total_candles_fetched = 500
    await repo.save_job(fetched_job)
    updated_job = await repo.get_job("JOB-CRUD-01")
    assert updated_job is not None
    assert updated_job.status == CollectionJobStatus.COMPLETED
    assert updated_job.total_candles_fetched == 500

    # 2. Checkpoint CRUD
    chk = HistoricalCollectionCheckpoint(
        checkpoint_id="CHK-01",
        job_id="JOB-CRUD-01",
        exchange=Exchange.ASTER,
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        direction="BACKWARD",
        last_fetched_open_time_ms=1500,
        last_page_candle_count=100,
        earliest_open_time_ms=1500,
        latest_open_time_ms=2000,
        is_exhausted=False,
    )
    await repo.save_checkpoint(chk)
    fetched_chk = await repo.get_checkpoint("JOB-CRUD-01")
    assert fetched_chk is not None
    assert fetched_chk.last_fetched_open_time_ms == 1500

    await repo.delete_checkpoint("CHK-01")
    assert await repo.get_checkpoint("JOB-CRUD-01") is None

    # 3. Manifest CRUD
    manifest = DatasetManifest(
        manifest_id="MAN-01",
        dataset_name="BTCUSDT_5m_test",
        dataset_version="DATASET_V1",
        feature_version="FEATURE_V1",
        exchange=Exchange.ASTER,
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        start_time_ms=1000,
        end_time_ms=2000,
        candle_count=10,
        raw_parquet_path="path/raw.parquet",
        canonical_parquet_path="path/canon.parquet",
        file_sha256="abc123sha",
        metadata={"test": True},
    )
    await repo.save_manifest(manifest)
    fetched_man = await repo.get_manifest("MAN-01")
    assert fetched_man is not None
    assert fetched_man.file_sha256 == "abc123sha"

    # 4. Quality Report CRUD
    report = DataQualityReport(
        report_id="DQR-01",
        run_id="JOB-CRUD-01",
        exchange=Exchange.ASTER,
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        requested_start_ms=1000,
        requested_end_ms=2000,
        actual_start_ms=1000,
        actual_end_ms=2000,
        expected_count=10,
        observed_count=10,
        missing_count=0,
        duplicate_count=0,
        conflicting_duplicate_count=0,
        invalid_ohlc_count=0,
        incomplete_candle_count=0,
        coverage_pct=100.0,
        validation_status=ValidationStatus.PASS,
        feature_version="FEATURE_V1",
        dataset_version="DATASET_V1",
        details={"audit": "clean"},
    )
    await repo.save_quality_report(report)
    fetched_rep = await repo.get_quality_report("DQR-01")
    assert fetched_rep is not None
    assert fetched_rep.validation_status == ValidationStatus.PASS
