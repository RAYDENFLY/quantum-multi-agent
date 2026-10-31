"""Unified Bybit V5 Linear Perpetuals adapter integrating REST and WebSocket."""

import asyncio
import time
from typing import Any, Callable, Coroutine, Dict, List, Optional

from quantum.config.settings import SingleExchangeConfig
from quantum.core.logging import get_logger
from quantum.domain.enums import ConnectionState, Exchange, OrderBookSyncStatus, Timeframe
from quantum.exchanges.base import BaseExchangeAdapter
from quantum.exchanges.bybit.normalizer import (
    BYBIT_TO_TIMEFRAME,
    TIMEFRAME_TO_BYBIT,
    normalize_bybit_instrument,
    normalize_bybit_klines,
    normalize_bybit_orderbook,
    normalize_bybit_ticker,
)
from quantum.exchanges.bybit.rest import BybitRestClient
from quantum.exchanges.bybit.websocket import BybitWebSocketClient
from quantum.exchanges.models import (
    ExchangeHealthStatus,
    InstrumentInfo,
    NormalizedCandle,
    NormalizedOrderBook,
    NormalizedTicker,
)
from quantum.exchanges.orderbook import BybitLocalOrderBook

logger = get_logger("exchanges.bybit.adapter")


class BybitExchangeAdapter(BaseExchangeAdapter):
    """Adapter for Bybit V5 Linear Perpetual futures."""

    def __init__(self, config: Optional[SingleExchangeConfig] = None) -> None:
        cfg = config or SingleExchangeConfig(
            rest_base_url="https://api.bybit.com",
            ws_base_url="wss://stream.bybit.com/v5/public/linear",
            rate_limit_rps=10.0,
        )
        super().__init__(exchange=Exchange.BYBIT, rate_limit_rps=cfg.rate_limit_rps)
        self.config = cfg

        self.rest = BybitRestClient(
            base_url=cfg.rest_base_url or "https://api.bybit.com",
            rate_limiter=self.rate_limiter,
            timeout_s=cfg.timeout_s,
            max_retries=cfg.max_retries,
            retry_backoff_s=cfg.retry_backoff_s,
        )

        self.ws: Optional[BybitWebSocketClient] = None
        self._local_orderbooks: Dict[str, BybitLocalOrderBook] = {}
        self._on_ticker: Optional[Callable[[NormalizedTicker], Coroutine[Any, Any, None]]] = None
        self._on_orderbook: Optional[Callable[[NormalizedOrderBook], Coroutine[Any, Any, None]]] = None
        self._on_candle: Optional[Callable[[NormalizedCandle], Coroutine[Any, Any, None]]] = None

    def get_orderbook(self, symbol: str) -> BybitLocalOrderBook:
        """Retrieve or create BybitLocalOrderBook for symbol."""
        sym = symbol.upper()
        if sym not in self._local_orderbooks:
            inst_id = f"BYBIT:{sym}"
            self._local_orderbooks[sym] = BybitLocalOrderBook(
                instrument_id=inst_id,
                symbol=sym,
                depth=50,
            )
        return self._local_orderbooks[sym]

    async def fetch_instruments(self) -> List[InstrumentInfo]:
        """Fetch and normalize all active Bybit linear perpetual instruments."""
        raw_list = await self.rest.get_instruments_info()
        instruments: List[InstrumentInfo] = []
        for raw in raw_list:
            norm = normalize_bybit_instrument(raw)
            if norm is not None:
                instruments.append(norm)

        self.update_instrument_cache(instruments)
        logger.info("Discovered %d active Bybit USDT perpetual instruments", len(instruments))
        return instruments

    async def fetch_ticker(self, symbol: str) -> NormalizedTicker:
        """Fetch current 24h ticker for symbol."""
        raw = await self.rest.get_ticker(symbol)
        return normalize_bybit_ticker(raw)

    async def fetch_orderbook_snapshot(self, symbol: str, limit: int = 50) -> NormalizedOrderBook:
        """Fetch static orderbook snapshot and populate local book."""
        raw = await self.rest.get_orderbook(symbol, limit=limit)
        norm = normalize_bybit_orderbook(raw, symbol.upper())
        local_ob = self.get_orderbook(symbol)
        bids = [(b.price, b.size) for b in norm.bids]
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
        interval = TIMEFRAME_TO_BYBIT.get(timeframe, "1")
        raw_list = await self.rest.get_klines(symbol, interval=interval, limit=limit, before_ms=before_ms)
        return normalize_bybit_klines(raw_list, symbol.upper(), timeframe)

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

        topics: List[str] = []
        for sym in symbols:
            s = sym.upper()
            topics.append(f"tickers.{s}")
            topics.append(f"orderbook.50.{s}")
            topics.append(f"kline.1.{s}")

        self.ws = BybitWebSocketClient(
            url=self.config.ws_base_url or "wss://stream.bybit.com/v5/public/linear",
            ping_interval_s=self.config.ping_interval_s,
            ping_timeout_s=self.config.ping_timeout_s,
            max_reconnect_attempts=self.config.max_reconnect_attempts,
            initial_backoff_s=self.config.initial_backoff_s,
            max_backoff_s=self.config.max_backoff_s,
            message_handler=self._handle_ws_message,
            state_callback=self._handle_ws_state,
        )
        await self.ws.connect(topics=topics)

    def _handle_ws_state(self, state: ConnectionState, error_msg: Optional[str] = None) -> None:
        """Handle WebSocket lifecycle state change."""
        self.set_connection_state(state, error_msg)

    async def _handle_ws_message(self, data: Dict[str, Any]) -> None:
        """Route incoming WebSocket message to appropriate normalizers and callbacks."""
        topic = data.get("topic", "")
        if not topic:
            return

        parts = topic.split(".")
        category = parts[0]

        if category == "tickers":
            ticker_data = data.get("data", {})
            if ticker_data and self._on_ticker:
                norm_ticker = normalize_bybit_ticker(ticker_data)
                await self._on_ticker(norm_ticker)

        elif category == "orderbook":
            msg_type = data.get("type", "")
            ob_data = data.get("data", {})
            symbol = ob_data.get("s", "")
            if not symbol:
                return

            local_ob = self.get_orderbook(symbol)
            bids = [(float(b[0]), float(b[1])) for b in ob_data.get("b", [])]
            asks = [(float(a[0]), float(a[1])) for a in ob_data.get("a", [])]
            update_id = int(ob_data.get("u", 0))
            seq = int(ob_data.get("seq", 0))
            ts = int(data.get("ts", time.time() * 1000))

            if msg_type == "snapshot" or update_id == 1:
                local_ob.apply_snapshot(bids, asks, update_id, ts, seq=seq)
            elif msg_type == "delta":
                success = local_ob.apply_delta(bids, asks, update_id, ts, seq=seq)
                if not success and local_ob.status in (OrderBookSyncStatus.RESYNCING, OrderBookSyncStatus.INVALID):
                    asyncio.create_task(self._resync_orderbook(symbol))

            if self._on_orderbook and local_ob.status == OrderBookSyncStatus.SYNCHRONIZED:
                await self._on_orderbook(local_ob.to_normalized())

        elif category == "kline":
            kline_list = data.get("data", [])
            interval_str = parts[1] if len(parts) > 1 else "1"
            symbol = parts[2] if len(parts) > 2 else ""
            timeframe = BYBIT_TO_TIMEFRAME.get(interval_str, Timeframe.M1)

            if kline_list and self._on_candle and symbol:
                for k in kline_list:
                    # WebSocket kline format has: start, end, interval, open, close, high, low, volume, turnover, confirm
                    open_time = int(k.get("start", 0))
                    close_time = int(k.get("end", 0))
                    open_p = float(k.get("open", 0.0))
                    high_p = float(k.get("high", 0.0))
                    low_p = float(k.get("low", 0.0))
                    close_p = float(k.get("close", 0.0))
                    vol = float(k.get("volume", 0.0))
                    turnover = float(k.get("turnover", 0.0))
                    is_closed = bool(k.get("confirm", False))

                    candle = NormalizedCandle(
                        instrument_id=f"BYBIT:{symbol}",
                        exchange=Exchange.BYBIT,
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
                        trades_count=0,
                        is_closed=is_closed,
                    )
                    await self._on_candle(candle)

    async def _resync_orderbook(self, symbol: str) -> None:
        """Fetch full snapshot after sequence gap detection."""
        try:
            logger.info("Resyncing order book for %s via REST snapshot", symbol)
            await self.fetch_orderbook_snapshot(symbol)
        except Exception as err:
            logger.error("Failed to resync orderbook for %s: %s", symbol, err)

    async def disconnect(self) -> None:
        """Disconnect WebSocket and REST sessions."""
        if self.ws:
            await self.ws.disconnect()
            self.ws = None
        await self.rest.close()
        self.set_connection_state(ConnectionState.DISCONNECTED)
        logger.info("Bybit adapter shutdown completed")

    async def health_check(self) -> ExchangeHealthStatus:
        """Query Bybit server time to compute REST round-trip latency."""
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
