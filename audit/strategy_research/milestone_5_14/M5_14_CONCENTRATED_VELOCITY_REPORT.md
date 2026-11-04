# M5.14 Concentrated Capital & Velocity Recycling Report

## Scope and controls

- 10-asset primary panel: BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, ADAUSDT, SOLUSDT, AVAXUSDT, LINKUSDT, DOGEUSDT, LTCUSDT (XMRUSDT excluded by its structural-break governance tier).
- Strict sealed boundary: every source row satisfies `open_time_ms < 1793491200000`; no post-boundary data is loaded.
- `44100` extreme-expansion candidates: completed 1h ATR percentile >=80%, volume surge >=2.5x, and a causal 15m confluence score above its prior 20-day 95th percentile.
- 15m and 1h features are shifted one completed bar before 5m execution. Profit recycling closes at +150 bps, or trails by 1.0 ATR_15m after +100 bps; a 4-hour safety exit remains only as a maximum holding guard.
- Every scenario uses `EventDrivenPortfolioLedger`, `IndependentAccountingOracle`, and `ActiveMTMMonitor` with a 0.9950x admission cap and a 1.0000x hard cap.

## Comparative results

| portfolio_mode                           | execution_regime                                         |   mean_net_daily_return_pct |   active_day_return_pct |   capital_utilization_pct |   turnover_per_day_x |   max_drawdown_pct |   oracle_reconciliation_delta_usd |   deflated_sharpe_ratio |
|:-----------------------------------------|:---------------------------------------------------------|----------------------------:|------------------------:|--------------------------:|---------------------:|-------------------:|----------------------------------:|------------------------:|
| Legacy 4-Slot Equal 24.5% Cap            | AsterDEX Maker-Queue (11.0 bps RT)                       |                    8.083927 |                0.800077 |                 37.189565 |             2.149250 |          13.697291 |                          0.000000 |                1.000000 |
| Legacy 4-Slot Equal 24.5% Cap            | Bybit VIP0 Maker-Queue (7.0 bps RT)                      |                   12.692779 |                0.879525 |                 37.187415 |             2.148950 |          13.094480 |                          0.000000 |                1.000000 |
| Legacy 4-Slot Equal 24.5% Cap            | Bybit VIP0 Hybrid Maker-Entry / Taker-Exit (11.0 bps RT) |                    7.765563 |                0.793098 |                 37.186888 |             2.149313 |          13.783596 |                          0.000000 |                1.000000 |
| Legacy 4-Slot Equal 24.5% Cap            | AsterDEX Retail Taker (26.0 bps RT)                      |                    1.438416 |                0.503766 |                 37.195648 |             2.150321 |          15.921570 |                          0.000000 |                1.000000 |
| Mode A Sniper 1-Slot Concentration       | AsterDEX Maker-Queue (11.0 bps RT)                       |                  141.767158 |                1.368529 |                 97.465108 |             4.277816 |          31.037395 |                          0.000000 |                1.000000 |
| Mode A Sniper 1-Slot Concentration       | Bybit VIP0 Maker-Queue (7.0 bps RT)                      |                  347.411373 |                1.531126 |                 97.450800 |             4.276632 |          30.482644 |                          0.000000 |                1.000000 |
| Mode A Sniper 1-Slot Concentration       | Bybit VIP0 Hybrid Maker-Entry / Taker-Exit (11.0 bps RT) |                  132.520152 |                1.356477 |                 97.441389 |             4.277944 |          31.108573 |                          0.000000 |                1.000000 |
| Mode A Sniper 1-Slot Concentration       | AsterDEX Retail Taker (26.0 bps RT)                      |                    4.830300 |                0.763524 |                 97.516596 |             4.281629 |          37.189379 |                          0.000000 |                1.000000 |
| Mode B Dual-Slot High-Beta Concentration | AsterDEX Maker-Queue (11.0 bps RT)                       |                   45.504910 |                1.121504 |                 63.940159 |             3.191476 |          17.884874 |                          0.000000 |                1.000000 |
| Mode B Dual-Slot High-Beta Concentration | Bybit VIP0 Maker-Queue (7.0 bps RT)                      |                   88.699563 |                1.240923 |                 63.934846 |             3.190969 |          16.994745 |                          0.000000 |                1.000000 |
| Mode B Dual-Slot High-Beta Concentration | Bybit VIP0 Hybrid Maker-Entry / Taker-Exit (11.0 bps RT) |                   43.105677 |                1.111953 |                 63.932263 |             3.191565 |          17.996955 |                          0.000000 |                1.000000 |
| Mode B Dual-Slot High-Beta Concentration | AsterDEX Retail Taker (26.0 bps RT)                      |                    3.654080 |                0.676559 |                 63.961814 |             3.193173 |          21.140264 |                          0.000000 |                1.000000 |

## Interpretation

These are historical simulated-execution results, not evidence for deployment. Maker-queue rows retain queue/fill-model uncertainty; fee sensitivity is isolated by holding the sealed signal stream and capital rules constant. Oracle delta is the absolute final-equity difference between the independently maintained accounting paths.

## Invariant verification

- Maximum observed portfolio gross exposure: `0.995038x` (must be <= `1.0000x`).
- Maximum oracle reconciliation delta: `$0.0000000000`.
- All rows are generated from the sealed pre-holdout sample only; this report makes no out-of-sample or live-trading claim.
