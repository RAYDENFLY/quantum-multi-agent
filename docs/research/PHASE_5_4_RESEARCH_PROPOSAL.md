# QUANTUM PHASE 5.4: RESEARCH PROPOSAL
## From Predictive Discrimination to Calibrated Decision Policies Under Market Frictions

**Proposal Version:** 5.4.1_REFINED_PROPOSAL  
**Governance Status:** `EXECUTION ON HOLD (STRICT_HOLD_AWAITING_EXPLICIT_HUMAN_AUTHORIZATION)`  
**Producing Role:** Senior Quantitative Research Engineer, ML Research Auditor, Research Governance Lead  
**Target Repository:** [quantum-multi-agent](file:///d:/quantum-multi-agent)  
**Proposed Execution Boundary:** Zero model retraining; strictly post-processing frozen Phase 5.3 OOF predictions  
**Prospective Holdout Status:** Completely sealed (`2026-11-01 00:00:00 UTC` to `2027-04-30 23:59:59.999 UTC`)  

---

## 1. Core Research Objective & Scientific Rationale (C1)

Phase 5.3 established that specialist model B4 (LightGBM) achieves statistically significant predictive discrimination over the B0 majority baseline across all 11 instruments (paired delta $\Delta\text{BA} \in [+0.0534, +0.1656]$, $p < 0.0001$). 

However, **predictive discrimination does not constitute economic profitability**.

A classifier with 45% Balanced Accuracy can produce catastrophic financial drawdowns if its probability outputs are uncalibrated, if it trades continuously during low-confidence regimes, or if the bid-ask spread and taker fees exceed the expected return of its directional calls.

The core research objective of **Phase 5.4** is to develop, calibrate, and validate a **non-trading decision-policy layer** on top of the frozen Phase 5.3 OOF predictions. Phase 5.4 operates under a strict **Zero Model Retraining Policy**: all research will evaluate post-processing transformations of frozen probability vectors without altering model binaries or features.

---

## 2. Evaluation of Candidate Research Directions (C2)

### 1. Probability Calibration
Raw LightGBM predicted probabilities are distorted by tree splitting criteria; applying post-hoc Platt scaling or Isotonic Regression on out-of-fold validation splits will reduce Multiclass Brier Score and Expected Calibration Error (ECE) without modifying model weights.
- **Required Input:** Frozen OOF probability vectors $\hat{P} = [p_{-1}, p_0, p_1]$ and ground truth $y_t$ from Phase 5.3.
- **Expected Output:** Calibrated probability vectors $P^*$, calibration curves, Brier Score reduction table, ECE metrics.
- **Evaluation Methodology:** Fit calibration maps on inner training splits and evaluate on validation OOF splits; measure Brier score and log-loss improvement.
- **Potential Leakage Risks & Mitigation:** Zero feature leakage. Must use strictly inner-fold fitting to prevent calibration leakage.
- **Computational Cost & Resource Impact:** Very low (< 2 minutes across fleet, minimal RAM).
- **Dependency on Phase 5.3:** Directly dependent on Phase 5.3 frozen OOF probability outputs.

### 2. Class-Specific Precision & Recall Optimization
Symmetric argmax prediction is suboptimal for asymmetric market payoffs; adjusting decision thresholds $\tau_c$ to maximize precision on directional classes (TP and SL) at the expense of lower recall will improve trade selectivity.
- **Required Input:** Calibrated probability vectors $P^*$ and class support metadata.
- **Expected Output:** Precision-Recall frontiers, optimal asymmetric threshold vectors $\boldsymbol{\tau}^* = [\tau_{-1}, \tau_0, \tau_1]$ per specialist.
- **Evaluation Methodology:** Evaluate PR-AUC curves across threshold grid; identify Pareto frontier balancing directional precision against trade frequency.
- **Potential Leakage Risks & Mitigation:** Threshold grid search must be conducted on training/inner validation folds only.
- **Computational Cost & Resource Impact:** Low (purely vector operations on stored probabilities).
- **Dependency on Phase 5.3:** Requires calibrated probabilities from Direction 1.

### 3. Confidence-Based Prediction Filtering
Predictions where the maximum class probability barely exceeds random guessing ($p_{\max} \approx 0.35$) have near-zero edge; enforcing a minimum confidence margin filters out regime noise.
- **Required Input:** Probability vectors $P^*$, margin threshold $\delta$.
- **Expected Output:** Filtered confusion matrices, accuracy as a function of confidence threshold, retention rate curves.
- **Evaluation Methodology:** Calculate Balanced Accuracy and precision conditional on confidence deciles.
- **Potential Leakage Risks & Mitigation:** Zero leakage if margin threshold is tuned on inner folds.
- **Computational Cost & Resource Impact:** Very low.
- **Dependency on Phase 5.3:** Dependent on Direction 1.

### 4. Selective Classification & Abstention Policy
Allowing the model to abstain from trading (outputting a 'Reject' / 'No Trade' action) will monotonically increase accuracy on the accepted decision subspace as coverage decreases.
- **Required Input:** Calibrated probabilities, cost of abstention $c_a = 0$.
- **Expected Output:** Risk-Coverage curves, optimal coverage point $\phi^*$, accepted-set Balanced Accuracy.
- **Evaluation Methodology:** Evaluate Chow's optimal rule for error minimization with a reject option; plot empirical selective risk versus coverage $\phi \in [0.1, 1.0]$.
- **Potential Leakage Risks & Mitigation:** Zero leakage risk under within-fold threshold selection.
- **Computational Cost & Resource Impact:** Low.
- **Dependency on Phase 5.3:** Dependent on Directions 1 and 3.

### 5. Cost-Sensitive Decision Policy
Formalizing an explicit utility matrix $U(a, y)$ that incorporates taker fees (0.04%), spread costs (0.01%), and asymmetric barrier payoffs ($1.5\sigma$ gain vs $1.5\sigma$ loss) will yield superior decision utility compared to accuracy maximization.
- **Required Input:** Calibrated probabilities $P^*$, fee parameter table, barrier volatility $\sigma_{20}$.
- **Expected Output:** Expected utility matrix, optimal Bayes decision rule, theoretical net edge per candle.
- **Evaluation Methodology:** Calculate Expected Decision Utility (EDU) across out-of-fold validation sets under conservative fee scenarios.
- **Potential Leakage Risks & Mitigation:** Zero market leakage; parameters are fixed exogenous constants.
- **Computational Cost & Resource Impact:** Low.
- **Dependency on Phase 5.3:** Dependent on Direction 1.

### 6. Triple-Barrier Prediction to Trading Decision Mapping
A multi-class label $y \in \{-1, 0, 1\}$ cannot be naively executed as a position; defining formal state machine rules provides a deterministic bridge to strategy simulation.
- **Required Input:** Decision signals from Direction 5, candle timestamps, high/low price paths.
- **Expected Output:** Event-driven state machine specification, position duration distributions, trade trigger frequency.
- **Evaluation Methodology:** Simulate state machine transitions on validation candles without order execution.
- **Potential Leakage Risks & Mitigation:** Must enforce strict causal order (entry on $t+1$ open, never $t$ close).
- **Computational Cost & Resource Impact:** Moderate.
- **Dependency on Phase 5.3:** Dependent on Directions 4 and 5.

### 7. Multi-Timeframe Confirmation
5-minute directional signals that align with higher-timeframe trend filters (15m and 1h EMA slope) will suffer fewer false breakout triggers than unconfirmed signals.
- **Required Input:** 5m OOF predictions, 15m and 1h canonical OHLCV candles.
- **Expected Output:** Gated signal series, conditional precision comparison (confirmed vs unconfirmed).
- **Evaluation Methodology:** Compute precision and F1 stratified by 15m/1h trend alignment.
- **Potential Leakage Risks & Mitigation:** High leakage risk if higher-timeframe bars are not strictly lagged to prevent lookahead bias.
- **Computational Cost & Resource Impact:** Moderate.
- **Dependency on Phase 5.3:** Independent of calibration, but best evaluated after Direction 4.

### 8. Robustness Across Market Regimes
B4's predictive performance is regime-dependent; conditioning decision policies on rolling volatility regimes will stabilize performance.
- **Required Input:** OOF predictions, 20-bar realized volatility, volume metrics.
- **Expected Output:** Regime-stratified confusion matrices, conditional precision by volatility quintile.
- **Evaluation Methodology:** Partition validation sets into Volatility Quintiles (Q1 low to Q5 high) and evaluate conditional metrics.
- **Potential Leakage Risks & Mitigation:** Zero leakage if regime classification uses strictly historical lookback.
- **Computational Cost & Resource Impact:** Low.
- **Dependency on Phase 5.3:** Complements Directions 4 and 5.

---

## 3. Recommended Research Sequence (C3)

```
+-------------------------------------------------------------------------+
|                  STAGE 1: Phase 5.4.1 (Calibration & Metric Audit)      |
|  - Calibrate OOF probabilities using Isotonic & Platt scaling           |
|  - Nested temporal calibration split (never in-sample)                  |
|  - Quantile (M=10) and Equal-Width (M=10) ECE evaluation               |
|  - Pre-registered Gate: ECE < 0.05 & Brier Score preserved/improved     |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|             STAGE 2: Phase 5.4.2 (Selective Classification & Abstention)|
|  - Map confidence thresholds tau to Coverage vs Selective BA frontier   |
|  - Threshold selection split strictly separated from evaluation split   |
|  - Comparison against naive random/majority abstention at same coverage |
|  - Pre-registered Gate: Selective BA >= 0.50 at coverage >= 30%         |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|             STAGE 3: Phase 5.4.3 (Cost-Sensitive Decision Policy)       |
|  - Utility payoff matrix incorporating 5 bps per-side friction          |
|  - Sensitivity analysis across 0, 2.5, 5.0, and 10.0 bps per-side       |
|  - Explicit accounting of turnover and funding drag                     |
|  - Pre-registered Gate: Net Expected Decision Utility > 0 under 5 bps   |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|             STAGE 4: Phase 5.4.4 (Regime-Conditioned Policy Validation) |
|  - Evaluate policy stability across realized volatility terciles        |
|  - Confirm zero catastrophic degradation in high-volatility regimes     |
|  - Pre-registered Gate: Positive delta maintained across all terciles    |
+-------------------------------------------------------------------------+
```

---

## 4. Evaluation Framework & Strict Tripartite Separation (C4)

To prevent self-deception in quantitative research, Phase 5.4 strictly segregates three distinct tiers of metrics:

### 4.1 Tier 1: Predictive Metrics (Statistical Discrimination)
- **Multiclass Brier Score:** Mean squared error between probability vector and one-hot label.
- **Multiclass Log-Loss:** Cross-entropy penalizing overconfident incorrect predictions.
- **Expected Calibration Error (ECE):** Evaluated with $M=10$ quantile bins and $M=10$ equal-width bins.
- **Macro Balanced Accuracy:** Unweighted mean of per-class recalls.

### 4.2 Tier 2: Decision-Policy Metrics (Action Quality Under Abstention)
- **Coverage ($\phi$):** Proportion of candles where the policy takes an active directional stance.
- **Selective Balanced Accuracy:** Balanced Accuracy computed strictly over active non-abstained bars.
- **Directional Precision:** Precision evaluated exclusively on triggered long/short stances.
- **Risk-Coverage Curve:** Monotonicity of accuracy as a function of confidence rejection threshold.
- **Expected Decision Utility (EDU):** Payoff score based on stylized utility matrix without live fill modeling.

### 4.3 Tier 3: Economic Metrics (Execution Realism - Permitted Only in Future Backtesting)
- **Net PnL:** Cash return after deducting exchange fees, bid-ask spread crossing, and slippage.
- **Turnover & Exposure Time:** Trading frequency and percentage of time capital is exposed to market risk.
- **Max Drawdown & Sharpe Ratio:** Risk-adjusted return profile under portfolio capital constraints.

### 4.4 Why the Three Metric Groups Must Never Be Interchanged
1. **Predictive Discrimination $\neq$ Decision Utility:** A model can have strong statistical discrimination ($p < 0.0001$) but trigger trades during high-spread periods where transaction costs exceed the marginal edge.
2. **Decision Quality $\neq$ Financial Profitability:** A selective policy can achieve 75% directional precision by trading once per quarter (0.01% coverage). Such a policy has exceptional selectivity but cannot generate sufficient economic turnover to cover infrastructure overhead.
3. **Economic Simulation $\neq$ Model Validity:** A strategy backtest can display positive return purely due to market beta drift during a secular bull run, even if the underlying machine learning model has zero predictive skill. Conflating economic returns with model validation leads directly to catastrophic live trading failure.

---

## 5. Refined Pre-Registered Acceptance & Gate Criteria

Phase 5.4 establishes rigorous, falsifiable gating criteria for each stage:

### 5.1 Stage 1 Gate: Probability Calibration
- **Binning Strategy:** Evaluated on both $M=10$ equal-frequency (quantile) bins and $M=10$ equal-width bins.
- **Calibration Methods:** Non-parametric Isotonic Regression and parametric Platt Scaling (logistic sigmoid).
- **Temporal Calibration Split:** Calibration models must be fit on preceding temporal folds (e.g. fold $k-1$ or inner expanding split) and evaluated out-of-sample on fold $k$. In-sample calibration evaluation is strictly prohibited.
- **Acceptance Threshold:** Calibrated ECE must be $< 0.05$ on quantile binning across at least 9 of 11 instruments, while strictly preserving or decreasing Brier Score and Log-Loss relative to uncalibrated outputs.

### 5.2 Stage 2 Gate: Selective Classification & Abstention
- **Baseline Comparison:** The selective policy must be benchmarked against a naive random/majority abstention policy at the identical coverage level $\phi$.
- **Sample Support:** A minimum of $N_c \ge 1,000$ active observations per class must be present on the non-abstained evaluation slice.
- **Statistical Significance:** Paired bootstrap 95% confidence interval for selective Balanced Accuracy must remain strictly superior to the unconstrained baseline.
- **Threshold Separation:** Confidence rejection threshold $\tau$ must be selected on a calibration split and evaluated on a separate holdout slice.
- **Acceptance Threshold:** Selective Balanced Accuracy must achieve Selective BA >= 0.50 at coverage >= 30% for at least 8 of 11 instruments.

### 5.3 Stage 3 Gate: Cost-Sensitive Decision Thresholding
- **Cost Specification:** Market friction is parameterized at **5.0 basis points per side** (10.0 bps round-trip), representing 4.0 bps taker fee plus 1.0 bps half-spread and slippage allowance.
- **Sensitivity Analysis:** Must be evaluated across the full friction grid: $[0.0, 2.5, 5.0, 10.0]$ bps per side.
- **Friction Drag:** Model must explicitly account for position turnover and perpetual futures funding rate drag over holding horizons.
- **Acceptance Threshold:** Net Expected Decision Utility (EDU) under 5.0 bps per-side friction must be strictly positive ($\text{EDU} > 0$) for at least 8 of 11 specialists.
- **Non-Profitability Clause:** A positive EDU score confirms decision quality under stylized costs, but does NOT constitute proof of live trading profitability.

### 5.4 Stage 4 Gate: Regime-Conditioned Validation
- **Regime Partitioning:** Evaluated across 20-bar realized volatility terciles (Low, Medium, High).
- **Acceptance Threshold:** The decision policy must maintain positive paired delta over the baseline in all three volatility terciles without catastrophic breakdown in high-volatility regimes.

---

## 6. Non-Negotiable Data Governance Boundaries

| Boundary | Definition | Enforcement |
| :--- | :--- | :--- |
| **Active Research Window** | `2023-11-01 00:00:00 UTC` to `2026-04-30 22:55:00 UTC` | All Phase 5.4 calibrations, threshold tuning, and evaluations execute strictly here. |
| **Validation Observed** | `2026-05-01 00:00:00 UTC` to `2026-10-31 23:59:59.999 UTC` | Historical research data; excluded from threshold tuning to prevent lookahead bias. |
| **Prospective Holdout** | `2026-11-01 00:00:00 UTC` to `2027-04-30 23:59:59.999 UTC` | **Completely sealed.** Zero reading, calibration, tuning, or evaluation permitted. |

---

## 7. Final Governance Disposition

> [!IMPORTANT]
> **GOVERNANCE DISPOSITION: EXECUTION ON HOLD**
> 
> This document is an architectural and methodological proposal only.
> **Phase 5.4 is NOT authorized to execute.**
> No code may be run, no models may be calibrated, and no simulation may be launched until this proposal receives explicit human architectural approval.

---

**Proposal Authored By:** Senior Quantitative Research Engineer & ML Research Auditor  
**Date:** 2026-11-02 00:30:00 UTC  
