# QUANTUM PHASE 5.5.0.1: POSITION SIZING AND RISK CORRECTION

**Document Status:** `REQUIRES_HUMAN_APPROVAL`  
**Publication Timestamp:** `2026-11-01 20:29:46 UTC`  
**Associated Deliverable:** Workstream D (Position Sizing and Execution Risk)  

---

## 1. POSITION SIZING TERMINOLOGY AND DEFINITION

Phase 5.5.0 proposed the position sizing formula:
$$N_i = \frac{E_t \times 0.01}{1.5 \times \sigma_t}$$

Phase 5.5.0.1 explicitly clarifies the mathematical identity of $N_i$:
- **$N_i$ is Position Notional Value in quote currency (USDT).**
- Base asset quantity is $Q_i = N_i / P_{\text{entry}}$.
- Initial margin committed is $M_i = N_i / \text{Leverage}$.
- **$N_i$ is NEVER initial margin.** Conflating notional value with margin would cause immediate $100\times$ over-leverage.

---

## 2. THE 1.0% RISK TARGET AS A PROVISIONAL ASSUMPTION

The $1.0\%$ equity risk parameter is a **provisional design target**, NOT a guaranteed maximum loss.
Realized loss exceeds $1.0\%$ whenever:
1. **Opening Gaps:** Price gaps through the Stop Loss barrier on candle open.
2. **Execution Slippage:** Adverse fill slippage expands the stop loss distance.
3. **Exchange Fees:** Entry and exit taker fees reduce net equity.
4. **Funding Payments:** Negative funding accrues against the active position.

### Tail Loss Reality
Under severe market shocks, a trade targeting $1.0\%$ nominal risk may realize $-2.5\%$ to $-4.0\%$ loss. Risk models must account for tail slippage.

---

## 3. AUDIT OF THE 5 PORTFOLIO RISK LIMITS

| Limit ID | Parameter Name | Proposed Value | Mathematical Definition | Failure Behavior | Governance Status |
|---|---|---|---|---|---|
| **LIM_01** | Max Concurrent Positions | $3$ | $\sum_{s=1}^{11} \mathbb{I}(\text{Active}_s) \le 3$ | Reject 4th signal: `REJECTED_CONCURRENCY_LIMIT` | `REQUIRES_HUMAN_APPROVAL` |
| **LIM_02** | Max Gross Leverage | $3.0\times$ | $\frac{\sum N_i}{E_t} \le 3.0$ | Cap order notional to remaining leverage capacity | `REQUIRES_HUMAN_APPROVAL` |
| **LIM_03** | Max Instrument Margin | $35\%$ | $M_i / E_t \le 0.35$ | Scale down order size to $35\%$ equity cap | `REQUIRES_HUMAN_APPROVAL` |
| **LIM_04** | 24h Rolling Loss Circuit Breaker | $3.0\%$ | $\frac{E_t - E_{t-24h}}{E_{t-24h}} < -0.03$ | Halt trading across fleet for 24 hours (`CIRCUIT_BREAKER_HALT`) | `REQUIRES_HUMAN_APPROVAL` |
| **LIM_05** | Max Peak-to-Trough Drawdown Halt | $15.0\%$ | $\frac{\text{Peak} - E_t}{\text{Peak}} > 0.15$ | Permanent strategy termination (`FAILED_MAX_DRAWDOWN_BREACH`) | `REQUIRES_HUMAN_APPROVAL` |
