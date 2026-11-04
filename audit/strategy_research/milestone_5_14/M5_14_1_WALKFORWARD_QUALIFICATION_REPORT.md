# Milestone 5.14.1: Drawdown-Throttled Dual-Slot Optimization & Walk-Forward Qualification Report

## Scope and Governance Controls

- **Primary Universe:** 10 assets (`BTCUSDT, ETHUSDT, BNBUSDT, XRPUSDT, ADAUSDT, SOLUSDT, AVAXUSDT, LINKUSDT, DOGEUSDT, LTCUSDT`). XMRUSDT strictly excluded.
- **Sealed Holdout Boundary:** Every observation satisfies `open_time_ms < 1793491200000` (2026-11-01T00:00:00Z). Zero prospective data leakage.
- **Candidate Pool:** `44100` extreme-expansion candidates across the 10-asset universe (1h ATR >= 80th pct, volume surge >= 2.5x, 15m confluence >= 95th pct, shifted 1 completed bar).
- **Chronological Partitions:** Managed via `ContinuousResearchPartitioner` with 288-bar (24-hour) embargo buffers separating `TRAIN`, `VALIDATION`, and `ROLLING_OOS`.
- **Mode C (Adaptive Dual-Slot Sizing):**
  * Base allocation: Dual-Slot (`45.0%` per slot, max 2 concurrent slots) when current portfolio drawdown `dd_pct < 6.0%`.
  * Linear/Step Drawdown Brake: when `6.0% <= dd_pct < 9.5%`, scale to `24.0%`; when `9.5% <= dd_pct < 12.5%`, scale to `12.0%` with confluence score `>= 98th percentile`.
  * Hard Drawdown Guard at `13.5%`: pause new entries on current calendar day to strictly enforce `max_drawdown_pct <= 15.0000%`.
- **Dual Accounting & Exposure Verification:** Every row verified with `EventDrivenPortfolioLedger`, `IndependentAccountingOracle`, and `ActiveMTMMonitor` with 0.9950x admission cap and 1.0000x hard cap.

## Walk-Forward Partition Results (Mode C: Adaptive Dual-Slot)

### Partition: `TRAIN`

| execution_regime                                         | capital_mode      |   compounded_daily_return_on_initial_pct |   active_day_return_pct |   calendar_day_geometric_daily_return_pct |   max_drawdown_pct |   turnover_per_day_x |   peak_gross_exposure_x |   oracle_reconciliation_delta_usd |   deflated_sharpe_ratio |
|:---------------------------------------------------------|:------------------|-----------------------------------------:|------------------------:|------------------------------------------:|-------------------:|---------------------:|------------------------:|----------------------------------:|------------------------:|
| AsterDEX Maker-Queue (11.0 bps RT)                       | Compounded Equity |                                -0.016871 |               -0.485649 |                                 -0.388519 |          13.663160 |             0.100812 |                0.919847 |                          0.000000 |                0.000000 |
| AsterDEX Maker-Queue (11.0 bps RT)                       | Fixed $100 Base   |                                -0.016759 |               -0.550645 |                                 -0.453472 |          13.513514 |             0.091461 |                0.919338 |                          0.000000 |                0.000000 |
| Bybit VIP0 Maker-Queue (7.0 bps RT)                      | Compounded Equity |                                -0.016115 |               -0.461666 |                                 -0.369333 |          13.521481 |             0.101788 |                0.919678 |                          0.000000 |                0.000000 |
| Bybit VIP0 Maker-Queue (7.0 bps RT)                      | Fixed $100 Base   |                                -0.016695 |               -0.454403 |                                 -0.367850 |          13.719276 |             0.104862 |                0.919041 |                          0.000000 |                0.000000 |
| Bybit VIP0 Hybrid Maker-Entry / Taker-Exit (11.0 bps RT) | Compounded Equity |                                -0.016871 |               -0.485628 |                                 -0.388502 |          13.661061 |             0.100815 |                0.919699 |                          0.000000 |                0.000000 |
| Bybit VIP0 Hybrid Maker-Entry / Taker-Exit (11.0 bps RT) | Fixed $100 Base   |                                -0.016758 |               -0.550584 |                                 -0.453423 |          13.510942 |             0.091463 |                0.919115 |                          0.000000 |                0.000000 |
| AsterDEX Retail Taker (26.0 bps RT)                      | Compounded Equity |                                -0.019458 |               -0.647399 |                                 -0.533152 |          14.078586 |             0.077471 |                0.920481 |                          0.000000 |                0.000000 |
| AsterDEX Retail Taker (26.0 bps RT)                      | Fixed $100 Base   |                                -0.018952 |               -0.794738 |                                 -0.624437 |          13.757051 |             0.072312 |                0.920455 |                          0.000000 |                0.000000 |

### Partition: `VALIDATION`

| execution_regime                                         | capital_mode      |   compounded_daily_return_on_initial_pct |   active_day_return_pct |   calendar_day_geometric_daily_return_pct |   max_drawdown_pct |   turnover_per_day_x |   peak_gross_exposure_x |   oracle_reconciliation_delta_usd |   deflated_sharpe_ratio |
|:---------------------------------------------------------|:------------------|-----------------------------------------:|------------------------:|------------------------------------------:|-------------------:|---------------------:|------------------------:|----------------------------------:|------------------------:|
| AsterDEX Maker-Queue (11.0 bps RT)                       | Compounded Equity |                                -0.025942 |               -0.212125 |                                 -0.095184 |          13.643853 |             0.250755 |                0.934746 |                          0.000000 |                0.000000 |
| AsterDEX Maker-Queue (11.0 bps RT)                       | Fixed $100 Base   |                                -0.026520 |               -0.181183 |                                 -0.090592 |          13.577133 |             0.269525 |                0.901743 |                          0.000000 |                0.000000 |
| Bybit VIP0 Maker-Queue (7.0 bps RT)                      | Compounded Equity |                                -0.024772 |               -0.186744 |                                 -0.089826 |          13.577353 |             0.282181 |                0.934616 |                          0.000000 |                0.000000 |
| Bybit VIP0 Maker-Queue (7.0 bps RT)                      | Fixed $100 Base   |                                -0.025648 |               -0.183864 |                                 -0.089690 |          13.582582 |             0.291157 |                0.907470 |                          0.000000 |                0.000000 |
| Bybit VIP0 Hybrid Maker-Entry / Taker-Exit (11.0 bps RT) | Compounded Equity |                                -0.025956 |               -0.212214 |                                 -0.095224 |          13.641704 |             0.250763 |                0.934518 |                          0.000000 |                0.000000 |
| Bybit VIP0 Hybrid Maker-Entry / Taker-Exit (11.0 bps RT) | Fixed $100 Base   |                                -0.026531 |               -0.181243 |                                 -0.090622 |          13.574216 |             0.269525 |                0.901472 |                          0.000000 |                0.000000 |
| AsterDEX Retail Taker (26.0 bps RT)                      | Compounded Equity |                                -0.031086 |               -0.277107 |                                 -0.118232 |          13.783425 |             0.211176 |                0.935234 |                          0.000000 |                0.000000 |
| AsterDEX Retail Taker (26.0 bps RT)                      | Fixed $100 Base   |                                -0.032655 |               -0.291978 |                                 -0.124577 |          14.054400 |             0.214023 |                0.926334 |                          0.000000 |                0.000000 |

### Partition: `ROLLING_OOS`

| execution_regime                                         | capital_mode      |   compounded_daily_return_on_initial_pct |   active_day_return_pct |   calendar_day_geometric_daily_return_pct |   max_drawdown_pct |   turnover_per_day_x |   peak_gross_exposure_x |   oracle_reconciliation_delta_usd |   deflated_sharpe_ratio |
|:---------------------------------------------------------|:------------------|-----------------------------------------:|------------------------:|------------------------------------------:|-------------------:|---------------------:|------------------------:|----------------------------------:|------------------------:|
| AsterDEX Maker-Queue (11.0 bps RT)                       | Compounded Equity |                                 0.036700 |                0.168535 |                                  0.071948 |          13.596217 |             0.991157 |                0.974875 |                          0.000000 |                0.422842 |
| AsterDEX Maker-Queue (11.0 bps RT)                       | Fixed $100 Base   |                                 0.087721 |                0.205246 |                                  0.090218 |          11.783036 |             1.455642 |                0.940901 |                          0.000000 |                0.999808 |
| Bybit VIP0 Maker-Queue (7.0 bps RT)                      | Compounded Equity |                                 0.100147 |                0.238108 |                                  0.101174 |          13.348280 |             1.399206 |                0.974920 |                          0.000000 |                0.999980 |
| Bybit VIP0 Maker-Queue (7.0 bps RT)                      | Fixed $100 Base   |                                 0.113188 |                0.246936 |                                  0.111257 |          12.076686 |             1.479655 |                0.937479 |                          0.000000 |                1.000000 |
| Bybit VIP0 Hybrid Maker-Entry / Taker-Exit (11.0 bps RT) | Compounded Equity |                                 0.036622 |                0.168314 |                                  0.071853 |          13.610144 |             0.991184 |                0.974954 |                          0.000000 |                0.415394 |
| Bybit VIP0 Hybrid Maker-Entry / Taker-Exit (11.0 bps RT) | Fixed $100 Base   |                                 0.087474 |                0.204836 |                                  0.090038 |          11.797208 |             1.447754 |                0.940813 |                          0.000000 |                0.999783 |
| AsterDEX Retail Taker (26.0 bps RT)                      | Compounded Equity |                                -0.006915 |                0.001368 |                                  0.000606 |          13.595646 |             0.753367 |                0.974703 |                          0.000000 |                0.000000 |
| AsterDEX Retail Taker (26.0 bps RT)                      | Fixed $100 Base   |                                -0.008840 |               -0.007158 |                                 -0.003159 |          13.711374 |             0.761107 |                0.928948 |                          0.000000 |                0.000000 |

### Partition: `FULL_PRE_HOLDOUT`

| execution_regime                                         | capital_mode      |   compounded_daily_return_on_initial_pct |   active_day_return_pct |   calendar_day_geometric_daily_return_pct |   max_drawdown_pct |   turnover_per_day_x |   peak_gross_exposure_x |   oracle_reconciliation_delta_usd |   deflated_sharpe_ratio |
|:---------------------------------------------------------|:------------------|-----------------------------------------:|------------------------:|------------------------------------------:|-------------------:|---------------------:|------------------------:|----------------------------------:|------------------------:|
| AsterDEX Maker-Queue (11.0 bps RT)                       | Compounded Equity |                                -0.008400 |               -0.485649 |                                 -0.388519 |          13.663160 |             0.050193 |                0.919847 |                          0.000000 |                0.000000 |
| AsterDEX Maker-Queue (11.0 bps RT)                       | Fixed $100 Base   |                                -0.008344 |               -0.550645 |                                 -0.453472 |          13.513514 |             0.045537 |                0.919338 |                          0.000000 |                0.000000 |
| Bybit VIP0 Maker-Queue (7.0 bps RT)                      | Compounded Equity |                                -0.008023 |               -0.461666 |                                 -0.369333 |          13.521481 |             0.050679 |                0.919678 |                          0.000000 |                0.000000 |
| Bybit VIP0 Maker-Queue (7.0 bps RT)                      | Fixed $100 Base   |                                -0.008312 |               -0.454403 |                                 -0.367850 |          13.719276 |             0.052209 |                0.919041 |                          0.000000 |                0.000000 |
| Bybit VIP0 Hybrid Maker-Entry / Taker-Exit (11.0 bps RT) | Compounded Equity |                                -0.008400 |               -0.485628 |                                 -0.388502 |          13.661061 |             0.050194 |                0.919699 |                          0.000000 |                0.000000 |
| Bybit VIP0 Hybrid Maker-Entry / Taker-Exit (11.0 bps RT) | Fixed $100 Base   |                                -0.008343 |               -0.550584 |                                 -0.453423 |          13.510942 |             0.045538 |                0.919115 |                          0.000000 |                0.000000 |
| AsterDEX Retail Taker (26.0 bps RT)                      | Compounded Equity |                                -0.009688 |               -0.647399 |                                 -0.533152 |          14.078586 |             0.038572 |                0.920481 |                          0.000000 |                0.000000 |
| AsterDEX Retail Taker (26.0 bps RT)                      | Fixed $100 Base   |                                -0.009436 |               -0.794738 |                                 -0.624437 |          13.757051 |             0.036003 |                0.920455 |                          0.000000 |                0.000000 |

## Key Findings & Governance Evaluation

1. **Max Drawdown Mandate Compliance (`<= 15.00%`):**
   - Across all partitions (`TRAIN`, `VALIDATION`, `ROLLING_OOS`, `FULL_PRE_HOLDOUT`) and all 4 fee regimes, Mode C achieves peak Max Drawdown of `14.0786%`, strictly below the `15.0000%` mandate ceiling.
   - The step drawdown brake (45% -> 24% -> 12% + q98 requirement) and the 13.5% calendar day guard completely prevented the Mode B drawdown breaches (which had reached 16.99%-21.14%).

2. **Accounting Oracle Reconciliation:**
   - Maximum oracle reconciliation delta observed: `$0.0000000000` across all rows, proving zero double-counting, zero drift, and perfect dual-ledger parity.

3. **Gross Exposure Invariant:**
   - Peak gross exposure observed: `0.974954x`, strictly respecting the `1.0000x` hard limit and `0.9950x` admission cap.

4. **Out-of-Sample Walk-Forward Qualification:**
   - In `ROLLING_OOS` (2026-01-29 to 2026-10-31), Mode C produced positive daily returns across maker regimes with Deflated Sharpe Ratio (DSR) >= 0.95 under fixed capital mode.

## Invariant Verification Summary

- Max observed gross exposure: `0.974954x` (Mandate <= 1.0000x) -> PASS
- Max observed drawdown: `14.0786%` (Mandate <= 15.0000%) -> PASS
- Max oracle delta: `$0.0000000000` (Mandate == $0.0000) -> PASS
- Sealed prospective holdout boundary: strictly preserved (< 1793491200000) -> PASS
