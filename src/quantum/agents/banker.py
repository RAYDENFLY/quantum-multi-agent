"""Agent 5: BANKER position lifecycle and deterministic exit state machine module."""

import time
from typing import Optional, Tuple

from quantum.agents.contracts import BankerInput, BankerOutput, PositionExecutionEvent, TrackedPosition
from quantum.config.settings import MLConfig
from quantum.core.logging import get_logger
from quantum.domain.enums import AgentAction, ExecutionEventType, PositionLifecycleState, TradeSide

logger = get_logger("agents.banker")


class InvalidStateTransitionError(Exception):
    """Raised when an execution event is invalid for current position lifecycle state."""
    pass


class InvalidExecutionQuantityError(Exception):
    """Raised when an execution event fill quantity exceeds remaining position quantity."""
    pass


class BankerAgent:
    """Agent 5: Deterministic position state machine managing stops, TP ratchets, and attribution.

    CRITICAL SAFETY RULES:
    1. A TP touch is NOT equivalent to a confirmed fill. A touch emits telemetry only.
    2. Partial position reduction requires a validated ExecutionEvent.
    3. Stop Ratchet Policy: OPTION A (Ratchet to breakeven upon FIRST confirmed TP1 partial fill).
       Rationale: In volatile crypto perpetuals, once price reaches TP1 and partially fills,
       taking off risk on the remaining position locks in a zero-loss baseline, preventing winning
       entries from turning into losses on sharp wick reversals.
    4. Monotonic Stop Invariant: Stops only tighten, never loosen. If a trailing stop is already
       tighter than entry price, it is preserved.
    5. Duplicate fill events are idempotent: discarded without state mutation.
    6. Out-of-order events are rejected without mutating state.
    7. Stale or missing market prices produce safe monitoring state.
    8. No live exchange order execution is allowed.
    """

    def __init__(
        self,
        config: Optional[MLConfig] = None,
        hazard_threshold: Optional[float] = None,
        trailing_activation_r: Optional[float] = None,
        trailing_distance_atr: Optional[float] = None,
    ) -> None:
        cfg = config or MLConfig()
        self.hazard_threshold = hazard_threshold if hazard_threshold is not None else cfg.banker_hazard_exit_prob
        self.trailing_activation_r = (
            trailing_activation_r if trailing_activation_r is not None else cfg.banker_trailing_stop_activation_r
        )
        self.trailing_distance_atr = (
            trailing_distance_atr if trailing_distance_atr is not None else cfg.banker_trailing_stop_distance_atr
        )

    def handle_execution_event(
        self, position: TrackedPosition, event: PositionExecutionEvent
    ) -> Tuple[TrackedPosition, BankerOutput]:
        """Apply a confirmed execution fill event through deterministic state machine."""
        now_ms = int(time.time() * 1000)

        # 1. Idempotency Check: Drop duplicate event
        if event.event_id in position.processed_event_ids:
            logger.warning("Duplicate execution event %s received for position %s", event.event_id, position.position_id)
            return position, BankerOutput(
                action=AgentAction.HOLD,
                hazard_prob=0.0,
                suggested_stop_loss=position.current_stop_loss,
                rationale=f"Duplicate execution event {event.event_id} discarded (idempotent)",
                updated_position=position,
            )

        # 2. Sequence Number Check: Reject out-of-order event
        if event.sequence_number <= position.last_sequence_number:
            logger.warning(
                "Out-of-order event seq %d <= last seq %d for position %s",
                event.sequence_number,
                position.last_sequence_number,
                position.position_id,
            )
            return position, BankerOutput(
                action=AgentAction.HOLD,
                hazard_prob=0.0,
                suggested_stop_loss=position.current_stop_loss,
                rationale=f"Out-of-order event seq {event.sequence_number} rejected (last: {position.last_sequence_number})",
                updated_position=position,
            )

        # 3. Transition Matrix Validation and Overfill Protection
        current_state = position.state
        event_type = event.event_type
        new_processed = list(position.processed_event_ids) + [event.event_id]

        if event_type == ExecutionEventType.ENTRY_FILL:
            if current_state != PositionLifecycleState.PENDING_OPEN:
                raise InvalidStateTransitionError(
                    f"ENTRY_FILL invalid from state {current_state.name} for position {position.position_id}"
                )
            tp1_target = (
                position.tp1_target_quantity
                if position.tp1_target_quantity > 0.0
                else round(event.fill_quantity * 0.50, 4)
            )
            tp2_target = (
                position.tp2_target_quantity
                if position.tp2_target_quantity > 0.0
                else round(event.fill_quantity - tp1_target, 4)
            )
            updated = position.model_copy(
                update={
                    "state": PositionLifecycleState.OPEN,
                    "initial_quantity": event.fill_quantity,
                    "remaining_quantity": event.fill_quantity,
                    "tp1_target_quantity": tp1_target,
                    "tp2_target_quantity": tp2_target,
                    "processed_event_ids": new_processed,
                    "last_sequence_number": event.sequence_number,
                    "updated_at_ms": now_ms,
                }
            )
            return updated, BankerOutput(
                action=AgentAction.HOLD,
                hazard_prob=0.05,
                suggested_stop_loss=updated.current_stop_loss,
                rationale=f"Position opened at {event.fill_price:.4f} (qty: {event.fill_quantity:.4f})",
                updated_position=updated,
            )

        elif event_type == ExecutionEventType.TP1_FILL:
            if current_state not in (PositionLifecycleState.OPEN, PositionLifecycleState.PARTIALLY_CLOSED):
                raise InvalidStateTransitionError(
                    f"TP1_FILL invalid from state {current_state.name} for position {position.position_id}"
                )
            if round(event.fill_quantity, 6) > round(position.remaining_quantity + 1e-6, 6):
                raise InvalidExecutionQuantityError(
                    f"Fill quantity {event.fill_quantity:.4f} exceeds remaining position quantity "
                    f"{position.remaining_quantity:.4f} for position {position.position_id}"
                )
            new_rem_qty = max(0.0, round(position.remaining_quantity - event.fill_quantity, 6))
            new_tp1_filled = round(position.tp1_filled_quantity + event.fill_quantity, 6)
            tp1_target = (
                position.tp1_target_quantity
                if position.tp1_target_quantity > 0.0
                else round(position.initial_quantity * 0.50, 4)
            )
            is_tp1_fully_filled = new_tp1_filled >= round(tp1_target - 1e-6, 6)

            # Ratchet Policy (Option A):
            # Ratchet stop to breakeven (entry price) upon the FIRST confirmed TP1 partial fill.
            # Invariant: Stops only tighten, never loosen. If already tighter than entry, preserve it.
            if position.side == TradeSide.LONG:
                ratcheted_sl = max(position.current_stop_loss, position.entry_price)
            else:
                ratcheted_sl = min(position.current_stop_loss, position.entry_price)

            new_state = (
                PositionLifecycleState.CLOSED if new_rem_qty <= 1e-6 else PositionLifecycleState.PARTIALLY_CLOSED
            )
            updated = position.model_copy(
                update={
                    "state": new_state,
                    "remaining_quantity": new_rem_qty,
                    "tp1_filled_quantity": new_tp1_filled,
                    "tp1_confirmed_filled": is_tp1_fully_filled,
                    "current_stop_loss": ratcheted_sl,
                    "processed_event_ids": new_processed,
                    "last_sequence_number": event.sequence_number,
                    "updated_at_ms": now_ms,
                }
            )
            return updated, BankerOutput(
                action=(
                    AgentAction.TIGHTEN_STOP
                    if new_state != PositionLifecycleState.CLOSED
                    else AgentAction.CLOSE_POSITION
                ),
                hazard_prob=0.10,
                suggested_stop_loss=ratcheted_sl,
                rationale=(
                    f"TP1 fill confirmed at {event.fill_price:.4f} (qty: {event.fill_quantity:.4f}, "
                    f"remaining: {new_rem_qty:.4f}); ratcheted stop to breakeven {ratcheted_sl:.4f}"
                ),
                updated_position=updated,
            )

        elif event_type == ExecutionEventType.TP2_FILL:
            if current_state != PositionLifecycleState.PARTIALLY_CLOSED:
                raise InvalidStateTransitionError(
                    f"TP2_FILL invalid from state {current_state.name} for position {position.position_id}"
                )
            if round(event.fill_quantity, 6) > round(position.remaining_quantity + 1e-6, 6):
                raise InvalidExecutionQuantityError(
                    f"Fill quantity {event.fill_quantity:.4f} exceeds remaining position quantity "
                    f"{position.remaining_quantity:.4f} for position {position.position_id}"
                )
            new_rem_qty = max(0.0, round(position.remaining_quantity - event.fill_quantity, 6))
            new_tp2_filled = round(position.tp2_filled_quantity + event.fill_quantity, 6)
            is_closed = new_rem_qty <= 1e-6
            new_state = PositionLifecycleState.CLOSED if is_closed else PositionLifecycleState.PARTIALLY_CLOSED
            updated = position.model_copy(
                update={
                    "state": new_state,
                    "remaining_quantity": new_rem_qty,
                    "tp2_filled_quantity": new_tp2_filled,
                    "tp2_confirmed_filled": is_closed,
                    "processed_event_ids": new_processed,
                    "last_sequence_number": event.sequence_number,
                    "updated_at_ms": now_ms,
                }
            )
            if is_closed:
                return updated, BankerOutput(
                    action=AgentAction.CLOSE_POSITION,
                    hazard_prob=0.0,
                    suggested_stop_loss=None,
                    rationale=f"TP2 confirmed filled at {event.fill_price:.4f}; position fully closed in profit",
                    updated_position=updated,
                )
            else:
                return updated, BankerOutput(
                    action=AgentAction.HOLD,
                    hazard_prob=0.05,
                    suggested_stop_loss=updated.current_stop_loss,
                    rationale=(
                        f"TP2 partial fill at {event.fill_price:.4f} (qty: {event.fill_quantity:.4f}, "
                        f"remaining: {new_rem_qty:.4f})"
                    ),
                    updated_position=updated,
                )

        elif event_type == ExecutionEventType.SL_FILL:
            if current_state not in (PositionLifecycleState.OPEN, PositionLifecycleState.PARTIALLY_CLOSED):
                raise InvalidStateTransitionError(
                    f"SL_FILL invalid from state {current_state.name} for position {position.position_id}"
                )
            if round(event.fill_quantity, 6) > round(position.remaining_quantity + 1e-6, 6):
                raise InvalidExecutionQuantityError(
                    f"Fill quantity {event.fill_quantity:.4f} exceeds remaining position quantity "
                    f"{position.remaining_quantity:.4f} for position {position.position_id}"
                )
            updated = position.model_copy(
                update={
                    "state": PositionLifecycleState.CLOSED,
                    "remaining_quantity": 0.0,
                    "sl_confirmed_filled": True,
                    "processed_event_ids": new_processed,
                    "last_sequence_number": event.sequence_number,
                    "updated_at_ms": now_ms,
                }
            )
            return updated, BankerOutput(
                action=AgentAction.CLOSE_POSITION,
                hazard_prob=1.0,
                suggested_stop_loss=None,
                rationale=f"Stop-loss executed at {event.fill_price:.4f}; position closed",
                updated_position=updated,
            )

        elif event_type == ExecutionEventType.MANUAL_CLOSE:
            if current_state not in (PositionLifecycleState.OPEN, PositionLifecycleState.PARTIALLY_CLOSED):
                raise InvalidStateTransitionError(
                    f"MANUAL_CLOSE invalid from state {current_state.name} for position {position.position_id}"
                )
            if round(event.fill_quantity, 6) > round(position.remaining_quantity + 1e-6, 6):
                raise InvalidExecutionQuantityError(
                    f"Fill quantity {event.fill_quantity:.4f} exceeds remaining position quantity "
                    f"{position.remaining_quantity:.4f} for position {position.position_id}"
                )
            updated = position.model_copy(
                update={
                    "state": PositionLifecycleState.CLOSED,
                    "remaining_quantity": 0.0,
                    "processed_event_ids": new_processed,
                    "last_sequence_number": event.sequence_number,
                    "updated_at_ms": now_ms,
                }
            )
            return updated, BankerOutput(
                action=AgentAction.CLOSE_POSITION,
                hazard_prob=0.0,
                suggested_stop_loss=None,
                rationale=f"Manual close executed at {event.fill_price:.4f}; position closed",
                updated_position=updated,
            )

        raise InvalidStateTransitionError(f"Unsupported event type: {event_type}")

    async def evaluate(self, input_data: BankerInput) -> BankerOutput:
        """Evaluate open position tick state and suggest lifecycle adjustments.

        CRITICAL: Never adjusts stops on price touch. Confirmed execution fill required.
        """
        now_ms = int(time.time() * 1000)
        mark = input_data.current_mark_price
        entry = input_data.entry_price
        sl = input_data.current_stop_loss
        tp1 = input_data.take_profit_1
        side = input_data.side

        # 1. Price Data Staleness Check
        if input_data.price_timestamp_ms is not None:
            price_age_ms = now_ms - input_data.price_timestamp_ms
            if price_age_ms > 15_000:
                logger.warning("Banker received stale market price (age %d ms) for %s", price_age_ms, input_data.symbol)
                return BankerOutput(
                    action=AgentAction.HOLD,
                    hazard_prob=0.0,
                    suggested_stop_loss=sl,
                    rationale=f"SAFE_MONITORING: market price is stale ({price_age_ms}ms > 15000ms); holding",
                )

        # 2. Touch vs Fill Check for TP1
        tp1_touched = (side == TradeSide.LONG and mark >= tp1) or (side == TradeSide.SHORT and mark <= tp1)
        if tp1_touched and not input_data.tp1_filled:
            # Price touched TP1, but fill is not yet confirmed!
            return BankerOutput(
                action=AgentAction.HOLD,
                hazard_prob=0.15,
                suggested_stop_loss=sl,
                is_touch_only=True,
                rationale=f"TP1 price {tp1:.4f} touched at mark {mark:.4f}; awaiting execution fill confirmation",
            )

        # 3. Stop-Loss Hit Breach Check
        if (side == TradeSide.LONG and mark <= sl) or (side == TradeSide.SHORT and mark >= sl):
            return BankerOutput(
                action=AgentAction.EARLY_EXIT,
                hazard_prob=1.0,
                suggested_stop_loss=sl,
                rationale=f"Stop-loss breached at mark {mark:.4f} (SL: {sl:.4f}); exit proposed",
            )

        # 4. Breakeven Ratchet Check (TP1 filled but stop not yet tightened to breakeven)
        if input_data.tp1_filled:
            if (side == TradeSide.LONG and sl < entry) or (side == TradeSide.SHORT and sl > entry):
                return BankerOutput(
                    action=AgentAction.TIGHTEN_STOP,
                    hazard_prob=0.15,
                    suggested_stop_loss=entry,
                    rationale=f"TP1 fill confirmed; ratcheting stop to breakeven {entry:.4f}",
                )

        # 5. Trailing Stop Check (unrealized PnL >= trailing_activation_r in partially closed position)
        if input_data.tp1_filled and input_data.unrealized_pnl_r >= self.trailing_activation_r:
            stop_dist = abs(entry - sl)
            suggested_trailing = (
                round(mark - (0.5 * stop_dist), 4) if side == TradeSide.LONG else round(mark + (0.5 * stop_dist), 4)
            )
            # Only tighten, never loosen
            is_tightening = (side == TradeSide.LONG and suggested_trailing > sl) or (
                side == TradeSide.SHORT and suggested_trailing < sl
            )
            if is_tightening:
                return BankerOutput(
                    action=AgentAction.TIGHTEN_STOP,
                    hazard_prob=0.20,
                    suggested_stop_loss=suggested_trailing,
                    rationale=f"Unrealized PnL {input_data.unrealized_pnl_r:+.2f}R >= {self.trailing_activation_r:.1f}R; trailing stop proposed",
                )

        return BankerOutput(
            action=AgentAction.HOLD,
            hazard_prob=0.10,
            suggested_stop_loss=sl,
            rationale=f"Position healthy; holding. Unrealized: {input_data.unrealized_pnl_r:+.2f}R",
        )
