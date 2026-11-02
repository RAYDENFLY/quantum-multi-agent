# QUANTUM  -  SEVEN-AGENT ARCHITECTURE AUDIT & THREE-TRACK RESEARCH EXPERIMENT DESIGN

**Document Version:** 1.0.0-PROPOSAL  
**Date:** 2026-11-02  
**Classification:** Research Architecture & Experiment Specification  
**Status:** PROPOSAL - AWAITING HUMAN GOVERNANCE AUTHORIZATION  
**Author:** Quantitative Research Systems Architect & Lead Auditor  

---

## 1. EXECUTIVE SUMMARY

This document provides a comprehensive technical source-code audit of the seven-module agent architecture under [`src/quantum/agents/`](file:///d:/quantum-multi-agent/src/quantum/agents/) and establishes a rigorous, scientifically controlled three-track research experiment design to evaluate model performance without confounding predictive power with execution heuristics.

```
+----------------------------------------------------------------------------------------------------+
|                                    THREE-TRACK RESEARCH TAXONOMY                                   |
+------------------------------------+----------------------------------+----------------------------+
| TRACK 1: PREDICTIVE BENCHMARK      | TRACK 2: RE-ANCHORED ECONOMIC    | TRACK 3: STRATEGY RESEARCH |
+------------------------------------+----------------------------------+----------------------------+
| * Anchor: close[i]                 | * Anchor: open[i+1]              | * Anchor: open[i+1] / limit|
| * Target: Symmetric +/- 1.5 sigma  | * Target: Symmetric +/- 1.5 sigma| * Target: Asymmetric/dynamic|
| * Hyperparameters: ZERO            | * Hyperparameters: ZERO          | * Hyperparameters: Tuned   |
| * Estimand: Conditional Prob P(y|x)| * Estimand: Baseline Economic PnL| * Estimand: Optimized Alpha|
| * Category: Statistical Score      | * Category: Causal Benchmark     | * Category: Live Trading   |
+------------------------------------+----------------------------------+----------------------------+
```

### 1.1 Architecture Audit Verdict

```
+----------------------------------------------------------------------------------------------------+
|                                     ARCHITECTURE AUDIT VERDICT                                     |
+----------------------------------------------------------------------------------------------------+
|                                 ARCHITECTURE_AUDIT_PASS_WITH_GAPS                                  |
+----------------------------------------------------------------------------------------------------+
```

The underlying software architecture exhibits high engineering discipline: Pydantic v2 data models guarantee strict boundary validation ([`contracts.py`](file:///d:/quantum-multi-agent/src/quantum/agents/contracts.py)), deterministic multi-gate risk filtering enforces strict loss and exposure limits ([`risk.py`](file:///d:/quantum-multi-agent/src/quantum/agents/risk.py)), and an explicit finite state machine (FSM) guarantees execution touch-versus-fill separation and idempotency ([`banker.py`](file:///d:/quantum-multi-agent/src/quantum/agents/banker.py)).

However, **eight material architectural and operational gaps** prevent immediate historical backtesting:
1. **Disconnected ML Models & Placeholder Probabilities:** In [`scout.py:L47-51`](file:///d:/quantum-multi-agent/src/quantum/agents/scout.py#L47-L51), [`analyst.py:L51-55`](file:///d:/quantum-multi-agent/src/quantum/agents/analyst.py#L51-L55), and [`sniper.py:L86-97`](file:///d:/quantum-multi-agent/src/quantum/agents/sniper.py#L86-L97), ML evaluation paths return hardcoded placeholder probabilities (`prob = 0.65`, `prob = 0.67`, `prob_tp1 = 0.62`) rather than calling frozen Phase 5.3 models or reading Phase 5.4 out-of-fold parquet artifacts.
2. **Wall-Clock Coupling in Historical Backtesting:** In [`risk.py:L94,L119`](file:///d:/quantum-multi-agent/src/quantum/agents/risk.py#L94-L119), `Signal Freshness` and `Cooldown` gates evaluate `time.time() * 1000`. In historical simulation on 2023-2026 candles, timestamp differences exceed 15,000 ms, causing Gate 1 to veto 100% of historical trades unless simulated clock injection is introduced.
3. **Misnamed Banker Agent & Missing Portfolio Ledger:** [`BankerAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/banker.py#L24-L368) is an in-trade order/stop lifecycle FSM rather than a portfolio treasury, capital allocator, or cash ledger. It does not calculate reference-price PnL, execution slippage, exchange fees, or 8-hour funding cash flows.
4. **Disconnected Pipeline Orchestration:** [`PipelineOrchestrator`](file:///d:/quantum-multi-agent/src/quantum/agents/orchestrator.py#L51-L518) coordinates `Scout -> Analyst -> Sniper -> Risk` but does not instantiate or invoke `BankerAgent`.
5. **Absence of a Historical Backtesting Engine:** The repository lacks a bar-by-bar discrete-event execution simulation engine under `src/quantum/`.
6. **Absence of Reference-Price & Funding Accounting Module:** The signed mathematical accounting specification ($L_{\text{realized}} = L_{\text{price,ref}} + C_{\text{exec,total}} + C_{\text{fees}} - CF_{\text{funding}}$) has no concrete Python implementation (`ISS_10 = NOT_VERIFIED`).
7. **Target Horizon Discrepancy:** The codebase implementation ([`TripleBarrierLabelGenerator`](file:///d:/quantum-multi-agent/src/quantum/features/labeling.py#L39) and [`TargetConfiguration`](file:///d:/quantum-multi-agent/src/quantum/ml/contracts.py#L40)) specifies `horizon_bars = 12` (60 minutes on 5m candles), whereas narrative governance documentation references a 288-bar (24-hour) horizon. Both must be reconciled and locked to the exact frozen Phase 5.3 training configuration.
8. **Asymmetric Reward-Risk Gate Rejection:** [`RiskConfig.min_net_reward_risk = 1.80`](file:///d:/quantum-multi-agent/src/quantum/config/settings.py#L82) and [`TradeProposal.estimated_reward_risk >= 1.50`](file:///d:/quantum-multi-agent/src/quantum/domain/models.py#L118) reject symmetric Track 2 trades (gross R:R = 1.00) unless adjusted for symmetric evaluation.

### 1.2 Immutable Governance Constraints

All governance constraints remain active and strictly enforced:
- **Phase 5.5 Research Status:** `NOT_STARTED`
- **Phase 5.6 Authorization Status:** `NOT_AUTHORIZED`
- **Economic Backtesting Status:** `NOT_STARTED`
- **Decisions DEC_01 through DEC_06:** `PENDING_HUMAN_DECISION`
- **Prospective Holdout Partition:** `STRICTLY_SEALED`
- **Frozen Phase 5.3 Models & Phase 5.4 Preprocessors:** Immutable, read-only artifacts.
- **Profitability Claims:** Strictly prohibited. No strategy or model is claimed or verified to be profitable.

---

## 2. REPOSITORY STRUCTURE AUDIT

The physical structure of the relevant components across [`d:\quantum-multi-agent`](file:///d:/quantum-multi-agent/) is organized as follows:

```text
d:\quantum-multi-agent\
├── artifacts\
│   ├── phase_5_3_1\ ... phase_5_3_3_6\   # 55 LightGBM models, 55 preprocessors, metrics
│   ├── phase_5_3_freeze\
│   │   └── frozen_artifact_manifest.json  # 304 cataloged immutable artifacts
│   └── phase_5_4\
│       ├── materialized_oof\              # 11 specialist out-of-fold Parquet datasets
│       │   ├── ADAUSDT_oof.parquet        # 130,684 to 261,488 rows per instrument
│       │   ├── BTCUSDT_oof.parquet        # Columns: fold, open_time_ms, true_label,
│       │   └── ... [11 assets total]      # predicted_class, raw_score_*, raw_prob_*
│       └── phase_5_4_3\ ... phase_5_4_6\  # ECE, AURCC, bootstrap audits, test execution reports
├── data\
│   └── historical\
│       └── canonical\                     # 11 specialist canonical 5m Parquet series
├── docs\
│   └── research\
│       └── phase_5_5_governance_dossier\  # Master governance status, errata, worksheet, brief
├── src\
│   └── quantum\
│       ├── agents\                        # Seven-module agent architecture under audit
│       │   ├── __init__.py                # Package exports (AgentId, Scout, Analyst, Sniper, Risk, Banker)
│       │   ├── analyst.py                 # Structural regime classifier & invalidation calculator
│       │   ├── banker.py                  # Order/stop state machine, partial fill & trailing stop FSM
│       │   ├── contracts.py               # Pydantic v2 inter-agent data contracts
│       │   ├── orchestrator.py            # Async pipeline coordinator & SQLite telemetry recorder
│       │   ├── risk.py                    # 12-gate deterministic safety validator & position sizer
│       │   ├── scout.py                   # Stage 1 candidate filter & wick trap detector
│       │   └── sniper.py                  # Stage 3 trade proposal generator (limit order & TP/SL ladder)
│       ├── config\
│       │   └── settings.py                # SystemConfig, TradingConfig, RiskConfig, MLConfig
│       ├── core\
│       │   ├── event_bus.py               # In-memory pub/sub message bus
│       │   ├── system_monitor.py          # Process memory and CPU thread watchdog
│       │   └── task_runner.py             # Background task lifecycle manager
│       ├── domain\
│       │   ├── enums.py                   # AgentId, AgentAction, MarketRegime, PositionState
│       │   └── models.py                  # TradeProposal, Position, ExecutionEvent, MarketSnapshot
│       ├── features\
│       │   ├── engine.py                  # 36 stationary technical & structural features
│       │   ├── labeling.py                # TripleBarrierLabelGenerator (horizon_bars = 12)
│       │   ├── schema.py                  # Feature schema definition & canonical hash
│       │   └── temporal_split.py          # PurgedGroupTimeSeriesSplit (5 folds, purge=12, embargo=24)
│       ├── ml\
│       │   ├── contracts.py               # TargetConfiguration, ExperimentManifest, DatasetSampleTrace
│       │   ├── evaluation.py              # ModelEvaluationContract (accuracy, Brier, ROC-AUC)
│       │   ├── preprocessor.py            # RobustScaler & QuantileTransformer pipeline
│       │   └── registry.py                # ModelRegistry (loads models into memory)
│       │   └── validation.py              # Statistical validation & metrics computation
│       └── storage\
│           └── database.py                # SQLite async engine & telemetry tables
└── tests\
    └── unit\
        ├── test_agents.py                 # Scout, Analyst, Sniper, Banker unit tests (193 lines)
        ├── test_banker_fsm.py             # Banker FSM lifecycle & event tests (499 lines)
        ├── test_contracts.py              # Pydantic contract validation tests (257 lines)
        ├── test_orchestrator.py           # Pipeline execution & error tests (219 lines)
        └── test_risk_engine.py            # 12-gate deterministic risk checks (689 lines)
```

---

## 3. SEVEN-AGENT SOURCE AUDIT

A complete inspection of the seven modules in [`src/quantum/agents/`](file:///d:/quantum-multi-agent/src/quantum/agents/) was conducted.

### 3.1 Taxonomy and Nomenclature Finding

The directory [`src/quantum/agents/`](file:///d:/quantum-multi-agent/src/quantum/agents/) contains eight Python files. An important distinction must be recognized:
- Five modules implement domain agent classes assigned an [`AgentId`](file:///d:/quantum-multi-agent/src/quantum/domain/enums.py#L48-L55): [`ScoutAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/scout.py#L15), [`AnalystAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/analyst.py#L15), [`SniperAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/sniper.py#L22), [`RiskAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/risk.py#L80), and [`BankerAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/banker.py#L24).
- One module defines data contracts: [`contracts.py`](file:///d:/quantum-multi-agent/src/quantum/agents/contracts.py). It contains no agent logic.
- One module implements pipeline execution: [`PipelineOrchestrator`](file:///d:/quantum-multi-agent/src/quantum/agents/orchestrator.py#L51). It is an asynchronous workflow engine, not a trading decision agent.
- One module exports the package namespace: [`__init__.py`](file:///d:/quantum-multi-agent/src/quantum/agents/__init__.py).

### 3.2 Seven-Agent Audit Summary Table

| Module / Agent | Actual Responsibility | Inputs | Outputs | Dependencies | Unit Tests | Findings |
|---|---|---|---|---|---|---|
| [`scout.py`](file:///d:/quantum-multi-agent/src/quantum/agents/scout.py)<br>`ScoutAgent` | Stage 1 candidate screening; filters on minimum score and maximum wick-trap ratio | [`ScoutInput`](file:///d:/quantum-multi-agent/src/quantum/agents/contracts.py#L18)<br>(candle data, wick metrics) | [`ScoutOutput`](file:///d:/quantum-multi-agent/src/quantum/agents/contracts.py#L34)<br>(`action`, `probability_estimate`, `reason`) | [`ModelRegistry`](file:///d:/quantum-multi-agent/src/quantum/ml/registry.py#L24), [`AgentId`](file:///d:/quantum-multi-agent/src/quantum/domain/enums.py#L48) | [`test_agents.py`](file:///d:/quantum-multi-agent/tests/unit/test_agents.py#L17-L50) | `[VERIFIED_FROM_SOURCE_CODE]` Hardcoded `prob = 0.65` in active ML path (L47-51). Rule fallback operates deterministically. |
| [`analyst.py`](file:///d:/quantum-multi-agent/src/quantum/agents/analyst.py)<br>`AnalystAgent` | Stage 2 regime classification; vetoes low-liquidity chop; calculates ATR structural invalidation | [`AnalystInput`](file:///d:/quantum-multi-agent/src/quantum/agents/contracts.py#L48)<br>(volatility, RSI, spread, scout output) | [`AnalystOutput`](file:///d:/quantum-multi-agent/src/quantum/agents/contracts.py#L65)<br>(`action`, `regime`, `invalidation_price`) | [`ModelRegistry`](file:///d:/quantum-multi-agent/src/quantum/ml/registry.py#L24), [`MarketRegime`](file:///d:/quantum-multi-agent/src/quantum/domain/enums.py#L31) | [`test_agents.py`](file:///d:/quantum-multi-agent/tests/unit/test_agents.py#L53-L92) | `[VERIFIED_FROM_SOURCE_CODE]` Hardcoded `regime = TREND_IMPULSE, prob = 0.67` in ML path (L51-55). Input field `scout_output` accepted but ignored (L48-115). |
| [`sniper.py`](file:///d:/quantum-multi-agent/src/quantum/agents/sniper.py)<br>`SniperAgent` | Stage 3 proposal generation; creates limit order at bid1/ask1; constructs asymmetric 2.0R/3.2R TP ladder | [`SniperInput`](file:///d:/quantum-multi-agent/src/quantum/agents/contracts.py#L82)<br>(order book, ATR, analyst output) | [`SniperOutput`](file:///d:/quantum-multi-agent/src/quantum/agents/contracts.py#L98)<br>([`TradeProposal`](file:///d:/quantum-multi-agent/src/quantum/domain/models.py#L96), execution plan) | [`TradeProposal`](file:///d:/quantum-multi-agent/src/quantum/domain/models.py#L96), [`ModelRegistry`](file:///d:/quantum-multi-agent/src/quantum/ml/registry.py#L24) | [`test_agents.py`](file:///d:/quantum-multi-agent/tests/unit/test_agents.py#L95-L138) | `[VERIFIED_FROM_SOURCE_CODE]` Hardcodes `prob_tp1 = 0.62`, `prob_tp2 = 0.44`, `friction_r = 0.08` (L86-97). Inherently an asymmetric live-desk heuristic module, not a symmetric benchmark runner. |
| [`risk.py`](file:///d:/quantum-multi-agent/src/quantum/agents/risk.py)<br>`RiskAgent` | Stage 4 deterministic 12-gate safety engine; validates sizing, limits, drawdown, and spreads | [`RiskInput`](file:///d:/quantum-multi-agent/src/quantum/agents/contracts.py#L119)<br>(proposal, equity, positions, daily PnL) | [`RiskOutput`](file:///d:/quantum-multi-agent/src/quantum/agents/contracts.py#L141)<br>(`action`, `approved_size`, `rejection_reasons`) | [`RiskConfig`](file:///d:/quantum-multi-agent/src/quantum/config/settings.py#L65), [`OrderSide`](file:///d:/quantum-multi-agent/src/quantum/domain/enums.py#L14) | [`test_risk_engine.py`](file:///d:/quantum-multi-agent/tests/unit/test_risk_engine.py#L1-L689) (14 tests) | `[VERIFIED_FROM_SOURCE_CODE]` 100% deterministic code. Wall-clock coupling via `time.time() * 1000` (L94, 119) vetoes historical backtests. Recomputes net R:R with hardcoded 5.5 bps fee (L220-228). |
| [`banker.py`](file:///d:/quantum-multi-agent/src/quantum/agents/banker.py)<br>`BankerAgent` | Stage 5 order and stop lifecycle state machine; manages partial fills, breakeven ratchets, trailing stops | [`BankerInput`](file:///d:/quantum-multi-agent/src/quantum/agents/contracts.py#L206)<br>or [`PositionExecutionEvent`](file:///d:/quantum-multi-agent/src/quantum/agents/contracts.py#L159) | [`BankerOutput`](file:///d:/quantum-multi-agent/src/quantum/agents/contracts.py#L213)<br>or [`TrackedPosition`](file:///d:/quantum-multi-agent/src/quantum/agents/contracts.py#L182) | [`PositionState`](file:///d:/quantum-multi-agent/src/quantum/domain/enums.py#L76), [`ExecutionEventType`](file:///d:/quantum-multi-agent/src/quantum/domain/enums.py#L86) | [`test_banker_fsm.py`](file:///d:/quantum-multi-agent/tests/unit/test_banker_fsm.py#L1-L499) (10 tests) | `[VERIFIED_FROM_SOURCE_CODE]` Misnamed; acts as an in-trade order/stop FSM, not a portfolio cash/funding ledger. Not called by `PipelineOrchestrator`. Wall-clock check in L62, 295. |
| [`contracts.py`](file:///d:/quantum-multi-agent/src/quantum/agents/contracts.py)<br>Data Contracts | Formal inter-agent data schemas and validation contracts using Pydantic v2 | Python objects or dictionaries | Validated immutable data transfer objects | Pydantic v2, [`quantum.domain.models`](file:///d:/quantum-multi-agent/src/quantum/domain/models.py) | [`test_contracts.py`](file:///d:/quantum-multi-agent/tests/unit/test_contracts.py#L1-L257) | `[VERIFIED_FROM_SOURCE_CODE]` Pure schema definition module (12 models). Does not define fee schedules, funding settlement, or Phase 5.5 accounting schemas. |
| [`orchestrator.py`](file:///d:/quantum-multi-agent/src/quantum/agents/orchestrator.py)<br>`PipelineOrchestrator` | Asynchronous FSM pipeline coordinator; runs Scout->Analyst->Sniper->Risk; records SQLite telemetry | [`PipelineContext`](file:///d:/quantum-multi-agent/src/quantum/agents/orchestrator.py#L28)<br>(symbol, snapshot, candidate) | [`PipelineResult`](file:///d:/quantum-multi-agent/src/quantum/agents/orchestrator.py#L42)<br>(stage outputs, final status) | [`EventBus`](file:///d:/quantum-multi-agent/src/quantum/core/event_bus.py#L21), SQLite database engine | [`test_orchestrator.py`](file:///d:/quantum-multi-agent/tests/unit/test_orchestrator.py#L1-L219) (6 tests) | `[VERIFIED_FROM_SOURCE_CODE]` Hardcodes dummy instrument specs (L387: tick=0.1, lot=0.001, taker_fee=0.00055). Bypasses Risk tracking defaults in L260-274. Does not call Banker. |

### 3.3 Detailed Module-by-Module Source Inspection

#### 3.3.1 [`src/quantum/agents/__init__.py`](file:///d:/quantum-multi-agent/src/quantum/agents/__init__.py)
- **Verified from source code:** Exports the public symbol list `["AgentId", "ScoutAgent", "AnalystAgent", "SniperAgent", "RiskAgent", "BankerAgent"]`. Re-exports `AgentId` from `quantum.domain.enums`.
- **Inferred from architecture:** Establishes the public API for agent consumers.
- **Proposed responsibility:** Maintain clean packaging; ensure any future execution simulation engine or backtesting harness imports agents through this interface.

#### 3.3.2 [`src/quantum/agents/scout.py`](file:///d:/quantum-multi-agent/src/quantum/agents/scout.py) (`ScoutAgent`)
- **Verified from source code:**
  - Class: [`ScoutAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/scout.py#L15). Method: `evaluate(input_data: ScoutInput) -> ScoutOutput`.
  - Configurable parameters: `min_probability` (default: 0.56), `max_wick_trap` (default: 0.55).
  - Queries `ModelRegistry.get_active_model(AgentId.SCOUT)`.
  - **Material Gap (L47-51):** When `active_model is not None`, sets `prob = 0.65` with inline comment `# Target placeholder for active ML test`. It does not call `model.predict_proba()` or pass feature tensors.
  - When `active_model is None` (rule fallback mode, L52-59), computes:
    $$\text{prob} = \min\left(0.95, \max\left(0.40, \frac{\text{deterministic\_score}}{100.0} \times (1.0 - 0.35 \times \text{wick\_trap})\right)\right)$$
  - Emits `AgentAction.PROCEED` if $\text{prob} \ge \text{min\_probability}$ and $\text{wick\_trap} \le \text{max\_wick\_trap}$; otherwise emits `AgentAction.SKIP`.
- **Inferred from architecture:** Intended as an initial high-throughput screening filter for 15-minute scanner candidates.
- **Proposed responsibility:** In Track 1 and Track 2 research, `ScoutAgent` is **NOT_REQUIRED** because model probabilities are evaluated directly across all valid bars. In Track 3, it may serve as an **OPTIONAL** candidate filter.

#### 3.3.3 [`src/quantum/agents/analyst.py`](file:///d:/quantum-multi-agent/src/quantum/agents/analyst.py) (`AnalystAgent`)
- **Verified from source code:**
  - Class: [`AnalystAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/analyst.py#L15). Method: `evaluate(input_data: AnalystInput) -> AnalystOutput`.
  - Configurable parameters: `min_probability` (0.58), `invalidation_atr_mult` (1.75).
  - Queries `ModelRegistry.get_active_model(AgentId.ANALYST)`.
  - **Material Gap (L51-55):** When `active_model is not None`, sets hardcoded `regime = MarketRegime.TREND_IMPULSE` and `prob = 0.67`.
  - Rule fallback mode (L57-70): Classifies regime into `LOW_LIQ_CHOP`, `HIGH_VOL_EXHAUSTION`, `MEAN_REVERT_RANGE`, or `TREND_IMPULSE` using heuristics on `rvol_15m`, `rsi_15m`, `spread_bps`, and `atr_15m / atr_1h`.
  - Computes structural invalidation price:
    $$\text{invalidation\_price} = \begin{cases} \text{mark\_price} - 1.75 \times \text{atr\_15m} & \text{if Long} \\ \text{mark\_price} + 1.75 \times \text{atr\_15m} & \text{if Short} \end{cases}$$
  - Vetoes (`AgentAction.SKIP`) if `regime == MarketRegime.LOW_LIQ_CHOP` or $\text{prob} < \text{min\_probability}$.
  - Accepts `scout_output` in [`AnalystInput`](file:///d:/quantum-multi-agent/src/quantum/agents/contracts.py#L48) but never reads or references it inside `evaluate()`.
- **Inferred from architecture:** Intended as a macro structural filter to avoid choppy regimes and calculate ATR stop anchors.
- **Proposed responsibility:** **NOT_REQUIRED** for Track 1 and Track 2. For Track 3, its regime classification rules can serve as an **OPTIONAL** regime filter for exit parameter switching.

#### 3.3.4 [`src/quantum/agents/sniper.py`](file:///d:/quantum-multi-agent/src/quantum/agents/sniper.py) (`SniperAgent`)
- **Verified from source code:**
  - Class: [`SniperAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/sniper.py#L22). Method: `evaluate(input_data: SniperInput) -> SniperOutput`.
  - Configurable parameters: `tp1_r_multiple` (2.0R), `tp2_r_multiple` (3.2R), `tp1_close_pct` (0.50), `max_spread_bps` (10.0), `atr_stop_multiplier` (1.25).
  - Constructs **LIMIT orders** placed at `bid1_price` (Long) or `ask1_price` (Short).
  - Sets stop-loss to `min(analyst.invalidation_price, entry - 1.25 * atr_15m)` (Long) or `max(analyst.invalidation_price, entry + 1.25 * atr_15m)` (Short).
  - **Material Gap (L86-97, L124, L154-161):** Hardcodes `prob_tp1 = 0.62`, `prob_tp2 = 0.44`, `friction_r = 0.08`, `expected_holding_minutes = 120`, and `confidence = 0.62`. Hardcodes `tp1_close_pct = 0.50` in output construction (L154).
  - Creates a [`TradeProposal`](file:///d:/quantum-multi-agent/src/quantum/domain/models.py#L96) object with two-stage take-profit targets (TP1 and TP2).
- **Inferred from architecture:** Designed specifically as an asymmetric, live-desk limit-order generator with a two-target take-profit ladder.
- **Proposed responsibility:** Incompatible with Track 1 (predictive target) and Track 2 (symmetric barriers). In Track 3, `SniperAgent` is **REQUIRED** (or refactored) to represent asymmetric strategy research.

#### 3.3.5 [`src/quantum/agents/risk.py`](file:///d:/quantum-multi-agent/src/quantum/agents/risk.py) (`RiskAgent`)
- **Verified from source code:**
  - Class: [`RiskAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/risk.py#L80). Method: `evaluate(input_data: RiskInput) -> RiskOutput`.
  - 100% deterministic code implementing a 12-gate safety sequence:
    1. Gate 1: `SIGNAL_FRESHNESS` ($\text{age} \le 15{,}000\text{ ms}$)
    2. Gate 2: `DRAWDOWN_CIRCUIT_BREAKER` ($\text{drawdown} \le 10\%$)
    3. Gate 3: `DAILY_LOSS_LIMIT` ($\text{daily\_loss} \le 3\%$)
    4. Gate 4: `LOSS_STREAK_COOLDOWN` ($N \ge 3 \implies 30\text{ min cooldown}$)
    5. Gate 5: `MAX_CONCURRENT_POSITIONS` ($\le 3\text{ positions}$)
    6. Gate 6: `STOP_GEOMETRY_VALID` ($\text{SL} > 0$, correctly placed)
    7. Gate 7: `MAX_SPREAD` ($\text{spread} \le 12\text{ bps}$)
    8. Gate 8: `MIN_NET_RR` ($\text{net\_RR} \ge 1.80$)
    9. Gate 9: `MAX_SLIPPAGE` ($\le 8\text{ bps}$)
    10. Gate 10: `LOT_STEP_AND_MIN_NOTIONAL` ($\text{notional} \ge 10\text{ USDT}$, valid lot step)
    11. Gate 11: `MAX_EXPOSURE_AND_LEVERAGE` ($\le 5\times\text{ leverage}$, portfolio cap)
    12. Gate 12: `LIQUIDATION_BUFFER` (buffer $\ge 30\%$)
  - Sizing logic (L245-283): Fixed risk percentage (1.0% of equity) divided by distance to stop loss.
  - **Material Gaps:**
    - Wall-clock coupling: L94 (`now_ms = int(time.time() * 1000)`) and L119 evaluate signal freshness against current host wall clock.
    - Asymmetric R:R requirement: Gate 8 requires $\text{net\_RR} \ge 1.80$, rejecting symmetric $1.00$ gross R:R trades.
    - Inconsistent fee assumptions: L220-228 recomputes net R:R using a hardcoded `fee_rate = 0.00055` (5.5 bps), omitting the exit fee on winning trades.
- **Inferred from architecture:** Production safety firewall designed to prevent live execution disasters.
- **Proposed responsibility:** **NOT_REQUIRED** for Track 1. For Track 2, sizing must be fixed-notional (to isolate signal edge from compounding) and Gate 1 wall-clock checks must accept simulated bar timestamps. For Track 3, `RiskAgent` is **REQUIRED** to test real-world risk constraints.

#### 3.3.6 [`src/quantum/agents/banker.py`](file:///d:/quantum-multi-agent/src/quantum/agents/banker.py) (`BankerAgent`)
- **Verified from source code:**
  - Class: [`BankerAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/banker.py#L24). Methods: `handle_execution_event(position, event) -> TrackedPosition` and `evaluate(input_data: BankerInput) -> BankerOutput`.
  - Implements an explicit position lifecycle FSM: `PENDING_OPEN -> OPEN -> PARTIALLY_CLOSED -> CLOSED`.
  - Enforces sequence monotonicity (`last_sequence_number`), event idempotency (`processed_event_ids`), and overfill validation (`InvalidExecutionQuantityError`).
  - Implements **Option A Breakeven Stop Ratchet**: When TP1 fill is confirmed, shifts `stop_loss_price` to `entry_price`.
  - Implements dynamic trailing stops: Activates when unrealized return reaches $2.0R$; updates stop monotonically by trailing mark price by $1.5 \times \text{ATR}$.
  - **Material Gaps:**
    - **Nomenclature Misalignment:** Does not perform portfolio banking, capital management, cash flow settlement, fee reconciliation, or funding accounting. It is an in-trade order/stop execution state machine.
    - L290-368 in `evaluate()` hardcodes hazard probabilities (`0.0, 0.05, 0.10, 0.15, 0.20, 1.0`).
    - Uses wall-clock `int(time.time() * 1000)` at L62, 295.
    - Completely disconnected from [`PipelineOrchestrator`](file:///d:/quantum-multi-agent/src/quantum/agents/orchestrator.py#L51).
- **Inferred from architecture:** Designed for live trade execution handling on Binance/Hyperliquid websockets.
- **Proposed responsibility:** **NOT_REQUIRED** for Track 1 and Track 2 (where symmetric barriers trigger instant single-event exits). For Track 3, `BankerAgent` is **REQUIRED** to manage partial TP1 fills and trailing stops.

#### 3.3.7 [`src/quantum/agents/contracts.py`](file:///d:/quantum-multi-agent/src/quantum/agents/contracts.py)
- **Verified from source code:**
  - Defines 12 frozen Pydantic v2 data models: `ScoutInput`, `ScoutOutput`, `AnalystInput`, `AnalystOutput`, `SniperInput`, `SniperOutput`, `RiskInput`, `RiskOutput`, `PositionExecutionEvent`, `TrackedPosition`, `BankerInput`, `BankerOutput`.
  - Enforces strong runtime validation on floating-point bounds, string lengths, and enum variants.
  - **Material Gap:** Does not define contracts for historical backtest configuration, fee structures, funding payment settlement, or reference-price PnL decomposition.
- **Inferred from architecture:** Data contract layer ensuring type safety and decoupling across pipeline stages.
- **Proposed responsibility:** Retain as the immutable contract definition layer. Proposed additions should define `BacktestRunContract` and `ReferencePriceAccountingContract`.

#### 3.3.8 [`src/quantum/agents/orchestrator.py`](file:///d:/quantum-multi-agent/src/quantum/agents/orchestrator.py) (`PipelineOrchestrator`)
- **Verified from source code:**
  - Class: [`PipelineOrchestrator`](file:///d:/quantum-multi-agent/src/quantum/agents/orchestrator.py#L51). Method: `async execute(context: PipelineContext) -> PipelineResult`.
  - Coordinates pipeline stages sequentially with asyncio timeouts: Feature Validation -> Scout (50ms) -> Analyst (50ms) -> Sniper (50ms) -> Risk (25ms).
  - Publishes completion events to [`EventBus`](file:///d:/quantum-multi-agent/src/quantum/core/event_bus.py#L21) and persists telemetry to SQLite.
  - **Material Gaps:**
    - Never instantiates or calls [`BankerAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/banker.py#L24).
    - In `_finalize_run` (L260-274), supplies unpopulated defaults (`open_positions_count=0, total_exposure_usdt=0.0`) and omits `peak_equity_usdt`, `daily_pnl_usdt`, `consecutive_losses_count`, and `last_loss_timestamp_ms`. This bypasses Risk Gates 2, 3, and 4 during execution.
    - Hardcodes dummy instrument specifications at L387 (`tick_size=0.1, lot_step=0.001, maker_fee=0.0002, taker_fee=0.00055`).
- **Inferred from architecture:** Production live-scanner pipeline runner designed to process incoming candle ticks in under 200 ms.
- **Proposed responsibility:** **NOT_REQUIRED** for Track 1 and Track 2. For Track 3, may be adapted or bypassed in favor of a specialized, high-performance historical backtest runner.

---

## 4. AGENT-TO-TRACK RESPONSIBILITY MATRIX

The following matrix details which components are strictly required, optional, or not required for each of the three research tracks:

```text
+------------------+-----------------+-----------------+-----------------+-----------------------------------------------------------+
| Agent / Module   | Track 1         | Track 2         | Track 3         | Justification                                             |
+------------------+-----------------+-----------------+-----------------+-----------------------------------------------------------+
| ScoutAgent       | NOT_REQUIRED    | NOT_REQUIRED    | OPTIONAL        | Stage 1 screening filter; bypass for pure model evaluation|
| AnalystAgent     | NOT_REQUIRED    | NOT_REQUIRED    | OPTIONAL        | Regime classifier; relevant only for regime-switched exits|
| SniperAgent      | NOT_REQUIRED    | NOT_REQUIRED    | REQUIRED        | Implements asymmetric TP/SL and limit order logic         |
| RiskAgent        | NOT_REQUIRED    | OPTIONAL        | REQUIRED        | Sizing & risk gates; Track 2 requires fixed notional size |
| BankerAgent      | NOT_REQUIRED    | NOT_REQUIRED    | REQUIRED        | Order FSM managing partial fills and trailing stops       |
| Contracts        | OPTIONAL        | OPTIONAL        | REQUIRED        | Inter-agent schemas; Track 1 & 2 use direct vector inputs |
| Orchestrator     | NOT_REQUIRED    | NOT_REQUIRED    | OPTIONAL        | Async live runner; historical backtesting needs batched engine|
+------------------+-----------------+-----------------+-----------------+-----------------------------------------------------------+
```

### 4.1 System-Wide Shared Infrastructure Requirements

To support the three research tracks without duplication or bias, six core infrastructure components must be established:

1. **Shared Data Layer (`REQUIRED`):**
   - Source: Canonical historical 5m Parquet datasets ([`data/historical/canonical/`](file:///d:/quantum-multi-agent/data/historical/canonical/)) and frozen Phase 5.4 out-of-fold predictions ([`artifacts/phase_5_4/materialized_oof/`](file:///d:/quantum-multi-agent/artifacts/phase_5_4/materialized_oof/)).
   - Verification: Cryptographic SHA-256 validation against [`frozen_artifact_manifest.json`](file:///d:/quantum-multi-agent/artifacts/phase_5_3_freeze/frozen_artifact_manifest.json).
2. **Independent Experiment Runner (`REQUIRED` - `NOT_IMPLEMENTED`):**
   - Dedicated, deterministic historical event-driven simulation runner (`src/quantum/backtesting/engine.py`).
   - Must support simulated clock injection (`eval_timestamp_ms`) to decouple backtesting from host wall-clock time.
3. **Shared Accounting Engine (`REQUIRED` - `NOT_IMPLEMENTED`):**
   - Implements reference-price PnL decomposition:
     $$L_{\text{realized}} = L_{\text{price,ref}} + C_{\text{exec,total}} + C_{\text{fees}} - CF_{\text{funding}}$$
   - Implements partial-fill cost basis allocation (Average Cost Basis and FIFO).
   - Simulates 8-hour funding cash flows at 00:00, 08:00, and 16:00 UTC.
4. **Track-Specific Evaluation Modules (`REQUIRED`):**
   - Track 1: Scikit-learn statistical metrics and calibration module ([`src/quantum/ml/evaluation.py`](file:///d:/quantum-multi-agent/src/quantum/ml/evaluation.py)).
   - Track 2: Causal re-anchored barrier simulator with zero tuning parameters.
   - Track 3: Parameterized strategy optimizer with multiple-testing corrections.
5. **Centralized Reporting (`REQUIRED`):**
   - Unified tabular export generating JSON and Markdown summaries containing all mandatory metrics.
6. **Reproducibility Metadata (`REQUIRED`):**
   - Experiment manifest recording software versions, git commit hash, random seed (42), and dataset checksums.

---

## 5. TRACK 1 METHODOLOGY  -  PREDICTIVE BENCHMARK

### 5.1 Objective and Definition

Track 1 measures the pure statistical classification power of the frozen Phase 5.3 models with respect to the exact label definitions on which they were trained.

```
+----------------------------------------------------------------------------------------------------+
|                                    TRACK 1 SPECIFICATION SUMMARY                                   |
+------------------------------------+---------------------------------------------------------------+
| Parameter                          | Specification Value                                           |
+------------------------------------+---------------------------------------------------------------+
| Target Anchor                      | Bar Close: close[i]                                           |
| Barrier Geometry                   | Symmetric: +/- 1.5 sigma_t                                    |
| Volatility Estimator               | 20-bar rolling standard deviation of 5m log returns            |
| Label Horizon                      | Reconciled to frozen target_config (12 bars / 60 minutes)      |
| Ambiguity Policy                   | CONSERVATIVE_EXCLUDE                                          |
| Hyperparameters                    | ZERO strategy-tuning hyperparameters                          |
| Causal Limitation                  | NOT AN EXECUTABLE ECONOMIC ENTRY ANCHOR                       |
+------------------------------------+---------------------------------------------------------------+
```

### 5.2 Horizon Reconciliation: 12 Bars vs. 288 Bars

A critical discrepancy exists between narrative documentation and executable code:
- Narrative governance documents describe a 288-bar (24-hour) horizon.
- Code implementation in [`TripleBarrierLabelGenerator`](file:///d:/quantum-multi-agent/src/quantum/features/labeling.py#L39) and [`TargetConfiguration`](file:///d:/quantum-multi-agent/src/quantum/ml/contracts.py#L40) specifies:
  ```python
  horizon_bars: int = 12
  maximum_holding_minutes: int = 60
  volatility_lookback: int = 20
  barrier_multiplier: float = 1.5
  ```
- The frozen training metadata in [`artifacts/phase_5_3_1/pilot_summary.json`](file:///d:/quantum-multi-agent/artifacts/phase_5_3_1/pilot_summary.json#L35) records `purged_samples: 12`, confirming that Phase 5.3 models were trained with `horizon_bars = 12`.

**Methodological Resolution:** Track 1 must evaluate against the exact 12-bar target horizon on which the frozen Phase 5.3 models were trained. Evaluating against 288 bars would introduce target label mismatch and invalidate the statistical benchmark.

### 5.3 Evaluated Predictive Metrics

Track 1 evaluation utilizes [`ModelEvaluationContract`](file:///d:/quantum-multi-agent/src/quantum/ml/evaluation.py#L21) across nine core statistical dimensions:
1. **Accuracy:** Overall multiclass correct classification rate.
2. **Balanced Accuracy:** Macro-averaged recall across classes $\{-1, 0, 1\}$.
3. **Precision and Recall:** Per-class precision, recall, and F1 scores.
4. **ROC-AUC (One-vs-Rest):** Multiclass area under the receiver operating characteristic.
5. **PR-AUC (One-vs-Rest):** Precision-recall area under curve.
6. **Confusion Matrix:** $3 \times 3$ error matrix documenting class migrations.
7. **Probability Calibration:** Expected Calibration Error (ECE) and Maximum Calibration Error (MCE) across 10 bins.
8. **Brier Score:** Multiclass quadratic probability error:
   $$\text{Brier} = \frac{1}{N} \sum_{i=1}^N \sum_{c=-1}^1 (p_{i,c} - y_{i,c})^2$$
9. **Coverage and Prediction Distribution:** Selective coverage curves (AURCC) evaluating accuracy degradation as the prediction rejection threshold is relaxed.

### 5.4 Methodological Limitation Notice

> [!WARNING]
> **PREDICTIVE BENCHMARK LIMITATION:**  
> Track 1 evaluates an abstract statistical estimand ($P(y | x)$). Anchoring at `close[i]` assumes instantaneous execution at bar close with zero latency and zero spread drag. In physical trading, `close[i]` is not executable. Track 1 results must NEVER be interpreted as executable economic returns.

---

## 6. TRACK 2 METHODOLOGY  -  RE-ANCHORED ECONOMIC EVALUATION

### 6.1 Objective and Definition

Track 2 measures whether the model's directional signal retains positive economic value when subjected to causal, realistic execution mechanics with zero additional strategy optimization.

```
+----------------------------------------------------------------------------------------------------+
|                                    TRACK 2 SPECIFICATION SUMMARY                                   |
+------------------------------------+---------------------------------------------------------------+
| Parameter                          | Specification Value                                           |
+------------------------------------+---------------------------------------------------------------+
| Entry Anchor                       | Next Bar Open: open[i+1]                                      |
| Barrier Geometry                   | Symmetric: +/- 1.5 sigma_t (computed at bar i close)           |
| Barrier Price Levels               | Long: open[i+1] * (1 +/- 1.5 sigma_t)                          |
|                                    | Short: open[i+1] * (1 -/+ 1.5 sigma_t)                         |
| Exit Evaluation                    | First touch within 12 bars (or bar 12 open on expiration)     |
| Execution Type                     | Immediate taker fill at open[i+1]                             |
| Strategy Tuning                    | STRICTLY ZERO hyperparameters                                 |
| Transaction Cost Sweep             | 0 bps, 15 bps, 20 bps, and 30 bps round-trip                   |
+------------------------------------+---------------------------------------------------------------+
```

### 6.2 Mandated Backtesting Reporting Metrics

Track 2 must output the `12_REQUIRED_BACKTESTING_REPORTING_METRICS`:
1. **Gross PnL (USDT):** Cumulative return prior to transaction frictions.
2. **Net PnL (USDT):** Cumulative return after all execution costs and fees.
3. **Net Expectancy per Trade (bps):** Average basis points captured per executed trade:
   $$\mathbb{E}[\text{bps}] = \frac{\text{Net PnL}}{\text{Total Notional Volume}} \times 10{,}000$$
4. **Profit Factor:** Gross profits divided by gross losses ($\sum \text{Gains} / \sum |\text{Losses}|$).
5. **Maximum Drawdown (USDT and %):** Peak-to-trough equity reduction.
6. **Annualized Sharpe Ratio:** Risk-adjusted return using zero risk-free rate.
7. **Win Rate (%):** Proportion of trades achieving positive realized return.
8. **Completed Trade Count:** Total trades executed across the evaluation period.
9. **Mean Holding Duration:** Average holding time measured in 5m bars.
10. **Fee Drag (% and bps):** Cumulative exchange fees paid.
11. **Slippage and Spread Drag (% and bps):** Execution cost relative to reference price.
12. **Funding Settlement Impact (USDT):** Net cash flows from 8-hour perpetual funding settlements.

### 6.3 Activity Tier Classification

To prevent data-mining on unreliably small sample sizes, trade frequency must be categorized against the `600 COMPLETED TRADES PER ASSET PER YEAR` benchmark:
- `< 150 trades/year:` `LOW_ACTIVITY` (Statistically unpowered)
- `150 - 300 trades/year:` `MODERATE_ACTIVITY`
- `300 - 600 trades/year:` `ACTIVE`
- `600 - 1200 trades/year:` `AGGRESSIVE` (Target research zone)
- `> 1200 trades/year:` `HIGH_FREQUENCY`

### 6.4 Accounting Separations and Funding Conventions

1. **Reference-Price Accounting vs. Execution Accounting:**
   - Reference Price PnL ($L_{\text{price,ref}}$): PnL evaluated at nominal decision prices (`open[i+1]`).
   - Execution Cost ($C_{\text{exec,total}}$): Signed price difference between actual fill and reference price:
     $$C_{\text{exec,total}} = C_{\text{exec,entry}} + C_{\text{exec,exit}}$$
     $$C_{\text{exec,entry}} = q \cdot d \cdot (P_{\text{entry,exec}} - P_{\text{entry,ref}})$$
     $$C_{\text{exec,exit}} = q \cdot (-d) \cdot (P_{\text{exit,exec}} - P_{\text{exit,ref}})$$
     where $d = +1$ for Long and $d = -1$ for Short.
   - Realized PnL:
     $$L_{\text{realized}} = L_{\text{price,ref}} + C_{\text{exec,total}} + C_{\text{fees}} - CF_{\text{funding}}$$
2. **Historical Funding vs. Parametric Scenarios:**
   - Canonical 5m Parquets do NOT contain historical perpetual funding rates (`FUNDING_DATA_UNAVAILABLE`).
   - Rather than fabricating historical funding timestamps, Track 2 must report under **Parametric Funding Scenarios**:
     - Scenario 0: Zero funding ($F_0 = 0.0\%$).
     - Scenario 1: Baseline neutral funding ($F_{\text{baseline}} = +0.01\%$ per 8 hours).
     - Scenario 2: Adverse regime funding ($F_{\text{adverse}} = +0.03\%$ per 8 hours against the position).
3. **Partial-Fill Cost Basis Allocation:**
   - Evaluated under both Average Cost Basis and FIFO ($Q_{\text{closed}} \le Q_{\text{open}}$).

---

## 7. TRACK 3 METHODOLOGY  -  INDEPENDENT STRATEGY RESEARCH

### 7.1 Objective and Definition

Track 3 treats the model's output probabilities as raw, uncalibrated alpha scores and evaluates downstream trading strategies designed to maximize risk-adjusted returns through asymmetric payoff engineering, dynamic stops, and order execution heuristics.

```
+----------------------------------------------------------------------------------------------------+
|                                    TRACK 3 RESEARCH ARCHITECTURE                                   |
+----------------------------------------------------------------------------------------------------+
|  [Model Probabilities] ---> [Entry Threshold Filter] ---> [Asymmetric Bracket Sizing]              |
|                                                                     |                              |
|  [Banker Lifecycle FSM] <--- [Dynamic Trailing Stop] <--- [Partial TP1 Ratchet]                    |
+----------------------------------------------------------------------------------------------------+
```

### 7.2 Candidate Strategy Mechanisms

1. **Asymmetric Take-Profit / Stop-Loss:** Decoupling TP from SL (e.g., $1.0\sigma$ SL with $2.5\sigma$ TP).
2. **ATR-Based Structural Invalidation:** Anchoring stops to local volatility extremes ([`AnalystAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/analyst.py#L95)).
3. **Partial Take-Profit Ladders:** Realizing 50% of position size at TP1 ($2.0R$) and holding 50% for TP2 ($3.2R$) ([`SniperAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/sniper.py#L86)).
4. **Option A Breakeven Stop Ratchet:** Shifting stop-loss to entry price immediately upon confirmed TP1 execution ([`BankerAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/banker.py#L136)).
5. **Dynamic Trailing Stops:** Ratcheting stops by $1.5 \times \text{ATR}$ once profit exceeds $2.0R$ ([`BankerAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/banker.py#L143)).
6. **Holding-Time Limits:** Forcing market exit after $H$ bars regardless of barrier status.
7. **Regime-Dependent Parameter Switching:** Adjusting barrier widths based on [`AnalystAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/analyst.py#L57) market regimes (`TREND_IMPULSE` vs. `MEAN_REVERT_RANGE`).

### 7.3 Tunable Hyperparameter Search Space

The parameter search space for Track 3 optimization is defined below:

```text
+------------------------------+--------------------+------------------------+-------------------------------+
| Hyperparameter               | Symbol             | Candidate Range        | Step / Values                 |
+------------------------------+--------------------+------------------------+-------------------------------+
| Entry Probability Threshold  | tau_entry          | [0.50, 0.70]           | 0.50, 0.55, 0.60, 0.65, 0.70  |
| Stop-Loss ATR Multiplier     | k_SL               | [1.0, 2.5]             | 1.0, 1.25, 1.5, 2.0, 2.5      |
| TP1 R-Multiple               | R_TP1              | [1.5, 3.0]             | 1.5, 2.0, 2.5, 3.0            |
| TP1 Volume Fraction          | f_TP1              | [0.33, 0.67]           | 0.33, 0.50, 0.67              |
| TP2 R-Multiple               | R_TP2              | [2.5, 5.0]             | 2.5, 3.2, 4.0, 5.0            |
| Trailing Activation R        | R_trail            | [1.5, 3.0]             | 1.5, 2.0, 2.5                 |
| Maximum Holding Bars         | H_max              | [6, 48]                | 6, 12, 24, 48 bars            |
+------------------------------+--------------------+------------------------+-------------------------------+
```

### 7.4 Overfitting Controls and Validation Protocol

Strategy optimization introduces severe data-mining and overfitting risks. Track 3 must enforce strict procedural controls:

1. **Purged In-Sample / Out-of-Sample Partitioning:**
   - **Optimization Set (In-Sample):** Folds 1 through 4 of the purged time-series cross-validation split ([`temporal_split.py`](file:///d:/quantum-multi-agent/src/quantum/features/temporal_split.py#L15)).
   - **Validation Set (Out-of-Sample):** Fold 5 strictly sealed during hyperparameter tuning and evaluated exactly once after parameter freeze.
2. **Multiple-Testing Correction ($K_{\text{Track3}}$):**
   - The total number of strategy variants evaluated ($K_{\text{Track3}}$) must be pre-registered.
   - Holm-Bonferroni family-wise error rate (FWER) correction must be applied to all performance p-values:
     $$p_{(i)} \le \frac{\alpha}{K_{\text{Track3}} - i + 1}$$
3. **Step-by-Step Ablation Schedule:**
   - Step 0 (Baseline): Track 2 re-anchored symmetric barriers.
   - Step 1: Base + Entry threshold filtering ($\tau_{\text{entry}}$).
   - Step 2: Step 1 + Asymmetric TP/SL ratios.
   - Step 3: Step 2 + Partial TP1 take-profit and breakeven stop ratchet.
   - Step 4: Step 3 + Dynamic trailing stop.
   - Step 5: Step 4 + Macro regime filter.

---

## 8. FAIR COMPARISON METHODOLOGY

To guarantee that comparative evaluations between Track 1, Track 2, and Track 3 remain unbiased and scientifically valid, nine core fairness criteria are enforced:

```text
+----+-----------------------------------------+-------------------------------------------------------------+
| #  | Fairness Question                       | Procedural Guarantee                                        |
+----+-----------------------------------------+-------------------------------------------------------------+
| 1  | Are identical frozen models used?       | YES. All tracks evaluate identical frozen Phase 5.3 models.|
| 2  | Are data periods identical?             | YES. Evaluated across identical 5-fold temporal splits.    |
| 3  | Are transaction costs applied fairly?   | YES. Identical cost sweep tiers (0, 15, 20, 30 bps).       |
| 4  | Does Track 3 have an unfair advantage?  | CONTROLLED. Fitted on Folds 1-4; verified OOS on Fold 5.   |
| 5  | How is multiple-testing limited?        | Holm-Bonferroni correction over pre-registered K variants. |
| 6  | Is look-ahead bias prevented?           | YES. Purged 12-bar gap, 24-bar embargo, open[i+1] entry.   |
| 7  | How are overlapping trades handled?     | Single-position FSM constraint; zero simultaneous entries.  |
| 8  | Is post-hoc cherry-picking avoided?     | Parameter freeze required prior to unsealing Fold 5 OOS.   |
| 9  | Are distinct estimands separated?       | YES. Reporting is segregated into Group A and Group B.     |
+----+-----------------------------------------+-------------------------------------------------------------+
```

### 8.1 Reporting Group Segregation

Cross-track reporting must never compare non-comparable estimands directly. Results must be partitioned into two distinct reporting groups:

- **GROUP A: PREDICTIVE PERFORMANCE (Statistical Scoring):**
  - Scope: Track 1.
  - Primary Metrics: Balanced Accuracy, ROC-AUC, PR-AUC, ECE Calibration Error, Brier Score, Coverage.
  - Prohibited Metrics: Net PnL, Profit Factor, Dollar Returns.
- **GROUP B: ECONOMIC & STRATEGY PERFORMANCE (Financial Realization):**
  - Scope: Track 2 and Track 3.
  - Primary Metrics: Net Expectancy (bps), Profit Factor, Max Drawdown, Annualized Sharpe Ratio, Fee Drag.
  - Relative Assessment: Track 3 Net PnL is reported as an incremental spread relative to Track 2 baseline ($\Delta \text{PnL} = \text{PnL}_{\text{Track3}} - \text{PnL}_{\text{Track2}}$).

---

## 9. EXPERIMENT EXECUTION BLUEPRINT

A structured, six-stage execution workflow is defined for implementation upon governance authorization:

```text
+----------------------------------------------------------------------------------------------------+
|                               SIX-STAGE EXPERIMENT EXECUTION WORKFLOW                              |
+----------------------------------------------------------------------------------------------------+
|  [Stage 1: Data Prep] --------> [Stage 2: Track 1 Predictive Eval]                                 |
|                                         |                                                          |
|                                         v                                                          |
|  [Stage 3: Track 2 Economic Benchmark] -> [Stage 4: Track 3 Optimization (Folds 1-4)]              |
|                                                          |                                         |
|                                                          v                                         |
|  [Stage 6: Comparative Reporting] <------ [Stage 5: Track 3 OOS Validation (Fold 5)]                |
+----------------------------------------------------------------------------------------------------+
```

### Stage 1: Data Preparation & Partition Integrity
- **Objective:** Verify integrity and temporal isolation of canonical datasets and out-of-fold predictions.
- **Inputs:** Canonical 5m Parquets ([`data/historical/canonical/`](file:///d:/quantum-multi-agent/data/historical/canonical/)), frozen OOF parquets ([`artifacts/phase_5_4/materialized_oof/`](file:///d:/quantum-multi-agent/artifacts/phase_5_4/materialized_oof/)).
- **Responsible Module:** [`src/quantum/features/temporal_split.py`](file:///d:/quantum-multi-agent/src/quantum/features/temporal_split.py).
- **Outputs:** Verified sample partition index with confirmed 12-bar purge and 24-bar embargo boundaries.
- **Validation Check:** SHA-256 match against [`frozen_artifact_manifest.json`](file:///d:/quantum-multi-agent/artifacts/phase_5_3_freeze/frozen_artifact_manifest.json). Zero timestamp overlaps across folds.
- **Failure Condition:** Checksum mismatch or detected temporal leakage aborts execution.
- **Approval Dependency:** Automatic verification check; no human intervention needed.

### Stage 2: Track 1 Predictive Evaluation
- **Objective:** Calculate frozen model classification metrics against close-anchored training labels.
- **Inputs:** Materialized OOF Parquets, [`ModelEvaluationContract`](file:///d:/quantum-multi-agent/src/quantum/ml/evaluation.py#L21).
- **Responsible Module:** [`src/quantum/ml/evaluation.py`](file:///d:/quantum-multi-agent/src/quantum/ml/evaluation.py).
- **Outputs:** `TRACK_1_PREDICTIVE_EVALUATION_REPORT.json` (Accuracy, AUC, ECE, Brier score).
- **Validation Check:** Metrics match historical Phase 5.4.3 baseline values within $\pm 10^{-5}$.
- **Failure Condition:** Inability to replicate frozen Phase 5.4.3 benchmark metrics.
- **Approval Dependency:** Prerequisite for Proceeding to Stage 3.

### Stage 3: Track 2 Re-Anchored Economic Accounting
- **Objective:** Simulate open[i+1] re-anchored symmetric barrier execution across all cost tiers.
- **Inputs:** Canonical 5m Parquets, OOF model probabilities, fee schedules (0, 15, 20, 30 bps).
- **Responsible Module:** `src/quantum/backtesting/engine.py` (New Engine) + Reference Accounting Engine.
- **Outputs:** `TRACK_2_ECONOMIC_BENCHMARK_REPORT.json` (12 required reporting metrics).
- **Validation Check:** Trade count categorized into activity tiers; reference PnL matches identity.
- **Failure Condition:** Wall-clock coupling failure or arithmetic divergence in PnL identity.
- **Approval Dependency:** Requires Human Sign-Off on DEC_01 (Alternative B).

### Stage 4: Track 3 Strategy Optimization (Folds 1–4)
- **Objective:** Perform grid search over candidate strategy parameters on In-Sample folds.
- **Inputs:** Folds 1-4 trade events, [`SniperAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/sniper.py#L22), [`BankerAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/banker.py#L24), [`RiskAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/risk.py#L80).
- **Responsible Module:** Strategy Search Runner.
- **Outputs:** Parameter performance surface, optimal candidate configuration, frozen parameter manifest.
- **Validation Check:** Folds 1-4 optimization only; Fold 5 strictly inaccessible.
- **Failure Condition:** Fold 5 data accessed or modified during search.
- **Approval Dependency:** Requires Human Sign-Off on DEC_01 (Alternative C).

### Stage 5: Track 3 Out-of-Sample Validation (Fold 5)
- **Objective:** Evaluate frozen optimal strategy parameters on unsealed Fold 5.
- **Inputs:** Frozen Stage 4 parameter manifest, Fold 5 canonical market candles.
- **Responsible Module:** `src/quantum/backtesting/engine.py` using frozen parameters.
- **Outputs:** `TRACK_3_OUT_OF_SAMPLE_REPORT.json` with Holm-Bonferroni adjusted p-values.
- **Validation Check:** Single pass execution with frozen parameters; zero post-hoc tuning.
- **Failure Condition:** Parameter modification or multiple passes on Fold 5.
- **Approval Dependency:** Formal parameter lock verification.

### Stage 6: Comparative Reporting & Synthesis
- **Objective:** Synthesize results from all three tracks into consolidated executive tables.
- **Inputs:** Outputs from Stages 2, 3, and 5.
- **Responsible Module:** Reporting Generator.
- **Outputs:** Consolidated Three-Track Evaluation Dossier.
- **Validation Check:** Clean separation between Group A (predictive) and Group B (economic) metrics.
- **Failure Condition:** Conflation of predictive metrics with economic returns.
- **Approval Dependency:** Final Human Governance Review.

---

## 10. RESOURCE AND PERFORMANCE AUDIT

The quantitative research framework must execute within strict operational limits:

```text
+------------------------------------+-----------------------+---------------------------------------+
| Operational Constraint             | Permitted Boundary    | Architectural Compliance Status       |
+------------------------------------+-----------------------+---------------------------------------+
| Processing Unit                    | CPU-first             | COMPLIANT (LightGBM CPU inference)    |
| Maximum CPU Threads                | <= 2 threads          | COMPLIANT (MLConfig.max_cpu_threads=2)|
| Maximum RAM Usage                  | <= 1.0 GB peak        | RISK IDENTIFIED (Requires streaming)  |
| Processing Mode                    | Sequential / Bounded  | COMPLIANT (Asset-by-asset processing) |
| GPU Requirement                    | ZERO (No GPU used)    | COMPLIANT                             |
+------------------------------------+-----------------------+---------------------------------------+
```

### 10.1 Code Bottlenecks and Optimization Targets

Inspection of the codebase identified four computational bottlenecks:

1. **Iterative Triple Barrier Labeling ([`labeling.py:L142-230`](file:///d:/quantum-multi-agent/src/quantum/features/labeling.py#L142-L230)):**
   - *Code:* `TripleBarrierLabelGenerator._generate_sample_matrix` iterates row-by-row using Python `for` loops across 260,000 candles.
   - *Risk:* High CPU execution time (>60 seconds per asset).
   - *Fix:* Replace with vectorized rolling window operations or bounded Polars expressions.
2. **Feature Matrix In-Memory Allocations ([`engine.py:L109-178`](file:///d:/quantum-multi-agent/src/quantum/features/engine.py#L109-L178)):**
   - *Code:* `FeatureEngine._compute_features_worker` constructs 36 continuous feature columns simultaneously for 316,000 bars in a single Pandas DataFrame.
   - *Risk:* Memory spikes to ~850 MB, nearing the 1.0 GB limit.
   - *Fix:* Stream features fold-by-fold and cast float64 tensors to float32.
3. **Synchronous Telemetry Recording ([`orchestrator.py:L380-420`](file:///d:/quantum-multi-agent/src/quantum/agents/orchestrator.py#L380-L420)):**
   - *Code:* `PipelineOrchestrator._record_run_start` commits SQLite records synchronously on every evaluated candle.
   - *Risk:* Disk I/O bottlenecks in historical simulations.
   - *Fix:* Disable SQLite logging during batch backtests; aggregate metrics in-memory.
4. **Full Parquet Out-of-Fold Ingestion:**
   - *Code:* Materialized OOF files in [`artifacts/phase_5_4/materialized_oof/`](file:///d:/quantum-multi-agent/artifacts/phase_5_4/materialized_oof/) reach 261,488 rows.
   - *Risk:* Loading multiple assets concurrently exceeds 1.0 GB RAM.
   - *Fix:* Enforce sequential, asset-by-asset execution; invoke Python garbage collection (`gc.collect()`) between folds.

---

## 11. ARCHITECTURE GAPS

The technical audit identified eight concrete architectural gaps in [`src/quantum/`](file:///d:/quantum-multi-agent/src/quantum/):

```text
+-------+---------------------------------------+-----------------------------------------------------------+
| Gap # | Identified Architecture Gap           | Source Location & Evidence                                |
+-------+---------------------------------------+-----------------------------------------------------------+
| GAP 1 | Hardcoded Placeholder Probabilities   | scout.py:L47-51, analyst.py:L51-55, sniper.py:L86-97      |
| GAP 2 | Wall-Clock Host Coupling              | risk.py:L94,L119, banker.py:L62,L295 (time.time() * 1000) |
| GAP 3 | Misnamed Banker / Missing PnL Ledger  | banker.py:L24-368 (acts as order FSM, lacks PnL ledger)   |
| GAP 4 | Disconnected Banker in Orchestrator   | orchestrator.py:L51-518 (never invokes BankerAgent)       |
| GAP 5 | Missing Historical Backtesting Engine | src/quantum/ (no backtesting/ or simulation engine)       |
| GAP 6 | Missing Reference-Price PnL Module    | ISS_10 = NOT_VERIFIED (no L_realized accounting code)     |
| GAP 7 | Target Horizon Discrepancy            | labeling.py:L39 (12 bars) vs narrative specs (288 bars)  |
| GAP 8 | Incomplete Risk Telemetry Defaults    | orchestrator.py:L260-274 (omits drawdown/loss tracking)   |
+-------+---------------------------------------+-----------------------------------------------------------+
```

---

## 12. RISKS AND UNRESOLVED GOVERNANCE QUESTIONS

The execution of any backtest remains blocked by eleven registered issues and six pending decisions:

### 12.1 Unresolved Issues Linkage ([`ISS_01` through `ISS_11`])
- [`ISS_01`]: Execution slippage accounting model requires formal verification.
- [`ISS_02`]: Historical perpetual funding rate data is unavailable (`FUNDING_DATA_UNAVAILABLE`).
- [`ISS_03`]: 24-bar MBB autocorrelation assumptions require empirical validation.
- [`ISS_04`]: Prospective holdout access logging history is unverified (`NOT_VERIFIED`).
- [`ISS_05`]: Disaggregated reporting vs. execution authorization boundary.
- [`ISS_06`]: Monero (XMR) historical candle gap (83,863 vs 316,500 bars).
- [`ISS_07`]: Overlapping trade position conflicts in discrete simulation.
- [`ISS_08`]: Wall-clock coupling in `RiskAgent` prevents historical replay.
- [`ISS_09`]: Disconnected ML model registry in active agent evaluation paths.
- [`ISS_10`]: Mathematical reference-price PnL decomposition unverified in code.
- [`ISS_11`]: Target horizon discrepancy between code (12 bars) and specs (288 bars).

### 12.2 Human Governance Decisions Linkage ([`DEC_01` through `DEC_06`])
- **DEC_01 (Barrier Execution Architecture):** Select Alternative A (close-anchored), Alternative B (re-anchored economic), or Alternative C (downstream strategy).
- **DEC_02 (Directional Asset Scope):** Authorize Long-only vs. Long/Short disaggregated reporting.
- **DEC_03 (Perpetual Funding Rate Policy):** Select parametric funding scenario models.
- **DEC_04 (Statistical Evaluation & Resampling):** Approve calendar-time multi-asset MBB and Holm-Bonferroni correction.
- **DEC_05 (Portfolio Risk & Cost Allocation):** Authorize Average Cost Basis vs. FIFO partial fill allocation.
- **DEC_06 (XMR Eligibility Policy):** Approve 3-tier XMR research status.

---

## 13. RECOMMENDED NEXT STEPS

Before any historical backtest or research phase can be executed, the following pre-execution technical tasks must be completed in order:

```text
+------+---------------------------------------------------------------+-------------------------------------+
| Step | Pre-Execution Engineering Task                                | Verification Criteria               |
+------+---------------------------------------------------------------+-------------------------------------+
| 1    | Human Decision Sign-off on DEC_01 through DEC_06              | Completed Human Decision Worksheet  |
| 2    | Implement Simulated Clock Injection in Risk & Banker Agents   | eval_timestamp_ms replaces wall-time|
| 3    | Connect Scout, Analyst, Sniper to ModelRegistry & OOF Data    | Eliminate hardcoded probabilities   |
| 4    | Construct Dedicated Discrete-Event Backtest Runner Engine     | src/quantum/backtesting/engine.py   |
| 5    | Implement Reference-Price & Funding PnL Accounting Engine    | Mathematically verified test suite  |
| 6    | Reconcile & Formally Lock Target Horizon (12 bars)            | Manifest and contracts updated      |
| 7    | Execute Stage 1 & Stage 2 (Track 1 Predictive Benchmark)     | Replicate Phase 5.4.3 metrics       |
| 8    | Execute Stage 3 (Track 2 Re-Anchored Economic Baseline)       | Generate 12 required metrics        |
| 9    | Pre-register Track 3 Parameter Space & Run Folds 1-4 Tuning   | Freeze manifest prior to Fold 5     |
+------+---------------------------------------------------------------+-------------------------------------+
```

---

## 14. GOVERNANCE DISCLAIMER

This document is a technical architecture audit and scientific experiment specification only. 

> [!IMPORTANT]
> **GOVERNANCE STATUS REAFFIRMATION:**  
> - Phase 5.5 Research Status: `NOT_STARTED`  
> - Phase 5.6 Authorization Status: `NOT_AUTHORIZED`  
> - Economic Backtesting Status: `NOT_STARTED`  
> - Decisions DEC_01 through DEC_06: `PENDING_HUMAN_DECISION`  
> - Prospective Holdout Partition: `STRICTLY_SEALED`  
> - Frozen Phase 5.3 Models & Phase 5.4 Preprocessors: `IMMUTABLE`  
>
> No research backtest has been executed. No trading models have been altered. No prospective holdout data has been accessed. No strategy or model is asserted to be profitable. All operational authorizations remain under the exclusive authority of the Human Governance Supervisor.

---
*End of Architectural Audit & Experiment Design Specification.*
