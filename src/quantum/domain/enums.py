"""Canonical enumerations for QUANTUM Multi-Agent Trading Desk."""

from enum import Enum, IntEnum


class ExchangeId(str, Enum):
    """Supported cryptocurrency derivatives exchanges."""
    BYBIT = "BYBIT"
    ASTER = "ASTER"


# Alias for concise reference across exchange adapters
Exchange = ExchangeId


class TradeSide(str, Enum):
    """Directional position bias or order side."""
    LONG = "LONG"
    SHORT = "SHORT"


class OrderType(str, Enum):
    """Order execution classification."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_MARKET = "STOP_MARKET"


class CandidateCategory(str, Enum):
    """Seven Stage C scanner opportunity buckets."""
    TOP_GAINERS = "TOP_GAINERS"
    TOP_LOSERS = "TOP_LOSERS"
    VOLUME_SURGE = "VOLUME_SURGE"
    MOMENTUM_ACCELERATION = "MOMENTUM_ACCELERATION"
    VOLATILITY_EXPANSION = "VOLATILITY_EXPANSION"
    REVERSAL_CANDIDATES = "REVERSAL_CANDIDATES"
    BREAKOUT_CANDIDATES = "BREAKOUT_CANDIDATES"


class MarketRegime(str, Enum):
    """Structural macro market condition classified by Analyst."""
    TREND_IMPULSE = "TREND_IMPULSE"
    MEAN_REVERT_RANGE = "MEAN_REVERT_RANGE"
    HIGH_VOL_EXHAUSTION = "HIGH_VOL_EXHAUSTION"
    LOW_LIQ_CHOP = "LOW_LIQ_CHOP"


class AgentId(str, Enum):
    """Five specialized local quantitative agents."""
    SCOUT = "SCOUT"
    ANALYST = "ANALYST"
    SNIPER = "SNIPER"
    RISK = "RISK"
    BANKER = "BANKER"


class AgentAction(str, Enum):
    """Action decision output from an agent evaluation."""
    PROCEED = "PROCEED"
    SKIP = "SKIP"
    PROPOSE_TRADE = "PROPOSE_TRADE"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    HOLD = "HOLD"
    TIGHTEN_STOP = "TIGHTEN_STOP"
    EARLY_EXIT = "EARLY_EXIT"
    CLOSE_POSITION = "CLOSE_POSITION"


class InferenceMode(str, Enum):
    """Operating mode used for an agent run."""
    LOCAL_ML = "LOCAL_ML"
    FALLBACK_RULE_ONLY = "FALLBACK_RULE_ONLY"
    DETERMINISTIC_PYTHON = "DETERMINISTIC_PYTHON"


class ModelStatus(str, Enum):
    """Lifecycle stage for versioned model artifacts."""
    CANDIDATE = "CANDIDATE"
    PRODUCTION = "PRODUCTION"
    ARCHIVED = "ARCHIVED"
    REJECTED = "REJECTED"


class PipelineStage(str, Enum):
    """Current step within the 5-agent pipeline execution."""
    QUEUED = "QUEUED"
    FEATURE_EXTRACTION = "FEATURE_EXTRACTION"
    SCOUT = "SCOUT"
    ANALYST = "ANALYST"
    SNIPER = "SNIPER"
    RISK = "RISK"
    EXECUTION_PENDING = "EXECUTION_PENDING"
    POSITION_ACTIVE = "POSITION_ACTIVE"
    BANKER_MONITORING = "BANKER_MONITORING"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"


class PipelineStatus(str, Enum):
    """Overall outcome of a pipeline run."""
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    APPROVED = "APPROVED"
    SKIP_EXPIRED = "SKIP_EXPIRED"
    SKIP_FEATURE_INVALID = "SKIP_FEATURE_INVALID"
    SKIP_SCOUT = "SKIP_SCOUT"
    SKIP_ANALYST = "SKIP_ANALYST"
    SKIP_SNIPER = "SKIP_SNIPER"
    VETO_RISK = "VETO_RISK"
    ERROR = "ERROR"


class EventPriority(IntEnum):
    """Priority lanes for EventBus message dispatch."""
    P0 = 0  # Critical: Risk decisions, emergency cancellations
    P1 = 1  # Pipeline: Stage transitions, proposals, candidates
    P2 = 2  # Telemetry: Ticker updates, scan summaries, progress


class PositionLifecycleState(str, Enum):
    """Deterministic position lifecycle states managed by Banker."""
    PENDING_OPEN = "PENDING_OPEN"
    OPEN = "OPEN"
    PARTIALLY_CLOSED = "PARTIALLY_CLOSED"
    CLOSED = "CLOSED"


class ExecutionEventType(str, Enum):
    """Confirmed execution events driving Banker state transitions."""
    ENTRY_FILL = "ENTRY_FILL"
    TP1_FILL = "TP1_FILL"
    TP2_FILL = "TP2_FILL"
    SL_FILL = "SL_FILL"
    MANUAL_CLOSE = "MANUAL_CLOSE"


class Timeframe(str, Enum):
    """Standardized multi-timeframe candle intervals."""
    M1 = "1m"
    M3 = "3m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H2 = "2h"
    H4 = "4h"
    D1 = "1d"


class ConnectionState(str, Enum):
    """WebSocket connection lifecycle states."""
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    DEGRADED = "DEGRADED"
    RECONNECTING = "RECONNECTING"
    STOPPING = "STOPPING"


class OrderBookSyncStatus(str, Enum):
    """L2 Order book synchronization states."""
    INITIALIZING = "INITIALIZING"
    SYNCHRONIZED = "SYNCHRONIZED"
    STALE = "STALE"
    INVALID = "INVALID"
    RESYNCING = "RESYNCING"


class ContractStatus(str, Enum):
    """Trading status of perpetual instruments."""
    TRADING = "TRADING"
    SETTLING = "SETTLING"
    DELIVERING = "DELIVERING"
    CLOSED = "CLOSED"
    HALTED = "HALTED"


class ContractType(str, Enum):
    """Derivatives contract type classification."""
    PERPETUAL = "PERPETUAL"
    LINEAR_PERPETUAL = "LINEAR_PERPETUAL"

