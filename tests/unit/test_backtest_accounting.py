"""Unit tests for Reference-Price PnL Accounting Engine (Workstream D).

Verifies all 20 required accounting scenarios:
1. Long profit (Canonical Case 1).
2. Long loss (Canonical Case 2).
3. Short profit (Canonical Case 3).
4. Short loss (Canonical Case 4).
5. Entry fee isolation.
6. Exit fee isolation.
7. Fee asymmetry between winning and losing trades.
8. Half-spread execution cost and effective fill prices.
9. Positive funding cash flow (CF > 0 received).
10. Negative funding cash flow (CF < 0 paid).
11. Multiple funding settlements across multi-period holds.
12. Funding settlement strict boundary rule (t_entry < t_settle <= t_exit).
13. Single partial close.
14. Multiple partial closes.
15. Remaining unrealized position mark-to-market.
16. Full close via multi-step reconciliation.
17. Open position at end of dataset.
18. Zero quantity handling.
19. Invalid price handling.
20. Unit and conservation reconciliation (BPS, pct, USDT, notional, margin, quantity).
"""

import math
import pytest

from quantum.backtesting.accounting import (
    HISTORICAL_FUNDING_STATUS,
    PartialExitStepInput,
    calculate_funding_cash_flow,
    compute_open_position_accounting,
    compute_partial_close,
    compute_two_legged_pnl,
    reconcile_position_lifecycle,
)
from quantum.domain.enums import TradeSide


def test_case_1_long_profitable():
    """Scenario 1: Canonical Long profitable (+150 bps gross), 15 bps fee, 0 slippage."""
    res = compute_two_legged_pnl(
        side=TradeSide.LONG,
        entry_price=100.0,
        exit_price=101.5,
        quantity=10.0,
        fee_rate_bps=15.0,
        slippage_bps=0.0,
        funding_cash_flow_usdt=0.0,
    )
    assert res.entry_notional_usdt == pytest.approx(1000.0)
    assert res.exit_notional_usdt == pytest.approx(1015.0)
    assert res.gross_return == pytest.approx(0.015)
    assert res.gross_return_pct == pytest.approx(1.5)
    assert res.gross_return_bps == pytest.approx(150.0)
    assert res.gross_pnl_usdt == pytest.approx(15.0)
    assert res.entry_fee_usdt == pytest.approx(1.5)
    assert res.exit_fee_usdt == pytest.approx(1.5225)
    assert res.total_fees_usdt == pytest.approx(3.0225)
    assert res.net_pnl_usdt == pytest.approx(11.9775)
    assert res.net_return_bps == pytest.approx(119.775)


def test_case_2_long_losing():
    """Scenario 2: Canonical Long losing (-150 bps gross), 15 bps fee, 0 slippage."""
    res = compute_two_legged_pnl(
        side=TradeSide.LONG,
        entry_price=100.0,
        exit_price=98.5,
        quantity=10.0,
        fee_rate_bps=15.0,
        slippage_bps=0.0,
        funding_cash_flow_usdt=0.0,
    )
    assert res.exit_notional_usdt == pytest.approx(985.0)
    assert res.gross_pnl_usdt == pytest.approx(-15.0)
    assert res.entry_fee_usdt == pytest.approx(1.5)
    assert res.exit_fee_usdt == pytest.approx(1.4775)
    assert res.total_fees_usdt == pytest.approx(2.9775)
    assert res.net_pnl_usdt == pytest.approx(-17.9775)
    assert res.net_return_bps == pytest.approx(-179.775)


def test_case_3_short_profitable():
    """Scenario 3: Canonical Short profitable (+150 bps gross), 15 bps fee, 0 slippage."""
    res = compute_two_legged_pnl(
        side=TradeSide.SHORT,
        entry_price=100.0,
        exit_price=98.5,
        quantity=10.0,
        fee_rate_bps=15.0,
        slippage_bps=0.0,
        funding_cash_flow_usdt=0.0,
    )
    assert res.exit_notional_usdt == pytest.approx(985.0)
    assert res.gross_pnl_usdt == pytest.approx(15.0)
    assert res.total_fees_usdt == pytest.approx(2.9775)
    assert res.net_pnl_usdt == pytest.approx(12.0225)
    assert res.net_return_bps == pytest.approx(120.225)


def test_case_4_short_losing():
    """Scenario 4: Canonical Short losing (-150 bps gross), 15 bps fee, 0 slippage."""
    res = compute_two_legged_pnl(
        side=TradeSide.SHORT,
        entry_price=100.0,
        exit_price=101.5,
        quantity=10.0,
        fee_rate_bps=15.0,
        slippage_bps=0.0,
        funding_cash_flow_usdt=0.0,
    )
    assert res.exit_notional_usdt == pytest.approx(1015.0)
    assert res.gross_pnl_usdt == pytest.approx(-15.0)
    assert res.total_fees_usdt == pytest.approx(3.0225)
    assert res.net_pnl_usdt == pytest.approx(-18.0225)
    assert res.net_return_bps == pytest.approx(-180.225)


def test_fee_asymmetry_and_leg_breakdown():
    """Scenarios 5, 6, 7: Entry fee, exit fee, and Long vs Short fee asymmetry."""
    long_win = compute_two_legged_pnl(TradeSide.LONG, 100.0, 101.5, 10.0, fee_rate_bps=15.0, slippage_bps=0.0)
    long_loss = compute_two_legged_pnl(TradeSide.LONG, 100.0, 98.5, 10.0, fee_rate_bps=15.0, slippage_bps=0.0)

    # Entry fees are identical ($1.50), exit fees scale with N_exit ($1.5225 vs $1.4775)
    assert long_win.entry_fee_usdt == long_loss.entry_fee_usdt == pytest.approx(1.50)
    assert long_win.exit_fee_usdt - long_loss.exit_fee_usdt == pytest.approx(0.0450)
    assert long_win.fee_drag_bps == pytest.approx(30.225)
    assert long_loss.fee_drag_bps == pytest.approx(29.775)


def test_half_spread_slippage_and_effective_fill_prices():
    """Scenario 8: Half-spread execution cost and effective fill prices."""
    res_long = compute_two_legged_pnl(
        side=TradeSide.LONG,
        entry_price=100.0,
        exit_price=100.0,
        quantity=10.0,
        fee_rate_bps=0.0,
        slippage_bps=2.0,
    )
    assert res_long.entry_fill_price_effective == pytest.approx(100.02)
    assert res_long.exit_fill_price_effective == pytest.approx(99.98)
    assert res_long.entry_slippage_usdt == pytest.approx(0.20)
    assert res_long.exit_slippage_usdt == pytest.approx(0.20)
    assert res_long.total_slippage_usdt == pytest.approx(0.40)
    assert res_long.net_pnl_usdt == pytest.approx(-0.40)
    assert res_long.slippage_drag_bps == pytest.approx(4.0)

    res_short = compute_two_legged_pnl(
        side=TradeSide.SHORT,
        entry_price=100.0,
        exit_price=100.0,
        quantity=10.0,
        fee_rate_bps=0.0,
        slippage_bps=2.0,
    )
    assert res_short.entry_fill_price_effective == pytest.approx(99.98)
    assert res_short.exit_fill_price_effective == pytest.approx(100.02)
    assert res_short.total_slippage_usdt == pytest.approx(0.40)


def test_signed_funding_positive_negative_multiple_and_boundaries():
    """Scenarios 9, 10, 11, 12: Positive/negative funding, multiple settlements, and t_entry < t_settle <= t_exit."""
    s_ms = 8 * 3600 * 1000  # 28,800,000 ms (8h)

    # Boundary check: entry exactly AT settlement s_ms, exit AT 2 * s_ms -> only 2 * s_ms is crossed!
    cf_long_pos_rate, sets1 = calculate_funding_cash_flow(
        side=TradeSide.LONG,
        entry_notional=1000.0,
        entry_time_ms=s_ms,
        exit_time_ms=2 * s_ms,
        funding_rate_bps_per_settlement=1.0,
    )
    assert len(sets1) == 1
    assert sets1[0].timestamp_ms == 2 * s_ms
    assert sets1[0].funding_data_status == HISTORICAL_FUNDING_STATUS
    assert cf_long_pos_rate == pytest.approx(-0.10)  # Long pays positive funding

    # Short receives positive funding (CF > 0)
    cf_short_pos_rate, _ = calculate_funding_cash_flow(
        side=TradeSide.SHORT,
        entry_notional=1000.0,
        entry_time_ms=s_ms,
        exit_time_ms=2 * s_ms,
        funding_rate_bps_per_settlement=1.0,
    )
    assert cf_short_pos_rate == pytest.approx(0.10)

    # Long receives negative funding (CF > 0), Short pays negative funding (CF < 0)
    cf_long_neg_rate, _ = calculate_funding_cash_flow(
        side=TradeSide.LONG,
        entry_notional=1000.0,
        entry_time_ms=s_ms,
        exit_time_ms=2 * s_ms,
        funding_rate_bps_per_settlement=-1.5,
    )
    assert cf_long_neg_rate == pytest.approx(0.15)

    # Multiple settlements: 3 settlements crossed over 24 hours
    cf_multi, sets_multi = calculate_funding_cash_flow(
        side=TradeSide.LONG,
        entry_notional=1000.0,
        entry_time_ms=s_ms,
        exit_time_ms=4 * s_ms,
        funding_rate_bps_per_settlement=1.0,
    )
    assert len(sets_multi) == 3
    assert [s.timestamp_ms for s in sets_multi] == [2 * s_ms, 3 * s_ms, 4 * s_ms]
    assert cf_multi == pytest.approx(-0.30)

    # Exit strictly before next settlement -> 0 settlements crossed
    cf_none, sets_none = calculate_funding_cash_flow(
        side=TradeSide.LONG,
        entry_notional=1000.0,
        entry_time_ms=s_ms,
        exit_time_ms=2 * s_ms - 1,
        funding_rate_bps_per_settlement=1.0,
    )
    assert len(sets_none) == 0
    assert cf_none == 0.0


def test_partial_close_and_multi_step_lifecycle_reconciliation():
    """Scenarios 13, 14, 15, 16, 17, 20: Single partial close, multiple partial closes, open remainder, full close."""
    # Scenario 13: Single partial close (50% closed at 102.0, 50% remaining marked at 103.0)
    part = compute_partial_close(
        side=TradeSide.LONG,
        entry_price=100.0,
        close_price=102.0,
        mark_price=103.0,
        closed_quantity=5.0,
        remaining_quantity=5.0,
        fee_rate_bps=15.0,
        slippage_bps=0.0,
    )
    assert part.closed_accounting.gross_pnl_usdt == pytest.approx(10.0)
    assert part.remaining_quantity == pytest.approx(5.0)
    assert part.remaining_entry_notional_usdt == pytest.approx(500.0)
    assert part.unrealized_pnl_usdt == pytest.approx(15.0)
    assert part.unrealized_return_bps == pytest.approx(300.0)

    # Scenarios 14, 15, 17, 20: Multi-step partial close with remaining open position at dataset end
    recon_open = reconcile_position_lifecycle(
        side=TradeSide.LONG,
        initial_quantity=10.0,
        entry_price=100.0,
        partial_exits=[
            PartialExitStepInput(quantity=3.0, exit_price=101.0),
            PartialExitStepInput(quantity=4.0, exit_price=102.0),
        ],
        final_mark_price=103.0,
        fee_rate_bps=15.0,
        slippage_bps=2.0,
        leverage=2.0,
    )
    assert recon_open.quantity_conserved is True
    assert recon_open.notional_conserved is True
    assert recon_open.closed_quantity_total == pytest.approx(7.0)
    assert recon_open.remaining_quantity == pytest.approx(3.0)
    assert recon_open.open_position_snapshot is not None
    assert recon_open.open_position_snapshot.unrealized_gross_pnl_usdt == pytest.approx(9.0)  # 3 * (103 - 100)
    assert recon_open.open_position_snapshot.initial_margin_usdt == pytest.approx(150.0)  # 300 / 2
    assert recon_open.reconciliation_error_usdt < 1e-6

    # Scenario 16: Full close across 3 partial exits (remaining_quantity == 0)
    recon_full = reconcile_position_lifecycle(
        side=TradeSide.SHORT,
        initial_quantity=10.0,
        entry_price=100.0,
        partial_exits=[
            PartialExitStepInput(quantity=4.0, exit_price=99.0),
            PartialExitStepInput(quantity=3.0, exit_price=98.0),
            PartialExitStepInput(quantity=3.0, exit_price=97.0),
        ],
        fee_rate_bps=15.0,
        slippage_bps=2.0,
    )
    assert recon_full.quantity_conserved is True
    assert recon_full.notional_conserved is True
    assert recon_full.remaining_quantity == 0.0
    assert recon_full.open_position_snapshot is None
    assert recon_full.unrealized_net_pnl_usdt == 0.0
    # Gross PnL = 4*(1) + 3*(2) + 3*(3) = 4 + 6 + 9 = 19.0
    assert recon_full.total_realized_gross_pnl_usdt == pytest.approx(19.0)


def test_zero_quantity_and_invalid_price_validations():
    """Scenarios 18 & 19: Zero quantity, negative/NaN/Inf prices, and overfill rejection."""
    with pytest.raises(ValueError, match="entry_price"):
        compute_two_legged_pnl(TradeSide.LONG, 0.0, 100.0, 10.0)

    with pytest.raises(ValueError, match="exit_price"):
        compute_two_legged_pnl(TradeSide.LONG, 100.0, -5.0, 10.0)

    with pytest.raises(ValueError, match="entry_price"):
        compute_two_legged_pnl(TradeSide.LONG, float("nan"), 100.0, 10.0)

    with pytest.raises(ValueError, match="quantity"):
        compute_two_legged_pnl(TradeSide.LONG, 100.0, 101.0, 0.0)

    with pytest.raises(ValueError, match="open_quantity"):
        compute_open_position_accounting(TradeSide.LONG, 100.0, 101.0, 0.0)

    with pytest.raises(ValueError, match="exceeds initial_quantity"):
        reconcile_position_lifecycle(
            side=TradeSide.LONG,
            initial_quantity=5.0,
            entry_price=100.0,
            partial_exits=[PartialExitStepInput(quantity=6.0, exit_price=101.0)],
        )
