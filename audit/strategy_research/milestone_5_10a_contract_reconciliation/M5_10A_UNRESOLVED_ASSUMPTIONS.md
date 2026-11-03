# QUANTUM — MILESTONE 5.10A
## REGISTER OF OPEN UNCERTAINTIES & EXECUTION ASSUMPTIONS

---

### 1. EXECUTIVE SUMMARY

- **Milestone Designation:** Milestone 5.10A (Contract Enforcement & Configuration Reconciliation)
- **Git Branch:** `research/quantum-next-3pct`
- **Location:** `audit/strategy_research/milestone_5_10a_contract_reconciliation/M5_10A_UNRESOLVED_ASSUMPTIONS.md`
- **Purpose:** Document all residual structural assumptions, empirical data gaps, and execution simplifications present in the QUANTUM research platform. 
- **Governance Mandate:** Any research finding derived under these assumptions must explicitly cite this register and report parametric sensitivity bounds to prevent false confidence.

---

### 2. REGISTER OF OPEN ASSUMPTIONS

```
+-----------------------------------------------------------------------------------------------------------------------------+
| REGISTER OF OPEN RESEARCH ASSUMPTIONS & STRUCTURAL UNCERTAINTIES                                                            |
+-----+----------------------------+-----------------------+----------------------------------+-------------------------------+
| ID  | Assumption Domain          | Risk Level            | Baseline Parameter / Assumption  | Stress / Sensitivity Range    |
+-----+----------------------------+-----------------------+----------------------------------+-------------------------------+
| A01 | Historical Funding Rates   | High (Multi-Day/LF)   | Parametric sensitivity required  | [-5.0, +5.0] bps / 8h         |
| A02 | Limit Order Fill Priority  | Medium (HF Maker)     | Price penetration >= 1.0 bps     | 100% Taker Execution (10 bps) |
| A03 | Bid-Ask Spread Dynamics    | Medium (Intraday)     | Static 1.0 bps half-spread       | Widening to 3.0–5.0 bps       |
| A04 | Execution Slippage Model   | Medium (Intraday)     | Static 2.0 bps / leg             | Escalation to 5.0–10.0 bps    |
| A05 | 1m Timeframe Data Feeds    | Low (Charter Scope)   | 5m canonical active baseline     | Ingestion pending validation  |
+-----+----------------------------+-----------------------+----------------------------------+-------------------------------+
```

---

### 3. DETAILED ASSUMPTION ANALYSIS

#### 3.1 A01: Historical Funding Rate Data Gap
- **Nature of Uncertainty:** Crypto perpetual contracts levy or credit an 8-hour funding payment based on the premium/discount between the perpetual mark price and the spot index. The current canonical dataset contains 5m OHLCV bars but does not include historical funding rate timestamps.
- **Previous Violation in Track C:** In M5.9 and M5.9B, missing funding data was erroneously reported as "verified zero funding." This concealed potential carry drag across multi-day holding periods.
- **Contract Enforcement:**
  - In `ResearchExperimentContract`, `funding_data_availability` is set to `"DATA_UNAVAILABLE"`.
  - Claiming "VERIFIED_ZERO_FUNDING" raises `FundingDataUncertaintyError`.
  - For high-frequency intraday trading (holding horizon $15\text{m}–4\text{h}$ with no overnight positions), net funding impact is minimal since positions are rarely open during the 00:00, 08:00, or 16:00 UTC funding settlement timestamps.
  - If any position crosses an 8-hour boundary, Banker PnL calculations must report sensitivity bounds across $[-5.0, +5.0]\text{ bps}/8\text{h}$.

#### 3.2 A02: Microstructure Limit Order Queue Priority
- **Nature of Uncertainty:** In bar-level discrete backtests (5m candles), exact intra-bar orderbook depth and queue priority cannot be observed without L2 tick-by-tick message feeds.
- **Risk:** Assuming that a limit order placed at the inside bid/ask is automatically filled when price touches that level introduces severe optimistic fill bias.
- **Remediation & Governance:**
  1. For conservative alpha validation, strategies should assume **taker execution** ($10.0\text{ bps}$ fee on Aster DEX).
  2. If maker execution is modeled ($4.0\text{ bps}$ fee), the backtester must require price penetration through the limit price by at least $1.0\text{ bps}$ before confirming an execution fill.

#### 3.3 A03 & A04: Dynamic Spread Widening & Slippage Surges
- **Nature of Uncertainty:** The baseline retail cost configuration models a static half-spread of $1.0\text{ bps}$ and static execution slippage of $2.0\text{ bps}$ per leg ($3.0\text{ bps}$ total friction per leg on top of fees).
- **Risk:** During high-volatility macro news releases, liquidity gaps, or decentralized network congestion on Aster DEX, spreads can blow out to $5.0–10.0\text{ bps}$ and market impact can double.
- **Remediation & Governance:**
  - All candidate alpha models passing the baseline profitability gate ($\ge 3.00\%$ daily net return) must undergo stress testing under **`ASTER_DEX_STRESS_CONFIG`** ($20.0\text{ bps}$ taker fee).
  - High-volatility periods must be flagged by the Risk Agent to temporarily widen slippage envelopes.

#### 3.4 A05: 1-Minute Execution Timeframe Availability
- **Nature of Uncertainty:** The QUANTUM Research Charter permits exploration of 1m execution timeframes if reliable data exists.
- **Current Status:** Aster DEX canonical data is verified and frozen at the 5m resolution ($316,500$ bars across 10 assets). 1m raw archives have not yet been downloaded, verified, or partitioned into canonical parquet stores.
- **Policy:** The 5m resolution is the single authoritative execution baseline for all immediate Phase 5.10 alpha research. Any transition to 1m requires an independent milestone data integrity audit.

---

### 4. CONCLUSION & RESEARCH SAFETY

By codifying these five assumptions into `ResearchExperimentContract` and maintaining explicit parameter checks, QUANTUM eliminates "hidden free lunches." Future alpha models will be evaluated strictly against real-world friction and transparent data constraints.
