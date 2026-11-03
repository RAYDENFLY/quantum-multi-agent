# QUANTUM — Timeframe, Lookback & Timestamp Alignment Forensic Audit

**Document Identifier:** `audit/strategy_research/post_300_review/TIMEFRAME_AND_TIMESTAMP_AUDIT.md`  
**Evaluation Date:** `2026-11-03T02:46:30Z`  
**Git Commit:** `dcc8ceb54d80b1b9685d92236f48b0994610522a`  
**Verification Target:** Timeframe mapping, lookahead bias checks, bar alignment, and prospective holdout isolation.

---

## 1. Timeframe Architecture & Mathematical Mapping

The QUANTUM backtesting and feature engineering engine operates on discrete multi-timeframe arrays. The exact definitions and mathematical equivalents are:

| Component | Declarative Parameter | Code Implementation | Exact Mathematical Duration | Human Description |
| :--- | :--- | :--- | :--- | :--- |
| **Base Candle Bar** | `timeframe: "5m"` | `timeframe=5m/*.parquet` | $300\text{ seconds} = 5\text{ minutes}$ | 5-Minute Base Microstructure Candle |
| **Higher-Timeframe Lookback** | `htf_lookback_bars = 12` | `pct_change(12).shift(1)` | $12 \times 5\text{m} = 60\text{ minutes} = 1.0\text{ hour}$ | 1-Hour Rolling Cumulative Return Filter |
| **Trade Holding Horizon** | `horizon_bars = 20` | `min(entry_bar + 20, n_bars - 1)` | $20 \times 5\text{m} = 100\text{ minutes} = 1\text{h } 40\text{m}$ | 100-Minute Maximum Trade Life (Vertical Barrier) |
| **Volatility Lookback** | `sigma_20` | `pct_change().rolling(20).std()` | $20 \times 5\text{m} = 100\text{ minutes}$ | Short-term 5m Volatility Basis ($\sigma_t$) |
| **Macro Volatility Lookback**| `sigma_96` | `pct_change().rolling(96).std()` | $96 \times 5\text{m} = 480\text{ minutes} = 8.0\text{ hours}$ | Medium-term Volatility Anchor for Vol-Expansion Ratio |
| **BTC Lead Lookback** | `btc_lead_lookback_bars = 6` | `pct_change(6).shift(1)` | $6 \times 5\text{m} = 30\text{ minutes}$ | 30-Minute Bitcoin Impulse Shock Filter |

---

## 2. Bar Alignment & Causal Shift Verification

### 2.1 Causal Shift in Higher-Timeframe Calculation
In `src/quantum/strategies/evaluator.py` lines 127–132:
```python
htf_rets_bps: Dict[int, np.ndarray] = {}
for lb in (6, 12, 24, 48):
    r_lb = df_c["close"].pct_change(lb).fillna(0.0).to_numpy(dtype=np.float64) * 10_000.0
    r_lb_prev = np.roll(r_lb, 1); r_lb_prev[0] = 0.0
    htf_rets_bps[lb] = r_lb_prev
```
- For bar $i$, the un-shifted `r_lb[i]` would represent $\frac{C_i - C_{i-12}}{C_{i-12}}$. If accessed at bar $i$ open, this would contain $C_i$ (future price at the end of bar $i$).
- However, the code explicitly performs `r_lb_prev = np.roll(r_lb, 1)`.
- Therefore, at index $i$, the feature accessed is:
  $$\text{htf\_rets\_bps}[12][i] = \frac{C_{i-1} - C_{i-13}}{C_{i-13}} \times 10,000\text{ bps}$$
- Because $C_{i-1}$ is the closing price of candle $i-1$, which occurred at or before the opening price $O_i$ of candle $i$, **there is ZERO lookahead bias in the higher-timeframe return calculation**.

### 2.2 Causal Shift in OOF Model Predictions
In `src/quantum/strategies/evaluator.py` lines 133–153:
```python
prev_ts = np.roll(ts, 1); prev_ts[0] = -1
oof_indexed = oof_f14.set_index("open_time_ms")
reindexed = oof_indexed.reindex(prev_ts)
```
- The LightGBM specialist model generates out-of-fold (OOF) probabilities for bar $i-1$ at timestamp `open_time_ms[i-1]`.
- The engine indexes the OOF table using `prev_ts = np.roll(ts, 1)`.
- Thus, the model probabilities evaluated at bar $i$ (`prob_p1_prev`, `prob_0_prev`, `prob_m1_prev`) were computed strictly from information available up to bar $i-1$.
- **Causal integrity is verified:** The agent observes the prediction at the close of candle $i-1$ and enters the trade at the open of candle $i$.

---

## 3. Trade Horizon & Bar Holding Duration

In `STRAT_242`, `exit.horizon_bars = 20`:
- **Execution Bar:** Entry occurs at index $i$ open (`entry_time_ms = ts[i]`).
- **Maximum Barrier:** The trade is monitored across bars $b \in [i+1, i+20]$.
- **Exit Logic:**
  - If Stop Loss ($1.15 \times \sigma_t$) is touched intrabar, exit occurs immediately at the stop price.
  - If Take Profit ($3.00 \times \sigma_t$) is touched intrabar, exit occurs immediately at the TP price.
  - If neither barrier is triggered after 20 bars (100 minutes), the position is liquidated at $C_{i+20}$ (`TIME_EXPIRATION`).
- **Holding Time Distribution in STRAT_242 (1,580 trades):**
  - Mean holding duration: `8.4 bars` (`42.0 minutes`).
  - Median holding duration: `5.0 bars` (`25.0 minutes`).
  - Max holding duration: `20.0 bars` (`100.0 minutes`, 312 trades closed at expiration).
  - Quick TP hits ($\le 3\text{ bars}$ / $15\text{ min}$): 428 trades (`27.1%`).

---

## 4. Prospective Holdout Seal Forensic Check

The QUANTUM project governance establishes a strict holdout boundary:
$$\text{PROSPECTIVE\_HOLDOUT\_START\_MS} = 1793491200000\text{ ms} \quad (\text{2026-11-01 00:00:00 UTC})$$

The raw canonical parquet datasets, materialized OOF parquets, and trade logs were forensically inspected for timestamp boundaries:

| Dataset / File | Minimum Timestamp (UTC) | Maximum Timestamp (UTC) | Holdout Start (UTC) | Breach Status |
| :--- | :---: | :---: | :---: | :---: |
| **`data/historical/canonical/exchange=ASTER/symbol=*/timeframe=5m/`** | `2025-01-29 11:20:00` | `2026-01-29 14:35:00` | `2026-11-01 00:00:00` | **`SEALED (9 months prior)`** |
| **`artifacts/phase_5_4/materialized_oof/*_oof.parquet`** (Folds 1–4) | `2025-01-29 11:20:00` | `2026-01-29 14:35:00` | `2026-11-01 00:00:00` | **`SEALED`** |
| **`STRAT_242_trades_full.json`** (First Trade) | `2025-01-29 19:30:00` | — | `2026-11-01 00:00:00` | **`SEALED`** |
| **`STRAT_242_trades_full.json`** (Last Trade) | — | `2026-01-29 13:30:00` | `2026-11-01 00:00:00` | **`SEALED (275 days prior)`** |

### Holdout Seal Verification Finding
**Zero access, leakage, or snooping of the prospective holdout occurred.**  
All 300 strategy evaluations were conducted strictly within the authorized confirmatory walk-forward Folds 1–4 window ($365.14\text{ calendar days}$).
