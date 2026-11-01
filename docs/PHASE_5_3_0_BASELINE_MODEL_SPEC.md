# QUANTUM PHASE 5.3.0 - BASELINE MODEL SPECIFICATION

**Author:** Senior Quantitative ML Research Architect & Machine Learning Engineer  
**Date:** 2026-11-01  
**Repository:** https://github.com/RAYDENFLY/quantum-multi-agent  
**Scope:** Architectural Specification for the Five Benchmark Classifiers  
**Implementation:** [baselines.py](file:///d:/quantum-multi-agent/src/quantum/ml/baselines.py)  

---

## 1. BASELINE MODEL SUITE OVERVIEW

To establish rigorous scientific benchmarks before introducing complex models, Phase 5.3 defines five standardized baseline architectures:

1. **Majority Class Heuristic (B0):** The minimal lower-bound benchmark.
2. **Prior Probability Frequency (B1):** The empirical class distribution benchmark.
3. **Regularized Logistic Regression (B2):** The linear statistical benchmark.
4. **Balanced Random Forest (B3):** The non-linear bagging ensemble benchmark.
5. **LightGBM Gradient Boosting (B4):** The non-linear boosting benchmark.

Zero model training is performed during Phase 5.3.0. All configurations represent frozen pre-training specifications.

---

## 2. DETAILED BASELINE SPECIFICATIONS

### Baseline 0: Majority Class Classifier
- **Purpose:** Establishes the trivial accuracy floor. Any model failing to outperform this baseline provides zero predictive utility.
- **Decision Rule:** Predicts $\arg\max_k (N_k)$ for all test samples, where $N_k$ is the frequency of class $k$ in the training fold.
- **Input Features:** None required.
- **Parameters:** None.
- **Computational Complexity:** $O(N)$ for training class counting, $O(1)$ for inference.
- **Memory Footprint:** $< 1$ MB.

### Baseline 1: Prior Class Probability Classifier
- **Purpose:** Evaluates uncalibrated frequency forecasting. Serves as the primary reference for Brier score and log-loss evaluations.
- **Decision Rule:** Emits the constant probability vector $\mathbf{p} = [p_{\text{SL}}, p_{\text{EXP}}, p_{\text{TP}}]$ matching training fold frequencies.
- **Input Features:** None required.
- **Parameters:** None.
- **Computational Complexity:** $O(N)$ for prior calculation, $O(1)$ for probability emission.
- **Memory Footprint:** $< 1$ MB.

### Baseline 2: Regularized Logistic Regression (Multinomial)
- **Purpose:** Linear statistical benchmark assessing whether linear hyperplanes in feature space possess directional predictability.
- **Algorithm:** `sklearn.linear_model.LogisticRegression`
- **Solver:** `lbfgs`
- **Penalty:** L2 regularization
- **Inverse Regularization ($C$):** Default $1.0$ (Candidate grid: $[0.01, 0.1, 1.0, 10.0]$)
- **Class Weighting:** `class_weight='balanced'` (inversely proportional to class frequencies)
- **Max Iterations:** 500 iterations
- **Preprocessing:** Requires [SpecialistPreprocessor](file:///d:/quantum-multi-agent/src/quantum/ml/preprocessor.py) with `RobustScaler` to ensure numerical convergence.
- **Computational Complexity:** $O(N \cdot d \cdot I)$ where $d=36$ features and $I \le 500$ iterations.
- **Expected Memory:** $\approx 150$ MB.

### Baseline 3: Balanced Random Forest
- **Purpose:** Non-linear decision boundary benchmark capable of capturing non-linear interactions without gradient boosting overhead.
- **Algorithm:** `sklearn.ensemble.RandomForestClassifier`
- **Number of Estimators:** 100 trees
- **Max Depth:** 8 (strictly bounded to prevent overfitting on noisy financial tick data)
- **Min Samples Leaf:** 50 samples
- **Max Features:** `"sqrt"` ($\sqrt{36} = 6$ features per split)
- **Class Weighting:** `class_weight='balanced'`
- **Thread Budget:** `n_jobs=2` (strictly capped for CPU resource conservation)
- **Random State:** Global seed $42 + \text{Instrument\_Offset}$
- **Computational Complexity:** $O(M \cdot N \cdot d \cdot \log N)$ where $M=100$ trees.
- **Expected Memory:** $\approx 350 - 450$ MB.

### Baseline 4: LightGBM Gradient Boosting
- **Purpose:** High-efficiency gradient boosted decision tree benchmark assessing additive tree performance.
- **Algorithm:** `lightgbm.LGBMClassifier` (verified version: 4.6.0)
- **Number of Estimators:** 100 boosting rounds
- **Learning Rate:** 0.05
- **Number of Leaves:** 31 (`num_leaves`)
- **Min Child Samples:** 50 samples
- **Subsample Ratio:** 0.8 (row subsampling per iteration)
- **Colsample By Tree:** 0.8 (feature subsampling per tree)
- **Class Weighting:** `class_weight='balanced'`
- **Thread Budget:** `n_jobs=2`
- **Random State:** Global seed $42 + \text{Instrument\_Offset}$
- **Computational Complexity:** $O(M \cdot N \cdot d)$ with histogram binning.
- **Expected Memory:** $\approx 200 - 300$ MB.

---

## 3. PROBABILITY CALIBRATION POLICY

In quantitative finance, uncalibrated raw model probabilities can severely distort risk management and Kelly sizing:
- Random Forest probability outputs tend to cluster away from 0 and 1.
- Boosted trees may produce overconfident extreme probabilities.

### Calibration Protocol
For regularized logistic regression, probabilities are inherently calibrated under cross-entropy minimization. For tree ensembles (Random Forest and LightGBM), probability calibration will be evaluated using out-of-fold predictions using:
- **Platt Scaling (Sigmoid):** Parametric calibration for monotonic distortions.
- **Isotonic Regression:** Non-parametric calibration if sample count $> 10,000$.

Calibration quality is audited via the multi-class Brier score and reliability curves.

---

## 4. HYPERPARAMETER SEARCH POLICY

In Phase 5.3.0, **no hyperparameter search or tuning is performed**. The parameters specified above serve as fixed, uniform baselines across all 11 instruments. Cross-instrument comparison requires identical starting baselines. Per-instrument hyperparameter optimization will be gated to Phase 5.3.2 after baseline results are established.
