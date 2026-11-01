# Phase 5.3.1 Pilot Dataset Profiling Report

## 1. Executive Summary

This report documents the quantitative dataset profiling for the two pilot instruments selected for Phase 5.3.1:
- `BTCUSDT`: High-liquidity benchmark representing the full long-history pilot (30 months of continuous data).
- `XMRUSDT`: Short-history feasibility stress test representing a recently onboarded perpetual futures contract (3.5 months of data).

Both datasets were profiled using the research-ready 5m multi-timeframe feature matrix and triple-barrier label series within the approved Development and Validation partitions (`2023-11-01 00:00:00 UTC` to `2026-04-30 23:59:59.999 UTC`).

---

## 2. Dataset Inventory and Profiling Summary

| Instrument | Exchange | Primary TF | Total Canonical Candles | Total Dev+Val Features | Clean Eligible Samples | Excluded / Ambiguous Samples |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| BTCUSDT | AsterDEX | 5m | 316,499 | 262,655 | 261,488 | 1,167 (0.44%) |
| XMRUSDT | AsterDEX | 5m | 83,863 | 30,703 | 30,623 | 80 (0.26%) |

### 2.1 Partition Sample Distribution

| Instrument | Development Samples (2023-11-01 to 2025-10-31) | Validation Samples (2025-11-01 to 2026-04-30) | Total Research Pool (Dev + Val) |
| :--- | :--- | :--- | :--- |
| BTCUSDT | 209,679 (80.19%) | 51,809 (19.81%) | 261,488 |
| XMRUSDT | 0 (0.00%) | 30,623 (100.00%) | 30,623 |

---

## 3. Class Distribution Analysis

Labels were generated using triple-barrier parameters: barrier multiplier = 1.5, horizon = 12 bars (60m), rolling volatility lookback = 20 bars.

### 3.1 BTCUSDT Class Breakdown
- Total Clean Samples: 261,488
- Take-Profit (`TP` / `+1`): 119,874 samples (45.84%)
- Stop-Loss (`SL` / `-1`): 120,922 samples (46.24%)
- Expiration (`EXP` / `0`): 20,692 samples (7.91%)
- Imbalance Ratio (`TP` vs `SL`): 0.9913 (almost perfectly balanced directional barrier hits)
- Vertical Barrier Hit Rate: 7.91% (low expiration rate indicates high barrier sensitivity)

### 3.2 XMRUSDT Class Breakdown
- Total Clean Samples: 30,623
- Take-Profit (`TP` / `+1`): 14,029 samples (45.81%)
- Stop-Loss (`SL` / `-1`): 13,396 samples (43.75%)
- Expiration (`EXP` / `0`): 3,198 samples (10.44%)
- Imbalance Ratio (`TP` vs `SL`): 1.0473 (slight upward directional tilt)
- Vertical Barrier Hit Rate: 10.44% (higher expiration rate due to distinct volatility regime)

---

## 4. Exclusion and Integrity Accounting

Samples were pruned according to the triple-barrier exclusion contract:
1. Warmup Exclusion: 200 bars at dataset start required to populate multi-timeframe moving averages and rolling volatility estimators.
2. Horizon Boundary Exclusion: The final 12 bars of the dataset cannot observe complete forward paths and are excluded from training labels.
3. Ambiguous Touch Exclusion: Intrabar touches where both upper and lower barriers were reached within the same 5m candle.

### Detailed Exclusion Counts:
- BTCUSDT:
  - Intrabar Ambiguous Touches: 1,131 samples (0.43%)
  - Warmup and Boundary Exclusions: 36 samples
  - Total Pruned: 1,167 samples (0.44% of available pool)
- XMRUSDT:
  - Intrabar Ambiguous Touches: 68 samples (0.22%)
  - Warmup and Boundary Exclusions: 12 samples
  - Total Pruned: 80 samples (0.26% of available pool)

---

## 5. Short-History Feasibility Stress Test: XMRUSDT

### 5.1 Root Cause of Zero Development History
AsterDEX officially listed and opened perpetual futures trading for XMRUSDT on `2026-01-14 09:25:00 UTC`. Consequently, no AsterDEX exchange orderbook or candle history exists prior to January 14, 2026. The Development partition (`2023-11-01` through `2025-10-31`) contains exactly 0 records.

### 5.2 Statistical and Research Implications
1. Regimes Under-Sampled: All 30,623 observations occur in a single 3.5-month macro regime (Q1-Q2 2026). The model has zero exposure to 2024 bull trends, 2025 pullbacks, or cross-cycle liquidity shifts.
2. Compressed Split Horizons: In a 5-fold expanding walk-forward validation:
   - Fold 1 training window spans only 53 calendar days (15,299 samples).
   - Test folds span only 10.6 calendar days (3,050 samples).
   - A single 2-day volatility event can dominate an entire test fold.
3. Generalization Hazard: Models trained on compressed windows risk over-indexing to localized microstructural patterns rather than persistent market dynamics.

### 5.3 Feasibility Recommendation
- Technical Feasibility: PASS. The quantitative pipeline, walk-forward splitter, robust preprocessor, and model trainers executed without software failure, numerical errors, or memory leakage.
- Research Validity: PASS WITH LIMITATIONS. XMRUSDT models should NOT be deployed in isolation without explicit transfer priors or pooled volatility representations. The specialist must be flagged as `FEASIBLE_WITH_SHORT_HISTORY_LIMITATIONS` in downstream production registries.
