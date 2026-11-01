# QUANTUM PHASE 5.5.0.5: DEC_01 RESEARCH OBJECTIVE CLARIFICATION

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-01 21:02:03 UTC`  
**Associated Deliverable:** Workstream A (DEC_01 Operational Definition)  

---

## 1. THE CORE RESEARCH OBJECTIVE AMBIGUITY

The prior governance package recommended both Alternative B and Alternative C without clearly distinguishing that they answer two fundamentally different scientific questions:

### Research Objective A: Frozen Classifier Economic Validation (Alternative B)
- **Core Scientific Question:** Does the frozen Phase 5.3 B4 LightGBM triple-barrier classifier possess genuine economic predictive alpha when fills occur at realistic market open prices?
- **Methodological Role:** Direct validation of the machine learning model. Tests whether the model's calibrated probabilities $P(+1), P(0), P(-1)$ generate positive net expected returns when evaluated on symmetric volatility brackets re-anchored to the entry fill $P_{\text{entry}} = \text{open}[i+1] \pm 1.5\sigma_t P_{\text{entry}}$.
- **Key Constraint:** Zero parameter tuning. Preserves frozen model binaries, preprocessors, and evaluation boundaries.
- **Limitation:** Re-anchoring barriers to $P_{\text{entry}}$ means economic outcomes will occasionally diverge from historical label outcomes if a large price gap occurs between $\text{close}[i]$ and $\text{open}[i+1]$.

### Research Objective B: Independent Trading Strategy Development (Alternative C)
- **Core Scientific Question:** Can the frozen classifier act as an effective directional signal filter within a separately engineered systematic trading strategy?
- **Methodological Role:** Algorithmic trading engineering. Decouples the classifier from static triple-barrier rules. Allows implementing trailing stops, time-decay exits, volatility targeting, or dynamic limits.
- **Key Constraint:** Introduces new strategy parameters (e.g. trailing stop distance, profit targets, max holding period). These parameters must be calibrated strictly on Folds 1 to 4, with Fold 5 held out as an un-tuned test period.
- **Limitation:** Cannot be presented as direct validation of the frozen triple-barrier target labels. If the strategy succeeds, it is unclear whether alpha came from the ML classifier or the exit policy heuristics.

---

## 2. COMPREHENSIVE COMPARISON MATRIX ACROSS 12 DIMENSIONS

| Dimension | Alternative B (Frozen Target Validation) | Alternative C (Independent Strategy Track) |
|---|---|---|
| **1. Research Hypothesis** | The frozen ML classifier provides positive economic expectancy under symmetric barrier execution. | The frozen ML classifier can serve as an effective directional filter for a multi-parameter trade management system. |
| **2. Estimand** | Net return of fixed symmetric $1.5\sigma_t$ barrier brackets. | Net return of an independent algorithmic exit policy. |
| **3. Entry Mechanics** | Market order at $t_{\text{open}}[i+1]$ adjusted by adverse slippage $C_{\text{exec}}$. | Market or limit order at $t_{\text{open}}[i+1]$ with execution heuristics. |
| **4. Exit Mechanics** | First touch of re-anchored $P_{\text{entry}}(1 \pm 1.5\sigma_t)$ or 12-bar expiration. | Trailing stops, ATR dynamic bands, time-decay, or volatility scaling. |
| **5. Label Dependency** | High: Directly evaluates the triple-barrier concept. | Low: Uses classifier probabilities only as a directional trigger. |
| **6. Frozen Artifact Dependency** | 100% frozen B4 models and preprocessors. | 100% frozen B4 models; introduces new exit parameters. |
| **7. Parameter Selection Needs** | Zero new parameters. | High: Trailing multipliers, holding periods, profit targets. |
| **8. Look-Ahead Bias Risk** | Zero. | Zero if and only if parameters are fit on Folds 1-4 only. |
| **9. Validation Leakage Risks** | None: Directly evaluates historical OOF predictions. | High if parameters are tuned using Fold 5 data. |
| **10. Interpretation of Results** | Clean: Confirms or refutes economic validity of Phase 5.3 ML models. | Confounded: Conflates classifier skill with trade exit engineering. |
| **11. Research Complexity** | Low to Moderate: Immediate, deterministic evaluation. | High: Multi-parameter walk-forward optimization protocol required. |
| **12. Reproducibility** | Exact bit-for-bit reproducibility across all folds. | Sensitive to exit policy parameter grid definitions. |

---

## 3. STRUCTURAL RELATIONSHIP & SUPERVISOR RECOMMENDATION

### Are Alternative B and Alternative C Mutually Exclusive?
- They are NOT mutually exclusive if structured as **Sequential Research Tracks**:
  - **Track 1 (Mandatory Baseline):** Execute Alternative B first to establish whether the raw frozen ML classifier has positive economic alpha after realistic execution costs.
  - **Track 2 (Exploratory Extension):** If and only if Track 1 completes, execute Alternative C as an exploratory downstream trading strategy experiment with strict parameter holdout rules.
- Presenting Alternative C as the sole evaluation of Phase 5.5 risks obscuring model failure behind aggressive trade management heuristics.

### Operational Recommendation for Supervisor
- Select `Alternative B` as the primary Phase 5.5 validation architecture.
- Authorize `Alternative C` strictly as a secondary, decoupled exploratory track in Phase 5.5.2.
- Status: `PENDING_HUMAN_DECISION`. The supervisor retains sole authority to choose.
