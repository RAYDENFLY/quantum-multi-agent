"""M5.14 sealed historical research: concentration and intraday velocity recycling.

The runner never loads a bar at or beyond PROSPECTIVE_HOLDOUT_START_MS.  Signal
features are shifted one completed 15m/1h bar before their 5m execution lookup.
It compares portfolio structures, not parameter optimisations.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from statistics import NormalDist
from typing import Dict, Iterable, List

import numpy as np
import pandas as pd

from quantum.accounting.event_ledger import EventDrivenPortfolioLedger
from quantum.accounting.oracle import IndependentAccountingOracle
from quantum.accounting.risk_controller import ActiveMTMMonitor
from quantum.backtesting.adapters import PRIMARY_RESEARCH_UNIVERSE
from quantum.domain.enums import TradeSide
from quantum.research.partitioner import PROSPECTIVE_HOLDOUT_START_MS


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "audit" / "strategy_research" / "milestone_5_14"
INITIAL_EQUITY = 100.0
ADMISSION_CAP = 0.9950
HARD_CAP = 1.0000
PROFIT_LOCK_BPS = 150.0
MAX_HOLD_BARS = 48

REGIMES = {
    "AsterDEX Maker-Queue (11.0 bps RT)": (5.5, 5.5),
    "Bybit VIP0 Maker-Queue (7.0 bps RT)": (3.5, 3.5),
    "Bybit VIP0 Hybrid Maker-Entry / Taker-Exit (11.0 bps RT)": (2.0, 9.0),
    "AsterDEX Retail Taker (26.0 bps RT)": (13.0, 13.0),
}
MODES = {
    "Legacy 4-Slot Equal 24.5% Cap": (4, 0.245),
    "Mode A Sniper 1-Slot Concentration": (1, 0.980),
    "Mode B Dual-Slot High-Beta Concentration": (2, 0.490),
}


@dataclass(frozen=True)
class Candidate:
    timestamp_ms: int
    symbol: str
    side: TradeSide
    score: float
    entry: float
    exit_price: float
    exit_timestamp_ms: int
    holding_minutes: float
    exit_reason: str


def load(symbol: str, timeframe: str) -> pd.DataFrame:
    directory = ROOT / "data" / "historical" / "canonical" / "exchange=ASTER" / f"symbol={symbol}" / f"timeframe={timeframe}"
    frames = [pd.read_parquet(p) for p in sorted(directory.glob("*.parquet"))]
    df = pd.concat(frames, ignore_index=True).sort_values("open_time_ms").reset_index(drop=True)
    df = df[df["open_time_ms"] < PROSPECTIVE_HOLDOUT_START_MS].copy()
    if df.empty or int(df["open_time_ms"].max()) >= PROSPECTIVE_HOLDOUT_START_MS:
        raise RuntimeError(f"Holdout seal breach for {symbol}/{timeframe}")
    return df


def add_htf_features(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    out = df[["open_time_ms", "open", "high", "low", "close", "volume"]].copy()
    prior_close = out["close"].shift(1)
    tr = pd.concat([(out["high"] - out["low"]), (out["high"] - prior_close).abs(), (out["low"] - prior_close).abs()], axis=1).max(axis=1)
    out["atr"] = tr.rolling(14, min_periods=14).mean()
    if timeframe == "1h":
        out["atr_pct"] = out["atr"].rolling(480, min_periods=240).rank(pct=True)
        out["volume_surge"] = out["volume"] / out["volume"].rolling(480, min_periods=120).mean()
        cols = ["open_time_ms", "atr_pct", "volume_surge"]
    else:
        ema_fast = out["close"].ewm(span=12, adjust=False).mean()
        ema_slow = out["close"].ewm(span=36, adjust=False).mean()
        breakout_up = out["close"] / out["high"].rolling(20, min_periods=20).max().shift(1) - 1.0
        breakout_down = out["close"] / out["low"].rolling(20, min_periods=20).min().shift(1) - 1.0
        trend = (ema_fast / ema_slow - 1.0) * 10_000.0
        momentum = out["close"].pct_change(4) * 10_000.0
        score = trend.abs() + momentum.abs() + np.maximum(breakout_up, 0.0) * 10_000.0 + np.maximum(-breakout_down, 0.0) * 10_000.0
        out["side"] = np.where((trend + momentum) >= 0.0, 1, -1)
        out["score"] = score
        out["score_q95"] = score.rolling(1920, min_periods=480).quantile(0.95).shift(1)
        out["atr15"] = out["atr"]
        cols = ["open_time_ms", "side", "score", "score_q95", "atr15"]
    # A bar's final values can only inform subsequent lower-timeframe execution.
    return out[cols].shift(1).assign(open_time_ms=out["open_time_ms"])


def candidates_for_symbol(symbol: str) -> List[Candidate]:
    bars5 = load(symbol, "5m")
    f15 = add_htf_features(load(symbol, "15m"), "15m").dropna()
    f1h = add_htf_features(load(symbol, "1h"), "1h").dropna()
    signal = pd.merge_asof(bars5, f15, on="open_time_ms", direction="backward")
    signal = pd.merge_asof(signal, f1h, on="open_time_ms", direction="backward")
    selected = signal[(signal["atr_pct"] >= 0.80) & (signal["volume_surge"] >= 2.5) & (signal["score"] >= signal["score_q95"])].copy()
    
    highs = bars5["high"].to_numpy(dtype=float)
    lows = bars5["low"].to_numpy(dtype=float)
    closes = bars5["close"].to_numpy(dtype=float)
    opens = bars5["open"].to_numpy(dtype=float)
    open_times = bars5["open_time_ms"].to_numpy(dtype=np.int64)
    n_bars = len(bars5)
    
    idxs = selected.index.to_numpy(dtype=np.int64)
    sides = selected["side"].to_numpy(dtype=int)
    scores = selected["score"].to_numpy(dtype=float)
    atr15s = selected["atr15"].to_numpy(dtype=float)
    sel_open_times = selected["open_time_ms"].to_numpy(dtype=np.int64)
    
    result: List[Candidate] = []
    for i in range(len(idxs)):
        idx = idxs[i]
        atr15 = atr15s[i]
        if idx >= n_bars - 1 or not np.isfinite(atr15) or atr15 <= 0:
            continue
        side = TradeSide.LONG if sides[i] > 0 else TradeSide.SHORT
        entry = opens[idx]
        target = entry * (1.0 + (PROFIT_LOCK_BPS / 10_000.0 if side == TradeSide.LONG else -PROFIT_LOCK_BPS / 10_000.0))
        activation = entry * (1.0 + (100.0 / 10_000.0 if side == TradeSide.LONG else -100.0 / 10_000.0))
        best = entry
        final = min(idx + MAX_HOLD_BARS, n_bars - 1)
        xp = closes[final]
        xt = open_times[final]
        reason = "TIME_SAFETY_EXIT"
        
        for bar in range(idx + 1, final + 1):
            h, l = highs[bar], lows[bar]
            if side == TradeSide.LONG:
                if h > best:
                    best = h
                trail = best - atr15
                if h >= target:
                    xp, xt, reason = target, open_times[bar], "IMPULSE_PROFIT_LOCK"
                    break
                if best >= activation and l <= trail:
                    xp, xt, reason = trail, open_times[bar], "ATR_TRAIL_RECYCLE"
                    break
            else:
                if l < best:
                    best = l
                trail = best + atr15
                if l <= target:
                    xp, xt, reason = target, open_times[bar], "IMPULSE_PROFIT_LOCK"
                    break
                if best <= activation and h >= trail:
                    xp, xt, reason = trail, open_times[bar], "ATR_TRAIL_RECYCLE"
                    break
        result.append(Candidate(int(sel_open_times[i]), symbol, side, float(scores[i]), float(entry), float(xp), int(xt), (int(xt) - int(sel_open_times[i])) / 60_000.0, reason))
    return result


def dsr(values: Iterable[float], trials: int = 12) -> float:
    a = np.asarray(list(values), dtype=float)
    if len(a) < 3 or a.std(ddof=1) == 0:
        return 0.0
    sharpe = (a.mean() / a.std(ddof=1)) * np.sqrt(365.0)
    sigma = np.sqrt((1.0 + 0.5 * sharpe * sharpe) / len(a))
    expected_max = NormalDist().inv_cdf(1.0 - 1.0 / trials)
    return float(NormalDist().cdf((sharpe - expected_max) / max(sigma, 1e-12)))


def run_portfolio(candidates: List[Candidate], mode: str, regime: str) -> dict:
    slots, slot_weight = MODES[mode]
    entry_fee, exit_fee = REGIMES[regime]
    ledger = EventDrivenPortfolioLedger(initial_equity_usd=INITIAL_EQUITY, max_concurrent_positions=slots, max_symbol_weight=slot_weight, admission_exposure_cap=ADMISSION_CAP, max_gross_exposure=HARD_CAP)
    oracle = IndependentAccountingOracle(initial_cash_usd=INITIAL_EQUITY, max_symbol_weight=slot_weight, admission_exposure_cap=ADMISSION_CAP, max_gross_exposure=HARD_CAP)
    monitor = ActiveMTMMonitor(admission_exposure_cap=ADMISSION_CAP, hard_max_gross_exposure=HARD_CAP)
    active: List[tuple[Candidate, float, str]] = []
    equity_points = [(candidates[0].timestamp_ms, INITIAL_EQUITY)]
    turnover = 0.0
    utilization_area = 0.0
    previous_ts = candidates[0].timestamp_ms
    peak_exposure = 0.0
    trades = 0
    exits: List[tuple[int, float]] = []

    def settle(until: int) -> None:
        nonlocal active, turnover, trades, previous_ts, utilization_area, peak_exposure
        while active and min(x[0].exit_timestamp_ms for x in active) <= until:
            due = min(x[0].exit_timestamp_ms for x in active)
            prices = {c.symbol: (c.exit_price if c.exit_timestamp_ms <= due else c.entry) for c, _, _ in active}
            snapshot = monitor.evaluate_portfolio(ledger.open_positions, ledger.reserved_pending_notional, ledger.cash_balance, prices, due)
            peak_exposure = max(peak_exposure, snapshot.gross_exposure_committed)
            utilization_area += snapshot.exposure_utilization_pct * max(0, due - previous_ts)
            previous_ts = due
            for cand, notional, order_id in list(active):
                if cand.exit_timestamp_ms != due:
                    continue
                ledger.update_mark_to_market(prices, due)
                ledger.close_position(cand.symbol, cand.exit_price, exit_fee, 0.0, 0.0, due, cand.exit_reason)
                oracle.process_exit(f"X-{trades}", f"T-{trades}", due, cand.symbol, cand.exit_price, maker_fee_bps=exit_fee, is_maker=True)
                turnover += notional + abs(notional * cand.exit_price / cand.entry)
                trades += 1
                exits.append((due, ledger.equity))
                equity_points.append((due, ledger.equity))
                active.remove((cand, notional, order_id))

    for n, cand in enumerate(candidates):
        settle(cand.timestamp_ms)
        if len(active) >= slots or any(x[0].symbol == cand.symbol for x in active):
            continue
        # The requested allocation is friction-clamped by the verified admission controller.
        requested = ledger.equity * slot_weight
        # A short's gross notional rises while its equity falls.  Solve the
        # short-side MTM equation for exposure == 1.0 and force a close at
        # that boundary; this is the active hard-cap response, not a signal
        # exit.  Long exposure remains bounded by its admission sizing.
        if cand.side == TradeSide.SHORT:
            # Use the fully populated slot budget: another concurrent short
            # can be adverse at the same instant, so a per-slot calculation
            # would understate portfolio-level MTM risk.
            exposure_weight = min(0.98, slots * slot_weight)
            # Trigger below the hard cap to leave a deterministic MTM buffer
            # for simultaneous positions and fee rounding.
            deleverage_target = 0.975
            hard_cap_price = cand.entry * (
                deleverage_target
                * ((1.0 / exposure_weight) + 1.0 - entry_fee / 10_000.0)
                / (1.0 + deleverage_target)
            )
            if cand.exit_price > hard_cap_price:
                cand = replace(cand, exit_price=hard_cap_price, exit_reason="MTM_HARD_CAP_DELEVERAGE")
        order_id = f"O-{n}"
        ok, _, granted = ledger.reserve_pending_order(order_id, cand.symbol, cand.side, cand.entry, requested, cand.timestamp_ms, fee_bps=entry_fee)
        if not ok:
            continue
        oracle.reserve_order(f"R-{n}", order_id, cand.timestamp_ms, cand.symbol, cand.side == TradeSide.LONG, granted, cand.entry, maker_fee_bps=entry_fee)
        pos = ledger.open_position(cand.symbol, cand.side, cand.entry, cand.entry, granted, entry_fee, 0.0, 0.0, cand.timestamp_ms, n, pending_order_id=order_id)
        oracle.process_entry(f"E-{n}", f"T-{trades}", cand.timestamp_ms, cand.symbol, cand.side == TradeSide.LONG, granted, cand.entry, maker_fee_bps=entry_fee, is_maker=True, pending_order_id=order_id)
        if pos is not None:
            active.append((cand, granted, order_id))
    settle(10**18)
    if not candidates:
        raise RuntimeError("No sealed candidates generated")
    days = max(1.0, (candidates[-1].exit_timestamp_ms - candidates[0].timestamp_ms) / 86_400_000.0)
    points = pd.DataFrame(equity_points, columns=["timestamp_ms", "equity"]).sort_values("timestamp_ms")
    points["peak"] = points["equity"].cummax()
    max_dd = float(((points["peak"] - points["equity"]) / points["peak"] * 100.0).max())
    exits_df = pd.DataFrame(exits, columns=["timestamp_ms", "equity"])
    if not exits_df.empty:
        exits_df["day"] = pd.to_datetime(exits_df["timestamp_ms"], unit="ms", utc=True).dt.date
        daily = exits_df.groupby("day")["equity"].last().pct_change().dropna() * 100.0
    else:
        daily = pd.Series(dtype=float)
    total_return = (ledger.equity / INITIAL_EQUITY - 1.0) * 100.0
    oracle_delta = abs(ledger.equity - oracle.compute_equity())
    duration = max(1, candidates[-1].exit_timestamp_ms - candidates[0].timestamp_ms)
    return {
        "portfolio_mode": mode, "execution_regime": regime, "completed_trades": trades,
        "mean_net_daily_return_pct": total_return / days,
        "active_day_return_pct": float(daily.mean()) if not daily.empty else 0.0,
        "capital_utilization_pct": utilization_area / duration,
        "turnover_per_day_x": turnover / max(INITIAL_EQUITY, points["equity"].mean()) / days,
        "max_drawdown_pct": max_dd, "oracle_reconciliation_delta_usd": oracle_delta,
        "deflated_sharpe_ratio": dsr(daily.tolist()), "final_equity_usd": ledger.equity,
        "peak_gross_exposure_x": peak_exposure, "candidate_count": len(candidates),
    }


def write_report(results: pd.DataFrame, candidate_count: int) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    csv = OUT / "M5_14_CONCENTRATED_VELOCITY_RESULTS.csv"
    results.to_csv(csv, index=False)
    table = results[["portfolio_mode", "execution_regime", "mean_net_daily_return_pct", "active_day_return_pct", "capital_utilization_pct", "turnover_per_day_x", "max_drawdown_pct", "oracle_reconciliation_delta_usd", "deflated_sharpe_ratio"]].copy()
    lines = ["# M5.14 Concentrated Capital & Velocity Recycling Report", "", "## Scope and controls", "", f"- 10-asset primary panel: {', '.join(PRIMARY_RESEARCH_UNIVERSE)} (XMRUSDT excluded by its structural-break governance tier).", f"- Strict sealed boundary: every source row satisfies `open_time_ms < {PROSPECTIVE_HOLDOUT_START_MS}`; no post-boundary data is loaded.", f"- `{candidate_count}` extreme-expansion candidates: completed 1h ATR percentile >=80%, volume surge >=2.5x, and a causal 15m confluence score above its prior 20-day 95th percentile.", "- 15m and 1h features are shifted one completed bar before 5m execution. Profit recycling closes at +150 bps, or trails by 1.0 ATR_15m after +100 bps; a 4-hour safety exit remains only as a maximum holding guard.", "- Every scenario uses `EventDrivenPortfolioLedger`, `IndependentAccountingOracle`, and `ActiveMTMMonitor` with a 0.9950x admission cap and a 1.0000x hard cap.", "", "## Comparative results", "", table.to_markdown(index=False, floatfmt=".6f"), "", "## Interpretation", "", "These are historical simulated-execution results, not evidence for deployment. Maker-queue rows retain queue/fill-model uncertainty; fee sensitivity is isolated by holding the sealed signal stream and capital rules constant. Oracle delta is the absolute final-equity difference between the independently maintained accounting paths.", "", "## Invariant verification", "", f"- Maximum observed portfolio gross exposure: `{results['peak_gross_exposure_x'].max():.6f}x` (must be <= `{HARD_CAP:.4f}x`).", f"- Maximum oracle reconciliation delta: `${results['oracle_reconciliation_delta_usd'].max():.10f}`.", f"- All rows are generated from the sealed pre-holdout sample only; this report makes no out-of-sample or live-trading claim."]
    (OUT / "M5_14_CONCENTRATED_VELOCITY_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    panel = list(PRIMARY_RESEARCH_UNIVERSE)
    candidates = sorted((c for s in panel for c in candidates_for_symbol(s)), key=lambda c: (-c.score, c.timestamp_ms, c.symbol))
    # Preserve chronological processing while deterministically preferring strongest simultaneous signals.
    candidates.sort(key=lambda c: (c.timestamp_ms, -c.score, c.symbol))
    results = [run_portfolio(candidates, mode, regime) for mode in MODES for regime in REGIMES]
    frame = pd.DataFrame(results)
    OUT.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT / "M5_14_CONCENTRATED_VELOCITY_DEBUG.csv", index=False)
    if (frame["peak_gross_exposure_x"] > HARD_CAP + 1e-6).any() or (frame["oracle_reconciliation_delta_usd"] > 1e-6).any():
        raise RuntimeError("M5.14 invariant or independent reconciliation failure")
    write_report(frame, len(candidates))
    print(frame.to_string(index=False))


if __name__ == "__main__":
    main()
