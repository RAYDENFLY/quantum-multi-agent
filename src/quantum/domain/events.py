"""Typed EventBus payloads, canonical topics, and MessageEnvelope."""

from dataclasses import dataclass
from typing import Any, Dict
from pydantic import BaseModel, ConfigDict, Field

from quantum.domain.enums import EventPriority, PipelineStage, PipelineStatus


# Canonical EventBus Topics
TOPIC_PIPELINE_CANDIDATE_QUEUED = "pipeline.candidate.queued"
TOPIC_PIPELINE_STAGE_COMPLETED = "pipeline.stage.completed"
TOPIC_PIPELINE_PROPOSAL_CREATED = "pipeline.proposal.created"
TOPIC_RISK_DECISION_EVALUATED = "risk.decision.evaluated"
TOPIC_ML_MODEL_HOT_SWAPPED = "ml.model.hot_swapped"
TOPIC_TELEMETRY_SCANNER_COMPLETED = "scanner.cycle.completed"
TOPIC_TELEMETRY_HEALTH = "telemetry.health.updated"

# Market Data Infrastructure Topics (Phase 3)
TOPIC_MARKET_FEED_ALERT = "market.feed.alert"
TOPIC_MARKET_CANDLE_CLOSED = "market.candle.closed"
TOPIC_MARKET_SNAPSHOT = "market.snapshot.created"
TOPIC_MARKET_TICKER = "market.ticker.updated"
TOPIC_MARKET_ORDERBOOK = "market.orderbook.updated"
TOPIC_MARKET_HEALTH = "market.health.updated"


@dataclass(frozen=True, slots=True)
class MessageEnvelope:
    """Standardized envelope header wrapping all inter-agent and pipeline messages."""
    message_id: str
    pipeline_run_id: str
    idempotency_key: str
    source: str
    topic: str
    priority: EventPriority
    created_at_ms: int
    snapshot_timestamp_ms: int
    model_version: str
    payload: Any


class PipelineStageCompletedPayload(BaseModel):
    """Payload emitted when an individual agent completes execution."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    pipeline_run_id: str
    stage: PipelineStage
    status: PipelineStatus
    agent_id: str
    action: str
    latency_ms: float
    summary: Dict[str, Any] = Field(default_factory=dict)


class ModelHotSwappedPayload(BaseModel):
    """Payload emitted when a model version is promoted or loaded."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    agent_id: str
    previous_version: str
    new_version: str
    timestamp_ms: int
