# QUANTUM — MILESTONE 5.10
## CENTRALIZED RESEARCH EXPERIMENT CONTRACT SPECIFICATION

---

### 1. Document Overview
- **Document Identifier:** `audit/strategy_research/milestone_5_10_architecture_correction/M5_10_RESEARCH_CONTRACT.md`
- **Code Implementation:** [`src/quantum/domain/research_contract.py`](file:///d:/quantum-multi-agent/src/quantum/domain/research_contract.py)
- **Research Branch:** `research/quantum-next-3pct`
- **Scope:** Defines the mandatory data contract and pre-backtest validation protocol that governs all future QUANTUM alpha research experiments.

---

### 2. Mandatory Contract Schema

The `ResearchExperimentContract` is a frozen Pydantic model that binds every quantitative and architectural assumption before backtesting code is permitted to execute:

```python
class ResearchExperimentContract(BaseModel):
    # Experiment Metadata & Category
    experiment_id: str
    experiment_name: str
    experiment_category: ExperimentCategory

    # Timeframe Architecture
    execution_timeframe: ExecutionTimeframe = ExecutionTimeframe.TF_5M
    context_timeframes: Tuple[ExecutionTimeframe, ...] = (
        ExecutionTimeframe.TF_15M,
        ExecutionTimeframe.TF_1H
    )

    # Holding Horizon & Frequency Bounds
    expected_holding_horizon: str = "15m to 4h"
    maximum_holding_horizon_minutes: int = 1440
    allow_overnight_holding: bool = False
    overnight_holding_justification: Optional[str] = None
    target_trade_frequency_daily: Tuple[float, float] = (10.0, 100.0)
    minimum_trade_frequency_daily: float = 1.0

    # Portfolio Sizing & Exposure Hard Caps
    maximum_concurrent_positions: int = 4
    maximum_symbol_weight: float = 0.25
    maximum_gross_exposure: float = 1.0000
    initial_equity_usd: float = 100.0
    mandatory_profitability_gate_daily_pct: float = 3.0000

    # Microstructure & Execution Frictions
    execution_model: str = "CAUSAL_NEXT_BAR_OPEN"
    fee_model: str = "BYBIT_VIP0_DEFAULT"
    slippage_model: str = "STATIC_HALF_SPREAD_SLIPPAGE"
    funding_model: str = "ZERO_UNAVAILABLE"
```

---

### 3. Detailed Parameter Specifications

```
+--------------------------------------------------------------------------------------------------------------------------+
| CONTRACT PARAMETER SPECIFICATION TABLE                                                                                   |
+----------------------------------------+--------------------+----------------+-------------------------------------------+
| Parameter Name                         | Type               | Default Value  | Architectural Purpose & Validation Rule   |
+----------------------------------------+--------------------+----------------+-------------------------------------------+
| experiment_id                          | str                | Mandatory      | Unique identifier (e.g. EXP-12)           |
| experiment_name                        | str                | Mandatory      | Descriptive name of alpha hypothesis      |
| experiment_category                    | ExperimentCategory | Mandatory      | Category A, B, C, or D                    |
| execution_timeframe                    | ExecutionTimeframe | "5m"           | Baseline 5m; 1m optional if available     |
| context_timeframes                     | Tuple[TF, ...]     | ("15m", "1h")  | Context resolutions for filters/regimes   |
| expected_holding_horizon               | str                | "15m to 4h"    | Target holding duration range             |
| maximum_holding_horizon_minutes        | int                | 1440           | Maximum permissible holding time (mins)   |
| allow_overnight_holding                | bool               | False          | Overnight holding forbidden by default    |
| overnight_holding_justification        | Optional[str]      | None           | Required if allow_overnight_holding=True  |
| target_trade_frequency_daily           | Tuple[float, float]| (10.0, 100.0)  | Intended completed trades per day         |
| minimum_trade_frequency_daily          | float              | 1.0            | Floor frequency for active intraday test  |
| maximum_concurrent_positions           | int                | 4              | Simultaneous active trade slots           |
| maximum_symbol_weight                  | float              | 0.25           | Max single asset capital fraction         |
| maximum_gross_exposure                 | float              | 1.0000         | Strictly unlevered portfolio cap (<=1.0x) |
| initial_equity_usd                     | float              | 100.0          | Standardized research capital base ($100) |
| mandatory_profitability_gate_daily_pct | float              | 3.0000         | Mandatory daily return hurdle (>= 3.00%)  |
| execution_model                        | str                | "CAUSAL_NEXT"  | Point-in-time causal next-bar open fill   |
| fee_model                              | str                | "BYBIT_VIP0"   | Standard unprivileged retail tier         |
| slippage_model                         | str                | "STATIC_HALF"  | Half-spread + depth slippage              |
| funding_model                          | str                | "ZERO_UNAVAIL" | Signed funding cash flows                 |
+----------------------------------------+--------------------+----------------+-------------------------------------------+
```

---

### 4. Contract Validation Invariant Rules

The contract enforces six architectural invariants via model validators:

#### Rule 1: Timeframe & Category Alignment
If `experiment_category == CATEGORY_A_HIGH_FREQUENCY_INTRADAY`:
- `execution_timeframe` must be either `"1m"` or `"5m"`. Any attempt to declare a Category A experiment on `"15m"`, `"1h"`, or `"1D"` immediately raises `TimeframeMismatchError`.
- `target_trade_frequency_daily[0]` must be $\ge 5.0\text{ trades/day}$.
- `maximum_holding_horizon_minutes` must be $\le 1440\text{ minutes}$ ($24\text{ hours}$) unless explicit overnight justification is provided.

#### Rule 2: Overnight Holding Governance
If `allow_overnight_holding == True`:
- `overnight_holding_justification` is mandatory and cannot be empty or null.
- If `allow_overnight_holding == False`, any trade held longer than 1,440 minutes raises `HoldingHorizonViolationError`.

#### Rule 3: Anti-Downsampling Runtime Invariant
When loading data into the backtest engine:
```python
validate_input_data_timeframe(contract, dataset_timeframe)
```
If the incoming dataset has a candle delta $\Delta t \ne \text{Expected\_Interval}(\text{contract.execution\_timeframe})$, execution halts before running a single iteration. Silent `.resample("1D")` downsampling is rendered impossible.

#### Rule 4: Strictly Unlevered Exposure Hard-Cap
- `maximum_gross_exposure` cannot exceed $1.00000\text{x}$.
- `maximum_symbol_weight` $\times$ `maximum_concurrent_positions` $\le 1.00000\text{x}$.
- Any attempt to configure leverage $> 1.0\text{x}$ raises `ExposureViolationError`.

#### Rule 5: Profitability Gate Immutability
- `mandatory_profitability_gate_daily_pct` is locked at `3.0000%`.
- Lowering the target gate in configuration files is strictly forbidden.

#### Rule 6: Swing Strategy Isolation
If an experiment operates on daily or multi-day horizons (e.g. cointegration pairs), it must declare:
`experiment_category = CATEGORY_C_SWING_MULTI_DAY` and `allow_overnight_holding = True`.
Category C experiments are segregated and can **never** be cited as evidence against the feasibility of high-frequency intraday alpha.

---

### 5. Multi-Agent Integration Protocol

The six autonomous agents interface with `ResearchExperimentContract` as follows:

1. **Scout Agent:** Reads `contract.execution_timeframe` and `contract.context_timeframes`. Only scans and loads features that match the contract resolutions.
2. **Analyst Agent:** Generates directional probability forecasts anchored to the declared `expected_holding_horizon` (e.g. 12 bars for 5m).
3. **Sniper Agent:** Enforces `contract.execution_model` (`CAUSAL_NEXT_BAR_OPEN`). Ensures entry fills occur at $t_{\text{exec}} = \text{open}[i+1]$ where $t_{\text{exec}} > t_{\text{signal}}$.
4. **Risk Agent:** Enforces `contract.maximum_gross_exposure` ($\le 1.0\text{x}$), `maximum_symbol_weight` ($\le 0.25$), and `maximum_concurrent_positions` ($\le 4$).
5. **Banker Agent:** Tracks cash balances, applies `contract.fee_model` and `contract.slippage_model`, and verifies that trade durations do not breach `maximum_holding_horizon_minutes`.
6. **Orchestrator Agent:** Validates the contract before initializing the pipeline and rejects any mismatch between agent outputs and contract bounds.
