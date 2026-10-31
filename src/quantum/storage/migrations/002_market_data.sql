-- ============================================================================
-- QUANTUM Trading Desk: Migration 002 - Market Data Infrastructure
-- High-throughput time-series tables for tickers, orderbooks, candles, and health
-- ============================================================================

-- Table 1: market_tickers
-- Periodic snapshots of market ticker metrics
CREATE TABLE IF NOT EXISTS market_tickers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_id TEXT NOT NULL REFERENCES exchange_instruments(instrument_id) ON DELETE CASCADE,
    timestamp_ms INTEGER NOT NULL,
    last_price REAL NOT NULL,
    mark_price REAL NOT NULL,
    index_price REAL NOT NULL,
    bid1_price REAL NOT NULL,
    bid1_size REAL NOT NULL,
    ask1_price REAL NOT NULL,
    ask1_size REAL NOT NULL,
    spread_bps REAL NOT NULL,
    volume_24h REAL NOT NULL,
    turnover_24h_usdt REAL NOT NULL,
    open_interest REAL,
    funding_rate REAL,
    next_funding_time_ms INTEGER
);

CREATE INDEX IF NOT EXISTS idx_market_tickers_inst_ts 
    ON market_tickers(instrument_id, timestamp_ms DESC);

CREATE INDEX IF NOT EXISTS idx_market_tickers_ts 
    ON market_tickers(timestamp_ms);


-- Table 2: market_orderbook_snapshots
-- Serialized snapshots of top-N order book depth
CREATE TABLE IF NOT EXISTS market_orderbook_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_id TEXT NOT NULL REFERENCES exchange_instruments(instrument_id) ON DELETE CASCADE,
    timestamp_ms INTEGER NOT NULL,
    update_id INTEGER NOT NULL,
    bids_json TEXT NOT NULL,
    asks_json TEXT NOT NULL,
    bid1_price REAL NOT NULL,
    ask1_price REAL NOT NULL,
    spread_bps REAL NOT NULL,
    is_crossed INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_market_ob_inst_ts 
    ON market_orderbook_snapshots(instrument_id, timestamp_ms DESC);

CREATE INDEX IF NOT EXISTS idx_market_ob_ts 
    ON market_orderbook_snapshots(timestamp_ms);


-- Table 3: market_candles
-- Multi-timeframe OHLCV bar history with deduplication
CREATE TABLE IF NOT EXISTS market_candles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_id TEXT NOT NULL REFERENCES exchange_instruments(instrument_id) ON DELETE CASCADE,
    timeframe TEXT NOT NULL,
    open_time_ms INTEGER NOT NULL,
    close_time_ms INTEGER NOT NULL,
    open_price REAL NOT NULL,
    high_price REAL NOT NULL,
    low_price REAL NOT NULL,
    close_price REAL NOT NULL,
    volume REAL NOT NULL,
    turnover_usdt REAL NOT NULL,
    trades_count INTEGER NOT NULL DEFAULT 0,
    is_closed INTEGER NOT NULL DEFAULT 1,
    CONSTRAINT uq_candles UNIQUE(instrument_id, timeframe, open_time_ms)
);

CREATE INDEX IF NOT EXISTS idx_market_candles_lookup 
    ON market_candles(instrument_id, timeframe, open_time_ms DESC);

CREATE INDEX IF NOT EXISTS idx_market_candles_ts 
    ON market_candles(open_time_ms);


-- Table 4: exchange_connection_health
-- Exchange connection lifecycle and latency metrics
CREATE TABLE IF NOT EXISTS exchange_connection_health (
    exchange TEXT PRIMARY KEY,
    state TEXT NOT NULL,
    rest_latency_ms REAL NOT NULL DEFAULT 0.0,
    ws_latency_ms REAL NOT NULL DEFAULT 0.0,
    last_heartbeat_ms INTEGER NOT NULL,
    last_message_ms INTEGER NOT NULL,
    reconnect_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    updated_at_ms INTEGER NOT NULL
);


-- Table 5: market_data_audit
-- Audit trail for gap detections, reconnects, uncrossed book violations, etc.
CREATE TABLE IF NOT EXISTS market_data_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_ms INTEGER NOT NULL,
    exchange TEXT NOT NULL,
    event_type TEXT NOT NULL,
    details_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_market_audit_ts 
    ON market_data_audit(timestamp_ms DESC);
