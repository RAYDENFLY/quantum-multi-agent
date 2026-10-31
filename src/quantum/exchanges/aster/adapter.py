"""Unified AsterDEX Futures adapter integrating REST and WebSocket."""

import asyncio
import time
from typing import Any, Callable, Coroutine, Dict, List, Optional

from quantum.config.settings import SingleExchangeConfig
from quantum.core.logging import get_logger
from quantum.domain.enums import ConnectionState, Exchange, OrderBookSyncStatus, Timeframe
from quantum.exchanges.aster.normalizer import (
    ASTER_TO_TIMEFRAME,
    TIMEFRAME_TO_ASTER,
    normalize_aster_instrument,
    normalize_aster_klines,
    normalize_aster_orderbook,
    normalize_aster_ticker,
)
from quantum.exchanges.aster.rest import AsterRestClient
from quantum.exchanges.aster.websocket import AsterWebSocketClient
from quantum.exchanges.base import BaseExchangeAdapter
from quantum.exchanges.models import (
    ExchangeHealthStatus,
    InstrumentInfo,
    NormalizedCandle,
    NormalizedOrderBook,
    NormalizedTicker,
)
from quantum.exchanges.orderbook import AsterLocalOrderBook

logger = get_logger("exchanges.aster.adapter")


class AsterExchangeAdapter(BaseExchangeAdapter):
    """Adapter for AsterDEX USDT Perpetual Futures."""

    def __init__(self, config: Optional[SingleExchangeConfig] = None) -> None:
        cfg = config or SingleExchangeConfig(
            rest_base_url="https://fapi.asterdex.com",
            ws_base_url="wss://fstream.asterdex.com/ws",
            rate_limit_rps=10.0,
        )
        super().__init__(exchange=Exchange.ASTER, rate_limit_rps=cfg.rate_limit_rps)
        self.config = cfg

        self.rest = AsterRestClient(
            base_url=cfg.rest_base_url or "https://fapi.asterdex.com",
            rate_limiter=self.rate_limiter,
            timeout_s=cfg.timeout_s,
            max_retries=cfg.max_retries,
            retry_backoff_s=cfg.retry_backoff_s,
        )

        self.ws: Optional[AsterWebSocketClient] = None
        self._local_orderbooks: Dict[str, AsterLocalOrderBook] = {}
        self._on_ticker: Optional[Callable[[NormalizedTicker], Coroutine[Any, Any, None]]] = None
        self._on_orderbook: Optional[Callable[[NormalizedOrderBook], Coroutine[Any, Any, None]]] = None
        self._on_candle: Optional[Callable[[NormalizedCandle], Coroutine[Any, Any, None]]] = None

    def get_orderbook(self, symbol: str) -> AsterLocalOrderBook:
        """Retrieve or create AsterLocalOrderBook for symbol."""
        sym = symbol.upper()
        if sym not in self._local_orderbooks:
            inst_id = f"ASTER:{sym}"
            self._local_orderbooks[sym] = AsterLocalOrderBook(
                instrument_id=inst_id,
                symbol=sym,
                depth=50,
            )
        return self._local_orderbooks[sym]

    async def fetch_instruments(self) -> List[InstrumentInfo]:
        """Fetch and normalize all active AsterDEX futures instruments."""
        raw_info = await self.rest.get_exchange_info()
        raw_symbols = raw_info.get("symbols", [])
        instruments: List[InstrumentInfo] = []
        for raw in raw_symbols:
            norm = normalize_aster_instrument(raw)
            if norm is not None:
                instruments.append(norm)

        self.update_instrument_cache(instruments)
        logger.info("Discovered %d active AsterDEX USDT perpetual instruments", len(instruments))
        return instruments

    async def fetch_ticker(self, symbol: str) -> NormalizedTicker:
        """Fetch current 24h ticker and mark/funding rates for symbol."""
        raw_24hr = await self.rest.get_ticker_24hr(symbol)
        try:
            raw_premium = await self.rest.get_premium_index(symbol)
        except Exception:
            raw_premium = None
        return normalize_aster_ticker(raw_24hr, raw_premium)

    async def fetch_orderbook_snapshot(self, symbol: str, limit: int = 50) -> NormalizedOrderBook:
        """Fetch static depth snapshot and align with buffered local book."""
        raw = await self.rest.get_depth(symbol, limit=limit)
        norm = normalize_aster_orderbook(raw, symbol.upper())
        local_ob = self.get_orderbook(symbol)
        bids = [(b.price, b.size) for b in norm.bids]
        asks = [(a.price, a.size) for a in norm.asks]
        local_ob.apply_snapshot_with_buffer(bids, asks, norm.update_id, norm.timestamp_ms)
        return norm
        asks = [(a.price, a.size) for a in norm.asks]
        local_ob.apply_snapshot(bids, asks, norm.update_id, norm.timestamp_ms)
        return norm

    async def fetch_klines(
        self,
        symbol: str,
        timeframe: Timeframe,
        limit: int = 200,
        before_ms: Optional[int] = None,
    ) -> List[NormalizedCandle]:
        """Fetch historical klines sorted ascending by open_time_ms."""
        interval = TIMEFRAME_TO_ASTER.get(timeframe, "1m")
        raw_list = await self.rest.get_klines(symbol, interval=interval, limit=limit, before_ms=before_ms)
        return normalize_aster_klines(raw_list, symbol.upper(), timeframe)

    async def connect_market_stream(
        self,
        symbols: List[str],
        on_ticker: Optional[Callable[[NormalizedTicker], Coroutine[Any, Any, None]]] = None,
        on_orderbook: Optional[Callable[[NormalizedOrderBook], Coroutine[Any, Any, None]]] = None,
        on_candle: Optional[Callable[[NormalizedCandle], Coroutine[Any, Any, None]]] = None,
    ) -> None:
        """Connect WebSocket and subscribe to ticker, depth, and kline streams."""
        self._on_ticker = on_ticker
        self._on_orderbook = on_orderbook
        self._on_candle = on_candle

        streams: List[str] = []
        for sym in symbols:
            s = sym.lower()
            streams.append(f"{s}@ticker")
            streams.append(f"{s}@depth@100ms")
            streams.append(f"{s}@kline_1m")

        self.ws = AsterWebSocketClient(
            url=self.config.ws_base_url or "wss://fstream.asterdex.com/ws",
            ping_interval_s=self.config.ping_interval_s,
            ping_timeout_s=self.config.ping_timeout_s,
            max_reconnect_attempts=self.config.max_reconnect_attempts,
            initial_backoff_s=self.config.initial_backoff_s,
            max_backoff_s=self.config.max_backoff_s,
            message_handler=self._handle_ws_message,
            state_callback=self._handle_ws_state,
        )
        await self.ws.connect(streams=streams)

    def _handle_ws_state(self, state: ConnectionState, error_msg: Optional[str] = None) -> None:
        """Handle WebSocket lifecycle state change."""
        self.set_connection_state(state, error_msg)

    async def _handle_ws_message(self, data: Dict[str, Any]) -> None:
        """Route incoming AsterDEX WebSocket message to appropriate normalizers."""
        event_type = data.get("e", "")

        if event_type == "24hrTicker":
            if self._on_ticker:
                norm_ticker = normalize_aster_ticker(data)
                await self._on_ticker(norm_ticker)

        elif event_type == "depthUpdate":
            symbol = data.get("s", "")
            if not symbol:
                return

            local_ob = self.get_orderbook(symbol)
            success = local_ob.apply_delta_event(data)
            if not success and local_ob.status in (OrderBookSyncStatus.RESYNCING, OrderBookSyncStatus.INVALID):
                # Sequence gap or invalid: fetch fresh snapshot in background
                asyncio.create_task(self._resync_orderbook(symbol))

            if self._on_orderbook and local_ob.status == OrderBookSyncStatus.SYNCHRONIZED:
                await self._on_orderbook(local_ob.to_normalized())

        elif event_type == "kline":
            k = data.get("k", {})
            symbol = data.get("s", "")
            if k and self._on_candle and symbol:
                interval_str = k.get("i", "1m")
                timeframe = ASTER_TO_TIMEFRAME.get(interval_str, Timeframe.M1)

                open_time = int(k.get("t", 0))
                close_time = int(k.get("T", 0))
                open_p = float(k.get("o", 0.0))
                high_p = float(k.get("h", 0.0))
                low_p = float(k.get("l", 0.0))
                close_p = float(k.get("c", 0.0))
                vol = float(k.get("v", 0.0))
                turnover = float(k.get("q", 0.0))
                trades = int(k.get("n", 0))
                is_closed = bool(k.get("x", False))

                candle = NormalizedCandle(
                    instrument_id=f"ASTER:{symbol}",
                    exchange=Exchange.ASTER,
                    symbol=symbol,
                    timeframe=timeframe,
                    open_time_ms=open_time,
                    close_time_ms=close_time,
                    open_price=open_p,
                    high_price=high_p,
                    low_price=low_p,
                    close_price=close_p,
                    volume=vol,
                    turnover_usdt=turnover,
                    trades_count=trades,
                    is_closed=is_closed,
                )
                await self._on_candle(candle)

    async def _resync_orderbook(self, symbol: str) -> None:
        """Fetch full depth snapshot after sequence gap detection."""
        try:
            logger.info("Resyncing AsterDEX order book for %s via REST snapshot", symbol)
            await self.fetch_orderbook_snapshot(symbol)
        except Exception as err:
            logger.error("Failed to resync AsterDEX orderbook for %s: %s", symbol, err)

    async def disconnect(self) -> None:
        """Disconnect WebSocket and REST sessions."""
        if self.ws:
            await self.ws.disconnect()
            self.ws = None
        await self.rest.close()
        self.set_connection_state(ConnectionState.DISCONNECTED)
        logger.info("AsterDEX adapter shutdown completed")

    async def health_check(self) -> ExchangeHealthStatus:
        """Query AsterDEX server time to compute REST round-trip latency."""
        start = time.perf_counter()
        try:
            server_time = await self.rest.get_server_time()
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            self.health.rest_latency_ms = elapsed_ms
            self.health.last_heartbeat_ms = int(time.time() * 1000)
            self.health.state = ConnectionState.CONNECTED if self.ws and self.ws.state == ConnectionState.CONNECTED else ConnectionState.DISCONNECTED
            self.health.updated_at_ms = int(time.time() * 1000)
            return self.health
        except Exception as err:
            self.health.error_count += 1
            self.health.last_error = str(err)
            self.health.updated_at_ms = int(time.time() * 1000)
            return self.health
