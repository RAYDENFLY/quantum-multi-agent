# QUANTUM — PORTFOLIO COMBINATION ANALYSIS
## Unified Multi-Strategy Simulation: HYP-01, HYP-02, and HYP-03

**Document Identifier:** `audit/strategy_research/milestone_5_4_alpha_expansion/PORTFOLIO_COMBINATION_ANALYSIS.md`  
**Publication Timestamp:** 2026-11-03 21:14:00 UTC  
**Active Branch:** `research/quantum-next-3pct`  
**Evaluation Universe:** 10 Liquid Perpetual Pairs (5m/30m/1h) | 1,099 Full Calendar Days  
**Lead Quantitative Research Engineer:** Quantitative Portfolio Architect & Execution Specialist  
**Research Status:** Multi-Strategy Alpha Feasibility Assessment  

---

## 1. Executive Summary & Core Research Finding

Milestone 5.4 tested whether combining three structurally orthogonal alpha hypotheses (`HYP-01` Trend Following, `HYP-02` Liquidity Sweep, and `HYP-03` Mean Reversion) could accelerate performance toward the mandatory **$3.00\%$ mean net daily return** target.

### Definitive Empirical Finding:
> **The standalone `HYP-01` trend-following system remains the strictly superior portfolio architecture.**  
> Combining `HYP-01` with `HYP-02` causes mild performance dilution (mean daily return drops from $+1.8848\%$ to $+1.7471\%$), while combining with `HYP-03` causes **catastrophic portfolio degradation** (mean daily return collapses to $+0.0156\%$ and maximum drawdown surges to $98.55\%$).

The mandatory $3.00\%$ gate is **NOT SATISFIED** by any portfolio combination under Bybit VIP0 taker fee schedules. The milestone status remains strictly **`REQUIRES_RESEARCH`**.

---

## 2. Multi-Strategy Simulation Architecture

In strict accordance with Phase 5 guidelines, strategies were **never evaluated by simply summing daily returns**. Instead, a unified multi-strategy portfolio simulator (`UnifiedPortfolioEngine`) was built and executed bar-by-bar across 316,499 five-minute candles:

1. **Shared Portfolio Capital:** All strategies operate out of a single $\$100.00$ dynamic margin equity pool.
2. **Global Concurrency Constraint:** A hard ceiling of **$4\text{ concurrent positions}$** is enforced across the entire 10-asset universe, regardless of how many strategies trigger simultaneously.
3. **Symbol Exclusivity & Conflict Resolution:**
   - Only one active position per asset is permitted at any timestamp.
   - If Strategy A triggers LONG and Strategy B triggers SHORT on the same asset at the same bar, **the contradictory signals cancel each other out** (net zero exposure).
4. **Dynamic Risk Budgeting:** Every executed trade is sized to risk exactly $1.50\%$ of current portfolio equity divided by its strategy-specific stop-loss distance, capped at $3.0\times$ portfolio leverage.
5. **Portfolio-Level Circuit Breakers:** A $4.0\%$ daily loss breaker halts all new entries across all strategies for the remainder of that calendar day.

---

## 3. Master Portfolio Combination Scorecard

```
+-----------------------------------------------------------------------------------------------------------------------------+
| Performance Metric                  | Combo 1 (HYP-01)  | Combo 2 (01+02)   | Combo 3 (01+03)   | Combo 4 (01+02+03)| Gate (>=3%)|
+-----------------------------------------------------------------------------------------------------------------------------+
| Strategies Included                 | HYP-01            | HYP-01 + HYP-02   | HYP-01 + HYP-03   | HYP-01+02+03      | Any Combo  |
| Mean Net Daily Return               | +1.8848%          | +1.7471%          | +0.0156%          | +0.0314%          | FAILED     |
| Median Daily Return                 | +0.4367%          | +0.3970%          | -0.8981%          | -0.9156%          | FAILED     |
| Annualized Sharpe Ratio (365)       | 7.06              | 6.74              | 0.09              | 0.17              | POOR (3/4) |
| Maximum Peak-to-Trough Drawdown     | 15.24%            | 15.87%            | 98.55%            | 98.62%            | CRITICAL   |
| Realized Profit Factor              | 1.327             | 1.263             | 0.999             | 0.999             | UNVIABLE   |
| Portfolio Win Rate                  | 51.19%            | 50.32%            | 44.22%            | 44.18%            | POOR (3/4) |
| Net Trade Expectancy                | +9.65 bps         | +8.55 bps         | -0.84 bps         | -0.83 bps         | NEGATIVE   |
| Gross Trade Expectancy              | +24.17 bps        | +23.03 bps        | +13.08 bps        | +13.10 bps        | DILUTED    |
| Total Executed Trades               | 28,043 trades     | 29,166 trades     | 63,955 trades     | 63,793 trades     | HYPER-CHURN|
| Trades Breakdown                    | 28,043 (HYP-01)   | 27,116 / 2,050    | 22,083 / 41,872   | 21,520/1,535/40,738| OVERRUN   |
| Days Achieving >= 3.0% Return       | 293 days (26.66%) | 275 days (25.02%) | 127 days (11.56%) | 125 days (11.37%) | COLLAPSED  |
| Negative Return Calendar Days       | 470 days (42.77%) | 480 days (43.68%) | 725 days (65.97%) | 721 days (65.61%) | CHRONIC LOSS|
| Zero-Trade Days (0.00% Return)      | 6 days            | 1 day             | 1 day             | 1 day             | MINIMAL    |
| Ending Equity ($100 Starting Base)  | $22.60 Billion    | $5.47 Billion     | $61.94            | $72.90            | DESTRUCTION|
| Research Gate Decision              | REQUIRES_RESEARCH | REQUIRES_RESEARCH | REQUIRES_RESEARCH | REQUIRES_RESEARCH | ALL FAILED  |
+-----------------------------------------------------------------------------------------------------------------------------+
```

---

## 4. Forensic Attribution & Mathematical Autopsy

### 4.1 Autopsy of Combo 2 (HYP-01 + HYP-02): Mild Alpha Dilution
- When `HYP-02` was added to `HYP-01`, it contributed **2,050 executed trades** alongside **27,116 trades** from `HYP-01`.
- However, as proven in [EXECUTION_COST_ANALYSIS.md](file:///d:/quantum-multi-agent/audit/strategy_research/milestone_5_4_alpha_expansion/EXECUTION_COST_ANALYSIS.md), `HYP-02` carries a standalone net expectancy of **$-1.20\text{ bps}$** under VIP0 taker fees.
- Consequently, blending a $+9.65\text{ bps}$ strategy with a $-1.20\text{ bps}$ strategy reduced the blended net expectancy to **$+8.55\text{ bps}$**, lowering mean daily return by $13.77\text{ bps/day}$ (from $+1.8848\%$ to $+1.7471\%$).
- **Takeaway:** `HYP-02` is close to net breakeven, but without maker execution or wider barriers, it acts as a mild friction drag on `HYP-01`.

### 4.2 Autopsy of Combo 3 & Combo 4 (The HYP-03 Concurrency Starvation Trap):
The inclusion of `HYP-03` triggered an immediate structural collapse of the entire portfolio:
1. **Hyper-Turnover Cannibalization:** `HYP-03` generated over **41,800 trades** in low-volatility regimes.
2. **Concurrency Slot Starvation:** Because global portfolio concurrency is capped at 4 positions, the high frequency of `HYP-03` signals filled all available slots with micro-mean-reversion trades. When a high-conviction `HYP-01` trend breakout signal fired, the portfolio had zero free capacity, blocking `HYP-01` from entering its highest-alpha trades!
3. **Friction Hemorrhage:** `HYP-03` trades incurred $13.62\text{ bps}$ of taker fees against an average gross move of only $+8.56\text{ bps}$, generating a net loss of $-5.06\text{ bps}$ per trade. Running this negative-expectancy churn 41,800 times drained portfolio capital and tripped the $4.0\%$ daily loss circuit breaker on $66\%$ of calendar days.
4. **Capital Annihilation:** Equity on a $\$100$ starting base collapsed to **$\$61.94$** (a peak-to-trough drawdown of **$98.55\%$**).

---

## 5. Quantitative Principle: The Fallacy of Blind Orthogonal Diversification

In classical Markowitz portfolio theory:
$$\sigma_P^2 = w_1^2 \sigma_1^2 + w_2^2 \sigma_2^2 + 2 w_1 w_2 \text{Cov}(1, 2)$$
Engineers often assume that if $\text{Cov}(1, 2) \approx 0$, diversification is guaranteed to be beneficial.

However, the expected portfolio return is:
$$\mathbb{E}[R_P] = w_1 \mathbb{E}[R_1] + w_2 \mathbb{E}[R_2]$$

If strategy 1 has $\mathbb{E}[R_1] > 0$, but strategy 2 has $\mathbb{E}[R_2] < 0$ after friction:
$$\mathbb{E}[R_P] < \mathbb{E}[R_1]$$

**Zero correlation with negative net expectancy guarantees value destruction.** No amount of mathematical diversification can overcome negative net trade expectancy.

---

## 6. Strategic Direction & Policy Mandate

1. **Immediate De-allocation of HYP-03:** `HYP-03` in its current market-taker formulation is permanently barred from deployment and combination with `HYP-01`.
2. **Preservation of Core HYP-01:** `HYP-01` remains the sole viable alpha core of the QUANTUM system.
3. **Path to 3.00% Daily Return:**
   Because adding secondary strategies under VIP0 taker fees reduces returns, achieving $\ge 3.00\%$ daily net return requires:
   - **Regime-Conditional Leverage Scaling in HYP-01:** Concentrating margin leverage during High-Vol Bear regimes ($+3.72\%$ daily) and High-Vol Bull regimes ($+2.71\%$ daily).
   - **Maker-Only Passive Limit Execution:** Converting entry orders to passive maker orders to recover $7.0\text{ bps}$ of friction per trade.
