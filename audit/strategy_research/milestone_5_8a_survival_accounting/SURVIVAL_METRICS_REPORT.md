# QUANTUM ACCOUNTING AUDIT — MILESTONE 5.8A
## Capital Survival Metrics & Bootstrap Ruin Probability Report

**Audit Dossier Path:** `audit/strategy_research/milestone_5_8a_survival_accounting/SURVIVAL_METRICS_REPORT.md`  
**Execution Timestamp:** 2026-11-03T23:58:00Z  
**Branch:** `research/quantum-next-3pct`  
**Authorizing Mandate:** Milestone 5.8A Terminal Equity & Survival Accounting Protocol  

---

## 1. Executive Summary & Survival Assessment

Milestone 5.8A introduces formal **Capital Survival Metrics** to measure an algorithm's operational longevity, capital depletion risk, and probability of ruin. 

A central principle of this report:
> *A quantitative strategy must never be judged as 'low-risk' merely because it executes fewer trades or survives longer under higher initial balances. If trade expectancy is negative, ruin is mathematically certain.*

### Survival Metrics Scorecard (Stored in `SURVIVAL_METRICS.json`)
```yaml
EMPIRICAL_RUIN_PROBABILITY_BOOTSTRAP: 100.00% (2,000 / 2,000 Resampled Paths Hit Ruin)
CALENDAR_OPERATIONAL_RATIO: 10.74% (118 Active Trading Days / 1,099 Total Days)
TIME_TO_OPERATIONAL_HALT:
  $100_CAPITAL: Median 79.0 Days (Min 45, Max 142 Days)
  $1,000_CAPITAL: Median 193.0 Days (Min 110, Max 315 Days)
MAXIMUM_CAPITAL_DEPLETION:
  $100_CAPITAL: 80.03% (Depleted to $19.965)
  $1,000_CAPITAL: 98.00% (Depleted to $19.965)
  $10,000_CAPITAL: 99.80% (Depleted to $19.982)
RECOVERY_POTENTIAL_POST_HALT: 0.00% (Zero autonomous recovery capacity)
AVERAGE_CAPITAL_UTILIZATION: 45.50% Gross Exposure (Peak: 75.08%)
SURVIVAL_CLASSIFICATION: ZERO_LONG_TERM_VIABILITY (Certain Ruin)
```

---

## 2. Stationary Block Bootstrap Ruin Probability ($B = 2,000$)

Using Politis & Romano (1994) stationary block bootstrap with expected block length $L = 10$ days, $2,000$ synthetic 3-year equity trajectories were simulated using empirical active daily returns:

### Bootstrap Simulation Findings

| Initial Capital | Ruin Threshold | Resamples Tested | Ruin Events | Empirical Ruin Probability | Median Days to Halt | Min Days | Max Days |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$100.00** | **$20.00** | 2,000 | 2,000 | **100.00%** | **79.0 Days** | 45 Days | 142 Days |
| **$1,000.00** | **$20.00** | 2,000 | 2,000 | **100.00%** | **193.0 Days** | 110 Days | 315 Days |

```
Distribution of Days to Starvation Halt ($100 Capital, B=2,000):
  10th Percentile: 58 Days
  25th Percentile: 68 Days
  50th Percentile (Median): 79 Days
  75th Percentile: 94 Days
  90th Percentile: 112 Days
  99th Percentile: 135 Days
  P(Halt <= 180 Days): 100.00%
```

Every single resampled path breached the $\$20.00$ operational starvation threshold well within the 1,099-day horizon.

---

## 3. Operational Longevity & Capital Depletion Metrics

### 3.1 Percentage of Calendar Days Operational
$$\text{Operational Ratio} = \frac{N_{\text{active}}}{N_{\text{total}}} = \frac{118}{1099} = \mathbf{10.74\%}$$
The algorithm was dead or paralyzed for **$89.26\%$** of the backtest calendar.

### 3.2 Maximum Capital Depletion
$$\text{Depletion} = \frac{\text{Initial Capital} - \text{Terminal Equity}}{\text{Initial Capital}} \times 100\%$$
- At $\$100$ initial capital: Depletion is **80.03%**.
- At $\$1,000$ initial capital: Depletion is **98.00%**.
- At $\$10,000$ initial capital: Depletion is **99.80%**.

### 3.3 Recovery Potential Post-Halt
$$\text{Recovery Potential} = \mathbf{0.00\%}$$
Because all order entries are rejected by exchange lot minimums once equity drops below $\$20.00$, the strategy has **zero internal mechanism to recover drawdown**. It cannot generate alpha from idle cash.

### 3.4 Capital Utilization
- Position sizing limits each trade to $25\%$ equity ($w_j \le 0.25$).
- During the 118 active days:
  - Average concurrent positions: **1.82 positions**.
  - Average gross leverage: **0.4550x** ($45.5\%$ capital utilized).
  - Peak gross leverage: **0.7508x** ($75.08\%$ capital utilized).
  - Cash drag: **54.5%** of capital sat idle in cash even during the active phase.

---

## 4. Audit Conclusion

The survival metrics prove conclusively that **Portfolio A suffers from mathematical certainty of ruin**.

The low trade count of 3,562–3,982 was not a product of selective high-conviction filtering, but the direct result of premature operational death.

**Deliverable Status:** `VERIFIED (SURVIVAL METRICS & 100% RUIN PROBABILITY CONFIRMED)`
