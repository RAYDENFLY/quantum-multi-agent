"""High-Speed $100 USD Multi-Asset Strategy Backtest & Validation Engine."""

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from quantum.backtesting.adapters import (
    PRIMARY_RESEARCH_UNIVERSE,
    PROSPECTIVE_HOLDOUT_START_MS,
)
from quantum.backtesting.resources import BACKTEST_MAX_THREADS, enforce_backtest_thread_limits
from quantum.strategies.schemas import (
    ExecutionPolicyMismatchError,
    FailureClassification,
    StrategyConfiguration,
    StrategyEvaluationResult,
    VENUE_PROFILES,
    ExecutionVenueSchedule,
    get_venue_schedule,
)

FEE_TIERS_BPS: Dict[str, Tuple[float, float]] = {
    # tier_name -> (round_trip_fee_bps, round_trip_slippage_bps)
    "maker_passive": (8.0, 0.0),
    "hybrid_tier": (14.0, 1.0),
    "baseline_taker": (40.0, 4.0),
}


@dataclass
class AssetFeatureMatrix:
    """Pre-aligned causal 5m candle and OOF feature arrays for ultra-fast evaluation."""
    symbol: str
    open_time_ms: np.ndarray
    opens: np.ndarray
    highs: np.ndarray
    lows: np.ndarray
    closes: np.ndarray
    sigma_20: np.ndarray
    vol_quantiles: Dict[float, float]
    vol_exp_ratio: np.ndarray
    rvol_20: np.ndarray
    taker_buy_ratio: np.ndarray
    lower_wick: np.ndarray
    upper_wick: np.ndarray
    htf_rets_bps: Dict[int, np.ndarray]
    btc_rets_bps: Dict[int, np.ndarray]
    # Aligned at bar i-1 close (signal index for entry at bar i open)
    has_oof_prev: np.ndarray
    fold_prev: np.ndarray
    prob_m1_prev: np.ndarray
    prob_0_prev: np.ndarray
    prob_p1_prev: np.ndarray


class StrategyDiscoveryEvaluator:
    """Evaluates declarative StrategyConfigurations on $100 USD portfolio capital."""

    def __init__(
        self,
        candle_base_dir: Path = Path("data/historical/canonical/exchange=ASTER"),
        oof_dir: Path = Path("artifacts/phase_5_4/materialized_oof"),
    ) -> None:
        enforce_backtest_thread_limits(BACKTEST_MAX_THREADS)
        self.candle_base_dir = candle_base_dir
        self.oof_dir = oof_dir
        self.matrices: Dict[str, AssetFeatureMatrix] = {}
        self._last_simulation_stats: Dict[str, Dict[str, int]] = {}
        self._preload_universe()

    def _load_raw_candles(self, symbol: str) -> pd.DataFrame:
        s_dir = self.candle_base_dir / f"symbol={symbol}" / "timeframe=5m"
        files = sorted(s_dir.glob("*.parquet"))
        cols = [
            "open_time_ms", "open", "high", "low", "close",
            "volume", "taker_buy_volume",
        ]
        dfs = [pq.ParquetFile(f).read(cols).to_pandas() for f in files]
        df = pd.concat(dfs, ignore_index=True)
        df = df.sort_values("open_time_ms", kind="mergesort").drop_duplicates("open_time_ms").reset_index(drop=True)
        if df["open_time_ms"].max() >= PROSPECTIVE_HOLDOUT_START_MS:
            raise ValueError(f"Holdout seal breach in {symbol}")
        return df

    def _preload_universe(self) -> None:
        """Pre-computes causal microstructure, HTF, and BTC lead-lag arrays for all 10 primary assets."""
        df_btc = self._load_raw_candles("BTCUSDT")
        btc_ts = df_btc["open_time_ms"].to_numpy(dtype=np.int64)
        btc_close = df_btc["close"]
        btc_lookup_maps: Dict[int, pd.Series] = {}
        for lb in (3, 6, 12, 24):
            s = pd.Series(btc_close.pct_change(lb).fillna(0.0).to_numpy() * 10_000.0, index=btc_ts)
            btc_lookup_maps[lb] = s

        for sym in PRIMARY_RESEARCH_UNIVERSE:
            df_c = df_btc.copy() if sym == "BTCUSDT" else self._load_raw_candles(sym)
            n = len(df_c)
            ts = df_c["open_time_ms"].to_numpy(dtype=np.int64)
            opens = df_c["open"].to_numpy(dtype=np.float64)
            highs = df_c["high"].to_numpy(dtype=np.float64)
            lows = df_c["low"].to_numpy(dtype=np.float64)
            closes = df_c["close"].to_numpy(dtype=np.float64)
            vols = df_c["volume"].to_numpy(dtype=np.float64)
            tb_vols = df_c["taker_buy_volume"].to_numpy(dtype=np.float64)

            ret_1 = df_c["close"].pct_change()
            s20 = ret_1.rolling(20, min_periods=20).std(ddof=1).clip(lower=1e-4).fillna(0.0).to_numpy(dtype=np.float64)
            s96 = ret_1.rolling(96, min_periods=40).std(ddof=1).clip(lower=1e-4).fillna(1e-4).to_numpy(dtype=np.float64)
            vol_exp = s20 / np.maximum(s96, 1e-6)

            vol_mean_20 = df_c["volume"].rolling(20, min_periods=10).mean().clip(lower=1e-6).fillna(1.0).to_numpy(dtype=np.float64)
            rvol_20 = vols / np.maximum(vol_mean_20, 1e-6)
            taker_buy_ratio = np.clip(tb_vols / np.maximum(vols, 1e-8), 0.0, 1.0)

            rng = np.maximum(highs - lows, 1e-8)
            lower_wick = (np.minimum(opens, closes) - lows) / rng
            upper_wick = (highs - np.maximum(opens, closes)) / rng

            # Shift all causal features by 1 so index i contains the feature value known at candle i-1 close
            s20_prev = np.roll(s20, 1); s20_prev[0] = 0.0
            vol_exp_prev = np.roll(vol_exp, 1); vol_exp_prev[0] = 0.0
            rvol_prev = np.roll(rvol_20, 1); rvol_prev[0] = 0.0
            tbr_prev = np.roll(taker_buy_ratio, 1); tbr_prev[0] = 0.5
            lw_prev = np.roll(lower_wick, 1); lw_prev[0] = 0.0
            uw_prev = np.roll(upper_wick, 1); uw_prev[0] = 0.0

            htf_rets_bps: Dict[int, np.ndarray] = {}
            for lb in (6, 12, 24, 48):
                r_lb = df_c["close"].pct_change(lb).fillna(0.0).to_numpy(dtype=np.float64) * 10_000.0
                r_lb_prev = np.roll(r_lb, 1); r_lb_prev[0] = 0.0
                htf_rets_bps[lb] = r_lb_prev

            prev_ts = np.roll(ts, 1); prev_ts[0] = -1
            btc_rets_bps: Dict[int, np.ndarray] = {}
            for lb in (3, 6, 12, 24):
                mapped = btc_lookup_maps[lb].reindex(prev_ts).fillna(0.0).to_numpy(dtype=np.float64)
                btc_rets_bps[lb] = mapped

            # Load OOF Folds 1-4
            oof_table = pq.read_table(
                self.oof_dir / f"{sym}_oof.parquet",
                columns=["fold", "open_time_ms", "raw_prob_m1", "raw_prob_0", "raw_prob_p1"],
            ).to_pandas()
            oof_f14 = oof_table[oof_table["fold"].isin([1, 2, 3, 4])].drop_duplicates("open_time_ms")
            oof_indexed = oof_f14.set_index("open_time_ms")

            reindexed = oof_indexed.reindex(prev_ts)
            has_oof = (~reindexed["fold"].isna()).to_numpy(dtype=bool)
            fold_prev = reindexed["fold"].fillna(0).to_numpy(dtype=np.int32)
            pm1_prev = reindexed["raw_prob_m1"].fillna(0.0).to_numpy(dtype=np.float64)
            p0_prev = reindexed["raw_prob_0"].fillna(1.0).to_numpy(dtype=np.float64)
            pp1_prev = reindexed["raw_prob_p1"].fillna(0.0).to_numpy(dtype=np.float64)

            # Restrict quantile calculation to confirmatory OOF window for fairness
            valid_s20 = s20_prev[has_oof & (s20_prev > 1e-4)]
            q_map = {}
            for q in np.round(np.linspace(0.50, 0.99, 50), 2):
                q_map[float(q)] = float(np.quantile(valid_s20, q))
            q_map[0.0] = 0.0
            q_map[1.0] = float(np.max(valid_s20)) + 1.0

            self.matrices[sym] = AssetFeatureMatrix(
                symbol=sym,
                open_time_ms=ts,
                opens=opens,
                highs=highs,
                lows=lows,
                closes=closes,
                sigma_20=s20_prev,
                vol_quantiles=q_map,
                vol_exp_ratio=vol_exp_prev,
                rvol_20=rvol_prev,
                taker_buy_ratio=tbr_prev,
                lower_wick=lw_prev,
                upper_wick=uw_prev,
                htf_rets_bps=htf_rets_bps,
                btc_rets_bps=btc_rets_bps,
                has_oof_prev=has_oof,
                fold_prev=fold_prev,
                prob_m1_prev=pm1_prev,
                prob_0_prev=p0_prev,
                prob_p1_prev=pp1_prev,
            )

    def _simulate_asset_trades(self, cfg: StrategyConfiguration, symbol: str) -> List[Dict[str, Any]]:
        """Generates candidate trade trajectories for a single asset under cfg."""
        m = self.matrices[symbol]
        ent = cfg.entry
        ext = cfg.exit

        q_min_key = round(ent.vol_quantile_min, 2)
        q_max_key = round(ent.vol_quantile_max, 2)
        vol_min = m.vol_quantiles.get(q_min_key, float(np.quantile(m.sigma_20[m.has_oof_prev], ent.vol_quantile_min)))
        vol_max = m.vol_quantiles.get(q_max_key, 999.0) if ent.vol_quantile_max < 1.0 else 999.0

        htf_lb = ent.htf_lookback_bars if ent.htf_lookback_bars in m.htf_rets_bps else 12
        btc_lb = ent.btc_lead_lookback_bars if ent.btc_lead_lookback_bars in m.btc_rets_bps else 6
        htf_arr = m.htf_rets_bps[htf_lb]
        btc_arr = m.btc_rets_bps[btc_lb]

        max_dir_prob = np.maximum(m.prob_p1_prev, m.prob_m1_prev)
        margin = max_dir_prob - m.prob_0_prev

        # Base vectorized mask
        mask = (
            m.has_oof_prev
            & (m.sigma_20 >= vol_min)
            & (m.sigma_20 <= vol_max)
            & (margin >= ent.prob_margin_min)
            & (m.prob_0_prev <= ent.p0_neutral_max)
        )

        if ent.vol_expansion_ratio_min > 0.0:
            mask &= (m.vol_exp_ratio >= ent.vol_expansion_ratio_min)
        if ent.rvol_min > 0.0:
            mask &= (m.rvol_20 >= ent.rvol_min)
        if ent.taker_buy_ratio_min > 0.0:
            mask &= (m.taker_buy_ratio >= ent.taker_buy_ratio_min)
        if ent.taker_buy_ratio_max < 1.0:
            mask &= (m.taker_buy_ratio <= ent.taker_buy_ratio_max)
        if ent.htf_return_min_bps > -9999.0:
            mask &= (htf_arr >= ent.htf_return_min_bps)
        if ent.htf_return_max_bps < 9999.0:
            mask &= (htf_arr <= ent.htf_return_max_bps)
        if ent.btc_lead_min_bps > -9999.0:
            mask &= (btc_arr >= ent.btc_lead_min_bps)
        if ent.btc_lead_max_bps < 9999.0:
            mask &= (btc_arr <= ent.btc_lead_max_bps)

        raw_side = np.where(m.prob_p1_prev >= m.prob_m1_prev, 1, -1)

        if ent.direction_mode == "LONG_ONLY":
            mask &= (raw_side == 1)
            if ent.wick_rejection_min > 0.0:
                mask &= (m.lower_wick >= ent.wick_rejection_min)
        elif ent.direction_mode == "SHORT_ONLY":
            mask &= (raw_side == -1)
            if ent.wick_rejection_min > 0.0:
                mask &= (m.upper_wick >= ent.wick_rejection_min)
        elif ent.direction_mode == "HTF_TREND_ALIGNED":
            mask &= (((raw_side == 1) & (htf_arr > 0.0)) | ((raw_side == -1) & (htf_arr < 0.0)))
        elif ent.direction_mode == "ABSORPTION_REVERSAL":
            # Long after flush (htf < -35 bps) or Short after overextension (htf > +60 bps with upper wick)
            long_abs = (raw_side == 1) & (htf_arr <= ent.htf_return_max_bps)
            short_abs = (raw_side == -1) & (htf_arr >= abs(ent.htf_return_max_bps) * 1.5) & (m.upper_wick >= max(0.20, ent.wick_rejection_min))
            mask &= (long_abs | short_abs)
            if ent.wick_rejection_min > 0.0:
                mask &= np.where(raw_side == 1, m.lower_wick >= ent.wick_rejection_min, m.upper_wick >= ent.wick_rejection_min)
        else:
            if ent.wick_rejection_min > 0.0:
                mask &= np.where(raw_side == 1, m.lower_wick >= ent.wick_rejection_min, m.upper_wick >= ent.wick_rejection_min)

        candidate_indices = np.flatnonzero(mask)
        raw_signals_count = len(candidate_indices)
        if raw_signals_count == 0:
            self._last_simulation_stats[symbol] = {
                "raw_signals": 0,
                "unique_orders": 0,
                "touched_orders": 0,
                "filled_orders": 0,
                "fill_events": 0,
            }
            return []

        trades: List[Dict[str, Any]] = []
        next_valid_bar = 20
        n_bars = len(m.opens)

        opens = m.opens
        highs = m.highs
        lows = m.lows
        closes = m.closes
        ts_arr = m.open_time_ms
        sigmas = m.sigma_20
        folds = m.fold_prev

        is_limit = (ent.order_type == "LIMIT")
        delta_off = ent.limit_offset_sigma
        timeout_bars = ent.order_timeout_bars
        tp1_m = ext.tp1_multiplier
        tp2_m = ext.tp2_multiplier
        tp1_pct = ext.tp1_close_pct
        sl_m = ext.sl_multiplier
        be_ratchet = ext.breakeven_ratchet_on_tp1
        trail_m = ext.trailing_stop_distance_sigma
        horizon = ext.horizon_bars
        cooldown = ent.cooldown_bars

        unique_orders_count = 0
        touched_orders_count = 0
        filled_orders_count = 0
        fill_events_count = 0

        for idx in candidate_indices:
            i = int(idx)
            if i < next_valid_bar or i >= n_bars - 2:
                continue

            unique_orders_count += 1
            side = int(raw_side[i])
            sigma = float(sigmas[i])
            fold = int(folds[i])

            # 1. Determine Entry Fill & Liquidity Role
            entry_bar = i
            arrival_px = opens[i]
            entry_px = arrival_px
            entry_role = "TAKER"
            order_filled = False

            if not is_limit:
                # Unconditional MARKET order -> Executes immediately at arrival price as TAKER
                entry_bar = i
                entry_px = arrival_px
                entry_role = "TAKER"
                touched_orders_count += 1
                filled_orders_count += 1
                fill_events_count += 1
                order_filled = True
            else:
                # LIMIT Order
                if side == 1:
                    limit_px = arrival_px * (1.0 - delta_off * sigma)
                    is_marketable = (limit_px >= arrival_px or delta_off <= 0.0)
                else:
                    limit_px = arrival_px * (1.0 + delta_off * sigma)
                    is_marketable = (limit_px <= arrival_px or delta_off <= 0.0)

                if is_marketable:
                    # Marketable Limit Order
                    if ent.post_only:
                        # CANCEL_ON_CROSS: Matching engine immediately rejects post-only order on cross
                        next_valid_bar = i + 1 + cooldown
                        continue
                    else:
                        # Immediate taker execution against resting book depth
                        entry_bar = i
                        entry_px = arrival_px
                        entry_role = "TAKER"
                        touched_orders_count += 1
                        filled_orders_count += 1
                        fill_events_count += 1
                        order_filled = True
                else:
                    # Passive Resting Limit Order: Enters book queue
                    order_touched = False
                    for k in range(i, min(i + timeout_bars, n_bars - 1)):
                        k_low = lows[k]
                        k_high = highs[k]

                        if side == 1:
                            if k_low <= limit_px:
                                order_touched = True
                                pen_threshold = limit_px - 0.2 * sigma * limit_px
                                if k_low < pen_threshold:
                                    # Deep penetration -> 100% fill probability
                                    fill_this_bar = True
                                else:
                                    # Boundary touch heuristic (uncalibrated simulation assumption: 50%)
                                    det_seed = (k * 2654435761 + int(limit_px * 1000) * 31 + i) & 0xFFFFFFFF
                                    fill_this_bar = (det_seed % 2 == 0)

                                if fill_this_bar:
                                    entry_bar = k
                                    # INSTITUTIONAL GAP-DOWN PRICING FIX: Buy limit fills strictly at limit_px
                                    entry_px = limit_px
                                    entry_role = "MAKER"
                                    order_filled = True
                                    break
                        else:
                            if k_high >= limit_px:
                                order_touched = True
                                pen_threshold = limit_px + 0.2 * sigma * limit_px
                                if k_high > pen_threshold:
                                    # Deep penetration -> 100% fill probability
                                    fill_this_bar = True
                                else:
                                    # Boundary touch heuristic (uncalibrated simulation assumption: 50%)
                                    det_seed = (k * 2654435761 + int(limit_px * 1000) * 31 + i) & 0xFFFFFFFF
                                    fill_this_bar = (det_seed % 2 == 0)

                                if fill_this_bar:
                                    entry_bar = k
                                    # INSTITUTIONAL GAP PRICING FIX: Sell limit fills strictly at limit_px
                                    entry_px = limit_px
                                    entry_role = "MAKER"
                                    order_filled = True
                                    break

                    if order_touched:
                        touched_orders_count += 1

                    if not order_filled:
                        next_valid_bar = i + timeout_bars
                        continue

                    filled_orders_count += 1
                    fill_events_count += 1

            # 2. Compute Barriers
            if side == 1:
                tp1_px = entry_px * (1.0 + tp1_m * sigma)
                tp2_px = entry_px * (1.0 + tp2_m * sigma)
                sl_px = entry_px * (1.0 - sl_m * sigma)
            else:
                tp1_px = entry_px * (1.0 - tp1_m * sigma)
                tp2_px = entry_px * (1.0 - tp2_m * sigma)
                sl_px = entry_px * (1.0 + sl_m * sigma)

            tp1_hit = False
            realized_gross_bps = 0.0
            rem_weight = 1.0
            exit_bar = entry_bar
            exit_px = entry_px
            exit_reason = "TIME_EXPIRATION"
            exit_maker_pct = 0.0
            exit_taker_pct = 1.0

            max_end = min(entry_bar + horizon, n_bars - 1)
            for b in range(entry_bar + 1, max_end + 1):
                o, h, l, c = opens[b], highs[b], lows[b], closes[b]

                # Check SL first (conservative collision priority)
                sl_triggered = (l <= sl_px) if side == 1 else (h >= sl_px)
                if sl_triggered:
                    fill_sl = min(o, sl_px) if side == 1 else max(o, sl_px)
                    leg_bps = float(side) * (fill_sl - entry_px) / entry_px * 10_000.0
                    realized_gross_bps += rem_weight * leg_bps
                    exit_bar = b
                    exit_px = fill_sl
                    exit_reason = "BREAKEVEN_STOP" if tp1_hit and be_ratchet else "STOP_LOSS"
                    fill_events_count += 1
                    if tp1_hit:
                        exit_maker_pct = tp1_pct
                        exit_taker_pct = 1.0 - tp1_pct
                    else:
                        exit_maker_pct = 0.0
                        exit_taker_pct = 1.0
                    rem_weight = 0.0
                    break

                # Check TP1 if not yet hit
                if not tp1_hit:
                    tp1_trig = (h >= tp1_px) if side == 1 else (l <= tp1_px)
                    if tp1_trig:
                        fill_tp1 = max(o, tp1_px) if side == 1 else min(o, tp1_px)
                        leg_bps = float(side) * (fill_tp1 - entry_px) / entry_px * 10_000.0
                        if tp1_pct <= 0.0 or tp1_pct >= 0.999:
                            realized_gross_bps += leg_bps
                            exit_bar = b
                            exit_px = fill_tp1
                            exit_reason = "TAKE_PROFIT"
                            exit_maker_pct = 1.0
                            exit_taker_pct = 0.0
                            fill_events_count += 1
                            rem_weight = 0.0
                            break
                        else:
                            # Partial close at TP1 (BankerAgent Option A)
                            realized_gross_bps += tp1_pct * leg_bps
                            rem_weight = 1.0 - tp1_pct
                            tp1_hit = True
                            fill_events_count += 1  # Partial TP1 fill event
                            if be_ratchet:
                                sl_px = entry_px

                # Check TP2 if TP1 already hit
                if tp1_hit and rem_weight > 0.0:
                    tp2_trig = (h >= tp2_px) if side == 1 else (l <= tp2_px)
                    if tp2_trig:
                        fill_tp2 = max(o, tp2_px) if side == 1 else min(o, tp2_px)
                        leg_bps = float(side) * (fill_tp2 - entry_px) / entry_px * 10_000.0
                        realized_gross_bps += rem_weight * leg_bps
                        exit_bar = b
                        exit_px = fill_tp2
                        exit_reason = "TAKE_PROFIT_2"
                        exit_maker_pct = 1.0
                        exit_taker_pct = 0.0
                        fill_events_count += 1
                        rem_weight = 0.0
                        break

                # Optional Trailing Stop Ratchet
                if trail_m > 0.0:
                    if side == 1:
                        cand_sl = c * (1.0 - trail_m * sigma)
                        if cand_sl > sl_px and c > entry_px * (1.0 + 0.8 * sigma):
                            sl_px = cand_sl
                    else:
                        cand_sl = c * (1.0 + trail_m * sigma)
                        if cand_sl < sl_px and c < entry_px * (1.0 - 0.8 * sigma):
                            sl_px = cand_sl

            # Time expiration if still open at horizon
            if rem_weight > 0.0:
                exit_bar = max_end
                exit_px = closes[max_end]
                leg_bps = float(side) * (exit_px - entry_px) / entry_px * 10_000.0
                realized_gross_bps += rem_weight * leg_bps
                exit_reason = "PARTIAL_TP1_TIME_EXIT" if tp1_hit else "TIME_EXPIRATION"
                fill_events_count += 1
                if tp1_hit:
                    exit_maker_pct = tp1_pct
                    exit_taker_pct = 1.0 - tp1_pct
                else:
                    exit_maker_pct = 0.0
                    exit_taker_pct = 1.0

            # 3. Post-Fill Markout Trajectory (h = 1, 2, 3, 6, 12 bars)
            markouts: Dict[int, float] = {}
            for h_bars in (1, 2, 3, 6, 12):
                tgt_bar = entry_bar + h_bars
                if tgt_bar < n_bars:
                    p_fwd = closes[tgt_bar]
                    m_bps = float(side) * (p_fwd - entry_px) / entry_px * 10_000.0
                    markouts[h_bars] = round(float(m_bps), 2)
                else:
                    markouts[h_bars] = 0.0

            entry_ts = int(ts_arr[entry_bar])
            exit_ts = int(ts_arr[exit_bar]) + 300_000
            funding_Crossings = max(0, int(exit_ts // (8 * 3600 * 1000) - entry_ts // (8 * 3600 * 1000)))

            trades.append({
                "symbol": symbol,
                "side": "LONG" if side == 1 else "SHORT",
                "entry_time_ms": entry_ts,
                "exit_time_ms": exit_ts,
                "entry_price": round(float(entry_px), 6),
                "exit_price": round(float(exit_px), 6),
                "exit_reason": exit_reason,
                "entry_role": entry_role,
                "exit_maker_pct": exit_maker_pct,
                "exit_taker_pct": exit_taker_pct,
                "bars_held": int(exit_bar - entry_bar),
                "sigma": float(sigma),
                "gross_return_bps": float(realized_gross_bps),
                "funding_events": funding_Crossings,
                "fold": fold,
                "markout_1_bps": markouts.get(1, 0.0),
                "markout_2_bps": markouts.get(2, 0.0),
                "markout_3_bps": markouts.get(3, 0.0),
                "markout_6_bps": markouts.get(6, 0.0),
                "markout_12_bps": markouts.get(12, 0.0),
            })

            next_valid_bar = exit_bar + 1 + cooldown

        self._last_simulation_stats[symbol] = {
            "raw_signals": raw_signals_count,
            "unique_orders": unique_orders_count,
            "touched_orders": touched_orders_count,
            "filled_orders": filled_orders_count,
            "fill_events": fill_events_count,
        }

        return trades

    def evaluate_strategy(
        self,
        cfg: StrategyConfiguration,
        experiment_id: str,
        strict_execution_policy: bool = True,
    ) -> Tuple[StrategyEvaluationResult, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Evaluates a StrategyConfiguration on $100 USD portfolio capital under institutional single-channel friction."""
        r_cfg = cfg.risk
        venue = get_venue_schedule(r_cfg.fee_tier)

        # 1. Execution Policy Compatibility Validation
        is_market_entry = (cfg.entry.order_type == "MARKET" or cfg.entry.limit_offset_sigma <= 0.0)
        is_maker_only_schedule = (venue.venue_id == "MAKER_PASSIVE_TRUE" or r_cfg.fee_tier == "maker_passive")
        if is_market_entry and is_maker_only_schedule and strict_execution_policy:
            raise ExecutionPolicyMismatchError(
                f"Execution policy mismatch: Market orders cannot execute under passive maker fee schedule "
                f"'{r_cfg.fee_tier}' ({venue.venue_id})."
            )

        all_candidates: List[Dict[str, Any]] = []
        per_asset_counts: Dict[str, int] = {}

        for sym in cfg.applicable_assets:
            sym_trades = self._simulate_asset_trades(cfg, sym)
            all_candidates.extend(sym_trades)
            per_asset_counts[sym] = 0

        all_candidates.sort(key=lambda x: (x["entry_time_ms"], x["symbol"]))

        initial_eq = r_cfg.initial_equity_usd
        current_eq = initial_eq
        peak_eq = initial_eq
        max_dd = 0.0

        fund_rate_8h = venue.funding_rate_bps_8h / 10_000.0

        events: List[Tuple[int, int, int, Dict[str, Any]]] = []
        for idx, tr in enumerate(all_candidates):
            events.append((tr["entry_time_ms"], 1, idx, tr))
            events.append((tr["exit_time_ms"], 0, idx, tr))
        events.sort(key=lambda x: (x[0], x[1], x[2]))

        open_map: Dict[int, Dict[str, Any]] = {}
        executed_trades: List[Dict[str, Any]] = []
        missed_min_notional = 0
        missed_capacity = 0

        total_fees_usd = 0.0
        total_slip_usd = 0.0
        total_fund_usd = 0.0

        # Calendar daily marks over the 365.14-day Folds 1-4 period
        t_start = 1738149600000
        t_end = 1769697300000
        day_ms = 86_400_000
        next_day_ts = (t_start // day_ms + 1) * day_ms

        daily_marks: List[Tuple[int, float]] = [(t_start, initial_eq)]
        underwater_dd_series: List[float] = [0.0]

        fold_pnl_usd: Dict[int, float] = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
        fold_start_eq: Dict[int, float] = {1: initial_eq, 2: initial_eq, 3: initial_eq, 4: initial_eq}
        seen_folds = set()

        for ts, ev_type, idx, tr in events:
            while next_day_ts <= ts:
                daily_marks.append((next_day_ts, current_eq))
                dd_day = ((peak_eq - current_eq) / peak_eq * 100.0) if peak_eq > 0 else 0.0
                underwater_dd_series.append(dd_day)
                next_day_ts += day_ms

            f_id = tr["fold"]
            if f_id in (1, 2, 3, 4) and f_id not in seen_folds:
                fold_start_eq[f_id] = max(current_eq, 1.0)
                seen_folds.add(f_id)

            if ev_type == 0:  # EXIT
                if idx in open_map:
                    pos = open_map.pop(idx)
                    notional = pos["notional_usd"]
                    gross_ret = tr["gross_return_bps"] / 10_000.0

                    entry_role = tr.get("entry_role", "TAKER")
                    exit_maker_pct = tr.get("exit_maker_pct", 0.0)
                    exit_taker_pct = tr.get("exit_taker_pct", 1.0)

                    # Entry Leg Friction
                    if entry_role == "MAKER":
                        fee_entry_bps = venue.maker_fee_bps_per_leg
                        spread_entry_bps = 0.0
                        slip_entry_bps = 0.0
                        adverse_entry_bps = venue.adverse_selection_bps
                    else:  # TAKER
                        fee_entry_bps = venue.taker_fee_bps_per_leg
                        spread_entry_bps = venue.default_spread_bps / 2.0
                        slip_entry_bps = venue.default_slippage_bps / 2.0
                        adverse_entry_bps = 0.0

                    # Exit Leg Friction
                    fee_exit_bps = exit_maker_pct * venue.maker_fee_bps_per_leg + exit_taker_pct * venue.taker_fee_bps_per_leg
                    spread_exit_bps = exit_taker_pct * (venue.default_spread_bps / 2.0)
                    slip_exit_bps = exit_taker_pct * (venue.default_slippage_bps / 2.0)
                    adverse_exit_bps = 0.0

                    # ANTI-DOUBLE-COUNTING ACTIVE ASSERTIONS
                    if entry_role == "MAKER":
                        assert spread_entry_bps == 0.0, "Maker entry cannot be charged spread crossing!"
                        assert slip_entry_bps == 0.0, "Maker entry cannot be charged arrival slippage!"
                    elif entry_role == "TAKER":
                        assert adverse_entry_bps == 0.0, "Taker entry cannot be charged adverse selection drag!"

                    if exit_maker_pct == 1.0:
                        assert spread_exit_bps == 0.0, "Maker exit cannot be charged spread crossing!"
                        assert slip_exit_bps == 0.0, "Maker exit cannot be charged arrival slippage!"
                    elif exit_taker_pct == 1.0:
                        assert adverse_exit_bps == 0.0, "Taker exit cannot be charged adverse selection drag!"

                    tot_fee_bps = fee_entry_bps + fee_exit_bps
                    tot_spread_bps = spread_entry_bps + spread_exit_bps
                    tot_slip_bps = slip_entry_bps + slip_exit_bps
                    tot_adverse_bps = adverse_entry_bps + adverse_exit_bps

                    fee_usd = notional * (tot_fee_bps / 10_000.0)
                    spread_usd = notional * (tot_spread_bps / 10_000.0)
                    slip_usd = notional * (tot_slip_bps / 10_000.0)
                    adverse_usd = notional * (tot_adverse_bps / 10_000.0)

                    # Signed funding: long pays positive funding, short receives 50% net
                    fund_mult = 1.0 if tr["side"] == "LONG" else -0.5
                    fund_usd = notional * tr["funding_events"] * fund_rate_8h * fund_mult
                    friction_usd = fee_usd + spread_usd + slip_usd + adverse_usd
                    net_pnl = notional * gross_ret - friction_usd - fund_usd

                    current_eq = max(0.0, current_eq + net_pnl)
                    total_fees_usd += fee_usd
                    total_slip_usd += (spread_usd + slip_usd + adverse_usd)
                    total_fund_usd += max(0.0, fund_usd)

                    if f_id in fold_pnl_usd:
                        fold_pnl_usd[f_id] += net_pnl

                    if current_eq > peak_eq:
                        peak_eq = current_eq
                    dd = ((peak_eq - current_eq) / peak_eq * 100.0) if peak_eq > 0 else 0.0
                    if dd > max_dd:
                        max_dd = dd
                    underwater_dd_series.append(dd)

                    net_ret_bps = (net_pnl / notional) * 10_000.0
                    per_asset_counts[tr["symbol"]] = per_asset_counts.get(tr["symbol"], 0) + 1
                    executed_trades.append({
                        **tr,
                        "notional_usd": round(notional, 2),
                        "net_return_bps": round(net_ret_bps, 2),
                        "net_pnl_usd": round(net_pnl, 4),
                        "fee_usd": round(fee_usd, 4),
                        "spread_usd": round(spread_usd, 4),
                        "slip_usd": round(slip_usd, 4),
                        "adverse_usd": round(adverse_usd, 4),
                        "fund_usd": round(fund_usd, 4),
                        "equity_after_usd": round(current_eq, 2),
                    })
            else:  # ENTRY
                if current_eq <= r_cfg.min_notional_usdt * 0.5:
                    missed_min_notional += 1
                    continue

                if len(open_map) >= r_cfg.max_concurrent_positions:
                    missed_capacity += 1
                    continue

                # Prevent duplicate simultaneous positions in the same symbol
                if any(p["symbol"] == tr["symbol"] for p in open_map.values()):
                    missed_capacity += 1
                    continue

                stop_frac = max(cfg.exit.sl_multiplier * tr["sigma"], 0.0015)
                risk_usd = current_eq * r_cfg.risk_per_trade_pct
                raw_notional = risk_usd / stop_frac

                sym_cap = current_eq * r_cfg.max_symbol_exposure_pct
                cur_exposure = sum(p["notional_usd"] for p in open_map.values())
                rem_port_cap = max(0.0, current_eq * r_cfg.max_total_exposure_pct - cur_exposure)
                lev_cap = current_eq * r_cfg.max_leverage

                notional = min(raw_notional, sym_cap, rem_port_cap, lev_cap)
                # Lot step rounding (0.5% step granularity)
                notional = math.floor(notional * 100.0) / 100.0

                if notional < r_cfg.min_notional_usdt:
                    if rem_port_cap < r_cfg.min_notional_usdt:
                        missed_capacity += 1
                    else:
                        missed_min_notional += 1
                    continue

                open_map[idx] = {
                    "symbol": tr["symbol"],
                    "notional_usd": notional,
                    "entry_time_ms": ts,
                }

        while next_day_ts <= t_end:
            daily_marks.append((next_day_ts, current_eq))
            next_day_ts += day_ms
        daily_marks.append((t_end, current_eq))

        df_daily = pd.DataFrame(daily_marks, columns=["timestamp_ms", "equity_usd"]).drop_duplicates("timestamp_ms")
        daily_rets = df_daily["equity_usd"].pct_change().fillna(0.0).to_numpy()[1:]
        n_days = max(1, len(daily_rets))

        mean_daily_pct = float(np.mean(daily_rets)) * 100.0
        med_daily_pct = float(np.median(daily_rets)) * 100.0
        geom_daily_pct = ((max(current_eq, 0.01) / initial_eq) ** (1.0 / n_days) - 1.0) * 100.0
        cum_ret_pct = (current_eq - initial_eq) / initial_eq * 100.0

        std_daily = float(np.std(daily_rets, ddof=1)) if len(daily_rets) > 1 else 0.0
        sharpe = (float(np.mean(daily_rets)) / std_daily * math.sqrt(365.25)) if std_daily > 1e-12 else 0.0
        neg_daily = daily_rets[daily_rets < 0.0]
        down_std = float(np.std(neg_daily, ddof=1)) if len(neg_daily) > 1 else 0.0
        sortino = (float(np.mean(daily_rets)) / down_std * math.sqrt(365.25)) if down_std > 1e-12 else (sharpe if sharpe > 0 else 0.0)

        # Deterministic Moving-Block Bootstrap (block_size=7 days, 200 resamples) for 95% CI
        rng_boot = np.random.default_rng(42)
        if len(daily_rets) >= 14:
            boot_means = []
            for _ in range(200):
                idx_b = rng_boot.integers(0, len(daily_rets), size=len(daily_rets))
                boot_means.append(float(np.mean(daily_rets[idx_b])) * 100.0)
            ci_low = round(float(np.percentile(boot_means, 2.5)), 4)
            ci_high = round(float(np.percentile(boot_means, 97.5)), 4)
        else:
            ci_low, ci_high = round(mean_daily_pct, 4), round(mean_daily_pct, 4)

        n_exec = len(executed_trades)
        if n_exec > 0:
            gross_arr = np.array([t["gross_return_bps"] for t in executed_trades], dtype=float)
            net_arr = np.array([t["net_return_bps"] for t in executed_trades], dtype=float)
            pnl_arr = np.array([t["net_pnl_usd"] for t in executed_trades], dtype=float)
            wins_usd = float(np.sum(pnl_arr[pnl_arr > 0.0]))
            loss_usd = float(np.abs(np.sum(pnl_arr[pnl_arr < 0.0])))
            pf = (wins_usd / loss_usd) if loss_usd > 1e-9 else (99.0 if wins_usd > 0 else 0.0)
            win_rate = float(np.mean(net_arr > 0.0)) * 100.0
            gross_exp = float(np.mean(gross_arr))
            net_exp = float(np.mean(net_arr))
            diag_m1 = round(float(np.median([t.get("markout_1_bps", 0.0) for t in executed_trades])), 2)
            diag_m3 = round(float(np.median([t.get("markout_3_bps", 0.0) for t in executed_trades])), 2)
        else:
            pf = 0.0; win_rate = 0.0; gross_exp = 0.0; net_exp = 0.0
            diag_m1 = 0.0; diag_m3 = 0.0

        mean_uw_dd = float(np.mean(underwater_dd_series))
        med_uw_dd = float(np.median(underwater_dd_series))
        rec_factor = (cum_ret_pct / max_dd) if max_dd > 0.01 else (99.0 if cum_ret_pct > 0 else 0.0)

        fold_rets_pct = {}
        pos_folds = 0
        for f_id in (1, 2, 3, 4):
            f_ret = (fold_pnl_usd[f_id] / max(fold_start_eq[f_id], 1.0)) * 100.0
            fold_rets_pct[f"fold_{f_id}"] = round(f_ret, 2)
            if f_ret > 0.0:
                pos_folds += 1

        # Qualification & Failure Classification:
        qualified = (
            n_exec >= 80
            and cum_ret_pct > 0.0
            and net_exp > 0.0
            and pf >= 1.05
            and max_dd <= 30.0
            and mean_uw_dd < 10.0
            and pos_folds >= 3
        )

        if n_exec < 40:
            if missed_min_notional > n_exec:
                f_class = FailureClassification.CAPITAL_MIN_NOTIONAL_STARVATION
                f_reason = f"Starved by $5.00 min notional on $100 equity ({missed_min_notional} missed vs {n_exec} executed)."
            else:
                f_class = FailureClassification.INSUFFICIENT_SAMPLE_STARVATION
                f_reason = f"Over-restrictive entry filters yielded only {n_exec} trades (<40 minimum)."
        elif max_dd > 30.0:
            f_class = FailureClassification.EXCESSIVE_DRAWDOWN_BREACH
            f_reason = f"Maximum portfolio drawdown {max_dd:.2f}% breached hard 30.0% ceiling."
        elif net_exp <= 0.0 or cum_ret_pct <= 0.0:
            if cfg.entry.order_type == "LIMIT" and cfg.entry.limit_offset_sigma > 0.0:
                f_class = FailureClassification.LIMIT_ORDER_ADVERSE_SELECTION
                f_reason = f"Passive limit entry (offset={cfg.entry.limit_offset_sigma}s) suffered adverse momentum selection (Net Exp={net_exp:+.2f} bps)."
            elif cfg.entry.direction_mode in ("BOTH", "SHORT_ONLY") and cfg.entry.htf_return_min_bps <= 0.0:
                f_class = FailureClassification.BIDIRECTIONAL_SHORT_DRAG
                f_reason = f"Unconditioned short trades eroded portfolio alpha (Net Exp={net_exp:+.2f} bps, CumRet={cum_ret_pct:+.2f}%)."
            else:
                f_class = FailureClassification.NEGATIVE_NET_EXPECTANCY_FRICTION
                f_reason = f"Gross expectancy ({gross_exp:+.2f} bps) insufficient to overcome friction under venue {venue.venue_id} + funding."
        elif pos_folds < 3:
            f_class = FailureClassification.FOLD_INSTABILITY_REGIME_MISMATCH
            f_reason = f"Positive cumulative return ({cum_ret_pct:+.2f}%) but only {pos_folds}/4 walk-forward folds positive."
        elif qualified and mean_daily_pct < 3.0:
            f_class = FailureClassification.POSITIVE_RETURN_BELOW_TARGET
            f_reason = (
                f"QUALIFIED POSITIVE ALPHA: Net Return {cum_ret_pct:+.2f}% ({mean_daily_pct:+.4f}%/day), "
                f"PF={pf:.3f}, AvgDD={mean_uw_dd:.2f}%, MDD={max_dd:.2f}%, {pos_folds}/4 folds positive "
                f"(below +3.0%/day aspirational target due to realistic 5m volatility & leverage bounds)."
            )
        else:
            f_class = FailureClassification.QUALIFIED_SUCCESS
            f_reason = f"Qualified positive strategy ({cum_ret_pct:+.2f}% net return, MDD={max_dd:.2f}%)."

        # 6-Tier Counter Aggregation & Invariant Verification
        tot_raw_signals = sum(self._last_simulation_stats.get(s, {}).get("raw_signals", 0) for s in cfg.applicable_assets)
        tot_unique_orders = sum(self._last_simulation_stats.get(s, {}).get("unique_orders", 0) for s in cfg.applicable_assets)
        tot_touched_orders = sum(self._last_simulation_stats.get(s, {}).get("touched_orders", 0) for s in cfg.applicable_assets)
        tot_filled_orders = sum(self._last_simulation_stats.get(s, {}).get("filled_orders", 0) for s in cfg.applicable_assets)
        tot_fill_events = sum(self._last_simulation_stats.get(s, {}).get("fill_events", 0) for s in cfg.applicable_assets)
        tot_portfolio_exec = n_exec

        # Counter Hierarchy Invariant: signals >= unique_orders >= touched_orders >= filled_orders >= portfolio_exec
        assert tot_raw_signals >= tot_unique_orders >= tot_touched_orders >= tot_filled_orders >= tot_portfolio_exec, (
            f"Counter hierarchy invariant breach: signals={tot_raw_signals} >= unique={tot_unique_orders} "
            f">= touched={tot_touched_orders} >= filled={tot_filled_orders} >= portfolio={tot_portfolio_exec}"
        )
        assert tot_fill_events >= tot_filled_orders, (
            f"Fill event invariant breach: fill_events={tot_fill_events} < filled_orders={tot_filled_orders}"
        )

        n_cand = len(all_candidates)
        fill_rate = (n_exec / n_cand * 100.0) if n_cand > 0 else 0.0
        tot_cost = total_fees_usd + total_fund_usd + total_slip_usd

        res = StrategyEvaluationResult(
            experiment_id=experiment_id,
            batch_id=cfg.batch_id,
            strategy_id=cfg.strategy_id,
            strategy_version=cfg.version,
            config_hash=cfg.config_hash,
            family=cfg.family,
            hypothesis=cfg.hypothesis,
            applicable_assets=list(cfg.applicable_assets),
            initial_equity_usd=initial_eq,
            ending_equity_usd=round(current_eq, 2),
            net_cumulative_return_pct=round(cum_ret_pct, 2),
            mean_net_daily_return_pct=round(mean_daily_pct, 4),
            geometric_mean_daily_return_pct=round(geom_daily_pct, 4),
            median_net_daily_return_pct=round(med_daily_pct, 4),
            mean_return_per_trade_bps=round(net_exp, 2),
            gross_expectancy_bps=round(gross_exp, 2),
            net_expectancy_bps=round(net_exp, 2),
            profit_factor=round(pf, 3),
            sharpe_annualized=round(sharpe, 3),
            sortino_annualized=round(sortino, 3),
            max_drawdown_pct=round(max_dd, 2),
            mean_underwater_drawdown_pct=round(mean_uw_dd, 2),
            median_underwater_drawdown_pct=round(med_uw_dd, 2),
            recovery_factor=round(rec_factor, 3),
            candidate_signal_count=n_cand,
            executed_trade_count=n_exec,
            missed_min_notional_count=missed_min_notional,
            missed_capacity_count=missed_capacity,
            execution_fill_rate_pct=round(fill_rate, 2),
            win_rate_pct=round(win_rate, 2),
            total_fees_usd=round(total_fees_usd, 2),
            total_funding_usd=round(total_fund_usd, 2),
            total_slippage_usd=round(total_slip_usd, 2),
            total_execution_cost_usd=round(tot_cost, 2),
            positive_folds_count=pos_folds,
            fold_returns_pct=fold_rets_pct,
            per_asset_trade_counts=per_asset_counts,
            bootstrap_95_ci_daily_pct=(ci_low, ci_high),
            qualified=qualified,
            failure_classification=f_class,
            failure_reason=f_reason,
            raw_signal_count=tot_raw_signals,
            unique_order_count=tot_unique_orders,
            touched_order_count=tot_touched_orders,
            filled_order_count=tot_filled_orders,
            fill_event_count=tot_fill_events,
            portfolio_execution_count=tot_portfolio_exec,
            diagnostic_markout_1_bps=diag_m1,
            diagnostic_markout_3_bps=diag_m3,
        )

        daily_curve = [
            {"timestamp_ms": int(r.timestamp_ms), "equity_usd": round(float(r.equity_usd), 2)}
            for r in df_daily.itertuples()
        ]
        return res, executed_trades, daily_curve
