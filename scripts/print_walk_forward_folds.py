import pandas as pd
from datetime import datetime, timezone
from quantum.historical.storage import ParquetStorageManager
from quantum.features.temporal_split import TemporalPartitionManager
from quantum.ml.validation import PurgedWalkForwardSplitter

storage = ParquetStorageManager('data/historical')
df = storage.read_canonical('ASTER', 'BTCUSDT', '5m')
df_dev_val = TemporalPartitionManager.filter_development_and_validation(df)

splitter = PurgedWalkForwardSplitter(n_splits=5, horizon_bars=12, embargo_bars=24, min_train_ratio=0.5)
meta = splitter.get_fold_metadata(df_dev_val)

print('Total Dev+Val samples:', len(df_dev_val))
for m in meta:
    t_start = datetime.fromtimestamp(m['train_start_ms']/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M')
    t_end = datetime.fromtimestamp(m['train_end_ms']/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M')
    test_start = datetime.fromtimestamp(m['test_start_ms']/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M')
    test_end = datetime.fromtimestamp(m['test_end_ms']/1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M')
    f_num = m['fold']
    tr_s = m['train_samples']
    te_s = m['test_samples']
    p_s = m['purged_samples']
    e_s = m['embargo_samples']
    print(f"Fold {f_num}: Train={tr_s:7,d} ({t_start} to {t_end}) | Test={te_s:6,d} ({test_start} to {test_end}) | Purged={p_s} | Embargo={e_s}")
