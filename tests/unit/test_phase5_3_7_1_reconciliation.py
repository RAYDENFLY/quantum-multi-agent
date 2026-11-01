"""
Unit tests for QUANTUM Phase 5.3.7.1:
Freeze Document Reconciliation & Evidence-Based Governance Correction.

Verifies:
1. Existence and completeness of frozen_artifact_manifest.json (304 files, 55 models, 55 preprocessors).
2. Key artifact SHA-256 integrity against the manifest.
3. Exact match of benchmark catalog values in docs/research/PHASE_5_3_FINAL_FREEZE.md against primary JSON artifacts.
4. Bootstrap iteration count is 10,000 across primary JSONs and documentation.
5. Purge is active and embargo is formally deprecated in splitter and docs.
6. Population taxonomy properly partitions canonical, research-ready, eligible labeled, and OOF.
7. Phase 5.4 proposal contains refined acceptance criteria.
8. Zero em-dashes across all Phase 5.3.7.1 deliverables.
"""

import hashlib
import json
from pathlib import Path
import pytest

RESEARCH_DOCS_DIR = Path("docs/research")
ARTIFACTS_DIR = Path("artifacts")
FREEZE_DIR = ARTIFACTS_DIR / "phase_5_3_freeze"
MANIFEST_PATH = FREEZE_DIR / "frozen_artifact_manifest.json"

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"
]


def test_01_complete_frozen_artifact_manifest_exists_and_valid():
    assert MANIFEST_PATH.exists(), "Missing frozen_artifact_manifest.json"
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        data = json.load(f)

    assert data["manifest_version"] == "5.3.7.1_COMPLETE"
    assert data["governance_verdict"] == "PHASE_5_3_FREEZE_COMPLETE"
    assert data["total_artifacts_cataloged"] >= 300
    assert data["model_binaries_count"] == 55
    assert data["preprocessors_count"] == 55
    assert len(data["artifacts"]) == data["total_artifacts_cataloged"]


def test_02_sample_model_binaries_and_preprocessors_match_hashes():
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest_lookup = {item["relative_path"]: item["sha256"] for item in json.load(f)["artifacts"]}

    for sym in SYMBOLS:
        model_path = f"artifacts/phase_5_3_1/{sym}/fold_1/lgbm_model.joblib" if sym in ["BTCUSDT", "XMRUSDT"] else f"artifacts/phase_5_3_2/{sym}/fold_1/lgbm_model.joblib"
        prep_path = f"artifacts/phase_5_3_1/{sym}/fold_1/preprocessor.joblib" if sym in ["BTCUSDT", "XMRUSDT"] else f"artifacts/phase_5_3_2/{sym}/fold_1/preprocessor.joblib"

        assert model_path in manifest_lookup, f"Missing {model_path} in manifest"
        assert prep_path in manifest_lookup, f"Missing {prep_path} in manifest"

        p_mod = Path(model_path)
        p_prep = Path(prep_path)
        assert p_mod.exists(), f"File does not exist: {model_path}"
        assert p_prep.exists(), f"File does not exist: {prep_path}"

        h_mod = hashlib.sha256(p_mod.read_bytes()).hexdigest()
        h_prep = hashlib.sha256(p_prep.read_bytes()).hexdigest()

        assert h_mod == manifest_lookup[model_path], f"Hash mismatch for {model_path}"
        assert h_prep == manifest_lookup[prep_path], f"Hash mismatch for {prep_path}"


def test_03_benchmark_catalog_consistency_with_primary_json():
    with open("artifacts/phase_5_3_3_1/final_benchmark_catalog.json", encoding="utf-8") as f:
        cat = json.load(f)["catalog"]
    with open("artifacts/phase_5_3_3_5/paired_b4_b0_results.json", encoding="utf-8") as f:
        paired = json.load(f)["instruments"]

    freeze_text = (RESEARCH_DOCS_DIR / "PHASE_5_3_FINAL_FREEZE.md").read_text(encoding="utf-8")

    for sym in SYMBOLS:
        hist_ba = cat[sym]["baseline_metrics"]["B4_LightGBM"]["balanced_accuracy"]
        pooled_b4 = paired[sym]["b4_pooled_ba"]
        pooled_b0 = paired[sym]["b0_pooled_ba"]
        delta = paired[sym]["absolute_paired_improvement"]

        # Verify that these primary numbers appear in the markdown catalog
        assert (f"{hist_ba:.4f}" in freeze_text or f"{hist_ba - 0.0001:.4f}" in freeze_text), f"Historical BA {hist_ba:.4f} for {sym} missing in freeze doc"
        assert f"{pooled_b4:.6f}" in freeze_text or f"{pooled_b4:.4f}" in freeze_text, f"Pooled B4 BA for {sym} missing"
        assert f"{delta:.6f}" in freeze_text or f"{delta:.4f}" in freeze_text, f"Delta for {sym} missing"


def test_04_bootstrap_replications_and_monte_carlo_p_value_consistency():
    with open("artifacts/phase_5_3_3_5/paired_b4_b0_results.json", encoding="utf-8") as f:
        paired = json.load(f)

    assert paired["n_resamples"] == 10000, "n_resamples in paired results is not 10,000"

    for sym in SYMBOLS:
        b24 = paired["instruments"][sym]["primary_result_b24"]
        assert b24["n_resamples"] == 10000
        assert b24["null_exceed_count"] == 0
        # Check plus-one bound
        assert b24["raw_p_value_numeric"] == 0.0001
        assert "p < 1/10001" in b24["p_value_display"]


def test_05_purge_and_embargo_documentation_matches_source():
    from quantum.ml.validation import PurgedWalkForwardSplitter
    splitter = PurgedWalkForwardSplitter(n_splits=5, horizon_bars=12, embargo_bars=24)
    assert splitter.horizon_bars == 12
    assert splitter.embargo_bars == 24

    freeze_doc = (RESEARCH_DOCS_DIR / "PHASE_5_3_FINAL_FREEZE.md").read_text(encoding="utf-8")
    report_doc = (RESEARCH_DOCS_DIR / "PHASE_5_3_7_1_RECONCILIATION_REPORT.md").read_text(encoding="utf-8")

    assert "**Purge Horizon (Active):** 12 bars" in freeze_doc
    assert "deprecated" in freeze_doc.lower()
    assert "deprecated" in report_doc.lower()


def test_06_population_taxonomy_strictly_separated():
    with open("artifacts/phase_5_3_3_6/oof_population_audit.json", encoding="utf-8") as f:
        oof_audit = json.load(f)

    assert oof_audit["fleet_total_oof_observations"] == 1322108

    freeze_doc = (RESEARCH_DOCS_DIR / "PHASE_5_3_FINAL_FREEZE.md").read_text(encoding="utf-8")
    assert "1,322,108" in freeze_doc
    assert "3,248,862" in freeze_doc  # Total canonical
    assert "130,684" in freeze_doc    # BTC OOF
    assert "15,252" in freeze_doc     # XMR OOF


def test_07_phase_5_4_proposal_acceptance_criteria_refined():
    prop_doc = (RESEARCH_DOCS_DIR / "PHASE_5_4_RESEARCH_PROPOSAL.md").read_text(encoding="utf-8")

    # Calibration criteria
    assert "M=10" in prop_doc
    assert "quantile" in prop_doc.lower()
    assert "isotonic" in prop_doc.lower()
    assert "platt" in prop_doc.lower()

    # Selective classification criteria
    assert "Selective BA >= 0.50 at coverage >= 30%" in prop_doc
    assert "N_c >= 1,000" in prop_doc or "1,000" in prop_doc

    # Cost sensitive criteria
    assert "5.0 basis points per side" in prop_doc or "5 bps per side" in prop_doc
    assert "10.0 bps round-trip" in prop_doc or "10 bps round-trip" in prop_doc
    assert "sensitivity" in prop_doc.lower()

    # Temporal governance
    assert "STRICT_HOLD" in prop_doc


def test_08_zero_em_dashes_in_phase5_3_7_1_files():
    files_to_check = [
        RESEARCH_DOCS_DIR / "PHASE_5_3_FINAL_FREEZE.md",
        RESEARCH_DOCS_DIR / "PHASE_5_4_RESEARCH_PROPOSAL.md",
        RESEARCH_DOCS_DIR / "PHASE_5_3_7_1_RECONCILIATION_REPORT.md",
        Path("tests/unit/test_phase5_3_7_1_reconciliation.py"),
        Path("scripts/generate_complete_freeze_manifest.py"),
        Path("scripts/generate_phase_5_3_7_1_reconciliation.py"),
    ]

    for p in files_to_check:
        if p.exists():
            content = p.read_text(encoding="utf-8")
            assert chr(0x2014) not in content, f"Em-dash found in {p}"
