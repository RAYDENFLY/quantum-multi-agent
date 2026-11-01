"""Historical data service coordinating discovery, downloads, validation, and features."""

import asyncio
from pathlib import Path
import time
from typing import Any, Callable, Coroutine, Dict, List, Optional
import aiosqlite
import pandas as pd

from quantum.core.logging import get_logger
from quantum.domain.enums import Exchange, Timeframe
from quantum.exchanges.base import BaseExchangeAdapter
from quantum.exchanges.models import InstrumentInfo
from quantum.features.engine import FeatureEngine
from quantum.features.multitimeframe import MultiTimeframeJoiner
from quantum.historical.discovery import HistoricalInstrumentDiscovery
from quantum.historical.downloader import HistoricalCandleDownloader
from quantum.historical.models import (
    CollectionJobStatus,
    DataQualityReport,
    DatasetManifest,
    HistoricalCollectionJob,
)
from quantum.historical.storage import ParquetStorageManager
from quantum.historical.validator import TIMEFRAME_INTERVAL_MS, DataQualityValidator
from quantum.storage.historical_repository import HistoricalRepository

logger = get_logger("historical.service")


class HistoricalDataService:
    """High-level service coordinating Phase 4 historical pipelines and feature stores."""

    def __init__(
        self,
        storage_dir: Path,
        db_conn: Optional[aiosqlite.Connection] = None,
        feature_version: str = "FEATURE_V1",
        dataset_version: str = "DATASET_V1",
    ) -> None:
        self.storage = ParquetStorageManager(storage_dir)
        self.repo = HistoricalRepository(db_conn) if db_conn else None
        self.validator = DataQualityValidator(feature_version=feature_version, dataset_version=dataset_version)
        self.discovery = HistoricalInstrumentDiscovery(db_conn=db_conn)
        self.downloader = HistoricalCandleDownloader(
            storage_manager=self.storage,
            repository=self.repo,
            validator=self.validator,
        )
        self.feature_engine = FeatureEngine(schema_version=feature_version)
        self.mtf_joiner = MultiTimeframeJoiner()
        self._active_jobs: Dict[str, HistoricalCollectionJob] = {}
        self._active_tasks: Dict[str, asyncio.Task[Any]] = {}

    async def discover_perpetuals(self, adapter: BaseExchangeAdapter) -> List[InstrumentInfo]:
        """Discover eligible USDT perpetuals on an exchange."""
        return await self.discovery.discover_eligible_instruments(adapter, persist=True)

    async def start_collection(
        self,
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
        requested_start_ms: int,
        requested_end_ms: int,
        adapter: BaseExchangeAdapter,
        progress_callback: Optional[Callable[[int, int], Coroutine[Any, Any, None]]] = None,
        use_year_partitioning: bool = False,
        listing_start_time_ms: Optional[int] = None,
    ) -> HistoricalCollectionJob:
        """Create and execute an asynchronous historical download job."""
        job_id = f"JOB-{exchange.value}-{symbol.upper()}-{timeframe.value}-{int(time.time() * 1000)}"

        # Guard against duplicate concurrent jobs for same partition
        for active in self._active_jobs.values():
            if (
                active.exchange == exchange
                and active.symbol.upper() == symbol.upper()
                and active.timeframe == timeframe
                and active.status == CollectionJobStatus.RUNNING
            ):
                raise RuntimeError(
                    f"A collection job is already actively running for {exchange.value}:{symbol}:{timeframe.value}"
                )

        job = HistoricalCollectionJob(
            job_id=job_id,
            exchange=exchange,
            symbol=symbol.upper(),
            timeframe=timeframe,
            requested_start_ms=requested_start_ms,
            requested_end_ms=requested_end_ms,
            status=CollectionJobStatus.PENDING,
        )

        if self.repo:
            await self.repo.save_job(job)

        self._active_jobs[job_id] = job

        # Execute download in background task on current loop
        task = asyncio.create_task(
            self._execute_download_job(
                job,
                adapter,
                progress_callback,
                use_year_partitioning=use_year_partitioning,
                listing_start_time_ms=listing_start_time_ms,
            )
        )
        self._active_tasks[job_id] = task
        return job

    async def sync_incremental(
        self,
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
        adapter: BaseExchangeAdapter,
        max_lookback_days: int = 1095,
        current_time_ms: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int], Coroutine[Any, Any, None]]] = None,
        use_year_partitioning: bool = False,
    ) -> Optional[HistoricalCollectionJob]:
        """Perform REST historical backfill (up to 3 years) or incremental catch-up.

        Operational Policy:
        - Primary source is exchange-provided historical REST endpoints.
        - Initial run performs historical backfill targeting up to 3 years without
          requiring continuous real-time collection.
        - Subsequent runs perform fast incremental catch-up from the latest stored bar
          to the current time.
        - If the local dataset is already current, zero network requests are issued.
        """
        now_ms = current_time_ms or int(time.time() * 1000)
        interval_ms = TIMEFRAME_INTERVAL_MS.get(timeframe, 300_000)

        df_existing = self.storage.read_canonical(exchange, symbol, timeframe)
        if df_existing.empty:
            # Full historical backfill targeting up to 3 years
            requested_start_ms = now_ms - (max_lookback_days * 86_400_000)
            logger.info(
                "No prior canonical data for %s:%s:%s. Initiating full REST backfill (up to %d days).",
                exchange.value,
                symbol,
                timeframe.value,
                max_lookback_days,
            )
            return await self.start_collection(
                exchange=exchange,
                symbol=symbol,
                timeframe=timeframe,
                requested_start_ms=requested_start_ms,
                requested_end_ms=now_ms,
                adapter=adapter,
                progress_callback=progress_callback,
                use_year_partitioning=use_year_partitioning,
            )
        else:
            latest_open_time_ms = int(df_existing["open_time_ms"].max())
            delta_ms = now_ms - (latest_open_time_ms + interval_ms)
            if delta_ms < interval_ms:
                logger.info(
                    "Canonical data for %s:%s:%s is already up to date (latest bar at %d). Zero requests needed.",
                    exchange.value,
                    symbol,
                    timeframe.value,
                    latest_open_time_ms,
                )
                return None

            requested_start_ms = latest_open_time_ms + interval_ms
            logger.info(
                "Incremental catch-up for %s:%s:%s from %d to %d (lag: %.1f hours).",
                exchange.value,
                symbol,
                timeframe.value,
                requested_start_ms,
                now_ms,
                delta_ms / 3_600_000,
            )
            return await self.start_collection(
                exchange=exchange,
                symbol=symbol,
                timeframe=timeframe,
                requested_start_ms=requested_start_ms,
                requested_end_ms=now_ms,
                adapter=adapter,
                progress_callback=progress_callback,
                use_year_partitioning=use_year_partitioning,
            )

    async def _execute_download_job(
        self,
        job: HistoricalCollectionJob,
        adapter: BaseExchangeAdapter,
        progress_callback: Optional[Callable[[int, int], Coroutine[Any, Any, None]]] = None,
        use_year_partitioning: bool = False,
        listing_start_time_ms: Optional[int] = None,
    ) -> None:
        """Background runner for collection job."""
        try:
            logger.info("Starting historical collection job %s", job.job_id)
            await self.downloader.download(
                job=job,
                adapter=adapter,
                progress_callback=progress_callback,
                use_year_partitioning=use_year_partitioning,
                listing_start_time_ms=listing_start_time_ms,
            )
            logger.info("Completed historical collection job %s", job.job_id)
        except asyncio.CancelledError:
            logger.warning("Historical collection task was cancelled for %s", job.job_id)
            job.status = CollectionJobStatus.CANCELLED
            if self.repo:
                await self.repo.save_job(job)
        except Exception as err:
            logger.error("Historical collection error on %s: %s", job.job_id, err, exc_info=True)
            job.status = CollectionJobStatus.FAILED
            job.error_message = str(err)
            if self.repo:
                await self.repo.save_job(job)
        finally:
            self._active_tasks.pop(job.job_id, None)

    def cancel_collection(self, job_id: str) -> bool:
        """Cancel an in-flight collection job."""
        task = self._active_tasks.get(job_id)
        if task and not task.done():
            self.downloader.request_cancellation()
            task.cancel()
            return True
        return False

    async def compute_and_store_features(
        self,
        exchange: Exchange,
        symbol: str,
        timeframe: Timeframe,
        use_year_partitioning: bool = False,
    ) -> pd.DataFrame:
        """Compute single-timeframe features from canonical store and persist to Parquet."""
        df_canonical = self.storage.read_canonical(exchange, symbol, timeframe)
        if df_canonical.empty:
            raise ValueError(f"No canonical data found for {exchange.value}:{symbol}:{timeframe.value}")

        df_features = self.feature_engine.compute_features(df_canonical)
        if use_year_partitioning:
            self.storage.write_features_partitioned_by_year(df_features, exchange, symbol, timeframe, layer="features")
        else:
            self.storage.write_features(df_features, exchange, symbol, timeframe, layer="features")

        # Materialize research-ready stationary feature set
        try:
            df_research = self.feature_engine.filter_research_features(df_features, warmup_bars=200)
            if use_year_partitioning:
                self.storage.write_features_partitioned_by_year(
                    df_research, exchange, symbol, timeframe, layer="features_research"
                )
            else:
                self.storage.write_features(
                    df_research, exchange, symbol, timeframe, layer="features_research"
                )
        except Exception as e:
            logger.warning(
                "Could not filter research features for %s:%s:%s: %s",
                exchange.value,
                symbol,
                timeframe.value,
                e,
            )

        return df_features

    async def build_multi_timeframe_dataset(
        self,
        exchange: Exchange,
        symbol: str,
        base_timeframe: Timeframe,
        htf_timeframes: List[Timeframe],
    ) -> pd.DataFrame:
        """Compute base features and causally join multiple higher-timeframe feature tables."""
        # Ensure base features exist
        df_base = self.storage.read_features(exchange, symbol, base_timeframe)
        if df_base.empty:
            df_base = await self.compute_and_store_features(exchange, symbol, base_timeframe)

        htf_tables: Dict[Timeframe, pd.DataFrame] = {}
        for htf in htf_timeframes:
            df_htf = self.storage.read_features(exchange, symbol, htf)
            if df_htf.empty:
                df_htf = await self.compute_and_store_features(exchange, symbol, htf)
            htf_tables[htf] = df_htf

        # Causal backward as-of join
        df_mtf = self.mtf_joiner.join_htf_features(df_base, htf_tables)
        return df_mtf
