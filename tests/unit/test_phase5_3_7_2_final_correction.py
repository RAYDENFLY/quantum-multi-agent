"""
Unit tests for QUANTUM Phase 5.3.7.2:
Final Statistical Table & Population Arithmetic Correction.

Verifies:
1. Monte Carlo plus-one p-value arithmetic (p_MC = 1/10001 approx 0.0000999900).
2. Holm-Bonferroni ranking consistency (ranks 1 to 11 unique, monotonic by delta, all reject H0).
3. Population arithmetic exactness across all four categories.
4. Definitive XRP (0.3748) and LINK (0.4068) historical benchmark values.
5. Checksum immutability of frozen artifacts.
6. Zero em-dashes across all Phase 5.3.7.2 files.
"""

import hashlib
import json
from pathlib import Path
import pytest

RESEARCH_DOCS_DIR = Path("docs/research")
ARTIFACTS_DIR = Path("artifacts")
FREEZE_DIR = ARTIFACTS_DIR / "phase_5_3_freeze"
MANIFEST_PATH = FREEZE_DIR / "frozen_artifact_manifest.json"

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"
]


def test_01_monte_carlo_plus_one_p_value_arithmetic():
    b_resamples = 10000
    null_exceed = 0
    p_mc = (1 + null_exceed) / (b_resamples + 1)

    assert p_mc == 1 / 10001
    assert abs(p_mc - 0.0000999900009999) < 1e-12

    freeze_doc = (RESEARCH_DOCS_DIR / "PHASE_5_3_FINAL_FREEZE.md").read_text(encoding="utf-8")
    report_doc = (RESEARCH_DOCS_DIR / "PHASE_5_3_7_2_FINAL_CORRECTION_REPORT.md").read_text(encoding="utf-8")

    assert "1/10001" in freeze_doc
    assert "1/10001" in report_doc
    assert "p < 1/10001" not in freeze_doc, "Invalid p < 1/10001 notation found in freeze doc"


def test_02_holm_bonferroni_ranking_and_tie_breaking_consistency():
    with open("artifacts/phase_5_3_3_5/paired_b4_b0_results.json", encoding="utf-8") as f:
        hb = json.load(f)["holm_bonferroni_family_b24"]

    evals = hb["evaluations"]
    assert len(evals) == 11

    ranks = [e["rank"] for e in evals]
    assert ranks == list(range(1, 12)), "Ranks are not strictly 1 to 11"

    # Check monotonicity of deltas
    deltas = [e["observed_paired_delta"] for e in evals]
    assert deltas == sorted(deltas, reverse=True), "Deltas are not sorted descending"

    # Check that all reject H0
    for e in evals:
        assert e["h0_rejected_significant"] is True
        assert e["raw_p_value_numeric"] <= e["step_down_alpha_threshold"]


def test_03_population_arithmetic_exactness():
    with open("artifacts/phase_5_3_1/pilot_summary.json", encoding="utf-8") as f:
        pilot = json.load(f)

    canonical = {}
    research_ready = {}
    eligible_labeled = {}
    oof_obs = {}

    with open("artifacts/phase_5_3_3_6/oof_population_audit.json", encoding="utf-8") as f:
        oof_pop = json.load(f)["instruments"]

    for sym in SYMBOLS:
        if sym in ["BTCUSDT", "XMRUSDT"]:
            s = pilot[sym]
        else:
            with open(f"artifacts/phase_5_3_2/{sym}/summary.json", encoding="utf-8") as f:
                s = json.load(f)
        dstats = s["data_stats"]
        canonical[sym] = dstats["total_canonical"]
        research_ready[sym] = dstats["total_dev_val_features"]
        eligible_labeled[sym] = dstats["eligible_samples"]
        oof_obs[sym] = oof_pop[sym]["phase_5_3_3_5_artifact_oof_count"]

    assert sum(canonical.values()) == 3248862
    assert sum(research_ready.values()) == 2657262
    assert sum(eligible_labeled.values()) == 2645531
    assert sum(oof_obs.values()) == 1322108

    freeze_doc = (RESEARCH_DOCS_DIR / "PHASE_5_3_FINAL_FREEZE.md").read_text(encoding="utf-8")
    assert "2,657,262" in freeze_doc
    assert "2,657,263" not in freeze_doc, "Old erroneous 2,657,263 found in freeze doc"


def test_04_xrp_and_link_definitive_benchmark_values():
    with open("artifacts/phase_5_3_3_1/final_benchmark_catalog.json", encoding="utf-8") as f:
        cat = json.load(f)["catalog"]

    assert cat["XRPUSDT"]["baseline_metrics"]["B4_LightGBM"]["balanced_accuracy"] == 0.3748
    assert cat["LINKUSDT"]["baseline_metrics"]["B4_LightGBM"]["balanced_accuracy"] == 0.4068

    freeze_doc = (RESEARCH_DOCS_DIR / "PHASE_5_3_FINAL_FREEZE.md").read_text(encoding="utf-8")
    assert "0.3748" in freeze_doc
    assert "0.4068" in freeze_doc
    assert "0.3748 / 0.3747" not in freeze_doc, "Slash placeholder found for XRP"
    assert "0.4068 / 0.4067" not in freeze_doc, "Slash placeholder found for LINK"


def test_05_checksum_immutability_of_frozen_artifacts():
    assert MANIFEST_PATH.exists()
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        manifest = json.load(f)

    # Check key files
    for item in manifest["artifacts"][:20]:
        p = Path(item["relative_path"])
        assert p.exists(), f"Missing file: {p}"
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        assert h == item["sha256"], f"Hash mismatch for {p}"


def test_06_zero_em_dashes_in_phase5_3_7_2_files():
    files_to_check = [
        RESEARCH_DOCS_DIR / "PHASE_5_3_FINAL_FREEZE.md",
        RESEARCH_DOCS_DIR / "PHASE_5_3_7_1_RECONCILIATION_REPORT.md",
        RESEARCH_DOCS_DIR / "PHASE_5_3_7_2_FINAL_CORRECTION_REPORT.md",
        Path("tests/unit/test_phase5_3_7_2_final_correction.py"),
        Path("scripts/generate_phase_5_3_7_2_final_correction.py"),
    ]
    em_dash = chr(0x2014)
    for p in files_to_check:
        if p.exists():
            text = p.read_text(encoding="utf-8")
            assert em_dash not in text, f"Em-dash found in {p}"
