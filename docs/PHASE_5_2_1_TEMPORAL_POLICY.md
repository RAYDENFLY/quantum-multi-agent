# QUANTUM PHASE 5.2.1 - REVISED TEMPORAL RESEARCH POLICY

**Author:** Senior Quantitative Systems Architect & Research Governance Director  
**Date:** 2026-11-01  
**Repository:** https://github.com/RAYDENFLY/quantum-multi-agent  
**Scope:** Reclassification of Observed Data, Prospective Holdout Specification, and Boundary Rules  
**Policy Status:** ACTIVE & BINDING  

---

## 1. RECLASSIFICATION OF OBSERVED RESEARCH DATA

Because the historical period from May 1, 2026 through October 31, 2026 was evaluated during Phase 5.2 target labeling and sensitivity analysis, its statistical distribution is now known to researchers and logged in the repository.

### Governing Principles
1. **Preservation of Research Record:**
   All Phase 5.2 deliverable reports, logs, and artifacts are preserved without alteration. No data or reports are deleted.
2. **Reclassification:**
   The partition previously designated as `FINAL_HOLDOUT` (`2026-05-01 00:00:00.000` to `2026-10-31 23:59:59.999 UTC`) is formally reclassified as:
   $$\mathbf{VALIDATION\_OBSERVED \quad (\text{Previously Observed Research Data})}$$
   This partition may be used for retrospective stress testing, feature cross-validation, and out-of-sample backtesting extensions, but it can never be treated as an untouched blind holdout.

---

## 2. SPECIFICATION OF NEW PROSPECTIVE UNTOUCHED HOLDOUT

To restore true, uncontaminated out-of-sample statistical power, QUANTUM establishes a **Prospective Untouched Holdout**.

### Prospective Holdout Boundaries
- **Partition Identifier:** `PROSPECTIVE_HOLDOUT`
- **Start UTC:** `2026-11-01 00:00:00.000 UTC` (`1793491200000`)
- **End UTC:** `2027-04-30 23:59:59.999 UTC` (`1809129599999`)
- **Required Duration:** 181 calendar days (approx. 6 months)
- **Data Source:** Future live continuous ingestion or forward paper trading execution.

### Structural Guarantee of Prospective Isolation
Because the repository's current simulation and operational time is `2026-11-01`, candles spanning from November 2026 to April 2027 do not exist in the downloaded historical Parquet store. It is physically and mathematically impossible for any algorithm, researcher, or script to inspect, leak, or optimize against this period.

---

## 3. MASTER TEMPORAL PARTITION ARCHITECTURE

| Partition Identifier | Start UTC | End UTC | Millisecond Start | Millisecond End | Research Status | Allowed Operations |
|---|---|---|---|---|---|---|
| **PRE_DEVELOPMENT** | Listing Date | 2023-10-31 23:59:59.999 | $0$ | `1698796799999` | In-Sample Warm-Up | Indicator warm-up calculation only |
| **DEVELOPMENT** | 2023-11-01 00:00:00.000 | 2025-10-31 23:59:59.999 | `1698796800000` | `1761955199999` | Primary In-Sample Training | Feature selection, model training, parameter search |
| **VALIDATION** | 2025-11-01 00:00:00.000 | 2026-04-30 23:59:59.999 | `1761955200000` | `1777593599999` | Primary Out-of-Sample Tuning | Hyperparameter tuning, target validation, walk-forward tests |
| **VALIDATION_OBSERVED** | 2026-05-01 00:00:00.000 | 2026-10-31 23:59:59.999 | `1777593600000` | `1793491199999` | Historical Secondary Validation | Secondary model evaluation, out-of-sample stress testing |
| **PROSPECTIVE_HOLDOUT** | 2026-11-01 00:00:00.000 | 2027-04-30 23:59:59.999 | `1793491200000` | `1809129599999` | **Strict Untouched Holdout** | **LOCKED.** Unlocked only for final blind model evaluation |

---

## 4. CODE-LEVEL ENFORCEMENT & PREVENTATIVE SAFEGUARDS

1. **Dedicated Development & Validation Filtering:**
   In [temporal_split.py](file:///d:/quantum-multi-agent/src/quantum/features/temporal_split.py), a dedicated convenience selector is implemented:
   ```python
   TemporalPartitionManager.filter_development_and_validation(df)
   ```
   This method strictly slices `df` to `1698796800000 <= open_time_ms <= 1777593599999`. It automatically excludes Pre-Development warm-up bars, excludes `VALIDATION_OBSERVED`, and excludes all future holdouts.

2. **Holdout Access Lock:**
   Any attempted read operation on `PROSPECTIVE_HOLDOUT` raises a `PermissionError` unless an explicit verification token is passed.

3. **Causal Transformer Rules:**
   All scikit-learn transformers, scalers, and dimensionality reduction tools must call `.fit()` exclusively on `DEVELOPMENT`. Applying transformers to `VALIDATION` or subsequent partitions must use `.transform()` only.
