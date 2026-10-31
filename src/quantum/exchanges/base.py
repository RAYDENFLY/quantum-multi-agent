"""Abstract base exchange adapter, rate limiting, and interface contracts."""

from abc import ABC, abstractmethod
import asyncio
import time
from typing import Any, Callable, Coroutine, Dict, List, Optional

from quantum.core.logging import get_logger
from quantum.domain.enums import ConnectionState, Exchange, Timeframe
from quantum.exchanges.models import (
    ExchangeHealthStatus,
    InstrumentInfo,
    NormalizedCandle,
    NormalizedOrderBook,
    NormalizedTicker,
)

logger = get_logger("exchanges.base")


class TokenBucketRateLimiter:
    """Async token bucket rate limiter to prevent exchange throttling.

    Concurrency Assumptions and Event Loop Confinement:
    1. Single Event Loop Confinement:
       This rate limiter is strictly confined to coroutines running within a single
       asyncio event loop. It uses `asyncio.Lock` to serialize token acquisitions
       across asynchronous coroutines without blocking the underlying OS thread.
    2. Multi-Loop and Cross-Thread Guard:
       The limiter dynamically binds to the active running asyncio event loop on its
       first `acquire()` call. If invoked from a different event loop or OS thread,
       it immediately raises a RuntimeError to prevent undefined scheduling behavior.
    3. Boundary and Starvation Safeguards:
       - Zero or negative cost requests return immediately without consuming tokens.
       - Requests with cost exceeding total burst capacity raise a ValueError,
         preventing permanent starvation loops.
    """

    def __init__(self, rate_limit_rps: float, capacity: Optional[float] = None) -> None:
        if rate_limit_rps <= 0.0:
            raise ValueError("rate_limit_rps must be strictly positive")
        self.rate = float(rate_limit_rps)
        self.capacity = float(capacity if capacity is not None else rate_limit_rps)
        self.tokens = self.capacity
        self.last_update = time.monotonic()
        self._lock: Optional[asyncio.Lock] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _get_lock(self) -> asyncio.Lock:
        """Retrieve or lazily initialize asyncio.Lock on the active running loop."""
        current_loop = asyncio.get_running_loop()
        if self._loop is None:
            self._loop = current_loop
            self._lock = asyncio.Lock()
        elif self._loop is not current_loop:
            raise RuntimeError(
                "TokenBucketRateLimiter is confined to a single asyncio event loop. "
                "Cross-event-loop usage is not supported."
            )
        assert self._lock is not None
        return self._lock

    async def acquire(self, cost: float = 1.0) -> None:
        """Acquire tokens, delaying asynchronously if bucket is empty."""
        if cost <= 0.0:
            return

        if cost > self.capacity:
            raise ValueError(
                f"Requested cost {cost} exceeds rate limiter burst capacity {self.capacity}"
            )

        lock = self._get_lock()
        async with lock:
            while True:
                now = time.monotonic()
                elapsed = now - self.last_update
                self.last_update = now
                self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)

                if self.tokens >= cost:
                    self.tokens -= cost
                    return

                # Calculate wait duration
                needed = cost - self.tokens
                wait_time = needed / self.rate
                await asyncio.sleep(wait_time)


class BaseExchangeAdapter(ABC):
    """Abstract interface defining required capabilities for any exchange adapter."""

    def __init__(self, exchange: Exchange, rate_limit_rps: float = 10.0) -> None:
        self.exchange = exchange
        self.rate_limiter = TokenBucketRateLimiter(rate_limit_rps=rate_limit_rps)
        self.state = ConnectionState.DISCONNECTED
        self.health = ExchangeHealthStatus(exchange=exchange, state=self.state)
        self._instruments: Dict[str, InstrumentInfo] = {}

    @abstractmethod
    async def fetch_instruments(self) -> List[InstrumentInfo]:
        """Fetch and normalize all active USDT perpetual futures instruments."""
        pass

    @abstractmethod
    async def fetch_ticker(self, symbol: str) -> NormalizedTicker:
        """Fetch current 24h ticker and market state for a single symbol."""
        pass

    @abstractmethod
    async def fetch_orderbook_snapshot(self, symbol: str, limit: int = 50) -> NormalizedOrderBook:
        """Fetch static L2 order book snapshot."""
        pass

    @abstractmethod
    async def fetch_klines(
        self,
        symbol: str,
        timeframe: Timeframe,
        limit: int = 200,
        before_ms: Optional[int] = None,
    ) -> List[NormalizedCandle]:
        """Fetch historical candlestick bars sorted ascending by open_time_ms."""
        pass

    @abstractmethod
    async def connect_market_stream(
        self,
        symbols: List[str],
        on_ticker: Optional[Callable[[NormalizedTicker], Coroutine[Any, Any, None]]] = None,
        on_orderbook: Optional[Callable[[NormalizedOrderBook], Coroutine[Any, Any, None]]] = None,
        on_candle: Optional[Callable[[NormalizedCandle], Coroutine[Any, Any, None]]] = None,
    ) -> None:
        """Connect WebSocket market stream and subscribe to tickers, depth, and klines."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close WebSocket connections and release underlying client sessions."""
        pass

    @abstractmethod
    async def health_check(self) -> ExchangeHealthStatus:
        """Perform active connectivity check and measure round-trip latency."""
        pass

    def get_instrument(self, symbol: str) -> Optional[InstrumentInfo]:
        """Lookup cached instrument info by raw symbol."""
        return self._instruments.get(symbol.upper())

    def update_instrument_cache(self, instruments: List[InstrumentInfo]) -> None:
        """Update internal instrument cache dictionary."""
        for inst in instruments:
            self._instruments[inst.symbol.upper()] = inst

    def set_connection_state(self, new_state: ConnectionState, error_msg: Optional[str] = None) -> None:
        """Update connection state and health record."""
        self.state = new_state
        self.health.state = new_state
        self.health.updated_at_ms = int(time.time() * 1000)
        if error_msg:
            self.health.last_error = error_msg
            self.health.error_count += 1
