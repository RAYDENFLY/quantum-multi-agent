"""Phase 5.3.2 Expanded Specialist Fleet Baseline Training and Validation Runner.

Executes:
1. Pre-training data integrity and schema audit for the 9 remaining instruments:
   ADAUSDT, XRPUSDT, BNBUSDT, ETHUSDT, SOLUSDT, AVAXUSDT, LINKUSDT, DOGEUSDT, LTCUSDT.
2. Purged and embargoed 5-fold walk-forward validation across all 5 baselines:
   B0: Majority Class
   B1: Prior Probability
   B2: Logistic Regression (L2)
   B3: Balanced Random Forest (100 trees, max_depth=8, min_samples_leaf=50)
   B4: LightGBM (100 boosting rounds, lr=0.05, num_leaves=31)
3. Strict causal preprocessing isolation (RobustScaler fit on train only).
4. Resource benchmarking (< 1.0 GB RAM peak RSS, n_jobs=2 CPU threads).
5. Deterministic replay verification on ETHUSDT Fold 1.
6. Integration with Phase 5.3.1 pilot results (BTCUSDT, XMRUSDT) to generate
   the comprehensive 11-instrument specialist catalog in artifacts/phase_5_3_2/fleet_summary/.
"""

import argparse
from datetime import datetime, timezone
import gc
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import psutil

from quantum.domain.enums import Exchange, Timeframe
from quantum.features.labeling import BarrierOutcome, TripleBarrierLabelGenerator
from quantum.features.temporal_split import (
    DEVELOPMENT_END_MS,
    DEVELOPMENT_START_MS,
    PROSPECTIVE_HOLDOUT_START_MS,
    VALIDATION_END_MS,
    VALIDATION_START_MS,
    TemporalPartitionManager,
)
from quantum.historical.storage import ParquetStorageManager
from quantum.ml.baselines import (
    BaselineModelFactory,
    MajorityClassBaseline,
    PriorProbabilityBaseline,
)
from quantum.ml.contracts import (
    ExperimentManifest,
    RESEARCH_FEATURE_SCHEMA_HASH,
    RESEARCH_STATIONARY_FEATURES,
    TargetConfiguration,
)
from quantum.ml.evaluation import ModelEvaluationContract
from quantum.ml.preprocessor import SpecialistPreprocessor
from quantum.ml.validation import PurgedWalkForwardSplitter

BASE_DIR = Path("data/historical")
PILOT_ARTIFACTS_DIR = Path("artifacts/phase_5_3_1")
ARTIFACTS_DIR = Path("artifacts/phase_5_3_2")
EXCHANGE = Exchange.ASTER
TIMEFRAME = Timeframe.M5

SEED_OFFSETS: Dict[str, int] = {
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

REMAINING_SYMBOLS: List[str] = [
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


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def audit_feature_schema(df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
    """Verify feature matrix columns, data types, and finiteness."""
    cols = list(df.columns)
    has_timestamps = "open_time_ms" in cols and "close_time_ms" in cols
    model_feature_cols = [
        c for c in cols
        if c not in ("open_time_ms", "close_time_ms", "label", "exclusion_reason")
    ]

    assert model_feature_cols == RESEARCH_STATIONARY_FEATURES, f"{symbol} feature columns mismatch!"

    X_num = df[model_feature_cols].to_numpy(dtype=float)
    nan_count = int(np.isnan(X_num).sum())
    inf_count = int(np.isinf(X_num).sum())

    return {
        "symbol": symbol,
        "total_columns": len(cols),
        "timestamp_columns": ["open_time_ms", "close_time_ms"] if has_timestamps else [],
        "stationary_feature_count": len(model_feature_cols),
        "nan_count": nan_count,
        "inf_count": inf_count,
        "schema_hash": RESEARCH_FEATURE_SCHEMA_HASH,
    }


def prepare_labeled_dataset(
    storage: ParquetStorageManager,
    symbol: str,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Load canonical data, generate causal labels, join features, and filter Dev+Val."""
    df_can = storage.read_canonical(EXCHANGE, symbol, TIMEFRAME)

    # Generate triple-barrier labels
    gen = TripleBarrierLabelGenerator(
        horizon_bars=12,
        volatility_lookback=20,
        barrier_multiplier=1.5,
        timeframe_ms=300_000,
    )
    labeled = gen.generate_labels(df_can, enforce_partition_boundaries=True)

    # Read research features
    feat_files = sorted(
        (BASE_DIR / f"features_research/exchange={EXCHANGE.value}/symbol={symbol}/timeframe={TIMEFRAME.value}").glob("*.parquet")
    )
    df_feats = pd.concat([pd.read_parquet(f) for f in feat_files], ignore_index=True)

    # Filter features to Dev+Val
    ts = df_feats["open_time_ms"]
    dev_val_mask = (ts >= DEVELOPMENT_START_MS) & (ts <= VALIDATION_END_MS)
    df_feats_dv = df_feats[dev_val_mask].copy().reset_index(drop=True)

    # Align labels with features (both have open_time_ms)
    merged = pd.merge(
        df_feats_dv,
        labeled[["open_time_ms", "label", "exclusion_reason"]],
        on="open_time_ms",
        how="inner",
    )

    # Filter for clean eligible samples (TP, SL, EXP)
    clean_mask = merged["label"].isin([
        BarrierOutcome.TP.value,
        BarrierOutcome.SL.value,
        BarrierOutcome.TIME_EXPIRATION.value,
    ])
    df_clean = merged[clean_mask].copy().reset_index(drop=True)

    # Statistics
    stats = {
        "symbol": symbol,
        "total_canonical": len(df_can),
        "total_dev_val_features": len(df_feats_dv),
        "eligible_samples": len(df_clean),
        "tp_count": int((df_clean["label"] == 1).sum()),
        "sl_count": int((df_clean["label"] == -1).sum()),
        "exp_count": int((df_clean["label"] == 0).sum()),
        "ambiguous_count": int((merged["label"] == -2).sum()),
        "excluded_count": int((merged["label"] == -999).sum()),
    }
    return df_clean, stats


def train_and_eval_fold(
    fold_idx: int,
    train_idx: np.ndarray,
    test_idx: np.ndarray,
    df: pd.DataFrame,
    symbol: str,
    seed: int,
    out_dir: Path,
) -> Dict[str, Any]:
    """Train B0-B4 and evaluate on out-of-fold test data."""
    X_raw = df[RESEARCH_STATIONARY_FEATURES]
    y = df["label"].to_numpy(dtype=int)

    X_train_raw = X_raw.iloc[train_idx]
    y_train = y[train_idx]

    X_test_raw = X_raw.iloc[test_idx]
    y_test = y[test_idx]

    # Preprocessor isolation: fit exclusively on X_train
    preprocessor = SpecialistPreprocessor(scaler_type="robust")
    t0_prep = time.time()
    X_train = preprocessor.fit_transform(X_train_raw)
    X_test = preprocessor.transform(X_test_raw)
    prep_duration = time.time() - t0_prep

    fold_results: Dict[str, Any] = {
        "fold": fold_idx + 1,
        "train_samples": int(len(train_idx)),
        "test_samples": int(len(test_idx)),
        "preprocessor_duration_s": round(prep_duration, 4),
        "models": {},
    }

    classes = [-1, 0, 1]
    predictions_payload: Dict[str, Any] = {
        "fold": fold_idx + 1,
        "y_true_hash": hashlib.sha256(y_test.tobytes()).hexdigest(),
        "predictions": {},
    }

    # Model B0: Majority Class
    b0 = MajorityClassBaseline()
    t0 = time.time()
    b0.fit(X_train, y_train)
    b0_train_time = time.time() - t0
    t0_p = time.time()
    b0_pred = b0.predict(X_test)
    b0_proba = b0.predict_proba(X_test)
    b0_pred_time = time.time() - t0_p
    b0_metrics = ModelEvaluationContract.evaluate_predictions(y_test, b0_pred, b0_proba, classes=classes)
    b0_metrics["train_time_s"] = round(b0_train_time, 4)
    b0_metrics["pred_time_s"] = round(b0_pred_time, 4)
    fold_results["models"]["B0_Majority"] = b0_metrics
    predictions_payload["predictions"]["B0_Majority"] = {
        "pred_hash": hashlib.sha256(b0_pred.tobytes()).hexdigest(),
        "proba_hash": hashlib.sha256(b0_proba.tobytes()).hexdigest(),
    }

    # Model B1: Prior Probability
    b1 = PriorProbabilityBaseline()
    t0 = time.time()
    b1.fit(X_train, y_train)
    b1_train_time = time.time() - t0
    t0_p = time.time()
    b1_pred = b1.predict(X_test)
    b1_proba = b1.predict_proba(X_test)
    b1_pred_time = time.time() - t0_p
    b1_metrics = ModelEvaluationContract.evaluate_predictions(y_test, b1_pred, b1_proba, classes=classes)
    b1_metrics["train_time_s"] = round(b1_train_time, 4)
    b1_metrics["pred_time_s"] = round(b1_pred_time, 4)
    fold_results["models"]["B1_Prior"] = b1_metrics
    predictions_payload["predictions"]["B1_Prior"] = {
        "pred_hash": hashlib.sha256(b1_pred.tobytes()).hexdigest(),
        "proba_hash": hashlib.sha256(b1_proba.tobytes()).hexdigest(),
    }

    # Model B2: Logistic Regression (L2)
    b2 = BaselineModelFactory.create_logistic_regression(c_penalty=1.0, random_seed=seed)
    t0 = time.time()
    b2.fit(X_train, y_train)
    b2_train_time = time.time() - t0
    t0_p = time.time()
    b2_pred = b2.predict(X_test)
    b2_proba = b2.predict_proba(X_test)
    b2_pred_time = time.time() - t0_p
    b2_metrics = ModelEvaluationContract.evaluate_predictions(y_test, b2_pred, b2_proba, classes=classes)
    b2_metrics["train_time_s"] = round(b2_train_time, 4)
    b2_metrics["pred_time_s"] = round(b2_pred_time, 4)
    fold_results["models"]["B2_LogisticRegression"] = b2_metrics
    predictions_payload["predictions"]["B2_LogisticRegression"] = {
        "pred_hash": hashlib.sha256(b2_pred.tobytes()).hexdigest(),
        "proba_hash": hashlib.sha256(b2_proba.tobytes()).hexdigest(),
    }

    # Model B3: Balanced Random Forest
    b3 = BaselineModelFactory.create_random_forest(
        n_estimators=100, max_depth=8, min_samples_leaf=50, random_seed=seed
    )
    t0 = time.time()
    b3.fit(X_train, y_train)
    b3_train_time = time.time() - t0
    t0_p = time.time()
    b3_pred = b3.predict(X_test)
    b3_proba = b3.predict_proba(X_test)
    b3_pred_time = time.time() - t0_p
    b3_metrics = ModelEvaluationContract.evaluate_predictions(y_test, b3_pred, b3_proba, classes=classes)
    b3_metrics["train_time_s"] = round(b3_train_time, 4)
    b3_metrics["pred_time_s"] = round(b3_pred_time, 4)
    fold_results["models"]["B3_RandomForest"] = b3_metrics
    predictions_payload["predictions"]["B3_RandomForest"] = {
        "pred_hash": hashlib.sha256(b3_pred.tobytes()).hexdigest(),
        "proba_hash": hashlib.sha256(b3_proba.tobytes()).hexdigest(),
    }

    # Model B4: LightGBM
    b4 = BaselineModelFactory.create_lightgbm(
        n_estimators=100, learning_rate=0.05, num_leaves=31, random_seed=seed
    )
    t0 = time.time()
    b4.fit(X_train, y_train)
    b4_train_time = time.time() - t0
    t0_p = time.time()
    b4_pred = b4.predict(X_test)
    b4_proba = b4.predict_proba(X_test)
    b4_pred_time = time.time() - t0_p
    b4_metrics = ModelEvaluationContract.evaluate_predictions(y_test, b4_pred, b4_proba, classes=classes)
    b4_metrics["train_time_s"] = round(b4_train_time, 4)
    b4_metrics["pred_time_s"] = round(b4_pred_time, 4)
    fold_results["models"]["B4_LightGBM"] = b4_metrics
    predictions_payload["predictions"]["B4_LightGBM"] = {
        "pred_hash": hashlib.sha256(b4_pred.tobytes()).hexdigest(),
        "proba_hash": hashlib.sha256(b4_proba.tobytes()).hexdigest(),
    }

    # Save fold artifacts for B4 and preprocessor
    fold_art_dir = out_dir / f"fold_{fold_idx+1}"
    fold_art_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(b4, fold_art_dir / "lgbm_model.joblib")
    joblib.dump(preprocessor, fold_art_dir / "preprocessor.joblib")

    with open(fold_art_dir / "metrics.json", "w") as f:
        json.dump(fold_results, f, indent=2)

    with open(fold_art_dir / "predictions.json", "w") as f:
        json.dump(predictions_payload, f, indent=2)

    return fold_results


def run_experiment_for_symbol(
    storage: ParquetStorageManager,
    symbol: str,
    process: psutil.Process,
) -> Dict[str, Any]:
    """Run full baseline training and evaluation for one instrument."""
    print(f"\n========================================================", flush=True)
    print(f"SPECIALIST FLEET EXECUTION: {symbol}", flush=True)
    print(f"========================================================", flush=True)

    out_dir = ARTIFACTS_DIR / symbol
    out_dir.mkdir(parents=True, exist_ok=True)

    mem_before = process.memory_info().rss / (1024 * 1024)

    # 1. Prepare clean labeled dataset
    df_clean, data_stats = prepare_labeled_dataset(storage, symbol)
    print(f"Loaded {symbol}: {data_stats['eligible_samples']:,} eligible samples (Dev+Val)", flush=True)

    # 2. Schema audit
    schema_stats = audit_feature_schema(df_clean, symbol)

    # 3. Check partition counts
    ts = df_clean["open_time_ms"]
    dev_samples = int(((ts >= DEVELOPMENT_START_MS) & (ts <= DEVELOPMENT_END_MS)).sum())
    val_samples = int(((ts >= VALIDATION_START_MS) & (ts <= VALIDATION_END_MS)).sum())
    is_short_history = dev_samples == 0 or len(df_clean) < 50_000

    # 4. Walk-forward splitter
    splitter = PurgedWalkForwardSplitter(
        n_splits=5,
        horizon_bars=12,
        embargo_bars=24,
        min_train_ratio=0.5,
        protect_test_horizon=True,
    )

    fold_meta = splitter.get_fold_metadata(df_clean)
    print(f"Generated {len(fold_meta)} walk-forward folds:", flush=True)
    for fm in fold_meta:
        print(
            f"  Fold {fm['fold']}: Train={fm['train_samples']:,} | Test={fm['test_samples']:,} "
            f"(Purged={fm['purged_samples']}, TestPurged={fm.get('test_purged_samples', 12)})",
            flush=True,
        )

    seed = SEED_OFFSETS.get(symbol, 42)
    fold_evaluations = []

    t_start_all = time.time()
    splits = list(splitter.split(df_clean))

    peak_rss = mem_before

    for fold_idx, (train_idx, test_idx) in enumerate(splits):
        print(f"  Training Fold {fold_idx+1}/5 ... ", end="", flush=True)
        t_fold_0 = time.time()
        res = train_and_eval_fold(fold_idx, train_idx, test_idx, df_clean, symbol, seed, out_dir)
        fold_evaluations.append(res)
        cur_rss = process.memory_info().rss / (1024 * 1024)
        peak_rss = max(peak_rss, cur_rss)
        print(f"DONE in {time.time()-t_fold_0:.2f}s | Current RSS: {cur_rss:.1f} MB", flush=True)

    total_duration = time.time() - t_start_all

    # Explicit garbage collection
    del df_clean
    gc.collect()
    mem_after = process.memory_info().rss / (1024 * 1024)

    # Compute aggregate metrics per model
    models = ["B0_Majority", "B1_Prior", "B2_LogisticRegression", "B3_RandomForest", "B4_LightGBM"]
    aggregate_summary: Dict[str, Any] = {}
    for m in models:
        accs = [f["models"][m]["accuracy"] for f in fold_evaluations]
        bal_accs = [f["models"][m]["balanced_accuracy"] for f in fold_evaluations]
        macro_f1s = [f["models"][m]["macro_f1"] for f in fold_evaluations]
        briers = [f["models"][m]["brier_score"] for f in fold_evaluations]
        roc_aucs = [
            f["models"][m]["roc_auc_ovr"]
            for f in fold_evaluations
            if f["models"][m].get("roc_auc_ovr") is not None
        ]

        aggregate_summary[m] = {
            "mean_accuracy": round(float(np.mean(accs)), 4),
            "std_accuracy": round(float(np.std(accs)), 4),
            "mean_balanced_accuracy": round(float(np.mean(bal_accs)), 4),
            "std_balanced_accuracy": round(float(np.std(bal_accs)), 4),
            "mean_macro_f1": round(float(np.mean(macro_f1s)), 4),
            "std_macro_f1": round(float(np.std(macro_f1s)), 4),
            "mean_brier_score": round(float(np.mean(briers)), 4),
            "std_brier_score": round(float(np.std(briers)), 4),
            "mean_roc_auc": round(float(np.mean(roc_aucs)), 4) if roc_aucs else None,
        }

    print(f"\n--- {symbol} AGGREGATE VALIDATION SUMMARY ---", flush=True)
    for m in models:
        s = aggregate_summary[m]
        print(
            f"  {m:22s} | BalAcc: {s['mean_balanced_accuracy']:.4f} +/- {s['std_balanced_accuracy']:.4f} "
            f"| MacroF1: {s['mean_macro_f1']:.4f} | Brier: {s['mean_brier_score']:.4f}",
            flush=True,
        )

    # Manifests and summaries
    dataset_manifest = {
        "symbol": symbol,
        "exchange": EXCHANGE.value,
        "timeframe": TIMEFRAME.value,
        "dev_start_ms": DEVELOPMENT_START_MS,
        "val_end_ms": VALIDATION_END_MS,
        "total_canonical": data_stats["total_canonical"],
        "total_dev_val_features": data_stats["total_dev_val_features"],
        "eligible_samples": data_stats["eligible_samples"],
        "tp_count": data_stats["tp_count"],
        "sl_count": data_stats["sl_count"],
        "exp_count": data_stats["exp_count"],
        "ambiguous_count": data_stats["ambiguous_count"],
        "excluded_count": data_stats["excluded_count"],
        "schema_hash": schema_stats["schema_hash"],
    }
    with open(out_dir / "dataset_manifest.json", "w") as f:
        json.dump(dataset_manifest, f, indent=2)

    with open(out_dir / "fold_manifest.json", "w") as f:
        json.dump(fold_meta, f, indent=2)

    model_configs = {
        "symbol": symbol,
        "seed": seed,
        "models": {
            "B0_Majority": {"type": "MajorityClassBaseline"},
            "B1_Prior": {"type": "PriorProbabilityBaseline"},
            "B2_LogisticRegression": BaselineModelFactory.get_logistic_regression_spec(c_penalty=1.0, random_seed=seed),
            "B3_RandomForest": BaselineModelFactory.get_random_forest_spec(n_estimators=100, max_depth=8, min_samples_leaf=50, random_seed=seed),
            "B4_LightGBM": BaselineModelFactory.get_lightgbm_spec(n_estimators=100, learning_rate=0.05, num_leaves=31, random_seed=seed),
        },
    }
    with open(out_dir / "model_configs.json", "w") as f:
        json.dump(model_configs, f, indent=2)

    resource_benchmark = {
        "symbol": symbol,
        "mem_before_mb": round(mem_before, 1),
        "peak_rss_mb": round(peak_rss, 1),
        "mem_after_gc_mb": round(mem_after, 1),
        "total_duration_s": round(total_duration, 2),
        "within_1gb_budget": peak_rss < 1024.0,
    }
    with open(out_dir / "resource_benchmark.json", "w") as f:
        json.dump(resource_benchmark, f, indent=2)

    summary_obj = {
        "symbol": symbol,
        "is_short_history": is_short_history,
        "dev_samples": dev_samples,
        "val_samples": val_samples,
        "data_stats": data_stats,
        "schema_stats": schema_stats,
        "fold_metadata": fold_meta,
        "fold_evaluations": fold_evaluations,
        "aggregate_summary": aggregate_summary,
        "resource_benchmark": resource_benchmark,
    }
    with open(out_dir / "summary.json", "w") as f:
        json.dump(summary_obj, f, indent=2)

    return summary_obj


def verify_deterministic_replay(
    storage: ParquetStorageManager,
    symbol: str = "ETHUSDT",
) -> Dict[str, Any]:
    """Replay Fold 1 for ETHUSDT under identical seed and compare predictions."""
    print("\n========================================================", flush=True)
    print(f"DETERMINISTIC REPLAY VERIFICATION: {symbol} Fold 1", flush=True)
    print("========================================================", flush=True)

    df_clean, _ = prepare_labeled_dataset(storage, symbol)
    splitter = PurgedWalkForwardSplitter(
        n_splits=5,
        horizon_bars=12,
        embargo_bars=24,
        min_train_ratio=0.5,
        protect_test_horizon=True,
    )
    splits = list(splitter.split(df_clean))
    train_idx, test_idx = splits[0]

    seed = SEED_OFFSETS.get(symbol, 42)

    # 1. Run 1 (in temporary dir)
    tmp_dir1 = ARTIFACTS_DIR / "_replay_tmp1"
    tmp_dir1.mkdir(parents=True, exist_ok=True)
    res1 = train_and_eval_fold(0, train_idx, test_idx, df_clean, symbol, seed, tmp_dir1)

    # 2. Run 2 (in temporary dir)
    tmp_dir2 = ARTIFACTS_DIR / "_replay_tmp2"
    tmp_dir2.mkdir(parents=True, exist_ok=True)
    res2 = train_and_eval_fold(0, train_idx, test_idx, df_clean, symbol, seed, tmp_dir2)

    # Load predictions
    with open(tmp_dir1 / "fold_1" / "predictions.json") as f:
        pred1 = json.load(f)
    with open(tmp_dir2 / "fold_1" / "predictions.json") as f:
        pred2 = json.load(f)

    pred_match = (
        pred1["predictions"]["B4_LightGBM"]["pred_hash"]
        == pred2["predictions"]["B4_LightGBM"]["pred_hash"]
    )
    proba_match = (
        pred1["predictions"]["B4_LightGBM"]["proba_hash"]
        == pred2["predictions"]["B4_LightGBM"]["proba_hash"]
    )

    eval_match = (
        res1["models"]["B4_LightGBM"]["macro_f1"]
        == res2["models"]["B4_LightGBM"]["macro_f1"]
    )

    # Cleanup temp dirs
    import shutil
    shutil.rmtree(tmp_dir1, ignore_errors=True)
    shutil.rmtree(tmp_dir2, ignore_errors=True)

    replay_res = {
        "replay_symbol": symbol,
        "fold": 1,
        "predictions_exact_match": pred_match,
        "probabilities_exact_match": proba_match,
        "evaluation_exact_match": eval_match,
        "bit_exact_reproducibility": pred_match and proba_match and eval_match,
    }
    print(f"Replay Result for {symbol} Fold 1: {replay_res}", flush=True)
    return replay_res


def build_fleet_catalog() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Integrate Phase 5.3.1 pilot results and Phase 5.3.2 fleet results."""
    print("\n========================================================", flush=True)
    print("INTEGRATING FLEET CATALOG (11 SPECIALISTS)", flush=True)
    print("========================================================", flush=True)

    fleet_summary_dir = ARTIFACTS_DIR / "fleet_summary"
    fleet_summary_dir.mkdir(parents=True, exist_ok=True)

    fleet_catalog: Dict[str, Any] = {}

    # 1. Load Phase 5.3.1 pilot results
    pilot_path = PILOT_ARTIFACTS_DIR / "pilot_summary.json"
    if pilot_path.exists():
        with open(pilot_path) as f:
            pilot_data = json.load(f)
        for sym in ["BTCUSDT", "XMRUSDT"]:
            if sym in pilot_data:
                fleet_catalog[sym] = pilot_data[sym]
                fleet_catalog[sym]["origin_phase"] = "Phase 5.3.1 Pilot"

    # 2. Load Phase 5.3.2 expanded fleet results
    for sym in REMAINING_SYMBOLS:
        sym_summary_path = ARTIFACTS_DIR / sym / "summary.json"
        if sym_summary_path.exists():
            with open(sym_summary_path) as f:
                sym_data = json.load(f)
            fleet_catalog[sym] = sym_data
            fleet_catalog[sym]["origin_phase"] = "Phase 5.3.2 Expanded Fleet"

    # Save master catalog
    with open(fleet_summary_dir / "fleet_catalog.json", "w") as f:
        json.dump(fleet_catalog, f, indent=2)

    # Build comparative analysis
    fleet_comparison: Dict[str, Any] = {
        "total_instruments": len(fleet_catalog),
        "instruments": list(fleet_catalog.keys()),
        "comparison_table": [],
    }

    for sym, data in fleet_catalog.items():
        aggs = data.get("aggregate_summary", {})
        b0 = aggs.get("B0_Majority", {})
        b1 = aggs.get("B1_Prior", {})
        b2 = aggs.get("B2_LogisticRegression", {})
        b3 = aggs.get("B3_RandomForest", {})
        b4 = aggs.get("B4_LightGBM", {})

        # Find best model
        candidate_models = ["B2_LogisticRegression", "B3_RandomForest", "B4_LightGBM"]
        best_bal_acc_model = max(
            candidate_models,
            key=lambda m: aggs.get(m, {}).get("mean_balanced_accuracy", 0.0),
        )
        best_f1_model = max(
            candidate_models,
            key=lambda m: aggs.get(m, {}).get("mean_macro_f1", 0.0),
        )
        lowest_brier_model = min(
            candidate_models,
            key=lambda m: aggs.get(m, {}).get("mean_brier_score", 999.0),
        )

        row = {
            "symbol": sym,
            "origin": data.get("origin_phase", "Unknown"),
            "eligible_samples": data.get("data_stats", {}).get("eligible_samples", 0),
            "is_short_history": data.get("is_short_history", False),
            "B0_bal_acc": b0.get("mean_balanced_accuracy"),
            "B0_macro_f1": b0.get("mean_macro_f1"),
            "B2_bal_acc": b2.get("mean_balanced_accuracy"),
            "B2_macro_f1": b2.get("mean_macro_f1"),
            "B3_bal_acc": b3.get("mean_balanced_accuracy"),
            "B3_macro_f1": b3.get("mean_macro_f1"),
            "B4_bal_acc": b4.get("mean_balanced_accuracy"),
            "B4_macro_f1": b4.get("mean_macro_f1"),
            "B4_brier": b4.get("mean_brier_score"),
            "B4_roc_auc": b4.get("mean_roc_auc"),
            "best_bal_acc_model": best_bal_acc_model,
            "best_f1_model": best_f1_model,
            "lowest_brier_model": lowest_brier_model,
        }
        fleet_comparison["comparison_table"].append(row)

    with open(fleet_summary_dir / "fleet_comparison.json", "w") as f:
        json.dump(fleet_comparison, f, indent=2)

    # Compute manifest hashes for all artifacts in phase_5_3_2
    hashes: Dict[str, str] = {}
    for root, _, files in os.walk(ARTIFACTS_DIR):
        for file in sorted(files):
            p = Path(root) / file
            rel_p = str(p.relative_to(ARTIFACTS_DIR)).replace("\\", "/")
            hashes[rel_p] = compute_sha256(p)

    with open(fleet_summary_dir / "manifest_hashes.json", "w") as f:
        json.dump(hashes, f, indent=2)

    print(f"Catalog completed for {len(fleet_catalog)} instruments. Hashes cataloged: {len(hashes)}.", flush=True)
    return fleet_catalog, fleet_comparison


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Phase 5.3.2 Specialist Fleet Baseline Training")
    parser.add_argument(
        "--symbol",
        type=str,
        default="ALL",
        help="Specific symbol to train or 'ALL' for all 9 remaining instruments",
    )
    args = parser.parse_args()

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    process = psutil.Process(os.getpid())
    storage = ParquetStorageManager(base_dir=BASE_DIR)

    if args.symbol.upper() == "ALL":
        target_symbols = REMAINING_SYMBOLS
    elif "," in args.symbol:
        target_symbols = [s.strip().upper() for s in args.symbol.split(",") if s.strip()]
    else:
        target_symbols = [args.symbol.upper()]

    print(f"Starting Phase 5.3.2 Fleet Training for: {target_symbols}", flush=True)

    for sym in target_symbols:
        _ = run_experiment_for_symbol(storage, sym, process)

    # Run replay verification on ETHUSDT if ETHUSDT was trained or if running ALL
    if "ETHUSDT" in target_symbols:
        _ = verify_deterministic_replay(storage, "ETHUSDT")

    # If all remaining symbols completed, build catalog
    all_completed = all((ARTIFACTS_DIR / s / "summary.json").exists() for s in REMAINING_SYMBOLS)
    if all_completed:
        build_fleet_catalog()

    print("\nPhase 5.3.2 execution finished successfully.", flush=True)


if __name__ == "__main__":
    main()
