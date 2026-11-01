# QUANTUM PHASE 5.5.0.5: DEC_04 COST DEFINITION & HURDLE AUDIT

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-01 21:02:03 UTC`  
**Associated Deliverable:** Workstream B (DEC_04 Operational Definition)  

---

## 1. COST CEILING VS BREAK-EVEN GROSS RETURN HURDLE

The previous governance materials risked conflating two distinct concepts that must be formally decoupled:

### Concept 1: Transaction Cost Ceiling ($C_{\text{round-trip, max}}$)
- **Definition:** A parameter bound or stress scenario representing the assumed round-trip friction of executing a trade.
- **Purpose:** Used in parametric sensitivity sweeps (e.g. 15, 20, 30 bps) to evaluate strategy resilience across different market microstructure regimes.
- **Nature:** An exogenous assumption, NOT a measured performance output.

### Concept 2: Break-Even Gross Return Hurdle ($R_{\text{gross, min}}$)
- **Definition:** The minimum average gross return that a specialist strategy must achieve so that its net expected return after all deductions is non-negative ($R_{\text{net}} \ge 0$).
- **Simplified Intuition:** $R_{\text{gross, min}} = C_{\text{round-trip}}$.
- **Why Simple Equality Fails in Reality:**
  1. **Discrete Financing Cash Flows:** Trades held across an 8-hour funding boundary incur financing drag ($CF_t = -d \times N_t \times f_t$) that is independent of execution slippage.
  2. **Nonlinear Market Impact:** Larger orders suffer disproportionately higher slippage due to participation ratio scaling ($\beta \sqrt{N/V}$).
  3. **Compounding & Drawdown Drag:** Losing trades reduce account equity, requiring greater percentage gains on subsequent trades to recover.
  4. **Asymmetric Entry vs Exit Denominators:** A 20 bps cost on an entry at $100.00$ ($0.20$ USDT) is not identical in dollar terms to a 20 bps cost on an exit at $102.00$ ($0.204$ USDT).

---

## 2. PRECISE COMPONENT DECOMPOSITION & DENOMINATOR CONSISTENCY

Phase 5.5.0.5 establishes strict mathematical consistency for round-trip cost components:
$$C_{\text{round-trip}} = C_{\text{fee, entry}} + C_{\text{fee, exit}} + C_{\text{spread, entry}} + C_{\text{spread, exit}} + C_{\text{vol, entry}} + C_{\text{vol, exit}} + C_{\text{impact, entry}} + C_{\text{impact, exit}}$$

### Denominator Standard
- All cost components are measured as **basis points of trade notional value** ($N = Q \times P$) at the exact instant of execution.
- Entry costs are denominated relative to entry notional ($N_{\text{entry}} = Q \times P_{\text{entry}}$).
- Exit costs are denominated relative to exit notional ($N_{\text{exit}} = Q \times P_{\text{exit}}$).
- Portfolio net return is denominated relative to **total account equity** ($E_t$).

---

## 3. OPERATIONAL ROLE OF THE 20 BPS HURDLE

Is 20 bps a hard acceptance threshold, a conservative scenario, or both?
- **Gate 2 Mandatory Hurdle:** 20 bps is the formal, binding pass/fail filter for Gate 2. If a specialist's gross OOF expectancy does not exceed 20 bps, it fails Gate 2.
- **Secondary Sensitivity Sweeps:** 15 bps (VIP fee tier) and 30 bps (extreme volatility stress) are secondary parametric scenarios evaluated across Gates 3 to 6 to measure margin of safety.
- **Epistemic Warning:** The 20 bps hurdle is an engineered regulatory benchmark based on modeled retail taker fees; it is NOT an empirically validated measurement of realized exchange fills.

### Supervisor Recommendation
- Confirm `20 bps Conservative Tier` as the mandatory Gate 2 break-even hurdle.
- Status: `PENDING_HUMAN_DECISION`. Awaiting supervisor selection.
