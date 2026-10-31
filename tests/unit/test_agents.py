"""Unit tests for specialized quantitative intelligence agents."""

import pytest

from quantum.agents.analyst import AnalystAgent
from quantum.agents.banker import BankerAgent
from quantum.agents.contracts import (
    AnalystInput,
    BankerInput,
    ScoutInput,
    SniperInput,
)
from quantum.agents.scout import ScoutAgent
from quantum.agents.sniper import SniperAgent
from quantum.domain.enums import (
    AgentAction,
    CandidateCategory,
    ExchangeId,
    InferenceMode,
    MarketRegime,
    TradeSide,
)
from quantum.domain.models import MarketContext, ScannerCandidate


def make_candidate(
    score: float = 85.0,
    wick_trap: float = 0.12,
    rvol: float = 2.2,
    rsi: float = 68.0,
    side: TradeSide = TradeSide.LONG,
    mark_price: float = 65000.0,
    atr_15m: float = 250.0,
) -> ScannerCandidate:
    ctx = MarketContext(
        exchange=ExchangeId.BYBIT,
        symbol="BTCUSDT",
        snapshot_timestamp_ms=1700000000000,
        last_price=mark_price,
        mark_price=mark_price,
        index_price=mark_price,
        bid1_price=mark_price - 1.0,
        ask1_price=mark_price + 1.0,
        spread_bps=0.5,
        turnover_24h_usdt=500_000_000.0,
        price_change_24h_pct=2.5,
        funding_rate=0.0001,
        next_funding_time_ms=1700028800000,
        atr_15m=atr_15m,
        atr_1h=atr_15m * 1.8,
        rvol_15m=rvol,
        rsi_15m=rsi,
        features={"wick_trap_ratio": wick_trap, "log_turnover_24h": 20.0},
    )
    return ScannerCandidate(
        candidate_id="cand_test_1",
        scan_cycle_id="cycle_test_1",
        exchange=ExchangeId.BYBIT,
        symbol="BTCUSDT",
        directional_bias=side,
        primary_category=CandidateCategory.MOMENTUM_ACCELERATION,
        deterministic_score=score,
        state_hash="a" * 16,
        context=ctx,
        created_at_ms=1700000000000,
        expires_at_ms=1700000060000,
    )


@pytest.mark.asyncio
async def test_scout_agent_proceed_and_skip() -> None:
    scout = ScoutAgent(min_probability=0.56, max_wick_trap=0.55)

    # 1. High scoring clean candidate -> PROCEED
    cand_good = make_candidate(score=85.0, wick_trap=0.10)
    out_good = await scout.evaluate(ScoutInput(pipeline_run_id="run_1", candidate=cand_good))
    assert out_good.action == AgentAction.PROCEED
    assert out_good.probability_estimate >= 0.56
    assert out_good.inference_mode == InferenceMode.FALLBACK_RULE_ONLY

    # 2. High wick-trap ratio candidate -> SKIP
    cand_trap = make_candidate(score=85.0, wick_trap=0.65)
    out_trap = await scout.evaluate(ScoutInput(pipeline_run_id="run_2", candidate=cand_trap))
    assert out_trap.action == AgentAction.SKIP
    assert "Wick trap ratio" in (out_trap.abort_reason or "")

    # 3. Low score candidate -> SKIP
    cand_low = make_candidate(score=30.0, wick_trap=0.10)
    out_low = await scout.evaluate(ScoutInput(pipeline_run_id="run_3", candidate=cand_low))
    assert out_low.action == AgentAction.SKIP
    assert "Probability estimate" in (out_low.abort_reason or "")


@pytest.mark.asyncio
async def test_analyst_agent_regime_and_invalidation() -> None:
    analyst = AnalystAgent(min_probability=0.58)

    # 1. Trending candidate
    cand_trend = make_candidate(rvol=2.5, rsi=72.0, side=TradeSide.LONG, mark_price=65000.0, atr_15m=200.0)
    scout_out = await ScoutAgent().evaluate(ScoutInput(pipeline_run_id="run_1", candidate=cand_trend))
    out_trend = await analyst.evaluate(AnalystInput(pipeline_run_id="run_1", candidate=cand_trend, scout_output=scout_out))

    assert out_trend.action == AgentAction.PROCEED
    assert out_trend.market_regime == MarketRegime.TREND_IMPULSE
    # Long invalidation below mark
    assert out_trend.invalidation_price < 65000.0

    # 2. Short candidate invalidation above mark
    cand_short = make_candidate(rvol=2.5, rsi=25.0, side=TradeSide.SHORT, mark_price=65000.0, atr_15m=200.0)
    scout_short = await ScoutAgent().evaluate(ScoutInput(pipeline_run_id="run_2", candidate=cand_short))
    out_short = await analyst.evaluate(AnalystInput(pipeline_run_id="run_2", candidate=cand_short, scout_output=scout_short))

    assert out_short.action == AgentAction.PROCEED
    assert out_short.invalidation_price > 65000.0


@pytest.mark.asyncio
async def test_sniper_agent_trade_proposal_generation() -> None:
    sniper = SniperAgent(min_expected_r=0.25, min_gross_rr=1.80)
    cand = make_candidate(side=TradeSide.LONG, mark_price=65000.0, atr_15m=200.0)
    scout_out = await ScoutAgent().evaluate(ScoutInput(pipeline_run_id="run_1", candidate=cand))
    analyst_out = await AnalystAgent().evaluate(AnalystInput(pipeline_run_id="run_1", candidate=cand, scout_output=scout_out))

    out_sniper = await sniper.evaluate(
        SniperInput(pipeline_run_id="run_1", candidate=cand, scout_output=scout_out, analyst_output=analyst_out)
    )

    assert out_sniper.action == AgentAction.PROPOSE_TRADE
    assert out_sniper.proposal is not None
    prop = out_sniper.proposal
    assert prop.side == TradeSide.LONG
    assert prop.stop_loss < prop.entry_price < prop.take_profit_1 < prop.take_profit_2
    assert prop.estimated_reward_risk >= 1.80
    assert prop.expected_net_r >= 0.25


@pytest.mark.asyncio
async def test_banker_agent_position_lifecycle() -> None:
    banker = BankerAgent()

    # 1. Position normal -> HOLD
    out_hold = await banker.evaluate(
        BankerInput(
            position_id="pos_1",
            symbol="BTCUSDT",
            side=TradeSide.LONG,
            entry_price=65000.0,
            current_mark_price=65200.0,
            current_stop_loss=64500.0,
            take_profit_1=66000.0,
            take_profit_2=66800.0,
            tp1_filled=False,
            unrealized_pnl_r=0.40,
        )
    )
    assert out_hold.action == AgentAction.HOLD
    assert out_hold.suggested_stop_loss == 64500.0

    # 2. Stop-loss breached -> EARLY_EXIT
    out_exit = await banker.evaluate(
        BankerInput(
            position_id="pos_2",
            symbol="BTCUSDT",
            side=TradeSide.LONG,
            entry_price=65000.0,
            current_mark_price=64400.0,  # Below SL 64500
            current_stop_loss=64500.0,
            take_profit_1=66000.0,
            take_profit_2=66800.0,
            tp1_filled=False,
            unrealized_pnl_r=-1.0,
        )
    )
    assert out_exit.action == AgentAction.EARLY_EXIT
    assert out_exit.hazard_prob == 1.0

    # 3. TP1 filled -> TIGHTEN_STOP to breakeven
    out_ratchet = await banker.evaluate(
        BankerInput(
            position_id="pos_3",
            symbol="BTCUSDT",
            side=TradeSide.LONG,
            entry_price=65000.0,
            current_mark_price=66100.0,
            current_stop_loss=64500.0,
            take_profit_1=66000.0,
            take_profit_2=66800.0,
            tp1_filled=True,
            unrealized_pnl_r=2.0,
        )
    )
    assert out_ratchet.action == AgentAction.TIGHTEN_STOP
    assert out_ratchet.suggested_stop_loss == 65000.0  # Ratcheted to breakeven
