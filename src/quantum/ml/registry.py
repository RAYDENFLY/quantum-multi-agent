"""Local model registry, SHA-256 artifact verification, and schema hash checks."""

import hashlib
import json
from pathlib import Path
import threading
import time
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from quantum.core.logging import get_logger
from quantum.domain.enums import AgentId, ModelStatus
from quantum.storage.database import DatabaseManager

logger = get_logger("ml.registry")

# Canonical 48 features defined in docs/AGENT_PROMPTS.md
FEATURE_SCHEMA_V1: List[str] = [
    # f00..f05: Signed Multi-TF Log Returns
    "ret_5m_1", "ret_5m_3", "ret_15m_1", "ret_15m_4", "ret_15m_16", "ret_1h_4",
    # f06..f11: Signed EMA Structure Distances
    "dist_ema9_5m", "dist_ema21_5m", "dist_ema9_15m", "dist_ema21_15m", "dist_ema50_15m", "dist_ema50_1h",
    # f12..f15: EMA Slope & Alignment Scores
    "slope_ema21_15m", "slope_ema21_1h", "slope_ema50_1h", "mtf_ema_alignment_score",
    # f16..f21: Momentum & Oscillator Regimes
    "directional_rsi_5m", "directional_rsi_15m", "directional_rsi_1h", "macd_hist_slope_15m", "adx_15m", "adx_1h",
    # f22..f27: Volatility & Squeeze Dynamics
    "natr_15m", "natr_1h", "atr_ratio_15m_1h", "bbw_percentile_15m", "tr_atr_ratio_15m", "parkinson_vol_ratio",
    # f28..f33: Volume & Microstructure
    "rvol_5m", "rvol_15m", "volume_zscore_15m", "close_location_value_15m", "wick_trap_ratio", "body_to_range_ratio",
    # f34..f39: Structural Support / Resistance Proximity
    "dist_donchian_high_20", "dist_donchian_low_20", "dist_donchian_high_50", "dist_donchian_low_50", "dist_vwap_24h", "dist_4h_swing_barrier",
    # f40..f43: Order Book & Liquidity Microstructure
    "spread_to_natr_ratio", "book_imbalance_top10", "depth_ratio_025_050", "log_turnover_24h",
    # f44..f47: Perpetual Derivatives & Cross-Asset Context
    "signed_funding_rate_bps", "funding_rate_zscore_30", "mark_index_basis_bps", "btc_beta_correlation_24",
]

FEATURE_SCHEMA_V1_HASH: str = hashlib.sha256(",".join(FEATURE_SCHEMA_V1).encode("utf-8")).hexdigest()


class ModelRegistryError(Exception):
    """Base exception for model registry errors."""
    pass


class IncompatibleSchemaError(ModelRegistryError):
    """Raised when model feature schema hash does not match current canonical schema."""
    pass


class CorruptedModelError(ModelRegistryError):
    """Raised when artifact SHA-256 verification fails or metadata is corrupted."""
    pass


class ModelUnavailableError(ModelRegistryError):
    """Raised when a production model is required but not present in registry."""
    pass


class ModelManifest(BaseModel):
    """Manifest describing a versioned model bundle on disk."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    model_version: str = Field(min_length=1)
    agent_id: AgentId
    algorithm: str = Field(min_length=1)
    feature_schema_hash: str = Field(min_length=16)
    artifact_dir_path: str
    artifact_sha256: str = Field(min_length=16)
    decision_threshold: float = Field(ge=0.0, le=1.0)
    feature_importance: Dict[str, float] = Field(default_factory=dict)
    created_at_ms: int = Field(gt=0)

    @field_validator("feature_schema_hash")
    @classmethod
    def validate_schema_hash(cls, v: str) -> str:
        if v != FEATURE_SCHEMA_V1_HASH:
            raise IncompatibleSchemaError(
                f"Model feature_schema_hash '{v}' does not match canonical FEATURE_SCHEMA_V1_HASH '{FEATURE_SCHEMA_V1_HASH}'"
            )
        return v


class ModelMetadata(BaseModel):
    """Active in-memory representation of registered model."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    model_version: str
    agent_id: AgentId
    algorithm: str
    feature_schema_hash: str
    artifact_dir_path: str
    artifact_sha256: str
    decision_threshold: float
    status: ModelStatus
    feature_importance: Dict[str, float] = Field(default_factory=dict)
    drift_psi_score: float = 0.0
    promoted_at_ms: Optional[int] = None
    created_at_ms: int


class ModelRegistry:
    """Manages versioned quantitative models, checksum verification, and hot-swapping.

    NOTE: No model may claim predictive capability or production readiness without
    passing purged cross-validation in Phase 5. In the absence of a qualified model,
    FALLBACK_RULE_ONLY is the honest and mandatory default.
    """

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        artifacts_root: Optional[Path] = None,
    ) -> None:
        self.db = db_manager
        self.artifacts_root = artifacts_root or Path.home() / ".quantum" / "artifacts"
        self._lock = threading.RLock()
        self._models: Dict[str, ModelMetadata] = {}  # version -> ModelMetadata
        self._active_production: Dict[AgentId, ModelMetadata] = {}  # agent -> active ModelMetadata

    def register_model(self, manifest: ModelManifest, status: ModelStatus = ModelStatus.CANDIDATE) -> ModelMetadata:
        """Register a new model bundle and verify checksum integrity."""
        with self._lock:
            # 1. Verify artifact integrity on disk
            if manifest.artifact_dir_path:
                artifact_dir = Path(manifest.artifact_dir_path)
                if artifact_dir.exists():
                    computed_hash = self.compute_dir_hash(artifact_dir)
                    if computed_hash != manifest.artifact_sha256:
                        raise CorruptedModelError(
                            f"Checksum mismatch for model '{manifest.model_version}': "
                            f"expected {manifest.artifact_sha256}, calculated {computed_hash}"
                        )
                else:
                    logger.warning("Artifact directory does not exist yet: %s", artifact_dir)

            metadata = ModelMetadata(
                model_version=manifest.model_version,
                agent_id=manifest.agent_id,
                algorithm=manifest.algorithm,
                feature_schema_hash=manifest.feature_schema_hash,
                artifact_dir_path=manifest.artifact_dir_path,
                artifact_sha256=manifest.artifact_sha256,
                decision_threshold=manifest.decision_threshold,
                status=status,
                feature_importance=manifest.feature_importance,
                created_at_ms=manifest.created_at_ms,
            )

            self._models[metadata.model_version] = metadata
            if status == ModelStatus.PRODUCTION:
                self._active_production[metadata.agent_id] = metadata

            logger.info("Registered model version %s for agent %s (Status: %s)", metadata.model_version, metadata.agent_id, status)
            return metadata

    def promote_model(self, model_version: str) -> ModelMetadata:
        """Promote a registered model version to PRODUCTION status."""
        with self._lock:
            if model_version not in self._models:
                raise ModelRegistryError(f"Model version '{model_version}' not found in registry")

            existing = self._models[model_version]
            now_ms = int(time.time() * 1000)

            # Demote prior active production model for this agent to ARCHIVED
            current_active = self._active_production.get(existing.agent_id)
            if current_active and current_active.model_version != model_version:
                archived = current_active.model_copy(update={"status": ModelStatus.ARCHIVED})
                self._models[archived.model_version] = archived
                logger.info("Demoted prior model %s to ARCHIVED", archived.model_version)

            promoted_ms = (
                max(now_ms, (current_active.promoted_at_ms or 0) + 1)
                if current_active
                else now_ms
            )
            promoted = existing.model_copy(update={"status": ModelStatus.PRODUCTION, "promoted_at_ms": promoted_ms})
            self._models[model_version] = promoted
            self._active_production[promoted.agent_id] = promoted
            logger.info("Promoted model %s to PRODUCTION for agent %s", model_version, promoted.agent_id)
            return promoted

    def rollback_promotion(self, agent_id: AgentId) -> Optional[ModelMetadata]:
        """Rollback active production model for an agent to the previously archived model.

        If no prior archived model exists, cleanly reverts agent to FALLBACK_RULE_ONLY (None).
        """
        with self._lock:
            current_active = self._active_production.get(agent_id)
            if current_active is not None:
                # Mark current failing production model as REJECTED
                rejected = current_active.model_copy(update={"status": ModelStatus.REJECTED})
                self._models[rejected.model_version] = rejected
                del self._active_production[agent_id]
                logger.warning("Rolled back model %s; demoted to REJECTED", rejected.model_version)

            # Find most recently promoted archived model for this agent
            archived_models = [
                m
                for m in self._models.values()
                if m.agent_id == agent_id and m.status == ModelStatus.ARCHIVED
            ]
            if not archived_models:
                logger.info("No prior archived model for agent %s; active model reverted to rule fallback", agent_id)
                return None

            # Sort by promoted_at_ms descending, tie-breaking by created_at_ms descending
            archived_models.sort(
                key=lambda m: (m.promoted_at_ms or 0, m.created_at_ms),
                reverse=True,
            )
            restored = archived_models[0].model_copy(update={"status": ModelStatus.PRODUCTION})
            self._models[restored.model_version] = restored
            self._active_production[agent_id] = restored
            logger.info("Restored prior model %s to PRODUCTION for agent %s", restored.model_version, agent_id)
            return restored

    def get_active_model(self, agent_id: AgentId, fallback_policy: str = "FALLBACK_RULE_ONLY") -> Optional[ModelMetadata]:
        """Look up active production model or evaluate fallback semantics."""
        with self._lock:
            model = self._active_production.get(agent_id)
            if model is not None:
                return model

            if fallback_policy == "FALLBACK_RULE_ONLY":
                return None  # Deterministic rule baseline active

            raise ModelUnavailableError(
                f"No PRODUCTION model registered for agent {agent_id} and policy is STRICT_ML_ONLY"
            )

    def list_models(self, agent_id: Optional[AgentId] = None) -> List[ModelMetadata]:
        """List all registered models, optionally filtered by agent."""
        with self._lock:
            if agent_id is not None:
                return [m for m in self._models.values() if m.agent_id == agent_id]
            return list(self._models.values())

    @staticmethod
    def compute_dir_hash(directory: Path) -> str:
        """Compute composite deterministic SHA-256 checksum over directory contents."""
        hasher = hashlib.sha256()
        files = sorted(directory.glob("**/*"))
        for file_path in files:
            if file_path.is_file():
                hasher.update(file_path.name.encode("utf-8"))
                with open(file_path, "rb") as f:
                    while chunk := f.read(65536):
                        hasher.update(chunk)
        return hasher.hexdigest()
