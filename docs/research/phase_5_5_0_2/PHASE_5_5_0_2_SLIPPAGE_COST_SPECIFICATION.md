# QUANTUM PHASE 5.5.0.2: SLIPPAGE AND COST SPECIFICATION

**Document Status:** `APPROVED_FOR_DESIGN`  
**Publication Timestamp:** `2026-11-01 20:41:45 UTC`  
**Associated Deliverable:** Workstream C (Slippage Dimensional Consistency)  

---

## 1. DIMENSIONAL SPECIFICATION & VARIABLE UNITS

Phase 5.5.0.2 establishes strict dimensional consistency for the OHLCV-derived slippage model:
$$S_{\text{trade}} = S_{\text{base}} + S_{\text{vol}} + S_{\text{liquidity}}$$
Plain text formula: S_trade = S_base + S_vol + S_liquidity

### Variable Definitions and Units
1. **Total Slippage ($S_{\text{trade}}$):** Dimensionless decimal fraction / return fraction per leg ($10^{-4} = 1\text{ bps}$).
2. **Base Slippage ($S_{\text{base}}$):** Dimensionless decimal fraction / return fraction per leg ($1.5\text{ bps} = 0.00015$ for BTC/ETH; $2.5\text{ bps} = 0.00025$ for mid-caps; $3.5\text{ bps} = 0.00035$ for high-beta).
3. **Volatility Slippage ($S_{\text{vol}} = \alpha \times \sigma_t$):**
   - $\sigma_t$ is the 5m simple return standard deviation (`ddof=1` over 20 candles), expressed as a Dimensionless decimal fraction (e.g. $0.0030 = 0.30\%$).
   - $\alpha$ is a dimensionless scaling factor (provisional assumption: alpha = 0.05).
   - Product $S_{\text{vol}}$ is a Dimensionless decimal fraction ($0.05 \times 0.0030 = 0.00015 = 1.5\text{ bps}$).
4. **Liquidity Slippage ($S_{\text{liquidity}} = \beta \times \sqrt{\text{Participation}}$):**
   - $\text{Notional}$: Quote currency value (USDT) of trade order.
   - $\text{Volume}$: 5m bar quote currency volume (USDT) from canonical Parquet (`quote_volume`).
   - $\text{Participation} = \frac{\text{Notional}_{\text{USDT}}}{\text{QuoteVolume}_{\text{USDT}}}$ is a dimensionless fraction.
   - $\beta$ has units of decimal return fraction / bps (provisional assumption: beta = 0.0010 = 10 bps).

---

## 2. CONCRETE HYPOTHETICAL DIMENSIONAL EXAMPLE

The following mathematical illustration demonstrates exact dimensional consistency using declared hypothetical values:

- **Order Notional:** $N = \$10,000.00$ USDT ($Q = 100$ contracts at arrival price $P_{\text{arrival}} = 100.00$ USDT).
- **5m Bar Quote Volume:** $V = \$500,000.00$ USDT.
- **Participation Ratio:** $\frac{N}{V} = \frac{10,000}{500,000} = 0.02$ ($2.0\%$ participation).
- **Square Root Participation:** $\sqrt{0.02} \approx 0.141421$.
- **20-Candle Return Volatility:** $\sigma_t = 0.0030$ ($0.30\%$ return std).

### Component Calculation (Per Leg)
$$S_{\text{base}} = 0.000150 \quad (1.50\text{ bps})$$
$$S_{\text{vol}} = 0.05 \times 0.0030 = 0.000150 \quad (1.50\text{ bps})$$
$$S_{\text{liquidity}} = 0.0010 \times 0.141421 = 0.000141 \quad (1.41\text{ bps})$$
$$S_{\text{trade, entry}} = 0.000150 + 0.000150 + 0.000141 = 0.000441 \quad (4.41\text{ bps per leg})$$
Result per leg: 4.41 bps

### Executed Fill Price (LONG Entry)
$$P_{\text{fill}} = P_{\text{arrival}} \times (1 + S_{\text{trade, entry}}) = 100.00 \times (1 + 0.000441) = 100.0441\text{ USDT}$$

### Full Round-Trip Transaction Drag
- Entry Taker Fee (5.0 bps): $0.000500$
- Exit Taker Fee (5.0 bps): $0.000500$
- Entry Slippage & Spread (4.41 bps): $0.000441$
- Exit Slippage & Spread (4.41 bps): $0.000441$
- **Total Round-Trip Friction:** $5.0 + 5.0 + 4.41 + 4.41 = \mathbf{18.82\text{ bps}}$ ($0.001882$).
Result round-trip: 18.82 bps

This matches the Conservative Cost Tier (20 bps round-trip) within 1.18 bps, verifying the realism of the Conservative Tier.

---

## 3. NO DOUBLE-COUNTING PROOF

A critical requirement of Phase 5.5.0.2 is establishing the NO DOUBLE-COUNTING PROOF:
- Double-counting occurs when a backtest applies BOTH a full bid-ask spread deduction AND an independent slippage penalty that already incorporates spread crossing.
- In the QUANTUM Phase 5.5.0.2 specification:
  1. $S_{\text{base}}$ explicitly subsumes half-spread crossing plus baseline order book depth friction.
  2. $S_{\text{vol}}$ captures spread widening and queue depletion during elevated volatility.
  3. $S_{\text{liquidity}}$ captures temporary price impact from order size relative to bar volume.
- **Governance Rule:** The economic execution engine applies $S_{\text{trade}}$ once at entry and once at exit. It NEVER deducts an additional standalone bid-ask spread cost on top of $S_{\text{trade}}$.
