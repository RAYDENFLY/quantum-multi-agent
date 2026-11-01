# QUANTUM PHASE 5.4: ACCEPTANCE CRITERIA & GATE GOVERNANCE
**Measurable Gate Thresholds, Diagnostic Standards & Phase Closure Contract**

**Document Version:** 5.4.0_CRITERIA  
**System:** QUANTUM 11-Specialist Cryptocurrency Perpetual Futures ML Trading Research System  
**Governance Status:** `CRITERIA_CONTRACT_AWAITING_EXPLICIT_AUTHORIZATION`  
**Classification Standards:** `VERIFIED_FROM_SOURCE` | `VERIFIED_FROM_ARTIFACT` | `DOCUMENTATION_ONLY`

---

## 1. Executive Gate Architecture

To prevent subjective or premature declaration of success, Phase 5.4 establishes formal, measurable criteria partitioned into **Hard Gates** (which must pass 100% for phase closure) and **Diagnostic Metrics** (which provide qualitative characterization).

Passing Phase 5.4 indicates solely that:
$$\text{Model Probabilities and Decision Policies Are Sufficiently Reliable to Proceed to Historical Backtesting (Phase 5.5)}$$

Passing Phase 5.4 does **NOT** constitute proof of live trading profitability or authorization for capital deployment.

---

## 2. Hard Gate Requirements (Mandatory for Closure)

| Gate ID | Domain | Metric / Verification Standard | Acceptance Threshold | Measurement Segment | Justification & Failure Consequence |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **GATE-5.4-01** | Data Provenance | Bit-Exact Inference Verification | **100% Hash Match** | All 55 Folds | Computed $P_{\text{raw}}$ hashes must match historical `proba_hash` in `predictions.json`. Failure = Code defect. |
| **GATE-5.4-02** | Temporal Isolation | Zero Leakage Across Segments | **100% Compliant** | Entire Pipeline | Zero calibrator fitting or threshold tuning permitted on Segment 3 (Fold 5). Failure = Invalidation of study. |
| **GATE-5.4-03** | Holdout Protection | Prospective Holdout Boundary Isolation | **0 Observations** | `2026-11-01` to `2027-04-30` | Absolute zero queries or reads to prospective holdout partition. Failure = Governance breach. |
| **GATE-5.4-04** | Calibration Quality | Expected Calibration Error Reduction | **$\text{ECE}_{\text{cal}} < \text{ECE}_{\text{raw}}$** | Segment 3 (Fold 5) | Calibrated probabilities must improve ECE over raw Softmax on unseen temporal data for $\ge 9/11$ instruments. |
| **GATE-5.4-05** | Probabilistic Score | Multiclass Brier Score Improvement | **$\text{BS}_{\text{cal}} \le \text{BS}_{\text{raw}}$** | Segment 3 (Fold 5) | Calibration must not degrade mean squared probability error on $\ge 10/11$ instruments. |
| **GATE-5.4-06** | Selective Monotonicity | Risk-Coverage Curve Positive Slope | **$\text{BA}_{\text{sel}}(30\%) > \text{BA}_{\text{sel}}(100\%)$** | Segment 3 (Fold 5) | Selective Balanced Accuracy at 30% coverage must exceed full coverage by $\ge 2.0\%$ points for $\ge 9/11$ instruments. |
| **GATE-5.4-07** | Economic Expectancy | Positive Net Expectancy at High Conviction | **$\mathbb{E}[R_{\text{net}}] > 0.0$** | Segment 3 (Fold 5) | Selected trades at target coverage (e.g. 30%) must have positive expected return after deducting 15 bps friction. |
| **GATE-5.4-08** | Temporal Stability | OOS Performance Degradation Bound | **$\Delta\text{BA}_{\text{sel}} < 15\%$** | Segment 3 vs Segment 2 | Selective BA on Segment 3 must not degrade by more than 15% relative to Segment 2 tuning performance. |
| **GATE-5.4-09** | Resource Budget | Peak Memory & Thread Caps | **$< 1$ GB RAM, $\le 2$ Threads** | Entire Execution | Execution must conform strictly to system resource bounds on standard CPU hardware. |
| **GATE-5.4-10** | Reproducibility | Deterministic Replay & Cryptographic Audit | **100% Match** | All Deliverables | Re-running execution script with `RANDOM_SEED=42` must produce bit-exact identical metrics and hashes. |

---

## 3. Diagnostic Metrics (Characterization Standards)

Diagnostic metrics inform qualitative trade-offs but do not constitute binary blockers:

1. **Temperature Parameter Stability ($T$):**
   - Ideal: $T \in [0.8, 2.5]$.
   - Diagnostic Value: $T > 3.0$ indicates extreme tree overconfidence; $T < 0.5$ indicates extreme underconfidence.
2. **Reliability Diagram Visual Flatness:**
   - Visual inspection of calibration curves across 15 bins.
   - Maximum deviation in any single bin: $< 0.10$.
3. **Directional Coverage Balance:**
   - Ratio of LONG trade candidates to SHORT trade candidates:
     $$\text{Ratio}_{\text{dir}} = \frac{N_{\text{LONG}}}{N_{\text{SHORT}}}$$
   - Healthy range: $\text{Ratio}_{\text{dir}} \in [0.5, 2.0]$. Values outside this range indicate severe directional asymmetry.
4. **Regime-Conditional Calibration Degradation:**
   - Difference in ECE between high-volatility and low-volatility regimes:
     $$\Delta\text{ECE}_{\text{vol}} = |\text{ECE}_{\text{high}} - \text{ECE}_{\text{low}}|$$
   - Healthy threshold: $\Delta\text{ECE}_{\text{vol}} < 0.05$.

---

## 4. Failure Modes & Remediations

| Failure Mode | Root Cause | Permitted Remediation | Prohibited Action |
| :--- | :--- | :--- | :--- |
| **Isotonic Overfitting on Segment 3** | Non-parametric step function overfit to Segment 1 noise. | Fallback to Temperature Scaling or Vector Platt Scaling. | Modifying Segment 3 boundaries or fitting on Segment 3. |
| **Selective BA Fails to Improve at Low Coverage** | Model confidence does not correlate with true class margin. | Reject selective classifier; declare confidence filter non-viable for trading. | Lowering coverage to $< 10\%$ to manufacture artificial lift. |
| **Negative Net Expectancy after 15 bps Friction** | Barrier distance ($1.5 \times \text{ATR}$) too small relative to exchange fees. | Increase minimum conviction threshold $\tau$ or filter out low-volatility regimes. | Artificially reducing fee assumptions below exchange schedule. |
| **XMR Data Scarcity Failure** | 15,252 OOF bars insufficient for robust binning. | Tag XMR as `INSUFFICIENT_DATA_EXCLUDED` from fleet aggregate gates. | Pooling XMR with BTC or ETH data without hypothesis. |
