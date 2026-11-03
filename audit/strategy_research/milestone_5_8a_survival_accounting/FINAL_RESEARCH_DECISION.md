# QUANTUM RESEARCH GOVERNANCE — MILESTONE 5.8A
## Final Research Decision, Strategy Viability & Governance Directive

**Audit Dossier Path:** `audit/strategy_research/milestone_5_8a_survival_accounting/FINAL_RESEARCH_DECISION.md`  
**Execution Timestamp:** 2026-11-04T00:06:00Z  
**Branch:** `research/quantum-next-3pct`  
**Authorizing Mandate:** Milestone 5.8A Terminal Equity & Survival Accounting Protocol  

---

## 1. Governance Classification & Paper Trading Status

Under the Project Owner's non-negotiable governance framework, this document formalizes the operational and research disposition of the candidate strategy portfolio (Portfolio A and its underlying HYP-01 / EXP-08–11 variants) following the Milestone 5.8A Survival Accounting and Terminal Equity Audit.

### Governance Scorecard
```yaml
RESEARCH_MILESTONE: MILESTONE_5_8A
CANDIDATE_EVALUATED: PORTFOLIO_A (HYP-01 / EXP-08 through EXP-11 under 1.0x Unlevered Exposure)
RESEARCH_STATUS: REQUIRES_RESEARCH
PORTFOLIO_A_DISPOSITION: REJECTED_AS_UNVIABLE
PAPER_TRADING_AUTHORIZATION: DENIED_PENDING_3_PERCENT_BACKTEST_VALIDATION
LIVE_TRADING_AUTHORIZATION: STRICTLY_PROHIBITED
OPERATIONAL_PROHIBITIONS:
  - PAPER_TRADING_DAEMON: STRICTLY_PROHIBITED
  - PAPER_SCHEDULER_SERVICES: STRICTLY_PROHIBITED
  - PROSPECTIVE_PAPER_DEPLOYMENT: STRICTLY_PROHIBITED
  - EXCHANGE_API_TRADING_CREDENTIALS: STRICTLY_PROHIBITED
  - LIVE_ACCOUNT_CONNECTION: STRICTLY_PROHIBITED
MANDATORY_GATE_REMAINDER:
  - MINIMUM_MEAN_NET_DAILY_RETURN: >= 3.00%
  - EFFECTIVE_LEVERAGE: STRICTLY 1.0x (UNLEVERED)
  - MAXIMUM_DRAWDOWN: <= 15.00%
  - PROFIT_FACTOR: >= 1.30
  - NET_EXPECTANCY: POSITIVE AFTER VIP0 TRANSACTION FRICTION
  - FULL_CALENDAR_ACCOUNTING: MANDATORY
```

---

## 2. Re-Evaluation of Strategy Viability

Milestone 5.8A conducted an exhaustive forensic reconciliation of Portfolio A. The empirical findings invalidate any claim of operational viability for this candidate:

### 2.1 Active-Period Capital Destruction vs False Dilution
1. **Severe Negative Active Edge:** During its 118-day active lifespan, Portfolio A experienced a continuous, compounding capital destruction at a rate of **$-1.3499\%$ to $-2.0068\%$ mean net daily return**, suffering an active maximum drawdown of **$80.03\%$** and losing $-\$80.03$ of its $\$100.00$ starting balance.
2. **Dilution Deception Unmasked:** The previously reported full-calendar return of $-0.1449\%$/day was an artifact of dividing an $80\%$ active collapse by 1,099 calendar days, treating 981 post-halt paralyzed days as "neutral zero-return" trading days.
3. **No Organic Alpha:** The strategy's net expectancy is **$-16.10\text{ bps}$ to $-17.99\text{ bps}$ per trade**, with a Profit Factor of only **$0.533$ to $0.545$**. The algorithm loses more than $\$1.80$ for every $\$1.00$ it generates.

### 2.2 Mathematical Certainty of Ruin
1. **Empirical Ruin Probability is 100.0%:** Across $2,000$ stationary block bootstrap iterations, $100.0\%$ of resampled paths breached the minimum-notional starvation threshold within 45 to 142 days ($100 balance) or 110 to 315 days ($1,000 balance).
2. **Capital Inefficiency:** Capital scale experiments demonstrate that injecting $\$1,000$ or $\$10,000$ does not rescue the strategy; it merely compounds the loss deeper, resulting in drawdowns of **$98.00\%$** and **$99.80\%$**, terminating at the exact same $\$19.98$ operational boundary.
3. **Passive Maker Execution Cannot Overcome Negative Drift:** Even with +2.0 bps maker fee rebates and limit-order queue execution, adverse selection and lack of predictive edge ensure that losses steadily consume all available capital.

---

## 3. Root Cause Analysis of Candidate Failure

The forensic investigation reveals four root causes underlying Portfolio A's failure:

```
+---------------------------------------------------------------------------------------------------+
|                                ROOT CAUSES OF PORTFOLIO A COLLAPSE                                |
+---------------------------------------------------------------------------------------------------+
| 1. Lack of Causal Directional Edge (Gross Expectancy <= 0)                                        |
|    - Gross trade return averages -4.92 bps per trade even before fees.                            |
|    - The underlying alpha signal does not forecast price displacement beyond random noise.        |
+---------------------------------------------------------------------------------------------------+
                                            │
                                            ▼
+---------------------------------------------------------------------------------------------------+
| 2. Friction Domination (Transaction Costs Exceed 71% of Capital)                                  |
|    - In 118 days, the strategy executed 3,562 trades, incurring $57.29 in transaction friction.  |
|    - Trading at high frequencies with marginal or non-existent edge acts as a fee siphon to Bybit.|
+---------------------------------------------------------------------------------------------------+
                                            │
                                            ▼
+---------------------------------------------------------------------------------------------------+
| 3. Adverse Selection on Passive Limit Orders                                                      |
|    - When limit orders fill immediately, the market is frequently trending violently through them.|
|    - Unfilled orders represent missed profitable moves; filled orders represent toxic flow.       |
+---------------------------------------------------------------------------------------------------+
                                            │
                                            ▼
+---------------------------------------------------------------------------------------------------+
| 4. Inability to Self-Heal Post Capital Depletion                                                  |
|    - Once equity falls below $20.00, maximum position sizing (25%) falls below Bybit's $5.00 limit.|
|    - The strategy possesses zero dynamic recovery mechanism and halts permanently.                 |
+---------------------------------------------------------------------------------------------------+
```

---

## 4. Architectural & Strategic Paradigm Shift Required

Prior to any prospective validation or further capital deployment, quantitative research must pivot away from micro-tuning failed candidates and transition to a fundamentally redesigned research framework:

### 4.1 Required Research Shifts
1. **True Structural Alpha Discovery:** Abandon parameter sweeps on existing indicators. Formulate novel hypotheses centered on observable market microstructure imbalances, liquidity sweeps with confirmed volume delta, funding-rate regime shifts, and cross-asset lead-lag dynamics.
2. **Gross Expectancy Hurdle:** No strategy shall proceed past initial screening unless its **gross expectancy exceeds $+25.0\text{ bps}$ per trade** prior to friction. A strategy cannot survive VIP0 costs without substantial gross cushion.
3. **Adaptive Trade Frequency & Quality Over Quantity:** Reduce trade churn. Strategies executing $>30$ trades per day with sub-5 bps margins are inherently fragile. Research must focus on high-conviction structural regimes with favorable asymmetric reward-to-risk ratios.
4. **Strict Causal & Provenance Standards:** All future strategy evaluations must adhere to the data provenance, zero-leakage, and bifurcated active/calendar accounting standards established in Milestones 5.7 and 5.8A.
5. **Virgin Holdout Preservation:** The holdout dataset ($1,793,491,200,000\text{ ms}$ / 2026-11-01 00:00:00 UTC onward) must remain 100% untouched until a strategy achieves $\ge 3.00\%$ mean net daily return in cross-validated backtests.

---

## 5. Non-Negotiable Governance Directives

In accordance with Project Owner requirements:

1. **Rejection of Portfolio A:** Portfolio A (including EXP-08, EXP-09, EXP-10A/B, and EXP-11 combinations) is **formally rejected** as a viable live trading candidate. It is permanently archived as a historical baseline and negative control.
2. **Paper Trading Prohibited:** Paper trading remains **STRICTLY PROHIBITED**. The status `PAPER_TRADING_AUTHORIZATION: DENIED_PENDING_3_PERCENT_BACKTEST_VALIDATION` remains active and immutable until:
   - Mean net daily return achieves $\ge 3.00\%$ at **1.0x unlevered exposure**.
   - Maximum drawdown remains $\le 15.00\%$.
   - Positive net expectancy is verified after full VIP0 taker/maker friction.
   - Independent out-of-sample reproduction succeeds without parameter contamination.
3. **Infrastructure Security:** No paper trading daemons, background schedulers, automated crons, or exchange API credentials may be configured, launched, or queried.
4. **Git Repository Hygiene:** Work remains on `research/quantum-next-3pct`. No merges to `main` are authorized.

---

## 6. Research Sign-Off

```yaml
GOVERNANCE_SIGN_OFF:
  AUDIT_MILESTONE: MILESTONE_5_8A
  ACCOUNTING_ENGINE: VERIFIED_INDEPENDENT
  ACTIVE_PERIOD_METRICS: CONFIRMED_NEGATIVE_EDGE
  RUIN_PROBABILITY: 100.0%_CERTAIN
  FINAL_STATUS: REQUIRES_RESEARCH
  PAPER_TRADING: DENIED
  AUTHORIZATION_DATE: 2026-11-04
```
