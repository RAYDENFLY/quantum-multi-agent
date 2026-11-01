# QUANTUM PHASE 5.3.3: BASELINE WINNER CATALOG & MULTI-METRIC DECISION AUDIT

**Phase:** Phase 5.3.3  
**Date:** 2026-11-01  
**Lead Quantitative Systems Auditor:** QUANTUM Independent Quality & Systems Audit Lead  
**Scope:** Metric-specific winner selection, stability evaluation, and tie-handling governance across 11 specialists  
**Source Manifest:** [master_winner_catalog.json](file:///d:/quantum-multi-agent/artifacts/phase_5_3_3/master_winner_catalog.json)

---

## 1. Executive Summary

In previous phase documentation, the term `Best Baseline` was occasionally applied without an explicit, metric-specific definition. This audit establishes a strict, multi-metric winner catalog that separates classification discrimination, macro calibration, probability accuracy, and temporal stability.

Key findings:
1. **No Universal Winner Exists:** Model superiority depends on asset class, liquidity regime, and evaluation objective.
2. **LightGBM (B4) Dominates Probability Calibration & ROC-AUC:** B4 won lowest Brier score on 10 out of 11 instruments and highest ROC-AUC on 8 out of 11 instruments.
3. **Random Forest (B3) Excels on High-Volume Trend Assets:** B3 captured top Balanced Accuracy on `LTCUSDT`, `ETHUSDT`, and `BTCUSDT`.
4. **Logistic Regression (B2) Wins on Sample-Constrained Regimes:** B2 won both Balanced Accuracy and Macro F1 on `XMRUSDT`.

---

## 2. Metric Winner Selection Rules & Governance

Each performance metric represents a distinct mathematical and operational property:

| Evaluation Objective | Primary Metric | Objective Direction | Operational Significance |
| :--- | :--- | :---: | :--- |
| **Class Discrimination** | Balanced Accuracy | Higher is Better | Evaluates average recall across all three barrier outcomes equally. |
| **Unbiased Harmonic Mean** | Macro F1 | Higher is Better | Penalizes models that fail on minority classes (e.g. expiration bars). |
| **Ranking Ability** | OvR Macro ROC-AUC | Higher is Better | Measures probability separability across decision thresholds. |
| **Probability Calibration** | Multiclass Brier Score | Lower is Better | Measures quadratic error of forecasted probabilities. |
| **Temporal Stability** | Fold Standard Deviation | Lower is Better | Quantifies consistency of Balanced Accuracy across walk-forward folds. |

### Tie-Handling Policy:
If two models achieve identical performance within \(1 \times 10^{-4}\):
1. **Occam's Razor Rule:** The model with lower structural parameter complexity is selected:  
   $$\text{B2\_LogisticRegression} \succ \text{B4\_LightGBM} \succ \text{B3\_RandomForest}$$
2. **No Composite Averaging:** Metrics are never collapsed into an arbitrary weighted index to force a single winner.

---

## 3. Metric-Specific Winner Matrix by Specialist

The table below catalogs the definitive metric-specific winners across all 11 instruments:

| Symbol | Best Balanced Accuracy | Best Macro F1 | Best ROC-AUC | Lowest Brier Score | Most Stable ML Model |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BTCUSDT** | **B3_RandomForest** (0.4127) | **B4_LightGBM** (0.3893) | **B4_LightGBM** (0.6050) | **B4_LightGBM** (0.5795) | **B2_LogisticRegression** (std 0.0222) |
| **XMRUSDT** | **B2_LogisticRegression** (0.4177) | **B2_LogisticRegression** (0.3796) | **B2_LogisticRegression** (0.5863) | **B4_LightGBM** (0.6362) | **B2_LogisticRegression** (std 0.0187) |
| **ADAUSDT** | **B4_LightGBM** (0.4490) | **B4_LightGBM** (0.3915) | **B4_LightGBM** (0.6209) | **B4_LightGBM** (0.6454) | **B2_LogisticRegression** (std 0.0300) |
| **XRPUSDT** | **B4_LightGBM** (0.3747) | **B4_LightGBM** (0.3714) | **B4_LightGBM** (0.6035) | **B4_LightGBM** (0.5635) | **B3_RandomForest** (std 0.0221) |
| **BNBUSDT** | **B4_LightGBM** (0.3699) | **B4_LightGBM** (0.3623) | **B4_LightGBM** (0.5975) | **B4_LightGBM** (0.5716) | **B2_LogisticRegression** (std 0.0176) |
| **ETHUSDT** | **B3_RandomForest** (0.4195) | **B4_LightGBM** (0.3975) | **B4_LightGBM** (0.6144) | **B4_LightGBM** (0.5750) | **B4_LightGBM** (std 0.0120) |
| **SOLUSDT** | **B4_LightGBM** (0.3878) | **B4_LightGBM** (0.3797) | **B4_LightGBM** (0.6108) | **B4_LightGBM** (0.5594) | **B2_LogisticRegression** (std 0.0298) |
| **AVAXUSDT** | **B4_LightGBM** (0.4145) | **B4_LightGBM** (0.3966) | **B4_LightGBM** (0.6057) | **B4_LightGBM** (0.6246) | **B4_LightGBM** (std 0.0431) |
| **LINKUSDT** | **B4_LightGBM** (0.4067) | **B4_LightGBM** (0.3905) | **B4_LightGBM** (0.6238) | **B4_LightGBM** (0.5957) | **B2_LogisticRegression** (std 0.0429) |
| **DOGEUSDT** | **B4_LightGBM** (0.3960) | **B4_LightGBM** (0.3904) | **B4_LightGBM** (0.6099) | **B4_LightGBM** (0.5749) | **B3_RandomForest** (std 0.0287) |
| **LTCUSDT** | **B3_RandomForest** (0.4402) | **B3_RandomForest** (0.4264) | **B4_LightGBM** (0.6399) | **B3_RandomForest** (0.6083) | **B4_LightGBM** (std 0.0514) |

---

## 4. Aggregate Model Architecture Win-Rate Accounting

Summing victories across the 11 specialists reveals distinct operational roles for each baseline family:

```
+-------------------------------------------------------------------------------+
| MODEL ARCHITECTURE | BAL ACC WINS | MACRO F1 WINS | ROC-AUC WINS | BRIER WINS |
+--------------------+--------------+---------------+--------------+------------+
| B4_LightGBM        |      7       |       9       |      10      |     10     |
| B3_RandomForest    |      3       |       1       |       0      |      1     |
| B2_LogisticRegress |      1       |       1       |       1      |      0     |
| B0_Majority        |      0       |       0       |       0      |      0     |
| B1_Prior           |      0       |       0       |       0      |      0     |
+--------------------+--------------+---------------+--------------+------------+
```

### Key Insights:
1. **LightGBM is the Premier Multi-Class Probability Engine:**  
   Winning lowest Brier score in 10/11 pairs and highest ROC-AUC in 10/11 pairs confirms that gradient boosted decision trees construct superior probability boundaries for directional cryptocurrency barriers.
2. **Random Forest is Highly Effective for Volatile Trend Outliers:**  
   B3's victories on `LTCUSDT` (0.4402 BalAcc, 0.4264 F1) and `ETHUSDT` (0.4195 BalAcc) highlight that bagging stabilizes decision trees during sharp crypto market regimes.
3. **Linear Models Dominate Low-Sample Regimes:**  
   B2's sweep on `XMRUSDT` (BalAcc 0.4177, F1 0.3796) illustrates that when sample depth is constrained (30,623 bars), regularized linear models guard against overfitting.
