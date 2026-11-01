# QUANTUM PHASE 5.5.0.4: DEC_05 PORTFOLIO RISK & CONCURRENCY BRIEF

**Decision ID:** `DEC_05`  
**Title:** Portfolio Concurrency and Leverage Limits  
**Governance Status:** `PENDING_HUMAN_DECISION`  
**Execution Blocking:** `YES`  

---

## 1. OPTIONS AND GOVERNANCE QUESTION

The 11 specialist models trade independently but share a single account equity pool. The supervisor must set portfolio-level risk limits:
1. **Max 2 Concurrent Positions, Max 2.0x Gross Leverage.**
2. **Max 3 Concurrent Positions, Max 3.0x Gross Leverage.**
3. **Max 5 Concurrent Positions, Max 5.0x Gross Leverage.**

---

## 2. PORTFOLIO RISK AGGREGATION & CROSS-ASSET CORRELATION

Gross leverage is defined precisely as:
$$\text{Gross Leverage}_t = \frac{\sum_{k=1}^K |N_{k, t}|}{\text{Equity}_t}$$

Crucial market dynamics to consider:
1. **High Cross-Asset Correlation:** Cryptocurrency assets exhibit high cross-correlation (frequently $\rho > 0.70$ with BTC). Holding 5 concurrent long positions in BTC, ETH, SOL, AVAX, and LINK is NOT 5 independent bets; it is a single concentrated $5.0\times$ levered bet on market direction.
2. **Clustered Drawdown Risk:** During sharp market pullbacks, stop losses across all open long positions hit simultaneously, causing severe compounding equity drawdowns.
3. **Position Sizing Rules:** Fixed fractional risk allocation budgets exactly $1.0\%$ account equity risk per trade based on distance to stop loss. Max 3 positions caps simultaneous capital at risk to $3.0\%$ of account equity.
4. **Signal Priority Queue:** When more valid signals trigger than allowed by the concurrency cap, signals are prioritized by calibrated probability margin $\Delta P = P_{\text{target}} - \max(P_{\text{other}})$.

---

## 3. COMPARISON OF CONCURRENCY OPTIONS

| Limit Setting | Max Positions | Max Gross Leverage | Max Capital at Risk | Trade-off Analysis |
|---|---|---|---|---|
| **Ultra-Conservative** | 2 positions | 2.0x | 2.0% equity | Minimizes drawdown risk; causes high signal rejection (opportunity cost) |
| **Balanced Standard** | 3 positions | 3.0x | 3.0% equity | Balances multi-asset diversification with strict drawdown control |
| **Aggressive** | 5 positions | 5.0x | 5.0% equity | Maximizes capital utilization; severe drawdown risk during correlated market crashes |

---

## 4. SUPERVISOR RECOMMENDATION

- **Recommendation:** Approve `Maximum 3 concurrent positions and maximum 3.0x gross leverage` with priority queue by calibrated confidence $\Delta P$.
- **Status:** `PENDING_HUMAN_DECISION`. Awaiting supervisor selection.
