"""Agent 1: SCOUT opportunity discovery and ranking module."""

import time
from typing import Optional

from quantum.agents.contracts import ScoutInput, ScoutOutput
from quantum.config.settings import MLConfig
from quantum.core.logging import get_logger
from quantum.domain.enums import AgentAction, AgentId, InferenceMode
from quantum.ml.registry import ModelRegistry

logger = get_logger("agents.scout")


class ScoutAgent:
    """Agent 1: Evaluates Stage D candidates using calibrated probability or deterministic fallback."""

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        config: Optional[MLConfig] = None,
        min_probability: Optional[float] = None,
        max_wick_trap: Optional[float] = None,
        fallback_policy: Optional[str] = None,
    ) -> None:
        self.registry = registry
        cfg = config or MLConfig()
        self.min_probability = min_probability if min_probability is not None else cfg.scout_min_prob
        self.max_wick_trap = max_wick_trap if max_wick_trap is not None else cfg.scout_max_wick_trap
        self.fallback_policy = fallback_policy or cfg.fallback_policy

    async def evaluate(self, input_data: ScoutInput) -> ScoutOutput:
        """Evaluate candidate and produce a validated ScoutOutput."""
        start_time = time.perf_counter()
        candidate = input_data.candidate
        context = candidate.context

        # Check model registry
        active_model = None
        if self.registry:
            active_model = self.registry.get_active_model(
                AgentId.SCOUT, fallback_policy=self.fallback_policy
            )

        wick_trap = context.features.get("wick_trap_ratio", 0.15)

        if active_model is not None:
            # Placeholder for Phase 5 LightGBM C++ booster inference
            model_ver = active_model.model_version
            mode = InferenceMode.LOCAL_ML
            prob = 0.65  # Target placeholder for active ML test
        else:
            # Deterministic quantitative rule baseline
            model_ver = "rule_baseline_v1"
            mode = InferenceMode.FALLBACK_RULE_ONLY
            base_score = candidate.deterministic_score / 100.0
            prob = min(0.95, max(0.40, base_score * (1.0 - 0.35 * wick_trap)))

        # Decision logic
        if prob >= self.min_probability and wick_trap <= self.max_wick_trap:
            action = AgentAction.PROCEED
            abort_reason = None
        else:
            action = AgentAction.SKIP
            if prob < self.min_probability:
                abort_reason = f"Probability estimate {prob:.3f} below threshold {self.min_probability:.3f}"
            else:
                abort_reason = f"Wick trap ratio {wick_trap:.2f} exceeds threshold {self.max_wick_trap:.2f}"

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return ScoutOutput(
            action=action,
            exchange=candidate.exchange,
            symbol=candidate.symbol,
            directional_bias=candidate.directional_bias,
            opportunity_category=candidate.primary_category,
            timeframe="15m",
            probability_estimate=round(prob, 4),
            candidate_score=candidate.deterministic_score,
            supporting_features={
                "rvol_15m": context.rvol_15m,
                "rsi_15m": context.rsi_15m,
                "wick_trap_ratio": wick_trap,
                "spread_bps": context.spread_bps,
            },
            model_version=model_ver,
            inference_mode=mode,
            snapshot_timestamp_ms=context.snapshot_timestamp_ms,
            abort_reason=abort_reason,
        )
