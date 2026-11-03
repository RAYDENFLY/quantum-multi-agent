"""Strict Dataset Partitioner with Holdout Protection & Cryptographic Fingerprinting."""

import hashlib
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from quantum.research.models import DatasetFingerprint, DatasetPartitionType

# Sealed prospective holdout boundary: strictly 2026-11-01 00:00:00 UTC
PROSPECTIVE_HOLDOUT_START_MS: int = 1_793_491_200_000


class HoldoutContaminationError(ValueError):
    """Raised when an optimization, training, or retrospective evaluation attempts to access holdout data."""
    pass


class PartitionLeakageError(ValueError):
    """Raised when dataset partitions violate chronological isolation or overlap across embargo buffers."""
    pass


class DatasetPartition:
    """Encapsulates a strictly bounded dataset slice with cryptographic provenance."""

    def __init__(
        self,
        df: pd.DataFrame,
        partition_type: DatasetPartitionType,
        symbol: str,
        timeframe: str = "5m",
    ) -> None:
        self.df = df
        self.partition_type = partition_type
        self.symbol = symbol
        self.timeframe = timeframe
        self.fingerprint = self._compute_fingerprint()

    def _compute_fingerprint(self) -> DatasetFingerprint:
        if self.df.empty:
            return DatasetFingerprint(
                partition_type=self.partition_type,
                symbol=self.symbol,
                timeframe=self.timeframe,
                start_timestamp_ms=0,
                end_timestamp_ms=0,
                row_count=0,
                sha256_hash=hashlib.sha256(b"EMPTY").hexdigest(),
            )

        start_ts = int(self.df["open_time_ms"].iloc[0])
        end_ts = int(self.df["close_time_ms"].iloc[-1])
        row_count = len(self.df)

        core_cols = ["open_time_ms", "close_time_ms", "open", "high", "low", "close", "volume"]
        present_cols = [c for c in core_cols if c in self.df.columns]
        raw_bytes = self.df[present_cols].to_numpy().tobytes()
        sha256 = hashlib.sha256(raw_bytes).hexdigest()

        return DatasetFingerprint(
            partition_type=self.partition_type,
            symbol=self.symbol,
            timeframe=self.timeframe,
            start_timestamp_ms=start_ts,
            end_timestamp_ms=end_ts,
            row_count=row_count,
            sha256_hash=sha256,
        )


class ContinuousResearchPartitioner:
    """Manages chronological dataset partitioning, embargo buffers, and holdout enforcement."""

    def __init__(
        self,
        embargo_bars: int = 288,  # 24 hours of 5m bars
        train_ratio: float = 0.50,
        val_ratio: float = 0.25,
        rolling_oos_ratio: float = 0.25,
        holdout_boundary_ms: int = PROSPECTIVE_HOLDOUT_START_MS,
    ) -> None:
        if not np.isclose(train_ratio + val_ratio + rolling_oos_ratio, 1.0):
            raise ValueError("Split ratios must sum exactly to 1.0.")
        self.embargo_bars = embargo_bars
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.rolling_oos_ratio = rolling_oos_ratio
        self.holdout_boundary_ms = holdout_boundary_ms

    def partition_pre_holdout_series(
        self,
        df_raw: pd.DataFrame,
        symbol: str,
        timeframe: str = "5m",
    ) -> Dict[DatasetPartitionType, DatasetPartition]:
        """Partitions continuous historical pre-holdout series into TRAIN, VALIDATION, and ROLLING_OOS."""
        if df_raw.empty:
            raise ValueError(f"Cannot partition empty DataFrame for symbol {symbol}.")

        df = df_raw.sort_values("open_time_ms").reset_index(drop=True)

        # 1. Enforce Sealed Holdout Isolation
        max_ts = int(df["close_time_ms"].max())
        if max_ts >= self.holdout_boundary_ms:
            raise HoldoutContaminationError(
                f"CRITICAL HOLDOUT CONTAMINATION: Data contains timestamp {max_ts} >= "
                f"sealed prospective holdout boundary {self.holdout_boundary_ms}. "
                f"Holdout data must NEVER be passed to retrospective research partitioning."
            )

        n = len(df)
        total_embargo = 2 * self.embargo_bars
        if n <= total_embargo + 300:
            raise ValueError(f"Insufficient observations ({n} bars) to partition with {total_embargo} embargo bars.")

        available_bars = n - total_embargo
        n_train = int(available_bars * self.train_ratio)
        n_val = int(available_bars * self.val_ratio)

        # Slice 1: TRAIN
        train_end = n_train
        df_train = df.iloc[:train_end].copy().reset_index(drop=True)

        # Slice 2: VALIDATION (separated by embargo buffer)
        val_start = train_end + self.embargo_bars
        val_end = val_start + n_val
        df_val = df.iloc[val_start:val_end].copy().reset_index(drop=True)

        # Slice 3: ROLLING_OOS (separated by second embargo buffer)
        oos_start = val_end + self.embargo_bars
        df_oos = df.iloc[oos_start:].copy().reset_index(drop=True)

        # 2. Strict Chronological Invariant Verification
        train_last_ts = int(df_train["close_time_ms"].iloc[-1])
        val_first_ts = int(df_val["open_time_ms"].iloc[0])
        val_last_ts = int(df_val["close_time_ms"].iloc[-1])
        oos_first_ts = int(df_oos["open_time_ms"].iloc[0])

        if train_last_ts >= val_first_ts:
            raise PartitionLeakageError(
                f"Training data leak: train_last_ts ({train_last_ts}) >= val_first_ts ({val_first_ts})"
            )
        if val_last_ts >= oos_first_ts:
            raise PartitionLeakageError(
                f"Validation data leak: val_last_ts ({val_last_ts}) >= oos_first_ts ({oos_first_ts})"
            )

        return {
            DatasetPartitionType.TRAIN: DatasetPartition(df_train, DatasetPartitionType.TRAIN, symbol, timeframe),
            DatasetPartitionType.VALIDATION: DatasetPartition(df_val, DatasetPartitionType.VALIDATION, symbol, timeframe),
            DatasetPartitionType.ROLLING_OOS: DatasetPartition(df_oos, DatasetPartitionType.ROLLING_OOS, symbol, timeframe),
        }

    def generate_rolling_oos_folds(
        self,
        partition_oos: DatasetPartition,
        n_folds: int = 4,
    ) -> List[DatasetPartition]:
        """Generates continuous non-overlapping walk-forward chronological evaluation folds."""
        df_oos = partition_oos.df
        n = len(df_oos)
        fold_size = n // n_folds
        folds: List[DatasetPartition] = []

        for i in range(n_folds):
            start_idx = i * fold_size
            end_idx = (i + 1) * fold_size if i < n_folds - 1 else n
            df_fold = df_oos.iloc[start_idx:end_idx].copy().reset_index(drop=True)
            folds.append(
                DatasetPartition(
                    df_fold,
                    DatasetPartitionType.ROLLING_OOS,
                    partition_oos.symbol,
                    partition_oos.timeframe,
                )
            )

        return folds
