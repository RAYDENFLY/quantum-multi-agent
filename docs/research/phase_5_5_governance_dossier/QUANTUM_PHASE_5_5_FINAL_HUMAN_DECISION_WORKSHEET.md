# QUANTUM PHASE 5.5: FINAL HUMAN DECISION WORKSHEET (REVISION 1.2)

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
