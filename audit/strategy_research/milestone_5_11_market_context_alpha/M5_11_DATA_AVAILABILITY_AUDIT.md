# QUANTUM — MILESTONE 5.11
## DATA AVAILABILITY, PROVENANCE & EXOGENOUS FEEDS AUDIT

---

### 1. EXECUTIVE SUMMARY

- **Milestone Designation:** Milestone 5.11 (Multi-Factor Market Context & Causal Alpha Discovery)
- **Git Branch:** `research/quantum-next-3pct`
- **Location:** `audit/strategy_research/milestone_5_11_market_context_alpha/M5_11_DATA_AVAILABILITY_AUDIT.md`
- **Objective:** Audit the availability, resolution, and empirical reality of all data inputs across the six research dimensions, formalizing what is verified present versus what is strictly `DATA_UNAVAILABLE`.
- **Primary Governance Finding:**
  - **Verified Present:** Canonical 5-minute OHLCV data for the 10 primary assets ($316,500$ bars each, $1,098.96\text{ days}$).
  - **Strictly Unavailable:** 1-minute execution bars, L2 orderbook tick queues, historical perpetual funding rate series, open interest feeds, liquidation logs, and macroeconomic announcement feeds.
  - **Non-Fabrication Invariant:** Under zero circumstances may unavailable feeds be synthetically simulated or fabricated. All unavailable dimensions are formally tagged `DATA_UNAVAILABLE`.

---

### 2. DATA AVAILABILITY STATUS MATRIX ACROSS THE SIX DIMENSIONS

```
+-------------------------------------------------------------------------------------------------------------------------------+
| MULTI-FACTOR DATA AVAILABILITY AUDIT                                                                                          |
+----+--------------------------------+-----------------+---------------+-----------------------+-------------------------------+
| Dim| Information Domain             | Resolution      | Source        | Empirical Status      | Scientific Governance Action  |
+----+--------------------------------+-----------------+---------------+-----------------------+-------------------------------+
| A  | OHLCV Market Structure         | 5m canonical    | Aster DEX     | FULLY AVAILABLE       | Verified 316,500 bars / asset |
| A  | 1-Minute Structural Bars       | 1m              | N/A           | DATA_UNAVAILABLE      | BANNED (No synthetic bars)    |
| B  | Momentum & Trend Indicators    | 5m, 15m, 1h     | Derived       | FULLY AVAILABLE       | Derived causally from OHLCV   |
| C  | Volatility & Regime States     | 5m derived      | Derived       | FULLY AVAILABLE       | Derived causally from OHLCV   |
| D  | Volume & Liquidity Proxies     | 5m volume/quote | Aster DEX     | FULLY AVAILABLE (PROX)| Labeled as OHLCV proxies only |
| D  | L2 Orderbook Queue Depth       | Tick-level      | N/A           | DATA_UNAVAILABLE      | BANNED from claiming L2 depth |
| E  | Cross-Asset Synchronized Panel | 5m multi-asset  | Aster DEX     | FULLY AVAILABLE       | Synchronized on open_time_ms  |
| F  | Historical Funding Rates       | 8-hour          | SQLite DB     | DATA_UNAVAILABLE      | 0 rows in DB; Stress testing  |
| F  | Open Interest Timeseries       | Periodic        | N/A           | DATA_UNAVAILABLE      | Pluggable interface only      |
| F  | Liquidation Tape Feeds         | Event-driven    | N/A           | DATA_UNAVAILABLE      | Pluggable interface only      |
| F  | Macroeconomic Announcements    | Event-driven    | N/A           | DATA_UNAVAILABLE      | Pluggable interface only      |
+----+--------------------------------+-----------------+---------------+-----------------------+-------------------------------+
```

---

### 3. EXHAUSTIVE DATA DIMENSION FINDINGS

#### 3.1 1-Minute Timeframe Status
- The QUANTUM Research Charter specifies that 5m is the mandatory baseline execution timeframe, with 1m permitted only if reliable data exists.
- **Audit Result:** Canonical parquet archives at `data/historical/canonical/exchange=ASTER/` contain exclusively 5m partitions. No canonical 1m partitions exist on disk.
- **Enforcement:** Ingesting downsampled or synthetically split 1m candles into the research engine is strictly prohibited. The system operates 100% on genuine 5m canonical candles.

#### 3.2 Volume vs Orderbook Depth Reality
- Volume features (`rvol_20`, `volume_zscore_50`, `amihud_illiquidity`, `effort_vs_result_ratio`) are computed from bar-level volume and turnover.
- **Audit Result:** These metrics represent aggregate trading activity over 5-minute intervals. They do **not** reveal resting limit order book depth, queue priority, cancellation ratios, or informed versus uninformed flow.
- **Enforcement:** Research documentation and agent prompts must never label volume proxies as "orderbook depth" or "institutional order flow measurements."

#### 3.3 Historical Funding Rate Gap
- In Milestone 5.10B, inspection of `data/historical/historical.db` confirmed that `SELECT count(*) FROM funding_events` returned exactly `0`.
- **Audit Result:** Historical funding payments across the 3-year backtest are unavailable in local stores.
- **Enforcement:** In compliance with Milestone 5.10A/5.10B contract rules, historical funding is tagged `DATA_UNAVAILABLE`. Rather than assuming zero funding, strategies are subjected to parametric sensitivity bounds ($[-5.0, +5.0]\text{ bps}/8\text{h}$) to evaluate carry drag robustness.

#### 3.4 Exogenous Feeds (Open Interest, Liquidations, Macro News)
- `ExogenousEventInterface` in [`src/quantum/features/market_context.py`](file:///d:/quantum-multi-agent/src/quantum/features/market_context.py#L368-L387) provides a standardized pluggable contract.
- In historical backtests, all methods return `status = "DATA_UNAVAILABLE"`.
- When live market connectivity is enabled in future phases, this interface will ingest live websocket liquidation streams without requiring modifications to the core strategy engine.

---

### 4. CANONICAL ASSET COVERAGE & PARTIAL DATA QUARANTINE

- **Primary 10 Assets (Full 3-Year Continuous History):**
  - BTCUSDT ($316,499$ bars; $1$ single missing bar isolated at $2025-09-13\text{ 13:50:00 UTC}$).
  - ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, ADAUSDT, AVAXUSDT, LINKUSDT, DOGEUSDT, LTCUSDT ($316,500$ bars each).
- **Quarantined Asset (XMRUSDT):**
  - Contains only $83,863$ bars ($291.19\text{ days}$) spanning $2026-01-13$ to $2026-10-31$.
  - Formally excluded from the primary portfolio backtest.

---

### 5. SEALED HOLDOUT PARTITION RE-VERIFICATION

- Prospective holdout boundary: `1,793,491,200,000 ms` ($2026-11-01\text{ 00:00:00 UTC}$).
- Maximum timestamp across all canonical files: `1,793,481,900,000 ms` ($2026-10-31\text{ 21:25:00 UTC}$).
- **Status:** Virgin. Zero contamination or leakage has occurred.
