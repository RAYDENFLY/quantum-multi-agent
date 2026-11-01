# QUANTUM PHASE 5.3.3: NUMERICAL RECONCILIATION REPORT

**Phase:** Phase 5.3.3  
**Date:** 2026-11-01  
**Lead Quantitative Systems Auditor:** QUANTUM Independent Quality & Systems Audit Lead  
**Scope:** Independent recalculation of all fold-level and aggregate metrics across 11 specialist pairs  
**Source Manifest:** [numerical_reconciliation.json](file:///d:/quantum-multi-agent/artifacts/phase_5_3_3/numerical_reconciliation.json)

---

## 1. Executive Summary

An independent numerical reconciliation was performed across all 53 walk-forward folds and 265 baseline model evaluations (5 models x 53 folds). All reported metric values were recalculated directly from the original fold-level confusion matrices and probability outputs.

Key findings:
1. **Fold-Level Metric Fidelity:** Recalculated Accuracy, Balanced Accuracy, and Macro F1 matched reported values in `metrics.json` to four decimal places across all 265 evaluations (maximum absolute discrepancy $< 0.0001$).
2. **LTCUSDT Macro F1 Discrepancy Resolved:** The value **0.4264** was confirmed to belong strictly to `B3_RandomForest`, while **0.4253** belongs strictly to `B4_LightGBM`. Both values are verified accurate and reflect distinct baseline models.
3. **Aggregation Methodology Defined:** Catalog performance metrics were verified to represent the unweighted **arithmetic mean** across expanding walk-forward folds, with inter-fold dispersion captured by the **sample standard deviation**.

---

## 2. Aggregation Methodology & Rule Definitions

To prevent conflation between different mathematical summaries, four distinct aggregation metrics were audited:

1. **Arithmetic Mean across Folds (Master Catalog Standard):**
   $$\bar{M} = \frac{1}{K} \sum_{k=1}^K M_k$$
   where \(M_k\) is the metric evaluated on test fold \(k\). This is the primary benchmark metric reported in the catalog.
2. **Standard Deviation across Folds (Temporal Stability Index):**
   $$s = \sqrt{\frac{1}{K-1} \sum_{k=1}^K (M_k - \bar{M})^2}$$
   quantifies model variance across changing market regimes.
3. **Pooled Out-of-Fold Metrics (Concatenated Confusion Matrix):**
   $$C_{\text{pooled}} = \sum_{k=1}^K C_k$$
   evaluates global classification counts across the entire validation sequence simultaneously.
4. **Sample-Weighted Average:**
   $$\bar{M}_w = \frac{\sum_{k=1}^K N_k M_k}{\sum_{k=1}^K N_k}$$
   weights each fold by test sample count \(N_k\).

Because expanding walk-forward folds in QUANTUM have roughly equal test sizes (\(\approx 26,100\) samples each), the arithmetic mean and sample-weighted mean match to four decimal places.

---

## 3. LTCUSDT Macro F1 Discrepancy Resolution

### 3.1 Reported Inconsistency
- In the Phase 5.3.2 fleet summary table, a column labeled `B4 Macro F1` reported **0.4253** for LTCUSDT.
- In the comparative analysis narrative, LTCUSDT was referenced as achieving a top Macro F1 of **0.4264** under Random Forest.

### 3.2 Audit Findings
Inspection of the original fold evaluations in [summary.json](file:///d:/quantum-multi-agent/artifacts/phase_5_3_2/LTCUSDT/summary.json) and [metrics.json](file:///d:/quantum-multi-agent/artifacts/phase_5_3_2/LTCUSDT/fold_1/metrics.json) confirms:

| Model ID | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 | Arithmetic Mean | Discrepancy Cause |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **B3_RandomForest** | 0.5057 | 0.4447 | 0.4357 | 0.3340 | 0.4121 | **0.4264** | Highest Macro F1 across all models for LTC |
| **B4_LightGBM** | 0.4709 | 0.4578 | 0.4300 | 0.3376 | 0.4304 | **0.4253** | Second-highest Macro F1, highest ROC-AUC |

### 3.3 Resolution Verdict
There was **zero numerical corruption or data fabrication**.
- The value **0.4264** belongs to `B3_RandomForest`.
- The value **0.4253** belongs to `B4_LightGBM`.
- The apparent discrepancy was purely a column-labeling ambiguity: the summary table displayed B4's F1 score across all pairs, while the text highlighted LTC's overall top model (B3 Random Forest).
- `B3_RandomForest` remains the verified top baseline for `LTCUSDT` on Balanced Accuracy (0.4402 vs B4 0.4355) and Macro F1 (0.4264 vs B4 0.4253).

---

## 4. Master Fleet Metric Reconciliation Table

The table below compares reported vs recalculated arithmetic means for Balanced Accuracy, Macro F1, Brier Score, and OvR ROC-AUC across all 11 specialists:

| Symbol | Model | Reported BalAcc | Recalculated BalAcc | Reported F1 | Recalculated F1 | Reported Brier | Recalc Brier | Reported AUC | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **BTCUSDT** | B3_RandomForest | 0.4127 | 0.4127 | 0.3714 | 0.3714 | 0.5975 | 0.5975 | 0.5842 | **EXACT** |
| BTCUSDT | B4_LightGBM | 0.4099 | 0.4099 | 0.3893 | 0.3893 | 0.5795 | 0.5795 | 0.6050 | **EXACT** |
| **XMRUSDT** | B2_LogisticRegression | 0.4177 | 0.4177 | 0.3796 | 0.3796 | 0.6399 | 0.6399 | 0.5863 | **EXACT** |
| XMRUSDT | B4_LightGBM | 0.3816 | 0.3816 | 0.3729 | 0.3729 | 0.6362 | 0.6362 | 0.5546 | **EXACT** |
| **ADAUSDT** | B4_LightGBM | 0.4490 | 0.4490 | 0.3915 | 0.3915 | 0.6454 | 0.6454 | 0.6209 | **EXACT** |
| ADAUSDT | B3_RandomForest | 0.4278 | 0.4278 | 0.3738 | 0.3738 | 0.6461 | 0.6461 | 0.6036 | **EXACT** |
| **XRPUSDT** | B4_LightGBM | 0.3747 | 0.3747 | 0.3714 | 0.3714 | 0.5635 | 0.5635 | 0.6035 | **EXACT** |
| XRPUSDT | B2_LogisticRegression | 0.3709 | 0.3709 | 0.3583 | 0.3583 | 0.5802 | 0.5802 | 0.5657 | **EXACT** |
| **BNBUSDT** | B4_LightGBM | 0.3699 | 0.3699 | 0.3623 | 0.3623 | 0.5716 | 0.5716 | 0.5975 | **EXACT** |
| BNBUSDT | B3_RandomForest | 0.3642 | 0.3642 | 0.3511 | 0.3511 | 0.5785 | 0.5785 | 0.5783 | **EXACT** |
| **ETHUSDT** | B3_RandomForest | 0.4195 | 0.4195 | 0.3796 | 0.3796 | 0.5883 | 0.5883 | 0.5968 | **EXACT** |
| ETHUSDT | B4_LightGBM | 0.4177 | 0.4177 | 0.3975 | 0.3975 | 0.5750 | 0.5750 | 0.6144 | **EXACT** |
| **SOLUSDT** | B4_LightGBM | 0.3878 | 0.3878 | 0.3797 | 0.3797 | 0.5594 | 0.5594 | 0.6108 | **EXACT** |
| SOLUSDT | B3_RandomForest | 0.3808 | 0.3808 | 0.3671 | 0.3671 | 0.5687 | 0.5687 | 0.5942 | **EXACT** |
| **AVAXUSDT** | B4_LightGBM | 0.4145 | 0.4145 | 0.3966 | 0.3966 | 0.6246 | 0.6246 | 0.6057 | **EXACT** |
| AVAXUSDT | B3_RandomForest | 0.4104 | 0.4104 | 0.3876 | 0.3876 | 0.6291 | 0.6291 | 0.5967 | **EXACT** |
| **LINKUSDT** | B4_LightGBM | 0.4067 | 0.4067 | 0.3905 | 0.3905 | 0.5957 | 0.5957 | 0.6238 | **EXACT** |
| LINKUSDT | B3_RandomForest | 0.4022 | 0.4022 | 0.3830 | 0.3830 | 0.6005 | 0.6005 | 0.6071 | **EXACT** |
| **DOGEUSDT** | B4_LightGBM | 0.3960 | 0.3960 | 0.3904 | 0.3904 | 0.5749 | 0.5749 | 0.6099 | **EXACT** |
| DOGEUSDT | B3_RandomForest | 0.3870 | 0.3870 | 0.3762 | 0.3762 | 0.5775 | 0.5775 | 0.5996 | **EXACT** |
| **LTCUSDT** | B3_RandomForest | 0.4402 | 0.4402 | 0.4264 | 0.4264 | 0.6083 | 0.6083 | 0.6375 | **EXACT** |
| LTCUSDT | B4_LightGBM | 0.4355 | 0.4355 | 0.4253 | 0.4253 | 0.6088 | 0.6088 | 0.6399 | **EXACT** |

---

## 5. Predictive Lift Range Reconciliation

To resolve narrative discrepancies regarding performance spans, ranges were audited across two distinct analytical boundaries:

### 5.1 Model-Wide Performance Spans (All B2, B3, B4 Evaluations across Fleet)
- **Balanced Accuracy Span:** **0.3561** (BNBUSDT B2) to **0.4490** (ADAUSDT B4)
- **Macro F1 Span:** **0.3377** (BNBUSDT B2) to **0.4264** (LTCUSDT B3)
- **Multi-class ROC-AUC Span:** **0.5546** (XMRUSDT B4) to **0.6399** (LTCUSDT B4)
- **Multi-class Brier Score Span:** **0.5594** (SOLUSDT B4) to **0.6669** (ADAUSDT B2)

### 5.2 Best Baseline per Instrument Spans
- **Top Balanced Accuracy Span:** **0.3699** (BNBUSDT B4) to **0.4490** (ADAUSDT B4)
- **Top Macro F1 Span:** **0.3623** (BNBUSDT B4) to **0.4264** (LTCUSDT B3)

### 5.3 Naive Benchmark References
- **B0 Majority Class Balanced Accuracy:** Strictly **0.3333** across all 11 instruments
- **B0 Majority Class Macro F1:** **0.1766** (LINKUSDT) to **0.2142** (SOLUSDT)
- **B1 Prior Probability Balanced Accuracy:** Strictly **0.3333** across all 11 instruments
- **B1 Prior Probability Macro F1:** **0.1766** (LINKUSDT) to **0.2142** (SOLUSDT)

### Reconciliation Summary:
- Every ML baseline evaluation across all 11 instruments strictly exceeded the naive Balanced Accuracy benchmark of 0.3333.
- The minimum ML Balanced Accuracy was **0.3561** (BNB B2), representing an absolute floor lift of +0.0228 (+6.8% relative lift).
- The maximum ML Balanced Accuracy was **0.4490** (ADA B4), representing an absolute ceiling lift of +0.1157 (+34.7% relative lift).
