# QUANTUM PHASE 5.5.0.3: FUNDING MATHEMATICAL AUDIT

**Document Status:** `APPROVED_FOR_DESIGN`  
**Publication Timestamp:** `2026-11-01 20:48:53 UTC`  
**Associated Deliverable:** Workstream B (Funding Scenario Single Source of Truth)  

---

## 1. RECONCILIATION OF PREVIOUS CONFLICTING VALUES

### Audit of Conflicting References
Cross-document forensic audit identified an inconsistency between documents:
1. In `PHASE_5_5_0_DATA_AVAILABILITY_AUDIT.json`, `PHASE_5_5_0_2_FINAL_APPROVAL_CHECKLIST.md` (DEC_03), and early drafts, the funding sensitivity sweep was loosely written as `[-10, 0, +10, +30 bps]`.
2. In `PHASE_5_5_0_FUNDING_AND_SLIPPAGE_SPECIFICATION.md` and `PHASE_5_5_0_2_FUNDING_SCENARIO_REGISTRY.json`, the rates were specified as `[-0.01%, 0.0%, +0.01%, +0.03% per 8h]` corresponding to `[-1.0, 0.0, +1.0, +3.0 bps per settlement]`.

### Root Cause Analysis
- The phrase `10 bps` was used informally by earlier drafts to mean $0.01\%$. However, mathematically $1\% = 100\text{ bps}$, so $0.01\% = 1.0\text{ bps}$.
- If a rate were $10\text{ bps per 8h settlement window}$, that would equal $0.10\% \text{ per 8h}$, which annualizes to $10 \times 1095 = 10,950\text{ bps annual} = 109.5\%\text{ annual}$. Such a rate represents an extreme crisis spike, not a typical market regime.
- Conversely, a baseline perpetual funding rate in cryptocurrency markets is typically $0.01\% \text{ per 8h}$ ($1.0\text{ bps per settlement}$), which annualizes to $10.95\%\text{ annual}$ ($1095\text{ bps annual}$).

---

## 2. AUTHORITATIVE PRIMARY UNIT & ANNUALIZATION FORMULA

Phase 5.5.0.3 establishes one authoritative primary unit across all specifications:
`funding_rate_bps_per_settlement`
For standard cryptocurrency perpetual futures with 3 settlements per 24 hours (every 8 hours at `00:00`, `08:00`, `16:00 UTC`):
$$F_{\text{bps,annual}} = F_{\text{bps,settlement}} \times 3 \times 365 = F_{\text{bps,settlement}} \times 1095$$
$$F_{\text{pct,annual}} = F_{\text{bps,settlement}} \times 0.1095\%$$

This conversion is a nominal annual scaling convention, NOT an empirical claim about realized historical funding.

---

## 3. SINGLE SOURCE OF TRUTH SCENARIO TABLE

| Scenario ID | Scenario Name | Rate (bps/settle) | Decimal Rate ($f_t$) | Rate (% / 8h) | Nominal Ann (bps) | Nominal Ann (%) | Evidence Status | Human Approval |
|---|---|---|---|---|---|---|---|---|
| `SCENARIO_F_NEUTRAL` | Zero Funding Baseline | 0.0 | 0.000000 | 0.00% | 0.0 | 0.00% | `UNVERIFIED_ASSUMPTION` | `PENDING_HUMAN_DECISION` |
| `SCENARIO_F_BULL_MODERATE` | Moderate Bull Premium | 1.0 | 0.000100 | +0.01% | 1095.0 | +10.95% | `UNVERIFIED_ASSUMPTION` | `PENDING_HUMAN_DECISION` |
| `SCENARIO_F_BULL_SEVERE` | Severe Bull Euphoria | 3.0 | 0.000300 | +0.03% | 3285.0 | +32.85% | `UNVERIFIED_ASSUMPTION` | `PENDING_HUMAN_DECISION` |
| `SCENARIO_F_BEAR_MODERATE` | Moderate Bear Discount | -1.0 | -0.000100 | -0.01% | -1095.0 | -10.95% | `UNVERIFIED_ASSUMPTION` | `PENDING_HUMAN_DECISION` |

---

## 4. CASH FLOW SIGN CONVENTIONS AND NUMERICAL PROOFS

For any position open across a funding settlement timestamp $t_{\text{settle}} \in \{00:00, 08:00, 16:00\text{ UTC}\}$:
$$CF_t = -d \times N_t \times f_t$$
where:
- $d = +1$ for LONG positions.
- $d = -1$ for SHORT positions.
- $N_t$ is active quote notional in USDT ($N_t = Q_t \times P_{\text{mark}, t}$).
- $f_t$ is decimal funding rate ($f_t = F_{\text{bps,settlement}} / 10,000$).

### Numerical Verification Example 1: Positive Funding Rate ($f_t = +0.0001$, Bull Regime)
- **LONG Position ($d = +1$):**
  $$CF_t = -(+1) \times 10,000 \times 0.0001 = -1.00\text{ USDT}$$
  Negative cash flow: Long pays 1.00 USDT funding financing drag.
- **SHORT Position ($d = -1$):**
  $$CF_t = -(-1) \times 10,000 \times 0.0001 = +1.00\text{ USDT}$$
  Positive cash flow: Short receives 1.00 USDT funding financing credit.

### Numerical Verification Example 2: Negative Funding Rate ($f_t = -0.0001$, Bear Regime)
- **LONG Position ($d = +1$):**
  $$CF_t = -(+1) \times 10,000 \times (-0.0001) = +1.00\text{ USDT}$$
  Positive cash flow: Long receives 1.00 USDT funding financing credit.
- **SHORT Position ($d = -1$):**
  $$CF_t = -(-1) \times 10,000 \times (-0.0001) = -1.00\text{ USDT}$$
  Negative cash flow: Short pays 1.00 USDT funding financing drag.
