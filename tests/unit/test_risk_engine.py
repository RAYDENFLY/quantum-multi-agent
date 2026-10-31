"""Unit tests for deterministic Python Risk Engine and position sizing gatekeeper.

Verifies all 12 hard deterministic risk gates and missing data integrity checks:
Gate 1: SIGNAL_FRESHNESS
Gate 2: DRAWDOWN_CIRCUIT_BREAKER
Gate 3: DAILY_LOSS_LIMIT
Gate 4: LOSS_STREAK_COOLDOWN
Gate 5: MAX_CONCURRENT_POSITIONS
Gate 6: STOP_GEOMETRY_VALID
Gate 7: MAX_SPREAD
Gate 8: MIN_NET_RR
Gate 9: MAX_SLIPPAGE
Gate 10: LOT_STEP_AND_MIN_NOTIONAL
Gate 11: MAX_EXPOSURE_AND_LEVERAGE
Gate 12: LIQUIDATION_BUFFER
"""

import time
import pytest

from quantum.agents.contracts import RiskInput
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


def make_test_environment(
    snapshot_age_ms: int = 100,
    spread_bps: float = 1.0,
    open_positions: int = 0,
    equity: float = 10000.0,
    entry: float = 65000.0,
    stop: float = 64500.0,
    tp1: float = 66500.0,
    tp2: float = 67500.0,
    atr_15m: float = 250.0,
) -> tuple[ScannerCandidate, TradeProposal]:
    now_ms = int(time.time() * 1000)
    ctx = MarketContext(
        exchange=ExchangeId.BYBIT,
        symbol="BTCUSDT",
        snapshot_timestamp_ms=now_ms - snapshot_age_ms,
        last_price=entry,
        mark_price=entry,
        index_price=entry,
        bid1_price=entry - 0.5,
        ask1_price=entry + 0.5,
        spread_bps=spread_bps,
        turnover_24h_usdt=500_000_000.0,
        price_change_24h_pct=2.5,
        funding_rate=0.0001,
        next_funding_time_ms=now_ms + 28800000,
        atr_15m=atr_15m,
        atr_1h=atr_15m * 1.8,
        rvol_15m=2.0,
        rsi_15m=60.0,
        features={"wick_trap_ratio": 0.12},
    )
    candidate = ScannerCandidate(
        candidate_id="cand_test_risk",
        scan_cycle_id="cycle_risk_1",
        exchange=ExchangeId.BYBIT,
        symbol="BTCUSDT",
        directional_bias=TradeSide.LONG,
        primary_category=CandidateCategory.MOMENTUM_ACCELERATION,
        deterministic_score=80.0,
        state_hash="a" * 16,
        context=ctx,
        created_at_ms=now_ms - snapshot_age_ms,
        expires_at_ms=now_ms + 60000,
    )
    proposal = TradeProposal(
        proposal_id="prop_risk_test",
        pipeline_run_id="run_risk_1",
        exchange=ExchangeId.BYBIT,
        symbol="BTCUSDT",
        side=TradeSide.LONG,
        order_type=OrderType.LIMIT,
        reference_mark_price=entry,
        entry_price=entry,
        entry_zone_low=entry - 50.0,
        entry_zone_high=entry + 20.0,
        stop_loss=stop,
        take_profit_1=tp1,
        take_profit_2=tp2,
        tp1_close_pct=0.5,
        estimated_reward_risk=2.0,
        expected_net_r=0.45,
        prob_tp1_before_sl=0.62,
        prob_tp2_before_sl=0.45,
        expected_holding_minutes=120,
        rationale="Risk test proposal",
        market_regime=MarketRegime.TREND_IMPULSE,
        invalidation_price=stop,
        sniper_model_version="rule_baseline_v1",
        created_at_ms=now_ms,
    )
    return candidate, proposal


@pytest.mark.asyncio
async def test_risk_agent_approved_clean_trade() -> None:
    config = RiskConfig(
        max_concurrent_positions=3,
        risk_per_trade_pct=0.01,
        max_symbol_exposure_pct=0.20,
        max_total_exposure_pct=0.50,
        max_leverage_per_position=5.0,
        max_spread_bps=5.0,
        min_net_reward_risk=1.50,
    )
    risk_agent = RiskAgent(config)
    cand, prop = make_test_environment(open_positions=0, equity=10000.0)

    out = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_clean",
            candidate=cand,
            proposal=prop,
            current_equity_usdt=10000.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
        )
    )

    assert out.decision.decision == AgentAction.APPROVED
    assert out.decision.approved_quantity > 0.0
    assert out.decision.notional_usdt >= 10.0
    assert out.decision.effective_leverage <= 5.0
    assert len(out.decision.veto_reasons) == 0


@pytest.mark.asyncio
async def test_risk_agent_missing_data_integrity() -> None:
    risk_agent = RiskAgent(RiskConfig())
    cand, prop = make_test_environment()

    # Missing equity
    out_no_eq = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_no_eq",
            candidate=cand,
            proposal=prop,
            current_equity_usdt=None,
            open_positions_count=0,
            total_exposure_usdt=0.0,
        )
    )
    assert out_no_eq.decision.decision == AgentAction.REJECTED
    assert any("VETO_MISSING_ACCOUNT_EQUITY" in r for r in out_no_eq.decision.veto_reasons)

    # Missing open positions count
    out_no_pos = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_no_pos",
            candidate=cand,
            proposal=prop,
            current_equity_usdt=10000.0,
            open_positions_count=None,
            total_exposure_usdt=0.0,
        )
    )
    assert out_no_pos.decision.decision == AgentAction.REJECTED
    assert any("VETO_MISSING_OPEN_POSITIONS" in r for r in out_no_pos.decision.veto_reasons)


@pytest.mark.asyncio
async def test_risk_agent_gate1_signal_freshness() -> None:
    risk_agent = RiskAgent(RiskConfig())
    # Stale signal > 15000 ms
    cand, prop = make_test_environment(snapshot_age_ms=16000)

    out = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_stale",
            candidate=cand,
            proposal=prop,
            current_equity_usdt=10000.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
        )
    )
    assert out.decision.decision == AgentAction.REJECTED
    assert any("VETO_STALE_SIGNAL" in r for r in out.decision.veto_reasons)


@pytest.mark.asyncio
async def test_risk_agent_gate2_drawdown_circuit_breaker() -> None:
    config = RiskConfig(max_total_drawdown_pct=0.08)  # 8% max DD
    risk_agent = RiskAgent(config)
    cand, prop = make_test_environment()

    # Current equity 9000, Peak equity 10000 -> 10% DD (> 8% max)
    out = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_dd",
            candidate=cand,
            proposal=prop,
            current_equity_usdt=9000.0,
            peak_equity_usdt=10000.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
        )
    )
    assert out.decision.decision == AgentAction.REJECTED
    assert any("VETO_DRAWDOWN_BREACHED" in r for r in out.decision.veto_reasons)


@pytest.mark.asyncio
async def test_risk_agent_gate3_daily_loss_limit() -> None:
    config = RiskConfig(max_daily_loss_pct=0.025)  # 2.5% max daily loss
    risk_agent = RiskAgent(config)
    cand, prop = make_test_environment()

    # Starting equity 10000, daily loss -300 USDT -> 3.0% loss (> 2.5% max)
    out = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_daily_loss",
            candidate=cand,
            proposal=prop,
            current_equity_usdt=9700.0,
            starting_day_equity_usdt=10000.0,
            daily_pnl_usdt=-300.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
        )
    )
    assert out.decision.decision == AgentAction.REJECTED
    assert any("VETO_DAILY_LOSS_BREACHED" in r for r in out.decision.veto_reasons)


@pytest.mark.asyncio
async def test_risk_agent_gate4_loss_streak_cooldown() -> None:
    config = RiskConfig(loss_streak_cooldown_count=3, per_symbol_loss_cooldown_min=45)
    risk_agent = RiskAgent(config)
    cand, prop = make_test_environment()
    now_ms = int(time.time() * 1000)

    # 3 consecutive losses, last loss 10 minutes ago (< 45 minutes cooldown)
    out = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_streak",
            candidate=cand,
            proposal=prop,
            current_equity_usdt=10000.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
            consecutive_losses_count=3,
            last_loss_timestamp_ms=now_ms - (10 * 60_000),
        )
    )
    assert out.decision.decision == AgentAction.REJECTED
    assert any("VETO_LOSS_STREAK_COOLDOWN" in r for r in out.decision.veto_reasons)


@pytest.mark.asyncio
async def test_risk_agent_gate5_max_concurrent_positions() -> None:
    config = RiskConfig(max_concurrent_positions=2)
    risk_agent = RiskAgent(config)
    cand, prop = make_test_environment()

    out = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_max_pos",
            candidate=cand,
            proposal=prop,
            current_equity_usdt=10000.0,
            open_positions_count=2,
            total_exposure_usdt=4000.0,
        )
    )
    assert out.decision.decision == AgentAction.REJECTED
    assert any("VETO_MAX_POSITIONS_BREACHED" in r for r in out.decision.veto_reasons)


@pytest.mark.asyncio
async def test_risk_agent_gate6_stop_geometry() -> None:
    risk_agent = RiskAgent(RiskConfig())
    cand, prop = make_test_environment(atr_15m=300.0)

    # Stop distance 50 < 0.4 * 300 (120)
    prop_tight = prop.model_copy(update={"stop_loss": 64950.0})
    out = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_tight_stop",
            candidate=cand,
            proposal=prop_tight,
            current_equity_usdt=10000.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
        )
    )
    assert out.decision.decision == AgentAction.REJECTED
    assert any("VETO_STOP_TOO_TIGHT" in r for r in out.decision.veto_reasons)


@pytest.mark.asyncio
async def test_risk_agent_gate7_max_spread() -> None:
    config = RiskConfig(max_spread_bps=3.0)
    risk_agent = RiskAgent(config)
    cand, prop = make_test_environment(spread_bps=4.5)

    out = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_wide_spread",
            candidate=cand,
            proposal=prop,
            current_equity_usdt=10000.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
        )
    )
    assert out.decision.decision == AgentAction.REJECTED
    assert any("VETO_EXCESSIVE_SPREAD" in r for r in out.decision.veto_reasons)


@pytest.mark.asyncio
async def test_risk_agent_gate8_min_net_rr() -> None:
    config = RiskConfig(min_net_reward_risk=2.50)
    risk_agent = RiskAgent(config)
    # Default environment produces net R:R ~ 1.95 < min 2.50
    cand, prop = make_test_environment(entry=65000.0, stop=64500.0, tp1=65800.0, tp2=66200.0)

    out = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_low_rr",
            candidate=cand,
            proposal=prop,
            current_equity_usdt=10000.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
        )
    )
    assert out.decision.decision == AgentAction.REJECTED
    assert any("VETO_INSUFFICIENT_NET_RR" in r for r in out.decision.veto_reasons)


@pytest.mark.asyncio
async def test_risk_agent_gate9_max_slippage() -> None:
    config = RiskConfig(max_estimated_slippage_bps=5.0)
    risk_agent = RiskAgent(config)
    cand, prop = make_test_environment()

    out = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_slip",
            candidate=cand,
            proposal=prop,
            current_equity_usdt=10000.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
            estimated_slippage_bps=8.0,  # 8.0 > max 5.0 bps
        )
    )
    assert out.decision.decision == AgentAction.REJECTED
    assert any("VETO_EXCESSIVE_SLIPPAGE" in r for r in out.decision.veto_reasons)


@pytest.mark.asyncio
async def test_risk_agent_gate10_min_notional() -> None:
    config = RiskConfig(risk_per_trade_pct=0.001)
    risk_agent = RiskAgent(config)
    # Entry 65000, stop 64500 (loss ~ 597/unit), equity 1000 -> budget = $1.00 -> qty = ~0.0016
    # With lot_step=0.001, qty rounds down to 0.001 -> notional = $65.00
    # Setting min_notional_usdt to 100.0 USDT triggers VETO_BELOW_MIN_NOTIONAL
    cand, prop = make_test_environment(equity=1000.0)

    out = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_tiny_notional",
            candidate=cand,
            proposal=prop,
            current_equity_usdt=1000.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
            min_notional_usdt=100.0,
        )
    )
    assert out.decision.decision == AgentAction.REJECTED
    assert any("VETO_BELOW_MIN_NOTIONAL" in r for r in out.decision.veto_reasons)


@pytest.mark.asyncio
async def test_risk_agent_gate11_leverage_and_exposure_caps() -> None:
    config = RiskConfig(max_leverage_per_position=1.0)  # Max 1.0x leverage
    risk_agent = RiskAgent(config)
    cand, prop = make_test_environment(equity=10000.0)

    out = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_lev",
            candidate=cand,
            proposal=prop,
            current_equity_usdt=10000.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
        )
    )
    assert out.decision.effective_leverage <= 1.0


@pytest.mark.asyncio
async def test_risk_agent_gate12_liquidation_buffer() -> None:
    # Set leverage to 5.0x (max allowed in RiskConfig)
    config = RiskConfig(max_leverage_per_position=5.0)
    risk_agent = RiskAgent(config)

    # Wide stop geometry: entry 65000, stop 55000 (stop_dist = 10000)
    # At 5.0x leverage: est_liq_distance = 65000 / 5.0 = 13000
    # 75% of liq distance = 9750. Since stop_dist 10000 >= 9750, VETO_INSUFFICIENT_LIQUIDATION_BUFFER triggers
    cand, prop = make_test_environment(
        entry=65000.0,
        stop=55000.0,
        tp1=95000.0,
        tp2=110000.0,
        equity=10000.0,
    )

    out = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_liq_buffer",
            candidate=cand,
            proposal=prop,
            current_equity_usdt=10000.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
        )
    )

    # Must be rejected due to insufficient liquidation buffer
    assert out.decision.decision == AgentAction.REJECTED
    assert any("VETO_INSUFFICIENT_LIQUIDATION_BUFFER" in r for r in out.decision.veto_reasons)


@pytest.mark.asyncio
async def test_risk_agent_missing_exposure_and_invalid_prices() -> None:
    risk_agent = RiskAgent(RiskConfig())
    cand, prop = make_test_environment()

    # 1. Missing total exposure (None)
    out_no_exp = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_no_exp",
            candidate=cand,
            proposal=prop,
            current_equity_usdt=10000.0,
            open_positions_count=0,
            total_exposure_usdt=None,
        )
    )
    assert out_no_exp.decision.decision == AgentAction.REJECTED
    assert any("VETO_MISSING_TOTAL_EXPOSURE" in r for r in out_no_exp.decision.veto_reasons)

    # 2. Non-positive snapshot timestamp (<= 0)
    cand_bad_ts = cand.model_copy(
        update={"context": cand.context.model_copy(update={"snapshot_timestamp_ms": 0})}
    )
    out_bad_ts = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_bad_ts",
            candidate=cand_bad_ts,
            proposal=prop,
            current_equity_usdt=10000.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
        )
    )
    assert out_bad_ts.decision.decision == AgentAction.REJECTED
    assert any("VETO_MISSING_TIMESTAMP" in r for r in out_bad_ts.decision.veto_reasons)

    # 3. Invalid non-positive market price
    cand_bad_price = cand.model_copy(
        update={"context": cand.context.model_copy(update={"last_price": 0.0})}
    )
    out_bad_price = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_bad_price",
            candidate=cand_bad_price,
            proposal=prop,
            current_equity_usdt=10000.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
        )
    )
    assert out_bad_price.decision.decision == AgentAction.REJECTED
    assert any("VETO_MISSING_PRICE_DATA" in r for r in out_bad_price.decision.veto_reasons)

    # 4. Invalid negative spread_bps
    cand_bad_spread = cand.model_copy(
        update={"context": cand.context.model_copy(update={"spread_bps": -1.0})}
    )
    out_bad_spread = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_bad_spread",
            candidate=cand_bad_spread,
            proposal=prop,
            current_equity_usdt=10000.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
        )
    )
    assert out_bad_spread.decision.decision == AgentAction.REJECTED
    assert any("VETO_MISSING_PRICE_DATA" in r for r in out_bad_spread.decision.veto_reasons)


@pytest.mark.asyncio
async def test_risk_agent_gate4_loss_streak_cooldown_boundaries() -> None:
    config = RiskConfig(loss_streak_cooldown_count=3, per_symbol_loss_cooldown_min=45)
    risk_agent = RiskAgent(config)
    cand, prop = make_test_environment()
    now_ms = int(time.time() * 1000)
    cooldown_ms = 45 * 60_000  # 2,700,000 ms

    # Boundary 1: 44 minutes 59 seconds (elapsed: 2,699,000 ms < 2,700,000 ms) -> VETO
    out_44m59s = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_44m59s",
            candidate=cand,
            proposal=prop,
            current_equity_usdt=10000.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
            consecutive_losses_count=3,
            last_loss_timestamp_ms=now_ms - (cooldown_ms - 1000),
        )
    )
    assert out_44m59s.decision.decision == AgentAction.REJECTED
    assert any("VETO_LOSS_STREAK_COOLDOWN" in r for r in out_44m59s.decision.veto_reasons)

    # Boundary 2: Exactly 45 minutes (elapsed: 2,700,000 ms == 2,700,000 ms) -> PASS
    out_45m00s = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_45m00s",
            candidate=cand,
            proposal=prop,
            current_equity_usdt=10000.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
            consecutive_losses_count=3,
            last_loss_timestamp_ms=now_ms - cooldown_ms,
        )
    )
    assert "LOSS_STREAK_COOLDOWN" in out_45m00s.decision.checks_passed
    assert not any("VETO_LOSS_STREAK_COOLDOWN" in r for r in out_45m00s.decision.veto_reasons)

    # Boundary 3: 45 minutes 1 second (elapsed: 2,701,000 ms > 2,700,000 ms) -> PASS
    out_45m01s = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_45m01s",
            candidate=cand,
            proposal=prop,
            current_equity_usdt=10000.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
            consecutive_losses_count=3,
            last_loss_timestamp_ms=now_ms - (cooldown_ms + 1000),
        )
    )
    assert "LOSS_STREAK_COOLDOWN" in out_45m01s.decision.checks_passed
    assert not any("VETO_LOSS_STREAK_COOLDOWN" in r for r in out_45m01s.decision.veto_reasons)

    # Missing timestamp when streak is active -> VETO
    out_missing_ts = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_missing_ts",
            candidate=cand,
            proposal=prop,
            current_equity_usdt=10000.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
            consecutive_losses_count=3,
            last_loss_timestamp_ms=None,
        )
    )
    assert out_missing_ts.decision.decision == AgentAction.REJECTED
    assert any("VETO_LOSS_STREAK_COOLDOWN" in r for r in out_missing_ts.decision.veto_reasons)

    # Non-positive timestamp when streak is active -> VETO
    out_zero_ts = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_zero_ts",
            candidate=cand,
            proposal=prop,
            current_equity_usdt=10000.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
            consecutive_losses_count=3,
            last_loss_timestamp_ms=0,
        )
    )
    assert out_zero_ts.decision.decision == AgentAction.REJECTED
    assert any("VETO_LOSS_STREAK_COOLDOWN" in r for r in out_zero_ts.decision.veto_reasons)

    # Future timestamp when streak is active -> VETO
    out_future_ts = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_future_ts",
            candidate=cand,
            proposal=prop,
            current_equity_usdt=10000.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
            consecutive_losses_count=3,
            last_loss_timestamp_ms=now_ms + 60000,
        )
    )
    assert out_future_ts.decision.decision == AgentAction.REJECTED
    assert any("VETO_LOSS_STREAK_COOLDOWN" in r for r in out_future_ts.decision.veto_reasons)


@pytest.mark.asyncio
async def test_risk_agent_gate12_liquidation_buffer_boundaries() -> None:
    # 5.0x leverage ceiling: est_liq_distance = 60000 / 5.0 = 12000.0
    # 75% threshold = 0.75 * 12000 = 9000.0
    config = RiskConfig(max_leverage_per_position=5.0)
    risk_agent = RiskAgent(config)

    # Boundary 1: Stop distance 8990 < 9000 (74.916% of liq dist) -> PASSES Gate 12
    cand_safe, prop_safe = make_test_environment(
        entry=60000.0,
        stop=51010.0,  # stop_dist = 8990.0 < 9000.0
        tp1=90000.0,
        tp2=100000.0,
        equity=10000.0,
    )
    out_safe = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_liq_74_9",
            candidate=cand_safe,
            proposal=prop_safe,
            current_equity_usdt=10000.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
        )
    )
    assert "LIQUIDATION_BUFFER" in out_safe.decision.checks_passed
    assert not any("VETO_INSUFFICIENT_LIQUIDATION_BUFFER" in r for r in out_safe.decision.veto_reasons)

    # Boundary 2: Stop distance exactly 9000.0 == 9000.0 (75.0% of liq dist) -> VETO
    cand_exact, prop_exact = make_test_environment(
        entry=60000.0,
        stop=51000.0,  # stop_dist = 9000.0 >= 9000.0
        tp1=90000.0,
        tp2=100000.0,
        equity=10000.0,
    )
    out_exact = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_liq_75_0",
            candidate=cand_exact,
            proposal=prop_exact,
            current_equity_usdt=10000.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
        )
    )
    assert out_exact.decision.decision == AgentAction.REJECTED
    assert any("VETO_INSUFFICIENT_LIQUIDATION_BUFFER" in r for r in out_exact.decision.veto_reasons)

    # Boundary 3: Stop distance 9010.0 > 9000.0 (75.083% of liq dist) -> VETO
    cand_over, prop_over = make_test_environment(
        entry=60000.0,
        stop=50990.0,  # stop_dist = 9010.0 >= 9000.0
        tp1=90000.0,
        tp2=100000.0,
        equity=10000.0,
    )
    out_over = await risk_agent.evaluate(
        RiskInput(
            pipeline_run_id="run_liq_75_1",
            candidate=cand_over,
            proposal=prop_over,
            current_equity_usdt=10000.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
        )
    )
    assert out_over.decision.decision == AgentAction.REJECTED
    assert any("VETO_INSUFFICIENT_LIQUIDATION_BUFFER" in r for r in out_over.decision.veto_reasons)


