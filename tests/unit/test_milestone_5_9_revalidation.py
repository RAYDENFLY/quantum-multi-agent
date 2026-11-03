"""QUANTUM Milestone 5.9 — Unit & Validation Tests for Track C Statistical Revalidation.

Verifies:
1. Existence and integrity of all Milestone 5.9 dossiers, ledgers, and economic models.
2. 45-pair Engle-Granger revalidation and Holm-Bonferroni correction (0 / 45 survive in training).
3. Rolling stability audit and out-of-sample spread stationarity breakdown.
4. Trade-level economic modeling under Bybit VIP0 friction and 1.0x unlevered leverage.
5. Absolute prospective holdout boundary isolation (zero leakage).
6. Governance compliance and paper trading prohibition.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


DOSSIER_DIR = Path("audit/strategy_research/milestone_5_9_track_c_revalidation")


class TestMilestone59TrackCRevalidation:
    """Verifies all Milestone 5.9 deliverables and statistical calculations."""

    def test_milestone_5_9_dossier_deliverables_exist(self) -> None:
        """Verifies all required markdown reports and CSV/JSON datasets exist and are non-empty."""
        required_md_files = [
            "M5_9_COINTEGRATION_REVALIDATION.md",
            "M5_9_DATA_PROVENANCE_AUDIT.md",
            "M5_9_TEST_RESULTS.md",
        ]
        for f in required_md_files:
            p = DOSSIER_DIR / f
            assert p.exists(), f"Required markdown dossier {f} does not exist"
            assert p.stat().st_size > 1000, f"Dossier {f} appears truncated or empty"

        required_data_files = [
            "M5_9_PAIRWISE_ADJUSTED_PVALUES.csv",
            "M5_9_ROLLING_STABILITY.csv",
            "TRADE_LEVEL_ECONOMICS.json",
        ]
        for f in required_data_files:
            p = DOSSIER_DIR / f
            assert p.exists(), f"Required dataset {f} does not exist"
            assert p.stat().st_size > 50, f"Dataset {f} appears truncated or empty"

    def test_pairwise_adjusted_pvalues_integrity(self) -> None:
        """Verifies 45 pairs, dual orientation metrics, and Holm-Bonferroni correction."""
        p = DOSSIER_DIR / "M5_9_PAIRWISE_ADJUSTED_PVALUES.csv"
        df = pd.read_csv(p)

        assert len(df) == 45, f"Expected 45 pairs, found {len(df)}"
        assert "pair" in df.columns
        assert "canonical_t_train" in df.columns
        assert "canonical_p_raw_train" in df.columns
        assert "holm_adjusted_p_train" in df.columns
        assert "survives_holm_train_5pct" in df.columns

        # Verify zero pairs survive Holm-Bonferroni correction on Training Data
        surviving_train = int(df["survives_holm_train_5pct"].sum())
        assert surviving_train == 0, f"Expected 0 surviving pairs on training data, found {surviving_train}"

        # Verify BTC/ETH is NOT cointegrated
        btc_eth = df[df["pair"] == "BTCUSDT/ETHUSDT"].iloc[0]
        assert btc_eth["canonical_t_train"] > -3.37
        assert btc_eth["canonical_p_raw_train"] > 0.10

    def test_rolling_stability_audit_integrity(self) -> None:
        """Verifies parameter instability and out-of-sample breakdown across all pairs."""
        p = DOSSIER_DIR / "M5_9_ROLLING_STABILITY.csv"
        df = pd.read_csv(p)

        assert len(df) == 45, f"Expected 45 pairs, found {len(df)}"
        assert "pair" in df.columns
        assert "rolling_beta_cv" in df.columns
        assert "val_adf_t" in df.columns
        assert "oos_adf_t" in df.columns
        assert "stability_status" in df.columns

        # Verify that all 45 pairs fail stability due to structural breaks out-of-sample
        rejected_count = int((df["stability_status"] == "STRUCTURAL_BREAK_REJECTED").sum())
        assert rejected_count == 45, f"Expected all 45 pairs to be rejected for structural breaks, found {rejected_count}"

        # Top candidate SOL/LTC must fail validation ADF stationarity
        sol_ltc = df[df["pair"] == "SOLUSDT/LTCUSDT"].iloc[0]
        assert sol_ltc["val_adf_t"] > -2.86, "SOL/LTC spread must fail stationarity in Validation"

    def test_trade_level_economic_model(self) -> None:
        """Verifies trade-level performance of dollar-neutral pairs vs directional relative strength."""
        p = DOSSIER_DIR / "TRADE_LEVEL_ECONOMICS.json"
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)

        assert "pair_trading_sol_ltc" in d
        assert "single_slot_directional_rs" in d

        # Pair trading: low drawdown but negative net daily return
        perf_pair = d["pair_trading_sol_ltc"]["performance"]
        assert perf_pair["mean_daily_return_pct"] < 0.0, "Pair trading net daily return must be negative"
        assert perf_pair["max_drawdown_pct"] <= 15.0, "Pair trading MDD should remain <= 15%"

        # Directional relative strength: massive drawdown (> 50%)
        perf_dir = d["single_slot_directional_rs"]["performance"]
        assert perf_dir["max_drawdown_pct"] > 50.0, "Directional RS should suffer > 50% MDD"

    def test_prospective_holdout_boundary_integrity(self) -> None:
        """Verifies canonical data precedes the prospective holdout boundary (1793491200000 ms)."""
        canonical_dir = Path("data/historical/canonical/exchange=ASTER")
        for sym_dir in canonical_dir.glob("symbol=*"):
            timeframe_dir = sym_dir / "timeframe=5m"
            for p_file in timeframe_dir.glob("*.parquet"):
                df_ts = pd.read_parquet(p_file, columns=["open_time_ms"])
                max_ts = int(df_ts["open_time_ms"].max())
                assert max_ts < 1793491200000, f"File {p_file} breaches holdout boundary ({max_ts})"

    def test_governance_decision_and_paper_trading_prohibition(self) -> None:
        """Verifies final governance decision enforces REQUIRES_RESEARCH and denies paper trading."""
        p = DOSSIER_DIR / "M5_9_TEST_RESULTS.md"
        content = p.read_text(encoding="utf-8")

        assert "FINAL_RESEARCH_STATUS: REQUIRES_RESEARCH" in content
        assert "PAPER_TRADING_AUTHORIZATION: DENIED_PENDING_3_PERCENT_BACKTEST_VALIDATION" in content
        assert "TRACK_C_DISPOSITION: REJECTED_AS_UNVIABLE" in content
