# QUANTUM — HYP-03 STRATEGY SPECIFICATION
## Statistical Mean Reversion in Low-Volatility & Ranging Regimes

**Document Identifier:** `audit/strategy_research/milestone_5_4_alpha_expansion/HYP03_SPECIFICATION.md`  
**Publication Timestamp:** 2026-11-03 21:07:00 UTC  
**Active Branch:** `research/quantum-next-3pct`  
**Strategy ID:** `HYP03_MEAN_REVERSION_V1`  
**Lead Quantitative Research Engineer:** Statistical Modeler & Quantitative Systems Architect  
**Research Status:** Experimental Alpha Candidate  

---

## 1. Executive Summary & Alpha Thesis

The primary objective of `HYP-03` is to extract statistical mean-reversion alpha during low-volatility, range-bound market environments where trend-following strategies (such as `HYP-01`) systematically suffer from whipsaws and low returns.

### 1.1 Research Motivation from Milestone 5.3
In Milestone 5.3, performance attribution across macro regimes revealed an acute performance asymmetry in `HYP-01`:
- **High-Volatility Bear Regime:** $+3.7214\%$ mean daily return.
- **High-Volatility Bull Regime:** $+2.7108\%$ mean daily return.
- **Low-Volatility Bear Regime:** $+1.3642\%$ mean daily return.
- **Low-Volatility Bull Regime:** $+1.2918\%$ mean daily return.

During low-volatility regimes ($49.8\%$ of total calendar days), trending momentum expansions are rare, and prices remain constrained within bounded statistical envelopes. Trend breakout systems repeatedly enter false breaks only to get chopped out. Conversely, mean-reversion systems that fade extreme statistical displacements can harvest steady, high-frequency edge in these stagnant regimes, lifting the overall portfolio daily return toward the mandatory $3.00\%$ target.

---

## 2. Mathematical Definition & Signal Logic

All calculations are strictly point-in-time and causal. Zero forward-looking information is utilized.

### 2.1 Moving Equilibrium Benchmark
Let $C_t$ denote the Close of the 5-minute candle at time $t$.  
Let $K = 20$ bars ($100\text{ minutes}$ on 5m timeframe) denote the moving equilibrium window.

The moving average equilibrium is defined as:
$$\mu_{20, t} = \frac{1}{K} \sum_{j=0}^{K-1} C_{t-j}$$

### 2.2 Volatility-Normalized Statistical Price Displacement ($Z$-Score)
Let $\sigma_{20, t}$ denote the trailing 20-bar 5-minute standard deviation of log-returns. The local dollar price volatility is given by:
$$\Sigma_t = \max(\sigma_{20, t} \times C_t, 10^{-6})$$

The standardized price displacement $Z_t$ is defined as:
$$Z_t = \frac{C_t - \mu_{20, t}}{\Sigma_t}$$

> [!NOTE]
> $Z_t$ measures how many standard deviations price has deviated from its 20-period moving average. In a Gaussian regime, $|Z_t| \ge 2.2$ represents a statistically extreme $> 98.6\%$ two-tailed deviation.

### 2.3 Strict Regime Suppression Filter (Anti-Trend Armor)
To prevent the catastrophic error of fading a strong directional trend or structural volatility breakout, `HYP-03` enforces strict point-in-time regime suppression:
1. **Higher-Timeframe Trend Ceiling:**
   $$|HTF_{12, t}| \le \theta_{\text{trend}} = 75.0\text{ bps}$$
   (where $HTF_{12, t} = \frac{C_t - C_{t-12}}{C_{t-12}} \times 10,000$).
2. **Volatility Ceiling:**
   $$\sigma_{20, t} \le \theta_{\sigma} = 0.0020$$
3. **Explosive Trend Exclusion:**
   If $|HTF_{12, t}| > 100.0\text{ bps}$ AND $\sigma_{20, t} > 0.0015$ (High-Volatility Trending Regime), all HYP-03 signals are **strictly blocked**.

### 2.4 Reversal Candle Confirmation
To prevent "catching falling knives", an extreme $Z$-score displacement must be accompanied by candle exhaustion:
- **Long Confirmation:** $C_t > O_t$ (candle closes green, confirming rejection of the oversold extreme).
- **Short Confirmation:** $C_t < O_t$ (candle closes red, confirming rejection of the overbought extreme).

---

## 3. Formal Entry & Exit Rules

### 3.1 Long Signal (Oversold Mean Reversion)
A Long entry signal ($S_t = +1$) is generated at candle $t$ close if and only if:
1. **Extreme Displacement:** $Z_t \le -2.20$ (price is $\ge 2.2\sigma$ below moving average).
2. **Reversal Confirmation:** $C_t > O_t$ (candle closes positive).
3. **Ranging Regime:** $|HTF_{12, t}| \le 75.0\text{ bps}$.
4. **Volatility Condition:** $\sigma_{20, t} \le 0.0020$.
5. **No Explosive Breakout:** Not classified as High-Volatility Trending.

### 3.2 Short Signal (Overbought Mean Reversion)
A Short entry signal ($S_t = -1$) is generated at candle $t$ close if and only if:
1. **Extreme Displacement:** $Z_t \ge +2.20$ (price is $\ge 2.2\sigma$ above moving average).
2. **Reversal Confirmation:** $C_t < O_t$ (candle closes negative).
3. **Ranging Regime:** $|HTF_{12, t}| \le 75.0\text{ bps}$.
4. **Volatility Condition:** $\sigma_{20, t} \le 0.0020$.
5. **No Explosive Breakout:** Not classified as High-Volatility Trending.

### 3.3 Execution Pricing & Arrival
- **Order Type:** Market Taker order executed at the open of the subsequent bar:
  $$P_{\text{entry}} = O_{t+1}$$

---

## 4. Volatility-Adjusted Barrier Engine

### 4.1 Stop-Loss Calibration
Because mean-reversion trades rely on rapid snap-back, stop losses are tight and volatility-scaled:
$$\Delta_{\text{SL}} = 1.50 \times \sigma_{20, t} \times P_{\text{entry}}$$
- **Long SL:** $P_{\text{SL}} = P_{\text{entry}} - \Delta_{\text{SL}}$
- **Short SL:** $P_{\text{SL}} = P_{\text{entry}} + \Delta_{\text{SL}}$

### 4.2 Take-Profit Targets & Breakeven Ratchet
- **Take-Profit 1 (TP1):** Placed at $+1.50 \times \sigma_{20, t} \times P_{\text{entry}}$ (reversion toward mean).
  - Closes $50\%$ of position via Limit Maker order ($2.0\text{ bps}$ fee).
  - Stop-loss is moved to $P_{\text{entry}}$ (breakeven ratchet).
- **Take-Profit 2 (TP2):** Placed at $+2.50 \times \sigma_{20, t} \times P_{\text{entry}}$ (full mean reversion / mean overshoot).
  - Closes remaining $50\%$ of position via Limit Maker order.
- **Trailing Stop:** $1.20 \times \sigma_{20, t} \times C_\tau$ active after TP1.
- **Maximum Holding Horizon:** Strictly capped at $8\text{ bars (40 minutes)}$. If the price has not reverted within 40 minutes, the trade is closed at market taker.

---

## 5. Position Sizing & Portfolio Risk Management

- **Risk Budget per Trade:** $1.50\%$ of current portfolio equity.
- **Leverage Constraints:** Max $3.0\times$ leverage, Max $25\%$ symbol exposure.
- **Circuit Breakers:** $4.0\%$ daily loss breaker and $15.0\%$ drawdown scaler ($0.5\times$).

---

## 6. Structural Synergy with HYP-01 and HYP-02

```
+---------------------------------------------------------------------------------------------------------+
| Characteristic          | HYP-01 (Trend Following)     | HYP-02 (Liquidity Sweep)   | HYP-03 (Mean Reversion)   |
+---------------------------------------------------------------------------------------------------------+
| Alpha Mechanism         | Directional Momentum Breakout| Stop-Run Absorption & Snap | Statistical Z-Score Decay |
| Optimal Market Regime   | High-Vol Trending            | Volatile Ranging / Turns   | Low-Vol Ranging / Chop    |
| Entry Style             | Trend Following (Pro-trend)  | Counter-Breakout (Fading)  | Counter-Deviation (Fading)|
| Barrier Multipliers     | TP1=2.5s, TP2=4.0s, SL=1.5s  | TP1=2.0s, TP2=3.5s, SL=1.5s| TP1=1.5s, TP2=2.5s, SL=1.5s|
| Average Holding Time    | 4 - 6 bars (20 - 30 mins)    | 6 - 8 bars (30 - 40 mins)  | 4 - 8 bars (20 - 40 mins) |
| Correlation with HYP-01 | +1.000 (Baseline)            | Low / Orthogonal           | Near Zero / Negative      |
+---------------------------------------------------------------------------------------------------------+
```

By pairing `HYP-01` with `HYP-03`, capital is productively deployed across both trending and ranging market regimes, providing smooth daily returns and suppressing portfolio drawdown.
