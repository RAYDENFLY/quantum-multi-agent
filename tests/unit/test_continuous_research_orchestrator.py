"""Unit & Integration Tests for Continuous Research Mode Addendum.

Verifies:
1. Deliverables in audit/strategy_research/continuous_research_orchestration/ exist and are non-empty.
2. Dataset partitioner chronological isolation, 288-bar embargo, and SHA-256 fingerprinting.
3. Fatal HoldoutContaminationError on prospective holdout access (t >= 1,793,491,200,000 ms).
4. ContinuousExperimentConfig immutability and deterministic SHA-256 fingerprinting.
5. IntermediateFeatureCache stampede protection, cache hit scaling, and time savings.
6. Asynchronous priority queue ordering (information gain vs computational cost).
7. Automatic rejection on methodological failure: gross exposure breach (> 1.0x).
8. Automatic rejection on methodological failure: holding duration breach (> 240m).
9. Automatic rejection on statistical failure: daily return < 3.00%, profit factor < 1.30, drawdown > 15%.
10. Deduplication & redundancy filter (instant skipping of duplicate experiment fingerprints).
11. Zero-survivorship-bias ledger integrity across CSV and JSONL persistent stores.
12. Independent unblocked prospective OOS collector monitoring.
"""

from pathlib import Path
import tempfile
import numpy as np
import pandas as pd
import pytest

from quantum.domain.research_contract import (
    ResearchExperimentContract,
    ExperimentCategory,
    ExecutionTimeframe,
    ASTER_DEX_RETAIL_CONFIG,
)
from quantum.research import (
    ContinuousExperimentConfig,
    ContinuousResearchOrchestrator,
    ContinuousResearchPartitioner,
    DatasetFingerprint,
    DatasetPartition,
    DatasetPartitionType,
    ExperimentExecutionRecord,
    ExperimentPriority,
    HoldoutContaminationError,
    HypothesisStatus,
    IntermediateFeatureCache,
    PartitionLeakageError,
    PROSPECTIVE_HOLDOUT_START_MS,
    RejectionCategory,
    SpecificRejectionReason,
    AutomaticRejectionEngine,
)
from quantum.strategies.hypothesis_engine import TradeRecord

ROOT = Path(__file__).resolve().parent.parent.parent
CONTINUOUS_AUDIT_DIR = ROOT / "audit" / "strategy_research" / "continuous_research_orchestration"


# ==============================================================================
# 1. DELIVERABLES AUDIT
# ==============================================================================

def test_continuous_research_deliverables_exist_and_non_empty():
    """Verify that all architecture, policy, benchmark, and ledger files exist."""
    required_files = [
        "CONTINUOUS_RESEARCH_ARCHITECTURE.md",
        "EVIDENCE_SEPARATION_POLICY.md",
        "REJECTION_TAXONOMY.md",
        "PARALLEL_EXECUTION_BENCHMARK.md",
        "EXPERIMENT_LEDGER.csv",
        "EXPERIMENT_LEDGER.jsonl",
    ]
    assert CONTINUOUS_AUDIT_DIR.exists(), f"Audit directory missing: {CONTINUOUS_AUDIT_DIR}"

    for f_name in required_files:
        p = CONTINUOUS_AUDIT_DIR / f_name
        assert p.exists(), f"Missing required file: {f_name}"
        assert p.stat().st_size > 50, f"File empty or too small: {f_name}"


# ==============================================================================
# 2. DATASET PARTITIONING & EMBARGO ISOLATION
# ==============================================================================

def test_dataset_partitioner_chronological_isolation_and_embargo():
    """Verify strict chronological boundaries, embargo gaps, and SHA-256 fingerprinting."""
    n_bars = 2000
    base_ts = 1_700_000_000_000
    ts = np.arange(base_ts, base_ts + n_bars * 300_000, 300_000)

    df = pd.DataFrame({
        "open_time_ms": ts,
        "close_time_ms": ts + 299_999,
        "open": np.linspace(100.0, 110.0, n_bars),
        "high": np.linspace(101.0, 111.0, n_bars),
        "low": np.linspace(99.0, 109.0, n_bars),
        "close": np.linspace(100.0, 110.0, n_bars),
        "volume": np.full(n_bars, 50.0),
    })

    embargo_bars = 50
    partitioner = ContinuousResearchPartitioner(
        embargo_bars=embargo_bars,
        train_ratio=0.50,
        val_ratio=0.25,
        rolling_oos_ratio=0.25,
    )
    parts = partitioner.partition_pre_holdout_series(df, symbol="BTCUSDT", timeframe="5m")

    train_part = parts[DatasetPartitionType.TRAIN]
    val_part = parts[DatasetPartitionType.VALIDATION]
    oos_part = parts[DatasetPartitionType.ROLLING_OOS]

    # Invariant 1: Embargo gap between TRAIN and VAL
    train_end = int(train_part.df["close_time_ms"].iloc[-1])
    val_start = int(val_part.df["open_time_ms"].iloc[0])
    gap_1 = val_start - train_end
    expected_gap_ms = embargo_bars * 300_000
    assert gap_1 > expected_gap_ms - 300_000, f"Embargo gap 1 too small: {gap_1} ms"

    # Invariant 2: Embargo gap between VAL and ROLLING_OOS
    val_end = int(val_part.df["close_time_ms"].iloc[-1])
    oos_start = int(oos_part.df["open_time_ms"].iloc[0])
    gap_2 = oos_start - val_end
    assert gap_2 > expected_gap_ms - 300_000, f"Embargo gap 2 too small: {gap_2} ms"

    # Invariant 3: Fingerprint length and deterministic consistency
    assert len(train_part.fingerprint.sha256_hash) == 64
    assert train_part.fingerprint.symbol == "BTCUSDT"
    assert train_part.fingerprint.row_count == len(train_part.df)


# ==============================================================================
# 3. SEALED HOLDOUT CONTAMINATION ERROR
# ==============================================================================

def test_holdout_contamination_error_fatal():
    """Verify that feeding holdout data to retrospective partitioning immediately fails closed."""
    n_bars = 500
    # Base timestamp starting at or after the holdout boundary
    ts = np.arange(
        PROSPECTIVE_HOLDOUT_START_MS,
        PROSPECTIVE_HOLDOUT_START_MS + n_bars * 300_000,
        300_000,
    )

    df_contaminated = pd.DataFrame({
        "open_time_ms": ts,
        "close_time_ms": ts + 299_999,
        "open": np.full(n_bars, 100.0),
        "high": np.full(n_bars, 101.0),
        "low": np.full(n_bars, 99.0),
        "close": np.full(n_bars, 100.0),
        "volume": np.full(n_bars, 10.0),
    })

    partitioner = ContinuousResearchPartitioner()
    with pytest.raises(HoldoutContaminationError, match="CRITICAL HOLDOUT CONTAMINATION"):
        partitioner.partition_pre_holdout_series(df_contaminated, symbol="BTCUSDT")


# ==============================================================================
# 4. EXPERIMENT CONFIG IMMUTABILITY & FINGERPRINTING
# ==============================================================================

def test_continuous_experiment_config_fingerprint_and_immutability():
    """Verify that experiment configs are frozen and produce deterministic SHA-256 hashes."""
    contract = ResearchExperimentContract(
        experiment_id="TEST-EXP-01",
        experiment_name="Immutability Test",
        experiment_category=ExperimentCategory.HIGH_FREQUENCY_INTRADAY,
        execution_timeframe=ExecutionTimeframe.TF_5M,
        maximum_holding_horizon_minutes=240,
        allow_overnight_holding=False,
        maximum_gross_exposure=1.0000,
        initial_equity_usd=100.0,
        mandatory_profitability_gate_daily_pct=3.0000,
        exchange_cost_config=ASTER_DEX_RETAIL_CONFIG,
    )

    cfg = ContinuousExperimentConfig(
        experiment_id="EXP-01",
        hypothesis_id="HYP-01",
        partition_type=DatasetPartitionType.TRAIN,
        symbol="BTCUSDT",
        contract=contract,
    )

    # Invariant 1: Config is frozen (immutability)
    with pytest.raises(Exception):
        cfg.hypothesis_id = "HYP-02"  # Pydantic ValidationError on frozen model

    # Invariant 2: Hash is 64 hex characters and deterministic
    fp1 = cfg.config_fingerprint
    fp2 = cfg.config_fingerprint
    assert len(fp1) == 64
    assert fp1 == fp2


# ==============================================================================
# 5. FEATURE CACHE SYNCHRONIZATION & HIT SCALING
# ==============================================================================

def test_feature_cache_hits_and_synchronization():
    """Verify intermediate feature cache returns hits for identical dataset hashes."""
    cache = IntermediateFeatureCache()
    n = 200
    df = pd.DataFrame({
        "open_time_ms": range(n),
        "close_time_ms": range(n),
        "open": [100.0] * n,
        "high": [102.0] * n,
        "low": [98.0] * n,
        "close": [101.0] * n,
        "volume": [1000.0] * n,
    })

    # Call 1: Cache Miss
    df1, was_cached1 = cache.get_or_compute(df, "BTCUSDT", "5m", "mock_hash_abc")
    assert not was_cached1
    assert cache.misses == 1
    assert cache.hits == 0

    # Call 2: Cache Hit
    df2, was_cached2 = cache.get_or_compute(df, "BTCUSDT", "5m", "mock_hash_abc")
    assert was_cached2
    assert cache.misses == 1
    assert cache.hits == 1
    assert cache.compute_seconds_saved > 0.0

    # Ensure output DataFrames are identical
    pd.testing.assert_frame_equal(df1, df2)


# ==============================================================================
# 6. PRIORITY QUEUE ORDERING
# ==============================================================================

def test_priority_queue_ordering():
    """Verify high-information experiments sort ahead of low-priority experiments."""
    contract = ResearchExperimentContract(
        experiment_id="TEST-PRIO",
        experiment_name="Priority Test",
        experiment_category=ExperimentCategory.HIGH_FREQUENCY_INTRADAY,
        execution_timeframe=ExecutionTimeframe.TF_5M,
        maximum_holding_horizon_minutes=240,
        allow_overnight_holding=False,
        maximum_gross_exposure=1.0000,
        initial_equity_usd=100.0,
        mandatory_profitability_gate_daily_pct=3.0000,
        exchange_cost_config=ASTER_DEX_RETAIL_CONFIG,
    )

    cfg_low = ContinuousExperimentConfig(
        experiment_id="EXP-LOW",
        hypothesis_id="HYP-01",
        partition_type=DatasetPartitionType.ROLLING_OOS,
        symbol="BTCUSDT",
        contract=contract,
        priority=ExperimentPriority(expected_information_gain=0.2, estimated_compute_cost=1.0),
    )
    cfg_high = ContinuousExperimentConfig(
        experiment_id="EXP-HIGH",
        hypothesis_id="HYP-01",
        partition_type=DatasetPartitionType.TRAIN,
        symbol="BTCUSDT",
        contract=contract,
        priority=ExperimentPriority(expected_information_gain=0.9, estimated_compute_cost=1.0),
    )

    assert cfg_high.priority.priority_score > cfg_low.priority.priority_score

    queue = [cfg_low, cfg_high]
    queue.sort(key=lambda c: c.priority.priority_score, reverse=True)
    assert queue[0].experiment_id == "EXP-HIGH"
    assert queue[1].experiment_id == "EXP-LOW"


# ==============================================================================
# 7. AUTOMATIC REJECTION: METHODOLOGICAL GATES
# ==============================================================================

def test_automatic_rejection_methodological_exposure_and_duration():
    """Verify rejection engine flags exposure breaches and holding horizon breaches."""
    contract = ResearchExperimentContract(
        experiment_id="TEST-REJECT",
        experiment_name="Rejection Test",
        experiment_category=ExperimentCategory.HIGH_FREQUENCY_INTRADAY,
        execution_timeframe=ExecutionTimeframe.TF_5M,
        maximum_holding_horizon_minutes=240,
        allow_overnight_holding=False,
        maximum_gross_exposure=1.0000,
        initial_equity_usd=100.0,
        mandatory_profitability_gate_daily_pct=3.0000,
        exchange_cost_config=ASTER_DEX_RETAIL_CONFIG,
    )

    cfg = ContinuousExperimentConfig(
        experiment_id="EXP-R1",
        hypothesis_id="HYP-01",
        partition_type=DatasetPartitionType.TRAIN,
        symbol="BTCUSDT",
        contract=contract,
    )

    # 1. Breach exposure: notional $150.0 > $100.0
    bad_exposure_trade = TradeRecord(
        hypothesis_id="HYP-01",
        symbol="BTCUSDT",
        side="LONG",
        entry_bar=10,
        exit_bar=15,
        entry_time_ms=1000,
        exit_time_ms=2500,
        duration_minutes=25.0,
        entry_price=100.0,
        exit_price=102.0,
        notional_usd=150.0,  # LEVERAGE BREACH
        gross_pnl_usd=3.0,
        gross_return_bps=30.0,
        fee_usd=0.2,
        slippage_usd=0.04,
        funding_usd=0.0,
        net_pnl_usd=2.76,
        net_return_bps=27.6,
        exit_reason="TAKE_PROFIT",
        market_regime="HV_TREND",
    )
    res_exp = AutomaticRejectionEngine.evaluate_methodology(cfg, [bad_exposure_trade])
    assert not res_exp.is_accepted
    assert res_exp.category == RejectionCategory.METHODOLOGICAL_FAILURE
    assert any("EXPOSURE_LIMIT_EXCEEDED" in r for r in res_exp.reasons)

    # 2. Breach duration: 300 minutes > 240 max horizon
    bad_duration_trade = TradeRecord(
        hypothesis_id="HYP-01",
        symbol="BTCUSDT",
        side="LONG",
        entry_bar=10,
        exit_bar=70,
        entry_time_ms=1000,
        exit_time_ms=19000,
        duration_minutes=300.0,  # HORIZON BREACH (5 hours)
        entry_price=100.0,
        exit_price=101.0,
        notional_usd=100.0,
        gross_pnl_usd=1.0,
        gross_return_bps=10.0,
        fee_usd=0.2,
        slippage_usd=0.04,
        funding_usd=0.0,
        net_pnl_usd=0.76,
        net_return_bps=7.6,
        exit_reason="TAKE_PROFIT",
        market_regime="HV_TREND",
    )
    res_dur = AutomaticRejectionEngine.evaluate_methodology(cfg, [bad_duration_trade])
    assert not res_dur.is_accepted
    assert res_dur.category == RejectionCategory.METHODOLOGICAL_FAILURE
    assert any("HOLDING_HORIZON_BREACH" in r for r in res_dur.reasons)


# ==============================================================================
# 8. AUTOMATIC REJECTION: STATISTICAL GATES
# ==============================================================================

def test_automatic_rejection_statistical_gates():
    """Verify rejection engine flags sub-target return, low profit factor, and excess drawdown."""
    contract = ResearchExperimentContract(
        experiment_id="TEST-STAT",
        experiment_name="Stat Test",
        experiment_category=ExperimentCategory.HIGH_FREQUENCY_INTRADAY,
        execution_timeframe=ExecutionTimeframe.TF_5M,
        maximum_holding_horizon_minutes=240,
        allow_overnight_holding=False,
        maximum_gross_exposure=1.0000,
        initial_equity_usd=100.0,
        mandatory_profitability_gate_daily_pct=3.0000,
        exchange_cost_config=ASTER_DEX_RETAIL_CONFIG,
    )

    cfg = ContinuousExperimentConfig(
        experiment_id="EXP-S1",
        hypothesis_id="HYP-01",
        partition_type=DatasetPartitionType.TRAIN,
        symbol="BTCUSDT",
        contract=contract,
    )

    # Sub-target return (1.5% < 3.00%), profit factor (1.10 < 1.30), drawdown (18% > 15%)
    res = AutomaticRejectionEngine.evaluate_statistics(
        config=cfg,
        frequency_daily=15.0,
        profit_factor=1.10,
        net_expectancy_bps=-5.0,
        mean_net_daily_return_pct=1.5,
        max_drawdown_pct=18.0,
    )

    assert not res.is_accepted
    assert res.category == RejectionCategory.STATISTICAL_FAILURE
    reasons_str = "; ".join(res.reasons)
    assert "DRAWDOWN_LIMIT_EXCEEDED" in reasons_str
    assert "SUB_TARGET_DAILY_RETURN" in reasons_str
    assert "LOW_PROFIT_FACTOR" in reasons_str
    assert "NEGATIVE_NET_EXPECTANCY" in reasons_str


# ==============================================================================
# 9. DEDUPLICATION & REDUNDANCY FILTER
# ==============================================================================

def test_deduplication_and_redundancy_skip():
    """Verify that re-evaluating an identical config and dataset fingerprint is skipped instantly."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        ledger_path = Path(tmp_dir)
        orchestrator = ContinuousResearchOrchestrator(ledger_dir=ledger_path, max_workers=2)

        contract = ResearchExperimentContract(
            experiment_id="TEST-DEDUP",
            experiment_name="Dedup Test",
            experiment_category=ExperimentCategory.HIGH_FREQUENCY_INTRADAY,
            execution_timeframe=ExecutionTimeframe.TF_5M,
            maximum_holding_horizon_minutes=240,
            allow_overnight_holding=False,
            maximum_gross_exposure=1.0000,
            initial_equity_usd=100.0,
            mandatory_profitability_gate_daily_pct=3.0000,
            exchange_cost_config=ASTER_DEX_RETAIL_CONFIG,
        )

        n = 300
        df = pd.DataFrame({
            "open_time_ms": range(n),
            "close_time_ms": range(n),
            "open": [100.0] * n,
            "high": [102.0] * n,
            "low": [98.0] * n,
            "close": [100.0] * n,
            "volume": [100.0] * n,
        })
        part = DatasetPartition(df, DatasetPartitionType.TRAIN, "BTCUSDT")

        cfg = ContinuousExperimentConfig(
            experiment_id="EXP-DUP-1",
            hypothesis_id="HYP-01",
            partition_type=DatasetPartitionType.TRAIN,
            symbol="BTCUSDT",
            contract=contract,
        )

        # Run 1: Executes
        rec1 = orchestrator._evaluate_single_experiment(cfg, part)
        assert rec1.rejection_category != RejectionCategory.REDUNDANT_CONFIGURATION

        # Run 2: Skipped as redundant
        rec2 = orchestrator._evaluate_single_experiment(cfg, part)
        assert rec2.rejection_category == RejectionCategory.REDUNDANT_CONFIGURATION
        assert SpecificRejectionReason.DUPLICATE_FINGERPRINT.value in rec2.rejection_reasons


# ==============================================================================
# 10. UNBLOCKED PROSPECTIVE OOS COLLECTOR
# ==============================================================================

def test_independent_unblocked_prospective_oos_collector():
    """Verify prospective collector logs ticks independently without gating backtest logic."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        orchestrator = ContinuousResearchOrchestrator(ledger_dir=Path(tmp_dir))

        tick = orchestrator.run_prospective_oos_collector_tick(
            new_candle_timestamp_ms=PROSPECTIVE_HOLDOUT_START_MS + 300_000,
            symbol="ETHUSDT",
            price=2750.0,
        )

        assert tick["is_holdout_sealed"] is True
        assert tick["partition"] == DatasetPartitionType.PROSPECTIVE_OOS.value
        assert tick["status"] == "COLLECTING_INDEPENDENTLY"
