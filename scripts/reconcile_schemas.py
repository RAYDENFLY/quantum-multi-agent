import pandas as pd
from pathlib import Path

base_feat = Path("data/historical/features/exchange=ASTER")
base_res = Path("data/historical/features_research/exchange=ASTER")

for sym in ["BTCUSDT", "XMRUSDT"]:
    f_feat = sorted((base_feat / f"symbol={sym}/timeframe=5m").glob("*.parquet"))[0]
    f_res = sorted((base_res / f"symbol={sym}/timeframe=5m").glob("*.parquet"))[0]
    
    df_feat = pd.read_parquet(f_feat)
    df_res = pd.read_parquet(f_res)
    
    cols_feat = set(df_feat.columns)
    cols_res = set(df_res.columns)
    
    removed = sorted(list(cols_feat - cols_res))
    added = sorted(list(cols_res - cols_feat))
    
    print(f"=== {sym} SCHEMA RECONCILIATION ===")
    print(f"Features (57) count: {len(cols_feat)}")
    print(f"Research (38) count: {len(cols_res)}")
    print(f"Removed features ({len(removed)}): {removed}")
    print(f"Added features ({len(added)}): {added}\n")
