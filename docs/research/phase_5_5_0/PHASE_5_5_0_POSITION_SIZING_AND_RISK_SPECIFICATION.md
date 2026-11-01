# QUANTUM PHASE 5.5.0: POSITION SIZING AND RISK SPECIFICATION

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-01 20:23:18 UTC`  
**Associated Deliverable:** Workstream F (Position Sizing and Risk Model)  

---

## 1. CAPITAL ALLOCATION AND RISK MODEL

Economic evaluation requires translating unitless classification signals into realistic, risk-managed portfolio positions.

### Account Equity & Margin Definitions
- **Account Equity ($E_t$):** Current total account liquidation value in USDT.
- **Fixed Fractional Risk Per Trade ($f_{\text{risk}}$):** Capped at $1.0\%$ ($0.01$) of current equity.
- **Stop-Loss Distance ($d_{\text{SL}}$):** Defined by the causal triple-barrier width: $d_{\text{SL}} = 1.5 \times \sigma_t$.

### Position Sizing Formula (Volatility Invariant)
$$\text{Position Notional } N_i = \frac{E_t \times f_{\text{risk}}}{d_{\text{SL}}} = \frac{E_t \times 0.01}{1.5 \times \sigma_t}$$
Under this formulation:
- Higher market volatility ($\sigma_t$) automatically scales DOWN position size.
- Lower market volatility scales UP position size.
- Every trade risks exactly $1.0\%$ of account equity to its Stop Loss barrier, ensuring equal dollar risk across diverse assets.

---

## 2. PORTFOLIO-LEVEL EXPOSURE & CONCURRENCY CONTROLS

Because 11 independent specialist agents operate in parallel, simultaneous signals can create aggregate over-exposure.

### Strict Portfolio Risk Guardrails
1. **Maximum Concurrent Positions:** Maximum $3$ active positions across the entire 11-instrument fleet.
2. **Maximum Aggregate Gross Leverage:** Gross notional exposure $\sum N_i$ must not exceed $3.0 \times E_t$.
3. **Maximum Instrument Allocation:** No single instrument may exceed $35\%$ of portfolio equity in initial margin.
4. **Daily Loss Circuit Breaker:** If cumulative portfolio drawdown exceeds $3.0\%$ within any rolling 24-hour window, all trading halts for 24 hours (`CIRCUIT_BREAKER_HALT`).
5. **Maximum Drawdown Hard Stop:** If total equity drawdown from peak exceeds $15.0\%$, the economic test terminates (`FAILED_MAX_DRAWDOWN_BREACH`).

### Concurrency Priority Queue
When more than 3 specialists trigger simultaneous entry signals at candle $i+1$:
1. Signals are ranked by calibrated confidence score: $\Delta P = P(\text{Signal}) - P(\text{Opposite})$.
2. The top 3 ranked instruments are allocated positions.
3. Remaining lower-ranked signals are logged as `REJECTED_CONCURRENCY_CAPACITY_EXCEEDED` and discarded.
