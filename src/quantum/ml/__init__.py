"""Machine learning models, registry, and validation module."""

from quantum.ml.baselines import (
    BaselineModelFactory,
    MajorityClassBaseline,
    PriorProbabilityBaseline,
)
from quantum.ml.contracts import (
    DatasetSampleTrace,
    ExperimentManifest,
    RESEARCH_FEATURE_SCHEMA_HASH,
    RESEARCH_STATIONARY_FEATURES,
    TargetClass,
    TargetConfiguration,
)
from quantum.ml.evaluation import (
    EconomicSimulationContract,
    ModelEvaluationContract,
)
from quantum.ml.preprocessor import SpecialistPreprocessor
from quantum.ml.registry import (
    FEATURE_SCHEMA_V1,
    FEATURE_SCHEMA_V1_HASH,
    ModelManifest,
    ModelMetadata,
    ModelRegistry,
    ModelRegistryError,
    ModelUnavailableError,
)
from quantum.ml.validation import PurgedWalkForwardSplitter

__all__ = [
    "FEATURE_SCHEMA_V1",
    "FEATURE_SCHEMA_V1_HASH",
    "ModelManifest",
    "ModelMetadata",
    "ModelRegistry",
    "ModelRegistryError",
    "ModelUnavailableError",
    "TargetClass",
    "RESEARCH_STATIONARY_FEATURES",
    "RESEARCH_FEATURE_SCHEMA_HASH",
    "TargetConfiguration",
    "DatasetSampleTrace",
    "ExperimentManifest",
    "PurgedWalkForwardSplitter",
    "SpecialistPreprocessor",
    "MajorityClassBaseline",
    "PriorProbabilityBaseline",
    "BaselineModelFactory",
    "ModelEvaluationContract",
    "EconomicSimulationContract",
]
