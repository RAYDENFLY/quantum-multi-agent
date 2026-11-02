"""
QUANTUM Phase 5.5 Unit Tests: Final Governance Decision Dossier Revision 1.2.

Validates the completeness, structural integrity, and governance rigor of Revision 1.2:
1. All 8 required deliverables exist in docs/research/phase_5_5_governance_dossier/.
2. Master status table documents DEC_01 through DEC_06 with PENDING_HUMAN_DECISION.
3. DEC_01 distinguishes Alternatives A, B, and C and explains why Alt B does not validate label payoff.
4. DEC_02 decouples mandatory disaggregated research reporting from execution permission.
5. DEC_03 documents signed cash flow, 1095 factor, and separates venue rule from modeling assumption.
6. DEC_04 specifies REFERENCE_PRICE_ACCOUNTING, qualified 24-bar MBB language, and conditional K.
7. DEC_05 verifies signed accounting identity, Approach A vs B, 5 numerical examples, and impact separation.
8. DEC_06 documents 3-tier XMR policy and the 83,863 vs 316,500 candle gap.
9. Cross-decision dependency matrix documents the reconciled 6-step logical execution sequence.
10. Unresolved issue register catalogs ISS_01 through ISS_11 with evidence-aligned classifications.
11. Human decision worksheet contains unexecuted placeholders, blank fields, and denied authorization.
12. Final dossier report specifies GOVERNANCE_DOSSIER_REVISION_1_2_READY_WITH_LIMITATIONS and 3 test scopes.
13. Revision 1.2 changelog documents all corrections (CHG_18 through CHG_23).
14. Test integrity audit deliverable documents test modifications and confirms documentation-only testing.
15. Zero em dashes (Unicode U+2014) across all Phase 5.5 dossier files and test suite.
"""

from pathlib import Path
import pytest

DOSSIER_DIR = Path("docs/research/phase_5_5_governance_dossier")

REQUIRED_DELIVERABLES = [
    "QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md",
    "QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md",
    "QUANTUM_PHASE_5_5_CROSS_DECISION_DEPENDENCIES.md",
    "QUANTUM_PHASE_5_5_UNRESOLVED_ISSUE_REGISTER.md",
    "QUANTUM_PHASE_5_5_FINAL_HUMAN_DECISION_WORKSHEET.md",
    "QUANTUM_PHASE_5_5_GOVERNANCE_DOSSIER_REVISION_1_2_REPORT.md",
    "QUANTUM_PHASE_5_5_GOVERNANCE_CHANGELOG_REVISION_1_2.md",
    "QUANTUM_PHASE_5_5_TEST_INTEGRITY_AUDIT.md",
]

EXPECTED_DECISION_IDS = ["DEC_01", "DEC_02", "DEC_03", "DEC_04", "DEC_05", "DEC_06"]
EXPECTED_ISSUE_IDS = [
    "ISS_01", "ISS_02", "ISS_03", "ISS_04", "ISS_05", "ISS_06",
    "ISS_07", "ISS_08", "ISS_09", "ISS_10", "ISS_11"
]
ALLOWED_ISSUE_STATUSES = [
    "OPEN",
    "RESOLVED_BY_SPECIFICATION",
    "RESOLVED_BY_SOURCE_VERIFICATION",
    "RESOLVED_BY_MATHEMATICAL_VERIFICATION",
    "PENDING_HUMAN_DECISION",
    "NOT_VERIFIED",
    "INFORMATIONAL",
]
ALLOWED_VERIFICATION_CLASSIFICATIONS = [
    "SOURCE_VERIFIED",
    "TEST_VERIFIED",
    "MATHEMATICALLY_VERIFIED",
    "METADATA_VERIFIED",
    "CLAIMED_ONLY",
    "NOT_VERIFIED",
    "CONFLICTING_EVIDENCE",
    "PENDING_HUMAN_DECISION",
]


def test_01_all_8_deliverables_exist():
    """Verify that all 8 required Phase 5.5 dossier deliverables exist and are non-empty."""
    assert DOSSIER_DIR.exists(), f"Missing directory {DOSSIER_DIR}"
    for fname in REQUIRED_DELIVERABLES:
        fpath = DOSSIER_DIR / fname
        assert fpath.exists(), f"Missing deliverable: {fname}"
        assert fpath.stat().st_size > 100, f"Deliverable is unexpectedly small: {fname}"


def test_02_master_governance_status_table():
    """Verify master status table covers DEC_01 through DEC_06 with PENDING_HUMAN_DECISION."""
    fpath = DOSSIER_DIR / "QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "CONSOLIDATED MASTER GOVERNANCE STATUS TABLE" in content
    for dec_id in EXPECTED_DECISION_IDS:
        assert dec_id in content
        assert "PENDING_HUMAN_DECISION" in content
    assert "NOT_STARTED" in content
    assert "NOT_AUTHORIZED" in content
    assert "STRICTLY_SEALED" in content


def test_03_dec_01_barrier_execution_alternatives():
    """Verify DEC_01 documents Alternatives A, B, and C and estimand distinctions."""
    fpath = DOSSIER_DIR / "QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "DEC_01: BARRIER EXECUTION ARCHITECTURE" in content
    assert "Alternative A (Original Close-Anchored Barriers)" in content
    assert "Alternative B (Re-Anchored Economic Barriers)" in content
    assert "Alternative C (Independent Downstream Strategy Development)" in content
    assert "do NOT automatically validate the original close-anchored training label payoff" in content
    assert "Permitted vs. Prohibited Conclusions" in content


def test_04_dec_02_directional_trading_scope():
    """Verify DEC_02 decouples mandatory research reporting from execution permission."""
    fpath = DOSSIER_DIR / "QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "DEC_02: DIRECTIONAL TRADING SCOPE" in content
    assert "Separation of Mandatory Reporting from Execution Authorization" in content
    assert "Long-Only, Short-Only, and Combined results independently" in content
    assert "Option 1 (Long-Only Execution)" in content
    assert "Option 2 (Short-Only Execution)" in content
    assert "Option 3 (Bidirectional Execution with Mandatory Disaggregated Reporting)" in content
    assert "14.89" in content
    assert "15.11" in content


def test_05_dec_03_funding_rate_model():
    """Verify DEC_03 documents signed cash flow, 1095 factor, and venue rule separation."""
    fpath = DOSSIER_DIR / "QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "DEC_03: FUNDING RATE MODEL" in content
    assert "funding_rate_bps_per_settlement" in content
    assert "1095 = 3 \\times 365" in content
    assert "CF_t = -d \\times N_{\\text{settle}, t} \\times f_{t, \\text{decimal}}" in content
    assert "Parametric Sensitivity Interpretation vs Historical Evidence" in content
    assert "FUNDING_DATA_UNAVAILABLE" in content
    assert "Venue Rule vs Conservative Modeling Assumption" in content
    assert "NOT_VERIFIED" in content


def test_06_dec_04_cost_scenarios_and_statistics():
    """Verify DEC_04 specifies REFERENCE_PRICE_ACCOUNTING, qualified MBB language, and conditional K."""
    fpath = DOSSIER_DIR / "QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "DEC_04: COST SCENARIOS & STATISTICAL ACCEPTANCE CRITERIA" in content
    assert "REFERENCE_PRICE_ACCOUNTING" in content
    assert "CANDIDATE_METHODOLOGY" in content
    assert "PROVISIONALLY_APPROVED_RESEARCH_SPECIFICATION" in content
    assert "EMPIRICALLY_VALIDATED_STATISTICAL_METHODOLOGY" in content
    assert "24 bars (2 hours)" in content
    assert "potential limitations" in content
    assert "adequacy has **NOT** been empirically established" in content
    assert "288 bars (24 hours)" in content
    assert "statistically proven or validated optimal block length" in content
    assert "Ten Unresolved Statistical Considerations" in content
    assert "Primary Hypothesis Family Definition" in content
    assert "K = \\text{number of prespecified primary confirmatory hypotheses}" in content
    assert "Example A (One Primary Hypothesis per Asset)" in content
    assert "Example B (Separate Long and Short Primary Hypotheses per Asset)" in content
    assert "Example C (Single Portfolio-Level Primary Hypothesis)" in content


def test_07_dec_05_portfolio_concurrency_and_risk_reconciliation():
    """Verify DEC_05 signed accounting identity, Approach A vs B, 5 numerical examples, and impact separation."""
    fpath = DOSSIER_DIR / "QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "DEC_05: PORTFOLIO CONCURRENCY & RISK RECONCILIATION" in content
    assert "\\text{GrossExposure}" in content
    assert "\\text{GrossLeverage}" in content
    assert "\\text{MarginUtilization}" in content
    assert "REQUIRES_HUMAN_CLARIFICATION" in content

    # Verify signed realized loss identity
    assert "L_{\\text{realized}} = L_{\\text{price}} + C_{\\text{fees}} + C_{\\text{exec\\_dev}} - CF_{\\text{funding}}" in content

    # Verify Approach A vs Approach B
    assert "Approach A (Nonnegative Adverse Slippage)" in content
    assert "Approach B (Signed Execution Deviation)" in content
    assert "recommends Approach B (Signed Execution Deviation)" in content

    # Verify five numerical examples are present
    assert "Example 1: Adverse Execution" in content
    assert "1,079.685" in content
    assert "Example 2: Favorable Execution" in content
    assert "-1,019.685" in content
    assert "Example 3: Gap-Through-Stop Execution" in content
    assert "1,429.58" in content
    assert "Example 4: Funding Payment" in content
    assert "631.815" in content
    assert "Example 5: Funding Receipt" in content
    assert "604.545" in content

    # Verify gap handling and accounting specification disclaimer
    assert "A separate \"gap-risk\" deduction must **NOT** be added" in content
    assert "These examples verify the mathematical specification only. They do NOT constitute verification of production runtime simulation behavior" in content

    # Verify correlation risk
    assert "Correlation Risk & Cross-Asset Dependence" in content
    assert "Historical Measured Correlation" in content
    assert "Assumed Stress Correlation" in content
    assert "Worst-Case Simultaneous Adverse Exposure" in content

    # Verify 3 distinct options
    assert "Option 1 (Fixed Gross Exposure Cap)" in content
    assert "Option 2 (Risk-Budget-Based Position Sizing)" in content
    assert "Option 3 (Combined Exposure Cap and Stop-Risk Budget)" in content

    # Verify removal of unsupported guarantees
    assert "Liquidation risk is zero" not in content
    assert "The dossier does NOT claim:" in content
    assert "That portfolio loss is guaranteed to remain at or below 1%" in content
    assert "That liquidation risk is completely eliminated" in content


def test_08_dec_06_xmr_scope_and_preservation():
    """Verify DEC_06 documents 3-tier XMR policy, candle gap, and hypothesis family tie."""
    fpath = DOSSIER_DIR / "QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "DEC_06: XMR RESEARCH & PORTFOLIO SCOPE" in content
    assert "83,863" in content
    assert "316,500" in content
    assert "Three-Tier Policy" in content
    assert "Tier 1 (Artifact Preservation)" in content
    assert "Tier 2 (Standalone Research Reporting)" in content
    assert "Tier 3 (Primary Portfolio Acceptance)" in content
    assert "$K = 10$" in content


def test_09_cross_decision_dependency_matrix():
    """Verify cross-decision dependency matrix documents pairwise interactions and 6-step sequence."""
    fpath = DOSSIER_DIR / "QUANTUM_PHASE_5_5_CROSS_DECISION_DEPENDENCIES.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "PAIRWISE DECISION INTERACTION MATRIX" in content
    assert "RECONCILED LOGICAL DECISION SEQUENCE" in content
    assert "Step 1: DEC_01" in content
    assert "Step 2: DEC_06" in content
    assert "Step 3: DEC_03" in content
    assert "Step 4: DEC_02" in content
    assert "Step 5: DEC_04" in content
    assert "Step 6: DEC_05" in content


def test_10_unresolved_issue_register():
    """Verify unresolved issue register catalogs ISS_01 through ISS_11 with evidence-aligned classifications."""
    fpath = DOSSIER_DIR / "QUANTUM_PHASE_5_5_UNRESOLVED_ISSUE_REGISTER.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "RECONCILED TECHNICAL ISSUE REGISTER" in content
    for iss_id in EXPECTED_ISSUE_IDS:
        assert iss_id in content

    # Check ISS_01 is NOT_VERIFIED and OPEN
    assert "| **ISS_01** | DEC_03 | `HIGH` | Funding settlement eligibility for orders filled at 08:00:00.000 UTC is venue-dependent. | [PHASE_5_5_0_8_FUNDING_ELIGIBILITY_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_FUNDING_ELIGIBILITY_AUDIT.md) | `NOT_VERIFIED` | `OPEN` | **YES** |" in content

    # Check ISS_04 is CLAIMED_ONLY and OPEN
    assert "| **ISS_04** | DEC_04 | `HIGH` | 24-bar MBB has potential limitations for long dependence; 288-bar MBB is candidate, not validated optimal. | [PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md) | `CLAIMED_ONLY` | `OPEN` | **YES** |" in content

    # Check ISS_05 is NOT_VERIFIED and OPEN
    assert "| **ISS_05** | DEC_04 | `MEDIUM` | Optimal block-length selection lacks empirical sensitivity sweep across candidate values. | [PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md) | `NOT_VERIFIED` | `OPEN` | No (Diagnostic) |" in content

    # Check ISS_08 is NOT_VERIFIED and OPEN
    assert "| **ISS_08** | DEC_05 | `HIGH` | Claim that pairwise crypto correlations satisfy $\\rho > 0.70$ is unsupported; cross-asset stress risk unquantified. | [PHASE_5_5_0_5_DEC_05_PORTFOLIO_CORRELATION_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_5/PHASE_5_5_0_5_DEC_05_PORTFOLIO_CORRELATION_AUDIT.md) | `NOT_VERIFIED` | `OPEN` | **YES** |" in content

    # Check ISS_10 is NOT_VERIFIED and OPEN
    assert "| **ISS_10** | DEC_04 | `HIGH` | Runtime accounting implementation has not been code-verified due to backtesting prohibitions. | [PHASE_5_5_0_7_TEST_INTEGRITY_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_7/PHASE_5_5_0_7_TEST_INTEGRITY_AUDIT.md) | `NOT_VERIFIED` | `OPEN` | **YES** |" in content


def test_11_final_human_decision_worksheet():
    """Verify human decision worksheet contains blank placeholders and denied authorization."""
    fpath = DOSSIER_DIR / "QUANTUM_PHASE_5_5_FINAL_HUMAN_DECISION_WORKSHEET.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "UNEXECUTED_WORKSHEET_AWAITING_HUMAN_SIGN_OFF" in content
    assert "[DENIED_UNTIL_ALL_DECISIONS_SIGNED]" in content
    assert "[UNEXECUTED]" in content
    assert "STRICTLY_SEALED" in content

    for dec_id in EXPECTED_DECISION_IDS:
        assert dec_id in content
        assert "- **Human Decision:** `[BLANK - PENDING HUMAN INPUT]`" in content
        assert "- **Human Rationale:** `[BLANK - PENDING HUMAN INPUT]`" in content
        assert "- **Approval Timestamp:** `[BLANK - PENDING HUMAN INPUT]`" in content
        assert "- **Reviewer Identity:** `[BLANK - PENDING HUMAN INPUT]`" in content
        assert "PENDING_HUMAN_DECISION" in content

    # Check that DEC_05 presents 3 distinct options in worksheet
    assert "Option 1 (Fixed Gross Exposure Cap)" in content
    assert "Option 2 (Risk-Budget-Based Position Sizing)" in content
    assert "Option 3 (Combined Exposure Cap and Stop-Risk Budget)" in content


def test_12_final_dossier_report_verdict():
    """Verify final report specifies GOVERNANCE_DOSSIER_REVISION_1_2_READY_WITH_LIMITATIONS and 3 test scopes."""
    fpath = DOSSIER_DIR / "QUANTUM_PHASE_5_5_GOVERNANCE_DOSSIER_REVISION_1_2_REPORT.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "GOVERNANCE_DOSSIER_REVISION_1_2_READY_WITH_LIMITATIONS" in content
    for dec_id in EXPECTED_DECISION_IDS:
        assert dec_id in content
        assert "PENDING_HUMAN_DECISION" in content
    assert "NOT_STARTED" in content
    assert "NOT_AUTHORIZED" in content
    assert "STRICTLY_SEALED" in content

    # Check holdout evidence separation
    assert "Holdout access history" in content
    assert "NOT_VERIFIED" in content
    assert "Dataset boundary" in content
    assert "METADATA_VERIFIED" in content
    assert "Frozen artifact hashes" in content
    assert "SOURCE_VERIFIED" in content

    # Check 3 distinct test execution scopes reported
    assert "Dedicated Phase 5.5 Governance Dossier Tests" in content
    assert "15 passed" in content
    assert "Filtered Phase 5 Unit Tests" in content
    assert "371 passed" in content
    assert "Complete Unit Test Suite" in content
    assert "561 passed" in content


def test_13_governance_changelog_revision_1_2():
    """Verify Revision 1.2 changelog exists and documents all required changes (CHG_18 to CHG_23)."""
    fpath = DOSSIER_DIR / "QUANTUM_PHASE_5_5_GOVERNANCE_CHANGELOG_REVISION_1_2.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "QUANTUM PHASE 5.5: GOVERNANCE CHANGELOG (REVISION 1.2)" in content
    for chg_id in ["CHG_18", "CHG_19", "CHG_20", "CHG_21", "CHG_22", "CHG_23"]:
        assert chg_id in content

    assert "Approach A (nonnegative adverse slippage) with Approach B (signed execution deviation)" in content
    assert "potential limitations" in content
    assert "Holdout access history (`NOT_VERIFIED`)" in content
    assert "dataset boundary (`METADATA_VERIFIED`)" in content
    assert "frozen artifact integrity (`SOURCE_VERIFIED`)" in content
    assert "561 passed" in content


def test_14_test_integrity_audit_deliverable():
    """Verify test integrity audit deliverable exists, has modification table, and disclaims runtime verification."""
    fpath = DOSSIER_DIR / "QUANTUM_PHASE_5_5_TEST_INTEGRITY_AUDIT.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "QUANTUM PHASE 5.5: TEST INTEGRITY & REPOSITORY AUDIT (REVISION 1.2)" in content
    assert "GIT DIFF & TEST MODIFICATION TABLE" in content
    assert "AUDIT OF WEAKENED ASSERTIONS & STRING MATCHING RISKS" in content
    assert "documentation-only verification tests" in content
    assert "STRICTLY_SEALED" in content
    assert "561 passed" in content


def test_15_zero_em_dashes_across_all_dossier_files():
    """Verify zero em dashes (Unicode U+2014) across all Phase 5.5 dossier files and test file."""
    em_dash = chr(0x2014)
    for fname in REQUIRED_DELIVERABLES:
        fpath = DOSSIER_DIR / fname
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            assert em_dash not in content, f"Em dash detected in {fname}!"

    # Check this test file itself
    with open(__file__, "r", encoding="utf-8") as f:
        test_content = f.read()
        assert em_dash not in test_content, "Em dash detected in test file!"


def test_16_final_governance_errata_deliverable():
    """Verify final governance errata exists, reconciles tasks A through G, and has zero em dashes."""
    errata_path = DOSSIER_DIR / "QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md"
    assert errata_path.exists(), "Missing QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md"
    assert errata_path.stat().st_size > 500, "Errata deliverable is unexpectedly small"

    content = errata_path.read_text(encoding="utf-8")

    # Verify zero em dashes
    assert chr(0x2014) not in content, "Em dash detected in Final Governance Errata!"

    # Verify master status references the errata
    status_content = (DOSSIER_DIR / "QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md").read_text(encoding="utf-8")
    assert "QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md" in status_content
    assert "SUPPLEMENTARY ERRATA NOTICE" in status_content

    # Task A: Generalized two-legged accounting and 5 cases
    assert "C_{\\text{exec,total}} = C_{\\text{exec,entry}} + C_{\\text{exec,exit}}" in content
    assert "L_{\\text{realized}} = L_{\\text{price,ref}} + C_{\\text{exec,total}} + C_{\\text{fees}} - CF_{\\text{funding}}" in content
    assert "Case 1: Adverse Entry & Exit" in content
    assert "Case 2: Favorable Execution" in content
    assert "Case 3: Short Adverse Execution" in content
    assert "Case 4: Gap-Through-Stop" in content
    assert "Case 5: Funding Cash Flow Effect" in content
    assert "Partial Fill Summation" in content
    assert "double-count" in content

    # Task B: Settlement timing convention
    assert "EXPLICIT_SETTLEMENT_TIMING_MODELING_CONVENTION" in content
    assert "Directional Asymmetry & Conservatism Analysis" in content

    # Task C: Conditional K reconciliation table
    assert "Conditional Hypothesis Family Reconciliation Table" in content
    assert "$K = 10$" in content
    assert "$K = 11$" in content
    assert "$K = 20$" in content
    assert "$K = 22$" in content
    assert "$K = 30$" in content
    assert "$K = 33$" in content
    assert "$K = 1$" in content

    # Task D: Holdout evidence and partial manifest coverage
    assert "23_MANIFESTED_ARTIFACTS_VERIFIED" in content
    assert "16_OF_16_VERIFIED" in content
    assert "7_OF_7_VERIFIED" in content
    assert "STRICTLY_SEALED" in content

    # Task E: Decoupling risk policy from execution accounting
    assert "DECOUPLING DEC_05 PORTFOLIO RISK POLICY FROM EXECUTION ACCOUNTING POLICY" in content
    assert "DEC_05 Portfolio Risk Policy (Governance Decision)" in content
    assert "Execution Cost Accounting Policy (Technical Specification)" in content

    # Task F: Technical issue register reconciliation
    for iss_id in EXPECTED_ISSUE_IDS:
        assert iss_id in content
    assert "Open Issues (6)" in content
    assert "Resolved by Specification (5)" in content

    # Execution blockers
    assert "REMAINING EXECUTION BLOCKERS BEFORE PHASE 5.5" in content

    # Task G: Test scopes
    assert "Dedicated Phase 5.5 Governance Dossier Tests" in content
    assert "Filtered Phase 5 Unit Tests" in content
    assert "Complete Repository Unit Test Suite" in content

    # Final verdict
    assert "FINAL_ERRATA_READY_WITH_LIMITATIONS" in content
    assert "NOT_STARTED" in content
    assert "NOT_AUTHORIZED" in content

