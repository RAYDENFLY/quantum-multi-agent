"""Pipeline Orchestrator managing deterministic state transitions across all 5 agents."""

import asyncio
import json
import time
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from quantum.agents.analyst import AnalystAgent
from quantum.agents.contracts import (
    AnalystInput,
    AnalystOutput,
    RiskInput,
    RiskOutput,
    ScoutInput,
    ScoutOutput,
    SniperInput,
    SniperOutput,
)
from quantum.agents.risk import RiskAgent
from quantum.agents.scout import ScoutAgent
from quantum.agents.sniper import SniperAgent
from quantum.core.event_bus import EventBus
from quantum.core.logging import get_logger
from quantum.domain.enums import (
    AgentAction,
    AgentId,
    EventPriority,
    InferenceMode,
    PipelineStage,
    PipelineStatus,
)
from quantum.domain.events import (
    MessageEnvelope,
    PipelineStageCompletedPayload,
    TOPIC_PIPELINE_PROPOSAL_CREATED,
    TOPIC_PIPELINE_STAGE_COMPLETED,
    TOPIC_RISK_DECISION_EVALUATED,
)
from quantum.domain.models import RiskDecision, ScannerCandidate, TradeProposal
from quantum.storage.database import DatabaseManager

logger = get_logger("agents.orchestrator")

TIMEOUT_SCOUT_S = 0.050    # 50 ms
TIMEOUT_ANALYST_S = 0.050  # 50 ms
TIMEOUT_SNIPER_S = 0.050   # 50 ms
TIMEOUT_RISK_S = 0.025     # 25 ms


class PipelineRunResult(BaseModel):
    """Complete outcome of an end-to-end multi-agent pipeline execution."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    pipeline_run_id: str
    status: PipelineStatus
    final_stage: PipelineStage
    scout_output: Optional[ScoutOutput] = None
    analyst_output: Optional[AnalystOutput] = None
    sniper_output: Optional[SniperOutput] = None
    risk_output: Optional[RiskOutput] = None
    total_latency_ms: float
    abort_reason: Optional[str] = None


class PipelineOrchestrator:
    """Finite State Machine orchestrating Scout -> Analyst -> Sniper -> Risk."""

    def __init__(
        self,
        scout: ScoutAgent,
        analyst: AnalystAgent,
        sniper: SniperAgent,
        risk: RiskAgent,
        event_bus: Optional[EventBus] = None,
        db_manager: Optional[DatabaseManager] = None,
        default_equity_usdt: Optional[float] = None,
    ) -> None:
        self.scout = scout
        self.analyst = analyst
        self.sniper = sniper
        self.risk = risk
        self.event_bus = event_bus
        self.db = db_manager
        self.default_equity_usdt = default_equity_usdt

    async def execute(
        self,
        candidate: ScannerCandidate,
        current_equity_usdt: Optional[float] = None,
        open_positions_count: Optional[int] = None,
        total_exposure_usdt: Optional[float] = None,
    ) -> PipelineRunResult:
        """Execute candidate through the sequential 5-agent quantitative pipeline."""
        start_time = time.perf_counter()
        now_ms = int(time.time() * 1000)
        run_id = f"run_{candidate.candidate_id}_{now_ms}"

        logger.info("Starting pipeline run %s for candidate %s (%s)", run_id, candidate.symbol, candidate.directional_bias.name)

        # Record run start in SQLite if database connected
        if self.db and self.db.is_connected:
            await self._record_run_start(run_id, candidate, now_ms)

        # 1. Feature Extraction & Missing Data Validation Gate
        if not self._validate_market_context(candidate):
            logger.warning("Pipeline run %s aborted: invalid market context features", run_id)
            return await self._finalize_run(
                run_id=run_id,
                candidate=candidate,
                status=PipelineStatus.SKIP_FEATURE_INVALID,
                final_stage=PipelineStage.FEATURE_EXTRACTION,
                start_time=start_time,
                abort_reason="Missing bars, NaN, or non-finite features in MarketContext",
            )

        # 2. Stage 1: SCOUT Evaluation
        try:
            scout_out = await asyncio.wait_for(
                self.scout.evaluate(ScoutInput(pipeline_run_id=run_id, candidate=candidate)),
                timeout=TIMEOUT_SCOUT_S,
            )
        except asyncio.TimeoutError:
            return await self._finalize_run(
                run_id=run_id,
                candidate=candidate,
                status=PipelineStatus.SKIP_SCOUT,
                final_stage=PipelineStage.SCOUT,
                start_time=start_time,
                abort_reason=f"SCOUT execution timed out (> {TIMEOUT_SCOUT_S * 1000:.0f}ms)",
            )
        except Exception as e:
            return await self._finalize_run(
                run_id=run_id,
                candidate=candidate,
                status=PipelineStatus.ERROR,
                final_stage=PipelineStage.SCOUT,
                start_time=start_time,
                abort_reason=f"SCOUT unexpected error: {e}",
            )

        await self._publish_stage_completed(run_id, PipelineStage.SCOUT, scout_out.action.name, AgentId.SCOUT, scout_out.model_version)

        if scout_out.action != AgentAction.PROCEED:
            return await self._finalize_run(
                run_id=run_id,
                candidate=candidate,
                status=PipelineStatus.SKIP_SCOUT,
                final_stage=PipelineStage.SCOUT,
                start_time=start_time,
                scout_out=scout_out,
                abort_reason=scout_out.abort_reason or "SCOUT decision was SKIP",
            )

        # 3. Stage 2: ANALYST Evaluation
        try:
            analyst_out = await asyncio.wait_for(
                self.analyst.evaluate(AnalystInput(pipeline_run_id=run_id, candidate=candidate, scout_output=scout_out)),
                timeout=TIMEOUT_ANALYST_S,
            )
        except asyncio.TimeoutError:
            return await self._finalize_run(
                run_id=run_id,
                candidate=candidate,
                status=PipelineStatus.SKIP_ANALYST,
                final_stage=PipelineStage.ANALYST,
                start_time=start_time,
                scout_out=scout_out,
                abort_reason=f"ANALYST execution timed out (> {TIMEOUT_ANALYST_S * 1000:.0f}ms)",
            )
        except Exception as e:
            return await self._finalize_run(
                run_id=run_id,
                candidate=candidate,
                status=PipelineStatus.ERROR,
                final_stage=PipelineStage.ANALYST,
                start_time=start_time,
                scout_out=scout_out,
                abort_reason=f"ANALYST unexpected error: {e}",
            )

        await self._publish_stage_completed(run_id, PipelineStage.ANALYST, analyst_out.action.name, AgentId.ANALYST, analyst_out.model_version)

        if analyst_out.action != AgentAction.PROCEED:
            return await self._finalize_run(
                run_id=run_id,
                candidate=candidate,
                status=PipelineStatus.SKIP_ANALYST,
                final_stage=PipelineStage.ANALYST,
                start_time=start_time,
                scout_out=scout_out,
                analyst_out=analyst_out,
                abort_reason=analyst_out.abort_reason or "ANALYST decision was SKIP",
            )

        # 4. Stage 3: SNIPER Evaluation
        try:
            sniper_out = await asyncio.wait_for(
                self.sniper.evaluate(
                    SniperInput(pipeline_run_id=run_id, candidate=candidate, scout_output=scout_out, analyst_output=analyst_out)
                ),
                timeout=TIMEOUT_SNIPER_S,
            )
        except asyncio.TimeoutError:
            return await self._finalize_run(
                run_id=run_id,
                candidate=candidate,
                status=PipelineStatus.SKIP_SNIPER,
                final_stage=PipelineStage.SNIPER,
                start_time=start_time,
                scout_out=scout_out,
                analyst_out=analyst_out,
                abort_reason=f"SNIPER execution timed out (> {TIMEOUT_SNIPER_S * 1000:.0f}ms)",
            )
        except Exception as e:
            return await self._finalize_run(
                run_id=run_id,
                candidate=candidate,
                status=PipelineStatus.ERROR,
                final_stage=PipelineStage.SNIPER,
                start_time=start_time,
                scout_out=scout_out,
                analyst_out=analyst_out,
                abort_reason=f"SNIPER unexpected error: {e}",
            )

        await self._publish_stage_completed(run_id, PipelineStage.SNIPER, sniper_out.action.name, AgentId.SNIPER, sniper_out.model_version)

        if sniper_out.action != AgentAction.PROPOSE_TRADE or sniper_out.proposal is None:
            return await self._finalize_run(
                run_id=run_id,
                candidate=candidate,
                status=PipelineStatus.SKIP_SNIPER,
                final_stage=PipelineStage.SNIPER,
                start_time=start_time,
                scout_out=scout_out,
                analyst_out=analyst_out,
                sniper_out=sniper_out,
                abort_reason=sniper_out.abort_reason or "SNIPER decision was SKIP",
            )

        # Publish proposal created event
        if self.event_bus:
            await self.event_bus.publish(
                MessageEnvelope(
                    message_id=f"msg_{sniper_out.proposal.proposal_id}",
                    pipeline_run_id=run_id,
                    idempotency_key=f"idemp_{run_id}_proposal",
                    source="AGENT_SNIPER",
                    topic=TOPIC_PIPELINE_PROPOSAL_CREATED,
                    priority=EventPriority.P1,
                    created_at_ms=int(time.time() * 1000),
                    snapshot_timestamp_ms=candidate.context.snapshot_timestamp_ms,
                    model_version=sniper_out.model_version,
                    payload=sniper_out.proposal,
                )
            )

        # 5. Stage 4: RISK Evaluation (Deterministic 12-Gate Veto)
        equity = current_equity_usdt if current_equity_usdt is not None else self.default_equity_usdt
        open_count = open_positions_count if open_positions_count is not None else 0
        tot_exposure = total_exposure_usdt if total_exposure_usdt is not None else 0.0

        try:
            risk_out = await asyncio.wait_for(
                self.risk.evaluate(
                    RiskInput(
                        pipeline_run_id=run_id,
                        candidate=candidate,
                        proposal=sniper_out.proposal,
                        current_equity_usdt=equity,
                        open_positions_count=open_count,
                        total_exposure_usdt=tot_exposure,
                    )
                ),
                timeout=TIMEOUT_RISK_S,
            )
        except asyncio.TimeoutError:
            return await self._finalize_run(
                run_id=run_id,
                candidate=candidate,
                status=PipelineStatus.VETO_RISK,
                final_stage=PipelineStage.RISK,
                start_time=start_time,
                scout_out=scout_out,
                analyst_out=analyst_out,
                sniper_out=sniper_out,
                abort_reason=f"RISK execution timed out (> {TIMEOUT_RISK_S * 1000:.0f}ms)",
            )
        except Exception as e:
            return await self._finalize_run(
                run_id=run_id,
                candidate=candidate,
                status=PipelineStatus.ERROR,
                final_stage=PipelineStage.RISK,
                start_time=start_time,
                scout_out=scout_out,
                analyst_out=analyst_out,
                sniper_out=sniper_out,
                abort_reason=f"RISK unexpected error: {e}",
            )

        # Publish risk decision event
        if self.event_bus:
            await self.event_bus.publish(
                MessageEnvelope(
                    message_id=f"msg_{risk_out.decision.decision_id}",
                    pipeline_run_id=run_id,
                    idempotency_key=f"idemp_{run_id}_risk",
                    source="AGENT_RISK",
                    topic=TOPIC_RISK_DECISION_EVALUATED,
                    priority=EventPriority.P0,
                    created_at_ms=int(time.time() * 1000),
                    snapshot_timestamp_ms=candidate.context.snapshot_timestamp_ms,
                    model_version="deterministic_v1",
                    payload=risk_out.decision,
                )
            )

        status = PipelineStatus.APPROVED if risk_out.decision.decision == AgentAction.APPROVED else PipelineStatus.VETO_RISK
        abort_reason = "; ".join(risk_out.decision.veto_reasons) if risk_out.decision.veto_reasons else None

        return await self._finalize_run(
            run_id=run_id,
            candidate=candidate,
            status=status,
            final_stage=PipelineStage.RISK,
            start_time=start_time,
            scout_out=scout_out,
            analyst_out=analyst_out,
            sniper_out=sniper_out,
            risk_out=risk_out,
            abort_reason=abort_reason,
        )

    def _validate_market_context(self, candidate: ScannerCandidate) -> bool:
        """Validate MarketContext has non-null, finite values."""
        context = candidate.context
        if context.last_price <= 0 or context.mark_price <= 0 or context.atr_15m <= 0:
            return False
        # Verify no NaN or Inf in features
        for val in context.features.values():
            if val is None or val != val or abs(val) == float("inf"):
                return False
        return True

    async def _publish_stage_completed(
        self, run_id: str, stage: PipelineStage, action: str, agent_id: AgentId, model_ver: str
    ) -> None:
        """Publish pipeline.stage.completed event to EventBus."""
        if not self.event_bus:
            return
        payload = PipelineStageCompletedPayload(
            pipeline_run_id=run_id,
            stage=stage,
            status=PipelineStatus.RUNNING,
            agent_id=agent_id.name,
            action=action,
            latency_ms=1.0,
        )
        await self.event_bus.publish(
            MessageEnvelope(
                message_id=f"msg_{run_id}_{stage.name}",
                pipeline_run_id=run_id,
                idempotency_key=f"idemp_{run_id}_{stage.name}",
                source=f"AGENT_{agent_id.name}",
                topic=TOPIC_PIPELINE_STAGE_COMPLETED,
                priority=EventPriority.P1,
                created_at_ms=int(time.time() * 1000),
                snapshot_timestamp_ms=0,
                model_version=model_ver,
                payload=payload,
            )
        )

    async def _record_run_start(self, run_id: str, candidate: ScannerCandidate, start_ms: int) -> None:
        """Insert initial record into agent_runs table, ensuring foreign keys exist."""
        try:
            instrument_id = f"{candidate.exchange.name}:{candidate.symbol}"
            snapshot_id = f"snap_{candidate.candidate_id}"
            await self.db.execute_commit(
                """
                INSERT OR IGNORE INTO exchange_instruments (
                    instrument_id, exchange, symbol, base_asset, quote_asset, status,
                    tick_size, lot_step, min_order_qty, max_order_qty, min_notional_usdt,
                    max_leverage, maker_fee_rate, taker_fee_rate, onboard_timestamp_ms, updated_at_ms
                ) VALUES (?, ?, ?, ?, 'USDT', 'TRADING', 0.1, 0.001, 0.001, 1000.0, 10.0, 50.0, 0.0002, 0.00055, ?, ?)
                """,
                (
                    instrument_id,
                    candidate.exchange.name,
                    candidate.symbol,
                    candidate.symbol.replace("USDT", ""),
                    start_ms,
                    start_ms,
                ),
            )
            await self.db.execute_commit(
                """
                INSERT OR IGNORE INTO market_snapshots (
                    snapshot_id, instrument_id, timestamp_ms, last_price, mark_price, index_price,
                    bid1_price, ask1_price, spread_bps, turnover_24h_usdt, price_change_24h_pct,
                    funding_rate, next_funding_time_ms, atr_15m, atr_1h, rvol_15m, rsi_15m,
                    feature_schema_version, features_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'FEATURE_SCHEMA_V1', '{}')
                """,
                (
                    snapshot_id,
                    instrument_id,
                    candidate.context.snapshot_timestamp_ms,
                    candidate.context.last_price,
                    candidate.context.mark_price,
                    candidate.context.index_price,
                    candidate.context.bid1_price,
                    candidate.context.ask1_price,
                    candidate.context.spread_bps,
                    candidate.context.turnover_24h_usdt,
                    candidate.context.price_change_24h_pct,
                    candidate.context.funding_rate,
                    candidate.context.next_funding_time_ms,
                    candidate.context.atr_15m,
                    candidate.context.atr_1h,
                    candidate.context.rvol_15m,
                    candidate.context.rsi_15m,
                ),
            )
            await self.db.execute_commit(
                """
                INSERT OR IGNORE INTO scanner_candidates (
                    candidate_id, scan_cycle_id, instrument_id, snapshot_id, exchange, symbol,
                    primary_category, secondary_categories_json, directional_bias,
                    deterministic_score, state_hash, queue_status, created_at_ms, expires_at_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, '[]', ?, ?, ?, 'DISPATCHED', ?, ?)
                """,
                (
                    candidate.candidate_id,
                    candidate.scan_cycle_id,
                    instrument_id,
                    snapshot_id,
                    candidate.exchange.name,
                    candidate.symbol,
                    candidate.primary_category.name,
                    candidate.directional_bias.name,
                    candidate.deterministic_score,
                    candidate.state_hash,
                    candidate.created_at_ms,
                    candidate.expires_at_ms,
                ),
            )
            await self.db.execute_commit(
                """
                INSERT OR IGNORE INTO agent_runs (
                    pipeline_run_id, candidate_id, instrument_id, snapshot_id,
                    run_type, status, final_stage_reached, started_at_ms
                ) VALUES (?, ?, ?, ?, 'DISCOVERY_PIPELINE', 'RUNNING', 'QUEUED', ?)
                """,
                (
                    run_id,
                    candidate.candidate_id,
                    instrument_id,
                    snapshot_id,
                    start_ms,
                ),
            )
        except Exception as e:
            logger.warning("Could not persist agent_runs start record: %s", e)

    async def _finalize_run(
        self,
        run_id: str,
        candidate: ScannerCandidate,
        status: PipelineStatus,
        final_stage: PipelineStage,
        start_time: float,
        scout_out: Optional[ScoutOutput] = None,
        analyst_out: Optional[AnalystOutput] = None,
        sniper_out: Optional[SniperOutput] = None,
        risk_out: Optional[RiskOutput] = None,
        abort_reason: Optional[str] = None,
    ) -> PipelineRunResult:
        """Assemble PipelineRunResult and commit run telemetry to SQLite."""
        total_ms = (time.perf_counter() - start_time) * 1000.0
        now_ms = int(time.time() * 1000)

        # Update SQLite audit record
        if self.db and self.db.is_connected:
            try:
                await self.db.execute_commit(
                    """
                    UPDATE agent_runs
                    SET status = ?, final_stage_reached = ?, total_inference_latency_ms = ?,
                        abort_reason = ?, completed_at_ms = ?
                    WHERE pipeline_run_id = ?
                    """,
                    (status.name, final_stage.name, round(total_ms, 2), abort_reason, now_ms, run_id),
                )
            except Exception as e:
                logger.warning("Could not update agent_runs completion record: %s", e)

        logger.info(
            "Pipeline run %s finished in %.2f ms (Status: %s, Stage: %s)",
            run_id,
            total_ms,
            status.name,
            final_stage.name,
        )

        return PipelineRunResult(
            pipeline_run_id=run_id,
            status=status,
            final_stage=final_stage,
            scout_output=scout_out,
            analyst_output=analyst_out,
            sniper_output=sniper_out,
            risk_output=risk_out,
            total_latency_ms=round(total_ms, 2),
            abort_reason=abort_reason,
        )
