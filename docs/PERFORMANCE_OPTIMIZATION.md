# PERFORMANCE_OPTIMIZATION.md: Resource Efficiency & Zero-Cost Local ML Architecture

## 1. Zero Operating Cost Policy

**QUANTUM** operates with **$0.00 mandatory recurring API or cloud AI expenditure**:
* **Market Data**: 100% free public REST and WebSocket feeds from Bybit V5 and AsterDEX.
* **Agent Intelligence (`SCOUT`, `ANALYST`, `SNIPER`, `BANKER`)**: 100% local CPU machine learning (`LightGBM` + `scikit-learn`) and deterministic quantitative algorithms.
* **Model Training & Walk-Forward Validation**: Executed locally on the user's CPU via the isolated `train_worker.py` subprocess.
* **Optional Paid Services**: None required. If a user optionally chooses to run the application on a rented cloud VPS or import external third-party historical CSV/Parquet archives, that is entirely optional and never a system dependency.

---

## 2. Rigorous Benchmark Claims Classification

To maintain scientific integrity, all numerical performance claims are formally classified into one of three verified tiers:
* **Measured Result**: Empirically measured on designated reference hardware under controlled test harnesses.
* **Engineering Estimate**: Analytically derived based on algorithmic complexity, data structures, and memory sizing math.
* **Acceptance Target**: Contractual quality gates that must be satisfied during CI/CD and pre-release hardware verification.

### 2.1 Benchmark Claims Classification Matrix

| Performance Metric | Numerical Claim | Benchmark Classification | Empirical Baseline / Theoretical Basis | Verification Method & Target Acceptance Gate |
| :--- | :---: | :---: | :--- | :--- |
| **Pipeline Latency (End-to-End)** | `1.2 - 3.5 ms` | **Engineering Estimate** | Vectorized NumPy feature math (~0.8 ms) + 4x single-row `LightGBM` OpenMP inference (`num_threads=1`, ~0.4 ms each) + Python risk checks (~0.2 ms). | 1,000 repetitions with synthetic and live vectors. Target Gate: `< 5.0 ms` P95 (`AC-2.4`). |
| **Per-Agent Inference Latency** | `0.3 - 1.5 ms` | **Engineering Estimate** | Single-tree evaluation across shallow decision trees (depth $\le 5$, 31 leaves, 48 features) with resident in-memory C++ pointers. | `time.perf_counter_ns()` over 500 iterations per agent (`AC-2.4`). |
| **Desktop Idle RAM** | `~205 MB` | **Engineering Estimate** | PySide6 base runtime (~120 MB) + SQLite WAL cache (~32 MB) + 4 resident boosters (~10 MB) + UI models/buffers (~40 MB). | Measured via `psutil.Process().memory_info().rss`. Target Gate: `le 300 MB` (`AC-2.1`). |
| **Active Scanning / Trading RAM** | `~272 MB` | **Engineering Estimate** | Idle baseline (205 MB) + 25 active WebSocket ring buffers (35 MB) + Stage A-D candidate caches (25 MB) + pending orders (7 MB). | 60-minute soak test under 850-contract load. Target Gate: `le 340 MB` (`AC-2.2`). |
| **Offline Training Peak RAM** | `350 - 550 MB` | **Engineering Estimate** | 250,000 rows x 48 features in `float32` (48 MB) + uint8 histogram bins (12 MB) + LightGBM internal trees/gradients (~180 MB) + OS buffer overhead. | Process memory peak tracking via `psutil` in `train_worker.py`. Target Gate: `le 550 MB` (`AC-2.3`). |
| **Full-Universe Scan Duration** | `< 300 ms` | **Acceptance Target** | Vectorized NumPy array slicing across 850 cached ticker/kline arrays without Python row loops. | Stage A-D benchmark test harness. Target Gate: `< 500 ms` for 850 contracts (`AC-3.1`). |
| **UI Main Thread Latency** | `< 12 ms` (P99) | **Acceptance Target** | Offloading all network I/O, database writes, and feature math to background threads; 4 Hz throttled UI model updates. | Qt event loop lag timer monitoring. Target Gate: 60 FPS UI responsiveness (`AC-2.4`). |

### 2.2 Standardized Benchmark Reproducibility Protocol

All formal benchmark measurements must adhere to the following repeatable protocol:
1. **Target Hardware Reference Profile**:
   * CPU: 4 cores / 8 threads (e.g., Intel Core i5-8250U / AMD Ryzen 3 3100 or equivalent).
   * System RAM: 12 GB physical RAM (representative of low-resource workstations).
   * Storage: Mechanical Hard Disk Drive (5400/7200 RPM SATA HDD) to verify worst-case I/O behavior.
   * OS: Windows 10/11 x64, clean boot with standard background services.
2. **Warmup & Iteration Count**:
   * JIT and CPU cache warmup: Minimum 50 unrecorded warmup cycles before timing begins.
   * Sample size: Exactly 1,000 consecutive test repetitions for latency benchmarks; continuous 60-minute duration for soak and RAM tests.
3. **Statistical Reporting**:
   * Latency metrics must report Median (P50), 95th Percentile (P95), and 99th Percentile (P99). Mean alone is rejected due to skewness.
   * Memory metrics must report baseline RSS, active peak RSS, and 60-minute post-warmup memory drift rate (`MB/hour`).

---

## 3. Separated Runtime vs. Offline Training Resource Architecture

### 3.1 Resource Allocation Matrix

| Resource Dimension | Desktop Runtime (`quantum.main` + Live CPU Inference) | Offline Training Subprocess (`quantum.ml.train_worker`) | Mechanical HDD & Low-Resource Safeguards |
| :--- | :---: | :---: | :--- |
| **Idle RAM** | `~205 MB` (Target $\le 300\text{ MB}$) | `0 MB` (Not running when idle) | Subprocess exits completely upon finishing training, releasing 100% of memory. |
| **Active Scanning RAM** | `~272 MB` (Target $\le 340\text{ MB}$) | `350 - 550 MB` (Strict ceiling) | Training uses sequential 1-model-at-a-time execution with `float32` matrices and aggressive `gc.collect()`. |
| **CPU Utilization** | `1% - 3%` idle; `8% - 14%` for 250ms during 60s scan | `25% - 50%` (`max(1, cores // 2)` threads) | `train_worker.py` runs with `psutil.BELOW_NORMAL_PRIORITY_CLASS` to keep desktop UI responsive. |
| **Disk I/O Profile** | SQLite WAL append-only (`PRAGMA synchronous = NORMAL`) | Sequential buffered `.npz` reads/writes (`psutil.IOPRIO_LOW`) | Low I/O priority prevents mechanical HDD head thrashing, preserving live database responsiveness. |

### 3.2 Five Core Runtime Memory Optimizations
1. **Strict Prohibition of Unbounded Collections**:
   * Every in-memory queue (`EventBus`, `aiosqlite` writer queue, `StageD` candidate queue), UI activity log (`collections.deque(maxlen=250)`), and OHLCV cache (`KlineRingBuffer(capacity=500)`) has a hard-coded upper bound.
   * No `pandas` DataFrames are instantiated in the desktop runtime process; all indicator and feature math operates on pre-allocated `numpy.ndarray` views.
2. **`__slots__` on All High-Frequency Dataclasses**:
   * `NormalizedTicker`, `MessageEnvelope`, `ScannerCandidate`, and `PaperOrderEvent` declare `@dataclass(frozen=True, slots=True)`, cutting per-instance Python dictionary overhead by ~55%.
3. **Single-Thread OpenMP Inference (`num_threads=1`)**:
   * Calling `LightGBM` `Booster.predict()` on a single `(1, 48)` `float32` array with default multi-threading wastes CPU cycles waking up OpenMP worker threads. Passing `num_threads=1` in `predict()` reduces single-row latency from `~4 ms` down to `~0.4 ms` and prevents CPU thread contention with the Qt event loop.
4. **Lazy UI Workspace Initialization & Chart Downsampling**:
   * The `Market` candlestick chart (`pyqtgraph`) and `Analytics` equity curve only construct OpenGL/QPainter vertex arrays when their workspace tab is visible (`QStackedWidget.currentChanged`).
   * Candlestick rendering caps visible bars to `300` at a time (`setClipToView(True)`, `setDownsampling(auto=True, mode='peak')`).
5. **Periodic Garbage Collection & Memory Telemetry**:
   * A lightweight health monitor runs every 60 seconds using `psutil.Process().memory_info().rss`.
   * If RSS exceeds `310 MB`, the cache manager trims Tier 2 inactive hot symbols from `60` down to `35` and runs `gc.collect(generation=1)`.

---

## 4. Mechanical HDD and Low-Resource (12 GB RAM) Safeguards

To prevent system freeze or memory swap thrashing on 12 GB RAM computers with mechanical HDDs:

1. **Process Priority & I/O Priority Clamping**:
   * The training subprocess is spawned with:
     ```python
     p = psutil.Process()
     p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
     try:
         p.ionice(psutil.IOPRIO_LOW)  # Avoid starving SQLite WAL writer
     except (AttributeError, psutil.Error):
         pass
     ```
2. **Sequential Buffered Disk I/O**:
   * Training data is persisted in compressed NumPy `.npz` chunks (e.g. 50 MB per partition) and read sequentially. Random disk seeks across thousands of small files are strictly prohibited.
3. **SQLite WAL Checkpointing Protection**:
   * SQLite uses `PRAGMA synchronous = NORMAL` and `PRAGMA wal_autocheckpoint = 1000`. Long WAL checkpoints run on an async background worker so the live paper trading engine is never blocked by disk write latency.
4. **Memory Paging & Swap Protection**:
   * Before launching training, `train_worker.py` verifies that available physical system RAM is at least `1.5 GB`. If available RAM is below this threshold, training halts gracefully with an explicit UI notification rather than forcing the OS into virtual memory swapping.
