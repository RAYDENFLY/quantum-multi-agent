"""Agent 3: SNIPER entry, TP/SL barrier geometry, and trade proposal generation module."""

import time
from typing import Optional

from quantum.agents.contracts import SniperInput, SniperOutput
from quantum.config.settings import MLConfig
from quantum.core.logging import get_logger
from quantum.domain.enums import (
    AgentAction,
    AgentId,
    InferenceMode,
    OrderType,
    TradeSide,
)
from quantum.domain.models import TradeProposal
from quantum.ml.registry import ModelRegistry

logger = get_logger("agents.sniper")


class SniperAgent:
    """Agent 3: Optimizes entry and exit barrier geometry grounded on ATR and mark prices."""

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        config: Optional[MLConfig] = None,
        min_expected_r: Optional[float] = None,
        min_gross_rr: Optional[float] = None,
        tp1_r_multiple: Optional[float] = None,
        tp2_r_multiple: Optional[float] = None,
        tp1_close_pct: Optional[float] = None,
        fallback_policy: Optional[str] = None,
    ) -> None:
        self.registry = registry
        cfg = config or MLConfig()
        self.min_expected_r = min_expected_r if min_expected_r is not None else cfg.sniper_min_expected_r
        self.min_gross_rr = min_gross_rr if min_gross_rr is not None else cfg.sniper_min_gross_rr
        self.tp1_r_multiple = tp1_r_multiple if tp1_r_multiple is not None else cfg.sniper_tp1_r_multiple
        self.tp2_r_multiple = tp2_r_multiple if tp2_r_multiple is not None else cfg.sniper_tp2_r_multiple
        self.tp1_close_pct = tp1_close_pct if tp1_close_pct is not None else cfg.sniper_tp1_close_pct
        self.fallback_policy = fallback_policy or cfg.fallback_policy

    async def evaluate(self, input_data: SniperInput) -> SniperOutput:
        """Construct tick-rounded trade proposal and evaluate expected net return."""
        start_time = time.perf_counter()
        candidate = input_data.candidate
        context = candidate.context
        analyst = input_data.analyst_output
        side = candidate.directional_bias
        atr = context.atr_15m
        mark = context.mark_price

        # Check model registry
        active_model = None
        if self.registry:
            active_model = self.registry.get_active_model(
                AgentId.SNIPER, fallback_policy=self.fallback_policy
            )

        model_ver = active_model.model_version if active_model else "rule_baseline_v1"
        mode = InferenceMode.LOCAL_ML if active_model else InferenceMode.FALLBACK_RULE_ONLY

        # Deterministic tick-grounded ATR price geometry
        if side == TradeSide.LONG:
            entry = round(context.bid1_price, 4)
            # Anchor stop strictly below invalidation and at least 1.0 ATR
            stop = round(min(analyst.invalidation_price, entry - (1.25 * atr)), 4)
            stop_dist = max(entry - stop, 0.0001)
            tp1 = round(entry + (self.tp1_r_multiple * stop_dist), 4)
            tp2 = round(entry + (self.tp2_r_multiple * stop_dist), 4)
            zone_low = round(entry - (0.15 * stop_dist), 4)
            zone_high = round(entry + (0.05 * stop_dist), 4)
        else:  # SHORT
            entry = round(context.ask1_price, 4)
            stop = round(max(analyst.invalidation_price, entry + (1.25 * atr)), 4)
            stop_dist = max(stop - entry, 0.0001)
            tp1 = round(entry - (self.tp1_r_multiple * stop_dist), 4)
            tp2 = round(entry - (self.tp2_r_multiple * stop_dist), 4)
            zone_low = round(entry - (0.05 * stop_dist), 4)
            zone_high = round(entry + (0.15 * stop_dist), 4)

        # Reward to risk ratio
        gross_rr = round(((self.tp1_r_multiple * self.tp1_close_pct) + (self.tp2_r_multiple * (1.0 - self.tp1_close_pct))), 2)
        prob_tp1 = 0.62
        prob_tp2 = 0.44

        # Net expected return after estimated friction (fees ~0.08R)
        friction_r = 0.08
        ev_net_r = round(
            (prob_tp1 * self.tp1_close_pct * self.tp1_r_multiple)
            + (prob_tp2 * (1.0 - self.tp1_close_pct) * self.tp2_r_multiple)
            - ((1.0 - prob_tp1) * 1.0)
            - friction_r,
            3,
        )

        proposal: Optional[TradeProposal] = None
        abort_reason: Optional[str] = None

        if ev_net_r >= self.min_expected_r and gross_rr >= self.min_gross_rr:
            action = AgentAction.PROPOSE_TRADE
            now_ms = int(time.time() * 1000)
            proposal = TradeProposal(
                proposal_id=f"prop_{candidate.candidate_id}_{now_ms}",
                pipeline_run_id=input_data.pipeline_run_id,
                exchange=candidate.exchange,
                symbol=candidate.symbol,
                side=side,
                order_type=OrderType.LIMIT,
                reference_mark_price=mark,
                entry_price=entry,
                entry_zone_low=zone_low,
                entry_zone_high=zone_high,
                stop_loss=stop,
                take_profit_1=tp1,
                take_profit_2=tp2,
                tp1_close_pct=self.tp1_close_pct,
                estimated_reward_risk=gross_rr,
                expected_net_r=ev_net_r,
                prob_tp1_before_sl=prob_tp1,
                prob_tp2_before_sl=prob_tp2,
                expected_holding_minutes=120,
                rationale=(
                    f"LIMIT entry at {entry}; SL={stop} (anchored on invalidation {analyst.invalidation_price}); "
                    f"TP1={tp1} ({self.tp1_r_multiple:.1f}R), TP2={tp2} ({self.tp2_r_multiple:.1f}R); "
                    f"blended gross R:R={gross_rr}; net E[R]={ev_net_r:+.2f}R"
                ),
                market_regime=analyst.market_regime,
                invalidation_price=analyst.invalidation_price,
                sniper_model_version=model_ver,
                created_at_ms=now_ms,
            )
        else:
            action = AgentAction.SKIP
            abort_reason = f"Expected net return {ev_net_r:.2f}R below minimum threshold {self.min_expected_r:.2f}R"

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return SniperOutput(
            action=action,
            exchange=candidate.exchange,
            symbol=candidate.symbol,
            side=side,
            order_type=OrderType.LIMIT,
            reference_mark_price=mark,
            entry_price=entry,
            entry_zone_low=zone_low,
            entry_zone_high=zone_high,
            stop_loss=stop,
            take_profit_1=tp1,
            take_profit_2=tp2,
            tp1_close_pct=0.50,
            estimated_reward_risk=gross_rr,
            expected_net_r=ev_net_r,
            prob_tp1_before_sl=prob_tp1,
            prob_tp2_before_sl=prob_tp2,
            expected_holding_minutes=120,
            rationale=f"ATR barrier evaluation (Net EV: {ev_net_r:+.2f}R)",
            confidence=0.62,
            model_version=model_ver,
            inference_mode=mode,
            proposal=proposal,
            abort_reason=abort_reason,
        )
