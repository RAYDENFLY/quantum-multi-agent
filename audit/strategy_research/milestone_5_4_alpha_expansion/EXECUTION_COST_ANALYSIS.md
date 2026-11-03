# QUANTUM — EXECUTION COST & MICROSTRUCTURE FRICTION AUDIT
## Mathematical Breakdown of Venue Frictions Across HYP-01, HYP-02, and HYP-03

**Document Identifier:** `audit/strategy_research/milestone_5_4_alpha_expansion/EXECUTION_COST_ANALYSIS.md`  
**Publication Timestamp:** 2026-11-03 21:10:00 UTC  
**Active Branch:** `research/quantum-next-3pct`  
**Execution Venue Schedule:** Bybit Perpetual (VIP0 Standard Tier)  
**Lead Quantitative Research Auditor:** Execution Specialist & Market Microstructure Modeler  

---

## 1. Executive Summary & Microstructure Diagnosis

A foundational principle of the QUANTUM research framework is that an alpha signal cannot be evaluated in isolation from its execution friction. 

In Milestone 5.4, we evaluated three distinct strategy archetypes across 1,099 calendar days:
1. **HYP-01:** Multi-Timeframe Volatility Expansion Trend Following (Directional Momentum).
2. **HYP-02:** Liquidity Sweep & Structural Reclaim (Counter-Breakout Fading).
3. **HYP-03:** Statistical Mean Reversion in Low-Volatility Regimes (Z-Score Displacement Fading).

The central finding of this audit is that **all three strategies possess genuine predictive alpha** before fees (positive gross trade expectancy across thousands of trades), but their **net realizable alpha diverges sharply** due to the interaction between average trade excursion size and fixed exchange frictions.

---

## 2. Institutional Venue Fee Schedule (Bybit VIP0 Perpetual)

The simulation engine implements the precise fee, spread, slippage, and funding rate schedule of Bybit USDT Perpetuals under VIP0 retail/unprivileged status:

```
+---------------------------------------------------------------------------------------------------------+
| Friction Component          | Order Role  | Fee Rate (bps) | Spread Penalty | Slippage Model | Total Leg Cost |
+---------------------------------------------------------------------------------------------------------+
| Entry Order (Market Taker)  | TAKER       | 5.0 bps        | 2.0 bps        | 1.5 bps        | 8.5 bps        |
| TP Exit (Limit Maker)       | MAKER       | 2.0 bps        | 0.0 bps        | 1.5 bps        | 3.5 bps        |
| SL / Time Exit (Stop Market)| TAKER       | 5.0 bps        | 0.0 bps        | 1.5 bps        | 6.5 bps        |
| Funding Accrual Rate        | PASSIVE     | 1.0 bps / 8h   | N/A            | N/A            | Scaled by time |
+---------------------------------------------------------------------------------------------------------+
```

### Cumulative Round-Trip Friction Profiles:
- **Winning Path (Taker Entry $\rightarrow$ Maker TP Exit):**
  $$\text{Friction}_{\text{win}} = 8.5\text{ bps (entry)} + 3.5\text{ bps (exit)} = \mathbf{12.0\text{ bps}}$$
- **Losing / Time-Expiration Path (Taker Entry $\rightarrow$ Taker SL/Time Exit):**
  $$\text{Friction}_{\text{loss}} = 8.5\text{ bps (entry)} + 6.5\text{ bps (exit)} = \mathbf{15.0\text{ bps}}$$
- **Average Empirical Cost Across Universe:** **$13.80\text{ to }14.50\text{ bps per trade}$**.

---

## 3. Comparative Strategy Friction & Alpha Retention Analysis

```
+-------------------------------------------------------------------------------------------------------------------+
| Metric                        | HYP-01 (Trend)       | HYP-02 (Sweep)       | HYP-03 (Mean Reversion)             |
+-------------------------------------------------------------------------------------------------------------------+
| Total Executed Trades         | 24,480 trades        | 3,076 trades         | 10,145 trades                       |
| Gross Trade Expectancy        | +27.57 bps           | +12.82 bps           | +8.56 bps                           |
| Average Friction Drag         | 14.50 bps            | 14.02 bps            | 13.62 bps                           |
| Net Trade Expectancy          | +13.07 bps           | -1.20 bps            | -5.06 bps                           |
| Alpha Friction Ratio (Cost/Gross)| 52.6%             | 109.4%               | 159.1%                              |
| Realized Net Profit Factor    | 1.495                | 0.972                | 0.597                               |
| Dominant Exit Reason          | TP1 / TP2 (Maker)    | Time Stop / SL (Taker)| Time Stop / SL (Taker)             |
| Realized Net Daily Return     | +2.2741%             | -0.0086%             | -0.1822%                            |
+-------------------------------------------------------------------------------------------------------------------+
```

---

## 4. Forensic Microstructure Takeaways

### 4.1 Why HYP-01 Retains Alpha While HYP-02 and HYP-03 Degrade:
1. **Excursion Magnitude vs Friction Hurdle:**
   - In `HYP-01`, entries trigger exclusively during **high-volatility momentum expansions**. The average winning excursion is $+70\text{ to }+120\text{ bps}$. Even after paying $12.0\text{ bps}$ in round-trip friction, a net profit of $+58\text{ to }+108\text{ bps}$ remains. The gross alpha ($+27.57\text{ bps}$) is large enough to absorb the $14.50\text{ bps}$ friction hurdle and leave $+13.07\text{ bps}$ net edge.
2. **The Low-Volatility Micro-Move Trap in HYP-03:**
   - In `HYP-03`, trades are taken during **low-volatility ranging regimes** where 5m candle standard deviation is only $8\text{ to }12\text{ bps}$ ($\sigma = 0.0008\text{–}0.0012$).
   - A $2.0\sigma$ price displacement is only $16\text{ to }24\text{ bps}$ in total distance.
   - When the target move is only $20\text{ bps}$ and execution costs $14\text{ bps}$, **friction consumes $70\%$ of the entire theoretical excursion**.
   - If the trade fails to snap back within 8 bars and exits via time expiration as a taker, the loss of $15\text{ bps}$ friction plus price drift produces a negative net expectancy ($-5.06\text{ bps}$), despite positive gross predictive power ($+8.56\text{ bps}$).
3. **Premature Time Stops in HYP-02:**
   - In `HYP-02`, liquidity sweeps often experience a multi-candle consolidation or re-test before the counter-expansion takes flight. A short horizon of 6 bars forced $36.7\%$ of trades to liquidate via market taker time expiration, paying $6.5\text{ bps}$ taker exit costs before the move could materialize.

---

## 5. Architectural Recommendations for Next Research Milestones

1. **Maker-Only Passive Entry Optimization:**
   If `HYP-02` and `HYP-03` utilize post-only limit orders placed at the bid/ask (saving $5.0\text{ bps}$ taker fee and $2.0\text{ bps}$ spread = $7.0\text{ bps}$ per entry), `HYP-02` net expectancy immediately flips from $-1.20\text{ bps}$ to **$+5.80\text{ bps}$**, making it an accretive diversification asset.
2. **Adaptive Horizon Scaling:**
   Holding horizon must scale inversely with volatility: when volatility is compressed, holding times must expand to allow price to travel across the spread.
3. **Portfolio Exclusion Gate:**
   Under current VIP0 taker fee schedules, `HYP-03` is net destructive to portfolio capital when executed as a standalone taker strategy. It must not be allocated independent capital without passive limit execution.
