# QUANTUM PHASE 5.3.0 - TEMPORAL VALIDATION IMPLEMENTATION SPECIFICATION

**Author:** Senior Quantitative Research Architect & Validation Engineer  
**Date:** 2026-11-01  
**Repository:** https://github.com/RAYDENFLY/quantum-multi-agent  
**Scope:** Purged & Embargoed Expanding-Window Walk-Forward Cross-Validation Design  
**Implementation:** [validation.py](file:///d:/quantum-multi-agent/src/quantum/ml/validation.py)  

---

## 1. TEMPORAL CROSS-VALIDATION PRINCIPLES

Standard K-fold cross-validation or random train-test splitting is catastrophic for financial time series because it creates massive lookahead bias, information leakage, and unrealistically inflated performance estimates.

QUANTUM mandates **Expanding-Window Walk-Forward Cross-Validation with Purging and Embargoing**:

1. **Strict Chronological Sequencing:**
   Samples are strictly ordered by `open_time_ms`. Random shuffling is strictly prohibited.
2. **Label Horizon Purging:**
   Because triple-barrier target labels look ahead $H = 12$ candles (60 minutes) to resolve first touches, training samples near the end of a training fold have forward horizons that overlap into the test fold. Purging removes the last $H = 12$ bars from every training window:
   $$\text{Train\_End\_Index} = \text{Test\_Start\_Index} - H$$
3. **Post-Test Embargoing:**
   An embargo of $E = 24$ bars (120 minutes / 2 hours) is enforced after test windows to prevent market microstructure autocorrelation leakage into subsequent evaluations.
4. **Prospective Holdout Inaccessibility:**
   The splitter strictly verifies that no sample timestamp touches `PROSPECTIVE_HOLDOUT` (`open_time_ms >= 1793491200000`). Attempting to split a dataset containing prospective holdout data triggers an immediate `PermissionError`.

---

## 2. WALK-FORWARD FOLD SPECIFICATION (5-FOLD EXPANDING DESIGN)

Evaluated strictly on uncontaminated Development and Validation partitions (`2023-11-01 00:00:00.000` to `2026-04-30 23:59:59.999 UTC`), containing 262,655 5m candles per standard instrument:

- **Initial Minimum Training Ratio:** 50.0% (approx. 131,327 candles / 15 months)
- **Evaluation Pool:** 50.0% (approx. 131,328 candles / 15 months)
- **Number of Walk-Forward Folds:** 5 folds
- **Test Fold Duration:** Approx. 26,265 candles (approx. 91 days / 3 months per fold)

### Exact Walk-Forward Fold Table (BTCUSDT 5m Benchmark)

| Fold # | Train Sample Count | Train Start UTC | Train End UTC (Purged) | Purged Bars | Test Sample Count | Test Start UTC | Test End UTC | Embargo Bars |
|---|---|---|---|---|---|---|---|---|
| **Fold 1** | 131,315 | 2023-11-01 00:00 | 2025-01-29 22:50 | 12 (60 min) | 26,265 | 2025-01-29 23:55 | 2025-05-01 04:35 | 24 (120 min) |
| **Fold 2** | 157,580 | 2023-11-01 00:00 | 2025-05-01 03:35 | 12 (60 min) | 26,265 | 2025-05-01 04:40 | 2025-07-31 09:20 | 24 (120 min) |
| **Fold 3** | 183,845 | 2023-11-01 00:00 | 2025-07-31 08:20 | 12 (60 min) | 26,265 | 2025-07-31 09:25 | 2025-10-30 14:10 | 24 (120 min) |
| **Fold 4** | 210,110 | 2023-11-01 00:00 | 2025-10-30 13:10 | 12 (60 min) | 26,265 | 2025-10-30 14:15 | 2026-01-29 18:55 | 24 (120 min) |
| **Fold 5** | 236,375 | 2023-11-01 00:00 | 2026-01-29 17:55 | 12 (60 min) | 26,268 | 2026-01-29 19:00 | 2026-04-30 23:55 | 24 (120 min) |

*Audit Verification:* In every fold, the purged gap ensures that the label of the last training candle resolves completely before the first test candle opens. The final test candle closes at `2026-04-30 23:55 UTC`, strictly respecting the `VALIDATION_END_MS` boundary.

---

## 3. STRICT PREPROCESSING BOUNDARY RULES

1. **Causal Fitting Only:**
   Feature scaling (via [SpecialistPreprocessor](file:///d:/quantum-multi-agent/src/quantum/ml/preprocessor.py)) must execute `fit()` strictly on the training fold indices `X[train_indices]`.
2. **Out-of-Fold Transform:**
   Test fold features `X[test_indices]` must be transformed using `preprocessor.transform()`. Re-fitting, updating scaler parameters, or calculating global statistics across the whole dataset is strictly forbidden.
3. **No Feature Selection on Test Folds:**
   Any future feature selection (such as mutual information or variance thresholding) must compute statistics exclusively on `X[train_indices]`.
