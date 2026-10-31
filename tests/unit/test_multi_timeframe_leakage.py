"""Deterministic tests verifying zero lookahead leakage in multi-timeframe feature joins."""

import numpy as np
import pandas as pd
import pytest

from quantum.domain.enums import Timeframe
from quantum.features.multitimeframe import MultiTimeframeJoiner


def test_mtf_causal_backward_alignment_basic() -> None:
    """Verify that lower timeframe candles only observe fully closed higher timeframe candles."""
    joiner = MultiTimeframeJoiner()

    # Base: 5m candles from 10:00 to 11:30 (18 bars)
    # open_time_ms: 10:00, 10:05, ..., 11:25
    base_times = [10_000_000 + (i * 300_000) for i in range(18)]
    base_df = pd.DataFrame({
        "open_time_ms": base_times,
        "close_time_ms": [t + 300_000 - 1 for t in base_times],
        "base_rsi": np.linspace(40.0, 60.0, 18),
    })

    # HTF: 1h candles
    # Candle A: 09:00 to 10:00 (open: 6_400_000, close: 10_000_000)
    # Candle B: 10:00 to 11:00 (open: 10_000_000, close: 13_600_000)
    # Candle C: 11:00 to 12:00 (open: 13_600_000, close: 17_200_000)
    htf_1h_df = pd.DataFrame({
        "open_time_ms": [6_400_000, 10_000_000, 13_600_000],
        "close_time_ms": [10_000_000, 13_600_000, 17_200_000],
        "ema_50": [100.0, 200.0, 300.0],
    })

    joined = joiner.join_htf_features(base_df, {Timeframe.H1: htf_1h_df})

    assert "htf_1h_ema_50" in joined.columns

    # 1. At 10:00:00 (base_times[0]):
    # Candle A closed exactly at 10:00:00.
    # Therefore, 10:00:00 sees Candle A (ema_50 = 100.0).
    assert joined.loc[joined["open_time_ms"] == 10_000_000, "htf_1h_ema_50"].values[0] == 100.0

    # 2. At 10:05:00 to 10:55:00:
    # Candle B is actively forming (closes at 13_600_000, which is 11:00:00).
    # All 5m bars in this range MUST STILL SEE Candle A (100.0) and CANNOT see Candle B (200.0)!
    for t in base_times[1:12]:  # 10:05 through 10:55
        val = joined.loc[joined["open_time_ms"] == t, "htf_1h_ema_50"].values[0]
        assert val == 100.0, f"Leakage detected at 5m open time {t}: observed {val} instead of 100.0!"

    # 3. At 11:00:00 (base_times[12] == 13_600_000):
    # Candle B has now fully closed.
    # The 11:00:00 5m bar is the first bar that can observe Candle B (ema_50 = 200.0)!
    val_1100 = joined.loc[joined["open_time_ms"] == 13_600_000, "htf_1h_ema_50"].values[0]
    assert val_1100 == 200.0

    # 4. At 11:05:00 through 11:25:00:
    # Continues to see Candle B (200.0) until 12:00:00.
    for t in base_times[13:]:
        val = joined.loc[joined["open_time_ms"] == t, "htf_1h_ema_50"].values[0]
        assert val == 200.0


def test_mtf_mutation_leakage_adversarial_test() -> None:
    """Adversarial test: Mutate future higher timeframe bar and prove past 5m features remain invariant."""
    joiner = MultiTimeframeJoiner()

    base_times = [10_000_000 + (i * 300_000) for i in range(24)]
    base_df = pd.DataFrame({
        "open_time_ms": base_times,
        "close_time_ms": [t + 300_000 - 1 for t in base_times],
        "base_val": np.arange(24),
    })

    htf_1h_original = pd.DataFrame({
        "open_time_ms": [6_400_000, 10_000_000],
        "close_time_ms": [10_000_000, 13_600_000],
        "trend_indicator": [15.5, 99.9],
    })

    joined_orig = joiner.join_htf_features(base_df, {Timeframe.H1: htf_1h_original})

    # Now mutate Candle B (10:00 to 11:00) to an extreme value
    htf_1h_mutated = htf_1h_original.copy()
    htf_1h_mutated.loc[1, "trend_indicator"] = -999999.0

    joined_mutated = joiner.join_htf_features(base_df, {Timeframe.H1: htf_1h_mutated})

    # For all 5m rows with open_time_ms < 11:00 (13_600_000), joined values MUST NOT change!
    mask_prior = joined_orig["open_time_ms"] < 13_600_000
    orig_prior = joined_orig.loc[mask_prior, "htf_1h_trend_indicator"].to_numpy()
    mutated_prior = joined_mutated.loc[mask_prior, "htf_1h_trend_indicator"].to_numpy()

    np.testing.assert_array_equal(
        orig_prior,
        mutated_prior,
        err_msg="Lookahead leakage: Mutating an in-flight HTF candle altered prior LTF feature values!",
    )


def test_mtf_missing_htf_interval_handling() -> None:
    """Verify that a missing HTF bar retains backward carry-forward without error."""
    joiner = MultiTimeframeJoiner()

    base_times = [10_000_000 + (i * 300_000) for i in range(30)]
    base_df = pd.DataFrame({
        "open_time_ms": base_times,
        "close_time_ms": [t + 300_000 - 1 for t in base_times],
    })

    # HTF has Candle A at 10:00, Candle C at 14:00 (Candle B at 11:00 and 12:00 are missing)
    htf_1h_gapped = pd.DataFrame({
        "open_time_ms": [6_400_000, 14_000_000],
        "close_time_ms": [10_000_000, 17_600_000],
        "metric": [42.0, 84.0],
    })

    joined = joiner.join_htf_features(base_df, {Timeframe.H1: htf_1h_gapped})
    assert len(joined) == 30
    # Between 10:00 and 14:00, all bars carry forward Candle A (42.0)
    mid_bars = joined.loc[joined["open_time_ms"] < 17_600_000, "htf_1h_metric"].to_numpy()
    assert np.all(mid_bars == 42.0)
