"""
Unit tests for QUANTUM Phase 5.4.1:
Methodology Correction & Execution Readiness.

Verifies:
1. Realized return reconstruction methodology is formally specified.
2. Transaction cost model includes multi-tier sensitivity scenarios.
3. Calibration input compatibility and raw logit extraction are verified.
4. Temporal fold boundaries and 13-bar purge gap are verified.
5. Selective classification acceptance criteria enforce monotonicity and support.
6. Phase 5.4 is strictly separated from Phase 5.5 (no net PnL gate in 5.4).
7. Zero em-dashes across all Phase 5.4.1 files.
"""

import json
from pathlib import Path
import pytest

RESEARCH_DOCS_DIR = Path("docs/research")

FILES_TO_CHECK = [
    RESEARCH_DOCS_DIR / "PHASE_5_4_RESEARCH_DESIGN.md",
    RESEARCH_DOCS_DIR / "PHASE_5_4_EXPERIMENT_PROTOCOL.md",
    RESEARCH_DOCS_DIR / "PHASE_5_4_ACCEPTANCE_CRITERIA.md",
    RESEARCH_DOCS_DIR / "PHASE_5_4_ARTIFACT_READINESS_AUDIT.md",
    RESEARCH_DOCS_DIR / "PHASE_5_4_1_METHODOLOGY_CORRECTION_REPORT.md",
]


def test_01_realized_return_reconstruction_methodology_specified():
    proto = (RESEARCH_DOCS_DIR / "PHASE_5_4_EXPERIMENT_PROTOCOL.md").read_text(encoding="utf-8")

    assert "Realized Barrier Outcome & Trade Return Reconstruction" in proto
    assert "Gap Open" in proto
    assert "{closes}[i + 12]" in proto
    assert "AMBIGUOUS" in proto
    assert "R_gross, long" in proto or "R_{\\text{gross, long}}" in proto


def test_02_transaction_cost_model_and_sensitivity_scenarios():
    proto = (RESEARCH_DOCS_DIR / "PHASE_5_4_EXPERIMENT_PROTOCOL.md").read_text(encoding="utf-8")

    assert "Friction Sensitivity Grid" in proto
    assert "Scenario A" in proto
    assert "Scenario B" in proto
    assert "Scenario C" in proto
    assert "Scenario D" in proto
    assert "Unresolved Prerequisite" in proto


def test_03_calibration_input_compatibility_and_raw_score_logits():
    audit = (RESEARCH_DOCS_DIR / "PHASE_5_4_ARTIFACT_READINESS_AUDIT.md").read_text(encoding="utf-8")

    assert "raw_score=True" in audit
    assert "classes_ = [-1, 0, 1]" in audit
    assert "max_diff == 0.0" in audit or "difference of **0.0**" in audit
    assert "UNAVAILABLE_WITHOUT_RETRAINING" in audit


def test_04_temporal_fold_timestamps_and_13_bar_purge_gap():
    proto = (RESEARCH_DOCS_DIR / "PHASE_5_4_EXPERIMENT_PROTOCOL.md").read_text(encoding="utf-8")

    assert "13-Bar Purge" in proto
    assert "3,900,000 ms" in proto
    assert "1738125600000" in proto
    assert "1777586100000" in proto
    assert "2026-11-01" in proto
    assert "2027-04-30" in proto


def test_05_selective_classification_acceptance_criteria_architecture():
    crit = (RESEARCH_DOCS_DIR / "PHASE_5_4_ACCEPTANCE_CRITERIA.md").read_text(encoding="utf-8")

    assert "GATE-5.4-06" in crit
    assert "beta_RC > 0" in crit or "\\beta_{\\text{RC}} > 0" in crit
    assert "N_c >= 100" in crit or "N_c \\ge 100" in crit
    assert "Random Abstention" in crit


def test_06_separation_of_phase_5_4_from_phase_5_5():
    design = (RESEARCH_DOCS_DIR / "PHASE_5_4_RESEARCH_DESIGN.md").read_text(encoding="utf-8")
    crit = (RESEARCH_DOCS_DIR / "PHASE_5_4_ACCEPTANCE_CRITERIA.md").read_text(encoding="utf-8")

    assert "PHASE 5.5: HISTORICAL STRATEGY BACKTESTING" in design
    assert "Phase 5.4 shall NOT claim trading profitability" in design
    assert "Realized portfolio net PnL" in crit


def test_07_zero_em_dashes_in_all_phase_5_4_1_deliverables():
    em_dash = chr(0x2014)
    all_files = FILES_TO_CHECK + [
        Path("tests/unit/test_phase5_4_1_correction.py"),
        Path("scripts/generate_phase_5_4_1_methodology_correction.py")
    ]
    for p in all_files:
        if p.exists():
            text = p.read_text(encoding="utf-8")
            assert em_dash not in text, f"Forbidden em-dash found in {p}"
