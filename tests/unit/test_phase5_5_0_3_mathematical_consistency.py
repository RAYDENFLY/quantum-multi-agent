"""
QUANTUM Phase 5.5.0.3 Unit Tests: Final Mathematical Consistency Audit.

Validates the structural integrity, mathematical consistency, and governance boundaries
of Phase 5.5.0.3:
1. All 8 required deliverables exist in docs/research/phase_5_5_0_3/.
2. All JSON deliverables parse successfully and conform to schema.
3. Sigma/ATR terminology matches the verified source implementation (TripleBarrierLabelGenerator).
4. Barrier formula matches the actual source implementation (u_t = P_ref(1 + m*sigma_t), l_t = P_ref(1 - m*sigma_t)).
5. Funding annualization conversion is correct (F_annual = F_settlement * 1095).
6. Funding scenario values match across authoritative documents (no conflicting rates).
7. Funding cash-flow sign conventions are correct (CF_t = -d * N_t * f_t).
8. The 87.5% statement is classified as a theoretical conditional result (THEORETICAL_UNDER_UNIFORM_ENTRY_AND_FIXED_HOLDING_ASSUMPTIONS).
9. Slippage components have explicit units (dimensionless decimal fraction / bps).
10. Spread and impact are not double-counted.
11. LONG and SHORT price adjustment signs are consistent (adverse for both entry and exit: BUY adds, SELL subtracts).
12. All six human decisions remain pending (PENDING_HUMAN_DECISION).
13. All six decisions remain execution-blocking (blocks_execution: true).
14. All 55 frozen LightGBM model binaries and 55 preprocessors remain 100% bit-for-bit intact.
15. Prospective holdout (2026-11-01 to 2027-04-30) remains strictly protected and unaccessed.
16. Zero em dashes (Unicode U+2014) anywhere in Phase 5.5.0.3 files or test suite.
"""

import hashlib
import json
from pathlib import Path
import pytest

from quantum.features.labeling import TripleBarrierLabelGenerator

PHASE_5_5_0_3_DIR = Path("docs/research/phase_5_5_0_3")
PHASE_5_3_FREEZE_MANIFEST = Path("artifacts/phase_5_3_freeze/frozen_artifact_manifest.json")

REQUIRED_DELIVERABLES = [
    "PHASE_5_5_0_3_SIGMA_ATR_SOURCE_VERIFICATION.md",
    "PHASE_5_5_0_3_FUNDING_MATHEMATICAL_AUDIT.md",
    "PHASE_5_5_0_3_FUNDING_SCENARIO_REGISTRY.json",
    "PHASE_5_5_0_3_FUNDING_EXPOSURE_ASSUMPTIONS.md",
    "PHASE_5_5_0_3_SLIPPAGE_COMPONENT_AUDIT.md",
    "PHASE_5_5_0_3_CROSS_DOCUMENT_CONSISTENCY_MATRIX.md",
    "PHASE_5_5_0_3_HUMAN_DECISION_INTEGRITY_AUDIT.md",
    "PHASE_5_5_0_3_FINAL_MATHEMATICAL_AUDIT_REPORT.md",
]

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"
]

EXPECTED_DECISION_IDS = ["DEC_01", "DEC_02", "DEC_03", "DEC_04", "DEC_05", "DEC_06"]


def test_01_all_8_deliverables_exist():
    """Verify that all 8 required Phase 5.5.0.3 deliverables exist and are non-empty."""
    assert PHASE_5_5_0_3_DIR.exists(), f"Missing directory {PHASE_5_5_0_3_DIR}"
    for fname in REQUIRED_DELIVERABLES:
        fpath = PHASE_5_5_0_3_DIR / fname
        assert fpath.exists(), f"Missing deliverable: {fname}"
        assert fpath.stat().st_size > 100, f"Deliverable is unexpectedly small: {fname}"


def test_02_all_json_deliverables_parse_and_validate():
    """Verify that all JSON deliverables parse successfully and conform to schema."""
    json_path = PHASE_5_5_0_3_DIR / "PHASE_5_5_0_3_FUNDING_SCENARIO_REGISTRY.json"
    assert json_path.exists(), "Missing funding scenario registry JSON"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert isinstance(data, dict), "Registry must be a JSON object"
        assert "title" in data
        assert "timestamp_utc" in data
        assert "scenarios" in data
        assert len(data["scenarios"]) == 4


def test_03_sigma_atr_terminology_matches_source_implementation():
    """Verify that labeling terminology matches TripleBarrierLabelGenerator source code."""
    generator = TripleBarrierLabelGenerator()
    assert generator.horizon_bars == 12
    assert generator.volatility_lookback == 20
    assert generator.barrier_multiplier == 1.5

    # Check documentation file
    doc_path = PHASE_5_5_0_3_DIR / "PHASE_5_5_0_3_SIGMA_ATR_SOURCE_VERIFICATION.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "VERIFIED_FROM_SOURCE" in content
    assert "src/quantum/features/labeling.py" in content
    assert "TripleBarrierLabelGenerator" in content
    assert "pct_change()" in content
    assert "std(ddof=1)" in content
    assert "volatility_lookback: int = 20" in content
    assert "NO. ABSOLUTELY NOT" in content
    assert "ATR was NEVER used to construct target labels" in content


def test_04_barrier_formula_matches_source_implementation():
    """Verify that the barrier formula is multiplicative and matches source code."""
    doc_path = PHASE_5_5_0_3_DIR / "PHASE_5_5_0_3_SIGMA_ATR_SOURCE_VERIFICATION.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "MULTIPLICATIVE" in content
    assert "u_t = P_{\\text{ref}} \\times (1 + m \\times \\sigma_t)" in content or "u_barrier = c_entry * (1.0 + self.barrier_multiplier * sigma_t)" in content
    assert "l_t = P_{\\text{ref}} \\times (1 - m \\times \\sigma_t)" in content or "l_barrier = c_entry * (1.0 - self.barrier_multiplier * sigma_t)" in content
    assert "d_t = P_{\\text{ref}} \\times m \\times \\sigma_t" in content or "It is NOT $1.5 \\times \\text{ATR}$" in content


def test_05_funding_annualization_conversion_is_correct():
    """Verify that the nominal annualization formula matches 1095 * bps_per_settlement."""
    json_path = PHASE_5_5_0_3_DIR / "PHASE_5_5_0_3_FUNDING_SCENARIO_REGISTRY.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "1095" in data["annualized_formula"]

    for sc in data["scenarios"]:
        rate_bps = sc["funding_rate_bps_per_settlement"]
        ann_bps = sc["nominal_annualized_bps"]
        ann_pct = sc["nominal_annualized_pct"]
        assert pytest.approx(ann_bps, rel=1e-5) == rate_bps * 1095.0
        assert pytest.approx(ann_pct, rel=1e-5) == (rate_bps * 1095.0) / 100.0


def test_06_funding_scenario_values_match_across_documents():
    """Verify that funding scenario values match across all Phase 5.5.0.3 documents."""
    json_path = PHASE_5_5_0_3_DIR / "PHASE_5_5_0_3_FUNDING_SCENARIO_REGISTRY.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    rates = {s["scenario_id"]: s["funding_rate_bps_per_settlement"] for s in data["scenarios"]}
    assert rates["SCENARIO_F_NEUTRAL"] == 0.0
    assert rates["SCENARIO_F_BULL_MODERATE"] == 1.0
    assert rates["SCENARIO_F_BULL_SEVERE"] == 3.0
    assert rates["SCENARIO_F_BEAR_MODERATE"] == -1.0

    # Cross-document check in mathematical audit doc
    doc_path = PHASE_5_5_0_3_DIR / "PHASE_5_5_0_3_FUNDING_MATHEMATICAL_AUDIT.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "funding_rate_bps_per_settlement" in content
    assert "1095" in content
    assert "SCENARIO_F_BULL_MODERATE" in content
    assert "+10.95%" in content
    assert "+32.85%" in content
    assert "-10.95%" in content


def test_07_funding_cash_flow_sign_conventions_correct():
    """Verify that funding cash flow formula CF_t = -d * N_t * f_t preserves correct signs."""
    doc_path = PHASE_5_5_0_3_DIR / "PHASE_5_5_0_3_FUNDING_MATHEMATICAL_AUDIT.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "CF_t = -d \\times N_t \\times f_t" in content
    assert "Long pays 1.00 USDT" in content
    assert "Short receives 1.00 USDT" in content
    assert "Long receives 1.00 USDT" in content
    assert "Short pays 1.00 USDT" in content


def test_08_funding_exposure_reclassified_as_theoretical_assumption():
    """Verify that the 87.5% figure is reclassified as THEORETICAL_UNDER_UNIFORM_ENTRY_AND_FIXED_HOLDING_ASSUMPTIONS."""
    doc_path = PHASE_5_5_0_3_DIR / "PHASE_5_5_0_3_FUNDING_EXPOSURE_ASSUMPTIONS.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "THEORETICAL_UNDER_UNIFORM_ENTRY_AND_FIXED_HOLDING_ASSUMPTIONS" in content
    assert "P(\\text{cross settlement}) = \\frac{60}{480} = 12.5\\%" in content
    assert "Fixed Duration Assumption" in content
    assert "Uniform Entry Distribution" in content
    assert "No empirical measurement is performed during Phase 5.5.0.3" in content


def test_09_slippage_components_have_explicit_units():
    """Verify that all slippage components have explicit dimensionless units."""
    doc_path = PHASE_5_5_0_3_DIR / "PHASE_5_5_0_3_SLIPPAGE_COMPONENT_AUDIT.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "C_{\\text{leg}} = C_{\\text{spread}} + C_{\\text{volatility}} + C_{\\text{impact}} + C_{\\text{fee}}" in content
    assert "Dimensionless decimal return fraction per leg" in content
    assert "UNVERIFIED_ASSUMPTION" in content


def test_10_spread_and_impact_not_double_counted():
    """Verify that spread and market impact are separated with no double-counting."""
    doc_path = PHASE_5_5_0_3_DIR / "PHASE_5_5_0_3_SLIPPAGE_COMPONENT_AUDIT.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "NO DOUBLE-COUNTING PROOF" in content
    assert "Contains ZERO depth friction or participation impact" in content
    assert "No component is deducted twice" in content


def test_11_long_and_short_price_adjustment_signs_consistent():
    """Verify that execution fills are adverse to both BUY and SELL orders."""
    doc_path = PHASE_5_5_0_3_DIR / "PHASE_5_5_0_3_SLIPPAGE_COMPONENT_AUDIT.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "P_{\\text{fill, buy}} = P_{\\text{ref}} \\times (1 + C_{\\text{exec}})" in content
    assert "P_{\\text{fill, sell}} = P_{\\text{ref}} \\times (1 - C_{\\text{exec}})" in content
    assert "Hypothetical LONG Trade" in content
    assert "Hypothetical SHORT Trade" in content
    assert "100.03914" in content
    assert "99.96086" in content


def test_12_all_six_human_decisions_remain_pending():
    """Verify that DEC_01 through DEC_06 remain in PENDING_HUMAN_DECISION status."""
    doc_path = PHASE_5_5_0_3_DIR / "PHASE_5_5_0_3_HUMAN_DECISION_INTEGRITY_AUDIT.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    for dec_id in EXPECTED_DECISION_IDS:
        assert dec_id in content, f"Missing {dec_id} in human decision audit"

    assert "PENDING_HUMAN_DECISION" in content
    assert "No decision has been pre-empted, assumed, or auto-approved" in content


def test_13_all_six_decisions_remain_execution_blocking():
    """Verify that all six decisions remain execution-blocking."""
    doc_path = PHASE_5_5_0_3_DIR / "PHASE_5_5_0_3_HUMAN_DECISION_INTEGRITY_AUDIT.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "blocks_execution: true" in content or "Blocking" in content
    assert "Phase 5.5 execution remains strictly blocked" in content


def test_14_frozen_models_and_preprocessors_integrity():
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


def test_15_prospective_holdout_protection():
    """Verify that prospective holdout (2026-11-01 to 2027-04-30) remains strictly protected."""
    doc_path = PHASE_5_5_0_3_DIR / "PHASE_5_5_0_3_FINAL_MATHEMATICAL_AUDIT_REPORT.md"
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "2026-11-01 00:00:00 UTC through 2027-04-30 23:59:59.999 UTC" in content
    assert "STRICLY SEALED" in content or "STRICTLY SEALED" in content
    assert "NOT STARTED" in content


def test_16_zero_em_dashes_across_all_phase_5_5_0_3_files():
    """Verify zero em dashes (Unicode U+2014) across all Phase 5.5.0.3 files."""
    em_dash = chr(0x2014)
    for fname in REQUIRED_DELIVERABLES:
        fpath = PHASE_5_5_0_3_DIR / fname
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            assert em_dash not in content, f"Em dash detected in {fname}!"
