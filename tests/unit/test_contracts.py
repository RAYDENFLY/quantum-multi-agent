"""Unit tests for Pydantic domain models and inter-agent contracts."""

import pytest
from pydantic import ValidationError

from quantum.domain.enums import (
    CandidateCategory,
    ExchangeId,
    MarketRegime,
    OrderType,
    TradeSide,
)
from quantum.domain.models import (
    MarketContext,
    RiskDecision,
    ScannerCandidate,
    TradeProposal,
)


def sample_context() -> MarketContext:
    return MarketContext(
        exchange=ExchangeId.BYBIT,
        symbol="BTCUSDT",
        snapshot_timestamp_ms=1700000000000,
        last_price=65000.0,
        mark_price=65005.0,
        index_price=65000.0,
        bid1_price=64998.0,
        ask1_price=65002.0,
        spread_bps=0.6,
        turnover_24h_usdt=500_000_000.0,
        price_change_24h_pct=2.5,
        funding_rate=0.0001,
        next_funding_time_ms=1700028800000,
        atr_15m=250.0,
        atr_1h=450.0,
        rvol_15m=1.85,
        rsi_15m=58.5,
        features={"wick_trap_ratio": 0.12, "log_turnover_24h": 20.03},
    )


def test_market_context_validation() -> None:
    ctx = sample_context()
    assert ctx.symbol == "BTCUSDT"
    assert ctx.last_price == 65000.0

    # Negative price validation
    with pytest.raises(ValidationError):
        data = ctx.model_dump()
        data["last_price"] = -10.0
        MarketContext(**data)

    # Negative spread validation
    with pytest.raises(ValidationError):
        data = ctx.model_dump()
        data["spread_bps"] = -1.0
        MarketContext(**data)


def test_scanner_candidate_validation() -> None:
    ctx = sample_context()
    cand = ScannerCandidate(
        candidate_id="cand_btc_1",
        scan_cycle_id="cycle_1",
        exchange=ExchangeId.BYBIT,
        symbol="BTCUSDT",
        directional_bias=TradeSide.LONG,
        primary_category=CandidateCategory.MOMENTUM_ACCELERATION,
        deterministic_score=78.5,
        state_hash="a" * 16,
        context=ctx,
        created_at_ms=1700000000000,
        expires_at_ms=1700000060000,
    )
    assert cand.deterministic_score == 78.5

    # Score above 100
    with pytest.raises(ValidationError):
        data = cand.model_dump()
        data["deterministic_score"] = 105.0
        ScannerCandidate(**data)

    # Score below 0
    with pytest.raises(ValidationError):
        data = cand.model_dump()
        data["deterministic_score"] = -5.0
        ScannerCandidate(**data)

    # Expiration before creation
    with pytest.raises(ValidationError, match="expires_at_ms must be greater than or equal to created_at_ms"):
        data = cand.model_dump()
        data["expires_at_ms"] = 1699999999000
        ScannerCandidate(**data)


def test_trade_proposal_long_geometry_validation() -> None:
    # Valid LONG: stop_loss < entry < tp1 < tp2
    prop = TradeProposal(
        proposal_id="prop_1",
        pipeline_run_id="run_1",
        exchange=ExchangeId.BYBIT,
        symbol="BTCUSDT",
        side=TradeSide.LONG,
        order_type=OrderType.LIMIT,
        reference_mark_price=65000.0,
        entry_price=65000.0,
        entry_zone_low=64950.0,
        entry_zone_high=65020.0,
        stop_loss=64500.0,
        take_profit_1=66000.0,
        take_profit_2=66800.0,
        tp1_close_pct=0.5,
        estimated_reward_risk=2.0,
        expected_net_r=0.45,
        prob_tp1_before_sl=0.62,
        prob_tp2_before_sl=0.45,
        expected_holding_minutes=120,
        rationale="Valid long proposal",
        market_regime=MarketRegime.TREND_IMPULSE,
        invalidation_price=64500.0,
        sniper_model_version="rule_baseline_v1",
        created_at_ms=1700000000000,
    )
    assert prop.entry_price == 65000.0

    # Invalid LONG: stop_loss >= entry_price
    with pytest.raises(ValidationError, match="Invalid LONG geometry"):
        TradeProposal(
            proposal_id="prop_bad_sl",
            pipeline_run_id="run_1",
            exchange=ExchangeId.BYBIT,
            symbol="BTCUSDT",
            side=TradeSide.LONG,
            order_type=OrderType.LIMIT,
            reference_mark_price=65000.0,
            entry_price=65000.0,
            entry_zone_low=64950.0,
            entry_zone_high=65020.0,
            stop_loss=65100.0,  # Invalid!
            take_profit_1=66000.0,
            take_profit_2=66800.0,
            tp1_close_pct=0.5,
            estimated_reward_risk=2.0,
            expected_net_r=0.45,
            prob_tp1_before_sl=0.62,
            prob_tp2_before_sl=0.45,
            expected_holding_minutes=120,
            rationale="Invalid long stop",
            market_regime=MarketRegime.TREND_IMPULSE,
            invalidation_price=64500.0,
            sniper_model_version="rule_baseline_v1",
            created_at_ms=1700000000000,
        )

    # Invalid LONG: take_profit_1 <= entry_price
    with pytest.raises(ValidationError, match="Invalid LONG geometry"):
        TradeProposal(
            proposal_id="prop_bad_tp",
            pipeline_run_id="run_1",
            exchange=ExchangeId.BYBIT,
            symbol="BTCUSDT",
            side=TradeSide.LONG,
            order_type=OrderType.LIMIT,
            reference_mark_price=65000.0,
            entry_price=65000.0,
            entry_zone_low=64950.0,
            entry_zone_high=65020.0,
            stop_loss=64500.0,
            take_profit_1=64900.0,  # Invalid!
            take_profit_2=66800.0,
            tp1_close_pct=0.5,
            estimated_reward_risk=2.0,
            expected_net_r=0.45,
            prob_tp1_before_sl=0.62,
            prob_tp2_before_sl=0.45,
            expected_holding_minutes=120,
            rationale="Invalid long tp",
            market_regime=MarketRegime.TREND_IMPULSE,
            invalidation_price=64500.0,
            sniper_model_version="rule_baseline_v1",
            created_at_ms=1700000000000,
        )


def test_trade_proposal_short_geometry_validation() -> None:
    # Valid SHORT: stop_loss > entry > tp1 > tp2
    prop = TradeProposal(
        proposal_id="prop_short",
        pipeline_run_id="run_1",
        exchange=ExchangeId.BYBIT,
        symbol="BTCUSDT",
        side=TradeSide.SHORT,
        order_type=OrderType.LIMIT,
        reference_mark_price=65000.0,
        entry_price=65000.0,
        entry_zone_low=64980.0,
        entry_zone_high=65050.0,
        stop_loss=65500.0,
        take_profit_1=64000.0,
        take_profit_2=63200.0,
        tp1_close_pct=0.5,
        estimated_reward_risk=2.0,
        expected_net_r=0.45,
        prob_tp1_before_sl=0.62,
        prob_tp2_before_sl=0.45,
        expected_holding_minutes=120,
        rationale="Valid short proposal",
        market_regime=MarketRegime.TREND_IMPULSE,
        invalidation_price=65500.0,
        sniper_model_version="rule_baseline_v1",
        created_at_ms=1700000000000,
    )
    assert prop.stop_loss == 65500.0

    # Invalid SHORT: stop_loss <= entry_price
    with pytest.raises(ValidationError, match="Invalid SHORT geometry"):
        TradeProposal(
            proposal_id="prop_bad_short_sl",
            pipeline_run_id="run_1",
            exchange=ExchangeId.BYBIT,
            symbol="BTCUSDT",
            side=TradeSide.SHORT,
            order_type=OrderType.LIMIT,
            reference_mark_price=65000.0,
            entry_price=65000.0,
            entry_zone_low=64980.0,
            entry_zone_high=65050.0,
            stop_loss=64500.0,  # Invalid!
            take_profit_1=64000.0,
            take_profit_2=63200.0,
            tp1_close_pct=0.5,
            estimated_reward_risk=2.0,
            expected_net_r=0.45,
            prob_tp1_before_sl=0.62,
            prob_tp2_before_sl=0.45,
            expected_holding_minutes=120,
            rationale="Invalid short stop",
            market_regime=MarketRegime.TREND_IMPULSE,
            invalidation_price=65500.0,
            sniper_model_version="rule_baseline_v1",
            created_at_ms=1700000000000,
        )


def test_immutability_and_serialization() -> None:
    ctx = sample_context()

    # Immutable: assignment raises error
    with pytest.raises(ValidationError):
        ctx.last_price = 70000.0

    # Roundtrip serialization
    json_str = ctx.model_dump_json()
    ctx_recovered = MarketContext.model_validate_json(json_str)
    assert ctx_recovered == ctx
