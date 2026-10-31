# Bybit V5 Linear Perpetuals Market Data Specification

## 1. Scope and Configuration

This document specifies the integration with Bybit V5 Linear Perpetual futures contracts (USDT-settled).

Default connectivity parameters:
- REST Base URL: `https://api.bybit.com`
- Public WebSocket URL: `wss://stream.bybit.com/v5/public/linear`
- Default rate limit: 10.0 requests per second
- Category filter: `category=linear`
- Settlement filter: `quoteCoin=USDT`, `contractType=LinearPerpetual`

## 2. Endpoints Implemented

### REST API
1. Instrument Discovery:
   - `GET /v5/market/instruments-info?category=linear&status=Trading&limit=1000`
   - Normalizes tick size, lot step, min/max quantity, min notional, and maximum leverage.
2. 24h Ticker:
   - `GET /v5/market/tickers?category=linear&symbol=<symbol>`
   - Extracts last price, mark price, index price, top bid/ask, 24h volume, turnover, funding rate, and next funding time.
3. Order Book Depth:
   - `GET /v5/market/orderbook?category=linear&symbol=<symbol>&limit=50`
   - Obtains baseline depth snapshot for local order book initialization.
4. Historical Candlesticks:
   - `GET /v5/market/kline?category=linear&symbol=<symbol>&interval=<interval>&limit=200`
   - Invariant enforcement: Bybit returns candles newest-first (descending). The normalizer explicitly reverses and sorts bars ascending by `open_time_ms`.
5. Server Time:
   - `GET /v5/market/time`
   - Computes network round-trip latency and clock drift.

### WebSocket Streams
Topics subscribed per active symbol:
- Tickers: `tickers.<symbol>`
- Order Book Depth: `orderbook.50.<symbol>`
- 1-minute Candlesticks: `kline.1.<symbol>`

## 3. Order Book Synchronization Mechanics

Bybit V5 Linear order book stream (`orderbook.50.<symbol>`) semantics:
1. Snapshot (`type: "snapshot"`):
   - Complete initial depth containing top bids and asks.
   - Clears existing memory book and loads levels.
   - Sets state to `SYNCHRONIZED`.
   - Repeated snapshots (e.g. periodically re-pushed by Bybit when depth is unchanged for 3 seconds on Level 1, or upon resubscription) cleanly overwrite the entire local book.
2. Delta (`type: "delta"`):
   - Modifies existing price levels or inserts new price levels.
   - Quantity of 0 indicates that the price level must be deleted (safe removal even if the level is not currently present in the local book).
   - Monotonic update ID check: Every delta has an update ID `u`. If incoming `u <= last_u`, the packet is a duplicate or out-of-order frame and is discarded.
   - Service restart detection: In Bybit V5, `u = 1` represents a service restart snapshot. The incoming payload immediately clears existing bid/ask levels and overwrites the local order book with the new snapshot levels, maintaining `SYNCHRONIZED` state unless crossed.
   - Cross-engine sequence (`seq`): Represents global matching engine sequence and is NOT consecutive between orderbook messages. It is recorded for telemetry, but never evaluated as consecutive (`seq == last_seq + 1`).
   - Bybit linear order book channel does not provide `pu` (previous update ID), and no `pu` is required or assumed.
   - If a sequence gap or crossed book is detected, state shifts to `RESYNCING` and triggers an asynchronous REST snapshot request.

## 4. Heartbeat Protocol

Bybit public linear WebSocket streams require application-level ping messages:
- Outgoing frame: `{"op": "ping"}`
- Interval: Every 20 seconds.
- Incoming confirmation: `{"op": "pong", "args": [...]}`.
- Connection is marked degraded or reconnecting if pong is not received within 10 seconds.

## 5. Verification Status on Current Host

- Unit Test Verification: Fully verified. 100% of unit tests pass, covering REST clients, rate limiting, kline ordering, order book snapshot overwrites, delta updates, duplicate rejection, and `u=1` service restart recovery.
- Mock Integration Verification: Fully verified using recorded payloads and mock servers.
- Live Public Connectivity: Unverified on this host due to network timeout. DNS resolves `api.bybit.com` and `stream.bybit.com` to `158.140.186.3`, but outbound TCP port 443 SYN packets time out at the local ISP/routing tier. No live traffic was completed on this host.
