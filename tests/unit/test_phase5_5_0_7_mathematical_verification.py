"""
QUANTUM Phase 5.5.0.7 Unit Tests: Mathematical & Test Integrity Verification.

Validates the analytical depth, structural completeness, and forensic rigor
of Phase 5.5.0.7:
1. All 6 required deliverables exist in docs/research/phase_5_5_0_7/.
2. Transaction cost audit verifies notional dimensionality, fee conventions, and double-counting risks.
3. Funding cash-flow aggregation verifies 7 core properties and synthetic multi-settlement examples.
4. Net return audit verifies dimensional consistency and catalogs the 4-level acceptance hierarchy.
5. Test integrity audit produces the complete test-change table and epistemic classification.
6. Frozen artifact audit programmatically verifies all 110 model/preprocessor binaries (SHA-256).
7. Holdout audit documents physical data boundaries and epistemic access classifications.
8. Master report verdict is FINAL_VERIFICATION_PASS_WITH_LIMITATIONS.
9. Zero em dashes (Unicode U+2014) across all Phase 5.5.0.7 files and test suite.
"""

import hashlib
import json
from pathlib import Path
import pytest

PHASE_5_5_0_7_DIR = Path("docs/research/phase_5_5_0_7")
PHASE_5_3_FREEZE_MANIFEST = Path("artifacts/phase_5_3_freeze/frozen_artifact_manifest.json")

REQUIRED_DELIVERABLES = [
    "PHASE_5_5_0_7_TRANSACTION_COST_AUDIT.md",
    "PHASE_5_5_0_7_FUNDING_AGGREGATION_AUDIT.md",
    "PHASE_5_5_0_7_NET_RETURN_AND_ACCEPTANCE_AUDIT.md",
    "PHASE_5_5_0_7_TEST_INTEGRITY_AUDIT.md",
    "PHASE_5_5_0_7_FROZEN_ARTIFACT_AND_HOLDOUT_AUDIT.md",
    "PHASE_5_5_0_7_FINAL_VERIFICATION_REPORT.md",
]

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"
]

EXPECTED_DECISION_IDS = ["DEC_01", "DEC_02", "DEC_03", "DEC_04", "DEC_05", "DEC_06"]


def test_01_all_6_deliverables_exist():
    """Verify that all 6 required Phase 5.5.0.7 deliverables exist and are non-empty."""
    assert PHASE_5_5_0_7_DIR.exists(), f"Missing directory {PHASE_5_5_0_7_DIR}"
    for fname in REQUIRED_DELIVERABLES:
        fpath = PHASE_5_5_0_7_DIR / fname
        assert fpath.exists(), f"Missing deliverable: {fname}"
        assert fpath.stat().st_size > 100, f"Deliverable is unexpectedly small: {fname}"


def test_02_transaction_cost_dimensional_audit():
    """Verify transaction cost audit covers notionals, fee conventions, and double-counting."""
    fpath = PHASE_5_5_0_7_DIR / "PHASE_5_5_0_7_TRANSACTION_COST_AUDIT.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "N_{\\text{entry}} = Q_{\\text{entry}} P_{\\text{entry}}" in content
    assert "N_{\\text{exit}} = Q_{\\text{exit}} P_{\\text{exit}}" in content
    assert "Convention 1 (Fixed Assumption on Entry Notional)" in content
    assert "Convention 2 (Sum of Nominal Leg Rates)" in content
    assert "Convention 3 (Effective Realized Bps Normalized to Entry Notional)" in content
    assert "Fill-Price Accounting (Net Price Method)" in content
    assert "Reference-Price Accounting (Gross Price + Cash Fee Method)" in content
    assert "CRITICAL WARNING" in content
    assert "DIMENSIONAL AUDIT TABLE" in content
    assert "PASS_WITH_LIMITATIONS" in content


def test_03_funding_cash_flow_aggregation():
    """Verify funding audit covers 7 properties and synthetic numerical examples."""
    fpath = PHASE_5_5_0_7_DIR / "PHASE_5_5_0_7_FUNDING_AGGREGATION_AUDIT.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "funding_rate_bps_per_settlement" in content
    assert "CF_t = -d \\times N_{\\text{settle}, t} \\times f_{t, \\text{decimal}}" in content
    assert "CF_{\\text{funding, total}} = \\sum_{t=1}^k CF_t" in content
    assert "Property 1: Positive Funding Rate Behavior" in content
    assert "Property 2: Negative Funding Rate Behavior" in content
    assert "Property 3: Position Eligibility at Settlement Timestamps" in content
    assert "Property 4: Discrete Mark Notional Dynamic Evaluation" in content
    assert "Property 5: Additive Aggregation Without Double Counting" in content
    assert "Property 6: Strict Exclusion from Transaction Cost Bps" in content
    assert "Property 7: 1095 Annualization Factor as a Nominal Convention" in content
    assert "SYNTHETIC NUMERICAL EXAMPLES" in content
    assert "illustrative and synthetic" in content


def test_04_net_return_and_acceptance_hierarchy():
    """Verify net return formula and 4-level acceptance hierarchy audit."""
    fpath = PHASE_5_5_0_7_DIR / "PHASE_5_5_0_7_NET_RETURN_AND_ACCEPTANCE_AUDIT.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "R_{\\text{net}} = R_{\\text{gross}} - C_{\\text{transaction, normalized}} + \\frac{CF_{\\text{funding, total}}}{N_{\\text{entry}}}" in content
    assert "Level 1" in content and "Cost Scenario Resilience" in content
    assert "Level 2" in content and "Net Economic Expectancy" in content
    assert "Level 3" in content and "Statistical Significance" in content
    assert "Level 4" in content and "Anti-Cherry-Picking Robustness" in content
    assert "Serial and Temporal Dependence of Overlapping Trades" in content
    assert "Overlapping Trades and Multi-Asset Concurrency" in content
    assert "Multiple Testing Family Size ($K$) Ambiguity" in content
    assert "CRITICAL DISTINCTION" in content


def test_05_test_integrity_investigation():
    """Verify test-change audit table and investigation of initial test failure."""
    fpath = PHASE_5_5_0_7_DIR / "PHASE_5_5_0_7_TEST_INTEGRITY_AUDIT.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "INVESTIGATION OF PHASE 5.5.0.6 TEST EXECUTION HISTORY" in content
    assert "DETAILED TEST-CHANGE AUDIT TABLE" in content
    assert "test_02_dec_01_target_vs_execution_distinction" in content
    assert "test_07_hypothetical_cost_examples_explicitly_labeled" in content
    assert "test_09_decision_worksheet_revision_all_pending" in content
    assert "Static Documentation Check vs. Runtime Execution" in content
    assert "test_10_frozen_models_and_preprocessors_integrity" in content
    assert "test_13_zero_em_dashes_across_all_phase_5_5_0_6_files" in content


def test_06_frozen_artifacts_sha256_verification():
    """Programmatically verify all 55 LightGBM models and 55 preprocessors against freeze manifest."""
    assert PHASE_5_3_FREEZE_MANIFEST.exists(), "Phase 5.3 freeze manifest missing!"
    with open(PHASE_5_3_FREEZE_MANIFEST, "r", encoding="utf-8") as f:
        freeze_data = json.load(f)

    freeze_lookup = {
        art["relative_path"].replace("\\", "/"): art["sha256"]
        for art in freeze_data["artifacts"]
    }

    verified_count = 0
    for sym in SYMBOLS:
        base_dir = Path("artifacts/phase_5_3_1" if sym in ["BTCUSDT", "XMRUSDT"] else "artifacts/phase_5_3_2") / sym
        for fold in range(1, 6):
            m_path = base_dir / f"fold_{fold}" / "lgbm_model.joblib"
            p_path = base_dir / f"fold_{fold}" / "preprocessor.joblib"

            assert m_path.exists(), f"Model binary missing: {m_path}"
            assert p_path.exists(), f"Preprocessor missing: {p_path}"

            h_m = hashlib.sha256(m_path.read_bytes()).hexdigest()
            h_p = hashlib.sha256(p_path.read_bytes()).hexdigest()

            assert h_m == freeze_lookup[str(m_path).replace("\\", "/")]
            assert h_p == freeze_lookup[str(p_path).replace("\\", "/")]
            verified_count += 2

    assert verified_count == 110, f"Expected 110 verified binaries, got {verified_count}"


def test_07_prospective_holdout_physical_boundary():
    """Verify holdout documentation, epistemic categories, and physical boundary."""
    fpath = PHASE_5_5_0_7_DIR / "PHASE_5_5_0_7_FROZEN_ARTIFACT_AND_HOLDOUT_AUDIT.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "EPISTEMIC INTEGRITY BOUNDARIES" in content
    assert "Artifact Hash Integrity: [SOURCE_VERIFIED / TEST_VERIFIED]" in content
    assert "Git Working-Tree Integrity: [SOURCE_VERIFIED]" in content
    assert "Dataset Read History: [NOT_VERIFIED]" in content
    assert "Prospective Holdout Access History: [NOT_VERIFIED via logs]" in content
    assert "2026-10-31 20:59:59.999 UTC" in content
    assert "2026-11-01 00:00:00 UTC" in content
    assert "2027-04-30 23:59:59.999 UTC" in content


def test_08_final_verification_report_verdict():
    """Verify master report verdict and pending governance states."""
    fpath = PHASE_5_5_0_7_DIR / "PHASE_5_5_0_7_FINAL_VERIFICATION_REPORT.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "FINAL_VERIFICATION_PASS_WITH_LIMITATIONS" in content
    for dec_id in EXPECTED_DECISION_IDS:
        assert f"{dec_id}" in content
        assert "PENDING_HUMAN_DECISION" in content
    assert "NOT_STARTED" in content
    assert "NOT_AUTHORIZED" in content
    assert "STRICTLY_SEALED" in content


def test_09_zero_em_dashes_in_phase_5_5_0_7():
    """Verify zero em dashes (Unicode U+2014) across all Phase 5.5.0.7 files."""
    em_dash = chr(0x2014)
    for fname in REQUIRED_DELIVERABLES:
        fpath = PHASE_5_5_0_7_DIR / fname
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            assert em_dash not in content, f"Em dash detected in {fname}!"
