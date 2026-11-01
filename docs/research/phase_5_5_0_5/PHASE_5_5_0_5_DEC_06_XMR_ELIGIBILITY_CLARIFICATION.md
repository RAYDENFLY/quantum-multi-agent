# QUANTUM PHASE 5.5.0.5: DEC_06 XMR ELIGIBILITY CLARIFICATION

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-01 21:02:03 UTC`  
**Associated Deliverable:** Workstream F (DEC_06 XMR Scope Clarification)  

---

## 1. THREE-TIER POLICY SEPARATION

To prevent confusing model preservation with portfolio aggregation, Phase 5.5 establishes three distinct tiers:
1. **Tier 1: Research Artifact Preservation (100% PRESERVED):** All 5 frozen LightGBM binaries and 5 preprocessors in `artifacts/phase_5_3_1/XMRUSDT/` remain permanent, immutable artifacts. They will never be retrained or deleted.
2. **Tier 2: Individual Specialist Evaluation (STANDALONE ONLY):** Standalone Fold 5 single-instrument research and diagnostics are fully permitted, with mandatory disclosure of the 291-day calendar limitation.
3. **Tier 3: Primary Multi-Asset Portfolio Eligibility (DEC_06):** The supervisor must decide whether XMR enters the primary portfolio aggregation engine (Gates 7 to 12).

---

## 2. STATISTICAL UNRELIABILITY OF INCLUDING XMR IN PORTFOLIO BOOTSTRAP

- **Data Length Disparity:** 10 fleet assets have 316,500 candles across 1,100 days (Folds 1 to 5). XMR has only 83,863 candles across 291 days (Fold 5 only).
- **Ragged Covariance Matrix:** For Folds 1 to 4 (October 2023 to January 2026), XMR returns are completely missing. Any synchronized multi-asset block bootstrap would suffer undefined cross-asset returns or artificial zero padding.
- **Distorted Portfolio Metrics:** Including an 11th asset that only exists during the final 26% of the backtest period distorts Sharpe ratios, Sortino ratios, and maximum drawdown calculations.
- **Class Support Deficit:** In Fold 5 at 20% coverage, XMR possesses only **1 minority-class sample**, making selective classification risk curves unidentifiable.

---

## 3. REPORTING POLICY & SUPERVISOR RECOMMENDATION

- **Primary Portfolio Universe:** Evaluate Gates 7 to 12 strictly on the 10 aligned fleet assets (BTC, ETH, BNB, XRP, ADA, SOL, AVAX, LINK, DOGE, LTC).
- **Isolated Appendix:** Report XMR's standalone economic metrics in a dedicated appendix without contaminating the portfolio statistics.
- **Supervisor Recommendation:** Approve `Option 1 (Exclude XMR from primary portfolio validation; report in isolated appendix)`.
- **Status:** `PENDING_HUMAN_DECISION`.
