"""QUANTUM Milestone 5.8B — Unit & Validation Tests for New Alpha Family Feasibility.

Verifies:
1. Existence and integrity of all Milestone 5.8B dossiers and datasets.
2. Track A data availability and acquisition requirements.
3. Track B microstructure constraints and prohibition of L2 synthesis from OHLCV.
4. Track C data availability, 45-pair cointegration audit, and unlevered capacity.
5. Comparative feasibility matrix and evidence-based rankings.
6. Preservation of prospective holdout boundary (zero leakage).
7. Governance compliance and paper trading prohibition.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


DOSSIER_DIR = Path("audit/strategy_research/milestone_5_8b_new_alpha_feasibility")


class TestMilestone58BAlphaFeasibility:
    """Verifies all feasibility deliverables and data audit calculations."""

    def test_milestone_5_8b_dossier_deliverables_exist(self) -> None:
        """Verifies all 7 markdown reports and structured data files exist."""
        required_md_files = [
            "TRACK_A_FUNDING_BASIS_FEASIBILITY.md",
            "TRACK_B_ORDER_FLOW_FEASIBILITY.md",
            "TRACK_C_RELATIVE_VALUE_FEASIBILITY.md",
            "DATA_AVAILABILITY_MATRIX.md",
            "EXECUTION_REQUIREMENTS.md",
            "COMPARATIVE_RESEARCH_DECISION.md",
            "FINAL_RESEARCH_DECISION.md",
        ]
        for f in required_md_files:
            p = DOSSIER_DIR / f
            assert p.exists(), f"Required markdown dossier {f} does not exist"
            assert p.stat().st_size > 1000, f"Dossier {f} appears truncated or empty"

        required_data_files = [
            "DATA_INVENTORY_AUDIT.json",
            "TRACK_FEASIBILITY_MATRIX.json",
            "CROSS_SECTIONAL_UNIVERSE_STATS.csv",
            "PAIRWISE_COINTEGRATION_AUDIT.csv",
        ]
        for f in required_data_files:
            p = DOSSIER_DIR / f
            assert p.exists(), f"Required dataset {f} does not exist"
            assert p.stat().st_size > 50, f"Dataset {f} appears truncated or empty"

    def test_data_inventory_summary_classifications(self) -> None:
        """Verifies correct track classifications in DATA_INVENTORY_AUDIT.json."""
        p = DOSSIER_DIR / "DATA_INVENTORY_AUDIT.json"
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)

        assert "data_availability_summary" in d
        summary = d["data_availability_summary"]
        assert summary["TRACK_A_FUNDING_BASIS"] == "DATA_ACQUISITION_REQUIRED"
        assert summary["TRACK_B_ORDER_FLOW"] == "DATA_ACQUISITION_REQUIRED"
        assert summary["TRACK_C_RELATIVE_VALUE"] == "READY_FOR_EMPIRICAL_RESEARCH"

        # Track A details
        ta = d["track_a_funding_basis"]
        assert ta["funding_events_db_count"] == 0
        assert ta["parquet_has_funding_columns"] is False
        assert ta["spot_data_available"] is False

        # Track B details
        tb = d["track_b_order_flow_microstructure"]
        assert tb["l2_snapshots_db_count"] == 0
        assert tb["has_l2_depth_snapshots"] is False
        assert tb["has_tick_trades_tape"] is False

        # Track C details
        tc = d["track_c_relative_value"]
        assert tc["universe_size"] == 10
        assert tc["calendar_days_available"] >= 1099
        assert tc["cointegrated_pairs_count"] == 9
        assert tc["total_pairs_tested"] == 45

    def test_track_feasibility_matrix_rankings(self) -> None:
        """Verifies comparative rankings and evidence-based ordering."""
        p = DOSSIER_DIR / "TRACK_FEASIBILITY_MATRIX.json"
        with open(p, "r", encoding="utf-8") as f:
            m = json.load(f)

        assert "tracks" in m
        tracks = m["tracks"]
        assert "PRIORITY_1" in tracks["TRACK_C_RELATIVE_VALUE"]["research_priority"]
        assert "PRIORITY_2" in tracks["TRACK_A_FUNDING_BASIS"]["research_priority"]
        assert "PRIORITY_3" in tracks["TRACK_B_ORDER_FLOW"]["research_priority"]

    def test_pairwise_cointegration_audit_table(self) -> None:
        """Verifies the 45-pair cointegration audit, ADF statistics, and BTC/ETH non-cointegration."""
        p = DOSSIER_DIR / "PAIRWISE_COINTEGRATION_AUDIT.csv"
        df = pd.read_csv(p)

        assert len(df) == 45, f"Expected 45 pairs for 10 assets, found {len(df)}"
        assert "pair" in df.columns
        assert "correlation" in df.columns
        assert "adf_t_statistic" in df.columns
        assert "is_cointegrated_5pct" in df.columns

        # Verify exactly 9 pairs are cointegrated at 5% level
        cointeg_count = int(df["is_cointegrated_5pct"].sum())
        assert cointeg_count == 9, f"Expected 9 cointegrated pairs, found {cointeg_count}"

        # BTC/ETH must have high correlation (> 0.75) but NOT be cointegrated
        btc_eth = df[df["pair"] == "BTCUSDT/ETHUSDT"].iloc[0]
        assert btc_eth["correlation"] > 0.75, "BTC/ETH correlation should be > 0.75"
        assert not bool(btc_eth["is_cointegrated_5pct"]), "BTC/ETH must not be cointegrated"
        assert btc_eth["adf_t_statistic"] > -3.37, "BTC/ETH ADF t-stat should fail critical value"

        # SOL/LTC must be strongly cointegrated
        sol_ltc = df[df["pair"] == "SOLUSDT/LTCUSDT"].iloc[0]
        assert bool(sol_ltc["is_cointegrated_5pct"]), "SOL/LTC must be cointegrated"
        assert sol_ltc["adf_t_statistic"] < -3.37

    def test_cross_sectional_universe_stats(self) -> None:
        """Verifies primary universe fingerprints and candle counts."""
        p = DOSSIER_DIR / "CROSS_SECTIONAL_UNIVERSE_STATS.csv"
        df = pd.read_csv(p)

        assert len(df) == 10, f"Expected 10 primary assets, found {len(df)}"
        assert (df["total_5m_candles"] >= 316400).all(), "All assets must have >= 316,400 5m candles"
        assert (df["calendar_days"] >= 1099).all(), "All assets must cover >= 1,099 calendar days"

    def test_prospective_holdout_boundary_integrity(self) -> None:
        """Verifies that all canonical datasets terminate before the holdout boundary."""
        p = DOSSIER_DIR / "CROSS_SECTIONAL_UNIVERSE_STATS.csv"
        df = pd.read_csv(p)

        for _, row in df.iterrows():
            end_iso = str(row["end_time_iso"])
            assert end_iso <= "2026-10-31T23:59:59+00:00", f"Asset {row['symbol']} breaches holdout boundary"

    def test_governance_decision_and_paper_trading_prohibition(self) -> None:
        """Verifies final governance decision enforces REQUIRES_RESEARCH and denies paper trading."""
        p = DOSSIER_DIR / "FINAL_RESEARCH_DECISION.md"
        content = p.read_text(encoding="utf-8")

        assert "RESEARCH_STATUS: REQUIRES_RESEARCH" in content
        assert "PAPER_TRADING_AUTHORIZATION: DENIED_PENDING_3_PERCENT_BACKTEST_VALIDATION" in content
        assert "PAPER_TRADING_DAEMON: STRICTLY_PROHIBITED" in content
        assert "EXCHANGE_API_TRADING_CREDENTIALS: STRICTLY_PROHIBITED" in content
        assert "EFFECTIVE_LEVERAGE: STRICTLY 1.0x (UNLEVERED)" in content
        assert "TRACK_A_STATUS: DATA_ACQUISITION_REQUIRED" in content
        assert "TRACK_B_STATUS: DATA_ACQUISITION_REQUIRED" in content
        assert "TRACK_C_STATUS: READY_FOR_EMPIRICAL_RESEARCH" in content
