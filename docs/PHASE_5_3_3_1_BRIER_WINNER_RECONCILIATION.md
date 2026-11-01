# QUANTUM PHASE 5.3.3.1: BRIER SCORE WINNER RECONCILIATION REPORT

**Phase:** Phase 5.3.3.1  
**Date:** 2026-11-01  
**Lead Quantitative Systems Auditor:** QUANTUM Independent Quality & Systems Audit Lead  
**Scope:** Definitive reconciliation of multiclass Brier score winner selection across all baselines vs ML models  
**Source Manifest:** [brier_reconciliation.json](file:///d:/quantum-multi-agent/artifacts/phase_5_3_3_1/brier_reconciliation.json)

---

## 1. Executive Summary

This audit resolves the apparent inconsistency identified in Phase 5.3.3 regarding multiclass Brier score winner selection:
- For several instruments (such as `BTCUSDT` and `XMRUSDT`), the naive baseline `B1_Prior` achieved a lower quadratic Brier loss than `B4_LightGBM` (e.g. BTC: B1 = 0.5549 vs B4 = 0.5795; XMR: B1 = 0.6010 vs B4 = 0.6362).
- However, the Phase 5.3.3 catalog labeled B4 as the winner because the comparison was performed solely across predictive ML models (`B2`, `B3`, `B4`).

To eliminate ambiguity, this report establishes two distinct, non-overlapping winner fields:
1. `LOWEST_BRIER_ALL_BASELINES`: Evaluates all 5 models (`B0` through `B4`).
2. `LOWEST_BRIER_ML_MODELS`: Evaluates strictly the 3 predictive machine learning models (`B2`, `B3`, `B4`).

In addition, the LTCUSDT values were verified: `B3_RandomForest` (0.6083) achieves a lower Brier score than `B4_LightGBM` (0.6088).

---

## 2. Mathematical Explanation: Why B1 Prior Beats B4 on Noisy Assets

In multiclass forecasting with $K=3$ classes, Brier score is the mean squared Euclidean distance between forecasted probabilities $\mathbf{f}_i = (f_{i,-1}, f_{i,0}, f_{i,+1})$ and one-hot outcomes $\mathbf{o}_i$:
$$BS = \frac{1}{N} \sum_{i=1}^N \sum_{k=1}^K (f_{ik} - o_{ik})^2$$

### 2.1 The Conservative Baseline Property of B1 Prior
`B1_Prior` outputs a static, unconditional probability vector $\mathbf{p} = (p_{-1}, p_0, p_{+1})$ for every single bar.
Because $\mathbf{p}$ matches the historical empirical class proportions, its expected Brier score simplifies to:
$$E[BS_{B1}] = 1 - \sum_{k=1}^K p_k^2$$
For roughly balanced 3-class data ($p_k \approx 0.33$), $E[BS_{B1}] \approx 1 - 3(0.1111) = 0.6667$.
When one class has slight dominance (e.g. $p_0 \approx 0.45$), $E[BS_{B1}] \approx 1 - (0.28^2 + 0.45^2 + 0.27^2) \approx 0.55 - 0.60$.
Because B1 never takes high-confidence bets, it never suffers large quadratic penalties.

### 2.2 The Decisive Prediction Penalty of Conditional Models (B4)
In contrast, `B4_LightGBM` attempts to predict conditional probabilities $P(Y_t = k \mid \mathbf{X}_t)$.
When a conditional model outputs high probabilities (e.g., $f_{i,+1} = 0.70$) on a noisy financial candle that ultimately hits the stop-loss barrier ($o_{i,-1} = 1.0$), the quadratic penalty is large:
$$(0.0 - 1.0)^2 + (0.0 - 0.0)^2 + (0.70 - 0.0)^2 = 1.0 + 0.49 = 1.49$$
In low-signal, high-noise regimes (such as BTC, ETH, SOL, ADA), the variance of conditional forecasts can cause unregularized probability predictions to incur higher quadratic loss than a static, perfectly calibrated prior forecast.

---

## 3. Definitive Brier Score Winner Table (11 Specialists)

The table below reconciles all 11 instruments, reporting exact Brier scores across all 5 models and distinguishing winners across both candidate comparison universes:

| Symbol | B0 Majority | B1 Prior | B2 Logistic Regression | B3 Random Forest | B4 LightGBM | LOWEST_BRIER_ALL_BASELINES | LOWEST_BRIER_ML_MODELS |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| **BTCUSDT** | 1.0582 | 0.5549 | 0.5900 | 0.5975 | 0.5795 | **B1_Prior (0.5549)** | **B4_LightGBM (0.5795)** |
| **XMRUSDT** | 1.0908 | 0.6010 | 0.6399 | 0.6382 | 0.6362 | **B1_Prior (0.6010)** | **B4_LightGBM (0.6362)** |
| **ADAUSDT** | 1.1642 | 0.6158 | 0.6669 | 0.6461 | 0.6454 | **B1_Prior (0.6158)** | **B4_LightGBM (0.6454)** |
| **XRPUSDT** | 1.0807 | 0.5855 | 0.5802 | 0.5723 | 0.5635 | **B4_LightGBM (0.5635)** | **B4_LightGBM (0.5635)** |
| **BNBUSDT** | 1.0955 | 0.5910 | 0.5836 | 0.5785 | 0.5716 | **B4_LightGBM (0.5716)** | **B4_LightGBM (0.5716)** |
| **ETHUSDT** | 1.0694 | 0.5598 | 0.5838 | 0.5883 | 0.5750 | **B1_Prior (0.5598)** | **B4_LightGBM (0.5750)** |
| **SOLUSDT** | 1.0529 | 0.5546 | 0.5741 | 0.5687 | 0.5594 | **B1_Prior (0.5546)** | **B4_LightGBM (0.5594)** |
| **AVAXUSDT** | 1.2125 | 0.6516 | 0.6413 | 0.6291 | 0.6246 | **B4_LightGBM (0.6246)** | **B4_LightGBM (0.6246)** |
| **LINKUSDT** | 1.2680 | 0.6746 | 0.6239 | 0.6005 | 0.5957 | **B4_LightGBM (0.5957)** | **B4_LightGBM (0.5957)** |
| **DOGEUSDT** | 1.1257 | 0.6057 | 0.5887 | 0.5775 | 0.5749 | **B4_LightGBM (0.5749)** | **B4_LightGBM (0.5749)** |
| **LTCUSDT** | 1.2471 | 0.6622 | 0.6292 | 0.6083 | 0.6088 | **B3_RandomForest (0.6083)** | **B3_RandomForest (0.6083)** |

---

## 4. Key Takeaways & LTCUSDT Reconciliation

1. **Comparison Universe Clarity:**
   - Under `LOWEST_BRIER_ALL_BASELINES`, `B1_Prior` wins on 5 instruments (`BTC`, `XMR`, `ADA`, `ETH`, `SOL`), while `B4_LightGBM` wins on 5 instruments (`XRP`, `BNB`, `AVAX`, `LINK`, `DOGE`), and `B3_RandomForest` wins on 1 instrument (`LTC`).
   - Under `LOWEST_BRIER_ML_MODELS`, `B4_LightGBM` wins on 10 out of 11 instruments, with `B3_RandomForest` winning on `LTCUSDT`.
2. **LTCUSDT Precision Verification:**
   - `B3_RandomForest`: **0.6083**
   - `B4_LightGBM`: **0.6088**
   - Discrepancy: $0.6088 - 0.6083 = 0.0005$.
   - `B3_RandomForest` is the verified winner across both universes for LTCUSDT.
3. **Governance Recommendation:**
   The master catalog must always present both fields side-by-side to ensure full transparency regarding whether conditional ML probabilities beat unconditional priors on quadratic scoring rules.
