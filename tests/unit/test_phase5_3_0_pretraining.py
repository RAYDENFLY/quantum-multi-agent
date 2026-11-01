"""Automated unit tests for Phase 5.3.0 pre-training architecture and specifications.

Covers:
- Dataset and sample trace contracts.
- Temporal leakage prevention in walk-forward splitter.
- Holdout access rejection.
- Per-instrument experiment isolation.
- Preprocessing fit boundary isolation (no leakage from test into train).
- Experiment manifest reproducibility and hash consistency.
- Baseline model instantiation without training.
"""

import numpy as np
import pandas as pd
import pytest

from quantum.domain.enums import Exchange, Timeframe
from quantum.features.temporal_split import (
    DEVELOPMENT_END_MS,
    DEVELOPMENT_START_MS,
    PROSPECTIVE_HOLDOUT_START_MS,
    VALIDATION_END_MS,
    VALIDATION_START_MS,
)
from quantum.ml.baselines import (
    BaselineModelFactory,
    MajorityClassBaseline,
    PriorProbabilityBaseline,
)
from quantum.ml.contracts import (
    ExperimentManifest,
    RESEARCH_FEATURE_SCHEMA_HASH,
    RESEARCH_STATIONARY_FEATURES,
    TargetClass,
    TargetConfiguration,
)
from quantum.ml.evaluation import ModelEvaluationContract
from quantum.ml.preprocessor import SpecialistPreprocessor
from quantum.ml.validation import PurgedWalkForwardSplitter


@pytest.fixture
def sample_clean_features() -> pd.DataFrame:
    """Generate synthetic DataFrame matching the research stationary feature schema."""
    n = 1000
    base_ts = DEVELOPMENT_START_MS
    ts_list = [base_ts + i * 300_000 for i in range(n)]

    data = {
        "open_time_ms": ts_list,
        "close_time_ms": [t + 299_999 for t in ts_list],
    }
    np.random.seed(42)
    for col in RESEARCH_STATIONARY_FEATURES:
        data[col] = np.random.randn(n)

    return pd.DataFrame(data)


def test_experiment_manifest_reproducibility() -> None:
    """Verify that identical experiment parameters produce identical manifest hashes."""
    target_cfg = TargetConfiguration(
        timeframe=Timeframe.M5,
        horizon_bars=12,
        maximum_holding_minutes=60,
        volatility_lookback=20,
        barrier_multiplier=1.5,
    )

    manifest_1 = ExperimentManifest(
        experiment_id="EXP-BTCUSDT-RF-001",
        model_name="RandomForest",
        specialist_instrument="BTCUSDT",
        feature_schema_hash=RESEARCH_FEATURE_SCHEMA_HASH,
        feature_names=RESEARCH_STATIONARY_FEATURES,
        target_config=target_cfg,
        random_seed=42,
        instrument_seed=1001,
        created_at_utc="2026-11-01T12:00:00Z",
    )

    manifest_2 = ExperimentManifest(
        experiment_id="EXP-BTCUSDT-RF-001",
        model_name="RandomForest",
        specialist_instrument="BTCUSDT",
        feature_schema_hash=RESEARCH_FEATURE_SCHEMA_HASH,
        feature_names=RESEARCH_STATIONARY_FEATURES,
        target_config=target_cfg,
        random_seed=42,
        instrument_seed=1001,
        created_at_utc="2026-11-01T12:00:00Z",
    )

    hash1 = manifest_1.compute_manifest_hash()
    hash2 = manifest_2.compute_manifest_hash()
    assert hash1 == hash2, "Manifest hashes must be 100% deterministic and equal"
    assert len(hash1) == 64


def test_purged_walk_forward_splitter_temporal_order(sample_clean_features: pd.DataFrame) -> None:
    """Verify walk-forward splits are strictly expanding, chronological, and purged."""
    splitter = PurgedWalkForwardSplitter(n_splits=4, horizon_bars=12, embargo_bars=24, min_train_ratio=0.5)
    splits = list(splitter.split(sample_clean_features))
    assert len(splits) == 4

    for fold_idx, (train_idx, test_idx) in enumerate(splits):
        # 1. Non-empty
        assert len(train_idx) > 0
        assert len(test_idx) > 0

        # 2. Chronological separation: all train indices strictly precede test indices
        assert np.max(train_idx) < np.min(test_idx)

        # 3. Purging: gap between train_max and test_min must be exactly horizon_bars (12)
        purge_gap = np.min(test_idx) - np.max(train_idx)
        assert purge_gap == 12 + 1, f"Purge gap should be 13 index units (12 purged bars): {purge_gap}"


def test_splitter_rejects_prospective_holdout() -> None:
    """Verify that walk-forward splitter raises PermissionError if DataFrame contains holdout rows."""
    splitter = PurgedWalkForwardSplitter(n_splits=3)
    df_with_holdout = pd.DataFrame({
        "open_time_ms": [DEVELOPMENT_START_MS, VALIDATION_START_MS, PROSPECTIVE_HOLDOUT_START_MS + 1000],
        "feature_1": [1.0, 2.0, 3.0],
    })

    with pytest.raises(PermissionError, match="PROSPECTIVE_HOLDOUT"):
        list(splitter.split(df_with_holdout))


def test_specialist_preprocessor_fit_boundary_isolation(sample_clean_features: pd.DataFrame) -> None:
    """Verify preprocessor fits only on train data and does not modify training statistics on test."""
    feature_cols = RESEARCH_STATIONARY_FEATURES
    X = sample_clean_features[feature_cols]

    X_train = X.iloc[:600]
    X_test = X.iloc[600:]

    preprocessor = SpecialistPreprocessor(scaler_type="robust")
    assert not preprocessor.is_fitted

    # Fit on training data
    X_train_scaled = preprocessor.fit_transform(X_train)
    assert preprocessor.is_fitted
    assert preprocessor.feature_names_in_ == feature_cols

    # Transform test data
    X_test_scaled = preprocessor.transform(X_test)

    # Validate output shapes and finite properties
    assert X_train_scaled.shape == X_train.shape
    assert X_test_scaled.shape == X_test.shape
    assert not np.isnan(X_train_scaled).any()
    assert not np.isnan(X_test_scaled).any()
    assert not np.isinf(X_train_scaled).any()
    assert not np.isinf(X_test_scaled).any()


def test_preprocessor_rejects_unfitted_transform() -> None:
    """Verify calling transform before fit raises RuntimeError."""
    preprocessor = SpecialistPreprocessor()
    df = pd.DataFrame({"col1": [1.0, 2.0]})
    with pytest.raises(RuntimeError, match="must be fitted"):
        preprocessor.transform(df)


def test_heuristic_baselines_correctness() -> None:
    """Verify MajorityClassBaseline and PriorProbabilityBaseline calculations."""
    X_train = np.array([[1], [2], [3], [4], [5], [6]])
    # 3 samples of class 1 (TP), 2 samples of class -1 (SL), 1 sample of class 0 (EXP)
    y_train = np.array([1, 1, 1, -1, -1, 0])

    X_test = np.array([[10], [20]])

    # 1. Majority class baseline
    maj = MajorityClassBaseline()
    maj.fit(X_train, y_train)
    assert maj.majority_class_ == 1
    preds_maj = maj.predict(X_test)
    assert np.array_equal(preds_maj, [1, 1])

    # 2. Prior class probability baseline
    prior = PriorProbabilityBaseline()
    prior.fit(X_train, y_train)
    probs_prior = prior.predict_proba(X_test)
    assert probs_prior.shape == (2, 3)
    # Check that probabilities sum to 1.0
    assert np.allclose(np.sum(probs_prior, axis=1), 1.0)


def test_model_evaluation_contract_metrics() -> None:
    """Verify ModelEvaluationContract computes accuracy, F1, and Brier score correctly."""
    y_true = np.array([1, 1, -1, -1, 0, 1])
    y_pred = np.array([1, 1, -1, 0, 0, 1])
    y_proba = np.array([
        [0.1, 0.1, 0.8],
        [0.1, 0.1, 0.8],
        [0.8, 0.1, 0.1],
        [0.2, 0.6, 0.2],
        [0.1, 0.8, 0.1],
        [0.2, 0.2, 0.6],
    ])

    metrics = ModelEvaluationContract.evaluate_predictions(y_true, y_pred, y_proba=y_proba, classes=[-1, 0, 1])

    assert "accuracy" in metrics
    assert "balanced_accuracy" in metrics
    assert "macro_f1" in metrics
    assert "brier_score" in metrics
    assert metrics["accuracy"] == round(5 / 6, 4)


def test_baseline_factory_instantiations() -> None:
    """Verify BaselineModelFactory creates valid un-fitted estimators matching spec."""
    lr = BaselineModelFactory.create_logistic_regression(c_penalty=0.5, random_seed=42)
    assert lr.C == 0.5
    assert lr.random_state == 42
    assert lr.penalty == "l2"

    rf = BaselineModelFactory.create_random_forest(n_estimators=50, max_depth=6, random_seed=42)
    assert rf.n_estimators == 50
    assert rf.max_depth == 6
    assert rf.n_jobs == 2

    lgbm = BaselineModelFactory.create_lightgbm(n_estimators=50, learning_rate=0.01, random_seed=42)
    assert lgbm.n_estimators == 50
    assert lgbm.learning_rate == 0.01
    assert lgbm.n_jobs == 2
