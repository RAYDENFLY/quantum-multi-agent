"""Centralized Research Hypothesis Registry with Versioning and Lifecycle Tracking."""

from datetime import datetime, timezone
import threading
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from quantum.research.models import HypothesisStatus
from quantum.strategies.hypothesis_engine import (
    HYPOTHESIS_REGISTRY,
    HypothesisSpecification,
)


class RegisteredHypothesisRecord(BaseModel):
    """Metadata tracking of an active, queued, or evaluated research hypothesis."""
    specification: HypothesisSpecification
    status: HypothesisStatus = HypothesisStatus.QUEUED
    registered_at_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_updated_at_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    total_evaluations: int = 0
    accepted_evaluations: int = 0
    rejected_evaluations: int = 0
    best_mean_daily_return_pct: Optional[float] = None
    best_profit_factor: Optional[float] = None


class CentralizedHypothesisRegistry:
    """Thread-safe centralized registry for continuous alpha research discovery."""

    def __init__(self) -> None:
        self._records: Dict[str, RegisteredHypothesisRecord] = {}
        self._lock = threading.Lock()
        self._seed_default_hypotheses()

    def _seed_default_hypotheses(self) -> None:
        """Seeds the registry with the canonical hypotheses from M5.11."""
        for hyp_id, spec in HYPOTHESIS_REGISTRY.items():
            self._records[hyp_id] = RegisteredHypothesisRecord(
                specification=spec,
                status=HypothesisStatus.QUEUED,
            )

    def register_hypothesis(self, spec: HypothesisSpecification) -> None:
        """Registers a new hypothesis into the continuous discovery registry."""
        with self._lock:
            if spec.hypothesis_id in self._records:
                # Update existing specification metadata
                rec = self._records[spec.hypothesis_id]
                rec.specification = spec
                rec.last_updated_at_utc = datetime.now(timezone.utc).isoformat()
            else:
                self._records[spec.hypothesis_id] = RegisteredHypothesisRecord(
                    specification=spec,
                    status=HypothesisStatus.QUEUED,
                )

    def update_status(self, hypothesis_id: str, status: HypothesisStatus) -> None:
        """Updates the lifecycle state of a hypothesis."""
        with self._lock:
            if hypothesis_id in self._records:
                rec = self._records[hypothesis_id]
                rec.status = status
                rec.last_updated_at_utc = datetime.now(timezone.utc).isoformat()

    def record_evaluation_outcome(
        self,
        hypothesis_id: str,
        is_accepted: bool,
        mean_net_daily_return_pct: float,
        profit_factor: float,
    ) -> None:
        """Updates performance tracking statistics for a hypothesis."""
        with self._lock:
            if hypothesis_id in self._records:
                rec = self._records[hypothesis_id]
                rec.total_evaluations += 1
                if is_accepted:
                    rec.accepted_evaluations += 1
                    rec.status = HypothesisStatus.ACCEPTED
                else:
                    rec.rejected_evaluations += 1
                    if rec.accepted_evaluations == 0:
                        rec.status = HypothesisStatus.REJECTED

                if rec.best_mean_daily_return_pct is None or mean_net_daily_return_pct > rec.best_mean_daily_return_pct:
                    rec.best_mean_daily_return_pct = mean_net_daily_return_pct
                if rec.best_profit_factor is None or profit_factor > rec.best_profit_factor:
                    rec.best_profit_factor = profit_factor

                rec.last_updated_at_utc = datetime.now(timezone.utc).isoformat()

    def get_hypothesis(self, hypothesis_id: str) -> Optional[HypothesisSpecification]:
        with self._lock:
            rec = self._records.get(hypothesis_id)
            return rec.specification if rec else None

    def list_all(self) -> List[RegisteredHypothesisRecord]:
        with self._lock:
            return list(self._records.values())

    def list_by_status(self, status: HypothesisStatus) -> List[RegisteredHypothesisRecord]:
        with self._lock:
            return [r for r in self._records.values() if r.status == status]
