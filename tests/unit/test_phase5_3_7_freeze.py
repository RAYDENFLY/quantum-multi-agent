"""
Unit tests for QUANTUM Phase 5.3.7: Research Freeze, Benchmark Closure & Phase 5.4 Proposal.
Verifies the existence, completeness, and cryptographic integrity of freeze and proposal
documentation, random seed governance, artifact immutability, and zero em-dash compliance.
"""

import hashlib
import json
from pathlib import Path
import pytest

RESEARCH_DOCS_DIR = Path("docs/research")
ARTIFACTS_DIR = Path("artifacts")
SCRIPTS_DIR = Path("scripts")
TESTS_DIR = Path("tests/unit")

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"
]

EXPECTED_KEY_ARTIFACTS = {
    "artifacts/phase_5_3_1/pilot_summary.json": "f38a33c6cbdbd30bc97be862da9faa966d962be0139f242d3beb147de365b20b",
    "artifacts/phase_5_3_1/BTCUSDT/fold_1/lgbm_model.joblib": "14438c40eb5849000198775030fd26f32f6c2026f326f068bef7f5c3f6ea161f",
    "artifacts/phase_5_3_1/XMRUSDT/fold_1/lgbm_model.joblib": "80f0d475f8091bfd75662c748c55dd6a28a38b665a9679c5624ff32a013ab10f",
    "artifacts/phase_5_3_2/ETHUSDT/fold_1/lgbm_model.joblib": "482bcf8cecad3ff3b0152c0bbf391f21b5b0852f37120d779630c5620b876168",
    "artifacts/phase_5_3_2/BNBUSDT/fold_1/lgbm_model.joblib": "91f7c5e52b664c2475b3cb0bfd7efdcb7b61cedd2178bb4d016a335602cacd6b",
    "artifacts/phase_5_3_2/SOLUSDT/fold_1/lgbm_model.joblib": "4376f902a251ed7ba5d056a2741f5fa833cdffce420d0211ed64ce81d26d812d",
    "artifacts/phase_5_3_3/master_benchmark_catalog.json": "199b243bc55936cc7fedd66e4549049494b8b4edb3811f2fc096b3e61acd423a",
    "artifacts/phase_5_3_3_1/final_benchmark_catalog.json": "94ca6ce51eb3035330095cdd78f645d0ed14c9f614b14fb664abcda084a19b64",
    "artifacts/phase_5_3_3_3/empirical_mbb_results.json": "99a342c80d3b7ea225e87447fb4288a5f2cdb58bdfd5aacac842f268e4ac4d88",
    "artifacts/phase_5_3_3_4/oof_sample_accounting.json": "741fe3fd4d448abce14b825e4bad423795c2ca160149e50b3e2079d938a4fd83",
    "artifacts/phase_5_3_3_5/fold_aggregation_audit.json": "edc4b0e88c9fe5b68d07f39ead514cb4b655445c11eead0f9f4dfd998d0d9999",
    "artifacts/phase_5_3_3_5/paired_b4_b0_results.json": "01c5f256ecbffd8bd34c83da1abe67eb34de537ebe4b1a29488d8f1690b25a1f",
    "artifacts/phase_5_3_3_6/oof_population_audit.json": "9ebc3fa04a7a218bc647390a40fc6f3b9722ac8545f11f419e0dc6d39ef1948c",
    "artifacts/phase_5_3_3_6/bootstrap_implementation_audit.json": "8bed87dbbef2067df7f002c5ccb17296a07aa58609cb06c52e260b5cd6e5fff9",
}


def test_01_freeze_and_proposal_documents_exist():
    freeze_doc = RESEARCH_DOCS_DIR / "PHASE_5_3_FINAL_FREEZE.md"
    proposal_doc = RESEARCH_DOCS_DIR / "PHASE_5_4_RESEARCH_PROPOSAL.md"

    assert freeze_doc.exists(), "Missing PHASE_5_3_FINAL_FREEZE.md"
    assert proposal_doc.exists(), "Missing PHASE_5_4_RESEARCH_PROPOSAL.md"
    assert freeze_doc.stat().st_size > 5_000, "PHASE_5_3_FINAL_FREEZE.md is too short"
    assert proposal_doc.stat().st_size > 5_000, "PHASE_5_4_RESEARCH_PROPOSAL.md is too short"


def test_02_key_artifacts_exist_and_hashes_match():
    for fpath_str, expected_hash in EXPECTED_KEY_ARTIFACTS.items():
        p = Path(fpath_str)
        assert p.exists(), f"Missing frozen artifact: {fpath_str}"
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        assert h == expected_hash, f"Hash mismatch for {fpath_str}: {h} != {expected_hash}"


def test_03_random_seed_governance_documented_and_verified():
    with open("artifacts/phase_5_3_3_5/paired_b4_b0_results.json", encoding="utf-8") as f:
        paired_data = json.load(f)

    assert paired_data["random_seed"] == 42
    for sym in SYMBOLS:
        b_dict = paired_data["instruments"][sym]["bootstrap_results_by_block_length"]
        assert b_dict["b_12"]["random_seed"] == 54  # 42 + 12
        assert b_dict["b_24"]["random_seed"] == 66  # 42 + 24
        assert b_dict["b_48"]["random_seed"] == 90  # 42 + 48
        assert b_dict["b_96"]["random_seed"] == 138 # 42 + 96

    freeze_text = (RESEARCH_DOCS_DIR / "PHASE_5_3_FINAL_FREEZE.md").read_text(encoding="utf-8")
    assert "RANDOM_SEED = 42" in freeze_text
    assert "42 + 12 = 54" in freeze_text
    assert "42 + 24 = 66" in freeze_text
    assert "42 + 48 = 90" in freeze_text
    assert "42 + 96 = 138" in freeze_text
    assert "PCG64" in freeze_text


def test_04_proposal_covers_all_required_sections():
    prop_text = (RESEARCH_DOCS_DIR / "PHASE_5_4_RESEARCH_PROPOSAL.md").read_text(encoding="utf-8")

    # Research objective & non-profitability
    assert "Core Research Objective" in prop_text
    assert "predictive discrimination does not constitute economic profitability" in prop_text

    # All 8 directions
    assert "1. Probability Calibration" in prop_text
    assert "2. Class-Specific Precision & Recall Optimization" in prop_text
    assert "3. Confidence-Based Prediction Filtering" in prop_text
    assert "4. Selective Classification & Abstention Policy" in prop_text
    assert "5. Cost-Sensitive Decision Policy" in prop_text
    assert "6. Triple-Barrier Prediction to Trading Decision Mapping" in prop_text
    assert "7. Multi-Timeframe Confirmation" in prop_text
    assert "8. Robustness Across Market Regimes" in prop_text

    # Recommended sequence
    assert "Recommended Research Sequence" in prop_text
    assert "STAGE 1: Phase 5.4.1" in prop_text
    assert "STAGE 2: Phase 5.4.2" in prop_text
    assert "STAGE 3: Phase 5.4.3" in prop_text
    assert "STAGE 4: Phase 5.4.4" in prop_text

    # Evaluation framework: 3 distinct groups
    assert "Predictive Metrics" in prop_text
    assert "Decision-Policy Metrics" in prop_text
    assert "Economic Metrics" in prop_text
    assert "Why the Three Metric Groups Must Never Be Interchanged" in prop_text

    # Gate status
    assert "EXECUTION ON HOLD" in prop_text


def test_05_prohibited_claims_explicitly_cataloged():
    freeze_text = (RESEARCH_DOCS_DIR / "PHASE_5_3_FINAL_FREEZE.md").read_text(encoding="utf-8")
    assert "Explicit Prohibited Claims" in freeze_text
    assert "Claiming that Specialist B4 constitutes a profitable or viable trading strategy" in freeze_text
    assert "Claiming positive expected economic return, net PnL, alpha, or positive Sharpe ratio" in freeze_text
    assert "Claiming readiness for live capital allocation" in freeze_text


def test_06_zero_em_dashes_in_phase5_3_7_files():
    files_to_check = [
        RESEARCH_DOCS_DIR / "PHASE_5_3_FINAL_FREEZE.md",
        RESEARCH_DOCS_DIR / "PHASE_5_4_RESEARCH_PROPOSAL.md",
        SCRIPTS_DIR / "generate_phase_5_3_7_freeze_and_proposal.py",
        TESTS_DIR / "test_phase5_3_7_freeze.py",
    ]
    em_dash = "\u2014"
    for fpath in files_to_check:
        text = fpath.read_text(encoding="utf-8")
        assert em_dash not in text, f"Forbidden em-dash found in {fpath}"
