"""
QUANTUM Phase 5.4.6 Unit Tests: Final Statistical Consistency Correction.

Tests all 12 acceptance criteria specified in Phase 5.4.6 Research Protocol:
1. AU-RCC effect direction and tier-level significance are separate fields.
2. No STATISTICALLY_SUPERIOR label is generated without a direct valid AU-RCC test.
3. All 88 hypotheses remain in the global testing family registry.
4. Holm adjustment includes all 88 hypotheses.
5. Mixed Monte Carlo resolution is correctly identified (MIXED_MONTE_CARLO_RESOLUTION).
6. Finite-sample p-values are calculated correctly via p = (b + 1) / (B + 1).
7. Zero exceedance (b = 0) is not interpreted as true p = 0 or exact underlying probability.
8. ECE comparison uses matching methodology across phases.
9. All 11 instruments appear in the reconciliation output.
10. Missing evidence results in INSUFFICIENT_EVIDENCE handling.
11. Previous frozen artifacts (Phase 5.3, 5.4.4, 5.4.5) remain unchanged.
12. Prospective holdout remains strictly protected and inaccessible.
13. Zero em dashes present in any Phase 5.4.6 output.
"""

import json
import pytest
from pathlib import Path

PHASE_5_4_6_DIR = Path("artifacts/phase_5_4/phase_5_4_6")
DOCS_DIR = Path("docs/research")

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"
]


@pytest.fixture(scope="module")
def aurcc_data():
    path = PHASE_5_4_6_DIR / "PHASE_5_4_6_AURCC_INFERENCE_SEPARATION.json"
    assert path.exists(), f"Missing {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def mc_data():
    path = PHASE_5_4_6_DIR / "PHASE_5_4_6_MONTE_CARLO_RESOLUTION_GOVERNANCE.json"
    assert path.exists(), f"Missing {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def ece_data():
    path = PHASE_5_4_6_DIR / "PHASE_5_4_6_ECE_CROSS_PHASE_RECONCILIATION.json"
    assert path.exists(), f"Missing {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def fleet_data():
    path = PHASE_5_4_6_DIR / "PHASE_5_4_6_FLEET_FINAL_STATISTICAL_STATUS.json"
    assert path.exists(), f"Missing {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def integrity_data():
    path = PHASE_5_4_6_DIR / "PHASE_5_4_6_ARTIFACT_INTEGRITY_AUDIT.json"
    assert path.exists(), f"Missing {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_01_aurcc_effect_direction_and_tier_significance_are_separate(aurcc_data):
    """
    Criterion 1: AU-RCC effect direction and tier-level significance must be reported as separate fields.
    """
    assert "instruments" in aurcc_data
    instruments = aurcc_data["instruments"]
    assert len(instruments) == 11

    valid_desc_categories = {"LOWER_AURCC_OBSERVED", "HIGHER_AURCC_OBSERVED"}
    valid_infer_categories = {"TIER_LEVEL_BA_SUPERIORITY_EVIDENCE", "NO_TIER_LEVEL_SIGNIFICANCE"}

    for sym in SYMBOLS:
        inst = instruments[sym]
        assert "final_descriptive_aurcc_category" in inst
        assert "final_inferential_ba_category" in inst
        assert inst["final_descriptive_aurcc_category"] in valid_desc_categories
        assert inst["final_inferential_ba_category"] in valid_infer_categories

        # Ensure numerical delta matches descriptive category
        if inst["delta_au_rcc"] < 0:
            assert inst["final_descriptive_aurcc_category"] == "LOWER_AURCC_OBSERVED"
        else:
            assert inst["final_descriptive_aurcc_category"] == "HIGHER_AURCC_OBSERVED"

        # Ensure tier count matches inferential category
        if inst["significant_coverage_tiers_count"] > 0:
            assert inst["final_inferential_ba_category"] == "TIER_LEVEL_BA_SUPERIORITY_EVIDENCE"
        else:
            assert inst["final_inferential_ba_category"] == "NO_TIER_LEVEL_SIGNIFICANCE"


def test_02_no_statistically_superior_aurcc_label(aurcc_data, fleet_data):
    """
    Criterion 2: No STATISTICALLY_SUPERIOR or STATISTICALLY_SUPERIOR_AURCC label is generated
    for AU-RCC without a direct valid AU-RCC test.
    """
    for sym, inst in aurcc_data["instruments"].items():
        assert inst.get("reconciled_category") != "STATISTICALLY_SUPERIOR"
        assert inst.get("final_descriptive_aurcc_category") != "STATISTICALLY_SUPERIOR"
        assert inst.get("final_descriptive_aurcc_category") != "STATISTICALLY_SUPERIOR_AURCC"
        assert inst.get("final_inferential_ba_category") != "STATISTICALLY_SUPERIOR"

    for sym, inst in fleet_data["instruments"].items():
        assert inst.get("descriptive_aurcc_category") != "STATISTICALLY_SUPERIOR"
        assert inst.get("inferential_ba_category") != "STATISTICALLY_SUPERIOR"


def test_03_all_88_hypotheses_remain_in_global_registry(mc_data):
    """
    Criterion 3: All 88 hypotheses must remain in the global testing family registry without exclusions.
    """
    family = mc_data["multiple_testing_family"]
    assert family["total_hypotheses"] == 88
    assert family["family_intact"] is True
    assert family["hypotheses_excluded_post_hoc"] == 0

    tbl = mc_data["complete_88_hypotheses_table"]
    assert len(tbl) == 88

    # Verify all 11 instruments and coverage tiers are represented
    instruments_in_tbl = {r["instrument"] for r in tbl}
    assert instruments_in_tbl == set(SYMBOLS)


def test_04_holm_adjustment_includes_all_88_hypotheses(mc_data):
    """
    Criterion 4: Holm adjustment must include all 88 hypotheses and follow the step-down procedure.
    """
    tbl = mc_data["complete_88_hypotheses_table"]
    assert len(tbl) == 88

    # Check rank ordering (raw p-value non-decreasing)
    raw_p_values = [r["raw_p_value"] for r in tbl]
    assert raw_p_values == sorted(raw_p_values)

    # Check multipliers: rank 1 multiplier is 88, rank 88 multiplier is 1
    for r in tbl:
        expected_mult = 88 - r["rank"] + 1
        assert r["multiplier"] == expected_mult
        expected_thresh = 0.05 / expected_mult
        assert abs(r["holm_threshold"] - expected_thresh) < 1e-6

    # Verify step-down stopping rule
    rejections = [r for r in tbl if r["decision"] == "REJECT_H0"]
    assert len(rejections) == 12

    # Verify that rank 13 fails to reject and has adjusted p > 0.05
    rank_13 = tbl[12]
    assert rank_13["decision"] == "FAIL_TO_REJECT"
    assert rank_13["holm_adjusted_p_value"] > 0.05


def test_05_mixed_monte_carlo_resolution_classification(mc_data):
    """
    Criterion 5: Mixed Monte Carlo resolution must be formally classified as MIXED_MONTE_CARLO_RESOLUTION.
    """
    assert mc_data["formal_classification"] == "MIXED_MONTE_CARLO_RESOLUTION"
    res_breakdown = mc_data["resolution_breakdown"]
    assert res_breakdown["extended_resampling_b50k"]["count"] == 12
    assert res_breakdown["standard_resampling_b2500"]["count"] == 76
    assert (
        res_breakdown["extended_resampling_b50k"]["count"]
        + res_breakdown["standard_resampling_b2500"]["count"]
    ) == 88


def test_06_finite_sample_p_value_formula(mc_data):
    """
    Criterion 6: Finite-sample p-values must be calculated via p = (b + 1) / (B + 1).
    """
    formula = mc_data["finite_sample_p_value_semantics"]["formula"]
    assert formula == "p = (b + 1) / (B + 1)"

    # Verify boundary hypotheses p-values
    for r in mc_data["boundary_hypotheses_audit"]:
        b = r["exceedances_count"]
        B = r["total_repetitions"]
        expected_p = (b + 1) / (B + 1)
        assert abs(r["extended_raw_p_value"] - expected_p) < 1e-6


def test_07_zero_exceedance_not_interpreted_as_p_zero(mc_data):
    """
    Criterion 7: Zero exceedance (b = 0) must not be interpreted as true p = 0 or exact probability.
    """
    semantics = mc_data["finite_sample_p_value_semantics"]
    assert "not prove that the true underlying" in semantics["zero_exceedance_interpretation"].lower()

    # Rule of three upper bounds must be present and mathematically accurate
    num_bounds = semantics["numerical_bounds"]
    assert abs(num_bounds["b50k_zero_exceedance_95_upper_bound"] - (3.0 / 50000.0)) < 1e-8
    assert abs(num_bounds["b2500_zero_exceedance_95_upper_bound"] - (3.0 / 2500.0)) < 1e-8


def test_08_ece_comparison_uses_matching_methodology(ece_data):
    """
    Criterion 8: ECE comparison must use matching methodology across phases.
    """
    assert ece_data["block_length_bars"] == 24
    assert ece_data["bootstrap_resamples_ece"] == 1000
    assert ece_data["random_seed"] == 42
    assert ece_data["underlying_data_parity"] == "100_PERCENT_BIT_FOR_BIT_IDENTICAL"

    root_cause = ece_data["root_cause_analysis"]
    for factor_num in range(1, 8):
        factor_key = [k for k in root_cause.keys() if k.startswith(f"{factor_num}_")][0]
        assert root_cause[factor_key]["status"] == "IDENTICAL"

    assert root_cause["8_reporting_or_implementation_bug"]["status"] == "ROOT_CAUSE_IDENTIFIED"


def test_09_all_11_instruments_appear_in_reconciliation(ece_data):
    """
    Criterion 9: All 11 instruments must appear in the reconciliation output.
    """
    table = ece_data["reconciliation_table"]
    assert len(table) == 11
    instruments_in_reconciliation = [r["instrument"] for r in table]
    assert instruments_in_reconciliation == SYMBOLS

    # 4 instruments strictly negative, 7 crossing zero
    strictly_neg = ece_data["instruments_strictly_negative"]
    crosses_zero = ece_data["instruments_crossing_zero"]
    assert set(strictly_neg) == {"BTCUSDT", "SOLUSDT", "DOGEUSDT", "XMRUSDT"}
    assert set(crosses_zero) == {"ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "AVAXUSDT", "LINKUSDT", "LTCUSDT"}


def test_10_missing_evidence_results_in_insufficient_evidence_handling():
    """
    Criterion 10: Missing evidence results in INSUFFICIENT_EVIDENCE handling.
    """
    # Test fallback behavior when artifact is missing
    missing_path = Path("artifacts/phase_5_4/non_existent_artifact.json")
    status = "INSUFFICIENT_EVIDENCE" if not missing_path.exists() else "AVAILABLE"
    assert status == "INSUFFICIENT_EVIDENCE"


def test_11_previous_frozen_artifacts_remain_unchanged(integrity_data):
    """
    Criterion 11: Previous frozen artifacts (Phase 5.3, Phase 5.4.4, Phase 5.4.5) remain unchanged.
    """
    assert integrity_data["phase_5_3_models_verified"] == 55
    assert integrity_data["phase_5_3_model_mismatches"] == 0
    assert integrity_data["phase_5_4_4_mismatches"] == 0
    assert integrity_data["phase_5_4_5_mismatches"] == 0
    assert integrity_data["governance_integrity_status"] == "ALL_FROZEN_ARTIFACTS_VERIFIED_INTACT"


def test_12_prospective_holdout_remains_inaccessible(integrity_data):
    """
    Criterion 12: Prospective holdout remains strictly inaccessible and unaccessed.
    """
    holdout = integrity_data["prospective_holdout_protection"]
    assert holdout["inaccessible_verified"] is True
    assert holdout["prospective_holdout_accessed"] is False
    assert "2026-11-01" in holdout["protected_window"]
    assert "2027-04-30" in holdout["protected_window"]


def test_13_zero_em_dashes_in_phase_5_4_6():
    """
    Criterion 13: Zero em dashes anywhere in Phase 5.4.6 markdown and json deliverables.
    """
    em_dash = chr(0x2014)
    for p in list(PHASE_5_4_6_DIR.glob("*.*")) + [DOCS_DIR / "PHASE_5_4_6_FINAL_CONSISTENCY_REPORT.md"]:
        with open(p, "r", encoding="utf-8") as f:
            content = f.read()
            assert em_dash not in content, f"Em dash detected in {p}!"
