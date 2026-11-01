"""Deterministic Triple-Barrier Label Generation for Phase 5.2.

Implements causal, reproducible triple-barrier labeling on OHLCV candle datasets.
Features:
- Primary timeframe: 5m (horizon: 12 candles = 60 minutes).
- Volatility lookback: 20 candles (evaluated strictly causally).
- Multipliers: candidate 1.5, sensitivity testing 1.0, 1.5, 2.0.
- Conservative ambiguity policy for intrabar double-touches.
- Strict partition boundary horizon isolation to prevent cross-partition leakage.
- Zero future data leakage.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from quantum.features.temporal_split import (
    PARTITION_BOUNDARIES,
    TemporalPartition,
    TemporalPartitionManager,
)


class BarrierOutcome(int, Enum):
    """Categorical label outcomes for triple-barrier method."""
    TP = 1
    SL = -1
    TIME_EXPIRATION = 0
    AMBIGUOUS = -2
    EXCLUDED = -999


class TripleBarrierLabelGenerator:
    """Generates causal triple-barrier target labels for quantitative research."""

    def __init__(
        self,
        horizon_bars: int = 12,
        volatility_lookback: int = 20,
        barrier_multiplier: float = 1.5,
        timeframe_ms: int = 300_000,
        min_volatility: float = 1e-6,
    ) -> None:
        """Initialize label generator parameters.

        Parameters
        ----------
        horizon_bars : int
            Number of forward candles in the prediction horizon (default: 12 bars).
        volatility_lookback : int
            Number of prior candles used to compute return volatility (default: 20 bars).
        barrier_multiplier : float
            Multiplier applied to return volatility for upper/lower barriers (default: 1.5).
        timeframe_ms : int
            Candle duration in milliseconds (default: 300,000 ms for 5m).
        min_volatility : float
            Lower bound for volatility to avoid zero-width barriers.
        """
        if horizon_bars <= 0:
            raise ValueError("horizon_bars must be positive")
        if volatility_lookback <= 1:
            raise ValueError("volatility_lookback must be at least 2")
        if barrier_multiplier <= 0:
            raise ValueError("barrier_multiplier must be positive")

        self.horizon_bars = horizon_bars
        self.volatility_lookback = volatility_lookback
        self.barrier_multiplier = barrier_multiplier
        self.timeframe_ms = timeframe_ms
        self.min_volatility = min_volatility

    def compute_causal_volatility(self, close_series: pd.Series) -> pd.Series:
        """Compute rolling return volatility using only past observations.

        Defined as the sample standard deviation (ddof=1) of simple returns
        over the lookback window of length `volatility_lookback`.

        Parameters
        ----------
        close_series : pd.Series
            Series of close prices.

        Returns
        -------
        pd.Series
            Rolling return volatility aligned causally with close_series.
        """
        returns = close_series.pct_change()
        vol = returns.rolling(
            window=self.volatility_lookback,
            min_periods=self.volatility_lookback,
        ).std(ddof=1)
        return vol.clip(lower=self.min_volatility)

    def generate_labels(
        self,
        df: pd.DataFrame,
        enforce_partition_boundaries: bool = True,
        timestamp_col: str = "open_time_ms",
    ) -> pd.DataFrame:
        """Generate deterministic triple-barrier labels for each candle in df.

        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame sorted ascending by timestamp. Must contain:
            open_time_ms, open, high, low, close.
        enforce_partition_boundaries : bool
            If True, samples whose horizon crosses partition boundaries
            (Development -> Validation or Validation -> Final Holdout)
            are marked as EXCLUDED to prevent leakage.
        timestamp_col : str
            Column name containing millisecond timestamp.

        Returns
        -------
        pd.DataFrame
            DataFrame with original columns plus:
            - label: int (-1, 0, 1, -2 for AMBIGUOUS, -999 for EXCLUDED)
            - label_name: str ("TP", "SL", "TIME_EXPIRATION", "AMBIGUOUS", "EXCLUDED")
            - touch_step: int (1 to horizon_bars, or 0 if excluded)
            - volatility: float (rolling return volatility sigma_t)
            - upper_barrier: float
            - lower_barrier: float
            - exclusion_reason: str or None
        """
        if df.empty:
            return pd.DataFrame()

        # Validate required columns
        req_cols = [timestamp_col, "open", "high", "low", "close"]
        for c in req_cols:
            if c not in df.columns:
                raise ValueError(f"Missing required column: {c}")

        df = df.copy().reset_index(drop=True)
        n = len(df)

        timestamps = df[timestamp_col].to_numpy()
        opens = df["open"].to_numpy(dtype=float)
        highs = df["high"].to_numpy(dtype=float)
        lows = df["low"].to_numpy(dtype=float)
        closes = df["close"].to_numpy(dtype=float)

        vol_series = self.compute_causal_volatility(df["close"]).to_numpy(dtype=float)

        # Output arrays
        labels = np.full(n, BarrierOutcome.EXCLUDED.value, dtype=int)
        label_names = ["EXCLUDED"] * n
        touch_steps = np.zeros(n, dtype=int)
        upper_barriers = np.full(n, np.nan, dtype=float)
        lower_barriers = np.full(n, np.nan, dtype=float)
        exclusion_reasons: List[Optional[str]] = [None] * n

        # Precompute partition info if requested
        partitions = [
            TemporalPartitionManager.get_partition(int(ts)) if enforce_partition_boundaries else None
            for ts in timestamps
        ]

        horizon_duration_ms = self.horizon_bars * self.timeframe_ms

        for i in range(n):
            # 1. Warm-up check
            if i < self.volatility_lookback or np.isnan(vol_series[i]):
                exclusion_reasons[i] = "WARMUP_INSUFFICIENT_LOOKBACK"
                continue

            current_ts = int(timestamps[i])
            c_entry = closes[i]
            sigma_t = vol_series[i]

            u_barrier = c_entry * (1.0 + self.barrier_multiplier * sigma_t)
            l_barrier = c_entry * (1.0 - self.barrier_multiplier * sigma_t)
            upper_barriers[i] = u_barrier
            lower_barriers[i] = l_barrier

            # 2. End-of-dataset check
            if i + self.horizon_bars >= n:
                exclusion_reasons[i] = "INSUFFICIENT_FUTURE_HORIZON"
                continue

            # 3. Partition boundary check
            if enforce_partition_boundaries:
                part = partitions[i]
                if part is not None:
                    _, part_end_ms = PARTITION_BOUNDARIES[part]
                    future_max_ts = current_ts + horizon_duration_ms
                    if future_max_ts > part_end_ms:
                        exclusion_reasons[i] = "PARTITION_BOUNDARY_OVERFLOW"
                        continue

            # 4. Check future horizon candles for timestamp continuity
            has_gap = False
            for k in range(1, self.horizon_bars + 1):
                expected_ts = current_ts + k * self.timeframe_ms
                actual_ts = int(timestamps[i + k])
                if actual_ts != expected_ts:
                    has_gap = True
                    break

            if has_gap:
                exclusion_reasons[i] = "MISSING_FUTURE_CANDLE_GAP"
                continue

            # 5. First-touch evaluation across future candles
            resolved = False
            for k in range(1, self.horizon_bars + 1):
                idx = i + k
                bar_h = highs[idx]
                bar_l = lows[idx]

                upper_touch = bar_h >= u_barrier
                lower_touch = bar_l <= l_barrier

                if upper_touch and lower_touch:
                    # Ambiguous: Both barriers touched in the same 5m candle
                    labels[i] = BarrierOutcome.AMBIGUOUS.value
                    label_names[i] = "AMBIGUOUS"
                    touch_steps[i] = k
                    exclusion_reasons[i] = "AMBIGUOUS_INTRABAR_DOUBLE_TOUCH"
                    resolved = True
                    break
                elif upper_touch:
                    labels[i] = BarrierOutcome.TP.value
                    label_names[i] = "TP"
                    touch_steps[i] = k
                    resolved = True
                    break
                elif lower_touch:
                    labels[i] = BarrierOutcome.SL.value
                    label_names[i] = "SL"
                    touch_steps[i] = k
                    resolved = True
                    break

            # 6. Expiration check if neither barrier was touched
            if not resolved:
                labels[i] = BarrierOutcome.TIME_EXPIRATION.value
                label_names[i] = "TIME_EXPIRATION"
                touch_steps[i] = self.horizon_bars

        out_df = df.copy()
        out_df["label"] = labels
        out_df["label_name"] = label_names
        out_df["touch_step"] = touch_steps
        out_df["volatility"] = vol_series
        out_df["upper_barrier"] = upper_barriers
        out_df["lower_barrier"] = lower_barriers
        out_df["exclusion_reason"] = exclusion_reasons

        return out_df
