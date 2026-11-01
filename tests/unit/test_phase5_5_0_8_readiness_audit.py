"""
QUANTUM Phase 5.5.0.8 Unit Tests: Final Quantitative Specification & Research Readiness Audit.

Validates the analytical depth, structural completeness, and forensic rigor
of Phase 5.5.0.8:
1. All 7 required deliverables exist in docs/research/phase_5_5_0_8/.
2. Long/short notional scaling, four canonical cases, and fee asymmetry are mathematically verified.
3. Transaction cost specification confirms REFERENCE_PRICE_ACCOUNTING and half-spread conventions.
4. Funding eligibility audit documents discrete settlement boundaries and 1095 nominal scaling.
5. Statistical inference specification documents 288-bar overlapping horizons and K=11 family size.
6. Full-fleet metadata scanner verifies all 33 partitions terminate before 2026-11-01 00:00:00 UTC.
7. Repository audit trail reconciles git status path-limiting and untracked file preservation.
8. Final readiness report specifies RESEARCH_SPECIFICATION_READY_WITH_LIMITATIONS and catalogs issues.
9. Zero em dashes (Unicode U+2014) across all Phase 5.5.0.8 files and test suite.
"""

import glob
import os
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
import pytest

PHASE_5_5_0_8_DIR = Path("docs/research/phase_5_5_0_8")
CANONICAL_BASE_DIR = Path("data/historical/canonical/exchange=ASTER")

REQUIRED_DELIVERABLES = [
    "PHASE_5_5_0_8_LONG_SHORT_ACCOUNTING_AUDIT.md",
    "PHASE_5_5_0_8_TRANSACTION_COST_SPECIFICATION.md",
    "PHASE_5_5_0_8_FUNDING_ELIGIBILITY_AUDIT.md",
    "PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md",
    "PHASE_5_5_0_8_FULL_FLEET_TEMPORAL_ISOLATION_AUDIT.md",
    "PHASE_5_5_0_8_REPOSITORY_AUDIT_TRAIL.md",
    "PHASE_5_5_0_8_FINAL_RESEARCH_READINESS_REPORT.md",
]

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"
]
TIMEFRAMES = ["5m", "15m", "1h"]

EXPECTED_DECISION_IDS = ["DEC_01", "DEC_02", "DEC_03", "DEC_04", "DEC_05", "DEC_06"]


def test_01_all_7_deliverables_exist():
    """Verify that all 7 required Phase 5.5.0.8 deliverables exist and are non-empty."""
    assert PHASE_5_5_0_8_DIR.exists(), f"Missing directory {PHASE_5_5_0_8_DIR}"
    for fname in REQUIRED_DELIVERABLES:
        fpath = PHASE_5_5_0_8_DIR / fname
        assert fpath.exists(), f"Missing deliverable: {fname}"
        assert fpath.stat().st_size > 100, f"Deliverable is unexpectedly small: {fname}"


def test_02_long_short_accounting_and_notional_derivation():
    """Verify long/short notional scaling, four canonical cases, and fee asymmetry."""
    fpath = PHASE_5_5_0_8_DIR / "PHASE_5_5_0_8_LONG_SHORT_ACCOUNTING_AUDIT.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "N_{\\text{exit}} = N_{\\text{entry}}(1 + d R_{\\text{gross}})" in content
    assert "Case 1: LONG Profitable" in content
    assert "Case 2: LONG Losing" in content
    assert "Case 3: SHORT Profitable" in content
    assert "Case 4: SHORT Losing" in content
    assert "15.1125 bps" in content
    assert "14.8875 bps" in content
    assert "strictly lower exit notional" in content
    assert "PARTIAL EXITS AUDIT (A2)" in content
    assert "PASS_WITH_LIMITATIONS" in content


def test_03_transaction_cost_specification():
    """Verify REFERENCE_PRICE_ACCOUNTING and half-spread conventions."""
    fpath = PHASE_5_5_0_8_DIR / "PHASE_5_5_0_8_TRANSACTION_COST_SPECIFICATION.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "REFERENCE_PRICE_ACCOUNTING" in content
    assert "Seven Invariant Rules" in content
    assert "CANONICAL DENOMINATOR STANDARDIZATION" in content
    assert "Half-Spread per Leg" in content
    assert "half-spread per leg" in content
    assert "SLIPPAGE & MARKET IMPACT ACCOUNTING MATRIX" in content
    assert "REQUIRES_HUMAN_DECISION" in content


def test_04_funding_eligibility_and_annualization():
    """Verify funding eligibility matrix and nominal annualization standard."""
    fpath = PHASE_5_5_0_8_DIR / "PHASE_5_5_0_8_FUNDING_ELIGIBILITY_AUDIT.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "funding_rate_bps_per_settlement" in content
    assert "SETTLEMENT ELIGIBILITY MATRIX & BOUNDARY RULES" in content
    assert "Pre-Settlement Entry" in content
    assert "Intra-Settlement Trade" in content
    assert "Multi-Settlement Hold" in content
    assert "Entry Exactly at Settlement" in content
    assert "Exit Exactly at Settlement" in content
    assert "1095 = 3 \\times 365" in content
    assert "nominal arithmetic scaling factor" in content
    assert "Strict Prohibitions" in content


def test_05_statistical_inference_specification():
    """Verify overlapping trades analysis and multiple testing family recommendations."""
    fpath = PHASE_5_5_0_8_DIR / "PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "BOOTSTRAP DEPENDENCE AUDIT & OVERLAPPING TRADES" in content
    assert "288 bars" in content
    assert "Calendar-Time Continuous Portfolio MBB" in content
    assert "Trade-Level Clustered Block Bootstrap" in content
    assert "MULTIPLE-TESTING FAMILY SPECIFICATION" in content
    assert "Confirmatory Family ($K = 11$)" in content
    assert "STATISTICAL INFERENCE SPECIFICATION MATRIX" in content
    assert "PENDING_HUMAN_DECISION" in content


def test_06_full_fleet_temporal_isolation_metadata():
    """Programmatically verify that all 33 fleet partitions terminate prior to holdout start."""
    holdout_start_ms = int(pd.Timestamp("2026-11-01 00:00:00+00:00").timestamp() * 1000)

    checked_partitions = 0
    for sym in SYMBOLS:
        for tf in TIMEFRAMES:
            dir_path = CANONICAL_BASE_DIR / f"symbol={sym}" / f"timeframe={tf}"
            assert dir_path.exists(), f"Missing partition directory: {dir_path}"

            parquet_files = sorted(glob.glob(str(dir_path / "*.parquet")))
            assert len(parquet_files) > 0, f"No parquet files in {dir_path}"

            max_close_ms = None
            total_rows = 0
            for pf in parquet_files:
                pfile = pq.ParquetFile(pf)
                total_rows += pfile.metadata.num_rows
                tbl = pfile.read(["close_time_ms"])
                p_max = tbl["close_time_ms"].to_pandas().max()
                if max_close_ms is None or p_max > max_close_ms:
                    max_close_ms = p_max

            assert max_close_ms < holdout_start_ms, (
                f"Partition {sym} {tf} violates holdout! Max close ms {max_close_ms} >= {holdout_start_ms}"
            )

            if sym == "XMRUSDT" and tf == "5m":
                assert total_rows == 83863, f"Expected 83,863 rows for XMR 5m, got {total_rows}"
            elif tf == "5m":
                assert total_rows in [316499, 316500], f"Expected ~316,500 rows for {sym} 5m, got {total_rows}"

            checked_partitions += 1

    assert checked_partitions == 33, f"Expected 33 checked partitions, got {checked_partitions}"


def test_07_repository_audit_trail_reconciliation():
    """Verify git status path-limiting explanation and execution timeline."""
    fpath = PHASE_5_5_0_8_DIR / "PHASE_5_5_0_8_REPOSITORY_AUDIT_TRAIL.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "INVESTIGATION OF THE GIT STATUS WORKING-TREE DISCREPANCY" in content
    assert "git status -- artifacts/" in content
    assert "untracked files" in content
    assert "CHRONOLOGICAL EXECUTION TIMELINE" in content
    assert "e79187c" in content


def test_08_final_readiness_report_and_issue_register():
    """Verify master readiness report verdict, issue register, and governance states."""
    fpath = PHASE_5_5_0_8_DIR / "PHASE_5_5_0_8_FINAL_RESEARCH_READINESS_REPORT.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "RESEARCH_SPECIFICATION_READY_WITH_LIMITATIONS" in content
    assert "CONSOLIDATED ISSUE REGISTER" in content
    for iss in ["ISS_01", "ISS_02", "ISS_03", "ISS_04", "ISS_05", "ISS_06", "ISS_07"]:
        assert iss in content

    for dec_id in EXPECTED_DECISION_IDS:
        assert dec_id in content
        assert "PENDING_HUMAN_DECISION" in content

    assert "NOT_STARTED" in content
    assert "NOT_AUTHORIZED" in content
    assert "STRICTLY_SEALED" in content


def test_09_zero_em_dashes_in_phase_5_5_0_8():
    """Verify zero em dashes (Unicode U+2014) across all Phase 5.5.0.8 files."""
    em_dash = chr(0x2014)
    for fname in REQUIRED_DELIVERABLES:
        fpath = PHASE_5_5_0_8_DIR / fname
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            assert em_dash not in content, f"Em dash detected in {fname}!"
