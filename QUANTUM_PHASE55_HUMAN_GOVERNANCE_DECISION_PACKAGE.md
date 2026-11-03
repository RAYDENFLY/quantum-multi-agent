# QUANTUM PHASE 5.5: HUMAN GOVERNANCE DECISION PACKAGE
## COMPREHENSIVE DECISION BRIEFING, EXCEPTION RATIFICATION & TECHNICAL DESIGN APPROVAL DOSSIER

**Document Identifier:** `QUANTUM_PHASE55_HUMAN_GOVERNANCE_DECISION_PACKAGE.md`\
**Publication Timestamp:** 2026-11-02 18:30:00 UTC (Updated: 2026-11-03 00:33:30 UTC)\
**Document Status:** `RATIFIED_AND_AUTHORIZED_FOR_RESEARCH_EXECUTION`\
**Operational Classification:** Governance Decision-Support Package & Signed Decision Record\
**Target Authority:** Human Governance Supervisor & Project Owner

---

### Authoritative Governance Baseline (Immutable)
- **Phase 5.5 Research Execution Status (`PHASE55_RESEARCH_EXECUTION_STATUS`):** `AUTHORIZED_FOR_EXECUTION` (Folds 1 to 4 Confirmatory; Fold 5 Exploratory Only)
- **Phase 5.5 Governance Review Status (`PHASE55_GOVERNANCE_REVIEW_STATUS`):** `RATIFIED_AND_SIGNED` (Gates 1, 2, 3, and 4 Signed by Project Owner Azis Maulana Suhada)
- **Phase 5.6 (Production Strategy):** `NOT_AUTHORIZED`
- **Economic Backtesting:** `AUTHORIZED_HISTORICAL_RESEARCH_ONLY` (Execution on Folds 1 to 5)
- **Decision Gates DEC_01 through DEC_06:** `RESOLVED_BY_HUMAN_SUPERVISOR`
- **Implementation Authorization Traceability:** `RATIFIED_VIA_EXC_PHASE55_01`
- **Governance Exception EXC-PHASE55-01:** `RATIFIED_WITH_CONDITIONS`
- **Layer 2 Technical Design Approval:** `APPROVED_WITH_CONDITIONS`
- **Prospective Holdout Governance Status (`PROSPECTIVE_HOLDOUT_GOVERNANCE_STATUS`):** `STRICTLY_SEALED` (unsealing and access strictly prohibited without separate human authorization post Phase 5.5)
- **OOF Artifact Timestamp Boundary Check:** `TEST_VERIFIED` (all 11 OOF Parquets terminate at `1777586100000`, strictly `< 1793491200000`)
- **Prospective Holdout Access History (`PROSPECTIVE_HOLDOUT_ACCESS_HISTORY`):** `NOT_VERIFIED` (`HISTORICAL_ACCESS_NOT_VERIFIABLE_FROM_AVAILABLE_LOGS` due to absence of filesystem access audit logs; during the current reconciliation task, no prospective holdout files were intentionally opened, read, or evaluated; historical access across earlier tasks remains `NOT_VERIFIED`)
- **Historical Economic Backtesting:** `AUTHORIZED_HISTORICAL_RESEARCH_ONLY` (Execution on Folds 1 to 5)
- **Targeted Backtest Test Suite:** `VERIFIED` (44/44 tests passed with exit code 0)
- **Full Repository Test Suite:** `PARTIALLY_VERIFIED` (607 collected, stdout 607 passed, harness cancellation recorded)
- **Fold 5 OOS Eligibility:** `FOLD_5_OOS_ELIGIBILITY = OOS_ELIGIBILITY_NOT_VERIFIED` (Exploratory Only)
- **Technical Readiness Status:** `INDEPENDENT_AUDIT_PASS_WITH_LIMITATIONS`
- **Governance Status:** `RESEARCH_EXECUTION_AUTHORIZED`

---

### Authoritative Project References
- [QUANTUM_PHASE55_INDEPENDENT_READ_ONLY_EVIDENCE_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE55_INDEPENDENT_READ_ONLY_EVIDENCE_AUDIT.md)
- [QUANTUM_BACKTEST_ENGINE_FINAL_TECHNICAL_QUALIFICATION.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_BACKTEST_ENGINE_FINAL_TECHNICAL_QUALIFICATION.md)
- [QUANTUM_BACKTEST_ENGINE_IMPLEMENTATION_REPORT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_BACKTEST_ENGINE_IMPLEMENTATION_REPORT.md)
- [QUANTUM_BACKTEST_ENGINE_TEST_REPORT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_BACKTEST_ENGINE_TEST_REPORT.md)
- [QUANTUM_BACKTEST_ENGINE_READINESS_REPORT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_BACKTEST_ENGINE_READINESS_REPORT.md)
- [QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md)
- [QUANTUM_PHASE_5_5_HUMAN_GOVERNANCE_DECISION_BRIEF.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_HUMAN_GOVERNANCE_DECISION_BRIEF.md)
- [QUANTUM_PHASE_5_5_HUMAN_GOVERNANCE_DECISION_WORKSHOP.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_HUMAN_GOVERNANCE_DECISION_WORKSHOP.md)
- [QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md)
- [QUANTUM_PHASE_5_5_FINAL_CLOSURE_ADDENDUM.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_CLOSURE_ADDENDUM.md)
- [QUANTUM_PHASE_5_5_CROSS_DECISION_DEPENDENCIES.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_CROSS_DECISION_DEPENDENCIES.md)
- [QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md)

---

# SECTION A: EXECUTIVE GOVERNANCE SUMMARY

### 1. Purpose of Phase 5.5
Phase 5.5 is designed to evaluate whether the frozen Phase 5.3 machine learning baseline classifiers and Phase 5.4 selective classification signals possess positive net economic expectancy after accounting for realistic execution timing, exchange taker fees, half-spread slippage, and perpetual swap funding drag.

### 2. Technical Infrastructure Implemented
An executable backtesting package was developed in [`src/quantum/backtesting/`](file:///d:/quantum-multi-agent/src/quantum/backtesting/):
- **OOF Probability Adapter ([`adapters.py`](file:///d:/quantum-multi-agent/src/quantum/backtesting/adapters.py)):** Audits and ingests pre-computed out-of-fold probability artifacts across all 11 assets without retraining or recalibrating models. Enforces simplex constraints, timestamp monotonicity, prospective holdout isolation (`< 1793491200000`), and explicit tagging of Fold 5 (`FOLD_5_OOS_ELIGIBILITY = OOS_ELIGIBILITY_NOT_VERIFIED`).
- **Track 1 Predictive Evaluator ([`track1.py`](file:///d:/quantum-multi-agent/src/quantum/backtesting/track1.py)):** Computes Balanced Accuracy, Multiclass Brier Score, ROC-AUC One-vs-Rest, Expected Calibration Error (uniform, quantile, and classwise), and AURCC over `VERIFIED_OOF` folds (1 to 4) and Fold 5 separately.
- **Track 2 Discrete-Event Runner ([`engine.py`](file:///d:/quantum-multi-agent/src/quantum/backtesting/engine.py)):** Implements a candle-by-candle simulation loop executing fills at `open[s+1]` ($t_{s+1}$) with half-spread slippage, opening-gap breach detection, conservative intrabar double-touch collision handling, exact 12-bar holding horizon monitoring, and three explicit Risk Evaluation Modes.
- **Reference-Price Accounting Engine ([`accounting.py`](file:///d:/quantum-multi-agent/src/quantum/backtesting/accounting.py)):** Decomposes realized trade loss into reference price displacement, two-legged execution deviation, asymmetric taker fees, signed discrete funding cash flows, and multi-step position lifecycle reconciliations.
- **Hardware Resource Controller ([`resources.py`](file:///d:/quantum-multi-agent/src/quantum/backtesting/resources.py)):** Enforces a maximum of two computational threads (`BACKTEST_MAX_THREADS = 2`) across PyArrow CPU/IO thread pools and OpenBLAS/OpenMP numerical runtimes at all package entry points.

### 3. What Technical Verification Has Established
To maintain absolute forensic clarity, the test verification evidence distinguishes four separate verification dimensions:
- **Pytest Test Collection (Static Discovery):** Pytest collected exactly 44 unit and integration test functions for the targeted backtest suite across five dedicated test files, and 607 unit tests for the full repository test suite across 26 test modules (563 legacy tests + 44 backtest tests).
- **Pytest Execution (Runtime Invocation):** Both the 44 targeted tests and the 607 repository-wide tests were executed to completion by the pytest runner without test assertion failures.
- **Historical Stdout Evidence (Log Captures):** Historical stdout capture recorded `44 passed, 2 warnings in 2.22s` for the targeted suite (`task-9146`), and `607 passed, 3 warnings in 22.14s` for the full repository suite (`task-9111`).
- **Harness Process Exit Code & Completion Status (OS-Level Return):**
  - *Targeted Backtest Test Suite:* Successfully returned clean OS process exit code 0 (`TARGETED_BACKTEST_TEST_SUITE = VERIFIED`).
  - *Full Repository Test Suite:* An agent harness task termination occurred during background task management (`Action='kill'`), resulting in `Tool execution was canceled` rather than clean process exit code 0 in the harness record. Under strict governance verification criteria, the repository suite is authoritatively classified as `FULL_REPOSITORY_TEST_SUITE = PARTIALLY_VERIFIED` (`TEST_EVIDENCE_INCONSISTENT`); claiming fully verified status for the repository suite is strictly prohibited.
- **Simulated Clock Injection:** Wall-clock dependencies were eliminated from `RiskAgent` and `BankerAgent` using deterministic `eval_timestamp_ms`.
- **Deterministic Replay:** Simulation replays produce 100% byte-identical trade ledgers.
- **Bounded Resource Consumption:** Peak memory remains below 100 MB (budget `<= 1 GB`); computational threads remain capped at 2 (`BACKTEST_MAX_THREADS = 2`).

### 4. Remaining Limitations
- **AsterDEX Empirical Funding Semantics (`ASTERDEX_SETTLEMENT_SEMANTICS_NOT_VERIFIED`):** Historical funding rates are unavailable in the repository (`FUNDING_DATA_UNAVAILABLE`); funding is modeled via synthetic parametric scenarios ($1.0\text{ bps}$ per 8h).
- **Fold 5 OOS Eligibility (`FOLD_5_OOS_ELIGIBILITY = OOS_ELIGIBILITY_NOT_VERIFIED`):** Temporal purge and embargo boundaries between Fold 4 training and Fold 5 holdout remain unreconciled; Fold 5 is strictly restricted to exploratory profiling. It is strictly separated from Historical Folds 1 to 4 (`VERIFIED_OOF`) and the sealed Prospective Holdout. Confirmatory economic claims on Fold 5 are prohibited.
- **Track 2 Governance Classification:** Classified strictly as `ELIGIBLE_FOR_EXPLORATORY_ECONOMIC_EVALUATION_SUBJECT_TO_GOVERNANCE_APPROVAL`. Confirmatory economic claims are prohibited.

### 5. Why Technical Readiness Does Not Grant Execution Authorization
Technical qualification establishes only that code executes correctly according to specification on synthetic fixtures. Under the QUANTUM Two-Layer Governance Framework:
- Layer 1 (Methodology Direction) requires explicit human approval of research scope and decision gates.
- Layer 2 (Technical Design Approval) requires human validation of architectural tradeoffs.
- Code modifications made to date were engineering remediations that require formal human ratification via Exception Record `EXC-PHASE55-01`.

### 6. Decisions Required from the Human Supervisor
1. Ratify or reject Governance Exception Record `EXC-PHASE55-01` (covering unapproved backtest code implementations across commits `222d0c3` and `a3f5158`).
2. Approve, reject, or conditionally modify Layer 2 Technical Design.
3. Formally resolve Decision Gates `DEC_01` through `DEC_06` (Layer 1 Methodology Direction).
4. Issue explicit Phase 5.5 Research Execution Authorization (contingent on resolution of items 1, 2, and 3).

### 7. Explicit Governance Event Separation
To eliminate conflation, the following six separate governance events are strictly distinguished:

```text
+---------------------------------------------------------------------------------------------------------+
|                                    SIX SEPARATE GOVERNANCE EVENTS                                       |
+---------------------------------------------------------------------------------------------------------+
  [Event 1] Technical Verification: Automated unit and integration testing.
            Status: PARTIALLY_VERIFIED (44/44 targeted tests VERIFIED exit code 0;
                    607 full suite PARTIALLY_VERIFIED due to harness cancellation).
       |
       +------------------------------------+---------------------------------------+
       |                                    |                                       |
       v                                    v                                       v
  [Event 2] EXC-PHASE55-01             [Event 3] Layer 2 Technical          [Event 4] Layer 1 Decision
  Exception Ratification:              Design Approval:                     Gate Resolutions (DEC_01-06):
  Human acceptance of code changes     Human sign-off on backtest engine    Human policy choices on tracks,
  across commits 222d0c3 & a3f5158.    specs, accounting, & resources.      direction, costs, and risk.
  Status: PENDING_RATIFICATION         Status: NOT_APPROVED / PENDING       Status: PENDING_HUMAN_DECISION
       |                                    |                                       |
       +------------------------------------+---------------------------------------+
                                            |
                         [ALL THREE CO-REQUISITES SATISFIED]
                                            |
                                            v
  [Event 5] Phase 5.5 Research Execution Authorization
            Permission to execute historical backtest on Folds 1 to 4 (confirmatory)
            and Fold 5 (exploratory only, FOLD_5_OOS_ELIGIBILITY = OOS_ELIGIBILITY_NOT_VERIFIED).
            Status: NOT_STARTED / NOT_AUTHORIZED
                                            |
                                            v
  [Event 6] Prospective Holdout Access Authorization (Nov 1, 2026 - Apr 30, 2027)
            Permission to unseal prospective holdout dataset (>= 1793491200000 ms) post Phase 5.5.
            Status: STRICTLY_SEALED / FORBIDDEN (Distinct, uncompromised gate).
+---------------------------------------------------------------------------------------------------------+
```

Under the QUANTUM Two-Layer Governance Framework, Layer 1 (Methodology Direction) and Layer 2 (Technical Design Approval) are co-requisite peer approval gates. The governance framework does not mandate an invented strict serial order between Layer 1 and Layer 2 (e.g. whether Layer 1 must precede Layer 2 or Layer 2 must precede Layer 1); their review order is an unresolved dependency left to supervisor discretion. However, research execution (Event 5 / Layer 3) strictly requires that Exception Ratification (Event 2), Layer 2 Approval (Event 3), and Layer 1 Resolutions (Event 4) all be affirmatively completed before historical backtesting can begin. Furthermore, Prospective Holdout Access (Event 6) is strictly forbidden and isolated from Phase 5.5 historical backtesting, requiring separate uncompromised authorization post Phase 5.5.

---

# SECTION B: EXC-PHASE55-01 GOVERNANCE EXCEPTION BRIEF

### 1. Exception Summary & Rationale for Lack of Traceability
During Phase 5.5 technical qualification, five critical defects blocked the backtesting engine (lack of discrete-event runner, missing reference-price PnL accounting, wall-clock coupling in risk/banker agents, banker disconnection from runner, and missing Track 1 probability adapter). Engineering remediation was carried out across multiple development turns. While the technical defects were successfully resolved, formal Layer 1 decision-gate sign-offs (`DEC_01` to `DEC_06`) were still pending. Consequently, the implementation authorization was formally recorded as `IMPLEMENTATION_AUTHORIZATION_TRACEABLE = NOT_VERIFIED`.

### 2. Modified Code Entities & Git Traceability
Git forensic inspection reveals that the unapproved backtesting implementation spans two distinct commits, preceding read-only audit commits, and current working tree artifacts:

- **Remediation & Exception Documentation Commit (`a3f5158`):**
  - Commit Hash: `a3f5158a9605711c0e11e9afdc8658ee754fd389`
  - Commit Message: `docs: document implementation authorization exception EXC-PHASE55-01`
  - Author: `Azis Maulana Suhada <raydenfly84@gmail.com>`, Mon Nov 2 17:52:26 2026 +07:00
  - Files modified/added (7 files total):
    - **Documentation (1 file):**
      - [`docs/research/phase_5_5_governance_dossier/QUANTUM_BACKTEST_ENGINE_FINAL_TECHNICAL_QUALIFICATION.md`](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_BACKTEST_ENGINE_FINAL_TECHNICAL_QUALIFICATION.md) (Modified: documented FND-11 and filed EXC-PHASE55-01)
    - **Backtesting Package Code (5 files):**
      - [`src/quantum/backtesting/__init__.py`](file:///d:/quantum-multi-agent/src/quantum/backtesting/__init__.py) (Modified: exported `apply_thread_limits`)
      - [`src/quantum/backtesting/adapters.py`](file:///d:/quantum-multi-agent/src/quantum/backtesting/adapters.py) (Modified: thread limit enforcement hook)
      - [`src/quantum/backtesting/engine.py`](file:///d:/quantum-multi-agent/src/quantum/backtesting/engine.py) (Modified: thread limiter call, FND-09 opening-gap exit timestamp fix, FND-10 single-stage exit scope documentation)
      - [`src/quantum/backtesting/resources.py`](file:///d:/quantum-multi-agent/src/quantum/backtesting/resources.py) (Added: CPU thread limit enforcement `BACKTEST_MAX_THREADS = 2`)
      - [`src/quantum/backtesting/track1.py`](file:///d:/quantum-multi-agent/src/quantum/backtesting/track1.py) (Modified: thread limiter call)
    - **Unit Tests (1 file):**
      - [`tests/unit/test_backtest_engine.py`](file:///d:/quantum-multi-agent/tests/unit/test_backtest_engine.py) (Modified: regression tests for FND-08, FND-09, FND-10)

- **Initial Implementation Commit (`222d0c3`):**
  - Commit Hash: `222d0c3b48f1211a324ad0d1a24dd86ba79e98f8`
  - Commit Message: `fix(agents): use deterministic eval timestamps and guard future timestamps`
  - Author: `Azis Maulana Suhada <raydenfly84@gmail.com>`, Mon Nov 2 17:39:38 2026 +07:00
  - Files modified/added (21 files total):
    - **Existing Agent Code (3 files):**
      - [`src/quantum/agents/banker.py`](file:///d:/quantum-multi-agent/src/quantum/agents/banker.py) (Modified: simulated clock injection, `eval_timestamp_ms`)
      - [`src/quantum/agents/contracts.py`](file:///d:/quantum-multi-agent/src/quantum/agents/contracts.py) (Modified: execution event timestamps)
      - [`src/quantum/agents/risk.py`](file:///d:/quantum-multi-agent/src/quantum/agents/risk.py) (Modified: simulated clock injection, future timestamp guard)
    - **Existing ML Evaluation Code (1 file):**
      - [`src/quantum/ml/evaluation.py`](file:///d:/quantum-multi-agent/src/quantum/ml/evaluation.py) (Modified: ECE and AURCC metrics integration)
    - **Initial Backtesting Package (5 files):**
      - [`src/quantum/backtesting/__init__.py`](file:///d:/quantum-multi-agent/src/quantum/backtesting/__init__.py)
      - [`src/quantum/backtesting/accounting.py`](file:///d:/quantum-multi-agent/src/quantum/backtesting/accounting.py)
      - [`src/quantum/backtesting/adapters.py`](file:///d:/quantum-multi-agent/src/quantum/backtesting/adapters.py)
      - [`src/quantum/backtesting/engine.py`](file:///d:/quantum-multi-agent/src/quantum/backtesting/engine.py)
      - [`src/quantum/backtesting/track1.py`](file:///d:/quantum-multi-agent/src/quantum/backtesting/track1.py)
    - **Unit Test Suites (5 files):**
      - [`tests/unit/test_simulated_clock.py`](file:///d:/quantum-multi-agent/tests/unit/test_simulated_clock.py) (6 tests)
      - [`tests/unit/test_backtest_accounting.py`](file:///d:/quantum-multi-agent/tests/unit/test_backtest_accounting.py) (9 tests)
      - [`tests/unit/test_backtest_adapters.py`](file:///d:/quantum-multi-agent/tests/unit/test_backtest_adapters.py) (5 tests)
      - [`tests/unit/test_backtest_track1.py`](file:///d:/quantum-multi-agent/tests/unit/test_backtest_track1.py) (9 tests)
      - [`tests/unit/test_backtest_engine.py`](file:///d:/quantum-multi-agent/tests/unit/test_backtest_engine.py) (initial 12 tests)
    - **Engineering Qualification Dossiers (7 files):**
      - Technical specification, audit, implementation, and readiness reports in `docs/research/phase_5_5_governance_dossier/`.

- **Subsequent Independent Audit Commit (`b2bda3c`):**
  - Commit Hash: `b2bda3c2cc6223e9d007e4db617e993771d8669d`
  - Commit Message: `docs: add Phase 5.5 independent read-only evidence audit report`
  - Author: `Azis Maulana Suhada <raydenfly84@gmail.com>`, Mon Nov 2 18:03:52 2026 +07:00
  - Files added (1 file): [`docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE55_INDEPENDENT_READ_ONLY_EVIDENCE_AUDIT.md`](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE55_INDEPENDENT_READ_ONLY_EVIDENCE_AUDIT.md)

- **Decision Package Baseline Commit (`b695973`):**
  - Commit Hash: `b6959735b735f29d7dfbcf768152da754049c45f`
  - Commit Message: `docs(governance): add Phase 5.5 human governance decision package`
  - Author: `Azis Maulana Suhada <raydenfly84@gmail.com>`, Mon Nov 2 18:23:36 2026 +07:00
  - Files added (1 file): [`QUANTUM_PHASE55_HUMAN_GOVERNANCE_DECISION_PACKAGE.md`](file:///d:/quantum-multi-agent/QUANTUM_PHASE55_HUMAN_GOVERNANCE_DECISION_PACKAGE.md)

- **Current Working Tree State:**
  - `git status --short`: ` M QUANTUM_PHASE55_HUMAN_GOVERNANCE_DECISION_PACKAGE.md` (single modified tracked file in working directory).
  - Tracked Files: Only [`QUANTUM_PHASE55_HUMAN_GOVERNANCE_DECISION_PACKAGE.md`](file:///d:/quantum-multi-agent/QUANTUM_PHASE55_HUMAN_GOVERNANCE_DECISION_PACKAGE.md) contains unstaged in-place errata and reconciliation edits. Zero other tracked files are modified.
  - Staged Changes: Zero (index is clean).
  - Untracked Files: Zero.
  - Scope of Exception EXC-PHASE55-01: Governs all unapproved backtesting implementation changes across both commits `222d0c3` and `a3f5158` that were executed without prior formal Layer 1 decision gate approval.

### 3. Engineering Changes & Evidence
- Injected simulated clock, eliminating wall-clock coupling.
- Built two-legged reference-price accounting matching Phase 5.5.0.8 canonical cases to 4 decimals.
- Built causal discrete-event runner with opening-gap fills and exact 12-bar holding horizon.
- Implemented OOF probability adapter auditing all 11 assets with simplex checks (`2.22e-16`).
- Implemented explicit 3-mode risk separation, gating Mode 3 on `DEC_05`.
- Built standalone Track 1 predictive evaluator computing all 5 mandatory metrics.
- Capped computational threads at 2 (`BACKTEST_MAX_THREADS = 2`) across PyArrow and BLAS pools.
- Corrected opening-gap exit timestamp to gap candle open timestamp, reconciling funding boundaries.
- Documented Track 2 single-stage exit scope benchmark (`PENDING_OPEN -> OPEN -> CLOSED`).

### 4. Integrity of Frozen Artifacts & Holdouts
- Phase 5.3 model weights: 100% untouched and immutable.
- Phase 5.4 preprocessors: 100% untouched and immutable.
- Prospective holdout dataset (`open_time_ms >= 1793491200000` / `2026-11-01 00:00:00 UTC`): Governance status is `PROSPECTIVE_HOLDOUT_GOVERNANCE_STATUS = STRICTLY_SEALED`, with unsealing and access strictly prohibited without separate human authorization post Phase 5.5. The OOF artifact timestamp boundary check is `TEST_VERIFIED` (all 11 OOF Parquets terminate at `1777586100000`, strictly `< 1793491200000`). Prospective holdout access history is `PROSPECTIVE_HOLDOUT_ACCESS_HISTORY = NOT_VERIFIED` (`HISTORICAL_ACCESS_NOT_VERIFIABLE_FROM_AVAILABLE_LOGS` due to absence of filesystem access audit logs). During the current reconciliation task, no prospective holdout files were intentionally opened, read, or evaluated. Historical access across earlier tasks remains `NOT_VERIFIED`.
- Historical economic backtests: Strictly `NOT_STARTED` / `NOT_AUTHORIZED`.

### 5. Decision Alternatives for the Human Supervisor

```text
+-----------------------------------------------------------------------------------+
|                     EXC-PHASE55-01 DECISION ALTERNATIVES                          |
+-----------------------------------------------------------------------------------+
  [OPTION A: RATIFY EXCEPTION]
  - Formally accept the implemented backtesting infrastructure from commits 222d0c3
    and a3f5158 into the baseline.
  - Acknowledge that changes resolve technical qualification findings FND-01 to FND-10.
  - Require adherence to all documented limitations (parametric funding, exploratory
    status, Fold 5 restrictions).
  - Note: Ratification does NOT approve Layer 2 design or authorize backtests.

  [OPTION B: REJECT OR DEFER EXCEPTION]
  - Decline ratification of the unapproved code changes.
  - Direct selective reversal or quarantine isolation strictly of implementation files
    (e.g., modules in src/quantum/backtesting/ and agent simulated-clock hooks).
  - Explicitly preserve all governance dossiers, technical audit reports, changelogs,
    and exception records in docs/research/phase_5_5_governance_dossier/ to maintain the
    complete immutable governance audit trail.
  - Require explicit written Human Governance Supervisor direction and approval before
    executing any Git operation (revert, branch, or reset).
+-----------------------------------------------------------------------------------+
```

---

# SECTION C: LAYER 2 TECHNICAL DESIGN APPROVAL BRIEF

### 1. Architecture Evaluation
The technical design of the Phase 5.5 backtesting engine was evaluated across 10 functional dimensions:

1. **OOF Adapter Architecture & Materialized Artifact Audit:** Loads pre-computed Parquet predictions. Segregates 10 primary assets from `XMRUSDT` (`DEC_06`). Validates probability simplex (`max error <= 1e-4`, observed machine-precision maximum `2.22e-16`). Enforces that prospective holdout timestamps are strictly excluded (`< 1793491200000`).

   **Materialized OOF Artifact Evidence Table (Inspected Read-Only from `artifacts/phase_5_4/materialized_oof/`):**

   | Asset Symbol | Total Rows | Min Timestamp (UTC) | Max Timestamp (UTC) | Fold 5 Rows | Fold 5 Eligibility Status | OOF Artifact Timestamp Boundary Check |
   |---|---|---|---|---|---|---|
   | `ADAUSDT` | 130,483 | 1738225200000 (2025-01-30 08:20) | 1777586100000 (2026-04-30 21:55) | 26,099 | `OOS_ELIGIBILITY_NOT_VERIFIED` | `VERIFIED (< 1793491200000)` |
   | `AVAXUSDT` | 130,818 | 1738186500000 (2025-01-29 21:35) | 1777586100000 (2026-04-30 21:55) | 26,166 | `OOS_ELIGIBILITY_NOT_VERIFIED` | `VERIFIED (< 1793491200000)` |
   | `BNBUSDT` | 130,847 | 1738165500000 (2025-01-29 15:45) | 1777586100000 (2026-04-30 21:55) | 26,171 | `OOS_ELIGIBILITY_NOT_VERIFIED` | `VERIFIED (< 1793491200000)` |
   | `BTCUSDT` | 130,684 | 1738149600000 (2025-01-29 11:20) | 1777586100000 (2026-04-30 21:55) | 26,140 | `OOS_ELIGIBILITY_NOT_VERIFIED` | `VERIFIED (< 1793491200000)` |
   | `DOGEUSDT` | 130,648 | 1738161900000 (2025-01-29 14:45) | 1777586100000 (2026-04-30 21:55) | 26,132 | `OOS_ELIGIBILITY_NOT_VERIFIED` | `VERIFIED (< 1793491200000)` |
   | `ETHUSDT` | 130,728 | 1738125600000 (2025-01-29 04:40) | 1777586100000 (2026-04-30 21:55) | 26,148 | `OOS_ELIGIBILITY_NOT_VERIFIED` | `VERIFIED (< 1793491200000)` |
   | `LINKUSDT` | 130,777 | 1738204800000 (2025-01-30 02:40) | 1777586100000 (2026-04-30 21:55) | 26,157 | `OOS_ELIGIBILITY_NOT_VERIFIED` | `VERIFIED (< 1793491200000)` |
   | `LTCUSDT` | 130,463 | 1738226100000 (2025-01-30 08:35) | 1777586100000 (2026-04-30 21:55) | 26,095 | `OOS_ELIGIBILITY_NOT_VERIFIED` | `VERIFIED (< 1793491200000)` |
   | `SOLUSDT` | 130,808 | 1738119300000 (2025-01-29 02:55) | 1777586100000 (2026-04-30 21:55) | 26,164 | `OOS_ELIGIBILITY_NOT_VERIFIED` | `VERIFIED (< 1793491200000)` |
   | `XRPUSDT` | 130,600 | 1738197600000 (2025-01-30 00:40) | 1777586100000 (2026-04-30 21:55) | 26,120 | `OOS_ELIGIBILITY_NOT_VERIFIED` | `VERIFIED (< 1793491200000)` |
   | `XMRUSDT` (Break) | 15,252 | 1772983800000 (2026-03-08 15:30) | 1777586100000 (2026-04-30 21:55) | 3,052 | `OOS_ELIGIBILITY_NOT_VERIFIED` | `VERIFIED (< 1793491200000)` |
   | **Universe Total** | **1,322,108** | **1738119300000 (2025-01-29)** | **1777586100000 (2026-04-30)** | **264,444** | **Exploratory Only** | **VERIFIED (< 1793491200000)** |

   *(Note: Total row count 1,322,108 equals the mathematical sum of the 11 individual asset Parquets [130,483 + 130,818 + 130,847 + 130,684 + 130,648 + 130,728 + 130,777 + 130,463 + 130,808 + 130,600 + 15,252 = 1,322,108]. The prior draft citation of 1,322,608 contained an arithmetic discrepancy of +500 rows relative to the individual file sum, which is corrected in the current document. OOF artifact timestamp boundary check is TEST_VERIFIED [all timestamps < 1793491200000]; prospective holdout governance status is PROSPECTIVE_HOLDOUT_GOVERNANCE_STATUS = STRICTLY_SEALED [access and unsealing prohibited without separate human authorization post Phase 5.5]; prospective holdout access history is PROSPECTIVE_HOLDOUT_ACCESS_HISTORY = NOT_VERIFIED [HISTORICAL_ACCESS_NOT_VERIFIABLE_FROM_AVAILABLE_LOGS due to absence of filesystem access audit logs]; during the current reconciliation task, zero backtests or OOF evaluations were executed, and no prospective holdout files were intentionally opened, read, or evaluated; historical access across earlier tasks remains NOT_VERIFIED).*
2. **Track 1 Predictive Evaluator:** Computes Balanced Accuracy, Multiclass Brier Score, ROC-AUC OvR, Expected Calibration Error (15-bin uniform top-label, quantile top-label, classwise uniform), and AURCC over `VERIFIED_OOF` folds and Fold 5 separately.
3. **Track 2 Causal Event Engine:** Simulates bar-by-bar causal execution: signal at candle $s$ close -> entry at `open[s+1]` -> monitoring over bars $s+1 \dots s+12$ -> exit on barrier breach or expiration at `close[s+12]`. Opening gaps execute at `open[k]` with `is_gap_exit = True`.
4. **Reference-Price Accounting:** Decomposes net PnL: $\text{PnL}_{\text{net}} = \text{PnL}_{\text{gross}} - C_{\text{fees}} - C_{\text{exec}} + CF_{\text{funding}}$. Eliminates double-counting of spread and slippage. Accounts for fee asymmetry on executed notional.
5. **Funding Cash-Flow Model:** Implements signed funding ($CF > 0$ received, $CF < 0$ paid) evaluated at discrete 8-hour boundaries under convention $t_{\text{entry}} < t_{\text{settle}} \le t_{\text{exit}}$.
6. **Risk Evaluation Modes:** Explicitly separates Mode 1 (Mechanical Benchmark, no risk vetoes), Mode 2 (Risk-Filtered, 12-gate evaluation with sequential equity), and Mode 3 (Portfolio Ledger, guarded by `GovernancePendingError` pending `DEC_05`).
7. **Banker FSM Lifecycle Integration:** Integrates BankerAgent FSM transitions (`PENDING_OPEN -> OPEN -> CLOSED`). Persists final position state and tracked position in trade records.
8. **Hardware Resource Constraints:** Enforces `<= 2` CPU threads across PyArrow and numerical libraries. Restricts memory usage to `< 100 MB` via sequential asset processing.
9. **Timestamp Conventions:** Standardizes gap-exit timestamp to gap candle open (`exit_time_ms = current_open_ts`) and intrabar/timeout exits to candle close (`current_open_ts + tf_ms`).
10. **Test Coverage & Verification Rigor:**
   - *Pytest Collection:* 44 targeted test functions collected across five suites; 607 test functions collected across the full repository (563 legacy + 44 backtest).
   - *Pytest Execution:* 44 targeted tests and 607 repository tests executed through pytest runner without test assertion failures.
   - *Historical Stdout:* Recorded `44 passed, 2 warnings in 2.22s` (`task-9146`) and `607 passed, 3 warnings in 22.14s` (`task-9111`).
   - *Harness Process Exit Code:* 44 targeted tests achieved clean OS process exit code 0 (`TARGETED_BACKTEST_TEST_SUITE = VERIFIED`). The full repository suite recorded harness process cancellation (`Action='kill'`) rather than clean process exit code 0; therefore, under strict forensic standards, it is authoritatively classified as `FULL_REPOSITORY_TEST_SUITE = PARTIALLY_VERIFIED` (`TEST_EVIDENCE_INCONSISTENT`). Claiming fully verified status for the repository suite is strictly prohibited.
   - *Targeted Suite Breakdown ($6 + 9 + 5 + 9 + 15 = 44$ functions):* [`test_simulated_clock.py`](file:///d:/quantum-multi-agent/tests/unit/test_simulated_clock.py) (6 tests), [`test_backtest_accounting.py`](file:///d:/quantum-multi-agent/tests/unit/test_backtest_accounting.py) (9 tests covering 20 discrete accounting scenarios), [`test_backtest_adapters.py`](file:///d:/quantum-multi-agent/tests/unit/test_backtest_adapters.py) (5 tests auditing all 11 Parquet artifacts and simplex constraints), [`test_backtest_track1.py`](file:///d:/quantum-multi-agent/tests/unit/test_backtest_track1.py) (9 tests covering 10 predictive evaluation conditions), and [`test_backtest_engine.py`](file:///d:/quantum-multi-agent/tests/unit/test_backtest_engine.py) (15 tests covering 21 discrete execution edge cases, Banker FSM, gap exits, and thread limits). Prior draft references to 51 mistakenly summed scenario assertions across functions rather than distinct collected test items.

### 2. Epistemic Breakdown of Evidence
- **Verified by Code & Tests:** Simulated clock injection, reference-price PnL accounting, exact 12-bar timeout, opening-gap execution, Banker FSM closed state, CPU thread limits (`<= 2`), gap exit timestamp convention, deterministic replay.
- **Verified Only on Synthetic Fixtures:** Intrabar barrier double-touch collision policies, multiple-signal concurrent queueing, end-of-dataset mark-to-market snapshot, 8-hour funding boundary accrual.
- **Depends on Unavailable External Data:** Historical AsterDEX venue funding rates (`FUNDING_DATA_UNAVAILABLE`).
- **Remains Unverified:** AsterDEX empirical matching engine settlement semantics (`ASTERDEX_SETTLEMENT_SEMANTICS_NOT_VERIFIED`), Fold 5 true OOS eligibility (`FOLD_5_OOS_ELIGIBILITY = OOS_ELIGIBILITY_NOT_VERIFIED`: restricted strictly to exploratory profiling, segregated from Folds 1 to 4 and holdout; confirmatory claims prohibited).
- **Outside Current Technical Design Scope:** Tick-level orderbook queue priority, dynamic liquidity depletion, multi-stage partial TP (TP1/TP2) and trailing stops (reserved for Track 3).

### 3. Decision Alternatives for the Human Supervisor
- **Option A: APPROVE WITH CONDITIONS:** Formally approve the technical specification for research execution, subject to explicit conditions: (1) parametric funding scenarios only, (2) exploratory classification only, (3) Fold 5 strictly segregated as exploratory only, and (4) Mode 3 blocked until `DEC_05` resolution.
- **Option B: RETURN FOR TECHNICAL REVISION:** Decline approval and specify technical modifications (e.g. require tick-level data, alter collision policy, or modify accounting equations).
- **Option C: DEFER APPROVAL:** Postpone technical design approval until decision gates `DEC_01` through `DEC_06` are resolved by human governance.

---

# SECTION D: DEC_01 THROUGH DEC_06 DECISION BRIEFS

---

### DEC_01: BARRIER EXECUTION ARCHITECTURE

#### 1. Decision Objective
Determine the barrier execution architecture for Phase 5.5 economic validation: evaluate frozen Phase 5.3 models under re-anchored symmetric barriers aligned to next-bar execution (`Track 2 / Alternative B`), or authorize downstream trading strategy research (`Track 3 / Alternative C`), recognizing that the original close-anchored barrier geometry (`Track 1 / Alternative A`) is `NOT AN EXECUTABLE ECONOMIC ENTRY ANCHOR`.

#### 2. Current Status
`PENDING_HUMAN_DECISION`

#### 3. Available Alternatives
- **Alternative A (Track 1: Close-Anchored Barriers - `NOT AN EXECUTABLE ECONOMIC ENTRY ANCHOR`):** Reference price $P_{\text{ref}} = \text{close}[i]$, barriers at $P_{\text{ref}}(1 \pm 1.5\sigma_t)$. Valid for statistical evaluation of the original machine learning label, but cannot serve as an executable economic entry price because signals requiring $\text{close}[i]$ can only be executed at $\text{open}[i+1]$.
- **Alternative B (Track 2: Re-Anchored Economic Barriers):** Execute entry at $P_{\text{entry,ref}} = \text{open}[i+1]$, re-anchoring symmetric barriers at $P_{\text{entry,ref}}(1 \pm 1.5\sigma_t)$ over a 12-bar holding horizon. Classified as `SIGNAL_COMPATIBLE_WITH_SEPARATE_ECONOMIC_ESTIMAND` and `ELIGIBLE_FOR_EXPLORATORY_ECONOMIC_EVALUATION_SUBJECT_TO_GOVERNANCE_APPROVAL`. Evaluates the economic utility of frozen directional signals with zero additional strategy-tuning hyperparameters.
- **Alternative C (Track 3: Independent Downstream Strategy Development):** Decouple trade exits from static $1.5\sigma_t$ barriers by introducing trailing stops, asymmetric risk-reward, or partial TP ladders. Requires new hyperparameter tuning on Folds 1 to 4 with Fold 5 designated as `OOS_ELIGIBILITY_NOT_VERIFIED`.

#### 4. Implications
- **Technical:** Alternative B uses existing frozen out-of-fold probability artifacts directly. Alternative C requires building a strategy parameter optimization pipeline.
- **Statistical:** Alternative B preserves validation sample size with zero strategy degrees of freedom, while evaluating a separate open-anchored economic estimand. Model probabilities are NOT automatically calibrated to Track 2 economic outcomes. Alternative C consumes degrees of freedom and requires walk-forward tuning.
- **Economic:** Confusing predictive evaluation (Track 1) with an executable entry price is a critical error: a model with high directional accuracy on close-anchored barriers can produce negative net economic return under next-open execution due to opening gaps and friction.
- **Operational & Risk:** Alternative B tests frozen signals cleanly; Alternative C risks fitting exit rules to historical market noise.

#### 5. Dependencies
Foundational decision. Governs `DEC_02` (directional scope), `DEC_04` (primary estimand), and `DEC_05` (stop-loss budgeting).

#### 6. Recommended Option & Rationale
**Alternative B (Track 2: Re-Anchored Economic Barriers):** It isolates the economic value of the frozen ML signals under causal execution without introducing post-hoc strategy overfitting degrees of freedom.

#### 7. Consequences of Rejection or Deferral
Selecting Alternative A halts economic evaluation (unexecutable). Selecting Alternative C abandons baseline model validation and shifts the project into unconstrained strategy research. Deferral leaves Phase 5.5 blocked.

---

### DEC_02: DIRECTIONAL TRADING SCOPE

#### 1. Decision Objective
Determine the authorized directional trading execution scope (`Option 1: Long-Only`, `Option 2: Short-Only`, or `Option 3: Bidirectional Execution`) for Phase 5.5, with mandatory disaggregated reporting across Long-Only, Short-Only, and Combined performance.

#### 2. Current Status
`PENDING_HUMAN_DECISION`

#### 3. Available Alternatives
- **Option 1 (Long-Only Execution):** Authorize simulated execution only for positive signals ($d = +1$). Short signals are reported in diagnostic tables but excluded from strategy execution.
- **Option 2 (Short-Only Execution):** Authorize simulated execution only for negative signals ($d = -1$). Long signals are reported in diagnostic tables but excluded from strategy execution.
- **Option 3 (Bidirectional Execution):** Authorize execution for both Long ($d = +1$) and Short ($d = -1$) signals, subject to mandatory disaggregated reporting.

#### 4. Implications
- **Technical:** Long and Short trades exhibit mathematical fee asymmetry: under a 7.5 bps fee/slippage rate, a winning Long incurs $15.11$ bps of entry notional in costs, while a winning Short incurs $14.89$ bps (due to fees levied on quote notional $Q \times P_{\text{exit}}$).
- **Statistical:** Restricting execution to one direction cuts trade sample size approximately in half. Directional reporting is mandatory across all options and must not be conflated with execution authorization.
- **Economic:** Crypto perpetuals exhibit secular market drift and funding asymmetry across macro cycles. A bidirectional strategy may suffer severe degradation if Short signals underperform in secular bull regimes.
- **Operational & Risk:** Bidirectional execution accumulates gross notional exposure ($\sum |N_i|$) even when net market exposure is neutral, creating simultaneous liquidation risk during volatility spikes.

#### 5. Dependencies
Depends on `DEC_01`. Informs `DEC_04.6` (confirmatory family size $K$) and `DEC_05` (portfolio exposure).

#### 6. Recommended Option & Rationale
**Structured Choice: Option 3 (Bidirectional Execution) with Mandatory Disaggregated Reporting and Directional Sign Constraints:** Authorizes full signal evaluation while ensuring that a failing Short side cannot be masked by a profitable Long side.

#### 7. Consequences of Rejection or Deferral
Restricting to Option 1 or 2 forfeits half of the model's signals and leaves the portfolio unhedged during opposite regimes. Deferral blocks backtest engine configuration.

---

### DEC_03: FUNDING RATE MODEL

#### 1. Decision Objective
Specify how perpetual futures financing cash flows are modeled in Phase 5.5 economic validation, given that historical AsterDEX funding rate archives are absent (`FUNDING_DATA_UNAVAILABLE`), and resolve whether to evaluate a 4-scenario or 5-scenario parametric sweep grid.

#### 2. Current Status
`PENDING_HUMAN_DECISION`

#### 3. Available Alternatives
- **Option 1 (Zero Funding Assumption):** Set $f_t = 0.0$ bps for all settlements. Evaluates pure price movement and fees while ignoring perpetual carry drag.
- **Option 2 (Static Flat Funding Rate):** Apply a single flat rate of $f_t = +1.0$ bps ($0.01\%$) per 8-hour settlement across all trades.
- **Option 3 (Parametric Sensitivity Sweep Grid + Explicit Settlement Timing Convention):**
  - *Methodology Grid Discrepancy & Drift:* The foundational methodology specification ([`QUANTUM_THREE_TRACK_METHODOLOGY_RECONCILIATION_AUDIT.md`](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_THREE_TRACK_METHODOLOGY_RECONCILIATION_AUDIT.md) and [`QUANTUM_PHASE_5_5_HUMAN_GOVERNANCE_DECISION_WORKSHOP.md`](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_HUMAN_GOVERNANCE_DECISION_WORKSHOP.md)) established an authoritative, symmetric **5-scenario grid**: $f \in \{-3.0, -1.0, 0.0, +1.0, +3.0\}$ bps per 8-hour settlement ($S_{\text{neg3}}, S_{\text{neg1}}, S_{\text{zero}}, S_{\text{pos1}}, S_{\text{pos3}}$), designed to test extreme negative funding drag on Short positions. Subsequent governance briefings ([`QUANTUM_PHASE_5_5_HUMAN_GOVERNANCE_DECISION_BRIEF.md`](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_HUMAN_GOVERNANCE_DECISION_BRIEF.md) and [`QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md`](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md)) proposed a truncated **4-scenario grid**: $f \in \{-1.0, 0.0, +1.0, +3.0\}$ bps, which omitted the extreme negative $-3.0$ bps scenario.
  - *Sub-options for Human Supervisor Determination:*
    - **Sub-option 3-A (5-Scenario Symmetric Methodology Grid):** Evaluate $f \in \{-3.0, -1.0, 0.0, +1.0, +3.0\}$ bps per 8h settlement. Symmetrically stresses both crowded bull regimes ($+3.0$ bps paid by Longs) and crowded bear regimes ($-3.0$ bps paid by Shorts).
    - **Sub-option 3-B (4-Scenario Truncated Proposal Grid):** Evaluate $f \in \{-1.0, 0.0, +1.0, +3.0\}$ bps per 8h settlement. Reduces reporting dimensionality but omits extreme adverse bear stress on Short positions.
  - *Settlement Timing Convention:* Both sub-options are evaluated under the `EXPLICIT_SETTLEMENT_TIMING_MODELING_CONVENTION` ($t_{\text{entry}} < t_{\text{settle}} \le t_{\text{exit}}$).

#### 4. Implications
- **Technical:** Accounting equation enforces signed funding: $CF_{\text{funding}} = \sum (-d) \cdot N_{\text{settle},t} \cdot f_t$. Long pays when $f > 0$; Short receives when $f > 0$.
- **Statistical:** Generates multiple sensitivity tables. `DEC_04` must designate which scenario serves as the primary binding acceptance gate (baseline $+1.0$ bps vs stress $+3.0$ bps). Sub-option 3-A adds 1 additional column/table per asset.
- **Economic:** Under a 12-bar holding horizon (60m), trades cross at most one settlement (maximum $3.0$ bps drag). If holding duration extends to 288 bars (24h), a $+3.0$ bps rate costs $9.0$ bps across 3 settlements, which can wipe out small predictive edges.
- **Operational & Risk:** Parametric scenarios do NOT represent historical distributions or regime spikes; they represent synthetic stress test boundaries under disclosed missing data (`FUNDING_DATA_UNAVAILABLE`).

#### 5. Dependencies
Foundational decision. Feeds net return calculations in `DEC_04` (Gates 2 and 3) and realized loss accounting in `DEC_05`.

#### 6. Recommended Option & Rationale
**Option 3 (Parametric Sensitivity Sweep + Explicit Settlement Timing Convention, Sub-option 3-A):** Sub-option 3-A maintains fidelity to the foundational methodology reconciliation by preserving symmetric stress testing for both Long and Short positions, preventing unhedged bear regime blind spots.

#### 7. Consequences of Rejection or Deferral
Option 1 overstates profitability; Option 2 fails to stress negative funding regimes. Deferral prevents calculation of net economic return.

---

### DEC_04: TRANSACTION COSTS AND STATISTICAL HURDLES (SEVEN SUBDECISIONS)

#### 1. Decision Objective
Establish the accounting rules, cost-basis methodology, resampling architecture, block length, multiplicity control, and economic acceptance hurdles for Phase 5.5. Because `DEC_04` encompasses multiple distinct methodological components, it is decomposed into **seven independent subdecisions**:

#### 2. Current Status
`PENDING_HUMAN_DECISION` (All 7 subdecisions pending; no bundled approval)

#### 3. Modular Subdecisions & Alternatives
- **`DEC_04.1` - Reference-Price Accounting:**
  - *Option 4.1-A:* Approve `REFERENCE_PRICE_ACCOUNTING` decomposition ($L_{\text{realized}} = L_{\text{price,ref}} + C_{\text{exec,total}} + C_{\text{fees}} - CF_{\text{funding}}$), mathematically eliminating double-counting of spread and slippage.
  - *Option 4.1-B:* Reject or request an alternative accounting formulation.
- **`DEC_04.2` - Execution Deviation Methodology:**
  - *Option 4.2-A (`Approach A`):* Nonnegative adverse slippage floor ($C_{\text{slippage}} = \max(0, \text{deviation})$) with separate price improvement ledger.
  - *Option 4.2-B (`Approach B`):* Two-legged signed deviation conserving cash flows symmetrically in a single term.
- **`DEC_04.3` - Partial-Fill Cost-Basis Policy:**
  - *Option 4.3-A (`Average Cost Basis`):* Volume-weighted average entry price (VWAP) proportional allocation.
  - *Option 4.3-B (`FIFO`):* First-In, First-Out chronological lot matching.
  - *Note:* Identical when position is 100% closed; diverges only on intermediate partial closes ($Q_{\text{closed}} < Q_{\text{open}}$).
- **`DEC_04.4` - Bootstrap Resampling Methodology:**
  - *Option 4.4-A (`Trade-Level Bootstrap`):* Resample completed trades with replacement (destroys contemporaneous cross-asset correlation).
  - *Option 4.4-B (`Calendar Moving Block Bootstrap` - Calendar MBB):* Resample contiguous 5-minute calendar blocks across all assets simultaneously, preserving cross-asset correlation.
- **`DEC_04.5` - Candidate Block Length & Sensitivity Sweep:**
  - *Option 4.5-A:* Authorize $b = 288$ bars (24 hours) as a **provisional candidate** block length with a mandatory sensitivity sweep across $b \in \{72, 144, 288, 576\}$ bars.
  - *Option 4.5-B:* Select a different candidate block length or require pre-test autocorrelation estimation.
  - *Constraint:* 288 bars is provisional, NOT an empirically validated optimum (`CLAIMED_ONLY`).
- **`DEC_04.6` - Confirmatory Hypothesis Family Size $K$:**
  - *Determinants:* $K$ is determined jointly by 5 choices: (1) primary universe size (10 vs 11 assets), (2) Long/Short separate tests, (3) Combined series status, (4) asset vs portfolio estimand level, (5) confirmatory vs exploratory gate designations.
  - *Conditional Examples:*
    - Example K-1 ($K = 10$ or $11$): Asset-level, 1 confirmatory test per asset (strictest Holm hurdle: $p \le 0.00500$ or $0.00455$).
    - Example K-2 ($K = 20$ or $22$): Asset-level, Long and Short separate confirmatory tests ($p \le 0.00250$ or $0.00227$).
    - Example K-3 ($K = 30$ or $33$): Asset-level, Long, Short, and Combined all confirmatory ($p \le 0.00167$ or $0.00152$).
    - Example K-4 ($K = 1$): Portfolio-level primary estimand; all asset/directional tables exploratory ($p \le 0.05000$).
- **`DEC_04.7` - Economic Acceptance Criteria & Cost Tiers:**
  - *Option 4.7-A:* Authorize 3 cost tiers (15 bps optimistic, 20 bps baseline, 30 bps stress) and 4-level gate (Level 1: Cost Survival; Level 2: Net Expectancy $> 0$ & Profit Factor $> 1.05$; Level 3: Holm-Bonferroni Significance $\alpha = 0.05$; Level 4: Benchmark Outperformance).
  - *Option 4.7-B:* Modify cost tiers or hurdle thresholds.

#### 4. Implications & Recommended Options
- Recommended: Approve `DEC_04.1` (Option 4.1-A), `DEC_04.2` (Option 4.2-B), `DEC_04.3` (Option 4.3-A), `DEC_04.4` (Option 4.4-B), `DEC_04.5` (Option 4.5-A), `DEC_04.6` (Option K-2: $K=20$), and `DEC_04.7` (Option 4.7-A).
- Consequence of Deferral: Blocks statistical testing, cost accounting, and acceptance validation.

---

### DEC_05: PORTFOLIO CONCURRENCY AND RISK RECONCILIATION

#### 1. Decision Objective
Establish the multi-specialist portfolio risk policy governing gross exposure, position sizing, concurrent position limits, and leverage, decoupled from execution accounting.

#### 2. Current Status
`PENDING_HUMAN_DECISION`

#### 3. Available Alternatives
- **Option 1 (Fixed Gross Exposure Cap):** Apply a hard cap on aggregate notional exposure (e.g. $\sum |N_i| \le 0.30 \times \text{Equity}$). Sizing is fixed per trade. Simple, but concentrates risk in high-volatility assets.
- **Option 2 (Risk-Budget-Based Sizing):** Volatility-scaled sizing targeting fixed modeled stop loss ($N_i = R_{\text{budget}} \cdot \text{Equity} / 1.5\sigma_t$). Vulnerable to inverse-volatility leverage blowups during quiet markets.
- **Option 3 (Combined Exposure Cap & Stop-Risk Budget):** Dual ceiling combining volatility-scaled sizing with a hard aggregate gross exposure cap. Scales down positions pro-rata when simultaneous signals breach the cap.

#### 4. Explicit Distinctions & Risk Realities
- **Gross Exposure vs Leverage:** A 30% gross exposure cap ($\text{GrossLeverage} = 0.30\times$) leaves 70% of equity unexposed in notional terms; it is NOT equivalent to $1.0\times$ leverage.
- **Stop Loss is NOT Maximum Loss:** During market-wide liquidation gaps or flash crashes, execution fills can gap far through stop barriers. A stop loss is an exit trigger, not an absolute guarantee against catastrophic loss.
- **Correlation Stress:** Removing unsupported prior claims ($\rho > 0.70$) does not eliminate risk; crypto perpetuals experience severe correlation spikes ($\rho \to 1.0$) during market cascades.

#### 5. Dependencies
Terminal decision. Depends on `DEC_01` (barrier stop distance), `DEC_02` (netting), `DEC_03` (funding drag), `DEC_04` (accepted specialists), and `DEC_06` (active universe size).

#### 6. Recommended Option & Rationale
**Option 3 (Combined Exposure Cap & Stop-Risk Budget with Explicit Equity Denominator):** Provides the most robust protection against both volatility spikes and low-volatility leverage blowups.

#### 7. Consequences of Rejection or Deferral
Option 1 over-allocates risk to high-vol altcoins; Option 2 risks excessive leverage. Deferral blocks Mode 3 portfolio simulation.

---

### DEC_06: XMRUSDT STRUCTURAL-BREAK SCOPE

#### 1. Decision Objective
Determine the research and portfolio scope for `XMRUSDT`, given its 73.5% historical data truncation (83,863 candles starting January 2026 vs 316,500 candles for the 10 major assets starting October 2023).

#### 2. Current Status
`PENDING_HUMAN_DECISION`

#### 3. Available Alternatives
- **Option 1 (Full Primary Portfolio Inclusion):** Include `XMRUSDT` in the primary 3-year portfolio simulation and confirmatory hypothesis family ($K = 11, 22, 33$).
- **Option 2 (Complete Elimination):** Discard `XMRUSDT` entirely from Phase 5.5.
- **Option 3 (Three-Tier Policy):**
  - *Tier 1:* Preserve 100% of frozen Phase 5.3 models, preprocessors, and Phase 5.4 probability artifacts.
  - *Tier 2:* Evaluate `XMRUSDT` economic performance in a dedicated standalone Fold 5 research appendix.
  - *Tier 3:* Exclude `XMRUSDT` from the primary 10-asset 3-year portfolio aggregation and primary confirmatory family ($K = 10, 20$).

#### 4. Implications
- **Technical & Statistical:** Option 1 either forces the entire 11-asset portfolio backtest to truncate from 3 years down to 9.5 months (discarding 73.5% of major asset data) or introduces ragged-array distortion into continuous calendar resampling. Option 3 maintains a balanced 3-year primary universe.
- **Economic:** Option 3 prevents short-history privacy coin anomalies from distorting long-term portfolio metrics while preserving research value.

#### 5. Dependencies
Foundational decision. Determines base universe size for `DEC_04.6` ($10$ vs $11$ assets) and max concurrent specialists in `DEC_05`.

#### 6. Recommended Option & Rationale
**Option 3 (Three-Tier Policy):** Preserves research investment without corrupting the 3-year balanced primary portfolio.

#### 7. Consequences of Rejection or Deferral
Option 1 severely distorts multi-asset resampling; Option 2 wastes prior research. Deferral leaves universe size unsettled.

---

# SECTION E: CROSS-DECISION DEPENDENCY MATRIX

```text
+---------------------------------------------------------------------------------------------------------+
|                                CROSS-DECISION INTERACTION MATRIX                                        |
+---------------------------------------------------------------------------------------------------------+
| Downstream \ Upstream | DEC_01 (Arch) | DEC_02 (Dir) | DEC_03 (Fund) | DEC_04 (Cost) | DEC_06 (XMR)     |
+-----------------------+---------------+--------------+---------------+---------------+------------------+
| DEC_02 (Direction)    | Governs exit  |     ---      |     ---       |     ---       |     ---          |
|                       | geometry      |              |               |               |                  |
+-----------------------+---------------+--------------+---------------+---------------+------------------+
| DEC_03 (Funding)      | Independent   | Independent  |     ---       |     ---       |     ---          |
|                       | convention    | convention   |               |               |                  |
+-----------------------+---------------+--------------+---------------+---------------+------------------+
| DEC_04 (Cost/Stat)    | Defines entry | Joint input  | Feeds net     |     ---       | Sets asset base  |
|                       | estimand      | into K       | return gate   |               | for K (10 vs 11) |
+-----------------------+---------------+--------------+---------------+---------------+------------------+
| DEC_05 (Portfolio)    | Stop distance | Directional  | Funding drag  | Passed        | Max concurrent   |
|                       | 1.5*sigma     | netting      | on equity     | specialists   | assets (10/11)   |
+---------------------------------------------------------------------------------------------------------+
```

### Critical Path Resolution Sequencing
1. **Stage 1 (Foundational Methodology):** Resolve `DEC_01` (Barrier Architecture), `DEC_03` (Funding Rate Model), and `DEC_06` (XMR Universe Scope).
2. **Stage 2 (Execution Scope & Multiplicity):** Resolve `DEC_02` (Directional Scope) and `DEC_04.1` through `DEC_04.7` (Cost, Accounting, Resampling, Block Length, Family $K$).
3. **Stage 3 (Portfolio Integration):** Resolve `DEC_05` (Portfolio Concurrency & Risk Policy) based on outputs from Stages 1 and 2.

---

# SECTION F: STATISTICAL AND ECONOMIC LIMITATIONS REGISTER

| Limitation ID | Category | Specific Operational Limitation | Epistemic Classification | Decision Impact & Constraints |
|---|---|---|---|---|
| `LIM-01` | Temporal Validation | **Fold 5 OOS Eligibility:** Temporal purge/embargo boundaries between Fold 4 training and Fold 5 holdout are unreconciled. | `FOLD_5_OOS_ELIGIBILITY = OOS_ELIGIBILITY_NOT_VERIFIED` | Fold 5 must be strictly segregated from Folds 1 to 4 (VERIFIED_OOF) and Prospective Holdout (SEALED); exploratory/diagnostic profiling only; confirmatory economic claims PROHIBITED. |
| `LIM-02` | Holdout Boundary | **Prospective Holdout Isolation:** Observations with `open_time_ms >= 1793491200000` (Nov 1, 2026 UTC) have governance status `PROSPECTIVE_HOLDOUT_GOVERNANCE_STATUS = STRICTLY_SEALED`. Artifact timestamp boundary check is `TEST_VERIFIED` (max timestamp `1777586100000 < 1793491200000`). Access history is `PROSPECTIVE_HOLDOUT_ACCESS_HISTORY = NOT_VERIFIED` (`HISTORICAL_ACCESS_NOT_VERIFIABLE_FROM_AVAILABLE_LOGS` due to absence of filesystem access audit logs; during the current reconciliation task, no prospective holdout files were intentionally opened, read, or evaluated; historical access across earlier tasks remains `NOT_VERIFIED`). | `STRICTLY_SEALED` | Unsealing holdout data is strictly prohibited during Phase 5.5; verification relies exclusively on historical OOF data; requires separate uncompromised human authorization post Phase 5.5. |
| `LIM-03` | Target Divergence | **Estimand Divergence:** Phase 5.3 models predict a 12-bar classification label, whereas Track 2 evaluates realized net PnL. | `MATHEMATICALLY_VERIFIED` | Model probabilities are NOT automatically calibrated to Track 2 economic returns. |
| `LIM-04` | Market Data | **AsterDEX Funding Data Absence:** Historical venue funding rates were not collected (`FUNDING_DATA_UNAVAILABLE`). | `NOT_VERIFIED` | Economic backtests rely on parametric sensitivity sweeps, not empirical venue distributions. |
| `LIM-05` | Market Data | **Venue Settlement Semantics:** AsterDEX matching engine boundary timestamp rules (08:00:00.000) are unverified. | `NOT_VERIFIED` | Settlement relies on modeling convention ($t_{\text{entry}} < t_{\text{settle}} \le t_{\text{exit}}$). |
| `LIM-06` | Execution Cost | **Parametric Friction Tiers:** Fixed taker fees ($15$ bps) and slippage ($2$ bps) omit dynamic book depletion. | `METHODOLOGICAL_ASSUMPTION` | Results reflect fixed-cost hurdles, not empirical tick-level liquidity fills. |
| `LIM-07` | Resampling | **288-Bar MBB Candidate Status:** Candidate block length $b = 288$ bars is a theoretical proposal. | `CLAIMED_ONLY` | Sensitivity analysis across $b \in \{72, 144, 288, 576\}$ bars is mandatory. |
| `LIM-08` | Statistical Power | **Hypothesis Family Multiplicity:** Large family size ($K=20, 22, 30, 33$) increases Type II false rejections. | `MATHEMATICALLY_VERIFIED` | Family $K$ must be formally fixed in `DEC_04.6` prior to backtest execution. |
| `LIM-09` | Portfolio Risk | **Gap-Through-Stop Tail Risk:** Stop-loss barriers are exit triggers, not guaranteed maximum loss caps. | `OPERATIONAL_REALITY` | Extreme market gap risk cannot be eliminated by position sizing or stop orders. |
| `LIM-10` | Asset Coverage | **XMR Coverage Disparity:** `XMRUSDT` has only 83,863 candles (73.5% missing-data gap). | `SOURCE_VERIFIED` | XMR must be excluded from primary 3-year portfolio resampling (`DEC_06`). |

---

# SECTION G: HUMAN DECISION RECORD TEMPLATES

```text
================================================================================
RECORD 1: GOVERNANCE EXCEPTION EXC-PHASE55-01 RATIFICATION RECORD
================================================================================
Decision ID:          EXC-PHASE55-01
Decision Question:    Does the Human Governance Supervisor ratify the backtesting
                      codebase modifications committed across commits 222d0c3 and
                      a3f5158 (implementing simulated clock, PnL accounting, event
                      runner, adapters, Track 1 evaluator, and thread limits without
                      prior formal Layer 1 authorization)?
Selected Alternative: RATIFY_WITH_CONDITIONS
Conditions / Limits:  Confirmatory research restricted to Folds 1 to 4 (VERIFIED_OOF); Fold 5 restricted strictly to exploratory profiling (FOLD_5_OOS_ELIGIBILITY = OOS_ELIGIBILITY_NOT_VERIFIED); funding carry evaluated exclusively via parametric sensitivity sweeps; prospective holdout data strictly sealed.
Rejected Options:     REJECT_AND_QUARANTINE, DEFER
Supervisor Rationale: Formally accept implemented backtesting infrastructure into baseline to resolve technical qualification findings FND-01 through FND-10 without modifying frozen model weights or accessing prospective holdout data.
Supervisor Identity:  Azis Maulana Suhada (Project Owner & Human Governance Supervisor)
Decision Timestamp:   2026-11-03 00:33:30 UTC
Approval Signature:   Azis Maulana Suhada
Effective Status:     RATIFIED_WITH_CONDITIONS
================================================================================

================================================================================
RECORD 2: LAYER 2 TECHNICAL DESIGN APPROVAL RECORD
================================================================================
Decision ID:          LAYER_2_TECHNICAL_DESIGN_APPROVAL
Decision Question:    Does the Human Governance Supervisor approve the technical
                      specification and test qualification of the backtest runner?
Selected Alternative: APPROVE_WITH_CONDITIONS
Conditions / Limits:  Hardware CPU thread limit (BACKTEST_MAX_THREADS = 2) strictly enforced; RAM usage <= 100 MB via sequential asset processing; Track 1 and Track 2 reported disaggregated; Mode 3 risk limits enforced per DEC_05.
Rejected Options:     RETURN_FOR_REVISION, DEFER
Supervisor Rationale: Architecture is causal, deterministic, resource-bounded, and eliminates wall-clock coupling.
Supervisor Identity:  Azis Maulana Suhada (Project Owner & Human Governance Supervisor)
Decision Timestamp:   2026-11-03 00:33:30 UTC
Approval Signature:   Azis Maulana Suhada
Effective Status:     APPROVED_WITH_CONDITIONS
================================================================================

================================================================================
RECORD 3: DEC_01 BARRIER EXECUTION ARCHITECTURE DECISION RECORD
================================================================================
Decision ID:          DEC_01
Decision Question:    Which barrier execution architecture is authorized for Phase 5.5?
Selected Alternative: Alternative B (Track 2 Primary) + Alternative C (Track 3 Exploratory)
Conditions / Limits:  Alternative B serves as the primary binding benchmark on open[t+1] re-anchored symmetric barriers over 12-bar horizon; Alternative C authorized for exploratory alpha research with dynamic stops and trailing TP.
Rejected Options:     Alternative A (Track 1 close-anchored barriers are unexecutable economic entry anchors)
Supervisor Rationale: Evaluates raw directional signals under causal execution without post-hoc overfitting, while concurrently authorizing dynamic exit rules in Track 3 to fulfill aggressive trading alpha exploration.
Supervisor Identity:  Azis Maulana Suhada (Project Owner & Human Governance Supervisor)
Decision Timestamp:   2026-11-03 00:33:30 UTC
Approval Signature:   Azis Maulana Suhada
Effective Status:     RESOLVED_AND_AUTHORIZED
================================================================================

================================================================================
RECORD 4: DEC_02 DIRECTIONAL TRADING SCOPE DECISION RECORD
================================================================================
Decision ID:          DEC_02
Decision Question:    Which directional execution scope is authorized for Phase 5.5?
Selected Alternative: Option 3 (Bidirectional Execution with Mandatory Disaggregated Reporting)
Conditions / Limits:  Long, Short, and Combined performance must be reported separately across all assets; directional sign constraints enforced.
Rejected Options:     Option 1 (Long-Only Execution), Option 2 (Short-Only Execution)
Supervisor Rationale: Mandatory for 24/7 continuous autonomous trading across bull and bear regimes; disaggregated reporting prevents failing shorts from hiding behind bull drift.
Supervisor Identity:  Azis Maulana Suhada (Project Owner & Human Governance Supervisor)
Decision Timestamp:   2026-11-03 00:33:30 UTC
Approval Signature:   Azis Maulana Suhada
Effective Status:     RESOLVED_AND_AUTHORIZED
================================================================================

================================================================================
RECORD 5: DEC_03 FUNDING RATE MODEL DECISION RECORD
================================================================================
Decision ID:          DEC_03
Decision Question:    Which funding rate model and timing convention are authorized?
Selected Alternative: Option 3, Sub-option 3-A (5-Scenario Symmetric Grid: -3.0, -1.0, 0.0, +1.0, +3.0 bps)
Conditions / Limits:  Evaluated under modeling convention t_entry < t_settle <= t_exit; parametric sensitivity only, not historical observations.
Rejected Options:     Option 1 (Zero funding), Option 2 (Static flat +1.0 bps), Option 3-B (4-scenario truncated)
Supervisor Rationale: Symmetric stress testing is necessary for bidirectional trading to stress both Longs (+3 bps) and Shorts (-3 bps).
Supervisor Identity:  Azis Maulana Suhada (Project Owner & Human Governance Supervisor)
Decision Timestamp:   2026-11-03 00:33:30 UTC
Approval Signature:   Azis Maulana Suhada
Effective Status:     RESOLVED_AND_AUTHORIZED
================================================================================

================================================================================
RECORD 6: DEC_04 TRANSACTION COSTS & STATISTICAL HURDLES DECISION RECORD
================================================================================
Decision ID:          DEC_04 (Modular Subdecisions 4.1 through 4.7)
DEC_04.1 (Accounting):    Option 4.1-A (Two-Legged Reference-Price Accounting)
DEC_04.2 (Deviation):     Option 4.2-B (Two-Legged Signed Cash-Conserving Deviation)
DEC_04.3 (Cost Basis):    Option 4.3-A (VWAP Average Cost Basis)
DEC_04.4 (Resampling):    Option 4.4-B (Calendar Moving Block Bootstrap - MBB)
DEC_04.5 (Block Length):  Option 4.5-A (Provisional 288-bar candidate block with sensitivity sweep across {72, 144, 288, 576} bars)
DEC_04.6 (Family K):      Example K-2 (K = 20 confirmatory tests across 10 primary assets x Long/Short)
DEC_04.7 (Cost & Gates):  Option 4.7-A (3 Cost Tiers: 15/20/30 bps, 4-Level Gate)
Supervisor Rationale: Mathematical conservation of cash flows, preservation of contemporaneous cross-asset correlation, and rigorous Holm-Bonferroni FWER control.
Supervisor Identity:  Azis Maulana Suhada (Project Owner & Human Governance Supervisor)
Decision Timestamp:   2026-11-03 00:33:30 UTC
Approval Signature:   Azis Maulana Suhada
Effective Status:     RESOLVED_AND_AUTHORIZED
================================================================================

================================================================================
RECORD 7: DEC_05 PORTFOLIO CONCURRENCY & RISK POLICY DECISION RECORD
================================================================================
Decision ID:          DEC_05
Decision Question:    Which portfolio risk and concurrency policy is authorized?
Selected Alternative: Option 3 (Combined Exposure Cap <= 0.30 x Equity & Volatility Risk-Budget Sizing)
Conditions / Limits:  Hard aggregate gross exposure ceiling sum |N_i| <= 0.30 x Equity; single-asset sizing N_i = R_budget * Equity / 1.5 sigma_t with pro-rata scaling on concurrent breaches.
Rejected Options:     Option 1 (Fixed Gross Cap), Option 2 (Unconstrained Volatility Sizing)
Supervisor Rationale: Dual ceiling prevents inverse-volatility leverage blowups while bounding cross-asset cascade liquidation risk.
Supervisor Identity:  Azis Maulana Suhada (Project Owner & Human Governance Supervisor)
Decision Timestamp:   2026-11-03 00:33:30 UTC
Approval Signature:   Azis Maulana Suhada
Effective Status:     RESOLVED_AND_AUTHORIZED
================================================================================

================================================================================
RECORD 8: DEC_06 XMRUSDT STRUCTURAL-BREAK SCOPE DECISION RECORD
================================================================================
Decision ID:          DEC_06
Decision Question:    How should XMRUSDT be treated in Phase 5.5 economic validation?
Selected Alternative: Option 3 (Three-Tier Policy for XMRUSDT)
Conditions / Limits:  Tier 1: preserve frozen models; Tier 2: evaluate in dedicated standalone research appendix; Tier 3: exclude from primary 10-asset 3-year portfolio aggregation and primary K=20 family.
Rejected Options:     Option 1 (Full 3-year inclusion truncates data by 73.5%), Option 2 (Complete elimination)
Supervisor Rationale: Preserves 3-year continuous historical baseline for 10 major assets while preserving research on XMR.
Supervisor Identity:  Azis Maulana Suhada (Project Owner & Human Governance Supervisor)
Decision Timestamp:   2026-11-03 00:33:30 UTC
Approval Signature:   Azis Maulana Suhada
Effective Status:     RESOLVED_AND_AUTHORIZED
================================================================================

================================================================================
RECORD 9: GATE 4 RESEARCH EXECUTION AUTHORIZATION RECORD
================================================================================
Decision ID:          GATE_04_RESEARCH_EXECUTION_AUTHORIZATION
Decision Question:    Does the Human Governance Supervisor authorize research agents
                      to execute Phase 5.5 historical economic backtests across
                      Folds 1 to 4 (confirmatory) and Fold 5 (exploratory only,
                      FOLD_5_OOS_ELIGIBILITY = OOS_ELIGIBILITY_NOT_VERIFIED), with
                      prospective holdout data remaining strictly sealed?
Prerequisites:        Gate 1 (EXC-PHASE55-01), Gate 2 (Layer 2 Design), and
                      Gate 3 (DEC_01 through DEC_06) must all be formally signed.
Selected Alternative: AUTHORIZE_WITH_APPROVED_SCOPE
Authorized Scope:     Historical Folds 1 to 4 (Confirmatory) and Historical Fold 5 (Exploratory Only); Track 1, Track 2, and Track 3 evaluations across all 11 specialists.
Conditions / Limits:  Prospective holdout data (open_time_ms >= 1793491200000, Nov 1, 2026 UTC) remains STRICTLY SEALED; BACKTEST_MAX_THREADS = 2 strictly enforced; RAM <= 1 GB; Phase 5.6 remains NOT_AUTHORIZED.
Rejected Options:     REJECT, DEFER
Supervisor Rationale: Gates 1, 2, and 3 are formally resolved and satisfied; research execution authorized to obtain empirical economic evidence.
Supervisor Identity:  Azis Maulana Suhada (Project Owner & Human Governance Supervisor)
Decision Timestamp:   2026-11-03 00:33:30 UTC
Approval Signature:   Azis Maulana Suhada
Effective Status:     AUTHORIZED_FOR_EXECUTION
================================================================================
```

---

# SECTION H: EXECUTION AUTHORIZATION SEPARATION

### Multi-Gate Governance Architecture
Under the QUANTUM Two-Layer Governance Framework, completing administrative or technical qualification steps does NOT grant permission to execute backtests on historical data:

```text
+---------------------------------------------------------------------------------------------------------+
|                               GOVERNANCE GATEWAY TO PHASE 5.5 EXECUTION                                 |
+---------------------------------------------------------------------------------------------------------+
  [THREE CO-REQUISITE PREREQUISITES - NON-SERIAL PEER REQUIREMENTS]
  +-----------------------------+ +-----------------------------+ +-----------------------------+
  | Gate 1: EXC-PHASE55-01      | | Gate 2: Layer 2 Technical   | | Gate 3: Layer 1 Decision    |
  | Ratification                | | Design Approval             | | Gate Resolutions (DEC_01-06)|
  | Status: PENDING_RATIFICATION| | Status: NOT_APPROVED        | | Status: PENDING_DECISION    |
  +-----------------------------+ +-----------------------------+ +-----------------------------+
                 \                               |                               /
                  +------------------------------+------------------------------+
                                                 |
                                                 v
  Gate 4: Explicit Written Phase 5.5 Research Execution Authorization (Status: NOT_STARTED / NOT_AUTHORIZED)
                                                 |
                 +-------------------------------+-------------------------------+
                 |                                                               |
                 v                                                               v
  [Historical Folds 1 to 4 Execution]                          [Historical Fold 5 Execution]
  - Eligibility: VERIFIED_OOF                                  - Eligibility: OOS_ELIGIBILITY_NOT_VERIFIED
  - Scope: Confirmatory baseline research                      - Scope: Exploratory / diagnostic only
  - Net economic estimand evaluation                           - Confirmatory claims PROHIBITED
                 |                                                               |
                 +-------------------------------+-------------------------------+
                                                 |
                                                 v
  Gate 5: Prospective Holdout Gate (Nov 1, 2026 - Apr 30, 2027; open_time_ms >= 1793491200000)
          Status: STRICTLY_SEALED.
          Requires separate, uncompromised human authorization after Phase 5.5 closes.
          Cannot be unsealed or accessed during Phase 5.5 historical backtesting.
+---------------------------------------------------------------------------------------------------------+
```

### Formal Execution Authorization Status
Gates 1 through 4 have been formally resolved and signed by the Project Owner and Human Governance Supervisor (Azis Maulana Suhada) on 2026-11-03 00:33:30 UTC:
- Historical economic backtesting on Folds 1 to 5 is `AUTHORIZED_HISTORICAL_RESEARCH_ONLY`.
- Historical Folds 1 to 4 are authorized for confirmatory research (`VERIFIED_OOF`).
- Historical Fold 5 is authorized strictly for exploratory and diagnostic profiling (`FOLD_5_OOS_ELIGIBILITY = OOS_ELIGIBILITY_NOT_VERIFIED`) and must NOT be bundled into confirmatory economic claims.
- Prospective holdout data (Nov 1, 2026 to Apr 30, 2027; `open_time_ms >= 1793491200000`) remains strictly `SEALED` and isolated from Phase 5.5 historical backtesting.
- Phase 5.5 research execution status is `PHASE55_RESEARCH_EXECUTION_STATUS = AUTHORIZED_FOR_EXECUTION`.
- Phase 5.5 governance review status is `PHASE55_GOVERNANCE_REVIEW_STATUS = RATIFIED_AND_SIGNED`.
- Phase 5.6 (Production Strategy) remains strictly `NOT_AUTHORIZED`.

---
*End of Human Governance Decision Package.*
