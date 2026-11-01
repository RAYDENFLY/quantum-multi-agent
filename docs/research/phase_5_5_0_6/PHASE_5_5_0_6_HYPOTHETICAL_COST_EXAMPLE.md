# QUANTUM PHASE 5.5.0.6: TRANSPARENT HYPOTHETICAL COST WALKTHROUGH

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-01 21:09:14 UTC`  
**Associated Deliverable:** Workstream C (Numerical Walkthrough)  

---

## 1. STANDARDIZED NOTIONAL DENOMINATOR WALKTHROUGH

The following mathematical walkthrough demonstrates the exact calculation of gross PnL, transaction costs, funding cash flows, and net returns across the three candidate cost scenarios using identical notional denominators:

### Hypothetical Trade Setup
- **Account Equity:** $E_0 = \$100,000.00$ USDT.
- **Trade Direction:** LONG ($d = +1$).
- **Position Quantity:** $Q = 100.0$ units.
- **Entry Reference Price:** $P_{\text{entry, ref}} = 100.00$ USDT.
- **Entry Notional:** $N_{\text{entry}} = 100.0 \times 100.00 = \$10,000.00$ USDT ($10.0\%$ portfolio notional).
- **Exit Reference Price:** $P_{\text{exit, ref}} = 101.50$ USDT ($+1.50\%$ gross move).
- **Exit Notional:** $N_{\text{exit}} = 100.0 \times 101.50 = \$10,150.00$ USDT.
- **Gross Trading PnL:** $\text{PnL}_{\text{gross}} = 100.0 \times (101.50 - 100.00) = +\$150.00$ USDT ($+150.0\text{ bps}$ of entry notional).

### Financing Cash Flow (1 Settlement Event Crossed)
- **Assumed Funding Rate:** $+1.0\text{ bps per settlement}$ ($f_t = +0.0001$).
- **Funding Payment:** $CF_{\text{funding}} = -(+1) \times 10,150.00 \times 0.0001 = -1.015\text{ USDT}$ (Long pays $1.015\text{ bps}$ of entry notional).

---

## 2. COMPARISON ACROSS THE THREE COST SCENARIOS

### Scenario 1: Base Case Tier (15 bps Round-Trip)
- Entry Cost ($7.5\text{ bps}$ of $N_{\text{entry}}$): $10,000.00 \times 0.00075 = \$7.50$ USDT.
- Exit Cost ($7.5\text{ bps}$ of $N_{\text{exit}}$): $10,150.00 \times 0.00075 = \$7.61$ USDT.
- Total Transaction Friction: $7.50 + 7.61 = \$15.11$ USDT ($15.11\text{ bps}$ of entry notional).
- **Net Realized PnL:** $150.00 - 15.11 - 1.015 = +\mathbf{\$133.875\text{ USDT}}$ ($+\mathbf{133.88\text{ bps}}$).
- **Break-Even Gross Hurdle:** $15.11 + 1.015 = \mathbf{16.125\text{ bps}}$ (+\$16.13 USDT).

### Scenario 2: Conservative Tier (20 bps Round-Trip)
- Entry Cost ($10.0\text{ bps}$ of $N_{\text{entry}}$): $10,000.00 \times 0.00100 = \$10.00$ USDT.
- Exit Cost ($10.0\text{ bps}$ of $N_{\text{exit}}$): $10,150.00 \times 0.00100 = \$10.15$ USDT.
- Total Transaction Friction: $10.00 + 10.15 = \$20.15$ USDT ($20.15\text{ bps}$ of entry notional).
- **Net Realized PnL:** $150.00 - 20.15 - 1.015 = +\mathbf{\$128.835\text{ USDT}}$ ($+\mathbf{128.84\text{ bps}}$).
- **Break-Even Gross Hurdle:** $20.15 + 1.015 = \mathbf{21.165\text{ bps}}$ (+\$21.17 USDT).

### Scenario 3: Severe Stress Tier (30 bps Round-Trip)
- Entry Cost ($15.0\text{ bps}$ of $N_{\text{entry}}$): $10,000.00 \times 0.00150 = \$15.00$ USDT.
- Exit Cost ($15.0\text{ bps}$ of $N_{\text{exit}}$): $10,150.00 \times 0.00150 = \$15.23$ USDT.
- Total Transaction Friction: $15.00 + 15.23 = \$30.23$ USDT ($30.23\text{ bps}$ of entry notional).
- **Net Realized PnL:** $150.00 - 30.23 - 1.015 = +\mathbf{\$118.755\text{ USDT}}$ ($+\mathbf{118.76\text{ bps}}$).
- **Break-Even Gross Hurdle:** $30.23 + 1.015 = \mathbf{31.245\text{ bps}}$ (+\$31.25 USDT).

---

## 3. EPISTEMIC DISCLAIMER

All numbers presented in this document are strictly **illustrative hypothetical examples** designed to verify dimensional and mathematical consistency. They do NOT represent observed QUANTUM trading returns or verified exchange fills.
