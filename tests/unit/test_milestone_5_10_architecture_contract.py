"""Unit tests for Milestone 5.10 High-Frequency Research Architecture Correction."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import pyarrow.parquet as pq

from quantum.domain.research_contract import (
    ResearchExperimentContract,
    ExperimentCategory,
    ExecutionTimeframe,
    TimeframeMismatchError,
    HoldingHorizonViolationError,
    ExposureViolationError,
    validate_input_data_timeframe,
    validate_trade_durations,
    validate_portfolio_gross_leverage,
)

ROOT = Path(__file__).resolve().parent.parent.parent
M5_10_DIR = ROOT / "audit" / "strategy_research" / "milestone_5_10_architecture_correction"
CANONICAL_DIR = ROOT / "data" / "historical" / "canonical" / "exchange=ASTER"
HOLDOUT_TIMESTAMP_MS = 1_793_491_200_000  # 2026-11-01 00:00:00 UTC


def test_m5_10_deliverables_exist():
    """Verify all 5 Milestone 5.10 deliverables exist and are non-empty."""
    required_files = [
        "M5_10_ARCHITECTURE_AUDIT.md",
        "M5_10_RESEARCH_CONTRACT.md",
        "M5_10_HISTORICAL_EXPERIMENT_CLASSIFICATION.csv",
        "M5_10_TIMEFRAME_INTEGRITY_TESTS.md",
        "M5_10_INTRADAY_DATA_READINESS.md",
    ]
    for fname in required_files:
        fpath = M5_10_DIR / fname
        assert fpath.exists(), f"Missing required file: {fname}"
        assert fpath.stat().st_size > 0, f"File is empty: {fname}"


def test_research_contract_instantiation_and_invariants():
    """Verify ResearchExperimentContract model constraints, defaults, and exposure caps."""
    contract = ResearchExperimentContract(
        experiment_id="EXP-12-TEST",
        experiment_name="High-Frequency Intraday Test Alpha",
        experiment_category=ExperimentCategory.HIGH_FREQUENCY_INTRADAY,
        execution_timeframe=ExecutionTimeframe.TF_5M,
    )
    assert contract.execution_timeframe == ExecutionTimeframe.TF_5M
    assert contract.maximum_gross_exposure == 1.0000
    assert contract.initial_equity_usd == 100.0
    assert contract.mandatory_profitability_gate_daily_pct == 3.0000
    assert contract.maximum_holding_horizon_minutes == 1440
    assert contract.allow_overnight_holding is False

    # Attempting leverage > 1.0 must fail
    with pytest.raises(Exception):
        ResearchExperimentContract(
            experiment_id="EXP-LEVERAGE-FAIL",
            experiment_name="Leverage Exceeded",
            experiment_category=ExperimentCategory.HIGH_FREQUENCY_INTRADAY,
            maximum_gross_exposure=1.5,
        )


def test_timeframe_mismatch_validation_rejection():
    """Verify that silent downsampling (e.g. 1D or 1h data for a 5m contract) raises TimeframeMismatchError."""
    contract = ResearchExperimentContract(
        experiment_id="EXP-12-TF-CHECK",
        experiment_name="Timeframe Validation Test",
        experiment_category=ExperimentCategory.HIGH_FREQUENCY_INTRADAY,
        execution_timeframe=ExecutionTimeframe.TF_5M,
    )

    # Valid match
    validate_input_data_timeframe(contract, "5m")

    # Invalid mismatches must raise TimeframeMismatchError
    with pytest.raises(TimeframeMismatchError):
        validate_input_data_timeframe(contract, "1D")

    with pytest.raises(TimeframeMismatchError):
        validate_input_data_timeframe(contract, "1h")

    with pytest.raises(TimeframeMismatchError):
        validate_input_data_timeframe(contract, "15m")


def test_category_a_timeframe_restrictions():
    """Verify Category A contracts strictly require 1m or 5m execution timeframes."""
    with pytest.raises(Exception) as exc_info:
        ResearchExperimentContract(
            experiment_id="EXP-CAT-A-FAIL",
            experiment_name="Category A Daily Flaw",
            experiment_category=ExperimentCategory.HIGH_FREQUENCY_INTRADAY,
            execution_timeframe=ExecutionTimeframe.TF_1D,
        )
    assert "Category A (High-Frequency Intraday) requires 1m or 5m" in str(exc_info.value)

    with pytest.raises(Exception) as exc_info_1h:
        ResearchExperimentContract(
            experiment_id="EXP-CAT-A-FAIL-1H",
            experiment_name="Category A Hourly Flaw",
            experiment_category=ExperimentCategory.HIGH_FREQUENCY_INTRADAY,
            execution_timeframe=ExecutionTimeframe.TF_1H,
        )
    assert "Category A (High-Frequency Intraday) requires 1m or 5m" in str(exc_info_1h.value)


def test_holding_horizon_boundary_enforcement():
    """Verify that Category A trades exceeding 1440 minutes raise HoldingHorizonViolationError."""
    contract = ResearchExperimentContract(
        experiment_id="EXP-HORIZON-CHECK",
        experiment_name="Horizon Validation Test",
        experiment_category=ExperimentCategory.HIGH_FREQUENCY_INTRADAY,
        execution_timeframe=ExecutionTimeframe.TF_5M,
        maximum_holding_horizon_minutes=1440,
        allow_overnight_holding=False,
    )

    # Valid intraday durations (e.g. 15m, 60m, 240m)
    valid_durations = [15.0, 45.0, 120.0, 360.0, 1200.0]
    passed, msg = validate_trade_durations(contract, valid_durations)
    assert passed is True

    # Multi-day durations without overnight flag must raise error
    violating_durations = [15.0, 60.0, 2880.0]  # 2880m = 2 days
    with pytest.raises(HoldingHorizonViolationError):
        validate_trade_durations(contract, violating_durations)


def test_overnight_holding_justification_enforcement():
    """Verify that allow_overnight_holding requires a non-empty justification string."""
    with pytest.raises(ValueError):
        ResearchExperimentContract(
            experiment_id="EXP-OVERNIGHT-NO-JUST",
            experiment_name="Overnight No Justification",
            experiment_category=ExperimentCategory.SWING_MULTI_DAY,
            execution_timeframe=ExecutionTimeframe.TF_1D,
            allow_overnight_holding=True,
            overnight_holding_justification=None,
        )


def test_historical_experiment_classification_coverage():
    """Verify that all historical experiments are classified and Track C is Category C."""
    fpath = M5_10_DIR / "M5_10_HISTORICAL_EXPERIMENT_CLASSIFICATION.csv"
    df = pd.read_csv(fpath)

    # Must contain at least 15 historical experiments
    assert len(df) >= 15

    # Check Track C classification
    track_c = df[df["experiment_id"] == "Track_C_SOL_LTC_Daily"].iloc[0]
    assert track_c["experiment_category"] == "CATEGORY_C_SWING_MULTI_DAY"
    assert track_c["execution_timeframe"] == "1D"
    assert track_c["trade_count"] == 19
    assert np.isclose(float(track_c["trades_per_day"]), 0.0521, atol=0.001)

    # All 4 categories must be represented
    categories = set(df["experiment_category"].unique())
    assert "CATEGORY_A_HIGH_FREQUENCY_INTRADAY" in categories
    assert "CATEGORY_B_INTRADAY_LOW_FREQUENCY" in categories
    assert "CATEGORY_C_SWING_MULTI_DAY" in categories
    assert "CATEGORY_D_INVALID_MISCONFIGURED" in categories


def test_canonical_5m_data_readiness_and_holdout_isolation():
    """Verify that the top 10 assets possess >= 300,000 canonical 5m candles and holdout is sealed."""
    primary_assets = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT",
        "DOGEUSDT", "LINKUSDT", "LTCUSDT", "AVAXUSDT", "XRPUSDT"
    ]
    for sym in primary_assets:
        sym_dir = CANONICAL_DIR / f"symbol={sym}" / "timeframe=5m"
        assert sym_dir.exists(), f"Missing 5m directory for {sym}"
        p_files = sorted(sym_dir.glob("*.parquet"))
        assert len(p_files) >= 4, f"Expected at least 4 yearly parquet files for {sym}"

        total_candles = 0
        for f in p_files:
            tbl = pq.ParquetFile(f).read(columns=["open_time_ms"])
            ts_arr = tbl["open_time_ms"].to_numpy()
            total_candles += len(ts_arr)

            # Assert holdout partition remains virgin
            assert (ts_arr < HOLDOUT_TIMESTAMP_MS).all(), (
                f"HOLDOUT BREACH in {sym} {f.name}: max ts {ts_arr.max()} >= {HOLDOUT_TIMESTAMP_MS}"
            )

        assert total_candles >= 300_000, f"Insufficient candles for {sym}: {total_candles}"


def test_causal_timestamp_sequencing_identity():
    """Verify the causal timestamp invariant: t_bar_close < t_signal <= t_fill = t_next_bar_open."""
    # Bar i: 10:00:00 to 10:04:59.999
    t_open_i = 1700000000000
    interval_ms = 300000  # 5 minutes
    t_close_i = t_open_i + interval_ms - 1

    # Signal generated at completed bar close
    t_signal = t_open_i + interval_ms
    assert t_signal > t_close_i

    # Causal fill at next bar open
    t_fill = t_signal
    assert t_fill == t_open_i + interval_ms
    assert t_fill > t_close_i
