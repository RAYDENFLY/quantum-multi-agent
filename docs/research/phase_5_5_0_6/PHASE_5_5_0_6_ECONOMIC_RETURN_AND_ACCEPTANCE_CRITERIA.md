# QUANTUM PHASE 5.5.0.6: ECONOMIC RETURN FORMULATION & ACCEPTANCE CRITERIA

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-01 21:09:14 UTC`  
**Associated Deliverable:** Workstream C (Return & Acceptance Criteria Architecture)  

---

## 1. MATHEMATICAL FORMULATION OF ECONOMIC RETURN

Phase 5.5.0.6 establishes rigorous, unambiguous mathematical definitions for all economic performance outputs:

### 1. Gross Trading PnL (USDT)
$$\text{PnL}_{\text{gross}} = d \times Q \times (P_{\text{exit, ref}} - P_{\text{entry, ref}})$$
where $d = +1$ for LONG, $d = -1$ for SHORT, and $Q$ is trade quantity in base currency.

### 2. Transaction Costs (USDT)
$$C_{\text{transaction, USDT}} = N_{\text{entry}} \times C_{\text{leg, entry}} + N_{\text{exit}} \times C_{\text{leg, exit}}$$
where $N_{\text{entry}} = Q \times P_{\text{entry}}$ and $N_{\text{exit}} = Q \times P_{\text{exit}}$.

### 3. Financing Cash Flow (USDT)
$$CF_{\text{funding, USDT}} = -d \times N_{\text{settle}} \times f_t$$
where $N_{\text{settle}}$ is mark notional at discrete settlement timestamps, and $f_t$ is the decimal funding rate.
- **Signed Nature:** When $f_t > 0$, Longs pay funding ($CF < 0$) and Shorts receive funding ($CF > 0$). When $f_t < 0$, Longs receive funding ($CF > 0$) and Shorts pay funding ($CF < 0$).

### 4. Net Trading PnL (USDT)
$$\text{PnL}_{\text{net}} = \text{PnL}_{\text{gross}} - C_{\text{transaction, USDT}} + CF_{\text{funding, USDT}}$$

### 5. Net Percentage Return per Trade
$$R_{\text{net}} = \frac{\text{PnL}_{\text{net}}}{N_{\text{entry}}}$$

### 6. Net Economic Expectancy
$$E[R_{\text{net}}] = \frac{1}{M} \sum_{m=1}^M R_{\text{net}, m}$$

### 7. Break-Even Gross Return
$$R_{\text{gross, breakeven}} = \frac{C_{\text{transaction, USDT}} - CF_{\text{funding, USDT}}}{N_{\text{entry}}}$$

---

## 2. FOUR-LEVEL ACCEPTANCE CRITERIA ARCHITECTURE

1. **Criterion 1 (Cost Scenario Resilience):** Evaluates strategy survival across the 15 bps, 20 bps, and 30 bps scenarios.
2. **Criterion 2 (Net Economic Expectancy):** Point estimate requirement: $E[R_{\text{net}}] > 0$ after all modeled costs and funding.
3. **Criterion 3 (Statistical Evidence):** Sample mean alone is INSUFFICIENT. Net positive expectancy must be confirmed via paired time-series Moving Block Bootstrap ($b=24$ bars, 10,000 resamples) with finite-sample empirical p-value $p < 0.05$ after Holm-Bonferroni family-wise error correction.
4. **Criterion 4 (Robustness):** Results across all three cost scenarios must be reported simultaneously in master tables to prevent post-hoc cherry-picking.
