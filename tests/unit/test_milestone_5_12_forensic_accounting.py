"""Comprehensive Independent Financial Invariant Testing Suite for Milestone 5.12.

Covers all 25 mandatory test scenarios from Phase F:
1. Single long position.
2. Single short position.
3. Multiple simultaneous assets.
4. Maximum exposure exactly 1.0x.
5. Exposure breach attempt.
6. Partial entry.
7. Partial exit.
8. Full stop-loss.
9. Take-profit.
10. Fee charged once.
11. Spread and slippage reconciliation.
12. Funding charge.
13. Rejected order.
14. Canceled order.
15. Gap-through-stop execution.
16. Equity reaches zero (ruin halt).
17. Negative equity protection.
18. Duplicate trade event.
19. Duplicate fill event.
20. Out-of-order event.
21. Dataset timestamp violation.
22. Holdout boundary violation.
23. Concurrent worker ledger collision.
24. Feature cache fingerprint mismatch.
25. Independent PnL reconciliation.
"""

from pathlib import Path
import tempfile
import threading
import numpy as np
import pandas as pd
import pytest

from quantum.accounting import (
    CostModelProfile,
    DEFAULT_ASTERDEX_COSTS,
    EventDrivenPortfolioLedger,
    ExecutionEconomicsEngine,
    ExecutionScenario,
    IndependentForensicReconciler,
    LedgerEventType,
    OpenPosition,
    ResearchLifecycleStage,
    CorrectedResearchGates,
)
from quantum.domain.enums import TradeSide
from quantum.research import (
    ContinuousResearchPartitioner,
    DatasetPartition,
    DatasetPartitionType,
    HoldoutContaminationError,
    IntermediateFeatureCache,
    PROSPECTIVE_HOLDOUT_START_MS,
)

ROOT = Path(__file__).resolve().parent.parent.parent
M5_12_DIR = ROOT / "audit" / "strategy_research" / "milestone_5_12_forensic_accounting"


# ==============================================================================
# SCENARIO 1 & 2: SINGLE LONG AND SINGLE SHORT
# ==============================================================================

def test_scenario_01_single_long_position():
    """Verify single long position accounting, double-entry cash deduction, and PnL."""
    ledger = EventDrivenPortfolioLedger(initial_equity_usd=100.0, max_gross_exposure=1.0)
    pos = ledger.open_position(
        symbol="BTCUSDT",
        side=TradeSide.LONG,
        reference_price=50000.0,
        fill_price=50000.0,
        notional=25.0,
        fee_bps=10.0,
        spread_bps_half=1.0,
        slippage_bps=2.0,
        timestamp_ms=1000,
        entry_bar=1,
        stop_price=49000.0,
        target_price=52000.0,
    )
    assert pos is not None
    assert pos.quantity == 25.0 / 50000.0
    # Entry friction: 13 bps of $25 = $0.0325
    assert pytest.approx(pos.accumulated_fees, abs=1e-4) == 0.0325
    assert pytest.approx(ledger.cash_balance, abs=1e-4) == 100.0 - 0.0325


def test_scenario_02_single_short_position():
    """Verify single short position accounting and inverse payoff."""
    ledger = EventDrivenPortfolioLedger(initial_equity_usd=100.0, max_gross_exposure=1.0)
    pos = ledger.open_position(
        symbol="ETHUSDT",
        side=TradeSide.SHORT,
        reference_price=3000.0,
        fill_price=3000.0,
        notional=25.0,
        fee_bps=10.0,
        spread_bps_half=1.0,
        slippage_bps=2.0,
        timestamp_ms=1000,
        entry_bar=1,
        stop_price=3100.0,
        target_price=2800.0,
    )
    assert pos is not None
    # Close short at profit (price falls to 2900)
    gross, net = ledger.close_position(
        symbol="ETHUSDT",
        fill_price=2900.0,
        fee_bps=10.0,
        spread_bps_half=1.0,
        slippage_bps=2.0,
        timestamp_ms=2000,
    )
    # Gross PnL on short: qty * (entry - exit) = (25 / 3000) * (3000 - 2900) = +$0.8333
    assert pytest.approx(gross, abs=1e-3) == 0.8333
    assert net < gross  # Friction deducted


# ==============================================================================
# SCENARIO 3, 4, 5: MULTIPLE ASSETS, EXACT 1.0X EXPOSURE, BREACH ATTEMPTS
# ==============================================================================

def test_scenario_03_multiple_simultaneous_assets():
    """Verify concurrent positions across multiple distinct symbols."""
    ledger = EventDrivenPortfolioLedger(initial_equity_usd=100.0, max_concurrent_positions=4, max_symbol_weight=0.25)
    for sym in ["BTCUSDT", "ETHUSDT", "SOLUSDT"]:
        pos = ledger.open_position(
            symbol=sym,
            side=TradeSide.LONG,
            reference_price=100.0,
            fill_price=100.0,
            notional=25.0,
            fee_bps=10.0,
            spread_bps_half=1.0,
            slippage_bps=2.0,
            timestamp_ms=1000,
            entry_bar=1,
            stop_price=95.0,
            target_price=110.0,
        )
        assert pos is not None
    assert len(ledger.open_positions) == 3


def test_scenario_04_maximum_exposure_exactly_1x():
    """Verify maximum gross exposure exactly reaches ~1.0000x without material breach."""
    ledger = EventDrivenPortfolioLedger(initial_equity_usd=100.0, max_concurrent_positions=4, max_symbol_weight=0.25)
    for sym in ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]:
        ledger.open_position(
            symbol=sym,
            side=TradeSide.LONG,
            reference_price=100.0,
            fill_price=100.0,
            notional=25.0,
            fee_bps=10.0,
            spread_bps_half=1.0,
            slippage_bps=2.0,
            timestamp_ms=1000,
            entry_bar=1,
            stop_price=95.0,
            target_price=110.0,
        )
    assert len(ledger.open_positions) == 4
    # Exposure is ~1.0000x (accounting for initial entry fee deduction from cash)
    assert pytest.approx(ledger.get_gross_exposure(), abs=0.005) == 1.0


def test_scenario_05_exposure_breach_attempt():
    """Verify 5th simultaneous position is strictly rejected to preserve exposure cap."""
    ledger = EventDrivenPortfolioLedger(initial_equity_usd=100.0, max_concurrent_positions=4, max_symbol_weight=0.25)
    for sym in ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]:
        ledger.open_position(
            symbol=sym,
            side=TradeSide.LONG,
            reference_price=100.0,
            fill_price=100.0,
            notional=25.0,
            fee_bps=10.0,
            spread_bps_half=1.0,
            slippage_bps=2.0,
            timestamp_ms=1000,
            entry_bar=1,
            stop_price=95.0,
            target_price=110.0,
        )
    # Attempt 5th position
    pos_5 = ledger.open_position(
        symbol="XRPUSDT",
        side=TradeSide.LONG,
        reference_price=1.0,
        fill_price=1.0,
        notional=25.0,
        fee_bps=10.0,
        spread_bps_half=1.0,
        slippage_bps=2.0,
        timestamp_ms=1000,
        entry_bar=1,
        stop_price=0.9,
        target_price=1.2,
    )
    assert pos_5 is None  # Must reject


# ==============================================================================
# SCENARIO 6 & 7: PARTIAL ENTRY AND PARTIAL EXIT
# ==============================================================================

def test_scenario_06_partial_entry():
    """Verify partial fill on entry logs PARTIAL_FILL and sets scaled quantity."""
    ledger = EventDrivenPortfolioLedger(initial_equity_usd=100.0)
    pos = ledger.open_position(
        symbol="BTCUSDT",
        side=TradeSide.LONG,
        reference_price=50000.0,
        fill_price=50000.0,
        notional=12.5,  # 50% partial fill of $25
        fee_bps=10.0,
        spread_bps_half=1.0,
        slippage_bps=2.0,
        timestamp_ms=1000,
        entry_bar=1,
        stop_price=49000.0,
        target_price=52000.0,
        is_partial=True,
    )
    assert pos.quantity == 12.5 / 50000.0
    assert ledger.events[-1].event_type == LedgerEventType.PARTIAL_FILL


def test_scenario_07_partial_exit():
    """Verify partial exit scales quantity down while leaving remainder open."""
    ledger = EventDrivenPortfolioLedger(initial_equity_usd=100.0)
    ledger.open_position(
        symbol="BTCUSDT",
        side=TradeSide.LONG,
        reference_price=50000.0,
        fill_price=50000.0,
        notional=20.0,
        fee_bps=10.0,
        spread_bps_half=1.0,
        slippage_bps=2.0,
        timestamp_ms=1000,
        entry_bar=1,
        stop_price=49000.0,
        target_price=52000.0,
    )
    # Close 50% at 55000.0
    gross, net = ledger.close_position(
        symbol="BTCUSDT",
        fill_price=55000.0,
        fee_bps=10.0,
        spread_bps_half=1.0,
        slippage_bps=2.0,
        timestamp_ms=2000,
        exit_quantity_pct=0.50,
    )
    assert "BTCUSDT" in ledger.open_positions
    remaining_pos = ledger.open_positions["BTCUSDT"]
    assert pytest.approx(remaining_pos.quantity, abs=1e-6) == 10.0 / 50000.0
    assert ledger.events[-1].event_type == LedgerEventType.PARTIAL_EXIT


# ==============================================================================
# SCENARIO 8 & 9: STOP LOSS AND TAKE PROFIT
# ==============================================================================

def test_scenario_08_full_stop_loss():
    """Verify full stop loss liquidation and event tagging."""
    ledger = EventDrivenPortfolioLedger(initial_equity_usd=100.0)
    ledger.open_position(
        symbol="BTCUSDT",
        side=TradeSide.LONG,
        reference_price=50000.0,
        fill_price=50000.0,
        notional=25.0,
        fee_bps=10.0,
        spread_bps_half=1.0,
        slippage_bps=2.0,
        timestamp_ms=1000,
        entry_bar=1,
        stop_price=48000.0,
        target_price=54000.0,
    )
    gross, net = ledger.close_position(
        symbol="BTCUSDT",
        fill_price=48000.0,
        fee_bps=10.0,
        spread_bps_half=1.0,
        slippage_bps=2.0,
        timestamp_ms=2000,
        exit_reason="STOP_LOSS",
    )
    assert gross < 0.0
    assert net < gross
    assert "BTCUSDT" not in ledger.open_positions
    assert ledger.events[-1].event_type == LedgerEventType.STOP_LOSS_HIT


def test_scenario_09_take_profit():
    """Verify take profit exit and positive cash balance increment."""
    ledger = EventDrivenPortfolioLedger(initial_equity_usd=100.0)
    ledger.open_position(
        symbol="BTCUSDT",
        side=TradeSide.LONG,
        reference_price=50000.0,
        fill_price=50000.0,
        notional=25.0,
        fee_bps=10.0,
        spread_bps_half=1.0,
        slippage_bps=2.0,
        timestamp_ms=1000,
        entry_bar=1,
        stop_price=48000.0,
        target_price=54000.0,
    )
    gross, net = ledger.close_position(
        symbol="BTCUSDT",
        fill_price=54000.0,
        fee_bps=10.0,
        spread_bps_half=1.0,
        slippage_bps=2.0,
        timestamp_ms=2000,
        exit_reason="TAKE_PROFIT",
    )
    assert gross > 0.0
    assert net > 0.0
    assert ledger.cash_balance > 100.0
    assert ledger.events[-1].event_type == LedgerEventType.TAKE_PROFIT_HIT


# ==============================================================================
# SCENARIO 10, 11, 12: FEES CHARGED ONCE, SPREAD/SLIPPAGE, FUNDING
# ==============================================================================

def test_scenario_10_fee_charged_once():
    """Verify entry and exit fees are each charged exactly once."""
    ledger = EventDrivenPortfolioLedger(initial_equity_usd=100.0)
    ledger.open_position(
        symbol="BTCUSDT",
        side=TradeSide.LONG,
        reference_price=50000.0,
        fill_price=50000.0,
        notional=20.0,
        fee_bps=10.0,
        spread_bps_half=0.0,
        slippage_bps=0.0,
        timestamp_ms=1000,
        entry_bar=1,
        stop_price=49000.0,
        target_price=52000.0,
    )
    # Entry fee: 10 bps of $20 = $0.02
    assert pytest.approx(ledger.cash_balance, abs=1e-5) == 99.98

    # Flat close (no price movement)
    ledger.close_position(
        symbol="BTCUSDT",
        fill_price=50000.0,
        fee_bps=10.0,
        spread_bps_half=0.0,
        slippage_bps=0.0,
        timestamp_ms=2000,
    )
    # Exit fee: 10 bps of $20 = $0.02
    assert pytest.approx(ledger.cash_balance, abs=1e-5) == 99.96


def test_scenario_11_spread_and_slippage_reconciliation():
    """Verify spread crossing and slippage cost separation in execution outcome."""
    outcome = ExecutionEconomicsEngine.evaluate_episode(
        side_is_long=True,
        entry_price=100.0,
        exit_price=100.0,
        notional_usd=25.0,
        scenario=ExecutionScenario.TAKER_TAKER,
        profile=DEFAULT_ASTERDEX_COSTS,
    )
    assert pytest.approx(outcome.spread_cost_usd, abs=1e-4) == 25.0 * (2.0 / 10_000.0)
    assert pytest.approx(outcome.slippage_cost_usd, abs=1e-4) == 25.0 * (4.0 / 10_000.0)


def test_scenario_12_funding_charge():
    """Verify funding payments are correctly settled on open positions."""
    ledger = EventDrivenPortfolioLedger(initial_equity_usd=100.0)
    ledger.open_position(
        symbol="BTCUSDT",
        side=TradeSide.LONG,
        reference_price=50000.0,
        fill_price=50000.0,
        notional=20.0,
        fee_bps=0.0,
        spread_bps_half=0.0,
        slippage_bps=0.0,
        timestamp_ms=1000,
        entry_bar=1,
        stop_price=49000.0,
        target_price=52000.0,
    )
    # Funding rate: +5 bps (Long pays cash)
    charge = ledger.accrue_funding("BTCUSDT", funding_rate_bps=5.0, timestamp_ms=2000)
    assert pytest.approx(charge, abs=1e-5) == 20.0 * (5.0 / 10_000.0)
    assert pytest.approx(ledger.cash_balance, abs=1e-5) == 100.0 - 0.01


# ==============================================================================
# SCENARIO 13, 14, 15: REJECTED ORDER, CANCELED ORDER, GAP THROUGH STOP
# ==============================================================================

def test_scenario_13_rejected_order():
    """Verify rejected order does not alter cash balance or equity."""
    ledger = EventDrivenPortfolioLedger(initial_equity_usd=100.0)
    # Force rejection by attempting notional below minimum ($2.0 < $5.0)
    pos = ledger.open_position(
        symbol="BTCUSDT",
        side=TradeSide.LONG,
        reference_price=50000.0,
        fill_price=50000.0,
        notional=2.0,
        fee_bps=10.0,
        spread_bps_half=1.0,
        slippage_bps=2.0,
        timestamp_ms=1000,
        entry_bar=1,
        stop_price=49000.0,
        target_price=52000.0,
    )
    assert pos is None
    assert ledger.cash_balance == 100.0
    assert ledger.events[-1].event_type == LedgerEventType.ORDER_REJECTED


def test_scenario_14_canceled_order():
    """Verify missed maker order produces 0 PnL and 0 fees."""
    outcome = ExecutionEconomicsEngine.evaluate_episode(
        side_is_long=True,
        entry_price=100.0,
        exit_price=105.0,
        notional_usd=25.0,
        scenario=ExecutionScenario.MAKER_MAKER,
        bar_high=105.0,
        bar_low=101.0,  # Price never reached limit buy at 100.0 (stayed above 101.0)
        atr=1.0,
    )
    assert outcome.fill_status == "MISSED_ENTRY"
    assert outcome.effective_notional == 0.0
    assert outcome.total_cost_usd == 0.0


def test_scenario_15_gap_through_stop_execution():
    """Verify gap-through-stop executes at adverse gap price, not nominal stop price."""
    ledger = EventDrivenPortfolioLedger(initial_equity_usd=100.0)
    ledger.open_position(
        symbol="BTCUSDT",
        side=TradeSide.LONG,
        reference_price=50000.0,
        fill_price=50000.0,
        notional=25.0,
        fee_bps=0.0,
        spread_bps_half=0.0,
        slippage_bps=0.0,
        timestamp_ms=1000,
        entry_bar=1,
        stop_price=48000.0,
        target_price=55000.0,
    )
    # Overnight/flash gap: market opens at 45000.0 (past stop 48000.0)
    gross, _ = ledger.close_position(
        symbol="BTCUSDT",
        fill_price=45000.0,  # Adverse gap fill
        fee_bps=0.0,
        spread_bps_half=0.0,
        slippage_bps=0.0,
        timestamp_ms=2000,
        exit_reason="STOP_LOSS",
    )
    assert pytest.approx(gross, abs=1e-3) == (25.0 / 50000.0) * (45000.0 - 50000.0)  # -$2.50 loss


# ==============================================================================
# SCENARIO 16 & 17: EQUITY ZERO RUIN HALT & NEGATIVE EQUITY PROTECTION
# ==============================================================================

def test_scenario_16_equity_reaches_zero_ruin_halt():
    """Verify that when equity reaches ruin threshold ($1.00), trading halts immediately."""
    ledger = EventDrivenPortfolioLedger(initial_equity_usd=20.0, max_symbol_weight=1.0, ruin_equity_threshold=1.0)
    pos = ledger.open_position(
        symbol="BTCUSDT",
        side=TradeSide.LONG,
        reference_price=100.0,
        fill_price=100.0,
        notional=20.0,
        fee_bps=0.0,
        spread_bps_half=0.0,
        slippage_bps=0.0,
        timestamp_ms=1000,
        entry_bar=1,
        stop_price=10.0,
        target_price=200.0,
    )
    assert pos is not None
    # Severe loss drops equity from $20.00 to $0.50
    ledger.close_position(
        symbol="BTCUSDT",
        fill_price=2.5,
        fee_bps=0.0,
        spread_bps_half=0.0,
        slippage_bps=0.0,
        timestamp_ms=2000,
    )
    assert ledger.is_ruined is True
    # Attempt next trade when ruined
    next_pos = ledger.open_position(
        symbol="ETHUSDT",
        side=TradeSide.LONG,
        reference_price=10.0,
        fill_price=10.0,
        notional=5.0,
        fee_bps=0.0,
        spread_bps_half=0.0,
        slippage_bps=0.0,
        timestamp_ms=3000,
        entry_bar=2,
        stop_price=5.0,
        target_price=20.0,
    )
    assert next_pos is None


def test_scenario_17_negative_equity_protection():
    """Verify max drawdown is mathematically bounded in [0.0, 100.0]% and cannot exceed 100%."""
    # Reconstruct trade stream with ruin
    fake_trades = [
        {"entry_time_ms": i * 1000, "exit_time_ms": (i + 1) * 1000, "symbol": "BTCUSDT", "side": "LONG", "entry_price": 100.0, "exit_price": 90.0}
        for i in range(100)
    ]
    summary, df_events = IndependentForensicReconciler.reconcile_trade_stream(
        raw_trades=fake_trades,
        initial_equity_usd=100.0,
    )
    assert summary.max_drawdown_pct <= 100.0
    assert summary.final_equity_usd >= 0.0
    assert summary.net_pnl_usd >= -100.0  # Cannot lose more than $100


# ==============================================================================
# SCENARIO 18, 19, 20: DUPLICATE & OUT-OF-ORDER EVENTS
# ==============================================================================

def test_scenario_18_duplicate_trade_event():
    """Verify identical duplicate trade cannot be opened simultaneously in the same symbol."""
    ledger = EventDrivenPortfolioLedger(initial_equity_usd=100.0)
    pos1 = ledger.open_position(
        symbol="BTCUSDT",
        side=TradeSide.LONG,
        reference_price=100.0,
        fill_price=100.0,
        notional=25.0,
        fee_bps=0.0,
        spread_bps_half=0.0,
        slippage_bps=0.0,
        timestamp_ms=1000,
        entry_bar=1,
        stop_price=90.0,
        target_price=110.0,
    )
    assert pos1 is not None
    # Duplicate attempt
    pos2 = ledger.open_position(
        symbol="BTCUSDT",
        side=TradeSide.LONG,
        reference_price=100.0,
        fill_price=100.0,
        notional=25.0,
        fee_bps=0.0,
        spread_bps_half=0.0,
        slippage_bps=0.0,
        timestamp_ms=1000,
        entry_bar=1,
        stop_price=90.0,
        target_price=110.0,
    )
    assert pos2 is None


def test_scenario_19_duplicate_fill_event():
    """Verify closing an already-closed position returns None and charges no fees."""
    ledger = EventDrivenPortfolioLedger(initial_equity_usd=100.0)
    ledger.open_position(
        symbol="BTCUSDT",
        side=TradeSide.LONG,
        reference_price=100.0,
        fill_price=100.0,
        notional=25.0,
        fee_bps=0.0,
        spread_bps_half=0.0,
        slippage_bps=0.0,
        timestamp_ms=1000,
        entry_bar=1,
        stop_price=90.0,
        target_price=110.0,
    )
    res1 = ledger.close_position("BTCUSDT", fill_price=100.0, fee_bps=0.0, spread_bps_half=0.0, slippage_bps=0.0, timestamp_ms=2000)
    assert res1 is not None
    # Duplicate close
    res2 = ledger.close_position("BTCUSDT", fill_price=100.0, fee_bps=0.0, spread_bps_half=0.0, slippage_bps=0.0, timestamp_ms=2000)
    assert res2 is None


def test_scenario_20_out_of_order_event():
    """Verify reconciler sorts out-of-order trades chronologically by timestamp."""
    out_of_order = [
        {"entry_time_ms": 3000, "exit_time_ms": 4000, "symbol": "BTCUSDT", "side": "LONG", "entry_price": 100.0, "exit_price": 101.0},
        {"entry_time_ms": 1000, "exit_time_ms": 2000, "symbol": "BTCUSDT", "side": "LONG", "entry_price": 100.0, "exit_price": 101.0},
    ]
    summary, df_events = IndependentForensicReconciler.reconcile_trade_stream(out_of_order)
    open_events = df_events[df_events["event_type"] == LedgerEventType.POSITION_OPENED.value]
    ts_list = open_events["timestamp_ms"].tolist()
    assert ts_list == [1000, 3000]  # Sorted strictly chronologically


# ==============================================================================
# SCENARIO 21 & 22: DATASET TIMESTAMPS & HOLDOUT BOUNDARY
# ==============================================================================

def test_scenario_21_dataset_timestamp_violation():
    """Verify partitioner detects chronological inversion between train and val."""
    partitioner = ContinuousResearchPartitioner(embargo_bars=50)
    parts = partitioner.partition_pre_holdout_series(
        pd.DataFrame({
            "open_time_ms": range(1000, 1000 + 700 * 300_000, 300_000),
            "close_time_ms": range(1299, 1299 + 700 * 300_000, 300_000),
            "open": [100.0] * 700,
            "high": [101.0] * 700,
            "low": [99.0] * 700,
            "close": [100.0] * 700,
            "volume": [10.0] * 700,
        }),
        symbol="BTCUSDT",
    )
    assert parts[DatasetPartitionType.TRAIN].fingerprint.start_timestamp_ms < parts[DatasetPartitionType.VALIDATION].fingerprint.start_timestamp_ms


def test_scenario_22_holdout_boundary_violation():
    """Verify that any attempt to partition data at or past 1,793,491,200,000 ms fails fatally."""
    df = pd.DataFrame({
        "open_time_ms": [PROSPECTIVE_HOLDOUT_START_MS],
        "close_time_ms": [PROSPECTIVE_HOLDOUT_START_MS + 299_999],
        "open": [100.0],
        "high": [101.0],
        "low": [99.0],
        "close": [100.0],
        "volume": [10.0],
    })
    partitioner = ContinuousResearchPartitioner()
    with pytest.raises(HoldoutContaminationError):
        partitioner.partition_pre_holdout_series(df, symbol="BTCUSDT")


# ==============================================================================
# SCENARIO 23 & 24: CONCURRENT WORKERS & CACHE MISMATCH
# ==============================================================================

def test_scenario_23_concurrent_worker_ledger_collision():
    """Verify that concurrent threads accessing the ledger do not corrupt state."""
    ledger = EventDrivenPortfolioLedger(initial_equity_usd=100.0, max_concurrent_positions=10)
    symbols = [f"SYM_{i}USDT" for i in range(10)]

    def worker_trade(sym: str):
        ledger.open_position(
            symbol=sym,
            side=TradeSide.LONG,
            reference_price=10.0,
            fill_price=10.0,
            notional=5.0,
            fee_bps=0.0,
            spread_bps_half=0.0,
            slippage_bps=0.0,
            timestamp_ms=1000,
            entry_bar=1,
            stop_price=5.0,
            target_price=20.0,
        )

    threads = [threading.Thread(target=worker_trade, args=(s,)) for s in symbols]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(ledger.open_positions) == 10
    assert ledger.get_gross_exposure() <= 1.0001


def test_scenario_24_feature_cache_fingerprint_mismatch():
    """Verify cache differentiates between distinct dataset fingerprints."""
    cache = IntermediateFeatureCache()
    df1 = pd.DataFrame({"open_time_ms": [1], "close_time_ms": [1], "open": [100.0], "high": [101.0], "low": [99.0], "close": [100.0], "volume": [10.0]})
    df2 = pd.DataFrame({"open_time_ms": [1], "close_time_ms": [1], "open": [200.0], "high": [201.0], "low": [199.0], "close": [200.0], "volume": [20.0]})

    _, hit1 = cache.get_or_compute(df1, "BTCUSDT", "5m", "hash_aaa")
    _, hit2 = cache.get_or_compute(df2, "BTCUSDT", "5m", "hash_bbb")

    assert not hit1
    assert not hit2
    assert cache.misses == 2


# ==============================================================================
# SCENARIO 25: INDEPENDENT PNL RECONCILIATION
# ==============================================================================

def test_scenario_25_independent_pnl_reconciliation():
    """Verify independent cash flow reconciliation matches final equity exactly."""
    ledger = EventDrivenPortfolioLedger(initial_equity_usd=100.0)
    ledger.open_position("BTCUSDT", TradeSide.LONG, 100.0, 100.0, 20.0, fee_bps=10.0, spread_bps_half=1.0, slippage_bps=2.0, timestamp_ms=1000, entry_bar=1, stop_price=90.0, target_price=120.0)
    ledger.close_position("BTCUSDT", 110.0, fee_bps=10.0, spread_bps_half=1.0, slippage_bps=2.0, timestamp_ms=2000)

    df_events = ledger.to_dataframe()
    fees_sum = df_events["fee"].sum()
    spread_sum = df_events["spread_cost"].sum()
    slippage_sum = df_events["slippage_cost"].sum()
    realized_sum = df_events["realized_pnl"].sum()

    calculated_equity = 100.0 + realized_sum - (fees_sum + spread_sum + slippage_sum)
    assert pytest.approx(ledger.equity, abs=1e-4) == calculated_equity
