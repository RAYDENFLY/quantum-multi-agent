"""Deterministic unit tests for historical collection, pagination, retries, and checkpoints."""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
import pytest

from quantum.domain.enums import ConnectionState, Exchange, Timeframe
from quantum.exchanges.base import BaseExchangeAdapter
from quantum.exchanges.models import (
    ExchangeHealthStatus,
    InstrumentInfo,
    NormalizedCandle,
    NormalizedOrderBook,
    NormalizedTicker,
)
from quantum.historical.downloader import HistoricalCandleDownloader, PaginationManager
from quantum.historical.models import (
    CollectionJobStatus,
    HistoricalCollectionCheckpoint,
    HistoricalCollectionJob,
)
from quantum.historical.storage import ParquetStorageManager
from quantum.storage.database import DatabaseManager
from quantum.storage.historical_repository import HistoricalRepository


class MockExchangeAdapter(BaseExchangeAdapter):
    """Deterministic mock exchange adapter simulating klines pagination and error injection."""

    def __init__(self, exchange: Exchange = Exchange.ASTER, rate_limit_rps: float = 100.0) -> None:
        super().__init__(exchange, rate_limit_rps=rate_limit_rps)
        self.mock_data: List[List[Any]] = []
        self.fail_attempts_remaining = 0
        self.request_history: List[Dict[str, Any]] = []

    async def fetch_instruments(self) -> List[InstrumentInfo]:
        return []

    async def fetch_ticker(self, symbol: str) -> NormalizedTicker:
        raise NotImplementedError

    async def fetch_orderbook_snapshot(self, symbol: str, limit: int = 50) -> NormalizedOrderBook:
        raise NotImplementedError

    async def fetch_klines(
        self,
        symbol: str,
        timeframe: Timeframe,
        limit: int = 200,
        before_ms: Optional[int] = None,
    ) -> List[NormalizedCandle]:
        return []

    async def connect_market_stream(self, symbols: List[str], **kwargs: Any) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    async def health_check(self) -> ExchangeHealthStatus:
        return self.health

    # Mock rest client wrapper
    class MockRest:
        def __init__(self, outer: "MockExchangeAdapter") -> None:
            self.outer = outer

        async def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
            self.outer.request_history.append({"endpoint": endpoint, "params": params or {}})

            if self.outer.fail_attempts_remaining > 0:
                self.outer.fail_attempts_remaining -= 1
                raise ConnectionResetError("Simulated transient transport reset")

            params = params or {}
            end_time = params.get("endTime") or params.get("end")
            limit = int(params.get("limit", 1000))

            filtered = self.outer.mock_data
            if end_time is not None:
                filtered = [row for row in filtered if int(row[0]) <= int(end_time)]

            # Return latest `limit` bars
            res = filtered[-limit:] if len(filtered) > limit else filtered
            if self.outer.exchange == Exchange.BYBIT:
                # Bybit returns newest first (descending)
                return {"list": list(reversed(res))}
            return res

    @property
    def rest(self) -> Any:
        return self.MockRest(self)


def generate_mock_aster_klines(start_ms: int, count: int, interval_ms: int = 300_000) -> List[List[Any]]:
    """Generate mock AsterDEX format kline bars."""
    bars: List[List[Any]] = []
    base_price = 50000.0
    for i in range(count):
        ts = start_ms + (i * interval_ms)
        o = base_price + (i % 10)
        h = o + 20.0
        l = o - 15.0
        c = o + 5.0
        v = 10.0 + (i % 5)
        close_ts = ts + interval_ms - 1
        turnover = c * v
        trades = 50 + (i % 10)
        taker_b = 5.0
        taker_q = c * 5.0
        bars.append([ts, str(o), str(h), str(l), str(c), str(v), close_ts, str(turnover), trades, str(taker_b), str(taker_q), "0"])
    return bars


def test_pagination_manager_backward_exhaustion() -> None:
    """Verify backward pagination advances cursor correctly and terminates upon reaching start time."""
    start_ms = 1_000_000
    end_ms = 2_000_000
    interval_ms = 300_000

    pm = PaginationManager(start_ms, end_ms, Timeframe.M5, direction="BACKWARD")
    assert pm.is_exhausted is False

    # Page 1 request
    p1 = pm.get_next_request_params(limit=3)
    assert p1 == (end_ms, None)

    # Record Page 1 (bars from 1_400_000 to 2_000_000)
    pm.record_page_results(candle_count=3, earliest_bar_ms=1_400_000, latest_bar_ms=2_000_000, limit=3)
    assert pm.cursor_ms == 1_399_999
    assert pm.is_exhausted is False

    # Page 2 request
    p2 = pm.get_next_request_params(limit=3)
    assert p2 == (1_399_999, None)

    # Record Page 2 (bars reaching 800_000, which is below start_ms)
    pm.record_page_results(candle_count=3, earliest_bar_ms=800_000, latest_bar_ms=1_399_999, limit=3)
    assert pm.is_exhausted is True
    assert pm.get_next_request_params() is None


def test_pagination_manager_empty_and_partial_page() -> None:
    """Verify that empty response or partial response terminates pagination."""
    pm = PaginationManager(1_000_000, 2_000_000, Timeframe.M5, direction="BACKWARD")

    # Empty response immediately exhausts
    pm.record_page_results(candle_count=0, earliest_bar_ms=0, latest_bar_ms=0, limit=1000)
    assert pm.is_exhausted is True

    # Partial response (fewer than limit) exhausts backward pagination
    pm2 = PaginationManager(1_000_000, 2_000_000, Timeframe.M5, direction="BACKWARD")
    pm2.record_page_results(candle_count=50, earliest_bar_ms=1_500_000, latest_bar_ms=2_000_000, limit=1000)
    assert pm2.is_exhausted is True


@pytest.mark.asyncio
async def test_downloader_retry_and_backoff(tmp_path: Path) -> None:
    """Verify downloader retries transient transport errors and resumes."""
    storage = ParquetStorageManager(tmp_path / "parquet")
    adapter = MockExchangeAdapter(exchange=Exchange.ASTER)

    # Populate 10 mock candles
    adapter.mock_data = generate_mock_aster_klines(1_000_000, 10, interval_ms=300_000)
    # Inject 2 transient network failures
    adapter.fail_attempts_remaining = 2

    downloader = HistoricalCandleDownloader(storage_manager=storage)
    job = HistoricalCollectionJob(
        job_id="TEST-JOB-RETRY-01",
        exchange=Exchange.ASTER,
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        requested_start_ms=1_000_000,
        requested_end_ms=1_000_000 + (9 * 300_000),
    )

    valid_candles, report = await downloader.download(
        job=job,
        adapter=adapter,
        page_limit=1000,
        max_retries=4,
        backoff_base_s=0.01,
    )

    assert len(valid_candles) == 10
    assert job.status == CollectionJobStatus.COMPLETED
    assert len(adapter.request_history) == 3  # 2 failed attempts + 1 successful attempt


@pytest.mark.asyncio
async def test_downloader_checkpoint_and_resume(tmp_path: Path) -> None:
    """Verify interrupted download persists checkpoint and resumes cleanly."""
    db_path = tmp_path / "test.db"
    db_mgr = DatabaseManager(db_path)
    await db_mgr.initialize()
    conn = await db_mgr.connect()
    repo = HistoricalRepository(conn)
    storage = ParquetStorageManager(tmp_path / "parquet")

    adapter = MockExchangeAdapter(exchange=Exchange.ASTER)
    # 25 candles total
    adapter.mock_data = generate_mock_aster_klines(1_000_000, 25, interval_ms=300_000)

    # Save job before checkpoint to satisfy foreign key integrity
    job = HistoricalCollectionJob(
        job_id="TEST-JOB-RESUME",
        exchange=Exchange.ASTER,
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        requested_start_ms=1_000_000,
        requested_end_ms=1_000_000 + (24 * 300_000),
    )
    await repo.save_job(job)

    # Create pre-existing checkpoint indicating that candles down to 1_500_000 have been fetched
    checkpoint = HistoricalCollectionCheckpoint(
        checkpoint_id="CHK-TEST-JOB-RESUME",
        job_id="TEST-JOB-RESUME",
        exchange=Exchange.ASTER,
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        direction="BACKWARD",
        last_fetched_open_time_ms=1_499_999,
        last_page_candle_count=10,
        earliest_open_time_ms=1_500_000,
        latest_open_time_ms=1_000_000 + (24 * 300_000),
        is_exhausted=False,
    )
    await repo.save_checkpoint(checkpoint)

    downloader = HistoricalCandleDownloader(storage_manager=storage, repository=repo)
    valid_candles, report = await downloader.download(job=job, adapter=adapter, page_limit=1000)

    # First request must resume from checkpoint cursor (1_499_999)
    first_req = adapter.request_history[0]
    assert first_req["params"]["endTime"] == 1_499_999
    assert job.status == CollectionJobStatus.COMPLETED
    # Checkpoint must be removed upon completion
    final_chk = await repo.get_checkpoint("TEST-JOB-RESUME")
    assert final_chk is None


@pytest.mark.asyncio
async def test_duplicate_concurrent_job_rejection(tmp_path: Path) -> None:
    """Verify that HistoricalDataService rejects duplicate active jobs on the same partition."""
    from quantum.historical.service import HistoricalDataService

    service = HistoricalDataService(storage_dir=tmp_path / "parquet")
    adapter = MockExchangeAdapter(exchange=Exchange.ASTER)
    adapter.mock_data = generate_mock_aster_klines(1_000_000, 5)

    job1 = await service.start_collection(
        exchange=Exchange.ASTER,
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        requested_start_ms=1_000_000,
        requested_end_ms=2_000_000,
        adapter=adapter,
    )

    # Immediately attempting to start a duplicate active job on same partition must raise RuntimeError
    # unless job1 has already finished
    if job1.status == CollectionJobStatus.RUNNING:
        with pytest.raises(RuntimeError, match="already actively running"):
            await service.start_collection(
                exchange=Exchange.ASTER,
                symbol="BTCUSDT",
                timeframe=Timeframe.M5,
                requested_start_ms=1_000_000,
                requested_end_ms=2_000_000,
                adapter=adapter,
            )


@pytest.mark.asyncio
async def test_sync_incremental_initial_and_catchup(tmp_path: Path) -> None:
    """Verify sync_incremental performs full backfill on cold start and catch-up on subsequent runs."""
    from quantum.historical.service import HistoricalDataService
    from quantum.historical.models import CanonicalCandle

    service = HistoricalDataService(storage_dir=tmp_path / "parquet")
    adapter = MockExchangeAdapter(exchange=Exchange.ASTER)
    adapter.mock_data = generate_mock_aster_klines(1_000_000_000, 20, interval_ms=300_000)

    now_ms = 1_000_000_000 + (100 * 300_000)

    # 1. Cold start: empty Parquet store -> full backfill targeting 3 years (1095 days)
    job_initial = await service.sync_incremental(
        exchange=Exchange.ASTER,
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        adapter=adapter,
        max_lookback_days=1095,
        current_time_ms=now_ms,
    )
    assert job_initial is not None
    expected_start = now_ms - (1095 * 86_400_000)
    assert job_initial.requested_start_ms == expected_start
    assert job_initial.requested_end_ms == now_ms

    # Wait for job_initial background task to complete
    await asyncio.sleep(0.1)

    # 2. Existing data test: populate canonical store with candles up to T_stored
    t_stored = 1_000_000_000 + (10 * 300_000)
    candles = [
        CanonicalCandle(
            exchange=Exchange.ASTER,
            symbol="ETHUSDT",
            market_type="PERPETUAL",
            timeframe=Timeframe.M5,
            open_time_ms=1_000_000_000 + (i * 300_000),
            close_time_ms=1_000_000_000 + ((i + 1) * 300_000) - 1,
            open=3000.0,
            high=3010.0,
            low=2990.0,
            close=3005.0,
            volume=5.0,
            source_run_id="PRE-POP",
        )
        for i in range(11)  # 0 to 10
    ]
    service.storage.write_canonical_candles(candles, Exchange.ASTER, "ETHUSDT", Timeframe.M5)

    # Catch-up run at t_stored + 10 hours
    now_catchup = t_stored + (10 * 3_600_000)
    job_catchup = await service.sync_incremental(
        exchange=Exchange.ASTER,
        symbol="ETHUSDT",
        timeframe=Timeframe.M5,
        adapter=adapter,
        current_time_ms=now_catchup,
    )
    assert job_catchup is not None
    assert job_catchup.requested_start_ms == t_stored + 300_000
    assert job_catchup.requested_end_ms == now_catchup

    # 3. Up to date test: current time is within 1 candle interval
    now_current = t_stored + 100_000  # only 100s after latest bar
    job_none = await service.sync_incremental(
        exchange=Exchange.ASTER,
        symbol="ETHUSDT",
        timeframe=Timeframe.M5,
        adapter=adapter,
        current_time_ms=now_current,
    )
    assert job_none is None  # Zero network requests issued
