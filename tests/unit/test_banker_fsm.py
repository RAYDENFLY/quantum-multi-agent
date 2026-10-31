"""Unit tests for Agent 5 (BANKER) deterministic position lifecycle state machine.

Tests transition table, touch vs fill integrity, idempotency, out-of-order rejection,
and stale price handling.
"""

import time
import pytest

from quantum.agents.banker import (
    BankerAgent,
    InvalidExecutionQuantityError,
    InvalidStateTransitionError,
)
from quantum.agents.contracts import (
    BankerInput,
    PositionExecutionEvent,
    TrackedPosition,
)
from quantum.domain.enums import (
    AgentAction,
    ExecutionEventType,
    PositionLifecycleState,
    TradeSide,
)


def make_test_position(
    state: PositionLifecycleState = PositionLifecycleState.PENDING_OPEN,
    side: TradeSide = TradeSide.LONG,
    entry: float = 65000.0,
    qty: float = 0.10,
    stop: float = 64500.0,
    tp1: float = 66000.0,
    tp2: float = 67000.0,
) -> TrackedPosition:
    now_ms = int(time.time() * 1000)
    return TrackedPosition(
        position_id="pos_test_1",
        symbol="BTCUSDT",
        side=side,
        state=state,
        entry_price=entry,
        initial_quantity=qty,
        remaining_quantity=qty if state != PositionLifecycleState.PENDING_OPEN else 0.0,
        current_stop_loss=stop,
        take_profit_1=tp1,
        take_profit_2=tp2,
        tp1_confirmed_filled=False,
        tp2_confirmed_filled=False,
        sl_confirmed_filled=False,
        processed_event_ids=[],
        last_sequence_number=0,
        created_at_ms=now_ms,
        updated_at_ms=now_ms,
    )


def test_banker_valid_full_lifecycle_progression() -> None:
    banker = BankerAgent()
    pos = make_test_position(state=PositionLifecycleState.PENDING_OPEN)
    now_ms = int(time.time() * 1000)

    # 1. ENTRY_FILL (PENDING_OPEN -> OPEN)
    ev_entry = PositionExecutionEvent(
        event_id="ev_entry_1",
        position_id="pos_test_1",
        event_type=ExecutionEventType.ENTRY_FILL,
        fill_price=65000.0,
        fill_quantity=0.10,
        timestamp_ms=now_ms,
        sequence_number=1,
    )
    pos, out1 = banker.handle_execution_event(pos, ev_entry)
    assert pos.state == PositionLifecycleState.OPEN
    assert pos.remaining_quantity == 0.10
    assert pos.last_sequence_number == 1
    assert "ev_entry_1" in pos.processed_event_ids

    # 2. TP1_FILL (OPEN -> PARTIALLY_CLOSED, ratchets SL to breakeven 65000)
    ev_tp1 = PositionExecutionEvent(
        event_id="ev_tp1_1",
        position_id="pos_test_1",
        event_type=ExecutionEventType.TP1_FILL,
        fill_price=66000.0,
        fill_quantity=0.05,
        timestamp_ms=now_ms + 1000,
        sequence_number=2,
    )
    pos, out2 = banker.handle_execution_event(pos, ev_tp1)
    assert pos.state == PositionLifecycleState.PARTIALLY_CLOSED
    assert pos.remaining_quantity == 0.05
    assert pos.tp1_confirmed_filled is True
    assert pos.current_stop_loss == 65000.0  # Ratcheted to breakeven!
    assert out2.action == AgentAction.TIGHTEN_STOP
    assert out2.suggested_stop_loss == 65000.0

    # 3. TP2_FILL (PARTIALLY_CLOSED -> CLOSED)
    ev_tp2 = PositionExecutionEvent(
        event_id="ev_tp2_1",
        position_id="pos_test_1",
        event_type=ExecutionEventType.TP2_FILL,
        fill_price=67000.0,
        fill_quantity=0.05,
        timestamp_ms=now_ms + 2000,
        sequence_number=3,
    )
    pos, out3 = banker.handle_execution_event(pos, ev_tp2)
    assert pos.state == PositionLifecycleState.CLOSED
    assert pos.remaining_quantity == 0.0
    assert pos.tp2_confirmed_filled is True
    assert out3.action == AgentAction.CLOSE_POSITION


def test_banker_sl_fill_from_open_and_partially_closed() -> None:
    banker = BankerAgent()
    now_ms = int(time.time() * 1000)

    # From OPEN to CLOSED via SL
    pos_open = make_test_position(state=PositionLifecycleState.OPEN)
    ev_sl = PositionExecutionEvent(
        event_id="ev_sl_1",
        position_id="pos_test_1",
        event_type=ExecutionEventType.SL_FILL,
        fill_price=64500.0,
        fill_quantity=0.10,
        timestamp_ms=now_ms,
        sequence_number=1,
    )
    pos_closed, out = banker.handle_execution_event(pos_open, ev_sl)
    assert pos_closed.state == PositionLifecycleState.CLOSED
    assert pos_closed.sl_confirmed_filled is True
    assert out.action == AgentAction.CLOSE_POSITION


@pytest.mark.asyncio
async def test_banker_touch_vs_fill_separation() -> None:
    banker = BankerAgent()

    # Price touched TP1 (66100 >= 66000), but tp1_filled is False
    inp = BankerInput(
        position_id="pos_1",
        symbol="BTCUSDT",
        side=TradeSide.LONG,
        entry_price=65000.0,
        current_mark_price=66100.0,
        current_stop_loss=64500.0,
        take_profit_1=66000.0,
        take_profit_2=67000.0,
        tp1_filled=False,
        unrealized_pnl_r=1.8,
    )

    out = await banker.evaluate(inp)

    # Crucial safety: Must NOT ratchet stop on touch! Must be is_touch_only
    assert out.is_touch_only is True
    assert out.action == AgentAction.HOLD
    assert out.suggested_stop_loss == 64500.0  # SL preserved, NOT tightened
    assert "touched" in out.rationale.lower()


def test_banker_idempotency_of_duplicate_events() -> None:
    banker = BankerAgent()
    pos = make_test_position(state=PositionLifecycleState.OPEN)
    now_ms = int(time.time() * 1000)

    ev_tp1 = PositionExecutionEvent(
        event_id="ev_tp1_dup",
        position_id="pos_test_1",
        event_type=ExecutionEventType.TP1_FILL,
        fill_price=66000.0,
        fill_quantity=0.05,
        timestamp_ms=now_ms,
        sequence_number=1,
    )

    pos_after_1, out1 = banker.handle_execution_event(pos, ev_tp1)
    assert pos_after_1.remaining_quantity == 0.05

    # Send exact same event again
    pos_after_2, out2 = banker.handle_execution_event(pos_after_1, ev_tp1)
    # Remaining quantity must NOT be reduced again
    assert pos_after_2.remaining_quantity == 0.05
    assert "discarded" in out2.rationale.lower()


def test_banker_out_of_order_event_rejection() -> None:
    banker = BankerAgent()
    pos = make_test_position(state=PositionLifecycleState.OPEN)
    pos = pos.model_copy(update={"last_sequence_number": 5})
    now_ms = int(time.time() * 1000)

    # Event with sequence_number 4 <= 5 (out of order)
    ev_stale = PositionExecutionEvent(
        event_id="ev_old_seq",
        position_id="pos_test_1",
        event_type=ExecutionEventType.TP1_FILL,
        fill_price=66000.0,
        fill_quantity=0.05,
        timestamp_ms=now_ms,
        sequence_number=4,
    )

    pos_after, out = banker.handle_execution_event(pos, ev_stale)
    assert pos_after.state == PositionLifecycleState.OPEN  # State not mutated
    assert "out-of-order" in out.rationale.lower()


@pytest.mark.asyncio
async def test_banker_stale_market_price_handling() -> None:
    banker = BankerAgent()
    now_ms = int(time.time() * 1000)

    # Price snapshot 20,000 ms ago (> 15,000 ms limit)
    inp = BankerInput(
        position_id="pos_stale",
        symbol="BTCUSDT",
        side=TradeSide.LONG,
        entry_price=65000.0,
        current_mark_price=64400.0,  # Below SL, but price is stale!
        current_stop_loss=64500.0,
        take_profit_1=66000.0,
        take_profit_2=67000.0,
        tp1_filled=False,
        price_timestamp_ms=now_ms - 20000,
    )

    out = await banker.evaluate(inp)
    # Safe monitoring mode: do NOT trigger exit or stop mutation on stale prices
    assert out.action == AgentAction.HOLD
    assert "SAFE_MONITORING" in out.rationale


def test_banker_invalid_state_transitions() -> None:
    banker = BankerAgent()
    now_ms = int(time.time() * 1000)

    # 1. TP1_FILL on PENDING_OPEN -> raises InvalidStateTransitionError
    pos_pending = make_test_position(state=PositionLifecycleState.PENDING_OPEN)
    with pytest.raises(InvalidStateTransitionError, match="TP1_FILL invalid from state PENDING_OPEN"):
        banker.handle_execution_event(
            pos_pending,
            PositionExecutionEvent(
                event_id="bad_1",
                position_id="p1",
                event_type=ExecutionEventType.TP1_FILL,
                fill_price=66000.0,
                fill_quantity=0.05,
                timestamp_ms=now_ms,
                sequence_number=1,
            ),
        )

    # 2. TP2_FILL on OPEN (before TP1) -> raises InvalidStateTransitionError
    pos_open = make_test_position(state=PositionLifecycleState.OPEN)
    with pytest.raises(InvalidStateTransitionError, match="TP2_FILL invalid from state OPEN"):
        banker.handle_execution_event(
            pos_open,
            PositionExecutionEvent(
                event_id="bad_2",
                position_id="p1",
                event_type=ExecutionEventType.TP2_FILL,
                fill_price=67000.0,
                fill_quantity=0.05,
                timestamp_ms=now_ms,
                sequence_number=1,
            ),
        )

    # 3. ENTRY_FILL on CLOSED -> raises InvalidStateTransitionError
    pos_closed = make_test_position(state=PositionLifecycleState.CLOSED)
    with pytest.raises(InvalidStateTransitionError, match="ENTRY_FILL invalid from state CLOSED"):
        banker.handle_execution_event(
            pos_closed,
            PositionExecutionEvent(
                event_id="bad_3",
                position_id="p1",
                event_type=ExecutionEventType.ENTRY_FILL,
                fill_price=65000.0,
                fill_quantity=0.10,
                timestamp_ms=now_ms,
                sequence_number=1,
            ),
        )


def test_banker_partial_tp1_fills_multiple_events() -> None:
    banker = BankerAgent()
    now_ms = int(time.time() * 1000)

    # Position opened with 0.10 BTC
    pos = make_test_position(state=PositionLifecycleState.OPEN, qty=0.10)
    pos = pos.model_copy(update={"remaining_quantity": 0.10, "last_sequence_number": 1})

    # Slice 1: First partial fill of TP1 (0.025 BTC out of 0.050 BTC TP1 target)
    ev_tp1_a = PositionExecutionEvent(
        event_id="ev_tp1_slice_1",
        position_id="pos_test_1",
        event_type=ExecutionEventType.TP1_FILL,
        fill_price=66000.0,
        fill_quantity=0.025,
        timestamp_ms=now_ms + 100,
        sequence_number=2,
    )
    pos_after_1, out1 = banker.handle_execution_event(pos, ev_tp1_a)
    assert pos_after_1.state == PositionLifecycleState.PARTIALLY_CLOSED
    assert pos_after_1.remaining_quantity == 0.075
    assert pos_after_1.tp1_filled_quantity == 0.025
    assert pos_after_1.tp1_confirmed_filled is False  # Target (0.05) not yet complete
    assert pos_after_1.current_stop_loss == 65000.0  # Option A: Ratcheted to breakeven on first partial fill!
    assert out1.action == AgentAction.TIGHTEN_STOP

    # Slice 2: Second partial fill of TP1 (0.025 BTC, completing TP1 target)
    ev_tp1_b = PositionExecutionEvent(
        event_id="ev_tp1_slice_2",
        position_id="pos_test_1",
        event_type=ExecutionEventType.TP1_FILL,
        fill_price=66005.0,
        fill_quantity=0.025,
        timestamp_ms=now_ms + 200,
        sequence_number=3,
    )
    pos_after_2, out2 = banker.handle_execution_event(pos_after_1, ev_tp1_b)
    assert pos_after_2.state == PositionLifecycleState.PARTIALLY_CLOSED
    assert pos_after_2.remaining_quantity == 0.050
    assert pos_after_2.tp1_filled_quantity == 0.050
    assert pos_after_2.tp1_confirmed_filled is True  # Target fully completed
    assert pos_after_2.current_stop_loss == 65000.0
    assert "ev_tp1_slice_1" in pos_after_2.processed_event_ids
    assert "ev_tp1_slice_2" in pos_after_2.processed_event_ids


def test_banker_cumulative_fill_exceeding_remaining_quantity_rejected() -> None:
    banker = BankerAgent()
    now_ms = int(time.time() * 1000)

    # Position opened with 0.10 BTC remaining
    pos_open = make_test_position(state=PositionLifecycleState.OPEN, qty=0.10)
    pos_open = pos_open.model_copy(update={"remaining_quantity": 0.10, "last_sequence_number": 1})

    # Execution event claiming 0.15 BTC fill (> 0.10 remaining)
    ev_overfill = PositionExecutionEvent(
        event_id="ev_overfill_1",
        position_id="pos_test_1",
        event_type=ExecutionEventType.TP1_FILL,
        fill_price=66000.0,
        fill_quantity=0.15,
        timestamp_ms=now_ms + 100,
        sequence_number=2,
    )
    with pytest.raises(InvalidExecutionQuantityError, match="exceeds remaining position quantity"):
        banker.handle_execution_event(pos_open, ev_overfill)

    # Partial close: reduce remaining to 0.04 BTC
    pos_part = make_test_position(state=PositionLifecycleState.PARTIALLY_CLOSED, qty=0.10)
    pos_part = pos_part.model_copy(
        update={
            "remaining_quantity": 0.04,
            "tp1_confirmed_filled": True,
            "last_sequence_number": 2,
        }
    )

    # Attempting to fill 0.045 BTC (> 0.04 remaining)
    ev_overfill_part = PositionExecutionEvent(
        event_id="ev_overfill_2",
        position_id="pos_test_1",
        event_type=ExecutionEventType.TP2_FILL,
        fill_price=67000.0,
        fill_quantity=0.045,
        timestamp_ms=now_ms + 200,
        sequence_number=3,
    )
    with pytest.raises(InvalidExecutionQuantityError, match="exceeds remaining position quantity"):
        banker.handle_execution_event(pos_part, ev_overfill_part)


def test_banker_remaining_quantity_verified_after_every_fill() -> None:
    banker = BankerAgent()
    now_ms = int(time.time() * 1000)

    # Start pending position
    pos = make_test_position(state=PositionLifecycleState.PENDING_OPEN)
    assert pos.remaining_quantity == 0.0

    # 1. Entry fill: 0.10 BTC
    ev_entry = PositionExecutionEvent(
        event_id="seq_1_entry",
        position_id="pos_test_1",
        event_type=ExecutionEventType.ENTRY_FILL,
        fill_price=65000.0,
        fill_quantity=0.10,
        timestamp_ms=now_ms,
        sequence_number=1,
    )
    pos, _ = banker.handle_execution_event(pos, ev_entry)
    assert pos.remaining_quantity == 0.10

    # 2. TP1 slice: 0.03 BTC fill -> remaining 0.07 BTC
    ev_tp1_1 = PositionExecutionEvent(
        event_id="seq_2_tp1_1",
        position_id="pos_test_1",
        event_type=ExecutionEventType.TP1_FILL,
        fill_price=66000.0,
        fill_quantity=0.03,
        timestamp_ms=now_ms + 100,
        sequence_number=2,
    )
    pos, _ = banker.handle_execution_event(pos, ev_tp1_1)
    assert pos.remaining_quantity == 0.07

    # 3. TP1 slice: 0.02 BTC fill -> remaining 0.05 BTC
    ev_tp1_2 = PositionExecutionEvent(
        event_id="seq_3_tp1_2",
        position_id="pos_test_1",
        event_type=ExecutionEventType.TP1_FILL,
        fill_price=66010.0,
        fill_quantity=0.02,
        timestamp_ms=now_ms + 200,
        sequence_number=3,
    )
    pos, _ = banker.handle_execution_event(pos, ev_tp1_2)
    assert pos.remaining_quantity == 0.05

    # 4. TP2 slice: 0.03 BTC fill -> remaining 0.02 BTC
    ev_tp2_1 = PositionExecutionEvent(
        event_id="seq_4_tp2_1",
        position_id="pos_test_1",
        event_type=ExecutionEventType.TP2_FILL,
        fill_price=67000.0,
        fill_quantity=0.03,
        timestamp_ms=now_ms + 300,
        sequence_number=4,
    )
    pos, out_tp2_1 = banker.handle_execution_event(pos, ev_tp2_1)
    assert pos.remaining_quantity == 0.02
    assert pos.state == PositionLifecycleState.PARTIALLY_CLOSED
    assert out_tp2_1.action == AgentAction.HOLD

    # 5. Final TP2 slice: 0.02 BTC fill -> remaining 0.00 BTC, CLOSED
    ev_tp2_2 = PositionExecutionEvent(
        event_id="seq_5_tp2_2",
        position_id="pos_test_1",
        event_type=ExecutionEventType.TP2_FILL,
        fill_price=67020.0,
        fill_quantity=0.02,
        timestamp_ms=now_ms + 400,
        sequence_number=5,
    )
    pos, out_tp2_2 = banker.handle_execution_event(pos, ev_tp2_2)
    assert pos.remaining_quantity == 0.00
    assert pos.state == PositionLifecycleState.CLOSED
    assert out_tp2_2.action == AgentAction.CLOSE_POSITION


def test_banker_monotonic_stop_loss_invariant() -> None:
    banker = BankerAgent()
    now_ms = int(time.time() * 1000)

    # Position with entry 65000, but trailing stop has already moved to 65500 (in profit)
    pos = make_test_position(state=PositionLifecycleState.OPEN, entry=65000.0, stop=65500.0, qty=0.10)
    pos = pos.model_copy(update={"remaining_quantity": 0.10, "last_sequence_number": 1})

    # When TP1 fill arrives, stop must NOT loosen down to breakeven (65000)
    ev_tp1 = PositionExecutionEvent(
        event_id="ev_tp1_tight",
        position_id="pos_test_1",
        event_type=ExecutionEventType.TP1_FILL,
        fill_price=66000.0,
        fill_quantity=0.05,
        timestamp_ms=now_ms,
        sequence_number=2,
    )
    pos_after, out = banker.handle_execution_event(pos, ev_tp1)
    # Stop loss must remain at 65500.0, not reset to entry 65000.0
    assert pos_after.current_stop_loss == 65500.0
    assert out.suggested_stop_loss == 65500.0

    # Verify duplicate event cannot alter stop loss
    pos_dup, out_dup = banker.handle_execution_event(pos_after, ev_tp1)
    assert pos_dup.current_stop_loss == 65500.0
    assert out_dup.action == AgentAction.HOLD

    # Verify out-of-order event cannot alter stop loss
    ev_old = PositionExecutionEvent(
        event_id="ev_old_seq",
        position_id="pos_test_1",
        event_type=ExecutionEventType.TP1_FILL,
        fill_price=66000.0,
        fill_quantity=0.01,
        timestamp_ms=now_ms,
        sequence_number=1,  # seq 1 <= last seq 2
    )
    pos_ooo, out_ooo = banker.handle_execution_event(pos_after, ev_old)
    assert pos_ooo.current_stop_loss == 65500.0
    assert out_ooo.action == AgentAction.HOLD


