"""
QUANTUM PHASE 5.4.4: UNIT TEST SUITE
Statistical Inference Correction & Selective Policy Validation Tests
"""

import json
from pathlib import Path
import pytest

OUTPUT_DIR = Path("artifacts/phase_5_4/phase_5_4_4")
DOCS_DIR = Path("docs/research")

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"
]

COVERAGE_GRID = [1.0, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]
BLOCK_LENGTHS = [12, 24, 48, 96]


def test_01_all_deliverables_exist():
    """Verify all 10 required deliverables exist in artifacts and docs."""
    required_artifacts = [
        "PHASE_5_4_4_BLOCK_BOOTSTRAP_RESULTS.json",
        "PHASE_5_4_4_RANDOM_ABSTENTION_RESULTS.json",
        "PHASE_5_4_4_MULTIPLE_TESTING_RESULTS.json",
        "PHASE_5_4_4_RISK_COVERAGE_RESULTS.json",
        "PHASE_5_4_4_AURCC_AUDIT.json",
        "PHASE_5_4_4_CLASS_SELECTION_BIAS_RESULTS.json",
        "PHASE_5_4_4_DIRECTIONAL_RANKING_DIAGNOSTICS.json",
        "PHASE_5_4_4_REPRODUCIBILITY_MANIFEST.json",
        "PHASE_5_4_4_HASH_MANIFEST.json",
        "PHASE_5_4_4_STATISTICAL_CORRECTION_REPORT.md",
    ]
    for fname in required_artifacts:
        fpath = OUTPUT_DIR / fname
        assert fpath.exists(), f"Missing required artifact: {fpath}"
        assert fpath.stat().st_size > 0, f"Artifact is empty: {fpath}"

    docs_report = DOCS_DIR / "PHASE_5_4_4_STATISTICAL_CORRECTION_REPORT.md"
    assert docs_report.exists(), f"Missing report in docs/research: {docs_report}"
    assert docs_report.stat().st_size > 0, f"Docs report is empty: {docs_report}"


def test_02_block_bootstrap_invariants():
    """Verify Moving Block Bootstrap across {12, 24, 48, 96} bars."""
    path = OUTPUT_DIR / "PHASE_5_4_4_BLOCK_BOOTSTRAP_RESULTS.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    instruments = data["instruments"]
    assert len(instruments) == 11, f"Expected 11 instruments, got {len(instruments)}"

    for sym in SYMBOLS:
        assert sym in instruments, f"Instrument {sym} missing from MBB results"
        blocks = instruments[sym]["block_evaluations"]
        assert len(blocks) == 4, f"Expected 4 block sizes for {sym}, got {len(blocks)}"

        for b in BLOCK_LENGTHS:
            b_key = f"block_{b}_bars"
            assert b_key in blocks, f"Block {b_key} missing for {sym}"
            b_data = blocks[b_key]

            # Linear metrics checks
            for metric in ["delta_brier", "delta_log_loss"]:
                m_data = b_data[metric]
                assert "point_estimate" in m_data
                assert "boot_mean" in m_data
                assert "boot_se" in m_data
                assert m_data["boot_se"] > 0, f"{sym} {metric} SE must be positive"
                assert len(m_data["ci_95"]) == 2
                assert m_data["ci_95"][0] < m_data["ci_95"][1]
                assert m_data["finite_p_value"] > 0, f"P-value cannot be 0: {m_data['finite_p_value']}"

            # ECE check
            assert "delta_ece" in b_data
            assert b_data["delta_ece"]["boot_se"] > 0


def test_03_random_abstention_finite_p_values():
    """Verify random abstention evaluates all coverages with non-zero finite p-values."""
    path = OUTPUT_DIR / "PHASE_5_4_4_RANDOM_ABSTENTION_RESULTS.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    instruments = data["instruments"]
    assert len(instruments) == 11

    for sym in SYMBOLS:
        cov_results = instruments[sym]["coverage_grid_results"]
        assert len(cov_results) == 8, f"Expected 8 coverage tiers for {sym}"

        for record in cov_results:
            cov = record["coverage"]
            p_val = record["comparison"]["finite_empirical_p_value"]
            # At coverage 1.0, analytical p-value is 1.0
            if cov == 1.0:
                assert p_val == 1.0, f"Coverage 1.0 p-value must be 1.0, got {p_val}"
            else:
                assert p_val > 0.0, f"Sub-coverage p-value cannot be 0.0: got {p_val}"
                assert p_val >= 1.0 / (2500 + 1), f"P-value cannot be lower than finite-sample bound 1/(B+1)"


def test_04_multiple_testing_correction_holm():
    """Verify Holm-Bonferroni multiple testing correction across 88 hypotheses."""
    path = OUTPUT_DIR / "PHASE_5_4_4_MULTIPLE_TESTING_RESULTS.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    table = data["hypotheses_table"]
    assert len(table) == 88, f"Expected exactly 88 hypotheses, found {len(table)}"

    # Check ascending sort order of raw p-values
    raw_p_vals = [row["raw_p_value"] for row in table]
    assert raw_p_vals == sorted(raw_p_vals), "Hypotheses must be sorted ascending by raw p-value"

    # Check monotonicity of adjusted p-values
    adj_p_vals = [row["holm_adjusted_p_value"] for row in table]
    for i in range(len(adj_p_vals) - 1):
        assert adj_p_vals[i] <= adj_p_vals[i + 1] + 1e-9, f"Non-monotonic adjusted p-value at rank {i+1}"

    # Check rejection consistency
    for row in table:
        rej = row["reject_null_hypothesis"]
        adj_p = row["holm_adjusted_p_value"]
        if adj_p <= 0.05:
            assert rej is True, f"Rank {row['rank']} with adj p {adj_p} should be rejected"
        else:
            assert rej is False, f"Rank {row['rank']} with adj p {adj_p} should fail to reject"


def test_05_aurcc_audit_validity():
    """Verify AU-RCC values and delta calculations across the fleet."""
    path = OUTPUT_DIR / "PHASE_5_4_4_AURCC_AUDIT.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    instruments = data["instruments"]
    assert len(instruments) == 11

    superior_count = 0
    inferior_count = 0

    for sym in SYMBOLS:
        sym_data = instruments[sym]
        for metric in ["au_rcc_error", "au_rcc_balanced_accuracy", "au_rcc_macro_f1"]:
            assert metric in sym_data
            m_info = sym_data[metric]
            assert 0.0 <= m_info["conf"] <= 1.0
            assert 0.0 <= m_info["rand"] <= 1.0
            expected_delta = round(m_info["conf"] - m_info["rand"], 6)
            assert abs(m_info["delta"] - expected_delta) < 1e-5

        if sym_data["selective_advantage_balanced_accuracy"]:
            superior_count += 1
        else:
            inferior_count += 1

    # In Phase 5.4.3 / 5.4.4, exactly 7 instruments have negative Delta AU-RCC and 4 have positive
    assert superior_count == 7, f"Expected 7 instruments with negative Delta AU-RCC, got {superior_count}"
    assert inferior_count == 4, f"Expected 4 instruments with positive Delta AU-RCC, got {inferior_count}"


def test_06_majority_bias_quantification():
    """Verify class retention ratios and majority bias detection."""
    path = OUTPUT_DIR / "PHASE_5_4_4_CLASS_SELECTION_BIAS_RESULTS.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    instruments = data["instruments"]
    assert len(instruments) == 11

    for sym in ["BNBUSDT", "XRPUSDT", "ADAUSDT", "AVAXUSDT"]:
        bias_records = instruments[sym]["coverage_bias_evaluations"]
        cov20_record = bias_records[-1]  # 20% coverage
        assert cov20_record["coverage"] == 0.2
        assert cov20_record["disparity_ratio"] > 1.0
        assert cov20_record["bias_detected"] is True, f"Majority bias must be detected for {sym}"


def test_07_four_diagnostic_ranking_policies():
    """Verify all 4 policies evaluated on Segment 2 and Segment 3."""
    path = OUTPUT_DIR / "PHASE_5_4_4_DIRECTIONAL_RANKING_DIAGNOSTICS.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    expected_policies = [
        "Policy_A_Global_Max",
        "Policy_B_Directional_Confidence",
        "Policy_C_Directional_Margin",
        "Policy_D_Directional_Mass",
    ]

    for segment in ["selection_data_segment_2", "evaluation_data_segment_3"]:
        seg_data = data[segment]
        assert len(seg_data) == 11
        for sym in SYMBOLS:
            sym_pols = seg_data[sym]["policies"]
            for pol in expected_policies:
                assert pol in sym_pols, f"Missing {pol} for {sym} in {segment}"
                assert "au_rcc_balanced_accuracy" in sym_pols[pol]
                assert "delta_ba_span" in sym_pols[pol]


def test_08_fleet_classification_integrity():
    """Verify mutually exclusive classification into 4 categories."""
    path = OUTPUT_DIR / "PHASE_5_4_4_REPRODUCIBILITY_MANIFEST.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    classification = data["fleet_classification_summary"]
    assert len(classification) == 11

    valid_categories = {
        "CONFIDENCE_SELECTION_SUPERIOR",
        "RANDOM_BASELINE_SUPERIOR",
        "NO_SIGNIFICANT_DIFFERENCE",
        "INSUFFICIENT_CLASS_SUPPORT",
    }

    counts = {cat: 0 for cat in valid_categories}
    for sym in SYMBOLS:
        cat = classification[sym]["classification"]
        assert cat in valid_categories, f"Invalid category {cat} for {sym}"
        counts[cat] += 1

    assert counts["CONFIDENCE_SELECTION_SUPERIOR"] == 6
    assert counts["RANDOM_BASELINE_SUPERIOR"] == 4
    assert counts["INSUFFICIENT_CLASS_SUPPORT"] == 1
    assert counts["NO_SIGNIFICANT_DIFFERENCE"] == 0


def test_09_resource_and_reproducibility():
    """Verify resource constraints and freeze compliance."""
    path = OUTPUT_DIR / "PHASE_5_4_4_REPRODUCIBILITY_MANIFEST.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    hw = data["hardware_and_resource_conformance"]
    assert hw["thread_limits_enforced"]["compliant"] is True
    assert hw["ram_consumption_mb"]["compliant"] is True
    assert hw["ram_consumption_mb"]["peak_rss_mb"] < 1024.0

    gov = data["governance_and_freeze_adherence"]
    assert gov["zero_model_retraining"] is True
    assert gov["frozen_b4_models_unmodified"] is True
    assert gov["prospective_holdout_untouched"] is True
    assert gov["retrospective_label_fold_5_enforced"] is True


def test_10_zero_em_dashes():
    """Strictly verify zero em dashes across all Phase 5.4.4 deliverables."""
    files_to_check = [
        OUTPUT_DIR / "PHASE_5_4_4_BLOCK_BOOTSTRAP_RESULTS.json",
        OUTPUT_DIR / "PHASE_5_4_4_RANDOM_ABSTENTION_RESULTS.json",
        OUTPUT_DIR / "PHASE_5_4_4_MULTIPLE_TESTING_RESULTS.json",
        OUTPUT_DIR / "PHASE_5_4_4_RISK_COVERAGE_RESULTS.json",
        OUTPUT_DIR / "PHASE_5_4_4_AURCC_AUDIT.json",
        OUTPUT_DIR / "PHASE_5_4_4_CLASS_SELECTION_BIAS_RESULTS.json",
        OUTPUT_DIR / "PHASE_5_4_4_DIRECTIONAL_RANKING_DIAGNOSTICS.json",
        OUTPUT_DIR / "PHASE_5_4_4_REPRODUCIBILITY_MANIFEST.json",
        OUTPUT_DIR / "PHASE_5_4_4_HASH_MANIFEST.json",
        OUTPUT_DIR / "PHASE_5_4_4_STATISTICAL_CORRECTION_REPORT.md",
        DOCS_DIR / "PHASE_5_4_4_STATISTICAL_CORRECTION_REPORT.md",
        Path(__file__),
    ]

    for fpath in files_to_check:
        assert fpath.exists(), f"File {fpath} does not exist"
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        assert chr(0x2014) not in content, f"Em dash found in {fpath}!"
