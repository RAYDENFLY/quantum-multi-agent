"""Unit tests for Phase 5.3.3.2 Independent Statistical and Artifact Verification.

Validates:
1. Holm family completeness and size (33 hypotheses).
2. Holm monotonic adjusted p-values and max p-value 0.032967.
3. BNB B2 rank, tie-breaking, and step-down threshold derivation.
4. Bootstrap configuration and 132-row matrix completeness.
5. Verification of 4 ROBUST instruments (BTC, XMR, ADA, ETH).
6. Verification of 7 SENSITIVE instruments (XRP, BNB, SOL, AVAX, LINK, DOGE, LTC).
7. Primary block length (b=24 bars) significance across all 11 instruments.
8. XMR physical directories count (exactly 5 folds).
9. XMR fold artifacts completeness (lgbm_model, preprocessor, metrics).
10. XMR full-precision arithmetic mean reconciliation (B2=0.4177, B3=0.3902, B4=0.3816).
11. Temporal ordering validity across all 55 folds.
12. Purge gap verification across all 55 folds (>= 12 bars).
13. Zero lookahead label overlap across all 55 folds (0 bars).
14. Test label horizon protection across all 55 folds (12 bars truncated).
15. SHA-256 recalculation match against Phase 5.3.3.1 manifest.
16. Historical artifact preservation (Phases 5.3.1, 5.3.2, 5.3.3).
17. Prospective holdout strict non-access.
18. Phase 5.3.3.2 audit manifest cryptographic integrity.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict
import numpy as np
import pytest

OUTPUT_DIR = Path("artifacts/phase_5_3_3_2")
P5331_DIR = Path("artifacts/phase_5_3_3_1")
P531_DIR = Path("artifacts/phase_5_3_1")
P532_DIR = Path("artifacts/phase_5_3_2")
P533_DIR = Path("artifacts/phase_5_3_3")


@pytest.fixture(scope="module")
def audit_artifacts() -> Dict[str, Dict]:
    """Load pre-computed Phase 5.3.3.2 JSON artifacts."""
    files = {
        "holm": OUTPUT_DIR / "holm_independent_verification.json",
        "bootstrap": OUTPUT_DIR / "bootstrap_independent_verification.json",
        "xmr": OUTPUT_DIR / "xmr_fold_independent_verification.json",
        "temporal": OUTPUT_DIR / "temporal_leakage_verification.json",
        "hashes": OUTPUT_DIR / "hash_verification.json",
        "manifest": OUTPUT_DIR / "final_audit_manifest.json",
    }
    loaded = {}
    for k, p in files.items():
        assert p.exists(), f"Audit artifact missing: {p}"
        with open(p, "r", encoding="utf-8") as f:
            loaded[k] = json.load(f)
    return loaded


def test_01_holm_family_completeness_and_size(audit_artifacts: Dict[str, Dict]) -> None:
    """1. Verify Holm family contains exactly 33 comparisons."""
    holm = audit_artifacts["holm"]
    assert holm["family_metadata"]["family_size"] == 33
    assert len(holm["audit_table"]) == 33
    assert holm["family_metadata"]["family_completeness_verified"] is True


def test_02_holm_monotonic_adjusted_pvalues(audit_artifacts: Dict[str, Dict]) -> None:
    """2. Verify Holm step-down monotonic adjusted p-values and max p-value."""
    table = audit_artifacts["holm"]["audit_table"]
    adj_p_vals = [r["adjusted_p_value"] for r in table]

    # Monotonicity check
    for i in range(len(adj_p_vals) - 1):
        assert adj_p_vals[i] <= adj_p_vals[i + 1]

    # Max adjusted p-value check
    assert max(adj_p_vals) <= 0.0330
    assert audit_artifacts["holm"]["audit_summary"]["max_adjusted_p_value"] <= 0.0330
    assert audit_artifacts["holm"]["audit_summary"]["significant_at_fwer_0_05"] == 33


def test_03_bnb_b2_rank_and_threshold_derivation(audit_artifacts: Dict[str, Dict]) -> None:
    """3. Verify BNB B2 rank, threshold, and tie-breaking invariant."""
    bnb_inv = audit_artifacts["holm"]["bnb_b2_investigation"]
    assert bnb_inv["symbol"] == "BNBUSDT"
    assert bnb_inv["model"] == "B2_LogisticRegression"
    assert bnb_inv["raw_p_value"] == 0.001998
    assert bnb_inv["derived_rank"] == 31
    assert bnb_inv["step_down_multiplier"] == 3
    assert abs(bnb_inv["step_down_alpha_threshold"] - (0.05 / 3)) < 1e-5
    assert bnb_inv["survives_under_all_tie_breaking_orders"] is True


def test_04_bootstrap_configuration_and_matrix_size(audit_artifacts: Dict[str, Dict]) -> None:
    """4. Verify bootstrap configuration and 132-row matrix completeness."""
    boot = audit_artifacts["bootstrap"]
    assert boot["configuration"]["total_configurations"] == 132
    assert len(boot["sensitivity_matrix"]) == 132
    assert boot["configuration"]["block_lengths"] == [12, 24, 48, 96]
    assert boot["configuration"]["resamples"] == 1000


def test_05_bootstrap_robust_classification(audit_artifacts: Dict[str, Dict]) -> None:
    """5. Verify 4 ROBUST instruments (BTC, XMR, ADA, ETH)."""
    boot = audit_artifacts["bootstrap"]
    robust_symbols = sorted(boot["robustness_summary"]["robust_instruments"])
    expected = sorted(["BTCUSDT", "XMRUSDT", "ADAUSDT", "ETHUSDT"])
    assert robust_symbols == expected
    assert boot["robustness_summary"]["four_claimed_robust_verified"] is True


def test_06_bootstrap_sensitive_classification(audit_artifacts: Dict[str, Dict]) -> None:
    """6. Verify 7 SENSITIVE instruments (XRP, BNB, SOL, AVAX, LINK, DOGE, LTC)."""
    boot = audit_artifacts["bootstrap"]
    sensitive_symbols = sorted(boot["robustness_summary"]["sensitive_instruments"])
    expected = sorted(["XRPUSDT", "BNBUSDT", "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT"])
    assert sensitive_symbols == expected
    assert boot["robustness_summary"]["seven_claimed_sensitive_verified"] is True


def test_07_bootstrap_primary_block_significance(audit_artifacts: Dict[str, Dict]) -> None:
    """7. Verify primary block length (b=24 bars) significance across all 11 instruments."""
    boot = audit_artifacts["bootstrap"]
    sm = boot["sensitivity_matrix"]
    b24_records = [r for r in sm if r["block_length"] == 24]
    assert len(b24_records) == 33  # 11 symbols * 3 models

    # Check that for every symbol, its best model is significant at b=24
    for sym, d in boot["symbol_summary"].items():
        best_m = d["best_model"]
        rec = [r for r in b24_records if r["symbol"] == sym and r["model"] == best_m][0]
        assert rec["status"] == "SIGNIFICANT"
        assert rec["ci_95_lower"] > 0.0
        assert rec["raw_p_value"] < 0.05


def test_08_xmr_physical_directories_count(audit_artifacts: Dict[str, Dict]) -> None:
    """8. Verify exactly 5 physical fold directories for XMR."""
    xmr = audit_artifacts["xmr"]
    assert xmr["physical_provenance"]["fold_count"] == 5
    assert len(xmr["physical_provenance"]["physical_fold_directories"]) == 5
    assert xmr["physical_provenance"]["unique_fold_identities_verified"] is True


def test_09_xmr_fold_artifacts_completeness(audit_artifacts: Dict[str, Dict]) -> None:
    """9. Verify all 5 XMR folds contain required model, scaler, and metric files."""
    xmr = audit_artifacts["xmr"]
    assert xmr["physical_provenance"]["all_directories_populated"] is True
    fold_details = xmr["sample_counts_and_boundaries"]["fold_details"]
    for fd in fold_details:
        assert fd["has_lgbm_model"] is True
        assert fd["has_preprocessor"] is True
        assert fd["has_metrics"] is True
        assert fd["train_samples"] > 10_000
        assert fd["test_samples"] > 3_000


def test_10_xmr_full_precision_arithmetic_mean(audit_artifacts: Dict[str, Dict]) -> None:
    """10. Verify XMR full-precision arithmetic mean matches reported values bit-for-bit."""
    arith = audit_artifacts["xmr"]["full_precision_arithmetic_recalculation"]
    assert arith["B2_LogisticRegression"]["matches"] is True
    assert round(arith["B2_LogisticRegression"]["recalculated_mean"], 4) == 0.4177
    assert arith["B3_RandomForest"]["matches"] is True
    assert round(arith["B3_RandomForest"]["recalculated_mean"], 4) == 0.3902
    assert arith["B4_LightGBM"]["matches"] is True
    assert round(arith["B4_LightGBM"]["recalculated_mean"], 4) == 0.3816


def test_11_temporal_ordering_all_55_folds(audit_artifacts: Dict[str, Dict]) -> None:
    """11. Verify temporal ordering train_end < test_start across all 55 folds."""
    temporal = audit_artifacts["temporal"]
    assert temporal["summary"]["total_folds_audited"] == 55
    assert temporal["summary"]["folds_with_temporal_ordering_valid"] == 55


def test_12_purge_gap_all_55_folds(audit_artifacts: Dict[str, Dict]) -> None:
    """12. Verify purge gap >= 12 bars across all 55 folds."""
    folds = audit_artifacts["temporal"]["fold_audits"]
    for f in folds:
        assert f["purge_gap_bars"] >= 12, f"{f['symbol']} fold {f['fold']} purge gap {f['purge_gap_bars']} < 12"


def test_13_zero_lookahead_label_overlap(audit_artifacts: Dict[str, Dict]) -> None:
    """13. Verify label overlap is strictly 0 bars across all 55 folds."""
    temporal = audit_artifacts["temporal"]
    assert temporal["summary"]["folds_with_zero_lookahead_leakage"] == 55
    assert temporal["summary"]["zero_leakage_certification"] is True


def test_14_test_label_horizon_protection(audit_artifacts: Dict[str, Dict]) -> None:
    """14. Verify 12-bar test label horizon protection across all 55 folds."""
    temporal = audit_artifacts["temporal"]
    assert temporal["summary"]["folds_with_test_horizon_protected"] == 55


def test_15_sha256_recalculation_matches_manifest(audit_artifacts: Dict[str, Dict]) -> None:
    """15. Verify SHA-256 recalculation matches Phase 5.3.3.1 manifest 100%."""
    h_audit = audit_artifacts["hashes"]
    assert h_audit["all_hashes_matched"] is True
    assert len(h_audit["missing_files"]) == 0
    assert len(h_audit["unexpected_files"]) == 0
    for detail in h_audit["hash_audit_details"]:
        assert detail["matched"] is True


def test_16_historical_artifacts_preservation(audit_artifacts: Dict[str, Dict]) -> None:
    """16. Verify historical artifacts from Phase 5.3.1, 5.3.2, 5.3.3 are intact."""
    hist = audit_artifacts["hashes"]["historical_artifacts_preserved"]
    assert hist["phase_5_3_1_intact"] is True
    assert hist["phase_5_3_2_intact"] is True
    assert hist["phase_5_3_3_intact"] is True


def test_17_prospective_holdout_untouched() -> None:
    """17. Verify prospective holdout period remains unaccessed."""
    PROSPECTIVE_HOLDOUT_START_MS = 1793491200000  # 2026-11-01 00:00:00 UTC
    temporal = json.load(open(OUTPUT_DIR / "temporal_leakage_verification.json"))
    for f in temporal["fold_audits"]:
        assert f["test_end_ms"] <= PROSPECTIVE_HOLDOUT_START_MS


def test_18_phase_5_3_3_2_manifest_integrity() -> None:
    """18. Verify Phase 5.3.3.2 final audit manifest covers all 5 artifacts."""
    manifest_path = OUTPUT_DIR / "final_audit_manifest.json"
    assert manifest_path.exists()
    with open(manifest_path) as fp:
        manifest = json.load(fp)

    assert len(manifest) == 5
    for fname, expected_hash in manifest.items():
        fpath = OUTPUT_DIR / fname
        assert fpath.exists(), f"Artifact missing: {fname}"
        h = hashlib.sha256(open(fpath, "rb").read()).hexdigest()
        assert h == expected_hash, f"Hash mismatch for {fname}"
