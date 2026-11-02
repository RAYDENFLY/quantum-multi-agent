"""Track 1 Predictive Evaluation Pipeline for Frozen Phase 5.3 Models.

Evaluates the original frozen target specification without altering labels, models, or estimands:
- Target: Triple-barrier categorical label in {-1 (SL), 0 (EXP), +1 (TP)}
- Horizon: 12 bars (60 minutes on 5m timeframe)
- Anchor: close[i]
- Barriers: Symmetric +/- 1.5 * sigma_t

Implements the 5 mandatory predictive evaluation metrics:
1. Balanced Accuracy
2. Multiclass Brier Score (unnormalized sum over K=3, range [0, 2])
3. ROC-AUC One-vs-Rest (macro-averaged across classes)
4. Expected Calibration Error (ECE: 15-bin uniform top-label, quantile top-label, and classwise)
5. AURCC (Area Under the Risk-Coverage Curve: full-span and [0.2, 1.0] span)
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple
import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    roc_auc_score,
)

from quantum.backtesting.adapters import OOFSignal


CANONICAL_CLASSES: Tuple[int, int, int] = (-1, 0, 1)


class Track1MetricBundle(BaseModel):
    """Complete predictive metric output for a single fold or pooled sample."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    sample_count: int = Field(ge=0)
    classes: List[int] = Field(default_factory=lambda: [-1, 0, 1])
    present_classes: List[int] = Field(default_factory=list)
    accuracy: Optional[float] = None
    balanced_accuracy: Optional[float] = None
    macro_f1: Optional[float] = None
    multiclass_brier_score: Optional[float] = None
    multiclass_log_loss: Optional[float] = None
    roc_auc_ovr: Optional[float] = None
    roc_auc_ovr_present_classes: Optional[float] = None
    ece_top_uniform: Optional[float] = None
    ece_top_quantile: Optional[float] = None
    ece_classwise_uniform: Optional[float] = None
    aurcc_error_full: Optional[float] = None
    aurcc_error_span_02_10: Optional[float] = None
    aurcc_error_random: Optional[float] = None
    delta_aurcc_error_span_02_10: Optional[float] = None
    per_class: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    confusion_matrix: List[List[int]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class Track1EvaluationReport(BaseModel):
    """Fold-separated Track 1 predictive evaluation report."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    symbol: str
    target_specification: str = "FROZEN_PHASE_5_3_TRIPLE_BARRIER_12BAR_CLOSE_ANCHOR_1_5_SIGMA"
    universe_tier: str = "PRIMARY_RESEARCH_UNIVERSE"
    verified_oof_pooled: Optional[Track1MetricBundle] = None
    fold_5_unverified_oos: Optional[Track1MetricBundle] = None
    per_fold_metrics: Dict[int, Track1MetricBundle] = Field(default_factory=dict)
    fold_5_governance_status: str = "OOS_ELIGIBILITY_NOT_VERIFIED"


def compute_top_label_ece_uniform(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    confidences: np.ndarray,
    n_bins: int = 15,
) -> float:
    """Compute top-label Expected Calibration Error using M equal-width bins over [0, 1]."""
    n = len(y_true)
    if n == 0:
        return 0.0

    correct = (y_true == y_pred).astype(float)
    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0

    for m in range(n_bins):
        low, high = bin_boundaries[m], bin_boundaries[m + 1]
        if m == 0:
            in_bin = (confidences >= low) & (confidences <= high)
        else:
            in_bin = (confidences > low) & (confidences <= high)

        count = int(np.sum(in_bin))
        if count > 0:
            acc_bin = float(np.mean(correct[in_bin]))
            conf_bin = float(np.mean(confidences[in_bin]))
            ece += (count / n) * abs(acc_bin - conf_bin)

    return float(ece)


def compute_top_label_ece_quantile(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    confidences: np.ndarray,
    n_bins: int = 15,
) -> float:
    """Compute top-label Expected Calibration Error using M equal-frequency (quantile) bins."""
    n = len(y_true)
    if n == 0:
        return 0.0

    correct = (y_true == y_pred).astype(float)
    order = np.argsort(confidences, kind="mergesort")
    sorted_correct = correct[order]
    sorted_conf = confidences[order]

    actual_bins = min(n_bins, n)
    splits = np.array_split(np.arange(n), actual_bins)
    ece = 0.0

    for idxs in splits:
        count = len(idxs)
        if count > 0:
            acc_bin = float(np.mean(sorted_correct[idxs]))
            conf_bin = float(np.mean(sorted_conf[idxs]))
            ece += (count / n) * abs(acc_bin - conf_bin)

    return float(ece)


def compute_classwise_ece_uniform(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    classes: Sequence[int] = CANONICAL_CLASSES,
    n_bins: int = 15,
) -> float:
    """Compute classwise Expected Calibration Error averaged across K classes."""
    n = len(y_true)
    k_count = len(classes)
    if n == 0 or k_count == 0:
        return 0.0

    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    total_cw_ece = 0.0

    for idx, cls in enumerate(classes):
        y_k = (y_true == cls).astype(float)
        p_k = y_proba[:, idx]
        class_ece = 0.0

        for m in range(n_bins):
            low, high = bin_boundaries[m], bin_boundaries[m + 1]
            if m == 0:
                in_bin = (p_k >= low) & (p_k <= high)
            else:
                in_bin = (p_k > low) & (p_k <= high)

            count = int(np.sum(in_bin))
            if count > 0:
                freq_bin = float(np.mean(y_k[in_bin]))
                conf_bin = float(np.mean(p_k[in_bin]))
                class_ece += (count / n) * abs(freq_bin - conf_bin)

        total_cw_ece += class_ece

    return float(total_cw_ece / k_count)


def compute_aurcc_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    confidences: np.ndarray,
    coverage_min: float = 0.2,
    coverage_max: float = 1.0,
    grid_points: int = 81,
) -> Tuple[float, float, float, float]:
    """Compute Area Under the Risk-Coverage Curve (AURCC) for classification error risk.

    Returns
    -------
    tuple of (aurcc_full, aurcc_span, aurcc_random, delta_aurcc_span)
        - aurcc_full: Exact prefix-sum mean risk across all coverage steps k/N in (0, 1].
        - aurcc_span: Trapezoidal integral over [coverage_min, coverage_max] normalized by span width.
        - aurcc_random: Expected risk under random abstention (equal to full-sample error rate).
        - delta_aurcc_span: aurcc_span - aurcc_random (negative means confidence ranking reduces error).
    """
    n = len(y_true)
    if n == 0:
        return 0.0, 0.0, 0.0, 0.0

    errors = (y_true != y_pred).astype(float)
    # Sort descending by confidence; mergesort preserves deterministic index order on ties
    order = np.argsort(-confidences, kind="mergesort")
    sorted_errors = errors[order]

    cum_errors = np.cumsum(sorted_errors)
    counts = np.arange(1, n + 1, dtype=float)
    prefix_risks = cum_errors / counts

    aurcc_full = float(np.mean(prefix_risks))
    aurcc_random = float(np.mean(errors))

    # Evaluate on coverage grid [coverage_min, coverage_max]
    kappas = np.linspace(coverage_min, coverage_max, grid_points)
    k_indices = np.clip(np.ceil(kappas * n).astype(int) - 1, 0, n - 1)
    grid_risks = prefix_risks[k_indices]

    span_width = coverage_max - coverage_min
    aurcc_span = float(np.trapezoid(grid_risks, kappas) / span_width) if span_width > 0 else aurcc_full
    delta_aurcc = aurcc_span - aurcc_random

    return aurcc_full, aurcc_span, aurcc_random, delta_aurcc


class Track1PredictiveEvaluator:
    """Standalone evaluator for Track 1 predictive benchmark on frozen Phase 5.3 predictions."""

    def __init__(
        self,
        classes: Sequence[int] = CANONICAL_CLASSES,
        normalize_probabilities: bool = False,
        simplex_tolerance: float = 1e-4,
        ece_bins: int = 15,
    ) -> None:
        self.classes = list(classes)
        self.normalize_probabilities = normalize_probabilities
        self.simplex_tolerance = simplex_tolerance
        self.ece_bins = ece_bins

    def validate_and_prepare_inputs(
        self,
        y_true: Sequence[int] | np.ndarray,
        y_pred: Sequence[int] | np.ndarray,
        y_proba: Sequence[Sequence[float]] | np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Validate class labels, sample alignment, and probability simplex."""
        yt = np.asarray(y_true, dtype=int)
        yp = np.asarray(y_pred, dtype=int)
        prob = np.asarray(y_proba, dtype=float)

        if yt.ndim != 1 or yp.ndim != 1:
            raise ValueError("y_true and y_pred must be 1D arrays")
        if len(yt) != len(yp):
            raise ValueError(f"Length mismatch: len(y_true)={len(yt)} != len(y_pred)={len(yp)}")
        if len(yt) == 0:
            raise ValueError("Cannot evaluate empty prediction arrays (sample_count == 0)")

        if prob.ndim != 2 or prob.shape[0] != len(yt) or prob.shape[1] != len(self.classes):
            raise ValueError(
                f"y_proba must have shape ({len(yt)}, {len(self.classes)}), got {prob.shape}"
            )

        valid_set = set(self.classes)
        invalid_true = set(np.unique(yt).tolist()) - valid_set
        if invalid_true:
            raise ValueError(f"y_true contains invalid class labels: {invalid_true}")

        invalid_pred = set(np.unique(yp).tolist()) - valid_set
        if invalid_pred:
            raise ValueError(f"y_pred contains invalid class labels: {invalid_pred}")

        if not np.all(np.isfinite(prob)):
            raise ValueError("y_proba contains NaN or infinite values")

        if np.any(prob < -1e-7):
            raise ValueError("y_proba contains negative probabilities")

        if not self.normalize_probabilities and np.any(prob > 1.0 + 1e-7):
            raise ValueError("y_proba contains probabilities > 1.0 while normalize_probabilities=False")

        prob = np.maximum(prob, 0.0)
        row_sums = np.sum(prob, axis=1)

        if self.normalize_probabilities:
            if np.any(row_sums <= 0.0):
                raise ValueError("Cannot normalize probability row with sum <= 0.0")
            prob = prob / row_sums[:, np.newaxis]
        else:
            max_err = float(np.max(np.abs(row_sums - 1.0)))
            if max_err > self.simplex_tolerance:
                raise ValueError(
                    f"Probability simplex violated: max |sum(p) - 1.0| = {max_err:.6e} > {self.simplex_tolerance}"
                )

        return yt, yp, prob

    def evaluate_arrays(
        self,
        y_true: Sequence[int] | np.ndarray,
        y_pred: Sequence[int] | np.ndarray,
        y_proba: Sequence[Sequence[float]] | np.ndarray,
    ) -> Track1MetricBundle:
        """Compute all 5 mandatory Track 1 predictive metrics on validated arrays."""
        yt, yp, prob = self.validate_and_inputs(y_true, y_pred, y_proba) if hasattr(self, "validate_and_inputs") else self.validate_and_prepare_inputs(y_true, y_pred, y_proba)
        n = len(yt)
        warnings_list: List[str] = []

        present_classes = sorted(int(c) for c in np.unique(yt))
        if len(present_classes) < len(self.classes):
            missing = [c for c in self.classes if c not in present_classes]
            warnings_list.append(f"MISSING_GROUND_TRUTH_CLASSES: {missing}")
        if n < 15:
            warnings_list.append(f"SMALL_SAMPLE_SIZE: N={n} < 15")

        # 1. Accuracy & Balanced Accuracy (computed without sklearn warning when classes missing in y_true)
        acc = float(accuracy_score(yt, yp))
        recalls_present: List[float] = []
        for cls in present_classes:
            mask = yt == cls
            recalls_present.append(float(np.mean(yp[mask] == cls)))
        bal_acc = float(np.mean(recalls_present)) if recalls_present else 0.0

        macro_f1 = float(f1_score(yt, yp, labels=self.classes, average="macro", zero_division=0))

        prec, rec, f1, support = precision_recall_fscore_support(
            yt, yp, labels=self.classes, zero_division=0
        )
        class_names = {-1: "SL", 0: "EXP", 1: "TP"}
        per_class: Dict[str, Dict[str, Any]] = {}
        for idx, cls in enumerate(self.classes):
            c_name = class_names.get(cls, str(cls))
            per_class[c_name] = {
                "class_id": cls,
                "precision": round(float(prec[idx]), 6),
                "recall": round(float(rec[idx]), 6),
                "f1": round(float(f1[idx]), 6),
                "support": int(support[idx]),
            }

        cm = confusion_matrix(yt, yp, labels=self.classes).tolist()

        # 2. Multiclass Brier Score & Log Loss
        one_hot = np.zeros_like(prob)
        for idx, cls in enumerate(self.classes):
            one_hot[yt == cls, idx] = 1.0
        brier = float(np.mean(np.sum((prob - one_hot) ** 2, axis=1)))

        eps = 1e-15
        prob_clipped = np.clip(prob, eps, 1.0 - eps)
        log_loss_val = float(-np.mean(np.sum(one_hot * np.log(prob_clipped), axis=1)))

        # 3. ROC-AUC One-vs-Rest
        roc_auc_full: Optional[float] = None
        roc_auc_present: Optional[float] = None

        per_class_aucs: List[float] = []
        for idx, cls in enumerate(self.classes):
            y_bin = (yt == cls).astype(int)
            n_pos = int(np.sum(y_bin == 1))
            n_neg = int(np.sum(y_bin == 0))
            if n_pos > 0 and n_neg > 0:
                per_class_aucs.append(float(roc_auc_score(y_bin, prob[:, idx])))

        if len(per_class_aucs) == len(self.classes):
            roc_auc_full = round(float(np.mean(per_class_aucs)), 6)
            roc_auc_present = roc_auc_full
        elif len(per_class_aucs) > 0:
            roc_auc_present = round(float(np.mean(per_class_aucs)), 6)
            warnings_list.append(
                f"ROC_AUC_OVR_UNDEFINED_FOR_ALL_CLASSES: computed over {len(per_class_aucs)}/{len(self.classes)} binary tasks"
            )
        else:
            warnings_list.append("ROC_AUC_OVR_UNDEFINED: only a single class present in y_true")

        # 4. Expected Calibration Error (ECE)
        confidences = np.max(prob, axis=1)
        argmax_classes = np.array([self.classes[i] for i in np.argmax(prob, axis=1)], dtype=int)

        ece_top_uni = compute_top_label_ece_uniform(yt, argmax_classes, confidences, n_bins=self.ece_bins)
        ece_top_quant = compute_top_label_ece_quantile(yt, argmax_classes, confidences, n_bins=self.ece_bins)
        ece_cw_uni = compute_classwise_ece_uniform(yt, prob, classes=self.classes, n_bins=self.ece_bins)

        # 5. AURCC
        aurcc_full, aurcc_span, aurcc_rand, delta_aurcc = compute_aurcc_metrics(
            yt, argmax_classes, confidences
        )

        return Track1MetricBundle(
            sample_count=n,
            classes=self.classes,
            present_classes=present_classes,
            accuracy=round(acc, 6),
            balanced_accuracy=round(bal_acc, 6),
            macro_f1=round(macro_f1, 6),
            multiclass_brier_score=round(brier, 6),
            multiclass_log_loss=round(log_loss_val, 6),
            roc_auc_ovr=roc_auc_full,
            roc_auc_ovr_present_classes=roc_auc_present,
            ece_top_uniform=round(ece_top_uni, 6),
            ece_top_quantile=round(ece_top_quant, 6),
            ece_classwise_uniform=round(ece_cw_uni, 6),
            aurcc_error_full=round(aurcc_full, 6),
            aurcc_error_span_02_10=round(aurcc_span, 6),
            aurcc_error_random=round(aurcc_rand, 6),
            delta_aurcc_error_span_02_10=round(delta_aurcc, 6),
            per_class=per_class,
            confusion_matrix=cm,
            warnings=warnings_list,
        )

    def evaluate_signals(
        self,
        symbol: str,
        signals: Sequence[OOFSignal],
        universe_tier: str = "PRIMARY_RESEARCH_UNIVERSE",
    ) -> Track1EvaluationReport:
        """Evaluate a list of OOFSignal objects with strict fold separation (Folds 1-4 vs Fold 5)."""
        if not signals:
            raise ValueError("Cannot evaluate empty signal list")

        for s in signals:
            if s.symbol != symbol:
                raise ValueError(f"Cross-asset signal detected: expected {symbol}, got {s.symbol}")

        by_fold: Dict[int, List[OOFSignal]] = {}
        verified_signals: List[OOFSignal] = []
        fold_5_signals: List[OOFSignal] = []

        for s in signals:
            by_fold.setdefault(s.fold, []).append(s)
            if s.fold == 5 or s.oos_eligibility == "OOS_ELIGIBILITY_NOT_VERIFIED":
                fold_5_signals.append(s)
            else:
                verified_signals.append(s)

        def _bundle_from_signals(sig_list: List[OOFSignal]) -> Track1MetricBundle:
            yt = np.array([s.true_label for s in sig_list], dtype=int)
            yp = np.array([s.predicted_class for s in sig_list], dtype=int)
            prob = np.array([[s.prob_sl, s.prob_exp, s.prob_tp] for s in sig_list], dtype=float)
            return self.evaluate_arrays(yt, yp, prob)

        per_fold: Dict[int, Track1MetricBundle] = {}
        for f_num in sorted(by_fold.keys()):
            per_fold[f_num] = _bundle_from_signals(by_fold[f_num])

        verified_bundle = _bundle_from_signals(verified_signals) if verified_signals else None
        fold_5_bundle = _bundle_from_signals(fold_5_signals) if fold_5_signals else None

        return Track1EvaluationReport(
            symbol=symbol,
            universe_tier=universe_tier,
            verified_oof_pooled=verified_bundle,
            fold_5_unverified_oos=fold_5_bundle,
            per_fold_metrics=per_fold,
        )

    def evaluate_oof_dataframe(
        self,
        symbol: str,
        df: pd.DataFrame,
        universe_tier: str = "PRIMARY_RESEARCH_UNIVERSE",
    ) -> Track1EvaluationReport:
        """Evaluate an OOF DataFrame directly with fold separation."""
        if df.empty:
            raise ValueError("Cannot evaluate empty OOF DataFrame")

        req = ["instrument", "fold", "true_label", "predicted_class", "raw_prob_m1", "raw_prob_0", "raw_prob_p1"]
        for c in req:
            if c not in df.columns:
                raise ValueError(f"OOF DataFrame missing column: {c}")

        if (df["instrument"] != symbol).any():
            raise ValueError(f"Cross-asset mismatch in DataFrame for symbol {symbol}")

        def _bundle_from_df(sub_df: pd.DataFrame) -> Track1MetricBundle:
            yt = sub_df["true_label"].to_numpy(dtype=int)
            yp = sub_df["predicted_class"].to_numpy(dtype=int)
            prob = sub_df[["raw_prob_m1", "raw_prob_0", "raw_prob_p1"]].to_numpy(dtype=float)
            return self.evaluate_arrays(yt, yp, prob)

        per_fold: Dict[int, Track1MetricBundle] = {}
        for f_num in sorted(int(f) for f in df["fold"].unique()):
            sub = df[df["fold"] == f_num]
            per_fold[f_num] = _bundle_from_df(sub)

        df_verified = df[df["fold"].isin([1, 2, 3, 4])]
        df_fold5 = df[df["fold"] == 5]

        verified_bundle = _bundle_from_df(df_verified) if not df_verified.empty else None
        fold5_bundle = _bundle_from_df(df_fold5) if not df_fold5.empty else None

        return Track1EvaluationReport(
            symbol=symbol,
            universe_tier=universe_tier,
            verified_oof_pooled=verified_bundle,
            fold_5_unverified_oos=fold5_bundle,
            per_fold_metrics=per_fold,
        )
