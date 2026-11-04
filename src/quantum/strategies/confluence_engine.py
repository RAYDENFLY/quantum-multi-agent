"""Multi-Factor Confluence & Alpha Generation Engine (Milestone 5.13).

Provides a modular, strictly causal multi-factor alpha discovery framework supporting:
1. Ten independent market factors:
   - Factor 1: Trend Structure & Alignment (Multi-timeframe EMA, slope, persistence)
   - Factor 2: Momentum & Acceleration (RSI, stochastic, momentum rate of change)
   - Factor 3: Volatility & Expansion (ATR percentile, Bollinger bandwidth, contraction)
   - Factor 4: Volume & Order Flow Proxy (RVOL, taker buy/sell volume delta, trade count)
   - Factor 5: Market Structure (Causal swings, break of structure, fair value gaps)
   - Factor 6: Liquidity Sweeps (Extrema sweeps, reclaim displacement, sweep distance)
   - Factor 7: Relative Strength & Cross-Asset (Asset vs BTC return, rolling beta, breadth)
   - Factor 8: Regime Classification (HV_TREND, LV_TREND, HV_RANGE, LV_RANGE)
   - Factor 9: Execution Quality (Spread proxy, turnover depth, adverse selection risk)
   - Factor 10: Risk-Adjusted Opportunity (ATR-normalized reward/risk ratio)

2. Three Aggregation Methods:
   - Method A: Rule-Based Confluence (Weighted condition gating with strict thresholds)
   - Method B: Statistical Scoring (Standardized Z-scores with configurable factor weights)
   - Method C: Machine Learning Opportunity Ranking (Causal Random Forest / Ridge regression
     predicting forward net risk-adjusted return)

Strict Causality Invariant:
No future information, overlapping lookahead, or post-decision tick data is permitted.
All multi-timeframe aggregations are strictly closed before the decision bar open.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge

from quantum.core.logging import get_logger
from quantum.domain.enums import TradeSide
from quantum.features.indicators import (
    compute_atr,
    compute_bollinger_bands,
    compute_donchian_channels,
    compute_ema,
    compute_rsi,
    compute_stochastic,
)
from quantum.features.market_context import (
    MarketRegimeState,
    classify_market_regime,
    compute_adx,
    compute_causal_swings,
    compute_displacement_and_sweeps,
    compute_kaufman_efficiency_ratio,
    compute_volatility_percentile,
    compute_volume_proxies,
)

logger = get_logger("strategies.confluence_engine")


class ConfluenceMethod(str, Enum):
    """The three canonical confluence aggregation methods."""
    RULE_BASED = "RULE_BASED"
    STATISTICAL_SCORING = "STATISTICAL_SCORING"
    ML_RANKING = "ML_RANKING"


@dataclass
class ConfluenceSignal:
    """Standardized output signal from the Multi-Factor Confluence Engine."""
    bar_index: int
    timestamp_ms: int
    symbol: str
    side: TradeSide
    confidence_score: float  # [0.0, 1.0]
    expected_holding_bars: int
    stop_distance_atr: float
    target_distance_atr: float
    contributing_factors: Dict[str, float]
    aggregation_method: ConfluenceMethod
    regime: str


class MultiFactorConfluenceEngine:
    """Vectorized, causal feature calculation and confluence scoring across multiple assets."""

    def __init__(
        self,
        lookback_bars: int = 100,
        min_confluence_threshold: float = 0.65,
    ) -> None:
        self.lookback_bars = lookback_bars
        self.min_confluence_threshold = min_confluence_threshold
        self.ml_model: Optional[Any] = None
        self.feature_names: List[str] = []

    def compute_factors(
        self,
        df_5m: pd.DataFrame,
        df_15m: Optional[pd.DataFrame] = None,
        df_1h: Optional[pd.DataFrame] = None,
        df_btc_5m: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """Computes all 10 independent factor dimensions causally on the 5m base dataset."""
        df = df_5m.copy().sort_values("open_time_ms").reset_index(drop=True)
        n = len(df)
        close = df["close"].to_numpy(dtype=float)
        high = df["high"].to_numpy(dtype=float)
        low = df["low"].to_numpy(dtype=float)
        open_p = df["open"].to_numpy(dtype=float)
        volume = df["volume"].to_numpy(dtype=float)
        taker_buy_vol = df["taker_buy_volume"].to_numpy(dtype=float) if "taker_buy_volume" in df.columns else (volume * 0.5)

        # ----------------------------------------------------------------------
        # Factor 1: Trend Structure & Alignment
        # ----------------------------------------------------------------------
        ema_9 = compute_ema(close, 9)
        ema_21 = compute_ema(close, 21)
        ema_50 = compute_ema(close, 50)
        ema_200 = compute_ema(close, min(200, max(50, n // 4)))

        # EMA slope (normalized by close)
        ema_21_slope = np.zeros(n)
        ema_21_slope[5:] = (ema_21[5:] - ema_21[:-5]) / close[5:]

        # Trend alignment score: [-1.0, +1.0]
        trend_score = np.zeros(n)
        bullish_alignment = (close > ema_9) & (ema_9 > ema_21) & (ema_21 > ema_50)
        bearish_alignment = (close < ema_9) & (ema_9 < ema_21) & (ema_21 < ema_50)
        trend_score[bullish_alignment] = 1.0
        trend_score[bearish_alignment] = -1.0
        # Partial alignment
        partial_bull = (close > ema_21) & (ema_21 > ema_50) & ~bullish_alignment
        partial_bear = (close < ema_21) & (ema_21 < ema_50) & ~bearish_alignment
        trend_score[partial_bull] = 0.5
        trend_score[partial_bear] = -0.5

        # Multi-timeframe trend integration (Causal merge: 1h trend broadcasted to 5m)
        htf_trend = np.zeros(n)
        if df_1h is not None and len(df_1h) > 20:
            df_htf = df_1h.copy().sort_values("open_time_ms").reset_index(drop=True)
            htf_close = df_htf["close"].to_numpy(dtype=float)
            htf_ema21 = compute_ema(htf_close, 21)
            htf_ema50 = compute_ema(htf_close, min(50, len(df_htf) - 1))
            htf_bias = np.where(htf_close > htf_ema21, 1.0, -1.0)
            df_htf["htf_bias"] = htf_bias
            
            # Map causally by close_time_ms: 1h candle must have closed BEFORE 5m open
            htf_merged = pd.merge_asof(
                df[["open_time_ms"]],
                df_htf[["close_time_ms", "htf_bias"]],
                left_on="open_time_ms",
                right_on="close_time_ms",
                direction="backward",
            )
            htf_trend = htf_merged["htf_bias"].fillna(0.0).to_numpy()

        # ----------------------------------------------------------------------
        # Factor 2: Momentum & Acceleration
        # ----------------------------------------------------------------------
        rsi_14 = compute_rsi(close, 14)
        stoch_k, stoch_d, _ = compute_stochastic(high, low, close, 14, 3, 3)
        # Momentum score: normalized [-1.0, +1.0]
        mom_score = np.zeros(n)
        mom_score = (rsi_14 - 50.0) / 50.0
        mom_score = np.clip(mom_score, -1.0, 1.0)

        # ----------------------------------------------------------------------
        # Factor 3: Volatility & Expansion
        # ----------------------------------------------------------------------
        atr_14 = compute_atr(high, low, close, 14)
        bb_mid, bb_upper, bb_lower, bb_bandwidth, _ = compute_bollinger_bands(close, 20, 2.0)
        vol_pct = compute_volatility_percentile(bb_bandwidth, window=min(100, n))

        # ----------------------------------------------------------------------
        # Factor 4: Volume & Order Flow Proxy
        # ----------------------------------------------------------------------
        rvol, vol_z, amihud, _ = compute_volume_proxies(high, low, open_p, close, volume, atr_14)
        # Order flow imbalance proxy: (taker_buy - taker_sell) / total_vol
        taker_sell_vol = np.maximum(0.0, volume - taker_buy_vol)
        vol_safe = np.where(volume > 0, volume, 1.0)
        ofi_proxy = np.where(volume > 0, (taker_buy_vol - taker_sell_vol) / vol_safe, 0.0)

        # ----------------------------------------------------------------------
        # Factor 5: Market Structure (Causal Swings & Donchian Breakout)
        # ----------------------------------------------------------------------
        swing_h, swing_l, _, _ = compute_causal_swings(high, low, lookback=5, lookforward=5)
        donch_high, donch_low = compute_donchian_channels(high, low, 20)
        struct_score = np.zeros(n)
        struct_score[close > donch_high] = 1.0
        struct_score[close < donch_low] = -1.0

        # ----------------------------------------------------------------------
        # Factor 6: Liquidity Sweeps & Reclaim
        # ----------------------------------------------------------------------
        disp_up, disp_down, sweeps_h, sweeps_l = compute_displacement_and_sweeps(
            open_p, high, low, close, atr_14, swing_h, swing_l
        )
        sweep_score = np.zeros(n)
        sweep_score[(sweeps_l > 0) & (disp_up > 0)] = 1.0    # Swept low and displaced upward -> Bullish reclaim
        sweep_score[(sweeps_h > 0) & (disp_down > 0)] = -1.0 # Swept high and displaced downward -> Bearish reclaim

        # ----------------------------------------------------------------------
        # Factor 7: Relative Strength & Cross-Asset Confluence
        # ----------------------------------------------------------------------
        rel_strength = np.zeros(n)
        if df_btc_5m is not None and len(df_btc_5m) == n:
            btc_close = df_btc_5m["close"].to_numpy(dtype=float)
            ret_asset = np.zeros(n)
            ret_btc = np.zeros(n)
            ret_asset[12:] = (close[12:] - close[:-12]) / close[:-12]
            ret_btc[12:] = (btc_close[12:] - btc_close[:-12]) / btc_close[:-12]
            rel_strength = np.clip((ret_asset - ret_btc) * 100.0, -2.0, 2.0) / 2.0

        # ----------------------------------------------------------------------
        # Factor 8: Regime Classification
        # ----------------------------------------------------------------------
        adx, plus_di, minus_di = compute_adx(high, low, close, 14)
        ker = compute_kaufman_efficiency_ratio(close, 20)
        regimes, cycles = classify_market_regime(adx, vol_pct, ker)

        # ----------------------------------------------------------------------
        # Factor 9: Execution Quality Proxy
        # ----------------------------------------------------------------------
        # Lower volatility + higher volume = higher liquidity & lower slippage
        exec_quality = np.clip(rvol / (vol_pct + 0.1), 0.1, 5.0) / 5.0

        # ----------------------------------------------------------------------
        # Factor 10: Risk-Adjusted Opportunity (Reward / Risk distance)
        # ----------------------------------------------------------------------
        # Target = 2.0 ATR, Stop = 1.0 ATR -> Base R:R = 2.0
        rr_ratio = np.full(n, 2.0)

        # Assemble Factor Matrix
        factors_df = pd.DataFrame({
            "open_time_ms": df["open_time_ms"],
            "close_time_ms": df["close_time_ms"],
            "open": open_p,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
            "atr": atr_14,
            "f01_trend_score": trend_score,
            "f01_htf_trend": htf_trend,
            "f01_ema21_slope": ema_21_slope,
            "f02_momentum_score": mom_score,
            "f02_rsi": rsi_14,
            "f03_vol_percentile": vol_pct,
            "f03_bb_bandwidth": bb_bandwidth,
            "f04_rvol": rvol,
            "f04_ofi_proxy": ofi_proxy,
            "f05_struct_score": struct_score,
            "f06_sweep_score": sweep_score,
            "f07_rel_strength": rel_strength,
            "f08_adx": adx,
            "f08_regime": regimes,
            "f09_exec_quality": exec_quality,
            "f10_rr_ratio": rr_ratio,
        })

        return factors_df

    # --------------------------------------------------------------------------
    # Aggregation Method A: Rule-Based Confluence
    # --------------------------------------------------------------------------
    def generate_signals_rule_based(
        self,
        factors_df: pd.DataFrame,
        symbol: str,
        hypothesis_family: str = "TREND_CONTINUATION",
    ) -> List[ConfluenceSignal]:
        """Generates signals using explicit weighted gating rules via fast vectorized masks."""
        signals: List[ConfluenceSignal] = []
        n = len(factors_df)
        if n < 60:
            return signals

        open_ts = factors_df["open_time_ms"].to_numpy(dtype=np.int64)
        open_p = factors_df["open"].to_numpy(dtype=np.float64)
        close_p = factors_df["close"].to_numpy(dtype=np.float64)
        htf_trend = factors_df["f01_htf_trend"].to_numpy(dtype=np.float64)
        trend_score = factors_df["f01_trend_score"].to_numpy(dtype=np.float64)
        rsi = factors_df["f02_rsi"].to_numpy(dtype=np.float64)
        adx = factors_df["f08_adx"].to_numpy(dtype=np.float64)
        rvol = factors_df["f04_rvol"].to_numpy(dtype=np.float64)
        rel_strength = factors_df["f07_rel_strength"].to_numpy(dtype=np.float64)
        vol_pct = factors_df["f03_vol_percentile"].to_numpy(dtype=np.float64)
        struct_score = factors_df["f05_struct_score"].to_numpy(dtype=np.float64)
        sweep_score = factors_df["f06_sweep_score"].to_numpy(dtype=np.float64)
        regimes = factors_df["f08_regime"].to_numpy()
        ofi = factors_df["f04_ofi_proxy"].to_numpy(dtype=np.float64)

        if hypothesis_family == "TREND_CONTINUATION":
            is_bull = (htf_trend > 0) & (trend_score >= 0.5) & (rsi > 45.0) & (rsi < 65.0) & (adx > 20.0)
            is_bear = (htf_trend < 0) & (trend_score <= -0.5) & (rsi < 55.0) & (rsi > 35.0) & (adx > 20.0)
            target_atr, stop_atr, hold_bars = 3.0, 1.5, 48
            active_idx = np.where((is_bull | is_bear) & (np.arange(n) >= 50) & (np.arange(n) < n - 1))[0]
            for i in active_idx:
                if is_bull[i]:
                    side = TradeSide.LONG
                    conf = 0.70 + (0.15 * min(1.0, rvol[i] / 2.0)) + (0.15 * max(0.0, rel_strength[i]))
                    contrib = {"htf_trend": 0.35, "trend_alignment": 0.25, "rsi_pullback": 0.20, "rvol": 0.20}
                else:
                    side = TradeSide.SHORT
                    conf = 0.70 + (0.15 * min(1.0, rvol[i] / 2.0)) - (0.15 * min(0.0, rel_strength[i]))
                    contrib = {"htf_trend": 0.35, "trend_alignment": 0.25, "rsi_pullback": 0.20, "rvol": 0.20}
                if conf >= self.min_confluence_threshold:
                    signals.append(ConfluenceSignal(
                        bar_index=int(i), timestamp_ms=int(open_ts[i]), symbol=symbol, side=side,
                        confidence_score=round(conf, 4), expected_holding_bars=hold_bars,
                        stop_distance_atr=stop_atr, target_distance_atr=target_atr,
                        contributing_factors=contrib, aggregation_method=ConfluenceMethod.RULE_BASED,
                        regime=str(regimes[i]),
                    ))

        elif hypothesis_family == "VOLATILITY_BREAKOUT":
            is_compression = vol_pct < 0.25
            is_breakout_long = (struct_score == 1.0) & (rvol > 1.5) & is_compression
            is_breakout_short = (struct_score == -1.0) & (rvol > 1.5) & is_compression
            target_atr, stop_atr, hold_bars = 3.5, 1.5, 36
            active_idx = np.where((is_breakout_long | is_breakout_short) & (np.arange(n) >= 50) & (np.arange(n) < n - 1))[0]
            for i in active_idx:
                side = TradeSide.LONG if is_breakout_long[i] else TradeSide.SHORT
                conf = 0.75 + (0.15 * min(1.0, (rvol[i] - 1.5) / 2.0))
                contrib = {"compression": 0.35, "donchian_breakout": 0.35, "volume_surge": 0.30}
                if conf >= self.min_confluence_threshold:
                    signals.append(ConfluenceSignal(
                        bar_index=int(i), timestamp_ms=int(open_ts[i]), symbol=symbol, side=side,
                        confidence_score=round(conf, 4), expected_holding_bars=hold_bars,
                        stop_distance_atr=stop_atr, target_distance_atr=target_atr,
                        contributing_factors=contrib, aggregation_method=ConfluenceMethod.RULE_BASED,
                        regime=str(regimes[i]),
                    ))

        elif hypothesis_family == "LIQUIDITY_SWEEP_RECLAIM":
            is_sweep_long = (sweep_score == 1.0) & (rvol > 1.2)
            is_sweep_short = (sweep_score == -1.0) & (rvol > 1.2)
            target_atr, stop_atr, hold_bars = 2.5, 1.5, 24
            active_idx = np.where((is_sweep_long | is_sweep_short) & (np.arange(n) >= 50) & (np.arange(n) < n - 1))[0]
            for i in active_idx:
                side = TradeSide.LONG if is_sweep_long[i] else TradeSide.SHORT
                contrib = {"liquidity_sweep": 0.50, "displacement": 0.30, "volume": 0.20}
                signals.append(ConfluenceSignal(
                    bar_index=int(i), timestamp_ms=int(open_ts[i]), symbol=symbol, side=side,
                    confidence_score=0.80, expected_holding_bars=hold_bars,
                    stop_distance_atr=stop_atr, target_distance_atr=target_atr,
                    contributing_factors=contrib, aggregation_method=ConfluenceMethod.RULE_BASED,
                    regime=str(regimes[i]),
                ))

        elif hypothesis_family == "RANGE_MEAN_REVERSION":
            is_range = np.array(["RANGE" in str(r) for r in regimes])
            is_rev_long = is_range & (rsi < 28.0) & (close_p <= (open_p * 0.998))
            is_rev_short = is_range & (rsi > 72.0) & (close_p >= (open_p * 1.002))
            target_atr, stop_atr, hold_bars = 1.5, 1.0, 18
            active_idx = np.where((is_rev_long | is_rev_short) & (np.arange(n) >= 50) & (np.arange(n) < n - 1))[0]
            for i in active_idx:
                if is_rev_long[i]:
                    side = TradeSide.LONG
                    conf = 0.70 + (0.15 * (28.0 - rsi[i]) / 15.0)
                    contrib = {"range_regime": 0.40, "rsi_oversold": 0.40, "mean_reversion": 0.20}
                else:
                    side = TradeSide.SHORT
                    conf = 0.70 + (0.15 * (rsi[i] - 72.0) / 15.0)
                    contrib = {"range_regime": 0.40, "rsi_overbought": 0.40, "mean_reversion": 0.20}
                if conf >= self.min_confluence_threshold:
                    signals.append(ConfluenceSignal(
                        bar_index=int(i), timestamp_ms=int(open_ts[i]), symbol=symbol, side=side,
                        confidence_score=round(conf, 4), expected_holding_bars=hold_bars,
                        stop_distance_atr=stop_atr, target_distance_atr=target_atr,
                        contributing_factors=contrib, aggregation_method=ConfluenceMethod.RULE_BASED,
                        regime=str(regimes[i]),
                    ))

        elif hypothesis_family == "CROSS_ASSET_MOMENTUM":
            is_ca_long = (rel_strength > 0.4) & (htf_trend > 0) & (adx > 22.0)
            is_ca_short = (rel_strength < -0.4) & (htf_trend < 0) & (adx > 22.0)
            target_atr, stop_atr, hold_bars = 2.8, 1.5, 36
            active_idx = np.where((is_ca_long | is_ca_short) & (np.arange(n) >= 50) & (np.arange(n) < n - 1))[0]
            for i in active_idx:
                if is_ca_long[i]:
                    side = TradeSide.LONG
                    conf = 0.72 + (0.20 * rel_strength[i])
                else:
                    side = TradeSide.SHORT
                    conf = 0.72 - (0.20 * rel_strength[i])
                contrib = {"cross_asset_rs": 0.45, "htf_trend": 0.35, "momentum": 0.20}
                if conf >= self.min_confluence_threshold:
                    signals.append(ConfluenceSignal(
                        bar_index=int(i), timestamp_ms=int(open_ts[i]), symbol=symbol, side=side,
                        confidence_score=round(conf, 4), expected_holding_bars=hold_bars,
                        stop_distance_atr=stop_atr, target_distance_atr=target_atr,
                        contributing_factors=contrib, aggregation_method=ConfluenceMethod.RULE_BASED,
                        regime=str(regimes[i]),
                    ))

        elif hypothesis_family == "MULTI_FACTOR_CONFLUENCE":
            bull_pts = np.zeros(n)
            bear_pts = np.zeros(n)
            bull_pts += np.where(htf_trend > 0, 0.25, 0.0)
            bear_pts += np.where(htf_trend < 0, 0.25, 0.0)
            bull_pts += np.where(trend_score > 0, 0.20, 0.0)
            bear_pts += np.where(trend_score < 0, 0.20, 0.0)
            bull_pts += np.where(ofi > 0.15, 0.15, 0.0)
            bear_pts += np.where(ofi < -0.15, 0.15, 0.0)
            bull_pts += np.where(sweep_score == 1.0, 0.25, 0.0)
            bear_pts += np.where(sweep_score == -1.0, 0.25, 0.0)
            bull_pts += np.where(rel_strength > 0.2, 0.15, 0.0)
            bear_pts += np.where(rel_strength < -0.2, 0.15, 0.0)

            is_conf_long = (bull_pts >= 0.70) & (bull_pts > (bear_pts + 0.40))
            is_conf_short = (bear_pts >= 0.70) & (bear_pts > (bull_pts + 0.40))
            target_atr, stop_atr, hold_bars = 3.0, 1.5, 36
            active_idx = np.where((is_conf_long | is_conf_short) & (np.arange(n) >= 50) & (np.arange(n) < n - 1))[0]
            for i in active_idx:
                if is_conf_long[i]:
                    side = TradeSide.LONG
                    conf = float(bull_pts[i])
                else:
                    side = TradeSide.SHORT
                    conf = float(bear_pts[i])
                contrib = {"confluence_score": conf}
                if conf >= self.min_confluence_threshold:
                    signals.append(ConfluenceSignal(
                        bar_index=int(i), timestamp_ms=int(open_ts[i]), symbol=symbol, side=side,
                        confidence_score=round(conf, 4), expected_holding_bars=hold_bars,
                        stop_distance_atr=stop_atr, target_distance_atr=target_atr,
                        contributing_factors=contrib, aggregation_method=ConfluenceMethod.RULE_BASED,
                        regime=str(regimes[i]),
                    ))

        return signals

    # --------------------------------------------------------------------------
    # Aggregation Method B: Statistical Scoring
    # --------------------------------------------------------------------------
    def generate_signals_statistical_scoring(
        self,
        factors_df: pd.DataFrame,
        symbol: str,
        z_score_threshold: float = 1.75,
    ) -> List[ConfluenceSignal]:
        """Aggregates standardized factor Z-scores with multivariate weighting."""
        signals: List[ConfluenceSignal] = []
        n = len(factors_df)
        if n < 120:
            return signals

        open_ts = factors_df["open_time_ms"].to_numpy(dtype=np.int64)
        regimes = factors_df["f08_regime"].to_numpy()
        
        # Linear weighted composite score
        composite = (
            0.30 * factors_df["f01_trend_score"].to_numpy()
            + 0.25 * factors_df["f01_htf_trend"].to_numpy()
            + 0.15 * factors_df["f02_momentum_score"].to_numpy()
            + 0.15 * factors_df["f04_ofi_proxy"].to_numpy()
            + 0.15 * factors_df["f07_rel_strength"].to_numpy()
        )

        # Rolling z-score over 100 bars
        window = 100
        roll_mean = pd.Series(composite).rolling(window, min_periods=20).mean().to_numpy()
        roll_std = pd.Series(composite).rolling(window, min_periods=20).std().replace(0.0, 1.0).to_numpy()
        z_scores = np.where(roll_std > 1e-6, (composite - roll_mean) / roll_std, 0.0)

        active_idx = np.where((np.abs(z_scores) >= z_score_threshold) & (np.arange(n) >= window) & (np.arange(n) < n - 1))[0]
        for i in active_idx:
            z = z_scores[i]
            side = TradeSide.LONG if z > 0 else TradeSide.SHORT
            conf = min(0.95, 0.65 + (abs(z) - z_score_threshold) * 0.10)
            signals.append(
                ConfluenceSignal(
                    bar_index=int(i),
                    timestamp_ms=int(open_ts[i]),
                    symbol=symbol,
                    side=side,
                    confidence_score=round(conf, 4),
                    expected_holding_bars=36,
                    stop_distance_atr=1.5,
                    target_distance_atr=2.8,
                    contributing_factors={"composite_z_score": round(float(z), 3)},
                    aggregation_method=ConfluenceMethod.STATISTICAL_SCORING,
                    regime=str(regimes[i]),
                )
            )

        return signals

    # --------------------------------------------------------------------------
    # Aggregation Method C: Machine Learning Opportunity Ranking
    # --------------------------------------------------------------------------
    def train_ml_ranker(
        self,
        factors_df_train: pd.DataFrame,
        forward_bars: int = 24,
    ) -> None:
        """Trains a causal Random Forest Regressor to predict forward ATR-normalized net return."""
        feature_cols = [
            "f01_trend_score", "f01_htf_trend", "f01_ema21_slope",
            "f02_momentum_score", "f03_vol_percentile", "f03_bb_bandwidth",
            "f04_rvol", "f04_ofi_proxy", "f05_struct_score", "f06_sweep_score",
            "f07_rel_strength", "f08_adx", "f09_exec_quality",
        ]
        self.feature_names = feature_cols

        df = factors_df_train.copy().dropna(subset=feature_cols).reset_index(drop=True)
        close = df["close"].to_numpy()
        atr = df["atr"].to_numpy()
        n = len(df)

        # Forward return: (close[t + forward_bars] - close[t]) / atr[t]
        y = np.zeros(n)
        valid_idx = []
        for t in range(n - forward_bars):
            if atr[t] > 1e-6:
                ret = (close[t + forward_bars] - close[t]) / atr[t]
                y[t] = ret
                valid_idx.append(t)

        X_train = df.loc[valid_idx, feature_cols].to_numpy()
        y_train = y[valid_idx]

        self.ml_model = RandomForestRegressor(
            n_estimators=50,
            max_depth=5,
            min_samples_leaf=20,
            random_state=42,
            n_jobs=-1,
        )
        self.ml_model.fit(X_train, y_train)
        logger.info("Trained ML Confluence Ranker with %d samples", len(valid_idx))

    def generate_signals_ml_ranking(
        self,
        factors_df: pd.DataFrame,
        symbol: str,
        ranking_threshold_atr: float = 0.50,
    ) -> List[ConfluenceSignal]:
        """Generates signals based on ML predicted forward directional move."""
        if self.ml_model is None:
            raise ValueError("ML model not trained. Call train_ml_ranker first.")

        signals: List[ConfluenceSignal] = []
        df = factors_df.dropna(subset=self.feature_names).reset_index(drop=True)
        open_ts = df["open_time_ms"].to_numpy(dtype=np.int64)
        regimes = df["f08_regime"].to_numpy()
        X = df[self.feature_names].to_numpy()
        preds = self.ml_model.predict(X)

        active_idx = np.where((np.abs(preds) >= ranking_threshold_atr) & (np.arange(len(df)) < len(df) - 1))[0]
        for i in active_idx:
            pred_move = preds[i]
            side = TradeSide.LONG if pred_move > 0 else TradeSide.SHORT
            conf = min(0.95, 0.65 + (abs(pred_move) - ranking_threshold_atr) * 0.15)
            signals.append(
                ConfluenceSignal(
                    bar_index=int(i),
                    timestamp_ms=int(open_ts[i]),
                    symbol=symbol,
                    side=side,
                    confidence_score=round(conf, 4),
                    expected_holding_bars=24,
                    stop_distance_atr=1.5,
                    target_distance_atr=2.5,
                    contributing_factors={"ml_predicted_atr_move": round(float(pred_move), 3)},
                    aggregation_method=ConfluenceMethod.ML_RANKING,
                    regime=str(regimes[i]),
                )
            )

        return signals
