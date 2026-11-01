# QUANTUM PHASE 5.5.0.8: TRANSACTION COST SPECIFICATION

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-01 21:25:00 UTC`  
**Associated Task:** Task B (Transaction Cost Decomposition)  
**Operational Mode:** `READ_ONLY_QUANTITATIVE_SPECIFICATION_AUDIT`  

---

## 1. CANONICAL CONVENTION: REFERENCE_PRICE_ACCOUNTING

To prevent double-counting of execution frictions, Phase 5.5 adopts one unambiguous accounting convention:

$$\mathbf{REFERENCE\_PRICE\_ACCOUNTING}$$

### Seven Invariant Rules
1. **Reference Price PnL:** Gross trading PnL is computed strictly from clean reference prices:
   $$\text{PnL}_{\text{gross}} = d \times Q \times (P_{\text{exit, ref}} - P_{\text{entry, ref}})$$
   where $P_{\text{entry, ref}} = \text{open}[i+1]$ and $P_{\text{exit, ref}} = P_{\text{barrier}}$.
2. **Explicit Fee Calculation:** Exchange taker fees are computed independently:
   $$C_{\text{fee}} = N_{\text{entry}} f_{\text{taker, entry}} + N_{\text{exit}} f_{\text{taker, exit}}$$
3. **Explicit Spread Friction:** Bid-ask spread cost is computed independently:
   $$C_{\text{spread}} = N_{\text{entry}} s_{\text{leg, entry}} + N_{\text{exit}} s_{\text{leg, exit}}$$
4. **Explicit Volatility Slippage:** Fast-market slippage buffer is computed independently:
   $$C_{\text{vol}} = N_{\text{entry}} v_{\text{leg, entry}} + N_{\text{exit}} v_{\text{leg, exit}}$$
5. **Explicit Market Impact:** Liquidity depletion impact is computed independently:
   $$C_{\text{impact}} = N_{\text{entry}} m_{\text{leg, entry}} + N_{\text{exit}} m_{\text{leg, exit}}$$
6. **Financing Cash Flow Isolation:** Funding rate cash flow ($CF_{\text{funding}}$) is strictly excluded from transaction costs and credited/debited directly to net PnL.
7. **Single Deduction Invariant:** Every friction component is deducted exactly once. Prices are never slipped prior to gross PnL calculation.

---

## 2. CANONICAL DENOMINATOR STANDARDIZATION (B1)

When normalizing dollar frictions into basis points for portfolio comparison, the standard denominator is **Entry Notional**:

$$C_{\text{transaction, normalized}} = \frac{C_{\text{transaction, USDT}}}{N_{\text{entry}}}$$

where $N_{\text{entry}} = Q \times P_{\text{entry}}$.

Expanding all components:
$$C_{\text{transaction, normalized}} = \sum_{\text{friction}} c_{\text{leg, entry}} + \left(1 + \frac{P_{\text{exit}} - P_{\text{entry}}}{P_{\text{entry}}}\right) \sum_{\text{friction}} c_{\text{leg, exit}}$$

---

## 3. SPREAD CONVENTION & HALF-SPREAD DISTINCTION (B2)

We formally distinguish full spread from half-spread per leg:

- **Full Bid-Ask Spread ($S$):** The difference between the lowest ask and the highest bid in the orderbook: $S = P_{\text{ask}} - P_{\text{bid}}$.
- **Half-Spread per Leg ($s_{\text{leg}}$):** The cost incurred by crossing the spread from the midpoint:
  $$s_{\text{leg}} = \frac{S}{2 P_{\text{mid}}}$$
- **Round-Trip Spread Cost:** Sum of crossing the spread at entry and exit:
  $$s_{\text{round-trip}} = s_{\text{leg, entry}} + s_{\text{leg, exit}} = \frac{S_{\text{entry}}}{2 P_{\text{entry}}} + \frac{S_{\text{exit}}}{2 P_{\text{exit}}}$$

**Audit of Phase 5.5.0.6 Scenario Table:**
In `PHASE_5_5_0_6_DEC_04_COST_SCENARIO_DEFINITION.md`, the spread term is listed as:
`Entry / Exit Spread: 1.0 bps / leg (2.0 bps total)`
This confirms that the documented scenario value ($1.0$ bps) refers to **half-spread per leg**, resulting in a $2.0$ bps round-trip spread friction.

---

## 4. SLIPPAGE & MARKET IMPACT ACCOUNTING MATRIX (B3)

| Friction Component | Nominal Leg Rate (Scenario 2 Baseline) | Applied To | Accounting Treatment | Double-Counting Danger | Governance Rule |
|---|---|---|---|---|---|
| **Exchange Taker Fee** | $5.0$ bps / leg ($10.0$ bps total) | $N_{\text{entry}}$ and $N_{\text{exit}}$ | Deducted from PnL | None | Standard exchange fee schedule. |
| **Bid-Ask Spread** | $1.0$ bps / leg ($2.0$ bps total) | $N_{\text{entry}}$ and $N_{\text{exit}}$ | Deducted from PnL | High (if fill price slipped) | Never slip $P_{\text{entry}}$ by spread. |
| **Volatility Slippage** | $1.5$ bps / leg ($3.0$ bps total) | $N_{\text{entry}}$ and $N_{\text{exit}}$ | Deducted from PnL | High (if fill price slipped) | Never slip $P_{\text{entry}}$ by volatility. |
| **Market Impact** | $2.5$ bps / leg ($5.0$ bps total) | $N_{\text{entry}}$ and $N_{\text{exit}}$ | Deducted from PnL | High (if fill price slipped) | Never slip $P_{\text{entry}}$ by impact. |
| **Funding Cash Flow** | Exogenous settlement rate | $N_{\text{settle}}$ | Direct balance cash flow | Moderate (if added to bps) | Never include funding in cost bps. |

---

## 5. COST SCENARIO RECONCILIATION (B4)

The three candidate cost scenarios (15, 20, 30 bps round-trip) represent:

- **Nominal Leg-Sum Assumptions:** Sum of nominal entry leg friction and exit leg friction ($c_{\text{leg, entry}} + c_{\text{leg, exit}}$).
- **Classification:** `REQUIRES_HUMAN_DECISION` (DEC_04).
- The human supervisor will select whether 20 bps is the binding Gate 2 hurdle or whether all three scenarios must be satisfied.
