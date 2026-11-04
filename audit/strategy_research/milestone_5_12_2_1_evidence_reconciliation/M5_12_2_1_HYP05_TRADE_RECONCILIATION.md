# QUANTUM MILESTONE 5.12.2.1: HYP-05 TRADE COUNT & GROSS PNL RECONCILIATION
## Forensic Audit of Canonical Trades (2,592) vs. Narrative Trades (10,429) & Gross PnL (+$48.36)

**Milestone:** 5.12.2.1 — Independent Evidence Reconciliation & Adversarial Validation  
**Hypothesis:** HYP-05 (Range Mean Reversion)  
**Branch:** `research/quantum-next-3pct`  
**Audit Harness:** `scripts/reconcile_hyp05_trades.py`  
**Audit Date:** 2026-11-04  
**Audit Status:** FULLY RECONCILED (+$48.36 BIT-EXACT REPRODUCED, EXACT CONSERVATION CONFIRMED)  

---

## 1. Executive Summary

Milestone 5.12.2 reported two sets of trade numbers for HYP-05:
1. **Statistical Table (`M5_12_2_EXECUTION_COVERAGE_MATRIX.csv`, Row 22):** **2,592 completed trades**, Net PnL **$-\$39.00**, Gross PnL **$+\$2.01**.
2. **Narrative / Zero-Friction Matrix (Row 26):** **10,429 completed trades**, Gross PnL **$+\$48.36**, Gross Expectancy **$+1.85\text{ bps}$**.

The independent review noted that referencing 10,429 trades in the narrative alongside a statistical table reporting 2,592 trades appeared inconsistent.

### The Forensic Finding:
The reconciliation independently reproduced both figures bit-for-bit from raw canonical data:
- **10,429 trades and $+\$48.36$ Gross PnL** is the exact output of the **`ZERO_FRICTION_DIAGNOSTIC`** run. In the absence of transaction fees, portfolio equity remained intact, allowing all 10,429 unconstrained symbol-level trade episodes across the 10 assets to be admitted and executed.
- **2,592 trades and $-\$39.00$ Net PnL** is the exact output of the **`TAKER_TAKER`** run. Under aggressive 26 bps roundtrip friction, cumulative fee drag ($-\$41.01$) eroded portfolio equity down to $\$20.00$. At $\$20.00$ equity, the $25\%$ maximum symbol allocation ($E \cdot 0.25 = \$5.00$) dropped subsequent orders below the $\$5.00$ minimum viable order threshold, choking off and rejecting **7,837 subsequent trade candidates**.
- **Conservation Law:**
  $$\mathbf{2,592\text{ (Taker Executed)}} + \mathbf{7,837\text{ (Margin Depletion Rejections)}} = \mathbf{10,429\text{ (Zero-Friction Executed)}}$$
  **Discrepancy: Exactly $0.000000$.**
- **Provenance of $+\$48.36$ Gross PnL:** Independently verified. Under zero friction, the 10,429 completed trades generated gross profits of $\$271.42$ against gross losses of $-\$223.06$, yielding a net gross profit of **$+\$48.36$** (Profit Factor: $1.10$).

---

## 2. Independent Recalculation Across Pipeline Stages

Extracted directly from `M5_12_2_1_HYP05_TRADE_RECONCILIATION.csv`:

| Pipeline Stage / Metric | Zero-Friction Diagnostic (Unconstrained) | Taker/Taker Retail (Capital Depleted) | Unit of Observation | Reconciliation Finding |
|---|:---:|:---:|:---:|---|
| **Universe 5m Bars** | 400,000 | 400,000 | Market Bars | Identical 10 assets $\times$ 40,000 bars |
| **Conjoint Raw Signals** | 13,431 | 13,431 | Signal Bars | Identical causal indicator rules (BB + Stoch + ADX) |
| **Completed Trade Episodes** | **10,429** | **2,592** | Trades | 10,429 unconstrained vs 2,592 fee-choked |
| **Gross Trading PnL** | **+$48.36** | **+$2.01** | USD | Exact match across respective trade counts |
| **Transaction Friction** | **$0.00** | **-$41.01** | USD | 26 bps taker fee + spread + slippage |
| **Net Trading PnL** | **+$48.36** | **-$39.00** | USD | +$48.36 gross vs -$39.00 net loss |
| **Trade Expectancy** | **+1.85 bps** (or +1.53 bps on alloc) | **-6.02 bps** (-12.36 bps on alloc) | Basis Points | Positive raw gross vs negative net |
| **Win Rate** | **45.94%** | **44.29%** | Percent | 4,791 / 10,429 wins vs 1,148 / 2,592 wins |
| **Margin Depletion Rejections** | **0** | **7,837** | Orders | Excluded after equity fell $\le \$20.00$ |

---

## 3. Symbol-Level Breakdown of HYP-05 Universe (10,429 Trades)

| Symbol | Total Bars | Raw Signals | Completed Trades | Win Rate (%) | Gross PnL ($) |
|:---|:---:|:---:|:---:|:---:|:---:|
| **BTCUSDT** | 40,000 | 1,712 | 1,278 | 46.24% | +$6.84 |
| **ETHUSDT** | 40,000 | 1,608 | 1,215 | 45.19% | +$5.12 |
| **SOLUSDT** | 40,000 | 1,786 | 1,344 | 46.50% | +$8.45 |
| **BNBUSDT** | 40,000 | 1,785 | 1,352 | 47.12% | +$7.90 |
| **XRPUSDT** | 40,000 | 1,862 | 1,375 | 45.89% | +$4.31 |
| **ADAUSDT** | 40,000 | 827 | 708 | 44.92% | +$2.15 |
| **AVAXUSDT**| 40,000 | 593 | 507 | 45.76% | +$2.80 |
| **LINKUSDT**| 40,000 | 737 | 648 | 44.60% | +$1.95 |
| **DOGEUSDT**| 40,000 | 1,746 | 1,335 | 46.89% | +$6.24 |
| **LTCUSDT** | 40,000 | 775 | 667 | 45.28% | +$2.60 |
| **TOTAL** | **400,000** | **13,431** | **10,429** | **45.94% Avg** | **+$48.36** |

---

## 4. Evaluation of the Reporting Inconsistency

The forensic audit clarifies:
1. **Was there an error in the simulation?**
   - **No.** Both simulations ran correctly. The portfolio ledger behaved exactly as designed: under zero friction, all 10,429 trades executed; under taker friction, capital depletion correctly choked off trading after 2,592 trades.
2. **Was there an error in reporting?**
   - **Yes, in presentation clarity.** The executive summary cited the **gross performance of the zero-friction universe** ($10,429$ trades, $+\$48.36$) to illustrate raw market inefficiency, but compared it directly against the **net performance of the fee-depleted run** ($2,592$ trades, $-\$39.00$) without explicitly clarifying that $7,837$ trades were skipped in the latter due to capital depletion.
3. **Corrected Scientific Statement:**
   - Under `ZERO_FRICTION_DIAGNOSTIC` ($10,429$ trades), HYP-05 achieved $+\$48.36$ gross PnL ($+1.85\text{ bps}$ gross expectancy).
   - Under `TAKER_TAKER` ($2,592$ trades), HYP-05 generated $+\$2.01$ gross PnL, paid $-\$41.01$ in transaction costs, and suffered a net loss of $-\$39.00$ ($-6.02\text{ bps}$ net expectancy), with the remaining $7,837$ trades blocked by capital exhaustion.
