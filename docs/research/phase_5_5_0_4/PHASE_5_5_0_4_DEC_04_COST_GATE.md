# QUANTUM PHASE 5.5.0.4: DEC_04 PRIMARY ECONOMIC COST GATE BRIEF

**Decision ID:** `DEC_04`  
**Title:** Primary Economic Cost Gate Tier  
**Governance Status:** `PENDING_HUMAN_DECISION`  
**Execution Blocking:** `YES`  

---

## 1. OPTIONS AND COST DEFINITION

Gate 2 defines the mandatory break-even hurdle that a specialist must clear on historical OOF data after transaction friction. The supervisor must establish the primary hurdle tier:
1. **15 bps Round-Trip (Base Case Tier):** Assumes institutional VIP exchange taker fees (2.5-3.5 bps per leg) and tight liquid top-of-book spreads.
2. **20 bps Round-Trip (Conservative Retail Tier):** Assumes standard retail taker fees (5.0 bps per leg = 10 bps round-trip) plus dynamic spread and market impact slippage (8-10 bps round-trip).
3. **30 bps Round-Trip (Severe Stress Tier):** Assumes elevated retail fees (6.0 bps per leg), fast-market volatility spread widening, and altcoin depth penalties.

---

## 2. PRECISE COMPONENT BREAKDOWN & DIMENSIONAL REALISM

Total round-trip transaction friction is formulated as:
$$C_{\text{round-trip}} = 2 \times C_{\text{fee}} + 2 \times C_{\text{spread}} + 2 \times C_{\text{volatility}} + 2 \times C_{\text{impact}}$$

In the verified hypothetical numerical walkthrough (notional $N = \$10,000$, 5m volume $V = \$500,000$, $\sigma_t = 0.0030$):
- Taker fees (5.0 bps entry + 5.0 bps exit): $10.0\text{ bps}$.
- Slippage per leg: $C_{\text{spread}} (1.0\text{ bps}) + C_{\text{volatility}} (1.5\text{ bps}) + C_{\text{impact}} (1.414\text{ bps}) = 3.914\text{ bps}$ per leg.
- Total round-trip drag: $10.0 + 3.914 + 3.914 = \mathbf{17.828\text{ bps}}$.

This proves that 20 bps represents an economically realistic, defensible break-even hurdle for retail crypto perpetual traders.

---

## 3. COMPARISON TABLE

| Tier | Round-Trip Cost | Fee Assumption | Slippage Buffer | Risk Profile | Justification Requirement |
|---|---|---|---|---|---|
| **Base Tier (15 bps)** | 15.0 bps | 5.0 bps total | 10.0 bps total | High risk of false positive alpha | Requires proving VIP fee tier and institutional execution |
| **Conservative Tier (20 bps)** | 20.0 bps | 10.0 bps total | 10.0 bps total | Balanced, realistic standard | Matches modeled retail taker friction (17.83 bps) |
| **Severe Stress (30 bps)** | 30.0 bps | 12.0 bps total | 18.0 bps total | High risk of rejecting viable alpha | Appropriate for extreme volatility stress testing |

---

## 4. SUPERVISOR RECOMMENDATION

- **Recommendation:** Confirm the `20 bps Conservative Tier` as the mandatory pass/fail break-even gate (Gate 2), while evaluating 15 bps and 30 bps as secondary sensitivity sweeps.
- **Status:** `PENDING_HUMAN_DECISION`. Awaiting supervisor selection.
