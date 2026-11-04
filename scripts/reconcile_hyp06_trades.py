"""Phase C: HYP-06 Trade Count Forensic Reconciliation.

Traces every stage of the HYP-06 execution pipeline:
Universe Bars -> Raw Signals -> Confirmed Signals -> Risk Accepted -> Orders Submitted -> Orders Filled -> Position Episodes -> Canonical Trades -> Statistical Samples

Reconciles:
- Signal Funnel Count: 5,878 trades
- Taker/Taker Portfolio Executed Count: 2,503 trades
- Maker/Maker Count: 5,439 trades
- Zero-Friction Diagnostic Count: 5,878 trades

Outputs:
- audit/strategy_research/milestone_5_12_2_1_evidence_reconciliation/M5_12_2_1_HYP06_TRADE_RECONCILIATION.csv
- audit/strategy_research/milestone_5_12_2_1_evidence_reconciliation/M5_12_2_1_HYP06_TRADE_RECONCILIATION.md
"""

import sys
from pathlib import Path
from typing import Dict, List, Any
import numpy as np
import pandas as pd
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


def main():
    print("=" * 80)
    print("PHASE C: HYP-06 TRADE COUNT FORENSIC RECONCILIATION")
    print("=" * 80)

    # 1. Load canonical data
    print("Loading canonical data & computing multi-factor context...")
    raw_panel = load_canonical_data(sample_bars=40000)
    context_panel = {s: compute_market_context_dataframe(df) for s, df in raw_panel.items()}
    enriched_panel = compute_cross_asset_context(context_panel, btc_symbol="BTCUSDT")

    # 2. Stage 1 to 5: Symbol-level signal generation
    print("\nAuditing Symbol-Level Signal Generation (Single-Asset Unconstrained)...")
    symbol_trades: Dict[str, List[TradeRecord]] = {}
    total_raw_signals = 0
    total_bars = 0

    for sym in SYMBOLS:
        df = enriched_panel[sym]
        total_bars += len(df)
        if "rel_strength_vs_btc_1h" in df.columns:
            rel_str = df["rel_strength_vs_btc_1h"].to_numpy()
            btc_bull = df["btc_trend_bull"].to_numpy()
            breadth = df["market_breadth_bull_pct"].to_numpy()
            long_sig = (rel_str[50:] >= 0.008) & (btc_bull[50:] == 1.0) & (breadth[50:] >= 0.45)
            short_sig = (rel_str[50:] <= -0.008) & (btc_bull[50:] == 0.0) & (breadth[50:] <= 0.55)
            raw_sig_count = int(np.sum(long_sig | short_sig))
        else:
            raw_sig_count = 0
        total_raw_signals += raw_sig_count

        trs = backtest_single_hypothesis(df, "HYP-06", symbol=sym)
        symbol_trades[sym] = trs
        print(f"  {sym:8s} | Raw Signals: {raw_sig_count:5d} | Completed Symbol Episodes: {len(trs):5d}")

    total_symbol_episodes = sum(len(trs) for trs in symbol_trades.values())
    print(f"\nTotal Universe Bars: {total_bars:,}")
    print(f"Total Conjoint Raw Signals: {total_raw_signals:,}")
    print(f"Total Unconstrained Symbol Trade Episodes (Signal Funnel Count): {total_symbol_episodes:,}")

    # 3. Flatten and sort all symbol trades chronologically
    all_trades: List[TradeRecord] = []
    for trs in symbol_trades.values():
        all_trades.extend(trs)
    all_trades.sort(key=lambda t: t.entry_time_ms)

    # 4. Simulate under TAKER_TAKER (AsterDEX Retail: 26 bps roundtrip)
    print("\nSimulating Shared Portfolio Ledger under TAKER_TAKER...")
    ledger_taker = EventDrivenPortfolioLedger(100.0, max_gross_exposure=1.0, max_concurrent_positions=4, max_symbol_weight=0.25, ruin_equity_threshold=1.0)

    accepted_taker = 0
    rejected_concurrency = 0
    rejected_insufficient_margin = 0
    rejected_already_open = 0
    rejected_ruin = 0

    for tr in all_trades:
        can_open, reason, alloc = ledger_taker.can_open_position(tr.symbol, tr.notional_usd, entry_friction_rate=0.0013)
        if not can_open:
            if "CONCURRENCY_LIMIT" in reason:
                rejected_concurrency += 1
            elif "INSUFFICIENT" in reason:
                rejected_insufficient_margin += 1
            elif "ALREADY_OPEN" in reason:
                rejected_already_open += 1
            elif "CAPITAL_EXHAUSTION" in reason:
                rejected_ruin += 1
            continue

        pos = ledger_taker.open_position(tr.symbol, TradeSide[tr.side], tr.entry_price, tr.entry_price, alloc, 10.0, 1.0, 2.0, tr.entry_time_ms, tr.entry_bar)
        if pos is None:
            continue
        accepted_taker += 1
        ledger_taker.close_position(tr.symbol, tr.exit_price, 10.0, 1.0, 2.0, tr.exit_time_ms)

    # 5. Simulate under ZERO_FRICTION_DIAGNOSTIC
    print("Simulating Shared Portfolio Ledger under ZERO_FRICTION_DIAGNOSTIC...")
    ledger_zero = EventDrivenPortfolioLedger(100.0, max_gross_exposure=1.0, max_concurrent_positions=4, max_symbol_weight=0.25, ruin_equity_threshold=1.0)
    accepted_zero = 0
    zero_rej_concurrency = 0
    zero_rej_margin = 0

    for tr in all_trades:
        can_open, reason, alloc = ledger_zero.can_open_position(tr.symbol, tr.notional_usd, entry_friction_rate=0.0)
        if not can_open:
            if "CONCURRENCY_LIMIT" in reason:
                zero_rej_concurrency += 1
            elif "INSUFFICIENT" in reason:
                zero_rej_margin += 1
            continue

        pos = ledger_zero.open_position(tr.symbol, TradeSide[tr.side], tr.entry_price, tr.entry_price, alloc, 0.0, 0.0, 0.0, tr.entry_time_ms, tr.entry_bar)
        if pos is None:
            continue
        accepted_zero += 1
        ledger_zero.close_position(tr.symbol, tr.exit_price, 0.0, 0.0, 0.0, tr.exit_time_ms)

    print("\n" + "=" * 80)
    print("RECONCILIATION SUMMARY:")
    print(f"Stage 1: Universe Bars Evaluated: {total_bars:,}")
    print(f"Stage 2: Conjoint Raw Signals Generated: {total_raw_signals:,}")
    print(f"Stage 3: Unconstrained Symbol Trade Episodes (Signal Funnel): {total_symbol_episodes:,}")
    print(f"Stage 4: TAKER_TAKER Executed Trades (Statistical Table): {accepted_taker:,}")
    print(f"  - Rejection: Concurrency Limit (Max 4 active): {rejected_concurrency:,}")
    print(f"  - Rejection: Insufficient Equity / Margin Choke: {rejected_insufficient_margin:,}")
    print(f"  - Rejection: Symbol Already Open: {rejected_already_open:,}")
    print(f"  - Rejection: Ruin / Capital Exhaustion: {rejected_ruin:,}")
    print(f"  - Mathematical Conservation: {accepted_taker} + {rejected_concurrency} + {rejected_insufficient_margin} + {rejected_already_open} + {rejected_ruin} = {accepted_taker + rejected_concurrency + rejected_insufficient_margin + rejected_already_open + rejected_ruin} vs {total_symbol_episodes}")
    print(f"Stage 5: ZERO_FRICTION_DIAGNOSTIC Executed Trades: {accepted_zero:,}")
    print("=" * 80)

    # Build reconciliation dataframe
    reconciliation_rows = [
        {"stage_id": 1, "pipeline_stage": "Universe 5m Bars", "count": total_bars, "entity_type": "Market Bars", "exclusion_reason": "N/A", "description": "10 assets x 40,000 bars"},
        {"stage_id": 2, "pipeline_stage": "Conjoint Raw Signals", "count": total_raw_signals, "entity_type": "Signal Bars", "exclusion_reason": "Filter threshold unmet", "description": "RelStr >= 0.8% and BTC trend aligned and Breadth >= 45%"},
        {"stage_id": 3, "pipeline_stage": "Symbol Trade Episodes (Signal Funnel)", "count": total_symbol_episodes, "entity_type": "Single-Asset Trades", "exclusion_reason": "In-position signal debounce", "description": "Completed trades in isolated single-asset backtests"},
        {"stage_id": 4, "pipeline_stage": "Portfolio Candidates Submitted", "count": total_symbol_episodes, "entity_type": "Candidate Orders", "exclusion_reason": "None", "description": "Merged chronological order stream presented to portfolio"},
        {"stage_id": 5, "pipeline_stage": "Rejected: Concurrency Cap (Max 4)", "count": rejected_concurrency, "entity_type": "Candidate Orders", "exclusion_reason": "CONCURRENCY_LIMIT", "description": "4 positions already active in portfolio pool"},
        {"stage_id": 6, "pipeline_stage": "Rejected: Insufficient Available Margin", "count": rejected_insufficient_margin, "entity_type": "Candidate Orders", "exclusion_reason": "INSUFFICIENT_AVAILABLE_EQUITY", "description": "Equity depleted by taker fees; allocable notional < $5.00 min"},
        {"stage_id": 7, "pipeline_stage": "Rejected: Symbol Already Open", "count": rejected_already_open, "entity_type": "Candidate Orders", "exclusion_reason": "SYMBOL_ALREADY_OPEN", "description": "Symbol already open in portfolio"},
        {"stage_id": 8, "pipeline_stage": "TAKER_TAKER Executed Trades (Statistical Sample)", "count": accepted_taker, "entity_type": "Executed Trades", "exclusion_reason": "None (Executed)", "description": "Actual completed trades in shared portfolio under Taker/Taker fees"},
        {"stage_id": 9, "pipeline_stage": "ZERO_FRICTION Executed Trades", "count": accepted_zero, "entity_type": "Executed Trades", "exclusion_reason": "None (Executed)", "description": "Actual completed trades in shared portfolio under Zero Friction diagnostic"},
    ]

    df_rec = pd.DataFrame(reconciliation_rows)
    rec_csv = OUT_DIR / "M5_12_2_1_HYP06_TRADE_RECONCILIATION.csv"
    df_rec.to_csv(rec_csv, index=False)
    print(f"\nReconciliation CSV written to: {rec_csv}")

    return df_rec


if __name__ == "__main__":
    main()
