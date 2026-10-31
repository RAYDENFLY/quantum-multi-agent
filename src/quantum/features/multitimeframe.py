"""Causal multi-timeframe feature joiner with mathematical zero-lookahead guarantee."""

from typing import Dict, List, Optional
import pandas as pd

from quantum.core.logging import get_logger
from quantum.domain.enums import Timeframe

logger = get_logger("features.multitimeframe")


class MultiTimeframeJoiner:
    """Joins higher-timeframe features into lower-timeframe records using backward as-of alignment.
    
    Causal Invariant:
    A lower-timeframe bar opening at T_base can ONLY observe higher-timeframe bars that have
    already fully closed on or before T_base (i.e. HTF.close_time_ms <= LTF.open_time_ms).
    Any higher-timeframe bar still forming at or after T_base is strictly inaccessible.
    """

    def join_htf_features(
        self,
        base_df: pd.DataFrame,
        htf_feature_dfs: Dict[Timeframe, pd.DataFrame],
        selected_columns: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """Perform causal backward as-of join of multiple higher-timeframe feature tables into base_df."""
        if base_df.empty:
            return base_df

        if "open_time_ms" not in base_df.columns:
            raise ValueError("base_df must contain 'open_time_ms' column")

        # Sort base DataFrame
        merged = base_df.sort_values(by="open_time_ms").copy()

        for htf, htf_df in htf_feature_dfs.items():
            if htf_df.empty:
                logger.warning("Empty feature DataFrame provided for HTF %s. Skipping join.", htf.value)
                continue

            if "close_time_ms" not in htf_df.columns:
                raise ValueError(f"HTF DataFrame for {htf.value} must contain 'close_time_ms' column")

            # Determine columns to copy
            cols_to_use = selected_columns or [
                c for c in htf_df.columns if c not in ("open_time_ms", "close_time_ms")
            ]

            # Subset and rename with prefix
            tf_str = htf.value if hasattr(htf, "value") else str(htf)
            prefix = f"htf_{tf_str}_"

            htf_subset = htf_df[["close_time_ms"] + [c for c in cols_to_use if c in htf_df.columns]].copy()
            htf_subset.sort_values(by="close_time_ms", inplace=True)

            rename_map = {c: f"{prefix}{c}" for c in cols_to_use if c in htf_df.columns}
            htf_subset.rename(columns=rename_map, inplace=True)

            # Causal As-Of Join:
            # Matches each base row's open_time_ms to the latest HTF close_time_ms <= open_time_ms
            merged = pd.merge_asof(
                merged,
                htf_subset,
                left_on="open_time_ms",
                right_on="close_time_ms",
                direction="backward",
                suffixes=("", f"_{tf_str}_right"),
            )

            # Drop temporary right join key if present
            if f"close_time_ms_{tf_str}_right" in merged.columns:
                merged.drop(columns=[f"close_time_ms_{tf_str}_right"], inplace=True)

        return merged
