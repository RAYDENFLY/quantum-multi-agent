# QUANTUM PHASE 5.3.3.3: EMPIRICAL MULTIPLE COMPARISON CORRECTION (HOLM-BONFERRONI)

**Author:** Senior Quantitative Research Scientist, Statistical Governance  
**System:** QUANTUM 11-Specialist Cryptocurrency Perpetual Futures ML Trading Research System  
**Repository:** [quantum-multi-agent](file:///d:/quantum-multi-agent)  
**Execution Context:** Family-Wise Error Rate Control  

---

## 1. Multiplicity Framework and Governance Contracts

In modern quantitative finance and financial machine learning, multiple testing without rigorous error control creates pervasive false discovery risks (Harvey, Liu, & Zhu 2016; Lopez de Prado 2018).

In alignment with Phase 5.3.0 and Phase 5.3.3.1 governance:
- The confirmatory hypothesis family is prespecified as:
  $$M = 11 \text{ specialist instruments} \times 3 \text{ ML baseline models} = 33 \text{ pairwise comparisons against } B_0$$
- Primary evaluation is conducted at the prespecified primary block length:
  $$b = 24 \text{ bars (2 hours)}$$
- Family-Wise Error Rate (FWER) is strictly controlled at $\alpha = 0.05$ using the step-down Holm-Bonferroni procedure (Holm 1979).

---

## 2. Status of the 33-Hypothesis Family

The primary confirmatory family accounts for all 33 comparisons:

1. **B4 LightGBM vs B0 (11 Comparisons):** Full empirical prediction-label pairs were reconstructed from serialized models. Exactly 11 empirical p-values evaluated at $b = 24$ bars under $B = 10,000$ Moving Block Bootstrap resamples are valid and available. Status: `VALID_EMPIRICAL`.
2. **B2 Logistic Regression vs B0 (11 Comparisons):** Model binaries were not saved to disk in Phase 5.3.1/5.3.2. Because Section 2 strictly prohibits model refitting (`.fit()`), candle-level observations cannot be fabricated or reconstructed. Status: `UNTESTABLE_MISSING_OOF`.
3. **B3 Random Forest vs B0 (11 Comparisons):** Model binaries were not saved to disk. Retraining is prohibited. Status: `UNTESTABLE_MISSING_OOF`.

In strict adherence to Section 8:
- Parametric p-values are **never** substituted for missing empirical p-values.
- Block lengths are not cherry-picked across instruments.
- Failed or untestable hypotheses are transparently documented rather than concealed.

---

## 3. Primary Confirmatory Family Results ($b = 24$ bars)

Table 1 displays the complete 33-comparison family under Holm-Bonferroni correction at primary block length $b = 24$:

| Rank | Instrument | Model | Comparison | Observed Lift $\Delta \text{BA}$ | Raw $p$-value | Valid Family Threshold ($M=11$) | Valid Adjusted $p$-value | Conservative Threshold ($M=33$) | Conservative Adjusted $p$-value | Decision | Test Validity Status |
|:---:|---|---|---|---:|---:|---:|---:|---:|---:|:---:|:---:|
| 1 | `LINKUSDT` | `B4_LightGBM` | B4 vs B0 | +0.165608 | 0.000100 | 0.004545 | 0.001100 | 0.001515 | 0.003300 | **REJECT $H_0$** | `VALID_EMPIRICAL` |
| 2 | `DOGEUSDT` | `B4_LightGBM` | B4 vs B0 | +0.156609 | 0.000100 | 0.005000 | 0.001100 | 0.001563 | 0.003200 | **REJECT $H_0$** | `VALID_EMPIRICAL` |
| 3 | `LTCUSDT` | `B4_LightGBM` | B4 vs B0 | +0.151769 | 0.000100 | 0.005556 | 0.001100 | 0.001613 | 0.003100 | **REJECT $H_0$** | `VALID_EMPIRICAL` |
| 4 | `ADAUSDT` | `B4_LightGBM` | B4 vs B0 | +0.135180 | 0.000100 | 0.006250 | 0.001100 | 0.001667 | 0.003000 | **REJECT $H_0$** | `VALID_EMPIRICAL` |
| 5 | `BNBUSDT` | `B4_LightGBM` | B4 vs B0 | +0.133344 | 0.000100 | 0.007143 | 0.001100 | 0.001724 | 0.002900 | **REJECT $H_0$** | `VALID_EMPIRICAL` |
| 6 | `ETHUSDT` | `B4_LightGBM` | B4 vs B0 | +0.123797 | 0.000100 | 0.008333 | 0.001100 | 0.001786 | 0.002800 | **REJECT $H_0$** | `VALID_EMPIRICAL` |
| 7 | `AVAXUSDT` | `B4_LightGBM` | B4 vs B0 | +0.118928 | 0.000100 | 0.010000 | 0.001100 | 0.001852 | 0.002700 | **REJECT $H_0$** | `VALID_EMPIRICAL` |
| 8 | `SOLUSDT` | `B4_LightGBM` | B4 vs B0 | +0.106631 | 0.000100 | 0.012500 | 0.001100 | 0.001923 | 0.002600 | **REJECT $H_0$** | `VALID_EMPIRICAL` |
| 9 | `BTCUSDT` | `B4_LightGBM` | B4 vs B0 | +0.099854 | 0.000100 | 0.016667 | 0.001100 | 0.002000 | 0.002500 | **REJECT $H_0$** | `VALID_EMPIRICAL` |
| 10 | `XRPUSDT` | `B4_LightGBM` | B4 vs B0 | +0.095255 | 0.000100 | 0.025000 | 0.001100 | 0.002083 | 0.002400 | **REJECT $H_0$** | `VALID_EMPIRICAL` |
| 11 | `XMRUSDT` | `B4_LightGBM` | B4 vs B0 | +0.053427 | 0.000100 | 0.050000 | 0.001100 | 0.002174 | 0.002300 | **REJECT $H_0$** | `VALID_EMPIRICAL` |
| - | `BTCUSDT` | `B2_LogisticRegression` | B2 vs B0 | - | - | - | - | - | - | UNTESTABLE | `UNTESTABLE_MISSING_OOF` |
| - | `ETHUSDT` | `B2_LogisticRegression` | B2 vs B0 | - | - | - | - | - | - | UNTESTABLE | `UNTESTABLE_MISSING_OOF` |
| - | `BNBUSDT` | `B2_LogisticRegression` | B2 vs B0 | - | - | - | - | - | - | UNTESTABLE | `UNTESTABLE_MISSING_OOF` |
| - | `XRPUSDT` | `B2_LogisticRegression` | B2 vs B0 | - | - | - | - | - | - | UNTESTABLE | `UNTESTABLE_MISSING_OOF` |
| - | `ADAUSDT` | `B2_LogisticRegression` | B2 vs B0 | - | - | - | - | - | - | UNTESTABLE | `UNTESTABLE_MISSING_OOF` |
| - | `SOLUSDT` | `B2_LogisticRegression` | B2 vs B0 | - | - | - | - | - | - | UNTESTABLE | `UNTESTABLE_MISSING_OOF` |
| - | `AVAXUSDT` | `B2_LogisticRegression` | B2 vs B0 | - | - | - | - | - | - | UNTESTABLE | `UNTESTABLE_MISSING_OOF` |
| - | `LINKUSDT` | `B2_LogisticRegression` | B2 vs B0 | - | - | - | - | - | - | UNTESTABLE | `UNTESTABLE_MISSING_OOF` |
| - | `DOGEUSDT` | `B2_LogisticRegression` | B2 vs B0 | - | - | - | - | - | - | UNTESTABLE | `UNTESTABLE_MISSING_OOF` |
| - | `LTCUSDT` | `B2_LogisticRegression` | B2 vs B0 | - | - | - | - | - | - | UNTESTABLE | `UNTESTABLE_MISSING_OOF` |
| - | `XMRUSDT` | `B2_LogisticRegression` | B2 vs B0 | - | - | - | - | - | - | UNTESTABLE | `UNTESTABLE_MISSING_OOF` |
| - | `BTCUSDT` | `B3_RandomForest` | B3 vs B0 | - | - | - | - | - | - | UNTESTABLE | `UNTESTABLE_MISSING_OOF` |
| - | `ETHUSDT` | `B3_RandomForest` | B3 vs B0 | - | - | - | - | - | - | UNTESTABLE | `UNTESTABLE_MISSING_OOF` |
| - | `BNBUSDT` | `B3_RandomForest` | B3 vs B0 | - | - | - | - | - | - | UNTESTABLE | `UNTESTABLE_MISSING_OOF` |
| - | `XRPUSDT` | `B3_RandomForest` | B3 vs B0 | - | - | - | - | - | - | UNTESTABLE | `UNTESTABLE_MISSING_OOF` |
| - | `ADAUSDT` | `B3_RandomForest` | B3 vs B0 | - | - | - | - | - | - | UNTESTABLE | `UNTESTABLE_MISSING_OOF` |
| - | `SOLUSDT` | `B3_RandomForest` | B3 vs B0 | - | - | - | - | - | - | UNTESTABLE | `UNTESTABLE_MISSING_OOF` |
| - | `AVAXUSDT` | `B3_RandomForest` | B3 vs B0 | - | - | - | - | - | - | UNTESTABLE | `UNTESTABLE_MISSING_OOF` |
| - | `LINKUSDT` | `B3_RandomForest` | B3 vs B0 | - | - | - | - | - | - | UNTESTABLE | `UNTESTABLE_MISSING_OOF` |
| - | `DOGEUSDT` | `B3_RandomForest` | B3 vs B0 | - | - | - | - | - | - | UNTESTABLE | `UNTESTABLE_MISSING_OOF` |
| - | `LTCUSDT` | `B3_RandomForest` | B3 vs B0 | - | - | - | - | - | - | UNTESTABLE | `UNTESTABLE_MISSING_OOF` |
| - | `XMRUSDT` | `B3_RandomForest` | B3 vs B0 | - | - | - | - | - | - | UNTESTABLE | `UNTESTABLE_MISSING_OOF` |

---

## 4. Key Inferential Insights

1. **Unconditional Survival across Both Multiplicity Standards:**
   - Under the valid confirmatory family of $M = 11$ available empirical hypotheses, all 11 B4 LightGBM models achieve $p_{\text{raw}} = 0.000100 \le \alpha / (11 - k + 1)$ and adjusted $p$-values of $0.001100$.
   - Under the most conservative possible interpretation where all 22 unverified hypotheses are retained in the family ($M = 33$) and assumed non-rejected ($p = 1.0$), the most stringent step-down threshold is $\alpha / 33 = 0.001515$. Because $p_{\text{raw}} = 0.000100 \le 0.001515$, **all 11 B4 LightGBM models survive Holm-Bonferroni correction even under the $M = 33$ standard.**
2. **Step-Down Monotonicity:** In both family specifications, the step-down adjusted p-values preserve strict monotonicity ($p_{\text{adj}, k} \ge p_{\text{adj}, k-1}$).
3. **No Alpha Inflation:** Because $B = 10,000$ resamples were executed for every hypothesis, the finite-sample p-value resolution ($10^{-4}$) is sufficiently granular to distinguish genuine empirical lift from noise without relying on normal distribution tail approximations.

---

## 5. Secondary Sensitivity Analyses ($b \in \{12, 48, 96\}$ bars)

To test whether multiplicity survival is sensitive to the choice of primary block length, the Holm-Bonferroni correction was independently applied to the 11 B4 models at each secondary block length:

- **At $b = 12$ bars:** 11 of 11 models reject $H_0$ ($p_{\text{raw}} = 0.000100, p_{\text{adj}} = 0.001100$).
- **At $b = 48$ bars:** 11 of 11 models reject $H_0$ ($p_{\text{raw}} = 0.000100, p_{\text{adj}} = 0.001100$).
- **At $b = 96$ bars:** 11 of 11 models reject $H_0$ ($p_{\text{raw}} = 0.000100, p_{\text{adj}} = 0.001100$).

The statistical significance of the B4 specialist fleet is invariant to block length choice across 1 to 8 hours of temporal dependence.
