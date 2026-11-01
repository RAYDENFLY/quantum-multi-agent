import pandas as pd
from pathlib import Path
from quantum.features.labeling import TripleBarrierLabelGenerator, BarrierOutcome
from quantum.features.temporal_split import (
    DEVELOPMENT_START_MS,
    DEVELOPMENT_END_MS,
    VALIDATION_START_MS,
    VALIDATION_END_MS,
)
from quantum.historical.storage import ParquetStorageManager

storage = ParquetStorageManager(Path("data/historical"))
gen = TripleBarrierLabelGenerator(horizon_bars=12, volatility_lookback=20, barrier_multiplier=1.5)

for sym in ["BTCUSDT", "XMRUSDT"]:
    df_can = storage.read_canonical("ASTER", sym, "5m")
    labeled = gen.generate_labels(df_can, enforce_partition_boundaries=True)
    
    ts = labeled["open_time_ms"]
    dev_mask = (ts >= DEVELOPMENT_START_MS) & (ts <= DEVELOPMENT_END_MS)
    val_mask = (ts >= VALIDATION_START_MS) & (ts <= VALIDATION_END_MS)
    dev_val_mask = dev_mask | val_mask
    
    df_dv = labeled[dev_val_mask]
    
    print(f"=== {sym} DEV+VAL AUDIT ===")
    print(f"Total Canonical: {len(df_can):,}")
    print(f"Dev rows: {dev_mask.sum():,}")
    print(f"Val rows: {val_mask.sum():,}")
    print(f"Dev+Val rows: {len(df_dv):,}")
    
    # Class distribution in Dev+Val
    lbls = df_dv["label"]
    tp = (lbls == BarrierOutcome.TP.value).sum()
    sl = (lbls == BarrierOutcome.SL.value).sum()
    exp = (lbls == BarrierOutcome.TIME_EXPIRATION.value).sum()
    amb = (lbls == BarrierOutcome.AMBIGUOUS.value).sum()
    exc = (lbls == BarrierOutcome.EXCLUDED.value).sum()
    el = tp + sl + exp
    
    print(f"Eligible: {el:,} (TP={tp:,} [{tp/el*100:.2f}%], SL={sl:,} [{sl/el*100:.2f}%], Exp={exp:,} [{exp/el*100:.2f}%])")
    print(f"Ambiguous: {amb:,} | Excluded: {exc:,}")
    print(f"Exclusion reasons:\n{df_dv['exclusion_reason'].value_counts()}\n")
