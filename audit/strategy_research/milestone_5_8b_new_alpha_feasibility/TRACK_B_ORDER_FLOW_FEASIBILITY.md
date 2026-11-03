# QUANTUM RESEARCH FEASIBILITY — MILESTONE 5.8B
## Track B: Order Flow Microstructure & L2 Imbalance Feasibility Study

**Dossier Path:** `audit/strategy_research/milestone_5_8b_new_alpha_feasibility/TRACK_B_ORDER_FLOW_FEASIBILITY.md`  
**Execution Timestamp:** 2026-11-04T00:16:00Z  
**Branch:** `research/quantum-next-3pct`  
**Authorizing Mandate:** Milestone 5.8B New Alpha Family Feasibility Protocol  

---

## 1. Executive Summary & Research Track Mandate

Track B investigates whether **High-Frequency Order Flow Imbalance (OFI), Book Depth Skew, and Volume Delta Dynamics** contain causal predictive power to generate sustainable alpha, bypassing the known failure modes of macro 5m OHLCV momentum.

### Research Track Scorecard
```yaml
RESEARCH_TRACK: TRACK_B_ORDER_FLOW_MICROSTRUCTURE
UNDERLYING_MECHANISM: Sub-Second Order Flow Imbalance, Microprice Displacement & Queue Dynamics
DATA_AVAILABILITY_STATUS: DATA_UNAVAILABLE (Requires Dedicated L2 / Tick Pipeline)
CURRENT_DATA_COVERAGE: 0 L2 Snapshots in historical.db / 0 Tick Trades in canonical
EXECUTION_LEVERAGE: Strictly 1.0x (Unlevered Intraday Inventory)
EXPECTED_TRANSACTION_FRICTION: Extremely High (Sub-Minute Turnover, Severe Fee Hurdle)
EXECUTION_COMPLEXITY: Extremely High (Microsecond Queue Priority & Fill Simulation)
PREDICTIVE_HORIZON: 100ms to 60 Seconds (Rapid Alpha Half-Life)
TARGET_GATE_FEASIBILITY: SEVERELY_CONSTRAINED_BY_EXCHANGE_FEES (At Bybit VIP0)
RECOMMENDED_DISPOSITION: DATA_ACQUISITION_REQUIRED
```

---

## 2. Microstructure Theory & Feature Taxonomy

Unlike bar-level technical indicators that aggregate price into arbitrary time windows, order flow microstructure measures the continuous interaction between aggressive market orders and resting passive limit orders.

### 2.1 Order Flow Imbalance (OFI)
Following Cont, Kukanov, and Stoikov (2014), OFI quantifies the net change in order book supply and demand at the best bid and ask levels across events $k$:
$$e_k = \Delta Q_B(k) - \Delta Q_A(k)$$
Where:
- $\Delta Q_B(k) = I_{\{P_B(k) \ge P_B(k-1)\}} \cdot q_B(k) - I_{\{P_B(k) \le P_B(k-1)\}} \cdot q_B(k-1)$
- $\Delta Q_A(k) = - I_{\{P_A(k) \le P_A(k-1)\}} \cdot q_A(k) + I_{\{P_A(k) \ge P_A(k-1)\}} \cdot q_A(k-1)$

### 2.2 Volume Delta & Cumulative Volume Delta (CVD)
Measures the aggressor direction of public executed trades:
$$\Delta V_t = V_{\text{aggressor\_buy}} - V_{\text{aggressor\_sell}}$$
When persistent aggressive buying fails to move price upward, absorption is detected, signaling potential inventory exhaustion and imminent mean-reversion.

### 2.3 Microprice Displacement & Depth Imbalance
The microprice incorporates volume-weighted bid/ask depth $q_B, q_A$ to forecast the next mid-price:
$$P_t^{\text{micro}} = \frac{q_B \cdot P_A + q_A \cdot P_B}{q_B + q_A} = P_B + \left(\frac{q_B}{q_B + q_A}\right) \cdot \text{Spread}$$
$$\text{Depth Imbalance} = \frac{\sum_{i=1}^{D} q_{B,i} - \sum_{i=1}^{D} q_{A,i}}{\sum_{i=1}^{D} q_{B,i} + \sum_{i=1}^{D} q_{A,i}}$$

---

## 3. Data Provenance & Availability Audit

Section 4 of the Milestone 5.8B Mandate strictly instructs:
> *"Strictly causal timestamps are mandatory. Do not synthesize L2 data from 5m OHLCV. If the required data is unavailable, produce a data acquisition specification and stop the empirical strategy test."*

The local repository was audited via [`scripts/audit_milestone_5_8b_data_inventory.py`](file:///d:/quantum-multi-agent/scripts/audit_milestone_5_8b_data_inventory.py):

```
+---------------------------------------------------------------------------------------------------+
| COMPONENT                  | STATUS      | DATABASE / PARQUET STATE                              |
+---------------------------------------------------------------------------------------------------+
| Tick Trades Tape           | MISSING     | 0 rows in historical.db; no raw trade streams         |
| L2 Order Book Snapshots    | MISSING     | 0 rows in historical.db ('market_orderbook_snapshots')|
| Sub-Second Tickers (L1)    | MISSING     | 0 rows in historical.db ('market_tickers' empty)      |
| Bid/Ask Spread History     | MISSING     | No top-of-book quotes available in canonical datasets |
| 5m Aggregated Volume       | AVAILABLE   | Candle volume and taker buy volume present in 5m bars |
+---------------------------------------------------------------------------------------------------+
```

### Prohibition Against L2 Synthesis
Attempting to synthesize L2 depth or quote dynamics from 5m OHLCV bars is mathematically invalid. 5-minute bars discard all intra-bar sequence, queue arrival order, cancellation volume, and spread transitions. 

In strict adherence to instructions, **all empirical strategy testing on Track B is halted immediately**.

---

## 4. Execution Friction, Latency & The Bybit VIP0 Fee Hurdle

Even if full L2 and tick datasets were immediately available, the economic viability of high-frequency microstructure strategies faces an insurmountable friction hurdle at the VIP0 tier:

```
+---------------------------------------------------------------------------------------------------+
|                           MICROSTRUCTURE PROFIT-TO-FRICTION BUDGET                                |
+---------------------------------------------------------------------------------------------------+
|  Typical Microstructure Alpha Displacement:  +1.5 to +4.0 bps per trade                           |
|                                            │
|                                            ▼
|  Bybit VIP0 Transaction Cost Hurdle:                                                              |
|    - Maker Fee: +2.0 bps (Entry) + Adverse Selection Slippage (+1.5 bps) = +3.5 bps              |
|    - Taker Fee: +5.5 bps (Entry) + Spread Half-Cost (+2.0 bps)          = +7.5 bps              |
|                                            │
|                                            ▼
|  Roundtrip Net Drag:                         -7.0 to -15.0 bps per trade                          |
+---------------------------------------------------------------------------------------------------+
```

### The VIP0 Friction Paradox
1. **Alpha Decay Half-Life:** Microstructural signals (OFI, depth imbalance) decay within $500\text{ ms}$ to $30\text{ seconds}$.
2. **Execution Dilemma:**
   - **Taker Orders:** Immediate fill, but $-11.0\text{ bps}$ round-trip taker fee destroys the $+2.5\text{ bps}$ signal edge instantly.
   - **Maker Orders:** Resting on the book earns $+2.0\text{ bps}$ fee rebate, but subjects the fill to **toxic adverse selection**: the order is filled primarily when an informed trader aggressively trades through the level, causing post-fill markout losses.
3. **Institutional Viability Requirement:** Microstructure alpha is viable only for MM/HFT desks operating at Bybit VIP5/Supreme or Binance Tier 9 where maker fees are **negative ($-1.0\text{ to } -1.5\text{ bps}$ rebate)** and colocation minimizes queue latency to $<50\mu\text{s}$.
4. At standard Bybit VIP0 (+2.0 bps maker / 5.5 bps taker), a strategy executing $>200$ micro-trades per day is guaranteed to experience capital exhaustion identical to Milestone 5.8A.

---

## 5. Data Acquisition Specification

To enable future microstructural research, the following streaming pipeline and storage architecture must be deployed:

```yaml
DATA_ACQUISITION_SPECIFICATION:
  EXCHANGE_VENUES:
    - BYBIT: "wss://stream.bybit.com/v5/public/linear"
    - BINANCE: "wss://fstream.binance.com/ws"
  REQUIRED_STREAMS:
    PUBLIC_TRADES: "publicTrade.{symbol} (Tick-by-tick trade tape with maker/taker flag)"
    L2_ORDERBOOK_DELTA: "orderbook.50.{symbol} (Depth diffs pushed at 20ms to 100ms)"
    TICKERS_L1: "tickers.{symbol} (Best bid/ask price and size pushed at 100ms)"
  TIME_SYNCHRONIZATION:
    PROTOCOL: Hardware PTP (Precision Time Protocol) / Cloud Chrony (< 500 microsecond jitter)
    TIMESTAMP_RECORDING: Hardware receipt timestamp (ts_local_ns) + Exchange matching engine timestamp (ts_match_ms)
  STORAGE_ARCHITECTURE:
    COMPRESSION: Zstandard (zstd) compressed Parquet or Feather
    PARTITIONING: Date / Hour / Symbol
    ESTIMATED_STORAGE_REQUIREMENT: ~120 GB per symbol/year (~1.2 TB/year for 10 assets)
  INGESTION_MODULE: scripts/data/stream_l2_microstructure.py
```

### Final Research Disposition
- **Classification:** **`DATA_ACQUISITION_REQUIRED`**
- **Action:** Empirical testing is halted. Prior to any modeling, the data collection daemon must be configured, deployed, and validated for timestamp monotonicity and queue sequence continuity.
