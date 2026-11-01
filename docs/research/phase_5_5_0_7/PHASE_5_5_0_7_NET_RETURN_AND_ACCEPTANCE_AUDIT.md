# QUANTUM PHASE 5.5.0.7: NET RETURN AND ACCEPTANCE HIERARCHY AUDIT

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-01 21:20:00 UTC`  
**Associated Task:** Task C (Net Return and Acceptance Hierarchy)  
**Operational Mode:** `READ_ONLY_VERIFICATION`  

---

## 1. NET RETURN FORMULATION AUDIT

Phase 5.5.0.6 defines the net economic trade return as:

$$R_{\text{net}} = R_{\text{gross}} - C_{\text{transaction, normalized}} + \frac{CF_{\text{funding, total}}}{N_{\text{entry}}}$$

### Component-by-Component Consistency Check
1. **Dimension Compatibility:**
   - Gross Return: $R_{\text{gross}} = \frac{\text{PnL}_{\text{gross}}}{N_{\text{entry}}}$ (dimensionless decimal).
   - Normalized Transaction Cost: $C_{\text{transaction, normalized}} = \frac{C_{\text{transaction, USDT}}}{N_{\text{entry}}}$ (dimensionless decimal).
   - Normalized Funding: $\frac{CF_{\text{funding, total}}}{N_{\text{entry}}}$ (dimensionless decimal).
   - *Status:* `MATHEMATICALLY_VERIFIED`. All three terms share identical dimensions and canonical denominator $N_{\text{entry}}$.
2. **Margin and Leverage Isolation:**
   - Execution notional $N_{\text{entry}} = Q \times P_{\text{entry}}$ is strictly the face value of the contract.
   - Account margin equity ($E_0$) and leverage multiplier ($L$) do not enter the per-trade return equation. This prevents artificial inflation of percentage returns via leverage.
   - *Status:* `MATHEMATICALLY_VERIFIED`.
3. **Directional PnL Consistency:**
   - Long ($d = +1$): $\text{PnL}_{\text{gross}} = Q (P_{\text{exit}} - P_{\text{entry}})$. Profitable when $P_{\text{exit}} > P_{\text{entry}}$.
   - Short ($d = -1$): $\text{PnL}_{\text{gross}} = Q (P_{\text{entry}} - P_{\text{exit}})$. Profitable when $P_{\text{exit}} < P_{\text{entry}}$.
   - *Status:* `MATHEMATICALLY_VERIFIED`.

---

## 2. AUDIT OF THE FOUR-LEVEL ACCEPTANCE HIERARCHY (C1)

We audit the four acceptance criteria levels defined in Phase 5.5.0.6:

| Level | Name | Purpose | Mathematical Criterion | Input Metrics | Nature | Status & Limitations |
|---|---|---|---|---|---|---|
| **Level 1** | Cost Scenario Resilience | Evaluates strategy survival across varied friction tiers. | Strategy evaluated at $C_{\text{round-trip}} \in \{15, 20, 30\}$ bps. | Trade distributions across 3 friction tiers. | Robustness / Scenario Sweep | `PASS_WITH_LIMITATIONS`. Requires human decision (DEC_04) on which scenario is binding. |
| **Level 2** | Net Economic Expectancy | Verifies non-negative sample trading expectancy. | $E[R_{\text{net}}] = \frac{1}{M} \sum_{m=1}^M R_{\text{net}, m} > 0$ | Sample mean of net trade returns. | Descriptive Point Estimate | `PASS_WITH_LIMITATIONS`. Point estimate only; does not prove statistical significance. |
| **Level 3** | Statistical Significance | Rejects null hypothesis of zero or negative expectancy. | $H_0: \mu_{\text{net}} \le 0$ vs $H_1: \mu_{\text{net}} > 0$; Paired MBB ($b=24$, 10,000 resamples), $p_{\text{empirical}} < 0.05$ after Holm-Bonferroni. | Block-bootstrapped trade returns, empirical p-values. | Inferential Hypothesis Test | `PASS_WITH_LIMITATIONS`. Family size $K$ for multiple testing not explicitly fixed. |
| **Level 4** | Anti-Cherry-Picking Robustness | Prevents selective reporting of winning parameter slices. | Simultaneous disaggregated reporting across Long, Short, Combined for all 3 cost tiers. | Master results table completeness check. | Governance / Reporting Standard | `PASS`. Fully specified and verifiable. |

---

## 3. STATISTICAL INFERENCE LIMITATIONS (C2)

Our audit identifies four critical statistical inference limitations in the current Phase 5.5 design:

### 1. Serial and Temporal Dependence of Overlapping Trades
- The specified Moving Block Bootstrap uses block length $b = 24$ bars (2 hours).
- In the frozen triple-barrier design, trade holding times range from 1 bar (5 minutes) up to 288 bars (24 hours).
- When a position is open for 144 bars, adjacent trade observations share underlying market price trajectories, causing **severe serial autocorrelation** that violates independence.
- A 24-bar block bootstrap on trade-level returns does NOT capture dependence extending across 144 to 288 bars.
- *Limitation:* The bootstrap block length must be calibrated to the maximum trade holding period, or resampling must occur on continuous calendar-time equity curves rather than trade arrays.

### 2. Overlapping Trades and Multi-Asset Concurrency
- Multiple specialists may enter positions concurrently (e.g. BTC and ETH simultaneously).
- Market-wide volatility shocks (liquidation cascades) affect all open trades simultaneously, generating cross-sectional return covariance.
- Treating asset trades as independent samples inflates effective degrees of freedom.

### 3. Multiple Testing Family Size ($K$) Ambiguity
- Phase 5.5.0.6 specifies Holm-Bonferroni correction, but does not fix the hypothesis family size $K$:
  - Asset level: $K = 11$ (11 specialists).
  - Directional level: $K = 11 \times 3 = 33$ (Long, Short, Combined).
  - Scenario level: $K = 33 \times 3 = 99$ (across 15, 20, 30 bps tiers).
- The family size $K$ must be formally fixed prior to any execution to prevent post-hoc significance inflation.

### 4. Point Estimate Distinction
- **CRITICAL DISTINCTION:** $E[R_{\text{net}}] > 0$ (Level 2) is strictly a sample mean condition. A strategy with $E[R_{\text{net}}] = +0.5$ bps may have $p = 0.42$ under bootstrap testing. Level 2 must never be presented as proof of statistically significant profitability.
