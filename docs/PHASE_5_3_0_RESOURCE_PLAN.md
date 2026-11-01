# QUANTUM PHASE 5.3.0 - COMPUTATIONAL RESOURCE PLAN

**Author:** Senior Infrastructure Architect & Quantitative Systems Engineer  
**Date:** 2026-11-01  
**Repository:** https://github.com/RAYDENFLY/quantum-multi-agent  
**Scope:** Memory Budget, CPU Thread Caps, Execution Schedules, and Hardware Constraints  
**Policy Status:** ACTIVE & MANDATORY  

---

## 1. TARGET HARDWARE PROFILES

QUANTUM is engineered for local-first execution on resource-constrained commodity developer machines without cloud dependencies:

| Specification | Primary Development Profile | Minimum Supported Low-Resource Profile |
|---|---|---|
| **CPU Architecture** | Intel Core i7-7700HQ (4 cores / 8 threads @ 2.80 GHz) | AMD A6-9225 (2 cores / 2 threads @ 2.60 GHz) |
| **System Memory (RAM)** | 16 GB DDR4 | 12 GB DDR4 |
| **Storage Architecture** | NVMe SSD | 5400 RPM Mechanical HDD |
| **GPU Acceleration** | NVIDIA GeForce GTX 1050 Ti (4 GB VRAM) | Integrated Radeon R4 (Shared VRAM) |
| **Execution Policy** | Local CPU-first execution | Local CPU-first execution (Strict serial) |

---

## 2. STRICT RESOURCE BUDGETS

To guarantee that the desktop application UI and background OS services remain responsive, the following resource caps are strictly enforced:

$$\mathbf{Maximum \quad Baseline \quad Training \quad Memory \quad Budget: \quad 1,024 \quad MB \quad (1.0 \quad GB)}$$

### Resource Allocation Caps

1. **Working Memory (RSS Cap):**
   - Maximum Resident Set Size for any single specialist training workload: **1.0 GB**.
   - Peak allocation during 100-tree Random Forest fitting on 230,000 samples: $\approx 450$ MB.
   - Peak allocation during LightGBM fitting on 230,000 samples: $\approx 300$ MB.
2. **CPU Thread Limits:**
   - Multi-threading is strictly capped to `n_jobs=2` for all scikit-learn and LightGBM estimators.
   - Uncapped thread allocation (`n_jobs=-1`) is strictly prohibited, as it would exhaust CPU cores and freeze the PySide6 desktop GUI.
3. **GPU Independence:**
   - All Phase 5.3 baseline models (Logistic Regression, Random Forest, LightGBM) run on CPU only.
   - GPU execution (CUDA) is not required, ensuring identical cross-platform reproducibility on machines without dedicated graphics cards.

---

## 3. SEQUENTIAL INSTRUMENT TRAINING PROTOCOL

To prevent memory bloat and disk I/O thrashing on mechanical hard drives:

$$\text{Active Instruments Loaded in Memory} = 1$$

1. **Serial Batching:**
   The 11 specialist models are trained in strict sequential order:
   $$\text{ADA} \longrightarrow \text{XRP} \longrightarrow \text{BTC} \longrightarrow \dots \longrightarrow \text{LTC}$$
2. **Deterministic Garbage Collection:**
   Upon completion of each specialist's 5-fold walk-forward validation:
   - DataFrames and model instances are dereferenced.
   - Explicit garbage collection (`gc.collect()`) is invoked.
   - Resident memory (`process.memory_info().rss`) is logged before the next instrument is loaded.
3. **Streaming Parquet Loads:**
   Data is loaded per-instrument and per-partition directly from year-partitioned Parquet files. Raw layers and unneeded timeframes (1h, 15m) are never loaded into RAM during 5m specialist training.

---

## 4. TIMEOUT & ARTIFACT SAFEGUARDS

1. **Training Timeout Policy:**
   - Maximum allowed training duration per specialist fold: **300 seconds (5 minutes)**.
   - Maximum total duration per specialist model across all 5 folds: **1,200 seconds (20 minutes)**.
   - If an estimator exceeds the timeout threshold, execution is gracefully halted and logged as `TIMEOUT_ABORT`.
2. **Atomic Artifact Writes:**
   - Model manifests, preprocessor states, and evaluation reports must be written to temporary staging files (`.tmp`) before atomic renaming (`os.replace`).
   - This prevents partial or corrupted artifacts in the event of an unexpected process termination.
3. **Crash Consistency & SHA-256 Signatures:**
   - Every saved artifact is immediately accompanied by a `.sha256` checksum file.
   - The [ModelRegistry](file:///d:/quantum-multi-agent/src/quantum/ml/registry.py) validates the SHA-256 hash before loading any model into memory for inference.
