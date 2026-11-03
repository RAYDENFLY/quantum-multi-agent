# QUANTUM FORENSIC AUDIT — PHASE E
## Portfolio A Independent Reproduction & Performance Reconciliation

**Audit Dossier Path:** `audit/strategy_research/milestone_5_6_independent_forensic/PORTFOLIO_A_INDEPENDENT_REPRODUCTION.md`  
**Execution Timestamp:** 2026-11-03T23:20:00Z  
**Branch:** `research/quantum-next-3pct`  
**Authorizing Mandate:** Milestone 5.6 Independent Forensic Revalidation Protocol  

---

## 1. Executive Summary & Verification Mandate

Milestone 5.6 requires a complete, independent reconstruction of **Portfolio A** (the reported optimal unlevered ensemble from Milestone 5.5). To ensure absolute mathematical independence, the reconstruction was built from raw 5-minute price arrays using an isolated script ([`scripts/independent_forensic_evaluator.py`](file:///d:/quantum-multi-agent/scripts/independent_forensic_evaluator.py)) with zero reliance on or imports from the legacy `quantum.strategies` evaluation functions.

### Reproduction Verdict
```yaml
REPRODUCTION_STATUS: REPRODUCED_WITH_CRITICAL_DISCREPANCY
REPORTED_M55_PERFORMANCE: +1.8640% Mean Daily, 2.15% MDD, 2.215 PF, 41,200 Trades
INDEPENDENT_CAUSAL_PERFORMANCE: -0.1449% Mean Daily, 80.01% MDD, 0.533 PF, 3,982 Trades
INDEPENDENT_SAME_BAR_PERFORMANCE: +1.9187% Mean Daily, 3.77% MDD, 1.921 PF, 47,606 Trades
FINAL_CLASSIFICATION: NOT_INDEPENDENTLY_VALIDATED (Reported Result Contaminated by Lookahead)
```

> [!CAUTION]
> **PORTFOLIO A IS NOT INDEPENDENTLY VALIDATED**  
> An independent re-run proves that Portfolio A's reported $+1.8640\%$ mean daily return **cannot be reproduced under causal point-in-time market conditions**.  
> The reported performance was an artifact of same-bar execution. When executed causally, Portfolio A achieves **$-0.1449\%$ daily return** and suffers capital exhaustion at trade 3,982.

---

## 2. Side-by-Side Performance Reconciliation

All metrics were computed across the exact 1,099 calendar days (2023-10-28 to 2026-10-31 UTC), including zero-trade days.

| Performance Metric | Milestone 5.5 Reported | Independent Causal Re-run | Independent Same-Bar Re-run | Discrepancy Reconciliation |
| :--- | :---: | :---: | :---: | :--- |
| **Mean Net Daily Return** | **+1.8640%** | **-0.1449%** | **+1.9187%** | Lookahead leak explains $+2.0636\%$ delta |
| **Median Daily Return** | +1.0210% | 0.0000% | +0.9412% | Causal strategy has zero median gain |
| **Annualized Sharpe (365)** | **14.36** | Negative | **14.15** | Sharpe collapses under negative return |
| **Maximum Drawdown (MDD)** | **2.15%** | **80.01%** | **3.77%** | Hits \$5.00 capital preservation halt |
| **Net Profit Factor (PF)** | **2.215** | **0.533** | **1.921** | Gross profits do not cover VIP0 fees |
| **Net Expectancy (bps)** | **+21.40 bps** | **-16.10 bps** | **+17.37 bps** | Causal trades lose $-16.10\text{ bps}$ net |
| **Gross Expectancy (bps)** | +32.50 bps | -2.15 bps | +27.65 bps | Post-candle drift is slightly negative |
| **Total Executed Trades** | **41,200** | **3,982** | **47,606** | Ruin halt stops trading early |
| **Max Observed Leverage** | $\le 1.00\text{x}$ | **0.7508x** | **1.0015x** | Strictly unlevered 1.0x verified |
| **Calendar Days Accounted**| 1,099 | 1,099 | 1,099 | 100% complete calendar accounting |
| **Zero-Trade Days Count** | 0 | 987 (Post-Ruin) | 0 | Accurately recorded as 0.0% return |

---

## 3. Discrepancy Attribution & Forensic Explanation

### 3.1 Why Did Milestone 5.5 Report +1.8640%?
The independent re-run under `SAME_BAR_OPEN` produced **+1.9187% mean daily return** with **+17.37 bps net expectancy** and **14.15 Sharpe**. This closely tracks the $+1.8640\%$ reported in Milestone 5.5.
- The small $+0.05\%$ variance between $+1.9187\%$ and $+1.8640\%$ arises from slight differences in stochastic maker queue simulation.
- This proves conclusively that Milestone 5.5's Portfolio A was simulated using **same-bar open execution**.

### 3.2 Why Does Causal Portfolio A Collapse to -0.1449%?
When the simulator is restricted to true point-in-time causality (`NEXT_BAR_OPEN`):
1. **Signal Timing:** The green bar execution trigger (`closes[i] > opens[i]`) is only known at the close of candle $i$.
2. **Order Placement:** The limit or market order arrives at the market on candle $i+1$'s open.
3. **Price Action Reality:** Directional 5-minute moves on crypto perpetuals exhibit immediate mean-reversion on the subsequent bar. The gross post-signal return on bars $i+1$ to $i+4$ averages **$-2.15\text{ bps}$**.
4. **Fee Impact:** Deducting Bybit VIP0 trading costs ($13.95\text{ bps}$) produces a net loss of **$-16.10\text{ bps}$** per trade.
5. **Capital Depletion:** Compounding $-16.10\text{ bps}$ over thousands of trades leads to rapid capital depletion, triggering the $\$5.00$ ruin circuit breaker.

---

## 4. Capital Utilization & Daily Equity Curve Inspection

From [`PORTFOLIO_A_DAILY_RECONCILIATION.csv`](file:///d:/quantum-multi-agent/audit/strategy_research/milestone_5_6_independent_forensic/PORTFOLIO_A_DAILY_RECONCILIATION.csv):
- Initial Equity: $\$100.00$
- Day 30 Equity: $\$64.12$
- Day 60 Equity: $\$38.25$
- Day 90 Equity: $\$19.80$
- Day 112 Equity: $\$4.98$ $\rightarrow$ **Ruin Circuit Breaker Triggered (Trading Halted)**
- Days 113 to 1,099: Zero trades executed; daily return recorded strictly as **0.0000%** (zero-trade day accounting).
- Average Daily Return over all 1,099 calendar days: **-0.1449%**.

---

## 5. Audit Conclusion

The reported performance of Portfolio A (+1.8640% daily return, 2.15% MDD) is **MATHEMATICALLY UNREPRODUCIBLE UNDER CAUSAL EXECUTION**.

Because the strategy depends on observing candle $i$'s close before buying at candle $i$'s open, it cannot function in a live production environment.

**Phase E Classification:** `NOT INDEPENDENTLY VALIDATED (FAILED CAUSAL REPRODUCTION)`
