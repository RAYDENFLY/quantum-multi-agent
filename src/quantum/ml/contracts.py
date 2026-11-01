"""Machine learning data contracts and experiment manifests for Phase 5.3.

Provides formal data contracts, sample-level traceability schemas,
and immutable experiment manifests to guarantee end-to-end reproducibility.
"""

from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from quantum.domain.enums import Exchange, Timeframe
from quantum.features.schema import RESEARCH_FEATURE_COLUMNS


class TargetClass(int, Enum):
    """Discrete target classes for triple-barrier classification."""
    TP = 1
    SL = -1
    TIME_EXPIRATION = 0


# Exact 36 stationary features (excluding timestamps)
RESEARCH_STATIONARY_FEATURES: List[str] = [
    c for c in RESEARCH_FEATURE_COLUMNS if c not in ("open_time_ms", "close_time_ms")
]

RESEARCH_FEATURE_SCHEMA_HASH: str = hashlib.sha256(
    ",".join(RESEARCH_STATIONARY_FEATURES).encode("utf-8")
).hexdigest()


class TargetConfiguration(BaseModel):
    """Specification of triple-barrier target parameters."""
    model_config = ConfigDict(frozen=True)

    timeframe: Timeframe = Timeframe.M5
    horizon_bars: int = 12
    maximum_holding_minutes: int = 60
    volatility_lookback: int = 20
    barrier_multiplier: float = 1.5
    volatility_type: str = "RETURN_VOLATILITY"
    min_volatility: float = 1e-6
    ambiguity_policy: str = "CONSERVATIVE_EXCLUDE"


class DatasetSampleTrace(BaseModel):
    """Traceability metadata linking each sample to raw and canonical origins."""
    model_config = ConfigDict(frozen=True)

    exchange: Exchange
    symbol: str
    timeframe: Timeframe
    feature_open_time_ms: int
    label_open_time_ms: int
    target_class: TargetClass
    dataset_version: str = "DATASET_V1"
    feature_version: str = "RESEARCH_V1"
    target_config_hash: str


class ExperimentManifest(BaseModel):
    """Immutable manifest completely defining an ML specialist experiment."""
    model_config = ConfigDict(frozen=True)

    experiment_id: str
    model_name: str
    specialist_instrument: str
    exchange: Exchange = Exchange.ASTER
    timeframe: Timeframe = Timeframe.M5
    dataset_version: str = "DATASET_V1"
    feature_version: str = "RESEARCH_V1"
    feature_schema_hash: str
    feature_names: List[str]
    target_config: TargetConfiguration
    partition_hashes: Dict[str, str] = Field(default_factory=dict)
    validation_folds: int = 5
    purge_bars: int = 12
    embargo_bars: int = 24
    random_seed: int = 42
    instrument_seed: int = 42
    software_dependencies: Dict[str, str] = Field(default_factory=dict)
    created_at_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def compute_manifest_hash(self) -> str:
        """Calculate canonical SHA-256 hash of the experiment manifest."""
        manifest_dict = self.model_dump(mode="json")
        canonical_json = json.dumps(manifest_dict, sort_keys=True)
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
