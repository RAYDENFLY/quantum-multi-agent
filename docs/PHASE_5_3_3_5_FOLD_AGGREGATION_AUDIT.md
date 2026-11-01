# QUANTUM PHASE 5.3.3.5: FOLD AGGREGATION & DISCREPANCY FORENSIC AUDIT

**Role:** Independent Senior Quantitative Research Auditor and Financial ML Validation Specialist  
**System:** QUANTUM 11-Specialist Cryptocurrency Perpetual Futures ML Trading Research System  
**Repository:** [quantum-multi-agent](file:///d:/quantum-multi-agent)  
**Phase:** Phase 5.3.3.5 (Audit Deliverable A)  
**Audit Scope:** Temporal Fold Confusion Matrices, Class Support Accounting, and Pooled vs Fold-Mean Mathematical Reconciliation  

---

## 1. Executive Summary

This forensic audit delivers a complete, instrument-by-instrument reconciliation between:
1. The **historical unweighted fold-mean Balanced Accuracy** benchmarks established in Phase 5.3.1 through Phase 5.3.3.2.
2. The **pooled out-of-fold (OOF) Balanced Accuracy** reconstructed across the 1,322,108 canonical evaluation candles.

Key audit conclusions:
- **Historical Benchmark Fidelity:** For all 11 specialist instruments, the reconstructed unweighted fold-mean Balanced Accuracy matches the historical benchmark catalog to four decimal places (exact 0.0000 difference). Provenance is 100% verified.
- **Mathematical Origin of Discrepancy:** The difference between pooled Balanced Accuracy and unweighted fold-mean Balanced Accuracy is strictly an arithmetic consequence of non-stationary class support across temporal folds. Under triple-barrier labeling with barrier multiplier 1.5, market volatility regime shifts cause Class 0 (Time Expiration) support to fluctuate by more than an order of magnitude between low-volatility folds (~13,000 candles) and high-volatility folds (~800 candles).
- **Consistent Model Ranking Across Strata and Aggregate:** Specialist Model B4 outperforms Baseline B0 in all 55 individual folds and across all 11 pooled datasets without a single ranking inversion. The divergence between pooled BA and unweighted fold-mean BA is strictly a **non-stationary support-weighted macro-aggregation effect**.
- **Data Integrity & Holdout Protection:** Exactly 1,322,108 canonical OOF candles were evaluated. Zero prospective holdout candles (2026-11-01 00:00:00 UTC through 2027-04-30 23:59:59.999 UTC) were accessed. Zero models were trained, retrained, or fitted.

---

## 2. Canonical Target Schema & Evaluation Metrics

### 2.1 Target Schema
All 11 instruments operate on the canonical three-class triple-barrier target definition:
- **Class -1 (SL):** Stop-loss barrier hit first within the 12-bar horizontal horizon.
- **Class 0 (EXP):** Neither stop-loss nor take-profit barrier hit; position expired at bar 12.
- **Class 1 (TP):** Take-profit barrier hit first within the 12-bar horizontal horizon.

### 2.2 Confusion Matrix Representation
Confusion matrices are defined in canonical class order `[-1, 0, 1] = [SL, EXP, TP]` with rows representing ground-truth classes and columns representing model predictions:
```
                 Predicted SL (-1)   Predicted EXP (0)   Predicted TP (+1)
True SL (-1)          C[0,0]              C[0,1]              C[0,2]
True EXP (0)          C[1,0]              C[1,1]              C[1,2]
True TP (+1)          C[2,0]              C[2,1]              C[2,2]
```

### 2.3 Mathematical Metric Formulations
For each fold $k \in \{1, \dots, K\}$ (where $K=5$):
- **Class Support:** $N_k(c) = \sum_{j \in \{-1, 0, 1\}} C_k[c, j]$
- **Per-Class Recall:** $\text{Recall}_k(c) = \frac{C_k[c, c]}{N_k(c)}$
- **Fold Balanced Accuracy:** $\text{BA}_k = \frac{1}{3} \sum_{c \in \{-1, 0, 1\}} \text{Recall}_k(c)$
- **Unweighted Fold-Mean Balanced Accuracy:**
  $$\overline{\text{BA}}_{\text{fold\_mean}} = \frac{1}{K} \sum_{k=1}^K \text{BA}_k = \frac{1}{3} \sum_{c \in \{-1, 0, 1\}} \left[ \frac{1}{K} \sum_{k=1}^K \text{Recall}_k(c) \right]$$
- **Pooled Balanced Accuracy:**
  $$\text{BA}_{\text{pooled}} = \frac{1}{3} \sum_{c \in \{-1, 0, 1\}} \left[ \frac{\sum_{k=1}^K C_k[c, c]}{\sum_{k=1}^K N_k(c)} \right] = \frac{1}{3} \sum_{c \in \{-1, 0, 1\}} \left[ \sum_{k=1}^K w_k(c) \cdot \text{Recall}_k(c) \right]$$
  where the fold support weight for class $c$ is:
  $$w_k(c) = \frac{N_k(c)}{N_{\text{total}}(c)}, \quad \sum_{k=1}^K w_k(c) = 1.0$$
- **Exact Difference Formula:**
  $$\text{BA}_{\text{pooled}} - \overline{\text{BA}}_{\text{fold\_mean}} = \frac{1}{3} \sum_{c \in \{-1, 0, 1\}} \sum_{k=1}^K \left( w_k(c) - \frac{1}{K} \right) \cdot \text{Recall}_k(c)$$

---

## 3. Master Fleet Summary Catalog

The table below contrasts the historical unweighted fold-mean Balanced Accuracy against the pooled OOF Balanced Accuracy across all 11 specialists:

| Specialist Instrument | Total OOF Candles | Historical Benchmark BA | Phase 5.3.3.5 Fold-Mean BA | Reconciliation Verdict | Pooled OOF BA | Absolute Difference | Relative Gap (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **BTCUSDT** | 130,684 | 0.4099 | 0.409888 | **EXACT MATCH** | **0.433187** | +0.023299 | +5.68% |
| **ETHUSDT** | 130,728 | 0.4177 | 0.417712 | **EXACT MATCH** | **0.457130** | +0.039418 | +9.44% |
| **BNBUSDT** | 130,847 | 0.3699 | 0.369943 | **EXACT MATCH** | **0.466677** | +0.096734 | +26.15% |
| **XRPUSDT** | 130,600 | 0.3747 | 0.374766 | **EXACT MATCH** | **0.428589** | +0.053823 | +14.36% |
| **ADAUSDT** | 130,483 | 0.4490 | 0.448953 | **EXACT MATCH** | **0.468513** | +0.019560 | +4.36% |
| **SOLUSDT** | 130,808 | 0.3878 | 0.387837 | **EXACT MATCH** | **0.439965** | +0.052128 | +13.44% |
| **AVAXUSDT** | 130,818 | 0.4145 | 0.414487 | **EXACT MATCH** | **0.452262** | +0.037775 | +9.11% |
| **LINKUSDT** | 130,777 | 0.4067 | 0.406753 | **EXACT MATCH** | **0.498942** | +0.092189 | +22.66% |
| **DOGEUSDT** | 130,648 | 0.3960 | 0.395983 | **EXACT MATCH** | **0.489942** | +0.093959 | +23.73% |
| **LTCUSDT** | 130,463 | 0.4355 | 0.435514 | **EXACT MATCH** | **0.485102** | +0.049589 | +11.39% |
| **XMRUSDT** | 15,252 | 0.3816 | 0.381554 | **EXACT MATCH** | **0.386760** | +0.005206 | +1.36% |

---

## 4. Mathematical Proof & Forensic Discrepancy Analysis

### 4.1 Proof of Equivalence Under Uniform Support
If class support were identical across all $K$ folds, such that $N_1(c) = N_2(c) = \dots = N_K(c)$ for each class $c$, then:
$$w_k(c) = \frac{N_k(c)}{K \cdot N_k(c)} = \frac{1}{K}$$
In that special case, pooled Balanced Accuracy would be mathematically identical to unweighted fold-mean Balanced Accuracy:
$$\text{BA}_{\text{pooled}} = \frac{1}{3} \sum_{c} \left[ \sum_{k=1}^K \frac{1}{K} \text{Recall}_k(c) \right] = \overline{\text{BA}}_{\text{fold\_mean}}$$

### 4.2 Non-Stationary Regime Shifts in Financial Time Series
In real-world cryptocurrency markets, price volatility regimes shift dramatically across multi-year temporal cross-validation folds. Under triple-barrier labeling:
1. **Low-Volatility Regimes (Compression / Consolidation):** Price moves within tight bands and rarely breaches the vertical $\pm 1.5\sigma$ barrier within 12 bars (60 minutes). As a result, Class 0 (Time Expiration) represents 30% to 50% of all fold observations, and the specialist model achieves very high recall on Class 0 (70% to 90%).
2. **High-Volatility Regimes (Trending / Expansion):** Price volatility surges, causing nearly every 5-minute candle to trigger either Take Profit (+1) or Stop Loss (-1) within 12 bars. Consequently, Class 0 support collapses to less than 4% of fold observations, and model recall on Class 0 drops toward zero (1% to 10%).

### 4.3 Why Unweighted Fold-Mean Severely Distorts Performance
When calculating the unweighted fold-mean Balanced Accuracy:
- Every fold receives an identical weight of $\frac{1}{K} = 0.20$.
- A fold containing only 893 Class 0 candles with 2.0% recall is given the **exact same weight (20%)** as a fold containing 7,477 Class 0 candles with 74.1% recall.
- This drastically suppresses the fold-mean Class 0 recall, pulling down the overall unweighted fold-mean Balanced Accuracy.
- In contrast, **pooled Balanced Accuracy weights each fold by its true empirical support $w_k(c)$**, giving the 7,477-candle fold its rightful ~60% share of Class 0 recall and the 893-candle fold only a ~7% share.

### 4.4 Case Study: BNBUSDT (Largest Discrepancy: +0.0967)
Consider the exact empirical numbers for BNBUSDT across its 5 temporal folds:

| Fold Index | Total Test Samples | SL Support ($N_k$) | EXP Support ($N_k$) | TP Support ($N_k$) | SL Recall | EXP Recall | TP Recall | Fold BA |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | 26,169 | 9,385 | 7,477 | 9,307 | 0.2432 | 0.7411 | 0.2626 | 0.4156 |
| Fold 2 | 26,169 | 12,210 | 1,950 | 12,009 | 0.6244 | 0.1190 | 0.3603 | 0.3679 |
| Fold 3 | 26,169 | 12,234 | 1,152 | 12,783 | 0.7057 | 0.0590 | 0.3009 | 0.3552 |
| Fold 4 | 26,169 | 12,736 | 893 | 12,540 | 0.5659 | 0.0202 | 0.4419 | 0.3426 |
| Fold 5 | 26,171 | 12,635 | 998 | 12,538 | 0.5767 | 0.0972 | 0.4312 | 0.3684 |

**Forensic Support Breakdown for BNBUSDT Class 0 (EXP):**
- Total EXP support across all folds: $7,477 + 1,950 + 1,152 + 893 + 998 = 12,470$ candles.
- Fold 1 contains 7,477 EXP candles: **59.96% of all EXP candles in the dataset**. Fold 1 EXP recall is **74.11%**.
- Fold 4 contains only 893 EXP candles: **7.16% of all EXP candles in the dataset**. Fold 4 EXP recall is **2.02%**.

**Comparing Recall Calculations for BNBUSDT Class 0:**
- **Unweighted Fold-Mean EXP Recall:**
  $$\overline{\text{Recall}}(\text{EXP}) = \frac{0.7411 + 0.1190 + 0.0590 + 0.0202 + 0.0972}{5} = 0.2073$$
- **Support-Weighted Pooled EXP Recall:**
  $$\text{Recall}_{\text{pooled}}(\text{EXP}) = 0.5996(0.7411) + 0.1564(0.1190) + 0.0924(0.0590) + 0.0716(0.0202) + 0.0800(0.0972) = 0.4771$$
- The difference in Class 0 recall alone is $+0.2698$. Dividing by 3 classes: $+0.2698 / 3 = +0.0899$.
- This single support asymmetry accounts for **93% of the entire +0.0967 difference** between pooled BA (0.4667) and fold-mean BA (0.3699).

### 4.5 Case Studies: LINKUSDT (+0.0922) and DOGEUSDT (+0.0940)
The exact same support-weighting mechanism operates in LINKUSDT and DOGEUSDT:
- **LINKUSDT:** Folds 1 and 2 represent low-volatility regimes where Class 0 support reached 11,226 and 13,309 candles (with 82.1% and 89.9% recall). Folds 4 and 5 represent high-volatility regimes where Class 0 support dropped to 2,083 and 3,374 candles (with 1.2% and 14.0% recall). Unweighted fold-mean gives the 1.2% recall fold 20% weight, dragging down fold-mean BA to 0.4067, while pooled BA properly weights the samples by $w_k(0) = [0.3186, 0.3779, 0.1485, 0.0591, 0.0958]$ to yield 0.4989.
- **DOGEUSDT:** Fold 1 contains 10,088 EXP candles ($w_1(0) = 0.6294$) with 74.9% recall, while Fold 4 and 5 contain only 1,055 ($w_4(0) = 0.0658$) and 974 ($w_5(0) = 0.0608$) candles with 4.5% and 10.9% recall. Unweighted fold-mean yields 0.3960, while pooled BA yields 0.4899.

### 4.6 Classification of the Aggregation Phenomenon
We evaluated Specialist Model B4 against Baseline Model B0 across every individual fold for all 11 instruments:
- In every single fold (55 out of 55 folds), Model B4 Balanced Accuracy is strictly greater than Baseline B0 Balanced Accuracy.
- In the pooled aggregate (11 out of 11 instruments), Model B4 Balanced Accuracy is strictly greater than Baseline B0 Balanced Accuracy.
- Because there is zero directional reversal or ranking inversion between any fold and the aggregate, this divergence is strictly classified as a **non-stationary support-weighted macro-aggregation effect** caused by positive covariance between fold class support $w_k(c)$ and fold recall $\text{Recall}_k(c)$ on Class 0.

---

## 5. Instrument-by-Instrument Granular Confusion Matrix Catalog

### 5.1 BTCUSDT Forensic Audit
- **Total OOF Candles:** 130,684
- **Historical Benchmark Fold-Mean BA:** 0.4099
- **Phase 5.3.3.5 Reconstructed Fold-Mean BA:** 0.409888 (Exact Reconciliation)
- **Pooled OOF B4 Balanced Accuracy:** 0.433187
- **Pooled OOF B0 Balanced Accuracy:** 0.332773
- **Discrepancy (B4 Pooled - B4 Fold-Mean):** +0.023299
- **Fold Support Weights $w_k(\text{SL})$:** [0.1872, 0.1993, 0.2038, 0.2048, 0.2049]
- **Fold Support Weights $w_k(\text{EXP})$:** [0.3895, 0.1708, 0.1691, 0.1384, 0.1322]
- **Fold Support Weights $w_k(\text{TP})$:** [0.1893, 0.2043, 0.2, 0.2028, 0.2036]

#### Per-Fold Support, Recall, and Balanced Accuracy Table
| Fold | Test Samples | Support [SL, EXP, TP] | B4 Recall [SL, EXP, TP] | B4 Fold BA | Historical BA | B0 Majority Class | B0 Fold BA |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | 26,136 | [11,618, 2,972, 11,546] | [0.3001, 0.6120, 0.3729] | 0.428347 | 0.4283 | +1 | 0.333333 |
| Fold 2 | 26,136 | [12,372, 1,303, 12,461] | [0.3847, 0.1650, 0.5956] | 0.381787 | 0.3818 | -1 | 0.333333 |
| Fold 3 | 26,136 | [12,649, 1,290, 12,197] | [0.4577, 0.2295, 0.5237] | 0.403592 | 0.4036 | +1 | 0.333333 |
| Fold 4 | 26,136 | [12,711, 1,056, 12,369] | [0.4849, 0.1809, 0.4852] | 0.383657 | 0.3837 | -1 | 0.333333 |
| Fold 5 | 26,140 | [12,716, 1,009, 12,415] | [0.5372, 0.3994, 0.4196] | 0.452059 | 0.4521 | -1 | 0.333333 |

#### Per-Fold 3x3 Confusion Matrices (Rows = True [SL, EXP, TP], Cols = Predicted [SL, EXP, TP])
| Fold | B4 Row SL (-1) | B4 Row EXP (0) | B4 Row TP (+1) | B0 Row SL (-1) | B0 Row EXP (0) | B0 Row TP (+1) | Matrix Sum |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | `[3486, 4036, 4096]` | `[533, 1819, 620]` | `[3260, 3980, 4306]` | `[0, 0, 11618]` | `[0, 0, 2972]` | `[0, 0, 11546]` | 26,136 |
| Fold 2 | `[4760, 264, 7348]` | `[463, 215, 625]` | `[4677, 362, 7422]` | `[12372, 0, 0]` | `[1303, 0, 0]` | `[12461, 0, 0]` | 26,136 |
| Fold 3 | `[5789, 402, 6458]` | `[508, 296, 486]` | `[5353, 457, 6387]` | `[0, 0, 12649]` | `[0, 0, 1290]` | `[0, 0, 12197]` | 26,136 |
| Fold 4 | `[6163, 438, 6110]` | `[404, 191, 461]` | `[5859, 508, 6002]` | `[12711, 0, 0]` | `[1056, 0, 0]` | `[12369, 0, 0]` | 26,136 |
| Fold 5 | `[6831, 851, 5034]` | `[295, 403, 311]` | `[6477, 729, 5209]` | `[12716, 0, 0]` | `[1009, 0, 0]` | `[12415, 0, 0]` | 26,140 |

#### Pooled 3x3 Confusion Matrices (B4 and B0)
```
B4 POOLED CONFUSION MATRIX (Total = 130,684, BA = 0.433187):
True SL  (62,066):    27029 (SL)     5991 (EXP)    29046 (TP)  |  Recall: 0.435488
True EXP (7,630):     2203 (SL)     2924 (EXP)     2503 (TP)  |  Recall: 0.383224
True TP  (60,988):    25626 (SL)     6036 (EXP)    29326 (TP)  |  Recall: 0.480849

B0 POOLED CONFUSION MATRIX (Total = 130,684, BA = 0.332773):
True SL  (62,066):    37799 (SL)        0 (EXP)    24267 (TP)  |  Recall: 0.609013
True EXP (7,630):     3368 (SL)        0 (EXP)     4262 (TP)  |  Recall: 0.000000
True TP  (60,988):    37245 (SL)        0 (EXP)    23743 (TP)  |  Recall: 0.389306
```

---

### 5.2 ETHUSDT Forensic Audit
- **Total OOF Candles:** 130,728
- **Historical Benchmark Fold-Mean BA:** 0.4177
- **Phase 5.3.3.5 Reconstructed Fold-Mean BA:** 0.417712 (Exact Reconciliation)
- **Pooled OOF B4 Balanced Accuracy:** 0.457130
- **Pooled OOF B0 Balanced Accuracy:** 0.330614
- **Discrepancy (B4 Pooled - B4 Fold-Mean):** +0.039418
- **Fold Support Weights $w_k(\text{SL})$:** [0.1826, 0.2002, 0.2048, 0.2053, 0.2072]
- **Fold Support Weights $w_k(\text{EXP})$:** [0.4664, 0.1326, 0.1352, 0.1263, 0.1396]
- **Fold Support Weights $w_k(\text{TP})$:** [0.1821, 0.2087, 0.2037, 0.2045, 0.2009]

#### Per-Fold Support, Recall, and Balanced Accuracy Table
| Fold | Test Samples | Support [SL, EXP, TP] | B4 Recall [SL, EXP, TP] | B4 Fold BA | Historical BA | B0 Majority Class | B0 Fold BA |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | 26,145 | [11,173, 3,789, 11,183] | [0.2848, 0.6865, 0.3273] | 0.432846 | 0.4328 | -1 | 0.333333 |
| Fold 2 | 26,145 | [12,251, 1,077, 12,817] | [0.4924, 0.2841, 0.4979] | 0.424835 | 0.4248 | -1 | 0.333333 |
| Fold 3 | 26,145 | [12,537, 1,098, 12,510] | [0.4411, 0.2404, 0.5233] | 0.401624 | 0.4016 | +1 | 0.333333 |
| Fold 4 | 26,145 | [12,563, 1,026, 12,556] | [0.4791, 0.2368, 0.5006] | 0.405528 | 0.4055 | +1 | 0.333333 |
| Fold 5 | 26,148 | [12,680, 1,134, 12,334] | [0.5123, 0.3139, 0.4449] | 0.423728 | 0.4237 | +1 | 0.333333 |

#### Per-Fold 3x3 Confusion Matrices (Rows = True [SL, EXP, TP], Cols = Predicted [SL, EXP, TP])
| Fold | B4 Row SL (-1) | B4 Row EXP (0) | B4 Row TP (+1) | B0 Row SL (-1) | B0 Row EXP (0) | B0 Row TP (+1) | Matrix Sum |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | `[3182, 4571, 3420]` | `[521, 2601, 667]` | `[3115, 4408, 3660]` | `[11173, 0, 0]` | `[3789, 0, 0]` | `[11183, 0, 0]` | 26,145 |
| Fold 2 | `[6033, 463, 5755]` | `[339, 306, 432]` | `[5927, 508, 6382]` | `[12251, 0, 0]` | `[1077, 0, 0]` | `[12817, 0, 0]` | 26,145 |
| Fold 3 | `[5530, 490, 6517]` | `[392, 264, 442]` | `[5411, 552, 6547]` | `[0, 0, 12537]` | `[0, 0, 1098]` | `[0, 0, 12510]` | 26,145 |
| Fold 4 | `[6019, 367, 6177]` | `[332, 243, 451]` | `[5859, 411, 6286]` | `[0, 0, 12563]` | `[0, 0, 1026]` | `[0, 0, 12556]` | 26,145 |
| Fold 5 | `[6496, 695, 5489]` | `[403, 356, 375]` | `[6292, 554, 5488]` | `[0, 0, 12680]` | `[0, 0, 1134]` | `[0, 0, 12334]` | 26,148 |

#### Pooled 3x3 Confusion Matrices (B4 and B0)
```
B4 POOLED CONFUSION MATRIX (Total = 130,728, BA = 0.457130):
True SL  (61,204):    27260 (SL)     6586 (EXP)    27358 (TP)  |  Recall: 0.445396
True EXP (8,124):     1987 (SL)     3770 (EXP)     2367 (TP)  |  Recall: 0.464057
True TP  (61,400):    26604 (SL)     6433 (EXP)    28363 (TP)  |  Recall: 0.461938

B0 POOLED CONFUSION MATRIX (Total = 130,728, BA = 0.330614):
True SL  (61,204):    23424 (SL)        0 (EXP)    37780 (TP)  |  Recall: 0.382720
True EXP (8,124):     4866 (SL)        0 (EXP)     3258 (TP)  |  Recall: 0.000000
True TP  (61,400):    24000 (SL)        0 (EXP)    37400 (TP)  |  Recall: 0.609121
```

---

### 5.3 BNBUSDT Forensic Audit
- **Total OOF Candles:** 130,847
- **Historical Benchmark Fold-Mean BA:** 0.3699
- **Phase 5.3.3.5 Reconstructed Fold-Mean BA:** 0.369943 (Exact Reconciliation)
- **Pooled OOF B4 Balanced Accuracy:** 0.466677
- **Pooled OOF B0 Balanced Accuracy:** 0.333333
- **Discrepancy (B4 Pooled - B4 Fold-Mean):** +0.096734
- **Fold Support Weights $w_k(\text{SL})$:** [0.1585, 0.2062, 0.2067, 0.2151, 0.2134]
- **Fold Support Weights $w_k(\text{EXP})$:** [0.5996, 0.1564, 0.0924, 0.0716, 0.08]
- **Fold Support Weights $w_k(\text{TP})$:** [0.1573, 0.2029, 0.216, 0.2119, 0.2119]

#### Per-Fold Support, Recall, and Balanced Accuracy Table
| Fold | Test Samples | Support [SL, EXP, TP] | B4 Recall [SL, EXP, TP] | B4 Fold BA | Historical BA | B0 Majority Class | B0 Fold BA |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | 26,169 | [9,385, 7,477, 9,307] | [0.2432, 0.7411, 0.2626] | 0.415608 | 0.4156 | +1 | 0.333333 |
| Fold 2 | 26,169 | [12,210, 1,950, 12,009] | [0.6244, 0.1190, 0.3603] | 0.367898 | 0.3679 | +1 | 0.333333 |
| Fold 3 | 26,169 | [12,234, 1,152, 12,783] | [0.7057, 0.0590, 0.3009] | 0.355184 | 0.3552 | +1 | 0.333333 |
| Fold 4 | 26,169 | [12,736, 893, 12,540] | [0.5659, 0.0202, 0.4419] | 0.342633 | 0.3426 | +1 | 0.333333 |
| Fold 5 | 26,171 | [12,635, 998, 12,538] | [0.5767, 0.0972, 0.4312] | 0.368392 | 0.3684 | +1 | 0.333333 |

#### Per-Fold 3x3 Confusion Matrices (Rows = True [SL, EXP, TP], Cols = Predicted [SL, EXP, TP])
| Fold | B4 Row SL (-1) | B4 Row EXP (0) | B4 Row TP (+1) | B0 Row SL (-1) | B0 Row EXP (0) | B0 Row TP (+1) | Matrix Sum |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | `[2282, 4887, 2216]` | `[794, 5541, 1142]` | `[2116, 4747, 2444]` | `[0, 0, 9385]` | `[0, 0, 7477]` | `[0, 0, 9307]` | 26,169 |
| Fold 2 | `[7624, 430, 4156]` | `[1047, 232, 671]` | `[7249, 433, 4327]` | `[0, 0, 12210]` | `[0, 0, 1950]` | `[0, 0, 12009]` | 26,169 |
| Fold 3 | `[8633, 124, 3477]` | `[696, 68, 388]` | `[8831, 106, 3846]` | `[0, 0, 12234]` | `[0, 0, 1152]` | `[0, 0, 12783]` | 26,169 |
| Fold 4 | `[7207, 41, 5488]` | `[514, 18, 361]` | `[6967, 32, 5541]` | `[0, 0, 12736]` | `[0, 0, 893]` | `[0, 0, 12540]` | 26,169 |
| Fold 5 | `[7287, 71, 5277]` | `[453, 97, 448]` | `[7038, 93, 5407]` | `[0, 0, 12635]` | `[0, 0, 998]` | `[0, 0, 12538]` | 26,171 |

#### Pooled 3x3 Confusion Matrices (B4 and B0)
```
B4 POOLED CONFUSION MATRIX (Total = 130,847, BA = 0.466677):
True SL  (59,200):    33033 (SL)     5553 (EXP)    20614 (TP)  |  Recall: 0.557990
True EXP (12,470):     3504 (SL)     5956 (EXP)     3010 (TP)  |  Recall: 0.477626
True TP  (59,177):    32201 (SL)     5411 (EXP)    21565 (TP)  |  Recall: 0.364415

B0 POOLED CONFUSION MATRIX (Total = 130,847, BA = 0.333333):
True SL  (59,200):        0 (SL)        0 (EXP)    59200 (TP)  |  Recall: 0.000000
True EXP (12,470):        0 (SL)        0 (EXP)    12470 (TP)  |  Recall: 0.000000
True TP  (59,177):        0 (SL)        0 (EXP)    59177 (TP)  |  Recall: 1.000000
```

---

### 5.4 XRPUSDT Forensic Audit
- **Total OOF Candles:** 130,600
- **Historical Benchmark Fold-Mean BA:** 0.3747
- **Phase 5.3.3.5 Reconstructed Fold-Mean BA:** 0.374766 (Exact Reconciliation)
- **Pooled OOF B4 Balanced Accuracy:** 0.428589
- **Pooled OOF B0 Balanced Accuracy:** 0.334817
- **Discrepancy (B4 Pooled - B4 Fold-Mean):** +0.053823
- **Fold Support Weights $w_k(\text{SL})$:** [0.1703, 0.1991, 0.2049, 0.2132, 0.2124]
- **Fold Support Weights $w_k(\text{EXP})$:** [0.5532, 0.1487, 0.1389, 0.0851, 0.0741]
- **Fold Support Weights $w_k(\text{TP})$:** [0.1723, 0.2094, 0.205, 0.2053, 0.208]

#### Per-Fold Support, Recall, and Balanced Accuracy Table
| Fold | Test Samples | Support [SL, EXP, TP] | B4 Recall [SL, EXP, TP] | B4 Fold BA | Historical BA | B0 Majority Class | B0 Fold BA |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | 26,120 | [10,465, 5,438, 10,217] | [0.3587, 0.5044, 0.4195] | 0.427543 | 0.4275 | +1 | 0.333333 |
| Fold 2 | 26,120 | [12,240, 1,462, 12,418] | [0.5550, 0.0814, 0.4643] | 0.366902 | 0.3669 | +1 | 0.333333 |
| Fold 3 | 26,120 | [12,595, 1,365, 12,160] | [0.5914, 0.1604, 0.3877] | 0.379843 | 0.3798 | +1 | 0.333333 |
| Fold 4 | 26,120 | [13,106, 837, 12,177] | [0.6739, 0.0227, 0.3319] | 0.342815 | 0.3428 | +1 | 0.333333 |
| Fold 5 | 26,120 | [13,057, 728, 12,335] | [0.7266, 0.0673, 0.2763] | 0.356726 | 0.3567 | -1 | 0.333333 |

#### Per-Fold 3x3 Confusion Matrices (Rows = True [SL, EXP, TP], Cols = Predicted [SL, EXP, TP])
| Fold | B4 Row SL (-1) | B4 Row EXP (0) | B4 Row TP (+1) | B0 Row SL (-1) | B0 Row EXP (0) | B0 Row TP (+1) | Matrix Sum |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | `[3754, 3138, 3573]` | `[1300, 2743, 1395]` | `[3078, 2853, 4286]` | `[0, 0, 10465]` | `[0, 0, 5438]` | `[0, 0, 10217]` | 26,120 |
| Fold 2 | `[6793, 254, 5193]` | `[704, 119, 639]` | `[6440, 212, 5766]` | `[0, 0, 12240]` | `[0, 0, 1462]` | `[0, 0, 12418]` | 26,120 |
| Fold 3 | `[7449, 373, 4773]` | `[589, 219, 557]` | `[7213, 233, 4714]` | `[0, 0, 12595]` | `[0, 0, 1365]` | `[0, 0, 12160]` | 26,120 |
| Fold 4 | `[8832, 34, 4240]` | `[518, 19, 300]` | `[8104, 32, 4041]` | `[0, 0, 13106]` | `[0, 0, 837]` | `[0, 0, 12177]` | 26,120 |
| Fold 5 | `[9487, 53, 3517]` | `[469, 49, 210]` | `[8881, 46, 3408]` | `[13057, 0, 0]` | `[728, 0, 0]` | `[12335, 0, 0]` | 26,120 |

#### Pooled 3x3 Confusion Matrices (B4 and B0)
```
B4 POOLED CONFUSION MATRIX (Total = 130,600, BA = 0.428589):
True SL  (61,463):    36315 (SL)     3852 (EXP)    21296 (TP)  |  Recall: 0.590843
True EXP (9,830):     3580 (SL)     3149 (EXP)     3101 (TP)  |  Recall: 0.320346
True TP  (59,307):    33716 (SL)     3376 (EXP)    22215 (TP)  |  Recall: 0.374576

B0 POOLED CONFUSION MATRIX (Total = 130,600, BA = 0.334817):
True SL  (61,463):    13057 (SL)        0 (EXP)    48406 (TP)  |  Recall: 0.212437
True EXP (9,830):      728 (SL)        0 (EXP)     9102 (TP)  |  Recall: 0.000000
True TP  (59,307):    12335 (SL)        0 (EXP)    46972 (TP)  |  Recall: 0.792014
```

---

### 5.5 ADAUSDT Forensic Audit
- **Total OOF Candles:** 130,483
- **Historical Benchmark Fold-Mean BA:** 0.4490
- **Phase 5.3.3.5 Reconstructed Fold-Mean BA:** 0.448953 (Exact Reconciliation)
- **Pooled OOF B4 Balanced Accuracy:** 0.468513
- **Pooled OOF B0 Balanced Accuracy:** 0.333333
- **Discrepancy (B4 Pooled - B4 Fold-Mean):** +0.019560
- **Fold Support Weights $w_k(\text{SL})$:** [0.1824, 0.1949, 0.192, 0.2163, 0.2145]
- **Fold Support Weights $w_k(\text{EXP})$:** [0.2843, 0.2124, 0.2415, 0.1175, 0.1444]
- **Fold Support Weights $w_k(\text{TP})$:** [0.189, 0.201, 0.1939, 0.2118, 0.2043]

#### Per-Fold Support, Recall, and Balanced Accuracy Table
| Fold | Test Samples | Support [SL, EXP, TP] | B4 Recall [SL, EXP, TP] | B4 Fold BA | Historical BA | B0 Majority Class | B0 Fold BA |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | 26,096 | [10,385, 5,405, 10,306] | [0.3130, 0.7717, 0.4549] | 0.513207 | 0.5132 | +1 | 0.333333 |
| Fold 2 | 26,096 | [11,097, 4,037, 10,962] | [0.2240, 0.8246, 0.2217] | 0.423441 | 0.4234 | +1 | 0.333333 |
| Fold 3 | 26,096 | [10,934, 4,590, 10,572] | [0.3219, 0.7688, 0.3212] | 0.470668 | 0.4707 | +1 | 0.333333 |
| Fold 4 | 26,096 | [12,317, 2,233, 11,546] | [0.4532, 0.3547, 0.4470] | 0.418290 | 0.4183 | +1 | 0.333333 |
| Fold 5 | 26,099 | [12,215, 2,744, 11,140] | [0.4029, 0.4235, 0.4311] | 0.419159 | 0.4192 | +1 | 0.333333 |

#### Per-Fold 3x3 Confusion Matrices (Rows = True [SL, EXP, TP], Cols = Predicted [SL, EXP, TP])
| Fold | B4 Row SL (-1) | B4 Row EXP (0) | B4 Row TP (+1) | B0 Row SL (-1) | B0 Row EXP (0) | B0 Row TP (+1) | Matrix Sum |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | `[3251, 4089, 3045]` | `[547, 4171, 687]` | `[1942, 3676, 4688]` | `[0, 0, 10385]` | `[0, 0, 5405]` | `[0, 0, 10306]` | 26,096 |
| Fold 2 | `[2486, 6436, 2175]` | `[374, 3329, 334]` | `[2328, 6204, 2430]` | `[0, 0, 11097]` | `[0, 0, 4037]` | `[0, 0, 10962]` | 26,096 |
| Fold 3 | `[3520, 4190, 3224]` | `[599, 3529, 462]` | `[3051, 4125, 3396]` | `[0, 0, 10934]` | `[0, 0, 4590]` | `[0, 0, 10572]` | 26,096 |
| Fold 4 | `[5582, 1868, 4867]` | `[767, 792, 674]` | `[4651, 1734, 5161]` | `[0, 0, 12317]` | `[0, 0, 2233]` | `[0, 0, 11546]` | 26,096 |
| Fold 5 | `[4922, 2691, 4602]` | `[808, 1162, 774]` | `[3934, 2404, 4802]` | `[0, 0, 12215]` | `[0, 0, 2744]` | `[0, 0, 11140]` | 26,099 |

#### Pooled 3x3 Confusion Matrices (B4 and B0)
```
B4 POOLED CONFUSION MATRIX (Total = 130,483, BA = 0.468513):
True SL  (56,948):    19761 (SL)    19274 (EXP)    17913 (TP)  |  Recall: 0.347001
True EXP (19,009):     3095 (SL)    12983 (EXP)     2931 (TP)  |  Recall: 0.682992
True TP  (54,526):    15906 (SL)    18143 (EXP)    20477 (TP)  |  Recall: 0.375546

B0 POOLED CONFUSION MATRIX (Total = 130,483, BA = 0.333333):
True SL  (56,948):        0 (SL)        0 (EXP)    56948 (TP)  |  Recall: 0.000000
True EXP (19,009):        0 (SL)        0 (EXP)    19009 (TP)  |  Recall: 0.000000
True TP  (54,526):        0 (SL)        0 (EXP)    54526 (TP)  |  Recall: 1.000000
```

---

### 5.6 SOLUSDT Forensic Audit
- **Total OOF Candles:** 130,808
- **Historical Benchmark Fold-Mean BA:** 0.3878
- **Phase 5.3.3.5 Reconstructed Fold-Mean BA:** 0.387837 (Exact Reconciliation)
- **Pooled OOF B4 Balanced Accuracy:** 0.439965
- **Pooled OOF B0 Balanced Accuracy:** 0.333333
- **Discrepancy (B4 Pooled - B4 Fold-Mean):** +0.052128
- **Fold Support Weights $w_k(\text{SL})$:** [0.184, 0.2018, 0.201, 0.2073, 0.2059]
- **Fold Support Weights $w_k(\text{EXP})$:** [0.4946, 0.1366, 0.1322, 0.1144, 0.1222]
- **Fold Support Weights $w_k(\text{TP})$:** [0.1815, 0.2056, 0.2069, 0.2027, 0.2032]

#### Per-Fold Support, Recall, and Balanced Accuracy Table
| Fold | Test Samples | Support [SL, EXP, TP] | B4 Recall [SL, EXP, TP] | B4 Fold BA | Historical BA | B0 Majority Class | B0 Fold BA |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | 26,161 | [11,397, 3,577, 11,187] | [0.2558, 0.6273, 0.4579] | 0.447018 | 0.4470 | -1 | 0.333333 |
| Fold 2 | 26,161 | [12,501, 988, 12,672] | [0.2824, 0.0577, 0.7126] | 0.350888 | 0.3509 | -1 | 0.333333 |
| Fold 3 | 26,161 | [12,451, 956, 12,754] | [0.4127, 0.1506, 0.6078] | 0.390392 | 0.3904 | -1 | 0.333333 |
| Fold 4 | 26,161 | [12,840, 827, 12,494] | [0.3847, 0.0834, 0.6185] | 0.362209 | 0.3622 | -1 | 0.333333 |
| Fold 5 | 26,164 | [12,756, 884, 12,524] | [0.4228, 0.1652, 0.5781] | 0.388677 | 0.3887 | -1 | 0.333333 |

#### Per-Fold 3x3 Confusion Matrices (Rows = True [SL, EXP, TP], Cols = Predicted [SL, EXP, TP])
| Fold | B4 Row SL (-1) | B4 Row EXP (0) | B4 Row TP (+1) | B0 Row SL (-1) | B0 Row EXP (0) | B0 Row TP (+1) | Matrix Sum |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | `[2915, 3521, 4961]` | `[588, 2244, 745]` | `[2449, 3615, 5123]` | `[11397, 0, 0]` | `[3577, 0, 0]` | `[11187, 0, 0]` | 26,161 |
| Fold 2 | `[3530, 33, 8938]` | `[408, 57, 523]` | `[3605, 37, 9030]` | `[12501, 0, 0]` | `[988, 0, 0]` | `[12672, 0, 0]` | 26,161 |
| Fold 3 | `[5139, 99, 7213]` | `[353, 144, 459]` | `[4842, 160, 7752]` | `[12451, 0, 0]` | `[956, 0, 0]` | `[12754, 0, 0]` | 26,161 |
| Fold 4 | `[4940, 95, 7805]` | `[305, 69, 453]` | `[4684, 83, 7727]` | `[12840, 0, 0]` | `[827, 0, 0]` | `[12494, 0, 0]` | 26,161 |
| Fold 5 | `[5393, 208, 7155]` | `[377, 146, 361]` | `[5121, 163, 7240]` | `[12756, 0, 0]` | `[884, 0, 0]` | `[12524, 0, 0]` | 26,164 |

#### Pooled 3x3 Confusion Matrices (B4 and B0)
```
B4 POOLED CONFUSION MATRIX (Total = 130,808, BA = 0.439965):
True SL  (61,945):    21917 (SL)     3956 (EXP)    36072 (TP)  |  Recall: 0.353814
True EXP (7,232):     2031 (SL)     2660 (EXP)     2541 (TP)  |  Recall: 0.367810
True TP  (61,631):    20701 (SL)     4058 (EXP)    36872 (TP)  |  Recall: 0.598270

B0 POOLED CONFUSION MATRIX (Total = 130,808, BA = 0.333333):
True SL  (61,945):    61945 (SL)        0 (EXP)        0 (TP)  |  Recall: 1.000000
True EXP (7,232):     7232 (SL)        0 (EXP)        0 (TP)  |  Recall: 0.000000
True TP  (61,631):    61631 (SL)        0 (EXP)        0 (TP)  |  Recall: 0.000000
```

---

### 5.7 AVAXUSDT Forensic Audit
- **Total OOF Candles:** 130,818
- **Historical Benchmark Fold-Mean BA:** 0.4145
- **Phase 5.3.3.5 Reconstructed Fold-Mean BA:** 0.414487 (Exact Reconciliation)
- **Pooled OOF B4 Balanced Accuracy:** 0.452262
- **Pooled OOF B0 Balanced Accuracy:** 0.333333
- **Discrepancy (B4 Pooled - B4 Fold-Mean):** +0.037775
- **Fold Support Weights $w_k(\text{SL})$:** [0.2015, 0.1646, 0.1864, 0.2262, 0.2212]
- **Fold Support Weights $w_k(\text{EXP})$:** [0.1953, 0.318, 0.2376, 0.1094, 0.1398]
- **Fold Support Weights $w_k(\text{TP})$:** [0.2011, 0.1687, 0.1923, 0.2251, 0.2128]

#### Per-Fold Support, Recall, and Balanced Accuracy Table
| Fold | Test Samples | Support [SL, EXP, TP] | B4 Recall [SL, EXP, TP] | B4 Fold BA | Historical BA | B0 Majority Class | B0 Fold BA |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | 26,163 | [10,381, 5,634, 10,148] | [0.3997, 0.5398, 0.4094] | 0.449624 | 0.4496 | -1 | 0.333333 |
| Fold 2 | 26,163 | [8,478, 9,174, 8,511] | [0.1906, 0.8016, 0.1665] | 0.386238 | 0.3862 | -1 | 0.333333 |
| Fold 3 | 26,163 | [9,603, 6,855, 9,705] | [0.3802, 0.7218, 0.3401] | 0.480712 | 0.4807 | -1 | 0.333333 |
| Fold 4 | 26,163 | [11,650, 3,156, 11,357] | [0.5647, 0.1470, 0.3918] | 0.367857 | 0.3679 | -1 | 0.333333 |
| Fold 5 | 26,166 | [11,394, 4,033, 10,739] | [0.5133, 0.2423, 0.4084] | 0.388003 | 0.3880 | -1 | 0.333333 |

#### Per-Fold 3x3 Confusion Matrices (Rows = True [SL, EXP, TP], Cols = Predicted [SL, EXP, TP])
| Fold | B4 Row SL (-1) | B4 Row EXP (0) | B4 Row TP (+1) | B0 Row SL (-1) | B0 Row EXP (0) | B0 Row TP (+1) | Matrix Sum |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | `[4149, 2850, 3382]` | `[1302, 3041, 1291]` | `[3151, 2842, 4155]` | `[10381, 0, 0]` | `[5634, 0, 0]` | `[10148, 0, 0]` | 26,163 |
| Fold 2 | `[1616, 5584, 1278]` | `[1080, 7354, 740]` | `[1433, 5661, 1417]` | `[8478, 0, 0]` | `[9174, 0, 0]` | `[8511, 0, 0]` | 26,163 |
| Fold 3 | `[3651, 2795, 3157]` | `[1023, 4948, 884]` | `[3411, 2993, 3301]` | `[9603, 0, 0]` | `[6855, 0, 0]` | `[9705, 0, 0]` | 26,163 |
| Fold 4 | `[6579, 1035, 4036]` | `[1625, 464, 1067]` | `[5817, 1090, 4450]` | `[11650, 0, 0]` | `[3156, 0, 0]` | `[11357, 0, 0]` | 26,163 |
| Fold 5 | `[5849, 1423, 4122]` | `[1739, 977, 1317]` | `[5016, 1337, 4386]` | `[11394, 0, 0]` | `[4033, 0, 0]` | `[10739, 0, 0]` | 26,166 |

#### Pooled 3x3 Confusion Matrices (B4 and B0)
```
B4 POOLED CONFUSION MATRIX (Total = 130,818, BA = 0.452262):
True SL  (51,506):    21844 (SL)    13687 (EXP)    15975 (TP)  |  Recall: 0.424106
True EXP (28,852):     6769 (SL)    16784 (EXP)     5299 (TP)  |  Recall: 0.581727
True TP  (50,460):    18828 (SL)    13923 (EXP)    17709 (TP)  |  Recall: 0.350951

B0 POOLED CONFUSION MATRIX (Total = 130,818, BA = 0.333333):
True SL  (51,506):    51506 (SL)        0 (EXP)        0 (TP)  |  Recall: 1.000000
True EXP (28,852):    28852 (SL)        0 (EXP)        0 (TP)  |  Recall: 0.000000
True TP  (50,460):    50460 (SL)        0 (EXP)        0 (TP)  |  Recall: 0.000000
```

---

### 5.8 LINKUSDT Forensic Audit
- **Total OOF Candles:** 130,777
- **Historical Benchmark Fold-Mean BA:** 0.4067
- **Phase 5.3.3.5 Reconstructed Fold-Mean BA:** 0.406753 (Exact Reconciliation)
- **Pooled OOF B4 Balanced Accuracy:** 0.498942
- **Pooled OOF B0 Balanced Accuracy:** 0.333333
- **Discrepancy (B4 Pooled - B4 Fold-Mean):** +0.092189
- **Fold Support Weights $w_k(\text{SL})$:** [0.1553, 0.1332, 0.2169, 0.2516, 0.243]
- **Fold Support Weights $w_k(\text{EXP})$:** [0.3187, 0.3779, 0.1485, 0.0591, 0.0958]
- **Fold Support Weights $w_k(\text{TP})$:** [0.1572, 0.1357, 0.2211, 0.2523, 0.2338]

#### Per-Fold Support, Recall, and Balanced Accuracy Table
| Fold | Test Samples | Support [SL, EXP, TP] | B4 Recall [SL, EXP, TP] | B4 Fold BA | Historical BA | B0 Majority Class | B0 Fold BA |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | 26,155 | [7,432, 11,226, 7,497] | [0.1566, 0.8210, 0.2110] | 0.396226 | 0.3962 | -1 | 0.333333 |
| Fold 2 | 26,155 | [6,376, 13,309, 6,470] | [0.1526, 0.8987, 0.1923] | 0.414530 | 0.4145 | -1 | 0.333333 |
| Fold 3 | 26,155 | [10,382, 5,230, 10,543] | [0.3718, 0.6562, 0.4445] | 0.490826 | 0.4908 | -1 | 0.333333 |
| Fold 4 | 26,155 | [12,041, 2,083, 12,031] | [0.5335, 0.0125, 0.5092] | 0.351726 | 0.3517 | -1 | 0.333333 |
| Fold 5 | 26,157 | [11,631, 3,374, 11,152] | [0.4806, 0.1405, 0.5203] | 0.380455 | 0.3805 | -1 | 0.333333 |

#### Per-Fold 3x3 Confusion Matrices (Rows = True [SL, EXP, TP], Cols = Predicted [SL, EXP, TP])
| Fold | B4 Row SL (-1) | B4 Row EXP (0) | B4 Row TP (+1) | B0 Row SL (-1) | B0 Row EXP (0) | B0 Row TP (+1) | Matrix Sum |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | `[1164, 5002, 1266]` | `[945, 9217, 1064]` | `[886, 5029, 1582]` | `[7432, 0, 0]` | `[11226, 0, 0]` | `[7497, 0, 0]` | 26,155 |
| Fold 2 | `[973, 4318, 1085]` | `[739, 11961, 609]` | `[1002, 4224, 1244]` | `[6376, 0, 0]` | `[13309, 0, 0]` | `[6470, 0, 0]` | 26,155 |
| Fold 3 | `[3860, 2238, 4284]` | `[809, 3432, 989]` | `[3507, 2350, 4686]` | `[10382, 0, 0]` | `[5230, 0, 0]` | `[10543, 0, 0]` | 26,155 |
| Fold 4 | `[6424, 90, 5527]` | `[1108, 26, 949]` | `[5772, 133, 6126]` | `[12041, 0, 0]` | `[2083, 0, 0]` | `[12031, 0, 0]` | 26,155 |
| Fold 5 | `[5590, 724, 5317]` | `[1271, 474, 1629]` | `[4679, 671, 5802]` | `[11631, 0, 0]` | `[3374, 0, 0]` | `[11152, 0, 0]` | 26,157 |

#### Pooled 3x3 Confusion Matrices (B4 and B0)
```
B4 POOLED CONFUSION MATRIX (Total = 130,777, BA = 0.498942):
True SL  (47,862):    18011 (SL)    12372 (EXP)    17479 (TP)  |  Recall: 0.376311
True EXP (35,222):     4872 (SL)    25110 (EXP)     5240 (TP)  |  Recall: 0.712907
True TP  (47,693):    15846 (SL)    12407 (EXP)    19440 (TP)  |  Recall: 0.407607

B0 POOLED CONFUSION MATRIX (Total = 130,777, BA = 0.333333):
True SL  (47,862):    47862 (SL)        0 (EXP)        0 (TP)  |  Recall: 1.000000
True EXP (35,222):    35222 (SL)        0 (EXP)        0 (TP)  |  Recall: 0.000000
True TP  (47,693):    47693 (SL)        0 (EXP)        0 (TP)  |  Recall: 0.000000
```

---

### 5.9 DOGEUSDT Forensic Audit
- **Total OOF Candles:** 130,648
- **Historical Benchmark Fold-Mean BA:** 0.3960
- **Phase 5.3.3.5 Reconstructed Fold-Mean BA:** 0.395983 (Exact Reconciliation)
- **Pooled OOF B4 Balanced Accuracy:** 0.489942
- **Pooled OOF B0 Balanced Accuracy:** 0.335793
- **Discrepancy (B4 Pooled - B4 Fold-Mean):** +0.093959
- **Fold Support Weights $w_k(\text{SL})$:** [0.1388, 0.2066, 0.21, 0.2215, 0.2231]
- **Fold Support Weights $w_k(\text{EXP})$:** [0.6294, 0.1263, 0.1177, 0.0658, 0.0608]
- **Fold Support Weights $w_k(\text{TP})$:** [0.1412, 0.2141, 0.2131, 0.2159, 0.2157]

#### Per-Fold Support, Recall, and Balanced Accuracy Table
| Fold | Test Samples | Support [SL, EXP, TP] | B4 Recall [SL, EXP, TP] | B4 Fold BA | Historical BA | B0 Majority Class | B0 Fold BA |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | 26,129 | [8,107, 10,088, 7,934] | [0.1701, 0.7485, 0.2238] | 0.380820 | 0.3808 | +1 | 0.333333 |
| Fold 2 | 26,129 | [12,070, 2,025, 12,034] | [0.4608, 0.2923, 0.4961] | 0.416417 | 0.4164 | +1 | 0.333333 |
| Fold 3 | 26,129 | [12,264, 1,886, 11,979] | [0.5082, 0.4152, 0.4348] | 0.452693 | 0.4527 | +1 | 0.333333 |
| Fold 4 | 26,129 | [12,938, 1,055, 12,136] | [0.6140, 0.0455, 0.4071] | 0.355546 | 0.3555 | +1 | 0.333333 |
| Fold 5 | 26,132 | [13,032, 974, 12,126] | [0.6195, 0.1088, 0.3950] | 0.374441 | 0.3744 | -1 | 0.333333 |

#### Per-Fold 3x3 Confusion Matrices (Rows = True [SL, EXP, TP], Cols = Predicted [SL, EXP, TP])
| Fold | B4 Row SL (-1) | B4 Row EXP (0) | B4 Row TP (+1) | B0 Row SL (-1) | B0 Row EXP (0) | B0 Row TP (+1) | Matrix Sum |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | `[1379, 5160, 1568]` | `[1382, 7551, 1155]` | `[1302, 4856, 1776]` | `[0, 0, 8107]` | `[0, 0, 10088]` | `[0, 0, 7934]` | 26,129 |
| Fold 2 | `[5562, 763, 5745]` | `[691, 592, 742]` | `[5269, 795, 5970]` | `[0, 0, 12070]` | `[0, 0, 2025]` | `[0, 0, 12034]` | 26,129 |
| Fold 3 | `[6232, 922, 5110]` | `[619, 783, 484]` | `[5928, 843, 5208]` | `[0, 0, 12264]` | `[0, 0, 1886]` | `[0, 0, 11979]` | 26,129 |
| Fold 4 | `[7944, 29, 4965]` | `[626, 48, 381]` | `[7170, 25, 4941]` | `[0, 0, 12938]` | `[0, 0, 1055]` | `[0, 0, 12136]` | 26,129 |
| Fold 5 | `[8073, 53, 4906]` | `[525, 106, 343]` | `[7281, 55, 4790]` | `[13032, 0, 0]` | `[974, 0, 0]` | `[12126, 0, 0]` | 26,132 |

#### Pooled 3x3 Confusion Matrices (B4 and B0)
```
B4 POOLED CONFUSION MATRIX (Total = 130,648, BA = 0.489942):
True SL  (58,411):    29190 (SL)     6927 (EXP)    22294 (TP)  |  Recall: 0.499735
True EXP (16,028):     3843 (SL)     9080 (EXP)     3105 (TP)  |  Recall: 0.566509
True TP  (56,209):    26950 (SL)     6574 (EXP)    22685 (TP)  |  Recall: 0.403583

B0 POOLED CONFUSION MATRIX (Total = 130,648, BA = 0.335793):
True SL  (58,411):    13032 (SL)        0 (EXP)    45379 (TP)  |  Recall: 0.223109
True EXP (16,028):      974 (SL)        0 (EXP)    15054 (TP)  |  Recall: 0.000000
True TP  (56,209):    12126 (SL)        0 (EXP)    44083 (TP)  |  Recall: 0.784269
```

---

### 5.10 LTCUSDT Forensic Audit
- **Total OOF Candles:** 130,463
- **Historical Benchmark Fold-Mean BA:** 0.4355
- **Phase 5.3.3.5 Reconstructed Fold-Mean BA:** 0.435514 (Exact Reconciliation)
- **Pooled OOF B4 Balanced Accuracy:** 0.485102
- **Pooled OOF B0 Balanced Accuracy:** 0.333333
- **Discrepancy (B4 Pooled - B4 Fold-Mean):** +0.049589
- **Fold Support Weights $w_k(\text{SL})$:** [0.184, 0.168, 0.1675, 0.2466, 0.2339]
- **Fold Support Weights $w_k(\text{EXP})$:** [0.2424, 0.2832, 0.281, 0.0732, 0.1201]
- **Fold Support Weights $w_k(\text{TP})$:** [0.1872, 0.1756, 0.1775, 0.2393, 0.2204]

#### Per-Fold Support, Recall, and Balanced Accuracy Table
| Fold | Test Samples | Support [SL, EXP, TP] | B4 Recall [SL, EXP, TP] | B4 Fold BA | Historical BA | B0 Majority Class | B0 Fold BA |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | 26,092 | [8,895, 8,002, 9,195] | [0.4044, 0.5457, 0.4598] | 0.469979 | 0.4700 | +1 | 0.333333 |
| Fold 2 | 26,092 | [8,120, 9,346, 8,626] | [0.1931, 0.8227, 0.2275] | 0.414420 | 0.4144 | +1 | 0.333333 |
| Fold 3 | 26,092 | [8,098, 9,276, 8,718] | [0.3676, 0.8008, 0.3837] | 0.517362 | 0.5174 | +1 | 0.333333 |
| Fold 4 | 26,092 | [11,922, 2,417, 11,753] | [0.5210, 0.0869, 0.5180] | 0.375283 | 0.3753 | +1 | 0.333333 |
| Fold 5 | 26,095 | [11,307, 3,965, 10,823] | [0.4584, 0.2729, 0.4703] | 0.400524 | 0.4005 | +1 | 0.333333 |

#### Per-Fold 3x3 Confusion Matrices (Rows = True [SL, EXP, TP], Cols = Predicted [SL, EXP, TP])
| Fold | B4 Row SL (-1) | B4 Row EXP (0) | B4 Row TP (+1) | B0 Row SL (-1) | B0 Row EXP (0) | B0 Row TP (+1) | Matrix Sum |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | `[3597, 2589, 2709]` | `[1810, 4367, 1825]` | `[2457, 2510, 4228]` | `[0, 0, 8895]` | `[0, 0, 8002]` | `[0, 0, 9195]` | 26,092 |
| Fold 2 | `[1568, 4874, 1678]` | `[774, 7689, 883]` | `[1627, 5037, 1962]` | `[0, 0, 8120]` | `[0, 0, 9346]` | `[0, 0, 8626]` | 26,092 |
| Fold 3 | `[2977, 2168, 2953]` | `[805, 7428, 1043]` | `[2907, 2466, 3345]` | `[0, 0, 8098]` | `[0, 0, 9276]` | `[0, 0, 8718]` | 26,092 |
| Fold 4 | `[6211, 209, 5502]` | `[1207, 210, 1000]` | `[5448, 217, 6088]` | `[0, 0, 11922]` | `[0, 0, 2417]` | `[0, 0, 11753]` | 26,092 |
| Fold 5 | `[5183, 1751, 4373]` | `[1368, 1082, 1515]` | `[4226, 1507, 5090]` | `[0, 0, 11307]` | `[0, 0, 3965]` | `[0, 0, 10823]` | 26,095 |

#### Pooled 3x3 Confusion Matrices (B4 and B0)
```
B4 POOLED CONFUSION MATRIX (Total = 130,463, BA = 0.485102):
True SL  (48,342):    19536 (SL)    11591 (EXP)    17215 (TP)  |  Recall: 0.404121
True EXP (33,006):     5964 (SL)    20776 (EXP)     6266 (TP)  |  Recall: 0.629461
True TP  (49,115):    16665 (SL)    11737 (EXP)    20713 (TP)  |  Recall: 0.421725

B0 POOLED CONFUSION MATRIX (Total = 130,463, BA = 0.333333):
True SL  (48,342):        0 (SL)        0 (EXP)    48342 (TP)  |  Recall: 0.000000
True EXP (33,006):        0 (SL)        0 (EXP)    33006 (TP)  |  Recall: 0.000000
True TP  (49,115):        0 (SL)        0 (EXP)    49115 (TP)  |  Recall: 1.000000
```

---

### 5.11 XMRUSDT Forensic Audit
- **Total OOF Candles:** 15,252
- **Historical Benchmark Fold-Mean BA:** 0.3816
- **Phase 5.3.3.5 Reconstructed Fold-Mean BA:** 0.381554 (Exact Reconciliation)
- **Pooled OOF B4 Balanced Accuracy:** 0.386760
- **Pooled OOF B0 Balanced Accuracy:** 0.333333
- **Discrepancy (B4 Pooled - B4 Fold-Mean):** +0.005206
- **Fold Support Weights $w_k(\text{SL})$:** [0.2051, 0.2107, 0.2036, 0.1976, 0.183]
- **Fold Support Weights $w_k(\text{EXP})$:** [0.1509, 0.152, 0.1937, 0.2547, 0.2488]
- **Fold Support Weights $w_k(\text{TP})$:** [0.2084, 0.2029, 0.1983, 0.1875, 0.2029]

#### Per-Fold Support, Recall, and Balanced Accuracy Table
| Fold | Test Samples | Support [SL, EXP, TP] | B4 Recall [SL, EXP, TP] | B4 Fold BA | Historical BA | B0 Majority Class | B0 Fold BA |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | 3,050 | [1,323, 282, 1,445] | [0.4573, 0.3298, 0.4491] | 0.412072 | 0.4121 | +1 | 0.333333 |
| Fold 2 | 3,050 | [1,359, 284, 1,407] | [0.4761, 0.1197, 0.4684] | 0.354725 | 0.3547 | +1 | 0.333333 |
| Fold 3 | 3,050 | [1,313, 362, 1,375] | [0.4806, 0.2238, 0.4422] | 0.382173 | 0.3822 | +1 | 0.333333 |
| Fold 4 | 3,050 | [1,274, 476, 1,300] | [0.3736, 0.3319, 0.4562] | 0.387238 | 0.3872 | +1 | 0.333333 |
| Fold 5 | 3,052 | [1,180, 465, 1,407] | [0.3771, 0.3957, 0.3419] | 0.371560 | 0.3716 | +1 | 0.333333 |

#### Per-Fold 3x3 Confusion Matrices (Rows = True [SL, EXP, TP], Cols = Predicted [SL, EXP, TP])
| Fold | B4 Row SL (-1) | B4 Row EXP (0) | B4 Row TP (+1) | B0 Row SL (-1) | B0 Row EXP (0) | B0 Row TP (+1) | Matrix Sum |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Fold 1 | `[605, 156, 562]` | `[88, 93, 101]` | `[597, 199, 649]` | `[0, 0, 1323]` | `[0, 0, 282]` | `[0, 0, 1445]` | 3,050 |
| Fold 2 | `[647, 97, 615]` | `[119, 34, 131]` | `[670, 78, 659]` | `[0, 0, 1359]` | `[0, 0, 284]` | `[0, 0, 1407]` | 3,050 |
| Fold 3 | `[631, 153, 529]` | `[170, 81, 111]` | `[643, 124, 608]` | `[0, 0, 1313]` | `[0, 0, 362]` | `[0, 0, 1375]` | 3,050 |
| Fold 4 | `[476, 212, 586]` | `[114, 158, 204]` | `[446, 261, 593]` | `[0, 0, 1274]` | `[0, 0, 476]` | `[0, 0, 1300]` | 3,050 |
| Fold 5 | `[445, 398, 337]` | `[109, 184, 172]` | `[551, 375, 481]` | `[0, 0, 1180]` | `[0, 0, 465]` | `[0, 0, 1407]` | 3,052 |

#### Pooled 3x3 Confusion Matrices (B4 and B0)
```
B4 POOLED CONFUSION MATRIX (Total = 15,252, BA = 0.386760):
True SL  (6,449):     2804 (SL)     1016 (EXP)     2629 (TP)  |  Recall: 0.434796
True EXP (1,869):      600 (SL)      550 (EXP)      719 (TP)  |  Recall: 0.294275
True TP  (6,934):     2907 (SL)     1037 (EXP)     2990 (TP)  |  Recall: 0.431209

B0 POOLED CONFUSION MATRIX (Total = 15,252, BA = 0.333333):
True SL  (6,449):        0 (SL)        0 (EXP)     6449 (TP)  |  Recall: 0.000000
True EXP (1,869):        0 (SL)        0 (EXP)     1869 (TP)  |  Recall: 0.000000
True TP  (6,934):        0 (SL)        0 (EXP)     6934 (TP)  |  Recall: 1.000000
```

---

## 6. Data Provenance & Governance Verification

| Verification Requirement | Mandated Boundary | Audit Finding | Status |
| :--- | :--- | :--- | :---: |
| Model Retraining / Fitting | Zero .fit() calls authorized | No models fitted or modified; predictions frozen from Phase 5.3.2 | **COMPLIANT** |
| Evaluation Samples Evaluated | Exactly 1,322,108 OOF observations | Exactly 1,322,108 candles processed across 11 instruments | **COMPLIANT** |
| Prospective Holdout Boundary | 2026-11-01 00:00:00 to 2027-04-30 23:59:59 UTC | 0 prospective holdout candles accessed or inspected | **COMPLIANT** |
| Temporal Boundary Compliance | Historical validation ended 2026-04-30 23:59:59 UTC | Max timestamp across all folds is 1777593599999 ms | **COMPLIANT** |
| Historical Benchmark Reproduction | Exact match to historical fold-mean BA | Reconstructed fold-mean BA matches historical catalog to 0.0000 | **COMPLIANT** |

---

**Audit Report Prepared By:** Independent Senior Quantitative Research Auditor  
**Timestamp:** 2026-11-01 22:00:00 UTC  
**Artifact Digest:** SHA-256 manifest recorded in `artifacts/phase_5_3_3_5/final_audit_manifest.json`  