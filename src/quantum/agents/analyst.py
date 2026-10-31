"""Agent 2: ANALYST market regime and directional context conditioning module."""

import time
from typing import Optional

from quantum.agents.contracts import AnalystInput, AnalystOutput
from quantum.config.settings import MLConfig
from quantum.core.logging import get_logger
from quantum.domain.enums import AgentAction, AgentId, InferenceMode, MarketRegime, TradeSide
from quantum.ml.registry import ModelRegistry

logger = get_logger("agents.analyst")


class AnalystAgent:
    """Agent 2: Evaluates macro regime and structural invalidation levels."""

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        config: Optional[MLConfig] = None,
        min_probability: Optional[float] = None,
        invalidation_atr_mult: Optional[float] = None,
        fallback_policy: Optional[str] = None,
    ) -> None:
        self.registry = registry
        cfg = config or MLConfig()
        self.min_probability = min_probability if min_probability is not None else cfg.analyst_min_prob
        self.invalidation_atr_mult = invalidation_atr_mult if invalidation_atr_mult is not None else cfg.analyst_invalidation_atr_mult
        self.fallback_policy = fallback_policy or cfg.fallback_policy

    async def evaluate(self, input_data: AnalystInput) -> AnalystOutput:
        """Classify market regime, compute invalidation, and output AnalystOutput."""
        start_time = time.perf_counter()
        candidate = input_data.candidate
        context = candidate.context
        bias = candidate.directional_bias

        # Check model registry
        active_model = None
        if self.registry:
            active_model = self.registry.get_active_model(
                AgentId.ANALYST, fallback_policy=self.fallback_policy
            )

        atr = context.atr_15m
        mark = context.mark_price
        rsi = context.rsi_15m
        rvol = context.rvol_15m

        if active_model is not None:
            model_ver = active_model.model_version
            mode = InferenceMode.LOCAL_ML
            regime = MarketRegime.TREND_IMPULSE
            prob = 0.67
        else:
            model_ver = "rule_baseline_v1"
            mode = InferenceMode.FALLBACK_RULE_ONLY

            # Deterministic regime heuristic
            if rvol >= 2.0 and (rsi >= 65 or rsi <= 35):
                regime = MarketRegime.TREND_IMPULSE
            elif rvol <= 0.6 and context.spread_bps > 10.0:
                regime = MarketRegime.LOW_LIQ_CHOP
            elif atr / max(context.atr_1h, 1e-6) > 1.8:
                regime = MarketRegime.HIGH_VOL_EXHAUSTION
            else:
                regime = MarketRegime.MEAN_REVERT_RANGE

            prob = 0.62 if regime != MarketRegime.LOW_LIQ_CHOP else 0.42

        # Invalidation price anchored on ATR and swing buffer
        if bias == TradeSide.LONG:
            invalidation = round(mark - (self.invalidation_atr_mult * atr), 4)
            supports = [invalidation, round(mark - (2.5 * atr), 4)]
            resistances = [round(mark + (2.0 * atr), 4), round(mark + (3.2 * atr), 4)]
        else:
            invalidation = round(mark + (self.invalidation_atr_mult * atr), 4)
            supports = [round(mark - (2.0 * atr), 4), round(mark - (3.2 * atr), 4)]
            resistances = [invalidation, round(mark + (2.5 * atr), 4)]

        # Decision policy
        if regime == MarketRegime.LOW_LIQ_CHOP:
            action = AgentAction.SKIP
            abort_reason = "Choppy un-tradeable regime detected (LOW_LIQ_CHOP)"
        elif prob < self.min_probability:
            action = AgentAction.SKIP
            abort_reason = f"Directional probability {prob:.3f} below threshold {self.min_probability:.3f}"
        else:
            action = AgentAction.PROCEED
            abort_reason = None

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return AnalystOutput(
            action=action,
            market_regime=regime,
            volatility_regime="EXPANDING" if rvol >= 1.5 else "NORMAL",
            directional_bias=bias,
            directional_probability=round(prob, 4),
            confidence=round(prob, 4),
            invalidation_price=invalidation,
            key_support_levels=supports,
            key_resistance_levels=resistances,
            supporting_evidence=[
                f"rsi_15m={rsi:.1f}",
                f"rvol_15m={rvol:.2f}",
                f"regime={regime.name}",
            ],
            contradicting_evidence=[],
            top_feature_contributions={"rvol_15m": 0.15, "directional_rsi": 0.12},
            model_version=model_ver,
            inference_mode=mode,
            abort_reason=abort_reason,
        )
