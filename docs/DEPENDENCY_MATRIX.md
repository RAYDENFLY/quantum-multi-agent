# DEPENDENCY_MATRIX.md: Approved Minimal Local ML & Desktop Stack

## 1. Dependency Selection Philosophy

Every third-party package in **QUANTUM** must justify its RAM footprint, startup import time, and Windows native wheel availability (`win_amd64`). Zero cloud AI SDKs or paid API clients are included.

### 1.1 Approved Production Dependencies (`pyproject.toml`)

| Package | Version Constraint | License | Est. RAM Impact | Architectural Purpose & Justification |
| :--- | :---: | :---: | :---: | :--- |
| **`python`** | `>=3.11, <3.14` | PSF | `~32 MB` | Fast specializing adaptive interpreter, native `asyncio.TaskGroup`, and `tomllib`. |
| **`PySide6-Essentials`** | `>=6.7.0, <6.9.0` | LGPLv3 | `~75 MB` | Official Qt6 bindings (`QtCore`, `QtGui`, `QtWidgets`, `QtNetwork`) without the 250 MB bloat of `QtWebEngine`, `Qt3D`, or `QtMultimedia`. |
| **`qasync`** | `>=0.27.1` | BSD-2 | `< 1 MB` | Bridges Python's `asyncio` event loop into `QApplication` on a single OS thread. |
| **`pyqtgraph`** | `>=0.13.7` | MIT | `~12 MB` | Hardware-accelerated, NumPy-native candlestick, volume, oscillator, L2 depth, and equity curve plotting inside Qt6. |
| **`numpy`** | `>=2.0.0, <2.3.0` | BSD-3 | `~18 MB` | Fixed-capacity structured OHLCV ring buffers, L2 book arrays, and vectorized 48-feature extraction. |
| **`scipy`** | `>=1.13.0, <1.16.0` | BSD-3 | `~14 MB` | Required by `scikit-learn` and `lightgbm`; used for statistical anomaly Z-scores, rank percentiles, and PSI drift metrics. |
| **`scikit-learn`** | `>=1.5.0, <1.7.0` | BSD-3 | `~14 MB` | Used for `IsotonicRegression` / Platt probability calibration, `Ridge` baseline regression, walk-forward Brier/AUC metrics, and regime clustering. |
| **`lightgbm`** | `>=4.5.0, <5.0.0` | MIT | `~6 MB` | Primary fast C++ CPU gradient-boosted decision tree engine (`< 1 ms` single-row inference, `< 2 MB` per loaded booster). |
| **`joblib`** | `>=1.4.0` | BSD-3 | `< 2 MB` | Transitive dependency of `scikit-learn` used to serialize/deserialize lightweight probability calibrator objects (`calibrator.joblib`). |
| **`aiohttp`** | `>=3.10.0` | Apache-2.0 | `~14 MB` | Async HTTP/1.1 & WebSocket client with connection pooling for Bybit V5 and AsterDEX `/fapi/v1` public market data. |
| **`orjson`** | `>=3.10.0` | Apache/MIT | `~3 MB` | Rust-backed zero-copy JSON parser/serializer (`5x-10x` faster and lower memory allocation than stdlib `json` on 850-symbol bulk ticker payloads). |
| **`pydantic`** | `>=2.9.0` | MIT | `~12 MB` | Rust-backed (`pydantic-core`) strict data contract validation for all 5 agents, model manifests, and app settings. |
| **`aiosqlite`** | `>=0.20.0` | MIT | `~2 MB` | Non-blocking async wrapper over Python's built-in `sqlite3` (WAL mode). |
| **`psutil`** | `>=6.0.0` | BSD-3 | `~3 MB` | Real-time process RSS memory and CPU telemetry displayed in the bottom status bar and used to set `BELOW_NORMAL_PRIORITY_CLASS` on `train_worker.py`. |

**Total Estimated Desktop Runtime Import Footprint**: **`~205 MB`**, leaving `~95 MB` of headroom below the `300 MB` idle target for ring buffers, UI widgets, and SQLite WAL cache.

### 1.2 Optional Offline Experimentation Packages (`[project.optional-dependencies.research]`)
Not loaded by the desktop runtime process; optionally usable inside `train_worker.py` for offline benchmark comparisons:
* **`xgboost >= 2.1.0`** (`Apache-2.0`): Secondary GBDT benchmark for comparing against `lightgbm` during offline walk-forward research.
* **`hmmlearn >= 0.3.2`** (`BSD-3`): Optional Gaussian Hidden Markov Model fitter for offline regime research (if not installed, `ANALYST` uses built-in `scikit-learn` `GaussianMixture` + Markov transition matrix).

---

## 2. Development & Testing Dependencies (`[project.optional-dependencies.dev]`)

| Package | Version Constraint | Purpose |
| :--- | :---: | :--- |
| **`pytest`** | `>=8.3.0` | Core test runner. |
| **`pytest-asyncio`** | `>=0.24.0` | Async coroutine test fixtures for adapters, orchestrator, and SQLite writer. |
| **`pytest-qt`** | `>=4.4.0` | Headless/offscreen Qt widget interaction, signal verification, and keyboard navigation tests. |
| **`aioresponses`** | `>=0.7.6` | Deterministic mocking of `aiohttp` REST endpoints for Bybit and AsterDEX. |
| **`ruff`** | `>=0.7.0` | Fast Rust linter and formatter enforcing strict import boundaries and code hygiene. |
| **`mypy`** | `>=1.13.0` | Static type checking across all domain models, adapters, and Pydantic contracts. |

---

## 3. Explicitly Banned Dependencies & Infrastructure

To protect the low-resource desktop engineering constraints and the **Zero Paid AI Cost Policy**, the following packages and external services are **strictly forbidden**:

| Banned Dependency / Service | Reason for Prohibition | Approved Alternative Used |
| :--- | :--- | :--- |
| **Any Paid Cloud AI API (`xai-sdk`, `openai`, `anthropic`, `google-genai`)** | Violates the hard zero-recurring-API-cost mandate. | 100% local CPU `lightgbm` + `scikit-learn` + deterministic quantitative Python. |
| **Heavyweight Agent Frameworks (`langchain`, `llamaindex`, `autogen`, `crewai`)** | Designed for cloud prompt orchestration; adds `50-120 MB` of unused transitive dependencies. | Direct typed `PipelineOrchestrator` and `EventBus` in pure Python. |
| **Local Deep Learning / Weights (`torch`, `tensorflow`, `transformers`, `ollama`, `llama-cpp-python`)** | Consumes `2-16 GB` RAM/VRAM, requires GPU acceleration, and overfits tabular financial features. | Compact CPU `lightgbm` (`< 2 MB` per model, `< 1 ms` inference). |
| **Electron / Tauri-WebView / Next.js / React** | Spawns Chromium/Edge WebView2 renderer processes consuming `450-900 MB` RAM at idle. | `PySide6-Essentials` + `pyqtgraph`. |
| **`PySide6` (Full Meta-Package with `QtWebEngine`)** | Bundles Chromium inside Qt (`+200 MB` disk/RAM overhead). | `PySide6-Essentials` only. |
| **`pandas` (in Desktop Runtime)** | High memory overhead (`~60+ MB` import + object overhead when mutating candle rows every tick). | Pre-allocated `numpy` structured ring buffers (`CANDLE_DTYPE`) and `.npz` archives. |
| **`ccxt` (Full Monolithic Import)** | Importing `ccxt` loads metadata/classes for 100+ unused exchanges (`+65-90 MB` RAM) and lacks fine-grained AsterDEX weight header control. | Dedicated `BybitAdapter` & `AsterDexAdapter` on `aiohttp` + `orjson`. |
| **PostgreSQL / Redis / Docker** | Requires background daemon services, container virtualization overhead, and manual user setup. | Embedded `sqlite3` in `WAL` mode + in-memory `EventBus`. |
| **`web3` / `eth-account` / Wallet Signers** | System operates strictly in **PAPER TRADING ONLY** mode; no on-chain signing or live order placement is permitted. | Public unauthenticated market data + local `PaperSimulator`. |
