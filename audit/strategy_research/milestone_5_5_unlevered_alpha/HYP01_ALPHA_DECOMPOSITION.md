# QUANTUM — HYP-01 ALPHA DECOMPOSITION DOSSIER
## Comprehensive Microstructure, Signal, Lifecycle, and Profit Concentration Audit

**Document Identifier:** `audit/strategy_research/milestone_5_5_unlevered_alpha/HYP01_ALPHA_DECOMPOSITION.md`  
**Publication Timestamp:** 2026-11-03 21:24:00 UTC  
**Active Branch:** `research/quantum-next-3pct`  
**Evaluated Baseline System:** `HYP-01` (EXP-08 Optimal Candidate Architecture)  
**Lead Quantitative Research Auditor:** Senior Quantitative Research Auditor & Alpha Diagnostic Specialist  
**Phase Objective:** Identify Exact Alpha Drivers and Structural Bottlenecks of HYP-01  

---

## 1. Executive Summary & Diagnostic Findings

Before engineering new alpha mechanisms in Milestone 5.5, a complete forensic decomposition of `HYP-01` was executed across all 28,043 trades and 1,099 calendar days.

### Top 5 Empirical Takeaways:
1. **The Time-Expiration Bleed (The #1 Structural Drag):**
   **$63.06\%$ of all trades (17,683 trades)** fail to hit TP1 or SL and exit at bar 4 via `TIME_EXPIRATION` as market takers, averaging **$-11.46\text{ bps}$ net loss**. Eliminating or improving this stagnant trade cohort is the single largest opportunity to lift net expectancy.
2. **Velocity of Edge (Fast Trades Dominate):**
   Trades resolving within 1 to 3 bars exhibit extraordinary profitability:
   - **1 Bar (5m):** $89.42\%$ win rate, **$+83.63\text{ bps}$ net expectancy**, profit factor $17.50$.
   - **2 Bars (10m):** $65.08\%$ win rate, **$+33.86\text{ bps}$ net expectancy**, profit factor $2.03$.
   - **3 Bars (15m):** $63.77\%$ win rate, **$+28.70\text{ bps}$ net expectancy**, profit factor $1.47$.
   - **4 Bars (20m):** $45.95\%$ win rate, **$+0.21\text{ bps}$ net expectancy**, profit factor $0.86$.
3. **Macro Regime Asymmetry (High-Vol Bear Clears 3% Gate):**
   - **High-Vol Bear (277 days):** **$+3.0945\%$ mean daily return**, $+13.43\text{ bps}$ net expectancy. The mandatory $3.00\%$ gate is already achieved in this quadrant.
   - **Low-Vol Bear (265 days):** $+0.9961\%$ mean daily return, $+5.66\text{ bps}$ net expectancy. Low-volatility drag depresses the overall multi-year average.
4. **Asset Alpha Breadth & Altcoin Concentration:**
   9 out of 10 primary perpetuals produce positive net PnL. ADA, AVAX, and DOGE account for **$63.36\%$ of total portfolio net dollar profit**, while BNB is slightly net negative (profit factor $0.925$).
5. **Profit Concentration Integrity:**
   The 5% trimmed mean daily return is **$+1.2925\%$**, and excluding the top 1% days yields **$+1.6472\%$ daily**. The alpha is not driven by single-day black swan flukes; it represents a genuine, recurring statistical edge across the entire 1,099-day sample.

---

## 2. Section A: Asset Attribution Matrix

```
+-----------------------------------------------------------------------------------------------------------------------------------------+
| Asset Symbol | Executed Trades | Win Rate % | Net Exp (bps) | Gross Exp (bps) | Profit Factor | Net PnL ($)     | Contribution % | MFE / MAE (bps) |
+-----------------------------------------------------------------------------------------------------------------------------------------+
| ADAUSDT      | 3,855           | 51.65%     | +10.16 bps    | +24.73 bps      | 1.611         | $6.98 Billion   | 30.89%         | +70.6 / -26.2   |
| AVAXUSDT     | 2,780           | 52.77%     | +11.51 bps    | +26.06 bps      | 1.429         | $4.57 Billion   | 20.20%         | +68.7 / -23.1   |
| DOGEUSDT     | 3,694           | 52.65%     | +12.94 bps    | +27.41 bps      | 1.364         | $2.77 Billion   | 12.27%         | +74.9 / -24.6   |
| LINKUSDT     | 2,785           | 51.31%     | +9.38 bps     | +23.93 bps      | 1.220         | $1.96 Billion   | 8.69%          | +66.7 / -24.3   |
| ETHUSDT      | 2,898           | 50.69%     | +8.28 bps     | +22.72 bps      | 1.408         | $1.97 Billion   | 8.71%          | +63.0 / -19.1   |
| SOLUSDT      | 4,172           | 51.61%     | +9.48 bps     | +23.99 bps      | 1.261         | $1.93 Billion   | 8.55%          | +66.7 / -22.7   |
| XRPUSDT      | 2,589           | 48.13%     | +7.25 bps     | +21.79 bps      | 1.150         | $1.13 Billion   | 4.99%          | +66.9 / -23.4   |
| BTCUSDT      | 1,527           | 49.90%     | +6.47 bps     | +20.90 bps      | 1.415         | $0.92 Billion   | 4.08%          | +56.4 / -17.5   |
| LTCUSDT      | 2,097           | 49.59%     | +9.18 bps     | +23.76 bps      | 1.092         | $0.55 Billion   | 2.44%          | +65.8 / -23.9   |
| BNBUSDT      | 1,646           | 51.82%     | +8.64 bps     | +23.08 bps      | 0.925         | -$0.19 Billion  | -0.82%         | +59.3 / -18.4   |
+-----------------------------------------------------------------------------------------------------------------------------------------+
```

### Key Asset Insights:
- **Top Alpha Drivers:** ADA, AVAX, and DOGE produce the largest favorable excursions (MFE $+68.7\text{ to }+74.9\text{ bps}$) due to high retail momentum participation during breakouts.
- **BNB Lag:** BNB exhibits tight intraday ranges with lower breakout follow-through, causing higher time-expiration churn.

---

## 3. Section B: Market Regime Attribution Matrix

Classified point-in-time using BTC daily close-to-open return and trailing 20-bar volatility ($\sigma_{\text{median}} = 0.00284$):

```
+-------------------------------------------------------------------------------------------------------------------+
| Macro Regime   | Calendar Days | Trades Count | Win Rate % | Net Exp (bps) | Profit Factor | Mean Daily Return %  |
+-------------------------------------------------------------------------------------------------------------------+
| HIGH_VOL_BEAR  | 277 days      | 8,230        | 52.92%     | +13.43 bps    | 1.473         | +3.0945% / day       |
| HIGH_VOL_BULL  | 273 days      | 7,564        | 52.12%     | +10.83 bps    | 1.399         | +2.2257% / day       |
| LOW_VOL_BULL   | 284 days      | 6,339        | 50.24%     | +7.09 bps     | 1.505         | +1.2064% / day       |
| LOW_VOL_BEAR   | 265 days      | 5,904        | 48.61%     | +5.66 bps     | 1.078         | +0.9961% / day       |
+-------------------------------------------------------------------------------------------------------------------+
```

### Regime Takeaways:
- **The Engine of 3%:** High-Vol Bear is the only market condition currently producing $\ge 3.00\%$ net daily return. Fast downward momentum triggers clean liquidity expansions and strong continuation.
- **The Drag of Low Vol:** Low-volatility days represent $49.9\%$ of the calendar and produce only $+0.99\%\text{ to }+1.21\%$ daily.

---

## 4. Section C: Signal Attribution & Directional Bias

```
+-------------------------------------------------------------------------------------------------------------------+
| Direction | Trades Count | Win Rate % | Net Exp (bps) | Gross Exp (bps) | Profit Factor | MFE Mean   | MAE Mean   |
+-------------------------------------------------------------------------------------------------------------------+
| LONG      | 14,099       | 51.77%     | +10.08 bps    | +24.62 bps      | 1.448         | +64.86 bps | -22.38 bps |
| SHORT     | 13,944       | 50.60%     | +9.22 bps     | +23.71 bps      | 1.211         | +69.32 bps | -23.35 bps |
+-------------------------------------------------------------------------------------------------------------------+
```

### Signal Insights:
- The strategy executes an almost perfectly balanced directional split: $50.3\%$ Long vs $49.7\%$ Short.
- Short trades experience larger maximum favorable excursions (MFE $+69.32\text{ bps}$ vs $+64.86\text{ bps}$), but higher volatility pullbacks reduce their profit factor slightly to $1.211$.

---

## 5. Section D: Trade Lifecycle & Execution Exit Autopsy

```
+-----------------------------------------------------------------------------------------------------------------------------+
| Exit Reason              | Trades Count | % of Trades | Win Rate % | Net Exp (bps) | Profit Factor | MFE (bps)  | MAE (bps) |
+-----------------------------------------------------------------------------------------------------------------------------+
| TAKE_PROFIT_2 (Maker)    | 3,894        | 13.89%      | 100.0%     | +108.39 bps   | inf           | +170.48    | -1.92     |
| TAKE_PROFIT_1_HORIZON    | 2,870        | 10.23%      | 98.08%     | +63.76 bps    | 288.60        | +103.69    | -3.95     |
| STOP_LOSS (Taker)        | 3,596        | 12.82%      | 34.34%     | -36.62 bps    | 0.169         | +60.67     | -54.26    |
| TIME_EXPIRATION (Taker)  | 17,683       | 63.06%      | 36.26%     | -11.46 bps    | 0.382         | +39.67     | -24.16    |
+-----------------------------------------------------------------------------------------------------------------------------+
```

### Breakdown by Holding Duration:
```
+-----------------------------------------------------------------------------------------------------------------------------+
| Holding Duration         | Trades Count | % of Trades | Win Rate % | Net Exp (bps) | Profit Factor | MFE (bps)  | MAE (bps) |
+-----------------------------------------------------------------------------------------------------------------------------+
| 1 Bar (5 minutes)        | 1,702        | 6.07%       | 89.42%     | +83.63 bps    | 17.50         | +167.66    | -10.83    |
| 2 Bars (10 minutes)      | 2,016        | 7.19%       | 65.08%     | +33.86 bps    | 2.03          | +110.09    | -28.10    |
| 3 Bars (15 minutes)      | 1,932        | 6.89%       | 63.77%     | +28.70 bps    | 1.47          | +104.18    | -29.86    |
| 4 Bars (20 minutes)      | 22,393       | 79.85%      | 45.95%     | +0.21 bps     | 0.86          | +52.36     | -22.71    |
+-----------------------------------------------------------------------------------------------------------------------------+
```

### Crucial Architectural Insight:
- **Immediate Follow-Through vs Stagnation:** When a momentum expansion is genuine, it explodes immediately into TP1 or TP2 within 1–3 bars.
- When price does not follow through by bar 2, the trade enters chop. Lingering until bar 4 and exiting as a market taker costs $6.5\text{ bps}$ in taker exit fees, turning borderline trades into $-11.46\text{ bps}$ losers.

---

## 6. Section E: Profit Concentration & Outlier Dependency

```
+---------------------------------------------------------------------------------------------------------+
| Concentration Metric                     | Metric Value | Quantitative Interpretation                   |
+---------------------------------------------------------------------------------------------------------+
| Full Sample Mean Net Daily Return        | +1.8848%     | Full 1,099 calendar days baseline             |
| Top 1% Days Cutoff Return                | +24.8194%    | Threshold defining the top 10 most profitable |
| Mean Return Excluding Top 1% Days        | +1.6472%     | Mean when top 10 outlier days are removed     |
| Top 5% Days Cutoff Return                | +11.7439%    | Threshold defining the top 54 most profitable |
| Mean Return Excluding Top 5% Days        | +1.0289%     | Mean when top 54 outlier days are removed     |
| Bottom 5% Days Cutoff Loss               | -3.2439%     | Threshold defining the worst 54 drawdown days |
| Mean Return Excluding Bottom 5% Days     | +2.1790%     | Mean when worst 54 drawdown days are removed  |
| 5% Symmetrically Trimmed Mean Return     | +1.2925%     | Central core alpha excluding both tails (90%) |
+---------------------------------------------------------------------------------------------------------+
```

### Outlier Diagnosis:
- Even when the top 5% of all calendar days are completely stripped away, `HYP-01` still generates a positive mean net daily return of **$+1.0289\%$**.
- The strategy's edge is **not a tail-event illusion**. However, the top 5% days (extreme volatility expansion events) are essential for elevating daily return toward institutional levels.

---

## 7. Conclusions & Strategic Action Plan for Milestone 5.5

Based on this decomposition, our engineering efforts in Phase C (EXP-09, EXP-10, EXP-11) will focus on:
1. **EXP-09 (Regime-Adaptive Alpha):**
   - In Low-Volatility regimes, increase entry threshold ($\text{vol\_exp} \ge 1.15$, trend $\ge 100\text{ bps}$) to eliminate stagnant trades.
   - In High-Volatility regimes, deploy full 1.0x unlevered allocation.
2. **EXP-10 (Execution-Aware Optimization):**
   - Address the 17,683 time-expiration exits: replace market taker time stops with passive limit maker exits at mid/bid to save $4.5\text{ bps}$ per exit.
3. **EXP-11 (Structural Alpha):**
   - Target fast 1-to-2 bar impulse continuation signals that resolve with high MFE before decay sets in.
