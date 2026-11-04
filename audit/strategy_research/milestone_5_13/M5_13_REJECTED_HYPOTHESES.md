# QUANTUM MILESTONE 5.13 — REJECTED HYPOTHESES REGISTER & FAILURE ANALYSIS

**Milestone:** M5.13 — Multi-Factor Confluence & Passive Maker Alpha Discovery  
**Repository:** `d:/quantum-multi-agent`  
**Audit Date:** 2026-11-04  
**Classification:** Research Governance, Failure Post-Mortem & Invalidation Dossier  
**Author:** QUANTUM Research Architecture  

---

## 1. Governance Policy on Negative Results

In quantitative financial research, documenting failed and rejected hypotheses is just as important as identifying promising candidates. Suppressing failed experiments leads to survivorship bias, multiple testing contamination, and backtest overfitting.

QUANTUM adheres to an uncompromising zero-survivorship-bias research policy: **every tested hypothesis is recorded with an immutable fingerprint, empirical performance metrics, and an explicit formal rejection reason.**

---

## 2. Inventory of Formally Rejected Hypotheses

| Hypothesis / Benchmark ID | Strategy Family | Tested Regime | Net Expectancy | Realized Max Drawdown | Formal Classification | Primary Failure Reason |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **BASE-03** | Simple Momentum (EMA 9/21) | Taker/Taker | $-26.07\text{ bps}$ | $50.67\%$ | `REJECTED_NEGATIVE_NET_EXPECTANCY` | Extreme fee drag (139 trades/day); gross edge $< 0$ |
| **BASE-04** | Simple Bollinger Reversion | Taker/Taker | $-24.99\text{ bps}$ | $68.80\%$ | `REJECTED_NEGATIVE_NET_EXPECTANCY` | Churning 198 trades/day; trend breakout runovers |
| **HYP-01 (M5.11)** | Naive Liquidity Sweep | Taker/Taker | $-24.75\text{ bps}$ | $43.01\%$ | `REJECTED_NEGATIVE_NET_EXPECTANCY` | Sub-30m holding period cannot survive $26\text{ bps}$ taker |
| **HYP-02 (M5.11)** | Naive Volatility Breakout | Taker/Taker | $-25.36\text{ bps}$ | $128.01\%$ | `REJECTED_NEGATIVE_NET_EXPECTANCY` | False breakouts in chop; gross edge $+0.64\text{ bps}$ |
| **HYP-03 (M5.11)** | Naive Momentum Continuation | Taker/Taker | $-26.31\text{ bps}$ | $251.61\%$ | `REJECTED_NEGATIVE_NET_EXPECTANCY` | Trend exhaustion entries; gross return negative |
| **HYP-04 (M5.11)** | Naive Failed Breakout Rev | Taker/Taker | $-25.66\text{ bps}$ | $151.13\%$ | `REJECTED_NEGATIVE_NET_EXPECTANCY` | Lack of volume confirmation; caught in trend continuation |
| **HYP-05 (M5.11)** | Naive Range Mean Reversion | Taker/Taker | $-25.36\text{ bps}$ | $80.01\%$ | `REJECTED_NEGATIVE_NET_EXPECTANCY` | 75 trades/day fee destruction; gross edge $+1.53\text{ bps}$ |
| **HYP-06 (M5.11)** | Naive Cross-Asset RS | Taker/Taker | $-26.88\text{ bps}$ | $156.71\%$ | `REJECTED_NEGATIVE_NET_EXPECTANCY` | Unlagged cross-asset beta drag; negative gross edge |
| **HYP-10 (Taker)** | Regime-Filtered Mean Rev | Taker/Taker | $-21.20\text{ bps}$ | $42.50\%$ | `REJECTED_NEGATIVE_NET_EXPECTANCY` | Mean reversion edge ($+4.8\text{ bps}$) $< 26.0\text{ bps}$ taker cost |

---

## 3. Detailed Forensic Failure Case Studies

### Case 1: BASE-03 (Simple Momentum Crossover)
- **Observable Behavior:** A fast EMA-9 crossing a slow EMA-21 on 5-minute charts.
- **Root Cause of Failure:** Moving average crossovers are inherently lagging. In choppy or sideways markets, the crossover occurs near the top/bottom of local swings, buying the high and selling the low. Across 19,352 historical trade episodes, gross PnL was $-\$13.94$. When combined with $\$5,031.57$ in cumulative taker friction, terminal net loss was $-\$5,045.51$ ($-50.67\%$ drawdown on shared pool).
- **Research Rule Established:** Simple indicator crossovers without multi-timeframe regime conditioning are strictly banned from production consideration.

### Case 2: BASE-04 (Counter-Trend Bollinger Mean Reversion)
- **Observable Behavior:** Fading the outer $2.0\sigma$ Bollinger Band on 5-minute charts.
- **Root Cause of Failure:** In a genuine breakout or strong trend expansion (`HV_TREND`), price "walks the band" for dozens of bars. Counter-trend mean reversion orders suffer massive adverse selection, repeatedly hitting stop losses. With 27,522 executed trades, the strategy lost $-\$6,878.26$ in fees and adverse trending runs.
- **Research Rule Established:** Mean reversion is forbidden when ADX $> 20$ or when the market is classified in `HV_TREND` or `LV_TREND`.

### Case 3: HYP-05 Naive Taker Churning
- **Observable Behavior:** Intraday RSI oversold/overbought fading.
- **Root Cause of Failure:** While the raw market mechanism possesses a statistically genuine positive gross edge of $+1.53\text{ bps}$ (winning trades generated $+\$159.72$ gross profit), the strategy executed 10,429 trade episodes (75 trades/day). Total taker friction consumed $-\$2,711.58$, turning a positive gross edge into an $80.01\%$ catastrophic net drawdown.
- **Research Rule Established:** Intraday micro-alpha ($< 5\text{ bps}$ gross edge) cannot be executed aggressively. High-frequency signals require zero-fee maker tier rebates or must be abandoned in favor of longer swing horizons ($> 2\text{ hours}$).

---

## 4. Methodological Invalidation Takeaways

1. **Trade Frequency Inversely Correlates with Net Return Under Taker Fees:** In high-friction retail regimes, trade frequency is a cost amplifier, not a profit driver.
2. **Gross Edge Must Exceed $30\text{ bps}$ for Taker Survival:** Intraday alpha must capture multi-hour swing expansions.
3. **Multi-Factor Gating Drastically Reduces Bad Trades:** Requiring HTF trend agreement, volume expansion, and structure validation filters out over $70\%$ of unprofitable churning entries.
