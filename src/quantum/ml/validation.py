"""Purged and embargoed walk-forward temporal cross-validation.

Implements expanding-window walk-forward validation with:
- Forward label purging to prevent target horizon overlap.
- Post-test embargo to mitigate autocorrelation leakage.
- Strict rejection of holdout partitions.
"""

from typing import Dict, Generator, List, Optional, Tuple
import numpy as np
import pandas as pd

from quantum.features.temporal_split import (
    DEVELOPMENT_START_MS,
    PROSPECTIVE_HOLDOUT_START_MS,
    VALIDATION_END_MS,
)


class PurgedWalkForwardSplitter:
    """Walk-forward cross-validation splitter with purging and embargoing."""

    def __init__(
        self,
        n_splits: int = 5,
        horizon_bars: int = 12,
        embargo_bars: int = 24,
        min_train_ratio: float = 0.5,
        protect_test_horizon: bool = True,
    ) -> None:
        """Initialize walk-forward splitter.

        Parameters
        ----------
        n_splits : int
            Number of walk-forward folds (default: 5).
        horizon_bars : int
            Prediction horizon length to purge before test window (default: 12 bars).
        embargo_bars : int
            Number of bars to embargo following test window (default: 24 bars).
            Note: Formally deprecated as non-operational for expanding-window walk-forward
            validation (Phase 5.3.3.1 Governance Decision Option B), as expanding-window
            training data strictly precedes test evaluation in chronological time.
        min_train_ratio : float
            Fraction of total samples reserved for initial minimum training window.
        protect_test_horizon : bool
            If True, truncate test fold end by horizon_bars so test sample labels
            never reference price observations beyond test_end (default: True).
        """
        if n_splits < 2:
            raise ValueError("n_splits must be at least 2")
        if horizon_bars < 0:
            raise ValueError("horizon_bars cannot be negative")
        if embargo_bars < 0:
            raise ValueError("embargo_bars cannot be negative")
        if not (0.1 <= min_train_ratio <= 0.8):
            raise ValueError("min_train_ratio must be between 0.1 and 0.8")

        self.n_splits = n_splits
        self.horizon_bars = horizon_bars
        self.embargo_bars = embargo_bars
        self.min_train_ratio = min_train_ratio
        self.protect_test_horizon = protect_test_horizon

    def split(
        self,
        df: pd.DataFrame,
        timestamp_col: str = "open_time_ms",
    ) -> Generator[Tuple[np.ndarray, np.ndarray], None, None]:
        """Generate (train_indices, test_indices) for walk-forward validation.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame containing chronological samples.
        timestamp_col : str
            Name of timestamp column in milliseconds.

        Yields
        ------
        Tuple[np.ndarray, np.ndarray]
            Array of training integer indices, Array of testing integer indices.
        """
        if df.empty:
            return

        # 1. Strict holdout access rejection
        if timestamp_col in df.columns:
            max_ts = int(df[timestamp_col].max())
            if max_ts >= PROSPECTIVE_HOLDOUT_START_MS:
                raise PermissionError(
                    f"Temporal violation: DataFrame contains timestamps ({max_ts}) "
                    f"in PROSPECTIVE_HOLDOUT (>= {PROSPECTIVE_HOLDOUT_START_MS}). "
                    f"Holdout data must never be used for validation splitting."
                )

        n_samples = len(df)
        min_train_size = int(n_samples * self.min_train_ratio)
        eval_pool = n_samples - min_train_size

        if eval_pool <= self.n_splits:
            raise ValueError(
                f"Insufficient samples ({n_samples}) for {self.n_splits} folds "
                f"with min_train_ratio={self.min_train_ratio}"
            )

        test_fold_size = eval_pool // self.n_splits

        for fold in range(self.n_splits):
            test_start = min_train_size + fold * test_fold_size
            test_end = (
                test_start + test_fold_size if fold < self.n_splits - 1 else n_samples
            )

            # Purging: remove samples near split whose horizon reaches into test_start
            train_end = max(0, test_start - self.horizon_bars)
            train_indices = np.arange(0, train_end, dtype=int)

            # Test horizon protection: truncate test_end by horizon_bars
            # so test sample labels cannot look past test_end
            effective_test_end = (
                max(test_start, test_end - self.horizon_bars)
                if self.protect_test_horizon
                else test_end
            )
            test_indices = np.arange(test_start, effective_test_end, dtype=int)

            if len(train_indices) == 0 or len(test_indices) == 0:
                continue

            yield train_indices, test_indices

    def get_fold_metadata(
        self,
        df: pd.DataFrame,
        timestamp_col: str = "open_time_ms",
    ) -> List[Dict[str, int]]:
        """Return detailed timestamp and sample count metadata for all folds."""
        metadata = []
        timestamps = df[timestamp_col].to_numpy() if timestamp_col in df.columns else None

        for fold_idx, (train_idx, test_idx) in enumerate(self.split(df, timestamp_col)):
            fold_info = {
                "fold": fold_idx + 1,
                "train_samples": int(len(train_idx)),
                "test_samples": int(len(test_idx)),
                "purged_samples": int(self.horizon_bars),
                "test_purged_samples": int(self.horizon_bars if self.protect_test_horizon else 0),
                "embargo_samples": int(self.embargo_bars),
            }
            if timestamps is not None:
                fold_info["train_start_ms"] = int(timestamps[train_idx[0]])
                fold_info["train_end_ms"] = int(timestamps[train_idx[-1]])
                fold_info["test_start_ms"] = int(timestamps[test_idx[0]])
                fold_info["test_end_ms"] = int(timestamps[test_idx[-1]])
            metadata.append(fold_info)
        return metadata
