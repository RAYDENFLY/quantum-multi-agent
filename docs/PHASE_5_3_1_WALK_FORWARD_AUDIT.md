# Phase 5.3.1 Walk-Forward Cross-Validation Audit

## 1. Overview and Design Principles

Walk-forward cross-validation in QUANTUM strictly mirrors real-world sequential decision-making. Standard k-fold cross-validation is invalid for financial time series due to temporal leakage and serial autocorrelation.

The validation protocol enforced by [`PurgedWalkForwardSplitter`](file:///d:/quantum-multi-agent/src/quantum/ml/validation.py) adheres to three non-negotiable quantitative protections:
1. Expanding Training Window: Training samples expand sequentially into the future. Future data never leaks into past training folds.
2. Training Label Purging (12 Bars): The final 12 bars (60 minutes) of each training window are completely purged. Because triple-barrier labels evaluate price movements up to 12 bars forward, this ensures no training label references price points inside the test window.
3. Test Horizon Protection (12 Bars): The final 12 bars of each test window are truncated. This ensures that every test sample label evaluates only price action occurring inside the assigned test window, preventing test labels from peering into subsequent folds.
4. Post-Test Embargo (24 Bars): An embargo buffer of 24 bars (120 minutes) prevents residual autoregressive leakage.

---

## 2. BTCUSDT Walk-Forward Split Audit (Long-History Benchmark)

Total Clean Eligible Pool: 261,488 samples  
Initial Minimum Training Ratio: 50.0%  
Number of Folds: 5

| Fold | Train Samples | Train Start (UTC) | Train End (UTC) | Purged Bars | Test Samples | Test Start (UTC) | Test End (UTC) | Embargo Bars |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | 130,732 | 2023-11-01 00:00:00 | 2025-01-29 10:15:00 | 12 (60m) | 26,136 | 2025-01-29 11:20:00 | 2025-04-30 11:20:00 | 24 (120m) |
| 2 | 156,880 | 2023-11-01 00:00:00 | 2025-04-30 11:20:00 | 12 (60m) | 26,136 | 2025-04-30 12:30:00 | 2025-07-30 19:50:00 | 24 (120m) |
| 3 | 183,028 | 2023-11-01 00:00:00 | 2025-07-30 19:50:00 | 12 (60m) | 26,136 | 2025-07-30 20:55:00 | 2025-10-30 04:50:00 | 24 (120m) |
| 4 | 209,176 | 2023-11-01 00:00:00 | 2025-10-30 04:50:00 | 12 (60m) | 26,136 | 2025-10-30 05:55:00 | 2026-01-29 14:35:00 | 24 (120m) |
| 5 | 235,324 | 2023-11-01 00:00:00 | 2026-01-29 14:35:00 | 12 (60m) | 26,140 | 2026-01-29 15:40:00 | 2026-04-30 21:55:00 | 24 (120m) |

### Key Observations:
- Initial Training Size: Fold 1 trains on 130,732 bars (15 months of continuous history).
- Test Fold Consistency: Folds 1 through 4 have exactly 26,136 samples (~3 months each); Fold 5 absorbs the final residual partition with 26,140 samples.
- Temporal Termination: Fold 5 test window concludes at `2026-04-30 21:55:00 UTC`. With 12 bars forward horizon, the evaluation window finishes at `22:55:00 UTC`, strictly prior to the start of Validation Observed (`2026-05-01 00:00:00 UTC`).

---

## 3. XMRUSDT Walk-Forward Split Audit (Short-History Feasibility)

Total Clean Eligible Pool: 30,623 samples  
Initial Minimum Training Ratio: 50.0%  
Number of Folds: 5

| Fold | Train Samples | Train Start (UTC) | Train End (UTC) | Purged Bars | Test Samples | Test Start (UTC) | Test End (UTC) | Embargo Bars |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | 15,299 | 2026-01-14 09:25:00 | 2026-03-08 14:25:00 | 12 (60m) | 3,050 | 2026-03-08 15:30:00 | 2026-03-19 05:55:00 | 24 (120m) |
| 2 | 18,361 | 2026-01-14 09:25:00 | 2026-03-19 05:55:00 | 12 (60m) | 3,050 | 2026-03-19 07:00:00 | 2026-03-29 21:45:00 | 24 (120m) |
| 3 | 21,423 | 2026-01-14 09:25:00 | 2026-03-29 21:45:00 | 12 (60m) | 3,050 | 2026-03-29 22:50:00 | 2026-04-09 13:00:00 | 24 (120m) |
| 4 | 24,485 | 2026-01-14 09:25:00 | 2026-04-09 13:00:00 | 12 (60m) | 3,050 | 2026-04-09 14:05:00 | 2026-04-20 05:45:00 | 24 (120m) |
| 5 | 27,547 | 2026-01-14 09:25:00 | 2026-04-20 05:45:00 | 12 (60m) | 3,052 | 2026-04-20 06:50:00 | 2026-04-30 21:55:00 | 24 (120m) |

### Key Observations:
- Compressed Window: Fold 1 trains on 15,299 bars (53 calendar days).
- Rapid Walk-Forward Progression: Each test fold spans 3,050 samples (10.6 calendar days).
- Boundary Compliance: All folds preserve strict chronological expansion and non-overlapping test partitions.

---

## 4. Leakage and Overlap Verification

Mathematical proof of non-leakage for any fold $k$:
1. Let $\mathcal{I}_{\text{train}}^{(k)} = [0, \dots, t_{\text{train\_end}}^{(k)}]$
2. Let $\mathcal{I}_{\text{purge}}^{(k)} = [t_{\text{train\_end}}^{(k)} + 1, \dots, t_{\text{test\_start}}^{(k)} - 1]$, where $|\mathcal{I}_{\text{purge}}^{(k)}| \ge 12$
3. Let $\mathcal{I}_{\text{test}}^{(k)} = [t_{\text{test\_start}}^{(k)}, \dots, t_{\text{test\_end}}^{(k)}]$
4. Intersection check:
   $$\mathcal{I}_{\text{train}}^{(k)} \cap \mathcal{I}_{\text{test}}^{(k)} = \emptyset$$
5. Across adjacent folds $k$ and $k+1$:
   $$\mathcal{I}_{\text{test}}^{(k)} \cap \mathcal{I}_{\text{test}}^{(k+1)} = \emptyset$$
6. Expanding monotonicity:
   $$\mathcal{I}_{\text{train}}^{(k)} \subset \mathcal{I}_{\text{train}}^{(k+1)}$$

Unit test `test_07_purge_and_embargo_enforcement` in [`tests/unit/test_phase5_3_1_pilot.py`](file:///d:/quantum-multi-agent/tests/unit/test_phase5_3_1_pilot.py) continuously verifies these mathematical conditions.
