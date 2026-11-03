"""QUANTUM Next — HYP-01: Multi-Timeframe Volatility Expansion Trend Following.

Implements the experimental strategy architecture derived from Milestone 4 research findings:
1. Deterministic Point-in-Time Market Regime Detector (High-Vol Trend, High-Vol Range, Low-Vol Trend, Low-Vol Range).
2. Multi-Timeframe Trend & Momentum Alignment (1h Higher-Timeframe, 15m Intermediate, 5m Execution).
3. Volatility-Adjusted Wide Barrier Exit Engine (Solves 1-bar premature noise stop-out, Breakeven Ratchet, Trailing Stop).
4. Independent Risk Management (Volatility sizing, Max leverage 3x, Daily loss circuit breaker, Drawdown control).
5. Banker High-Fidelity Execution Simulator (Venue fee schedules, Maker vs Taker non-conflated accounting).
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from quantum.strategies.schemas import (
    ExecutionVenueSchedule,
    VENUE_PROFILES,
    get_venue_schedule,
)


class HYP01Configuration(BaseModel):
    """Full declarative configuration for HYP-01 strategy."""

    strategy_id: str = "HYP01_MTF_VOL_EXP_V1"
    version: str = "1.0.0"

    # Multi-Timeframe Parameters
    htf_trend_bars: int = Field(default=12, description="1h trend bar horizon (12x 5m bars)")
    itf_momentum_bars: int = Field(default=3, description="15m intermediate momentum horizon (3x 5m bars)")
    trend_threshold_bps: float = Field(default=75.0, description="Minimum absolute 1h return in bps for trend classification")
    vol_expansion_min: float = Field(default=1.05, description="Minimum volume/volatility expansion ratio")
    
    # Regime Filter Switches
    enable_regime_filter: bool = Field(default=True, description="Strictly trade only in HIGH_VOLATILITY_TRENDING")
    allow_long_entries: bool = Field(default=True, description="Allow long entries on confirmed uptrend")
    allow_short_entries: bool = Field(default=True, description="Allow short entries on confirmed downtrend")
    filter_altcoin_shorts: bool = Field(default=False, description="Filter short positions on altcoins to avoid short drag")

    # Entry & Execution Timing
    order_type: str = Field(default="MARKET", description="MARKET or LIMIT")
    limit_offset_sigma: float = Field(default=0.0, description="Limit offset from arrival price in sigmas")
    cooldown_bars: int = Field(default=3, description="Cooldown between successive trades on same symbol")

    # Volatility-Adjusted Exit Engine (Anti-Noise Solution)
    sl_multiplier: float = Field(default=2.5, description="Initial Stop-Loss in sigmas (widened to absorb 5m noise)")
    tp1_multiplier: float = Field(default=4.0, description="Take-Profit 1 in sigmas (~1.6x Risk)")
    tp2_multiplier: float = Field(default=7.5, description="Take-Profit 2 in sigmas (~3.0x Risk)")
    tp1_close_pct: float = Field(default=0.50, description="Fraction closed at TP1")
    enable_breakeven_ratchet: bool = Field(default=True, description="Move SL to entry price once TP1 is hit")
    trailing_stop_sigma: float = Field(default=2.0, description="Trailing stop distance in sigmas active after TP1")
    min_horizon_bars: int = Field(default=6, description="Minimum target holding duration (30 mins)")
    max_horizon_bars: int = Field(default=24, description="Maximum holding duration before time expiration (2 hours)")

    # Risk Management Parameters (Risk Agent Authority)
    risk_per_trade_pct: float = Field(default=0.015, description="Risk budget per trade (1.5% of equity)")
    max_leverage: float = Field(default=3.0, description="Hard cap on position leverage (max 3x)")
    max_concurrent_positions: int = Field(default=4, description="Maximum concurrent active positions across universe")
    max_symbol_exposure_pct: float = Field(default=0.25, description="Maximum capital allocated to any single symbol")
    daily_loss_circuit_breaker_pct: float = Field(default=0.04, description="Halts trading for 24h if daily loss hits 4%")
    max_drawdown_circuit_breaker_pct: float = Field(default=0.15, description="Halves position sizing if drawdown exceeds 15%")
    initial_equity_usd: float = Field(default=100.0, description="Starting portfolio equity")

    # Venue & Execution Assumption
    fee_tier: str = Field(default="BYBIT_VIP0_DEFAULT", description="Execution venue fee schedule key")

    @property
    def config_hash(self) -> str:
        """Deterministic SHA-256 hash of configuration parameters."""
        data_str = json.dumps(self.model_dump(), sort_keys=True)
        return hashlib.sha256(data_str.encode("utf-8")).hexdigest()[:16]


@dataclass
class HYP01RegimeDetector:
    """Point-in-time, deterministic market regime detector.
    
    Fits baseline thresholds strictly on Fold 0/1 training data and freezes them
    to prevent lookahead bias or validation leakage.
    """
    trend_threshold_bps: float = 75.0
    sigma_threshold: float = 0.0015
    vol_expansion_min: float = 1.05

    def classify_bar(
        self,
        sigma_20: float,
        htf_12_bps: float,
        vol_exp_ratio: float,
    ) -> Tuple[str, bool]:
        """Classifies a single bar into one of 4 mutually exclusive regimes point-in-time.
        
        Returns:
            Tuple of (regime_name, is_high_vol_trending)
        """
        is_high_vol = (sigma_20 >= self.sigma_threshold)
        is_trending = (abs(htf_12_bps) >= self.trend_threshold_bps) and (vol_exp_ratio >= self.vol_expansion_min)

        if is_high_vol and is_trending:
            return "HIGH_VOLATILITY_TRENDING", True
        elif is_high_vol and not is_trending:
            return "HIGH_VOLATILITY_RANGING", False
        elif not is_high_vol and is_trending:
            return "LOW_VOLATILITY_TRENDING", False
        else:
            return "LOW_VOLATILITY_RANGING", False


class HYP01Trade(BaseModel):
    """Complete forensic record of an executed trade under HYP-01."""
    trade_id: str
    symbol: str
    side: str  # LONG or SHORT
    entry_time_ms: int
    exit_time_ms: int
    entry_price: float
    exit_price: float
    exit_reason: str
    bars_held: int
    sigma: float
    regime: str
    htf_12_bps: float
    itf_3_bps: float
    notional_usd: float
    initial_equity_usd: float
    equity_after_usd: float
    gross_return_bps: float
    net_return_bps: float
    gross_pnl_usd: float
    net_pnl_usd: float
    fee_usd: float
    spread_usd: float
    slip_usd: float
    fund_usd: float
    entry_role: str
    exit_role: str
    fold: int


class HYP01Engine:
    """High-fidelity backtest engine implementing HYP-01 with Risk & Banker integration."""

    def __init__(self, config: HYP01Configuration) -> None:
        self.config = config
        self.venue = get_venue_schedule(config.fee_tier)
        self.regime_detector = HYP01RegimeDetector(
            trend_threshold_bps=config.trend_threshold_bps,
            sigma_threshold=0.0015,
            vol_expansion_min=config.vol_expansion_min,
        )

    def fit_thresholds_on_training_fold(
        self,
        matrices: Dict[str, Any],
        train_folds: Tuple[int, ...] = (0, 1),
    ) -> None:
        """Calibrates regime thresholds strictly on training folds and freezes them."""
        sigmas = []
        htf_abs = []
        for sym, m in matrices.items():
            mask = np.isin(m.fold_prev, train_folds)
            if mask.sum() > 0:
                sigmas.extend(m.sigma_20[mask])
                if 12 in m.htf_rets_bps:
                    htf_abs.extend(np.abs(m.htf_rets_bps[12][mask]))

        if sigmas:
            self.regime_detector.sigma_threshold = float(np.nanmedian(sigmas))
        if htf_abs:
            # Set trend threshold to 50th percentile of trending moves
            self.regime_detector.trend_threshold_bps = float(np.nanpercentile(htf_abs, 50))

    def evaluate_multi_asset(
        self,
        matrices: Dict[str, Any],
        experiment_id: str,
        holdout_cutoff_ms: int = 1793491200000,
    ) -> Tuple[Dict[str, Any], List[HYP01Trade], pd.DataFrame]:
        """Runs the complete multi-asset portfolio simulation across all preloaded matrices."""
        cfg = self.config
        venue = self.venue

        # Sort all bars chronologically across assets for realistic portfolio interleaving
        symbol_list = [s for s in matrices.keys() if s != "XMRUSDT"]
        
        # Pre-compute signals per asset
        asset_signals: Dict[str, Dict[str, np.ndarray]] = {}
        for sym in symbol_list:
            m = matrices[sym]
            n_bars = len(m.opens)
            sig_side = np.zeros(n_bars, dtype=np.int8)
            regimes = []
            
            htf_12 = m.htf_rets_bps[12] if 12 in m.htf_rets_bps else np.zeros(n_bars)
            htf_3 = m.htf_rets_bps[6] if 6 in m.htf_rets_bps else np.zeros(n_bars) # 3-6 bars proxy

            for i in range(20, n_bars - 2):
                if m.open_time_ms[i] >= holdout_cutoff_ms:
                    continue

                sigma = m.sigma_20[i]
                htf_val = htf_12[i]
                vol_exp = m.vol_exp_ratio[i]
                regime_name, is_trend = self.regime_detector.classify_bar(sigma, htf_val, vol_exp)
                regimes.append(regime_name)

                # Regime filter
                if cfg.enable_regime_filter and not is_trend:
                    continue

                # Long Entry Trigger
                if cfg.allow_long_entries and htf_val >= cfg.trend_threshold_bps:
                    # Intermediate momentum confirmation
                    if htf_3[i] >= 0:
                        # 5m Green bar execution trigger
                        if m.closes[i] > m.opens[i]:
                            sig_side[i] = 1

                # Short Entry Trigger
                elif cfg.allow_short_entries and htf_val <= -cfg.trend_threshold_bps:
                    # Optional Altcoin short filter
                    if cfg.filter_altcoin_shorts and sym not in ("BTCUSDT", "ETHUSDT"):
                        continue
                    # Intermediate momentum confirmation
                    if htf_3[i] <= 0:
                        # 5m Red bar execution trigger
                        if m.closes[i] < m.opens[i]:
                            sig_side[i] = -1

            asset_signals[sym] = {
                "signal_side": sig_side,
                "htf_12": htf_12,
                "htf_3": htf_3,
            }

        # Portfolio simulation loop with shared cash and risk limits
        portfolio_equity = float(cfg.initial_equity_usd)
        peak_equity = portfolio_equity
        trades: List[HYP01Trade] = []
        equity_curve: List[Dict[str, Any]] = []

        # Track active positions: {sym: position_dict}
        active_positions: Dict[str, Dict[str, Any]] = {}
        last_trade_bar: Dict[str, int] = {s: -999 for s in symbol_list}
        daily_loss_accum = 0.0
        current_day = None

        # Determine total bars (using BTC as master clock)
        master_bars = len(matrices["BTCUSDT"].opens)
        
        for i in range(20, master_bars - 2):
            t_ms = matrices["BTCUSDT"].open_time_ms[i]
            if t_ms >= holdout_cutoff_ms:
                break

            day_key = t_ms // (86400 * 1000)
            if current_day is not None and day_key != current_day:
                # Mark-to-market daily calendar equity tracking (zero skipped days!)
                unrealized_pnl = 0.0
                for sym, pos in active_positions.items():
                    curr_c = matrices[sym].closes[i - 1]
                    unrealized_pnl += pos["notional"] * pos["side"] * (curr_c - pos["entry_price"]) / pos["entry_price"]
                eod_mtm_equity = portfolio_equity + unrealized_pnl
                equity_curve.append({
                    "open_time_ms": current_day * 86400 * 1000,
                    "equity_usd": eod_mtm_equity,
                    "active_positions_count": len(active_positions),
                })
                daily_loss_accum = 0.0  # Reset daily loss tracker

            current_day = day_key

            # 1. Update & Manage Active Positions
            closed_syms = []
            for sym, pos in active_positions.items():
                m = matrices[sym]
                o, h, l, c = m.opens[i], m.highs[i], m.lows[i], m.closes[i]
                side = pos["side"]
                entry_px = pos["entry_price"]
                sl_px = pos["sl_price"]
                tp1_px = pos["tp1_price"]
                tp2_px = pos["tp2_price"]
                bars_held = i - pos["entry_bar"]
                sigma = pos["sigma"]
                
                # Check Stop-Loss
                sl_hit = (l <= sl_px) if side == 1 else (h >= sl_px)
                if sl_hit:
                    fill_px = sl_px
                    exit_reason = "BREAKEVEN_STOP" if pos["tp1_hit"] else "STOP_LOSS"
                    exit_role = "TAKER"
                    closed_syms.append((sym, fill_px, exit_reason, exit_role, bars_held))
                    continue

                # Check TP1 if not yet hit
                if not pos["tp1_hit"]:
                    tp1_hit = (h >= tp1_px) if side == 1 else (l <= tp1_px)
                    if tp1_hit:
                        pos["tp1_hit"] = True
                        if cfg.enable_breakeven_ratchet:
                            pos["sl_price"] = entry_px  # Ratchet SL to breakeven!

                # Check TP2
                tp2_hit = (h >= tp2_px) if side == 1 else (l <= tp2_px)
                if tp2_hit:
                    fill_px = tp2_px
                    exit_reason = "TAKE_PROFIT"
                    exit_role = "MAKER"
                    closed_syms.append((sym, fill_px, exit_reason, exit_role, bars_held))
                    continue

                # Dynamic Trailing Stop (Active after TP1)
                if pos["tp1_hit"] and cfg.trailing_stop_sigma > 0:
                    trail_dist = cfg.trailing_stop_sigma * sigma * c
                    if side == 1:
                        new_sl = c - trail_dist
                        if new_sl > pos["sl_price"]:
                            pos["sl_price"] = new_sl
                    else:
                        new_sl = c + trail_dist
                        if new_sl < pos["sl_price"]:
                            pos["sl_price"] = new_sl

                # Max Horizon Check
                if bars_held >= cfg.max_horizon_bars:
                    fill_px = c
                    exit_reason = "TIME_EXPIRATION"
                    exit_role = "TAKER"
                    closed_syms.append((sym, fill_px, exit_reason, exit_role, bars_held))
                    continue

            # Process closures
            for sym, fill_px, reason, exit_role, bars_held in closed_syms:
                pos = active_positions.pop(sym)
                side = pos["side"]
                entry_px = pos["entry_price"]
                notional = pos["notional"]
                
                leg_return = float(side) * (fill_px - entry_px) / entry_px
                gross_ret_bps = leg_return * 10_000.0
                gross_pnl = notional * leg_return

                # Banker Fee Accounting
                entry_fee_rate = (venue.taker_fee_bps_per_leg / 10_000.0) if pos["entry_role"] == "TAKER" else (venue.maker_fee_bps_per_leg / 10_000.0)
                exit_fee_rate = (venue.taker_fee_bps_per_leg / 10_000.0) if exit_role == "TAKER" else (venue.maker_fee_bps_per_leg / 10_000.0)
                fee_usd = notional * (entry_fee_rate + exit_fee_rate)
                
                spread_usd = notional * (venue.default_spread_bps / 10_000.0) if pos["entry_role"] == "TAKER" else 0.0
                slip_usd = notional * (venue.default_slippage_bps / 10_000.0)
                fund_usd = notional * 0.0001 * (bars_held // 96) # 8h rate proxy
                
                total_cost = fee_usd + spread_usd + slip_usd + fund_usd
                net_pnl = gross_pnl - total_cost
                net_ret_bps = (net_pnl / notional) * 10_000.0

                portfolio_equity += net_pnl
                daily_loss_accum += min(0.0, net_pnl)
                peak_equity = max(peak_equity, portfolio_equity)

                trade_record = HYP01Trade(
                    trade_id=f"T_{len(trades)+1:06d}_{sym}",
                    symbol=sym,
                    side="LONG" if side == 1 else "SHORT",
                    entry_time_ms=pos["entry_time"],
                    exit_time_ms=matrices[sym].open_time_ms[i],
                    entry_price=entry_px,
                    exit_price=fill_px,
                    exit_reason=reason,
                    bars_held=bars_held,
                    sigma=pos["sigma"],
                    regime=pos["regime"],
                    htf_12_bps=pos["htf_12"],
                    itf_3_bps=pos["itf_3"],
                    notional_usd=round(notional, 2),
                    initial_equity_usd=round(portfolio_equity - net_pnl, 2),
                    equity_after_usd=round(portfolio_equity, 2),
                    gross_return_bps=round(gross_ret_bps, 2),
                    net_return_bps=round(net_ret_bps, 2),
                    gross_pnl_usd=round(gross_pnl, 4),
                    net_pnl_usd=round(net_pnl, 4),
                    fee_usd=round(fee_usd, 4),
                    spread_usd=round(spread_usd, 4),
                    slip_usd=round(slip_usd, 4),
                    fund_usd=round(fund_usd, 4),
                    entry_role=pos["entry_role"],
                    exit_role=exit_role,
                    fold=int(matrices[sym].fold_prev[i]),
                )
                trades.append(trade_record)

            # 2. Risk Agent Circuit Breaker Checks
            if portfolio_equity <= 5.0:
                break  # Ruin protection
            
            # Daily loss circuit breaker
            if abs(daily_loss_accum) / max(portfolio_equity, 10.0) >= cfg.daily_loss_circuit_breaker_pct:
                continue  # Halt entries for remainder of day

            # Max drawdown circuit breaker
            dd_pct = (peak_equity - portfolio_equity) / peak_equity
            leverage_mult = 0.5 if dd_pct >= cfg.max_drawdown_circuit_breaker_pct else 1.0

            # 3. Scan & Execute New Signals
            if len(active_positions) >= cfg.max_concurrent_positions:
                continue  # Concurrent position cap

            for sym in symbol_list:
                if len(active_positions) >= cfg.max_concurrent_positions:
                    break
                if sym in active_positions:
                    continue
                if (i - last_trade_bar[sym]) < cfg.cooldown_bars:
                    continue

                sig = asset_signals[sym]["signal_side"][i]
                if sig == 0:
                    continue

                m = matrices[sym]
                sigma = m.sigma_20[i]
                arrival_px = m.opens[i]

                # Volatility-Adjusted Barrier Pricing (Anti-Noise Solution)
                sl_dist = cfg.sl_multiplier * sigma * arrival_px
                tp1_dist = cfg.tp1_multiplier * sigma * arrival_px
                tp2_dist = cfg.tp2_multiplier * sigma * arrival_px

                if sig == 1:
                    sl_px = arrival_px - sl_dist
                    tp1_px = arrival_px + tp1_dist
                    tp2_px = arrival_px + tp2_dist
                else:
                    sl_px = arrival_px + sl_dist
                    tp1_px = arrival_px - tp1_dist
                    tp2_px = arrival_px - tp2_dist

                # Volatility Position Sizing
                sl_pct = (sl_dist / arrival_px)
                risk_budget = portfolio_equity * cfg.risk_per_trade_pct
                desired_notional = risk_budget / max(sl_pct, 0.005)
                max_allowed_notional = portfolio_equity * cfg.max_leverage * leverage_mult * cfg.max_symbol_exposure_pct
                notional = min(desired_notional, max_allowed_notional)

                if notional < 5.0:
                    continue  # Sub-minimum notional

                active_positions[sym] = {
                    "side": int(sig),
                    "entry_price": arrival_px,
                    "entry_bar": i,
                    "entry_time": m.open_time_ms[i],
                    "entry_role": "TAKER" if cfg.order_type == "MARKET" else "MAKER",
                    "sl_price": sl_px,
                    "tp1_price": tp1_px,
                    "tp2_price": tp2_px,
                    "tp1_hit": False,
                    "notional": notional,
                    "sigma": float(sigma),
                    "regime": "HIGH_VOLATILITY_TRENDING",
                    "htf_12": float(asset_signals[sym]["htf_12"][i]),
                    "itf_3": float(asset_signals[sym]["htf_3"][i]),
                }
                last_trade_bar[sym] = i

            # End of bar loop
        
        # Record final day if not already recorded
        if current_day is not None and (not equity_curve or equity_curve[-1]["open_time_ms"] != current_day * 86400 * 1000):
            unrealized_pnl = 0.0
            for sym, pos in active_positions.items():
                curr_c = matrices[sym].closes[-2]
                unrealized_pnl += pos["notional"] * pos["side"] * (curr_c - pos["entry_price"]) / pos["entry_price"]
            equity_curve.append({
                "open_time_ms": current_day * 86400 * 1000,
                "equity_usd": portfolio_equity + unrealized_pnl,
                "active_positions_count": len(active_positions),
            })

        # Summary Metrics Calculation
        df_trades = pd.DataFrame([t.model_dump() for t in trades]) if trades else pd.DataFrame()
        summary = self._compute_performance_summary(df_trades, cfg.initial_equity_usd, portfolio_equity, peak_equity, equity_curve)
        return summary, trades, pd.DataFrame(equity_curve)

    def _compute_performance_summary(
        self,
        df_trades: pd.DataFrame,
        initial_equity: float,
        ending_equity: float,
        peak_equity: float,
        equity_curve: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Calculates comprehensive performance metrics matching institutional standards."""
        if df_trades.empty:
            return {
                "strategy_id": self.config.strategy_id,
                "config_hash": self.config.config_hash,
                "executed_trades_count": 0,
                "net_cumulative_return_pct": 0.0,
                "mean_daily_return_pct": 0.0,
                "median_daily_return_pct": 0.0,
                "pct_days_gte_3pct": 0.0,
                "pct_negative_days": 0.0,
                "worst_daily_loss_pct": 0.0,
                "profit_factor": 0.0,
                "max_drawdown_pct": 0.0,
                "win_rate_pct": 0.0,
                "gross_expectancy_bps": 0.0,
                "net_expectancy_bps": 0.0,
                "sharpe_annualized": 0.0,
                "sortino_annualized": 0.0,
                "calmar_ratio": 0.0,
                "qualified_3pct_daily": False,
            }

        n_trades = len(df_trades)
        net_ret_pct = ((ending_equity - initial_equity) / initial_equity) * 100.0
        
        # Daily return analysis
        df_eq = pd.DataFrame(equity_curve)
        if len(df_eq) > 1:
            df_eq["daily_return_pct"] = df_eq["equity_usd"].pct_change() * 100.0
            daily_returns = df_eq["daily_return_pct"].dropna()
            mean_daily = float(daily_returns.mean())
            median_daily = float(daily_returns.median())
            pct_gte_3 = float((daily_returns >= 3.0).mean() * 100.0)
            pct_neg = float((daily_returns < 0.0).mean() * 100.0)
            worst_daily = float(daily_returns.min())
            daily_std = float(daily_returns.std()) if len(daily_returns) > 1 else 1.0
            sharpe = (mean_daily / daily_std * np.sqrt(365)) if daily_std > 0 else 0.0
            downside_std = float(daily_returns[daily_returns < 0].std()) if len(daily_returns[daily_returns < 0]) > 1 else 1.0
            sortino = (mean_daily / downside_std * np.sqrt(365)) if downside_std > 0 else 0.0
        else:
            mean_daily = 0.0
            median_daily = 0.0
            pct_gte_3 = 0.0
            pct_neg = 0.0
            worst_daily = 0.0
            sharpe = 0.0
            sortino = 0.0

        # Drawdown calculation
        eq_arr = df_eq["equity_usd"].values if not df_eq.empty else np.array([initial_equity, ending_equity])
        peaks = np.maximum.accumulate(eq_arr)
        drawdowns = (peaks - eq_arr) / peaks * 100.0
        max_dd = float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0
        calmar = (net_ret_pct / max_dd) if max_dd > 0 else 0.0

        # Trade expectancy and profit factor
        wins = df_trades[df_trades["net_pnl_usd"] > 0]["net_pnl_usd"].sum()
        losses = abs(df_trades[df_trades["net_pnl_usd"] < 0]["net_pnl_usd"].sum())
        profit_factor = (wins / losses) if losses > 0 else float("inf")
        win_rate = (df_trades["net_pnl_usd"] > 0).mean() * 100.0
        gross_exp = df_trades["gross_return_bps"].mean()
        net_exp = df_trades["net_return_bps"].mean()

        # Qualification criterion: Mean daily return >= 3.0% and Max Drawdown <= 25.0%
        qualified_3pct = (mean_daily >= 3.0) and (max_dd <= 25.0) and (net_ret_pct > 0)

        return {
            "strategy_id": self.config.strategy_id,
            "config_hash": self.config.config_hash,
            "executed_trades_count": int(n_trades),
            "initial_equity_usd": float(initial_equity),
            "ending_equity_usd": round(float(ending_equity), 2),
            "net_cumulative_return_pct": round(float(net_ret_pct), 2),
            "mean_daily_return_pct": round(mean_daily, 3),
            "median_daily_return_pct": round(median_daily, 3),
            "pct_days_gte_3pct": round(pct_gte_3, 2),
            "pct_negative_days": round(pct_neg, 2),
            "worst_daily_loss_pct": round(worst_daily, 2),
            "profit_factor": round(float(profit_factor), 3),
            "max_drawdown_pct": round(max_dd, 2),
            "win_rate_pct": round(float(win_rate), 2),
            "gross_expectancy_bps": round(float(gross_exp), 2),
            "net_expectancy_bps": round(float(net_exp), 2),
            "sharpe_annualized": round(float(sharpe), 2),
            "sortino_annualized": round(float(sortino), 2),
            "calmar_ratio": round(float(calmar), 2),
            "qualified_3pct_daily": bool(qualified_3pct),
        }
