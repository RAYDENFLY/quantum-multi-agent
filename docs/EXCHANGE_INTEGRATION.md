# EXCHANGE_INTEGRATION.md: Bybit V5 & AsterDEX Integration Specification

## 1. Architectural Isolation & Normalized Domain Model

Exchange-specific wire formats, endpoint paths, pagination schemes, and WebSocket framing are strictly isolated inside `src/quantum/exchanges/bybit_adapter.py` and `src/quantum/exchanges/aster_adapter.py`. No upstream module (`scanner`, `ml`, `agents`, `risk`, `execution`, `ui`) may inspect raw exchange JSON payloads.

### 1.1 Symbol Normalization Convention
Both Bybit Linear Perpetuals and AsterDEX USDT-M Futures list USDT-margined contracts using concatenated ticker strings (e.g., `BTCUSDT`, `SOLUSDT`, `1000PEPEUSDT`).
* **Canonical Internal Identifier (`instrument_id`)**: `{EXCHANGE}:{RAW_SYMBOL}`, e.g., `BYBIT:BTCUSDT` or `ASTER:BTCUSDT`.
* **Display Symbol (`symbol`)**: `BTCUSDT`.
* **Contract Scope Filter**:
  * Quote coin must be `USDT` (`quoteCoin == "USDT"` on Bybit; `quoteAsset == "USDT"` and `marginAsset == "USDT"` on AsterDEX).
  * Contract type must be perpetual (`contractType == "LinearPerpetual"` on Bybit; `contractType == "PERPETUAL"` on AsterDEX). Dated futures, inverse contracts, and USDC-margined contracts are excluded at Stage A.

---

## 2. Exchange Integration Feasibility & Endpoint Matrix

All endpoints listed below are **100% public, free market data endpoints** requiring no API key, no paid subscription, and no cryptographic signature.

| Capability | Bybit V5 Linear Perpetuals | AsterDEX Perpetuals (`/fapi/v1` & `/fapi/v3`) | Verification Status | Missing Data / Quirks & Fallback Strategy |
| :--- | :--- | :--- | :--- | :--- |
| **REST Base URL** | `https://api.bybit.com` | `https://fapi.asterdex.com` | **VERIFIED FACT** | Configurable fallback mirror URLs in `app_settings`. |
| **WebSocket Base URL** | `wss://stream.bybit.com/v5/public/linear` | `wss://sstream.asterdex.com` | **VERIFIED FACT** | Automatic reconnection with exponential backoff. |
| **Server Time Sync** | `GET /v5/market/time` | `GET /fapi/v1/time` | **VERIFIED FACT** | Polled every 5m to compute `clock_offset_ms`. |
| **Instrument Discovery & Metadata** | `GET /v5/market/instruments-info?category=linear&limit=1000` | `GET /fapi/v1/exchangeInfo` (or `/fapi/v3/exchangeInfo`) | **VERIFIED FACT** | Extracts `tickSize`, `qtyStep`, `minOrderQty`, `minNotional`, `maxLeverage`, and `status`. Refreshed every 30m. |
| **Bulk 24h Tickers (All Pairs)** | `GET /v5/market/tickers?category=linear` | `GET /fapi/v1/ticker/24hr` (no `symbol` param) | **VERIFIED FACT** | Bybit returns 24h stats + bid/ask + mark/index + funding in **1 call**. AsterDEX splits these across 3 bulk endpoints (`ticker/24hr`, `premiumIndex`, `bookTicker`). |
| **Mark Price, Index Price & Funding Rate** | Included in `GET /v5/market/tickers?category=linear` | `GET /fapi/v1/premiumIndex` (no `symbol` param returns all pairs) | **VERIFIED FACT** | If `indexPrice` is `0` or null on newly listed AsterDEX pairs, fallback to `markPrice`. |
| **Best Bid / Ask Spread (Bulk)** | Included in `GET /v5/market/tickers?category=linear` (`bid1Price`, `ask1Price`) | `GET /fapi/v1/ticker/bookTicker` (no `symbol` param returns all pairs) | **VERIFIED FACT** | AsterDEX `Adapter.fetch_all_tickers()` executes `gather(ticker/24hr, premiumIndex, bookTicker)` and merges by `symbol` in `< 5 ms`. |
| **Historical OHLCV (Klines)** | `GET /v5/market/kline?category=linear&symbol={S}&interval={I}&limit=1000` | `GET /fapi/v1/klines?symbol={S}&interval={I}&limit=1500` | **VERIFIED FACT** | **Quirk**: Bybit returns newest candle first (`list[0]`); AsterDEX returns oldest candle first (`list[0]`). Normalizer sorts all kline arrays strictly ascending by `open_time_ms`. |
| **Historical Funding Rate Series (For ML Training)** | `GET /v5/market/funding/history?category=linear&symbol={S}&limit=200` | `GET /fapi/v1/fundingRate?symbol={S}&limit=1000` | **VERIFIED FACT** | Used by the offline historical harvester to build point-in-time funding rate features for ML training. |
| **Order-Book Depth (L2 Snapshot)** | `GET /v5/market/orderbook?category=linear&symbol={S}&limit=50` | `GET /fapi/v1/depth?symbol={S}&limit=50` | **VERIFIED FACT** | Fetched on-demand for Stage D candidates and streamed via WS for active paper positions. |
| **Recent Public Trades** | `GET /v5/market/recent-trade?category=linear&symbol={S}&limit=100` | `GET /fapi/v1/trades?symbol={S}&limit=100` | **VERIFIED FACT** | Used to verify limit order trade-through fills and short-term taker buy/sell aggression features. |
| **WebSocket Ticker / Mark Price** | Topic: `tickers.{symbol}` | Stream: `{symbol_lower}@markPrice@1s` & `{symbol_lower}@miniTicker` | **VERIFIED FACT** | Bybit `tickers.{symbol}` sends delta frames (`type="delta"`) after the initial snapshot; `BybitAdapter` merges delta fields into the cached ticker state. |
| **WebSocket Orderbook Depth** | Topic: `orderbook.50.{symbol}` | Stream: `{symbol_lower}@depth20@100ms` | **VERIFIED FACT** | Maintains live top-20/50 L2 book in memory for realistic paper execution slippage and UI depth bars. |
| **WebSocket Klines** | Topic: `kline.{interval}.{symbol}` | Stream: `{symbol_lower}@kline_{interval}` | **VERIFIED FACT** | Updates the head of the NumPy ring buffer in real time. |
| **Open Interest (Bulk / Per-Pair)** | Included in `GET /v5/market/tickers` (`openInterestValue`) | `GET /fapi/v1/openInterest?symbol={S}` | **UNVERIFIED CAPABILITY** (AsterDEX bulk OI) | Bybit provides bulk `openInterestValue` in tickers. AsterDEX requires per-symbol calls; therefore, OI on AsterDEX is queried **only** for top Stage C candidates, never in Stage A bulk scans. |

---

## 3. Rate Limits, Weight Accounting & Historical Data Harvester

### 3.1 Bybit V5 Rate Limit Policy
* **IP HTTP Limit**: 600 requests per 5-second rolling window (`120 req/sec` theoretical ceiling).
* **Safe Runtime Budget**: Cap `BybitAdapter` REST client at **15 requests/second** (`TokenBucket(rate=15.0, capacity=30)`).
* **Header Inspection**: On every HTTP response, inspect `X-Bapi-Limit-Status` and `X-Bapi-Limit-Reset-Timestamp`. If remaining quota drops below `15%`, pause non-critical backfill requests until `Reset-Timestamp`.

### 3.2 AsterDEX Futures Rate Limit Policy
* **IP Weight Limit**: Standard `/fapi/v1/exchangeInfo` `REQUEST_WEIGHT` ceiling (`1,200-2,400` weight per minute).
* **Endpoint Weights**:
  * `GET /fapi/v1/ticker/24hr` (all symbols): Weight **40**
  * `GET /fapi/v1/premiumIndex` (all symbols): Weight **10**
  * `GET /fapi/v1/ticker/bookTicker` (all symbols): Weight **2**
  * `GET /fapi/v1/klines` (limit 200): Weight **2**; (limit 1000-1500): Weight **5-10**
  * `GET /fapi/v1/depth` (limit 50): Weight **2**
* **Header Inspection**: Read `X-MBX-USED-WEIGHT-1M` on every response. If `used_weight > 800`, throttle kline backfills automatically.

### 3.3 Historical Data Harvester for Local ML Training (`src/quantum/ml/train_worker.py`)
When building or updating the local training dataset for `SCOUT`, `ANALYST`, `SNIPER`, and `BANKER`:
* Paginates backward using `end` / `endTime` (`1000` bars per call on Bybit, `1500` bars per call on AsterDEX) across the top 50 liquid perpetual symbols for `5m`, `15m`, `1h`, and `4h` intervals (e.g., 90 to 180 days of history).
* Incremental delta sync: stores compressed binary NumPy `.npz` partitions on disk (`~/.quantum/historical/{exchange}_{symbol}_{timeframe}.npz`) so subsequent training runs only fetch the newly closed bars since the last training timestamp.
* Strict rate-limit pacing (`max 5 req/sec` on Bybit, `max 300 weight/min` on AsterDEX) so historical harvesting never interferes with live desktop scanning.

---

## 4. Normalized Market Data Interface (`src/quantum/exchanges/base.py`)

```python
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
import numpy as np

from quantum.domain.enums import ExchangeId, Timeframe

@dataclass(frozen=True, slots=True)
class InstrumentMeta:
    instrument_id: str          # e.g. "BYBIT:BTCUSDT"
    exchange: ExchangeId
    symbol: str                 # e.g. "BTCUSDT"
    base_asset: str             # e.g. "BTC"
    quote_asset: str            # "USDT"
    status: str                 # "TRADING" | "SETTLING" | "HALTED"
    tick_size: float            # Minimum price increment
    lot_step: float             # Minimum quantity increment
    min_order_qty: float
    max_order_qty: float
    min_notional_usdt: float
    max_leverage: float
    maker_fee_rate: float       # Default 0.0002 (0.02%)
    taker_fee_rate: float       # Default 0.00055 (0.055% Bybit) / 0.0005 (Aster)
    onboard_timestamp_ms: int

@dataclass(frozen=True, slots=True)
class NormalizedTicker:
    instrument_id: str
    exchange: ExchangeId
    symbol: str
    timestamp_ms: int           # Exchange server timestamp (UTC ms)
    last_price: float
    mark_price: float
    index_price: float
    bid1_price: float
    bid1_size: float
    ask1_price: float
    ask1_size: float
    spread_bps: float           # ((ask1 - bid1) / mid_price) * 10_000
    price_change_24h_pct: float
    volume_24h_base: float
    turnover_24h_usdt: float
    high_24h: float
    low_24h: float
    funding_rate: float         # Current decimal rate (e.g. 0.0001 = 0.01%)
    next_funding_time_ms: int
    open_interest_usdt: float | None

@dataclass(frozen=True, slots=True)
class NormalizedOrderBook:
    instrument_id: str
    exchange: ExchangeId
    symbol: str
    timestamp_ms: int
    sequence_id: int
    bids: np.ndarray            # Shape (N, 2) float64: [price, size] descending
    asks: np.ndarray            # Shape (N, 2) float64: [price, size] ascending

class ExchangeAdapter(ABC):
    """Unified interface implemented by BybitAdapter and AsterDexAdapter."""

    @property
    @abstractmethod
    def exchange_id(self) -> ExchangeId: ...

    @abstractmethod
    async def sync_server_time(self) -> int: ...

    @abstractmethod
    async def fetch_instruments(self) -> list[InstrumentMeta]: ...

    @abstractmethod
    async def fetch_all_tickers(self) -> list[NormalizedTicker]: ...

    @abstractmethod
    async def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: Timeframe,
        limit: int = 250,
        end_time_ms: int | None = None,
    ) -> np.ndarray:
        """
        Returns structured NumPy array sorted oldest-first:
        dtype=[('ts', '<i8'), ('open', '<f8'), ('high', '<f8'), ('low', '<f8'),
               ('close', '<f8'), ('volume', '<f8'), ('turnover', '<f8'), ('is_closed', '?')]
        """

    @abstractmethod
    async def fetch_orderbook(self, symbol: str, limit: int = 50) -> NormalizedOrderBook: ...

    @abstractmethod
    async def subscribe_symbols(
        self,
        symbols: list[str],
        timeframes: list[Timeframe],
        include_orderbook: bool = True,
    ) -> None: ...
```
