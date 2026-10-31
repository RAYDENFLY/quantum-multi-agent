# Unified Exchange Adapter Architecture

## 1. Architectural Overview

The QUANTUM exchange layer provides a unified, asynchronous, low-resource interface for streaming and querying cryptocurrency derivatives market data from Bybit V5 Linear Perpetuals and AsterDEX Futures.

All adapter implementations inherit from `BaseExchangeAdapter` and normalize external exchange payloads into strictly validated Pydantic models.

```
                      +-----------------------------+
                      |      MarketDataService      |
                      +--------------+--------------+
                                     |
              +----------------------+----------------------+
              |                                             |
   +----------v-----------+                      +----------v-----------+
   | BybitExchangeAdapter |                      | AsterExchangeAdapter |
   +----------+-----------+                      +----------+-----------+
              |                                             |
     +--------+--------+                           +--------+--------+
     |                 |                           |                 |
+----v----+      +-----v----+                 +----v----+      +-----v----+
| REST    |      | WS       |                 | REST    |      | WS       |
| Client  |      | Client   |                 | Client  |      | Client   |
+---------+      +----------+                 +---------+      +----------+
```

## 2. Core Components

### BaseExchangeAdapter
Located in `src/quantum/exchanges/base.py`, this abstract base class defines:
- Dynamic instrument discovery: `fetch_instruments() -> List[InstrumentInfo]`
- 24h ticker retrieval: `fetch_ticker(symbol: str) -> NormalizedTicker`
- Static depth retrieval: `fetch_orderbook_snapshot(symbol: str, limit: int) -> NormalizedOrderBook`
- Chronological OHLCV candles: `fetch_klines(symbol: str, timeframe: Timeframe, limit: int) -> List[NormalizedCandle]`
- Real-time streaming: `connect_market_stream(...)`
- Lifecycle management: `disconnect() -> None`
- Connectivity audit: `health_check() -> ExchangeHealthStatus`

### TokenBucketRateLimiter
Protects exchange IP endpoints from 429 throttling:
- Thread-safe and coroutine-safe using `asyncio.Lock()`.
- Calculates token refill dynamically based on monotonic time delta.
- Non-blocking: coroutines sleep asynchronously for the required fraction of a second when capacity is exhausted.
- Independent limiter per exchange adapter instance.

### MarketDataService Orchestration
Located in `src/quantum/exchanges/service.py`:
- Manages dual-adapter lifecycle concurrently.
- Directs high-frequency tick data to memory buffers.
- Drains memory buffers periodically using a dedicated background worker task off the event loop.
- Routes events across the EventBus using priority lanes:
  - P0 Lane: Critical alerts (feed disconnects, sequence gaps, crossed order books, stale feeds).
  - P1 Lane: Pipeline market events (closed OHLCV candles, market snapshots).
  - P2 Lane: Telemetry (high-frequency ticker updates, L2 depth snapshots, health updates).

## 3. Concurrency and Resource Targets

- Maximum WebSocket subscriptions: 25 symbols per exchange (bounded).
- Concurrency limit: Bounded background tasks for network listening and batch flushing.
- Memory target: Under 250 MB active working set on target hardware (Intel i7-7700HQ / AMD A6-9225).
- Database writes: Grouped into multi-row batch executions (`executemany`) to preserve SQLite WAL performance.
