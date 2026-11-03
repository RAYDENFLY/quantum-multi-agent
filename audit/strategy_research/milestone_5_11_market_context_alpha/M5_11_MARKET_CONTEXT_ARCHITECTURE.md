# QUANTUM — MILESTONE 5.11
## MULTI-FACTOR MARKET CONTEXT ARCHITECTURE

---

### 1. EXECUTIVE SUMMARY

- **Milestone Designation:** Milestone 5.11 (Multi-Factor Market Context & Causal Alpha Discovery)
- **Git Branch:** `research/quantum-next-3pct`
- **Location:** `audit/strategy_research/milestone_5_11_market_context_alpha/M5_11_MARKET_CONTEXT_ARCHITECTURE.md`
- **Objective:** Evolve QUANTUM beyond a conventional indicator-based system into a multi-factor market context engine that identifies, classifies, and evaluates trading opportunities across multiple independent information dimensions.
- **Architectural Paradigm Shift:**
  - **Legacy QUANTUM (Phases 3–5.6):** Relied on isolated heuristic indicators (e.g., single EMA crossovers, MACD histogram flips) executed without regime awareness, resulting in fee churn and silent drawdown.
  - **Modern Multi-Factor Engine (M5.11):** Integrates six independent dimensions (Market Structure, Momentum, Volatility Regime, Volume Proxies, Cross-Asset Context, Exogenous Events) to form testable, falsifiable market hypotheses evaluated against real-world AsterDEX friction.

---

### 2. THE SIX CORE EPISTEMOLOGICAL QUESTIONS

To prevent curve-fitting and the fabrication of false causal narratives, every trade proposal evaluated by QUANTUM must answer six mandatory questions:

```
+-----------------------------------------------------------------------------------------------------------------------+
| THE SIX CORE MARKET CONTEXT QUESTIONS                                                                                 |
+-----+---------------------------------------------+-------------------------------------------------------------------+
| No. | Question                                    | Engine Evaluation Dimension & Observable Metric                   |
+-----+---------------------------------------------+-------------------------------------------------------------------+
| 1   | What is happening in the market?            | Dimension A & D: Causal Swing breaks, FVGs, Displacement, RVOL    |
| 2   | Why is it happening?                        | Dimension A & E: Liquidity sweep of trapped stops, BTC dominance  |
| 3   | What conditions create the opportunity?     | Dimension C: Discrete 4-State Regime (HV_TREND, LV_RANGE, etc.)   |
| 4   | What is the probable next behavior?         | Dimension B & E: Trend persistence, relative strength divergence  |
| 5   | What evidence invalidates the hypothesis?   | Dimension A: Opposite swing breach, displacement cancellation     |
| 6   | Does it retain net expectancy after costs?  | Dimension C & F: AsterDEX Base Retail 26 bps round-trip hurdle    |
+-----+---------------------------------------------+-------------------------------------------------------------------+
```

---

### 3. THE SIX INFORMATION DIMENSIONS

```
+-----------------------------------------------------------------------------------------------------------------------+
| QUANTUM MULTI-FACTOR MARKET CONTEXT DIMENSIONS                                                                        |
+-----------------------------------------------------------------------------------------------------------------------+
|                                                                                                                       |
|   +------------------------------------+          +------------------------------------+                              |
|   | A. MARKET STRUCTURE                |          | B. MOMENTUM & TREND                |                              |
|   | - Causal Swings (lookback/forward) |          | - ADX (14-period Wilder)           |                              |
|   | - Break of Structure (BOS)         |          | - Momentum Acceleration (ROC-10)   |                              |
|   | - Change of Character (CHoCH)      |          | - EMA Alignment Score (9/21/50/200)|                              |
|   | - Liquidity Sweeps & Reclaim       |          | - Trend Persistence (bars vs EMA)  |                              |
|   | - Fair Value Gaps (3-bar FVG)      |          | - Multi-Timeframe Alignment (15m/1h|                              |
|   +------------------------------------+          +------------------------------------+                              |
|                     |                                                |                                                |
|                     +-----------------------+------------------------+                                                |
|                                             |                                                                         |
|                                             v                                                                         |
|   +----------------------------------------------------------------------------+                                      |
|   | C. VOLATILITY & MARKET REGIME                                              |                                      |
|   | - 4-State Classification: HV_TREND, LV_TREND, HV_RANGE, LV_RANGE           |                                      |
|   | - Kaufman Efficiency Ratio (0.0 Noise to 1.0 Linear Trend)                 |                                      |
|   | - Volatility Cycle: EXPANSION vs CONTRACTION vs NEUTRAL                    |                                      |
|   | - 100-bar Normalized ATR Percentile                                        |                                      |
|   +----------------------------------------------------------------------------+                                      |
|                                             |                                                                         |
|                     +-----------------------+------------------------+                                                |
|                     |                                                |                                                |
|   +------------------------------------+          +------------------------------------+                              |
|   | D. VOLUME & LIQUIDITY PROXIES      |          | E. CROSS-ASSET CONTEXT             |                              |
|   | - Relative Volume (RVOL-20)        |          | - BTC Directional Influence (5m/1h)|                              |
|   | - Log Volume Z-Score (50-bar)      |          | - ETH/BTC Relative Strength        |                              |
|   | - Amihud Illiquidity Proxy         |          | - Market Breadth (% above EMA 50)  |                              |
|   | - Effort vs Result Anomaly Ratio   |          | - Rolling 50-bar BTC Correlation   |                              |
|   | * Note: OHLCV != L2 Orderbook Depth|          | - Synchronized Timestamps (Zero lag|                              |
|   +------------------------------------+          +------------------------------------+                              |
|                                                                                                                       |
|   +----------------------------------------------------------------------------+                                      |
|   | F. EVENT & EXOGENOUS CONTEXT (INTERFACE ONLY)                              |                                      |
|   | - Status: DATA_UNAVAILABLE in historical backtests                         |                                      |
|   | - Pluggable schema for funding rates, liquidations, and macro news         |                                      |
|   | - Zero historical fabrication or lookahead insertion                       |                                      |
|   +----------------------------------------------------------------------------+                                      |
+-----------------------------------------------------------------------------------------------------------------------+
```

---

### 4. DISTINGUISHING EVIDENCE FROM INFERENCE

A fundamental rule of QUANTUM is the separation of **Observable Evidence** from **Inferred Explanations**:

1. **Observable Evidence (Deterministic Facts):**
   - Price pierced bar $t - 5$ swing high and closed $12\text{ bps}$ lower.
   - Volume was $2.4\times$ the 20-bar moving average.
   - 14-period ADX was $18.2$.
2. **Inferred Explanations (Falsifiable Hypotheses):**
   - "Institutional liquidity sweep absorbed retail breakout orders."
   - "Compression regime is about to resolve into an explosive trend."
3. **Prohibition:**
   - The engine must never assert an inference as an objective fact. All inferences must be formalized as hypotheses with explicit invalidation rules.

---

### 5. PRESERVATION OF SIX-AGENT ARCHITECTURE

The multi-factor market context engine maps directly into the preserved six-agent architecture:

- **Scout Agent:** Computes Dimensions A, B, D, and E across the 10 canonical symbols on 5m, 15m, and 1h resolutions.
- **Analyst Agent:** Synthesizes Dimension C (Regime Classification) and verifies hypothesis preconditions.
- **Sniper Agent:** Enforces causal next-bar open execution (`CAUSAL_NEXT_BAR_OPEN`) and point-in-time order routing.
- **Risk Agent:** Enforces 1.0x unlevered exposure on every event, manages stop-loss bounds, and monitors drawdowns.
- **Banker Agent:** Audits trade duration ($\le 240\text{m}$), applies AsterDEX retail fee schedules, and maintains cash ledgers.
- **Orchestrator Agent:** Coordinates pipeline execution, validates experiment contracts, and logs results.
