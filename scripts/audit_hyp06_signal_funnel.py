"""Phase E: HYP-06 Zero-Signal Forensic Isolation and Signal Funnel Audit.

Analyzes the signal generation funnel for HYP-06 (Cross-Asset Relative Strength)
and documents the exact failure mode across both the defective (M5.12.1) and corrected pipelines.

Outputs:
- audit/strategy_research/milestone_5_12_2_exposure_invariant_patch/M5_12_2_HYP06_SIGNAL_FUNNEL.csv
- audit/strategy_research/milestone_5_12_2_exposure_invariant_patch/M5_12_2_HYP06_ZERO_SIGNAL_AUDIT.md
"""

import sys
from pathlib import Path
from typing import Dict, List, Any
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "src"))

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


def audit_hyp06_funnel():
    print("=" * 80)
    print("AUDITING HYP-06 SIGNAL FUNNEL (CROSS-ASSET RELATIVE STRENGTH)")
    print("=" * 80)

    # 1. Load canonical data
    print("Loading canonical 5m panels...")
    raw_panel = load_canonical_data(sample_bars=40000)

    # 2. Pipeline A (Defective M5.12.1): Single-asset market context only (compute_cross_asset_context omitted)
    print("Evaluating Defective Pipeline (compute_cross_asset_context omitted)...")
    defective_panel = {}
    for sym, df_raw in raw_panel.items():
        defective_panel[sym] = compute_market_context_dataframe(df_raw)

    defective_trades = {}
    for sym, df in defective_panel.items():
        trades = backtest_single_hypothesis(df, "HYP-06", symbol=sym)
        defective_trades[sym] = trades

    # 3. Pipeline B (Corrected M5.12.2): Full multi-factor pipeline with cross-asset context
    print("Evaluating Corrected Pipeline (with compute_cross_asset_context)...")
    corrected_panel = compute_cross_asset_context(defective_panel, btc_symbol="BTCUSDT")

    corrected_trades = {}
    for sym, df in corrected_panel.items():
        trades = backtest_single_hypothesis(df, "HYP-06", symbol=sym)
        corrected_trades[sym] = trades

    # 4. Detailed Stage-by-Stage Breakdown for Corrected Pipeline
    funnel_rows = []

    for sym in SYMBOLS:
        df_def = defective_panel[sym]
        df_cor = corrected_panel[sym]
        n_bars = len(df_cor)

        # Defective Pipeline stats
        def_has_col = "rel_strength_vs_btc_1h" in df_def.columns
        def_raw_signals = 0
        def_completed = len(defective_trades[sym])

        # Corrected Pipeline stats
        cor_has_col = "rel_strength_vs_btc_1h" in df_cor.columns
        
        # Unpack arrays
        rel_str = df_cor["rel_strength_vs_btc_1h"].to_numpy()
        btc_bull = df_cor["btc_trend_bull"].to_numpy()
        breadth = df_cor["market_breadth_bull_pct"].to_numpy()

        # Funnel stage counts
        cond_rel_str = np.sum((rel_str[50:] >= 0.008) | (rel_str[50:] <= -0.008))
        cond_btc_trend = np.sum((btc_bull[50:] == 1.0) | (btc_bull[50:] == 0.0))  # Always defined
        cond_breadth = np.sum((breadth[50:] >= 0.45) | (breadth[50:] <= 0.55))

        long_signals = (rel_str[50:] >= 0.008) & (btc_bull[50:] == 1.0) & (breadth[50:] >= 0.45)
        short_signals = (rel_str[50:] <= -0.008) & (btc_bull[50:] == 0.0) & (breadth[50:] <= 0.55)
        raw_signals = np.sum(long_signals | short_signals)

        cor_completed = len(corrected_trades[sym])
        
        funnel_rows.append({
            "symbol": sym,
            "total_bars_evaluated": n_bars,
            "defective_has_feature_col": def_has_col,
            "defective_raw_signals": def_raw_signals,
            "defective_completed_trades": def_completed,
            "corrected_has_feature_col": cor_has_col,
            "stage_1_relative_strength_triggers": int(cond_rel_str),
            "stage_2_btc_trend_aligned": int(cond_btc_trend),
            "stage_3_breadth_aligned": int(cond_breadth),
            "stage_4_conjoint_raw_signals": int(raw_signals),
            "stage_5_completed_trades": cor_completed,
            "funnel_conversion_rate_pct": round((cor_completed / max(1, raw_signals)) * 100.0, 2),
        })

    df_funnel = pd.DataFrame(funnel_rows)
    funnel_csv = OUT_DIR / "M5_12_2_HYP06_SIGNAL_FUNNEL.csv"
    df_funnel.to_csv(funnel_csv, index=False)
    print(f"\nFunnel CSV written to: {funnel_csv}")
    print(df_funnel[["symbol", "defective_completed_trades", "stage_4_conjoint_raw_signals", "stage_5_completed_trades", "funnel_conversion_rate_pct"]].to_string(index=False))

    # Print summary
    tot_def_trades = sum(r["defective_completed_trades"] for r in funnel_rows)
    tot_cor_trades = sum(r["stage_5_completed_trades"] for r in funnel_rows)
    print("\n" + "=" * 80)
    print(f"DEFECTIVE PIPELINE TRADES (compute_cross_asset_context omitted): {tot_def_trades}")
    print(f"CORRECTED PIPELINE TRADES (compute_cross_asset_context applied): {tot_cor_trades}")
    print("=" * 80)

    return df_funnel, corrected_trades


if __name__ == "__main__":
    audit_hyp06_funnel()
