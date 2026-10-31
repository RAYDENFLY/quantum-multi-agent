"""Unified market data orchestrator service for Bybit and AsterDEX."""

import asyncio
import json
import time
import uuid
from typing import Any, Dict, List, Optional, Set

from quantum.config.settings import Settings
from quantum.core.event_bus import EventBus
from quantum.core.logging import get_logger
from quantum.domain.enums import ConnectionState, EventPriority, Exchange, OrderBookSyncStatus, Timeframe
from quantum.domain.events import (
    TOPIC_MARKET_CANDLE_CLOSED,
    TOPIC_MARKET_FEED_ALERT,
    TOPIC_MARKET_HEALTH,
    TOPIC_MARKET_ORDERBOOK,
    TOPIC_MARKET_TICKER,
    MessageEnvelope,
)
from quantum.exchanges.aster.adapter import AsterExchangeAdapter
from quantum.exchanges.base import BaseExchangeAdapter
from quantum.exchanges.bybit.adapter import BybitExchangeAdapter
from quantum.exchanges.freshness import MarketDataFreshnessMonitor
from quantum.exchanges.models import (
    ExchangeHealthStatus,
    InstrumentInfo,
    NormalizedCandle,
    NormalizedOrderBook,
    NormalizedTicker,
)
from quantum.storage.database import DatabaseManager
from quantum.storage.market_repository import MarketRepository

logger = get_logger("exchanges.service")


class MarketDataService:
    """Manages exchange connectivity, streaming, batch persistence, and EventBus routing."""

    def __init__(
        self,
        settings: Settings,
        db: DatabaseManager,
        event_bus: EventBus,
    ) -> None:
        self.settings = settings
        self.db = db
        self.repository = MarketRepository(db)
        self.event_bus = event_bus

        self.adapters: Dict[Exchange, BaseExchangeAdapter] = {}
        if settings.exchange.bybit_enabled:
            self.adapters[Exchange.BYBIT] = BybitExchangeAdapter(config=settings.exchange.bybit)
        if settings.exchange.aster_enabled:
            self.adapters[Exchange.ASTER] = AsterExchangeAdapter(config=settings.exchange.aster)

        self.freshness = MarketDataFreshnessMonitor(
            stale_threshold_s=settings.exchange.freshness_stale_threshold_s,
            invalid_threshold_s=settings.exchange.freshness_invalid_threshold_s,
            on_stale_callback=self._on_freshness_transition,
        )

        # Batch persistence queues
        self._ticker_batch: List[Dict[str, Any]] = []
        self._orderbook_batch: List[Dict[str, Any]] = []
        self._candle_batch: List[Dict[str, Any]] = []
        self._batch_lock = asyncio.Lock()
        self._flush_lock = asyncio.Lock()

        self._running = False
        self._flush_task: Optional[asyncio.Task] = None
        self._health_task: Optional[asyncio.Task] = None
        self._subscribed_instruments: Set[str] = set()
        self._active_freshness_alerts: Dict[str, OrderBookSyncStatus] = {}
        self._active_crossed_alerts: Set[str] = set()

    async def start(
        self,
        bybit_symbols: Optional[List[str]] = None,
        aster_symbols: Optional[List[str]] = None,
    ) -> None:
        """Initialize discovery, launch market streams, and start background workers."""
        if self._running:
            return

        self._running = True
        logger.info("Starting MarketDataService...")

        # 1. Discover instruments and persist to exchange_instruments table
        await self.discover_instruments()

        # 2. Subscribe to requested or default top symbols
        if Exchange.BYBIT in self.adapters:
            symbols = bybit_symbols or ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
            symbols = symbols[: self.settings.exchange.max_ws_subscriptions]
            for s in symbols:
                self._subscribed_instruments.add(f"BYBIT:{s.upper()}")
            await self.adapters[Exchange.BYBIT].connect_market_stream(
                symbols=symbols,
                on_ticker=self._handle_ticker,
                on_orderbook=self._handle_orderbook,
                on_candle=self._handle_candle,
            )

        if Exchange.ASTER in self.adapters:
            symbols = aster_symbols or ["BTCUSDT", "ETHUSDT"]
            symbols = symbols[: self.settings.exchange.max_ws_subscriptions]
            for s in symbols:
                self._subscribed_instruments.add(f"ASTER:{s.upper()}")
            await self.adapters[Exchange.ASTER].connect_market_stream(
                symbols=symbols,
                on_ticker=self._handle_ticker,
                on_orderbook=self._handle_orderbook,
                on_candle=self._handle_candle,
            )

        # 3. Start batch flushing and health monitoring background tasks
        self._flush_task = asyncio.create_task(self._batch_flush_loop(), name="market_batch_flush")
        self._health_task = asyncio.create_task(self._health_monitor_loop(), name="market_health_monitor")
        logger.info("MarketDataService started with %d subscriptions", len(self._subscribed_instruments))

    async def stop(self) -> None:
        """Gracefully stop background tasks, disconnect adapters, and flush batches."""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping MarketDataService...")

        if self._health_task and not self._health_task.done():
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
            self._health_task = None

        if self._flush_task and not self._flush_task.done():
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
            self._flush_task = None

        # Disconnect all active adapters
        for exchange, adapter in self.adapters.items():
            try:
                await adapter.disconnect()
            except Exception as err:
                logger.error("Error disconnecting adapter %s: %s", exchange.value, err)

        # Flush any remaining items in queues
        await self.flush_batches()
        logger.info("MarketDataService stopped successfully")

    async def discover_instruments(self) -> Dict[Exchange, List[InstrumentInfo]]:
        """Fetch and persist active instruments from all enabled exchanges."""
        results: Dict[Exchange, List[InstrumentInfo]] = {}

        for exchange, adapter in self.adapters.items():
            try:
                instruments = await adapter.fetch_instruments()
                results[exchange] = instruments

                # Convert to dicts for persistence
                records = [
                    {
                        "instrument_id": inst.instrument_id,
                        "exchange": inst.exchange.value,
                        "symbol": inst.symbol,
                        "base_asset": inst.base_asset,
                        "quote_asset": inst.quote_asset,
                        "status": inst.status.value,
                        "tick_size": inst.tick_size,
                        "lot_step": inst.lot_step,
                        "min_order_qty": inst.min_order_qty,
                        "max_order_qty": inst.max_order_qty,
                        "min_notional_usdt": inst.min_notional_usdt,
                        "max_leverage": inst.max_leverage,
                        "maker_fee_rate": inst.maker_fee_rate,
                        "taker_fee_rate": inst.taker_fee_rate,
                        "onboard_timestamp_ms": inst.onboard_timestamp_ms,
                        "updated_at_ms": inst.updated_at_ms,
                    }
                    for inst in instruments
                ]
                count = await self.repository.save_instruments(records)
                logger.info("Persisted %d instruments for %s", count, exchange.value)
            except Exception as err:
                logger.error("Failed discovering instruments for %s: %s", exchange.value, err, exc_info=True)

        return results

    async def _handle_ticker(self, ticker: NormalizedTicker) -> None:
        """Process incoming ticker update."""
        self.freshness.record_ticker_heartbeat(ticker.instrument_id)

        # Append to persistence batch
        record = {
            "instrument_id": ticker.instrument_id,
            "timestamp_ms": ticker.timestamp_ms,
            "last_price": ticker.last_price,
            "mark_price": ticker.mark_price,
            "index_price": ticker.index_price,
            "bid1_price": ticker.bid1_price,
            "bid1_size": ticker.bid1_size,
            "ask1_price": ticker.ask1_price,
            "ask1_size": ticker.ask1_size,
            "spread_bps": ticker.spread_bps,
            "volume_24h": ticker.volume_24h,
            "turnover_24h_usdt": ticker.turnover_24h_usdt,
            "open_interest": ticker.open_interest,
            "funding_rate": ticker.funding_rate,
            "next_funding_time_ms": ticker.next_funding_time_ms,
        }
        async with self._batch_lock:
            self._ticker_batch.append(record)

        # Publish to EventBus on P2 lane
        envelope = MessageEnvelope(
            message_id=str(uuid.uuid4()),
            pipeline_run_id=f"tick_{ticker.instrument_id}",
            idempotency_key=f"ticker:{ticker.instrument_id}:{ticker.timestamp_ms}",
            source=f"exchange.{ticker.exchange.value.lower()}",
            topic=TOPIC_MARKET_TICKER,
            priority=EventPriority.P2,
            created_at_ms=int(time.time() * 1000),
            snapshot_timestamp_ms=ticker.timestamp_ms,
            model_version="market_v1",
            payload=ticker.model_dump(),
        )
        try:
            await self.event_bus.publish(envelope)
        except Exception:
            pass

    async def _handle_orderbook(self, book: NormalizedOrderBook) -> None:
        """Process incoming orderbook update."""
        self.freshness.record_orderbook_heartbeat(book.instrument_id)

        # Edge-triggered crossed book alert detection
        if book.is_crossed:
            if book.instrument_id not in self._active_crossed_alerts:
                self._active_crossed_alerts.add(book.instrument_id)
                alert_env = MessageEnvelope(
                    message_id=str(uuid.uuid4()),
                    pipeline_run_id=f"alert_{book.instrument_id}",
                    idempotency_key=f"crossed:{book.instrument_id}:alert",
                    source=f"exchange.{book.exchange.value.lower()}",
                    topic=TOPIC_MARKET_FEED_ALERT,
                    priority=EventPriority.P0,
                    created_at_ms=int(time.time() * 1000),
                    snapshot_timestamp_ms=book.timestamp_ms,
                    model_version="market_v1",
                    payload={
                        "type": "CROSSED_ORDERBOOK",
                        "action": "ALERT",
                        "instrument_id": book.instrument_id,
                        "bid1_price": book.bid1_price,
                        "ask1_price": book.ask1_price,
                        "update_id": book.update_id,
                    },
                )
                try:
                    await self.event_bus.publish(alert_env)
                except Exception:
                    pass

                await self.repository.save_audit_event(
                    exchange=book.exchange.value,
                    event_type="CROSSED_BOOK_DETECTED",
                    details={"instrument_id": book.instrument_id, "bid1": book.bid1_price, "ask1": book.ask1_price},
                )
        else:
            if book.instrument_id in self._active_crossed_alerts:
                self._active_crossed_alerts.remove(book.instrument_id)
                recovery_env = MessageEnvelope(
                    message_id=str(uuid.uuid4()),
                    pipeline_run_id=f"alert_recovery_{book.instrument_id}",
                    idempotency_key=f"crossed:{book.instrument_id}:recovery",
                    source=f"exchange.{book.exchange.value.lower()}",
                    topic=TOPIC_MARKET_FEED_ALERT,
                    priority=EventPriority.P0,
                    created_at_ms=int(time.time() * 1000),
                    snapshot_timestamp_ms=book.timestamp_ms,
                    model_version="market_v1",
                    payload={
                        "type": "CROSSED_ORDERBOOK",
                        "action": "RECOVERY",
                        "instrument_id": book.instrument_id,
                        "bid1_price": book.bid1_price,
                        "ask1_price": book.ask1_price,
                        "update_id": book.update_id,
                    },
                )
                try:
                    await self.event_bus.publish(recovery_env)
                except Exception:
                    pass

                await self.repository.save_audit_event(
                    exchange=book.exchange.value,
                    event_type="CROSSED_BOOK_RESOLVED",
                    details={"instrument_id": book.instrument_id},
                )

        # Append to orderbook persistence batch
        top_book = book.top_n(depth=20)
        record = {
            "instrument_id": book.instrument_id,
            "timestamp_ms": book.timestamp_ms,
            "update_id": book.update_id,
            "bids_json": json.dumps([[b.price, b.size] for b in top_book.bids]),
            "asks_json": json.dumps([[a.price, a.size] for a in top_book.asks]),
            "bid1_price": book.bid1_price,
            "ask1_price": book.ask1_price,
            "spread_bps": book.spread_bps,
            "is_crossed": 1 if book.is_crossed else 0,
        }
        async with self._batch_lock:
            self._orderbook_batch.append(record)

        # Publish to EventBus on P2 lane
        envelope = MessageEnvelope(
            message_id=str(uuid.uuid4()),
            pipeline_run_id=f"ob_{book.instrument_id}",
            idempotency_key=f"ob:{book.instrument_id}:{book.update_id}",
            source=f"exchange.{book.exchange.value.lower()}",
            topic=TOPIC_MARKET_ORDERBOOK,
            priority=EventPriority.P2,
            created_at_ms=int(time.time() * 1000),
            snapshot_timestamp_ms=book.timestamp_ms,
            model_version="market_v1",
            payload=top_book.model_dump(),
        )
        try:
            await self.event_bus.publish(envelope)
        except Exception:
            pass

    async def _handle_candle(self, candle: NormalizedCandle) -> None:
        """Process incoming candlestick bar."""
        self.freshness.record_candle_heartbeat(candle.instrument_id)

        # Append to candle persistence batch
        record = {
            "instrument_id": candle.instrument_id,
            "timeframe": candle.timeframe.value,
            "open_time_ms": candle.open_time_ms,
            "close_time_ms": candle.close_time_ms,
            "open_price": candle.open_price,
            "high_price": candle.high_price,
            "low_price": candle.low_price,
            "close_price": candle.close_price,
            "volume": candle.volume,
            "turnover_usdt": candle.turnover_usdt,
            "trades_count": candle.trades_count,
            "is_closed": 1 if candle.is_closed else 0,
        }
        async with self._batch_lock:
            self._candle_batch.append(record)

        # If bar closed, publish to EventBus on P1 lane
        if candle.is_closed:
            envelope = MessageEnvelope(
                message_id=str(uuid.uuid4()),
                pipeline_run_id=f"candle_{candle.instrument_id}_{candle.open_time_ms}",
                idempotency_key=f"candle:{candle.instrument_id}:{candle.timeframe.value}:{candle.open_time_ms}",
                source=f"exchange.{candle.exchange.value.lower()}",
                topic=TOPIC_MARKET_CANDLE_CLOSED,
                priority=EventPriority.P1,
                created_at_ms=int(time.time() * 1000),
                snapshot_timestamp_ms=candle.close_time_ms,
                model_version="market_v1",
                payload=candle.model_dump(),
            )
            try:
                await self.event_bus.publish(envelope)
            except Exception:
                pass

    def _on_freshness_transition(self, instrument_id: str, status: OrderBookSyncStatus) -> None:
        """Edge-triggered callback when feed freshness state changes."""
        if status in (OrderBookSyncStatus.STALE, OrderBookSyncStatus.INVALID):
            if self._active_freshness_alerts.get(instrument_id) != status:
                self._active_freshness_alerts[instrument_id] = status
                logger.warning("Feed alert: %s is now %s", instrument_id, status.value)
                alert_env = MessageEnvelope(
                    message_id=str(uuid.uuid4()),
                    pipeline_run_id=f"freshness_{instrument_id}",
                    idempotency_key=f"freshness:{instrument_id}:{status.value}",
                    source="market.freshness",
                    topic=TOPIC_MARKET_FEED_ALERT,
                    priority=EventPriority.P0,
                    created_at_ms=int(time.time() * 1000),
                    snapshot_timestamp_ms=int(time.time() * 1000),
                    model_version="market_v1",
                    payload={"instrument_id": instrument_id, "action": "ALERT", "status": status.value},
                )
                asyncio.create_task(self.event_bus.publish(alert_env))
                asyncio.create_task(
                    self.repository.save_audit_event(
                        exchange=instrument_id.split(":")[0],
                        event_type=f"FEED_{status.value}",
                        details={"instrument_id": instrument_id},
                    )
                )
        elif status == OrderBookSyncStatus.SYNCHRONIZED:
            if instrument_id in self._active_freshness_alerts:
                prev_status = self._active_freshness_alerts.pop(instrument_id)
                logger.info("Feed recovery: %s recovered from %s", instrument_id, prev_status.value)
                recovery_env = MessageEnvelope(
                    message_id=str(uuid.uuid4()),
                    pipeline_run_id=f"freshness_recovery_{instrument_id}",
                    idempotency_key=f"freshness_recovery:{instrument_id}:{int(time.time() * 1000)}",
                    source="market.freshness",
                    topic=TOPIC_MARKET_FEED_ALERT,
                    priority=EventPriority.P0,
                    created_at_ms=int(time.time() * 1000),
                    snapshot_timestamp_ms=int(time.time() * 1000),
                    model_version="market_v1",
                    payload={
                        "instrument_id": instrument_id,
                        "action": "RECOVERY",
                        "status": "SYNCHRONIZED",
                        "recovered_from": prev_status.value,
                    },
                )
                asyncio.create_task(self.event_bus.publish(recovery_env))
                asyncio.create_task(
                    self.repository.save_audit_event(
                        exchange=instrument_id.split(":")[0],
                        event_type="FEED_RECOVERED",
                        details={"instrument_id": instrument_id, "recovered_from": prev_status.value},
                    )
                )

    async def flush_batches(self) -> None:
        """Flush in-memory batches to SQLite database."""
        async with self._flush_lock:
            async with self._batch_lock:
                tickers = self._ticker_batch
                orderbooks = self._orderbook_batch
                candles = self._candle_batch

                self._ticker_batch = []
                self._orderbook_batch = []
                self._candle_batch = []

            if tickers:
                try:
                    await self.repository.save_tickers_batch(tickers)
                except Exception as err:
                    logger.error("Failed to save tickers batch: %s", err)

            if orderbooks:
                try:
                    await self.repository.save_orderbook_snapshots_batch(orderbooks)
                except Exception as err:
                    logger.error("Failed to save orderbooks batch: %s", err)

            if candles:
                try:
                    await self.repository.save_candles_batch(candles)
                except Exception as err:
                    logger.error("Failed to save candles batch: %s", err)

    async def _batch_flush_loop(self) -> None:
        """Periodic background task draining and flushing write queues."""
        interval = self.settings.exchange.batch_flush_interval_s
        max_size = self.settings.exchange.batch_max_size

        while self._running:
            try:
                await asyncio.sleep(interval)
                # Check if buffer has items or max size reached
                async with self._batch_lock:
                    total_items = len(self._ticker_batch) + len(self._orderbook_batch) + len(self._candle_batch)
                if total_items > 0:
                    await self.flush_batches()
            except asyncio.CancelledError:
                break
            except Exception as err:
                logger.error("Error in batch flush loop: %s", err, exc_info=True)

    async def _health_monitor_loop(self) -> None:
        """Periodic background task conducting health checks and freshness audits."""
        poll_interval = self.settings.exchange.rest_poll_interval_s

        while self._running:
            try:
                await asyncio.sleep(poll_interval)

                # 1. Check freshness of active streams
                self.freshness.check_all()

                # 2. Check health for each adapter
                for exchange, adapter in self.adapters.items():
                    health = await adapter.health_check()
                    await self.repository.update_exchange_health(
                        {
                            "exchange": health.exchange.value,
                            "state": health.state.value,
                            "rest_latency_ms": health.rest_latency_ms,
                            "ws_latency_ms": health.ws_latency_ms,
                            "last_heartbeat_ms": health.last_heartbeat_ms,
                            "last_message_ms": health.last_message_ms,
                            "reconnect_count": health.reconnect_count,
                            "error_count": health.error_count,
                            "last_error": health.last_error,
                            "updated_at_ms": health.updated_at_ms,
                        }
                    )

                    # Publish health update to EventBus P2 lane
                    envelope = MessageEnvelope(
                        message_id=str(uuid.uuid4()),
                        pipeline_run_id=f"health_{exchange.value}",
                        idempotency_key=f"health:{exchange.value}:{health.updated_at_ms}",
                        source=f"exchange.{exchange.value.lower()}",
                        topic=TOPIC_MARKET_HEALTH,
                        priority=EventPriority.P2,
                        created_at_ms=int(time.time() * 1000),
                        snapshot_timestamp_ms=health.updated_at_ms,
                        model_version="market_v1",
                        payload=health.model_dump(),
                    )
                    await self.event_bus.publish(envelope)

            except asyncio.CancelledError:
                break
            except Exception as err:
                logger.error("Error in market health monitor loop: %s", err, exc_info=True)
