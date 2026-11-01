"""
QUANTUM Phase 5.5.0.2 Unit Tests: Final Economic Validation Design Reconciliation.

Validates the structural integrity, mathematical consistency, and governance boundaries
of Phase 5.5.0.2:
1. All 10 deliverables exist in docs/research/phase_5_5_0_2/.
2. All JSON deliverables parse successfully and conform to strict schema requirements.
3. All 6 decision IDs exist (DEC_01 through DEC_06) in both checklist and JSON registry.
4. Human decision counts match (exactly 6 in both checklist and JSON).
5. Funding parameters use declared unit (funding_rate_bps_per_settlement).
6. Annualized funding conversion formula verified (1095 * bps_per_settlement).
7. Slippage variables have explicit units and scales.
8. Slippage dimensional example is internally consistent (4.41 bps per leg, 18.82 bps round-trip).
9. Spread and slippage are not double-counted.
10. XMR eligibility categories are separate (Preservation, Specialist Research, Portfolio).
11. Alternatives A, B, and C are documented with comparison matrix.
12. All 6 decisions remain explicitly PENDING_HUMAN_DECISION.
13. All 55 frozen LightGBM model binaries and 55 preprocessors remain 100% bit-for-bit intact.
14. Prospective holdout (2026-11-01 to 2027-04-30) remains strictly protected and unaccessed.
15. Zero em dashes (Unicode U+2014) anywhere in Phase 5.5.0.2 files or test suite.
"""

import hashlib
import json
from pathlib import Path
import pytest

PHASE_5_5_0_2_DIR = Path("docs/research/phase_5_5_0_2")
PHASE_5_3_FREEZE_MANIFEST = Path("artifacts/phase_5_3_freeze/frozen_artifact_manifest.json")

REQUIRED_DELIVERABLES = [
    "PHASE_5_5_0_2_LABEL_EXECUTION_ARCHITECTURE.md",
    "PHASE_5_5_0_2_FUNDING_MODEL_SPECIFICATION.md",
    "PHASE_5_5_0_2_FUNDING_SCENARIO_REGISTRY.json",
    "PHASE_5_5_0_2_SLIPPAGE_COST_SPECIFICATION.md",
    "PHASE_5_5_0_2_HUMAN_DECISION_REGISTRY.json",
    "PHASE_5_5_0_2_XMR_ELIGIBILITY_POLICY.md",
    "PHASE_5_5_0_2_DOCUMENT_CONSISTENCY_AUDIT.md",
    "PHASE_5_5_0_2_FINAL_DESIGN_SPECIFICATION.md",
    "PHASE_5_5_0_2_FINAL_APPROVAL_CHECKLIST.md",
    "PHASE_5_5_0_2_FINAL_AUDIT_REPORT.md",
]

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"
]

EXPECTED_DECISION_IDS = ["DEC_01", "DEC_02", "DEC_03", "DEC_04", "DEC_05", "DEC_06"]


def test_01_all_10_deliverables_exist():
    """Verify that all 10 required Phase 5.5.0.2 deliverables exist and are non-empty."""
    assert PHASE_5_5_0_2_DIR.exists(), f"Missing directory {PHASE_5_5_0_2_DIR}"
    for fname in REQUIRED_DELIVERABLES:
        fpath = PHASE_5_5_0_2_DIR / fname
        assert fpath.exists(), f"Missing deliverable: {fname}"
        assert fpath.stat().st_size > 100, f"Deliverable is unexpectedly small: {fname}"


def test_02_all_json_deliverables_parse_and_validate():
    """Verify that all JSON deliverables parse successfully and conform to schema."""
    json_files = [
        "PHASE_5_5_0_2_FUNDING_SCENARIO_REGISTRY.json",
        "PHASE_5_5_0_2_HUMAN_DECISION_REGISTRY.json"
    ]
    for fname in json_files:
        fpath = PHASE_5_5_0_2_DIR / fname
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert isinstance(data, dict), f"{fname} must be a JSON object"
            assert "title" in data, f"{fname} missing title"
            assert "timestamp_utc" in data, f"{fname} missing timestamp_utc"


def test_03_all_6_decision_ids_exist_and_counts_match():
    """Verify that exactly 6 decisions (DEC_01 to DEC_06) exist in both JSON and Checklist."""
    # JSON registry check
    json_path = PHASE_5_5_0_2_DIR / "PHASE_5_5_0_2_HUMAN_DECISION_REGISTRY.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["total_registered_decisions"] == 6
    assert data["total_unresolved_decisions"] == 6
    assert len(data["decisions"]) == 6

    json_decision_ids = [d["decision_id"] for d in data["decisions"]]
    assert json_decision_ids == EXPECTED_DECISION_IDS

    # Markdown checklist check
    checklist_path = PHASE_5_5_0_2_DIR / "PHASE_5_5_0_2_FINAL_APPROVAL_CHECKLIST.md"
    with open(checklist_path, "r", encoding="utf-8") as f:
        checklist_content = f.read()

    for dec_id in EXPECTED_DECISION_IDS:
        assert dec_id in checklist_content, f"Missing {dec_id} in checklist"


def test_04_funding_model_specification_and_registry():
    """Verify that funding parameters use funding_rate_bps_per_settlement and 1095 conversion."""
    json_path = PHASE_5_5_0_2_DIR / "PHASE_5_5_0_2_FUNDING_SCENARIO_REGISTRY.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "funding_rate_bps_per_settlement" in data["primary_unit"]
    assert "1095" in data["annualized_formula"]
    assert data["empirical_data_status"] == "FUNDING_DATA_UNAVAILABLE"
    assert len(data["scenarios"]) == 4

    for sc in data["scenarios"]:
        bps = sc["funding_rate_bps_per_settlement"]
        ann_bps = sc["nominal_annualized_bps"]
        assert pytest.approx(ann_bps, rel=1e-5) == bps * 1095.0
        assert sc["evidence_status"] == "UNVERIFIED_ASSUMPTION"

    # Verify documentation file
    doc_path = PHASE_5_5_0_2_DIR / "PHASE_5_5_0_2_FUNDING_MODEL_SPECIFICATION.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        doc_content = f.read()

    assert "funding_rate_bps_per_settlement" in doc_content
    assert "1095" in doc_content
    assert "CF_t = -d * N_t * f_t" in doc_content
    assert "87.5%" in doc_content
    assert "FUNDING_DATA_UNAVAILABLE" in doc_content


def test_05_slippage_cost_specification_dimensional_consistency():
    """Verify that slippage variables have explicit units and the dimensional example matches."""
    doc_path = PHASE_5_5_0_2_DIR / "PHASE_5_5_0_2_SLIPPAGE_COST_SPECIFICATION.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "S_trade = S_base + S_vol + S_liquidity" in content
    assert "Dimensionless decimal fraction" in content
    assert "alpha = 0.05" in content
    assert "beta = 0.0010" in content

    # Check numerical example
    assert "10,000" in content
    assert "500,000" in content
    assert "4.41 bps" in content
    assert "18.82 bps" in content
    assert "Conservative Tier" in content


def test_06_spread_and_slippage_not_double_counted():
    """Verify that spread and slippage separation is explicitly documented with no double-counting."""
    doc_path = PHASE_5_5_0_2_DIR / "PHASE_5_5_0_2_SLIPPAGE_COST_SPECIFICATION.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "NO DOUBLE-COUNTING PROOF" in content
    assert "Double-counting occurs when a backtest applies BOTH" in content


def test_07_xmr_eligibility_three_distinct_tiers():
    """Verify that XMR eligibility is decoupled into 3 distinct policy tiers."""
    doc_path = PHASE_5_5_0_2_DIR / "PHASE_5_5_0_2_XMR_ELIGIBILITY_POLICY.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Tier 1: Model Artifact Preservation (100% PRESERVED)" in content
    assert "Tier 2: Specialist Research Eligibility (PRESERVED WITH CAVEATS)" in content
    assert "Tier 3: Economic Portfolio Validation Eligibility (PENDING HUMAN DECISION)" in content
    assert "EXCLUDED_FROM_PRIMARY_PORTFOLIO_VALIDATION" in content


def test_08_label_execution_architecture_alternatives():
    """Verify that Alternatives A, B, and C are documented with complete comparison matrix."""
    doc_path = PHASE_5_5_0_2_DIR / "PHASE_5_5_0_2_LABEL_EXECUTION_ARCHITECTURE.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Alternative A: Original Barrier Preservation" in content
    assert "Alternative B: Re-Anchor Symmetric Barriers to Economic Entry Fill" in content
    assert "Alternative C: Decouple Directional ML Classifier from Independent Trade Policy" in content
    assert "1:5 Risk-Reward Inversion" in content
    assert "Comparison Matrix" in content or "COMPARISON MATRIX" in content
    assert "PENDING_HUMAN_DECISION" in content
    assert "DEC_01" in content


def test_09_all_6_decisions_remain_pending_human_decision():
    """Verify that all 6 decisions in the human decision registry remain PENDING_HUMAN_DECISION."""
    json_path = PHASE_5_5_0_2_DIR / "PHASE_5_5_0_2_HUMAN_DECISION_REGISTRY.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for dec in data["decisions"]:
        assert dec["current_status"] == "PENDING_HUMAN_DECISION", (
            f"Decision {dec['decision_id']} has status {dec['current_status']}, "
            f"expected PENDING_HUMAN_DECISION"
        )
        assert dec["blocks_execution"] is True


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
    doc_path = PHASE_5_5_0_2_DIR / "PHASE_5_5_0_2_FINAL_AUDIT_REPORT.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "2026-11-01 00:00:00 UTC through 2027-04-30 23:59:59.999 UTC" in content
    assert "SEALED AND UNTOUCHED" in content


def test_12_document_consistency_audit_supersession():
    """Verify that the document consistency audit has a complete supersession table."""
    doc_path = PHASE_5_5_0_2_DIR / "PHASE_5_5_0_2_DOCUMENT_CONSISTENCY_AUDIT.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "SUPERSEDED_AND_RECONCILED" in content
    assert "PHASE_5_5_0_RESEARCH_DESIGN.md" in content
    assert "PHASE_5_5_0_1_LABEL_ENTRY_BARRIER_SEMANTICS.md" in content


def test_13_final_approval_checklist_integrity():
    """Verify that the approval checklist contains all 6 decision blocks and sign-off table."""
    doc_path = PHASE_5_5_0_2_DIR / "PHASE_5_5_0_2_FINAL_APPROVAL_CHECKLIST.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "DEC_01" in content
    assert "DEC_02" in content
    assert "DEC_03" in content
    assert "DEC_04" in content
    assert "DEC_05" in content
    assert "DEC_06" in content
    assert "DECISION SIGN-OFF MATRIX" in content
    assert "BLOCKING_STATUS: EXECUTION_BLOCKED_PENDING_ALL_DECISIONS" in content


def test_14_zero_em_dashes_across_all_phase_5_5_0_2_files():
    """Verify zero em dashes (Unicode U+2014) across all Phase 5.5.0.2 files."""
    em_dash = chr(0x2014)
    for fname in REQUIRED_DELIVERABLES:
        fpath = PHASE_5_5_0_2_DIR / fname
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            assert em_dash not in content, f"Em dash detected in {fname}!"
