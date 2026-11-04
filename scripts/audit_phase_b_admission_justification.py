"""Empirical analysis for Phase B: Admission Buffer Justification.

Analyzes historical 5m volatility, price range, spread, slippage, and fee impact
across the canonical dataset to derive the mathematically rigorous admission buffer.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parent.parent
CANONICAL_DIR = ROOT / "data" / "historical" / "canonical" / "exchange=ASTER"

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT",
    "ADAUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT"
]

def analyze_volatility():
    stats = []
    for sym in SYMBOLS:
        p = CANONICAL_DIR / f"symbol={sym}" / "timeframe=5m"
        files = sorted(p.glob("*.parquet"))
        dfs = [
            pq.ParquetFile(str(f)).read(
                columns=["open_time_ms", "open", "high", "low", "close", "volume"]
            ).to_pandas()
            for f in files
        ]
        df = pd.concat(dfs, ignore_index=True)
        # Filter sealed holdout boundary
        df = df[df["open_time_ms"] < 1_793_491_200_000].copy()
        
        # 5m bar range = (high - low) / open * 10,000 (in bps)
        bar_range_bps = ((df["high"] - df["low"]) / df["open"]) * 10_000.0
        # 5m bar return = abs(close - open) / open * 10,000 (in bps)
        bar_return_bps = (abs(df["close"] - df["open"]) / df["open"]) * 10_000.0
        
        stats.append({
            "symbol": sym,
            "bars": len(df),
            "median_range_bps": np.median(bar_range_bps),
            "p90_range_bps": np.percentile(bar_range_bps, 90),
            "p95_range_bps": np.percentile(bar_range_bps, 95),
            "p99_range_bps": np.percentile(bar_range_bps, 99),
            "median_ret_bps": np.median(bar_return_bps),
            "p95_ret_bps": np.percentile(bar_return_bps, 95),
            "p99_ret_bps": np.percentile(bar_return_bps, 99),
        })
    
    df_stats = pd.DataFrame(stats)
    print("=== EMPIRICAL 5-MINUTE VOLATILITY STATS (bps) ===")
    print(df_stats.to_string(index=False))
    
    agg = {
        "median_range_bps": df_stats["median_range_bps"].median(),
        "p95_range_bps": df_stats["p95_range_bps"].median(),
        "p99_range_bps": df_stats["p99_range_bps"].median(),
        "median_ret_bps": df_stats["median_ret_bps"].median(),
        "p95_ret_bps": df_stats["p95_ret_bps"].median(),
        "p99_ret_bps": df_stats["p99_ret_bps"].median(),
    }
    print("\nAggregate Universe Medians:")
    for k, v in agg.items():
        print(f"  {k}: {v:.2f} bps")

if __name__ == "__main__":
    analyze_volatility()
