"""Specialist baseline model specifications for Phase 5.3.

Specifies five standardized baseline model architectures:
1. Majority Class Baseline (heuristic lower bound)
2. Prior Class Probability Baseline (empirical frequency benchmark)
3. Regularized Logistic Regression (linear statistical baseline)
4. Balanced Random Forest (non-linear ensemble baseline)
5. LightGBM Gradient Boosting (gradient boosted decision tree baseline)

Pure architecture specifications and parameter contracts.
Zero model training is performed during Phase 5.3.0.
"""

from typing import Any, Dict, Optional
import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import lightgbm as lgb


class MajorityClassBaseline(BaseEstimator, ClassifierMixin):
    """Majority class heuristic baseline.

    Always predicts the most frequent class observed during training.
    """

    def __init__(self) -> None:
        self.majority_class_: Optional[int] = None
        self.classes_: Optional[np.ndarray] = None

    def fit(self, X: Any, y: np.ndarray) -> "MajorityClassBaseline":
        """Fit by recording majority class from training labels."""
        y_arr = np.asarray(y)
        classes, counts = np.unique(y_arr, return_counts=True)
        self.classes_ = classes
        self.majority_class_ = int(classes[np.argmax(counts)])
        return self

    def predict(self, X: Any) -> np.ndarray:
        """Predict majority class for all samples."""
        if self.majority_class_ is None:
            raise RuntimeError("Estimator not fitted")
        n = len(X)
        return np.full(n, self.majority_class_, dtype=int)

    def predict_proba(self, X: Any) -> np.ndarray:
        """Predict one-hot probability for majority class."""
        if self.classes_ is None:
            raise RuntimeError("Estimator not fitted")
        n = len(X)
        probs = np.zeros((n, len(self.classes_)), dtype=float)
        maj_idx = np.where(self.classes_ == self.majority_class_)[0][0]
        probs[:, maj_idx] = 1.0
        return probs


class PriorProbabilityBaseline(BaseEstimator, ClassifierMixin):
    """Prior class probability frequency baseline.

    Predicts constant class prior probabilities equal to training proportions.
    """

    def __init__(self) -> None:
        self.classes_: Optional[np.ndarray] = None
        self.priors_: Optional[np.ndarray] = None

    def fit(self, X: Any, y: np.ndarray) -> "PriorProbabilityBaseline":
        """Fit by recording empirical class priors from training labels."""
        y_arr = np.asarray(y)
        classes, counts = np.unique(y_arr, return_counts=True)
        self.classes_ = classes
        self.priors_ = counts / len(y_arr)
        return self

    def predict(self, X: Any) -> np.ndarray:
        """Predict highest-prior class for all samples."""
        if self.classes_ is None or self.priors_ is None:
            raise RuntimeError("Estimator not fitted")
        n = len(X)
        maj_class = self.classes_[np.argmax(self.priors_)]
        return np.full(n, maj_class, dtype=int)

    def predict_proba(self, X: Any) -> np.ndarray:
        """Predict constant prior distribution for all samples."""
        if self.priors_ is None:
            raise RuntimeError("Estimator not fitted")
        n = len(X)
        return np.tile(self.priors_, (n, 1))


class BaselineModelFactory:
    """Factory creating configured baseline classifier instances."""

    @staticmethod
    def create_majority_class() -> MajorityClassBaseline:
        """Instantiate MajorityClassBaseline classifier."""
        return MajorityClassBaseline()

    @staticmethod
    def create_prior_probability() -> PriorProbabilityBaseline:
        """Instantiate PriorProbabilityBaseline classifier."""
        return PriorProbabilityBaseline()

    @staticmethod
    def get_logistic_regression_spec(
        c_penalty: float = 1.0,
        random_seed: int = 42,
    ) -> Dict[str, Any]:
        """Specification for L2-regularized multinomial logistic regression."""
        return {
            "model_type": "LogisticRegression",
            "hyperparameters": {
                "C": c_penalty,
                "penalty": "l2",
                "solver": "lbfgs",
                "max_iter": 500,
                "class_weight": "balanced",
                "random_state": random_seed,
            },
            "memory_budget_mb": 150.0,
            "cpu_threads": 2,
        }

    @staticmethod
    def create_logistic_regression(
        c_penalty: float = 1.0,
        random_seed: int = 42,
    ) -> LogisticRegression:
        """Instantiate configured LogisticRegression classifier."""
        return LogisticRegression(
            C=c_penalty,
            penalty="l2",
            solver="lbfgs",
            max_iter=500,
            class_weight="balanced",
            random_state=random_seed,
        )

    @staticmethod
    def get_random_forest_spec(
        n_estimators: int = 100,
        max_depth: int = 8,
        min_samples_leaf: int = 50,
        random_seed: int = 42,
    ) -> Dict[str, Any]:
        """Specification for Balanced Random Forest classifier."""
        return {
            "model_type": "RandomForestClassifier",
            "hyperparameters": {
                "n_estimators": n_estimators,
                "max_depth": max_depth,
                "min_samples_leaf": min_samples_leaf,
                "class_weight": "balanced",
                "max_features": "sqrt",
                "n_jobs": 2,
                "random_state": random_seed,
            },
            "memory_budget_mb": 400.0,
            "cpu_threads": 2,
        }

    @staticmethod
    def create_random_forest(
        n_estimators: int = 100,
        max_depth: int = 8,
        min_samples_leaf: int = 50,
        random_seed: int = 42,
    ) -> RandomForestClassifier:
        """Instantiate configured RandomForestClassifier."""
        return RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_leaf=min_samples_leaf,
            class_weight="balanced",
            max_features="sqrt",
            n_jobs=2,
            random_state=random_seed,
        )

    @staticmethod
    def get_lightgbm_spec(
        n_estimators: int = 100,
        learning_rate: float = 0.05,
        num_leaves: int = 31,
        random_seed: int = 42,
    ) -> Dict[str, Any]:
        """Specification for LightGBM GBDT classifier."""
        return {
            "model_type": "LGBMClassifier",
            "hyperparameters": {
                "n_estimators": n_estimators,
                "learning_rate": learning_rate,
                "num_leaves": num_leaves,
                "class_weight": "balanced",
                "subsample": 0.8,
                "colsample_bytree": 0.8,
                "n_jobs": 2,
                "random_state": random_seed,
                "verbosity": -1,
            },
            "memory_budget_mb": 250.0,
            "cpu_threads": 2,
        }

    @staticmethod
    def create_lightgbm(
        n_estimators: int = 100,
        learning_rate: float = 0.05,
        num_leaves: int = 31,
        random_seed: int = 42,
    ) -> lgb.LGBMClassifier:
        """Instantiate configured LGBMClassifier."""
        return lgb.LGBMClassifier(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            num_leaves=num_leaves,
            class_weight="balanced",
            subsample=0.8,
            colsample_bytree=0.8,
            n_jobs=2,
            random_state=random_seed,
            verbosity=-1,
        )
