"""Deterministic feature computation engine with strict causal boundaries."""

from typing import Optional
import numpy as np
import pandas as pd

from quantum.core.logging import get_logger
from quantum.features.indicators import (
    compute_atr,
    compute_bollinger_bands,
    compute_donchian_channels,
    compute_ema,
    compute_macd,
    compute_rsi,
    compute_stochastic,
)
from quantum.features.schema import BASE_FEATURE_COLUMNS, FEATURE_SCHEMA_VERSION, RESEARCH_FEATURE_COLUMNS

logger = get_logger("features.engine")


class FeatureEngine:
    """Computes deterministic, scale-invariant feature vectors from canonical OHLCV data."""

    def __init__(self, schema_version: str = FEATURE_SCHEMA_VERSION) -> None:
        self.schema_version = schema_version

    def compute_features(self, df_canonical: pd.DataFrame) -> pd.DataFrame:
        """Compute full suite of causal technical features from canonical OHLCV DataFrame."""
        if df_canonical.empty:
            return pd.DataFrame()

        required_cols = {"open_time_ms", "close_time_ms", "open", "high", "low", "close", "volume"}
        missing = required_cols - set(df_canonical.columns)
        if missing:
            raise ValueError(f"Missing required canonical columns for feature extraction: {missing}")

        # Ensure strict ascending chronological order
        df = df_canonical.sort_values(by="open_time_ms").reset_index(drop=True)

        o = df["open"].to_numpy(dtype=np.float64)
        h = df["high"].to_numpy(dtype=np.float64)
        l = df["low"].to_numpy(dtype=np.float64)
        c = df["close"].to_numpy(dtype=np.float64)
        v = df["volume"].to_numpy(dtype=np.float64)
        qv = df["quote_volume"].to_numpy(dtype=np.float64) if "quote_volume" in df.columns else None

        eps = 1e-12
        features: dict[str, np.ndarray] = {
            "open_time_ms": df["open_time_ms"].to_numpy(dtype=np.int64),
            "close_time_ms": df["close_time_ms"].to_numpy(dtype=np.int64),
        }

        # 1. Price and Return Features
        s_c = pd.Series(c)
        s_v = pd.Series(v)

        simple_ret = s_c.pct_change().to_numpy()
        prev_c = s_c.shift(1).to_numpy()
        log_ret = np.full_like(c, np.nan)
        valid_prev = (prev_c > 0.0) & (c > 0.0)
        log_ret[valid_prev] = np.log(c[valid_prev] / prev_c[valid_prev])

        hl_span = h - l
        features["simple_return"] = simple_ret
        features["log_return"] = log_ret
        features["pct_change"] = simple_ret * 100.0
        features["hl_range"] = hl_span
        features["hl_range_pct"] = hl_span / (c + eps)
        features["body_pct"] = np.abs(c - o) / (hl_span + eps)
        features["upper_wick_pct"] = (h - np.maximum(o, c)) / (hl_span + eps)
        features["lower_wick_pct"] = (np.minimum(o, c) - l) / (hl_span + eps)
        features["clv"] = ((2.0 * c) - h - l) / (hl_span + eps)

        # 2. Trend Features (EMAs 9, 21, 50, 100, 200)
        ema_9 = compute_ema(c, 9)
        ema_21 = compute_ema(c, 21)
        ema_50 = compute_ema(c, 50)
        ema_100 = compute_ema(c, 100)
        ema_200 = compute_ema(c, 200)

        features["ema_9"] = ema_9
        features["ema_21"] = ema_21
        features["ema_50"] = ema_50
        features["ema_100"] = ema_100
        features["ema_200"] = ema_200

        features["price_dist_ema_9"] = (c - ema_9) / (ema_9 + eps)
        features["price_dist_ema_21"] = (c - ema_21) / (ema_21 + eps)
        features["price_dist_ema_50"] = (c - ema_50) / (ema_50 + eps)
        features["price_dist_ema_100"] = (c - ema_100) / (ema_100 + eps)
        features["price_dist_ema_200"] = (c - ema_200) / (ema_200 + eps)

        features["ema_9_slope"] = pd.Series(ema_9).pct_change().to_numpy()
        features["ema_21_slope"] = pd.Series(ema_21).pct_change().to_numpy()
        features["ema_50_slope"] = pd.Series(ema_50).pct_change().to_numpy()
        features["ema_100_slope"] = pd.Series(ema_100).pct_change().to_numpy()
        features["ema_200_slope"] = pd.Series(ema_200).pct_change().to_numpy()

        features["crossover_9_21"] = np.where(np.isnan(ema_9) | np.isnan(ema_21), np.nan, (ema_9 > ema_21).astype(float))
        features["crossover_21_50"] = np.where(np.isnan(ema_21) | np.isnan(ema_50), np.nan, (ema_21 > ema_50).astype(float))
        features["crossover_50_200"] = np.where(np.isnan(ema_50) | np.isnan(ema_200), np.nan, (ema_50 > ema_200).astype(float))

        # 3. Momentum Features (RSI 14, MACD, Stoch 5/3/3, ROC 10)
        features["rsi_14"] = compute_rsi(c, 14)

        macd_line, macd_sig, macd_hist = compute_macd(c, 12, 26, 9)
        features["macd_line"] = macd_line
        features["macd_signal"] = macd_sig
        features["macd_hist"] = macd_hist

        stoch_k, stoch_d, stoch_slow_d = compute_stochastic(h, l, c, 5, 3, 3)
        features["stoch_k"] = stoch_k
        features["stoch_d"] = stoch_d
        features["stoch_slow_d"] = stoch_slow_d

        prev_10 = s_c.shift(10).to_numpy()
        roc_10 = np.full_like(c, np.nan)
        valid_roc = prev_10 > 0.0
        roc_10[valid_roc] = (c[valid_roc] - prev_10[valid_roc]) / prev_10[valid_roc]
        features["roc_10"] = roc_10

        # 4. Volatility Features (ATR 14, Rolling std, Bollinger Bands)
        atr_14 = compute_atr(h, l, c, 14)
        features["atr_14"] = atr_14
        features["atr_14_pct"] = atr_14 / (c + eps)
        features["rolling_std_returns_20"] = pd.Series(simple_ret).rolling(window=20, min_periods=20).std(ddof=1).to_numpy()

        bb_mid, bb_up, bb_low, bb_w, bb_b = compute_bollinger_bands(c, 20, 2.0)
        features["bb_middle_20"] = bb_mid
        features["bb_upper_20"] = bb_up
        features["bb_lower_20"] = bb_low
        features["bb_width_20"] = bb_w
        features["bb_pct_b_20"] = bb_b

        roll_h20 = pd.Series(h).rolling(window=20, min_periods=20).max().to_numpy()
        roll_l20 = pd.Series(l).rolling(window=20, min_periods=20).min().to_numpy()
        features["rolling_hl_range_20"] = (roll_h20 - roll_l20) / (c + eps)

        # 5. Volume Features
        vol_sma_20 = s_v.rolling(window=20, min_periods=20).mean().to_numpy()
        features["vol_sma_20"] = vol_sma_20
        features["rvol_20"] = v / (vol_sma_20 + eps)
        v_shift = s_v.shift(1)
        raw_vol_change = np.where(v_shift > 0, (s_v - v_shift) / v_shift, 0.0).astype(float)
        raw_vol_change[0] = np.nan
        features["vol_change"] = raw_vol_change

        if qv is not None and not np.all(np.isnan(qv)):
            s_qv = pd.Series(qv)
            q_sma = s_qv.rolling(window=20, min_periods=20).mean().to_numpy()
            features["quote_vol_sma_20"] = q_sma
            features["quote_rvol_20"] = qv / (q_sma + eps)
        else:
            features["quote_vol_sma_20"] = np.full_like(c, np.nan)
            features["quote_rvol_20"] = np.full_like(c, np.nan)

        # 6. Market Structure Features
        don_h, don_l = compute_donchian_channels(h, l, 20)
        features["donchian_high_20"] = don_h
        features["donchian_low_20"] = don_l

        breakout_dist = np.zeros_like(c)
        valid_don = ~np.isnan(don_h) & ~np.isnan(don_l)
        above_mask = valid_don & (c > don_h)
        below_mask = valid_don & (c < don_l)
        breakout_dist[above_mask] = (c[above_mask] - don_h[above_mask]) / (c[above_mask] + eps)
        breakout_dist[below_mask] = (c[below_mask] - don_l[below_mask]) / (c[below_mask] + eps)
        breakout_dist[~valid_don] = np.nan
        features["donchian_breakout_dist"] = breakout_dist

        features["dist_from_high_20"] = (c - roll_h20) / (c + eps)
        features["dist_from_low_20"] = (c - roll_l20) / (c + eps)

        # Deterministic trend state
        trend_state = np.zeros_like(c)
        valid_trend = ~np.isnan(ema_50) & ~np.isnan(ema_200) & ~np.isnan(features["ema_50_slope"])
        bull_mask = valid_trend & (ema_50 > ema_200) & (features["ema_50_slope"] > 0)
        bear_mask = valid_trend & (ema_50 < ema_200) & (features["ema_50_slope"] < 0)
        trend_state[bull_mask] = 1.0
        trend_state[bear_mask] = -1.0
        trend_state[~valid_trend] = np.nan
        features["trend_state"] = trend_state

        out_df = pd.DataFrame(features)
        return out_df

    def filter_research_features(self, df_features: pd.DataFrame, warmup_bars: int = 200) -> pd.DataFrame:
        """Apply Phase 5.0 feature hygiene: trim warm-up and retain stationary features."""
        if df_features.empty:
            return pd.DataFrame()

        available_cols = [c for c in RESEARCH_FEATURE_COLUMNS if c in df_features.columns]
        if len(df_features) <= warmup_bars:
            raise ValueError(
                f"Feature DataFrame has {len(df_features)} rows, insufficient to trim {warmup_bars} warm-up bars"
            )

        df_trimmed = df_features[available_cols].iloc[warmup_bars:].copy().reset_index(drop=True)

        num_cols = df_trimmed.select_dtypes(include=[np.number]).columns
        nan_count = int(df_trimmed[num_cols].isna().sum().sum())
        if nan_count > 0:
            raise ValueError(f"Research feature matrix contains {nan_count} unexpected NaNs after warm-up")

        inf_count = int(np.isinf(df_trimmed[num_cols]).sum().sum())
        if inf_count > 0:
            raise ValueError(f"Research feature matrix contains {inf_count} infinite values")

        return df_trimmed
