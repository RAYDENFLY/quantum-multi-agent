# QUANTUM PHASE 5.5.0.7: FUNDING CASH-FLOW AGGREGATION AUDIT

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-01 21:20:00 UTC`  
**Associated Task:** Task B (Funding Cash-Flow Aggregation)  
**Operational Mode:** `READ_ONLY_VERIFICATION`  

---

## 1. FUNDING MODEL CONVENTION & FORMULATION

Funding payments in cryptocurrency perpetual futures contracts are periodic financing cash flows exchanged between long and short contract holders to anchor futures mark prices to spot index prices.

### Canonical Formulation
The established repository standard is:

`funding_rate_bps_per_settlement`

For settlement event $t$ occurring at discrete timestamps (00:00, 08:00, 16:00 UTC), the signed cash flow received by the position is:

$$CF_t = -d \times N_{\text{settle}, t} \times f_{t, \text{decimal}}$$

where:
- $d = +1$ for LONG positions, $d = -1$ for SHORT positions.
- $N_{\text{settle}, t} = Q \times P_{\text{mark}, t}$ is the position mark notional at settlement timestamp $t$.
- $f_{t, \text{decimal}} = \frac{\text{funding\_rate\_bps\_per\_settlement}_t}{10,000}$ is the decimal funding rate.

Total aggregate funding cash flow across a trade holding period crossing $k$ discrete settlement events is:

$$CF_{\text{funding, total}} = \sum_{t=1}^k CF_t = -d \sum_{t=1}^k N_{\text{settle}, t} f_{t, \text{decimal}}$$

---

## 2. AUDIT OF THE SEVEN MANDATORY PROPERTIES

### Property 1: Positive Funding Rate Behavior ($f_t > 0$)
- **Long ($d = +1$):** $CF_t = -(+1) \times N_{\text{settle}, t} \times f_t = - N_{\text{settle}, t} f_t < 0$. Long pays cash.
- **Short ($d = -1$):** $CF_t = -(-1) \times N_{\text{settle}, t} \times f_t = + N_{\text{settle}, t} f_t > 0$. Short receives cash.
- *Status:* `MATHEMATICALLY_VERIFIED`.

### Property 2: Negative Funding Rate Behavior ($f_t < 0$)
- **Long ($d = +1$):** $CF_t = -(+1) \times N_{\text{settle}, t} \times (-|f_t|) = + N_{\text{settle}, t} |f_t| > 0$. Long receives cash.
- **Short ($d = -1$):** $CF_t = -(-1) \times N_{\text{settle}, t} \times (-|f_t|) = - N_{\text{settle}, t} |f_t| < 0$. Short pays cash.
- *Status:* `MATHEMATICALLY_VERIFIED`.

### Property 3: Position Eligibility at Settlement Timestamps
- Positions are subject to funding ONLY if they are active and open at the exact discrete settlement timestamp (e.g. 00:00:00, 08:00:00, or 16:00:00 UTC).
- **Intra-settlement trade:** A trade opened at 09:15 UTC and closed at 14:30 UTC crosses $k = 0$ settlement events. Total funding is strictly $CF_{\text{funding}} = 0$.
- *Status:* `SOURCE_VERIFIED` from domain exchange contracts; `MATHEMATICALLY_VERIFIED`.

### Property 4: Discrete Mark Notional Dynamic Evaluation
- If a position remains open across multiple settlements, $N_{\text{settle}, t} = Q \times P_{\text{mark}, t}$ must be re-evaluated using the prevailing mark price at each settlement $t$.
- Assuming constant entry notional $N_{\text{entry}}$ across all settlements introduces distortion if the asset has trended significantly during the holding period.
- *Status:* `MATHEMATICALLY_VERIFIED`.

### Property 5: Additive Aggregation Without Double Counting
- Cash flows across $k$ discrete events are additive: $CF_{\text{funding, total}} = \sum_{t=1}^k CF_t$.
- No compounding is applied during the trade, as funding payments are settled directly into the cash balance at each 8-hour timestamp.
- *Status:* `MATHEMATICALLY_VERIFIED`.

### Property 6: Strict Exclusion from Transaction Cost Bps
- Funding cash flow is a balance adjustment resulting from financing, NOT an execution friction resulting from bid-ask spread or taker fees.
- Funding must NEVER be added to $C_{\text{round-trip}}$. It enters net return via $\frac{CF_{\text{funding, total}}}{N_{\text{entry}}}$.
- *Status:* `SOURCE_VERIFIED` in Phase 5.5.0.6; `MATHEMATICALLY_VERIFIED`.

### Property 7: 1095 Annualization Factor as a Nominal Convention
- Perpetual futures funding is settled 3 times daily (every 8 hours), giving $3 \times 365 = 1095$ settlement events per non-leap year.
- Annualized rate: $f_{\text{annual, bps}} = f_{\text{settlement, bps}} \times 1095$.
- **Governance Qualification:** This is strictly an arithmetic nominal scaling convention for reporting comparison, NOT an investment forecast or compounding annual yield.
- *Status:* `SOURCE_VERIFIED`; `PASS_WITH_LIMITATIONS`.

---

## 3. SYNTHETIC NUMERICAL EXAMPLES

> [!NOTE]
> All numerical examples below are strictly **illustrative and synthetic**. They do NOT represent observed trading returns or exchange records.

### Synthetic Example 1: Multi-Settlement Long Trade Crossing 2 Events
- **Parameters:** LONG ($d = +1$), Quantity $Q = 2.0$ BTC.
- **Entry:** $P_{\text{entry}} = \$60,000$, $N_{\text{entry}} = \$120,000$. Open at 06:00 UTC.
- **Settlement 1 (08:00 UTC):** Mark price $P_{\text{mark}, 1} = \$61,000$, Rate $f_1 = +2.5$ bps ($+0.00025$).
  $$N_{\text{settle}, 1} = 2.0 \times 61,000 = \$122,000$$
  $$CF_1 = -(+1) \times 122,000 \times 0.00025 = -\$30.50 \text{ USDT (Paid)}$$
- **Settlement 2 (16:00 UTC):** Mark price $P_{\text{mark}, 2} = \$62,500$, Rate $f_2 = -1.0$ bps ($-0.00010$).
  $$N_{\text{settle}, 2} = 2.0 \times 62,500 = \$125,000$$
  $$CF_2 = -(+1) \times 125,000 \times (-0.00010) = +\$12.50 \text{ USDT (Received)}$$
- **Exit:** Closed at 18:00 UTC at $P_{\text{exit}} = \$63,000$.
- **Total Aggregate Funding:**
  $$CF_{\text{funding, total}} = -30.50 + 12.50 = -\$18.00 \text{ USDT}$$
- **Normalized Funding Impact on Trade:**
  $$\frac{CF_{\text{funding, total}}}{N_{\text{entry}}} = \frac{-18.00}{120,000} = -0.00015 = -1.50 \text{ bps}$$

### Synthetic Example 2: Intra-Settlement Trade (Zero Funding)
- **Parameters:** SHORT ($d = -1$), Quantity $Q = 50.0$ ETH.
- **Entry:** Open at 09:30 UTC, $P_{\text{entry}} = \$3,000$, $N_{\text{entry}} = \$150,000$.
- **Exit:** Closed at 14:45 UTC, $P_{\text{exit}} = \$2,950$, $N_{\text{exit}} = \$147,500$.
- **Settlement Events Crossed:** $k = 0$ (No 00:00, 08:00, or 16:00 boundary crossed).
- **Total Aggregate Funding:** $CF_{\text{funding, total}} = \$0.00$ USDT ($0.0$ bps).
