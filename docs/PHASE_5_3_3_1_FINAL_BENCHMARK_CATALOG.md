# QUANTUM PHASE 5.3.3.1: FINAL MASTER BENCHMARK CATALOG

**Document Type:** Definitive Research Baseline Benchmark Catalog  
**Phase:** Phase 5.3.3.1 (Final Benchmark Correction and Governance Closure)  
**System:** QUANTUM 11-Specialist Cryptocurrency Perpetual Futures ML Trading Research System  
**Repository:** https://github.com/RAYDENFLY/quantum-multi-agent  
**Artifact Sources:**  
- [`artifacts/phase_5_3_3_1/final_benchmark_catalog.json`](file:///d:/quantum-multi-agent/artifacts/phase_5_3_3_1/final_benchmark_catalog.json)  
- [`artifacts/phase_5_3_3_1/final_winner_catalog.json`](file:///d:/quantum-multi-agent/artifacts/phase_5_3_3_1/final_winner_catalog.json)  
- [`artifacts/phase_5_3_3_1/bootstrap_sensitivity.json`](file:///d:/quantum-multi-agent/artifacts/phase_5_3_3_1/bootstrap_sensitivity.json)  
- [`artifacts/phase_5_3_3_1/holm_adjusted_pvalues.json`](file:///d:/quantum-multi-agent/artifacts/phase_5_3_3_1/holm_adjusted_pvalues.json)  
**Execution Timestamp:** 2026-11-01  
**Status:** COMPLETE, AUDITED, AND RATIFIED  

---

## 1. EXECUTIVE OVERVIEW

This document establishes the definitive, immutable master benchmark catalog for the QUANTUM 11-Specialist Machine Learning Trading Research System. It supersedes and replaces all preliminary, pilot, and draft performance tables published across Phase 5.3.1, Phase 5.3.2, and Phase 5.3.3.

All performance metrics presented herein represent the unweighted arithmetic mean across expanding-window walk-forward validation folds, evaluated strictly on out-of-fold validation periods under the approved research governance contracts:
1. **Target:** 3-class Triple-Barrier Labels (+1 Long, 0 Neutral, -1 Short) with horizontal barrier multiplier 1.5x and 12-bar (60-minute) maximum holding horizon.
2. **Temporal Validation:** Expanding-window walk-forward validation with 12-bar training purge and 12-bar test horizon protection.
3. **Data Isolation:** Prospective Holdout (`2026-11-01` to `2027-04-30`) remains strictly unread, untouched, and unindexed.
4. **Reproducibility:** Seed 42 across all pipelines, deterministic feature schemas, and verified bit-exact execution.

---

## 2. FLEET-WIDE SUMMARY TABLES

### 2.1 Fleet Mean Performance by Model Architecture (11 Instruments)

| Baseline Model | Fleet Mean Balanced Acc | Fleet Mean Macro F1 | Fleet Mean Brier Score | Fleet Mean ROC AUC OvR |
| :--- | :---: | :---: | :---: | :---: |
| **B0 Majority Class** | 0.3333 | 0.2008 | 1.1332 | 0.5000 |
| **B1 Empirical Prior** | 0.3333 | 0.2008 | 0.6052 | 0.5000 |
| **B2 Logistic Regression** | 0.3939 | 0.3707 | 0.6092 | 0.5834 |
| **B3 Random Forest** | 0.4001 | 0.3760 | 0.6005 | 0.5951 |
| **B4 LightGBM** | **0.4040** | **0.3879** | **0.5941** | **0.6078** |

### 2.2 Model Win Counts Across 11 Specialist Instruments

| Performance Dimension | B4 LightGBM | B3 Random Forest | B2 Logistic Regression | B1 Empirical Prior | B0 Majority |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Balanced Accuracy Winner** | **7** | 3 | 1 | 0 | 0 |
| **Macro F1 Winner** | **9** | 1 | 1 | 0 | 0 |
| **ROC AUC OvR Winner** | **10** | 0 | 1 | 0 | 0 |
| **LOWEST_BRIER_ALL_BASELINES** | 5 | 1 | 0 | **5** | 0 |
| **LOWEST_BRIER_ML_MODELS** | **10** | 1 | 0 | N/A | N/A |
| **Most Stable ML Model (Lowest BA Std)** | 2 | 2 | **7** | N/A | N/A |

### 2.3 Master Winner Catalog Across All 11 Specialists

| Instrument | Balanced Accuracy Winner | Macro F1 Winner | ROC AUC Winner | Lowest Brier (All Baselines) | Lowest Brier (ML Models Only) | Most Stable ML Model |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BTCUSDT** | B3 RandomForest (0.4126) | B4 LightGBM (0.3893) | B4 LightGBM (0.6050) | B1 Prior (0.5549) | B4 LightGBM (0.5795) | B2 LogisticReg (std 0.0222) |
| **ETHUSDT** | B3 RandomForest (0.4195) | B4 LightGBM (0.3975) | B4 LightGBM (0.6144) | B1 Prior (0.5598) | B4 LightGBM (0.5750) | B4 LightGBM (std 0.0120) |
| **BNBUSDT** | B4 LightGBM (0.3699) | B4 LightGBM (0.3623) | B4 LightGBM (0.5975) | B4 LightGBM (0.5716) | B4 LightGBM (0.5716) | B2 LogisticReg (std 0.0176) |
| **XRPUSDT** | B4 LightGBM (0.3748) | B4 LightGBM (0.3714) | B4 LightGBM (0.6035) | B4 LightGBM (0.5635) | B4 LightGBM (0.5635) | B3 RandomForest (std 0.0221) |
| **ADAUSDT** | B4 LightGBM (0.4490) | B4 LightGBM (0.3915) | B4 LightGBM (0.6209) | B1 Prior (0.6158) | B4 LightGBM (0.6454) | B2 LogisticReg (std 0.0300) |
| **SOLUSDT** | B4 LightGBM (0.3878) | B4 LightGBM (0.3797) | B4 LightGBM (0.6108) | B1 Prior (0.5546) | B4 LightGBM (0.5594) | B2 LogisticReg (std 0.0298) |
| **AVAXUSDT** | B4 LightGBM (0.4145) | B4 LightGBM (0.3966) | B4 LightGBM (0.6057) | B4 LightGBM (0.6246) | B4 LightGBM (0.6246) | B4 LightGBM (std 0.0431) |
| **LINKUSDT** | B4 LightGBM (0.4068) | B4 LightGBM (0.3905) | B4 LightGBM (0.6238) | B4 LightGBM (0.5957) | B4 LightGBM (0.5957) | B2 LogisticReg (std 0.0429) |
| **DOGEUSDT** | B4 LightGBM (0.3960) | B4 LightGBM (0.3904) | B4 LightGBM (0.6099) | B4 LightGBM (0.5749) | B4 LightGBM (0.5749) | B3 RandomForest (std 0.0287) |
| **LTCUSDT** | B3 RandomForest (0.4401) | B3 RandomForest (0.4264) | B4 LightGBM (0.6399) | B3 RandomForest (0.6083) | B3 RandomForest (0.6083) | B2 LogisticReg (std 0.0486) |
| **XMRUSDT** | B2 LogisticReg (0.4177) | B2 LogisticReg (0.3796) | B2 LogisticReg (0.5863) | B1 Prior (0.6010) | B4 LightGBM (0.6362) | B2 LogisticReg (std 0.0187) |

---

## 3. INDIVIDUAL SPECIALIST BENCHMARK PROFILES

### 3.1 BTCUSDT Specialist Profile
- **Clean Sample Count:** 261,085 (5m candles)
- **Valid Walk-Forward Folds:** 5
- **Data Sufficiency Status:** SUFFICIENT
- **Originating Campaign:** Phase 5.3.1 Pilot

#### Baseline Performance Table (Mean across 5 folds +/- inter-fold std):
| Baseline Model | Balanced Accuracy | Macro F1 | Brier Score | ROC AUC OvR |
| :--- | :---: | :---: | :---: | :---: |
| B0 Majority Class | 0.3333 (+/-0.0000) | 0.2134 (+/-0.0051) | 1.0582 (+/-0.0329) | 0.5000 (+/-0.0000) |
| B1 Empirical Prior | 0.3333 (+/-0.0000) | 0.2134 (+/-0.0051) | 0.5549 (+/-0.0203) | 0.5000 (+/-0.0000) |
| B2 Logistic Regression | 0.3919 (+/-0.0222) | 0.3843 (+/-0.0281) | 0.5900 (+/-0.0505) | 0.5978 (+/-0.0113) |
| B3 Random Forest | **0.4126 (+/-0.0251)** | 0.3714 (+/-0.0178) | 0.5975 (+/-0.0259) | 0.5842 (+/-0.0104) |
| B4 LightGBM | 0.4099 (+/-0.0270) | **0.3893 (+/-0.0199)** | 0.5795 (+/-0.0398) | **0.6050 (+/-0.0098)** |

- **Metric Winners:**
  - Balanced Accuracy: B3 Random Forest (0.4126, lift +0.0793 over B0)
  - Macro F1: B4 LightGBM (0.3893)
  - ROC AUC: B4 LightGBM (0.6050)
  - LOWEST_BRIER_ALL_BASELINES: B1 Empirical Prior (0.5549)
  - LOWEST_BRIER_ML_MODELS: B4 LightGBM (0.5795)
  - Most Stable ML Model: B2 Logistic Regression (std 0.0222)
- **Statistical Significance vs B0:**
  - B3 Lift: +0.0793, 95% CI: [+0.0558, +0.0987], Raw p: 0.000999, Holm-adjusted p: 0.032967 (SIGNIFICANT)
  - B4 Lift: +0.0766, 95% CI: [+0.0527, +0.1013], Raw p: 0.000999, Holm-adjusted p: 0.032967 (SIGNIFICANT)
  - B2 Lift: +0.0586, 95% CI: [+0.0403, +0.0776], Raw p: 0.000999, Holm-adjusted p: 0.032967 (SIGNIFICANT)
- **Bootstrap Sensitivity Profile:** ROBUST across all block lengths $b \in \{12, 24, 48, 96\}$.

---

### 3.2 ETHUSDT Specialist Profile
- **Clean Sample Count:** 261,085
- **Valid Walk-Forward Folds:** 5
- **Data Sufficiency Status:** SUFFICIENT
- **Originating Campaign:** Phase 5.3.2 Fleet

#### Baseline Performance Table:
| Baseline Model | Balanced Accuracy | Macro F1 | Brier Score | ROC AUC OvR |
| :--- | :---: | :---: | :---: | :---: |
| B0 Majority Class | 0.3333 (+/-0.0000) | 0.2116 (+/-0.0061) | 1.0694 (+/-0.0389) | 0.5000 (+/-0.0000) |
| B1 Empirical Prior | 0.3333 (+/-0.0000) | 0.2116 (+/-0.0061) | 0.5598 (+/-0.0273) | 0.5000 (+/-0.0000) |
| B2 Logistic Regression | 0.3875 (+/-0.0191) | 0.3798 (+/-0.0245) | 0.5838 (+/-0.0613) | 0.5971 (+/-0.0090) |
| B3 Random Forest | **0.4195 (+/-0.0165)** | 0.3796 (+/-0.0176) | 0.5883 (+/-0.0365) | 0.5968 (+/-0.0079) |
| B4 LightGBM | 0.4177 (+/-0.0120)** | **0.3975 (+/-0.0202)** | 0.5750 (+/-0.0483) | **0.6144 (+/-0.0065)** |

- **Metric Winners:**
  - Balanced Accuracy: B3 Random Forest (0.4195, lift +0.0862 over B0)
  - Macro F1: B4 LightGBM (0.3975)
  - ROC AUC: B4 LightGBM (0.6144)
  - LOWEST_BRIER_ALL_BASELINES: B1 Empirical Prior (0.5598)
  - LOWEST_BRIER_ML_MODELS: B4 LightGBM (0.5750)
  - Most Stable ML Model: B4 LightGBM (std 0.0120)
- **Statistical Significance vs B0:**
  - B3 Lift: +0.0862, 95% CI: [+0.0712, +0.1003], Raw p: 0.000999, Holm-adj p: 0.032967 (SIGNIFICANT)
  - B4 Lift: +0.0844, 95% CI: [+0.0746, +0.0941], Raw p: 0.000999, Holm-adj p: 0.032967 (SIGNIFICANT)
  - B2 Lift: +0.0542, 95% CI: [+0.0382, +0.0723], Raw p: 0.000999, Holm-adj p: 0.032967 (SIGNIFICANT)
- **Bootstrap Sensitivity Profile:** ROBUST across all block lengths $b \in \{12, 24, 48, 96\}$.

---

### 3.3 BNBUSDT Specialist Profile
- **Clean Sample Count:** 261,085
- **Valid Walk-Forward Folds:** 5
- **Data Sufficiency Status:** SUFFICIENT
- **Originating Campaign:** Phase 5.3.2 Fleet

#### Baseline Performance Table:
| Baseline Model | Balanced Accuracy | Macro F1 | Brier Score | ROC AUC OvR |
| :--- | :---: | :---: | :---: | :---: |
| B0 Majority Class | 0.3333 (+/-0.0000) | 0.2071 (+/-0.0164) | 1.0955 (+/-0.0985) | 0.5000 (+/-0.0000) |
| B1 Empirical Prior | 0.3333 (+/-0.0000) | 0.2071 (+/-0.0164) | 0.5910 (+/-0.0452) | 0.5000 (+/-0.0000) |
| B2 Logistic Regression | 0.3561 (+/-0.0176) | 0.3377 (+/-0.0091) | 0.5836 (+/-0.0500) | 0.5571 (+/-0.0128) |
| B3 Random Forest | 0.3642 (+/-0.0245) | 0.3511 (+/-0.0118) | 0.5785 (+/-0.0418) | 0.5783 (+/-0.0187) |
| B4 LightGBM | **0.3699 (+/-0.0247)** | **0.3623 (+/-0.0157)** | **0.5716 (+/-0.0467)** | **0.5975 (+/-0.0189)** |

- **Metric Winners:**
  - Balanced Accuracy: B4 LightGBM (0.3699, lift +0.0366 over B0)
  - Macro F1: B4 LightGBM (0.3623)
  - ROC AUC: B4 LightGBM (0.5975)
  - LOWEST_BRIER_ALL_BASELINES: B4 LightGBM (0.5716)
  - LOWEST_BRIER_ML_MODELS: B4 LightGBM (0.5716)
  - Most Stable ML Model: B2 Logistic Regression (std 0.0176)
- **Statistical Significance vs B0:**
  - B4 Lift: +0.0366, 95% CI: [+0.0138, +0.0586], Raw p: 0.001998, Holm-adj p: 0.032967 (SIGNIFICANT)
  - B3 Lift: +0.0309, 95% CI: [+0.0095, +0.0516], Raw p: 0.005994, Holm-adj p: 0.032967 (SIGNIFICANT)
  - B2 Lift: +0.0228, 95% CI: [+0.0077, +0.0391], Raw p: 0.001998, Holm-adj p: 0.032967 (SIGNIFICANT)
- **Bootstrap Sensitivity Profile:** SENSITIVE_TO_BLOCK_LENGTH (95% CI approaches zero at $b = 96$ bars).

---

### 3.4 XRPUSDT Specialist Profile
- **Clean Sample Count:** 261,085
- **Valid Walk-Forward Folds:** 5
- **Data Sufficiency Status:** SUFFICIENT
- **Originating Campaign:** Phase 5.3.2 Fleet

#### Baseline Performance Table:
| Baseline Model | Balanced Accuracy | Macro F1 | Brier Score | ROC AUC OvR |
| :--- | :---: | :---: | :---: | :---: |
| B0 Majority Class | 0.3333 (+/-0.0000) | 0.2096 (+/-0.0117) | 1.0807 (+/-0.0729) | 0.5000 (+/-0.0000) |
| B1 Empirical Prior | 0.3333 (+/-0.0000) | 0.2096 (+/-0.0117) | 0.5855 (+/-0.0317) | 0.5000 (+/-0.0000) |
| B2 Logistic Regression | 0.3709 (+/-0.0257) | 0.3583 (+/-0.0136) | 0.5802 (+/-0.0499) | 0.5657 (+/-0.0136) |
| B3 Random Forest | 0.3659 (+/-0.0221) | 0.3522 (+/-0.0265) | 0.5723 (+/-0.0406) | 0.5853 (+/-0.0076) |
| B4 LightGBM | **0.3748 (+/-0.0290)** | **0.3714 (+/-0.0259)** | **0.5635 (+/-0.0418)** | **0.6035 (+/-0.0066)** |

- **Metric Winners:**
  - Balanced Accuracy: B4 LightGBM (0.3748, lift +0.0415 over B0)
  - Macro F1: B4 LightGBM (0.3714)
  - ROC AUC: B4 LightGBM (0.6035)
  - LOWEST_BRIER_ALL_BASELINES: B4 LightGBM (0.5635)
  - LOWEST_BRIER_ML_MODELS: B4 LightGBM (0.5635)
  - Most Stable ML Model: B3 Random Forest (std 0.0221)
- **Statistical Significance vs B0:**
  - B4 Lift: +0.0415, 95% CI: [+0.0174, +0.0644], Raw p: 0.000999, Holm-adj p: 0.032967 (SIGNIFICANT)
  - B2 Lift: +0.0376, 95% CI: [+0.0155, +0.0606], Raw p: 0.000999, Holm-adj p: 0.032967 (SIGNIFICANT)
  - B3 Lift: +0.0326, 95% CI: [+0.0131, +0.0520], Raw p: 0.000999, Holm-adj p: 0.032967 (SIGNIFICANT)
- **Bootstrap Sensitivity Profile:** SENSITIVE_TO_BLOCK_LENGTH (95% CI approaches zero at $b = 96$ bars).

---

### 3.5 ADAUSDT Specialist Profile
- **Clean Sample Count:** 261,085
- **Valid Walk-Forward Folds:** 5
- **Data Sufficiency Status:** SUFFICIENT
- **Originating Campaign:** Phase 5.3.2 Fleet

#### Baseline Performance Table:
| Baseline Model | Balanced Accuracy | Macro F1 | Brier Score | ROC AUC OvR |
| :--- | :---: | :---: | :---: | :---: |
| B0 Majority Class | 0.3333 (+/-0.0000) | 0.1964 (+/-0.0055) | 1.1642 (+/-0.0332) | 0.5000 (+/-0.0000) |
| B1 Empirical Prior | 0.3333 (+/-0.0000) | 0.1964 (+/-0.0055) | 0.6158 (+/-0.0288) | 0.5000 (+/-0.0000) |
| B2 Logistic Regression | 0.4234 (+/-0.0300) | 0.3586 (+/-0.0515) | 0.6669 (+/-0.0310) | 0.5964 (+/-0.0304) |
| B3 Random Forest | 0.4278 (+/-0.0481) | 0.3738 (+/-0.0484) | 0.6461 (+/-0.0264) | 0.6036 (+/-0.0430) |
| B4 LightGBM | **0.4490 (+/-0.0376)** | **0.3915 (+/-0.0468)** | 0.6454 (+/-0.0352) | **0.6209 (+/-0.0335)** |

- **Metric Winners:**
  - Balanced Accuracy: B4 LightGBM (0.4490, lift +0.1157 over B0)
  - Macro F1: B4 LightGBM (0.3915)
  - ROC AUC: B4 LightGBM (0.6209)
  - LOWEST_BRIER_ALL_BASELINES: B1 Empirical Prior (0.6158)
  - LOWEST_BRIER_ML_MODELS: B4 LightGBM (0.6454)
  - Most Stable ML Model: B2 Logistic Regression (std 0.0300)
- **Statistical Significance vs B0:**
  - B4 Lift: +0.1157, 95% CI: [+0.0820, +0.1503], Raw p: 0.000999, Holm-adj p: 0.032967 (SIGNIFICANT)
  - B3 Lift: +0.0945, 95% CI: [+0.0521, +0.1339], Raw p: 0.000999, Holm-adj p: 0.032967 (SIGNIFICANT)
  - B2 Lift: +0.0901, 95% CI: [+0.0652, +0.1129], Raw p: 0.000999, Holm-adj p: 0.032967 (SIGNIFICANT)
- **Bootstrap Sensitivity Profile:** ROBUST across all block lengths $b \in \{12, 24, 48, 96\}$.

---

### 3.6 SOLUSDT Specialist Profile
- **Clean Sample Count:** 261,085
- **Valid Walk-Forward Folds:** 5
- **Data Sufficiency Status:** SUFFICIENT
- **Originating Campaign:** Phase 5.3.2 Fleet

#### Baseline Performance Table:
| Baseline Model | Balanced Accuracy | Macro F1 | Brier Score | ROC AUC OvR |
| :--- | :---: | :---: | :---: | :---: |
| B0 Majority Class | 0.3333 (+/-0.0000) | 0.2142 (+/-0.0062) | 1.0529 (+/-0.0395) | 0.5000 (+/-0.0000) |
| B1 Empirical Prior | 0.3333 (+/-0.0000) | 0.2142 (+/-0.0062) | 0.5546 (+/-0.0275) | 0.5000 (+/-0.0000) |
| B2 Logistic Regression | 0.3735 (+/-0.0298) | 0.3658 (+/-0.0157) | 0.5741 (+/-0.0503) | 0.5813 (+/-0.0160) |
| B3 Random Forest | 0.3808 (+/-0.0310) | 0.3671 (+/-0.0173) | 0.5687 (+/-0.0370) | 0.5942 (+/-0.0096) |
| B4 LightGBM | **0.3878 (+/-0.0333)** | **0.3797 (+/-0.0216)** | 0.5594 (+/-0.0417) | **0.6108 (+/-0.0090)** |

- **Metric Winners:**
  - Balanced Accuracy: B4 LightGBM (0.3878, lift +0.0545 over B0)
  - Macro F1: B4 LightGBM (0.3797)
  - ROC AUC: B4 LightGBM (0.6108)
  - LOWEST_BRIER_ALL_BASELINES: B1 Empirical Prior (0.5546)
  - LOWEST_BRIER_ML_MODELS: B4 LightGBM (0.5594)
  - Most Stable ML Model: B2 Logistic Regression (std 0.0298)
- **Statistical Significance vs B0:**
  - B4 Lift: +0.0545, 95% CI: [+0.0239, +0.0834], Raw p: 0.000999, Holm-adj p: 0.032967 (SIGNIFICANT)
  - B3 Lift: +0.0475, 95% CI: [+0.0210, +0.0779], Raw p: 0.001998, Holm-adj p: 0.032967 (SIGNIFICANT)
  - B2 Lift: +0.0402, 95% CI: [+0.0136, +0.0693], Raw p: 0.001998, Holm-adj p: 0.032967 (SIGNIFICANT)
- **Bootstrap Sensitivity Profile:** SENSITIVE_TO_BLOCK_LENGTH.

---

### 3.7 AVAXUSDT Specialist Profile
- **Clean Sample Count:** 261,085
- **Valid Walk-Forward Folds:** 5
- **Data Sufficiency Status:** SUFFICIENT
- **Originating Campaign:** Phase 5.3.2 Fleet

#### Baseline Performance Table:
| Baseline Model | Balanced Accuracy | Macro F1 | Brier Score | ROC AUC OvR |
| :--- | :---: | :---: | :---: | :---: |
| B0 Majority Class | 0.3333 (+/-0.0000) | 0.1878 (+/-0.0155) | 1.2125 (+/-0.0893) | 0.5000 (+/-0.0000) |
| B1 Empirical Prior | 0.3333 (+/-0.0000) | 0.1878 (+/-0.0155) | 0.6516 (+/-0.0157) | 0.5000 (+/-0.0000) |
| B2 Logistic Regression | 0.4084 (+/-0.0451) | 0.3693 (+/-0.0528) | 0.6413 (+/-0.0199) | 0.5821 (+/-0.0422) |
| B3 Random Forest | 0.4104 (+/-0.0481) | 0.3876 (+/-0.0466) | 0.6291 (+/-0.0181) | 0.5967 (+/-0.0411) |
| B4 LightGBM | **0.4145 (+/-0.0431)** | **0.3966 (+/-0.0417)** | **0.6246 (+/-0.0213)** | **0.6057 (+/-0.0379)** |

- **Metric Winners:**
  - Balanced Accuracy: B4 LightGBM (0.4145, lift +0.0812 over B0)
  - Macro F1: B4 LightGBM (0.3966)
  - ROC AUC: B4 LightGBM (0.6057)
  - LOWEST_BRIER_ALL_BASELINES: B4 LightGBM (0.6246)
  - LOWEST_BRIER_ML_MODELS: B4 LightGBM (0.6246)
  - Most Stable ML Model: B4 LightGBM (std 0.0431)
- **Statistical Significance vs B0:**
  - B4 Lift: +0.0812, 95% CI: [+0.0465, +0.1214], Raw p: 0.000999, Holm-adj p: 0.032967 (SIGNIFICANT)
  - B3 Lift: +0.0771, 95% CI: [+0.0337, +0.1166], Raw p: 0.000999, Holm-adj p: 0.032967 (SIGNIFICANT)
  - B2 Lift: +0.0751, 95% CI: [+0.0332, +0.1164], Raw p: 0.000999, Holm-adj p: 0.032967 (SIGNIFICANT)
- **Bootstrap Sensitivity Profile:** SENSITIVE_TO_BLOCK_LENGTH.

---

### 3.8 LINKUSDT Specialist Profile
- **Clean Sample Count:** 261,085
- **Valid Walk-Forward Folds:** 5
- **Data Sufficiency Status:** SUFFICIENT
- **Originating Campaign:** Phase 5.3.2 Fleet

#### Baseline Performance Table:
| Baseline Model | Balanced Accuracy | Macro F1 | Brier Score | ROC AUC OvR |
| :--- | :---: | :---: | :---: | :---: |
| B0 Majority Class | 0.3333 (+/-0.0000) | 0.1766 (+/-0.0318) | 1.2680 (+/-0.1736) | 0.5000 (+/-0.0000) |
| B1 Empirical Prior | 0.3333 (+/-0.0000) | 0.1766 (+/-0.0318) | 0.6746 (+/-0.0583) | 0.5000 (+/-0.0000) |
| B2 Logistic Regression | 0.3984 (+/-0.0429) | 0.3714 (+/-0.0320) | 0.6239 (+/-0.0204) | 0.5708 (+/-0.0391) |
| B3 Random Forest | 0.4022 (+/-0.0453) | 0.3829 (+/-0.0387) | 0.6005 (+/-0.0194) | 0.6071 (+/-0.0496) |
| B4 LightGBM | **0.4068 (+/-0.0468)** | **0.3905 (+/-0.0406)** | **0.5957 (+/-0.0240)** | **0.6238 (+/-0.0363)** |

- **Metric Winners:**
  - Balanced Accuracy: B4 LightGBM (0.4068, lift +0.0735 over B0)
  - Macro F1: B4 LightGBM (0.3905)
  - ROC AUC: B4 LightGBM (0.6238)
  - LOWEST_BRIER_ALL_BASELINES: B4 LightGBM (0.5957)
  - LOWEST_BRIER_ML_MODELS: B4 LightGBM (0.5957)
  - Most Stable ML Model: B2 Logistic Regression (std 0.0429)
- **Statistical Significance vs B0:**
  - B4 Lift: +0.0735, 95% CI: [+0.0353, +0.1127], Raw p: 0.000999, Holm-adj p: 0.032967 (SIGNIFICANT)
  - B3 Lift: +0.0689, 95% CI: [+0.0303, +0.1093], Raw p: 0.001998, Holm-adj p: 0.032967 (SIGNIFICANT)
  - B2 Lift: +0.0651, 95% CI: [+0.0258, +0.1031], Raw p: 0.000999, Holm-adj p: 0.032967 (SIGNIFICANT)
- **Bootstrap Sensitivity Profile:** SENSITIVE_TO_BLOCK_LENGTH.

---

### 3.9 DOGEUSDT Specialist Profile
- **Clean Sample Count:** 261,085
- **Valid Walk-Forward Folds:** 5
- **Data Sufficiency Status:** SUFFICIENT
- **Originating Campaign:** Phase 5.3.2 Fleet

#### Baseline Performance Table:
| Baseline Model | Balanced Accuracy | Macro F1 | Brier Score | ROC AUC OvR |
| :--- | :---: | :---: | :---: | :---: |
| B0 Majority Class | 0.3333 (+/-0.0000) | 0.2017 (+/-0.0236) | 1.1257 (+/-0.1367) | 0.5000 (+/-0.0000) |
| B1 Empirical Prior | 0.3333 (+/-0.0000) | 0.2017 (+/-0.0236) | 0.6057 (+/-0.0681) | 0.5000 (+/-0.0000) |
| B2 Logistic Regression | 0.3838 (+/-0.0402) | 0.3723 (+/-0.0330) | 0.5887 (+/-0.0511) | 0.5752 (+/-0.0247) |
| B3 Random Forest | 0.3870 (+/-0.0287) | 0.3761 (+/-0.0271) | 0.5775 (+/-0.0404) | 0.5996 (+/-0.0165) |
| B4 LightGBM | **0.3960 (+/-0.0345)** | **0.3904 (+/-0.0317)** | **0.5749 (+/-0.0474)** | **0.6099 (+/-0.0197)** |

- **Metric Winners:**
  - Balanced Accuracy: B4 LightGBM (0.3960, lift +0.0627 over B0)
  - Macro F1: B4 LightGBM (0.3904)
  - ROC AUC: B4 LightGBM (0.6099)
  - LOWEST_BRIER_ALL_BASELINES: B4 LightGBM (0.5749)
  - LOWEST_BRIER_ML_MODELS: B4 LightGBM (0.5749)
  - Most Stable ML Model: B3 Random Forest (std 0.0287)
- **Statistical Significance vs B0:**
  - B4 Lift: +0.0627, 95% CI: [+0.0329, +0.0934], Raw p: 0.000999, Holm-adj p: 0.032967 (SIGNIFICANT)
  - B3 Lift: +0.0537, 95% CI: [+0.0303, +0.0784], Raw p: 0.000999, Holm-adj p: 0.032967 (SIGNIFICANT)
  - B2 Lift: +0.0505, 95% CI: [+0.0172, +0.0871], Raw p: 0.003996, Holm-adj p: 0.032967 (SIGNIFICANT)
- **Bootstrap Sensitivity Profile:** SENSITIVE_TO_BLOCK_LENGTH.

---

### 3.10 LTCUSDT Specialist Profile
- **Clean Sample Count:** 261,085
- **Valid Walk-Forward Folds:** 5
- **Data Sufficiency Status:** SUFFICIENT
- **Originating Campaign:** Phase 5.3.2 Fleet

#### Baseline Performance Table:
| Baseline Model | Balanced Accuracy | Macro F1 | Brier Score | ROC AUC OvR |
| :--- | :---: | :---: | :---: | :---: |
| B0 Majority Class | 0.3333 (+/-0.0000) | 0.1818 (+/-0.0166) | 1.2471 (+/-0.0956) | 0.5000 (+/-0.0000) |
| B1 Empirical Prior | 0.3333 (+/-0.0000) | 0.1818 (+/-0.0166) | 0.6622 (+/-0.0323) | 0.5000 (+/-0.0000) |
| B2 Logistic Regression | 0.4208 (+/-0.0486) | 0.4001 (+/-0.0594) | 0.6292 (+/-0.0223) | 0.6075 (+/-0.0511) |
| B3 Random Forest | **0.4401 (+/-0.0674)** | **0.4264 (+/-0.0639)** | **0.6083 (+/-0.0272)** | 0.6375 (+/-0.0673) |
| B4 LightGBM | 0.4355 (+/-0.0513) | 0.4253 (+/-0.0515) | 0.6088 (+/-0.0299) | **0.6399 (+/-0.0475)** |

- **Metric Winners:**
  - Balanced Accuracy: B3 Random Forest (0.4401, lift +0.1068 over B0)
  - Macro F1: B3 Random Forest (0.4264)
  - ROC AUC: B4 LightGBM (0.6399)
  - LOWEST_BRIER_ALL_BASELINES: B3 Random Forest (0.6083)
  - LOWEST_BRIER_ML_MODELS: B3 Random Forest (0.6083)
  - Most Stable ML Model: B2 Logistic Regression (std 0.0486)
- **Statistical Significance vs B0:**
  - B3 Lift: +0.1068, 95% CI: [+0.0471, +0.1683], Raw p: 0.000999, Holm-adj p: 0.032967 (SIGNIFICANT)
  - B4 Lift: +0.1022, 95% CI: [+0.0589, +0.1459], Raw p: 0.000999, Holm-adj p: 0.032967 (SIGNIFICANT)
  - B2 Lift: +0.0875, 95% CI: [+0.0445, +0.1303], Raw p: 0.000999, Holm-adj p: 0.032967 (SIGNIFICANT)
- **Bootstrap Sensitivity Profile:** SENSITIVE_TO_BLOCK_LENGTH.

---

### 3.11 XMRUSDT Specialist Profile
- **Clean Sample Count:** 30,623 (sample-constrained due to exchange listing window)
- **Valid Walk-Forward Folds:** 5 (definitively verified across fold_1 to fold_5 on disk)
- **Data Sufficiency Status:** SAMPLE_CONSTRAINED
- **Originating Campaign:** Phase 5.3.1 Pilot

#### Baseline Performance Table:
| Baseline Model | Balanced Accuracy | Macro F1 | Brier Score | ROC AUC OvR |
| :--- | :---: | :---: | :---: | :---: |
| B0 Majority Class | 0.3333 (+/-0.0000) | 0.2083 (+/-0.0051) | 1.0908 (+/-0.0319) | 0.5000 (+/-0.0000) |
| B1 Empirical Prior | 0.3333 (+/-0.0000) | 0.2083 (+/-0.0051) | 0.6010 (+/-0.0196) | 0.5000 (+/-0.0000) |
| B2 Logistic Regression | **0.4177 (+/-0.0187)** | **0.3796 (+/-0.0086)** | 0.6399 (+/-0.0152) | **0.5863 (+/-0.0121)** |
| B3 Random Forest | 0.3902 (+/-0.0273) | 0.3681 (+/-0.0182) | 0.6382 (+/-0.0098) | 0.5628 (+/-0.0129) |
| B4 LightGBM | 0.3816 (+/-0.0189) | 0.3729 (+/-0.0172) | 0.6362 (+/-0.0194) | 0.5546 (+/-0.0096) |

- **Metric Winners:**
  - Balanced Accuracy: B2 Logistic Regression (0.4177, lift +0.0844 over B0)
  - Macro F1: B2 Logistic Regression (0.3796)
  - ROC AUC: B2 Logistic Regression (0.5863)
  - LOWEST_BRIER_ALL_BASELINES: B1 Empirical Prior (0.6010)
  - LOWEST_BRIER_ML_MODELS: B4 LightGBM (0.6362)
  - Most Stable ML Model: B2 Logistic Regression (std 0.0187)
- **Statistical Significance vs B0:**
  - B2 Lift: +0.0844, 95% CI: [+0.0682, +0.1005], Raw p: 0.000999, Holm-adj p: 0.032967 (SIGNIFICANT)
  - B3 Lift: +0.0569, 95% CI: [+0.0348, +0.0808], Raw p: 0.000999, Holm-adj p: 0.032967 (SIGNIFICANT)
  - B4 Lift: +0.0483, 95% CI: [+0.0307, +0.0643], Raw p: 0.000999, Holm-adj p: 0.032967 (SIGNIFICANT)
- **Bootstrap Sensitivity Profile:** ROBUST across all block lengths $b \in \{12, 24, 48, 96\}$.

---

## 4. DUAL BRIER SCORE WINNER CATALOG RECONCILIATION

In prior phases, reporting an unconditional "Brier Score Winner" created confusion because unconditional static class probabilities ($B_1$ Prior) achieve lower quadratic loss than conditional probability forecasts ($B_4$ LightGBM) on high-noise assets. In this master catalog, the two dimensions are permanently separated:

| Specialist Instrument | LOWEST_BRIER_ALL_BASELINES | LOWEST_BRIER_ML_MODELS | Architectural Cause for Discrepancy |
| :--- | :--- | :--- | :--- |
| **BTCUSDT** | B1 Prior (0.5549) | B4 LightGBM (0.5795) | Static priors hedge against extreme market noise bars |
| **ETHUSDT** | B1 Prior (0.5598) | B4 LightGBM (0.5750) | High label noise penalizes confident conditional predictions |
| **BNBUSDT** | B4 LightGBM (0.5716) | B4 LightGBM (0.5716) | Conditional probabilities well-calibrated; beats static prior |
| **XRPUSDT** | B4 LightGBM (0.5635) | B4 LightGBM (0.5635) | B4 achieves better probability calibration than static prior |
| **ADAUSDT** | B1 Prior (0.6158) | B4 LightGBM (0.6454) | Sharp non-stationary regime shifts inflate B4 quadratic loss |
| **SOLUSDT** | B1 Prior (0.5546) | B4 LightGBM (0.5594) | Unconditional prior achieves near-optimal static Brier score |
| **AVAXUSDT** | B4 LightGBM (0.6246) | B4 LightGBM (0.6246) | B4 probabilities consistently outperform static priors |
| **LINKUSDT** | B4 LightGBM (0.5957) | B4 LightGBM (0.5957) | B4 conditional probabilities accurately separate class barriers |
| **DOGEUSDT** | B4 LightGBM (0.5749) | B4 LightGBM (0.5749) | B4 probabilities outperform static priors |
| **LTCUSDT** | B3 RandomForest (0.6083) | B3 RandomForest (0.6083) | B3 bagging smooths probabilities, beating B4 (0.6088) and B1 |
| **XMRUSDT** | B1 Prior (0.6010) | B4 LightGBM (0.6362) | Small sample size creates probability overconfidence in tree models |

---

## 5. COMPUTATIONAL RESOURCE FOOTPRINT SUMMARY

The fleet training and validation campaign was executed strictly within the mandated hardware budget (max 2 CPU threads, 1,024 MB RAM, 100 GB SSD storage):

- **Peak RSS Memory Recorded:** 815.4 MB (LTCUSDT training fold 5). Budget: 1,024.0 MB. Compliance: 100% PASS.
- **Total Fleet Wall-Clock Execution Time:** 52.6 minutes (3,153.7 seconds total computation across all 55 folds).
- **Fastest Instrument Execution:** XMRUSDT (34.42 seconds total across 5 folds).
- **Slowest Instrument Execution:** ADAUSDT (352.51 seconds total across 5 folds).
- **Disk Storage Footprint:** 57.42 MB total for all serialized model binaries, scalers, and metric manifests.

---

## 6. GOVERNANCE CERTIFICATION

This master catalog is certified as the single, internally consistent source of truth for the QUANTUM specialist baseline fleet. Any model candidate evaluated in Phase 5.4 or subsequent phases must benchmark against the figures documented in this catalog.
