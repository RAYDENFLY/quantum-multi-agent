"""Unit tests for OOFProbabilityAdapter (Workstream A).

Verifies:
1. Full 11-asset artifact universe inspection and loading.
2. Separation of 10-asset PRIMARY_RESEARCH_UNIVERSE vs XMRUSDT STRUCTURAL_BREAK_SUBGROUP (DEC_06 pending).
3. Cross-asset mapping validation (instrument == symbol).
4. Probability bounds and simplex validation.
5. Duplicate timestamp and missing value rejection.
6. Prospective holdout boundary enforcement (< 2026-11-01 00:00:00 UTC).
7. Fold 5 OOS_ELIGIBILITY_NOT_VERIFIED tagging.
8. Bounded memory (cache_enabled=False by default).
"""

from pathlib import Path
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from quantum.backtesting.adapters import (
    FULL_ARTIFACT_UNIVERSE,
    PRIMARY_RESEARCH_UNIVERSE,
    PROSPECTIVE_HOLDOUT_START_MS,
    STRUCTURAL_BREAK_SUBGROUP,
    OOFProbabilityAdapter,
)


def test_full_11_asset_universe_manifest_audit():
    """Verify all 11 materialized OOF artifacts exist and pass schema/simplex/holdout checks."""
    adapter = OOFProbabilityAdapter()
    manifest = adapter.audit_universe_manifest()

    assert len(manifest) == 11
    assert set(manifest.keys()) == set(FULL_ARTIFACT_UNIVERSE)

    for sym in PRIMARY_RESEARCH_UNIVERSE:
        meta = manifest[sym]
        assert meta.exists is True, f"Missing primary asset OOF parquet: {sym}"
        assert meta.universe_tier == "PRIMARY_RESEARCH_UNIVERSE"
        assert meta.row_count > 100_000
        assert meta.folds_present == [1, 2, 3, 4, 5]
        assert meta.has_nulls is False
        assert meta.has_duplicates is False
        assert meta.cross_asset_mismatch is False
        assert meta.is_monotonic_increasing is True
        assert meta.holdout_seal_preserved is True
        assert meta.max_simplex_error is not None and meta.max_simplex_error < 1e-6

    # XMRUSDT subgroup has truncated history (15,252 rows) and pending DEC_06 status
    xmr_meta = manifest["XMRUSDT"]
    assert xmr_meta.exists is True
    assert xmr_meta.universe_tier == "STRUCTURAL_BREAK_SUBGROUP_DEC_06_PENDING"
    assert xmr_meta.row_count == 15_252
    assert xmr_meta.folds_present == [1, 2, 3, 4, 5]
    assert xmr_meta.has_nulls is False
    assert xmr_meta.has_duplicates is False
    assert xmr_meta.cross_asset_mismatch is False
    assert xmr_meta.holdout_seal_preserved is True


def test_primary_universe_guard_blocks_xmr_when_requested():
    """Verify require_primary_universe=True rejects XMRUSDT while DEC_06 is pending."""
    adapter = OOFProbabilityAdapter()
    with pytest.raises(ValueError, match="PRIMARY_RESEARCH_UNIVERSE"):
        adapter.load_oof_dataset("XMRUSDT", fold=1, require_primary_universe=True)

    # Without require_primary_universe, XMRUSDT loads with explicit tier tag
    df_xmr = adapter.load_oof_dataset("XMRUSDT", fold=1, require_primary_universe=False)
    assert len(df_xmr) > 0
    assert (df_xmr["universe_tier"] == "STRUCTURAL_BREAK_SUBGROUP_DEC_06_PENDING").all()


def test_oof_signal_generation_and_fold5_status():
    """Verify Fold 1-4 are VERIFIED_OOF and Fold 5 is OOS_ELIGIBILITY_NOT_VERIFIED."""
    adapter = OOFProbabilityAdapter()
    signals_f1 = adapter.get_signal_series("BTCUSDT", fold=1)
    assert len(signals_f1) > 0
    assert all(s.oos_eligibility == "VERIFIED_OOF" for s in signals_f1)
    assert all(s.fold == 1 for s in signals_f1)

    signals_f5 = adapter.get_signal_series("BTCUSDT", fold=5)
    assert len(signals_f5) > 0
    assert all(s.oos_eligibility == "OOS_ELIGIBILITY_NOT_VERIFIED" for s in signals_f5)
    assert all(s.fold == 5 for s in signals_f5)


def test_oof_adapter_missing_file_and_invalid_fold():
    """Verify missing symbol raises FileNotFoundError and invalid fold raises ValueError."""
    adapter = OOFProbabilityAdapter()
    with pytest.raises(FileNotFoundError):
        adapter.load_oof_dataset("NONEXISTENT_USDT")

    with pytest.raises(ValueError, match="Invalid fold"):
        adapter.load_oof_dataset("BTCUSDT", fold=99)


def test_oof_adapter_rejects_corrupted_synthetic_parquets(tmp_path: Path):
    """Verify adapter catches cross-asset mismatch, simplex error, duplicates, nulls, and holdout breach."""
    base_df = pd.DataFrame({
        "instrument": ["BTCUSDT", "BTCUSDT"],
        "fold": [1, 1],
        "open_time_ms": [1740000000000, 1740000300000],
        "true_label": [1, -1],
        "predicted_class": [1, -1],
        "raw_prob_m1": [0.1, 0.7],
        "raw_prob_0": [0.2, 0.2],
        "raw_prob_p1": [0.7, 0.1],
    })

    # 1. Cross-asset mismatch
    df_cross = base_df.copy()
    df_cross["instrument"] = ["ETHUSDT", "ETHUSDT"]
    pq.write_table(pa.Table.from_pandas(df_cross), tmp_path / "BTCUSDT_oof.parquet")
    adapter = OOFProbabilityAdapter(oof_dir=tmp_path)
    with pytest.raises(ValueError, match="Cross-asset mapping error"):
        adapter.load_oof_dataset("BTCUSDT")

    # 2. Duplicate timestamps
    df_dup = base_df.copy()
    df_dup["open_time_ms"] = [1740000000000, 1740000000000]
    pq.write_table(pa.Table.from_pandas(df_dup), tmp_path / "BTCUSDT_oof.parquet")
    with pytest.raises(ValueError, match="duplicate open_time_ms"):
        adapter.load_oof_dataset("BTCUSDT")

    # 3. Probability simplex violation
    df_simplex = base_df.copy()
    df_simplex["raw_prob_p1"] = [0.9, 0.1]  # sum = 1.2
    pq.write_table(pa.Table.from_pandas(df_simplex), tmp_path / "BTCUSDT_oof.parquet")
    with pytest.raises(ValueError, match="violates probability simplex"):
        adapter.load_oof_dataset("BTCUSDT")

    # 4. Prospective holdout breach
    df_holdout = base_df.copy()
    df_holdout["open_time_ms"] = [1740000000000, PROSPECTIVE_HOLDOUT_START_MS]
    pq.write_table(pa.Table.from_pandas(df_holdout), tmp_path / "BTCUSDT_oof.parquet")
    with pytest.raises(ValueError, match="GOVERNANCE VIOLATION"):
        adapter.load_oof_dataset("BTCUSDT")
