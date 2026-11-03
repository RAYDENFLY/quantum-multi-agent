"""Unit tests for Milestone 5.9D Trade Frequency & Holding Duration Forensic Audit."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
M5_9D_DIR = ROOT / "audit" / "strategy_research" / "milestone_5_9d_frequency_duration_audit"
HOLDOUT_TIMESTAMP_MS = 1_793_491_200_000  # 2026-11-01 00:00:00 UTC


def test_m5_9d_deliverables_exist():
    """Verify all Milestone 5.9D deliverables exist and are non-empty."""
    required_files = [
        "M5_9D_TRADE_FREQUENCY_AUDIT.md",
        "M5_9D_TRADE_HOLDING_DURATION.csv",
        "M5_9D_SIGNAL_TO_EXECUTION_RECONCILIATION.csv",
    ]
    for fname in required_files:
        fpath = M5_9D_DIR / fname
        assert fpath.exists(), f"Missing required file: {fname}"
        assert fpath.stat().st_size > 0, f"File is empty: {fname}"


def test_m5_9d_trade_count_and_execution_events():
    """Verify the 19 trade episodes and 76 individual execution events."""
    fpath = M5_9D_DIR / "M5_9D_TRADE_HOLDING_DURATION.csv"
    df = pd.read_csv(fpath)

    # Exactly 19 completed trade episodes
    assert len(df) == 19

    # Each episode consists of 4 individual execution events
    assert (df["individual_execution_events_count"] == 4).all()
    assert df["individual_execution_events_count"].sum() == 76

    # Verify PnL arithmetic matches M5.9B ledger
    total_gross = df["pair_gross_pnl_usd"].sum()
    total_net = df["pair_net_pnl_usd"].sum()
    assert np.isclose(total_gross, 0.3663, atol=0.01)
    assert np.isclose(total_net, -0.9370, atol=0.01)


def test_m5_9d_holding_duration_metrics():
    """Verify holding duration conversions and distribution statistics."""
    fpath = M5_9D_DIR / "M5_9D_TRADE_HOLDING_DURATION.csv"
    df = pd.read_csv(fpath)

    # Units consistency: days -> hours -> minutes
    assert (df["holding_hours"] == df["holding_days"] * 24).all()
    assert (df["holding_minutes"] == df["holding_hours"] * 60).all()

    # Distribution statistics
    durations = df["holding_days"].values
    assert np.isclose(np.mean(durations), 7.6842, atol=0.01)
    assert np.median(durations) == 6.0
    assert np.min(durations) == 1
    assert np.max(durations) == 24
    assert np.sum(durations) == 146


def test_m5_9d_signal_reconciliation_identity():
    """Verify complete mathematical reconciliation across all 365 calendar days."""
    fpath = M5_9D_DIR / "M5_9D_SIGNAL_TO_EXECUTION_RECONCILIATION.csv"
    df = pd.read_csv(fpath)

    # Exactly 365 calendar days in evaluation period
    assert len(df) == 365

    reasons = df["rejection_or_skip_reason"].value_counts().to_dict()
    warmup_count = reasons.get("WARMUP_WINDOW_30_DAYS", 0)
    executed_count = reasons.get("EXECUTED_SUCCESSFULLY", 0)
    blocked_count = reasons.get("REJECTED_ALREADY_IN_POSITION", 0)
    below_thresh_count = reasons.get("BELOW_ENTRY_THRESHOLD_2_SIGMA", 0)

    assert warmup_count == 30
    assert executed_count == 19
    assert blocked_count == 30
    assert below_thresh_count == 286

    # Arithmetic partition sum must equal 365
    assert (warmup_count + executed_count + blocked_count + below_thresh_count) == 365

    # Concurrent positions must never exceed 1 pair
    assert (df["concurrent_open_positions"] <= 1).all()


def test_m5_9d_exit_reasons_and_asymmetric_duration():
    """Verify that mean reversion trades hold significantly longer than stop-loss trades."""
    fpath = M5_9D_DIR / "M5_9D_TRADE_HOLDING_DURATION.csv"
    df = pd.read_csv(fpath)

    mr_trades = df[df["exit_reason"] == "MEAN_REVERSION_EXIT"]
    sl_trades = df[df["exit_reason"] == "STOP_LOSS_DIVERGENCE"]

    assert len(mr_trades) == 10
    assert len(sl_trades) == 9

    # Mean reversion trades take longer (mean 12.0 days vs 2.89 days)
    assert mr_trades["holding_days"].mean() == 12.0
    assert np.isclose(sl_trades["holding_days"].mean(), 2.8889, atol=0.01)

    # Mean reversion trades are net profitable, stop-outs are net losing
    assert mr_trades["pair_net_pnl_usd"].sum() > 0.0
    assert sl_trades["pair_net_pnl_usd"].sum() < 0.0


def test_m5_9d_holdout_boundary_isolation():
    """Assert that the holdout boundary remains completely unbreached."""
    for csv_file in M5_9D_DIR.glob("*.csv"):
        df = pd.read_csv(csv_file)
        if "timestamp_ms" in df.columns:
            assert (df["timestamp_ms"] < HOLDOUT_TIMESTAMP_MS).all()
        if "entry_timestamp_ms" in df.columns:
            assert (df["entry_timestamp_ms"] < HOLDOUT_TIMESTAMP_MS).all()
        if "exit_timestamp_ms" in df.columns:
            assert (df["exit_timestamp_ms"] < HOLDOUT_TIMESTAMP_MS).all()
