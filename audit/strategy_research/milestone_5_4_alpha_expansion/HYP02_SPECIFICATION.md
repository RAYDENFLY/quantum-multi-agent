# QUANTUM — HYP-02 STRATEGY SPECIFICATION
## Institutional Liquidity Sweep & Reclaim Architecture

**Document Identifier:** `audit/strategy_research/milestone_5_4_alpha_expansion/HYP02_SPECIFICATION.md`  
**Publication Timestamp:** 2026-11-03 21:05:00 UTC  
**Active Branch:** `research/quantum-next-3pct`  
**Strategy ID:** `HYP02_LIQUIDITY_SWEEP_V1`  
**Lead Quantitative Research Engineer:** Quantitative Architect & Microstructure Specialist  
**Research Status:** Experimental Alpha Candidate  

---

## 1. Executive Summary & Alpha Thesis

The primary objective of `HYP-02` is to capture high-probability counter-liquidity reversals following structural stop-runs across crypto perpetual markets. 

### 1.1 Microstructure Rationale
Retail and algorithmic breakout strategies systematically place stop-loss and breakout entry orders just beyond visible swing highs and swing lows. In crypto perpetuals, large institutional market participants and liquidity providers exploit these liquidity pools:
1. **Stop Run (The Sweep):** Price is driven beyond a key swing level, triggering stop-loss clusters and market breakout orders.
2. **Absorption & Rejection:** The aggressive flow is absorbed by institutional limit orders, creating an immediate order-book vacuum in the breakout direction.
3. **Reclaim:** Price rapidly snaps back inside the previous trading range, leaving a long rejection wick and trapping breakout traders offside.
4. **Impulsive Reversal:** Forced liquidations of trapped breakout traders propel an impulsive counter-directional move toward the opposite liquidity boundary or range midpoint.

---

## 2. Mathematical Definition & Signal Logic

All calculations are strictly point-in-time and causal. Zero future information is utilized.

### 2.1 Swing Liquidity Pool Identification
Let $H_t, L_t, O_t, C_t$ denote the High, Low, Open, and Close of the 5-minute candle at time $t$.  
Let $K = 12$ bars ($1\text{ hour}$ on 5m timeframe) denote the trailing swing evaluation window.

The reference liquidity levels are defined as:
$$H_{\text{prior}, t} = \max_{1 \le j \le K} H_{t-j}$$
$$L_{\text{prior}, t} = \min_{1 \le j \le K} L_{t-j}$$

> [!NOTE]
> The indexing strictly uses $t-j$ with $j \ge 1$, ensuring the current candle $t$ is never included in the reference swing calculation.

### 2.2 Candle Geometry & Wick Rejection
Let the candle total range be:
$$R_t = \max(H_t - L_t, 10^{-8})$$

The upper and lower rejection wicks are defined as:
$$W_{\text{upper}, t} = \frac{H_t - \max(O_t, C_t)}{R_t}$$
$$W_{\text{lower}, t} = \frac{\min(O_t, C_t) - L_t}{R_t}$$

### 2.3 Volume Expansion Confirmation
Let $V_t$ be the volume of candle $t$, and let $\bar{V}_{20, t} = \frac{1}{20} \sum_{j=0}^{19} V_{t-j}$ be the trailing 20-bar average volume.  
The relative volume expansion is defined as:
$$\text{RVOL}_{20, t} = \frac{V_t}{\bar{V}_{20, t}}$$

### 2.4 Multi-Timeframe (MTF) Context
Let $HTF_{12, t}$ denote the trailing 1-hour return in basis points:
$$HTF_{12, t} = \frac{C_t - C_{t-12}}{C_{t-12}} \times 10,000$$

To ensure the sweep is not attempting to catch an un-reclaimable macro liquidation cascade, entries are conditioned on:
$$|HTF_{12, t}| \le \theta_{\text{macro}} = 150.0\text{ bps}$$

---

## 3. Formal Entry & Exit Rules

### 3.1 Long Signal (Bullish Sweep & Reclaim)
A Long entry signal ($S_t = +1$) is generated at candle $t$ close if and only if all the following conditions are simultaneously satisfied:
1. **Penetration:** $L_t < L_{\text{prior}, t}$ (low sweeps below prior 1h swing low).
2. **Reclaim:** $C_t > L_{\text{prior}, t}$ (close reclaims back above prior 1h swing low).
3. **Wick Rejection:** $W_{\text{lower}, t} \ge 0.35$ (lower wick comprises $\ge 35\%$ of candle range).
4. **Volume Confirmation:** $\text{RVOL}_{20, t} \ge 1.10$ (volume expands $\ge 10\%$ above 20-period baseline).
5. **Macro Context:** $HTF_{12, t} \ge -150.0\text{ bps}$ (1h trend is not in an extreme vertical crash).
6. **Reversal Color:** $C_t > O_t$ (candle closes green, confirming immediate buyer dominance).

### 3.2 Short Signal (Bearish Sweep & Reclaim)
A Short entry signal ($S_t = -1$) is generated at candle $t$ close if and only if:
1. **Penetration:** $H_t > H_{\text{prior}, t}$ (high sweeps above prior 1h swing high).
2. **Reclaim:** $C_t < H_{\text{prior}, t}$ (close reclaims back below prior 1h swing high).
3. **Wick Rejection:** $W_{\text{upper}, t} \ge 0.35$ (upper wick comprises $\ge 35\%$ of candle range).
4. **Volume Confirmation:** $\text{RVOL}_{20, t} \ge 1.10$.
5. **Macro Context:** $HTF_{12, t} \le +150.0\text{ bps}$.
6. **Reversal Color:** $C_t < O_t$ (candle closes red).

### 3.3 Execution Pricing & Arrival
- **Order Type:** Market Taker order executed at the arrival open price of the subsequent bar:
  $$P_{\text{entry}} = O_{t+1}$$

---

## 4. Volatility-Adjusted Barrier Engine

### 4.1 Stop-Loss Calibration
Let $\sigma_{20, t}$ denote the trailing 20-bar 5-minute return standard deviation. The stop loss is anchored directly to the sweep extreme:
$$\Delta_{\text{SL}} = 1.50 \times \sigma_{20, t} \times P_{\text{entry}}$$
- **Long SL:** $P_{\text{SL}} = P_{\text{entry}} - \Delta_{\text{SL}}$
- **Short SL:** $P_{\text{SL}} = P_{\text{entry}} + \Delta_{\text{SL}}$

### 4.2 Dynamic Profit Taking & Breakeven Ratchet
- **Take-Profit 1 (TP1):** Placed at $+2.50 \times \sigma_{20, t} \times P_{\text{entry}}$.
  - When touched by high/low, $50\%$ of position notional is closed via a Limit Maker order ($2.0\text{ bps}$ maker fee).
  - **Breakeven Ratchet:** Stop-loss is instantly ratcheted to $P_{\text{entry}}$, eliminating remaining downside risk.
- **Take-Profit 2 (TP2):** Placed at $+4.00 \times \sigma_{20, t} \times P_{\text{entry}}$.
  - The remaining $50\%$ notional is closed via Limit Maker.
- **Trailing Stop:** After TP1 is achieved, an active trailing stop follows price at $1.50 \times \sigma_{20, t} \times C_{\tau}$.
- **Time Stop Horizon:** Maximum holding duration is strictly capped at $6\text{ bars (30 minutes)}$. Any position active at bar $t+6$ is liquidated at market taker.

---

## 5. Position Sizing & Portfolio Risk Management

- **Risk Budget per Trade:** $1.50\%$ of current portfolio equity:
  $$\text{Risk Budget} = \text{Portfolio Equity} \times 0.015$$
  $$\text{Desired Notional} = \frac{\text{Risk Budget}}{\Delta_{\text{SL}} / P_{\text{entry}}}$$
- **Leverage Constraints:**
  $$\text{Max Notional} = \text{Portfolio Equity} \times \text{Max Leverage } (3.0\times) \times \text{Max Symbol Exposure } (25\%)$$
- **Circuit Breakers:**
  - $4.0\%$ Daily Loss Circuit Breaker: Halts all new entries until next calendar day.
  - $15.0\%$ Drawdown Scaler: Halves position sizing ($0.5\times$) while peak-to-trough drawdown exceeds $15\%$.

---

## 6. Mathematical Independence from HYP-01

`HYP-02` operates on an orthogonal market mechanic compared to `HYP-01`:
- `HYP-01` is a **pro-cyclical momentum strategy**: It buys high after a sustained multi-timeframe trend has already formed and volume expands in the trend direction.
- `HYP-02` is a **counter-cyclical structural rejection strategy**: It fades breakouts beyond local swing extremes, anticipating liquidity absorption and sharp mean-reverting reclaims.

This theoretical divergence guarantees low cross-correlation and superior portfolio diversification.
