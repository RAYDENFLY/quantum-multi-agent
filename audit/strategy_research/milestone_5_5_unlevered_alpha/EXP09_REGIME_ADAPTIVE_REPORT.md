# QUANTUM EXPERIMENT REPORT — EXP-09
## Regime-Adaptive Structural Alpha (Strictly 1.0x Unlevered)

**Audit Dossier Path:** `audit/strategy_research/milestone_5_5_unlevered_alpha/EXP09_REGIME_ADAPTIVE_REPORT.md`  
**Execution Timestamp:** 2026-11-03T21:30:00Z  
**Branch:** `research/quantum-next-3pct`  
**Mandatory Performance Target:** $\ge 3.00\%$ Net Mean Daily Return  
**Mandatory Leverage Constraint:** 1.0x (UNLEVERED) Gross Exposure Cap  
**Authorizing Mandate:** Milestone 5.5 Research Protocol  

---

## 1. Executive Summary

EXP-09 investigates whether regime-conditioned parameter adaptation can elevate unlevered returns to the non-negotiable $\ge 3.00\%$ daily benchmark. Building on the findings of Phase A (which proved that High-Volatility Bear regimes produce $+3.0945\%$ daily return whereas Low-Volatility regimes dilute portfolio expectancy), EXP-09 implements dynamic regime classification, variable hurdle rates, and regime-specific barrier management under a strict 1.0x total portfolio leverage limit.

### Performance Scorecard (1,099 Calendar Days)

| Metric | Baseline EXP-08 (1.0x Norm) | EXP-09 (Regime Adaptive 1.0x) | Milestone Target | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Mean Net Daily Return** | +0.6732% | **+1.0383%** | $\ge +3.0000\%$ | **FAILED** |
| **Median Daily Return** | +0.0000% | **+0.4033%** | $> 0.0000\%$ | **PASSED** |
| **Annualized Sharpe (365)** | 5.21 | **7.77** | $\ge 3.00$ | **PASSED** |
| **Maximum Drawdown (MDD)** | 6.84% | **15.52%** | $\le 15.00\%$ | **FAILED** |
| **Net Profit Factor (PF)** | 1.495 | **1.207** | $\ge 1.300$ | **FAILED** |
| **Net Expectancy (bps/trade)** | +11.36 bps | **+6.61 bps** | $> 0.00\text{ bps}$ | **PASSED** |
| **Total Executed Trades** | 25,694 | **67,483** | Statistically Valid | **PASSED** |
| **Effective Gross Leverage** | 1.00x | **1.00x** | $\le 1.00\text{x}$ | **PASSED** |

> [!WARNING]
> While EXP-09 expands mean daily return from $+0.6732\%$ to $+1.0383\%$ through increased turnover, it falls drastically short of the required $3.00\%$ daily return hurdle. Furthermore, its maximum drawdown ($15.52\%$) slightly violates the $15.0\%$ risk budget, and profit factor decays from $1.495$ to $1.207$.

---

## 2. Mathematical Formulation & Architecture

EXP-09 partitions the continuous market state into four mutually exclusive regimes using causal rolling 20-period volatility $\sigma_{20}$, 1-hour trend $r_{12}$, and volatility expansion ratio $\text{VER} = \sigma_{20} / \sigma_{96}$:

$$\mathcal{R}_t = \begin{cases}
\text{HIGH\_VOL\_BEAR}, & \sigma_{20, t} \ge \tilde{\sigma}_{20} \land r_{12, t} < 0 \\
\text{HIGH\_VOL\_BULL}, & \sigma_{20, t} \ge \tilde{\sigma}_{20} \land r_{12, t} \ge 0 \\
\text{LOW\_VOL\_BULL},  & \sigma_{20, t} < \tilde{\sigma}_{20} \land r_{12, t} \ge 0 \\
\text{LOW\_VOL\_BEAR},  & \sigma_{20, t} < \tilde{\sigma}_{20} \land r_{12, t} < 0
\end{cases}$$

### Parameter Adaptation Matrix

| Parameter | High-Vol Bear | High-Vol Bull | Low-Vol Regimes |
| :--- | :---: | :---: | :---: |
| **Required Trend Hurdle ($|r_{12}|$)** | $\ge 75\text{ bps}$ | $\ge 75\text{ bps}$ | $\ge 100\text{ bps}$ |
| **Volume Expansion Ratio ($\text{VER}$)** | $\ge 1.08$ | $\ge 1.08$ | $\ge 1.15$ |
| **Stop-Loss Multiplier ($\text{SL}_\sigma$)** | $2.00\sigma$ | $2.00\sigma$ | $1.50\sigma$ |
| **Take-Profit 1 ($\text{TP1}_\sigma$)** | $2.50\sigma$ | $2.50\sigma$ | $1.80\sigma$ |
| **Take-Profit 2 ($\text{TP2}_\sigma$)** | $4.50\sigma$ | $4.00\sigma$ | $2.50\sigma$ |
| **Max Holding Horizon ($H$)** | 4 bars (20m) | 4 bars (20m) | 2 bars (10m) |
| **Max Capital per Symbol** | 0.25x | 0.25x | 0.25x |

### Capital Allocation & Leverage Hard Cap
To ensure zero leverage amplification:
$$N_{\text{max}} = 4, \quad w_j \le 0.25, \quad \sum_{j=1}^{N_{\text{active}}} w_j \le 1.00$$

---

## 3. Empirical Results & Performance Breakdown

### 3.1 Regime-Specific Attribution

```
+-------------------+----------------+-------------+------------+---------------+
| Regime            | Trade Count    | Win Rate    | Net Exp    | Total Net PnL |
+-------------------+----------------+-------------+------------+---------------+
| HIGH_VOL_BEAR     | 24,115 (35.7%) | 51.2%       | +12.44 bps | +$3,412,890   |
| HIGH_VOL_BULL     | 21,804 (32.3%) | 48.9%       | +6.82 bps  | +$1,845,120   |
| LOW_VOL_BULL      | 11,280 (16.7%) | 43.1%       | -0.85 bps  | -$112,400     |
| LOW_VOL_BEAR      | 10,284 (15.2%) | 42.5%       | -1.42 bps  | -$189,200     |
+-------------------+----------------+-------------+------------+---------------+
```

1. **High-Vol Bear Remains Alpha Engine:** 70% of cumulative gains originate in High-Vol Bear regimes.
2. **Low-Vol Dilution Persists:** Despite tightening the entry filters to $100\text{ bps}$ trend and $1.15\text{ VER}$, trades executed in Low-Vol regimes exhibit negative net expectancy after VIP0 transaction costs.
3. **Turnover Drag:** Increasing trade count from 25,694 to 67,483 multiplied gross transaction fees to over $\$1.4\text{M}$ total cost drag, suppressing net expectancy from $+11.36\text{ bps}$ down to $+6.61\text{ bps}$.

---

## 4. Forensic Evaluation & Gate Compliance

1. **Target Return Compliance:** Reached $+1.0383\%$, missing the $3.00\%$ threshold by $-1.9617\%$.
2. **Drawdown Compliance:** Breached limit ($15.52\% > 15.00\%$) during the March 2024 low-vol chop regime.
3. **Profit Factor Compliance:** Decayed to $1.207$, failing the $\ge 1.30$ requirement.

### Scientific Verdict
EXP-09 demonstrates that adaptive filtering improves turnover and lifts daily return from $+0.67\%$ to $+1.04\%$ at 1.0x unlevered leverage. However, parameter adaptation alone cannot compensate for the structural friction of taker fees in low-vol regimes. EXP-09 fails backtest qualification.
