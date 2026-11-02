"""Reference-Price PnL Accounting Engine for Phase 5.5.

Implements two-legged entry/exit notional scaling, signed friction (fees and slippage),
signed perpetual funding cash flows, partial close accounting, multi-step partial close
reconciliation, and end-of-dataset open-position mark-to-market accounting according to
PHASE_5_5_0_8_LONG_SHORT_ACCOUNTING_AUDIT.md and PHASE_5_5_0_8_TRANSACTION_COST_SPECIFICATION.md.

Formulas:
- Exit Notional: N_exit = N_entry * (1 + d * R_gross)
- Friction: C_total = C_fees + C_exec = (c_fee + c_slip) * (N_entry + N_exit)
- Signed Funding: CF_funding > 0 (received/inflow), CF_funding < 0 (paid/outflow)
- Net PnL: PnL_net = PnL_gross - C_fees - C_exec + CF_funding
- Net Return: R_net = PnL_net / N_entry
"""

import math
from typing import List, Optional, Sequence, Tuple
from pydantic import BaseModel, ConfigDict, Field

from quantum.domain.enums import TradeSide


HISTORICAL_FUNDING_STATUS: str = "FUNDING_DATA_UNAVAILABLE"
PARAMETRIC_FUNDING_GOVERNANCE_NOTE: str = "PARAMETRIC_SCENARIO_ONLY_NOT_EMPIRICAL_HISTORICAL_DATA"
COST_BASIS_SCOPE_NOTE: str = "SINGLE_ENTRY_ISOLATED_POSITION_DEC_04_DEC_05_PENDING"


class FeeSchedule(BaseModel):
    """Transaction cost parameters."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    taker_fee_bps: float = Field(default=15.0, ge=0.0, description="Taker fee rate in basis points per leg")
    maker_fee_bps: float = Field(default=5.0, ge=0.0, description="Maker fee rate in basis points per leg")
    half_spread_slippage_bps: float = Field(default=2.0, ge=0.0, description="Half-spread execution slippage in bps per leg")


class FundingSettlement(BaseModel):
    """Discrete funding settlement event."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    timestamp_ms: int = Field(gt=0)
    rate_bps: float = Field(description="Funding rate in bps for the 8-hour period")
    cash_flow_usdt: float = Field(description="Signed funding cash flow (positive = received, negative = paid)")
    funding_data_status: str = Field(default=HISTORICAL_FUNDING_STATUS)


class TradeAccountingResult(BaseModel):
    """Complete financial accounting ledger for a closed position or closed partial fill."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    side: TradeSide
    direction: int = Field(description="+1 for Long, -1 for Short")
    quantity: float = Field(gt=0.0)
    entry_price: float = Field(gt=0.0, description="Entry reference price")
    exit_price: float = Field(gt=0.0, description="Exit reference price")
    entry_fill_price_effective: float = Field(gt=0.0, description="Simulated entry fill price including half-spread slippage")
    exit_fill_price_effective: float = Field(gt=0.0, description="Simulated exit fill price including half-spread slippage")

    # Notionals & Margin
    entry_notional_usdt: float = Field(gt=0.0)
    exit_notional_usdt: float = Field(gt=0.0)
    leverage: float = Field(default=1.0, gt=0.0)
    initial_margin_usdt: float = Field(gt=0.0)

    # Returns & Price PnL
    gross_price_return: float = Field(description="(exit - entry) / entry")
    gross_return: float = Field(description="d * (exit - entry) / entry")
    gross_return_pct: float = Field(description="gross_return * 100.0")
    gross_return_bps: float = Field(description="gross_return * 10,000")
    gross_pnl_usdt: float = Field(description="entry_notional * gross_return")

    # Friction Breakdown
    entry_fee_usdt: float = Field(ge=0.0)
    exit_fee_usdt: float = Field(ge=0.0)
    total_fees_usdt: float = Field(ge=0.0)
    entry_slippage_usdt: float = Field(ge=0.0)
    exit_slippage_usdt: float = Field(ge=0.0)
    total_slippage_usdt: float = Field(ge=0.0)
    total_friction_usdt: float = Field(ge=0.0)

    # Funding Cash Flow
    funding_cash_flow_usdt: float = Field(description="Signed sum: CF > 0 received, CF < 0 paid")
    funding_settlements: List[FundingSettlement] = Field(default_factory=list)
    funding_data_status: str = Field(default=HISTORICAL_FUNDING_STATUS)

    # Net Realized Payoffs
    net_pnl_usdt: float = Field(description="gross_pnl - total_fees - total_slippage + funding_cash_flow")
    net_return: float = Field(description="net_pnl / entry_notional")
    net_return_pct: float = Field(description="net_return * 100.0")
    net_return_bps: float = Field(description="net_return * 10,000")

    # Normalized Drag Components in Basis Points
    fee_drag_bps: float = Field(description="total_fees / entry_notional * 10,000")
    slippage_drag_bps: float = Field(description="total_slippage / entry_notional * 10,000")
    funding_drag_bps: float = Field(description="-funding_cash_flow / entry_notional * 10,000")
    cost_basis_scope: str = Field(default=COST_BASIS_SCOPE_NOTE)


class OpenPositionAccountingResult(BaseModel):
    """Mark-to-market accounting snapshot for an unclosed position (e.g. at dataset end)."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    side: TradeSide
    direction: int
    open_quantity: float = Field(gt=0.0)
    entry_price: float = Field(gt=0.0)
    mark_price: float = Field(gt=0.0)
    entry_notional_usdt: float = Field(gt=0.0)
    mark_notional_usdt: float = Field(gt=0.0)
    initial_margin_usdt: float = Field(gt=0.0)
    accrued_entry_fee_usdt: float = Field(ge=0.0)
    accrued_entry_slippage_usdt: float = Field(ge=0.0)
    accrued_funding_cash_flow_usdt: float = Field(default=0.0)
    unrealized_gross_pnl_usdt: float
    unrealized_net_pnl_usdt: float = Field(
        description="unrealized_gross_pnl - accrued_entry_fee - accrued_entry_slippage + accrued_funding"
    )
    unrealized_gross_return: float
    unrealized_gross_return_bps: float
    unrealized_net_return: float
    unrealized_net_return_bps: float
    funding_data_status: str = Field(default=HISTORICAL_FUNDING_STATUS)


class PartialCloseResult(BaseModel):
    """Accounting ledger for partial position reduction."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    closed_accounting: TradeAccountingResult
    remaining_quantity: float = Field(ge=0.0)
    mark_price: float = Field(gt=0.0)
    remaining_entry_notional_usdt: float = Field(ge=0.0)
    unrealized_pnl_usdt: float = Field(description="Mark-to-market unrealized gross PnL on remaining quantity")
    unrealized_return: float = Field(description="d * (mark - entry) / entry")
    unrealized_return_bps: float = Field(description="unrealized_return * 10,000")


class PartialExitStepInput(BaseModel):
    """Specification of a single partial or final exit leg for lifecycle reconciliation."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    quantity: float = Field(gt=0.0)
    exit_price: float = Field(gt=0.0)
    funding_cash_flow_usdt: float = 0.0


class PositionLifecycleReconciliation(BaseModel):
    """Consolidated accounting reconciliation across multiple partial closes and remaining open quantity."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    side: TradeSide
    initial_quantity: float = Field(gt=0.0)
    closed_quantity_total: float = Field(ge=0.0)
    remaining_quantity: float = Field(ge=0.0)
    entry_price: float = Field(gt=0.0)
    initial_entry_notional_usdt: float = Field(gt=0.0)
    closed_entry_notional_usdt: float = Field(ge=0.0)
    remaining_entry_notional_usdt: float = Field(ge=0.0)
    closed_legs: List[TradeAccountingResult]
    open_position_snapshot: Optional[OpenPositionAccountingResult] = None
    total_realized_gross_pnl_usdt: float
    total_realized_fees_usdt: float
    total_realized_slippage_usdt: float
    total_realized_funding_usdt: float
    total_realized_net_pnl_usdt: float
    unrealized_gross_pnl_usdt: float
    unrealized_net_pnl_usdt: float
    combined_economic_equity_delta_usdt: float = Field(
        description="total_realized_net_pnl_usdt + unrealized_net_pnl_usdt"
    )
    quantity_conserved: bool
    notional_conserved: bool
    reconciliation_error_usdt: float
    cost_basis_scope: str = Field(default=COST_BASIS_SCOPE_NOTE)


def _validate_positive_finite(val: float, name: str) -> None:
    if not isinstance(val, (int, float)) or not math.isfinite(val) or val <= 0.0:
        raise ValueError(f"{name} must be finite and strictly positive, got {val}")


def _validate_non_negative_finite(val: float, name: str) -> None:
    if not isinstance(val, (int, float)) or not math.isfinite(val) or val < 0.0:
        raise ValueError(f"{name} must be finite and non-negative, got {val}")


def compute_two_legged_pnl(
    side: TradeSide,
    entry_price: float,
    exit_price: float,
    quantity: float,
    fee_rate_bps: float = 15.0,
    slippage_bps: float = 2.0,
    funding_cash_flow_usdt: float = 0.0,
    funding_settlements: Optional[List[FundingSettlement]] = None,
    leverage: float = 1.0,
) -> TradeAccountingResult:
    """Compute exact two-legged entry/exit financial accounting."""
    _validate_positive_finite(entry_price, "entry_price")
    _validate_positive_finite(exit_price, "exit_price")
    _validate_positive_finite(quantity, "quantity")
    _validate_non_negative_finite(fee_rate_bps, "fee_rate_bps")
    _validate_non_negative_finite(slippage_bps, "slippage_bps")
    _validate_positive_finite(leverage, "leverage")
    if not math.isfinite(funding_cash_flow_usdt):
        raise ValueError(f"funding_cash_flow_usdt must be finite, got {funding_cash_flow_usdt}")

    d = 1 if side == TradeSide.LONG else -1

    # 1. Notionals & Margin
    n_entry = quantity * entry_price
    n_exit = quantity * exit_price
    init_margin = n_entry / leverage

    # 2. Price Returns & Gross PnL
    r_price = (exit_price - entry_price) / entry_price
    r_gross = d * r_price
    pnl_gross = n_entry * r_gross

    # 3. Frictional Costs (Fees and Half-Spread Slippage)
    c_fee_rate = fee_rate_bps / 10_000.0
    c_slip_rate = slippage_bps / 10_000.0

    # Effective fill prices (adverse half-spread impact on both entry and exit)
    entry_fill_eff = entry_price * (1.0 + d * c_slip_rate)
    exit_fill_eff = max(1e-12, exit_price * (1.0 - d * c_slip_rate))

    fee_entry = n_entry * c_fee_rate
    fee_exit = n_exit * c_fee_rate
    total_fees = fee_entry + fee_exit

    slip_entry = n_entry * c_slip_rate
    slip_exit = n_exit * c_slip_rate
    total_slip = slip_entry + slip_exit

    total_friction = total_fees + total_slip

    # 4. Net Financial Payoff: PnL_net = PnL_gross - C_fees - C_exec + CF_funding
    cf_funding = funding_cash_flow_usdt
    pnl_net = pnl_gross - total_fees - total_slip + cf_funding
    r_net = pnl_net / n_entry
    pct_net = r_net * 100.0
    bps_net = r_net * 10_000.0

    # Normalized Drags
    fee_drag_bps = (total_fees / n_entry) * 10_000.0
    slip_drag_bps = (total_slip / n_entry) * 10_000.0
    funding_drag_bps = (-cf_funding / n_entry) * 10_000.0

    return TradeAccountingResult(
        side=side,
        direction=d,
        quantity=round(quantity, 8),
        entry_price=round(entry_price, 8),
        exit_price=round(exit_price, 8),
        entry_fill_price_effective=round(entry_fill_eff, 8),
        exit_fill_price_effective=round(exit_fill_eff, 8),
        entry_notional_usdt=round(n_entry, 6),
        exit_notional_usdt=round(n_exit, 6),
        leverage=round(leverage, 4),
        initial_margin_usdt=round(init_margin, 6),
        gross_price_return=round(r_price, 8),
        gross_return=round(r_gross, 8),
        gross_return_pct=round(r_gross * 100.0, 6),
        gross_return_bps=round(r_gross * 10_000.0, 4),
        gross_pnl_usdt=round(pnl_gross, 6),
        entry_fee_usdt=round(fee_entry, 6),
        exit_fee_usdt=round(fee_exit, 6),
        total_fees_usdt=round(total_fees, 6),
        entry_slippage_usdt=round(slip_entry, 6),
        exit_slippage_usdt=round(slip_exit, 6),
        total_slippage_usdt=round(total_slip, 6),
        total_friction_usdt=round(total_friction, 6),
        funding_cash_flow_usdt=round(cf_funding, 6),
        funding_settlements=funding_settlements or [],
        net_pnl_usdt=round(pnl_net, 6),
        net_return=round(r_net, 8),
        net_return_pct=round(pct_net, 6),
        net_return_bps=round(bps_net, 4),
        fee_drag_bps=round(fee_drag_bps, 4),
        slippage_drag_bps=round(slip_drag_bps, 4),
        funding_drag_bps=round(funding_drag_bps, 4),
    )


def calculate_funding_cash_flow(
    side: TradeSide,
    entry_notional: float,
    entry_time_ms: int,
    exit_time_ms: int,
    funding_rate_bps_per_settlement: float = 1.0,
) -> Tuple[float, List[FundingSettlement]]:
    """Compute signed funding cash flow across discrete 8-hour settlement intervals.

    Convention:
    - Long pays funding if rate > 0 (cash outflow, negative CF).
    - Long receives funding if rate < 0 (cash inflow, positive CF).
    - Short receives funding if rate > 0 (cash inflow, positive CF).
    - Short pays funding if rate < 0 (cash outflow, negative CF).
    - Boundary rule: t_entry < t_settle <= t_exit.
    """
    _validate_positive_finite(entry_notional, "entry_notional")
    if entry_time_ms >= exit_time_ms:
        raise ValueError(f"entry_time_ms {entry_time_ms} must be strictly less than exit_time_ms {exit_time_ms}")

    settlement_ms = 8 * 3600 * 1000  # 28,800,000 ms
    d = 1 if side == TradeSide.LONG else -1

    # Strictly greater than entry_time_ms: floor to multiple of 8h, then add 8h
    first_settle = ((entry_time_ms // settlement_ms) + 1) * settlement_ms

    settlements: List[FundingSettlement] = []
    current_settle = first_settle
    rate_factor = funding_rate_bps_per_settlement / 10_000.0

    while current_settle <= exit_time_ms:
        cf = -d * rate_factor * entry_notional
        settlements.append(
            FundingSettlement(
                timestamp_ms=current_settle,
                rate_bps=funding_rate_bps_per_settlement,
                cash_flow_usdt=round(cf, 6),
            )
        )
        current_settle += settlement_ms

    total_cf = sum(s.cash_flow_usdt for s in settlements)
    return round(total_cf, 6), settlements


def compute_open_position_accounting(
    side: TradeSide,
    entry_price: float,
    mark_price: float,
    open_quantity: float,
    fee_rate_bps: float = 15.0,
    slippage_bps: float = 2.0,
    accrued_funding_cash_flow_usdt: float = 0.0,
    leverage: float = 1.0,
) -> OpenPositionAccountingResult:
    """Compute mark-to-market unrealized accounting for an open position (e.g. at dataset end)."""
    _validate_positive_finite(entry_price, "entry_price")
    _validate_positive_finite(mark_price, "mark_price")
    _validate_positive_finite(open_quantity, "open_quantity")
    _validate_non_negative_finite(fee_rate_bps, "fee_rate_bps")
    _validate_non_negative_finite(slippage_bps, "slippage_bps")
    _validate_positive_finite(leverage, "leverage")

    d = 1 if side == TradeSide.LONG else -1
    n_entry = open_quantity * entry_price
    n_mark = open_quantity * mark_price
    init_margin = n_entry / leverage

    accrued_fee = n_entry * (fee_rate_bps / 10_000.0)
    accrued_slip = n_entry * (slippage_bps / 10_000.0)

    unreal_gross_ret = d * ((mark_price - entry_price) / entry_price)
    unreal_gross_pnl = n_entry * unreal_gross_ret
    unreal_net_pnl = unreal_gross_pnl - accrued_fee - accrued_slip + accrued_funding_cash_flow_usdt
    unreal_net_ret = unreal_net_pnl / n_entry

    return OpenPositionAccountingResult(
        side=side,
        direction=d,
        open_quantity=round(open_quantity, 8),
        entry_price=round(entry_price, 8),
        mark_price=round(mark_price, 8),
        entry_notional_usdt=round(n_entry, 6),
        mark_notional_usdt=round(n_mark, 6),
        initial_margin_usdt=round(init_margin, 6),
        accrued_entry_fee_usdt=round(accrued_fee, 6),
        accrued_entry_slippage_usdt=round(accrued_slip, 6),
        accrued_funding_cash_flow_usdt=round(accrued_funding_cash_flow_usdt, 6),
        unrealized_gross_pnl_usdt=round(unreal_gross_pnl, 6),
        unrealized_net_pnl_usdt=round(unreal_net_pnl, 6),
        unrealized_gross_return=round(unreal_gross_ret, 8),
        unrealized_gross_return_bps=round(unreal_gross_ret * 10_000.0, 4),
        unrealized_net_return=round(unreal_net_ret, 8),
        unrealized_net_return_bps=round(unreal_net_ret * 10_000.0, 4),
    )


def compute_partial_close(
    side: TradeSide,
    entry_price: float,
    close_price: float,
    mark_price: float,
    closed_quantity: float,
    remaining_quantity: float,
    fee_rate_bps: float = 15.0,
    slippage_bps: float = 2.0,
    funding_cash_flow_usdt: float = 0.0,
) -> PartialCloseResult:
    """Compute accounting for partial position close and mark-to-market remainder."""
    _validate_positive_finite(mark_price, "mark_price")
    _validate_non_negative_finite(remaining_quantity, "remaining_quantity")

    closed_acc = compute_two_legged_pnl(
        side=side,
        entry_price=entry_price,
        exit_price=close_price,
        quantity=closed_quantity,
        fee_rate_bps=fee_rate_bps,
        slippage_bps=slippage_bps,
        funding_cash_flow_usdt=funding_cash_flow_usdt,
    )

    d = 1 if side == TradeSide.LONG else -1
    rem_notional = remaining_quantity * entry_price if remaining_quantity > 0.0 else 0.0
    unreal_ret = d * ((mark_price - entry_price) / entry_price) if remaining_quantity > 0.0 else 0.0
    unreal_pnl = rem_notional * unreal_ret if remaining_quantity > 0.0 else 0.0

    return PartialCloseResult(
        closed_accounting=closed_acc,
        remaining_quantity=round(remaining_quantity, 8),
        mark_price=round(mark_price, 8),
        remaining_entry_notional_usdt=round(rem_notional, 6),
        unrealized_pnl_usdt=round(unreal_pnl, 6),
        unrealized_return=round(unreal_ret, 8),
        unrealized_return_bps=round(unreal_ret * 10_000.0, 4),
    )


def reconcile_position_lifecycle(
    side: TradeSide,
    initial_quantity: float,
    entry_price: float,
    partial_exits: Sequence[PartialExitStepInput],
    final_mark_price: Optional[float] = None,
    fee_rate_bps: float = 15.0,
    slippage_bps: float = 2.0,
    open_funding_cash_flow_usdt: float = 0.0,
    leverage: float = 1.0,
) -> PositionLifecycleReconciliation:
    """Reconcile multi-step partial closes and optional remaining open quantity at dataset end."""
    _validate_positive_finite(initial_quantity, "initial_quantity")
    _validate_positive_finite(entry_price, "entry_price")
    _validate_non_negative_finite(fee_rate_bps, "fee_rate_bps")
    _validate_non_negative_finite(slippage_bps, "slippage_bps")

    closed_qty_total = sum(step.quantity for step in partial_exits)
    if round(closed_qty_total, 8) > round(initial_quantity + 1e-8, 8):
        raise ValueError(
            f"Cumulative closed quantity ({closed_qty_total}) exceeds initial_quantity ({initial_quantity})"
        )

    rem_qty = max(0.0, round(initial_quantity - closed_qty_total, 8))
    if rem_qty > 1e-8 and final_mark_price is None:
        raise ValueError("final_mark_price is required when remaining_quantity > 0")

    closed_legs: List[TradeAccountingResult] = []
    for step in partial_exits:
        leg_acc = compute_two_legged_pnl(
            side=side,
            entry_price=entry_price,
            exit_price=step.exit_price,
            quantity=step.quantity,
            fee_rate_bps=fee_rate_bps,
            slippage_bps=slippage_bps,
            funding_cash_flow_usdt=step.funding_cash_flow_usdt,
            leverage=leverage,
        )
        closed_legs.append(leg_acc)

    open_snap: Optional[OpenPositionAccountingResult] = None
    if rem_qty > 1e-8 and final_mark_price is not None:
        open_snap = compute_open_position_accounting(
            side=side,
            entry_price=entry_price,
            mark_price=final_mark_price,
            open_quantity=rem_qty,
            fee_rate_bps=fee_rate_bps,
            slippage_bps=slippage_bps,
            accrued_funding_cash_flow_usdt=open_funding_cash_flow_usdt,
            leverage=leverage,
        )

    init_notional = initial_quantity * entry_price
    closed_notional = sum(leg.entry_notional_usdt for leg in closed_legs)
    rem_notional = open_snap.entry_notional_usdt if open_snap is not None else 0.0

    tot_real_gross = sum(leg.gross_pnl_usdt for leg in closed_legs)
    tot_real_fees = sum(leg.total_fees_usdt for leg in closed_legs)
    tot_real_slip = sum(leg.total_slippage_usdt for leg in closed_legs)
    tot_real_fund = sum(leg.funding_cash_flow_usdt for leg in closed_legs)
    tot_real_net = sum(leg.net_pnl_usdt for leg in closed_legs)

    unreal_gross = open_snap.unrealized_gross_pnl_usdt if open_snap is not None else 0.0
    unreal_net = open_snap.unrealized_net_pnl_usdt if open_snap is not None else 0.0

    expected_real_net = tot_real_gross - tot_real_fees - tot_real_slip + tot_real_fund
    recon_err = abs(tot_real_net - expected_real_net)

    qty_ok = abs((closed_qty_total + rem_qty) - initial_quantity) <= 1e-6
    notional_ok = abs((closed_notional + rem_notional) - init_notional) <= 1e-4

    return PositionLifecycleReconciliation(
        side=side,
        initial_quantity=round(initial_quantity, 8),
        closed_quantity_total=round(closed_qty_total, 8),
        remaining_quantity=rem_qty,
        entry_price=round(entry_price, 8),
        initial_entry_notional_usdt=round(init_notional, 6),
        closed_entry_notional_usdt=round(closed_notional, 6),
        remaining_entry_notional_usdt=round(rem_notional, 6),
        closed_legs=closed_legs,
        open_position_snapshot=open_snap,
        total_realized_gross_pnl_usdt=round(tot_real_gross, 6),
        total_realized_fees_usdt=round(tot_real_fees, 6),
        total_realized_slippage_usdt=round(tot_real_slip, 6),
        total_realized_funding_usdt=round(tot_real_fund, 6),
        total_realized_net_pnl_usdt=round(tot_real_net, 6),
        unrealized_gross_pnl_usdt=round(unreal_gross, 6),
        unrealized_net_pnl_usdt=round(unreal_net, 6),
        combined_economic_equity_delta_usdt=round(tot_real_net + unreal_net, 6),
        quantity_conserved=qty_ok,
        notional_conserved=notional_ok,
        reconciliation_error_usdt=round(recon_err, 8),
    )
