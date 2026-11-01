# QUANTUM PHASE 5.5.0.6: DEC_04 COST SCENARIO SPECIFICATION

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-01 21:09:14 UTC`  
**Associated Deliverable:** Workstream C (DEC_04 Cost Scenario Definition)  

---

## 1. COST SCENARIO SPECIFICATION & COMPONENT DECOMPOSITION

A transaction cost scenario represents an exogenous modeled friction budget ($C_{\text{round-trip, scenario}}$). Every scenario specifies all 8 orthogonal execution terms:
$$C_{\text{round-trip}} = C_{\text{fee, entry}} + C_{\text{fee, exit}} + C_{\text{spread, entry}} + C_{\text{spread, exit}} + C_{\text{vol, entry}} + C_{\text{vol, exit}} + C_{\text{impact, entry}} + C_{\text{impact, exit}}$$

### Strict Exclusion of Funding Cash Flows
- **Governance Rule:** Funding cash flows are strictly **EXCLUDED** from $C_{\text{round-trip}}$.
- **Reason:** Funding is a financing cash flow that occurs at discrete 8-hour settlement timestamps, not an execution friction incurred upon crossing the bid-ask spread.

### Canonical Denominator Standard
- All cost basis points are denominated relative to **trade notional value at execution** ($N = Q \times P$).
- Entry friction in USDT: $C_{\text{entry, USDT}} = N_{\text{entry}} \times C_{\text{leg, entry}}$, where $N_{\text{entry}} = Q \times P_{\text{entry}}$.
- Exit friction in USDT: $C_{\text{exit, USDT}} = N_{\text{exit}} \times C_{\text{leg, exit}}$, where $N_{\text{exit}} = Q \times P_{\text{exit}}$.

---

## 2. THE THREE CANDIDATE COST SCENARIOS

| Scenario Name | Round-Trip Cost | Entry / Exit Fee | Entry / Exit Spread | Volatility Penalty | Market Impact Proxy | Microstructure Profile |
|---|---|---|---|---|---|---|
| **15 bps Scenario (Base)** | 15.0 bps ($0.00150$) | 2.5 bps / leg (5.0 bps total) | 1.0 bps / leg (2.0 bps total) | 1.5 bps / leg (3.0 bps total) | 2.5 bps / leg (5.0 bps total) | Institutional VIP taker fee tier, tight liquid top-of-book spreads. |
| **20 bps Scenario (Conservative)** | 20.0 bps ($0.00200$) | 5.0 bps / leg (10.0 bps total) | 1.0 bps / leg (2.0 bps total) | 1.5 bps / leg (3.0 bps total) | 2.5 bps / leg (5.0 bps total) | Standard retail taker fee tier (10 bps) + modeled dynamic spread/impact buffer (10 bps). |
| **30 bps Scenario (Severe Stress)** | 30.0 bps ($0.00300$) | 6.0 bps / leg (12.0 bps total) | 2.0 bps / leg (4.0 bps total) | 3.0 bps / leg (6.0 bps total) | 4.0 bps / leg (8.0 bps total) | Elevated retail fees, wide altcoin spreads, and fast-market volatility blowouts. |

---

## 3. SEPARATION FROM ACCEPTANCE HURDLES

- A cost scenario is an assumed simulation condition.
- An acceptance hurdle (Gate 2) is a mandatory statistical pass/fail filter.
- The supervisor may approve 20 bps as a scenario, as the Gate 2 hurdle, or adopt multi-scenario reporting.
- Status: `PENDING_HUMAN_DECISION`.
