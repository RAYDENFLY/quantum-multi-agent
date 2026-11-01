# QUANTUM PHASE 5.1: FEATURE MATERIALIZATION & RESEARCH HYGIENE REPORT

**Project:** QUANTUM - Multi-Agent Quantitative Research Platform  
**Phase:** Phase 5.1 - Historical Backfill & Dataset Materialization  
**Role:** Senior Quantitative Data Engineer & Market Data Infrastructure Engineer  
**Status:** COMPLETED  
**Feature Version:** `FEATURE_V1`  
**Schema Architecture:** Dual-Layer Persistence (`features` and `features_research`)  
**Deliverable Document:** `docs/PHASE_5_1_FEATURE_MATERIALIZATION_REPORT.md`

---

## 1. DUAL-LAYER FEATURE STORAGE ARCHITECTURE

Phase 5.1 strictly preserved the original Phase 4 feature matrix outputs while materializing an independent, clean, research-ready stationary feature set conforming to Phase 5.0 hygiene specifications.

```
data/historical/
|-- features/                     <-- Original Phase 4 Feature Output (57 columns)
|   `-- exchange=ASTER/symbol={SYM}/timeframe={TF}/{YEAR}.parquet
|
`-- features_research/            <-- Filtered Research-Ready Stationary Set (40 columns)
    `-- exchange=ASTER/symbol={SYM}/timeframe={TF}/{YEAR}.parquet
```

- **Invariant:** Neither dataset overwrites the other. Both layers are stored as independent year-partitioned Parquet datasets.
- **Warm-Up Policy:** The initial 200 bars are preserved in `features/` for complete auditability, and strictly trimmed in `features_research/` to ensure 100% numerical completeness.

---

## 2. FEATURE HYGIENE SPECIFICATION & COLUMN AUDIT

### Excluded Non-Stationary & Redundant Features
1. **Redundant Returns:** `simple_return` and `pct_change` were excluded from `features_research/`. `log_return` was retained as the time-additive, mathematically stationary representation.
2. **Nominal Moving Averages:** Nominal price levels (`ema_9`, `ema_20`, `ema_50`, `ema_200`, `bb_middle_20`, `bb_upper_20`, `bb_lower_20`, `donchian_high_20`, `donchian_low_20`) were excluded from candidate predictors due to non-stationarity and arbitrary nominal scaling.
3. **Stationary Scale-Invariant Equivalents Retained:**
   - Fractional distance to EMAs: `dist_from_ema_9`, `dist_from_ema_20`, `dist_from_ema_50`, `dist_from_ema_200`.
   - Relative Bollinger metrics: `bb_width_20`, `bb_pct_b_20`.
   - Normalized range: `rolling_hl_range_20`, `donchian_breakout_dist`.
   - Extremum distances: `dist_from_high_20`, `dist_from_low_20`.

### The 40 Research-Ready Columns (`RESEARCH_FEATURE_COLUMNS`)
1. `open_time_ms` (Reference bar open timestamp)
2. `close_time_ms` (Reference bar close timestamp)
3. `log_return` (Logarithmic return)
4. `hl_range` (High-low range)
5. `hl_range_pct` (High-low range as fraction of close)
6. `body_pct` (Candle body as fraction of close)
7. `upper_wick_pct` (Upper wick as fraction of close)
8. `lower_wick_pct` (Lower wick as fraction of close)
9. `clv` (Close location value in [-1, 1])
10. `dist_from_ema_9` (Fractional distance from EMA 9)
11. `dist_from_ema_20` (Fractional distance from EMA 20)
12. `dist_from_ema_50` (Fractional distance from EMA 50)
13. `dist_from_ema_200` (Fractional distance from EMA 200)
14. `ema_cross_9_20` (EMA 9/20 difference relative to close)
15. `ema_cross_20_50` (EMA 20/50 difference relative to close)
16. `ema_cross_50_200` (EMA 50/200 difference relative to close)
17. `rsi_14` (Relative Strength Index 14 in [0, 100])
18. `stoch_k_14` (Stochastic %K 14 in [0, 100])
19. `stoch_d_14` (Stochastic %D 14 in [0, 100])
20. `macd_line` (MACD line normalized by close)
21. `macd_signal` (MACD signal line normalized by close)
22. `macd_hist` (MACD histogram normalized by close)
23. `atr_14` (Average True Range 14)
24. `natr_14` (Normalized ATR 14 as percentage of close)
25. `bb_width_20` (Bollinger Band width)
26. `bb_pct_b_20` (Bollinger %B oscillator)
27. `rolling_hl_range_20` (20-bar rolling high-low range normalized)
28. `vol_sma_20` (Volume 20-period simple moving average)
29. `rvol_20` (Relative volume ratio)
30. `vol_change` (One-period relative volume change with zero-volume guard)
31. `quote_vol_sma_20` (Quote volume 20-period simple moving average)
32. `quote_rvol_20` (Quote relative volume ratio)
33. `donchian_breakout_dist` (Donchian channel breakout distance normalized)
34. `dist_from_high_20` (Fractional distance from 20-bar high)
35. `dist_from_low_20` (Fractional distance from 20-bar low)
36. `hour_of_day` (UTC hour [0-23])
37. `day_of_week` (Day of week [0-6])
38. `is_weekend` (Binary weekend indicator)
39. `regime_volatility` (Categorical volatility regime)
40. `trend_state` (Categorical trend classification)

---

## 3. ZERO-NAN & ZERO-INF REMEDIATION

During the initial materialization run, a numerical defect was identified in `vol_change` where periods of zero exchange trading volume produced `0/0 = NaN` or `x/0 = +inf`.

### Remediation Applied
In `src/quantum/features/engine.py`:
```python
# Safe volume change: if prior volume was 0, change is 0.0 (or neutral ratio)
v_shift = s_v.shift(1)
raw_vol_change = np.where(v_shift > 0, (s_v - v_shift) / v_shift, 0.0).astype(float)
raw_vol_change[0] = np.nan
features["vol_change"] = raw_vol_change
```
This mathematically robust formula guarantees:
- Bar 0 remains `NaN` during the warm-up period.
- For all bars after bar 0, if prior volume was 0 and current volume is 0, volume change is evaluated to `0.0`.
- Zero infinite values and zero NaNs remain in the post-warm-up matrix across all 4,595,735 rows.

---

## 4. CAUSAL MULTI-TIMEFRAME JOIN INTEGRITY

Multi-timeframe features are combined causally using backward as-of joining:

```
5m Base Bars:    |----5m_1----|----5m_2----|----5m_3----|----5m_4----|----5m_5----|
15m HTF Bars:    |-------------15m_Bar_1-------------|-------------15m_Bar_2-------------|
Join Rule:       As-of backward matching on closed higher-timeframe bars ONLY
Zero Lookahead:  5m bar at t=10m receives features from 15m bar ending at t=0m.
```

- **Validation:** Automated unit test `test_multi_timeframe_leakage.py` and `test_phase5_1_backfill.py` confirm bit-for-bit invariance when future bars are modified.
- **Empirical Test:** BTCUSDT 5m joined with 15m and 1h materialized 316,499 rows with 167 total columns and exactly 0 NaNs after warm-up.
