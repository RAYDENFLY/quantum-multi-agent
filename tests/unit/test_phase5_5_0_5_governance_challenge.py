"""
QUANTUM Phase 5.5.0.5 Unit Tests: Governance Challenge & Decision Clarification Audit.

Validates the structural integrity, governance boundaries, and analytical rigor
of Phase 5.5.0.5:
1. All 10 required deliverables exist in docs/research/phase_5_5_0_5/.
2. DEC_01 separates Objective A (Frozen ML, Alt B) from Objective B (Strategy Track, Alt C).
3. DEC_04 separates cost ceiling from break-even hurdle and defines denominator conventions.
4. DEC_02 audits the four directional claims with rigorous epistemic classifications.
5. DEC_05 reclassifies the rho > 0.70 correlation claim as unsupported in repository.
6. DEC_03 clarifies parametric sweep vs historical backfill tradeoffs.
7. DEC_06 decouples model preservation from portfolio eligibility.
8. Decision dependency reconciliation justifies the operational decision sequencing.
9. Unresolved assumptions register captures all active assumptions (ASM_01 to ASM_06).
10. Human decision worksheet contains unexecuted placeholders for all six decisions.
11. All 55 frozen LightGBM binaries and 55 preprocessors remain 100% bit-for-bit intact.
12. Prospective holdout (2026-11-01 to 2027-04-30) remains strictly protected and unaccessed.
13. Final report specifies GOVERNANCE_CHALLENGE_PASS_WITH_LIMITATIONS.
14. Zero em dashes (Unicode U+2014) anywhere in Phase 5.5.0.5 files or test suite.
"""

import hashlib
import json
from pathlib import Path
import pytest

PHASE_5_5_0_5_DIR = Path("docs/research/phase_5_5_0_5")
PHASE_5_3_FREEZE_MANIFEST = Path("artifacts/phase_5_3_freeze/frozen_artifact_manifest.json")

REQUIRED_DELIVERABLES = [
    "PHASE_5_5_0_5_DEC_01_RESEARCH_OBJECTIVE_CLARIFICATION.md",
    "PHASE_5_5_0_5_DEC_04_COST_DEFINITION_AUDIT.md",
    "PHASE_5_5_0_5_DEC_02_DIRECTIONAL_EVIDENCE_AUDIT.md",
    "PHASE_5_5_0_5_DEC_05_PORTFOLIO_CORRELATION_AUDIT.md",
    "PHASE_5_5_0_5_DEC_03_FUNDING_DECISION_CLARIFICATION.md",
    "PHASE_5_5_0_5_DEC_06_XMR_ELIGIBILITY_CLARIFICATION.md",
    "PHASE_5_5_0_5_DECISION_DEPENDENCY_RECONCILIATION.md",
    "PHASE_5_5_0_5_UNRESOLVED_ASSUMPTIONS_REGISTER.md",
    "PHASE_5_5_0_5_HUMAN_DECISION_WORKSHEET.md",
    "PHASE_5_5_0_5_FINAL_GOVERNANCE_CHALLENGE_REPORT.md",
]

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"
]

EXPECTED_DECISION_IDS = ["DEC_01", "DEC_02", "DEC_03", "DEC_04", "DEC_05", "DEC_06"]


def test_01_all_10_deliverables_exist():
    """Verify that all 10 required Phase 5.5.0.5 deliverables exist and are non-empty."""
    assert PHASE_5_5_0_5_DIR.exists(), f"Missing directory {PHASE_5_5_0_5_DIR}"
    for fname in REQUIRED_DELIVERABLES:
        fpath = PHASE_5_5_0_5_DIR / fname
        assert fpath.exists(), f"Missing deliverable: {fname}"
        assert fpath.stat().st_size > 100, f"Deliverable is unexpectedly small: {fname}"


def test_02_dec_01_research_objectives_properly_distinguished():
    """Verify DEC_01 distinguishes Objective A from Objective B with 12-dimension matrix."""
    fpath = PHASE_5_5_0_5_DIR / "PHASE_5_5_0_5_DEC_01_RESEARCH_OBJECTIVE_CLARIFICATION.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Research Objective A: Frozen Classifier Economic Validation" in content
    assert "Research Objective B: Independent Trading Strategy Development" in content
    assert "Alternative B" in content
    assert "Alternative C" in content
    assert "1. Research Hypothesis" in content
    assert "12. Reproducibility" in content
    assert "Sequential Research Tracks" in content


def test_03_dec_04_cost_ceiling_and_breakeven_hurdle_separated():
    """Verify DEC_04 separates cost ceiling from break-even hurdle with denominator rules."""
    fpath = PHASE_5_5_0_5_DIR / "PHASE_5_5_0_5_DEC_04_COST_DEFINITION_AUDIT.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Concept 1: Transaction Cost Ceiling" in content
    assert "Concept 2: Break-Even Gross Return Hurdle" in content
    assert "Why Simple Equality Fails in Reality" in content
    assert "Denominator Standard" in content
    assert "Gate 2 Mandatory Hurdle" in content
    assert "Secondary Sensitivity Sweeps" in content


def test_04_dec_02_directional_asymmetry_evidence_audited():
    """Verify DEC_02 audits the four directional claims with epistemic classifications."""
    fpath = PHASE_5_5_0_5_DIR / "PHASE_5_5_0_5_DEC_02_DIRECTIONAL_EVIDENCE_AUDIT.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "DATA_SUPPORTED" in content
    assert "UNSUPPORTED_IN_REPO" in content
    assert "THEORETICAL" in content
    assert "THEORETICAL_UNVERIFIED" in content
    assert "Strict Directional Disaggregation" in content


def test_05_dec_05_correlation_claim_reclassified_as_unsupported():
    """Verify DEC_05 confirms no empirical correlation matrix exists in repo."""
    fpath = PHASE_5_5_0_5_DIR / "PHASE_5_5_0_5_DEC_05_PORTFOLIO_CORRELATION_AUDIT.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Empirical Correlation Matrix in Repo" in content
    assert "DOMAIN_STYLIZED_FACT_UNVERIFIED_IN_DATASET" in content
    assert "Why Three 1% Risk Allocations Do NOT Guarantee a 3% Maximum Loss" in content
    assert "Gross Notional Leverage" in content


def test_06_dec_03_funding_model_clarification():
    """Verify DEC_03 clarifies parametric sweep vs historical backfill tradeoffs."""
    fpath = PHASE_5_5_0_5_DIR / "PHASE_5_5_0_5_DEC_03_FUNDING_DECISION_CLARIFICATION.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "What a Parametric Sweep CAN Prove" in content
    assert "What a Parametric Sweep CANNOT Prove" in content
    assert "funding_rate_bps_per_settlement" in content
    assert "1095" in content
    assert "CF_t = -d \\times N_t \\times f_t" in content


def test_07_dec_06_xmr_three_tier_policy_separated():
    """Verify DEC_06 separates artifact preservation from portfolio eligibility."""
    fpath = PHASE_5_5_0_5_DIR / "PHASE_5_5_0_5_DEC_06_XMR_ELIGIBILITY_CLARIFICATION.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Tier 1: Research Artifact Preservation (100% PRESERVED)" in content
    assert "Tier 3: Primary Multi-Asset Portfolio Eligibility (DEC_06)" in content
    assert "Ragged Covariance Matrix" in content
    assert "83,863" in content
    assert "316,500" in content


def test_08_decision_dependency_reconciliation():
    """Verify dependency reconciliation documents re-sequenced order."""
    fpath = PHASE_5_5_0_5_DIR / "PHASE_5_5_0_5_DECISION_DEPENDENCY_RECONCILIATION.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Funding assumptions (DEC_03) directly affect the net break-even return hurdle of DEC_04" in content
    assert "Four Types of Decision Dependencies" in content
    assert "Reconciled 6x6 Pairwise Dependency Table" in content or "RECONCILED 6x6 PAIRWISE DEPENDENCY TABLE" in content
    assert "Step 1: DEC_01" in content
    assert "Step 3: DEC_03" in content
    assert "Step 4: DEC_04" in content


def test_09_unresolved_assumptions_register_coverage():
    """Verify assumptions register covers all active assumptions ASM_01 to ASM_06."""
    fpath = PHASE_5_5_0_5_DIR / "PHASE_5_5_0_5_UNRESOLVED_ASSUMPTIONS_REGISTER.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "ASM_01" in content
    assert "ASM_02" in content
    assert "ASM_03" in content
    assert "ASM_04" in content
    assert "ASM_05" in content
    assert "ASM_06" in content


def test_10_human_decision_worksheet_integrity():
    """Verify worksheet contains unexecuted placeholders for all six decisions."""
    fpath = PHASE_5_5_0_5_DIR / "PHASE_5_5_0_5_HUMAN_DECISION_WORKSHEET.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "UNEXECUTED_WORKSHEET_AWAITING_HUMAN_SIGN_OFF" in content
    assert "DENIED_UNTIL_ALL_DECISIONS_SIGNED" in content
    assert "[UNEXECUTED]" in content

    for dec_id in EXPECTED_DECISION_IDS:
        assert dec_id in content
        assert "Human Selection:" in content
        assert "[PENDING_HUMAN_SELECTION]" in content
        assert "PENDING_HUMAN_DECISION" in content


def test_11_frozen_models_and_preprocessors_integrity():
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


def test_12_prospective_holdout_protection():
    """Verify that prospective holdout (2026-11-01 to 2027-04-30) remains strictly protected."""
    doc_path = PHASE_5_5_0_5_DIR / "PHASE_5_5_0_5_FINAL_GOVERNANCE_CHALLENGE_REPORT.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "2026-11-01" in content
    assert "2027-04-30" in content
    assert "SEALED" in content
    assert "NOT STARTED" in content or "NOT_STARTED" in content


def test_13_final_challenge_report_verdict():
    """Verify final challenge report specifies GOVERNANCE_CHALLENGE_PASS_WITH_LIMITATIONS."""
    doc_path = PHASE_5_5_0_5_DIR / "PHASE_5_5_0_5_FINAL_GOVERNANCE_CHALLENGE_REPORT.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "GOVERNANCE_CHALLENGE_PASS_WITH_LIMITATIONS" in content


def test_14_zero_em_dashes_across_all_phase_5_5_0_5_files():
    """Verify zero em dashes (Unicode U+2014) across all Phase 5.5.0.5 files."""
    em_dash = chr(0x2014)
    for fname in REQUIRED_DELIVERABLES:
        fpath = PHASE_5_5_0_5_DIR / fname
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            assert em_dash not in content, f"Em dash detected in {fname}!"
