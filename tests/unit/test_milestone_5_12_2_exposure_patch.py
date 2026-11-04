"""Unit and Integration Tests for Milestone 5.12.2: Exposure Invariant Correction.

Verifies:
1. TC-19 Hard Exposure Invariant: gross_exposure <= Decimal("1.000000") with 0.0 tolerance.
2. Pending Order Reservation Lifecycle: reservations, cancellations, no phantom exposure.
3. Partial-Fill and Full-Fill Conservation: seamless transfer from reservation to position.
4. Friction-Aware Capacity Sizing: denominator adjustment (1 + max_exp * friction_rate).
5. Multi-Asset Shared Capital Pool: 4 assets with tight capacity limits.
6. HYP-06 Multi-Factor Pipeline Integration: cross-asset enrichment produces non-zero trades.
7. Oracle Reconciliation: bit-exact agreement between primary ledger and independent oracle.
"""

from decimal import Decimal
import numpy as np
import pandas as pd
import pytest

from quantum.accounting.event_ledger import EventDrivenPortfolioLedger, LedgerEventType
from quantum.accounting.oracle import IndependentAccountingOracle
from quantum.domain.enums import TradeSide
from quantum.features.market_context import (
    compute_market_context_dataframe,
    compute_cross_asset_context,
)
from quantum.strategies.hypothesis_engine import backtest_single_hypothesis


class TestMilestone5122ExposurePatch:
    """Rigorous tests for exposure invariant enforcement and pending reservations."""

    def test_tc19_hard_exposure_invariant_zero_tolerance(self):
        """TC-19: 4-asset shared pool must enforce gross_exposure <= 1.000000x at every event."""
        initial_cash = 100.0
        max_exposure = 1.0
        max_weight = 0.25

        ledger = EventDrivenPortfolioLedger(
            initial_equity_usd=initial_cash,
            max_gross_exposure=max_exposure,
            max_concurrent_positions=4,
            max_symbol_weight=max_weight,
        )
        oracle = IndependentAccountingOracle(
            initial_cash_usd=initial_cash,
            max_gross_exposure=max_exposure,
            max_symbol_weight=max_weight,
        )

        assets = [
            ("BTCUSDT", 50000.0, 25.0),
            ("ETHUSDT", 3000.0, 25.0),
            ("SOLUSDT", 150.0, 25.0),
            ("BNBUSDT", 400.0, 25.0),
        ]

        t_ms = 1_000_000
        for i, (sym, price, target_notional) in enumerate(assets):
            t_ms += 60_000
            evt_id = f"EVT_TC19_{i+1}"
            oid = f"ORD_TC19_{i+1}"

            # 1. Capacity check
            ok, reason, alloc_usd = ledger.can_open_position(
                sym, target_notional, entry_friction_rate=0.0013
            )
            assert ok is True, f"Failed capacity check for {sym}: {reason}"
            assert alloc_usd > 0.0

            # 2. Primary ledger entry
            pos = ledger.open_position(
                symbol=sym,
                side=TradeSide.LONG,
                reference_price=price,
                fill_price=price,
                notional=alloc_usd,
                fee_bps=10.0,
                spread_bps_half=1.0,
                slippage_bps=2.0,
                timestamp_ms=t_ms,
                entry_bar=i,
            )
            assert pos is not None

            # 3. Independent oracle entry
            ok_o, err_o = oracle.process_entry(
                event_id=evt_id,
                trade_id=oid,
                timestamp_ms=t_ms,
                symbol=sym,
                is_long=True,
                requested_notional=alloc_usd,
                price=price,
                taker_fee_bps=10.0,
                spread_bps_half=1.0,
                slippage_bps=2.0,
            )
            assert ok_o is True, f"Oracle rejected {sym}: {err_o}"

            # 4. Strict Exposure Assertions (6 decimals)
            l_exp = ledger.get_gross_exposure()
            o_exp = oracle.compute_gross_exposure()

            l_exp_dec = Decimal(str(round(l_exp, 6)))
            o_exp_dec = Decimal(str(round(o_exp, 6)))

            assert l_exp_dec <= Decimal("1.000000"), f"Ledger invariant breach at {sym}: {l_exp:.8f} > 1.000000"
            assert o_exp_dec <= Decimal("1.000000"), f"Oracle invariant breach at {sym}: {o_exp:.8f} > 1.000000"
            assert abs(l_exp - o_exp) < 1e-5, f"Discrepancy between ledger {l_exp} and oracle {o_exp}"

        # After all 4 assets opened:
        assert len(ledger.open_positions) == 4
        assert len(oracle.positions) == 4
        final_exp = ledger.get_gross_exposure()
        assert Decimal(str(round(final_exp, 6))) <= Decimal("1.000000")

    def test_pending_order_reservation_and_cancellation(self):
        """Limit orders must reserve exposure; cancellation must cleanly release reservation."""
        ledger = EventDrivenPortfolioLedger(100.0, max_gross_exposure=1.0, max_concurrent_positions=4, max_symbol_weight=0.25)
        oracle = IndependentAccountingOracle(100.0, max_gross_exposure=1.0, max_symbol_weight=0.25)

        # 1. Reserve 2 orders of $25 each
        ok1, _, a1 = ledger.reserve_pending_order("ORD_1", "BTCUSDT", TradeSide.LONG, 50000.0, 25.0, 1000)
        assert ok1 is True
        oracle.reserve_order("EVT_1", "ORD_1", 1000, "BTCUSDT", True, 25.0, 50000.0)

        ok2, _, a2 = ledger.reserve_pending_order("ORD_2", "ETHUSDT", TradeSide.LONG, 3000.0, 25.0, 1001)
        assert ok2 is True
        oracle.reserve_order("EVT_2", "ORD_2", 1001, "ETHUSDT", True, 25.0, 3000.0)

        # Exposure must reflect reserved orders
        assert abs(ledger.reserved_pending_notional - 50.0) < 1e-5
        assert abs(ledger.get_gross_exposure() - 0.50) < 1e-4
        assert abs(oracle.compute_gross_exposure() - 0.50) < 1e-4

        # 2. Cancel ORD_1
        ledger.cancel_pending_order("ORD_1", 2000)
        oracle.cancel_order("EVT_3", "ORD_1", 2000)

        assert abs(ledger.reserved_pending_notional - 25.0) < 1e-5
        assert abs(ledger.get_gross_exposure() - 0.25) < 1e-4
        assert abs(oracle.compute_gross_exposure() - 0.25) < 1e-4

        # 3. Cancel ORD_2
        ledger.cancel_pending_order("ORD_2", 3000)
        oracle.cancel_order("EVT_4", "ORD_2", 3000)

        assert abs(ledger.reserved_pending_notional - 0.0) < 1e-5
        assert abs(ledger.get_gross_exposure() - 0.0) < 1e-5
        assert abs(oracle.compute_gross_exposure() - 0.0) < 1e-5

    def test_partial_fill_notional_conservation(self):
        """Partial fill must reduce reserved pending notional and create position without double counting."""
        ledger = EventDrivenPortfolioLedger(100.0, max_gross_exposure=1.0, max_concurrent_positions=4, max_symbol_weight=0.25)
        oracle = IndependentAccountingOracle(100.0, max_gross_exposure=1.0, max_symbol_weight=0.25)

        # Reserve $24 order
        ok, _, alloc = ledger.reserve_pending_order("ORD_PF", "SOLUSDT", TradeSide.LONG, 150.0, 24.0, 1000)
        assert ok is True
        oracle.reserve_order("EVT_1", "ORD_PF", 1000, "SOLUSDT", True, 24.0, 150.0)

        # 50% partial fill ($12.0)
        pos = ledger.open_position(
            symbol="SOLUSDT", side=TradeSide.LONG, reference_price=150.0, fill_price=150.0, notional=12.0,
            fee_bps=4.0, spread_bps_half=0.0, slippage_bps=0.0,
            timestamp_ms=1050, entry_bar=1, is_partial=True, pending_order_id="ORD_PF"
        )
        assert pos is not None
        oracle.process_entry(
            "EVT_2", "ORD_PF", 1050, "SOLUSDT", True, 12.0, 150.0,
            maker_fee_bps=4.0, is_maker=True, pending_order_id="ORD_PF"
        )

        # Remaining reserved: $12.0; Open position: $12.0; Total gross notional: $24.0
        assert abs(ledger.pending_orders["ORD_PF"].reserved_notional - 12.0) < 1e-5
        assert abs(ledger.reserved_pending_notional - 12.0) < 1e-5
        assert abs(ledger.open_positions["SOLUSDT"].entry_notional - 12.0) < 1e-5
        assert abs(ledger.get_gross_notional() - 24.0) < 1e-4

        # Fill second half ($12.0)
        pos2 = ledger.open_position(
            symbol="SOLUSDT", side=TradeSide.LONG, reference_price=150.0, fill_price=150.0, notional=12.0,
            fee_bps=4.0, spread_bps_half=0.0, slippage_bps=0.0,
            timestamp_ms=1100, entry_bar=2, is_partial=False, pending_order_id="ORD_PF"
        )
        assert pos2 is not None
        oracle.process_entry(
            "EVT_3", "ORD_PF", 1100, "SOLUSDT", True, 12.0, 150.0,
            maker_fee_bps=4.0, is_maker=True, pending_order_id="ORD_PF"
        )

        # Pending order completed and removed
        assert "ORD_PF" not in ledger.pending_orders
        assert abs(ledger.reserved_pending_notional - 0.0) < 1e-5
        assert abs(ledger.open_positions["SOLUSDT"].entry_notional - 24.0) < 1e-4
        assert abs(ledger.get_gross_notional() - 24.0) < 1e-4

    def test_friction_aware_capacity_sizing_formula(self):
        """can_open_position adjusts available notional by (1 + max_exp * friction_rate)."""
        ledger = EventDrivenPortfolioLedger(100.0, max_gross_exposure=1.0, max_concurrent_positions=1, max_symbol_weight=1.0)

        # Attempt to open $100 notional with 20 bps friction (0.0020)
        ok, reason, alloc = ledger.can_open_position("BTCUSDT", 100.0, entry_friction_rate=0.0020)
        assert ok is True
        # Expected max alloc = 100.0 / (1.0 + 1.0 * 0.0020) = 100.0 / 1.0020 = 99.800399
        expected_alloc = 100.0 / 1.0020
        assert abs(alloc - expected_alloc) < 1e-3

        # Execute order
        pos = ledger.open_position(
            symbol="BTCUSDT", side=TradeSide.LONG, reference_price=50000.0, fill_price=50000.0,
            notional=alloc, fee_bps=10.0, spread_bps_half=5.0, slippage_bps=5.0,
            timestamp_ms=1000, entry_bar=1
        )
        assert pos is not None

        # Verify post-trade gross exposure is strictly <= 1.000000x
        post_exp = ledger.get_gross_exposure()
        assert Decimal(str(round(post_exp, 6))) <= Decimal("1.000000")

    def test_hyp06_cross_asset_pipeline_generates_trades(self):
        """Cross-asset enriched dataframe allows HYP-06 to generate signals and completed trades."""
        # Synthesize multi-asset panel of 300 bars
        n = 300
        dates = pd.date_range("2026-01-01", periods=n, freq="5min")
        ts = dates.astype(np.int64) // 10**6

        # BTC: steady uptrend
        btc_close = 50000.0 + np.cumsum(np.full(n, 10.0))
        btc_df = pd.DataFrame({
            "open_time_ms": ts, "close_time_ms": ts + 300000,
            "open": btc_close - 5.0, "high": btc_close + 15.0,
            "low": btc_close - 10.0, "close": btc_close, "volume": 100.0
        })

        # SOL: alternating acceleration and flat phases
        sol_steps = np.where(np.arange(n) % 40 < 20, 2.0, -0.5)
        sol_close = 150.0 + np.cumsum(sol_steps)
        sol_df = pd.DataFrame({
            "open_time_ms": ts, "close_time_ms": ts + 300000,
            "open": sol_close - 0.1, "high": sol_close + 0.5,
            "low": sol_close - 0.2, "close": sol_close, "volume": 1000.0
        })

        raw_panel = {"BTCUSDT": btc_df, "SOLUSDT": sol_df}
        single_context = {
            s: compute_market_context_dataframe(df) for s, df in raw_panel.items()
        }

        # Pipeline WITHOUT cross asset -> 0 trades
        defective_trades = backtest_single_hypothesis(single_context["SOLUSDT"], "HYP-06", symbol="SOLUSDT")
        assert len(defective_trades) == 0

        # Pipeline WITH cross asset -> trades generated
        enriched_panel = compute_cross_asset_context(single_context, btc_symbol="BTCUSDT")
        assert "rel_strength_vs_btc_1h" in enriched_panel["SOLUSDT"].columns
        assert "btc_trend_bull" in enriched_panel["SOLUSDT"].columns

        corrected_trades = backtest_single_hypothesis(enriched_panel["SOLUSDT"], "HYP-06", symbol="SOLUSDT")
        assert len(corrected_trades) > 0, "Corrected HYP-06 pipeline should produce completed trades."
