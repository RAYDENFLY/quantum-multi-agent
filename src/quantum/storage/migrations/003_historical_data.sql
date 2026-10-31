-- ============================================================================
-- QUANTUM Trading Desk: Migration 003 - Historical Data & Feature Engineering
-- Metadata persistence for collection jobs, checkpoints, manifests, and quality
-- ============================================================================

-- Table 1: historical_collection_jobs
-- Tracks asynchronous historical download jobs and their lifecycle
CREATE TABLE IF NOT EXISTS historical_collection_jobs (
    job_id TEXT PRIMARY KEY,
    exchange TEXT NOT NULL CHECK (exchange IN ('BYBIT', 'ASTER')),
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    requested_start_ms INTEGER NOT NULL,
    requested_end_ms INTEGER NOT NULL,
    actual_start_ms INTEGER,
    actual_end_ms INTEGER,
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', 'PAUSED')),
    total_candles_fetched INTEGER NOT NULL DEFAULT 0,
    checkpoint_ms INTEGER,
    error_message TEXT,
    created_at_ms INTEGER NOT NULL,
    updated_at_ms INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_hist_jobs_exchange_sym 
    ON historical_collection_jobs(exchange, symbol, timeframe);

CREATE INDEX IF NOT EXISTS idx_hist_jobs_status 
    ON historical_collection_jobs(status);


-- Table 2: historical_collection_checkpoints
-- Persists download resume states to support interrupted pagination
CREATE TABLE IF NOT EXISTS historical_collection_checkpoints (
    checkpoint_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES historical_collection_jobs(job_id) ON DELETE CASCADE,
    exchange TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('BACKWARD', 'FORWARD')),
    last_fetched_open_time_ms INTEGER NOT NULL,
    last_page_candle_count INTEGER NOT NULL,
    earliest_open_time_ms INTEGER NOT NULL,
    latest_open_time_ms INTEGER NOT NULL,
    is_exhausted INTEGER NOT NULL DEFAULT 0,
    updated_at_ms INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_hist_checkpoints_job 
    ON historical_collection_checkpoints(job_id);


-- Table 3: dataset_manifests
-- Reproducible manifests storing schema versions, file paths, and SHA-256 hashes
CREATE TABLE IF NOT EXISTS dataset_manifests (
    manifest_id TEXT PRIMARY KEY,
    dataset_name TEXT NOT NULL,
    dataset_version TEXT NOT NULL,
    feature_version TEXT NOT NULL,
    exchange TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    start_time_ms INTEGER NOT NULL,
    end_time_ms INTEGER NOT NULL,
    candle_count INTEGER NOT NULL,
    raw_parquet_path TEXT NOT NULL,
    canonical_parquet_path TEXT NOT NULL,
    feature_parquet_path TEXT,
    file_sha256 TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    created_at_ms INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_manifests_lookup 
    ON dataset_manifests(exchange, symbol, timeframe, dataset_version);


-- Table 4: data_quality_reports
-- Audit reports detailing gaps, duplicates, invalid OHLC, and coverage metrics
CREATE TABLE IF NOT EXISTS data_quality_reports (
    report_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    exchange TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    requested_start_ms INTEGER NOT NULL,
    requested_end_ms INTEGER NOT NULL,
    actual_start_ms INTEGER NOT NULL,
    actual_end_ms INTEGER NOT NULL,
    expected_count INTEGER NOT NULL,
    observed_count INTEGER NOT NULL,
    missing_count INTEGER NOT NULL,
    duplicate_count INTEGER NOT NULL,
    conflicting_duplicate_count INTEGER NOT NULL,
    invalid_ohlc_count INTEGER NOT NULL,
    incomplete_candle_count INTEGER NOT NULL,
    coverage_pct REAL NOT NULL,
    validation_status TEXT NOT NULL CHECK (validation_status IN ('PASS', 'PASS_WITH_WARNINGS', 'FAIL', 'INSUFFICIENT_HISTORY')),
    feature_version TEXT NOT NULL,
    dataset_version TEXT NOT NULL,
    details_json TEXT NOT NULL,
    created_at_ms INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_quality_reports_lookup 
    ON data_quality_reports(exchange, symbol, timeframe, run_id);
