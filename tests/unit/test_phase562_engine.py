"""Unit tests for Phase 5.6.2 Engine."""

import math
import numpy as np
import pandas as pd
import pytest

from quantum.backtesting.adapters import PROSPECTIVE_HOLDOUT_START_MS
from quantum.backtesting.phase562_engine import (
    COST_TIER_BASELINE_TAKER,
    COST_TIER_HYBRID,
    COST_TIER_MAKER_PASSIVE,
    CompletedTrade,
    CostSchedule,
    Phase562Engine,
    StrategyConfig,
    calculate_sharpe_sortino,
)


def test_cost_schedule_friction():
    maker = COST_TIER_MAKER_PASSIVE
    assert maker.round_trip_friction_bps == 8.0

    hybrid = COST_TIER_HYBRID
    assert hybrid.round_trip_friction_bps == 15.0

    taker = COST_TIER_BASELINE_TAKER
    assert taker.round_trip_friction_bps == 44.0


def test_sharpe_sortino_calculation():
    # Constant positive returns: Sharpe should be non-negative
    rets = np.array([0.01, 0.02, 0.015, 0.025, 0.018])
    sharpe, sortino = calculate_sharpe_sortino(rets, periods_per_year=365.25)
    assert sharpe > 0.0
    assert sortino >= sharpe  # No downside returns, sortino defaults to sharpe

    # Empty or single return
    assert calculate_sharpe_sortino(np.array([0.01])) == (0.0, 0.0)


def test_holdout_seal_enforcement(tmp_path):
    engine = Phase562Engine(candle_base_dir=tmp_path / "candles", oof_dir=tmp_path / "oof")

    # Create dummy candle parquet with a timestamp at or above holdout
    candle_dir = tmp_path / "candles" / "symbol=BTCUSDT" / "timeframe=5m"
    candle_dir.mkdir(parents=True)
    df_breach = pd.DataFrame({
        "open_time_ms": [PROSPECTIVE_HOLDOUT_START_MS + 1000],
        "open": [50000.0],
        "high": [50100.0],
        "low": [49900.0],
        "close": [50050.0],
    })
    df_breach.to_parquet(candle_dir / "breach.parquet")

    with pytest.raises(ValueError, match="PROSPECTIVE HOLDOUT BREACH"):
        engine.load_candles("BTCUSDT")


def test_double_touch_sl_priority():
    """Verify conservative collision resolution: SL prioritized when both TP and SL are hit intrabar."""
    engine = Phase562Engine()

    cfg = StrategyConfig(
        symbol="TESTUSDT",
        vol_floor_bps=0.0,
        vol_quantile=0.0,
        prob_margin=0.20,
        tp_multiplier=2.5,
        sl_multiplier=1.0,
        horizon_bars=24,
    )

    # Synthetic candles:
    # Bar 0-19: quiet history for rolling 20 vol
    # Bar 20: trigger signal
    # Bar 21: Entry at 100.0, high spikes to 105 (TP=102.5) AND low drops to 98 (SL=99.0)
    # Provide 40 candles so rolling 20 is fully warm before signal
    n_bars = 40
    timestamps = [1000 + i * 300_000 for i in range(n_bars)]
    opens = [100.0] * n_bars
    highs = [100.5] * n_bars
    lows = [99.5] * n_bars
    closes = [100.0 if (i % 2 == 0) else 102.0 for i in range(n_bars)]

    # Signal at bar 25 close (timestamps[25]), entry at bar 26 open
    # Give bar 27 extreme intrabar high and low to test double-touch collision
    highs[27] = 120.0  # triggers TP
    lows[27] = 80.0    # triggers SL

    df_c = pd.DataFrame({
        "open_time_ms": timestamps,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
    })

    # OOF signal at bar 25 close (open_time_ms=timestamps[25])
    df_oof = pd.DataFrame([{
        "fold": 1,
        "open_time_ms": timestamps[25],
        "true_label": 1,
        "predicted_class": 1,
        "raw_prob_m1": 0.10,
        "raw_prob_0": 0.20,
        "raw_prob_p1": 0.70,  # margin = 0.70 - 0.20 = 0.50 >= 0.20
    }])

    trades = engine.simulate_specialist(cfg, df_candles=df_c, df_oof=df_oof)
    assert len(trades) == 1
    # SL must be chosen conservatively over TP
    assert trades[0].exit_reason == "STOP_LOSS"
    assert trades[0].exit_price < trades[0].entry_price
    assert trades[0].gross_return_bps < 0.0


def test_limit_order_timeout():
    """Verify pending limit orders that never touch fill price are canceled after 3 bars."""
    engine = Phase562Engine()

    cfg = StrategyConfig(
        symbol="TESTUSDT",
        vol_floor_bps=100.0,
        prob_margin=0.20,
        delta_limit_offset=0.25,  # limit order at discount
        order_timeout_bars=3,
    )

    timestamps = [1000 + i * 300_000 for i in range(30)]
    # Flat market: low never reaches discounted limit price
    opens = [100.0] * 30
    highs = [100.0] * 30
    lows = [100.0] * 30
    closes = [100.0] * 30

    df_c = pd.DataFrame({
        "open_time_ms": timestamps,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
    })

    df_oof = pd.DataFrame([{
        "fold": 1,
        "open_time_ms": timestamps[19],
        "true_label": 1,
        "predicted_class": 1,
        "raw_prob_m1": 0.10,
        "raw_prob_0": 0.20,
        "raw_prob_p1": 0.70,
    }])

    trades = engine.simulate_specialist(cfg, df_candles=df_c, df_oof=df_oof)
    # Order never filled, expired after 3 bars -> 0 completed trades
    assert len(trades) == 0


def test_portfolio_exposure_cap_and_metrics():
    """Verify DEC_05 Option 3: gross exposure cap <= 30%, single-asset <= 10%, mark-to-market daily returns."""
    engine = Phase562Engine()

    # Generate 5 overlapping trades across different symbols
    trades = []
    base_t = 1_000_000_000  # millisecond timestamp
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "AVAXUSDT", "LINKUSDT"]

    for idx, s in enumerate(symbols):
        trades.append(
            CompletedTrade(
                symbol=s,
                side="LONG",
                entry_time_ms=base_t + 10_000,
                exit_time_ms=base_t + 500_000,
                entry_price=100.0,
                exit_price=102.0,  # +200 bps gross
                exit_reason="TAKE_PROFIT",
                bars_held=12,
                volatility_sigma=0.01,  # 100 bps sigma -> target notional = 0.005 / 0.01 = 50% equity -> capped at 10%
                gross_return_bps=200.0,
                fold=1,
            )
        )

    # Initial equity $10,000.
    # Each trade demands 10% ($1,000). Total capacity is 30% ($3,000).
    # Thus, only 3 trades can enter concurrently (or 3 trades sum to $3,000 capacity).
    res = engine.simulate_multi_asset_portfolio(
        trades,
        cost=COST_TIER_MAKER_PASSIVE,
        initial_equity=10_000.0,
        gross_exposure_cap=0.30,
        single_asset_cap=0.10,
    )

    assert res["total_portfolio_trades"] == 3
    assert res["execution_fill_rate_pct"] == 60.0  # 3 out of 5 trades entered
    assert res["ending_equity_usdt"] > 10_000.0
    assert res["max_drawdown_pct"] >= 0.0
    assert res["mean_underwater_drawdown_pct"] >= 0.0


def test_directional_filtering():
    """Verify that LONG_ONLY only takes long positions and SHORT_ONLY only takes shorts."""
    engine = Phase562Engine()

    n_bars = 40
    timestamps = [1000 + i * 300_000 for i in range(n_bars)]
    opens = [100.0] * n_bars
    highs = [100.5] * n_bars
    lows = [99.5] * n_bars
    closes = [100.0 if (i % 2 == 0) else 102.0 for i in range(n_bars)]

    df_c = pd.DataFrame({
        "open_time_ms": timestamps,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
    })

    # OOF has two signals: bar 24 produces short (raw_prob_m1 > raw_prob_p1), bar 28 produces long
    df_oof = pd.DataFrame([
        {
            "fold": 1,
            "open_time_ms": timestamps[23],
            "true_label": -1,
            "predicted_class": -1,
            "raw_prob_m1": 0.70,
            "raw_prob_0": 0.20,
            "raw_prob_p1": 0.10,
        },
        {
            "fold": 1,
            "open_time_ms": timestamps[27],
            "true_label": 1,
            "predicted_class": 1,
            "raw_prob_m1": 0.10,
            "raw_prob_0": 0.20,
            "raw_prob_p1": 0.70,
        },
    ])

    cfg_long = StrategyConfig(
        symbol="TESTUSDT",
        vol_floor_bps=0.0,
        vol_quantile=0.0,
        prob_margin=0.20,
        direction_filter="LONG_ONLY",
        horizon_bars=2,
    )
    trades_long = engine.simulate_specialist(cfg_long, df_candles=df_c, df_oof=df_oof)
    assert all(t.side == "LONG" for t in trades_long)

    cfg_short = StrategyConfig(
        symbol="TESTUSDT",
        vol_floor_bps=0.0,
        vol_quantile=0.0,
        prob_margin=0.20,
        direction_filter="SHORT_ONLY",
        horizon_bars=2,
    )
    trades_short = engine.simulate_specialist(cfg_short, df_candles=df_c, df_oof=df_oof)
    assert all(t.side == "SHORT" for t in trades_short)


def test_evaluate_trade_series_metrics():
    """Verify single-asset evaluation calculates win rates and expectancy correctly."""
    engine = Phase562Engine()

    trades = [
        CompletedTrade(
            symbol="TESTUSDT",
            side="LONG",
            entry_time_ms=1000,
            exit_time_ms=2000,
            entry_price=100.0,
            exit_price=102.5,  # +250 bps gross
            exit_reason="TAKE_PROFIT",
            bars_held=5,
            volatility_sigma=0.01,
            gross_return_bps=250.0,
            funding_events_count=1,
        ),
        CompletedTrade(
            symbol="TESTUSDT",
            side="SHORT",
            entry_time_ms=3000,
            exit_time_ms=4000,
            entry_price=100.0,
            exit_price=101.0,  # -100 bps gross
            exit_reason="STOP_LOSS",
            bars_held=3,
            volatility_sigma=0.01,
            gross_return_bps=-100.0,
            funding_events_count=0,
        ),
    ]

    # Evaluate under Maker-Passive: 8 bps friction + 1 bps funding on trade 1
    # Trade 1 net: 250 - 8 - 1 = 241 bps
    # Trade 2 net: -100 - 8 - 0 = -108 bps
    # Mean gross: (250 - 100) / 2 = 75 bps
    # Mean net: (241 - 108) / 2 = 66.5 bps
    m = engine.evaluate_trade_series(trades, cost=COST_TIER_MAKER_PASSIVE)
    assert m["trade_count"] == 2
    assert m["tp_count"] == 1
    assert m["sl_count"] == 1
    assert m["gross_win_rate_pct"] == 50.0
    assert m["gross_expectancy_bps"] == 75.0
    assert m["net_expectancy_bps"] == 66.5
    assert m["profit_factor"] == pytest.approx(241.0 / 108.0, rel=1e-2)
