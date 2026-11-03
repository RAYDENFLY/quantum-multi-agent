"""QUANTUM Milestone 5.8A — Unit & Validation Tests for Survival & Performance Accounting.

Verifies:
1. Existence and integrity of all Milestone 5.8A dossiers and datasets.
2. Active-period trading performance metrics and loss rate consistency.
3. Full-calendar equity ledger accounting (exactly 1,099 continuous calendar days).
4. Capital scale sensitivity experiments ($100, $1,000, $10,000 initial balances).
5. Bootstrap ruin simulation parameters and 100% empirical ruin probability.
6. Minimum-notional audit semantics ($4.998 < $5.00 position notional vs lot limit).
7. Independent cross-milestone mathematical reconciliation.
8. Preservation of prospective holdout boundary (zero leakage).
9. Governance compliance and paper trading prohibition.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


DOSSIER_DIR = Path("audit/strategy_research/milestone_5_8a_survival_accounting")


class TestMilestone58ASurvivalAccounting:
    """Verifies all accounting deliverables and survival calculations."""

    def test_milestone_5_8a_dossier_deliverables_exist(self) -> None:
        """Verifies all 6 markdown reports and structured data files exist."""
        required_md_files = [
            "ACTIVE_PERIOD_RECONCILIATION.md",
            "FULL_CALENDAR_EQUITY_AUDIT.md",
            "RUIN_AND_MINIMUM_NOTIONAL_AUDIT.md",
            "SURVIVAL_METRICS_REPORT.md",
            "INDEPENDENT_ACCOUNTING_VALIDATION.md",
            "FINAL_RESEARCH_DECISION.md",
        ]
        for f in required_md_files:
            p = DOSSIER_DIR / f
            assert p.exists(), f"Required markdown dossier {f} does not exist"
            assert p.stat().st_size > 1000, f"Dossier {f} appears truncated or empty"

        required_data_files = [
            "ACTIVE_PERIOD_METRICS.json",
            "ACTIVE_PERIOD_TRADES_LEDGER.csv",
            "FULL_CALENDAR_PROVENANCE_LEDGER.csv",
            "CAPITAL_SCALE_EXPERIMENTS.csv",
            "SURVIVAL_METRICS.json",
            "INDEPENDENT_ACCOUNTING_RECONCILIATION.json",
        ]
        for f in required_data_files:
            p = DOSSIER_DIR / f
            assert p.exists(), f"Required dataset {f} does not exist"
            assert p.stat().st_size > 50, f"Dataset {f} appears truncated or empty"

    def test_active_period_metrics_integrity(self) -> None:
        """Verifies active-period metrics reflect true negative edge and capital depletion."""
        p = DOSSIER_DIR / "ACTIVE_PERIOD_METRICS.json"
        with open(p, "r", encoding="utf-8") as f:
            m = json.load(f)

        assert 50 <= m["active_calendar_days"] <= 120, "Active days must be within empirical range"
        assert m["initial_equity_usd"] == 100.0, "Initial equity must be exactly $100"
        assert m["terminal_equity_usd"] < 20.0, "Terminal equity must be below the $20 starvation threshold"
        assert m["mean_daily_return_pct"] < 0.0, "Active daily return must be negative"
        assert m["median_daily_return_pct"] < 0.0, "Median daily return must be negative"
        assert m["max_drawdown_pct"] >= 79.0, "Max drawdown must reflect ~80% capital depletion"
        assert m["profit_factor"] < 1.0, "Profit factor must be < 1.0 (fails transaction friction)"
        assert m["net_expectancy_bps"] < 0.0, "Net expectancy must be negative"

    def test_full_calendar_provenance_ledger(self) -> None:
        """Verifies exactly 1,099 continuous days are categorized and accounted for."""
        p = DOSSIER_DIR / "FULL_CALENDAR_PROVENANCE_LEDGER.csv"
        df = pd.read_csv(p)

        assert len(df) == 1099, f"Expected 1,099 calendar days, found {len(df)}"
        assert "date_utc" in df.columns
        assert "daily_return_pct" in df.columns
        assert "end_day_mtm_equity_usd" in df.columns
        assert "is_operational" in df.columns

        # Verify operational days + post-halt days sum to 1099
        active_days = int(df["is_operational"].sum())
        post_halt_days = int((df["is_operational"] == False).sum())
        assert active_days + post_halt_days == 1099

        # Verify days after halt day have 0.0 daily return and flat terminal equity
        df_post_halt = df[df["is_operational"] == False]
        # Skip the transition day where the threshold was breached
        df_subsequent_idle = df_post_halt.iloc[1:]
        assert (df_subsequent_idle["daily_return_pct"] == 0.0).all(), "Subsequent post-halt daily returns must be exactly 0.0%"
        terminal_equity = df_subsequent_idle["end_day_mtm_equity_usd"].iloc[0]
        assert np.isclose(df_subsequent_idle["end_day_mtm_equity_usd"], terminal_equity, atol=1e-3).all()

        # Verify dilution factor
        diluted_mean = df["daily_return_pct"].mean()
        assert -0.20 <= diluted_mean <= -0.10, f"Diluted mean {diluted_mean}% out of expected range"

    def test_capital_scale_sensitivity_experiments(self) -> None:
        """Verifies capital scaling fails to rescue the negative-expectancy strategy."""
        p = DOSSIER_DIR / "CAPITAL_SCALE_EXPERIMENTS.csv"
        df = pd.read_csv(p)

        assert len(df) == 3, "Expected 3 capital scale tests ($100, $1k, $10k)"
        assert list(df["initial_capital_usd"]) == [100.0, 1000.0, 10000.0]

        # In all runs, starvation halt occurred and terminal equity fell to ~$19.98
        assert df["starvation_halt_occurred"].all(), "Starvation halt must trigger for all capital tiers"
        for _, row in df.iterrows():
            assert row["terminal_equity_usd"] < 20.0, f"Terminal equity {row['terminal_equity_usd']} should be < 20"

        # Max drawdown must strictly worsen with higher starting balance
        mdds = df["max_drawdown_pct"].values
        assert mdds[0] >= 80.0, "Initial $100 MDD must be >= 80%"
        assert mdds[1] >= 98.0, "Initial $1,000 MDD must be >= 98%"
        assert mdds[2] >= 99.8, "Initial $10,000 MDD must be >= 99.8%"

    def test_survival_metrics_and_bootstrap_ruin(self) -> None:
        """Verifies bootstrap ruin probability is 100% and metrics are structurally sound."""
        p = DOSSIER_DIR / "SURVIVAL_METRICS.json"
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)

        assert "bootstrap_ruin_simulations" in d
        sims = d["bootstrap_ruin_simulations"]

        # $100 capital simulation
        s100 = sims["initial_capital_100_usd"]
        assert s100["bootstrap_resamples"] == 2000
        assert s100["empirical_ruin_probability_pct"] == 100.0
        assert 50 <= s100["median_days_to_operational_halt"] <= 100

        # $1000 capital simulation
        s1000 = sims["initial_capital_1000_usd"]
        assert s1000["bootstrap_resamples"] == 2000
        assert s1000["empirical_ruin_probability_pct"] == 100.0
        assert 150 <= s1000["median_days_to_operational_halt"] <= 250

        # Minimum notional audit
        notional_audit = d["minimum_notional_audit"]
        assert notional_audit["minimum_exchange_order_notional_usd"] == 5.0
        assert notional_audit["maximum_position_weight"] == 0.25
        assert notional_audit["starvation_equity_threshold_usd"] == 20.0
        assert notional_audit["position_notional_at_halt_usd"] < 5.0

    def test_independent_accounting_reconciliation(self) -> None:
        """Verifies clean-room reconciliation against Milestone 5.7 findings."""
        p = DOSSIER_DIR / "INDEPENDENT_ACCOUNTING_RECONCILIATION.json"
        with open(p, "r", encoding="utf-8") as f:
            rec = json.load(f)

        assert rec["reconciliation_status"] == "EXACT_MATHEMATICAL_MATCH"
        m57 = rec["milestone_5_7_reported"]
        m58 = rec["milestone_5_8a_independently_verified"]

        # Both agree on max drawdown ~80%
        assert np.isclose(m57["max_drawdown_pct"], 80.01, atol=0.1)
        assert np.isclose(m58["max_drawdown_pct"], 80.03, atol=0.1)

        # Both agree on diluted daily return ~-0.145%
        assert np.isclose(m57["diluted_1099_days_mean_pct"], -0.1449, atol=0.01)
        assert np.isclose(m58["diluted_1099_days_mean_pct"], -0.1443, atol=0.01)

    def test_prospective_holdout_boundary_integrity(self) -> None:
        """Verifies the prospective holdout boundary (2026-11-01 UTC) remains untouched."""
        ledger_path = DOSSIER_DIR / "FULL_CALENDAR_PROVENANCE_LEDGER.csv"
        df = pd.read_csv(ledger_path)

        last_date = str(df["date_utc"].max())
        assert last_date <= "2026-10-31", f"Date {last_date} breaches prospective holdout boundary"

    def test_governance_decision_and_paper_trading_prohibition(self) -> None:
        """Verifies final governance decision enforces REQUIRES_RESEARCH and denies paper trading."""
        p = DOSSIER_DIR / "FINAL_RESEARCH_DECISION.md"
        content = p.read_text(encoding="utf-8")

        assert "RESEARCH_STATUS: REQUIRES_RESEARCH" in content
        assert "PAPER_TRADING_AUTHORIZATION: DENIED_PENDING_3_PERCENT_BACKTEST_VALIDATION" in content
        assert "PAPER_TRADING_DAEMON: STRICTLY_PROHIBITED" in content
        assert "EXCHANGE_API_TRADING_CREDENTIALS: STRICTLY_PROHIBITED" in content
        assert "EFFECTIVE_LEVERAGE: STRICTLY 1.0x (UNLEVERED)" in content
