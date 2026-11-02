"""Unit tests for Track 1 Predictive Evaluation Pipeline (Workstream B).

Verifies all 5 mandatory metrics against hand-calculated synthetic fixtures:
1. Balanced Accuracy
2. Multiclass Brier Score
3. ROC-AUC One-vs-Rest
4. Expected Calibration Error (ECE)
5. AURCC

Covers all 10 acceptance edge cases:
1. Perfect predictions.
2. Random / uniform predictions.
3. Completely incorrect predictions.
4. Class imbalance.
5. Missing class in ground truth.
6. Invalid probabilities.
7. Probability normalization.
8. Fold-specific reporting (Folds 1-4 VERIFIED_OOF vs Fold 5 UNVERIFIED_OOS).
9. Empty sample handling.
10. Small sample behavior.
"""

import numpy as np
import pytest

from quantum.backtesting.adapters import OOFSignal
from quantum.backtesting.track1 import Track1PredictiveEvaluator
from quantum.ml.evaluation import ModelEvaluationContract


def test_track1_perfect_predictions():
    """Verify exact metric values for 100% confident perfect predictions."""
    y_true = np.array([-1, 0, 1, -1, 0, 1] * 5)
    y_pred = y_true.copy()
    y_proba = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ] * 10)

    ev = Track1PredictiveEvaluator()
    res = ev.evaluate_arrays(y_true, y_pred, y_proba)

    assert res.sample_count == 30
    assert res.accuracy == pytest.approx(1.0)
    assert res.balanced_accuracy == pytest.approx(1.0)
    assert res.multiclass_brier_score == pytest.approx(0.0)
    assert res.roc_auc_ovr == pytest.approx(1.0)
    assert res.ece_top_uniform == pytest.approx(0.0)
    assert res.ece_top_quantile == pytest.approx(0.0)
    assert res.ece_classwise_uniform == pytest.approx(0.0)
    assert res.aurcc_error_full == pytest.approx(0.0)
    assert res.aurcc_error_span_02_10 == pytest.approx(0.0)


def test_track1_uniform_random_predictions():
    """Verify exact Brier score (2/3) and ROC-AUC (0.5) for uniform [1/3, 1/3, 1/3] probabilities."""
    y_true = np.array([-1, 0, 1] * 10)
    y_pred = np.array([0] * 30)
    y_proba = np.full((30, 3), 1.0 / 3.0)

    ev = Track1PredictiveEvaluator()
    res = ev.evaluate_arrays(y_true, y_pred, y_proba)

    # Hand-calculated Brier score: (2/3)^2 + (1/3)^2 + (1/3)^2 = 4/9 + 1/9 + 1/9 = 6/9 = 2/3
    assert res.multiclass_brier_score == pytest.approx(2.0 / 3.0, abs=1e-5)
    assert res.balanced_accuracy == pytest.approx(1.0 / 3.0, abs=1e-5)
    assert res.roc_auc_ovr == pytest.approx(0.5, abs=1e-5)
    assert res.ece_top_uniform == pytest.approx(0.0, abs=1e-5)
    assert res.aurcc_error_random == pytest.approx(2.0 / 3.0, abs=1e-5)


def test_track1_completely_incorrect_predictions():
    """Verify exact metrics when model assigns probability 1.0 to the wrong class on every sample."""
    y_true = np.array([-1, 0, 1] * 6)
    # Shift classes so every prediction is wrong: -1 -> 0, 0 -> 1, 1 -> -1
    y_pred = np.array([0, 1, -1] * 6)
    y_proba = np.array([
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0],
    ] * 6)

    ev = Track1PredictiveEvaluator()
    res = ev.evaluate_arrays(y_true, y_pred, y_proba)

    # Brier score for 100% wrong one-hot = 1^2 + 1^2 + 0^2 = 2.0
    assert res.accuracy == pytest.approx(0.0)
    assert res.balanced_accuracy == pytest.approx(0.0)
    assert res.multiclass_brier_score == pytest.approx(2.0)
    assert res.ece_top_uniform == pytest.approx(1.0)
    assert res.aurcc_error_full == pytest.approx(1.0)
    assert res.aurcc_error_span_02_10 == pytest.approx(1.0)


def test_track1_class_imbalance():
    """Verify balanced accuracy vs raw accuracy under severe class imbalance (80% class 0)."""
    # 16 samples of 0, 2 of -1, 2 of 1; majority classifier always predicts 0
    y_true = np.array([0] * 16 + [-1, -1, 1, 1])
    y_pred = np.array([0] * 20)
    y_proba = np.tile([0.1, 0.8, 0.1], (20, 1))

    ev = Track1PredictiveEvaluator()
    res = ev.evaluate_arrays(y_true, y_pred, y_proba)

    assert res.accuracy == pytest.approx(0.80)
    # Recall for class 0 is 1.0, for -1 is 0.0, for 1 is 0.0 -> balanced accuracy = 1/3
    assert res.balanced_accuracy == pytest.approx(1.0 / 3.0, abs=1e-5)


def test_track1_missing_class_behavior():
    """Verify missing ground truth class does not crash and reports undefined full OvR ROC-AUC."""
    # Only classes -1 and 1 present in y_true (class 0 absent)
    y_true = np.array([-1, 1, -1, 1, -1, 1])
    y_pred = np.array([-1, 1, -1, 0, -1, 1])
    y_proba = np.array([
        [0.8, 0.1, 0.1],
        [0.1, 0.1, 0.8],
        [0.7, 0.2, 0.1],
        [0.2, 0.5, 0.3],
        [0.9, 0.05, 0.05],
        [0.1, 0.2, 0.7],
    ])

    ev = Track1PredictiveEvaluator()
    res = ev.evaluate_arrays(y_true, y_pred, y_proba)

    assert res.present_classes == [-1, 1]
    assert res.roc_auc_ovr is None
    assert res.roc_auc_ovr_present_classes is not None
    assert any("MISSING_GROUND_TRUTH_CLASSES" in w for w in res.warnings)


def test_track1_invalid_and_normalized_probabilities():
    """Verify rejection of invalid probabilities and normalization when enabled."""
    y_true = np.array([-1, 0, 1])
    y_pred = np.array([-1, 0, 1])

    ev_strict = Track1PredictiveEvaluator(normalize_probabilities=False)

    # Probabilities > 1.0 rejected in strict mode
    with pytest.raises(ValueError, match="probabilities > 1.0"):
        ev_strict.evaluate_arrays(y_true, y_pred, np.array([[2.0, 1.0, 1.0]] * 3))

    # Unnormalized probabilities in [0, 1] rejected in strict mode
    with pytest.raises(ValueError, match="simplex violated"):
        ev_strict.evaluate_arrays(y_true, y_pred, np.array([[0.5, 0.5, 0.5]] * 3))

    # Negative probabilities rejected even when normalize_probabilities=True
    ev_norm = Track1PredictiveEvaluator(normalize_probabilities=True)
    with pytest.raises(ValueError, match="negative probabilities"):
        ev_norm.evaluate_arrays(y_true, y_pred, np.array([[-0.1, 0.6, 0.5]] * 3))

    # Positive unnormalized weights succeed when normalize_probabilities=True
    res = ev_norm.evaluate_arrays(
        y_true,
        y_pred,
        np.array([
            [8.0, 1.0, 1.0],
            [1.0, 8.0, 1.0],
            [1.0, 1.0, 8.0],
        ]),
    )
    assert res.accuracy == pytest.approx(1.0)
    # Normalized probabilities are [0.8, 0.1, 0.1], so Brier = (0.2)^2 + 0.1^2 + 0.1^2 = 0.06
    assert res.multiclass_brier_score == pytest.approx(0.06, abs=1e-5)


def test_track1_empty_and_small_samples():
    """Verify empty sample raises ValueError and small sample N=3 evaluates cleanly."""
    ev = Track1PredictiveEvaluator()
    with pytest.raises(ValueError, match="empty"):
        ev.evaluate_arrays([], [], np.empty((0, 3)))

    res_small = ev.evaluate_arrays(
        [-1, 0, 1],
        [-1, 0, 1],
        [[0.7, 0.2, 0.1], [0.1, 0.8, 0.1], [0.1, 0.1, 0.8]],
    )
    assert res_small.sample_count == 3
    assert any("SMALL_SAMPLE_SIZE" in w for w in res_small.warnings)
    assert res_small.balanced_accuracy == pytest.approx(1.0)


def test_track1_fold_separation_reporting():
    """Verify Track1PredictiveEvaluator separates Folds 1-4 VERIFIED_OOF from Fold 5 UNVERIFIED_OOS."""
    signals = []
    base_ts = 1740000000000
    for fold in [1, 2, 3, 4, 5]:
        for idx, cls in enumerate([-1, 0, 1]):
            ts = base_ts + fold * 10_000_000 + idx * 300_000
            probs = {
                -1: (0.8, 0.1, 0.1),
                0: (0.1, 0.8, 0.1),
                1: (0.1, 0.1, 0.8),
            }[cls]
            signals.append(
                OOFSignal(
                    symbol="BTCUSDT",
                    fold=fold,
                    open_time_ms=ts,
                    close_time_ms=ts + 300_000,
                    predicted_class=cls,
                    prob_sl=probs[0],
                    prob_exp=probs[1],
                    prob_tp=probs[2],
                    true_label=cls,
                    oos_eligibility="OOS_ELIGIBILITY_NOT_VERIFIED" if fold == 5 else "VERIFIED_OOF",
                )
            )

    ev = Track1PredictiveEvaluator()
    report = ev.evaluate_signals("BTCUSDT", signals)

    assert report.symbol == "BTCUSDT"
    assert report.fold_5_governance_status == "OOS_ELIGIBILITY_NOT_VERIFIED"
    assert report.verified_oof_pooled is not None
    assert report.verified_oof_pooled.sample_count == 12  # 4 folds * 3 samples
    assert report.fold_5_unverified_oos is not None
    assert report.fold_5_unverified_oos.sample_count == 3
    assert set(report.per_fold_metrics.keys()) == {1, 2, 3, 4, 5}


def test_model_evaluation_contract_includes_ece_and_aurcc():
    """Verify ModelEvaluationContract.evaluate_predictions includes ECE and AURCC."""
    y_true = np.array([-1, 0, 1, -1, 0, 1])
    y_pred = np.array([-1, 0, 1, -1, 0, 1])
    y_proba = np.array([
        [0.8, 0.1, 0.1],
        [0.1, 0.8, 0.1],
        [0.1, 0.1, 0.8],
        [0.9, 0.05, 0.05],
        [0.05, 0.9, 0.05],
        [0.05, 0.05, 0.9],
    ])
    m = ModelEvaluationContract.evaluate_predictions(y_true, y_pred, y_proba)
    assert "ece_top_uniform" in m and m["ece_top_uniform"] is not None
    assert "aurcc_error_span_02_10" in m and m["aurcc_error_span_02_10"] is not None
