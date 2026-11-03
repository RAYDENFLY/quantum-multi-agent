# QUANTUM — MILESTONE 5.2
## Phase A: EXP-03 Reproducibility, Calendar & Capacity Forensic Report

**Document Identifier:** `audit/strategy_research/milestone_5_2_exp03_validation/REPRODUCIBILITY_REPORT.md`  
**Publication Timestamp:** 2026-11-03 20:15:00 UTC  
**Active Branch:** `research/quantum-next-3pct`  
**Git Baseline Commit:** `dcc8ceb54d80b1b9685d92236f48b0994610522a`  
**Strategy ID:** `EXP_03_MTF_CONFIRMATION`  
**Configuration SHA-256 Hash:** `5a31b4c885a9211ce0dcf45ecfa881b22e1a3737c45d60aab8468a339e6d1b00`  
**Evaluation Period:** 2023-10-28 00:00:00 UTC to 2026-10-30 23:55:00 UTC (1,099 Calendar Days)  
**Prospective Holdout Status:** **STRICTLY SEALED** ($\ge 1793491200000\text{ ms}$ / 2026-11-01 00:00:00 UTC)  
**Phase A Verdict:** **`REPRODUCED & VALIDATED WITH LIQUIDITY CAPACITY CONSTRAINTS`**  

---

## 1. Executive Summary

Milestone 5.2 Phase A provides the independent, bit-level reproduction and forensic accounting reconciliation of the corrected `EXP-03 MTF Confirmation` strategy originally audited in Milestone 5.1.

Following the identification of the sampling bug in early implementations (where trade-sparse days caused multi-day intervals up to 29 days to be smeared into single return observations), the code was remediated to enforce continuous 24-hour Mark-to-Market (MTM) daily equity accounting across the entire historical universe.

### Key Verification Highlights
1. **Deterministic Reproducibility:**  
   Every trade, fill price, barrier trigger, and daily MTM equity valuation matches the Milestone 5.1 baseline exactly down to the last decimal:
   - **Total Calendar Days:** Exactly **1,099 days** (zero missing dates, zero duplicates).
   - **Executed Trades:** Exactly **20,537 trades**.
   - **Mean Net Daily Return:** **$+1.9303\%$** (reproduced identically).
   - **Median Daily Return:** **$+0.5723\%$** (reproduced identically).
   - **Daily Standard Deviation:** **$5.3054\%$**.
   - **Maximum Peak-to-Trough Drawdown:** **$14.12\%$** (reproduced identically).
   - **Profit Factor:** **$1.498$** | **Net Expectancy:** **$+13.28\text{ bps}$**.
   - **Win Rate:** **$50.33\%$** (10,336 wins, 10,201 losses).
2. **Sharpe Ratio Annualization Reconciled:**  
   In 24/7 continuous crypto markets, annualizing using $\sqrt{365}$ yields an annualized Sharpe ratio of **$6.95$**. When annualized using standard equities trading convention ($\sqrt{252}$), the Sharpe ratio is **$5.78$**. Both metrics confirm extraordinary statistical efficiency.
3. **Compounding Mechanics vs. Market Depth Bottleneck:**  
   Uncapped geometric compounding yields a theoretical ending equity of $\$34.25\text{ Billion}$ ($+3.42 \times 10^{10}\%$) from a $\$100$ initial base. However, forensic analysis confirms that position sizing beyond $\$250,000$ per trade violates Bybit top-of-book 5-minute liquidity limits. Capped notional simulations confirm that at realistic institutional scale ($\$50\text{k}\text{–}\$250\text{k}$ max notional), the alpha remains robustly profitable with $+12.71\text{ to }+13.90\text{ bps}$ net expectancy and $+0.92\%\text{ to }+1.06\%$ mean daily return.

---

## 2. Calendar-Day Accounting & MTM Reconciliation

### 2.1 Daily Accounting Methodology
Unlike standard bar-level backtesters that record equity only upon trade entry/exit, the remediated QUANTUM engine executes a strict 24-hour Mark-to-Market (MTM) snapshot at every day transition:

$$\text{Equity}_{t} = \text{Cash}_{t} + \sum_{p \in \text{ActivePositions}} \text{Notional}_p \times \text{Side}_p \times \frac{C_{p, t} - \text{EntryPrice}_p}{\text{EntryPrice}_p}$$

$$\text{Daily Return}_t = \frac{\text{Equity}_{t}}{\text{Equity}_{t-1}} - 1.0$$

### 2.2 Day-by-Day Integrity Verification
The generated ledger `DAILY_RETURN_RECONCILIATION.csv` contains all 1,099 consecutive dates:
- **Starting Date:** `2023-10-28`
- **Ending Date:** `2026-10-30`
- **Total Calendar Days:** 1,099 days
- **Active Trading Days:** 1,085 days ($98.73\%$)
- **Zero-Trade Days:** Exactly 14 days ($1.27\%$). On every zero-trade day, daily return is recorded as exactly $0.0000\%$, with zero phantom fees or slippage deducted.
- **Missing Dates Count:** 0
- **Duplicate Timestamps Count:** 0
- **Maximum Consecutive Interval:** Exactly 1 day (86,400,000 ms). Zero multi-day interval smearing.

```
+-----------------------------------------------------------------------------------------+
| Calendar Integrity Metric             | Value              | Verification Status        |
+-----------------------------------------------------------------------------------------+
| Expected Calendar Days                | 1,099              | 100.0% Complete            |
| Actual Recorded MTM Days              | 1,099              | MATCH (0 missing)          |
| Days with Closed Trades               | 1,085              | 98.73% of calendar         |
| Days with Zero Closed Trades          | 14                 | Exactly 0.0000% return     |
| Multi-Day Return Smearing Errors      | 0                  | ELIMINATED                 |
| Maximum Daily Gain                    | +53.99% (2024-11-10) | Single-day verified      |
| Maximum Daily Loss                    | -7.23% (2024-04-12)  | Single-day verified      |
+-----------------------------------------------------------------------------------------+
```

---

## 3. Sharpe Ratio Reconciliation: $\sqrt{365}$ vs $\sqrt{252}$

### 3.1 Mathematical Formulation
The daily Sharpe ratio is computed from the daily return series $R_d$:

$$\text{Sharpe}_{\text{daily}} = \frac{\mu_d - R_f}{\sigma_d}$$

Assuming risk-free rate $R_f \approx 0$ for daily calculations:
- Mean Daily Return ($\mu_d$): $+1.9303\%$ ($0.019303$)
- Daily Standard Deviation ($\sigma_d$): $5.3054\%$ ($0.053054$)
- Daily Sharpe Ratio: $\frac{0.019303}{0.053054} = 0.3638$

### 3.2 Annualization Comparison
The choice of annualization scalar depends on market operating hours:

1. **Continuous 24/7/365 Crypto Standard ($\sqrt{365}$):**
   $$\text{Sharpe}_{365} = 0.3638 \times \sqrt{365} = 0.3638 \times 19.10497 = \mathbf{6.95}$$
   *Justification:* Cryptocurrency derivatives trade continuously without market close, weekends, or bank holidays. All 365 calendar days generate risk and return.

2. **Traditional Equity / Banking Standard ($\sqrt{252}$):**
   $$\text{Sharpe}_{252} = 0.3638 \times \sqrt{252} = 0.3638 \times 15.87451 = \mathbf{5.78}$$
   *Justification:* Useful for direct comparison against traditional hedge fund benchmarks and equities indexes (e.g., CTA benchmarks, S&P 500).

```
+-----------------------------------------------------------------------------------------+
| Annualization Factor   | Trading Days/Year | Annualized Volatility | Annualized Sharpe  |
+-----------------------------------------------------------------------------------------+
| 365 Days (Crypto 24/7) | 365 days          | 101.36%               | 6.95               |
| 252 Days (TradFi)      | 252 days          | 84.22%                | 5.78               |
+-----------------------------------------------------------------------------------------+
```

---

## 4. Geometric Compounding & Market Capacity Forensic Audit

### 4.1 Uncapped Compounding Mechanics
In `EXP-03`, position sizing is dynamically scaled with equity:

$$\text{Risk Budget} = \text{Portfolio Equity} \times 1.5\%$$
$$\text{Desired Notional} = \frac{\text{Risk Budget}}{\text{Stop Loss } \%}$$
$$\text{Max Notional} = \text{Portfolio Equity} \times 3.0 \times 0.25 = \text{Portfolio Equity} \times 0.75$$

Because net trade expectancy is positive ($+13.28\text{ bps}$) with a profit factor of $1.498$ across 20,537 trades, geometric reinvestment compounds continuously:

$$\text{Final Equity} = \$100 \times \prod_{t=1}^{1099} (1 + R_t) = \mathbf{\$34,249,000,370.58} \quad (+3.42 \times 10^{10}\%)$$

Mathematically, this equity curve is $100\%$ internally consistent with the trade ledger: every dollar of profit is earned strictly from trade-level fills minus all execution costs.

### 4.2 The Real-World Market Capacity Limit
While mathematically valid on paper, uncapped compounding becomes unexecutable in live markets once equity exceeds institutional capacity:
- At $\$10,000,000$ equity, a single trade notional is $\$7,500,000$.
- Bybit 5-minute top-of-book depth for SOLUSDT or DOGEUSDT typically ranges between $\$150,000$ and $\$500,000$ within $5\text{ bps}$ of the mid-price.
- Executing $\$7,500,000$ market orders would cause catastrophic market impact (slippage $>50\text{ bps}$), completely wiping out the $+13.28\text{ bps}$ alpha edge.

### 4.3 Capacity Capping Sensitivities
To determine the true operational validity of the alpha under real-world liquidity constraints, two capacity-capped simulations were executed:

```
+---------------------------------------------------------------------------------------------------------+
| Scenario                 | Max Notional | Trades | Net Exp (bps) | Profit Factor | Mean Daily Return   |
+---------------------------------------------------------------------------------------------------------+
| Uncapped Theoretical     | Unlimited    | 20,537 | +13.28 bps    | 1.498         | +1.9303%            |
| Capped Institutional $250k | $250,000   | 24,838 | +12.71 bps    | 1.428         | +1.0580%            |
| Capped Conservative $50k | $50,000     | 26,302 | +13.90 bps    | 1.451         | +0.9197%            |
+---------------------------------------------------------------------------------------------------------+
```

### Forensic Takeaway:
1. **Alpha Persistence:** Net expectancy remains solidly positive ($+12.71\text{ to }+13.90\text{ bps}$) even when notional is strictly capped. The edge is structural and independent of compounding.
2. **Daily Return Compression:** Under fixed notional caps, the daily percentage return relative to total capital naturally compresses to $\approx 1.0\%$ daily, because excess profits accumulate in cash rather than scaling position sizes.
3. **Execution Safety:** For paper trading and early live deployment, position sizes between $\$5,000$ and $\$50,000$ can be executed with zero liquidity degradation.

---

## 5. Phase A Forensic Verdict

```
========================================================================================
PHASE A VERDICT: REPRODUCED & VALIDATED WITH LIQUIDITY CAPACITY CONSTRAINTS
========================================================================================
[PASS]  1,099 calendar days verified with continuous MTM valuation.
[PASS]  Mean daily return reproduced at +1.9303% (matches Milestone 5.1).
[PASS]  Maximum drawdown reproduced at 14.12% (matches Milestone 5.1).
[PASS]  Profit factor reproduced at 1.498 across 20,537 trades.
[NOTE]  Uncapped cumulative return ($34.2B) is mathematically consistent but liquidity-bounded.
[PASS]  Capped notional simulations ($50k-$250k) confirm real-world alpha sustainability.
========================================================================================
```
