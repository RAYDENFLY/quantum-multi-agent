"""Data contracts for historical collection, raw/canonical layers, manifests, and quality audit."""

from enum import Enum
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

from quantum.domain.enums import Exchange, Timeframe


class CollectionJobStatus(str, Enum):
    """Lifecycle states for historical download jobs."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PAUSED = "PAUSED"


class ValidationStatus(str, Enum):
    """Audit outcome for historical dataset validation."""
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    FAIL = "FAIL"
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"


class RawHistoricalCandle(BaseModel):
    """Raw layer candle capturing original exchange payload values with audit metadata."""
    model_config = ConfigDict(frozen=True)

    exchange: Exchange
    symbol: str
    contract_type: str = "PERPETUAL"
    timeframe: Timeframe
    exchange_candle_ts_ms: int
    raw_open: str
    raw_high: str
    raw_low: str
    raw_close: str
    raw_volume: str
    raw_turnover: Optional[str] = None
    raw_trades: Optional[str] = None
    raw_taker_buy_volume: Optional[str] = None
    raw_taker_buy_turnover: Optional[str] = None
    raw_payload_json: Optional[str] = None
    retrieval_timestamp_ms: int = Field(default_factory=lambda: int(time.time() * 1000))
    source_endpoint: str
    collection_run_id: str


class CanonicalCandle(BaseModel):
    """Canonical normalized candle schema.
    
    Field semantics:
    - volume: Base asset volume (e.g. BTC in BTCUSDT).
    - quote_volume: Quote asset volume in USDT turnover.
    - trade_count: Number of trades executed during candle, or None if unprovided.
    - taker_buy_volume: Base asset volume bought by aggressive takers, or None if unprovided.
    - taker_buy_quote_volume: Quote USDT volume bought by aggressive takers, or None if unprovided.
    - All timestamps are UTC in milliseconds.
    """
    model_config = ConfigDict(validate_assignment=True)

    exchange: Exchange
    symbol: str
    market_type: str = "PERPETUAL"
    timeframe: Timeframe
    open_time_ms: int
    close_time_ms: int
    open: float = Field(gt=0.0)
    high: float = Field(gt=0.0)
    low: float = Field(gt=0.0)
    close: float = Field(gt=0.0)
    volume: float = Field(ge=0.0)
    quote_volume: Optional[float] = Field(default=None, ge=0.0)
    trade_count: Optional[int] = Field(default=None, ge=0)
    taker_buy_volume: Optional[float] = Field(default=None, ge=0.0)
    taker_buy_quote_volume: Optional[float] = Field(default=None, ge=0.0)
    ingestion_time_ms: int = Field(default_factory=lambda: int(time.time() * 1000))
    source_run_id: str

    @model_validator(mode="after")
    def validate_ohlc_invariants(self) -> "CanonicalCandle":
        """Enforce mathematical OHLC boundaries."""
        if self.high < max(self.open, self.close):
            raise ValueError(f"High {self.high} cannot be less than open {self.open} or close {self.close}")
        if self.low > min(self.open, self.close):
            raise ValueError(f"Low {self.low} cannot be greater than open {self.open} or close {self.close}")
        if self.close_time_ms <= self.open_time_ms:
            raise ValueError(f"Close time {self.close_time_ms} must be strictly greater than open time {self.open_time_ms}")
        return self


class HistoricalCollectionJob(BaseModel):
    """Job definition tracking an asynchronous historical download."""
    model_config = ConfigDict(validate_assignment=True)

    job_id: str
    exchange: Exchange
    symbol: str
    timeframe: Timeframe
    requested_start_ms: int
    requested_end_ms: int
    actual_start_ms: Optional[int] = None
    actual_end_ms: Optional[int] = None
    status: CollectionJobStatus = CollectionJobStatus.PENDING
    total_candles_fetched: int = 0
    checkpoint_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at_ms: int = Field(default_factory=lambda: int(time.time() * 1000))
    updated_at_ms: int = Field(default_factory=lambda: int(time.time() * 1000))


class HistoricalCollectionCheckpoint(BaseModel):
    """Progress checkpoint enabling safe resumption of interrupted downloads."""
    model_config = ConfigDict(validate_assignment=True)

    checkpoint_id: str
    job_id: str
    exchange: Exchange
    symbol: str
    timeframe: Timeframe
    direction: str = "BACKWARD"
    last_fetched_open_time_ms: int
    last_page_candle_count: int
    earliest_open_time_ms: int
    latest_open_time_ms: int
    is_exhausted: bool = False
    updated_at_ms: int = Field(default_factory=lambda: int(time.time() * 1000))


class DatasetManifest(BaseModel):
    """Cryptographic manifest guaranteeing dataset reproducibility and versioning."""
    model_config = ConfigDict(validate_assignment=True)

    manifest_id: str
    dataset_name: str
    dataset_version: str
    feature_version: str
    exchange: Exchange
    symbol: str
    timeframe: Timeframe
    start_time_ms: int
    end_time_ms: int
    candle_count: int
    raw_parquet_path: str
    canonical_parquet_path: str
    feature_parquet_path: Optional[str] = None
    file_sha256: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at_ms: int = Field(default_factory=lambda: int(time.time() * 1000))


class DataQualityReport(BaseModel):
    """Audit report quantifying historical dataset completeness and integrity."""
    model_config = ConfigDict(validate_assignment=True)

    report_id: str
    run_id: str
    exchange: Exchange
    symbol: str
    timeframe: Timeframe
    requested_start_ms: int
    requested_end_ms: int
    actual_start_ms: int
    actual_end_ms: int
    expected_count: int
    observed_count: int
    missing_count: int
    duplicate_count: int
    conflicting_duplicate_count: int
    invalid_ohlc_count: int
    incomplete_candle_count: int
    coverage_pct: float
    validation_status: ValidationStatus
    feature_version: str
    dataset_version: str
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at_ms: int = Field(default_factory=lambda: int(time.time() * 1000))
