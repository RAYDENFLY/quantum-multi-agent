# QUANTUM — EVIDENCE SEPARATION & DATA PARTITIONING POLICY
## PROTOCOLS FOR CHRONOLOGICAL INTEGRITY & HOLDOUT PRESERVATION

---

### 1. OBJECTIVE & CORE MANDATE

To eliminate the most prevalent forms of quantitative research corruption (data leakage, lookahead bias, parameter snooping, and survivorship bias), QUANTUM enforces a strict, four-tier evidence separation protocol.

Every research experiment executed in QUANTUM must explicitly declare its target evidence tier:
1. `TRAIN`
2. `VALIDATION`
3. `ROLLING_OOS`
4. `PROSPECTIVE_OOS`

> [!IMPORTANT]
> **Cardinal Invariant:** Results obtained on `VALIDATION` partitions can NEVER be reported as independent out-of-sample evidence. Validation exists solely for hyperparameter tuning and model selection. Only `ROLLING_OOS` and `PROSPECTIVE_OOS` constitute valid out-of-sample confirmation.

---

### 2. THE FOUR EVIDENCE TIERS

```
+-------------------------------------------------------------------------------------------------------------------------------+
| THE FOUR EVIDENCE TIERS IN CONTINUOUS RESEARCH MODE                                                                           |
+-------------------+--------------------+------------------------+-------------------------------------------------------------+
| Evidence Tier     | Data Share         | Permitted Operations   | Epistemological Role                                        |
+-------------------+--------------------+------------------------+-------------------------------------------------------------+
| TRAIN             | First 50% of       | Feature discovery,     | Primary laboratory for hypothesis generation and initial   |
|                   | pre-holdout data   | parameter calibration  | alpha signal formulation.                                   |
+-------------------+--------------------+------------------------+-------------------------------------------------------------+
| [24h Embargo]     | 288 bars (24h)     | PURGED / UNUSED        | Eliminates serial autocorrelation and indicator spillover.  |
+-------------------+--------------------+------------------------+-------------------------------------------------------------+
| VALIDATION        | Next 25% of        | Hyperparameter tuning, | Controlled evaluation to discard overfitted candidates;     |
|                   | pre-holdout data   | model selection        | strictly quarantined from training.                         |
+-------------------+--------------------+------------------------+-------------------------------------------------------------+
| [24h Embargo]     | 288 bars (24h)     | PURGED / UNUSED        | Eliminates serial autocorrelation and indicator spillover.  |
+-------------------+--------------------+------------------------+-------------------------------------------------------------+
| ROLLING_OOS       | Final 25% of       | Read-only evaluation   | Chronological walk-forward test folds simulating live       |
|                   | pre-holdout data   | (no parameter fitting) | unseen performance prior to prospective testing.            |
+-------------------+--------------------+------------------------+-------------------------------------------------------------+
| [Sealed Cutoff]   | >= 2026-11-01 UTC  | SEALED / ISOLATED      | Immutable holdout boundary (t >= 1,793,491,200,000 ms).     |
+-------------------+--------------------+------------------------+-------------------------------------------------------------+
| PROSPECTIVE_OOS   | Forward live feed  | Real-time observation  | Forward-running prospective market evaluation without       |
|                   | from 2026-11-01    | (no optimization)      | gating or halting ongoing retrospective research.           |
+-------------------+--------------------+------------------------+-------------------------------------------------------------+
```

---

### 3. THE 24-HOUR EMBARGO BUFFER PROTOCOL

In financial time-series, overlapping indicator calculations (e.g., 50-period EMAs, 100-period volatility percentiles, 20-period Donchian channels) create persistent autocorrelation tails. If a validation partition begins immediately after a training partition, information from the training period leaks into the initial bars of the validation set.

To mathematically eliminate this leakage:
- A mandatory **$288\text{-bar embargo buffer}$ ($24\text{ hours}$ of 5m bars)** is excised between `TRAIN` and `VALIDATION`.
- An identical **$288\text{-bar embargo buffer}$** is excised between `VALIDATION` and `ROLLING_OOS`.
- Embargo bars are discarded completely; no indicators, features, or signals may span across the boundary.

---

### 4. SEALED PROSPECTIVE HOLDOUT BOUNDARY INVARIANT

The prospective holdout cutoff is anchored at:
$$t_{\text{holdout}} = 1,793,491,200,000\text{ ms} \quad (2026-11-01\text{ 00:00:00 UTC})$$

#### Strict Enforcement Rules:
1. **Zero Access for Retrospective Research:** Any experiment configured as `TRAIN`, `VALIDATION`, or `ROLLING_OOS` that accesses data timestamped at or after $t_{\text{holdout}}$ is rejected immediately with a fatal `HoldoutContaminationError`.
2. **One-Way Arrow of Information:** Information flows exclusively forward in time. Prospective data can never influence retrospective hypothesis generation or feature definition.
3. **Continuous Unblocked Collection:** Prospective observation feeds run continuously in the background, logging forward market behavior without delaying retrospective research experiments.

---

### 5. AUDIT & VERIFICATION MATRIX

| Partition Integrity Check | Verification Method | Enforcement Mechanism |
| :--- | :--- | :--- |
| **Chronological Ordering** | $t_{\text{train\_end}} < t_{\text{val\_start}} < t_{\text{oos\_start}}$ | `PartitionLeakageError` raised on overlap |
| **Embargo Completeness** | $\Delta t \ge 288 \times 300,000\text{ ms}$ | Automatic slice gap verification |
| **Holdout Boundary** | $\max(t) < 1,793,491,200,000\text{ ms}$ | `HoldoutContaminationError` raised on violation |
| **Cryptographic Provenance**| SHA-256 over raw OHLCV array bytes | Embedded in `DatasetFingerprint` |
| **Config Immutability** | Pydantic `frozen=True` + SHA-256 hash | Embedded in `ContinuousExperimentConfig` |
