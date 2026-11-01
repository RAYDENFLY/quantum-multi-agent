"""Phase 5.3.1 Pilot Baseline Training and Validation Runner.

Executes:
1. Feature schema reconciliation and integrity verification for BTCUSDT and XMRUSDT.
2. Purged and embargoed 5-fold walk-forward validation on BTCUSDT (B0-B4).
3. Short-history feasibility audit and walk-forward evaluation on XMRUSDT.
4. Deterministic replay verification on BTCUSDT Fold 1.
5. Resource benchmarking (memory RSS, training duration, artifact sizing).
6. Exports auditable experiment manifests, artifacts, and summary metrics.
"""

from datetime import datetime, timezone
import gc
import json
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Tuple
import joblib
import numpy as np
import pandas as pd
import psutil

from quantum.domain.enums import Exchange, Timeframe
from quantum.features.labeling import BarrierOutcome, TripleBarrierLabelGenerator
from quantum.features.schema import RESEARCH_FEATURE_COLUMNS
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
ARTIFACTS_DIR = Path("artifacts/phase_5_3_1")
EXCHANGE = Exchange.ASTER
TIMEFRAME = Timeframe.M5

SEED_OFFSETS = {
    "BTCUSDT": 342,
    "XMRUSDT": 942,
}


def audit_feature_schema(df: pd.DataFrame, symbol: str) -> Dict[str, Any]:
    """Verify feature matrix columns, data types, and finiteness."""
    cols = list(df.columns)
    has_timestamps = "open_time_ms" in cols and "close_time_ms" in cols
    model_feature_cols = [c for c in cols if c not in ("open_time_ms", "close_time_ms", "label", "exclusion_reason")]
    
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
    # Note: storage.read_canonical and read_features have identical row alignment
    feat_files = sorted((BASE_DIR / f"features_research/exchange={EXCHANGE.value}/symbol={symbol}/timeframe={TIMEFRAME.value}").glob("*.parquet"))
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
    
    fold_results = {
        "fold": fold_idx + 1,
        "train_samples": int(len(train_idx)),
        "test_samples": int(len(test_idx)),
        "preprocessor_duration_s": round(prep_duration, 4),
        "models": {},
    }
    
    classes = [-1, 0, 1]
    
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
    
    # Model B3: Balanced Random Forest
    b3 = BaselineModelFactory.create_random_forest(n_estimators=100, max_depth=8, min_samples_leaf=50, random_seed=seed)
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
    
    # Model B4: LightGBM
    b4 = BaselineModelFactory.create_lightgbm(n_estimators=100, learning_rate=0.05, num_leaves=31, random_seed=seed)
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
    
    # Save fold artifacts for B4 and B3
    fold_art_dir = out_dir / f"fold_{fold_idx+1}"
    fold_art_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(b4, fold_art_dir / "lgbm_model.joblib")
    joblib.dump(preprocessor, fold_art_dir / "preprocessor.joblib")
    with open(fold_art_dir / "metrics.json", "w") as f:
        json.dump(fold_results, f, indent=2)
        
    return fold_results


def run_pilot_for_symbol(
    storage: ParquetStorageManager,
    symbol: str,
    process: psutil.Process,
) -> Dict[str, Any]:
    """Run full pilot baseline experiment for one symbol."""
    print(f"\n========================================================")
    print(f"PILOT EXECUTION: {symbol}")
    print(f"========================================================")
    
    out_dir = ARTIFACTS_DIR / symbol
    out_dir.mkdir(parents=True, exist_ok=True)
    
    mem_before = process.memory_info().rss / (1024 * 1024)
    
    # 1. Prepare clean labeled dataset
    df_clean, data_stats = prepare_labeled_dataset(storage, symbol)
    print(f"Loaded {symbol}: {data_stats['eligible_samples']:,} eligible samples (Dev+Val)")
    
    # Schema audit
    schema_stats = audit_feature_schema(df_clean, symbol)
    
    # Check minimum history sufficiency
    # If symbol has zero Development samples or fewer than 50,000 samples, evaluate feasibility
    ts = df_clean["open_time_ms"]
    dev_samples = int(((ts >= DEVELOPMENT_START_MS) & (ts <= DEVELOPMENT_END_MS)).sum())
    val_samples = int(((ts >= VALIDATION_START_MS) & (ts <= VALIDATION_END_MS)).sum())
    
    is_short_history = dev_samples == 0 or len(df_clean) < 50_000
    
    splitter = PurgedWalkForwardSplitter(
        n_splits=5,
        horizon_bars=12,
        embargo_bars=24,
        min_train_ratio=0.5,
        protect_test_horizon=True,
    )
    
    fold_meta = splitter.get_fold_metadata(df_clean)
    print(f"Generated {len(fold_meta)} walk-forward folds:")
    for fm in fold_meta:
        print(f"  Fold {fm['fold']}: Train={fm['train_samples']:,} | Test={fm['test_samples']:,} (Purged={fm['purged_samples']}, TestPurged={fm.get('test_purged_samples', 12)})")
        
    seed = SEED_OFFSETS.get(symbol, 42)
    fold_evaluations = []
    
    t_start_all = time.time()
    splits = list(splitter.split(df_clean))
    
    peak_rss = mem_before
    
    for fold_idx, (train_idx, test_idx) in enumerate(splits):
        print(f"  Training Fold {fold_idx+1}/5 ...", end="", flush=True)
        t_fold_0 = time.time()
        res = train_and_eval_fold(fold_idx, train_idx, test_idx, df_clean, symbol, seed, out_dir)
        fold_evaluations.append(res)
        cur_rss = process.memory_info().rss / (1024 * 1024)
        peak_rss = max(peak_rss, cur_rss)
        print(f" DONE in {time.time()-t_fold_0:.2f}s | Current RSS: {cur_rss:.1f} MB")
        
    total_duration = time.time() - t_start_all
    
    # Explicit garbage collection
    del df_clean
    gc.collect()
    mem_after = process.memory_info().rss / (1024 * 1024)
    
    # Compute aggregate metrics per model
    models = ["B0_Majority", "B1_Prior", "B2_LogisticRegression", "B3_RandomForest", "B4_LightGBM"]
    aggregate_summary = {}
    for m in models:
        accs = [f["models"][m]["accuracy"] for f in fold_evaluations]
        bal_accs = [f["models"][m]["balanced_accuracy"] for f in fold_evaluations]
        macro_f1s = [f["models"][m]["macro_f1"] for f in fold_evaluations]
        briers = [f["models"][m]["brier_score"] for f in fold_evaluations]
        roc_aucs = [f["models"][m]["roc_auc_ovr"] for f in fold_evaluations if f["models"][m]["roc_auc_ovr"] is not None]
        
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
        
    print(f"\n--- {symbol} AGGREGATE VALIDATION SUMMARY ---")
    for m in models:
        s = aggregate_summary[m]
        print(f"  {m:22s} | BalAcc: {s['mean_balanced_accuracy']:.4f} +/- {s['std_balanced_accuracy']:.4f} | MacroF1: {s['mean_macro_f1']:.4f} | Brier: {s['mean_brier_score']:.4f}")
        
    return {
        "symbol": symbol,
        "is_short_history": is_short_history,
        "dev_samples": dev_samples,
        "val_samples": val_samples,
        "data_stats": data_stats,
        "schema_stats": schema_stats,
        "fold_metadata": fold_meta,
        "fold_evaluations": fold_evaluations,
        "aggregate_summary": aggregate_summary,
        "resource_benchmark": {
            "mem_before_mb": round(mem_before, 1),
            "peak_rss_mb": round(peak_rss, 1),
            "mem_after_gc_mb": round(mem_after, 1),
            "total_duration_s": round(total_duration, 2),
            "within_1gb_budget": peak_rss < 1024.0,
        },
    }


def verify_deterministic_replay(
    storage: ParquetStorageManager,
    symbol: str = "BTCUSDT",
) -> Dict[str, Any]:
    """Replay Fold 1 for BTCUSDT under identical seed and compare predictions."""
    print("\n========================================================")
    print("DETERMINISTIC REPLAY VERIFICATION: BTCUSDT Fold 1")
    print("========================================================")
    
    df_clean, _ = prepare_labeled_dataset(storage, symbol)
    splitter = PurgedWalkForwardSplitter(n_splits=5, horizon_bars=12, embargo_bars=24, min_train_ratio=0.5)
    train_idx, test_idx = next(splitter.split(df_clean))
    
    X_raw = df_clean[RESEARCH_STATIONARY_FEATURES]
    y = df_clean["label"].to_numpy(dtype=int)
    seed = SEED_OFFSETS[symbol]
    
    # Run 1
    prep1 = SpecialistPreprocessor(scaler_type="robust")
    X_tr1 = prep1.fit_transform(X_raw.iloc[train_idx])
    X_te1 = prep1.transform(X_raw.iloc[test_idx])
    rf1 = BaselineModelFactory.create_random_forest(n_estimators=100, max_depth=8, min_samples_leaf=50, random_seed=seed)
    rf1.fit(X_tr1, y[train_idx])
    p1 = rf1.predict(X_te1)
    prob1 = rf1.predict_proba(X_te1)
    
    # Run 2 (Replay)
    prep2 = SpecialistPreprocessor(scaler_type="robust")
    X_tr2 = prep2.fit_transform(X_raw.iloc[train_idx])
    X_te2 = prep2.transform(X_raw.iloc[test_idx])
    rf2 = BaselineModelFactory.create_random_forest(n_estimators=100, max_depth=8, min_samples_leaf=50, random_seed=seed)
    rf2.fit(X_tr2, y[train_idx])
    p2 = rf2.predict(X_te2)
    prob2 = rf2.predict_proba(X_te2)
    
    is_exact_pred = bool(np.array_equal(p1, p2))
    is_exact_prob = bool(np.allclose(prob1, prob2, atol=1e-12))
    is_exact_prep = bool(np.allclose(X_tr1, X_tr2, atol=1e-12))
    
    print(f"  Predictions Exact Match: {is_exact_pred}")
    print(f"  Probabilities Exact Match: {is_exact_prob}")
    print(f"  Preprocessor Scaling Exact Match: {is_exact_prep}")
    
    return {
        "replay_symbol": symbol,
        "fold": 1,
        "predictions_exact_match": is_exact_pred,
        "probabilities_exact_match": is_exact_prob,
        "preprocessor_exact_match": is_exact_prep,
        "bit_exact_reproducibility": is_exact_pred and is_exact_prob and is_exact_prep,
    }


def main():
    print("=" * 80)
    print("QUANTUM PHASE 5.3.1: PILOT BASELINE TRAINING & VALIDATION")
    print("=" * 80)
    
    process = psutil.Process(os.getpid())
    storage = ParquetStorageManager(BASE_DIR)
    
    results = {}
    
    # Pilot A: BTCUSDT (Long History)
    results["BTCUSDT"] = run_pilot_for_symbol(storage, "BTCUSDT", process)
    
    # Pilot B: XMRUSDT (Short History Feasibility)
    results["XMRUSDT"] = run_pilot_for_symbol(storage, "XMRUSDT", process)
    
    # Deterministic Replay Test
    replay_results = verify_deterministic_replay(storage, "BTCUSDT")
    results["replay_verification"] = replay_results
    
    # Save overall pilot summary
    out_file = ARTIFACTS_DIR / "pilot_summary.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved master pilot summary to {out_file}")


if __name__ == "__main__":
    main()
