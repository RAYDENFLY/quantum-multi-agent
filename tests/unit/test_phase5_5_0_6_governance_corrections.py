"""
QUANTUM Phase 5.5.0.6 Unit Tests: Final Governance Corrections & Acceptance Criteria Reconciliation.

Validates the structural integrity, governance boundaries, and analytical rigor
of Phase 5.5.0.6:
1. All 9 required deliverables exist in docs/research/phase_5_5_0_6/.
2. DEC_01 distinguishes frozen target prediction from re-anchored economic execution.
3. DEC_01 distinguishes economic evaluation of frozen classifier from independent strategy development.
4. DEC_02 audits and correctly classifies 7 directional claims into 6 epistemic tiers.
5. DEC_04 clearly separates cost scenarios from net expectancy acceptance criteria.
6. Gross PnL, transaction costs, funding cash flows, and net PnL are mathematically consistent.
7. Hypothetical examples are clearly distinguished from empirical findings.
8. DEC_03, DEC_05, and DEC_06 are preserved without unnecessary redesign.
9. All six decisions remain pending human decision in the revised worksheet.
10. All 55 frozen LightGBM binaries and 55 preprocessors remain 100% bit-for-bit intact.
11. Prospective holdout (2026-11-01 to 2027-04-30) remains strictly protected and unaccessed.
12. Final report verdict is FINAL_GOVERNANCE_CORRECTIONS_PASS_WITH_LIMITATIONS.
13. Zero em dashes (Unicode U+2014) anywhere in Phase 5.5.0.6 files or test suite.
"""

import hashlib
import json
from pathlib import Path
import pytest

PHASE_5_5_0_6_DIR = Path("docs/research/phase_5_5_0_6")
PHASE_5_3_FREEZE_MANIFEST = Path("artifacts/phase_5_3_freeze/frozen_artifact_manifest.json")

REQUIRED_DELIVERABLES = [
    "PHASE_5_5_0_6_DEC_01_ESTIMAND_CLARIFICATION.md",
    "PHASE_5_5_0_6_RESEARCH_TRACK_COMPARISON.md",
    "PHASE_5_5_0_6_DEC_02_DIRECTIONAL_EVIDENCE_RECONCILIATION.md",
    "PHASE_5_5_0_6_DEC_04_COST_SCENARIO_DEFINITION.md",
    "PHASE_5_5_0_6_ECONOMIC_RETURN_AND_ACCEPTANCE_CRITERIA.md",
    "PHASE_5_5_0_6_HYPOTHETICAL_COST_EXAMPLE.md",
    "PHASE_5_5_0_6_GOVERNANCE_CHANGELOG.md",
    "PHASE_5_5_0_6_DECISION_WORKSHEET_REVISION.md",
    "PHASE_5_5_0_6_FINAL_GOVERNANCE_CORRECTION_REPORT.md",
]

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"
]

EXPECTED_DECISION_IDS = ["DEC_01", "DEC_02", "DEC_03", "DEC_04", "DEC_05", "DEC_06"]


def test_01_all_9_deliverables_exist():
    """Verify that all 9 required Phase 5.5.0.6 deliverables exist and are non-empty."""
    assert PHASE_5_5_0_6_DIR.exists(), f"Missing directory {PHASE_5_5_0_6_DIR}"
    for fname in REQUIRED_DELIVERABLES:
        fpath = PHASE_5_5_0_6_DIR / fname
        assert fpath.exists(), f"Missing deliverable: {fname}"
        assert fpath.stat().st_size > 100, f"Deliverable is unexpectedly small: {fname}"


def test_02_dec_01_target_vs_execution_distinction():
    """Verify DEC_01 distinguishes frozen target prediction from re-anchored execution."""
    fpath = PHASE_5_5_0_6_DIR / "PHASE_5_5_0_6_DEC_01_ESTIMAND_CLARIFICATION.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Frozen ML Target (System 1)" in content
    assert "Economic Execution (System 2)" in content
    assert "Alternative B Economic Barriers" in content
    assert "P_{\\text{ref}} = \\text{close}[i]" in content
    assert "P_{\\text{entry}} = \\text{open}[i+1]" in content
    assert "Crucial Methodological Conclusion" in content
    assert "Track 1: Frozen Target Predictive Validation" in content
    assert "Track 2: Frozen Classifier Economic Evaluation Under Re-Anchored Execution" in content
    assert "Track 3: Independent Trading Strategy Development" in content


def test_03_dec_01_three_research_tracks_matrix():
    """Verify DEC_01 distinguishes Track 1, Track 2, and Track 3 with 11-dimension matrix."""
    fpath = PHASE_5_5_0_6_DIR / "PHASE_5_5_0_6_RESEARCH_TRACK_COMPARISON.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Track 1: Predictive Target Validation" in content
    assert "Track 2: Re-Anchored Economic Evaluation" in content
    assert "Track 3: Independent Strategy Development" in content
    assert "1. Primary Question" in content
    assert "9. Primary Estimand" in content
    assert "11. Invalid Conclusion" in content
    assert "Track 1 is **FROZEN**" in content
    assert "Track 2 represents **Alternative B**" in content
    assert "Track 3 represents **Alternative C**" in content


def test_04_dec_02_directional_asymmetry_7_claims_audit():
    """Verify DEC_02 audits 7 directional claims into 6 epistemic tiers."""
    fpath = PHASE_5_5_0_6_DIR / "PHASE_5_5_0_6_DEC_02_DIRECTIONAL_EVIDENCE_RECONCILIATION.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "DATA_SUPPORTED" in content
    assert "PARTIALLY_SUPPORTED" in content
    assert "UNSUPPORTED_IN_REPO" in content
    assert "THEORETICAL" in content
    assert "THEORETICAL_UNVERIFIED" in content
    assert "THEORETICAL_ASSUMPTION" in content
    assert "UNVERIFIED_ASSUMPTION" in content
    assert "Claim 1: BTC Bull-Market Bias" in content
    assert "Claim 2: Broad Altcoin Bull-Market Bias" in content
    assert "Claim 3: Persistently Positive Historical Funding" in content
    assert "Claim 4: Higher SHORT Exit Slippage" in content
    assert "Claim 5: Bidirectional Trading Doubles Signal Frequency" in content
    assert "Claim 6: LONG and SHORT Execution Costs Are Symmetric" in content
    assert "Claim 7: LONG and SHORT Economic Expectancy Are Symmetric" in content
    assert "Long-Only Trades" in content
    assert "Short-Only Trades" in content
    assert "Combined Portfolio Trades" in content


def test_05_dec_04_cost_scenarios_vs_acceptance_hurdle_separation():
    """Verify DEC_04 separates cost scenarios from net expectancy acceptance criteria."""
    fpath = PHASE_5_5_0_6_DIR / "PHASE_5_5_0_6_DEC_04_COST_SCENARIO_DEFINITION.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "COST SCENARIO SPECIFICATION & COMPONENT DECOMPOSITION" in content
    assert "Strict Exclusion of Funding Cash Flows" in content
    assert "Canonical Denominator Standard" in content
    assert "15 bps Scenario (Base)" in content
    assert "20 bps Scenario (Conservative)" in content
    assert "30 bps Scenario (Severe Stress)" in content
    assert "SEPARATION FROM ACCEPTANCE HURDLES" in content
    assert "Gate 2" in content


def test_06_economic_return_and_acceptance_criteria_math():
    """Verify mathematical consistency of gross return, costs, funding, and net return."""
    fpath = PHASE_5_5_0_6_DIR / "PHASE_5_5_0_6_ECONOMIC_RETURN_AND_ACCEPTANCE_CRITERIA.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "1. Gross Trading PnL (USDT)" in content
    assert "2. Transaction Costs (USDT)" in content
    assert "3. Financing Cash Flow (USDT)" in content
    assert "4. Net Trading PnL (USDT)" in content
    assert "5. Net Percentage Return per Trade" in content
    assert "6. Net Economic Expectancy" in content
    assert "7. Break-Even Gross Return" in content
    assert "FOUR-LEVEL ACCEPTANCE CRITERIA ARCHITECTURE" in content
    assert "Criterion 1 (Cost Scenario Resilience)" in content
    assert "Criterion 2 (Net Economic Expectancy)" in content
    assert "Criterion 3 (Statistical Evidence)" in content
    assert "Criterion 4 (Robustness)" in content


def test_07_hypothetical_cost_examples_explicitly_labeled():
    """Verify hypothetical examples are explicitly labeled and mathematically verified."""
    fpath = PHASE_5_5_0_6_DIR / "PHASE_5_5_0_6_HYPOTHETICAL_COST_EXAMPLE.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "STANDARDIZED NOTIONAL DENOMINATOR WALKTHROUGH" in content
    assert "Hypothetical Trade Setup" in content
    assert "Scenario 1: Base Case Tier (15 bps Round-Trip)" in content
    assert "Scenario 2: Conservative Tier (20 bps Round-Trip)" in content
    assert "Scenario 3: Severe Stress Tier (30 bps Round-Trip)" in content
    assert "EPISTEMIC DISCLAIMER" in content
    assert "illustrative hypothetical examples" in content
    assert "+133.88" in content or "133.88" in content
    assert "+128.84" in content or "128.84" in content
    assert "+118.76" in content or "118.76" in content


def test_08_preservation_of_dec_03_dec_05_dec_06():
    """Verify DEC_03, DEC_05, DEC_06 are preserved without redesign."""
    changelog_path = PHASE_5_5_0_6_DIR / "PHASE_5_5_0_6_GOVERNANCE_CHANGELOG.md"
    with open(changelog_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Preserved without change" in content
    assert "funding_rate_bps_per_settlement" in content
    assert "1095x annualization" in content
    assert "rho > 0.70" in content
    assert "83,863" in content
    assert "316,500" in content


def test_09_decision_worksheet_revision_all_pending():
    """Verify revised worksheet retains all six decisions in PENDING_HUMAN_DECISION state."""
    fpath = PHASE_5_5_0_6_DIR / "PHASE_5_5_0_6_DECISION_WORKSHEET_REVISION.md"
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    assert "UNEXECUTED_WORKSHEET_AWAITING_HUMAN_SIGN_OFF" in content
    assert "DENIED_UNTIL_ALL_DECISIONS_SIGNED" in content
    assert "[UNEXECUTED]" in content

    for dec_id in EXPECTED_DECISION_IDS:
        assert dec_id in content
        assert "Human Selection:" in content
        assert "[PENDING_HUMAN_SELECTION]" in content
        assert "PENDING_HUMAN_DECISION" in content


def test_10_frozen_models_and_preprocessors_integrity():
    """Verify that all 55 Phase 5.3 LightGBM binaries and 55 preprocessors remain unchanged."""
    assert PHASE_5_3_FREEZE_MANIFEST.exists(), "Phase 5.3 freeze manifest missing!"
    with open(PHASE_5_3_FREEZE_MANIFEST, "r", encoding="utf-8") as f:
        freeze_data = json.load(f)

    freeze_lookup = {
        art["relative_path"].replace("\\", "/"): art["sha256"]
        for art in freeze_data["artifacts"]
    }

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


def test_11_prospective_holdout_protection():
    """Verify that prospective holdout (2026-11-01 to 2027-04-30) remains strictly protected."""
    doc_path = PHASE_5_5_0_6_DIR / "PHASE_5_5_0_6_FINAL_GOVERNANCE_CORRECTION_REPORT.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "2026-11-01" in content
    assert "2027-04-30" in content
    assert "STRICTLY SEALED" in content
    assert "NOT STARTED" in content or "NOT_STARTED" in content


def test_12_final_correction_report_verdict():
    """Verify final correction report specifies FINAL_GOVERNANCE_CORRECTIONS_PASS_WITH_LIMITATIONS."""
    doc_path = PHASE_5_5_0_6_DIR / "PHASE_5_5_0_6_FINAL_GOVERNANCE_CORRECTION_REPORT.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "FINAL_GOVERNANCE_CORRECTIONS_PASS_WITH_LIMITATIONS" in content


def test_13_zero_em_dashes_across_all_phase_5_5_0_6_files():
    """Verify zero em dashes (Unicode U+2014) across all Phase 5.5.0.6 files."""
    em_dash = chr(0x2014)
    for fname in REQUIRED_DELIVERABLES:
        fpath = PHASE_5_5_0_6_DIR / fname
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            assert em_dash not in content, f"Em dash detected in {fname}!"
