"""Phase E: Independent Statistical Audit & Multi-Block Bootstrap Sensitivity.

Performs:
1. Re-calculation of Gross & Net PnL and expectancies for all 6 hypotheses.
2. Sensitivity analysis of Circular Block Bootstrap across b=6, 12, 24 bars.
3. Autocorrelation analysis and effective sample size (N_eff).
4. Multiple testing correction across the complete 30-cell experiment family (6 hypotheses x 5 regimes).
5. Deflated Sharpe Ratio (DSR) under Bailey & Lopez de Prado (2014).

Outputs:
- audit/strategy_research/milestone_5_12_2_1_evidence_reconciliation/M5_12_2_1_STATISTICAL_AUDIT_DATA.json
- audit/strategy_research/milestone_5_12_2_1_evidence_reconciliation/M5_12_2_1_INDEPENDENT_STATISTICAL_AUDIT.md
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

OUT_DIR = ROOT / "audit" / "strategy_research" / "milestone_5_12_2_1_evidence_reconciliation"
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
    initial_equity: float = 100.0,
) -> Dict[str, Any]:
    if regime == "TAKER_TAKER":
        f_in, f_out = 10.0, 10.0
        sp_in, sp_out = 1.0, 1.0
        sl_in, sl_out = 2.0, 2.0
    elif regime == "MAKER_MAKER":
        f_in, f_out = 4.0, 4.0
        sp_in, sp_out = 0.0, 0.0
        sl_in, sl_out = 1.5, 1.5
    elif regime == "MAKER_TAKER":
        f_in, f_out = 4.0, 10.0
        sp_in, sp_out = 0.0, 1.0
        sl_in, sl_out = 1.5, 2.0
    elif regime == "TAKER_MAKER":
        f_in, f_out = 10.0, 4.0
        sp_in, sp_out = 1.0, 0.0
        sl_in, sl_out = 2.0, 1.5
    elif regime == "ZERO_FRICTION_DIAGNOSTIC":
        f_in, f_out = 0.0, 0.0
        sp_in, sp_out = 0.0, 0.0
        sl_in, sl_out = 0.0, 0.0
    else:
        raise ValueError(f"Unknown regime: {regime}")

    ledger = EventDrivenPortfolioLedger(
        initial_equity_usd=initial_equity,
        max_gross_exposure=1.0000,
        max_concurrent_positions=4,
        max_symbol_weight=0.25,
        ruin_equity_threshold=1.0,
    )

    sorted_trades = sorted(trades, key=lambda t: t.entry_time_ms)
    net_pnls, gross_pnls, net_bps, gross_bps = [], [], [], []

    for tr in sorted_trades:
        can_open, _, alloc = ledger.can_open_position(
            tr.symbol, tr.notional_usd, entry_friction_rate=(f_in + sp_in + sl_in) / 10_000.0
        )
        if not can_open:
            continue
        pos = ledger.open_position(
            tr.symbol, TradeSide[tr.side], tr.entry_price, tr.entry_price, alloc,
            f_in, sp_in, sl_in, tr.entry_time_ms, tr.entry_bar
        )
        if pos is None:
            continue
        res = ledger.close_position(
            tr.symbol, tr.exit_price, f_out, sp_out, sl_out, tr.exit_time_ms
        )
        if res is not None:
            g_pnl, n_pnl = res
            gross_pnls.append(g_pnl)
            net_pnls.append(n_pnl)
            gross_bps.append((g_pnl / max(1e-6, alloc)) * 10_000.0)
            net_bps.append((n_pnl / max(1e-6, alloc)) * 10_000.0)

    return {
        "completed_trades": len(net_pnls),
        "gross_pnl": sum(gross_pnls),
        "net_pnl": sum(net_pnls),
        "gross_bps": gross_bps,
        "net_bps": net_bps,
    }


def compute_circular_block_bootstrap(
    series: List[float],
    block_size: int = 12,
    num_bootstraps: int = 1000,
    seed: int = 42,
) -> Tuple[float, float, float]:
    n = len(series)
    if n < 10:
        return 0.0, 0.0, 0.0
    arr = np.array(series, dtype=np.float64)
    rng = np.random.default_rng(seed)
    circ_arr = np.concatenate([arr, arr[:block_size]])
    num_blocks = int(np.ceil(n / block_size))

    boot_means = np.zeros(num_bootstraps)
    for b in range(num_bootstraps):
        start_indices = rng.integers(0, n, size=num_blocks)
        resampled = np.concatenate([circ_arr[idx : idx + block_size] for idx in start_indices])[:n]
        boot_means[b] = np.mean(resampled)

    return float(np.percentile(boot_means, 2.5)), float(np.mean(boot_means)), float(np.percentile(boot_means, 97.5))


def compute_effective_sample_size(series: List[float]) -> Tuple[float, float]:
    n = len(series)
    if n < 5:
        return 0.0, float(n)
    s = pd.Series(series)
    rho_1 = float(s.autocorr(lag=1))
    if np.isnan(rho_1):
        rho_1 = 0.0
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
    if sample_len <= 1 or sharpe_ratio <= 0.0:
        return 0.0
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
    return float(stats.norm.cdf(z_stat))


def main():
    print("=" * 80)
    print("PHASE E: INDEPENDENT STATISTICAL AUDIT & MULTI-BLOCK SENSITIVITY")
    print("=" * 80)

    # 1. Load canonical data
    raw_panel = load_canonical_data(sample_bars=40000)
    context_panel = {s: compute_market_context_dataframe(df) for s, df in raw_panel.items()}
    enriched_panel = compute_cross_asset_context(context_panel, btc_symbol="BTCUSDT")

    # 2. Backtest all 6 hypotheses across all 10 assets
    hypothesis_trades: Dict[str, List[TradeRecord]] = {h: [] for h in HYPOTHESIS_IDS}
    for h_id in HYPOTHESIS_IDS:
        for sym, df in enriched_panel.items():
            hypothesis_trades[h_id].extend(backtest_single_hypothesis(df, h_id, symbol=sym))

    # 3. Multi-Block Bootstrap Sensitivity & Multiple Testing across 30 cells
    family_results = []
    raw_p_values = []
    sharpe_estimates = []

    print("\nAuditing 30-cell experiment family and block-length sensitivity...")
    for h_id in HYPOTHESIS_IDS:
        trades = hypothesis_trades[h_id]
        for reg in REGIMES:
            sim = run_portfolio_simulation(trades, reg)
            net_rets = sim["net_bps"]
            gross_rets = sim["gross_bps"]
            n_trades = sim["completed_trades"]

            # Autocorrelation and N_eff
            rho_1, n_eff = compute_effective_sample_size(net_rets)

            # Circular Block Bootstrap sensitivity across b = 6, 12, 24
            ci_6_low, ci_6_mean, ci_6_high = compute_circular_block_bootstrap(net_rets, block_size=6)
            ci_12_low, ci_12_mean, ci_12_high = compute_circular_block_bootstrap(net_rets, block_size=12)
            ci_24_low, ci_24_mean, ci_24_high = compute_circular_block_bootstrap(net_rets, block_size=24)

            # Gross CI at b=12
            ci_grs_low, ci_grs_mean, ci_grs_high = compute_circular_block_bootstrap(gross_rets, block_size=12)

            # Standard error and raw p-value against H0: mean net <= 0
            if n_trades >= 10:
                se = (ci_12_high - ci_12_low) / (2 * 1.96) if ci_12_high > ci_12_low else 1.0
                mean_est = ci_12_mean
                z_score = mean_est / max(1e-6, se)
                p_val = float(1.0 - stats.norm.cdf(z_score))
                sharpe_ann = float((mean_est / max(1.0, np.std(net_rets))) * math.sqrt(252 * 288)) if np.std(net_rets) > 0 else 0.0
            else:
                p_val = 1.0
                sharpe_ann = 0.0

            raw_p_values.append(p_val)
            sharpe_estimates.append(sharpe_ann)

            family_results.append({
                "hypothesis_id": h_id,
                "execution_regime": reg,
                "completed_trades": n_trades,
                "effective_n": float(round(n_eff, 1)),
                "autocorr_rho_1": float(round(rho_1, 4)),
                "gross_pnl_usd": float(round(sim["gross_pnl"], 2)),
                "net_pnl_usd": float(round(sim["net_pnl"], 2)),
                "gross_exp_bps": float(round(np.mean(gross_rets) if gross_rets else 0.0, 2)),
                "gross_ci_b12": [round(ci_grs_low, 2), round(ci_grs_high, 2)],
                "net_exp_bps": float(round(np.mean(net_rets) if net_rets else 0.0, 2)),
                "net_ci_b6": [round(ci_6_low, 2), round(ci_6_high, 2)],
                "net_ci_b12": [round(ci_12_low, 2), round(ci_12_high, 2)],
                "net_ci_b24": [round(ci_24_low, 2), round(ci_24_high, 2)],
                "raw_p_value": float(round(p_val, 6)),
                "sharpe_ann": float(round(sharpe_ann, 2)),
            })

    # 4. Holm-Bonferroni correction across the COMPLETE 30-cell family
    m_family = len(family_results)  # 30 trials
    sorted_idx = np.argsort(raw_p_values)
    adj_p_values = np.zeros(m_family)

    for rank, idx in enumerate(sorted_idx):
        adj = raw_p_values[idx] * (m_family - rank)
        adj_p_values[idx] = min(1.0, adj)

    for r in range(1, m_family):
        cur_i = sorted_idx[r]
        prev_i = sorted_idx[r - 1]
        adj_p_values[cur_i] = max(adj_p_values[cur_i], adj_p_values[prev_i])

    # 5. Deflated Sharpe Ratio across the 30-cell family
    var_sharpe = float(np.var(sharpe_estimates)) if len(sharpe_estimates) > 1 else 0.1

    for i, res in enumerate(family_results):
        res["holm_bonferroni_p_family30"] = float(round(adj_p_values[i], 6))
        res["family_alpha_significant_05"] = bool(adj_p_values[i] < 0.05)
        dsr = compute_deflated_sharpe_ratio(
            sharpe_ratio=max(0.0, res["sharpe_ann"]),
            n_trials=30,
            var_sharpe=var_sharpe,
            skewness=-0.5,
            kurtosis=3.5,
            sample_len=int(res["effective_n"])
        )
        res["deflated_sharpe_ratio"] = float(round(dsr, 4))
        res["statistical_verdict"] = (
            "STATISTICALLY_SIGNIFICANT_ALPHA"
            if res["family_alpha_significant_05"] and res["net_pnl_usd"] > 0
            else "FAIL_TO_REJECT_NULL (NO DEMONSTRATED NET ALPHA)"
        )

    # Save to JSON
    with open(OUT_DIR / "M5_12_2_1_STATISTICAL_AUDIT_DATA.json", "w") as f:
        json.dump(family_results, f, indent=2)

    print("\nPhase E Statistical Audit Complete. Results written to M5_12_2_1_STATISTICAL_AUDIT_DATA.json")
    return family_results


if __name__ == "__main__":
    main()
