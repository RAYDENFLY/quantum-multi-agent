# QUANTUM PHASE 5.5.0.2: XMR RESEARCH ELIGIBILITY POLICY

**Document Status:** `PENDING_HUMAN_DECISION`  
**Publication Timestamp:** `2026-11-01 20:41:45 UTC`  
**Associated Deliverable:** Workstream E (XMR Research Eligibility)  

---

## 1. EMPIRICAL DATA DEFICIT AUDIT

Forensic audit of [`data/historical/canonical/`](file:///d:/quantum-multi-agent/data/historical/canonical/) establishes:
- **10 Fleet Specialists:** Possess 316,500 candles spanning 1,100 days (October 2023 through October 2026).
- **XMRUSDT Specialist:** Possesses only **83,863 candles** spanning 291 days (`2026-01-13` to `2026-10-31`).
- **Class Support Deficit:** In Fold 5 at 20% coverage tier, XMR possesses only **1 minority-class sample**, rendering selective risk curves unidentifiable.

---

## 2. THREE-TIER ELIGIBILITY CLASSIFICATION

To prevent conflating model integrity with portfolio inclusion, Phase 5.5.0.2 establishes three distinct tiers:

### Tier 1: Model Artifact Preservation (100% PRESERVED)
- All 5 frozen LightGBM binaries and 5 preprocessors in `artifacts/phase_5_3_1/XMRUSDT/` remain 100% bit-for-bit intact.
- No retraining, deletion, or modification is permitted.

### Tier 2: Specialist Research Eligibility (PRESERVED WITH CAVEATS)
- XMRUSDT remains an eligible specialist for standalone ML research and single-instrument diagnostics.
- All statistical findings must prominently document the 291-day calendar limitation and class support deficit.

### Tier 3: Economic Portfolio Validation Eligibility (PENDING HUMAN DECISION)
- **Recommendation:** `EXCLUDED_FROM_PRIMARY_PORTFOLIO_VALIDATION`.
- **Rationale:** Combining 1,100 days of data for 10 assets with 291 days for XMR creates an unaligned multi-asset covariance matrix and distorts portfolio drawdowns.
- **Reporting Protocol:** Primary portfolio metrics (Gates 7-12) will be evaluated on the 10-asset fleet (BTC, ETH, BNB, XRP, ADA, SOL, AVAX, LINK, DOGE, LTC). XMR economic performance will be reported separately in an isolated appendix.
