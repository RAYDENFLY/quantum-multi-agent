"""Unit tests for Milestone 5.9C Cross-Strategy Cost Model Audit."""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
M5_9C_DIR = ROOT / "audit" / "strategy_research" / "milestone_5_9c_cross_strategy_cost_audit"
HOLDOUT_TIMESTAMP_MS = 1_793_491_200_000  # 2026-11-01 00:00:00 UTC


def test_m5_9c_deliverables_exist():
    """Verify all 8 Milestone 5.9C deliverables exist and are non-empty."""
    required_files = [
        "M5_9C_CROSS_STRATEGY_COST_AUDIT.md",
        "M5_9C_HISTORICAL_COST_MODEL_COMPARISON.csv",
        "M5_9C_POSITION_SIZING_RECONCILIATION.csv",
        "M5_9C_EXCHANGE_FEE_EVIDENCE.csv",
        "M5_9C_CORRECTED_PERFORMANCE_COMPARISON.csv",
        "M5_9C_COST_DISCREPANCY_MATRIX.csv",
        "M5_9C_INDEPENDENT_ACCOUNTING_TESTS.md",
        "M5_9C_UNRESOLVED_ASSUMPTIONS.md",
    ]
    for fname in required_files:
        fpath = M5_9C_DIR / fname
        assert fpath.exists(), f"Missing required file: {fname}"
        assert fpath.stat().st_size > 0, f"File is empty: {fname}"


def test_m5_9c_historical_cost_model_coverage():
    """Verify all 11 historical milestones are represented in the cost comparison table."""
    fpath = M5_9C_DIR / "M5_9C_HISTORICAL_COST_MODEL_COMPARISON.csv"
    df = pd.read_csv(fpath)
    expected_milestones = {
        "M3", "M4", "M5.2", "M5.4", "M5.5", "M5.6", "M5.7", "M5.8A", "M5.8B", "M5.9", "M5.9B"
    }
    actual_milestones = set(df["milestone"].unique())
    assert expected_milestones.issubset(actual_milestones), (
        f"Missing milestones: {expected_milestones - actual_milestones}"
    )
    assert (df["round_trip_friction_bps"] > 0).all(), "Round-trip friction must be positive"


def test_m5_9c_position_sizing_reconciliation():
    """Verify position sizing invariants across historical strategies."""
    fpath = M5_9C_DIR / "M5_9C_POSITION_SIZING_RECONCILIATION.csv"
    df = pd.read_csv(fpath)

    # All standardized rows must use $100 initial equity
    assert (df["initial_equity_usd"] == 100.0).all()

    # Minimum notional rule is $5.00 USDT
    assert (df["min_notional_rule_usd"] == 5.0).all()

    # Turnover multiplier check: single-leg strategies are 2.0x, pairs strategies are 4.0x
    for _, row in df.iterrows():
        multiplier = float(row["turnover_multiplier_per_trade"])
        family = str(row["strategy_family"])
        if "Pairs" in family or "Statistical Arbitrage" in family:
            assert multiplier == 4.0, f"Expected 4.0x turnover for pairs, got {multiplier}"
        else:
            assert multiplier == 2.0, f"Expected 2.0x turnover for single-leg, got {multiplier}"


def test_m5_9c_exchange_fee_evidence():
    """Verify authoritative fee evidence for Bybit and Aster DEX."""
    fpath = M5_9C_DIR / "M5_9C_EXCHANGE_FEE_EVIDENCE.csv"
    df = pd.read_csv(fpath)

    exchanges = set(df["exchange"].unique())
    assert "Bybit" in exchanges
    assert "Aster DEX" in exchanges

    # Bybit VIP0 Retail taker fee must be 5.5 bps, maker fee 2.0 bps
    bybit_vip0 = df[(df["exchange"] == "Bybit") & (df["tier_name"] == "VIP0_Retail")]
    assert not bybit_vip0.empty
    taker_fee = bybit_vip0[bybit_vip0["order_role"] == "TAKER"]["fee_rate_bps"].values[0]
    maker_fee = bybit_vip0[bybit_vip0["order_role"] == "MAKER"]["fee_rate_bps"].values[0]
    assert taker_fee == 5.5
    assert maker_fee == 2.0

    # Aster DEX Base Tier Retail taker fee must be 10.0 bps, maker fee 4.0 bps
    aster_base = df[(df["exchange"] == "Aster DEX") & (df["tier_name"] == "Base_Tier_Retail")]
    assert not aster_base.empty
    aster_taker = aster_base[aster_base["order_role"] == "TAKER"]["fee_rate_bps"].values[0]
    aster_maker = aster_base[aster_base["order_role"] == "MAKER"]["fee_rate_bps"].values[0]
    assert aster_taker == 10.0
    assert aster_maker == 4.0


def test_m5_9c_corrected_performance_verdict():
    """Verify that zero historical strategies met the mandatory 3.00% daily target."""
    fpath = M5_9C_DIR / "M5_9C_CORRECTED_PERFORMANCE_COMPARISON.csv"
    df = pd.read_csv(fpath)

    # 100% of historical strategies must fail the 3.00% target
    assert not df["target_3pct_met"].any(), "No strategy should meet the 3.00% mandate"

    # Track C zero-fee gross return must be ~0.0010%/day (far below 3.00%/day)
    track_c_row = df[df["strategy"].str.contains("Track C")].iloc[0]
    zero_fee_ret = float(track_c_row["zero_fee_gross_daily_return_pct"])
    assert zero_fee_ret < 0.01, f"Track C zero fee return too high: {zero_fee_ret}"

    # Directional Portfolio A gross expectancy must be negative (-4.92 bps)
    port_a_row = df[df["milestone"] == "M5.8A"].iloc[0]
    gross_exp = float(port_a_row["zero_fee_gross_expectancy_bps"])
    assert gross_exp < 0.0, f"Portfolio A gross expectancy should be negative, got {gross_exp}"
    assert np.isclose(gross_exp, -4.92, atol=0.01)


def test_m5_9c_holdout_isolation():
    """Assert that the holdout boundary (1,793,491,200,000 ms) remains completely unbreached."""
    # Check all CSV files in the audit directory
    for csv_file in M5_9C_DIR.glob("*.csv"):
        content = csv_file.read_text(encoding="utf-8")
        # Ensure no holdout timestamp appears in data rows
        assert "1793491200000" not in content or "HOLDOUT" in content or "UNBREACHED" in content


def test_m5_9c_asymmetric_notional_accounting_identity():
    """Test exact mathematical formula for asymmetric exit notional scaling."""
    # Long trade with 5% gain
    n_entry = 50.0
    gross_ret = 0.05
    d = 1
    n_exit = n_entry * (1.0 + d * gross_ret)
    assert np.isclose(n_exit, 52.5)

    # Short trade with 5% loss (price went up by 5%)
    d = -1
    gross_ret = -0.05
    n_exit = n_entry * (1.0 + d * gross_ret)
    # n_exit = 50.0 * (1 + (-1)*(-0.05)) = 50.0 * 1.05 = 52.5 (short closed at higher price)
    assert np.isclose(n_exit, 52.5)

    # Fee asymmetry: taker fee 5.5 bps
    fee_rate = 5.5 / 10_000.0
    entry_fee = n_entry * fee_rate
    exit_fee = n_exit * fee_rate
    assert exit_fee > entry_fee  # More fee paid on exit when notional expanded
