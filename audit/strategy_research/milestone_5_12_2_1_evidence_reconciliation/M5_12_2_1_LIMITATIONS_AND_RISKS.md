# M5.12.2.1 Limitations, Operational Risks & Research Disclosures

**Milestone:** M5.12.2.1 — Independent Evidence Reconciliation & Adversarial Validation  
**Repository:** `d:/quantum-multi-agent`  
**Branch:** `research/quantum-next-3pct`  
**Baseline Commit:** `273b897`  
**Audit Date:** 2026-11-04  
**Classification:** Research Governance, Risk Disclosure & Systemic Limitations  

---

## 1. Executive Summary of Audit Limitations

This forensic audit confirms that the accounting mechanisms, double-entry cash reconciliations, unit tests, and order-admission exposure bounds in `273b897` are implemented correctly and reproducibly.

However, an exhaustive adversarial audit reveals five critical limitations and risks that must govern all future research in Milestone 5.13 and beyond:
1. **Mark-to-Market (MTM) Exposure Drift on Open Short Positions.**
2. **Inert Safety Buffer (`self.safety_buffer = 0.0020`) in Pre-Trade Admission.**
3. **The Retail Taker Fee Economic Barrier (26 bps Roundtrip Friction vs +1.85 bps Gross Edge).**
4. **Statistical Insignificance under Family-Wise Multiple Testing Correction ($m=30$).**
5. **Capital Depletion Truncation of Trade Signal Funnels.**

---

## 2. Invariant Risk: Mark-to-Market Exposure Drift vs. Pre-Trade Admission

### 2.1 The Architectural Distinction
In M5.12.2, the exposure invariant `gross_exposure <= 1.000000x` was evaluated and enforced exclusively as a **pre-trade order admission gate** in `can_open_position()`.
- **Pre-Trade Admission:** When an order is submitted, the ledger verifies that `(current_reserved_notional + new_order_notional) / current_equity <= 1.000000x`. This invariant held in 100.00% of tested scenarios (120 adversarial boundary tests and 10,000 property-based testing sequences).
- **Post-Trade Mark-to-Market Drift:** Once positions are open, price movements alter the mark-to-market notional value of positions and portfolio equity continuously.

### 2.2 Mathematical Exposure Expansion on Short Positions
For long positions, an adverse price drop reduces notional and equity in equal absolute dollar terms, keeping gross exposure $\le 1.0x$.
For short positions, an adverse price increase increases position notional while reducing equity:

$$\text{Exposure}_{\text{MTM}} = \frac{N_{\text{entry}} \cdot (1 + \Delta_{\text{price}})}{E_{\text{entry}} - N_{\text{entry}} \cdot \Delta_{\text{price}}}$$

Under full 1.0000x initial allocation:
- A $5.0\%$ adverse price spike drives gross exposure to:
  $$\frac{100 \cdot 1.05}{100 - 5} = \frac{105}{95} = 1.1053x$$
- A $10.0\%$ adverse price spike drives gross exposure to:
  $$\frac{100 \cdot 1.10}{100 - 10} = \frac{110}{90} = 1.2222x$$
- A $20.0\%$ adverse price shock drives gross exposure to:
  $$\frac{100 \cdot 1.20}{100 - 20} = \frac{120}{80} = 1.5000x$$

### 2.3 Operational Risk & Remediation for M5.13
Currently, `EventDrivenPortfolioLedger` contains no dynamic de-leveraging or partial position trimming mechanism to enforce `gross_exposure <= 1.000000x` during continuous mark-to-market updates.
- **Mandate for M5.13:** Implement an active risk daemon that monitors real-time MTM exposure and triggers automated trimming if exposure crosses $1.000000x$.

---

## 3. Configuration Defect: Inert Safety Buffer

### 3.1 Forensic Finding
In `src/quantum/accounting/event_ledger.py`:
- Line 56 initializes: `self.safety_buffer = 0.0020` (20 basis points).
- However, throughout `can_open_position()`, capacity calculations use a hardcoded epsilon:
  ```python
  remaining_cap = (self.equity * self.max_gross_exposure) - (current_exposure + pending_exposure) - 1e-6
  ```
- The variable `self.safety_buffer` is never referenced anywhere else in the class or codebase. It is completely inert.

### 3.2 Derived Microstructural Buffer Recommendation
In high-frequency 5-minute crypto perpetuals, 99th-percentile single-bar adverse drift across the 10-asset universe is approximately $0.42\%$ (42 basis points).
- To guarantee that mark-to-market exposure does not breach $1.000000x$ prior to stop-loss execution, pre-trade order admission must enforce a mandatory microstructural safety buffer:

$$\text{Max Allowed Admission Exposure} = 1.000000x - 0.005000x = 0.995000x \text{ (50 bps)}$$

- **Remediation for M5.13:** Wire `self.safety_buffer = 0.0050` directly into `can_open_position()` as an active subtraction from `max_gross_exposure`.

---

## 4. Execution Economics: The Retail Taker Fee Barrier

### 4.1 The AsterDEX Retail Schedule Drag
The verified AsterDEX Base Retail taker fee schedule imposes:
- Entry Taker Fee: $10.0\text{ bps}$
- Exit Taker Fee: $10.0\text{ bps}$
- Entry Spread Crossing: $1.0\text{ bps}$
- Exit Spread Crossing: $1.0\text{ bps}$
- Entry Slippage: $2.0\text{ bps}$
- Exit Slippage: $2.0\text{ bps}$
- **Total Roundtrip Friction:** $26.0\text{ bps}$ ($0.26\%$) per completed trade episode.

### 4.2 Economic Infeasibility of Retail Taker Execution
The highest gross-expectancy hypothesis identified in M5.12, HYP-05 (Volume Profile POC Reversion), generates:
- Gross Mean Return: $+1.85\text{ bps}$ per trade
- Unconstrained Gross PnL: $+\$48.36$ across 10,429 trades ($148.36\%$ terminal equity)
- Under Retail Taker Fees ($26\text{ bps}$), Net Mean Return is:
  $$\text{Net Expectancy} = +1.85\text{ bps} - 26.0\text{ bps} = -24.15\text{ bps}$$
- Result: Fast portfolio exhaustion to $-\$39.00$ net loss and $80.01\%$ max drawdown.

### 4.3 Strategic Implication
No high-frequency intraday crypto strategy with a gross edge of $1\text{ to }5\text{ bps}$ can survive retail taker fees. QUANTUM must either:
1. Shift execution entirely to **Passive Maker Orders** (earning maker rebates or incurring lower fees of 2-4 bps with zero spread crossing), and model queue priority delay and adverse selection rigorously.
2. Restructure signal generation to target wider swing targets ($\ge 50\text{ bps}$ holding horizons of 4h to 24h), reducing execution frequency but allowing gross margins to exceed retail fees.

---

## 5. Statistical Rigor: Multiple Testing & Deflated Sharpe Ratio

### 5.1 Unadjusted Significance vs Family-Wise Reality
In isolation, HYP-05 appears statistically significant:
- Unadjusted Asymptotic P-Value: $p = 0.00456$
- Circular Block Bootstrap (Block length $b=24$ bars = 2 hours): $95\%\text{ CI} = [+0.37, +2.68]\text{ bps}$ (strictly bounded above zero).

### 5.2 Family-Wise Error Rate ($m=30$)
However, the research engine evaluated 30 distinct combinations ($6\text{ hypotheses} \times 5\text{ regimes}$):
- Under the conservative **Holm-Bonferroni correction**:
  $$p_{\text{adj}} = m \times p = 30 \times 0.00456 = 0.1370$$
- Because $p_{\text{adj}} = 0.1370 > 0.05$, the null hypothesis of zero edge cannot be rejected at the standard 5% significance level.
- **Deflated Sharpe Ratio (DSR):**
  $$\text{DSR} = 0.4820 < 0.95$$
- **Formal Downgrade:** The claim of "proven statistical alpha" is formally rejected. HYP-05 represents **preliminary descriptive evidence of gross market inefficiency**, requiring prospective holdout validation.

---

## 6. Capital Depletion & Trade Funnel Distortion

### 6.1 The Disappearing Trade Mechanism
In M5.12.2, a major source of confusion was the discrepancy between raw signal counts and executed trade counts:
- HYP-06: 5,878 unconstrained trades vs 2,503 taker trades.
- HYP-05: 10,429 unconstrained trades vs 2,592 taker trades.

### 6.2 The Forensic Mechanism
The reconciliation proved this collapse was entirely an artifact of simulated equity depletion:
1. Both strategies started with $\$100.00$ initial capital.
2. Under 26 bps taker drag, equity steadily decayed towards $\$20.00$.
3. The portfolio rules cap maximum symbol allocation at $25\%$ of equity:
   $$\text{Max Order Size} = 0.25 \times \$20.00 = \$5.00$$
4. At $\$5.00$, the order size hit the exchange minimum viable notional ($min\_order = \$5.00$). Any further small drawdown caused calculated allocation to fall below $\$5.00$, triggering runtime order rejection:
   `REJECTED_ALLOCATION_BELOW_MIN_ORDER`
5. Consequently, the backtest silently stopped executing trades for the final 60% of the dataset, creating the illusion of a shrinking signal funnel.

---

## 7. Operational Execution Risks for High-Frequency Deployment

If QUANTUM transitions from backtesting to live deployment in future phases, the following execution risks must be managed:
1. **Adverse Selection on Limit Orders:** Limit orders resting at the bid/ask suffer adverse selection when informed flow sweeps the book, turning simulated maker fills into net losses.
2. **Queue Position Priority:** In crypto perpetuals, limit orders are FIFO queue-priority. A simulated bar low touching the limit price does not guarantee a fill in live markets.
3. **API Latency and Rate Limiting:** 10 to 100 trades per day across 10 altcoin markets requires robust async websocket management and connection failover.
4. **Funding Rate Volatility:** Perpetual funding rates fluctuate between -100 bps and +100 bps annualized. Sustained positions during high volatility can incur significant holding drag.

---

## 8. Summary Table of Risks & Status

| Risk Area | Severity | Root Cause | Mitigation Strategy | Milestone Target |
| :--- | :---: | :--- | :--- | :---: |
| **MTM Exposure Drift** | HIGH | Short position notional expansion under adverse price drift | Implement active intraday deleveraging daemon | M5.13 |
| **Inert Safety Buffer** | MEDIUM | `self.safety_buffer` defined but unused in capacity check | Wire 50 bps microstructural buffer into admission logic | M5.13 |
| **Retail Taker Drag** | CRITICAL | 26 bps taker friction overwhelms 1.85 bps gross edge | Shift to passive maker execution or wider swing horizons | M5.13 |
| **Multiple Testing Bias** | HIGH | $m=30$ hypothesis tests dilute statistical significance | Enforce family-wise FDR/FWER gating before promotion | M5.13 |
| **Funnel Depletion** | MEDIUM | Low equity hits minimum viable order threshold ($5.00) | Implement capital scaling and proportional sizing floors | M5.13 |
