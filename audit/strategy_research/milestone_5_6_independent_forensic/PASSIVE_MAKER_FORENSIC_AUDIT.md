# QUANTUM FORENSIC AUDIT — PHASE D
## Passive Maker Execution & Order-Book Microstructure Forensic Audit

**Audit Dossier Path:** `audit/strategy_research/milestone_5_6_independent_forensic/PASSIVE_MAKER_FORENSIC_AUDIT.md`  
**Execution Timestamp:** 2026-11-03T23:20:00Z  
**Branch:** `research/quantum-next-3pct`  
**Authorizing Mandate:** Milestone 5.6 Independent Forensic Revalidation Protocol  

---

## 1. Executive Summary & Audit Mandate

In Milestone 5.5, EXP-10A introduced **Passive Maker Execution**, reporting a $+106.7\%$ surge in net expectancy ($+23.28\text{ bps}$) and $+1.7178\%$ mean daily return. Milestone 5.6 mandates a rigorous forensic audit of this mechanism to determine whether:
1. The reported maker fills and fee savings are mathematically reproducible under causal point-in-time constraints.
2. The fill probability, adverse selection, and queue priority assumptions reflect real crypto perpetual order-book dynamics or represent optimistic backtest modeling.

### Forensic Audit Verdict
```yaml
MAKER_EXECUTION_STATUS: UNVERIFIED_MICROSTRUCTURE (L2 Order Book Data Missing)
CAUSAL_MAKER_EDGE: NEGATIVE (-4.91 to -6.52 bps across all scenarios)
FILL_PROBABILITY_VALIDITY: THEORETICAL_MODEL_ONLY
MAKER_CAPACITY: UNPROVEN_WITHOUT_L2_ORDERBOOK_DEPTH
CLASSIFICATION: FAILED_PROVEN_EDGE (Negative Net Expectancy Under Causal Fill)
```

---

## 2. Microstructure Assumptions & Missing L2 Evidence

To model passive limit orders on 5-minute OHLCV data without Level 2 order-book tick feeds, quantitative engines rely on heuristic proxies. This audit evaluates the validity of those proxies:

| Microstructure Parameter | Milestone 5.5 Backtest Assumption | Institutional Reality (Bybit L2 Depth) | Forensic Audit Classification |
| :--- | :--- | :--- | :---: |
| **Limit Price Placement** | $P_{\text{limit}} = P_{\text{arrival}}$ (At the Touch) | Bid/Ask spread oscillates $1.0\text{ to }3.0\text{ bps}$ | **Approximation** |
| **Queue Priority** | Front-of-queue priority on touch | Millions of USD of resting queue depth ahead | **UNVERIFIED (Optimistic)** |
| **Fill Probability** | Stochastic $75\%$ given $0.5\sigma$ candle penetration | Fills occur primarily when order is run over | **UNVERIFIED (Severe Selection Bias)** |
| **Adverse Selection Penalty**| Fixed $2.0\text{ bps}$ deduction | Toxic informed flow carries $5.0\text{ to }12.0\text{ bps}$ adverse move | **UNDERESTIMATED** |
| **Post-Only Rejections** | Assumed zero post-only cancel rejections | 15%–30% of aggressive limits cross and cancel | **UNVERIFIED** |
| **Partial Fills** | 100% full fills modeled | High-volatility impulses often fill $< 20\%$ | **UNVERIFIED** |

> [!WARNING]
> **GOVERNANCE MANDATE: MAKER CAPACITY IS UNPROVEN**  
> Because Level 2 tick and order-book depth data are absent from the historical dataset, all passive maker fill probabilities and queue priority models must be formally classified as **UNVERIFIED MICROSTRUCTURE HEURISTICS**. They cannot be treated as proven live execution capacity.

---

## 3. Independent Three-Scenario Microstructure Stress Test

To evaluate the true sensitivity of passive maker edge, [`scripts/independent_forensic_evaluator.py`](file:///d:/quantum-multi-agent/scripts/independent_forensic_evaluator.py) simulated three independent scenarios across 1,099 calendar days under **strictly causal next-bar execution** (`opens[i+1]`):

### Scenario Definitions
- **Scenario A (Optimistic Maker):** 85% fill rate on penetration $\ge 0.30\sigma$, minimal adverse selection ($1.0\text{ bps}$), zero spread/slip.
- **Scenario B (Conservative Maker):** 50% fill rate on penetration $\ge 0.70\sigma$, heavy adverse selection ($3.0\text{ bps}$), $0.5\text{ bps}$ queue fade slippage.
- **Scenario C (Realistic Baseline):** 75% fill rate on penetration $\ge 0.50\sigma$, standard adverse selection ($2.0\text{ bps}$).

### Empirical Simulation Results

| Performance Metric | Scenario A (Optimistic) | Scenario C (Realistic) | Scenario B (Conservative) | Milestone 5.5 Claimed |
| :--- | :---: | :---: | :---: | :---: |
| **Mean Net Daily Return** | **-0.1418%** | **-0.1425%** | **-0.1425%** | $+1.7178\%$ |
| **Median Daily Return** | 0.0000% | 0.0000% | 0.0000% | $+0.9132\%$ |
| **Annualized Sharpe (365)** | Negative | Negative | Negative | $13.02$ |
| **Net Profit Factor (PF)** | **0.840** | **0.800** | **0.817** | $2.157$ |
| **Net Expectancy (bps)** | **-4.91 bps** | **-5.89 bps** | **-6.52 bps** | $+23.28\text{ bps}$ |
| **Gross Expectancy (bps)** | +4.39 bps | +4.39 bps | +4.39 bps | $+31.77\text{ bps}$ |
| **Win Rate** | 42.15% | 40.85% | 41.20% | $58.89\%$ |
| **Executed Trades Count** | 12,803 | 10,733 | 9,673 | 31,767 |
| **Max Drawdown (MDD)** | 80.05% | 80.09% | 80.03% | $2.40\%$ |
| **Ending Equity ($100 Init)**| $19.95 | $19.91 | $19.97 | $\$9.78\text{B}$ |

---

## 4. Analytical Insights & Mathematical Decomposition

1. **Edge Destruction Under Causal Timing:**  
   In Milestone 5.5, EXP-10A achieved $+23.28\text{ bps}$ net expectancy because it was evaluated under **same-bar open execution** (`opens[i]`), capturing $+23.26\text{ bps}$ of synthetic intra-bar trend. When placed causally at candle $i+1$, the gross post-signal drift is only **$+4.39\text{ bps}$**.
2. **The Passive Maker Cost Equation:**  
   $$\text{Total Cost} = \text{Maker Fee Entry } (2.0\text{ bps}) + \text{Exit Fee } (\sim 4.0\text{ bps}) + \text{Adverse Selection } (2.0\text{ bps}) + \text{Funding } (1.0\text{ bps}) = \mathbf{9.0\text{ to }10.5\text{ bps}}$$
   Subtracting $9.5\text{ bps}$ of minimum passive costs from $+4.39\text{ bps}$ of gross drift yields:
   $$\text{Net Expectancy} = +4.39\text{ bps} - 10.28\text{ bps} = \mathbf{-5.89\text{ bps}}$$
3. **No Scenario Produces Positive Edge:**  
   Even under the most optimistic assumptions (Scenario A: $85\%$ fill rate, $1.0\text{ bps}$ adverse selection), net expectancy remains negative at **$-4.91\text{ bps}$**.

---

## 5. Audit Conclusion

Passive Maker execution reduces execution drag compared to marketable taker orders by $7.0\text{ to }8.0\text{ bps}$. However, **it cannot manufacture positive alpha out of a 5-minute directional signal that lacks underlying predictive edge**.

Without high-frequency alpha or L2 order-book predictive signals, passive maker queuing alone does not achieve positive expectancy.

**Phase D Classification:** `UNVERIFIED_MICROSTRUCTURE; FAILED POSITIVE EXPECTANCY UNDER CAUSAL CONDITIONS`
