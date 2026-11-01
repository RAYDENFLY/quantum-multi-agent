import json
import pandas as pd

with open('data/historical/phase5_1_backfill_summary.json') as f:
    summary = json.load(f)

df_csv = pd.read_csv('data/historical/reconciliation_audit_summary.csv')

print(f"Summary reported total canonical: {summary['total_canonical_candles']}")
print(f"Actual disk total canonical: {df_csv['canonical_rows'].sum()}")
diff_total = df_csv['canonical_rows'].sum() - summary['total_canonical_candles']
print(f"Discrepancy: {diff_total}")

print("\nDifferences per workload:")
for w in summary['workloads']:
    sym = w['symbol']
    tf = w['timeframe']
    rep_can = w['actual_candle_count']
    rep_res = w['feature_research_rows']
    actual_row = df_csv[(df_csv['symbol'] == sym) & (df_csv['timeframe'] == tf)].iloc[0]
    act_can = int(actual_row['canonical_rows'])
    act_res = int(actual_row['research_rows'])
    if rep_can != act_can or rep_res != act_res:
        print(f"  {sym} {tf}: reported_can={rep_can}, actual_can={act_can} (diff={act_can-rep_can}) | reported_res={rep_res}, actual_res={act_res}")
