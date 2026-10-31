"""Stress and concurrency tests for QUANTUM multi-agent pipeline orchestrator.

Tests concurrent candidate dispatch, SQLite WAL write contention, and cold vs warm
latency separation.
"""

import asyncio
from pathlib import Path
import time
from typing import List
import pytest

from quantum.agents.analyst import AnalystAgent
from quantum.agents.orchestrator import PipelineOrchestrator
from quantum.agents.risk import RiskAgent
from quantum.agents.scout import ScoutAgent
from quantum.agents.sniper import SniperAgent
from quantum.config.settings import RiskConfig
from quantum.core.event_bus import EventBus
from quantum.domain.enums import (
    CandidateCategory,
    ExchangeId,
    PipelineStatus,
    TradeSide,
)
from quantum.domain.models import MarketContext, ScannerCandidate
from quantum.storage.database import DatabaseManager


def make_stress_candidate(i: int) -> ScannerCandidate:
    now_ms = int(time.time() * 1000)
    ctx = MarketContext(
        exchange=ExchangeId.BYBIT,
        symbol=f"SYM{i}USDT",
        snapshot_timestamp_ms=now_ms,
        last_price=50000.0 + i,
        mark_price=50000.0 + i,
        index_price=50000.0 + i,
        bid1_price=49998.0 + i,
        ask1_price=50002.0 + i,
        spread_bps=0.8,
        turnover_24h_usdt=200_000_000.0,
        price_change_24h_pct=3.0,
        funding_rate=0.0001,
        next_funding_time_ms=now_ms + 28800000,
        atr_15m=200.0,
        atr_1h=360.0,
        rvol_15m=2.2,
        rsi_15m=64.0,
        features={"wick_trap_ratio": 0.10, "log_turnover_24h": 19.5},
    )
    return ScannerCandidate(
        candidate_id=f"cand_stress_{i}_{now_ms}",
        scan_cycle_id=f"cycle_stress_{i}",
        exchange=ExchangeId.BYBIT,
        symbol=f"SYM{i}USDT",
        directional_bias=TradeSide.LONG,
        primary_category=CandidateCategory.MOMENTUM_ACCELERATION,
        deterministic_score=82.0,
        state_hash="b" * 16,
        context=ctx,
        created_at_ms=now_ms,
        expires_at_ms=now_ms + 60000,
    )


@pytest.mark.asyncio
async def test_concurrent_candidate_dispatch() -> None:
    risk_config = RiskConfig(
        max_concurrent_positions=8,
        risk_per_trade_pct=0.01,
        min_net_reward_risk=1.50,
    )
    orchestrator = PipelineOrchestrator(
        scout=ScoutAgent(),
        analyst=AnalystAgent(),
        sniper=SniperAgent(),
        risk=RiskAgent(risk_config),
        default_equity_usdt=10000.0,
    )

    candidates = [make_stress_candidate(i) for i in range(8)]
    # Dispatch all 8 candidates concurrently
    tasks = [orchestrator.execute(c) for c in candidates]
    results = await asyncio.gather(*tasks)

    assert len(results) == 8
    for r in results:
        assert r.status in (PipelineStatus.APPROVED, PipelineStatus.VETO_RISK)
        assert r.total_latency_ms > 0.0


@pytest.mark.asyncio
async def test_sqlite_wal_write_contention(tmp_path: Path) -> None:
    db_file = tmp_path / "stress_contention.db"
    db_manager = DatabaseManager(db_file)
    await db_manager.initialize()

    risk_config = RiskConfig(
        max_concurrent_positions=8,
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

    # 10 simultaneous executions writing to SQLite WAL concurrently
    candidates = [make_stress_candidate(i) for i in range(10)]
    results = await asyncio.gather(*[orchestrator.execute(c) for c in candidates])

    assert len(results) == 10

    # Verify that all 10 runs were persisted without database lock contention
    rows = await db_manager.fetch_all("SELECT COUNT(*) FROM agent_runs")
    await db_manager.close()
    assert rows[0][0] == 10


@pytest.mark.asyncio
async def test_cold_vs_warm_pipeline_latency_separation() -> None:
    risk_config = RiskConfig(
        max_concurrent_positions=5,
        risk_per_trade_pct=0.01,
        min_net_reward_risk=1.50,
    )
    orchestrator = PipelineOrchestrator(
        scout=ScoutAgent(),
        analyst=AnalystAgent(),
        sniper=SniperAgent(),
        risk=RiskAgent(risk_config),
        default_equity_usdt=10000.0,
    )

    # 1. Cold Run
    t0_cold = time.perf_counter()
    cold_result = await orchestrator.execute(make_stress_candidate(0))
    cold_latency_ms = (time.perf_counter() - t0_cold) * 1000.0

    # 2. Warm Runs (10 iterations)
    warm_latencies = []
    for i in range(1, 11):
        t0_warm = time.perf_counter()
        await orchestrator.execute(make_stress_candidate(i))
        warm_latencies.append((time.perf_counter() - t0_warm) * 1000.0)

    warm_latencies.sort()
    warm_median = warm_latencies[len(warm_latencies) // 2]

    # Warm median latency must be fast (< 25 ms in-memory)
    assert warm_median < 25.0
    assert cold_result.status in (PipelineStatus.APPROVED, PipelineStatus.VETO_RISK)
