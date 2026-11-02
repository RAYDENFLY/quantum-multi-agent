"""Unit tests for Simulated Clock Injection in RiskAgent and BankerAgent.

Verifies:
1. Historical fresh signal passes Gate 1 with simulated clock.
2. Historical stale signal is vetoed when age > 15,000 ms.
3. Future timestamp is vetoed with VETO_FUTURE_TIMESTAMP.
4. Loss streak cooldown boundary behaves deterministically under simulated time.
5. Deterministic replay produces identical decision outputs.
6. BankerAgent stale price monitoring uses simulated clock.
"""

import pytest

from quantum.agents.banker import BankerAgent
from quantum.agents.contracts import BankerInput, RiskInput
from quantum.agents.risk import RiskAgent
from quantum.config.settings import RiskConfig
from quantum.domain.enums import (
    AgentAction,
    CandidateCategory,
    ExchangeId,
    MarketRegime,
    OrderType,
    TradeSide,
)
from quantum.domain.models import MarketContext, ScannerCandidate, TradeProposal


@pytest.fixture
def risk_agent() -> RiskAgent:
    config = RiskConfig(
        max_spread_bps=10.0,
        max_estimated_slippage_bps=10.0,
        min_net_reward_risk=1.5,
        min_notional_usdt=10.0,
        max_notional_usdt=50000.0,
        max_leverage_per_position=5.0,
        loss_streak_cooldown_count=3,
        per_symbol_loss_cooldown_min=30,
    )
    return RiskAgent(config)


@pytest.fixture
def base_candidate_and_proposal():
    ts_hist = 1704067200000  # 2024-01-01 00:00:00 UTC
    context = MarketContext(
        symbol="BTCUSDT",
        exchange=ExchangeId.ASTER,
        snapshot_timestamp_ms=ts_hist,
        last_price=50000.0,
        mark_price=50000.0,
        index_price=50000.0,
        bid1_price=49999.0,
        ask1_price=50001.0,
        spread_bps=0.4,
        turnover_24h_usdt=500_000_000.0,
        price_change_24h_pct=2.5,
        funding_rate=0.0001,
        next_funding_time_ms=ts_hist + 28800000,
        atr_15m=500.0,
        atr_1h=750.0,
        rsi_15m=50.0,
        rvol_15m=1.0,
        features={"wick_trap_ratio": 0.12},
    )
    candidate = ScannerCandidate(
        candidate_id="cand_hist_1",
        scan_cycle_id="cycle_hist_1",
        symbol="BTCUSDT",
        exchange=ExchangeId.ASTER,
        directional_bias=TradeSide.LONG,
        primary_category=CandidateCategory.MOMENTUM_ACCELERATION,
        deterministic_score=85.0,
        state_hash="a" * 16,
        context=context,
        created_at_ms=ts_hist,
        expires_at_ms=ts_hist + 60000,
    )
    proposal = TradeProposal(
        proposal_id="prop_hist_1",
        pipeline_run_id="pipe_hist_1",
        exchange=ExchangeId.ASTER,
        symbol="BTCUSDT",
        side=TradeSide.LONG,
        order_type=OrderType.LIMIT,
        reference_mark_price=50000.0,
        entry_price=50000.0,
        entry_zone_low=49800.0,
        entry_zone_high=50200.0,
        stop_loss=49000.0,  # 1000 stop distance = 2 ATR
        take_profit_1=52000.0,
        take_profit_2=54000.0,
        tp1_close_pct=0.5,
        estimated_reward_risk=2.0,
        expected_net_r=1.8,
        prob_tp1_before_sl=0.6,
        prob_tp2_before_sl=0.4,
        expected_holding_minutes=60,
        rationale="Historical test proposal",
        market_regime=MarketRegime.TREND_IMPULSE,
        invalidation_price=49000.0,
        sniper_model_version="rule_baseline_v1",
        created_at_ms=ts_hist,
    )
    return candidate, proposal, ts_hist


@pytest.mark.asyncio
async def test_historical_fresh_signal(risk_agent, base_candidate_and_proposal):
    """Historical signal with matching eval_timestamp_ms passes Gate 1 freshness."""
    candidate, proposal, ts_hist = base_candidate_and_proposal

    risk_input = RiskInput(
        pipeline_run_id="pipe_hist_1",
        candidate=candidate,
        proposal=proposal,
        current_equity_usdt=10000.0,
        open_positions_count=0,
        total_exposure_usdt=0.0,
        eval_timestamp_ms=ts_hist,  # Exactly aligned to historical candle
    )

    output = await risk_agent.evaluate(risk_input)
    assert output.decision.decision == AgentAction.APPROVED
    assert "SIGNAL_FRESHNESS" in output.decision.checks_passed
    assert output.decision.evaluated_at_ms == ts_hist


@pytest.mark.asyncio
async def test_historical_stale_signal(risk_agent, base_candidate_and_proposal):
    """Historical signal older than 15s relative to eval_timestamp_ms is vetoed."""
    candidate, proposal, ts_hist = base_candidate_and_proposal

    # Snapshot is 20s older than simulated evaluation time
    eval_ts = ts_hist + 20_000

    risk_input = RiskInput(
        pipeline_run_id="pipe_hist_1",
        candidate=candidate,
        proposal=proposal,
        current_equity_usdt=10000.0,
        open_positions_count=0,
        total_exposure_usdt=0.0,
        eval_timestamp_ms=eval_ts,
    )

    output = await risk_agent.evaluate(risk_input)
    assert output.decision.decision == AgentAction.REJECTED
    assert any("VETO_STALE_SIGNAL" in r for r in output.decision.veto_reasons)


@pytest.mark.asyncio
async def test_future_timestamp_rejection(risk_agent, base_candidate_and_proposal):
    """Snapshot timestamp in the future relative to eval_timestamp_ms is vetoed."""
    candidate, proposal, ts_hist = base_candidate_and_proposal

    # Eval timestamp is in the past relative to snapshot
    eval_ts = ts_hist - 5_000

    risk_input = RiskInput(
        pipeline_run_id="pipe_hist_1",
        candidate=candidate,
        proposal=proposal,
        current_equity_usdt=10000.0,
        open_positions_count=0,
        total_exposure_usdt=0.0,
        eval_timestamp_ms=eval_ts,
    )

    output = await risk_agent.evaluate(risk_input)
    assert output.decision.decision == AgentAction.REJECTED
    assert any("VETO_FUTURE_TIMESTAMP" in r for r in output.decision.veto_reasons)


@pytest.mark.asyncio
async def test_cooldown_boundary_simulated_time(risk_agent, base_candidate_and_proposal):
    """Cooldown is evaluated strictly against simulated eval_timestamp_ms."""
    candidate, proposal, ts_hist = base_candidate_and_proposal

    # Case A: Active cooldown (10 minutes elapsed < 30 minutes)
    risk_input_active = RiskInput(
        pipeline_run_id="pipe_hist_1",
        candidate=candidate,
        proposal=proposal,
        current_equity_usdt=10000.0,
        open_positions_count=0,
        total_exposure_usdt=0.0,
        consecutive_losses_count=3,
        last_loss_timestamp_ms=ts_hist - (10 * 60 * 1000),
        eval_timestamp_ms=ts_hist,
    )
    out_active = await risk_agent.evaluate(risk_input_active)
    assert out_active.decision.decision == AgentAction.REJECTED
    assert any("VETO_LOSS_STREAK_COOLDOWN" in r for r in out_active.decision.veto_reasons)

    # Case B: Expired cooldown (35 minutes elapsed >= 30 minutes)
    risk_input_expired = RiskInput(
        pipeline_run_id="pipe_hist_1",
        candidate=candidate,
        proposal=proposal,
        current_equity_usdt=10000.0,
        open_positions_count=0,
        total_exposure_usdt=0.0,
        consecutive_losses_count=3,
        last_loss_timestamp_ms=ts_hist - (35 * 60 * 1000),
        eval_timestamp_ms=ts_hist,
    )
    out_expired = await risk_agent.evaluate(risk_input_expired)
    assert out_expired.decision.decision == AgentAction.APPROVED
    assert "LOSS_STREAK_COOLDOWN" in out_expired.decision.checks_passed


@pytest.mark.asyncio
async def test_deterministic_replay(risk_agent, base_candidate_and_proposal):
    """Two evaluations with identical historical timestamps yield identical outputs."""
    candidate, proposal, ts_hist = base_candidate_and_proposal

    risk_input = RiskInput(
        pipeline_run_id="pipe_hist_1",
        candidate=candidate,
        proposal=proposal,
        current_equity_usdt=10000.0,
        open_positions_count=0,
        total_exposure_usdt=0.0,
        eval_timestamp_ms=ts_hist,
    )

    out1 = await risk_agent.evaluate(risk_input)
    out2 = await risk_agent.evaluate(risk_input)

    assert out1.decision.decision_id == out2.decision.decision_id
    assert out1.decision.evaluated_at_ms == out2.decision.evaluated_at_ms
    assert out1.decision.approved_quantity == out2.decision.approved_quantity
    assert out1.decision.checks_passed == out2.decision.checks_passed


@pytest.mark.asyncio
async def test_banker_simulated_clock():
    """BankerAgent uses eval_timestamp_ms for price staleness checks."""
    banker = BankerAgent()
    ts_hist = 1704067200000

    # Fresh price under simulated time
    fresh_input = BankerInput(
        position_id="pos_1",
        symbol="BTCUSDT",
        side=TradeSide.LONG,
        entry_price=50000.0,
        current_mark_price=50500.0,
        current_stop_loss=49000.0,
        take_profit_1=52000.0,
        take_profit_2=54000.0,
        price_timestamp_ms=ts_hist,
        eval_timestamp_ms=ts_hist + 5_000,  # 5s age <= 15s
    )
    out_fresh = await banker.evaluate(fresh_input)
    assert out_fresh.action == AgentAction.HOLD
    assert "SAFE_MONITORING" not in out_fresh.rationale

    # Stale price under simulated time
    stale_input = BankerInput(
        position_id="pos_1",
        symbol="BTCUSDT",
        side=TradeSide.LONG,
        entry_price=50000.0,
        current_mark_price=50500.0,
        current_stop_loss=49000.0,
        take_profit_1=52000.0,
        take_profit_2=54000.0,
        price_timestamp_ms=ts_hist,
        eval_timestamp_ms=ts_hist + 20_000,  # 20s age > 15s
    )
    out_stale = await banker.evaluate(stale_input)
    assert out_stale.action == AgentAction.HOLD
    assert "SAFE_MONITORING: market price is stale" in out_stale.rationale

    # Future price timestamp under simulated time
    future_input = BankerInput(
        position_id="pos_1",
        symbol="BTCUSDT",
        side=TradeSide.LONG,
        entry_price=50000.0,
        current_mark_price=50500.0,
        current_stop_loss=49000.0,
        take_profit_1=52000.0,
        take_profit_2=54000.0,
        price_timestamp_ms=ts_hist + 5_000,
        eval_timestamp_ms=ts_hist,  # Price is 5s ahead of eval
    )
    out_future = await banker.evaluate(future_input)
    assert out_future.action == AgentAction.HOLD
    assert "market price timestamp is in the future" in out_future.rationale
