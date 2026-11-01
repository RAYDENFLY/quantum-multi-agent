# QUANTUM PHASE 5.3.0 - MODEL INPUT CONTRACT SPECIFICATION

**Author:** Senior Quantitative ML Research Architect & Data Contracts Engineer  
**Date:** 2026-11-01  
**Repository:** https://github.com/RAYDENFLY/quantum-multi-agent  
**Scope:** Pre-Training Input Contracts, Feature Schema, Label Mapping, and Traceability  
**Implementation:** [contracts.py](file:///d:/quantum-multi-agent/src/quantum/ml/contracts.py)  

---

## 1. RESEARCH-READY FEATURE MATRIX SCHEMA

The training and validation pipelines consume the Phase 5.1 stationary research feature matrix stored on disk at `data/historical/features_research`.

### Schema Summary
- **Physical Column Count on Disk:** 38 columns
- **Timestamp Columns:** 2 (`open_time_ms`, `close_time_ms`)
- **Stationary Feature Columns:** 36 columns
- **Warm-Up Trimming:** Initial 200 bars removed per dataset
- **Stationarity & Scale-Invariance Guarantee:** Nominal prices (close, open, high, low, nominal EMAs, nominal Bollinger middle/upper/lower, nominal Donchian channels) are completely excluded.
- **Return Redundancy Policy:** `log_return` is retained; `simple_return` and `pct_change` are excluded to prevent collinearity.

### Exact Feature Column Inventory

| Category | Column Name | Type | Mathematical Formula / Semantic Definition |
|---|---|---|---|
| **Timestamps** | `open_time_ms` | int64 | Candle opening UTC timestamp in milliseconds |
| | `close_time_ms` | int64 | Candle closing UTC timestamp in milliseconds ($t_{\text{open}} + 299,999$) |
| **Returns & Candles** | `log_return` | float64 | $\ln(C_t / C_{t-1})$ |
| | `hl_range_pct` | float64 | $(H_t - L_t) / C_t$ |
| | `body_pct` | float64 | $|C_t - O_t| / (H_t - L_t + \epsilon)$ |
| | `upper_wick_pct` | float64 | $(H_t - \max(O_t, C_t)) / (H_t - L_t + \epsilon)$ |
| | `lower_wick_pct` | float64 | $(\min(O_t, C_t) - L_t) / (H_t - L_t + \epsilon)$ |
| | `clv` | float64 | $((C_t - L_t) - (H_t - C_t)) / (H_t - L_t + \epsilon)$ |
| **Trend Distances** | `price_dist_ema_9` | float64 | $(C_t - \text{EMA}_9) / (\text{EMA}_9 + \epsilon)$ |
| | `price_dist_ema_21` | float64 | $(C_t - \text{EMA}_{21}) / (\text{EMA}_{21} + \epsilon)$ |
| | `price_dist_ema_50` | float64 | $(C_t - \text{EMA}_{50}) / (\text{EMA}_{50} + \epsilon)$ |
| | `price_dist_ema_100` | float64 | $(C_t - \text{EMA}_{100}) / (\text{EMA}_{100} + \epsilon)$ |
| | `price_dist_ema_200` | float64 | $(C_t - \text{EMA}_{200}) / (\text{EMA}_{200} + \epsilon)$ |
| **Trend Slopes** | `ema_9_slope` | float64 | $(\text{EMA}_{9,t} - \text{EMA}_{9,t-1}) / \text{EMA}_{9,t-1}$ |
| | `ema_21_slope` | float64 | $(\text{EMA}_{21,t} - \text{EMA}_{21,t-1}) / \text{EMA}_{21,t-1}$ |
| | `ema_50_slope` | float64 | $(\text{EMA}_{50,t} - \text{EMA}_{50,t-1}) / \text{EMA}_{50,t-1}$ |
| | `ema_100_slope` | float64 | $(\text{EMA}_{100,t} - \text{EMA}_{100,t-1}) / \text{EMA}_{100,t-1}$ |
| | `ema_200_slope` | float64 | $(\text{EMA}_{200,t} - \text{EMA}_{200,t-1}) / \text{EMA}_{200,t-1}$ |
| **Crossovers** | `crossover_9_21` | float64 | $1.0 \text{ if } \text{EMA}_9 > \text{EMA}_{21} \text{ else } 0.0$ |
| | `crossover_21_50` | float64 | $1.0 \text{ if } \text{EMA}_{21} > \text{EMA}_{50} \text{ else } 0.0$ |
| | `crossover_50_200` | float64 | $1.0 \text{ if } \text{EMA}_{50} > \text{EMA}_{200} \text{ else } 0.0$ |
| **Momentum** | `rsi_14` | float64 | Relative Strength Index (14 periods), bounded [0, 100] |
| | `stoch_k` | float64 | Fast Stochastic %K (5 periods), bounded [0, 100] |
| | `stoch_d` | float64 | Stochastic %D (3-period SMA of %K), bounded [0, 100] |
| | `stoch_slow_d` | float64 | Slow Stochastic (3-period SMA of %D), bounded [0, 100] |
| | `roc_10` | float64 | Rate of Change over 10 periods: $(C_t - C_{t-10}) / C_{t-10}$ |
| **Volatility** | `atr_14_pct` | float64 | $\text{ATR}_{14} / (C_t + \epsilon)$ |
| | `rolling_std_returns_20` | float64 | Sample standard deviation ($\text{ddof}=1$) of simple returns over 20 bars |
| | `bb_width_20` | float64 | $(\text{BB}_{\text{upper}} - \text{BB}_{\text{lower}}) / (\text{BB}_{\text{middle}} + \epsilon)$ |
| | `bb_pct_b_20` | float64 | $(C_t - \text{BB}_{\text{lower}}) / (\text{BB}_{\text{upper}} - \text{BB}_{\text{lower}} + \epsilon)$ |
| | `rolling_hl_range_20` | float64 | $(\max_{20}(H) - \min_{20}(L)) / (C_t + \epsilon)$ |
| **Volume** | `rvol_20` | float64 | $V_t / (\text{SMA}_{20}(V) + \epsilon)$ |
| | `vol_change` | float64 | Zero-guarded volume percentage change $(V_t - V_{t-1}) / V_{t-1}$ |
| | `quote_rvol_20` | float64 | $QV_t / (\text{SMA}_{20}(QV) + \epsilon)$ |
| **Structure & Regime** | `donchian_breakout_dist` | float64 | Distance from closest 20-period high/low channel bound |
| | `dist_from_high_20` | float64 | $(C_t - \max_{20}(H)) / (C_t + \epsilon)$ |
| | `dist_from_low_20` | float64 | $(C_t - \min_{20}(L)) / (C_t + \epsilon)$ |
| | `trend_state` | float64 | Categorical regime: $+1.0$ (bull), $-1.0$ (bear), $0.0$ (neutral) |

---

## 2. TARGET LABEL CONTRACT

The prediction target is a discrete 3-class classification problem generated by [labeling.py](file:///d:/quantum-multi-agent/src/quantum/features/labeling.py):

| Target Class | Numerical Value | Semantic Meaning | Horizon / Touch Condition |
|---|---|---|---|
| **TP** | `1` | Take Profit | Upper barrier hit first before lower barrier and before expiration |
| **SL** | `-1` | Stop Loss | Lower barrier hit first before upper barrier and before expiration |
| **TIME_EXPIRATION** | `0` | Time Expiration | Neither barrier touched within the 12-candle horizon (60 minutes) |
| **AMBIGUOUS** | `-2` | Intrabar Double Touch | Both barriers hit within the same 5m bar; **EXCLUDED** from clean training targets |
| **EXCLUDED** | `-999` | Pipeline Exclusion | Warm-up, horizon gap, boundary overflow; **EXCLUDED** from training targets |

### Target Candidate Configuration Hash
- `timeframe`: `5m`
- `horizon_bars`: `12`
- `maximum_holding_minutes`: `60`
- `volatility_lookback`: `20`
- `barrier_multiplier`: `1.5`
- `volatility_type`: `RETURN_VOLATILITY`

---

## 3. DATA INTEGRITY & SAMPLE POLICIES

1. **Zero Missing-Value Tolerance:**
   Every input row must contain exactly 0 NaNs and 0 infinite values. If any NaN or Inf is encountered in the stationary feature columns after the 200-bar warm-up, the dataset loader immediately raises a `ValueError`.
2. **Invalid Sample Exclusion:**
   Samples labeled with `-2` (AMBIGUOUS) or `-999` (EXCLUDED) are filtered out of the supervised training matrix before feeding estimators. They are never coerced into arbitrary classes.
3. **Traceability Guarantee:**
   Each sample $i$ is linked to its provenance via [DatasetSampleTrace](file:///d:/quantum-multi-agent/src/quantum/ml/contracts.py#L42-L55):
   - Exchange: `ASTER`
   - Instrument: (e.g. `BTCUSDT`)
   - Timeframe: `5m`
   - Feature Timestamp: `open_time_ms`
   - Label Timestamp: `open_time_ms`
   - Target Config Hash: SHA-256
   - Dataset Version: `DATASET_V1`
   - Feature Version: `RESEARCH_V1`

---

## 4. EXPERIMENT MANIFEST CONTRACT

Every ML specialist experiment must serialize an immutable JSON manifest defined by [ExperimentManifest](file:///d:/quantum-multi-agent/src/quantum/ml/contracts.py#L58-L86):

```json
{
  "experiment_id": "EXP-BTCUSDT-5M-RF-BASE-001",
  "model_name": "RandomForest",
  "specialist_instrument": "BTCUSDT",
  "exchange": "ASTER",
  "timeframe": "5m",
  "dataset_version": "DATASET_V1",
  "feature_version": "RESEARCH_V1",
  "feature_schema_hash": "63f538...",
  "feature_names": ["log_return", "hl_range_pct", "..."],
  "target_config": {
    "timeframe": "5m",
    "horizon_bars": 12,
    "maximum_holding_minutes": 60,
    "volatility_lookback": 20,
    "barrier_multiplier": 1.5,
    "volatility_type": "RETURN_VOLATILITY"
  },
  "random_seed": 42,
  "instrument_seed": 1003,
  "validation_folds": 5,
  "purge_bars": 12,
  "embargo_bars": 24
}
```

Calling `compute_manifest_hash()` generates a SHA-256 checksum that guarantees experiment immutability and complete auditability.
