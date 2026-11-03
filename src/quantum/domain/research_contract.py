"""Centralized Research Experiment Contract & Timeframe Architecture Validator.

Enforces QUANTUM's mandatory research charter:
- 5m baseline execution timeframe (1m optional if reliable data exists).
- High-frequency intraday trading style (10–100 completed trades/day target).
- Explicit experiment classification (A: HF Intraday, B: Low-Freq Intraday, C: Swing, D: Invalid).
- Zero silent timeframe downsampling or substitution.
- Strict 1.0x unlevered gross exposure cap.
- Explicit AsterDEX-first exchange cost configuration.
- Unified 10.0 trades/day minimum frequency and 240m (4h) maximum holding horizon for Category A.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ExperimentCategory(str, Enum):
    """Rigorous classification of QUANTUM research experiments."""
    HIGH_FREQUENCY_INTRADAY = "CATEGORY_A_HIGH_FREQUENCY_INTRADAY"
    INTRADAY_LOW_FREQUENCY = "CATEGORY_B_INTRADAY_LOW_FREQUENCY"
    SWING_MULTI_DAY = "CATEGORY_C_SWING_MULTI_DAY"
    INVALID_MISCONFIGURED = "CATEGORY_D_INVALID_MISCONFIGURED"


class ExecutionTimeframe(str, Enum):
    """Permitted execution timeframes."""
    TF_1M = "1m"
    TF_5M = "5m"
    TF_15M = "15m"
    TF_1H = "1h"
    TF_1D = "1D"


class TimeframeMismatchError(ValueError):
    """Raised when data timeframe deviates from declared contract execution timeframe."""
    pass


class HoldingHorizonViolationError(ValueError):
    """Raised when holding duration violates the declared intraday contract boundary."""
    pass


class ExposureViolationError(ValueError):
    """Raised when gross exposure exceeds the strictly unlevered 1.0x limit."""
    pass


class FundingDataUncertaintyError(ValueError):
    """Raised when missing funding data is improperly represented as verified zero funding."""
    pass


class ExchangeCostConfiguration(BaseModel):
    """Explicit exchange-specific transaction cost and microstructure schedule."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    exchange: str = Field(description="Target exchange identifier (e.g. 'Aster DEX', 'Bybit')")
    contract_type: str = Field(default="USDT Perpetual Linear Futures")
    fee_tier: str = Field(description="Account fee tier (e.g. 'Base_Retail_Tier', 'VIP0_Retail')")
    maker_fee_bps: float = Field(ge=0.0, description="Maker fee rate in basis points per leg")
    taker_fee_bps: float = Field(ge=0.0, description="Taker fee rate in basis points per leg")
    fee_source_and_verification_date: str = Field(
        min_length=10,
        description="Authoritative documentation source and verification date (YYYY-MM-DD)"
    )
    spread_model: str = Field(default="STATIC_HALF_SPREAD_1_BPS")
    spread_bps_half: float = Field(default=1.0, ge=0.0, description="Half-spread in bps per leg")
    slippage_model: str = Field(default="STATIC_LINEAR_SLIPPAGE")
    slippage_bps_per_leg: float = Field(default=2.0, ge=0.0, description="Execution slippage in bps per leg")
    funding_data_availability: str = Field(
        default="DATA_UNAVAILABLE",
        description="'DATA_AVAILABLE' or 'DATA_UNAVAILABLE'"
    )
    funding_uncertainty_status: str = Field(
        default="PARAMETRIC_BOUNDS_SENSITIVITY_REQUIRED",
        description="Formal status of funding data uncertainty"
    )
    funding_sensitivity_min_bps_8h: float = Field(default=-5.0, description="Sensitivity lower bound in bps/8h")
    funding_sensitivity_max_bps_8h: float = Field(default=5.0, description="Sensitivity upper bound in bps/8h")

    @model_validator(mode="after")
    def validate_funding_transparency(self) -> "ExchangeCostConfiguration":
        """Ensures missing funding data cannot be represented as verified zero funding."""
        if self.funding_data_availability == "DATA_UNAVAILABLE":
            if "ZERO" in self.funding_uncertainty_status.upper() and "VERIFIED" in self.funding_uncertainty_status.upper():
                raise FundingDataUncertaintyError(
                    "Missing historical funding data cannot be represented as 'VERIFIED_ZERO_FUNDING'. "
                    "Must be labeled 'PARAMETRIC_BOUNDS_SENSITIVITY_REQUIRED'."
                )
        return self


# Authoritative Pre-configured Exchange Profiles
ASTER_DEX_RETAIL_CONFIG = ExchangeCostConfiguration(
    exchange="Aster DEX",
    contract_type="USDT Perpetual Linear Futures",
    fee_tier="Base_Retail_Tier",
    maker_fee_bps=4.0,
    taker_fee_bps=10.0,
    fee_source_and_verification_date="docs/ASTERDEX_MARKET_DATA.md; Verified 2026-11-04",
    spread_model="STATIC_HALF_SPREAD_1_BPS",
    spread_bps_half=1.0,
    slippage_model="STATIC_LINEAR_SLIPPAGE",
    slippage_bps_per_leg=2.0,
    funding_data_availability="DATA_UNAVAILABLE",
    funding_uncertainty_status="PARAMETRIC_BOUNDS_SENSITIVITY_REQUIRED",
    funding_sensitivity_min_bps_8h=-5.0,
    funding_sensitivity_max_bps_8h=5.0,
)

ASTER_DEX_STRESS_CONFIG = ExchangeCostConfiguration(
    exchange="Aster DEX",
    contract_type="USDT Perpetual Linear Futures",
    fee_tier="Stress_Tier_3",
    maker_fee_bps=4.0,
    taker_fee_bps=20.0,
    fee_source_and_verification_date="Phase 5.5 DEC_04.7 Stress Specification; Verified 2026-11-04",
    spread_model="STATIC_HALF_SPREAD_1_BPS",
    spread_bps_half=1.0,
    slippage_model="STATIC_LINEAR_SLIPPAGE",
    slippage_bps_per_leg=2.0,
    funding_data_availability="DATA_UNAVAILABLE",
    funding_uncertainty_status="PARAMETRIC_BOUNDS_SENSITIVITY_REQUIRED",
    funding_sensitivity_min_bps_8h=-10.0,
    funding_sensitivity_max_bps_8h=10.0,
)

BYBIT_VIP0_BENCHMARK_CONFIG = ExchangeCostConfiguration(
    exchange="Bybit",
    contract_type="USDT Perpetual Linear Futures",
    fee_tier="VIP0_Retail",
    maker_fee_bps=2.0,
    taker_fee_bps=5.5,
    fee_source_and_verification_date="https://www.bybit.com/en/help-center/article/Trading-Fee-Structure; Verified 2026-11-04",
    spread_model="STATIC_HALF_SPREAD_1_BPS",
    spread_bps_half=1.0,
    slippage_model="STATIC_LINEAR_SLIPPAGE",
    slippage_bps_per_leg=1.5,
    funding_data_availability="DATA_UNAVAILABLE",
    funding_uncertainty_status="PARAMETRIC_BOUNDS_SENSITIVITY_REQUIRED",
    funding_sensitivity_min_bps_8h=-5.0,
    funding_sensitivity_max_bps_8h=5.0,
)


class ResearchExperimentContract(BaseModel):
    """Mandatory contract that must be declared and validated prior to backtest execution."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    # Experiment Identification
    experiment_id: str = Field(min_length=1, description="Unique experiment identifier (e.g. EXP-12)")
    experiment_name: str = Field(min_length=3, description="Descriptive human-readable experiment name")
    experiment_category: ExperimentCategory = Field(
        description="Mandatory category (A: HF Intraday, B: LF Intraday, C: Swing, D: Invalid)"
    )

    # Timeframe Architecture
    execution_timeframe: ExecutionTimeframe = Field(
        default=ExecutionTimeframe.TF_5M,
        description="Primary execution resolution (baseline: 5m, optional: 1m)"
    )
    context_timeframes: Tuple[ExecutionTimeframe, ...] = Field(
        default=(ExecutionTimeframe.TF_15M, ExecutionTimeframe.TF_1H),
        description="Multi-timeframe confirmation and regime context resolutions"
    )

    # Horizon & Frequency Bounds (Reconciled: Target 10-100, Min 10.0 for Cat A, Max Holding 240m)
    expected_holding_horizon: str = Field(
        default="15m to 4h",
        description="Expected holding duration range for the alpha mechanism"
    )
    maximum_holding_horizon_minutes: int = Field(
        default=240,
        gt=0,
        description="Maximum permissible holding duration in minutes (default 240m = 4 hours)"
    )
    allow_overnight_holding: bool = Field(
        default=False,
        description="Whether holding positions across 00:00 UTC day boundary is permitted"
    )
    overnight_holding_justification: Optional[str] = Field(
        default=None,
        description="Mandatory justification if allow_overnight_holding is True"
    )

    target_trade_frequency_daily: Tuple[float, float] = Field(
        default=(10.0, 100.0),
        description="Target range of completed trade episodes per day (10 to 100)"
    )
    minimum_trade_frequency_daily: float = Field(
        default=10.0,
        ge=0.0,
        description="Authoritative minimum completed trade episodes/day (strictly 10.0 for Category A)"
    )

    # Portfolio Sizing & Exposure Hard Caps
    maximum_concurrent_positions: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Maximum number of simultaneous open positions"
    )
    maximum_symbol_weight: float = Field(
        default=0.25,
        gt=0.0,
        le=1.0,
        description="Maximum capital allocation to a single asset"
    )
    maximum_gross_exposure: float = Field(
        default=1.0000,
        ge=0.1,
        le=1.0000,
        description="Strictly unlevered portfolio exposure hard cap"
    )
    initial_equity_usd: float = Field(
        default=100.0,
        gt=0.0,
        description="Standardized research capital base ($100.00 USD)"
    )
    mandatory_profitability_gate_daily_pct: float = Field(
        default=3.0000,
        description="Non-negotiable mean net daily return target (>= 3.0000%)"
    )

    # Microstructure & Friction Specification (AsterDEX Primary Target)
    execution_model: str = Field(
        default="CAUSAL_NEXT_BAR_OPEN",
        description="Execution timing model (must be causal, point-in-time)"
    )
    exchange_cost_config: ExchangeCostConfiguration = Field(
        default=ASTER_DEX_RETAIL_CONFIG,
        description="Authoritative exchange cost configuration (AsterDEX Retail primary)"
    )

    @model_validator(mode="after")
    def validate_contract_invariants(self) -> "ResearchExperimentContract":
        """Asserts strict architectural coherence across parameters."""
        # 1. Category A (High-Frequency Intraday) Invariants
        if self.experiment_category == ExperimentCategory.HIGH_FREQUENCY_INTRADAY:
            if self.execution_timeframe not in (ExecutionTimeframe.TF_1M, ExecutionTimeframe.TF_5M):
                raise TimeframeMismatchError(
                    f"Category A (High-Frequency Intraday) requires 1m or 5m execution timeframe, "
                    f"got {self.execution_timeframe.value}."
                )
            if self.minimum_trade_frequency_daily < 10.0:
                raise ValueError(
                    f"Category A minimum trade frequency must be strictly >= 10.0 completed trade episodes/day, "
                    f"got {self.minimum_trade_frequency_daily}."
                )
            if self.maximum_holding_horizon_minutes > 240 and not self.allow_overnight_holding:
                raise HoldingHorizonViolationError(
                    f"Category A maximum holding horizon cannot exceed 240 minutes (4 hours) without "
                    f"explicit overnight authorization. Got {self.maximum_holding_horizon_minutes} minutes."
                )

        # 2. Category C (Swing / Multi-Day) Restrictions
        if self.experiment_category == ExperimentCategory.SWING_MULTI_DAY:
            if not self.allow_overnight_holding:
                raise ValueError("Category C (Swing / Multi-Day) must set allow_overnight_holding=True.")

        # 3. Overnight Holding Justification Enforcement
        if self.allow_overnight_holding and not self.overnight_holding_justification:
            raise ValueError(
                "When allow_overnight_holding is True, overnight_holding_justification must be provided."
            )

        # 4. Exposure Cap Enforcement
        if self.maximum_gross_exposure > 1.00000:
            raise ExposureViolationError(
                f"Gross exposure cap cannot exceed 1.0000x (unlevered), got {self.maximum_gross_exposure}."
            )

        # 5. Primary Target Enforcement
        if not self.exchange_cost_config.exchange:
            raise ValueError("Exchange cost configuration must specify exchange identifier.")

        return self


# ==============================================================================
# PIPELINE INTEGRATION ENFORCEMENT HOOKS
# ==============================================================================

def validate_input_data_timeframe(contract: ResearchExperimentContract, dataset_timeframe: str) -> None:
    """Verifies that the ingested dataset strictly matches the contract's declared execution timeframe."""
    clean_tf = dataset_timeframe.strip().lower()
    expected_tf = contract.execution_timeframe.value.strip().lower()

    if clean_tf != expected_tf:
        raise TimeframeMismatchError(
            f"CRITICAL TIMEFRAME MISMATCH: Contract '{contract.experiment_id}' declared "
            f"execution_timeframe='{contract.execution_timeframe.value}', but received data "
            f"with timeframe='{dataset_timeframe}'. Silent timeframe substitution is strictly prohibited."
        )


def validate_trade_durations(
    contract: ResearchExperimentContract,
    holding_durations_minutes: Sequence[float]
) -> Tuple[bool, str]:
    """Validates that realized trade holding durations comply with contract horizon boundaries."""
    if not holding_durations_minutes:
        return True, "No trades to validate."

    max_dur = max(holding_durations_minutes)
    mean_dur = sum(holding_durations_minutes) / len(holding_durations_minutes)

    if contract.experiment_category == ExperimentCategory.HIGH_FREQUENCY_INTRADAY:
        if max_dur > contract.maximum_holding_horizon_minutes and not contract.allow_overnight_holding:
            raise HoldingHorizonViolationError(
                f"Holding duration violation in '{contract.experiment_id}': Maximum observed duration "
                f"was {max_dur:.1f} minutes ({max_dur/60:.2f} hours), exceeding the contract limit of "
                f"{contract.maximum_holding_horizon_minutes} minutes without overnight authorization."
            )

    return True, f"Durations validated: Mean={mean_dur:.1f}m, Max={max_dur:.1f}m."


def validate_portfolio_gross_leverage(
    contract: ResearchExperimentContract,
    observed_peak_leverage: float
) -> None:
    """Asserts that portfolio gross exposure never breached the contract limit."""
    if observed_peak_leverage > contract.maximum_gross_exposure + 1e-4:
        raise ExposureViolationError(
            f"Leverage limit breached in '{contract.experiment_id}': Peak observed gross leverage "
            f"{observed_peak_leverage:.4f}x exceeds contract limit of {contract.maximum_gross_exposure:.4f}x."
        )


# Agent & Component Enforcement Hooks
def enforce_contract_on_scout(contract: ResearchExperimentContract, candidate_timeframe: str) -> None:
    """Ensures Scout scans only timeframes approved by the contract."""
    allowed = [contract.execution_timeframe.value] + [tf.value for tf in contract.context_timeframes]
    if candidate_timeframe not in allowed:
        raise TimeframeMismatchError(
            f"SCOUT ENFORCEMENT FAILURE: Scout candidate timeframe '{candidate_timeframe}' "
            f"not permitted by contract '{contract.experiment_id}'. Permitted: {allowed}."
        )


def enforce_contract_on_analyst(contract: ResearchExperimentContract, forecast_horizon_bars: int) -> None:
    """Ensures Analyst forecast horizon aligns with expected holding horizon."""
    max_bars = int(contract.maximum_holding_horizon_minutes / 5)  # for 5m
    if forecast_horizon_bars > max_bars and not contract.allow_overnight_holding:
        raise HoldingHorizonViolationError(
            f"ANALYST ENFORCEMENT FAILURE: Forecast horizon {forecast_horizon_bars} bars exceeds "
            f"contract max of {max_bars} bars."
        )


def enforce_contract_on_sniper(contract: ResearchExperimentContract, order_execution_model: str) -> None:
    """Ensures Sniper executes causally at next-bar open."""
    if order_execution_model != contract.execution_model:
        raise ValueError(
            f"SNIPER ENFORCEMENT FAILURE: Order execution model '{order_execution_model}' "
            f"does not match contract model '{contract.execution_model}'."
        )


def enforce_contract_on_risk(contract: ResearchExperimentContract, aggregate_gross_exposure: float) -> None:
    """Ensures Risk Agent hard-caps portfolio leverage at <= 1.0x."""
    validate_portfolio_gross_leverage(contract, aggregate_gross_exposure)


def enforce_contract_on_banker(contract: ResearchExperimentContract, trade_duration_minutes: float) -> None:
    """Ensures Banker audits trade durations against contract max holding horizon."""
    if trade_duration_minutes > contract.maximum_holding_horizon_minutes and not contract.allow_overnight_holding:
        raise HoldingHorizonViolationError(
            f"BANKER ENFORCEMENT FAILURE: Trade duration {trade_duration_minutes:.1f}m exceeds "
            f"contract limit {contract.maximum_holding_horizon_minutes}m."
        )


def enforce_contract_on_orchestrator(contract: ResearchExperimentContract, pipeline_timeframe: str) -> None:
    """Ensures Orchestrator validates pipeline execution timeframe before triggering agents."""
    validate_input_data_timeframe(contract, pipeline_timeframe)


def enforce_contract_on_feature_engine(contract: ResearchExperimentContract, base_candle_delta_ms: int) -> None:
    """Ensures Feature Engine receives un-downsampled 5m base candles."""
    expected_delta_ms = 300_000 if contract.execution_timeframe == ExecutionTimeframe.TF_5M else 60_000
    if base_candle_delta_ms != expected_delta_ms:
        raise TimeframeMismatchError(
            f"FEATURE ENGINE ENFORCEMENT FAILURE: Base candle delta {base_candle_delta_ms} ms "
            f"does not match contract expected delta {expected_delta_ms} ms."
        )


def enforce_contract_on_data_adapter(contract: ResearchExperimentContract, dataset_timeframe: str) -> None:
    """Ensures Data Adapter fails closed on silent downsampling."""
    validate_input_data_timeframe(contract, dataset_timeframe)


def enforce_contract_on_simulator(contract: ResearchExperimentContract, simulator_step_ms: int) -> None:
    """Ensures Discrete Event Simulator steps at the exact contract execution interval."""
    expected_step_ms = 300_000 if contract.execution_timeframe == ExecutionTimeframe.TF_5M else 60_000
    if simulator_step_ms != expected_step_ms:
        raise TimeframeMismatchError(
            f"SIMULATOR ENFORCEMENT FAILURE: Simulator step {simulator_step_ms} ms does not "
            f"match contract expected interval {expected_step_ms} ms."
        )
