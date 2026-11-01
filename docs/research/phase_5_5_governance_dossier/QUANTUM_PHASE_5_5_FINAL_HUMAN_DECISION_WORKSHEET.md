# QUANTUM PHASE 5.5: FINAL HUMAN DECISION WORKSHEET (REVISION 1)

**Worksheet Status:** `UNEXECUTED_WORKSHEET_AWAITING_HUMAN_SIGN_OFF`  
**Revision:** `Revision 1 (Decision Consistency & Risk-Claim Correction)`  
**Publication Timestamp:** `2026-11-01 22:55:00 UTC`  
**Operational Mode:** `READ_ONLY_EVIDENCE_RECONCILIATION_AND_GOVERNANCE_DOCUMENTATION`  
**Associated Deliverable:** Human Decision Package (Task H)  

---

## INSTRUCTIONS FOR HUMAN SUPERVISOR

This worksheet represents the official human governance sign-off document for QUANTUM Phase 5.5.
- All six decisions must be explicitly signed by the supervisor.
- All decision, rationale, timestamp, and reviewer identity fields below remain **BLANK** pending your input.
- Phase 5.5 economic backtesting execution remains **DENIED** until this entire document is signed.

---

## DECISION 1: BARRIER EXECUTION ARCHITECTURE (DEC_01)
- **Question:** Does Phase 5.5 evaluate the frozen classifier under re-anchored barrier execution (Track 2 / Alternative B) or explore independent strategy development (Track 3 / Alternative C)?
- **Available Options:**
  - `Alternative B`: Re-anchor symmetric barriers to entry fill ($P_{\text{entry}} = \text{open}[i+1]$). Tests classifier utility with zero new parameters.
  - `Alternative C`: Decouple classifier from barriers; engineer trailing stops and dynamic exits. Tests a downstream trading strategy.
  - `Sequential Tracks`: Execute Track 2 (Alternative B) first as the mandatory baseline; authorize Track 3 for subsequent exploratory phases.
- **Current Recommendation:** `Sequential Tracks (Alternative B as primary baseline)`.
- **Evidence Supporting Recommendation:** Phase 5.3 models were trained to predict directional barrier touches; Alternative B directly tests this capability under realistic fill timing without introducing parameter-tuning degrees of freedom.
- **Unresolved Limitations:** Alternative B shifts barrier price levels relative to candle $i$ close; positive results evaluate classifier skill under re-anchoring, not original label payoff.
- **Dependencies:** Establishes the primary estimand for DEC_02 through DEC_06.
- **Consequences of Approval:** Phase 5.5 evaluates classifier utility under re-anchored brackets.
- **Consequences of Rejection:** Research cannot proceed without defining an alternative execution policy.
- **Human Decision:** `[BLANK - PENDING HUMAN INPUT]`
- **Human Rationale:** `[BLANK - PENDING HUMAN INPUT]`
- **Reviewer Identity:** `[BLANK - PENDING HUMAN INPUT]`
- **Approval Timestamp:** `[BLANK - PENDING HUMAN INPUT]`
- **Formal Status:** `PENDING_HUMAN_DECISION`

---

## DECISION 2: DIRECTIONAL TRADING SCOPE (DEC_02)
- **Question:** Should the strategy execute Long-only, Short-only, or Bidirectional positions?
- **Available Options:**
  - `Long-Only Execution`: Execute only Class +1 signals.
  - `Short-Only Execution`: Execute only Class -1 signals.
  - `Bidirectional Execution with Separate Reporting`: Execute both Class +1 and Class -1 signals, with mandatory disaggregated reporting for Long-Only, Short-Only, and Combined metrics.
- **Current Recommendation:** `Bidirectional Execution with Separate Reporting`.
- **Evidence Supporting Recommendation:** BTC experienced secular bull drift ($2023\text{-}2026$), while altcoins showed mixed regimes. Profitable Short trades incur lower fee drag ($14.89$ vs $15.11$ bps). Disaggregated reporting exposes directional asymmetry without imposing premature constraints.
- **Unresolved Limitations:** Disaggregated reporting does not automatically guarantee execution viability; Short positions face negative funding drag during bull regimes and theoretical liquidation squeeze slippage.
- **Dependencies:** Depends on DEC_01; directly affects DEC_05 gross exposure and DEC_04 hypothesis family.
- **Consequences of Approval:** Authorizes bidirectional execution with mandatory separate reporting.
- **Consequences of Rejection:** Strategy is artificially restricted to one direction prior to empirical evaluation.
- **Human Decision:** `[BLANK - PENDING HUMAN INPUT]`
- **Human Rationale:** `[BLANK - PENDING HUMAN INPUT]`
- **Reviewer Identity:** `[BLANK - PENDING HUMAN INPUT]`
- **Approval Timestamp:** `[BLANK - PENDING HUMAN INPUT]`
- **Formal Status:** `PENDING_HUMAN_DECISION`

---

## DECISION 3: FUNDING RATE MODEL APPROVAL (DEC_03)
- **Question:** What funding rate model should be adopted in the absence of canonical exchange funding series?
- **Available Options:**
  - `Zero Funding Benchmark`: Assume $f_t = 0$ across all settlements (frictionless funding).
  - `Fixed Bull-Market Baseline`: Assume constant $+1.0$ bps per settlement ($+10.95\%$ nominal annualized).
  - `Four-Scenario Parametric Sweep`: Evaluate all trades across -1, 0, +1, and +3 bps per settlement.
- **Current Recommendation:** `Four-Scenario Parametric Sweep (-1, 0, +1, +3 bps per settlement)`.
- **Evidence Supporting Recommendation:** Funding series is completely absent from local data (`FUNDING_DATA_UNAVAILABLE`). A parametric sweep establishes performance sensitivity bounds across varied market regimes.
- **Unresolved Limitations:** Scenarios are assumed sensitivities, not historical distributions; exact millisecond eligibility rule for orders filled at 08:00:00.000 UTC remains `NOT_VERIFIED`.
- **Dependencies:** Directly shifts the break-even gross return hurdle in DEC_04.
- **Consequences of Approval:** Establishes funding sensitivity bounds across -10.95% to +32.85% nominal annualized.
- **Consequences of Rejection:** Economic net return cannot be computed for perpetual futures.
- **Human Decision:** `[BLANK - PENDING HUMAN INPUT]`
- **Human Rationale:** `[BLANK - PENDING HUMAN INPUT]`
- **Reviewer Identity:** `[BLANK - PENDING HUMAN INPUT]`
- **Approval Timestamp:** `[BLANK - PENDING HUMAN INPUT]`
- **Formal Status:** `PENDING_HUMAN_DECISION`

---

## DECISION 4: PRIMARY COST GATE & SCENARIOS (DEC_04)
- **Question:** What transaction cost ceiling and acceptance hurdle should govern Phase 5.5?
- **Available Options:**
  - `Institutional VIP Tier`: 15 bps round-trip ($C_{\text{round-trip}} = 0.0015$).
  - `Baseline Retail Tier`: 20 bps round-trip ($C_{\text{round-trip}} = 0.0020$).
  - `Conservative Stress Tier`: 30 bps round-trip ($C_{\text{round-trip}} = 0.0030$).
  - `Multi-Tier Resilience Policy`: Evaluate all three tiers; require binding Gate 2 hurdle $E[R_{\text{net}}] > 0$ with $p < 0.05$ at 20 bps baseline.
- **Current Recommendation:** `Multi-Tier Resilience Policy (Binding Gate 2 at 20 bps baseline; report 15 and 30 bps sweeps)`.
- **Evidence Supporting Recommendation:** 20 bps reflects realistic retail taker fees ($10$ bps total) plus modeled spread and impact ($10$ bps total). `REFERENCE_PRICE_ACCOUNTING` eliminates double-counting.
- **Unresolved Limitations:** Overlapping holding periods (up to 288 bars) make 24-bar MBB inadequate; 288-bar calendar MBB is a candidate, not validated optimal; confirmatory family size ($K=10$ vs $K=11$) depends on DEC_06.
- **Dependencies:** Depends on DEC_01 estimand, DEC_06 fleet size, and DEC_03 funding cash flows.
- **Consequences of Approval:** Sets unambiguous statistical and cost thresholds for economic validation.
- **Consequences of Rejection:** No quantitative standard exists to determine whether models have tradeable alpha.
- **Human Decision:** `[BLANK - PENDING HUMAN INPUT]`
- **Human Rationale:** `[BLANK - PENDING HUMAN INPUT]`
- **Reviewer Identity:** `[BLANK - PENDING HUMAN INPUT]`
- **Approval Timestamp:** `[BLANK - PENDING HUMAN INPUT]`
- **Formal Status:** `PENDING_HUMAN_DECISION`

---

## DECISION 5: PORTFOLIO CONCURRENCY AND RISK OPTIONS (DEC_05)
- **Question:** What portfolio concurrency, gross exposure, and stop-loss risk policy should be enforced?
- **Available Options:**
  - `Option 1 (Fixed Gross Exposure Cap)`: Hard cap on aggregate gross notional (e.g. $\sum |N_i| \le 0.30 \times \text{Equity}$).
  - `Option 2 (Risk-Budget-Based Position Sizing)`: Dynamic sizing scaled inversely with asset volatility ($N_i \propto 1 / \sigma_i$) to equalize nominal stop risk.
  - `Option 3 (Combined Exposure Cap and Stop-Risk Budget)`: Enforce both a maximum gross exposure cap and a per-position nominal stop-risk limit.
- **Current Recommendation:** Evaluate the three options; remove all unsupported claims of guaranteed loss caps or zero liquidation risk; clarify exposure denominator.
- **Evidence Supporting Recommendation:** Nominal stop loss $L_{\text{stop, nominal}} = \sum |N_i| D_i$ decouples stop loss from gross notional under ideal stop assumptions. Realized losses depend on slippage, fees, funding, gaps, and execution reliability.
- **Unresolved Limitations:** Realized losses can exceed nominal stops; $\rho > 0.70$ is `UNSUPPORTED_IN_REPO`; exposure denominator requires human clarification.
- **Dependencies:** Depends on DEC_02 directional concurrency and DEC_06 fleet size.
- **Consequences of Approval:** Constrains portfolio gross exposure and establishes clear risk boundaries.
- **Consequences of Rejection:** Portfolio risk remains unconstrained or arbitrarily restricted.
- **Human Decision:** `[BLANK - PENDING HUMAN INPUT]`
- **Human Rationale:** `[BLANK - PENDING HUMAN INPUT]`
- **Reviewer Identity:** `[BLANK - PENDING HUMAN INPUT]`
- **Approval Timestamp:** `[BLANK - PENDING HUMAN INPUT]`
- **Formal Status:** `PENDING_HUMAN_DECISION`

---

## DECISION 6: XMR RESEARCH AND PORTFOLIO SCOPE (DEC_06)
- **Question:** How should XMRUSDT be handled given its shorter historical coverage (83,863 vs 316,500 candles)?
- **Available Options:**
  - `Include in Primary Portfolio (K=11)`: Include XMR directly in the multi-asset portfolio aggregation and set confirmatory family size to $K=11$.
  - `Exclude from Primary Portfolio (K=10)`: Preserve all XMR artifacts 100%; report standalone metrics in an appendix; set primary confirmatory family size to $K=10$.
  - `Complete Exclusion`: Delete or ignore XMR model binaries entirely.
- **Current Recommendation:** `Exclude from Primary Portfolio (Three-Tier Policy, K=10)`.
- **Evidence Supporting Recommendation:** XMR data starts January 13, 2026 ($9.5$ months), while all other assets cover October 2023 to October 2026 ($36$ months). Aggregating XMR into the primary portfolio creates a ragged covariance matrix and distorts 3-year multi-asset metrics.
- **Unresolved Limitations:** Standalone XMR evaluation covers only Fold 5 out-of-fold data.
- **Dependencies:** Directly sets the primary confirmatory hypothesis family size in DEC_04 ($K=10$ vs $K=11$) and fleet size in DEC_05.
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
