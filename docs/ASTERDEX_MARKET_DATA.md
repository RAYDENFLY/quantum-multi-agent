# AsterDEX Futures Market Data Specification

## 1. Scope and Configuration

This document specifies the integration with AsterDEX USDT Perpetual Futures contracts.

Default connectivity parameters:
- REST Base URL: `https://fapi.asterdex.com`
- Public WebSocket URL: `wss://fstream.asterdex.com/ws`
- Rate limit: 10.0 requests per second
- Standard: Binance Futures-compatible API conventions (`/fapi/v1`)
- Settlement filter: `quoteAsset=USDT`, `contractType=PERPETUAL`

## 2. Endpoints Implemented

### REST API
1. Instrument Discovery:
   - `GET /fapi/v1/exchangeInfo`
   - Parses symbol definitions and filters (`PRICE_FILTER`, `LOT_SIZE`, `MIN_NOTIONAL`).
2. 24h Ticker Statistics:
   - `GET /fapi/v1/ticker/24hr?symbol=<symbol>`
   - Provides last price, bid/ask, 24h volume, turnover, and price change percentage.
3. Premium Index:
   - `GET /fapi/v1/premiumIndex?symbol=<symbol>`
   - Provides mark price, index price, funding rate, and next funding timestamp.
4. Order Book Depth:
   - `GET /fapi/v1/depth?symbol=<symbol>&limit=50`
   - Returns bids, asks, and `lastUpdateId`.
5. Candlesticks:
   - `GET /fapi/v1/klines?symbol=<symbol>&interval=<interval>&limit=200`
   - Invariant enforcement: AsterDEX delivers bars in chronological order (oldest first). The normalizer verifies and guarantees ascending order.
6. Server Time:
   - `GET /fapi/v1/time`
   - Queries server timestamp for latency diagnostics.

### WebSocket Streams
Subscriptions per symbol:
- Tickers: `<symbol_lower>@ticker`
- Order Book Depth: `<symbol_lower>@depth@100ms`
- Candlesticks: `<symbol_lower>@kline_1m`

Subscription payload structure:
```json
{
  "method": "SUBSCRIBE",
  "params": [
    "btcusdt@depth@100ms",
    "btcusdt@ticker",
    "btcusdt@kline_1m"
  ],
  "id": 1
}
```

## 3. Order Book Synchronization Mechanics

AsterDEX differential depth stream (`<symbol>@depth@100ms`) follows Binance Futures V1/V3 depth synchronization rules:
1. Event Buffering Before Snapshot:
   - When connecting, incoming `depthUpdate` events are accumulated into an in-memory buffer while the REST snapshot is being requested.
2. Snapshot Bridging and Buffer Playback:
   - A REST depth snapshot is retrieved via `GET /fapi/v1/depth?symbol=<symbol>&limit=1000`, returning baseline bids, asks, and `lastUpdateId`.
   - Any buffered event where final update ID `u < lastUpdateId` is dropped.
   - The first processed event must satisfy the bridging condition:
     $$U \le \text{lastUpdateId} \le u \quad \text{or} \quad pu \le \text{lastUpdateId} \le u$$
   - If the buffer cannot bridge the snapshot (e.g. first buffered event has `U > lastUpdateId`), a gap is detected, the book transitions to `RESYNCING`, and synchronization restarts.
   - Once bridged, all remaining buffered events are played back sequentially.
3. Live Delta Continuity:
   - Subsequent events must satisfy: `event.pu == local_ob.last_update_id`.
   - If `event.pu != local_ob.last_update_id`, a sequence mismatch is detected, the local book is invalidated (`RESYNCING`), and a fresh snapshot alignment is scheduled.
4. Level Updates and Invariants:
   - Updates represent absolute quantities, not quantity increments.
   - Quantity of 0 deletes the price level (safe removal even if the level is not present).
   - Uncrossed book invariant (`best_bid < best_ask`) is verified after every update.

## 4. API Version Audit (V1 vs V3)

1. Architecture Evolution:
   - AsterDEX originally deployed standard Binance Futures V1 endpoints under `/fapi/v1/` using HMAC-SHA256 authentication.
   - AsterDEX has phased out issuing new V1 API keys and transitioned account/order execution to V3 (`/fapi/v3/`), which uses an Agent wallet model authenticated by EIP-712 typed signatures and ECDSA.
2. Public Market Data Status:
   - Public market data endpoints (`exchangeInfo`, `ticker/24hr`, `premiumIndex`, `depth`, `klines`, `time`) do not require authentication or API keys.
   - Live network tests confirm that public market data endpoints under `/fapi/v1/` remain fully active, stable, and responsive.
3. Migration Recommendation:
   - Phase 3 (Market Data): Retain the verified V1 public market data adapter. It operates flawlessly without private credentials or EIP-712 complexity.
   - Phase 4 (Live Trading): Plan a dedicated V3 adapter migration for authenticated order placement, position management, and EIP-712 wallet signatures.

## 5. Verification Status on Current Host

- Unit Test Verification: Fully verified across unit test suite.
- Mock Integration Verification: Fully verified with recorded fixtures and synthetic streams.
- Live Public REST Verified: Confirmed live against `https://fapi.asterdex.com` (`exchangeInfo`, `ticker/24hr`, `premiumIndex`, `depth`, `klines`, `time`). Latency: ~300ms.
- Live Public WebSocket Ticker Verified: Confirmed live against `wss://fstream.asterdex.com/ws`, streaming real-time `24hrTicker` frames.
- Live Public WebSocket Depth Synchronized: Confirmed live against `wss://fstream.asterdex.com/ws` with `btcusdt@depth@100ms`. Successfully verified event buffering, REST snapshot bridging ($U \le \text{lastUpdateId} \le u$), continuous $pu$ progression across consecutive frames, and uncrossed top-of-book depth levels.
