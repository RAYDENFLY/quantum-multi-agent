"""Continuous Research Mode Addendum Package for QUANTUM Multi-Agent Trading System."""

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
    PartitionLeakageError,
    PROSPECTIVE_HOLDOUT_START_MS,
)
from quantum.research.feature_cache import IntermediateFeatureCache
from quantum.research.registry import CentralizedHypothesisRegistry, RegisteredHypothesisRecord
from quantum.research.rejection import AutomaticRejectionEngine, RejectionEvaluationResult
from quantum.research.orchestrator import ContinuousResearchOrchestrator

__all__ = [
    "ContinuousExperimentConfig",
    "DatasetFingerprint",
    "DatasetPartitionType",
    "ExperimentExecutionRecord",
    "ExperimentPriority",
    "HypothesisStatus",
    "RejectionCategory",
    "SpecificRejectionReason",
    "ContinuousResearchPartitioner",
    "DatasetPartition",
    "HoldoutContaminationError",
    "PartitionLeakageError",
    "PROSPECTIVE_HOLDOUT_START_MS",
    "IntermediateFeatureCache",
    "CentralizedHypothesisRegistry",
    "RegisteredHypothesisRecord",
    "AutomaticRejectionEngine",
    "RejectionEvaluationResult",
    "ContinuousResearchOrchestrator",
]
