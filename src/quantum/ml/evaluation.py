"""Model evaluation contracts, predictive metrics, and economic simulation contracts.

Defines:
1. Multi-class predictive evaluation metrics (Accuracy, Balanced Acc, Macro F1, Brier, ROC/PR-AUC).
2. Economic simulation metrics contracts for downstream strategy evaluation.
3. Separation contract guaranteeing that statistical predictive metrics are never conflated with trading profitability.
"""

from typing import Any, Dict, List, Optional
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    roc_auc_score,
)


class ModelEvaluationContract:
    """Computes comprehensive multi-class predictive metrics on out-of-fold validation predictions."""

    @staticmethod
    def evaluate_predictions(
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_proba: Optional[np.ndarray] = None,
        classes: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """Compute all required classification performance metrics.

        Parameters
        ----------
        y_true : np.ndarray
            Ground truth target classes (-1, 0, 1).
        y_pred : np.ndarray
            Predicted target classes (-1, 0, 1).
        y_proba : np.ndarray, optional
            Predicted class probabilities (shape: [N, num_classes]).
        classes : list of int, optional
            Explicit class list (default: [-1, 0, 1]).

        Returns
        -------
        Dict[str, Any]
            Dictionary of predictive performance metrics.
        """
        if classes is None:
            classes = [-1, 0, 1]

        acc = float(accuracy_score(y_true, y_pred))
        bal_acc = float(balanced_accuracy_score(y_true, y_pred))
        macro_f1 = float(f1_score(y_true, y_pred, average="macro", zero_division=0))

        prec, rec, f1, support = precision_recall_fscore_support(
            y_true, y_pred, labels=classes, zero_division=0
        )

        class_names = {1: "TP", -1: "SL", 0: "EXP"}
        per_class = {}
        for idx, cls in enumerate(classes):
            c_name = class_names.get(cls, str(cls))
            per_class[c_name] = {
                "precision": round(float(prec[idx]), 4),
                "recall": round(float(rec[idx]), 4),
                "f1": round(float(f1[idx]), 4),
                "support": int(support[idx]),
            }

        cm = confusion_matrix(y_true, y_pred, labels=classes).tolist()

        metrics = {
            "accuracy": round(acc, 4),
            "balanced_accuracy": round(bal_acc, 4),
            "macro_f1": round(macro_f1, 4),
            "per_class": per_class,
            "confusion_matrix": cm,
            "classes": classes,
        }

        # Multi-class probability metrics if probabilities provided
        if y_proba is not None:
            # Multi-class Brier score: mean squared difference from one-hot ground truth
            one_hot = np.zeros_like(y_proba)
            for idx, cls in enumerate(classes):
                one_hot[y_true == cls, idx] = 1.0
            brier = float(np.mean(np.sum((y_proba - one_hot) ** 2, axis=1)))
            metrics["brier_score"] = round(brier, 4)

            # One-vs-Rest ROC-AUC if all classes present
            try:
                roc_auc = float(
                    roc_auc_score(
                        y_true,
                        y_proba,
                        multi_class="ovr",
                        labels=classes,
                    )
                )
                metrics["roc_auc_ovr"] = round(roc_auc, 4)
            except Exception:
                metrics["roc_auc_ovr"] = None

        return metrics


class EconomicSimulationContract:
    """Formal specification contract for economic trading metrics in subsequent phases.

    Note: Predictive classification metrics do NOT establish trading profitability.
    Trading performance must be evaluated through realistic financial execution simulation.
    """

    FEE_RATES_BPS: Dict[str, float] = {
        "taker_fee_bps": 5.0,     # 0.05%
        "maker_fee_bps": 2.0,     # 0.02%
        "default_slippage_bps": 2.0,
    }

    REQUIRED_ECONOMIC_METRICS: List[str] = [
        "net_pnl_usdt",
        "net_return_pct",
        "maximum_drawdown_pct",
        "profit_factor",
        "expectancy_bps",
        "turnover_usdt",
        "trade_frequency_per_day",
        "funding_cost_usdt",
        "slippage_impact_bps",
    ]
