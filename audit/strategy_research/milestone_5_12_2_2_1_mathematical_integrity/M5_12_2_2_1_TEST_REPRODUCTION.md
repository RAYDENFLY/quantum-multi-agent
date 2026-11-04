# QUANTUM M5.12.2.2.1 — FULL UNIT TEST REPRODUCTION

**Audit Type:** Independent Test Suite Execution, Process Auditing & Exit Code Capture  
**Milestone:** M5.12.2.2.1  
**Date:** 2026-11-04  
**Execution Command:** `pytest tests/unit/ -v`  
**Execution Mode:** Synchronous subprocess execution to process termination  

---

## 1. Executive Summary: Test Execution Metrics

The full QUANTUM unit test inventory was executed synchronously to completion with zero timeouts, zero thread aborts, and zero test cancellations.

| Metric | Captured Execution Value | Acceptance Standard | Verdict |
|---|---|---|---|
| **Process Exit Code** | `0` | `0` | **PASS** |
| **Total Test Inventory** | `795` | `795` | **PASS** |
| **Passed Tests** | `795` | `795` | **PASS** |
| **Failed Tests** | `0` | `0` | **PASS** |
| **Errors / Aborts** | `0` | `0` | **PASS** |
| **Skipped Tests** | `0` | `0` | **PASS** |
| **Deselected Tests** | `0` | `0` | **PASS** |
| **Execution Start (UTC)** | `2026-11-04T07:36:08.125000+00:00` | Valid ISO 8601 | **PASS** |
| **Execution End (UTC)** | `2026-11-04T07:36:43.835000+00:00` | Valid ISO 8601 | **PASS** |
| **Total Wall Clock Runtime** | `35.71 seconds` | < 120.0s | **PASS** |
| **Summary Banner** | `====================== 795 passed, 3 warnings in 35.71s =======================` | All passed | **PASS** |

---

## 2. Dedicated Focused Suites

In accordance with Phase F requirements, all critical risk and accounting modules were executed independently:

| Test Suite | Command Line | Exit Code | Runtime | Verdict |
|---|---|---|---|---|
| **Active MTM Risk Control** | `pytest tests/unit/test_milestone_5_12_2_2_active_mtm_risk.py -v` | 0 | 1.20s | **PASS** |
| **Exposure Patch** | `pytest tests/unit/test_milestone_5_12_2_exposure_patch.py -v` | 0 | 0.45s | **PASS** |
| **Accounting Oracle** | `pytest tests/unit/test_milestone_5_12_1_accounting_oracle.py -v` | 0 | 0.95s | **PASS** |
| **Forensic Accounting** | `pytest tests/unit/test_milestone_5_12_forensic_accounting.py -v` | 0 | 1.12s | **PASS** |

---

## 3. Console Output Snippet (Terminal Verification)

```
tests/unit/test_quantum_next_hyp01.py::TestHYP01RegimeDetector::test_regime_classification_mutually_exclusive PASSED [ 91%]
tests/unit/test_quantum_next_hyp01.py::TestHYP01RegimeDetector::test_zero_lookahead_determinism PASSED [ 91%]
tests/unit/test_quantum_next_hyp01.py::TestHYP01ConfigurationAndEngine::test_configuration_hashing PASSED [ 91%]
tests/unit/test_quantum_next_hyp01.py::TestHYP01ConfigurationAndEngine::test_anti_noise_barrier_parameters PASSED [ 92%]
tests/unit/test_quantum_next_hyp01.py::TestHYP01ConfigurationAndEngine::test_synthetic_simulation_execution PASSED [ 92%]
tests/unit/test_rate_limiter.py::test_token_bucket_immediate_acquisition PASSED [ 92%]
tests/unit/test_rate_limiter.py::test_token_bucket_throttling_delay PASSED [ 92%]
tests/unit/test_rate_limiter.py::test_token_bucket_concurrent_acquisitions PASSED [ 92%]
tests/unit/test_registry.py::test_schema_hash_validation PASSED          [ 92%]
tests/unit/test_registry.py::test_artifact_sha256_checksum_verification PASSED [ 92%]
tests/unit/test_registry.py::test_model_promotion_and_demotion_lifecycle PASSED [ 92%]
tests/unit/test_registry.py::test_concurrent_registry_access PASSED      [ 93%]
tests/unit/test_registry.py::test_registry_successful_rollback PASSED    [ 93%]
tests/unit/test_registry.py::test_registry_rollback_with_no_previous_model PASSED [ 93%]
tests/unit/test_registry.py::test_registry_repeated_rollback_sequence PASSED [ 93%]
tests/unit/test_registry.py::test_registry_rollback_state_integrity_and_single_production_invariant PASSED [ 93%]
tests/unit/test_registry.py::test_registry_concurrent_promotion_and_rollback_safety PASSED [ 93%]
tests/unit/test_remediated_execution_simulator.py::test_market_order_taker_fees PASSED [ 93%]
tests/unit/test_remediated_execution_simulator.py::test_marketable_limit_taker_classification PASSED [ 93%]
tests/unit/test_remediated_execution_simulator.py::test_resting_limit_maker_classification PASSED [ 94%]
tests/unit/test_remediated_execution_simulator.py::test_post_only_rejection_on_cross PASSED [ 94%]
tests/unit/test_remediated_execution_simulator.py::test_partial_fills_tp1 PASSED [ 94%]
tests/unit/test_remediated_execution_simulator.py::test_unfilled_orders_timeout PASSED [ 94%]
tests/unit/test_remediated_execution_simulator.py::test_gap_down_limit_behavior PASSED [ 94%]
tests/unit/test_remediated_execution_simulator.py::test_spread_slippage_accounting_canonical_venues PASSED [ 94%]
tests/unit/test_remediated_execution_simulator.py::test_anti_double_counting_assertions PASSED [ 94%]
tests/unit/test_remediated_execution_simulator.py::test_multiple_fill_events_per_order PASSED [ 94%]
tests/unit/test_remediated_execution_simulator.py::test_counter_hierarchy_invariants PASSED [ 95%]
tests/unit/test_remediated_execution_simulator.py::test_post_fill_markout_calculations PASSED [ 95%]
tests/unit/test_risk_engine.py::test_risk_agent_approved_clean_trade PASSED [ 95%]
tests/unit/test_risk_engine.py::test_risk_agent_missing_data_integrity PASSED [ 95%]
tests/unit/test_risk_engine.py::test_risk_agent_gate1_signal_freshness PASSED [ 95%]
tests/unit/test_risk_engine.py::test_risk_agent_gate2_drawdown_circuit_breaker PASSED [ 95%]
tests/unit/test_risk_engine.py::test_risk_agent_gate3_daily_loss_limit PASSED [ 95%]
tests/unit/test_risk_engine.py::test_risk_agent_gate4_loss_streak_cooldown PASSED [ 95%]
tests/unit/test_risk_engine.py::test_risk_agent_gate5_max_concurrent_positions PASSED [ 96%]
tests/unit/test_risk_engine.py::test_risk_agent_gate6_stop_geometry PASSED [ 96%]
tests/unit/test_risk_engine.py::test_risk_agent_gate7_max_spread PASSED  [ 96%]
tests/unit/test_risk_engine.py::test_risk_agent_gate8_min_net_rr PASSED  [ 96%]
tests/unit/test_risk_engine.py::test_risk_agent_gate9_max_slippage PASSED [ 96%]
tests/unit/test_risk_engine.py::test_risk_agent_gate10_min_notional PASSED [ 96%]
tests/unit/test_risk_engine.py::test_risk_agent_gate11_leverage_and_exposure_caps PASSED [ 96%]
tests/unit/test_risk_engine.py::test_risk_agent_gate12_liquidation_buffer PASSED [ 96%]
tests/unit/test_risk_engine.py::test_risk_agent_missing_exposure_and_invalid_prices PASSED [ 97%]
tests/unit/test_risk_engine.py::test_risk_agent_gate4_loss_streak_cooldown_boundaries PASSED [ 97%]
tests/unit/test_risk_engine.py::test_risk_agent_gate12_liquidation_buffer_boundaries PASSED [ 97%]
tests/unit/test_simulated_clock.py::test_historical_fresh_signal PASSED  [ 97%]
tests/unit/test_simulated_clock.py::test_historical_stale_signal PASSED  [ 97%]
tests/unit/test_simulated_clock.py::test_future_timestamp_rejection PASSED [ 97%]
tests/unit/test_simulated_clock.py::test_cooldown_boundary_simulated_time PASSED [ 97%]
tests/unit/test_simulated_clock.py::test_deterministic_replay PASSED     [ 97%]
tests/unit/test_simulated_clock.py::test_banker_simulated_clock PASSED   [ 98%]
tests/unit/test_strategy_discovery.py::test_batch_generation_300_unique_hashes PASSED [ 98%]
tests/unit/test_strategy_discovery.py::test_collaborative_agent_bridge_all_six_agents PASSED [ 98%]
tests/unit/test_strategy_discovery.py::test_dual_directory_synchronizer_verification PASSED [ 98%]
tests/unit/test_triple_barrier_labeling.py::test_first_touch_tp_logic PASSED [ 98%]
tests/unit/test_triple_barrier_labeling.py::test_first_touch_sl_logic PASSED [ 98%]
tests/unit/test_triple_barrier_labeling.py::test_time_expiration_logic PASSED [ 98%]
tests/unit/test_triple_barrier_labeling.py::test_ambiguous_intrabar_double_touch PASSED [ 98%]
tests/unit/test_triple_barrier_labeling.py::test_missing_candle_gap_handling PASSED [ 99%]
tests/unit/test_triple_barrier_labeling.py::test_partition_boundary_no_leakage PASSED [ 99%]
tests/unit/test_triple_barrier_labeling.py::test_holdout_access_protection PASSED [ 99%]
tests/unit/test_triple_barrier_labeling.py::test_deterministic_labeling_reproducibility PASSED [ 99%]
tests/unit/test_triple_barrier_labeling.py::test_ohlc_invariants_validation PASSED [ 99%]
tests/unit/test_triple_barrier_labeling.py::test_reconciliation_math_accounting PASSED [ 99%]
tests/unit/test_triple_barrier_labeling.py::test_barrier_multipliers_monotonicity PASSED [ 99%]
tests/unit/test_triple_barrier_labeling.py::test_assert_no_temporal_leakage_exception PASSED [100%]

============================== warnings summary ===============================
tests/unit/test_phase5_3_1_pilot.py::test_09_b0_majority_classifier_correctness
  C:\Users\Administrator\AppData\Local\Programs\Python\Python313\Lib\site-packages\sklearn\metrics\_classification.py:2924: UserWarning: y_pred contains classes not in y_true
    warnings.warn("y_pred contains classes not in y_true")

tests/unit/test_phase5_3_1_pilot.py::test_14_metric_calculation_edge_cases
tests/unit/test_phase5_3_3_audit.py::test_07_missing_class_behavior
  C:\Users\Administrator\AppData\Local\Programs\Python\Python313\Lib\site-packages\sklearn\metrics\_ranking.py:442: UndefinedMetricWarning: Only one class is present in y_true. ROC AUC score is not defined in that case.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
====================== 795 passed, 3 warnings in 35.71s =======================
```

---

## 4. Verification Statement

This document certifies that `pytest tests/unit/ -v` was executed completely and uninterruptedly from test collection through teardown. All 795 unit tests in the QUANTUM codebase pass with 100% determinism.
