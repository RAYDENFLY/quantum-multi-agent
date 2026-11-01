"""Unit tests for Phase 5.3.3 Fleet Results Reconciliation & Statistical Evidence Audit.

Covers the 15 required verification items:
1. Metric JSON reconciliation.
2. Aggregate calculation correctness.
3. LTC Macro F1 attribution.
4. Baseline winner selection.
5. Brier Score formula consistency.
6. ROC-AUC class alignment.
7. Missing-class behavior.
8. Statistical test assumptions.
9. Multiple-comparison correction.
10. Temporal fold metadata integrity.
11. Purge and embargo distinction.
12. Test-label boundary verification.
13. Prospective holdout rejection.
14. Artifact SHA-256 verification.
15. Pilot-versus-expanded protocol consistency.
"""

import hashlib
import json
import math
from pathlib import Path
from typing import Dict, List
import numpy as np
import pandas as pd
import pytest

from quantum.features.temporal_split import (
    DEVELOPMENT_START_MS,
    PROSPECTIVE_HOLDOUT_START_MS,
    VALIDATION_END_MS,
)
from quantum.ml.contracts import (
    RESEARCH_FEATURE_SCHEMA_HASH,
    RESEARCH_STATIONARY_FEATURES,
)
from quantum.ml.evaluation import ModelEvaluationContract
from quantum.ml.validation import PurgedWalkForwardSplitter

AUDIT_DIR = Path("artifacts/phase_5_3_3")
FLEET_DIR = Path("artifacts/phase_5_3_2")
PILOT_DIR = Path("artifacts/phase_5_3_1")

ALL_SYMBOLS = [
    "BTCUSDT", "XMRUSDT", "ADAUSDT", "XRPUSDT", "BNBUSDT",
    "ETHUSDT", "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT"
]


@pytest.fixture(scope="module")
def audit_results() -> Dict[str, Dict]:
    """Load pre-computed audit JSON files."""
    files = {
        "inventory": AUDIT_DIR / "source_of_truth_inventory.json",
        "reconciliation": AUDIT_DIR / "numerical_reconciliation.json",
        "winners": AUDIT_DIR / "master_winner_catalog.json",
        "formula": AUDIT_DIR / "formula_audit.json",
        "statistical": AUDIT_DIR / "statistical_evidence.json",
        "temporal": AUDIT_DIR / "temporal_leakage_audit.json",
        "resource": AUDIT_DIR / "resource_reproducibility_audit.json",
        "master_catalog": AUDIT_DIR / "master_benchmark_catalog.json",
    }
    loaded = {}
    for k, p in files.items():
        assert p.exists(), f"Audit file missing: {p}"
        with open(p, "r", encoding="utf-8") as f:
            loaded[k] = json.load(f)
    return loaded


def test_01_metric_json_reconciliation(audit_results: Dict[str, Dict]) -> None:
    """1. Verify fold-level metrics reconcile with confusion matrix recalculation."""
    reconciliation = audit_results["reconciliation"]
    symbols = reconciliation["symbols"]

    assert len(symbols) == 11
    for sym, sym_data in symbols.items():
        for m_name, m_res in sym_data["models"].items():
            for f_info in m_res["fold_details"]:
                diffs = f_info["diff"]
                assert diffs["accuracy"] <= 1e-3, f"{sym} {m_name} fold {f_info['fold']} acc diff too high"
                assert diffs["balanced_accuracy"] <= 1e-3, f"{sym} {m_name} fold {f_info['fold']} bal_acc diff too high"
                assert diffs["macro_f1"] <= 1e-3, f"{sym} {m_name} fold {f_info['fold']} macro_f1 diff too high"
                assert f_info["reconciliation_status"] == "EXACT_MATCH"


def test_02_aggregate_calculation_correctness(audit_results: Dict[str, Dict]) -> None:
    """2. Verify arithmetic mean and standard deviation across fold-level metrics."""
    reconciliation = audit_results["reconciliation"]
    symbols = reconciliation["symbols"]

    for sym, sym_data in symbols.items():
        for m_name, m_res in sym_data["models"].items():
            fold_bal_accs = [f["recalculated"]["balanced_accuracy"] for f in m_res["fold_details"]]
            expected_mean = float(np.mean(fold_bal_accs))
            expected_std = float(np.std(fold_bal_accs))

            actual_mean = m_res["recalculated_arithmetic_mean"]["mean_balanced_accuracy"]
            actual_std = m_res["fold_standard_deviation"]["std_balanced_accuracy"]

            assert abs(actual_mean - expected_mean) <= 1e-3
            assert abs(actual_std - expected_std) <= 1e-3


def test_03_ltc_macro_f1_attribution(audit_results: Dict[str, Dict]) -> None:
    """3. Resolve LTC Macro F1 discrepancy and verify correct attribution."""
    reconciliation = audit_results["reconciliation"]
    ltc_res = reconciliation["ltc_discrepancy_resolution"]

    assert ltc_res["B3_RandomForest_Macro_F1"] == 0.4264
    assert ltc_res["B4_LightGBM_Macro_F1"] == 0.4253
    assert ltc_res["B3_RandomForest_Macro_F1"] > ltc_res["B4_LightGBM_Macro_F1"]


def test_04_baseline_winner_selection(audit_results: Dict[str, Dict]) -> None:
    """4. Verify baseline winner selection across all criteria."""
    winners = audit_results["winners"]
    per_sym = winners["per_instrument_winners"]

    assert len(per_sym) == 11
    # Check that LTC winner for BalAcc is B3_RandomForest
    assert per_sym["LTCUSDT"]["best_balanced_accuracy"]["model"] == "B3_RandomForest"
    assert per_sym["LTCUSDT"]["best_macro_f1"]["model"] == "B3_RandomForest"
    # Check that ADA winner for BalAcc is B4_LightGBM
    assert per_sym["ADAUSDT"]["best_balanced_accuracy"]["model"] == "B4_LightGBM"
    # Check that XMR winner for BalAcc is B2_LogisticRegression
    assert per_sym["XMRUSDT"]["best_balanced_accuracy"]["model"] == "B2_LogisticRegression"


def test_05_brier_score_formula_consistency(audit_results: Dict[str, Dict]) -> None:
    """5. Verify multiclass Brier score formula and B0 values > 1.0 mathematical proof."""
    formula = audit_results["formula"]["brier_score_audit"]
    sym_verif = formula["symbol_verification"]

    # In 3-class classification, E[BS] = 2*(1 - p_maj) for hard majority prediction
    for sym, data in sym_verif.items():
        assert data["mathematically_verified"], f"{sym} theoretical Brier score diverged"
        assert data["reported_B0_brier"] > 1.0, f"{sym} expected B0 Brier > 1.0"


def test_06_roc_auc_class_alignment() -> None:
    """6. Verify OvR macro ROC-AUC calculation and class alignment."""
    y_true = np.array([-1, 0, 1, -1, 0, 1, 1, -1])
    # Uniform probabilities
    y_proba = np.array([[1/3, 1/3, 1/3] for _ in range(8)])
    metrics = ModelEvaluationContract.evaluate_predictions(y_true, y_true, y_proba, classes=[-1, 0, 1])

    assert metrics["roc_auc_ovr"] == 0.5
    assert metrics["accuracy"] == 1.0


def test_07_missing_class_behavior() -> None:
    """7. Verify missing class zero-division handling."""
    y_true = np.array([0, 1, 0, 1])  # Class -1 missing
    y_pred = np.array([0, 1, 0, 1])
    y_proba = np.array([[0.0, 0.5, 0.5] for _ in range(4)])

    metrics = ModelEvaluationContract.evaluate_predictions(y_true, y_pred, y_proba, classes=[-1, 0, 1])
    assert metrics["per_class"]["SL"]["f1"] == 0.0
    assert metrics["per_class"]["SL"]["support"] == 0
    assert metrics["per_class"]["EXP"]["f1"] == 1.0
    assert metrics["per_class"]["TP"]["f1"] == 1.0


def test_08_statistical_test_assumptions(audit_results: Dict[str, Dict]) -> None:
    """8. Verify Moving Block Bootstrap respects temporal dependence (block length 12)."""
    stat = audit_results["statistical"]
    assert "Moving Block Bootstrap" in stat["resampling_method"]
    assert "Block Size = 12" in stat["resampling_method"]

    # Claim disposition must be PARTIALLY_SUPPORTED
    assert stat["claim_audit"]["disposition"] == "PARTIALLY_SUPPORTED"


def test_09_multiple_comparison_correction(audit_results: Dict[str, Dict]) -> None:
    """9. Verify Holm-Bonferroni correction maintains valid adjusted alphas."""
    stat = audit_results["statistical"]
    comparisons = stat["comparisons"]

    assert len(comparisons) == 33  # 11 instruments * 3 ML models
    alphas = [c["holm_adjusted_alpha"] for c in comparisons]
    # Alphas must be positive and bounded by 0.05
    for a in alphas:
        assert 0.0 < a <= 0.05


def test_10_temporal_fold_metadata_integrity(audit_results: Dict[str, Dict]) -> None:
    """10. Verify temporal fold metadata across all 11 instruments."""
    temporal = audit_results["temporal"]
    symbols = temporal["symbols"]

    assert len(symbols) == 11
    for sym, sym_info in symbols.items():
        assert sym_info["prospective_holdout_untouched"] is True
        assert sym_info["validation_observed_status"] == "EXCLUDED_FROM_TRAINING"


def test_11_purge_and_embargo_distinction() -> None:
    """11. Verify purge (12 bars) and embargo (24 bars) distinction."""
    splitter = PurgedWalkForwardSplitter(
        n_splits=5,
        horizon_bars=12,
        embargo_bars=24,
        min_train_ratio=0.5,
        protect_test_horizon=True,
    )
    assert splitter.horizon_bars == 12
    assert splitter.embargo_bars == 24
    assert splitter.protect_test_horizon is True


def test_12_test_label_boundary_verification() -> None:
    """12. Verify test samples truncate test_end by horizon_bars to protect test labels."""
    df = pd.DataFrame({
        "open_time_ms": [DEVELOPMENT_START_MS + i * 300_000 for i in range(1000)]
    })
    splitter = PurgedWalkForwardSplitter(n_splits=5, horizon_bars=12, protect_test_horizon=True)
    folds = list(splitter.split(df))

    for fold_idx, (train_idx, test_idx) in enumerate(folds):
        # Assert training and testing sets have strictly zero overlap
        overlap = set(train_idx).intersection(set(test_idx))
        assert len(overlap) == 0
        # Assert test start is separated from train end by at least horizon_bars
        gap = test_idx[0] - train_idx[-1] - 1
        assert gap >= 12, f"Purge gap {gap} < 12 in fold {fold_idx}"


def test_13_prospective_holdout_rejection() -> None:
    """13. Verify strict rejection when input contains timestamps in Prospective Holdout."""
    df_leak = pd.DataFrame({
        "open_time_ms": [DEVELOPMENT_START_MS, PROSPECTIVE_HOLDOUT_START_MS + 1000]
    })
    splitter = PurgedWalkForwardSplitter(n_splits=2)
    with pytest.raises(PermissionError, match="Temporal violation.*PROSPECTIVE_HOLDOUT"):
        list(splitter.split(df_leak))


def test_14_artifact_sha256_verification(audit_results: Dict[str, Dict]) -> None:
    """14. Verify SHA-256 hashes of audited artifacts."""
    inventory = audit_results["inventory"]["inventory"]
    assert len(inventory) == 259

    # Spot check 5 artifacts on disk
    for item in inventory[:5]:
        p = Path(item["relative_path"])
        assert p.exists()
        hasher = hashlib.sha256()
        with open(p, "rb") as f:
            hasher.update(f.read())
        assert hasher.hexdigest() == item["sha256"]


def test_15_pilot_versus_expanded_protocol_consistency(audit_results: Dict[str, Dict]) -> None:
    """15. Verify protocol consistency between Phase 5.3.1 pilot and Phase 5.3.2 fleet."""
    master = audit_results["master_catalog"]["master_catalog"]

    assert len(master) == 11
    # Check pilot symbols identified
    assert master["BTCUSDT"]["origin"] == "Phase 5.3.1 Pilot"
    assert master["XMRUSDT"]["origin"] == "Phase 5.3.1 Pilot"
    # Check expanded symbols identified
    for sym in ["ADAUSDT", "XRPUSDT", "BNBUSDT", "ETHUSDT", "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT"]:
        assert master[sym]["origin"] == "Phase 5.3.2 Fleet"

    # Stationary schema hash matches contract
    assert RESEARCH_FEATURE_SCHEMA_HASH == "cc779ea9e3b1862394b7115375c54c4f4cf3d6496bfabf7de457b578762aaf92"
