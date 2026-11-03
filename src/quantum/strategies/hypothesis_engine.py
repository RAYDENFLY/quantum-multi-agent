"""Structured Hypothesis Registry & Backtesting Evaluation Engine for Milestone 5.11.

Formalizes and evaluates six distinct market hypotheses:
- HYP-01: Liquidity Sweep and Reclaim
- HYP-02: Volatility Expansion Breakout
- HYP-03: Momentum Continuation
- HYP-04: Failed Breakout Reversal
- HYP-05: Range Mean Reversion
- HYP-06: Cross-Asset Relative Strength

Alongside four benchmark baselines:
- BASE-01: Always Flat
- BASE-02: Buy and Hold
- BASE-03: Simple Momentum (EMA 9/21)
- BASE-04: Simple Mean Reversion (Bollinger Band Counter-Trend)
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from quantum.backtesting.accounting import compute_two_legged_pnl
from quantum.domain.enums import TradeSide


class HypothesisSpecification(BaseModel):
    """Rigorous metadata schema for QUANTUM alpha research hypotheses."""
    model_config = ConfigDict(frozen=True)

    hypothesis_id: str
    hypothesis_name: str
    market_mechanism: str
    observable_evidence: str
    required_features: List[str]
    entry_conditions: str
    exit_conditions: str
    invalidation_conditions: str
    expected_holding_period: str
    expected_trade_frequency: str
    expected_market_regime: str
    cost_assumptions: str
    risk_assumptions: str
    validation_protocol: str
    known_limitations: str


# ==============================================================================
# AUTHORITATIVE HYPOTHESIS REGISTRY
# ==============================================================================

HYPOTHESIS_REGISTRY: Dict[str, HypothesisSpecification] = {
    "HYP-01": HypothesisSpecification(
        hypothesis_id="HYP-01",
        hypothesis_name="Liquidity Sweep and Reclaim",
        market_mechanism=(
            "Cluster of retail stop-losses beyond confirmed swing extrema provide liquidity for "
            "institutional absorption. Once stops are swept, lack of opposing limit orders allows "
            "aggressive displacement back into the prior range."
        ),
        observable_evidence=(
            "Price pierces confirmed swing high (BSL) or swing low (SSL) intra-bar, but closes back "
            "inside the range with abnormal volume (RVOL > 1.5) and solid body displacement (>70% body)."
        ),
        required_features=["swing_high", "swing_low", "bsl_sweep_reclaim", "ssl_sweep_reclaim", "rvol_20", "atr_14"],
        entry_conditions="Long on SSL sweep + reclaim + bullish displacement; Short on BSL sweep + reclaim + bearish displacement.",
        exit_conditions="Take profit at 2.0x ATR or opposing swing level; Stop loss at swept extreme plus 0.5x ATR; Max hold 48 bars (4h).",
        invalidation_conditions="Immediate bar close beyond the swept extreme invalidates the absorption premise.",
        expected_holding_period="30 minutes to 3 hours (6 to 36 bars).",
        expected_trade_frequency="2 to 8 completed trade episodes per day across 10 assets.",
        expected_market_regime="HV_RANGE or regime transition from range to trend.",
        cost_assumptions="AsterDEX Base Retail: Taker entry (13 bps friction), Taker/Maker exit (8-13 bps friction).",
        risk_assumptions="1.0x unlevered gross exposure max, 25% max position allocation.",
        validation_protocol="Chronological train/validation split, purged cross-validation, bootstrap CI on net expectancy.",
        known_limitations="High-momentum runaway breakout trends blow through swing levels without reclaiming, causing stop-outs.",
    ),
    "HYP-02": HypothesisSpecification(
        hypothesis_id="HYP-02",
        hypothesis_name="Volatility Expansion Breakout",
        market_mechanism=(
            "Compression regimes store directional energy as order books thin out. A breakout accompanied "
            "by surging volume and volatility expansion represents fresh institutional participation."
        ),
        observable_evidence=(
            "Price closes outside 20-bar Donchian channel while Volatility Cycle is EXPANSION "
            "(ATR percentile > 70%), ADX > 25, and RVOL > 1.8."
        ),
        required_features=["donchian_high_20", "donchian_low_20", "atr_percentile_100", "rvol_20", "adx_14"],
        entry_conditions="Long on Donchian High break with expansion + RVOL > 1.8; Short on Donchian Low break with expansion.",
        exit_conditions="Trailing stop at 21 EMA or opposite Donchian band; Max hold 48 bars.",
        invalidation_conditions="Close back inside Donchian midpoint indicates a false breakout.",
        expected_holding_period="1 hour to 4 hours (12 to 48 bars).",
        expected_trade_frequency="1 to 5 completed trade episodes per day across portfolio.",
        expected_market_regime="HV_TREND (High-Volatility Trending).",
        cost_assumptions="AsterDEX Base Retail taker fee + 2 bps slippage on aggressive breakout entry.",
        risk_assumptions="Strict 1.0x unlevered portfolio cap.",
        validation_protocol="Purged temporal split with 24-bar embargo; Deflated Sharpe Ratio calculation.",
        known_limitations="Prone to severe whipsaws during choppy range regimes (false breakouts).",
    ),
    "HYP-03": HypothesisSpecification(
        hypothesis_id="HYP-03",
        hypothesis_name="Momentum Continuation",
        market_mechanism=(
            "Established multi-timeframe trends exhibit directional autocorrelation. Minor counter-trend "
            "pullbacks to dynamic moving averages offer favorable risk/reward continuation entries."
        ),
        observable_evidence=(
            "EMAs (9, 21, 50, 200) stacked in bullish/bearish alignment, ADX > 25, price pulls back to "
            "EMA 21 zone, and RSI rebounds from 40-50 zone (for longs) with positive ROC acceleration."
        ),
        required_features=["ema_alignment_score", "ema_21", "adx_14", "rsi_14", "momentum_acceleration"],
        entry_conditions="Long when trend alignment == +1.0, ADX > 25, Low touches EMA 21, Close > EMA 21, RSI > 45; Inverse for short.",
        exit_conditions="Take profit at 1.5x ATR; Stop loss at 1.0x ATR below EMA 21; Max hold 48 bars.",
        invalidation_conditions="Close below EMA 50 signals trend breakdown and terminates trade.",
        expected_holding_period="45 minutes to 3 hours (9 to 36 bars).",
        expected_trade_frequency="5 to 15 completed trade episodes per day across 10 assets.",
        expected_market_regime="HV_TREND or LV_TREND.",
        cost_assumptions="AsterDEX Base Retail: Limit maker entry on pullback (5.5 bps friction), taker exit on SL/TP.",
        risk_assumptions="Max 1.0x unlevered exposure.",
        validation_protocol="Walk-forward analysis with 1,000 bootstrap resamples on net expectancy.",
        known_limitations="Degrades rapidly when broad market enters prolonged consolidation or mean-reverting chop.",
    ),
    "HYP-04": HypothesisSpecification(
        hypothesis_id="HYP-04",
        hypothesis_name="Failed Breakout Reversal",
        market_mechanism=(
            "Breakouts that occur on drying volume or during range regimes fail due to lack of follow-through, "
            "trapping breakout traders and causing a sharp snap-back to the opposite range boundary."
        ),
        observable_evidence=(
            "Price pierces 20-bar Donchian band, but RVOL < 1.0, followed immediately (within 2 bars) by an "
            "opposite displacement candle and RSI divergence."
        ),
        required_features=["donchian_high_20", "donchian_low_20", "rvol_20", "market_regime", "rsi_14"],
        entry_conditions="Short when High breaks Donchian High, RVOL < 1.0, close falls back below within 2 bars; Long for Low break.",
        exit_conditions="Take profit at Donchian midline or 1.5x ATR; Stop loss at breakout extreme plus 0.5x ATR; Max hold 36 bars.",
        invalidation_conditions="Subsequent candle closing above the breakout candle high invalidates the trap.",
        expected_holding_period="30 minutes to 2 hours (6 to 24 bars).",
        expected_trade_frequency="3 to 10 completed trade episodes per day.",
        expected_market_regime="LV_RANGE or HV_RANGE.",
        cost_assumptions="AsterDEX Base Retail taker execution on structural rejection confirmation.",
        risk_assumptions="1.0x gross exposure hard cap.",
        validation_protocol="Regime-stratified cross-validation; Holm-Bonferroni correction.",
        known_limitations="Can incur severe losses if the breakout is genuine and launches a major macro trend.",
    ),
    "HYP-05": HypothesisSpecification(
        hypothesis_id="HYP-05",
        hypothesis_name="Range Mean Reversion",
        market_mechanism=(
            "In certified range-bound regimes with low directional efficiency, price behaves as an Ornstein-Uhlenbeck "
            "mean-reverting process around the local volume-weighted average price or moving average."
        ),
        observable_evidence=(
            "Market Regime is LV_RANGE (ADX < 20, Efficiency Ratio < 0.30), price touches or pierces outer Bollinger "
            "Band (2.0 std), and Stochastic oscillator shows extreme exhaustion (%K < 15 crossing above %D)."
        ),
        required_features=["market_regime", "efficiency_ratio_20", "bb_upper", "bb_lower", "stoch_k", "stoch_d"],
        entry_conditions="Long when Regime == LV_RANGE, Low <= bb_lower, Stoch %K < 20, %K crosses %D upward; Inverse for short.",
        exit_conditions="Take profit at Bollinger middle band (SMA 20); Stop loss at 1.0x ATR beyond band; Max hold 24 bars.",
        invalidation_conditions="Regime transition from range to trend immediately aborts the trade.",
        expected_holding_period="30 minutes to 2 hours (6 to 24 bars).",
        expected_trade_frequency="5 to 20 completed trade episodes per day.",
        expected_market_regime="LV_RANGE (Low-Volatility Range).",
        cost_assumptions="AsterDEX Base Retail: Passive limit order on band touch (maker 4 bps) + taker exit (10 bps).",
        risk_assumptions="1.0x unlevered portfolio cap.",
        validation_protocol="Permutation test and bootstrap confidence intervals on profit factor.",
        known_limitations="Catastrophic vulnerability to sudden volatility expansion and breakout trends.",
    ),
    "HYP-06": HypothesisSpecification(
        hypothesis_id="HYP-06",
        hypothesis_name="Cross-Asset Relative Strength",
        market_mechanism=(
            "Crypto capital flows sequentially between Bitcoin and high-beta altcoins. Assets demonstrating persistent "
            "relative strength against BTC during consolidations attract momentum flow when the market resumes."
        ),
        observable_evidence=(
            "Asset 1-hour return outperforms BTC 1-hour return by >= 1.0%, BTC trend is bullish/neutral, "
            "and market breadth >= 0.50."
        ),
        required_features=["rel_strength_vs_btc_1h", "btc_trend_bull", "market_breadth_bull_pct", "rsi_14"],
        entry_conditions="Long when rel_strength_vs_btc_1h >= +0.010 (+1.0%), btc_trend_bull == 1.0, market_breadth >= 0.50.",
        exit_conditions="Relative strength flips negative (< -0.005) or after 24 bars (2 hours); Stop loss at 1.5x ATR.",
        invalidation_conditions="BTC sudden sharp decline (> 1% 5m drop) triggers emergency risk exit.",
        expected_holding_period="1 hour to 3 hours (12 to 36 bars).",
        expected_trade_frequency="2 to 6 completed trade episodes per day.",
        expected_market_regime="Broad market bull or altcoin rotation regime.",
        cost_assumptions="AsterDEX Base Retail: Taker entry (13 bps), Taker exit (13 bps).",
        risk_assumptions="1.0x unlevered portfolio cap; 25% max symbol allocation.",
        validation_protocol="Cross-sectional multi-asset validation; deflated Sharpe Ratio.",
        known_limitations="Beta divergence can collapse instantly during Bitcoin liquidity panics or flash crashes.",
    ),
}


# ==============================================================================
# DETERMINISTIC SIGNAL GENERATION & BACKTEST ENGINE
# ==============================================================================

class TradeRecord(BaseModel):
    """Normalized completed trade episode execution record."""
    model_config = ConfigDict(frozen=True)

    hypothesis_id: str
    symbol: str
    side: str
    entry_bar: int
    exit_bar: int
    entry_time_ms: int
    exit_time_ms: int
    duration_minutes: float
    entry_price: float
    exit_price: float
    notional_usd: float
    gross_pnl_usd: float
    gross_return_bps: float
    fee_usd: float
    slippage_usd: float
    funding_usd: float
    net_pnl_usd: float
    net_return_bps: float
    exit_reason: str
    market_regime: str


def backtest_single_hypothesis(
    df: pd.DataFrame,
    hypothesis_id: str,
    symbol: str = "BTCUSDT",
    capital_usd: float = 100.0,
    taker_fee_bps: float = 10.0,
    maker_fee_bps: float = 4.0,
    slippage_bps: float = 2.0,
    spread_bps_half: float = 1.0,
) -> List[TradeRecord]:
    """Causally backtests a single hypothesis on a single asset dataframe with causal next-bar execution."""
    n = len(df)
    if n < 250:
        return []

    # Unpack series
    open_arr = df["open"].to_numpy()
    high_arr = df["high"].to_numpy()
    low_arr = df["low"].to_numpy()
    close_arr = df["close"].to_numpy()
    ts_arr = df["open_time_ms"].to_numpy()
    atr_arr = df["atr_14"].to_numpy() if "atr_14" in df.columns else np.full(n, 1.0)
    regimes = df["market_regime"].to_numpy() if "market_regime" in df.columns else np.full(n, "UNKNOWN")

    trades: List[TradeRecord] = []
    in_pos = False
    side = TradeSide.LONG
    entry_bar = 0
    entry_price = 0.0
    entry_ts = 0
    stop_price = 0.0
    target_price = 0.0
    entry_regime = "UNKNOWN"
    max_hold_bars = 48  # 4 hours max

    # 1. Generate Raw Causal Signals at bar t
    # Signal array: +1 for Long, -1 for Short, 0 for None
    signals = np.zeros(n, dtype=np.int32)

    if hypothesis_id == "HYP-01":
        # Liquidity Sweep & Reclaim
        ssl_swp = df["ssl_sweep_reclaim"].to_numpy()
        bsl_swp = df["bsl_sweep_reclaim"].to_numpy()
        b_disp = df["bullish_displacement"].to_numpy()
        br_disp = df["bearish_displacement"].to_numpy()
        rvol = df["rvol_20"].to_numpy()

        for t in range(50, n):
            if ssl_swp[t] == 1.0 and b_disp[t] == 1.0 and rvol[t] >= 1.2:
                signals[t] = 1
            elif bsl_swp[t] == 1.0 and br_disp[t] == 1.0 and rvol[t] >= 1.2:
                signals[t] = -1

    elif hypothesis_id == "HYP-02":
        # Volatility Expansion Breakout
        don_h = df["donchian_high_20"].to_numpy()
        don_l = df["donchian_low_20"].to_numpy()
        pctl = df["atr_percentile_100"].to_numpy()
        rvol = df["rvol_20"].to_numpy()
        adx = df["adx_14"].to_numpy()

        for t in range(50, n):
            if close_arr[t] > don_h[t] and pctl[t] >= 65.0 and rvol[t] >= 1.5 and adx[t] >= 22.0:
                signals[t] = 1
            elif close_arr[t] < don_l[t] and pctl[t] >= 65.0 and rvol[t] >= 1.5 and adx[t] >= 22.0:
                signals[t] = -1

    elif hypothesis_id == "HYP-03":
        # Momentum Continuation
        align = df["ema_alignment_score"].to_numpy()
        ema21 = df["ema_21"].to_numpy()
        adx = df["adx_14"].to_numpy()
        rsi = df["rsi_14"].to_numpy()
        accel = df["momentum_acceleration"].to_numpy()

        for t in range(50, n):
            if align[t] == 1.0 and adx[t] >= 22.0 and low_arr[t] <= ema21[t] * 1.002 and close_arr[t] >= ema21[t] and rsi[t] >= 42.0 and accel[t] > 0:
                signals[t] = 1
            elif align[t] == -1.0 and adx[t] >= 22.0 and high_arr[t] >= ema21[t] * 0.998 and close_arr[t] <= ema21[t] and rsi[t] <= 58.0 and accel[t] < 0:
                signals[t] = -1

    elif hypothesis_id == "HYP-04":
        # Failed Breakout Reversal
        don_h = df["donchian_high_20"].to_numpy()
        don_l = df["donchian_low_20"].to_numpy()
        rvol = df["rvol_20"].to_numpy()

        for t in range(50, n - 2):
            # Failed low break: Low broke don_l, but close finished back above on low volume, next bar reverses up
            if low_arr[t] < don_l[t] and close_arr[t] > don_l[t] and rvol[t] < 1.1 and close_arr[t] > open_arr[t]:
                signals[t] = 1
            elif high_arr[t] > don_h[t] and close_arr[t] < don_h[t] and rvol[t] < 1.1 and close_arr[t] < open_arr[t]:
                signals[t] = -1

    elif hypothesis_id == "HYP-05":
        # Range Mean Reversion
        adx = df["adx_14"].to_numpy()
        er = df["efficiency_ratio_20"].to_numpy()
        bb_low = df["bb_lower"].to_numpy()
        bb_up = df["bb_upper"].to_numpy()
        stoch_k = df["stoch_k"].to_numpy()
        stoch_d = df["stoch_d"].to_numpy()

        for t in range(50, n):
            is_range = (adx[t] < 22.0) or (er[t] < 0.35)
            if is_range:
                if low_arr[t] <= bb_low[t] and stoch_k[t] < 25.0 and stoch_k[t] > stoch_d[t]:
                    signals[t] = 1
                elif high_arr[t] >= bb_up[t] and stoch_k[t] > 75.0 and stoch_k[t] < stoch_d[t]:
                    signals[t] = -1

    elif hypothesis_id == "HYP-06":
        # Cross-Asset Relative Strength
        if "rel_strength_vs_btc_1h" in df.columns:
            rel_str = df["rel_strength_vs_btc_1h"].to_numpy()
            btc_bull = df["btc_trend_bull"].to_numpy()
            breadth = df["market_breadth_bull_pct"].to_numpy()

            for t in range(50, n):
                if rel_str[t] >= 0.008 and btc_bull[t] == 1.0 and breadth[t] >= 0.45:
                    signals[t] = 1
                elif rel_str[t] <= -0.008 and btc_bull[t] == 0.0 and breadth[t] <= 0.55:
                    signals[t] = -1

    elif hypothesis_id == "BASE-03":
        # Simple Momentum (EMA 9 / 21 Crossover)
        ema9 = df["ema_9"].to_numpy()
        ema21 = df["ema_21"].to_numpy()
        for t in range(50, n):
            if ema9[t - 1] <= ema21[t - 1] and ema9[t] > ema21[t]:
                signals[t] = 1
            elif ema9[t - 1] >= ema21[t - 1] and ema9[t] < ema21[t]:
                signals[t] = -1

    elif hypothesis_id == "BASE-04":
        # Simple Mean Reversion (Bollinger Band Counter-Trend)
        bb_low = df["bb_lower"].to_numpy()
        bb_up = df["bb_upper"].to_numpy()
        for t in range(50, n):
            if close_arr[t] < bb_low[t]:
                signals[t] = 1
            elif close_arr[t] > bb_up[t]:
                signals[t] = -1

    # 2. Simulate Causal Execution at Next Bar Open (t + 1)
    for t in range(50, n - 1):
        cur_open = open_arr[t]
        cur_high = high_arr[t]
        cur_low = low_arr[t]
        cur_close = close_arr[t]
        cur_ts = int(ts_arr[t])

        # A. Check Exit for Open Position
        if in_pos:
            bars_held = t - entry_bar
            exit_price = 0.0
            exit_reason = ""

            # Check stop loss hit
            if side == TradeSide.LONG and cur_low <= stop_price:
                exit_price = stop_price
                exit_reason = "STOP_LOSS"
            elif side == TradeSide.SHORT and cur_high >= stop_price:
                exit_price = stop_price
                exit_reason = "STOP_LOSS"
            # Check take profit hit
            elif side == TradeSide.LONG and cur_high >= target_price:
                exit_price = target_price
                exit_reason = "TAKE_PROFIT"
            elif side == TradeSide.SHORT and cur_low <= target_price:
                exit_price = target_price
                exit_reason = "TAKE_PROFIT"
            # Check max holding duration (48 bars = 4 hours)
            elif bars_held >= max_hold_bars:
                exit_price = cur_close
                exit_reason = "HORIZON_TIMEOUT"
            # Check opposing signal
            elif (side == TradeSide.LONG and signals[t] == -1) or (side == TradeSide.SHORT and signals[t] == 1):
                exit_price = cur_close
                exit_reason = "SIGNAL_REVERSAL"

            if exit_price > 0.0:
                # Compute exact financial accounting
                acc = compute_two_legged_pnl(
                    side=side,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    quantity=capital_usd / entry_price,
                    fee_rate_bps=taker_fee_bps,
                    slippage_bps=slippage_bps + spread_bps_half,
                    leverage=1.0,
                )

                trades.append(
                    TradeRecord(
                        hypothesis_id=hypothesis_id,
                        symbol=symbol,
                        side=side.name,
                        entry_bar=entry_bar,
                        exit_bar=t,
                        entry_time_ms=entry_ts,
                        exit_time_ms=cur_ts,
                        duration_minutes=float(bars_held * 5),
                        entry_price=round(entry_price, 4),
                        exit_price=round(exit_price, 4),
                        notional_usd=round(capital_usd, 2),
                        gross_pnl_usd=round(acc.gross_pnl_usdt, 4),
                        gross_return_bps=round(acc.gross_return_bps, 2),
                        fee_usd=round(acc.total_fees_usdt, 4),
                        slippage_usd=round(acc.total_slippage_usdt, 4),
                        funding_usd=0.0,
                        net_pnl_usd=round(acc.net_pnl_usdt, 4),
                        net_return_bps=round(acc.net_return_bps, 2),
                        exit_reason=exit_reason,
                        market_regime=str(entry_regime),
                    )
                )
                in_pos = False

        # B. Check Entry for Next Bar Open (Causal Execution)
        if not in_pos and t < n - 1:
            sig = signals[t]
            if sig != 0:
                # Next bar open price
                next_open = open_arr[t + 1]
                cur_atr = atr_arr[t] if not np.isnan(atr_arr[t]) and atr_arr[t] > 0 else (next_open * 0.005)

                in_pos = True
                side = TradeSide.LONG if sig == 1 else TradeSide.SHORT
                entry_bar = t + 1
                entry_price = next_open
                entry_ts = int(ts_arr[t + 1])
                entry_regime = regimes[t]

                if side == TradeSide.LONG:
                    stop_price = entry_price - (1.5 * cur_atr)
                    target_price = entry_price + (2.0 * cur_atr)
                else:
                    stop_price = entry_price + (1.5 * cur_atr)
                    target_price = entry_price - (2.0 * cur_atr)

    return trades
