"""Historical candlestick downloader with pagination, rate limiting, and resume."""

import asyncio
import json
import random
import time
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple
import pandas as pd

from quantum.core.logging import get_logger
from quantum.domain.enums import Exchange, Timeframe
from quantum.exchanges.aster.adapter import TIMEFRAME_TO_ASTER, AsterExchangeAdapter
from quantum.exchanges.base import BaseExchangeAdapter
from quantum.exchanges.bybit.adapter import TIMEFRAME_TO_BYBIT, BybitExchangeAdapter
from quantum.historical.models import (
    CanonicalCandle,
    CollectionJobStatus,
    DataQualityReport,
    DatasetManifest,
    HistoricalCollectionCheckpoint,
    HistoricalCollectionJob,
    RawHistoricalCandle,
    ValidationStatus,
)
from quantum.historical.storage import ParquetStorageManager, compute_file_sha256
from quantum.historical.validator import TIMEFRAME_INTERVAL_MS, DataQualityValidator
from quantum.storage.historical_repository import HistoricalRepository

logger = get_logger("historical.downloader")


class PaginationManager:
    """Manages pagination state and cursor advancement for historical chunking."""

    def __init__(
        self,
        requested_start_ms: int,
        requested_end_ms: int,
        timeframe: Timeframe,
        direction: str = "BACKWARD",
        checkpoint: Optional[HistoricalCollectionCheckpoint] = None,
    ) -> None:
        self.requested_start_ms = requested_start_ms
        self.requested_end_ms = requested_end_ms
        self.timeframe = timeframe
        self.direction = direction.upper()
        self.interval_ms = TIMEFRAME_INTERVAL_MS.get(timeframe, 300_000)

        self.is_exhausted = False
        self.total_pages_fetched = 0
        self.earliest_seen_ms = requested_end_ms
        self.latest_seen_ms = requested_start_ms

        if checkpoint:
            self.cursor_ms = checkpoint.last_fetched_open_time_ms
            self.earliest_seen_ms = checkpoint.earliest_open_time_ms
            self.latest_seen_ms = checkpoint.latest_open_time_ms
            self.is_exhausted = checkpoint.is_exhausted
        else:
            self.cursor_ms = requested_end_ms if self.direction == "BACKWARD" else requested_start_ms

    def get_next_request_params(self, limit: int = 1000) -> Optional[Tuple[Optional[int], Optional[int]]]:
        """Return (before_ms, after_ms) for the next exchange request, or None if exhausted."""
        if self.is_exhausted:
            return None

        if self.direction == "BACKWARD":
            if self.cursor_ms < self.requested_start_ms:
                self.is_exhausted = True
                return None
            return (self.cursor_ms, None)
        else:
            if self.cursor_ms > self.requested_end_ms:
                self.is_exhausted = True
                return None
            return (None, self.cursor_ms)

    def record_page_results(self, candle_count: int, earliest_bar_ms: int, latest_bar_ms: int, limit: int = 1000) -> None:
        """Update pagination cursor based on returned page results."""
        self.total_pages_fetched += 1

        if candle_count == 0:
            self.is_exhausted = True
            logger.info("Pagination reached empty response. Exhausted.")
            return

        self.earliest_seen_ms = min(self.earliest_seen_ms, earliest_bar_ms)
        self.latest_seen_ms = max(self.latest_seen_ms, latest_bar_ms)

        if self.direction == "BACKWARD":
            # Advance cursor to before the earliest returned candle
            new_cursor = earliest_bar_ms - 1
            if new_cursor >= self.cursor_ms:
                logger.warning("Pagination loop detected in BACKWARD direction for %s. Exhausting.", self.timeframe.value)
                self.is_exhausted = True
                return
            self.cursor_ms = new_cursor
            if self.cursor_ms < self.requested_start_ms:
                self.is_exhausted = True
            elif candle_count < limit:
                # Exchange returned fewer bars than requested limit: reached beginning of listing
                self.is_exhausted = True
        else:
            # Forward pagination
            new_cursor = latest_bar_ms + self.interval_ms
            if new_cursor <= self.cursor_ms:
                logger.warning("Pagination loop detected in FORWARD direction for %s. Exhausting.", self.timeframe.value)
                self.is_exhausted = True
                return
            self.cursor_ms = new_cursor
            if self.cursor_ms > self.requested_end_ms:
                self.is_exhausted = True
            elif candle_count < limit:
                self.is_exhausted = True

        if self.total_pages_fetched >= 10000:
            logger.warning("Pagination reached safety ceiling (10,000 pages). Exhausting.")
            self.is_exhausted = True


class HistoricalCandleDownloader:
    """Orchestrates historical downloading, pagination, rate limiting, and resume."""

    def __init__(
        self,
        storage_manager: ParquetStorageManager,
        repository: Optional[HistoricalRepository] = None,
        validator: Optional[DataQualityValidator] = None,
    ) -> None:
        self.storage = storage_manager
        self.repo = repository
        self.validator = validator or DataQualityValidator()
        self._cancel_requested = False

    def request_cancellation(self) -> None:
        """Signal download cancellation at next page boundary."""
        self._cancel_requested = True

    async def download(
        self,
        job: HistoricalCollectionJob,
        adapter: BaseExchangeAdapter,
        page_limit: int = 1000,
        max_retries: int = 4,
        backoff_base_s: float = 0.5,
        progress_callback: Optional[Callable[[int, int], Coroutine[Any, Any, None]]] = None,
    ) -> Tuple[List[CanonicalCandle], DataQualityReport]:
        """Download historical candles with rate limiting, retries, checkpointing, and validation."""
        self._cancel_requested = False
        job.status = CollectionJobStatus.RUNNING
        job.updated_at_ms = int(time.time() * 1000)
        if self.repo:
            await self.repo.save_job(job)

        # Check for resume checkpoint
        existing_checkpoint: Optional[HistoricalCollectionCheckpoint] = None
        if self.repo:
            existing_checkpoint = await self.repo.get_checkpoint(job.job_id)

        paginator = PaginationManager(
            requested_start_ms=job.requested_start_ms,
            requested_end_ms=job.requested_end_ms,
            timeframe=job.timeframe,
            direction="BACKWARD",
            checkpoint=existing_checkpoint,
        )

        total_downloaded = 0
        raw_buffer: List[RawHistoricalCandle] = []
        canonical_buffer: List[CanonicalCandle] = []

        try:
            while not paginator.is_exhausted and not self._cancel_requested:
                params = paginator.get_next_request_params(limit=page_limit)
                if not params:
                    break

                before_ms, after_ms = params

                # Fetch page with retries and rate limiting
                raw_records, can_records = await self._fetch_page_with_retry(
                    adapter=adapter,
                    symbol=job.symbol,
                    timeframe=job.timeframe,
                    limit=page_limit,
                    before_ms=before_ms,
                    after_ms=after_ms,
                    max_retries=max_retries,
                    backoff_base_s=backoff_base_s,
                    run_id=job.job_id,
                )

                if can_records:
                    raw_buffer.extend(raw_records)
                    canonical_buffer.extend(can_records)
                    total_downloaded += len(can_records)

                    earliest_ms = min(c.open_time_ms for c in can_records)
                    latest_ms = max(c.open_time_ms for c in can_records)
                    paginator.record_page_results(len(can_records), earliest_ms, latest_ms, limit=page_limit)

                    # Periodically flush chunks to Parquet and checkpoint (every 2,000 candles)
                    if len(canonical_buffer) >= 2000 or paginator.is_exhausted:
                        try:
                            self.storage.write_raw_candles(raw_buffer, job.exchange, job.symbol, job.timeframe)
                            self.storage.write_canonical_candles(canonical_buffer, job.exchange, job.symbol, job.timeframe)
                        except Exception as write_err:
                            logger.error("Failed to persist Parquet chunk for job %s: %s", job.job_id, write_err)
                            raise

                        raw_buffer.clear()
                        canonical_buffer.clear()

                        if self.repo:
                            checkpoint = HistoricalCollectionCheckpoint(
                                checkpoint_id=f"CHK-{job.job_id}",
                                job_id=job.job_id,
                                exchange=job.exchange,
                                symbol=job.symbol,
                                timeframe=job.timeframe,
                                direction=paginator.direction,
                                last_fetched_open_time_ms=paginator.cursor_ms,
                                last_page_candle_count=len(can_records),
                                earliest_open_time_ms=paginator.earliest_seen_ms,
                                latest_open_time_ms=paginator.latest_seen_ms,
                                is_exhausted=paginator.is_exhausted,
                            )
                            await self.repo.save_checkpoint(checkpoint)
                            job.total_candles_fetched = total_downloaded
                            job.checkpoint_ms = paginator.cursor_ms
                            job.actual_start_ms = paginator.earliest_seen_ms
                            job.actual_end_ms = paginator.latest_seen_ms
                            await self.repo.save_job(job)

                    if progress_callback:
                        await progress_callback(total_downloaded, paginator.cursor_ms)
                else:
                    paginator.record_page_results(0, 0, 0, limit=page_limit)

            # Flush any remaining buffer
            if canonical_buffer:
                try:
                    self.storage.write_raw_candles(raw_buffer, job.exchange, job.symbol, job.timeframe)
                    self.storage.write_canonical_candles(canonical_buffer, job.exchange, job.symbol, job.timeframe)
                except Exception as flush_err:
                    logger.error("Failed to flush final Parquet chunk: %s", flush_err)
                    raise
                raw_buffer.clear()
                canonical_buffer.clear()

            if self._cancel_requested:
                job.status = CollectionJobStatus.CANCELLED
                job.error_message = "Download cancelled by user request"
                if self.repo:
                    await self.repo.save_job(job)
                logger.warning("Historical download cancelled for %s %s", job.symbol, job.timeframe.value)
                return [], self._generate_cancelled_report(job)

            # Load canonical dataset for full quality validation
            df_canonical = self.storage.read_canonical(
                job.exchange,
                job.symbol,
                job.timeframe,
                start_time_ms=job.requested_start_ms,
                end_time_ms=job.requested_end_ms,
            )

            all_candles: List[CanonicalCandle] = []
            for _, row in df_canonical.iterrows():
                all_candles.append(
                    CanonicalCandle(
                        exchange=job.exchange,
                        symbol=job.symbol,
                        market_type="PERPETUAL",
                        timeframe=job.timeframe,
                        open_time_ms=int(row["open_time_ms"]),
                        close_time_ms=int(row["close_time_ms"]),
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=float(row["volume"]),
                        quote_volume=float(row["quote_volume"]) if pd.notna(row["quote_volume"]) else None,
                        trade_count=int(row["trade_count"]) if pd.notna(row["trade_count"]) else None,
                        taker_buy_volume=float(row["taker_buy_volume"]) if pd.notna(row["taker_buy_volume"]) else None,
                        taker_buy_quote_volume=float(row["taker_buy_quote_volume"]) if pd.notna(row["taker_buy_quote_volume"]) else None,
                        ingestion_time_ms=int(row["ingestion_time_ms"]),
                        source_run_id=str(row["source_run_id"]),
                    )
                )

            # Execute data quality audit
            valid_candles, quality_report = self.validator.validate_dataset(
                candles=all_candles,
                exchange=job.exchange,
                symbol=job.symbol,
                timeframe=job.timeframe,
                requested_start_ms=job.requested_start_ms,
                requested_end_ms=job.requested_end_ms,
                run_id=job.job_id,
            )

            # Write validated canonical candles
            if valid_candles:
                canon_path = self.storage.write_canonical_candles(
                    valid_candles, job.exchange, job.symbol, job.timeframe
                )
                raw_path = self.storage.get_partition_path("raw", job.exchange, job.symbol, job.timeframe)
                sha256_hash = compute_file_sha256(canon_path)

                manifest = DatasetManifest(
                    manifest_id=f"MAN-{job.exchange.value}-{job.symbol}-{job.timeframe.value}-{int(time.time()*1000)}",
                    dataset_name=f"{job.symbol}_{job.timeframe.value}_dataset",
                    dataset_version=self.validator.dataset_version,
                    feature_version=self.validator.feature_version,
                    exchange=job.exchange,
                    symbol=job.symbol,
                    timeframe=job.timeframe,
                    start_time_ms=quality_report.actual_start_ms,
                    end_time_ms=quality_report.actual_end_ms,
                    candle_count=len(valid_candles),
                    raw_parquet_path=str(raw_path),
                    canonical_parquet_path=str(canon_path),
                    file_sha256=sha256_hash,
                    metadata={"coverage_pct": quality_report.coverage_pct, "validation_status": quality_report.validation_status.value},
                )
                if self.repo:
                    await self.repo.save_manifest(manifest)

            # Persist quality report and update job outcome
            job.status = CollectionJobStatus.COMPLETED
            job.total_candles_fetched = len(valid_candles)
            job.actual_start_ms = quality_report.actual_start_ms
            job.actual_end_ms = quality_report.actual_end_ms

            if self.repo:
                await self.repo.save_quality_report(quality_report)
                await self.repo.save_job(job)
                # Remove checkpoint on success
                await self.repo.delete_checkpoint(f"CHK-{job.job_id}")

            return valid_candles, quality_report

        except Exception as err:
            logger.error("Download failed for job %s: %s", job.job_id, err, exc_info=True)
            job.status = CollectionJobStatus.FAILED
            job.error_message = str(err)
            if self.repo:
                await self.repo.save_job(job)
            raise

    async def _fetch_page_with_retry(
        self,
        adapter: BaseExchangeAdapter,
        symbol: str,
        timeframe: Timeframe,
        limit: int,
        before_ms: Optional[int],
        after_ms: Optional[int],
        max_retries: int,
        backoff_base_s: float,
        run_id: str,
    ) -> Tuple[List[RawHistoricalCandle], List[CanonicalCandle]]:
        """Execute rate-limited request with exponential backoff and jitter."""
        for attempt in range(max_retries):
            try:
                await adapter.rate_limiter.acquire(1.0)

                # Query exchange-specific REST client directly to retain raw response fields
                if hasattr(adapter, "rest") and hasattr(adapter.rest, "_request"):
                    if adapter.exchange == Exchange.ASTER:
                        interval = TIMEFRAME_TO_ASTER.get(timeframe, "1m")
                        params: Dict[str, Any] = {"symbol": symbol.upper(), "interval": interval, "limit": min(limit, 1000)}
                        if before_ms:
                            params["endTime"] = before_ms
                        if after_ms:
                            params["startTime"] = after_ms
                        raw_response = await adapter.rest._request("/fapi/v1/klines", params=params)
                        return self._parse_aster_page(raw_response, symbol, timeframe, run_id)

                    elif adapter.exchange == Exchange.BYBIT:
                        interval = TIMEFRAME_TO_BYBIT.get(timeframe, "1")
                        params = {"category": "linear", "symbol": symbol.upper(), "interval": interval, "limit": min(limit, 1000)}
                        if before_ms:
                            params["end"] = before_ms
                        if after_ms:
                            params["start"] = after_ms
                        result = await adapter.rest._request("/v5/market/kline", params=params)
                        raw_response = result.get("list", []) if isinstance(result, dict) else result
                        return self._parse_bybit_page(raw_response, symbol, timeframe, run_id)

                # Generic fallback using adapter fetch_klines
                norm_candles = await adapter.fetch_klines(symbol, timeframe, limit=limit, before_ms=before_ms)
                return self._fallback_page(norm_candles, adapter.exchange, symbol, timeframe, run_id)

            except Exception as err:
                if attempt == max_retries - 1:
                    logger.error("Failed to fetch klines page on %s after %d retries: %s", symbol, max_retries, err)
                    raise
                backoff = (backoff_base_s * (2 ** attempt)) + random.uniform(0.05, 0.25)
                logger.warning("Retryable error on %s %s (attempt %d/%d): %s. Backoff %.2fs", symbol, timeframe.value, attempt + 1, max_retries, err, backoff)
                await asyncio.sleep(backoff)

        return [], []

    def _parse_aster_page(
        self,
        raw_list: List[List[Any]],
        symbol: str,
        timeframe: Timeframe,
        run_id: str,
    ) -> Tuple[List[RawHistoricalCandle], List[CanonicalCandle]]:
        """Convert AsterDEX raw kline rows into RawHistoricalCandle and CanonicalCandle lists."""
        raw_candles: List[RawHistoricalCandle] = []
        canonical_candles: List[CanonicalCandle] = []

        now_ms = int(time.time() * 1000)
        for row in raw_list:
            if len(row) < 7:
                continue

            open_ts = int(row[0])
            close_ts = int(row[6])
            o = float(row[1])
            h = float(row[2])
            l = float(row[3])
            c = float(row[4])
            vol = float(row[5])
            turnover = float(row[7]) if len(row) > 7 else None
            trades = int(row[8]) if len(row) > 8 and row[8] is not None else None
            taker_base = float(row[9]) if len(row) > 9 and row[9] is not None else None
            taker_quote = float(row[10]) if len(row) > 10 and row[10] is not None else None

            raw_candles.append(
                RawHistoricalCandle(
                    exchange=Exchange.ASTER,
                    symbol=symbol.upper(),
                    contract_type="PERPETUAL",
                    timeframe=timeframe,
                    exchange_candle_ts_ms=open_ts,
                    raw_open=str(row[1]),
                    raw_high=str(row[2]),
                    raw_low=str(row[3]),
                    raw_close=str(row[4]),
                    raw_volume=str(row[5]),
                    raw_turnover=str(row[7]) if len(row) > 7 else None,
                    raw_trades=str(row[8]) if len(row) > 8 else None,
                    raw_taker_buy_volume=str(row[9]) if len(row) > 9 else None,
                    raw_taker_buy_turnover=str(row[10]) if len(row) > 10 else None,
                    raw_payload_json=json.dumps(row),
                    retrieval_timestamp_ms=now_ms,
                    source_endpoint="/fapi/v1/klines",
                    collection_run_id=run_id,
                )
            )

            canonical_candles.append(
                CanonicalCandle(
                    exchange=Exchange.ASTER,
                    symbol=symbol.upper(),
                    market_type="PERPETUAL",
                    timeframe=timeframe,
                    open_time_ms=open_ts,
                    close_time_ms=close_ts,
                    open=o,
                    high=h,
                    low=l,
                    close=c,
                    volume=vol,
                    quote_volume=turnover,
                    trade_count=trades,
                    taker_buy_volume=taker_base,
                    taker_buy_quote_volume=taker_quote,
                    ingestion_time_ms=now_ms,
                    source_run_id=run_id,
                )
            )

        return raw_candles, canonical_candles

    def _parse_bybit_page(
        self,
        raw_list: List[List[str]],
        symbol: str,
        timeframe: Timeframe,
        run_id: str,
    ) -> Tuple[List[RawHistoricalCandle], List[CanonicalCandle]]:
        """Convert Bybit raw kline rows into RawHistoricalCandle and CanonicalCandle lists."""
        raw_candles: List[RawHistoricalCandle] = []
        canonical_candles: List[CanonicalCandle] = []

        interval_ms = TIMEFRAME_INTERVAL_MS.get(timeframe, 300_000)
        now_ms = int(time.time() * 1000)

        for row in raw_list:
            if len(row) < 7:
                continue

            open_ts = int(row[0])
            close_ts = open_ts + interval_ms - 1
            o = float(row[1])
            h = float(row[2])
            l = float(row[3])
            c = float(row[4])
            vol = float(row[5])
            turnover = float(row[6])

            raw_candles.append(
                RawHistoricalCandle(
                    exchange=Exchange.BYBIT,
                    symbol=symbol.upper(),
                    contract_type="LINEAR_PERPETUAL",
                    timeframe=timeframe,
                    exchange_candle_ts_ms=open_ts,
                    raw_open=str(row[1]),
                    raw_high=str(row[2]),
                    raw_low=str(row[3]),
                    raw_close=str(row[4]),
                    raw_volume=str(row[5]),
                    raw_turnover=str(row[6]),
                    raw_trades=None,
                    raw_taker_buy_volume=None,
                    raw_taker_buy_turnover=None,
                    raw_payload_json=json.dumps(row),
                    retrieval_timestamp_ms=now_ms,
                    source_endpoint="/v5/market/kline",
                    collection_run_id=run_id,
                )
            )

            canonical_candles.append(
                CanonicalCandle(
                    exchange=Exchange.BYBIT,
                    symbol=symbol.upper(),
                    market_type="PERPETUAL",
                    timeframe=timeframe,
                    open_time_ms=open_ts,
                    close_time_ms=close_ts,
                    open=o,
                    high=h,
                    low=l,
                    close=c,
                    volume=vol,
                    quote_volume=turnover,
                    trade_count=None,
                    taker_buy_volume=None,
                    taker_buy_quote_volume=None,
                    ingestion_time_ms=now_ms,
                    source_run_id=run_id,
                )
            )

        return raw_candles, canonical_candles

    def _fallback_page(
        self,
        norm_candles: Any,
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
        run_id: str,
    ) -> Tuple[List[RawHistoricalCandle], List[CanonicalCandle]]:
        """Fallback normalization from NormalizedCandle objects."""
        now_ms = int(time.time() * 1000)
        raw_list: List[RawHistoricalCandle] = []
        can_list: List[CanonicalCandle] = []

        for c in norm_candles:
            raw_list.append(
                RawHistoricalCandle(
                    exchange=exchange,
                    symbol=symbol.upper(),
                    contract_type="PERPETUAL",
                    timeframe=timeframe,
                    exchange_candle_ts_ms=c.open_time_ms,
                    raw_open=str(c.open_price),
                    raw_high=str(c.high_price),
                    raw_low=str(c.low_price),
                    raw_close=str(c.close_price),
                    raw_volume=str(c.volume),
                    raw_turnover=str(c.turnover_usdt),
                    retrieval_timestamp_ms=now_ms,
                    source_endpoint="generic_fetch_klines",
                    collection_run_id=run_id,
                )
            )
            can_list.append(
                CanonicalCandle(
                    exchange=exchange,
                    symbol=symbol.upper(),
                    market_type="PERPETUAL",
                    timeframe=timeframe,
                    open_time_ms=c.open_time_ms,
                    close_time_ms=c.close_time_ms,
                    open=c.open_price,
                    high=c.high_price,
                    low=c.low_price,
                    close=c.close_price,
                    volume=c.volume,
                    quote_volume=c.turnover_usdt,
                    trade_count=c.trades_count if c.trades_count > 0 else None,
                    ingestion_time_ms=now_ms,
                    source_run_id=run_id,
                )
            )

        return raw_list, can_list

    def _generate_cancelled_report(self, job: HistoricalCollectionJob) -> DataQualityReport:
        """Produce placeholder report for cancelled downloads."""
        return DataQualityReport(
            report_id=f"DQR-CANCELLED-{job.job_id}",
            run_id=job.job_id,
            exchange=job.exchange,
            symbol=job.symbol,
            timeframe=job.timeframe,
            requested_start_ms=job.requested_start_ms,
            requested_end_ms=job.requested_end_ms,
            actual_start_ms=job.requested_start_ms,
            actual_end_ms=job.requested_end_ms,
            expected_count=0,
            observed_count=0,
            missing_count=0,
            duplicate_count=0,
            conflicting_duplicate_count=0,
            invalid_ohlc_count=0,
            incomplete_candle_count=0,
            coverage_pct=0.0,
            validation_status=ValidationStatus.FAIL,
            feature_version=self.validator.feature_version,
            dataset_version=self.validator.dataset_version,
            details={"cancellation": True},
        )
