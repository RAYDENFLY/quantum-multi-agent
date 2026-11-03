"""Declarative Strategy Configuration Schemas & Deterministic Hashing for Phase 5.6.2."""

from enum import Enum
import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field, computed_field


class StrategyFamily(str, Enum):
    """Seven core quantitative strategy families for Phase 5.6.2 discovery."""
    LIQUIDITY_MICROSTRUCTURE = "LIQUIDITY_MICROSTRUCTURE"
    MARKET_REGIME_TRANSITIONS = "MARKET_REGIME_TRANSITIONS"
    DIRECTIONAL_PREDICTION = "DIRECTIONAL_PREDICTION"
    VOLATILITY_DYNAMICS = "VOLATILITY_DYNAMICS"
    CROSS_ASSET_RELATIONSHIPS = "CROSS_ASSET_RELATIONSHIPS"
    MEAN_REVERSION_BREAKOUT = "MEAN_REVERSION_BREAKOUT"
    ADAPTIVE_ENTRY_EXECUTION = "ADAPTIVE_ENTRY_EXECUTION"


class FailureClassification(str, Enum):
    """Structured failure classification for non-qualifying strategy configurations."""
    QUALIFIED_SUCCESS = "QUALIFIED_SUCCESS"
    POSITIVE_RETURN_BELOW_TARGET = "POSITIVE_RETURN_BELOW_TARGET"
    NEGATIVE_NET_EXPECTANCY_FRICTION = "NEGATIVE_NET_EXPECTANCY_FRICTION"
    BIDIRECTIONAL_SHORT_DRAG = "BIDIRECTIONAL_SHORT_DRAG"
    LIMIT_ORDER_ADVERSE_SELECTION = "LIMIT_ORDER_ADVERSE_SELECTION"
    EXCESSIVE_DRAWDOWN_BREACH = "EXCESSIVE_DRAWDOWN_BREACH"
    INSUFFICIENT_SAMPLE_STARVATION = "INSUFFICIENT_SAMPLE_STARVATION"
    CAPITAL_MIN_NOTIONAL_STARVATION = "CAPITAL_MIN_NOTIONAL_STARVATION"
    FOLD_INSTABILITY_REGIME_MISMATCH = "FOLD_INSTABILITY_REGIME_MISMATCH"


class ExecutionPolicyMismatchError(ValueError):
    """Raised when execution policy invariants are breached (e.g. market order on passive maker tier)."""
    pass


class EntryParameters(BaseModel):
    """Declarative entry gating and microstructure conditioning parameters."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    direction_mode: str = Field(
        default="LONG_ONLY",
        description="BOTH, LONG_ONLY, SHORT_ONLY, HTF_TREND_ALIGNED, or ABSORPTION_REVERSAL",
    )
    prob_margin_min: float = Field(default=0.20, ge=0.0, le=0.95)
    p0_neutral_max: float = Field(default=0.45, ge=0.05, le=1.0)
    vol_quantile_min: float = Field(default=0.85, ge=0.0, le=0.99)
    vol_quantile_max: float = Field(default=1.00, ge=0.10, le=1.00)
    vol_expansion_ratio_min: float = Field(default=0.0, ge=0.0)
    rvol_min: float = Field(default=0.0, ge=0.0)
    taker_buy_ratio_min: float = Field(default=0.0, ge=0.0, le=1.0)
    taker_buy_ratio_max: float = Field(default=1.0, ge=0.0, le=1.0)
    wick_rejection_min: float = Field(default=0.0, ge=0.0, le=0.95)
    htf_lookback_bars: int = Field(default=12, ge=1, le=288)
    htf_return_min_bps: float = Field(default=-10000.0)
    htf_return_max_bps: float = Field(default=10000.0)
    btc_lead_lookback_bars: int = Field(default=6, ge=1, le=96)
    btc_lead_min_bps: float = Field(default=-10000.0)
    btc_lead_max_bps: float = Field(default=10000.0)
    order_type: str = Field(default="MARKET", description="MARKET or LIMIT")
    limit_offset_sigma: float = Field(default=0.0, ge=0.0, le=1.0)
    order_timeout_bars: int = Field(default=3, ge=1, le=12)
    cooldown_bars: int = Field(default=0, ge=0, le=48)
    post_only: bool = Field(default=False, description="If True, LIMIT order cancels on cross")


class ExitParameters(BaseModel):
    """Declarative exit, TP1/TP2 partial close, breakeven ratchet, and horizon parameters."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    tp1_multiplier: float = Field(default=2.0, gt=0.1, le=10.0)
    tp2_multiplier: float = Field(default=3.5, gt=0.1, le=15.0)
    tp1_close_pct: float = Field(default=0.0, ge=0.0, le=1.0)
    sl_multiplier: float = Field(default=1.2, gt=0.1, le=10.0)
    breakeven_ratchet_on_tp1: bool = Field(default=False)
    trailing_stop_distance_sigma: float = Field(default=0.0, ge=0.0, le=5.0)
    horizon_bars: int = Field(default=18, ge=3, le=96)


class RiskExecutionParameters(BaseModel):
    """Risk and $100 USD capital execution constraints."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    initial_equity_usd: float = Field(default=100.0, gt=0.0)
    risk_per_trade_pct: float = Field(default=0.015, gt=0.0, le=0.10)
    max_symbol_exposure_pct: float = Field(default=0.35, gt=0.0, le=2.0)
    max_total_exposure_pct: float = Field(default=1.00, gt=0.0, le=3.0)
    max_leverage: float = Field(default=2.0, ge=1.0, le=5.0)
    max_concurrent_positions: int = Field(default=4, ge=1, le=10)
    min_notional_usdt: float = Field(default=5.0, ge=1.0)
    fee_tier: str = Field(default="maker_passive")


class ExecutionVenueSchedule(BaseModel):
    """Declarative execution venue cost and microstructure schedule."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    venue_id: str
    exchange_name: str
    account_tier: str
    maker_fee_bps_per_leg: float
    taker_fee_bps_per_leg: float
    default_spread_bps: float
    default_slippage_bps: float
    adverse_selection_bps: float = 0.0
    funding_rate_bps_8h: float = 1.0
    provenance_doc: str
    validity_start_utc: str


VENUE_PROFILES: Dict[str, ExecutionVenueSchedule] = {
    "BYBIT_VIP0_DEFAULT": ExecutionVenueSchedule(
        venue_id="BYBIT_VIP0_DEFAULT",
        exchange_name="Bybit",
        account_tier="VIP0_Retail",
        maker_fee_bps_per_leg=2.0,
        taker_fee_bps_per_leg=5.5,
        default_spread_bps=2.0,
        default_slippage_bps=2.0,
        adverse_selection_bps=0.0,
        funding_rate_bps_8h=1.0,
        provenance_doc="Bybit Official Fee Rate Schedule, USDT Linear Perps (https://www.bybit.com/en/help-center/article/Trading-Fee-Structure)",
        validity_start_utc="2022-03-18",
    ),
    "BYBIT_VIP1": ExecutionVenueSchedule(
        venue_id="BYBIT_VIP1",
        exchange_name="Bybit",
        account_tier="VIP1",
        maker_fee_bps_per_leg=1.8,
        taker_fee_bps_per_leg=4.0,
        default_spread_bps=2.0,
        default_slippage_bps=2.0,
        adverse_selection_bps=0.0,
        funding_rate_bps_8h=1.0,
        provenance_doc="Bybit Official VIP 1 derivatives schedule (asset balance >= $50k or 30d volume >= $10M)",
        validity_start_utc="2023-01-01",
    ),
    "BYBIT_PRO3": ExecutionVenueSchedule(
        venue_id="BYBIT_PRO3",
        exchange_name="Bybit",
        account_tier="Pro3_Institutional",
        maker_fee_bps_per_leg=0.0,
        taker_fee_bps_per_leg=2.5,
        default_spread_bps=2.0,
        default_slippage_bps=2.0,
        adverse_selection_bps=0.0,
        funding_rate_bps_8h=1.0,
        provenance_doc="Bybit Institutional Pro Tier 3 (30d volume >= $100M)",
        validity_start_utc="2023-01-01",
    ),
    "ASTER_RETAIL_CORE": ExecutionVenueSchedule(
        venue_id="ASTER_RETAIL_CORE",
        exchange_name="Aster DEX",
        account_tier="Base_Tier",
        maker_fee_bps_per_leg=4.0,
        taker_fee_bps_per_leg=10.0,
        default_spread_bps=2.0,
        default_slippage_bps=2.0,
        adverse_selection_bps=0.0,
        funding_rate_bps_8h=1.0,
        provenance_doc="Aster DEX Protocol Public Specification (Phase 5.5 baseline)",
        validity_start_utc="2024-01-01",
    ),
    "ASTER_STRESS_TAKER": ExecutionVenueSchedule(
        venue_id="ASTER_STRESS_TAKER",
        exchange_name="Aster DEX",
        account_tier="Stress_Tier_3",
        maker_fee_bps_per_leg=4.0,
        taker_fee_bps_per_leg=20.0,
        default_spread_bps=2.0,
        default_slippage_bps=2.0,
        adverse_selection_bps=0.0,
        funding_rate_bps_8h=1.0,
        provenance_doc="QUANTUM Phase 5.5 Human Governance Decision Package DEC_04.7 Tier 3 Stress Specification",
        validity_start_utc="2026-11-01",
    ),
    "MAKER_PASSIVE_TRUE": ExecutionVenueSchedule(
        venue_id="MAKER_PASSIVE_TRUE",
        exchange_name="Aster DEX",
        account_tier="Passive_Maker_Only",
        maker_fee_bps_per_leg=4.0,
        taker_fee_bps_per_leg=10.0,
        default_spread_bps=0.0,
        default_slippage_bps=0.0,
        adverse_selection_bps=1.5,
        funding_rate_bps_8h=1.0,
        provenance_doc="True Passive Post-Only Schedule (8 bps RT maker fee + 1.5 bps adverse selection drag)",
        validity_start_utc="2026-11-01",
    ),
}


def get_venue_schedule(identifier: str) -> ExecutionVenueSchedule:
    """Resolve venue profile from ID or legacy fee tier alias."""
    if identifier in VENUE_PROFILES:
        return VENUE_PROFILES[identifier]

    legacy_map = {
        "maker_passive": "MAKER_PASSIVE_TRUE",
        "hybrid_tier": "BYBIT_VIP0_DEFAULT",
        "baseline_taker": "ASTER_STRESS_TAKER",
    }
    mapped = legacy_map.get(identifier.lower())
    if mapped and mapped in VENUE_PROFILES:
        return VENUE_PROFILES[mapped]

    if identifier.startswith("custom_"):
        parts = identifier.replace("custom_", "").split("_")
        f_bps = 20.0
        s_bps = 2.0
        for p in parts:
            if "fee" in p:
                try:
                    f_bps = float(p.replace("bps", "").replace("fee", "")) / 2.0
                except ValueError:
                    pass
            elif "slip" in p:
                try:
                    s_bps = float(p.replace("bps", "").replace("slip", "")) / 2.0
                except ValueError:
                    pass
        return ExecutionVenueSchedule(
            venue_id=identifier,
            exchange_name="Custom",
            account_tier="Custom",
            maker_fee_bps_per_leg=f_bps,
            taker_fee_bps_per_leg=f_bps,
            default_spread_bps=s_bps * 2.0,
            default_slippage_bps=s_bps * 2.0,
            adverse_selection_bps=0.0,
            provenance_doc=f"Custom schedule parsed from {identifier}",
            validity_start_utc="2026-11-01",
        )

    return VENUE_PROFILES["BYBIT_VIP0_DEFAULT"]


class StrategyConfiguration(BaseModel):
    """Complete, independently identifiable, hash-verified strategy configuration."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    strategy_id: str = Field(min_length=1)
    version: str = Field(default="1.0.0")
    batch_id: str = Field(min_length=1)
    family: StrategyFamily
    hypothesis: str = Field(min_length=10)
    parent_strategy_id: Optional[str] = None
    applicable_assets: Tuple[str, ...]
    timeframe: str = Field(default="5m")
    required_inputs: Tuple[str, ...] = (
        "oof_probabilities",
        "candles_5m",
        "microstructure_orderflow",
        "cross_asset_btc",
    )
    entry: EntryParameters
    exit: ExitParameters
    risk: RiskExecutionParameters

    @computed_field  # type: ignore[prop-decorator]
    @property
    def config_hash(self) -> str:
        """Deterministic SHA-256 hash of canonical strategy parameters."""
        entry_data = self.entry.model_dump()
        if not entry_data.get("post_only", False):
            entry_data.pop("post_only", None)
        payload = {
            "version": self.version,
            "family": self.family.value,
            "applicable_assets": list(self.applicable_assets),
            "timeframe": self.timeframe,
            "entry": entry_data,
            "exit": self.exit.model_dump(),
            "risk": self.risk.model_dump(),
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


class ExperimentManifest(BaseModel):
    """Immutable experiment provenance record linking audit/ and data_backtest/."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    experiment_id: str
    batch_id: str
    strategy_id: str
    strategy_version: str
    config_hash: str
    git_commit: str
    dataset_id: str = "ASTER_CANONICAL_5M_FOLDS_1_4"
    dataset_hash: str = "sha256_f14_104544bars_sealed_1793491200000"
    model_version: str = "phase_5_3_frozen_lgbm_v1"
    asset_universe: List[str]
    timeframe: str = "5m"
    evaluation_period: str = "2025-01-29T11:20:00Z to 2026-01-29T14:35:00Z (365.14 days)"
    initial_equity_usd: float = 100.0
    fee_tier: str
    round_trip_fee_bps: float
    funding_rate_bps_8h: float = 1.0
    slippage_bps: float = 0.0
    execution_model_version: str = "phase_5_6_2_micro_capital_v1"
    risk_config_summary: Dict[str, Any]
    random_seed: int = 42
    timestamp_utc: str
    result_file_ref: str
    metrics_file_ref: str
    trade_log_file_ref: str
    status: str = "VERIFIED"


class StrategyEvaluationResult(BaseModel):
    """Comprehensive evaluation metrics for a single strategy configuration."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    experiment_id: str
    batch_id: str
    strategy_id: str
    strategy_version: str
    config_hash: str
    family: StrategyFamily
    hypothesis: str
    applicable_assets: List[str]
    initial_equity_usd: float
    ending_equity_usd: float
    net_cumulative_return_pct: float
    mean_net_daily_return_pct: float
    geometric_mean_daily_return_pct: float
    median_net_daily_return_pct: float
    mean_return_per_trade_bps: float
    gross_expectancy_bps: float
    net_expectancy_bps: float
    profit_factor: float
    sharpe_annualized: float
    sortino_annualized: float
    max_drawdown_pct: float
    mean_underwater_drawdown_pct: float
    median_underwater_drawdown_pct: float
    recovery_factor: float
    candidate_signal_count: int
    executed_trade_count: int
    missed_min_notional_count: int
    missed_capacity_count: int
    execution_fill_rate_pct: float
    win_rate_pct: float
    total_fees_usd: float
    total_funding_usd: float
    total_slippage_usd: float
    total_execution_cost_usd: float
    positive_folds_count: int
    fold_returns_pct: Dict[str, float]
    per_asset_trade_counts: Dict[str, int]
    bootstrap_95_ci_daily_pct: Tuple[float, float]
    qualified: bool
    failure_classification: FailureClassification
    failure_reason: str
    raw_signal_count: int = Field(default=0)
    unique_order_count: int = Field(default=0)
    touched_order_count: int = Field(default=0)
    filled_order_count: int = Field(default=0)
    fill_event_count: int = Field(default=0)
    portfolio_execution_count: int = Field(default=0)
    diagnostic_markout_1_bps: float = Field(default=0.0)
    diagnostic_markout_3_bps: float = Field(default=0.0)
