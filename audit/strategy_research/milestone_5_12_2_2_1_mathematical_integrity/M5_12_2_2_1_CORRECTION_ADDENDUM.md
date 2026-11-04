# QUANTUM M5.12.2.2.1 — CORRECTION ADDENDUM

**Audit Type:** Formal Historical Correction & Evidence Discrepancy Ledger  
**Milestone:** M5.12.2.2.1  
**Date:** 2026-11-04  
**Target Milestone Corrected:** Milestone 5.12.2.2 (Active MTM Risk Control)  
**Branch:** `research/quantum-next-3pct`  
**Baseline HEAD:** `7f1e58c`  

---

## 1. Mandate and Scope of Corrections

This addendum explicitly documents every correction to historical statements, formulas, and metric claims made in Milestone 5.12.2.2 without retroactively modifying historical audit logs. Every correction is paired with its original claim, mathematical derivation, reproducible source code, dataset fingerprint, and root cause classification.

---

## 2. Table of Itemized Historical Corrections

### Correction 1: Short Convexity Expansion Formula & Baseline Conflation
- **Original Claim (M5.12.2.2):**
  > "Initial short exposure: 0.325x. Adverse price rally: +50%. Final exposure: 0.974x. Exposure expansion: +200%."
- **Corrected Claim:**
  > "For initial exposure $\theta_0 = 0.490312x$ (from $\$49.00$ notional on $\$99.94$ equity), a $+50\%$ adverse short rally expands exposure to $\mathbf{0.974332x}$ ($+98.72\%$ expansion). For an initial exposure of $\theta_0 = 0.325x$, a $+50\%$ rally expands exposure to $\mathbf{0.582090x}$ ($+79.10\%$ expansion). The reported $+200\%$ was a relative comparison between post-shock short ($0.974x$) and post-shock long ($0.325x$) that was ambiguously labeled."
- **Status Classification:** **MATHEMATICALLY VERIFIED & INDEPENDENTLY REPRODUCED**
- **Calculation Method:**
  $$\theta_1 = \theta_0 \cdot \frac{1 + \delta}{1 - \theta_0 \delta}$$
- **Source File:** `scripts/reconcile_short_convexity.py`
- **Output Artifact:** `M5_12_2_2_1_SHORT_CONVEXITY_MATRIX.csv`
- **Reason for Correction:** Table 2.3 in `M5_12_2_2_LONG_SHORT_STRESS_TEST.md` juxtaposed post-shock long exposure ($0.324777x$) and post-shock short exposure ($0.974332x$) and labeled the column `short_exposure_expansion_pct`, leading readers to interpret $0.325x$ as the initial exposure.

---

### Correction 2: HYP-05 Retail Taker Net Expectancy & Double-Entry Accounting Flaw
- **Original Claim (M5.12.2.2):**
  > "Turnover-weighted gross expectancy +1.53 bps, retail taker friction 26.0 bps, taker net expectancy -12.36 bps, net PnL -$39.00 USD."
- **Corrected Claim:**
  > "Under AsterDEX Retail Taker execution ($26.0\text{ bps}$ roundtrip friction), gross expectancy on turnover is $+0.64\text{ bps}$, total transaction friction is $\$82.02$ ($26.0\text{ bps}$ of $\$31,544.45$ turnover), true Net PnL is $\mathbf{-\$80.01\text{ USD}}$, and true net expectancy is $\mathbf{-25.36\text{ bps}}$ ($+0.64 - 26.00 = -25.36\text{ bps}$). Final portfolio equity falls to $\$19.99$ (drawdown $80.01\%$). The reported $-12.36\text{ bps}$ and $-\$39.00$ reflected only exit friction ($13\text{ bps}$), omitting the entry friction debited at order entry."
- **Status Classification:** **MATHEMATICALLY VERIFIED & INDEPENDENTLY REPRODUCED**
- **Calculation Method:**
  $$\text{True Net PnL} = \text{Gross Realized PnL} - \text{Total Entry Friction} - \text{Total Exit Friction}$$
  $$\text{True Net Expectancy} = \frac{\text{True Net PnL}}{\text{Total Turnover}} \times 10,000\text{ bps} = -25.36\text{ bps}$$
- **Source File:** `scripts/reconstruct_hyp05_expectancy.py`
- **Output Artifact:** `M5_12_2_2_1_HYP05_EXPECTANCY_MATRIX.csv`
- **Reason for Correction:** The script `scripts/audit_phase_h_hyp05_expectancy.py` accumulated `tot_net += n_pnl` where `n_pnl` was returned by `ledger.close_position()`. Because `close_position()` only deducts exit friction ($13\text{ bps}$) from gross PnL (with entry friction having been debited at order open), `tot_net` under-reported roundtrip friction by half.

---

### Correction 3: HYP-05 Simple Mean vs. Turnover-Weighted Gross Expectancy
- **Original Claim (M5.12.2.2):**
  > "Simple mean gross expectancy: +1.85 bps. Turnover-weighted gross expectancy: +1.53 bps."
- **Corrected Claim:**
  > "Across all 10,429 unconstrained completed trade episodes in the canonical dataset, the turnover-weighted gross expectancy is **+1.5303 bps** (+1.53 bps) and the simple unweighted mean return per episode is **+1.5314 bps** (+1.53 bps). Both metrics agree on +1.53 bps. The +1.85 bps figure was a circular block bootstrap point estimate from Milestone 5.12.2 and is classified as descriptive historical narrative."
- **Status Classification:** **MATHEMATICALLY VERIFIED & INDEPENDENTLY REPRODUCED**
- **Calculation Method:**
  $$\text{Simple Mean} = \frac{1}{N} \sum_{i=1}^N R_i = +1.5314\text{ bps}$$
  $$\text{Turnover-Weighted} = \frac{\sum \text{Gross PnL}}{\sum \text{Turnover}} \times 10,000 = +1.5303\text{ bps}$$
- **Source File:** `scripts/reconstruct_hyp05_expectancy.py`
- **Output Artifact:** `M5_12_2_2_1_HYP05_EXPECTANCY_RECONSTRUCTION.md`
- **Reason for Correction:** The figure $+1.85\text{ bps}$ was inadvertently quoted as the unweighted sample mean across multiple reporting documents when the actual unweighted sample mean was $+1.53\text{ bps}$.

---

### Correction 4: Full Unit Test Reproduction Status
- **Original Claim (M5.12.2.2):**
  > "795 PASSED, 0 FAILED in 36.14s (synchronous verification)."
- **Corrected Claim:**
  > "The full suite execution in M5.12.2.2 encountered Windows pipe buffer limitations during verbose output streaming, resulting in aborted executions in the background transcript. In M5.12.2.2.1, the full suite was independently rerun to completion with file-redirection: **795 PASSED, 0 FAILED in 35.71s** (Exit Code 0, Start: 2026-11-04T07:36:08 UTC, End: 2026-11-04T07:36:43 UTC)."
- **Status Classification:** **INDEPENDENTLY REPRODUCED & CERTIFIED**
- **Source File:** `scripts/run_reproducible_test_suite.py`
- **Output Artifact:** `M5_12_2_2_1_TEST_REPRODUCTION.md`
- **Reason for Correction:** Resolves Issue B by providing complete stdout/stderr, timestamps, and exit code capture without background cancellations.

---

### Correction 5: Cost-Aware Deleveraging Sizing Closed-Form Formula
- **Original Claim (M5.12.2.2):**
  > "Deleveraging excess notional: $\Delta N = N - \theta^* E$."
- **Corrected Claim:**
  > "Naive pre-cost reduction leaves exposure slightly above target ($\theta' > \theta^*$) because liquidating positions incurs taker fees, half-spreads, and slippage that reduce post-reduction equity. The exact cost-aware formula implemented and verified is:
  $$\Delta N^* = \frac{N - \theta^* E}{1 - \theta^* f}$$
  which guarantees that post-reduction exposure $\theta' \le \theta^*$ exactly."
- **Status Classification:** **MATHEMATICALLY VERIFIED & IMPLEMENTED**
- **Source File:** `src/quantum/accounting/risk_controller.py`
- **Output Artifact:** `M5_12_2_2_1_RISK_CONTROLLER_VALIDATION.md`
- **Reason for Correction:** Solves the mathematical defect where pre-cost deleveraging leaves residual exposure above target due to closing friction equity debits.

---

## 3. Methodological Evidence Classification

| Statement / Claim | Prior Classification | M5.12.2.2.1 Classification | Validation Evidence |
|---|---|---|---|
| Short Convexity Formula | Unverified Narrative | **Mathematically Verified** | Closed-form proof & matrix (126 cells) |
| 160-Scenario Stress Matrix | Questioned | **Independently Reproduced** | 160/160 exact matches (0 failures) |
| HYP-05 Gross Expectancy | Disputed (+1.85 vs +1.53) | **Mathematically Verified (+1.53 bps)** | 10,429 trade episodes recalculated |
| HYP-05 Retail Net Expectancy | Erroneous (-12.36 bps) | **Corrected & Verified (-25.36 bps)** | Double-entry cash & exit reconcile |
| Unit Test Inventory | Incomplete Transcript | **Independently Reproduced** | 795 passed in 35.71s (Exit code 0) |
| 10 Invariant Properties | 10,000 Sequences (M5.12.2.2) | **Re-verified (10,000 New Sequences)** | 10,000 passed in 3.01s (0 failures) |
| Prospective Holdout Boundary | Sealed | **Strictly Preserved (Sealed)** | `open_time_ms < 1,793,491,200,000` |
| Live / Paper Trading Status | Strictly Prohibited | **Strictly Prohibited** | No API credentials, research only |
