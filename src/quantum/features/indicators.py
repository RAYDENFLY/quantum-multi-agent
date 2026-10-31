"""Deterministic, vectorized technical indicators with zero future data access."""

import numpy as np
import pandas as pd


def compute_ema(series: np.ndarray, period: int) -> np.ndarray:
    """Compute Exponential Moving Average initialized with SMA of first N bars."""
    n = len(series)
    out = np.full(n, np.nan, dtype=np.float64)
    if n < period or period <= 0:
        return out

    # Initial SMA
    sma = np.mean(series[:period])
    out[period - 1] = sma
    alpha = 2.0 / (period + 1.0)
    one_minus_alpha = 1.0 - alpha

    curr = sma
    for i in range(period, n):
        curr = (series[i] * alpha) + (curr * one_minus_alpha)
        out[i] = curr
    return out


def compute_rsi(close: np.ndarray, period: int = 14) -> np.ndarray:
    """Compute Wilder's Relative Strength Index (RSI)."""
    n = len(close)
    out = np.full(n, np.nan, dtype=np.float64)
    if n <= period or period <= 0:
        return out

    deltas = np.diff(close)
    gains = np.maximum(deltas, 0.0)
    losses = np.maximum(-deltas, 0.0)

    # First Wilder smoothing period
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    if avg_loss == 0.0:
        out[period] = 100.0 if avg_gain > 0.0 else 50.0
    else:
        rs = avg_gain / avg_loss
        out[period] = 100.0 - (100.0 / (1.0 + rs))

    alpha = 1.0 / period
    for i in range(period, len(deltas)):
        idx = i + 1
        avg_gain = (avg_gain * (period - 1) + gains[i]) * alpha
        avg_loss = (avg_loss * (period - 1) + losses[i]) * alpha

        if avg_loss == 0.0:
            out[idx] = 100.0 if avg_gain > 0.0 else 50.0
        else:
            rs = avg_gain / avg_loss
            out[idx] = 100.0 - (100.0 / (1.0 + rs))

    return out


def compute_macd(
    close: np.ndarray,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute MACD line, signal line, and MACD histogram."""
    fast_ema = compute_ema(close, fast_period)
    slow_ema = compute_ema(close, slow_period)
    macd_line = fast_ema - slow_ema

    # Signal line is EMA of macd_line over valid values
    signal_line = np.full_like(macd_line, np.nan)
    valid_mask = ~np.isnan(macd_line)
    if np.sum(valid_mask) >= signal_period:
        valid_indices = np.where(valid_mask)[0]
        sub_signal = compute_ema(macd_line[valid_indices], signal_period)
        signal_line[valid_indices] = sub_signal

    macd_hist = macd_line - signal_line
    return macd_line, signal_line, macd_hist


def compute_stochastic(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    k_period: int = 5,
    d_period: int = 3,
    slow_d_period: int = 3,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute Stochastic Oscillator (%K, %D, Slow %D)."""
    n = len(close)
    k_line = np.full(n, np.nan, dtype=np.float64)
    eps = 1e-12

    for i in range(k_period - 1, n):
        h_win = np.max(high[i - k_period + 1 : i + 1])
        l_win = np.min(low[i - k_period + 1 : i + 1])
        denom = h_win - l_win
        k_line[i] = ((close[i] - l_win) / (denom + eps)) * 100.0

    # Smooth %K to get %D
    d_line = pd.Series(k_line).rolling(window=d_period, min_periods=d_period).mean().to_numpy()
    slow_d = pd.Series(d_line).rolling(window=slow_d_period, min_periods=slow_d_period).mean().to_numpy()

    return k_line, d_line, slow_d


def compute_atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
    """Compute Wilder's Average True Range (ATR)."""
    n = len(close)
    out = np.full(n, np.nan, dtype=np.float64)
    if n < period or period <= 0:
        return out

    # Compute True Range array
    tr = np.zeros(n, dtype=np.float64)
    tr[0] = high[0] - low[0]
    for i in range(1, n):
        hl = high[i] - low[i]
        hc = abs(high[i] - close[i - 1])
        lc = abs(low[i] - close[i - 1])
        tr[i] = max(hl, hc, lc)

    # Initial SMA of TR
    first_atr = np.mean(tr[:period])
    out[period - 1] = first_atr

    curr = first_atr
    alpha = 1.0 / period
    for i in range(period, n):
        curr = (curr * (period - 1) + tr[i]) * alpha
        out[i] = curr

    return out


def compute_bollinger_bands(
    close: np.ndarray,
    period: int = 20,
    num_std: float = 2.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute Bollinger Bands (middle, upper, lower, bandwidth, %B)."""
    s = pd.Series(close)
    middle = s.rolling(window=period, min_periods=period).mean().to_numpy()
    std = s.rolling(window=period, min_periods=period).std(ddof=0).to_numpy()
    eps = 1e-12

    upper = middle + (num_std * std)
    lower = middle - (num_std * std)
    bandwidth = (upper - lower) / (middle + eps)
    pct_b = (close - lower) / ((upper - lower) + eps)

    return middle, upper, lower, bandwidth, pct_b


def compute_donchian_channels(high: np.ndarray, low: np.ndarray, period: int = 20) -> tuple[np.ndarray, np.ndarray]:
    """Compute Donchian Channel High and Low strictly over past N closed bars [t-N : t-1]."""
    # Shift by 1 to guarantee strict causality (zero lookahead into current bar)
    s_high = pd.Series(high).shift(1)
    s_low = pd.Series(low).shift(1)

    donchian_high = s_high.rolling(window=period, min_periods=period).max().to_numpy()
    donchian_low = s_low.rolling(window=period, min_periods=period).min().to_numpy()

    return donchian_high, donchian_low
