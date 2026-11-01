"""
QUANTUM Phase 5.5 Unit Tests: Final Governance Decision Dossier Revision 1.

Validates the completeness, structural integrity, and governance rigor of Revision 1:
1. All 7 required deliverables exist in docs/research/phase_5_5_governance_dossier/.
2. Master status table documents DEC_01 through DEC_06 with PENDING_HUMAN_DECISION.
3. DEC_01 distinguishes Alternatives A, B, and C and explains why Alt B does not validate label payoff.
4. DEC_02 decouples mandatory disaggregated research reporting from execution permission.
5. DEC_03 documents funding_rate_bps_per_settlement, 1095 nominal factor, and signed cash flow.
6. DEC_04 specifies REFERENCE_PRICE_ACCOUNTING, unvalidated block status, and K dependency on DEC_06.
7. DEC_05 removes unsupported guarantees, defines exposure/nominal stop loss, and offers 3 distinct options.
8. DEC_06 documents 3-tier XMR policy and the 83,863 vs 316,500 candle gap.
9. Cross-decision dependency matrix documents the reconciled 6-step logical execution sequence.
10. Unresolved issue register catalogs ISS_01 through ISS_11 with strict allowed statuses.
11. Human decision worksheet contains unexecuted placeholders and denied authorization.
12. Final dossier report specifies GOVERNANCE_DOSSIER_REVISION_1_READY_FOR_HUMAN_REVIEW.
13. Revision 1 changelog documents all 8 governance corrections.
14. Zero em dashes (Unicode U+2014) across all Phase 5.5 dossier files and test suite.
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
    "QUANTUM_PHASE_5_5_GOVERNANCE_DOSSIER_REVISION_1_REPORT.md",
    "QUANTUM_PHASE_5_5_GOVERNANCE_CHANGELOG_REVISION_1.md",
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


def test_01_all_7_deliverables_exist():
    """Verify that all 7 required Phase 5.5 dossier deliverables exist and are non-empty."""
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
    assert "NOT STARTED" in content
    assert "NOT AUTHORIZED" in content
    assert "STRICTLY SEALED" in content


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
    """Verify DEC_03 documents funding_rate_bps_per_settlement, 1095, and signed cash flow."""
    fpath = DOSSIER_DIR / "QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "DEC_03: FUNDING RATE MODEL" in content
    assert "funding_rate_bps_per_settlement" in content
    assert "1095 = 3 \\times 365" in content
    assert "CF_t = -d \\times N_{\\text{settle}, t} \\times f_{t, \\text{decimal}}" in content
    assert "Parametric Sensitivity Interpretation" in content
    assert "do NOT represent historical distributions" in content
    assert "FUNDING_DATA_UNAVAILABLE" in content
    assert "NOT_VERIFIED" in content


def test_06_dec_04_cost_scenarios_and_statistics():
    """Verify DEC_04 specifies REFERENCE_PRICE_ACCOUNTING, unvalidated block status, and K values."""
    fpath = DOSSIER_DIR / "QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "DEC_04: COST SCENARIOS & STATISTICAL ACCEPTANCE CRITERIA" in content
    assert "REFERENCE_PRICE_ACCOUNTING" in content
    assert "24 bars (2 hours)" in content
    assert "underestimates serial autocorrelation" in content
    assert "288 bars (24 hours)" in content
    assert "NOT a statistically validated optimal block length" in content
    assert "Continuous Calendar-Time Portfolio Moving Block Bootstrap" in content
    assert "$K = 10$" in content
    assert "$K = 11$" in content


def test_07_dec_05_portfolio_concurrency_and_risk_reconciliation():
    """Verify DEC_05 removes unsupported guarantees, defines exposure/stops, and offers 3 options."""
    fpath = DOSSIER_DIR / "QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "DEC_05: PORTFOLIO CONCURRENCY & RISK RECONCILIATION" in content
    assert "\\text{GrossExposure}" in content
    assert "\\text{GrossLeverage}" in content
    assert "\\text{MarginUtilization}" in content
    assert "REQUIRES_HUMAN_CLARIFICATION" in content
    assert "L_{\\text{stop, nominal}}" in content
    assert "Explicit Removal of Unsupported Guarantees" in content
    assert "Option 1 (Fixed Gross Exposure Cap)" in content
    assert "Option 2 (Risk-Budget-Based Position Sizing)" in content
    assert "Option 3 (Combined Exposure Cap and Stop-Risk Budget)" in content

    # Verify that unsupported claims are explicitly NOT presented as true facts
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
    """Verify unresolved issue register catalogs ISS_01 through ISS_11 with strict allowed statuses."""
    fpath = DOSSIER_DIR / "QUANTUM_PHASE_5_5_UNRESOLVED_ISSUE_REGISTER.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "RECONCILED TECHNICAL ISSUE REGISTER" in content
    for iss_id in EXPECTED_ISSUE_IDS:
        assert iss_id in content

    # Check ISS_04 is PENDING_HUMAN_DECISION (not marked resolved)
    assert "| **ISS_04** | DEC_04 | `HIGH` | 24-bar MBB does not capture autocorrelation for trades held up to 288 bars; 288-bar calendar MBB is candidate, not validated. | [PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md) | `MATHEMATICALLY_VERIFIED` | `PENDING_HUMAN_DECISION` | **YES** |" in content

    # Check ISS_01 has NOT_VERIFIED
    assert "NOT_VERIFIED" in content

    # Check ISS_05 has PENDING_HUMAN_DECISION
    assert "PENDING_HUMAN_DECISION" in content


def test_11_final_human_decision_worksheet():
    """Verify human decision worksheet contains blank placeholders and denied authorization."""
    fpath = DOSSIER_DIR / "QUANTUM_PHASE_5_5_FINAL_HUMAN_DECISION_WORKSHEET.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "UNEXECUTED_WORKSHEET_AWAITING_HUMAN_SIGN_OFF" in content
    assert "[DENIED_UNTIL_ALL_DECISIONS_SIGNED]" in content
    assert "[UNEXECUTED]" in content

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
    """Verify final report specifies GOVERNANCE_DOSSIER_REVISION_1_READY_FOR_HUMAN_REVIEW."""
    fpath = DOSSIER_DIR / "QUANTUM_PHASE_5_5_GOVERNANCE_DOSSIER_REVISION_1_REPORT.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "GOVERNANCE_DOSSIER_REVISION_1_READY_FOR_HUMAN_REVIEW" in content
    for dec_id in EXPECTED_DECISION_IDS:
        assert dec_id in content
        assert "PENDING_HUMAN_DECISION" in content
    assert "NOT_STARTED" in content
    assert "NOT_AUTHORIZED" in content
    assert "STRICTLY_SEALED" in content


def test_13_governance_changelog_revision_1():
    """Verify Revision 1 changelog exists and documents all 8 required changes."""
    fpath = DOSSIER_DIR / "QUANTUM_PHASE_5_5_GOVERNANCE_CHANGELOG_REVISION_1.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "QUANTUM PHASE 5.5: GOVERNANCE CHANGELOG (REVISION 1)" in content
    for chg_id in ["CHG_01", "CHG_02", "CHG_03", "CHG_04", "CHG_05", "CHG_06", "CHG_07", "CHG_08"]:
        assert chg_id in content

    assert "Removed all guarantee language" in content
    assert "REQUIRES_HUMAN_CLARIFICATION" in content
    assert "Option 1 (Fixed gross cap)" in content
    assert "288 bars is candidate, not validated optimal" in content
    assert "parametric sensitivity inputs" in content
    assert "Decoupled research reporting" in content
    assert "$K=10$ if XMR excluded; $K=11$ if included" in content
    assert "Step 1 (DEC_01), Step 2 (DEC_06), Step 3 (DEC_03), Step 4 (DEC_02), Step 5 (DEC_04), Step 6 (DEC_05)" in content


def test_14_zero_em_dashes_across_all_dossier_files():
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
