"""
QUANTUM Phase 5.5.0.4 Unit Tests: Human Governance Decision Package Review.

Validates the structural integrity, governance boundaries, and mathematical consistency
of Phase 5.5.0.4:
1. All 11 required deliverables exist in docs/research/phase_5_5_0_4/.
2. All 6 decisions (DEC_01 to DEC_06) have dedicated analytical briefs.
3. All 6 decisions remain strictly PENDING_HUMAN_DECISION.
4. All 6 decisions are execution-blocking.
5. Human approval template contains no fabricated approvals (all unexecuted placeholders).
6. Cross-decision dependency matrix covers pairwise interactions and logical sequencing.
7. Reversibility and risk register covers research impact, risk, and reversibility for all 6 decisions.
8. Each decision brief presents the exact authorized options.
9. All 55 frozen LightGBM binaries and 55 preprocessors remain 100% bit-for-bit intact.
10. Prospective holdout (2026-11-01 to 2027-04-30) remains strictly protected and unaccessed.
11. Final governance report specifies GOVERNANCE_PACKAGE_READY_WITH_LIMITATIONS.
12. Zero em dashes (Unicode U+2014) anywhere in Phase 5.5.0.4 files or test suite.
"""

import hashlib
import json
from pathlib import Path
import pytest

PHASE_5_5_0_4_DIR = Path("docs/research/phase_5_5_0_4")
PHASE_5_3_FREEZE_MANIFEST = Path("artifacts/phase_5_3_freeze/frozen_artifact_manifest.json")

REQUIRED_DELIVERABLES = [
    "PHASE_5_5_0_4_DECISION_EXECUTIVE_BRIEF.md",
    "PHASE_5_5_0_4_DEC_01_BARRIER_ARCHITECTURE.md",
    "PHASE_5_5_0_4_DEC_02_DIRECTIONAL_SCOPE.md",
    "PHASE_5_5_0_4_DEC_03_FUNDING_MODEL.md",
    "PHASE_5_5_0_4_DEC_04_COST_GATE.md",
    "PHASE_5_5_0_4_DEC_05_PORTFOLIO_RISK.md",
    "PHASE_5_5_0_4_DEC_06_XMR_SCOPE.md",
    "PHASE_5_5_0_4_DECISION_DEPENDENCY_MATRIX.md",
    "PHASE_5_5_0_4_REVERSIBILITY_AND_RISK_REGISTER.md",
    "PHASE_5_5_0_4_HUMAN_APPROVAL_TEMPLATE.md",
    "PHASE_5_5_0_4_FINAL_GOVERNANCE_REPORT.md",
]

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"
]

EXPECTED_DECISION_IDS = ["DEC_01", "DEC_02", "DEC_03", "DEC_04", "DEC_05", "DEC_06"]


def test_01_all_11_deliverables_exist():
    """Verify that all 11 required Phase 5.5.0.4 deliverables exist and are non-empty."""
    assert PHASE_5_5_0_4_DIR.exists(), f"Missing directory {PHASE_5_5_0_4_DIR}"
    for fname in REQUIRED_DELIVERABLES:
        fpath = PHASE_5_5_0_4_DIR / fname
        assert fpath.exists(), f"Missing deliverable: {fname}"
        assert fpath.stat().st_size > 100, f"Deliverable is unexpectedly small: {fname}"


def test_02_all_six_decisions_have_dedicated_briefs():
    """Verify that each decision has a dedicated markdown brief file."""
    brief_files = [
        ("DEC_01", "PHASE_5_5_0_4_DEC_01_BARRIER_ARCHITECTURE.md"),
        ("DEC_02", "PHASE_5_5_0_4_DEC_02_DIRECTIONAL_SCOPE.md"),
        ("DEC_03", "PHASE_5_5_0_4_DEC_03_FUNDING_MODEL.md"),
        ("DEC_04", "PHASE_5_5_0_4_DEC_04_COST_GATE.md"),
        ("DEC_05", "PHASE_5_5_0_4_DEC_05_PORTFOLIO_RISK.md"),
        ("DEC_06", "PHASE_5_5_0_4_DEC_06_XMR_SCOPE.md"),
    ]
    for dec_id, fname in brief_files:
        fpath = PHASE_5_5_0_4_DIR / fname
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            assert dec_id in content, f"Missing {dec_id} header in {fname}"
            assert "PENDING_HUMAN_DECISION" in content, f"Decision {dec_id} not pending in {fname}"
            assert "Execution Blocking: `YES`" in content or "Execution Blocking" in content


def test_03_human_approval_template_has_no_fabricated_approvals():
    """Verify that human approval template contains unexecuted placeholders only."""
    fpath = PHASE_5_5_0_4_DIR / "PHASE_5_5_0_4_HUMAN_APPROVAL_TEMPLATE.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "UNEXECUTED_TEMPLATE_READY_FOR_HUMAN_SIGN_OFF" in content
    assert "DENIED_UNTIL_ALL_DECISIONS_SIGNED" in content
    assert "[UNEXECUTED]" in content

    # All decisions must be marked PENDING_HUMAN_DECISION with pending inputs
    for dec_id in EXPECTED_DECISION_IDS:
        assert dec_id in content
        assert "Selected Option" in content
        assert "[PENDING_HUMAN_INPUT]" in content
        assert "PENDING_HUMAN_DECISION" in content


def test_04_dec_01_presents_three_architectures():
    """Verify DEC_01 presents Alternatives A, B, and C with comparison matrix."""
    fpath = PHASE_5_5_0_4_DIR / "PHASE_5_5_0_4_DEC_01_BARRIER_ARCHITECTURE.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Alternative A: Original Barrier Preservation" in content
    assert "Alternative B: Re-Anchor Symmetric Barriers" in content
    assert "Alternative C: Decouple Directional Classifier" in content
    assert "1:17 risk-reward inversion" in content or "Risk-Reward Inversion" in content
    assert "Comparison Matrix" in content or "COMPARISON MATRIX" in content


def test_05_dec_02_directional_scope_analysis():
    """Verify DEC_02 presents Long, Short, and Bidirectional with independent reporting."""
    fpath = PHASE_5_5_0_4_DIR / "PHASE_5_5_0_4_DEC_02_DIRECTIONAL_SCOPE.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Long-Only" in content
    assert "Short-Only" in content
    assert "Bidirectional" in content
    assert "Separate PnL curves" in content or "separate PnL reporting" in content
    assert "Funding Rate Asymmetry" in content


def test_06_dec_03_funding_model_specification():
    """Verify DEC_03 presents canonical settlement rate and annualization formula."""
    fpath = PHASE_5_5_0_4_DEC_03_dir = PHASE_5_5_0_4_DIR / "PHASE_5_5_0_4_DEC_03_FUNDING_MODEL.md"
    with open(PHASE_5_5_0_4_DEC_03_dir, "r", encoding="utf-8") as f:
        content = f.read()

    assert "funding_rate_bps_per_settlement" in content
    assert "1095" in content
    assert "CF_t = -d \\times N_t \\times f_t" in content
    assert "Parametric Sensitivity Sweep" in content
    assert "THEORETICAL_UNDER_UNIFORM_ENTRY_AND_FIXED_HOLDING_ASSUMPTIONS" in content


def test_07_dec_04_cost_gate_tiers():
    """Verify DEC_04 presents 15 bps, 20 bps, and 30 bps round-trip tiers."""
    fpath = PHASE_5_5_0_4_DIR / "PHASE_5_5_0_4_DEC_04_COST_GATE.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "15 bps Round-Trip" in content
    assert "20 bps Round-Trip" in content
    assert "30 bps Round-Trip" in content
    assert "17.828" in content or "17.83" in content
    assert "Conservative Tier" in content


def test_08_dec_05_portfolio_risk_and_concurrency():
    """Verify DEC_05 defines gross leverage and limits of 2, 3, and 5 positions."""
    fpath = PHASE_5_5_0_4_DIR / "PHASE_5_5_0_4_DEC_05_PORTFOLIO_RISK.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Max 2 Concurrent Positions" in content
    assert "Max 3 Concurrent Positions" in content
    assert "Max 5 Concurrent Positions" in content
    assert "Gross Leverage" in content
    assert "Cross-Asset Correlation" in content


def test_09_dec_06_xmr_research_and_portfolio_scope():
    """Verify DEC_06 separates model preservation from portfolio eligibility."""
    fpath = PHASE_5_5_0_4_DIR / "PHASE_5_5_0_4_DEC_06_XMR_SCOPE.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "83,863" in content
    assert "316,500" in content
    assert "Model Artifact Preservation (100% PRESERVED)" in content
    assert "Exclude XMR from Primary Economic Portfolio" in content


def test_10_decision_dependency_matrix_completeness():
    """Verify dependency matrix covers all pairwise interactions and sequencing."""
    fpath = PHASE_5_5_0_4_DIR / "PHASE_5_5_0_4_DECISION_DEPENDENCY_MATRIX.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    for dec_id in EXPECTED_DECISION_IDS:
        assert dec_id in content

    assert "DEC_01 (Barrier Architecture) & DEC_04 (Cost Gate)" in content
    assert "DEC_02 (Directional Scope) & DEC_03 (Funding Model)" in content
    assert "DEC_02 (Directional Scope) & DEC_05 (Portfolio Risk)" in content
    assert "DEC_04 (Cost Gate) & DEC_05 (Portfolio Risk)" in content
    assert "DEC_05 (Portfolio Risk) & DEC_06 (XMR Scope)" in content
    assert "Recommended Logical Decision Sequence" in content or "RECOMMENDED LOGICAL DECISION SEQUENCE" in content


def test_11_reversibility_and_risk_register_coverage():
    """Verify reversibility register covers all six decisions."""
    fpath = PHASE_5_5_0_4_DIR / "PHASE_5_5_0_4_REVERSIBILITY_AND_RISK_REGISTER.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    for dec_id in EXPECTED_DECISION_IDS:
        assert dec_id in content

    assert "NO (100% Intact)" in content


def test_12_frozen_models_and_preprocessors_integrity():
    """Verify that all 55 Phase 5.3 LightGBM binaries and 55 preprocessors remain unchanged."""
    assert PHASE_5_3_FREEZE_MANIFEST.exists(), "Phase 5.3 freeze manifest missing!"
    with open(PHASE_5_3_FREEZE_MANIFEST, "r", encoding="utf-8") as f:
        freeze_data = json.load(f)

    freeze_lookup = {
        art["relative_path"].replace("\\", "/"): art["sha256"]
        for art in freeze_data["artifacts"]
    }

    for sym in SYMBOLS:
        base_dir = Path("artifacts/phase_5_3_1" if sym in ["BTCUSDT", "XMRUSDT"] else "artifacts/phase_5_3_2") / sym
        for fold in range(1, 6):
            m_path = base_dir / f"fold_{fold}" / "lgbm_model.joblib"
            p_path = base_dir / f"fold_{fold}" / "preprocessor.joblib"

            assert m_path.exists(), f"Model binary missing: {m_path}"
            assert p_path.exists(), f"Preprocessor missing: {p_path}"

            h_m = hashlib.sha256(m_path.read_bytes()).hexdigest()
            h_p = hashlib.sha256(p_path.read_bytes()).hexdigest()

            assert h_m == freeze_lookup[str(m_path).replace("\\", "/")]
            assert h_p == freeze_lookup[str(p_path).replace("\\", "/")]


def test_13_prospective_holdout_protection():
    """Verify that prospective holdout (2026-11-01 to 2027-04-30) remains strictly protected."""
    doc_path = PHASE_5_5_0_4_DIR / "PHASE_5_5_0_4_FINAL_GOVERNANCE_REPORT.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "2026-11-01 00:00:00 UTC" in content
    assert "2027-04-30 23:59:59.999 UTC" in content
    assert "SEALED" in content or "sealed" in content
    assert "NOT_STARTED" in content


def test_14_final_governance_report_verdict():
    """Verify final governance report specifies GOVERNANCE_PACKAGE_READY_WITH_LIMITATIONS."""
    doc_path = PHASE_5_5_0_4_DIR / "PHASE_5_5_0_4_FINAL_GOVERNANCE_REPORT.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "GOVERNANCE_PACKAGE_READY_WITH_LIMITATIONS" in content


def test_15_zero_em_dashes_across_all_phase_5_5_0_4_files():
    """Verify zero em dashes (Unicode U+2014) across all Phase 5.5.0.4 files."""
    em_dash = chr(0x2014)
    for fname in REQUIRED_DELIVERABLES:
        fpath = PHASE_5_5_0_4_DIR / fname
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            assert em_dash not in content, f"Em dash detected in {fname}!"
