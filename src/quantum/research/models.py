"""Data Models and Enums for Continuous Research Orchestration."""

from enum import Enum
import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field

from quantum.domain.research_contract import ResearchExperimentContract


class DatasetPartitionType(str, Enum):
    """Rigorous classification of data partitions to prevent evidence contamination."""
    TRAIN = "TRAIN"                      # Model calibration and initial hypothesis screening
    VALIDATION = "VALIDATION"            # Hyperparameter confirmation; strictly isolated from training
    ROLLING_OOS = "ROLLING_OOS"          # Walk-forward chronological out-of-sample evaluation folds
    PROSPECTIVE_OOS = "PROSPECTIVE_OOS"  # Forward-running real-time sealed holdout (strictly read-only)


class HypothesisStatus(str, Enum):
    """Centralized lifecycle states for research hypotheses."""
    DRAFT = "DRAFT"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    EVALUATED = "EVALUATED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    ARCHIVED = "ARCHIVED"


class RejectionCategory(str, Enum):
    """Classification of reasons for hypothesis rejection."""
    METHODOLOGICAL_FAILURE = "METHODOLOGICAL_FAILURE"
    STATISTICAL_FAILURE = "STATISTICAL_FAILURE"
    GOVERNANCE_VIOLATION = "GOVERNANCE_VIOLATION"
    REDUNDANT_CONFIGURATION = "REDUNDANT_CONFIGURATION"


class SpecificRejectionReason(str, Enum):
    """Granular failure modes enforced by automatic rejection gates."""
    # Methodological failures
    EXPOSURE_LIMIT_EXCEEDED = "EXPOSURE_LIMIT_EXCEEDED"
    DRAWDOWN_LIMIT_EXCEEDED = "DRAWDOWN_LIMIT_EXCEEDED"
    HOLDING_HORIZON_BREACH = "HOLDING_HORIZON_BREACH"
    TIMEFRAME_MISMATCH = "TIMEFRAME_MISMATCH"
    DATA_LEAKAGE_DETECTED = "DATA_LEAKAGE_DETECTED"
    HOLDOUT_BOUNDARY_VIOLATION = "HOLDOUT_BOUNDARY_VIOLATION"
    LOOKAHEAD_BIAS_DETECTED = "LOOKAHEAD_BIAS_DETECTED"
    
    # Statistical failures
    NEGATIVE_NET_EXPECTANCY = "NEGATIVE_NET_EXPECTANCY"
    SUB_TARGET_DAILY_RETURN = "SUB_TARGET_DAILY_RETURN"
    LOW_PROFIT_FACTOR = "LOW_PROFIT_FACTOR"
    INSUFFICIENT_FREQUENCY = "INSUFFICIENT_FREQUENCY"
    STATISTICALLY_INSIGNIFICANT = "STATISTICALLY_INSIGNIFICANT"
    DEFLATED_SHARPE_REJECTED = "DEFLATED_SHARPE_REJECTED"
    
    # Redundancy
    DUPLICATE_FINGERPRINT = "DUPLICATE_FINGERPRINT"


class DatasetFingerprint(BaseModel):
    """Cryptographic and temporal fingerprint of a dataset partition."""
    model_config = ConfigDict(frozen=True)

    partition_type: DatasetPartitionType
    symbol: str
    timeframe: str
    start_timestamp_ms: int
    end_timestamp_ms: int
    row_count: int
    sha256_hash: str


class ExperimentPriority(BaseModel):
    """Priority scoring to accelerate high-information research."""
    model_config = ConfigDict(frozen=True)

    expected_information_gain: float = Field(ge=0.0, le=1.0, default=0.5)
    estimated_compute_cost: float = Field(gt=0.0, default=1.0)

    @property
    def priority_score(self) -> float:
        """Higher score executes first in the asynchronous research queue."""
        return self.expected_information_gain / (self.estimated_compute_cost + 1e-6)


class ContinuousExperimentConfig(BaseModel):
    """Immutable, fingerprinted specification of an individual research experiment."""
    model_config = ConfigDict(frozen=True)

    experiment_id: str
    hypothesis_id: str
    partition_type: DatasetPartitionType
    symbol: str
    contract: ResearchExperimentContract
    feature_specs: Tuple[str, ...] = Field(default_factory=tuple)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: ExperimentPriority = Field(default_factory=ExperimentPriority)

    @property
    def config_fingerprint(self) -> str:
        """SHA-256 deterministic hash of the experiment parameters and contract."""
        payload = {
            "hypothesis_id": self.hypothesis_id,
            "partition_type": self.partition_type.value,
            "symbol": self.symbol,
            "execution_timeframe": self.contract.execution_timeframe.value,
            "maximum_gross_exposure": self.contract.maximum_gross_exposure,
            "maximum_holding_horizon_minutes": self.contract.maximum_holding_horizon_minutes,
            "exchange": self.contract.exchange_cost_config.exchange,
            "taker_fee_bps": self.contract.exchange_cost_config.taker_fee_bps,
            "maker_fee_bps": self.contract.exchange_cost_config.maker_fee_bps,
            "feature_specs": list(self.feature_specs),
            "parameters": self.parameters,
        }
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


class ExperimentExecutionRecord(BaseModel):
    """Immutable record of an executed experiment, including all rejections."""
    model_config = ConfigDict(frozen=True)

    experiment_id: str
    hypothesis_id: str
    partition_type: DatasetPartitionType
    symbol: str
    dataset_fingerprint: str
    config_fingerprint: str
    executed_at_utc: str
    duration_seconds: float
    
    # Empirical Metrics
    completed_episodes: int
    frequency_daily: float
    win_rate_pct: float
    profit_factor: float
    gross_pnl_usd: float
    net_pnl_usd: float
    net_expectancy_bps: float
    mean_net_daily_return_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    avg_duration_minutes: float
    
    # Acceptance / Rejection Classification
    is_accepted: bool
    rejection_category: Optional[RejectionCategory] = None
    rejection_reasons: List[str] = Field(default_factory=list)
