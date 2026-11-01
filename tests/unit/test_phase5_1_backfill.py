"""Unit and integration tests for Phase 5.1 historical backfill and feature materialization.

Covers:
- Safe volume change calculation with zero-volume handling.
- Research feature filtering and 200-bar warm-up trimming.
- Zero-NaN and zero-Inf guarantees on stationary features.
- Year-partitioned Parquet storage round-trip.
- Temporal partition boundary isolation.
"""

from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from quantum.domain.enums import Exchange, Timeframe
from quantum.features.engine import FeatureEngine
from quantum.features.schema import RESEARCH_FEATURE_COLUMNS
from quantum.historical.models import CanonicalCandle, RawHistoricalCandle
from quantum.historical.storage import ParquetStorageManager


def test_vol_change_zero_volume_safety() -> None:
    """Verify that zero-volume bars do not produce NaNs or infinite values in vol_change."""
    engine = FeatureEngine()
    n = 250
    # Simulate a series where volume drops to zero repeatedly
    prices = 100.0 + np.cumsum(np.random.randn(n) * 0.5)
    highs = prices + 1.0
    lows = prices - 1.0
    opens = (highs + lows) / 2.0
    volumes = np.random.uniform(5.0, 100.0, n)
    volumes[10] = 0.0
    volumes[11] = 0.0
    volumes[50] = 0.0
    volumes[210] = 0.0
    volumes[211] = 0.0

    df = pd.DataFrame({
        "open_time_ms": [1_700_000_000_000 + (i * 300_000) for i in range(n)],
        "close_time_ms": [1_700_000_000_000 + ((i + 1) * 300_000) - 1 for i in range(n)],
        "open": opens,
        "high": highs,
        "low": lows,
        "close": prices,
        "volume": volumes,
        "quote_volume": prices * volumes,
    })

    feats = engine.compute_features(df)
    assert not np.isinf(feats["vol_change"]).any(), "vol_change contains unexpected infinite values"
    
    # After bar 0, no NaNs should exist in vol_change
    assert not feats["vol_change"].iloc[1:].isna().any(), "vol_change contains unexpected NaNs after bar 0"


def test_research_features_hygiene_and_warmup_trimming() -> None:
    """Verify filter_research_features removes warm-up and guarantees 0 NaNs and 0 Infs."""
    engine = FeatureEngine()
    n = 300
    np.random.seed(42)
    prices = 50.0 + np.cumsum(np.random.randn(n) * 0.2)
    highs = prices + 0.5
    lows = prices - 0.5
    opens = prices - 0.1
    volumes = np.random.uniform(10.0, 50.0, n)

    df = pd.DataFrame({
        "open_time_ms": [1_700_000_000_000 + (i * 300_000) for i in range(n)],
        "close_time_ms": [1_700_000_000_000 + ((i + 1) * 300_000) - 1 for i in range(n)],
        "open": opens,
        "high": highs,
        "low": lows,
        "close": prices,
        "volume": volumes,
        "quote_volume": prices * volumes,
    })

    feats = engine.compute_features(df)
    res = engine.filter_research_features(feats, warmup_bars=200)

    # Expected row count: 300 - 200 = 100 rows
    assert len(res) == 100
    assert len(res.columns) == len(RESEARCH_FEATURE_COLUMNS)
    assert res.isna().sum().sum() == 0, "Research features contain unexpected NaNs"
    num_cols = res.select_dtypes(include=[np.number]).columns
    assert not np.isinf(res[num_cols]).any().any(), "Research features contain infinite values"


def test_year_partitioned_storage_roundtrip(tmp_path: Path) -> None:
    """Verify writing and reading canonical and feature records across year partitions."""
    storage = ParquetStorageManager(tmp_path)
    sym = "TESTUSDT"
    tf = Timeframe.H1

    # Create candles spanning two years (2024 and 2025)
    t_2024 = int(datetime(2024, 6, 1, tzinfo=timezone.utc).timestamp() * 1000)
    t_2025 = int(datetime(2025, 6, 1, tzinfo=timezone.utc).timestamp() * 1000)

    candles = [
        CanonicalCandle(
            exchange=Exchange.ASTER,
            symbol=sym,
            market_type="PERPETUAL",
            timeframe=tf,
            open_time_ms=t_2024,
            close_time_ms=t_2024 + 3599999,
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=500.0,
            ingestion_time_ms=t_2024,
            source_run_id="TEST-RUN",
        ),
        CanonicalCandle(
            exchange=Exchange.ASTER,
            symbol=sym,
            market_type="PERPETUAL",
            timeframe=tf,
            open_time_ms=t_2025,
            close_time_ms=t_2025 + 3599999,
            open=102.0,
            high=110.0,
            low=101.0,
            close=108.0,
            volume=600.0,
            ingestion_time_ms=t_2025,
            source_run_id="TEST-RUN",
        ),
    ]

    paths = storage.write_canonical_partitioned_by_year(candles, Exchange.ASTER, sym, tf)
    assert len(paths) == 2
    assert any("2024.parquet" in str(p) for p in paths)
    assert any("2025.parquet" in str(p) for p in paths)

    # Read combined canonical data seamlessly
    df_read = storage.read_canonical(Exchange.ASTER, sym, tf)
    assert len(df_read) == 2
    assert df_read["open_time_ms"].tolist() == [t_2024, t_2025]


def test_temporal_holdout_boundaries() -> None:
    """Verify temporal partition boundaries are strictly ordered, contiguous, and non-overlapping."""
    dev_start = 1698796800000      # 2023-11-01 00:00:00 UTC
    dev_end = 1761955199999        # 2025-10-31 23:59:59.999 UTC
    val_start = 1761955200000      # 2025-11-01 00:00:00 UTC
    val_end = 1777593599999        # 2026-04-30 23:59:59.999 UTC
    holdout_start = 1777593600000  # 2026-05-01 00:00:00 UTC
    holdout_end = 1793491199999    # 2026-10-31 23:59:59.999 UTC

    # 1. Contiguity
    assert val_start == dev_end + 1, "Validation start must follow development end by 1 ms"
    assert holdout_start == val_end + 1, "Holdout start must follow validation end by 1 ms"

    # 2. Strict Ordering
    assert dev_start < dev_end < val_start < val_end < holdout_start < holdout_end

    # 3. Isolation
    assert holdout_start - val_end == 1
