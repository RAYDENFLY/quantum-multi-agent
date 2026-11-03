"""Independent Accounting Oracle Engine (Phase C - Milestone 5.12.1).

A completely independent secondary accounting implementation designed specifically
to verify the mathematical and financial integrity of EventDrivenPortfolioLedger.
DOES NOT import, inherit, or reuse primary ledger arithmetic or state functions.
"""

from dataclasses import dataclass, field
import math
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class OraclePosition:
    """Internal oracle position tracking."""
    symbol: str
    is_long: bool
    quantity: float
    avg_entry_price: float
    accumulated_fees: float = 0.0
    accumulated_spread: float = 0.0
    accumulated_slippage: float = 0.0
    accumulated_funding: float = 0.0


@dataclass
class OracleStateSnapshot:
    """Complete snapshot of oracle financial state."""
    timestamp_ms: int
    cash_balance: float
    total_quantity: float
    realized_pnl: float
    unrealized_pnl: float
    total_fees: float
    total_spread: float
    total_slippage: float
    total_funding: float
    equity: float
    gross_exposure: float
    drawdown_pct: float
    is_ruined: bool


@dataclass
class OracleReconciliationRecord:
    """Comparison record between primary ledger and independent oracle."""
    test_case_id: str
    test_case_name: str
    variable_name: str
    primary_value: float
    oracle_value: float
    absolute_difference: float
    tolerance: float
    passed: bool
    notes: str = ""


class IndependentAccountingOracle:
    """Secondary, independent double-entry accounting oracle.
    
    Independent implementation of:
    - Cash conservation: Cash_t = Cash_0 + Realized_PnL - Fees - Spread - Slippage - Funding
    - Mark-to-market Equity: Equity_t = Cash_t + Unrealized_PnL_t
    - Exposure Invariant: Sum(|Notional_i|) / Equity_t <= 1.0000x
    - Unclamped Peak-to-Trough Drawdown: (Peak - Equity) / Peak * 100
    """

    def __init__(
        self,
        initial_cash_usd: float = 100.0,
        max_gross_exposure: float = 1.0000,
        ruin_threshold_usd: float = 1.0,
        max_symbol_weight: float = 0.25,
    ) -> None:
        self.initial_cash = float(initial_cash_usd)
        self.cash = float(initial_cash_usd)
        self.max_exposure = float(max_gross_exposure)
        self.ruin_threshold = float(ruin_threshold_usd)
        self.max_symbol_weight = float(max_symbol_weight)

        self.positions: Dict[str, OraclePosition] = {}
        self.tot_realized_pnl = 0.0
        self.tot_fees = 0.0
        self.tot_spread = 0.0
        self.tot_slippage = 0.0
        self.tot_funding = 0.0

        self.peak_equity = float(initial_cash_usd)
        self.is_ruined = False
        self.seen_event_ids: set = set()
        self.seen_trade_ids: set = set()
        self.last_timestamp_ms = -1

    def compute_unrealized_pnl(self, current_prices: Dict[str, float]) -> float:
        """Independently marks open positions to current market prices."""
        unrealized = 0.0
        for sym, pos in self.positions.items():
            price = current_prices.get(sym, pos.avg_entry_price)
            if pos.is_long:
                unrealized += pos.quantity * (price - pos.avg_entry_price)
            else:
                unrealized += pos.quantity * (pos.avg_entry_price - price)
        return unrealized

    def compute_equity(self, current_prices: Optional[Dict[str, float]] = None) -> float:
        """Equity = Cash + Unrealized PnL."""
        prices = current_prices or {}
        return self.cash + self.compute_unrealized_pnl(prices)

    def compute_gross_exposure(self, current_prices: Optional[Dict[str, float]] = None) -> float:
        """Gross exposure = Total Open Notional / Equity."""
        prices = current_prices or {}
        total_notional = 0.0
        for sym, pos in self.positions.items():
            price = prices.get(sym, pos.avg_entry_price)
            total_notional += abs(pos.quantity * price)
        eq = self.compute_equity(prices)
        if eq <= 1e-6:
            return 0.0 if total_notional == 0.0 else 1.0
        return total_notional / eq

    def compute_drawdown_pct(self, current_prices: Optional[Dict[str, float]] = None) -> float:
        """Unclamped peak-to-trough drawdown calculation."""
        eq = self.compute_equity(current_prices)
        if eq > self.peak_equity:
            self.peak_equity = eq
        if self.peak_equity <= 1e-6:
            return 0.0
        return ((self.peak_equity - eq) / self.peak_equity) * 100.0

    def process_entry(
        self,
        event_id: str,
        trade_id: str,
        timestamp_ms: int,
        symbol: str,
        is_long: bool,
        requested_notional: float,
        price: float,
        maker_fee_bps: float = 0.0,
        taker_fee_bps: float = 10.0,
        spread_bps_half: float = 1.0,
        slippage_bps: float = 2.0,
        is_maker: bool = False,
    ) -> Tuple[bool, str]:
        """Processes an entry order through independent risk and accounting rules."""
        # Check chronological ordering
        if timestamp_ms < self.last_timestamp_ms:
            return False, "OUT_OF_ORDER_TIMESTAMP"
        self.last_timestamp_ms = timestamp_ms

        # Check idempotency
        if event_id in self.seen_event_ids:
            return False, "DUPLICATE_EVENT_ID"
        self.seen_event_ids.add(event_id)

        # Ruin check
        if self.is_ruined or self.compute_equity() <= self.ruin_threshold:
            self.is_ruined = True
            return False, "HALTED_ON_RUIN"

        # Sizing and Exposure clamping
        current_eq = self.compute_equity()
        max_notional_per_symbol = current_eq * self.max_symbol_weight
        open_notional = sum(abs(p.quantity * p.avg_entry_price) for p in self.positions.values())
        available_portfolio_notional = max(0.0, (current_eq * self.max_exposure) - open_notional)

        actual_notional = min(requested_notional, max_notional_per_symbol, available_portfolio_notional)
        if actual_notional < 5.0:  # Minimum viable order size
            return False, "ORDER_REJECTED_INSUFFICIENT_MARGIN"

        qty = actual_notional / price

        # Friction calculations
        fee_rate = (maker_fee_bps if is_maker else taker_fee_bps) / 10_000.0
        fee_usd = actual_notional * fee_rate
        spread_usd = 0.0 if is_maker else actual_notional * (spread_bps_half / 10_000.0)
        slip_usd = 0.0 if is_maker else actual_notional * (slippage_bps / 10_000.0)

        # Cash deduction for entry friction
        self.cash -= (fee_usd + spread_usd + slip_usd)
        self.tot_fees += fee_usd
        self.tot_spread += spread_usd
        self.tot_slippage += slip_usd

        # Position tracking
        if symbol in self.positions:
            existing = self.positions[symbol]
            new_qty = existing.quantity + qty
            new_avg_p = ((existing.quantity * existing.avg_entry_price) + (qty * price)) / new_qty
            existing.quantity = new_qty
            existing.avg_entry_price = new_avg_p
            existing.accumulated_fees += fee_usd
            existing.accumulated_spread += spread_usd
            existing.accumulated_slippage += slip_usd
        else:
            self.positions[symbol] = OraclePosition(
                symbol=symbol,
                is_long=is_long,
                quantity=qty,
                avg_entry_price=price,
                accumulated_fees=fee_usd,
                accumulated_spread=spread_usd,
                accumulated_slippage=slip_usd,
            )

        self.seen_trade_ids.add(trade_id)
        return True, "FILLED"

    def process_exit(
        self,
        event_id: str,
        trade_id: str,
        timestamp_ms: int,
        symbol: str,
        exit_price: float,
        exit_quantity_pct: float = 1.0,
        maker_fee_bps: float = 0.0,
        taker_fee_bps: float = 10.0,
        spread_bps_half: float = 1.0,
        slippage_bps: float = 2.0,
        is_maker: bool = False,
        is_forced_liquidation: bool = False,
    ) -> Tuple[bool, float, float]:
        """Processes partial or full exit and settles cash."""
        if timestamp_ms < self.last_timestamp_ms:
            return False, 0.0, 0.0
        self.last_timestamp_ms = timestamp_ms

        if event_id in self.seen_event_ids:
            return False, 0.0, 0.0
        self.seen_event_ids.add(event_id)

        if symbol not in self.positions:
            return False, 0.0, 0.0

        pos = self.positions[symbol]
        close_qty = pos.quantity * exit_quantity_pct
        close_notional = close_qty * exit_price

        # Gross Realized PnL
        if pos.is_long:
            gross_pnl = close_qty * (exit_price - pos.avg_entry_price)
        else:
            gross_pnl = close_qty * (pos.avg_entry_price - exit_price)

        # Exit Friction
        fee_rate = (maker_fee_bps if is_maker else taker_fee_bps) / 10_000.0
        fee_usd = close_notional * fee_rate
        spread_usd = 0.0 if is_maker else close_notional * (spread_bps_half / 10_000.0)
        slip_usd = 0.0 if is_maker else close_notional * (slippage_bps / 10_000.0)

        total_exit_friction = fee_usd + spread_usd + slip_usd
        net_pnl = gross_pnl - total_exit_friction

        # Settle Cash
        self.cash += gross_pnl - total_exit_friction
        self.tot_realized_pnl += gross_pnl
        self.tot_fees += fee_usd
        self.tot_spread += spread_usd
        self.tot_slippage += slip_usd

        # Update position
        if exit_quantity_pct >= 0.999999:
            del self.positions[symbol]
        else:
            pos.quantity -= close_qty

        # Check ruin
        eq = self.compute_equity()
        if eq <= self.ruin_threshold:
            self.is_ruined = True

        return True, gross_pnl, net_pnl

    def process_funding(
        self,
        event_id: str,
        timestamp_ms: int,
        symbol: str,
        funding_rate_bps: float,
    ) -> float:
        """Accrues periodic perpetual funding."""
        if symbol not in self.positions:
            return 0.0
        pos = self.positions[symbol]
        notional = pos.quantity * pos.avg_entry_price
        rate = funding_rate_bps / 10_000.0
        
        # Long pays when funding > 0, Short receives
        charge = notional * rate if pos.is_long else -notional * rate
        self.cash -= charge
        self.tot_funding += charge
        pos.accumulated_funding += charge

        if self.compute_equity() <= self.ruin_threshold:
            self.is_ruined = True
        return charge

    def get_snapshot(self, current_prices: Optional[Dict[str, float]] = None) -> OracleStateSnapshot:
        """Generates comprehensive state snapshot."""
        prices = current_prices or {}
        tot_qty = sum(p.quantity for p in self.positions.values())
        unrealized = self.compute_unrealized_pnl(prices)
        eq = self.cash + unrealized
        exposure = self.compute_gross_exposure(prices)
        dd = self.compute_drawdown_pct(prices)

        return OracleStateSnapshot(
            timestamp_ms=self.last_timestamp_ms,
            cash_balance=round(self.cash, 6),
            total_quantity=round(tot_qty, 6),
            realized_pnl=round(self.tot_realized_pnl, 6),
            unrealized_pnl=round(unrealized, 6),
            total_fees=round(self.tot_fees, 6),
            total_spread=round(self.tot_spread, 6),
            total_slippage=round(self.tot_slippage, 6),
            total_funding=round(self.tot_funding, 6),
            equity=round(eq, 6),
            gross_exposure=round(exposure, 4),
            drawdown_pct=round(dd, 4),
            is_ruined=self.is_ruined,
        )
