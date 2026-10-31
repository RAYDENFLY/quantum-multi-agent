"""Data quality validator for historical market data integrity, gaps, and invariants."""

import time
from typing import Any, Dict, List, Optional, Set, Tuple
import pandas as pd

from quantum.core.logging import get_logger
from quantum.domain.enums import Exchange, Timeframe
from quantum.historical.models import (
    CanonicalCandle,
    DataQualityReport,
    ValidationStatus,
)

logger = get_logger("historical.validator")

TIMEFRAME_INTERVAL_MS: Dict[Timeframe, int] = {
    Timeframe.M1: 60_000,
    Timeframe.M3: 180_000,
    Timeframe.M5: 300_000,
    Timeframe.M15: 900_000,
    Timeframe.M30: 1_800_000,
    Timeframe.H1: 3_600_000,
    Timeframe.H2: 7_200_000,
    Timeframe.H4: 14_400_000,
    Timeframe.D1: 86_400_000,
}


class DataQualityValidator:
    """Validates structural invariants, timestamps, gaps, and duplicates in historical datasets."""

    def __init__(self, feature_version: str = "FEATURE_V1", dataset_version: str = "DATASET_V1") -> None:
        self.feature_version = feature_version
        self.dataset_version = dataset_version

    def validate_dataset(
        self,
        candles: List[CanonicalCandle],
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
        requested_start_ms: int,
        requested_end_ms: int,
        run_id: str,
        current_time_ms: Optional[int] = None,
        listing_start_time_ms: Optional[int] = None,
    ) -> Tuple[List[CanonicalCandle], DataQualityReport]:
        """Audit candidate canonical candles, exclude incomplete bars, and produce quality report."""
        now_ms = current_time_ms or int(time.time() * 1000)
        interval_ms = TIMEFRAME_INTERVAL_MS.get(timeframe, 300_000)

        # 1. Structural and OHLC invariant validation
        valid_candles: List[CanonicalCandle] = []
        invalid_ohlc_count = 0
        incomplete_candle_count = 0
        misaligned_timestamp_count = 0

        # Duplicate tracking
        seen_timestamps: Dict[int, CanonicalCandle] = {}
        exact_duplicate_count = 0
        conflicting_duplicate_count = 0
        conflicts: List[Dict[str, Any]] = []

        for c in candles:
            # Incomplete candle check: if candle close time or interval extends past current time
            if c.close_time_ms > now_ms or (c.open_time_ms + interval_ms) > now_ms:
                incomplete_candle_count += 1
                logger.debug("Excluded incomplete in-flight candle for %s %s at %d", symbol, timeframe.value, c.open_time_ms)
                continue

            # Timeframe boundary and span alignment check
            candle_span = c.close_time_ms - c.open_time_ms + 1
            is_span_valid = (candle_span == interval_ms)
            is_boundary_valid = (c.open_time_ms % interval_ms == 0) if c.open_time_ms > 1_000_000_000_000 else True

            if not (is_span_valid and is_boundary_valid):
                misaligned_timestamp_count += 1
                logger.warning(
                    "Misaligned candle timestamp detected for %s %s: open=%d, span=%d, expected=%d",
                    symbol, timeframe.value, c.open_time_ms, candle_span, interval_ms
                )
                continue

            # OHLC boundary check
            if not self._check_ohlc_invariants(c):
                invalid_ohlc_count += 1
                logger.warning("Invalid OHLC invariants detected for %s %s at %d", symbol, timeframe.value, c.open_time_ms)
                continue

            # Duplicate check
            ts = c.open_time_ms
            if ts in seen_timestamps:
                prior = seen_timestamps[ts]
                if (
                    prior.open == c.open
                    and prior.high == c.high
                    and prior.low == c.low
                    and prior.close == c.close
                    and prior.volume == c.volume
                ):
                    exact_duplicate_count += 1
                else:
                    conflicting_duplicate_count += 1
                    conflicts.append({
                        "open_time_ms": ts,
                        "prior_ohlc": [prior.open, prior.high, prior.low, prior.close, prior.volume],
                        "new_ohlc": [c.open, c.high, c.low, c.close, c.volume],
                    })
                # In both cases, keep latest record deterministically
                seen_timestamps[ts] = c
            else:
                seen_timestamps[ts] = c

        valid_candles = list(seen_timestamps.values())
        valid_candles.sort(key=lambda x: x.open_time_ms)

        # 2. Gap and coverage analysis
        observed_count = len(valid_candles)
        actual_start_ms = valid_candles[0].open_time_ms if observed_count > 0 else requested_start_ms
        actual_end_ms = valid_candles[-1].open_time_ms if observed_count > 0 else requested_end_ms

        if observed_count > 0:
            effective_start = max(requested_start_ms, listing_start_time_ms) if listing_start_time_ms else max(requested_start_ms, actual_start_ms)
            effective_end = min(requested_end_ms, actual_end_ms)
            expected_count = max(1, int((effective_end - effective_start) // interval_ms) + 1)
        else:
            effective_start = max(requested_start_ms, listing_start_time_ms) if listing_start_time_ms else requested_start_ms
            expected_count = max(1, int((requested_end_ms - effective_start) // interval_ms) + 1)

        missing_count = 0
        missing_intervals: List[Dict[str, int]] = []

        if observed_count > 0 and listing_start_time_ms and actual_start_ms > effective_start:
            lead_missed = int((actual_start_ms - effective_start) // interval_ms)
            if lead_missed > 0:
                missing_count += lead_missed
                missing_intervals.append({
                    "gap_start_ms": effective_start,
                    "gap_end_ms": actual_start_ms - interval_ms,
                    "missed_bars": lead_missed,
                })

        if observed_count > 1:
            for i in range(1, observed_count):
                prev_ts = valid_candles[i - 1].open_time_ms
                curr_ts = valid_candles[i].open_time_ms
                diff = curr_ts - prev_ts
                if diff > interval_ms:
                    missed_bars = int(diff // interval_ms) - 1
                    missing_count += missed_bars
                    missing_intervals.append({
                        "gap_start_ms": prev_ts + interval_ms,
                        "gap_end_ms": curr_ts - interval_ms,
                        "missed_bars": missed_bars,
                    })

        coverage_pct = round(min(100.0, (observed_count / expected_count) * 100.0), 2) if expected_count > 0 else 0.0

        # 3. Determine validation status
        if observed_count < 30:
            status = ValidationStatus.INSUFFICIENT_HISTORY
        elif invalid_ohlc_count > 0 or conflicting_duplicate_count > 0 or misaligned_timestamp_count > 0:
            status = ValidationStatus.FAIL
        elif coverage_pct < 80.0:
            status = ValidationStatus.FAIL
        elif coverage_pct < 98.0 or missing_count > 0 or exact_duplicate_count > 0:
            status = ValidationStatus.PASS_WITH_WARNINGS
        else:
            status = ValidationStatus.PASS

        report = DataQualityReport(
            report_id=f"DQR-{exchange.value}-{symbol}-{timeframe.value}-{int(time.time()*1000)}",
            run_id=run_id,
            exchange=exchange,
            symbol=symbol,
            timeframe=timeframe,
            requested_start_ms=requested_start_ms,
            requested_end_ms=requested_end_ms,
            actual_start_ms=actual_start_ms,
            actual_end_ms=actual_end_ms,
            expected_count=expected_count,
            observed_count=observed_count,
            missing_count=missing_count,
            duplicate_count=exact_duplicate_count,
            conflicting_duplicate_count=conflicting_duplicate_count,
            invalid_ohlc_count=invalid_ohlc_count,
            incomplete_candle_count=incomplete_candle_count,
            coverage_pct=coverage_pct,
            validation_status=status,
            feature_version=self.feature_version,
            dataset_version=self.dataset_version,
            details={
                "interval_ms": interval_ms,
                "misaligned_timestamp_count": misaligned_timestamp_count,
                "missing_intervals_count": len(missing_intervals),
                "missing_intervals_sample": missing_intervals[:10],
                "conflicts_sample": conflicts[:5],
            },
        )

        return valid_candles, report

    @staticmethod
    def _check_ohlc_invariants(c: CanonicalCandle) -> bool:
        """Verify strict non-negative positive prices and low <= open/close <= high."""
        if c.open <= 0.0 or c.high <= 0.0 or c.low <= 0.0 or c.close <= 0.0:
            return False
        if c.volume < 0.0:
            return False
        if c.high < max(c.open, c.close):
            return False
        if c.low > min(c.open, c.close):
            return False
        if c.high < c.low:
            return False
        if c.close_time_ms <= c.open_time_ms:
            return False
        return True
