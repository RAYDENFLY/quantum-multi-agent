# QUANTUM PHASE 5.5.0.8: STATISTICAL INFERENCE SPECIFICATION

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-01 21:25:00 UTC`  
**Associated Task:** Task D (Statistical Inference Specification)  
**Operational Mode:** `READ_ONLY_QUANTITATIVE_SPECIFICATION_AUDIT`  

---

## 1. BOOTSTRAP DEPENDENCE AUDIT & OVERLAPPING TRADES (D1)

Phase 5.5.0.6 specifies a Paired Moving Block Bootstrap (MBB) with block length $b = 24$ bars (2 hours) and 10,000 resamples.

### The Overlapping Holding Horizon Limitation
- In QUANTUM's triple-barrier design, trade holding horizons reach up to **288 bars (24 hours)**.
- When trades remain open for 144 to 288 bars, multiple trades in sequence or open concurrently across assets share underlying market price movements.
- Resampling with a 24-bar block length breaks temporal price trajectory continuity, artificially destroying the serial autocorrelation of trades with multi-hour holding durations.

### Candidate Statistical Resolutions
1. **Resolution A (Calendar-Time Continuous Portfolio MBB):**
   - Transform trade outcomes into a continuous 5-minute portfolio return time series: $R_{\text{port}}[t]$.
   - Resample blocks of continuous calendar time with block length $b = 288$ bars ($24$ hours).
   - This automatically preserves trade overlap, cross-asset correlation, and macro market shocks.
2. **Resolution B (Trade-Level Clustered Block Bootstrap):**
   - Resample trades in clusters where block length is scaled to the maximum trade duration: $b_{\text{trade}} = \lceil 288 / \bar{H} \rceil$, where $\bar{H}$ is mean holding bars.
3. **Paired Alignment Requirement:**
   - Both candidate policy and baseline policy must be resampled using **identical bootstrap index sets** to preserve paired trade differences: $\Delta_m = R_{\text{cand}, m} - R_{\text{base}, m}$.

---

## 2. MULTIPLE-TESTING FAMILY SPECIFICATION (D2)

Phase 5.5 must resolve the hypothesis family size $K$ for Holm-Bonferroni correction:

### The Three Candidate Family Structures
- **Confirmatory Family ($K = 11$):** Evaluates the 11 specialist models on Combined direction at the baseline 20 bps cost tier. This tests the core scientific question: *Does the specialist fleet demonstrate positive net expectancy?*
- **Directional Family ($K = 33$):** Evaluates 11 assets $\times$ 3 directions (Long, Short, Combined) at 20 bps.
- **Full Scenario Family ($K = 99$):** Evaluates 11 assets $\times$ 3 directions $\times$ 3 cost tiers (15, 20, 30 bps).

### Recommended Two-Tier Testing Architecture
1. **Primary Confirmatory Tier ($K = 11$):** Apply Holm-Bonferroni strictly across the 11 specialist models at the baseline 20 bps scenario. This avoids severe loss of statistical power from inflating $K$.
2. **Secondary Exploratory Tier ($K = 33$ and $K = 99$):** Report directional and scenario sweeps as sensitivity diagnostics with nominal and unadjusted p-values clearly marked.
3. **Governance Status:** `PENDING_HUMAN_DECISION` (To be confirmed by supervisor on DEC_04/DEC_02).

---

## 3. STATISTICAL INFERENCE SPECIFICATION MATRIX (D4)

| Statistical Issue | Existing Phase 5.5.0.6 Specification | Identified Limitation | Recommended Candidate Resolution | Human Decision Required |
|---|---|---|---|---|
| **Block Length** | $b = 24$ bars (2 hours) | Underestimates autocorrelation for 144 to 288-bar trades. | Calendar-time portfolio MBB with $b = 288$ bars (24 hours). | Yes (Approve $b=288$ calendar MBB). |
| **Overlapping Trades** | Trade-level paired array | Trades overlap in calendar time, violating sample independence. | Resample continuous 5m equity curve rather than isolated trade returns. | Yes (Approve calendar equity resampling). |
| **Multi-Asset Concurrency** | Assets tested independently | Ignores cross-sectional correlation during market crashes. | Aggregate concurrent specialist returns into single fleet portfolio series. | Yes (DEC_05 Concurrency Policy). |
| **Multiple Testing Family** | Holm-Bonferroni referenced; $K$ unspecified | Ambiguity between $K=11, 33, 99$ alters statistical thresholds. | Fix primary confirmatory family at $K=11$; report $K=33$ as secondary. | Yes (Confirm $K=11$ confirmatory). |
| **Expectancy Distinction** | $E[R_{\text{net}}] > 0$ | Point estimate does not establish statistical significance. | Enforce Level 3 bootstrap p-value ($p < 0.05$) as mandatory for alpha claims. | Yes (Approve Gate 2 hurdle). |
