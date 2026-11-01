# QUANTUM PHASE 5.2.1 - RESEARCH TARGET SELECTION GOVERNANCE

**Author:** Senior Quantitative Research Director & Financial ML Governance Specialist  
**Date:** 2026-11-01  
**Repository:** https://github.com/RAYDENFLY/quantum-multi-agent  
**Scope:** Re-Evaluation of Multiplier Candidate on Uncontaminated Data & Target Selection Protocol  
**Audit Script:** [evaluate_dev_val_governance.py](file:///d:/quantum-multi-agent/scripts/evaluate_dev_val_governance.py)  

---

## 1. RESEARCH TARGET SELECTION PROBLEM

In Phase 5.2, the 1.5 return volatility multiplier was recommended as the primary target candidate based on aggregate metrics across approximately 3.2 million candles. Because those metrics inadvertently included 579,806 samples from the Final Holdout, the recommendation could not be formally accepted as an independently validated decision without re-evaluation.

Under quantitative governance rules, target parameters must be validated **strictly on Development and Validation partitions**, completely excluding holdout data.

---

## 2. RE-EVALUATION STRICTLY ON DEVELOPMENT & VALIDATION DATA

A clean sensitivity analysis was executed across all 11 instruments strictly within the window `2023-11-01 00:00:00.000` to `2026-04-30 23:59:59.999 UTC` (timestamps `1698796800000` to `1777593599999`).

This strictly in-sample / tuning dataset contains:
- **Total Candles Evaluated:** 2,657,462
- **Pre-Development History:** Excluded (0 candles)
- **Observed / Historical Holdout:** Excluded (0 candles)
- **Prospective Holdout:** Excluded (0 candles)

### Empirical Sensitivity Comparison (Dev + Val Only)

| Metric | Multiplier 1.0 | Multiplier 1.5 (Candidate) | Multiplier 2.0 |
|---|---|---|---|
| **Total Input Candles** | 2,657,462 | 2,657,462 | 2,657,462 |
| **Eligible Samples** | 2,622,950 | **2,645,709** | 2,651,683 |
| **Take Profit (TP) Count** | 1,188,688 | **1,122,811** | 1,009,927 |
| **Take Profit (TP) %** | 45.32% | **42.44%** | 38.09% |
| **Stop Loss (SL) Count** | 1,180,836 | **1,123,618** | 1,017,466 |
| **Stop Loss (SL) %** | 45.02% | **42.47%** | 38.37% |
| **TP vs SL Asymmetry** | +0.30% | **-0.03% (Near-Perfect Balance)** | -0.28% |
| **Time Expiration Count** | 253,426 | **399,280** | 624,290 |
| **Time Expiration %** | 9.66% | **15.09%** | 23.54% |
| **Ambiguous Double-Touch Count** | 34,228 | **11,469** | 5,495 |
| **Ambiguity Rate (%)** | 1.2880% | **0.4316%** | 0.2068% |
| **Ambiguity Reduction vs M=1.0** | Baseline | **-66.5% reduction** | -83.9% reduction |

---

## 3. INDEPENDENT VALIDATION OF MULTIPLIER 1.5

When evaluated strictly on the uncontaminated 2.65 million Development and Validation candles:

1. **Near-Perfect Natural Class Symmetry:**
   At $M = 1.5$, TP is 42.44% and SL is 42.47%. The difference between Take Profit and Stop Loss is a negligible **0.03%** across 2.65 million candles. In comparison, at $M = 1.0$, the difference is 0.30%, and at $M = 2.0$, it is 0.28%. Multiplier 1.5 achieves the highest degree of directional neutrality.

2. **Substantial Ambiguity Suppression:**
   At $M = 1.0$, tighter barriers result in 34,228 ambiguous double-touch events (1.29% of candles). At $M = 1.5$, ambiguous events drop by **66.5%** down to 11,469 events (0.43% of candles). This removes noise from the supervised training signal.

3. **Controlled Expiration Rate:**
   At $M = 2.0$, wide barriers cause the expiration rate to inflate to 23.54% (nearly 1 in every 4 trades expires without resolution). At $M = 1.5$, expiration remains well-bounded at 15.09%, ensuring that 84.91% of trades achieve a decisive barrier hit within 60 minutes.

### Formal Status of Candidate 1.5
The 1.5 volatility multiplier **is confirmed as the primary research candidate** based strictly on Development and Validation evidence. It is now documented as an in-sample validated parameter, completely independent of the holdout data.

---

## 4. STRICT PROSPECTIVE RESEARCH GOVERNANCE RULES

To prevent future target contamination, all subsequent project phases (including Phase 5.3 feature selection and Phase 6 model training) must strictly adhere to the following governance rules:

1. **Strict Target Immobility:**
   Target labeling parameters (primary timeframe = 5m, horizon = 12 bars, lookback = 20 bars, multiplier = 1.5) are permanently frozen for Phase 5. They must not be modified, re-tuned, or optimized based on holdout performance.
2. **Holdout Non-Influence Rule:**
   The `PROSPECTIVE_HOLDOUT` partition must not influence:
   - Barrier multiplier selection
   - Prediction horizon selection
   - Feature engineering or selection
   - Model architecture or algorithm selection
   - Decision threshold selection
   - Hyperparameter optimization
   - Research design adjustments
3. **Audit Trail Verification:**
   Before any final performance evaluation on prospective holdout data, an automated check must verify that all training artifacts and models were compiled strictly prior to the prospective holdout period.
