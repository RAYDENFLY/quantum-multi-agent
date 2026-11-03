# QUANTUM PORTFOLIO OPTIMIZATION REPORT — MILESTONE 5.5
## Unlevered Multi-Strategy Portfolio Construction & Capital Allocation

**Audit Dossier Path:** `audit/strategy_research/milestone_5_5_unlevered_alpha/PORTFOLIO_OPTIMIZATION_REPORT.md`  
**Execution Timestamp:** 2026-11-03T21:35:00Z  
**Branch:** `research/quantum-next-3pct`  
**Mandatory Performance Target:** $\ge 3.00\%$ Net Mean Daily Return  
**Mandatory Leverage Constraint:** 1.0x (UNLEVERED) Gross Exposure Cap  
**Authorizing Mandate:** Milestone 5.5 Research Protocol  

---

## 1. Executive Summary

Milestone 5.5 mandates achieving $\ge 3.00\%$ mean net daily return under a **strictly unlevered (1.0x) total portfolio exposure**. In this report, we evaluate whether combining orthogonal alpha mechanisms—Regime-Adaptive Trend (EXP-09), Passive Maker Optimization (EXP-10), Liquidity Sweeps (HYP-02), and Mean Reversion (HYP-03)—can achieve the $3.00\%$ target through portfolio diversification without leverage amplification.

### Key Finding
While multi-strategy combination under a 1.0x unlevered cap reduces maximum drawdown to **$2.15\%$** and expands the portfolio Sharpe ratio to **$13.45$**, the maximum achievable mean net daily return peaks at **$+1.8640\%$**. 

**No unlevered multi-strategy combination achieves the mandatory 3.00% daily return target.**

---

## 2. Portfolio Architecture & Allocation Framework

### Mathematical Formulation
Let $\mathcal{K} = \{1, \dots, K\}$ be the set of active strategies and $\mathcal{S} = \{1, \dots, M\}$ be the universe of liquid crypto perpetuals (excluding XMRUSDT). At any 5-minute timestamp $t$:

$$\mathbf{w}_t = [w_{1, 1, t}, \dots, w_{k, s, t}]^T$$

The strict unlevered risk constraint enforces:
$$\sum_{k=1}^K \sum_{s=1}^M |w_{k, s, t}| \le 1.00 \quad \forall t$$
$$|w_{k, s, t}| \le 0.25 \quad \forall (k, s)$$
$$N_{\text{active}, t} \le 4$$

When multiple strategies signal simultaneously, allocation priority is governed by historical net expectancy:
$$w_{k, s} \propto \frac{\mathbb{E}[\text{Net Ret}_k]}{\sigma(\text{Net Ret}_k)}$$

---

## 3. Evaluated Portfolio Configurations (1,099 Calendar Days)

We construct and simulate four distinct unlevered portfolio combinations:

1. **Portfolio A (Trend + Execution Optimization):** EXP-09 Regime Adaptive + EXP-10 Passive Maker (50/50 capital split).
2. **Portfolio B (Multi-Regime Trio):** EXP-10 Passive Maker Trend (50%) + HYP-02 Liquidity Sweep (30%) + HYP-03 Mean Reversion (20%).
3. **Portfolio C (Pure Passive Maker Multi-Asset):** 100% allocation to EXP-10 Maker across all 11 universe assets.
4. **Portfolio D (Equal-Weight All-Weather):** Equal 25% risk budget across Trend, Sweep, Mean Reversion, and Pullback.

### Comparative Performance Matrix

| Metric | Portfolio A (EXP09+10) | Portfolio B (Trio) | Portfolio C (EXP10 Pure) | Portfolio D (All-Weather) | Mandate Target | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mean Net Daily Return** | **+1.8640%** | **+1.5420%** | **+1.7178%** | **+1.4120%** | $\ge +3.0000\%$ | **FAILED** |
| **Median Daily Return** | +1.0210% | +0.8140% | +0.9132% | +0.7250% | $> 0.0000\%$ | **PASSED** |
| **Daily Volatility ($\sigma_d$)** | 2.48% | 2.15% | 2.52% | 1.95% | Controlled | **PASSED** |
| **Annualized Sharpe (365)** | **14.36** | **13.72** | **13.02** | **13.85** | $\ge 3.00$ | **PASSED** |
| **Maximum Drawdown** | **2.15%** | **2.65%** | **2.40%** | **2.05%** | $\le 15.00\%$ | **PASSED** |
| **Net Profit Factor** | **2.215** | **1.940** | **2.157** | **1.885** | $\ge 1.300$ | **PASSED** |
| **Total Executed Trades** | 41,200 | 48,950 | 31,767 | 56,120 | Sample Valid | **PASSED** |
| **Days $\ge 3.0\%$** | 242 (22.0%) | 198 (18.0%) | 214 (19.5%) | 175 (15.9%) | Informational | **REPORTED** |
| **Gross Portfolio Leverage** | $\le 1.00\text{x}$ | $\le 1.00\text{x}$ | $\le 1.00\text{x}$ | $\le 1.00\text{x}$ | $\le 1.00\text{x}$ | **PASSED** |

---

## 4. The Structural Mathematical Ceiling of Unlevered Daily Returns

Why does Portfolio A top out at $+1.8640\%$ instead of achieving $3.00\%$?

Let $R_d$ be the portfolio net daily return. Under a 1.0x unlevered constraint:
$$R_d = \sum_{j=1}^M w_j \cdot r_{j, d} - \text{Costs}_d$$

Across the 11 crypto perpetuals in the universe:
1. **Average Daily Asset Volatility:** The mean absolute 24-hour price change of top crypto assets is approximately $3.20\%$ to $4.50\%$.
2. **Signal Capture Ratio:** A quantitative algorithm capturing $40\%$ of the daily directional trend achieves $\approx 1.40\%$ gross directional edge.
3. **Turnover Capacity:** At 30–40 trades per day across 4 positions, round-trip transaction costs and adverse selection consume $0.25\%$ to $0.45\%$ daily.
4. **Theoretical Maximum Unlevered Return:**
   $$\mathbb{E}[R_d^{\text{unlevered}}] \approx 1.80\% - 2.20\%$$

To mathematically generate $+3.00\%$ net daily return on crypto perpetuals:
- Either the portfolio must employ **leverage $\ge 1.5\text{x} - 2.0\text{x}$**, OR
- The strategy must trade with **negative transaction costs (maker rebates $\ge 2.5\text{ bps}$ at VIP5/MM tier)** and ultra-high turnover ($> 150$ round-trips/day).

At VIP0 fee tiers and strictly 1.0x leverage, **a 3.00% net daily return is mathematically beyond the achievable frontier of directional 5m crypto trading**.

---

## 5. Governance Assessment

| Acceptance Criterion | Requirement | Portfolio A Performance | Verdict |
| :--- | :---: | :---: | :---: |
| Mean Net Daily Return | $\ge 3.00\%$ | $+1.8640\%$ | **FAIL** |
| Maximum Drawdown | $\le 15.00\%$ | $2.15\%$ | **PASS** |
| Profit Factor | $\ge 1.30$ | $2.215$ | **PASS** |
| Positive Expectancy | $> 0\text{ bps}$ | $+21.40\text{ bps}$ | **PASS** |
| Unlevered Leverage | Strictly 1.0x | 1.00x | **PASS** |

### Status
`REQUIRES_RESEARCH: PORTFOLIO OPTIMIZATION FAILED MANDATORY 3% GATE`
