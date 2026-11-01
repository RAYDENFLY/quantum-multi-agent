# QUANTUM PHASE 5.5.0: STATISTICAL ACCEPTANCE CRITERIA

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-01 20:23:18 UTC`  
**Associated Deliverable:** Workstream I (Statistical Acceptance) & Workstream J (Economic Gates)  

---

## 1. FORMAL HYPOTHESIS TESTING FRAMEWORK

A positive sample mean net return alone is insufficient to establish economic viability. The primary statistical hypothesis is formulated as:

### Primary Hypothesis
$$H_0: \mathbb{E}[R_{\text{net}}] \le 0$$
$$H_1: \mathbb{E}[R_{\text{net}}] > 0$$
where $R_{\text{net}}$ is the realized return per trade after all modeled costs under the Conservative Cost Tier (20 bps round-trip).

### Resampling Methodology
- **Moving Block Bootstrap (MBB):** Block length $b = 24$ bars ($2$ hours), with $B = 10,000$ bootstrap iterations.
- **Confidence Intervals:** Nominal $95\%$ percentile confidence interval $[\text{CI}_{0.025}, \text{CI}_{0.975}]$.
- **Statistical Significance Requirement:** The lower $95\%$ confidence bound must be strictly greater than zero ($\text{CI}_{0.025} > 0.0$).
- **Multiple Testing Correction:** Holm-Bonferroni step-down correction applied across all 11 specialist hypotheses ($m = 11$, $\alpha = 0.05$).

---

## 2. THE 12 QUANTITATIVE ECONOMIC GATES

Phase 5.5 mandates evaluation against 12 unambiguous quantitative gates. The system is explicitly allowed to fail.

| Gate ID | Economic Gate Description | Numerical Pass Threshold | Gate Severity |
|---|---|---|---|
| **GATE_01** | Positive Net Expectancy (Base 15 bps) | $\mu_{\text{net}} > +5.0$ bps per trade | **HARD REJECTION** |
| **GATE_02** | Positive Net Expectancy (Conservative 20 bps) | $\mu_{\text{net}} > 0.0$ bps per trade | **HARD REJECTION** |
| **GATE_03** | Statistical Significance of Net Return | Lower 95% MBB CI $> 0.0$ bps | **HARD REJECTION** |
| **GATE_04** | Maximum Portfolio Drawdown | $\text{MDD} \le 15.0\%$ | **HARD REJECTION** |
| **GATE_05** | Net Profit Factor (Conservative 20 bps) | $\text{PF} \ge 1.15$ | **HARD REJECTION** |
| **GATE_06** | Adequate Trade Sample Size | $N_{\text{trades}} \ge 100$ per specialist (Fold 5) | **HARD REJECTION** |
| **GATE_07** | Temporal Stability Across Segments | Net return positive in both Segment 2 & Segment 3 | **CONDITIONAL ACCEPTANCE** |
| **GATE_08** | Fleet Diversification (No Monoculture) | Top specialist generates $\le 45\%$ of fleet profits | **CONDITIONAL ACCEPTANCE** |
| **GATE_09** | Turnover and Fee Drag Ceiling | Total fees $\le 65\%$ of gross trading profit | **CONDITIONAL ACCEPTANCE** |
| **GATE_10** | Tail Risk Control (CVaR 95%) | Mean tail loss $\le -3.0 \times d_{\text{SL}}$ | **HARD REJECTION** |
| **GATE_11** | Superiority Over Naive Baselines | Net Sharpe exceeds Always Long & Random Entry | **HARD REJECTION** |
| **GATE_12** | Directional Symmetry Proof | Long and Short trades both achieve positive gross PnL | **CONDITIONAL ACCEPTANCE** |

---

## 3. VERDICT TAXONOMY

At completion of Phase 5.5 execution, only four conclusive outcomes are authorized:
1. **`ECONOMICALLY_VIABLE`:** All 12 gates passed. System is authorized for prospective holdout review.
2. **`ECONOMICALLY_VIABLE_WITH_LIMITATIONS`:** All Hard Rejection gates passed; 1-2 Conditional gates flagged.
3. **`ECONOMICALLY_UNVIABLE`:** Any Hard Rejection gate failed. System rejected for live trading.
4. **`INSUFFICIENT_EVIDENCE`:** Data deficit or sample size prevents statistical determination.
