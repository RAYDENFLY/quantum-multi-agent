# QUANTUM PHASE 5.5: BACKTEST ENGINE IMPLEMENTATION PLAN

**Document Version:** 1.0.0-STAGE-0-GOVERNANCE  
**Publication Timestamp:** 2026-11-02 17:15:00 UTC  
**Scope:** Engineering Remediation Workstreams A through F  
**Governance State:** Phase 5.5 `NOT_STARTED` | Phase 5.6 `NOT_AUTHORIZED` | Economic Backtesting `NOT_STARTED` | Prospective Holdout `STRICTLY_SEALED`  
**Decision Gate:** `DEC_01: BARRIER EXECUTION ARCHITECTURE` (`PENDING_HUMAN_DECISION`)  

**Authoritative Dossier References:**
- [QUANTUM_BACKTEST_ENGINE_AUDIT_AND_TECHNICAL_DESIGN_DRAFT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_BACKTEST_ENGINE_AUDIT_AND_TECHNICAL_DESIGN_DRAFT.md)
- [QUANTUM_PHASE_5_5_HUMAN_GOVERNANCE_DECISION_WORKSHOP.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_HUMAN_GOVERNANCE_DECISION_WORKSHOP.md)
- [PHASE_5_5_0_8_LONG_SHORT_ACCOUNTING_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_LONG_SHORT_ACCOUNTING_AUDIT.md)

---

## 1. PURPOSE AND ENGINEERING GOVERNANCE

Following the repository audit which resulted in `BLOCKED_BY_CRITICAL_DEFECTS`, this implementation plan defines the controlled engineering remediation to build the missing backtesting infrastructure for QUANTUM.

### Immutable Governance Bounds
- **Zero Economic Backtests:** No historical experiments are executed on real datasets during this engineering phase.
- **Sealed Holdout:** The prospective holdout dataset (2026-11-01+) remains strictly sealed.
- **Frozen Models and Preprocessors:** All 55 Phase 5.3 models and Phase 5.4 preprocessors remain strictly immutable.
- **Verification Domain:** Engineering validation is restricted to synthetic test fixtures, isolated unit tests, and adapter metadata checks.

---

## 2. WORKSTREAM BREAKDOWN AND SOURCE AUDIT VERIFICATION

```text
+-----------------------------+---------------------------------------+-------------------------------------------------------------+
| Workstream                  | Target Files                          | Revalidated Defect & Implementation Scope                   |
+-----------------------------+---------------------------------------+-------------------------------------------------------------+
| Workstream A: Clock Inject  | `src/quantum/agents/contracts.py`     | Hardcoded `time.time()*1000` in RiskAgent (Gate 1, Gate 4)  |
|                             | `src/quantum/agents/risk.py`          | and BankerAgent causes 100% historical signal veto.         |
|                             | `src/quantum/agents/banker.py`        | Add optional `eval_timestamp_ms` to RiskInput/BankerInput.  |
+-----------------------------+---------------------------------------+-------------------------------------------------------------+
| Workstream B: PnL Accounting| `src/quantum/backtesting/`            | No executable PnL accounting module exists in repository.   |
|                             | `src/quantum/backtesting/accounting.py| Build two-legged notional scaling, signed fees, slippage,   |
|                             |                                       | signed funding cash flows, realized vs unrealized PnL.      |
+-----------------------------+---------------------------------------+-------------------------------------------------------------+
| Workstream C: Backtest Engine| `src/quantum/backtesting/engine.py`   | No discrete-event simulation runner exists.                 |
|                             |                                       | Build causal candle-stepping runner with 12-bar horizon,    |
|                             |                                       | open[i+1] fill reference, conservative collision handling.  |
+-----------------------------+---------------------------------------+-------------------------------------------------------------+
| Workstream D: OOF Adapter   | `src/quantum/backtesting/adapters.py` | Analyst/Sniper use placeholder probabilities (0.67, 0.62).  |
|                             |                                       | Build causal reader for materialized OOF Parquet files.     |
+-----------------------------+---------------------------------------+-------------------------------------------------------------+
| Workstream E: Banker Integr.| `src/quantum/backtesting/engine.py`   | BankerAgent is disconnected from Orchestrator.              |
|                             |                                       | Wire simulated execution fills to Banker FSM lifecycle.     |
+-----------------------------+---------------------------------------+-------------------------------------------------------------+
| Workstream F: Risk Controls | `src/quantum/backtesting/engine.py`   | Ensure RiskAgent 12 gates are evaluated causally per trade. |
+-----------------------------+---------------------------------------+-------------------------------------------------------------+
```

---

## 3. ACCEPTANCE CRITERIA AND REGRESSION RISKS

### Acceptance Criteria
1. **Clock Injection:**
   - Historical timestamps pass Gate 1 (`SIGNAL_FRESHNESS`) when `eval_timestamp_ms == snapshot_timestamp_ms`.
   - Genuinely stale historical signals (> 15,000 ms before `eval_timestamp_ms`) are correctly vetoed.
   - Future timestamps (`eval_timestamp_ms < snapshot_timestamp_ms`) are vetoed with `VETO_FUTURE_TIMESTAMP`.
   - Existing live tests without `eval_timestamp_ms` continue to pass without regression.
2. **PnL Accounting:**
   - Long and Short profitable and losing trades produce exact arithmetic match with Phase 5.5.0.8 canonical test cases.
   - Signed funding cash flows adhere to convention: $CF > 0$ received, $CF < 0$ paid.
   - Partial exits compute realized PnL on closed quantity and mark-to-market unrealized PnL on remainder.
3. **Discrete-Event Engine:**
   - Causal sequence enforced: candle $i$ close signal -> candle $i+1$ open fill -> forward 12 candles barrier check.
   - Same-bar double touch resolved via conservative policy (SL hit first).
   - Time expiration enforced exactly at bar 12.
   - Replay is 100% deterministic.
4. **OOF Adapter:**
   - Zero future data leakage; clean timestamp alignment.
   - Folds 1 to 5 parsed correctly; Fold 5 tagged as unverified OOS.

### Regression Prevention
- All changes to existing files (`contracts.py`, `risk.py`, `banker.py`) must be strictly backward-compatible.
- `eval_timestamp_ms` defaults to `None`, in which case original `time.time() * 1000` logic executes.
- Zero changes to model files, feature engineering, or database repositories.

---

## 4. IMPLEMENTATION SEQUENCING

```text
Stage 0: Implementation Plan & Technical Specification (Complete)
Stage 1: Workstream A - Simulated Clock Injection (contracts, risk, banker)
Stage 2: Workstream B - Reference-Price PnL Accounting Engine (accounting.py)
Stage 3: Workstream D - Materialized OOF Probability Adapter (adapters.py)
Stage 4: Workstream C - Discrete-Event Backtest Runner (engine.py)
Stage 5: Workstream E - Banker FSM Integration & Workstream F Risk Controls
Stage 6: Multi-Level Testing & Technical Readiness Audit
```

---
*End of Backtest Engine Implementation Plan.*
