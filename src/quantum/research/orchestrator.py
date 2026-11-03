"""Continuous, Asynchronous, Parallelized Alpha Discovery Orchestrator."""

import concurrent.futures
import csv
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

from quantum.core.logging import get_logger
from quantum.domain.research_contract import (
    ResearchExperimentContract,
    ASTER_DEX_RETAIL_CONFIG,
    calculate_frequency_metrics,
)
from quantum.research.feature_cache import IntermediateFeatureCache
from quantum.research.models import (
    ContinuousExperimentConfig,
    DatasetFingerprint,
    DatasetPartitionType,
    ExperimentExecutionRecord,
    ExperimentPriority,
    HypothesisStatus,
    RejectionCategory,
    SpecificRejectionReason,
)
from quantum.research.partitioner import (
    ContinuousResearchPartitioner,
    DatasetPartition,
    HoldoutContaminationError,
    PROSPECTIVE_HOLDOUT_START_MS,
)
from quantum.research.registry import CentralizedHypothesisRegistry
from quantum.research.rejection import AutomaticRejectionEngine, RejectionEvaluationResult
from quantum.strategies.hypothesis_engine import backtest_single_hypothesis

logger = get_logger("research.orchestrator")


class ContinuousResearchOrchestrator:
    """Orchestrates continuous, parallelized hypothesis evaluation with strict evidence separation."""

    def __init__(
        self,
        ledger_dir: Path = Path("audit/strategy_research/continuous_research_orchestration"),
        max_workers: int = 4,
        feature_cache: Optional[IntermediateFeatureCache] = None,
        registry: Optional[CentralizedHypothesisRegistry] = None,
        partitioner: Optional[ContinuousResearchPartitioner] = None,
    ) -> None:
        self.ledger_dir = ledger_dir
        self.ledger_dir.mkdir(parents=True, exist_ok=True)
        self.max_workers = max_workers
        self.feature_cache = feature_cache or IntermediateFeatureCache(
            disk_cache_dir=ledger_dir / ".cache"
        )
        self.registry = registry or CentralizedHypothesisRegistry()
        self.partitioner = partitioner or ContinuousResearchPartitioner()

        self._queue: List[ContinuousExperimentConfig] = []
        self._executed_fingerprints: Set[Tuple[str, str]] = set()
        self._ledger_lock = threading.Lock()
        self.ledger_csv_path = self.ledger_dir / "EXPERIMENT_LEDGER.csv"
        self.ledger_jsonl_path = self.ledger_dir / "EXPERIMENT_LEDGER.jsonl"

        self._init_ledger_files()
        self._load_existing_fingerprints()

        # Telemetry
        self.total_dispatched = 0
        self.total_completed = 0
        self.total_accepted = 0
        self.total_rejected = 0
        self.total_redundant_skipped = 0

    def _init_ledger_files(self) -> None:
        if not self.ledger_csv_path.exists():
            headers = [
                "experiment_id",
                "hypothesis_id",
                "partition_type",
                "symbol",
                "dataset_fingerprint",
                "config_fingerprint",
                "executed_at_utc",
                "duration_seconds",
                "completed_episodes",
                "frequency_daily",
                "win_rate_pct",
                "profit_factor",
                "gross_pnl_usd",
                "net_pnl_usd",
                "net_expectancy_bps",
                "mean_net_daily_return_pct",
                "max_drawdown_pct",
                "sharpe_ratio",
                "avg_duration_minutes",
                "is_accepted",
                "rejection_category",
                "rejection_reasons",
            ]
            with open(self.ledger_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

    def _load_existing_fingerprints(self) -> None:
        if self.ledger_csv_path.exists() and self.ledger_csv_path.stat().st_size > 0:
            try:
                df = pd.read_csv(self.ledger_csv_path)
                if "config_fingerprint" in df.columns and "dataset_fingerprint" in df.columns:
                    for _, row in df.iterrows():
                        self._executed_fingerprints.add(
                            (str(row["config_fingerprint"]), str(row["dataset_fingerprint"]))
                        )
            except Exception:
                pass

    def enqueue_experiment(self, config: ContinuousExperimentConfig) -> None:
        """Enqueues an experiment into the priority queue."""
        self._queue.append(config)
        self.registry.update_status(config.hypothesis_id, HypothesisStatus.QUEUED)

    def _evaluate_single_experiment(
        self,
        config: ContinuousExperimentConfig,
        partition: DatasetPartition,
    ) -> ExperimentExecutionRecord:
        """Executes a single experiment causally on the designated dataset partition."""
        t0 = time.perf_counter()
        executed_at = datetime.now(timezone.utc).isoformat()
        dataset_fp = partition.fingerprint.sha256_hash
        config_fp = config.config_fingerprint

        # 1. Enforce Sealed Holdout Isolation
        if partition.partition_type != DatasetPartitionType.PROSPECTIVE_OOS:
            if partition.fingerprint.end_timestamp_ms >= PROSPECTIVE_HOLDOUT_START_MS:
                raise HoldoutContaminationError(
                    f"FATAL: Experiment {config.experiment_id} on partition {partition.partition_type.value} "
                    f"attempted to access sealed holdout timestamp {partition.fingerprint.end_timestamp_ms}."
                )

        # 2. Check for Redundancy
        pair_key = (config_fp, dataset_fp)
        with self._ledger_lock:
            if pair_key in self._executed_fingerprints:
                self.total_redundant_skipped += 1
                return ExperimentExecutionRecord(
                    experiment_id=config.experiment_id,
                    hypothesis_id=config.hypothesis_id,
                    partition_type=config.partition_type,
                    symbol=config.symbol,
                    dataset_fingerprint=dataset_fp,
                    config_fingerprint=config_fp,
                    executed_at_utc=executed_at,
                    duration_seconds=0.0,
                    completed_episodes=0,
                    frequency_daily=0.0,
                    win_rate_pct=0.0,
                    profit_factor=0.0,
                    gross_pnl_usd=0.0,
                    net_pnl_usd=0.0,
                    net_expectancy_bps=0.0,
                    mean_net_daily_return_pct=0.0,
                    max_drawdown_pct=0.0,
                    sharpe_ratio=0.0,
                    avg_duration_minutes=0.0,
                    is_accepted=False,
                    rejection_category=RejectionCategory.REDUNDANT_CONFIGURATION,
                    rejection_reasons=[SpecificRejectionReason.DUPLICATE_FINGERPRINT.value],
                )

        # 3. Obtain Features via Reproducible Intermediate Cache
        enriched_df, was_cached = self.feature_cache.get_or_compute(
            df_raw=partition.df,
            symbol=config.symbol,
            timeframe=partition.timeframe,
            dataset_sha256=dataset_fp,
        )

        # 4. Execute Causal Next-Bar Backtest
        cost_cfg = config.contract.exchange_cost_config
        trades = backtest_single_hypothesis(
            df=enriched_df,
            hypothesis_id=config.hypothesis_id,
            symbol=config.symbol,
            capital_usd=config.contract.initial_equity_usd,
            taker_fee_bps=cost_cfg.taker_fee_bps,
            maker_fee_bps=cost_cfg.maker_fee_bps,
            slippage_bps=cost_cfg.slippage_bps_per_leg,
            spread_bps_half=cost_cfg.spread_bps_half,
        )

        duration = time.perf_counter() - t0
        n_trades = len(trades)
        obs_days = max(1.0, len(enriched_df) * 5.0 / 1440.0)
        freq_daily = round(n_trades / obs_days, 4)

        if n_trades == 0:
            win_rate = 0.0
            profit_factor = 0.0
            gross_pnl = 0.0
            net_pnl = 0.0
            net_exp_bps = 0.0
            mean_daily_ret = 0.0
            max_dd = 0.0
            sharpe = 0.0
            avg_dur = 0.0
        else:
            wins = sum(1 for t in trades if t.net_pnl_usd > 0)
            win_rate = round((wins / n_trades) * 100.0, 2)
            gross_wins = sum(t.gross_pnl_usd for t in trades if t.gross_pnl_usd > 0)
            gross_losses = abs(sum(t.gross_pnl_usd for t in trades if t.gross_pnl_usd < 0))
            profit_factor = round(gross_wins / gross_losses, 2) if gross_losses > 0 else 1.0

            gross_pnl = round(sum(t.gross_pnl_usd for t in trades), 2)
            net_pnl = round(sum(t.net_pnl_usd for t in trades), 2)
            net_exp_bps = round(float(np.mean([t.net_return_bps for t in trades])), 2)
            mean_daily_ret = round((net_pnl / config.contract.initial_equity_usd) / obs_days * 100.0, 4)
            avg_dur = round(float(np.mean([t.duration_minutes for t in trades])), 1)

            # Max drawdown calculation
            rets = np.array([t.net_pnl_usd for t in trades])
            equity_curve = config.contract.initial_equity_usd + np.cumsum(rets)
            peaks = np.maximum.accumulate(equity_curve)
            dd_pct = (peaks - equity_curve) / np.maximum(peaks, 1e-6) * 100.0
            max_dd = round(float(np.max(dd_pct)), 2)

            # Sharpe
            ret_series = pd.Series([t.net_return_bps for t in trades])
            std = float(ret_series.std())
            sharpe = round(float(ret_series.mean() / (std + 1e-6) * np.sqrt(freq_daily * 365.0)), 2) if std > 0 else 0.0

        # 5. Automated Rejection Inspection
        methodology_res = AutomaticRejectionEngine.evaluate_methodology(config, trades)
        statistical_res = AutomaticRejectionEngine.evaluate_statistics(
            config=config,
            frequency_daily=freq_daily,
            profit_factor=profit_factor,
            net_expectancy_bps=net_exp_bps,
            mean_net_daily_return_pct=mean_daily_ret,
            max_drawdown_pct=max_dd,
        )

        rejection_category = None
        rejection_reasons = []

        if not methodology_res.is_accepted:
            is_accepted = False
            rejection_category = methodology_res.category
            rejection_reasons.extend(methodology_res.reasons)
        elif not statistical_res.is_accepted:
            is_accepted = False
            rejection_category = statistical_res.category
            rejection_reasons.extend(statistical_res.reasons)
        else:
            is_accepted = True

        rec = ExperimentExecutionRecord(
            experiment_id=config.experiment_id,
            hypothesis_id=config.hypothesis_id,
            partition_type=config.partition_type,
            symbol=config.symbol,
            dataset_fingerprint=dataset_fp,
            config_fingerprint=config_fp,
            executed_at_utc=executed_at,
            duration_seconds=round(duration, 3),
            completed_episodes=n_trades,
            frequency_daily=freq_daily,
            win_rate_pct=win_rate,
            profit_factor=profit_factor,
            gross_pnl_usd=gross_pnl,
            net_pnl_usd=net_pnl,
            net_expectancy_bps=net_exp_bps,
            mean_net_daily_return_pct=mean_daily_ret,
            max_drawdown_pct=max_dd,
            sharpe_ratio=sharpe,
            avg_duration_minutes=avg_dur,
            is_accepted=is_accepted,
            rejection_category=rejection_category,
            rejection_reasons=rejection_reasons,
        )

        # 6. Record into Centralized Registry and Ledger
        self._record_execution(rec)
        return rec

    def _record_execution(self, rec: ExperimentExecutionRecord) -> None:
        """Appends execution record atomically to CSV and JSONL ledgers."""
        with self._ledger_lock:
            self._executed_fingerprints.add((rec.config_fingerprint, rec.dataset_fingerprint))
            self.total_completed += 1
            if rec.is_accepted:
                self.total_accepted += 1
            else:
                self.total_rejected += 1

            # Append to CSV
            with open(self.ledger_csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    rec.experiment_id,
                    rec.hypothesis_id,
                    rec.partition_type.value,
                    rec.symbol,
                    rec.dataset_fingerprint,
                    rec.config_fingerprint,
                    rec.executed_at_utc,
                    rec.duration_seconds,
                    rec.completed_episodes,
                    rec.frequency_daily,
                    rec.win_rate_pct,
                    rec.profit_factor,
                    rec.gross_pnl_usd,
                    rec.net_pnl_usd,
                    rec.net_expectancy_bps,
                    rec.mean_net_daily_return_pct,
                    rec.max_drawdown_pct,
                    rec.sharpe_ratio,
                    rec.avg_duration_minutes,
                    rec.is_accepted,
                    rec.rejection_category.value if rec.rejection_category else "",
                    "; ".join(rec.rejection_reasons),
                ])

            # Append to JSONL
            with open(self.ledger_jsonl_path, "a", encoding="utf-8") as f:
                f.write(rec.model_dump_json() + "\n")

        # Update registry
        self.registry.record_evaluation_outcome(
            hypothesis_id=rec.hypothesis_id,
            is_accepted=rec.is_accepted,
            mean_net_daily_return_pct=rec.mean_net_daily_return_pct,
            profit_factor=rec.profit_factor,
        )

    def run_queued_experiments(
        self,
        partitions_by_symbol: Dict[str, Dict[DatasetPartitionType, DatasetPartition]],
    ) -> List[ExperimentExecutionRecord]:
        """Dispatches queued experiments across workers according to priority scores."""
        if not self._queue:
            return []

        # Sort queue by priority score descending
        self._queue.sort(key=lambda c: c.priority.priority_score, reverse=True)
        pending_configs = list(self._queue)
        self._queue.clear()

        records: List[ExperimentExecutionRecord] = []

        # Execute in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_config = {}
            for cfg in pending_configs:
                sym = cfg.symbol
                part_type = cfg.partition_type
                if sym not in partitions_by_symbol or part_type not in partitions_by_symbol[sym]:
                    logger.warning(f"Partition {part_type.value} not available for {sym}; skipping {cfg.experiment_id}")
                    continue

                part = partitions_by_symbol[sym][part_type]
                future = executor.submit(self._evaluate_single_experiment, cfg, part)
                future_to_config[future] = cfg
                self.total_dispatched += 1

            for future in concurrent.futures.as_completed(future_to_config):
                cfg = future_to_config[future]
                try:
                    rec = future.result()
                    records.append(rec)
                except Exception as exc:
                    logger.error(f"Experiment {cfg.experiment_id} generated exception: {exc}")
                    raise exc

        return records

    def run_prospective_oos_collector_tick(
        self,
        new_candle_timestamp_ms: int,
        symbol: str,
        price: float,
    ) -> Dict[str, Any]:
        """Simulates/monitors continuous forward-running prospective observation tick.
        
        Runs asynchronously without blocking retrospective backtests or leaking into training.
        """
        is_holdout = new_candle_timestamp_ms >= PROSPECTIVE_HOLDOUT_START_MS
        return {
            "timestamp_ms": new_candle_timestamp_ms,
            "symbol": symbol,
            "price": price,
            "partition": DatasetPartitionType.PROSPECTIVE_OOS.value if is_holdout else DatasetPartitionType.ROLLING_OOS.value,
            "is_holdout_sealed": is_holdout,
            "status": "COLLECTING_INDEPENDENTLY",
            "message": "Prospective collection proceeding independently without gating research."
        }
