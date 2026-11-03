"""Centralized Research Experiment Contract & Timeframe Architecture Validator.

Enforces QUANTUM's mandatory research charter:
- 5m baseline execution timeframe (1m optional if available).
- High-frequency intraday trading style (10–100 completed trades/day target).
- Explicit experiment classification (A: HF Intraday, B: Low-Freq Intraday, C: Swing, D: Invalid).
- Zero silent timeframe downsampling or substitution.
- Strict 1.0x unlevered gross exposure cap.
"""

from enum import Enum
from typing import List, Optional, Sequence, Tuple
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

    # Horizon & Frequency Bounds
    expected_holding_horizon: str = Field(
        default="15m to 4h",
        description="Expected holding duration range for the alpha mechanism"
    )
    maximum_holding_horizon_minutes: int = Field(
        default=1440,
        gt=0,
        description="Maximum permissible holding duration in minutes (1440 = 24 hours)"
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
        description="Target range of completed trade episodes per day (e.g. 10 to 100)"
    )
    minimum_trade_frequency_daily: float = Field(
        default=1.0,
        ge=0.0,
        description="Minimum acceptable trades/day to qualify as active intraday strategy"
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

    # Microstructure & Friction Specification
    execution_model: str = Field(
        default="CAUSAL_NEXT_BAR_OPEN",
        description="Execution timing model (must be causal, point-in-time)"
    )
    fee_model: str = Field(
        default="BYBIT_VIP0_DEFAULT",
        description="Venue fee profile (Bybit VIP0 baseline: 2 bps maker, 5.5 bps taker)"
    )
    slippage_model: str = Field(
        default="STATIC_HALF_SPREAD_SLIPPAGE",
        description="Slippage model (half-spread + depth slippage)"
    )
    funding_model: str = Field(
        default="ZERO_UNAVAILABLE",
        description="Perpetual funding rate treatment"
    )

    @model_validator(mode="after")
    def validate_category_and_timeframe_coherence(self) -> "ResearchExperimentContract":
        """Asserts architectural alignment between experiment category, timeframe, and holding horizon."""
        # 1. Category A (High-Frequency Intraday) Invariants
        if self.experiment_category == ExperimentCategory.HIGH_FREQUENCY_INTRADAY:
            if self.execution_timeframe not in (ExecutionTimeframe.TF_1M, ExecutionTimeframe.TF_5M):
                raise TimeframeMismatchError(
                    f"Category A (High-Frequency Intraday) requires 1m or 5m execution timeframe, "
                    f"got {self.execution_timeframe.value}."
                )
            if self.maximum_holding_horizon_minutes > 1440 and not self.allow_overnight_holding:
                raise HoldingHorizonViolationError(
                    f"Category A cannot hold positions > 24 hours without explicit overnight justification."
                )
            if self.target_trade_frequency_daily[0] < 5.0:
                raise ValueError(
                    f"Category A target frequency lower bound must be >= 5.0 trades/day, "
                    f"got {self.target_trade_frequency_daily[0]}."
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

        return self


def validate_input_data_timeframe(contract: ResearchExperimentContract, dataset_timeframe: str) -> None:
    """Verifies that the ingested dataset strictly matches the contract's declared execution timeframe.
    
    Prevents silent downsampling (e.g. substituting 1D daily candles for a 5m contract).
    """
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
