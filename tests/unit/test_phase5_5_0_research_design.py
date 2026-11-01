"""
QUANTUM Phase 5.5.0 Unit Tests: Economic Validation Research Design.

Validates the completeness, integrity, and governance compliance of the Phase 5.5.0
economic validation research design deliverables:
1. All 10 required deliverables exist in docs/research/phase_5_5_0/.
2. Data availability audit accurately reflects repository state (canonical data verified, funding unavailable).
3. Parameter registry enforces standardized statuses (VERIFIED, UNVERIFIED_ASSUMPTION, UNAVAILABLE, REQUIRES_HUMAN_APPROVAL).
4. Risk and limitations register covers critical economic validation risks.
5. Strict execution boundaries maintained (DESIGN ONLY, zero backtesting, zero model fitting).
6. Prospective holdout (2026-11-01 to 2027-04-30) remains strictly protected and inaccessible.
7. Frozen Phase 5.3 models and preprocessors remain 100% unchanged.
8. Zero em dashes (Unicode U+2014) in any Phase 5.5.0 file.
"""

import json
import pytest
from pathlib import Path

PHASE_5_5_0_DIR = Path("docs/research/phase_5_5_0")
PHASE_5_3_FREEZE_MANIFEST = Path("artifacts/phase_5_3_freeze/frozen_artifact_manifest.json")

REQUIRED_DELIVERABLES = [
    "PHASE_5_5_0_ECONOMIC_VALIDATION_RESEARCH_DESIGN.md",
    "PHASE_5_5_0_EXECUTION_COST_SPECIFICATION.md",
    "PHASE_5_5_0_FUNDING_AND_SLIPPAGE_SPECIFICATION.md",
    "PHASE_5_5_0_POSITION_SIZING_AND_RISK_SPECIFICATION.md",
    "PHASE_5_5_0_TEMPORAL_VALIDATION_PROTOCOL.md",
    "PHASE_5_5_0_STATISTICAL_ACCEPTANCE_CRITERIA.md",
    "PHASE_5_5_0_DATA_AVAILABILITY_AUDIT.json",
    "PHASE_5_5_0_PARAMETER_REGISTRY.json",
    "PHASE_5_5_0_RISK_AND_LIMITATIONS_REGISTER.json",
    "PHASE_5_5_0_DESIGN_APPROVAL_CHECKLIST.md"
]

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"
]


def test_01_all_10_deliverables_exist():
    """Verify that all 10 required Phase 5.5.0 deliverables exist and are non-empty."""
    assert PHASE_5_5_0_DIR.exists(), f"Missing directory {PHASE_5_5_0_DIR}"
    for fname in REQUIRED_DELIVERABLES:
        fpath = PHASE_5_5_0_DIR / fname
        assert fpath.exists(), f"Missing deliverable: {fname}"
        assert fpath.stat().st_size > 100, f"Deliverable is unexpectedly small: {fname}"


def test_02_data_availability_audit_schema_and_findings():
    """Verify data availability audit structure, symbols coverage, and critical data gaps."""
    audit_path = PHASE_5_5_0_DIR / "PHASE_5_5_0_DATA_AVAILABILITY_AUDIT.json"
    with open(audit_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "historical_market_data" in data
    assert "critical_data_gaps" in data

    # Verify all 11 instruments are accounted for
    coverage = data["historical_market_data"]["instruments_coverage"]
    assert set(coverage.keys()) == set(SYMBOLS)
    for sym in SYMBOLS:
        assert coverage[sym]["total_rows"] > 0

    # Verify critical data gaps are explicitly acknowledged
    gaps = data["critical_data_gaps"]
    assert gaps["historical_funding_rates"]["status"] == "UNAVAILABLE"
    assert gaps["orderbook_l2_depth_and_spreads"]["status"] == "UNAVAILABLE"
    assert gaps["trade_level_tick_data"]["status"] == "UNAVAILABLE"

    # Verify prospective holdout protection
    span = data["historical_market_data"]["temporal_span"]
    assert span["prospective_holdout_isolation"] == "VERIFIED_STRICTLY_INACCESSIBLE"
    assert "2026-11-01" in span["prospective_holdout_window"]


def test_03_parameter_registry_governance():
    """Verify parameter registry schema, mandatory fields, and standardized statuses."""
    reg_path = PHASE_5_5_0_DIR / "PHASE_5_5_0_PARAMETER_REGISTRY.json"
    with open(reg_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "parameters" in data
    assert len(data["parameters"]) >= 10

    valid_evidence_statuses = {"VERIFIED", "UNVERIFIED_ASSUMPTION", "UNAVAILABLE"}
    valid_approval_statuses = {"APPROVED_FOR_DESIGN", "REQUIRES_HUMAN_APPROVAL", "APPROVED"}

    for p in data["parameters"]:
        assert "parameter_name" in p
        assert "proposed_value_or_range" in p
        assert "unit" in p
        assert "source" in p
        assert "evidence_status" in p
        assert "validation_requirement" in p
        assert "sensitivity_impact" in p
        assert "approval_status" in p

        assert p["evidence_status"] in valid_evidence_statuses
        assert p["approval_status"] in valid_approval_statuses

        # Parameters with UNVERIFIED_ASSUMPTION must require human approval
        if p["evidence_status"] in ["UNVERIFIED_ASSUMPTION", "UNAVAILABLE"]:
            assert p["approval_status"] == "REQUIRES_HUMAN_APPROVAL"


def test_04_risk_and_limitations_register():
    """Verify risk register covers key economic validation vulnerabilities."""
    risk_path = PHASE_5_5_0_DIR / "PHASE_5_5_0_RISK_AND_LIMITATIONS_REGISTER.json"
    with open(risk_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "risks" in data
    assert len(data["risks"]) >= 5

    risk_ids = [r["risk_id"] for r in data["risks"]]
    assert "RISK_01_DIRECTIONAL_SYMMETRY_ASSUMPTION" in risk_ids
    assert "RISK_02_OHLCV_SLIPPAGE_PROXY_LIMITATION" in risk_ids
    assert "RISK_03_FUNDING_RATE_DATA_ABSENCE" in risk_ids
    assert "RISK_04_RETROSPECTIVE_EVALUATION_BIAS" in risk_ids
    assert "RISK_05_PORTFOLIO_CONCURRENCY_ESTIMATION" in risk_ids

    for r in data["risks"]:
        assert "mitigation_protocol" in r
        assert len(r["mitigation_protocol"]) > 20


def test_05_design_only_boundary_compliance():
    """Verify that all Markdown deliverables strictly maintain DESIGN ONLY boundaries."""
    prohibited_claims = [
        "backtest executed",
        "live trading authorized",
        "paper trading initiated",
        "retraining completed"
    ]

    for fname in REQUIRED_DELIVERABLES:
        if fname.endswith(".md"):
            fpath = PHASE_5_5_0_DIR / fname
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read().lower()
                for claim in prohibited_claims:
                    assert claim not in content, f"Prohibited claim '{claim}' found in {fname}"


def test_06_frozen_models_integrity():
    """Verify that all Phase 5.3 frozen models remain intact and unchanged."""
    assert PHASE_5_3_FREEZE_MANIFEST.exists(), "Phase 5.3 freeze manifest missing!"
    with open(PHASE_5_3_FREEZE_MANIFEST, "r", encoding="utf-8") as f:
        freeze_data = json.load(f)

    freeze_lookup = {
        art["relative_path"].replace("\\", "/"): art["sha256"]
        for art in freeze_data["artifacts"]
    }

    import hashlib
    mismatches = 0
    for sym in SYMBOLS:
        base_dir = Path("artifacts/phase_5_3_1" if sym in ["BTCUSDT", "XMRUSDT"] else "artifacts/phase_5_3_2") / sym
        for fold in range(1, 6):
            m_path = base_dir / f"fold_{fold}" / "lgbm_model.joblib"
            p_path = base_dir / f"fold_{fold}" / "preprocessor.joblib"
            assert m_path.exists(), f"Model missing: {m_path}"
            assert p_path.exists(), f"Preprocessor missing: {p_path}"

            h_m = hashlib.sha256(m_path.read_bytes()).hexdigest()
            h_p = hashlib.sha256(p_path.read_bytes()).hexdigest()

            assert h_m == freeze_lookup[str(m_path).replace("\\", "/")]
            assert h_p == freeze_lookup[str(p_path).replace("\\", "/")]


def test_07_zero_em_dashes_in_phase_5_5_0():
    """Verify zero em dashes (Unicode U+2014) across all Phase 5.5.0 deliverables."""
    em_dash = chr(0x2014)
    for fname in REQUIRED_DELIVERABLES:
        fpath = PHASE_5_5_0_DIR / fname
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            assert em_dash not in content, f"Em dash detected in {fname}!"
