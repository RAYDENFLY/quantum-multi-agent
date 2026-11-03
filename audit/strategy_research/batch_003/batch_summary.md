# Strategy Research Report — `BATCH_003` Summary

**Batch ID:** `batch_003`  
**Git Commit:** `dcc8ceb54d80b1b9685d92236f48b0994610522a`  
**Evaluation Period:** Confirmatory Folds 1–4 (`2025-01-29` to `2026-01-29`, `365.14 days`)  
**Initial Capital:** `$100.00 USD` (`min_notional = $5.00 USDT`)  
**Total Strategies Evaluated:** `100`  
**Positive Net Return Strategies:** `100`  
**Qualified Strategies (MDD <= 30%, AvgDD < 10%, PF >= 1.05, >= 3/4 Folds Positive):** `20`

---

## 1. Batch Champion Summary

- **Batch Best Strategy ID:** `STRAT_242` (`config_hash = b02f17c3e006c2c9`, `experiment_id = EXP_B003_STRAT_242_b02f17c3`)
- **Strategy Family:** `LIQUIDITY_MICROSTRUCTURE`
- **Hypothesis:** Batch 3 Local Surface Refinement of STRAT_134: margin=0.22, htf_max=-93.0 bps, TP=3.0s, SL=1.15s, H=20b, risk=2.40%.
- **Mean Net Daily Portfolio Return:** **`+0.1092% / day`** (95% Bootstrap CI: `[-0.0073%, +0.2524%]`)
- **Net Cumulative Return (`$100 USD` Initial Equity):** **`+44.40%`** (Ending Equity: **`$144.40 USD`**)
- **Profit Factor:** **`1.108`** | **Sharpe:** **`1.577`** | **Sortino:** **`1.409`**
- **Maximum Drawdown (MDD):** **`16.35%`** | **Mean Underwater Drawdown:** **`4.40%`**
- **Executed Trades:** `1580` (Candidate Signals: `1760`, Fill Rate: `89.8%`)
- **Walk-Forward Fold Returns:** Fold 1: `+5.11%`, Fold 2: `+7.98%`, Fold 3: `+33.79%`, Fold 4: `-4.55%` (`3/4` folds positive)

---

## 2. Breakdown by Strategy Family

| Strategy Family | Candidates Tested | Positive Net Return Count | Positive Rate (%) |
| :--- | :---: | :---: | :---: |
| `LIQUIDITY_MICROSTRUCTURE` | 100 | 100 | 100.0% |
