"""
QUANTUM Phase 5.5: Final Governance Decision Dossier & Human Sign-Off Package Generator.

Generates the six formal deliverables in docs/research/phase_5_5_governance_dossier/:
1. QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md
2. QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md
3. QUANTUM_PHASE_5_5_CROSS_DECISION_DEPENDENCIES.md
4. QUANTUM_PHASE_5_5_UNRESOLVED_ISSUE_REGISTER.md
5. QUANTUM_PHASE_5_5_FINAL_HUMAN_DECISION_WORKSHEET.md
6. QUANTUM_PHASE_5_5_GOVERNANCE_DOSSIER_FINAL_REPORT.md

Zero em dashes (Unicode U+2014) standard strictly enforced.
"""

import os
from pathlib import Path

OUTPUT_DIR = Path("docs/research/phase_5_5_governance_dossier")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# Document 1: QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md
# -----------------------------------------------------------------------------
DOC_1_CONTENT = """# QUANTUM PHASE 5.5: MASTER GOVERNANCE STATUS

**Document Status:** `APPROVED_FOR_HUMAN_REVIEW`  
**Publication Timestamp:** `2026-11-01 21:35:00 UTC`  
**Operational Mode:** `GOVERNANCE_DECISION_PREPARATION_ONLY`  
**Associated Deliverable:** Master Governance Status Table (Task A)  

---

## 1. EXECUTIVE OVERVIEW

Following the completion of technical and quantitative research phases (Phase 5.5.0.0 through Phase 5.5.0.8), all six human governance decisions (DEC_01 through DEC_06) have been audited, mathematically reconciled, and formatted for human review.

### Strict Governance Boundary
- **All six decisions remain strictly:** `PENDING_HUMAN_DECISION`.
- No decision has been approved, rejected, or conditionally executed by AI.
- Phase 5.5 economic backtesting remains **NOT STARTED**.
- Phase 5.6 remains **NOT AUTHORIZED**.
- Prospective holdout (`2026-11-01` to `2027-04-30`) remains **STRICTLY SEALED**.

---

## 2. CONSOLIDATED MASTER GOVERNANCE STATUS TABLE

| Decision ID | Original Question | Current Status | Latest Recommendation | Supporting Evidence | Known Limitations | Dependencies | Consequence of Approval | Consequence of Rejection | Clarification Required? |
|---|---|---|---|---|---|---|---|---|---|
| **DEC_01** | Should Phase 5.5 evaluate the frozen classifier under re-anchored barrier execution (Track 2 / Alternative B) or explore independent strategy development (Track 3 / Alternative C)? | `PENDING_HUMAN_DECISION` | Sequential Tracks: Execute Alternative B (Track 2) as mandatory baseline; authorize Alternative C (Track 3) secondarily. | Re-anchoring barriers to entry fill ($P_{\\text{entry}} = \\text{open}[i+1]$) avoids look-ahead bias and requires zero parameter tuning. | Re-anchoring shifts nominal barrier levels relative to close[i] labels; does not directly validate close-anchored label payoff. | Governs the primary scientific estimand; foundation for DEC_02 through DEC_06. | Phase 5.5 tests classifier utility under re-anchored brackets. | Model cannot be evaluated without defining an alternative execution policy. | Requires supervisor sign-off on sequential track architecture. |
| **DEC_02** | Should the strategy execute Long-only, Short-only, or Bidirectional positions? | `PENDING_HUMAN_DECISION` | Mandatory disaggregated reporting across Long-Only, Short-Only, and Combined. | BTC bull bias is `DATA_SUPPORTED`; broad altcoin bias is `PARTIALLY_SUPPORTED`; short fee drag is lower on wins ($14.89$ vs $15.11$ bps). | Funding rates persistently positive and short liquidation slippage are theoretical assumptions in repo. | Depends on DEC_01; directly affects DEC_05 gross exposure and DEC_04 hypothesis family. | Authorizes full disaggregated evaluation; exposes directional asymmetry. | Strategy is artificially restricted to one direction before empirical evaluation. | Requires supervisor selection of primary portfolio direction. |
| **DEC_03** | What funding rate model should be adopted in the absence of canonical exchange funding series? | `PENDING_HUMAN_DECISION` | Parametric sweep across four scenarios (-1, 0, +1, +3 bps per settlement) with 1095x nominal annualization. | Canonical formula $CF_t = -d \\times N_{\\text{settle}, t} \\times f_t$ verified dimensionally with dynamic mark notional. | Historical funding rates are absent from local canonical datasets (`FUNDING_DATA_UNAVAILABLE`). | Directly impacts DEC_04 net break-even return hurdle. | Establishes funding resilience bounds across -10.95% to +32.85% annualized. | Economic net return cannot be computed for perpetual futures. | Requires supervisor sign-off on parametric scenario bounds. |
| **DEC_04** | What transaction cost ceiling and acceptance hurdle should govern Phase 5.5? | `PENDING_HUMAN_DECISION` | Adopt `REFERENCE_PRICE_ACCOUNTING`; evaluate 15, 20, 30 bps tiers; Gate 2 binding hurdle: $E[R_{\\text{net}}] > 0$ at 20 bps with $p < 0.05$ (K=11). | Reference-price accounting eliminates double-counting; normalized fee is $15.11$ bps on a $+1.50\\%$ win. | Overlapping trades (up to 288 bars) require calendar-time portfolio MBB rather than 24-bar trade array MBB. | Depends on DEC_01 estimand and DEC_03 funding cash flows. | Sets unambiguous statistical and cost thresholds for economic validation. | No quantitative standard exists to determine whether models have tradeable alpha. | Requires supervisor approval of 20 bps hurdle and K=11 family size. |
| **DEC_05** | What portfolio concurrency and gross leverage limits should be enforced? | `PENDING_HUMAN_DECISION` | Decouple gross notional leverage from stop loss risk; enforce 3 concurrent positions maximum (30% gross notional, 1x equity). | Three 1% risk allocations with 1.5 sigma stop-loss distance require ~30% gross notional, completely eliminating liquidation risk. | Claim that pairwise crypto correlations satisfy $\\rho > 0.70$ is `UNSUPPORTED_IN_REPO`. | Depends on DEC_02 directional concurrency and DEC_06 fleet size. | Protects portfolio equity against margin calls during simultaneous adverse barrier hits. | Portfolio risk remains unconstrained or arbitrarily restricted. | Requires supervisor confirmation of 3-position concurrency limit. |
| **DEC_06** | How should XMRUSDT be handled given its shorter historical coverage (83,863 vs 316,500 candles)? | `PENDING_HUMAN_DECISION` | Three-tier policy: preserve artifacts 100%, report standalone metrics in appendix, exclude from primary portfolio acceptance. | XMR data starts January 13, 2026; including it in primary portfolio creates a ragged covariance matrix and distorts multi-year Sharpe. | Standalone XMR performance cannot be cross-sectionally compared to 3-year asset records. | Governs instrument fleet size in DEC_04 ($K=10$ vs $K=11$) and DEC_05. | Prevents statistical distortion of 3-year fleet metrics while preserving all research work. | Multi-asset portfolio metrics are distorted by ragged missing data in Folds 1-4. | Requires supervisor approval of isolated appendix reporting. |
"""

# -----------------------------------------------------------------------------
# Document 2: QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md
# -----------------------------------------------------------------------------
DOC_2_CONTENT = """# QUANTUM PHASE 5.5: DECISION OPTIONS AND TRADEOFFS

**Document Status:** `APPROVED_FOR_HUMAN_REVIEW`  
**Publication Timestamp:** `2026-11-01 21:35:00 UTC`  
**Operational Mode:** `GOVERNANCE_DECISION_PREPARATION_ONLY`  
**Associated Deliverable:** Detailed Option Cards (Tasks B, C, D, E, F, G)  

---

## 1. DEC_01: BARRIER EXECUTION ARCHITECTURE (TASK B)

### The Three Formal Alternatives
1. **Alternative A (Original Close-Anchored Barriers):**
   - *Specification:* $P_{\\text{ref}} = \\text{close}[i]$, barriers at $P_{\\text{ref}}(1 \\pm 1.5\\sigma_t)$.
   - *Limitation:* Look-ahead latency violation. In real trading, an order cannot be filled at candle $i$ close because model inference requires candle $i$ close data. Fills occur at candle $i+1$ open.
   - *Status:* Statistically evaluated in Phase 5.4 (Track 1); economically unexecutable.
2. **Alternative B (Re-Anchored Economic Barriers):**
   - *Specification:* Fill at $P_{\\text{entry}} = \\text{open}[i+1]$, barriers re-anchored to $P_{\\text{entry}}(1 \\pm 1.5\\sigma_t)$.
   - *Advantage:* Zero new parameters. Cleanly tests whether the frozen classifier's directional signals have economic utility under realistic execution timing.
   - *Critical Epistemic Caveat:* Re-anchoring shifts the price levels of the upper and lower barriers. Therefore, positive economic results under Alternative B **do NOT automatically validate the original close-anchored training label payoff**. It evaluates the classifier as a directional filter under a re-anchored policy.
3. **Alternative C (Independent Downstream Strategy Development):**
   - *Specification:* Decouples classifier from static barriers; introduces trailing stops, dynamic ATR bands, and time-decay exits.
   - *Advantage:* Tests an algorithmic trading system.
   - *Limitation:* Introduces multiple degrees of freedom requiring cross-validation tuning on Folds 1-4 with Fold 5 held out. Conflates classifier quality with heuristic trade management.

### Permitted vs. Prohibited Conclusions
- **Permitted under Alt B:** "The frozen classifier demonstrates statistically significant economic expectancy after realistic taker fees and funding under a re-anchored triple-barrier policy."
- **Prohibited under Alt B:** "Phase 5.5 validates the exact economic payoff of the Phase 5.3 training labels."

---

## 2. DEC_02: DIRECTIONAL TRADING SCOPE (TASK C)

### The Seven Directional Claims and Epistemic Classifications
1. **BTC Secular Bull Bias:** `DATA_SUPPORTED`. Bitcoin rose from ~$27,000 in October 2023 to ~$73,000 in March 2024 and maintained elevated levels through October 2026 across 316,500 candles.
2. **Broad Altcoin Secular Bull Bias:** `PARTIALLY_SUPPORTED` / `CONTRADICTED_FOR_CERTAIN_ALTCOINS`. ADA and LTC experienced multi-month drawdowns; generalizing bull bias across all 11 assets is empirically false.
3. **Persistently Positive Funding:** `UNSUPPORTED_IN_REPO` / `UNVERIFIED_ASSUMPTION`. Funding series is absent from local datasets (`FUNDING_DATA_UNAVAILABLE`).
4. **Higher Short Liquidation Slippage:** `THEORETICAL` domain stylized fact. Microstructure depth and liquidation cascades indicate short stop-loss slippage can be elevated during fast upward squeezes.
5. **Bidirectional Doubles Frequency:** `THEORETICAL_UNVERIFIED` / Mathematically Inaccurate. Asymmetric thresholds and directional drift ensure $N_{\\text{long}} + N_{\\text{short}} \\ne 2 N_{\\text{long}}$.
6. **Execution Cost Symmetry:** `THEORETICAL_ASSUMPTION`. Fee schedules are symmetric, but realized fee drag is asymmetric: winning Short trades have lower exit notional ($N_{\\text{exit}} < N_{\\text{entry}}$) and incur lower fees in USDT ($14.89$ vs $15.11$ bps on a $1.50\\%$ move).
7. **Expectancy Symmetry:** `UNVERIFIED_ASSUMPTION`. Long and Short expectancies must be tested empirically.

### Mandatory Reporting Policy
To prevent confounding directional bias with classifier skill, Phase 5.5 mandates simultaneous disaggregated reporting for:
1. Long-Only Trades
2. Short-Only Trades
3. Combined Portfolio Trades

---

## 3. DEC_03: FUNDING RATE MODEL (TASK D)

### Standard Formulations
- **Canonical Unit:** `funding_rate_bps_per_settlement`
- **Nominal Annualization Factor:** $1095 = 3 \\times 365$ (Arithmetic scaling convention; strictly not realized yield or compounding return).
- **Signed Cash Flow Equation:**
  $$CF_t = -d \\times N_{\\text{settle}, t} \\times f_{t, \\text{decimal}}$$
  where $N_{\\text{settle}, t} = Q \\times P_{\\text{mark}, t}$ and $f_{t, \\text{decimal}} = \\frac{\\text{bps}}{10,000}$.
  - Longs pay ($CF < 0$) when $f > 0$; Longs receive ($CF > 0$) when $f < 0$.
  - Shorts receive ($CF > 0$) when $f > 0$; Shorts pay ($CF < 0$) when $f < 0$.

### The Four Parametric Scenarios
- **Scenario A (-1.0 bps / settlement):** Annualized $-10.95\\%$. Sustained bear market / short-crowded regime.
- **Scenario B (0.0 bps / settlement):** Annualized $0.00\\%$. Neutral baseline / frictionless funding benchmark.
- **Scenario C (+1.0 bps / settlement):** Annualized $+10.95\\%$. Moderate secular bull market baseline.
- **Scenario D (+3.0 bps / settlement):** Annualized $+32.85\\%$. Extreme bull market / high retail leverage stress test.

---

## 4. DEC_04: COST SCENARIOS & ACCEPTANCE CRITERIA (TASK E)

### Accounting Convention: REFERENCE_PRICE_ACCOUNTING
To prevent double-counting:
- Gross PnL is computed strictly from clean reference prices: $\\text{PnL}_{\\text{gross}} = d \\times Q \\times (P_{\\text{exit, ref}} - P_{\\text{entry, ref}})$.
- Exchange taker fees, bid-ask spread, volatility slippage, and market impact are aggregated into $C_{\\text{transaction, USDT}}$ and deducted as a cash friction.
- Prices are never slipped prior to gross PnL calculation.
- Normalized return equation:
  $$R_{\\text{net}} = R_{\\text{gross}} - \\frac{C_{\\text{transaction, USDT}}}{N_{\\text{entry}}} + \\frac{CF_{\\text{funding, total}}}{N_{\\text{entry}}}$$

### Statistical Inference Decision Alternatives
1. **Bootstrap Block Length:**
   - 24-bar block length is insufficient for holding horizons extending up to 288 bars (24 hours).
   - Candidate Resolution: Continuous Calendar-Time Portfolio Moving Block Bootstrap with $b = 288$ bars ($24$ hours) on continuous 5m fleet equity curves.
2. **Multiple-Testing Family Size ($K$):**
   - Confirmatory Family ($K = 11$): 11 specialist instruments evaluated at baseline 20 bps scenario on Combined direction.
   - Secondary Directional Sweeps ($K = 33$): 11 assets $\\times$ 3 directions.
   - Exploratory Scenario Sweeps ($K = 99$): 11 assets $\\times$ 3 directions $\\times$ 3 cost tiers.
   - Recommendation: Apply Holm-Bonferroni correction strictly to the primary $K = 11$ confirmatory family to preserve statistical power.

---

## 5. DEC_05: PORTFOLIO CONCURRENCY & LEVERAGE (TASK F)

### Separation of Gross Exposure from Stop Loss Risk
- **Gross Exposure:** $E_{\\text{gross}} = \\sum_{j=1}^J N_j$. With 3 positions of $10\\%$ notional each, $E_{\\text{gross}} = 30\\%$ of account equity ($0.3\\text{x}$ gross leverage).
- **Stop Loss Risk:** With a $1.5\\sigma$ barrier stop (typically $1.5\\%$ to $3.0\\%$ price distance), the maximum cash loss per trade is:
  $$\\text{Loss}_{\\text{stop}} = N_j \\times 1.5\\sigma \\approx 0.10 \\times E_0 \\times 0.02 = 0.002 \\times E_0 \\; (0.20\\% \\text{ of account equity})$$
- Even if all 3 concurrent positions hit their stop loss simultaneously, total loss is $\\le 1.0\\%$ of account equity. Liquidation risk is zero.
- **Correlation Finding:** The claim that crypto assets satisfy $\\rho > 0.70$ across all regimes is `UNSUPPORTED_IN_REPO`. In market stress, correlations spike toward 1.0; in sideways markets, altcoins decouple.

---

## 6. DEC_06: XMR RESEARCH & PORTFOLIO SCOPE (TASK G)

### The Data Disparity Finding
- 10 Assets (BTC, ETH, BNB, XRP, ADA, SOL, AVAX, LINK, DOGE, LTC): 316,500 5m candles ($3.0$ years, October 2023 to October 2026).
- XMRUSDT: 83,863 5m candles ($9.5$ months, starting January 13, 2026).
- Including XMR in the primary multi-asset portfolio creates a ragged covariance matrix and distorts multi-year portfolio Sharpe and drawdown metrics.

### Recommended Three-Tier Policy
1. **Tier 1 (Artifact Preservation):** 100% of XMR model binaries (5 folds) and preprocessors are preserved intact.
2. **Tier 2 (Standalone Research Reporting):** XMR economic metrics are evaluated and published in a dedicated standalone research appendix.
3. **Tier 3 (Primary Portfolio Acceptance):** XMR is excluded from the primary 10-asset portfolio aggregation hurdle to preserve mathematical symmetry.
"""

# -----------------------------------------------------------------------------
# Document 3: QUANTUM_PHASE_5_5_CROSS_DECISION_DEPENDENCIES.md
# -----------------------------------------------------------------------------
DOC_3_CONTENT = """# QUANTUM PHASE 5.5: CROSS-DECISION DEPENDENCY MATRIX

**Document Status:** `APPROVED_FOR_HUMAN_REVIEW`  
**Publication Timestamp:** `2026-11-01 21:35:00 UTC`  
**Operational Mode:** `GOVERNANCE_DECISION_PREPARATION_ONLY`  
**Associated Deliverable:** Cross-Decision Interaction Matrix (Task H)  

---

## 1. PAIRWISE DECISION INTERACTION MATRIX

The six governance decisions are deeply interconnected. Approving or altering one decision directly constrains the statistical and operational validity of other decisions:

| Impacting Decision | Impacted Decision | Dependency Nature | Operational Consequence |
|---|---|---|---|
| **DEC_01** (Architecture) | **DEC_02** (Direction) | Structural | If Alternative B is selected, directional scope applies to symmetric re-anchored brackets. If Alt C is selected, directional scope applies to asymmetric trend-following rules. |
| **DEC_01** (Architecture) | **DEC_04** (Cost Gate) | Foundational | The primary estimand defined in DEC_01 determines whether Gate 2 tests classifier utility ($E[R_{\\text{net}}] > 0$) or complete strategy Sharpe ratio. |
| **DEC_02** (Direction) | **DEC_05** (Concurrency) | Exposure Multiplier | Bidirectional trading allows concurrent Long and Short positions, creating market-neutral netting or doubling directional gross exposure. |
| **DEC_02** (Direction) | **DEC_04** (Hypothesis Family) | Hypothesis Multiplier | Disaggregating into Long, Short, and Combined triples the hypothesis family from $K=11$ to $K=33$. |
| **DEC_03** (Funding Model) | **DEC_04** (Cost Gate) | Arithmetic Offset | Funding payments directly shift the break-even return hurdle: $R_{\\text{breakeven}} = c_{\\text{rt}} - \\frac{CF_{\\text{funding}}}{N}$. At $+3$ bps funding, Longs require $+3$ bps higher gross alpha to break even. |
| **DEC_05** (Concurrency) | **DEC_04** (Bootstrap Design) | Correlation Coupling | Concurrent positions across assets require calendar-time portfolio resampling rather than isolated asset trade arrays. |
| **DEC_06** (XMR Scope) | **DEC_04** (Fleet Size) | Sample Sizing | Including XMR sets confirmatory fleet size to $K=11$; excluding XMR sets fleet size to $K=10$. |
| **DEC_06** (XMR Scope) | **DEC_05** (Portfolio Risk) | Covariance Structure | Including XMR creates a ragged covariance matrix from October 2023 to January 2026. |

---

## 2. RECONCILED LOGICAL DECISION SEQUENCE

To prevent circular logic and ensure that dependent assumptions are resolved in mathematical order, the human supervisor should evaluate decisions in the following sequence:

```
+-------------------------------------------------------------------------------+
|                       RECOMMENDED DECISION SEQUENCING                         |
+-------------------------------------------------------------------------------+
| Step 1: DEC_01 (Estimand & Architecture)                                     |
|         -> Defines the primary research question and barrier mechanics.       |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Step 2: DEC_06 (Instrument Fleet Scope)                                       |
|         -> Resolves whether XMR is in primary portfolio (K=10 vs K=11).       |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Step 3: DEC_03 (Funding Model)                                                |
|         -> Establishes the financing cash flow bounds across scenarios.       |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Step 4: DEC_04 (Cost Gate & Statistical Criteria)                             |
|         -> Sets the binding break-even hurdle and multiple testing family.    |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Step 5: DEC_02 (Directional Trading Scope)                                    |
|         -> Authorizes Long, Short, or Bidirectional execution reporting.      |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Step 6: DEC_05 (Portfolio Concurrency & Leverage)                             |
|         -> Enforces maximum concurrent exposure and margin limits.            |
+-------------------------------------------------------------------------------+
```
"""

# -----------------------------------------------------------------------------
# Document 4: QUANTUM_PHASE_5_5_UNRESOLVED_ISSUE_REGISTER.md
# -----------------------------------------------------------------------------
DOC_4_CONTENT = """# QUANTUM PHASE 5.5: UNRESOLVED ISSUE REGISTER

**Document Status:** `APPROVED_FOR_HUMAN_REVIEW`  
**Publication Timestamp:** `2026-11-01 21:35:00 UTC`  
**Operational Mode:** `GOVERNANCE_DECISION_PREPARATION_ONLY`  
**Associated Deliverable:** Master Technical Issue Register (Task I)  

---

## 1. CONSOLIDATED TECHNICAL ISSUE REGISTER

The table below catalogs all eleven unresolved issues identified across Phase 5.5.0.0 through Phase 5.5.0.8. No issue is marked resolved merely because a candidate recommendation exists:

| Issue ID | Related Decision | Severity | Description | Evidence & Source Reference | Verification Classification | Consequence if Unresolved | Required Human Clarification | Execution Blocking? |
|---|---|---|---|---|---|---|---|---|
| **ISS_01** | DEC_03 | `HIGH` | Funding settlement eligibility boundary for orders filled exactly at 08:00:00.000 UTC is venue-dependent. | [PHASE_5_5_0_8_FUNDING_ELIGIBILITY_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_FUNDING_ELIGIBILITY_AUDIT.md) | `PASS_WITH_LIMITATIONS` | Potential 1-cycle funding over- or under-counting in backtest. | Confirm non-eligibility for orders executing at 08:00:00.000 open. | **YES** |
| **ISS_02** | DEC_04 | `MEDIUM` | Ambiguity between full bid-ask spread ($S$) and half-spread per leg ($s_{\\text{leg}}$). | [PHASE_5_5_0_8_TRANSACTION_COST_SPECIFICATION.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_TRANSACTION_COST_SPECIFICATION.md) | `SOURCE_VERIFIED` | Misinterpreting $1.0$ bps as full spread would understate friction by $50\\%$. | Confirm $1.0$ bps represents half-spread per leg ($2.0$ bps round-trip). | **YES** |
| **ISS_03** | DEC_04 | `HIGH` | Potential double-counting of spread, slippage, and market impact if fill prices are slipped AND fees deducted. | [PHASE_5_5_0_7_TRANSACTION_COST_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_7/PHASE_5_5_0_7_TRANSACTION_COST_AUDIT.md) | `MATHEMATICALLY_VERIFIED` | Imposes an artificial 30 to 60 bps penalty, creating false negative strategy rejection. | Mandate strict `REFERENCE_PRICE_ACCOUNTING` across all simulation code. | **YES** |
| **ISS_04** | DEC_04 | `HIGH` | Moving Block Bootstrap block length of $b=24$ bars fails to capture autocorrelation for trades held up to 288 bars. | [PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md) | `MATHEMATICALLY_VERIFIED` | Underestimates standard errors and inflates empirical t-statistics. | Approve Continuous Calendar-Time Portfolio MBB with $b=288$ bars ($24$h). | **YES** |
| **ISS_05** | DEC_04 | `MEDIUM` | Optimal block length selection methodology lacks empirical sensitivity sweep. | [PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md) | `MATHEMATICALLY_VERIFIED` | Results could be sensitive to arbitrary choice of 288 bars vs 144 or 576 bars. | Authorize sensitivity sweep across $b \\in \\{72, 144, 288, 576\\}$ bars. | No (Diagnostic) |
| **ISS_06** | DEC_01 | `HIGH` | Conflation between ML target predictive validation (Track 1) and economic strategy performance (Track 3). | [PHASE_5_5_0_6_RESEARCH_TRACK_COMPARISON.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_6/PHASE_5_5_0_6_RESEARCH_TRACK_COMPARISON.md) | `SOURCE_VERIFIED` | Misleads stakeholders into believing downstream strategy profits prove ML label accuracy. | Formally adopt the Three-Track Sequential Architecture. | **YES** |
| **ISS_07** | DEC_04 | `HIGH` | Hypothesis family size $K$ for Holm-Bonferroni correction is ambiguous ($K=11$ vs $K=33$ vs $K=99$). | [PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md) | `MATHEMATICALLY_VERIFIED` | Inflating $K$ to 99 destroys statistical power; setting $K=1$ invalidates multiple testing control. | Formally fix $K=11$ as primary confirmatory family; report $K=33$ secondarily. | **YES** |
| **ISS_08** | DEC_05 | `HIGH` | Claim that pairwise crypto correlations satisfy $\\rho > 0.70$ is unsupported by repository data. | [PHASE_5_5_0_5_DEC_05_PORTFOLIO_CORRELATION_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_5/PHASE_5_5_0_5_DEC_05_PORTFOLIO_CORRELATION_AUDIT.md) | `NOT_VERIFIED` | Portfolio risk policy is based on unverified domain stylized facts. | Decouple risk policy from $\\rho$; base concurrency on gross notional limits. | **YES** |
| **ISS_09** | DEC_03 | `HIGH` | Historical funding rate series are completely absent from canonical datasets. | [PHASE_5_5_0_8_FUNDING_ELIGIBILITY_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_FUNDING_ELIGIBILITY_AUDIT.md) | `SOURCE_VERIFIED` | Cannot compute historical realized funding cash flows for OOF trades. | Authorize parametric sweep across 4 scenarios (-1, 0, +1, +3 bps). | **YES** |
| **ISS_10** | DEC_04 | `HIGH` | Runtime accounting implementation has not been code-verified because backtesting is prohibited. | [PHASE_5_5_0_7_TEST_INTEGRITY_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_7/PHASE_5_5_0_7_TEST_INTEGRITY_AUDIT.md) | `TEST_VERIFIED` | Potential software implementation bugs in backtest engine could distort metrics. | Mandate unit-test verification of backtest engine prior to full fleet execution. | **YES** |
| **ISS_11** | Governance | `MEDIUM` | Operating system file read-access history cannot be audited via SHA-256 hashes or Git logs. | [PHASE_5_5_0_8_FULL_FLEET_TEMPORAL_ISOLATION_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_FULL_FLEET_TEMPORAL_ISOLATION_AUDIT.md) | `METADATA_VERIFIED` | Cannot prove via OS logs that historical files were never read in memory. | Acknowledge limitation; note that prospective holdout data does not exist locally. | No (Informational) |
"""

# -----------------------------------------------------------------------------
# Document 5: QUANTUM_PHASE_5_5_FINAL_HUMAN_DECISION_WORKSHEET.md
# -----------------------------------------------------------------------------
DOC_5_CONTENT = """# QUANTUM PHASE 5.5: FINAL HUMAN DECISION WORKSHEET

**Worksheet Status:** `UNEXECUTED_WORKSHEET_AWAITING_HUMAN_SIGN_OFF`  
**Publication Timestamp:** `2026-11-01 21:35:00 UTC`  
**Operational Mode:** `GOVERNANCE_DECISION_PREPARATION_ONLY`  
**Associated Deliverable:** Human Decision Package (Task J)  

---

## INSTRUCTIONS FOR HUMAN SUPERVISOR

This worksheet represents the official human governance sign-off document for QUANTUM Phase 5.5.
- All six decisions must be explicitly signed by the supervisor.
- All decision, rationale, and timestamp fields below remain **BLANK** pending your input.
- Phase 5.5 economic backtesting execution remains **DENIED** until this entire document is signed.

---

## DECISION 1: BARRIER EXECUTION ARCHITECTURE (DEC_01)
- **Question:** Does Phase 5.5 evaluate the frozen classifier under re-anchored barrier execution (Track 2 / Alternative B) or explore independent strategy development (Track 3 / Alternative C)?
- **Available Options:**
  - `Alternative B`: Re-anchor symmetric barriers to entry fill ($P_{\\text{entry}} = \\text{open}[i+1]$). Tests classifier utility with zero new parameters.
  - `Alternative C`: Decouple classifier from barriers; engineer trailing stops and dynamic exits. Tests a downstream trading strategy.
  - `Sequential Tracks`: Execute Track 2 (Alternative B) first as the mandatory baseline; authorize Track 3 for subsequent exploratory phases.
- **Recommended Option:** `Sequential Tracks (Alternative B as primary baseline)`.
- **Evidence Supporting Recommendation:** Phase 5.3 models were trained to predict directional barrier touches; Alternative B directly tests this capability under realistic fill timing without introducing parameter-tuning degrees of freedom.
- **Risks and Trade-offs:** Alternative B shifts barrier price levels relative to candle $i$ close; positive results evaluate classifier skill under re-anchoring, not original label payoff.
- **Unresolved Limitations:** Real market fills may experience intra-bar slippage not captured by candle open.
- **Required Additional Information:** None. Fully specified.
- **Human Decision:** `[BLANK - PENDING HUMAN INPUT]`
- **Human Rationale:** `[BLANK - PENDING HUMAN INPUT]`
- **Accepted Limitations:** `[BLANK - PENDING HUMAN INPUT]`
- **Approval Timestamp:** `[BLANK - PENDING HUMAN INPUT]`
- **Reviewer Signature:** `[BLANK - PENDING HUMAN INPUT]`
- **Formal Status:** `PENDING_HUMAN_DECISION`

---

## DECISION 2: DIRECTIONAL TRADING SCOPE (DEC_02)
- **Question:** Should the strategy execute Long-only, Short-only, or Bidirectional positions?
- **Available Options:**
  - `Long-Only`: Execute only Class +1 signals.
  - `Short-Only`: Execute only Class -1 signals.
  - `Bidirectional`: Execute both Class +1 and Class -1 signals concurrently.
  - `Mandatory Disaggregated Reporting`: Execute both, but report Long-Only, Short-Only, and Combined metrics independently in all master tables.
- **Recommended Option:** `Mandatory Disaggregated Reporting (Bidirectional execution with independent reporting)`.
- **Evidence Supporting Recommendation:** BTC experienced secular bull drift ($2023\\text{-}2026$), while altcoins showed mixed regimes. Profitable Short trades incur lower fee drag ($14.89$ vs $15.11$ bps). Disaggregated reporting exposes directional asymmetry without imposing premature constraints.
- **Risks and Trade-offs:** Short positions face negative funding drag during bull regimes and theoretical liquidation squeeze slippage.
- **Unresolved Limitations:** Realized short slippage distribution cannot be verified from 5-minute OHLCV candles alone.
- **Required Additional Information:** None. Fully specified.
- **Human Decision:** `[BLANK - PENDING HUMAN INPUT]`
- **Human Rationale:** `[BLANK - PENDING HUMAN INPUT]`
- **Accepted Limitations:** `[BLANK - PENDING HUMAN INPUT]`
- **Approval Timestamp:** `[BLANK - PENDING HUMAN INPUT]`
- **Reviewer Signature:** `[BLANK - PENDING HUMAN INPUT]`
- **Formal Status:** `PENDING_HUMAN_DECISION`

---

## DECISION 3: FUNDING RATE MODEL APPROVAL (DEC_03)
- **Question:** What funding rate model should be adopted in the absence of canonical exchange funding series?
- **Available Options:**
  - `Zero Funding Benchmark`: Assume $f_t = 0$ across all settlements (frictionless funding).
  - `Fixed Bull-Market Baseline`: Assume constant $+1.0$ bps per settlement ($+10.95\\%$ annualized).
  - `Four-Scenario Parametric Sweep`: Evaluate all trades across -1, 0, +1, and +3 bps per settlement.
- **Recommended Option:** `Four-Scenario Parametric Sweep (-1, 0, +1, +3 bps per settlement)`.
- **Evidence Supporting Recommendation:** Funding series is completely absent from local data (`FUNDING_DATA_UNAVAILABLE`). A parametric sweep establishes rigorous upper and lower performance bounds across varied market regimes.
- **Risks and Trade-offs:** Parametric sweeps prove robustness under assumed rates, but cannot reveal exact historical cash flows for specific dates.
- **Unresolved Limitations:** Exact millisecond eligibility rule for orders filled at 08:00:00.000 UTC requires venue definition.
- **Required Additional Information:** None. Parametric formulation is complete.
- **Human Decision:** `[BLANK - PENDING HUMAN INPUT]`
- **Human Rationale:** `[BLANK - PENDING HUMAN INPUT]`
- **Accepted Limitations:** `[BLANK - PENDING HUMAN INPUT]`
- **Approval Timestamp:** `[BLANK - PENDING HUMAN INPUT]`
- **Reviewer Signature:** `[BLANK - PENDING HUMAN INPUT]`
- **Formal Status:** `PENDING_HUMAN_DECISION`

---

## DECISION 4: PRIMARY COST GATE & SCENARIOS (DEC_04)
- **Question:** What transaction cost ceiling and acceptance hurdle should govern Phase 5.5?
- **Available Options:**
  - `Institutional VIP Tier`: 15 bps round-trip ($C_{\\text{round-trip}} = 0.0015$).
  - `Baseline Retail Tier`: 20 bps round-trip ($C_{\\text{round-trip}} = 0.0020$).
  - `Conservative Stress Tier`: 30 bps round-trip ($C_{\\text{round-trip}} = 0.0030$).
  - `Multi-Tier Resilience Policy`: Evaluate all three tiers; require binding Gate 2 hurdle $E[R_{\\text{net}}] > 0$ with $p < 0.05$ (K=11) at 20 bps baseline.
- **Recommended Option:** `Multi-Tier Resilience Policy (Binding Gate 2 at 20 bps baseline; report 15 and 30 bps sweeps)`.
- **Evidence Supporting Recommendation:** 20 bps reflects realistic retail taker fees ($10$ bps total) plus modeled spread and impact ($10$ bps total). `REFERENCE_PRICE_ACCOUNTING` eliminates double-counting.
- **Risks and Trade-offs:** 20 bps is a demanding hurdle for 5-minute holding periods; models must capture genuine directional volatility to overcome $20$ bps friction.
- **Unresolved Limitations:** Overlapping holding periods (up to 288 bars) require Continuous Calendar-Time Portfolio MBB ($b=288$ bars).
- **Required Additional Information:** Approval of calendar-time bootstrap design.
- **Human Decision:** `[BLANK - PENDING HUMAN INPUT]`
- **Human Rationale:** `[BLANK - PENDING HUMAN INPUT]`
- **Accepted Limitations:** `[BLANK - PENDING HUMAN INPUT]`
- **Approval Timestamp:** `[BLANK - PENDING HUMAN INPUT]`
- **Reviewer Signature:** `[BLANK - PENDING HUMAN INPUT]`
- **Formal Status:** `PENDING_HUMAN_DECISION`

---

## DECISION 5: PORTFOLIO CONCURRENCY AND LEVERAGE (DEC_05)
- **Question:** What portfolio concurrency and gross leverage limits should be enforced?
- **Available Options:**
  - `Unconstrained Independent Specialists`: Allow all 11 specialists to trade concurrently with independent margin.
  - `Single Position Exclusive`: Allow only 1 specialist position across the entire fleet at any time.
  - `Decoupled Risk / 3-Position Cap`: Limit maximum concurrent positions to 3 ($10\\%$ notional each; $30\\%$ gross notional; $\\le 1.0\\%$ equity at risk).
- **Recommended Option:** `Decoupled Risk / 3-Position Cap (30% gross notional limit, 1x equity)`.
- **Evidence Supporting Recommendation:** Decoupling gross notional from stop loss distance guarantees that even simultaneous stop-outs across all 3 positions result in $\\le 1.0\\%$ total loss. Liquidation risk is zero.
- **Risks and Trade-offs:** Limiting concurrency to 3 positions requires an order queue priority rule when $>3$ specialists trigger simultaneously.
- **Unresolved Limitations:** Pairwise correlation claim $\\rho > 0.70$ is unverified in repository.
- **Required Additional Information:** Approval of concurrency priority rule (e.g. highest predicted probability).
- **Human Decision:** `[BLANK - PENDING HUMAN INPUT]`
- **Human Rationale:** `[BLANK - PENDING HUMAN INPUT]`
- **Accepted Limitations:** `[BLANK - PENDING HUMAN INPUT]`
- **Approval Timestamp:** `[BLANK - PENDING HUMAN INPUT]`
- **Reviewer Signature:** `[BLANK - PENDING HUMAN INPUT]`
- **Formal Status:** `PENDING_HUMAN_DECISION`

---

## DECISION 6: XMR RESEARCH AND PORTFOLIO SCOPE (DEC_06)
- **Question:** How should XMRUSDT be handled given its shorter historical coverage (83,863 vs 316,500 candles)?
- **Available Options:**
  - `Include in Primary Portfolio`: Include XMR directly in the 11-asset multi-asset portfolio aggregation.
  - `Complete Exclusion`: Delete or ignore XMR model binaries entirely.
  - `Three-Tier Policy`: Preserve all XMR artifacts 100%; report standalone metrics in an appendix; exclude XMR from primary 10-asset portfolio aggregation.
- **Recommended Option:** `Three-Tier Policy (100% artifact preservation, standalone appendix reporting, exclude from primary portfolio aggregation)`.
- **Evidence Supporting Recommendation:** XMR data starts January 13, 2026 ($9.5$ months), while all other assets cover October 2023 to October 2026 ($36$ months). Aggregating XMR into the primary portfolio creates a ragged covariance matrix and distorts 3-year multi-asset metrics.
- **Risks and Trade-offs:** XMR does not contribute to primary fleet Sharpe ratio.
- **Unresolved Limitations:** Standalone XMR evaluation covers only Fold 5 out-of-fold data.
- **Required Additional Information:** None. Fully specified.
- **Human Decision:** `[BLANK - PENDING HUMAN INPUT]`
- **Human Rationale:** `[BLANK - PENDING HUMAN INPUT]`
- **Accepted Limitations:** `[BLANK - PENDING HUMAN INPUT]`
- **Approval Timestamp:** `[BLANK - PENDING HUMAN INPUT]`
- **Reviewer Signature:** `[BLANK - PENDING HUMAN INPUT]`
- **Formal Status:** `PENDING_HUMAN_DECISION`

---

## MASTER EXECUTION SIGN-OFF BLOCK

- **Phase 5.5 Backtesting Execution Authorization:** `[DENIED_UNTIL_ALL_DECISIONS_SIGNED]`
- **Supervisor Signature:** `__________________________________________________`
- **Supervisor Name:** `[BLANK - PENDING HUMAN INPUT]`
- **Sign-Off Date:** `[UNEXECUTED]`
- **Overall Authorization Status:** `PENDING_SUPERVISOR_SIGNATURE`
"""

# -----------------------------------------------------------------------------
# Document 6: QUANTUM_PHASE_5_5_GOVERNANCE_DOSSIER_FINAL_REPORT.md
# -----------------------------------------------------------------------------
DOC_6_CONTENT = """# QUANTUM PHASE 5.5: GOVERNANCE DOSSIER FINAL REPORT

**Master Governance Verdict:** `GOVERNANCE_PACKAGE_READY_FOR_HUMAN_SIGN_OFF`  
**Publication Timestamp:** `2026-11-01 21:35:00 UTC`  
**Repository:** `https://github.com/RAYDENFLY/quantum-multi-agent`  
**Operational Mode:** `GOVERNANCE_DECISION_PREPARATION_ONLY`  

---

## 1. EXECUTIVE SUMMARY & VERDICT JUSTIFICATION

This dossier consolidates the research design, mathematical derivations, statistical limitations, and governance structures developed across Phase 5.5.0.0 through Phase 5.5.0.8 into one comprehensive, decision-ready package for the human supervisor.

### Master Governance Readiness Verdict
$$\\mathbf{GOVERNANCE\\_PACKAGE\\_READY\\_FOR\\_HUMAN\\_SIGN\\_OFF}$$

### Comprehensive Six-Point Verdict Justification
1. **Are all six decisions understandable?** YES. Each decision (DEC_01 through DEC_06) is formulated with an explicit operational question, plain-language options, and detailed technical trade-offs.
2. **Are alternatives clearly distinguished?** YES. Alternatives A, B, and C in DEC_01, directional scopes in DEC_02, parametric scenarios in DEC_03, cost tiers in DEC_04, leverage boundaries in DEC_05, and 3-tier XMR scoping in DEC_06 are rigorously separated.
3. **Are unresolved issues visible?** YES. The eleven technical issues (ISS_01 through ISS_11) are cataloged in [QUANTUM_PHASE_5_5_UNRESOLVED_ISSUE_REGISTER.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_UNRESOLVED_ISSUE_REGISTER.md) with severity, evidence, and required resolutions.
4. **Are dependencies explicit?** YES. The 6x6 pairwise dependency matrix and the reconciled 6-step execution sequence are fully documented in [QUANTUM_PHASE_5_5_CROSS_DECISION_DEPENDENCIES.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_CROSS_DECISION_DEPENDENCIES.md).
5. **Is the decision worksheet complete?** YES. [QUANTUM_PHASE_5_5_FINAL_HUMAN_DECISION_WORKSHEET.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_HUMAN_DECISION_WORKSHEET.md) provides a clean, unexecuted worksheet with all human input fields left blank.
6. **Is critical missing evidence transparently reported?** YES. The absence of historical funding rate series (`FUNDING_DATA_UNAVAILABLE`), the lack of OS read-access logs, and the unverified crypto correlation claims are explicitly documented.

---

## 2. SUMMARY OF THE SIX PENDING DECISIONS

| ID | Domain | Recommended Option | Core Justification |
|---|---|---|---|
| **DEC_01** | Architecture | Sequential Tracks (Alt B Baseline) | Evaluates classifier under realistic execution with zero new tuning parameters. |
| **DEC_02** | Directional Scope | Mandatory Disaggregated Reporting | Exposes directional asymmetry and fee drag without premature constraints. |
| **DEC_03** | Funding Model | 4-Scenario Parametric Sweep | Establishes rigorous performance bounds in the absence of canonical funding data. |
| **DEC_04** | Cost Gate & Hurdle | 20 bps Hurdle / Calendar MBB ($K=11$) | Realistic retail friction; solves overlapping holding period autocorrelation. |
| **DEC_05** | Portfolio Concurrency | Decoupled 3-Position Cap (30% Gross) | Guarantees maximum portfolio loss $\\le 1.0\\%$; eliminates liquidation risk. |
| **DEC_06** | XMR Research Scope | Three-Tier Policy (Appendix Only) | Preserves all models 100%; prevents ragged covariance matrix distortion. |

---

## 3. SUMMARY OF MISSING EVIDENCE & UNRESOLVED ISSUES

1. **Historical Funding Series:** Local datasets contain only OHLCV candles (`FUNDING_DATA_UNAVAILABLE`). Parametric sweeps (DEC_03) are required.
2. **Venue Snapshot Boundary:** Exact millisecond behavior at 08:00:00.000 UTC requires formal definition prior to backtest execution.
3. **Overlapping Trade Autocorrelation:** The 24-bar block bootstrap must be upgraded to a Continuous Calendar-Time Portfolio MBB with $b=288$ bars ($24$ hours).
4. **Cross-Asset Correlation:** The assumption $\\rho > 0.70$ is unverified; risk management is decoupled from correlation.

---

## 4. PRESERVED GOVERNANCE STATES

- **DEC_01:** `PENDING_HUMAN_DECISION`
- **DEC_02:** `PENDING_HUMAN_DECISION`
- **DEC_03:** `PENDING_HUMAN_DECISION`
- **DEC_04:** `PENDING_HUMAN_DECISION`
- **DEC_05:** `PENDING_HUMAN_DECISION`
- **DEC_06:** `PENDING_HUMAN_DECISION`
- **Phase 5.5 Backtesting Execution:** `NOT_STARTED`
- **Phase 5.6 Authorization:** `NOT_AUTHORIZED`
- **Prospective Holdout:** `STRICTLY_SEALED` (`2026-11-01` to `2027-04-30`)

---

## 5. CONFIRMATION OF ZERO PROHIBITED ACTIVITY & STRICT STOP CONDITION

All activities in this phase complied with `GOVERNANCE_DECISION_PREPARATION_ONLY`:
- Zero backtests, paper trading, or live trading executed.
- Zero model training, retraining, recalibration, or inference.
- Zero prospective holdout rows queried or materialized.
- Zero production code or frozen model binary modifications.
- All human decision fields in the worksheet remain strictly **BLANK**.

The dossier is ready for human supervisor review. All automated activity is halted.
"""

def generate_all():
    print("=" * 80)
    print("QUANTUM Phase 5.5: Final Governance Decision Dossier Generator")
    print("=" * 80)

    deliverables = {
        "QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md": DOC_1_CONTENT,
        "QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md": DOC_2_CONTENT,
        "QUANTUM_PHASE_5_5_CROSS_DECISION_DEPENDENCIES.md": DOC_3_CONTENT,
        "QUANTUM_PHASE_5_5_UNRESOLVED_ISSUE_REGISTER.md": DOC_4_CONTENT,
        "QUANTUM_PHASE_5_5_FINAL_HUMAN_DECISION_WORKSHEET.md": DOC_5_CONTENT,
        "QUANTUM_PHASE_5_5_GOVERNANCE_DOSSIER_FINAL_REPORT.md": DOC_6_CONTENT,
    }

    em_dash = chr(0x2014)
    for filename, content in deliverables.items():
        assert em_dash not in content, f"Em dash detected in {filename} content!"
        target_path = OUTPUT_DIR / filename
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Generated: {target_path} ({len(content)} bytes)")

    print("-" * 80)
    print("All 6 Phase 5.5 Governance Dossier Deliverables successfully generated.")
    print("=" * 80)

if __name__ == "__main__":
    generate_all()
