# QUANTUM PHASE 5.4: CALIBRATION & DECISION POLICY RESEARCH DESIGN
**Architectural Blueprint, Research Hypotheses & Theoretical Framework**

**Document Version:** 5.4.0_RESEARCH_DESIGN  
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
2. **Asymmetric Payoffs & Friction Inversion:** Triple-barrier outcomes (Take-Profit vs Stop-Loss) occur in an environment governed by bid-ask spreads, taker fees (5 bps per side = 10 bps round-trip), slippage, and funding rates. A trade with 55% win rate can produce negative expected value if losses and fees exceed gains.
3. **No Trade / Abstention Absence:** Forcing the system to trade every 5-minute bar (100% coverage) guarantees fee churn. Without a principled abstention policy, the system trades during low-conviction regimes.

Phase 5.4 is designed to resolve these gaps through **Calibration & Decision Policy Research**.

---

## 2. Formal Research Hypotheses

Phase 5.4 will test four formal quantitative hypotheses:

### Hypothesis H1: Post-Hoc Probability Calibration
*Post-hoc probability calibration (Platt scaling, Isotonic regression, or Temperature scaling) fitted on early OOF segments significantly reduces Expected Calibration Error (ECE) and multiclass Brier score on subsequent temporal evaluation segments without degrading underlying ranking discrimination (Balanced Accuracy / ROC-AUC).*

### Hypothesis H2: Confidence-Based Selective Abstention
*Restricting trade candidates to candles with high calibrated posterior confidence yields a monotonically decreasing risk-coverage curve, where selective balanced accuracy increases systematically as coverage decreases from 100% down to 30%.*

### Hypothesis H3: Cost-Sensitive Net Expectancy Superiority
*A cost-sensitive decision policy that maps calibrated probabilities, local volatility ($1.5 \times \text{ATR}_t$), and transaction frictions into an expected net return $\mathbb{E}[R_{\text{net}}]$ outperforms naive argmax probability classification by filtering out trades whose expected gross gain is smaller than round-trip execution drag.*

### Hypothesis H4: Temporal & Cross-Instrument Robustness
*Calibrators and decision policies fitted on historical OOF data exhibit parameter stability across market regimes and generalize to the final chronological evaluation segment without performance collapse, while maintaining independent specialist identity across all 11 instruments.*

---

## 3. Strict Separation of Three Metric Domains

To maintain research integrity, Phase 5.4 strictly segregates performance measurement into three non-interchangeable tiers:

```
+-------------------------------------------------------------------+
| 1. PREDICTIVE METRICS (Probabilistic & Discrimination Quality)     |
| - Multiclass Brier Score, Log Loss                                |
| - Expected Calibration Error (ECE: Equal-Width & Equal-Frequency) |
| - Balanced Accuracy, Class-Wise Recall (TP, EXP, SL)               |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
| 2. DECISION-POLICY METRICS (Selective Classification & Coverage)  |
| - Trade Coverage (Cov): Fraction of candles where action != NO_TRADE|
| - Selective Balanced Accuracy (BA_sel at Cov = 30%, 50%, 70%)      |
| - Precision-Coverage Trade-Off & Abstention Monotonicity          |
| - Per-Class Coverage Ratios (LONG coverage vs SHORT coverage)     |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
| 3. ECONOMIC METRICS (Frictional Viability & Trade Expectancy)     |
| - Expected Net Return per Trade: E[R_net] (basis points)          |
| - Win/Loss Ratio vs Payoff Ratio under Volatility-Scaled Barriers |
| - Breakeven Win Rate Threshold: p_crit = C_roundtrip / (R_TP + R_SL)|
| - Fee-to-Gross Gain Ratio: C_roundtrip / E[R_gross]               |
+-------------------------------------------------------------------+
```

**Rule:** High predictive Balanced Accuracy shall never be cited as evidence of economic profitability. Conversely, economic metrics in Phase 5.4 are theoretical expectancy estimates and shall never be conflated with backtesting equity curves.

---

## 4. Architectural System Integration

Phase 5.4 operates strictly as an inference and post-processing research layer situated between the frozen Phase 5.3 models and future Phase 5.5 backtesting:

```
[Phase 5.3 Frozen Models & Preprocessors]
             |
             v  (Bit-Exact OOF Inference)
[Uncalibrated Raw OOF Probabilities P_raw: (N, 3)]
             |
             +------------------------------+
             |                              |
             v (Folds 1-2 Fit)              v (Evaluation)
   [Calibrator Fitting]            [Reliability Audit]
   - Vector Platt Scaling          - Brier Score & ECE
   - Temperature Scaling           - Reliability Curves
   - Isotonic Regression           - M=15 Bins (Width/Freq)
             |
             v
   [Calibrated Probabilities P_cal: (N, 3)]
             |
             v (Folds 3-4 Tuning)
   [Selective Classification & Decision Policy]
   - Confidence Abstention (Coverage 20% to 80%)
   - Dynamic Cost Matrix (10 bps Round-Trip Fee Drag)
   - Expected Net Return Calculation E[R_net]
             |
             v (Fold 5 Frozen Evaluation)
   [Final Out-of-Sample Temporal Validation]
   - Policy Generalization Test
   - Regime Robustness Assessment
   - Phase 5.5 Backtesting Readiness Verdict
```

---

## 5. Scope & Strict Boundaries

1. **Research Design Only:** This document and its accompanying specifications constitute a formal research protocol. No experiments, model fitting, or threshold tuning are executed during Phase 5.4.0.
2. **Prospective Holdout Remains Sealed:** The holdout period (`2026-11-01 00:00:00 UTC` through `2027-04-30 23:59:59.999 UTC`) is strictly off-limits and protected by cryptographic assertions.
3. **Historical Period Is Not a Fresh Holdout:** The historical period through `2026-10-31` was utilized for model development and OOF validation in Phase 5.3. All Phase 5.4 evaluations must acknowledge that this is a retrospective validation environment, not an unseen prospective holdout.
4. **No Model Retraining:** Frozen LightGBM binaries and preprocessors are utilized as immutable feature extractors and probability generators.
