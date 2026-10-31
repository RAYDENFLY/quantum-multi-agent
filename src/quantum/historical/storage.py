"""Columnar Parquet storage manager for raw, canonical, and feature datasets."""

import hashlib
from pathlib import Path
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

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir).resolve()
        self.raw_dir = self.base_dir / "raw"
        self.canonical_dir = self.base_dir / "canonical"
        self.features_dir = self.base_dir / "features"

        for directory in [self.raw_dir, self.canonical_dir, self.features_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def get_partition_path(
        self,
        layer: str,
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
        year: Optional[int] = None,
    ) -> Path:
        """Resolve partitioned directory and file path."""
        ex_str = exchange.value if hasattr(exchange, "value") else str(exchange)
        sym_str = symbol.upper()
        tf_str = timeframe.value if hasattr(timeframe, "value") else str(timeframe)

        partition_dir = self.base_dir / layer / f"exchange={ex_str}" / f"symbol={sym_str}" / f"timeframe={tf_str}"
        partition_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{year}.parquet" if year else "data.parquet"
        return partition_dir / filename

    def write_raw_candles(
        self,
        candles: List[RawHistoricalCandle],
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
    ) -> Path:
        """Write raw candles to Parquet partition, appending and deduplicating."""
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
        target_path = self.get_partition_path("raw", exchange, symbol, timeframe)

        if target_path.exists():
            df_existing = pd.read_parquet(target_path)
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
        target_path = self.get_partition_path("canonical", exchange, symbol, timeframe)

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

    def write_features(
        self,
        df_features: pd.DataFrame,
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
    ) -> Path:
        """Write feature DataFrame to Parquet with atomic swap."""
        if df_features.empty:
            raise ValueError("Feature DataFrame is empty")

        if "open_time_ms" not in df_features.columns:
            raise ValueError("Feature DataFrame must contain open_time_ms as reference timestamp")

        target_path = self.get_partition_path("features", exchange, symbol, timeframe)
        df_sorted = df_features.drop_duplicates(subset=["open_time_ms"], keep="last").sort_values(by="open_time_ms")
        table = pa.Table.from_pandas(df_sorted, preserve_index=False)
        self._atomic_write_parquet(table, target_path)
        logger.info("Wrote %d feature rows to %s", len(table), target_path)
        return target_path

    def read_raw(
        self,
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
        start_time_ms: Optional[int] = None,
        end_time_ms: Optional[int] = None,
    ) -> pd.DataFrame:
        """Read raw candles as pandas DataFrame with optional time range filter."""
        target_path = self.get_partition_path("raw", exchange, symbol, timeframe)
        if not target_path.exists():
            return pd.DataFrame()

        df = pd.read_parquet(target_path)
        if df.empty:
            return df

        if start_time_ms is not None:
            df = df[df["exchange_candle_ts_ms"] >= start_time_ms]
        if end_time_ms is not None:
            df = df[df["exchange_candle_ts_ms"] <= end_time_ms]

        return df.sort_values(by="exchange_candle_ts_ms").reset_index(drop=True)

    def read_canonical(
        self,
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
        start_time_ms: Optional[int] = None,
        end_time_ms: Optional[int] = None,
    ) -> pd.DataFrame:
        """Read canonical candles as pandas DataFrame with optional time range filter."""
        target_path = self.get_partition_path("canonical", exchange, symbol, timeframe)
        if not target_path.exists():
            return pd.DataFrame()

        df = pd.read_parquet(target_path)
        if df.empty:
            return df

        if start_time_ms is not None:
            df = df[df["open_time_ms"] >= start_time_ms]
        if end_time_ms is not None:
            df = df[df["open_time_ms"] <= end_time_ms]

        return df.sort_values(by="open_time_ms").reset_index(drop=True)

    def read_features(
        self,
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
        start_time_ms: Optional[int] = None,
        end_time_ms: Optional[int] = None,
    ) -> pd.DataFrame:
        """Read engineered features as pandas DataFrame with optional time range filter."""
        target_path = self.get_partition_path("features", exchange, symbol, timeframe)
        if not target_path.exists():
            return pd.DataFrame()

        df = pd.read_parquet(target_path)
        if df.empty:
            return df

        if start_time_ms is not None:
            df = df[df["open_time_ms"] >= start_time_ms]
        if end_time_ms is not None:
            df = df[df["open_time_ms"] <= end_time_ms]

        return df.sort_values(by="open_time_ms").reset_index(drop=True)

    def _atomic_write_parquet(self, table: pa.Table, target_path: Path) -> None:
        """Atomically write PyArrow Table using a temporary file and replace."""
        temp_path = target_path.with_suffix(".tmp.parquet")
        pq.write_table(table, temp_path, compression="snappy")
        temp_path.replace(target_path)
