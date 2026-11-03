"""
Unit tests for QUANTUM Phase 5.6.2 Strategy Discovery Package (`src/quantum/strategies/`).

Verifies:
1. Deterministic config_hash generation and uniqueness across all 300 configurations
   in Batch 001 (STRAT_001-100), Batch 002 (STRAT_101-200), and Batch 003 (STRAT_201-300).
2. CollaborativeAgentStrategyBridge end-to-end execution across all 6 agents
   (Scout -> Analyst -> Sniper -> Risk -> Banker -> Orchestrator) on $100.00 USD equity.
3. DualDirectorySynchronizer 10-rule synchronization verification between
   `data_backtest/` and `audit/strategy_research/`.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from quantum.domain.enums import TradeSide
from quantum.strategies.agent_bridge import CollaborativeAgentStrategyBridge
from quantum.strategies.generator import (
    generate_batch_001,
    generate_batch_002,
    generate_batch_003,
)
from quantum.strategies.schemas import (
    EntryParameters,
    ExitParameters,
    FailureClassification,
    RiskExecutionParameters,
    StrategyConfiguration,
    StrategyEvaluationResult,
    StrategyFamily,
)
from quantum.strategies.synchronizer import DualDirectorySynchronizer


def test_batch_generation_300_unique_hashes() -> None:
    """Verify Batch 001, 002, and 003 produce 300 distinct strategy IDs and 300 unique SHA-256 config hashes."""
    b1 = generate_batch_001()
    b2 = generate_batch_002(best_batch_1_id="STRAT_006")
    b3 = generate_batch_003(best_batch_2=b2[0])

    assert len(b1) == 100
    assert len(b2) == 100
    assert len(b3) == 100

    all_configs = b1 + b2 + b3
    strat_ids = [c.strategy_id for c in all_configs]
    hashes = [c.config_hash for c in all_configs]

    assert len(set(strat_ids)) == 300
    assert len(set(hashes)) == 300, "All 300 strategy configurations must have unique SHA-256 config_hash values"

    # Check family counts in Batch 001 (20 + 15 + 15 + 15 + 15 + 10 + 10 = 100)
    fam_counts: dict[StrategyFamily, int] = {}
    for c in b1:
        fam_counts[c.family] = fam_counts.get(c.family, 0) + 1
    assert fam_counts[StrategyFamily.LIQUIDITY_MICROSTRUCTURE] == 20
    assert fam_counts[StrategyFamily.MARKET_REGIME_TRANSITIONS] == 15
    assert fam_counts[StrategyFamily.DIRECTIONAL_PREDICTION] == 15
    assert fam_counts[StrategyFamily.VOLATILITY_DYNAMICS] == 15
    assert fam_counts[StrategyFamily.CROSS_ASSET_RELATIONSHIPS] == 15
    assert fam_counts[StrategyFamily.MEAN_REVERSION_BREAKOUT] == 10
    assert fam_counts[StrategyFamily.ADAPTIVE_ENTRY_EXECUTION] == 10


def test_collaborative_agent_bridge_all_six_agents() -> None:
    """Verify CollaborativeAgentStrategyBridge runs Scout, Analyst, Sniper, Risk, Banker, and Orchestrator on $100 USD."""
    cfg = generate_batch_001()[0]
    bridge = CollaborativeAgentStrategyBridge(cfg)

    trace = asyncio.run(
        bridge.evaluate_signal_through_six_agents(
            symbol="SOLUSDT",
            side=TradeSide.LONG,
            mark_price=150.0,
            atr=2.25,
            rvol=1.65,
            rsi=32.0,
            timestamp_ms=1750000000000,
            current_equity_usdt=100.0,
            open_positions_count=0,
            total_exposure_usdt=0.0,
            peak_equity_usdt=100.0,
        )
    )

    assert trace["strategy_id"] == cfg.strategy_id
    assert trace["config_hash"] == cfg.config_hash
    assert "scout_action" in trace
    assert "analyst_action" in trace
    assert "sniper_action" in trace
    assert "risk_decision" in trace
    assert "banker_state" in trace


def test_dual_directory_synchronizer_verification(tmp_path: Path) -> None:
    """Verify DualDirectorySynchronizer persists and verifies 10-rule synchronization."""
    audit_root = tmp_path / "audit"
    backtest_root = tmp_path / "data_backtest"
    sync = DualDirectorySynchronizer(
        audit_root=audit_root,
        backtest_root=backtest_root,
        git_commit="dcc8ceb54d80b1b9685d92236f48b0994610522a",
    )

    cfg = StrategyConfiguration(
        strategy_id="STRAT_001",
        batch_id="batch_001",
        family=StrategyFamily.LIQUIDITY_MICROSTRUCTURE,
        hypothesis="Unit test liquidity flush absorption hypothesis on $100 equity.",
        applicable_assets=("DOGEUSDT", "SOLUSDT", "ADAUSDT", "XRPUSDT"),
        entry=EntryParameters(prob_margin_min=0.25, htf_return_max_bps=-50.0),
        exit=ExitParameters(tp1_multiplier=2.8, sl_multiplier=1.2, horizon_bars=18),
        risk=RiskExecutionParameters(initial_equity_usd=100.0, risk_per_trade_pct=0.025),
    )

    res = StrategyEvaluationResult(
        experiment_id=f"EXP_B001_STRAT_001_{cfg.config_hash[:8]}",
        batch_id="batch_001",
        strategy_id="STRAT_001",
        strategy_version="1.0.0",
        config_hash=cfg.config_hash,
        family=cfg.family,
        hypothesis=cfg.hypothesis,
        applicable_assets=list(cfg.applicable_assets),
        initial_equity_usd=100.0,
        ending_equity_usd=148.50,
        net_cumulative_return_pct=48.50,
        mean_net_daily_return_pct=0.1150,
        geometric_mean_daily_return_pct=0.1085,
        median_net_daily_return_pct=0.0,
        mean_return_per_trade_bps=18.5,
        gross_expectancy_bps=27.5,
        net_expectancy_bps=18.5,
        profit_factor=1.35,
        sharpe_annualized=2.10,
        sortino_annualized=3.20,
        max_drawdown_pct=11.20,
        mean_underwater_drawdown_pct=3.40,
        median_underwater_drawdown_pct=2.80,
        recovery_factor=4.33,
        candidate_signal_count=200,
        executed_trade_count=180,
        missed_min_notional_count=0,
        missed_capacity_count=20,
        execution_fill_rate_pct=90.0,
        win_rate_pct=48.5,
        total_fees_usd=12.40,
        total_funding_usd=1.20,
        total_slippage_usd=0.0,
        total_execution_cost_usd=13.60,
        positive_folds_count=4,
        fold_returns_pct={"fold_1": 10.5, "fold_2": 12.0, "fold_3": 9.8, "fold_4": 11.2},
        per_asset_trade_counts={"DOGEUSDT": 45, "SOLUSDT": 45, "ADAUSDT": 45, "XRPUSDT": 45},
        bootstrap_95_ci_daily_pct=(0.04, 0.19),
        qualified=True,
        failure_classification=FailureClassification.POSITIVE_RETURN_BELOW_TARGET,
        failure_reason="Qualified positive strategy.",
    )

    sync.persist_strategy_experiment(
        cfg=cfg,
        res=res,
        trades=[{"symbol": "SOLUSDT", "net_pnl_usd": 1.25}],
        daily_curve=[{"timestamp_ms": 1738149600000, "equity_usd": 100.0}],
    )
    sync.write_batch_audit_reports(
        batch_id="batch_001",
        configs=[cfg],
        results=[res],
        global_best_before=None,
        global_best_after=res,
        next_batch_plan="Proceed to Batch 002.",
    )

    report = sync.verify_synchronization(expected_count=1)
    assert report["status"] == "SYNCHRONIZED_VERIFIED"
    assert report["verified_manifests_count"] == 1
    assert report["unique_config_hashes_count"] == 1
    assert len(report["mismatches"]) == 0
    assert len(report["missing_files"]) == 0
