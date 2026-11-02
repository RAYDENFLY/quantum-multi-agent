# QUANTUM PHASE 5.5: HUMAN GOVERNANCE DECISION WORKSHOP
## STAGE 1 (FOUNDATIONAL DECISION 1 OF 6) - `DEC_01: BARRIER EXECUTION ARCHITECTURE`

**Document Version:** 1.3.0-FINAL-RECONCILED
**Publication Timestamp:** 2026-11-02 16:30:00 UTC
**Workshop Mode:** READ_ONLY_DECISION_SUPPORT_ONLY
**Current Decision Under Review:** `DEC_01` (`PENDING_HUMAN_DECISION`)
**All Remaining Decisions (`DEC_02` through `DEC_06`):** `PENDING_HUMAN_DECISION`
**Lifecycle Status:** Phase 5.5 `NOT_STARTED` | Phase 5.6 `NOT_AUTHORIZED` | Economic Backtesting `NOT_STARTED` | Prospective Holdout `STRICTLY_SEALED`

**Authoritative References:**
- [QUANTUM_THREE_TRACK_METHODOLOGY_RECONCILIATION_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_THREE_TRACK_METHODOLOGY_RECONCILIATION_AUDIT.md)
- [QUANTUM_SEVEN_AGENT_ARCHITECTURE_AND_THREE_TRACK_EXPERIMENT_DESIGN.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_SEVEN_AGENT_ARCHITECTURE_AND_THREE_TRACK_EXPERIMENT_DESIGN.md)
- [QUANTUM_PHASE_5_5_HUMAN_GOVERNANCE_DECISION_BRIEF.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_HUMAN_GOVERNANCE_DECISION_BRIEF.md) (Section 3.1)
- [QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md)
- [QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md)
- [QUANTUM_PHASE_5_5_FINAL_CLOSURE_ADDENDUM.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_CLOSURE_ADDENDUM.md)
- [QUANTUM_PHASE_5_5_FINAL_HUMAN_DECISION_WORKSHEET.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_HUMAN_DECISION_WORKSHEET.md) (Section 2.1)
- [QUANTUM_PHASE_5_5_UNRESOLVED_ISSUE_REGISTER.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_UNRESOLVED_ISSUE_REGISTER.md) (`ISS_06`, `ISS_10`, `ISS_11`)

---

### 1. Exact Governance Question

Because feature computation and out-of-fold classifier inference at bar $i$ depend on $\text{close}[i]$ (which is only physically known at the completion of bar $i$), how should Phase 5.5 define the economic trade entry anchor and exit barrier structure relative to the original close-anchored triple-barrier predictive target (`Alternative A / Track 1`, `Alternative B / Track 2`, or `Alternative C / Track 3`)?

#### Three Distinct Approval Layers

To prevent premature research execution or scope creep, the governance architecture separates the evaluation lifecycle into **Three Distinct Approval Layers**:

1. **Layer 1: Methodology Direction Approval (Strict Scope of DEC_01)**
   - The Human Governance Supervisor determines the conceptual research methodology, track selection, and sequencing priority among Track 1, Track 2, and Track 3.
   - **DEC_01 strictly decides Layer 1 only.**
   - Approval of Layer 1 does **NOT** authorize writing backtesting engine production code, does **NOT** authorize executing simulation runs, and does **NOT** authorize Phase 5.6.
2. **Layer 2: Technical Design Approval (Specification Gate)**
   - The Human Governance Supervisor approves concrete technical specifications prior to any simulation implementation:
     - Backtest discrete-event engine architecture and simulated clock injection design.
     - Reference-price signed PnL accounting specification.
     - Execution assumptions document (slippage modeling, taker fee schedules, fill latency).
     - Parameter space boundaries and pre-registration manifests (for Track 3).
   - Approval of Layer 2 approves design specifications only; it does **NOT** authorize running backtests.
3. **Layer 3: Execution Authorization (Operational Gate)**
   - The formal authorization to run backtests against out-of-fold datasets.
   - Strictly contingent upon prior approval of Layer 1 (DEC_01), approval of Layer 2 specifications, and formal human resolution of downstream decisions:
     - `DEC_02`: Directional trading execution scope (Long-Only, Short-Only, Bidirectional).
     - `DEC_03`: Parametric funding rate vectors and stress scenarios.
     - `DEC_04`: Statistical validation protocol, hypothesis family size $K$, and block bootstrap parameters.
     - `DEC_05`: Portfolio accounting reference-price rules vs risk budgeting.
     - `DEC_06`: Asset universe scope (fleet aggregation with or without XMR).

---

### 2. Synthesis of Latest Methodology & Architecture Audit Findings

Before evaluating the alternatives, the following critical empirical facts established in the latest methodology and architecture audits must be recognized:

1. **Target Horizon Reconciliation (12 Bars / 60 Minutes):**
   - Source code ([`src/quantum/features/labeling.py:L39`](file:///d:/quantum-multi-agent/src/quantum/features/labeling.py#L39)), data contracts ([`src/quantum/ml/contracts.py:L40`](file:///d:/quantum-multi-agent/src/quantum/ml/contracts.py#L40)), and training manifests ([`artifacts/phase_5_3_2/fleet_summary/fleet_catalog.json`](file:///d:/quantum-multi-agent/artifacts/phase_5_3_2/fleet_summary/fleet_catalog.json)) verify that all 55 frozen Phase 5.3 models were trained on a **12-bar (60-minute)** horizon with `purged_samples: 12` and `embargo_samples: 24`.
   - The "288-bar" specification in prior narrative documents was a daily holding concept. Evaluating 12-bar frozen models against a 288-bar target is an invalid `TARGET_MISMATCH`.
2. **Estimand Separation for Track 2:**
   - Track 2 is NOT `TARGET_ALIGNED`. It is classified as `SIGNAL_COMPATIBLE_WITH_SEPARATE_ECONOMIC_ESTIMAND`.
   - Shifting the entry anchor to $\text{open}[i+1]$ alters the estimand from conditional probability $P(y \mid X)$ to realized financial payoff $\mathbb{E}[R_{\text{net}}]$. Frozen model probabilities are signal scores and cannot be assumed to be calibrated for the re-anchored economic outcome.
3. **Fold 5 OOS Status:**
   - Fold 5 is classified as `OOS_ELIGIBILITY_NOT_VERIFIED`.
   - Fold 5 test data was evaluated during Phase 5.3 ([`fold_5/metrics.json`](file:///d:/quantum-multi-agent/artifacts/phase_5_3_1/BTCUSDT/fold_5/metrics.json)) and concatenated into [`materialized_oof`](file:///d:/quantum-multi-agent/artifacts/phase_5_4/materialized_oof/). Because researcher exposure to Fold 5 metrics cannot be audited, Fold 5 is permitted for exploratory research but **STRICTLY PROHIBITED FOR CONFIRMATORY ALPHA CLAIMS**.
   - The prospective holdout (starting 2026-11-01) remains `STRICTLY_SEALED`.
4. **Epistemic Classification of Track 2 (Exploratory vs Confirmatory):**
   - Track 2 cannot be claimed to have demonstrated a "confirmatory economic edge" or to be "valid for baseline economic edge".
   - Confirmatory economic claims require:
     1. Formal pre-registration of the evaluation protocol and primary financial estimand.
     2. An approved hypothesis family size $K$ with family-wise error rate control.
     3. Empirically validated transaction cost, slippage, and funding drag models.
     4. Uncompromised, unexposed out-of-sample data.
   - Because no economic backtest has ever been executed in the repository (`Phase 5.5 = NOT_STARTED`), Track 2 is classified strictly as:
     `ELIGIBLE_FOR_EXPLORATORY_ECONOMIC_EVALUATION_SUBJECT_TO_GOVERNANCE_APPROVAL`.
5. **Agent Architecture Implementation Reality:**
   - [`BankerAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/banker.py#L24) is an in-trade order/stop lifecycle FSM, NOT a portfolio cash or treasury manager.
   - [`PipelineOrchestrator`](file:///d:/quantum-multi-agent/src/quantum/agents/orchestrator.py#L51) does not invoke `BankerAgent`, and ML agents currently output placeholder probabilities. A dedicated discrete-event backtest runner and accounting engine must be developed before economic simulation can execute.

---

### 3. Comprehensive Analysis of the Three Alternatives

#### Alternative A (Track 1: Predictive Benchmark on Frozen Target)

```text
[Candle i Close] ---> [Inference: P(y | X_i)] ---> [Evaluate vs close[i] * (1 +/- 1.5 sigma_t) over 12 bars]
```

1. **What Exactly Is Being Approved (Layer 1 Scope):**
   - Authorizes formal compilation and reporting of out-of-fold statistical classification metrics (Balanced Accuracy, ROC-AUC, Brier score, ECE calibration error, and AURCC) against the exact 12-bar training target.
   - Utilizes already materialized out-of-fold predictions from [`artifacts/phase_5_4/materialized_oof/`](file:///d:/quantum-multi-agent/artifacts/phase_5_4/materialized_oof/).
2. **What Is Not Being Approved:**
   - Does NOT authorize trade execution simulation, backtesting, or financial PnL calculation.
   - Does NOT permit using $\text{close}[i]$ as an executable trade entry anchor (`NOT AN EXECUTABLE ECONOMIC ENTRY ANCHOR`).
3. **Technical Consequences:**
   - Lowest engineering complexity. Requires zero new execution simulation code.
   - Operates entirely on frozen Phase 5.4 Parquet datasets using scikit-learn evaluation routines ([`src/quantum/ml/evaluation.py`](file:///d:/quantum-multi-agent/src/quantum/ml/evaluation.py)).
4. **Statistical Consequences:**
   - `TARGET_ALIGNED`. Perfectly preserves the statistical validity of the training estimand ($P(y \mid X)$).
   - Introduces **`ZERO ADDITIONAL STRATEGY-TUNING HYPERPARAMETERS`**.
   - Free of trade execution assumptions.
5. **Economic Consequences:**
   - Generates zero economic return, cash flow, or drawdown data.
   - Provides pure information on model predictive skill, establishing whether directional edge exists prior to transaction frictions.
6. **Required Infrastructure:**
   - Existing and verified. Uses [`ModelEvaluationContract`](file:///d:/quantum-multi-agent/src/quantum/ml/evaluation.py#L21) and Parquet readers.
7. **Dependencies on DEC_02 through DEC_06:**
   - Independent of DEC_02 (directional execution), DEC_03 (funding), and DEC_05 (execution accounting).
   - Informs DEC_04 (baseline statistical power) and DEC_06 (identifies data length constraints for XMR).
8. **Remaining Evidence Gaps:**
   - Fleet-wide consolidated reporting table across all 11 assets has not yet been compiled under the Phase 5.5 dossier.
9. **Strongest Argument Against Alternative A:**
   - Does not answer whether the quantitative model can generate profit in the real world after taker fees, slippage, and opening gaps. Stopping at Alternative A leaves the economic viability of QUANTUM completely unanswered.
10. **Non-Binding Engineering Recommendation:**
    - Essential baseline prerequisite. Must be formally reported as Group A Predictive Performance, but should not be the sole deliverable of Phase 5.5.

---

#### Alternative B (Track 2: Re-Anchored Economic Evaluation at open[i+1])

```text
[Candle i Close] ---> [Inference] ---> [Fill at open[i+1]] ---> [Evaluate vs open[i+1] * (1 +/- 1.5 sigma_t) over 12 bars]
```

1. **What Exactly Is Being Approved (Layer 1 Scope):**
   - Authorizes the conceptual methodology for a causal, discrete-event execution simulation entering positions at $P_{\text{entry,ref}} = \text{open}[i+1]$ with symmetric $\pm 1.5\sigma_t$ barriers over a **12-bar holding horizon** (matching the frozen 60-minute Phase 5.3 target horizon).
   - Establishes the evaluation of net economic expectancy under fixed notional sizing across standardized transaction cost tiers (0, 15, 20, 30 bps) and parametric funding scenarios.
   - Enforces **`ZERO ADDITIONAL STRATEGY-TUNING HYPERPARAMETERS`** beyond the fixed entry timing rule and symmetric barrier geometry.
2. **What Is Not Being Approved:**
   - Does **NOT** authorize backtest engine code implementation (Layer 2) or running backtests (Layer 3).
   - Does **NOT** authorize dynamic stop-loss tuning, asymmetric risk-reward optimization, trailing stops, or partial profit taking.
   - Does **NOT** retrospectively prove the economic payoff of the original close-anchored training label (`ISS_06`).
   - Does **NOT** authorize live exchange trading or capital deployment.
3. **Technical Consequences:**
   - Requires constructing a dedicated bar-by-bar historical backtesting engine (`src/quantum/backtesting/engine.py`) and reference-price accounting module (`src/quantum/backtesting/accounting.py`) under Layer 2 specifications.
   - Requires implementing simulated clock injection (`eval_timestamp_ms`) in [`RiskAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/risk.py#L80) to prevent wall-clock staleness rejections during historical replays.
4. **Statistical Consequences:**
   - Classified as `SIGNAL_COMPATIBLE_WITH_SEPARATE_ECONOMIC_ESTIMAND`.
   - Evaluates a separate economic estimand: $\mathbb{E}[R_{\text{net}} \mid \text{open}[i+1]]$.
   - Introduces **`ZERO ADDITIONAL STRATEGY-TUNING HYPERPARAMETERS`**, preventing post-hoc strategy curve-fitting across validation folds.
   - *Methodological Clarification:* Having zero additional strategy-tuning hyperparameters eliminates post-hoc strategy curve-fitting, but does **NOT** eliminate statistical estimation uncertainty, sampling variance, model selection bias from upstream Phase 5.3 architecture/feature choices, or multiple-testing risks across broader governance choices.
5. **Economic Consequences & Break-Even Mathematics:**
   - Directly measures opening gap risk ($\text{open}[i+1] - \text{close}[i]$), taker fee drag, and execution slippage.
   - Evaluates whether the directional signal survives the theoretical break-even win rate hurdle.
   - **Break-Even Win Rate Derivation:**
     - Under symmetric barriers with gross winning return $G = 150$ bps ($+1.5\%$) and gross losing return $L = 150$ bps ($-1.5\%$), let round-trip transaction cost be $C$ bps.
     - Expected net return per trade: $\mathbb{E}[R_{\text{net}}] = p \cdot (G - C) - (1 - p) \cdot (L + C) = p \cdot (G + L) - (L + C)$.
     - Setting $\mathbb{E}[R_{\text{net}}] = 0$ yields the break-even win rate formula:
       $$p_{\text{BE}} = \frac{L + C}{G + L} = \frac{150 + C}{300}$$
     - Required break-even win rates across standardized cost tiers:
       - **$C = 0$ bps:** $p_{\text{BE}} = \frac{150}{300} = 50.00\%$ (frictionless baseline)
       - **$C = 15$ bps:** $p_{\text{BE}} = \frac{165}{300} = 55.00\%$ (institutional VIP tier)
       - **$C = 20$ bps:** $p_{\text{BE}} = \frac{170}{300} = 56.67\%$ (standard retail taker tier)
       - **$C = 30$ bps:** $p_{\text{BE}} = \frac{180}{300} = 60.00\%$ (stressed slippage tier)
     - **Funding Rate Impact:**
       - Under the 12-bar horizon (60 minutes), a trade crosses at most one 8-hour perpetual settlement timestamp.
       - A parametric funding rate $f \in \{-3, -1, 0, +1, +3\}$ bps shifts the net payoff by $-f$ bps, altering the break-even win rate by $\Delta p_{\text{BE}} = \frac{f}{300} = \pm 0.33\%$ to $\pm 1.00\%$.
6. **Required Infrastructure:**
   - Layer 2 engineering required: Backtesting event simulator, signed PnL accounting engine, clock injection specification.
7. **Dependencies on DEC_02 through DEC_06:**
   - Hard dependency on DEC_02 (authorizes Long-only, Short-only, or Bidirectional execution).
   - Hard dependency on DEC_03 (defines parametric funding rates $-3, -1, 0, +1, +3$ bps).
   - Hard dependency on DEC_04 (defines confirmatory family $K$ and resampling block length).
   - Hard dependency on DEC_05 (governs reference-price accounting vs portfolio risk policy).
   - Hard dependency on DEC_06 (governs inclusion of XMR in fleet aggregation).
8. **Remaining Evidence Gaps:**
   - Empirical distribution of $|\text{open}[i+1] - \text{close}[i]| / \sigma_t$ is unmeasured (`NOT_VERIFIED`).
   - Actual net expectancy under re-anchored execution is unknown (`Phase 5.5 = NOT_STARTED`).
9. **Strongest Argument Against Alternative B:**
   - If market prices experience immediate mean-reversion or momentum exhaustion during the inter-bar gap, entering at $\text{open}[i+1]$ with symmetric $1.5\sigma_t$ brackets may systematically underperform, falsely rejecting a skilled predictive model that could have succeeded with asymmetric or adaptive trade management.
10. **Non-Binding Engineering Recommendation:**
    - **RECOMMENDED PRIMARY CHOICE FOR LAYER 1.** Provides an unconfounded, zero-tuning benchmark to determine whether the frozen signal possesses baseline economic viability before introducing strategy complexity. Classified as `ELIGIBLE_FOR_EXPLORATORY_ECONOMIC_EVALUATION_SUBJECT_TO_GOVERNANCE_APPROVAL`.

---

#### Alternative C (Track 3: Independent Downstream Strategy Research)

```text
[Model Probability p_1] ---> [Raw Alpha Ranking] ---> [Optimized Entry tau] ---> [Asymmetric TP/SL & Trailing FSM]
```

1. **What Exactly Is Being Approved (Layer 1 Scope):**
   - Authorizes downstream algorithmic strategy research treating frozen model probabilities as raw alpha ranking scores.
   - Establishes exploratory research into entry thresholds ($\tau_{\text{entry}}$), asymmetric stop/target multiples ($k_{\text{SL}}, R_{\text{TP1}}, R_{\text{TP2}}$), partial profit fractions ($f_{\text{TP1}}$), breakeven stop ratchets, and dynamic trailing stops ([`BankerAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/banker.py#L136-L143)).
2. **What Is Not Being Approved:**
   - Does **NOT** authorize retraining, fine-tuning, or altering base Phase 5.3 models.
   - Does **NOT** authorize using Fold 5 for parameter tuning.
   - Does **NOT** authorize confirmatory alpha claims based on Fold 5 (classified as `OOS_ELIGIBILITY_NOT_VERIFIED`).
   - Does **NOT** access or unseal the prospective holdout (`STRICTLY_SEALED`).
   - Does **NOT** authorize Layer 2 optimization harness code or Layer 3 grid execution until pre-registration manifests are approved.
3. **Technical Consequences:**
   - Highest engineering complexity. Requires building a full walk-forward hyperparameter optimization harness, integrating [`SniperAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/sniper.py#L22) and [`BankerAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/banker.py#L24) FSMs into the backtest engine, and implementing strict parameter freeze mechanics.
4. **Statistical Consequences:**
   - Introduces a high-dimensional strategy hyperparameter space. An unconstrained grid search across candidate ranges produces **up to 14,400 parameter configurations**, creating severe data-mining and multiple-testing risks.
   - Consumes Folds 1 through 4 for parameter optimization, leaving Fold 5 restricted strictly to exploratory profiling (`OOS_ELIGIBILITY_NOT_VERIFIED`).
   - Requires formal multiplicity correction under a conditional hypothesis family $K_{\text{Track3}}$ framework (see Section 5.2).
5. **Economic Consequences:**
   - Maximizes potential risk-adjusted performance by engineering asymmetric payoff profiles (e.g. cutting losses at $1.0\sigma$ while capturing $2.5\sigma$ runners).
   - Carries severe risk of historical curve-fitting that degrades sharply out-of-sample.
6. **Required Infrastructure:**
   - Optimization search harness, Banker FSM integration, parameter manifest freeze manager, Holm-Bonferroni correction engine.
7. **Dependencies on DEC_02 through DEC_06:**
   - Hard dependencies on DEC_02, DEC_03, DEC_04, DEC_05, and DEC_06.
   - Directly governs the definition of multiple-testing family $K_{\text{Track3}}$.
8. **Remaining Evidence Gaps:**
   - Strategy search space has not been pre-registered.
   - Interaction between model score decay and dynamic trailing stops is unmodeled in code.
9. **Strongest Argument Against Alternative C:**
   - Severe risk of strategy curve-fitting. If an optimized strategy produces positive returns, it is impossible to determine whether the profit stems from genuine ML predictive alpha or post-hoc heuristic exploitation of historical market regimes.
10. **Non-Binding Engineering Recommendation:**
    - Secondary/conditional choice. Should be authorized as an exploratory follow-up research track only after Track 2 establishes the baseline economic properties of the frozen signals.

---

### 4. Direct Comparison Matrix Across Alternatives

```text
+-----------------------------+------------------------------------+---------------------------------------------------------------+---------------------------------------+
| Evaluation Dimension        | Alternative A (Track 1)            | Alternative B (Track 2)                                       | Alternative C (Track 3)               |
+-----------------------------+------------------------------------+---------------------------------------------------------------+---------------------------------------+
| Target Alignment            | TARGET_ALIGNED (12 bars / 60 min)  | SIGNAL_COMPATIBLE_WITH_SEPARATE_ECONOMIC_ESTIMAND             | INDEPENDENT_ALPHA_SCORE               |
| Entry Reference Price       | close[i] (Non-executable)          | open[i+1] (Causal market fill)                                | open[i+1] or Limit (bid1/ask1)        |
| Exit Geometry               | Symmetric +/- 1.5 sigma            | Symmetric +/- 1.5 sigma                                       | Asymmetric TP/SL, Trailing, Ratchet   |
| Maximum Holding Horizon     | 12 bars (60 minutes)               | 12 bars (60 minutes)                                          | Provisional 6 to 48 bars              |
| Strategy Hyperparameters    | ZERO ADDITIONAL STRATEGY TUNING    | ZERO ADDITIONAL STRATEGY TUNING                               | High (Up to 14,400 grid states)       |
| Validation Sample Scope     | Concatenated OOF (All Folds)       | Concatenated OOF (All Folds)                                  | Folds 1-4 Tuning, Fold 5 Exploratory  |
| Claim Classification        | Valid for Statistical ML Skill     | ELIGIBLE_FOR_EXPLORATORY_ECONOMIC_EVALUATION_SUBJECT_TO_GOV...  | PROHIBITED on Fold 5 (Unverified OOS) |
| Primary Financial Output    | ROC-AUC, Brier, Calibration        | Net Expectancy (bps), Profit Factor, Drawdown                 | Sharpe Ratio, Alpha Spread vs Trk 2   |
| Approval Scope Boundary     | Layer 1: Report Existing OOF Only  | Layer 1: Direction Only (No code/execution authorized)        | Layer 1: Direction Only (Gated by Trk2)
| Implementation Status       | READY_FOR_HUMAN_REVIEW             | REQUIRES_INFRASTRUCTURE_DEVELOPMENT                           | REQUIRES_INFRASTRUCTURE_DEVELOPMENT   |
+-----------------------------+------------------------------------+---------------------------------------------------------------+---------------------------------------+
```

*Note on Claim Classification for Alternative B:* Full status is `ELIGIBLE_FOR_EXPLORATORY_ECONOMIC_EVALUATION_SUBJECT_TO_GOVERNANCE_APPROVAL`. Confirmatory economic edge claims are prohibited until formal pre-registration, hypothesis family $K$ approval, cost/funding validation, and uncompromised OOS data are fully satisfied.

---

### 5. Scope of Decision DEC_01 & Methodological Governance Framework

#### 5.1 The Three Approval Layers

DEC_01 operates strictly at **Layer 1 (Methodology Direction Approval)**. The boundaries of approval are defined as follows:

```text
+-----------------------------+----------------------------------+----------------------------------+----------------------------------+
| Approval Dimension          | Layer 1: Methodology Direction   | Layer 2: Technical Design        | Layer 3: Execution Authorization |
|                             | (Decided by DEC_01)              | (Subsequent Technical Review)    | (Final Operational Gate)         |
+-----------------------------+----------------------------------+----------------------------------+----------------------------------+
| What Is Approved            | Conceptual research track        | Technical specifications, engine | Running backtests against OOF    |
|                             | selection, priority, sequence    | design, accounting rules, bounds | datasets; generating PnL tables  |
| Code Implementation Rights  | NONE (No code development)       | Architecture specs ratified      | Implementation authorized        |
| Execution Rights            | NONE (No simulations run)        | NONE (No simulations run)        | Authorized under strict gates    |
| Dependencies                | Independent foundational choice  | Requires Layer 1 approval        | Requires Layers 1-2 & DEC_02-06  |
+-----------------------------+----------------------------------+----------------------------------+----------------------------------+
```

- **Under Alternative A:** Approves compiling and publishing out-of-fold predictive benchmark reporting from frozen Phase 5.4 Parquet datasets. Does not require Layer 2 engine specifications or Layer 3 execution authorization.
- **Under Alternative B:** Approves the conceptual methodology of re-anchored $\text{open}[i+1]$ evaluation as the primary economic benchmark. Does **NOT** authorize building backtest engine code (Layer 2) or running backtests (Layer 3), which remain gated by technical specifications and decisions DEC_02 through DEC_06.
- **Under Alternative C:** Approves exploratory downstream strategy research direction. Explicitly does **NOT** authorize building optimization harnesses (Layer 2) or executing hyperparameter grid evaluations (Layer 3) until Track 2 baseline properties are documented and pre-registration manifests are ratified.

#### 5.2 Hypothesis Family $K$ Multiplicity Framework for Track 3

Prior governance narrative documents suggested a universal formula $K_{\text{Track3}} = 11 \times N$. The latest methodology audit establishes that this formula is not universally valid and depends on four distinct structural parameters:

1. **Asset Universe Scope ($M$ Assets):**
   - $M = 11$ assets if the full Phase 5.3 fleet is evaluated.
   - $M = 10$ assets if XMR is excluded under `DEC_06` due to data length limitations (`ISS_10`).
2. **Directional Execution Scope ($D$ Modes):**
   - $D = 1$ if execution is strictly Long-Only or strictly Short-Only under `DEC_02`.
   - $D = 2$ if Long-Only and Short-Only strategies are disaggregated and tested as independent confirmatory hypotheses.
   - $D = 3$ if Long-Only, Short-Only, and Combined portfolio strategies are each tested as confirmatory hypotheses.
3. **Aggregation Level:**
   - **Portfolio-Level Estimand:** If the primary confirmatory hypothesis is evaluated on the pooled cross-sectional portfolio return, $K = N$ (or $D \times N$). Cross-asset pooling tests the global portfolio edge rather than 11 separate asset hypotheses.
   - **Asset-Level Estimands:** If each asset's strategy performance is tested independently for alpha, the hypothesis family multiplies across assets: $K = M \times D \times N$.
4. **Research Mode (Exploratory vs Confirmatory):**
   - **Exploratory Tuning (Folds 1-4):** Grid search across parameter states ($N$) is exploratory. Multiplicity correction is not required for in-sample discovery, but the total number of tested configurations must be documented to quantify search breadth.
   - **Confirmatory Validation:** Requires strict pre-registration of a sparse grid ($N \le 10$) and family-wise error rate control (Holm-Bonferroni or Benjamini-Hochberg FDR) across the ratified hypothesis family $K$.

```text
+-----------------------------+-------------------+-------------------+-------------------+-------------------+-----------------------------------+
| Configuration Mode          | Asset Scope ($M$) | Directional ($D$) | Grid States ($N$) | Family Size ($K$) | Primary FWER Hurdle (Bonferroni)  |
+-----------------------------+-------------------+-------------------+-------------------+-------------------+-----------------------------------+
| Portfolio-Level Pooled      | 10 or 11          | Combined ($D=1$)  | Pre-reg ($N \le 10$)| $K = N$           | alpha_adj = 0.05 / N              |
| Asset-Level, Long-Only      | 10 (ex-XMR)       | Long ($D=1$)      | Pre-reg ($N \le 10$)| $K = 10 * N$      | alpha_adj = 0.05 / (10 * N)       |
| Asset-Level, Long-Only      | 11 (Full Fleet)   | Long ($D=1$)      | Pre-reg ($N \le 10$)| $K = 11 * N$      | alpha_adj = 0.05 / (11 * N)       |
| Asset-Level, Disaggregated  | 10 (ex-XMR)       | Long/Short ($D=2$)| Pre-reg ($N \le 10$)| $K = 20 * N$      | alpha_adj = 0.05 / (20 * N)       |
| Asset-Level, Disaggregated  | 11 (Full Fleet)   | Long/Short ($D=2$)| Pre-reg ($N \le 10$)| $K = 22 * N$      | alpha_adj = 0.05 / (22 * N)       |
| Asset-Level, Full Triad     | 11 (Full Fleet)   | Triad ($D=3$)     | Pre-reg ($N \le 10$)| $K = 33 * N$      | alpha_adj = 0.05 / (33 * N)       |
+-----------------------------+-------------------+-------------------+-------------------+-------------------+-----------------------------------+
```

*Governance Constraint:* The binding hypothesis family $K_{\text{Track3}}$ cannot be finalized in DEC_01; it directly depends on decisions `DEC_02` (directional scope), `DEC_04` (statistical validation protocol), and `DEC_06` (asset universe).

#### 5.3 Decision Combinations

The human decision on DEC_01 does NOT require forced mutual exclusivity. The supervisor may choose:
- **Sequential Staged Authorization:** (e.g., compile Track 1 reporting immediately, authorize Layer 1 direction for Track 2 baseline, defer Track 3).
- **Conditional Authorization:** (e.g., authorize Track 2 baseline direction, and conditionally authorize Track 3 exploratory research only if Track 2 demonstrates non-negative gross expectancy).
- **Single Exclusive Track:** (e.g., authorize Track 1 reporting only and halt further backtest development).

---

### 6. Human Response Protocol

The Human Governance Supervisor is requested to review the alternatives and provide an explicit decision.

Please respond using one of the following four standardized governance actions:

```text
1. APPROVE: [Specify selected Alternative, operational scope, and Layer 1 boundaries]
   Examples:
   - "APPROVE: Alternative B as primary economic benchmark (Layer 1 direction only), with Alternative A compiled for predictive baseline; defer Alternative C"
   - "APPROVE: Alternative A reporting only; defer Alternative B and C until further review"
   - "APPROVE: Alternative B primary (Layer 1), with Alternative C authorized strictly for exploratory Folds 1-4 tuning contingent on Track 2 results"

2. REJECT: [Specify option rejected and technical/governance reason]
   Examples:
   - "REJECT: Alternative C due to multiple-testing data-mining risk and unverified Fold 5 status"
   - "REJECT: Alternative B due to opening gap concerns; require direct limit order modeling"

3. DEFER: [Specify reason for deferral and required trigger]
   Examples:
   - "DEFER: DEC_01 pending review of the completed backtesting engine design specification (Layer 2 draft)"
   - "DEFER: DEC_01 pending empirical measurement of opening gap distributions (|open[i+1] - close[i]| / sigma_t)"

4. REQUEST_MORE_EVIDENCE: [Specify exact empirical evidence or analysis required]
   Examples:
   - "REQUEST_MORE_EVIDENCE: Empirical distribution of opening gaps |open[i+1] - close[i]| / sigma_t across the 11 assets"
   - "REQUEST_MORE_EVIDENCE: Reconciled 12-bar out-of-fold predictive metrics table for all 11 assets"
```

---

### 7. Concise Correction Record

This document incorporates the following four mandatory governance and methodological corrections:

1. **Correction A (Elimination of Confirmatory Economic Claims for Track 2):**
   - Removed all assertions that Track 2 has demonstrated a "confirmatory economic edge" or is "valid for baseline economic edge".
   - Classified Track 2 strictly as `ELIGIBLE_FOR_EXPLORATORY_ECONOMIC_EVALUATION_SUBJECT_TO_GOVERNANCE_APPROVAL`.
   - Documented the four prerequisite conditions required for confirmatory claims (pre-registration, approved $K$, validated cost/funding models, and uncompromised OOS data).
2. **Correction B (Elimination of 'Zero Degrees of Freedom' Terminology):**
   - Replaced all instances of `zero degrees of freedom` and `0 degrees of freedom` with `ZERO ADDITIONAL STRATEGY-TUNING HYPERPARAMETERS`.
   - Added explicit methodological clarification that having zero additional strategy-tuning hyperparameters prevents post-hoc strategy curve-fitting, but does not eliminate statistical estimation uncertainty, sampling variance, model selection bias from upstream modeling, or multiple-testing risks across broader governance choices.
3. **Correction C (Reconciliation of Hypothesis Family $K$ for Track 3):**
   - Eliminated the universal formula $K_{\text{Track3}} = 11 \times N$.
   - Replaced with a comprehensive conditional formula framework detailing dependencies on asset scope $M \in \{10, 11\}$, directional scope $D \in \{1, 2, 3\}$, aggregation level (portfolio-level $K=N$ vs asset-level $K = M \times D \times N$), and research mode (exploratory vs confirmatory).
   - Documented dependencies on pending decisions DEC_02, DEC_04, and DEC_06.
4. **Correction D (Establishment of Three Distinct Approval Layers):**
   - Established explicit governance boundaries: Layer 1 (Methodology Direction Approval), Layer 2 (Technical Design Approval), and Layer 3 (Execution Authorization).
   - Defined DEC_01 as strictly deciding Layer 1.
   - Explicitly delineated what is and is not approved under Alternatives A, B, and C at each layer.

---
*End of DEC_01 Human Governance Decision Workshop.*  
*Awaiting explicit Human Governance Supervisor directive. No automated progression to DEC_02 will occur.*
