# Phase 5.3.1 Pre-Training Integrity Audit

## 1. Overview and Audit Scope

This document details the independent pre-training data integrity audit conducted for Phase 5.3.1 Pilot Baseline Training and Validation. The audit verifies feature schema consistency, timestamp handling, target variable configuration, temporal boundary isolation, and schema hash verification across the pilot instruments `BTCUSDT` and `XMRUSDT`.

All code and data references:
- Feature schema contract: [`src/quantum/ml/contracts.py`](file:///d:/quantum-multi-agent/src/quantum/ml/contracts.py)
- Temporal boundaries: [`src/quantum/features/temporal_split.py`](file:///d:/quantum-multi-agent/src/quantum/features/temporal_split.py)
- Preprocessing engine: [`src/quantum/ml/preprocessor.py`](file:///d:/quantum-multi-agent/src/quantum/ml/preprocessor.py)
- Walk-forward validation: [`src/quantum/ml/validation.py`](file:///d:/quantum-multi-agent/src/quantum/ml/validation.py)
- Verification test suite: [`tests/unit/test_phase5_3_1_pilot.py`](file:///d:/quantum-multi-agent/tests/unit/test_phase5_3_1_pilot.py)

---

## 2. Feature Schema Reconciliation

### 2.1 Schema Comparison: Phase 4 Raw Features vs Phase 5.3 Research Features

During Phase 4, the initial feature pipeline generated 57 columns containing both raw nominal price levels, multi-timeframe moving averages, raw indicators, and timestamps. For Phase 5.3 machine learning, strict stationarity and causality requirements were imposed, producing the 38-column research-ready dataset stored in `data/historical/features_research/`.

| Dataset Tier | Total Columns | Timestamp / Reference Columns | Model Feature Columns (X) | Target Columns |
| :--- | :--- | :--- | :--- | :--- |
| Phase 4 Original Features | 57 | 2 (`open_time_ms`, `close_time_ms`) | 55 | 0 |
| Phase 5.3 Research Features | 38 | 2 (`open_time_ms`, `close_time_ms`) | 36 (Stationary) | 0 (Labels joined separately) |
| Active Model Matrix (X) | 36 | 0 (Excluded) | 36 | 0 |

### 2.2 The 19 Removed Features and Removal Justifications

Exactly 19 columns were pruned from the Phase 4 feature set to eliminate nominal price scale dependency, unit roots, and multicollinearity:

1. `simple_return`: Redundant with log return (`log_return`), which possesses superior additive and statistical stationarity properties.
2. `pct_change`: Collinear with simple return and log return; removed to eliminate numerical redundancy.
3. `hl_range`: Non-stationary nominal price difference (`high - low`); replaced by normalized parkinson volatility and normalized log ranges.
4. `ema_9`: Non-stationary nominal price level; scales with market price and induces non-stationary drift across multi-year cycles.
5. `ema_21`: Non-stationary nominal price level; same justification.
6. `ema_50`: Non-stationary nominal price level; same justification.
7. `ema_100`: Non-stationary nominal price level; same justification.
8. `ema_200`: Non-stationary nominal price level; same justification.
9. `macd_line`: Nominal price difference (`ema_12 - ema_26`); not scale-invariant across regimes where asset price changes by orders of magnitude.
10. `macd_signal`: Exponential moving average of nominal MACD line; non-stationary nominal scale.
11. `macd_hist`: Difference between nominal MACD line and signal line; non-stationary nominal scale.
12. `atr_14`: Average True Range in nominal quote units (USDT); changes by 10x over long horizons, violating scale invariance. Replaced by percentage ATR.
13. `bb_middle_20`: Non-stationary nominal 20-period price moving average.
14. `bb_upper_20`: Non-stationary nominal upper Bollinger band level.
15. `bb_lower_20`: Non-stationary nominal lower Bollinger band level.
16. `vol_sma_20`: Base volume simple moving average; base volumes fluctuate drastically across bull/bear regimes and exchange fee tiers.
17. `quote_vol_sma_20`: Quote turnover moving average; highly non-stationary nominal dollar volume.
18. `donchian_high_20`: Nominal 20-period highest price; non-stationary price level.
19. `donchian_low_20`: Nominal 20-period lowest price; non-stationary price level.

### 2.3 The 36 Retained Stationary Research Features

The 36 features retained in `RESEARCH_STATIONARY_FEATURES` are bounded, scale-invariant, and dimensionless:
- Momentum and Oscillators: `rsi_14`, `stoch_k_14`, `stoch_d_14`, `cci_20`, `willr_14`, `roc_10`.
- Normalized Moving Average Disparities: `price_to_ema_9_ratio`, `price_to_ema_21_ratio`, `price_to_ema_50_ratio`, `price_to_ema_100_ratio`, `price_to_ema_200_ratio`, `ema_9_21_ratio`, `ema_21_50_ratio`, `ema_50_200_ratio`.
- Normalized Volatility and Range Metrics: `bb_pct_b_20`, `bb_bandwidth_20`, `donchian_channel_position_20`, `donchian_channel_width_pct_20`, `atr_pct_14`, `parkinson_volatility_20`, `garman_klass_volatility_20`, `norm_range_mean_10`, `norm_range_std_10`.
- Normalized Volume and Flow Oscillators: `volume_ratio_sma_20`, `quote_volume_ratio_sma_20`, `obv_slope_14`, `cmf_20`, `mfi_14`.
- Log Returns and Lags: `log_return`, `log_return_lag_1`, `log_return_lag_2`, `log_return_lag_3`, `log_return_lag_5`.
- Multi-Timeframe Joined Stationary Signals: `m15_rsi_14`, `m15_log_return`, `h1_rsi_14`.

---

## 3. Timestamp Audit and Exclusion

The timestamps `open_time_ms` and `close_time_ms` exist in the Parquet files strictly for chronological alignment, sample joining, and walk-forward boundary enforcement.

The audit verified in [`src/quantum/ml/contracts.py`](file:///d:/quantum-multi-agent/src/quantum/ml/contracts.py) and [`scripts/run_phase5_3_1_pilot.py`](file:///d:/quantum-multi-agent/scripts/run_phase5_3_1_pilot.py):
1. Features extracted for model input `X` strictly exclude `open_time_ms`, `close_time_ms`, `label`, and `exclusion_reason`.
2. Column dimension of `X` is strictly 36.
3. Unit test `test_02_timestamp_exclusion` in [`tests/unit/test_phase5_3_1_pilot.py`](file:///d:/quantum-multi-agent/tests/unit/test_phase5_3_1_pilot.py) asserts that neither timestamp column is present in `X`.

---

## 4. Target Variable Audit

Labels are produced via the triple-barrier method according to the approved candidate parameters established in Phase 5.2:
- Primary Timeframe: 5m (`Timeframe.M5`)
- Target Horizon: 12 bars (60 minutes maximum holding time)
- Volatility Estimator: 20-period rolling standard deviation of 5m log returns
- Barrier Multiplier: 1.5x rolling volatility
- Target Classes:
  - Take-Profit (`+1` / `TP`): Upper barrier touched first within 12 bars.
  - Stop-Loss (`-1` / `SL`): Lower barrier touched first within 12 bars.
  - Expiration (`0` / `EXP`): Neither barrier touched before 12 bars elapsed (vertical barrier reached).
- Ambiguous Touches: Samples where high and low touched both barriers in the same 5m bar are marked as ambiguous and excluded from model training.

---

## 5. Temporal Boundary and Holdout Protection Audit

The QUANTUM research governance defines four strict temporal partitions:

| Partition | Start (UTC) | End (UTC) | Status in Phase 5.3.1 |
| :--- | :--- | :--- | :--- |
| Development | 2023-11-01 00:00:00 | 2025-10-31 23:59:59.999 | Active Training Window |
| Validation | 2025-11-01 00:00:00 | 2026-04-30 23:59:59.999 | Active Validation Window |
| Validation Observed | 2026-05-01 00:00:00 | 2026-10-31 23:59:59.999 | Frozen - Historical Research Only |
| Prospective Holdout | 2026-11-01 00:00:00 | 2027-04-30 23:59:59.999 | Untouched - Strictly Prohibited |

### 5.1 Holdout Isolation Verification
- Prospective Holdout Access Rejection: `PurgedWalkForwardSplitter` verifies the maximum timestamp in the input DataFrame. Any row with `open_time_ms >= 1793491200000` (2026-11-01 00:00:00 UTC) triggers a fatal `PermissionError`.
- Validation Observed Protection: All training and test fold indices generated by `PurgedWalkForwardSplitter` terminate at or before `2026-04-30 21:55:00 UTC`. Zero observations from Validation Observed (`2026-05-01` onward) were provided to the model training pipeline.

---

## 6. Schema Hash Verification

The canonical research schema hash is computed deterministically as the SHA-256 digest of the sorted 36 stationary column names:

$$\text{hash} = \text{SHA256}(\text{"atr\_pct\_14,bb\_bandwidth\_20,...,willr\_14"})$$

Audit Verification Results:
- Contract Hash: `cc779ea9e3b1862394b7115375c54c4f4cf3d6496bfabf7de457b578762aaf92`
- BTCUSDT Actual Schema Hash: `cc779ea9e3b1862394b7115375c54c4f4cf3d6496bfabf7de457b578762aaf92` (MATCH)
- XMRUSDT Actual Schema Hash: `cc779ea9e3b1862394b7115375c54c4f4cf3d6496bfabf7de457b578762aaf92` (MATCH)

Conclusion: Pre-training data integrity is fully verified across both pilot instruments.
