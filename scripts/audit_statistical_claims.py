"""Phase F & G: Statistical Claims Verification & Execution Regime Coverage Matrix.

Audits all 6 causal alpha hypotheses (HYP-01 to HYP-06) across all 5 execution regimes
(30 combinations total) under AsterDEX Base Retail cost models and zero-friction diagnostic.

Performs:
1. Stationary / circular block bootstrap (B=1000 resamples, block length b=12 bars) for gross and net expectancy CIs.
2. Autocorrelation analysis and effective sample size (N_eff).
3. Holm-Bonferroni multiple testing correction on family-wise error rate.
4. Deflated Sharpe Ratio (DSR) using Bailey & Lopez de Prado (2014).
5. Generates:
   - audit/strategy_research/milestone_5_12_2_exposure_invariant_patch/M5_12_2_EXECUTION_COVERAGE_MATRIX.csv
   - audit/strategy_research/milestone_5_12_2_exposure_invariant_patch/M5_12_2_STATISTICAL_CLAIMS_DATA.json
"""

import sys
import json
import math
from pathlib import Path
from typing import Dict, List, Any, Tuple
import numpy as np
import pandas as pd
import scipy.stats as stats
import pyarrow.parquet as pq

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "src"))

from quantum.accounting.event_ledger import EventDrivenPortfolioLedger
from quantum.domain.enums import TradeSide
from quantum.features.market_context import (
    compute_market_context_dataframe,
    compute_cross_asset_context,
)
from quantum.strategies.hypothesis_engine import (
    backtest_single_hypothesis,
    TradeRecord,
)

OUT_DIR = ROOT / "audit" / "strategy_research" / "milestone_5_12_2_exposure_invariant_patch"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CANONICAL_DIR = ROOT / "data" / "historical" / "canonical" / "exchange=ASTER"

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "ADAUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT"
]

HYPOTHESIS_IDS = ["HYP-01", "HYP-02", "HYP-03", "HYP-04", "HYP-05", "HYP-06"]

REGIMES = [
    "TAKER_TAKER",
    "MAKER_MAKER",
    "MAKER_TAKER",
    "TAKER_MAKER",
    "ZERO_FRICTION_DIAGNOSTIC",
]


def load_canonical_data(sample_bars: int = 40000) -> Dict[str, pd.DataFrame]:
    """Loads synchronized canonical 5m data for the 10 assets strictly prior to holdout timestamp."""
    panel = {}
    for sym in SYMBOLS:
        p = CANONICAL_DIR / f"symbol={sym}" / "timeframe=5m"
        files = sorted(p.glob("*.parquet"))
        dfs = [
            pq.ParquetFile(str(f)).read(
                columns=["open_time_ms", "close_time_ms", "open", "high", "low", "close", "volume"]
            ).to_pandas()
            for f in files
        ]
        full_df = pd.concat(dfs, ignore_index=True)
        valid_df = full_df[full_df["open_time_ms"] < 1_793_491_200_000].copy()
        valid_df = valid_df.sort_values("open_time_ms").reset_index(drop=True)
        if len(valid_df) > sample_bars:
            valid_df = valid_df.iloc[-sample_bars:].reset_index(drop=True)
        panel[sym] = valid_df
    return panel


def run_portfolio_simulation(
    trades: List[TradeRecord],
    regime: str,
    total_days: float,
    initial_equity: float = 100.0,
) -> Dict[str, Any]:
    """Simulates multi-asset portfolio execution under specified regime."""
    if regime == "TAKER_TAKER":
        fee_in_bps, fee_out_bps = 10.0, 10.0
        sprd_in_bps, sprd_out_bps = 1.0, 1.0
        slip_in_bps, slip_out_bps = 2.0, 2.0
        adv_in_bps, adv_out_bps = 0.0, 0.0
        classification = "AGGRESSIVE_TAKER_OBSERVED"
    elif regime == "MAKER_MAKER":
        fee_in_bps, fee_out_bps = 4.0, 4.0
        sprd_in_bps, sprd_out_bps = 0.0, 0.0
        slip_in_bps, slip_out_bps = 0.0, 0.0
        adv_in_bps, adv_out_bps = 1.5, 1.5
        classification = "SIMULATED_EXECUTION_ASSUMPTION"
    elif regime == "MAKER_TAKER":
        fee_in_bps, fee_out_bps = 4.0, 10.0
        sprd_in_bps, sprd_out_bps = 0.0, 1.0
        slip_in_bps, slip_out_bps = 0.0, 2.0
        adv_in_bps, adv_out_bps = 1.5, 0.0
        classification = "SIMULATED_EXECUTION_ASSUMPTION"
    elif regime == "TAKER_MAKER":
        fee_in_bps, fee_out_bps = 10.0, 4.0
        sprd_in_bps, sprd_out_bps = 1.0, 0.0
        slip_in_bps, slip_out_bps = 2.0, 0.0
        adv_in_bps, adv_out_bps = 0.0, 1.5
        classification = "SIMULATED_EXECUTION_ASSUMPTION"
    elif regime == "ZERO_FRICTION_DIAGNOSTIC":
        fee_in_bps, fee_out_bps = 0.0, 0.0
        sprd_in_bps, sprd_out_bps = 0.0, 0.0
        slip_in_bps, slip_out_bps = 0.0, 0.0
        adv_in_bps, adv_out_bps = 0.0, 0.0
        classification = "THEORETICAL_GROSS_DIAGNOSTIC"
    else:
        raise ValueError(f"Unknown regime: {regime}")

    ledger = EventDrivenPortfolioLedger(
        initial_equity_usd=initial_equity,
        max_gross_exposure=1.0000,
        max_concurrent_positions=4,
        max_symbol_weight=0.25,
        ruin_equity_threshold=1.0,
    )

    # Sort trades chronologically
    sorted_trades = sorted(trades, key=lambda t: t.entry_time_ms)

    trade_returns_net_bps = []
    trade_returns_gross_bps = []
    holding_durations = []
    gross_pnls = []
    net_pnls = []
    ruin_ts = None
    start_ts = sorted_trades[0].entry_time_ms if sorted_trades else 0

    for tr in sorted_trades:
        if ledger.is_ruined:
            if ruin_ts is None:
                ruin_ts = tr.entry_time_ms
            break

        # Check entry capacity
        can_open, _, alloc_usd = ledger.can_open_position(
            tr.symbol,
            tr.notional_usd,
            entry_friction_rate=(fee_in_bps + sprd_in_bps + slip_in_bps + adv_in_bps) / 10_000.0
        )
        if not can_open or alloc_usd <= 0.0:
            continue

        # Open position
        side_enum = TradeSide[tr.side] if isinstance(tr.side, str) else tr.side
        pos = ledger.open_position(
            symbol=tr.symbol,
            side=side_enum,
            reference_price=tr.entry_price,
            fill_price=tr.entry_price,
            notional=alloc_usd,
            fee_bps=fee_in_bps,
            spread_bps_half=sprd_in_bps,
            slippage_bps=slip_in_bps + adv_in_bps,
            timestamp_ms=tr.entry_time_ms,
            entry_bar=tr.entry_bar,
        )
        if pos is None:
            continue

        # Accrue estimated funding (approx 1 funding interval per 8 hours)
        hold_hours = tr.duration_minutes / 60.0
        funding_intervals = int(hold_hours / 8.0)
        for _ in range(funding_intervals):
            ledger.accrue_funding(tr.symbol, funding_rate_bps=1.0, timestamp_ms=tr.entry_time_ms + 28_800_000)

        # Close position
        res = ledger.close_position(
            symbol=tr.symbol,
            fill_price=tr.exit_price,
            fee_bps=fee_out_bps,
            spread_bps_half=sprd_out_bps,
            slippage_bps=slip_out_bps + adv_out_bps,
            timestamp_ms=tr.exit_time_ms,
        )
        if res is not None:
            gross_pnl, net_pnl = res
            net_pnls.append(net_pnl)
            gross_pnls.append(gross_pnl)
            net_bps = (net_pnl / max(1e-6, alloc_usd)) * 10_000.0
            gross_bps = (gross_pnl / max(1e-6, alloc_usd)) * 10_000.0
            trade_returns_net_bps.append(net_bps)
            trade_returns_gross_bps.append(gross_bps)
            holding_durations.append(tr.duration_minutes)

    completed = len(net_pnls)
    tot_gross = sum(gross_pnls)
    tot_net = sum(net_pnls)
    tot_friction = tot_gross - tot_net

    win_count = sum(1 for p in net_pnls if p > 0.0)
    win_rate = (win_count / max(1, completed)) * 100.0

    trades_per_day = completed / max(1e-6, total_days)
    mean_daily = (tot_net / initial_equity) / max(1e-6, total_days) * 100.0

    df_ev = ledger.to_dataframe()
    if not df_ev.empty and "equity" in df_ev.columns:
        eqs = df_ev["equity"].to_numpy()
        pks = np.maximum.accumulate(eqs)
        dds = (pks - eqs) / np.maximum(pks, 1e-6) * 100.0
        max_dd = float(np.max(dds))
    else:
        max_dd = 0.0

    profit_factor = round(abs(tot_gross / max(1e-6, tot_friction)), 2)
    tot_notional = completed * 25.0
    net_exp_bps = (tot_net / max(1e-6, tot_notional)) * 10_000.0 if completed > 0 else 0.0
    gross_exp_bps = (tot_gross / max(1e-6, tot_notional)) * 10_000.0 if completed > 0 else 0.0

    time_to_ruin_days = round((ruin_ts - start_ts) / 86_400_000.0, 2) if ruin_ts else None

    return {
        "regime": regime,
        "classification": classification,
        "completed_trades": completed,
        "trades_per_day": round(trades_per_day, 2),
        "win_rate_pct": round(win_rate, 2),
        "gross_pnl_usd": round(tot_gross, 2),
        "friction_cost_usd": round(tot_friction, 2),
        "net_pnl_usd": round(tot_net, 2),
        "gross_expectancy_bps": round(gross_exp_bps, 2),
        "net_expectancy_bps": round(net_exp_bps, 2),
        "profit_factor": profit_factor,
        "mean_daily_return_pct": round(mean_daily, 4),
        "max_drawdown_pct": round(max_dd, 2),
        "final_equity_usd": round(ledger.equity, 2),
        "time_to_ruin_days": time_to_ruin_days,
        "avg_holding_mins": round(np.mean(holding_durations) if holding_durations else 0.0, 1),
        "net_returns_bps_series": trade_returns_net_bps,
        "gross_returns_bps_series": trade_returns_gross_bps,
    }


def compute_circular_block_bootstrap(
    series: List[float],
    block_size: int = 12,
    num_bootstraps: int = 1000,
    seed: int = 42,
) -> Tuple[float, float, float]:
    """Computes circular block bootstrap 95% confidence intervals for the mean."""
    n = len(series)
    if n < 10:
        return 0.0, 0.0, 0.0

    arr = np.array(series, dtype=np.float64)
    rng = np.random.default_rng(seed)

    # Circular array for wrapping
    circ_arr = np.concatenate([arr, arr[:block_size]])
    num_blocks = int(np.ceil(n / block_size))

    boot_means = np.zeros(num_bootstraps)
    for b in range(num_bootstraps):
        start_indices = rng.integers(0, n, size=num_blocks)
        resampled_blocks = [circ_arr[idx : idx + block_size] for idx in start_indices]
        resampled_sample = np.concatenate(resampled_blocks)[:n]
        boot_means[b] = np.mean(resampled_sample)

    ci_lower = float(np.percentile(boot_means, 2.5))
    mean_val = float(np.mean(boot_means))
    ci_upper = float(np.percentile(boot_means, 97.5))
    return ci_lower, mean_val, ci_upper


def compute_effective_sample_size(series: List[float]) -> Tuple[float, float]:
    """Computes lag-1 autocorrelation rho_1 and effective sample size N_eff."""
    n = len(series)
    if n < 5:
        return 0.0, float(n)

    s = pd.Series(series)
    rho_1 = float(s.autocorr(lag=1))
    if np.isnan(rho_1):
        rho_1 = 0.0

    # AR(1) proxy for effective sample size: N_eff = N * (1 - rho) / (1 + rho)
    rho_clamped = max(-0.99, min(0.99, rho_1))
    n_eff = float(n * (1.0 - rho_clamped) / (1.0 + rho_clamped))
    return rho_1, max(1.0, min(float(n), n_eff))


def compute_deflated_sharpe_ratio(
    sharpe_ratio: float,
    n_trials: int,
    var_sharpe: float,
    skewness: float,
    kurtosis: float,
    sample_len: int,
) -> float:
    """Computes Bailey & Lopez de Prado (2014) Deflated Sharpe Ratio."""
    if sample_len <= 1 or sharpe_ratio <= 0.0:
        return 0.0

    # Expected maximum Sharpe under null hypothesis
    euler_mascheroni = 0.5772156649
    if n_trials > 1:
        sr_star = math.sqrt(var_sharpe) * (
            (1.0 - euler_mascheroni) * stats.norm.ppf(1.0 - 1.0 / n_trials)
            + euler_mascheroni * stats.norm.ppf(1.0 - 1.0 / (n_trials * math.e))
        )
    else:
        sr_star = 0.0

    denom = math.sqrt(1.0 - skewness * sharpe_ratio + ((kurtosis - 1.0) / 4.0) * (sharpe_ratio ** 2))
    if denom <= 1e-6:
        return 0.0

    z_stat = (sharpe_ratio - sr_star) * math.sqrt(sample_len - 1) / denom
    dsr = float(stats.norm.cdf(z_stat))
    return dsr


def main():
    print("=" * 80)
    print("QUANTUM M5.12.2: STATISTICAL CLAIMS AUDIT & EXECUTION COVERAGE MATRIX")
    print("=" * 80)

    # 1. Load canonical data
    print("\n[1/4] Loading canonical 5m panel...")
    raw_panel = load_canonical_data(sample_bars=40000)

    print("[2/4] Computing single-asset and cross-asset market context...")
    context_panel = {}
    for sym, df_raw in raw_panel.items():
        context_panel[sym] = compute_market_context_dataframe(df_raw)

    enriched_panel = compute_cross_asset_context(context_panel, btc_symbol="BTCUSDT")

    btc_df = raw_panel["BTCUSDT"]
    total_days = max(1.0, (btc_df["open_time_ms"].iloc[-1] - btc_df["open_time_ms"].iloc[0]) / 86_400_000.0)
    print(f"Dataset span: {total_days:.2f} calendar days ({len(btc_df):,} 5m bars).")

    # 2. Generate Trade Records for all 6 Hypotheses across 10 symbols
    print("\n[3/4] Backtesting all 6 hypotheses across 10 assets...")
    hypothesis_trades: Dict[str, List[TradeRecord]] = {h: [] for h in HYPOTHESIS_IDS}

    for h_id in HYPOTHESIS_IDS:
        for sym, df in enriched_panel.items():
            tr_list = backtest_single_hypothesis(df, h_id, symbol=sym)
            hypothesis_trades[h_id].extend(tr_list)
        print(f"  {h_id}: Generated {len(hypothesis_trades[h_id]):,} completed trade records.")

    # 3. Evaluate 30 Combinations (6 Hypotheses x 5 Regimes)
    print("\n[4/4] Evaluating 30 Execution Matrix Combinations...")
    matrix_rows = []
    claims_data = {}

    for h_id in HYPOTHESIS_IDS:
        trades = hypothesis_trades[h_id]
        claims_data[h_id] = {}

        # Capture Sharpe ratios across regimes for DSR variance
        regime_sharpes = []

        for reg in REGIMES:
            res = run_portfolio_simulation(trades, reg, total_days=total_days)

            # Circular Block Bootstrap on net returns bps
            net_rets = res["net_returns_bps_series"]
            gross_rets = res["gross_returns_bps_series"]

            ci_low_net, mean_net_boot, ci_high_net = compute_circular_block_bootstrap(net_rets, block_size=12, num_bootstraps=1000)
            ci_low_grs, mean_grs_boot, ci_high_grs = compute_circular_block_bootstrap(gross_rets, block_size=12, num_bootstraps=1000)

            # Effective Sample Size
            rho_1, n_eff = compute_effective_sample_size(net_rets)

            # Sharpe Ratio (annualized from 5m mean daily)
            std_daily = np.std(net_rets) if len(net_rets) > 1 else 1.0
            sr_ann = (res["mean_daily_return_pct"] / max(0.01, std_daily * math.sqrt(288))) * math.sqrt(365) if std_daily > 0 else 0.0
            regime_sharpes.append(sr_ann)

            row = {
                "hypothesis_id": h_id,
                "execution_regime": reg,
                "execution_classification": res["classification"],
                "completed_trades": res["completed_trades"],
                "trades_per_day": res["trades_per_day"],
                "win_rate_pct": res["win_rate_pct"],
                "gross_pnl_usd": res["gross_pnl_usd"],
                "friction_cost_usd": res["friction_cost_usd"],
                "net_pnl_usd": res["net_pnl_usd"],
                "gross_expectancy_bps": res["gross_expectancy_bps"],
                "gross_exp_ci_95": f"[{ci_low_grs:.1f}, {ci_high_grs:.1f}]",
                "net_expectancy_bps": res["net_expectancy_bps"],
                "net_exp_ci_95": f"[{ci_low_net:.1f}, {ci_high_net:.1f}]",
                "autocorr_rho_1": round(rho_1, 4),
                "effective_n": round(n_eff, 1),
                "profit_factor": res["profit_factor"],
                "mean_daily_return_pct": res["mean_daily_return_pct"],
                "max_drawdown_pct": res["max_drawdown_pct"],
                "final_equity_usd": res["final_equity_usd"],
                "time_to_ruin_days": str(res["time_to_ruin_days"]) if res["time_to_ruin_days"] is not None else "SURVIVED",
                "avg_holding_mins": res["avg_holding_mins"],
            }
            matrix_rows.append(row)

            claims_data[h_id][reg] = {
                "net_pnl": res["net_pnl_usd"],
                "gross_pnl": res["gross_pnl_usd"],
                "trades": res["completed_trades"],
                "ci_net": [ci_low_net, ci_high_net],
                "ci_gross": [ci_low_grs, ci_high_grs],
                "rho_1": rho_1,
                "n_eff": n_eff,
                "sharpe_ann": sr_ann,
            }

    # Save CSV
    df_matrix = pd.DataFrame(matrix_rows)
    matrix_csv = OUT_DIR / "M5_12_2_EXECUTION_COVERAGE_MATRIX.csv"
    df_matrix.to_csv(matrix_csv, index=False)
    print(f"\nExecution Coverage Matrix written to: {matrix_csv}")

    # 4. Statistical Claims Verification: Multiple Testing & Deflated Sharpe Ratio
    print("\n" + "=" * 80)
    print("STATISTICAL INFERENCE & MULTIPLE TESTING CORRECTION")
    print("=" * 80)

    stats_summary_rows = []
    raw_p_values = []

    # Calculate p-value of net return > 0 under TAKER_TAKER (the strict observed reality)
    for h_id in HYPOTHESIS_IDS:
        taker_data = claims_data[h_id]["TAKER_TAKER"]
        trades_count = taker_data["trades"]
        n_eff = taker_data["n_eff"]
        ci_net = taker_data["ci_net"]
        net_pnl = taker_data["net_pnl"]

        # One-tailed t-test / z-test against H0: mean net return <= 0
        if trades_count >= 10:
            se = (ci_net[1] - ci_net[0]) / (2 * 1.96) if ci_net[1] > ci_net[0] else 1.0
            mean_est = (ci_net[1] + ci_net[0]) / 2.0
            z_score = mean_est / max(1e-6, se)
            p_val = float(1.0 - stats.norm.cdf(z_score))
        else:
            p_val = 1.0
        raw_p_values.append(p_val)

    # Holm-Bonferroni correction (step-down)
    sorted_indices = np.argsort(raw_p_values)
    m = len(HYPOTHESIS_IDS)
    adjusted_p_values = np.zeros(m)
    for rank, idx in enumerate(sorted_indices):
        adj = raw_p_values[idx] * (m - rank)
        adjusted_p_values[idx] = min(1.0, adj)

    # Ensure monotonicity of Holm-Bonferroni
    for r in range(1, m):
        idx_cur = sorted_indices[r]
        idx_prev = sorted_indices[r - 1]
        adjusted_p_values[idx_cur] = max(adjusted_p_values[idx_cur], adjusted_p_values[idx_prev])

    # Compute DSR for each hypothesis under ZERO_FRICTION_DIAGNOSTIC and TAKER_TAKER
    all_sharpes = [claims_data[h]["TAKER_TAKER"]["sharpe_ann"] for h in HYPOTHESIS_IDS]
    var_sharpes = float(np.var(all_sharpes)) if len(all_sharpes) > 1 else 0.1

    for i, h_id in enumerate(HYPOTHESIS_IDS):
        taker_data = claims_data[h_id]["TAKER_TAKER"]
        zero_data = claims_data[h_id]["ZERO_FRICTION_DIAGNOSTIC"]
        raw_p = raw_p_values[i]
        adj_p = adjusted_p_values[i]
        sr_taker = taker_data["sharpe_ann"]
        dsr_taker = compute_deflated_sharpe_ratio(
            sharpe_ratio=max(0.0, sr_taker),
            n_trials=6,
            var_sharpe=var_sharpes,
            skewness=-0.5,
            kurtosis=3.5,
            sample_len=int(taker_data["n_eff"])
        )

        stats_summary_rows.append({
            "hypothesis_id": str(h_id),
            "sample_trades": int(taker_data["trades"]),
            "effective_n": float(round(taker_data["n_eff"], 2)),
            "taker_net_pnl": float(taker_data["net_pnl"]),
            "zero_gross_pnl": float(zero_data["gross_pnl"]),
            "net_exp_ci_95": f"[{taker_data['ci_net'][0]:.1f}, {taker_data['ci_net'][1]:.1f}]",
            "raw_p_value": float(round(raw_p, 4)),
            "holm_bonferroni_p": float(round(adj_p, 4)),
            "alpha_significant_05": bool(adj_p < 0.05),
            "deflated_sharpe_ratio": float(round(dsr_taker, 4)),
            "statistical_verdict": "REJECT_NULL (ALPHA CONFIRMED)" if adj_p < 0.05 and taker_data["net_pnl"] > 0 else "FAIL_TO_REJECT (ZERO/NEGATIVE ALPHA)",
        })

    df_stats = pd.DataFrame(stats_summary_rows)
    print("\n" + df_stats.to_string(index=False))

    # Save stats data to JSON
    with open(OUT_DIR / "M5_12_2_STATISTICAL_CLAIMS_DATA.json", "w") as f:
        json.dump({
            "matrix": matrix_rows,
            "stats_summary": stats_summary_rows,
        }, f, indent=2)

    print("\nStatistical Claims Data saved to JSON.")
    return df_matrix, df_stats


if __name__ == "__main__":
    main()
