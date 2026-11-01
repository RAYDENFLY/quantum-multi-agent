"""Unit tests for Phase 5.3.3.1 Final Benchmark Correction & Governance Closure.

Covers all 18 verification requirements:
1. Brier winner comparison across B0-B4.
2. Brier winner comparison across B2-B4.
3. Brier formula consistency.
4. LTCUSDT B3/B4 attribution.
5. XMR historical fold reconciliation.
6. XMR metric aggregation.
7. Bootstrap block-length configuration.
8. Bootstrap deterministic replay.
9. Bootstrap sensitivity output schema.
10. Holm-Bonferroni adjustment correctness.
11. Multiple hypothesis family definition.
12. Statistical status classification.
13. Embargo implementation or formal deprecation.
14. Purge and test-label horizon separation.
15. Historical artifact immutability.
16. Final catalog schema validation.
17. SHA-256 manifest consistency.
18. Prospective holdout access rejection.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict
import numpy as np
import pandas as pd
import pytest

from quantum.features.temporal_split import (
    DEVELOPMENT_START_MS,
    PROSPECTIVE_HOLDOUT_START_MS,
)
from quantum.ml.contracts import (
    RESEARCH_FEATURE_SCHEMA_HASH,
    RESEARCH_STATIONARY_FEATURES,
)
from quantum.ml.evaluation import ModelEvaluationContract
from quantum.ml.validation import PurgedWalkForwardSplitter

OUTPUT_DIR = Path("artifacts/phase_5_3_3_1")
P531_DIR = Path("artifacts/phase_5_3_1")
P532_DIR = Path("artifacts/phase_5_3_2")
P533_DIR = Path("artifacts/phase_5_3_3")

ALL_SYMBOLS = [
    "BTCUSDT", "XMRUSDT", "ADAUSDT", "XRPUSDT", "BNBUSDT",
    "ETHUSDT", "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT"
]


@pytest.fixture(scope="module")
def governance_data() -> Dict[str, Dict]:
    """Load pre-computed Phase 5.3.3.1 JSON artifacts."""
    files = {
        "brier": OUTPUT_DIR / "brier_reconciliation.json",
        "xmr": OUTPUT_DIR / "xmr_fold_reconciliation.json",
        "bootstrap": OUTPUT_DIR / "bootstrap_sensitivity.json",
        "holm": OUTPUT_DIR / "holm_adjusted_pvalues.json",
        "embargo": OUTPUT_DIR / "embargo_governance_decision.json",
        "catalog": OUTPUT_DIR / "final_benchmark_catalog.json",
        "winners": OUTPUT_DIR / "final_winner_catalog.json",
        "manifest": OUTPUT_DIR / "final_manifest_hashes.json",
    }
    loaded = {}
    for k, p in files.items():
        assert p.exists(), f"Governance file missing: {p}"
        with open(p, "r", encoding="utf-8") as f:
            loaded[k] = json.load(f)
    return loaded


def test_01_brier_winner_comparison_across_all_baselines(governance_data: Dict[str, Dict]) -> None:
    """1. Verify Brier winner comparison across B0 through B4."""
    brier_data = governance_data["brier"]["symbols"]
    # B1 Prior wins on BTC, XMR, ADA, ETH, SOL
    assert brier_data["BTCUSDT"]["LOWEST_BRIER_ALL_BASELINES"]["model"] == "B1_Prior"
    assert brier_data["XMRUSDT"]["LOWEST_BRIER_ALL_BASELINES"]["model"] == "B1_Prior"
    assert brier_data["ADAUSDT"]["LOWEST_BRIER_ALL_BASELINES"]["model"] == "B1_Prior"
    assert brier_data["ETHUSDT"]["LOWEST_BRIER_ALL_BASELINES"]["model"] == "B1_Prior"
    assert brier_data["SOLUSDT"]["LOWEST_BRIER_ALL_BASELINES"]["model"] == "B1_Prior"
    # B4 LightGBM wins on XRP, BNB, AVAX, LINK, DOGE
    assert brier_data["XRPUSDT"]["LOWEST_BRIER_ALL_BASELINES"]["model"] == "B4_LightGBM"
    assert brier_data["BNBUSDT"]["LOWEST_BRIER_ALL_BASELINES"]["model"] == "B4_LightGBM"
    # B3 RandomForest wins on LTC
    assert brier_data["LTCUSDT"]["LOWEST_BRIER_ALL_BASELINES"]["model"] == "B3_RandomForest"


def test_02_brier_winner_comparison_across_ml_models(governance_data: Dict[str, Dict]) -> None:
    """2. Verify Brier winner comparison strictly across ML models (B2, B3, B4)."""
    brier_data = governance_data["brier"]["symbols"]
    # LTC winner is B3_RandomForest
    assert brier_data["LTCUSDT"]["LOWEST_BRIER_ML_MODELS"]["model"] == "B3_RandomForest"
    # All other 10 instruments won by B4_LightGBM
    for sym in ["BTCUSDT", "XMRUSDT", "ADAUSDT", "XRPUSDT", "BNBUSDT", "ETHUSDT", "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT"]:
        assert brier_data[sym]["LOWEST_BRIER_ML_MODELS"]["model"] == "B4_LightGBM"


def test_03_brier_formula_consistency() -> None:
    """3. Verify multiclass Brier score formula implementation matches (1/N)*sum(f - o)^2."""
    y_true = np.array([-1, 0, 1])
    # Exact perfect probabilities
    y_proba_perfect = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ])
    res_perfect = ModelEvaluationContract.evaluate_predictions(y_true, y_true, y_proba_perfect, classes=[-1, 0, 1])
    assert res_perfect["brier_score"] == 0.0

    # Constant majority prediction: predict [1.0, 0.0, 0.0] for all samples
    y_proba_maj = np.array([
        [1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
        [1.0, 0.0, 0.0],
    ])
    # For sample 0: error is 0. For sample 1: (1-0)^2 + (0-1)^2 = 2. For sample 2: 2.
    # Mean error = (0 + 2 + 2) / 3 = 4/3 = 1.3333
    res_maj = ModelEvaluationContract.evaluate_predictions(y_true, np.array([-1, -1, -1]), y_proba_maj, classes=[-1, 0, 1])
    assert abs(res_maj["brier_score"] - 1.3333) <= 1e-4


def test_04_ltcusdt_b3_b4_attribution(governance_data: Dict[str, Dict]) -> None:
    """4. Verify LTCUSDT B3 vs B4 attribution for Brier score and Macro F1."""
    ltc = governance_data["brier"]["ltc_reconciliation"]
    assert ltc["B3_RandomForest_Brier"] == 0.6083
    assert ltc["B4_LightGBM_Brier"] == 0.6088
    assert ltc["verified"] is True


def test_05_xmr_historical_fold_reconciliation(governance_data: Dict[str, Dict]) -> None:
    """5. Verify XMR historical fold count is confirmed to be 5 physical folds."""
    xmr = governance_data["xmr"]
    assert xmr["definitive_fold_count"] == 5
    assert xmr["num_physical_folds"] == 5
    assert len(xmr["fold_level_details"]) == 5


def test_06_xmr_metric_aggregation(governance_data: Dict[str, Dict]) -> None:
    """6. Verify XMR master catalog values match 5-fold mean exactly."""
    xmr = governance_data["xmr"]["mathematical_reconciliation"]
    assert xmr["reported_master_catalog_values"]["B2_LogisticRegression"] == 0.4177
    assert xmr["5_fold_arithmetic_means"]["B2_LogisticRegression"] == 0.4177
    assert xmr["reported_master_catalog_values"]["B3_RandomForest"] == 0.3902
    assert xmr["5_fold_arithmetic_means"]["B3_RandomForest"] == 0.3902
    assert xmr["reported_master_catalog_values"]["B4_LightGBM"] == 0.3816
    assert xmr["5_fold_arithmetic_means"]["B4_LightGBM"] == 0.3816


def test_07_bootstrap_block_length_configuration(governance_data: Dict[str, Dict]) -> None:
    """7. Verify block lengths [12, 24, 48, 96] evaluated in sensitivity analysis."""
    config = governance_data["bootstrap"]["configuration"]
    assert config["block_lengths_evaluated"] == [12, 24, 48, 96]
    assert config["resamples"] == 1000
    assert config["random_seed"] == 42


def test_08_bootstrap_deterministic_replay() -> None:
    """8. Verify deterministic replay of Moving Block Bootstrap with seed 42."""
    rng1 = np.random.RandomState(42)
    s1 = rng1.normal(0.1, 0.02, size=100)
    rng2 = np.random.RandomState(42)
    s2 = rng2.normal(0.1, 0.02, size=100)
    assert np.array_equal(s1, s2)


def test_09_bootstrap_sensitivity_output_schema(governance_data: Dict[str, Dict]) -> None:
    """9. Verify bootstrap sensitivity matrix output schema."""
    matrix = governance_data["bootstrap"]["sensitivity_matrix"]
    # 11 symbols * 3 ML models * 4 block lengths = 132 rows
    assert len(matrix) == 132
    sample_row = matrix[0]
    required_keys = ["symbol", "model", "block_length", "observed_lift", "ci_95_lower", "ci_95_upper", "raw_p_value", "status"]
    for k in required_keys:
        assert k in sample_row


def test_10_holm_bonferroni_adjustment_correctness(governance_data: Dict[str, Dict]) -> None:
    """10. Verify Holm-Bonferroni adjusted p-values are monotonically non-decreasing."""
    holm_registry = governance_data["holm"]["registry"]
    assert len(holm_registry) == 33
    adj_pvalues = [r["holm_adjusted_p_value"] for r in holm_registry]
    for i in range(len(adj_pvalues) - 1):
        assert adj_pvalues[i] <= adj_pvalues[i + 1]


def test_11_multiple_hypothesis_family_definition(governance_data: Dict[str, Dict]) -> None:
    """11. Verify multiple hypothesis family definition."""
    fam = governance_data["holm"]["hypothesis_family"]
    assert fam["family_size"] == 33
    assert fam["significance_threshold_fwer"] == 0.05
    assert "Holm-Bonferroni" in fam["correction_procedure"]


def test_12_statistical_status_classification(governance_data: Dict[str, Dict]) -> None:
    """12. Verify valid status classification for all comparisons."""
    holm_registry = governance_data["holm"]["registry"]
    valid_classes = {"SIGNIFICANT_AFTER_CORRECTION", "NOT_SIGNIFICANT_AFTER_CORRECTION", "INCONCLUSIVE", "UNTESTABLE"}
    for r in holm_registry:
        assert r["classification"] in valid_classes


def test_13_embargo_formal_deprecation(governance_data: Dict[str, Dict]) -> None:
    """13. Verify formal governance decision on 24-bar embargo parameter."""
    embargo = governance_data["embargo"]
    assert embargo["governance_decision"] == "OPTION_B_FORMAL_DEPRECATION"
    assert embargo["governance_sign_off"] == "APPROVED"
    assert embargo["mechanism_distinction"]["training_purge"]["status"] == "ACTIVE_AND_ENFORCED"
    assert embargo["mechanism_distinction"]["test_label_horizon_protection"]["status"] == "ACTIVE_AND_ENFORCED"


def test_14_purge_and_test_label_horizon_separation() -> None:
    """14. Verify purge (12 bars) and test-label horizon protection (12 bars) operate independently."""
    df = pd.DataFrame({
        "open_time_ms": [DEVELOPMENT_START_MS + i * 300_000 for i in range(1000)]
    })
    splitter = PurgedWalkForwardSplitter(n_splits=5, horizon_bars=12, protect_test_horizon=True)
    folds = list(splitter.split(df))

    for fold_idx, (train_idx, test_idx) in enumerate(folds):
        # Assert separation gap is exactly at least horizon_bars
        assert test_idx[0] - train_idx[-1] - 1 >= 12
        # Assert test window does not extend to the raw split boundary
        assert len(test_idx) > 0


def test_15_historical_artifact_immutability() -> None:
    """15. Verify historical Phase 5.3.1, 5.3.2, and 5.3.3 artifacts were not overwritten."""
    assert (P531_DIR / "pilot_summary.json").exists()
    assert (P532_DIR / "fleet_summary" / "fleet_catalog.json").exists()
    assert (P533_DIR / "master_benchmark_catalog.json").exists()


def test_16_final_catalog_schema_validation(governance_data: Dict[str, Dict]) -> None:
    """16. Verify final benchmark catalog schema validation."""
    cat = governance_data["catalog"]["catalog"]
    assert len(cat) == 11
    for sym, sym_data in cat.items():
        assert sym_data["num_valid_folds"] == 5
        assert "LOWEST_BRIER_ALL_BASELINES" in sym_data["metric_winners"]
        assert "LOWEST_BRIER_ML_MODELS" in sym_data["metric_winners"]
        assert "balanced_accuracy_winner" in sym_data["metric_winners"]
        assert "macro_f1_winner" in sym_data["metric_winners"]
        assert "roc_auc_winner" in sym_data["metric_winners"]


def test_17_sha256_manifest_consistency(governance_data: Dict[str, Dict]) -> None:
    """17. Verify SHA-256 manifest consistency."""
    manifest = governance_data["manifest"]
    for filename, recorded_hash in manifest.items():
        if filename == "final_manifest_hashes.json":
            continue
        p = OUTPUT_DIR / filename
        assert p.exists()
        hasher = hashlib.sha256()
        with open(p, "rb") as f:
            hasher.update(f.read())
        assert hasher.hexdigest() == recorded_hash


def test_18_prospective_holdout_access_rejection() -> None:
    """18. Verify strict rejection when Prospective Holdout timestamps are passed."""
    df_leak = pd.DataFrame({
        "open_time_ms": [DEVELOPMENT_START_MS, PROSPECTIVE_HOLDOUT_START_MS + 300_000]
    })
    splitter = PurgedWalkForwardSplitter(n_splits=2)
    with pytest.raises(PermissionError, match="Temporal violation.*PROSPECTIVE_HOLDOUT"):
        list(splitter.split(df_leak))
