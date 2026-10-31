# TESTING_STRATEGY.md: Engineering Verification & Local ML Research Validation

## 1. Software Engineering Verification Pyramid

Every module in **QUANTUM** is verified through an automated `pytest` + `pytest-asyncio` + `pytest-qt` suite (`tests/`).

| Test Layer | Target Modules | Key Assertions & Edge Cases | Target Coverage |
| :--- | :--- | :--- | :---: |
| **1. Unit & Anti-Leakage Feature Tests (`tests/unit/`)** | `indicators`, `features`, `labels`, `splitter`, `screener`, `classifier`, `queue` | Verify exact mathematical accuracy of all 48 features; prove **zero future lookahead leakage** by mutating bars at $t > t_{\text{eval}}$ and asserting `extract_feature_vector(t_eval)` is bit-for-bit identical; verify dynamically computed purge windows ($1.5 \times H_{\max}$) and zero index overlap between train/val/test splits. | `>= 95%` |
| **2. Exchange Adapter Tests (`tests/adapters/`)** | `BybitAdapter`, `AsterDexAdapter` | Replay recorded HTTP JSON fixtures and WebSocket frames (`snapshot` + `delta` ticker merges on Bybit; 3-endpoint bulk merge on AsterDEX); verify reverse-chronological kline sorting, crossed-book rejection (`bid1 >= ask1`), and HTTP `429`/`418` backoff. | `>= 90%` |
| **3. Local ML Contract & Registry Tests (`tests/ml/`)** | `contracts.py`, `registry.py`, `calibration.py`, `drift.py` | Feed `NaN`/`Inf` features, mismatched `feature_schema_hash`, corrupted `.lgb` SHA-256 files, and inverted SL/TP geometries; assert `100%` result in immediate `SKIP` or explicit `FALLBACK_RULE_ONLY` with zero crashes; verify validation-only threshold tuning. | `100%` of contract rules |
| **4. Orchestration & Chaos Recovery (`tests/agents/test_chaos.py`)** | `PipelineOrchestrator`, `EventBus`, `SQLiteWriter`, `train_worker` | Inject simulated `> 50ms` inference delays, mid-pipeline bias contradictions, WebSocket disconnects during an active position, training subprocess `SIGTERM` aborts, and app restart state rehydration. | `>= 90%` |
| **5. Deterministic Risk Engine Tests (`tests/unit/test_risk.py`)** | `RiskEngine`, `PortfolioState` | Boundary-test all 12 risk gates individually and in combination: lot-step rounding down, fee-adjusted $R:R_{\text{net}} < 1.80$ veto, daily loss limit breach, symbol/total exposure caps, and loss-streak cooldown enforcement. | `100%` branch coverage |
| **6. Paper Execution & Accounting Tests (`tests/execution/`)** | `PaperSimulator`, `FundingCalculator`, `Accounting` | Verify L2 orderbook depth walk VWAP + slippage, partial fills on resting limit orders, same-bar TP/SL collision pessimistic tie-break, gap-through open fill, maker vs. taker fee deduction, positive vs. negative 8h funding settlements, TP1 breakeven ratchet, and exact equity conservation. | `100%` accounting accuracy |
| **7. UI Responsiveness & Accessibility (`tests/ui/`)** | `PySide6` Workspaces 1-7, `theme.py` | `pytest-qt` tests verifying all 7 workspaces render Empty/Loading/Error states (`R-27`), keyboard `Alt+1..7` and `Tab`/`Escape` navigation works (`R-32`), contrast checker passes all theme token pairs (`R-25`), and 4 Hz table bursts keep main-thread frame times `< 12 ms`. | All 7 pages |

---

## 2. Memory, CPU & Latency Profiling on Low-Resource Hardware

All performance benchmarks are executed against the **Low-Resource Reference Hardware Profile** (4 cores / 4 threads, 12 GB DDR4 RAM, mechanical HDD 5400/7200 RPM, Windows 10/11 x64).

### 2.1 Standardized Benchmark Protocol
* **Warm-Up Period**: Exactly 50 full pipeline inference cycles (or 1 full 60-second market scan) executed before sampling to eliminate JIT/OS page fault bias.
* **Repetition Count**: 1,000 consecutive candidate inference cycles for latency; 30 minutes continuous operation for RAM stability.
* **Reported Statistics**: Latency reported as Median (P50), 95th Percentile (P95), and 99th Percentile (P99). Memory reported as Peak Resident Set Size (RSS) sampled every 1.0s via `psutil`.

### 2.2 Five Operational Acceptance Tests (Acceptance Targets)

1. **Test A: Desktop Idle (`bench_idle.py`)**:
   * Desktop application open on `Overview`, WebSocket connected to Bybit and AsterDEX, SQLite WAL initialized, 4 resident models loaded.
   * **Acceptance Target**: Peak RSS $\le 300\text{ MB}$ (Engineering Estimate: ~205-240 MB), CPU $< 3\%$.
2. **Test B: Active Market Scanning (`bench_scanning.py`)**:
   * Recurring 60-second universe discovery across ~850 pairs, Stage A-D vectorized indicator compute, 4 Hz UI table refreshes.
   * **Acceptance Target**: Stage A-D compute duration $< 450\text{ ms}$; main-thread Qt frame block $< 12\text{ ms}$ (P99); Peak RSS $\le 340\text{ MB}$.
3. **Test C: Local Inference Burst (`bench_inference.py`)**:
   * 5 top candidates extracted and evaluated sequentially through `SCOUT -> ANALYST -> SNIPER -> RISK` with `num_threads=1`.
   * **Acceptance Target**: Single-agent inference $\le 2.5\text{ ms}$ (P95); full 4-agent pipeline latency $\le 15.0\text{ ms}$ (P95).
4. **Test D: Historical Data Harvesting on Mechanical HDD (`bench_harvesting.py`)**:
   * Sequential REST pagination across 50 pairs writing compressed `.npz` files to mechanical HDD.
   * **Acceptance Target**: Buffered sequential disk writes; SQLite WAL checkpointing does not block UI event loop; Desktop RAM $\le 250\text{ MB}$.
5. **Test E: Offline Model Training on Mechanical HDD (`bench_training.py`)**:
   * `train_worker.py` subprocess running walk-forward training on 250,000 historical bars with `BELOW_NORMAL_PRIORITY_CLASS` and `psutil.IOPRIO_LOW`.
   * **Acceptance Target**: Subprocess Peak RSS $\le 550\text{ MB}$; zero Windows swap thrashing; desktop GUI maintains responsive interaction ($\ge 45\text{ FPS}$) with zero freeze.

---

## 3. Quantitative ML Research Validation & Ablation Protocol

The architecture **never assumes** machine learning automatically improves trading performance over deterministic rules. Every trained model and agent stage must prove its net value out-of-sample after realistic fees, spread, slippage, and funding.

### 3.1 Five-Tier Baseline & Ablation Matrix (`src/quantum/analytics/ablation.py`)

To distinguish between agents that rank opportunities and agents that condition/filter trades, and to measure trade coverage across each stage, all 5 tiers are evaluated over identical chronological walk-forward out-of-sample windows:

| Tier ID | Configuration Architecture | Primary Agent Function | Measured Trade-Off / Scientific Purpose |
| :--- | :--- | :--- | :--- |
| **Tier 1: `RULE_ONLY` Baseline** | Stage A-D deterministic scanner (`Score >= 75`) directly triggers trades with fixed ATR stops ($1.5 \times \text{ATR}_{15m}$) and targets ($2.0R / 3.2R$) passed to `RiskEngine` and deterministic `Banker` (**Zero ML models**). | Ground-truth quantitative benchmark. | Establishes baseline trade frequency, net expectancy, and fee drag without any machine learning. |
| **Tier 2: `SCOUT_ONLY`** | Stage A-D scanner $\rightarrow$ `SCOUT` LightGBM ranks and filters candidates by positive excursion probability $\rightarrow$ fixed ATR stops/targets $\rightarrow$ `RiskEngine` $\rightarrow$ deterministic `Banker`. | Candidate Ranking & Quality Floor. | Tests whether ML ranking of scanner candidates improves win rate and net expectancy compared to deterministic Stage D scoring alone. |
| **Tier 3: `SCOUT_ANALYST`** | `SCOUT` (Ranking) $\rightarrow$ `ANALYST` (Regime Classification & Meta-Labeling) $\rightarrow$ fixed ATR stops/targets $\rightarrow$ `RiskEngine` $\rightarrow$ deterministic `Banker`. | Contextual Conditioning & Invalidation Anchoring. | Evaluates whether higher-timeframe regime awareness and structural swing invalidation reduces drawdowns without causing funnel collapse. |
| **Tier 4: `SCOUT_ANALYST_SNIPER`** | `SCOUT` (Ranking) $\rightarrow$ `ANALYST` (Regime Conditioning) $\rightarrow$ `SNIPER` (Barrier EV Optimization across candidate TP/SL geometries) $\rightarrow$ `RiskEngine` $\rightarrow$ deterministic `Banker`. | Target Geometry & Expected Net Return Optimization. | Tests whether dynamically selecting barrier ratios via ML outcome models outperforms fixed ATR target multiples. |
| **Tier 5: `QUANTUM_5_AGENT`** | Full 5-agent pipeline: `SCOUT` + `ANALYST` + `SNIPER` + `RISK` + `BANKER` (with 5m Exit Hazard ML Classifier enabled) + leave-one-out ablations (`NO_SCOUT_ML`, `NO_ANALYST_ML`, etc.). | Full Dynamic Entry & Exit Lifecycle. | Quantifies whether early exit ML during position deterioration improves net expectancy over deterministic trailing stops alone. |

### 3.2 Trade Coverage, Rejection Tracking & Funnel Balance
To guarantee that the multi-agent pipeline discovers sufficiently frequent trading opportunities without over-filtering, the ablation engine tracks:
* **Trade Coverage Ratio**: $\frac{\text{Trades Executed}}{\text{Stage C Qualified Candidates}}$ (Target: $15\% - 35\%$).
* **Rejection Reason Pareto Breakdown**: Exact accounting of why candidates did not trade (e.g., Scout probability cutoff, Analyst regime chop, Sniper negative EV, Risk exposure limit, Risk spread limit).
* **Trade Frequency**: Minimum target of **`3 to 8 closed trades per active pair per week`** under normal market conditions.

### 3.3 Walk-Forward Validation & Promotion Rules
1. **Dynamic Horizon Purge & Embargo**:
   * Evaluated across at least 3 sequential out-of-sample folds covering Bull, Bear, and Chop regimes.
   * Purge window dynamically calculated as $\text{PurgeDuration} = 1.5 \times (H_{\max} + \text{MaxEntryDelay})$ to eliminate all label overlap.
2. **Validation-Only Threshold Tuning**:
   * Decision thresholds ($p_{\text{scout}}$, $p_{\text{analyst}}$, $\mathbb{E}[R_{\text{net}}]$) are selected exclusively on the Validation fold using Precision-Recall trade-offs subject to the minimum trade frequency constraint.
   * All thresholds are **frozen** before OOS evaluation. Zero tuning on OOS test data is permitted.
3. **Automatic Promotion Gate**:
   * An agent ML model is promoted to `PRODUCTION` only if its Out-of-Sample Net Expectancy $E_R > \text{RULE\_ONLY } E_R$, Profit Factor $\ge 1.15$, and Brier calibration score $< 0.23$. If an ML model fails to beat `RULE_ONLY`, the system defaults that agent to `FALLBACK_RULE_ONLY`.
4. **Statistical Significance Gate**:
   * Results are marked `PRELIMINARY (INSUFFICIENT SAMPLE)` until $N \ge 50$ out-of-sample closed trades across at least 2 market regimes.

---

## 4. Mandatory Quantitative & ML Calibration Metrics

Every evaluation run and live paper trading session computes and reports:

1. **Trading Performance Metrics (Net of Fees, Spread, Slippage & Funding)**:
   * **Net Expectancy per Trade ($E_R$ and $E_{\$}$)**:
     $$E_R = \left(P_{\text{win}} \times \overline{R}_{\text{win\_net}}\right) - \left(P_{\text{loss}} \times |\overline{R}_{\text{loss\_net}}|\right)$$
   * **Net Profit Factor ($\text{PF}_{\text{net}}$)**:
     $$\text{PF}_{\text{net}} = \frac{\sum \text{NetWinningTrades}_{\text{USDT}}}{\left|\sum \text{NetLosingTrades}_{\text{USDT}}\right|}$$
   * **Maximum Drawdown ($\text{MDD}_{\%}$)**, **Win Rate ($\%$)**, and **Trade Frequency (trades/day)**.
2. **Execution Friction Attribution**:
   * **Fee Drag Ratio**: $\frac{\sum \text{TradingFees}_{\text{USDT}}}{|\sum \text{GrossPnL}_{\text{USDT}}|}$
   * **Slippage Drag (Mean & P95 bps)**: Realized fill price vs. mid-price at order trigger.
   * **Funding Impact ($ / R)**: Net funding paid vs. received across holding periods.
3. **ML Calibration & Operational Telemetry**:
   * **Brier Calibration Score**: $\frac{1}{N} \sum_{i=1}^N (p_i - y_i)^2$.
   * **ROC-AUC & PR-AUC** on out-of-sample folds.
   * **Feature Drift PSI (Population Stability Index)**.
   * **CPU Inference Latency (P50 / P95 / P99 ms)** and **Desktop Runtime RAM (MB)**.

---

## 4. Mandatory Quantitative & ML Calibration Metrics

Every evaluation run and live paper trading session computes and reports:

1. **Trading Performance Metrics (Net of Fees, Spread, Slippage & Funding)**:
   * **Net Expectancy per Trade ($E_R$ and $E_{\$}$)**:
     $$E_R = \left(P_{\text{win}} \times \overline{R}_{\text{win\_net}}\right) - \left(P_{\text{loss}} \times |\overline{R}_{\text{loss\_net}}|\right)$$
   * **Net Profit Factor ($\text{PF}_{\text{net}}$)**:
     $$\text{PF}_{\text{net}} = \frac{\sum \text{NetWinningTrades}_{\text{USDT}}}{\left|\sum \text{NetLosingTrades}_{\text{USDT}}\right|}$$
   * **Maximum Drawdown ($\text{MDD}_{\%}$)**, **Win Rate ($\%$)**, and **Trade Frequency (trades/day)**.
2. **Execution Friction Attribution**:
   * **Fee Drag Ratio**: $\frac{\sum \text{TradingFees}_{\text{USDT}}}{|\sum \text{GrossPnL}_{\text{USDT}}|}$
   * **Slippage Drag (Mean & P95 bps)**: Realized fill price vs. mid-price at order trigger.
   * **Funding Impact ($ / R)**: Net funding paid vs. received across holding periods.
3. **ML Calibration & Operational Telemetry**:
   * **Brier Calibration Score**: $\frac{1}{N} \sum_{i=1}^N (p_i - y_i)^2$ (verifying predicted probabilities match empirical outcomes).
   * **ROC-AUC & PR-AUC** on out-of-sample folds.
   * **Feature Drift PSI (Population Stability Index)**.
   * **CPU Inference Latency (P50 / P95 / P99 ms)** and **Desktop Runtime RAM (MB)**.
