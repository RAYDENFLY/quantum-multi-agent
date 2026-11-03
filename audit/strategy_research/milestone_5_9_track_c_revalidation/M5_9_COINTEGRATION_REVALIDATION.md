# QUANTUM RESEARCH AUDIT — MILESTONE 5.9
## Track C Statistical Revalidation & Pairwise Cointegration Audit

**Dossier Path:** `audit/strategy_research/milestone_5_9_track_c_revalidation/M5_9_COINTEGRATION_REVALIDATION.md`  
**Execution Timestamp:** 2026-11-04T00:26:00Z  
**Branch:** `research/quantum-next-3pct`  
**Authorizing Mandate:** Milestone 5.9 Track C Statistical Revalidation Protocol  

---

## 1. Executive Summary & Objective

Milestone 5.9 independently revalidates the statistical claims made in Milestone 5.8B regarding **Track C (Cross-Sectional Relative Value & Cointegration)**.

In Milestone 5.8B, an initial exploratory scan reported that 9 of 45 asset pairs appeared cointegrated at the unadjusted $5\%$ significance level ($t < -3.37$). Milestone 5.9 applies strict econometric rigor to determine whether these relationships represent genuine, exploitable market-neutral alpha or are artifacts of:
1. **Multiple-Testing Contamination (Family-Wise Error Rate inflation across 45 hypothesis tests)**,
2. **Regression Orientation Asymmetry ($y \sim x$ vs $x \sim y$)**,
3. **Full-Sample Fitting Lookahead (Estimating parameters across the full timeline including the future)**,
4. **Out-of-Sample Parameter Instability & Structural Breaks**.

### Key Forensic Findings
```yaml
RESEARCH_MILESTONE: MILESTONE_5_9
CANDIDATE_TRACK: TRACK_C_CROSS_SECTIONAL_RELATIVE_VALUE
TOTAL_PAIRS_TESTED: 45 Asset Pairs (10 Primary Universe Assets)
SURVIVING_PAIRS_TRAINING_ONLY_HOLM_0.05: 0 / 45 (0.0% Survival Rate)
SURVIVING_PAIRS_FULL_SAMPLE_HOLM_0.05: 2 / 45 (SOL/LTC, SOL/DOGE)
ROLLING_STABILITY_AUDIT: 45 / 45 REJECTED (100% Structural Break Failure)
OUT_OF_SAMPLE_SPREAD_STATIONARITY: FAILS_ACROSS_ALL_PAIRS (ADF t collapses to > -2.0)
TRADE_LEVEL_PAIR_TRADING_NET_RETURN: -0.0028% per day (Negative Expectancy after VIP0 Fees)
DIRECTIONAL_RELATIVE_STRENGTH_MDD: 55.65% (Catastrophic Breach of <= 15% MDD Gate)
FINAL_FEASIBILITY_DISPOSITION: REJECTED_AS_UNVIABLE_UNDER_1X_UNLEVERED_GATE
GOVERNANCE_STATUS: REQUIRES_RESEARCH
```

---

## 2. Revalidation of 45 Pairwise Cointegration Tests

### 2.1 Regression Orientation & Residual Asymmetry
In the two-step Engle-Granger procedure, regression orientation matters in finite samples:
- **Orientation 1:** $\ln(P_{A,t}) = \alpha_1 + \beta_1 \ln(P_{B,t}) + \epsilon_{1,t}$
- **Orientation 2:** $\ln(P_{B,t}) = \alpha_2 + \beta_2 \ln(P_{A,t}) + \epsilon_{2,t}$

The empirical audit reveals severe directional asymmetry across multiple crypto pairs:
- **`SOLUSDT / XRPUSDT`:** In Orientation 1 ($SOL \sim XRP$), $t_1 = -3.836$ ($p = 0.013$). But in Orientation 2 ($XRP \sim SOL$), $t_2 = -1.082$ ($p = 0.852$, non-stationary).
- **`SOLUSDT / BNBUSDT`:** Orientation 1 yields $t_1 = -3.657$, while Orientation 2 yields $t_2 = -2.374$ ($p = 0.320$).
- Selecting only the favorable orientation without penalizing orientation divergence introduces selection bias.

### 2.2 Multiple-Testing Correction (Holm-Bonferroni at $\alpha = 0.05$)
When evaluating $m = 45$ simultaneous pairs, the unadjusted nominal significance level $\alpha = 0.05$ produces a family-wise error rate (FWER) of:
$$\text{FWER} = 1 - (1 - 0.05)^{45} \approx \mathbf{90.06\% \text{ Probability of False Positive}}$$

To control FWER at $\alpha = 0.05$, the Holm-Bonferroni step-down correction sorts raw p-values $p_{(1)} \le \dots \le p_{(45)}$ and enforces:
$$p^{\text{adj}}_{(k)} = \max_{j \le k} \left(\min\left(1.0, (m - j + 1) \cdot p_{(j)}\right)\right) \le 0.05$$

#### Results on In-Sample Training Data (`DEVELOPMENT`: 2023-11-01 to 2025-10-31 UTC):
- The single strongest pair in Training is `ADAUSDT / LTCUSDT` with $t = -4.116$ and raw p-value $p_{\text{raw}} = 0.00712$.
- Applying Holm-Bonferroni correction:
  $$p^{\text{adj}} = 45 \times 0.00712 = \mathbf{0.3204} \gg 0.05$$
- **ZERO PAIRS (0 / 45) survive multiple-testing correction on training data.** The 9 pairs identified in M5.8B fail to achieve statistical significance when multiple testing is properly penalized.

#### Results on Full Sample (Oct 2023 – Oct 2026 UTC, with lookahead):
- Even under full-sample lookahead fitting, only **2 pairs** survive Holm-Bonferroni:
  1. `SOLUSDT / LTCUSDT`: $t = -5.474$, $p_{\text{raw}} = 0.00005 \implies p^{\text{adj}} = \mathbf{0.00270} < 0.05$ (Survives).
  2. `SOLUSDT / DOGEUSDT`: $t = -4.789$, $p_{\text{raw}} = 0.00089 \implies p^{\text{adj}} = \mathbf{0.03916} < 0.05$ (Survives).
  3. `SOLUSDT / ADAUSDT`: $t = -4.604$, $p_{\text{raw}} = 0.00177 \implies p^{\text{adj}} = \mathbf{0.07604} > 0.05$ (**Fails**).
  4. All other 42 pairs: $p^{\text{adj}} \ge 0.20$ (**Fails**).

---

## 3. Rolling Stability & Chronological Out-of-Sample Audit

To prevent future-data contamination, all parameters ($\beta_{\text{train}}, \alpha_{\text{train}}$) were estimated **strictly on Training data (`DEVELOPMENT`)** and frozen before evaluating out-of-sample performance in `VALIDATION` (Nov 2025 – Apr 2026) and `OOS` (May 2026 – Oct 2026).

### 3.1 Spread Breakdown Across Partitions
Every candidate pair that exhibited in-sample mean-reversion experienced catastrophic structural breakdown out-of-sample:

| Asset Pair | Frozen $\beta_{\text{train}}$ | Training ADF $t$ (HL) | Validation ADF $t$ (HL) | OOS ADF $t$ (HL) | Validation Drift ($\Delta \mu / \sigma$) | Final Stability Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **SOLUSDT / LTCUSDT** | $1.008$ | **$-3.99$** (30.5d) | **$-1.28$** (31.5d) | **$-2.23$** (15.6d) | $0.68\sigma$ | **STRUCTURAL_BREAK_REJECTED** |
| **SOLUSDT / DOGEUSDT** | $0.618$ | **$-3.89$** (27.8d) | **$-0.01$** (6,575d) | **$-1.61$** (63.8d) | $1.12\sigma$ | **STRUCTURAL_BREAK_REJECTED** |
| **ADAUSDT / LTCUSDT** | $0.526$ | **$-4.12$** (17.8d) | **$-1.63$** (128.6d) | **$-0.85$** (Exploding) | $2.19\sigma$ | **STRUCTURAL_BREAK_REJECTED** |
| **DOGEUSDT / LTCUSDT** | $0.388$ | **$-3.87$** (23.3d) | **$-0.25$** (103.0d) | **$-0.86$** (92.1d) | $1.22\sigma$ | **STRUCTURAL_BREAK_REJECTED** |
| **SOLUSDT / LINKUSDT** | $0.632$ | **$-3.54$** (38.1d) | **$-0.94$** (88.4d) | **$-1.45$** (55.2d) | $1.44\sigma$ | **STRUCTURAL_BREAK_REJECTED** |
| **LINKUSDT / LTCUSDT** | $0.914$ | **$-3.49$** (21.3d) | **$-0.68$** (103.9d) | **$-1.81$** (22.8d) | $1.44\sigma$ | **STRUCTURAL_BREAK_REJECTED** |

### 3.2 Root Cause of Cointegration Breakdown
1. **Regime Shift in Relative Crypto Valuations:** In crypto markets, relative valuations do not reflect underlying cash flows or structural substitution; they are driven by episodic ecosystem rotations (e.g. Solana memecoin volume surge vs Litecoin stagnation).
2. **Permanent Spread Drift:** Once a spread shifts by $>1.5\sigma$, the assumption of a constant unconditional mean $\alpha$ is violated. The spread becomes an integrated random walk $I(1)$ with drift.
3. **Parameter Non-Stationarity:** Rolling 90-day regressions reveal that the hedge ratio $\beta$ fluctuates violently (coefficients of variation $CV(\beta) > 0.45$), rendering fixed-hedge statistical arbitrage unviable.

---

## 4. Fresh Trade-Level Economic Backtest

To comply with Section 4 of the Mandate, a fresh trade-level simulation was built without assuming any baseline profitability.

### 4.1 Methodology & Operational Constraints
- **Venue & Friction:** Bybit VIP0 rates (Maker: +2.0 bps + 1.5 bps adverse selection = 3.5 bps/leg; Taker: 5.5 bps + 2.0 bps spread = 7.5 bps/leg).
- **Round-Trip Cost:** Two legs (Long + Short) require 4 execution events $\approx \mathbf{14.0\text{ bps roundtrip}}$.
- **Lot Sizing & Minimum Notional:** Enforces Bybit $5.00 USDT minimum order value.
- **Strict 1.0x Gross Leverage:** Long weight $\le 0.50$, Short weight $\le 0.50$, Aggregate leverage $\le 1.0000$.

### 4.2 Economic Comparison (Validation + OOS: 365 Days)

```
+---------------------------------------------------------------------------------------------------+
| STRATEGY ARCHITECTURE              | INITIAL EQ | TERMINAL EQ | MEAN DAILY RET | MAX DD | SHARPE  |
+---------------------------------------------------------------------------------------------------+
| Two-Leg Dollar-Neutral Pair        | $100.00    | $97.75      | -0.0028% / day | 13.93% | -0.06   |
| (SOL/LTC, 50% L / 50% S)           |            |             |                |        |         |
|                                    |            |             |                |        |         |
| Single-Slot Directional RS         | $100.00    | $46.09      | -0.1621% / day | 55.65% | -0.90   |
| (100% Long Top 14d Momentum)       |            |             |                |        |         |
+---------------------------------------------------------------------------------------------------+
```

### 4.3 Economic Analysis
1. **Two-Leg Dollar-Neutral Pairs Trading:**
   - Maximum drawdown remained controlled at **$13.93\%$** (satisfying $\le 15.0\%$).
   - However, because the spread drifted non-stationarily out-of-sample, trades suffered repeated divergence stop-outs at $Z = \pm 3.5$.
   - Combined with 14 bps VIP0 friction across two legs, the strategy produced a **negative net daily return of $-0.0028\%$**, completely missing the mandatory $+3.00\%$ target.
2. **Single-Slot Directional Relative Strength:**
   - Attempting to capture pure directional momentum by holding the strongest asset unleashed catastrophic drawdowns (**$55.65\%$ MDD**), destroying more than half of initial capital.

---

## 5. Audit Conclusion & Governance Verdict

The rigorous statistical revalidation in Milestone 5.9 demonstrates:
1. **Track C Falsification:** Cross-sectional relative value and cointegration across crypto majors fail under strictly causal, out-of-sample testing with multiple-testing correction.
2. **Zero Pairs Viable:** Not a single asset pair exhibits stationary cointegration out-of-sample when hedge ratios are estimated without lookahead.
3. **The 3.00% Daily Gate Remains Unmet:** Neither delta-neutral pairs trading nor directional momentum can achieve $+3.00\%$ net daily return at 1.0x unlevered exposure.

Governance Status remains:
`RESEARCH_STATUS: REQUIRES_RESEARCH`  
`PAPER_TRADING_AUTHORIZATION: DENIED_PENDING_3_PERCENT_BACKTEST_VALIDATION`
