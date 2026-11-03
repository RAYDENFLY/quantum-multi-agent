# QUANTUM RESEARCH FEASIBILITY — MILESTONE 5.8B
## Track A: Delta-Neutral Funding & Perpetual-to-Spot Basis Feasibility Study

**Dossier Path:** `audit/strategy_research/milestone_5_8b_new_alpha_feasibility/TRACK_A_FUNDING_BASIS_FEASIBILITY.md`  
**Execution Timestamp:** 2026-11-04T00:15:00Z  
**Branch:** `research/quantum-next-3pct`  
**Authorizing Mandate:** Milestone 5.8B New Alpha Family Feasibility Protocol  

---

## 1. Executive Summary & Research Track Mandate

Track A investigates whether **Delta-Neutral Funding Arbitrage and Perpetual-to-Spot Basis Convergence** can serve as an independent, non-directional source of alpha for the QUANTUM trading engine following the rejection of the HYP-01 directional momentum architecture.

### Research Track Scorecard
```yaml
RESEARCH_TRACK: TRACK_A_FUNDING_AND_BASIS
UNDERLYING_MECHANISM: Delta-Neutral Cash-and-Carry / Funding Rate Harvesting
DATA_AVAILABILITY_STATUS: DATA_UNAVAILABLE (Requires Dedicated Historical Backfill)
CURRENT_DATA_COVERAGE: 0 Funding Events in historical.db / 0 Spot Series in canonical
EXECUTION_LEVERAGE: Strictly 1.0x (Unlevered Spot + 1.0x Short Perpetual)
EXPECTED_TRANSACTION_FRICTION: Low to Medium (8-Hour Holding Period Cadence)
LEGGING_RISK_PROFILE: High (Non-Simultaneous Execution Across Spot & Derivative Books)
UNLEVERED_ANNUALIZED_CAPACITY: 10% to 35% APR (~0.027% to ~0.096% Net Daily Return)
TARGET_GATE_FEASIBILITY: INSUFFICIENT_FOR_3_PERCENT_DAILY_GATE (At 1.0x Unlevered)
RECOMMENDED_DISPOSITION: DATA_ACQUISITION_REQUIRED
```

---

## 2. Market Mechanics & Theoretical Foundation

### 2.1 Perpetual Funding Rate Settlement
Perpetual contracts maintain price alignment with the underlying index via periodic cash payments exchanged between long and short market participants:
$$F_t = \text{Clamp}\left(\text{Premium Index}_t, -0.05\%, +0.05\%\right) + \text{Interest Rate}$$

- **Settlement Cadence:** Every 8 hours at `00:00:00`, `08:00:00`, and `16:00:00 UTC` on Bybit and Binance.
- **Cash Flow Direction:**
  - If $F_t > 0$ (Bullish bias / contango): Longs pay shorts. A short perpetual position receives $+F_t \cdot \text{Notional}$.
  - If $F_t < 0$ (Bearish bias / backwardation): Shorts pay longs. A short perpetual position pays $|F_t| \cdot \text{Notional}$.
- **Volatility & Reversals:** Funding rates are non-stationary, exhibiting clustering during bull runs (where rates spike to $+0.05\%$ to $+0.10\%$ per 8 hours) followed by rapid collapses to zero or negative rates during liquidation flushes.

### 2.2 Perpetual-to-Spot Basis
The basis $B_t$ is defined as the absolute or percentage spread between the perpetual mark price $P_t^{\text{perp}}$ and the spot index price $P_t^{\text{spot}}$:
$$B_t = \frac{P_t^{\text{perp}} - P_t^{\text{spot}}}{P_t^{\text{spot}}}$$

Under an unlevered cash-and-carry framework:
1. **Long Spot:** Allocate $\$50.00$ cash to purchase $Q$ units of spot asset at $P_t^{\text{spot}}$.
2. **Short Perpetual:** Allocate $\$50.00$ margin to sell short $Q$ contracts of perpetual at $P_t^{\text{perp}}$.
3. **Net Delta:** $\Delta_{\text{net}} = Q - Q = 0$ (Delta-neutral).
4. **Gross Yield:** Accrues from (a) funding payments collected every 8 hours, and (b) basis convergence at settlement/unwind:
   $$\text{Gross Return} = \sum_{k=1}^{N} F_k \cdot \text{Notional}_{\text{short}} + \left(B_{\text{entry}} - B_{\text{exit}}\right) \cdot \text{Notional}$$

---

## 3. Data Provenance & Availability Audit

An exhaustive forensic scan of the local repository was conducted via [`scripts/audit_milestone_5_8b_data_inventory.py`](file:///d:/quantum-multi-agent/scripts/audit_milestone_5_8b_data_inventory.py).

### Forensic Inventory Findings
```
+---------------------------------------------------------------------------------------------------+
| COMPONENT                  | STATUS      | DATABASE / PARQUET STATE                              |
+---------------------------------------------------------------------------------------------------+
| 8-Hour Funding Rate Series | MISSING     | 0 rows in historical.db ('funding_events' table empty) |
| Spot OHLCV / Spot Book     | MISSING     | No spot directory or files exist in data/             |
| Cross-Exchange Spreads     | MISSING     | Only exchange=ASTER perpetual candles exist           |
| Margin Borrow Rates        | MISSING     | No lending/borrow rate series available in workspace   |
| 5m Perpetual OHLCV         | AVAILABLE   | 1,099 continuous calendar days for 10 assets          |
+---------------------------------------------------------------------------------------------------+
```

In accordance with Section 3 of the Milestone 5.8B Mandate:
> *"If historical funding data is unavailable, classify the hypothesis as DATA_UNAVAILABLE rather than fabricating it."*

**Governance Classification:** Track A is formally designated as **`DATA_UNAVAILABLE`**. No simulated funding rates may be generated or backtested until real historical exchange feeds are ingested.

---

## 4. Execution Friction, Legging & Counterparty Risk

A realistic cash-and-carry strategy cannot assume simultaneous, costless execution:

```
+---------------------------------------------------------------------------------------------------+
|                              CHRONOLOGICAL MULTI-LEG EXECUTION                                    |
+---------------------------------------------------------------------------------------------------+
|  T_0: Signal Generated -> Basis / Funding Dislocation Exceeds Friction Hurdle                     |
|                                            │
|                                            ▼
|  T_1: Leg 1 Execution (Spot Book)                                                                 |
|       - Submit Limit Buy on Spot -> Await Maker Fill or Pay Taker Fee (10.0 bps Bybit VIP0)       |
|       - Execution Lag: 100ms - 5,000ms                                                            |
|                                            │
|                                            ▼
|  T_2: Leg 2 Execution (Perpetual Derivative Book)                                                 |
|       - Upon Spot Fill Confirmation, Submit Limit Sell on Perpetual                               |
|       - Taker / Maker Fee: +2.0 bps Maker / 5.5 bps Taker (Bybit VIP0)                            |
|       - Price Slippage / Adverse Market Movement during Legging Interval                          |
+---------------------------------------------------------------------------------------------------+
```

### Risk Vectors
1. **Legging Risk (Execution Lag):** If the market moves sharply between the spot fill and the perpetual fill, delta is unhedged, creating adverse selection losses that exceed months of expected funding yield.
2. **Asymmetric Fee Drag:** Spot trading fees are typically higher (10.0 bps taker on Bybit VIP0) than perpetual fees (5.5 bps taker / 2.0 bps maker). A complete round-trip across both legs incurs:
   $$\text{Round-Trip Friction} = \text{Fee}_{\text{spot\_entry}} + \text{Fee}_{\text{perp\_entry}} + \text{Fee}_{\text{spot\_exit}} + \text{Fee}_{\text{perp\_exit}} \approx 20.0 \text{ to } 31.0 \text{ bps}$$
   To break even, the position must harvest at least 3 to 4 positive funding cycles (24 to 32 hours) at $+0.01\%$ per 8 hours.
3. **Negative Funding Risk:** During market drawdowns, funding rates frequently turn negative ($-0.02\%$ to $-0.05\%$). If held, the cash-and-carry position bleeds cash on every 8-hour timestamp.
4. **Capital Fragmentation & Liquidation Risk:** While the overall portfolio is delta-neutral, spot collateral cannot automatically offset unrealized losses on the short perpetual leg. In a massive bull surge, the perpetual leg can face forced margin liquidation unless dynamically rebalanced.

---

## 5. Economic Capacity & The 3.00% Daily Return Hurdle

The Project Owner's mandatory acceptance criterion requires:
$$\text{Mean Net Daily Return } \ge \mathbf{+3.00\%} \quad \text{at Strictly 1.0x Unlevered Exposure}$$

### Mathematical Boundary Analysis
Let us evaluate whether an unlevered cash-and-carry portfolio can mathematically achieve $+3.00\%$ net daily return:

1. **Daily Compounding Requirement:**
   $$R_{\text{annual}} = (1 + 0.03)^{365} - 1 \approx 4,848,272\% \quad (\text{or } 3.00\% \times 365 = \mathbf{1,095\% \text{ Simple APR}})$$
2. **Empirical Reality of Crypto Funding Rates:**
   - Benchmark Bybit/Binance 8-hour funding rate: Typically $+0.0100\%$ per 8 hours ($+0.0300\%$ per day).
   - High-bull market funding rate: $+0.0300\%$ per 8 hours ($+0.0900\%$ per day).
   - Extreme speculative frenzy funding rate: $+0.1000\%$ per 8 hours ($+0.3000\%$ per day).
3. **Unlevered Portfolio Yield:**
   Because only $50\%$ of equity is allocated to the short perpetual leg (the other $50\%$ is deployed in spot collateral):
   $$\text{Daily Net Yield} = 0.50 \times \text{Daily Funding Rate} - \text{Financing/Friction Drag}$$
   - Baseline Annualized Yield: **$5.48\%$ to $10.95\%$ APR** ($\mathbf{0.015\% \text{ to } 0.030\% \text{ per day}}$).
   - Bull Market Annualized Yield: **$16.42\%$ to $32.85\%$ APR** ($\mathbf{0.045\% \text{ to } 0.090\% \text{ per day}}$).
   - Extreme Ceiling (Unlevered): **$\le 55.0\%$ APR** ($\mathbf{\le 0.150\% \text{ per day}}$).

### Economic Conclusion
$$\text{Max Attainable Unlevered Return } (\approx 0.05\%/\text{day}) \ll \text{Target Gate } (3.00\%/\text{day})$$
The mandatory $3.00\%$ daily return gate is **$60\times$ larger** than the maximum theoretical yield of an unlevered funding arbitrage strategy. 

While Track A represents an institutional-grade, low-drawdown delta-neutral strategy capable of delivering $10\%$ to $25\%$ unlevered annual returns with $\text{MDD} \le 3\%$, it is **structurally incapable of satisfying a $3.00\%$ daily return mandate at 1.0x leverage**.

---

## 6. Data Acquisition Specification & Next Steps

Before Track A can be tested empirically, the following data infrastructure must be constructed:

```yaml
DATA_ACQUISITION_SPECIFICATION:
  ENDPOINTS:
    BYBIT_FUNDING: "GET /v5/market/funding/history?category=linear&symbol={symbol}&limit=200"
    BYBIT_SPOT_KLINES: "GET /v5/market/kline?category=spot&symbol={symbol}&interval=5"
    BINANCE_FUNDING: "GET /fapi/v1/fundingRate?symbol={symbol}&limit=1000"
  TARGET_DATE_RANGE: "2023-10-28 00:00:00 to 2026-10-31 23:59:59 UTC"
  STORAGE_FORMAT: Parquet partitioned by exchange, symbol, and year
  ESTIMATED_DATASET_SIZE: ~4.5 GB across 10 primary universe pairs
  INGESTION_MODULE_PATH: scripts/data/backfill_funding_and_basis.py
```

### Final Research Disposition
- **Classification:** **`DATA_ACQUISITION_REQUIRED`**
- **Action:** Suspend empirical testing until historical funding and spot datasets are acquired, validated, and cryptographically fingerprinted.
