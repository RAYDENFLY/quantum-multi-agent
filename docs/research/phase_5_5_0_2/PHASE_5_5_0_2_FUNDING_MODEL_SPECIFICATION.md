# QUANTUM PHASE 5.5.0.2: FUNDING MODEL SPECIFICATION

**Document Status:** `APPROVED_FOR_DESIGN`  
**Publication Timestamp:** `2026-11-01 20:41:45 UTC`  
**Associated Deliverable:** Workstream B (Funding Rate Unit Reconciliation)  

---

## 1. UNIT RECONCILIATION & STANDARDIZATION

Phase 5.5.0.2 resolves previous unit inconsistencies by establishing one authoritative standard unit:

### Primary Unit Convention
The standard unit across all Phase 5.5 specifications is:
`funding_rate_bps_per_settlement`
Funding rate is measured as **basis points per 8-hour settlement window** ($1\text{ bps} = 0.01\% = 0.0001$).

### Nominal Annualized Conversion Formula
For standard cryptocurrency perpetual futures contracts with 3 settlement events per 24 hours (every 8 hours at `00:00`, `08:00`, and `16:00 UTC`):
$$F_{\text{bps,annual}} = F_{\text{bps,settlement}} \times 3 \times 365 = F_{\text{bps,settlement}} \times 1095$$
$$F_{\text{pct,annual}} = F_{\text{bps,settlement}} \times 0.1095\%$$

This is a nominal annualized scaling convention for reporting, NOT an empirical claim about realized historical funding.

---

## 2. MATHEMATICAL CASH FLOW FORMULATION

For any open position held across a funding settlement timestamp $t_{\text{settle}} \in \{00:00, 08:00, 16:00\text{ UTC}\}$:
$$CF_t = -d \times N_t \times f_t$$
In plain text: CF_t = -d * N_t * f_t
where:
- $d = +1$ for LONG positions.
- $d = -1$ for SHORT positions.
- $N_t$ is the active quote notional in USDT at timestamp $t_{\text{settle}}$ ($N_t = Q_t \times P_{\text{mark}, t}$).
- $f_t$ is the decimal funding rate ($f_t = F_{\text{bps,settlement}} / 10,000$).

### Strict Sign and Direction Rules
- **Positive Funding Rate ($f_t > 0$):** Perp trades at a premium to spot. Long positions PAY funding ($CF_t < 0$); Short positions RECEIVE funding ($CF_t > 0$).
- **Negative Funding Rate ($f_t < 0$):** Perp trades at a discount to spot. Long positions RECEIVE funding ($CF_t > 0$); Short positions PAY funding ($CF_t < 0$).

### Holding Period Overlap Analysis
- Triple-barrier positions have a maximum holding duration of $H = 12$ bars ($60$ minutes).
- A position opened at candle $i$ only crosses a funding settlement if $t_{\text{settle}} \in [t_{\text{entry}}, t_{\text{exit}}]$.
- With 8-hour settlement intervals (480 minutes), exactly $60 / 480 = 12.5\%$ of trades cross a funding timestamp.
- The remaining 87.5% of trades enter and exit between funding timestamps, incurring exactly zero funding cash flow.

---

## 3. ABSENCE OF EMPIRICAL FUNDING DATA

- Forensic audit confirms historical funding rates are **absent** from canonical Parquet data (`FUNDING_DATA_UNAVAILABLE`).
- **Governance Rule:** The absence of empirical data must NEVER be replaced with zero funding. Parametric sensitivity scenarios are strictly classified as **`UNVERIFIED_ASSUMPTION`**.
