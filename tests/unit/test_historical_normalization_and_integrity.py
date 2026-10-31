"""Deterministic unit tests for OHLC invariants, gap detection, duplicates, and data quality."""

import pytest

from quantum.domain.enums import Exchange, Timeframe
from quantum.historical.models import CanonicalCandle, ValidationStatus
from quantum.historical.validator import DataQualityValidator


def create_candle(
    open_time_ms: int,
    open_p: float = 50000.0,
    high_p: float = 50100.0,
    low_p: float = 49900.0,
    close_p: float = 50050.0,
    volume: float = 10.0,
    interval_ms: int = 300_000,
    run_id: str = "RUN-01",
) -> CanonicalCandle:
    """Helper to construct valid CanonicalCandle."""
    return CanonicalCandle(
        exchange=Exchange.ASTER,
        symbol="BTCUSDT",
        market_type="PERPETUAL",
        timeframe=Timeframe.M5,
        open_time_ms=open_time_ms,
        close_time_ms=open_time_ms + interval_ms - 1,
        open=open_p,
        high=high_p,
        low=low_p,
        close=close_p,
        volume=volume,
        quote_volume=close_p * volume,
        trade_count=100,
        source_run_id=run_id,
    )


def test_ohlc_invariant_validation_clean() -> None:
    """Verify that compliant OHLC candles pass validation."""
    validator = DataQualityValidator()
    # 40 valid candles
    candles = [create_candle(1_000_000 + (i * 300_000)) for i in range(40)]

    valid, report = validator.validate_dataset(
        candles=candles,
        exchange=Exchange.ASTER,
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        requested_start_ms=1_000_000,
        requested_end_ms=1_000_000 + (39 * 300_000),
        run_id="RUN-01",
        current_time_ms=20_000_000,
    )

    assert len(valid) == 40
    assert report.invalid_ohlc_count == 0
    assert report.missing_count == 0
    assert report.duplicate_count == 0
    assert report.coverage_pct == 100.0
    assert report.validation_status == ValidationStatus.PASS


def test_incomplete_candle_exclusion() -> None:
    """Verify that in-flight or incomplete latest candles are excluded from canonical output."""
    validator = DataQualityValidator()

    # Candle 0 is fully closed (open at 1_000_000, close at 1_299_999)
    # Candle 1 is still forming at current_time_ms = 1_350_000 (open at 1_300_000, close at 1_599_999)
    candles = [
        create_candle(1_000_000),
        create_candle(1_300_000),
    ]

    valid, report = validator.validate_dataset(
        candles=candles,
        exchange=Exchange.ASTER,
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        requested_start_ms=1_000_000,
        requested_end_ms=1_600_000,
        run_id="RUN-02",
        current_time_ms=1_350_000,  # Middle of candle 1
    )

    assert len(valid) == 1
    assert valid[0].open_time_ms == 1_000_000
    assert report.incomplete_candle_count == 1


def test_gap_detection_and_interval_reporting() -> None:
    """Verify missing candles are detected and exact gap boundaries reported."""
    validator = DataQualityValidator()
    interval_ms = 300_000

    # 50 bars, but omit index 10 to 14 (5 bars missing between 9 and 15)
    candles: list[CanonicalCandle] = []
    for i in range(50):
        if 10 <= i <= 14:
            continue
        candles.append(create_candle(1_000_000 + (i * interval_ms)))

    valid, report = validator.validate_dataset(
        candles=candles,
        exchange=Exchange.ASTER,
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        requested_start_ms=1_000_000,
        requested_end_ms=1_000_000 + (49 * interval_ms),
        run_id="RUN-03",
        current_time_ms=20_000_000,
    )

    assert len(valid) == 45
    assert report.missing_count == 5
    assert report.observed_count == 45
    assert report.expected_count == 50
    assert report.coverage_pct == 90.0
    assert report.validation_status == ValidationStatus.PASS_WITH_WARNINGS

    # Check details contain gap range
    details = report.details
    assert details["missing_intervals_count"] == 1
    gap = details["missing_intervals_sample"][0]
    assert gap["missed_bars"] == 5
    assert gap["gap_start_ms"] == 1_000_000 + (10 * interval_ms)
    assert gap["gap_end_ms"] == 1_000_000 + (14 * interval_ms)


def test_duplicate_and_conflicting_duplicate_detection() -> None:
    """Verify exact duplicates are deduplicated and conflicting duplicates trigger FAIL status."""
    validator = DataQualityValidator()
    interval_ms = 300_000

    # 40 bars baseline
    candles = [create_candle(1_000_000 + (i * interval_ms)) for i in range(40)]

    # 1 exact duplicate of candle 5
    candles.append(create_candle(1_000_000 + (5 * interval_ms)))

    # 1 conflicting duplicate of candle 10 (different close price within valid high/low bounds)
    conflicting = create_candle(1_000_000 + (10 * interval_ms), close_p=50080.0)
    candles.append(conflicting)

    valid, report = validator.validate_dataset(
        candles=candles,
        exchange=Exchange.ASTER,
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        requested_start_ms=1_000_000,
        requested_end_ms=1_000_000 + (39 * interval_ms),
        run_id="RUN-04",
        current_time_ms=20_000_000,
    )

    assert len(valid) == 40  # Both duplicates were deduplicated to single distinct timestamps
    assert report.duplicate_count == 1
    assert report.conflicting_duplicate_count == 1
    assert report.validation_status == ValidationStatus.FAIL
    assert len(report.details["conflicts_sample"]) == 1


def test_out_of_order_record_sorting() -> None:
    """Verify out-of-order records are sorted ascending by open_time_ms."""
    validator = DataQualityValidator()
    interval_ms = 300_000

    c1 = create_candle(1_000_000)
    c2 = create_candle(1_000_000 + interval_ms)
    c3 = create_candle(1_000_000 + (2 * interval_ms))

    # Pass in shuffled order
    shuffled = [c3, c1, c2]
    valid, report = validator.validate_dataset(
        candles=shuffled,
        exchange=Exchange.ASTER,
        symbol="BTCUSDT",
        timeframe=Timeframe.M5,
        requested_start_ms=1_000_000,
        requested_end_ms=1_000_000 + (2 * interval_ms),
        run_id="RUN-05",
        current_time_ms=20_000_000,
    )

    assert [c.open_time_ms for c in valid] == [1_000_000, 1_000_000 + interval_ms, 1_000_000 + (2 * interval_ms)]
