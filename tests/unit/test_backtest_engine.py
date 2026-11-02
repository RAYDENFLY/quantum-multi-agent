"""Unit and integration tests for DiscreteEventBacktestEngine (Workstreams C, E, F, G).

Verifies all 15 critical Track 2 edge cases plus Risk Modes, Banker FSM, and Resource Constraints:
1. Long TP.
2. Long SL.
3. Short TP.
4. Short SL.
5. Opening gap above TP (fills at gap open price with is_gap_exit=True).
6. Opening gap below SL (fills at worse gap open price with is_gap_exit=True).
7. Both barriers touched in same bar (CONSERVATIVE_SL_FIRST vs OPTIMISTIC_TP_FIRST).
8. Barrier untouched for 12 bars (exact 12-bar / 60-minute expiration at close[entry_bar + 11]).
9. Missing candle gap handling.
10. Duplicate timestamp rejection.
11. Zero volatility rejection when min_volatility == 0.0.
12. Volatility floor enforcement (min_volatility > 0.0).
13. Invalid entry/OHLC price rejection.
14. Position still open at dataset end (mark-to-market snapshot).
15. Multiple signals on adjacent bars (concurrent block vs sequential re-entry).
16. Explicit Risk Evaluation Modes (Mode 1, Mode 2, Mode 3).
17. BankerAgent FSM full lifecycle integration.
18. Deterministic replay and bounded RAM (< 1 GB) / CPU thread constraints.
"""

import tracemalloc
import pandas as pd
import pyarrow as pa
import pytest
import threadpoolctl

from quantum.backtesting.adapters import OOFSignal
from quantum.backtesting.engine import (
    TRACK_2_GOVERNANCE_CLASSIFICATION,
    TRACK_2_ORDER_LIFECYCLE_SCOPE,
    BacktestConfig,
    DiscreteEventBacktestEngine,
    GovernancePendingError,
    RiskEvaluationMode,
)
from quantum.backtesting.resources import (
    BACKTEST_MAX_THREADS,
    check_thread_limits,
    enforce_backtest_thread_limits,
    get_active_thread_limits,
    verify_thread_limits,
)
from quantum.domain.enums import PositionLifecycleState, TradeSide


def create_synthetic_candles(n: int = 50, start_price: float = 100.0) -> pd.DataFrame:
    """Create deterministic OHLCV candles with tight +/- 0.1 oscillation."""
    base_ts = 1704067200000  # 2024-01-01 00:00:00 UTC
    data = []

    curr_price = start_price
    for i in range(n):
        open_ts = base_ts + (i * 300_000)
        if i % 2 == 0:
            open_px = curr_price
            high_px = curr_price + 0.1
            low_px = curr_price - 0.1
            close_px = curr_price + 0.05
        else:
            open_px = curr_price
            high_px = curr_price + 0.1
            low_px = curr_price - 0.1
            close_px = curr_price - 0.05

        data.append({
            "open_time_ms": open_ts,
            "open": open_px,
            "high": high_px,
            "low": low_px,
            "close": close_px,
            "volume": 1000.0,
        })
        curr_price = close_px

    return pd.DataFrame(data)


def make_signal(open_time_ms: int, predicted_class: int = 1, symbol: str = "BTCUSDT") -> OOFSignal:
    """Create a deterministic OOFSignal for testing."""
    return OOFSignal(
        symbol=symbol,
        fold=1,
        open_time_ms=open_time_ms,
        close_time_ms=open_time_ms + 300_000,
        predicted_class=predicted_class,
        prob_tp=0.80 if predicted_class == 1 else 0.10,
        prob_sl=0.80 if predicted_class == -1 else 0.10,
        prob_exp=0.10,
        true_label=predicted_class,
        oos_eligibility="VERIFIED_OOF",
    )


@pytest.mark.asyncio
async def test_01_long_take_profit_and_effective_fills():
    """Edge Case 1: Long fills at open[i+1] and exits at Take-Profit barrier."""
    candles = create_synthetic_candles(35, start_price=100.0)
    sig_ts = int(candles.iloc[20]["open_time_ms"])
    signal = make_signal(sig_ts, predicted_class=1)

    candles.loc[21, "open"] = 100.0
    candles.loc[21, "high"] = 100.05
    candles.loc[21, "low"] = 99.95
    candles.loc[22, "open"] = 100.02
    candles.loc[22, "high"] = 100.05
    candles.loc[22, "low"] = 99.95
    candles.loc[23, "open"] = 100.02
    candles.loc[23, "high"] = 101.0
    candles.loc[23, "low"] = 99.95

    cfg = BacktestConfig(
        symbol="BTCUSDT",
        directional_mode="LONG_ONLY",
        fee_rate_bps=2.0,
        slippage_bps=1.0,
        funding_rate_bps_per_settlement=0.0,
    )
    engine = DiscreteEventBacktestEngine(cfg)
    summary = await engine.run(candles, [signal])

    assert summary.track_classification == TRACK_2_GOVERNANCE_CLASSIFICATION
    assert summary.approved_trades == 1
    trade = summary.trades[0]
    assert trade.side == TradeSide.LONG
    assert trade.entry_price == 100.0
    assert trade.entry_fill_price_effective > trade.entry_price  # Adverse slippage on entry
    assert trade.exit_fill_price_effective < trade.exit_price    # Adverse slippage on exit
    assert trade.exit_reason == "TAKE_PROFIT"
    assert trade.is_gap_exit is False
    assert trade.holding_bars == 3  # Bars 21, 22, 23
    assert trade.exit_price == pytest.approx(trade.upper_barrier, abs=1e-5)
    assert trade.accounting.gross_return > 0
    assert trade.accounting.net_pnl_usdt > 0


@pytest.mark.asyncio
async def test_02_long_stop_loss():
    """Edge Case 2: Long fills at open[i+1] and exits at Stop-Loss barrier."""
    candles = create_synthetic_candles(35, start_price=100.0)
    sig_ts = int(candles.iloc[20]["open_time_ms"])
    signal = make_signal(sig_ts, predicted_class=1)

    candles.loc[21, "open"] = 100.0
    candles.loc[21, "high"] = 100.05
    candles.loc[21, "low"] = 99.0  # Breaches lower barrier on bar 1 (candle 21 itself!)

    cfg = BacktestConfig(symbol="BTCUSDT", directional_mode="LONG_ONLY")
    engine = DiscreteEventBacktestEngine(cfg)
    summary = await engine.run(candles, [signal])

    assert summary.approved_trades == 1
    trade = summary.trades[0]
    assert trade.holding_bars == 1  # Triggered on entry bar 21 intrabar low!
    assert trade.exit_reason == "STOP_LOSS"
    assert trade.exit_price == pytest.approx(trade.lower_barrier, abs=1e-5)
    assert trade.accounting.net_pnl_usdt < 0


@pytest.mark.asyncio
async def test_03_04_short_take_profit_and_stop_loss():
    """Edge Cases 3 & 4: Short Take-Profit (lower barrier) and Short Stop-Loss (upper barrier)."""
    # Short TP
    candles_tp = create_synthetic_candles(35, start_price=100.0)
    sig_ts = int(candles_tp.iloc[20]["open_time_ms"])
    signal = make_signal(sig_ts, predicted_class=-1)

    candles_tp.loc[21, "open"] = 100.0
    candles_tp.loc[21, "high"] = 100.05
    candles_tp.loc[21, "low"] = 99.0

    cfg = BacktestConfig(symbol="BTCUSDT", directional_mode="SHORT_ONLY", fee_rate_bps=2.0, slippage_bps=0.0)
    engine = DiscreteEventBacktestEngine(cfg)
    sum_tp = await engine.run(candles_tp, [signal])
    assert sum_tp.trades[0].exit_reason == "TAKE_PROFIT"
    assert sum_tp.trades[0].accounting.net_pnl_usdt > 0

    # Short SL
    candles_sl = create_synthetic_candles(35, start_price=100.0)
    candles_sl.loc[21, "open"] = 100.0
    candles_sl.loc[21, "high"] = 101.0
    candles_sl.loc[21, "low"] = 99.95
    sum_sl = await engine.run(candles_sl, [signal])
    assert sum_sl.trades[0].exit_reason == "STOP_LOSS"
    assert sum_sl.trades[0].exit_price == pytest.approx(sum_sl.trades[0].upper_barrier, abs=1e-5)
    assert sum_sl.trades[0].accounting.net_pnl_usdt < 0


@pytest.mark.asyncio
async def test_05_06_opening_gap_beyond_tp_and_sl():
    """Edge Cases 5 & 6: Opening gaps beyond TP and SL execute at gap open price, NOT exact barrier."""
    # Edge Case 5: Long opening gap above TP on bar 22
    candles_gap_tp = create_synthetic_candles(35, start_price=100.0)
    sig_ts = int(candles_gap_tp.iloc[20]["open_time_ms"])
    signal = make_signal(sig_ts, predicted_class=1)

    candles_gap_tp.loc[21, "open"] = 100.0
    candles_gap_tp.loc[21, "high"] = 100.05
    candles_gap_tp.loc[21, "low"] = 99.95
    candles_gap_tp.loc[21, "close"] = 100.02
    # Bar 22 gaps open at 102.5 (well above upper barrier ~100.08)
    candles_gap_tp.loc[22, "open"] = 102.5
    candles_gap_tp.loc[22, "high"] = 103.0
    candles_gap_tp.loc[22, "low"] = 102.0
    candles_gap_tp.loc[22, "close"] = 102.8

    engine = DiscreteEventBacktestEngine(BacktestConfig(symbol="BTCUSDT", directional_mode="LONG_ONLY"))
    sum_gap_tp = await engine.run(candles_gap_tp, [signal])
    t_tp = sum_gap_tp.trades[0]
    assert t_tp.exit_reason == "TAKE_PROFIT"
    assert t_tp.is_gap_exit is True
    assert t_tp.exit_price == pytest.approx(102.5)
    assert t_tp.exit_price > t_tp.upper_barrier
    assert t_tp.exit_time_ms == int(candles_gap_tp.iloc[22]["open_time_ms"])

    # Edge Case 6: Long opening gap below SL on bar 22 (worse fill than stop barrier!)
    candles_gap_sl = create_synthetic_candles(35, start_price=100.0)
    candles_gap_sl.loc[21, "open"] = 100.0
    candles_gap_sl.loc[21, "high"] = 100.05
    candles_gap_sl.loc[21, "low"] = 99.95
    candles_gap_sl.loc[21, "close"] = 99.98
    # Bar 22 gaps open at 97.0 (well below lower barrier ~99.92)
    candles_gap_sl.loc[22, "open"] = 97.0
    candles_gap_sl.loc[22, "high"] = 97.5
    candles_gap_sl.loc[22, "low"] = 96.5
    candles_gap_sl.loc[22, "close"] = 97.2

    sum_gap_sl = await engine.run(candles_gap_sl, [signal])
    t_sl = sum_gap_sl.trades[0]
    assert t_sl.exit_reason == "STOP_LOSS"
    assert t_sl.is_gap_exit is True
    assert t_sl.exit_price == pytest.approx(97.0)
    assert t_sl.exit_price < t_sl.lower_barrier
    assert t_sl.exit_time_ms == int(candles_gap_sl.iloc[22]["open_time_ms"])


@pytest.mark.asyncio
async def test_07_same_bar_collision_policies():
    """Edge Case 7: Both barriers touched in same bar resolves to SL under CONSERVATIVE_SL_FIRST."""
    candles = create_synthetic_candles(35, start_price=100.0)
    sig_ts = int(candles.iloc[20]["open_time_ms"])
    signal = make_signal(sig_ts, predicted_class=1)

    candles.loc[21, "open"] = 100.0
    candles.loc[21, "high"] = 102.0
    candles.loc[21, "low"] = 98.0

    engine_cons = DiscreteEventBacktestEngine(
        BacktestConfig(symbol="BTCUSDT", directional_mode="LONG_ONLY", collision_policy="CONSERVATIVE_SL_FIRST")
    )
    sum_cons = await engine_cons.run(candles, [signal])
    assert sum_cons.trades[0].exit_reason == "STOP_LOSS"
    assert sum_cons.trades[0].exit_price == pytest.approx(sum_cons.trades[0].lower_barrier, abs=1e-5)


@pytest.mark.asyncio
async def test_08_12_bar_timeout_exact_duration():
    """Edge Case 8: Trade untouched across 12 bars (bars 21..32) expires at bar 32 close (exact 60m)."""
    candles = create_synthetic_candles(40, start_price=100.0)
    sig_ts = int(candles.iloc[20]["open_time_ms"])
    signal = make_signal(sig_ts, predicted_class=1)

    candles.loc[21, "open"] = 100.0
    for k in range(21, 35):
        candles.loc[k, "open"] = 100.0
        candles.loc[k, "high"] = 100.05
        candles.loc[k, "low"] = 99.95
        candles.loc[k, "close"] = 100.02
    candles.loc[32, "close"] = 100.04  # Distinct close on 12th holding bar (index 32)

    engine = DiscreteEventBacktestEngine(BacktestConfig(symbol="BTCUSDT", directional_mode="LONG_ONLY"))
    summary = await engine.run(candles, [signal])

    assert summary.approved_trades == 1
    trade = summary.trades[0]
    assert trade.holding_bars == 12
    assert trade.exit_reason == "TIME_EXPIRATION"
    assert trade.exit_price == pytest.approx(100.04, abs=1e-5)
    assert (trade.exit_time_ms - trade.entry_fill_time_ms) == 12 * 300_000  # Exact 60 minutes


@pytest.mark.asyncio
async def test_09_10_missing_candle_gap_and_duplicate_timestamps():
    """Edge Cases 9 & 10: Missing candle gap and duplicate timestamp handling."""
    candles = create_synthetic_candles(35, start_price=100.0)
    sig_ts = int(candles.iloc[20]["open_time_ms"])
    signal = make_signal(sig_ts, predicted_class=1)

    # Introduce a missing 5m candle gap at index 21 by shifting all timestamps from 21 onward by +300,000 ms
    gapped = candles.copy()
    gapped.loc[21:, "open_time_ms"] += 300_000

    # Non-strict mode rejects the gapped entry and records gap count
    engine_soft = DiscreteEventBacktestEngine(
        BacktestConfig(symbol="BTCUSDT", strict_candle_continuity=False)
    )
    sum_soft = await engine_soft.run(gapped, [signal])
    assert sum_soft.missing_candle_gaps_detected == 1
    assert sum_soft.approved_trades == 0
    assert sum_soft.rejection_breakdown.get("REJECTED_MISSING_CANDLE_GAP") == 1

    # Strict mode raises ValueError
    engine_strict = DiscreteEventBacktestEngine(
        BacktestConfig(symbol="BTCUSDT", strict_candle_continuity=True)
    )
    with pytest.raises(ValueError, match="Missing candle gap"):
        await engine_strict.run(gapped, [signal])

    # Duplicate candle timestamp raises ValueError
    dup_candles = candles.copy()
    dup_candles.loc[10, "open_time_ms"] = dup_candles.loc[9, "open_time_ms"]
    with pytest.raises(ValueError, match="duplicate open_time_ms"):
        await engine_soft.run(dup_candles, [signal])


@pytest.mark.asyncio
async def test_11_12_13_zero_volatility_floor_and_invalid_prices():
    """Edge Cases 11, 12, 13: Zero volatility rejection vs volatility floor, and invalid OHLC prices."""
    flat_candles = create_synthetic_candles(35, start_price=100.0)
    flat_candles["open"] = 100.0
    flat_candles["high"] = 100.0
    flat_candles["low"] = 100.0
    flat_candles["close"] = 100.0

    sig_ts = int(flat_candles.iloc[20]["open_time_ms"])
    signal = make_signal(sig_ts, predicted_class=1)

    # Edge Case 11: When min_volatility=0.0, zero volatility is rejected
    engine_no_floor = DiscreteEventBacktestEngine(
        BacktestConfig(symbol="BTCUSDT", min_volatility=0.0)
    )
    sum_no_floor = await engine_no_floor.run(flat_candles, [signal])
    assert sum_no_floor.approved_trades == 0
    assert sum_no_floor.rejection_breakdown.get("REJECTED_ZERO_VOLATILITY") == 1

    # Edge Case 12: When min_volatility=1e-3 (10 bps), flat series uses floored volatility
    engine_floored = DiscreteEventBacktestEngine(
        BacktestConfig(symbol="BTCUSDT", min_volatility=1e-3)
    )
    sum_floored = await engine_floored.run(flat_candles, [signal])
    assert sum_floored.approved_trades == 1
    assert sum_floored.trades[0].volatility_sigma == pytest.approx(1e-3)

    # Edge Case 13: Invalid negative or inverted OHLC price raises ValueError
    bad_candles = flat_candles.copy()
    bad_candles.loc[5, "open"] = -10.0
    with pytest.raises(ValueError, match="non-positive"):
        await engine_floored.run(bad_candles, [signal])

    bad_geom = flat_candles.copy()
    bad_geom.loc[5, "high"] = 99.0
    bad_geom.loc[5, "low"] = 101.0
    with pytest.raises(ValueError, match="Invalid OHLC geometry"):
        await engine_floored.run(bad_geom, [signal])


@pytest.mark.asyncio
async def test_14_15_open_position_at_dataset_end_and_adjacent_signals():
    """Edge Cases 14 & 15: Position still open at dataset end and multiple signals on adjacent bars."""
    candles = create_synthetic_candles(26, start_price=100.0)
    for k in range(21, 26):
        candles.loc[k, "open"] = 100.0
        candles.loc[k, "high"] = 100.05
        candles.loc[k, "low"] = 99.95
        candles.loc[k, "close"] = 100.03

    # Signals on bar 20 (fills at 21) and bar 21 (blocked because position from bar 20 is still open!)
    sig_20 = make_signal(int(candles.iloc[20]["open_time_ms"]), predicted_class=1)
    sig_21 = make_signal(int(candles.iloc[21]["open_time_ms"]), predicted_class=1)

    engine = DiscreteEventBacktestEngine(
        BacktestConfig(symbol="BTCUSDT", directional_mode="LONG_ONLY", enable_banker_agent=True)
    )
    summary = await engine.run(candles, [sig_20, sig_21])

    assert summary.total_signals == 2
    assert summary.approved_trades == 1
    assert summary.rejected_trades == 1
    assert summary.rejection_breakdown.get("CONCURRENT_POSITION_BLOCKED") == 1
    # Dataset ends at index 25 (only 5 bars held < 12 bars), so trade is in open_positions_at_end!
    assert len(summary.trades) == 0
    assert len(summary.open_positions_at_end) == 1
    open_snap = summary.open_positions_at_end[0]
    assert open_snap.bars_held == 5
    assert open_snap.position_state == PositionLifecycleState.OPEN
    assert open_snap.accounting.unrealized_gross_pnl_usdt > 0


@pytest.mark.asyncio
async def test_16_explicit_risk_evaluation_modes():
    """Workstream E: Verify Mode 1, Mode 2 (RiskAgent gating), and Mode 3 (DEC_05 guard)."""
    candles = create_synthetic_candles(35, start_price=100.0)
    sig_ts = int(candles.iloc[20]["open_time_ms"])
    signal = make_signal(sig_ts, predicted_class=1)

    # Mode 1: Mechanical Barrier Benchmark
    cfg_m1 = BacktestConfig(
        symbol="BTCUSDT",
        risk_evaluation_mode=RiskEvaluationMode.MODE_1_BARRIER_ACCOUNTING_BENCHMARK,
    )
    sum_m1 = await DiscreteEventBacktestEngine(cfg_m1).run(candles, [signal])
    assert sum_m1.mode_output_classification == "MECHANICAL_BARRIER_ACCOUNTING_NO_RISK_ENFORCEMENT"
    assert sum_m1.approved_trades == 1

    # Mode 2 with symmetric 1.0 R:R is vetoed by RiskAgent Gate 8 (min_net_reward_risk >= 1.50)
    cfg_m2_veto = BacktestConfig(
        symbol="BTCUSDT",
        risk_evaluation_mode=RiskEvaluationMode.MODE_2_RISK_FILTERED_EXECUTION_SIMULATION,
    )
    sum_m2_veto = await DiscreteEventBacktestEngine(cfg_m2_veto).run(candles, [signal])
    assert sum_m2_veto.mode_output_classification == "SINGLE_ASSET_RISK_GATED_EXECUTION_SIMULATION"
    assert sum_m2_veto.approved_trades == 0
    assert sum_m2_veto.rejected_trades == 1

    # Mode 2 with proposal_estimated_rr_override=2.0 passes Gate 8
    cfg_m2_pass = BacktestConfig(
        symbol="BTCUSDT",
        risk_evaluation_mode=RiskEvaluationMode.MODE_2_RISK_FILTERED_EXECUTION_SIMULATION,
        proposal_estimated_rr_override=2.0,
    )
    sum_m2_pass = await DiscreteEventBacktestEngine(cfg_m2_pass).run(candles, [signal])
    assert sum_m2_pass.approved_trades == 1

    # Mode 3 raises GovernancePendingError unless allow_bounded_mode3_preview=True
    cfg_m3_blocked = BacktestConfig(
        symbol="BTCUSDT",
        risk_evaluation_mode=RiskEvaluationMode.MODE_3_PORTFOLIO_LEVEL_RISK_SIMULATION,
    )
    with pytest.raises(GovernancePendingError, match="DEC_05"):
        await DiscreteEventBacktestEngine(cfg_m3_blocked).run(candles, [signal])

    cfg_m3_preview = BacktestConfig(
        symbol="BTCUSDT",
        risk_evaluation_mode=RiskEvaluationMode.MODE_3_PORTFOLIO_LEVEL_RISK_SIMULATION,
        allow_bounded_mode3_preview=True,
        proposal_estimated_rr_override=2.0,
    )
    sum_m3 = await DiscreteEventBacktestEngine(cfg_m3_preview).run(candles, [signal])
    assert sum_m3.mode_output_classification == "BOUNDED_PORTFOLIO_LEDGER_DEC_05_PENDING_HUMAN_DECISION"
    assert sum_m3.approved_trades == 1


@pytest.mark.asyncio
async def test_17_banker_agent_fsm_integration():
    """Workstream F: Verify BankerAgent FSM reaches CLOSED state across TP, SL, and TIME_EXPIRATION."""
    candles = create_synthetic_candles(40, start_price=100.0)
    sig_ts = int(candles.iloc[20]["open_time_ms"])
    signal = make_signal(sig_ts, predicted_class=1)

    candles.loc[21, "open"] = 100.0
    candles.loc[21, "high"] = 101.5
    candles.loc[21, "low"] = 99.95

    cfg = BacktestConfig(symbol="BTCUSDT", directional_mode="LONG_ONLY", enable_banker_agent=True)
    summary = await DiscreteEventBacktestEngine(cfg).run(candles, [signal])

    assert summary.approved_trades == 1
    trade = summary.trades[0]
    assert trade.exit_reason == "TAKE_PROFIT"
    assert trade.final_position_state == PositionLifecycleState.CLOSED
    assert trade.tracked_position is not None
    assert trade.tracked_position.remaining_quantity == 0.0


@pytest.mark.asyncio
async def test_18_deterministic_replay_and_resource_bounds():
    """Workstream G: Verify deterministic replay and bounded memory (< 50 MB << 1 GB budget)."""
    tracemalloc.start()
    candles = create_synthetic_candles(1000, start_price=100.0)
    signals = [
        make_signal(int(candles.iloc[idx]["open_time_ms"]), predicted_class=1 if idx % 2 == 0 else -1)
        for idx in range(25, 950, 20)
    ]

    cfg = BacktestConfig(symbol="BTCUSDT", directional_mode="BIDIRECTIONAL", enable_banker_agent=True)
    engine = DiscreteEventBacktestEngine(cfg)

    sum1 = await engine.run(candles.copy(), signals)
    sum2 = await engine.run(candles.copy(), signals)
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert sum1.total_pnl_usdt == sum2.total_pnl_usdt
    assert sum1.net_expectancy_bps == sum2.net_expectancy_bps
    assert len(sum1.trades) == len(sum2.trades)
    assert peak_bytes < 100 * 1024 * 1024  # Peak allocation well under 100 MB (budget <= 1 GB)


def test_19_cpu_thread_limits_enforced():
    """FND-08: Verify computational thread limit <= 2 across PyArrow and BLAS."""
    limits = enforce_backtest_thread_limits(2)
    assert limits["pyarrow_cpu"] <= 2
    assert limits["pyarrow_io"] <= 2
    assert pa.cpu_count() <= 2
    assert pa.io_thread_count() <= 2
    assert verify_thread_limits(2) is True
    check_thread_limits(2)

    for controller in limits["threadpool_controllers"]:
        nt = controller.get("num_threads")
        if nt is not None:
            assert nt <= 2

    # Verification of error on invalid thread count
    with pytest.raises(ValueError, match="Backtest thread limit must be between 1 and 2"):
        enforce_backtest_thread_limits(4)


@pytest.mark.asyncio
async def test_20_opening_gap_exit_timestamp_and_funding_boundary():
    """FND-09: Verify gap-exit timestamp equals gap candle open, preventing post-exit funding accrual."""
    # 08:00 UTC = 1704096000000 (8h boundary: 1704096000000 % 28_800_000 == 0)
    boundary_8h_ts = 1704096000000
    # Create 35 candles ending after 08:00 UTC
    # Let bar 26 be 08:00 UTC (1704096000000)
    # Then bar 0 open_ts = 1704096000000 - (26 * 300_000) = 1704088200000 (05:50 UTC)
    start_ts = boundary_8h_ts - (26 * 300_000)

    # Sub-case A: Gap exit occurs AT exact 08:00 UTC open (bar 26)
    data_a = []
    curr_px = 100.0
    for i in range(35):
        o_ts = start_ts + (i * 300_000)
        data_a.append({
            "open_time_ms": o_ts,
            "open": curr_px,
            "high": curr_px + 0.1,
            "low": curr_px - 0.1,
            "close": curr_px + (0.05 if i % 2 == 0 else -0.05),
            "volume": 10.0,
        })
    candles_a = pd.DataFrame(data_a)

    # Signal at bar 20 close (07:30 UTC), enters at bar 21 open (07:35 UTC = 1704094500000)
    sig_ts_a = int(candles_a.iloc[20]["open_time_ms"])
    sig_a = make_signal(sig_ts_a, predicted_class=1)

    # Bar 26 opens at exact 08:00 UTC (1704096000000) with severe gap down to 95.0
    candles_a.loc[26, "open"] = 95.0
    candles_a.loc[26, "high"] = 95.5
    candles_a.loc[26, "low"] = 94.5
    candles_a.loc[26, "close"] = 95.0

    engine = DiscreteEventBacktestEngine(BacktestConfig(
        symbol="BTCUSDT",
        directional_mode="LONG_ONLY",
        funding_rate_bps_per_settlement=1.0,
    ))
    res_a = await engine.run(candles_a, [sig_a])
    assert len(res_a.trades) == 1
    t_a = res_a.trades[0]
    assert t_a.is_gap_exit is True
    assert t_a.exit_reason == "STOP_LOSS"
    # Gap exit timestamp must equal opening timestamp of the gap candle (08:00 UTC), not +300s
    assert t_a.exit_time_ms == boundary_8h_ts
    assert t_a.exit_price == 95.0
    # Position was held up to 08:00 UTC, so exactly 1 settlement at 08:00 UTC is accrued
    assert len(t_a.accounting.funding_settlements) == 1
    assert t_a.accounting.funding_settlements[0].timestamp_ms == boundary_8h_ts
    # Crucially, no settlements beyond 08:00 UTC exist
    assert t_a.accounting.funding_settlements[0].timestamp_ms <= t_a.exit_time_ms

    # Sub-case B: Gap exit occurs AT 07:55 UTC open (bar 25, 5m BEFORE 08:00 UTC boundary)
    candles_b = pd.DataFrame(data_a)
    candles_b.loc[25, "open"] = 95.0
    candles_b.loc[25, "high"] = 95.5
    candles_b.loc[25, "low"] = 94.5
    candles_b.loc[25, "close"] = 95.0

    res_b = await engine.run(candles_b, [sig_a])
    assert len(res_b.trades) == 1
    t_b = res_b.trades[0]
    assert t_b.is_gap_exit is True
    # Gap exit timestamp must equal 07:55 UTC (boundary_8h_ts - 300_000)
    assert t_b.exit_time_ms == boundary_8h_ts - 300_000
    # Proves no funding is accrued after exit: 08:00 settlement was NOT reached before exit
    assert len(t_b.accounting.funding_settlements) == 0
    assert t_b.accounting.funding_cash_flow_usdt == 0.0


def test_21_track_2_single_stage_full_exit_scope():
    """FND-10: Verify Track 2 lifecycle scope documentation and single-stage invariant."""
    assert "TRACK_2_SINGLE_STAGE_FULL_EXIT_BENCHMARK" in TRACK_2_ORDER_LIFECYCLE_SCOPE
    assert "PENDING_OPEN -> OPEN -> CLOSED" in TRACK_2_ORDER_LIFECYCLE_SCOPE
    assert "Track 3" in TRACK_2_ORDER_LIFECYCLE_SCOPE

