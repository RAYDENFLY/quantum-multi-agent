# Market Data Validation and Freshness Architecture

## 1. Feed Freshness Monitor and State Separation

The `MarketDataFreshnessMonitor` (`src/quantum/exchanges/freshness.py`) ensures that silent feed stalls or dead TCP connections are detected without relying on OS TCP keepalives.

### State Independence Invariants
To prevent feed contamination and false health reporting, five distinct states are strictly decoupled:
1. WebSocket Connection Health: Tracked in `ConnectionState` (`CONNECTED`, `CONNECTING`, `RECONNECTING`, `FAILED`).
2. Ticker Freshness: Tracked via `_last_ticker_monotonic`.
3. Order Book Freshness: Tracked via `_last_orderbook_monotonic`.
4. Order Book Synchronization Validity: Managed strictly on the `LocalOrderBook` instance (`SYNCHRONIZED`, `INITIALIZING`, `RESYNCING`, `INVALID`, `STALE`).
5. Candlestick Freshness: Tracked via `_last_candle_monotonic`.

Key Invariants Enforced:
- A ticker update never marks an unsynchronized or invalid order book as `SYNCHRONIZED`.
- A WebSocket reconnection to `CONNECTED` never automatically restores order book validity; validity is restored only upon successful snapshot and delta alignment.
- A fresh ticker with an invalid order book correctly reports fresh ticker telemetry while preserving an invalid order book veto.

### Monotonic Clock Invariant
All freshness calculations utilize `time.monotonic()` rather than wall-clock `time.time()`. This guards against:
- NTP time synchronization jumps.
- Daylight saving adjustments.
- System clock drift.

### Freshness Thresholds
- Active threshold: Elapsed time < 5.0 seconds -> `SYNCHRONIZED`.
- Stale threshold: Elapsed time >= 5.0 seconds and < 15.0 seconds -> `STALE`.
- Invalid threshold: Elapsed time >= 15.0 seconds -> `INVALID`.

## 2. Edge-Triggered P0 Alert Deduplication

To prevent EventBus saturation and queue overflow during persistent feed degradation, all P0 critical alerts are strictly edge-triggered:
1. Transition on Alert:
   - When a feed degrades to `STALE` or `INVALID`, or an order book crosses, exactly one P0 `TOPIC_MARKET_FEED_ALERT` is published.
   - While the feed remains in that state, subsequent health checks suppress duplicate alerts.
2. Transition on Recovery:
   - When the feed recovers to `SYNCHRONIZED` or uncrosses, exactly one recovery alert (`action: "RECOVERY"`) is published.
3. Symbol Isolation:
   - Alert state tracking is partitioned by `instrument_id`. An alert on symbol A (`BYBIT:BTCUSDT`) never suppresses or interferes with an alert on symbol B (`ASTER:ETHUSDT`).

## 3. TokenBucketRateLimiter Concurrency Semantics

The `TokenBucketRateLimiter` (`src/quantum/exchanges/base.py`) operates under explicit concurrency contracts:
1. Single Event Loop Confinement:
   - Synchronizes coroutines running within a single asyncio event loop using `asyncio.Lock()`.
   - Lazy binding captures `asyncio.get_running_loop()` on initial acquisition.
   - Cross-thread or cross-event-loop usage raises a `RuntimeError` to prevent silent corruption of token state.
2. Boundary Protections:
   - Non-positive costs (`cost <= 0.0`) return immediately.
   - Costs exceeding burst capacity (`cost > capacity`) immediately raise a `ValueError` to prevent indefinite blocking.

## 2. Uncrossed Order Book Invariant

In liquid central limit order books, the best bid must be strictly less than the best ask:

$$\text{bid1\_price} < \text{ask1\_price}$$

Validation sequence:
1. Upon loading any snapshot or applying any delta update, `_is_crossed()` evaluates `max(bids.keys()) >= min(asks.keys())`.
2. If crossed:
   - `is_crossed` flag is set to `True`.
   - Status transitions to `OrderBookSyncStatus.INVALID`.
   - `crossed_count` metric increments.
   - P0 Critical alert `TOPIC_MARKET_FEED_ALERT` is published to the EventBus.
   - An audit record `CROSSED_BOOK_DETECTED` is saved to SQLite.

## 3. High-Throughput Batch Persistence

Writing ticks directly to SQLite on the asyncio loop causes lock contention and latency spikes. QUANTUM addresses this through non-blocking batch persistence:

1. Incoming ticks, orderbook snapshots, and candles are buffered in in-memory Python lists protected by an `asyncio.Lock()`.
2. A background worker task wakes up every `batch_flush_interval_s` (default 1.0s) or when buffer length exceeds `batch_max_size` (default 500 items).
3. The queue is swapped under lock, and writes are executed via `cursor.executemany(...)` using SQLite WAL mode with `PRAGMA synchronous = NORMAL`.
4. Stale historical records are purged periodically according to configured retention policies:
   - Candles: Retained 30 days.
   - Tickers: Retained 7 days.
   - Orderbook snapshots: Retained 24 hours.
