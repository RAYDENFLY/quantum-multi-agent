# QUANTUM PHASE 5.5: HUMAN GOVERNANCE DECISION BRIEFING
## SIX-DECISION EXECUTIVE REVIEW & AUTHORIZATION READINESS

**Document Status:** `DECISION_BRIEFING_FOR_SUPERVISOR_REVIEW`  
**Publication Timestamp:** `2026-11-02 14:15:00 UTC`  
**Operational Mode:** `DECISION_PREPARATION_ONLY`  
**Repository:** `https://github.com/RAYDENFLY/quantum-multi-agent`  
**Human Decision Status:** `PENDING_HUMAN_DECISION` (All 6 decisions unexecuted; all decision fields blank)  
**Research Lifecycle Status:** Phase 5.5 `NOT_STARTED` | Phase 5.6 `NOT_AUTHORIZED` | Economic Backtesting `NOT_STARTED` | Holdout `STRICTLY_SEALED`  

---

## 1. MISSION & AUTHORITATIVE SOURCES

This briefing provides a comprehensive, evidence-based synthesis of the six pending human governance decisions (`DEC_01` through `DEC_06`) required before QUANTUM Phase 5.5 economic validation can be authorized.

This document does **not** create a new governance revision, does **not** modify the human decision worksheet, and does **not** select or approve any option on behalf of the human supervisor.

### Authoritative Source Hierarchy
1. [QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md) (Master Status Index)
2. [QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md) (Reconciled Errata Baseline)
3. [QUANTUM_PHASE_5_5_FINAL_CLOSURE_ADDENDUM.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_CLOSURE_ADDENDUM.md) (Final Closure Addendum)
4. [QUANTUM_PHASE_5_5_FINAL_HUMAN_DECISION_WORKSHEET.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_HUMAN_DECISION_WORKSHEET.md) (Unexecuted Sign-Off Worksheet)
5. [QUANTUM_PHASE_5_5_UNRESOLVED_ISSUE_REGISTER.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_UNRESOLVED_ISSUE_REGISTER.md) (Technical Issue Register)
6. [QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md) (Revision 1.2 Option Analysis)
7. [QUANTUM_PHASE_5_5_CROSS_DECISION_DEPENDENCIES.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_CROSS_DECISION_DEPENDENCIES.md) (Revision 1.2 Dependency Matrix)
8. Phase 5.5.0.x Quantitative Specifications:
   - [PHASE_5_5_0_6_RESEARCH_TRACK_COMPARISON.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_6/PHASE_5_5_0_6_RESEARCH_TRACK_COMPARISON.md)
   - [PHASE_5_5_0_7_TRANSACTION_COST_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_7/PHASE_5_5_0_7_TRANSACTION_COST_AUDIT.md)
   - [PHASE_5_5_0_7_TEST_INTEGRITY_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_7/PHASE_5_5_0_7_TEST_INTEGRITY_AUDIT.md)
   - [PHASE_5_5_0_8_TRANSACTION_COST_SPECIFICATION.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_TRANSACTION_COST_SPECIFICATION.md)
   - [PHASE_5_5_0_8_FUNDING_ELIGIBILITY_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_FUNDING_ELIGIBILITY_AUDIT.md)
   - [PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md)
   - [PHASE_5_5_0_8_FULL_FLEET_TEMPORAL_ISOLATION_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_FULL_FLEET_TEMPORAL_ISOLATION_AUDIT.md)

---

## 2. EPISTEMIC & EVIDENCE CLASSIFICATION RULES

Every technical claim, mathematical identity, and decision tradeoff in this briefing is governed by strict epistemic classifications:

| Classification | Operational Definition | What It Establishes | What It Cannot Establish |
|---|---|---|---|
| `VERIFIED` | Directly confirmed by command execution, deterministic validator script, or passing automated unit test in the current workspace with exit code `0`. | Document integrity, test execution pass count, and current git working-tree cleanliness. | Unexecuted backtest results or external live exchange rules. |
| `SOURCE_VERIFIED` | Directly confirmed by inspecting repository files, dataset schemas, or artifact manifests. | Physical presence of files, exact row/candle counts, SHA-256 hash matches on manifested files, or absence of funding columns. | Future out-of-sample profitability or external exchange matching engine rules. |
| `MATHEMATICALLY_VERIFIED` | Algebraically proven from closed-form accounting identities or statistical definitions. | Exact cash-flow conservation, non-double-counting of fees/slippage, and directional fee asymmetry on fixed price displacements. | That production simulation code implements the math without bugs (`ISS_10`), or that assumed parameters match market reality. |
| `METADATA_VERIFIED` | Confirmed via file footer metadata (such as Parquet row-group timestamps) without loading holdout rows. | That the 33 inspected canonical development/validation partitions terminate at `2026-10-31 21:59:59 UTC`. | That historical OS-level read access never occurred prior to this audit (`ISS_11`). |
| `REPORTED_ONLY` | Recorded in historical research reports or prior audit narratives without independent re-execution in the current turn. | Traceability to an earlier phase report or audit log. | Current-turn runtime verification unless independently re-verified. |
| `CLAIMED_ONLY` | Proposed in prior design documents based on theoretical reasoning without empirical verification on fleet return series. | A conceptual rationale for a candidate parameter (such as 24-bar MBB limitations or 288-bar horizon motivation). | Empirical statistical optimality or validated family-wise error rate coverage. |
| `NOT_VERIFIED` | Lacks empirical verification, code verification, or authoritative external documentation in the repository. | An explicit evidentiary gap that must be disclosed as a limitation or execution blocker. | Any verified guarantee. Deciding without this evidence requires accepting explicit modeling conventions or risk bounds. |
| `NOT_RUN` | Intentionally not executed during the current read-only governance turn to respect operational boundaries or avoid known legacy runner hangs. | That no prohibited backtest, training, or hanging test runner was triggered in this turn. | Pass/fail verification for the unexecuted suite. |
| `PENDING_HUMAN_DECISION` | Requires a normative governance choice, risk-tolerance selection, or research scope authorization by the human supervisor. | That engineering has presented structured alternatives and halted execution awaiting sign-off. | Authorization to execute backtesting or deploy capital. |

---

## 3. INDIVIDUAL GOVERNANCE DECISION ANALYSES (DEC_01 THROUGH DEC_06)

---

### 3.1 DEC_01: BARRIER EXECUTION ARCHITECTURE

#### 1. Decision Question
Should Phase 5.5 evaluate the frozen Phase 5.3/5.4 classifiers under re-anchored symmetric barriers aligned to realistic next-bar execution (`Track 2 / Alternative B`), or authorize independent downstream trading strategy development with new exit parameters (`Track 3 / Alternative C`), while recognizing that the original close-anchored barrier geometry (`Track 1 / Alternative A`) is `NOT AN EXECUTABLE ECONOMIC ENTRY ANCHOR`?

DEC_01 strictly decides **Layer 1: Methodology Direction Approval**. It establishes conceptual track priority and sequencing. Approval of DEC_01 does not authorize backtest engine code development (**Layer 2: Technical Design Approval**) or backtest execution (**Layer 3: Execution Authorization**), which remain contingent on specification approvals and decisions DEC_02 through DEC_06.

#### 2. Available Alternatives
- **Alternative A (Track 1: Original Close-Anchored Barriers - `NOT AN EXECUTABLE ECONOMIC ENTRY ANCHOR`):**
  - *Specification:* Reference price $P_{\text{ref}} = \text{close}[i]$, with take-profit and stop-loss barriers at $P_{\text{ref}}(1 \pm 1.5\sigma_t)$.
  - *Role:* Statistical predictive validation of the original close-anchored ML target (completed in Phase 5.3 and Phase 5.4). Track 1 is **not** described as universally or categorically "unexecutable" for all research purposes; rather, its exact classification is `NOT AN EXECUTABLE ECONOMIC ENTRY ANCHOR`. Track 1 remains directly relevant to the original close-anchored predictive target (statistical evaluation of the machine-learning classification label itself), but it must not be confused with an executable economic entry price in a causal trading simulation because feature computation and model inference require $\text{close}[i]$, which is only known after candle $i$ closes while actual market orders fill at $\text{open}[i+1]$.
- **Alternative B (Track 2: Re-Anchored Economic Barriers):**
  - *Specification:* Execute entry at $P_{\text{entry,ref}} = \text{open}[i+1]$ (plus execution deviation) and re-anchor symmetric triple barriers to $P_{\text{entry,ref}}(1 \pm 1.5\sigma_t)$ over the 12-bar holding horizon (matching the frozen Phase 5.3 target horizon of 60 minutes).
  - *Role:* Economic evaluation of the frozen classifier's directional signals under executable timing with zero additional strategy-tuning hyperparameters beyond the fixed entry rule and symmetric barrier geometry. Track 2's re-anchored economic evaluation is classified as `SIGNAL_COMPATIBLE_WITH_SEPARATE_ECONOMIC_ESTIMAND` and `ELIGIBLE_FOR_EXPLORATORY_ECONOMIC_EVALUATION_SUBJECT_TO_GOVERNANCE_APPROVAL`. It cannot retrospectively prove the original close-anchored predictive label's economic payoff, and confirmatory claims are prohibited without pre-registered protocols, approved hypothesis family $K$, validated costs/funding, and uncompromised data. Furthermore, Track 2 has **not** been empirically validated (`Phase 5.5 = NOT_STARTED`).
- **Alternative C (Track 3: Independent Downstream Strategy Development):**
  - *Specification:* Decouple trade exits from the static $1.5\sigma_t$ triple-barrier structure by introducing trailing stops, asymmetric reward-to-risk ratios, dynamic ATR bands, or partial take-profit ladders.
  - *Role:* Full algorithmic trading strategy design requiring new hyperparameter tuning on Folds 1 to 4 with Fold 5 designated as `OOS_ELIGIBILITY_NOT_VERIFIED` (prohibited for confirmatory claims, permitted for exploratory profiling only).

#### 3. Evidence Supporting Each Alternative
- **Source Documents:** [QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md) (Section 1), [PHASE_5_5_0_6_RESEARCH_TRACK_COMPARISON.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_6/PHASE_5_5_0_6_RESEARCH_TRACK_COMPARISON.md).
- **Verified Facts (`SOURCE_VERIFIED`):**
  - Phase 5.3 labels were constructed anchored to $\text{close}[i]$.
  - Using $\text{close}[i]$ as a simulated trade entry price violates causal execution timing when signals depend on $\text{close}[i]$ (`NOT AN EXECUTABLE ECONOMIC ENTRY ANCHOR`).
  - Alternative B introduces zero additional strategy-tuning hyperparameters beyond the fixed entry rule and symmetric barrier geometry, preventing post-hoc strategy overfitting on validation folds while evaluating a separate open-anchored economic estimand. (Note: zero additional strategy hyperparameters does not eliminate statistical estimation uncertainty, sampling variance, model selection bias, or multiple-testing risks across broader governance choices.)
  - Alternative C introduces multiple free parameters that require walk-forward cross-validation.

#### 4. Evidence Limitations & Missing Evidence
- **Epistemic Gap (`ISS_06`, `RESOLVED_BY_SPECIFICATION`):** Because $\text{open}[i+1] \neq \text{close}[i]$ in the presence of inter-bar gaps or microstructure noise, re-anchoring barriers to $\text{open}[i+1]$ defines a separate economic estimand and shifts the absolute barrier price levels relative to the Phase 5.3 training labels. Track 2 cannot retrospectively prove the economic payoff of the original close-anchored predictive label.
- **Missing Evidence (`NOT_VERIFIED`):** Track 2 has **not** been empirically validated; no backtest has been run under either Alternative B or Alternative C (`Phase 5.5 = NOT_STARTED`). Neither track has demonstrated positive economic expectancy.

#### 5. What Each Track Measures vs. What Each Track Cannot Prove
| Research Track | What It Measures | What It Cannot Prove | Role in Research Validity |
|---|---|---|---|
| **Track 1 (Alt A: Close-Anchored)** | Out-of-fold statistical predictive skill (ROC-AUC, Brier score, log-loss, selective precision) on the exact close-anchored predictive target. | Cannot serve as an executable economic entry price (`NOT AN EXECUTABLE ECONOMIC ENTRY ANCHOR`) because $\text{close}[i]$ is only known after bar $i$ closes. | Valid and relevant for **statistical predictive evaluation** of the ML label (already frozen in Phase 5.4). |
| **Track 2 (Alt B: Re-Anchored)** | Separate economic estimand: whether frozen model directional signals generate positive net economic expectancy under causal $\text{open}[i+1]$ entry and symmetric $1.5\sigma_t$ barriers with zero additional strategy-tuning hyperparameters. | **Cannot retrospectively prove the original predictive label's economic payoff**, because barrier levels are shifted by $(\text{open}[i+1] - \text{close}[i])$. Not yet empirically validated. | Candidate specification for **exploratory economic evaluation** (`ELIGIBLE_FOR_EXPLORATORY_ECONOMIC_EVALUATION_SUBJECT_TO_GOVERNANCE_APPROVAL`) of the frozen signals. |
| **Track 3 (Alt C: Downstream Strategy)** | Combined economic performance of the ML signal paired with newly engineered trade-management heuristics. | Cannot isolate whether economic gains or losses originate from ML signal quality or from downstream stop/target engineering. | Optional subsequent stage if Track 2 shows signal utility but suboptimal static exits. |

#### 6. Technical, Statistical, and Economic Consequences
- **Technical Consequences:** Selecting Alternative B allows direct simulation using the existing frozen out-of-fold probability artifacts without building a hyperparameter optimization loop. Selecting Alternative C requires building a strategy parameter tuning pipeline over Folds 1 to 4.
- **Statistical Consequences:** Alternative B preserves full out-of-fold sample size across all validation folds with zero optimization bias, while evaluating a separate open-anchored economic estimand (`SIGNAL_COMPATIBLE_WITH_SEPARATE_ECONOMIC_ESTIMAND`). Alternative C consumes Folds 1 to 4 for parameter fitting, while Fold 5 is classified as `OOS_ELIGIBILITY_NOT_VERIFIED` due to prior model evaluation and unverified researcher exposure (prohibiting confirmatory claims on Fold 5 and restricting it to exploratory profiling), which sharply reduces statistical power and increases multiple-testing burden.
- **Economic Consequences:** Confusing predictive evaluation of the close-anchored target (Track 1) with an executable economic entry price is a severe methodological error: a classifier with >53% directional accuracy on close-anchored barriers can still lose money under next-open execution due to opening gaps, taker fees, and funding drag.

#### 7. Dependencies
- **Upstream:** None (Foundational decision).
- **Downstream:** Directly governs `DEC_02` (whether directional scope applies to re-anchored brackets or custom strategies), `DEC_04` (whether primary estimand tests fixed-barrier net expectancy or tuned strategy returns), and `DEC_05` (how stop-loss distances are defined for risk budgeting).

#### 8. Risks of Approval vs. Risks of Rejection
- **Risks of Approving Alternative B (Recommended by Engineering, Pending Human Approval):**
  - If opening gaps between $\text{close}[i]$ and $\text{open}[i+1]$ are large, re-anchored barriers may fail even if the model accurately predicted the close-anchored trajectory.
  - Reviewers must be strictly prohibited from claiming that Alternative B retrospectively proves the original predictive label's economic payoff or that Track 2 has already been empirically validated.
- **Risks of Rejecting Alternative B in Favor of Alternative C:**
  - High risk of overfitting downstream exit rules to historical noise, masking poor underlying ML signal quality, and exhausting statistical degrees of freedom prior to the prospective holdout.

#### 9. Additional Evidence That Would Improve the Decision
- Empirical measurement of the distribution of $|\text{open}[i+1] - \text{close}[i]| / \sigma_t$ across the 11 assets in the pre-holdout dataset to quantify how much barrier re-anchoring shifts trigger boundaries relative to intrabar volatility.

#### 10. Explicit Human Decision Field
- **Decision Status:** `PENDING_HUMAN_DECISION`
- **Approval Scope:** Strictly Layer 1 (Methodology Direction Approval). Does not authorize Layer 2 (technical design) or Layer 3 (execution).
- **Selected Alternative (`Alternative A` / `Alternative B` / `Alternative C`):** `[BLANK - PENDING HUMAN INPUT]`
- **Supervisor Rationale:** `[BLANK - PENDING HUMAN INPUT]`

---

### 3.2 DEC_02: DIRECTIONAL TRADING SCOPE

#### 1. Decision Question
Which directional trading execution scope (`Option 1: Long-Only`, `Option 2: Short-Only`, or `Option 3: Bidirectional Execution`) is authorized for Phase 5.5 economic evaluation, given that disaggregated research reporting across Long-Only, Short-Only, and Combined results is mandatory across all options?

#### 2. Available Alternatives
- **Option 1 (Long-Only Execution Authorization):** Authorize simulated trade execution only for positive directional signals ($d = +1$). Short signals ($d = -1$) and Combined series are evaluated in mandatory diagnostic reporting tables but excluded from authorized strategy execution.
- **Option 2 (Short-Only Execution Authorization):** Authorize simulated trade execution only for negative directional signals ($d = -1$). Long signals ($d = +1$) and Combined series are evaluated in mandatory diagnostic reporting tables but excluded from authorized strategy execution.
- **Option 3 (Bidirectional Execution Authorization):** Authorize simulated trade execution for both Long ($d = +1$) and Short ($d = -1$) signals, subject to mandatory disaggregated reporting of Long-Only, Short-Only, and Combined performance.

#### 3. Separation of Evaluation, Directional Reporting, and Execution Authorization
Source documents ([QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md) Section 5) establish four distinct concepts that must never be conflated:
1. **Directional Model Evaluation:** Inspecting out-of-fold predictions for Class $+1$ and Class $-1$ separately.
2. **Directional Reporting (Mandatory Transparency Standard):** Publishing separate performance tables for Long-Only, Short-Only, and Combined trades across every option so that strong performance on one side cannot conceal negative expectancy on the other.
3. **Combined Statistical Reporting:** Computing aggregate metrics across pooled Long and Short trades.
4. **Actual Execution Authorization (`DEC_02`):** The normative governance decision specifying whether the trading system is permitted to execute Long-Only, Short-Only, or Bidirectional trades. **Directional reporting is mandatory across all options and must be strictly distinguished from execution authorization: evaluating or reporting Long, Short, and Combined tables does NOT automatically authorize bidirectional execution or pre-determine the confirmatory hypothesis family size $K$.**

#### 4. Evidence Supporting Each Alternative
- **Source Documents:** [QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md) (Section 2), [PHASE_5_5_0_8_QUANTITATIVE_SPECIFICATION_AUDIT_REPORT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_QUANTITATIVE_SPECIFICATION_AUDIT_REPORT.md).
- **Verified Facts (`MATHEMATICALLY_VERIFIED` & `SOURCE_VERIFIED`):**
  - **Directional Fee Asymmetry (`MATHEMATICALLY_VERIFIED`):** Because perpetual futures exchange fees are charged on executed quote notional ($N = Q \times P_{\text{exec}}$), a winning Long trade exiting at $+1.50\%$ has a higher exit notional ($1.015 N_{\text{entry}}$) than a winning Short trade exiting at $-1.50\%$ ($0.985 N_{\text{entry}}$). Under a $7.5$ bps per-leg fee/slippage scenario, a winning Long incurs $15.1125$ bps of entry notional in costs, whereas a winning Short incurs $14.8875$ bps ($14.89$ vs $15.11$ bps). Conversely, losing Short trades exiting at $+1.50\%$ incur higher fee drag ($15.1125$ bps) than losing Long trades exiting at $-1.50\%$ ($14.8875$ bps).
  - **Selective Classification Sample Asymmetry (`SOURCE_VERIFIED`):** In Phase 5.4 selective classification, confidence thresholds ($\tau$) filter Class $+1$ and Class $-1$ tails independently, producing unequal Long and Short trade counts across instruments and folds.

#### 5. Evidence Limitations & Missing Evidence
- **Missing Evidence (`NOT_VERIFIED`):** Actual post-cost net expectancy for Long vs. Short subsets across the 11 assets has not been computed (`Phase 5.5 = NOT_STARTED`).
- **Market-Regime Sensitivity (`NOT_VERIFIED`):** Perpetual futures exhibit strong secular drift and funding asymmetry across bull and bear years (2023-2026). Whether Short signals survive positive bull-market drift or Long signals survive bear-market drawdowns is unknown prior to backtesting.

#### 6. Technical, Statistical, and Economic Consequences
- **Sample Size & Signal Frequency:** Restricting execution to Long-Only or Short-Only cuts total executed trade frequency roughly in half, directly impacting whether a specialist can reach the future aggressive research benchmark (`600 COMPLETED TRADES PER ASSET PER YEAR`).
- **Multiple-Hypothesis Implications (`DEC_02 -> DEC_04.6` Link):**
  - Selecting Long-Only, Short-Only, or Bidirectional execution in `DEC_02` does **not** automatically multiply the confirmatory hypothesis family $K$ by $1\times$, $2\times$, or $3\times$.
  - Rather, $K$ is determined jointly by five explicit governance specifications in `DEC_04.6`, `DEC_02`, and `DEC_06`:
    1. The number of assets in the primary universe (`DEC_06`: 10 vs. 11).
    2. Whether Long and Short are evaluated as separate confirmatory hypotheses.
    3. Whether the Combined series is evaluated as an independent confirmatory hypothesis.
    4. Whether the primary confirmatory estimand is defined at the asset level or portfolio level.
    5. Which directional and asset tests are designated as confirmatory gates versus exploratory/diagnostic reporting tables.
  - Consequently, the values $K = 10/11$, $K = 20/22$, $K = 30/33$, and $K = 1$ are **conditional examples** illustrating specific combinations of those five choices, not an automatic multiplier of `DEC_02` or a pre-approved multiplicity family.
- **Portfolio Exposure Consequences (`DEC_05` Link):** Bidirectional execution allows simultaneous Long positions in some assets and Short positions in others. While this reduces net directional market beta, gross exposure ($\sum |N_i|$) still accumulates and can suffer simultaneous losses if both Long and Short positions are stopped out during high-volatility whipsaw regimes.

#### 7. Dependencies
- **Upstream:** Depends on `DEC_01` (barrier execution specification).
- **Downstream:** Informs `DEC_04.6` (as one of the five joint inputs into confirmatory hypothesis family size $K$) and `DEC_05` (portfolio concurrency and gross vs. net exposure behavior).

#### 8. Risks of Approval vs. Risks of Rejection
- **Risks of Approving Option 1 (Long-Only) or Option 2 (Short-Only):** Forfeits half of the model's predictive signals, leaves the portfolio unhedged during opposite macro regimes, and reduces active trading days.
- **Risks of Approving Option 3 (Bidirectional Execution):** If one direction (e.g. Short in a secular bull market) has structurally negative net expectancy, pooling it with a profitable Long side in combined execution degrades net portfolio alpha unless Long and Short are subjected to separate confirmatory gates (e.g. conditional example $K=20$ or $22$) or an explicit directional sign constraint.

#### 9. Additional Evidence That Would Improve the Decision
- Clarification from the human supervisor on whether independent directional approval (allowing a specialist to trade Long-Only if Long passes and Short fails) is desired, which informs the selection of confirmatory hypothesis family $K$ in `DEC_04.6`.

#### 10. Explicit Human Decision Field
- **Decision Status:** `PENDING_HUMAN_DECISION`
- **Selected Option (`Option 1: Long-Only` / `Option 2: Short-Only` / `Option 3: Bidirectional`):** `[BLANK - PENDING HUMAN INPUT]`
- **Supervisor Rationale:** `[BLANK - PENDING HUMAN INPUT]`

---

### 3.3 DEC_03: FUNDING RATE MODEL

#### 1. Decision Question
How should perpetual futures financing cash flows be modeled in Phase 5.5 economic validation (`Option 1: Zero Funding`, `Option 2: Static +1.0 bps`, or `Option 3: 4-Scenario Parametric Sensitivity Sweep` across $\{-1.0, 0.0, +1.0, +3.0\}$ bps per 8-hour settlement), and do you authorize the `EXPLICIT_SETTLEMENT_TIMING_MODELING_CONVENTION` for boundary fills given that historical funding data are unavailable and AsterDEX venue rules are unverified?

#### 2. Available Alternatives
- **Option 1 (Zero Funding Assumption):** Set $f_t = 0.0$ bps for all settlements. Evaluates pure price action and execution friction while ignoring perpetual swap carry costs.
- **Option 2 (Static Flat Funding Rate):** Apply a single constant funding rate of $f_t = +1.0$ bps ($0.01\%$) per 8-hour settlement across all trades.
- **Option 3 (4-Scenario Parametric Sensitivity Sweep):** Evaluate every trade and portfolio metric across four constant parametric scenarios: $f \in \{-1.0, 0.0, +1.0, +3.0\}$ bps per settlement (`funding_rate_bps_per_settlement`).

#### 3. Evidence Supporting Each Alternative
- **Source Documents:** [QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md) (Section 3), [QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md) (Section 6.2 & Section 8.1), [PHASE_5_5_0_8_FUNDING_ELIGIBILITY_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_FUNDING_ELIGIBILITY_AUDIT.md).
- **Verified Facts (`SOURCE_VERIFIED` & `MATHEMATICALLY_VERIFIED`):**
  - **Missing Historical Funding Data (`SOURCE_VERIFIED`, `ISS_09`):** Inspection of canonical Parquet datasets confirms that historical funding rate series are completely absent (`FUNDING_DATA_UNAVAILABLE`). Acquiring external historical data is strictly prohibited in this phase.
  - **Signed Cash-Flow Accounting Identity (`MATHEMATICALLY_VERIFIED`):**
    $$CF_{\text{funding}} = \sum_{t \in \mathcal{S}} (-d) \times N_{\text{settle},t} \times f_{t,\text{decimal}}$$
    where $N_{\text{settle},t} = Q \times P_{\text{mark},t}$ and $f_{t,\text{decimal}} = \text{bps} / 10,000$.
    In the realized loss identity $L_{\text{realized}} = L_{\text{price,ref}} + C_{\text{exec,total}} + C_{\text{fees}} - CF_{\text{funding}}$:
    - Positive $CF_{\text{funding}} > 0$ means funding is **received** (reduces economic loss).
    - Negative $CF_{\text{funding}} < 0$ means funding is **paid** (increases economic loss).
  - **Nominal Annualization Convention (`MATHEMATICALLY_VERIFIED`, `ISS_09`):** With 3 settlements per day (00:00, 08:00, 16:00 UTC), nominal annualized basis points equal $1095 = 3 \times 365$ times the per-settlement rate (an arithmetic scaling convention, not compounded portfolio return).

#### 4. Evidence Limitations & Missing Evidence
- **Parametric Scenarios Are Not Historical Evidence (`SOURCE_VERIFIED`):** The scenarios $\{-1.0, 0.0, +1.0, +3.0\}$ bps are synthetic stress parameters. They do **not** capture time-varying funding spikes, regime correlation between price rallies and funding spikes, or cross-asset funding dispersion.
- **Unverified Venue Boundary Rule (`NOT_VERIFIED`, `ISS_01`):** For an order filled at the exact settlement timestamp `08:00:00.000 UTC` (or `00:00:00.000`, `16:00:00.000`), whether the exchange matching engine includes or excludes that position from the contemporaneous settlement is `NOT_VERIFIED` because official AsterDEX matching engine timestamp specifications are not in the repository.
- **Directional Asymmetry of Boundary Exclusion (`MATHEMATICALLY_VERIFIED`):** In [QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md) (Section 8.1), excluding an `08:00:00.000` open fill from the `08:00:00` settlement is designated as `EXPLICIT_SETTLEMENT_TIMING_MODELING_CONVENTION`. It is **not uniformly conservative**:
  - When a trade would **receive** funding (Long with $f_t < 0$, or Short with $f_t > 0$), excluding the boundary settlement withholds income (**conservative**).
  - When a trade would **pay** funding (Long with $f_t > 0$, or Short with $f_t < 0$), excluding the boundary settlement shields the trade from a cash outflow (**optimistic**).

#### 5. What Parametric Scenarios Can and Cannot Establish
- **Permitted Conclusions:** "The strategy maintains positive net expectancy under constant per-settlement funding charges up to $+3.0$ bps for Longs and $-1.0$ bps for Shorts."
- **Prohibited Conclusions:** "The sensitivity sweep reproduces actual historical funding economics or proves that historical funding drag was bounded by $+3.0$ bps."

#### 6. Technical, Statistical, and Economic Consequences
- **Technical Consequences:** Option 3 requires computing net return trajectories under 4 funding vectors and adopting the `EXPLICIT_SETTLEMENT_TIMING_MODELING_CONVENTION` (strict inequality $t_{\text{entry}} < t_{\text{settle}} \le t_{\text{exit}}$) in simulation code.
- **Statistical Consequences:** Multiplies the number of reported cost/funding sensitivity tables, requiring a clear designation in `DEC_04` of which funding scenario serves as the primary binding gate (typically $+1.0$ bps baseline, with $+3.0$ bps as stress).
- **Economic Consequences:** Under the reconciled 12-bar horizon (60 minutes), a trade crosses at most one 8-hour settlement timestamp, incurring up to $3.0$ bps of funding drag under $+3.0$ bps stress; if an extended holding duration (up to 288 bars / 24 hours) were used, a $+3.0$ bps funding rate would cost a Long position up to $9.0$ bps across 3 settlements, which can erase thin predictive edges.

#### 7. Dependencies
- **Upstream:** Independent foundational decision (depends on dataset availability status `ISS_09` and convention `ISS_01`).
- **Downstream:** Directly feeds net return calculations in `DEC_04` (Acceptance Gate 2 & Gate 3) and realized loss accounting in `DEC_05`.

#### 8. Risks of Approval vs. Risks of Rejection
- **Risks of Approving Option 3 + Timing Convention:** Simulates synthetic constant funding rather than realized historical funding; boundary exclusion slightly understates funding costs for funding-payers entering exactly on settlement bars.
- **Risks of Rejecting Option 3 (Selecting Option 1 or Option 2):** Option 1 ($0.0$ bps) ignores a major perpetual futures cost component and overstates Long profitability; Option 2 ($+1.0$ bps only) fails to test Short funding payments during negative-funding bear regimes ($-1.0$ bps) or Long costs during crowded bull regimes ($+3.0$ bps).

#### 9. Additional Evidence That Would Improve the Decision
- Official AsterDEX exchange technical documentation verifying exact millisecond cutoff rules for funding settlement snapshots (`ISS_01`), and authorized ingestion of historical exchange funding rate archives in a future data-acquisition phase (`ISS_09`).

#### 10. Explicit Human Decision Field
- **Decision Status:** `PENDING_HUMAN_DECISION`
- **Selected Option (`Option 1` / `Option 2` / `Option 3` + Settlement Convention):** `[BLANK - PENDING HUMAN INPUT]`
- **Supervisor Rationale:** `[BLANK - PENDING HUMAN INPUT]`

---

### 3.4 DEC_04: COST SCENARIOS AND STATISTICAL ACCEPTANCE CRITERIA (SEVEN INDEPENDENT SUBDECISIONS)

#### 1. Decision Question & Modular Decomposition
Because `DEC_04` spans accounting conventions, partial-fill allocation rules, resampling mechanics, multiplicity definitions, and acceptance hurdles, **it must NOT be treated as a single inseparable methodological package**. Approval of any one component below does **not** imply approval of the others. `DEC_04` is decomposed into **seven independently identifiable subdecisions (`DEC_04.1` through `DEC_04.7`)**:

1. **`DEC_04.1` - Economic Reference-Price Accounting (`REFERENCE_PRICE_ACCOUNTING`):**
   - *Question:* Authorize decomposing realized trade loss into reference price displacement $L_{\text{price,ref}} = -d Q (P_{\text{exit,ref}} - P_{\text{entry,ref}})$, execution deviation $C_{\text{exec,total}}$, exchange fees $C_{\text{fees}}$ on actual executed notional, and signed funding $-CF_{\text{funding}}$ so that spread, slippage, and gap-through-stop fills are never double-counted?
   - *Alternatives:* **Option 4.1-A:** Approve `REFERENCE_PRICE_ACCOUNTING` decomposition (`MATHEMATICALLY_VERIFIED` zero double-counting). | **Option 4.1-B:** Reject or request an alternative accounting decomposition.
   - *Constraint:* Mathematical identity is `MATHEMATICALLY_VERIFIED` (`ISS_02`, `ISS_03`), whereas runtime simulation code implementation remains `NOT_VERIFIED` (`ISS_10`).

2. **`DEC_04.2` - Execution Deviation Methodology (`Approach A` vs. `Approach B`):**
   - *Question:* Which execution deviation ledger formulation should be used inside the reference-price accounting specification?
   - *Alternatives:*
     - **Option 4.2-A (`Approach A` - Nonnegative Adverse Slippage Floor):** $C_{\text{slippage}} = \max(0, Q(-d)(P_{\text{exec}} - P_{\text{ref}}))$, paired with a separate price-improvement ledger when fills beat $P_{\text{ref}}$.
     - **Option 4.2-B (`Approach B` - Signed Execution Deviation):** Two-legged signed deviation $C_{\text{exec,total}} = Q d (P_{\text{entry,exec}} - P_{\text{entry,ref}}) + Q (-d) (P_{\text{exit,exec}} - P_{\text{exit,ref}})$ (or slice-summed equivalent), conserving cash flows symmetrically in a single term.
   - *Constraint:* `Approach B` is **not** approved merely because it is recommended by engineering (`RECOMMENDED_PENDING_HUMAN_APPROVAL`); both `Approach A` and `Approach B` remain open alternatives awaiting explicit supervisor selection.

3. **`DEC_04.3` - Partial-Fill Cost-Basis Policy (`Average Cost Basis` vs. `FIFO`):**
   - *Question:* When a position is entered via multiple partial fills ($m > 1$) and only partially exited ($\sum_{j=1}^n q_{\text{exit},j} = Q_{\text{closed}} < Q_{\text{open}} = \sum_{i=1}^m q_{\text{entry},i}$), which cost-basis allocation rule governs the closed portion?
   - *Alternatives:*
     - **Option 4.3-A (`Average Cost Basis` / VWAP Allocation):** Allocate volume-weighted average entry price $\bar{P}_{\text{entry,exec}}$ and entry execution deviation proportionally by closed quantity fraction $(Q_{\text{closed}} / Q_{\text{open}})$.
     - **Option 4.3-B (`FIFO` / First-In, First-Out Matching):** Match each exit fill slice $q_{\text{exit},j}$ chronologically against the earliest unclosed entry fill lots $q_{\text{entry},i}$.
   - *Constraint:* For a fully closed trade ($Q_{\text{closed}} = Q_{\text{open}}$), both methods yield the exact same cumulative PnL (`MATHEMATICALLY_VERIFIED`). For partially closed positions ($Q_{\text{closed}} < Q_{\text{open}}$), `Average Cost Basis` and `FIFO` remain **unselected alternatives** (`PENDING_HUMAN_DECISION`).

4. **`DEC_04.4` - Bootstrap Methodology (Trade-Level vs. Calendar Moving Block Bootstrap):**
   - *Question:* Which resampling architecture should generate empirical sampling distributions and p-values for correlated multi-asset return series?
   - *Alternatives:*
     - **Option 4.4-A (`Trade-Level Resampling Bootstrap`):** Resample individual completed trade returns with replacement.
     - **Option 4.4-B (`Continuous Calendar-Time Portfolio Moving Block Bootstrap` - Calendar MBB):** Resample contiguous calendar-time blocks of 5-minute bar returns simultaneously across all active assets in the primary universe.
   - *Constraint:* Calendar MBB preserves contemporaneous cross-asset correlation and overlapping holding periods (`MATHEMATICALLY_VERIFIED`), whereas runtime implementation remains `NOT_VERIFIED` (`ISS_10`).

5. **`DEC_04.5` - Candidate Block Length and Sensitivity Analysis ($72$, $144$, $288$, and $576$ Bars):**
   - *Question:* If Calendar MBB is selected in `DEC_04.4`, should $b = 288$ bars (24 hours) be authorized as the **provisional candidate block length**, accompanied by a mandatory diagnostic sensitivity sweep across $b \in \{72, 144, 288, 576\}$ bars (`6h, 12h, 24h, 48h`)?
   - *Alternatives:*
     - **Option 4.5-A:** Authorize $b = 288$ bars as a provisional candidate block length (`PROVISIONALLY_APPROVED_RESEARCH_SPECIFICATION`) with mandatory sensitivity reporting across $72$, $144$, $288$, and $576$ bars.
     - **Option 4.5-B:** Select a different primary block length from $\{72, 144, 288, 576\}$ or require empirical autocorrelation estimation prior to fixing $b$.
   - *Constraint:* **$288$ bars is a provisional candidate, NOT an empirically validated optimum (`ISS_04: CLAIMED_ONLY`).** Furthermore, **the sensitivity sweep across $72$, $144$, $288$, and $576$ bars has NOT been performed (`ISS_05: NOT_VERIFIED`).** Approving `DEC_04.5` authorizes a provisional research specification, not an empirically validated statistical methodology.

6. **`DEC_04.6` - Confirmatory Hypothesis Family $K$:**
   - *Question:* How should the confirmatory hypothesis family size $K$ be defined for Holm-Bonferroni Family-Wise Error Rate ($\text{FWER} \le 0.05$) control?
   - *Determinants of $K$:* $K$ is **not** an automatic $1\times, 2\times, 3\times$ multiple of `DEC_02`. It depends jointly on five explicit specification choices: (1) number of assets in the primary universe (`DEC_06`: 10 vs. 11), (2) whether Long and Short are separate confirmatory hypotheses, (3) whether Combined is an independent confirmatory hypothesis, (4) whether the primary estimand is asset-level or portfolio-level, and (5) which tests are designated as confirmatory gates vs. exploratory diagnostics.
   - *Conditional Examples (Not a Pre-Approved Multiplicity Family):*
     - **Conditional Example K-1 ($K = 10$ or $11$):** Asset-level primary estimand; 1 confirmatory hypothesis per asset (e.g. Long-only, Short-only, or Combined per asset; remaining tables exploratory).
     - **Conditional Example K-2 ($K = 20$ or $22$):** Asset-level primary estimand; Long and Short tested as 2 separate confirmatory hypotheses per asset (Combined table exploratory).
     - **Conditional Example K-3 ($K = 30$ or $33$):** Asset-level primary estimand; Long, Short, and Combined all treated as 3 independent confirmatory hypotheses per asset.
     - **Conditional Example K-4 ($K = 1$):** Portfolio-level primary estimand; 1 aggregate portfolio confirmatory hypothesis (all asset-level and directional tables exploratory).

7. **`DEC_04.7` - Economic Acceptance Criteria and Cost Assumptions:**
   - *Question:* Authorize the 3-tier round-trip transaction-cost sensitivity sweep ($15$ bps optimistic, $20$ bps baseline, $30$ bps punitive stress) and the 4-level hierarchical economic acceptance gate (Level 1: Cost Survival; Level 2: Positive Net Expectancy & Profit Factor $> 1.05$; Level 3: Holm-Bonferroni Statistical Significance at $\alpha = 0.05$; Level 4: Benchmark Outperformance)?
   - *Alternatives:*
     - **Option 4.7-A:** Authorize the $15 / 20 / 30$ bps cost sweep (with $20$ bps as baseline gate) and the 4-level acceptance hierarchy.
     - **Option 4.7-B:** Modify the cost bps tiers or acceptance thresholds.

#### 2. Evidence Supporting Each Subdecision & What Remains Empirically Unvalidated
- **Source Documents:** [QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md) (Sections 4 & 5), [QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md) (Sections 2, 4, 6, 7), [QUANTUM_PHASE_5_5_FINAL_CLOSURE_ADDENDUM.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_CLOSURE_ADDENDUM.md) (Section 3), [PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_STATISTICAL_INFERENCE_SPECIFICATION.md).
- **Mathematically Established (`MATHEMATICALLY_VERIFIED`):**
  - Reference-price accounting (`DEC_04.1`) and signed execution deviation (`DEC_04.2`) satisfy exact cash-flow conservation with zero residual error (`ISS_02`, `ISS_03`).
  - Average Cost Basis and FIFO (`DEC_04.3`) are algebraically identical when $Q_{\text{closed}} = Q_{\text{open}}$ and diverge only on intermediate partial exits ($Q_{\text{closed}} < Q_{\text{open}}$).
  - Multi-asset calendar block resampling (`DEC_04.4`) preserves cross-asset timestamp alignment, and Holm-Bonferroni step-down thresholds $\alpha / (K - i + 1)$ (`DEC_04.6`) bound FWER at $\alpha = 0.05$ for any fixed $K$.
- **Unvalidated / Unverified Elements (`CLAIMED_ONLY` & `NOT_VERIFIED`):**
  - **288-Bar Provisional Status (`ISS_04`, `CLAIMED_ONLY`):** $b = 288$ bars is a theoretical candidate based on the 24-hour maximum barrier horizon, **not** an empirically validated optimum. Likewise, potential limitations of 24-bar MBB for 288-bar trades remain `CLAIMED_ONLY`.
  - **Sensitivity Sweep Unexecuted (`ISS_05`, `NOT_VERIFIED`):** The block-length sensitivity sweep across $72$, $144$, $288$, and $576$ bars has **not** been executed.
  - **Runtime Accounting Code Unverified (`ISS_10`, `NOT_VERIFIED`):** The runtime Python implementation of reference-price accounting, partial-fill cost basis, and MBB resampling remains `NOT_VERIFIED` until Phase 5.5 code verification is authorized.

#### 3. Conditional Examples of Confirmatory Hypothesis Family $K$ (`DEC_04.6`)
| Conditional Example | Primary Estimand Level | Confirmatory vs Exploratory Designation | `DEC_06` Primary Universe | Resulting $K$ | Strictest Holm Hurdle ($\alpha / K$ at $\alpha=0.05$) |
|---|---|---|---|---|---|
| **Example K-1a** | Asset-Level | 1 confirmatory test/asset (L-only, S-only, or Combined); other tables exploratory | 10 Assets (XMR Excluded) | **$K = 10$** | $p_{(1)} \le 0.00500$ |
| **Example K-1b** | Asset-Level | 1 confirmatory test/asset (L-only, S-only, or Combined); other tables exploratory | 11 Assets (XMR Included) | **$K = 11$** | $p_{(1)} \le 0.00455$ |
| **Example K-2a** | Asset-Level | Long and Short as 2 separate confirmatory tests/asset; Combined exploratory | 10 Assets (XMR Excluded) | **$K = 20$** | $p_{(1)} \le 0.00250$ |
| **Example K-2b** | Asset-Level | Long and Short as 2 separate confirmatory tests/asset; Combined exploratory | 11 Assets (XMR Included) | **$K = 22$** | $p_{(1)} \le 0.00227$ |
| **Example K-3a** | Asset-Level | Long, Short, and Combined all designated as 3 confirmatory tests/asset | 10 Assets (XMR Excluded) | **$K = 30$** | $p_{(1)} \le 0.00167$ |
| **Example K-3b** | Asset-Level | Long, Short, and Combined all designated as 3 confirmatory tests/asset | 11 Assets (XMR Included) | **$K = 33$** | $p_{(1)} \le 0.00152$ |
| **Example K-4** | Portfolio-Level | 1 aggregate portfolio confirmatory test; all asset & directional tables exploratory | 10 or 11 Assets | **$K = 1$** | $p_{(1)} \le 0.05000$ |

#### 4. Technical, Statistical, and Economic Consequences
- **Modular Governance Control:** Separating `DEC_04.1` through `DEC_04.7` allows the supervisor to approve `REFERENCE_PRICE_ACCOUNTING` (`DEC_04.1`) and `Calendar MBB` (`DEC_04.4`) while independently choosing `Approach A` vs. `Approach B` (`DEC_04.2`), `Average Cost Basis` vs. `FIFO` (`DEC_04.3`), provisional block length (`DEC_04.5`), multiplicity structure $K$ (`DEC_04.6`), and cost tiers (`DEC_04.7`).
- **Consequences of Mis-specifying $K$:** Under-specifying $K$ while selecting winners post-hoc inflates Type I false discoveries; over-specifying $K$ (e.g. $K=33$ when only 1 test per asset is confirmatory) inflates Type II false rejections.

#### 5. Dependencies
- **Upstream:** Depends on `DEC_01` (economic estimand), `DEC_02` (authorized execution directions), `DEC_03` (funding scenarios), and `DEC_06` (10 vs. 11 primary assets).
- **Downstream:** Governs which specialists pass economic validation to enter the `DEC_05` portfolio risk policy.

#### 6. Risks of Approval vs. Risks of Rejection
- **Risks of Approving `DEC_04` Subdecisions Without Resolving `ISS_10`:** Approving the mathematical specification does not verify runtime code; `ISS_10` must be closed by unit tests before running full fleet simulations.
- **Risks of Selecting Trade-Level Bootstrap (`DEC_04.4` Option 4.4-A):** Ignores cross-asset and temporal dependence, producing invalid p-values.

#### 7. Additional Evidence That Would Improve the Decision
- Runtime unit-test verification of the accounting and MBB code (`ISS_10`), and empirical return autocorrelation diagnostics across $b \in \{72, 144, 288, 576\}$ bars (`ISS_05`).

#### 8. Explicit Independent Human Decision Fields (`DEC_04.1` Through `DEC_04.7`)
- **Overall `DEC_04` Status:** `PENDING_HUMAN_DECISION` (Approval of any subdecision below does **not** imply approval of any other subdecision)
  - **`DEC_04.1` (Economic Reference-Price Accounting - `REFERENCE_PRICE_ACCOUNTING`):** `[BLANK - PENDING HUMAN INPUT]`
  - **`DEC_04.2` (Execution Deviation Methodology - `Approach A` vs. `Approach B`):** `[BLANK - PENDING HUMAN INPUT]`
  - **`DEC_04.3` (Partial-Fill Cost-Basis Policy - `Average Cost Basis` vs. `FIFO`):** `[BLANK - PENDING HUMAN INPUT]`
  - **`DEC_04.4` (Bootstrap Methodology - `Trade-Level Bootstrap` vs. `Calendar MBB`):** `[BLANK - PENDING HUMAN INPUT]`
  - **`DEC_04.5` (Candidate Block Length $b=288$ Provisional & Sensitivity Sweep `{72, 144, 288, 576}`):** `[BLANK - PENDING HUMAN INPUT]`
  - **`DEC_04.6` (Confirmatory Hypothesis Family $K$ Specification):** `[BLANK - PENDING HUMAN INPUT]`
  - **`DEC_04.7` (Economic Acceptance Criteria & `15 / 20 / 30` bps Cost Sweep):** `[BLANK - PENDING HUMAN INPUT]`
- **Supervisor Rationale:** `[BLANK - PENDING HUMAN INPUT]`

---

### 3.5 DEC_05: PORTFOLIO CONCURRENCY AND LEVERAGE

#### 1. Decision Question
Which portfolio risk and concurrency policy (`Option 1: Fixed Gross Exposure Cap`, `Option 2: Risk-Budget-Based Position Sizing`, or `Option 3: Combined Exposure Cap and Stop-Risk Budget`) is authorized to govern multi-specialist capital allocation, and how should the exposure cap denominator be defined?

#### 2. Strict Separation of Portfolio Risk Policy from Execution Accounting
As established in [QUANTUM_PHASE_5_5_FINAL_CLOSURE_ADDENDUM.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_CLOSURE_ADDENDUM.md) and [QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md), `DEC_05` addresses **pure portfolio risk policy only** (capital allocation, gross exposure, leverage limits, position sizing, concurrency, correlation stress, and drawdown limits). Execution cost accounting (`Approach A` vs. `Approach B`) belongs to the technical accounting specification (`DEC_04`) and must **not** be combined with `DEC_05` or treated as an automatic consequence of selecting `DEC_05` Option 1, 2, or 3.

#### 3. Explicit Distinction of Exposure, Leverage, Margin, and Loss Concepts
| Risk Metric | Exact Mathematical / Operational Definition | Why It Cannot Be Conflated With Other Metrics |
|---|---|---|
| **Gross Notional Exposure** | $\text{GrossExposure} = \sum_{i=1}^n |N_i| = \sum_{i=1}^n Q_i P_i$ | Measures total absolute market value of open positions. Does not account for account equity denominator or asset volatility $\sigma_i$. |
| **Gross Leverage** | $\text{GrossLeverage} = \frac{\text{GrossExposure}}{\text{AccountEquity}}$ | A 30% gross exposure limit ($\text{GrossLeverage} = 0.30\times$) is **NOT** equivalent to $1.0\times$ leverage; it leaves 70% of equity unexposed in notional terms. |
| **Margin Usage (Utilization)** | $\text{MarginUtilization} = \frac{\sum_{i=1}^n \text{InitialMargin}_i}{\text{AvailableEquity}}$ | Depends on venue initial margin requirements (e.g. 5% to 10% on AsterDEX). Low margin usage does not imply low portfolio risk. |
| **Modeled Stop-Loss Loss** | $\sum_{i=1}^n Q_i \cdot (1.5 \sigma_{i,t} P_{\text{entry},i}) + C_{\text{fees},i}$ | Theoretical loss if every active position exits exactly at its reference stop-loss barrier $P_{\text{entry}}(1 \mp 1.5\sigma_t)$ with zero slippage. |
| **Maximum Possible Loss** | Unbounded up to 100% of allocated collateral (or account equity under cross-margin) | **A stop-loss is NOT a guaranteed maximum loss.** During liquidity voids or flash crashes, execution fills can gap far beyond $P_{\text{stop,ref}}$, causing realized loss $L_{\text{realized}}$ to substantially exceed modeled stop-loss risk. |

#### 4. Comparison of the Three Portfolio Risk Options
| Dimension | Option 1: Fixed Gross Exposure Cap | Option 2: Risk-Budget-Based Sizing | Option 3: Combined Exposure Cap & Stop-Risk Budget |
|---|---|---|---|
| **Maximum Gross Exposure** | Hard cap (e.g. $\sum |N_i| \le 0.30 \times \text{Denominator}$). | Uncapped in notional terms unless volatility is low; bounded indirectly by risk budget. | Hard cap on aggregate gross notional (e.g. $\le 0.50\times$ or $1.00\times$ equity). |
| **Position Sizing Rule** | Equal or fixed notional per active signal until cap is reached. | Volatility-scaled: $N_i = \frac{R_{\text{budget}} \cdot \text{Equity}}{1.5 \sigma_{i,t}}$, targeting fixed nominal stop loss (e.g. $0.25\%$ to $0.33\%$ equity) per trade. | Volatility-scaled per trade, scaled down pro-rata whenever aggregate gross notional hits the hard cap. |
| **Concurrent Position Limits** | Up to $M_{\max}$ (10 or 11) specialists, subject to gross cap. | Up to $M_{\max}$ specialists, subject to total stop-risk budget (e.g. $\le 1.0\%$ aggregate modeled stop risk). | Dual ceiling: bounded by both max concurrent positions, total stop-risk budget, and gross notional cap. |
| **Leverage Implications** | Prevents high notional leverage, but concentrates risk in high-volatility altcoins. | When $\sigma_{i,t}$ is very small (quiet market regimes), inverse volatility sizing ($1/\sigma_{i,t}$) can command dangerously high notional leverage. | Prevents inverse-volatility leverage blowups during quiet markets while equalizing risk across high-vol assets. |
| **Correlation Stress & Joint Drawdown Risk** | If all 10 assets move together ($\rho \to 1.0$) and drop $5\%$, a $0.30\times$ gross cap loses $1.5\%$ of equity plus fees/slippage. | If all 10 concurrent trades hit their $0.33\%$ modeled stop simultaneously during a market crash, portfolio loses $3.3\%$ (or much more if stops gap). | Caps both normal-regime volatility risk and quiet-regime notional leverage, though extreme gap-through-stop tail risk remains. |
| **Capital Allocation Consequences** | Simple static allocation; under-allocates in low-vol assets and over-allocates risk in high-vol assets. | Dynamic capital allocation; vulnerable to volatility estimation error and flash crashes after low-vol compression. | Most robust institutional structure; requires Priority Queue / pro-rata tie-breaking when simultaneous signals exceed the cap. |

#### 5. Evidence Supporting Each Alternative & Limitations
- **Source Documents:** [QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md) (Section 5), [PHASE_5_5_0_5_DEC_05_PORTFOLIO_CORRELATION_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_5/PHASE_5_5_0_5_DEC_05_PORTFOLIO_CORRELATION_AUDIT.md).
- **Missing Evidence (`NOT_VERIFIED`, `ISS_08`):**
  - Prior claims that pairwise crypto correlations satisfy $\rho > 0.70$ were removed as unsupported (`NOT_VERIFIED`) because no empirical cross-asset return correlation matrix has been computed on the repository dataset.
  - However, removing the unverified $\rho > 0.70$ claim does **not** eliminate correlation stress risk: cryptocurrency perpetuals historically experience severe correlation spikes ($\rho \to 1.0$) during market-wide liquidation cascades.
- **Denominator Ambiguity (`REQUIRES_HUMAN_CLARIFICATION`):** Previous specifications referenced a "30% gross notional limit" without defining whether the denominator is initial starting capital, mark-to-market account equity, or free available margin.

#### 6. Dependencies
- **Upstream:** Terminal decision in the 6-step sequence; depends on `DEC_01` (barrier stop distance $1.5\sigma_t$), `DEC_02` (Long/Short concurrency and directional netting), `DEC_03` (funding drag on equity), `DEC_04` (which specialists pass acceptance), and `DEC_06` (10 vs. 11 maximum concurrent specialists).
- **Downstream:** Directly governs portfolio-level simulation in Phase 5.5.

#### 7. Risks of Approval vs. Risks of Rejection
- **Risks of Approving Option 1:** Ignores cross-asset volatility differences (e.g. BTC vs. DOGE/AVAX).
- **Risks of Approving Option 2:** Can generate excessive gross leverage during low-volatility compression regimes that precede violent breakouts (gap-through-stop risk).
- **Risks of Approving Option 3:** Requires explicit tie-breaking / scaling rules when concurrent signals exceed the cap; still does not guarantee a hard 1% maximum loss during extreme market gaps.

#### 8. Additional Evidence That Would Improve the Decision
- Empirical computation of the $11 \times 11$ unconditional and tail-stress (bottom 5% quantile) return correlation matrices across the pre-holdout dataset (`ISS_08`), and explicit human specification of the exposure cap denominator and tie-breaking rule.

#### 9. Explicit Human Decision Field
- **Decision Status:** `PENDING_HUMAN_DECISION`
- **Selected Option (`Option 1` / `Option 2` / `Option 3` + Denominator Definition):** `[BLANK - PENDING HUMAN INPUT]`
- **Supervisor Rationale:** `[BLANK - PENDING HUMAN INPUT]`

---

### 3.6 DEC_06: XMR RESEARCH AND PORTFOLIO SCOPE

#### 1. Decision Question
How should `XMRUSDT` be treated in Phase 5.5 economic validation (`Option 1 / Tier 1 Primary Inclusion`, `Option 2 / Complete Elimination`, or `Option 3 / Three-Tier Policy`: preserve artifacts, evaluate in standalone appendix, exclude from primary portfolio aggregation), given its severe historical data truncation relative to the other 10 assets?

#### 2. Available Alternatives
- **Option 1 (Full Primary Portfolio Inclusion):** Include `XMRUSDT` alongside the other 10 assets in the primary confirmatory hypothesis family ($K = 11$, $22$, or $33$) and primary multi-asset portfolio simulation.
- **Option 2 (Complete Elimination of XMR):** Discard `XMRUSDT` from Phase 5.5 entirely, omitting standalone evaluation and archiving/ignoring its frozen Phase 5.3/5.4 artifacts.
- **Option 3 (Three-Tier Policy):**
  - *Tier 1 (Artifact Preservation):* Preserve 100% of frozen `XMRUSDT` Phase 5.3 models, preprocessors, and Phase 5.4 materialized out-of-fold probability artifacts.
  - *Tier 2 (Standalone Research Appendix):* Evaluate `XMRUSDT` economic performance over its available Fold 5 window and report results in a dedicated standalone research appendix.
  - *Tier 3 (Primary Portfolio Exclusion):* Exclude `XMRUSDT` from the primary 3-year multi-asset portfolio simulation and primary confirmatory hypothesis family (fixing the primary universe at the 10 full-history assets).

#### 3. Evidence Supporting Each Alternative
- **Source Documents:** [QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md) (Section 6), [PHASE_5_5_0_8_FULL_FLEET_TEMPORAL_ISOLATION_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_FULL_FLEET_TEMPORAL_ISOLATION_AUDIT.md).
- **Verified Facts (`SOURCE_VERIFIED`):**
  - **10 Primary Assets** (`BTCUSDT`, `ETHUSDT`, `BNBUSDT`, `XRPUSDT`, `ADAUSDT`, `SOLUSDT`, `AVAXUSDT`, `LINKUSDT`, `DOGEUSDT`, `LTCUSDT`): Each contains exactly **316,500** 5-minute candles (~3.0 years, from October 2023 through `2026-10-31 21:59:59 UTC`), spanning Walk-Forward Folds 1 through 5.
  - **`XMRUSDT` Coverage Gap:** Contains only **83,863** 5-minute candles (~9.5 months, starting `2026-01-13` through `2026-10-31 21:59:59 UTC`), representing a **73.5% missing-data gap** across the 3-year research window and lacking Folds 1 through 4.

#### 4. Evidence Limitations & Missing Evidence
- **Single-Regime Limitation (`SOURCE_VERIFIED`):** Because `XMRUSDT` data begins in January 2026, its out-of-fold validation predictions exist only for Fold 5. It cannot be evaluated for multi-year out-of-sample stability across 2024 and 2025 market regimes.

#### 5. Technical, Statistical, and Economic Consequences
- **Technical Consequences:** Including XMR in continuous 3-year calendar-time portfolio resampling (`DEC_04`) either forces the entire 11-asset portfolio backtest to truncate to 9.5 months (throwing away 73.5% of the history of the 10 major assets) or requires ragged-array imputation/zero-padding for XMR prior to January 2026.
- **Statistical Consequences:**
  - Under Option 1, ragged missing data distorts cross-asset covariance and alters portfolio concurrency behavior between 2024-2025 (10 active assets) and 2026 (11 active assets). It also increases $K$ from $10 \to 11$ (or $20 \to 22$, $30 \to 33$).
  - Under Option 3 (Three-Tier Policy), the primary 10-asset universe is 100% balanced across all 316,500 candles ($K = 10$ or $20$), while XMR still receives rigorous standalone evaluation on Fold 5.
- **Economic Consequences:** Option 3 prevents a short-history privacy-coin specialist from distorting 3-year portfolio drawdown and Sharpe metrics while retaining the option to deploy XMR as a secondary specialist if its standalone Fold 5 results are strong.

#### 6. Dependencies
- **Upstream:** Independent foundational decision based on verified dataset geometry.
- **Downstream:** Directly sets the asset dimension of $K$ in `DEC_04` ($10$ vs. $11$ base assets) and maximum concurrent specialist count in `DEC_05`.

#### 7. Risks of Approval vs. Risks of Rejection
- **Risks of Approving Option 3 (Three-Tier Policy):** `XMRUSDT` cannot contribute diversification to the primary confirmatory portfolio metrics.
- **Risks of Approving Option 1 (Full Inclusion):** Severe statistical distortion of 3-year portfolio resampling or loss of 2+ years of validation history across 10 major assets.
- **Risks of Approving Option 2 (Complete Elimination):** Wastes already-completed Phase 5.3 and Phase 5.4 computational and research work on XMR.

#### 8. Additional Evidence That Would Improve the Decision
- No additional technical evidence is required; the candle counts ($83,863$ vs. $316,500$) are `SOURCE_VERIFIED`. The choice is purely a governance scope decision.

#### 9. Explicit Human Decision Field
- **Decision Status:** `PENDING_HUMAN_DECISION`
- **Selected Option (`Option 1: Full Inclusion` / `Option 2: Elimination` / `Option 3: Three-Tier Policy`):** `[BLANK - PENDING HUMAN INPUT]`
- **Supervisor Rationale:** `[BLANK - PENDING HUMAN INPUT]`

---

## 4. CONCISE SIX-DECISION MASTER COMPARISON TABLE

| Decision ID | Core Governance Question | Documented Alternatives | Engineering Recommendation (Non-Binding) | Highest Epistemic Support | Key Missing / Unverified Evidence | Upstream Dependencies | Downstream Impact | Current Status |
|---|---|---|---|---|---|---|---|---|
| **DEC_01** | Barrier Execution Architecture | **Alt A:** Close-anchored (Track 1, `NOT AN EXECUTABLE ECONOMIC ENTRY ANCHOR`)<br>**Alt B:** Re-anchored at $\text{open}[i+1]$ (Track 2, separate estimand)<br>**Alt C:** Downstream strategy tuning (Track 3) | **Alternative B (Track 2)** *(Pending Human Approval)* | `SOURCE_VERIFIED` (Eliminates look-ahead with 0 new DoF) | Track 2 is a separate estimand that cannot retrospectively prove close-anchored label payoff (`ISS_06`) and is `NOT_VERIFIED` empirically. | None (Foundational) | `DEC_02`, `DEC_04`, `DEC_05` | `PENDING_HUMAN_DECISION` |
| **DEC_02** | Directional Trading Execution Scope | **Opt 1:** Long-Only execution<br>**Opt 2:** Short-Only execution<br>**Opt 3:** Bidirectional execution<br>*(Disaggregated reporting mandatory for all; distinct from execution authorization)* | **Structured Choice (Opt 1, 2, or 3) with Mandatory Disaggregated Reporting** | `MATHEMATICALLY_VERIFIED` (14.89 vs 15.11 bps fee asymmetry) | Empirical Long vs Short net expectancy across regimes is `NOT_VERIFIED`. | `DEC_01` | `DEC_04.6` ($K$ joint input), `DEC_05` | `PENDING_HUMAN_DECISION` |
| **DEC_03** | Funding Rate Model & Boundary Convention | **Opt 1:** 0.0 bps<br>**Opt 2:** +1.0 bps static<br>**Opt 3:** 4-scenario sweep (-1, 0, +1, +3 bps) + Boundary Convention | **Option 3 + Explicit Settlement Timing Convention** | `MATHEMATICALLY_VERIFIED` (Signed cash-flow identity & 1095 factor) | Historical funding is `FUNDING_DATA_UNAVAILABLE` (`ISS_09`); AsterDEX 08:00:00 rule is `NOT_VERIFIED` (`ISS_01`). | None (Foundational) | `DEC_04`, `DEC_05` | `PENDING_HUMAN_DECISION` |
| **DEC_04** | Cost, Accounting, Resampling & Multiplicity (7 Independent Subdecisions `DEC_04.1`-`DEC_04.7`) | **4.1:** `REFERENCE_PRICE_ACCOUNTING`<br>**4.2:** `Approach A` vs `Approach B`<br>**4.3:** `Average Cost Basis` vs `FIFO`<br>**4.4:** Trade-level vs Calendar MBB<br>**4.5:** Provisional $b=288$ + `{72,144,288,576}` sweep<br>**4.6:** Confirmatory family $K$<br>**4.7:** 4-level gate + `15/20/30` bps sweep | **7 Independent Subdecisions** *(No bundled approval; Approach B not auto-approved; Avg Cost vs FIFO unselected)* | `MATHEMATICALLY_VERIFIED` (Zero double-counting & FWER math) | 288-bar candidate is provisional, not validated optimum (`ISS_04: CLAIMED_ONLY`); `{72,144,288,576}` sweep unrun (`ISS_05: NOT_VERIFIED`); runtime accounting code `NOT_VERIFIED` (`ISS_10`). | `DEC_01`, `DEC_02`, `DEC_03`, `DEC_06` | `DEC_05` | `PENDING_HUMAN_DECISION` |
| **DEC_05** | Portfolio Concurrency & Risk Policy | **Opt 1:** Fixed Gross Exposure Cap<br>**Opt 2:** Risk-Budget Sizing<br>**Opt 3:** Combined Cap & Stop-Risk Budget | **Structured Choice (Opt 1, 2, or 3)** *(Strictly decoupled from Approach A/B)* | `SOURCE_VERIFIED` (Exposure vs leverage definitions) | Stress correlation matrix is `NOT_VERIFIED` (`ISS_08`); 30% cap denominator `REQUIRES_HUMAN_CLARIFICATION`; stop loss $\neq$ max loss. | `DEC_01`, `DEC_02`, `DEC_03`, `DEC_04`, `DEC_06` | None (Terminal) | `PENDING_HUMAN_DECISION` |
| **DEC_06** | XMRUSDT Research & Portfolio Scope | **Opt 1:** Full primary inclusion<br>**Opt 2:** Complete elimination<br>**Opt 3:** Three-Tier Policy (Preserve, Appendix, Exclude from primary) | **Option 3 (Three-Tier Policy)** | `SOURCE_VERIFIED` (83,863 vs 316,500 candles; 73.5% gap) | XMR has only 9.5 months (Fold 5) of history; cannot test multi-year stability. | None (Foundational) | `DEC_04.6` ($K$ joint input), `DEC_05` | `PENDING_HUMAN_DECISION` |

---

## 5. DECISION DEPENDENCY ANALYSIS & RATIONAL SEQUENCE

### 5.1 Explicit Evaluation of Required Dependency Links
Based on [QUANTUM_PHASE_5_5_CROSS_DECISION_DEPENDENCIES.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_CROSS_DECISION_DEPENDENCIES.md) and the reconciled errata, each dependency link is evaluated below, distinguishing **Hard Technical/Mathematical Dependencies** from **Recommended Governance Sequencing**:

1. **DEC_01 vs. DEC_02 (`Hard Structural Dependency: DEC_01 -> DEC_02`):**
   - `DEC_01` does **not** depend on `DEC_02`. Rather, `DEC_02` depends on `DEC_01`: the supervisor must first define what a trade execution is (`DEC_01`: re-anchored symmetric barriers vs. custom downstream strategy) before deciding whether that execution mechanism is authorized for Long-Only, Short-Only, or Bidirectional trading (`DEC_02`).
2. **DEC_02 vs. DEC_04 through $K$ (`Joint Specification Dependency: {DEC_02, DEC_06, DEC_04.6} -> K`):**
   - The confirmatory hypothesis family size $K$ in `DEC_04.6` is **not** an automatic $1\times$, $2\times$, or $3\times$ multiplication based solely on whether `DEC_02` selects Long-only, Short-only, or Bidirectional execution. Instead, $K$ depends jointly on five explicit specification choices: (1) the number of assets in the primary universe (`DEC_06`: 10 vs. 11), (2) whether Long and Short are evaluated as separate confirmatory hypotheses, (3) whether Combined is evaluated as an independent confirmatory hypothesis, (4) whether the primary estimand is asset-level or portfolio-level, and (5) which tests are designated as confirmatory gates vs. exploratory diagnostics. Conditional examples ($K = 10/11$, $K = 20/22$, $K = 30/33$, and $K = 1$) illustrate specific combinations of these choices rather than a pre-approved multiplicity family. Furthermore, mandatory directional reporting is strictly separated from execution authorization.
3. **DEC_03 vs. Funding Data and Settlement Conventions (`Hard Evidentiary Dependency -> DEC_03 -> DEC_04/05`):**
   - Because local canonical datasets lack historical funding rates (`ISS_09: FUNDING_DATA_UNAVAILABLE`) and AsterDEX boundary fill rules are unverified (`ISS_01: NOT_VERIFIED`), `DEC_03` cannot rely on empirical funding series. It depends directly on human authorization of parametric sensitivity inputs and the `EXPLICIT_SETTLEMENT_TIMING_MODELING_CONVENTION`, which then feed net return calculations in `DEC_04` and `DEC_05`.
4. **DEC_04 Dependency on DEC_02 and DEC_06 (`Hard Mathematical Dependency: {DEC_01, DEC_02, DEC_03, DEC_06} -> DEC_04`):**
   - `DEC_04` is a convergence node of seven independent subdecisions (`DEC_04.1` through `DEC_04.7`). Its statistical multiplicity hurdle ($\alpha / (K - i + 1)$ in `DEC_04.6`) is determined jointly by `DEC_06` (10 vs. 11 assets), `DEC_02` (authorized execution directions), and the supervisor's confirmatory vs. exploratory estimand designation (`DEC_04.6`), while its net return series ($R_{\text{net}}$) requires the barrier mechanics of `DEC_01` and financing cash flows of `DEC_03`.
5. **DEC_05 Dependency on Cross-Asset Correlation and Exposure Analysis (`Hard Risk Dependency: {DEC_01, DEC_02, DEC_04, DEC_06, ISS_08} -> DEC_05`):**
   - `DEC_05` depends on `DEC_01` for per-trade stop distance ($1.5\sigma_t$), `DEC_02` for whether simultaneous opposing positions can net or stack, `DEC_06` for whether maximum concurrent positions are 10 or 11, and `ISS_08` (correlation stress analysis) to bound joint drawdown when multiple positions hit or gap through stops simultaneously.
6. **DEC_06 Dependency on Hypothesis Family Size and Universe Definition (`Hard Sizing Dependency: DEC_06 -> DEC_04 & DEC_05`):**
   - `DEC_06` is an independent upstream universe decision driven by the verified candle disparity ($83,863$ vs. $316,500$). Once `DEC_06` fixes the primary universe at $N_{\text{assets}} \in \{10, 11\}$, that integer propagates downstream into `DEC_04.6` (as the asset dimension of $K$) and `DEC_05` (fleet concurrency cap).

### 5.2 Pairwise Dependency Matrix (6x6)

Rows represent the **Upstream (Impacting) Decision**; columns represent the **Downstream (Impacted) Decision**.

| Upstream \ Downstream | **DEC_01** (Architecture) | **DEC_02** (Direction) | **DEC_03** (Funding) | **DEC_04** (Cost & Stats) | **DEC_05** (Portfolio Risk) | **DEC_06** (XMR Scope) |
|---|---|---|---|---|---|---|
| **DEC_01** (Architecture) | -- | **HARD:** Defines trade exit mechanics for L/S signals | None | **HARD:** Defines primary economic estimand | **HARD:** Defines $1.5\sigma_t$ stop distance for risk sizing | None |
| **DEC_02** (Direction) | None | -- | None | **HARD:** Joint input into $K$ (`DEC_04.6`) alongside estimand & confirmatory vs exploratory rules | **HARD:** Determines L/S concurrency & exposure stacking | None |
| **DEC_03** (Funding) | None | Informational (L vs S carry drag) | -- | **HARD:** Enters net return $R_{\text{net}}$ in Gates 1-3 | **HARD:** Enters realized loss $L_{\text{realized}}$ | None |
| **DEC_04** (Cost & Stats) | None | None | None | -- | **RECOMMENDED ORDER:** Determines which specialists qualify for portfolio | None |
| **DEC_05** (Portfolio Risk) | None | None | None | Informational (if $K=1$ portfolio estimand is chosen) | -- | None |
| **DEC_06** (XMR Scope) | None | None | None | **HARD:** Sets base asset count (10 vs 11) in $K$ (`DEC_04.6`) and MBB matrix | **HARD:** Sets max concurrent specialists (10 vs 11) | -- |

### 5.3 Rational Decision Sequence
- **Tier I (Independent Foundational Decisions - Can Be Decided Immediately and in Any Order Among Themselves):**
  - **Step 1: `DEC_01` (Barrier Execution Architecture)**
  - **Step 2: `DEC_06` (XMR Research & Portfolio Scope)**
  - **Step 3: `DEC_03` (Funding Rate Model & Settlement Convention)**
- **Tier II (Intermediate Scope Decision - Requires `DEC_01`):**
  - **Step 4: `DEC_02` (Directional Trading Scope)**
- **Tier III (Convergent Statistical & Risk Decisions - Require Tiers I & II):**
  - **Step 5: `DEC_04` (Cost Scenarios, Partial-Fill Cost Basis, Bootstrap Design & Hypothesis Family $K$)**
  - **Step 6: `DEC_05` (Portfolio Concurrency, Exposure Denominator & Risk Policy)**

---

## 6. AGGRESSIVE TRADING RESEARCH OBJECTIVE & MANDATORY REPORTING

As preserved in [QUANTUM_PHASE_5_5_FINAL_CLOSURE_ADDENDUM.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_CLOSURE_ADDENDUM.md) (Section 4), the future backtesting framework must evaluate high-activity algorithmic viability under the following strict research requirements:

### 6.1 Initial Research Target & Activity Classifications
- **Initial Aggressive Research Target:** **`600 COMPLETED TRADES PER ASSET PER YEAR`**
- **Annual Completed Trade Frequency Classifications (Per Asset, Per Year):**
  - **Below 100 trades/year:** `LOW_ACTIVITY`
  - **100 to 299 trades/year:** `MODERATE_ACTIVITY`
  - **300 to 599 trades/year:** `ACTIVE`
  - **600 to 1,199 trades/year:** `AGGRESSIVE` (Target research regime)
  - **1,200 or more trades/year:** `HIGH_FREQUENCY`

### 6.2 Why Trade Frequency Alone Cannot Establish Profitability
Trade frequency is a descriptive activity classification, **never** a proof of economic edge:
1. **Linear Accumulation of Transaction Friction:** Every completed round-trip trade incurs maker/taker exchange fees, bid-ask half-spreads, and execution deviation ($C_{\text{fees}} + C_{\text{exec,total}}$). At 600 trades per asset per year under a 15 bps round-trip cost scenario, a specialist must overcome **9,000 bps (90.0%) of cumulative annual gross notional cost drag** just to break even.
2. **Expectancy Sign Dominance:** By the Law of Large Numbers, if net expectancy per trade is negative ($\mathbb{E}[\text{PnL}_{\text{net}}] < 0$), increasing trade frequency from 100 to 600+ trades per year **accelerates capital destruction** and reduces the probability of surviving drawdown limits.
3. **Prohibition on Frequency Optimization:** Thresholds ($\tau$) must never be lowered merely to inflate trade counts into the `AGGRESSIVE` tier if doing so degrades net expectancy below zero. A high trade count with negative net expectancy must automatically fail Phase 5.5 economic validation.

### 6.3 The 12 Required Backtesting Reporting Metrics (`12_REQUIRED_BACKTESTING_REPORTING_METRICS`)
When Phase 5.5 backtesting is eventually authorized, the engine must report all 12 metrics below, **disaggregated separately by asset, calendar year, strategy, direction (Long, Short, Combined), and market regime** (aggregate 11-asset totals must never be used to mask inactive assets or weak annual periods):
1. **Monthly trade-count distribution.**
2. **Zero-trade months.**
3. **Active trading days.**
4. **Average holding duration.**
5. **Net expectancy per trade** ($\mathbb{E}[\text{PnL}_{\text{net}}]$).
6. **Net PnL after fees, spread, slippage, and funding.**
7. **Profit factor.**
8. **Maximum drawdown.**
9. **Risk-adjusted returns** (Sharpe, Sortino, Calmar ratios).
10. **Transaction-cost drag** (total friction as a percentage of gross profit).
11. **PnL concentration** (fraction of net PnL generated by top 5% of trades).
12. **Annual out-of-sample stability.**

*Governance Boundary:* Recording this requirement does **not** authorize backtesting now (`Economic Backtesting = NOT_STARTED`).

---

## 7. FINAL EXECUTIVE SUMMARY & READINESS ASSESSMENT

### 7.1 Decision Readiness Categorization
Rather than forcing all six decisions into an artificially uniform state, the decisions are categorized by their evidentiary maturity:

1. **Decisions Ready for Immediate Informed Human Consideration (Complete Structural & Dataset Evidence):**
   - **`DEC_01` (Barrier Execution Architecture):** All architectural tradeoffs between Track 1 (close-anchored), Track 2 (re-anchored at $\text{open}[i+1]$), and Track 3 (downstream strategy) are fully specified (`SOURCE_VERIFIED`). The supervisor can decide immediately provided the estimand caveat (`ISS_06`) is acknowledged.
   - **`DEC_06` (XMR Research & Portfolio Scope):** The dataset coverage gap ($83,863$ vs. $316,500$ candles) is exact (`SOURCE_VERIFIED`). The supervisor can select among Options 1, 2, or 3 immediately.
   - **`DEC_02` (Directional Trading Scope):** Directional fee asymmetry ($14.89$ vs. $15.11$ bps) and reporting mandates are fully specified (`MATHEMATICALLY_VERIFIED`). The supervisor can select the permitted execution scope once `DEC_01` is chosen.

2. **Decisions Lacking Critical Empirical Evidence (Requiring Explicit Assumption / Convention Sign-Off):**
   - **`DEC_03` (Funding Rate Model):** Lacks historical funding rate series (`ISS_09: FUNDING_DATA_UNAVAILABLE`) and lacks official AsterDEX verification of the `08:00:00.000 UTC` boundary fill rule (`ISS_01: NOT_VERIFIED`). Approving `DEC_03` requires explicitly accepting synthetic parametric scenarios and the `EXPLICIT_SETTLEMENT_TIMING_MODELING_CONVENTION`.
   - **`DEC_04` (Cost Scenarios & Statistical Acceptance):** Lacks empirical autocorrelation validation of the 288-bar candidate block length (`ISS_04: CLAIMED_ONLY`, `ISS_05: NOT_VERIFIED`), lacks runtime code verification of the simulation accounting engine (`ISS_10: NOT_VERIFIED`), and requires selecting between **Average Cost Basis** and **FIFO** for partial fills. Approving `DEC_04` can only be done as a `PROVISIONALLY_APPROVED_RESEARCH_SPECIFICATION` contingent on resolving `ISS_10` before full fleet execution.
   - **`DEC_05` (Portfolio Concurrency & Leverage):** Lacks an empirical cross-asset stress correlation matrix (`ISS_08: NOT_VERIFIED`) and requires human clarification of the exposure cap denominator (`REQUIRES_HUMAN_CLARIFICATION`).

### 7.2 Summary of Direct Execution Blockers vs. Methodological Limitations
- **Direct Execution Blockers (6 Issues + 1 Specification Choice + 6 Human Decisions):**
  1. **`ISS_01` (`NOT_VERIFIED`, `OPEN`):** AsterDEX `08:00:00.000 UTC` funding boundary eligibility rule is unverified; requires supervisor sign-off on `EXPLICIT_SETTLEMENT_TIMING_MODELING_CONVENTION` or venue confirmation.
  2. **`ISS_04` (`CLAIMED_ONLY`, `OPEN`):** 288-bar MBB is a candidate methodology, not validated optimal; requires supervisor provisional approval in `DEC_04`.
  3. **`ISS_07` (`MATHEMATICALLY_VERIFIED`, `OPEN`):** Confirmatory hypothesis family size $K \in \{1, 10, 11, 20, 22, 30, 33\}$ is blocked awaiting human sign-off on `DEC_02`, `DEC_04`, and `DEC_06`.
  4. **`ISS_08` (`NOT_VERIFIED`, `OPEN`):** Cross-asset stress correlation is unquantified; blocks portfolio concurrency deployment until `DEC_05` option and denominator are chosen.
  5. **`ISS_09` (`SOURCE_VERIFIED`, `OPEN`):** Historical funding data are absent (`FUNDING_DATA_UNAVAILABLE`); blocks execution until `DEC_03` parametric sweep is authorized.
  6. **`ISS_10` (`NOT_VERIFIED`, `OPEN`):** Runtime simulation accounting code is unverified; blocks full fleet backtesting until unit tests of the runtime accounting engine pass (once backtesting code execution is authorized).
  7. **Partial-Fill Cost-Basis Dependency (`PENDING_HUMAN_DECISION`):** Selection between Average Cost Basis and FIFO for partial exits (`Task B` of Closure Addendum).
- **Supporting Methodological & Informational Limitations (Non-Blocking for Launch, Mandatory for Reporting):**
  1. **`ISS_05` (`NOT_VERIFIED`, `OPEN` - Diagnostic Limitation):** Block-length sensitivity sweep across $b \in \{72, 144, 288, 576\}$ bars must be executed and reported as a mandatory diagnostic during Phase 5.5.
  2. **`ISS_11` (`NOT_VERIFIED` for historical OS access / `METADATA_VERIFIED` for 33 partition boundaries / `23_MANIFESTED_ARTIFACTS_VERIFIED` - Informational Limitation):** Historical OS-level file read access prior to this audit cannot be disproven via Git or SHA-256 hashes.
  3. **Full Unit Test Suite Limitation (`FULL_UNIT_SUITE_NOT_VERIFIED`):** While 17 dedicated dossier tests and 372 filtered Phase 5 tests pass with exit code `0`, the complete 562-test repository suite experiences a Python 3.13 interpreter shutdown hang (`threading._shutdown()`) in legacy non-Phase-5 tests.

### 7.3 Audit Report of Residual Contradictions Across Source Documents
In accordance with Section 3 (*"If source documents conflict, report the conflict instead of silently resolving it"*), four legacy phrasing discrepancies exist between the earlier Revision 1.2 baseline documents and the superseding Final Governance Errata / Final Closure Addendum (preserved untouched to maintain historical audit traceability):

| Discrepancy ID | Earlier Revision 1.2 Baseline Document | Superseding Errata / Closure Addendum Document | Nature of Discrepancy & Authoritative Resolution |
|---|---|---|---|
| **CONFLICT_01** | [QUANTUM_PHASE_5_5_FINAL_HUMAN_DECISION_WORKSHEET.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_HUMAN_DECISION_WORKSHEET.md) (Line 105) & [QUANTUM_PHASE_5_5_CROSS_DECISION_DEPENDENCIES.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_CROSS_DECISION_DEPENDENCIES.md) (Line 65) | [QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md) (Section 4) & [QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md) (Line 21) | The unexecuted worksheet and dependency diagram still mention "Approach B (Signed Execution Deviation)" inside the `DEC_05` recommendation text. The Errata and Master Status explicitly decoupled Approach A/B into the technical execution-cost accounting specification (`DEC_04`) so that `DEC_05` addresses pure portfolio risk policy only. |
| **CONFLICT_02** | [QUANTUM_PHASE_5_5_FINAL_HUMAN_DECISION_WORKSHEET.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_HUMAN_DECISION_WORKSHEET.md) (Line 46) | [QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md) (Line 18) & [QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md) (Section 5) | The worksheet lists `Option 3 (Bidirectional Execution)` as the recommended option for `DEC_02`, whereas the Master Status and Errata refined this to a neutral structured choice among Options 1, 2, or 3 with mandatory disaggregated reporting across all options so bidirectional execution is not silently preselected. |
| **CONFLICT_03** | [QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md) (Lines 70-73) & [QUANTUM_PHASE_5_5_UNRESOLVED_ISSUE_REGISTER.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_UNRESOLVED_ISSUE_REGISTER.md) (Line 17) | [QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md) (Section 8.1) | Revision 1.2 referred to excluding `08:00:00.000 UTC` fills from the `08:00:00` funding settlement as a "conservative modeling assumption." The Errata proved mathematically that exclusion is optimistic when the trader pays funding, replacing the term with `EXPLICIT_SETTLEMENT_TIMING_MODELING_CONVENTION`. |
| **CONFLICT_04** | [QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md) (Lines 150, 174) | [QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md) (Sections 6 & 7) & [QUANTUM_PHASE_5_5_FINAL_CLOSURE_ADDENDUM.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_CLOSURE_ADDENDUM.md) (Section 3) | Revision 1.2 wrote a single-leg exit deviation formula $C_{\text{exec\_dev}} = Q(-d)(P_{\text{exec}} - P_{\text{ref}})$. The Errata generalized this to the symmetric two-legged entry and exit formulation $C_{\text{exec,total}} = C_{\text{exec,entry}} + C_{\text{exec,exit}}$ and per-fill slice summation, while the Closure Addendum separated Average Cost Basis vs. FIFO as an open specification choice. |

### 7.4 Verification Audit & Root-Cause Explanation of Prior Exit Code `1`
To ensure complete audit transparency across verification logs, the prior execution log entry (`Ran Verify decision brief and run dossier tests · Exited with code 1`) was investigated and verified as follows:

1. **Exact Command Executed in Prior Failed Step (`2026-11-02T14:11:52+07:00`):**
   ```powershell
   python -c "from pathlib import Path; em = chr(0x2014); p = Path('docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_HUMAN_GOVERNANCE_DECISION_BRIEF.md'); txt = p.read_text(encoding='utf-8'); assert em not in txt, 'Em dash found!'; print(f'Verified {p.name}: {len(txt)} chars, ZERO em dashes.')" && python -m pytest tests/unit/test_phase5_5_governance_dossier.py -v
   ```
2. **Exact Output and Root Cause of Exit Code `1` (`VERIFIED`):**
   - **Shell Output:**
     `At line:1 char:293 ... && python -m pytest tests/unit/test_phase5_5_governance_dossier.py -v ... The token '&&' is not a valid statement separator in this version. CategoryInfo: ParserError: (:) [], ParentContainsErrorRecordException. FullyQualifiedErrorId: InvalidEndOfLine`
   - **Failure Cause:** The command was dispatched to Windows PowerShell 5.1, where `&&` is not a valid statement separator (PowerShell 5.1 requires `;` or separate invocations). The PowerShell parser rejected the command syntax before either `python` or `pytest` started. Neither the document validator nor the unit test suite failed. When re-executed immediately afterward (`2026-11-02T14:12:02+07:00`) using `;` instead of `&&`, both commands succeeded with exit code `0`.
3. **Disaggregated Verification Status Table:**
   | Verification Scope | Classification | Result & Evidence |
   |---|---|---|
   | **Document Validation Result** | `VERIFIED` | Standalone Python validator confirms zero em dashes (`\u2014`), presence of `NOT AN EXECUTABLE ECONOMIC ENTRY ANCHOR`, all 7 `DEC_04` subdecisions (`DEC_04.1` through `DEC_04.7`), `600 COMPLETED TRADES PER ASSET PER YEAR`, and `12_REQUIRED_BACKTESTING_REPORTING_METRICS` (Exit code `0`). |
   | **Dedicated Dossier Test Result** | `VERIFIED` | `python -m pytest tests/unit/test_phase5_5_governance_dossier.py -v` passes **17 / 17** tests with exit code `0`. |
   | **Filtered Phase 5 Test Result** | `REPORTED_ONLY` / `NOT_RUN` (current turn) | Previously verified at **372 / 372** passing in 1.71s (`exit code 0`) in the Final Errata Correction audit; not re-run in this documentation-only turn (`NOT_RUN`). |
   | **Full Unit-Suite Status** | `NOT_VERIFIED` / `NOT_RUN` | Classified as `NOT_VERIFIED` (`FULL_UNIT_SUITE_NOT_VERIFIED`) and `NOT_RUN` in this turn because `pytest tests/unit/` experiences a Python 3.13 interpreter shutdown hang (`threading._shutdown()`) in legacy non-Phase-5 tests (`test_app_lifecycle.py` / `test_freshness_alert_audit.py`). |
   | **Git Working-Tree Status** | `VERIFIED` | Verified via `git status --short` and `git diff`: zero tracked files modified; only `docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_HUMAN_GOVERNANCE_DECISION_BRIEF.md` is untracked (`??`), and `QUANTUM_PHASE_5_5_FINAL_HUMAN_DECISION_WORKSHEET.md` remains 100% untouched and unexecuted. |

---

## 8. IMMUTABLE GOVERNANCE STATUS

- **DEC_01 (Barrier Execution Architecture):** `PENDING_HUMAN_DECISION`
- **DEC_02 (Directional Trading Scope):** `PENDING_HUMAN_DECISION`
- **DEC_03 (Funding Rate Model):** `PENDING_HUMAN_DECISION`
- **DEC_04 (Cost Scenarios & Statistical Acceptance - Subdecisions `DEC_04.1` to `DEC_04.7`):** `PENDING_HUMAN_DECISION`
- **DEC_05 (Portfolio Concurrency & Leverage):** `PENDING_HUMAN_DECISION`
- **DEC_06 (XMR Research & Portfolio Scope):** `PENDING_HUMAN_DECISION`
- **Phase 5.5 Lifecycle Status:** `NOT_STARTED`
- **Phase 5.6 Lifecycle Status:** `NOT_AUTHORIZED`
- **Economic Backtesting Status:** `NOT_STARTED`
- **Prospective Holdout (`2026-11-01 00:00:00 UTC` to `2027-04-30 23:59:59.999 UTC`):** `STRICTLY_SEALED`
