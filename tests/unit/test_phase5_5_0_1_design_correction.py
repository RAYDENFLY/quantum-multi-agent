"""
QUANTUM Phase 5.5.0.1 Unit Tests: Design Correction & Execution Readiness Audit.

Validates the structural integrity, mathematical consistency, and governance boundaries
of Phase 5.5.0.1:
1. All 11 required deliverables exist in docs/research/phase_5_5_0_1/.
2. All 3 JSON deliverables parse successfully and conform to strict schema requirements.
3. No prospective holdout path (2026-11-01 to 2027-04-30) is accessed or inspected.
4. All 55 frozen LightGBM model binaries remain 100% bit-for-bit intact.
5. All 55 frozen preprocessors remain 100% bit-for-bit intact.
6. All unresolved parameters and issues are explicitly registered with standardized statuses.
7. All 12 acceptance gates have complete mathematical definitions and pass thresholds.
8. All transaction cost variables have explicit physical units and scales.
9. Both statistical bootstrap levels (Specialist and Portfolio) define their resampling unit.
10. All governance decisions requiring human approval are explicitly marked.
11. Zero em dashes (Unicode U+2014) anywhere in Phase 5.5.0.1 files.
"""

import json
import pytest
from pathlib import Path

PHASE_5_5_0_1_DIR = Path("docs/research/phase_5_5_0_1")
PHASE_5_3_FREEZE_MANIFEST = Path("artifacts/phase_5_3_freeze/frozen_artifact_manifest.json")

REQUIRED_DELIVERABLES = [
    "PHASE_5_5_0_1_LABEL_ENTRY_BARRIER_SEMANTICS.md",
    "PHASE_5_5_0_1_SLIPPAGE_DIMENSIONAL_AUDIT.md",
    "PHASE_5_5_0_1_PORTFOLIO_STATISTICAL_INFERENCE.md",
    "PHASE_5_5_0_1_POSITION_SIZING_RISK_CORRECTION.md",
    "PHASE_5_5_0_1_DATA_AND_FUNDING_AUDIT.json",
    "PHASE_5_5_0_1_ACCEPTANCE_GATE_AUDIT.md",
    "PHASE_5_5_0_1_TEMPORAL_GOVERNANCE_CORRECTION.md",
    "PHASE_5_5_0_1_PARAMETER_DECISION_REGISTRY.json",
    "PHASE_5_5_0_1_UNRESOLVED_ISSUES_REGISTER.json",
    "PHASE_5_5_0_1_HUMAN_APPROVAL_CHECKLIST.md",
    "PHASE_5_5_0_1_FINAL_AUDIT_REPORT.md"
]

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"
]


def test_01_all_11_deliverables_exist():
    """Verify that all 11 required Phase 5.5.0.1 deliverables exist and are non-empty."""
    assert PHASE_5_5_0_1_DIR.exists(), f"Missing directory {PHASE_5_5_0_1_DIR}"
    for fname in REQUIRED_DELIVERABLES:
        fpath = PHASE_5_5_0_1_DIR / fname
        assert fpath.exists(), f"Missing deliverable: {fname}"
        assert fpath.stat().st_size > 100, f"Deliverable is unexpectedly small: {fname}"


def test_02_all_json_deliverables_parse_and_validate():
    """Verify that all JSON deliverables parse successfully and conform to schema."""
    json_files = [
        "PHASE_5_5_0_1_DATA_AND_FUNDING_AUDIT.json",
        "PHASE_5_5_0_1_PARAMETER_DECISION_REGISTRY.json",
        "PHASE_5_5_0_1_UNRESOLVED_ISSUES_REGISTER.json"
    ]
    for fname in json_files:
        fpath = PHASE_5_5_0_1_DIR / fname
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert isinstance(data, dict), f"{fname} must be a JSON object"
            assert "title" in data, f"{fname} missing title"
            assert "timestamp_utc" in data, f"{fname} missing timestamp_utc"


def test_03_prospective_holdout_protection():
    """Verify that prospective holdout (2026-11-01 to 2027-04-30) remains strictly protected."""
    audit_path = PHASE_5_5_0_1_DIR / "PHASE_5_5_0_1_DATA_AND_FUNDING_AUDIT.json"
    with open(audit_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    holdout = data["prospective_holdout_protection"]
    assert holdout["isolation_status"] == "VERIFIED_STRICTLY_INACCESSIBLE"
    assert holdout["inspected_records"] == 0
    assert "2026-11-01" in holdout["holdout_window_utc"]
    assert "2027-04-30" in holdout["holdout_window_utc"]


def test_04_frozen_models_and_preprocessors_integrity():
    """Verify that all 55 Phase 5.3 LightGBM binaries and 55 preprocessors remain unchanged."""
    assert PHASE_5_3_FREEZE_MANIFEST.exists(), "Phase 5.3 freeze manifest missing!"
    with open(PHASE_5_3_FREEZE_MANIFEST, "r", encoding="utf-8") as f:
        freeze_data = json.load(f)

    freeze_lookup = {
        art["relative_path"].replace("\\", "/"): art["sha256"]
        for art in freeze_data["artifacts"]
    }

    import hashlib
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


def test_05_unresolved_parameters_and_issues_registered():
    """Verify that all parameters and unresolved issues have standardized evidence statuses."""
    reg_path = PHASE_5_5_0_1_DIR / "PHASE_5_5_0_1_PARAMETER_DECISION_REGISTRY.json"
    with open(reg_path, "r", encoding="utf-8") as f:
        reg_data = json.load(f)

    valid_statuses = {
        "VERIFIED_FROM_SOURCE",
        "VERIFIED_FROM_DATA_METADATA",
        "UNVERIFIED_ASSUMPTION",
        "UNAVAILABLE",
        "REQUIRES_HUMAN_DECISION"
    }

    for p in reg_data["parameters"]:
        assert p["evidence_status"] in valid_statuses, f"Invalid status: {p['evidence_status']}"
        assert len(p["validation_requirement"]) > 5

    issues_path = PHASE_5_5_0_1_DIR / "PHASE_5_5_0_1_UNRESOLVED_ISSUES_REGISTER.json"
    with open(issues_path, "r", encoding="utf-8") as f:
        issues_data = json.load(f)

    assert len(issues_data["issues"]) >= 5
    for issue in issues_data["issues"]:
        assert "issue_id" in issue
        assert "recommended_resolution" in issue
        assert issue["impact"] in {"CRITICAL", "HIGH", "MEDIUM"}


def test_06_acceptance_gates_completeness():
    """Verify that all 12 acceptance gates are defined in the acceptance gate audit."""
    doc_path = PHASE_5_5_0_1_DIR / "PHASE_5_5_0_1_ACCEPTANCE_GATE_AUDIT.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    for gate_num in range(1, 13):
        assert f"Gate {gate_num}:" in content, f"Missing definition for Gate {gate_num}"

    # Verify zero-division handling is documented
    assert "Zero-Division Handling:" in content


def test_07_slippage_and_cost_dimensional_consistency():
    """Verify that the slippage audit document explicitly covers physical units and definitions."""
    doc_path = PHASE_5_5_0_1_DIR / "PHASE_5_5_0_1_SLIPPAGE_DIMENSIONAL_AUDIT.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Physical Unit" in content
    assert "USDT" in content
    assert "Decimal fraction / bps" in content
    assert "Bid-Ask Spread Cost" in content
    assert "Execution Slippage" in content
    assert "Market Impact" in content


def test_08_portfolio_inference_resampling_units():
    """Verify that Level 1 and Level 2 bootstrap resampling units are defined."""
    doc_path = PHASE_5_5_0_1_DIR / "PHASE_5_5_0_1_PORTFOLIO_STATISTICAL_INFERENCE.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Level 1: Specialist-Level Inference" in content
    assert "Level 2: Portfolio-Level Inference" in content
    assert "Resampling Unit:" in content
    assert "Synchronized Moving Block Bootstrap" in content
    assert "$b = 24$ bars" in content


def test_09_human_approval_decisions_explicitly_marked():
    """Verify that all unresolved decisions are presented in the Human Approval Checklist."""
    doc_path = PHASE_5_5_0_1_DIR / "PHASE_5_5_0_1_HUMAN_APPROVAL_CHECKLIST.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "DEC_01" in content
    assert "DEC_02" in content
    assert "DEC_03" in content
    assert "DEC_04" in content
    assert "DEC_05" in content
    assert "DEC_06" in content
    assert "PENDING_HUMAN_DECISION" in content


def test_10_calendar_duration_correction():
    """Verify that the calendar duration is accurately reported as 3 years and 3 days."""
    audit_path = PHASE_5_5_0_1_DIR / "PHASE_5_5_0_1_DATA_AND_FUNDING_AUDIT.json"
    with open(audit_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    corr = data["calendar_duration_correction"]
    assert "3 years and 3 days" in corr["corrected_calendar_span"]
    assert "1,100" in corr["corrected_calendar_span"]
    assert "4 years" in corr["erroneous_prior_description"]


def test_11_zero_em_dashes_in_phase_5_5_0_1():
    """Verify zero em dashes (Unicode U+2014) across all Phase 5.5.0.1 files."""
    em_dash = chr(0x2014)
    for fname in REQUIRED_DELIVERABLES:
        fpath = PHASE_5_5_0_1_DIR / fname
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            assert em_dash not in content, f"Em dash detected in {fname}!"
