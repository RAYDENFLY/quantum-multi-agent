# QUANTUM PHASE 5.5.0.3: SLIPPAGE COMPONENT DECOMPOSITION & AUDIT

**Document Status:** `APPROVED_FOR_DESIGN`  
**Publication Timestamp:** `2026-11-01 20:48:53 UTC`  
**Associated Deliverable:** Workstream D (Slippage Component Separation)  

---

## 1. COMPONENT DECOMPOSITION & SEPARATION OF OVERLAPS

Phase 5.5.0.2 established a three-term equation $S_{\text{trade}} = S_{\text{base}} + S_{\text{vol}} + S_{\text{liquidity}}$, where $S_{\text{base}}$ was loosely described as containing both half-spread and orderbook depth friction. This created potential overlap with the liquidity impact term.

Phase 5.5.0.3 establishes a strictly non-overlapping, orthogonal decomposition of transaction friction for marketable orders:
$$C_{\text{leg}} = C_{\text{spread}} + C_{\text{volatility}} + C_{\text{impact}} + C_{\text{fee}}$$

### Formal Definition of Each Term
1. **$C_{\text{spread}}$ (Bid-Ask Half-Spread Crossing):**
   - **Physical Mechanism:** Cost of crossing the prevailing top-of-book bid-ask spread at market arrival.
   - **Unit:** Dimensionless decimal return fraction per leg.
   - **Instrument Schedule:**
     - Tier 1 Majors (BTCUSDT, ETHUSDT): $1.0\text{ bps}$ ($0.00010$).
     - Tier 2 Mid-Caps (SOL, BNB, XRP, DOGE, LTC): $2.0\text{ bps}$ ($0.00020$).
     - Tier 3 High-Beta / Privacy (ADA, AVAX, LINK, XMR): $3.0\text{ bps}$ ($0.00030$).
   - **Overlap Resolution:** Strictly restricted to half-spread. Contains ZERO depth friction or participation impact.

2. **$C_{\text{volatility}}$ (Fast-Market Queue Depletion):**
   - **Physical Mechanism:** Spread widening and adverse limit-order queue shifts during volatile intervals.
   - **Formula:** $C_{\text{volatility}} = \alpha \times \sigma_t$.
   - **Units:** $\sigma_t$ is rolling 20-candle return standard deviation (dimensionless fraction, e.g. $0.0030 = 0.30\%$); $\alpha = 0.05$ (dimensionless multiplier).
   - **Result:** Dimensionless decimal return fraction ($0.05 \times 0.0030 = 0.00015 = 1.5\text{ bps}$).

3. **$C_{\text{impact}}$ (Order Participation Market Impact Proxy):**
   - **Physical Mechanism:** Temporary price depression or elevation caused by consuming available book depth.
   - **Formula:**
     $$C_{\text{impact}} = \beta \times \sqrt{\frac{N_{\text{order, USDT}}}{V_{\text{bar, USDT}}}}$$
   - **Units:** $\frac{N}{V}$ is the dimensionless volume participation ratio; $\beta = 0.0010 = 10\text{ bps}$ is a dimensionless decimal cost scaling coefficient.
   - **Status:** Explicitly classified as an **empirical proxy**, NOT a calibrated L2/L3 order book model (`UNVERIFIED_ASSUMPTION`).

4. **$C_{\text{fee}}$ (Exchange Taker Commission Fee):**
   - **Physical Mechanism:** Direct exchange fee charged on trade execution notional.
   - **Units:** Dimensionless decimal return fraction ($5.0\text{ bps} = 0.00050$ per leg base case; $6.0\text{ bps} = 0.00060$ conservative).

5. **$CF_{\text{fund}}$ (Financing Cash Flow):**
   - Evaluated orthogonally as a cash flow adjustment at discrete settlement timestamps via $CF_t = -d \times N_t \times f_t$. Never mixed into price slippage.

---

## 2. PRICE-SIDE CONSISTENCY & ADVERSE EXECUTION ADJUSTMENTS

A fundamental rule of market microstructure is that transaction frictions MUST always be adverse to the trader:
Let $C_{\text{exec}} = C_{\text{spread}} + C_{\text{volatility}} + C_{\text{impact}}$ be the total execution price slippage fraction.

### BUY Orders (LONG Entry or SHORT Exit)
- Market buy orders cross the ask. Fills occur at a HIGHER price than reference price:
  $$P_{\text{fill, buy}} = P_{\text{ref}} \times (1 + C_{\text{exec}})$$

### SELL Orders (LONG Exit or SHORT Entry)
- Market sell orders cross the bid. Fills occur at a LOWER price than reference price:
  $$P_{\text{fill, sell}} = P_{\text{ref}} \times (1 - C_{\text{exec}})$$

### Sign Symmetry Verification
- LONG Trade: Enters at $P_{\text{fill, entry}} = P_{\text{open}} \times (1 + C_{\text{exec}})$; Exits at $P_{\text{fill, exit}} = P_{\text{exit, ref}} \times (1 - C_{\text{exec}})$. Both adjustments reduce LONG PnL.
- SHORT Trade: Enters at $P_{\text{fill, entry}} = P_{\text{open}} \times (1 - C_{\text{exec}})$; Exits at $P_{\text{fill, exit}} = P_{\text{exit, ref}} \times (1 + C_{\text{exec}})$. Both adjustments reduce SHORT PnL.

---

## 3. COMPLETE SEPARATE HYPOTHETICAL LONG & SHORT VERIFICATIONS

Parameters:
- Order Notional $N = \$10,000.00$ USDT ($Q = 100$ units at $P = 100.00$).
- 5m Bar Volume $V = \$500,000.00$ USDT (Participation = 0.02, $\sqrt{0.02} \approx 0.141421$).
- Volatility $\sigma_t = 0.0030$ (0.30% return std).
- Slippage terms: $C_{\text{spread}} = 1.0\text{ bps}$, $C_{\text{volatility}} = 1.5\text{ bps}$, $C_{\text{impact}} = 1.414\text{ bps}$.
- Total execution slippage per leg: $C_{\text{exec}} = 1.0 + 1.5 + 1.414 = 3.914\text{ bps}$ ($0.0003914$).
- Taker fee per leg: $C_{\text{fee}} = 5.0\text{ bps}$ ($0.0005000$).

### Scenario 1: Hypothetical LONG Trade
1. **Entry Reference Price:** $P_{\text{ref, entry}} = 100.00$ USDT.
2. **Entry Fill Price (BUY):** $P_{\text{fill, entry}} = 100.00 \times (1 + 0.0003914) = 100.03914$ USDT.
3. **Exit Reference Price:** $P_{\text{ref, exit}} = 101.00$ USDT (market moved up 1.00%).
4. **Exit Fill Price (SELL):** $P_{\text{fill, exit}} = 101.00 \times (1 - 0.0003914) = 100.96047$ USDT.
5. **Gross Realized Price Gain:** $100.96047 - 100.03914 = +0.92133$ USDT ($+0.92133\%$).
6. **Frictionless Reference Gain:** $101.00 - 100.00 = +1.00000$ USDT ($+1.00000\%$).
7. **Execution Slippage Drag:** $1.00000\% - 0.92133\% = 0.07867\% = 7.867\text{ bps}$.
8. **Taker Commission Drag:** $5.0\text{ bps (entry)} + 5.0\text{ bps (exit)} = 10.0\text{ bps}$.
9. **Total Round-Trip Friction:** $7.867 + 10.0 = \mathbf{17.867\text{ bps}}$ ($0.0017867$).
10. **Net Realized PnL:** $+0.92133\% - 0.10000\% = +0.82133\%$ ($+\$82.13$ USDT).

### Scenario 2: Hypothetical SHORT Trade
1. **Entry Reference Price:** $P_{\text{ref, entry}} = 100.00$ USDT.
2. **Entry Fill Price (SELL):** $P_{\text{fill, entry}} = 100.00 \times (1 - 0.0003914) = 99.96086$ USDT.
3. **Exit Reference Price:** $P_{\text{ref, exit}} = 99.00$ USDT (market moved down 1.00%).
4. **Exit Fill Price (BUY):** $P_{\text{fill, exit}} = 99.00 \times (1 + 0.0003914) = 99.03875$ USDT.
5. **Gross Realized Price Gain:** $99.96086 - 99.03875 = +0.92211$ USDT ($+0.92211\%$).
6. **Frictionless Reference Gain:** $100.00 - 99.00 = +1.00000$ USDT ($+1.00000\%$).
7. **Execution Slippage Drag:** $1.00000\% - 0.92211\% = 0.07789\% = 7.789\text{ bps}$.
8. **Taker Commission Drag:** $5.0\text{ bps (entry)} + 5.0\text{ bps (exit)} = 10.0\text{ bps}$.
9. **Total Round-Trip Friction:** $7.789 + 10.0 = \mathbf{17.789\text{ bps}}$ ($0.0017789$).
10. **Net Realized PnL:** $+0.92211\% - 0.10000\% = +0.82211\%$ ($+\$82.21$ USDT).

---

## 4. NO DOUBLE-COUNTING PROOF

- $C_{\text{spread}}$ is strictly the top-of-book half spread.
- $C_{\text{volatility}}$ captures fast-market queue widening.
- $C_{\text{impact}}$ captures book depth participation penalty.
- $C_{\text{fee}}$ is broker/exchange commission.
- No component is deducted twice in either the LONG or SHORT execution pipelines.
