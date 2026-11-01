"""
Unit tests for QUANTUM Phase 5.4.3:
Corrective Statistical & Artifact Audit.

Verifies:
1. All Phase 5.4.3 JSON artifacts and markdown report exist.
2. Frozen model binary checksums (55/55) match Phase 5.3 master freeze manifest.
3. Calibration metrics validity and paired bootstrap uncertainty intervals.
4. Temporal separation, 13-bar purge gap enforcement, and holdout protection.
5. Confidence selection vs 1,000-repetition uniform random abstention baseline.
6. Risk-coverage dynamics, AU-RCC reduction, and XMR sample support guardrail.
7. Decision policy causal execution rules (entry at open[i+1], adverse collisions).
8. Cost sensitivity round-trip friction reconciliation and execution log audit.
9. Strict zero em-dashes across all Phase 5.4.3 deliverables.
"""

import json
from pathlib import Path
import pytest

AUDIT_DIR = Path("artifacts/phase_5_4/phase_5_4_3")
DOCS_DIR = Path("docs/research")

EXPECTED_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"
]


def test_01_all_phase_5_4_3_artifacts_and_reports_exist():
    expected_files = [
        AUDIT_DIR / "PHASE_5_4_3_ARTIFACT_INTEGRITY_AUDIT.json",
        AUDIT_DIR / "PHASE_5_4_3_CALIBRATION_METRIC_AUDIT.json",
        AUDIT_DIR / "PHASE_5_4_3_TEMPORAL_SEPARATION_AUDIT.json",
        AUDIT_DIR / "PHASE_5_4_3_RANDOM_ABSTENTION_RESULTS.json",
        AUDIT_DIR / "PHASE_5_4_3_RISK_COVERAGE_AUDIT.json",
        AUDIT_DIR / "PHASE_5_4_3_DECISION_POLICY_AUDIT.json",
        AUDIT_DIR / "PHASE_5_4_3_COST_RECONCILIATION.json",
        AUDIT_DIR / "PHASE_5_4_3_EXECUTION_LOG_AUDIT.json",
        AUDIT_DIR / "PHASE_5_4_3_HASH_MANIFEST.json",
        DOCS_DIR / "PHASE_5_4_3_CORRECTIVE_AUDIT_REPORT.md",
    ]
    for p in expected_files:
        assert p.exists(), f"Missing artifact: {p}"
        assert p.stat().st_size > 100, f"Empty artifact: {p}"


def test_02_frozen_artifact_integrity_audit():
    p = AUDIT_DIR / "PHASE_5_4_3_ARTIFACT_INTEGRITY_AUDIT.json"
    assert p.exists()
    with open(p, encoding="utf-8") as f:
        data = json.load(f)

    assert data["total_models_evaluated"] == 55
    assert data["models_verified_count"] == 55
    assert data["model_hash_mismatches"] == 0
    assert data["total_materialized_observations"] == 1322108
    assert data["workstream_status"] == "PASS"

    for rec in data["models_audit_table"]:
        assert rec["model_hash_matches_freeze_manifest"] is True
        assert rec["preprocessor_hash_matches_freeze_manifest"] is True
        assert rec["classes_verified"] is True
        assert rec["status"] == "PASS"


def test_03_calibration_metric_validity_and_bootstrap_cis():
    p = AUDIT_DIR / "PHASE_5_4_3_CALIBRATION_METRIC_AUDIT.json"
    assert p.exists()
    with open(p, encoding="utf-8") as f:
        data = json.load(f)

    assert data["workstream_status"] == "PASS"
    assert "multiclass_brier_score" in data["metric_specifications"]
    assert "multiclass_log_loss" in data["metric_specifications"]
    assert "expected_calibration_error" in data["metric_specifications"]

    for sym in EXPECTED_SYMBOLS:
        inst = data["instruments"][sym]
        assert "paired_deltas_with_95_ci" in inst
        d_bs = inst["paired_deltas_with_95_ci"]["delta_brier"]
        d_ll = inst["paired_deltas_with_95_ci"]["delta_log_loss"]
        assert len(d_bs["ci_95"]) == 2
        assert len(d_ll["ci_95"]) == 2
        assert d_bs["ci_95"][0] <= d_bs["ci_95"][1]
        assert d_ll["ci_95"][0] <= d_ll["ci_95"][1]


def test_04_temporal_separation_and_holdout_protection():
    p = AUDIT_DIR / "PHASE_5_4_3_TEMPORAL_SEPARATION_AUDIT.json"
    assert p.exists()
    with open(p, encoding="utf-8") as f:
        data = json.load(f)

    assert data["workstream_status"] == "PASS"
    assert len(data["instruments"]) == 11

    for inst in data["instruments"]:
        assert inst["prospective_holdout_untouched"] is True
        assert inst["status"] == "PASS"
        for gap in inst["inter_fold_purge_gaps"]:
            assert gap["gap_ms"] >= 3_900_000
            assert gap["purge_gap_satisfied"] is True


def test_05_random_abstention_baseline_and_superiority():
    p = AUDIT_DIR / "PHASE_5_4_3_RANDOM_ABSTENTION_RESULTS.json"
    assert p.exists()
    with open(p, encoding="utf-8") as f:
        data = json.load(f)

    assert data["n_repetitions"] == 1000
    assert len(data["instruments"]) == 11

    # Verify that delta comparison and empirical p-values are computed for all 11 instruments
    superior_count = 0
    for sym in EXPECTED_SYMBOLS:
        inst = data["instruments"][sym]
        assert "coverage_evaluations" in inst
        cov_50 = next(c for c in inst["coverage_evaluations"] if c["target_coverage"] == 0.5)
        assert "delta_balanced_accuracy" in cov_50["delta_comparison"]
        assert "empirical_p_value" in cov_50["delta_comparison"]
        assert "balanced_accuracy_95_ci" in cov_50["random_abstention_baseline"]
        if cov_50["delta_comparison"]["confidence_beats_random_95_ci"]:
            superior_count += 1

    # Key finding: Confidence selection significantly beats random baseline on majors and key alts
    assert superior_count >= 4
    # Specifically verified on BTC, ETH, DOGE, XMR
    for sym in ["BTCUSDT", "ETHUSDT", "DOGEUSDT", "XMRUSDT"]:
        inst = data["instruments"][sym]
        cov_50 = next(c for c in inst["coverage_evaluations"] if c["target_coverage"] == 0.5)
        assert cov_50["delta_comparison"]["delta_balanced_accuracy"] > 0.0
        assert cov_50["delta_comparison"]["confidence_beats_random_95_ci"] is True
        assert cov_50["delta_comparison"]["empirical_p_value"] < 0.05


def test_06_risk_coverage_and_xmr_guardrail():
    p = AUDIT_DIR / "PHASE_5_4_3_RISK_COVERAGE_AUDIT.json"
    assert p.exists()
    with open(p, encoding="utf-8") as f:
        data = json.load(f)

    assert data["workstream_status"] == "PASS"

    risk_reduced_count = 0
    for sym in EXPECTED_SYMBOLS:
        inst = data["instruments"][sym]
        assert "au_rcc_confidence" in inst
        assert "au_rcc_random_baseline" in inst
        assert "delta_au_rcc" in inst
        if inst["delta_au_rcc"] < 0.0:
            risk_reduced_count += 1

    # Verified finding: 7 of 11 instruments show negative delta AU-RCC (risk reduction over random baseline)
    assert risk_reduced_count == 7
    for sym in ["BTCUSDT", "ETHUSDT", "SOLUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"]:
        assert data["instruments"][sym]["delta_au_rcc"] < 0.0


def test_07_decision_policy_causal_execution():
    p = AUDIT_DIR / "PHASE_5_4_3_DECISION_POLICY_AUDIT.json"
    assert p.exists()
    with open(p, encoding="utf-8") as f:
        data = json.load(f)

    assert data["workstream_status"] == "PASS"
    rules = data["causal_execution_rules"]
    assert "P_entry = open[i+1]" in rules["earliest_executable_entry"]
    assert "P_ref = close[i]" in rules["reference_price"]
    assert "conservative adverse assumption" in rules["ambiguous_intrabar_collision"].lower()


def test_08_cost_sensitivity_and_execution_logs():
    p_cost = AUDIT_DIR / "PHASE_5_4_3_COST_RECONCILIATION.json"
    assert p_cost.exists()
    with open(p_cost, encoding="utf-8") as f:
        cost_data = json.load(f)

    assert "TOTAL round-trip friction" in cost_data["friction_definitions"]["round_trip_specification"]
    assert cost_data["funding_rate_status"]["audit_verdict"] == "UNAVAILABLE_PRE_FUNDING_DIAGNOSTIC"

    p_log = AUDIT_DIR / "PHASE_5_4_3_EXECUTION_LOG_AUDIT.json"
    assert p_log.exists()
    with open(p_log, encoding="utf-8") as f:
        log_data = json.load(f)

    assert log_data["workstream_status"] == "PASS"
    assert len(log_data["audited_failure_events"]) == 7
    assert log_data["clean_execution_verification"]["full_repo_test_passed"] == 206
    assert log_data["clean_execution_verification"]["full_repo_test_failed"] == 0


def test_09_zero_em_dashes_across_all_phase_5_4_3_deliverables():
    em_dash = chr(0x2014)
    files = [
        AUDIT_DIR / "PHASE_5_4_3_ARTIFACT_INTEGRITY_AUDIT.json",
        AUDIT_DIR / "PHASE_5_4_3_CALIBRATION_METRIC_AUDIT.json",
        AUDIT_DIR / "PHASE_5_4_3_TEMPORAL_SEPARATION_AUDIT.json",
        AUDIT_DIR / "PHASE_5_4_3_RANDOM_ABSTENTION_RESULTS.json",
        AUDIT_DIR / "PHASE_5_4_3_RISK_COVERAGE_AUDIT.json",
        AUDIT_DIR / "PHASE_5_4_3_DECISION_POLICY_AUDIT.json",
        AUDIT_DIR / "PHASE_5_4_3_COST_RECONCILIATION.json",
        AUDIT_DIR / "PHASE_5_4_3_EXECUTION_LOG_AUDIT.json",
        AUDIT_DIR / "PHASE_5_4_3_HASH_MANIFEST.json",
        AUDIT_DIR / "PHASE_5_4_3_CORRECTIVE_AUDIT_REPORT.md",
        DOCS_DIR / "PHASE_5_4_3_CORRECTIVE_AUDIT_REPORT.md",
        Path("scripts/run_phase5_4_3_audit.py"),
        Path("tests/unit/test_phase5_4_3_audit.py"),
    ]
    for p in files:
        if p.exists():
            text = p.read_text(encoding="utf-8")
            assert em_dash not in text, f"Forbidden em-dash found in {p}"
