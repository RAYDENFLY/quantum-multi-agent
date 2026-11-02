# QUANTUM PHASE 5.5: HUMAN GOVERNANCE DECISION WORKSHOP
## STAGE 1 (FOUNDATIONAL DECISION 1 OF 6) - `DEC_01: BARRIER EXECUTION ARCHITECTURE`

**Document Status:** `DECISION_WORKSHOP_STAGE_1_DEC_01_CORRECTED`  
**Publication Timestamp:** `2026-11-02 14:35:00 UTC`  
**Workshop Mode:** `READ_ONLY_DECISION_SUPPORT_ONLY`  
**Current Decision Under Review:** `DEC_01` (`PENDING_HUMAN_DECISION`)  
**All Remaining Decisions (`DEC_02` through `DEC_06`):** `PENDING_HUMAN_DECISION`  
**Lifecycle Status:** Phase 5.5 `NOT_STARTED` | Phase 5.6 `NOT_AUTHORIZED` | Economic Backtesting `NOT_STARTED` | Prospective Holdout `STRICTLY_SEALED`  

**Authoritative References:**
- [QUANTUM_PHASE_5_5_HUMAN_GOVERNANCE_DECISION_BRIEF.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_HUMAN_GOVERNANCE_DECISION_BRIEF.md) (Section 3.1)
- [QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_MASTER_GOVERNANCE_STATUS.md)
- [QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_GOVERNANCE_ERRATA.md)
- [QUANTUM_PHASE_5_5_FINAL_CLOSURE_ADDENDUM.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_CLOSURE_ADDENDUM.md)
- [QUANTUM_PHASE_5_5_FINAL_HUMAN_DECISION_WORKSHEET.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_FINAL_HUMAN_DECISION_WORKSHEET.md) (Section 2.1)
- [QUANTUM_PHASE_5_5_UNRESOLVED_ISSUE_REGISTER.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_UNRESOLVED_ISSUE_REGISTER.md) (`ISS_06`)
- [QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md) (Section 1)
- [QUANTUM_PHASE_5_5_CROSS_DECISION_DEPENDENCIES.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_CROSS_DECISION_DEPENDENCIES.md)
- [PHASE_5_5_0_6_RESEARCH_TRACK_COMPARISON.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_6/PHASE_5_5_0_6_RESEARCH_TRACK_COMPARISON.md)
- [PHASE_5_5_0_8_FULL_FLEET_TEMPORAL_ISOLATION_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_FULL_FLEET_TEMPORAL_ISOLATION_AUDIT.md)

---

### 1. Exact Governance Question
Because feature computation and out-of-fold classifier inference at bar $i$ depend on $\text{close}[i]$ (which is only known at the completion of bar $i$), how should Phase 5.5 define the economic trade entry anchor and exit barrier structure relative to the original close-anchored triple-barrier predictive target (`Alternative A / Track 1`, `Alternative B / Track 2`, or `Alternative C / Track 3`)?

---

### 2. Available Alternatives & Full Tradeoffs

| Alternative | Exact Specification | Advantages | Disadvantages & Failure Risks |
|---|---|---|---|
| **Alternative A (`Track 1`: Close-Anchored Evaluation)** | Anchor entry reference price at $P_{\text{ref}} = \text{close}[i]$ and symmetric barriers at $\text{close}[i](1 \pm 1.5\sigma_t)$ over the 288-bar horizon. | Matches the exact Phase 5.3/5.4 predictive training label (`SOURCE_VERIFIED`). Remains directly relevant for statistical evaluation of the ML classification target (ROC-AUC, Brier score, log-loss, selective precision). | **`NOT AN EXECUTABLE ECONOMIC ENTRY ANCHOR`:** You cannot observe $\text{close}[i]$, run inference, and fill a market order at $\text{close}[i]$. Using Track 1 as an economic trade entry rule introduces causal look-ahead bias and invalidates economic PnL claims. |
| **Alternative B (`Track 2`: Re-Anchored Economic Barriers at $\text{open}[i+1]$)** | Execute trade entry at the next bar's open ($P_{\text{entry,ref}} = \text{open}[i+1]$, plus execution deviation) and re-anchor symmetric triple barriers to $P_{\text{entry,ref}}(1 \pm 1.5\sigma_t)$ over the 288-bar horizon using causal $\sigma_t$ from bar $i$. | Eliminates intrabar look-ahead bias while introducing **`ZERO ADDITIONAL STRATEGY-TUNING HYPERPARAMETERS`** (`SOURCE_VERIFIED` when barrier multiplier $1.5\sigma_t$ and 288-bar horizon remain fixed as specified). Avoids an exit-rule parameter search loop on validation folds. | **Separate Economic Estimand (`ISS_06`):** Because $\text{open}[i+1] \neq \text{close}[i]$, shifting barriers by $(\text{open}[i+1] - \text{close}[i])$ changes the trajectory target. Track 2 **cannot** retrospectively prove the original close-anchored predictive label's economic profitability, has **not** been empirically validated (`NOT_VERIFIED`), and is **not** exempt from upstream/downstream design choices, multiple-testing risks, or selection bias. |
| **Alternative C (`Track 3`: Independent Downstream Strategy Development)** | Treat calibrated Phase 5.4 probabilities as raw alpha scores and engineer new downstream exit rules (asymmetric reward/risk ratios, trailing stops, partial take-profit ladders, or dynamic ATR bands). | Can adapt trade management if symmetric $\pm 1.5\sigma_t$ barriers are economically suboptimal after fees and funding, or if directional drift favors wider profit targets than stops. | **Additional Strategy Hyperparameter Optimization & Sample Partitioning Cost:** Introduces new strategy-tuning hyperparameters that must be fit on Folds 1 to 4, leaving only Fold 5 as an uncontaminated pre-holdout validation fold and confounding ML signal quality with post-hoc exit engineering. |

---

### 3. Technical Consequences
- **Alternative A (`Track 1`):** Requires no new simulation architecture because statistical predictive evaluation on the close-anchored target was already completed and frozen in Phase 5.4. Cannot be used as the Phase 5.5 economic trade simulator (`NOT AN EXECUTABLE ECONOMIC ENTRY ANCHOR`).
- **Alternative B (`Track 2`):** Uses the frozen Phase 5.4 out-of-fold probability predictions directly with deterministic barrier placement anchored at $\text{open}[i+1]$. Requires zero model retraining, zero recalibration, and **`ZERO ADDITIONAL STRATEGY-TUNING HYPERPARAMETERS`** (no exit-rule parameter search loop is required provided the $\pm 1.5\sigma_t$ barrier multiplier and 288-bar horizon follow the fixed specification).
- **Alternative C (`Track 3`):** Requires implementing a walk-forward hyperparameter optimization loop over Folds 1 to 4 to fit stop/target/trailing parameters before evaluating on Fold 5.

---

### 4. Statistical Consequences
- **Separation of Predictive vs. Executable Estimands:**
  - **Track 1 Estimand:** $\mathbb{P}(\text{close-anchored barrier }+1.5\sigma_t\text{ hit before }-1.5\sigma_t \mid \mathcal{F}_i)$. Validated statistically in Phase 5.4.
  - **Track 2 Estimand:** $\mathbb{E}[\text{Net PnL of open}[i+1]\text{-anchored }\pm 1.5\sigma_t\text{ bracket} \mid \mathcal{F}_i]$. This is a **distinct economic estimand** (`ISS_06`).
- **Methodological Boundary on Degrees of Freedom (`ZERO ADDITIONAL STRATEGY-TUNING HYPERPARAMETERS`):**
  - **What Can Be Claimed (`SOURCE_VERIFIED`):** Track 2 adds **`ZERO ADDITIONAL STRATEGY-TUNING HYPERPARAMETERS`** beyond the inherited triple-barrier specification ($\pm 1.5\sigma_t$ barriers and 288-bar maximum holding horizon) and therefore does not require an exit-rule parameter optimization search across Folds 1 to 4.
  - **What Cannot Be Claimed (Strict Statistical Caveat):** Having `ZERO ADDITIONAL STRATEGY-TUNING HYPERPARAMETERS` does **not** mean the overall statistical evaluation is "free of degrees of freedom," free of selection bias, or immune to multiple-testing risk. Prior Phase 5.3/5.4 modeling and threshold choices ($\tau$), alongside governance design choices across `DEC_01` through `DEC_06` (such as directional scope, universe selection, cost/funding scenarios, and hypothesis family $K$), still influence statistical inference and require formal multiplicity control (`DEC_04.6`).
- **Validation Sample Availability (Subject to `DEC_06` Universe Decision):**
  - Under **Alternative B (`Track 2`)**, no validation folds are consumed by exit-rule tuning. Across the 10 full-history assets (`BTCUSDT`, `ETHUSDT`, `BNBUSDT`, `XRPUSDT`, `ADAUSDT`, `SOLUSDT`, `AVAXUSDT`, `LINKUSDT`, `DOGEUSDT`, `LTCUSDT`), Folds 1 through 5 remain available (`316,499` 5m candles for `BTCUSDT` and `316,500` 5m candles for each of the other 9 full-history assets; `METADATA_VERIFIED`), whereas `XMRUSDT` has only `83,863` 5m candles covering Fold 5 (`METADATA_VERIFIED`), with its primary vs. supplementary portfolio status pending human decision in `DEC_06` (`PENDING_HUMAN_DECISION`).
  - Under **Alternative C (`Track 3`)**, Folds 1 to 4 are consumed for downstream exit-rule parameter fitting, leaving only Fold 5 as an uncontaminated validation fold prior to the sealed prospective holdout.

---

### 5. Economic Consequences & Simplified Theoretical Break-Even Analysis
- **Inter-Bar Gap & Slippage Exposure:** Between the bar-$i$ close timestamp and the bar-$(i+1)$ open execution timestamp, price jumps ($\text{open}[i+1] - \text{close}[i]$) and opening bid-ask spreads occur. Under **Alternative B (`Track 2`)**, barriers shift with $\text{open}[i+1]$, so the trader risks $-1.5\sigma_t$ and targets $+1.5\sigma_t$ relative to the executable open reference price $P_{\text{entry,ref}} = \text{open}[i+1]$ rather than chasing a stale close-anchored level.
- **Simplified Theoretical Break-Even Win Rate Derivation (`MATHEMATICALLY_VERIFIED`):**
  To audit the exact friction hurdle under symmetric $\pm 1.5\sigma_t$ barriers at a baseline volatility of $\sigma_t = 1.0\%$ ($100$ bps), consider the **simplified theoretical break-even model** under the following explicit assumptions:
  - Gross winning return: $G = +1.5\sigma_t = +1.50\% = 0.0150$ ($150$ bps).
  - Absolute gross losing return: $L = |-1.5\sigma_t| = 1.50\% = 0.0150$ ($150$ bps).
  - Round-trip transaction cost scenarios: $C \in \{15\text{ bps}, 20\text{ bps}, 30\text{ bps}\} = \{0.0015, 0.0020, 0.0030\}$.
  - Perpetual funding cash flows ($CF_{\text{funding}}$) are excluded ($0$ bps).
  - Zero vertical time-barrier exits before hitting $\pm 1.5\sigma_t$, zero partial fills, zero gap-through-stop slippage, and no quote-notional fee asymmetry between winning and losing legs.

  Expected net return per trade is given by:
  $$\mathbb{E}[R] = p \times G - (1 - p) \times L - C = p(G + L) - L - C$$
  Setting $\mathbb{E}[R] = 0$ yields the exact simplified theoretical break-even win probability $p_{\text{BE}}$:
  $$p_{\text{BE}} = \frac{L + C}{G + L}$$
  Since $G = 150\text{ bps}$ and $L = 150\text{ bps}$, the denominator is $G + L = 300\text{ bps}$ ($3.00\% = 0.0300$):

  | Round-Trip Cost Scenario ($C$) | Gross Win ($G$) | Gross Loss ($L$) | Exact Formula Substitution $p_{\text{BE}} = \frac{L + C}{G + L}$ | Exact Fraction | Theoretical Break-Even Win Rate ($p_{\text{BE}}$) | Required Edge Above $50.00\%$ Coin Flip |
  |---|---|---|---|---|---|---|
  | **$0$ bps (Frictionless)** | $150$ bps ($1.50\%$) | $150$ bps ($1.50\%$) | $\frac{150 + 0}{150 + 150} = \frac{150}{300}$ | $\frac{1}{2}$ | **$50.00\%$** ($0.500000$) | $+0.00\%$ ($0$ bps) |
  | **$15$ bps ($0.15\%$ Optimistic)** | $150$ bps ($1.50\%$) | $150$ bps ($1.50\%$) | $\frac{150 + 15}{150 + 150} = \frac{165}{300}$ | $\frac{11}{20}$ | **$55.00\%$** ($0.550000$) | $+5.00\%$ ($500$ bps) |
  | **$20$ bps ($0.20\%$ Baseline)** | $150$ bps ($1.50\%$) | $150$ bps ($1.50\%$) | $\frac{150 + 20}{150 + 150} = \frac{170}{300}$ | $\frac{17}{30}$ | **$56.67\%$** ($0.566667$) | $+6.67\%$ ($667$ bps) |
  | **$30$ bps ($0.30\%$ Punitive Stress)** | $150$ bps ($1.50\%$) | $150$ bps ($1.50\%$) | $\frac{150 + 30}{150 + 150} = \frac{180}{300}$ | $\frac{3}{5}$ | **$60.00\%$** ($0.600000$) | $+10.00\%$ ($1000$ bps) |

  *(Audit Note: The prior unverified range of "53.3% to 55.0%" understated the true simplified break-even range at $\sigma_t = 1.0\%$, which is exactly **$55.00\%$ to $60.00\%$** across the $15/20/30$ bps cost tiers; `53.33%` corresponds to a $10$ bps cost tier $\frac{160}{300}$ that is not part of the proposed $15/20/30$ bps sweep.)*
- **Strict Limitations of This Simplified Theoretical Break-Even Calculation:**
  1. **Not an Empirical Profitability Threshold:** These numbers represent a simplified theoretical identity at fixed $\sigma_t = 1.0\%$, **not** an empirical profitability guarantee.
  2. **Omitted Real-World Friction Factors:** In actual Phase 5.5 simulation, the break-even threshold varies dynamically per trade and can be shifted upward or downward by:
     - Time-varying volatility $\sigma_t \neq 1.0\%$ (when $\sigma_t < 1.0\%$, fixed bps costs $C$ represent a larger fraction of $G+L$, pushing $p_{\text{BE}}$ even higher; when $\sigma_t > 1.0\%$, $p_{\text{BE}}$ is lower);
     - Perpetual funding settlements ($CF_{\text{funding}}$ over up to three 8-hour intervals);
     - Bid-ask spread, market-impact slippage, and signed execution deviation ($C_{\text{exec,total}}$);
     - Gap-through-stop adverse excursions where realized loss exceeds $1.5\sigma_t$;
     - Vertical time-barrier exits at bar 288 with intermediate returns $|R| < 1.5\sigma_t$; and
     - Directional quote-notional fee asymmetry (`14.89 bps` vs. `15.11 bps`).
  3. **No Claim of Achieved Model Win Rate (`NOT_VERIFIED`):** Nothing in this derivation claims or implies that the frozen QUANTUM Phase 5.3/5.4 models have achieved a $55.00\%$, $56.67\%$, or $60.00\%$ win rate under Track 2 execution (`Phase 5.5 = NOT_STARTED`).

---

### 6. Operational and Risk Implications
- **Bounded Reference Stop Distance (Not a Guaranteed Maximum Loss):** Under **Alternative B (`Track 2`)**, every trade has an explicit, deterministic reference stop-loss distance of $1.5\sigma_t$ from $P_{\text{entry,ref}} = \text{open}[i+1]$, providing a clean volatility scaling input for `DEC_05` portfolio risk sizing. However, a reference stop-loss barrier is **never** a guaranteed maximum loss due to intrabar liquidity gaps and gap-through-stop execution risk.
- **Auditability:** Alternative B prevents post-hoc exit-rule curve-fitting on historical validation folds, maintaining separation between evaluating the frozen directional signals and engineering a new downstream trading strategy.

---

### 7. Upstream and Downstream Dependencies
- **Upstream Dependencies:** **None.** `DEC_01` is the foundational Stage 1 architectural gate. (`DEC_01` does **not** depend on `DEC_02`.)
- **Downstream Dependencies (`Hard Dependencies`):**
  1. **`DEC_02` (Directional Trading Scope):** Requires `DEC_01` to define the trade entry/exit mechanics before authorizing Long-only, Short-only, or Bidirectional execution.
  2. **`DEC_04` (Cost & Statistical Acceptance):** Requires `DEC_01` to define the primary economic estimand and the entry reference price $P_{\text{entry,ref}} = \text{open}[i+1]$ used in `DEC_04.1` (`REFERENCE_PRICE_ACCOUNTING`) and `DEC_04.2` (`Approach A` vs. `Approach B`).
  3. **`DEC_05` (Portfolio Concurrency & Leverage):** Uses the `DEC_01` reference stop-loss distance ($1.5\sigma_t$) in risk-budgeted position sizing (`Option 2` and `Option 3`).

---

### 8. Unresolved Issues, Missing Evidence & Asset-Universe Reconciliation
1. **`ISS_06` (`RESOLVED_BY_SPECIFICATION` - Estimand Shift Limitation):** Track 2 evaluates a re-anchored economic estimand at $\text{open}[i+1]$ and **cannot** retrospectively validate the economic payoff of the original close-anchored training label.
2. **Empirical Gap Distribution (`NOT_VERIFIED`):** The empirical distribution of inter-bar opening gaps $|\text{open}[i+1] - \text{close}[i]| / \sigma_t$ across the repository dataset (whether evaluated across the 10 full-history assets or all 11 total repository assets including `XMRUSDT`, pending `DEC_06`) has not been computed (`NOT_VERIFIED`).
3. **Empirical Economic Performance (`NOT_VERIFIED`):** Neither Track 2 (`Alternative B`) nor Track 3 (`Alternative C`) has been executed or empirically validated (`Phase 5.5 = NOT_STARTED`, `Economic Backtesting = NOT_STARTED`).
4. **Asset-Universe & Candle-Count Reconciliation Across Governance Sources:**
   - **Total Repository Specialist Fleet (`SOURCE_VERIFIED`):** There are **11 total specialist assets** in `data/historical/canonical/exchange=ASTER/`: 10 full-history assets (`BTCUSDT`, `ETHUSDT`, `BNBUSDT`, `XRPUSDT`, `ADAUSDT`, `SOLUSDT`, `AVAXUSDT`, `LINKUSDT`, `DOGEUSDT`, `LTCUSDT`) plus 1 truncated-history asset (`XMRUSDT`).
   - **Primary Evaluation Universe Status (`PENDING_HUMAN_DECISION` in `DEC_06`):** Whether the primary Phase 5.5 portfolio evaluation universe consists of **10 assets** (excluding `XMRUSDT` from primary portfolio aggregation and evaluating `XMRUSDT` in a standalone research appendix under `DEC_06` Option 3, the non-binding engineering recommendation) or **11 assets** (`DEC_06` Option 1) is **not yet decided** (`DEC_06 = PENDING_HUMAN_DECISION`).
   - **Exact 5m Candle Counts (`METADATA_VERIFIED` in `PHASE_5_5_0_8_FULL_FLEET_TEMPORAL_ISOLATION_AUDIT.md`):**
     - `ETHUSDT`, `BNBUSDT`, `XRPUSDT`, `ADAUSDT`, `SOLUSDT`, `AVAXUSDT`, `LINKUSDT`, `DOGEUSDT`, `LTCUSDT` (9 assets): exactly **`316,500`** 5-minute candles each (`2023-10-28` to `2026-10-31`).
     - `BTCUSDT` (1 asset): exactly **`316,499`** 5-minute candles (`2023-10-28 22:00:00` to `2026-10-31 20:59:59.999`, i.e., 1 candle fewer than `316,500`).
     - `XMRUSDT` (1 asset): exactly **`83,863`** 5-minute candles (`2026-01-13 16:45:00` to `2026-10-31 21:19:59.999`, covering Fold 5 only).

#### Asset-Universe Reconciliation Table (`DEC_01` Claims vs. Authoritative Repository Sources)

| Claim in Prior Workshop Draft | Source Evidence in Repository | Verified Status | Required Correction Applied |
|---|---|---|---|
| `"10 primary assets"` (`316,500` bars across the 10 primary assets) | [PHASE_5_5_0_8_FULL_FLEET_TEMPORAL_ISOLATION_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_FULL_FLEET_TEMPORAL_ISOLATION_AUDIT.md) (Lines 28-60) & [QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_PHASE_5_5_DECISION_OPTIONS_AND_TRADEOFFS.md) (Section 6) | `METADATA_VERIFIED` (for candle counts) / `PENDING_HUMAN_DECISION` (for primary universe status in `DEC_06`) | Clarify that the repository has **10 full-history assets** (`BTCUSDT` with `316,499` 5m candles; 9 other assets with `316,500` 5m candles each) and **1 truncated-history asset** (`XMRUSDT` with `83,863` 5m candles in Fold 5). Do not pre-judge `DEC_06`: whether the primary evaluation universe is 10 assets (excluding `XMRUSDT` to a standalone appendix) or 11 assets remains `PENDING_HUMAN_DECISION`. |
| `"11 assets"` (Empirical gap distribution across the 11 assets) | [PHASE_5_5_0_8_FULL_FLEET_TEMPORAL_ISOLATION_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_FULL_FLEET_TEMPORAL_ISOLATION_AUDIT.md) (Line 23: 11 specialist instruments in `data/historical/canonical/exchange=ASTER/`) | `SOURCE_VERIFIED` (total repository fleet is 11 assets) / `NOT_VERIFIED` (empirical gap distribution not computed) | Distinguish **11 total repository specialist assets** (10 full-history + `XMRUSDT` covering Fold 5 only) from the **primary portfolio evaluation universe** (`10` vs. `11` assets, which awaits `DEC_06`). Mark the empirical gap distribution $|\text{open}[i+1] - \text{close}[i]|/\sigma_t$ as `NOT_VERIFIED`. |
| `"316,500 bars across the 10 primary assets"` | [PHASE_5_5_0_8_FULL_FLEET_TEMPORAL_ISOLATION_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_FULL_FLEET_TEMPORAL_ISOLATION_AUDIT.md) (Table Lines 28-57) | `METADATA_VERIFIED` | Specify exact per-asset 5m row counts from the canonical metadata audit: `ETHUSDT`, `BNBUSDT`, `XRPUSDT`, `ADAUSDT`, `SOLUSDT`, `AVAXUSDT`, `LINKUSDT`, `DOGEUSDT`, and `LTCUSDT` each contain **`316,500`** 5m bars (`2023-10-28` to `2026-10-31`), while `BTCUSDT` contains **`316,499`** 5m bars (`1` bar fewer), and `XMRUSDT` contains **`83,863`** 5m bars (`2026-01-13` to `2026-10-31`). |

---

### 9. Epistemic Separation: Facts vs. Identities vs. Assumptions vs. Unverified Claims
- **Verified Facts (`SOURCE_VERIFIED` & `METADATA_VERIFIED`):**
  - Phase 5.3 triple-barrier labels are anchored to $\text{close}[i]$ with symmetric $\pm 1.5\sigma_t$ horizontal barriers and a 288-bar vertical limit (`SOURCE_VERIFIED`).
  - $\text{close}[i]$ is `NOT AN EXECUTABLE ECONOMIC ENTRY ANCHOR` for causal orders triggered by bar-$i$ close features (`SOURCE_VERIFIED`).
  - Alternative B (`Track 2`) introduces **`ZERO ADDITIONAL STRATEGY-TUNING HYPERPARAMETERS`** when barrier multiplier $1.5\sigma_t$ and 288-bar horizon follow the fixed specification (`SOURCE_VERIFIED`).
  - Canonical 5-minute pre-holdout partitions contain `316,499` bars for `BTCUSDT`, `316,500` bars for each of the other 9 full-history assets, and `83,863` bars for `XMRUSDT` (`METADATA_VERIFIED`).
- **Mathematical Identities (`MATHEMATICALLY_VERIFIED`):**
  - Re-anchoring barriers from $\text{close}[i]$ to $\text{open}[i+1]$ shifts both upper and lower barrier price levels by $\Delta P_{\text{gap}} = (\text{open}[i+1] - \text{close}[i])(1 \pm 1.5\sigma_t)$.
  - Under the simplified theoretical binary barrier model ($G = 150$ bps, $L = 150$ bps, zero funding, zero time-exits), $p_{\text{BE}} = \frac{L+C}{G+L}$ equals **$55.00\%$** at $C=15$ bps, **$56.67\%$** at $C=20$ bps, and **$60.00\%$** at $C=30$ bps.
- **Modeling Assumptions:**
  - Assuming that directional alpha learned on excursion paths starting at $\text{close}[i]$ persists across the bar boundary when barriers are re-anchored at $\text{open}[i+1]$.
- **Unverified Claims (`NOT_VERIFIED`):**
  - Any claim that Track 2 (`Alternative B`) or Track 3 (`Alternative C`) achieves positive net economic expectancy or meets the theoretical break-even win rate after transaction costs and funding.
  - Any claim that Track 2 inference is completely free of overall statistical degrees of freedom, selection bias, or multiple-testing risk.

---

### 10. Non-Binding Engineering Recommendation & Failure Analysis

- **Preferred Engineering Option (Non-Binding):** **`Alternative B (Track 2: Re-Anchored Economic Barriers at open[i+1] with ZERO ADDITIONAL STRATEGY-TUNING HYPERPARAMETERS)`**
- **Strongest Alternative:** **`Alternative C (Track 3: Independent Downstream Strategy Development on Folds 1-4, Validated on Fold 5)`**
- **Evidence Supporting Preferred Option:**
  1. Enforces strict causal execution timing ($P_{\text{entry,ref}} = \text{open}[i+1]$) without intrabar look-ahead bias (`SOURCE_VERIFIED`).
  2. Introduces **`ZERO ADDITIONAL STRATEGY-TUNING HYPERPARAMETERS`**, avoiding an exit-rule parameter optimization search across Folds 1 to 4 and preserving all available walk-forward validation folds (`316,499` to `316,500` 5m bars across the 10 full-history assets, plus `83,863` Fold 5 bars for `XMRUSDT` subject to `DEC_06`) for out-of-sample economic evaluation.
  3. Evaluates the frozen Phase 5.3/5.4 selective classifiers without confounding ML signal quality with newly fitted exit heuristics (while still requiring formal multiplicity control in `DEC_04.6` for upstream/downstream governance and threshold choices).
- **Evidence Still Missing:**
  - Empirical out-of-fold net return series under Track 2 (`NOT_VERIFIED`), and empirical measurement of $|\text{open}[i+1] - \text{close}[i]| / \sigma_t$ (`NOT_VERIFIED`).
- **Main Failure Mode (What Would Make This Recommendation Wrong):**
  1. **Microstructure Gap Decay:** If a large fraction of the predicted bar-$i$ price excursion occurs instantaneously in the opening jump between $\text{close}[i]$ and $\text{open}[i+1]$, re-anchoring the $+1.5\sigma_t$ take-profit barrier at $\text{open}[i+1]$ may push the target beyond the remaining impulse exhaustion point, causing Track 2 to fail even when the model's close-anchored forecast was directionally accurate.
  2. **High Symmetric `1:1` Break-Even Hurdle Under Friction:** At $\sigma_t = 1.0\%$, symmetric $\pm 1.5\sigma_t$ barriers (`150` bps win / `150` bps loss) require a simplified theoretical break-even win rate of **$55.00\%$** (at $15$ bps cost), **$56.67\%$** (at $20$ bps cost), or **$60.00\%$** (at $30$ bps cost) before funding and execution deviation. If the frozen models have genuine directional skill but lower win rates that only profit under asymmetric targets (e.g. $+2.5\sigma_t / -1.0\sigma_t$), Track 2 will reject them whereas Track 3 might capture positive expectancy.
- **Conditions Under Which the Alternative (`Alternative C / Track 3`) Would Be Preferable:**
  - If the human supervisor views the Phase 5.3/5.4 classifiers strictly as raw probability alpha filters rather than self-contained bracket-trading rules, **and** is willing to dedicate Folds 1 to 4 to downstream exit-rule parameter optimization (accepting reduced validation sample size on Fold 5 and higher multiple-testing scrutiny).

---

### 11. Governance Status Summary (No Decision Assumed or Requested in This Audit Turn)

- **`DEC_01` (Barrier Execution Architecture):** `PENDING_HUMAN_DECISION`
- **`DEC_02` through `DEC_06`:** `PENDING_HUMAN_DECISION`
- **Phase 5.5:** `NOT_STARTED`
- **Phase 5.6:** `NOT_AUTHORIZED`
- **Economic Backtesting:** `NOT_STARTED`
- **Prospective Holdout (`2026-11-01 00:00:00 UTC` to `2027-04-30 23:59:59.999 UTC`):** `STRICTLY_SEALED`
