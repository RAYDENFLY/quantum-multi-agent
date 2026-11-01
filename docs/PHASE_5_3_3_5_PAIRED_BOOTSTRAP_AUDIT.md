# QUANTUM PHASE 5.3.3.5: PAIRED B4-VS-B0 STATISTICAL BOOTSTRAP AUDIT

**Role:** Independent Senior Quantitative Research Auditor and Financial ML Validation Specialist  
**System:** QUANTUM 11-Specialist Cryptocurrency Perpetual Futures ML Trading Research System  
**Repository:** [quantum-multi-agent](file:///d:/quantum-multi-agent)  
**Phase:** Phase 5.3.3.5 (Audit Deliverable B)  
**Audit Scope:** Paired B4 vs B0 Out-of-Fold Statistical Testing, Empirical Moving Block Bootstrap, Hall & Wilson Centering, and Holm-Bonferroni Multiplicity Correction  

---

## 1. Executive Summary

This audit delivers an independent, empirical statistical evaluation of Specialist Model B4 (LightGBM) against Baseline Model B0 (Majority Class Classifier) across all 11 QUANTUM trading instruments.

Key statistical findings:
1. **Paired Benchmark Verification:** Every evaluation is strictly paired on identical timestamps from the 1,322,108 out-of-fold (OOF) candles. Baseline B0 is evaluated on its actual empirical predictions rather than assuming a theoretical 1/3 benchmark. For 7 instruments with stationary fold majorities, B0 pooled Balanced Accuracy is identically 0.333333; for 4 instruments with majority class shifts between folds, B0 pooled Balanced Accuracy ranges from 0.330614 to 0.335793.
2. **Substantial Observed Lift:** Specialist Model B4 achieves statistically and practically significant paired Balanced Accuracy improvements over Baseline B0 across all 11 instruments, ranging from **+0.053427 (+16.03% relative improvement)** in XMRUSDT to **+0.165609 (+49.68% relative improvement)** in LINKUSDT.
3. **Empirical Moving Block Bootstrap:** Resampling $B = 10,000$ contiguous blocks of length $b \in \{12, 24, 48, 96\}$ bars under the Hall & Wilson (1991) centered null distribution produced **zero exceedances** across all 44 test configurations. In accordance with finite-sample Monte Carlo standards, every comparison achieves an exact upper-bound p-value of $p < \frac{1}{B+1} = \mathbf{p < 0.000100}$.
4. **Holm-Bonferroni Family-Wise Error Control:** Applying the Holm-Bonferroni step-down correction across the family of 11 primary comparisons ($b=24$), the null hypothesis $H_0: \Delta\text{BA} \le 0$ is decisively rejected for **all 11 instruments** at family-wise significance level $\alpha = 0.05$ (maximum adjusted p-value $p_{\text{adj}} \le 0.001100$).
5. **Confidence Interval Robustness:** All 95% bootstrap percentile confidence interval lower bounds are strictly positive across all block lengths, confirming robustness against temporal autocorrelation up to 8-hour dependencies.

---

## 2. Paired Benchmark Methodology & Ground Rules

### 2.1 The Paired Difference Metric
For each specialist instrument, the evaluation vector consists of $N$ identical timestamps $t_1, t_2, \dots, t_N$ within the out-of-fold validation set:
- True ground truth label: $y_t \in \{-1, 0, 1\}$
- Specialist Model B4 prediction: $\hat{y}_{t, B4} \in \{-1, 0, 1\}$
- Baseline Model B0 prediction: $\hat{y}_{t, B0} \in \{-1, 0, 1\}$

The primary performance metric is the paired improvement in Balanced Accuracy:
$$\Delta\text{BA} = \text{BA}_{\text{pooled}}(B4) - \text{BA}_{\text{pooled}}(B0)$$

### 2.2 Why Theoretical 1/3 Must Not Be Blindly Substituted
In multi-class evaluation with cross-validation:
- A static majority classifier evaluated on an entire dataset with 3 classes would achieve Balanced Accuracy = $1/3$ ($0.333333$) if one class were predicted globally.
- However, Baseline B0 determines its majority class **independently within each training fold**.
- In 7 instruments (BNBUSDT, ADAUSDT, SOLUSDT, AVAXUSDT, LINKUSDT, LTCUSDT, XMRUSDT), the majority class was identical across all 5 folds, resulting in an exact pooled Balanced Accuracy of $1/3$.
- In 4 instruments (BTCUSDT, ETHUSDT, XRPUSDT, DOGEUSDT), the majority class shifted between folds (e.g. alternating between Take Profit and Stop Loss during bull and bear market regimes). Because the majority class in one training fold does not match the majority class of other test folds, pooled Balanced Accuracy deviates slightly from $1/3$ ($0.330614$ to $0.335793$).
- Rigorous auditing requires evaluating B4 against actual B0 predictions on matched timestamps, as implemented herein.

---

## 3. Master Paired B4-vs-B0 Performance Catalog

The table below reports the complete paired performance metrics across all 11 QUANTUM instruments:

| Specialist Instrument | Total OOF Candles | B4 Pooled BA | B0 Pooled BA | Paired Delta ($\Delta\text{BA}$) | Relative Improvement (%) | Theoretical 1/3 Ref | Delta vs Theoretical 1/3 |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **BTCUSDT** | 130,684 | 0.433187 | 0.332773 | **+0.100414** | **+30.17%** | 0.333333 | +0.099854 |
| **ETHUSDT** | 130,728 | 0.457130 | 0.330614 | **+0.126517** | **+38.27%** | 0.333333 | +0.123797 |
| **BNBUSDT** | 130,847 | 0.466677 | 0.333333 | **+0.133344** | **+40.00%** | 0.333333 | +0.133344 |
| **XRPUSDT** | 130,600 | 0.428589 | 0.334817 | **+0.093771** | **+28.01%** | 0.333333 | +0.095256 |
| **ADAUSDT** | 130,483 | 0.468513 | 0.333333 | **+0.135180** | **+40.55%** | 0.333333 | +0.135180 |
| **SOLUSDT** | 130,808 | 0.439965 | 0.333333 | **+0.106631** | **+31.99%** | 0.333333 | +0.106632 |
| **AVAXUSDT** | 130,818 | 0.452262 | 0.333333 | **+0.118928** | **+35.68%** | 0.333333 | +0.118929 |
| **LINKUSDT** | 130,777 | 0.498942 | 0.333333 | **+0.165608** | **+49.68%** | 0.333333 | +0.165609 |
| **DOGEUSDT** | 130,648 | 0.489942 | 0.335793 | **+0.154149** | **+45.91%** | 0.333333 | +0.156609 |
| **LTCUSDT** | 130,463 | 0.485102 | 0.333333 | **+0.151769** | **+45.53%** | 0.333333 | +0.151769 |
| **XMRUSDT** | 15,252 | 0.386760 | 0.333333 | **+0.053427** | **+16.03%** | 0.333333 | +0.053427 |

---

## 4. Empirical Moving Block Bootstrap Methodology

### 4.1 Temporal Dependence & The Need for Block Resampling
Financial return series and triple-barrier exit outcomes exhibit substantial temporal autocorrelation, volatility clustering, and regime persistence. Standard i.i.d. bootstrap resampling invalidates statistical inference by destroying the serial dependence structure.

The Moving Block Bootstrap (Kunsch, 1989; Liu & Singh, 1992) preserves dependence by resampling contiguous overlapping blocks of length $b$.

### 4.2 Candidate Block Selection Within Contiguous Temporal Segments
To prevent leakage and preserve temporal boundaries:
1. Candidate blocks are drawn **exclusively within contiguous temporal segments**.
2. Blocks are never permitted to straddle cross-validation fold boundaries, purging gaps, or calendar breaks.
3. For an out-of-fold dataset with $N$ observations split into contiguous segments $S_1, \dots, S_m$, each segment of length $L_j \ge b$ contributes $L_j - b + 1$ overlapping candidate blocks.

### 4.3 Hall & Wilson (1991) Centered Null Distribution
To test the one-sided null hypothesis:
$$H_0: \Delta\text{BA} \le 0 \quad \text{versus} \quad H_1: \Delta\text{BA} > 0$$
Under the bootstrap resampling mechanism, each resample $r \in \{1, \dots, B\}$ produces a bootstrap estimate $\Delta\text{BA}^{*(r)}$. Because the resamples are drawn from the empirical data where the true mean is $\Delta\text{BA}_{\text{obs}}$, the bootstrap distribution is centered at $\Delta\text{BA}_{\text{obs}}$, not at the null value 0.

In accordance with the foundational methodology of **Hall & Wilson (1991)**, the bootstrap distribution is centered under the null hypothesis by shifting each realization by the observed sample estimate:
$$\Delta\text{BA}^{*}_{\text{null}, r} = \Delta\text{BA}^{*(r)} - \Delta\text{BA}_{\text{obs}}$$

The empirical one-sided p-value is the proportion of centered null resamples that meet or exceed the observed test statistic:
$$p = \frac{1 + \sum_{r=1}^B \mathbb{I}\left(\Delta\text{BA}^{*}_{\text{null}, r} \ge \Delta\text{BA}_{\text{obs}}\right)}{B + 1}$$

### 4.4 Rigorous Finite-Sample Monte Carlo Upper-Bound Reporting
When evaluating $B = 10,000$ bootstrap replications, if zero null resamples exceed the observed statistic (exceedance count $= 0$):
- Reporting $p = 0.0000$ is mathematically invalid because finite Monte Carlo sampling cannot guarantee an exact zero probability.
- The mathematically rigorous reporting standard is the finite-sample Monte Carlo upper bound:
  $$p < \frac{1}{B + 1} = \frac{1}{10,001} \approx \mathbf{p < 0.000100}$$
- This audit enforces this strict notation across all tables and manifests.

---

## 5. Multiplicity Control: Holm-Bonferroni Step-Down Correction

### 5.1 Multiplicity Correction Specification
When testing $M = 11$ specialist instruments simultaneously, unadjusted p-values risk inflating family-wise Type I error. We apply the **Holm-Bonferroni step-down procedure** at family-wise significance level $\alpha = 0.05$ across the primary benchmark family ($b = 24$ bars / 2 hours).

Algorithm:
1. Sort the $M = 11$ hypotheses in descending order of evidence (ascending order of p-values, or descending order of effect size $\Delta\text{BA}_{\text{obs}}$ when p-values are tied at the bound).
2. For rank $i \in \{1, \dots, M\}$, compare the raw p-value to the step-down alpha threshold:
   $$\alpha_i = \frac{\alpha}{M - i + 1}$$
3. Compute the Holm-Bonferroni adjusted p-value:
   $$p_{\text{adj}, i} = \min\left(1.0, \max_{j \le i} \left[ (M - j + 1) \cdot p_{(j)} \right] \right)$$
4. Reject $H_0$ if $p_{\text{adj}, i} \le \alpha$.

### 5.2 Primary Benchmark Holm-Bonferroni Table ($b = 24$ bars)

| Rank | Specialist Instrument | Observed Paired $\Delta\text{BA}$ | Raw p-Value Bound | Step-Down Alpha Threshold ($\alpha_i$) | Holm-Adjusted p-Value ($p_{\text{adj}}$) | Null Hypothesis ($H_0$) Decision |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | **LINKUSDT** | **+0.165608** | p < 1/10001 (p < 0.000100) | 0.004545 | **0.0011** | **REJECT H0 (SIGNIFICANT)** |
| 2 | **DOGEUSDT** | **+0.154149** | p < 1/10001 (p < 0.000100) | 0.005000 | **0.0010** | **REJECT H0 (SIGNIFICANT)** |
| 3 | **LTCUSDT** | **+0.151769** | p < 1/10001 (p < 0.000100) | 0.005556 | **0.0009** | **REJECT H0 (SIGNIFICANT)** |
| 4 | **ADAUSDT** | **+0.135180** | p < 1/10001 (p < 0.000100) | 0.006250 | **0.0008** | **REJECT H0 (SIGNIFICANT)** |
| 5 | **BNBUSDT** | **+0.133344** | p < 1/10001 (p < 0.000100) | 0.007143 | **0.0007** | **REJECT H0 (SIGNIFICANT)** |
| 6 | **ETHUSDT** | **+0.126517** | p < 1/10001 (p < 0.000100) | 0.008333 | **0.0006** | **REJECT H0 (SIGNIFICANT)** |
| 7 | **AVAXUSDT** | **+0.118928** | p < 1/10001 (p < 0.000100) | 0.010000 | **0.0005** | **REJECT H0 (SIGNIFICANT)** |
| 8 | **SOLUSDT** | **+0.106631** | p < 1/10001 (p < 0.000100) | 0.012500 | **0.0004** | **REJECT H0 (SIGNIFICANT)** |
| 9 | **BTCUSDT** | **+0.100414** | p < 1/10001 (p < 0.000100) | 0.016667 | **0.0003** | **REJECT H0 (SIGNIFICANT)** |
| 10 | **XRPUSDT** | **+0.093771** | p < 1/10001 (p < 0.000100) | 0.025000 | **0.0002** | **REJECT H0 (SIGNIFICANT)** |
| 11 | **XMRUSDT** | **+0.053427** | p < 1/10001 (p < 0.000100) | 0.050000 | **0.0001** | **REJECT H0 (SIGNIFICANT)** |

**Multiplicity Audit Finding:** All 11 specialist models decisively reject the null hypothesis $H_0: \Delta\text{BA} \le 0$ after family-wise error rate control at $\alpha = 0.05$. The maximum adjusted p-value is $p_{\text{adj}} = 0.001100 \le 0.05$.

---

## 6. Sensitivity Analysis Across Block Lengths ($b \in \{12, 24, 48, 96\}$)

To verify that statistical significance is not an artifact of block length selection, we evaluated Moving Block Bootstrap across four distinct temporal dependence scales:
- $b = 12$ bars (1 hour)
- $b = 24$ bars (2 hours, primary benchmark)
- $b = 48$ bars (4 hours)
- $b = 96$ bars (8 hours)

For every block length, $B = 10,000$ resamples were executed with isolated deterministic random seeds.

### 6.1 BTCUSDT Bootstrap Sensitivity
- **Observed Paired Delta ($\Delta\text{BA}$):** +0.100414
- **Relative Improvement:** +30.17%

| Block Length ($b$) | Horizon | Candidate Blocks | Blocks / Resample | Bootstrap Mean $\Delta\text{BA}$ | Bootstrap Std Error | 95% Bootstrap CI | Null Exceedances | p-Value Bound |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 12 bars | 1h | 125,901 | 10,890 | +0.099660 | 0.004275 | [+0.091395, +0.108182] | 0 | p < 1/10001 (p < 0.000100) |
| 24 bars | 2h | 121,091 | 5,445 | +0.099731 | 0.004521 | [+0.090766, +0.108663] | 0 | p < 1/10001 (p < 0.000100) |
| 48 bars | 4h | 112,011 | 2,722 | +0.100409 | 0.004670 | [+0.091263, +0.109500] | 0 | p < 1/10001 (p < 0.000100) |
| 96 bars | 8h | 95,822 | 1,361 | +0.101089 | 0.004744 | [+0.091907, +0.110360] | 0 | p < 1/10001 (p < 0.000100) |

### 6.2 ETHUSDT Bootstrap Sensitivity
- **Observed Paired Delta ($\Delta\text{BA}$):** +0.126517
- **Relative Improvement:** +38.27%

| Block Length ($b$) | Horizon | Candidate Blocks | Blocks / Resample | Bootstrap Mean $\Delta\text{BA}$ | Bootstrap Std Error | 95% Bootstrap CI | Null Exceedances | p-Value Bound |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 12 bars | 1h | 125,437 | 10,894 | +0.125126 | 0.004188 | [+0.116872, +0.133317] | 0 | p < 1/10001 (p < 0.000100) |
| 24 bars | 2h | 120,217 | 5,447 | +0.124895 | 0.004380 | [+0.116260, +0.133468] | 0 | p < 1/10001 (p < 0.000100) |
| 48 bars | 4h | 110,639 | 2,723 | +0.126034 | 0.004448 | [+0.117319, +0.134887] | 0 | p < 1/10001 (p < 0.000100) |
| 96 bars | 8h | 94,238 | 1,361 | +0.127581 | 0.004509 | [+0.118663, +0.136415] | 0 | p < 1/10001 (p < 0.000100) |

### 6.3 BNBUSDT Bootstrap Sensitivity
- **Observed Paired Delta ($\Delta\text{BA}$):** +0.133344
- **Relative Improvement:** +40.00%

| Block Length ($b$) | Horizon | Candidate Blocks | Blocks / Resample | Bootstrap Mean $\Delta\text{BA}$ | Bootstrap Std Error | 95% Bootstrap CI | Null Exceedances | p-Value Bound |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 12 bars | 1h | 127,329 | 10,903 | +0.133017 | 0.003706 | [+0.125573, +0.140269] | 0 | p < 1/10001 (p < 0.000100) |
| 24 bars | 2h | 123,738 | 5,451 | +0.133923 | 0.004199 | [+0.125669, +0.142136] | 0 | p < 1/10001 (p < 0.000100) |
| 48 bars | 4h | 117,039 | 2,725 | +0.136341 | 0.004588 | [+0.127217, +0.145369] | 0 | p < 1/10001 (p < 0.000100) |
| 96 bars | 8h | 104,796 | 1,362 | +0.139596 | 0.005158 | [+0.129209, +0.149649] | 0 | p < 1/10001 (p < 0.000100) |

### 6.4 XRPUSDT Bootstrap Sensitivity
- **Observed Paired Delta ($\Delta\text{BA}$):** +0.093771
- **Relative Improvement:** +28.01%

| Block Length ($b$) | Horizon | Candidate Blocks | Blocks / Resample | Bootstrap Mean $\Delta\text{BA}$ | Bootstrap Std Error | 95% Bootstrap CI | Null Exceedances | p-Value Bound |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 12 bars | 1h | 126,441 | 10,883 | +0.094020 | 0.003858 | [+0.086566, +0.101634] | 0 | p < 1/10001 (p < 0.000100) |
| 24 bars | 2h | 122,345 | 5,441 | +0.094202 | 0.004268 | [+0.086009, +0.102570] | 0 | p < 1/10001 (p < 0.000100) |
| 48 bars | 4h | 114,719 | 2,720 | +0.095649 | 0.004650 | [+0.086722, +0.104771] | 0 | p < 1/10001 (p < 0.000100) |
| 96 bars | 8h | 101,623 | 1,360 | +0.097701 | 0.005144 | [+0.087695, +0.107747] | 0 | p < 1/10001 (p < 0.000100) |

### 6.5 ADAUSDT Bootstrap Sensitivity
- **Observed Paired Delta ($\Delta\text{BA}$):** +0.135180
- **Relative Improvement:** +40.55%

| Block Length ($b$) | Horizon | Candidate Blocks | Blocks / Resample | Bootstrap Mean $\Delta\text{BA}$ | Bootstrap Std Error | 95% Bootstrap CI | Null Exceedances | p-Value Bound |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 12 bars | 1h | 127,118 | 10,873 | +0.132831 | 0.002717 | [+0.127482, +0.138140] | 0 | p < 1/10001 (p < 0.000100) |
| 24 bars | 2h | 123,895 | 5,436 | +0.131370 | 0.002940 | [+0.125559, +0.137066] | 0 | p < 1/10001 (p < 0.000100) |
| 48 bars | 4h | 118,140 | 2,718 | +0.129470 | 0.003139 | [+0.123268, +0.135529] | 0 | p < 1/10001 (p < 0.000100) |
| 96 bars | 8h | 108,934 | 1,359 | +0.128253 | 0.003399 | [+0.121516, +0.134830] | 0 | p < 1/10001 (p < 0.000100) |

### 6.6 SOLUSDT Bootstrap Sensitivity
- **Observed Paired Delta ($\Delta\text{BA}$):** +0.106631
- **Relative Improvement:** +31.99%

| Block Length ($b$) | Horizon | Candidate Blocks | Blocks / Resample | Bootstrap Mean $\Delta\text{BA}$ | Bootstrap Std Error | 95% Bootstrap CI | Null Exceedances | p-Value Bound |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 12 bars | 1h | 125,925 | 10,900 | +0.106696 | 0.004194 | [+0.098426, +0.114685] | 0 | p < 1/10001 (p < 0.000100) |
| 24 bars | 2h | 121,073 | 5,450 | +0.107528 | 0.004639 | [+0.098474, +0.116582] | 0 | p < 1/10001 (p < 0.000100) |
| 48 bars | 4h | 112,110 | 2,725 | +0.111298 | 0.005009 | [+0.101240, +0.121106] | 0 | p < 1/10001 (p < 0.000100) |
| 96 bars | 8h | 96,246 | 1,362 | +0.116940 | 0.005299 | [+0.106285, +0.127147] | 0 | p < 1/10001 (p < 0.000100) |

### 6.7 AVAXUSDT Bootstrap Sensitivity
- **Observed Paired Delta ($\Delta\text{BA}$):** +0.118928
- **Relative Improvement:** +35.68%

| Block Length ($b$) | Horizon | Candidate Blocks | Blocks / Resample | Bootstrap Mean $\Delta\text{BA}$ | Bootstrap Std Error | 95% Bootstrap CI | Null Exceedances | p-Value Bound |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 12 bars | 1h | 128,731 | 10,901 | +0.117988 | 0.002788 | [+0.112562, +0.123481] | 0 | p < 1/10001 (p < 0.000100) |
| 24 bars | 2h | 126,653 | 5,450 | +0.117629 | 0.003117 | [+0.111510, +0.123708] | 0 | p < 1/10001 (p < 0.000100) |
| 48 bars | 4h | 122,829 | 2,725 | +0.117147 | 0.003411 | [+0.110479, +0.123854] | 0 | p < 1/10001 (p < 0.000100) |
| 96 bars | 8h | 116,173 | 1,362 | +0.116032 | 0.003700 | [+0.108844, +0.123149] | 0 | p < 1/10001 (p < 0.000100) |

### 6.8 LINKUSDT Bootstrap Sensitivity
- **Observed Paired Delta ($\Delta\text{BA}$):** +0.165608
- **Relative Improvement:** +49.68%

| Block Length ($b$) | Horizon | Candidate Blocks | Blocks / Resample | Bootstrap Mean $\Delta\text{BA}$ | Bootstrap Std Error | 95% Bootstrap CI | Null Exceedances | p-Value Bound |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 12 bars | 1h | 129,148 | 10,898 | +0.165069 | 0.002558 | [+0.160032, +0.170066] | 0 | p < 1/10001 (p < 0.000100) |
| 24 bars | 2h | 127,533 | 5,449 | +0.164617 | 0.002867 | [+0.158918, +0.170243] | 0 | p < 1/10001 (p < 0.000100) |
| 48 bars | 4h | 124,464 | 2,724 | +0.164285 | 0.003176 | [+0.157989, +0.170458] | 0 | p < 1/10001 (p < 0.000100) |
| 96 bars | 8h | 118,706 | 1,362 | +0.163684 | 0.003682 | [+0.156475, +0.170838] | 0 | p < 1/10001 (p < 0.000100) |

### 6.9 DOGEUSDT Bootstrap Sensitivity
- **Observed Paired Delta ($\Delta\text{BA}$):** +0.154149
- **Relative Improvement:** +45.91%

| Block Length ($b$) | Horizon | Candidate Blocks | Blocks / Resample | Bootstrap Mean $\Delta\text{BA}$ | Bootstrap Std Error | 95% Bootstrap CI | Null Exceedances | p-Value Bound |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 12 bars | 1h | 126,363 | 10,887 | +0.153456 | 0.003542 | [+0.146528, +0.160246] | 0 | p < 1/10001 (p < 0.000100) |
| 24 bars | 2h | 122,128 | 5,443 | +0.153578 | 0.003864 | [+0.146002, +0.161182] | 0 | p < 1/10001 (p < 0.000100) |
| 48 bars | 4h | 114,247 | 2,721 | +0.153906 | 0.004096 | [+0.145954, +0.161883] | 0 | p < 1/10001 (p < 0.000100) |
| 96 bars | 8h | 100,540 | 1,360 | +0.154172 | 0.004079 | [+0.146218, +0.162096] | 0 | p < 1/10001 (p < 0.000100) |

### 6.10 LTCUSDT Bootstrap Sensitivity
- **Observed Paired Delta ($\Delta\text{BA}$):** +0.151769
- **Relative Improvement:** +45.53%

| Block Length ($b$) | Horizon | Candidate Blocks | Blocks / Resample | Bootstrap Mean $\Delta\text{BA}$ | Bootstrap Std Error | 95% Bootstrap CI | Null Exceedances | p-Value Bound |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 12 bars | 1h | 127,641 | 10,871 | +0.151017 | 0.002804 | [+0.145511, +0.156501] | 0 | p < 1/10001 (p < 0.000100) |
| 24 bars | 2h | 124,902 | 5,435 | +0.150931 | 0.003181 | [+0.144576, +0.157176] | 0 | p < 1/10001 (p < 0.000100) |
| 48 bars | 4h | 119,884 | 2,717 | +0.151327 | 0.003548 | [+0.144315, +0.158200] | 0 | p < 1/10001 (p < 0.000100) |
| 96 bars | 8h | 111,155 | 1,358 | +0.151879 | 0.004062 | [+0.143970, +0.159860] | 0 | p < 1/10001 (p < 0.000100) |

### 6.11 XMRUSDT Bootstrap Sensitivity
- **Observed Paired Delta ($\Delta\text{BA}$):** +0.053427
- **Relative Improvement:** +16.03%

| Block Length ($b$) | Horizon | Candidate Blocks | Blocks / Resample | Bootstrap Mean $\Delta\text{BA}$ | Bootstrap Std Error | 95% Bootstrap CI | Null Exceedances | p-Value Bound |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 12 bars | 1h | 15,063 | 1,271 | +0.053264 | 0.008618 | [+0.036298, +0.069962] | 0 | p < 1/10001 (p < 0.000100) |
| 24 bars | 2h | 14,859 | 635 | +0.053385 | 0.009111 | [+0.035825, +0.071202] | 0 | p < 1/10001 (p < 0.000100) |
| 48 bars | 4h | 14,451 | 317 | +0.053563 | 0.009688 | [+0.034789, +0.072469] | 0 | p < 1/10001 (p < 0.000100) |
| 96 bars | 8h | 13,664 | 158 | +0.054048 | 0.010060 | [+0.034670, +0.073985] | 0 | p < 1/10001 (p < 0.000100) |

---

## 7. Granular Per-Class Recall Improvements

The table below reports the paired per-class recall differences ($\text{Recall}_{B4} - \text{Recall}_{B0}$) across the canonical target classes:

| Specialist Instrument | SL Recall Delta ($\Delta\text{Recall}_{-1}$) | EXP Recall Delta ($\Delta\text{Recall}_{0}$) | TP Recall Delta ($\Delta\text{Recall}_{1}$) | Net Balanced Accuracy Lift | Primary Source of Lift |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **BTCUSDT** | -0.1735 | +0.3832 | +0.0915 | **+0.1004** | High EXP Recognition |
| **ETHUSDT** | +0.0627 | +0.4641 | -0.1472 | **+0.1265** | High EXP Recognition |
| **BNBUSDT** | +0.5580 | +0.4776 | -0.6356 | **+0.1333** | High EXP Recognition, Stop-Loss Precision |
| **XRPUSDT** | +0.3784 | +0.3203 | -0.4174 | **+0.0938** | High EXP Recognition, Stop-Loss Precision |
| **ADAUSDT** | +0.3470 | +0.6830 | -0.6245 | **+0.1352** | High EXP Recognition, Stop-Loss Precision |
| **SOLUSDT** | -0.6462 | +0.3678 | +0.5983 | **+0.1066** | High EXP Recognition, Take-Profit Precision |
| **AVAXUSDT** | -0.5759 | +0.5817 | +0.3510 | **+0.1189** | High EXP Recognition, Take-Profit Precision |
| **LINKUSDT** | -0.6237 | +0.7129 | +0.4076 | **+0.1656** | High EXP Recognition, Take-Profit Precision |
| **DOGEUSDT** | +0.2766 | +0.5665 | -0.3807 | **+0.1541** | High EXP Recognition, Stop-Loss Precision |
| **LTCUSDT** | +0.4041 | +0.6295 | -0.5783 | **+0.1518** | High EXP Recognition, Stop-Loss Precision |
| **XMRUSDT** | +0.4348 | +0.2943 | -0.5688 | **+0.0534** | High EXP Recognition, Stop-Loss Precision |

---

## 8. Data Provenance & Governance Verification

| Governance Requirement | Verification Standard | Audit Finding | Status |
| :--- | :--- | :--- | :---: |
| Model Training & Fitting | Zero .fit() calls authorized | No models trained or refitted; all predictions frozen from Phase 5.3.2 | **COMPLIANT** |
| Sample Accounting | Exactly 1,322,108 OOF observations | Reconciles exactly to 1,322,108 candles across 11 instruments | **COMPLIANT** |
| Prospective Holdout Boundary | 2026-11-01 00:00:00 to 2027-04-30 23:59:59 UTC | 0 prospective holdout candles accessed or analyzed | **COMPLIANT** |
| Temporal Boundary Compliance | Maximum historical timestamp 1777593599999 ms | Confirmed: zero samples past 2026-04-30 23:59:59 UTC | **COMPLIANT** |
| Multiplicity Control | Holm-Bonferroni correction at alpha = 0.05 | Implemented and confirmed: all 11 comparisons significant | **COMPLIANT** |
| Phase 5.4 Gate Status | Formal authorization required | Strict HOLD: no Phase 5.4 activity permitted | **COMPLIANT** |

---

**Audit Report Prepared By:** Independent Senior Quantitative Research Auditor  
**Timestamp:** 2026-11-01 22:00:00 UTC  
**Artifact Digest:** SHA-256 manifest recorded in `artifacts/phase_5_3_3_5/final_audit_manifest.json`  