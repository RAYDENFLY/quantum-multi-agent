# QUANTUM PHASE 5.5.0: EXECUTION COST SPECIFICATION

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-01 20:23:18 UTC`  
**Associated Deliverable:** Workstream C (Realistic Transaction Cost Model)  

---

## 1. COMPREHENSIVE COST ARCHITECTURE

In perpetual futures trading, gross returns are eroded by multiple distinct friction components:
$$\text{Net PnL} = \text{Gross PnL} - \text{Fees} - \text{Slippage} - \text{Spread} - \text{Funding} - \text{Other Costs}$$

To avoid double-counting, each cost component is strictly separated:
1. **Exchange Trading Fees ($C_{\text{fee}}$):** Contractual fees charged by the exchange on trade notional.
2. **Bid-Ask Spread Cost ($C_{\text{spread}}$):** The cost of crossing the half-spread on market orders.
3. **Execution Slippage ($C_{\text{slip}}$):** Price impact caused by order execution relative to decision price.
4. **Funding Payments ($C_{\text{fund}}$):** Periodic financing transfers between long and short contract holders.
5. **Liquidation / Forced Deleveraging ($C_{\text{other}}$):** Penalty fees incurred during margin calls (prevented via risk controls).

---

## 2. MAKER AND TAKER EXECUTION SCENARIOS

Historical backtests frequently make unrealistic assumptions regarding maker execution. Phase 5.5 evaluates four distinct execution regimes:

### Scenario 1: Taker Entry / Taker Exit (Base Model - Primary Benchmark)
- **Entry:** Market order executed immediately at $P_{\text{entry}} = \text{open}[i+1]$.
- **Exit:** Market order executed immediately upon barrier breach ($P_{\text{exit}} = \text{barrier}$) or expiration.
- **Fee Treatment:** Taker fee applied at both entry and exit.
- **Slippage Treatment:** Full dynamic slippage applied at both entry and exit.
- **Fill Certainty:** 100% fill probability assumed on eligible bars.
- **Governance Rule:** This is the **primary baseline** for all economic acceptance decisions.

### Scenario 2: Maker Entry / Taker Exit (Optimistic Passive Entry)
- **Entry:** Limit order placed at $\text{close}[i]$.
- **Fill Condition:** Order is filled only if $\text{low}[i+1] < \text{close}[i]$ (for long) or $\text{high}[i+1] > \text{close}[i]$ (for short).
- **Unfilled Policy:** If limit order is not touched within 1 candle (5m), order is cancelled (`CANCELLED_UNFILLED`). No trade recorded.
- **Fee Treatment:** Maker fee/rebate applied at entry; taker fee applied at exit.
- **Adverse Selection Penalty:** Filled maker orders face adverse selection bias (trades filled passively tend to move against the position).

### Scenario 3: Maker Entry / Maker Exit (Ultra-Optimistic - Stress Test Only)
- **Entry:** Passive limit order at close.
- **Exit:** Passive limit order at target barrier.
- **Governance Status:** **Rejected for primary validation**. Limit orders placed at volatile barrier touches face near-certain queue non-execution.

---

## 3. COST SENSITIVITY TIERS

To maintain continuity with Phase 5.4 while providing institutional-grade validation, Phase 5.5 establishes four standardized cost tiers:

| Tier Name | Round-Trip Cost | Entry Fee | Exit Fee | Entry Slip | Exit Slip | Rationale & Governance Status |
|---|---|---|---|---|---|---|
| **Comparability Tier** | **7 bps** (0.07%) | 2.0 bps | 2.0 bps | 1.5 bps | 1.5 bps | VIP maker/taker blend; historical Phase 5.4.2 comparability only. |
| **Base Case Tier** | **15 bps** (0.15%) | 5.0 bps | 5.0 bps | 2.5 bps | 2.5 bps | Standard retail/VIP0 crypto perpetual taker fees + normal spread. |
| **Conservative Tier** | **20 bps** (0.20%) | 6.0 bps | 6.0 bps | 4.0 bps | 4.0 bps | Standard retail taker fees + moderate volatility slippage buffer. **Mandatory Gate**. |
| **Severe Stress Tier** | **30 bps** (0.30%) | 8.0 bps | 8.0 bps | 7.0 bps | 7.0 bps | High-volatility market stress, illiquid conditions, and spread widening. |

---

## 4. ADVERSE AMBIGUITY EXECUTION RULE

In 5m OHLC bar evaluation, when both the upper barrier ($u$) and lower barrier ($l$) are touched within the same candle:
$$\text{high}[j] \ge u \quad \text{and} \quad \text{low}[j] \le l$$
Intrabar tick ordering cannot be determined from OHLC data alone.

### Mandatory Governance Rule
- **For LONG Positions:** It must be assumed that the lower barrier (Stop Loss) was touched **FIRST**. Fill price is set to lower barrier ($P_{\text{exit}} = l$).
- **For SHORT Positions:** It must be assumed that the upper barrier (Stop Loss) was touched **FIRST**. Fill price is set to upper barrier ($P_{\text{exit}} = u$).
- **Zero Favorable Assumptions:** Under no circumstances may an ambiguous touch be resolved as a Take Profit.
