"""Integration and Contract Enforcement Tests for Milestone 5.10A.

Covers:
1. Deliverable existence and non-emptiness.
2. Category A minimum frequency gate (strictly 10.0 completed trades/day).
3. Maximum holding duration harmonization (240m default for Category A).
4. Timeframe mismatch fail-closed enforcement (5m contract with 1D/1h input data).
5. Leverage cap enforcement (strictly unlevered <= 1.0x).
6. Explicit exchange cost configuration (AsterDEX Base Retail primary; Bybit not silent default).
7. Missing funding transparency (prohibiting false verified zero funding).
8. BTC missing candle forensic detection (1757771400000 -> 2025-09-13 13:50:00 UTC).
9. Component and agent enforcement hooks (Scout, Analyst, Sniper, Risk, Banker, Orchestrator, Feature Engine, Data Adapter, Simulator).
10. Canonical dataset holdout partition isolation (all data strictly < 1,793,491,200,000 ms).
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import pyarrow.parquet as pq

from quantum.domain.research_contract import (
    ResearchExperimentContract,
    ExperimentCategory,
    ExecutionTimeframe,
    ExchangeCostConfiguration,
    ASTER_DEX_RETAIL_CONFIG,
    ASTER_DEX_STRESS_CONFIG,
    BYBIT_VIP0_BENCHMARK_CONFIG,
    TimeframeMismatchError,
    HoldingHorizonViolationError,
    ExposureViolationError,
    FundingDataUncertaintyError,
    validate_input_data_timeframe,
    validate_trade_durations,
    validate_portfolio_gross_leverage,
    enforce_contract_on_scout,
    enforce_contract_on_analyst,
    enforce_contract_on_sniper,
    enforce_contract_on_risk,
    enforce_contract_on_banker,
    enforce_contract_on_orchestrator,
    enforce_contract_on_feature_engine,
    enforce_contract_on_data_adapter,
    enforce_contract_on_simulator,
)

ROOT = Path(__file__).resolve().parent.parent.parent
M5_10A_DIR = ROOT / "audit" / "strategy_research" / "milestone_5_10a_contract_reconciliation"
CANONICAL_DIR = ROOT / "data" / "historical" / "canonical" / "exchange=ASTER"
HOLDOUT_TIMESTAMP_MS = 1_793_491_200_000  # 2026-11-01 00:00:00 UTC


def test_m5_10a_deliverables_exist():
    """Verify all 5 Milestone 5.10A deliverables exist and are non-empty."""
    required_files = [
        "M5_10A_CONTRACT_RECONCILIATION.md",
        "M5_10A_INTEGRATION_AUDIT.md",
        "M5_10A_EXCHANGE_COST_CONFIG.csv",
        "M5_10A_DATA_INTEGRITY_REPORT.md",
        "M5_10A_UNRESOLVED_ASSUMPTIONS.md",
    ]
    for fname in required_files:
        fpath = M5_10A_DIR / fname
        assert fpath.exists(), f"Missing required file: {fname}"
        assert fpath.stat().st_size > 0, f"File is empty: {fname}"


def test_category_a_frequency_gate_enforcement():
    """Verify Category A contracts strictly enforce minimum_trade_frequency_daily >= 10.0."""
    # Valid 10.0 frequency
    contract = ResearchExperimentContract(
        experiment_id="EXP-12-VALID-FREQ",
        experiment_name="Valid HF Intraday Frequency",
        experiment_category=ExperimentCategory.HIGH_FREQUENCY_INTRADAY,
        execution_timeframe=ExecutionTimeframe.TF_5M,
        minimum_trade_frequency_daily=10.0,
    )
    assert contract.minimum_trade_frequency_daily == 10.0

    # Invalid: frequency below 10.0 must raise ValidationError containing descriptive text
    with pytest.raises(Exception) as exc_info:
        ResearchExperimentContract(
            experiment_id="EXP-12-INVALID-FREQ",
            experiment_name="Invalid Low Frequency",
            experiment_category=ExperimentCategory.HIGH_FREQUENCY_INTRADAY,
            execution_timeframe=ExecutionTimeframe.TF_5M,
            minimum_trade_frequency_daily=5.0,
        )
    assert "Category A minimum trade frequency must be strictly >= 10.0" in str(exc_info.value)


def test_holding_horizon_harmonization_and_overnight_prohibition():
    """Verify default maximum holding horizon is 240m (4h) and trades > 240m fail closed without overnight authorization."""
    contract = ResearchExperimentContract(
        experiment_id="EXP-12-HORIZON",
        experiment_name="Holding Horizon Reconciliation Test",
        experiment_category=ExperimentCategory.HIGH_FREQUENCY_INTRADAY,
        execution_timeframe=ExecutionTimeframe.TF_5M,
    )
    assert contract.maximum_holding_horizon_minutes == 240
    assert contract.allow_overnight_holding is False

    # Valid trade durations (<= 240 minutes)
    passed, msg = validate_trade_durations(contract, [15.0, 60.0, 180.0, 240.0])
    assert passed is True

    # Violating trade duration (> 240 minutes, e.g. 300 minutes = 5 hours)
    with pytest.raises(HoldingHorizonViolationError) as exc_info:
        validate_trade_durations(contract, [15.0, 120.0, 300.0])
    assert "exceeding the contract limit of 240 minutes" in str(exc_info.value)


def test_timeframe_mismatch_fails_closed():
    """Verify that passing 1D or 1h dataset to a 5m contract fails closed with TimeframeMismatchError."""
    contract = ResearchExperimentContract(
        experiment_id="EXP-12-TF-FAIL",
        experiment_name="Timeframe Mismatch Test",
        experiment_category=ExperimentCategory.HIGH_FREQUENCY_INTRADAY,
        execution_timeframe=ExecutionTimeframe.TF_5M,
    )

    # Valid 5m match
    validate_input_data_timeframe(contract, "5m")

    # Mismatches must raise TimeframeMismatchError
    with pytest.raises(TimeframeMismatchError) as exc_1d:
        validate_input_data_timeframe(contract, "1D")
    assert "CRITICAL TIMEFRAME MISMATCH" in str(exc_1d.value)

    with pytest.raises(TimeframeMismatchError) as exc_1h:
        validate_input_data_timeframe(contract, "1h")
    assert "CRITICAL TIMEFRAME MISMATCH" in str(exc_1h.value)


def test_leverage_cap_strictly_unlevered():
    """Verify that portfolio gross exposure above 1.0000x fails closed with ExposureViolationError."""
    contract = ResearchExperimentContract(
        experiment_id="EXP-12-LEVERAGE",
        experiment_name="Leverage Cap Test",
        experiment_category=ExperimentCategory.HIGH_FREQUENCY_INTRADAY,
        execution_timeframe=ExecutionTimeframe.TF_5M,
        maximum_gross_exposure=1.0000,
    )

    # Valid exposure <= 1.0x
    validate_portfolio_gross_leverage(contract, 0.9500)
    validate_portfolio_gross_leverage(contract, 1.0000)

    # Violating exposure (> 1.0x)
    with pytest.raises(ExposureViolationError) as exc_info:
        validate_portfolio_gross_leverage(contract, 1.0500)
    assert "Leverage limit breached" in str(exc_info.value)


def test_exchange_cost_config_asterdex_primary():
    """Verify AsterDEX Retail is primary target and Bybit VIP0 is strictly benchmark comparison."""
    contract = ResearchExperimentContract(
        experiment_id="EXP-12-COST",
        experiment_name="Exchange Cost Configuration Test",
        experiment_category=ExperimentCategory.HIGH_FREQUENCY_INTRADAY,
        execution_timeframe=ExecutionTimeframe.TF_5M,
    )

    # Default cost configuration must be Aster DEX Retail
    assert contract.exchange_cost_config.exchange == "Aster DEX"
    assert contract.exchange_cost_config.fee_tier == "Base_Retail_Tier"
    assert contract.exchange_cost_config.maker_fee_bps == 4.0
    assert contract.exchange_cost_config.taker_fee_bps == 10.0
    assert contract.exchange_cost_config.slippage_bps_per_leg == 2.0
    assert contract.exchange_cost_config.spread_bps_half == 1.0

    # Verify Bybit benchmark exists and has lower fees
    assert BYBIT_VIP0_BENCHMARK_CONFIG.exchange == "Bybit"
    assert BYBIT_VIP0_BENCHMARK_CONFIG.maker_fee_bps == 2.0
    assert BYBIT_VIP0_BENCHMARK_CONFIG.taker_fee_bps == 5.5


def test_funding_data_uncertainty_transparency():
    """Verify missing funding cannot be represented as 'VERIFIED_ZERO_FUNDING'."""
    # Attempting to declare missing funding as verified zero funding must fail
    with pytest.raises(Exception) as exc_info:
        ExchangeCostConfiguration(
            exchange="Aster DEX",
            fee_tier="Base_Retail_Tier",
            maker_fee_bps=4.0,
            taker_fee_bps=10.0,
            fee_source_and_verification_date="docs/test.md; Verified 2026-11-04",
            funding_data_availability="DATA_UNAVAILABLE",
            funding_uncertainty_status="VERIFIED_ZERO_FUNDING",
        )
    assert "Missing historical funding data cannot be represented as 'VERIFIED_ZERO_FUNDING'" in str(exc_info.value)

    # Correct transparent representation passes
    cfg = ExchangeCostConfiguration(
        exchange="Aster DEX",
        fee_tier="Base_Retail_Tier",
        maker_fee_bps=4.0,
        taker_fee_bps=10.0,
        fee_source_and_verification_date="docs/test.md; Verified 2026-11-04",
        funding_data_availability="DATA_UNAVAILABLE",
        funding_uncertainty_status="PARAMETRIC_BOUNDS_SENSITIVITY_REQUIRED",
        funding_sensitivity_min_bps_8h=-5.0,
        funding_sensitivity_max_bps_8h=5.0,
    )
    assert cfg.funding_uncertainty_status == "PARAMETRIC_BOUNDS_SENSITIVITY_REQUIRED"


def test_btc_missing_candle_forensic_isolation():
    """Forensically detect the exact missing BTC 5m candle at 1757771400000 (2025-09-13 13:50:00 UTC)."""
    p_btc = sorted((CANONICAL_DIR / "symbol=BTCUSDT" / "timeframe=5m").glob("*.parquet"))
    ts_btc = np.concatenate([pq.ParquetFile(f).read(columns=["open_time_ms"])["open_time_ms"].to_numpy() for f in p_btc])
    ts_btc = np.unique(ts_btc)

    assert len(ts_btc) == 316_499, f"Expected 316,499 BTC candles, got {len(ts_btc)}"

    deltas = np.diff(ts_btc)
    gap_indices = np.where(deltas > 300_000)[0]

    assert len(gap_indices) == 1, f"Expected exactly 1 internal gap in BTC, got {len(gap_indices)}"
    gap_idx = gap_indices[0]

    t_before = int(ts_btc[gap_idx])
    t_after = int(ts_btc[gap_idx + 1])
    missing_ts = t_before + 300_000

    assert missing_ts == 1_757_771_400_000, f"Expected missing timestamp 1757771400000, got {missing_ts}"
    assert deltas[gap_idx] == 600_000, f"Expected delta of 600,000 ms, got {deltas[gap_idx]}"

    missing_dt = pd.to_datetime(missing_ts, unit="ms", utc=True)
    assert str(missing_dt) == "2025-09-13 13:50:00+00:00"


def test_agent_contract_enforcement_hooks():
    """Verify all six agents and pipeline modules enforce contract constraints and fail closed."""
    contract = ResearchExperimentContract(
        experiment_id="EXP-12-AGENTS",
        experiment_name="Agent Enforcement Test",
        experiment_category=ExperimentCategory.HIGH_FREQUENCY_INTRADAY,
        execution_timeframe=ExecutionTimeframe.TF_5M,
        maximum_holding_horizon_minutes=240,
    )

    # 1. Scout Enforcement
    enforce_contract_on_scout(contract, "5m")
    enforce_contract_on_scout(contract, "15m")
    with pytest.raises(TimeframeMismatchError):
        enforce_contract_on_scout(contract, "1D")

    # 2. Analyst Enforcement (48 bars = 240m max)
    enforce_contract_on_analyst(contract, 48)
    with pytest.raises(HoldingHorizonViolationError):
        enforce_contract_on_analyst(contract, 50)

    # 3. Sniper Enforcement
    enforce_contract_on_sniper(contract, "CAUSAL_NEXT_BAR_OPEN")
    with pytest.raises(ValueError):
        enforce_contract_on_sniper(contract, "OPTIMISTIC_BAR_CLOSE")

    # 4. Risk Enforcement
    enforce_contract_on_risk(contract, 0.90)
    with pytest.raises(ExposureViolationError):
        enforce_contract_on_risk(contract, 1.10)

    # 5. Banker Enforcement
    enforce_contract_on_banker(contract, 200.0)
    with pytest.raises(HoldingHorizonViolationError):
        enforce_contract_on_banker(contract, 250.0)

    # 6. Orchestrator Enforcement
    enforce_contract_on_orchestrator(contract, "5m")
    with pytest.raises(TimeframeMismatchError):
        enforce_contract_on_orchestrator(contract, "1D")

    # 7. Feature Engine Enforcement
    enforce_contract_on_feature_engine(contract, 300_000)
    with pytest.raises(TimeframeMismatchError):
        enforce_contract_on_feature_engine(contract, 86_400_000)

    # 8. Backtest Data Adapter Enforcement
    enforce_contract_on_data_adapter(contract, "5m")
    with pytest.raises(TimeframeMismatchError):
        enforce_contract_on_data_adapter(contract, "1h")

    # 9. Simulator Enforcement
    enforce_contract_on_simulator(contract, 300_000)
    with pytest.raises(TimeframeMismatchError):
        enforce_contract_on_simulator(contract, 60_000)


def test_sealed_holdout_partition_isolation():
    """Assert all canonical parquet timestamps are strictly prior to holdout timestamp (1,793,491,200,000 ms)."""
    for symbol_dir in sorted(CANONICAL_DIR.glob("symbol=*")):
        parquet_files = sorted((symbol_dir / "timeframe=5m").glob("*.parquet"))
        assert len(parquet_files) > 0, f"No parquet files in {symbol_dir}"
        last_file = parquet_files[-1]
        last_ts = pq.ParquetFile(last_file).read(columns=["open_time_ms"])["open_time_ms"][-1].as_py()
        assert last_ts < HOLDOUT_TIMESTAMP_MS, (
            f"Holdout contamination in {symbol_dir.name}: last_ts {last_ts} >= {HOLDOUT_TIMESTAMP_MS}"
        )
