# QUANTUM PHASE 5.3.2: 11-INSTRUMENT SPECIALIST BASELINE RESULTS CATALOG

**Status:** Complete  
**Date:** 2026-11-01  
**Author:** QUANTUM Quantitative ML Research Fleet  
**Scope:** Phase 5.3.2 Specialist Fleet Extension & Phase 5.3.1 Pilot Integration  
**Directory:** [artifacts/phase_5_3_2/fleet_summary/](file:///d:/quantum-multi-agent/artifacts/phase_5_3_2/fleet_summary/)

---

## 1. Executive Summary

This document establishes the official empirical baseline performance catalog across all 11 specialist trading pairs of the QUANTUM architecture:
1. `BTCUSDT` (Phase 5.3.1 Pilot)
2. `XMRUSDT` (Phase 5.3.1 Pilot)
3. `ADAUSDT` (Phase 5.3.2 Fleet)
4. `XRPUSDT` (Phase 5.3.2 Fleet)
5. `BNBUSDT` (Phase 5.3.2 Fleet)
6. `ETHUSDT` (Phase 5.3.2 Fleet)
7. `SOLUSDT` (Phase 5.3.2 Fleet)
8. `AVAXUSDT` (Phase 5.3.2 Fleet)
9. `LINKUSDT` (Phase 5.3.2 Fleet)
10. `DOGEUSDT` (Phase 5.3.2 Fleet)
11. `LTCUSDT` (Phase 5.3.2 Fleet)

Each specialist was evaluated independently under strict zero-leakage conditions:
- **Zero cross-instrument pooling:** Each model fitted strictly on its own symbol's historical data.
- **Strict temporal isolation:** Expanding walk-forward validation (Folds 1 to 5) confined to Development + Validation Observed (`2023-11-01` to `2026-04-30`). The Prospective Holdout (`2026-11-01` to `2027-04-30`) remained completely untouched and unread.
- **Standardized Feature Schema:** 36 stationary features per bar (`RESEARCH_STATIONARY_FEATURES`, Schema Hash `cc779ea9e3b1862394b7115375c54c4f4cf3d6496bfabf7de457b578762aaf92`).
- **Baseline Models:** Naive Baselines (B0 Majority, B1 Prior) and Machine Learning Baselines (B2 Logistic Regression L2, B3 Balanced Random Forest, B4 LightGBM GBDT).

---

## 2. Fleet Overview and Primary Metric Comparison

The table below summarizes aggregate cross-fold performance across all 11 instruments:

| Symbol | History Type | Clean Samples | B0 BalAcc | B1 BalAcc | B2 BalAcc | B3 BalAcc | B4 BalAcc | B4 Macro F1 | B4 ROC-AUC | B4 Brier | Best BalAcc Model |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **BTCUSDT** | Full (5 folds) | 261,488 | 0.3333 | 0.3333 | 0.3919 | **0.4127** | 0.4099 | 0.3893 | 0.6050 | 0.5795 | **B3_RandomForest** |
| **XMRUSDT** | Short (3 folds) | 30,623 | 0.3333 | 0.3333 | **0.4177** | 0.3902 | 0.3816 | 0.3729 | 0.5546 | 0.6362 | **B2_LogisticRegression** |
| **ADAUSDT** | Full (5 folds) | 261,085 | 0.3333 | 0.3333 | 0.4234 | 0.4278 | **0.4490** | 0.3915 | 0.6209 | 0.6454 | **B4_LightGBM** |
| **XRPUSDT** | Full (5 folds) | 261,319 | 0.3333 | 0.3333 | 0.3709 | 0.3659 | **0.3747** | 0.3714 | 0.6035 | 0.5635 | **B4_LightGBM** |
| **BNBUSDT** | Full (5 folds) | 261,814 | 0.3333 | 0.3333 | 0.3561 | 0.3642 | **0.3699** | 0.3623 | 0.5975 | 0.5716 | **B4_LightGBM** |
| **ETHUSDT** | Full (5 folds) | 261,576 | 0.3333 | 0.3333 | 0.3875 | **0.4195** | 0.4177 | 0.3975 | 0.6144 | 0.5750 | **B3_RandomForest** |
| **SOLUSDT** | Full (5 folds) | 261,735 | 0.3333 | 0.3333 | 0.3734 | 0.3808 | **0.3878** | 0.3797 | 0.6108 | 0.5594 | **B4_LightGBM** |
| **AVAXUSDT** | Full (5 folds) | 261,756 | 0.3333 | 0.3333 | 0.4084 | 0.4104 | **0.4145** | 0.3966 | 0.6057 | 0.6246 | **B4_LightGBM** |
| **LINKUSDT** | Full (5 folds) | 261,673 | 0.3333 | 0.3333 | 0.3984 | 0.4022 | **0.4067** | 0.3905 | 0.6238 | 0.5957 | **B4_LightGBM** |
| **DOGEUSDT** | Full (5 folds) | 261,416 | 0.3333 | 0.3333 | 0.3838 | 0.3870 | **0.3960** | 0.3904 | 0.6099 | 0.5749 | **B4_LightGBM** |
| **LTCUSDT** | Full (5 folds) | 261,046 | 0.3333 | 0.3333 | 0.4208 | **0.4402** | 0.4355 | 0.4253 | 0.6399 | 0.6088 | **B3_RandomForest** |

---

## 3. Detailed Instrument Performance Summaries

### 3.1 BTCUSDT Specialist (Pilot Baseline Reference)
- Source: [artifacts/phase_5_3_1/BTCUSDT/](file:///d:/quantum-multi-agent/artifacts/phase_5_3_1/BTCUSDT/)
- Samples: 261,488 (5 Folds: Train=130,732 to 235,324, Test=26,146)

| Model | BalAcc (mean +/- std) | Macro F1 (mean +/- std) | Brier Score (mean +/- std) | ROC-AUC | SL (-1) F1 | EXP (0) F1 | TP (+1) F1 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **B0_Majority** | 0.3333 +/- 0.0000 | 0.2134 +/- 0.0051 | 1.0582 +/- 0.0329 | 0.5000 | 0.3903 | 0.0000 | 0.2498 |
| **B1_Prior** | 0.3333 +/- 0.0000 | 0.2134 +/- 0.0051 | 0.5549 +/- 0.0203 | 0.5000 | 0.3903 | 0.0000 | 0.2498 |
| **B2_LogisticRegression** | 0.3919 +/- 0.0222 | 0.3843 +/- 0.0281 | 0.5900 +/- 0.0505 | 0.5978 | 0.4425 | 0.2086 | 0.5018 |
| **B3_RandomForest** | 0.4127 +/- 0.0251 | 0.3714 +/- 0.0179 | 0.5975 +/- 0.0259 | 0.5842 | 0.4465 | 0.2025 | 0.4651 |
| **B4_LightGBM** | 0.4099 +/- 0.0270 | 0.3893 +/- 0.0199 | 0.5795 +/- 0.0398 | 0.6050 | 0.4565 | 0.2341 | 0.4774 |

### 3.2 XMRUSDT Specialist (Pilot Baseline Reference: Short History)
- Source: [artifacts/phase_5_3_1/XMRUSDT/](file:///d:/quantum-multi-agent/artifacts/phase_5_3_1/XMRUSDT/)
- Samples: 30,623 (3 Folds: Train=15,301 to 21,425, Test=3,061)

| Model | BalAcc (mean +/- std) | Macro F1 (mean +/- std) | Brier Score (mean +/- std) | ROC-AUC | SL (-1) F1 | EXP (0) F1 | TP (+1) F1 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **B0_Majority** | 0.3333 +/- 0.0000 | 0.2083 +/- 0.0051 | 1.0908 +/- 0.0319 | 0.5000 | 0.0000 | 0.0000 | 0.6249 |
| **B1_Prior** | 0.3333 +/- 0.0000 | 0.2083 +/- 0.0051 | 0.6010 +/- 0.0196 | 0.5000 | 0.0000 | 0.0000 | 0.6249 |
| **B2_LogisticRegression** | 0.4177 +/- 0.0187 | 0.3796 +/- 0.0086 | 0.6399 +/- 0.0152 | 0.5863 | 0.4546 | 0.2862 | 0.3981 |
| **B3_RandomForest** | 0.3902 +/- 0.0273 | 0.3681 +/- 0.0182 | 0.6382 +/- 0.0098 | 0.5628 | 0.4666 | 0.2258 | 0.4119 |
| **B4_LightGBM** | 0.3816 +/- 0.0189 | 0.3729 +/- 0.0172 | 0.6362 +/- 0.0194 | 0.5546 | 0.4371 | 0.2324 | 0.4493 |

### 3.3 ADAUSDT Specialist
- Source: [artifacts/phase_5_3_2/ADAUSDT/](file:///d:/quantum-multi-agent/artifacts/phase_5_3_2/ADAUSDT/)
- Samples: 261,085 (5 Folds: Train=130,530 to 234,962, Test=26,096)

| Model | BalAcc (mean +/- std) | Macro F1 (mean +/- std) | Brier Score (mean +/- std) | ROC-AUC | SL (-1) F1 | EXP (0) F1 | TP (+1) F1 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **B0_Majority** | 0.3333 +/- 0.0000 | 0.1964 +/- 0.0055 | 1.1642 +/- 0.0332 | 0.5000 | 0.0000 | 0.0000 | 0.5892 |
| **B1_Prior** | 0.3333 +/- 0.0000 | 0.1964 +/- 0.0055 | 0.6158 +/- 0.0288 | 0.5000 | 0.0000 | 0.0000 | 0.5892 |
| **B2_LogisticRegression** | 0.4234 +/- 0.0300 | 0.3586 +/- 0.0515 | 0.6669 +/- 0.0310 | 0.5964 | 0.3954 | 0.3104 | 0.3701 |
| **B3_RandomForest** | 0.4278 +/- 0.0481 | 0.3738 +/- 0.0484 | 0.6461 +/- 0.0264 | 0.6036 | 0.3928 | 0.3159 | 0.4126 |
| **B4_LightGBM** | 0.4490 +/- 0.0376 | 0.3915 +/- 0.0468 | 0.6454 +/- 0.0352 | 0.6209 | 0.4052 | 0.3481 | 0.4211 |

### 3.4 XRPUSDT Specialist
- Source: [artifacts/phase_5_3_2/XRPUSDT/](file:///d:/quantum-multi-agent/artifacts/phase_5_3_2/XRPUSDT/)
- Samples: 261,319 (5 Folds: Train=130,647 to 235,175, Test=26,120)

| Model | BalAcc (mean +/- std) | Macro F1 (mean +/- std) | Brier Score (mean +/- std) | ROC-AUC | SL (-1) F1 | EXP (0) F1 | TP (+1) F1 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **B0_Majority** | 0.3333 +/- 0.0000 | 0.2096 +/- 0.0117 | 1.0807 +/- 0.0729 | 0.5000 | 0.1333 | 0.0000 | 0.4956 |
| **B1_Prior** | 0.3333 +/- 0.0000 | 0.2096 +/- 0.0117 | 0.5855 +/- 0.0317 | 0.5000 | 0.1333 | 0.0000 | 0.4956 |
| **B2_LogisticRegression** | 0.3709 +/- 0.0257 | 0.3583 +/- 0.0136 | 0.5802 +/- 0.0499 | 0.5657 | 0.4961 | 0.1478 | 0.4311 |
| **B3_RandomForest** | 0.3659 +/- 0.0221 | 0.3522 +/- 0.0264 | 0.5723 +/- 0.0406 | 0.5853 | 0.5437 | 0.1388 | 0.3741 |
| **B4_LightGBM** | 0.3747 +/- 0.0290 | 0.3714 +/- 0.0259 | 0.5635 +/- 0.0418 | 0.6035 | 0.5261 | 0.1713 | 0.4169 |

### 3.5 BNBUSDT Specialist
- Source: [artifacts/phase_5_3_2/BNBUSDT/](file:///d:/quantum-multi-agent/artifacts/phase_5_3_2/BNBUSDT/)
- Samples: 261,814 (5 Folds: Train=130,895 to 235,623, Test=26,169)

| Model | BalAcc (mean +/- std) | Macro F1 (mean +/- std) | Brier Score (mean +/- std) | ROC-AUC | SL (-1) F1 | EXP (0) F1 | TP (+1) F1 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **B0_Majority** | 0.3333 +/- 0.0000 | 0.2071 +/- 0.0164 | 1.0955 +/- 0.0985 | 0.5000 | 0.0000 | 0.0000 | 0.6212 |
| **B1_Prior** | 0.3333 +/- 0.0000 | 0.2071 +/- 0.0164 | 0.5910 +/- 0.0452 | 0.5000 | 0.0000 | 0.0000 | 0.6212 |
| **B2_LogisticRegression** | 0.3561 +/- 0.0176 | 0.3377 +/- 0.0091 | 0.5836 +/- 0.0500 | 0.5571 | 0.5026 | 0.1443 | 0.3660 |
| **B3_RandomForest** | 0.3642 +/- 0.0245 | 0.3511 +/- 0.0118 | 0.5785 +/- 0.0418 | 0.5783 | 0.5012 | 0.1594 | 0.3926 |
| **B4_LightGBM** | 0.3699 +/- 0.0247 | 0.3623 +/- 0.0158 | 0.5716 +/- 0.0467 | 0.5975 | 0.4961 | 0.1852 | 0.4055 |

### 3.6 ETHUSDT Specialist
- Source: [artifacts/phase_5_3_2/ETHUSDT/](file:///d:/quantum-multi-agent/artifacts/phase_5_3_2/ETHUSDT/)
- Samples: 261,576 (5 Folds: Train=130,776 to 235,408, Test=26,145)

| Model | BalAcc (mean +/- std) | Macro F1 (mean +/- std) | Brier Score (mean +/- std) | ROC-AUC | SL (-1) F1 | EXP (0) F1 | TP (+1) F1 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **B0_Majority** | 0.3333 +/- 0.0000 | 0.2116 +/- 0.0062 | 1.0694 +/- 0.0389 | 0.5000 | 0.2474 | 0.0000 | 0.3874 |
| **B1_Prior** | 0.3333 +/- 0.0000 | 0.2116 +/- 0.0062 | 0.5598 +/- 0.0273 | 0.5000 | 0.2474 | 0.0000 | 0.3874 |
| **B2_LogisticRegression** | 0.3875 +/- 0.0191 | 0.3798 +/- 0.0245 | 0.5838 +/- 0.0613 | 0.5971 | 0.4417 | 0.2168 | 0.4809 |
| **B3_RandomForest** | 0.4195 +/- 0.0165 | 0.3796 +/- 0.0176 | 0.5883 +/- 0.0365 | 0.5968 | 0.4649 | 0.2304 | 0.4435 |
| **B4_LightGBM** | 0.4177 +/- 0.0120 | 0.3975 +/- 0.0203 | 0.5750 +/- 0.0483 | 0.6144 | 0.4593 | 0.2631 | 0.4700 |

### 3.7 SOLUSDT Specialist
- Source: [artifacts/phase_5_3_2/SOLUSDT/](file:///d:/quantum-multi-agent/artifacts/phase_5_3_2/SOLUSDT/)
- Samples: 261,735 (5 Folds: Train=130,855 to 235,551, Test=26,162)

| Model | BalAcc (mean +/- std) | Macro F1 (mean +/- std) | Brier Score (mean +/- std) | ROC-AUC | SL (-1) F1 | EXP (0) F1 | TP (+1) F1 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **B0_Majority** | 0.3333 +/- 0.0000 | 0.2142 +/- 0.0062 | 1.0529 +/- 0.0395 | 0.5000 | 0.6425 | 0.0000 | 0.0000 |
| **B1_Prior** | 0.3333 +/- 0.0000 | 0.2142 +/- 0.0062 | 0.5546 +/- 0.0275 | 0.5000 | 0.6425 | 0.0000 | 0.0000 |
| **B2_LogisticRegression** | 0.3734 +/- 0.0298 | 0.3659 +/- 0.0157 | 0.5741 +/- 0.0503 | 0.5813 | 0.4264 | 0.1632 | 0.5080 |
| **B3_RandomForest** | 0.3808 +/- 0.0310 | 0.3671 +/- 0.0173 | 0.5687 +/- 0.0370 | 0.5942 | 0.3986 | 0.1709 | 0.5318 |
| **B4_LightGBM** | 0.3878 +/- 0.0333 | 0.3797 +/- 0.0215 | 0.5594 +/- 0.0417 | 0.6108 | 0.4059 | 0.1995 | 0.5337 |

### 3.8 AVAXUSDT Specialist
- Source: [artifacts/phase_5_3_2/AVAXUSDT/](file:///d:/quantum-multi-agent/artifacts/phase_5_3_2/AVAXUSDT/)
- Samples: 261,756 (5 Folds: Train=130,866 to 235,570, Test=26,164)

| Model | BalAcc (mean +/- std) | Macro F1 (mean +/- std) | Brier Score (mean +/- std) | ROC-AUC | SL (-1) F1 | EXP (0) F1 | TP (+1) F1 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **B0_Majority** | 0.3333 +/- 0.0000 | 0.1878 +/- 0.0155 | 1.2125 +/- 0.0893 | 0.5000 | 0.5635 | 0.0000 | 0.0000 |
| **B1_Prior** | 0.3333 +/- 0.0000 | 0.1878 +/- 0.0155 | 0.6516 +/- 0.0157 | 0.5000 | 0.5635 | 0.0000 | 0.0000 |
| **B2_LogisticRegression** | 0.4084 +/- 0.0451 | 0.3693 +/- 0.0528 | 0.6413 +/- 0.0199 | 0.5821 | 0.4024 | 0.3976 | 0.3079 |
| **B3_RandomForest** | 0.4104 +/- 0.0481 | 0.3876 +/- 0.0467 | 0.6291 +/- 0.0181 | 0.5967 | 0.4079 | 0.3794 | 0.3755 |
| **B4_LightGBM** | 0.4145 +/- 0.0431 | 0.3966 +/- 0.0417 | 0.6246 +/- 0.0213 | 0.6057 | 0.4213 | 0.3857 | 0.3829 |

### 3.9 LINKUSDT Specialist
- Source: [artifacts/phase_5_3_2/LINKUSDT/](file:///d:/quantum-multi-agent/artifacts/phase_5_3_2/LINKUSDT/)
- Samples: 261,673 (5 Folds: Train=130,825 to 235,497, Test=26,155)

| Model | BalAcc (mean +/- std) | Macro F1 (mean +/- std) | Brier Score (mean +/- std) | ROC-AUC | SL (-1) F1 | EXP (0) F1 | TP (+1) F1 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **B0_Majority** | 0.3333 +/- 0.0000 | 0.1766 +/- 0.0318 | 1.2680 +/- 0.1736 | 0.5000 | 0.5298 | 0.0000 | 0.0000 |
| **B1_Prior** | 0.3333 +/- 0.0000 | 0.1766 +/- 0.0318 | 0.6746 +/- 0.0583 | 0.5000 | 0.5298 | 0.0000 | 0.0000 |
| **B2_LogisticRegression** | 0.3984 +/- 0.0429 | 0.3714 +/- 0.0320 | 0.6239 +/- 0.0204 | 0.5708 | 0.3649 | 0.4204 | 0.3289 |
| **B3_RandomForest** | 0.4022 +/- 0.0453 | 0.3830 +/- 0.0387 | 0.6005 +/- 0.0194 | 0.6071 | 0.3765 | 0.3956 | 0.3767 |
| **B4_LightGBM** | 0.4067 +/- 0.0468 | 0.3905 +/- 0.0406 | 0.5957 +/- 0.0240 | 0.6238 | 0.3686 | 0.4067 | 0.3964 |

### 3.10 DOGEUSDT Specialist
- Source: [artifacts/phase_5_3_2/DOGEUSDT/](file:///d:/quantum-multi-agent/artifacts/phase_5_3_2/DOGEUSDT/)
- Samples: 261,416 (5 Folds: Train=130,695 to 235,263, Test=26,130)

| Model | BalAcc (mean +/- std) | Macro F1 (mean +/- std) | Brier Score (mean +/- std) | ROC-AUC | SL (-1) F1 | EXP (0) F1 | TP (+1) F1 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **B0_Majority** | 0.3333 +/- 0.0000 | 0.2017 +/- 0.0236 | 1.1257 +/- 0.1367 | 0.5000 | 0.1331 | 0.0000 | 0.4719 |
| **B1_Prior** | 0.3333 +/- 0.0000 | 0.2017 +/- 0.0236 | 0.6057 +/- 0.0681 | 0.5000 | 0.1331 | 0.0000 | 0.4719 |
| **B2_LogisticRegression** | 0.3838 +/- 0.0402 | 0.3723 +/- 0.0330 | 0.5887 +/- 0.0511 | 0.5752 | 0.4400 | 0.2390 | 0.4378 |
| **B3_RandomForest** | 0.3870 +/- 0.0287 | 0.3762 +/- 0.0270 | 0.5775 +/- 0.0404 | 0.5996 | 0.4685 | 0.2583 | 0.4017 |
| **B4_LightGBM** | 0.3960 +/- 0.0346 | 0.3904 +/- 0.0317 | 0.5749 +/- 0.0474 | 0.6099 | 0.4617 | 0.2889 | 0.4207 |

### 3.11 LTCUSDT Specialist
- Source: [artifacts/phase_5_3_2/LTCUSDT/](file:///d:/quantum-multi-agent/artifacts/phase_5_3_2/LTCUSDT/)
- Samples: 261,046 (5 Folds: Train=130,511 to 234,927, Test=26,092)

| Model | BalAcc (mean +/- std) | Macro F1 (mean +/- std) | Brier Score (mean +/- std) | ROC-AUC | SL (-1) F1 | EXP (0) F1 | TP (+1) F1 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **B0_Majority** | 0.3333 +/- 0.0000 | 0.1817 +/- 0.0165 | 1.2471 +/- 0.0956 | 0.5000 | 0.0000 | 0.0000 | 0.5453 |
| **B1_Prior** | 0.3333 +/- 0.0000 | 0.1817 +/- 0.0165 | 0.6622 +/- 0.0323 | 0.5000 | 0.0000 | 0.0000 | 0.5453 |
| **B2_LogisticRegression** | 0.4208 +/- 0.0487 | 0.4002 +/- 0.0594 | 0.6292 +/- 0.0223 | 0.6075 | 0.4084 | 0.4236 | 0.3684 |
| **B3_RandomForest** | **0.4402 +/- 0.0674** | **0.4264 +/- 0.0639** | **0.6083 +/- 0.0272** | **0.6375** | 0.4380 | 0.4313 | 0.4099 |
| **B4_LightGBM** | 0.4355 +/- 0.0514 | 0.4253 +/- 0.0516 | 0.6088 +/- 0.0299 | 0.6399 | 0.4124 | 0.4330 | 0.4306 |

---

## 4. Key Analytical Findings

1. **Decisive Outperformance Over Naive Baselines:**
   - In all 11 instruments, Machine Learning baselines (B2, B3, B4) outperformed Naive Baselines (B0 Majority, B1 Prior) by a substantial margin:
     - Balanced Accuracy increased from random chance (0.3333) to between 0.370 (BNBUSDT) and 0.449 (ADAUSDT).
     - Macro F1 improved from naive baselines (0.1766 to 0.2142) to between 0.3623 and 0.4264 (+70% to +140% relative improvement).
     - Multi-class ROC-AUC (OvR macro-average) exceeded 0.5000 across all ML models, reaching up to 0.6399 on LTCUSDT and 0.6238 on LINKUSDT.

2. **Per-Class Barrier Dynamics:**
   - Naive baselines predict only the dominant class, resulting in 0.0000 F1 for the other two classes (particularly the expiration class EXP=0).
   - In contrast, ML models successfully learn non-trivial decision boundaries across all three outcomes: Stop Loss hit first (SL=-1), Expiration / Barrier not reached (EXP=0), and Take Profit hit first (TP=+1).

3. **Specialist Performance Archetypes:**
   - **High-Learnability Trend Specialists (ADA, LTC, ETH, BTC):** B3/B4 achieve Balanced Acc > 0.4100 and ROC-AUC > 0.6050, showing strong responsiveness to momentum and volatility signals.
   - **Mean-Reverting / Microstructure Specialists (XRP, BNB, DOGE):** Lower Balanced Acc (0.3700 to 0.3960) and lower ROC-AUC (0.5500 to 0.6099), indicating noisy short-term dynamics where linear models underperform non-linear trees.
   - **Short-History Anomaly (XMR):** Constrained sample size (30,623 samples) led to linear B2 (0.4177) outperforming tree models (0.3816 to 0.3902), typical of sample-limited regimes.

---

## 5. Artifact Audit Verification

All individual model artifacts, fold evaluations, preprocessor states, and predictions have been verified on disk:
- Master Catalog: [artifacts/phase_5_3_2/fleet_summary/fleet_catalog.json](file:///d:/quantum-multi-agent/artifacts/phase_5_3_2/fleet_summary/fleet_catalog.json)
- Comparative Summary: [artifacts/phase_5_3_2/fleet_summary/fleet_comparison.json](file:///d:/quantum-multi-agent/artifacts/phase_5_3_2/fleet_summary/fleet_comparison.json)
- Checksum Manifests: [artifacts/phase_5_3_2/fleet_summary/manifest_hashes.json](file:///d:/quantum-multi-agent/artifacts/phase_5_3_2/fleet_summary/manifest_hashes.json)
