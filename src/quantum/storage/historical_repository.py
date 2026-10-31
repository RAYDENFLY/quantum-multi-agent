"""SQLite repository for historical collection jobs, checkpoints, manifests, and quality reports."""

import json
from typing import Any, Dict, List, Optional
import aiosqlite

from quantum.core.logging import get_logger
from quantum.domain.enums import Exchange, Timeframe
from quantum.historical.models import (
    CollectionJobStatus,
    DataQualityReport,
    DatasetManifest,
    HistoricalCollectionCheckpoint,
    HistoricalCollectionJob,
    ValidationStatus,
)

logger = get_logger("storage.historical_repository")


class HistoricalRepository:
    """Async repository managing SQLite persistence for Phase 4 metadata."""

    def __init__(self, connection: aiosqlite.Connection) -> None:
        self.conn = connection

    async def save_job(self, job: HistoricalCollectionJob) -> None:
        """Insert or update a historical collection job."""
        sql = """
        INSERT INTO historical_collection_jobs (
            job_id, exchange, symbol, timeframe, requested_start_ms, requested_end_ms,
            actual_start_ms, actual_end_ms, status, total_candles_fetched, checkpoint_ms,
            error_message, created_at_ms, updated_at_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(job_id) DO UPDATE SET
            actual_start_ms = excluded.actual_start_ms,
            actual_end_ms = excluded.actual_end_ms,
            status = excluded.status,
            total_candles_fetched = excluded.total_candles_fetched,
            checkpoint_ms = excluded.checkpoint_ms,
            error_message = excluded.error_message,
            updated_at_ms = excluded.updated_at_ms;
        """
        await self.conn.execute(
            sql,
            (
                job.job_id,
                job.exchange.value if hasattr(job.exchange, "value") else str(job.exchange),
                job.symbol.upper(),
                job.timeframe.value if hasattr(job.timeframe, "value") else str(job.timeframe),
                job.requested_start_ms,
                job.requested_end_ms,
                job.actual_start_ms,
                job.actual_end_ms,
                job.status.value,
                job.total_candles_fetched,
                job.checkpoint_ms,
                job.error_message,
                job.created_at_ms,
                job.updated_at_ms,
            ),
        )
        await self.conn.commit()

    async def get_job(self, job_id: str) -> Optional[HistoricalCollectionJob]:
        """Fetch job by ID."""
        sql = "SELECT * FROM historical_collection_jobs WHERE job_id = ?;"
        async with self.conn.execute(sql, (job_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return self._row_to_job(row)

    async def list_jobs(
        self,
        exchange: Optional[Exchange] = None,
        status: Optional[CollectionJobStatus] = None,
        limit: int = 50,
    ) -> List[HistoricalCollectionJob]:
        """List historical jobs matching optional filters."""
        query = "SELECT * FROM historical_collection_jobs"
        params: List[Any] = []
        conditions: List[str] = []

        if exchange:
            conditions.append("exchange = ?")
            params.append(exchange.value if hasattr(exchange, "value") else str(exchange))
        if status:
            conditions.append("status = ?")
            params.append(status.value if hasattr(status, "value") else str(status))

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_at_ms DESC LIMIT ?"
        params.append(limit)

        async with self.conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_job(row) for row in rows]

    async def save_checkpoint(self, checkpoint: HistoricalCollectionCheckpoint) -> None:
        """Insert or replace a collection checkpoint."""
        sql = """
        INSERT INTO historical_collection_checkpoints (
            checkpoint_id, job_id, exchange, symbol, timeframe, direction,
            last_fetched_open_time_ms, last_page_candle_count, earliest_open_time_ms,
            latest_open_time_ms, is_exhausted, updated_at_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(checkpoint_id) DO UPDATE SET
            last_fetched_open_time_ms = excluded.last_fetched_open_time_ms,
            last_page_candle_count = excluded.last_page_candle_count,
            earliest_open_time_ms = excluded.earliest_open_time_ms,
            latest_open_time_ms = excluded.latest_open_time_ms,
            is_exhausted = excluded.is_exhausted,
            updated_at_ms = excluded.updated_at_ms;
        """
        await self.conn.execute(
            sql,
            (
                checkpoint.checkpoint_id,
                checkpoint.job_id,
                checkpoint.exchange.value if hasattr(checkpoint.exchange, "value") else str(checkpoint.exchange),
                checkpoint.symbol.upper(),
                checkpoint.timeframe.value if hasattr(checkpoint.timeframe, "value") else str(checkpoint.timeframe),
                checkpoint.direction,
                checkpoint.last_fetched_open_time_ms,
                checkpoint.last_page_candle_count,
                checkpoint.earliest_open_time_ms,
                checkpoint.latest_open_time_ms,
                1 if checkpoint.is_exhausted else 0,
                checkpoint.updated_at_ms,
            ),
        )
        await self.conn.commit()

    async def get_checkpoint(self, job_id: str) -> Optional[HistoricalCollectionCheckpoint]:
        """Fetch the latest checkpoint associated with a job."""
        sql = "SELECT * FROM historical_collection_checkpoints WHERE job_id = ? ORDER BY updated_at_ms DESC LIMIT 1;"
        async with self.conn.execute(sql, (job_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return self._row_to_checkpoint(row)

    async def delete_checkpoint(self, checkpoint_id: str) -> None:
        """Delete checkpoint upon completed download."""
        sql = "DELETE FROM historical_collection_checkpoints WHERE checkpoint_id = ?;"
        await self.conn.execute(sql, (checkpoint_id,))
        await self.conn.commit()

    async def save_manifest(self, manifest: DatasetManifest) -> None:
        """Insert or replace a dataset manifest."""
        sql = """
        INSERT INTO dataset_manifests (
            manifest_id, dataset_name, dataset_version, feature_version, exchange,
            symbol, timeframe, start_time_ms, end_time_ms, candle_count,
            raw_parquet_path, canonical_parquet_path, feature_parquet_path,
            file_sha256, metadata_json, created_at_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(manifest_id) DO UPDATE SET
            file_sha256 = excluded.file_sha256,
            metadata_json = excluded.metadata_json,
            candle_count = excluded.candle_count,
            feature_parquet_path = excluded.feature_parquet_path;
        """
        await self.conn.execute(
            sql,
            (
                manifest.manifest_id,
                manifest.dataset_name,
                manifest.dataset_version,
                manifest.feature_version,
                manifest.exchange.value if hasattr(manifest.exchange, "value") else str(manifest.exchange),
                manifest.symbol.upper(),
                manifest.timeframe.value if hasattr(manifest.timeframe, "value") else str(manifest.timeframe),
                manifest.start_time_ms,
                manifest.end_time_ms,
                manifest.candle_count,
                manifest.raw_parquet_path,
                manifest.canonical_parquet_path,
                manifest.feature_parquet_path,
                manifest.file_sha256,
                json.dumps(manifest.metadata),
                manifest.created_at_ms,
            ),
        )
        await self.conn.commit()

    async def get_manifest(self, manifest_id: str) -> Optional[DatasetManifest]:
        """Fetch dataset manifest by ID."""
        sql = "SELECT * FROM dataset_manifests WHERE manifest_id = ?;"
        async with self.conn.execute(sql, (manifest_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return self._row_to_manifest(row)

    async def list_manifests(
        self,
        symbol: Optional[str] = None,
        timeframe: Optional[Timeframe] = None,
        limit: int = 50,
    ) -> List[DatasetManifest]:
        """List manifests with optional filters."""
        query = "SELECT * FROM dataset_manifests"
        params: List[Any] = []
        conditions: List[str] = []

        if symbol:
            conditions.append("symbol = ?")
            params.append(symbol.upper())
        if timeframe:
            conditions.append("timeframe = ?")
            params.append(timeframe.value if hasattr(timeframe, "value") else str(timeframe))

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_at_ms DESC LIMIT ?"
        params.append(limit)

        async with self.conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_manifest(row) for row in rows]

    async def save_quality_report(self, report: DataQualityReport) -> None:
        """Insert a data quality report."""
        sql = """
        INSERT INTO data_quality_reports (
            report_id, run_id, exchange, symbol, timeframe, requested_start_ms,
            requested_end_ms, actual_start_ms, actual_end_ms, expected_count,
            observed_count, missing_count, duplicate_count, conflicting_duplicate_count,
            invalid_ohlc_count, incomplete_candle_count, coverage_pct, validation_status,
            feature_version, dataset_version, details_json, created_at_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(report_id) DO UPDATE SET
            validation_status = excluded.validation_status,
            coverage_pct = excluded.coverage_pct,
            details_json = excluded.details_json;
        """
        await self.conn.execute(
            sql,
            (
                report.report_id,
                report.run_id,
                report.exchange.value if hasattr(report.exchange, "value") else str(report.exchange),
                report.symbol.upper(),
                report.timeframe.value if hasattr(report.timeframe, "value") else str(report.timeframe),
                report.requested_start_ms,
                report.requested_end_ms,
                report.actual_start_ms,
                report.actual_end_ms,
                report.expected_count,
                report.observed_count,
                report.missing_count,
                report.duplicate_count,
                report.conflicting_duplicate_count,
                report.invalid_ohlc_count,
                report.incomplete_candle_count,
                report.coverage_pct,
                report.validation_status.value,
                report.feature_version,
                report.dataset_version,
                json.dumps(report.details),
                report.created_at_ms,
            ),
        )
        await self.conn.commit()

    async def get_quality_report(self, report_id: str) -> Optional[DataQualityReport]:
        """Fetch quality report by ID."""
        sql = "SELECT * FROM data_quality_reports WHERE report_id = ?;"
        async with self.conn.execute(sql, (report_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return self._row_to_quality_report(row)

    async def list_quality_reports(
        self,
        symbol: Optional[str] = None,
        limit: int = 50,
    ) -> List[DataQualityReport]:
        """List recent data quality reports."""
        query = "SELECT * FROM data_quality_reports"
        params: List[Any] = []
        if symbol:
            query += " WHERE symbol = ?"
            params.append(symbol.upper())
        query += " ORDER BY created_at_ms DESC LIMIT ?"
        params.append(limit)

        async with self.conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [self._row_to_quality_report(row) for row in rows]

    # --- Deserialization helpers ---

    def _row_to_job(self, row: Any) -> HistoricalCollectionJob:
        return HistoricalCollectionJob(
            job_id=row["job_id"],
            exchange=Exchange(row["exchange"]),
            symbol=row["symbol"],
            timeframe=Timeframe(row["timeframe"]),
            requested_start_ms=row["requested_start_ms"],
            requested_end_ms=row["requested_end_ms"],
            actual_start_ms=row["actual_start_ms"],
            actual_end_ms=row["actual_end_ms"],
            status=CollectionJobStatus(row["status"]),
            total_candles_fetched=row["total_candles_fetched"],
            checkpoint_ms=row["checkpoint_ms"],
            error_message=row["error_message"],
            created_at_ms=row["created_at_ms"],
            updated_at_ms=row["updated_at_ms"],
        )

    def _row_to_checkpoint(self, row: Any) -> HistoricalCollectionCheckpoint:
        return HistoricalCollectionCheckpoint(
            checkpoint_id=row["checkpoint_id"],
            job_id=row["job_id"],
            exchange=Exchange(row["exchange"]),
            symbol=row["symbol"],
            timeframe=Timeframe(row["timeframe"]),
            direction=row["direction"],
            last_fetched_open_time_ms=row["last_fetched_open_time_ms"],
            last_page_candle_count=row["last_page_candle_count"],
            earliest_open_time_ms=row["earliest_open_time_ms"],
            latest_open_time_ms=row["latest_open_time_ms"],
            is_exhausted=bool(row["is_exhausted"]),
            updated_at_ms=row["updated_at_ms"],
        )

    def _row_to_manifest(self, row: Any) -> DatasetManifest:
        return DatasetManifest(
            manifest_id=row["manifest_id"],
            dataset_name=row["dataset_name"],
            dataset_version=row["dataset_version"],
            feature_version=row["feature_version"],
            exchange=Exchange(row["exchange"]),
            symbol=row["symbol"],
            timeframe=Timeframe(row["timeframe"]),
            start_time_ms=row["start_time_ms"],
            end_time_ms=row["end_time_ms"],
            candle_count=row["candle_count"],
            raw_parquet_path=row["raw_parquet_path"],
            canonical_parquet_path=row["canonical_parquet_path"],
            feature_parquet_path=row["feature_parquet_path"],
            file_sha256=row["file_sha256"],
            metadata=json.loads(row["metadata_json"]) if row["metadata_json"] else {},
            created_at_ms=row["created_at_ms"],
        )

    def _row_to_quality_report(self, row: Any) -> DataQualityReport:
        return DataQualityReport(
            report_id=row["report_id"],
            run_id=row["run_id"],
            exchange=Exchange(row["exchange"]),
            symbol=row["symbol"],
            timeframe=Timeframe(row["timeframe"]),
            requested_start_ms=row["requested_start_ms"],
            requested_end_ms=row["requested_end_ms"],
            actual_start_ms=row["actual_start_ms"],
            actual_end_ms=row["actual_end_ms"],
            expected_count=row["expected_count"],
            observed_count=row["observed_count"],
            missing_count=row["missing_count"],
            duplicate_count=row["duplicate_count"],
            conflicting_duplicate_count=row["conflicting_duplicate_count"],
            invalid_ohlc_count=row["invalid_ohlc_count"],
            incomplete_candle_count=row["incomplete_candle_count"],
            coverage_pct=row["coverage_pct"],
            validation_status=ValidationStatus(row["validation_status"]),
            feature_version=row["feature_version"],
            dataset_version=row["dataset_version"],
            details=json.loads(row["details_json"]) if row["details_json"] else {},
            created_at_ms=row["created_at_ms"],
        )
