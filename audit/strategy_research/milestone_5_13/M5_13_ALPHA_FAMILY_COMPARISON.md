# QUANTUM MILESTONE 5.13 — ALPHA RESEARCH FAMILY COMPARISON

**Milestone:** M5.13 — Multi-Factor Confluence & Passive Maker Alpha Discovery  
**Repository:** `d:/quantum-multi-agent`  
**Audit Date:** 2026-11-04  
**Classification:** Strategy Research & Alpha Taxonomy  
**Author:** QUANTUM Research Architecture  

---

## 1. Executive Summary

Milestone 5.13 moves beyond naive single-indicator trading systems by systematically defining, formalizing, and comparing five independent alpha families alongside a synthesized multi-factor confluence engine and four benchmark baselines.

The core motivation is economic: micro-scalping strategies (holding $< 30$ minutes) generating $+1\text{ to } +2\text{ bps}$ gross expectancy cannot survive AsterDEX retail taker friction ($26.0\text{ bps}$). To survive realistic execution costs, strategies must capture larger gross price swings ($\ge 30\text{ to } 70\text{ bps}$) through higher-timeframe alignment, regime conditioning, and multi-factor confirmation.

---

## 2. Taxonomy of Investigated Alpha Families

### Family B1: Higher-Timeframe Trend Continuation (`HYP-07`)
- **Core Market Mechanism:** Large institutional market orders originate on higher timeframes (1h to 4h), creating persistent directional order flow that creates intraday continuation moves.
- **Key Indicators:** 1h EMA-21/50 slope, 15m pullback into EMA-21, 5m ADX $> 20$, and RVOL $> 1.0$.
- **Expected Holding Horizon:** 2 to 4 hours (24 to 48 five-minute bars).
- **Target Market Regime:** `HV_TREND`, `LV_TREND`.
- **Gross Capture Potential:** $+40\text{ to } +80\text{ bps}$ per winning trade.

### Family B2: Volatility Expansion and Breakout (`HYP-08`)
- **Core Market Mechanism:** Extended consolidation causes Bollinger bandwidth compression ($< 25\text{th}$ percentile). Breakout through Donchian 20-bar channel with expanding volume indicates institutional participation and directional volatility expansion.
- **Key Indicators:** Bollinger Bandwidth, Donchian Channel Breakout, Relative Volume (RVOL $> 1.5$).
- **Expected Holding Horizon:** 1 to 3 hours (12 to 36 bars).
- **Target Market Regime:** `LV_RANGE` transitioning into `HV_TREND`.
- **Gross Capture Potential:** $+50\text{ to } +100\text{ bps}$ on momentum continuation.

### Family B3: Causal Liquidity Sweep & Displacement Reclaim (`HYP-09`)
- **Core Market Mechanism:** Retail stop-loss clusters resting beyond confirmed swing highs and lows provide liquidity pools for institutional absorption. Once stops are absorbed, absence of opposing limit orders triggers sharp displacement back into the prior trading range.
- **Key Indicators:** Causal swing highs/lows (lookback 5, lookforward 5), displacement candle ($> 1.35$ ATR and solid body $> 68\%$), RVOL $> 1.2$.
- **Expected Holding Horizon:** 1 to 2 hours (12 to 24 bars).
- **Target Market Regime:** `HV_RANGE`, `LV_RANGE`.
- **Gross Capture Potential:** $+30\text{ to } +60\text{ bps}$.

### Family B4: Regime-Filtered Range Mean Reversion (`HYP-10`)
- **Core Market Mechanism:** In stable consolidating regimes (`LV_RANGE`, ADX $< 20$), price oscillates within standard statistical boundaries. Deviations beyond $2.5\sigma$ Bollinger bands or extreme RSI ($< 28$ or $> 72$) revert toward mean price equilibrium.
- **Key Indicators:** ADX $< 20$, Kaufman Efficiency Ratio $< 0.30$, RSI(14) extremes, counter-trend reversal close.
- **Expected Holding Horizon:** 30 minutes to 1.5 hours (6 to 18 bars).
- **Target Market Regime:** `LV_RANGE` exclusively.
- **Gross Capture Potential:** $+15\text{ to } +35\text{ bps}$.

### Family B5: Cross-Asset Leadership Momentum (`HYP-11`)
- **Core Market Mechanism:** Leading altcoins exhibit relative strength versus Bitcoin. When Bitcoin is stable or trending upward, top-quintile altcoin momentum experiences outsized beta continuation.
- **Key Indicators:** 24h rolling return difference (Asset minus BTC), 5m relative strength percentile, BTC 1h trend filter.
- **Expected Holding Horizon:** 2 to 4 hours.
- **Target Market Regime:** `HV_TREND`.
- **Gross Capture Potential:** $+45\text{ to } +90\text{ bps}$.

### Family B6: Multi-Factor Confluence Synthesis (`HYP-12`)
- **Core Market Mechanism:** Combines orthogonal information dimensions (Trend Alignment + Volume Confirmation + Liquidity Absorption + Cross-Asset Strength). Eliminates false breakouts by requiring multi-factor consensus.
- **Expected Holding Horizon:** 2 to 4 hours.
- **Target Market Regime:** Robust across trending and transitioning regimes.
- **Gross Capture Potential:** $+50\text{ to } +110\text{ bps}$.

---

## 3. Structural Comparison Matrix

| Hypothesis ID | Family Name | Primary Timeframe | Expected Holding Horizon | Frequency Category | Target Regime | Target R:R | Minimum Gross Edge Target |
| :--- | :--- | :---: | :---: | :---: | :--- | :---: | :---: |
| **HYP-07** | Trend Continuation | 1h + 5m | 2h - 4h | Category B (2-5/day) | `HV_TREND`, `LV_TREND` | 1:2.0 | $+35\text{ bps}$ |
| **HYP-08** | Volatility Breakout | 15m + 5m | 1h - 3h | Category B (2-6/day) | `LV_RANGE` $\to$ Trend | 1:2.5 | $+40\text{ bps}$ |
| **HYP-09** | Liquidity Sweep | 5m | 1h - 2h | Category B (3-8/day) | `HV_RANGE`, `LV_RANGE` | 1:1.7 | $+25\text{ bps}$ |
| **HYP-10** | Range Mean Reversion | 5m | 30m - 1.5h | Category A/B (5-12/day) | `LV_RANGE` | 1:1.5 | $+20\text{ bps}$ |
| **HYP-11** | Cross-Asset Momentum | 5m + 1h | 2h - 4h | Category B (1-4/day) | `HV_TREND` | 1:2.0 | $+35\text{ bps}$ |
| **HYP-12** | Multi-Factor Confluence | 5m + 15m + 1h | 2h - 4h | Category B (1-3/day) | Confluence | 1:2.5 | $+45\text{ bps}$ |
| **BASE-01** | Always Flat | N/A | 0 min | 0/day | ALL | N/A | $0.0\text{ bps}$ |
| **BASE-02** | Buy & Hold BTC | 5m | 3 years | $<0.01$/day | ALL | N/A | Variable |
| **BASE-03** | Simple Momentum (9/21) | 5m | 20m - 1h | Category A (>50/day) | Trending | 1:1.0 | $+5\text{ bps}$ |
| **BASE-04** | Simple Bollinger Reversion | 5m | 15m - 45m | Category A (>80/day) | Ranging | 1:1.0 | $+5\text{ bps}$ |

---

## 4. Key Strategic Insights

1. **Holding Period Determines Cost Feasibility:** Strategies with average holding times $< 30$ minutes (like BASE-03 and BASE-04) suffer fatal fee drag under retail taker models. Increasing expected holding horizons to 2–4 hours allows ATR targets to expand to 2.5–3.5 ATR ($\approx 50\text{ to } 100\text{ bps}$), giving the strategy sufficient margin to absorb friction.
2. **Regime Gating is Essential:** Mean reversion (`HYP-10`) must be strictly blocked in `HV_TREND` regimes where adverse trend runs cause severe drawdowns.
3. **Confluence Filter Reduces Fee Waste:** Unconstrained single-indicator triggers generate hundreds of low-quality trades. Multi-factor gating dramatically improves selectivity, lowering turnover and transaction cost drag.
