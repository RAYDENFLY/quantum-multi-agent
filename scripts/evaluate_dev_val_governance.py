"""Evaluate Multiplier Sensitivity strictly on Development and Validation partitions.
Excludes Pre-Development and Final Holdout.
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np

from quantum.domain.enums import Exchange, Timeframe
from quantum.features.labeling import BarrierOutcome, TripleBarrierLabelGenerator
from quantum.features.temporal_split import (
    DEVELOPMENT_START_MS,
    DEVELOPMENT_END_MS,
    VALIDATION_START_MS,
    VALIDATION_END_MS,
)
from quantum.historical.storage import ParquetStorageManager

BASE_DIR = Path("data/historical")
EXCHANGE = Exchange.ASTER
SYMBOLS = [
    "ADAUSDT", "XRPUSDT", "BTCUSDT", "BNBUSDT", "ETHUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "XMRUSDT", "DOGEUSDT", "LTCUSDT"
]
TIMEFRAME = Timeframe.M5
MULTIPLIERS = [1.0, 1.5, 2.0]

storage = ParquetStorageManager(BASE_DIR)

dev_val_results = {m: {"tp": 0, "sl": 0, "exp": 0, "amb": 0, "eligible": 0, "total": 0} for m in MULTIPLIERS}

for sym in SYMBOLS:
    df_can = storage.read_canonical(EXCHANGE, sym, TIMEFRAME)
    for m in MULTIPLIERS:
        gen = TripleBarrierLabelGenerator(horizon_bars=12, volatility_lookback=20, barrier_multiplier=m)
        labeled = gen.generate_labels(df_can, enforce_partition_boundaries=True)
        ts = labeled["open_time_ms"].to_numpy()
        lbl = labeled["label"].to_numpy()
        
        # Filter strictly for Development and Validation (1698796800000 to 1777593599999)
        dev_val_mask = (ts >= DEVELOPMENT_START_MS) & (ts <= VALIDATION_END_MS)
        p_lbl = lbl[dev_val_mask]
        
        tp = int((p_lbl == BarrierOutcome.TP.value).sum())
        sl = int((p_lbl == BarrierOutcome.SL.value).sum())
        exp = int((p_lbl == BarrierOutcome.TIME_EXPIRATION.value).sum())
        amb = int((p_lbl == BarrierOutcome.AMBIGUOUS.value).sum())
        
        dev_val_results[m]["tp"] += tp
        dev_val_results[m]["sl"] += sl
        dev_val_results[m]["exp"] += exp
        dev_val_results[m]["amb"] += amb
        dev_val_results[m]["eligible"] += (tp + sl + exp)
        dev_val_results[m]["total"] += int(dev_val_mask.sum())

print("=== SENSITIVITY STRICTLY ON DEVELOPMENT + VALIDATION (EXCLUDING HOLDOUT) ===")
for m in MULTIPLIERS:
    res = dev_val_results[m]
    el = res["eligible"]
    tot = res["total"]
    tp_pct = res["tp"] / el * 100
    sl_pct = res["sl"] / el * 100
    exp_pct = res["exp"] / el * 100
    amb_pct = res["amb"] / tot * 100
    print(f"Multiplier {m:3.1f}: Total={tot:,} | Eligible={el:,} | TP={tp_pct:.2f}% | SL={sl_pct:.2f}% | Exp={exp_pct:.2f}% | Amb={res['amb']:,} ({amb_pct:.4f}%)")
