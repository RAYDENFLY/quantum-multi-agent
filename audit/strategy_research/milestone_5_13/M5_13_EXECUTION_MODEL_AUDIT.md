# QUANTUM MILESTONE 5.13 — EXECUTION MODEL AUDIT & TRANSACTION COST DECOMPOSITION

**Milestone:** M5.13 — Multi-Factor Confluence & Passive Maker Alpha Discovery  
**Repository:** `d:/quantum-multi-agent`  
**Audit Date:** 2026-11-04  
**Classification:** Microstructure & Execution Economics  
**Venue:** AsterDEX USDT Linear Perpetual Futures (Base Retail Tier)  

---

## 1. Executive Summary

Milestone 5.13 establishes an exhaustive, four-regime transaction cost accounting framework. A strategy cannot be considered viable merely because it demonstrates gross profitability or places hypothetical limit orders at favorable past prices.

This audit evaluates strategies across four operational execution regimes plus a zero-friction diagnostic benchmark:
1. **Regime 1: TAKER / TAKER** — Aggressive market entry, aggressive market exit.
2. **Regime 2: MAKER / MAKER** — Passive limit entry, passive limit exit with queue and adverse selection modeling.
3. **Regime 3: MAKER / TAKER** — Passive limit entry, aggressive market stop-loss or emergency exit.
4. **Regime 4: TAKER / MAKER** — Aggressive market entry, passive limit take-profit exit.
5. **Upper Bound: ZERO FRICTION** — Diagnostic theoretical upper bound for alpha potential.

---

## 2. Transaction Cost Parameters & Fee Decomposition

All cost accounting derives from the authoritative fee schedule profile `ASTERDEX_BASE_RETAIL_v1` in [`src/quantum/accounting/fee_schedules.py`](file:///d:/quantum-multi-agent/src/quantum/accounting/fee_schedules.py):

| Cost Dimension | Taker Order (per leg) | Maker Order (per leg) | Economic Rationale / Microstructural Origin |
| :--- | :---: | :---: | :--- |
| **Exchange Exchange Fee** | $10.0\text{ bps}$ | $4.0\text{ bps}$ | Base Retail tier schedule on executed notional |
| **Half-Spread Crossing** | $1.0\text{ bps}$ | $0.0\text{ bps}$ | Takers pay half-spread; makers earn or sit at best bid/ask |
| **Execution Slippage** | $2.0\text{ bps}$ | $0.0\text{ bps}$ | Price impact and depth consumption for aggressive orders |
| **Adverse Selection Markout** | $0.0\text{ bps}$ | $1.5\text{ to } 2.5\text{ bps}$ | Toxic order flow penalty (limit orders picked off before adverse runs) |
| **Total Friction per Leg** | **$13.0\text{ bps}$** | **$5.5\text{ bps}$** | Double-entry cash deduction |

---

## 3. Four Canonical Execution Regimes Comparison

```
   TAKER / TAKER:  [ Entry: 10 fee + 1 spread + 2 slip ] + [ Exit: 10 fee + 1 spread + 2 slip ] = 26.0 bps
   MAKER / MAKER:  [ Entry: 4 fee + 1.5 adv_sel ]        + [ Exit: 4 fee + 1.5 adv_sel ]        = 11.0 bps
   MAKER / TAKER:  [ Entry: 4 fee + 1.5 adv_sel ]        + [ Exit: 10 fee + 1 spread + 2 slip ] = 18.5 bps
   TAKER / MAKER:  [ Entry: 10 fee + 1 spread + 2 slip ] + [ Exit: 4 fee + 1.5 adv_sel ]        = 18.5 bps
```

| Execution Regime | Entry Friction | Exit Friction | Total Roundtrip Friction | Fill Certainty | Execution Latency |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1. Taker / Taker** | $13.0\text{ bps}$ | $13.0\text{ bps}$ | **$26.00\text{ bps}$** | $100\%$ immediate fill | $0\text{ ms}$ (Immediate execution) |
| **2. Maker / Maker** | $5.5\text{ bps}$ | $5.5\text{ bps}$ | **$11.00\text{ bps}$** | $\approx 45\% - 65\%$ queue fill | Variable (5m to 30m in queue) |
| **3. Maker / Taker** | $5.5\text{ bps}$ | $13.0\text{ bps}$ | **$18.50\text{ bps}$** | Entry conditional; Exit 100% | Exit immediate on stop hit |
| **4. Taker / Maker** | $13.0\text{ bps}$ | $5.5\text{ bps}$ | **$18.50\text{ bps}$** | Entry 100%; Exit conditional | Limit take-profit resting |
| **5. Zero Friction** | $0.0\text{ bps}$ | $0.0\text{ bps}$ | **$0.00\text{ bps}$** | $100\%$ immediate | Diagnostic upper bound |

---

## 4. Economic Implications for Alpha Design

1. **The $26.0\text{ bps}$ Taker Barrier:**
   Under retail taker execution, any strategy with a gross edge $< 26.0\text{ bps}$ will generate a guaranteed net negative return. Micro-alpha strategies (such as HYP-01 to HYP-06 in M5.11) with gross edges of $+1.0\text{ to } +2.0\text{ bps}$ cannot operate under taker execution.
2. **The $11.0\text{ bps}$ Maker Reality:**
   While maker execution cuts fees from $26.0\text{ bps}$ to $11.0\text{ bps}$, it is NOT free. Maker orders pay $8.0\text{ bps}$ in exchange fees plus $3.0\text{ bps}$ in adverse selection drag.
3. **Hybrid Regime 3 (Maker Entry / Taker Exit):**
   In institutional practice, Maker Entry / Taker Exit is the most robust realistic architecture: entry orders patient in the queue reduce cost to $5.5\text{ bps}$, while protective stop-loss orders execute aggressively ($13.0\text{ bps}$) to prevent ruinous gap exposure. Total roundtrip friction is $18.5\text{ bps}$.
