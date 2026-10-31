"""Unit tests for PipelineOrchestrator state machine, timeouts, and persistence."""

import asyncio
from pathlib import Path
import time
import pytest

from quantum.agents.analyst import AnalystAgent
from quantum.agents.contracts import ScoutInput, ScoutOutput
from quantum.agents.orchestrator import PipelineOrchestrator
from quantum.agents.risk import RiskAgent
from quantum.agents.scout import ScoutAgent
from quantum.agents.sniper import SniperAgent
from quantum.config.settings import RiskConfig
from quantum.core.event_bus import EventBus
from quantum.domain.enums import (
    AgentAction,
    CandidateCategory,
    ExchangeId,
    InferenceMode,
    PipelineStage,
    PipelineStatus,
    TradeSide,
)
from quantum.domain.models import MarketContext, ScannerCandidate
from quantum.storage.database import DatabaseManager


def make_clean_candidate(
    score: float = 85.0,
    wick_trap: float = 0.10,
    rvol: float = 2.2,
    rsi: float = 65.0,
) -> ScannerCandidate:
    now_ms = int(time.time() * 1000)
    ctx = MarketContext(
        exchange=ExchangeId.BYBIT,
        symbol="BTCUSDT",
        snapshot_timestamp_ms=now_ms,
        last_price=65000.0,
        mark_price=65000.0,
        index_price=65000.0,
        bid1_price=64998.0,
        ask1_price=65002.0,
        spread_bps=0.6,
        turnover_24h_usdt=500_000_000.0,
        price_change_24h_pct=2.5,
        funding_rate=0.0001,
        next_funding_time_ms=now_ms + 28800000,
        atr_15m=250.0,
        atr_1h=450.0,
        rvol_15m=rvol,
        rsi_15m=rsi,
        features={"wick_trap_ratio": wick_trap, "log_turnover_24h": 20.0},
    )
    return ScannerCandidate(
        candidate_id="cand_orch_1",
        scan_cycle_id="cycle_orch_1",
        exchange=ExchangeId.BYBIT,
        symbol="BTCUSDT",
        directional_bias=TradeSide.LONG,
        primary_category=CandidateCategory.MOMENTUM_ACCELERATION,
        deterministic_score=score,
        state_hash="a" * 16,
        context=ctx,
        created_at_ms=now_ms,
        expires_at_ms=now_ms + 60000,
    )


@pytest.mark.asyncio
async def test_pipeline_orchestrator_full_run_approved() -> None:
    risk_config = RiskConfig(
        max_concurrent_positions=3,
        risk_per_trade_pct=0.01,
        max_symbol_exposure_pct=0.20,
        max_total_exposure_pct=0.50,
        max_leverage_per_position=5.0,
        max_spread_bps=5.0,
        min_net_reward_risk=1.50,
    )
    orchestrator = PipelineOrchestrator(
        scout=ScoutAgent(min_probability=0.56),
        analyst=AnalystAgent(min_probability=0.58),
        sniper=SniperAgent(min_expected_r=0.25, min_gross_rr=1.80),
        risk=RiskAgent(risk_config),
        default_equity_usdt=10000.0,
    )

    candidate = make_clean_candidate()
    result = await orchestrator.execute(candidate)

    assert result.status == PipelineStatus.APPROVED
    assert result.final_stage == PipelineStage.RISK
    assert result.scout_output is not None
    assert result.analyst_output is not None
    assert result.sniper_output is not None
    assert result.risk_output is not None
    assert result.total_latency_ms > 0.0


@pytest.mark.asyncio
async def test_pipeline_orchestrator_invalid_features_short_circuit() -> None:
    orchestrator = PipelineOrchestrator(
        scout=ScoutAgent(),
        analyst=AnalystAgent(),
        sniper=SniperAgent(),
        risk=RiskAgent(RiskConfig()),
    )

    cand = make_clean_candidate()
    # Inject NaN feature
    cand_bad = cand.model_copy(
        update={
            "context": cand.context.model_copy(
                update={"features": {"wick_trap_ratio": float("nan")}}
            )
        }
    )

    result = await orchestrator.execute(cand_bad)
    assert result.status == PipelineStatus.SKIP_FEATURE_INVALID
    assert result.final_stage == PipelineStage.FEATURE_EXTRACTION
    assert result.scout_output is None


@pytest.mark.asyncio
async def test_pipeline_orchestrator_scout_skip_propagation() -> None:
    # Scout threshold very high so candidate is skipped
    orchestrator = PipelineOrchestrator(
        scout=ScoutAgent(min_probability=0.99),
        analyst=AnalystAgent(),
        sniper=SniperAgent(),
        risk=RiskAgent(RiskConfig()),
    )

    cand = make_clean_candidate(score=70.0)
    result = await orchestrator.execute(cand)

    assert result.status == PipelineStatus.SKIP_SCOUT
    assert result.final_stage == PipelineStage.SCOUT
    assert result.scout_output is not None
    assert result.analyst_output is None
    assert result.sniper_output is None


@pytest.mark.asyncio
async def test_pipeline_orchestrator_timeout_handling() -> None:
    class SlowScout(ScoutAgent):
        async def evaluate(self, input_data: ScoutInput) -> ScoutOutput:
            await asyncio.sleep(0.100)  # Exceeds 50ms timeout
            return await super().evaluate(input_data)

    orchestrator = PipelineOrchestrator(
        scout=SlowScout(),
        analyst=AnalystAgent(),
        sniper=SniperAgent(),
        risk=RiskAgent(RiskConfig()),
    )

    cand = make_clean_candidate()
    result = await orchestrator.execute(cand)

    assert result.status == PipelineStatus.SKIP_SCOUT
    assert "timed out" in (result.abort_reason or "")


@pytest.mark.asyncio
async def test_pipeline_orchestrator_missing_equity_veto() -> None:
    orchestrator = PipelineOrchestrator(
        scout=ScoutAgent(),
        analyst=AnalystAgent(),
        sniper=SniperAgent(),
        risk=RiskAgent(RiskConfig()),
        default_equity_usdt=None,  # No equity provided
    )

    cand = make_clean_candidate()
    result = await orchestrator.execute(cand)

    assert result.status == PipelineStatus.VETO_RISK
    assert result.final_stage == PipelineStage.RISK
    assert "VETO_MISSING_ACCOUNT_EQUITY" in (result.abort_reason or "")


@pytest.mark.asyncio
async def test_pipeline_orchestrator_sqlite_persistence(tmp_path: Path) -> None:
    db_file = tmp_path / "test_pipeline.db"
    db_manager = DatabaseManager(db_file)
    await db_manager.initialize()

    risk_config = RiskConfig(
        max_concurrent_positions=3,
        risk_per_trade_pct=0.01,
        min_net_reward_risk=1.50,
    )
    orchestrator = PipelineOrchestrator(
        scout=ScoutAgent(),
        analyst=AnalystAgent(),
        sniper=SniperAgent(),
        risk=RiskAgent(risk_config),
        db_manager=db_manager,
        default_equity_usdt=10000.0,
    )

    cand = make_clean_candidate()
    result = await orchestrator.execute(cand)

    # Query agent_runs table
    rows = await db_manager.fetch_all(
        "SELECT pipeline_run_id, status, final_stage_reached FROM agent_runs WHERE pipeline_run_id = ?",
        (result.pipeline_run_id,),
    )
    await db_manager.close()

    assert len(rows) == 1
    assert rows[0][0] == result.pipeline_run_id
    assert rows[0][1] == PipelineStatus.APPROVED.name
    assert rows[0][2] == PipelineStage.RISK.name
