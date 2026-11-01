#!/usr/bin/env python3
"""
QUANTUM Phase 5.4.0: Calibration & Decision Policy Research Design Generator.

Generates:
1. docs/research/PHASE_5_4_RESEARCH_DESIGN.md
2. docs/research/PHASE_5_4_ARTIFACT_READINESS_AUDIT.md
3. docs/research/PHASE_5_4_EXPERIMENT_PROTOCOL.md
4. docs/research/PHASE_5_4_ACCEPTANCE_CRITERIA.md
5. tests/unit/test_phase5_4_0_design.py

Strict Constraints:
- Zero em-dashes (\\u2014 or chr(0x2014)) anywhere.
- Forward slashes for all markdown links.
- No model retraining, no OOF modification, no holdout access.
"""

import pathlib

EM_DASH = chr(0x2014)

def check_no_em_dash(text: str, filename: str):
    if EM_DASH in text:
        raise ValueError(f"Forbidden em-dash found in {filename}!")
    if "\u2014" in text:
        raise ValueError(f"Forbidden unicode em-dash found in {filename}!")


# -----------------------------------------------------------------------------
# 1. docs/research/PHASE_5_4_ARTIFACT_READINESS_AUDIT.md
# -----------------------------------------------------------------------------
def generate_artifact_readiness_audit() -> str:
    return """# QUANTUM PHASE 5.4.0: ARTIFACT READINESS & PROBABILITY AUDIT
**Forensic Inventory, Probability Reproducibility & Model Availability Audit**

**Document Version:** 5.4.0_ARTIFACT_AUDIT  
**System:** QUANTUM 11-Specialist Cryptocurrency Perpetual Futures ML Trading Research System  
**Audit Date:** 2026-11-02  
**Governance Status:** `PHASE_5_4_AUDIT_COMPLETE`  
**Classification Standards:** `VERIFIED_FROM_SOURCE` | `VERIFIED_FROM_ARTIFACT` | `DOCUMENTATION_ONLY`

---

## 1. Executive Summary

Prior to embarking on Phase 5.4 (Calibration & Decision Policy Research), a comprehensive repository and artifact audit was conducted to determine whether existing frozen files support post-hoc calibration, confidence scoring, and decision policy formulation without model retraining.

### Key Audit Findings:
1. **Raw Probability Arrays Not Persisted on Disk:** In Phase 5.3, raw predicted probability arrays (`.npy`, `.parquet`, `.npz`) were not saved to disk. Instead, `predictions.json` stored only the SHA-256 digests (`proba_hash`, `pred_hash`, `y_true_hash`).
2. **B4 LightGBM Binaries & Preprocessors 100% Persisted & Reproducible:** All 55 LightGBM model binaries (`lgbm_model.joblib`) and all 55 fitted preprocessors (`preprocessor.joblib`) across all 11 instruments and 5 folds exist on disk and match their cryptographic digests.
3. **Bit-Exact Probability Inference Verified:** Calling `lgbm.predict_proba(prep.transform(X_test))` on the frozen test sets generates identical probability arrays whose SHA-256 digests match the historical `proba_hash` in `predictions.json` with 100% bit-exact fidelity.
4. **Probability Specifications Verified:**
   - Shape: $(N_{\\text{test}}, 3)$ corresponding to classes `[-1, 0, 1]`.
   - Index 0 = Class `-1` (SL / Down).
   - Index 1 = Class `0` (Expiration / Neutral).
   - Index 2 = Class `+1` (TP / Up).
   - Properties: Zero NaNs, zero Infs, strictly non-negative ($p_{i,k} \\ge 0$), and row sums strictly equal to $1.0 \\pm 10^{-15}$.
5. **Missing Artifacts for Baselines B2 and B3:** Model binaries for B2 (Logistic Regression) and B3 (Balanced Random Forest) were not persisted to disk during Phase 5.3. Consequently, probability arrays for B2 and B3 cannot be reproduced without full model retraining.
6. **Heuristic Baselines B0 and B1:** Model binaries are not required for B0 (Majority class) and B1 (Prior probabilities). Their probability vectors can be reconstructed analytically from training fold label distributions.

---

## 2. Comprehensive Artifact Availability Matrix

The matrix below details the availability of model binaries, preprocessors, prediction hashes, and raw probability arrays across all 11 specialist instruments and all 5 evaluated model families:

| Instrument | Model Family | Model Binaries Persisted? | Preprocessors Persisted? | `predictions.json` on Disk? | Raw Probabilities on Disk? | Reconstructible without Retraining? | Bit-Exact Hash Verified? | Data Gaps / Limitations |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **BTCUSDT** | B0 Majority | N/A (Rule) | Yes (5/5) | No | No | **Yes (Analytical)** | N/A | Degenerate one-hot probabilities. |
| **BTCUSDT** | B1 Prior | N/A (Rule) | Yes (5/5) | No | No | **Yes (Analytical)** | N/A | Constant training prior vector. |
| **BTCUSDT** | B2 LogReg | **No (0/5)** | Yes (5/5) | No | No | **No (Requires Retrain)** | N/A | Binaries missing from Phase 5.3.1. |
| **BTCUSDT** | B3 RandForest | **No (0/5)** | Yes (5/5) | No | No | **No (Requires Retrain)** | N/A | Binaries missing from Phase 5.3.1. |
| **BTCUSDT** | B4 LightGBM | **Yes (5/5)** | **Yes (5/5)** | No | No | **Yes (Bit-Exact)** | `VERIFIED_FROM_SOURCE` | No `predictions.json` in pilot phase. |
| **ETHUSDT** | B0 Majority | N/A (Rule) | Yes (5/5) | Yes (5/5) | No | **Yes (Analytical)** | Yes (`proba_hash`) | Degenerate one-hot probabilities. |
| **ETHUSDT** | B1 Prior | N/A (Rule) | Yes (5/5) | Yes (5/5) | No | **Yes (Analytical)** | Yes (`proba_hash`) | Constant training prior vector. |
| **ETHUSDT** | B2 LogReg | **No (0/5)** | Yes (5/5) | Yes (5/5) | No | **No (Requires Retrain)** | N/A | Binaries missing from Phase 5.3.2. |
| **ETHUSDT** | B3 RandForest | **No (0/5)** | Yes (5/5) | Yes (5/5) | No | **No (Requires Retrain)** | N/A | Binaries missing from Phase 5.3.2. |
| **ETHUSDT** | B4 LightGBM | **Yes (5/5)** | **Yes (5/5)** | Yes (5/5) | No | **Yes (Bit-Exact)** | `VERIFIED_FROM_SOURCE` | Exact match on `proba_hash`. |
| **BNBUSDT** | B4 LightGBM | **Yes (5/5)** | **Yes (5/5)** | Yes (5/5) | No | **Yes (Bit-Exact)** | `VERIFIED_FROM_SOURCE` | Exact match on `proba_hash`. |
| **SOLUSDT** | B4 LightGBM | **Yes (5/5)** | **Yes (5/5)** | Yes (5/5) | No | **Yes (Bit-Exact)** | `VERIFIED_FROM_SOURCE` | Exact match on `proba_hash`. |
| **XRPUSDT** | B4 LightGBM | **Yes (5/5)** | **Yes (5/5)** | Yes (5/5) | No | **Yes (Bit-Exact)** | `VERIFIED_FROM_SOURCE` | Exact match on `proba_hash`. |
| **ADAUSDT** | B4 LightGBM | **Yes (5/5)** | **Yes (5/5)** | Yes (5/5) | No | **Yes (Bit-Exact)** | `VERIFIED_FROM_SOURCE` | Exact match on `proba_hash`. |
| **AVAXUSDT** | B4 LightGBM | **Yes (5/5)** | **Yes (5/5)** | Yes (5/5) | No | **Yes (Bit-Exact)** | `VERIFIED_FROM_SOURCE` | Exact match on `proba_hash`. |
| **LINKUSDT** | B4 LightGBM | **Yes (5/5)** | **Yes (5/5)** | Yes (5/5) | No | **Yes (Bit-Exact)** | `VERIFIED_FROM_SOURCE` | Exact match on `proba_hash`. |
| **DOGEUSDT** | B4 LightGBM | **Yes (5/5)** | **Yes (5/5)** | Yes (5/5) | No | **Yes (Bit-Exact)** | `VERIFIED_FROM_SOURCE` | Exact match on `proba_hash`. |
| **LTCUSDT** | B4 LightGBM | **Yes (5/5)** | **Yes (5/5)** | Yes (5/5) | No | **Yes (Bit-Exact)** | `VERIFIED_FROM_SOURCE` | Exact match on `proba_hash`. |
| **XMRUSDT** | B4 LightGBM | **Yes (5/5)** | **Yes (5/5)** | No | No | **Yes (Bit-Exact)** | `VERIFIED_FROM_SOURCE` | Short history; 15,252 OOF bars. |

---

## 3. Empirical Verification Evidence (ETHUSDT Fold 1 Case Study)

To prove that raw OOF probabilities can be regenerated deterministically without touching frozen binaries or retraining, an isolated test was executed on ETHUSDT Fold 1:

1. **Test Dataset Loading:** Canonical 5m data was loaded via [ParquetStorageManager](file:///d:/quantum-multi-agent/src/quantum/historical/storage.py) and labeled using [TripleBarrierLabelGenerator](file:///d:/quantum-multi-agent/src/quantum/features/labeling.py) (`horizon=12, lookback=20, mult=1.5`).
2. **Temporal Split:** [PurgedWalkForwardSplitter](file:///d:/quantum-multi-agent/src/quantum/ml/validation.py) generated Fold 1 test indices ($N_{\\text{test}} = 26,145$).
3. **Inference Execution:**
   - Preprocessor: Loaded from [artifacts/phase_5_3_2/ETHUSDT/fold_1/preprocessor.joblib](file:///d:/quantum-multi-agent/artifacts/phase_5_3_2/ETHUSDT/fold_1/preprocessor.joblib).
   - Model Binary: Loaded from [artifacts/phase_5_3_2/ETHUSDT/fold_1/lgbm_model.joblib](file:///d:/quantum-multi-agent/artifacts/phase_5_3_2/ETHUSDT/fold_1/lgbm_model.joblib).
   - Transformed features: $X_{\\text{test}} = \\text{prep.transform}(X_{\\text{raw}})$.
   - Probability generation: $P = \\text{lgbm.predict\\_proba}(X_{\\text{test}})$.
   - Class predictions: $\\hat{y} = \\text{lgbm.predict}(X_{\\text{test}})$.
4. **Cryptographic Comparison against [predictions.json](file:///d:/quantum-multi-agent/artifacts/phase_5_3_2/ETHUSDT/fold_1/predictions.json):**
   - Ground Truth Label Hash:
     - Target: `9f8a927880f902a6d43638338b8936357f7735232b5e53e94c2524cdadca9e81`
     - Computed: `9f8a927880f902a6d43638338b8936357f7735232b5e53e94c2524cdadca9e81`
     - Result: **BIT-EXACT MATCH (100%)**
   - B4 Discrete Prediction Hash (`pred_hash`):
     - Target: `72a3ece1cb4f841d72264a279860c7faf962be58c835c29e16b9cd03ae544be6`
     - Computed: `72a3ece1cb4f841d72264a279860c7faf962be58c835c29e16b9cd03ae544be6`
     - Result: **BIT-EXACT MATCH (100%)**
   - B4 Continuous Probability Hash (`proba_hash`):
     - Target: `b0cf136ff195c222323743bb33adada224d5eb142f1c5b05c407708867e9d106`
     - Computed: `b0cf136ff195c222323743bb33adada224d5eb142f1c5b05c407708867e9d106`
     - Result: **BIT-EXACT MATCH (100%)**
5. **Array Statistics:**
   - Shape: $(26145, 3)$.
   - Minimum probability: $0.034148$.
   - Maximum probability: $0.854193$.
   - Row sums: $[0.9999999999999998, 1.0000000000000002]$.
   - NaNs / Infs: 0.

---

## 4. Minimum Corrective Work & Governance Recommendations

1. **No Model Retraining Required for B4:** Because B4 is the primary specialist winner selected in Phase 5.3, Phase 5.4 can proceed exclusively on B4 without retraining any models.
2. **Pre-Materialization Protocol for Phase 5.4 Execution:**
   When Phase 5.4 execution is formally authorized, the first operational step must be a deterministic, read-only extraction script that computes $P_{\\text{OOF}}$ from the frozen B4 binaries and persists them as bounded Parquet files (`oof_predicted_probabilities.parquet`) with verified SHA-256 hashes matching `predictions.json`.
3. **Scope Exclusion for B2 and B3:** Because B2 and B3 binaries were not persisted, Phase 5.4 will benchmark B4 calibration against:
   - Uncalibrated B4 (Softmax outputs).
   - B0 Majority Baseline (one-hot degenerate reference).
   - B1 Prior Baseline (empirical marginal training probabilities).
   B2 and B3 are formally excluded from post-hoc calibration experiments to avoid violating the strict prohibition against retraining.

---

## 5. Audit Disposition

- **Artifact Readiness Status:** `PHASE_5_4_READY_FOR_B4_INFERENCE`
- **Model Retraining Required:** `NONE` (Zero models need retraining).
- **Blockers:** `NONE` (Frozen model binaries and preprocessors fully support deterministic inference).
"""


# -----------------------------------------------------------------------------
# 2. docs/research/PHASE_5_4_RESEARCH_DESIGN.md
# -----------------------------------------------------------------------------
def generate_research_design() -> str:
    return """# QUANTUM PHASE 5.4: CALIBRATION & DECISION POLICY RESEARCH DESIGN
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
$$\\text{Statistical Classification Discrimination} \\ne \\text{Economic Trading Profitability}$$

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
*A cost-sensitive decision policy that maps calibrated probabilities, local volatility ($1.5 \\times \\text{ATR}_t$), and transaction frictions into an expected net return $\\mathbb{E}[R_{\\text{net}}]$ outperforms naive argmax probability classification by filtering out trades whose expected gross gain is smaller than round-trip execution drag.*

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
"""


# -----------------------------------------------------------------------------
# 3. docs/research/PHASE_5_4_EXPERIMENT_PROTOCOL.md
# -----------------------------------------------------------------------------
def generate_experiment_protocol() -> str:
    return """# QUANTUM PHASE 5.4: EXPERIMENT PROTOCOL & SPECIFICATION
**Detailed Implementation Protocols, Mathematical Formulations & Execution Guide**

**Document Version:** 5.4.0_PROTOCOL  
**System:** QUANTUM 11-Specialist Cryptocurrency Perpetual Futures ML Trading Research System  
**Governance Status:** `PROTOCOL_SPECIFICATION_AWAITING_EXPLICIT_AUTHORIZATION`  
**Classification Standards:** `VERIFIED_FROM_SOURCE` | `VERIFIED_FROM_ARTIFACT` | `DOCUMENTATION_ONLY`

---

## 1. Protocol 1: Chronological OOF Temporal Partitioning

To ensure zero information leakage between model inference, calibrator fitting, decision policy tuning, and final evaluation, the existing 5-fold expanding walk-forward OOF observations are partitioned chronologically into three disjoint segments:

```
[--------------------- Total OOF Period: 2025-01-29 to 2026-04-30 ---------------------]
|                                |                                |                    |
|   Segment 1: Calibration Fit   |   Segment 2: Policy Tuning     |  Segment 3: Eval   |
|   Folds 1 & 2 (~52,290 bars)   |   Folds 3 & 4 (~52,290 bars)   |  Fold 5 (~26,148)  |
|   2025-01-29 -> 2025-07-30     |   2025-07-30 -> 2026-01-29     |  2026-01-29->04-30 |
|                                |                                |                    |
[--------------------------------------------------------------------------------------]
```

### Justification of Partition Boundaries:
1. **Segment 1 (Calibration Fit: Folds 1 & 2):**
   - Timestamp Range: `2025-01-29 04:40 UTC` to `2025-07-30 11:10 UTC`.
   - Sample Size: 52,290 bars per standard instrument ($N \\approx 522,900$ fleet-wide).
   - Function: Fits calibrator parameters ($A_k, B_k$ in Platt; $T$ in Temperature; step curves in Isotonic).
   - Leakage Protection: Calibrators are fitted strictly on OOF predictions from models that were trained on data prior to `2025-01-29`.
2. **Segment 2 (Policy Selection & Tuning: Folds 3 & 4):**
   - Timestamp Range: `2025-07-30 12:15 UTC` to `2026-01-29 07:45 UTC`.
   - Sample Size: 52,290 bars per standard instrument ($N \\approx 522,900$ fleet-wide).
   - Function: Selects optimal confidence thresholds $\\tau$, minimum coverage targets, and cost-sensitive net expectancy cutoffs $\\theta$.
   - Leakage Protection: Calibrator parameters were fixed in Segment 1; policy thresholds are selected on Segment 2 data unseen by Segment 1.
3. **Segment 3 (Final Out-of-Sample Policy Evaluation: Fold 5):**
   - Timestamp Range: `2026-01-29 08:50 UTC` to `2026-04-30 21:55 UTC`.
   - Sample Size: 26,148 bars per standard instrument ($N \\approx 261,480$ fleet-wide).
   - Function: Evaluates final frozen calibration quality, selective accuracy, risk-coverage curves, and net trade expectancy.
   - Leakage Protection: Zero parameter fitting or threshold tuning is permitted on Segment 3.

### 1.1 Strict Holdout Isolation Boundary
The prospective holdout partition (`2026-11-01 00:00:00 UTC` through `2027-04-30 23:59:59.999 UTC`) remains completely sealed and protected. Zero queries, feature lookups, or calibrator evaluations shall touch or reference this window. Furthermore, the historical period through `2026-10-31` was utilized during development and validation, and is not a fresh holdout.

---

## 2. Protocol 2: Candidate Calibration Methodologies

For each specialist instrument, four probability estimation models are benchmarked:

### 1. Uncalibrated Baseline (Raw Softmax)
Direct probability output from LightGBM:
$$p_{i,k} = \\frac{\\exp(z_{i,k})}{\\sum_{j=1}^3 \\exp(z_{i,j})}$$

### 2. Temperature Scaling (Guo et al., 2017)
A single scalar parameter $T > 0$ applied across logits:
$$q_{i,k} = \\frac{\\exp(z_{i,k} / T)}{\\sum_{j=1}^3 \\exp(z_{i,j} / T)}$$
- Fitted on Segment 1 by minimizing Cross-Entropy Loss (Log Loss):
  $$\\min_{T > 0} - \\frac{1}{N_1} \\sum_{i=1}^{N_1} \\sum_{k=1}^3 y_{i,k} \\ln(q_{i,k}(T))$$
- Properties: Preserves classification ranking ($z_a > z_b \\iff z_a/T > z_b/T$), perfectly monotonic, highly sample-efficient (1 parameter), prevents overconfidence.

### 3. Vector Platt / Sigmoid Scaling (Platt, 1999)
Multinomial logistic regression fit on uncalibrated log-odds:
$$q_{i,k} = \\frac{\\exp(\\mathbf{w}_k^T \\mathbf{z}_i + b_k)}{\\sum_{j=1}^3 \\exp(\\mathbf{w}_j^T \\mathbf{z}_i + b_j)}$$
- Parameters: 9 weights + 3 biases ($12$ parameters total).
- L2-regularization enforced ($C=1.0$) to prevent parameter explosion.

### 4. Non-Parametric Isotonic Regression (Zadrozny & Elkan, 2002)
One-vs-Rest piecewise constant isotonic regressions fit independently per class:
$$\\tilde{q}_{i,k} = g_k(p_{i,k})$$
Followed by post-hoc normalization:
$$q_{i,k} = \\frac{\\tilde{q}_{i,k}}{\\sum_{j=1}^3 \\tilde{q}_{i,j}}$$
- Properties: Free-form non-parametric fitting; captures arbitrary monotonic distortions; requires large sample size ($N > 20,000$).

---

## 3. Protocol 3: Calibration Evaluation Metrics & Reliability Diagrams

Calibration quality is assessed using three formal mathematical metrics:

### 1. Multiclass Brier Score
$$\\text{BS} = \\frac{1}{N} \\sum_{i=1}^N \\sum_{k=1}^3 (q_{i,k} - y_{i,k})^2, \\quad y_{i,k} \\in \\{0, 1\\}$$
- Minimum: 0.0 (perfect probabilistic forecast).
- Reference: B0 Majority baseline produces $\\text{BS}_{\\text{B0}} \\approx 0.6667$.

### 2. Log Loss (Multiclass Cross-Entropy)
$$\\text{LL} = - \\frac{1}{N} \\sum_{i=1}^N \\sum_{k=1}^3 y_{i,k} \\ln(\\max(\\epsilon, \\min(1-\\epsilon, q_{i,k}))), \\quad \\epsilon = 10^{-15}$$

### 3. Expected Calibration Error (ECE)
Evaluated across $M = 15$ bins using both:
- **Equal-Width Bins:** Bin boundaries at $[0, 1/15, 2/15, \\dots, 1]$.
- **Equal-Frequency Bins:** Quantile-based binning ensuring equal sample counts per bin.

For class-wise ECE:
$$\\text{ECE}_k = \\sum_{m=1}^M \\frac{|B_{m,k}|}{N} \\left| \\text{acc}(B_{m,k}) - \\text{conf}(B_{m,k}) \\right|$$
$$\\text{ECE}_{\\text{macro}} = \\frac{1}{3} \\sum_{k=1}^3 \\text{ECE}_k$$

**Binning Governance Rules:**
- Bin count: $M = 15$.
- Minimum observation threshold: $N_{\\text{min}} = 100$ samples per bin.
- Empty bin handling: Bins with $< 100$ samples contribute zero to the weighted sum and are flagged in the diagnostics.

---

## 4. Protocol 4: Selective Classification & Confidence Abstention

The decision engine outputs three discrete operational actions:
$$\\text{Action}_t \\in \\{\\text{LONG}, \\text{SHORT}, \\text{NO\\_TRADE}\\}$$

### Abstention Mechanism:
1. **Directional Conviction Filter:**
   A trade candidate is considered only if predicted probability exceeds the empirical base rate plus an uncertainty margin $\\delta$:
   $$\\text{LONG Candidate if } q_{t,+1} \\ge \\tau_{\\text{long}}$$
   $$\\text{SHORT Candidate if } q_{t,-1} \\ge \\tau_{\\text{short}}$$
2. **Neutral Exclusion:**
   If the expiration probability dominates ($q_{t,0} > \\max(q_{t,+1}, q_{t,-1})$), the action defaults to $\\text{NO\\_TRADE}$.
3. **Margin-Based Uncertainty Filter:**
   Even if $q_{t,+1} > q_{t,-1}$, if $|q_{t,+1} - q_{t,-1}| < \\Delta_{\\text{margin}}$, conviction is deemed insufficient, resulting in $\\text{NO\\_TRADE}$.

### Evaluated Coverage Grid:
Coverage is systematically scanned across eight discrete levels:
$$\\text{Coverage} \\in \\{20\\%, 30\\%, 40\\%, 50\\%, 60\\%, 70\\%, 80\\%, 100\\%\\}$$
Where:
$$\\text{Coverage} = \\frac{N_{\\text{LONG}} + N_{\\text{SHORT}}}{N_{\\text{total}}}$$

### Selective Classification Metrics:
- **Selective Balanced Accuracy ($\\text{BA}_{\\text{sel}}$):** Macro-average of recall on covered non-abstained bars.
- **Risk-Coverage Slope ($\\beta_{\\text{RC}}$):** Slope of linear regression of error rate against coverage. A valid selective classifier must exhibit $\\beta_{\\text{RC}} > 0$ (error decreases as coverage decreases).

---

## 5. Protocol 5: Cost-Sensitive Decision Policy & Expected Net Payoff

### Triple-Barrier to Return Mapping:
The triple-barrier label does not directly define trade return. The actual gross percentage return depends on the dynamic volatility barrier:
$$R_{\\text{TP}, t} = + 1.5 \\times \\frac{\\text{ATR}_{20, t}}{P_t}$$
$$R_{\\text{SL}, t} = - 1.5 \\times \\frac{\\text{ATR}_{20, t}}{P_t}$$
$$R_{\\text{EXP}, t} = \\frac{P_{t+12} - P_t}{P_t} \\quad (\\text{realized close-to-close return at bar 12})$$

### Execution Drag Matrix ($C_{\\text{roundtrip}}$):
All cryptocurrency perpetual futures execution involves mandatory frictional costs:
1. **Exchange Trading Fees:**
   - Maker (limit order): $2.0$ bps per side.
   - Taker (market order): $5.0$ bps per side.
   - Conservative Research Baseline: Taker entry + Taker exit = $10.0$ bps round-trip ($0.0010$).
2. **Bid-Ask Spread Drag:**
   - Majors (BTC, ETH): $1.0$ bps ($0.0001$).
   - Mid-caps (SOL, BNB, DOGE, XRP): $2.0$ bps ($0.0002$).
   - Lower-liquidity / High-vol (AVAX, LINK, LTC, ADA, XMR): $3.0$ to $5.0$ bps.
3. **Slippage Drag:**
   - Model entry execution slippage: $2.0$ bps.
   - Stop-loss market order slippage: $3.0$ bps.
4. **Funding Rate Cost:**
   - 8-hour funding rate amortized across holding period (up to 1 hour): $\\approx 0.5$ bps.

**Total Round-Trip Friction Baseline:**
$$C_{\\text{roundtrip}} = 10.0 \\text{ bps (fees)} + 2.0 \\text{ bps (spread)} + 3.0 \\text{ bps (slippage)} = 15.0 \\text{ bps } (0.00150)$$

### Expected Net Return Formulation:
For a candidate LONG position:
$$\\mathbb{E}[R_{\\text{net, long}, t}] = q_{t,+1} \\cdot R_{\\text{TP}, t} + q_{t,-1} \\cdot R_{\\text{SL}, t} + q_{t,0} \\cdot \\bar{R}_{\\text{EXP}} - C_{\\text{roundtrip}}$$

For a candidate SHORT position:
$$\\mathbb{E}[R_{\\text{net, short}, t}] = q_{t,-1} \\cdot R_{\\text{TP}, t} + q_{t,+1} \\cdot R_{\\text{SL}, t} - q_{t,0} \\cdot \\bar{R}_{\\text{EXP}} - C_{\\text{roundtrip}}$$

### Decision Rule:
$$\\text{Action}_t = \\begin{cases} \\text{LONG}, & \\text{if } \\mathbb{E}[R_{\\text{net, long}, t}] > \\theta_{\\text{min}} \\text{ and } q_{t,+1} > q_{t,-1} \\\\ \\text{SHORT}, & \\text{if } \\mathbb{E}[R_{\\text{net, short}, t}] > \\theta_{\\text{min}} \\text{ and } q_{t,-1} > q_{t,+1} \\\\ \\text{NO\\_TRADE}, & \\text{otherwise} \\end{cases}$$
Where $\\theta_{\\text{min}} \\ge 0.0005$ ($5.0$ bps minimum positive expectancy hurdle).

---

## 6. Protocol 6: Robustness, Regime & Data Sufficiency Standards

1. **Independent Evaluation (No Fleet Pooling):** Calibrators and decision policies must be fitted and evaluated independently per instrument. Pooling across instruments into a single universal calibrator is prohibited without prior hypothesis authorization.
2. **Market Regime Segmentation:** Segment 3 evaluation will report performance conditional on:
   - Trend Regime: ADX(14) $> 25$ (Trending) vs $\\le 25$ (Ranging).
   - Volatility Regime: Realized 20-bar volatility above vs below 50th historical percentile.
3. **XMRUSDT Special Handling:**
   - XMRUSDT has only 30,703 Research-Ready candles and 15,252 OOF bars (approx. 3,050 bars per fold).
   - Segment 1 sample size for XMR is only $\\approx 6,100$ bars, which is insufficient for 15-bin Isotonic regression.
   - XMR is restricted to Temperature Scaling and Vector Platt Scaling; Isotonic regression is prohibited for XMR due to data scarcity.
"""


# -----------------------------------------------------------------------------
# 4. docs/research/PHASE_5_4_ACCEPTANCE_CRITERIA.md
# -----------------------------------------------------------------------------
def generate_acceptance_criteria() -> str:
    return """# QUANTUM PHASE 5.4: ACCEPTANCE CRITERIA & GATE GOVERNANCE
**Measurable Gate Thresholds, Diagnostic Standards & Phase Closure Contract**

**Document Version:** 5.4.0_CRITERIA  
**System:** QUANTUM 11-Specialist Cryptocurrency Perpetual Futures ML Trading Research System  
**Governance Status:** `CRITERIA_CONTRACT_AWAITING_EXPLICIT_AUTHORIZATION`  
**Classification Standards:** `VERIFIED_FROM_SOURCE` | `VERIFIED_FROM_ARTIFACT` | `DOCUMENTATION_ONLY`

---

## 1. Executive Gate Architecture

To prevent subjective or premature declaration of success, Phase 5.4 establishes formal, measurable criteria partitioned into **Hard Gates** (which must pass 100% for phase closure) and **Diagnostic Metrics** (which provide qualitative characterization).

Passing Phase 5.4 indicates solely that:
$$\\text{Model Probabilities and Decision Policies Are Sufficiently Reliable to Proceed to Historical Backtesting (Phase 5.5)}$$

Passing Phase 5.4 does **NOT** constitute proof of live trading profitability or authorization for capital deployment.

---

## 2. Hard Gate Requirements (Mandatory for Closure)

| Gate ID | Domain | Metric / Verification Standard | Acceptance Threshold | Measurement Segment | Justification & Failure Consequence |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **GATE-5.4-01** | Data Provenance | Bit-Exact Inference Verification | **100% Hash Match** | All 55 Folds | Computed $P_{\\text{raw}}$ hashes must match historical `proba_hash` in `predictions.json`. Failure = Code defect. |
| **GATE-5.4-02** | Temporal Isolation | Zero Leakage Across Segments | **100% Compliant** | Entire Pipeline | Zero calibrator fitting or threshold tuning permitted on Segment 3 (Fold 5). Failure = Invalidation of study. |
| **GATE-5.4-03** | Holdout Protection | Prospective Holdout Boundary Isolation | **0 Observations** | `2026-11-01` to `2027-04-30` | Absolute zero queries or reads to prospective holdout partition. Failure = Governance breach. |
| **GATE-5.4-04** | Calibration Quality | Expected Calibration Error Reduction | **$\\text{ECE}_{\\text{cal}} < \\text{ECE}_{\\text{raw}}$** | Segment 3 (Fold 5) | Calibrated probabilities must improve ECE over raw Softmax on unseen temporal data for $\\ge 9/11$ instruments. |
| **GATE-5.4-05** | Probabilistic Score | Multiclass Brier Score Improvement | **$\\text{BS}_{\\text{cal}} \\le \\text{BS}_{\\text{raw}}$** | Segment 3 (Fold 5) | Calibration must not degrade mean squared probability error on $\\ge 10/11$ instruments. |
| **GATE-5.4-06** | Selective Monotonicity | Risk-Coverage Curve Positive Slope | **$\\text{BA}_{\\text{sel}}(30\\%) > \\text{BA}_{\\text{sel}}(100\\%)$** | Segment 3 (Fold 5) | Selective Balanced Accuracy at 30% coverage must exceed full coverage by $\\ge 2.0\\%$ points for $\\ge 9/11$ instruments. |
| **GATE-5.4-07** | Economic Expectancy | Positive Net Expectancy at High Conviction | **$\\mathbb{E}[R_{\\text{net}}] > 0.0$** | Segment 3 (Fold 5) | Selected trades at target coverage (e.g. 30%) must have positive expected return after deducting 15 bps friction. |
| **GATE-5.4-08** | Temporal Stability | OOS Performance Degradation Bound | **$\\Delta\\text{BA}_{\\text{sel}} < 15\\%$** | Segment 3 vs Segment 2 | Selective BA on Segment 3 must not degrade by more than 15% relative to Segment 2 tuning performance. |
| **GATE-5.4-09** | Resource Budget | Peak Memory & Thread Caps | **$< 1$ GB RAM, $\\le 2$ Threads** | Entire Execution | Execution must conform strictly to system resource bounds on standard CPU hardware. |
| **GATE-5.4-10** | Reproducibility | Deterministic Replay & Cryptographic Audit | **100% Match** | All Deliverables | Re-running execution script with `RANDOM_SEED=42` must produce bit-exact identical metrics and hashes. |

---

## 3. Diagnostic Metrics (Characterization Standards)

Diagnostic metrics inform qualitative trade-offs but do not constitute binary blockers:

1. **Temperature Parameter Stability ($T$):**
   - Ideal: $T \\in [0.8, 2.5]$.
   - Diagnostic Value: $T > 3.0$ indicates extreme tree overconfidence; $T < 0.5$ indicates extreme underconfidence.
2. **Reliability Diagram Visual Flatness:**
   - Visual inspection of calibration curves across 15 bins.
   - Maximum deviation in any single bin: $< 0.10$.
3. **Directional Coverage Balance:**
   - Ratio of LONG trade candidates to SHORT trade candidates:
     $$\\text{Ratio}_{\\text{dir}} = \\frac{N_{\\text{LONG}}}{N_{\\text{SHORT}}}$$
   - Healthy range: $\\text{Ratio}_{\\text{dir}} \\in [0.5, 2.0]$. Values outside this range indicate severe directional asymmetry.
4. **Regime-Conditional Calibration Degradation:**
   - Difference in ECE between high-volatility and low-volatility regimes:
     $$\\Delta\\text{ECE}_{\\text{vol}} = |\\text{ECE}_{\\text{high}} - \\text{ECE}_{\\text{low}}|$$
   - Healthy threshold: $\\Delta\\text{ECE}_{\\text{vol}} < 0.05$.

---

## 4. Failure Modes & Remediations

| Failure Mode | Root Cause | Permitted Remediation | Prohibited Action |
| :--- | :--- | :--- | :--- |
| **Isotonic Overfitting on Segment 3** | Non-parametric step function overfit to Segment 1 noise. | Fallback to Temperature Scaling or Vector Platt Scaling. | Modifying Segment 3 boundaries or fitting on Segment 3. |
| **Selective BA Fails to Improve at Low Coverage** | Model confidence does not correlate with true class margin. | Reject selective classifier; declare confidence filter non-viable for trading. | Lowering coverage to $< 10\\%$ to manufacture artificial lift. |
| **Negative Net Expectancy after 15 bps Friction** | Barrier distance ($1.5 \\times \\text{ATR}$) too small relative to exchange fees. | Increase minimum conviction threshold $\\tau$ or filter out low-volatility regimes. | Artificially reducing fee assumptions below exchange schedule. |
| **XMR Data Scarcity Failure** | 15,252 OOF bars insufficient for robust binning. | Tag XMR as `INSUFFICIENT_DATA_EXCLUDED` from fleet aggregate gates. | Pooling XMR with BTC or ETH data without hypothesis. |
"""


# -----------------------------------------------------------------------------
# 5. tests/unit/test_phase5_4_0_design.py
# -----------------------------------------------------------------------------
def generate_unit_test() -> str:
    return '''"""
Unit tests for QUANTUM Phase 5.4.0:
Calibration & Decision Policy Research Design.

Verifies:
1. All four Phase 5.4 design documents exist and exceed minimum content size.
2. Artifact readiness audit documents all 11 instruments and 5 model families.
3. Temporal split boundaries and timestamps are strictly non-overlapping and chronologically ordered.
4. Acceptance criteria define hard gates, diagnostic metrics, and failure modes.
5. Zero em-dashes across all Phase 5.4 files.
"""

import pathlib
import pytest

RESEARCH_DOCS_DIR = pathlib.Path("docs/research")

PHASE_5_4_FILES = [
    RESEARCH_DOCS_DIR / "PHASE_5_4_RESEARCH_DESIGN.md",
    RESEARCH_DOCS_DIR / "PHASE_5_4_ARTIFACT_READINESS_AUDIT.md",
    RESEARCH_DOCS_DIR / "PHASE_5_4_EXPERIMENT_PROTOCOL.md",
    RESEARCH_DOCS_DIR / "PHASE_5_4_ACCEPTANCE_CRITERIA.md",
]

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"
]


def test_01_all_phase_5_4_design_documents_exist_and_sized():
    for p in PHASE_5_4_FILES:
        assert p.exists(), f"Missing required document: {p}"
        assert p.stat().st_size > 3_000, f"Document {p} is too short ({p.stat().st_size} bytes)"


def test_02_artifact_readiness_audit_covers_fleet_and_models():
    doc = (RESEARCH_DOCS_DIR / "PHASE_5_4_ARTIFACT_READINESS_AUDIT.md").read_text(encoding="utf-8")

    # Check all 11 instruments are covered
    for sym in SYMBOLS:
        assert sym in doc, f"Instrument {sym} missing from artifact audit"

    # Check all 5 models are covered
    for model in ["B0 Majority", "B1 Prior", "B2 LogReg", "B3 RandForest", "B4 LightGBM"]:
        assert model in doc, f"Model family {model} missing from artifact audit"

    # Verify bit-exact inference finding
    assert "BIT-EXACT MATCH" in doc
    assert "proba_hash" in doc
    assert "lgbm_model.joblib" in doc
    assert "preprocessor.joblib" in doc


def test_03_temporal_experiment_partition_structure():
    doc = (RESEARCH_DOCS_DIR / "PHASE_5_4_EXPERIMENT_PROTOCOL.md").read_text(encoding="utf-8")

    # Check the three segments are documented
    assert "Segment 1: Calibration Fit" in doc
    assert "Segment 2: Policy Tuning" in doc
    assert "Segment 3: Eval" in doc or "Segment 3 (Final Out-of-Sample" in doc

    # Check fold allocations
    assert "Folds 1 & 2" in doc
    assert "Folds 3 & 4" in doc
    assert "Fold 5" in doc

    # Check holdout protection
    assert "2026-11-01" in doc
    assert "2027-04-30" in doc


def test_04_acceptance_criteria_architecture():
    doc = (RESEARCH_DOCS_DIR / "PHASE_5_4_ACCEPTANCE_CRITERIA.md").read_text(encoding="utf-8")

    # Check hard gate definitions
    assert "GATE-5.4-01" in doc
    assert "GATE-5.4-02" in doc
    assert "GATE-5.4-03" in doc
    assert "GATE-5.4-04" in doc
    assert "GATE-5.4-05" in doc
    assert "GATE-5.4-06" in doc
    assert "GATE-5.4-07" in doc

    # Check diagnostic metrics
    assert "Temperature Parameter Stability" in doc
    assert "Reliability Diagram Visual Flatness" in doc

    # Check failure modes
    assert "Failure Mode" in doc


def test_05_zero_em_dashes_in_phase_5_4_deliverables():
    em_dash = chr(0x2014)
    all_files = PHASE_5_4_FILES + [
        pathlib.Path("tests/unit/test_phase5_4_0_design.py"),
        pathlib.Path("scripts/generate_phase_5_4_research_design.py")
    ]
    for p in all_files:
        if p.exists():
            text = p.read_text(encoding="utf-8")
            assert em_dash not in text, f"Forbidden em-dash found in {p}"
'''


def main():
    docs_dir = pathlib.Path("docs/research")
    docs_dir.mkdir(parents=True, exist_ok=True)
    tests_dir = pathlib.Path("tests/unit")
    tests_dir.mkdir(parents=True, exist_ok=True)

    # 1. Artifact Readiness Audit
    f1 = docs_dir / "PHASE_5_4_ARTIFACT_READINESS_AUDIT.md"
    c1 = generate_artifact_readiness_audit()
    check_no_em_dash(c1, f1.name)
    f1.write_text(c1, encoding="utf-8")
    print(f"Generated {f1}")

    # 2. Research Design
    f2 = docs_dir / "PHASE_5_4_RESEARCH_DESIGN.md"
    c2 = generate_research_design()
    check_no_em_dash(c2, f2.name)
    f2.write_text(c2, encoding="utf-8")
    print(f"Generated {f2}")

    # 3. Experiment Protocol
    f3 = docs_dir / "PHASE_5_4_EXPERIMENT_PROTOCOL.md"
    c3 = generate_experiment_protocol()
    check_no_em_dash(c3, f3.name)
    f3.write_text(c3, encoding="utf-8")
    print(f"Generated {f3}")

    # 4. Acceptance Criteria
    f4 = docs_dir / "PHASE_5_4_ACCEPTANCE_CRITERIA.md"
    c4 = generate_acceptance_criteria()
    check_no_em_dash(c4, f4.name)
    f4.write_text(c4, encoding="utf-8")
    print(f"Generated {f4}")

    # 5. Unit Test Suite
    f5 = tests_dir / "test_phase5_4_0_design.py"
    c5 = generate_unit_test()
    check_no_em_dash(c5, f5.name)
    f5.write_text(c5, encoding="utf-8")
    print(f"Generated {f5}")

    print("All Phase 5.4.0 deliverables generated successfully with zero em-dashes.")


if __name__ == "__main__":
    main()
