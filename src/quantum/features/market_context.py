"""Multi-Factor Market Context Engine with Strict Causal Boundaries.

Vectorized, deterministic implementation across six research dimensions:
1. Dimension A: Market Structure (Causal Swings, BOS, CHoCH, Liquidity Sweeps, FVGs, Displacement).
2. Dimension B: Momentum and Trend (ADX, Momentum Acceleration, EMA Alignment, Trend Persistence).
3. Dimension C: Volatility and Market Regime (Kaufman Efficiency Ratio, Volatility Percentile, 4-State Regime).
4. Dimension D: Volume and Liquidity Proxies (RVOL, Volume Z-Score, Amihud Illiquidity, Effort vs Result).
5. Dimension E: Cross-Asset Context (BTC Influence, ETH/BTC Strength, Rolling Correlation, Market Breadth).
6. Dimension F: Event & Exogenous Context (Pluggable interface; DATA_UNAVAILABLE for historical backtesting).

Strict Causal Invariant:
No future candles, lookahead confirmations, or same-bar executions are permitted.
Swing levels confirmed at t - k are only emitted at bar t.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from quantum.core.logging import get_logger
from quantum.features.indicators import (
    compute_atr,
    compute_bollinger_bands,
    compute_donchian_channels,
    compute_ema,
    compute_rsi,
    compute_stochastic,
)

logger = get_logger("features.market_context")


class MarketRegimeState(str, Enum):
    """Discrete 4-state market regime classification."""
    HV_TREND = "HV_TREND"    # High-Volatility Trending
    LV_TREND = "LV_TREND"    # Low-Volatility Trending
    HV_RANGE = "HV_RANGE"    # High-Volatility Range / Choppy
    LV_RANGE = "LV_RANGE"    # Low-Volatility Range / Quiet Consolidation


class VolatilityCycleState(str, Enum):
    """Volatility expansion/contraction cycle states."""
    EXPANSION = "EXPANSION"
    CONTRACTION = "CONTRACTION"
    NEUTRAL = "NEUTRAL"


# ==============================================================================
# DIMENSION A: MARKET STRUCTURE
# ==============================================================================

def compute_causal_swings(
    high: np.ndarray,
    low: np.ndarray,
    lookback: int = 5,
    lookforward: int = 5,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Causally detect swing highs and swing lows using vectorized rolling extrema.
    
    A peak occurs at bar i if high[i] is the maximum in [i - lookback, i + lookforward].
    CAUSAL INVARIANT:
    The peak at bar i can ONLY be confirmed and known at bar i + lookforward.
    Therefore, the confirmed swing level emitted at bar t is the peak from t - lookforward.
    Zero future information is accessible at bar t.
    """
    n = len(high)
    s_h = pd.Series(high)
    s_l = pd.Series(low)
    win = lookback + lookforward + 1

    # Centered maximum at bar i
    roll_max = s_h.rolling(window=win, min_periods=win).max().shift(-lookforward)
    roll_min = s_l.rolling(window=win, min_periods=win).min().shift(-lookforward)

    is_sh = (s_h == roll_max)
    is_sl = (s_l == roll_min)

    # Shift by lookforward so the confirmed level only appears at bar t = i + lookforward
    confirmed_sh = pd.Series(np.where(is_sh, high, np.nan)).shift(lookforward).ffill().to_numpy()
    confirmed_sl = pd.Series(np.where(is_sl, low, np.nan)).shift(lookforward).ffill().to_numpy()

    # Track bars since confirmed swing
    sh_indices = np.where(is_sh)[0]
    sl_indices = np.where(is_sl)[0]

    bars_since_sh = np.full(n, np.nan, dtype=np.float64)
    bars_since_sl = np.full(n, np.nan, dtype=np.float64)

    # Calculate bars since last confirmed swing efficiently
    last_sh_idx = -1
    last_sl_idx = -1
    sh_set = set(sh_indices + lookforward)
    sl_set = set(sl_indices + lookforward)

    for t in range(lookback + lookforward, n):
        cand = t - lookforward
        if cand in sh_indices:
            last_sh_idx = cand
        if cand in sl_indices:
            last_sl_idx = cand
        if last_sh_idx >= 0:
            bars_since_sh[t] = float(t - last_sh_idx)
        if last_sl_idx >= 0:
            bars_since_sl[t] = float(t - last_sl_idx)

    return confirmed_sh, confirmed_sl, bars_since_sh, bars_since_sl


def compute_fair_value_gaps(
    high: np.ndarray,
    low: np.ndarray,
    atr: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute 3-bar Fair Value Gaps (FVG) and normalized gap magnitudes causally.
    
    Bullish FVG at bar t: low[t] > high[t-2]. Gap = low[t] - high[t-2].
    Bearish FVG at bar t: high[t] < low[t-2]. Gap = low[t-2] - high[t].
    """
    n = len(high)
    s_h = pd.Series(high)
    s_l = pd.Series(low)
    s_atr = pd.Series(atr) + 1e-12

    h_prev2 = s_h.shift(2)
    l_prev2 = s_l.shift(2)

    bull_cond = (s_l > h_prev2)
    bear_cond = (s_h < l_prev2)

    bullish_fvg = np.where(bull_cond, 1.0, 0.0)
    bearish_fvg = np.where(bear_cond, 1.0, 0.0)

    fvg_magnitude = np.zeros(n, dtype=np.float64)
    bull_mag = (s_l - h_prev2) / s_atr
    bear_mag = (l_prev2 - s_h) / s_atr

    fvg_magnitude = np.where(bull_cond, bull_mag, np.where(bear_cond, -bear_mag, 0.0))
    bullish_fvg[:2] = 0.0
    bearish_fvg[:2] = 0.0
    fvg_magnitude[:2] = 0.0

    return bullish_fvg, bearish_fvg, fvg_magnitude


def compute_displacement_and_sweeps(
    open_p: np.ndarray,
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    atr: np.ndarray,
    swing_high: np.ndarray,
    swing_low: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute displacement candles and liquidity sweeps of confirmed swing levels."""
    s_c = pd.Series(close)
    prev_c = s_c.shift(1).to_numpy()

    tr = np.maximum(high - low, np.maximum(np.abs(high - prev_c), np.abs(low - prev_c)))
    body = np.abs(close - open_p)
    span = high - low + 1e-12
    cur_atr = np.where(np.isnan(atr), span, atr)

    is_large_range = tr >= 1.35 * cur_atr
    is_solid_body = (body / span) >= 0.68

    bullish_displacement = np.where(is_large_range & is_solid_body & (close > open_p), 1.0, 0.0)
    bearish_displacement = np.where(is_large_range & is_solid_body & (close < open_p), 1.0, 0.0)

    # Liquidity Sweeps
    prev_sh = pd.Series(swing_high).shift(1).to_numpy()
    prev_sl = pd.Series(swing_low).shift(1).to_numpy()

    bsl_sweep = np.where(~np.isnan(prev_sh) & (high > prev_sh) & (close < prev_sh), 1.0, 0.0)
    ssl_sweep = np.where(~np.isnan(prev_sl) & (low < prev_sl) & (close > prev_sl), 1.0, 0.0)

    bullish_displacement[0] = 0.0
    bearish_displacement[0] = 0.0
    bsl_sweep[0] = 0.0
    ssl_sweep[0] = 0.0

    return bullish_displacement, bearish_displacement, bsl_sweep, ssl_sweep


# ==============================================================================
# DIMENSION B: MOMENTUM AND TREND
# ==============================================================================

def compute_adx(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    period: int = 14,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute Average Directional Index (ADX), +DI, and -DI causally."""
    n = len(close)
    adx = np.full(n, np.nan, dtype=np.float64)
    plus_di = np.full(n, np.nan, dtype=np.float64)
    minus_di = np.full(n, np.nan, dtype=np.float64)

    if n <= period * 2:
        return adx, plus_di, minus_di

    plus_dm = np.zeros(n, dtype=np.float64)
    minus_dm = np.zeros(n, dtype=np.float64)
    tr = np.zeros(n, dtype=np.float64)

    tr[0] = high[0] - low[0]
    for i in range(1, n):
        up = high[i] - high[i - 1]
        down = low[i - 1] - low[i]
        if up > down and up > 0:
            plus_dm[i] = up
        if down > up and down > 0:
            minus_dm[i] = down
        tr[i] = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))

    tr_smooth = np.zeros(n, dtype=np.float64)
    plus_smooth = np.zeros(n, dtype=np.float64)
    minus_smooth = np.zeros(n, dtype=np.float64)

    tr_smooth[period] = np.sum(tr[1 : period + 1])
    plus_smooth[period] = np.sum(plus_dm[1 : period + 1])
    minus_smooth[period] = np.sum(minus_dm[1 : period + 1])

    alpha = 1.0 / period
    for i in range(period + 1, n):
        tr_smooth[i] = tr_smooth[i - 1] - (tr_smooth[i - 1] * alpha) + tr[i]
        plus_smooth[i] = plus_smooth[i - 1] - (plus_smooth[i - 1] * alpha) + plus_dm[i]
        minus_smooth[i] = minus_smooth[i - 1] - (minus_smooth[i - 1] * alpha) + minus_dm[i]

    eps = 1e-12
    dx = np.zeros(n, dtype=np.float64)
    for i in range(period, n):
        p_di = (plus_smooth[i] / (tr_smooth[i] + eps)) * 100.0
        m_di = (minus_smooth[i] / (tr_smooth[i] + eps)) * 100.0
        plus_di[i] = p_di
        minus_di[i] = m_di
        di_sum = p_di + m_di
        dx[i] = (abs(p_di - m_di) / (di_sum + eps)) * 100.0

    start_adx = 2 * period
    if n > start_adx:
        adx[start_adx - 1] = np.mean(dx[period:start_adx])
        curr_adx = adx[start_adx - 1]
        for i in range(start_adx, n):
            curr_adx = ((curr_adx * (period - 1)) + dx[i]) * alpha
            adx[i] = curr_adx

    return adx, plus_di, minus_di


def compute_momentum_acceleration(close: np.ndarray, period: int = 10) -> Tuple[np.ndarray, np.ndarray]:
    """Compute Rate of Change (ROC) and second-derivative momentum acceleration."""
    s_c = pd.Series(close)
    prev = s_c.shift(period)
    roc = (s_c - prev) / (prev + 1e-12)

    roc_prev = roc.shift(3)
    acceleration = roc - roc_prev

    return roc.to_numpy(), acceleration.to_numpy()


def compute_trend_persistence(close: np.ndarray, ema_21: np.ndarray) -> np.ndarray:
    """Compute consecutive bars price has held strictly above (+N) or below (-N) EMA 21."""
    n = len(close)
    persistence = np.zeros(n, dtype=np.float64)
    count = 0.0

    for i in range(n):
        if np.isnan(ema_21[i]):
            persistence[i] = np.nan
            continue
        if close[i] > ema_21[i]:
            count = count + 1.0 if count >= 0 else 1.0
        elif close[i] < ema_21[i]:
            count = count - 1.0 if count <= 0 else -1.0
        else:
            count = 0.0
        persistence[i] = count

    return persistence


# ==============================================================================
# DIMENSION C: VOLATILITY AND MARKET REGIME
# ==============================================================================

def compute_kaufman_efficiency_ratio(close: np.ndarray, period: int = 20) -> np.ndarray:
    """Compute Kaufman Efficiency Ratio (KER): |Close_t - Close_{t-n}| / Sum(|Close_i - Close_{i-1}|)."""
    s_c = pd.Series(close)
    net_change = (s_c - s_c.shift(period)).abs()
    single_step = (s_c - s_c.shift(1)).abs()
    sum_noise = single_step.rolling(window=period, min_periods=period).sum()
    ker = net_change / (sum_noise + 1e-12)
    return ker.to_numpy()


def compute_volatility_percentile(metric: np.ndarray, window: int = 100) -> np.ndarray:
    """Compute normalized rolling percentile rank of a volatility metric over past N bars (0.0 to 100.0)."""
    s = pd.Series(metric)
    roll_min = s.rolling(window=window, min_periods=max(20, int(window * 0.5))).min()
    roll_max = s.rolling(window=window, min_periods=max(20, int(window * 0.5))).max()
    pctl = (s - roll_min) / (roll_max - roll_min + 1e-12) * 100.0
    return pctl.clip(0.0, 100.0).to_numpy()


def classify_market_regime(
    adx: np.ndarray,
    atr_percentile: np.ndarray,
    efficiency_ratio: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Classifies market into 4 regime states and 3 volatility cycle states causally."""
    n = len(adx)
    regimes = np.full(n, "UNKNOWN", dtype=object)
    cycles = np.full(n, VolatilityCycleState.NEUTRAL.value, dtype=object)

    valid_mask = (~np.isnan(adx)) & (~np.isnan(atr_percentile)) & (~np.isnan(efficiency_ratio))
    is_trend = (adx >= 22.0) & (efficiency_ratio >= 0.32)
    is_high_vol = atr_percentile >= 50.0

    regimes[valid_mask & is_trend & is_high_vol] = MarketRegimeState.HV_TREND.value
    regimes[valid_mask & is_trend & (~is_high_vol)] = MarketRegimeState.LV_TREND.value
    regimes[valid_mask & (~is_trend) & is_high_vol] = MarketRegimeState.HV_RANGE.value
    regimes[valid_mask & (~is_trend) & (~is_high_vol)] = MarketRegimeState.LV_RANGE.value

    cycles[valid_mask & (atr_percentile >= 70.0)] = VolatilityCycleState.EXPANSION.value
    cycles[valid_mask & (atr_percentile <= 30.0)] = VolatilityCycleState.CONTRACTION.value

    return regimes, cycles


# ==============================================================================
# DIMENSION D: VOLUME AND LIQUIDITY PROXIES
# ==============================================================================

def compute_volume_proxies(
    high: np.ndarray,
    low: np.ndarray,
    open_p: np.ndarray,
    close: np.ndarray,
    volume: np.ndarray,
    atr: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute volume expansion, log volume Z-Score, Amihud illiquidity proxy, and effort vs result.
    
    IMPORTANT GOVERNANCE NOTE:
    These are OHLCV proxies. They do NOT reflect actual order-book depth, queue priority,
    or institutional order flow.
    """
    s_v = pd.Series(volume)
    vol_sma_20 = s_v.rolling(window=20, min_periods=20).mean()
    eps = 1e-12

    rvol = s_v / (vol_sma_20 + eps)

    log_v = np.log(s_v + 1.0)
    vol_mean = log_v.rolling(window=50, min_periods=20).mean()
    vol_std = log_v.rolling(window=50, min_periods=20).std(ddof=1)
    vol_zscore = (log_v - vol_mean) / (vol_std + eps)

    simple_ret = pd.Series(close).pct_change().abs()
    turnover = s_v * pd.Series(close)
    amihud = (simple_ret / (turnover + eps)) * 1_000_000.0

    candle_span = pd.Series(high - low)
    norm_result = candle_span / (pd.Series(atr) + eps)
    effort_result_ratio = norm_result / (rvol + eps)

    return rvol.to_numpy(), vol_zscore.to_numpy(), amihud.to_numpy(), effort_result_ratio.to_numpy()


# ==============================================================================
# DIMENSION E: CROSS-ASSET CONTEXT
# ==============================================================================

def compute_cross_asset_context(
    asset_panels: Dict[str, pd.DataFrame],
    btc_symbol: str = "BTCUSDT",
) -> Dict[str, pd.DataFrame]:
    """Compute cross-asset features: BTC momentum, ETH/BTC relative strength, rolling correlation, and market breadth.
    
    CAUSAL INVARIANT:
    All asset observations are synchronized strictly by open_time_ms.
    """
    if btc_symbol not in asset_panels:
        raise ValueError(f"BTC panel '{btc_symbol}' required for cross-asset context calculations.")

    btc_df = asset_panels[btc_symbol].sort_values("open_time_ms").copy()
    btc_c = btc_df["close"].to_numpy()
    btc_ema_50 = compute_ema(btc_c, 50)
    btc_ret_12 = pd.Series(btc_c).pct_change(12).to_numpy()  # 1-hour return (12 x 5m)
    btc_ret_5m = pd.Series(btc_c).pct_change(1).to_numpy()

    btc_context_df = pd.DataFrame({
        "open_time_ms": btc_df["open_time_ms"],
        "btc_ret_5m": btc_ret_5m,
        "btc_ret_1h": btc_ret_12,
        "btc_trend_bull": np.where(btc_c > btc_ema_50, 1.0, 0.0),
    }).set_index("open_time_ms")

    # Compute Market Breadth across all symbols
    symbol_emas = {}
    for sym, df_sym in asset_panels.items():
        s_df = df_sym.sort_values("open_time_ms").set_index("open_time_ms")
        if "close" in s_df.columns:
            ema50 = compute_ema(s_df["close"].to_numpy(), 50)
            symbol_emas[sym] = (s_df["close"] > ema50).astype(float)

    breadth_df = pd.DataFrame(symbol_emas)
    breadth_series = breadth_df.mean(axis=1)

    enriched_panels = {}
    for sym, df_sym in asset_panels.items():
        res_df = df_sym.sort_values("open_time_ms").copy()
        merged = res_df.join(btc_context_df, on="open_time_ms", how="left")
        merged["market_breadth_bull_pct"] = merged["open_time_ms"].map(breadth_series).fillna(0.5)

        s_c = merged["close"]
        asset_ret1h = s_c.pct_change(12).to_numpy()
        merged["asset_ret_1h"] = asset_ret1h
        merged["rel_strength_vs_btc_1h"] = asset_ret1h - merged["btc_ret_1h"].to_numpy()

        # Rolling 50-bar correlation to BTC
        ret_s = s_c.pct_change(1)
        b_ret_s = merged["btc_ret_5m"]
        merged["rolling_corr_btc_50"] = ret_s.rolling(window=50, min_periods=30).corr(b_ret_s).to_numpy()

        enriched_panels[sym] = merged

    return enriched_panels


# ==============================================================================
# DIMENSION F: EVENT AND EXOGENOUS CONTEXT (INTERFACE DESIGN)
# ==============================================================================

class ExogenousEventInterface:
    """Optional interface for macro announcements, funding payments, and liquidation feeds.
    
    CURRENT PLATFORM STATUS: DATA_UNAVAILABLE.
    Historical event feeds are not available in canonical OHLCV stores.
    This interface guarantees fail-safe handling without inventing historical records.
    """

    def __init__(self, is_live: bool = False) -> None:
        self.is_live = is_live
        self.status = "DATA_AVAILABLE" if is_live else "DATA_UNAVAILABLE"

    def get_event_context(self, timestamp_ms: int) -> Dict[str, Any]:
        """Returns structured event context or formal DATA_UNAVAILABLE envelope."""
        return {
            "timestamp_ms": timestamp_ms,
            "status": self.status,
            "open_interest_usd": None,
            "funding_rate_bps": None,
            "liquidation_long_usd": None,
            "liquidation_short_usd": None,
            "macro_event_active": False,
            "note": "Historical exogenous feeds unverified; classified DATA_UNAVAILABLE under M5.11.",
        }


# ==============================================================================
# MASTER MULTI-FACTOR ENGINE
# ==============================================================================

def compute_market_context_dataframe(df_canonical: pd.DataFrame) -> pd.DataFrame:
    """Computes all single-asset market context features across Dimensions A, B, C, D."""
    df = df_canonical.sort_values("open_time_ms").reset_index(drop=True).copy()
    o = df["open"].to_numpy(dtype=np.float64)
    h = df["high"].to_numpy(dtype=np.float64)
    l = df["low"].to_numpy(dtype=np.float64)
    c = df["close"].to_numpy(dtype=np.float64)
    v = df["volume"].to_numpy(dtype=np.float64)

    # 1. Base Indicators
    atr14 = compute_atr(h, l, c, 14)
    df["atr_14"] = atr14
    df["atr_pct"] = atr14 / (c + 1e-12)

    ema9 = compute_ema(c, 9)
    ema21 = compute_ema(c, 21)
    ema50 = compute_ema(c, 50)
    ema200 = compute_ema(c, 200)
    df["ema_9"] = ema9
    df["ema_21"] = ema21
    df["ema_50"] = ema50
    df["ema_200"] = ema200

    bull_align = (ema9 > ema21) & (ema21 > ema50) & (ema50 > ema200)
    bear_align = (ema9 < ema21) & (ema21 < ema50) & (ema50 < ema200)
    align_score = np.zeros_like(c)
    align_score[bull_align] = 1.0
    align_score[bear_align] = -1.0
    df["ema_alignment_score"] = align_score

    df["rsi_14"] = compute_rsi(c, 14)
    stoch_k, stoch_d, _ = compute_stochastic(h, l, c, 14, 3, 3)
    df["stoch_k"] = stoch_k
    df["stoch_d"] = stoch_d

    bb_mid, bb_up, bb_low, bb_w, bb_b = compute_bollinger_bands(c, 20, 2.0)
    df["bb_upper"] = bb_up
    df["bb_lower"] = bb_low
    df["bb_width"] = bb_w
    df["bb_pct_b"] = bb_b

    don_h, don_l = compute_donchian_channels(h, l, 20)
    df["donchian_high_20"] = don_h
    df["donchian_low_20"] = don_l

    # 2. Dimension A: Market Structure
    sh, sl, bars_sh, bars_sl = compute_causal_swings(h, l, lookback=5, lookforward=5)
    df["swing_high"] = sh
    df["swing_low"] = sl
    df["bars_since_sh"] = bars_sh
    df["bars_since_sl"] = bars_sl

    b_fvg, br_fvg, fvg_mag = compute_fair_value_gaps(h, l, atr14)
    df["bullish_fvg"] = b_fvg
    df["bearish_fvg"] = br_fvg
    df["fvg_magnitude"] = fvg_mag

    b_disp, br_disp, bsl_swp, ssl_swp = compute_displacement_and_sweeps(o, h, l, c, atr14, sh, sl)
    df["bullish_displacement"] = b_disp
    df["bearish_displacement"] = br_disp
    df["bsl_sweep_reclaim"] = bsl_swp
    df["ssl_sweep_reclaim"] = ssl_swp

    # 3. Dimension B: Momentum and Trend
    adx_arr, p_di, m_di = compute_adx(h, l, c, 14)
    df["adx_14"] = adx_arr
    df["plus_di"] = p_di
    df["minus_di"] = m_di

    roc_arr, accel_arr = compute_momentum_acceleration(c, 10)
    df["roc_10"] = roc_arr
    df["momentum_acceleration"] = accel_arr
    df["trend_persistence"] = compute_trend_persistence(c, ema21)

    # 4. Dimension C: Volatility and Regime
    ker = compute_kaufman_efficiency_ratio(c, 20)
    df["efficiency_ratio_20"] = ker

    atr_pctl = compute_volatility_percentile(atr14, 100)
    df["atr_percentile_100"] = atr_pctl

    regimes, cycles = classify_market_regime(adx_arr, atr_pctl, ker)
    df["market_regime"] = regimes
    df["volatility_cycle"] = cycles

    # 5. Dimension D: Volume Proxies
    rvol, v_z, amihud, eff_res = compute_volume_proxies(h, l, o, c, v, atr14)
    df["rvol_20"] = rvol
    df["volume_zscore_50"] = v_z
    df["amihud_illiquidity"] = amihud
    df["effort_vs_result_ratio"] = eff_res

    return df
