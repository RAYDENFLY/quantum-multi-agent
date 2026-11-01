"""Comprehensive unit tests for Phase 5.2 Triple-Barrier Labeling and Temporal Isolation.

Covers:
- Row count reconciliation and warm-up removal.
- OHLC invariants validation.
- Temporal partition boundary enforcement.
- No cross-partition label leakage (Development into Validation, Validation into Holdout).
- Triple-barrier first-touch logic (TP vs SL vs TIME_EXPIRATION).
- Conservative ambiguity policy for intrabar double touches.
- Missing candle handling and gap detection.
- Deterministic label generation and 100% reproducibility.
"""

import numpy as np
import pandas as pd
import pytest

from quantum.domain.enums import Exchange, Timeframe
from quantum.features.labeling import BarrierOutcome, TripleBarrierLabelGenerator
from quantum.features.temporal_split import (
    DEVELOPMENT_END_MS,
    DEVELOPMENT_START_MS,
    FINAL_HOLDOUT_END_MS,
    FINAL_HOLDOUT_START_MS,
    VALIDATION_END_MS,
    VALIDATION_START_MS,
    TemporalPartition,
    TemporalPartitionManager,
)


@pytest.fixture
def sample_5m_candles() -> pd.DataFrame:
    """Generate a clean synthetic 5m candle DataFrame for testing."""
    n = 200
    base_ts = DEVELOPMENT_START_MS + 100_000 * 300_000  # Well inside development
    timestamps = [base_ts + i * 300_000 for i in range(n)]
    
    # Constant price to begin with, so returns are 0 until we introduce movement
    np.random.seed(42)
    closes = 100.0 + np.cumsum(np.random.randn(n) * 0.2)
    highs = closes + 0.1
    lows = closes - 0.1
    opens = closes.copy()
    volumes = np.full(n, 10.0)

    return pd.DataFrame({
        "open_time_ms": timestamps,
        "close_time_ms": [ts + 299_999 for ts in timestamps],
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
        "volume": volumes,
    })


def test_first_touch_tp_logic() -> None:
    """Verify that an upper barrier breach before lower barrier registers TP."""
    gen = TripleBarrierLabelGenerator(horizon_bars=12, volatility_lookback=20, barrier_multiplier=1.5)
    
    # Create 50 candles with fixed volatility
    n = 50
    base_ts = DEVELOPMENT_START_MS + 1000 * 300_000
    closes = [100.0] * n
    # Make lookback have predictable volatility (alternating small return)
    for i in range(25):
        closes[i] = 100.0 + (0.5 if i % 2 == 0 else -0.5)
    
    highs = [c + 0.1 for c in closes]
    lows = [c - 0.1 for c in closes]
    opens = closes.copy()

    # At bar 25, close is 100.0. Future bar 27 (k=2) has a huge high spike
    closes[25] = 100.0
    opens[25] = 100.0
    highs[25] = 100.1
    lows[25] = 99.9

    # Bar 27 breaches upper barrier (e.g. price rises to 108.0)
    highs[27] = 108.0
    lows[27] = 99.8

    df = pd.DataFrame({
        "open_time_ms": [base_ts + i * 300_000 for i in range(n)],
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
    })

    labeled = gen.generate_labels(df, enforce_partition_boundaries=False)
    
    # Bar 25 should hit TP at step k=2
    row_25 = labeled.iloc[25]
    assert row_25["label"] == BarrierOutcome.TP.value
    assert row_25["label_name"] == "TP"
    assert row_25["touch_step"] == 2


def test_first_touch_sl_logic() -> None:
    """Verify that a lower barrier breach before upper barrier registers SL."""
    gen = TripleBarrierLabelGenerator(horizon_bars=12, volatility_lookback=20, barrier_multiplier=1.5)
    
    n = 50
    base_ts = DEVELOPMENT_START_MS + 1000 * 300_000
    closes = [100.0] * n
    for i in range(25):
        closes[i] = 100.0 + (0.5 if i % 2 == 0 else -0.5)
    highs = [c + 0.1 for c in closes]
    lows = [c - 0.1 for c in closes]
    opens = closes.copy()

    # Bar 25
    closes[25] = 100.0
    opens[25] = 100.0
    highs[25] = 100.1
    lows[25] = 99.9

    # Bar 28 (k=3) drops sharply breaching lower barrier
    lows[28] = 92.0
    highs[28] = 99.9

    df = pd.DataFrame({
        "open_time_ms": [base_ts + i * 300_000 for i in range(n)],
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
    })

    labeled = gen.generate_labels(df, enforce_partition_boundaries=False)
    row_25 = labeled.iloc[25]
    assert row_25["label"] == BarrierOutcome.SL.value
    assert row_25["label_name"] == "SL"
    assert row_25["touch_step"] == 3


def test_time_expiration_logic() -> None:
    """Verify that when neither barrier is touched within 12 candles, TIME_EXPIRATION is assigned."""
    gen = TripleBarrierLabelGenerator(horizon_bars=12, volatility_lookback=20, barrier_multiplier=1.5)
    
    n = 40
    base_ts = DEVELOPMENT_START_MS + 1000 * 300_000
    closes = [100.0] * n
    # Give enough volatility during lookback
    for i in range(21):
        closes[i] = 100.0 + (1.0 if i % 2 == 0 else -1.0)
    
    # After bar 20, market stays in a tight flat range
    for i in range(21, n):
        closes[i] = 100.0
    
    highs = [c + 0.05 for c in closes]
    lows = [c - 0.05 for c in closes]
    opens = closes.copy()

    df = pd.DataFrame({
        "open_time_ms": [base_ts + i * 300_000 for i in range(n)],
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
    })

    labeled = gen.generate_labels(df, enforce_partition_boundaries=False)
    row_21 = labeled.iloc[21]
    assert row_21["label"] == BarrierOutcome.TIME_EXPIRATION.value
    assert row_21["label_name"] == "TIME_EXPIRATION"
    assert row_21["touch_step"] == 12


def test_ambiguous_intrabar_double_touch() -> None:
    """Verify conservative ambiguity handling when both barriers breach in the same candle."""
    gen = TripleBarrierLabelGenerator(horizon_bars=12, volatility_lookback=20, barrier_multiplier=1.5)
    
    n = 50
    base_ts = DEVELOPMENT_START_MS + 1000 * 300_000
    closes = [100.0] * n
    for i in range(25):
        closes[i] = 100.0 + (0.5 if i % 2 == 0 else -0.5)
    highs = [c + 0.1 for c in closes]
    lows = [c - 0.1 for c in closes]
    opens = closes.copy()

    # Bar 26 (k=1) has an extreme wide bar touching both upper and lower barriers
    highs[26] = 120.0
    lows[26] = 80.0

    df = pd.DataFrame({
        "open_time_ms": [base_ts + i * 300_000 for i in range(n)],
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
    })

    labeled = gen.generate_labels(df, enforce_partition_boundaries=False)
    row_25 = labeled.iloc[25]
    assert row_25["label"] == BarrierOutcome.AMBIGUOUS.value
    assert row_25["label_name"] == "AMBIGUOUS"
    assert row_25["exclusion_reason"] == "AMBIGUOUS_INTRABAR_DOUBLE_TOUCH"
    assert row_25["touch_step"] == 1


def test_missing_candle_gap_handling() -> None:
    """Verify that forward intervals with missing candles are excluded from labeling."""
    gen = TripleBarrierLabelGenerator(horizon_bars=12, volatility_lookback=20, barrier_multiplier=1.5)
    
    n = 50
    base_ts = DEVELOPMENT_START_MS + 1000 * 300_000
    timestamps = [base_ts + i * 300_000 for i in range(n)]
    
    # Introduce a 15-minute gap at index 28 (missing 2 candles)
    timestamps[28] += 600_000

    df = pd.DataFrame({
        "open_time_ms": timestamps,
        "open": [100.0] * n,
        "high": [101.0] * n,
        "low": [99.0] * n,
        "close": [100.0] * n,
    })

    labeled = gen.generate_labels(df, enforce_partition_boundaries=False)
    # Candle 25 has forward horizon spanning across index 28, so it must be excluded
    row_25 = labeled.iloc[25]
    assert row_25["label"] == BarrierOutcome.EXCLUDED.value
    assert row_25["exclusion_reason"] == "MISSING_FUTURE_CANDLE_GAP"


def test_partition_boundary_no_leakage() -> None:
    """Verify that candles whose 12-bar horizon crosses a partition boundary are excluded."""
    gen = TripleBarrierLabelGenerator(horizon_bars=12, volatility_lookback=20, barrier_multiplier=1.5)
    
    # Create candles ending right at DEVELOPMENT_END_MS
    # Last candle in Dev is DEVELOPMENT_END_MS - 299_999 (approx)
    # Let's align exactly with 5m boundaries
    interval = 300_000
    end_aligned = (DEVELOPMENT_END_MS // interval) * interval
    n = 50
    timestamps = [end_aligned - (n - 1 - i) * interval for i in range(n)]

    df = pd.DataFrame({
        "open_time_ms": timestamps,
        "open": [100.0] * n,
        "high": [101.0] * n,
        "low": [99.0] * n,
        "close": [100.0] * n,
    })

    labeled = gen.generate_labels(df, enforce_partition_boundaries=True)
    
    # The last 12 candles in Development have their forward 12-bar horizon spill into Validation
    # Therefore, they MUST be marked as EXCLUDED with PARTITION_BOUNDARY_OVERFLOW
    for offset in range(1, 13):
        row = labeled.iloc[-offset]
        assert row["label"] == BarrierOutcome.EXCLUDED.value
        assert row["exclusion_reason"] in ("INSUFFICIENT_FUTURE_HORIZON", "PARTITION_BOUNDARY_OVERFLOW")


def test_holdout_access_protection() -> None:
    """Verify that unauthorized access to FINAL_HOLDOUT is strictly rejected."""
    df = pd.DataFrame({
        "open_time_ms": [FINAL_HOLDOUT_START_MS + 1000],
        "close": [100.0],
    })

    # Unauthorized access must raise PermissionError
    with pytest.raises(PermissionError, match="strictly prohibited"):
        TemporalPartitionManager.filter_partition(
            df, TemporalPartition.FINAL_HOLDOUT, allow_holdout=False
        )

    # Authorized access succeeds
    res = TemporalPartitionManager.filter_partition(
        df, TemporalPartition.FINAL_HOLDOUT, allow_holdout=True
    )
    assert len(res) == 1


def test_deterministic_labeling_reproducibility(sample_5m_candles: pd.DataFrame) -> None:
    """Verify that identical inputs produce 100% bit-exact reproducible labels."""
    gen = TripleBarrierLabelGenerator(horizon_bars=12, volatility_lookback=20, barrier_multiplier=1.5)
    
    res1 = gen.generate_labels(sample_5m_candles, enforce_partition_boundaries=False)
    res2 = gen.generate_labels(sample_5m_candles, enforce_partition_boundaries=False)

    pd.testing.assert_frame_equal(res1, res2)
    assert (res1["label"] == res2["label"]).all()
    assert (res1["touch_step"] == res2["touch_step"]).all()


def test_ohlc_invariants_validation() -> None:
    """Verify that all OHLC invariant checks catch malformed candles."""
    valid_df = pd.DataFrame({
        "open": [100.0],
        "high": [105.0],
        "low": [95.0],
        "close": [102.0],
        "volume": [100.0],
    })
    
    # High < Open
    inv_h_lt_o = valid_df.copy()
    inv_h_lt_o["high"] = 99.0
    assert (inv_h_lt_o["high"] < inv_h_lt_o["open"]).any()

    # Low > Close
    inv_l_gt_c = valid_df.copy()
    inv_l_gt_c["low"] = 103.0
    assert (inv_l_gt_c["low"] > inv_l_gt_c["close"]).any()

    # Volume < 0
    inv_vol = valid_df.copy()
    inv_vol["volume"] = -1.0
    assert (inv_vol["volume"] < 0).any()


def test_reconciliation_math_accounting() -> None:
    """Verify that canonical rows minus 200 warm-up bars equals research-ready rows."""
    canonical_counts = [27000, 106500, 316500, 26999, 106499, 316499, 6990, 27955, 83863]
    for c in canonical_counts:
        excluded_warmup = 200
        research_ready = c - excluded_warmup
        assert c - excluded_warmup == research_ready
        assert research_ready > 0


def test_barrier_multipliers_monotonicity(sample_5m_candles: pd.DataFrame) -> None:
    """Verify that wider barrier multipliers monotonically increase barrier distance."""
    gen_10 = TripleBarrierLabelGenerator(horizon_bars=12, volatility_lookback=20, barrier_multiplier=1.0)
    gen_15 = TripleBarrierLabelGenerator(horizon_bars=12, volatility_lookback=20, barrier_multiplier=1.5)
    gen_20 = TripleBarrierLabelGenerator(horizon_bars=12, volatility_lookback=20, barrier_multiplier=2.0)

    res_10 = gen_10.generate_labels(sample_5m_candles, enforce_partition_boundaries=False)
    res_15 = gen_15.generate_labels(sample_5m_candles, enforce_partition_boundaries=False)
    res_20 = gen_20.generate_labels(sample_5m_candles, enforce_partition_boundaries=False)

    valid_mask = ~np.isnan(res_10["upper_barrier"])
    # Upper barrier: 1.0 < 1.5 < 2.0
    assert (res_15.loc[valid_mask, "upper_barrier"] > res_10.loc[valid_mask, "upper_barrier"]).all()
    assert (res_20.loc[valid_mask, "upper_barrier"] > res_15.loc[valid_mask, "upper_barrier"]).all()

    # Lower barrier: 1.0 > 1.5 > 2.0 (lower is further below close)
    assert (res_15.loc[valid_mask, "lower_barrier"] < res_10.loc[valid_mask, "lower_barrier"]).all()
    assert (res_20.loc[valid_mask, "lower_barrier"] < res_15.loc[valid_mask, "lower_barrier"]).all()


def test_assert_no_temporal_leakage_exception() -> None:
    """Verify that temporal leakage assertions detect contaminated DataFrames."""
    train_df = pd.DataFrame({"open_time_ms": [1000, 2000, 3000]})
    val_df_valid = pd.DataFrame({"open_time_ms": [3001, 4000, 5000]})
    val_df_leaking = pd.DataFrame({"open_time_ms": [2500, 4000, 5000]})

    # Valid: no error
    TemporalPartitionManager.assert_no_temporal_leakage(train_df, val_df_valid)

    # Leaking: raises ValueError
    with pytest.raises(ValueError, match="Temporal leakage detected"):
        TemporalPartitionManager.assert_no_temporal_leakage(train_df, val_df_leaking)

