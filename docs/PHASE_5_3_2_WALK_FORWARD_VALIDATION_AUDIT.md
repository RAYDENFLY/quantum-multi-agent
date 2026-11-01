# Phase 5.3.2 Walk-Forward Cross-Validation Audit

## 1. Executive Summary

This report documents the temporal validation structure and mathematical leakage audit for all 11 instruments evaluated in Phase 5.3.2.

Standard cross-validation (e.g. k-fold or random shuffling) is fundamentally invalid for financial time series due to forward-peeking lookahead bias and autocorrelated errors. QUANTUM enforces expanding-window walk-forward validation with three layers of temporal defense:
1. Expanding Training Window: Training sets expand strictly forward in time. Prior test folds are absorbed into subsequent training windows.
2. Forward Label Purging (12 Bars): The final 12 bars (60 minutes) of each training window are purged. Because triple-barrier labels evaluate price movements up to 12 bars into the future, this guarantees that no training sample's label references price observations inside the test fold.
3. Test Horizon Protection (12 Bars): The final 12 bars of each test window are truncated from model evaluation. This guarantees that test sample labels evaluate only price action occurring inside the assigned test window, preventing test evaluations from looking into subsequent embargoed or holdout periods.
4. Post-Test Embargo (24 Bars): A 24-bar (120 minutes) embargo buffer prevents residual autoregressive autocorrelation leakage.

---

## 2. Walk-Forward Fold Schedules Across All 11 Instruments

### 2.1 The Ten Long-History Specialists
All ten long-history specialists (BTC, ETH, SOL, BNB, ADA, XRP, AVAX, LINK, DOGE, LTC) span the complete 30-month Development and Validation window (`2023-11-01 00:00:00 UTC` to `2026-04-30 23:59:59.999 UTC`).

Because each instrument exhibits slight variations in ambiguous touch exclusions (0.3% to 0.6%), their clean sample counts vary slightly between 261,046 and 261,814. Their fold schedules are summarized below:

| Fold | Training Window (UTC) | Train Samples (Range) | Purged Gap | Test Window (UTC) | Test Samples (Range) | Test Protection | Post Embargo |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Fold 1** | 2023-11-01 00:00 to ~2025-01-29 10:15 | 130,511 to 130,895 | 12 bars (60m) | ~2025-01-29 11:20 to ~2025-04-30 11:20 | 26,092 to 26,169 | 12 bars (60m) | 24 bars (120m) |
| **Fold 2** | 2023-11-01 00:00 to ~2025-04-30 11:20 | 156,615 to 157,076 | 12 bars (60m) | ~2025-04-30 12:30 to ~2025-07-30 19:50 | 26,092 to 26,169 | 12 bars (60m) | 24 bars (120m) |
| **Fold 3** | 2023-11-01 00:00 to ~2025-07-30 19:50 | 182,719 to 183,257 | 12 bars (60m) | ~2025-07-30 20:55 to ~2025-10-30 04:50 | 26,092 to 26,169 | 12 bars (60m) | 24 bars (120m) |
| **Fold 4** | 2023-11-01 00:00 to ~2025-10-30 04:50 | 208,823 to 209,438 | 12 bars (60m) | ~2025-10-30 05:55 to ~2026-01-29 14:35 | 26,092 to 26,169 | 12 bars (60m) | 24 bars (120m) |
| **Fold 5** | 2023-11-01 00:00 to ~2026-01-29 14:35 | 234,927 to 235,619 | 12 bars (60m) | ~2026-01-29 15:40 to 2026-04-30 21:55 | 26,095 to 26,173 | 12 bars (60m) | 24 bars (120m) |

### 2.2 The Short-History Outlier: XMRUSDT
XMRUSDT was onboarded on AsterDEX on `2026-01-14 09:25:00 UTC` and has 30,623 clean samples:

| Fold | Training Window (UTC) | Train Samples | Purged Gap | Test Window (UTC) | Test Samples | Test Protection | Post Embargo |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Fold 1** | 2026-01-14 09:25 to 2026-03-08 14:25 | 15,299 (53 days) | 12 bars (60m) | 2026-03-08 15:30 to 2026-03-19 05:55 | 3,050 (10.6 days) | 12 bars (60m) | 24 bars (120m) |
| **Fold 2** | 2026-01-14 09:25 to 2026-03-19 05:55 | 18,361 (64 days) | 12 bars (60m) | 2026-03-19 07:00 to 2026-03-29 21:45 | 3,050 (10.6 days) | 12 bars (60m) | 24 bars (120m) |
| **Fold 3** | 2026-01-14 09:25 to 2026-03-29 21:45 | 21,423 (74 days) | 12 bars (60m) | 2026-03-29 22:50 to 2026-04-09 13:00 | 3,050 (10.6 days) | 12 bars (60m) | 24 bars (120m) |
| **Fold 4** | 2026-01-14 09:25 to 2026-04-09 13:00 | 24,485 (85 days) | 12 bars (60m) | 2026-04-09 14:05 to 2026-04-20 05:45 | 3,050 (10.6 days) | 12 bars (60m) | 24 bars (120m) |
| **Fold 5** | 2026-01-14 09:25 to 2026-04-20 05:45 | 27,547 (96 days) | 12 bars (60m) | 2026-04-20 06:50 to 2026-04-30 21:55 | 3,052 (10.6 days) | 12 bars (60m) | 24 bars (120m) |

---

## 3. Mathematical Proof of Zero Leakage

For any instrument and fold $k \in \{1, \dots, 5\}$:
Let indices be denoted by integer chronological row order $t \in [0, N-1]$:
1. Training sample set:
   $$\mathcal{T}_{\text{train}}^{(k)} = \{0, 1, \dots, t_{\text{train\_end}}^{(k)}\}$$
2. Purge buffer:
   $$\mathcal{P}_{\text{train}}^{(k)} = \{t_{\text{train\_end}}^{(k)} + 1, \dots, t_{\text{test\_start}}^{(k)} - 1\}, \quad |\mathcal{P}_{\text{train}}^{(k)}| = 12 \text{ bars}$$
   Since any training label evaluates at most $t + 12$, for the last training sample $t = t_{\text{train\_end}}^{(k)}$, its forward horizon evaluates up to $t_{\text{train\_end}}^{(k)} + 12 = t_{\text{test\_start}}^{(k)} - 1$.
   Therefore, no training label can observe any price point at or after $t_{\text{test\_start}}^{(k)}$.
3. Test sample set:
   $$\mathcal{T}_{\text{test}}^{(k)} = \{t_{\text{test\_start}}^{(k)}, \dots, t_{\text{test\_end}}^{(k)} - 12\}$$
   By truncating $12$ bars from the end of the test fold, the last evaluated test sample $t_{\text{last\_test}} = t_{\text{test\_end}}^{(k)} - 12$ evaluates price action up to:
   $$t_{\text{last\_test}} + 12 = t_{\text{test\_end}}^{(k)}$$
   Therefore, no test label can evaluate price points beyond $t_{\text{test\_end}}^{(k)}$.
4. Disjointness guarantees:
   $$\mathcal{T}_{\text{train}}^{(k)} \cap \mathcal{T}_{\text{test}}^{(k)} = \emptyset$$
   $$\mathcal{T}_{\text{test}}^{(k)} \cap \mathcal{T}_{\text{test}}^{(k+1)} = \emptyset$$
   $$\max(\mathcal{T}_{\text{train}}^{(k)}) < \min(\mathcal{T}_{\text{test}}^{(k)})$$

Unit tests `test_07_purge_enforcement`, `test_09_training_label_boundary_protection`, and `test_10_test_label_boundary_protection` in [`tests/unit/test_phase5_3_2_fleet.py`](file:///d:/quantum-multi-agent/tests/unit/test_phase5_3_2_fleet.py) continuously verify these invariants.
