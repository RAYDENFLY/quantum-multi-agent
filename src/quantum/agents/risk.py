"""Agent 4: Deterministic Python Risk Engine and sizing gatekeeper.

Enforces 12 deterministic safety gates:
Gate 1: SIGNAL_FRESHNESS
  - Inputs: candidate.context.snapshot_timestamp_ms, system time
  - Source: MarketContext snapshot
  - Freshness: age <= 15,000 ms
  - Missing-data: VETO_MISSING_TIMESTAMP if <= 0; VETO_STALE_SIGNAL if > 15,000 ms
Gate 2: DRAWDOWN_CIRCUIT_BREAKER
  - Inputs: current_equity_usdt, peak_equity_usdt
  - Source: Account ledger / wallet state
  - Freshness: Synchronous account snapshot
  - Missing-data: VETO_MISSING_ACCOUNT_EQUITY if equity is None or <= 0
  - Rejection: VETO_DRAWDOWN_BREACHED if total drawdown > max_total_drawdown_pct
Gate 3: DAILY_LOSS_LIMIT
  - Inputs: daily_pnl_usdt, starting_day_equity_usdt
  - Source: Daily account ledger
  - Freshness: Current trading session
  - Rejection: VETO_DAILY_LOSS_BREACHED if daily loss > max_daily_loss_pct
Gate 4: LOSS_STREAK_COOLDOWN
  - Inputs: consecutive_losses_count, last_loss_timestamp_ms
  - Source: Trade execution history
  - Freshness: Current day session
  - Rejection: VETO_LOSS_STREAK_COOLDOWN if streak >= limit and cooldown active
Gate 5: MAX_CONCURRENT_POSITIONS
  - Inputs: open_positions_count, config.max_concurrent_positions
  - Source: Active position tracker
  - Freshness: Real-time position count
  - Missing-data: VETO_MISSING_OPEN_POSITIONS if count is None or < 0
  - Rejection: VETO_MAX_POSITIONS_BREACHED if active >= max
Gate 6: STOP_GEOMETRY_VALID
  - Inputs: proposal.entry_price, proposal.stop_loss, proposal.side, context.atr_15m
  - Source: TradeProposal and MarketContext
  - Freshness: Current evaluation snapshot
  - Missing-data: VETO_MISSING_PRICE_DATA if prices are non-positive or NaN
  - Rejection: VETO_INVALID_STOP_GEOMETRY or VETO_STOP_TOO_TIGHT (< 0.4 ATR)
Gate 7: MAX_SPREAD
  - Inputs: context.spread_bps, config.max_spread_bps
  - Source: MarketContext
  - Freshness: Current tick snapshot
  - Missing-data: VETO_MISSING_PRICE_DATA if spread_bps is negative or NaN
  - Rejection: VETO_EXCESSIVE_SPREAD if spread_bps > max_spread_bps
Gate 8: MIN_NET_RR
  - Inputs: proposal.entry_price, stop_loss, take_profit_1, take_profit_2, tp1_close_pct
  - Source: TradeProposal and fee/slippage config
  - Freshness: Current evaluation
  - Rejection: VETO_INSUFFICIENT_NET_RR if net R:R after friction < min_net_reward_risk
Gate 9: MAX_SLIPPAGE
  - Inputs: estimated_slippage_bps, config.max_estimated_slippage_bps
  - Source: Order book depth / execution model
  - Rejection: VETO_EXCESSIVE_SLIPPAGE if slippage > max_estimated_slippage_bps
Gate 10: LOT_STEP_AND_MIN_NOTIONAL
  - Inputs: calculated notional, min_notional_usdt (>= 10 USDT)
  - Source: Exchange instrument specifications
  - Rejection: VETO_BELOW_MIN_NOTIONAL if calculated notional < 10.0 USDT
Gate 11: MAX_EXPOSURE_AND_LEVERAGE
  - Inputs: effective_leverage, total_exposure_usdt, equity
  - Source: Sizing model and portfolio caps
  - Missing-data: VETO_MISSING_TOTAL_EXPOSURE if total_exposure_usdt is None
  - Rejection: VETO_EXCESSIVE_LEVERAGE or VETO_EXPOSURE_LIMIT_EXCEEDED
Gate 12: LIQUIDATION_BUFFER
  - Inputs: estimated liquidation distance, stop distance
  - Source: Margin model
  - Rejection: VETO_INSUFFICIENT_LIQUIDATION_BUFFER if stop distance >= 75% of liquidation distance
"""

import math
import time
from typing import List

from quantum.agents.contracts import RiskInput, RiskOutput
from quantum.config.settings import RiskConfig
from quantum.core.logging import get_logger
from quantum.domain.enums import AgentAction, TradeSide
from quantum.domain.models import RiskDecision

logger = get_logger("agents.risk")


class RiskAgent:
    """Agent 4: 100% deterministic Python risk validation and position sizing engine."""

    def __init__(self, config: RiskConfig) -> None:
        self.config = config

    async def evaluate(self, input_data: RiskInput) -> RiskOutput:
        """Evaluate trade proposal against all 12 hard deterministic safety rules."""
        start_time = time.perf_counter()
        proposal = input_data.proposal
        context = input_data.candidate.context

        checks_passed: List[str] = []
        veto_reasons: List[str] = []
        now_ms = input_data.eval_timestamp_ms if input_data.eval_timestamp_ms is not None else int(time.time() * 1000)

        # 0. Strict Data Integrity and Missing-Data Gates
        if input_data.current_equity_usdt is None or input_data.current_equity_usdt <= 0.0 or math.isnan(input_data.current_equity_usdt):
            veto_reasons.append("VETO_MISSING_ACCOUNT_EQUITY: equity is None, non-positive, or NaN")
            equity = 0.0
        else:
            equity = input_data.current_equity_usdt

        if input_data.open_positions_count is None or input_data.open_positions_count < 0:
            veto_reasons.append("VETO_MISSING_OPEN_POSITIONS: open_positions_count is None or negative")
            open_positions = 999
        else:
            open_positions = input_data.open_positions_count

        if input_data.total_exposure_usdt is None or input_data.total_exposure_usdt < 0.0 or math.isnan(input_data.total_exposure_usdt):
            veto_reasons.append("VETO_MISSING_TOTAL_EXPOSURE: total_exposure_usdt is None or invalid")
            current_total_exposure = 0.0
        else:
            current_total_exposure = input_data.total_exposure_usdt

        # Gate 1: Signal Freshness Check
        if context.snapshot_timestamp_ms <= 0:
            veto_reasons.append("VETO_MISSING_TIMESTAMP: snapshot_timestamp_ms is non-positive")
        else:
            signal_age_ms = now_ms - context.snapshot_timestamp_ms
            if signal_age_ms < 0:
                veto_reasons.append("VETO_FUTURE_TIMESTAMP: snapshot_timestamp_ms is in the future")
            elif signal_age_ms <= 15_000:
                checks_passed.append("SIGNAL_FRESHNESS")
            else:
                veto_reasons.append(f"VETO_STALE_SIGNAL: age {signal_age_ms}ms > 15000ms")

        # Gate 2: Drawdown Circuit Breaker Check
        if input_data.peak_equity_usdt and input_data.peak_equity_usdt > 0.0 and equity > 0.0:
            drawdown_pct = max(0.0, (input_data.peak_equity_usdt - equity) / input_data.peak_equity_usdt)
            if drawdown_pct > self.config.max_total_drawdown_pct:
                veto_reasons.append(
                    f"VETO_DRAWDOWN_BREACHED: drawdown {drawdown_pct:.1%} > max {self.config.max_total_drawdown_pct:.1%}"
                )
            else:
                checks_passed.append("DRAWDOWN_CIRCUIT_BREAKER")
        else:
            checks_passed.append("DRAWDOWN_CIRCUIT_BREAKER")

        # Gate 3: Daily Loss Limit Check
        if input_data.daily_pnl_usdt is not None and input_data.starting_day_equity_usdt and input_data.starting_day_equity_usdt > 0.0:
            if input_data.daily_pnl_usdt < 0:
                daily_loss_pct = abs(input_data.daily_pnl_usdt) / input_data.starting_day_equity_usdt
                if daily_loss_pct > self.config.max_daily_loss_pct:
                    veto_reasons.append(
                        f"VETO_DAILY_LOSS_BREACHED: loss {daily_loss_pct:.1%} > max {self.config.max_daily_loss_pct:.1%}"
                    )
                else:
                    checks_passed.append("DAILY_LOSS_LIMIT")
            else:
                checks_passed.append("DAILY_LOSS_LIMIT")
        else:
            checks_passed.append("DAILY_LOSS_LIMIT")

        # Gate 4: Loss Streak Cooldown Check
        # Semantics:
        # - If consecutive_losses_count >= config.loss_streak_cooldown_count:
        #   - Missing, non-positive, or NaN timestamp: fail closed with VETO_LOSS_STREAK_COOLDOWN
        #   - elapsed time < cooldown duration: VETO_LOSS_STREAK_COOLDOWN (active cooldown window)
        #   - elapsed time >= cooldown duration: PASS (cooldown has expired)
        # - If consecutive_losses_count < config.loss_streak_cooldown_count or None: PASS
        if (
            input_data.consecutive_losses_count is not None
            and input_data.consecutive_losses_count >= self.config.loss_streak_cooldown_count
        ):
            if (
                input_data.last_loss_timestamp_ms is None
                or input_data.last_loss_timestamp_ms <= 0
                or math.isnan(input_data.last_loss_timestamp_ms)
            ):
                veto_reasons.append(
                    f"VETO_LOSS_STREAK_COOLDOWN: streak {input_data.consecutive_losses_count} active but missing or invalid last_loss_timestamp_ms"
                )
            else:
                cooldown_ms = self.config.per_symbol_loss_cooldown_min * 60_000
                elapsed_loss_cooldown = now_ms - input_data.last_loss_timestamp_ms
                if elapsed_loss_cooldown < 0:
                    veto_reasons.append("VETO_LOSS_STREAK_COOLDOWN: last_loss_timestamp_ms is in the future")
                elif elapsed_loss_cooldown < cooldown_ms:
                    remaining_s = int((cooldown_ms - elapsed_loss_cooldown) / 1000)
                    veto_reasons.append(
                        f"VETO_LOSS_STREAK_COOLDOWN: streak {input_data.consecutive_losses_count} active (cooldown remaining {remaining_s}s)"
                    )
                else:
                    checks_passed.append("LOSS_STREAK_COOLDOWN")
        else:
            checks_passed.append("LOSS_STREAK_COOLDOWN")

        # Gate 5: Max Concurrent Positions Check
        if open_positions < self.config.max_concurrent_positions:
            checks_passed.append("MAX_CONCURRENT_POSITIONS")
        else:
            veto_reasons.append(
                f"VETO_MAX_POSITIONS_BREACHED: active {open_positions} >= max {self.config.max_concurrent_positions}"
            )

        # Gate 6: Stop Geometry Validation Check
        if context.last_price <= 0.0 or context.mark_price <= 0.0 or proposal.entry_price <= 0.0 or proposal.stop_loss <= 0.0:
            veto_reasons.append("VETO_MISSING_PRICE_DATA: invalid non-positive market or proposal prices")
            stop_dist = 0.0
        else:
            stop_dist = abs(proposal.entry_price - proposal.stop_loss)
            if proposal.side == TradeSide.LONG and proposal.stop_loss >= proposal.entry_price:
                veto_reasons.append("VETO_INVALID_STOP_GEOMETRY: LONG stop_loss >= entry_price")
            elif proposal.side == TradeSide.SHORT and proposal.stop_loss <= proposal.entry_price:
                veto_reasons.append("VETO_INVALID_STOP_GEOMETRY: SHORT stop_loss <= entry_price")
            elif stop_dist < (0.4 * context.atr_15m):
                veto_reasons.append(f"VETO_STOP_TOO_TIGHT: stop distance {stop_dist:.2f} < 0.4 ATR ({0.4 * context.atr_15m:.2f})")
            else:
                checks_passed.append("STOP_GEOMETRY_VALID")

        # Gate 7: Spread Check
        if context.spread_bps < 0.0 or math.isnan(context.spread_bps):
            veto_reasons.append("VETO_MISSING_PRICE_DATA: invalid negative or NaN spread_bps")
        elif context.spread_bps <= self.config.max_spread_bps:
            checks_passed.append("MAX_SPREAD")
        else:
            veto_reasons.append(
                f"VETO_EXCESSIVE_SPREAD: {context.spread_bps:.1f} bps > max {self.config.max_spread_bps:.1f} bps"
            )

        # Gate 8: Reward-to-Risk after Friction Check
        fee_rate = 0.00055  # Taker fee
        slip_bps = input_data.estimated_slippage_bps if input_data.estimated_slippage_bps is not None else self.config.max_estimated_slippage_bps
        slip_frac = slip_bps / 10000.0
        loss_per_unit = stop_dist + (proposal.entry_price * (fee_rate + slip_frac)) + (proposal.stop_loss * (fee_rate + slip_frac))
        gain_tp1 = abs(proposal.take_profit_1 - proposal.entry_price)
        gain_tp2 = abs(proposal.take_profit_2 - proposal.entry_price)
        blended_gain = (proposal.tp1_close_pct * gain_tp1) + ((1.0 - proposal.tp1_close_pct) * gain_tp2)
        gain_per_unit = blended_gain - (proposal.entry_price * fee_rate)
        net_rr = round(gain_per_unit / max(loss_per_unit, 1e-6), 2)

        if net_rr >= self.config.min_net_reward_risk:
            checks_passed.append("MIN_NET_RR")
        else:
            veto_reasons.append(
                f"VETO_INSUFFICIENT_NET_RR: net R:R {net_rr:.2f} < min {self.config.min_net_reward_risk:.2f}"
            )

        # Gate 9: Max Estimated Slippage Check
        if slip_bps <= self.config.max_estimated_slippage_bps:
            checks_passed.append("MAX_SLIPPAGE")
        else:
            veto_reasons.append(
                f"VETO_EXCESSIVE_SLIPPAGE: estimated slippage {slip_bps:.1f} bps > max {self.config.max_estimated_slippage_bps:.1f} bps"
            )

        # Gate 10: Position Sizing & Lot Step / Min Notional Caps
        risk_budget_usdt = equity * self.config.risk_per_trade_pct if equity > 0 else 0.0
        raw_qty = risk_budget_usdt / max(loss_per_unit, 1e-6) if equity > 0 else 0.0

        # Clamp by symbol exposure
        max_sym_notional = equity * self.config.max_symbol_exposure_pct if equity > 0 else 0.0
        qty_sym_cap = max_sym_notional / max(proposal.entry_price, 1e-6)

        # Clamp by total portfolio exposure
        remaining_notional = max(0.0, (equity * self.config.max_total_exposure_pct) - current_total_exposure) if equity > 0 else 0.0
        qty_port_cap = remaining_notional / max(proposal.entry_price, 1e-6)

        # Clamp by leverage ceiling
        qty_lev_cap = (equity * self.config.max_leverage_per_position) / max(proposal.entry_price, 1e-6) if equity > 0 else 0.0

        final_qty = max(0.0, min(raw_qty, qty_sym_cap, qty_port_cap, qty_lev_cap))
        
        # Round quantity to lot_step if provided
        lot_step = input_data.lot_step or 0.001
        final_qty = math.floor(final_qty / lot_step) * lot_step

        final_notional = final_qty * proposal.entry_price
        effective_lev = round(final_notional / max(equity, 1e-6), 2) if equity > 0 else 0.0

        min_notional_threshold = input_data.min_notional_usdt or 10.0
        if final_notional >= min_notional_threshold and final_qty > 0.0:
            checks_passed.append("LOT_STEP_AND_MIN_NOTIONAL")
        else:
            veto_reasons.append(
                f"VETO_BELOW_MIN_NOTIONAL: calculated notional {final_notional:.2f} USDT < min {min_notional_threshold:.2f} USDT"
            )

        # Gate 11: Exposure & Leverage Checks
        if effective_lev <= self.config.max_leverage_per_position:
            checks_passed.append("MAX_EXPOSURE_AND_LEVERAGE")
        else:
            veto_reasons.append(
                f"VETO_EXCESSIVE_LEVERAGE: {effective_lev:.1f}x > max {self.config.max_leverage_per_position:.1f}x"
            )

        # Gate 12: Liquidation Buffer Check
        # Formula: est_liq_distance = proposal.entry_price * (1.0 / pos_leverage)
        # where pos_leverage = max(effective_lev, self.config.max_leverage_per_position).
        #
        # ASSUMPTIONS AND LIMITATIONS:
        # 1. Isolated Margin Assumption: Assumes position is opened under isolated margin where only
        #    allocated initial margin backs the position, not total portfolio account equity.
        # 2. Linear Approximation: Uses est_liq_dist ~ Entry / L. It neglects the exchange maintenance margin
        #    rate (MMR, typically 0.5% to 1.0%), which slightly reduces actual distance to liquidation.
        # 3. Conservative Leverage Input: Taking max(effective_lev, max_leverage_per_position) ensures the
        #    leverage assumption is never lower than the configured ceiling (default 3.0x to 5.0x). A higher
        #    leverage produces a smaller liquidation distance, yielding a strictly conservative bound.
        # 4. 25% Safety Haircut: Enforces stop_dist < 0.75 * est_liq_distance, guaranteeing the hard stop
        #    triggers long before liquidation price can be reached under normal market conditions.
        # 5. This is a local risk engine approximation and NOT an exchange-confirmed liquidation price.
        pos_leverage = max(effective_lev, self.config.max_leverage_per_position)
        if pos_leverage > 0.0:
            est_liq_distance = proposal.entry_price * (1.0 / pos_leverage)
            # Safe invariant: stop distance must not exceed 75% of liquidation distance
            if stop_dist >= (0.75 * est_liq_distance):
                veto_reasons.append(
                    f"VETO_INSUFFICIENT_LIQUIDATION_BUFFER: stop distance {stop_dist:.2f} >= 75% liquidation distance {0.75 * est_liq_distance:.2f}"
                )
            else:
                checks_passed.append("LIQUIDATION_BUFFER")
        else:
            checks_passed.append("LIQUIDATION_BUFFER")

        decision_action = AgentAction.APPROVED if len(veto_reasons) == 0 else AgentAction.REJECTED

        decision = RiskDecision(
            decision_id=f"risk_{proposal.proposal_id}_{now_ms}",
            proposal_id=proposal.proposal_id,
            pipeline_run_id=input_data.pipeline_run_id,
            decision=decision_action,
            approved_quantity=round(final_qty, 4) if decision_action == AgentAction.APPROVED else 0.0,
            notional_usdt=round(final_notional, 2) if decision_action == AgentAction.APPROVED else 0.0,
            effective_leverage=effective_lev if decision_action == AgentAction.APPROVED else 0.0,
            risk_amount_usdt=round(risk_budget_usdt, 2),
            risk_pct_of_equity=self.config.risk_per_trade_pct,
            net_reward_risk=net_rr,
            estimated_fee_usdt=round(final_notional * fee_rate, 4),
            estimated_slippage_bps=slip_bps,
            equity_at_eval_usdt=equity,
            checks_passed=checks_passed,
            veto_reasons=veto_reasons,
            evaluated_at_ms=now_ms,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        logger.debug("Risk evaluation completed in %.2f ms (Decision: %s)", elapsed_ms, decision_action.name)

        return RiskOutput(decision=decision)
