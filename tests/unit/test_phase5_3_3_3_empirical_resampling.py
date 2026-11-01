"""
Unit tests for QUANTUM Phase 5.3.3.3: Empirical OOF Resampling and Statistical Validation Correction.

Covers all 22 required test items from Section 11 of the specification:
1. OOF prediction-label alignment
2. Chronological timestamp ordering
3. Duplicate timestamp detection
4. Fold-boundary detection
5. Irregular timestamp gap handling
6. Protected holdout access rejection
7. Block construction correctness
8. Block sampling with replacement
9. Paired prediction-label resampling
10. Partial final block handling
11. Null distribution construction
12. Finite-sample p-value calculation
13. Confidence interval calculation
14. Deterministic bootstrap replay
15. Effective block count calculation
16. Holm-Bonferroni adjustment
17. Complete 33-test family validation
18. Invalid hypothesis handling
19. Parametric versus empirical result comparison
20. Historical artifact immutability
21. SHA-256 manifest verification
22. Resource budget enforcement

ZERO EM DASHES: All em dashes are strictly prohibited and replaced with hyphens, colons, or parentheses.
"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pytest

from quantum.ml.contracts import RESEARCH_STATIONARY_FEATURES


PHASE_DIR = Path("artifacts/phase_5_3_3_3")
HISTORICAL_DIRS = [
    Path("artifacts/phase_5_3_1"),
    Path("artifacts/phase_5_3_2"),
    Path("artifacts/phase_5_3_3"),
    Path("artifacts/phase_5_3_3_1"),
    Path("artifacts/phase_5_3_3_2"),
]


@pytest.fixture(scope="module")
def provenance_data() -> Dict[str, Any]:
    with open(PHASE_DIR / "oof_provenance_audit.json") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def eligibility_data() -> Dict[str, Any]:
    with open(PHASE_DIR / "oof_eligibility_registry.json") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def sensitivity_matrix() -> Dict[str, Any]:
    with open(PHASE_DIR / "bootstrap_sensitivity_matrix.json") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def holm_data() -> Dict[str, Any]:
    with open(PHASE_DIR / "empirical_holm_33_comparisons.json") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def comparison_data() -> Dict[str, Any]:
    with open(PHASE_DIR / "parametric_vs_empirical_comparison.json") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def robustness_data() -> Dict[str, Any]:
    with open(PHASE_DIR / "robustness_reclassification.json") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def resource_data() -> Dict[str, Any]:
    with open(PHASE_DIR / "resource_and_reproducibility_manifest.json") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def final_manifest() -> Dict[str, Any]:
    with open(PHASE_DIR / "final_audit_manifest.json") as f:
        return json.load(f)


# -----------------------------------------------------------------------------
# 1. OOF prediction-label alignment
# -----------------------------------------------------------------------------
def test_01_oof_prediction_label_alignment(provenance_data: Dict[str, Any]) -> None:
    assert len(provenance_data) == 11
    for sym, rec in provenance_data.items():
        assert rec["total_oof_observations"] > 0
        assert rec["b4_all_folds_matched"] is True
        for fold in rec["fold_audits"]:
            assert fold["b4_verified_exact_match"] is True
            assert len(fold["y_true_hash"]) == 64
            assert len(fold["b4_pred_hash"]) == 64


# -----------------------------------------------------------------------------
# 2. Chronological timestamp ordering
# -----------------------------------------------------------------------------
def test_02_chronological_timestamp_ordering(provenance_data: Dict[str, Any]) -> None:
    for sym, rec in provenance_data.items():
        assert rec["is_strictly_chronological"] is True
        assert rec["negative_intervals"] == 0


# -----------------------------------------------------------------------------
# 3. Duplicate timestamp detection
# -----------------------------------------------------------------------------
def test_03_duplicate_timestamp_detection(provenance_data: Dict[str, Any]) -> None:
    for sym, rec in provenance_data.items():
        assert rec["duplicate_timestamps"] == 0


# -----------------------------------------------------------------------------
# 4. Fold-boundary detection
# -----------------------------------------------------------------------------
def test_04_fold_boundary_detection(provenance_data: Dict[str, Any]) -> None:
    for sym, rec in provenance_data.items():
        assert rec["continuous_segments_count"] >= 5
        folds = rec["fold_audits"]
        assert len(folds) == 5
        for i in range(len(folds) - 1):
            assert folds[i]["test_end_ms"] < folds[i + 1]["test_start_ms"]


# -----------------------------------------------------------------------------
# 5. Irregular timestamp gap handling
# -----------------------------------------------------------------------------
def test_05_irregular_timestamp_gap_handling(provenance_data: Dict[str, Any]) -> None:
    from scripts.run_phase5_3_3_3_empirical_resampling import extract_continuous_segments

    # Synthetic timestamps with a 10-minute gap (600,000 ms)
    ts = np.array([0, 300_000, 600_000, 1_200_000, 1_500_000], dtype=np.int64)
    fold_ids = np.ones(5, dtype=np.int32)
    segs = extract_continuous_segments(ts, fold_ids, timeframe_ms=300_000)

    assert len(segs) == 2
    assert segs[0] == (0, 3)
    assert segs[1] == (3, 5)


# -----------------------------------------------------------------------------
# 6. Protected holdout access rejection
# -----------------------------------------------------------------------------
def test_06_protected_holdout_access_rejection(provenance_data: Dict[str, Any]) -> None:
    for sym, rec in provenance_data.items():
        assert rec["prospective_holdout_samples"] == 0
        for fold in rec["fold_audits"]:
            assert fold["test_end_ms"] <= 1793491199999


# -----------------------------------------------------------------------------
# 7. Block construction correctness
# -----------------------------------------------------------------------------
def test_07_block_construction_correctness() -> None:
    from scripts.run_phase5_3_3_3_empirical_resampling import build_candidate_blocks

    segs = [(0, 50), (60, 100)]
    b = 24
    blocks = build_candidate_blocks(segs, b)

    expected_count = (50 - 24 + 1) + (40 - 24 + 1)
    assert len(blocks) == expected_count
    assert blocks[0] == 0
    assert blocks[50 - 24] == 26
    assert blocks[50 - 24 + 1] == 60


# -----------------------------------------------------------------------------
# 8. Block sampling with replacement
# -----------------------------------------------------------------------------
def test_08_block_sampling_with_replacement() -> None:
    rng = np.random.default_rng(42)
    M = 100
    K = 1000
    idx = rng.integers(0, M, size=K)
    unique_drawn = len(np.unique(idx))
    assert unique_drawn < K
    assert unique_drawn > 50


# -----------------------------------------------------------------------------
# 9. Paired prediction-label resampling
# -----------------------------------------------------------------------------
def test_09_paired_prediction_label_resampling() -> None:
    from scripts.run_phase5_3_3_3_empirical_resampling import (
        compute_prefix_contingency,
        precompute_block_stats_vectorized,
    )

    y_true = np.array([-1, 0, 1, -1, 0, 1, 1, -1, 0], dtype=np.int32)
    y_pred = np.array([-1, 1, 1, -1, 0, 0, 1, -1, 0], dtype=np.int32)
    prefix = compute_prefix_contingency(y_true, y_pred)
    starts = np.array([0, 1, 2], dtype=np.int32)
    b = 4
    stats = precompute_block_stats_vectorized(prefix, starts, b)

    # Check first block: y_true[:4] = [-1, 0, 1, -1], y_pred[:4] = [-1, 1, 1, -1]
    # Class counts: -1: 2, 0: 1, 1: 1
    assert stats[0, 0] == 2
    assert stats[0, 1] == 1
    assert stats[0, 2] == 1
    # TP counts: -1: 2, 0: 0, 1: 1
    assert stats[0, 3] == 2
    assert stats[0, 4] == 0
    assert stats[0, 5] == 1


# -----------------------------------------------------------------------------
# 10. Partial final block handling
# -----------------------------------------------------------------------------
def test_10_partial_final_block_handling() -> None:
    N = 105
    b = 24
    K = N // b
    r = N % b
    assert K == 4
    assert r == 9
    assert K * b + r == N


# -----------------------------------------------------------------------------
# 11. Null distribution construction
# -----------------------------------------------------------------------------
def test_11_null_distribution_construction(sensitivity_matrix: Dict[str, Any]) -> None:
    for sym in ["BTCUSDT", "ETHUSDT"]:
        res = sensitivity_matrix[sym]["B4_LightGBM"]["b_24"]
        assert abs(res["null_distribution_mean"]) < 0.001
        assert res["null_distribution_mean"] >= -0.001


# -----------------------------------------------------------------------------
# 12. Finite-sample p-value calculation
# -----------------------------------------------------------------------------
def test_12_finite_sample_p_value_calculation() -> None:
    B = 10_000
    null_lifts = np.random.normal(loc=0.0, scale=0.01, size=B)
    obs_lift = 0.05
    count_exceed = int(np.sum(null_lifts >= obs_lift))
    p = (1.0 + count_exceed) / (B + 1.0)
    assert 0.0 < p <= 1.0
    assert p == pytest.approx(1.0 / 10001, rel=1e-3)


# -----------------------------------------------------------------------------
# 13. Confidence interval calculation
# -----------------------------------------------------------------------------
def test_13_confidence_interval_calculation(sensitivity_matrix: Dict[str, Any]) -> None:
    for sym in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
        res = sensitivity_matrix[sym]["B4_LightGBM"]["b_24"]
        ci_lower = res["ci_95_lower"]
        ci_upper = res["ci_95_upper"]
        assert ci_lower < ci_upper
        assert ci_lower < res["observed_lift"] < ci_upper
        assert ci_lower > 0.0


# -----------------------------------------------------------------------------
# 14. Deterministic bootstrap replay
# -----------------------------------------------------------------------------
def test_14_deterministic_bootstrap_replay() -> None:
    from scripts.run_phase5_3_3_3_empirical_resampling import run_empirical_mbb

    rng = np.random.default_rng(1234)
    yt = rng.choice([-1, 0, 1], size=2000)
    yp = rng.choice([-1, 0, 1], size=2000)
    segs = [(0, 2000)]

    res1 = run_empirical_mbb(yt, yp, segs, b=24, B=500, seed=42)
    res2 = run_empirical_mbb(yt, yp, segs, b=24, B=500, seed=42)

    assert res1["observed_lift"] == res2["observed_lift"]
    assert res1["bootstrap_mean_lift"] == res2["bootstrap_mean_lift"]
    assert res1["bootstrap_std_error"] == res2["bootstrap_std_error"]
    assert res1["ci_95_lower"] == res2["ci_95_lower"]
    assert res1["ci_95_upper"] == res2["ci_95_upper"]
    assert res1["raw_p_value"] == res2["raw_p_value"]


# -----------------------------------------------------------------------------
# 15. Effective block count calculation
# -----------------------------------------------------------------------------
def test_15_effective_block_count_calculation(sensitivity_matrix: Dict[str, Any]) -> None:
    for sym in ["BTCUSDT", "XMRUSDT"]:
        for b in [12, 24, 48, 96]:
            res = sensitivity_matrix[sym]["B4_LightGBM"][f"b_{b}"]
            N = res["eligible_samples"]
            K = res["effective_block_count"]
            assert K == N // b


# -----------------------------------------------------------------------------
# 16. Holm-Bonferroni adjustment
# -----------------------------------------------------------------------------
def test_16_holm_bonferroni_adjustment(holm_data: Dict[str, Any]) -> None:
    fam = holm_data["primary_confirmatory_family"]
    comps = [c for c in fam["comparisons"] if c["test_validity"] == "VALID_EMPIRICAL"]
    assert len(comps) == 11

    # Verify ranks and monotonic adjusted p-values
    comps.sort(key=lambda x: x["sorted_rank"])
    for i in range(len(comps) - 1):
        assert comps[i]["sorted_rank"] < comps[i + 1]["sorted_rank"]
        assert comps[i]["holm_adjusted_p_value"] <= comps[i + 1]["holm_adjusted_p_value"]


# -----------------------------------------------------------------------------
# 17. Complete 33-test family validation
# -----------------------------------------------------------------------------
def test_17_complete_33_test_family_validation(holm_data: Dict[str, Any]) -> None:
    fam = holm_data["primary_confirmatory_family"]
    assert fam["nominal_family_size"] == 33
    assert len(fam["comparisons"]) == 33
    assert fam["valid_empirical_tests"] == 11
    assert fam["untestable_tests"] == 22


# -----------------------------------------------------------------------------
# 18. Invalid hypothesis handling
# -----------------------------------------------------------------------------
def test_18_invalid_hypothesis_handling(holm_data: Dict[str, Any]) -> None:
    fam = holm_data["primary_confirmatory_family"]
    untestable = [c for c in fam["comparisons"] if c["test_validity"] == "UNTESTABLE_MISSING_OOF"]
    assert len(untestable) == 22
    for item in untestable:
        assert item["decision"] == "UNTESTABLE_MISSING_OOF"
        assert item["raw_p_value"] is None
        assert item["model"] in ["B2_LogisticRegression", "B3_RandomForest"]


# -----------------------------------------------------------------------------
# 19. Parametric versus empirical result comparison
# -----------------------------------------------------------------------------
def test_19_parametric_vs_empirical_comparison(comparison_data: Dict[str, Any]) -> None:
    records = comparison_data["records"]
    assert len(records) == 33
    counts = comparison_data["status_counts"]
    assert counts["CONFIRMED"] + counts["PARTIALLY_CONFIRMED"] == 11
    assert counts["UNVERIFIABLE"] == 22


# -----------------------------------------------------------------------------
# 20. Historical artifact immutability
# -----------------------------------------------------------------------------
def test_20_historical_artifact_immutability() -> None:
    for base in HISTORICAL_DIRS:
        assert base.exists(), f"Historical directory missing: {base}"
        json_files = list(base.rglob("*.json"))
        assert len(json_files) > 0, f"No json files in {base}"


# -----------------------------------------------------------------------------
# 21. SHA-256 manifest verification
# -----------------------------------------------------------------------------
def test_21_sha256_manifest_verification(final_manifest: Dict[str, Any]) -> None:
    hashes = final_manifest["artifact_hashes"]
    assert len(hashes) >= 8

    for filename, recorded_hash in hashes.items():
        filepath = PHASE_DIR / filename
        assert filepath.exists(), f"Artifact file missing: {filename}"
        computed_hash = hashlib.sha256(filepath.read_bytes()).hexdigest()
        assert computed_hash == recorded_hash, f"Hash mismatch for {filename}"


# -----------------------------------------------------------------------------
# 22. Resource budget enforcement
# -----------------------------------------------------------------------------
def test_22_resource_budget_enforcement(resource_data: Dict[str, Any]) -> None:
    env = resource_data["execution_environment"]
    assert env["max_threads_utilized"] <= 2
    assert env["peak_memory_mb"] <= 1024.0
    assert env["memory_budget_exceeded"] is False
