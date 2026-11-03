# QUANTUM EXECUTION GOVERNANCE — MILESTONE 5.8B
## Multi-Leg Execution Requirements, Friction Modeling & Operational Constraints

**Dossier Path:** `audit/strategy_research/milestone_5_8b_new_alpha_feasibility/EXECUTION_REQUIREMENTS.md`  
**Execution Timestamp:** 2026-11-04T00:19:00Z  
**Branch:** `research/quantum-next-3pct`  
**Authorizing Mandate:** Milestone 5.8B New Alpha Family Feasibility Protocol  

---

## 1. Executive Summary & Purpose

A major failure identified in previous milestones (EXP-08 through Milestone 5.7) was unrealistic execution assumptions: instantaneous fills, zero slippage, unhedged inventory, and synthetic maker rebates without adverse selection.

This document establishes the **mandatory execution and friction specifications** that must govern any subsequent empirical research across all candidate alpha families.

---

## 2. Strictly Unlevered Leverage Architecture (1.0x Hard Cap)

In strict accordance with the Project Owner's directives:
> *"Strictly unlevered exposure: 1.0x maximum. Do not use dynamic leverage. Do not use leverage increases as return optimization."*

### Mathematical Formalization
Let $E_t$ denote total portfolio Mark-to-Market equity in USDT.
Let $Q_i(t)$ denote the signed position size in asset $i$ and $P_i(t)$ denote its mark price.

$$\text{Gross Exposure} = \sum_{i=1}^{N} |Q_i(t)| \cdot P_i(t)$$
$$\text{Gross Leverage } (L_{\text{gross}}) = \frac{\sum_{i=1}^{N} |Q_i(t)| \cdot P_i(t)}{E_t} \le \mathbf{1.0000}$$

### Allocation Constraints for Market-Neutral Relative Value (Track C)
To maintain dollar neutrality without exceeding $1.0\times$ gross exposure:
$$\sum_{i \in \text{Long}} Q_i(t) \cdot P_i(t) \le +0.50 \cdot E_t$$
$$\sum_{j \in \text{Short}} |Q_j(t)| \cdot P_j(t) \le +0.50 \cdot E_t$$
$$\text{Net Delta Exposure } (\Delta_{\text{net}}) = \frac{\sum_{i=1}^{N} Q_i(t) \cdot P_i(t)}{E_t} \approx \mathbf{0.00 \pm 0.05}$$

**Zero Hidden Leverage Prohibition:** Borrowed capital, isolated cross-margin multipliers, or synthetic derivative leverage $>1.0\times$ are strictly forbidden.

---

## 3. Bybit VIP0 Baseline Transaction Cost Schedule

All strategy simulations must enforce standard Bybit VIP0 fee structures with zero unverified promotional fee assumptions:

```
+---------------------------------------------------------------------------------------------------+
| INSTRUMENT / VENUE         | ORDER TYPE            | VIP0 FEE RATE | SLIPPAGE & SPREAD DRAG      |
+---------------------------------------------------------------------------------------------------+
| USDT Perpetual Contracts   | Maker (Resting Limit) | +2.0 bps      | +1.5 bps Adverse Selection  |
| USDT Perpetual Contracts   | Taker (Aggressive)    | +5.5 bps      | +2.0 bps Half-Spread Drag   |
| Spot Market                | Maker (Resting Limit) | +10.0 bps     | +2.5 bps Queue Adverse Drag |
| Spot Market                | Taker (Aggressive)    | +10.0 bps     | +3.0 bps Half-Spread Drag   |
+---------------------------------------------------------------------------------------------------+
```

### Round-Trip Friction Budgets by Strategy Family
1. **Track A (Cash-and-Carry Spot + Perp):**
   - Spot Leg (Entry + Exit): $2 \times 10.0\text{ bps} = 20.0\text{ bps}$.
   - Perp Leg (Entry + Exit, Maker): $2 \times 2.0\text{ bps} = 4.0\text{ bps}$.
   - Legging Slippage Buffer: $7.0\text{ bps}$.
   - **Total Round-Trip Friction:** **$\mathbf{\approx 31.0\text{ bps}}$**.
2. **Track B (High-Frequency Order Flow):**
   - Entry (Maker) + Exit (Taker): $2.0 + 5.5 = 7.5\text{ bps}$.
   - Microprice Slippage: $3.5\text{ bps}$.
   - **Total Round-Trip Friction:** **$\mathbf{\approx 11.0\text{ bps per trade}}$** (Devastating for 5 bps alpha).
3. **Track C (Dollar-Neutral Pairs / Relative Value):**
   - Long Leg (Entry + Exit, Maker/Taker blend): $2 \times 3.75\text{ bps} = 7.5\text{ bps}$.
   - Short Leg (Entry + Exit, Maker/Taker blend): $2 \times 3.75\text{ bps} = 7.5\text{ bps}$.
   - Cross-Leg Slippage: $3.0\text{ bps}$.
   - **Total Round-Trip Friction:** **$\mathbf{\approx 18.0\text{ bps}}$**.

---

## 4. Multi-Leg Execution & Legging Risk Modeling

In multi-asset strategies (Track A cash-and-carry and Track C pairs/baskets), orders can never be assumed to fill simultaneously.

```
+---------------------------------------------------------------------------------------------------+
|                            MULTI-LEG SEQUENTIAL QUEUE PROTOCOL                                    |
+---------------------------------------------------------------------------------------------------+
|  1. Target Weight Calculation (Causal Close Bar t)                                                |
|                                            │
|                                            ▼
|  2. Limit Order Submission on Primary Leg (Bar t+1 Open)                                          |
|     - Check Exchange Minimum Notional ($5.00 USDT per leg)                                        |
|     - Place Limit Order at Best Bid / Best Ask                                                    |
|                                            │
|                                            ▼
|  3. Fill Determination & Legging Timeout Check:                                                   |
|     - IF Primary Leg Fills:                                                                       |
|         Immediately submit hedge order on Secondary Leg.                                          |
|         Apply slippage penalty based on price displacement during interval.                       |
|     - IF Primary Leg Does NOT Fill within Timeout Window:                                         |
|         Cancel order; do NOT submit secondary leg.                                                |
|         Account remains 100% flat (0 unhedged exposure).                                          |
|     - IF Partial Fill Occurs on Primary Leg:                                                      |
|         Hedge ONLY the filled fractional quantity on Secondary Leg.                               |
|         Cancel residual primary quantity.                                                         |
+---------------------------------------------------------------------------------------------------+
```

### The $5.00 Minimum Order Notional Gate
Following the critical finding in Milestone 5.8A:
$$\text{If Target Notional } (w_i \cdot E_t) < \mathbf{5.00 \text{ USDT}} \implies \text{Reject Order}$$

- In a 4-asset market-neutral relative value portfolio ($w_i = 0.125$ per slot), total portfolio equity must satisfy:
  $$E_t \ge \frac{\$5.00}{0.125} = \mathbf{\$40.00 \text{ USDT}}$$
- Any simulation initializing capital below $\$100.00$ must enforce strict minimum-notional rejections to prevent simulator artifacts.

---

## 5. Execution Governance Sign-Off

All future strategy simulators submitted to the QUANTUM governance committee must implement:
1. Hard programmatic assertion: `assert gross_leverage <= 1.0001`.
2. Explicit limit order timeout and queue fill modeling.
3. Full VIP0 taker and maker fee deduction per trade record.
4. Independent trade-level and calendar-level equity reconciliation.
