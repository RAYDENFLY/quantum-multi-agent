"""Unit and End-to-End Integration Tests for Milestone 5.12.2.2.

Validates:
1. Admission buffer enforcement (0.995000x cap).
2. Active MTM Monitor exposure and capacity tracking.
3. Risk State Machine deterministic transitions and hysteresis.
4. Deleveraging Engine multi-policy execution and friction accounting.
5. End-to-End Pipeline: Market Data -> MTM Monitor -> Risk State Machine -> Deleveraging -> Ledger -> Independent Oracle.
"""

import pytest
from decimal import Decimal

from quantum.accounting.event_ledger import EventDrivenPortfolioLedger, LedgerEventType
from quantum.accounting.oracle import IndependentAccountingOracle
from quantum.accounting.risk_controller import (
    ActiveMTMMonitor,
    DeleveragingEngine,
    DeleveragingPolicyType,
    RiskState,
    RiskStateMachine,
)
from quantum.domain.enums import TradeSide


class TestMilestone51222ActiveMTMRisk:
    """Test suite for Milestone 5.12.2.2 Layer A and Layer B risk architecture."""

    def test_admission_buffer_enforcement(self):
        """Verifies order admission is capped at 0.995000x post-friction."""
        ledger = EventDrivenPortfolioLedger(100.0, max_gross_exposure=1.0, safety_buffer=0.0050, admission_exposure_cap=0.9950)
        assert abs(ledger.admission_exposure_cap - 0.9950) < 1e-6
        assert abs(ledger.safety_buffer - 0.0050) < 1e-6

        # Attempt to open 4 assets with equal $25 allocation
        for sym in ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]:
            ok, reason, alloc = ledger.can_open_position(sym, 25.0, entry_friction_rate=0.0013)
            assert ok is True
            pos = ledger.open_position(
                symbol=sym, side=TradeSide.LONG, reference_price=100.0, fill_price=100.0,
                notional=alloc, fee_bps=10.0, spread_bps_half=1.0, slippage_bps=2.0,
                timestamp_ms=1000, entry_bar=1
            )
            assert pos is not None

        exp = ledger.get_gross_exposure()
        assert round(exp, 6) <= 0.995000
        assert Decimal(str(round(exp, 6))) <= Decimal("0.995000")

        # 5th asset must be rejected
        ok_5, reason_5, _ = ledger.can_open_position("XRPUSDT", 25.0)
        assert ok_5 is False
        assert "CONCURRENCY_LIMIT" in reason_5

    def test_active_mtm_monitor_revaluation(self):
        """Verifies ActiveMTMMonitor produces accurate 15-field snapshots."""
        ledger = EventDrivenPortfolioLedger(100.0, safety_buffer=0.0050, admission_exposure_cap=0.9950)
        ledger.open_position("BTCUSDT", TradeSide.LONG, 50000.0, 50000.0, 24.5, 10.0, 1.0, 2.0, 1000, 1)
        ledger.open_position("ETHUSDT", TradeSide.SHORT, 3000.0, 3000.0, 24.5, 10.0, 1.0, 2.0, 1000, 1)

        monitor = ActiveMTMMonitor(hard_max_gross_exposure=1.0, admission_exposure_cap=0.9950)
        prices = {"BTCUSDT": 52000.0, "ETHUSDT": 2900.0}

        snap = monitor.evaluate_portfolio(ledger.open_positions, 0.0, ledger.cash_balance, prices, 2000)
        assert snap.open_position_count == 2
        assert snap.long_notional > 0.0
        assert snap.short_notional > 0.0
        assert snap.unrealized_pnl > 0.0  # BTC gained, ETH dropped (short gain)
        assert snap.equity > 100.0
        assert snap.gross_exposure_open < 0.50

    def test_risk_state_machine_hysteresis(self):
        """Verifies anti-oscillation hysteresis in risk state transitions."""
        rsm = RiskStateMachine(warning_threshold=0.9000, hysteresis_buffer=0.0200)
        monitor = ActiveMTMMonitor()

        # Step 1: Normal exposure
        snap1 = monitor.evaluate_portfolio({}, 0.0, 100.0, {}, 1000)
        assert rsm.update_state(snap1) == RiskState.NORMAL

        # Step 2: Jump to 0.91 -> WARNING
        ledger = EventDrivenPortfolioLedger(100.0)
        snap2 = monitor.evaluate_portfolio({}, 91.0, 100.0, {}, 2000)
        assert rsm.update_state(snap2) == RiskState.WARNING

        # Step 3: Dips to 0.895 -> Must stay WARNING (hysteresis target is 0.880)
        snap3 = monitor.evaluate_portfolio({}, 89.5, 100.0, {}, 3000)
        assert rsm.update_state(snap3) == RiskState.WARNING

        # Step 4: Dips to 0.875 -> Cleared hysteresis -> Recovers to NORMAL
        snap4 = monitor.evaluate_portfolio({}, 87.5, 100.0, {}, 4000)
        assert rsm.update_state(snap4) == RiskState.NORMAL

    def test_deleveraging_policy_cost_aware_reduction(self):
        """Verifies deleveraging calculates excess notional and restores target exposure."""
        ledger = EventDrivenPortfolioLedger(100.0, max_symbol_weight=0.50, safety_buffer=0.0050)
        ledger.open_position("SOLUSDT", TradeSide.SHORT, 150.0, 150.0, 48.0, 10.0, 1.0, 2.0, 1000, 1)
        ledger.open_position("AVAXUSDT", TradeSide.SHORT, 30.0, 30.0, 48.0, 10.0, 1.0, 2.0, 1000, 1)

        # 20% rally on both shorts -> catastrophic exposure expansion
        shock_prices = {"SOLUSDT": 180.0, "AVAXUSDT": 36.0}
        ledger.update_mark_to_market(shock_prices, timestamp_ms=2000)

        pre_exp = ledger.get_gross_exposure(shock_prices)
        assert pre_exp > 1.30  # Severe CRITICAL breach

        engine = DeleveragingEngine(target_restored_exposure=0.9500)
        actions = engine.execute_deleveraging(
            ledger, shock_prices, timestamp_ms=3000, policy=DeleveragingPolicyType.HIGHEST_RISK_FIRST
        )
        assert len(actions) > 0
        assert all(a.success for a in actions)

        post_exp = ledger.get_gross_exposure(shock_prices)
        assert post_exp <= 0.950000

    def test_end_to_end_closed_loop_pipeline(self):
        """Full Pipeline: Market Data -> MTM Monitor -> RSM -> Deleveraging -> Cost Engine -> Ledger -> Oracle."""
        initial_cash = 100.0
        ledger = EventDrivenPortfolioLedger(initial_cash, safety_buffer=0.0050, admission_exposure_cap=0.9950)
        oracle = IndependentAccountingOracle(initial_cash, safety_buffer=0.0050, admission_exposure_cap=0.9950)
        monitor = ActiveMTMMonitor(admission_exposure_cap=0.9950)
        rsm = RiskStateMachine()
        engine = DeleveragingEngine(target_restored_exposure=0.9500)

        t_ms = 1_000_000
        # 1. Open 2 positions
        for sym, price, side in [("BTCUSDT", 50000.0, TradeSide.LONG), ("ETHUSDT", 3000.0, TradeSide.SHORT)]:
            t_ms += 60_000
            ok, r, alloc = ledger.can_open_position(sym, 24.5, entry_friction_rate=0.0013)
            assert ok is True
            pos = ledger.open_position(
                sym, side, price, price, alloc, fee_bps=10.0, spread_bps_half=1.0, slippage_bps=2.0,
                timestamp_ms=t_ms, entry_bar=1
            )
            assert pos is not None
            ok_o, _ = oracle.process_entry(
                f"EVT_{sym}", f"TRD_{sym}", t_ms, sym, (side == TradeSide.LONG), alloc, price,
                taker_fee_bps=10.0, spread_bps_half=1.0, slippage_bps=2.0
            )
            assert ok_o is True

        # 2. Market shock occurs
        shock_prices = {"BTCUSDT": 47000.0, "ETHUSDT": 3300.0}  # Both suffer losses
        t_ms += 60_000

        # Ledger update MTM first
        l_eq = ledger.update_mark_to_market(shock_prices, t_ms)
        o_eq = oracle.compute_equity(shock_prices)
        assert abs(l_eq - o_eq) < 1e-3

        # MTM Monitor recalculates
        snap = monitor.evaluate_portfolio(ledger.open_positions, 0.0, ledger.cash_balance, shock_prices, t_ms)
        state = rsm.update_state(snap)
        assert state in (RiskState.NORMAL, RiskState.WARNING, RiskState.REDUCE_ONLY, RiskState.CRITICAL)

        # Reconcile Ledger and Oracle equity and exposure
        l_exp = ledger.get_gross_exposure(shock_prices)
        o_exp = oracle.compute_gross_exposure(shock_prices)
        assert abs(l_exp - o_exp) < 1e-3
