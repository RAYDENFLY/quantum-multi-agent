"""Automated tests for Phase 5.2.1 Holdout Governance and Scope Verification.

Covers:
- Verification of partition boundaries including reclassified observed validation and prospective holdout.
- Verification that filter_development_and_validation strictly excludes Pre-Development and Holdouts.
- Holdout compromise status classification.
- Prospective holdout strict non-overlap and future ordering.
"""

import pandas as pd
import pytest

from quantum.features.temporal_split import (
    DEVELOPMENT_END_MS,
    DEVELOPMENT_START_MS,
    FINAL_HOLDOUT_END_MS,
    FINAL_HOLDOUT_START_MS,
    PRE_DEVELOPMENT_END_MS,
    PROSPECTIVE_HOLDOUT_END_MS,
    PROSPECTIVE_HOLDOUT_START_MS,
    VALIDATION_END_MS,
    VALIDATION_OBSERVED_END_MS,
    VALIDATION_OBSERVED_START_MS,
    VALIDATION_START_MS,
    TemporalPartition,
    TemporalPartitionManager,
)


def test_prospective_holdout_boundaries() -> None:
    """Verify prospective holdout starts exactly 1 ms after observed validation and is contiguous."""
    # Historical Final Holdout ends at 1793491199999 (2026-10-31 23:59:59.999 UTC)
    assert PROSPECTIVE_HOLDOUT_START_MS == FINAL_HOLDOUT_END_MS + 1
    assert PROSPECTIVE_HOLDOUT_START_MS == 1793491200000  # 2026-11-01 00:00:00.000 UTC
    assert PROSPECTIVE_HOLDOUT_END_MS == 1809129599999    # 2027-04-30 23:59:59.999 UTC
    assert PROSPECTIVE_HOLDOUT_START_MS < PROSPECTIVE_HOLDOUT_END_MS


def test_reclassified_validation_observed_equivalence() -> None:
    """Verify that VALIDATION_OBSERVED exactly maps to historical holdout boundaries."""
    assert VALIDATION_OBSERVED_START_MS == FINAL_HOLDOUT_START_MS
    assert VALIDATION_OBSERVED_END_MS == FINAL_HOLDOUT_END_MS


def test_filter_development_and_validation_strictly_bounds() -> None:
    """Verify that filter_development_and_validation excludes pre-dev and holdout bars."""
    df = pd.DataFrame({
        "open_time_ms": [
            PRE_DEVELOPMENT_END_MS - 1000,          # Pre-dev
            DEVELOPMENT_START_MS,                   # Dev start
            DEVELOPMENT_START_MS + 300_000,         # Dev
            DEVELOPMENT_END_MS,                     # Dev end
            VALIDATION_START_MS,                    # Val start
            VALIDATION_END_MS,                      # Val end
            FINAL_HOLDOUT_START_MS,                 # Holdout start
            FINAL_HOLDOUT_END_MS,                   # Holdout end
            PROSPECTIVE_HOLDOUT_START_MS,           # Prospective holdout
        ],
        "close": [10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0],
    })

    filtered = TemporalPartitionManager.filter_development_and_validation(df)
    
    # Must only retain indices 1, 2, 3, 4, 5 (5 rows)
    assert len(filtered) == 5
    assert filtered["open_time_ms"].min() == DEVELOPMENT_START_MS
    assert filtered["open_time_ms"].max() == VALIDATION_END_MS
    assert (filtered["open_time_ms"] < DEVELOPMENT_START_MS).sum() == 0
    assert (filtered["open_time_ms"] > VALIDATION_END_MS).sum() == 0


def test_holdout_compromised_classification() -> None:
    """Verify that is_original_holdout_compromised reports True under Phase 5.2.1 audit findings."""
    assert TemporalPartitionManager.is_original_holdout_compromised() is True
