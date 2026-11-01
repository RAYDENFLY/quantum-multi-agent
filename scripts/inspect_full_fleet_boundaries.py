"""
QUANTUM Phase 5.5.0.8: Full Fleet Temporal Boundary Scanner.
Inspects metadata of all 11 symbols across timeframes 5m, 15m, 1h.
"""

import os
import glob
import pyarrow.parquet as pq
import pandas as pd

base_dir = "data/historical/canonical/exchange=ASTER"
symbols = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT", "XMRUSDT"
]
timeframes = ["5m", "15m", "1h"]

holdout_start_ms = int(pd.Timestamp("2026-11-01 00:00:00+00:00").timestamp() * 1000)

results = []
for sym in symbols:
    for tf in timeframes:
        dir_path = os.path.join(base_dir, f"symbol={sym}", f"timeframe={tf}")
        if not os.path.exists(dir_path):
            results.append((sym, tf, "MISSING", None, None, 0, False))
            continue
        parquet_files = sorted(glob.glob(os.path.join(dir_path, "*.parquet")))
        total_rows = 0
        min_open_ms = None
        max_close_ms = None
        for pf in parquet_files:
            pfile = pq.ParquetFile(pf)
            total_rows += pfile.metadata.num_rows
            tbl = pfile.read(["open_time_ms", "close_time_ms"])
            p_min_open = tbl["open_time_ms"].to_pandas().min()
            p_max_close = tbl["close_time_ms"].to_pandas().max()
            if min_open_ms is None or p_min_open < min_open_ms:
                min_open_ms = p_min_open
            if max_close_ms is None or p_max_close > max_close_ms:
                max_close_ms = p_max_close

        violates_holdout = max_close_ms >= holdout_start_ms if max_close_ms else False
        min_open_str = str(pd.to_datetime(min_open_ms, unit="ms", utc=True)) if min_open_ms else "N/A"
        max_close_str = str(pd.to_datetime(max_close_ms, unit="ms", utc=True)) if max_close_ms else "N/A"
        results.append((sym, tf, "EXISTS", min_open_str, max_close_str, total_rows, violates_holdout))

print(f"{'Symbol':8s} | {'TF':3s} | {'Status':6s} | {'Rows':7s} | {'Min Open':25s} | {'Max Close':28s} | {'Violation'}")
print("-" * 95)
for r in results:
    print(f"{r[0]:8s} | {r[1]:3s} | {r[2]:6s} | {r[5]:7d} | {r[3]:25s} | {r[4]:28s} | {r[6]}")
