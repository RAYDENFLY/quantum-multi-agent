"""
Unit tests for Phase 5.3.3.5: Pooled OOF Aggregation and Paired B4-vs-B0 Statistical Audit.
Verifies fold confusion matrix integrity, mathematical support-weighted reconciliation,
paired B4 vs B0 delta metrics, Moving Block Bootstrap results, Holm-Bonferroni corrections,
and zero em-dash compliance.
"""

import json
from pathlib import Path
import pytest

ARTIFACTS_DIR = Path("artifacts/phase_5_3_3_5")
DOCS_DIR = Path("docs")
SCRIPTS_DIR = Path("scripts")
TESTS_DIR = Path("tests/unit")

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"
]

HISTORICAL_B4_BENCHMARKS = {
    "BTCUSDT": 0.4099,
    "ETHUSDT": 0.4177,
    "BNBUSDT": 0.3699,
    "XRPUSDT": 0.3747,
    "ADAUSDT": 0.4490,
    "SOLUSDT": 0.3878,
    "AVAXUSDT": 0.4145,
    "LINKUSDT": 0.4067,
    "DOGEUSDT": 0.3960,
    "LTCUSDT": 0.4355,
    "XMRUSDT": 0.3816,
}


def test_01_all_artifacts_exist():
    expected_files = [
        "fold_aggregation_audit.json",
        "paired_b4_b0_results.json",
        "final_audit_manifest.json",
    ]
    for fname in expected_files:
        p = ARTIFACTS_DIR / fname
        assert p.exists(), f"Missing artifact: {fname}"
        assert p.stat().st_size > 0, f"Empty artifact: {fname}"


def test_02_per_fold_confusion_matrix_sums():
    with open(ARTIFACTS_DIR / "fold_aggregation_audit.json") as f:
        data = json.load(f)
    for sym in SYMBOLS:
        inst = data["instruments"][sym]
        for fold_info in inst["folds"]:
            fold_idx = fold_info["fold"]
            test_samples = fold_info["test_samples"]
            b4_cm = fold_info["b4_confusion_matrix"]
            b0_cm = fold_info["b0_confusion_matrix"]
            b4_sum = sum(sum(row) for row in b4_cm)
            b0_sum = sum(sum(row) for row in b0_cm)
            assert b4_sum == test_samples, (
                f"{sym} fold {fold_idx}: B4 CM sum {b4_sum} != test_samples {test_samples}"
            )
            assert b0_sum == test_samples, (
                f"{sym} fold {fold_idx}: B0 CM sum {b0_sum} != test_samples {test_samples}"
            )
            # Support per class must sum to test_samples
            supp = fold_info["class_support"]
            supp_sum = supp["SL"] + supp["EXP"] + supp["TP"]
            assert supp_sum == test_samples, (
                f"{sym} fold {fold_idx}: support sum {supp_sum} != test_samples {test_samples}"
            )


def test_03_pooled_confusion_matrix_sums_to_total_oof():
    with open(ARTIFACTS_DIR / "fold_aggregation_audit.json") as f:
        data = json.load(f)
    fleet_total = 0
    for sym in SYMBOLS:
        inst = data["instruments"][sym]
        tot_samples = inst["total_oof_samples"]
        b4_pooled_cm = inst["pooled_b4_confusion_matrix"]
        b0_pooled_cm = inst["pooled_b0_confusion_matrix"]
        b4_cm_sum = sum(sum(row) for row in b4_pooled_cm)
        b0_cm_sum = sum(sum(row) for row in b0_pooled_cm)
        assert b4_cm_sum == tot_samples, (
            f"{sym}: B4 pooled CM sum {b4_cm_sum} != total {tot_samples}"
        )
        assert b0_cm_sum == tot_samples, (
            f"{sym}: B0 pooled CM sum {b0_cm_sum} != total {tot_samples}"
        )
        fleet_total += tot_samples
    assert fleet_total == 1_322_108, f"Fleet total OOF {fleet_total} != 1,322,108"


def test_04_b4_fold_ba_matches_historical_benchmark():
    with open(ARTIFACTS_DIR / "fold_aggregation_audit.json") as f:
        data = json.load(f)
    for sym in SYMBOLS:
        inst = data["instruments"][sym]
        fold_mean_ba = inst["unweighted_fold_mean_b4_ba"]
        hist_ba = HISTORICAL_B4_BENCHMARKS[sym]
        assert fold_mean_ba == pytest.approx(hist_ba, abs=1e-4), (
            f"{sym}: unweighted fold mean BA {fold_mean_ba} != historical {hist_ba}"
        )


def test_05_mathematical_support_weighted_reconciliation():
    with open(ARTIFACTS_DIR / "fold_aggregation_audit.json") as f:
        data = json.load(f)
    for sym in SYMBOLS:
        inst = data["instruments"][sym]
        pooled_ba = inst["pooled_b4_balanced_accuracy"]
        tot_supp = inst["pooled_class_support"]
        
        # Calculate support-weighted recall per class
        class_keys = ["SL", "EXP", "TP"]
        reconstructed_class_recalls = {c: 0.0 for c in class_keys}
        for fold_info in inst["folds"]:
            fold_supp = fold_info["class_support"]
            fold_rec = fold_info["b4_per_class_recall"]
            for c in class_keys:
                weight = fold_supp[c] / tot_supp[c]
                reconstructed_class_recalls[c] += weight * fold_rec[c]
                
        reconstructed_pooled_ba = sum(reconstructed_class_recalls.values()) / 3.0
        assert reconstructed_pooled_ba == pytest.approx(pooled_ba, abs=1e-5), (
            f"{sym}: reconstructed pooled BA {reconstructed_pooled_ba} != actual {pooled_ba}"
        )


def test_06_paired_b4_b0_delta_calculation():
    with open(ARTIFACTS_DIR / "paired_b4_b0_results.json") as f:
        data = json.load(f)
    for sym in SYMBOLS:
        inst = data["instruments"][sym]
        b4_ba = inst["b4_pooled_ba"]
        b0_ba = inst["b0_pooled_ba"]
        reported_delta = inst["absolute_paired_improvement"]
        expected_delta = b4_ba - b0_ba
        assert reported_delta == pytest.approx(expected_delta, abs=1e-5), (
            f"{sym}: reported delta {reported_delta} != {expected_delta}"
        )
        # B4 must strictly beat B0 for every instrument
        assert reported_delta > 0.05, f"{sym}: paired delta {reported_delta} is not > 0.05"


def test_07_paired_b0_pooled_ba_values():
    with open(ARTIFACTS_DIR / "paired_b4_b0_results.json") as f:
        data = json.load(f)
    stationary_majority_syms = ["BNBUSDT", "ADAUSDT", "SOLUSDT", "AVAXUSDT", "LINKUSDT", "LTCUSDT", "XMRUSDT"]
    shifting_majority_syms = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "DOGEUSDT"]

    for sym in stationary_majority_syms:
        inst = data["instruments"][sym]
        assert inst["b0_pooled_ba"] == pytest.approx(1.0 / 3.0, abs=1e-5), (
            f"{sym}: B0 pooled BA {inst['b0_pooled_ba']} != 1/3"
        )

    for sym in shifting_majority_syms:
        inst = data["instruments"][sym]
        assert 0.3300 <= inst["b0_pooled_ba"] <= 0.3360, (
            f"{sym}: B0 pooled BA {inst['b0_pooled_ba']} outside expected range [0.3300, 0.3360]"
        )
        assert abs(inst["b0_pooled_ba"] - 0.5000) > 0.10, (
            f"{sym}: B0 pooled BA {inst['b0_pooled_ba']} unexpectedly near 0.5000"
        )


def test_08_paired_mbb_p_value_finite_sample_bound():
    with open(ARTIFACTS_DIR / "paired_b4_b0_results.json") as f:
        data = json.load(f)
    block_lengths = [12, 24, 48, 96]
    for sym in SYMBOLS:
        inst = data["instruments"][sym]
        for b in block_lengths:
            b_key = f"b_{b}"
            res = inst["bootstrap_results_by_block_length"][b_key]
            assert res["null_exceed_count"] == 0, (
                f"{sym} b={b}: null exceed count {res['null_exceed_count']} != 0"
            )
            assert res["is_upper_bound_reporting"] is True
            assert "p < 1/10001" in res["p_value_display"]
            assert res["is_statistically_significant_05"] is True


def test_09_holm_bonferroni_all_rejected():
    with open(ARTIFACTS_DIR / "paired_b4_b0_results.json") as f:
        data = json.load(f)
    hb_info = data["holm_bonferroni_family_b24"]
    assert hb_info["all_rejected"] is True
    assert hb_info["family_size"] == 11
    hb_table = hb_info["evaluations"]
    assert len(hb_table) == 11
    for row in hb_table:
        assert row["h0_rejected_significant"] is True
        assert row["holm_adjusted_p_value"] <= 0.05
        assert row["observed_paired_delta"] > 0.05


def test_10_bootstrap_95ci_strictly_positive():
    with open(ARTIFACTS_DIR / "paired_b4_b0_results.json") as f:
        data = json.load(f)
    for sym in SYMBOLS:
        inst = data["instruments"][sym]
        for b in [12, 24, 48, 96]:
            res = inst["bootstrap_results_by_block_length"][f"b_{b}"]
            ci_low, ci_high = res["ci_95_percentile"]
            assert ci_low > 0.03, f"{sym} b={b}: CI lower bound {ci_low} is not > 0.03"
            assert ci_high > ci_low, f"{sym} b={b}: invalid CI [{ci_low}, {ci_high}]"


def test_11_documentation_deliverables_exist():
    expected_docs = [
        "PHASE_5_3_3_5_FOLD_AGGREGATION_AUDIT.md",
        "PHASE_5_3_3_5_PAIRED_BOOTSTRAP_AUDIT.md",
        "PHASE_5_3_3_5_FINAL_REPORT.md",
    ]
    for doc in expected_docs:
        p = DOCS_DIR / doc
        assert p.exists(), f"Missing doc: {doc}"
        assert p.stat().st_size > 500, f"Doc {doc} is too short or empty"


def test_12_no_em_dashes_in_phase5_3_3_5_files():
    files_to_check = [
        ARTIFACTS_DIR / "fold_aggregation_audit.json",
        ARTIFACTS_DIR / "paired_b4_b0_results.json",
        ARTIFACTS_DIR / "final_audit_manifest.json",
        DOCS_DIR / "PHASE_5_3_3_5_FOLD_AGGREGATION_AUDIT.md",
        DOCS_DIR / "PHASE_5_3_3_5_PAIRED_BOOTSTRAP_AUDIT.md",
        DOCS_DIR / "PHASE_5_3_3_5_FINAL_REPORT.md",
        SCRIPTS_DIR / "run_phase5_3_3_5_paired_audit.py",
        TESTS_DIR / "test_phase5_3_3_5_paired_audit.py",
    ]
    em_dash = "\u2014"
    for fpath in files_to_check:
        if not fpath.exists():
            continue
        text = fpath.read_text(encoding="utf-8")
        assert em_dash not in text, f"Forbidden em-dash found in {fpath}"


def test_13_block_boundary_protection_and_segment_extraction():
    import numpy as np
    import sys
    sys.path.insert(0, str(SCRIPTS_DIR))
    from run_phase5_3_3_5_paired_audit import (
        extract_continuous_segments,
        build_candidate_blocks,
        compute_prefix_contingency_paired,
    )

    # Create synthetic timestamps with a fold boundary and a timestamp gap
    # Segment 1: fold 1, indices 0..14 (15 bars, contiguous 300_000 ms)
    ts1 = np.arange(0, 15 * 300_000, 300_000, dtype=np.int64)
    f1 = np.ones(15, dtype=np.int32)

    # Segment 2: fold 1, but after a 600_000 ms gap, indices 15..24 (10 bars < block_length 12)
    ts2 = np.arange(15 * 300_000 + 300_000, 25 * 300_000 + 300_000, 300_000, dtype=np.int64)
    f2 = np.ones(10, dtype=np.int32)

    # Segment 3: fold 2, contiguous timestamp with end of ts2, indices 25..40 (16 bars)
    ts3 = np.arange(ts2[-1] + 300_000, ts2[-1] + 17 * 300_000, 300_000, dtype=np.int64)
    f3 = np.full(16, 2, dtype=np.int32)

    timestamps = np.concatenate([ts1, ts2, ts3])
    fold_ids = np.concatenate([f1, f2, f3])

    segments = extract_continuous_segments(timestamps, fold_ids, timeframe_ms=300_000)
    assert segments == [(0, 15), (15, 25), (25, 41)]

    # For block_length = 12:
    # Segment (0, 15) has length 15 -> valid starts 0, 1, 2, 3 (4 blocks)
    # Segment (15, 25) has length 10 < 12 -> 0 blocks
    # Segment (25, 41) has length 16 -> valid starts 25, 26, 27, 28, 29 (5 blocks)
    cands = build_candidate_blocks(segments, block_length=12)
    expected_starts = [0, 1, 2, 3, 25, 26, 27, 28, 29]
    assert list(cands) == expected_starts

    # Verify that no candidate block crosses a fold boundary or timestamp gap
    for st in cands:
        block_ts = timestamps[st : st + 12]
        block_folds = fold_ids[st : st + 12]
        assert np.all(np.diff(block_ts) == 300_000), f"Block at {st} crossed timestamp gap!"
        assert len(np.unique(block_folds)) == 1, f"Block at {st} crossed fold boundary!"

    # Verify prefix table exactness
    y_true = np.array([-1, 0, 1] * 13 + [-1, 0], dtype=np.int32)
    y_b4 = np.array([-1, 0, 1] * 10 + [1, 1, 1] * 3 + [-1, 0], dtype=np.int32)
    y_b0 = np.full(41, 1, dtype=np.int32)
    cs = compute_prefix_contingency_paired(y_true, y_b4, y_b0)
    totals = cs[41] - cs[0]
    assert totals[0] == np.sum(y_true == -1)
    assert totals[1] == np.sum(y_true == 0)
    assert totals[2] == np.sum(y_true == 1)
    assert totals[3] == np.sum((y_true == -1) & (y_b4 == -1))
    assert totals[4] == np.sum((y_true == 0) & (y_b4 == 0))
    assert totals[5] == np.sum((y_true == 1) & (y_b4 == 1))


def test_14_no_unverified_paradox_terminology():
    files_to_check = [
        ARTIFACTS_DIR / "fold_aggregation_audit.json",
        ARTIFACTS_DIR / "paired_b4_b0_results.json",
        ARTIFACTS_DIR / "final_audit_manifest.json",
        DOCS_DIR / "PHASE_5_3_3_5_FOLD_AGGREGATION_AUDIT.md",
        DOCS_DIR / "PHASE_5_3_3_5_PAIRED_BOOTSTRAP_AUDIT.md",
        DOCS_DIR / "PHASE_5_3_3_5_FINAL_REPORT.md",
        SCRIPTS_DIR / "run_phase5_3_3_5_paired_audit.py",
    ]
    forbidden_term = "simp" + "son"
    for fpath in files_to_check:
        text = fpath.read_text(encoding="utf-8").lower()
        assert forbidden_term not in text, f"Prohibited unverified term found in {fpath}"


def test_15_manifest_sha256_integrity():
    import hashlib
    with open(ARTIFACTS_DIR / "final_audit_manifest.json") as f:
        manifest = json.load(f)
    assert manifest["phase"] == "5.3.3.5"
    assert manifest["verdict"] == "PHASE_5_3_3_5_PASS"
    assert manifest["phase_5_4_gate_status"] == "HOLD"
    assert manifest["fleet_total_oof_observations"] == 1_322_108
    for fname, meta in manifest["files"].items():
        p = Path(meta["path"])
        assert p.exists(), f"Manifest file missing: {p}"
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        assert h == meta["sha256"], f"SHA-256 mismatch for {p}: {h} != {meta['sha256']}"
        assert p.stat().st_size == meta["bytes"], f"Byte size mismatch for {p}"


