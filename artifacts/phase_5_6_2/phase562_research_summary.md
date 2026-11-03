# QUANTUM Phase 5.6.2 Experimental Research Summary Report

**Document Identifier:** `artifacts/phase_5_6_2/phase562_research_summary.md`  
**Execution Timestamp:** 2026-11-02T19:08:25Z  
**Git Commit:** `dcc8ceb54d80b1b9685d92236f48b0994610522a`  
**Author:** Antigravity AI Engine (on behalf of Project Owner Azis Maulana Suhada)  
**Governance Scope:** Research Execution on Historical Folds 1–4 (Prospective Holdout $\ge 1793491200000\text{ ms}$ Strictly Sealed)

---

## Executive Summary & Goal Assessment

### Outcome Classification: `NOT ACHIEVABLE UNDER CURRENT CONSTRAINTS`

The Phase 5.6.2 experimental program successfully solved the **frequency target** ($\approx 600$ trades/asset/year achieved across all 10 assets; 5,781 total portfolio trades), but definitively established that **+3% net portfolio equity return per day** and **sub-10% average underwater drawdown** cannot be achieved under the frozen Phase 5.3 5-minute LightGBM models, bidirectional execution, and the DEC_05 Option 3 30% gross exposure cap.

| Research Target | Mandate Objective | Observed Result (Maker 8 bps) | Observed Result (Hybrid 15 bps) | Observed Result (Taker 44 bps) | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Net Daily Portfolio Return** | **$+3.00\%$ / day** | **$-0.0987\%$ / day** | **$-0.1847\%$ / day** | **$-0.5385\%$ / day** | **FAILED** |
| **Trade Frequency (Per Asset)** | $\mathbf{\approx 600\text{ trades/yr}}$ | **$550 - 644\text{ trades/yr}$** | **$550 - 644\text{ trades/yr}$** | **$550 - 644\text{ trades/yr}$** | **ACHIEVED** |
| **Portfolio Aggregate Frequency**| $\mathbf{\approx 6,000\text{ trades/yr}}$ | **$5,781\text{ candidate / } 4,525\text{ executed}$** | **$5,781 / 4,525$** | **$5,781 / 4,524$** | **ACHIEVED** |
| **Average Underwater Drawdown** | **$< 10.0\%$** | **$14.02\%$** | **$25.67\%$** | **$55.82\%$** | **FAILED** |
| **Maximum Portfolio Drawdown** | **$\le 30.0\%$** | **$30.71\%$** | **$49.52\%$** | **$86.41\%$** | **FAILED** |
| **Net Realized Expectancy** | **$> 0.0\text{ bps}$** | **$-6.11\text{ bps}$** | **$-13.11\text{ bps}$** | **$-42.11\text{ bps}$** | **FAILED** |
| **Portfolio Profit Factor** | **$\ge 1.20$** | **$0.887$** | **$0.773$** | **$0.433$** | **FAILED** |

---

## 1. Stage 1: Frequency Calibration Results

By replacing uniform basis-point volatility floors with asset-specific empirical quantiles ($q \in [0.90, 0.95]$) and directional probability margins ($\theta \in [0.15, 0.30]$), every asset in the 10-asset primary universe landed within the $[500, 750]$ trades/year target band:

| Asset | Calibrated $q_{\text{vol}}$ | Calibrated $\theta_{\text{margin}}$ | Completed Trades/Yr | Gross Win Rate (%) | Gross Expectancy (bps) | Net Expectancy (8 bps) | Profit Factor (Maker) | Band Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **BTCUSDT** | 0.90 | 0.25 | 570 | 28.6% | +0.07 | -7.98 | 0.731 | `IN_BAND` |
| **ETHUSDT** | 0.95 | 0.20 | 568 | 30.8% | +0.85 | -7.21 | 0.840 | `IN_BAND` |
| **BNBUSDT** | 0.95 | 0.30 | 550 | 28.5% | -2.37 | -10.43 | 0.738 | `IN_BAND` |
| **XRPUSDT** | 0.95 | 0.15 | 595 | 29.6% | +0.17 | -7.90 | 0.886 | `IN_BAND` |
| **ADAUSDT** | 0.95 | 0.20 | 615 | 30.4% | +1.14 | -6.93 | 0.893 | `IN_BAND` |
| **SOLUSDT** | 0.92 | 0.25 | 558 | 29.6% | +1.47 | -6.60 | 0.870 | `IN_BAND` |
| **AVAXUSDT**| 0.92 | 0.30 | 629 | 30.2% | +2.89 | -5.18 | 0.907 | `IN_BAND` |
| **LINKUSDT**| 0.92 | 0.25 | 644 | 30.9% | +5.67 | -2.43 | 0.957 | `IN_BAND` |
| **DOGEUSDT**| 0.90 | 0.30 | 598 | 30.9% | +5.46 | -2.60 | 0.951 | `IN_BAND` |
| **LTCUSDT** | 0.95 | 0.25 | 627 | 30.0% | -0.61 | -8.70 | 0.867 | `IN_BAND` |
| **Aggregate**| — | — | **5,781** | **29.9%** | **+1.89** | **-6.11** | **0.887** | `IN_BAND` |

---

## 2. Stage 2: Signal Ranking & Directional Asymmetry Discovery

Stage 2 revealed that predictive skill is **heavily directionally asymmetric**. Long signals show positive gross expectancy on 8 out of 10 assets, with 3 assets generating positive *net* expectancy after fees:

| Asset | BOTH Trades | BOTH Net (bps) | LONG Trades | LONG Gross (bps) | LONG Net (8 bps) | LONG PF | SHORT Trades | SHORT Gross (bps) | SHORT Net (8 bps) | SHORT PF |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **LINKUSDT** | 644 | -2.43 | 501 | **+11.63** | **+3.53** | **1.065** | 326 | -1.51 | -9.62 | 0.819 |
| **AVAXUSDT** | 629 | -5.18 | 416 | **+9.81** | **+1.74** | **1.031** | 373 | -12.22 | -20.30 | 0.652 |
| **DOGEUSDT** | 598 | -2.60 | 393 | **+8.39** | **+0.34** | **1.006** | 311 | -4.16 | -12.21 | 0.760 |
| **ADAUSDT**  | 615 | -6.93 | 488 | **+4.81** | -3.25 | 0.948 | 269 | -8.20 | -16.25 | 0.758 |
| **SOLUSDT**  | 558 | -6.60 | 447 | **+4.21** | -3.86 | 0.924 | 217 | -4.64 | -12.71 | 0.726 |
| **XRPUSDT**  | 595 | -7.90 | 425 | **+3.76** | -4.33 | 0.938 | 367 | -0.39 | -8.47 | 0.866 |
| **BTCUSDT**  | 570 | -7.98 | 405 | -0.23 | -8.29 | 0.732 | 280 | **+2.05** | -6.00 | 0.776 |
| **ETHUSDT**  | 568 | -7.21 | 409 | -1.49 | -9.56 | 0.792 | 294 | -0.07 | -8.13 | 0.818 |
| **BNBUSDT**  | 550 | -10.43 | 427 | +0.24 | -7.82 | 0.809 | 203 | -8.24 | -16.31 | 0.580 |
| **LTCUSDT**  | 627 | -8.70 | 427 | -7.34 | -15.44 | 0.780 | 338 | -0.66 | -8.74 | 0.851 |

**Core Quantitative Takeaway:** Forced bidirectional execution causes catastrophic performance degradation. Short trades across altcoins suffer severe losses due to collisions with the macro upward trend in 2025.

---

## 3. Stage 3: Entry Optimization & Adverse Selection Discovery

Comparing immediate market entry ($\delta = 0.0$) against passive limit orders at discount ($\delta \in \{0.10, 0.25\}$ with 3-bar timeout) revealed that **passive limit entry suffers severe adverse selection**:

| Asset | Delta Offset | Completed Trades | Gross Expectancy | Net Expectancy (8 bps) | Profit Factor |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **LINKUSDT** | $\delta = 0.00$ (Market) | 644 | **+5.67 bps** | **-2.43 bps** | **0.957** |
| **LINKUSDT** | $\delta = 0.10$ (Limit)  | 428 | -37.62 bps | -45.68 bps | 0.379 |
| **LINKUSDT** | $\delta = 0.25$ (Limit)  | 395 | -37.51 bps | -45.57 bps | 0.377 |
| **AVAXUSDT** | $\delta = 0.00$ (Market) | 629 | **+2.89 bps** | **-5.18 bps** | **0.907** |
| **AVAXUSDT** | $\delta = 0.10$ (Limit)  | 415 | -30.88 bps | -38.93 bps | 0.462 |
| **AVAXUSDT** | $\delta = 0.25$ (Limit)  | 396 | -29.01 bps | -37.06 bps | 0.477 |

**Microstructure Mechanism:** When a directional predictor triggers, if the limit order gets filled at a pullback discount, it indicates the market is moving *against* the prediction, leading to an immediate drop in TP rate from 30.9% to ~18% and collapsing gross return by $>40\text{ bps}$.

---

## 4. Stage 5: DEC_05 Option 3 Multi-Asset Portfolio Simulation

Simulating the simultaneous multi-asset ledger under DEC_05 Option 3 ($30\%$ gross exposure cap, $10\%$ single-asset cap, pro-rata allocation) yielded:

| Portfolio Metric | Maker-Passive (8 bps) | Hybrid Tier (15 bps) | Baseline Taker (44 bps) |
| :--- | :---: | :---: | :---: |
| **Initial Equity** | $10,000.00 USDT | $10,000.00 USDT | $10,000.00 USDT |
| **Ending Equity** | **$6,933.82 USDT** | **$5,051.68 USDT** | **$1,359.65 USDT** |
| **Total Net PnL** | -$3,066.18 USDT | -$4,948.32 USDT | -$8,640.35 USDT |
| **Net Return** | **-30.66%** | **-49.48%** | **-86.40%** |
| **Arithmetic Mean Daily Return** | **-0.0987% / day** | **-0.1847% / day** | **-0.5385% / day** |
| **Geometric Mean Daily Return** | **-0.1000% / day** | **-0.1856% / day** | **-0.5401% / day** |
| **Median Daily Return** | 0.0000% / day | 0.0000% / day | -0.1159% / day |
| **Mean Rolling 7-day Return** | -0.68% | -1.27% | -3.64% |
| **Worst Rolling 7-day Return** | -10.22% | -12.47% | -21.24% |
| **Worst Single-Day Loss** | -7.12% | -7.41% | -8.63% |
| **Mean Underwater Drawdown** | **14.02%** | **25.67%** | **55.82%** |
| **Maximum Drawdown (MDD)** | **30.71%** | **49.52%** | **86.41%** |
| **Annualized Sharpe Ratio** | -3.718 | -6.134 | -10.233 |
| **Annualized Sortino Ratio** | -2.843 | -4.859 | -8.900 |
| **Total Portfolio Trades** | 4,525 | 4,525 | 4,524 |
| **Candidate Fill Rate** | 78.27% | 78.27% | 78.25% |
| **Average Open Concurrency**| 2.09 positions | 2.09 positions | 2.09 positions |

---

## 5. Stage 6: Walk-Forward Robustness across Folds 1–4

| Fold | Date Span | Evaluated Days | Portfolio Trades | Net Return (%) | Mean Daily (%) | Max Drawdown (%) | Sharpe |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Fold 1** | 2025-01-29 to 2025-04-30 | 91.0 | 2,163 | -10.70% | -0.1258% | 11.72% | -4.751 |
| **Fold 2** | 2025-04-30 to 2025-07-30 | 91.3 | 668 | -3.87% | -0.0435% | 4.52% | -3.045 |
| **Fold 3** | 2025-07-30 to 2025-10-30 | 91.3 | 860 | -12.72% | -0.1430% | 14.01% | -3.454 |
| **Fold 4** | 2025-10-30 to 2026-01-29 | 91.4 | 838 | -7.33% | -0.0823% | 7.75% | -5.803 |

The performance is consistently negative across all four walk-forward folds, proving that the negative expectancy is not driven by an idiosyncratic regime shock, but is intrinsic to trading bidirectional 5-minute LightGBM signals against 8–15 bps of execution drag.

---

## 6. Mathematical Impossibility Proof for +3% Daily Return under DEC_05

1. **Portfolio Exposure Limit:** Under DEC_05 Option 3, aggregate gross exposure is capped at $E_{\text{cap}} = 0.30$ of portfolio equity.
2. **Implied Return on Position Notional:** To achieve a daily portfolio equity return of $R_{\text{daily}} = +3.0\%$, open positions must generate:
   $$R_{\text{notional}} = \frac{R_{\text{daily}}}{E_{\text{cap}}} = \frac{+3.0\%}{0.30} = +10.0\% \text{ per day on position notional} = +1,000\text{ bps/day}$$
3. **Volatility vs Payoff Ceiling:** In 5-minute crypto perpetual candles, median 20-bar volatility ($\sigma_t$) is $14\text{ to }30\text{ bps}$. A complete $2.5\sigma$ Take-Profit hit yields $35\text{ to }75\text{ bps}$ gross. Even across 16 executed trades per day ($4,525 / 365 \approx 12.4\text{ trades/day}$), if **100% of trades hit Take-Profit with zero losses**, the maximum theoretical gross daily portfolio return would be:
   $$\text{Max Gross Daily Return} \approx 12.4 \times (0.05 \text{ notional}) \times 50\text{ bps} \approx +0.31\% \text{ per day}$$
4. **Empirical Edge:** With realistic win rates of $29.9\%$, the gross expectancy is $+1.89\text{ bps}$. After maker-passive friction ($-8.0\text{ bps}$), the net expectancy is $-6.11\text{ bps}$.
5. **Conclusion:** Targeting $+3.0\%$ daily return on total equity under a $30\%$ gross exposure cap is mathematically impossible without exceeding $300\%$ leverage or assuming miraculous $100\%$ win rates.
