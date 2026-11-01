# QUANTUM PHASE 5.5.0.4: REVERSIBILITY AND RISK REGISTER

**Document Status:** `APPROVED_FOR_DESIGN`  
**Publication Timestamp:** `2026-11-01 20:56:06 UTC`  

---

## 1. COMPREHENSIVE DECISION RISK & REVERSIBILITY EVALUATION

| Decision ID | Research & Economic Impact | Risk of Incorrect Selection | Reversibility Level | Evidence Required to Revisit | Affects Frozen Artifacts? | Can Change Mid-Phase 5.5? |
|---|---|---|---|---|---|---|
| **DEC_01** (Barrier Architecture) | High: Governs trade payoff geometry and holding duration. | High: Selecting Alt A causes 1:17 risk-reward collapse on gaps, falsely rejecting alpha. | **MODERATE** | Out-of-fold execution slippage and fill simulation metrics. | **NO (100% Intact)** | **NO** (Invalidates backtest comparisons) |
| **DEC_02** (Directional Scope) | High: Governs trade volume, market exposure, and direction. | High: Selecting Bidirectional without separation allows bull market long profits to hide short losses. | **HIGH** | Separate Long vs Short PnL curves and win rates from Folds 1-4. | **NO (100% Intact)** | **YES** (Can restrict to Long-only if Shorts fail) |
| **DEC_03** (Funding Model) | Moderate: Financing drag on held positions (12.5% crossing incidence). | Low: Parametric sweep covers wide spectrum (0 to +32.85% annual). | **HIGH** | External audited historical funding rate dataset backfill. | **NO (100% Intact)** | **YES** (Can re-run sensitivity grid) |
| **DEC_04** (Cost Gate Tier) | Critical: Gate 2 break-even pass/fail filter. | High: Setting too low (15 bps) yields false alpha; setting too high (30 bps) prematurely kills strategy. | **MODERATE** | Audited live exchange execution logs and tick slippage data. | **NO (100% Intact)** | **NO** (Moving goalposts invalidates Gate 2) |
| **DEC_05** (Portfolio Risk) | High: Governs total account leverage and max drawdown. | Critical: Excess leverage (5.0x) during correlated crypto crash causes account liquidation. | **HIGH** | Synchronized block bootstrap drawdown distributions. | **NO (100% Intact)** | **YES** (Can adjust leverage cap downward) |
| **DEC_06** (XMR Scope) | Moderate: Portfolio asset universe alignment. | Moderate: Including XMR corrupts 1,100-day covariance matrix with 291-day ragged data. | **HIGH** | Historical XMR data backfill from alternative exchanges. | **NO (100% Intact)** | **YES** (Can add/remove XMR from portfolio runs) |

---

## 2. GOVERNANCE RULE ON REVERSIBILITY

- Primary acceptance hurdles (DEC_01, DEC_04) must remain fixed throughout Phase 5.5 to maintain scientific integrity and prevent p-hacking.
- Risk control parameters (DEC_02, DEC_05) may be restricted conservatively during Phase 5.5 if empirical evidence warrants tighter safety buffers.
