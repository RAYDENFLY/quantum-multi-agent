# QUANTUM PHASE 5.5.0: TEMPORAL VALIDATION PROTOCOL

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-01 20:23:18 UTC`  
**Associated Deliverable:** Workstream H (Temporal Validation and Experiment Design)  

---

## 1. TEMPORAL DATA SEGMENTATION & GOVERNANCE

Phase 5.5 strictly preserves the established 3-segment temporal architecture from Phase 5.3 and Phase 5.4:

### Segment Structure
- **Segment 1 (Folds 1-2): Model Training & Baseline Calibration**
  - Historical development data.
  - Used to fit initial models and baseline preprocessors.
- **Segment 2 (Folds 3-4): Decision Policy Threshold Optimization**
  - Validation data used strictly for tuning confidence thresholds $\theta$.
  - Policy selection criterion: Maximum mean net return under 15 bps cost.
- **Segment 3 (Fold 5): Retrospective Historical Evaluation**
  - Historical evaluation fold (264,584 observations across 11 instruments).
  - **Governance Rule:** Fold 5 is classified as **retrospective historical evidence**, NOT a fresh prospective out-of-sample holdout.
  - Thresholds and policy rules optimized on Segment 2 are locked; zero tuning permitted on Fold 5.
- **Prospective Holdout (`2026-11-01` to `2027-04-30`): STRICTLY SEALED**
  - Zero access permitted during Phase 5.5.

---

## 2. PURGING AND EMBARGO PROTOCOL

In financial time series, overlapping prediction horizons create artificial autocorrelation and information leakage.

### Purging Implementation
- Horizon duration: $H = 12$ bars ($60$ minutes).
- For each active trade entering at $t_{\text{entry}}$, all subsequent candle signals from the same instrument during the active holding window $[t_{\text{entry}}, t_{\text{exit}}]$ are **purged** (`PURGED_ACTIVE_TRADE_OVERLAP`).
- No specialist may enter a new position in the same instrument while an existing position is open.

### Embargo Implementation
- Following trade exit at $t_{\text{exit}}$, an embargo window of $E = 12$ bars ($60$ minutes) is enforced before that specialist may open another position.
- This guarantees temporal separation between trade evaluations and prevents serial clustering bias during extreme market runs.
