# QUANTUM MILESTONE 5.13 — MULTI-FACTOR CONFLUENCE ENGINE DESIGN

**Milestone:** M5.13 — Multi-Factor Confluence & Passive Maker Alpha Discovery  
**Repository:** `d:/quantum-multi-agent`  
**Audit Date:** 2026-11-04  
**Classification:** Research Architecture & Quantitative Engineering  
**Module:** [`src/quantum/strategies/confluence_engine.py`](file:///d:/quantum-multi-agent/src/quantum/strategies/confluence_engine.py)  

---

## 1. Engine Objective

The Multi-Factor Confluence Engine solves a critical structural weakness of previous QUANTUM iterations: relying on isolated indicators (e.g. single moving average crosses or unconditioned oscillator extremes) that generated high-frequency, low-margin signals easily destroyed by execution friction.

The Confluence Engine transforms alpha discovery by:
1. Extracting 10 orthogonal information dimensions across multiple timeframes (5m, 15m, 1h).
2. Implementing strict causal broadcasting (higher timeframe candles must be 100% completed before lower timeframe ingestion).
3. Providing three distinct aggregation methodologies (Rule-Based, Statistical Scoring, and Machine Learning Ranking) evaluated under identical backtest conditions.

---

## 2. The Ten Factor Dimensions

```
   +-----------------------------------------------------------------------+
   |                MULTI-FACTOR CONFLUENCE ENGINE (10 FACTORS)            |
   +-----------------------------------+-----------------------------------+
   | Dimension                         | Operational Feature / Indicator   |
   +-----------------------------------+-----------------------------------+
   | 1. Trend Structure & Alignment    | EMA (9, 21, 50, 200), slope, 1h   |
   | 2. Momentum & Acceleration        | RSI(14), Stochastic, RoC          |
   | 3. Volatility & Expansion         | ATR Percentile, BB Bandwidth      |
   | 4. Volume & Order Flow Proxy      | RVOL, OFI Proxy, Taker Volume     |
   | 5. Market Structure               | Causal Swings, Donchian Breakout  |
   | 6. Liquidity Sweeps               | BSL/SSL Sweeps, Displacement Recl |
   | 7. Relative Strength              | Cross-sectional vs BTC, Beta      |
   | 8. Regime Classification          | 4-State (HV/LV Trend, HV/LV Range)|
   | 9. Execution Quality              | Spread/Depth Proxy, Vol/Liquidity |
   | 10. Risk-Adjusted Opportunity     | Target/Stop Distance (ATR units)  |
   +-----------------------------------+-----------------------------------+
```

### Detailed Factor Specifications
1. **Factor 1 (Trend):** Computes exponential moving averages across 4 horizons. Bullish alignment requires $C > \text{EMA}_9 > \text{EMA}_{21} > \text{EMA}_{50}$. Integrates 1-hour directional bias via backward asof merge.
2. **Factor 2 (Momentum):** Normalized RSI centered around 50: $M = \text{clip}\left(\frac{\text{RSI}_{14} - 50}{50}, -1.0, 1.0\right)$.
3. **Factor 3 (Volatility):** Rolling 100-bar percentile of Bollinger Bandwidth: $\text{BW} = \frac{\text{Upper} - \text{Lower}}{\text{Middle}}$. Identifies compression cycles ($< 25\text{th}$ percentile) preceding breakouts.
4. **Factor 4 (Volume & Order Flow):** RVOL relative to 20-bar SMA; Order Flow Imbalance (OFI) proxy:
   $$\text{OFI} = \frac{V_{\text{taker\_buy}} - V_{\text{taker\_sell}}}{V_{\text{total}}}$$
5. **Factor 5 (Market Structure):** Causal swing detection using 5-bar rolling lookback and 5-bar confirmation. Donchian 20-bar channel high/low breaks.
6. **Factor 6 (Liquidity Sweeps):** Identifies sweeps where price pierces a confirmed swing high/low by $\ge 0.5$ ATR and immediately closes back inside the range with high-volume displacement.
7. **Factor 7 (Relative Strength):** 1-hour rolling return differential against Bitcoin benchmark: $RS = R_{\text{asset}} - R_{\text{BTC}}$.
8. **Factor 8 (Regime):** 4-State classification combining ADX(14), ATR Percentile, and Kaufman Efficiency Ratio.
9. **Factor 9 (Execution Quality):** Ratio of volume expansion to volatility percentile: measures expected book depth and slippage resistance.
10. **Factor 10 (Opportunity):** Dynamic reward-to-risk ratio based on structure-based stop loss versus next liquidity target (default 1:2.0 to 1:2.5).

---

## 3. The Three Aggregation Methodologies

### Method A: Rule-Based Confluence
- **Mechanism:** Weighted logical condition gates with explicit confidence thresholds ($S_{\text{conf}} \ge 0.65$).
- **Advantage:** Maximum transparency and determinism; zero risk of machine learning overfitting.
- **Rule Example (Trend Continuation):**
  $$\text{Signal} = 1 \iff (\text{HTF\_Trend} > 0) \land (\text{Trend\_Score} \ge 0.5) \land (45 < \text{RSI} < 65) \land (\text{ADX} > 20) \land (\text{RVOL} > 1.0)$$

### Method B: Statistical Scoring
- **Mechanism:** Standardizes linear composite factor scores using a rolling 100-bar Z-score:
  $$Z_t = \frac{C_t - \mu_{C, 100}}{\sigma_{C, 100}}$$
  where composite $C_t = \sum w_k f_k(t)$.
- **Threshold:** Triggers entries when $|Z_t| \ge 1.75$ (top/bottom $4\%$ statistical extremes).
- **Advantage:** Continuous confidence metric; scales naturally with changing market volatility.

### Method C: Machine Learning Opportunity Ranking
- **Mechanism:** Causal Random Forest Regressor trained strictly on historical in-sample discovery partitions (TRAIN).
- **Target Variable:** Forward 24-bar ATR-normalized net return:
  $$y_t = \frac{P_{t+24} - P_t}{\text{ATR}_t}$$
- **Hyperparameters:** `n_estimators=50`, `max_depth=5`, `min_samples_leaf=20`, `random_state=42`.
- **Ranking Gating:** Emits long signals when $\hat{y}_t \ge +0.45\text{ ATR}$; short signals when $\hat{y}_t \le -0.45\text{ ATR}$.
- **Advantage:** Captures non-linear feature interactions (e.g., volume confirmation matters much more during volatility compression than during trend exhaustion).

---

## 4. Implementation Validation

The engine is encapsulated in [`src/quantum/strategies/confluence_engine.py`](file:///d:/quantum-multi-agent/src/quantum/strategies/confluence_engine.py). All operations are strictly vectorized in NumPy and Pandas, avoiding Python iteration across the 1.5 million historical bars.
