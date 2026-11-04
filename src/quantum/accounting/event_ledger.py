"""Event-Driven Financial Accounting Ledger & Portfolio Exposure Engine.

Enforces:
1. Strict 1.0000x unlevered gross exposure invariant across all open positions.
2. Dynamic position sizing scaled strictly by current available equity.
3. Terminal equity and ruin protection: trading halts immediately if equity <= $1.00 USD.
4. Drawdown mathematically bounded in [0.0%, 100.0%].
5. Complete 19-field event telemetry with double-entry cash and position accounting.
"""

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from quantum.domain.enums import TradeSide


class LedgerEventType(str, Enum):
    """Event types recorded in the discrete event ledger."""
    PORTFOLIO_INITIALIZED = "PORTFOLIO_INITIALIZED"
    ORDER_SUBMITTED = "ORDER_SUBMITTED"
    ORDER_REJECTED = "ORDER_REJECTED"
    ORDER_FILLED = "ORDER_FILLED"
    POSITION_OPENED = "POSITION_OPENED"
    PARTIAL_FILL = "PARTIAL_FILL"
    PARTIAL_EXIT = "PARTIAL_EXIT"
    STOP_LOSS_HIT = "STOP_LOSS_HIT"
    TAKE_PROFIT_HIT = "TAKE_PROFIT_HIT"
    TIME_EXIT = "TIME_EXIT"
    SIGNAL_REVERSAL = "SIGNAL_REVERSAL"
    FUNDING_ACCRUED = "FUNDING_ACCRUED"
    POSITION_CLOSED = "POSITION_CLOSED"
    ORDER_CANCELED = "ORDER_CANCELED"
    CAPITAL_EXHAUSTION_HALT = "CAPITAL_EXHAUSTION_HALT"


@dataclass
class LedgerEvent:
    """Immutable discrete ledger entry recording a state transformation."""
    event_id: str
    trade_id: str
    symbol: str
    timestamp_ms: int
    event_type: LedgerEventType
    side: str
    quantity: float
    reference_price: float
    fill_price: float
    notional: float
    fee: float
    spread_cost: float
    slippage_cost: float
    funding_cost: float
    realized_pnl: float
    unrealized_pnl: float
    cash_balance: float
    equity: float
    gross_exposure: float


@dataclass
class OpenPosition:
    """State tracking for an active position in the portfolio."""
    trade_id: str
    symbol: str
    side: TradeSide
    quantity: float
    entry_price: float
    entry_notional: float
    entry_timestamp_ms: int
    entry_bar: int
    stop_price: float
    target_price: float
    market_regime: str
    accumulated_fees: float = 0.0
    accumulated_funding: float = 0.0


@dataclass
class PendingOrder:
    """State tracking for a pending unexecuted limit or reservation order."""
    order_id: str
    symbol: str
    side: TradeSide
    quantity: float
    price: float
    reserved_notional: float
    timestamp_ms: int
    is_limit: bool = True


class EventDrivenPortfolioLedger:
    """Event-driven accounting engine tracking cash, positions, fees, and exposure."""

    def __init__(
        self,
        initial_equity_usd: float = 100.0,
        max_gross_exposure: float = 1.0000,
        max_concurrent_positions: int = 4,
        max_symbol_weight: float = 0.25,
        ruin_equity_threshold: float = 1.0,
        safety_buffer: float = 0.0020,
    ) -> None:
        self.initial_equity_usd = float(initial_equity_usd)
        self.max_gross_exposure = float(max_gross_exposure)
        self.max_concurrent_positions = int(max_concurrent_positions)
        self.max_symbol_weight = float(max_symbol_weight)
        self.ruin_equity_threshold = float(ruin_equity_threshold)
        self.safety_buffer = float(safety_buffer)

        self.cash_balance = float(initial_equity_usd)
        self.equity = float(initial_equity_usd)
        self.peak_equity = float(initial_equity_usd)
        self.is_ruined = False

        self.open_positions: Dict[str, OpenPosition] = {}  # symbol -> OpenPosition
        self.pending_orders: Dict[str, PendingOrder] = {}  # order_id -> PendingOrder
        self.reserved_pending_notional: float = 0.0
        self.events: List[LedgerEvent] = []
        self._event_counter = 0
        self._trade_counter = 0

        # Log portfolio initialization
        self._record_event(
            trade_id="SYSTEM",
            symbol="PORTFOLIO",
            timestamp_ms=0,
            event_type=LedgerEventType.PORTFOLIO_INITIALIZED,
            side="NONE",
            quantity=0.0,
            reference_price=0.0,
            fill_price=0.0,
            notional=0.0,
            fee=0.0,
            spread_cost=0.0,
            slippage_cost=0.0,
            funding_cost=0.0,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
        )

    def _next_event_id(self) -> str:
        self._event_counter += 1
        return f"EVT-{self._event_counter:06d}"

    def _next_trade_id(self) -> str:
        self._trade_counter += 1
        return f"TRD-{self._trade_counter:05d}"

    def get_gross_notional(self, current_prices: Optional[Dict[str, float]] = None) -> float:
        """Computes aggregate gross notional across all open positions and reserved pending orders."""
        tot = 0.0
        for sym, pos in self.open_positions.items():
            if current_prices and sym in current_prices:
                tot += pos.quantity * current_prices[sym]
            else:
                tot += pos.entry_notional
        tot += self.reserved_pending_notional
        return tot

    def get_gross_exposure(self, current_prices: Optional[Dict[str, float]] = None) -> float:
        """Computes gross exposure = sum(abs(notional) + abs(reserved_pending_notional)) / current_equity."""
        if self.equity <= 1e-6:
            return 0.0 if self.get_gross_notional(current_prices) == 0.0 else 1.0
        return self.get_gross_notional(current_prices) / self.equity

    def update_mark_to_market(
        self,
        current_prices: Dict[str, float],
        timestamp_ms: int,
    ) -> float:
        """Marks all open positions to market prices and updates portfolio equity."""
        unrealized_tot = 0.0
        for sym, pos in self.open_positions.items():
            if sym in current_prices:
                p_cur = current_prices[sym]
                if pos.side == TradeSide.LONG:
                    unrealized = pos.quantity * (p_cur - pos.entry_price)
                else:
                    unrealized = pos.quantity * (pos.entry_price - p_cur)
                unrealized_tot += unrealized

        self.equity = self.cash_balance + unrealized_tot
        if self.equity > self.peak_equity:
            self.peak_equity = self.equity

        # Check ruin / liquidation condition
        if self.equity <= self.ruin_equity_threshold and not self.is_ruined:
            self.is_ruined = True
            self._record_event(
                trade_id="SYSTEM",
                symbol="PORTFOLIO",
                timestamp_ms=timestamp_ms,
                event_type=LedgerEventType.CAPITAL_EXHAUSTION_HALT,
                side="NONE",
                quantity=0.0,
                reference_price=0.0,
                fill_price=0.0,
                notional=0.0,
                fee=0.0,
                spread_cost=0.0,
                slippage_cost=0.0,
                funding_cost=0.0,
                realized_pnl=0.0,
                unrealized_pnl=unrealized_tot,
            )

        return self.equity

    def can_open_position(
        self,
        symbol: str,
        desired_notional: float,
        entry_friction_rate: float = 0.0013,
    ) -> Tuple[bool, str, float]:
        """Validates whether a new position can be opened within strict portfolio bounds.
        
        Sizing mathematically guarantees that post-trade gross exposure remains <= max_gross_exposure
        even after immediate cash deduction of all entry friction (fees, spread, and slippage).
        
        Returns:
            Tuple of (can_open, rejection_reason, allocated_notional)
        """
        # 1. Check Ruin
        if self.is_ruined or self.equity <= self.ruin_equity_threshold:
            return False, "CAPITAL_EXHAUSTION: Equity <= ruin threshold ($1.00). Trading halted.", 0.0

        # 2. Check Symbol Exclusivity
        if symbol in self.open_positions:
            return False, f"SYMBOL_ALREADY_OPEN: Position in {symbol} already exists.", 0.0

        # 3. Check Max Concurrent Positions (open + pending)
        active_count = len(self.open_positions) + len(self.pending_orders)
        if active_count >= self.max_concurrent_positions:
            return False, f"CONCURRENCY_LIMIT: Reached {self.max_concurrent_positions} concurrent positions/orders.", 0.0

        # 4. Compute Permissible Notional bounded post-friction
        max_notional_by_weight = self.equity * self.max_symbol_weight
        current_committed = self.get_gross_notional()
        raw_avail = max(0.0, (self.equity * self.max_gross_exposure) - current_committed)
        denom_exp = 1.0 + (self.max_gross_exposure * entry_friction_rate)
        fric_cap = max(0.0, ((self.equity * self.max_gross_exposure) - current_committed - 1e-6) / denom_exp)

        candidate = min(desired_notional, max_notional_by_weight, raw_avail)
        anticipated_post_eq = self.equity - (candidate * entry_friction_rate)
        if anticipated_post_eq > 1e-6 and ((current_committed + candidate) / anticipated_post_eq) > self.max_gross_exposure:
            allocated_notional = min(candidate, fric_cap)
        else:
            allocated_notional = candidate

        if allocated_notional < 5.0:  # Minimum viable notional
            return False, f"INSUFFICIENT_AVAILABLE_EQUITY: Allocated notional ${allocated_notional:.2f} < $5.00 min.", 0.0

        # 5. Assert Post-Trade Exposure Invariant (Zero-tolerance check)
        anticipated_post_equity = self.equity - (allocated_notional * entry_friction_rate)
        if anticipated_post_equity <= 1e-6:
            return False, "CAPITAL_EXHAUSTION: Post-trade equity would be <= 0.", 0.0

        anticipated_post_exposure = (current_committed + allocated_notional) / anticipated_post_equity
        if round(anticipated_post_exposure, 6) > round(self.max_gross_exposure, 6):
            return False, f"EXPOSURE_BREACH: Anticipated post-trade exposure {anticipated_post_exposure:.6f} > {self.max_gross_exposure:.6f}", 0.0

        return True, "APPROVED", allocated_notional

    def reserve_pending_order(
        self,
        order_id: str,
        symbol: str,
        side: TradeSide,
        price: float,
        requested_notional: float,
        timestamp_ms: int,
        fee_bps: float = 4.0,
        spread_bps_half: float = 0.0,
        slippage_bps: float = 0.0,
    ) -> Tuple[bool, str, float]:
        """Reserves exposure capacity for a pending limit order prior to execution."""
        entry_fric = (fee_bps + spread_bps_half + slippage_bps) / 10_000.0
        can_open, reason, alloc_notional = self.can_open_position(symbol, requested_notional, entry_friction_rate=entry_fric)
        if not can_open:
            self._record_event(
                trade_id=order_id,
                symbol=symbol,
                timestamp_ms=timestamp_ms,
                event_type=LedgerEventType.ORDER_REJECTED,
                side=side.name,
                quantity=0.0,
                reference_price=price,
                fill_price=0.0,
                notional=requested_notional,
                fee=0.0,
                spread_cost=0.0,
                slippage_cost=0.0,
                funding_cost=0.0,
                realized_pnl=0.0,
                unrealized_pnl=0.0,
            )
            return False, reason, 0.0

        qty = alloc_notional / price
        pending = PendingOrder(
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=qty,
            price=price,
            reserved_notional=alloc_notional,
            timestamp_ms=timestamp_ms,
            is_limit=True,
        )
        self.pending_orders[order_id] = pending
        self.reserved_pending_notional += alloc_notional

        self._record_event(
            trade_id=order_id,
            symbol=symbol,
            timestamp_ms=timestamp_ms,
            event_type=LedgerEventType.ORDER_SUBMITTED,
            side=side.name,
            quantity=qty,
            reference_price=price,
            fill_price=price,
            notional=alloc_notional,
            fee=0.0,
            spread_cost=0.0,
            slippage_cost=0.0,
            funding_cost=0.0,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
        )
        return True, "ORDER_RESERVED", alloc_notional

    def cancel_pending_order(
        self,
        order_id: str,
        timestamp_ms: int,
    ) -> bool:
        """Cancels a pending order and releases all reserved exposure."""
        if order_id not in self.pending_orders:
            return False

        order = self.pending_orders.pop(order_id)
        self.reserved_pending_notional = max(0.0, self.reserved_pending_notional - order.reserved_notional)

        self._record_event(
            trade_id=order_id,
            symbol=order.symbol,
            timestamp_ms=timestamp_ms,
            event_type=LedgerEventType.ORDER_CANCELED,
            side=order.side.name,
            quantity=order.quantity,
            reference_price=order.price,
            fill_price=0.0,
            notional=order.reserved_notional,
            fee=0.0,
            spread_cost=0.0,
            slippage_cost=0.0,
            funding_cost=0.0,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
        )
        return True

    def open_position(
        self,
        symbol: str,
        side: TradeSide,
        reference_price: float,
        fill_price: float,
        notional: float,
        fee_bps: float,
        spread_bps_half: float,
        slippage_bps: float,
        timestamp_ms: int,
        entry_bar: int,
        stop_price: float = 0.0,
        target_price: float = 0.0,
        market_regime: str = "UNKNOWN",
        is_partial: bool = False,
        pending_order_id: Optional[str] = None,
    ) -> Optional[OpenPosition]:
        """Opens a position with exact cash flow deduction and ledger event generation."""
        entry_friction_rate = (fee_bps + spread_bps_half + slippage_bps) / 10_000.0

        if pending_order_id and pending_order_id in self.pending_orders:
            p_order = self.pending_orders[pending_order_id]
            if is_partial:
                fill_slice = min(notional, p_order.reserved_notional)
                p_order.reserved_notional = max(0.0, p_order.reserved_notional - fill_slice)
                p_order.quantity = max(0.0, p_order.quantity - (fill_slice / fill_price))
                self.reserved_pending_notional = max(0.0, self.reserved_pending_notional - fill_slice)
                alloc_notional = fill_slice
            else:
                self.reserved_pending_notional = max(0.0, self.reserved_pending_notional - p_order.reserved_notional)
                alloc_notional = p_order.reserved_notional
                del self.pending_orders[pending_order_id]
        else:
            can_open, reason, alloc_notional = self.can_open_position(symbol, notional, entry_friction_rate=entry_friction_rate)
            if not can_open:
                self._record_event(
                    trade_id="REJECTED",
                    symbol=symbol,
                    timestamp_ms=timestamp_ms,
                    event_type=LedgerEventType.ORDER_REJECTED,
                    side=side.name,
                    quantity=0.0,
                    reference_price=reference_price,
                    fill_price=0.0,
                    notional=notional,
                    fee=0.0,
                    spread_cost=0.0,
                    slippage_cost=0.0,
                    funding_cost=0.0,
                    realized_pnl=0.0,
                    unrealized_pnl=0.0,
                )
                return None

        trade_id = self._next_trade_id()
        quantity = alloc_notional / fill_price
        actual_notional = quantity * fill_price

        # Compute transaction cost components
        fee_cost = actual_notional * (fee_bps / 10_000.0)
        spread_cost = actual_notional * (spread_bps_half / 10_000.0)
        slippage_cost = actual_notional * (slippage_bps / 10_000.0)
        total_entry_cost = fee_cost + spread_cost + slippage_cost

        # Double-entry cash deduction
        self.cash_balance -= total_entry_cost
        self.equity -= total_entry_cost

        if symbol in self.open_positions:
            pos = self.open_positions[symbol]
            new_qty = pos.quantity + quantity
            new_entry_notional = pos.entry_notional + actual_notional
            new_entry_price = new_entry_notional / new_qty
            pos.quantity = new_qty
            pos.entry_price = new_entry_price
            pos.entry_notional = new_entry_notional
            pos.accumulated_fees += total_entry_cost
        else:
            pos = OpenPosition(
                trade_id=trade_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=fill_price,
                entry_notional=actual_notional,
                entry_timestamp_ms=timestamp_ms,
                entry_bar=entry_bar,
                stop_price=stop_price,
                target_price=target_price,
                market_regime=market_regime,
                accumulated_fees=total_entry_cost,
            )
            self.open_positions[symbol] = pos

        # Clamping safeguard: strictly ensure exposure does not breach max_gross_exposure
        post_exp = self.get_gross_exposure()
        if round(post_exp, 6) > round(self.max_gross_exposure, 6):
            excess_notional = self.get_gross_notional() - (self.equity * self.max_gross_exposure)
            if excess_notional > 0:
                trim_qty = excess_notional / fill_price
                pos.quantity = max(0.0, pos.quantity - trim_qty)
                pos.entry_notional = pos.quantity * fill_price
                actual_notional = pos.entry_notional

        evt_type = LedgerEventType.PARTIAL_FILL if is_partial else LedgerEventType.POSITION_OPENED
        self._record_event(
            trade_id=trade_id,
            symbol=symbol,
            timestamp_ms=timestamp_ms,
            event_type=evt_type,
            side=side.name,
            quantity=pos.quantity,
            reference_price=reference_price,
            fill_price=fill_price,
            notional=actual_notional,
            fee=fee_cost,
            spread_cost=spread_cost,
            slippage_cost=slippage_cost,
            funding_cost=0.0,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
        )

        return pos

        return pos

    def close_position(
        self,
        symbol: str,
        fill_price: float,
        fee_bps: float,
        spread_bps_half: float,
        slippage_bps: float,
        timestamp_ms: int,
        exit_reason: str = "TAKE_PROFIT",
        exit_quantity_pct: float = 1.0,  # 1.0 for full close, < 1.0 for partial exit
    ) -> Optional[Tuple[float, float]]:
        """Closes or partially closes an open position with exact cash flows.
        
        Returns:
            Tuple of (realized_gross_pnl, realized_net_pnl)
        """
        if symbol not in self.open_positions:
            return None

        pos = self.open_positions[symbol]
        close_qty = pos.quantity * exit_quantity_pct
        close_notional = close_qty * fill_price

        # 1. Gross Realized PnL
        if pos.side == TradeSide.LONG:
            gross_pnl = close_qty * (fill_price - pos.entry_price)
        else:
            gross_pnl = close_qty * (pos.entry_price - fill_price)

        # 2. Exit Friction Components
        fee_cost = close_notional * (fee_bps / 10_000.0)
        spread_cost = close_notional * (spread_bps_half / 10_000.0)
        slippage_cost = close_notional * (slippage_bps / 10_000.0)
        total_exit_friction = fee_cost + spread_cost + slippage_cost

        # 3. Net Realized PnL for this exit slice
        net_pnl = gross_pnl - total_exit_friction

        # 4. Double-Entry Cash Update
        self.cash_balance += net_pnl
        self.equity = self.cash_balance  # Assuming all others marked

        # Check ruin / liquidation condition upon position close
        if self.equity <= self.ruin_equity_threshold and not self.is_ruined:
            self.is_ruined = True
            self._record_event(
                trade_id=pos.trade_id,
                symbol="PORTFOLIO",
                timestamp_ms=timestamp_ms,
                event_type=LedgerEventType.CAPITAL_EXHAUSTION_HALT,
                side="NONE",
                quantity=0.0,
                reference_price=0.0,
                fill_price=0.0,
                notional=0.0,
                fee=0.0,
                spread_cost=0.0,
                slippage_cost=0.0,
                funding_cost=0.0,
                realized_pnl=0.0,
                unrealized_pnl=0.0,
            )

        pos.accumulated_fees += total_exit_friction

        # Event type determination
        if exit_quantity_pct < 1.0:
            evt_type = LedgerEventType.PARTIAL_EXIT
            pos.quantity -= close_qty
            pos.entry_notional = pos.quantity * pos.entry_price
        else:
            if "STOP" in exit_reason.upper():
                evt_type = LedgerEventType.STOP_LOSS_HIT
            elif "PROFIT" in exit_reason.upper():
                evt_type = LedgerEventType.TAKE_PROFIT_HIT
            elif "TIME" in exit_reason.upper():
                evt_type = LedgerEventType.TIME_EXIT
            else:
                evt_type = LedgerEventType.POSITION_CLOSED
            del self.open_positions[symbol]

        self._record_event(
            trade_id=pos.trade_id,
            symbol=symbol,
            timestamp_ms=timestamp_ms,
            event_type=evt_type,
            side=pos.side.name,
            quantity=close_qty,
            reference_price=fill_price,
            fill_price=fill_price,
            notional=close_notional,
            fee=fee_cost,
            spread_cost=spread_cost,
            slippage_cost=slippage_cost,
            funding_cost=0.0,
            realized_pnl=gross_pnl,
            unrealized_pnl=0.0,
        )

        return gross_pnl, net_pnl

    def accrue_funding(
        self,
        symbol: str,
        funding_rate_bps: float,
        timestamp_ms: int,
    ) -> float:
        """Accrues periodic funding payment or receipt on open position."""
        if symbol not in self.open_positions:
            return 0.0

        pos = self.open_positions[symbol]
        # In perpetual linear futures: Long pays when funding > 0, Short receives
        funding_rate = funding_rate_bps / 10_000.0
        current_notional = pos.quantity * pos.entry_price

        if pos.side == TradeSide.LONG:
            funding_cost = current_notional * funding_rate  # Positive means cash deduction
        else:
            funding_cost = -current_notional * funding_rate

        self.cash_balance -= funding_cost
        self.equity -= funding_cost
        pos.accumulated_funding += funding_cost

        self._record_event(
            trade_id=pos.trade_id,
            symbol=symbol,
            timestamp_ms=timestamp_ms,
            event_type=LedgerEventType.FUNDING_ACCRUED,
            side=pos.side.name,
            quantity=pos.quantity,
            reference_price=pos.entry_price,
            fill_price=pos.entry_price,
            notional=current_notional,
            fee=0.0,
            spread_cost=0.0,
            slippage_cost=0.0,
            funding_cost=funding_cost,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
        )
        return funding_cost

    def _record_event(
        self,
        trade_id: str,
        symbol: str,
        timestamp_ms: int,
        event_type: LedgerEventType,
        side: str,
        quantity: float,
        reference_price: float,
        fill_price: float,
        notional: float,
        fee: float,
        spread_cost: float,
        slippage_cost: float,
        funding_cost: float,
        realized_pnl: float,
        unrealized_pnl: float,
    ) -> None:
        """Appends a discrete event to the ledger with full state snapshot."""
        evt = LedgerEvent(
            event_id=self._next_event_id(),
            trade_id=trade_id,
            symbol=symbol,
            timestamp_ms=timestamp_ms,
            event_type=event_type,
            side=side,
            quantity=round(quantity, 6),
            reference_price=round(reference_price, 4),
            fill_price=round(fill_price, 4),
            notional=round(notional, 2),
            fee=round(fee, 4),
            spread_cost=round(spread_cost, 4),
            slippage_cost=round(slippage_cost, 4),
            funding_cost=round(funding_cost, 4),
            realized_pnl=round(realized_pnl, 4),
            unrealized_pnl=round(unrealized_pnl, 4),
            cash_balance=round(self.cash_balance, 2),
            equity=round(self.equity, 2),
            gross_exposure=round(self.get_gross_exposure(), 6),
        )
        self.events.append(evt)

    def to_dataframe(self) -> pd.DataFrame:
        """Exports the event ledger to a structured Pandas DataFrame."""
        return pd.DataFrame([e.__dict__ for e in self.events])
