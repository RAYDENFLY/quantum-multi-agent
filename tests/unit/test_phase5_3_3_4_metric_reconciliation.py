"""
Unit tests for Phase 5.3.3.4: Metric Consistency and OOF Benchmark Reconciliation.
Verifies three-class target schemas, B0 majority baseline behavior, B4 confusion matrices,
historical benchmark reconciliation, OOF sample population accounting, and documentation integrity.
"""

import json
from pathlib import Path
import pytest

ARTIFACTS_DIR = Path("artifacts/phase_5_3_3_4")
DOCS_DIR = Path("docs")

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"
]

HISTORICAL_B4_BENCHMARKS = {
    "BTCUSDT": 0.4099,
    "ETHUSDT": 0.4177,
    "BNBUSDT": 0.3699,
    "XRPUSDT": 0.3747,
    "ADAUSDT": 0.4490,
    "SOLUSDT": 0.3878,
    "AVAXUSDT": 0.4145,
    "LINKUSDT": 0.4067,
    "DOGEUSDT": 0.3960,
    "LTCUSDT": 0.4355,
    "XMRUSDT": 0.3816,
}


def test_01_all_artifacts_exist():
    expected_files = [
        "target_schema_audit.json",
        "b0_reconstruction_audit.json",
        "b4_confusion_matrix_audit.json",
        "historical_benchmark_reconciliation.json",
        "oof_sample_accounting.json",
        "bootstrap_input_validity.json",
        "final_benchmark_reconciliation.json",
        "final_audit_manifest.json",
    ]
    for fname in expected_files:
        p = ARTIFACTS_DIR / fname
        assert p.exists(), f"Missing artifact: {fname}"
        assert p.stat().st_size > 0, f"Empty artifact: {fname}"


def test_02_target_schema_audit_three_classes():
    with open(ARTIFACTS_DIR / "target_schema_audit.json") as f:
        data = json.load(f)
    assert data["target_definition"]["classes"] == [-1, 0, 1]
    for sym in SYMBOLS:
        inst = data["instruments"][sym]
        assert inst["target_schema_status"] == "THREE_CLASS_CANONICAL_CONFIRMED"
        assert inst["is_multiclass_three_class"] is True
        assert inst["has_binary_conversion"] is False
        assert inst["class_minus_1_sl_count"] > 0
        assert inst["class_0_exp_count"] > 0
        assert inst["class_1_tp_count"] > 0
        total = inst["class_minus_1_sl_count"] + inst["class_0_exp_count"] + inst["class_1_tp_count"]
        assert total == inst["total_eligible_observations"]


def test_03_b0_baseline_fold_balanced_accuracy_is_one_third():
    with open(ARTIFACTS_DIR / "b0_reconstruction_audit.json") as f:
        data = json.load(f)
    for sym in SYMBOLS:
        inst = data["instruments"][sym]
        for fold in inst["folds"]:
            assert fold["balanced_accuracy"] == pytest.approx(1.0 / 3.0, abs=1e-4), (
                f"B0 fold BA for {sym} fold {fold['fold']} was {fold['balanced_accuracy']}, expected ~0.3333"
            )
            # Exactly one predicted class per fold
            rec = fold["per_class_recall"]
            rec_vals = [rec["SL"], rec["EXP"], rec["TP"]]
            assert sorted(rec_vals) == [0.0, 0.0, 1.0]


def test_04_b0_baseline_pooled_balanced_accuracy_is_approximately_one_third():
    with open(ARTIFACTS_DIR / "b0_reconstruction_audit.json") as f:
        data = json.load(f)
    for sym in SYMBOLS:
        inst = data["instruments"][sym]
        pooled_ba = inst["pooled_balanced_accuracy"]
        # Pooled BA must be close to 0.3333 (within 0.01) and NEVER 0.5000
        assert 0.3200 <= pooled_ba <= 0.3500, f"B0 pooled BA for {sym} was {pooled_ba}"
        assert abs(pooled_ba - 0.5000) > 0.10, f"B0 pooled BA for {sym} unexpectedly near 0.5000"


def test_05_b4_fold_mean_matches_historical_benchmarks():
    with open(ARTIFACTS_DIR / "historical_benchmark_reconciliation.json") as f:
        data = json.load(f)
    for comp in data["comparisons"]:
        sym = comp["symbol"]
        hist_ba = comp["historical_b4_fold_mean_ba"]
        recon_ba = comp["reconstructed_b4_fold_mean_ba"]
        assert hist_ba == pytest.approx(HISTORICAL_B4_BENCHMARKS[sym], abs=1e-4)
        assert recon_ba == pytest.approx(hist_ba, abs=1e-4), (
            f"Mismatch for {sym}: hist {hist_ba} != recon {recon_ba}"
        )
        assert comp["reconciliation_status"] == "EXACT_RECONCILIATION"


def test_06_b4_confusion_matrices_valid_multiclass():
    with open(ARTIFACTS_DIR / "b4_confusion_matrix_audit.json") as f:
        data = json.load(f)
    for sym in SYMBOLS:
        inst = data["instruments"][sym]
        cm = inst["pooled_confusion_matrix"]
        assert len(cm) == 3 and all(len(row) == 3 for row in cm)
        per_class = inst["per_class"]
        for cname in ["SL", "EXP", "TP"]:
            assert 0.0 <= per_class[cname]["precision"] <= 1.0
            assert 0.0 <= per_class[cname]["recall"] <= 1.0
            assert 0.0 <= per_class[cname]["f1"] <= 1.0
            assert per_class[cname]["support"] > 0


def test_07_oof_sample_accounting_reconciles_1322108():
    with open(ARTIFACTS_DIR / "oof_sample_accounting.json") as f:
        data = json.load(f)
    assert data["fleet_total_oof_observations"] == 1_322_108
    fleet_sum = sum(inst["oof_test_observations"] for inst in data["instruments"].values())
    assert fleet_sum == 1_322_108


def test_08_prospective_holdout_untouched():
    with open(ARTIFACTS_DIR / "oof_sample_accounting.json") as f:
        data = json.load(f)
    for sym, inst in data["instruments"].items():
        assert inst["prospective_holdout_samples"] == 0, f"Holdout accessed for {sym}!"


def test_09_bootstrap_inputs_conform_to_three_class_metric():
    with open(ARTIFACTS_DIR / "bootstrap_input_validity.json") as f:
        data = json.load(f)
    for sym, ev in data["evaluations"].items():
        assert ev["ba_metric_matches_artifact"] is True
        assert ev["lift_matches_artifact"] is True
        assert ev["classes_verified"] == [-1, 0, 1]
        assert ev["sample_count_verified"] is True
        assert ev["bootstrap_inputs_verdict"] == "VALID_THREE_CLASS_INPUTS"


def test_10_final_benchmark_reconciliation_structure():
    with open(ARTIFACTS_DIR / "final_benchmark_reconciliation.json") as f:
        data = json.load(f)
    assert len(data["instruments"]) == 11
    for sym in SYMBOLS:
        inst = data["instruments"][sym]
        assert inst["target_schema"] == "THREE_CLASS_CANONICAL"
        assert inst["metrics_reconciliation_verdict"] == "EXACT_RECONCILIATION"
        assert inst["b0_majority"]["fold_mean_balanced_accuracy"] == pytest.approx(1.0 / 3.0, abs=1e-4)
        assert inst["b4_lightgbm"]["reconstructed_fold_mean_balanced_accuracy"] == pytest.approx(
            HISTORICAL_B4_BENCHMARKS[sym], abs=1e-4
        )


def test_11_audit_manifest_contains_all_files():
    with open(ARTIFACTS_DIR / "final_audit_manifest.json") as f:
        manifest = json.load(f)
    assert manifest["phase"] == "5.3.3.4"
    assert manifest["verdict"] == "PHASE_5_3_3_4_PASS"
    assert manifest["phase_5_4_gate_status"] == "HOLD"
    assert manifest["fleet_total_oof_observations"] == 1_322_108
    assert len(manifest["files"]) >= 7
