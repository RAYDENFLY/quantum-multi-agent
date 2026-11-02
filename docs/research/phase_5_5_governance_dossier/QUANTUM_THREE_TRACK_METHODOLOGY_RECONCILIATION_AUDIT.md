# QUANTUM - THREE-TRACK METHODOLOGY RECONCILIATION AUDIT
## HORIZON RECONCILIATION, TEMPORAL FOLD INTEGRITY, AND ESTIMAND SEPARATION

**Document Version:** 1.1.0-FINAL-CORRECTION  
**Date:** 2026-11-02  
**Classification:** Quantitative Methodology & Statistical Governance Audit  
**Status:** FINAL CORRECTION - AWAITING HUMAN GOVERNANCE REVIEW  
**Author:** Senior Quantitative Research Auditor & Lead Systems Architect  

---

## 1. EXECUTIVE SUMMARY

This audit delivers a rigorous, evidence-based methodological reconciliation of the three research tracks (Track 1 Predictive Benchmark, Track 2 Re-Anchored Economic Evaluation, and Track 3 Independent Strategy Research) for QUANTUM.

This final correction addresses and resolves three material methodological issues identified during audit review:
1. **Fold 5 OOS Eligibility:** Reclassifies Fold 5 from conditionally eligible to `OOS_ELIGIBILITY_NOT_VERIFIED` for confirmatory alpha claims, establishing that prior observation during Phase 5.3 and Phase 5.4 alongside unverified researcher exposure restricts Fold 5 to exploratory research only.
2. **Track 2 Target Alignment:** Reclassifies Track 2 from partially aligned to `SIGNAL_COMPATIBLE_WITH_SEPARATE_ECONOMIC_ESTIMAND`, establishing that re-anchoring from `close[i]` to `open[i+1]` alters the mathematical estimand from conditional probability $P(y \mid X)$ to realized financial payoff $\mathbb{E}[R_{\text{net}}]$.
3. **Hypothesis Family K Formulation:** Replaces hardcoded $K=11$ assertions with a conditional hypothesis framework detailing how $K \in \{1, 10, 11, 22, 33, \dots\}$ depends strictly on pending decisions DEC_01, DEC_02, DEC_03, DEC_04, and DEC_06.

Additionally, this document incorporates explicit clarifications regarding the provisional nature of the Track 3 holding range (6 to 48 bars) and formalizes the signed cash-flow conventions for perpetual funding scenarios.

```
+----------------------------------------------------------------------------------------------------+
|                                METHODOLOGY AUDIT FINAL VERDICT                                     |
+----------------------------------------------------------------------------------------------------+
|                         METHODOLOGY_RECONCILIATION_CLOSED_WITH_LIMITATIONS                         |
+----------------------------------------------------------------------------------------------------+
```

### 1.1 Track Readiness Status

```text
+------------------------------------+---------------------------------------------------+-----------------------+
| Research Track                     | Target Alignment Classification                   | Operational Readiness |
+------------------------------------+---------------------------------------------------+-----------------------+
| Track 1: Predictive Benchmark      | TARGET_ALIGNED (at 12-bar horizon)                | READY_FOR_REVIEW      |
| Track 2: Re-Anchored Economic      | SIGNAL_COMPATIBLE_WITH_SEPARATE_ECONOMIC_ESTIMAND | REQUIRES_REVISION     |
| Track 3: Strategy Research         | INDEPENDENT_ALPHA_SCORE                           | REQUIRES_REVISION     |
+------------------------------------+---------------------------------------------------+-----------------------+
```

---

## 2. IMMUTABLE GOVERNANCE CONSTRAINTS

All governance constraints remain active and strictly enforced:
- **Phase 5.5 Research Status:** `NOT_STARTED`
- **Phase 5.6 Authorization Status:** `NOT_AUTHORIZED`
- **Economic Backtesting Status:** `NOT_STARTED`
- **Decisions DEC_01 through DEC_06:** `PENDING_HUMAN_DECISION`
- **Prospective Holdout Partition:** `STRICTLY_SEALED`
- **Frozen Phase 5.3 Models & Phase 5.4 Preprocessors:** `IMMUTABLE`
- **Profitability Claims:** Strictly prohibited. No strategy or model is verified as profitable.

---

## 3. HORIZON RECONCILIATION AUDIT

### 3.1 Empirical Evidence from Codebase and Manifests

A direct audit of the production code and training execution scripts reveals the exact mathematical target used to train the 55 frozen Phase 5.3 LightGBM models:

1. **Target Contract Specification ([`src/quantum/ml/contracts.py:L35-47`](file:///d:/quantum-multi-agent/src/quantum/ml/contracts.py#L35-L47)):**
   ```python
   class TargetConfiguration(BaseModel):
       model_config = ConfigDict(frozen=True)
       timeframe: Timeframe = Timeframe.M5
       horizon_bars: int = 12
       maximum_holding_minutes: int = 60
       volatility_lookback: int = 20
       barrier_multiplier: float = 1.5
       volatility_type: str = "RETURN_VOLATILITY"
       min_volatility: float = 1e-6
       ambiguity_policy: str = "CONSERVATIVE_EXCLUDE"
   ```
2. **Label Generator Implementation ([`src/quantum/features/labeling.py:L33-47`](file:///d:/quantum-multi-agent/src/quantum/features/labeling.py#L33-L47)):**
   ```python
   class TripleBarrierLabelGenerator:
       def __init__(
           self,
           horizon_bars: int = 12,
           volatility_lookback: int = 20,
           barrier_multiplier: float = 1.5,
           timeframe_ms: int = 300_000,
           ambiguity_policy: str = "CONSERVATIVE_EXCLUDE",
           ...
       ):
   ```
3. **Pilot Training Script ([`scripts/run_phase5_3_1_pilot.py:L93-98`](file:///d:/quantum-multi-agent/scripts/run_phase5_3_1_pilot.py#L93-L98)):**
   ```python
   gen = TripleBarrierLabelGenerator(
       horizon_bars=12,
       volatility_lookback=20,
       barrier_multiplier=1.5,
       timeframe_ms=300_000,
   )
   ```
4. **Fleet Training Script ([`scripts/run_phase5_3_2_fleet.py:L137-142`](file:///d:/quantum-multi-agent/scripts/run_phase5_3_2_fleet.py#L137-L142)):**
   All 11 assets were processed with identical parameters: `horizon_bars=12`, `volatility_lookback=20`, `barrier_multiplier=1.5`, `timeframe_ms=300_000`.
5. **Purging and Embargo Metadata ([`artifacts/phase_5_3_2/fleet_summary/fleet_catalog.json`](file:///d:/quantum-multi-agent/artifacts/phase_5_3_2/fleet_summary/fleet_catalog.json)):**
   Every fold across all 11 assets records:
   - `purged_samples: 12` (Purge length exactly equals the 12-bar label horizon to eliminate label overlap leakage between train and test sets).
   - `embargo_samples: 24` (Embargo length equals $2 \times$ horizon to prevent autoregressive feature leakage).

### 3.2 Detailed Answers to Horizon Audit Questions

#### Q1: Apa target persis yang digunakan saat training Phase 5.3?
Multiclass triple-barrier classification with target classes $\{-1, 0, 1\}$:
- $+1$ (Take-Profit / Upper Barrier): Price touches $\text{close}[i] \times (1 + 1.5\sigma_t)$ prior to lower barrier and within 12 bars.
- $-1$ (Stop-Loss / Lower Barrier): Price touches $\text{close}[i] \times (1 - 1.5\sigma_t)$ prior to upper barrier and within 12 bars.
- $0$ (Time Expiration): Neither barrier is touched within 12 bars ($60$ minutes).
- Ambiguity Policy: If high and low of the same bar touch both barriers, sample is marked ambiguous and excluded (`CONSERVATIVE_EXCLUDE`).

#### Q2: Apa definisi label, barrier, anchor, dan horizon?
- **Timeframe:** 5-minute candles (`M5`, 300,000 ms).
- **Anchor:** Bar close price ($\text{close}[i]$) of the feature snapshot bar.
- **Barrier Multiplier:** $1.5 \times \sigma_t$, where $\sigma_t$ is the 20-bar rolling standard deviation of 5m log returns:
  $$\sigma_t = \sqrt{\frac{1}{20}\sum_{k=0}^{19} \left(r_{t-k} - \bar{r}\right)^2}$$
- **Horizon:** Exactly 12 bars (60 minutes). Evaluation inspects bars $i+1$ through $i+12$.

#### Q3: Apakah horizon 12 bar benar-benar digunakan oleh seluruh 11 specialist models?
**YES.** Verified across all 11 assets in [`fleet_catalog.json`](file:///d:/quantum-multi-agent/artifacts/phase_5_3_2/fleet_summary/fleet_catalog.json): `BTCUSDT`, `ETHUSDT`, `SOLUSDT`, `BNBUSDT`, `XRPUSDT`, `ADAUSDT`, `DOGEUSDT`, `AVAXUSDT`, `LINKUSDT`, `LTCUSDT`, and `XMRUSDT` all record `purged_samples: 12` and `embargo_samples: 24` across all 5 folds.

#### Q4: Apakah ada perbedaan konfigurasi antar-asset?
**NO.** Target parameters, feature schemas (36 stationary features, schema hash `cc779ea9e3b1862394b7115375c54c4f4cf3d6496bfabf7de457b578762aaf92`), scaling algorithms, and fold splitting logic are completely identical across all 11 assets. The only difference is dataset length for `XMRUSDT` (83,863 candles vs 316,500 candles for the remaining 10 assets, due to exchange historical availability).

#### Q5: Apakah Track 1 dengan horizon 288 masih mengukur target yang sama dengan frozen model?
**NO. It is an irreconcilable `TARGET_MISMATCH`.**
Evaluating a model trained on 12-bar labels against a 288-bar label measures a completely different target. Over 288 bars (24 hours), the probability of touching a $\pm 1.5\sigma_{5m}$ barrier approaches 1.0, expiration rates collapse, and the class distribution diverges drastically from the training distribution. Track 1 MUST use the original 12-bar target.

#### Q6: Apakah Track 2 dapat menggunakan probabilitas frozen model tanpa mengubah target?
Track 2 re-anchors execution to `open[i+1]`. This inherently alters the target from a close-anchored prediction to an open-anchored economic return. Therefore, Track 2 is classified as `SIGNAL_COMPATIBLE_WITH_SEPARATE_ECONOMIC_ESTIMAND`. If Track 2 were forced to use a 288-bar holding horizon, it becomes an unviable `TARGET_MISMATCH` because the model's prediction window is only 12 bars.

#### Q7: Apa konsekuensi jika prediksi horizon 12 digunakan untuk keputusan dengan horizon 288?
1. **Information Decay:** Machine learning models trained on high-frequency 5m microstructural features suffer rapid alpha decay. By bar 12, the conditional information is exhausted. Holding for 288 bars subjects the position to 276 bars (23 hours) of unmodeled market drift.
2. **Funding and Volatility Accumulation:** Holding for 288 bars crosses up to three 8-hour perpetual funding cycles (00:00, 08:00, 16:00 UTC), accumulating significant funding drag that was never incorporated into the model's objective function.
3. **Invalid Sizing & Risk Calibration:** Sizing based on 12-bar win probabilities fails because the probability of barrier breach over 288 bars is governed by long-term diffusion, leading to severe underestimation of downside tail risk.

#### Q8: Apakah Track 3 dapat mengoptimalkan exit horizon tanpa mengubah makna prediksi model?
**YES, under explicit strategy research framing.**
Track 3 treats model output probabilities as a **raw alpha score** or initiation trigger. Downstream execution research optimizes holding horizons, trailing stops, and profit targets to maximize risk-adjusted economic return without claiming that the base model directly predicted those multi-hour outcomes.

### 3.3 Horizon Reconciliation Summary Table

```text
+-------------------+--------------------+--------------+--------------+------------------+-------------------------------------------------+---------------------------------------------------+
| Component         | Training Target    | Horizon      | Anchor       | Barrier          | Source Evidence                                 | Alignment Classification                          |
+-------------------+--------------------+--------------+--------------+------------------+-------------------------------------------------+---------------------------------------------------+
| Phase 5.3 Models  | Multiclass {-1,0,1}| 12 bars (1h) | close[i]     | +/- 1.5 sigma    | labeling.py:L39, pilot_summary.json             | BASELINE_FROZEN                                   |
| Track 1 (12-bar)  | Multiclass {-1,0,1}| 12 bars (1h) | close[i]     | +/- 1.5 sigma    | ModelEvaluationContract, materialized_oof       | TARGET_ALIGNED                                    |
| Track 1 (288-bar) | Hypothetical Daily | 288 bars(24h)| close[i]     | Unscaled sigma   | PHASE_5_5_0_8 narrative specification           | TARGET_MISMATCH                                   |
| Track 2 (12-bar)  | Causal Economic    | 12 bars (1h) | open[i+1]    | +/- 1.5 sigma    | Proposed causal economic engine                 | SIGNAL_COMPATIBLE_WITH_SEPARATE_ECONOMIC_ESTIMAND |
| Track 2 (288-bar) | Extended Economic  | 288 bars(24h)| open[i+1]    | Unscaled sigma   | PHASE_5_5_0_8 narrative specification           | TARGET_MISMATCH                                   |
| Track 3 (Dynamic) | Downstream Alpha   | Provisional  | open[i+1]/LMT| Dynamic ATR / R  | SniperAgent:L86, BankerAgent:L143               | INDEPENDENT_ALPHA_SCORE                           |
+-------------------+--------------------+--------------+--------------+------------------+-------------------------------------------------+---------------------------------------------------+
```

---

## 4. TEMPORAL FOLD AND OOS AUDIT (ISSUE A RESOLUTION)

### 4.1 Separation of OOS Concepts

To maintain statistical rigor, three distinct concepts of out-of-sample data must be decoupled:
1. **Model OOS (Base Learner Generalization):** Whether the base LightGBM specialist was trained on the data partition.
2. **Strategy OOS (Parameter Search Generalization):** Whether downstream execution parameters ($\tau_{\text{entry}}$, TP/SL ladders, trailing stop thresholds) were fitted on the data partition.
3. **Researcher Exposure (Information Leakage):** Whether human researchers or automated processes observed performance statistics, error distributions, or market regimes on that partition prior to formulating strategy rules.

### 4.2 Fold Usage History and Classification

Inspection of [`artifacts/phase_5_3_1/pilot_summary.json`](file:///d:/quantum-multi-agent/artifacts/phase_5_3_1/pilot_summary.json#L30-L91) and [`artifacts/phase_5_4/materialized_oof/BTCUSDT_oof.parquet`](file:///d:/quantum-multi-agent/artifacts/phase_5_4/materialized_oof/BTCUSDT_oof.parquet) provides exact empirical boundary timestamps and prior usage logs:

```text
+--------+--------------------------+------------------------+-------------------------------------+-----------------------------+------------------------------------+
| Fold   | Time Range (UTC)         | Historical Role        | Prior Usage in Phase 5.3 / 5.4      | Access Verification Status  | OOS Eligibility Classification     |
+--------+--------------------------+------------------------+-------------------------------------+-----------------------------+------------------------------------+
| Fold 1 | 2025-01-29 -> 2025-04-30 | CV Test Partition 1    | B0-B4 evaluation, OOF materialization| VERIFIED_FROM_REPOSITORY    | IN_SAMPLE_FOR_STRATEGY_TUNING      |
| Fold 2 | 2025-04-30 -> 2025-07-30 | CV Test Partition 2    | B0-B4 evaluation, OOF materialization| VERIFIED_FROM_REPOSITORY    | IN_SAMPLE_FOR_STRATEGY_TUNING      |
| Fold 3 | 2025-07-30 -> 2025-10-30 | CV Test Partition 3    | B0-B4 evaluation, OOF materialization| VERIFIED_FROM_REPOSITORY    | IN_SAMPLE_FOR_STRATEGY_TUNING      |
| Fold 4 | 2025-10-30 -> 2026-01-29 | CV Test Partition 4    | B0-B4 evaluation, OOF materialization| VERIFIED_FROM_REPOSITORY    | IN_SAMPLE_FOR_STRATEGY_TUNING      |
| Fold 5 | 2026-01-29 -> 2026-04-30 | CV Test Partition 5    | B0-B4 evaluation, OOF materialization| VERIFIED_FROM_REPOSITORY    | OOS_ELIGIBILITY_NOT_VERIFIED       |
| Holdout| 2026-11-01 onwards       | Prospective Validation | NONE (Sealed holdout)               | STRICTLY_SEALED             | RESERVED_FUTURE_GOVERNANCE_ONLY    |
+--------+--------------------------+------------------------+-------------------------------------+-----------------------------+------------------------------------+
```

### 4.3 Detailed Audit of Fold 5 Status

1. **Prior Observation:** In Phase 5.3, Fold 5 test data was evaluated to assess model performance, and results were cataloged in [`artifacts/phase_5_3_1/BTCUSDT/fold_5/metrics.json`](file:///d:/quantum-multi-agent/artifacts/phase_5_3_1/BTCUSDT/fold_5/metrics.json). In Phase 5.4, 26,140 predictions were concatenated into [`artifacts/phase_5_4/materialized_oof/BTCUSDT_oof.parquet`](file:///d:/quantum-multi-agent/artifacts/phase_5_4/materialized_oof/BTCUSDT_oof.parquet). Consequently, Fold 5 is `PREVIOUSLY_OBSERVED_VALIDATION_DATA` with respect to the base models.
2. **Lack of Researcher Exposure Audit Trail:** While the repository contains no script demonstrating that downstream strategy parameters were fitted on Fold 5, the absence of parameter fitting does not prove that Fold 5 is an independent, virgin out-of-sample partition. Researchers have observed the evaluation metrics and macroeconomic regimes of the Fold 5 period (January to April 2026). Without a cryptographic audit trail proving zero researcher exposure, declaring Fold 5 as a clean OOS dataset is scientifically invalid.
3. **Mandatory Governance Ruling:** Fold 5 is formally classified as:
   ```
   OOS_ELIGIBILITY_NOT_VERIFIED
   ```
   - **Permitted Role:** Fold 5 MAY be used for **exploratory research**, internal cross-validation stability checks, and diagnostic parameter sensitivity profiling.
   - **Prohibited Role:** Fold 5 is **STRICTLY PROHIBITED FOR CONFIRMATORY ALPHA CLAIMS**. No strategy tested on Fold 5 may be declared validated or production-ready without formal unsealing of a truly unobserved dataset under human governance authorization.
4. **Prospective Holdout Integrity:** The prospective holdout partition (`2026-11-01 00:00 UTC` onwards) remains completely unobserved and `STRICTLY_SEALED`.

---

## 5. TRACK 1 - PREDICTIVE BENCHMARK RECONCILIATION

### 5.1 Objective and Scope

Track 1 is an isolated statistical measurement of the classification performance of the frozen Phase 5.3 models against the exact 12-bar target used during training.

### 5.2 Evaluated Metrics Matrix

```text
+-----------------------+-------------------------+-----------------------------------------+------------------------------------+
| Metric                | Mathematical Definition | Source File / Implementation            | Current Computation Status         |
+-----------------------+-------------------------+-----------------------------------------+------------------------------------+
| Accuracy              | (TP + TN) / Total       | ml/evaluation.py:L43                    | COMPUTED in metrics.json (0.3677)  |
| Balanced Accuracy     | Mean recall per class   | ml/evaluation.py:L44                    | COMPUTED in metrics.json (0.4283)  |
| Macro F1-Score        | Unweighted mean F1      | ml/evaluation.py:L45                    | COMPUTED in metrics.json (0.3572)  |
| Per-Class Prec/Rec/F1 | Precision, Recall per c | ml/evaluation.py:L48-59                 | COMPUTED in metrics.json           |
| Confusion Matrix      | 3x3 error transitions   | ml/evaluation.py:L62                    | COMPUTED in metrics.json           |
| ROC-AUC (OvR)         | Multiclass OvR AUC      | ml/evaluation.py:L68                    | COMPUTED in metrics.json (0.5962)  |
| Brier Score           | Mean squared prob error | ml/evaluation.py:L65                    | COMPUTED in metrics.json (0.6591)  |
| ECE Calibration Error | 10-bin reliability diff | artifacts/phase_5_4_3/                  | COMPUTED in Phase 5.4.3 audits     |
| AURCC / Risk-Coverage | Selective abstention    | artifacts/phase_5_4_4/                  | COMPUTED in Phase 5.4.4 audits     |
| PR-AUC (OvR)          | Precision-Recall AUC    | scikit-learn average_precision_score    | PENDING fleet-wide consolidation   |
+-----------------------+-------------------------+-----------------------------------------+------------------------------------+
```

### 5.3 Methodological Isolation Guarantee

Track 1 evaluates the statistical conditional distribution $P(y \mid X_t)$. It generates zero economic cash flows, applies zero transaction costs, and creates no trading positions. It serves as the baseline ground truth for model predictive quality.

---

## 6. TRACK 2 - ECONOMIC EVALUATION RECONCILIATION (ISSUE B RESOLUTION)

### 6.1 Mathematical Separation of Estimands

Track 2 re-anchors execution to the open of the subsequent bar (`open[i+1]`) to enforce physical causality. This re-anchoring alters the fundamental estimand:

```
+----------------------------------------------------------------------------------------------------+
|                                    ESTIMAND SEPARATION ANALYSIS                                    |
+------------------------------------+---------------------------------------------------------------+
| Target / Metric                    | Mathematical Specification                                    |
+------------------------------------+---------------------------------------------------------------+
| 1. Training Label                  | y_i = sign(touch(close[i], +/- 1.5 sigma_t, 12 bars))          |
| 2. Model Predictive Output         | p_1 = P(y_i = +1 | X_i) [Calibrated for close[i] target]      |
| 3. Re-Anchored Economic Outcome    | R_econ = touch(open[i+1], +/- 1.5 sigma_t, 12 bars)           |
| 4. Realized Net Financial Payoff   | L_realized = L_price,ref + C_exec,total + C_fees - CF_funding |
+------------------------------------+---------------------------------------------------------------+
```

### 6.2 Key Methodological Findings on Track 2

1. **Target Alignment vs Signal Compatibility:** Track 2 is NOT target-aligned. It is formally classified as:
   ```
   SIGNAL_COMPATIBLE_WITH_SEPARATE_ECONOMIC_ESTIMAND
   ```
   The model was trained to predict barrier touches anchored at `close[i]`. Evaluating an execution that enters at `open[i+1]` introduces gap risk ($\text{open}[i+1] - \text{close}[i]$), execution slippage, bid-ask spread, and exchange taker fees.
2. **Probability Calibration:** The frozen model probability $p_1$ cannot be assumed to be a calibrated probability for the re-anchored economic outcome $R_{\text{econ}}$. The calibration curves (ECE/MCE) verified in Phase 5.4.3 apply strictly to the `close[i]` label distribution.
3. **Requirement for Independent Empirical Validation:** To evaluate Track 2 without invalid claims, research must independently estimate the empirical relationship between model score tiers ($p_1 \in [0.5, 0.6], [0.6, 0.7], \dots$) and realized economic expectancy $\mathbb{E}[R_{\text{net}} \mid p_1]$.
4. **Zero Profitability Claim:** Track 2 is an experimental benchmark. No claim of economic viability or positive net expectancy is asserted or implied prior to empirical verification under an authorized backtest engine.

---

## 7. TRACK 3 - STRATEGY RESEARCH & CLARIFICATIONS

### 7.1 Objective and Alpha Score Framing

Track 3 treats the frozen LightGBM model probability $p_1 = P(y = +1 \mid X_t)$ as a **continuous raw alpha ranking signal**. Downstream strategy heuristics manage order entry, asymmetric stop placement, and trade lifecycle.

### 7.2 Holding Range Clarification (Section 5 Resolution)

The previously proposed holding range of 6 to 48 bars is classified as:
```
PROVISIONAL_DESIGN_RANGE_NOT_EMPIRICALLY_VALIDATED
```
- **Origin:** The range represents an architectural proposal based on microstructural intuition ($6\text{ bars} = 30\text{ min}$, $48\text{ bars} = 4\text{ hours}$), NOT an empirically validated parameter boundary derived from asset volatility or autocorrelation structures.
- **Multiple-Testing Impact:** If all candidate strategy parameters are evaluated across a full grid search (5 entry thresholds $\times$ 5 SL multipliers $\times$ 4 TP1 multiples $\times$ 3 TP1 fractions $\times$ 4 TP2 multiples $\times$ 3 trailing stop multiples $\times$ 4 holding limits), the search space yields:
  $$5 \times 5 \times 4 \times 3 \times 4 \times 3 \times 4 = 14{,}400 \text{ parameter configurations}$$
- **Data-Mining Penalty:** Evaluating 14,400 configurations creates severe data-snooping risks. Under family-wise error rate control, dividing $\alpha = 0.05$ across 14,400 hypotheses requires significance hurdles ($p < 3.47 \times 10^{-6}$) that make positive discoveries virtually impossible.
- **Technical Recommendation:** Strategy research must pre-register a sparse configuration set ($N \le 10$ candidates) or utilize cross-validation shrinkage before any testing occurs.

---

## 8. FUNDING SCENARIOS & CASH-FLOW RECONCILIATION (SECTION 6 RESOLUTION)

### 8.1 Parametric Funding Grid

Canonical historical 5m Parquet datasets do NOT contain historical perpetual funding rate timestamps. The repository state remains strictly:
```
FUNDING_DATA_UNAVAILABLE
```
Historical funding rates cannot be fabricated. Therefore, Track 2 and Track 3 must evaluate performance across a standardized parametric funding sensitivity grid:

```text
+----------+-----------------------------+------------------------+-------------------------------------------------------------+
| Scenario | Funding Rate per 8h (r_F)   | Annualized Drag / Gain | Analytical Role                                             |
+----------+-----------------------------+------------------------+-------------------------------------------------------------+
| S_neg3   | -3.0 bps (-0.03%)           | -32.85% p.a.           | Extreme adverse regime (Shorts pay Longs heavily)           |
| S_neg1   | -1.0 bps (-0.01%)           | -10.95% p.a.           | Moderate adverse regime                                     |
| S_zero   |  0.0 bps ( 0.00%)           |   0.00% p.a.           | Pure price-action baseline (Zero funding drag)              |
| S_pos1   | +1.0 bps (+0.01%)           | +10.95% p.a.           | Baseline neutral regime (Longs pay Shorts baseline)         |
| S_pos3   | +3.0 bps (+0.03%)           | +32.85% p.a.           | Elevated bull regime (Longs pay Shorts heavily)             |
+----------+-----------------------------+------------------------+-------------------------------------------------------------+
```

### 8.2 Signed Cash-Flow Accounting Convention

To prevent accounting sign errors, the cash-flow sign convention is explicitly codified:

$$\text{Net PnL} = L_{\text{price,ref}} + C_{\text{exec,total}} + C_{\text{fees}} - CF_{\text{funding}}$$

Where $CF_{\text{funding}}$ represents net cash flow from funding settlements:
- $CF_{\text{funding}} > 0$: **Cash Inflow** (Funding payment received by the trader; increases net equity).
- $CF_{\text{funding}} < 0$: **Cash Outflow** (Funding payment paid by the trader; decreases net equity).

#### Impact by Position Direction:
1. **When Funding Rate $r_F > 0$ (Positive Funding):**
   - **Long Position:** Pays funding. $CF_{\text{funding}} = - q \cdot P_{\text{mark}} \cdot r_F < 0$ (Cost drag).
   - **Short Position:** Receives funding. $CF_{\text{funding}} = + q \cdot P_{\text{mark}} \cdot r_F > 0$ (Income boost).
2. **When Funding Rate $r_F < 0$ (Negative Funding):**
   - **Long Position:** Receives funding. $CF_{\text{funding}} = + q \cdot P_{\text{mark}} \cdot |r_F| > 0$ (Income boost).
   - **Short Position:** Pays funding. $CF_{\text{funding}} = - q \cdot P_{\text{mark}} \cdot |r_F| < 0$ (Cost drag).

*Notice: Parametric funding scenarios represent analytical stress tests only and do NOT constitute historical empirical evidence. DEC_03 remains strictly `PENDING_HUMAN_DECISION`.*

---

## 9. HYPOTHESIS FAMILY K RECONCILIATION (ISSUE C RESOLUTION)

### 9.1 Factors Determining Hypothesis Family Size K

The size of the confirmatory hypothesis family $K$ cannot be fixed arbitrarily to $K=11$ based solely on asset count. $K$ is a direct mathematical consequence of research design choices governed by pending human decisions:

1. **Primary Evaluation Universe (DEC_06):** 10 core liquid assets vs 11 assets (including XMR with 83K bars).
2. **Directional Scope (DEC_02):** Long-only testing ($M=1$) vs separate Long and Short testing ($M=2$) vs Long, Short, and Blended portfolio testing ($M=3$).
3. **Primary Aggregation Level:** Per-asset hypothesis testing ($K \propto \text{Assets}$) vs a single aggregate fleet portfolio hypothesis ($K=1$, where individual asset metrics are treated as secondary/exploratory).
4. **Strategy Variants ($N_{\text{variants}}$):** In Track 3, testing multiple parameter configurations expands $K$ multiplicatively ($K = \text{Assets} \times N_{\text{variants}}$).

### 9.2 Conditional Hypothesis Family Scenarios

```text
+----+----------------------------------------------+--------+------------------+------------------------------+-------+-------------------------+
| #  | Research Scope Description                   | Assets | Directional Mode | Confirmatory Hypotheses      | K     | Governing Dependencies  |
+----+----------------------------------------------+--------+------------------+------------------------------+-------+-------------------------+
| 1  | Fleet Portfolio Aggregate Primary Hypothesis | Fleet  | Combined         | Single Portfolio Return      | K = 1 | DEC_01, DEC_04          |
| 2  | Core Liquid Fleet Per-Asset Confirmatory     | 10     | Long-Only        | 10 Individual Assets         | K = 10| DEC_02 (Long), DEC_06   |
| 3  | Full Fleet Per-Asset Confirmatory            | 11     | Long-Only        | 11 Individual Assets         | K = 11| DEC_02 (Long), DEC_06   |
| 4  | Core Liquid Fleet Disaggregated Confirmatory | 10     | Long & Short     | 10 Long + 10 Short           | K = 20| DEC_02 (L/S), DEC_06    |
| 5  | Full Fleet Disaggregated Confirmatory        | 11     | Long & Short     | 11 Long + 11 Short           | K = 22| DEC_02 (L/S), DEC_06    |
| 6  | Full Fleet Comprehensive Directional Family  | 11     | Long, Short, Comb| 11 Long + 11 Short + 11 Comb | K = 33| DEC_02, DEC_04, DEC_06  |
| 7  | Track 3 Multi-Variant Strategy Confirmatory  | 11     | Long-Only        | 11 Assets x N Variants       | 11 x N| DEC_01 (Alt C), DEC_04  |
+----+----------------------------------------------+--------+------------------+------------------------------+-------+-------------------------+
```

*Governance Status: The exact value of $K$ is NOT a technical parameter to be determined by engineering agents. It remains strictly `PENDING_HUMAN_DECISION` under DEC_04.*

---

## 10. FAIR COMPARISON PROTOCOL

To ensure scientific validity without confounding disparate objectives, results must be reported across three decoupled reporting tiers:

```text
+-------------------+----------------------------+-------------------------------------+-------------------------------------+
| Dimension         | Group A: Predictive Eval   | Group B: Economic Evaluation        | Group C: Strategy Research          |
+-------------------+----------------------------+-------------------------------------+-------------------------------------+
| Primary Track     | Track 1                    | Track 2                             | Track 3                             |
| Investigated Role | Pure Classification Power  | Causal Baseline Economic Edge       | Downstream Risk-Adjusted PnL        |
| Evaluation Anchor | Bar Close: close[i]        | Next Open: open[i+1]                | Next Open / Limit Order             |
| Exit Mechanism    | Symmetric +/- 1.5 sigma    | Symmetric +/- 1.5 sigma             | Asymmetric TP/SL, Trailing, Ratchet |
| Tuned Parameters  | ZERO                       | ZERO                                | Optimized over grid                 |
| Primary Metrics   | Balanced Acc, ROC-AUC, ECE | Net Expectancy (bps), Profit Factor | Annualized Sharpe, Max DD, Net PnL  |
| Direct Comparison | Independent Ground Truth   | Comparative Baseline for Track 3    | Incremental Delta vs Track 2        |
+-------------------+----------------------------+-------------------------------------+-------------------------------------+
```

### 10.1 Methodological Prohibitions
- **NO Single Composite Score:** Combining classification accuracy with dollar PnL into a single score is strictly forbidden.
- **NO Post-Hoc Tuning:** Strategy parameters tested on Fold 5 must never be adjusted after viewing Fold 5 results.
- **NO Overlapping Position Fabrications:** Concurrency must respect discrete position limits ($\le 3$ positions) enforced by [`RiskAgent`](file:///d:/quantum-multi-agent/src/quantum/agents/risk.py#L130).

---

## 11. REQUIRED DECISION TABLE

```text
+----+-----------------------------+------------------------------------+--------------------------------+----------------------------------+------------------------------------+--------------------------+
| #  | Question                    | Repository Evidence                | Finding                        | Risk                             | Technical Recommendation           | Human Decision Required  |
+----+-----------------------------+------------------------------------+--------------------------------+----------------------------------+------------------------------------+--------------------------+
| 1  | Horizon 12 vs 288           | labeling.py:L39, pilot_summary.json| Phase 5.3 models trained on 12b| Target mismatch if 288b is used  | Reconcile Track 1 & 2 to 12 bars   | Approve 12-bar horizon   |
| 2  | Track 1 Target Alignment    | target_config: horizon=12, bar=1.5 | Exact 12-bar match exists      | Bias if evaluated on 288 bars    | Maintain frozen 12-bar target      | Approve Track 1 scope    |
| 3  | Track 2 Estimand Status     | open[i+1] entry with 12b barrier   | Separate economic estimand     | False assumption of calibration  | Signal-compatible separate estimand| Approve DEC_01 (Alt B)   |
| 4  | Track 3 Alpha Framing       | SniperAgent:L86, BankerAgent:L143  | Raw alpha score optimization   | Data-mining and overfitting      | Folds 1-4 tuning, Fold 5 OOS lock  | Approve DEC_01 (Alt C)   |
| 5  | Fold 5 OOS Status           | BTCUSDT_oof.parquet (26,140 rows)  | Prior base model evaluation    | Invalidation of model holdout    | OOS_ELIGIBILITY_NOT_VERIFIED       | Approve exploratory role |
| 6  | Funding Rate Policy         | Canonical parquets lack funding    | FUNDING_DATA_UNAVAILABLE       | False precision in historical PnL| Parametric grid (-3 to +3 bps)     | Approve DEC_03 policy    |
| 7  | Execution Accounting Spec   | ISS_10 = NOT_VERIFIED              | Formula unverified in code     | Execution slippage distortion    | Implement reference-price module   | Approve DEC_05 policy    |
| 8  | Multiple Testing Family K   | 11 assets x strategy variants      | Ambiguity in family size       | Spurious discovery risk          | Conditional K framework            | Approve DEC_04 family    |
| 9  | Primary Asset Universe      | fleet_catalog.json (11 assets)     | XMR has 83K bars vs 316K bars  | Survivorship / liquidity bias    | 10 core assets, 3-tier XMR policy  | Approve DEC_06 policy    |
+----+-----------------------------+------------------------------------+--------------------------------+----------------------------------+------------------------------------+--------------------------+
```

---

## 12. FINAL TRACK READINESS MATRIX

```text
+---------+---------------------------------------------------+------------------------------------+----------------------------------+---------------------------------------------------+
| Track   | Target Alignment Classification                   | OOS Eligibility Status             | Methodology Status               | Remaining Blockers Before Execution               |
+---------+---------------------------------------------------+------------------------------------+----------------------------------+---------------------------------------------------+
| Track 1 | TARGET_ALIGNED (at 12-bar horizon)                | PREVIOUSLY_OBSERVED_VALIDATION_DATA| METHODOLOGY_READY_FOR_HUMAN_REVIEW| None. Ready for consolidated reporting format.    |
| Track 2 | SIGNAL_COMPATIBLE_WITH_SEPARATE_ECONOMIC_ESTIMAND | PREVIOUSLY_OBSERVED_VALIDATION_DATA| METHODOLOGY_REQUIRES_REVISION    | DEC_01 (Alt B), DEC_03, DEC_05, Backtest Engine.  |
| Track 3 | INDEPENDENT_ALPHA_SCORE                           | OOS_ELIGIBILITY_NOT_VERIFIED       | METHODOLOGY_REQUIRES_REVISION    | DEC_01 (Alt C), Sparse Grid Pre-Reg, Banker FSM.  |
+---------+---------------------------------------------------+------------------------------------+----------------------------------+---------------------------------------------------+
```

*Note: Operational readiness for human review does NOT imply authorization to execute.*

---

## 13. SUMMARY OF DOCUMENT CORRECTIONS

The following modifications were executed during this final correction cycle:
1. **Section 1 & 4 (Fold 5 Reclassification):** Changed status from `CONDITIONALLY_ELIGIBLE_FOR_STRATEGY` to `OOS_ELIGIBILITY_NOT_VERIFIED`. Documented that lack of parameter tuning does not establish independent OOS validity due to prior model evaluation and unverified researcher exposure. Prohibited Fold 5 for confirmatory claims.
2. **Section 1, 3 & 6 (Track 2 Reclassification):** Changed classification from `PARTIALLY_ALIGNED` to `SIGNAL_COMPATIBLE_WITH_SEPARATE_ECONOMIC_ESTIMAND`. Added mathematical proof showing that changing the entry reference from `close[i]` to `open[i+1]` fundamentally alters the estimand and decouples predictive calibration from economic outcome.
3. **Section 9 (Hypothesis Family K Framework):** Replaced hardcoded $K=11$ assertions with a conditional hypothesis family table covering $K \in \{1, 10, 11, 20, 22, 33, 11 \times N\}$ tied explicitly to decisions DEC_01, DEC_02, DEC_04, and DEC_06.
4. **Section 7 (Track 3 Holding Range):** Explicitly classified the 6-to-48 bar holding range as `PROVISIONAL_DESIGN_RANGE_NOT_EMPIRICALLY_VALIDATED` and calculated the combinatorial data-mining risk of the 14,400 configuration parameter space.
5. **Section 8 (Funding Scenarios & Cash Flow Sign):** Reconciled parametric funding scenarios ($-3, -1, 0, +1, +3$ bps) and codified signed cash-flow conventions ($CF > 0$ for receipts, $CF < 0$ for payments). Reaffirmed `FUNDING_DATA_UNAVAILABLE` status for canonical historical parquets.

---

## 14. GOVERNANCE DISCLAIMER

This document is a technical methodology audit and experiment design reconciliation.

> [!IMPORTANT]
> **GOVERNANCE STATUS REAFFIRMATION:**  
> - Phase 5.5 Research Status: `NOT_STARTED`  
> - Phase 5.6 Authorization Status: `NOT_AUTHORIZED`  
> - Economic Backtesting Status: `NOT_STARTED`  
> - Decisions DEC_01 through DEC_06: `PENDING_HUMAN_DECISION`  
> - Prospective Holdout Partition: `STRICTLY_SEALED`  
> - Frozen Phase 5.3 Models & Phase 5.4 Preprocessors: `IMMUTABLE`  
>
> No research backtest has been executed. No trading models have been modified. No prospective holdout data has been accessed. No strategy or model is claimed to be profitable. All research operational authorizations remain under the exclusive authority of the Human Governance Supervisor.

---
*End of Final Methodology Reconciliation Audit.*
