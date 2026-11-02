"""Materialized Out-Of-Fold (OOF) Probability Adapter for Phase 5.5.

Safely loads and aligns pre-computed frozen Phase 5.3 model out-of-fold predictions
from `artifacts/phase_5_4/materialized_oof/` without retraining or recalibrating models.
Enforces causal temporal alignment, strict fold metadata integrity, cross-asset mapping
validation, probability simplex checks, prospective holdout sealing, and bounded RAM usage.
"""

from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from pydantic import BaseModel, ConfigDict, Field

from quantum.backtesting.resources import BACKTEST_MAX_THREADS, enforce_backtest_thread_limits


FULL_ARTIFACT_UNIVERSE: Tuple[str, ...] = (
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "ADAUSDT",
    "SOLUSDT",
    "AVAXUSDT",
    "LINKUSDT",
    "DOGEUSDT",
    "LTCUSDT",
    "XMRUSDT",
)

PRIMARY_RESEARCH_UNIVERSE: Tuple[str, ...] = (
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "ADAUSDT",
    "SOLUSDT",
    "AVAXUSDT",
    "LINKUSDT",
    "DOGEUSDT",
    "LTCUSDT",
)

STRUCTURAL_BREAK_SUBGROUP: Tuple[str, ...] = ("XMRUSDT",)

# 2026-11-01 00:00:00 UTC in milliseconds
PROSPECTIVE_HOLDOUT_START_MS: int = 1793491200000


class OOFSignal(BaseModel):
    """Immutable model predictive signal at candle i close."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    symbol: str
    fold: int = Field(ge=1, le=5)
    open_time_ms: int = Field(gt=0, description="Opening timestamp of candle i")
    close_time_ms: int = Field(gt=0, description="Closing timestamp of candle i (inference time)")
    predicted_class: int = Field(description="-1 (SL), 0 (EXP), 1 (TP)")
    prob_tp: float = Field(ge=0.0, le=1.0, description="P(y = +1 | X_i)")
    prob_sl: float = Field(ge=0.0, le=1.0, description="P(y = -1 | X_i)")
    prob_exp: float = Field(ge=0.0, le=1.0, description="P(y = 0 | X_i)")
    true_label: int = Field(description="Ground truth ML target label")
    oos_eligibility: str = Field(description="VERIFIED_OOF or OOS_ELIGIBILITY_NOT_VERIFIED")
    universe_tier: str = Field(
        default="PRIMARY_RESEARCH_UNIVERSE",
        description="PRIMARY_RESEARCH_UNIVERSE or STRUCTURAL_BREAK_SUBGROUP_DEC_06_PENDING",
    )


class OOFDatasetMetadata(BaseModel):
    """Audit metadata for a single asset's materialized OOF artifact."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    symbol: str
    universe_tier: str
    file_path: str
    exists: bool
    row_count: int = 0
    folds_present: List[int] = Field(default_factory=list)
    fold_row_counts: Dict[int, int] = Field(default_factory=dict)
    min_open_time_ms: Optional[int] = None
    max_open_time_ms: Optional[int] = None
    max_simplex_error: Optional[float] = None
    has_duplicates: bool = False
    has_nulls: bool = False
    cross_asset_mismatch: bool = False
    is_monotonic_increasing: bool = False
    holdout_seal_preserved: bool = True
    fold_5_status: str = "OOS_ELIGIBILITY_NOT_VERIFIED"
    dec_06_status: str = "PENDING_HUMAN_DECISION"


class OOFProbabilityAdapter:
    """Adapter for reading and causally querying materialized out-of-fold probability artifacts."""

    REQUIRED_COLUMNS: List[str] = [
        "instrument",
        "fold",
        "open_time_ms",
        "true_label",
        "predicted_class",
        "raw_prob_m1",
        "raw_prob_0",
        "raw_prob_p1",
    ]
    VALID_CLASSES = {-1, 0, 1}
    VALID_FOLDS = {1, 2, 3, 4, 5}

    def __init__(
        self,
        oof_dir: Optional[Path] = None,
        timeframe_ms: int = 300_000,
        cache_enabled: bool = False,
        simplex_tolerance: float = 1e-4,
    ) -> None:
        self.oof_dir = Path(oof_dir) if oof_dir else Path("artifacts/phase_5_4/materialized_oof")
        self.timeframe_ms = timeframe_ms
        self.cache_enabled = cache_enabled
        self.simplex_tolerance = simplex_tolerance
        self._cache: Dict[str, pd.DataFrame] = {}
        enforce_backtest_thread_limits(BACKTEST_MAX_THREADS)

    @staticmethod
    def get_universe_tier(symbol: str) -> str:
        """Return governance universe tier for symbol without altering scope."""
        if symbol in PRIMARY_RESEARCH_UNIVERSE:
            return "PRIMARY_RESEARCH_UNIVERSE"
        if symbol in STRUCTURAL_BREAK_SUBGROUP:
            return "STRUCTURAL_BREAK_SUBGROUP_DEC_06_PENDING"
        return "UNREGISTERED_ASSET"

    def clear_cache(self) -> None:
        """Evict all cached DataFrames to bound memory usage."""
        self._cache.clear()

    def load_oof_dataset(
        self,
        symbol: str,
        fold: Optional[int] = None,
        require_primary_universe: bool = False,
    ) -> pd.DataFrame:
        """Load materialized OOF Parquet dataset for symbol, optionally filtering by fold.

        Parameters
        ----------
        symbol : str
            Asset symbol (e.g. "BTCUSDT").
        fold : int, optional
            Filter for fold 1 to 5.
        require_primary_universe : bool
            If True, raises ValueError if symbol is not in the 10-asset PRIMARY_RESEARCH_UNIVERSE.

        Returns
        -------
        pd.DataFrame
            Validated DataFrame sorted ascending by open_time_ms.
        """
        if require_primary_universe and symbol not in PRIMARY_RESEARCH_UNIVERSE:
            raise ValueError(
                f"Symbol {symbol} is not in PRIMARY_RESEARCH_UNIVERSE "
                f"(tier: {self.get_universe_tier(symbol)}; DEC_06 pending)"
            )

        if fold is not None and fold not in self.VALID_FOLDS:
            raise ValueError(f"Invalid fold {fold}; must be in [1, 2, 3, 4, 5]")

        cache_key = f"{symbol}_fold_{fold}" if fold else symbol
        if self.cache_enabled and cache_key in self._cache:
            return self._cache[cache_key].copy()

        enforce_backtest_thread_limits(BACKTEST_MAX_THREADS)

        fpath = self.oof_dir / f"{symbol}_oof.parquet"
        if not fpath.exists():
            raise FileNotFoundError(f"Materialized OOF artifact not found at {fpath}")

        table = pq.read_table(fpath)
        for col in self.REQUIRED_COLUMNS:
            if col not in table.schema.names:
                raise ValueError(f"OOF Parquet {fpath} missing required column: {col}")

        df = table.to_pandas()
        if df.empty:
            raise ValueError(f"OOF Parquet {fpath} is empty")

        # 1. Validate missing values
        if df[self.REQUIRED_COLUMNS].isnull().any().any():
            null_cols = df[self.REQUIRED_COLUMNS].isnull().sum()
            raise ValueError(f"OOF Parquet {fpath} contains NaN/null values:\n{null_cols}")

        # 2. Validate cross-asset mapping
        unique_instruments = df["instrument"].unique()
        if len(unique_instruments) != 1 or str(unique_instruments[0]) != symbol:
            raise ValueError(
                f"Cross-asset mapping error in {fpath}: expected '{symbol}', found {unique_instruments.tolist()}"
            )

        # 3. Validate duplicate timestamps
        dups = df.duplicated(subset=["open_time_ms"])
        if dups.any():
            num_dups = int(dups.sum())
            raise ValueError(f"OOF Parquet {fpath} contains {num_dups} duplicate open_time_ms values")

        # 4. Validate prospective holdout boundary (strictly < 2026-11-01 00:00:00 UTC)
        if (df["open_time_ms"] >= PROSPECTIVE_HOLDOUT_START_MS).any():
            raise ValueError(
                f"GOVERNANCE VIOLATION: OOF Parquet {fpath} contains timestamps >= {PROSPECTIVE_HOLDOUT_START_MS} "
                f"(prospective holdout is STRICTLY_SEALED)"
            )

        # 5. Validate fold numbers and class labels
        invalid_folds = set(df["fold"].unique()) - self.VALID_FOLDS
        if invalid_folds:
            raise ValueError(f"OOF Parquet {fpath} contains invalid folds: {invalid_folds}")

        invalid_true = set(df["true_label"].unique()) - self.VALID_CLASSES
        if invalid_true:
            raise ValueError(f"OOF Parquet {fpath} contains invalid true_label values: {invalid_true}")

        invalid_pred = set(df["predicted_class"].unique()) - self.VALID_CLASSES
        if invalid_pred:
            raise ValueError(f"OOF Parquet {fpath} contains invalid predicted_class values: {invalid_pred}")

        # 6. Validate probability bounds and simplex
        prob_cols = ["raw_prob_m1", "raw_prob_0", "raw_prob_p1"]
        prob_matrix = df[prob_cols].to_numpy(dtype=float)
        if not np.all(np.isfinite(prob_matrix)):
            raise ValueError(f"OOF Parquet {fpath} contains non-finite probability values")
        if np.any(prob_matrix < -1e-7) or np.any(prob_matrix > 1.0 + 1e-7):
            raise ValueError(f"OOF Parquet {fpath} contains probabilities outside [0.0, 1.0]")

        prob_sums = np.sum(prob_matrix, axis=1)
        max_simplex_err = float(np.max(np.abs(prob_sums - 1.0)))
        if max_simplex_err > self.simplex_tolerance:
            raise ValueError(
                f"OOF Parquet {fpath} violates probability simplex: max |sum(p) - 1| = {max_simplex_err:.6e} > {self.simplex_tolerance}"
            )

        # 7. Sort ascending by timestamp and annotate metadata columns
        df = df.sort_values("open_time_ms", kind="mergesort").reset_index(drop=True)
        df["oos_eligibility"] = np.where(
            df["fold"] == 5,
            "OOS_ELIGIBILITY_NOT_VERIFIED",
            "VERIFIED_OOF",
        )
        df["universe_tier"] = self.get_universe_tier(symbol)

        if fold is not None:
            df = df[df["fold"] == fold].copy().reset_index(drop=True)

        if self.cache_enabled:
            self._cache[cache_key] = df

        return df.copy() if self.cache_enabled else df

    def iter_signals(
        self,
        symbol: str,
        fold: Optional[int] = None,
        require_primary_universe: bool = False,
    ) -> Iterator[OOFSignal]:
        """Stream causal OOFSignal objects lazily without building a full list in memory."""
        df = self.load_oof_dataset(symbol, fold=fold, require_primary_universe=require_primary_universe)
        tier = self.get_universe_tier(symbol)

        for row in df.itertuples(index=False):
            f_num = int(row.fold)
            oos_status = "OOS_ELIGIBILITY_NOT_VERIFIED" if f_num == 5 else "VERIFIED_OOF"
            open_ts = int(row.open_time_ms)
            close_ts = open_ts + self.timeframe_ms

            yield OOFSignal(
                symbol=str(row.instrument),
                fold=f_num,
                open_time_ms=open_ts,
                close_time_ms=close_ts,
                predicted_class=int(row.predicted_class),
                prob_tp=float(np.clip(row.raw_prob_p1, 0.0, 1.0)),
                prob_sl=float(np.clip(row.raw_prob_m1, 0.0, 1.0)),
                prob_exp=float(np.clip(row.raw_prob_0, 0.0, 1.0)),
                true_label=int(row.true_label),
                oos_eligibility=oos_status,
                universe_tier=tier,
            )

    def get_signal_series(
        self,
        symbol: str,
        fold: Optional[int] = None,
        require_primary_universe: bool = False,
    ) -> List[OOFSignal]:
        """Convert OOF dataset into an immutable list of causal OOFSignal objects."""
        return list(self.iter_signals(symbol, fold=fold, require_primary_universe=require_primary_universe))

    def inspect_asset_metadata(self, symbol: str) -> OOFDatasetMetadata:
        """Audit an asset's OOF Parquet file and return comprehensive validation metadata."""
        tier = self.get_universe_tier(symbol)
        fpath = self.oof_dir / f"{symbol}_oof.parquet"
        if not fpath.exists():
            return OOFDatasetMetadata(
                symbol=symbol,
                universe_tier=tier,
                file_path=str(fpath),
                exists=False,
            )

        table = pq.read_table(fpath)
        for col in self.REQUIRED_COLUMNS:
            if col not in table.schema.names:
                raise ValueError(f"OOF Parquet {fpath} missing required column: {col}")

        df = table.to_pandas()
        has_nulls = bool(df[self.REQUIRED_COLUMNS].isnull().any().any())
        has_dups = bool(df.duplicated(subset=["open_time_ms"]).any())
        unique_inst = df["instrument"].unique()
        cross_mismatch = len(unique_inst) != 1 or str(unique_inst[0]) != symbol
        is_monotonic = bool(df["open_time_ms"].is_monotonic_increasing)

        prob_matrix = df[["raw_prob_m1", "raw_prob_0", "raw_prob_p1"]].to_numpy(dtype=float)
        max_simplex_err = float(np.max(np.abs(np.sum(prob_matrix, axis=1) - 1.0))) if len(df) > 0 else 0.0

        min_ts = int(df["open_time_ms"].min()) if len(df) > 0 else None
        max_ts = int(df["open_time_ms"].max()) if len(df) > 0 else None
        holdout_ok = bool(max_ts < PROSPECTIVE_HOLDOUT_START_MS) if max_ts is not None else True

        folds_present = sorted(int(x) for x in df["fold"].unique())
        fold_counts = {int(k): int(v) for k, v in df["fold"].value_counts().sort_index().items()}

        return OOFDatasetMetadata(
            symbol=symbol,
            universe_tier=tier,
            file_path=str(fpath),
            exists=True,
            row_count=len(df),
            folds_present=folds_present,
            fold_row_counts=fold_counts,
            min_open_time_ms=min_ts,
            max_open_time_ms=max_ts,
            max_simplex_error=max_simplex_err,
            has_duplicates=has_dups,
            has_nulls=has_nulls,
            cross_asset_mismatch=cross_mismatch,
            is_monotonic_increasing=is_monotonic,
            holdout_seal_preserved=holdout_ok,
        )

    def audit_universe_manifest(
        self,
        universe: Tuple[str, ...] = FULL_ARTIFACT_UNIVERSE,
    ) -> Dict[str, OOFDatasetMetadata]:
        """Sequentially audit all assets in the specified universe with bounded memory."""
        report: Dict[str, OOFDatasetMetadata] = {}
        for sym in universe:
            report[sym] = self.inspect_asset_metadata(sym)
        return report
