"""Deterministic unit tests for feature engineering, known-value indicators, and zero lookahead."""

import numpy as np
import pandas as pd
import pytest

from quantum.features.engine import FeatureEngine
from quantum.features.indicators import (
    compute_atr,
    compute_bollinger_bands,
    compute_donchian_channels,
    compute_ema,
    compute_macd,
    compute_rsi,
    compute_stochastic,
)


def test_ema_known_values_and_warmup() -> None:
    """Verify EMA matches analytical values on constant and linear series."""
    # 1. Constant series: EMA must equal constant
    const_series = np.full(50, 42.0, dtype=np.float64)
    ema_9 = compute_ema(const_series, 9)

    # Warm-up: first 8 values are NaN
    assert np.all(np.isnan(ema_9[:8]))
    # Starting at index 8 (9th bar), value must be 42.0
    assert np.allclose(ema_9[8:], 42.0)

    # 2. Step series: analytical formula check
    # series of 10 tens followed by 10 twenties
    step_series = np.array([10.0] * 10 + [20.0] * 10)
    ema_5 = compute_ema(step_series, 5)
    assert np.all(np.isnan(ema_5[:4]))
    assert np.isclose(ema_5[4], 10.0)
    # At index 10 (first twenty): ema_10 = 20 * (2/6) + 10 * (4/6) = 6.6667 + 6.6667 = 13.3333
    expected_10 = 20.0 * (2.0 / 6.0) + 10.0 * (4.0 / 6.0)
    assert np.isclose(ema_5[10], expected_10)


def test_rsi_known_values_extremes() -> None:
    """Verify RSI behavior on monotonic and constant sequences."""
    # 1. Strictly increasing: RSI must be 100
    inc_series = np.arange(1.0, 50.0, 1.0)
    rsi_inc = compute_rsi(inc_series, 14)
    assert np.all(np.isnan(rsi_inc[:14]))
    assert np.allclose(rsi_inc[14:], 100.0)

    # 2. Strictly decreasing: RSI must be 0
    dec_series = np.arange(50.0, 1.0, -1.0)
    rsi_dec = compute_rsi(dec_series, 14)
    assert np.all(np.isnan(rsi_dec[:14]))
    assert np.allclose(rsi_dec[14:], 0.0)

    # 3. Constant prices: RSI is 50.0
    const_series = np.full(30, 100.0, dtype=np.float64)
    rsi_const = compute_rsi(const_series, 14)
    assert np.all(np.isnan(rsi_const[:14]))
    assert np.allclose(rsi_const[14:], 50.0)


def test_atr_and_bollinger_known_values() -> None:
    """Verify ATR and Bollinger Bands known mathematical values."""
    # Constant range bar of 10.0
    h = np.full(30, 110.0)
    l = np.full(30, 100.0)
    c = np.full(30, 105.0)

    atr = compute_atr(h, l, c, 14)
    assert np.all(np.isnan(atr[:13]))
    assert np.allclose(atr[13:], 10.0)

    # Bollinger Bands on constant close
    mid, up, low, bw, pct_b = compute_bollinger_bands(c, 20, 2.0)
    assert np.all(np.isnan(mid[:19]))
    assert np.allclose(mid[19:], 105.0)
    assert np.allclose(up[19:], 105.0)
    assert np.allclose(low[19:], 105.0)
    assert np.allclose(bw[19:], 0.0)


def test_donchian_channel_causality() -> None:
    """Verify Donchian channel strictly shifts by 1 bar to prevent intra-bar lookahead."""
    # Series with a sudden spike at bar 20
    h = np.full(30, 100.0)
    l = np.full(30, 90.0)
    h[20] = 500.0  # Big spike on bar 20

    don_h, don_l = compute_donchian_channels(h, l, 10)

    # At bar 20, donchian_high MUST NOT include bar 20's high (it must be 100.0)
    assert np.isclose(don_h[20], 100.0)
    # At bar 21, donchian_high should now reflect the spike at bar 20 (500.0)
    assert np.isclose(don_h[21], 500.0)


def test_feature_engine_zero_volume_and_flat_price() -> None:
    """Verify that zero volume and flat prices do not produce Inf or ZeroDivisionError."""
    engine = FeatureEngine()
    n = 60
    # Flat price where open == high == low == close, volume == 0
    df_flat = pd.DataFrame({
        "open_time_ms": [1_000_000 + (i * 300_000) for i in range(n)],
        "close_time_ms": [1_000_000 + ((i + 1) * 300_000) - 1 for i in range(n)],
        "open": np.full(n, 50000.0),
        "high": np.full(n, 50000.0),
        "low": np.full(n, 50000.0),
        "close": np.full(n, 50000.0),
        "volume": np.zeros(n),
        "quote_volume": np.zeros(n),
    })

    feats = engine.compute_features(df_flat)
    assert len(feats) == n

    # Check for any infinite values in the output
    numeric_cols = feats.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        vals = feats[col].to_numpy()
        assert not np.any(np.isinf(vals)), f"Infinite values found in column {col}"


def test_feature_engine_deterministic_repeatability() -> None:
    """Verify identical input data produces bit-for-bit identical feature matrices."""
    engine = FeatureEngine()
    np.random.seed(42)
    n = 100
    prices = 50000.0 + np.cumsum(np.random.randn(n) * 10.0)
    highs = prices + np.abs(np.random.randn(n) * 5.0)
    lows = prices - np.abs(np.random.randn(n) * 5.0)
    opens = (highs + lows) / 2.0
    vols = np.random.uniform(1.0, 50.0, n)

    df = pd.DataFrame({
        "open_time_ms": [1_000_000 + (i * 300_000) for i in range(n)],
        "close_time_ms": [1_000_000 + ((i + 1) * 300_000) - 1 for i in range(n)],
        "open": opens,
        "high": highs,
        "low": lows,
        "close": prices,
        "volume": vols,
        "quote_volume": prices * vols,
    })

    run1 = engine.compute_features(df)
    run2 = engine.compute_features(df)

    pd.testing.assert_frame_equal(run1, run2)


def test_feature_engine_zero_lookahead_leakage() -> None:
    """Verify mutating future bars leaves all historical feature values bit-for-bit identical."""
    engine = FeatureEngine()
    np.random.seed(123)
    n = 150
    prices = 50000.0 + np.cumsum(np.random.randn(n) * 10.0)
    highs = prices + 15.0
    lows = prices - 15.0
    opens = prices - 2.0
    vols = np.random.uniform(5.0, 20.0, n)

    df_original = pd.DataFrame({
        "open_time_ms": [1_000_000 + (i * 300_000) for i in range(n)],
        "close_time_ms": [1_000_000 + ((i + 1) * 300_000) - 1 for i in range(n)],
        "open": opens,
        "high": highs,
        "low": lows,
        "close": prices,
        "volume": vols,
        "quote_volume": prices * vols,
    })

    feats_orig = engine.compute_features(df_original)

    # Mutate future rows (e.g. from index 100 to 149)
    df_mutated = df_original.copy()
    df_mutated.loc[100:, "close"] = df_mutated.loc[100:, "close"] * 2.5
    df_mutated.loc[100:, "high"] = df_mutated.loc[100:, "high"] * 3.0
    df_mutated.loc[100:, "volume"] = df_mutated.loc[100:, "volume"] * 10.0

    feats_mutated = engine.compute_features(df_mutated)

    # Features at indices 0 to 99 MUST BE IDENTICAL
    cols = [c for c in feats_orig.columns if c not in ("open_time_ms", "close_time_ms")]
    for col in cols:
        v_orig = feats_orig.loc[:99, col].to_numpy()
        v_mut = feats_mutated.loc[:99, col].to_numpy()
        # Handle NaNs and exact float match
        np.testing.assert_allclose(
            np.nan_to_num(v_orig),
            np.nan_to_num(v_mut),
            rtol=1e-12,
            atol=1e-12,
            err_msg=f"Lookahead leakage detected in column {col} prior to mutation point!",
        )
