# QUANTUM PHASE 5.5.0.1: SLIPPAGE AND MARKET IMPACT DIMENSIONAL AUDIT

**Document Status:** `VERIFIED_WITH_LIMITATIONS`  
**Publication Timestamp:** `2026-11-01 20:29:46 UTC`  
**Associated Deliverable:** Workstream B (Slippage, Spread, and Market Impact)  

---

## 1. DIMENSIONAL AND UNIT AUDIT OF THE SLIPPAGE MODEL

Phase 5.5.0 proposed the parametric slippage model:
$$S_{\text{trade}} = S_{\text{base}} + S_{\text{vol}} + S_{\text{liquidity}}$$

Phase 5.5.0.1 audits each variable for strict dimensional and scale consistency:

| Variable | Mathematical Definition | Physical Unit | Scale / Type | Validated Dimensional Treatment |
|---|---|---|---|---|
| $S_{\text{trade}}$ | Total execution slippage per leg | Decimal fraction / bps | Decimal (e.g. $0.00025 = 2.5$ bps) | Dimensionless fraction of trade price. Applied as $P_{\text{fill}} = P_{\text{arrival}} \times (1 \pm S_{\text{trade}})$. |
| $S_{\text{base}}$ | Constant minimum half-spread | Decimal fraction / bps | Decimal (e.g. $0.00015 = 1.5$ bps) | Asset-specific baseline half-spread: 1.5 bps for BTC/ETH; 2.5 bps mid-caps; 3.5 bps high-beta. |
| $\alpha$ | Volatility scaling coefficient | Dimensionless scalar | Float (e.g. $0.05$) | Dimensionless multiplier mapping return volatility into slippage fraction. |
| $\sigma_t$ | 20-candle return volatility | Decimal fraction | Float (e.g. $0.0030 = 0.30\%$) | Standard deviation of 5m simple percentage returns (`ddof=1`). |
| $S_{\text{vol}}$ | $\alpha \times \sigma_t$ | Decimal fraction / bps | Decimal (e.g. $0.05 \times 0.003 = 1.5$ bps) | Dimensionally consistent decimal fraction. |
| $\beta$ | Market impact scaling coefficient | Decimal fraction / bps | Float (e.g. $0.0010 = 10$ bps) | Must carry units of decimal fraction / bps to ensure product is dimensionless fraction. |
| $\text{Notional}$ | Trade order notional value | Quote currency (USDT) | Positive float (e.g. \$10,000 USDT) | Order size in USDT. |
| $\text{Volume}$ | 5m bar volume notional | Quote currency (USDT) | Positive float (e.g. \$500,000 USDT) | From canonical `quote_volume`. Guarantees $\text{Notional} / \text{Volume}$ is dimensionless participation rate. |
| $S_{\text{liquidity}}$ | $\beta \times \sqrt{\frac{\text{Notional}}{\text{Volume}}}$ | Decimal fraction / bps | Decimal (e.g. $0.0010 \times \sqrt{0.02} \approx 1.4$ bps) | Dimensionally consistent decimal fraction. |

---

## 2. DECOUPLING OF EXECUTION FRICTION COMPONENTS

To avoid double-counting and economic distortion, the six execution frictions are strictly distinguished:

1. **Bid-Ask Spread Cost ($C_{\text{spread}}$):** The mechanical cost of crossing from bid to ask on a market order. Represented by $S_{\text{base}}$.
2. **Execution Slippage ($C_{\text{slip}}$):** Price movement between decision timestamp and execution timestamp caused by market drift. Represented by $S_{\text{vol}}$.
3. **Market Impact ($C_{\text{impact}}$):** Adverse orderbook price concession caused by order size consuming liquidity. Represented by $S_{\text{liquidity}}$.
4. **Taker Fee ($C_{\text{taker}}$):** Contractual exchange fee charged for removing liquidity (e.g. 5.0 to 6.0 bps).
5. **Maker Fee / Rebate ($C_{\text{maker}}$):** Contractual exchange fee or rebate for providing passive liquidity (e.g. -0.5 to +2.0 bps).
6. **Adverse Selection ($C_{\text{adverse}}$):** Post-fill adverse price drift experienced by filled limit orders.

---

## 3. PROVISIONAL SENSITIVITY SCENARIO SPECIFICATION

The 7, 15, 20, and 30 bps round-trip scenarios are classified as **provisional sensitivity scenarios** (`UNVERIFIED_ASSUMPTION`):
- They must NOT be described as verified exchange execution costs.
- They serve as stress-testing bounds to evaluate strategy fragility against increasing transaction drag.
