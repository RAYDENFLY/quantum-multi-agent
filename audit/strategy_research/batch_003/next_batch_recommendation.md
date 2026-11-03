# Next Batch Research Decision & Recommendation — Post `BATCH_003`

- **Global Best Before `batch_003`:** `STRAT_134` (`+0.0920%/day`, CumRet `+36.16%`)
- **Batch `batch_003` Best Candidate:** `STRAT_242` (`config_hash = b02f17c3e006c2c9`, Mean Daily: **`+0.1092%/day`**, Net Cum. Return: **`+44.40%`**)
- **Global Best After `batch_003`:** `STRAT_242` (`config_hash = b02f17c3e006c2c9`, Mean Daily: **`+0.1092%/day`**, Net Cum. Return: **`+44.40%`**)

---

## Research State & Action Plan

**State C & State D — Optimization Plateau Reached Within Current Frozen 5m Model Space:**

1. Across 100 fine-grained neighborhood variations in Batch 003 (`STRAT_201`–`STRAT_300`), the marginal improvement over Batch 002 was `+0.0172%/day` (reaching **`+0.1092%/day`**, **`+44.40%`** cumulative net return on `$100 USD`, ending equity **`$144.40`**, `MDD = 16.35%`, `AvgDD = 4.40%`, `4/4` positive folds).
2. The local response surface around `STRAT_242` is smooth and stable (high parameter robustness), confirming that `STRAT_242` is a genuine structural peak rather than an isolated noise spike.
3. However, because the frozen Phase 5.3 5-minute LightGBM models and non-destructive leverage bounds (`<= 2.0x`, `MDD <= 30%`) plateau at **`+0.1092%/day`** (below the aspirational `+3.00%/day` target), further gains require order-book L2/funding-rate feature expansion or multi-timeframe model retraining.
