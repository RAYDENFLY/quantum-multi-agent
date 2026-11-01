# QUANTUM PHASE 5.4: CALIBRATION & DECISION POLICY RESEARCH DESIGN
**Architectural Blueprint, Research Hypotheses & Theoretical Framework**

**Document Version:** 5.4.1_RESEARCH_DESIGN  
**System:** QUANTUM 11-Specialist Cryptocurrency Perpetual Futures ML Trading Research System  
**Repository:** [quantum-multi-agent](file:///d:/quantum-multi-agent)  
**Governance Status:** `DESIGN_PHASE_ONLY_AWAITING_EXPLICIT_HUMAN_AUTHORIZATION`  
**Classification Standards:** `VERIFIED_FROM_SOURCE` | `VERIFIED_FROM_ARTIFACT` | `DOCUMENTATION_ONLY`

---

## 1. Context & Research Problem

Phase 5.3 concluded with the final research freeze (`PHASE_5_3_FINAL_FREEZE_COMPLETE`), establishing that Specialist B4 (LightGBM) achieved statistically significant improvements in Balanced Accuracy over the B0 Majority baseline across all 11 instruments on out-of-fold (OOF) evaluation.

However, a fundamental tenet of financial machine learning is that:
$$\text{Statistical Classification Discrimination} \ne \text{Economic Trading Profitability}$$

A multiclass classifier may produce a Balanced Accuracy of 0.45 (well above the 0.3333 random baseline) yet remain completely unprofitable or catastrophic when deployed in live perpetual futures trading due to:
1. **Probability Distortion (Miscalibration):** GBDT leaf outputs are known to suffer from sigmoid distortion, producing overconfident probabilities near 0 and 1 or compressed middle ranges that do not reflect true posterior odds.
2. **Asymmetric Payoffs & Friction Inversion:** Triple-barrier outcomes (Take-Profit vs Stop-Loss) occur in an environment governed by bid-ask spreads, taker fees, slippage, and funding rates. Realized returns do not equal nominal barrier parameters.
3. **No Trade / Abstention Absence:** Forcing the system to trade every 5-minute bar (100% coverage) guarantees fee churn. Without a principled abstention policy, the system trades during low-conviction regimes.

Phase 5.4 is designed to resolve these gaps through **Calibration & Decision Policy Research**.

---

## 2. Formal Research Hypotheses

Phase 5.4 will test four formal quantitative hypotheses:

### Hypothesis H1: Post-Hoc Probability Calibration
*Post-hoc probability calibration (Platt scaling, Isotonic regression, or Temperature scaling) fitted on early OOF segments significantly reduces Expected Calibration Error (ECE) and multiclass Brier score on subsequent temporal evaluation segments without degrading underlying ranking discrimination (Balanced Accuracy / ROC-AUC).*

### Hypothesis H2: Confidence-Based Selective Abstention
*Restricting trade candidates to candles with high calibrated posterior confidence yields a monotonically decreasing risk-coverage curve, where selective balanced accuracy increases systematically as coverage decreases across the evaluation grid {100%, 80%, 70%, 60%, 50%, 40%, 30%, 20%}.*

### Hypothesis H3: Dynamic Friction Invariance & Filter Discrimination
*A decision policy incorporating local volatility ($1.5 \times \text{ATR}_t$), bid-ask spread, and execution friction distinguishes high-expectancy trade opportunities from marginal trades that appear positive under classification but collapse under realistic execution drag.*

### Hypothesis H4: Temporal & Cross-Instrument Robustness
*Calibrators and decision policies fitted on historical OOF data exhibit parameter stability across market regimes and generalize to the final chronological evaluation segment without performance collapse, while maintaining independent specialist identity across all 11 instruments.*

---

## 3. Strict Separation of Research Phases: Phase 5.4 vs Phase 5.5

To eliminate circular reasoning and prevent premature claims of trading profitability, a strict boundary is established between Phase 5.4 and Phase 5.5:

```
+-------------------------------------------------------------------+
| PHASE 5.4: CALIBRATION & DECISION POLICY RESEARCH                 |
| Scope: Probabilistic Reliability & Selective Decision Rules      |
| Evaluated Metrics:                                                |
| - Multiclass Brier Score, Log Loss                                |
| - Expected Calibration Error (ECE: 15 Equal-Width & Equal-Freq)   |
| - Selective Balanced Accuracy across Coverage Grid (20% to 100%)  |
| - Risk-Coverage Monotonicity Slope (beta_RC > 0)                  |
| - Minimum Class Support Guardrails (N_c >= 100)                   |
| - Decision Filter Stability across Volatility & Trend Regimes     |
| PROHIBITED: No cumulative PnL, no equity curves, no Sharpe ratios |
+-------------------------------------------------------------------+
                                  |
                                  v (Requires Phase 5.4 Gate Pass)
+-------------------------------------------------------------------+
| PHASE 5.5: HISTORICAL STRATEGY BACKTESTING                       |
| Scope: Realistic Portfolio Simulation & Economic Alpha Validation |
| Evaluated Metrics:                                                |
| - Realized Net Cumulative PnL                                     |
| - Realized Execution Drag (Fees, Spread, Fill Slippage, Funding)  |
| - Maximum Drawdown (MDD) & Recovery Factor                        |
| - Trade Frequency, Win Rate, Realized Payoff Ratio                |
| - Annualized Sharpe Ratio, Sortino Ratio, Calmar Ratio            |
+-------------------------------------------------------------------+
```

**Governance Rule:** Phase 5.4 shall NOT claim trading profitability, positive Sharpe ratios, or live readiness. It establishes solely whether model probabilities and decision policies are sufficiently reliable to proceed to historical strategy backtesting.

---

## 4. Scope & Strict Boundaries

1. **Research Design Only:** This document and its accompanying specifications constitute a formal research protocol. No experiments, model fitting, or threshold tuning are executed during Phase 5.4.1.
2. **Prospective Holdout Remains Sealed:** The holdout period (`2026-11-01 00:00:00 UTC` through `2027-04-30 23:59:59.999 UTC`) is strictly off-limits and protected by cryptographic assertions.
3. **Historical Period Is Not a Fresh Holdout:** The historical period through `2026-10-31` was utilized for model development and OOF validation in Phase 5.3. All Phase 5.4 evaluations must acknowledge that this is a retrospective validation environment, not an unseen prospective holdout.
4. **No Model Retraining:** Frozen LightGBM binaries and preprocessors are utilized as immutable feature extractors and probability generators.
