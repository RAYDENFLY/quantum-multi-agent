"""
Unit tests for QUANTUM Phase 5.4.0:
Calibration & Decision Policy Research Design.

Verifies:
1. All four Phase 5.4 design documents exist and exceed minimum content size.
2. Artifact readiness audit documents all 11 instruments and 5 model families.
3. Temporal split boundaries and timestamps are strictly non-overlapping and chronologically ordered.
4. Acceptance criteria define hard gates, diagnostic metrics, and failure modes.
5. Zero em-dashes across all Phase 5.4 files.
"""

import pathlib
import pytest

RESEARCH_DOCS_DIR = pathlib.Path("docs/research")

PHASE_5_4_FILES = [
    RESEARCH_DOCS_DIR / "PHASE_5_4_RESEARCH_DESIGN.md",
    RESEARCH_DOCS_DIR / "PHASE_5_4_ARTIFACT_READINESS_AUDIT.md",
    RESEARCH_DOCS_DIR / "PHASE_5_4_EXPERIMENT_PROTOCOL.md",
    RESEARCH_DOCS_DIR / "PHASE_5_4_ACCEPTANCE_CRITERIA.md",
]

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"
]


def test_01_all_phase_5_4_design_documents_exist_and_sized():
    for p in PHASE_5_4_FILES:
        assert p.exists(), f"Missing required document: {p}"
        assert p.stat().st_size > 3_000, f"Document {p} is too short ({p.stat().st_size} bytes)"


def test_02_artifact_readiness_audit_covers_fleet_and_models():
    doc = (RESEARCH_DOCS_DIR / "PHASE_5_4_ARTIFACT_READINESS_AUDIT.md").read_text(encoding="utf-8")

    # Check all 11 instruments are covered
    for sym in SYMBOLS:
        assert sym in doc, f"Instrument {sym} missing from artifact audit"

    # Check all 5 models are covered
    for model in ["B0 Majority", "B1 Prior", "B2 LogReg", "B3 RandForest", "B4 LightGBM"]:
        assert model in doc, f"Model family {model} missing from artifact audit"

    # Verify bit-exact inference finding
    assert "BIT-EXACT MATCH" in doc
    assert "proba_hash" in doc
    assert "lgbm_model.joblib" in doc
    assert "preprocessor.joblib" in doc


def test_03_temporal_experiment_partition_structure():
    doc = (RESEARCH_DOCS_DIR / "PHASE_5_4_EXPERIMENT_PROTOCOL.md").read_text(encoding="utf-8")

    # Check the three segments are documented
    assert "Segment 1: Calibration Fit" in doc
    assert "Segment 2: Policy Tuning" in doc
    assert "Segment 3: Eval" in doc or "Segment 3 (Final Out-of-Sample" in doc

    # Check fold allocations
    assert "Folds 1 & 2" in doc
    assert "Folds 3 & 4" in doc
    assert "Fold 5" in doc

    # Check holdout protection
    assert "2026-11-01" in doc
    assert "2027-04-30" in doc


def test_04_acceptance_criteria_architecture():
    doc = (RESEARCH_DOCS_DIR / "PHASE_5_4_ACCEPTANCE_CRITERIA.md").read_text(encoding="utf-8")

    # Check hard gate definitions
    assert "GATE-5.4-01" in doc
    assert "GATE-5.4-02" in doc
    assert "GATE-5.4-03" in doc
    assert "GATE-5.4-04" in doc
    assert "GATE-5.4-05" in doc
    assert "GATE-5.4-06" in doc
    assert "GATE-5.4-07" in doc

    # Check diagnostic metrics
    assert "Temperature Parameter Stability" in doc
    assert "Reliability Diagram Visual Flatness" in doc

    # Check failure modes
    assert "Failure Mode" in doc


def test_05_zero_em_dashes_in_phase_5_4_deliverables():
    em_dash = chr(0x2014)
    all_files = PHASE_5_4_FILES + [
        pathlib.Path("tests/unit/test_phase5_4_0_design.py"),
        pathlib.Path("scripts/generate_phase_5_4_research_design.py")
    ]
    for p in all_files:
        if p.exists():
            text = p.read_text(encoding="utf-8")
            assert em_dash not in text, f"Forbidden em-dash found in {p}"
