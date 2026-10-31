-- 001_initial.sql: QUANTUM Master Schema (18 Tables)
-- Compliant with docs/DATABASE_SCHEMA.md

-- 1. Schema Migrations Tracking
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at_ms INTEGER NOT NULL
);

-- 2. Exchange Instruments Metadata
CREATE TABLE IF NOT EXISTS exchange_instruments (
    instrument_id TEXT PRIMARY KEY,          -- 'BYBIT:BTCUSDT' or 'ASTER:BTCUSDT'
    exchange TEXT NOT NULL CHECK (exchange IN ('BYBIT', 'ASTER')),
    symbol TEXT NOT NULL,
    base_asset TEXT NOT NULL,
    quote_asset TEXT NOT NULL DEFAULT 'USDT',
    status TEXT NOT NULL,                    -- 'TRADING', 'HALTED', 'SETTLING'
    tick_size REAL NOT NULL,
    lot_step REAL NOT NULL,
    min_order_qty REAL NOT NULL,
    max_order_qty REAL NOT NULL,
    min_notional_usdt REAL NOT NULL,
    max_leverage REAL NOT NULL,
    maker_fee_rate REAL NOT NULL,
    taker_fee_rate REAL NOT NULL,
    onboard_timestamp_ms INTEGER NOT NULL,
    updated_at_ms INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_instruments_exchange_status ON exchange_instruments(exchange, status);

-- 3. Market Snapshots & Extracted Feature Vectors
CREATE TABLE IF NOT EXISTS market_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    instrument_id TEXT NOT NULL REFERENCES exchange_instruments(instrument_id),
    timestamp_ms INTEGER NOT NULL,
    last_price REAL NOT NULL,
    mark_price REAL NOT NULL,
    index_price REAL NOT NULL,
    bid1_price REAL NOT NULL,
    ask1_price REAL NOT NULL,
    spread_bps REAL NOT NULL,
    turnover_24h_usdt REAL NOT NULL,
    price_change_24h_pct REAL NOT NULL,
    funding_rate REAL NOT NULL,
    next_funding_time_ms INTEGER NOT NULL,
    atr_15m REAL,
    atr_1h REAL,
    rvol_15m REAL,
    rsi_15m REAL,
    feature_schema_version TEXT NOT NULL,    -- e.g. 'FEATURE_SCHEMA_V1'
    features_json TEXT NOT NULL              -- Serialized 48-element float32 feature dictionary
);
CREATE INDEX IF NOT EXISTS idx_snapshots_instrument_ts ON market_snapshots(instrument_id, timestamp_ms DESC);

-- 4. Scanner Candidates (Stage C/D output)
CREATE TABLE IF NOT EXISTS scanner_candidates (
    candidate_id TEXT PRIMARY KEY,
    scan_cycle_id TEXT NOT NULL,
    instrument_id TEXT NOT NULL REFERENCES exchange_instruments(instrument_id),
    snapshot_id TEXT NOT NULL REFERENCES market_snapshots(snapshot_id),
    exchange TEXT NOT NULL,
    symbol TEXT NOT NULL,
    primary_category TEXT NOT NULL,          -- 'TOP_GAINERS', 'BREAKOUT_CANDIDATES', etc.
    secondary_categories_json TEXT NOT NULL, -- JSON array
    directional_bias TEXT NOT NULL CHECK (directional_bias IN ('LONG', 'SHORT')),
    deterministic_score REAL NOT NULL,
    state_hash TEXT NOT NULL,
    queue_status TEXT NOT NULL,              -- 'QUEUED', 'DISPATCHED', 'DEDUP', 'EXPIRED', 'COOLDOWN'
    created_at_ms INTEGER NOT NULL,
    expires_at_ms INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_candidates_created ON scanner_candidates(created_at_ms DESC);
CREATE INDEX IF NOT EXISTS idx_candidates_state_hash ON scanner_candidates(state_hash, created_at_ms DESC);

-- 5. Offline Model Training Runs
CREATE TABLE IF NOT EXISTS training_runs (
    training_run_id TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL CHECK (agent_name IN ('SCOUT', 'ANALYST', 'SNIPER', 'BANKER')),
    algorithm TEXT NOT NULL,                 -- 'LightGBM_Isotonic', 'Regime_LightGBM', etc.
    feature_schema_hash TEXT NOT NULL,
    train_start_ms INTEGER NOT NULL,
    train_end_ms INTEGER NOT NULL,
    val_start_ms INTEGER NOT NULL,
    val_end_ms INTEGER NOT NULL,
    oos_start_ms INTEGER NOT NULL,
    oos_end_ms INTEGER NOT NULL,
    sample_count INTEGER NOT NULL,
    hyperparameters_json TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('RUNNING', 'COMPLETED', 'FAILED', 'ABORTED')),
    duration_seconds REAL,
    peak_ram_mb REAL,
    started_at_ms INTEGER NOT NULL,
    completed_at_ms INTEGER
);
CREATE INDEX IF NOT EXISTS idx_training_runs_agent ON training_runs(agent_name, started_at_ms DESC);

-- 6. Local Model Registry & Versioning
CREATE TABLE IF NOT EXISTS model_registry (
    model_version TEXT PRIMARY KEY,          -- e.g. 'scout_lgbm_v1.0.2'
    training_run_id TEXT NOT NULL REFERENCES training_runs(training_run_id),
    agent_name TEXT NOT NULL CHECK (agent_name IN ('SCOUT', 'ANALYST', 'SNIPER', 'BANKER')),
    algorithm TEXT NOT NULL,
    feature_schema_hash TEXT NOT NULL,
    artifact_dir_path TEXT NOT NULL,
    artifact_sha256 TEXT NOT NULL,
    decision_threshold REAL NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('CANDIDATE', 'PRODUCTION', 'ARCHIVED', 'REJECTED')),
    feature_importance_json TEXT NOT NULL,   -- Top features by gain/split
    drift_psi_score REAL NOT NULL DEFAULT 0.0,
    promoted_at_ms INTEGER,
    created_at_ms INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_model_registry_active ON model_registry(agent_name, status);

-- 7. Walk-Forward & Out-of-Sample Model Evaluations
CREATE TABLE IF NOT EXISTS model_evaluations (
    eval_id TEXT PRIMARY KEY,
    model_version TEXT NOT NULL REFERENCES model_registry(model_version) ON DELETE CASCADE,
    eval_split TEXT NOT NULL CHECK (eval_split IN ('VALIDATION', 'OOS_TEST', 'LIVE_PAPER_ROLLING')),
    baseline_compared TEXT NOT NULL,         -- 'RULE_ONLY', 'SINGLE_ML_MODEL', 'PRIOR_PROD'
    sample_trades INTEGER NOT NULL,
    roc_auc REAL,
    pr_auc REAL,
    brier_score REAL,                        -- Calibration accuracy (lower is better)
    log_loss REAL,
    net_expectancy_r REAL NOT NULL,
    baseline_expectancy_r REAL NOT NULL,
    net_profit_factor REAL NOT NULL,
    max_drawdown_pct REAL NOT NULL,
    win_rate_pct REAL NOT NULL,
    passed_promotion_gate INTEGER NOT NULL,  -- Boolean 0/1
    evaluated_at_ms INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_model_evals_version ON model_evaluations(model_version, evaluated_at_ms DESC);

-- 8. Agent Pipeline Runs
CREATE TABLE IF NOT EXISTS agent_runs (
    pipeline_run_id TEXT PRIMARY KEY,
    candidate_id TEXT REFERENCES scanner_candidates(candidate_id),
    instrument_id TEXT NOT NULL REFERENCES exchange_instruments(instrument_id),
    snapshot_id TEXT NOT NULL REFERENCES market_snapshots(snapshot_id),
    run_type TEXT NOT NULL CHECK (run_type IN ('DISCOVERY_PIPELINE', 'BANKER_HAZARD_CHECK')),
    status TEXT NOT NULL,                    -- 'APPROVED', 'SKIP_SCOUT', 'SKIP_ANALYST', 'SKIP_SNIPER', 'VETO_RISK', 'SKIP_FEATURE_INVALID'
    final_stage_reached TEXT NOT NULL,
    total_inference_latency_ms REAL NOT NULL DEFAULT 0.0,
    abort_reason TEXT,
    started_at_ms INTEGER NOT NULL,
    completed_at_ms INTEGER
);
CREATE INDEX IF NOT EXISTS idx_agent_runs_started ON agent_runs(started_at_ms DESC);
CREATE INDEX IF NOT EXISTS idx_agent_runs_status ON agent_runs(status);

-- 9. Individual Agent Inference Records
CREATE TABLE IF NOT EXISTS agent_messages (
    message_id TEXT PRIMARY KEY,
    pipeline_run_id TEXT NOT NULL REFERENCES agent_runs(pipeline_run_id) ON DELETE CASCADE,
    agent_name TEXT NOT NULL CHECK (agent_name IN ('SCOUT', 'ANALYST', 'SNIPER', 'RISK', 'BANKER')),
    model_version TEXT NOT NULL,             -- e.g. 'scout_lgbm_v1.0.2' or 'FALLBACK_RULE_ONLY'
    inference_mode TEXT NOT NULL CHECK (inference_mode IN ('LOCAL_ML', 'FALLBACK_RULE_ONLY', 'DETERMINISTIC_PYTHON')),
    action_taken TEXT NOT NULL,              -- 'PROCEED', 'SKIP', 'PROPOSE_TRADE', 'APPROVED', 'REJECTED'
    raw_score REAL,
    calibrated_probability REAL,
    latency_ms REAL NOT NULL,
    top_features_json TEXT NOT NULL,
    output_json TEXT NOT NULL,
    error_message TEXT,
    created_at_ms INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_agent_messages_run ON agent_messages(pipeline_run_id, created_at_ms ASC);
CREATE INDEX IF NOT EXISTS idx_agent_messages_agent ON agent_messages(agent_name, created_at_ms DESC);

-- 10. Trade Proposals (Generated by SNIPER)
CREATE TABLE IF NOT EXISTS trade_proposals (
    proposal_id TEXT PRIMARY KEY,
    pipeline_run_id TEXT NOT NULL UNIQUE REFERENCES agent_runs(pipeline_run_id),
    instrument_id TEXT NOT NULL REFERENCES exchange_instruments(instrument_id),
    snapshot_id TEXT NOT NULL REFERENCES market_snapshots(snapshot_id),
    exchange TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('LONG', 'SHORT')),
    order_type TEXT NOT NULL CHECK (order_type IN ('MARKET', 'LIMIT')),
    reference_mark_price REAL NOT NULL,
    entry_price REAL NOT NULL,
    entry_zone_low REAL NOT NULL,
    entry_zone_high REAL NOT NULL,
    stop_loss REAL NOT NULL,
    take_profit_1 REAL NOT NULL,
    take_profit_2 REAL NOT NULL,
    tp1_close_pct REAL NOT NULL,
    estimated_reward_risk REAL NOT NULL,
    expected_net_r REAL NOT NULL,
    prob_tp1_before_sl REAL NOT NULL,
    prob_tp2_before_sl REAL NOT NULL,
    expected_holding_minutes INTEGER NOT NULL,
    confidence REAL NOT NULL,
    rationale TEXT NOT NULL,
    market_regime TEXT NOT NULL,
    invalidation_price REAL NOT NULL,
    sniper_model_version TEXT NOT NULL,
    created_at_ms INTEGER NOT NULL
);

-- 11. Risk Engine Decisions (Deterministic Agent 4)
CREATE TABLE IF NOT EXISTS risk_decisions (
    decision_id TEXT PRIMARY KEY,
    proposal_id TEXT NOT NULL UNIQUE REFERENCES trade_proposals(proposal_id),
    pipeline_run_id TEXT NOT NULL REFERENCES agent_runs(pipeline_run_id),
    decision TEXT NOT NULL CHECK (decision IN ('APPROVED', 'REJECTED')),
    approved_quantity REAL NOT NULL DEFAULT 0.0,
    notional_usdt REAL NOT NULL DEFAULT 0.0,
    effective_leverage REAL NOT NULL DEFAULT 0.0,
    risk_amount_usdt REAL NOT NULL DEFAULT 0.0,
    risk_pct_of_equity REAL NOT NULL DEFAULT 0.0,
    net_reward_risk REAL NOT NULL DEFAULT 0.0,
    estimated_fee_usdt REAL NOT NULL DEFAULT 0.0,
    estimated_slippage_bps REAL NOT NULL DEFAULT 0.0,
    equity_at_eval_usdt REAL NOT NULL,
    checks_passed_json TEXT NOT NULL,
    veto_reasons_json TEXT NOT NULL,
    evaluated_at_ms INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_risk_decisions_eval ON risk_decisions(evaluated_at_ms DESC);

-- 12. Paper Positions
CREATE TABLE IF NOT EXISTS positions (
    position_id TEXT PRIMARY KEY,
    proposal_id TEXT NOT NULL REFERENCES trade_proposals(proposal_id),
    decision_id TEXT NOT NULL REFERENCES risk_decisions(decision_id),
    instrument_id TEXT NOT NULL REFERENCES exchange_instruments(instrument_id),
    exchange TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('LONG', 'SHORT')),
    status TEXT NOT NULL CHECK (status IN ('OPEN', 'CLOSED')),
    leverage REAL NOT NULL,
    initial_quantity REAL NOT NULL,
    open_quantity REAL NOT NULL,
    avg_entry_price REAL NOT NULL,
    avg_exit_price REAL,
    last_mark_price REAL NOT NULL,
    initial_stop_loss REAL NOT NULL,
    current_stop_loss REAL NOT NULL,
    take_profit_1 REAL NOT NULL,
    take_profit_2 REAL NOT NULL,
    tp1_filled INTEGER NOT NULL DEFAULT 0,
    initial_risk_usdt REAL NOT NULL,
    allocated_margin_usdt REAL NOT NULL,
    unrealized_pnl_usdt REAL NOT NULL DEFAULT 0.0,
    realized_gross_pnl_usdt REAL NOT NULL DEFAULT 0.0,
    total_fees_usdt REAL NOT NULL DEFAULT 0.0,
    total_funding_usdt REAL NOT NULL DEFAULT 0.0,
    realized_net_pnl_usdt REAL NOT NULL DEFAULT 0.0,
    mfe_usdt REAL NOT NULL DEFAULT 0.0,
    mae_usdt REAL NOT NULL DEFAULT 0.0,
    exit_reason TEXT,
    opened_at_ms INTEGER NOT NULL,
    closed_at_ms INTEGER
);
CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status, opened_at_ms DESC);
CREATE INDEX IF NOT EXISTS idx_positions_instrument ON positions(instrument_id, status);

-- 13. Paper Orders
CREATE TABLE IF NOT EXISTS paper_orders (
    order_id TEXT PRIMARY KEY,
    client_order_id TEXT NOT NULL UNIQUE,
    position_id TEXT REFERENCES positions(position_id),
    decision_id TEXT REFERENCES risk_decisions(decision_id),
    instrument_id TEXT NOT NULL REFERENCES exchange_instruments(instrument_id),
    order_purpose TEXT NOT NULL CHECK (order_purpose IN ('ENTRY', 'STOP_LOSS', 'TAKE_PROFIT_1', 'TAKE_PROFIT_2', 'TRAILING_STOP', 'EMERGENCY_EXIT')),
    side TEXT NOT NULL CHECK (side IN ('BUY', 'SELL')),
    order_type TEXT NOT NULL CHECK (order_type IN ('MARKET', 'LIMIT', 'STOP_MARKET')),
    reduce_only INTEGER NOT NULL DEFAULT 0,
    limit_price REAL,
    stop_trigger_price REAL,
    requested_qty REAL NOT NULL,
    filled_qty REAL NOT NULL DEFAULT 0.0,
    avg_fill_price REAL,
    status TEXT NOT NULL CHECK (status IN ('OPEN', 'PARTIALLY_FILLED', 'FILLED', 'CANCELLED', 'EXPIRED')),
    cancel_reason TEXT,
    created_at_ms INTEGER NOT NULL,
    updated_at_ms INTEGER NOT NULL,
    expires_at_ms INTEGER
);
CREATE INDEX IF NOT EXISTS idx_orders_status ON paper_orders(status, instrument_id);
CREATE INDEX IF NOT EXISTS idx_orders_position ON paper_orders(position_id);

-- 14. Simulated Order Executions (Fills)
CREATE TABLE IF NOT EXISTS executions (
    execution_id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL REFERENCES paper_orders(order_id),
    position_id TEXT NOT NULL REFERENCES positions(position_id),
    instrument_id TEXT NOT NULL REFERENCES exchange_instruments(instrument_id),
    side TEXT NOT NULL CHECK (side IN ('BUY', 'SELL')),
    liquidity_role TEXT NOT NULL CHECK (liquidity_role IN ('MAKER', 'TAKER')),
    fill_qty REAL NOT NULL,
    reference_mid_price REAL NOT NULL,
    reference_mark_price REAL NOT NULL,
    fill_price REAL NOT NULL,
    spread_cost_bps REAL NOT NULL,
    slippage_bps REAL NOT NULL,
    fee_rate REAL NOT NULL,
    fee_usdt REAL NOT NULL,
    realized_pnl_delta_usdt REAL NOT NULL DEFAULT 0.0,
    executed_at_ms INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_executions_position ON executions(position_id, executed_at_ms ASC);

-- 15. Funding Settlement Events
CREATE TABLE IF NOT EXISTS funding_events (
    funding_event_id TEXT PRIMARY KEY,
    position_id TEXT NOT NULL REFERENCES positions(position_id),
    instrument_id TEXT NOT NULL REFERENCES exchange_instruments(instrument_id),
    position_side TEXT NOT NULL,
    open_quantity REAL NOT NULL,
    mark_price REAL NOT NULL,
    notional_usdt REAL NOT NULL,
    funding_rate REAL NOT NULL,
    cashflow_usdt REAL NOT NULL,
    settled_at_ms INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_funding_position ON funding_events(position_id, settled_at_ms ASC);

-- 16. Banker Quantitative Trade Journal
CREATE TABLE IF NOT EXISTS trade_journal (
    journal_id TEXT PRIMARY KEY,
    position_id TEXT NOT NULL UNIQUE REFERENCES positions(position_id),
    instrument_id TEXT NOT NULL,
    scanner_category TEXT NOT NULL,
    market_regime TEXT NOT NULL,
    side TEXT NOT NULL,
    model_bundle_summary TEXT NOT NULL,
    predicted_entry_prob REAL NOT NULL,
    predicted_expected_r REAL NOT NULL,
    realized_r_multiple REAL NOT NULL,
    realized_net_pnl_usdt REAL NOT NULL,
    mfe_r REAL NOT NULL,
    mae_r REAL NOT NULL,
    edge_ratio REAL NOT NULL,
    fee_and_slippage_drag_r REAL NOT NULL,
    funding_drag_r REAL NOT NULL,
    holding_duration_minutes REAL NOT NULL,
    exit_reason TEXT NOT NULL,
    quantitative_summary TEXT NOT NULL,
    created_at_ms INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_journal_created ON trade_journal(created_at_ms DESC);

-- 17. Equity & Performance Metrics Time-Series
CREATE TABLE IF NOT EXISTS performance_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_ms INTEGER NOT NULL,
    total_equity_usdt REAL NOT NULL,
    rule_baseline_equity_usdt REAL NOT NULL,
    available_balance_usdt REAL NOT NULL,
    used_margin_usdt REAL NOT NULL,
    unrealized_pnl_usdt REAL NOT NULL,
    cumulative_realized_net_pnl_usdt REAL NOT NULL,
    cumulative_fees_usdt REAL NOT NULL,
    cumulative_funding_usdt REAL NOT NULL,
    peak_equity_usdt REAL NOT NULL,
    drawdown_pct REAL NOT NULL,
    open_positions_count INTEGER NOT NULL,
    total_closed_trades INTEGER NOT NULL,
    win_rate_pct REAL NOT NULL,
    profit_factor REAL NOT NULL,
    expectancy_r REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_perf_metrics_ts ON performance_metrics(timestamp_ms ASC);

-- 18. Application Settings (Key-Value Store)
CREATE TABLE IF NOT EXISTS app_settings (
    setting_key TEXT PRIMARY KEY,
    setting_value_json TEXT NOT NULL,
    updated_at_ms INTEGER NOT NULL
);
