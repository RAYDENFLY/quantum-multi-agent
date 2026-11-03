"""Collaborative Six-Agent Strategy Integration Bridge.

Ensures every StrategyConfiguration is evaluated through the established 6-agent
workflow (Scout -> Analyst -> Sniper -> Risk -> Banker -> Orchestrator) using shared
contracts without creating duplicate agents or bypassing Risk/Banker controls.
"""

from typing import Any, Dict, Optional, Tuple

from quantum.agents.analyst import AnalystAgent
from quantum.agents.banker import BankerAgent
from quantum.agents.contracts import (
    AnalystInput,
    AnalystOutput,
    BankerInput,
    BankerOutput,
    PositionExecutionEvent,
    RiskInput,
    RiskOutput,
    ScoutInput,
    ScoutOutput,
    SniperInput,
    SniperOutput,
    TrackedPosition,
)
from quantum.agents.orchestrator import PipelineOrchestrator, PipelineRunResult
from quantum.agents.risk import RiskAgent
from quantum.agents.scout import ScoutAgent
from quantum.agents.sniper import SniperAgent
from quantum.config.settings import MLConfig, RiskConfig
from quantum.domain.enums import (
    AgentAction,
    CandidateCategory,
    ExchangeId,
    ExecutionEventType,
    MarketRegime,
    OrderType,
    PositionLifecycleState,
    TradeSide,
)
from quantum.domain.models import MarketContext, ScannerCandidate
from quantum.strategies.schemas import StrategyConfiguration


class CollaborativeAgentStrategyBridge:
    """Connects declarative StrategyConfigurations to the 6 operational QUANTUM agents."""

    def __init__(self, strategy: StrategyConfiguration) -> None:
        self.strategy = strategy

        # Configure ML thresholds from StrategyConfiguration within MLConfig schema bounds
        r1 = strategy.exit.tp1_multiplier / max(strategy.exit.sl_multiplier, 0.1)
        r2 = strategy.exit.tp2_multiplier / max(strategy.exit.sl_multiplier, 0.1)
        close_pct = strategy.exit.tp1_close_pct if strategy.exit.tp1_close_pct > 0.0 else 0.50

        ml_cfg = MLConfig(
            scout_min_prob=min(0.80, max(0.50, 0.50 + strategy.entry.prob_margin_min * 0.5)),
            scout_max_wick_trap=0.80,
            analyst_min_prob=min(0.85, max(0.50, 0.50 + strategy.entry.prob_margin_min * 0.5)),
            analyst_invalidation_atr_mult=min(3.0, max(1.0, strategy.exit.sl_multiplier)),
            sniper_min_expected_r=0.10,
            sniper_min_gross_rr=1.50,
            sniper_tp1_r_multiple=min(3.5, max(1.2, r1)),
            sniper_tp2_r_multiple=min(6.0, max(2.0, r2)),
            sniper_tp1_close_pct=min(0.80, max(0.20, close_pct)),
        )

        risk_cfg = RiskConfig(
            risk_per_trade_pct=min(0.02, max(0.001, strategy.risk.risk_per_trade_pct)),
            max_symbol_exposure_pct=min(0.30, max(0.05, strategy.risk.max_symbol_exposure_pct)),
            max_total_exposure_pct=min(1.00, max(0.10, strategy.risk.max_total_exposure_pct)),
            max_leverage_per_position=min(5.0, max(1.0, strategy.risk.max_leverage)),
            max_concurrent_positions=min(8, max(1, strategy.risk.max_concurrent_positions)),
            max_total_drawdown_pct=0.15,
            max_daily_loss_pct=0.05,
            min_net_reward_risk=1.50,
            max_spread_bps=25.0,
            max_estimated_slippage_bps=15.0,
        )

        self.scout = ScoutAgent(config=ml_cfg)
        self.analyst = AnalystAgent(config=ml_cfg)
        self.sniper = SniperAgent(config=ml_cfg)
        self.risk = RiskAgent(config=risk_cfg)
        self.banker = BankerAgent(config=ml_cfg)
        self.orchestrator = PipelineOrchestrator(
            scout=self.scout,
            analyst=self.analyst,
            sniper=self.sniper,
            risk=self.risk,
            default_equity_usdt=strategy.risk.initial_equity_usd,
        )

    async def evaluate_signal_through_six_agents(
        self,
        symbol: str,
        side: TradeSide,
        mark_price: float,
        atr: float,
        rvol: float,
        rsi: float,
        timestamp_ms: int,
        current_equity_usdt: float,
        open_positions_count: int,
        total_exposure_usdt: float,
        peak_equity_usdt: float,
    ) -> Dict[str, Any]:
        """Executes a market observation through Scout -> Analyst -> Sniper -> Risk -> Banker."""
        spread_bps = 2.0
        half_spread = mark_price * (spread_bps / 20_000.0)
        ctx = MarketContext(
            exchange=ExchangeId.ASTER,
            symbol=symbol,
            snapshot_timestamp_ms=timestamp_ms,
            last_price=mark_price,
            mark_price=mark_price,
            index_price=mark_price,
            bid1_price=round(mark_price - half_spread, 4),
            ask1_price=round(mark_price + half_spread, 4),
            spread_bps=spread_bps,
            turnover_24h_usdt=50_000_000.0,
            price_change_24h_pct=-2.50,
            funding_rate=0.0001,
            next_funding_time_ms=timestamp_ms + 3_600_000,
            atr_15m=max(atr, mark_price * 0.005),
            atr_1h=max(atr * 1.8, mark_price * 0.009),
            rvol_15m=max(rvol, 1.2),
            rsi_15m=rsi,
            features={
                "wick_trap_ratio": 0.10,
                "strategy_config_hash": float(int(self.strategy.config_hash[:6], 16)),
            },
        )

        candidate = ScannerCandidate(
            candidate_id=f"{self.strategy.strategy_id}_{symbol}_{timestamp_ms}",
            scan_cycle_id=f"scan_{self.strategy.strategy_id}_{timestamp_ms}",
            exchange=ExchangeId.ASTER,
            symbol=symbol,
            primary_category=CandidateCategory.REVERSAL_CANDIDATES,
            directional_bias=side,
            deterministic_score=85.0,
            state_hash=self.strategy.config_hash,
            created_at_ms=timestamp_ms,
            expires_at_ms=timestamp_ms + 300_000,
            context=ctx,
        )

        run_id = f"run_{self.strategy.strategy_id}_{self.strategy.config_hash}_{timestamp_ms}"

        # 1. Scout
        scout_out: ScoutOutput = await self.scout.evaluate(
            ScoutInput(pipeline_run_id=run_id, candidate=candidate)
        )
        # 2. Analyst
        analyst_out: AnalystOutput = await self.analyst.evaluate(
            AnalystInput(pipeline_run_id=run_id, candidate=candidate, scout_output=scout_out)
        )
        # 3. Sniper
        sniper_out: SniperOutput = await self.sniper.evaluate(
            SniperInput(
                pipeline_run_id=run_id,
                candidate=candidate,
                scout_output=scout_out,
                analyst_output=analyst_out,
            )
        )

        risk_out: Optional[RiskOutput] = None
        banker_out: Optional[BankerOutput] = None
        tracked_pos: Optional[TrackedPosition] = None

        if sniper_out.proposal is not None:
            # 4. Risk (Non-bypassable validation with $5.00 min notional and accurate lot_step)
            lot_step = 0.0001 if mark_price > 1000 else 0.01
            risk_out = await self.risk.evaluate(
                RiskInput(
                    pipeline_run_id=run_id,
                    candidate=candidate,
                    proposal=sniper_out.proposal,
                    current_equity_usdt=current_equity_usdt,
                    open_positions_count=open_positions_count,
                    total_exposure_usdt=total_exposure_usdt,
                    peak_equity_usdt=peak_equity_usdt,
                    daily_pnl_usdt=0.0,
                    starting_day_equity_usdt=current_equity_usdt,
                    consecutive_losses_count=0,
                    estimated_slippage_bps=1.0,
                    eval_timestamp_ms=timestamp_ms,
                    lot_step=lot_step,
                    min_notional_usdt=self.strategy.risk.min_notional_usdt,
                )
            )

            # 5. Banker (Position lifecycle initialization & entry fill handling)
            if risk_out.decision.decision == AgentAction.APPROVED:
                qty = risk_out.decision.approved_quantity
                prop = sniper_out.proposal
                pos = TrackedPosition(
                    position_id=f"pos_{prop.proposal_id}",
                    symbol=symbol,
                    side=side,
                    state=PositionLifecycleState.PENDING_OPEN,
                    entry_price=prop.entry_price,
                    initial_quantity=qty,
                    remaining_quantity=qty,
                    current_stop_loss=prop.stop_loss,
                    take_profit_1=prop.take_profit_1,
                    take_profit_2=prop.take_profit_2,
                    created_at_ms=timestamp_ms,
                    updated_at_ms=timestamp_ms,
                )
                entry_ev = PositionExecutionEvent(
                    event_id=f"ev_entry_{timestamp_ms}",
                    position_id=pos.position_id,
                    event_type=ExecutionEventType.ENTRY_FILL,
                    fill_price=prop.entry_price,
                    fill_quantity=qty,
                    timestamp_ms=timestamp_ms,
                    sequence_number=1,
                )
                tracked_pos, banker_out = self.banker.handle_execution_event(pos, entry_ev)

        return {
            "strategy_id": self.strategy.strategy_id,
            "config_hash": self.strategy.config_hash,
            "pipeline_run_id": run_id,
            "scout_action": scout_out.action.name,
            "analyst_action": analyst_out.action.name,
            "analyst_regime": analyst_out.market_regime.name,
            "sniper_action": sniper_out.action.name,
            "risk_decision": risk_out.decision.decision.name if risk_out else "SKIPPED",
            "approved_notional_usdt": risk_out.decision.notional_usdt if risk_out else 0.0,
            "banker_state": tracked_pos.state.name if tracked_pos else "NONE",
            "banker_action": banker_out.action.name if banker_out else "NONE",
        }
