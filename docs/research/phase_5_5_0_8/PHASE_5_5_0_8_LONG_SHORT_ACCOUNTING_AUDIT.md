# QUANTUM PHASE 5.5.0.8: LONG/SHORT NOTIONAL AND PNL CONSISTENCY AUDIT

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-01 21:25:00 UTC`  
**Associated Task:** Task A (Long/Short Notional and PnL Consistency)  
**Operational Mode:** `READ_ONLY_QUANTITATIVE_SPECIFICATION_AUDIT`  

---

## 1. MATHEMATICAL FORMULATION & NOTIONAL ASYMMETRY DERIVATION

In linear USDT-margined perpetual futures, contract value and execution notionals depend on order direction and price trajectory:

- **Direction Convention:** LONG: $d = +1$; SHORT: $d = -1$.
- **Underlying Price Return:**
  $$r_p = \frac{P_{\text{exit}} - P_{\text{entry}}}{P_{\text{entry}}}$$
- **Directional Gross Trade Return:**
  $$R_{\text{gross}} = d \times r_p = d \times \frac{P_{\text{exit}} - P_{\text{entry}}}{P_{\text{entry}}}$$
- **Entry Execution Notional:**
  $$N_{\text{entry}} = Q_{\text{entry}} P_{\text{entry}}$$
- **Full Position Closure Assumption:**
  Under the frozen QUANTUM research architecture (Phase 5.3 baseline and Phase 5.5 triple-barrier protocol), positions are closed in full ($100\%$) upon triggering a barrier or reaching the 288-bar timeout:
  $$Q_{\text{exit}} = Q_{\text{entry}} = Q$$
- **Exit Execution Notional:**
  $$N_{\text{exit}} = Q_{\text{exit}} P_{\text{exit}} = Q P_{\text{entry}}(1 + r_p) = N_{\text{entry}}(1 + r_p)$$
  Substituting $r_p = d R_{\text{gross}}$ (since $d^2 = 1$):
  $$N_{\text{exit}} = N_{\text{entry}}(1 + d R_{\text{gross}})$$

### Crucial Mathematical Insight
1. **For LONG Positions ($d = +1$):**
   - Profitable Trade ($R_{\text{gross}} > 0 \implies r_p > 0$): $N_{\text{exit}} = N_{\text{entry}}(1 + R_{\text{gross}}) > N_{\text{entry}}$.
   - Losing Trade ($R_{\text{gross}} < 0 \implies r_p < 0$): $N_{\text{exit}} = N_{\text{entry}}(1 - |R_{\text{gross}}|) < N_{\text{entry}}$.
2. **For SHORT Positions ($d = -1$):**
   - Profitable Trade ($R_{\text{gross}} > 0 \implies r_p < 0$): $N_{\text{exit}} = N_{\text{entry}}(1 - R_{\text{gross}}) < N_{\text{entry}}$.
   - Losing Trade ($R_{\text{gross}} < 0 \implies r_p > 0$): $N_{\text{exit}} = N_{\text{entry}}(1 + |R_{\text{gross}}|) > N_{\text{entry}}$.

**Verification Result:** In linear USDT perpetual contracts, a profitable SHORT trade exits at a lower price than entry, and therefore has a **strictly lower exit notional** ($N_{\text{exit}} < N_{\text{entry}}$). Conversely, a losing SHORT trade exits at a higher price, producing a **strictly higher exit notional** ($N_{\text{exit}} > N_{\text{entry}}$).

---

## 2. MANDATORY NUMERICAL EXAMPLES (A1)

> [!NOTE]
> All numerical examples below are strictly **illustrative and synthetic**. They use an identical absolute price move of $|r_p| = 1.50\%$ and a constant base fee rate of $7.5$ bps ($0.00075$) per leg ($15.0$ bps nominal round-trip).

### Summary Table of the Four Canonical Cases
| Metric | Case 1: LONG Profitable | Case 2: LONG Losing | Case 3: SHORT Profitable | Case 4: SHORT Losing |
|---|---|---|---|---|
| **Direction ($d$)** | $+1$ (LONG) | $+1$ (LONG) | $-1$ (SHORT) | $-1$ (SHORT) |
| **Quantity ($Q$)** | $100.0$ units | $100.0$ units | $100.0$ units | $100.0$ units |
| **Entry Price ($P_{\text{entry}}$)** | $100.00$ USDT | $100.00$ USDT | $100.00$ USDT | $100.00$ USDT |
| **Exit Price ($P_{\text{exit}}$)** | $101.50$ USDT | $98.50$ USDT | $98.50$ USDT | $101.50$ USDT |
| **Price Return ($r_p$)** | $+1.5000\%$ | $-1.5000\%$ | $-1.5000\%$ | $+1.5000\%$ |
| **Gross Trade Return ($R_{\text{gross}}$)** | $+1.5000\%$ | $-1.5000\%$ | $+1.5000\%$ | $-1.5000\%$ |
| **Entry Notional ($N_{\text{entry}}$)** | $\$10,000.00$ | $\$10,000.00$ | $\$10,000.00$ | $\$10,000.00$ |
| **Exit Notional ($N_{\text{exit}}$)** | $\$10,150.00$ | $\$9,850.00$ | $\$9,850.00$ | $\$10,150.00$ |
| **Gross PnL (USDT)** | $+\$150.00$ | $-\$150.00$ | $+\$150.00$ | $-\$150.00$ |
| **Entry Fee ($7.5$ bps)** | $\$7.50$ | $\$7.50$ | $\$7.50$ | $\$7.50$ |
| **Exit Fee ($7.5$ bps)** | $\$7.6125$ | $\$7.3875$ | $\$7.3875$ | $\$7.6125$ |
| **Total Fee (USDT)** | $15.1125 | $14.8875 | $14.8875 | $15.1125 |
| **Normalized Fee (bps of $N_{\text{entry}}$)** | **15.1125 bps** | **14.8875 bps** | **14.8875 bps** | **15.1125 bps** |

### Detailed Analysis of Findings
1. On winning trades with $+1.50\%$ gross return:
   - The profitable LONG incurs $15.1125 USDT in fees (15.1125 bps of entry notional) because exit notional expanded to $10,150.
   - The profitable SHORT incurs only $14.8875 USDT in fees (14.8875 bps of entry notional) because exit notional contracted to $9,850.
2. On losing trades with $-1.50\%$ gross return:
   - The losing LONG incurs $14.8875 USDT in fees (14.8875 bps of entry notional).
   - The losing SHORT incurs $15.1125 USDT in fees (15.1125 bps of entry notional).
3. This asymmetric fee drag is an inherent property of linear contracts denominated in USDT and confirms that profitable short positions experience lower exit fee friction.

---

## 3. PARTIAL EXITS AUDIT (A2)

- **Audit Question:** Does the QUANTUM Phase 5.5 research specification support partial position scaling or staggered barrier exits?
- **Source Inspection:** Inspection of Phase 5.3 label generation code (`labeling.py`) and Phase 5.5 research designs confirms that all barrier exits trigger full liquidation ($Q_{\text{exit}} = Q_{\text{entry}}$).
- **Governance Limitation:** Partial exits (e.g. scaling out $50\%$ at target 1 and trailing remaining $50\%$) are strictly **UNSUPPORTED** in the frozen architecture. Any downstream trading strategy featuring partial scaling belongs strictly to Track 3 (Exploratory Strategy Development) and cannot be claimed as an evaluation of the frozen classifier.
- *Status:* `PASS_WITH_LIMITATIONS`.

---

## 4. VERDICT CLASSIFICATION TABLE (A3)

| Mathematical Property | Derivation / Formula | Evaluation Standard | Verdict |
|---|---|---|---|
| **Price Return ($r_p$)** | $(P_{\text{exit}} - P_{\text{entry}}) / P_{\text{entry}}$ | Definitionally sound | `PASS` |
| **Directional Return ($R_{\text{gross}}$)** | $d \times r_p$ | Standard linear perpetual sign | `PASS` |
| **Exit Notional ($N_{\text{exit}}$)** | $N_{\text{entry}}(1 + r_p) = N_{\text{entry}}(1 + d R_{\text{gross}})$ | Exact base-quote product | `PASS` |
| **Fee Dynamic Scaling** | $N_{\text{entry}} f_{\text{entry}} + N_{\text{exit}} f_{\text{exit}}$ | Exact exchange fee formula | `PASS` |
| **Short Fee Asymmetry** | Profitable SHORT has $N_{\text{exit}} < N_{\text{entry}}$ | Dimensionally verified | `PASS` |
| **Full Exit Boundary** | $Q_{\text{exit}} = Q_{\text{entry}}$ | Frozen system limitation | `PASS_WITH_LIMITATIONS` |
