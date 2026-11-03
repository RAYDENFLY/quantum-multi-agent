# Strategy Research Report — `BATCH_001` Summary

**Batch ID:** `batch_001`  
**Git Commit:** `dcc8ceb54d80b1b9685d92236f48b0994610522a`  
**Evaluation Period:** Confirmatory Folds 1–4 (`2025-01-29` to `2026-01-29`, `365.14 days`)  
**Initial Capital:** `$100.00 USD` (`min_notional = $5.00 USDT`)  
**Total Strategies Evaluated:** `100`  
**Positive Net Return Strategies:** `12`  
**Qualified Strategies (MDD <= 30%, AvgDD < 10%, PF >= 1.05, >= 3/4 Folds Positive):** `3`

---

## 1. Batch Champion Summary

- **Batch Best Strategy ID:** `STRAT_061` (`config_hash = 63e038a425dfbd55`, `experiment_id = EXP_B001_STRAT_061_63e038a4`)
- **Strategy Family:** `VOLATILITY_DYNAMICS`
- **Hypothesis:** 93rd-percentile volatility flush climax reclaim.
- **Mean Net Daily Portfolio Return:** **`+0.0381% / day`** (95% Bootstrap CI: `[-0.0273%, +0.1176%]`)
- **Net Cumulative Return (`$100 USD` Initial Equity):** **`+13.88%`** (Ending Equity: **`$113.88 USD`**)
- **Profit Factor:** **`1.077`** | **Sharpe:** **`1.009`** | **Sortino:** **`1.021`**
- **Maximum Drawdown (MDD):** **`9.47%`** | **Mean Underwater Drawdown:** **`3.31%`**
- **Executed Trades:** `915` (Candidate Signals: `1035`, Fill Rate: `88.4%`)
- **Walk-Forward Fold Returns:** Fold 1: `-1.52%`, Fold 2: `+2.10%`, Fold 3: `+10.37%`, Fold 4: `+2.81%` (`3/4` folds positive)

---

## 2. Breakdown by Strategy Family

| Strategy Family | Candidates Tested | Positive Net Return Count | Positive Rate (%) |
| :--- | :---: | :---: | :---: |
| `LIQUIDITY_MICROSTRUCTURE` | 20 | 5 | 25.0% |
| `MARKET_REGIME_TRANSITIONS` | 15 | 0 | 0.0% |
| `DIRECTIONAL_PREDICTION` | 15 | 0 | 0.0% |
| `VOLATILITY_DYNAMICS` | 15 | 2 | 13.3% |
| `CROSS_ASSET_RELATIONSHIPS` | 15 | 4 | 26.7% |
| `MEAN_REVERSION_BREAKOUT` | 10 | 1 | 10.0% |
| `ADAPTIVE_ENTRY_EXECUTION` | 10 | 0 | 0.0% |
