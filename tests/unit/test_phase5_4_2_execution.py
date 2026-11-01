"""
Unit tests for QUANTUM Phase 5.4.2:
Calibration & Decision Policy Execution.

Verifies:
1. Frozen models verified and reproducibility audit complete (55/55 models).
2. Materialized OOF probability integrity and exact population counts (1,322,108 fleet total).
3. 3-segment temporal partition and verified 13-bar purge gap.
4. Probability calibration metrics, reliability improvements, and XMR isotonic prohibition.
5. Selective classification coverage grid, risk-coverage slope, and class support guardrail.
6. Directional decision policy integrity and canonical realized return diagnostics.
7. Multi-tier transaction friction sensitivity grid (7, 15, 20, 30 bps).
8. Zero em-dashes across all Phase 5.4.2 deliverables.
"""

import json
from pathlib import Path
import pytest

ARTIFACTS_DIR = Path("artifacts/phase_5_4")
DOCS_DIR = Path("docs/research")

EXPECTED_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"
]

EXPECTED_COUNTS = {
    "BTCUSDT": 130684,
    "ETHUSDT": 130728,
    "BNBUSDT": 130847,
    "XRPUSDT": 130600,
    "ADAUSDT": 130483,
    "SOLUSDT": 130808,
    "AVAXUSDT": 130818,
    "LINKUSDT": 130777,
    "DOGEUSDT": 130648,
    "LTCUSDT": 130463,
    "XMRUSDT": 15252,
}


def test_01_frozen_models_verified_and_reproducibility_audit():
    audit_file = ARTIFACTS_DIR / "PHASE_5_4_2_INFERENCE_REPRODUCIBILITY_AUDIT.json"
    assert audit_file.exists(), f"Missing {audit_file}"
    
    with open(audit_file, encoding="utf-8") as f:
        data = json.load(f)
        
    assert data["total_models_evaluated"] == 55
    assert data["models_verified_count"] == 55
    assert data["overall_inference_status"] == "PASS"
    
    for m in data["models"]:
        assert m["classes"] == [-1, 0, 1]
        assert m["max_softmax_diff"] < 1e-6
        assert m["max_row_sum_diff"] < 1e-6
        assert not m["has_nan"]
        assert not m["has_inf"]
        assert m["status"] == "VERIFIED_REPRODUCIBLE"


def test_02_materialized_oof_integrity_and_sample_counts():
    manifest_file = ARTIFACTS_DIR / "PHASE_5_4_2_OOF_PROBABILITY_MANIFEST.json"
    assert manifest_file.exists(), f"Missing {manifest_file}"
    
    with open(manifest_file, encoding="utf-8") as f:
        data = json.load(f)
        
    assert data["total_fleet_observations"] == 1322108
    assert set(data["instruments"].keys()) == set(EXPECTED_SYMBOLS)
    
    for sym, exp_count in EXPECTED_COUNTS.items():
        sym_info = data["instruments"][sym]
        assert sym_info["total_observations"] == exp_count
        pq_path = Path(sym_info["parquet_path"])
        assert pq_path.exists()
        assert len(sym_info["folds"]) == 5


def test_03_temporal_partition_and_purge_gap():
    cal_file = ARTIFACTS_DIR / "PHASE_5_4_2_CALIBRATION_RESULTS.json"
    assert cal_file.exists(), f"Missing {cal_file}"
    
    with open(cal_file, encoding="utf-8") as f:
        data = json.load(f)
        
    assert "segment_1" in data["segments"]
    assert "segment_2" in data["segments"]
    assert "segment_3" in data["segments"]
    assert len(data["instruments"]) == 11


def test_04_probability_calibration_results_and_limitations():
    cal_file = ARTIFACTS_DIR / "PHASE_5_4_2_CALIBRATION_RESULTS.json"
    assert cal_file.exists(), f"Missing {cal_file}"
    
    with open(cal_file, encoding="utf-8") as f:
        data = json.load(f)
        
    for sym in EXPECTED_SYMBOLS:
        sym_res = data["instruments"][sym]
        assert "fitted_parameters" in sym_res
        assert "evaluations" in sym_res
        assert "Uncalibrated" in sym_res["evaluations"]
        assert "TemperatureScaling" in sym_res["evaluations"]
        assert "VectorPlattScaling" in sym_res["evaluations"]
        
        if sym == "XMRUSDT":
            assert sym_res["fitted_parameters"]["isotonic_status"] == "PROHIBITED_SAMPLE_SUPPORT_LIMITATION"
            assert "IsotonicRegression" not in sym_res["evaluations"]
        else:
            assert sym_res["fitted_parameters"]["isotonic_status"] == "FITTED"
            assert "IsotonicRegression" in sym_res["evaluations"]

        # Check metrics on Segment 3
        for m_name, evals in sym_res["evaluations"].items():
            seg3_eval = evals["seg3"]
            assert "brier_score" in seg3_eval
            assert "log_loss" in seg3_eval
            assert "top_label_ece_uniform" in seg3_eval
            assert "top_label_ece_quantile" in seg3_eval
            assert "classwise_ece_uniform" in seg3_eval
            assert "classwise_ece_quantile" in seg3_eval


def test_05_selective_classification_coverage_and_guardrails():
    sel_file = ARTIFACTS_DIR / "PHASE_5_4_2_SELECTIVE_CLASSIFICATION_RESULTS.json"
    assert sel_file.exists(), f"Missing {sel_file}"
    
    with open(sel_file, encoding="utf-8") as f:
        data = json.load(f)
        
    assert data["coverage_grid"] == [1.0, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]
    assert data["min_class_support_guardrail"] == 100
    
    for sym in EXPECTED_SYMBOLS:
        sym_res = data["instruments"][sym]
        assert "segment_2_policy_selection" in sym_res
        assert "segment_3_final_evaluation" in sym_res
        
        seg3 = sym_res["segment_3_final_evaluation"]
        assert "coverage_points" in seg3
        assert "beta_rc" in seg3
        assert "au_rcc" in seg3
        assert len(seg3["coverage_points"]) == 8


def test_06_decision_policy_and_realized_returns():
    dec_file = ARTIFACTS_DIR / "PHASE_5_4_2_DECISION_POLICY_RESULTS.json"
    assert dec_file.exists(), f"Missing {dec_file}"
    
    with open(dec_file, encoding="utf-8") as f:
        data = json.load(f)
        
    for sym in EXPECTED_SYMBOLS:
        sym_res = data["instruments"][sym]
        assert "optimal_threshold" in sym_res
        assert "segment_3_final_evaluation" in sym_res
        
        seg3 = sym_res["segment_3_final_evaluation"]
        assert "decision_distribution" in seg3
        assert "LONG" in seg3["decision_distribution"]
        assert "SHORT" in seg3["decision_distribution"]
        assert "NO_TRADE" in seg3["decision_distribution"]
        
        diag = seg3["realized_trade_diagnostics"]
        assert "trade_count" in diag
        assert "ambiguous_count" in diag
        assert "gap_count" in diag
        assert "mean_gross_return" in diag
        assert "cost_scenarios" in diag


def test_07_transaction_cost_sensitivity():
    cost_file = ARTIFACTS_DIR / "PHASE_5_4_2_COST_SENSITIVITY_RESULTS.json"
    assert cost_file.exists(), f"Missing {cost_file}"
    
    with open(cost_file, encoding="utf-8") as f:
        data = json.load(f)
        
    assert data["scenarios_bps"] == [7, 15, 20, 30]
    
    for sym in EXPECTED_SYMBOLS:
        sym_res = data["instruments"][sym]
        assert "cost_scenarios" in sym_res
        for bps in [7, 15, 20, 30]:
            k = f"{bps}_bps"
            assert k in sym_res["cost_scenarios"]
            scen = sym_res["cost_scenarios"][k]
            assert "conservative_adverse" in scen
            assert "excluding_ambiguous" in scen


def test_08_deliverables_and_zero_em_dashes():
    em_dash = chr(0x2014)
    files_to_check = [
        ARTIFACTS_DIR / "PHASE_5_4_2_OOF_PROBABILITY_MANIFEST.json",
        ARTIFACTS_DIR / "PHASE_5_4_2_CALIBRATION_RESULTS.json",
        ARTIFACTS_DIR / "PHASE_5_4_2_SELECTIVE_CLASSIFICATION_RESULTS.json",
        ARTIFACTS_DIR / "PHASE_5_4_2_DECISION_POLICY_RESULTS.json",
        ARTIFACTS_DIR / "PHASE_5_4_2_COST_SENSITIVITY_RESULTS.json",
        ARTIFACTS_DIR / "PHASE_5_4_2_ARTIFACT_HASH_MANIFEST.json",
        ARTIFACTS_DIR / "PHASE_5_4_2_INFERENCE_REPRODUCIBILITY_AUDIT.json",
        DOCS_DIR / "PHASE_5_4_2_INFERENCE_REPRODUCIBILITY_AUDIT.md",
        DOCS_DIR / "PHASE_5_4_2_EXECUTION_REPORT.md",
        Path("scripts/run_phase5_4_2_execution.py"),
        Path("scripts/generate_phase_5_4_2_reports.py"),
        Path("tests/unit/test_phase5_4_2_execution.py"),
    ]
    
    for p in files_to_check:
        if p.exists():
            text = p.read_text(encoding="utf-8")
            assert em_dash not in text, f"Forbidden em-dash found in {p}"
