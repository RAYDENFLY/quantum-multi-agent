# QUANTUM PHASE 5.5.0: FUNDING AND SLIPPAGE SPECIFICATION

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-01 20:23:18 UTC`  
**Associated Deliverable:** Workstream D (Funding Rate Model) & Workstream E (Slippage Model)  

---

## 1. PERPETUAL FUTURES FUNDING RATE MODEL

Perpetual futures contracts utilize periodic funding payments to tether the perpetual contract price to the underlying spot index.

### Funding Mechanics & Cash Flow Formula
Funding payments occur at discrete settlement timestamps (typically every 8 hours: `00:00`, `08:00`, and `16:00 UTC`).
For an active position holding notional value $N_t = Q_t \times P_{\text{mark}, t}$ at funding timestamp $t_{\text{fund}}$:
$$\text{CashFlow}_{\text{fund}} = -1 \times \text{Direction} \times N_t \times F_t$$
where:
- $\text{Direction} = +1$ for LONG, $-1$ for SHORT.
- $F_t$ is the 8-hour funding rate (expressed as a decimal fraction).
- If $F_t > 0$ (perp trading at a premium to spot): Longs PAY Shorts.
- If $F_t < 0$ (perp trading at a discount to spot): Shorts PAY Longs.

### Repository Audit Finding: `FUNDING_DATA_UNAVAILABLE`
Forensic audit of `data/historical/canonical/` confirmed that historical funding rates are **NOT stored** in canonical parquet datasets.
Because triple-barrier positions have a maximum holding horizon of 12 bars (60 minutes), only a fraction of trades cross an 8-hour funding boundary:
$$\text{Probability of crossing funding timestamp} \approx \frac{60 \text{ minutes}}{480 \text{ minutes}} = 12.5\%$$

### Parametric Funding Rate Sensitivity Protocol
Until an audited historical funding dataset is acquired, Phase 5.5 executes a four-scenario parametric funding sweep:
1. **Neutral Funding Scenario:** $F_t = 0.0\%$ (baseline).
2. **Standard Bull Market Drag (Longs Pay):** $F_t = +0.01\%$ per 8h (+10.95% annualized).
3. **Aggressive Bull Market Drag (Longs Pay):** $F_t = +0.03\%$ per 8h (+32.85% annualized).
4. **Bear Market Discount (Shorts Pay):** $F_t = -0.01\%$ per 8h (-10.95% annualized).

---

## 2. DYNAMIC SLIPPAGE AND MARKET IMPACT MODEL

Because tick-level orderbook snapshots are unavailable in the repository, Phase 5.5 establishes an **OHLCV-derived dynamic slippage model** based on empirical microstructure principles (Hasbrouck, Almgren-Chriss).

### Slippage Formulation
$$S_{\text{trade}} = S_{\text{base}} + S_{\text{vol}} + S_{\text{liquidity}}$$

1. **Base Slippage ($S_{\text{base}}$):**
   - Constant minimum bid-ask half-spread: $1.5$ bps for major pairs (BTC, ETH); $2.5$ bps for mid-caps (SOL, BNB, XRP, DOGE, LTC); $3.5$ bps for high-beta pairs (ADA, AVAX, LINK, XMR).
2. **Volatility-Adjusted Slippage ($S_{\text{vol}}$):**
   $$S_{\text{vol}} = \alpha \times \sigma_t$$
   where $\sigma_t$ is the causal 20-candle return volatility and $\alpha = 0.05$. Slippage expands linearly during elevated volatility regimes.
3. **Liquidity / Market Impact Slippage ($S_{\text{liquidity}}$):**
   $$S_{\text{liquidity}} = \beta \times \left( \frac{\text{Order Notional}}{\text{5m Volume Notional}} \right)^{0.5}$$
   where $\beta = 0.10$. With standard retail trade size (e.g. \$10,000 notional) against typical 5m volumes (> \$500,000), participation rate is < 2%, keeping market impact below 1.5 bps.

### Stress Slippage Floor
Under Severe Stress (Tier 4), slippage is bounded below by a hard floor of $7.0$ bps per leg ($14.0$ bps round-trip).
