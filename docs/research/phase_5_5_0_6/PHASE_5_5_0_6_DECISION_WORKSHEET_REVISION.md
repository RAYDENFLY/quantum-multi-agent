# QUANTUM PHASE 5.5.0.6: REVISED HUMAN DECISION WORKSHEET

**Worksheet Status:** `UNEXECUTED_WORKSHEET_AWAITING_HUMAN_SIGN_OFF`  
**Publication Timestamp:** `2026-11-01 21:09:14 UTC`  
**Repository:** `https://github.com/RAYDENFLY/quantum-multi-agent`  

---

## INSTRUCTIONS FOR HUMAN SUPERVISOR

This worksheet incorporates all Phase 5.5.0.6 corrections. For each decision, record your selection, rationale, and accepted limitations. All fields remain pending until signed by the supervisor.

---

## DECISION 1: BARRIER EXECUTION ARCHITECTURE (DEC_01)
- **Question:** Does Phase 5.5 evaluate the frozen classifier under re-anchored barrier execution (Track 2 / Alternative B) or explore independent strategy development (Track 3 / Alternative C)?
- **Options:**
  - `Alternative B`: Re-anchor symmetric barriers to entry fill (Tests classifier utility under re-anchored execution).
  - `Alternative C`: Decouple classifier from independent trade management policy (Tests downstream algorithmic strategy).
  - `Sequential Tracks`: Execute Track 2 first as mandatory baseline; authorize Track 3 for subsequent exploratory phases.
- **Consequences:** Alt B provides clean economic evaluation with zero parameter tuning. Alt C requires tuning exit parameters on Folds 1-4 with Fold 5 held out.
- **Evidence Limitations:** Re-anchoring barriers changes the price levels relative to close[i] training labels.
- **Recommended Choice:** `Sequential Tracks (Alternative B as primary baseline)`.
- **Human Selection:** `[PENDING_HUMAN_SELECTION]`
- **Human Rationale:** `[PENDING_HUMAN_INPUT]`
- **Accepted Limitations:** `[PENDING_HUMAN_INPUT]`
- **Approval Timestamp:** `[PENDING_HUMAN_TIMESTAMP]`
- **Status:** `PENDING_HUMAN_DECISION`

---

## DECISION 2: DIRECTIONAL TRADING SCOPE (DEC_02)
- **Question:** Should the strategy execute Long-only, Short-only, or Bidirectional positions?
- **Options:**
  - `Long-Only`: Strictly execute Class +1 signals.
  - `Short-Only`: Strictly execute Class -1 signals.
  - `Bidirectional with Mandatory Separate Reporting`: Execute both directions with separate Long, Short, and Combined PnL curves.
- **Consequences:** Bidirectional doubles signal opportunity but requires proving Short trades achieve positive expectancy independently.
- **Evidence Limitations:** Historical funding rates are unverified in repository; short liquidation slippage is theoretical.
- **Recommended Choice:** `Bidirectional with mandatory separate reporting`.
- **Human Selection:** `[PENDING_HUMAN_SELECTION]`
- **Human Rationale:** `[PENDING_HUMAN_INPUT]`
- **Accepted Limitations:** `[PENDING_HUMAN_INPUT]`
- **Approval Timestamp:** `[PENDING_HUMAN_TIMESTAMP]`
- **Status:** `PENDING_HUMAN_DECISION`

---

## DECISION 3: FUNDING RATE MODEL APPROVAL (DEC_03)
- **Question:** How should unobserved financing cash flows be modeled in Phase 5.5?
- **Options:**
  - `Parametric Sensitivity Sweep`: Evaluate across [-1.0, 0.0, +1.0, +3.0 bps/settle] as unverified assumptions.
  - `Require External Backfill`: Halt Phase 5.5 until audited historical funding datasets are acquired.
- **Consequences:** Parametric sweep allows research to proceed but cannot prove historical realized net PnL.
- **Evidence Limitations:** Canonical Parquet has no funding records (`FUNDING_DATA_UNAVAILABLE`).
- **Recommended Choice:** `Parametric sensitivity sweep approved as unverified assumption`.
- **Human Selection:** `[PENDING_HUMAN_SELECTION]`
- **Human Rationale:** `[PENDING_HUMAN_INPUT]`
- **Accepted Limitations:** `[PENDING_HUMAN_INPUT]`
- **Approval Timestamp:** `[PENDING_HUMAN_TIMESTAMP]`
- **Status:** `PENDING_HUMAN_DECISION`

---

## DECISION 4: PRIMARY COST GATE & SCENARIOS (DEC_04)
- **Question:** What cost scenario and break-even acceptance rule should govern Gate 2?
- **Options:**
  - `20 bps Primary Hurdle`: Mandatory break-even filter at 20 bps round-trip friction.
  - `Multi-Scenario Reporting`: Report performance simultaneously across 15, 20, and 30 bps scenarios.
- **Consequences:** 20 bps provides a realistic hurdle for retail taker fees. Multi-scenario reporting prevents cherry-picking.
- **Evidence Limitations:** Modeled friction totals 17.83 bps, but tick-level exchange fill records are unavailable.
- **Recommended Choice:** `20 bps Primary Hurdle with Multi-Scenario Reporting (15, 20, 30 bps)`.
- **Human Selection:** `[PENDING_HUMAN_SELECTION]`
- **Human Rationale:** `[PENDING_HUMAN_INPUT]`
- **Accepted Limitations:** `[PENDING_HUMAN_INPUT]`
- **Approval Timestamp:** `[PENDING_HUMAN_TIMESTAMP]`
- **Status:** `PENDING_HUMAN_DECISION`

---

## DECISION 5: PORTFOLIO CONCURRENCY AND LEVERAGE (DEC_05)
- **Question:** What are the maximum concurrent positions and gross leverage limits?
- **Options:**
  - `Max 2 Positions, 2.0x Gross Leverage`.
  - `Max 3 Positions, 3.0x Gross Leverage`.
  - `Max 5 Positions, 5.0x Gross Leverage`.
- **Consequences:** Higher leverage magnifies drawdowns during correlated crypto sell-offs.
- **Evidence Limitations:** Cross-asset correlation $\rho > 0.70$ is a domain stylized fact, unverified in repo.
- **Recommended Choice:** `Max 3 positions, max 3.0x gross leverage with priority queue by Delta P`.
- **Human Selection:** `[PENDING_HUMAN_SELECTION]`
- **Human Rationale:** `[PENDING_HUMAN_INPUT]`
- **Accepted Limitations:** `[PENDING_HUMAN_INPUT]`
- **Approval Timestamp:** `[PENDING_HUMAN_TIMESTAMP]`
- **Status:** `PENDING_HUMAN_DECISION`

---

## DECISION 6: XMR RESEARCH AND PORTFOLIO SCOPE (DEC_06)
- **Question:** Should XMR be included in primary multi-asset portfolio aggregation?
- **Options:**
  - `Exclude from Primary Portfolio (Appendix Only)`: Preserve models 100%; report standalone metrics in appendix.
  - `Include in Primary Portfolio`: Include despite 83,863 vs 316,500 candle disparity.
- **Consequences:** Including XMR creates a ragged covariance matrix and distorts multi-year portfolio metrics.
- **Evidence Limitations:** XMR has zero data in Folds 1-4 and only 1 minority sample in Fold 5 at 20% coverage.
- **Recommended Choice:** `Exclude from primary portfolio (report in isolated appendix)`.
- **Human Selection:** `[PENDING_HUMAN_SELECTION]`
- **Human Rationale:** `[PENDING_HUMAN_INPUT]`
- **Accepted Limitations:** `[PENDING_HUMAN_INPUT]`
- **Approval Timestamp:** `[PENDING_HUMAN_TIMESTAMP]`
- **Status:** `PENDING_HUMAN_DECISION`

---

## FORMAL EXECUTION SIGN-OFF BLOCK

- **Phase 5.5 Backtesting Authorization:** `[DENIED_UNTIL_ALL_DECISIONS_SIGNED]`
- **Supervisor Signature:** `___________________________________`
- **Date:** `[UNEXECUTED]`
