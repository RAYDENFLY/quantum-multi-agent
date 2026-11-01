# QUANTUM PHASE 5.3.3.4: HISTORICAL BENCHMARK RECONCILIATION
## Cross-Phase Comparative Audit of B4 Balanced Accuracy

**Document ID:** `docs/PHASE_5_3_3_4_HISTORICAL_BENCHMARK_COMPARISON.md`  
**Phase:** Phase 5.3.3.4 (Forensic Metric Consistency and OOF Reconciliation)  
**Auditor:** Independent Senior Quantitative Research Auditor  
**Repository:** [quantum-multi-agent](file:///d:/quantum-multi-agent)  
**Status:** 100% Exact Reconciliation Established Across All 11 Specialists  

---

### 1. Executive Summary

This document reconciles the B4 (LightGBM Specialist) performance figures reported across previous phases:
- **Phase 5.3.1:** Pilot baseline training (BTCUSDT, XMRUSDT)
- **Phase 5.3.2:** Expanded fleet baseline training (remaining 9 pairs)
- **Phase 5.3.3.1:** Benchmark correction and governance closure
- **Phase 5.3.3.2:** Independent statistical verification
- **Phase 5.3.3.3:** Empirical OOF resampling and validation correction
- **Phase 5.3.3.4:** Forensic metric consistency and reconciliation

The investigation resolves the apparent conflict between the historical benchmarks (e.g. BTC = 0.4099, ETH = 0.4177) and the Phase 5.3.3.3 / Phase 5.3.3.4 reconstructed out-of-fold metrics (BTC = 0.4332, ETH = 0.4571).

The critical finding is that **no discrepancy exists in the underlying predictions**. When evaluated using the identical aggregation rule (unweighted fold mean), the reconstructed predictions reproduce the historical benchmarks to four decimal places across all 11 instruments. The difference between the fold mean and the pooled out-of-fold metric is an expected mathematical consequence of metric aggregation over unequal fold supports and regime shifts.

---

### 2. Required Reconciliation Table

The table below directly compares the historical reported benchmark and the reconstructed out-of-fold metrics for all 11 instruments:

| Instrument | Historical B4 Fold Mean BA | Reconstructed B4 Fold Mean BA | Reconstructed B4 Pooled OOF BA | Historical Test Samples | Reconstructed OOF Samples | Difference (Recon Fold Mean vs Historical) | Reconciliation Status |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| **BTCUSDT** | 0.4099 | 0.4099 | 0.4332 | 130,684 | 130,684 | **+0.0000** | **EXACT_RECONCILIATION** |
| **ETHUSDT** | 0.4177 | 0.4177 | 0.4571 | 130,728 | 130,728 | **+0.0000** | **EXACT_RECONCILIATION** |
| **BNBUSDT** | 0.3699 | 0.3699 | 0.4667 | 130,733 | 130,733 | **+0.0000** | **EXACT_RECONCILIATION** |
| **XRPUSDT** | 0.3747 | 0.3747 | 0.4286 | 130,741 | 130,741 | **+0.0000** | **EXACT_RECONCILIATION** |
| **ADAUSDT** | 0.4490 | 0.4490 | 0.4685 | 130,582 | 130,582 | **+0.0000** | **EXACT_RECONCILIATION** |
| **SOLUSDT** | 0.3878 | 0.3878 | 0.4400 | 130,713 | 130,713 | **+0.0000** | **EXACT_RECONCILIATION** |
| **AVAXUSDT** | 0.4145 | 0.4145 | 0.4523 | 130,724 | 130,724 | **+0.0000** | **EXACT_RECONCILIATION** |
| **LINKUSDT** | 0.4067 | 0.4067 | 0.4989 | 130,719 | 130,719 | **+0.0000** | **EXACT_RECONCILIATION** |
| **DOGEUSDT** | 0.3960 | 0.3960 | 0.4899 | 130,729 | 130,729 | **+0.0000** | **EXACT_RECONCILIATION** |
| **LTCUSDT** | 0.4355 | 0.4355 | 0.4851 | 130,731 | 130,731 | **+0.0000** | **EXACT_RECONCILIATION** |
| **XMRUSDT** | 0.3816 | 0.3816 | 0.3868 | 15,024 | 15,024 | **+0.0000** | **EXACT_RECONCILIATION** |

---

### 3. Investigation of Potential Causal Factors

Each potential factor was investigated systematically:

| Potential Factor | Verified Status | Impact on Discrepancy | Forensic Evidence |
| :--- | :---: | :--- | :--- |
| **Metric Aggregation** | **PRIMARY CAUSE** | **Fully explains difference** | Historical benchmarks reported unweighted fold mean. Phase 5.3.3.3 empirical resampling evaluated the continuous pooled OOF series. |
| **OOF Sample Population** | **IDENTICAL** | None | Reconstructed sample counts match historical fold test counts bit-exact across all 5 folds of all 11 instruments (1,322,108 total). |
| **Label Mapping** | **IDENTICAL** | None | Both phases used `{-1: SL, 0: EXP, 1: TP}` without alteration. |
| **Target Schema** | **IDENTICAL** | None | Strictly three-class triple barrier with horizon 12 bars and barrier multiplier 1.5. |
| **Fold Selection** | **IDENTICAL** | None | Identical `PurgedWalkForwardSplitter(n_splits=5, horizon_bars=12, embargo_bars=24, min_train_ratio=0.5)`. |
| **Warmup Exclusion** | **IDENTICAL** | None | 20 bars volatility warmup excluded identically. |
| **Ambiguous Exclusion** | **IDENTICAL** | None | Ambiguous (-2) and boundary (-999) excluded identically. |
| **Prediction Reconstruction** | **VERIFIED BIT-EXACT** | None | Predictions generated from serialized LightGBM binaries matched stored prediction hashes bit-exact. |

---

### 4. Methodological Interpretation

The higher score observed under pooled OOF evaluation ($0.4332$ vs $0.4099$ for BTC) must **not** be interpreted as an empirical improvement or algorithmic progress. It is entirely a property of the aggregation method:
- The underlying machine learning model is identical.
- The model weights and hyperparameters are identical.
- The test predictions and ground truth labels are identical.

**Audit Conclusion:** The historical fold mean benchmark remains the official reference for fold-by-fold stability, while the pooled OOF benchmark serves as the input for time-series bootstrap resampling and dependent-data statistical inference.
