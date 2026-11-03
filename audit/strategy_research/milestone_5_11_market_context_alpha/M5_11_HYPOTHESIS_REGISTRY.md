# QUANTUM — MILESTONE 5.11
## HYPOTHESIS REGISTRY & FALSIFIABLE SPECIFICATION

---

### 1. EXECUTIVE SUMMARY

- **Milestone Designation:** Milestone 5.11 (Multi-Factor Market Context & Causal Alpha Discovery)
- **Git Branch:** `research/quantum-next-3pct`
- **Location:** `audit/strategy_research/milestone_5_11_market_context_alpha/M5_11_HYPOTHESIS_REGISTRY.md`
- **Objective:** Formulate, document, and catalog six distinct falsifiable market hypotheses and four benchmark baselines, codifying their economic mechanisms, observable entry/exit rules, invalidation conditions, and structural limitations.
- **Scientific Premise:** These hypotheses are research constructs, not proven strategies. They are tested under strict AsterDEX Base Retail transaction friction to measure whether genuine net economic edge exists.

---

### 2. HYPOTHESIS CATALOG OVERVIEW

```
+------------------------------------------------------------------------------------------------------------------------------------+
| QUANTUM HYPOTHESIS REGISTRY MATRIX                                                                                                 |
+---------+-------------------------------+-----------------------+---------------------+-------------------+------------------------+
| ID      | Hypothesis Nomenclature       | Primary Information   | Target Regime       | Expected Horizon  | Invalidation Rule      |
+---------+-------------------------------+-----------------------+---------------------+-------------------+------------------------+
| HYP-01  | Liquidity Sweep and Reclaim   | Structure + Volume    | HV_RANGE / Choppy   | 30m to 3h (6-36b) | Bar close past extreme |
| HYP-02  | Volatility Expansion Breakout | Volatility + Volume   | HV_TREND            | 1h to 4h (12-48b) | Midline Donchian cross |
| HYP-03  | Momentum Continuation         | Trend + Momentum      | HV_TREND / LV_TREND | 45m to 3h (9-36b) | Close beyond 50 EMA    |
| HYP-04  | Failed Breakout Reversal      | Structure + Momentum  | LV_RANGE / HV_RANGE | 30m to 2h (6-24b) | Breakout candle breach |
| HYP-05  | Range Mean Reversion          | Volatility + Oscill.  | LV_RANGE            | 30m to 2h (6-24b) | Transition to Trend    |
| HYP-06  | Cross-Asset Relative Strength | Cross-Asset + Breadth | Altcoin Rotation    | 1h to 3h (12-36b) | Relative Strength flip |
+---------+-------------------------------+-----------------------+---------------------+-------------------+------------------------+
| BASE-01 | Always Flat Baseline          | Benchmark             | All Regimes         | Infinite          | Zero activity          |
| BASE-02 | Buy and Hold BTC Baseline     | Benchmark             | Macro Trend         | Full Backtest     | N/A                    |
| BASE-03 | Simple Momentum (EMA 9/21)    | Technical Indicator   | All Regimes         | 30m to 6h         | Opposite crossover     |
| BASE-04 | Simple Mean Reversion (BB)    | Technical Indicator   | All Regimes         | 30m to 4h         | Band cross             |
+---------+-------------------------------+-----------------------+---------------------+-------------------+------------------------+
```

---

### 3. COMPLETE HYPOTHESIS SPECIFICATIONS

#### 3.1 HYP-01: Liquidity Sweep and Reclaim
- **Hypothesis ID:** `HYP-01`
- **Market Mechanism:** Clusters of retail stop-loss orders beyond confirmed swing highs and lows provide depth for institutional absorption. Once stops are triggered, the depletion of opposing orders allows aggressive displacement back into the prior range.
- **Observable Evidence:** Price pierces confirmed swing high (BSL) or swing low (SSL) intra-bar, but closes back inside the range with abnormal volume ($RVOL \ge 1.20$) and solid body displacement ($Body/Range \ge 0.68$).
- **Required Features:** `swing_high`, `swing_low`, `bsl_sweep_reclaim`, `ssl_sweep_reclaim`, `rvol_20`, `atr_14`, `bullish_displacement`.
- **Entry Conditions:** Long at next-bar open following SSL sweep + reclaim + bullish displacement; Short following BSL sweep + reclaim + bearish displacement.
- **Exit Conditions:** Take profit at $2.0 \times \text{ATR}$; Stop loss at swept extreme plus $0.5 \times \text{ATR}$; Maximum holding duration $48\text{ bars}$ ($240\text{ minutes}$).
- **Invalidation Conditions:** Immediate subsequent candle close beyond the swept extreme invalidates the absorption premise.
- **Cost Assumptions:** AsterDEX Base Retail ($10.0\text{ bps}$ taker entry, $10.0\text{ bps}$ taker exit, $2.0\text{ bps}$ slippage, $1.0\text{ bps}$ half-spread).
- **Known Limitations:** In high-momentum runaway trends, price pierces swing extrema without looking back, resulting in immediate stop-outs.

---

#### 3.2 HYP-02: Volatility Expansion Breakout
- **Hypothesis ID:** `HYP-02`
- **Market Mechanism:** Consolidation regimes store directional energy as liquidity clusters beyond the range boundaries. A breakout accompanied by volatility expansion and volume surge reflects institutional expansion rather than a retail trap.
- **Observable Evidence:** Price closes outside the 20-bar Donchian channel while Volatility Cycle is `EXPANSION` ($\text{ATR Percentile} \ge 65.0\%$), $ADX \ge 22.0$, and $RVOL \ge 1.50$.
- **Required Features:** `donchian_high_20`, `donchian_low_20`, `atr_percentile_100`, `rvol_20`, `adx_14`.
- **Entry Conditions:** Long on Donchian High close + expansion; Short on Donchian Low close + expansion. Causal entry at next-bar open.
- **Exit Conditions:** Stop loss at $1.5 \times \text{ATR}$; Take profit at $2.0 \times \text{ATR}$; Max hold $48\text{ bars}$.
- **Invalidation Conditions:** Close back inside the Donchian channel midline.
- **Known Limitations:** Severe vulnerability to false breakouts during choppy range regimes ($80\%$ of crypto 5m bars).

---

#### 3.3 HYP-03: Momentum Continuation
- **Hypothesis ID:** `HYP-03`
- **Market Mechanism:** Persistent multi-timeframe trends exhibit positive directional autocorrelation. Minor pullbacks to dynamic support levels (e.g. 21 EMA) provide favorable risk/reward continuation entries.
- **Observable Evidence:** EMAs stacked in alignment score ($+1.0$ or $-1.0$), $ADX \ge 22.0$, low touches EMA 21, close recovers above EMA 21, and RSI rebounds from $42-50$ zone with positive ROC acceleration.
- **Required Features:** `ema_alignment_score`, `ema_21`, `adx_14`, `rsi_14`, `momentum_acceleration`.
- **Entry Conditions:** Long on pullback touch + recovery + positive acceleration; Short inverse. Next-bar open.
- **Exit Conditions:** Take profit at $2.0 \times \text{ATR}$; Stop loss at $1.5 \times \text{ATR}$; Max hold $48\text{ bars}$.
- **Invalidation Conditions:** Candle close beyond EMA 50 signals trend structure breakdown.
- **Known Limitations:** Degrades when macro trend momentum exhausts into climax consolidation.

---

#### 3.4 HYP-04: Failed Breakout Reversal
- **Hypothesis ID:** `HYP-04`
- **Market Mechanism:** Breakouts that occur on drying volume or during range regimes fail due to lack of aggressive order flow follow-through, trapping breakout traders and forcing a mean-reverting snapback.
- **Observable Evidence:** Price pierces Donchian high or low, but relative volume is dry ($RVOL < 1.10$), followed immediately by an opposite close.
- **Required Features:** `donchian_high_20`, `donchian_low_20`, `rvol_20`, `market_regime`.
- **Entry Conditions:** Short when High breaks Donchian High but $RVOL < 1.10$ and close finishes lower; Long inverse. Next-bar open.
- **Exit Conditions:** Stop loss at breakout extreme plus $0.5 \times \text{ATR}$; Take profit at $2.0 \times \text{ATR}$; Max hold $48\text{ bars}$.
- **Invalidation Conditions:** Subsequent bar closing beyond the breakout extreme confirms true breakout.
- **Known Limitations:** Incur catastrophic losses if the market enters an unexpected trend runaway.

---

#### 3.5 HYP-05: Range Mean Reversion
- **Hypothesis ID:** `HYP-05`
- **Market Mechanism:** In certified low-volatility range regimes ($ADX < 22.0$, $KER < 0.35$), price oscillates as a bounded mean-reverting process between statistical equilibrium extremes.
- **Observable Evidence:** Regime is `LV_RANGE` or `HV_RANGE`, price pierces outer Bollinger Band ($2.0\text{ std}$), and Stochastic oscillator shows extreme exhaustion ($Stoch\_K < 25$ crossing $Stoch\_D$ upward for Long).
- **Required Features:** `market_regime`, `efficiency_ratio_20`, `bb_upper`, `bb_lower`, `stoch_k`, `stoch_d`.
- **Entry Conditions:** Long on lower band touch + Stoch bullish cross in Range regime; Short inverse. Next-bar open.
- **Exit Conditions:** Take profit at $2.0 \times \text{ATR}$; Stop loss at $1.5 \times \text{ATR}$; Max hold $48\text{ bars}$.
- **Invalidation Conditions:** Regime transition into `HV_TREND` immediately terminates trade.
- **Known Limitations:** Extreme vulnerability when a quiet range abruptly transitions into an explosive breakout.

---

#### 3.6 HYP-06: Cross-Asset Relative Strength
- **Hypothesis ID:** `HYP-06`
- **Market Mechanism:** Capital rotates between Bitcoin and high-beta altcoins. Assets demonstrating persistent relative strength over 1-hour windows during Bitcoin consolidation lead subsequent directional moves.
- **Observable Evidence:** Asset 1-hour return outperforms BTC 1-hour return by $\ge +0.80\%$, BTC trend is non-bearish (`btc_trend_bull == 1.0`), and market breadth $\ge 0.45$.
- **Required Features:** `rel_strength_vs_btc_1h`, `btc_trend_bull`, `market_breadth_bull_pct`, `rsi_14`.
- **Entry Conditions:** Long when relative strength divergence $\ge +0.80\%$ and market breadth $\ge 0.45$; Short when relative strength $\le -0.80\%$ and breadth $\le 0.55$.
- **Exit Conditions:** Take profit at $2.0 \times \text{ATR}$; Stop loss at $1.5 \times \text{ATR}$; Max hold $48\text{ bars}$.
- **Invalidation Conditions:** BTC flash crash or violent reversal.
- **Known Limitations:** Beta divergence collapses instantly during market-wide liquidity shocks.

---

### 4. BENCHMARK BASELINES

- **BASE-01 (Always Flat):** Evaluates risk-free zero-position baseline ($0$ trades, $\$0.00$ PnL, $0.0\text{ bps}$ expectancy).
- **BASE-02 (Buy and Hold BTC):** 1 long trade held across entire evaluation window ($+1,803.86\text{ bps}$ net, $18.4\%$ max drawdown).
- **BASE-03 (Simple Momentum EMA 9/21):** Classic moving average crossover without regime filtering ($19,352$ trades, $22.47\%$ win rate, $-26.07\text{ bps}$ net expectancy).
- **BASE-04 (Simple Mean Reversion BB):** Classic counter-trend Bollinger Band fade ($27,522$ trades, $27.28\%$ win rate, $-24.99\text{ bps}$ net expectancy).
