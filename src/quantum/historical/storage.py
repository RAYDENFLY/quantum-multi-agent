"""Columnar Parquet storage manager for raw, canonical, and feature datasets."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from quantum.core.logging import get_logger
from quantum.domain.enums import Exchange, Timeframe
from quantum.historical.models import CanonicalCandle, DatasetManifest, RawHistoricalCandle

logger = get_logger("historical.storage")

RAW_ARROW_SCHEMA = pa.schema([
    ("exchange", pa.string()),
    ("symbol", pa.string()),
    ("contract_type", pa.string()),
    ("timeframe", pa.string()),
    ("exchange_candle_ts_ms", pa.int64()),
    ("raw_open", pa.string()),
    ("raw_high", pa.string()),
    ("raw_low", pa.string()),
    ("raw_close", pa.string()),
    ("raw_volume", pa.string()),
    ("raw_turnover", pa.string()),
    ("raw_trades", pa.string()),
    ("raw_taker_buy_volume", pa.string()),
    ("raw_taker_buy_turnover", pa.string()),
    ("raw_payload_json", pa.string()),
    ("retrieval_timestamp_ms", pa.int64()),
    ("source_endpoint", pa.string()),
    ("collection_run_id", pa.string()),
])

CANONICAL_ARROW_SCHEMA = pa.schema([
    ("exchange", pa.string()),
    ("symbol", pa.string()),
    ("market_type", pa.string()),
    ("timeframe", pa.string()),
    ("open_time_ms", pa.int64()),
    ("close_time_ms", pa.int64()),
    ("open", pa.float64()),
    ("high", pa.float64()),
    ("low", pa.float64()),
    ("close", pa.float64()),
    ("volume", pa.float64()),
    ("quote_volume", pa.float64()),
    ("trade_count", pa.int64()),
    ("taker_buy_volume", pa.float64()),
    ("taker_buy_quote_volume", pa.float64()),
    ("ingestion_time_ms", pa.int64()),
    ("source_run_id", pa.string()),
])


def compute_file_sha256(file_path: Path) -> str:
    """Compute SHA-256 hex digest for a file."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as fh:
        while chunk := fh.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class ParquetStorageManager:
    """Manages chunked, partitioned Parquet datasets with schema validation and manifests."""

    _partition_locks: Dict[str, threading.Lock] = {}
    _meta_lock = threading.Lock()

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.raw_dir = self.base_dir / "raw"
        self.canonical_dir = self.base_dir / "canonical"
        self.features_dir = self.base_dir / "features"

        for directory in [self.raw_dir, self.canonical_dir, self.features_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        self._cleanup_stale_temp_files()

    @classmethod
    def _get_partition_lock(cls, partition_dir: Path) -> threading.Lock:
        with cls._meta_lock:
            key = str(partition_dir.resolve())
            if key not in cls._partition_locks:
                cls._partition_locks[key] = threading.Lock()
            return cls._partition_locks[key]

    def _cleanup_stale_temp_files(self) -> None:
        """Clean up orphaned temporary files left by abruptly terminated processes."""
        try:
            for tmp in self.base_dir.rglob("*.tmp.*.parquet"):
                try:
                    # If older than 60 seconds, remove
                    if time.time() - tmp.stat().st_mtime > 60:
                        tmp.unlink()
                except OSError:
                    pass
        except Exception:
            pass

    def get_partition_dir(
        self,
        layer: str,
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
    ) -> Path:
        """Resolve directory path for a partition."""
        ex_str = exchange.value if hasattr(exchange, "value") else str(exchange)
        sym_str = symbol.upper()
        tf_str = timeframe.value if hasattr(timeframe, "value") else str(timeframe)
        return self.base_dir / layer / f"exchange={ex_str}" / f"symbol={sym_str}" / f"timeframe={tf_str}"

    def get_partition_path(
        self,
        layer: str,
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
        year: Optional[int] = None,
    ) -> Path:
        """Resolve partitioned directory and file path."""
        partition_dir = self.get_partition_dir(layer, exchange, symbol, timeframe)
        partition_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{year}.parquet" if year else "data.parquet"
        return partition_dir / filename

    def write_raw_candles(
        self,
        candles: List[RawHistoricalCandle],
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
        year: Optional[int] = None,
    ) -> Path:
        """Write raw candles to Parquet partition, appending and handling conflicts."""
        if not candles:
            raise ValueError("No raw candles provided to write")

        records: List[Dict[str, Any]] = []
        for c in candles:
            records.append({
                "exchange": c.exchange.value if hasattr(c.exchange, "value") else str(c.exchange),
                "symbol": c.symbol.upper(),
                "contract_type": c.contract_type,
                "timeframe": c.timeframe.value if hasattr(c.timeframe, "value") else str(c.timeframe),
                "exchange_candle_ts_ms": c.exchange_candle_ts_ms,
                "raw_open": c.raw_open,
                "raw_high": c.raw_high,
                "raw_low": c.raw_low,
                "raw_close": c.raw_close,
                "raw_volume": c.raw_volume,
                "raw_turnover": c.raw_turnover,
                "raw_trades": c.raw_trades,
                "raw_taker_buy_volume": c.raw_taker_buy_volume,
                "raw_taker_buy_turnover": c.raw_taker_buy_turnover,
                "raw_payload_json": c.raw_payload_json,
                "retrieval_timestamp_ms": c.retrieval_timestamp_ms,
                "source_endpoint": c.source_endpoint,
                "collection_run_id": c.collection_run_id,
            })

        df_new = pd.DataFrame(records)
        target_path = self.get_partition_path("raw", exchange, symbol, timeframe, year=year)
        lock = self._get_partition_lock(target_path.parent)

        with lock:
            if target_path.exists():
                df_existing = pd.read_parquet(target_path)

                # Check for conflicting duplicates on overlapping timestamps
                existing_ts = set(df_existing["exchange_candle_ts_ms"])
                new_ts = set(df_new["exchange_candle_ts_ms"])
                overlap = existing_ts.intersection(new_ts)

                if overlap:
                    cols_to_compare = ["raw_open", "raw_high", "raw_low", "raw_close", "raw_volume"]
                    common_cols = [c for c in cols_to_compare if c in df_existing.columns and c in df_new.columns]

                    sub_exist = df_existing[df_existing["exchange_candle_ts_ms"].isin(overlap)].set_index("exchange_candle_ts_ms")
                    sub_new = df_new[df_new["exchange_candle_ts_ms"].isin(overlap)].set_index("exchange_candle_ts_ms")

                    conflicts: List[Dict[str, Any]] = []
                    for ts in overlap:
                        row_e = sub_exist.loc[ts]
                        row_n = sub_new.loc[ts]
                        e_dict = row_e.to_dict() if isinstance(row_e, pd.Series) else row_e.iloc[0].to_dict()
                        n_dict = row_n.to_dict() if isinstance(row_n, pd.Series) else row_n.iloc[0].to_dict()

                        differs = any(str(e_dict.get(col)) != str(n_dict.get(col)) for col in common_cols)
                        if differs:
                            conflicts.append({
                                "timestamp_ms": ts,
                                "existing_run_id": str(e_dict.get("collection_run_id", "")),
                                "existing_values": {c: str(e_dict.get(c)) for c in common_cols},
                                "incoming_run_id": str(n_dict.get("collection_run_id", "")),
                                "incoming_values": {c: str(n_dict.get(c)) for c in common_cols},
                                "detected_at_ms": int(time.time() * 1000),
                            })

                    if conflicts:
                        logger.warning(
                            "Detected %d conflicting raw candles for %s %s! Quarantining to conflicts log.",
                            len(conflicts), symbol, timeframe.value if hasattr(timeframe, 'value') else timeframe
                        )
                        self._record_raw_conflicts(conflicts, exchange, symbol, timeframe)

                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                df_combined.drop_duplicates(subset=["exchange_candle_ts_ms"], keep="last", inplace=True)
                df_combined.sort_values(by="exchange_candle_ts_ms", ascending=True, inplace=True)
            else:
                df_combined = df_new.drop_duplicates(subset=["exchange_candle_ts_ms"], keep="last")
                df_combined.sort_values(by="exchange_candle_ts_ms", ascending=True, inplace=True)

            table = pa.Table.from_pandas(df_combined, schema=RAW_ARROW_SCHEMA, preserve_index=False)
            self._atomic_write_parquet(table, target_path)
            logger.info("Wrote %d raw rows to %s", len(table), target_path)
            return target_path

    def write_canonical_candles(
        self,
        candles: List[CanonicalCandle],
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
        year: Optional[int] = None,
    ) -> Path:
        """Write canonical candles to Parquet partition, validating schema and deduplicating."""
        if not candles:
            raise ValueError("No canonical candles provided to write")

        records: List[Dict[str, Any]] = []
        for c in candles:
            records.append({
                "exchange": c.exchange.value if hasattr(c.exchange, "value") else str(c.exchange),
                "symbol": c.symbol.upper(),
                "market_type": c.market_type,
                "timeframe": c.timeframe.value if hasattr(c.timeframe, "value") else str(c.timeframe),
                "open_time_ms": c.open_time_ms,
                "close_time_ms": c.close_time_ms,
                "open": float(c.open),
                "high": float(c.high),
                "low": float(c.low),
                "close": float(c.close),
                "volume": float(c.volume),
                "quote_volume": float(c.quote_volume) if c.quote_volume is not None else None,
                "trade_count": int(c.trade_count) if c.trade_count is not None else None,
                "taker_buy_volume": float(c.taker_buy_volume) if c.taker_buy_volume is not None else None,
                "taker_buy_quote_volume": float(c.taker_buy_quote_volume) if c.taker_buy_quote_volume is not None else None,
                "ingestion_time_ms": c.ingestion_time_ms,
                "source_run_id": c.source_run_id,
            })

        df_new = pd.DataFrame(records)
        target_path = self.get_partition_path("canonical", exchange, symbol, timeframe, year=year)
        lock = self._get_partition_lock(target_path.parent)

        with lock:
            if target_path.exists():
                df_existing = pd.read_parquet(target_path)
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                df_combined.drop_duplicates(subset=["open_time_ms"], keep="last", inplace=True)
                df_combined.sort_values(by="open_time_ms", ascending=True, inplace=True)
            else:
                df_combined = df_new.drop_duplicates(subset=["open_time_ms"], keep="last")
                df_combined.sort_values(by="open_time_ms", ascending=True, inplace=True)

            table = pa.Table.from_pandas(df_combined, schema=CANONICAL_ARROW_SCHEMA, preserve_index=False)
            self._atomic_write_parquet(table, target_path)
            logger.info("Wrote %d canonical rows to %s", len(table), target_path)
            return target_path

    def write_canonical_partitioned_by_year(
        self,
        candles: List[CanonicalCandle],
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
    ) -> List[Path]:
        """Partition canonical candles by UTC year to bound per-file size and rewrite I/O."""
        by_year: Dict[int, List[CanonicalCandle]] = {}
        for c in candles:
            yr = datetime.fromtimestamp(c.open_time_ms / 1000, tz=timezone.utc).year
            by_year.setdefault(yr, []).append(c)

        paths: List[Path] = []
        for yr, yr_candles in sorted(by_year.items()):
            p = self.write_canonical_candles(yr_candles, exchange, symbol, timeframe, year=yr)
            paths.append(p)
        return paths

    def write_features(
        self,
        df_features: pd.DataFrame,
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
        year: Optional[int] = None,
    ) -> Path:
        """Write feature DataFrame to Parquet with atomic swap."""
        if df_features.empty:
            raise ValueError("Feature DataFrame is empty")

        if "open_time_ms" not in df_features.columns:
            raise ValueError("Feature DataFrame must contain open_time_ms as reference timestamp")

        target_path = self.get_partition_path("features", exchange, symbol, timeframe, year=year)
        lock = self._get_partition_lock(target_path.parent)

        with lock:
            df_sorted = df_features.drop_duplicates(subset=["open_time_ms"], keep="last").sort_values(by="open_time_ms")
            table = pa.Table.from_pandas(df_sorted, preserve_index=False)
            self._atomic_write_parquet(table, target_path)
            logger.info("Wrote %d feature rows to %s", len(table), target_path)
            return target_path

    def _record_raw_conflicts(
        self,
        conflicts: List[Dict[str, Any]],
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
    ) -> Path:
        """Persist conflicting raw candles to quarantine audit file."""
        partition_dir = self.get_partition_dir("raw", exchange, symbol, timeframe)
        conflict_path = partition_dir / "conflicts.parquet"

        df_new_conf = pd.DataFrame([{
            "timestamp_ms": c["timestamp_ms"],
            "existing_run_id": c["existing_run_id"],
            "existing_values_json": json.dumps(c["existing_values"]),
            "incoming_run_id": c["incoming_run_id"],
            "incoming_values_json": json.dumps(c["incoming_values"]),
            "detected_at_ms": c["detected_at_ms"],
        } for c in conflicts])

        if conflict_path.exists():
            df_prior = pd.read_parquet(conflict_path)
            df_combined = pd.concat([df_prior, df_new_conf], ignore_index=True)
        else:
            df_combined = df_new_conf

        table = pa.Table.from_pandas(df_combined, preserve_index=False)
        self._atomic_write_parquet(table, conflict_path)
        return conflict_path

    def read_raw_conflicts(
        self,
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
    ) -> pd.DataFrame:
        """Read quarantined conflicting raw records if any."""
        partition_dir = self.get_partition_dir("raw", exchange, symbol, timeframe)
        conflict_path = partition_dir / "conflicts.parquet"
        if not conflict_path.exists():
            return pd.DataFrame()
        return pd.read_parquet(conflict_path)

    def read_raw(
        self,
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
        start_time_ms: Optional[int] = None,
        end_time_ms: Optional[int] = None,
    ) -> pd.DataFrame:
        """Read raw candles as pandas DataFrame with optional time range filter."""
        partition_dir = self.get_partition_dir("raw", exchange, symbol, timeframe)
        if not partition_dir.exists():
            return pd.DataFrame()

        files = [
            f for f in partition_dir.glob("*.parquet")
            if not f.name.startswith(".") and ".tmp." not in f.name and f.name != "conflicts.parquet"
        ]
        if not files:
            return pd.DataFrame()

        dfs: List[pd.DataFrame] = []
        for file_path in files:
            if file_path.stem.isdigit() and len(file_path.stem) == 4:
                file_year = int(file_path.stem)
                year_start = int(datetime(file_year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
                year_end = int(datetime(file_year + 1, 1, 1, tzinfo=timezone.utc).timestamp() * 1000) - 1
                if start_time_ms is not None and year_end < start_time_ms:
                    continue
                if end_time_ms is not None and year_start > end_time_ms:
                    continue

            df = pd.read_parquet(file_path)
            if not df.empty:
                if start_time_ms is not None:
                    df = df[df["exchange_candle_ts_ms"] >= start_time_ms]
                if end_time_ms is not None:
                    df = df[df["exchange_candle_ts_ms"] <= end_time_ms]
                if not df.empty:
                    dfs.append(df)

        if not dfs:
            return pd.DataFrame()

        df_combined = pd.concat(dfs, ignore_index=True)
        df_combined.drop_duplicates(subset=["exchange_candle_ts_ms"], keep="last", inplace=True)
        return df_combined.sort_values(by="exchange_candle_ts_ms").reset_index(drop=True)

    def read_canonical(
        self,
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
        start_time_ms: Optional[int] = None,
        end_time_ms: Optional[int] = None,
    ) -> pd.DataFrame:
        """Read canonical candles as pandas DataFrame with optional time range filter."""
        partition_dir = self.get_partition_dir("canonical", exchange, symbol, timeframe)
        if not partition_dir.exists():
            return pd.DataFrame()

        files = [
            f for f in partition_dir.glob("*.parquet")
            if not f.name.startswith(".") and ".tmp." not in f.name and f.name != "conflicts.parquet"
        ]
        if not files:
            return pd.DataFrame()

        dfs: List[pd.DataFrame] = []
        for file_path in files:
            if file_path.stem.isdigit() and len(file_path.stem) == 4:
                file_year = int(file_path.stem)
                year_start = int(datetime(file_year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
                year_end = int(datetime(file_year + 1, 1, 1, tzinfo=timezone.utc).timestamp() * 1000) - 1
                if start_time_ms is not None and year_end < start_time_ms:
                    continue
                if end_time_ms is not None and year_start > end_time_ms:
                    continue

            df = pd.read_parquet(file_path)
            if not df.empty:
                if start_time_ms is not None:
                    df = df[df["open_time_ms"] >= start_time_ms]
                if end_time_ms is not None:
                    df = df[df["open_time_ms"] <= end_time_ms]
                if not df.empty:
                    dfs.append(df)

        if not dfs:
            return pd.DataFrame()

        df_combined = pd.concat(dfs, ignore_index=True)
        df_combined.drop_duplicates(subset=["open_time_ms"], keep="last", inplace=True)
        return df_combined.sort_values(by="open_time_ms").reset_index(drop=True)

    def read_features(
        self,
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
        start_time_ms: Optional[int] = None,
        end_time_ms: Optional[int] = None,
    ) -> pd.DataFrame:
        """Read engineered features as pandas DataFrame with optional time range filter."""
        partition_dir = self.get_partition_dir("features", exchange, symbol, timeframe)
        if not partition_dir.exists():
            return pd.DataFrame()

        files = [
            f for f in partition_dir.glob("*.parquet")
            if not f.name.startswith(".") and ".tmp." not in f.name and f.name != "conflicts.parquet"
        ]
        if not files:
            return pd.DataFrame()

        dfs: List[pd.DataFrame] = []
        for file_path in files:
            if file_path.stem.isdigit() and len(file_path.stem) == 4:
                file_year = int(file_path.stem)
                year_start = int(datetime(file_year, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
                year_end = int(datetime(file_year + 1, 1, 1, tzinfo=timezone.utc).timestamp() * 1000) - 1
                if start_time_ms is not None and year_end < start_time_ms:
                    continue
                if end_time_ms is not None and year_start > end_time_ms:
                    continue

            df = pd.read_parquet(file_path)
            if not df.empty:
                if start_time_ms is not None:
                    df = df[df["open_time_ms"] >= start_time_ms]
                if end_time_ms is not None:
                    df = df[df["open_time_ms"] <= end_time_ms]
                if not df.empty:
                    dfs.append(df)

        if not dfs:
            return pd.DataFrame()

        df_combined = pd.concat(dfs, ignore_index=True)
        df_combined.drop_duplicates(subset=["open_time_ms"], keep="last", inplace=True)
        return df_combined.sort_values(by="open_time_ms").reset_index(drop=True)

    def _atomic_write_parquet(self, table: pa.Table, target_path: Path) -> None:
        """Atomically write PyArrow Table using unique temporary file and atomic replace."""
        target_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = target_path.with_name(f"{target_path.stem}.tmp.{os.getpid()}.{time.time_ns()}.parquet")
        try:
            pq.write_table(table, temp_path, compression="snappy")
            temp_path.replace(target_path)
        except Exception:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            raise
