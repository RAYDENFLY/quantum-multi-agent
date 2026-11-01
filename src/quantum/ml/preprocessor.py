"""Causal Specialist Preprocessor with Strict Fit Boundaries.

Ensures that feature scalers and normalizers are fitted exclusively
on designated training folds and never on validation or holdout data.
"""

from typing import List, Optional
import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler, StandardScaler


class SpecialistPreprocessor:
    """Specialist feature preprocessor with strict causal fitting boundaries."""

    def __init__(
        self,
        scaler_type: str = "robust",
        quantile_range: tuple = (5.0, 95.0),
        clip_range: tuple = (-5.0, 5.0),
    ) -> None:
        """Initialize specialist preprocessor.

        Parameters
        ----------
        scaler_type : str
            Type of scaler ('robust' or 'standard').
        quantile_range : tuple
            Quantile range for RobustScaler (default: 5th to 95th percentile).
        clip_range : tuple
            Bounds to clip scaled values to prevent extreme numerical outliers.
        """
        if scaler_type not in ("robust", "standard"):
            raise ValueError(f"Unsupported scaler_type: {scaler_type}")

        self.scaler_type = scaler_type
        self.quantile_range = quantile_range
        self.clip_range = clip_range

        self._scaler = (
            RobustScaler(quantile_range=quantile_range)
            if scaler_type == "robust"
            else StandardScaler()
        )
        self.feature_names_in_: Optional[List[str]] = None
        self.is_fitted: bool = False

    def fit(self, X: pd.DataFrame) -> "SpecialistPreprocessor":
        """Fit preprocessor parameters strictly on training fold features.

        Parameters
        ----------
        X : pd.DataFrame
            Training feature matrix.

        Returns
        -------
        SpecialistPreprocessor
            Fitted preprocessor instance.
        """
        if X.empty:
            raise ValueError("Cannot fit preprocessor on empty DataFrame")

        # Validate no NaNs or Infs in training data
        nan_count = int(X.isna().sum().sum())
        if nan_count > 0:
            raise ValueError(f"Training features contain {nan_count} unexpected NaNs")

        inf_count = int(np.isinf(X.to_numpy(dtype=float)).sum())
        if inf_count > 0:
            raise ValueError(f"Training features contain {inf_count} unexpected infinite values")

        self.feature_names_in_ = list(X.columns)
        self._scaler.fit(X.to_numpy(dtype=float))
        self.is_fitted = True
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """Apply fitted scaling transformation to a feature matrix.

        Parameters
        ----------
        X : pd.DataFrame
            Feature matrix to scale.

        Returns
        -------
        np.ndarray
            Scaled and outlier-clipped feature array.
        """
        if not self.is_fitted:
            raise RuntimeError("Preprocessor must be fitted on training data before calling transform")

        if list(X.columns) != self.feature_names_in_:
            raise ValueError(
                f"Feature mismatch: expected {self.feature_names_in_}, received {list(X.columns)}"
            )

        arr = X.to_numpy(dtype=float)
        scaled = self._scaler.transform(arr)

        if self.clip_range is not None:
            scaled = np.clip(scaled, self.clip_range[0], self.clip_range[1])

        return scaled

    def fit_transform(self, X: pd.DataFrame) -> np.ndarray:
        """Fit on training fold and return transformed array."""
        return self.fit(X).transform(X)
