"""Integration tests for MarketDataService orchestrating adapters, persistence, and EventBus."""

import asyncio
from pathlib import Path
import time
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from quantum.config.settings import Settings
from quantum.core.event_bus import EventBus
from quantum.domain.enums import ConnectionState, ContractStatus, ContractType, EventPriority, Exchange, Timeframe
from quantum.domain.events import (
    TOPIC_MARKET_CANDLE_CLOSED,
    TOPIC_MARKET_FEED_ALERT,
    TOPIC_MARKET_ORDERBOOK,
    TOPIC_MARKET_TICKER,
    MessageEnvelope,
)
from quantum.exchanges.models import (
    ExchangeHealthStatus,
    InstrumentInfo,
    NormalizedCandle,
    NormalizedOrderBook,
    NormalizedTicker,
    OrderBookLevel,
)
from quantum.exchanges.service import MarketDataService
from quantum.storage.database import DatabaseManager


@pytest.mark.asyncio
async def test_market_data_service_lifecycle_and_eventbus_dispatch(tmp_path: Path) -> None:
    """Verify instrument discovery, ticker/candle/orderbook routing to EventBus and SQLite."""
    settings = Settings(data_dir_path=str(tmp_path))
    settings.exchange.batch_flush_interval_s = 0.1

    db = DatabaseManager(settings.db_path)
    await db.initialize()

    event_bus = EventBus()
    await event_bus.start()

    service = MarketDataService(settings, db, event_bus)

    # Capture published EventBus envelopes
    dispatched_events = []

    async def event_collector(envelope: MessageEnvelope) -> None:
        dispatched_events.append(envelope)

    event_bus.subscribe("market.*", event_collector)

    # Mock instruments returned by discovery
    mock_bybit_instruments = [
        InstrumentInfo(
            instrument_id="BYBIT:BTCUSDT",
            exchange=Exchange.BYBIT,
            symbol="BTCUSDT",
            base_asset="BTC",
            quote_asset="USDT",
            status=ContractStatus.TRADING,
            contract_type=ContractType.PERPETUAL,
            tick_size=0.1,
            lot_step=0.001,
            min_order_qty=0.001,
            max_order_qty=100.0,
            min_notional_usdt=5.0,
            max_leverage=50.0,
            updated_at_ms=int(time.time() * 1000),
        )
    ]
    mock_aster_instruments = [
        InstrumentInfo(
            instrument_id="ASTER:ETHUSDT",
            exchange=Exchange.ASTER,
            symbol="ETHUSDT",
            base_asset="ETH",
            quote_asset="USDT",
            status=ContractStatus.TRADING,
            contract_type=ContractType.PERPETUAL,
            tick_size=0.01,
            lot_step=0.01,
            min_order_qty=0.01,
            max_order_qty=500.0,
            min_notional_usdt=5.0,
            max_leverage=75.0,
            updated_at_ms=int(time.time() * 1000),
        )
    ]

    service.adapters[Exchange.BYBIT].fetch_instruments = AsyncMock(return_value=mock_bybit_instruments)
    service.adapters[Exchange.BYBIT].connect_market_stream = AsyncMock()
    service.adapters[Exchange.BYBIT].disconnect = AsyncMock()
    service.adapters[Exchange.BYBIT].health_check = AsyncMock(
        return_value=ExchangeHealthStatus(exchange=Exchange.BYBIT, state=ConnectionState.CONNECTED, rest_latency_ms=20.0)
    )

    service.adapters[Exchange.ASTER].fetch_instruments = AsyncMock(return_value=mock_aster_instruments)
    service.adapters[Exchange.ASTER].connect_market_stream = AsyncMock()
    service.adapters[Exchange.ASTER].disconnect = AsyncMock()
    service.adapters[Exchange.ASTER].health_check = AsyncMock(
        return_value=ExchangeHealthStatus(exchange=Exchange.ASTER, state=ConnectionState.CONNECTED, rest_latency_ms=25.0)
    )

    # 1. Start service
    await service.start(bybit_symbols=["BTCUSDT"], aster_symbols=["ETHUSDT"])
    assert service._running is True

    # Verify instruments persisted in database
    instruments = await service.repository.get_instruments()
    assert len(instruments) == 2
    symbols = {i["symbol"] for i in instruments}
    assert "BTCUSDT" in symbols
    assert "ETHUSDT" in symbols

    now_ms = int(time.time() * 1000)

    # 2. Simulate incoming ticker
    ticker = NormalizedTicker(
        instrument_id="BYBIT:BTCUSDT",
        exchange=Exchange.BYBIT,
        symbol="BTCUSDT",
        timestamp_ms=now_ms,
        last_price=50000.0,
        mark_price=50001.0,
        index_price=50000.5,
        bid1_price=49999.0,
        bid1_size=1.0,
        ask1_price=50001.0,
        ask1_size=1.0,
        volume_24h=500.0,
        turnover_24h_usdt=25000000.0,
    )
    await service._handle_ticker(ticker)

    # 3. Simulate incoming orderbook
    ob = NormalizedOrderBook(
        instrument_id="BYBIT:BTCUSDT",
        exchange=Exchange.BYBIT,
        symbol="BTCUSDT",
        timestamp_ms=now_ms,
        update_id=101,
        bids=[OrderBookLevel(price=49999.0, size=2.0)],
        asks=[OrderBookLevel(price=50001.0, size=2.0)],
    )
    await service._handle_orderbook(ob)

    # 4. Simulate closed candle
    candle = NormalizedCandle(
        instrument_id="BYBIT:BTCUSDT",
        exchange=Exchange.BYBIT,
        symbol="BTCUSDT",
        timeframe=Timeframe.M1,
        open_time_ms=now_ms - 60000,
        close_time_ms=now_ms - 1,
        open_price=50000.0,
        high_price=50080.0,
        low_price=49980.0,
        close_price=50050.0,
        volume=10.0,
        turnover_usdt=500000.0,
        is_closed=True,
    )
    await service._handle_candle(candle)

    # 5. Simulate crossed book alert
    crossed_ob = NormalizedOrderBook(
        instrument_id="ASTER:ETHUSDT",
        exchange=Exchange.ASTER,
        symbol="ETHUSDT",
        timestamp_ms=now_ms,
        update_id=202,
        bids=[OrderBookLevel(price=3002.0, size=1.0)],
        asks=[OrderBookLevel(price=3001.0, size=1.0)],
    )
    await service._handle_orderbook(crossed_ob)

    # Allow event bus dispatch loop to run
    await asyncio.sleep(0.1)

    # Verify event priorities on EventBus
    topics = [e.topic for e in dispatched_events]
    assert TOPIC_MARKET_TICKER in topics
    assert TOPIC_MARKET_ORDERBOOK in topics
    assert TOPIC_MARKET_CANDLE_CLOSED in topics
    assert TOPIC_MARKET_FEED_ALERT in topics

    candle_event = next(e for e in dispatched_events if e.topic == TOPIC_MARKET_CANDLE_CLOSED)
    assert candle_event.priority == EventPriority.P1

    alert_event = next(e for e in dispatched_events if e.topic == TOPIC_MARKET_FEED_ALERT)
    assert alert_event.priority == EventPriority.P0
    assert alert_event.payload["type"] == "CROSSED_ORDERBOOK"

    # 6. Flush persistence queues to SQLite
    await service.flush_batches()

    persisted_ticker = await service.repository.get_latest_ticker("BYBIT:BTCUSDT")
    assert persisted_ticker is not None
    assert persisted_ticker["last_price"] == 50000.0

    persisted_candles = await service.repository.get_candles("BYBIT:BTCUSDT", "1m")
    assert len(persisted_candles) == 1
    assert persisted_candles[0]["close_price"] == 50050.0

    # 7. Stop service
    await service.stop()
    assert service._running is False

    await event_bus.stop()
    await db.close()
