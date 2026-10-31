# Market Data Contracts and Invariants

## 1. Domain Models

All market data flowing from external exchanges into QUANTUM is validated against immutable and typed Pydantic contracts located in `src/quantum/exchanges/models.py`.

### OrderBookLevel
Represents an individual price level:
- `price: float`: Strictly greater than 0.
- `size: float`: Greater than or equal to 0.

### NormalizedOrderBook
Represents an L2 order book snapshot:
- `instrument_id: str`: Formatted as `<EXCHANGE>:<SYMBOL>` (e.g. `BYBIT:BTCUSDT`).
- `exchange: Exchange`: Enum identifier (`BYBIT` or `ASTER`).
- `symbol: str`: Uppercase raw symbol.
- `timestamp_ms: int`: Millisecond timestamp of data snapshot.
- `update_id: int`: Exchange sequence update counter.
- `bids: List[OrderBookLevel]`: Sorted descending by price.
- `asks: List[OrderBookLevel]`: Sorted ascending by price.
- `bid1_price: float`: Top bid price.
- `bid1_size: float`: Top bid quantity.
- `ask1_price: float`: Top ask price.
- `ask1_size: float`: Top ask quantity.
- `spread_bps: float`: Basis point spread relative to mid-price.
- `mid_price: float`: Average of top bid and top ask.
- `is_crossed: bool`: Flag indicating if `bid1 >= ask1`.

### NormalizedTicker
Represents 24h market activity:
- `instrument_id: str`: Standardized ID.
- `exchange: Exchange`: Originating exchange.
- `symbol: str`: Symbol name.
- `timestamp_ms: int`: Capture timestamp.
- `last_price: float`: Most recent execution price.
- `mark_price: float`: Mark price used for liquidation and margins.
- `index_price: float`: Composite index price.
- `bid1_price: float`, `bid1_size: float`: Best bid.
- `ask1_price: float`, `ask1_size: float`: Best ask.
- `spread_bps: float`: Basis point bid/ask spread.
- `volume_24h: float`: 24h rolling volume in base asset.
- `turnover_24h_usdt: float`: 24h rolling turnover in USDT.
- `funding_rate: Optional[float]`: Current 8-hour funding rate.
- `next_funding_time_ms: Optional[int]`: Next funding settlement time.

### NormalizedCandle
Represents OHLCV candlestick bar:
- `instrument_id: str`: Standardized ID.
- `exchange: Exchange`: Originating exchange.
- `symbol: str`: Symbol name.
- `timeframe: Timeframe`: Standard timeframe enum (e.g. `1m`, `5m`, `15m`, `1h`, `4h`, `1d`).
- `open_time_ms: int`: Bar start timestamp.
- `close_time_ms: int`: Bar close timestamp.
- `open_price: float`, `high_price: float`, `low_price: float`, `close_price: float`: Prices.
- `volume: float`: Volume in base units.
- `turnover_usdt: float`: Volume in USDT units.
- `trades_count: int`: Number of trades executed in bar.
- `is_closed: bool`: True if candle is finalized.

## 2. Mathematical Invariants Enforced

1. OHLC High/Low Bounds:
   - `high_price >= max(open_price, close_price)`
   - `low_price <= min(open_price, close_price)`
   - Any candle violating these bounds fails validation immediately.

2. Chronological Duration:
   - `close_time_ms > open_time_ms`
   - Non-positive durations are rejected.

3. Spread Invariant:
   - `spread_bps = max(0.0, ((ask1_price - bid1_price) / mid_price) * 10000.0)`
   - If `bid1 >= ask1`, book is marked crossed (`is_crossed = True`).
