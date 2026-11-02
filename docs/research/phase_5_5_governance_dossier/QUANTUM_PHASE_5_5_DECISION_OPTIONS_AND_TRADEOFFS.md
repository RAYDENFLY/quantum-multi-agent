# QUANTUM PHASE 5.5: DECISION OPTIONS AND TRADEOFFS (REVISION 1.2)

**Document Status:** `APPROVED_FOR_HUMAN_REVIEW`  
**Revision:** `Revision 1.2 (Final Governance Closure Check)`  
**Publication Timestamp:** `2026-11-02 10:30:00 UTC`  
**Operational Mode:** `FINAL_GOVERNANCE_CLOSURE_AUDIT`  
**Associated Deliverable:** Detailed Option Cards (Tasks A through E)  

---

## 1. DEC_01: BARRIER EXECUTION ARCHITECTURE

### The Three Formal Alternatives
1. **Alternative A (Original Close-Anchored Barriers):**
   - *Specification:* $P_{\text{ref}} = \text{close}[i]$, barriers at $P_{\text{ref}}(1 \pm 1.5\sigma_t)$.
   - *Limitation:* Look-ahead latency violation. In live trading, an order cannot be filled at candle $i$ close because model inference requires candle $i$ close data. Fills occur at candle $i+1$ open.
   - *Status:* Statistically evaluated in Phase 5.4 (Track 1); economically unexecutable.
2. **Alternative B (Re-Anchored Economic Barriers):**
   - *Specification:* Fill at $P_{\text{entry}} = \text{open}[i+1]$, barriers re-anchored to $P_{\text{entry}}(1 \pm 1.5\sigma_t)$.
   - *Advantage:* Zero new parameters. Cleanly tests whether the frozen classifier's directional signals have economic utility under realistic execution timing.
   - *Critical Epistemic Caveat:* Re-anchoring shifts the price levels of the upper and lower barriers. Therefore, positive economic results under Alternative B **do NOT automatically validate the original close-anchored training label payoff**. It evaluates the classifier as a directional conditioning filter under a re-anchored execution policy.
3. **Alternative C (Independent Downstream Strategy Development):**
   - *Specification:* Decouples classifier from static barriers; introduces trailing stops, dynamic ATR bands, and time-decay exits.
   - *Advantage:* Tests a complete algorithmic trading system.
   - *Limitation:* Introduces multiple degrees of freedom requiring cross-validation tuning on Folds 1-4 with Fold 5 held out. Conflates classifier quality with heuristic trade management.

### Permitted vs. Prohibited Conclusions
- **Permitted under Alt B:** "The frozen classifier demonstrates statistically significant economic expectancy after realistic taker fees and funding under a re-anchored triple-barrier policy."
- **Prohibited under Alt B:** "Phase 5.5 validates the exact economic payoff of the Phase 5.3 training labels."

---

## 2. DEC_02: DIRECTIONAL TRADING SCOPE

### Separation of Mandatory Reporting from Execution Authorization
A critical distinction must be enforced between research reporting and execution permission:
1. **Directional Evaluation Scope (Mandatory Research Reporting):** All backtests must report Long-Only, Short-Only, and Combined results independently to expose directional performance asymmetry.
2. **Execution Permission (Human Decision):** Authorizing bidirectional evaluation reporting does NOT automatically authorize bidirectional execution in production. The supervisor must decide which directions are permitted for trading.
3. **Direction-Specific Costs:** Asymmetric fee drag is mathematically verified: winning Short trades have lower exit notional ($N_{\text{exit}} < N_{\text{entry}}$) and incur lower fees in USDT ($14.89$ vs $15.11$ bps on a $1.50\%$ price displacement).
4. **Funding Asymmetry:** Financing cash flows depend on prevailing regime (Longs pay in bull markets; Shorts pay in bear markets).
5. **Statistical Power:** Splitting trades into Long and Short halves the sample size per directional subset, reducing statistical power.

### Directional Scope Alternatives
- **Option 1 (Long-Only Execution):** Execute Class +1 signals only. Aligns with secular crypto bull market drift; avoids short-side liquidation squeeze risk. Misses multi-month bear market opportunities.
- **Option 2 (Short-Only Execution):** Execute Class -1 signals only. Provides hedge against portfolio drawdowns; lower fee drag on winning trades. Suffers persistent negative funding drag during bull regimes.
- **Option 3 (Bidirectional Execution with Mandatory Disaggregated Reporting):** Execute both Class +1 and Class -1 signals. Maximizes utilization of the 11 specialists. Requires separate reporting of Long-Only, Short-Only, and Combined metrics in all master tables.

---

## 3. DEC_03: FUNDING RATE MODEL

### Standard Formulations
- **Canonical Unit:** `funding_rate_bps_per_settlement`
- **Nominal Annualization Factor:** $1095 = 3 \times 365$ (Arithmetic scaling convention; strictly not realized yield or compounding return).
- **Signed Cash Flow Equation:**
  $$CF_t = -d \times N_{\text{settle}, t} \times f_{t, \text{decimal}}$$
  where $N_{\text{settle}, t} = Q \times P_{\text{mark}, t}$ and $f_{t, \text{decimal}} = \frac{\text{bps}}{10,000}$.

### Parametric Sensitivity Interpretation vs Historical Evidence
- The four scenarios (-1.0, 0.0, +1.0, +3.0 bps per settlement) represent **parametric sensitivity inputs**.
- They do NOT represent historical distributions, empirical bounds, or guaranteed coverage of future regimes.
- **Missing Data Status:** Historical funding rates remain completely absent from local canonical datasets (`FUNDING_DATA_UNAVAILABLE`).
- Distinguish:
  1. Documentation of parametric assumptions (what the sensitivity framework evaluates).
  2. Human approval of a sensitivity framework (supervisor agreeing to evaluate those 4 inputs).
  3. Historical funding evidence (empirical funding rates from exchange archives).
  4. Empirical validation of funding effects (backtest results under realized funding history).
- Categories 1 and 2 exist; categories 3 and 4 are completely missing.

### Venue Rule vs Conservative Modeling Assumption (ISS_01)
- **Venue Rule:** The actual AsterDEX funding eligibility and settlement rule for orders filled at exactly 08:00:00.000 UTC. This rule is `NOT_VERIFIED` because exchange matching engine source specifications are absent from the repository.
- **Conservative Modeling Assumption:** A deliberately conservative convention adopted for research simulation (e.g., assuming orders filled at 08:00:00.000 open are ineligible for 08:00 funding).
- A supervisor can approve a modeling convention for simulation; a supervisor CANNOT approve venue truth. ISS_01 remains `OPEN` and `NOT_VERIFIED`.

---

## 4. DEC_04: COST SCENARIOS & STATISTICAL ACCEPTANCE CRITERIA (TASK B)

### Accounting Convention: REFERENCE_PRICE_ACCOUNTING
To prevent double-counting:
- Gross PnL is computed strictly from clean reference prices: $\text{PnL}_{\text{gross}} = d \times Q \times (P_{\text{exit, ref}} - P_{\text{entry, ref}})$.
- Transaction frictions (spread, execution deviation, fees) are accounted for separately as ledger entries and deducted from gross PnL.
- Prices are never slipped prior to gross PnL calculation.

### Statistical Methodology Status Reconciled (Task B)
Governance approval and statistical validation must never be conflated. Three distinct statuses are defined:
1. `CANDIDATE_METHODOLOGY`: A proposed statistical design concept under consideration (e.g. 288-bar Continuous Calendar-Time Portfolio MBB).
2. `PROVISIONALLY_APPROVED_RESEARCH_SPECIFICATION`: A methodology provisionally approved by governance for a research protocol. Approval sets operational bounds, but does NOT establish statistical optimality.
3. `EMPIRICALLY_VALIDATED_STATISTICAL_METHODOLOGY`: A methodology proven through rigorous empirical testing, diagnostic sweeps, and validated error-rate control.

### Rigorous Classification of Candidate Block Lengths (Task B):
- **24 bars (2 hours):** Existing candidate block length with potential limitations for capturing longer-duration serial dependence across multi-hour trades. Its adequacy has **NOT** been empirically established or tested against fleet return series. It must not be asserted as an empirically proven underestimation without empirical validation.
- **288 bars (24 hours):** Candidate block length motivated by the maximum trade holding horizon (288 5m bars). It is **NOT** a statistically proven or validated optimal block length.
- **72, 144, 576 bars:** Candidate sensitivity values for a future permitted diagnostic study during execution; currently unrun and unvalidated.
- **Core Principle:** Block-length adequacy depends on the empirical autocorrelation decay and cross-dependence structure of the sampled portfolio returns, not merely on the trade holding period.

### Ten Unresolved Statistical Considerations:
1. Serial dependence (autocorrelation decay across consecutive 5-minute intervals).
2. Overlapping trade outcomes (positions held simultaneously up to 288 bars violate independence).
3. Cross-asset dependence (macro market shocks causing simultaneous co-movements).
4. Concurrent portfolio exposure (multiple specialists in active trades at the same timestamp).
5. Calendar-time alignment (synchronizing discrete 5m bars across 10 or 11 crypto assets).
6. Paired comparison preservation (preserving timestamp-matched differences between model and benchmark).
7. Effective sample size ($N_{\text{eff}} \ll N$ under dependent observations).
8. Block-length sensitivity (trade-off between finite-sample variance and bootstrap bias).
9. Bootstrap confidence interval calibration (coverage error of percentile vs studentized intervals).
10. Multiple testing (family-wise error rate inflation across assets, directions, and scenarios).

### Acceptance Hierarchy (Four Levels):
- Level 1: Cost Scenario Resilience (15, 20, 30 bps sweeps).
- Level 2: Positive Sample Expectancy ($E[R_{\text{net}}] > 0$). *Descriptive point estimate only; not proof of statistically significant alpha.*
- Level 3: Statistical Significance (Paired MBB, $p < 0.05$ after Holm-Bonferroni).
- Level 4: Anti-Cherry-Picking Robustness (Simultaneous disaggregated reporting).

### Primary Hypothesis Family Definition ($K$)
The primary confirmatory hypothesis family size is defined by:
$$K = \text{number of prespecified primary confirmatory hypotheses}$$
$K$ does NOT depend solely on asset count. It is governed by: asset universe, directional scope, primary estimand, portfolio-level vs asset-level hypotheses, confirmatory vs exploratory analyses, and whether Long, Short, and Combined are independent confirmatory tests.

Illustrative structures (conditional, non-approved examples):
- **Example A (One Primary Hypothesis per Asset):**
  - $K = 10$ (if XMR excluded from primary portfolio).
  - $K = 11$ (if XMR included in primary portfolio).
- **Example B (Separate Long and Short Primary Hypotheses per Asset):**
  - $K = 20$ (if 10 assets $\times$ 2 directions).
  - $K = 22$ (if 11 assets $\times$ 2 directions).
  - If Combined is also confirmatory: $K = 30$ or $K = 33$.
- **Example C (Single Portfolio-Level Primary Hypothesis):**
  - $K = 1$, provided the primary confirmatory estimand is strictly portfolio-level and specialist tests are designated secondary/exploratory.

*Caveat:* Holm-Bonferroni step-down adjustment ($p_{(i)} \le \frac{\alpha}{K - i + 1}$) only controls FWER if the confirmatory family is correctly prespecified. DEC_04 and DEC_06 remain strictly `PENDING_HUMAN_DECISION`.

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

### Reconciled Realized-Loss Accounting Identity (Task A)
Under the convention that positive realized loss means an economic loss ($L_{\text{realized}} > 0$), and funding cash flow is signed ($CF_{\text{funding}} > 0$ received into portfolio, $CF_{\text{funding}} < 0$ paid out of portfolio):

$$L_{\text{realized}} = L_{\text{price}} + C_{\text{fees}} + C_{\text{exec\_dev}} - CF_{\text{funding}}$$

where:
- $L_{\text{realized}}$: Net realized economic loss in USDT ($> 0$ indicates loss, $< 0$ indicates profit).
- $L_{\text{price}}$: Nominal reference price displacement loss in USDT:
  $$L_{\text{price}} = -d \times Q \times (P_{\text{exit, ref}} - P_{\text{entry, ref}})$$
  where $d \in \{+1, -1\}$ ($+1$ for Long, $-1$ for Short), $Q > 0$ is filled contract quantity, $P_{\text{entry, ref}}$ is clean entry reference price (candle open), and $P_{\text{exit, ref}}$ is clean exit reference price (barrier trigger or horizon close). For an adverse exit, $L_{\text{price}} > 0$.
- $C_{\text{fees}}$: Total exchange maker/taker execution fees in USDT:
  $$C_{\text{fees}} = (\text{fee}_{\text{entry}} \times Q \times P_{\text{entry, exec}}) + (\text{fee}_{\text{exit}} \times Q \times P_{\text{exit, exec}}) \ge 0$$
- $C_{\text{exec\_dev}}$: Execution price deviation cost across entry and exit in USDT.
- $CF_{\text{funding}}$: Aggregate signed financing cash flow across all settlement timestamps $\mathcal{S}$ in USDT:
  $$CF_{\text{funding}} = \sum_{t \in \mathcal{S}} (-d) \times N_{\text{settle}, t} \times f_{t, \text{decimal}}$$
  Since $- CF_{\text{funding}}$ enters the equation:
  - If $CF_{\text{funding}} > 0$ (funding received), it subtracts from loss.
  - If $CF_{\text{funding}} < 0$ (funding paid), $- CF_{\text{funding}} = + |CF_{\text{funding}}|$, which increases loss.

### Slippage Representation Comparison: Approach A vs. Approach B (Task A1)
A key edge case arises when an order executes at a price more favorable than the reference price ($P_{\text{exec}} < P_{\text{ref}}$ for buy; $P_{\text{exec}} > P_{\text{ref}}$ for sell). Two approaches are evaluated:

1. **Approach A (Nonnegative Adverse Slippage):**
   $$C_{\text{slippage}} = \max(0, Q(-d)(P_{\text{exec}} - P_{\text{ref}}))$$
   - *Implication:* Restricts slippage cost to non-negative values ($C_{\text{slippage}} \ge 0$). Favorable executions yield $C_{\text{slippage}} = 0$.
   - *Accounting Consequence:* Favorable price improvements are ignored unless tracked in an independent price-improvement credit ledger ($R_{\text{improvement}} = \max(0, Qd(P_{\text{ref}} - P_{\text{exec}}))$). Without this credit, Approach A overstates execution costs.
2. **Approach B (Signed Execution Deviation):**
   $$C_{\text{exec\_dev}} = Q(-d)(P_{\text{exec}} - P_{\text{ref}})$$
   - *Implication:* Permits $C_{\text{exec\_dev}}$ to be signed. Adverse execution yields $C_{\text{exec\_dev}} > 0$ (adding to loss); favorable execution yields $C_{\text{exec\_dev}} < 0$ (reducing loss).
   - *Accounting Consequence:* Naturally conserves cash flows across all executions without requiring an asymmetric dual-ledger mechanism.
- **Recommendation for Human Review:** The research specification **recommends Approach B (Signed Execution Deviation)** for simulation accounting because it cleanly and symmetricly preserves net portfolio equity under two-sided execution.

### Market-Impact Separation & Anti-Double-Counting (Task A2)
The components of trade friction are defined as:
- **Reference-Price Movement:** Unadulterated price displacement ($P_{\text{exit, ref}} - P_{\text{entry, ref}}$) on clean exchange data.
- **Execution-Price Deviation:** Total divergence between executed fill and reference price ($P_{\text{exec}} - P_{\text{ref}}$).
- **Spread:** Half-spread per leg ($s_{\text{leg}} \cdot P_{\text{ref}}$).
- **Slippage:** Execution latency and depth consumption across the order book.
- **Temporary Market Impact:** Transient adverse price displacement caused by immediate trade liquidity demand that dissipates over subsequent intervals.
- **Permanent Market Impact:** Enduring price change caused by trade information content.
- **Exchange Fees:** Explicit percentage fee levied by the venue.
- **Double-Counting Prevention:** If market impact is already embedded in the executed fill price ($P_{\text{exec}}$) relative to the reference price ($P_{\text{ref}}$), deducting a separate $C_{\text{impact}}$ term double-counts the cost. Because the current simulation lacks an empirical order-book micro-simulator to separate temporary impact from liquidity slippage, the specification recommends using **one aggregate execution deviation term** $C_{\text{exec\_dev}}$ rather than an unverified synthetic decomposition.

### Gap Treatment (Task A3)
- Stop trigger price: The threshold price that activates the order in the matching engine.
- Reference stop price ($P_{\text{stop, ref}}$): The barrier level specified by the research protocol ($P_{\text{entry, ref}}(1 \pm 1.5\sigma_t)$).
- Actual execution price ($P_{\text{exit, exec}}$): The price at which the order actually fills after crossing the book.
- Price Gap: When liquidity voids cause the fill to blow through the stop price, the entire gap is captured by $(P_{\text{exit, exec}} - P_{\text{stop, ref}})$.
- **Anti-Double-Counting:** This gap difference is captured directly in $C_{\text{exec\_dev}} = Q(-d)(P_{\text{exit, exec}} - P_{\text{stop, ref}})$. A separate "gap-risk" deduction must **NOT** be added.

### Five Synthetic Numerical Examples (Task A4)
1. **Example 1: Adverse Execution (Slippage > 0)**
   - Long 1.0 BTC ($d = +1$). Entry ref: $50,000$ USDT. Exit ref: $49,000$ USDT (stop barrier hit).
   - Fills: Entry at ref ($50,000$). Exit filled with adverse slippage at $48,950$ USDT ($50$ USDT slippage).
   - $L_{\text{price}} = -(+1) \times 1.0 \times (49,000 - 50,000) = 1,000.00$ USDT.
   - Fees: $0.0003 \times 50,000 + 0.0003 \times 48,950 = 15.00 + 14.685 = 29.685$ USDT.
   - Execution deviation (Approach B): $C_{\text{exec\_dev}} = 1.0 \times (-(+1)) \times (48,950 - 49,000) = +50.00$ USDT.
   - Funding: $CF_{\text{funding}} = 0.00$ USDT.
   - Realized Loss:
     $$L_{\text{realized}} = 1,000.00 + 29.685 + 50.00 - 0 = 1,079.685\text{ USDT}$$
2. **Example 2: Favorable Execution (Price Improvement, Execution Deviation < 0)**
   - Long 1.0 BTC ($d = +1$). Entry ref: $50,000$ USDT. Exit ref: $51,000$ USDT (take-profit hit).
   - Fills: Entry at ref ($50,000$). Exit limit order filled with price improvement at $51,050$ USDT.
   - $L_{\text{price}} = -(+1) \times 1.0 \times (51,000 - 50,000) = -1,000.00$ USDT (profit).
   - Fees: $0.0003 \times 50,000 + 0.0003 \times 51,050 = 15.00 + 15.315 = 30.315$ USDT.
   - Execution deviation (Approach B): $C_{\text{exec\_dev}} = 1.0 \times (-(+1)) \times (51,050 - 51,000) = -50.00$ USDT (favorable).
   - Funding: $CF_{\text{funding}} = 0.00$ USDT.
   - Realized Loss:
     $$L_{\text{realized}} = -1,000.00 + 30.315 + (-50.00) - 0 = -1,019.685\text{ USDT}$$
     (Net economic gain of $1,019.685$ USDT).
3. **Example 3: Gap-Through-Stop Execution**
   - Long 1.0 BTC ($d = +1$). Entry ref: $50,000$ USDT. Barrier stop ref: $49,000$ USDT.
   - Market gap blowout: Liquidity evaporates; stop fills at $P_{\text{exit, exec}} = 48,600$ USDT ($400$ USDT gap).
   - $L_{\text{price}} = -(+1) \times 1.0 \times (49,000 - 50,000) = 1,000.00$ USDT.
   - Fees: $0.0003 \times 50,000 + 0.0003 \times 48,600 = 15.00 + 14.58 = 29.58$ USDT.
   - Execution deviation: $C_{\text{exec\_dev}} = 1.0 \times (-(+1)) \times (48,600 - 49,000) = +400.00$ USDT.
   - Funding: $CF_{\text{funding}} = 0.00$ USDT.
   - Realized Loss:
     $$L_{\text{realized}} = 1,000.00 + 29.58 + 400.00 - 0 = 1,429.58\text{ USDT}$$
     The entire $400$ USDT gap is captured by $C_{\text{exec\_dev}}$; zero double-counting.
4. **Example 4: Funding Payment**
   - Short 10.0 ETH ($d = -1$). Entry ref: $3,000$ USDT ($N_{\text{entry}} = 30,000$). Exit ref: $3,060$ USDT (stop hit).
   - Fills at ref prices ($C_{\text{exec\_dev}} = 0.00$).
   - $L_{\text{price}} = -(-1) \times 10.0 \times (3,060 - 3,000) = 600.00$ USDT.
   - Fees: $0.0003 \times 30,000 + 0.0003 \times 30,600 = 9.00 + 9.18 = 18.18$ USDT.
   - Funding: Held across 3 settlements in bear regime where shorts pay longs (-1.5 bps / settlement).
     $CF_{\text{funding}} = -13.635$ USDT (funding paid).
   - Realized Loss:
     $$L_{\text{realized}} = 600.00 + 18.18 + 0.00 - (-13.635) = 631.815\text{ USDT}$$
     Funding payment increases loss.
5. **Example 5: Funding Receipt**
   - Short 10.0 ETH ($d = -1$). Entry ref: $3,000$ USDT. Exit ref: $3,060$ USDT (stop hit).
   - Fills at ref prices ($C_{\text{exec\_dev}} = 0.00$).
   - $L_{\text{price}} = 600.00$ USDT. Fees: $18.18$ USDT.
   - Funding: Held across 3 settlements in bull regime where longs pay shorts (+1.5 bps / settlement).
     $CF_{\text{funding}} = +13.635$ USDT (funding received).
   - Realized Loss:
     $$L_{\text{realized}} = 600.00 + 18.18 + 0.00 - (+13.635) = 604.545\text{ USDT}$$
     Funding receipt offsets fees and reduces loss.

*Qualification:* These examples verify the mathematical specification only. They do NOT constitute verification of production runtime simulation behavior (ISS_10 remains `NOT_VERIFIED`).

### Correlation Risk & Cross-Asset Dependence
- The unsupported claim $\rho > 0.70$ was removed because repository data lacks an empirical correlation matrix.
- Deleting the claim does NOT eliminate cross-asset dependence risk. In crypto markets, stress regimes exhibit sharp correlation spikes.
- Distinguish:
  1. *Historical Measured Correlation:* Pairwise empirical correlation across observed 5m returns (unmeasured in repo).
  2. *Assumed Stress Correlation:* Sensitivity parameter assuming elevated co-movement ($\rho \to 1.0$) during liquidation cascades.
  3. *Worst-Case Simultaneous Adverse Exposure:* All concurrent active positions hitting stop barriers simultaneously.
  4. *Portfolio Concentration Limits:* Structural ceilings on concurrent positions or net exposure.
- A fixed gross exposure cap alone does NOT prevent correlated drawdowns. Future risk controls (e.g. directional netting caps, factor exposure limits) are presented as candidate options, not approved controls. ISS_08 remains `OPEN` and `NOT_VERIFIED`.

### Explicit Removal of Unsupported Guarantees
The dossier does NOT claim:
- That portfolio loss is guaranteed to remain at or below 1%.
- That liquidation risk is completely eliminated.
- That stop-loss orders guarantee the assumed execution price.

### DEC_05 Decision Alternatives
- **Option 1 (Fixed Gross Exposure Cap):** Enforce hard limit on gross notional (e.g. $\sum |N_i| \le 0.30 \times \text{Equity}$). Simple to enforce; does not adjust for varying asset volatility.
- **Option 2 (Risk-Budget-Based Position Sizing):** Scale position notionals inversely with volatility ($N_i \propto 1 / \sigma_i$) so nominal stop loss is targeted at a fixed percentage of equity per position (e.g. 0.33% nominal risk per trade). Equalizes risk across assets; requires dynamic sizing logic.
- **Option 3 (Combined Exposure Cap and Stop-Risk Budget):** Enforce both a maximum gross notional cap (e.g. 50% equity) AND a per-position nominal stop-risk limit (e.g. 0.50% equity). Provides dual constraints; requires engineering both position sizing and portfolio concurrency controls.

---

## 6. DEC_06: XMR RESEARCH & PORTFOLIO SCOPE

### Data Coverage Disparity
- 10 Assets (BTC, ETH, BNB, XRP, ADA, SOL, AVAX, LINK, DOGE, LTC): 316,500 5m candles ($3.0$ years, October 2023 to October 2026).
- XMRUSDT: 83,863 5m candles ($9.5$ months, starting January 13, 2026).

### Three-Tier Policy and Hypothesis Family Link
1. **Tier 1 (Artifact Preservation):** 100% of XMR model binaries and preprocessors are preserved.
2. **Tier 2 (Standalone Research Reporting):** XMR economic metrics are evaluated and published in a dedicated standalone research appendix.
3. **Tier 3 (Primary Portfolio Acceptance):** XMR is excluded from primary portfolio aggregation, which fixes the primary confirmatory hypothesis family at **$K = 10$** (under Example A).
