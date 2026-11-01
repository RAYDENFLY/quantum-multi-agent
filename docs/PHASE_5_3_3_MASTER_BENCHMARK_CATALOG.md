# QUANTUM PHASE 5.3.3: RECONCILED MASTER BENCHMARK CATALOG

**Phase:** Phase 5.3.3  
**Date:** 2026-11-01  
**Lead Quantitative Systems Auditor:** QUANTUM Independent Quality & Systems Audit Lead  
**Scope:** Definitive reconciled master baseline catalog for all 11 QUANTUM specialist instruments  
**Source Manifest:** [master_benchmark_catalog.json](file:///d:/quantum-multi-agent/artifacts/phase_5_3_3/master_benchmark_catalog.json)

---

## 1. Executive Summary

This document establishes the official, reconciled master benchmark performance catalog for the QUANTUM 11-pair specialist architecture. All metrics reflect verified out-of-fold evaluations under causal expanding walk-forward cross-validation on Development and Validation Observed periods (`2023-11-01` to `2026-04-30`). The Prospective Holdout (`2026-11-01` to `2027-04-30`) remains strictly untouched and unopened.

All figures have been independently reconciled against fold-level confusion matrices, probability outputs, and physical resource logs.

---

## 2. Reconciled Master Baseline Table (11 Specialists)

The table below presents the verified arithmetic mean and fold standard deviation across all 5 baselines:
- **B0:** Majority Class
- **B1:** Prior Probability
- **B2:** Logistic Regression (L2)
- **B3:** Balanced Random Forest
- **B4:** LightGBM (GBDT)

| Symbol | Origin Phase | Clean Samples | Folds | B0 BalAcc | B1 BalAcc | B2 BalAcc (mean +/- std) | B3 BalAcc (mean +/- std) | B4 BalAcc (mean +/- std) | B4 Macro F1 | B4 ROC-AUC | B4 Brier | Peak RSS | Best BalAcc Baseline |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **BTCUSDT** | Phase 5.3.1 Pilot | 261,488 | 5 | 0.3333 | 0.3333 | 0.3919 +/- 0.0222 | **0.4127 +/- 0.0251** | 0.4099 +/- 0.0270 | 0.3893 +/- 0.0199 | 0.6050 | 0.5795 | 689.0 MB | **B3_RandomForest** |
| **XMRUSDT** | Phase 5.3.1 Pilot | 30,623 | 3 | 0.3333 | 0.3333 | **0.4177 +/- 0.0187** | 0.3902 +/- 0.0273 | 0.3816 +/- 0.0189 | 0.3729 +/- 0.0172 | 0.5546 | 0.6362 | 504.0 MB | **B2_LogisticRegression** |
| **ADAUSDT** | Phase 5.3.2 Fleet | 261,085 | 5 | 0.3333 | 0.3333 | 0.4234 +/- 0.0300 | 0.4278 +/- 0.0481 | **0.4490 +/- 0.0376** | 0.3915 +/- 0.0468 | 0.6209 | 0.6454 | 558.2 MB | **B4_LightGBM** |
| **XRPUSDT** | Phase 5.3.2 Fleet | 261,319 | 5 | 0.3333 | 0.3333 | 0.3709 +/- 0.0257 | 0.3659 +/- 0.0221 | **0.3747 +/- 0.0290** | 0.3714 +/- 0.0259 | 0.6035 | 0.5635 | 550.2 MB | **B4_LightGBM** |
| **BNBUSDT** | Phase 5.3.2 Fleet | 261,814 | 5 | 0.3333 | 0.3333 | 0.3561 +/- 0.0176 | 0.3642 +/- 0.0245 | **0.3699 +/- 0.0247** | 0.3623 +/- 0.0158 | 0.5975 | 0.5716 | 672.4 MB | **B4_LightGBM** |
| **ETHUSDT** | Phase 5.3.2 Fleet | 261,576 | 5 | 0.3333 | 0.3333 | 0.3875 +/- 0.0191 | **0.4195 +/- 0.0165** | 0.4177 +/- 0.0120 | 0.3975 +/- 0.0203 | 0.6144 | 0.5750 | 738.0 MB | **B3_RandomForest** |
| **SOLUSDT** | Phase 5.3.2 Fleet | 261,735 | 5 | 0.3333 | 0.3333 | 0.3734 +/- 0.0298 | 0.3808 +/- 0.0310 | **0.3878 +/- 0.0333** | 0.3797 +/- 0.0215 | 0.6108 | 0.5594 | 743.9 MB | **B4_LightGBM** |
| **AVAXUSDT** | Phase 5.3.2 Fleet | 261,756 | 5 | 0.3333 | 0.3333 | 0.4084 +/- 0.0451 | 0.4104 +/- 0.0481 | **0.4145 +/- 0.0431** | 0.3966 +/- 0.0417 | 0.6057 | 0.6246 | 749.9 MB | **B4_LightGBM** |
| **LINKUSDT** | Phase 5.3.2 Fleet | 261,673 | 5 | 0.3333 | 0.3333 | 0.3984 +/- 0.0429 | 0.4022 +/- 0.0453 | **0.4067 +/- 0.0468** | 0.3905 +/- 0.0406 | 0.6238 | 0.5957 | 804.6 MB | **B4_LightGBM** |
| **DOGEUSDT** | Phase 5.3.2 Fleet | 261,416 | 5 | 0.3333 | 0.3333 | 0.3838 +/- 0.0402 | 0.3870 +/- 0.0287 | **0.3960 +/- 0.0346** | 0.3904 +/- 0.0317 | 0.6099 | 0.5749 | 812.8 MB | **B4_LightGBM** |
| **LTCUSDT** | Phase 5.3.2 Fleet | 261,046 | 5 | 0.3333 | 0.3333 | 0.4208 +/- 0.0487 | **0.4402 +/- 0.0674** | 0.4355 +/- 0.0514 | 0.4253 +/- 0.0516 | 0.6399 | 0.6088 | 815.4 MB | **B3_RandomForest** |

---

## 3. Metric-Specific Winner Rankings

### 3.1 Balanced Accuracy Winners
| Rank | Symbol | Winning Model | Balanced Accuracy | Lift over B0 (0.3333) |
| :---: | :--- | :--- | :---: | :---: |
| 1 | `ADAUSDT` | B4_LightGBM | **0.4490** | +0.1157 (+34.7%) |
| 2 | `LTCUSDT` | B3_RandomForest | **0.4402** | +0.1069 (+32.1%) |
| 3 | `ETHUSDT` | B3_RandomForest | **0.4195** | +0.0862 (+25.9%) |
| 4 | `XMRUSDT` | B2_LogisticRegression | **0.4177** | +0.0844 (+25.3%) |
| 5 | `AVAXUSDT` | B4_LightGBM | **0.4145** | +0.0812 (+24.4%) |
| 6 | `BTCUSDT` | B3_RandomForest | **0.4127** | +0.0794 (+23.8%) |
| 7 | `LINKUSDT` | B4_LightGBM | **0.4067** | +0.0734 (+22.0%) |
| 8 | `DOGEUSDT` | B4_LightGBM | **0.3960** | +0.0627 (+18.8%) |
| 9 | `SOLUSDT` | B4_LightGBM | **0.3878** | +0.0545 (+16.4%) |
| 10 | `XRPUSDT` | B4_LightGBM | **0.3747** | +0.0414 (+12.4%) |
| 11 | `BNBUSDT` | B4_LightGBM | **0.3699** | +0.0366 (+11.0%) |

### 3.2 Macro F1 Winners
| Rank | Symbol | Winning Model | Macro F1 | Lift over Naive B0 |
| :---: | :--- | :--- | :---: | :---: |
| 1 | `LTCUSDT` | B3_RandomForest | **0.4264** | +0.2447 (+134.7%) |
| 2 | `ETHUSDT` | B4_LightGBM | **0.3975** | +0.1859 (+87.9%) |
| 3 | `AVAXUSDT` | B4_LightGBM | **0.3966** | +0.2088 (+111.2%) |
| 4 | `ADAUSDT` | B4_LightGBM | **0.3915** | +0.1951 (+99.3%) |
| 5 | `LINKUSDT` | B4_LightGBM | **0.3905** | +0.2139 (+121.1%) |
| 6 | `DOGEUSDT` | B4_LightGBM | **0.3904** | +0.1887 (+93.6%) |
| 7 | `BTCUSDT` | B4_LightGBM | **0.3893** | +0.1759 (+82.4%) |
| 8 | `SOLUSDT` | B4_LightGBM | **0.3797** | +0.1655 (+77.3%) |
| 9 | `XMRUSDT` | B2_LogisticRegression | **0.3796** | +0.1713 (+82.2%) |
| 10 | `XRPUSDT` | B4_LightGBM | **0.3714** | +0.1618 (+77.2%) |
| 11 | `BNBUSDT` | B4_LightGBM | **0.3623** | +0.1552 (+75.0%) |

### 3.3 Multi-Class OvR Macro ROC-AUC Winners
| Rank | Symbol | Winning Model | Multi-Class ROC-AUC |
| :---: | :--- | :--- | :---: |
| 1 | `LTCUSDT` | B4_LightGBM | **0.6399** |
| 2 | `LINKUSDT` | B4_LightGBM | **0.6238** |
| 3 | `ADAUSDT` | B4_LightGBM | **0.6209** |
| 4 | `ETHUSDT` | B4_LightGBM | **0.6144** |
| 5 | `SOLUSDT` | B4_LightGBM | **0.6108** |
| 6 | `DOGEUSDT` | B4_LightGBM | **0.6099** |
| 7 | `AVAXUSDT` | B4_LightGBM | **0.6057** |
| 8 | `BTCUSDT` | B4_LightGBM | **0.6050** |
| 9 | `XRPUSDT` | B4_LightGBM | **0.6035** |
| 10 | `BNBUSDT` | B4_LightGBM | **0.5975** |
| 11 | `XMRUSDT` | B2_LogisticRegression | **0.5863** |

### 3.4 Multi-Class Brier Score Winners (Lowest Quadratic Error)
| Rank | Symbol | Winning Model | Lowest Brier Score |
| :---: | :--- | :--- | :---: |
| 1 | `SOLUSDT` | B4_LightGBM | **0.5594** |
| 2 | `XRPUSDT` | B4_LightGBM | **0.5635** |
| 3 | `BNBUSDT` | B4_LightGBM | **0.5716** |
| 4 | `DOGEUSDT` | B4_LightGBM | **0.5749** |
| 5 | `ETHUSDT` | B4_LightGBM | **0.5750** |
| 6 | `BTCUSDT` | B4_LightGBM | **0.5795** |
| 7 | `LINKUSDT` | B4_LightGBM | **0.5957** |
| 8 | `LTCUSDT` | B3_RandomForest | **0.6083** |
| 9 | `AVAXUSDT` | B4_LightGBM | **0.6246** |
| 10 | `XMRUSDT` | B4_LightGBM | **0.6362** |
| 11 | `ADAUSDT` | B4_LightGBM | **0.6454** |

### 3.5 Inter-Fold Stability Winners (Lowest Balanced Accuracy Standard Deviation)
| Rank | Symbol | Most Stable ML Model | Inter-Fold Std |
| :---: | :--- | :--- | :---: |
| 1 | `ETHUSDT` | B4_LightGBM | **0.0120** |
| 2 | `BNBUSDT` | B2_LogisticRegression | **0.0176** |
| 3 | `XMRUSDT` | B2_LogisticRegression | **0.0187** |
| 4 | `XRPUSDT` | B3_RandomForest | **0.0221** |
| 5 | `BTCUSDT` | B2_LogisticRegression | **0.0222** |
| 6 | `DOGEUSDT` | B3_RandomForest | **0.0287** |
| 7 | `SOLUSDT` | B2_LogisticRegression | **0.0298** |
| 8 | `ADAUSDT` | B2_LogisticRegression | **0.0300** |
| 9 | `LINKUSDT` | B2_LogisticRegression | **0.0429** |
| 10 | `AVAXUSDT` | B4_LightGBM | **0.0431** |
| 11 | `LTCUSDT` | B4_LightGBM | **0.0514** |

---

## 4. Per-Class F1 Score Breakdown

The table below catalogs average out-of-fold F1 scores across the three target barrier outcomes:
- **SL (-1):** Stop-loss barrier touched first
- **EXP (0):** Expiration / time horizon reached without barrier touch
- **TP (+1):** Take-profit barrier touched first

| Symbol | Top Model | SL (-1) F1 | EXP (0) F1 | TP (+1) F1 | Naive Baseline Failure Mechanism |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **BTCUSDT** | B4_LightGBM | 0.4565 | 0.2341 | 0.4774 | B0 achieves 0.0000 on EXP (0) |
| **XMRUSDT** | B2_LogisticRegression | 0.4546 | 0.2862 | 0.3981 | B0 achieves 0.0000 on SL (-1) and EXP (0) |
| **ADAUSDT** | B4_LightGBM | 0.4052 | 0.3481 | 0.4211 | B0 achieves 0.0000 on SL (-1) and EXP (0) |
| **XRPUSDT** | B4_LightGBM | 0.5261 | 0.1713 | 0.4169 | B0 achieves 0.0000 on EXP (0) |
| **BNBUSDT** | B4_LightGBM | 0.4961 | 0.1852 | 0.4055 | B0 achieves 0.0000 on SL (-1) and EXP (0) |
| **ETHUSDT** | B4_LightGBM | 0.4593 | 0.2631 | 0.4700 | B0 achieves 0.0000 on EXP (0) |
| **SOLUSDT** | B4_LightGBM | 0.4059 | 0.1995 | 0.5337 | B0 achieves 0.0000 on EXP (0) and TP (+1) |
| **AVAXUSDT** | B4_LightGBM | 0.4213 | 0.3857 | 0.3829 | B0 achieves 0.0000 on EXP (0) and TP (+1) |
| **LINKUSDT** | B4_LightGBM | 0.3686 | 0.4067 | 0.3964 | B0 achieves 0.0000 on EXP (0) and TP (+1) |
| **DOGEUSDT** | B4_LightGBM | 0.4617 | 0.2889 | 0.4207 | B0 achieves 0.0000 on EXP (0) |
| **LTCUSDT** | B3_RandomForest | 0.4380 | 0.4313 | 0.4099 | B0 achieves 0.0000 on SL (-1) and EXP (0) |

---

## 5. Official Master Catalog Sign-Off

The metrics contained in this catalog represent the verified empirical baseline foundation for QUANTUM. Any future candidate model developed in Phase 6 must demonstrate statistically significant, fees-and-slippage-adjusted performance superior to these verified baselines.
