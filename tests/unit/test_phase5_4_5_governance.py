"""
QUANTUM PHASE 5.4.5: UNIT TEST SUITE
Final Statistical Governance Reconciliation Tests
"""

import json
from pathlib import Path
import pytest

OUTPUT_DIR = Path("artifacts/phase_5_4/phase_5_4_5")
DOCS_DIR = Path("docs/research")

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"
]


def test_01_all_phase_5_4_5_deliverables_exist():
    """Verify all required deliverables exist in artifacts and docs."""
    required_artifacts = [
        "PHASE_5_4_5_MULTIPLE_TESTING_FAMILY_REGISTRY.json",
        "PHASE_5_4_5_MONTE_CARLO_RESOLUTION_AUDIT.json",
        "PHASE_5_4_5_EXTENDED_MONTE_CARLO_RESULTS.json",
        "PHASE_5_4_5_AURCC_FLEET_RECLASSIFICATION.json",
        "PHASE_5_4_5_RETROSPECTIVE_POLICY_ROBUSTNESS.json",
        "PHASE_5_4_5_SELECTION_BIAS_RECONCILIATION.json",
        "PHASE_5_4_5_CALIBRATION_BOOTSTRAP_RECONCILIATION.json",
        "PHASE_5_4_5_ARTIFACT_INTEGRITY_AUDIT.json",
        "PHASE_5_4_5_HASH_MANIFEST.json",
        "PHASE_5_4_5_FINAL_GOVERNANCE_REPORT.md",
    ]
    for fname in required_artifacts:
        fpath = OUTPUT_DIR / fname
        assert fpath.exists(), f"Missing required artifact: {fpath}"
        assert fpath.stat().st_size > 0, f"Artifact is empty: {fpath}"

    docs_report = DOCS_DIR / "PHASE_5_4_5_FINAL_GOVERNANCE_REPORT.md"
    assert docs_report.exists(), f"Missing report in docs/research: {docs_report}"
    assert docs_report.stat().st_size > 0, f"Docs report is empty: {docs_report}"


def test_02_multiple_testing_family_registry_invariants():
    """Verify multiple testing family formal registry."""
    path = OUTPUT_DIR / "PHASE_5_4_5_MULTIPLE_TESTING_FAMILY_REGISTRY.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    families = data["families"]
    assert "FAM_01_GLOBAL_ABSTENTION_88" in families
    assert "FAM_02_DERIVED_INSTRUMENT_SUBSET_7" in families
    assert "FAM_03_AURCC_DELTA_TEST" in families

    fam1 = families["FAM_01_GLOBAL_ABSTENTION_88"]
    assert fam1["hypothesis_count"] == 88
    assert fam1["classification"] == "PREDECLARED_GLOBAL_FAMILY"
    assert len(data["hypotheses_registry"]) == 88

    fam2 = families["FAM_02_DERIVED_INSTRUMENT_SUBSET_7"]
    assert fam2["classification"] == "DERIVED_SUBSET_NOT_INDEPENDENT_FAMILY"

    fam3 = families["FAM_03_AURCC_DELTA_TEST"]
    assert fam3["classification"] == "INSUFFICIENT_EVIDENCE"


def test_03_extended_monte_carlo_resampling_validity():
    """Verify extended Monte Carlo resampling (B=50,000) for boundary hypotheses."""
    path = OUTPUT_DIR / "PHASE_5_4_5_EXTENDED_MONTE_CARLO_RESULTS.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    detailed = data["boundary_hypotheses_detailed_results"]
    assert len(detailed) == 12, f"Expected 12 boundary hypotheses, got {len(detailed)}"

    for row in detailed:
        assert row["total_repetitions"] == 50000
        assert row["extended_raw_p_value"] > 0.0
        expected_p = (row["exceedances_count"] + 1) / 50001
        assert abs(row["extended_raw_p_value"] - expected_p) < 1e-6, f"Mismatch in extended p: {row['extended_raw_p_value']} vs {expected_p}"

    recomputed = data["recomputed_holm_correction_global_88_family"]
    assert recomputed["total_hypotheses"] == 88
    assert recomputed["recomputed_rejections_count"] == 12
    assert recomputed["rejection_consistency"] is True


def test_04_aurcc_fleet_reclassification_schema():
    """Verify AU-RCC fleet reclassification across 5 categories."""
    path = OUTPUT_DIR / "PHASE_5_4_5_AURCC_FLEET_RECLASSIFICATION.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    counts = data["fleet_summary_counts"]
    assert counts["STATISTICALLY_SUPERIOR"] == 4
    assert counts["LOWER_AURCC_OBSERVED"] == 2
    assert counts["RANDOM_BASELINE_SUPERIOR"] == 4
    assert counts["INSUFFICIENT_CLASS_SUPPORT"] == 1
    assert counts["NO_SIGNIFICANT_DIFFERENCE"] == 0

    instruments = data["instruments"]
    assert len(instruments) == 11

    # BTC and SOL must NOT be claimed as statistically superior
    assert instruments["BTCUSDT"]["reconciled_category"] == "LOWER_AURCC_OBSERVED"
    assert instruments["SOLUSDT"]["reconciled_category"] == "LOWER_AURCC_OBSERVED"

    # Statistically superior 4
    for sym in ["ETHUSDT", "DOGEUSDT", "LINKUSDT", "LTCUSDT"]:
        assert instruments[sym]["reconciled_category"] == "STATISTICALLY_SUPERIOR"
        assert instruments[sym]["holm_rejected_subcoverages_count"] > 0

    # Random baseline superior 4
    for sym in ["BNBUSDT", "XRPUSDT", "ADAUSDT", "AVAXUSDT"]:
        assert instruments[sym]["reconciled_category"] == "RANDOM_BASELINE_SUPERIOR"

    # Insufficient class support
    assert instruments["XMRUSDT"]["reconciled_category"] == "INSUFFICIENT_CLASS_SUPPORT"


def test_05_retrospective_temporal_robustness_labeling():
    """Verify retrospective temporal robustness labeling and full policy visibility."""
    path = OUTPUT_DIR / "PHASE_5_4_5_RETROSPECTIVE_POLICY_ROBUSTNESS.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    assert data["analysis_classification"] == "RETROSPECTIVE_TEMPORAL_ROBUSTNESS_ANALYSIS"

    instruments = data["instruments"]
    assert len(instruments) == 11

    for sym in SYMBOLS:
        item = instruments[sym]
        assert "policy_selected_on_segment_2" in item
        pols = item["all_policies_evaluation"]
        assert len(pols) == 4, f"All 4 policies must be visible for {sym}"
        pol_names = [p["policy_name"] for p in pols]
        assert "Policy_A_Global_Max" in pol_names
        assert "Policy_B_Directional_Confidence" in pol_names
        assert "Policy_C_Directional_Margin" in pol_names
        assert "Policy_D_Directional_Mass" in pol_names


def test_06_majority_class_selection_bias_boundaries():
    """Verify selection bias mechanism diagnosis boundaries."""
    path = OUTPUT_DIR / "PHASE_5_4_5_SELECTION_BIAS_RECONCILIATION.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    assert data["analysis_classification"] == "SELECTION_BIAS_MECHANISM_DIAGNOSIS"
    bounds = data["governance_boundaries"]
    assert bounds["no_causal_mechanism_solved_claim"] is True
    assert bounds["no_production_ready_policy_claim"] is True
    assert bounds["no_proven_directional_alpha_claim"] is True

    pillars = data["four_evidence_pillars_separation"]
    assert len(pillars) == 4


def test_07_calibration_bootstrap_btc_doge_ece():
    """Verify calibration bootstrap interpretation and ECE intervals crossing zero."""
    path = OUTPUT_DIR / "PHASE_5_4_5_CALIBRATION_BOOTSTRAP_RECONCILIATION.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    assert data["governance_terminology"] == "ROBUST_ACROSS_TESTED_BLOCK_LENGTHS"

    instruments = data["instruments"]
    assert len(instruments) == 11

    # Multiple instruments cross zero at block 24 (e.g. ETH, BNB, XRP, ADA, AVAX, LINK, LTC)
    zero_crossing_instruments = [
        sym for sym in SYMBOLS if instruments[sym]["delta_ece_block_24"]["ci_crosses_zero"]
    ]
    assert len(zero_crossing_instruments) >= 5, f"Expected at least 5 instruments crossing zero for ECE, got {len(zero_crossing_instruments)}"
    assert "ETHUSDT" in zero_crossing_instruments
    assert "LINKUSDT" in zero_crossing_instruments

    # Document BTC and DOGE ECE intervals
    for sym in ["BTCUSDT", "DOGEUSDT"]:
        assert "delta_ece_block_24" in instruments[sym]
        assert "ci_95" in instruments[sym]["delta_ece_block_24"]

    # Brier and Log Loss must be robust across all 4 block lengths for all instruments
    for sym in SYMBOLS:
        assert instruments[sym]["delta_brier_block_24"]["robust_across_all_4_blocks"] is True
        assert instruments[sym]["delta_log_loss_block_24"]["robust_across_all_4_blocks"] is True


def test_08_artifact_integrity_and_holdout_protection():
    """Verify artifact integrity and prospective holdout protection."""
    path = OUTPUT_DIR / "PHASE_5_4_5_ARTIFACT_INTEGRITY_AUDIT.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    assert data["status"] == "PASS"
    assert data["frozen_models_audited_count"] == 55
    assert data["frozen_model_hash_mismatches"] == 0
    assert data["materialized_parquet_mismatches"] == 0
    assert data["phase_5_4_4_artifact_mismatches"] == 0
    assert data["prospective_holdout_protected"] is True


def test_09_hash_manifest_completeness():
    """Verify hash manifest covers all phase 5.4.5 deliverables."""
    path = OUTPUT_DIR / "PHASE_5_4_5_HASH_MANIFEST.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    artifacts = data["artifacts"]
    assert len(artifacts) >= 9

    for fname, info in artifacts.items():
        fpath = OUTPUT_DIR / fname
        assert fpath.exists(), f"Artifact in manifest missing from disk: {fpath}"
        assert "sha256" in info
        assert "size_bytes" in info


def test_10_zero_em_dashes():
    """Strictly verify zero em dashes across all Phase 5.4.5 deliverables."""
    files_to_check = [
        OUTPUT_DIR / "PHASE_5_4_5_MULTIPLE_TESTING_FAMILY_REGISTRY.json",
        OUTPUT_DIR / "PHASE_5_4_5_MONTE_CARLO_RESOLUTION_AUDIT.json",
        OUTPUT_DIR / "PHASE_5_4_5_EXTENDED_MONTE_CARLO_RESULTS.json",
        OUTPUT_DIR / "PHASE_5_4_5_AURCC_FLEET_RECLASSIFICATION.json",
        OUTPUT_DIR / "PHASE_5_4_5_RETROSPECTIVE_POLICY_ROBUSTNESS.json",
        OUTPUT_DIR / "PHASE_5_4_5_SELECTION_BIAS_RECONCILIATION.json",
        OUTPUT_DIR / "PHASE_5_4_5_CALIBRATION_BOOTSTRAP_RECONCILIATION.json",
        OUTPUT_DIR / "PHASE_5_4_5_ARTIFACT_INTEGRITY_AUDIT.json",
        OUTPUT_DIR / "PHASE_5_4_5_HASH_MANIFEST.json",
        OUTPUT_DIR / "PHASE_5_4_5_FINAL_GOVERNANCE_REPORT.md",
        DOCS_DIR / "PHASE_5_4_5_FINAL_GOVERNANCE_REPORT.md",
        Path(__file__),
    ]

    for fpath in files_to_check:
        assert fpath.exists(), f"File {fpath} does not exist"
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        assert chr(0x2014) not in content, f"Em dash (\\u2014) found in {fpath}!"
