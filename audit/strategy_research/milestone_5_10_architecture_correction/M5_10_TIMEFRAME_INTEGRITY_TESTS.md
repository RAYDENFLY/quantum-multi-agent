# QUANTUM — MILESTONE 5.10
## TIMEFRAME INTEGRITY & CAUSAL EXECUTION TESTS SPECIFICATION

---

### 1. Document Overview
- **Document Identifier:** `audit/strategy_research/milestone_5_10_architecture_correction/M5_10_TIMEFRAME_INTEGRITY_TESTS.md`
- **Associated Test Suite:** [`tests/unit/test_milestone_5_10_architecture_contract.py`](file:///d:/quantum-multi-agent/tests/unit/test_milestone_5_10_architecture_contract.py)
- **Research Branch:** `research/quantum-next-3pct`
- **Scope:** Defines the test specifications and mathematical assertions that guarantee timeframe integrity, prevent silent data substitution, and enforce causal execution.

---

### 2. Timeframe Integrity Assertions

#### Test 1: Silent Timeframe Downsampling Rejection
- **Objective:** Guarantee that if a script attempts to pass a daily (`1D`) or hourly (`1h`) dataset to a strategy declared with `execution_timeframe = "5m"`, the engine immediately halts with a descriptive exception before running any backtest iterations.
- **Assertion:**
  $$\text{validate\_input\_data\_timeframe}(C_{\text{contract}}, D_{\text{dataset}}) \implies \begin{cases} \text{PASS} & \text{if } \text{timeframe}(D) == C.\text{execution\_timeframe} \\ \text{RAISE TimeframeMismatchError} & \text{if } \text{timeframe}(D) \ne C.\text{execution\_timeframe} \end{cases}$$
- **Verification:** Verified by passing `"1D"` and `"1h"` to a 5m contract; confirms `TimeframeMismatchError` is raised.

#### Test 2: Category A Timeframe Restriction
- **Objective:** Guarantee that Category A (High-Frequency Intraday) experiments can only be declared on `"1m"` or `"5m"` timeframes.
- **Assertion:**
  $$\text{Contract}(C = \text{CATEGORY\_A}, \text{TF} \in \{\text{"15m"}, \text{"1h"}, \text{"1D"}\}) \implies \text{RAISE TimeframeMismatchError}$$
- **Verification:** Verified that defining a Category A contract with execution timeframe `"1D"` or `"15m"` fails initialization.

#### Test 3: Holding Horizon Boundary Enforcement
- **Objective:** Ensure that any strategy designated as intraday cannot hold open positions beyond 1,440 minutes (24 hours) unless `allow_overnight_holding = True` and explicit governance justification is supplied.
- **Assertion:**
  $$\forall \text{Trade } j \in \text{Trades}: \quad \text{Duration}_j \le C.\text{maximum\_holding\_horizon\_minutes}$$
  $$\text{If } \max(\text{Duration}) > 1440 \text{ and } \text{allow\_overnight\_holding} == \text{False} \implies \text{RAISE HoldingHorizonViolationError}$$
- **Verification:** Simulated trade durations of $[30\text{m}, 120\text{m}, 2880\text{m}]$ correctly trigger `HoldingHorizonViolationError` on a Category A contract.

#### Test 4: Overnight Holding Justification Enforcement
- **Objective:** Prevent silent setting of `allow_overnight_holding = True` without documented justification.
- **Assertion:**
  $$\text{If } \text{allow\_overnight\_holding} == \text{True} \land (\text{justification} == \text{None} \lor \text{len}(\text{justification}) == 0) \implies \text{RAISE ValueError}$$
- **Verification:** Tested that initializing a contract with `allow_overnight_holding=True` but no justification string raises `ValueError`.

---

### 3. Causal Execution & Timestamp Sequencing Assertions

#### Test 5: Point-in-Time Causal Timestamp Ordering
- **Objective:** Eliminate lookahead bias by mathematically asserting that information generation strictly precedes trade execution.
- **Strict Invariant Sequence:**
  $$t_{\text{feature}} \le t_{\text{bar\_close}} < t_{\text{signal}} \le t_{\text{order\_submit}} < t_{\text{fill}} = t_{\text{next\_bar\_open}}$$
- **Concrete 5-Minute Candle Example (Bar Index $i$):**
  - Bar $i$ Open Time: $t_{\text{open}, i} = \text{10:00:00.000 UTC}$
  - Bar $i$ Close Time: $t_{\text{close}, i} = \text{10:04:59.999 UTC}$
  - Signal Generation: $t_{\text{signal}} = \text{10:05:00.000 UTC}$ (Evaluated on Bar $i$ completed data)
  - Execution Fill Time: $t_{\text{fill}} = t_{\text{open}, i+1} = \text{10:05:00.000 UTC}$ (Filled at Bar $i+1$ Open Price)
- **Violation Assertion:**
  $$\text{If } t_{\text{fill}} \le t_{\text{close}, i} \implies \text{RAISE CRITICAL LOOKAHEAD VIOLATION}$$
  This assertion mathematically prevents the same-bar lookahead bug that contaminated Milestone 5.5 EXP-10A.

#### Test 6: Multi-Timeframe Feature Leakage Guard
- **Objective:** Ensure higher-timeframe context features (15m, 1h, 4h) do not incorporate future 5m bars.
- **Mathematical Alignment:**
  For a 5m bar at timestamp $t$:
  $$\text{Context\_Bar}_{15\text{m}}(t) = \lfloor t / 900,000 \rfloor \cdot 900,000$$
  $$\text{Only 15m candles with } t_{\text{close}} \le t_{\text{open}, 5\text{m}} \text{ are visible to the feature pipeline.}$$

---

### 4. Portfolio Exposure & Holdout Isolation Assertions

#### Test 7: Strictly Unlevered Exposure Hard-Cap
- **Objective:** Guarantee that portfolio gross exposure never exceeds $1.0000x$ at any time $t$.
- **Assertion:**
  $$\Lambda_t = \frac{\sum_{j=1}^{N_{\text{active}, t}} |\text{Notional}_{j, t}|}{\text{Equity}_t} \le 1.00000 \quad \forall t$$
  $$\text{If } \Lambda_t > 1.00000 \implies \text{RAISE ExposureViolationError}$$
- **Contract Level Assertion:**
  Contract initialization rejects any configuration with `maximum_gross_exposure > 1.0000`.

#### Test 8: Prospective Holdout Boundary Isolation
- **Objective:** Guarantee that no model, feature pipeline, or backtest touches the prospective holdout partition.
- **Partition Invariant:**
  $$\forall \text{DataRow } r \in \text{ResearchEngine}: \quad t_r < 1,793,491,200,000\text{ ms} \quad (2026-11-01\text{ 00:00:00 UTC})$$
  Any access to $t \ge 1,793,491,200,000\text{ ms}$ raises a security and governance audit failure.
