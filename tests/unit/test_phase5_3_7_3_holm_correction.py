"""
Unit tests for QUANTUM Phase 5.3.7.3:
Holm-Bonferroni Adjusted P-Value Correction.

Verifies:
1. 11 identical raw p-values evaluate to uniform adjusted p-value 11/10001.
2. Distinct raw p-values calculate correct Holm step-down and enforce monotonicity.
3. Partial ties handle cumulative maximum correctly and preserve monotonicity.
4. Monotonicity holds across arbitrary permutations.
5. Reconciled tables in documentation match exact formula and nomenclature.
6. Claimed vs displayed SHA-256 artifact count consistency.
7. Zero em-dashes across all Phase 5.3.7.3 files.
"""

import hashlib
import json
from pathlib import Path
import pytest

RESEARCH_DOCS_DIR = Path("docs/research")
ARTIFACTS_DIR = Path("artifacts")
FREEZE_DIR = ARTIFACTS_DIR / "phase_5_3_freeze"
MANIFEST_PATH = FREEZE_DIR / "frozen_artifact_manifest.json"


def compute_holm_adjusted_pvalues(p_values: list[float]) -> list[float]:
    """
    Computes Holm-Bonferroni adjusted p-values according to Holm (1979):
    p_adj(i) = min(1, max_{j <= i} ((m - j + 1) * p_(j)))
    """
    m = len(p_values)
    # Sort ascending
    sorted_indices = sorted(range(m), key=lambda i: p_values[i])
    sorted_p = [p_values[i] for i in sorted_indices]

    adjusted_sorted = [0.0] * m
    cum_max = 0.0
    for j in range(m):
        multiplier = m - j
        val = multiplier * sorted_p[j]
        if val > cum_max:
            cum_max = val
        adjusted_sorted[j] = min(1.0, cum_max)

    # Restore original order
    adjusted_original = [0.0] * m
    for orig_idx, adj_val in zip(sorted_indices, adjusted_sorted):
        adjusted_original[orig_idx] = adj_val

    return adjusted_original


def test_01_all_11_identical_raw_pvalues_evaluate_to_eleven_over_10001():
    m = 11
    raw_p = 1 / 10001
    p_values = [raw_p] * m

    adj_p = compute_holm_adjusted_pvalues(p_values)

    expected = 11 / 10001
    assert len(adj_p) == 11
    for val in adj_p:
        assert abs(val - expected) < 1e-15
        assert abs(val - 0.0010998900109989) < 1e-12

    # Verify that all reject H0 at alpha = 0.05
    alpha = 0.05
    for val in adj_p:
        assert val <= alpha, f"Adjusted p-value {val} exceeds alpha {alpha}"


def test_02_distinct_raw_pvalues_step_down_and_monotonicity():
    # Synthetic distinct raw p-values
    p_values = [0.001, 0.005, 0.015, 0.040]
    m = len(p_values)

    adj_p = compute_holm_adjusted_pvalues(p_values)

    # Step calculations:
    # j=0: 4 * 0.001 = 0.004, cum_max = 0.004
    # j=1: 3 * 0.005 = 0.015, cum_max = 0.015
    # j=2: 2 * 0.015 = 0.030, cum_max = 0.030
    # j=3: 1 * 0.040 = 0.040, cum_max = 0.040
    expected = [0.004, 0.015, 0.030, 0.040]
    for actual, exp in zip(adj_p, expected):
        assert abs(actual - exp) < 1e-9

    # Verify monotonicity
    for i in range(len(adj_p) - 1):
        assert adj_p[i] <= adj_p[i + 1]


def test_03_partial_ties_in_hypotheses():
    # Synthetic vector with partial ties where multiplier would decrease without cum_max
    p_values = [0.002, 0.002, 0.010, 0.030]
    # j=0: 4 * 0.002 = 0.008, cum_max = 0.008
    # j=1: 3 * 0.002 = 0.006, cum_max = max(0.008, 0.006) = 0.008
    # j=2: 2 * 0.010 = 0.020, cum_max = 0.020
    # j=3: 1 * 0.030 = 0.030, cum_max = 0.030
    expected = [0.008, 0.008, 0.020, 0.030]

    adj_p = compute_holm_adjusted_pvalues(p_values)
    for actual, exp in zip(adj_p, expected):
        assert abs(actual - exp) < 1e-9

    # Both tied hypotheses receive identical adjusted p-values
    assert adj_p[0] == adj_p[1]


def test_04_monotonicity_across_arbitrary_permutations():
    import random
    rng = random.Random(42)

    for _ in range(50):
        length = rng.randint(2, 20)
        p_vals = [rng.uniform(0.00001, 0.2) for _ in range(length)]
        adj = compute_holm_adjusted_pvalues(p_vals)

        # Sort both by raw p-value to check monotonicity
        sorted_pairs = sorted(zip(p_vals, adj), key=lambda x: x[0])
        sorted_adj = [p[1] for p in sorted_pairs]

        for i in range(len(sorted_adj) - 1):
            assert sorted_adj[i] <= sorted_adj[i + 1] + 1e-12, (
                f"Monotonicity violation: {sorted_adj[i]} > {sorted_adj[i+1]}"
            )


def test_05_reconciled_tables_in_documentation():
    freeze_doc = (RESEARCH_DOCS_DIR / "PHASE_5_3_FINAL_FREEZE.md").read_text(encoding="utf-8")
    report_doc = (RESEARCH_DOCS_DIR / "PHASE_5_3_7_3_HOLM_CORRECTION_REPORT.md").read_text(encoding="utf-8")

    # Both documents must have 11/10001 and 0.00109989
    assert "11/10001" in freeze_doc
    assert "0.00109989" in freeze_doc
    assert "11/10001" in report_doc
    assert "0.00109989" in report_doc

    # Both documents must use 'Effect Size Rank' nomenclature
    assert "Effect Size Rank" in freeze_doc
    assert "Effect Size Rank" in report_doc

    # Obsolete multiplier sequences (0.0001, 0.0002... 0.0011) should not be reported as adjusted p-values in Section 3.2
    # Verify exact phrase
    assert "11/10001 (0.00109989)" in freeze_doc
    assert "11/10001 (0.00109989)" in report_doc


def test_06_claimed_vs_displayed_sha256_count_consistency():
    freeze_doc = (RESEARCH_DOCS_DIR / "PHASE_5_3_FINAL_FREEZE.md").read_text(encoding="utf-8")
    report_doc = (RESEARCH_DOCS_DIR / "PHASE_5_3_7_3_HOLM_CORRECTION_REPORT.md").read_text(encoding="utf-8")

    # In freeze doc, Section 5 claims 19 key files and displays exactly 19 rows
    sec5_start = freeze_doc.find("## 5. Complete Frozen Artifact Inventory")
    sec5_end = freeze_doc.find("## 6. Systemic Known Limitations")
    sec5_text = freeze_doc[sec5_start:sec5_end]
    rows = [line for line in sec5_text.splitlines() if line.strip().startswith("| **")]
    assert len(rows) == 19, f"Expected 19 rows in freeze doc, got {len(rows)}"
    assert "19 key governance files" in sec5_text

    # In 5.3.7.3 report, Section 4 claims 19 key files and displays exactly 19 rows
    sec4_start = report_doc.find("### 4.2 Exact Count Verification")
    sec4_end = report_doc.find("## 5. Task 4: Unit Test Suite")
    sec4_text = report_doc[sec4_start:sec4_end]
    report_rows = [line for line in sec4_text.splitlines() if line.strip().startswith("| **")]
    assert len(report_rows) == 19, f"Expected 19 rows in report doc, got {len(report_rows)}"
    assert "19" in sec4_text and "displayed" in sec4_text


def test_07_zero_em_dashes_in_all_phase_5_3_7_3_files():
    files_to_check = [
        RESEARCH_DOCS_DIR / "PHASE_5_3_FINAL_FREEZE.md",
        RESEARCH_DOCS_DIR / "PHASE_5_3_7_2_FINAL_CORRECTION_REPORT.md",
        RESEARCH_DOCS_DIR / "PHASE_5_3_7_3_HOLM_CORRECTION_REPORT.md",
        Path("tests/unit/test_phase5_3_7_3_holm_correction.py"),
        Path("scripts/generate_phase_5_3_7_3_holm_correction.py"),
    ]
    em_dash = chr(0x2014)
    for p in files_to_check:
        if p.exists():
            text = p.read_text(encoding="utf-8")
            assert em_dash not in text, f"Em-dash found in {p}"
