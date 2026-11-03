# Strategy Research Report — `BATCH_002` Summary

**Batch ID:** `batch_002`  
**Git Commit:** `dcc8ceb54d80b1b9685d92236f48b0994610522a`  
**Evaluation Period:** Confirmatory Folds 1–4 (`2025-01-29` to `2026-01-29`, `365.14 days`)  
**Initial Capital:** `$100.00 USD` (`min_notional = $5.00 USDT`)  
**Total Strategies Evaluated:** `100`  
**Positive Net Return Strategies:** `30`  
**Qualified Strategies (MDD <= 30%, AvgDD < 10%, PF >= 1.05, >= 3/4 Folds Positive):** `5`

---

## 1. Batch Champion Summary

- **Batch Best Strategy ID:** `STRAT_134` (`config_hash = 858816599bacc574`, `experiment_id = EXP_B002_STRAT_134_85881659`)
- **Strategy Family:** `LIQUIDITY_MICROSTRUCTURE`
- **Hypothesis:** Batch 2 Exploitation (STRAT_061 refinement): 5-asset pool, 1h flush <= -85.0 bps, margin >= 0.22, p0 <= 0.27, TP=3.0s, SL=1.15s.
- **Mean Net Daily Portfolio Return:** **`+0.0920% / day`** (95% Bootstrap CI: `[-0.0151%, +0.2191%]`)
- **Net Cumulative Return (`$100 USD` Initial Equity):** **`+36.16%`** (Ending Equity: **`$136.16 USD`**)
- **Profit Factor:** **`1.092`** | **Sharpe:** **`1.424`** | **Sortino:** **`1.267`**
- **Maximum Drawdown (MDD):** **`15.30%`** | **Mean Underwater Drawdown:** **`4.59%`**
- **Executed Trades:** `1626` (Candidate Signals: `1805`, Fill Rate: `90.1%`)
- **Walk-Forward Fold Returns:** Fold 1: `+2.83%`, Fold 2: `+8.21%`, Fold 3: `+30.39%`, Fold 4: `-5.86%` (`3/4` folds positive)

---

## 2. Breakdown by Strategy Family

| Strategy Family | Candidates Tested | Positive Net Return Count | Positive Rate (%) |
| :--- | :---: | :---: | :---: |
| `LIQUIDITY_MICROSTRUCTURE` | 60 | 26 | 43.3% |
| `ADAPTIVE_ENTRY_EXECUTION` | 15 | 0 | 0.0% |
| `CROSS_ASSET_RELATIONSHIPS` | 15 | 4 | 26.7% |
| `MEAN_REVERSION_BREAKOUT` | 10 | 0 | 0.0% |
