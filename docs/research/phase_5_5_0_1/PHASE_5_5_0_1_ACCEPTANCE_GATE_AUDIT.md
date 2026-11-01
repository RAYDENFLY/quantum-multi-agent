# QUANTUM PHASE 5.5.0.1: ACCEPTANCE GATE AUDIT & CLARIFICATION

**Document Status:** `APPROVED_FOR_DESIGN`  
**Publication Timestamp:** `2026-11-01 20:29:46 UTC`  
**Associated Deliverable:** Workstream F (Acceptance Gate Governance)  

---

## 1. COMPREHENSIVE DEFINITION OF THE 12 ECONOMIC GATES

Phase 5.5.0.1 audits all 12 economic acceptance gates, defining exact mathematical formulas, measurement units, sample sizes, and zero-division handling:

### Gate 1: Positive Net Expectancy at Base Cost (15 bps)
- **Metric Formula:** $\mu_{\text{net, 15bps}} = \frac{1}{N} \sum_{i=1}^N (R_{\text{gross}, i} - 0.0015) > +0.0005$ ($+5.0$ bps).
- **Evaluation Period:** Segment 3 (Fold 5 retrospective evaluation).
- **Classification:** `HARD_REJECTION`. A strategy unable to generate $+5$ bps net expectancy under standard retail fees is economically unviable.

### Gate 2: Positive Net Expectancy at Conservative Cost (20 bps)
- **Metric Formula:** $\mu_{\text{net, 20bps}} = \frac{1}{N} \sum_{i=1}^N (R_{\text{gross}, i} - 0.0020) > 0.0$ ($0.0$ bps).
- **Classification:** `HARD_REJECTION`. Mandatory break-even gate under conservative friction.

### Gate 3: Statistical Significance of Net Return (Conservative 20 bps)
- **Metric Formula:** Lower bound of 95% Moving Block Bootstrap confidence interval: $\text{CI}_{0.025} > 0.0$ bps.
- **Resampling:** MBB with $b = 24$ bars, $B = 10,000$ iterations.
- **Classification:** `HARD_REJECTION`.

### Gate 4: Maximum Portfolio Drawdown
- **Metric Formula:** $\text{MDD} = \max_{t \in [0, T]} \frac{\text{Peak}_t - E_t}{\text{Peak}_t} \le 0.15$ ($15.0\%$).
- **Equity Definition:** Mark-to-market equity evaluated at every 5m candle close.
- **Classification:** `HARD_REJECTION`.

### Gate 5: Net Profit Factor at Conservative Cost (20 bps)
- **Metric Formula:** $\text{PF} = \frac{\sum_{R_{\text{net}} > 0} R_{\text{net}}}{\sum_{R_{\text{net}} < 0} |R_{\text{net}}|} \ge 1.15$.
- **Zero-Division Handling:** If $\sum |R_{\text{losses}}| = 0$ and $\sum R_{\text{gains}} > 0$, $\text{PF} = 999.0$. If both zero, $\text{PF} = 0.0$.
- **Classification:** `HARD_REJECTION`.

### Gate 6: Adequate Trade Sample Count
- **Metric Formula:** $N_{\text{trades}} \ge 100$ per evaluated specialist on Fold 5.
- **Statistical Rationale:** 100 trades is the minimal sample size to ensure asymptotic normality of bootstrap means under Central Limit Theorem.
- **Classification:** `HARD_REJECTION`.

### Gate 7: Temporal Stability Across Segments
- **Metric Formula:** $\mu_{\text{net}}(\text{Segment 2}) > 0$ and $\mu_{\text{net}}(\text{Segment 3}) > 0$.
- **Classification:** `CONDITIONAL_ACCEPTANCE`.

### Gate 8: Fleet Diversification (Monoculture Guardrail)
- **Metric Formula:** $\max_{s} \frac{\text{Net Profit}_s}{\text{Total Portfolio Net Profit}} \le 0.45$ ($45.0\%$).
- **Classification:** `CONDITIONAL_ACCEPTANCE`.

### Gate 9: Turnover and Fee Drag Ceiling
- **Metric Formula:** $\frac{\text{Total Fees Paid}}{\text{Total Gross Trading Gains}} \le 0.65$ ($65.0\%$).
- **Classification:** `CONDITIONAL_ACCEPTANCE`.

### Gate 10: Tail Risk Control (CVaR 95%)
- **Metric Formula:** $\text{CVaR}_{0.05} = \mathbb{E}[R \mid R \le \text{VaR}_{0.05}] \ge -3.0 \times d_{\text{SL}}$.
- **Classification:** `HARD_REJECTION`.

### Gate 11: Superiority Over Naive Baselines
- **Metric Formula:** $\text{Sharpe}(\text{Strategy}) > \max(\text{Sharpe}(\text{Always Long}), \text{Sharpe}(\text{Random Entry}))$.
- **Classification:** `HARD_REJECTION`.

### Gate 12: Directional Symmetry Proof
- **Metric Formula:** $\mu_{\text{gross}}(\text{Long Trades}) > 0$ and $\mu_{\text{gross}}(\text{Short Trades}) > 0$.
- **Classification:** `CONDITIONAL_ACCEPTANCE`.
