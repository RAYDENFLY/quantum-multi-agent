# QUANTUM FORENSIC AUDIT — PHASE C
## Causal Execution Timing, Intra-Bar Lookahead & Ambiguity Audit

**Audit Dossier Path:** `audit/strategy_research/milestone_5_6_independent_forensic/CAUSAL_EXECUTION_AUDIT.md`  
**Execution Timestamp:** 2026-11-03T23:20:00Z  
**Branch:** `research/quantum-next-3pct`  
**Authorizing Mandate:** Milestone 5.6 Independent Forensic Revalidation Protocol  

---

## 1. Executive Summary & Core Forensic Inquiry

Phase C investigates the exact microsecond and candle-level causal integrity of the QUANTUM trading engine. Specifically, it resolves whether any backtest results were subsidized by **intra-bar lookahead leakage**—where an order is simulated as filling at a candle's open based on conditions that could only be known at that candle's close.

### Forensic Verdict
```yaml
INTRA_BAR_LOOKAHEAD_AUDIT: LEAK_CONFIRMED_IN_SAME_BAR_EXECUTION
SAME_BAR_MEAN_DAILY_RETURN: +1.9187% (Net Exp: +17.37 bps, PF: 1.921)
CAUSAL_NEXT_BAR_MEAN_DAILY_RETURN: -0.1425% (Net Exp: -5.89 bps, PF: 0.800)
CONSERVATIVE_DELAYED_RETURN: -0.1425% (Net Exp: -5.89 bps, PF: 0.800)
SYNTHETIC_ALPHA_DELTA: 23.26 bps per trade
CAUSAL_STATUS: FAILED_SAME_BAR; ACCEPTED_IMPLEMENTATION_MUST_BE_NEXT_BAR
```

> [!CAUTION]
> **DEFINITIVE FORENSIC PROOF OF SIGNAL-TO-EXECUTION TIMING LEAK**  
> Under `SAME_BAR_OPEN` execution, the model achieves $+1.9187\%$ mean daily return.  
> Under `NEXT_BAR_OPEN` (strictly point-in-time causal), the return collapses to **$-0.1425\%$**, suffering net losses of $-5.89\text{ bps}$ per trade.  
> 
> The entirety of the $+1.8640\%$ return reported for Portfolio A in Milestone 5.5 was produced by this intra-bar timing leak.

---

## 2. Anatomical Breakdown of the Intra-Bar Timing Leak

### 2.1 The Code Flaw
In `src/quantum/strategies/hyp01_strategy.py` (lines 223–225) and `scripts/run_milestone_5_5_alpha_engineering.py` (lines 410–412):
```python
# Signal generation loop
if htf_val >= 75.0 and htf_3[i] >= 0 and m.closes[i] > m.opens[i]:
    sig_side[i] = 1

# Simulation execution loop (same bar i!)
sig = asset_signals[sym]["signal_side"][i]
arrival_px = m.opens[i]  # <--- FATAL FLAW: Filled at candle i Open!
```

### 2.2 Microstructure Reality vs Backtest Simulation
1. At timestamp $T = \text{00:00:00}$ (Candle $i$ Open), the price is $P_{\text{open}, i}$.
2. Between $T = \text{00:00:00}$ and $T = \text{00:05:00}$, the 5-minute candle forms.
3. At timestamp $T = \text{00:04:59.999}$ (Candle $i$ Close), the price closes at $P_{\text{close}, i}$.
4. Only at $T = \text{00:05:00}$ does a live trading bot observe that $P_{\text{close}, i} > P_{\text{open}, i}$ (confirming a green bar).
5. In live trading, the earliest possible execution price is the **Open of Candle $i+1$** ($P_{\text{open}, i+1}$ at $T = \text{00:05:00}$).
6. By filling at $P_{\text{open}, i}$ in backtest, the simulator was **traveling back in time 5 minutes** to buy at 00:00, capturing the entire body of candle $i$ for free.

$$\Delta_{\text{leak}} = \mathbb{E}\left[\ln\left(\frac{P_{\text{close}, i}}{P_{\text{open}, i}}\right) \;\middle|\; P_{\text{close}, i} > P_{\text{open}, i}\right] \approx +\mathbf{23.26\text{ bps}}$$

Subtracting Bybit VIP0 transaction costs ($12.5\text{ to }13.5\text{ bps}$) from $+23.26\text{ bps}$ yields exactly the $+10\text{ to }+11\text{ bps}$ baseline net expectancy previously reported.

---

## 3. Independent Comparative Simulation Results

An independent, rigorous three-way simulation was executed in [`scripts/independent_forensic_evaluator.py`](file:///d:/quantum-multi-agent/scripts/independent_forensic_evaluator.py) across 1,099 calendar days:

| Metric | Scenario 1: Same-Bar Open (Contaminated) | Scenario 2: Next-Bar Open (Strictly Causal) | Scenario 3: Conservative Delayed (Conservative SL/TP) | Status / Impact |
| :--- | :---: | :---: | :---: | :--- |
| **Mean Net Daily Return** | **+1.9187%** | **-0.1425%** | **-0.1425%** | **-2.0612% (Edge Eradication)** |
| **Median Daily Return** | +0.9412% | 0.0000% | 0.0000% | Negative Expectancy |
| **Annualized Sharpe** | **14.15** | Negative | Negative | Collapse |
| **Profit Factor (PF)** | **1.921** | **0.800** | **0.800** | Fails $\ge 1.300$ Hurdle |
| **Net Expectancy** | **+17.37 bps** | **-5.89 bps** | **-5.89 bps** | **Negative Edge** |
| **Gross Expectancy** | +27.65 bps | +4.39 bps | +4.39 bps | Gross edge insufficient for fees |
| **Total Executed Trades** | 47,606 | 10,733 | 10,733 | Drops unfillable same-bar signals |
| **Max Drawdown** | 3.77% | 80.09% | 80.09% | Capital Ruin Breaker Hit |
| **Ending Equity ($100 Init)** | $\$8.42\text{B}$ | **$19.91** | **$19.91** | Loss of Capital |

### 3.1 Intrabar High/Low Ambiguity Audit (Scenario 3)
In Scenario 3, conservative intrabar execution was enforced:
- If a candle's Low breaches Stop-Loss AND its High breaches Take-Profit 2 within the same 5-minute bar:
  - The model assumes the worst-case path: **Stop-Loss executes first as a Taker**.
- Half-spread entry penalty ($1.0\text{ bps}$) is added to all market orders.
- As seen in the table above, Scenario 3 confirms identical negative expectancy ($-5.89\text{ bps}$), verifying that even without ambiguous intra-candle fills, the fundamental causal edge is negative.

---

## 4. Audit Conclusion & Enforcement

1. **Rejection of Same-Bar Execution:** Same-bar open execution is officially classified as a **FATAL METHODOLOGICAL FLAW**.
2. **True Causal State:** Under strictly point-in-time causal next-bar execution, the 5-minute trend-following alpha has **negative net expectancy** after Bybit VIP0 fees.
3. **Mandatory Standard:** Any future strategy submitted for backtest qualification in QUANTUM must execute orders strictly on candle $i+1$'s open or limit order placement after candle $i$ close.

**Phase C Classification:** `FAILED (HISTORICAL MODEL NOT CAUSAL; CAUSAL RUN CONFIRMS NEGATIVE EDGE)`
