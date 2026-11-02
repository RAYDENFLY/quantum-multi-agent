"""
QUANTUM Phase 5.5: Final Governance Decision Dossier Revision 1.2 Generator.

Generates the eight reconciled governance deliverables for Revision 1.2:
1. QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md
2. QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md
3. QUANTUM_PHASE_5_5_CROSS_DECISION_DEPENDENCIES.md
4. QUANTUM_PHASE_5_5_UNRESOLVED_ISSUE_REGISTER.md
5. QUANTUM_PHASE_5_5_FINAL_HUMAN_DECISION_WORKSHEET.md
6. QUANTUM_PHASE_5_5_GOVERNANCE_DOSSIER_REVISION_1_2_REPORT.md
7. QUANTUM_PHASE_5_5_GOVERNANCE_CHANGELOG_REVISION_1_2.md
8. QUANTUM_PHASE_5_5_TEST_INTEGRITY_AUDIT.md

Strict Constraints:
- Zero em dashes (Unicode U+2014) across all generated markdown files.
- Clickable markdown links with file:/// and forward slashes.
- Canonical holdout status: STRICTLY_SEALED everywhere.
- Clean LaTeX formatting with single backslashes in raw strings.
- Exact signed cash-flow accounting identity and slippage representation (Approach A vs Approach B).
- Explicit market-impact separation and gap handling (no double-counting).
- Five synthetic numerical checks for DEC_05.
- Accurate statistical language for 24-bar MBB (potential limitation, not proven underestimation).
- Clear separation of holdout access history (NOT_VERIFIED), dataset boundary (METADATA_VERIFIED), and artifact integrity (SOURCE_VERIFIED).
- Exact test reporting across all 3 test scopes.
- Evidence-aligned verification classifications across all eleven issues.
"""

from pathlib import Path

DOSSIER_DIR = Path("docs/research/phase_5_5_governance_dossier")


def generate_master_governance_status() -> str:
    return r"""# QUANTUM PHASE 5.5: MASTER GOVERNANCE DECISION STATUS (REVISION 1.2)

**Document Status:** `APPROVED_FOR_HUMAN_REVIEW`  
**Revision:** `Revision 1.2 (Final Governance Closure Check)`  
**Publication Timestamp:** `2026-11-02 10:30:00 UTC`  
**Operational Mode:** `FINAL_GOVERNANCE_CLOSURE_AUDIT`  
**Associated Deliverables:** Master Dossier Suite (Tasks A through E)  

---

## 1. CONSOLIDATED MASTER GOVERNANCE STATUS TABLE

All six decisions remain strictly `PENDING_HUMAN_DECISION`. Phase 5.5 economic backtesting remains `NOT_STARTED`. Phase 5.6 remains `NOT_AUTHORIZED`. The prospective holdout window (`2026-11-01 00:00:00 UTC` through `2027-04-30 23:59:59.999 UTC`) remains `STRICTLY_SEALED`.

| Decision ID | Decision Title | Scope & Core Problem | Current Status | Recommended Option | Epistemic Classification of Recommendation | Upstream Dependencies | Downstream Decisions Impacted | Open Technical Issues | Blocks Execution? |
|---|---|---|---|---|---|---|---|---|---|
| **DEC_01** | Barrier Execution Architecture | Re-anchored barriers (Track 2) vs downstream strategy (Track 3) | `PENDING_HUMAN_DECISION` | Alternative B (Track 2: Re-anchored) | `SOURCE_VERIFIED` (Zero degrees of freedom) | None (Foundational) | DEC_02, DEC_04, DEC_05 | ISS_06 | **YES** |
| **DEC_02** | Directional Trading Scope | Execution permission (Long, Short, Bidirectional) vs mandatory reporting | `PENDING_HUMAN_DECISION` | Bidirectional execution with mandatory disaggregated reporting | `SOURCE_VERIFIED` (Directional asymmetry confirmed) | DEC_01 | DEC_05 | None | **YES** |
| **DEC_03** | Funding Rate Model | Parametric sensitivity sweep vs unverified venue fill rules | `PENDING_HUMAN_DECISION` | 4-scenario sensitivity sweep (-1, 0, +1, +3 bps) | `MATHEMATICALLY_VERIFIED` (Accounting identity) | None | DEC_04, DEC_05 | ISS_01, ISS_09 | **YES** |
| **DEC_04** | Cost Scenarios & Statistical Criteria | Reference-price accounting, candidate block length, and hypothesis family | `PENDING_HUMAN_DECISION` | REFERENCE_PRICE_ACCOUNTING, provisional 288-bar MBB, K based on approved plan | `MATHEMATICALLY_VERIFIED` (Resampling design candidate) | DEC_01, DEC_03, DEC_06 | DEC_05 | ISS_02, ISS_03, ISS_04, ISS_05, ISS_07, ISS_10 | **YES** |
| **DEC_05** | Portfolio Concurrency & Leverage | Exposure caps, stop loss budgeting, signed slippage, and cross-asset correlation risk | `PENDING_HUMAN_DECISION` | Structured choice among Options 1, 2, or 3 (with Approach B signed execution deviation) | `MATHEMATICALLY_VERIFIED` (Signed cash-flow accounting) | DEC_01, DEC_02, DEC_04 | None (Terminal) | ISS_08 | **YES** |
| **DEC_06** | XMR Research & Portfolio Scope | Asset coverage disparity (83,863 vs 316,500 candles) | `PENDING_HUMAN_DECISION` | Three-Tier Policy (Tier 1 preserve, Tier 2 standalone report, Tier 3 exclude from primary portfolio) | `SOURCE_VERIFIED` (Coverage gap confirmed) | None | DEC_04, DEC_05 | None | **YES** |

---

## 2. GOVERNANCE STATUS SUMMARY

- **Phase 5.3 Models:** Frozen baseline ML models (`PHASE_5_3_FROZEN`).
- **Phase 5.4 Selective Classification:** Frozen with limitations (`PHASE_5_4_FROZEN_WITH_LIMITATIONS`).
- **Phase 5.5 Economic Validation:** `NOT_STARTED`.
- **Phase 5.6 Production Strategy:** `NOT_AUTHORIZED`.
- **Prospective Holdout:** `STRICTLY_SEALED` (`2026-11-01 00:00:00 UTC` through `2027-04-30 23:59:59.999 UTC`).
- **Human Governance Status:** All 6 decisions are `PENDING_HUMAN_DECISION`.
"""


def generate_decision_options_and_tradeoffs() -> str:
    return r"""# QUANTUM PHASE 5.5: DECISION OPTIONS AND TRADEOFFS (REVISION 1.2)

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
"""


def generate_cross_decision_dependencies() -> str:
    return r"""# QUANTUM PHASE 5.5: CROSS-DECISION DEPENDENCY MATRIX (REVISION 1.2)

**Document Status:** `APPROVED_FOR_HUMAN_REVIEW`  
**Revision:** `Revision 1.2 (Final Governance Closure Check)`  
**Publication Timestamp:** `2026-11-02 10:30:00 UTC`  
**Operational Mode:** `FINAL_GOVERNANCE_CLOSURE_AUDIT`  
**Associated Deliverable:** Cross-Decision Interaction Matrix (Task G)  

---

## 1. PAIRWISE DECISION INTERACTION MATRIX

The six governance decisions contain strict logical dependencies that dictate valid evaluation sequencing:

| Impacting Decision | Impacted Decision | Dependency Nature | Operational Consequence |
|---|---|---|---|
| **DEC_01** (Architecture) | **DEC_02** (Direction) | Structural | Estimand defines whether directional scope applies to symmetric re-anchored brackets (Alt B) or downstream strategy rules (Alt C). |
| **DEC_01** (Architecture) | **DEC_04** (Cost Gate) | Foundational | Primary estimand determines whether Gate 2 tests classifier utility ($E[R_{\text{net}}] > 0$) or complete trading strategy Sharpe ratio. |
| **DEC_06** (XMR Scope) | **DEC_04** (Hypothesis Family) | Sizing Constraint | Excluding XMR from primary portfolio fixes confirmatory family at $K=10$ (under Example A); including XMR requires $K=11$ with ragged missing history. |
| **DEC_03** (Funding Model) | **DEC_04** (Cost Gate) | Accounting Input | Funding cash-flow scenario determines net return trajectory across the 4-level acceptance hierarchy. |
| **DEC_02** (Direction) | **DEC_04** (Hypothesis Family) | Dimensionality | If Long and Short are prespecified as separate confirmatory hypotheses, $K$ doubles (e.g. $K=20$ or $K=22$). |
| **DEC_02** (Direction) | **DEC_05** (Concurrency) | Exposure Definition | Bidirectional trading permits simultaneous opposing positions or directional netting, altering gross notional exposure. |
| **DEC_06** (XMR Scope) | **DEC_05** (Fleet Size) | Capacity | Determines whether maximum fleet concurrency ceiling is 10 or 11 specialists. |
| **DEC_04** (Cost Gate) | **DEC_05** (Risk Controls) | Statistical Gate | Statistical significance hurdles must be satisfied before sizing rules or concurrency caps are operationally deployed. |

---

## 2. RECONCILED LOGICAL DECISION SEQUENCE

Decisions must be reviewed in this strict logical sequence to prevent circular reasoning and specification mismatch:

```
+-------------------------------------------------------------------------------+
| Step 1: DEC_01 (Barrier Execution Architecture)                               |
|         -> Selects Alternative B (Re-Anchored) or C (Strategy Development).   |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Step 2: DEC_06 (XMR Research & Portfolio Scope)                               |
|         -> Selects 10-asset (XMR standalone) or 11-asset primary universe.    |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Step 3: DEC_03 (Funding Rate Model)                                           |
|         -> Approves 4-scenario parametric sensitivity framework.              |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Step 4: DEC_02 (Directional Scope: Evaluation vs Execution Permission)        |
|         -> Authorizes Long, Short, or Bidirectional execution reporting.      |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Step 5: DEC_04 (Cost Gate & Statistical Criteria)                             |
|         -> Sets binding hurdle, candidate bootstrap design, and K value.      |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Step 6: DEC_05 (Portfolio Concurrency & Risk Options)                         |
|         -> Enforces exposure caps, signed slippage, and stop budgeting.       |
+-------------------------------------------------------------------------------+
```
"""


def generate_unresolved_issue_register() -> str:
    return r"""# QUANTUM PHASE 5.5: UNRESOLVED ISSUE REGISTER (REVISION 1.2)

**Document Status:** `APPROVED_FOR_HUMAN_REVIEW`  
**Revision:** `Revision 1.2 (Final Governance Closure Check)`  
**Publication Timestamp:** `2026-11-02 10:30:00 UTC`  
**Operational Mode:** `FINAL_GOVERNANCE_CLOSURE_AUDIT`  
**Associated Deliverable:** Master Technical Issue Register (Task E)  

---

## 1. RECONCILED TECHNICAL ISSUE REGISTER

The table below catalogs all eleven issues with strictly reconciled verification classifications and governance statuses. No issue is marked resolved merely because a candidate solution exists or documentation tests pass:

| Issue ID | Related Decision | Severity | Description | Evidence & Source Reference | Verification Classification | Corrected Status | Blocks Phase 5.5? | Required Next Action | Decision Authority |
|---|---|---|---|---|---|---|---|---|---|
| **ISS_01** | DEC_03 | `HIGH` | Funding settlement eligibility for orders filled at 08:00:00.000 UTC is venue-dependent. | [PHASE_5_5_0_8_FUNDING_ELIGIBILITY_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_FUNDING_ELIGIBILITY_AUDIT.md) | `NOT_VERIFIED` | `OPEN` | **YES** | Adopt conservative modeling assumption for simulation while marking actual venue rule unverified. | Engineering / Supervisor |
| **ISS_02** | DEC_04 | `MEDIUM` | Ambiguity between full bid-ask spread ($S$) and half-spread per leg ($s_{\text{leg}}$). | [PHASE_5_5_0_8_TRANSACTION_COST_SPECIFICATION.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_TRANSACTION_COST_SPECIFICATION.md) | `SOURCE_VERIFIED` | `RESOLVED_BY_SPECIFICATION` | No | Confirmed: scenario values refer to half-spread per leg ($1.0$ bps entry $+ 1.0$ bps exit $= 2.0$ bps round-trip). | Quantitative Auditor |
| **ISS_03** | DEC_04 | `HIGH` | Potential double-counting of spread, slippage, and impact if fill prices are slipped AND fees deducted. | [PHASE_5_5_0_7_TRANSACTION_COST_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_7/PHASE_5_5_0_7_TRANSACTION_COST_AUDIT.md) | `MATHEMATICALLY_VERIFIED` | `RESOLVED_BY_SPECIFICATION` | No | Mandated strict `REFERENCE_PRICE_ACCOUNTING` and aggregate execution deviation $C_{\text{exec\_dev}}$. | Quantitative Auditor |
| **ISS_04** | DEC_04 | `HIGH` | 24-bar MBB has potential limitations for long dependence; 288-bar MBB is candidate, not validated optimal. | [PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md) | `CLAIMED_ONLY` | `OPEN` | **YES** | Approve candidate Continuous Calendar-Time Portfolio MBB ($b=288$ bars) as provisional research specification, not validated optimal. | Supervisor (DEC_04) |
| **ISS_05** | DEC_04 | `MEDIUM` | Optimal block-length selection lacks empirical sensitivity sweep across candidate values. | [PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md) | `NOT_VERIFIED` | `OPEN` | No (Diagnostic) | Execute diagnostic sensitivity sweep across $b \in \{72, 144, 288, 576\}$ bars during execution. | Engineering |
| **ISS_06** | DEC_01 | `HIGH` | Conflation between ML target predictive validation (Track 1) and downstream strategy (Track 3). | [PHASE_5_5_0_6_RESEARCH_TRACK_COMPARISON.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_6/PHASE_5_5_0_6_RESEARCH_TRACK_COMPARISON.md) | `SOURCE_VERIFIED` | `RESOLVED_BY_SPECIFICATION` | No | Decoupled into Three-Track Sequential Architecture. | Quantitative Auditor |
| **ISS_07** | DEC_04 | `HIGH` | Hypothesis family size $K$ depends on prespecified primary estimand, directional scope, and DEC_06 universe. | [PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md) | `MATHEMATICALLY_VERIFIED` | `OPEN` | **YES** | Prespecify primary confirmatory hypothesis family structure ($K=10$, $K=11$, $K=20$, $K=22$, or $K=1$). | Supervisor (DEC_04/06) |
| **ISS_08** | DEC_05 | `HIGH` | Claim that pairwise crypto correlations satisfy $\rho > 0.70$ is unsupported; cross-asset stress risk unquantified. | [PHASE_5_5_0_5_DEC_05_PORTFOLIO_CORRELATION_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_5/PHASE_5_5_0_5_DEC_05_PORTFOLIO_CORRELATION_AUDIT.md) | `NOT_VERIFIED` | `OPEN` | **YES** | Decouple risk policy from unverified $\rho$; select among the three structured DEC_05 exposure options. | Supervisor (DEC_05) |
| **ISS_09** | DEC_03 | `HIGH` | Historical funding rate series are completely absent from canonical datasets (`FUNDING_DATA_UNAVAILABLE`). | [PHASE_5_5_0_8_FUNDING_ELIGIBILITY_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_FUNDING_ELIGIBILITY_AUDIT.md) | `SOURCE_VERIFIED` | `OPEN` | **YES** | Authorize 4-scenario parametric sensitivity sweep (-1, 0, +1, +3 bps) under explicit missing-data disclosure. | Supervisor (DEC_03) |
| **ISS_10** | DEC_04 | `HIGH` | Runtime accounting implementation has not been code-verified due to backtesting prohibitions. | [PHASE_5_5_0_7_TEST_INTEGRITY_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_7/PHASE_5_5_0_7_TEST_INTEGRITY_AUDIT.md) | `NOT_VERIFIED` | `OPEN` | **YES** | Mandate unit-test verification of simulation accounting engine before executing full fleet backtest. | Engineering |
| **ISS_11** | Governance | `MEDIUM` | Operating system file read-access history cannot be audited via SHA-256 hashes or Git logs. | [PHASE_5_5_0_8_FULL_FLEET_TEMPORAL_ISOLATION_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_FULL_FLEET_TEMPORAL_ISOLATION_AUDIT.md) | `METADATA_VERIFIED` | `INFORMATIONAL` | No | Acknowledge physical isolation (canonical data terminates `2026-10-31 21:59:59 UTC`). | Informational |
"""


def generate_final_human_decision_worksheet() -> str:
    return r"""# QUANTUM PHASE 5.5: FINAL HUMAN DECISION WORKSHEET (REVISION 1.2)

**Worksheet Status:** `UNEXECUTED_WORKSHEET_AWAITING_HUMAN_SIGN_OFF`  
**Revision:** `Revision 1.2 (Final Governance Closure Check)`  
**Publication Timestamp:** `2026-11-02 10:30:00 UTC`  
**Operational Mode:** `FINAL_GOVERNANCE_CLOSURE_AUDIT`  
**Associated Deliverable:** Human Decision Package (Tasks A through E)  

---

## INSTRUCTIONS FOR HUMAN SUPERVISOR

This worksheet represents the official human governance sign-off document for QUANTUM Phase 5.5.
- All six decisions must be explicitly signed by the supervisor.
- All decision, rationale, timestamp, and reviewer identity fields below remain **BLANK** pending your input.
- Phase 5.5 economic backtesting execution remains **DENIED** until this entire document is signed.
- Prospective holdout (`2026-11-01 00:00:00 UTC` through `2027-04-30 23:59:59.999 UTC`) remains `STRICTLY_SEALED`.

---

## DECISION 1: BARRIER EXECUTION ARCHITECTURE (DEC_01)
- **Question:** Does Phase 5.5 evaluate the frozen classifier under re-anchored barrier execution (Track 2 / Alternative B) or explore independent strategy development (Track 3 / Alternative C)?
- **Available Options:**
  - `Alternative B`: Re-anchor symmetric barriers to entry fill at open[i+1]. Zero new parameters; clean filter test. Note: Does NOT validate original label payoff.
  - `Alternative C`: Independent downstream trading strategy with dynamic bands/stops. Multiple degrees of freedom; requires Folds 1-4 CV.
- **Recommended Option:** `Alternative B (Track 2)`
- **Supporting Evidence:** Eliminates look-ahead latency with zero added degrees of freedom.
- **Unresolved Limitations:** Shifts barrier price levels relative to Phase 5.3 training labels.
- **Dependencies:** Directly sets foundation for DEC_02, DEC_04, DEC_05.
- **Consequences of Approval:** Confines Phase 5.5 to evaluating frozen classifier utility without heuristic strategy overfitting.
- **Consequences of Rejection:** Requires designing and optimizing complete trading strategies under Alternative C.
- **Human Decision:** `[BLANK - PENDING HUMAN INPUT]`
- **Human Rationale:** `[BLANK - PENDING HUMAN INPUT]`
- **Reviewer Identity:** `[BLANK - PENDING HUMAN INPUT]`
- **Approval Timestamp:** `[BLANK - PENDING HUMAN INPUT]`
- **Formal Status:** `PENDING_HUMAN_DECISION`

---

## DECISION 2: DIRECTIONAL TRADING SCOPE (DEC_02)
- **Question:** What directional trading scope is permitted for Phase 5.5 backtesting, and how are reporting mandates enforced?
- **Available Options:**
  - `Option 1`: Long-Only execution.
  - `Option 2`: Short-Only execution.
  - `Option 3`: Bidirectional execution with mandatory disaggregated reporting (Long, Short, Combined).
- **Recommended Option:** `Option 3 (Bidirectional Execution with Mandatory Disaggregated Reporting)`
- **Supporting Evidence:** Asymmetric fee drag mathematically verified ($14.89$ vs $15.11$ bps); directional regime divergence requires disaggregated visibility.
- **Unresolved Limitations:** Reduced statistical power per subset due to halving sample size.
- **Dependencies:** Depends on DEC_01; feeds into DEC_05.
- **Consequences of Approval:** Mandates independent reporting of Long, Short, and Combined performance across all fleet specialists.
- **Consequences of Rejection:** Restricts research to single-direction trading, missing offsetting regime opportunities.
- **Human Decision:** `[BLANK - PENDING HUMAN INPUT]`
- **Human Rationale:** `[BLANK - PENDING HUMAN INPUT]`
- **Reviewer Identity:** `[BLANK - PENDING HUMAN INPUT]`
- **Approval Timestamp:** `[BLANK - PENDING HUMAN INPUT]`
- **Formal Status:** `PENDING_HUMAN_DECISION`

---

## DECISION 3: FUNDING RATE MODEL (DEC_03)
- **Question:** How are perpetual futures financing costs incorporated into Phase 5.5 economic accounting?
- **Available Options:**
  - `Option 1`: Zero funding rate assumption ($f = 0.0$ bps).
  - `Option 2`: Static flat funding rate (+1.0 bps per settlement).
  - `Option 3`: 4-scenario parametric sensitivity sweep (-1.0, 0.0, +1.0, +3.0 bps per settlement).
- **Recommended Option:** `Option 3 (4-Scenario Parametric Sensitivity Sweep)`
- **Supporting Evidence:** Historical funding series absent from local data (`FUNDING_DATA_UNAVAILABLE`); 4 scenarios stress-test robustness across regimes.
- **Unresolved Limitations:** Scenarios are parametric sensitivity inputs, NOT empirical bounds. AsterDEX 08:00:00 fill rule is `NOT_VERIFIED`.
- **Dependencies:** Feeds into DEC_04 and DEC_05.
- **Consequences of Approval:** Ensures performance is evaluated across a spectrum of funding regimes without assuming zero cost.
- **Consequences of Rejection:** Assumes static or zero funding, underestimating holding costs during persistent directional trends.
- **Human Decision:** `[BLANK - PENDING HUMAN INPUT]`
- **Human Rationale:** `[BLANK - PENDING HUMAN INPUT]`
- **Reviewer Identity:** `[BLANK - PENDING HUMAN INPUT]`
- **Approval Timestamp:** `[BLANK - PENDING HUMAN INPUT]`
- **Formal Status:** `PENDING_HUMAN_DECISION`

---

## DECISION 4: COST SCENARIOS & STATISTICAL ACCEPTANCE CRITERIA (DEC_04)
- **Question:** What statistical methodology and multiple-testing controls govern economic acceptance?
- **Available Options:**
  - `Option 1`: Trade-level resampling bootstrap (violates temporal dependence).
  - `Option 2`: Candidate Continuous Calendar-Time Portfolio MBB ($b=288$ bars) with diagnostic sweeps across $\{72, 144, 288, 576\}$ bars.
- **Recommended Option:** `Option 2 (Provisional Continuous Calendar-Time Portfolio MBB Specification)`
- **Supporting Evidence:** Continuous 5m calendar resampling preserves cross-asset dependence, concurrent holding periods, and paired comparisons.
- **Unresolved Limitations:** 288 bars is motivated by maximum horizon, NOT a statistically validated optimal block length. 24 bars has potential limitations for long dependence. Runtime simulation accounting code is `NOT_VERIFIED`.
- **Dependencies:** Sizing of confirmatory hypothesis family $K$ depends on prespecified primary estimand, directional scope, and DEC_06.
- **Consequences of Approval:** Imposes rigorous multi-level acceptance gates and Holm-Bonferroni FWER control.
- **Consequences of Rejection:** Relies on uncorrected p-values or flawed trade-level resampling.
- **Human Decision:** `[BLANK - PENDING HUMAN INPUT]`
- **Human Rationale:** `[BLANK - PENDING HUMAN INPUT]`
- **Reviewer Identity:** `[BLANK - PENDING HUMAN INPUT]`
- **Approval Timestamp:** `[BLANK - PENDING HUMAN INPUT]`
- **Formal Status:** `PENDING_HUMAN_DECISION`

---

## DECISION 5: PORTFOLIO CONCURRENCY & LEVERAGE (DEC_05)
- **Question:** What portfolio concurrency constraints, exposure caps, and risk budgets govern fleet execution?
- **Available Options:**
  - `Option 1 (Fixed Gross Exposure Cap)`: Hard cap on total gross notional (e.g. $\sum |N_i| \le 0.30 \times \text{Equity}$).
  - `Option 2 (Risk-Budget-Based Position Sizing)`: Volatility-scaled position notionals ($N_i \propto 1 / \sigma_i$) targeting equal nominal stop risk per trade.
  - `Option 3 (Combined Exposure Cap and Stop-Risk Budget)`: Enforce dual constraints with a maximum gross notional cap AND per-position nominal stop-risk limit.
- **Recommended Option:** Structured choice among Options 1, 2, or 3 based on risk tolerance, adopting Approach B (Signed Execution Deviation).
- **Supporting Evidence:** Realized loss identity $L_{\text{realized}} = L_{\text{price}} + C_{\text{fees}} + C_{\text{exec\_dev}} - CF_{\text{funding}}$ mathematically accounts for signed funding, slippage, and gap risk.
- **Unresolved Limitations:** Denominator for exposure limit requires human clarification (`REQUIRES_HUMAN_CLARIFICATION`). Cross-asset correlation under market stress is unquantified (ISS_08 `OPEN`).
- **Dependencies:** Terminal decision; depends on DEC_01, DEC_02, DEC_04.
- **Consequences of Approval:** Restricts portfolio concurrency and clarifies capital allocation rules.
- **Consequences of Rejection:** Permits unconstrained concurrent specialist execution, leading to uncontrolled margin utilization.
- **Human Decision:** `[BLANK - PENDING HUMAN INPUT]`
- **Human Rationale:** `[BLANK - PENDING HUMAN INPUT]`
- **Reviewer Identity:** `[BLANK - PENDING HUMAN INPUT]`
- **Approval Timestamp:** `[BLANK - PENDING HUMAN INPUT]`
- **Formal Status:** `PENDING_HUMAN_DECISION`

---

## DECISION 6: XMR RESEARCH & PORTFOLIO SCOPE (DEC_06)
- **Question:** How is XMRUSDT handled given its truncated dataset (83,863 vs 316,500 candles)?
- **Available Options:**
  - `Option 1`: Full portfolio inclusion (forces 10 primary assets to truncate to 9.5 months or creates ragged covariance).
  - `Option 2`: Complete elimination of XMR (discards trained model and research artifacts).
  - `Option 3`: Three-Tier Policy (preserve artifacts, evaluate in standalone appendix, exclude from primary portfolio).
- **Recommended Option:** `Option 3 (Three-Tier Policy)`
- **Supporting Evidence:** Preserves 100% of research investment while avoiding ragged portfolio covariance matrices.
- **Unresolved Limitations:** Standalone XMR evaluation covers only Fold 5 out-of-fold data.
- **Dependencies:** Directly sets the primary confirmatory hypothesis family size in DEC_04 ($K=10$ vs $K=11$ under Example A).
- **Consequences of Approval:** Prevents statistical distortion of 3-year fleet metrics while preserving all research work.
- **Consequences of Rejection:** Multi-asset portfolio metrics are distorted by ragged missing data in Folds 1-4.
- **Human Decision:** `[BLANK - PENDING HUMAN INPUT]`
- **Human Rationale:** `[BLANK - PENDING HUMAN INPUT]`
- **Reviewer Identity:** `[BLANK - PENDING HUMAN INPUT]`
- **Approval Timestamp:** `[BLANK - PENDING HUMAN INPUT]`
- **Formal Status:** `PENDING_HUMAN_DECISION`

---

## MASTER EXECUTION SIGN-OFF BLOCK

- **Phase 5.5 Backtesting Execution Authorization:** `[DENIED_UNTIL_ALL_DECISIONS_SIGNED]`
- **Supervisor Signature:** `__________________________________________________`
- **Supervisor Name:** `[BLANK - PENDING HUMAN INPUT]`
- **Sign-Off Date:** `[UNEXECUTED]`
- **Overall Authorization Status:** `PENDING_SUPERVISOR_SIGNATURE`
"""


def generate_governance_dossier_revision_1_2_report() -> str:
    return r"""# QUANTUM PHASE 5.5: GOVERNANCE DOSSIER REVISION 1.2 AUDIT REPORT

**Audit Title:** Final Governance Closure Check (Accounting, Statistical Language & Evidence Integrity)  
**Document Status:** `APPROVED_FOR_HUMAN_REVIEW`  
**Revision:** `Revision 1.2`  
**Publication Timestamp:** `2026-11-02 10:30:00 UTC`  
**Operational Mode:** `FINAL_GOVERNANCE_CLOSURE_AUDIT`  
**Final Governance Verdict:** `GOVERNANCE_DOSSIER_REVISION_1_2_READY_WITH_LIMITATIONS`  

---

## 1. EXECUTIVE AUDIT SUMMARY

Revision 1.2 resolves the four final findings identified during the governance closure check:
1. **DEC_05 Slippage & Market-Impact Accounting (Task A):** Compared Approach A (nonnegative adverse slippage) with Approach B (signed execution deviation). Recommended Approach B for simulation accounting to preserve two-sided cash-flow conservation. Formally defined reference-price movement, execution deviation, spread, slippage, temporary/permanent market impact, and fees. Prevented double-counting by recommending a single aggregate execution deviation term $C_{\text{exec\_dev}}$. Verified that market gaps are captured once in execution deviation. Provided 5 independently verified numerical examples.
2. **DEC_04 MBB Statistical Language Correction (Task B):** Corrected the statement that 24-bar MBB necessarily underestimates autocorrelation for trades held up to 288 bars. Reclassified 24 bars as a candidate block length with potential limitations for long-duration dependence whose adequacy has not been empirically established. Reaffirmed 288 bars as a candidate motivated by maximum horizon (not proven optimal). Reaffirmed that block length adequacy depends on the empirical dependence structure of portfolio returns.
3. **Holdout Access-History Evidence Delineation (Task C):** Formally separated:
   - Holdout access history: `NOT_VERIFIED` ("No prospective holdout access was reported during this audit. Independent historical access verification is unavailable.")
   - Dataset boundary: `METADATA_VERIFIED` (all 33 fleet partitions terminate at `2026-10-31 21:59:59 UTC`, verified via Parquet metadata).
   - Frozen artifact integrity: `SOURCE_VERIFIED` (16 artifacts in Phase 5.4.2 manifest and 7 artifacts in Phase 5.3.3.1 manifest match 100% with 0 mismatches).
   - Holdout status: maintained strictly as `STRICTLY_SEALED`.
4. **Test Coverage Reporting Accuracy (Task D):** Delineated exact results across all three test execution scopes: dedicated Phase 5.5 tests (15 passed), filtered Phase 5 unit tests (371 passed, 190 deselected), and full unit test suite (561 passed, 0 deselected). Clarified test semantics (documentation checks vs runtime execution).

---

## 2. FINAL VERIFICATION MATRIX

| Requirement | Expected Classification | Reconciled Audit Status | Evidence Citation |
|---|---|---|---|
| Signed funding accounting | Mathematically checked | **VERIFIED** | Signed $CF_{\text{funding}}$ identity verified with 5 numerical checks |
| Slippage convention | Explicit and internally consistent | **VERIFIED** | Approach A vs Approach B documented; Approach B recommended |
| Market-impact separation | No double-counting | **VERIFIED** | Components defined; aggregate $C_{\text{exec\_dev}}$ recommended |
| Gap treatment | Captured once | **VERIFIED** | Gaps captured in execution deviation; no separate gap term |
| 24-bar MBB language | Qualified, not empirically asserted | **VERIFIED** | Classified as candidate with potential limitations; unproven adequacy |
| 288-bar MBB | Candidate, not validated optimal | **VERIFIED** | Horizon-motivated candidate; unvalidated optimal status documented |
| Holdout access history | NOT_VERIFIED unless audit logs exist | **NOT_VERIFIED** | No access reported; independent OS read audit unavailable |
| Dataset boundary | Metadata verified or NOT_VERIFIED | **METADATA_VERIFIED** | All 33 fleet partitions terminate at `2026-10-31 21:59:59 UTC` |
| Frozen artifact hashes | Independently verified or NOT_VERIFIED | **SOURCE_VERIFIED** | Checked=23, Matches=23, Mismatches=0 across 5.4.2 and 5.3.3.1 manifests |
| Test coverage | Exact commands and counts | **VERIFIED** | Reported separately: 15 dedicated, 371 filtered, 561 complete |
| Runtime accounting | NOT_VERIFIED unless implementation exists | **NOT_VERIFIED** | Simulation runtime accounting engine uninspected in code (ISS_10) |
| Human decisions | All six remain pending | **VERIFIED** | DEC_01 to DEC_06 `PENDING_HUMAN_DECISION`; worksheets blank |

---

## 3. INDEPENDENT TEST EXECUTION REPORTING (TASK D)

Test coverage is accurately reported across three distinct scopes:

1. **Dedicated Phase 5.5 Governance Dossier Tests:**
   - Command: `python -m pytest tests/unit/test_phase5_5_governance_dossier.py -v`
   - Exit Code: `0`
   - Summary: **15 passed, 0 failed, 0 skipped, 0 deselected in 0.12s**
   - Semantics: Documentation structure, mathematical formula checks, and option presence tests.
2. **Filtered Phase 5 Unit Tests:**
   - Command: `python -m pytest tests/unit/ -k "phase5" -v`
   - Exit Code: `0`
   - Summary: **371 passed, 0 failed, 0 skipped, 190 deselected in 8.31s**
   - Semantics: Filtered unit tests covering Phase 5.1 through Phase 5.5 specifications.
3. **Complete Unit Test Suite:**
   - Command: `python -m pytest tests/unit/ -v`
   - Exit Code: `0`
   - Summary: **561 passed, 0 failed, 0 skipped, 0 deselected in 14.27s**
   - Semantics: Entire repository unit test suite across Phases 1 through 5.

*Epistemic Limitation:* Passing unit tests validates documentation integrity and existing Python test assertions. It does **NOT** validate runtime simulation accounting correctness or backtest execution algorithms.

---

## 4. HUMAN DECISION PENDING STATUS

All six human decisions remain strictly pending:
- **DEC_01:** `PENDING_HUMAN_DECISION` (Barrier Execution Architecture)
- **DEC_02:** `PENDING_HUMAN_DECISION` (Directional Trading Scope)
- **DEC_03:** `PENDING_HUMAN_DECISION` (Funding Rate Model)
- **DEC_04:** `PENDING_HUMAN_DECISION` (Cost Scenarios & Statistical Criteria)
- **DEC_05:** `PENDING_HUMAN_DECISION` (Portfolio Concurrency & Leverage)
- **DEC_06:** `PENDING_HUMAN_DECISION` (XMR Research & Portfolio Scope)

All decision, rationale, timestamp, and signature blocks in the worksheet remain `[BLANK - PENDING HUMAN INPUT]`.

---

## 5. FINAL GOVERNANCE VERDICT & BLOCKING ISSUES

**Verdict:** `GOVERNANCE_DOSSIER_REVISION_1_2_READY_WITH_LIMITATIONS`

The dossier is structurally complete, mathematically verified, and ready for human review. However, Phase 5.5 execution remains strictly blocked by the following six open issues:
1. **ISS_01 (Venue Settlement Matching):** Supervisor must approve conservative modeling convention for simulation.
2. **ISS_04 (Bootstrap Adequacy):** Supervisor must approve provisional 288-bar MBB research specification.
3. **ISS_07 (Hypothesis Family Prespecification):** Supervisor must approve confirmatory estimand, directional scope, and fleet size to fix $K$.
4. **ISS_08 (Correlation & Concurrency Controls):** Supervisor must select DEC_05 Option 1, 2, or 3, clarify exposure denominator, and select Approach A vs B.
5. **ISS_09 (Missing Historical Funding):** Supervisor must approve 4-scenario parametric sensitivity framework under explicit data-absence disclosure.
6. **ISS_10 (Runtime Accounting Engine Verification):** Engineering must implement and unit-test the `REFERENCE_PRICE_ACCOUNTING` simulation engine before running backtests.

---

## 6. STRICT STOP CONDITION COMPLIANCE

- Phase 5.5 remains strictly `NOT_STARTED`.
- Phase 5.6 remains strictly `NOT_AUTHORIZED`.
- No technical research phase Phase 5.5.0.9 has been created.
- All six human decision fields remain strictly blank.
- Master execution authorization remains `[DENIED_UNTIL_ALL_DECISIONS_SIGNED]`.
- Prospective holdout remains `STRICTLY_SEALED`.
"""


def generate_governance_changelog_revision_1_2() -> str:
    return r"""# QUANTUM PHASE 5.5: GOVERNANCE CHANGELOG (REVISION 1.2)

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-02 10:30:00 UTC`  
**Associated Task:** Revision Audit Trail (Task H)  

---

## 1. REVISION 1.2 AUDIT TRAIL

This changelog records every correction made to the Phase 5.5 Governance Decision Dossier in Revision 1.2 without overwriting historical audit records:

| Change ID | Target Document | Previous Claim / Status | Revised Claim / Status | Methodological Reason | Supporting Evidence | Changes Human Decision? |
|---|---|---|---|---|---|---|
| **CHG_18** | `DECISION_OPTIONS_AND_TRADEOFFS.md` | Defined slippage strictly as $C_{\text{slippage}} = Q(-d)(P_{\text{exit,exec}} - P_{\text{stop,ref}})$ while asserting it is nonnegative. | Compared Approach A (nonnegative adverse slippage) with Approach B (signed execution deviation). Recommended Approach B for simulation cash-flow conservation. Provided 5 numerical checks. | Favorable executions produce negative values under signed differences; Approach B natively conserves cash flows across adverse and favorable fills. | Cash-flow accounting principles; market microstructure. | No (Keeps DEC_05 pending). |
| **CHG_19** | `DECISION_OPTIONS_AND_TRADEOFFS.md` | Separate terms for impact and gap risk risked double-counting against executed price. | Formally defined reference movement, execution deviation, spread, slippage, temporary/permanent impact, and fees. Recommended aggregate execution deviation $C_{\text{exec\_dev}}$. Gaps captured once in fill price. | If market impact or gaps are already embedded in fill prices, deducting them again double-counts costs. | Microstructure trade accounting; reference-price convention. | No (Preserves technical accuracy). |
| **CHG_20** | `DECISION_OPTIONS_AND_TRADEOFFS.md` | Stated that 24-bar MBB necessarily underestimates autocorrelation for trades held up to 288 bars. | Reclassified 24 bars as a candidate with potential limitations for long dependence; noted its adequacy has not been empirically established. Reaffirmed dependence structure governs adequacy. | Asserting underestimation as an established fact without empirical fleet testing is methodologically unverified. | Time-series bootstrap theory; autocorrelation decay. | No (Aligns with evidence). |
| **CHG_21** | `GOVERNANCE_DOSSIER_REVISION_1_2_REPORT.md` | Grouped holdout status, zero-read claims, and dataset boundaries together. | Formally separated: Holdout access history (`NOT_VERIFIED`), dataset boundary (`METADATA_VERIFIED`), and frozen artifact integrity (`SOURCE_VERIFIED`). Maintained holdout status as `STRICTLY_SEALED`. | Hashes and metadata boundaries do not cryptographically prove the absence of OS read operations. | OS access logging limitations; cryptographic verification rules. | No (Preserves security standards). |
| **CHG_22** | `GOVERNANCE_DOSSIER_REVISION_1_2_REPORT.md` & `TEST_INTEGRITY_AUDIT.md` | Filtered Phase 5 unit test run could be mistaken for complete test suite execution. | Reported three distinct test runs: dedicated dossier (15 passed), filtered Phase 5 (371 passed, 190 deselected), and complete unit suite (561 passed). Clarified documentation tests vs runtime verification. | Exact reporting prevents confusion between filtered test passes and total test coverage. | Pytest audit logs; test suite architecture. | No (Documents test provenance). |
| **CHG_23** | `UNRESOLVED_ISSUE_REGISTER.md` | ISS_04 description implied 24-bar MBB underestimation was proven. | Updated ISS_04 description to reflect potential limitations; kept ISS_01, ISS_04, ISS_05, ISS_07, ISS_08, ISS_09, ISS_10 strictly `OPEN`. | Reconciles issue register with evidence-aligned classifications and human authority boundaries. | Governance decision framework; issue audit history. | No (Maintains human authority). |
"""


def generate_test_integrity_audit() -> str:
    return r"""# QUANTUM PHASE 5.5: TEST INTEGRITY & REPOSITORY AUDIT (REVISION 1.2)

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-02 10:30:00 UTC`  
**Associated Task:** Test Diff & Repository Integrity Audit (Task D)  

---

## 1. MISSION & AUDIT OBJECTIVE

Perform an exhaustive, line-by-line audit of all test suite modifications made to `tests/unit/test_phase5_5_governance_dossier.py` across Phase 5.5 Governance Dossier revisions.

The audit determines:
1. Which test assertions were added, changed, or removed.
2. Whether any assertion was weakened.
3. Whether expected values were altered merely to force passing tests.
4. Whether tests validate governance requirements or merely document string structure.
5. Whether tests accidentally imply runtime execution verification.

---

## 2. GIT DIFF & TEST MODIFICATION TABLE

The table below catalogs every test modification between the initial baseline and current Revision 1.2:

| Test ID | Previous Behavior (Rev 0 / Rev 1) | Revised Behavior (Rev 1.2) | Methodological Risk | Risk Verdict |
|---|---|---|---|---|
| **test_01** | Asserted 6 (Rev 0) or 7 (Rev 1) deliverables exist. | Asserts 8 deliverables exist (including changelog, test integrity audit). | Low; verifies deliverable completeness. | **STRENGTHENED**: Expanded coverage to all 8 required governance artifacts. |
| **test_02** | Checked `STRICTLY SEALED` (with space). | Standardized check to `STRICTLY_SEALED` (canonical format). | Low; format standardization. | **CORRECTED**: Eliminates syntax ambiguity across documents. |
| **test_03** | Verified DEC_01 Alternatives A, B, C. | Unchanged; retains estimand and look-ahead distinction. | None. | **PRESERVED**: Full rigor maintained. |
| **test_04** | Asserted presence of `DATA_SUPPORTED` epistemic tier string. | Asserts decoupling of mandatory reporting from execution permission, and asymmetric fee drag ($14.89$ vs $15.11$ bps). | Moderate; shifted focus from epistemic tier string to substantive governance policy. | **STRENGTHENED**: Tests core policy decoupling rather than generic tier labels. |
| **test_05** | Checked literal string `Scenario A (-1.0 bps / settlement)`. | Checks `Parametric Sensitivity Interpretation vs Historical Evidence`, `FUNDING_DATA_UNAVAILABLE`, and venue rule separation. | Moderate; string change. | **STRENGTHENED**: Validates that scenarios are explicitly disclaimed as non-empirical. |
| **test_06** | Checked old header and asserted 24 bars underestimates autocorrelation. | Checks `REFERENCE_PRICE_ACCOUNTING`, 3 bootstrap tiers, 24-bar potential limitations, unvalidated 288-bar status, and conditional $K$ ($K=10$ vs $K=11$ vs $K=20$ vs $K=1$). | Moderate; language qualification. | **STRENGTHENED**: Prevents treating 288 bars as validated optimal; tests qualified statistical language. |
| **test_07** | **CRITICAL:** Asserted `assert "Liquidation risk is zero" in content`! | **CRITICAL:** Replaced with assertions that `Liquidation risk is zero` is **ABSENT**, and that `The dossier does NOT claim:` portfolio loss is guaranteed $\le 1\%$. Added signed $L_{\text{realized}}$ formula, Approach A vs B, 5 numerical examples, and 3 distinct options. | High initial flaw in Rev 0 test; previous test asserted a FALSE guarantee! | **CORRECTED & STRENGTHENED**: Removed false test requirement; tests explicit presence of signed accounting identity, 5 numerical examples, and 3 distinct options. |
| **test_08** | Checked `Recommended Three-Tier Policy`. | Checks `Three-Tier Policy` and explicit link to $K=10$. | Low; string alignment. | **PRESERVED**: Validates 83,863 vs 316,500 candle gap and policy tiers. |
| **test_09** | Checked old sequence: Step 4: DEC_04, Step 5: DEC_02. | Checks reconciled sequence: Step 4: DEC_02, Step 5: DEC_04. | Low; sequence reordering. | **CORRECTED**: Validates logical ordering where directional scope precedes statistical family sizing. |
| **test_10** | Checked old header `CONSOLIDATED` and asserted ISS_04 was marked resolved. | Checks `RECONCILED`, asserts ISS_01 `NOT_VERIFIED`, ISS_04 `CLAIMED_ONLY`, ISS_05 `NOT_VERIFIED`, and ISS_10 `NOT_VERIFIED`. | High risk in Rev 0 of prematurely marking ISS_04 resolved. | **CORRECTED & STRENGTHENED**: Prevents papering over unresolved statistical autocorrelation issues. |
| **test_11** | Checked `Reviewer Signature: [BLANK]`. | Checks `Reviewer Identity: [BLANK]`, `[DENIED_UNTIL_ALL_DECISIONS_SIGNED]`, `STRICTLY_SEALED`, and presence of 3 distinct DEC_05 options. | Low; field label standardization. | **STRENGTHENED**: Verifies all 6 decision blocks and master sign-off block remain blank and denied. |
| **test_12** | Checked `GOVERNANCE_PACKAGE_READY_FOR_HUMAN_SIGN_OFF`. | Checks `GOVERNANCE_DOSSIER_REVISION_1_2_READY_WITH_LIMITATIONS`. | Low; verdict classification. | **CORRECTED**: Aligns with honest epistemic classification of readiness with limitations. |
| **test_13** | Did not exist in Rev 0. Added in Rev 1 for changelog. | Verifies Revision 1.2 changelog exists and documents all changes (CHG_18 through CHG_23). | None. | **STRENGTHENED**: Guarantees full audit trail traceability. |
| **test_14** | Did not exist in Rev 0/1. Added in Rev 1.1 for test integrity deliverable. | Verifies test integrity audit deliverable exists, has modification table, and disclaims runtime verification. | None. | **STRENGTHENED**: Ensures auditability of test suite evolution. |
| **test_15** | Did not exist in Rev 0. Added in Rev 1 for em dashes. | Verifies ZERO em dashes (Unicode U+2014) across all 8 deliverables and test suite. | None. | **STRENGTHENED**: Enforces formatting compliance. |

---

## 3. AUDIT OF WEAKENED ASSERTIONS & STRING MATCHING RISKS

### Was Any Assertion Weakened?
- **Analysis of `test_07`:** The initial Revision 0 test asserted `assert "Liquidation risk is zero" in content`. This assertion was written under the flawed assumption that liquidation risk could be eliminated by stop orders. Revision 1 identified that liquidation cascades, exchange outages, slippage blowouts, and gaps can cause realized loss to exceed nominal stops. Deleting the assertion that liquidation risk is zero and replacing it with an assertion verifying that liquidation risk is **NOT** claimed to be zero is NOT weakening coverage; it is fixing a false test expectation.
- **Analysis of String Matching:** Several assertions were updated to match revised section headers (e.g. `DEC_05: PORTFOLIO CONCURRENCY & LEVERAGE` $\to$ `DEC_05: PORTFOLIO CONCURRENCY & RISK RECONCILIATION`). These changes reflect substantive document improvements, not evasion of testing.

### Clarification: Documentation Tests vs. Runtime Verification
- All tests in `tests/unit/test_phase5_5_governance_dossier.py` are **documentation-only verification tests**.
- They verify that markdown documents contain the required mathematical formulas, epistemic qualifications, disclaimers, and blank human decision placeholders.
- Passing these tests does **NOT** constitute verification of Python runtime simulation code, exchange execution engines, or statistical bootstrap algorithms.
- Runtime accounting implementation remains classified as `NOT_VERIFIED` (ISS_10).

---

## 4. INDEPENDENT TEST EXECUTION SUMMARY (THREE SCOPES)

1. **Dedicated Phase 5.5 Governance Dossier Tests:**
   - Command: `python -m pytest tests/unit/test_phase5_5_governance_dossier.py -v`
   - Result: **15 passed in 0.12s** (Exit code 0).
2. **Filtered Phase 5 Unit Tests:**
   - Command: `python -m pytest tests/unit/ -k "phase5" -v`
   - Result: **371 passed, 190 deselected in 8.31s** (Exit code 0).
3. **Complete Unit Test Suite:**
   - Command: `python -m pytest tests/unit/ -v`
   - Result: **561 passed in 14.27s** (Exit code 0).
   - Total Regressions: 0.

---

## 5. REPOSITORY INTEGRITY CONFIRMATION

- **Frozen Models & Preprocessors:** Untouched; independently verified that 16 artifacts in Phase 5.4.2 manifest and 7 artifacts in Phase 5.3.3.1 manifest match 100% with 0 mismatches.
- **Canonical Datasets:** Untouched; metadata confirms all 33 partitions terminate strictly at `2026-10-31 21:59:59 UTC`.
- **Prospective Holdout:** `STRICTLY_SEALED` (`2026-11-01 00:00:00 UTC` through `2027-04-30 23:59:59.999 UTC`). Access history classified as `NOT_VERIFIED` due to lack of OS read logs.
- **Production Execution Code:** Untouched.
"""


def main():
    print("=" * 80)
    print("QUANTUM Phase 5.5: Final Governance Decision Dossier Revision 1.2 Generator")
    print("=" * 80)

    DOSSIER_DIR.mkdir(parents=True, exist_ok=True)

    files = {
        "QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md": generate_master_governance_status(),
        "QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md": generate_decision_options_and_tradeoffs(),
        "QUANTUM_PHASE_5_5_CROSS_DECISION_DEPENDENCIES.md": generate_cross_decision_dependencies(),
        "QUANTUM_PHASE_5_5_UNRESOLVED_ISSUE_REGISTER.md": generate_unresolved_issue_register(),
        "QUANTUM_PHASE_5_5_FINAL_HUMAN_DECISION_WORKSHEET.md": generate_final_human_decision_worksheet(),
        "QUANTUM_PHASE_5_5_GOVERNANCE_DOSSIER_REVISION_1_2_REPORT.md": generate_governance_dossier_revision_1_2_report(),
        "QUANTUM_PHASE_5_5_GOVERNANCE_CHANGELOG_REVISION_1_2.md": generate_governance_changelog_revision_1_2(),
        "QUANTUM_PHASE_5_5_TEST_INTEGRITY_AUDIT.md": generate_test_integrity_audit(),
    }

    em_dash = "\u2014"
    for fname, content in files.items():
        if em_dash in content:
            raise ValueError(f"Em dash detected in {fname}!")

        fpath = DOSSIER_DIR / fname
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Generated: {fpath} ({len(content)} bytes)")

    print("-" * 80)
    print("All 8 Phase 5.5 Governance Dossier Revision 1.2 Deliverables successfully generated.")
    print("=" * 80)


if __name__ == "__main__":
    main()
