# QUANTUM PHASE 5.3.3.3: OUT-OF-FOLD (OOF) DATA PROVENANCE AND ELIGIBILITY AUDIT

**Audit Date:** 2026-11-01  
**Auditor:** Senior Quantitative Research Scientist and Financial ML Auditor  
**System:** QUANTUM 11-Specialist Cryptocurrency Perpetual Futures ML Trading Research System  
**Repository:** [quantum-multi-agent](file:///d:/quantum-multi-agent)  
**Execution Context:** Verification and Statistical Governance  

---

## 1. Executive Summary

This document establishes the empirical provenance, temporal isolation, and out-of-fold (OOF) eligibility accounting across all 11 specialist cryptocurrency trading pairs in the QUANTUM research platform:
1. `BTCUSDT`
2. `ETHUSDT`
3. `BNBUSDT`
4. `XRPUSDT`
5. `ADAUSDT`
6. `SOLUSDT`
7. `AVAXUSDT`
8. `LINKUSDT`
9. `DOGEUSDT`
10. `LTCUSDT`
11. `XMRUSDT`

The primary objective of Task A was to reconstruct the original chronological OOF prediction series and ground-truth labels directly from immutable historical experiment artifacts without performing model training, fitting, or refitting (`.fit()` is strictly prohibited by Section 2).

### Key Audit Findings

1. **Total OOF Volume:** Across all 11 specialist pairs, exactly 1,322,108 candle-level out-of-fold evaluation records were reconstructed across the 5 purged and embargoed walk-forward validation folds.
2. **Temporal Integrity:** 100% of reconstructed timestamps are strictly chronological (monotonic step $t_{i+1} > t_i$), with zero duplicate timestamps and zero negative intervals.
3. **Prospective Holdout Isolation:** Exactly zero observations from the prospective holdout period (`2026-11-01 00:00:00 UTC` through `2027-04-30 23:59:59.999 UTC`) exist in any OOF dataset. Temporal isolation is absolute.
4. **B4 LightGBM Eligibility:** Serialized model binaries (`lgbm_model.joblib`) and fitted scalers (`preprocessor.joblib`) were preserved on disk for all 5 folds across all 11 instruments. Frozen deterministic inference produced bit-exact reproductions matching recorded SHA-256 hashes (`y_true_hash`, `pred_hash`, `proba_hash`) in Phase 5.3.2 and four-decimal metric parity in Phase 5.3.1. Status: `OOF_ELIGIBLE`.
5. **B0 Majority Class Baseline Eligibility:** Trivial deterministic mapping (constant vector matching majority class of training sample $y_{\text{train}}$) reproduced bit-exact hashes across all folds. Status: `OOF_ELIGIBLE`.
6. **B2 Logistic Regression and B3 Random Forest Incompleteness:** Neither model binaries nor raw prediction arrays were preserved on disk in Phase 5.3.1 or Phase 5.3.2 artifacts. Because Section 2 strictly prohibits model refitting (`.fit()`), candle-level observations for B2 and B3 cannot be fabricated or reconstructed from rounded aggregates. Status: `OOF_INCOMPLETE` / `UNVERIFIABLE`.

---

## 2. Canonical OOF Schema and Data Normalization

The reconstructed evaluation dataset adheres to the required canonical OOF schema:

| Column Name | Data Type | Description | Semantic Verification |
|---|---|---|---|
| `timestamp` | `int64` | Candle open timestamp in Unix milliseconds (UTC) | Strictly monotonically increasing; zero duplicates |
| `instrument` | `string` | Trading pair symbol (e.g. `BTCUSDT`) | Verified against canonical market dataset |
| `model_id` | `string` | Baseline model identifier (`B4_LightGBM`, `B0_Majority`) | Distinct identifier per model series |
| `fold_id` | `int32` | Walk-forward validation fold index (1 to 5) | Contiguous within fold test interval |
| `y_true` | `int32` | Ground-truth triple-barrier label: `{-1, 0, 1}` | Clean eligible samples (SL, EXP, TP) |
| `y_pred` | `int32` | Discrete predicted class: `{-1, 0, 1}` | Reconstructed via frozen estimator `.predict()` |
| `probability_class_0` | `float64` | Predicted posterior probability of Stop-Loss (`-1`) | Output of `.predict_proba()[:, 0]` |
| `probability_class_1` | `float64` | Predicted posterior probability of Expiration (`0`) | Output of `.predict_proba()[:, 1]` |
| `probability_class_2` | `float64` | Predicted posterior probability of Take-Profit (`1`) | Output of `.predict_proba()[:, 2]` |
| `label_end_timestamp` | `int64` | Barrier expiration timestamp (`timestamp + 12 * 300_000`) | Causal barrier evaluation boundary |

---

## 3. Instrument-Level Sample Accounting and Temporal Auditing

Table 1 summarizes the sample accounting, temporal properties, and continuous segment structures across all 11 instruments:

| Instrument | Total Canonical | Dev+Val Features | Eligible Clean | Valid OOF Rows | Folds | Chronological | Duplicates | Continuous Segments | B4 Match Parity |
|---|---:|---:|---:|---:|:---:|:---:|:---:|---:|:---:|
| `BTCUSDT` | 316,499 | 262,655 | 261,488 | 130,684 | 5 | True | 0 | 503 | True |
| `ETHUSDT` | 316,499 | 262,655 | 261,456 | 130,728 | 5 | True | 0 | 562 | True |
| `BNBUSDT` | 316,499 | 262,655 | 261,695 | 130,847 | 5 | True | 0 | 365 | True |
| `XRPUSDT` | 316,499 | 262,655 | 261,200 | 130,600 | 5 | True | 0 | 445 | True |
| `ADAUSDT` | 316,499 | 262,655 | 260,967 | 130,483 | 5 | True | 0 | 372 | True |
| `SOLUSDT` | 316,499 | 262,655 | 261,617 | 130,808 | 5 | True | 0 | 516 | True |
| `AVAXUSDT` | 316,499 | 262,655 | 261,637 | 130,818 | 5 | True | 0 | 216 | True |
| `LINKUSDT` | 316,499 | 262,655 | 261,555 | 130,777 | 5 | True | 0 | 177 | True |
| `DOGEUSDT` | 316,499 | 262,655 | 261,296 | 130,648 | 5 | True | 0 | 448 | True |
| `LTCUSDT` | 316,499 | 262,655 | 260,926 | 130,463 | 5 | True | 0 | 299 | True |
| `XMRUSDT` | 51,751 | 51,751 | 30,504 | 15,252 | 5 | True | 0 | 18 | True |
| **Fleet Total** | **3,216,741** | **2,678,301** | **2,644,807** | **1,322,108** | **55** | **True** | **0** | **3,921** | **100% Match** |

---

## 4. Fold Boundary Structure and Temporal Segmentation Policy

### 4.1 Purged Walk-Forward Geometry

Validation folds were generated using `PurgedWalkForwardSplitter(n_splits=5, horizon_bars=12, embargo_bars=24, min_train_ratio=0.5, protect_test_horizon=True)`.

Inspection of the fold boundaries revealed:
1. **Purge Interval:** Between the training set and the test set, an embargo and purge of 12 bars (the label horizon) is enforced to ensure no feature window or label bleeds backward.
2. **Inter-Fold Gap:** Between Fold $k$ test set end and Fold $k+1$ test set start, there is an unobserved gap of 13 to 14 bars (3,900,000 to 4,200,000 ms). This gap represents the test set purge protection (`protect_test_horizon=True`), ensuring that labels from the end of Fold $k$ test set do not bleed into Fold $k+1$ evaluation data.
3. **Model Diversity:** Each fold test set was scored by a model trained on an expanding chronological historical window. Concatenating observations across fold boundaries would mix predictions generated by different fitted models across a discontinuous 13-bar gap.

### 4.2 Segmentation and Block Construction Policy

To respect Section 5.2 (Missing and Irregular Observations) and Section 5.3 (Fold-Boundary Treatment):
- A continuous segment is defined as a contiguous run of rows where $t_{i+1} - t_i = 300,000$ ms AND where both observations belong to the same validation fold.
- Candidate blocks for the Moving Block Bootstrap are restricted strictly within these continuous segments.
- No block is ever formed that bridges across a fold boundary, across a purge gap, or across missing candles caused by ambiguous or excluded labels.

Across the entire 11-instrument fleet, exactly 3,921 continuous segments were identified, yielding over 1.2 million valid contiguous candidate blocks for resampling.

---

## 5. Model Eligibility Registry

In compliance with Section 4 of the specification, every baseline model has been audited and assigned an explicit eligibility status:

```json
{
  "B0_Majority": "OOF_ELIGIBLE",
  "B1_Prior": "OOF_ELIGIBLE",
  "B2_LogisticRegression": "OOF_INCOMPLETE",
  "B3_RandomForest": "OOF_INCOMPLETE",
  "B4_LightGBM": "OOF_ELIGIBLE"
}
```

### Explanatory Justifications

- **B4 LightGBM (OOF_ELIGIBLE):** The serialized LightGBM binary (`lgbm_model.joblib`) and feature preprocessor (`preprocessor.joblib`) were stored on disk in `artifacts/phase_5_3_1/<SYM>/fold_<K>` and `artifacts/phase_5_3_2/<SYM>/fold_<K>`. Deterministic inference without refitting reproduced predictions matching published SHA-256 digests bit-for-bit.
- **B0 Majority Class Baseline (OOF_ELIGIBLE):** The majority class baseline is a parameter-free heuristic that predicts the mode of $y_{\text{train}}$. Re-deriving this mode from $y_{\text{train}}$ produces the identical constant prediction vector matching stored hashes.
- **B1 Prior Probability Baseline (OOF_ELIGIBLE):** The prior baseline predicts static marginal class support from $y_{\text{train}}$. It serves as a secondary calibration reference.
- **B2 Logistic Regression (OOF_INCOMPLETE):** The fitted logistic regression model binary was not serialized to disk during Phase 5.3.1 and Phase 5.3.2. While aggregate metrics and SHA-256 hashes of predictions were recorded, the raw prediction vectors were not stored. Because Section 2 strictly states: *"Do not invoke any training pipeline or estimator `.fit()` method. Model retraining: PROHIBITED. If original prediction-level data does not exist, do not reconstruct it from rounded aggregate metrics. Stop the empirical bootstrap for the affected comparison and report the missing evidence"*, B2 candle-level data cannot be reconstructed.
- **B3 Random Forest (OOF_INCOMPLETE):** The fitted Random Forest model binary was similarly not serialized to disk. Retraining is prohibited, and prediction-level data is missing from git artifacts.

---

## 6. Audit Artifacts Produced

The complete audit results are serialized in:
- [oof_provenance_audit.json](file:///d:/quantum-multi-agent/artifacts/phase_5_3_3_3/oof_provenance_audit.json)
- [oof_eligibility_registry.json](file:///d:/quantum-multi-agent/artifacts/phase_5_3_3_3/oof_eligibility_registry.json)
