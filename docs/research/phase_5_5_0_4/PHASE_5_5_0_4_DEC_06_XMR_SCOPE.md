# QUANTUM PHASE 5.5.0.4: DEC_06 XMR RESEARCH & PORTFOLIO SCOPE BRIEF

**Decision ID:** `DEC_06`  
**Title:** XMRUSDT Research and Portfolio Eligibility  
**Governance Status:** `PENDING_HUMAN_DECISION`  
**Execution Blocking:** `YES`  

---

## 1. DATA DEFICIT AUDIT & EMPIRICAL REALITY

Forensic metadata audit reveals a fundamental asymmetry between XMR and the rest of the fleet:
- **10 Fleet Specialists:** Possess 316,500 5m candles spanning 1,100 days (October 2023 through October 2026 across Folds 1 to 5).
- **XMRUSDT Specialist:** Possesses only **83,863 candles** spanning 291 days (`2026-01-13` to `2026-10-31`, 2026 calendar year only).
- **Missing History:** XMR has ZERO data in Folds 1 to 4.
- **Class Support Deficit:** In Fold 5 at 20% coverage tier, XMR possesses only **1 minority-class sample**, rendering selective risk curves unidentifiable.

---

## 2. SEPARATION OF MODEL PRESERVATION FROM PORTFOLIO ELIGIBILITY

To prevent conflating model integrity with portfolio inclusion, Phase 5.5 establishes three distinct policy tiers:
1. **Tier 1: Model Artifact Preservation (100% PRESERVED):** All 5 frozen LightGBM binaries and 5 preprocessors in `artifacts/phase_5_3_1/XMRUSDT/` remain permanent, immutable artifacts. They will NEVER be deleted or retrained.
2. **Tier 2: Specialist Research Eligibility (PRESERVED WITH CAVEATS):** Single-instrument ML research and diagnostics on XMR can continue with documented caveats.
3. **Tier 3: Economic Portfolio Validation Eligibility (PENDING HUMAN DECISION):** The supervisor must decide whether XMR should be included in the primary multi-asset portfolio evaluation.

### Options for DEC_06
- **Option 1: Exclude XMR from Primary Economic Portfolio:** Evaluate primary portfolio metrics (Gates 7 to 12) strictly on the 10-asset fleet with full 1,100-day histories. Report XMR standalone economic performance in an isolated appendix.
- **Option 2: Include XMR in Primary Portfolio:** Combine 1,100-day histories with 291-day history, accepting ragged covariance matrices and unaligned time series.

---

## 3. SUPERVISOR RECOMMENDATION

- **Recommendation:** Approve `Option 1 (Exclude XMR from primary portfolio validation; report in isolated appendix)`. This preserves scientific rigor by preventing a single-year data deficit from distorting multi-year portfolio backtesting statistics.
- **Status:** `PENDING_HUMAN_DECISION`. Awaiting supervisor selection.
