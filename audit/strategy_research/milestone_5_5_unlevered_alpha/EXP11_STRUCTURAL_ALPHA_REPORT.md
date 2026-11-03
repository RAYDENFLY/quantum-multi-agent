# QUANTUM EXPERIMENT REPORT — EXP-11
## Structural Impulse Continuation Alpha & Forensic Lookahead Audit

**Audit Dossier Path:** `audit/strategy_research/milestone_5_5_unlevered_alpha/EXP11_STRUCTURAL_ALPHA_REPORT.md`  
**Execution Timestamp:** 2026-11-03T21:30:00Z  
**Branch:** `research/quantum-next-3pct`  
**Mandatory Performance Target:** $\ge 3.00\%$ Net Mean Daily Return  
**Mandatory Leverage Constraint:** 1.0x (UNLEVERED) Gross Exposure Cap  
**Authorizing Mandate:** Milestone 5.5 Research Protocol  

---

## 1. Executive Summary & Critical Forensic Finding

EXP-11 was formulated to capture ultra-high-velocity order flow impulses. Based on Phase A's discovery that trades resolving within 1–2 bars possess an $89.4\%$ win rate and $+83.6\text{ bps}$ net expectancy, EXP-11 detects extreme 1-bar directional expansion (candle body $\ge 1.0\sigma$, relative volume $\text{RVOL} \ge 1.30$, and minimal counter-wick $\le 20\%$) and exits strictly within 2 bars (10 minutes).

### Initial Reported Performance vs Point-in-Time Audit

In initial simulation, EXP-11 appeared to achieve the elusive project mandate:
- Initial Reported Return: **$+3.0840\%$ mean daily return**
- Initial Reported Profit Factor: **2.637**
- Initial Reported Sharpe: **16.68**
- Initial Reported Trades: **93,684**

> [!CAUTION]
> **CRITICAL FORENSIC AUDIT DISCOVERY: INTRA-BAR LOOKAHEAD CONTAMINATION**  
> An independent forensic audit of the simulation engine revealed that EXP-11 suffered from an **intra-bar signal-to-execution timing leak**.
> 
> The signal condition was evaluated using candle $i$'s completed close:
> `if body >= (1.0 * sigma * c) and rvol >= 1.30 and (h - c) / rng <= 0.20:`  
> However, the execution engine filled the order at candle $i$'s open:  
> `arrival_px = m.opens[i]`
> 
> By filling at the open of candle $i$ based on the characteristics of candle $i$'s close, the backtest was **buying at 00:00 using price information known only at 00:05**. It captured the entire body of the impulse candle before it occurred!

---

## 2. Forensic Reconciliation: Causal vs Non-Causal Performance

When the execution timing is corrected so that the order is executed at candle $i+1$'s open (`opens[i+1]`)—the exact moment the completed candle $i$ is visible to a live trading algorithm—the strategy's edge undergoes immediate structural decay:

| Metric | Contaminated (Same-Bar Open) | Corrected Causal (Next-Bar Open) | Forensic Delta ($\Delta$) | Gate Compliance |
| :--- | :---: | :---: | :---: | :---: |
| **Mean Net Daily Return** | **+3.0840%** | **-0.2104%** | **-3.2944%** | **FAILED** |
| **Median Daily Return** | +2.0871% | 0.0000% | -2.0871% | **FAILED** |
| **Annualized Sharpe** | 16.68 | Negative | -100% | **FAILED** |
| **Profit Factor (PF)** | 2.637 | 0.812 | -69.2% | **FAILED** |
| **Net Expectancy** | +14.04 bps | **-8.45 bps** | **-22.49 bps** | **FAILED** |
| **Gross Expectancy** | +26.81 bps | +4.35 bps | -22.46 bps | **FAILED** |
| **Win Rate** | 70.81% | 41.20% | -29.61% | **FAILED** |
| **Ending Equity ($100 Init)** | $\$1.71\times 10^{16}$ | **$21.40** (Ruin Breaker) | -100% | **FAILED** |

### Mathematical Decomposition of the Leak

Let $P_{o, i}$ and $P_{c, i}$ be the open and close of bar $i$, and $P_{c, i+2}$ be the exit price at bar $i+2$.
The total log return recorded by the contaminated simulator was:

$$R_{\text{reported}} = \ln\left(\frac{P_{c, i+2}}{P_{o, i}}\right) = \underbrace{\ln\left(\frac{P_{c, i}}{P_{o, i}}\right)}_{\text{Synthetic Lookahead Body } (\approx +22.5\text{ bps})} + \underbrace{\ln\left(\frac{P_{c, i+2}}{P_{c, i}}\right)}_{\text{True Post-Signal Return } (\approx +4.3\text{ bps})}$$

1. The impulse selection criterion required $\ln(P_{c, i} / P_{o, i}) \ge 1.0\sigma \approx +22.5\text{ bps}$.
2. In reality, once an extreme impulse candle completes on a 5-minute chart, liquidity providers lean against the move, causing immediate mean-reversion or shallow consolidation on bars $i+1$ and $i+2$.
3. The true post-signal gross return is only $+4.35\text{ bps}$.
4. Subtracting Bybit VIP0 transaction costs ($12.80\text{ bps}$) yields a net expectancy of:
$$\text{Net Expectancy} = +4.35\text{ bps} - 12.80\text{ bps} = \mathbf{-8.45\text{ bps}}$$

---

## 3. Generalization to Historical Research (EXP-01 through EXP-08)

This forensic discovery led directly to an audit of the baseline HYP-01 engine (`src/quantum/strategies/hyp01_strategy.py`).
Lines 223 and 234 contained:
```python
if m.closes[i] > m.opens[i]:
    sig_side[i] = 1
```
Followed by line 428:
```python
arrival_px = m.opens[i]
```

This confirmed that **the reported $+11.36\text{ to }+13.28\text{ bps}$ baseline expectancy in HYP-01 was also heavily subsidized by intra-bar candle color information**.
When evaluated strictly point-in-time (`closes[i-1] > opens[i-1]` entering at `opens[i]`), HYP-01's net expectancy drops to **-14.28 bps**, resulting in steady portfolio drawdown.

---

## 4. Research Conclusion & Governance Enforcement

1. **Rejection of EXP-11:** EXP-11's apparent qualification ($+3.084\%$) is completely invalidated as a artifact of intra-bar lookahead bias.
2. **True Causal Performance:** Strictly causal impulse continuation fails with $-8.45\text{ bps}$ net expectancy.
3. **Integrity Mandate Fulfilled:** In accordance with the Project Owner's instructions, QUANTUM's forensic verification has prevented the authorization of a non-viable strategy that would have incurred substantial capital losses in live market conditions.

### Final Classification
`DISQUALIFIED: FATAL LOOKAHEAD TIMING CONTAMINATION`
