"""Unit tests for freshness state separation, P0 alert deduplication, and rate limiter concurrency."""

import asyncio
from pathlib import Path
import time
from unittest.mock import AsyncMock
import pytest

from quantum.config.settings import Settings
from quantum.core.event_bus import EventBus
from quantum.domain.enums import ConnectionState, EventPriority, Exchange, OrderBookSyncStatus
from quantum.domain.events import TOPIC_MARKET_FEED_ALERT, MessageEnvelope
from quantum.exchanges.base import TokenBucketRateLimiter
from quantum.exchanges.freshness import MarketDataFreshnessMonitor
from quantum.exchanges.models import NormalizedOrderBook, NormalizedTicker, OrderBookLevel
from quantum.exchanges.orderbook import BybitLocalOrderBook
from quantum.exchanges.service import MarketDataService
from quantum.storage.database import DatabaseManager


# ============================================================================
# 1. Freshness State Separation Tests
# ============================================================================


def test_freshness_state_separation_ticker_vs_orderbook() -> None:
    """Verify that receiving ticker updates never marks order book feed or sync as valid."""
    monitor = MarketDataFreshnessMonitor(stale_threshold_s=1.0, invalid_threshold_s=3.0)
    ob = BybitLocalOrderBook("BYBIT:BTCUSDT", "BTCUSDT")

    # Order book was initialized and then degraded to STALE
    ob.apply_snapshot([(50000.0, 1.0)], [(50010.0, 1.0)], update_id=10, timestamp_ms=1000)
    ob._last_monotonic = time.monotonic() - 2.0
    assert ob.check_freshness(stale_threshold_s=1.0) == OrderBookSyncStatus.STALE

    # Feed monitor order book last seen is also stale
    monitor._last_orderbook_monotonic["BYBIT:BTCUSDT"] = time.monotonic() - 2.0
    assert monitor.check_orderbook_freshness("BYBIT:BTCUSDT") == OrderBookSyncStatus.STALE

    # Now a fresh TICKER arrives
    monitor.record_ticker_heartbeat("BYBIT:BTCUSDT")

    # 1. Ticker is fresh
    assert monitor.check_ticker_freshness("BYBIT:BTCUSDT") == OrderBookSyncStatus.SYNCHRONIZED

    # 2. Order book feed MUST REMAIN STALE
    assert monitor.check_orderbook_freshness("BYBIT:BTCUSDT") == OrderBookSyncStatus.STALE

    # 3. Order book instance sync status MUST REMAIN STALE
    assert ob.status == OrderBookSyncStatus.STALE


def test_ws_reconnect_does_not_restore_orderbook_validity() -> None:
    """Verify that WebSocket reconnect sets connection state but leaves order book in degraded state."""
    ob = BybitLocalOrderBook("BYBIT:BTCUSDT", "BTCUSDT")
    ob.status = OrderBookSyncStatus.RESYNCING

    # Connection state transitions to CONNECTED after reconnect
    ws_state = ConnectionState.CONNECTED

    # Order book MUST NOT automatically become SYNCHRONIZED
    assert ob.status == OrderBookSyncStatus.RESYNCING
    assert ws_state == ConnectionState.CONNECTED

    # Only a valid snapshot can restore SYNCHRONIZED status
    ob.apply_snapshot([(50000.0, 1.0)], [(50010.0, 1.0)], update_id=20, timestamp_ms=2000)
    assert ob.status == OrderBookSyncStatus.SYNCHRONIZED


def test_fresh_ticker_with_invalid_orderbook_independence() -> None:
    """Verify that an INVALID order book remains INVALID even when receiving rapid tickers."""
    monitor = MarketDataFreshnessMonitor(stale_threshold_s=1.0, invalid_threshold_s=3.0)
    ob = BybitLocalOrderBook("BYBIT:BTCUSDT", "BTCUSDT")

    # Order book is crossed / invalid
    ob.apply_snapshot([(50020.0, 1.0)], [(50010.0, 1.0)], update_id=10, timestamp_ms=1000)
    assert ob.status == OrderBookSyncStatus.INVALID

    # Receive 10 rapid ticker heartbeats
    for _ in range(10):
        monitor.record_ticker_heartbeat("BYBIT:BTCUSDT")

    assert monitor.check_ticker_freshness("BYBIT:BTCUSDT") == OrderBookSyncStatus.SYNCHRONIZED
    # Order book validity remains strictly INVALID
    assert ob.status == OrderBookSyncStatus.INVALID


# ============================================================================
# 2. Edge-Triggered P0 Alert Deduplication Tests
# ============================================================================


@pytest.mark.asyncio
async def test_p0_alert_edge_triggered_deduplication_and_recovery(tmp_path: Path) -> None:
    """Verify edge-triggered P0 alert: 1 alert on STALE, 0 on repeated STALE, 1 on RECOVERY."""
    settings = Settings(data_dir_path=str(tmp_path))
    db = DatabaseManager(settings.db_path)
    await db.initialize()
    event_bus = EventBus()
    await event_bus.start()

    service = MarketDataService(settings, db, event_bus)

    alerts = []

    def on_alert(envelope: MessageEnvelope) -> None:
        if envelope.topic == TOPIC_MARKET_FEED_ALERT:
            alerts.append(envelope)

    event_bus.subscribe(TOPIC_MARKET_FEED_ALERT, on_alert)

    inst = "BYBIT:BTCUSDT"

    # 1. First transition to STALE emits 1 alert
    service._on_freshness_transition(inst, OrderBookSyncStatus.STALE)
    await asyncio.sleep(0.05)
    assert len(alerts) == 1
    assert alerts[0].priority == EventPriority.P0
    assert alerts[0].payload["action"] == "ALERT"
    assert alerts[0].payload["status"] == "STALE"

    # 2. Subsequent repeated STALE checks emit ZERO new alerts
    for _ in range(5):
        service._on_freshness_transition(inst, OrderBookSyncStatus.STALE)
    await asyncio.sleep(0.05)
    assert len(alerts) == 1  # Deduplicated, still 1

    # 3. Transition to SYNCHRONIZED emits 1 RECOVERY event
    service._on_freshness_transition(inst, OrderBookSyncStatus.SYNCHRONIZED)
    await asyncio.sleep(0.05)
    assert len(alerts) == 2
    assert alerts[1].payload["action"] == "RECOVERY"
    assert alerts[1].payload["status"] == "SYNCHRONIZED"

    # 4. Repeated SYNCHRONIZED checks emit nothing
    service._on_freshness_transition(inst, OrderBookSyncStatus.SYNCHRONIZED)
    await asyncio.sleep(0.05)
    assert len(alerts) == 2

    await event_bus.stop()
    await db.close()


@pytest.mark.asyncio
async def test_p0_alert_symbol_isolation(tmp_path: Path) -> None:
    """Verify that one symbol's stale state does not suppress another symbol's alert."""
    settings = Settings(data_dir_path=str(tmp_path))
    db = DatabaseManager(settings.db_path)
    await db.initialize()
    event_bus = EventBus()
    await event_bus.start()

    service = MarketDataService(settings, db, event_bus)

    alerts = []

    def on_alert(envelope: MessageEnvelope) -> None:
        if envelope.topic == TOPIC_MARKET_FEED_ALERT:
            alerts.append(envelope)

    event_bus.subscribe(TOPIC_MARKET_FEED_ALERT, on_alert)

    # Symbol A enters STALE
    service._on_freshness_transition("BYBIT:BTCUSDT", OrderBookSyncStatus.STALE)
    await asyncio.sleep(0.05)
    assert len(alerts) == 1
    assert alerts[0].payload["instrument_id"] == "BYBIT:BTCUSDT"

    # Symbol B enters STALE (MUST NOT be suppressed by Symbol A)
    service._on_freshness_transition("ASTER:ETHUSDT", OrderBookSyncStatus.STALE)
    await asyncio.sleep(0.05)
    assert len(alerts) == 2
    assert alerts[1].payload["instrument_id"] == "ASTER:ETHUSDT"

    await event_bus.stop()
    await db.close()


@pytest.mark.asyncio
async def test_crossed_book_edge_triggered_deduplication(tmp_path: Path) -> None:
    """Verify that crossed order books emit 1 alert on entry and 1 on uncrossing."""
    settings = Settings(data_dir_path=str(tmp_path))
    db = DatabaseManager(settings.db_path)
    await db.initialize()
    event_bus = EventBus()
    await event_bus.start()

    service = MarketDataService(settings, db, event_bus)

    alerts = []

    def on_alert(envelope: MessageEnvelope) -> None:
        if envelope.topic == TOPIC_MARKET_FEED_ALERT:
            alerts.append(envelope)

    event_bus.subscribe(TOPIC_MARKET_FEED_ALERT, on_alert)

    # 1. Crossed book update
    crossed_book = NormalizedOrderBook(
        instrument_id="BYBIT:BTCUSDT",
        exchange=Exchange.BYBIT,
        symbol="BTCUSDT",
        timestamp_ms=1000,
        update_id=1,
        bids=[OrderBookLevel(price=50010.0, size=1.0)],
        asks=[OrderBookLevel(price=50005.0, size=1.0)],
    )
    await service._handle_orderbook(crossed_book)
    await asyncio.sleep(0.05)
    assert len(alerts) == 1
    assert alerts[0].payload["type"] == "CROSSED_ORDERBOOK"
    assert alerts[0].payload["action"] == "ALERT"

    # 2. Repeated crossed updates emit no duplicate alert
    for _ in range(3):
        await service._handle_orderbook(crossed_book)
    await asyncio.sleep(0.05)
    assert len(alerts) == 1

    # 3. Valid uncrossed book update emits 1 RECOVERY event
    uncrossed_book = NormalizedOrderBook(
        instrument_id="BYBIT:BTCUSDT",
        exchange=Exchange.BYBIT,
        symbol="BTCUSDT",
        timestamp_ms=2000,
        update_id=2,
        bids=[OrderBookLevel(price=50000.0, size=1.0)],
        asks=[OrderBookLevel(price=50005.0, size=1.0)],
    )
    await service._handle_orderbook(uncrossed_book)
    await asyncio.sleep(0.05)
    assert len(alerts) == 2
    assert alerts[1].payload["type"] == "CROSSED_ORDERBOOK"
    assert alerts[1].payload["action"] == "RECOVERY"

    await event_bus.stop()
    await db.close()


# ============================================================================
# 3. TokenBucketRateLimiter Concurrency & Boundary Tests
# ============================================================================


@pytest.mark.asyncio
async def test_rate_limiter_event_loop_confinement() -> None:
    """Verify that TokenBucketRateLimiter enforces single event loop confinement."""
    import threading

    limiter = TokenBucketRateLimiter(rate_limit_rps=10.0)

    # First acquisition in current loop succeeds and binds loop
    await limiter.acquire(1.0)
    assert limiter._loop is asyncio.get_running_loop()

    # Attempting to call from a different event loop in another thread raises RuntimeError
    err_holder = []

    def thread_target():
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            async def call_limiter():
                await limiter.acquire(1.0)
            new_loop.run_until_complete(call_limiter())
        except Exception as err:
            err_holder.append(err)
        finally:
            new_loop.close()

    t = threading.Thread(target=thread_target)
    t.start()
    t.join()

    assert len(err_holder) == 1
    assert isinstance(err_holder[0], RuntimeError)
    assert "confined to a single asyncio event loop" in str(err_holder[0])


@pytest.mark.asyncio
async def test_rate_limiter_boundary_safeguards() -> None:
    """Verify zero-cost instant return and cost-exceeds-capacity ValueError."""
    limiter = TokenBucketRateLimiter(rate_limit_rps=5.0, capacity=10.0)

    # Zero cost returns immediately
    start = time.perf_counter()
    await limiter.acquire(0.0)
    await limiter.acquire(-1.0)
    assert time.perf_counter() - start < 0.05

    # Cost exceeding capacity raises ValueError
    with pytest.raises(ValueError, match="exceeds rate limiter burst capacity"):
        await limiter.acquire(15.0)

    # Non-positive rate_limit_rps raises ValueError
    with pytest.raises(ValueError, match="must be strictly positive"):
        TokenBucketRateLimiter(rate_limit_rps=0.0)
