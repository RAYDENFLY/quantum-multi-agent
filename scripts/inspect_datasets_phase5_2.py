"""Reconciliation and audit script for Phase 5.2.
Inspects actual Parquet files on disk across canonical, features, features_research, and raw.
Also inspects historical.db metadata.
"""

import sys
import hashlib
from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np

BASE_DIR = Path("data/historical")
EXCHANGE = "ASTER"
SYMBOLS = [
    "ADAUSDT", "XRPUSDT", "BTCUSDT", "BNBUSDT", "ETHUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "XMRUSDT", "DOGEUSDT", "LTCUSDT"
]
TIMEFRAMES = ["1h", "15m", "5m"]
TF_MS = {"1h": 3600000, "15m": 900000, "5m": 300000}

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def get_layer_parquet_files(layer: str, symbol: str, tf: str):
    p = BASE_DIR / layer / f"exchange={EXCHANGE}" / f"symbol={symbol}" / f"timeframe={tf}"
    if not p.exists():
        return []
    return sorted(list(p.glob("*.parquet")))

def read_layer_df(layer: str, symbol: str, tf: str) -> pd.DataFrame:
    files = get_layer_parquet_files(layer, symbol, tf)
    if not files:
        return pd.DataFrame()
    dfs = [pd.read_parquet(f) for f in files]
    return pd.concat(dfs, ignore_index=True)

def main():
    print("Beginning Phase 5.2 dataset audit and reconciliation...")
    results = []
    
    # 1. Inspect DB
    conn = sqlite3.connect(BASE_DIR / "historical.db")
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    print(f"DB Tables: {tables}")
    
    # Check quarantine table or logs if any
    for t in tables:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        cnt = cur.fetchone()[0]
        print(f"  Table {t}: {cnt} rows")

    # 2. Iterate through all 33 datasets
    for symbol in SYMBOLS:
        for tf in TIMEFRAMES:
            ds_key = f"{symbol}_{tf}"
            interval_ms = TF_MS[tf]
            
            # Canonical
            can_files = get_layer_parquet_files("canonical", symbol, tf)
            can_df = read_layer_df("canonical", symbol, tf)
            
            # Features
            feat_files = get_layer_parquet_files("features", symbol, tf)
            feat_df = read_layer_df("features", symbol, tf)
            
            # Research Features
            res_files = get_layer_parquet_files("features_research", symbol, tf)
            res_df = read_layer_df("features_research", symbol, tf)
            
            # Raw
            raw_files = get_layer_parquet_files("raw", symbol, tf)
            raw_df = read_layer_df("raw", symbol, tf)
            
            can_len = len(can_df)
            feat_len = len(feat_df)
            res_len = len(res_df)
            raw_len = len(raw_df)
            
            # Check timestamps and ordering in canonical
            can_first_ts = int(can_df["open_time_ms"].min()) if can_len > 0 else 0
            can_last_ts = int(can_df["open_time_ms"].max()) if can_len > 0 else 0
            can_dups = int(can_df["open_time_ms"].duplicated().sum()) if can_len > 0 else 0
            
            # Missing intervals in canonical
            missing_count = 0
            if can_len > 1:
                diffs = can_df["open_time_ms"].diff().dropna()
                gaps = (diffs // interval_ms) - 1
                missing_count = int(gaps[gaps > 0].sum())
            
            # OHLC validity in canonical
            ohlc_invalid = 0
            if can_len > 0:
                h_lt_o = can_df["high"] < can_df["open"]
                h_lt_c = can_df["high"] < can_df["close"]
                l_gt_o = can_df["low"] > can_df["open"]
                l_gt_c = can_df["low"] > can_df["close"]
                h_lt_l = can_df["high"] < can_df["low"]
                v_lt_0 = can_df["volume"] < 0
                ohlc_invalid = int((h_lt_o | h_lt_c | l_gt_o | l_gt_c | h_lt_l | v_lt_0).sum())
            
            # In raw, check if there are invalid OHLC rows (e.g. BTCUSDT quarantined)
            raw_ohlc_invalid = 0
            if raw_len > 0 and "raw_high" in raw_df.columns:
                ro = raw_df["raw_open"].astype(float)
                rh = raw_df["raw_high"].astype(float)
                rl = raw_df["raw_low"].astype(float)
                rc = raw_df["raw_close"].astype(float)
                rv = raw_df["raw_volume"].astype(float)
                rh_lt_ro = rh < ro
                rh_lt_rc = rh < rc
                rl_gt_ro = rl > ro
                rl_gt_rc = rl > rc
                rh_lt_rl = rh < rl
                rv_lt_0 = rv < 0
                raw_ohlc_invalid = int((rh_lt_ro | rh_lt_rc | rl_gt_ro | rl_gt_rc | rh_lt_rl | rv_lt_0).sum())
                if raw_ohlc_invalid > 0:
                    inv_rows = raw_df[rh_lt_ro | rh_lt_rc | rl_gt_ro | rl_gt_rc | rh_lt_rl | rv_lt_0]
                    print(f"  [QUARANTINE AUDIT] Found {raw_ohlc_invalid} invalid rows in raw {symbol} {tf}:")
                    for _, r in inv_rows.iterrows():
                        print(f"    ts={r['exchange_candle_ts_ms']}, O={r['raw_open']}, H={r['raw_high']}, L={r['raw_low']}, C={r['raw_close']}")

            # Warmup rows removed
            warmup_removed = can_len - res_len
            
            # Hashes of partition files
            can_hashes = [compute_sha256(f) for f in can_files]
            combined_can_hash = hashlib.sha256("".join(can_hashes).encode()).hexdigest()
            
            res_hashes = [compute_sha256(f) for f in res_files]
            combined_res_hash = hashlib.sha256("".join(res_hashes).encode()).hexdigest()

            results.append({
                "symbol": symbol,
                "timeframe": tf,
                "canonical_rows": can_len,
                "features_rows": feat_len,
                "research_rows": res_len,
                "raw_rows": raw_len,
                "warmup_removed": warmup_removed,
                "diff_can_minus_res": can_len - res_len,
                "diff_feat_minus_can": feat_len - can_len,
                "first_ts": can_first_ts,
                "last_ts": can_last_ts,
                "missing_intervals": missing_count,
                "duplicate_ts": can_dups,
                "canonical_invalid_ohlc": ohlc_invalid,
                "raw_invalid_ohlc": raw_ohlc_invalid,
                "can_files_count": len(can_files),
                "res_files_count": len(res_files),
                "combined_can_sha256": combined_can_hash,
                "combined_res_sha256": combined_res_hash,
            })
            print(f"Checked {ds_key}: can={can_len}, feat={feat_len}, res={res_len}, raw={raw_len}, warmup_diff={can_len - res_len}, can_inv={ohlc_invalid}, raw_inv={raw_ohlc_invalid}")
    
    df_res = pd.DataFrame(results)
    df_res.to_csv(BASE_DIR / "reconciliation_audit_summary.csv", index=False)
    print("\nTotal canonical rows across all 33:", df_res["canonical_rows"].sum())
    print("Total features rows across all 33:", df_res["features_rows"].sum())
    print("Total research rows across all 33:", df_res["research_rows"].sum())
    print("Total raw rows across all 33:", df_res["raw_rows"].sum())

if __name__ == "__main__":
    main()
