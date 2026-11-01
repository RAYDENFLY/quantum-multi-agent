# QUANTUM PHASE 5.4: ACCEPTANCE CRITERIA & GATE GOVERNANCE
**Measurable Gate Thresholds, Diagnostic Standards & Phase Closure Contract**

**Document Version:** 5.4.1_CRITERIA  
**System:** QUANTUM 11-Specialist Cryptocurrency Perpetual Futures ML Trading Research System  
**Governance Status:** `CRITERIA_CONTRACT_AWAITING_EXPLICIT_AUTHORIZATION`  
**Classification Standards:** `VERIFIED_FROM_SOURCE` | `VERIFIED_FROM_ARTIFACT` | `DOCUMENTATION_ONLY`

---

## 1. Executive Gate Architecture

To prevent subjective or premature declaration of success, Phase 5.4 establishes formal, measurable criteria partitioned into **Hard Gates** (which must pass 100% for phase closure) and **Diagnostic Metrics** (which provide qualitative characterization).

Passing Phase 5.4 indicates solely that:
$$\text{Model Probabilities and Decision Policies Are Sufficiently Reliable to Proceed to Historical Backtesting (Phase 5.5)}$$

Realized portfolio net PnL, dollar returns, cumulative equity curves, Sharpe ratio, and drawdown are explicitly excluded from Phase 5.4 and governed by Phase 5.5.

---

## 2. Revised Hard Gate Requirements (Mandatory for Closure)

| Gate ID | Domain | Metric / Verification Standard | Acceptance Threshold | Measurement Segment | Justification & Failure Consequence |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **GATE-5.4-01** | Data Provenance | Bit-Exact Inference Verification | **100% Hash Match** | All 55 Folds | Computed $P_{\text{raw}}$ hashes must match historical `proba_hash` in `predictions.json`. Failure = Code defect. |
| **GATE-5.4-02** | Temporal Isolation | Zero Leakage Across Segments | **100% Compliant** | Entire Pipeline | Verified 13-bar purge gap. Zero calibrator fitting or threshold tuning permitted on Segment 3. Failure = Invalid study. |
| **GATE-5.4-03** | Holdout Protection | Prospective Holdout Boundary Isolation | **0 Observations** | `2026-11-01` to `2027-04-30` | Absolute zero queries or reads to prospective holdout partition. Failure = Governance breach. |
| **GATE-5.4-04** | Calibration Quality | Expected Calibration Error Reduction | **$\text{ECE}_{\text{cal}} < \text{ECE}_{\text{raw}}$** | Segment 3 (Fold 5) | Calibrated probabilities must improve ECE over raw Softmax on unseen temporal data for $\ge 9/11$ instruments. |
| **GATE-5.4-05** | Probabilistic Score | Multiclass Brier Score Improvement | **$\text{BS}_{\text{cal}} \le \text{BS}_{\text{raw}}$** | Segment 3 (Fold 5) | Calibration must not degrade mean squared probability error on $\ge 10/11$ instruments. |
| **GATE-5.4-06** | Selective Monotonicity | Monotonic Risk-Coverage Curve | **$\beta_{\text{RC}} > 0$ across Grid** | Segment 3 (Fold 5) | Error rate must decrease as coverage decreases across {100%, 80%, 60%, 40%, 20%}, with $N_c \ge 100$ per class. |
| **GATE-5.4-07** | Policy Stability | Directional Filter Non-Degeneracy | **Non-Empty & Balanced** | Segment 3 (Fold 5) | Cost-sensitive filter must produce trades in both directions (LONG/SHORT ratio $\in [0.33, 3.0]$) without class collapse. |
| **GATE-5.4-08** | Temporal Stability | OOS Performance Degradation Bound | **$\Delta\text{BA}_{\text{sel}} < 15\%$** | Segment 3 vs Segment 2 | Selective BA on Segment 3 must not degrade by more than 15% relative to Segment 2 tuning performance. |
| **GATE-5.4-09** | Resource Budget | Peak Memory & Thread Caps | **$< 1$ GB RAM, $\le 2$ Threads** | Entire Execution | Execution must conform strictly to system resource bounds on standard CPU hardware. |
| **GATE-5.4-10** | Reproducibility | Deterministic Replay & Cryptographic Audit | **100% Match** | All Deliverables | Re-running execution script with `RANDOM_SEED=42` must produce bit-exact identical metrics and hashes. |

---

## 3. Revised Diagnostic Metrics

1. **Selective Classification Lift over Random Abstention:**
   - 95% bootstrap confidence interval of $\text{BA}_{\text{sel}}(\text{cov})$ must exceed the random abstention baseline.
2. **Per-Class Support Floor:**
   - Minimum $N_{\text{covered}, c} \ge 100$ for all classes $c \in \{-1, 0, 1\}$ at target evaluation coverage.
3. **Friction Sensitivity Breakeven:**
   - Identification of the maximum round-trip friction $C_{\text{crit}}$ at which expected net return becomes negative.
4. **Temperature Parameter Stability:**
   - $T \in [0.8, 2.5]$ indicates healthy calibration scaling.
5. **Reliability Diagram Visual Flatness:**
   - Visual inspection of calibration curves across 15 bins; maximum deviation in any single bin: $< 0.10$.

---

## 4. Failure Modes & Remediations

| Failure Mode | Root Cause | Permitted Remediation | Prohibited Action |
| :--- | :--- | :--- | :--- |
| **Isotonic Overfitting on Segment 3** | Non-parametric step function overfit to Segment 1 noise. | Fallback to Temperature Scaling or Vector Platt Scaling. | Modifying Segment 3 boundaries or fitting on Segment 3. |
| **Selective BA Fails to Improve at Low Coverage** | Model confidence does not correlate with true class margin. | Reject selective classifier; declare confidence filter non-viable for trading. | Lowering coverage to $< 10\%$ to manufacture artificial lift. |
| **Class Collapse at Low Coverage** | Classifier predicts only majority class and drops minority classes below 100 samples. | Enforce minimum class support guardrail $N_c \ge 100$. | Ignoring minority class recall degradation. |
| **XMR Data Scarcity Failure** | 15,252 OOF bars insufficient for robust 15-bin estimation. | Tag XMR as `INSUFFICIENT_DATA_EXCLUDED` from fleet aggregate gates. | Pooling XMR with BTC or ETH data without hypothesis. |
