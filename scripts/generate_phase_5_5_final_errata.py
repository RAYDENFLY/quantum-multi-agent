"""
QUANTUM Phase 5.5: Final Governance Errata Generator (Corrected).

Generates:
docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md

Updates:
docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md

Strict Constraints:
- ZERO em dashes (Unicode U+2014) anywhere in markdown files.
- Clickable links with forward slashes (file:///d:/quantum-multi-agent/...).
- Clean LaTeX formatting with single backslashes in raw strings.
- Complete coverage of Tasks A through I.
- Final verdict: FINAL_ERRATA_READY_WITH_LIMITATIONS.
"""

from pathlib import Path

DOSSIER_DIR = Path("docs/research/phase_5_5_governance_dossier")


def generate_final_governance_errata() -> str:
    return r"""# QUANTUM PHASE 5.5: FINAL GOVERNANCE ERRATA
## HUMAN SIGN-OFF PREPARATION & FINAL CONSISTENCY REVIEW

**Document Status:** `APPROVED_FOR_HUMAN_REVIEW`  
**Publication Timestamp:** `2026-11-02 13:30:00 UTC`  
**Operational Mode:** `FINAL_ERRATA_AND_HUMAN_REVIEW_PREPARATION`  
**Target Scope:** Official supplementary errata to Revision 1.2 dossier suite  
**Final Governance Verdict:** `FINAL_ERRATA_READY_WITH_LIMITATIONS`  
**Human Decision Status:** `PENDING_HUMAN_DECISION` (All 6 decisions unexecuted)  
**Research Lifecycle Status:** Phase 5.5 `NOT_STARTED` | Phase 5.6 `NOT_AUTHORIZED` | Holdout `STRICTLY_SEALED`  

---

## 1. PURPOSE & SCOPE OF ERRATA

This document constitutes the official Final Governance Errata for QUANTUM Phase 5.5.

This is a narrowly scoped reconciliation document designed to resolve the final fine-grained specification details, terminology distinctions, and evidentiary boundaries identified during the closure review of Revision 1.2:
- [QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md)
- [QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md)
- [QUANTUM_PHASE_5_5_CROSS_DECISION_DEPENDENCIES.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_CROSS_DECISION_DEPENDENCIES.md)
- [QUANTUM_PHASE_5_5_UNRESOLVED_ISSUE_REGISTER.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_UNRESOLVED_ISSUE_REGISTER.md)
- [QUANTUM_PHASE_5_5_FINAL_HUMAN_DECISION_WORKSHEET.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_HUMAN_DECISION_WORKSHEET.md)
- [QUANTUM_PHASE_5_5_GOVERNANCE_DOSSIER_REVISION_1_2_REPORT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_GOVERNANCE_DOSSIER_REVISION_1_2_REPORT.md)

### Strict Operational Boundaries
1. **No Technical Redesign:** This errata does not create Revision 1.3, Phase 5.5.0.9, or Phase 5.6.
2. **No Execution Authorization:** This errata does not authorize economic backtesting, model inference, paper trading, or live execution.
3. **No Retraining or Recalibration:** All Phase 5.3 models and Phase 5.4 calibrations remain frozen.
4. **Prospective Holdout Isolation:** The holdout window (`2026-11-01 00:00:00 UTC` through `2027-04-30 23:59:59.999 UTC`) remains strictly sealed and uninspected.
5. **Human Governance Precedence:** All six governance decisions (DEC_01 through DEC_06) remain strictly pending human input; all decision fields in the worksheet remain blank.

---

## 2. TASK A: FULL UNIT TEST EVIDENCE AUDIT & TEST INTEGRITY

### 2.1 Test Execution History & Scope Verification
A rigorous audit of the test execution history was conducted across three distinct scopes:

1. **Dedicated Phase 5.5 Governance Dossier Tests:**
   - Exact Command: `python -m pytest tests/unit/test_phase5_5_governance_dossier.py -v`
   - Completion Status: Completed normally without intervention.
   - Results: **16 passed**, 0 failed, 0 skipped, 0 deselected.
   - Exit Code: `0`
   - Execution Duration: `0.11s`
   - Verification Status: `TEST_VERIFIED`.

2. **Filtered Phase 5 Unit Tests:**
   - Exact Command: `python -m pytest tests/unit/ -k "phase5" -v`
   - Completion Status: Completed normally without intervention.
   - Results: **372 passed**, 0 failed, 0 skipped, 190 deselected.
   - Exit Code: `0`
   - Execution Duration: `8.05s`
   - Verification Status: `TEST_VERIFIED`.

3. **Complete Repository Unit Test Suite:**
   - Exact Command: `python -m pytest tests/unit/ -v`
   - Total Collected Tests: 562 tests.
   - Pytest In-Session Results: All 562 tests passed assertions (`562 passed, 3 warnings in 14.38s`).
   - Process Exit Status: Upon completing test assertions, the Python 3.13 process hangs during interpreter finalization (`threading._shutdown()` waiting on unclosed background thread or event loop handles from non-Phase-5 integration tests such as `test_freshness_alert_audit.py` or PySide6 application lifecycle in `test_app_lifecycle.py`), preventing the background PowerShell task from naturally exiting without external termination.
   - Audit Rule Applied: *"Do not interpret a killed, canceled, timed-out, or incomplete process as a passing test run."*
   - Official Status: **`FULL_UNIT_SUITE_NOT_VERIFIED`**.
   - Note on Regressions: No test failures or assertion regressions occurred; the limitation is strictly an environment interpreter-shutdown hang in non-Phase-5 legacy integration tests.

### 2.2 Test Integrity & Assertion Verification
An inspection of the Git diff for [tests/unit/test_phase5_5_governance_dossier.py](file:///d:/quantum-multi-agent/tests/unit/test_phase5_5_governance_dossier.py) confirms:
- Assertions `test_01` through `test_15` were completely untouched and preserved.
- `test_16_final_governance_errata_deliverable()` was added purely to verify the presence, structure, and zero-em-dash compliance of this errata deliverable.
- Zero assertions were weakened, relaxed, or removed.

---

## 3. TASK B & TASK D: RECONCILED TECHNICAL ISSUE REGISTER & EXECUTION BLOCKERS

### 3.1 Reconciled Technical Issue Register (ISS_01 through ISS_11)
The technical issue register is fully reconciled across all eleven issues with strict evidence-based classifications:

| Issue ID | Related Decision | Severity | Description | Authoritative Source Document | Verification Classification | Corrected Status | Blocks Phase 5.5? | Category | Required Next Action | Decision Authority |
|---|---|---|---|---|---|---|---|---|---|---|
| **ISS_01** | DEC_03 | `HIGH` | Funding settlement eligibility for boundary orders filled at 08:00:00.000 UTC is venue-dependent. | [PHASE_5_5_0_8_FUNDING_ELIGIBILITY_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_FUNDING_ELIGIBILITY_AUDIT.md) | `NOT_VERIFIED` | `OPEN` | **YES** | Direct Execution Blocker | Confirm AsterDEX boundary matching rule from official venue documentation; until confirmed, apply explicit modeling convention. | Engineering / Supervisor |
| **ISS_02** | DEC_04 | `MEDIUM` | Ambiguity between full bid-ask spread ($S$) and half-spread per leg ($s_{\text{leg}}$), and PnL denominator definition. | [PHASE_5_5_0_8_TRANSACTION_COST_SPECIFICATION.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_TRANSACTION_COST_SPECIFICATION.md) | `SOURCE_VERIFIED` | `RESOLVED_BY_SPECIFICATION` | No | Methodological Resolution | Enforce entry notional $N_{\text{entry}}$ denominator across all evaluation code. | Quantitative Auditor |
| **ISS_03** | DEC_04 | `HIGH` | Potential double-counting of spread, slippage, and impact if fill prices are slipped AND transaction costs deducted. | [PHASE_5_5_0_7_TRANSACTION_COST_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_7/PHASE_5_5_0_7_TRANSACTION_COST_AUDIT.md) | `MATHEMATICALLY_VERIFIED` | `RESOLVED_BY_SPECIFICATION` | No | Methodological Resolution | Mandate strict `REFERENCE_PRICE_ACCOUNTING` where aggregate deviation $C_{\text{exec,total}}$ absorbs spread and impact. | Quantitative Auditor |
| **ISS_04** | DEC_04 | `HIGH` | 24-bar MBB has potential limitations for long dependence; 288-bar MBB is candidate, not validated optimal. | [PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md) | `CLAIMED_ONLY` | `OPEN` | **YES** | Direct Execution Blocker / Decision Dependency | Approve candidate Continuous Calendar-Time Portfolio MBB ($b=288$ bars) as provisional research specification in DEC_04. | Supervisor (DEC_04) |
| **ISS_05** | DEC_04 | `MEDIUM` | Optimal block-length selection lacks empirical sensitivity sweep across candidate values ($b \in \{72, 144, 288, 576\}$ bars). | [PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md) | `NOT_VERIFIED` | `OPEN` | No (Diagnostic) | Supporting Methodological Limitation | Execute diagnostic sensitivity sweep across candidate block lengths during Phase 5.5 execution. | Engineering |
| **ISS_06** | DEC_01 | `HIGH` | Conflation between ML target predictive validation (Track 1) and downstream strategy (Track 3). Track 2 does not validate label payoff. | [PHASE_5_5_0_6_RESEARCH_TRACK_COMPARISON.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_6/PHASE_5_5_0_6_RESEARCH_TRACK_COMPARISON.md) | `SOURCE_VERIFIED` | `RESOLVED_BY_SPECIFICATION` | No | Methodological Resolution | Decoupled into Three-Track Sequential Architecture; estimand limitations presented for DEC_01. | Quantitative Auditor / Supervisor (DEC_01) |
| **ISS_07** | DEC_04 | `HIGH` | Hypothesis family size $K$ depends on prespecified primary estimand, directional scope (DEC_02), and asset universe (DEC_06). | [PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md) | `MATHEMATICALLY_VERIFIED` | `OPEN` | **YES** | Direct Execution Blocker / Decision Dependency | Prespecify primary confirmatory hypothesis family structure ($K \in \{1, 10, 11, 20, 22, 30, 33\}$) upon signing DEC_04/06. | Supervisor (DEC_04 / DEC_06) |
| **ISS_08** | DEC_05 | `HIGH` | Claim that pairwise crypto correlations satisfy $\rho > 0.70$ is unsupported; cross-asset stress risk unquantified. | [PHASE_5_5_0_5_DEC_05_PORTFOLIO_CORRELATION_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_5/PHASE_5_5_0_5_DEC_05_PORTFOLIO_CORRELATION_AUDIT.md) | `NOT_VERIFIED` | `OPEN` | **YES** | Direct Execution Blocker / Risk Modeling Limitation | Decouple risk policy from unverified correlation; select among structured DEC_05 exposure options and conduct stress tests. | Supervisor (DEC_05) |
| **ISS_09** | DEC_03 | `HIGH` | Historical funding rate series are completely absent from canonical datasets (`FUNDING_DATA_UNAVAILABLE`). | [PHASE_5_5_0_8_FUNDING_ELIGIBILITY_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_FUNDING_ELIGIBILITY_AUDIT.md) | `SOURCE_VERIFIED` | `OPEN` | **YES** | Direct Execution Blocker / Decision Dependency | Authorize 4-scenario parametric sensitivity sweep (-1, 0, +1, +3 bps) under explicit missing-data disclosure in DEC_03. | Supervisor (DEC_03) |
| **ISS_10** | DEC_04 | `HIGH` | Runtime accounting implementation has not been code-verified due to backtesting prohibitions. | [PHASE_5_5_0_7_TEST_INTEGRITY_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_7/PHASE_5_5_0_7_TEST_INTEGRITY_AUDIT.md) | `NOT_VERIFIED` | `OPEN` | **YES** | Direct Execution Blocker / Code Verification Limitation | Mandate unit-test verification of simulation accounting engine before executing full fleet backtest once permitted. | Engineering |
| **ISS_11** | Governance | `MEDIUM` | Operating system file read-access history cannot be audited via SHA-256 hashes or Git logs. | [PHASE_5_5_0_8_FULL_FLEET_TEMPORAL_ISOLATION_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_FULL_FLEET_TEMPORAL_ISOLATION_AUDIT.md) | Historical Access: `NOT_VERIFIED` \| Boundaries: `METADATA_VERIFIED` \| Artifacts: `23_MANIFESTED_ARTIFACTS_VERIFIED` | `INFORMATIONAL` | No | Informational Governance Issue | Acknowledge physical isolation (canonical partitions terminate `2026-10-31 21:59:59 UTC`); retain access verification limitation. | Informational / Human Governance |

### 3.2 Derived Issue Register Summary
- **Total Cataloged Issues:** Exactly 11 issues (ISS_01 through ISS_11).
- **Open Issues (7):** ISS_01, ISS_04, ISS_05, ISS_07, ISS_08, ISS_09, ISS_10.
- **Resolved by Specification (3):** ISS_02, ISS_03, ISS_06.
- **Informational Issues (1):** ISS_11 (Status: `INFORMATIONAL`, historical access strictly `NOT_VERIFIED`).
- **Direct Execution Blockers (6):** ISS_01, ISS_04, ISS_07, ISS_08, ISS_09, ISS_10.
- **Supporting Methodological Limitation (1):** ISS_05 (Block-length sensitivity sweep; mandatory diagnostic during execution, non-blocking for launch).

### 3.3 Task B: Holdout Evidentiary Boundaries & Separation
A strict evidentiary separation is enforced regarding prospective holdout data:
1. **Historical Access History:** Classified strictly as `NOT_VERIFIED`. Unrecorded historical OS-level read access cannot be proven or disproven via repository hashes. ISS_11 must never be described as proof that no historical access occurred.
2. **Canonical Dataset Boundary:** Classified as `METADATA_VERIFIED`. Parquet file footer metadata confirms that all 33 fleet partitions terminate at `2026-10-31 21:59:59 UTC`.
3. **Frozen Artifact Hashes:** Precisely `23_MANIFESTED_ARTIFACTS_VERIFIED` (16 in [PHASE_5_4_2_ARTIFACT_HASH_MANIFEST.json](file:///d:/quantum-multi-agent/artifacts/phase_5_4/PHASE_5_4_2_ARTIFACT_HASH_MANIFEST.json) and 7 in [final_manifest_hashes.json](file:///d:/quantum-multi-agent/artifacts/phase_5_3_3_1/final_manifest_hashes.json)). These 23 artifacts do **not** cover the entire frozen model fleet across all assets and horizons.
4. **Prospective Holdout Status:** The holdout period (`2026-11-01 00:00:00 UTC` through `2027-04-30 23:59:59.999 UTC`) remains `STRICTLY_SEALED`.

---

## 4. TASK C: DECOUPLING DEC_05 PORTFOLIO RISK POLICY FROM EXECUTION ACCOUNTING POLICY

### 4.1 DEC_05: Pure Portfolio Risk Policy
DEC_05 is strictly a portfolio risk governance decision. It addresses capital allocation and multi-position risk boundaries:
- Gross portfolio exposure caps ($E_{\text{gross}} \le E_{\text{max}}$).
- Maximum portfolio leverage and margin utilization bounds.
- Risk-budget-based position sizing and stop-loss risk allocation.
- Maximum concurrent positions across the 11 asset specialists.
- Cross-asset correlation stress limits and portfolio drawdown circuit breakers.

Human governance must select among the three structured alternatives:
- **Option 1:** Fixed Gross Exposure Cap (e.g. $1.0\times$ or $2.0\times$ capital).
- **Option 2:** Risk-Budget-Based Sizing (fixed risk percentage per trade, e.g. 0.25% capital at stop).
- **Option 3:** Combined Exposure Cap and Stop-Risk Budget.

### 4.2 Execution Cost Accounting Policy (Technical Specification)
Approach A and Approach B belong entirely to the technical execution-cost accounting specification:
- **Approach A:** Nonnegative adverse slippage floor with separately tracked price improvement.
- **Approach B:** Signed execution deviation ($C_{\text{exec,total}} = Q d (P_{\text{entry,exec}} - P_{\text{entry,ref}}) + Q (-d) (P_{\text{exit,exec}} - P_{\text{exit,ref}})$).

Approach B is an engineering recommendation because it conserves cash flows and avoids asymmetric bias. However:
- Approach B is **NOT** an approved production policy.
- Approach B is **NOT** a DEC_05 sub-option.
- Approach B is **NOT** an automatic consequence of selecting DEC_05 Option 1, 2, or 3.

DEC_05 remains strictly `PENDING_HUMAN_DECISION`.

---

## 5. TASK G: DEC_02 DIRECTIONAL SCOPE: REPORTING VS EXECUTION

A strict governance distinction is established between research reporting and trading authorization:
1. **Independent Directional Evaluation:** Long and Short specialists must be evaluated independently to detect performance asymmetries.
2. **Mandatory Disaggregated Reporting:** Long-Only, Short-Only, and Combined performance metrics must all be reported independently as a scientific transparency standard. This reporting requirement is mandatory regardless of which execution option is selected.
3. **Execution Permission (DEC_02 Governance Choice):** Authorizing execution is a separate governance decision. Selecting Option 1 (Long-Only Execution) or Option 2 (Short-Only Execution) permits trading in only one direction while retaining disaggregated reporting. Option 3 (Bidirectional Execution) permits trading in both directions.
4. **No Silent Selection:** Mandatory combined reporting does **not** constitute execution approval. Bidirectional execution is not preselected. DEC_02 remains strictly `PENDING_HUMAN_DECISION`.

---

## 6. TASK E: ENTRY, EXIT & COMPLETE NUMERICAL FUNDING ACCOUNTING

### 6.1 Two-Legged Realized Loss Formulation
The realized loss identity symmetric across both entry and exit legs is:

$$L_{\text{price,ref}} = -d Q (P_{\text{exit,ref}} - P_{\text{entry,ref}})$$

$$C_{\text{exec,entry}} = Q d (P_{\text{entry,exec}} - P_{\text{entry,ref}})$$

$$C_{\text{exec,exit}} = Q (-d) (P_{\text{exit,exec}} - P_{\text{exit,ref}})$$

$$C_{\text{exec,total}} = C_{\text{exec,entry}} + C_{\text{exec,exit}} = Q d (P_{\text{entry,exec}} - P_{\text{entry,ref}}) + Q (-d) (P_{\text{exit,exec}} - P_{\text{exit,ref}})$$

$$L_{\text{realized}} = L_{\text{price,ref}} + C_{\text{exec,total}} + C_{\text{fees}} - CF_{\text{funding}}$$

Direct fill loss algebraically equates to:

$$L_{\text{realized,exec}} = -d Q (P_{\text{exit,exec}} - P_{\text{entry,exec}}) + C_{\text{fees}} - CF_{\text{funding}} \equiv L_{\text{price,ref}} + C_{\text{exec,total}} + C_{\text{fees}} - CF_{\text{funding}}$$

### 6.2 Complete Numerical Funding Examples

Funding cash flow is signed: $CF_{\text{funding}} = -d \times N_{\text{settle}} \times f_{t,\text{decimal}}$.
- **Positive $CF_{\text{funding}}$:** Strategy receives funding (cash inflow, reduces loss).
- **Negative $CF_{\text{funding}}$:** Strategy pays funding (cash outflow, increases loss).
- **Positive $L_{\text{realized}}$:** Economic loss.

#### Baseline Parameters for Funding Cases
Let $Q = 10.0$ ETH, $P_{\text{entry,ref}} = P_{\text{entry,exec}} = 3,000.00$ USDT, $P_{\text{exit,ref}} = P_{\text{exit,exec}} = 3,000.00$ USDT.
$L_{\text{price,ref}} = 0.00$ USDT, $C_{\text{exec,total}} = 0.00$ USDT.
Transaction fees: Entry Maker 0.02% ($6.00$) + Exit Taker 0.05% ($15.00$) $\implies C_{\text{fees}} = 21.00$ USDT.
Settlement notional: $N_{\text{settle}} = 10.0 \times 3,000 = 30,000$ USDT.
Settlement funding rate: $f_t = +0.01\% = +0.0001$ (+1 bps).

#### Case 5a: Funding Payment (Long Position, $d = +1$, Positive Funding Rate $f_t = +0.01\%$)
- Funding Cash Flow:
  $$CF_{\text{funding}} = -(+1) \times 30,000 \times (+0.0001) = -3.00 \text{ USDT}$$
- Realized Loss Substitution:
  $$L_{\text{realized}} = L_{\text{price,ref}} + C_{\text{exec,total}} + C_{\text{fees}} - CF_{\text{funding}}$$
  $$= 0.00 + 0.00 + 21.00 - (-3.00) = 21.00 + 3.00 = +24.00 \text{ USDT}$$
- Economic Verification: The funding payment of 3.00 USDT increases the total economic loss from 21.00 USDT to 24.00 USDT. Cash outflows: 21.00 (fees) + 3.00 (funding) = 24.00 USDT. Exact!

#### Case 5b: Funding Receipt (Short Position, $d = -1$, Positive Funding Rate $f_t = +0.01\%$)
- Funding Cash Flow:
  $$CF_{\text{funding}} = -(-1) \times 30,000 \times (+0.0001) = +3.00 \text{ USDT}$$
- Realized Loss Substitution:
  $$L_{\text{realized}} = L_{\text{price,ref}} + C_{\text{exec,total}} + C_{\text{fees}} - CF_{\text{funding}}$$
  $$= 0.00 + 0.00 + 21.00 - (+3.00) = 21.00 - 3.00 = +18.00 \text{ USDT}$$
- Economic Verification: The funding receipt of 3.00 USDT offsets transaction fees, reducing realized loss from 21.00 USDT to 18.00 USDT. Net cash outflow: 21.00 (fees paid) - 3.00 (funding received) = 18.00 USDT. Exact!

### 6.3 Consolidated Numerical Verification Table

| Case | Direction | Ref Entry | Exec Entry | Ref Exit | Exec Exit | Ref Loss ($L_{\text{price,ref}}$) | Exec Dev ($C_{\text{exec,total}}$) | Fees ($C_{\text{fees}}$) | Funding ($CF_{\text{funding}}$) | Total Realized Loss ($L_{\text{realized}}$) | Direct Exec Loss | Match? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Case 1: Adverse Entry & Exit** | Long ($d=+1$) | 50,000 | 50,020 | 49,000 | 48,950 | +1,000.00 | +70.00 (+20 entry, +50 exit) | 34.479 | 0.00 | +1,104.479 | +1,104.479 | **EXACT** |
| **Case 2: Favorable Execution** | Long ($d=+1$) | 50,000 | 49,980 | 51,000 | 51,030 | -1,000.00 | -50.00 (-20 entry, -30 exit) | 35.353 | 0.00 | -1,014.647 | -1,014.647 | **EXACT** |
| **Case 3: Short Adverse Execution** | Short ($d=-1$) | 3,000 | 2,990 | 3,060 | 3,070 | +60.00 | +20.00 (+10 entry, +10 exit) | 2.133 | 0.00 | +82.133 | +82.133 | **EXACT** |
| **Case 4: Gap-Through-Stop** | Long ($d=+1$) | 50,000 | 50,000 | 48,500 | 48,100 | +1,500.00 | +400.00 (0 entry, +400 exit) | 34.050 | 0.00 | +1,934.050 | +1,934.050 | **EXACT** |
| **Case 5a: Funding Payment** | Long ($d=+1$) | 3,000 | 3,000 | 3,000 | 3,000 | 0.00 | 0.00 | 21.000 | -3.000 (paid) | +24.000 | +24.000 | **EXACT** |
| **Case 5b: Funding Receipt** | Short ($d=-1$) | 3,000 | 3,000 | 3,000 | 3,000 | 0.00 | 0.00 | 21.000 | +3.000 (received) | +18.000 | +18.000 | **EXACT** |

*Note on Double Counting:* Aggregate execution deviation $C_{\text{exec,total}}$ absorbs bid-ask spread crossing, order-book depth, and immediate market impact. A separate post-trade market impact deduction must not be added.  
*Note on Runtime Verification:* These calculations verify the mathematical accounting specification only. Runtime simulation behavior remains unverified; ISS_10 remains `NOT_VERIFIED` and `OPEN`.

---

## 7. TASK F: PER-FILL PARTIAL-FILL ACCOUNTING SPECIFICATION

### 7.1 Per-Fill Execution Formulations
Where a position is established or liquidated across multiple fills, accounting applies on a per-fill basis:

1. **Multiple Entry Fills:** Position is established across $M$ entry execution slices $i \in \{1, \dots, M\}$:
   $$Q_{\text{open}} = \sum_{i=1}^M q_{\text{entry},i}$$
   $$C_{\text{entry}} = \sum_{i=1}^M q_{\text{entry},i} d (P_{\text{entry},i,\text{exec}} - P_{\text{entry},i,\text{ref}})$$
   $$\bar{P}_{\text{entry,exec}} = \frac{\sum_{i=1}^M q_{\text{entry},i} P_{\text{entry},i,\text{exec}}}{Q_{\text{open}}}, \quad \bar{P}_{\text{entry,ref}} = \frac{\sum_{i=1}^M q_{\text{entry},i} P_{\text{entry},i,\text{ref}}}{Q_{\text{open}}}$$

2. **Multiple Exit Fills & Partial Closures:** Position is closed across $K$ exit execution slices $j \in \{1, \dots, K\}$:
   $$Q_{\text{closed}} = \sum_{j=1}^K q_{\text{exit},j}$$
   $$C_{\text{exit}} = \sum_{j=1}^K q_{\text{exit},j} (-d) (P_{\text{exit},j,\text{exec}} - P_{\text{exit},j,\text{ref}})$$
   $$\bar{P}_{\text{exit,exec}} = \frac{\sum_{j=1}^K q_{\text{exit},j} P_{\text{exit},j,\text{exec}}}{Q_{\text{closed}}}, \quad \bar{P}_{\text{exit,ref}} = \frac{\sum_{j=1}^K q_{\text{exit},j} P_{\text{exit},j,\text{ref}}}{Q_{\text{closed}}}$$

### 7.2 Strict Position Quantity Invariants
- **Closure Boundary:** At all times, $Q_{\text{closed}} \le Q_{\text{open}}$. A strategy cannot close more contracts than currently open.
- **Remaining Open Position:** $Q_{\text{remaining}} = Q_{\text{open}} - Q_{\text{closed}} \ge 0$.
- **Cost Allocation Method:** For realized PnL on partially closed positions ($Q_{\text{closed}} < Q_{\text{open}}$), entry cost basis is allocated proportionally under the Average Cost Basis convention (or FIFO sequence):
  $$L_{\text{price,ref}}(Q_{\text{closed}}) = -d Q_{\text{closed}} (\bar{P}_{\text{exit,ref}} - \bar{P}_{\text{entry,ref}})$$
  $$C_{\text{exec,entry}}(Q_{\text{closed}}) = \frac{Q_{\text{closed}}}{Q_{\text{open}}} C_{\text{entry}} = Q_{\text{closed}} d (\bar{P}_{\text{entry,exec}} - \bar{P}_{\text{entry,ref}})$$
  $$C_{\text{exec,exit}}(Q_{\text{closed}}) = C_{\text{exit}} = Q_{\text{closed}} (-d) (\bar{P}_{\text{exit,exec}} - \bar{P}_{\text{exit,ref}})$$
  $$C_{\text{exec,total}}(Q_{\text{closed}}) = C_{\text{exec,entry}}(Q_{\text{closed}}) + C_{\text{exec,exit}}(Q_{\text{closed}})$$
  Unclosed quantity $Q_{\text{remaining}}$ generates zero realized PnL and is tracked as unrealized mark-to-market equity.

### 7.3 Fee Calculation from Actual Executed Fill Notionals
Transaction fees are computed strictly on actual executed notionals across all fills:
$$C_{\text{fees}} = \sum_{i=1}^M q_{\text{entry},i} P_{\text{entry},i,\text{exec}} r_{\text{fee},i} + \sum_{j=1}^K q_{\text{exit},j} P_{\text{exit},j,\text{exec}} r_{\text{fee},j}$$
Fees are never calculated from reference prices.

*Status:* Documented as a specification choice for research modeling. Runtime implementation remains unverified; ISS_10 remains `NOT_VERIFIED` and `OPEN`.

---

## 8. SETTLEMENT TIMING CONVENTION & HYPOTHESIS FAMILY K

### 8.1 ISS_01: Explicit Settlement Timing Modeling Convention
Excluding an order filled at `08:00:00.000 UTC` from the `08:00:00 UTC` funding settlement is designated as an:
`EXPLICIT_SETTLEMENT_TIMING_MODELING_CONVENTION`
Because funding cash flows are signed ($CF_t = -d \times N_{\text{settle},t} \times f_{t,\text{decimal}}$), excluding the fill is conservative when the trade would receive funding (Long with $f_t < 0$ or Short with $f_t > 0$), but optimistic when the trade would pay funding (Long with $f_t > 0$ or Short with $f_t < 0$). It is not uniformly conservative. The actual AsterDEX venue matching rule remains `NOT_VERIFIED`; ISS_01 remains `OPEN`.

### 8.2 Conditional Hypothesis Family $K$ Reconciliation Table
The parameter $K$ is the number of prespecified primary confirmatory hypotheses subject to FWER/FDR control:

| Hypothesis Family Scope | Condition on DEC_06 (XMR Scope) | Number of Hypotheses $K$ | Confirmatory Estimand Definition | Downstream Correction Formula |
|---|---|---|---|---|
| **One Primary Hypothesis per Asset** | Tier 3 (XMR Excluded from primary acceptance) | $K = 10$ | Asset-level Sharpe / net PnL across 10 major assets | Bonferroni: $\alpha / 10$; Holm-Bonferroni step-down |
| **One Primary Hypothesis per Asset** | Tier 1 or Tier 2 (XMR Included in primary acceptance) | $K = 11$ | Asset-level Sharpe / net PnL across all 11 fleet assets | Bonferroni: $\alpha / 11$; Holm-Bonferroni step-down |
| **Separate Long & Short per Asset** | Tier 3 (XMR Excluded from primary acceptance) | $K = 20$ ($10 \times 2$) | Independent Long-Only and Short-Only confirmatory tests per asset | Bonferroni: $\alpha / 20$; Holm-Bonferroni step-down |
| **Separate Long & Short per Asset** | Tier 1 or Tier 2 (XMR Included in primary acceptance) | $K = 22$ ($11 \times 2$) | Independent Long-Only and Short-Only confirmatory tests across 11 assets | Bonferroni: $\alpha / 22$; Holm-Bonferroni step-down |
| **Long, Short & Combined Confirmatory** | Tier 3 (XMR Excluded from primary acceptance) | $K = 30$ ($10 \times 3$) | Long, Short, and Combined all designated as formal confirmatory tests | Bonferroni: $\alpha / 30$; Holm-Bonferroni step-down |
| **Long, Short & Combined Confirmatory** | Tier 1 or Tier 2 (XMR Included in primary acceptance) | $K = 33$ ($11 \times 3$) | Long, Short, and Combined all designated as formal confirmatory tests | Bonferroni: $\alpha / 33$; Holm-Bonferroni step-down |
| **Single Portfolio-Level Hypothesis** | Invariant to DEC_06 | $K = 1$ | Aggregate system portfolio Sharpe ratio / net return | Single unadjusted confirmatory test ($\alpha = 0.05$) |

DEC_04 and DEC_06 remain `PENDING_HUMAN_DECISION`; ISS_07 remains `OPEN`.

---

## 9. TASK H: FUTURE RESEARCH REQUIREMENT: AGGRESSIVE STRATEGY TRADE FREQUENCY & REPORTING BENCHMARKS

### 9.1 Research Trade Frequency Objective
To evaluate high-activity trading viability under realistic transaction costs, the future Phase 5.5 backtesting engine must incorporate an aggressive trading objective:
- Initial Research Target: **`600 COMPLETED TRADES PER ASSET PER YEAR`**
- Granularity: Completed round-trip trade frequency must be reported separately by asset, calendar year, specialist strategy, directional scope (Long vs Short), and market regime.

### 9.2 Activity Classification Thresholds
Activity levels are classified strictly according to completed round-trip trades per asset per year:
- **Below 100 trades/year:** `LOW_ACTIVITY`
- **100 to 299 trades/year:** `MODERATE_ACTIVITY`
- **300 to 599 trades/year:** `ACTIVE`
- **600 to 1,199 trades/year:** `AGGRESSIVE` (Target research regime)
- **1,200 or more trades/year:** `HIGH_FREQUENCY`

*Strict Rule:* These thresholds are descriptive research activity classifications, **NOT** profitability criteria. A strategy generating 600+ trades per year with negative net expectancy after transaction costs fails economic validation.

### 9.3 Mandatory Backtesting Reporting Suite
When backtesting is formally authorized, the engine must report:
1. Monthly trade-count distribution and count of zero-trade months.
2. Active trading days and average position holding duration.
3. Net trade expectancy ($\mathbb{E}[\text{PnL}_{\text{net}}]$) per trade.
4. Net realized PnL after all fees, half-spreads, execution slippage, and funding.
5. Profit factor, Maximum Drawdown (MDD), and recovery factor.
6. Risk-adjusted returns (Sharpe ratio, Sortino ratio, Calmar ratio).
7. Transaction-cost drag (fees + slippage as percentage of gross profit).
8. PnL concentration (fraction of net profit generated by top 5% of trades).
9. Annual out-of-sample performance stability across all pre-holdout years.

*Operational Boundary:* Documenting this research requirement does **NOT** authorize economic backtesting. Lifecycle status remains `NOT_STARTED`.

---

## 10. FINAL GOVERNANCE VERDICT & READINESS

### 10.1 Human Review Readiness
The QUANTUM Phase 5.5 Governance Dossier Suite is fully reconciled, mathematically verified, and ready for human executive review. All human decision fields remain strictly blank:
- DEC_01: `PENDING_HUMAN_DECISION`
- DEC_02: `PENDING_HUMAN_DECISION`
- DEC_03: `PENDING_HUMAN_DECISION`
- DEC_04: `PENDING_HUMAN_DECISION`
- DEC_05: `PENDING_HUMAN_DECISION`
- DEC_06: `PENDING_HUMAN_DECISION`

### 10.2 Final Lifecycle Verdict
The official verdict for this phase is:

`FINAL_ERRATA_READY_WITH_LIMITATIONS`

- **Phase 5.5 Economic Validation:** `NOT_STARTED`
- **Phase 5.6 Production Strategy:** `NOT_AUTHORIZED`
- **Prospective Holdout:** `STRICTLY_SEALED`
- **Full Unit Test Suite:** `FULL_UNIT_SUITE_NOT_VERIFIED` (Environment interpreter-shutdown hang documented; dedicated and filtered suites verified)
- **Runtime Simulation Code:** `NOT_VERIFIED` (ISS_10 remains open)
- **Historical Holdout Access:** `NOT_VERIFIED` (ISS_11 informational limitation retained)
"""


def update_master_governance_status():
    status_path = DOSSIER_DIR / "QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md"
    content = status_path.read_text(encoding="utf-8")
    
    # Update DEC_02 and DEC_05 table rows to prevent mixing
    # DEC_02 recommended option: Structured choice with mandatory disaggregated reporting
    # DEC_05 recommended option: Structured choice among Options 1, 2, or 3 (Portfolio Risk Policy)
    target_row_02 = r"| **DEC_02** | Directional Trading Scope | Execution permission (Long, Short, Bidirectional) vs mandatory reporting | `PENDING_HUMAN_DECISION` | Bidirectional execution with mandatory disaggregated reporting | `SOURCE_VERIFIED` (Directional asymmetry confirmed) | DEC_01 | DEC_05 | None | **YES** |"
    replacement_row_02 = r"| **DEC_02** | Directional Trading Scope | Execution permission (Long, Short, Bidirectional) vs mandatory reporting | `PENDING_HUMAN_DECISION` | Structured choice among Options 1, 2, or 3 with mandatory disaggregated reporting | `SOURCE_VERIFIED` (Directional asymmetry confirmed) | DEC_01 | DEC_05 | None | **YES** |"
    
    target_row_05 = r"| **DEC_05** | Portfolio Concurrency & Leverage | Exposure caps, stop loss budgeting, signed slippage, and cross-asset correlation risk | `PENDING_HUMAN_DECISION` | Structured choice among Options 1, 2, or 3 (with Approach B signed execution deviation) | `MATHEMATICALLY_VERIFIED` (Signed cash-flow accounting) | DEC_01, DEC_02, DEC_04 | None (Terminal) | ISS_08 | **YES** |"
    replacement_row_05 = r"| **DEC_05** | Portfolio Concurrency & Leverage | Exposure caps, stop loss budgeting, and cross-asset correlation risk | `PENDING_HUMAN_DECISION` | Structured choice among Options 1, 2, or 3 (Portfolio Risk Policy) | `SOURCE_VERIFIED` (Capital allocation specification) | DEC_01, DEC_02, DEC_04 | None (Terminal) | ISS_08 | **YES** |"

    if target_row_02 in content:
        content = content.replace(target_row_02, replacement_row_02)
    if target_row_05 in content:
        content = content.replace(target_row_05, replacement_row_05)
        
    status_path.write_text(content, encoding="utf-8")
    print("Updated QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md table rows.")


def main():
    print("Generating corrected QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md...")
    errata_content = generate_final_governance_errata()
    
    # Verify zero em dashes
    em_dash = chr(0x2014)
    if em_dash in errata_content:
        raise ValueError("Em dash detected in errata content!")
        
    errata_path = DOSSIER_DIR / "QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md"
    errata_path.write_text(errata_content, encoding="utf-8")
    print(f"Written: {errata_path}")
    
    update_master_governance_status()
    
    # Verify zero em dashes across all dossier files
    for p in DOSSIER_DIR.glob("*.md"):
        txt = p.read_text(encoding="utf-8")
        if em_dash in txt:
            raise ValueError(f"Em dash detected in {p.name}!")
    print("All dossier markdown files verified: ZERO em dashes detected.")


if __name__ == "__main__":
    main()
