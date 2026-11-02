"""Strict Pydantic data contracts for all 5 specialized agents."""

from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from quantum.domain.enums import (
    AgentAction,
    CandidateCategory,
    EventPriority,
    ExchangeId,
    ExecutionEventType,
    InferenceMode,
    MarketRegime,
    OrderType,
    PositionLifecycleState,
    TradeSide,
)
from quantum.domain.models import RiskDecision, ScannerCandidate, TradeProposal


class ScoutInput(BaseModel):
    """Input payload for Agent 1 (SCOUT)."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    pipeline_run_id: str = Field(min_length=1)
    candidate: ScannerCandidate


class ScoutOutput(BaseModel):
    """Output payload from Agent 1 (SCOUT)."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    action: AgentAction
    exchange: ExchangeId
    symbol: str
    directional_bias: TradeSide
    opportunity_category: CandidateCategory
    timeframe: str = "15m"
    probability_estimate: float = Field(ge=0.0, le=1.0)
    candidate_score: float = Field(ge=0.0, le=100.0)
    supporting_features: Dict[str, float] = Field(default_factory=dict)
    model_version: str = Field(min_length=1)
    inference_mode: InferenceMode
    snapshot_timestamp_ms: int = Field(gt=0)
    abort_reason: Optional[str] = None


class AnalystInput(BaseModel):
    """Input payload for Agent 2 (ANALYST)."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    pipeline_run_id: str = Field(min_length=1)
    candidate: ScannerCandidate
    scout_output: ScoutOutput


class AnalystOutput(BaseModel):
    """Output payload from Agent 2 (ANALYST)."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    action: AgentAction
    market_regime: MarketRegime
    volatility_regime: str = "NORMAL"
    directional_bias: TradeSide
    directional_probability: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    invalidation_price: float = Field(gt=0.0)
    key_support_levels: List[float] = Field(default_factory=list)
    key_resistance_levels: List[float] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    contradicting_evidence: List[str] = Field(default_factory=list)
    top_feature_contributions: Dict[str, float] = Field(default_factory=dict)
    model_version: str = Field(min_length=1)
    inference_mode: InferenceMode
    abort_reason: Optional[str] = None


class SniperInput(BaseModel):
    """Input payload for Agent 3 (SNIPER)."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    pipeline_run_id: str = Field(min_length=1)
    candidate: ScannerCandidate
    scout_output: ScoutOutput
    analyst_output: AnalystOutput


class SniperOutput(BaseModel):
    """Output payload from Agent 3 (SNIPER)."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    action: AgentAction
    exchange: ExchangeId
    symbol: str
    side: TradeSide
    order_type: OrderType
    reference_mark_price: float = Field(gt=0.0)
    entry_price: float = Field(gt=0.0)
    entry_zone_low: float = Field(gt=0.0)
    entry_zone_high: float = Field(gt=0.0)
    stop_loss: float = Field(gt=0.0)
    take_profit_1: float = Field(gt=0.0)
    take_profit_2: float = Field(gt=0.0)
    tp1_close_pct: float = Field(default=0.50, gt=0.0, le=1.0)
    estimated_reward_risk: float = Field(ge=1.50)
    expected_net_r: float
    prob_tp1_before_sl: float = Field(ge=0.0, le=1.0)
    prob_tp2_before_sl: float = Field(ge=0.0, le=1.0)
    expected_holding_minutes: int = Field(gt=0)
    rationale: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    model_version: str = Field(min_length=1)
    inference_mode: InferenceMode
    proposal: Optional[TradeProposal] = None
    abort_reason: Optional[str] = None


class RiskInput(BaseModel):
    """Input payload for Agent 4 (RISK).

    NOTE: No fabricated defaults are permitted. If equity, position counts,
    or exposure data are missing or None, RiskAgent must explicitly veto.
    """
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    pipeline_run_id: str = Field(min_length=1)
    candidate: ScannerCandidate
    proposal: TradeProposal
    current_equity_usdt: Optional[float] = None
    open_positions_count: Optional[int] = None
    total_exposure_usdt: Optional[float] = None
    peak_equity_usdt: Optional[float] = None
    daily_pnl_usdt: Optional[float] = None
    starting_day_equity_usdt: Optional[float] = None
    consecutive_losses_count: Optional[int] = None
    last_loss_timestamp_ms: Optional[int] = None
    estimated_slippage_bps: Optional[float] = None
    eval_timestamp_ms: Optional[int] = Field(default=None, description="Simulated evaluation timestamp in ms for historical replay")
    lot_step: Optional[float] = None
    min_notional_usdt: Optional[float] = None


class RiskOutput(BaseModel):
    """Output payload from Agent 4 (RISK)."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    decision: RiskDecision


class PositionExecutionEvent(BaseModel):
    """Confirmed execution event from paper or exchange execution engine."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    event_id: str = Field(min_length=1)
    position_id: str = Field(min_length=1)
    event_type: ExecutionEventType
    fill_price: float = Field(gt=0.0)
    fill_quantity: float = Field(gt=0.0)
    timestamp_ms: int = Field(gt=0)
    sequence_number: int = Field(ge=1)


class TrackedPosition(BaseModel):
    """Complete in-memory position state machine entity."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    position_id: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    side: TradeSide
    state: PositionLifecycleState = PositionLifecycleState.PENDING_OPEN
    entry_price: float = Field(gt=0.0)
    initial_quantity: float = Field(gt=0.0)
    remaining_quantity: float = Field(ge=0.0)
    current_stop_loss: float = Field(gt=0.0)
    take_profit_1: float = Field(gt=0.0)
    take_profit_2: float = Field(gt=0.0)
    tp1_target_quantity: float = Field(default=0.0, ge=0.0)
    tp1_filled_quantity: float = Field(default=0.0, ge=0.0)
    tp2_target_quantity: float = Field(default=0.0, ge=0.0)
    tp2_filled_quantity: float = Field(default=0.0, ge=0.0)
    tp1_confirmed_filled: bool = False
    tp2_confirmed_filled: bool = False
    sl_confirmed_filled: bool = False
    processed_event_ids: List[str] = Field(default_factory=list)
    last_sequence_number: int = 0
    created_at_ms: int = Field(gt=0)
    updated_at_ms: int = Field(gt=0)


class BankerInput(BaseModel):
    """Input payload for Agent 5 (BANKER)."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    position_id: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    side: TradeSide
    entry_price: float = Field(gt=0.0)
    current_mark_price: float = Field(gt=0.0)
    current_stop_loss: float = Field(gt=0.0)
    take_profit_1: float = Field(gt=0.0)
    take_profit_2: float = Field(gt=0.0)
    tp1_filled: bool = False
    unrealized_pnl_r: float = 0.0
    holding_duration_minutes: float = Field(default=0.0, ge=0.0)
    price_timestamp_ms: Optional[int] = None
    state: PositionLifecycleState = PositionLifecycleState.OPEN
    position: Optional[TrackedPosition] = None
    eval_timestamp_ms: Optional[int] = Field(default=None, description="Simulated evaluation timestamp in ms for historical replay")


class BankerOutput(BaseModel):
    """Output payload from Agent 5 (BANKER)."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    action: AgentAction
    hazard_prob: float = Field(default=0.0, ge=0.0, le=1.0)
    suggested_stop_loss: Optional[float] = None
    rationale: str = Field(min_length=1)
    is_touch_only: bool = False
    updated_position: Optional[TrackedPosition] = None
