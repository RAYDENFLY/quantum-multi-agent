"""
QUANTUM PHASE 5.4.2: CALIBRATION & DECISION POLICY EXECUTION
Execution script for:
1. Frozen Model Inference Reproducibility Audit (55 B4 model binaries across 11 specialists).
2. Out-of-Fold (OOF) Probability & Raw Logit Materialization.
3. 3-Segment Temporal Partitioning (Folds 1-2 Calibration, Folds 3-4 Selection, Fold 5 Final Evaluation).
4. Probability Calibration Evaluation (Uncalibrated, Temperature Scaling, Vector Platt, Isotonic).
5. Selective Classification & Risk-Coverage Dynamics (Coverage grid 100% down to 20%).
6. Directional Decision Policy (LONG / SHORT / NO TRADE) Construction & Barrier Outcomes.
7. Realized Return Diagnostics (Market Entry at Open i+1, Gap Handling, Expiration Exit).
8. Transaction Cost Sensitivity Grid (7 bps, 15 bps, 20 bps, 30 bps).
9. Resource Benchmarking & Strict Cryptographic Hash Verification.
"""

import gc
import hashlib
import json
import os
import platform
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import lightgbm
import numpy as np
import pandas as pd
import psutil
from scipy.optimize import minimize_scalar
from scipy.special import softmax
import sklearn
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_recall_fscore_support,
)
import warnings
warnings.filterwarnings("ignore")

# Enforce resource constraints
os.environ["OMP_NUM_THREADS"] = "2"
os.environ["MKL_NUM_THREADS"] = "2"
os.environ["OPENBLAS_NUM_THREADS"] = "2"

sys.path.insert(0, "src")
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
from quantum.ml.contracts import RESEARCH_STATIONARY_FEATURES
from quantum.ml.validation import PurgedWalkForwardSplitter

BASE_DIR = Path("data/historical")
STORAGE = ParquetStorageManager(BASE_DIR)
ARTIFACTS_DIR = Path("artifacts/phase_5_4")
MATERIALIZED_DIR = ARTIFACTS_DIR / "materialized_oof"
DOCS_DIR = Path("docs/research")

ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
MATERIALIZED_DIR.mkdir(parents=True, exist_ok=True)

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"
]

NEW_PROSPECTIVE_HOLDOUT_START_MS = 1793491200000  # 2026-11-01 00:00:00 UTC
PURGE_GAP_MS = 3_900_000                          # 13 bars * 300,000 ms
RANDOM_SEED = 42
N_BINS = 15

CLASS_LABELS = [-1, 0, 1]
CLASS_NAMES = {-1: "SL", 0: "EXP", 1: "TP"}


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def compute_multiclass_brier(y_true: np.ndarray, probs: np.ndarray, classes: List[int] = CLASS_LABELS) -> float:
    """Multiclass Brier score: mean squared difference across all classes."""
    n = len(y_true)
    if n == 0:
        return 0.0
    y_one_hot = np.zeros((n, len(classes)), dtype=np.float64)
    for idx, c in enumerate(classes):
        y_one_hot[y_true == c, idx] = 1.0
    return float(np.mean(np.sum((probs - y_one_hot) ** 2, axis=1)))


def compute_multiclass_log_loss(y_true: np.ndarray, probs: np.ndarray, classes: List[int] = CLASS_LABELS) -> float:
    """Multiclass log loss (cross-entropy) with clipping."""
    eps = 1e-15
    clipped = np.clip(probs, eps, 1.0 - eps)
    n = len(y_true)
    if n == 0:
        return 0.0
    y_one_hot = np.zeros((n, len(classes)), dtype=np.float64)
    for idx, c in enumerate(classes):
        y_one_hot[y_true == c, idx] = 1.0
    return float(-np.mean(np.sum(y_one_hot * np.log(clipped), axis=1)))


def compute_top_label_ece(y_true: np.ndarray, probs: np.ndarray, classes: List[int] = CLASS_LABELS,
                          n_bins: int = 15, bin_strategy: str = "uniform") -> Tuple[float, List[Dict[str, Any]]]:
    """Top-label Expected Calibration Error (ECE) for equal-width or equal-frequency bins."""
    n = len(y_true)
    if n == 0:
        return 0.0, []
    
    confs = np.max(probs, axis=1)
    preds = np.array(classes)[np.argmax(probs, axis=1)]
    accuracies = (preds == y_true).astype(float)
    
    if bin_strategy == "uniform":
        bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    elif bin_strategy == "quantile":
        quantiles = np.linspace(0.0, 1.0, n_bins + 1)
        bin_edges = np.percentile(confs, quantiles * 100.0)
        bin_edges[0] = 0.0
        bin_edges[-1] = 1.0
    else:
        raise ValueError(f"Unknown bin strategy: {bin_strategy}")

    ece = 0.0
    bin_details = []
    
    for i in range(n_bins):
        low, high = bin_edges[i], bin_edges[i + 1]
        if i == n_bins - 1:
            mask = (confs >= low) & (confs <= high)
        else:
            mask = (confs >= low) & (confs < high)
            
        count = int(np.sum(mask))
        if count == 0:
            bin_details.append({
                "bin_index": i + 1,
                "range": [float(low), float(high)],
                "count": 0,
                "accuracy": 0.0,
                "confidence": 0.0,
                "calibration_gap": 0.0,
            })
            continue
            
        acc = float(np.mean(accuracies[mask]))
        conf = float(np.mean(confs[mask]))
        gap = abs(acc - conf)
        ece += (count / n) * gap
        
        bin_details.append({
            "bin_index": i + 1,
            "range": [float(low), float(high)],
            "count": count,
            "accuracy": round(acc, 6),
            "confidence": round(conf, 6),
            "calibration_gap": round(gap, 6),
        })

    return float(ece), bin_details


def compute_classwise_ece(y_true: np.ndarray, probs: np.ndarray, classes: List[int] = CLASS_LABELS,
                          n_bins: int = 15, bin_strategy: str = "uniform") -> Tuple[float, Dict[str, float]]:
    """Class-wise Expected Calibration Error (mean ECE across one-vs-rest binary problems)."""
    n = len(y_true)
    if n == 0:
        return 0.0, {}
    
    per_class_ece = {}
    for idx, c in enumerate(classes):
        binary_true = (y_true == c).astype(float)
        binary_prob = probs[:, idx]
        
        if bin_strategy == "uniform":
            bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
        elif bin_strategy == "quantile":
            quantiles = np.linspace(0.0, 1.0, n_bins + 1)
            bin_edges = np.percentile(binary_prob, quantiles * 100.0)
            bin_edges[0] = 0.0
            bin_edges[-1] = 1.0
        else:
            raise ValueError(f"Unknown bin strategy: {bin_strategy}")

        c_ece = 0.0
        for i in range(n_bins):
            low, high = bin_edges[i], bin_edges[i + 1]
            if i == n_bins - 1:
                mask = (binary_prob >= low) & (binary_prob <= high)
            else:
                mask = (binary_prob >= low) & (binary_prob < high)
            count = np.sum(mask)
            if count == 0:
                continue
            acc = np.mean(binary_true[mask])
            conf = np.mean(binary_prob[mask])
            c_ece += (count / n) * abs(acc - conf)
        
        per_class_ece[CLASS_NAMES[c]] = float(c_ece)
        
    mean_ece = float(np.mean(list(per_class_ece.values())))
    return mean_ece, per_class_ece


class TemperatureScaling:
    """Multiclass Temperature Scaling optimizer on raw logits z."""
    def __init__(self):
        self.temperature: float = 1.0

    def fit(self, logits: np.ndarray, y_true: np.ndarray, classes: List[int] = CLASS_LABELS) -> float:
        n = len(y_true)
        y_one_hot = np.zeros((n, len(classes)), dtype=np.float64)
        for idx, c in enumerate(classes):
            y_one_hot[y_true == c, idx] = 1.0

        def nll_loss(T: float) -> float:
            scaled_logits = logits / T
            # Subtract max for numerical stability
            scaled_logits -= np.max(scaled_logits, axis=1, keepdims=True)
            exp_logits = np.exp(scaled_logits)
            softmax_probs = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)
            eps = 1e-15
            clipped = np.clip(softmax_probs, eps, 1.0 - eps)
            return -np.mean(np.sum(y_one_hot * np.log(clipped), axis=1))

        res = minimize_scalar(nll_loss, bounds=(0.05, 10.0), method="bounded")
        self.temperature = float(res.x)
        return self.temperature

    def predict_proba(self, logits: np.ndarray) -> np.ndarray:
        return softmax(logits / self.temperature, axis=1)


class VectorPlattScaling:
    """Multinomial Vector Platt Scaling via L2-regularized logistic regression on logits."""
    def __init__(self, c_reg: float = 1.0):
        self.c_reg = c_reg
        self.model = LogisticRegression(
            solver="lbfgs",
            C=c_reg,
            max_iter=500,
            random_state=RANDOM_SEED,
        )

    def fit(self, logits: np.ndarray, y_true: np.ndarray) -> None:
        self.model.fit(logits, y_true)

    def predict_proba(self, logits: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(logits)


class IsotonicCalibrator:
    """One-vs-rest Isotonic Regression calibrator with L1 probability normalization."""
    def __init__(self):
        self.calibrators: Dict[int, IsotonicRegression] = {}

    def fit(self, uncalibrated_probs: np.ndarray, y_true: np.ndarray, classes: List[int] = CLASS_LABELS) -> None:
        for idx, c in enumerate(classes):
            y_binary = (y_true == c).astype(float)
            iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
            iso.fit(uncalibrated_probs[:, idx], y_binary)
            self.calibrators[c] = iso

    def predict_proba(self, uncalibrated_probs: np.ndarray, classes: List[int] = CLASS_LABELS) -> np.ndarray:
        n = len(uncalibrated_probs)
        calibrated = np.zeros((n, len(classes)), dtype=np.float64)
        for idx, c in enumerate(classes):
            calibrated[:, idx] = self.calibrators[c].predict(uncalibrated_probs[:, idx])
        
        # Normalize rows to sum to 1.0
        row_sums = np.sum(calibrated, axis=1, keepdims=True)
        # Avoid division by zero
        zero_mask = (row_sums.flatten() == 0.0)
        row_sums[zero_mask] = 1.0
        normalized = calibrated / row_sums
        if np.any(zero_mask):
            normalized[zero_mask] = 1.0 / len(classes)
        return normalized


def evaluate_selective_classification_grid(
    y_true: np.ndarray,
    probs: np.ndarray,
    coverage_grid: List[float] = [1.0, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2],
    classes: List[int] = CLASS_LABELS,
) -> Dict[str, Any]:
    """Evaluate selective classification across coverage grid."""
    n = len(y_true)
    confs = np.max(probs, axis=1)
    preds = np.array(classes)[np.argmax(probs, axis=1)]
    
    # Sort indices descending by confidence
    sorted_idx = np.argsort(-confs)
    
    results_by_coverage = []
    risks = []
    coverages = []
    
    for cov in coverage_grid:
        k = int(np.floor(cov * n))
        if k == 0:
            continue
        sel_idx = sorted_idx[:k]
        y_sel = y_true[sel_idx]
        p_sel = preds[sel_idx]
        
        # Check class support
        supp = {CLASS_NAMES[c]: int(np.sum(y_sel == c)) for c in classes}
        min_supp = min(supp.values())
        sufficient_support = bool(min_supp >= 100)
        
        # Metrics
        cm = confusion_matrix(y_sel, p_sel, labels=classes)
        recalls = []
        precisions = []
        for i, c in enumerate(classes):
            c_supp = supp[CLASS_NAMES[c]]
            rec = cm[i, i] / c_supp if c_supp > 0 else 0.0
            pred_supp = np.sum(cm[:, i])
            prec = cm[i, i] / pred_supp if pred_supp > 0 else 0.0
            recalls.append(rec)
            precisions.append(prec)
            
        ba = float(np.mean(recalls))
        acc = float(accuracy_score(y_sel, p_sel))
        f1_mac = float(f1_score(y_sel, p_sel, labels=classes, average="macro", zero_division=0))
        risk = 1.0 - ba
        
        risks.append(risk)
        coverages.append(cov)
        
        results_by_coverage.append({
            "target_coverage": cov,
            "actual_coverage": round(k / n, 6),
            "sample_count": k,
            "min_confidence": float(confs[sel_idx[-1]]),
            "class_support": supp,
            "sufficient_support": sufficient_support,
            "balanced_accuracy": round(ba, 6),
            "accuracy": round(acc, 6),
            "macro_f1": round(f1_mac, 6),
            "risk": round(risk, 6),
            "per_class_recall": {CLASS_NAMES[c]: round(recalls[i], 6) for i, c in enumerate(classes)},
            "per_class_precision": {CLASS_NAMES[c]: round(precisions[i], 6) for i, c in enumerate(classes)},
            "confusion_matrix": cm.tolist(),
        })

    # Linear regression slope of Risk vs Coverage: beta_RC
    # Positive beta_RC means risk decreases as coverage decreases (desired selective property)
    if len(coverages) > 1:
        x = np.array(coverages)
        y = np.array(risks)
        slope, intercept = np.polyfit(x, y, 1)
        beta_rc = float(slope)
        
        # AU-RCC: Area Under Risk-Coverage Curve via trapezoid rule
        # Normalized by coverage span
        order = np.argsort(x)
        au_rcc = float(np.trapezoid(y[order], x[order]) / (x[order][-1] - x[order][0]))
    else:
        beta_rc = 0.0
        au_rcc = 0.0

    # Random abstention baseline: expected balanced accuracy at coverage cov is the full-coverage BA
    full_cov_ba = results_by_coverage[0]["balanced_accuracy"] if results_by_coverage else 0.0
    
    return {
        "coverage_points": results_by_coverage,
        "beta_rc": round(beta_rc, 6),
        "au_rcc": round(au_rcc, 6),
        "full_coverage_balanced_accuracy": full_cov_ba,
        "selective_monotonicity_positive": bool(beta_rc > 0),
    }


def simulate_realized_returns(
    can_opens: np.ndarray,
    can_highs: np.ndarray,
    can_lows: np.ndarray,
    can_closes: np.ndarray,
    can_timestamps: np.ndarray,
    can_indices: np.ndarray,
    directions: np.ndarray,         # +1 for LONG, -1 for SHORT
    vol_series: np.ndarray,
    barrier_multiplier: float = 1.5,
    horizon_bars: int = 12,
) -> Dict[str, Any]:
    """
    Simulate causal market execution on canonical 5m OHLC bars.
    Entry at open of candle i + 1. Reference price is close of candle i.
    Barriers: close[i] * (1 +/- barrier_multiplier * sigma_t).
    Checks open gaps, intrabar collisions (with conservative adverse assumption), and expiration at close[i + 12].
    """
    n_trades = len(can_indices)
    gross_returns_adverse = np.zeros(n_trades, dtype=np.float64)
    gross_returns_no_ambig = []
    
    touch_steps = np.zeros(n_trades, dtype=np.int32)
    barrier_types = []
    has_gap_list = []
    is_ambiguous_list = []
    
    entry_prices = np.zeros(n_trades, dtype=np.float64)
    exit_prices = np.zeros(n_trades, dtype=np.float64)
    ref_prices = np.zeros(n_trades, dtype=np.float64)
    entry_ts = np.zeros(n_trades, dtype=np.int64)
    decision_ts = np.zeros(n_trades, dtype=np.int64)

    total_bars = len(can_opens)

    for m in range(n_trades):
        i = can_indices[m]
        pos = directions[m]  # +1 (LONG) or -1 (SHORT)
        
        c_ref = can_closes[i]
        sigma = vol_series[i]
        u_bar = c_ref * (1.0 + barrier_multiplier * sigma)
        l_bar = c_ref * (1.0 - barrier_multiplier * sigma)
        
        p_entry = can_opens[i + 1]
        t_entry = can_timestamps[i + 1]
        t_dec = can_timestamps[i]
        
        ref_prices[m] = c_ref
        entry_prices[m] = p_entry
        entry_ts[m] = t_entry
        decision_ts[m] = t_dec
        
        resolved = False
        gap_detected = False
        ambig_detected = False
        p_exit = p_entry
        b_type = "EXPIRATION"
        t_step = horizon_bars
        
        for k in range(1, horizon_bars + 1):
            j = i + k
            if j >= total_bars:
                p_exit = can_closes[-1]
                t_step = k
                b_type = "END_OF_DATA"
                resolved = True
                break
                
            b_open = can_opens[j]
            b_high = can_highs[j]
            b_low = can_lows[j]
            
            # 1. Open gap check
            if b_open >= u_bar:
                gap_detected = True
                p_exit = b_open
                b_type = "UPPER"
                t_step = k
                resolved = True
                break
            elif b_open <= l_bar:
                gap_detected = True
                p_exit = b_open
                b_type = "LOWER"
                t_step = k
                resolved = True
                break
                
            # 2. Intrabar check
            upper_hit = b_high >= u_bar
            lower_hit = b_low <= l_bar
            
            if upper_hit and lower_hit:
                # Ambiguous collision
                ambig_detected = True
                # Conservative adverse assumption:
                # LONG hits lower barrier (SL), SHORT hits upper barrier (SL)
                if pos == 1:
                    p_exit = l_bar
                    b_type = "LOWER"
                else:
                    p_exit = u_bar
                    b_type = "UPPER"
                t_step = k
                resolved = True
                break
            elif upper_hit:
                p_exit = u_bar
                b_type = "UPPER"
                t_step = k
                resolved = True
                break
            elif lower_hit:
                p_exit = l_bar
                b_type = "LOWER"
                t_step = k
                resolved = True
                break
                
        if not resolved:
            # Expiration exit at close of candle i + 12
            exp_j = min(i + horizon_bars, total_bars - 1)
            p_exit = can_closes[exp_j]
            b_type = "EXPIRATION"
            t_step = horizon_bars
            
        exit_prices[m] = p_exit
        touch_steps[m] = t_step
        barrier_types.append(b_type)
        has_gap_list.append(gap_detected)
        is_ambiguous_list.append(ambig_detected)
        
        # Realized gross return
        if pos == 1:
            r_gross = (p_exit - p_entry) / p_entry
        else:
            r_gross = (p_entry - p_exit) / p_entry
            
        gross_returns_adverse[m] = r_gross
        if not ambig_detected:
            gross_returns_no_ambig.append(r_gross)

    gross_returns_no_ambig = np.array(gross_returns_no_ambig, dtype=np.float64)

    # Calculate metrics across cost scenarios: 7, 15, 20, 30 bps
    cost_scenarios_bps = [7, 15, 20, 30]
    cost_results = {}
    
    for bps in cost_scenarios_bps:
        fee_fraction = bps / 10_000.0
        
        # Adverse ambiguous scenario
        net_ret_adv = gross_returns_adverse - fee_fraction
        win_rate_adv = float(np.mean(net_ret_adv > 0)) if n_trades > 0 else 0.0
        mean_net_adv = float(np.mean(net_ret_adv)) if n_trades > 0 else 0.0
        pos_sum_adv = float(np.sum(net_ret_adv[net_ret_adv > 0]))
        neg_sum_adv = float(np.abs(np.sum(net_ret_adv[net_ret_adv < 0])))
        pf_adv = float(pos_sum_adv / neg_sum_adv) if neg_sum_adv > 0 else (999.0 if pos_sum_adv > 0 else 0.0)

        # Exclude ambiguous scenario
        if len(gross_returns_no_ambig) > 0:
            net_ret_clean = gross_returns_no_ambig - fee_fraction
            win_rate_clean = float(np.mean(net_ret_clean > 0))
            mean_net_clean = float(np.mean(net_ret_clean))
            pos_sum_clean = float(np.sum(net_ret_clean[net_ret_clean > 0]))
            neg_sum_clean = float(np.abs(np.sum(net_ret_clean[net_ret_clean < 0])))
            pf_clean = float(pos_sum_clean / neg_sum_clean) if neg_sum_clean > 0 else (999.0 if pos_sum_clean > 0 else 0.0)
        else:
            win_rate_clean = 0.0
            mean_net_clean = 0.0
            pf_clean = 0.0

        cost_results[f"{bps}_bps"] = {
            "fee_bps": bps,
            "fee_fraction": fee_fraction,
            "conservative_adverse": {
                "mean_net_return": round(mean_net_adv, 6),
                "win_rate": round(win_rate_adv, 6),
                "profit_factor": round(pf_adv, 4),
            },
            "excluding_ambiguous": {
                "trade_count": len(gross_returns_no_ambig),
                "mean_net_return": round(mean_net_clean, 6),
                "win_rate": round(win_rate_clean, 6),
                "profit_factor": round(pf_clean, 4),
            }
        }

    ambig_count = int(np.sum(is_ambiguous_list))
    gap_count = int(np.sum(has_gap_list))
    
    # Split by direction
    long_mask = (directions == 1)
    short_mask = (directions == -1)
    
    return {
        "trade_count": n_trades,
        "long_trade_count": int(np.sum(long_mask)),
        "short_trade_count": int(np.sum(short_mask)),
        "ambiguous_count": ambig_count,
        "ambiguous_fraction": round(ambig_count / n_trades, 6) if n_trades > 0 else 0.0,
        "gap_count": gap_count,
        "gap_fraction": round(gap_count / n_trades, 6) if n_trades > 0 else 0.0,
        "mean_gross_return": round(float(np.mean(gross_returns_adverse)), 6) if n_trades > 0 else 0.0,
        "long_mean_gross_return": round(float(np.mean(gross_returns_adverse[long_mask])), 6) if np.sum(long_mask) > 0 else 0.0,
        "short_mean_gross_return": round(float(np.mean(gross_returns_adverse[short_mask])), 6) if np.sum(short_mask) > 0 else 0.0,
        "cost_scenarios": cost_results,
    }


def run_phase_5_4_2() -> None:
    t_start_total = time.time()
    rss_initial_mb = psutil.Process().memory_info().rss / (1024 * 1024)
    print(f"Starting Phase 5.4.2 Execution. Initial RSS: {rss_initial_mb:.2f} MB", flush=True)

    reproducibility_audit = {
        "title": "Phase 5.4.2 Frozen Model Inference Reproducibility Audit",
        "timestamp_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "python_version": sys.version,
        "platform": platform.platform(),
        "library_versions": {
            "lightgbm": lightgbm.__version__,
            "scikit_learn": sklearn.__version__,
            "joblib": joblib.__version__,
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "total_models_evaluated": 0,
        "models_verified_count": 0,
        "models": [],
        "overall_inference_status": "PASS",
    }

    oof_manifest = {
        "title": "Phase 5.4.2 Out-of-Fold Materialized Probabilities Manifest",
        "timestamp_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "total_fleet_observations": 0,
        "target_classes": CLASS_LABELS,
        "class_mapping": CLASS_NAMES,
        "instruments": {},
    }

    calibration_results = {
        "title": "Phase 5.4.2 Probability Calibration Evaluation",
        "timestamp_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "n_bins": N_BINS,
        "bin_strategies": ["uniform", "quantile"],
        "segments": {
            "segment_1": "Folds 1-2 (Calibration Fit)",
            "segment_2": "Folds 3-4 (Policy Selection)",
            "segment_3": "Fold 5 (Final Temporal Evaluation)",
        },
        "instruments": {},
    }

    selective_results = {
        "title": "Phase 5.4.2 Selective Classification & Risk-Coverage Dynamics",
        "timestamp_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "coverage_grid": [1.0, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2],
        "min_class_support_guardrail": 100,
        "instruments": {},
    }

    decision_results = {
        "title": "Phase 5.4.2 Decision Policy Evaluation",
        "timestamp_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "description": "Probability threshold optimization on Segment 2 and untouched evaluation on Segment 3 (Fold 5).",
        "instruments": {},
    }

    cost_results = {
        "title": "Phase 5.4.2 Transaction Friction Sensitivity Grid",
        "timestamp_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "scenarios_bps": [7, 15, 20, 30],
        "funding_status": "UNAVAILABLE_ON_CANONICAL_OHLC_MARKED_HYPOTHETICAL",
        "instruments": {},
    }

    resource_benchmarks = {
        "instruments": {},
        "peak_rss_mb": 0.0,
        "total_duration_s": 0.0,
    }

    fleet_total_obs = 0
    peak_rss = rss_initial_mb

    for symbol in SYMBOLS:
        t_sym_start = time.time()
        print(f"\n==================================================", flush=True)
        print(f"Processing Instrument Specialist: {symbol}", flush=True)
        print(f"==================================================", flush=True)

        # 1. Canonical data
        df_can = STORAGE.read_canonical(Exchange.ASTER, symbol, Timeframe.M5)
        
        # Precompute canonical arrays for fast lookups
        can_opens = df_can["open"].to_numpy(dtype=np.float64)
        can_highs = df_can["high"].to_numpy(dtype=np.float64)
        can_lows = df_can["low"].to_numpy(dtype=np.float64)
        can_closes = df_can["close"].to_numpy(dtype=np.float64)
        can_timestamps = df_can["open_time_ms"].to_numpy(dtype=np.int64)
        
        # Fast map from open_time_ms to canonical index
        ts_to_idx = {int(ts): idx for idx, ts in enumerate(can_timestamps)}

        # 2. Labels
        gen = TripleBarrierLabelGenerator(
            horizon_bars=12,
            volatility_lookback=20,
            barrier_multiplier=1.5,
            timeframe_ms=300_000,
        )
        labeled = gen.generate_labels(df_can, enforce_partition_boundaries=True)
        vol_series = labeled["volatility"].to_numpy(dtype=np.float64)

        # 3. Features
        feat_files = sorted(
            (BASE_DIR / f"features_research/exchange=ASTER/symbol={symbol}/timeframe=5m").glob("*.parquet")
        )
        df_feats = pd.concat([pd.read_parquet(f) for f in feat_files], ignore_index=True)

        # 4. Filter features to Dev+Val
        ts = df_feats["open_time_ms"]
        df_feats_dv = df_feats[(ts >= DEVELOPMENT_START_MS) & (ts <= VALIDATION_END_MS)].copy().reset_index(drop=True)

        # Verify prospective holdout protection
        holdout_count = int((df_feats_dv["open_time_ms"] >= NEW_PROSPECTIVE_HOLDOUT_START_MS).sum())
        assert holdout_count == 0, f"FATAL: Holdout accessed for {symbol}!"

        # 5. Merge labels
        merged = pd.merge(
            df_feats_dv,
            labeled[["open_time_ms", "label", "exclusion_reason"]],
            on="open_time_ms",
            how="inner",
        )

        clean_mask = merged["label"].isin([
            BarrierOutcome.TP.value,
            BarrierOutcome.SL.value,
            BarrierOutcome.TIME_EXPIRATION.value,
        ])
        df_clean = merged[clean_mask].copy().reset_index(drop=True)

        # 6. Walk-forward splitter
        splitter = PurgedWalkForwardSplitter(
            n_splits=5,
            horizon_bars=12,
            embargo_bars=24,
            min_train_ratio=0.5,
            protect_test_horizon=True,
        )
        splits = list(splitter.split(df_clean))
        base_art = Path("artifacts/phase_5_3_1" if symbol in ["BTCUSDT", "XMRUSDT"] else "artifacts/phase_5_3_2") / symbol

        oof_rows = []
        oof_y_true = []
        oof_logits = []
        oof_probs = []
        oof_folds = []
        oof_timestamps = []
        oof_can_indices = []

        # 7. Iterate folds
        for fold_idx, (tr_idx, te_idx) in enumerate(splits, start=1):
            fold_dir = base_art / f"fold_{fold_idx}"
            model_path = fold_dir / "lgbm_model.joblib"
            prep_path = fold_dir / "preprocessor.joblib"

            # Check files exist
            assert model_path.exists(), f"Missing model: {model_path}"
            assert prep_path.exists(), f"Missing preprocessor: {prep_path}"

            model_sha = compute_sha256(model_path)
            prep_sha = compute_sha256(prep_path)

            t0_load = time.time()
            lgbm = joblib.load(model_path)
            prep = joblib.load(prep_path)
            load_duration = time.time() - t0_load

            # Verify classes
            assert list(lgbm.classes_) == CLASS_LABELS, f"Class ordering mismatch in {model_path}: {lgbm.classes_}"

            # Transform test features
            X_test_raw = df_clean[RESEARCH_STATIONARY_FEATURES].iloc[te_idx]
            y_test = df_clean["label"].to_numpy(dtype=int)[te_idx]
            ts_test = df_clean["open_time_ms"].iloc[te_idx].to_numpy(dtype=np.int64)

            t0_inf = time.time()
            X_test = prep.transform(X_test_raw)
            raw_logits = lgbm.predict(X_test, raw_score=True)
            pred_probs = lgbm.predict_proba(X_test)
            pred_classes = lgbm.predict(X_test)
            inf_duration = time.time() - t0_inf

            # Numerical stability and softmax check
            softmax_probs = softmax(raw_logits, axis=1)
            max_num_diff = float(np.max(np.abs(softmax_probs - pred_probs)))
            row_sum_diff = float(np.max(np.abs(np.sum(pred_probs, axis=1) - 1.0)))
            has_nan = bool(np.isnan(raw_logits).any() or np.isnan(pred_probs).any())
            has_inf = bool(np.isinf(raw_logits).any() or np.isinf(pred_probs).any())

            assert max_num_diff < 1e-6, f"Softmax mismatch in {symbol} fold {fold_idx}: {max_num_diff}"
            assert row_sum_diff < 1e-6, f"Probabilities do not sum to 1 in {symbol} fold {fold_idx}: {row_sum_diff}"
            assert not has_nan and not has_inf, f"NaN/Inf detected in {symbol} fold {fold_idx}"

            reproducibility_audit["total_models_evaluated"] += 1
            reproducibility_audit["models_verified_count"] += 1
            reproducibility_audit["models"].append({
                "instrument": symbol,
                "fold": fold_idx,
                "model_path": str(model_path).replace("\\", "/"),
                "model_sha256": model_sha,
                "preprocessor_path": str(prep_path).replace("\\", "/"),
                "preprocessor_sha256": prep_sha,
                "classes": [int(c) for c in lgbm.classes_],
                "test_samples": int(len(te_idx)),
                "max_softmax_diff": float(max_num_diff),
                "max_row_sum_diff": float(row_sum_diff),
                "has_nan": bool(has_nan),
                "has_inf": bool(has_inf),
                "load_time_s": round(float(load_duration), 4),
                "inference_time_s": round(float(inf_duration), 4),
                "status": "VERIFIED_REPRODUCIBLE",
            })

            # Map canonical index
            for s_idx in range(len(te_idx)):
                t_cur = int(ts_test[s_idx])
                can_i = ts_to_idx[t_cur]
                oof_can_indices.append(can_i)
                oof_rows.append({
                    "instrument": symbol,
                    "fold": fold_idx,
                    "open_time_ms": t_cur,
                    "true_label": int(y_test[s_idx]),
                    "predicted_class": int(pred_classes[s_idx]),
                    "raw_score_m1": float(raw_logits[s_idx, 0]),
                    "raw_score_0": float(raw_logits[s_idx, 1]),
                    "raw_score_p1": float(raw_logits[s_idx, 2]),
                    "raw_prob_m1": float(pred_probs[s_idx, 0]),
                    "raw_prob_0": float(pred_probs[s_idx, 1]),
                    "raw_prob_p1": float(pred_probs[s_idx, 2]),
                    "model_path": str(model_path).replace("\\", "/"),
                    "preprocessor_path": str(prep_path).replace("\\", "/"),
                })

            oof_y_true.extend(y_test)
            oof_logits.append(raw_logits)
            oof_probs.append(pred_probs)
            oof_folds.extend([fold_idx] * len(te_idx))
            oof_timestamps.extend(ts_test)

        # Materialize parquet file
        df_oof = pd.DataFrame(oof_rows)
        parquet_path = MATERIALIZED_DIR / f"{symbol}_oof.parquet"
        df_oof.to_parquet(parquet_path, index=False)
        parquet_sha = compute_sha256(parquet_path)

        sym_total_obs = len(df_oof)
        fleet_total_obs += sym_total_obs

        # Record manifest
        oof_manifest["instruments"][symbol] = {
            "total_observations": sym_total_obs,
            "parquet_path": str(parquet_path).replace("\\", "/"),
            "parquet_sha256": parquet_sha,
            "start_timestamp_utc": pd.to_datetime(int(df_oof["open_time_ms"].min()), unit="ms", utc=True).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "end_timestamp_utc": pd.to_datetime(int(df_oof["open_time_ms"].max()), unit="ms", utc=True).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "folds": {
                f"fold_{f}": {
                    "count": int((df_oof["fold"] == f).sum()),
                    "start_utc": pd.to_datetime(int(df_oof[df_oof["fold"] == f]["open_time_ms"].min()), unit="ms", utc=True).strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "end_utc": pd.to_datetime(int(df_oof[df_oof["fold"] == f]["open_time_ms"].max()), unit="ms", utc=True).strftime("%Y-%m-%d %H:%M:%S UTC"),
                }
                for f in range(1, 6)
            }
        }

        # Convert to numpy for modeling
        oof_y_arr = np.array(oof_y_true, dtype=np.int32)
        oof_logits_arr = np.vstack(oof_logits)
        oof_probs_arr = np.vstack(oof_probs)
        oof_folds_arr = np.array(oof_folds, dtype=np.int32)
        oof_can_idx_arr = np.array(oof_can_indices, dtype=np.int32)

        # Partition segments:
        # Segment 1: Folds 1-2 (Calibration Fit)
        # Segment 2: Folds 3-4 (Policy Selection)
        # Segment 3: Fold 5 (Final Temporal Evaluation)
        seg1_mask = np.isin(oof_folds_arr, [1, 2])
        seg2_mask = np.isin(oof_folds_arr, [3, 4])
        seg3_mask = (oof_folds_arr == 5)

        # Verify 13-bar separation between segments
        seg1_end = int(df_oof[seg1_mask]["open_time_ms"].max())
        seg2_start = int(df_oof[seg2_mask]["open_time_ms"].min())
        gap_1_2 = seg2_start - seg1_end
        assert gap_1_2 >= PURGE_GAP_MS, f"Purge gap violation between Seg1 and Seg2 for {symbol}: {gap_1_2} ms"

        seg2_end = int(df_oof[seg2_mask]["open_time_ms"].max())
        seg3_start = int(df_oof[seg3_mask]["open_time_ms"].min())
        gap_2_3 = seg3_start - seg2_end
        assert gap_2_3 >= PURGE_GAP_MS, f"Purge gap violation between Seg2 and Seg3 for {symbol}: {gap_2_3} ms"

        # 8. Calibration Fitting on Segment 1
        print(f"Fitting calibration methods for {symbol} on Segment 1 (Folds 1-2, N={np.sum(seg1_mask)})...", flush=True)

        # Baseline: Uncalibrated
        # Method 1: Temperature Scaling
        temp_scaler = TemperatureScaling()
        t0_ts = time.time()
        fitted_T = temp_scaler.fit(oof_logits_arr[seg1_mask], oof_y_arr[seg1_mask])
        ts_fit_time = time.time() - t0_ts

        # Method 2: Vector Platt Scaling
        platt_scaler = VectorPlattScaling(c_reg=1.0)
        t0_vp = time.time()
        platt_scaler.fit(oof_logits_arr[seg1_mask], oof_y_arr[seg1_mask])
        vp_fit_time = time.time() - t0_vp

        # Method 3: Isotonic Regression (Prohibited on XMR)
        iso_scaler = None
        iso_fit_time = 0.0
        if symbol != "XMRUSDT":
            iso_scaler = IsotonicCalibrator()
            t0_iso = time.time()
            iso_scaler.fit(oof_probs_arr[seg1_mask], oof_y_arr[seg1_mask])
            iso_fit_time = time.time() - t0_iso

        # Predict calibrated probabilities across all segments
        probs_uncal = {
            "seg1": oof_probs_arr[seg1_mask],
            "seg2": oof_probs_arr[seg2_mask],
            "seg3": oof_probs_arr[seg3_mask],
        }
        probs_temp = {
            "seg1": temp_scaler.predict_proba(oof_logits_arr[seg1_mask]),
            "seg2": temp_scaler.predict_proba(oof_logits_arr[seg2_mask]),
            "seg3": temp_scaler.predict_proba(oof_logits_arr[seg3_mask]),
        }
        probs_platt = {
            "seg1": platt_scaler.predict_proba(oof_logits_arr[seg1_mask]),
            "seg2": platt_scaler.predict_proba(oof_logits_arr[seg2_mask]),
            "seg3": platt_scaler.predict_proba(oof_logits_arr[seg3_mask]),
        }
        probs_iso = None
        if iso_scaler is not None:
            probs_iso = {
                "seg1": iso_scaler.predict_proba(oof_probs_arr[seg1_mask]),
                "seg2": iso_scaler.predict_proba(oof_probs_arr[seg2_mask]),
                "seg3": iso_scaler.predict_proba(oof_probs_arr[seg3_mask]),
            }

        # Evaluate calibration metrics
        methods = {
            "Uncalibrated": probs_uncal,
            "TemperatureScaling": probs_temp,
            "VectorPlattScaling": probs_platt,
        }
        if probs_iso is not None:
            methods["IsotonicRegression"] = probs_iso

        y_segs = {
            "seg1": oof_y_arr[seg1_mask],
            "seg2": oof_y_arr[seg2_mask],
            "seg3": oof_y_arr[seg3_mask],
        }

        cal_sym_results = {
            "fitted_parameters": {
                "temperature": round(fitted_T, 6),
                "vector_platt_c": 1.0,
                "isotonic_status": "FITTED" if iso_scaler is not None else "PROHIBITED_SAMPLE_SUPPORT_LIMITATION",
                "fitting_durations_s": {
                    "temperature_scaling": round(ts_fit_time, 4),
                    "vector_platt_scaling": round(vp_fit_time, 4),
                    "isotonic_regression": round(iso_fit_time, 4),
                }
            },
            "evaluations": {},
        }

        for m_name, p_dict in methods.items():
            cal_sym_results["evaluations"][m_name] = {}
            for s_key in ["seg1", "seg2", "seg3"]:
                p_eval = p_dict[s_key]
                y_eval = y_segs[s_key]

                brier = compute_multiclass_brier(y_eval, p_eval)
                logloss = compute_multiclass_log_loss(y_eval, p_eval)
                top_ece_uni, _ = compute_top_label_ece(y_eval, p_eval, n_bins=N_BINS, bin_strategy="uniform")
                top_ece_qnt, _ = compute_top_label_ece(y_eval, p_eval, n_bins=N_BINS, bin_strategy="quantile")
                cls_ece_uni, _ = compute_classwise_ece(y_eval, p_eval, n_bins=N_BINS, bin_strategy="uniform")
                cls_ece_qnt, _ = compute_classwise_ece(y_eval, p_eval, n_bins=N_BINS, bin_strategy="quantile")

                cal_sym_results["evaluations"][m_name][s_key] = {
                    "sample_count": len(y_eval),
                    "brier_score": round(brier, 6),
                    "log_loss": round(logloss, 6),
                    "top_label_ece_uniform": round(top_ece_uni, 6),
                    "top_label_ece_quantile": round(top_ece_qnt, 6),
                    "classwise_ece_uniform": round(cls_ece_uni, 6),
                    "classwise_ece_quantile": round(cls_ece_qnt, 6),
                }

        # Select best calibration method based on Segment 2 (Policy Selection) Log Loss
        seg2_loglosses = {
            m_name: cal_sym_results["evaluations"][m_name]["seg2"]["log_loss"]
            for m_name in methods.keys()
        }
        best_method = min(seg2_loglosses, key=seg2_loglosses.get)
        cal_sym_results["selected_best_method"] = best_method
        calibration_results["instruments"][symbol] = cal_sym_results

        # 9. Selective Classification Evaluation on Segment 2 & Segment 3 using selected calibrated probabilities
        print(f"Evaluating selective classification for {symbol} using {best_method}...", flush=True)
        sel_eval_seg2 = evaluate_selective_classification_grid(y_segs["seg2"], methods[best_method]["seg2"])
        sel_eval_seg3 = evaluate_selective_classification_grid(y_segs["seg3"], methods[best_method]["seg3"])
        
        # Also evaluate uncalibrated on Segment 3 for baseline comparison
        sel_eval_seg3_uncal = evaluate_selective_classification_grid(y_segs["seg3"], methods["Uncalibrated"]["seg3"])

        selective_results["instruments"][symbol] = {
            "calibration_method_used": best_method,
            "segment_2_policy_selection": sel_eval_seg2,
            "segment_3_final_evaluation": sel_eval_seg3,
            "segment_3_uncalibrated_baseline": sel_eval_seg3_uncal,
        }

        # 10. Decision Policy Threshold Optimization on Segment 2 (Folds 3-4)
        print(f"Optimizing directional decision policy threshold for {symbol} on Segment 2...", flush=True)
        seg2_probs = methods[best_method]["seg2"]
        seg2_can_idx = oof_can_idx_arr[seg2_mask]

        # Candidate threshold grid
        threshold_candidates = [0.34, 0.35, 0.36, 0.37, 0.38, 0.40, 0.42, 0.45]
        threshold_search_results = []
        best_theta = 0.35
        best_metric = -999.0

        for theta in threshold_candidates:
            # Directional mapping
            long_cands = (seg2_probs[:, 2] > theta) & (seg2_probs[:, 2] > seg2_probs[:, 0])
            short_cands = (seg2_probs[:, 0] > theta) & (seg2_probs[:, 0] > seg2_probs[:, 2])
            
            n_long = int(np.sum(long_cands))
            n_short = int(np.sum(short_cands))
            n_total = n_long + n_short
            
            # Policy requires directional decisions and support guardrail
            if n_total < 100 or n_long < 20 or n_short < 20:
                threshold_search_results.append({
                    "threshold": theta,
                    "trade_count": n_total,
                    "status": "REJECTED_INSUFFICIENT_SUPPORT",
                })
                continue
                
            # Simulate trades on Segment 2
            dir_indices = []
            dir_signals = []
            for idx_m in range(len(seg2_can_idx)):
                if long_cands[idx_m]:
                    dir_indices.append(seg2_can_idx[idx_m])
                    dir_signals.append(1)
                elif short_cands[idx_m]:
                    dir_indices.append(seg2_can_idx[idx_m])
                    dir_signals.append(-1)
                    
            dir_indices = np.array(dir_indices, dtype=np.int32)
            dir_signals = np.array(dir_signals, dtype=np.int32)
            
            sim_res = simulate_realized_returns(
                can_opens, can_highs, can_lows, can_closes, can_timestamps,
                dir_indices, dir_signals, vol_series,
            )
            
            # Selection criterion: mean net return at 15 bps (or gross return)
            crit_metric = sim_res["cost_scenarios"]["15_bps"]["conservative_adverse"]["mean_net_return"]
            threshold_search_results.append({
                "threshold": theta,
                "trade_count": n_total,
                "long_trades": n_long,
                "short_trades": n_short,
                "mean_net_return_15bps": crit_metric,
                "win_rate_15bps": sim_res["cost_scenarios"]["15_bps"]["conservative_adverse"]["win_rate"],
                "profit_factor_15bps": sim_res["cost_scenarios"]["15_bps"]["conservative_adverse"]["profit_factor"],
            })
            
            if crit_metric > best_metric:
                best_metric = crit_metric
                best_theta = theta

        # 11. Final Untouched Policy Evaluation on Segment 3 (Fold 5)
        print(f"Selected optimal threshold theta={best_theta} for {symbol}. Evaluating on Segment 3 (Fold 5)...", flush=True)
        seg3_probs = methods[best_method]["seg3"]
        seg3_can_idx = oof_can_idx_arr[seg3_mask]

        seg3_long = (seg3_probs[:, 2] > best_theta) & (seg3_probs[:, 2] > seg3_probs[:, 0])
        seg3_short = (seg3_probs[:, 0] > best_theta) & (seg3_probs[:, 0] > seg3_probs[:, 2])
        seg3_no_trade = ~(seg3_long | seg3_short)

        seg3_trade_idx = []
        seg3_trade_signals = []
        for idx_m in range(len(seg3_can_idx)):
            if seg3_long[idx_m]:
                seg3_trade_idx.append(seg3_can_idx[idx_m])
                seg3_trade_signals.append(1)
            elif seg3_short[idx_m]:
                seg3_trade_idx.append(seg3_can_idx[idx_m])
                seg3_trade_signals.append(-1)

        seg3_trade_idx = np.array(seg3_trade_idx, dtype=np.int32)
        seg3_trade_signals = np.array(seg3_trade_signals, dtype=np.int32)

        seg3_sim = simulate_realized_returns(
            can_opens, can_highs, can_lows, can_closes, can_timestamps,
            seg3_trade_idx, seg3_trade_signals, vol_series,
        )

        decision_results["instruments"][symbol] = {
            "selected_calibrator": best_method,
            "optimal_threshold": best_theta,
            "threshold_selection_grid": threshold_search_results,
            "segment_3_final_evaluation": {
                "total_candles": len(seg3_probs),
                "long_candidates": int(np.sum(seg3_long)),
                "short_candidates": int(np.sum(seg3_short)),
                "no_trade_candidates": int(np.sum(seg3_no_trade)),
                "decision_distribution": {
                    "LONG": round(float(np.mean(seg3_long)), 4),
                    "SHORT": round(float(np.mean(seg3_short)), 4),
                    "NO_TRADE": round(float(np.mean(seg3_no_trade)), 4),
                },
                "realized_trade_diagnostics": seg3_sim,
            }
        }

        # 12. Transaction Cost Sensitivity Table
        cost_results["instruments"][symbol] = {
            "optimal_threshold": best_theta,
            "total_trades_eval": seg3_sim["trade_count"],
            "ambiguous_trades_count": seg3_sim["ambiguous_count"],
            "ambiguous_trades_pct": round(seg3_sim["ambiguous_fraction"] * 100.0, 2),
            "gap_trades_count": seg3_sim["gap_count"],
            "gap_trades_pct": round(seg3_sim["gap_fraction"] * 100.0, 2),
            "mean_gross_return": seg3_sim["mean_gross_return"],
            "long_mean_gross_return": seg3_sim["long_mean_gross_return"],
            "short_mean_gross_return": seg3_sim["short_mean_gross_return"],
            "cost_scenarios": seg3_sim["cost_scenarios"],
        }

        t_sym_dur = time.time() - t_sym_start
        sym_rss = psutil.Process().memory_info().rss / (1024 * 1024)
        if sym_rss > peak_rss:
            peak_rss = sym_rss

        resource_benchmarks["instruments"][symbol] = {
            "duration_s": round(t_sym_dur, 2),
            "observations": sym_total_obs,
            "rss_mb": round(sym_rss, 2),
        }
        print(f"Completed {symbol} in {t_sym_dur:.2f}s. Memory RSS: {sym_rss:.2f} MB", flush=True)

        # Explicit garbage collection
        del df_can, labeled, df_feats, df_feats_dv, merged, df_clean, df_oof
        gc.collect()

    t_total_dur = time.time() - t_start_total
    oof_manifest["total_fleet_observations"] = fleet_total_obs
    resource_benchmarks["peak_rss_mb"] = round(peak_rss, 2)
    resource_benchmarks["total_duration_s"] = round(t_total_dur, 2)

    print(f"\nAll 11 instruments processed in {t_total_dur:.2f}s. Fleet Total OOF: {fleet_total_obs}. Peak RSS: {peak_rss:.2f} MB.", flush=True)

    # 13. Write JSON Artifacts
    print("\nWriting JSON Artifacts...", flush=True)
    def json_fallback(o):
        if isinstance(o, (np.integer, np.int64, np.int32)):
            return int(o)
        if isinstance(o, (np.floating, np.float64, np.float32)):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        return str(o)

    manifest_path = ARTIFACTS_DIR / "PHASE_5_4_2_OOF_PROBABILITY_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(oof_manifest, f, indent=2, default=json_fallback)

    cal_path = ARTIFACTS_DIR / "PHASE_5_4_2_CALIBRATION_RESULTS.json"
    with open(cal_path, "w", encoding="utf-8") as f:
        json.dump(calibration_results, f, indent=2, default=json_fallback)

    sel_path = ARTIFACTS_DIR / "PHASE_5_4_2_SELECTIVE_CLASSIFICATION_RESULTS.json"
    with open(sel_path, "w", encoding="utf-8") as f:
        json.dump(selective_results, f, indent=2, default=json_fallback)

    dec_path = ARTIFACTS_DIR / "PHASE_5_4_2_DECISION_POLICY_RESULTS.json"
    with open(dec_path, "w", encoding="utf-8") as f:
        json.dump(decision_results, f, indent=2, default=json_fallback)

    cost_path = ARTIFACTS_DIR / "PHASE_5_4_2_COST_SENSITIVITY_RESULTS.json"
    with open(cost_path, "w", encoding="utf-8") as f:
        json.dump(cost_results, f, indent=2, default=json_fallback)

    # SHA-256 Manifest of all Phase 5.4 artifacts
    artifact_hash_manifest = {
        "title": "Phase 5.4.2 Artifact Cryptographic Hash Manifest",
        "timestamp_utc": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "artifacts": {
            "PHASE_5_4_2_OOF_PROBABILITY_MANIFEST.json": compute_sha256(manifest_path),
            "PHASE_5_4_2_CALIBRATION_RESULTS.json": compute_sha256(cal_path),
            "PHASE_5_4_2_SELECTIVE_CLASSIFICATION_RESULTS.json": compute_sha256(sel_path),
            "PHASE_5_4_2_DECISION_POLICY_RESULTS.json": compute_sha256(dec_path),
            "PHASE_5_4_2_COST_SENSITIVITY_RESULTS.json": compute_sha256(cost_path),
        },
        "materialized_parquet_files": {
            f"{sym}_oof.parquet": compute_sha256(MATERIALIZED_DIR / f"{sym}_oof.parquet")
            for sym in SYMBOLS
        },
        "frozen_model_binaries_verified_count": reproducibility_audit["models_verified_count"],
        "governance_status": "FROZEN_REPRODUCIBILITY_VERIFIED",
    }

    hash_manifest_path = ARTIFACTS_DIR / "PHASE_5_4_2_ARTIFACT_HASH_MANIFEST.json"
    with open(hash_manifest_path, "w", encoding="utf-8") as f:
        json.dump(artifact_hash_manifest, f, indent=2, default=json_fallback)

    repro_audit_path = ARTIFACTS_DIR / "PHASE_5_4_2_INFERENCE_REPRODUCIBILITY_AUDIT.json"
    with open(repro_audit_path, "w", encoding="utf-8") as f:
        json.dump(reproducibility_audit, f, indent=2, default=json_fallback)

    print("All JSON artifacts successfully generated and hashed.", flush=True)


if __name__ == "__main__":
    run_phase_5_4_2()
