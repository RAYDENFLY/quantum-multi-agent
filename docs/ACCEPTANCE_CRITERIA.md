# ACCEPTANCE_CRITERIA.md: System-Wide Verification & Sign-Off Gates (Local ML Edition)

## 1. Master Acceptance Gate Overview

**QUANTUM: Multi-Agent Trading Desk** is considered architecturally complete and ready for production paper trading only when **100% of the gates below pass** across functional, quantitative, local ML, resource, safety, and UI craftsmanship dimensions.

All numerical performance criteria are classified as formal **Acceptance Targets** and must be verified against the standardized benchmark protocol on the designated low-resource reference hardware profile (4 cores, 12 GB RAM, mechanical SATA HDD, Windows 10/11 x64).

---

## 2. Gate 1: Zero Paid AI Cost, Safety & Paper-Only Isolation

- [ ] **AC-1.1 (Zero Paid AI / Cloud Inference Dependency)**: Codebase contains zero paid AI SDKs, zero cloud inference HTTP calls, zero paid API keys, and zero recurring operating costs. All 5 agents execute 100% locally on the user's CPU.
- [ ] **AC-1.2 (Zero Live Execution Code)**: Codebase contains zero endpoints, methods, or UI controls for placing live exchange orders, signing Web3 EIP-712 transactions, or initiating withdrawals on Bybit or AsterDEX.
- [ ] **AC-1.3 (Unauthenticated Public Market Data)**: Both `BybitAdapter` and `AsterDexAdapter` operate 100% on free public market data endpoints without requiring user exchange API keys.

---

## 3. Gate 2: Hardware & Performance Footprint (Low-Resource Profile Verification)

- [ ] **AC-2.1 (Desktop Runtime Idle RAM Target)**: Main desktop application RSS memory after startup, SQLite WAL initialization, loading 4 resident `LightGBM` boosters + calibrators, and loading all 7 workspace shells is **`<= 300 MB`** (Acceptance Target: `~205 - 240 MB` on 12 GB RAM system).
- [ ] **AC-2.2 (Sustained Active Runtime RAM Bound)**: During active 60s full-universe scanning (~850 contracts), 25 live WebSocket streams, live CPU ML inference, and 3 active paper positions over a 60-minute soak test, desktop runtime RSS memory remains **`<= 340 MB`** with zero unbounded growth (`< 1 MB/hour` drift after warmup).
- [ ] **AC-2.3 (Isolated Offline Training Subprocess Bound on HDD)**: Running `python -m quantum.ml.train_worker` executes in a separate low-priority subprocess (`BELOW_NORMAL_PRIORITY_CLASS`, `IOPRIO_LOW`) with RAM ceiling **`<= 550 MB`**, training one model at a time with sequential buffered `.npz` I/O. Must release 100% of its memory upon exit without inducing HDD thrashing, UI frame drops, or blocking the SQLite WAL writer.
- [ ] **AC-2.4 (CPU Inference Latency & UI Responsiveness)**: Full 4-agent local CPU ML inference per candidate completes in **`< 5.0 ms` (P95)** over 1,000 repetitions following the benchmark reproducibility protocol (`num_threads=1`), and main Qt event loop block time remains **`< 12 ms` (P99)**.
- [ ] **AC-2.5 (Bounded Disk Footprint)**: Rotating log files are strictly capped at `50 MB` (`5 x 10 MB`), and automated SQLite snapshot pruning keeps unreferenced raw snapshots bounded to a 14-day rolling window.

---

## 4. Gate 3: Exchange Integration & Dynamic Market Discovery

- [ ] **AC-3.1 (Dual-Exchange Universe Discovery)**: Stage A dynamically discovers all active USDT-margined linear perpetual contracts on both **Bybit** and **AsterDEX** without relying on a hardcoded watchlist.
- [ ] **AC-3.2 (Normalized Adapter Boundary)**: All upstream modules consume only `InstrumentMeta`, `NormalizedTicker`, `NormalizedOrderBook`, and `CANDLE_DTYPE` NumPy arrays; zero exchange-specific JSON keys leak outside `src/quantum/exchanges/`.
- [ ] **AC-3.3 (Bidirectional 7-Bucket Classification)**: Stage C classifies opportunities across all 7 required categories (`Top Gainers`, `Top Losers`, `Volume Surge`, `Momentum Acceleration`, `Volatility Expansion`, `Reversal Candidates`, `Breakout Candidates`) and assigns both `LONG` and `SHORT` biases based on market structure.
- [ ] **AC-3.4 (Anti-Duplication & Stale Suppression)**: Stage D enforces SHA-256 `state_hash` deduplication (15m window), per-symbol cooldowns (15m after `SKIP`), and hard 30s candidate TTL expiration before invoking `SCOUT`.

---

## 5. Gate 4: Five-Agent Local ML Pipeline, Anti-Leakage & Deterministic Risk Veto

- [ ] **AC-4.1 (Zero Train/Serve Skew & Zero Data Leakage)**: Both live inference and offline training call the exact same causal `extract_feature_vector()` function (`48 float32` scale-invariant features), verified by automated future-bar mutation tests (`tests/unit/test_features_leakage.py`) and dynamically purged chronological walk-forward splits ($\text{PurgeDuration} = 1.5 \times (H_{\max} + \text{MaxEntryDelay})$, Embargo $= 0.5 \times H_{\max}$).
- [ ] **AC-4.2 (Strict Contract Validation & Fail-Safe `SKIP`)**: Any `NaN`/`Inf` feature, schema hash mismatch, corrupted model checksum, or timeout (`> 50ms`) defaults immediately to **`SKIP`** (or explicit `FALLBACK_RULE_ONLY` on cold start).
- [ ] **AC-4.3 (Deterministic Price Geometry in `SNIPER`)**: `SNIPER` never predicts raw price numbers directly; all proposed `entry_price`, `stop_loss`, `take_profit_1`, and `take_profit_2` levels are derived deterministically from `mark_price`, `ANALYST.invalidation_price`, and `ATR_15m` rounded to `tick_size`.
- [ ] **AC-4.4 (Deterministic Risk Engine Veto Authority)**: Agent 4 (`RiskEngine`) is 100% deterministic Python and enforces all 12 hard checks (signal freshness, drawdown breaker, daily loss limit, loss-streak cooldown, max concurrent positions, stop geometry, spread cap, min notional/lot step, L2 book slippage cap, net $R:R \ge 1.80$ after fees/slippage, exposure/leverage caps, and liquidation buffer). No ML prediction can override a Risk veto.
- [ ] **AC-4.5 (Validation-Only Threshold Tuning & Out-of-Sample Promotion Gate)**: All decision thresholds ($\tau_{\text{scout}}$, $\tau_{\text{analyst}}$, $\tau_{\text{EV}}$) must be tuned exclusively on validation folds with minimum trade coverage constraints ($N_{\text{trades}} \ge 50$), and frozen prior to OOS testing. A trained model is promoted to `PRODUCTION` in `model_registry` only if its walk-forward out-of-sample Net Expectancy ($E_R$) and Profit Factor exceed the deterministic `RULE_ONLY` baseline after realistic fees, spread, and slippage.

---

## 6. Gate 5: Realistic Paper Execution & Accounting Integrity

- [ ] **AC-5.1 (L2 Orderbook Slippage, Spread & Collision Modeling)**: Market and triggered stop-market orders walk the live L2 orderbook plus latency buffer; limit orders require trade-through or simulated L1 queue depletion. Same-candle TP/SL collisions are resolved via 1-minute drill-down or pessimistic SL tie-break, and gap-through executions fill at worse open price to match training label semantics.
- [ ] **AC-5.2 (Full Fee & Funding Ledger)**: Maker/taker fees are deducted on every execution fill, and perpetual funding payments are settled accurately at each contract's `next_funding_time_ms` into `funding_events`.
- [ ] **AC-5.3 (Atomic Audit Trail & Crash Recovery)**: Every order, fill, position update, and equity snapshot commits atomically in SQLite WAL mode and rehydrates accurately upon application restart.

---

## 7. Gate 6: Multi-Agent Ablation & Trade Frequency Verification

- [ ] **AC-6.1 (5-Tier Ablation Benchmark Pass)**: System must evaluate all 5 pipeline tiers (`RULE_ONLY`, `SCOUT_ONLY`, `SCOUT_ANALYST`, `SCOUT_ANALYST_SNIPER`, `QUANTUM_5_AGENT`) on validation and OOS datasets.
- [ ] **AC-6.2 (Trade Coverage Preservation)**: Adding upstream ranking agents (`SCOUT`, `ANALYST`) must not reduce monthly trade frequency below 15 qualifying proposals per month, ensuring the desk maintains sufficient statistical opportunity sample size.
- [ ] **AC-6.3 (Rejection Reason Pareto Tracking)**: The system logs and displays exact Pareto distributions of all candidate rejection reasons across the entire pipeline.

---

## 8. Gate 7: Desktop UI & Anti-Slop Craftsmanship Compliance

- [ ] **AC-7.1 (All 7 Workspaces Functional)**: `Overview`, `Market Scanner`, `Agents` (Model Registry & Training Controls), `Market`, `Positions`, `Analytics`, and `Settings` are fully navigable via mouse and keyboard (`Alt+1..7`, `Tab`, `Escape`) with visible `#22D3EE` focus rings (`R-32`).
- [ ] **AC-7.2 (WCAG AA Contrast Verified)**: Every text and interactive border token in `UI_DESIGN_SYSTEM.md` meets or exceeds `4.5:1` for normal text and `3.0:1` for non-text boundaries (`R-25`), with non-color prefix symbols (`+`, `-`, `▲ LONG`, `▼ SHORT`) on all semantic indicators.
- [ ] **AC-7.3 (Complete Empty, Loading & Error States)**: Every table, chart, and model inspector renders informative Empty, Loading, and Error states naming the cause and next action (`R-27`).
- [ ] **AC-7.4 (Zero Dead Controls or Fabricated Numbers)**: Every button, filter, and toggle performs a real bound action (`R-26`), and every displayed metric is computed from real exchange data, real model evaluations, or real SQLite paper ledger records (`R-17`, `R-36`, `R-38`).
