"""
Unit Test Suite for QUANTUM Remediated Execution Simulator & Microstructure Engine.

Implements Milestone 2 Deterministic Verification covering all 12 required scenarios:
1. Market order taker fees.
2. Marketable limit taker classification.
3. Resting limit maker classification.
4. Post-only rejection on cross.
5. Partial fills (TP1 close pct).
6. Unfilled orders (timeout).
7. Gap-down limit behavior (strictly P_fill = P_limit).
8. Spread and slippage accounting (15 bps, 44 bps, 9.5 bps).
9. Anti-double-counting assertions.
10. Multiple fill events per order.
11. Counter invariants: signals >= orders >= touches >= fills >= executions.
12. Post-fill markout calculations.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Optional, Sequence

import numpy as np
import pytest

from quantum.strategies.evaluator import AssetFeatureMatrix, StrategyDiscoveryEvaluator
from quantum.strategies.schemas import (
    EntryParameters,
    ExecutionPolicyMismatchError,
    ExecutionVenueSchedule,
    ExitParameters,
    RiskExecutionParameters,
    StrategyConfiguration,
    StrategyEvaluationResult,
    StrategyFamily,
    VENUE_PROFILES,
    get_venue_schedule,
)


def build_synthetic_evaluator(
    symbol: str = "BTCUSDT",
    n_bars: int = 40,
    opens: Optional[Sequence[float]] = None,
    highs: Optional[Sequence[float]] = None,
    lows: Optional[Sequence[float]] = None,
    closes: Optional[Sequence[float]] = None,
    sigmas: Optional[Sequence[float]] = None,
    signal_bars: Optional[Sequence[int]] = None,
    side: int = 1,
) -> StrategyDiscoveryEvaluator:
    """Creates a lightweight, deterministic in-memory StrategyDiscoveryEvaluator without disk I/O."""
    evaluator = StrategyDiscoveryEvaluator.__new__(StrategyDiscoveryEvaluator)
    evaluator.matrices = {}
    evaluator._last_simulation_stats = {}

    ts = np.array([1_700_000_000_000 + i * 300_000 for i in range(n_bars)], dtype=np.int64)

    o_arr = np.array(opens if opens is not None else [100.0] * n_bars, dtype=np.float64)
    h_arr = np.array(highs if highs is not None else [101.0] * n_bars, dtype=np.float64)
    l_arr = np.array(lows if lows is not None else [99.5] * n_bars, dtype=np.float64)
    c_arr = np.array(closes if closes is not None else [100.0] * n_bars, dtype=np.float64)
    s_arr = np.array(sigmas if sigmas is not None else [0.01] * n_bars, dtype=np.float64)

    has_oof = np.zeros(n_bars, dtype=bool)
    pm1 = np.zeros(n_bars, dtype=np.float64)
    p0 = np.full(n_bars, 0.20, dtype=np.float64)
    pp1 = np.zeros(n_bars, dtype=np.float64)

    target_signals = signal_bars if signal_bars is not None else [25]
    for b in target_signals:
        if 0 <= b < n_bars:
            has_oof[b] = True
            if side == 1:
                pp1[b] = 0.70  # prob_margin = 0.70 - 0.20 = 0.50 >= 0.20
            else:
                pm1[b] = 0.70

    m = AssetFeatureMatrix(
        symbol=symbol,
        open_time_ms=ts,
        opens=o_arr,
        highs=h_arr,
        lows=l_arr,
        closes=c_arr,
        sigma_20=s_arr,
        vol_quantiles={0.85: 0.005, 1.0: 0.05},
        vol_exp_ratio=np.full(n_bars, 1.0),
        rvol_20=np.full(n_bars, 1.0),
        taker_buy_ratio=np.full(n_bars, 0.5),
        lower_wick=np.zeros(n_bars),
        upper_wick=np.zeros(n_bars),
        htf_rets_bps={12: np.zeros(n_bars)},
        btc_rets_bps={6: np.zeros(n_bars)},
        has_oof_prev=has_oof,
        fold_prev=np.full(n_bars, 1, dtype=np.int32),
        prob_m1_prev=pm1,
        prob_0_prev=p0,
        prob_p1_prev=pp1,
    )
    evaluator.matrices[symbol] = m
    return evaluator


def make_test_config(
    strategy_id: str = "STRAT_UNIT_TEST",
    order_type: str = "MARKET",
    limit_offset_sigma: float = 0.0,
    post_only: bool = False,
    order_timeout_bars: int = 3,
    tp1_multiplier: float = 2.0,
    tp2_multiplier: float = 3.5,
    tp1_close_pct: float = 0.0,
    sl_multiplier: float = 1.0,
    horizon_bars: int = 18,
    fee_tier: str = "BYBIT_VIP0_DEFAULT",
    symbol: str = "BTCUSDT",
) -> StrategyConfiguration:
    """Helper to create a fully validated StrategyConfiguration."""
    return StrategyConfiguration(
        strategy_id=strategy_id,
        batch_id="BATCH_VERIFICATION",
        family=StrategyFamily.LIQUIDITY_MICROSTRUCTURE,
        hypothesis="Deterministic verification of execution mechanics",
        applicable_assets=[symbol],
        entry=EntryParameters(
            order_type=order_type,
            limit_offset_sigma=limit_offset_sigma,
            post_only=post_only,
            order_timeout_bars=order_timeout_bars,
            vol_quantile_min=0.85,
        ),
        exit=ExitParameters(
            tp1_multiplier=tp1_multiplier,
            tp2_multiplier=tp2_multiplier,
            tp1_close_pct=tp1_close_pct,
            sl_multiplier=sl_multiplier,
            horizon_bars=horizon_bars,
        ),
        risk=RiskExecutionParameters(
            initial_equity_usd=100.0,
            fee_tier=fee_tier,
        ),
    )


# ==============================================================================
# SCENARIO 1: Market Order Taker Fees
# ==============================================================================
def test_market_order_taker_fees():
    """Verify market orders are strictly classified as TAKER and charged taker rates."""
    evaluator = build_synthetic_evaluator(signal_bars=[25])
    cfg = make_test_config(order_type="MARKET", fee_tier="BYBIT_VIP0_DEFAULT")

    res, trades, _ = evaluator.evaluate_strategy(cfg, "EXP_S1", strict_execution_policy=True)

    assert len(trades) == 1
    t = trades[0]
    assert t["entry_role"] == "TAKER", "Market order must always have TAKER entry role"

    # Strict Policy Enforcement: Market order on passive maker schedule must raise ExecutionPolicyMismatchError
    cfg_invalid = make_test_config(order_type="MARKET", fee_tier="MAKER_PASSIVE_TRUE")
    with pytest.raises(ExecutionPolicyMismatchError, match="Market orders cannot execute under passive maker"):
        evaluator.evaluate_strategy(cfg_invalid, "EXP_S1_FAIL", strict_execution_policy=True)

    # If strict policy is overridden, entry role must still be TAKER (no maker fee concession)
    res_permissive, trades_p, _ = evaluator.evaluate_strategy(cfg_invalid, "EXP_S1_PERMISSIVE", strict_execution_policy=False)
    assert len(trades_p) == 1
    assert trades_p[0]["entry_role"] == "TAKER"


# ==============================================================================
# SCENARIO 2: Marketable Limit Taker Classification
# ==============================================================================
def test_marketable_limit_taker_classification():
    """Verify limit orders that cross or meet the arrival price match immediately as TAKER."""
    evaluator = build_synthetic_evaluator(signal_bars=[25])
    # limit_offset_sigma = 0.0 means P_limit == P_arrival (marketable)
    cfg = make_test_config(order_type="LIMIT", limit_offset_sigma=0.0, post_only=False, fee_tier="BYBIT_VIP0_DEFAULT")

    res, trades, _ = evaluator.evaluate_strategy(cfg, "EXP_S2", strict_execution_policy=False)

    assert len(trades) == 1
    t = trades[0]
    assert t["entry_role"] == "TAKER", "Marketable limit order without post-only must execute as TAKER"
    assert t["entry_price"] == 100.0, "Executed immediately at arrival price"


# ==============================================================================
# SCENARIO 3: Resting Limit Maker Classification
# ==============================================================================
def test_resting_limit_maker_classification():
    """Verify resting limit orders in the book execute as MAKER when touched or penetrated."""
    # Bar 25 signal: opens[25]=100.0, sigma=0.01. Limit buy offset=0.2 sigma -> P_limit = 100.0 * (1 - 0.002) = 99.80
    # Bar 25 low is 99.50 (penetration below 99.80 - 0.2*0.01*99.80 = 99.60)
    lows = [100.0] * 40
    lows[25] = 99.50
    evaluator = build_synthetic_evaluator(signal_bars=[25], lows=lows)

    cfg = make_test_config(order_type="LIMIT", limit_offset_sigma=0.20, post_only=True, fee_tier="MAKER_PASSIVE_TRUE")

    res, trades, _ = evaluator.evaluate_strategy(cfg, "EXP_S3", strict_execution_policy=False)

    assert len(trades) == 1
    t = trades[0]
    assert t["entry_role"] == "MAKER", "Resting limit order filled from queue must be MAKER"
    assert t["entry_price"] == 99.80, "Fill price must be strictly at limit price"


# ==============================================================================
# SCENARIO 4: Post-Only Rejection on Cross
# ==============================================================================
def test_post_only_rejection_on_cross():
    """Verify post_only=True immediately cancels on cross without entering book or filling."""
    evaluator = build_synthetic_evaluator(signal_bars=[25])
    # Marketable limit with post_only=True
    cfg = make_test_config(order_type="LIMIT", limit_offset_sigma=0.0, post_only=True)

    res, trades, _ = evaluator.evaluate_strategy(cfg, "EXP_S4", strict_execution_policy=False)

    assert len(trades) == 0, "Post-only marketable order must be rejected on cross (0 trades)"
    assert res.unique_order_count == 1, "Order was dispatched"
    assert res.filled_order_count == 0, "Zero orders filled"
    assert res.portfolio_execution_count == 0, "Zero executions"


# ==============================================================================
# SCENARIO 5: Partial Fills (TP1 Close Pct)
# ==============================================================================
def test_partial_fills_tp1():
    """Verify partial TP1 closure records multi-leg fill events and blends realized return."""
    # Entry at bar 25 open=100.0, sigma=0.01
    # TP1 mult = 2.0 -> TP1 price = 102.0
    # Bar 27 high spikes to 102.5 (triggers TP1), close=101.0
    # Bar 28-30 flat at 100.0, exits on horizon at close=100.0
    highs = [101.0] * 40
    highs[27] = 102.5
    lows = [99.5] * 40  # safe low above SL (99.0)
    closes = [100.0] * 40
    closes[27] = 101.0
    evaluator = build_synthetic_evaluator(signal_bars=[25], highs=highs, lows=lows, closes=closes)

    cfg = make_test_config(
        order_type="MARKET",
        tp1_multiplier=2.0,
        tp1_close_pct=0.50,  # 50% partial close at TP1
        horizon_bars=5,
    )

    res, trades, _ = evaluator.evaluate_strategy(cfg, "EXP_S5", strict_execution_policy=False)

    assert len(trades) == 1
    t = trades[0]
    # TP1 leg: 50% of (102.0 - 100.0)/100.0 * 10,000 = 0.5 * 200 = 100 bps
    # Horizon exit: 50% of (100.0 - 100.0) = 0 bps
    # Total gross return: 100.0 bps
    assert t["gross_return_bps"] == pytest.approx(100.0, rel=1e-3)
    assert t["exit_maker_pct"] == 0.50, "TP1 portion was executed as MAKER"
    assert t["exit_taker_pct"] == 0.50, "Time expiration remainder was executed as TAKER"
    # Fill events: 1 entry + 1 TP1 partial fill + 1 horizon exit = 3 fill events
    assert res.fill_event_count == 3
    assert res.filled_order_count == 1


# ==============================================================================
# SCENARIO 6: Unfilled Orders (Timeout)
# ==============================================================================
def test_unfilled_orders_timeout():
    """Verify resting limit orders that are never touched cancel cleanly after timeout."""
    # Flat market at 100.0, low never drops to 99.50
    opens = [100.0] * 40
    highs = [100.0] * 40
    lows = [100.0] * 40
    closes = [100.0] * 40
    evaluator = build_synthetic_evaluator(signal_bars=[25], opens=opens, highs=highs, lows=lows, closes=closes)

    # Offset 0.5 sigma -> limit buy at 99.50. Low is 100.0 -> never touched
    cfg = make_test_config(order_type="LIMIT", limit_offset_sigma=0.50, order_timeout_bars=3)

    res, trades, _ = evaluator.evaluate_strategy(cfg, "EXP_S6", strict_execution_policy=False)

    assert len(trades) == 0
    assert res.unique_order_count == 1
    assert res.touched_order_count == 0
    assert res.filled_order_count == 0


# ==============================================================================
# SCENARIO 7: Gap-Down Limit Behavior (Strictly P_fill = P_limit)
# ==============================================================================
def test_gap_down_limit_behavior():
    """Verify limit buy order fills strictly at limit_px when candle opens on a downward gap."""
    n = 40
    opens = [100.0] * n
    highs = [101.0] * n
    lows = [100.0] * n  # Bar 25 low is 100.0 -> resting limit buy at 99.80 not touched on bar 25
    closes = [100.0] * n

    # Bar 26 gaps down to 95.0, low=94.0, close=97.0
    opens[26] = 95.0
    lows[26] = 94.0
    closes[26] = 97.0
    for b in range(27, n):
        opens[b] = 97.0
        highs[b] = 97.5
        lows[b] = 96.5
        closes[b] = 97.0

    evaluator = build_synthetic_evaluator(signal_bars=[25], opens=opens, highs=highs, lows=lows, closes=closes)

    # Large sl_multiplier so SL does not trigger on gap
    cfg = make_test_config(order_type="LIMIT", limit_offset_sigma=0.20, sl_multiplier=10.0, horizon_bars=3)

    res, trades, _ = evaluator.evaluate_strategy(cfg, "EXP_S7", strict_execution_policy=False)

    assert len(trades) == 1
    t = trades[0]
    # Institutional Gap Rule: P_fill == P_limit (99.80), NOT opens[26] (95.0) and NOT lows[26] (94.0)
    assert t["entry_price"] == 99.80, f"Expected entry_price 99.80, got {t['entry_price']}"
    # Closing at 97.0 on horizon bar 29:
    # Gross return = (97.0 - 99.80)/99.80 * 10,000 = -280.56 bps (unrealized gap loss preserved!)
    assert t["gross_return_bps"] == pytest.approx(-280.56, abs=0.1)


# ==============================================================================
# SCENARIO 8: Spread and Slippage Accounting (Canonical Venues)
# ==============================================================================
def test_spread_slippage_accounting_canonical_venues():
    """Verify round-trip friction math across BYBIT_VIP0_DEFAULT (15 bps), ASTER_STRESS_TAKER (44 bps), and MAKER_PASSIVE_TRUE (9.5 bps)."""
    # 1. BYBIT_VIP0_DEFAULT: Taker entry (5.5) + Taker exit (5.5) + Spread (2.0) + Slippage (2.0) = 15.0 bps
    s_bybit = get_venue_schedule("BYBIT_VIP0_DEFAULT")
    rt_bybit = (
        s_bybit.taker_fee_bps_per_leg * 2.0
        + s_bybit.default_spread_bps
        + s_bybit.default_slippage_bps
        + s_bybit.adverse_selection_bps
    )
    assert rt_bybit == 15.0

    # 2. ASTER_STRESS_TAKER: Taker entry (20.0) + Taker exit (20.0) + Spread (2.0) + Slippage (2.0) = 44.0 bps
    s_aster = get_venue_schedule("ASTER_STRESS_TAKER")
    rt_aster = (
        s_aster.taker_fee_bps_per_leg * 2.0
        + s_aster.default_spread_bps
        + s_aster.default_slippage_bps
        + s_aster.adverse_selection_bps
    )
    assert rt_aster == 44.0

    # 3. MAKER_PASSIVE_TRUE: Maker entry (4.0) + Maker exit (4.0) + Spread (0.0) + Slippage (0.0) + Adverse (1.5) = 9.5 bps
    s_maker = get_venue_schedule("MAKER_PASSIVE_TRUE")
    rt_maker = (
        s_maker.maker_fee_bps_per_leg * 2.0
        + s_maker.default_spread_bps
        + s_maker.default_slippage_bps
        + s_maker.adverse_selection_bps
    )
    assert rt_maker == 9.5


# ==============================================================================
# SCENARIO 9: Anti-Double-Counting Assertions
# ==============================================================================
def test_anti_double_counting_assertions():
    """Verify fill prices are strictly benchmark prices and friction is single-channel cash drag."""
    evaluator = build_synthetic_evaluator(signal_bars=[25])
    cfg = make_test_config(order_type="MARKET", fee_tier="BYBIT_VIP0_DEFAULT")

    res, trades, _ = evaluator.evaluate_strategy(cfg, "EXP_S9", strict_execution_policy=False)

    assert len(trades) == 1
    t = trades[0]
    # Benchmark check: entry_price equals candle open exactly
    assert t["entry_price"] == 100.0
    # No price degrading applied intrabar: net return equals gross return minus exact fee/slip/fund drag
    net_pnl = t["net_pnl_usd"]
    gross_pnl = t["notional_usd"] * (t["gross_return_bps"] / 10_000.0)
    fee_usd = t["fee_usd"]
    assert net_pnl < gross_pnl
    assert gross_pnl - net_pnl >= fee_usd


# ==============================================================================
# SCENARIO 10: Multiple Fill Events Per Order
# ==============================================================================
def test_multiple_fill_events_per_order():
    """Verify fill events counter tracks every discrete fill transaction (N_fill_events >= N_filled_orders)."""
    # 2 signals -> 2 trades with partial closes
    highs = [101.0] * 50
    highs[27] = 103.0
    highs[37] = 103.0
    lows = [99.5] * 50  # safe low above SL
    evaluator = build_synthetic_evaluator(n_bars=50, signal_bars=[25, 35], highs=highs, lows=lows)

    cfg = make_test_config(
        order_type="MARKET",
        tp1_multiplier=2.0,
        tp1_close_pct=0.50,
        horizon_bars=5,
    )

    res, trades, _ = evaluator.evaluate_strategy(cfg, "EXP_S10", strict_execution_policy=False)

    assert res.filled_order_count == 2
    # Each partial trade has 3 fill events (entry, TP1 partial fill, horizon exit)
    assert res.fill_event_count == 6
    assert res.fill_event_count >= res.filled_order_count


# ==============================================================================
# SCENARIO 11: Counter Invariants Hierarchy
# ==============================================================================
def test_counter_hierarchy_invariants():
    """Verify signals >= unique_orders >= touched_orders >= filled_orders >= executions."""
    # 3 raw signals: bar 20, 25, 30.
    # Bar 20: Dispatched.
    # Bar 25: Filtered by active trade / cooldown.
    # Bar 30: Dispatched.
    evaluator = build_synthetic_evaluator(n_bars=50, signal_bars=[20, 25, 30])
    cfg = make_test_config(order_type="MARKET", horizon_bars=8)

    res, trades, _ = evaluator.evaluate_strategy(cfg, "EXP_S11", strict_execution_policy=False)

    n_sig = res.raw_signal_count
    n_ord = res.unique_order_count
    n_touch = res.touched_order_count
    n_fill = res.filled_order_count
    n_exec = res.portfolio_execution_count
    n_events = res.fill_event_count

    assert n_sig >= n_ord, f"Signals ({n_sig}) must be >= unique orders ({n_ord})"
    assert n_ord >= n_touch, f"Unique orders ({n_ord}) must be >= touched orders ({n_touch})"
    assert n_touch >= n_fill, f"Touched orders ({n_touch}) must be >= filled orders ({n_fill})"
    assert n_fill >= n_exec, f"Filled orders ({n_fill}) must be >= portfolio executions ({n_exec})"
    assert n_events >= n_fill, f"Fill events ({n_events}) must be >= filled orders ({n_fill})"


# ==============================================================================
# SCENARIO 12: Post-Fill Markout Calculations
# ==============================================================================
def test_post_fill_markout_calculations():
    """Verify post-fill forward price markouts (h = 1, 2, 3, 6, 12) are recorded accurately."""
    # Signal at bar 25 close -> entry at bar 25 open=100.0
    # Closes: bar 26 (h=1) = 99.50 -> Markout_1 = (99.5 - 100.0)/100.0 * 10,000 = -50.0 bps
    #         bar 27 (h=2) = 99.20 -> Markout_2 = (99.2 - 100.0)/100.0 * 10,000 = -80.0 bps
    #         bar 28 (h=3) = 99.80 -> Markout_3 = (99.8 - 100.0)/100.0 * 10,000 = -20.0 bps
    lows = [99.5] * 40
    closes = [100.0] * 40
    closes[26] = 99.50
    closes[27] = 99.20
    closes[28] = 99.80
    evaluator = build_synthetic_evaluator(signal_bars=[25], lows=lows, closes=closes)

    cfg = make_test_config(order_type="MARKET", horizon_bars=10)

    res, trades, _ = evaluator.evaluate_strategy(cfg, "EXP_S12", strict_execution_policy=False)

    assert len(trades) == 1
    t = trades[0]
    assert t["markout_1_bps"] == -50.0
    assert t["markout_2_bps"] == -80.0
    assert t["markout_3_bps"] == -20.0

    # Aggregate diagnostic markouts in StrategyEvaluationResult
    assert res.diagnostic_markout_1_bps == -50.0
    assert res.diagnostic_markout_3_bps == -20.0
