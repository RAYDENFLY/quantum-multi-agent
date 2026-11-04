"""Phase H: HYP-05 Net Expectancy Forensic Reconciliation.

Forensically reconciles HYP-05 expectancy metrics across all 5 execution regimes:
1. TAKER_TAKER
2. MAKER_MAKER
3. MAKER_TAKER
4. TAKER_MAKER
5. ZERO_FRICTION_DIAGNOSTIC

Disentangles denominators:
- Per-unit notional basis (bps of executed trade notional)
- Per completed trade episode ($/trade)
- Portfolio equity return basis (% of initial/current capital)
- Daily annualized net return

Ensures 26 bps roundtrip taker friction and 1.85 bps gross expectancy
are evaluated on compatible mathematical bases.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "src"))

from quantum.accounting.event_ledger import EventDrivenPortfolioLedger
from quantum.accounting.fee_schedules import FeeScheduleRegistry
from quantum.domain.enums import TradeSide
from quantum.features.market_context import (
    compute_market_context_dataframe,
    compute_cross_asset_context,
)
from quantum.strategies.hypothesis_engine import (
    backtest_single_hypothesis,
    TradeRecord,
)

OUT_DIR = ROOT / "audit" / "strategy_research" / "milestone_5_12_2_2_active_mtm_risk_control"
CANONICAL_DIR = ROOT / "data" / "historical" / "canonical" / "exchange=ASTER"
SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "ADAUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT"
]


def load_canonical_data(sample_bars: int = 40000):
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


def run_expectancy_audit():
    print("Loading canonical data and computing cross-asset context...")
    raw_panel = load_canonical_data(sample_bars=40000)
    context_panel = {s: compute_market_context_dataframe(df) for s, df in raw_panel.items()}
    enriched_panel = compute_cross_asset_context(context_panel, btc_symbol="BTCUSDT")

    print("Generating HYP-05 trade episodes...")
    all_trades: list[TradeRecord] = []
    for sym, df in enriched_panel.items():
        all_trades.extend(backtest_single_hypothesis(df, "HYP-05", symbol=sym))
    sorted_trades = sorted(all_trades, key=lambda t: t.entry_time_ms)
    print(f"Total unconstrained completed episodes: {len(sorted_trades):,}")

    regimes = [
        ("ZERO_FRICTION_DIAGNOSTIC", 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        ("TAKER_TAKER", 10.0, 10.0, 1.0, 1.0, 2.0, 2.0, 0.0, 0.0),
        ("MAKER_MAKER", 4.0, 4.0, 0.0, 0.0, 0.0, 0.0, 1.5, 1.5),
        ("MAKER_TAKER", 4.0, 10.0, 0.0, 1.0, 0.0, 2.0, 1.5, 0.0),
        ("TAKER_MAKER", 10.0, 4.0, 1.0, 0.0, 2.0, 0.0, 0.0, 1.5),
    ]

    results = []

    for name, f_in, f_out, sp_in, sp_out, sl_in, sl_out, adv_in, adv_out in regimes:
        ledger = EventDrivenPortfolioLedger(100.0, max_gross_exposure=1.0, max_concurrent_positions=4, max_symbol_weight=0.25, safety_buffer=0.0050)
        tot_fric_in = (f_in + sp_in + sl_in + adv_in) / 10_000.0
        tot_fric_out = (f_out + sp_out + sl_out + adv_out) / 10_000.0
        roundtrip_fric_bps = (f_in + f_out + sp_in + sp_out + sl_in + sl_out + adv_in + adv_out)

        executed_count = 0
        tot_turnover = 0.0
        tot_gross = 0.0
        tot_net = 0.0
        tot_fee = 0.0
        tot_spread = 0.0
        tot_slip = 0.0
        tot_adv = 0.0
        tot_funding = 0.0

        for tr in sorted_trades:
            ok, r, alloc = ledger.can_open_position(tr.symbol, tr.notional_usd, entry_friction_rate=tot_fric_in)
            if not ok:
                continue

            pos = ledger.open_position(
                tr.symbol, TradeSide[tr.side], tr.entry_price, tr.entry_price, alloc,
                f_in, sp_in, sl_in + adv_in, tr.entry_time_ms, tr.entry_bar
            )
            if pos is None:
                continue

            executed_count += 1
            tot_turnover += alloc

            # Accrue funding
            hold_hours = tr.duration_minutes / 60.0
            intervals = int(hold_hours / 8.0)
            for _ in range(intervals):
                tot_funding += alloc * 0.0001

            res = ledger.close_position(
                tr.symbol, tr.exit_price, f_out, sp_out, sl_out + adv_out, tr.exit_time_ms
            )
            if res is not None:
                g_pnl, n_pnl = res
                tot_gross += g_pnl
                tot_net += n_pnl
                tot_fee += alloc * ((f_in + f_out) / 10_000.0)
                tot_spread += alloc * ((sp_in + sp_out) / 10_000.0)
                tot_slip += alloc * ((sl_in + sl_out) / 10_000.0)
                tot_adv += alloc * ((adv_in + adv_out) / 10_000.0)

        # Expectancy on notional turnover basis (bps)
        gross_exp_bps = (tot_gross / tot_turnover * 10_000.0) if tot_turnover > 0 else 0.0
        net_exp_bps = (tot_net / tot_turnover * 10_000.0) if tot_turnover > 0 else 0.0
        fee_exp_bps = (tot_fee / tot_turnover * 10_000.0) if tot_turnover > 0 else 0.0
        spread_exp_bps = (tot_spread / tot_turnover * 10_000.0) if tot_turnover > 0 else 0.0
        slip_exp_bps = (tot_slip / tot_turnover * 10_000.0) if tot_turnover > 0 else 0.0
        adv_exp_bps = (tot_adv / tot_turnover * 10_000.0) if tot_turnover > 0 else 0.0
        fund_exp_bps = (tot_funding / tot_turnover * 10_000.0) if tot_turnover > 0 else 0.0

        # Drawdown
        df_ev = ledger.to_dataframe()
        if not df_ev.empty and "equity" in df_ev.columns:
            eqs = df_ev["equity"].to_numpy()
            pks = np.maximum.accumulate(eqs)
            dds = (pks - eqs) / np.maximum(pks, 1e-6) * 100.0
            max_dd = float(np.max(dds))
        else:
            max_dd = 0.0

        # Mean net daily return (over 138.8 days)
        days = (sorted_trades[-1].exit_time_ms - sorted_trades[0].entry_time_ms) / 86_400_000.0
        mean_net_daily_ret = ((tot_net / 100.0) / days) * 100.0 if days > 0 else 0.0

        results.append({
            "regime": name,
            "executed_trades": executed_count,
            "total_turnover_usd": round(tot_turnover, 2),
            "gross_pnl_usd": round(tot_gross, 2),
            "net_pnl_usd": round(tot_net, 2),
            "gross_expectancy_bps": round(gross_exp_bps, 2),
            "fee_drag_bps": round(fee_exp_bps, 2),
            "spread_drag_bps": round(spread_exp_bps, 2),
            "slippage_drag_bps": round(slip_exp_bps, 2),
            "adverse_selection_bps": round(adv_exp_bps, 2),
            "funding_drag_bps": round(fund_exp_bps, 2),
            "net_expectancy_bps": round(net_exp_bps, 2),
            "mean_net_daily_return_pct": round(mean_net_daily_ret, 3),
            "max_drawdown_pct": round(max_dd, 2),
            "final_equity_usd": round(ledger.equity, 2),
        })

    df_exp = pd.DataFrame(results)
    print("\n=== HYP-05 EXPECTANCY RECONCILIATION ACROSS 5 REGIMES ===")
    print(df_exp.to_string(index=False))
    return df_exp

if __name__ == "__main__":
    run_expectancy_audit()
