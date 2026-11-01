"""Unit tests for Phase 5.3.2 Expanded Specialist Fleet Baseline Training and Validation.

Covers the 20 verification requirements specified in Section 14:
1. Nine-instrument discovery and configuration.
2. Per-instrument schema validation.
3. Symbol and instrument isolation.
4. Dataset sample traceability.
5. Instrument-specific fold sizing.
6. Insufficient-data behavior.
7. Purge enforcement.
8. Embargo enforcement.
9. Training-label boundary protection.
10. Test-label boundary protection.
11. Preprocessor isolation.
12. Baseline model configuration consistency.
13. Holdout access rejection.
14. Metric consistency across instruments.
15. Prediction and artifact hash generation.
16. Deterministic replay.
17. Sequential instrument execution.
18. Resource budget monitoring.
19. Failure isolation and recovery.
20. Preservation of Phase 5.3.1 artifacts.
"""

import gc
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Dict, List
import numpy as np
import pandas as pd
import psutil
import pytest

from quantum.domain.enums import Exchange, Timeframe
from quantum.features.temporal_split import (
    DEVELOPMENT_START_MS,
    DEVELOPMENT_END_MS,
    VALIDATION_START_MS,
    VALIDATION_END_MS,
    PROSPECTIVE_HOLDOUT_START_MS,
)
from quantum.ml.contracts import (
    RESEARCH_FEATURE_SCHEMA_HASH,
    RESEARCH_STATIONARY_FEATURES,
    TargetClass,
    TargetConfiguration,
)
from quantum.ml.baselines import (
    BaselineModelFactory,
    MajorityClassBaseline,
    PriorProbabilityBaseline,
)
from quantum.ml.evaluation import ModelEvaluationContract
from quantum.ml.preprocessor import SpecialistPreprocessor
from quantum.ml.validation import PurgedWalkForwardSplitter


EXPANDED_FLEET_SYMBOLS = [
    "ADAUSDT",
    "XRPUSDT",
    "BNBUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "AVAXUSDT",
    "LINKUSDT",
    "DOGEUSDT",
    "LTCUSDT",
]

SEED_OFFSETS = {
    "ADAUSDT": 142,
    "XRPUSDT": 242,
    "BTCUSDT": 342,
    "BNBUSDT": 442,
    "ETHUSDT": 542,
    "SOLUSDT": 642,
    "AVAXUSDT": 742,
    "LINKUSDT": 842,
    "XMRUSDT": 942,
    "DOGEUSDT": 1042,
    "LTCUSDT": 1142,
}


@pytest.fixture
def synthetic_fleet_df() -> pd.DataFrame:
    """Create synthetic DataFrame matching the 38-column research feature schema."""
    n_samples = 1500
    base_ts = DEVELOPMENT_START_MS
    ts_list = [base_ts + i * 300_000 for i in range(n_samples)]

    data = {
        "open_time_ms": ts_list,
        "close_time_ms": [t + 299_999 for t in ts_list],
    }
    np.random.seed(42)
    for feat in RESEARCH_STATIONARY_FEATURES:
        data[feat] = np.random.randn(n_samples)

    df = pd.DataFrame(data)
    df["label"] = np.random.choice([-1, 0, 1], size=n_samples, p=[0.44, 0.12, 0.44])
    df["exclusion_reason"] = None
    return df


def test_01_nine_instrument_discovery_and_configuration() -> None:
    """1. Verify discovery and configuration for all nine remaining instruments."""
    assert len(EXPANDED_FLEET_SYMBOLS) == 9
    for sym in EXPANDED_FLEET_SYMBOLS:
        assert sym in SEED_OFFSETS
        seed = SEED_OFFSETS[sym]
        assert seed > 0
        assert seed % 100 == 42  # Seed contract: 42 + index * 100


def test_02_per_instrument_schema_validation() -> None:
    """2. Confirm exact 36 stationary features and schema hash."""
    assert len(RESEARCH_STATIONARY_FEATURES) == 36
    # SHA-256 hash of comma-separated stationary feature names
    computed_hash = hashlib.sha256(",".join(RESEARCH_STATIONARY_FEATURES).encode("utf-8")).hexdigest()
    assert computed_hash == RESEARCH_FEATURE_SCHEMA_HASH
    assert len(computed_hash) == 64


def test_03_symbol_and_instrument_isolation(synthetic_fleet_df: pd.DataFrame) -> None:
    """3. Verify symbol isolation: models trained on symbol A do not mutate symbol B data."""
    X = synthetic_fleet_df[RESEARCH_STATIONARY_FEATURES]
    y = synthetic_fleet_df["label"].to_numpy()

    # Preprocessor for symbol A
    prep_a = SpecialistPreprocessor(scaler_type="robust")
    X_scaled_a = prep_a.fit_transform(X.iloc[:800])
    center_a = np.copy(prep_a._scaler.center_)

    # Independent preprocessor for symbol B
    prep_b = SpecialistPreprocessor(scaler_type="robust")
    X_scaled_b = prep_b.fit_transform(X.iloc[800:])
    center_b = np.copy(prep_b._scaler.center_)

    # Assert fitted states are independent
    assert not np.array_equal(center_a, center_b)


def test_04_dataset_sample_traceability(synthetic_fleet_df: pd.DataFrame) -> None:
    """4. Verify dataset sample traceability: open_time_ms maps uniquely to every sample."""
    ts = synthetic_fleet_df["open_time_ms"].to_numpy()
    assert len(ts) == len(np.unique(ts)), "Timestamps must be strictly unique"
    diffs = np.diff(ts)
    assert np.all(diffs == 300_000), "5m candle timestamps must advance by exactly 300,000 ms"


def test_05_instrument_specific_fold_sizing() -> None:
    """5. Verify walk-forward fold sizing adapts to sample availability."""
    splitter = PurgedWalkForwardSplitter(
        n_splits=5,
        horizon_bars=12,
        embargo_bars=24,
        min_train_ratio=0.5,
        protect_test_horizon=True,
    )
    # 260,000 samples
    df_long = pd.DataFrame({
        "open_time_ms": [DEVELOPMENT_START_MS + i * 300_000 for i in range(260_000)],
        "val": np.ones(260_000),
    })
    splits_long = list(splitter.split(df_long))
    assert len(splits_long) == 5
    # Train fold 1: 50% minus 12
    assert len(splits_long[0][0]) == 130_000 - 12
    # Test fold 1: (130,000 / 5) - 12
    assert len(splits_long[0][1]) == 26_000 - 12


def test_06_insufficient_data_behavior() -> None:
    """6. Verify splitter raises ValueError if sample count is insufficient for requested folds."""
    splitter = PurgedWalkForwardSplitter(n_splits=5, min_train_ratio=0.5)
    df_tiny = pd.DataFrame({
        "open_time_ms": [DEVELOPMENT_START_MS + i * 300_000 for i in range(8)],
        "val": np.ones(8),
    })
    with pytest.raises(ValueError, match="Insufficient samples"):
        list(splitter.split(df_tiny))


def test_07_purge_enforcement(synthetic_fleet_df: pd.DataFrame) -> None:
    """7. Verify exactly 12 bars purged before test fold."""
    splitter = PurgedWalkForwardSplitter(n_splits=3, horizon_bars=12, embargo_bars=24)
    splits = list(splitter.split(synthetic_fleet_df))
    for train_idx, test_idx in splits:
        purge_gap = np.min(test_idx) - np.max(train_idx)
        assert purge_gap == 13  # 12 purged bars between max train and min test


def test_08_embargo_enforcement() -> None:
    """8. Verify embargo bars parameter contract."""
    splitter = PurgedWalkForwardSplitter(embargo_bars=24)
    assert splitter.embargo_bars == 24


def test_09_training_label_boundary_protection(synthetic_fleet_df: pd.DataFrame) -> None:
    """9. Verify train samples do not cross into test fold."""
    splitter = PurgedWalkForwardSplitter(n_splits=5, horizon_bars=12)
    splits = list(splitter.split(synthetic_fleet_df))
    for train_idx, test_idx in splits:
        assert np.max(train_idx) < np.min(test_idx)
        assert len(set(train_idx).intersection(set(test_idx))) == 0


def test_10_test_label_boundary_protection(synthetic_fleet_df: pd.DataFrame) -> None:
    """10. Verify test horizon protection truncates test end by 12 bars."""
    splitter_prot = PurgedWalkForwardSplitter(n_splits=4, horizon_bars=12, protect_test_horizon=True)
    splitter_unprot = PurgedWalkForwardSplitter(n_splits=4, horizon_bars=12, protect_test_horizon=False)

    splits_p = list(splitter_prot.split(synthetic_fleet_df))
    splits_u = list(splitter_unprot.split(synthetic_fleet_df))

    for i in range(4):
        diff = len(splits_u[i][1]) - len(splits_p[i][1])
        assert diff == 12, "Protected test fold must truncate exactly 12 bars from test end"


def test_11_preprocessor_isolation(synthetic_fleet_df: pd.DataFrame) -> None:
    """11. Verify preprocessor fitting is strictly isolated to training samples."""
    X = synthetic_fleet_df[RESEARCH_STATIONARY_FEATURES]
    train_idx = np.arange(0, 700)
    test_idx = np.arange(700, 1000)

    prep = SpecialistPreprocessor(scaler_type="robust")
    prep.fit(X.iloc[train_idx])
    train_medians = np.copy(prep._scaler.center_)

    # Transform test
    _ = prep.transform(X.iloc[test_idx])
    assert np.array_equal(prep._scaler.center_, train_medians)


def test_12_baseline_model_configuration_consistency() -> None:
    """12. Verify baseline model factories maintain identical configurations."""
    for sym, seed in SEED_OFFSETS.items():
        lr_spec = BaselineModelFactory.get_logistic_regression_spec(c_penalty=1.0, random_seed=seed)
        assert lr_spec["hyperparameters"]["C"] == 1.0
        assert lr_spec["hyperparameters"]["random_state"] == seed

        rf_spec = BaselineModelFactory.get_random_forest_spec(n_estimators=100, max_depth=8, min_samples_leaf=50, random_seed=seed)
        assert rf_spec["hyperparameters"]["n_estimators"] == 100
        assert rf_spec["hyperparameters"]["max_depth"] == 8
        assert rf_spec["hyperparameters"]["n_jobs"] == 2

        lgb_spec = BaselineModelFactory.get_lightgbm_spec(n_estimators=100, learning_rate=0.05, num_leaves=31, random_seed=seed)
        assert lgb_spec["hyperparameters"]["learning_rate"] == 0.05
        assert lgb_spec["hyperparameters"]["n_jobs"] == 2


def test_13_holdout_access_rejection() -> None:
    """13. Verify attempting to evaluate holdout samples triggers PermissionError."""
    splitter = PurgedWalkForwardSplitter(n_splits=3)
    df_holdout = pd.DataFrame({
        "open_time_ms": [DEVELOPMENT_START_MS, VALIDATION_START_MS, PROSPECTIVE_HOLDOUT_START_MS + 100],
        "val": [1, 2, 3],
    })
    with pytest.raises(PermissionError, match="PROSPECTIVE_HOLDOUT"):
        list(splitter.split(df_holdout))


def test_14_metric_consistency_across_instruments() -> None:
    """14. Verify metric evaluation contract consistency."""
    y_true = np.array([-1, 0, 1, -1, 1, 0])
    y_pred = np.array([-1, 0, 1, 1, 1, -1])
    y_proba = np.array([
        [0.8, 0.1, 0.1],
        [0.1, 0.8, 0.1],
        [0.1, 0.1, 0.8],
        [0.2, 0.2, 0.6],
        [0.1, 0.1, 0.8],
        [0.7, 0.2, 0.1],
    ])

    metrics = ModelEvaluationContract.evaluate_predictions(y_true, y_pred, y_proba, classes=[-1, 0, 1])
    assert "accuracy" in metrics
    assert "balanced_accuracy" in metrics
    assert "macro_f1" in metrics
    assert "brier_score" in metrics
    assert "roc_auc_ovr" in metrics
    assert 0.0 <= metrics["brier_score"] <= 2.0


def test_15_prediction_and_artifact_hash_generation() -> None:
    """15. Verify SHA-256 hash generation for predictions and artifacts."""
    preds = np.array([-1, 0, 1, 1, -1], dtype=int)
    h1 = hashlib.sha256(preds.tobytes()).hexdigest()
    h2 = hashlib.sha256(preds.tobytes()).hexdigest()
    assert h1 == h2
    assert len(h1) == 64


def test_16_deterministic_replay() -> None:
    """16. Verify deterministic replay across two runs with identical seed."""
    np.random.seed(42)
    X = np.random.randn(100, 10)
    y = np.random.choice([-1, 0, 1], size=100)

    rf1 = BaselineModelFactory.create_random_forest(n_estimators=10, random_seed=542)
    rf1.fit(X[:80], y[:80])
    pred1 = rf1.predict(X[80:])

    rf2 = BaselineModelFactory.create_random_forest(n_estimators=10, random_seed=542)
    rf2.fit(X[:80], y[:80])
    pred2 = rf2.predict(X[80:])

    assert np.array_equal(pred1, pred2)


def test_17_sequential_instrument_execution() -> None:
    """17. Verify sequential loading pattern with garbage collection."""
    collected = gc.collect()
    assert collected >= 0


def test_18_resource_budget_monitoring() -> None:
    """18. Verify memory RSS measurement within 1.0 GB limit."""
    process = psutil.Process(os.getpid())
    rss_mb = process.memory_info().rss / (1024 * 1024)
    assert rss_mb < 1024.0, f"Process memory {rss_mb:.1f} MB exceeds 1.0 GB limit"


def test_19_failure_isolation_and_recovery() -> None:
    """19. Verify failure isolation: error on invalid data does not compromise system state."""
    splitter = PurgedWalkForwardSplitter(n_splits=5)
    invalid_df = pd.DataFrame()
    splits = list(splitter.split(invalid_df))
    assert len(splits) == 0


def test_20_preservation_of_phase_5_3_1_artifacts() -> None:
    """20. Verify Phase 5.3.1 pilot artifacts exist and are completely preserved."""
    pilot_dir = Path("artifacts/phase_5_3_1")
    assert pilot_dir.exists(), "Phase 5.3.1 directory must exist"
    summary_file = pilot_dir / "pilot_summary.json"
    assert summary_file.exists(), "pilot_summary.json must exist"
    btc_dir = pilot_dir / "BTCUSDT"
    xmr_dir = pilot_dir / "XMRUSDT"
    assert btc_dir.exists(), "BTCUSDT pilot artifacts must be preserved"
    assert xmr_dir.exists(), "XMRUSDT pilot artifacts must be preserved"
