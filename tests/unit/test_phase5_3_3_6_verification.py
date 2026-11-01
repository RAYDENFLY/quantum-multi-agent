"""
Unit tests for Phase 5.3.3.6: Final OOF Population & Bootstrap Implementation Verification.
Covers OOF timestamp population reconciliation, Moving Block Bootstrap boundary and remainder
protection, tuple and class support preservation, deterministic seeding, Hall & Wilson null
centering consistency, class support weighting decomposition, and governance invariants.
"""

import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import pytest

sys.path.insert(0, "scripts")
from run_phase5_3_3_5_paired_audit import (
    extract_continuous_segments,
    build_candidate_blocks,
    compute_prefix_contingency_paired,
    run_paired_empirical_mbb,
)

ARTIFACTS_DIR = Path("artifacts/phase_5_3_3_6")
DOCS_DIR = Path("docs")
SCRIPTS_DIR = Path("scripts")
TESTS_DIR = Path("tests/unit")

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"
]


def test_01_all_phase5_3_3_6_artifacts_and_docs_exist():
    expected_artifacts = [
        "oof_population_audit.json",
        "bootstrap_implementation_audit.json",
        "final_audit_manifest.json",
    ]
    for fname in expected_artifacts:
        p = ARTIFACTS_DIR / fname
        assert p.exists(), f"Missing artifact: {p}"
        assert p.stat().st_size > 100, f"Empty artifact: {p}"

    expected_docs = [
        "PHASE_5_3_3_6_OOF_POPULATION_AUDIT.md",
        "PHASE_5_3_3_6_BOOTSTRAP_IMPLEMENTATION_AUDIT.md",
        "PHASE_5_3_3_6_FINAL_REPORT.md",
    ]
    for dname in expected_docs:
        p = DOCS_DIR / dname
        assert p.exists(), f"Missing doc: {p}"
        assert p.stat().st_size > 500, f"Empty doc: {p}"


def test_02_oof_population_exact_reconciliation_between_phases():
    with open(ARTIFACTS_DIR / "oof_population_audit.json", encoding="utf-8") as f:
        data = json.load(f)

    assert data["fleet_total_oof_observations"] == 1_322_108
    total_intersection = 0
    for sym in SYMBOLS:
        inst = data["instruments"][sym]
        c4 = inst["phase_5_3_3_4_artifact_oof_count"]
        c5 = inst["phase_5_3_3_5_artifact_oof_count"]
        inter = inst["timestamp_intersection_count"]
        assert c4 == c5 == inter, f"{sym}: mismatch c4={c4}, c5={c5}, inter={inter}"
        assert inst["timestamps_only_in_phase_5_3_3_4_artifact"] == 0
        assert inst["timestamps_only_in_phase_5_3_3_5_artifact"] == 0
        assert inst["duplicate_timestamp_count"] == 0
        assert inst["multi_fold_timestamp_overlap_count"] == 0
        assert inst["fold_membership_differences_count"] == 0
        assert inst["b4_b0_timestamp_label_alignment_verified"] is True
        assert sum(inst["fold_sample_counts"]) == inter
        # Verify prose differences are accounted for
        assert (
            inst["phase_5_3_3_4_prose_doc_reported_count"] - c4
            == inst["phase_5_3_3_4_prose_vs_artifact_diff"]
        )
        assert (
            inst["phase_5_3_3_5_chat_table_reported_count"] - c5
            == inst["phase_5_3_3_5_chat_vs_artifact_diff"]
        )
        total_intersection += inter

    assert total_intersection == 1_322_108


def test_03_mbb_candidate_and_remainder_blocks_never_cross_boundaries():
    with open(ARTIFACTS_DIR / "bootstrap_implementation_audit.json", encoding="utf-8") as f:
        data = json.load(f)

    summary = data["verification_summary"]
    assert summary["total_configurations_audited"] == 44
    assert summary["total_replicates_audited"] == 440_000
    assert summary["total_fold_crossing_blocks"] == 0
    assert summary["total_discontinuity_crossing_blocks"] == 0
    assert summary["total_remainder_boundary_crossings"] == 0

    for sym in SYMBOLS:
        inst = data["instruments"][sym]
        assert inst["tuple_preservation_verified"] is True
        assert inst["deterministic_reproduction_exact"] is True
        for b in [12, 24, 48, 96]:
            b_audit = inst["block_length_audits"][f"b_{b}"]
            assert b_audit["fold_crossing_blocks"] == 0
            assert b_audit["discontinuity_crossing_blocks"] == 0
            assert b_audit["remainder_fold_crossings"] == 0
            assert b_audit["remainder_discontinuity_crossings"] == 0

    # Synthetic edge case: remainder r > 0 with short segments and fold boundaries
    ts_seg1 = np.arange(0, 14 * 300_000, 300_000, dtype=np.int64)
    ts_seg2 = np.arange(20 * 300_000, 23 * 300_000, 300_000, dtype=np.int64)  # length 3 < remainder 5
    ts_seg3 = np.arange(23 * 300_000, 39 * 300_000, 300_000, dtype=np.int64)  # fold 2, length 16
    ts_all = np.concatenate([ts_seg1, ts_seg2, ts_seg3])
    folds_all = np.array([1] * 14 + [1] * 3 + [2] * 16, dtype=np.int32)
    # Total N = 33. For b = 12, K = 2, r = 9.
    segs = extract_continuous_segments(ts_all, folds_all, timeframe_ms=300_000)
    assert segs == [(0, 14), (14, 17), (17, 33)]
    full_cands = build_candidate_blocks(segs, 12)
    rem_cands = build_candidate_blocks(segs, 9)
    # Segment (14, 17) of length 3 cannot contribute to full (12) or remainder (9) blocks
    for st in full_cands:
        assert len(np.unique(folds_all[st : st + 12])) == 1
        assert np.all(np.diff(ts_all[st : st + 12]) == 300_000)
    for st in rem_cands:
        assert len(np.unique(folds_all[st : st + 9])) == 1
        assert np.all(np.diff(ts_all[st : st + 9]) == 300_000)


def test_04_mbb_exact_sample_length_and_positive_class_support():
    with open(ARTIFACTS_DIR / "bootstrap_implementation_audit.json", encoding="utf-8") as f:
        data = json.load(f)

    for sym in SYMBOLS:
        inst = data["instruments"][sym]
        tot_n = inst["total_oof_samples"]
        for b in [12, 24, 48, 96]:
            b_audit = inst["block_length_audits"][f"b_{b}"]
            assert b_audit["intended_sample_length"] == tot_n
            assert b_audit["min_replicate_sample_length"] == tot_n
            assert b_audit["max_replicate_sample_length"] == tot_n
            assert b_audit["exact_sample_length_preserved"] is True
            assert b_audit["full_blocks_per_replicate"] * b + b_audit["remainder_length"] == tot_n
            supp = b_audit["min_resampled_support"]
            assert supp["SL"] > 0
            assert supp["EXP"] > 0
            assert supp["TP"] > 0
            assert b_audit["zero_support_replicate_count"] == 0
            assert b_audit["discarded_replicate_count"] == 0


def test_05_mbb_deterministic_seed_reproducibility():
    rng = np.random.default_rng(99)
    n = 300
    ts = np.arange(0, n * 300_000, 300_000, dtype=np.int64)
    folds = np.ones(n, dtype=np.int32)
    y_true = rng.choice([-1, 0, 1], size=n).astype(np.int32)
    y_b4 = y_true.copy()
    flip_idx = rng.choice(n, size=80, replace=False)
    y_b4[flip_idx] = rng.choice([-1, 0, 1], size=80).astype(np.int32)
    y_b0 = np.ones(n, dtype=np.int32)

    segs = extract_continuous_segments(ts, folds, 300_000)
    prefix = compute_prefix_contingency_paired(y_true, y_b4, y_b0)
    res1 = run_paired_empirical_mbb(prefix, segs, b=12, observed_paired_delta=0.25, observed_b4_ba=0.58, observed_b0_ba=0.33, B=500, seed=66)
    res2 = run_paired_empirical_mbb(prefix, segs, b=12, observed_paired_delta=0.25, observed_b4_ba=0.58, observed_b0_ba=0.33, B=500, seed=66)
    res3 = run_paired_empirical_mbb(prefix, segs, b=12, observed_paired_delta=0.25, observed_b4_ba=0.58, observed_b0_ba=0.33, B=500, seed=67)

    assert res1 == res2, "Identical seeds must produce bit-identical results"
    assert res1["ci_95_percentile"] != res3["ci_95_percentile"], "Different seeds must produce distinct resamples"


def test_06_null_centering_and_exceedance_consistency():
    with open(ARTIFACTS_DIR / "bootstrap_implementation_audit.json", encoding="utf-8") as f:
        data = json.load(f)

    for sym in SYMBOLS:
        inst = data["instruments"][sym]
        for b in [12, 24, 48, 96]:
            b_audit = inst["block_length_audits"][f"b_{b}"]
            obs = b_audit["observed_paired_delta"]
            b_mean = b_audit["bootstrap_mean_delta"]
            b_std = b_audit["bootstrap_std_error"]
            n_mean = b_audit["centered_null_mean"]
            n_std = b_audit["centered_null_std"]
            n_max = b_audit["centered_null_max"]
            ci_low, ci_high = b_audit["ci_95_percentile"]
            n_low, n_high = b_audit["centered_null_95_range"]

            assert n_mean == pytest.approx(b_mean - obs, abs=1e-5)
            assert n_std == pytest.approx(b_std, abs=1e-5)
            assert n_low == pytest.approx(ci_low - obs, abs=1e-5)
            assert n_high == pytest.approx(ci_high - obs, abs=1e-5)
            assert b_audit["null_exceed_count"] == 0
            assert n_max < obs, f"{sym} b={b}: centered_null_max {n_max} >= obs {obs}"
            assert b_audit["p_value_bound"] == "p < 1/10001 (p < 0.000100)"


def test_07_class_support_weighting_reconciles_pooled_vs_fold_mean_ba():
    with open(ARTIFACTS_DIR / "oof_population_audit.json", encoding="utf-8") as f:
        data = json.load(f)

    for sym in SYMBOLS:
        inst = data["instruments"][sym]
        cw = inst["class_support_weighting_ba_contribution"]
        tot_diff = inst["total_pooled_minus_fold_mean_ba"]
        sum_cw = cw["SL"] + cw["EXP"] + cw["TP"]
        assert sum_cw == pytest.approx(tot_diff, abs=1e-5), (
            f"{sym}: class weight sum {sum_cw} != total diff {tot_diff}"
        )


def test_08_governance_and_holdout_protection():
    with open(ARTIFACTS_DIR / "oof_population_audit.json", encoding="utf-8") as f:
        data = json.load(f)

    for sym in SYMBOLS:
        inst = data["instruments"][sym]
        assert inst["first_oof_timestamp_ms"] >= 1698796800000
        assert inst["last_oof_timestamp_ms"] <= 1777593599999


def test_09_manifest_sha256_integrity_and_no_em_dashes():
    with open(ARTIFACTS_DIR / "final_audit_manifest.json", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["phase"] == "5.3.3.6"
    assert manifest["verdict"] == "PHASE_5_3_3_6_PASS"
    assert manifest["phase_5_4_gate_status"] == "HOLD"
    assert manifest["fleet_total_oof_observations"] == 1_322_108

    for fname, meta in manifest["files"].items():
        p = Path(meta["path"])
        assert p.exists(), f"Missing manifest file: {p}"
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        assert h == meta["sha256"], f"SHA-256 mismatch for {p}"
        assert p.stat().st_size == meta["bytes"], f"Byte size mismatch for {p}"

    files_to_check = [
        ARTIFACTS_DIR / "oof_population_audit.json",
        ARTIFACTS_DIR / "bootstrap_implementation_audit.json",
        ARTIFACTS_DIR / "final_audit_manifest.json",
        DOCS_DIR / "PHASE_5_3_3_6_OOF_POPULATION_AUDIT.md",
        DOCS_DIR / "PHASE_5_3_3_6_BOOTSTRAP_IMPLEMENTATION_AUDIT.md",
        DOCS_DIR / "PHASE_5_3_3_6_FINAL_REPORT.md",
        SCRIPTS_DIR / "run_phase5_3_3_6_verification_audit.py",
        TESTS_DIR / "test_phase5_3_3_6_verification.py",
    ]
    em_dash = "\u2014"
    for fpath in files_to_check:
        text = fpath.read_text(encoding="utf-8")
        assert em_dash not in text, f"Forbidden em-dash found in {fpath}"
