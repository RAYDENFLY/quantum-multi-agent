"""Temporal Partition Management and Boundary Enforcement.

Provides authoritative UTC boundaries, strict partition slicing,
and boundary violation guards to prevent data leakage between
Development, Validation, and Final Holdout partitions.
"""

from enum import Enum
from typing import Dict, Optional, Tuple
import pandas as pd


class TemporalPartition(str, Enum):
    """Authoritative dataset partition names for Phase 5."""
    DEVELOPMENT = "DEVELOPMENT"
    VALIDATION = "VALIDATION"
    FINAL_HOLDOUT = "FINAL_HOLDOUT"  # Historical Phase 5.0-5.2 designation
    VALIDATION_OBSERVED = "VALIDATION_OBSERVED"  # Reclassified Phase 5.2.1 designation (May-Oct 2026)
    PROSPECTIVE_HOLDOUT = "PROSPECTIVE_HOLDOUT"  # New prospective holdout (Nov 2026 - Apr 2027)


# Authoritative UTC millisecond timestamps
# Pre-Development: Prior to 2023-11-01 00:00:00.000 UTC
PRE_DEVELOPMENT_END_MS: int = 1698796799999

# Development: 2023-11-01 00:00:00.000 UTC through 2025-10-31 23:59:59.999 UTC
DEVELOPMENT_START_MS: int = 1698796800000
DEVELOPMENT_END_MS: int = 1761955199999

# Validation: 2025-11-01 00:00:00.000 UTC through 2026-04-30 23:59:59.999 UTC
VALIDATION_START_MS: int = 1761955200000
VALIDATION_END_MS: int = 1777593599999

# Historical Final Holdout (Now Reclassified to VALIDATION_OBSERVED)
# 2026-05-01 00:00:00.000 UTC through 2026-10-31 23:59:59.999 UTC
FINAL_HOLDOUT_START_MS: int = 1777593600000
FINAL_HOLDOUT_END_MS: int = 1793491199999
VALIDATION_OBSERVED_START_MS: int = 1777593600000
VALIDATION_OBSERVED_END_MS: int = 1793491199999

# Prospective Untouched Holdout (Phase 5.2.1 Governance)
# 2026-11-01 00:00:00.000 UTC through 2027-04-30 23:59:59.999 UTC (6 months / 181 days)
PROSPECTIVE_HOLDOUT_START_MS: int = 1793491200000
PROSPECTIVE_HOLDOUT_END_MS: int = 1809129599999

PARTITION_BOUNDARIES: Dict[TemporalPartition, Tuple[int, int]] = {
    TemporalPartition.DEVELOPMENT: (DEVELOPMENT_START_MS, DEVELOPMENT_END_MS),
    TemporalPartition.VALIDATION: (VALIDATION_START_MS, VALIDATION_END_MS),
    TemporalPartition.FINAL_HOLDOUT: (FINAL_HOLDOUT_START_MS, FINAL_HOLDOUT_END_MS),
    TemporalPartition.VALIDATION_OBSERVED: (VALIDATION_OBSERVED_START_MS, VALIDATION_OBSERVED_END_MS),
    TemporalPartition.PROSPECTIVE_HOLDOUT: (PROSPECTIVE_HOLDOUT_START_MS, PROSPECTIVE_HOLDOUT_END_MS),
}


class TemporalPartitionManager:
    """Manages temporal dataset partitioning and enforces isolation boundaries."""

    @staticmethod
    def get_partition(open_time_ms: int) -> Optional[TemporalPartition]:
        """Return the partition name for a given timestamp, or None if out of bounds."""
        for part, (start_ms, end_ms) in PARTITION_BOUNDARIES.items():
            if start_ms <= open_time_ms <= end_ms:
                return part
        return None

    @staticmethod
    def filter_partition(
        df: pd.DataFrame,
        partition: TemporalPartition,
        timestamp_col: str = "open_time_ms",
        allow_holdout: bool = False,
    ) -> pd.DataFrame:
        """Filter a DataFrame to a specific partition with strict holdout access controls.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame containing a millisecond timestamp column.
        partition : TemporalPartition
            Target partition to extract.
        timestamp_col : str
            Name of the millisecond timestamp column.
        allow_holdout : bool
            Must be explicitly set to True to access FINAL_HOLDOUT.
            Otherwise, access is blocked with PermissionError.

        Returns
        -------
        pd.DataFrame
            Filtered slice of the DataFrame.
        """
        if partition == TemporalPartition.FINAL_HOLDOUT and not allow_holdout:
            raise PermissionError(
                "Access to FINAL_HOLDOUT is strictly prohibited during research and development."
            )

        if df.empty or timestamp_col not in df.columns:
            return pd.DataFrame(columns=df.columns)

        start_ms, end_ms = PARTITION_BOUNDARIES[partition]
        mask = (df[timestamp_col] >= start_ms) & (df[timestamp_col] <= end_ms)
        return df[mask].copy().reset_index(drop=True)

    @staticmethod
    def split_dataset(
        df: pd.DataFrame,
        timestamp_col: str = "open_time_ms",
        include_holdout: bool = False,
    ) -> Dict[TemporalPartition, pd.DataFrame]:
        """Split a dataset into its temporal partitions.

        Parameters
        ----------
        df : pd.DataFrame
            Input DataFrame.
        timestamp_col : str
            Timestamp column name.
        include_holdout : bool
            Whether to include FINAL_HOLDOUT. Defaults to False.

        Returns
        -------
        Dict[TemporalPartition, pd.DataFrame]
            Dictionary of partition DataFrames.
        """
        result = {
            TemporalPartition.DEVELOPMENT: TemporalPartitionManager.filter_partition(
                df, TemporalPartition.DEVELOPMENT, timestamp_col=timestamp_col
            ),
            TemporalPartition.VALIDATION: TemporalPartitionManager.filter_partition(
                df, TemporalPartition.VALIDATION, timestamp_col=timestamp_col
            ),
        }
        if include_holdout:
            result[TemporalPartition.FINAL_HOLDOUT] = TemporalPartitionManager.filter_partition(
                df,
                TemporalPartition.FINAL_HOLDOUT,
                timestamp_col=timestamp_col,
                allow_holdout=True,
            )
        return result

    @staticmethod
    def is_within_horizon_boundary(
        open_time_ms: int,
        horizon_ms: int,
        partition: TemporalPartition,
    ) -> bool:
        """Check whether a forward evaluation horizon stays strictly inside the partition.

        Parameters
        ----------
        open_time_ms : int
            Candle open timestamp in milliseconds.
        horizon_ms : int
            Forward horizon duration in milliseconds.
        partition : TemporalPartition
            The partition the candle belongs to.

        Returns
        -------
        bool
            True if (open_time_ms + horizon_ms) <= partition_end_ms, False if horizon crosses boundary.
        """
        _, end_ms = PARTITION_BOUNDARIES[partition]
        return (open_time_ms + horizon_ms) <= end_ms

    @staticmethod
    def assert_no_temporal_leakage(
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        holdout_df: Optional[pd.DataFrame] = None,
        timestamp_col: str = "open_time_ms",
    ) -> None:
        """Assert strict temporal ordering and non-overlapping partitions."""
        if train_df.empty or val_df.empty:
            return

        train_max = int(train_df[timestamp_col].max())
        val_min = int(val_df[timestamp_col].min())
        if train_max >= val_min:
            raise ValueError(
                f"Temporal leakage detected: max train timestamp ({train_max}) "
                f">= min val timestamp ({val_min})"
            )

        if holdout_df is not None and not holdout_df.empty:
            val_max = int(val_df[timestamp_col].max())
            holdout_min = int(holdout_df[timestamp_col].min())
            if val_max >= holdout_min:
                raise ValueError(
                    f"Temporal leakage detected: max val timestamp ({val_max}) "
                    f">= min holdout timestamp ({holdout_min})"
                )

    @staticmethod
    def filter_development_and_validation(
        df: pd.DataFrame,
        timestamp_col: str = "open_time_ms",
    ) -> pd.DataFrame:
        """Filter a dataset strictly to Development and Validation (excluding holdouts).

        Restricts samples strictly to 1698796800000 <= open_time_ms <= 1777593599999.
        Excludes Pre-Development (< 2023-11-01) and all historical/prospective holdouts.
        """
        if df.empty or timestamp_col not in df.columns:
            return pd.DataFrame(columns=df.columns)
        mask = (df[timestamp_col] >= DEVELOPMENT_START_MS) & (df[timestamp_col] <= VALIDATION_END_MS)
        return df[mask].copy().reset_index(drop=True)

    @staticmethod
    def is_original_holdout_compromised() -> bool:
        """Return True indicating Phase 5.2.1 classification of original holdout."""
        return True

