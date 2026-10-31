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

            # Check for grouping columns (e.g. symbol, exchange)
            by_cols = [col for col in ["symbol", "exchange"] if col in merged.columns and col in htf_df.columns]

            req_cols = ["close_time_ms"] + by_cols + [c for c in cols_to_use if c in htf_df.columns and c not in by_cols]
            htf_subset = htf_df[req_cols].copy()

            # Handle unsorted and duplicate HTF timestamps deterministically
            dup_keys = by_cols + ["close_time_ms"] if by_cols else ["close_time_ms"]
            htf_subset.drop_duplicates(subset=dup_keys, keep="last", inplace=True)

            rename_map = {c: f"{prefix}{c}" for c in cols_to_use if c in htf_df.columns and c not in by_cols}
            htf_join_key = f"_htf_join_close_{tf_str}"
            rename_map["close_time_ms"] = htf_join_key
            htf_subset.rename(columns=rename_map, inplace=True)

            # Pandas merge_asof requires the 'on' column to be monotonically increasing
            htf_subset.sort_values(by=htf_join_key, inplace=True)
            merged.sort_values(by="open_time_ms", inplace=True)

            # Causal As-Of Join:
            # Matches each base row's open_time_ms to the latest HTF close_time_ms <= open_time_ms
            merged = pd.merge_asof(
                merged,
                htf_subset,
                left_on="open_time_ms",
                right_on=htf_join_key,
                by=by_cols if by_cols else None,
                direction="backward",
            )

            # Drop temporary right join key
            if htf_join_key in merged.columns:
                merged.drop(columns=[htf_join_key], inplace=True)

        return merged
