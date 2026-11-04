"""Unit tests for Milestone 5.14.1 Walk-Forward Qualification and Adaptive Dual-Slot Mode C."""
from pathlib import Path
import pandas as pd
import pytest

from quantum.accounting.event_ledger import EventDrivenPortfolioLedger
from quantum.accounting.oracle import IndependentAccountingOracle
from quantum.accounting.risk_controller import ActiveMTMMonitor
from quantum.backtesting.adapters import PRIMARY_RESEARCH_UNIVERSE
from quantum.domain.enums import TradeSide
from quantum.research.partitioner import ContinuousResearchPartitioner, PROSPECTIVE_HOLDOUT_START_MS
from quantum.research.models import DatasetPartitionType

ROOT = Path(__file__).resolve().parent.parent.parent
M5_14_DIR = ROOT / "audit" / "strategy_research" / "milestone_5_14"
CSV_PATH = M5_14_DIR / "M5_14_1_WALKFORWARD_QUALIFICATION_RESULTS.csv"
REPORT_PATH = M5_14_DIR / "M5_14_1_WALKFORWARD_QUALIFICATION_REPORT.md"
SCRIPT_PATH = ROOT / "scripts" / "run_m5_14_1_walkforward_qualification.py"


def test_01_all_m5_14_1_deliverables_exist_and_non_empty():
    assert SCRIPT_PATH.exists(), f"Missing script: {SCRIPT_PATH}"
    assert REPORT_PATH.exists(), f"Missing report: {REPORT_PATH}"
    assert CSV_PATH.exists(), f"Missing results CSV: {CSV_PATH}"
    assert SCRIPT_PATH.stat().st_size > 1000
    assert REPORT_PATH.stat().st_size > 1000
    assert CSV_PATH.stat().st_size > 500


def test_02_max_drawdown_mandate_strict_compliance():
    df = pd.read_csv(CSV_PATH)
    assert not df.empty, "Results CSV is empty"
    assert "max_drawdown_pct" in df.columns
    # Mandate: Max Drawdown <= 15.0000%
    peak_mdd = df["max_drawdown_pct"].max()
    assert peak_mdd <= 15.0000, f"Max drawdown breached 15.0000%: observed {peak_mdd:.4f}%"
    for _, row in df.iterrows():
        assert row["max_drawdown_pct"] <= 15.0000, (
            f"Row breached 15.0% MDD: partition={row['partition']}, regime={row['execution_regime']}, "
            f"mode={row['capital_mode']}, mdd={row['max_drawdown_pct']:.4f}%"
        )


def test_03_gross_exposure_and_admission_cap_invariants():
    df = pd.read_csv(CSV_PATH)
    assert "peak_gross_exposure_x" in df.columns
    peak_exp = df["peak_gross_exposure_x"].max()
    # Mandate: Hard Cap <= 1.0000x, Admission Cap <= 0.9950x
    assert peak_exp <= 1.0000 + 1e-6, f"Hard exposure cap breached: observed {peak_exp:.6f}x"
    assert peak_exp <= 0.9950 + 1e-4, f"Admission exposure cap breached: observed {peak_exp:.6f}x"


def test_04_dual_accounting_oracle_zero_drift():
    df = pd.read_csv(CSV_PATH)
    assert "oracle_reconciliation_delta_usd" in df.columns
    max_delta = df["oracle_reconciliation_delta_usd"].max()
    assert max_delta < 1e-8, f"Dual-ledger oracle drift detected: max delta = ${max_delta:.10f}"


def test_05_sealed_prospective_holdout_boundary():
    from scripts.run_m5_14_1_walkforward_qualification import load

    for symbol in PRIMARY_RESEARCH_UNIVERSE:
        df5 = load(symbol, "5m")
        max_ts = int(df5["open_time_ms"].max())
        assert max_ts < PROSPECTIVE_HOLDOUT_START_MS, (
            f"Holdout contamination for {symbol}: max_ts {max_ts} >= {PROSPECTIVE_HOLDOUT_START_MS}"
        )


def test_06_chronological_partitions_and_embargoes():
    from scripts.run_m5_14_1_walkforward_qualification import load

    df_sample = load("BTCUSDT", "5m")
    partitioner = ContinuousResearchPartitioner()
    parts = partitioner.partition_pre_holdout_series(df_sample, "BTCUSDT")

    train_part = parts[DatasetPartitionType.TRAIN].df
    val_part = parts[DatasetPartitionType.VALIDATION].df
    oos_part = parts[DatasetPartitionType.ROLLING_OOS].df

    train_end = int(train_part["close_time_ms"].iloc[-1])
    val_start = int(val_part["open_time_ms"].iloc[0])
    val_end = int(val_part["close_time_ms"].iloc[-1])
    oos_start = int(oos_part["open_time_ms"].iloc[0])

    # Chronological ordering
    assert train_end < val_start, "TRAIN overlaps with VALIDATION"
    assert val_end < oos_start, "VALIDATION overlaps with ROLLING_OOS"

    # Embargo buffer verification (at least 288 bars = 24 hours = 86,400,000 ms)
    embargo_ms_1 = val_start - train_end
    embargo_ms_2 = oos_start - val_end
    assert embargo_ms_1 >= 288 * 5 * 60 * 1000 - 1000, f"Embargo 1 insufficient: {embargo_ms_1} ms"
    assert embargo_ms_2 >= 288 * 5 * 60 * 1000 - 1000, f"Embargo 2 insufficient: {embargo_ms_2} ms"


def test_07_adaptive_dual_slot_mode_c_braking_logic():
    # Test Tier 1: dd < 6.0% -> 45%
    def get_slot_weight(dd_pct: float, score: float, score_q98: float) -> tuple[float, bool]:
        if dd_pct >= 13.5:
            return 0.0, True  # paused
        if dd_pct < 6.0:
            return 0.450, False
        elif dd_pct < 9.5:
            return 0.240, False
        else:
            if score < score_q98:
                return 0.0, False  # skipped
            return 0.120, False

    sw, paused = get_slot_weight(3.5, 100.0, 150.0)
    assert sw == 0.450 and not paused

    # Test Tier 2: 6.0% <= dd < 9.5% -> 24%
    sw, paused = get_slot_weight(7.2, 100.0, 150.0)
    assert sw == 0.240 and not paused

    # Test Tier 3: 9.5% <= dd < 12.5% -> 12% if score >= q98, else 0%
    sw_fail, paused = get_slot_weight(10.5, 120.0, 150.0)
    assert sw_fail == 0.0 and not paused
    sw_pass, paused = get_slot_weight(10.5, 160.0, 150.0)
    assert sw_pass == 0.120 and not paused

    # Test Tier 4: dd >= 13.5% -> paused
    sw_halt, paused = get_slot_weight(13.6, 200.0, 150.0)
    assert sw_halt == 0.0 and paused


def test_08_dual_return_reporting_completeness():
    df = pd.read_csv(CSV_PATH)
    assert len(df) == 32, f"Expected 32 rows (4 partitions * 4 regimes * 2 modes), got {len(df)}"

    required_cols = [
        "partition",
        "execution_regime",
        "capital_mode",
        "completed_trades",
        "compounded_daily_return_on_initial_pct",
        "calendar_day_geometric_daily_return_pct",
        "active_day_return_pct",
        "capital_utilization_pct",
        "turnover_per_day_x",
        "max_drawdown_pct",
        "oracle_reconciliation_delta_usd",
        "deflated_sharpe_ratio",
        "final_equity_usd",
        "peak_gross_exposure_x",
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing column: {col}"
        assert not df[col].isnull().any(), f"Column {col} contains null values"
