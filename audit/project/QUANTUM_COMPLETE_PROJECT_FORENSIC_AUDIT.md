# QUANTUM — Complete Project Forensic Audit

**Document Identifier:** `audit/project/QUANTUM_COMPLETE_PROJECT_FORENSIC_AUDIT.md`  
**Audit Timestamp:** 2026-11-03T02:18:00+07:00  
**Git Commit Baseline:** `dcc8ceb54d80b1b9685d92236f48b0994610522a`  
**Authority:** Project Owner / Human Governance Supervisor  
**Scope:** Complete end-to-end forensic inspection of repository code, 6-agent architecture, 11 frozen specialist models, historical datasets, backtesting engines, and previous experimental phases (Phases 5.1–5.6.2, Tracks 1–3, Phases 6A–6B).

---

## 1. Repository Inventory & Component Disposition

Every major module in `D:\quantum-multi-agent` was inspected directly against source code and runtime tests.

| Component Path | Actual Responsibility | Dependencies | Implementation Status | Verification Evidence | Known Limitations | Disposition |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `src/quantum/agents/contracts.py` | Immutable Pydantic v2 data schemas (`ScoutInput/Output`, `AnalystInput/Output`, `SniperInput/Output`, `RiskInput/Output`, `BankerInput/Output`, `TrackedPosition`, `PositionExecutionEvent`). | `pydantic`, `quantum.domain` | Operational | `test_contracts.py` (5 passed) | Lacks explicit `strategy_id` / `config_hash` metadata fields on `SniperInput` for multi-strategy routing. | **PRESERVE & EXTEND** (add optional `strategy_id` / `config_hash` fields) |
| `src/quantum/agents/scout.py` | Opportunity discovery, Stage D candidate filtering, wick-trap & probability screening. | `ModelRegistry`, `MLConfig`, `contracts` | Operational | `test_agents.py`, `test_ml_pipeline.py` | When `active_model` is present, line 51 uses a static placeholder `prob = 0.65` instead of querying materialized OOF or dynamic strategy features. | **PRESERVE & INTEGRATE** with strategy layer |
| `src/quantum/agents/analyst.py` | Market regime classification (`TREND_IMPULSE`, `MEAN_REVERT_RANGE`, `LOW_LIQ_CHOP`, `HIGH_VOL_EXHAUSTION`), ATR invalidation anchoring. | `ModelRegistry`, `MLConfig`, `contracts` | Operational | `test_agents.py` | Uses fixed 15m heuristics unless strategy parameters override regime thresholds. | **PRESERVE & INTEGRATE** with strategy layer |
| `src/quantum/agents/sniper.py` | Trade proposal construction, entry price, stop loss, TP1/TP2 geometry, expected net R calculation. | `ModelRegistry`, `MLConfig`, `contracts`, `TradeProposal` | Operational | `test_agents.py` | Hardcodes `expected_holding_minutes = 120` and `OrderType.LIMIT` unless parameterized by a strategy configuration. | **PRESERVE & INTEGRATE** with strategy layer |
| `src/quantum/agents/risk.py` | Independent non-bypassable 12-gate deterministic risk engine & position sizer. | `RiskConfig`, `contracts`, `RiskDecision` | Operational | `test_risk.py` | Gate 10 defaults `min_notional_usdt = 10.0` and `lot_step = 0.001`; on a `$100 USD` account with 50 bps risk budget (`$0.50` risk), tight stops or coarse lot steps cause `VETO_BELOW_MIN_NOTIONAL` on high-priced assets unless exchange-accurate lot steps and min notionals (`$5.00`) are supplied. | **PRESERVE** (non-bypassable control; pass accurate exchange lot step / min notional in `RiskInput`) |
| `src/quantum/agents/banker.py` | Deterministic position lifecycle FSM (`PENDING_OPEN` -> `OPEN` -> `PARTIALLY_CLOSED` -> `CLOSED`), Option A breakeven ratchet on TP1 fill, monotonic stop tightening. | `MLConfig`, `contracts` | Operational | `test_banker.py` | Enforces idempotent sequence numbers; requires explicit `PositionExecutionEvent` objects. | **PRESERVE** |
| `src/quantum/agents/orchestrator.py` | Coordinates `Scout -> Analyst -> Sniper -> Risk` with strict latency timeouts (50ms/50ms/50ms/25ms), EventBus telemetry, and SQLite audit logging. | All agents, `EventBus`, `DatabaseManager` | Operational | `test_orchestrator.py` | Coordinates up to `Risk` decision; `Banker` lifecycle feedback loop is invoked separately by execution engine. | **PRESERVE & EXTEND** (add strategy-aware evaluation method linking `Banker` execution feedback) |
| `src/quantum/backtesting/accounting.py` | Reference-price two-legged PnL accounting, signed maker/taker fees, half-spread slippage, 8h funding settlements, partial close accounting. | `pydantic`, `TradeSide` | Operational | `test_backtest_accounting.py` (9 passed) | Designed for isolated position accounting; portfolio cash/margin constraints handled at engine level. | **PRESERVE** |
| `src/quantum/backtesting/adapters.py` | Causal OOF probability loader for `artifacts/phase_5_4/materialized_oof/*.parquet`, enforces `PROSPECTIVE_HOLDOUT_START_MS = 1793491200000`. | `pyarrow`, `pandas`, `numpy` | Operational | `test_backtest_adapters.py` | Strictly read-only on frozen Phase 5.3 OOF predictions. | **PRESERVE** |
| `src/quantum/backtesting/engine.py` | Phase 5.5 Track 2 causal discrete-event backtest runner (Modes 1, 2, 3). | `accounting`, `adapters`, `BankerAgent`, `RiskAgent` | Operational | `test_backtest_engine.py` (15 passed) | Restricted to fixed 12-bar horizon and Track 2 single-stage exit benchmark. | **PRESERVE** |
| `src/quantum/backtesting/phase562_engine.py` | Phase 5.6.2 multi-asset backtest and portfolio simulator. | `adapters`, `resources`, `pandas`, `numpy` | Operational | `test_phase562_engine.py` (8 passed) | Built for 6-stage mandate; needs extension for `$100 USD` capital constraints, 100+ strategy batch discovery, and 6-agent pipeline integration. | **PRESERVE & EXTEND** |
| `src/quantum/ml/feature_engineering.py` | Causal technical & microstructure feature pipeline (ATR, RVOL, RSI, wick trap, volatility ratios). | `numpy`, `pandas` | Operational | `test_feature_engineering.py` (7 passed) | Frozen feature definitions for Phase 5.3 models. | **PRESERVE** |
| `src/quantum/data/` & `src/quantum/exchange/` | Canonical Parquet storage (`exchange=ASTER`), Bybit & Aster REST/WS clients, normalizers, freshness monitors. | `aiohttp`, `pyarrow`, `sqlite3` | Operational | `test_aster_clients.py`, `test_bybit_clients.py`, `test_historical_collection.py` | Live exchange execution disabled by governance policy. | **PRESERVE** |
| `src/quantum/daemon/` & `desktop/QuantumDesktop/` | Phase 6A FastAPI + WebSocket paper-trading daemon & Phase 6B C# Avalonia MVVM desktop app. | `fastapi`, `uvicorn`, `.NET 8/9` | Suspended per Directive | `test_paper_daemon.py` | Suspended pending Phase 5.6.2 strategy discovery completion. | **PRESERVE (SUSPENDED)** |

---

## 2. Six-Agent Architecture Audit

The repository implements six collaborative agents in `src/quantum/agents/` plus `contracts.py`:

1. **Scout (`ScoutAgent` in `src/quantum/agents/scout.py`):**
   - **Role:** Scans candidate instruments, evaluates directional bias, opportunity category, `rvol_15m`, `rsi_15m`, `wick_trap_ratio`, and `spread_bps`, and emits `ScoutOutput` (`PROCEED` or `SKIP`).
   - **Finding:** Functional and fast (<1 ms). Needs strategy configuration binding so candidate filtering thresholds (`min_probability`, `max_wick_trap`, microstructure filters) reflect the active `StrategyConfiguration`.
2. **Analyst (`AnalystAgent` in `src/quantum/agents/analyst.py`):**
   - **Role:** Evaluates `ScoutOutput` + `MarketContext`, classifies `MarketRegime` (`TREND_IMPULSE`, `MEAN_REVERT_RANGE`, `HIGH_VOL_EXHAUSTION`, `LOW_LIQ_CHOP`) and `volatility_regime`, computes ATR-based `invalidation_price` and support/resistance levels, and emits `AnalystOutput`.
   - **Finding:** Functional. Needs strategy configuration binding so regime activation rules and OOF probability margins (`max(p_long, p_short) - p_neutral`) are evaluated according to the strategy's hypothesis.
3. **Sniper (`SniperAgent` in `src/quantum/agents/sniper.py`):**
   - **Role:** Consumes `AnalystOutput` and `ScoutOutput`, selects direction (`LONG`/`SHORT`), order type (`MARKET`/`LIMIT`), entry price/zone, `stop_loss`, `take_profit_1`, `take_profit_2`, `tp1_close_pct`, and `expected_holding_minutes`, emitting `SniperOutput` containing a validated `TradeProposal`.
   - **Finding:** Functional. Must be parameterized by `StrategyConfiguration` so each strategy's TP/SL multipliers, partial close percentages, limit offsets, and holding horizons govern the generated `TradeProposal`.
4. **Risk (`RiskAgent` in `src/quantum/agents/risk.py`):**
   - **Role:** Independent, non-bypassable 12-gate safety engine (`SIGNAL_FRESHNESS`, `DRAWDOWN_CIRCUIT_BREAKER`, `DAILY_LOSS_LIMIT`, `LOSS_STREAK_COOLDOWN`, `MAX_CONCURRENT_POSITIONS`, `STOP_GEOMETRY_VALID`, `MAX_SPREAD`, `MIN_NET_RR`, `MAX_SLIPPAGE`, `LOT_STEP_AND_MIN_NOTIONAL`, `MAX_EXPOSURE_AND_LEVERAGE`, `LIQUIDATION_BUFFER`).
   - **Finding:** Strictly deterministic and non-bypassable. Under `$100 USD` initial capital, Gate 10 (`LOT_STEP_AND_MIN_NOTIONAL`) and Gate 11 (`MAX_EXPOSURE_AND_LEVERAGE`) actively constrain position sizing. Specifically, with `$100` equity, a `$5.00` exchange minimum notional represents `5.0%` of account equity (`0.05x` leverage). If a strategy specifies a tiny position or if lot-step rounding truncates notional below the minimum threshold, `RiskAgent` vetoes the trade with `VETO_BELOW_MIN_NOTIONAL`.
5. **Banker (`BankerAgent` in `src/quantum/agents/banker.py`):**
   - **Role:** Manages order placement, partial fills (`TP1_FILL`, `TP2_FILL`), stop ratcheting to breakeven (Option A), trailing stop ratchets, order expiration, and position closure (`SL_FILL`, `TIME_EXIT`, `MANUAL_CLOSE`).
   - **Finding:** Complete deterministic FSM.
6. **Orchestrator (`PipelineOrchestrator` in `src/quantum/agents/orchestrator.py`):**
   - **Role:** Sequences `Scout -> Analyst -> Sniper -> Risk -> Banker -> Execution Feedback`, enforces timeouts, resolves conflicts across concurrent proposals, and records full provenance.

---

## 3. Audit of Frozen Specialist Models (Phase 5.3 & Phase 5.4)

All 11 specialist models are 3-class LightGBM classifiers (`raw_prob_m1` = SL/-1, `raw_prob_0` = EXP/0, `raw_prob_p1` = TP/+1) trained on 5-minute canonical candles (`exchange=ASTER`) using 5-fold purged walk-forward cross-validation.
- **Confirmatory OOF Sample (Folds 1–4):** `2025-01-29 11:20 UTC` to `2026-01-29 14:35 UTC` (`365.14 days` = `1.00 year`, ~104,544 bars per primary asset).
- **Exploratory Sample (Fold 5):** `2026-01-29 15:40 UTC` to `2026-04-30 21:55 UTC` (`91.3 days`, ~26,140 bars; `OOS_ELIGIBILITY_NOT_VERIFIED`).
- **Prospective Holdout:** `>= 2026-11-01 00:00:00 UTC` (`1793491200000 ms`) — **STRICTLY SEALED** (verified max timestamp in OOF and canonical candles is `1777586100000 ms`, `2026-04-30 21:55 UTC`).

### Verified Predictive Performance (Folds 1–4 Pooled OOF from `artifacts/phase_5_5/track1_predictive_evaluation.json`)

| Specialist | Universe Tier | OOF Rows (F1–4) | Macro OvR ROC-AUC | Multiclass Brier | Top-1 Uniform ECE | AURCC Full | $\Delta$ AURCC (0.2–1.0) | Class Support (SL / EXP / TP) |
| :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| **BTCUSDT** | Primary | 104,544 | 0.6104 | 0.5843 | 0.0274 | 0.5517 | -0.0123 | 49,350 / 6,621 / 48,573 |
| **ETHUSDT** | Primary | 104,580 | 0.6285 | 0.5806 | 0.0231 | 0.5531 | -0.0108 | 48,524 / 6,990 / 49,066 |
| **BNBUSDT** | Primary | 104,676 | 0.6459 | 0.5806 | 0.0115 | 0.5249 | -0.0189 | 46,565 / 11,472 / 46,639 |
| **XRPUSDT** | Primary | 104,480 | 0.6351 | 0.5723 | 0.0096 | 0.5116 | -0.0222 | 48,406 / 9,102 / 46,972 |
| **ADAUSDT** | Primary | 104,384 | 0.6384 | 0.6502 | 0.0663 | 0.5747 | -0.0138 | 44,733 / 16,265 / 43,386 |
| **SOLUSDT** | Primary | 104,644 | 0.6214 | 0.5831 | 0.0251 | 0.5412 | -0.0145 | 49,189 / 6,348 / 49,107 |
| **AVAXUSDT** | Primary | 104,652 | 0.6379 | 0.6255 | 0.0175 | 0.5217 | -0.0349 | 40,112 / 24,819 / 39,721 |
| **LINKUSDT** | Primary | 104,620 | **0.6944** | 0.5935 | 0.0204 | **0.4224** | **-0.0563** | 36,231 / 31,848 / 36,541 |
| **DOGEUSDT** | Primary | 104,516 | **0.6663** | 0.5853 | 0.0193 | 0.5177 | -0.0220 | 45,379 / 15,054 / 44,083 |
| **LTCUSDT** | Primary | 104,368 | **0.6810** | 0.6049 | 0.0291 | 0.4493 | -0.0458 | 37,035 / 29,041 / 38,292 |
| **XMRUSDT** | Exploratory (DEC_06) | 12,200 | 0.5563 | 0.6280 | 0.0451 | 0.5484 | -0.0158 | 5,269 / 1,404 / 5,527 |

**Key Model Audit Findings:**
1. All 10 primary models exhibit genuine statistical discrimination (`ROC-AUC 0.610–0.694`, well above the `0.50` random baseline) and strong probability calibration (`ECE 0.0096–0.0663`).
2. `LINKUSDT` (`AUC 0.6944`, `ΔAURCC -0.0563`), `LTCUSDT` (`AUC 0.6810`, `ΔAURCC -0.0458`), and `DOGEUSDT` (`AUC 0.6663`) have the strongest selective abstention skill (risk decreases sharply as coverage is reduced).
3. However, in unconditional 5-minute barriers (`1.5 * sigma_t`), the median volatility $\sigma_t$ is only `10.3–21.0 bps`, meaning unconditional barrier widths (`15–31 bps`) are smaller than standard taker round-trip friction (`44.0 bps`).

---

## 4. Audit & Forensic Reconciliation of Historical Backtests

All previously cited backtest numbers across Phases 5.5, 5.6, and 5.6.2 were traced directly to their raw JSON artifacts on disk:

| Historical Experiment | Source Artifact Path | Trade Count Reconciled | Initial Equity | Fee / Slippage Model | Net Return | Max Drawdown | Root Cause of Performance |
| :--- | :--- | :--- | ---: | :--- | ---: | ---: | :--- |
| **Phase 5.5 Unconditional Baseline (Folds 1–4, 10 Primary Assets)** | `artifacts/phase_5_5/track2_economic_evaluation.json` | **215,640** (`217,786` incl. XMR) | Isolated $1,000/trade | 40 bps taker fee + 4 bps slippage (`44.0 bps` RT) | `-100%` (cum. `-9,397%` uncompounded) | `549%–1,228%` (uncompounded) | Gross expectancy is `+0.00` to `+2.76 bps`, which is overwhelmed by `44.0 bps` round-trip taker friction (`-41.25` to `-44.00 bps` net/trade). |
| **Phase 5.5 Unconditional Baseline (Folds 1–5 Overall)** | `artifacts/phase_5_5/track2_economic_evaluation.json` | **282,692** (10 assets) / **285,270** (11 assets) | Isolated $1,000/trade | `44.0 bps` RT taker | `-100%` | `>500%` | Same friction drag across all 5 folds. |
| **Phase 5.5 Mode 3 Portfolio Ledger** | `artifacts/phase_5_5/portfolio_evaluation.json` | **11,124** executed (halted at ruin) | `$10,000.00` | `44.0 bps` RT taker | **`-99.00%`** (ending `$99.84`) | **`99.00%`** | Portfolio compounded down to `$99.84`, where `10%` single-asset cap (`$9.98`) fell below the `$10.00` minimum notional gate, halting trading. |
| **Phase 5.6 Overlay `120 / 0.30`** | `artifacts/phase_5_6/overlay_validation_report.json` (`vol_120bps_margin_30pct`) | **543** candidate / **479** portfolio executed | `$10,000.00` | Maker-Passive (`8.0 bps` RT) | **`-5.31%`** (ending `$9,468.92`) | **`8.24%`** | Uniform `1.5*sigma >= 120 bps` filter across all 10 assets included unprofitable short trades and low-edge BTC/ETH trades (`-1.43 bps` net expectancy). |
| **Phase 5.6 Overlay `160 / 0.30`** | `artifacts/phase_5_6/overlay_validation_report.json` (`vol_160bps_margin_30pct`) | **103** candidate / **102** portfolio executed | `$10,000.00` | Maker-Passive (`8.0 bps` RT) | **`-2.97%`** (ending `$9,702.74`) | **`5.46%`** | Extreme volatility tail (`1.5*sigma >= 160 bps`) starved trade frequency to ~10 trades/asset/year; bidirectional short losses offset long gains. |
| **Phase 5.6 Overlay `160 / 0.20`** | `artifacts/phase_5_6/overlay_validation_report.json` (`vol_160bps_margin_20pct`) | **194** candidate / **175** portfolio executed | `$10,000.00` | Maker-Passive (`8.0 bps` RT) | **`-3.77%`** (ending `$9,623.26`) | **`9.54%`** | Previously misreported in Phase 6A directive by mixing per-asset cherry-picked thresholds with the uniform `160/0.30` portfolio ledger (reconciled in `phase_5_6_overlay_forensic_reconciliation_report.md`). |
| **Phase 5.6.2 Forced 600 Trades/Yr Uniform Fleet** | `artifacts/phase_5_6_2/phase562_research_results.json` | **5,781** candidate / **4,525** portfolio executed | `$10,000.00` | Maker (`8 bps`) / Hybrid (`15 bps`) / Taker (`44 bps`) | `-30.66%` / `-49.48%` / `-86.40%` | `30.71%` / `49.52%` / `86.41%` | Forcing all 10 assets to trade ~600 times/year bidirectionally diluted conviction and included heavy altcoin short losses (`-8` to `-20 bps`/trade). |

---

## 5. Why Previous Approaches Failed to Demonstrate Integrated Portfolio Alpha

Forensic synthesis of Phases 5.5, 5.6, and 5.6.2 establishes four root causes of previous portfolio failures:
1. **Unconditional Bidirectional Execution in a Structural Bull/Expansion Regime:** Across Folds 1–4 (2025–2026), short signals on altcoins (`AVAX`, `ADA`, `BNB`, `SOL`, `DOGE`) suffered `-8.2` to `-20.3 bps` net expectancy per trade, whereas long signals on `LINK`, `AVAX`, and `DOGE` were net profitable. Forcing symmetric long/short trading destroyed positive long alpha.
2. **Uniform Cross-Asset Parameterization:** Applying identical volatility and probability thresholds to `BTCUSDT` (median $\sigma = 10.3\text{ bps}$, `AUC = 0.610`) and `LINKUSDT` (median $\sigma = 20.8\text{ bps}$, `AUC = 0.694`) either starved `BTC` of trades or flooded `LINK` with low-quality signals.
3. **Single-Feature Gate Over-Simplicity:** Previous overlays gated solely on `20-bar close std` and `raw_prob_margin`, ignoring microstructure absorption (wick rejection, volume surges), higher-timeframe trend alignment (1h/4h momentum), cross-asset BTC/ETH leadership, and multi-stage partial profit ratcheting (`BankerAgent` Option A breakeven ratchet).
4. **Lack of `$100 USD` Micro-Capital Mechanics:** Previous portfolio simulations assumed `$10,000 USD` initial equity with a `30%` gross exposure cap and `$10.00` minimum notional. On a **`$100 USD` initial capital account**, exchange minimum notional (`$5.00 USDT` on Bybit/Aster perpetuals), lot-step rounding, leverage utilization, and fee minimums directly govern which trades can execute and how equity compounds.

---

## 6. Missing Capabilities Required for Phase 5.6.2 Strategy Discovery

To fulfill the Project Owner's mandate without altering frozen models or bypassing the 6 agents:
1. **Strategy Configuration Layer (`src/quantum/strategies/`):** Declarative, versioned, hash-verified strategy configurations (`StrategyConfiguration`) spanning 7 distinct quantitative research families, starting with Batch 001 (Strategies 001–100) and expanding iteratively to Batch 002 (Strategies 101–200) and Batch 003 (Strategies 201–300).
2. **Six-Agent Strategy Integration:** Connecting `Scout`, `Analyst`, `Sniper`, `Risk`, `Banker`, and `Orchestrator` to evaluate each `StrategyConfiguration` with full provenance and `$100 USD` capital accounting.
3. **Synchronized Dual-Directory Persistence (`audit/` and `data_backtest/`):** Deterministic SHA-256 `config_hash` and `experiment_id` cross-verification between raw backtest artifacts (`data_backtest/`) and human-readable research reports (`audit/`).
