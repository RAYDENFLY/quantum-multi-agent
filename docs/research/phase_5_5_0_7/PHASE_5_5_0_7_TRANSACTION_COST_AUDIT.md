# QUANTUM PHASE 5.5.0.7: TRANSACTION COST MATHEMATICAL AUDIT

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-01 21:20:00 UTC`  
**Associated Task:** Task A (Transaction Cost Mathematical Audit)  
**Operational Mode:** `READ_ONLY_VERIFICATION`  

---

## 1. EXECUTION NOTIONAL DIMENSIONALITY & ASYMMETRY (A1)

In cryptocurrency perpetual futures execution, transaction notionals are determined at the point of order filling:

$$\text{Entry Notional:} \quad N_{\text{entry}} = Q_{\text{entry}} P_{\text{entry}}$$
$$\text{Exit Notional:} \quad N_{\text{exit}} = Q_{\text{exit}} P_{\text{exit}}$$

where $Q$ represents contract quantity in base asset units (e.g., BTC) and $P$ represents execution fill price in quote units (USDT).

### Mathematical Verification of Notional Disparity
1. **Quantity Symmetry:** In the frozen QUANTUM research architecture (Phase 5.3 and Phase 5.5 triple-barrier specification), all barrier exits (upper target, lower stop, or 288-bar horizon timeout) execute the entire position with zero partial scaling:
   $$Q_{\text{exit}} = Q_{\text{entry}} = Q$$
   *Verification Status:* `MATHEMATICALLY_VERIFIED` under full-exit policy; `PASS_WITH_LIMITATIONS` if partial fills occur in real-market execution.
2. **Price Disparity & Notional Asymmetry:** Because $P_{\text{exit}} = P_{\text{entry}}(1 + r_{\text{price}})$, where $r_{\text{price}} = d \times (P_{\text{exit}} - P_{\text{entry}}) / P_{\text{entry}}$, the exit notional differs from entry notional whenever price changes:
   $$N_{\text{exit}} = Q P_{\text{entry}}(1 + r_{\text{price}}) = N_{\text{entry}}(1 + r_{\text{price}})$$
3. **Implication for Fee Sizing:** If exchange fees are levied in USDT as a constant decimal rate $f_{\text{taker}}$ per leg:
   $$C_{\text{fee, USDT}} = N_{\text{entry}} f_{\text{entry}} + N_{\text{exit}} f_{\text{exit}} = N_{\text{entry}} [f_{\text{entry}} + f_{\text{exit}}(1 + r_{\text{price}})]$$
   When normalized by entry notional $N_{\text{entry}}$:
   $$\frac{C_{\text{fee, USDT}}}{N_{\text{entry}}} = f_{\text{entry}} + f_{\text{exit}} + f_{\text{exit}} r_{\text{price}}$$
   - On a winning trade ($r_{\text{price}} > 0$), exit fee in USDT is higher, increasing realized cost in basis points of entry notional.
   - On a losing trade ($r_{\text{price}} < 0$), exit fee in USDT is lower, reducing realized cost in basis points of entry notional.

---

## 2. FEE CALCULATION & SCENARIO CONVENTIONS (A2)

Phase 5.5.0.6 documents candidate cost scenarios of 15, 20, and 30 basis points round-trip. We audit the mathematical convention governing these numbers.

### Distinguishing the Three Possible Conventions
1. **Convention 1 (Fixed Assumption on Entry Notional):**
   $$C_{\text{round-trip, USDT}} = N_{\text{entry}} \times c_{\text{round-trip, bps}} \times 10^{-4}$$
   Here, 15 bps implies exactly $0.0015 \times N_{\text{entry}}$, regardless of price path.
2. **Convention 2 (Sum of Nominal Leg Rates):**
   $$c_{\text{round-trip}} = c_{\text{leg, entry}} + c_{\text{leg, exit}}$$
   where each leg rate applies to that leg's actual execution notional:
   $$C_{\text{transaction, USDT}} = N_{\text{entry}} c_{\text{leg, entry}} + N_{\text{exit}} c_{\text{leg, exit}}$$
3. **Convention 3 (Effective Realized Bps Normalized to Entry Notional):**
   $$c_{\text{effective, bps}} = \frac{C_{\text{transaction, USDT}}}{N_{\text{entry}}} \times 10^4 = c_{\text{leg, entry}} + c_{\text{leg, exit}} \left(1 + \frac{P_{\text{exit}} - P_{\text{entry}}}{P_{\text{entry}}}\right)$$

### Forensic Audit of Phase 5.5.0.6 Documents
- In `PHASE_5_5_0_6_DEC_04_COST_SCENARIO_DEFINITION.md`, the 15, 20, and 30 bps scenarios are defined by breaking down nominal leg rates (e.g. 15 bps = 7.5 bps entry leg + 7.5 bps exit leg).
- In `PHASE_5_5_0_6_HYPOTHETICAL_COST_EXAMPLE.md`, the numerical walkthrough demonstrates **Convention 2**:
  - Entry leg friction: $10,000.00 \times 0.00075 = \$7.50$ USDT.
  - Exit leg friction: $10,150.00 \times 0.00075 = \$7.61$ USDT.
  - Total friction: $\$15.11$ USDT.
  - Realized normalized bps: $15.11$ bps (which is Convention 3 evaluated from Convention 2).
- **Audit Conclusion:** The scenarios are **Nominal Leg-Sum Assumptions (Convention 2)** whose realized cost normalized to entry notional varies slightly with return (Convention 3). They are NOT fixed flat cash fees.

---

## 3. SPREAD, SLIPPAGE, AND MARKET IMPACT AUDIT (A3)

We investigate potential double-counting between execution fill prices and fee deductions.

### The Double-Counting Risk
There are two valid, mutually exclusive accounting methods for execution frictions:
1. **Fill-Price Accounting (Net Price Method):**
   - Frictions are embedded directly into execution prices:
     $$P_{\text{entry, fill}} = P_{\text{entry, ref}} + d \times (\text{half-spread} + \text{impact} + \text{slippage})$$
     $$P_{\text{exit, fill}} = P_{\text{exit, ref}} - d \times (\text{half-spread} + \text{impact} + \text{slippage})$$
   - Only pure exchange taker fees are deducted explicitly as cash outflows.
2. **Reference-Price Accounting (Gross Price + Cash Fee Method):**
   - Both entry and exit prices remain clean mid/reference prices: $P_{\text{entry}} = P_{\text{entry, ref}}$ and $P_{\text{exit}} = P_{\text{exit, ref}}$.
   - Gross PnL is computed from reference prices.
   - All frictions (fees, bid-ask spread, volatility buffer, and market impact) are bundled into $C_{\text{transaction, USDT}}$ and deducted as a cash friction.

### Inconsistency in Phase 5.5.0.6 Documentation
- `PHASE_5_5_0_6_DEC_01_ESTIMAND_CLARIFICATION.md` states:
  $$P_{\text{entry}} = \text{open}[i+1] \pm C_{\text{exec}}$$
  which implies Fill-Price Accounting.
- `PHASE_5_5_0_6_DEC_04_COST_SCENARIO_DEFINITION.md` and `PHASE_5_5_0_6_HYPOTHETICAL_COST_EXAMPLE.md` state:
  $$\text{PnL}_{\text{gross}} = d \times Q \times (P_{\text{exit, ref}} - P_{\text{entry, ref}})$$
  $$C_{\text{round-trip}} = C_{\text{fee}} + C_{\text{spread}} + C_{\text{vol}} + C_{\text{impact}}$$
  which implies Reference-Price Accounting.
- **CRITICAL WARNING:** If an engineer implements both (i.e. slips the execution price AND subtracts spread/impact in the fee formula), bid-ask spread and market impact are **double-counted**, imposing an artificial 30 to 60 bps penalty.
- **Enforced Standard for Phase 5.5:** Reference-Price Accounting must be strictly enforced. All models use clean reference prices ($P_{\text{entry}} = \text{open}[i+1]$, $P_{\text{exit}} = P_{\text{barrier}}$), and the full 8-component friction is deducted exclusively in $C_{\text{transaction}}$.

---

## 4. DIMENSIONAL AUDIT TABLE (A4)

| Component | Formula | Denominator | Unit | Verification Status | Notes / Limitations |
|---|---|---|---|---|---|
| **Entry Notional** | $N_{\text{entry}} = Q \times P_{\text{entry}}$ | None (Base product) | USDT | `PASS` | Evaluated at candle $i+1$ open. |
| **Exit Notional** | $N_{\text{exit}} = Q \times P_{\text{exit}}$ | None (Base product) | USDT | `PASS` | Evaluated at barrier trigger price. |
| **Gross PnL** | $d \times Q \times (P_{\text{exit}} - P_{\text{entry}})$ | None (Cash flow) | USDT | `PASS` | Evaluated from reference prices. |
| **Gross Return** | $\frac{\text{PnL}_{\text{gross}}}{N_{\text{entry}}} = d \frac{P_{\text{exit}} - P_{\text{entry}}}{P_{\text{entry}}}$ | $N_{\text{entry}}$ | Dimensionless ratio | `PASS` | Standard return convention. |
| **Exchange Taker Fee** | $N_{\text{entry}} f_{\text{entry}} + N_{\text{exit}} f_{\text{exit}}$ | None (Cash fee) | USDT | `PASS` | Dynamic with price change. |
| **Bid-Ask Spread** | $N_{\text{entry}} s_{\text{entry}} + N_{\text{exit}} s_{\text{exit}}$ | None (Modeled cost) | USDT | `PASS_WITH_LIMITATIONS` | Modeled as cash friction; must not be embedded in $P$. |
| **Volatility Slippage** | $N_{\text{entry}} v_{\text{entry}} + N_{\text{exit}} v_{\text{exit}}$ | None (Modeled cost) | USDT | `PASS_WITH_LIMITATIONS` | Modeled as cash friction; must not be embedded in $P$. |
| **Market Impact** | $N_{\text{entry}} m_{\text{entry}} + N_{\text{exit}} m_{\text{exit}}$ | None (Modeled cost) | USDT | `PASS_WITH_LIMITATIONS` | Modeled as cash friction; must not be embedded in $P$. |
| **Total Transaction Cost** | $N_{\text{entry}} c_{\text{entry}} + N_{\text{exit}} c_{\text{exit}}$ | None (Cash fee) | USDT | `PASS` | Sum of all 8 leg components. |
| **Normalized Cost** | $\frac{C_{\text{transaction, USDT}}}{N_{\text{entry}}}$ | $N_{\text{entry}}$ | Decimal / bps | `PASS` | Standardized canonical denominator. |
| **Break-Even Hurdle** | $\frac{C_{\text{transaction}} - CF_{\text{funding}}}{N_{\text{entry}}}$ | $N_{\text{entry}}$ | Decimal / bps | `PASS` | Net non-negative requirement. |
