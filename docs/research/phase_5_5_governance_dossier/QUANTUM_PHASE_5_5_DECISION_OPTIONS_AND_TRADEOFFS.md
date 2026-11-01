# QUANTUM PHASE 5.5: DECISION OPTIONS AND TRADEOFFS (REVISION 1)

**Document Status:** `APPROVED_FOR_HUMAN_REVIEW`  
**Revision:** `Revision 1 (Decision Consistency & Risk-Claim Correction)`  
**Publication Timestamp:** `2026-11-01 22:55:00 UTC`  
**Operational Mode:** `READ_ONLY_EVIDENCE_RECONCILIATION_AND_GOVERNANCE_DOCUMENTATION`  
**Associated Deliverable:** Detailed Option Cards (Tasks A, B, C, D, E)  

---

## 1. DEC_01: BARRIER EXECUTION ARCHITECTURE (TASK B)

### The Three Formal Alternatives
1. **Alternative A (Original Close-Anchored Barriers):**
   - *Specification:* $P_{\text{ref}} = \text{close}[i]$, barriers at $P_{\text{ref}}(1 \pm 1.5\sigma_t)$.
   - *Limitation:* Look-ahead latency violation. In live trading, an order cannot be filled at candle $i$ close because model inference requires candle $i$ close data. Fills occur at candle $i+1$ open.
   - *Status:* Statistically evaluated in Phase 5.4 (Track 1); economically unexecutable.
2. **Alternative B (Re-Anchored Economic Barriers):**
   - *Specification:* Fill at $P_{\text{entry}} = \text{open}[i+1]$, barriers re-anchored to $P_{\text{entry}}(1 \pm 1.5\sigma_t)$.
   - *Advantage:* Zero new parameters. Cleanly tests whether the frozen classifier's directional signals have economic utility under realistic execution timing.
   - *Critical Epistemic Caveat:* Re-anchoring shifts the price levels of the upper and lower barriers. Therefore, positive economic results under Alternative B **do NOT automatically validate the original close-anchored training label payoff**. It evaluates the classifier as a directional filter under a re-anchored policy.
3. **Alternative C (Independent Downstream Strategy Development):**
   - *Specification:* Decouples classifier from static barriers; introduces trailing stops, dynamic ATR bands, and time-decay exits.
   - *Advantage:* Tests a complete algorithmic trading system.
   - *Limitation:* Introduces multiple degrees of freedom requiring cross-validation tuning on Folds 1-4 with Fold 5 held out. Conflates classifier quality with heuristic trade management.

### Permitted vs. Prohibited Conclusions
- **Permitted under Alt B:** "The frozen classifier demonstrates statistically significant economic expectancy after realistic taker fees and funding under a re-anchored triple-barrier policy."
- **Prohibited under Alt B:** "Phase 5.5 validates the exact economic payoff of the Phase 5.3 training labels."

---

## 2. DEC_02: DIRECTIONAL TRADING SCOPE (TASK D)

### Separation of Mandatory Reporting from Execution Authorization
A critical distinction must be enforced between research reporting and execution permission:
1. **Directional Evaluation Scope (Mandatory Research Reporting):** All backtests must report Long-Only, Short-Only, and Combined results independently to expose directional performance asymmetry.
2. **Execution Permission (Human Decision):** Authorizing bidirectional evaluation reporting does NOT automatically authorize bidirectional execution in production. The supervisor must decide which directions are permitted for trading.
3. **Portfolio Combination Policy:** How Long and Short signals interact (netting opposing signals vs concurrent independent positions).
4. **Direction-Specific Costs:** Asymmetric fee drag is mathematically verified: winning Short trades have lower exit notional ($N_{\text{exit}} < N_{\text{entry}}$) and incur lower fees in USDT ($14.89$ vs $15.11$ bps on a $1.50\%$ move).
5. **Funding Asymmetry:** Financing cash flows depend on prevailing regime (Longs pay in bull markets; Shorts pay in bear markets).
6. **Statistical Power:** Splitting trades into Long and Short halves the sample size per directional subset, reducing statistical power.

### Directional Scope Alternatives
- **Option 1 (Long-Only Execution):** Execute Class +1 signals only. Aligns with secular crypto bull market drift; avoids short-side liquidation squeeze risk. Misses multi-month bear market opportunities.
- **Option 2 (Short-Only Execution):** Execute Class -1 signals only. Provides hedge against portfolio drawdowns; lower fee drag on winning trades. Suffers persistent negative funding drag during bull regimes.
- **Option 3 (Bidirectional Execution with Mandatory Disaggregated Reporting):** Execute both Class +1 and Class -1 signals. Maximizes utilization of the 11 specialists. Requires separate reporting of Long-Only, Short-Only, and Combined metrics in all master tables.

---

## 3. DEC_03: FUNDING RATE MODEL (TASK C)

### Standard Formulations
- **Canonical Unit:** `funding_rate_bps_per_settlement`
- **Nominal Annualization Factor:** $1095 = 3 \times 365$ (Arithmetic scaling convention; strictly not realized yield or compounding return).
- **Signed Cash Flow Equation:**
  $$CF_t = -d \times N_{\text{settle}, t} \times f_{t, \text{decimal}}$$
  where $N_{\text{settle}, t} = Q \times P_{\text{mark}, t}$ and $f_{t, \text{decimal}} = \frac{\text{bps}}{10,000}$.

### Parametric Sensitivity Interpretation
- The four scenarios (-1.0, 0.0, +1.0, +3.0 bps per settlement) represent **parametric sensitivity inputs**.
- They do NOT represent historical distributions, empirical bounds, or guaranteed coverage of future regimes.
- **Missing Data Status:** Historical funding rates remain completely absent from local canonical datasets (`FUNDING_DATA_UNAVAILABLE`).
- **Settlement Eligibility:** The exact AsterDEX matching engine rule for orders filled at 08:00:00.000 UTC remains `NOT_VERIFIED` until supported by authoritative venue specifications.

---

## 4. DEC_04: COST SCENARIOS & STATISTICAL ACCEPTANCE CRITERIA (TASK B & E)

### Accounting Convention: REFERENCE_PRICE_ACCOUNTING
To prevent double-counting:
- Gross PnL is computed strictly from clean reference prices: $\text{PnL}_{\text{gross}} = d \times Q \times (P_{\text{exit, ref}} - P_{\text{entry, ref}})$.
- Exchange taker fees, bid-ask spread, volatility slippage, and market impact are aggregated into $C_{\text{transaction, USDT}}$ and deducted as a cash friction.
- Prices are never slipped prior to gross PnL calculation.

### Statistical Methodology Status Reconciled
1. **Bootstrap Block-Length Classifications:**
   - **24 bars (2 hours):** Existing candidate with identified limitations (underestimates serial autocorrelation for trades held up to 288 bars).
   - **288 bars (24 hours):** Candidate motivated by the maximum holding horizon; **NOT a statistically validated optimal block length**.
   - **72, 144, 576 bars:** Candidate sensitivity values for empirical robustness checks; not approved methodology.
2. **Resampling Design:**
   - Trade-level resampling violates temporal continuity when holding horizons overlap.
   - Continuous Calendar-Time Portfolio Moving Block Bootstrap on continuous 5-minute equity curves is the recommended candidate design.
3. **Acceptance Hierarchy (Four Levels):**
   - Level 1: Cost Scenario Resilience (15, 20, 30 bps sweeps).
   - Level 2: Positive Sample Expectancy ($E[R_{\text{net}}] > 0$). *Descriptive point estimate only; not proof of statistically significant alpha.*
   - Level 3: Statistical Significance (Paired MBB, $p < 0.05$ after Holm-Bonferroni).
   - Level 4: Anti-Cherry-Picking Robustness (Simultaneous disaggregated reporting).

### Hypothesis Family Dependency on DEC_06
- If XMR is **excluded** from primary portfolio inference (DEC_06 Tier 3): Primary Confirmatory Family is **$K = 10$**.
- If XMR is **included** in primary portfolio inference: Primary Confirmatory Family is **$K = 11$**.
- Secondary Directional Family: $K = 30$ (if $K=10$) or $K = 33$ (if $K=11$).
- Exploratory Scenario Family: $K = 90$ (if $K=10$) or $K = 99$ (if $K=11$).

---

## 5. DEC_05: PORTFOLIO CONCURRENCY & RISK RECONCILIATION (TASK A)

### Reconciling Exposure Definitions
1. **Gross Exposure:**
   $$\text{GrossExposure} = \sum_{i=1}^n |N_i|$$
2. **Gross Leverage:**
   $$\text{GrossLeverage} = \frac{\text{GrossExposure}}{\text{Equity}}$$
3. **Margin Utilization:**
   $$\text{MarginUtilization} = \frac{\text{InitialMargin}}{\text{AvailableEquity}}$$
4. **Denominator Ambiguity:**
   The previously documented "30% gross notional limit" does NOT define whether the denominator is account equity, total balance, or a separate risk budget. This requires human clarification (`REQUIRES_HUMAN_CLARIFICATION`). Furthermore, a 30% gross notional limit ($0.3\text{x}$ exposure) is NOT equivalent to 1x leverage.

### Reconciling Stop-Loss Risk: Nominal vs. Realized Loss
- **Nominal Stop Loss:**
  $$L_{\text{stop, nominal}} = \sum_{i=1}^n |N_i| D_i$$
  where $D_i$ is the adverse price distance from entry to the barrier stop price.
- **Realized Loss Under Real-Market Frictions:**
  $$\text{Realized Loss} = L_{\text{stop, nominal}} + C_{\text{fees}} + C_{\text{slippage}} + C_{\text{impact}} + CF_{\text{funding}} + \text{Gap Risk}$$
- **Explicit Removal of Unsupported Guarantees:**
  The dossier does NOT claim:
  - That portfolio loss is guaranteed to remain at or below 1%.
  - That liquidation risk is completely eliminated.
  - That stop-loss orders guarantee the assumed execution price.
  Real-world liquidation cascades, exchange outages, slippage blowouts, and weekend price gaps can cause realized losses to exceed nominal stop distances.

### DEC_05 Decision Alternatives
- **Option 1 (Fixed Gross Exposure Cap):** Enforce hard limit on gross notional (e.g. $\sum |N_i| \le 0.30 \times \text{Equity}$). Simple to enforce; does not adjust for varying asset volatility.
- **Option 2 (Risk-Budget-Based Position Sizing):** Scale position notionals inversely with volatility ($N_i \propto 1 / \sigma_i$) so nominal stop loss is targeted at a fixed percentage of equity per position (e.g. 0.33% nominal risk per trade). Equalizes risk across assets; requires dynamic sizing logic.
- **Option 3 (Combined Exposure Cap and Stop-Risk Budget):** Enforce both a maximum gross notional cap (e.g. 50% equity) AND a per-position nominal stop-risk limit (e.g. 0.50% equity). Provides dual constraints; requires engineering both position sizing and portfolio concurrency controls.

---

## 6. DEC_06: XMR RESEARCH & PORTFOLIO SCOPE (TASK E)

### Data Coverage Disparity
- 10 Assets (BTC, ETH, BNB, XRP, ADA, SOL, AVAX, LINK, DOGE, LTC): 316,500 5m candles ($3.0$ years, October 2023 to October 2026).
- XMRUSDT: 83,863 5m candles ($9.5$ months, starting January 13, 2026).

### Three-Tier Policy and Hypothesis Family Link
1. **Tier 1 (Artifact Preservation):** 100% of XMR model binaries and preprocessors are preserved.
2. **Tier 2 (Standalone Research Reporting):** XMR economic metrics are evaluated and published in a dedicated standalone research appendix.
3. **Tier 3 (Primary Portfolio Acceptance):** XMR is excluded from primary portfolio aggregation, which fixes the primary confirmatory hypothesis family at **$K = 10$**.
