# AGENT_SPECIFICATION.md: Five-Agent Local Quantitative & ML Architecture

## 1. Multi-Agent Design: Ranking, Conditioning & Separation of Powers

**QUANTUM** implements five specialized agents operating as local quantitative and CPU machine learning modules. There are **zero cloud AI calls**.

### 1.1 Architectural Philosophy: Ranking & Conditioning vs. Restrictive Filtering
A common pathology in multi-agent trading systems is "funnel collapse": making each agent an independent, highly restrictive binary filter, resulting in zero trade frequency. QUANTUM explicitly prevents this by assigning complementary roles across agents:
* **`SCOUT` (Ranking & Opportunity Triage)**: Ranks Stage D candidates using calibrated probability of positive price excursion. Its threshold is an adjustable minimum quality floor tuned on validation data to maintain healthy trade volume (target: 10-30 qualified setups per day across the 850-contract universe).
* **`ANALYST` (Contextual Conditioning & Meta-Labeling)**: Rather than acting as a simple veto, `ANALYST` conditions the thesis by classifying the macro regime (`TREND_IMPULSE`, `MEAN_REVERT_RANGE`, `HIGH_VOL_EXHAUSTION`) and scaling directional probability. It rejects setups only in un-tradeable dead markets (`LOW_LIQ_CHOP`) or outright directional conflicts.
* **`SNIPER` (Barrier Geometry & Expected Value Optimizer)**: Rather than rejecting trades arbitrarily, `SNIPER` optimizes entry type and evaluates multiple candidate TP/SL barrier ratios to find the profile that maximizes expected net return $\mathbb{E}[R_{\text{net}}]$. It skips only if all evaluated barrier profiles fail to yield positive net EV after realistic fees and slippage.
* **`RISK` (Hard Capital Protection Gate)**: 100% deterministic Python. Absolute veto power based strictly on portfolio safety limits (drawdown, exposure, leverage, liquidity).
* **`BANKER` (Trade Lifecycle & Post-Trade Analytics)**: Deterministic state machine handling stops, partial exits, trailing ratchets, and attribution.

### 1.2 Validation-Only Threshold Selection Protocol
All probability and expected value thresholds mentioned in this document (e.g., initial defaults `scout_min_prob = 0.56`, `analyst_min_prob = 0.58`, `sniper_min_expected_r = +0.25R`) are **configurable hyperparameters**, NOT dogmatic hardcoded constants. They must follow this strict selection protocol:
1. **Fit & Calibrate**: Models and isotonic calibrators are trained exclusively on the Training fold.
2. **Optimize on Validation Fold**: Thresholds are selected on the purged Validation fold by sweeping candidate cutoffs over the Precision-Recall curve to maximize total expected net return $\sum \mathbb{E}[R_{\text{net}}]$ subject to a **Minimum Trade Coverage Constraint** (e.g., $\ge 3$ to $8$ trades per active symbol per week).
3. **Freeze Before Test**: Once chosen, all thresholds are frozen in `manifest.json`.
4. **Out-of-Sample Verification**: The frozen thresholds are evaluated on the strictly unseen Out-of-Sample (OOS) Test fold. Optimization on OOS data is strictly forbidden.

### 1.3 Algorithm Selection Matrix (Evaluated Against Hardware & Quantitative Constraints)

| Candidate Algorithm | CPU Inference Latency (1 Row) | Model RAM Footprint | Sample Efficiency on Financial Tabular Data | Overfitting Risk | Architectural Selection Verdict |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`LightGBM` (`LGBMClassifier` / `LGBMRegressor`)** | **`0.2 - 0.8 ms`** (`num_threads=1`) | **`1.5 - 3.0 MB`** | **High** (handles non-linear feature interactions & monotonic constraints) | Controlled via `max_depth <= 5`, `num_leaves <= 24`, `min_child_samples >= 100` | **PRIMARY SELECTED ENGINE** for `SCOUT`, `ANALYST`, and `SNIPER`. |
| **`XGBoost`** | `0.4 - 1.2 ms` | `2.5 - 5.0 MB` | High | Controlled via `max_depth`, `subsample`, `colsample_bytree` | **Optional Secondary Benchmark** in offline `train_worker.py` (only `LightGBM` required in default runtime to save ~25 MB import RAM). |
| **Isotonic / Platt Calibration (`scikit-learn`)** | `< 0.1 ms` | `< 0.2 MB` | High | Low (monotonic 1D mapping) | **MANDATORY WRAPPER** on all classification outputs so predicted probabilities reflect empirical win rates. |
| **Gaussian Hidden Markov Model / Volatility Quantile Clustering** | `< 0.3 ms` | `< 0.5 MB` | High on low-dimensional return/volatility vectors (3-4 features) | Low when restricted to 3-4 states | **SELECTED** for `ANALYST` Macro Volatility & Trend Regime sub-classifier (3-state Gaussian Mixture / Markov transition filter). |
| **Ridge / Huber Linear Regression (`scikit-learn`)** | `< 0.05 ms` | `< 0.1 MB` | Very High on small samples | Very Low ($L_2$ regularized) | **SELECTED** as cold-start linear baseline and ensemble anchor for `SNIPER` expected excursion estimation. |
| **Deep Neural Networks (LSTM / Transformer)** | `15 - 80 ms` | `150 - 600 MB` | Poor on noisy OHLCV | Very High | **REJECTED** (violates RAM target and interpretability). |

---

## 2. Detailed Specification of the Five Agents

### 2.1 AGENT 1: SCOUT (Opportunity Discovery & Anomaly Triage)
* **Purpose**: Filter Stage D scanner candidates by predicting the calibrated probability that a detected momentum, volume, volatility, or reversal anomaly will follow through by at least $+1.0 \times \text{ATR}_{15m}$ in the candidate's directional bias before hitting $-1.0 \times \text{ATR}_{15m}$ within the next 8 bars (`2 hours` on `15m`).
* **Local Quantitative & ML Methods**:
  1. **Multivariate Anomaly Z-Score**: Computes Mahalanobis / composite Z-score across `RVOL_15m`, `NATR_expansion`, `book_imbalance_top10`, and `funding_rate_zscore`.
  2. **Calibrated `LightGBM` Binary Classifier (`scout_lgbm_v{N}`)**: Trained on 24 micro-structure and single-timeframe (`5m` + `15m`) features with `IsotonicRegression` probability calibration.
  3. **Rule Baseline (`FALLBACK_RULE_ONLY`)**: Deterministic logistic transformation of Stage D `scanner_score` penalized by opposing candle wick ratio.
* **Decision Policy**:
  * `action = "PROCEED"` if and only if `calibrated_probability >= scout_min_prob` (default `0.56`) AND `wick_trap_ratio <= 0.55`. Otherwise `action = "SKIP"`.
* **Strict Output Contract (`ScoutOutput`)**:
```json
{
  "action": "PROCEED",
  "exchange": "BYBIT",
  "symbol": "SOLUSDT",
  "directional_bias": "LONG",
  "opportunity_category": "BREAKOUT_CANDIDATES",
  "timeframe": "15m",
  "probability_estimate": 0.642,
  "candidate_score": 81.5,
  "supporting_features": {
    "rvol_15m": 3.45,
    "close_location_value_15m": 0.88,
    "donchian_breakout_atr": 0.38,
    "book_imbalance_top10": 0.218,
    "wick_trap_ratio": 0.12
  },
  "model_version": "scout_lgbm_v1.0.2",
  "inference_mode": "LOCAL_ML",
  "snapshot_timestamp_ms": 1761896880000
}
```

### 2.2 AGENT 2: ANALYST (Market Regime & Multi-Timeframe Directional Classifier)
* **Purpose**: Classify the macro/structural market regime (`TREND_IMPULSE`, `MEAN_REVERT_RANGE`, `HIGH_VOL_EXHAUSTION`, `LOW_LIQ_CHOP`) and predict meta-labeling directional survival probability across `5m`, `15m`, `1h`, and `4h` features.
* **Local Quantitative & ML Methods**:
  1. **Unsupervised/Statistical Regime Filter**: 4-state regime classifier using `1h`/`4h` `ADX_14`, `NATR_percentile_100`, `Hurst_exponent_64`, and `EMA_alignment_score`.
  2. **Calibrated `LightGBM` Meta-Classifier (`analyst_lgbm_v{N}`)**: Evaluates 38 multi-timeframe features (`5m`, `15m`, `1h`, `4h` + cross-asset BTC/ETH beta correlation) to predict whether `SCOUT`'s directional signal survives a 16-bar (`4 hour`) horizon without breaching structural invalidation.
  3. **Deterministic Invalidation Calculator**: Computes `invalidation_price` directly from point-in-time `15m`/`1h` swing lows (for `LONG`) or swing highs (for `SHORT`) bounded by `[0.6 * ATR_15m, 3.0 * ATR_15m]`.
* **Decision Policy**:
  * `action = "PROCEED"` if `regime != "LOW_LIQ_CHOP"`, `directional_probability >= analyst_min_prob` (default `0.58`), and `directional_bias` matches `SCOUT.directional_bias`. Otherwise `action = "SKIP"`.
* **Strict Output Contract (`AnalystOutput`)**:
```json
{
  "action": "PROCEED",
  "market_regime": "TREND_IMPULSE",
  "volatility_regime": "EXPANDING",
  "directional_bias": "LONG",
  "directional_probability": 0.668,
  "confidence": 0.668,
  "invalidation_price": 182.40,
  "key_support_levels": [182.40, 180.50, 176.80],
  "key_resistance_levels": [186.90, 189.40, 191.00],
  "supporting_evidence": [
    "mtf_ema_alignment_score=1.00 (5m/15m/1h/4h bullish)",
    "adx_1h=28.5 (>25 trend threshold)",
    "hurst_1h=0.61 (persistent trending regime)"
  ],
  "contradicting_evidence": [
    "funding_rate_pct=0.0105 (moderately positive)"
  ],
  "top_feature_contributions": {
    "mtf_ema_alignment": 0.19,
    "rvol_15m_zscore": 0.14,
    "dist_to_4h_resistance_atr": 0.11,
    "funding_crowding_penalty": -0.04
  },
  "model_version": "analyst_lgbm_v1.0.2",
  "inference_mode": "LOCAL_ML"
}
```

### 2.3 AGENT 3: SNIPER (Quantitative Entry, TP/SL Outcome & Expected Value Optimizer)
* **Purpose**: Convert validated `ANALYST` setups into concrete, tick-rounded trade proposals (`entry_price`, `stop_loss`, `take_profit_1`, `take_profit_2`, `order_type`) by optimizing expected net R-multiple across candidate ATR barrier grids.
* **Strict Price Grounding Rule**: `SNIPER` **never** predicts raw asset prices directly. All prices are computed deterministically from `mark_price`, `bid1`, `ask1`, `ANALYST.invalidation_price`, and `ATR_15m`, then rounded to `InstrumentMeta.tick_size`.
* **Local Quantitative & ML Methods**:
  1. **Candidate Barrier Grid Evaluation**:
     * Defines stop distance $d_{\text{SL}} = |P_{\text{entry}} - P_{\text{stop}}|$ anchored just beyond `ANALYST.invalidation_price` ($+0.15 \times \text{ATR}_{15m}$ buffer), clamped to $[0.6 \times \text{ATR}_{15m},\; 3.2 \times \text{ATR}_{15m}]$.
     * Evaluates 3 candidate target profiles: Conservative ($1.8R / 2.5R$), Balanced ($2.0R / 3.2R$), and Extended ($2.5R / 4.5R$), capped so `take_profit_2` does not exceed $0.90 \times$ distance to major `4h` opposing structure.
  2. **Triple-Barrier Outcome Models (`sniper_lgbm_v{N}`)**:
     * Predicts calibrated $P(\text{Hit TP1 before SL})$, $P(\text{Hit TP2 before SL})$, and expected holding duration (in minutes) conditioned on volatility, orderbook imbalance, and spread.
  3. **Expected Net R-Multiple Calculation**:
     $$\mathbb{E}[R_{\text{net}}] = P_{\text{TP1}} \cdot w_1 R_{\text{TP1}} + P_{\text{TP2}} \cdot (1 - w_1) R_{\text{TP2}} - (1 - P_{\text{TP1}}) \cdot 1.0 - \text{FeeAndSlippageInR}$$
  4. **Deterministic Entry Methodology (`MARKET` vs. `LIMIT`)**:
     * Selects `MARKET` if `Scout.opportunity_category in ("BREAKOUT_CANDIDATES", "VOLATILITY_EXPANSION")`, `rvol_15m >= 2.5`, and `spread_bps <= 8.0`.
     * Selects `LIMIT` otherwise, placing `entry_price` at the optimal pullback level (`max(bid1, ema9_5m)` for `LONG` or `min(ask1, ema9_5m)` for `SHORT`, within $0.4 \times \text{ATR}_{15m}$ of `mark_price`).
* **Decision Policy**:
  * `action = "PROPOSE_TRADE"` if $\mathbb{E}[R_{\text{net}}] \ge 0.25R$ and gross blended $R:R \ge 1.85$. Otherwise `action = "SKIP"`.
* **Strict Output Contract (`SniperOutput`)**:
```json
{
  "action": "PROPOSE_TRADE",
  "exchange": "BYBIT",
  "symbol": "SOLUSDT",
  "side": "LONG",
  "order_type": "LIMIT",
  "reference_mark_price": 184.63,
  "entry_price": 184.45,
  "entry_zone_low": 184.20,
  "entry_zone_high": 184.65,
  "stop_loss": 182.22,
  "take_profit_1": 188.91,
  "take_profit_2": 191.59,
  "tp1_close_pct": 0.50,
  "estimated_reward_risk": 2.60,
  "expected_net_r": 0.41,
  "prob_tp1_before_sl": 0.61,
  "prob_tp2_before_sl": 0.44,
  "expected_holding_minutes": 135,
  "rationale": "LIMIT pullback entry at 184.45 (0.15 ATR pullback); SL=182.22 (-1.89 ATR below 15m swing low 182.40); TP1=2.0R (188.91), TP2=3.2R (191.59); E[R_net]=+0.41R.",
  "confidence": 0.635,
  "model_version": "sniper_lgbm_v1.0.2",
  "inference_mode": "LOCAL_ML"
}
```

### 2.4 AGENT 4: RISK (100% Deterministic Python Risk & Sizing Engine)
* **Purpose**: Enforce all 12 hard portfolio, leverage, spread, slippage, drawdown, and net $R:R$ constraints and calculate exact contract quantity (`RISK_ENGINE_SPECIFICATION.md`).
* **Authority**: **Absolute Veto (`REJECT`)**. 100% deterministic Python. No ML model is ever used inside `RISK`, and no ML probability can override a hard risk limit.

### 2.5 AGENT 5: BANKER (Deterministic Position State Machine + Optional Exit Classifier)
* **Purpose**: Manage active paper positions on every WebSocket tick, execute stop-loss / take-profit / trailing-stop rules, settle perpetual funding, and record structured post-trade analytics in `trade_journal`.
* **Local Quantitative & ML Methods**:
  1. **Primary Engine: Deterministic Position State Machine (100% Python, Runs Every Tick `< 0.2 ms`)**:
     * Monitors `mark_price` against `current_stop_loss`.
     * Monitors L1/last price against `take_profit_1` and `take_profit_2`.
     * Automatically ratchets `current_stop_loss` to `avg_entry_price + fee_buffer` upon `TP1` fill.
     * Trails stop-loss at $1.5 \times \text{ATR}_{5m}$ behind highest `5m` close (for `LONG`) or lowest `5m` close (for `SHORT`) once unrealized PnL exceeds $+2.0R$.
     * Enforces time-stop cancellation on unfilled `LIMIT` entry orders after `30 minutes`.
  2. **Secondary Optional Module: Exit Deterioration Classifier (`banker_lgbm_v{N}`)**:
     * Evaluated only on **closed `5m` candle boundaries** (every 5 minutes, `< 0.5 ms` CPU).
     * Enabled **only** if walk-forward out-of-sample testing proves it improves net portfolio expectancy over the deterministic trailing stop alone (`TESTING_STRATEGY.md`).
     * Predicts `hazard_prob` (probability that an open position in drawdown or stagnation will hit SL before recovering to breakeven given opposing `5m`/`15m` volume climax and orderbook reversal).
     * **Hard Safety Constraint**: Even when enabled, the classifier may only recommend `HOLD`, `TIGHTEN_STOP` (strictly reducing risk), or `EARLY_EXIT` when `hazard_prob >= 0.78`. It can **never** widen or remove a stop-loss.
  3. **Automated Quantitative Post-Trade Evaluator**:
     * Upon position close, deterministically calculates `realized_r_multiple`, `MFE_in_R` (Maximum Favorable Excursion), `MAE_in_R` (Maximum Adverse Excursion), `edge_ratio = MFE / MAE`, `slippage_drag_r`, and `funding_drag_r`, generating a structured attribution summary for `trade_journal`.
