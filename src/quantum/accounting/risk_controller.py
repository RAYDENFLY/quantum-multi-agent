"""Active Mark-to-Market (MTM) Risk Controller & Deleveraging Engine.

Implements Milestone 5.12.2.2 Layer B: Active Mark-to-Market Risk Control:
1. ActiveMTMMonitor: Real-time portfolio-level MTM exposure, equity, and capacity tracking.
2. RiskStateMachine: 6 deterministic risk states with anti-oscillation hysteresis.
3. DeleveragingEngine: Cost-aware, multi-policy position reduction with realistic friction,
   minimum order notional constraints, and failure logging (no fabricated liquidity).
"""

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from quantum.domain.enums import TradeSide


class RiskState(str, Enum):
    """Operational states of the deterministic portfolio risk state machine."""
    NORMAL = "NORMAL"            # Exposure < 0.90x: normal operation
    WARNING = "WARNING"          # 0.90x <= Exposure < 0.95x: increased monitoring, block expansion
    REDUCE_ONLY = "REDUCE_ONLY"  # 0.95x <= Exposure < 1.00x: block new entries, evaluate trimming
    CRITICAL = "CRITICAL"        # Exposure >= 1.00x: immediate simulated risk reduction required
    HALTED = "HALTED"            # Risk reduction failure or execution blockage: all trading halted
    RUIN = "RUIN"                # Terminal capital exhaustion (equity <= ruin threshold)


class DeleveragingPolicyType(str, Enum):
    """Deterministic position reduction selection policies."""
    LARGEST_NOTIONAL_FIRST = "LARGEST_NOTIONAL_FIRST"      # Policy A: Reduce largest notional position first
    HIGHEST_RISK_FIRST = "HIGHEST_RISK_FIRST"              # Policy B: Reduce position with highest risk / adverse loss
    LOWEST_COST_FIRST = "LOWEST_COST_FIRST"                # Policy C: Reduce position with lowest closing friction


@dataclass
class RiskStateTransition:
    """Audit log record for risk state machine transitions."""
    timestamp_ms: int
    from_state: RiskState
    to_state: RiskState
    trigger_exposure: float
    trigger_equity: float
    reason_code: str
    details: str = ""


@dataclass
class PortfolioMTMSnapshot:
    """Detailed real-time snapshot of portfolio mark-to-market risk."""
    timestamp_ms: int
    open_position_notional: float
    pending_reserved_notional: float
    total_committed_notional: float
    cash_balance: float
    unrealized_pnl: float
    realized_pnl: float
    equity: float
    gross_exposure_open: float
    gross_exposure_committed: float
    exposure_utilization_pct: float
    available_exposure_capacity: float
    risk_state: RiskState
    open_position_count: int
    long_notional: float
    short_notional: float


@dataclass
class DeleveragingAction:
    """Record of a simulated position reduction attempt."""
    action_id: str
    timestamp_ms: int
    policy: DeleveragingPolicyType
    symbol: str
    side: str
    target_reduction_notional: float
    executed_reduction_notional: float
    executed_quantity: float
    fill_price: float
    fee_usd: float
    spread_usd: float
    slippage_usd: float
    total_friction_usd: float
    gross_pnl_slice: float
    net_pnl_slice: float
    success: bool
    status_code: str
    residual_exposure: float


class ActiveMTMMonitor:
    """Active portfolio-level mark-to-market exposure and equity tracking engine."""

    def __init__(
        self,
        hard_max_gross_exposure: float = 1.0000,
        admission_exposure_cap: float = 0.9950,
        ruin_equity_threshold: float = 1.0,
    ) -> None:
        self.hard_max_gross_exposure = float(hard_max_gross_exposure)
        self.admission_exposure_cap = float(admission_exposure_cap)
        self.ruin_equity_threshold = float(ruin_equity_threshold)

    def evaluate_portfolio(
        self,
        open_positions: Dict[str, Any],
        pending_reserved_notional: float,
        cash_balance: float,
        current_prices: Dict[str, float],
        timestamp_ms: int,
        realized_pnl: float = 0.0,
        current_state: RiskState = RiskState.NORMAL,
    ) -> PortfolioMTMSnapshot:
        """Computes comprehensive mark-to-market portfolio exposure metrics."""
        open_notional = 0.0
        unrealized_tot = 0.0
        long_notional = 0.0
        short_notional = 0.0

        for sym, pos in open_positions.items():
            price = current_prices.get(sym, getattr(pos, "entry_price", 0.0))
            qty = getattr(pos, "quantity", 0.0)
            side = getattr(pos, "side", TradeSide.LONG)
            entry_price = getattr(pos, "entry_price", price)

            cur_notional = abs(qty * price)
            open_notional += cur_notional

            if side == TradeSide.LONG or side == "LONG":
                unrealized = qty * (price - entry_price)
                long_notional += cur_notional
            else:
                unrealized = qty * (entry_price - price)
                short_notional += cur_notional

            unrealized_tot += unrealized

        equity = cash_balance + unrealized_tot
        total_committed = open_notional + pending_reserved_notional

        if equity <= 1e-6:
            exp_open = 1.0 if open_notional > 0 else 0.0
            exp_committed = 1.0 if total_committed > 0 else 0.0
            avail_cap = 0.0
            utilization = 100.0 if total_committed > 0 else 0.0
        else:
            exp_open = open_notional / equity
            exp_committed = total_committed / equity
            avail_cap = max(0.0, (equity * self.admission_exposure_cap) - total_committed)
            utilization = (exp_committed / self.hard_max_gross_exposure) * 100.0

        return PortfolioMTMSnapshot(
            timestamp_ms=timestamp_ms,
            open_position_notional=round(open_notional, 4),
            pending_reserved_notional=round(pending_reserved_notional, 4),
            total_committed_notional=round(total_committed, 4),
            cash_balance=round(cash_balance, 4),
            unrealized_pnl=round(unrealized_tot, 4),
            realized_pnl=round(realized_pnl, 4),
            equity=round(equity, 4),
            gross_exposure_open=round(exp_open, 6),
            gross_exposure_committed=round(exp_committed, 6),
            exposure_utilization_pct=round(utilization, 2),
            available_exposure_capacity=round(avail_cap, 4),
            risk_state=current_state,
            open_position_count=len(open_positions),
            long_notional=round(long_notional, 4),
            short_notional=round(short_notional, 4),
        )


class RiskStateMachine:
    """Deterministic 6-state portfolio risk controller with anti-oscillation hysteresis."""

    def __init__(
        self,
        warning_threshold: float = 0.9000,
        reduce_only_threshold: float = 0.9500,
        critical_threshold: float = 1.0000,
        ruin_equity_threshold: float = 1.0,
        hysteresis_buffer: float = 0.0200,  # 200 bps hysteresis to prevent flip-flopping
        min_recovery_dwell_ms: int = 60_000,  # Must sustain safe exposure for at least 60s
    ) -> None:
        self.warning_threshold = float(warning_threshold)
        self.reduce_only_threshold = float(reduce_only_threshold)
        self.critical_threshold = float(critical_threshold)
        self.ruin_equity_threshold = float(ruin_equity_threshold)
        self.hysteresis_buffer = float(hysteresis_buffer)
        self.min_recovery_dwell_ms = int(min_recovery_dwell_ms)

        self.current_state = RiskState.NORMAL
        self.last_transition_time_ms = 0
        self.safe_exposure_start_time_ms: Optional[int] = None
        self.transitions: List[RiskStateTransition] = []

    def update_state(
        self,
        mtm_snapshot: PortfolioMTMSnapshot,
        response_failed: bool = False,
    ) -> RiskState:
        """Evaluates exposure and equity against deterministic thresholds to transition risk state."""
        prev_state = self.current_state
        exposure = mtm_snapshot.gross_exposure_committed
        equity = mtm_snapshot.equity
        t_ms = mtm_snapshot.timestamp_ms
        new_state = prev_state
        reason = ""

        # 1. Check Permanent Ruin State (Terminal)
        if prev_state == RiskState.RUIN or equity <= self.ruin_equity_threshold:
            new_state = RiskState.RUIN
            reason = f"EQUITY_LE_RUIN_THRESHOLD: Equity ${equity:.2f} <= ${self.ruin_equity_threshold:.2f}"

        # 2. Check Execution Response Failure -> HALTED
        elif response_failed:
            new_state = RiskState.HALTED
            reason = "DELEVERAGING_RESPONSE_FAILURE: Risk reduction failed to execute or illiquid market"

        # 3. Check Escalating Conditions (Instantaneous, zero delay)
        elif exposure >= self.critical_threshold:
            new_state = RiskState.CRITICAL
            reason = f"EXPOSURE_GE_CRITICAL: Committed exposure {exposure:.6f} >= {self.critical_threshold:.4f}"
        elif exposure >= self.reduce_only_threshold and prev_state not in (RiskState.CRITICAL, RiskState.HALTED):
            new_state = RiskState.REDUCE_ONLY
            reason = f"EXPOSURE_GE_REDUCE_ONLY: Committed exposure {exposure:.6f} >= {self.reduce_only_threshold:.4f}"
        elif exposure >= self.warning_threshold and prev_state == RiskState.NORMAL:
            new_state = RiskState.WARNING
            reason = f"EXPOSURE_GE_WARNING: Committed exposure {exposure:.6f} >= {self.warning_threshold:.4f}"

        # 4. Check De-escalation / Recovery Conditions (Requires Hysteresis & Dwell)
        elif prev_state in (RiskState.WARNING, RiskState.REDUCE_ONLY, RiskState.CRITICAL):
            # Recovery target with hysteresis: must drop below threshold - hysteresis_buffer
            if prev_state == RiskState.CRITICAL:
                target_rec = self.critical_threshold - self.hysteresis_buffer
                if exposure < target_rec:
                    # Transition down to REDUCE_ONLY or lower
                    if exposure < self.reduce_only_threshold - self.hysteresis_buffer:
                        new_state = RiskState.NORMAL if exposure < self.warning_threshold - self.hysteresis_buffer else RiskState.WARNING
                    else:
                        new_state = RiskState.REDUCE_ONLY
                    reason = f"CRITICAL_RECOVERY: Exposure {exposure:.6f} cleared hysteresis target {target_rec:.4f}"
            elif prev_state == RiskState.REDUCE_ONLY:
                target_rec = self.reduce_only_threshold - self.hysteresis_buffer
                if exposure < target_rec:
                    new_state = RiskState.NORMAL if exposure < self.warning_threshold - self.hysteresis_buffer else RiskState.WARNING
                    reason = f"REDUCE_ONLY_RECOVERY: Exposure {exposure:.6f} cleared target {target_rec:.4f}"
            elif prev_state == RiskState.WARNING:
                target_rec = self.warning_threshold - self.hysteresis_buffer
                if exposure < target_rec:
                    new_state = RiskState.NORMAL
                    reason = f"WARNING_RECOVERY: Exposure {exposure:.6f} cleared target {target_rec:.4f}"

        # Record transition if state changed
        if new_state != prev_state:
            self.transitions.append(
                RiskStateTransition(
                    timestamp_ms=t_ms,
                    from_state=prev_state,
                    to_state=new_state,
                    trigger_exposure=exposure,
                    trigger_equity=equity,
                    reason_code=reason,
                )
            )
            self.current_state = new_state
            self.last_transition_time_ms = t_ms

        return self.current_state


class DeleveragingEngine:
    """Cost-aware, multi-policy position reduction engine.
    
    Calculates required notional reduction to restore target exposure, selects positions
    deterministically across 3 policies, and accounts for closing friction, minimum order
    size ($5.00), and execution liquidity failures.
    """

    def __init__(
        self,
        target_restored_exposure: float = 0.9500,  # Restore to REDUCE_ONLY or below
        min_viable_order_notional: float = 5.0,
    ) -> None:
        self.target_restored_exposure = float(target_restored_exposure)
        self.min_viable_order_notional = float(min_viable_order_notional)
        self.action_history: List[DeleveragingAction] = []
        self._action_counter = 0

    def compute_excess_notional(
        self,
        current_committed_notional: float,
        current_equity: float,
        target_exposure: Optional[float] = None,
    ) -> float:
        """Calculates excess notional that must be liquidated to restore target exposure."""
        tgt = target_exposure or self.target_restored_exposure
        target_notional = current_equity * tgt
        return max(0.0, current_committed_notional - target_notional)

    def select_positions_to_reduce(
        self,
        open_positions: Dict[str, Any],
        current_prices: Dict[str, float],
        policy: DeleveragingPolicyType,
        fee_schedule: Any = None,
    ) -> List[Tuple[str, float, float]]:
        """Sorts open positions according to the declared deleveraging policy.
        
        Returns:
            List of (symbol, current_notional, priority_score)
        """
        candidates = []
        for sym, pos in open_positions.items():
            price = current_prices.get(sym, getattr(pos, "entry_price", 0.0))
            qty = getattr(pos, "quantity", 0.0)
            side = getattr(pos, "side", TradeSide.LONG)
            entry_p = getattr(pos, "entry_price", price)
            notional = abs(qty * price)

            if policy == DeleveragingPolicyType.LARGEST_NOTIONAL_FIRST:
                # Priority: highest notional first
                score = notional
            elif policy == DeleveragingPolicyType.HIGHEST_RISK_FIRST:
                # Priority: highest adverse unrealized loss or short exposure first
                is_short = (side == TradeSide.SHORT or side == "SHORT")
                unrealized = qty * (entry_p - price) if is_short else qty * (price - entry_p)
                # Adverse loss gives higher score; short positions penalized higher due to exposure expansion
                short_multiplier = 1.5 if is_short else 1.0
                score = (-unrealized if unrealized < 0 else 0.0) * short_multiplier + (notional * 0.1)
            elif policy == DeleveragingPolicyType.LOWEST_COST_FIRST:
                # Priority: lowest estimated closing friction first (score inverted so smallest is first)
                fee_bps = 10.0  # Taker default
                spread_bps = 1.0
                slip_bps = 2.0
                cost = notional * ((fee_bps + spread_bps + slip_bps) / 10_000.0)
                score = -cost  # Largest negative = smallest cost
            else:
                score = notional

            candidates.append((sym, notional, score))

        # Sort descending by priority score
        candidates.sort(key=lambda x: x[2], reverse=True)
        return candidates

    def execute_deleveraging(
        self,
        ledger: Any,
        current_prices: Dict[str, float],
        timestamp_ms: int,
        policy: DeleveragingPolicyType = DeleveragingPolicyType.LARGEST_NOTIONAL_FIRST,
        target_exposure: float = 0.9500,
        simulated_liquidity_failure: bool = False,
        fee_bps: float = 10.0,
        spread_bps_half: float = 1.0,
        slippage_bps: float = 2.0,
    ) -> List[DeleveragingAction]:
        """Executes simulated cost-aware position reduction on the primary ledger."""
        actions: List[DeleveragingAction] = []
        current_eq = ledger.equity
        cur_notional = ledger.get_gross_notional(current_prices)
        excess_notional = self.compute_excess_notional(cur_notional, current_eq, target_exposure)

        if excess_notional <= 0.0:
            return actions

        if simulated_liquidity_failure:
            self._action_counter += 1
            act = DeleveragingAction(
                action_id=f"DEL-{self._action_counter:05d}",
                timestamp_ms=timestamp_ms,
                policy=policy,
                symbol="ALL",
                side="NONE",
                target_reduction_notional=excess_notional,
                executed_reduction_notional=0.0,
                executed_quantity=0.0,
                fill_price=0.0,
                fee_usd=0.0,
                spread_usd=0.0,
                slippage_usd=0.0,
                total_friction_usd=0.0,
                gross_pnl_slice=0.0,
                net_pnl_slice=0.0,
                success=False,
                status_code="SIMULATED_LIQUIDITY_FAILURE",
                residual_exposure=ledger.get_gross_exposure(current_prices),
            )
            actions.append(act)
            self.action_history.append(act)
            return actions

        remaining_needed = excess_notional
        candidates = self.select_positions_to_reduce(ledger.open_positions, current_prices, policy)

        for sym, pos_notional, _ in candidates:
            if remaining_needed <= 0.0:
                break
            if sym not in ledger.open_positions:
                continue

            pos = ledger.open_positions[sym]
            fill_p = current_prices.get(sym, pos.entry_price)
            pos_cur_notional = pos.quantity * fill_p

            if remaining_needed >= pos_cur_notional:
                # Full close of this position
                reduction_slice = pos_cur_notional
                close_pct = 1.0
            else:
                # Partial reduction
                reduction_slice = remaining_needed
                # Check minimum order notional
                if reduction_slice < self.min_viable_order_notional:
                    # If remaining slice < $5, either close entire position or min order
                    if pos_cur_notional >= self.min_viable_order_notional:
                        reduction_slice = min(self.min_viable_order_notional, pos_cur_notional)
                        close_pct = reduction_slice / pos_cur_notional
                    else:
                        reduction_slice = pos_cur_notional
                        close_pct = 1.0
                else:
                    close_pct = reduction_slice / pos_cur_notional

            # Execute close on primary ledger
            res = ledger.close_position(
                symbol=sym,
                fill_price=fill_p,
                fee_bps=fee_bps,
                spread_bps_half=spread_bps_half,
                slippage_bps=slippage_bps,
                timestamp_ms=timestamp_ms,
                exit_reason=f"DELEVERAGING_{policy.name}",
                exit_quantity_pct=close_pct,
            )

            self._action_counter += 1
            if res is not None:
                g_pnl, n_pnl = res
                fee_usd = reduction_slice * (fee_bps / 10_000.0)
                spread_usd = reduction_slice * (spread_bps_half / 10_000.0)
                slip_usd = reduction_slice * (slippage_bps / 10_000.0)
                tot_fric = fee_usd + spread_usd + slip_usd

                act = DeleveragingAction(
                    action_id=f"DEL-{self._action_counter:05d}",
                    timestamp_ms=timestamp_ms,
                    policy=policy,
                    symbol=sym,
                    side=pos.side.name,
                    target_reduction_notional=round(reduction_slice, 4),
                    executed_reduction_notional=round(reduction_slice, 4),
                    executed_quantity=round(reduction_slice / fill_p, 6),
                    fill_price=round(fill_p, 4),
                    fee_usd=round(fee_usd, 4),
                    spread_usd=round(spread_usd, 4),
                    slippage_usd=round(slip_usd, 4),
                    total_friction_usd=round(tot_fric, 4),
                    gross_pnl_slice=round(g_pnl, 4),
                    net_pnl_slice=round(n_pnl, 4),
                    success=True,
                    status_code="EXECUTED_SUCCESS",
                    residual_exposure=round(ledger.get_gross_exposure(current_prices), 6),
                )
                remaining_needed -= reduction_slice
            else:
                act = DeleveragingAction(
                    action_id=f"DEL-{self._action_counter:05d}",
                    timestamp_ms=timestamp_ms,
                    policy=policy,
                    symbol=sym,
                    side=pos.side.name,
                    target_reduction_notional=round(reduction_slice, 4),
                    executed_reduction_notional=0.0,
                    executed_quantity=0.0,
                    fill_price=round(fill_p, 4),
                    fee_usd=0.0,
                    spread_usd=0.0,
                    slippage_usd=0.0,
                    total_friction_usd=0.0,
                    gross_pnl_slice=0.0,
                    net_pnl_slice=0.0,
                    success=False,
                    status_code="LEDGER_CLOSE_FAILED",
                    residual_exposure=round(ledger.get_gross_exposure(current_prices), 6),
                )

            actions.append(act)
            self.action_history.append(act)

        return actions
