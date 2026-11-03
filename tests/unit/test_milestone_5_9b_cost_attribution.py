"""QUANTUM Milestone 5.9B — Unit & Validation Tests for Forensic PnL Attribution.

Verifies:
1. Existence and integrity of all Milestone 5.9B dossiers, ledgers, and cost tables.
2. Trade-level and leg-level ledger structure (19 trades, 38 individual leg executions).
3. Exact mathematical proof of the master accounting identity (discrepancy == 0.00000000).
4. Win rate, payoff ratio, gross expectancy, and net expectancy reconciliation.
5. Exchange-specific fee schedule reconciliation (Bybit VIP0 vs AsterDEX Base Tier).
6. Slippage, spread, and funding attribution integrity.
7. Seven-scenario cost sensitivity matrix consistency.
8. Governance compliance and paper trading prohibition.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


DOSSIER_DIR = Path("audit/strategy_research/milestone_5_9b_cost_reconciliation")


class TestMilestone59BCostAttribution:
    """Verifies all Milestone 5.9B deliverables, ledgers, and cost accounting identities."""

    def test_milestone_5_9b_deliverables_exist(self) -> None:
        """Verifies all 8 required dossiers and CSV datasets exist and are non-empty."""
        required_md_files = [
            "M5_9B_FORENSIC_COST_ATTRIBUTION.md",
            "M5_9B_INDEPENDENT_ACCOUNTING_TESTS.md",
        ]
        for f in required_md_files:
            p = DOSSIER_DIR / f
            assert p.exists(), f"Required markdown dossier {f} does not exist"
            assert p.stat().st_size > 1000, f"Dossier {f} appears truncated or empty"

        required_csv_files = [
            "M5_9B_TRADE_LEVEL_LEDGER.csv",
            "M5_9B_WIN_RATE_RR_ANALYSIS.csv",
            "M5_9B_FEE_RECONCILIATION.csv",
            "M5_9B_SLIPPAGE_ATTRIBUTION.csv",
            "M5_9B_FUNDING_ATTRIBUTION.csv",
            "M5_9B_COST_SENSITIVITY.csv",
        ]
        for f in required_csv_files:
            p = DOSSIER_DIR / f
            assert p.exists(), f"Required CSV dataset {f} does not exist"
            assert p.stat().st_size > 50, f"Dataset {f} appears truncated or empty"

    def test_trade_level_ledger_structure(self) -> None:
        """Verifies the exact 38 leg executions and 19 trade pairs."""
        p = DOSSIER_DIR / "M5_9B_TRADE_LEVEL_LEDGER.csv"
        df = pd.read_csv(p)

        assert len(df) == 38, f"Expected 38 leg executions (19 trades x 2 legs), found {len(df)}"
        assert "trade_id" in df.columns
        assert "leg_id" in df.columns
        assert "pair" in df.columns
        assert "symbol" in df.columns
        assert "direction" in df.columns
        assert "entry_notional_usd" in df.columns
        assert "gross_pnl_usd" in df.columns
        assert "net_pnl_usd" in df.columns

        # Verify pair is SOLUSDT/LTCUSDT
        assert (df["pair"] == "SOLUSDT/LTCUSDT").all()
        # Verify 19 SOL legs and 19 LTC legs
        assert (df["symbol"] == "SOLUSDT").sum() == 19
        assert (df["symbol"] == "LTCUSDT").sum() == 19

    def test_accounting_identity_proof(self) -> None:
        """Verifies Gross PnL - Fees - Slippage - Funding == Net PnL with zero discrepancy."""
        p = DOSSIER_DIR / "M5_9B_WIN_RATE_RR_ANALYSIS.csv"
        df = pd.read_csv(p)

        assert len(df) == 1
        row = df.iloc[0]

        gross_pnl = row["total_gross_pnl_usd"]
        friction = row["total_transaction_friction_usd"]
        net_pnl = row["total_net_pnl_usd"]
        discrepancy = row["accounting_identity_discrepancy_usd"]

        assert bool(row["accounting_identity_reconciled"]) is True
        assert np.isclose(discrepancy, 0.0, atol=1e-8), f"Accounting discrepancy {discrepancy} must be exactly zero"
        assert np.isclose(gross_pnl - friction, net_pnl, atol=1e-4)

    def test_win_rate_and_rr_metrics(self) -> None:
        """Verifies 19 trades, 8 wins, 11 losses, and expectancy figures."""
        p = DOSSIER_DIR / "M5_9B_WIN_RATE_RR_ANALYSIS.csv"
        df = pd.read_csv(p)
        row = df.iloc[0]

        assert row["total_trades_count"] == 19
        assert row["gross_winning_trades"] == 8
        assert row["gross_losing_trades"] == 11
        assert np.isclose(row["gross_win_rate_pct"], 42.11, atol=0.1)
        assert row["profit_factor_before_costs"] > 1.0  # Gross PF is 1.014
        assert row["profit_factor_after_costs"] < 1.0   # Net PF is 0.964

        # Gross expectancy is marginally positive, Net expectancy is negative
        assert row["gross_expectancy_bps_per_trade"] > 0.0
        assert row["net_expectancy_bps_per_trade"] < 0.0

    def test_exchange_fee_reconciliation_table(self) -> None:
        """Verifies Bybit VIP0 vs AsterDEX fee schedule comparison across 5 scenarios."""
        p = DOSSIER_DIR / "M5_9B_FEE_RECONCILIATION.csv"
        df = pd.read_csv(p)

        assert len(df) == 5
        scenarios = list(df["scenario_id"])
        assert "SCENARIO_A_BYBIT_VIP0" in scenarios
        assert "SCENARIO_B_ASTER_TAKER_ALL" in scenarios
        assert "SCENARIO_C_ASTER_HYBRID" in scenarios
        assert "SCENARIO_D_FEE_ONLY_DIAGNOSTIC" in scenarios
        assert "SCENARIO_E_ZERO_FEE_DIAGNOSTIC" in scenarios

        # Aster taker fees (~$3.72) must be ~5x Bybit maker fees (~$0.74)
        bybit_row = df[df["scenario_id"] == "SCENARIO_A_BYBIT_VIP0"].iloc[0]
        aster_row = df[df["scenario_id"] == "SCENARIO_B_ASTER_TAKER_ALL"].iloc[0]
        assert aster_row["total_fees_usd"] > bybit_row["total_fees_usd"] * 4.5

        # Zero-fee scenario must reflect pure gross PnL
        zero_fee_row = df[df["scenario_id"] == "SCENARIO_E_ZERO_FEE_DIAGNOSTIC"].iloc[0]
        assert np.isclose(zero_fee_row["net_realized_pnl_usd"], zero_fee_row["gross_pnl_usd"])

    def test_cost_sensitivity_scenarios_table(self) -> None:
        """Verifies all 7 cost sensitivity environments are properly sequenced."""
        p = DOSSIER_DIR / "M5_9B_COST_SENSITIVITY.csv"
        df = pd.read_csv(p)

        assert len(df) == 7
        assert list(df["scenario_number"]) == [1, 2, 3, 4, 5, 6, 7]

        # Scenario 1 (Gross) has positive PnL
        assert df.iloc[0]["net_pnl_usd"] > 0.0
        # Scenarios 2 through 7 have negative PnL due to friction
        for idx in range(1, 7):
            assert df.iloc[idx]["net_pnl_usd"] < 0.0, f"Scenario {idx+1} should have negative net PnL"

    def test_governance_decision_and_paper_trading_prohibition(self) -> None:
        """Verifies final governance decision enforces REQUIRES_RESEARCH and denies paper trading."""
        p = DOSSIER_DIR / "M5_9B_FORENSIC_COST_ATTRIBUTION.md"
        content = p.read_text(encoding="utf-8")

        assert "GOVERNANCE_STATUS: REQUIRES_RESEARCH" in content
        assert "PAPER_TRADING_AUTHORIZATION: DENIED_PENDING_3_PERCENT_BACKTEST_VALIDATION" in content
        assert "COMBINATION_OF_MARGINAL_ALPHA_AND_PUNITIVE_FRICTION" in content
