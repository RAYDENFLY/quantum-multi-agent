# QUANTUM PHASE 5.5: BACKTEST ENGINE TEST REPORT

**Document Version:** 2.0.0-FINAL-QUALIFICATION  
**Publication Timestamp:** 2026-11-02 17:32:00 UTC  
**Scope:** Multi-Level Verification Suite (Levels 1 through 5) for `quantum.backtesting`  
**Governance State:** Phase 5.5 `NOT_STARTED` | Phase 5.6 `NOT_AUTHORIZED` | Economic Backtesting `NOT_STARTED` | Prospective Holdout `STRICTLY_SEALED`  

**Authoritative Dossier References:**
- [QUANTUM_BACKTEST_ENGINE_IMPLEMENTATION_PLAN.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_BACKTEST_ENGINE_IMPLEMENTATION_PLAN.md)
- [QUANTUM_BACKTEST_ENGINE_TECHNICAL_SPECIFICATION.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_BACKTEST_ENGINE_TECHNICAL_SPECIFICATION.md)
- [QUANTUM_BACKTEST_ENGINE_IMPLEMENTATION_REPORT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_governance_dossier/QUANTUM_BACKTEST_ENGINE_IMPLEMENTATION_REPORT.md)

---

## 1. EXECUTIVE SUMMARY & FIVE-LEVEL TESTING PROTOCOL

All testing was conducted strictly within governance bounds using synthetic fixtures, hand-calculated mathematical test cases, and read-only artifact manifest metadata checks.

```text
+--------------------------------------------------+-------------------------------+------------+-----------+
| Test Level / Suite                               | Test File(s)                  | Test Count | Status    |
+--------------------------------------------------+-------------------------------+------------+-----------+
| Level 1: Simulated Clock Unit Tests              | test_simulated_clock.py       | 6 tests    | ALL PASSED|
| Level 1: Reference-Price Accounting (20 Scen.)   | test_backtest_accounting.py   | 9 tests    | ALL PASSED|
| Level 1: 11-Asset OOF Adapter & Integrity        | test_backtest_adapters.py     | 5 tests    | ALL PASSED|
| Level 1: Track 1 Predictive Pipeline (10 Scen.)  | test_backtest_track1.py       | 9 tests    | ALL PASSED|
| Level 2 & 3: Track 2 Causal Engine (18 Scen.)    | test_backtest_engine.py       | 12 tests   | ALL PASSED|
| Total Phase 5.5 Backtest Remediation Suite       | 5 dedicated test files        | 41 tests   | ALL PASSED|
| Level 4: Full Repository Regression Suite        | 26 test files in tests/unit/  | 604 tests  | ALL PASSED|
+--------------------------------------------------+-------------------------------+------------+-----------+
```

---

## 2. WORKSTREAM A: OOF UNIVERSE ADAPTER TESTS

**Test File:** [tests/unit/test_backtest_adapters.py](file:///d:/quantum-multi-agent/tests/unit/test_backtest_adapters.py) (5/5 PASSED)

- `test_full_11_asset_universe_manifest_audit`: Verifies all 11 materialized OOF Parquet files exist, pass schema/null/duplicate/simplex/monotonicity checks, preserve the prospective holdout seal (`max_open_time_ms = 1777586100000 < 1793491200000`), and distinguish the 10-asset `PRIMARY_RESEARCH_UNIVERSE` (~130,600 rows each) from `XMRUSDT` (`15,252` rows, `STRUCTURAL_BREAK_SUBGROUP_DEC_06_PENDING`).
- `test_primary_universe_guard_blocks_xmr_when_requested`: Confirms `require_primary_universe=True` blocks `XMRUSDT` while `DEC_06` is pending.
- `test_oof_signal_generation_and_fold5_status`: Confirms Folds 1 to 4 are tagged `VERIFIED_OOF` and Fold 5 is tagged `OOS_ELIGIBILITY_NOT_VERIFIED`.
- `test_oof_adapter_missing_file_and_invalid_fold`: Verifies `FileNotFoundError` and `ValueError` on invalid inputs.
- `test_oof_adapter_rejects_corrupted_synthetic_parquets`: Verifies rejection of cross-asset mismatch, duplicate timestamps, simplex errors, and prospective holdout breaches.

---

## 3. WORKSTREAM B: TRACK 1 PREDICTIVE EVALUATION TESTS

**Test File:** [tests/unit/test_backtest_track1.py](file:///d:/quantum-multi-agent/tests/unit/test_backtest_track1.py) (9/9 PASSED)

- `test_track1_perfect_predictions`: Verifies `balanced_accuracy = 1.0`, `multiclass_brier_score = 0.0`, `roc_auc_ovr = 1.0`, `ece_top_uniform = 0.0`, `aurcc_error_full = 0.0`.
- `test_track1_uniform_random_predictions`: Verifies exact Brier score $2/3 \approx 0.666667$, balanced accuracy $1/3$, and ROC-AUC $0.5$.
- `test_track1_completely_incorrect_predictions`: Verifies Brier score $2.0$, accuracy $0.0$, ECE $1.0$, and AURCC $1.0$.
- `test_track1_class_imbalance`: Verifies separation of raw accuracy ($0.80$) vs balanced accuracy ($1/3$).
- `test_track1_missing_class_behavior`: Verifies graceful handling when a ground-truth class is absent (`roc_auc_ovr = None`, `roc_auc_ovr_present_classes` computed, zero unhandled exceptions).
- `test_track1_invalid_and_normalized_probabilities`: Verifies rejection of out-of-range/unnormalized probabilities in strict mode and exact renormalization when `normalize_probabilities=True`.
- `test_track1_empty_and_small_samples`: Verifies `ValueError` on empty arrays and clean execution on $N = 3$.
- `test_track1_fold_separation_reporting`: Verifies `verified_oof_pooled` (Folds 1 to 4) vs `fold_5_unverified_oos` (Fold 5).
- `test_model_evaluation_contract_includes_ece_and_aurcc`: Verifies `ModelEvaluationContract` integration.

---

## 4. WORKSTREAM D: REFERENCE-PRICE ACCOUNTING LIFECYCLE TESTS

**Test File:** [tests/unit/test_backtest_accounting.py](file:///d:/quantum-multi-agent/tests/unit/test_backtest_accounting.py) (9/9 PASSED, covering all 20 scenarios)

- `test_case_1_long_profitable` through `test_case_4_short_losing`: Exact match to 4 decimal places with Phase 5.5.0.8 canonical cases (+$11.9775, -$17.9775, +$12.0225, -$18.0225).
- `test_fee_asymmetry_and_leg_breakdown`: Verifies entry fee ($1.50), exit fee scaling ($1.5225 vs $1.4775), and 0.45 bps fee asymmetry.
- `test_half_spread_slippage_and_effective_fill_prices`: Verifies effective fill prices (`100.02` / `99.98`) and slippage drag.
- `test_signed_funding_positive_negative_multiple_and_boundaries`: Verifies $CF > 0$ received, $CF < 0$ paid, multi-settlement accumulation, and strict $t_{\text{entry}} < t_{\text{settle}} \le t_{\text{exit}}$ boundary exclusion/inclusion.
- `test_partial_close_and_multi_step_lifecycle_reconciliation`: Verifies single partial close, multi-step partial closes with remaining open mark-to-market snapshot, full 3-step close, and conservation of quantity and notional.
- `test_zero_quantity_and_invalid_price_validations`: Verifies rejection of zero/negative/NaN quantities and prices and overfill protection.

---

## 5. WORKSTREAMS C, E, F, G: CAUSAL DISCRETE-EVENT ENGINE TESTS

**Test File:** [tests/unit/test_backtest_engine.py](file:///d:/quantum-multi-agent/tests/unit/test_backtest_engine.py) (12/12 PASSED, covering all 18 scenarios)

- `test_01` to `test_04`: Long TP, Long SL (including intrabar touch on entry bar 1), Short TP, Short SL.
- `test_05_06_opening_gap_beyond_tp_and_sl`: Verifies opening gaps beyond TP (`102.5 > U`) and SL (`97.0 < L`) execute at the gap open price with `is_gap_exit=True`.
- `test_07_same_bar_collision_policies`: Verifies `CONSERVATIVE_SL_FIRST` triggers Stop-Loss on same-bar double touch.
- `test_08_12_bar_timeout_exact_duration`: Verifies 12-bar timeout occurs on bar `entry_bar + 11` (`holding_bars == 12`, `exit_time_ms - entry_fill_time_ms == 3,600,000 ms`).
- `test_09_10_missing_candle_gap_and_duplicate_timestamps`: Verifies soft rejection vs strict exception on missing 5m bars, and `ValueError` on duplicate timestamps.
- `test_11_12_13_zero_volatility_floor_and_invalid_prices`: Verifies `REJECTED_ZERO_VOLATILITY` when `min_volatility=0.0`, floor application when `min_volatility=1e-3`, and `ValueError` on invalid OHLC geometry.
- `test_14_15_open_position_at_dataset_end_and_adjacent_signals`: Verifies `CONCURRENT_POSITION_BLOCKED` on overlapping adjacent signals and mark-to-market `open_positions_at_end` snapshot when dataset ends before bar 12.
- `test_16_explicit_risk_evaluation_modes`: Verifies Mode 1, Mode 2 (Gate 8 veto on 1.0 R:R vs approval when R:R >= 2.0), and Mode 3 (`GovernancePendingError` guard for `DEC_05`).
- `test_17_banker_agent_fsm_integration`: Verifies `PENDING_OPEN -> OPEN -> CLOSED` transition and zero remaining quantity.
- `test_18_deterministic_replay_and_resource_bounds`: Verifies byte-identical replay and peak memory `< 100 MB` (well below the `1 GB` RAM budget).

---

## 6. LEVEL 4: FULL REPOSITORY REGRESSION SUITE

- **Command:** `python -m pytest tests/unit/ -q`
- **Exit Code:** `0`
- **Passed:** `604`
- **Failed:** `0`
- **Errors:** `0`
- **Skipped:** `0`
- **Warnings:** `3` (pre-existing Phase 5.3 single-class sklearn fixture warnings)
- **Runtime:** `17.54s`

---
*End of Backtest Engine Test Report.*
