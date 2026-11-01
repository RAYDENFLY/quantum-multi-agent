# QUANTUM PHASE 5.3.0 - EXPERIMENT REPRODUCIBILITY SPECIFICATION

**Author:** Senior Quantitative ML Research Architect & Software Integrity Engineer  
**Date:** 2026-11-01  
**Repository:** https://github.com/RAYDENFLY/quantum-multi-agent  
**Scope:** Deterministic Seeds, Checksum Specifications, Manifest Verification, and Environment Lock  
**Standard:** 100% BIT-EXACT REPRODUCIBILITY CONTRACT  

---

## 1. REPRODUCIBILITY CORE CONTRACT

Every specialist model trained within QUANTUM must be 100% reproducible from its serialized [ExperimentManifest](file:///d:/quantum-multi-agent/src/quantum/ml/contracts.py#L58-L86). Any run given the same manifest, dataset hash, and software environment must produce bit-exact predictions and evaluation metrics.

---

## 2. DETERMINISTIC SEEDING POLICY

To prevent random state collisions while maintaining independent stochastic processes across instruments:

$$\mathbf{Global \quad Master \quad Seed: \quad 42}$$
$$\mathbf{Instrument \quad Seed_s = 42 + (\text{Instrument\_Index} \times 100)}$$

| Instrument | Index | Specialist Seed | Applied In |
|---|---|---|---|
| **ADAUSDT** | 1 | 142 | Bagging row/col subsampling, Logistic solver init |
| **XRPUSDT** | 2 | 242 | Bagging row/col subsampling, Logistic solver init |
| **BTCUSDT** | 3 | 342 | Bagging row/col subsampling, Logistic solver init |
| **BNBUSDT** | 4 | 442 | Bagging row/col subsampling, Logistic solver init |
| **ETHUSDT** | 5 | 542 | Bagging row/col subsampling, Logistic solver init |
| **SOLUSDT** | 6 | 642 | Bagging row/col subsampling, Logistic solver init |
| **AVAXUSDT** | 7 | 742 | Bagging row/col subsampling, Logistic solver init |
| **LINKUSDT** | 8 | 842 | Bagging row/col subsampling, Logistic solver init |
| **XMRUSDT** | 9 | 942 | Bagging row/col subsampling, Logistic solver init |
| **DOGEUSDT** | 10 | 1042 | Bagging row/col subsampling, Logistic solver init |
| **LTCUSDT** | 11 | 1142 | Bagging row/col subsampling, Logistic solver init |

---

## 3. CHECKSUM & VERSION INTEGRITY SIGNATURES

Every experiment manifest records five cryptographic hashes:

1. **Feature Schema Hash (`feature_schema_hash`):**
   Calculated as the SHA-256 of the comma-delimited 36 stationary feature column names:
   $$\text{Hash} = \text{SHA256}(\text{"log\_return,hl\_range\_pct,body\_pct,\dots,trend\_state"})$$
   Any modification to column names, ordering, or feature set triggers an immediate schema mismatch error.

2. **Target Configuration Hash (`target_config_hash`):**
   Calculated as the SHA-256 of the canonical JSON string of the target parameters:
   `{"barrier_multiplier": 1.5, "horizon_bars": 12, "maximum_holding_minutes": 60, "timeframe": "5m", "volatility_lookback": 20}`.

3. **Partition Data Hashes (`partition_hashes`):**
   SHA-256 hashes of the underlying Parquet partition files for Development and Validation. If input data is modified or re-generated, the partition hash changes, detecting dataset drift.

4. **Model Hyperparameter Hash (`model_config_hash`):**
   SHA-256 of the sorted hyperparameter dictionary passed to the estimator constructor.

5. **Composite Manifest Hash (`manifest_hash`):**
   A composite SHA-256 hash calculated over the entire serialized manifest. This serves as the primary unique experiment key in the [ModelRegistry](file:///d:/quantum-multi-agent/src/quantum/ml/registry.py).

---

## 4. SOFTWARE ENVIRONMENT LOCK

All machine learning experiments in Phase 5.3 must execute within a locked Python environment. The local versions verified on this host are:

| Package | Locked Version | Verification Command | Purpose |
|---|---|---|---|
| **Python** | 3.13.7 | `sys.version` | Core runtime environment |
| **scikit-learn** | 1.8.0 | `sklearn.__version__` | Baseline estimators & preprocessors |
| **LightGBM** | 4.6.0 | `lightgbm.__version__` | Gradient boosted decision trees |
| **NumPy** | 2.4.4 | `numpy.__version__` | Numerical array computations |
| **Pandas** | 3.0.3 | `pandas.__version__` | Data manipulation & time indexing |
| **SciPy** | 1.16.1 | `scipy.__version__` | Statistical distributions & optimization |
| **Joblib** | 1.5.2 | `joblib.__version__` | Serialization & process pooling |

Any variation in major or minor versions must be flagged in experiment manifests to prevent cross-version numerical floating-point discrepancies.

---

## 5. REPRODUCIBILITY AUDIT PROTOCOL

Prior to accepting any model artifact into the Model Registry:
1. The experiment runner must instantiate the model using the manifest's parameters.
2. The dataset loader must verify that the partition hashes match the manifest.
3. The evaluation metrics from a test fold must be re-evaluated and matched against the reported metrics.
4. If metrics deviate by more than $10^{-6}$, the build is failed and quarantined.
