# QUANTUM Phase 5.0 - Baseline Experiment Specification

**Role:** Senior Quantitative Research Engineer, ML Research Scientist, and Financial Data Auditor  
**Repository:** https://github.com/RAYDENFLY/quantum-multi-agent  
**Phase:** Phase 5.0 (Dataset Readiness & Target Research)  
**Date:** November 1, 2026  
**Status:** Experimental Design Completed - Ready for Phase 5.1 Review  

---

## 1. Executive Summary

This document specifies the experimental protocol, baseline candidate models, specialist training architecture, economic evaluation criteria, and hardware execution constraints for Phase 5.1.

### Core Principles
1. **Strictly Specification Only**: No machine learning models are trained in Phase 5.0. This specification establishes the hypothesis-driven boundaries and benchmarks prior to empirical fitting.
2. **Specialist Model Architecture**: Specialist models dedicated to individual trading instruments (`BTCUSDT.P`, `ETHUSDT.P`, `SOLUSDT.P`, etc.) are specified rather than a single universal model. Individual cryptocurrencies possess distinct volatility distributions, order book dynamics, tick sizes, and funding rate behaviors.
3. **Dual Metric Evaluation**: Every experiment must be evaluated on both **predictive accuracy metrics** (statistical capability) and **economic simulation metrics** (realistic net profitability after transaction fees, slippage, and funding rate friction).
4. **Modest Hardware Compatibility**: All specified algorithms and batch sizes are constrained to run efficiently on modest CPU workstations (e.g. Intel i7-7700HQ 16 GB RAM or AMD A6-9225 12 GB RAM) with a strict peak memory budget under 1,024 MB.

---

## 2. Specialist vs Universal Model Architecture

### Why Specialist Models Are Required
In cryptocurrency perpetual markets, pooling all instruments into one universal model introduces substantial structural distortion:
- **Volatility Heterogeneity**: Annualized volatility ranges from ~45% for BTCUSDT to > 110% for SOLUSDT and DOGEUSDT. A universal model tends to overfit high-volatility altcoins or become desensitized to BTC regime transitions.
- **Microstructure and Liquidity Asymmetry**: BTCUSDT features dense top-of-book depth with tight 0.10 USDT spreads (0.01 bps), whereas lower-cap pairs exhibit wider spreads and frequent slippage gaps.
- **Funding Rate Divergence**: Altcoins frequently sustain high positive funding (e.g. 0.05% to 0.10% per 8 hours during bull runs) while BTC funding remains moderate (0.01%). Holding costs differ by orders of magnitude.
- **Decoupled Agent Architecture**: In the QUANTUM multi-agent framework, specialist models serve as pair-specific analytical engines for the ANALYST and SNIPER agents, allowing per-pair risk thresholds and dynamic position sizing.

---

## 3. Candidate Baseline Models Specification

To ensure that any sophisticated machine learning architecture genuinely extracts economic alpha, it must demonstrably outperform five progressively challenging baselines:

### Baseline 1: Naive Trivial Baselines (Directional & Drift)
- **Candidate 1A (Always LONG)**: Predicts positive return for all bars ($y_t = +1$). Measures secular market beta and long-drift bias.
- **Candidate 1B (Always SHORT)**: Predicts negative return for all bars ($y_t = -1$). Measures secular bear-drift bias.
- **Candidate 1C (No-Change / Prior Bar Persistence)**: Predicts that price direction mirrors the immediate prior candle ($y_t = \text{sign}(C_t - C_{t-1})$). Measures 1-lag autoregressive momentum.
- **Computational Cost**: Negligible (< 1 MB RAM, < 0.1s runtime).
- **Benchmark Gate**: Any statistical ML model that fails to outperform all three naive baselines on out-of-sample data is immediately rejected.

### Baseline 2: Linear / Regularized Logistic Regression
- **Purpose**: Establishes the linear feature-separability benchmark.
- **Algorithm**: L2-regularized Logistic Regression with cross-validated penalty parameter $C \in [10^{-3}, 10^{2}]$.
- **Inputs**: 38 stationary `SAFE` features, scaled via `RobustScaler` (fit on training fold only).
- **Loss Function**: Binary cross-entropy with class weight balancing.
- **Expected Limitations**: Incapable of capturing non-linear interactions or regime-conditional thresholds.
- **Overfitting Risk**: Minimal. High bias, low variance.
- **Hardware Profile**: Fast CPU solver (`lbfgs`), < 150 MB RAM, < 5s per fold.

### Baseline 3: Tree Ensemble (Random Forest)
- **Purpose**: Establishes the non-linear bagging benchmark with robust resistance to feature noise.
- **Algorithm**: `RandomForestClassifier` (100 trees, max depth = 6, min samples leaf = 50, max features = "sqrt").
- **Inputs**: 38 stationary `SAFE` features (tree models do not require monotonic feature scaling).
- **Loss Function**: Gini impurity / entropy with out-of-bag scoring.
- **Expected Limitations**: Cannot extrapolate beyond observed feature boundaries; sensitive to sudden structural regime breaks.
- **Overfitting Risk**: Moderate if depth is unconstrained. Constraining max depth to 6 and min samples leaf to 50 prevents memorization.
- **Hardware Profile**: Parallel CPU (`n_jobs=-1`), < 400 MB RAM, < 25s per fold.

### Baseline 4: Gradient Boosted Trees (LightGBM / XGBoost)
- **Purpose**: High-capacity non-linear boosting benchmark with leaf-wise splitting and native missing value handling.
- **Algorithm**: `LGBMClassifier` (version 4.6.0 installed and verified):
  - `max_depth = 5`
  - `num_leaves = 24`
  - `learning_rate = 0.03`
  - `n_estimators = 200`
  - `subsample = 0.8` (bagging fraction)
  - `colsample_bytree = 0.7` (feature fraction)
  - `reg_alpha = 0.1` (L1 penalty)
  - `reg_lambda = 1.0` (L2 penalty)
- **Inputs**: Complete stationary feature matrix with early stopping on validation fold.
- **Expected Limitations**: High capacity risks fitting transient microstructure noise if regularizations are relaxed.
- **Overfitting Risk**: High if learning rate is too large or early stopping is omitted.
- **Hardware Profile**: Highly optimized CPU multi-threading, < 350 MB RAM, < 15s per fold.

---

## 4. Market Microstructure and Cost Model Integration

A model predicting price direction with 53% accuracy is economically disastrous if trading costs exceed the edge. Every experiment must simulate real exchange friction:

### Cost Model Parameters

| Cost Parameter | AsterDEX Perpetual | Bybit Linear Perpetual | Simulated Impact |
| :--- | :--- | :--- | :--- |
| **Maker Fee** | 0.02% (2 bps) | 0.02% (2 bps) | Favorable entry on passive limit orders. |
| **Taker Fee** | 0.05% (5 bps) | 0.055% (5.5 bps) | Aggressive market order penalty (10 to 11 bps roundtrip). |
| **Bid-Ask Spread** | 0.5 to 2.0 bps (BTC/ETH) | 0.5 to 2.0 bps (BTC/ETH) | Half-spread paid on every crossing of the book. |
| **Slippage Buffer** | 1.0 to 3.0 bps | 1.0 to 3.0 bps | Execution slippage under market volatility. |
| **Funding Rate** | Settle every 8 hours | Settle every 8 hours | Cash flow penalty for holding positions across funding boundaries. |

### Why Directional Accuracy Alone Cannot Establish Profitability
1. **Fee Asymmetry**: On 5-minute candles, the average move is ~0.15% (15 bps). A roundtrip taker execution costs ~10 bps in fees plus ~2 bps spread/slippage, leaving only 3 bps of net move under perfect timing. A single losing trade of -0.30% wipes out the gross gains of three winning trades.
2. **Fat-Tailed Losses**: Cryptocurrency returns exhibit severe negative skewness during sell-offs. A model with 60% directional accuracy that suffers large catastrophic losses during flash crashes will have a deeply negative net PnL.
3. **Execution Path Reality**: Intrabar volatility often triggers a stop-loss order before the target candle closes in profit.

---

## 5. Comprehensive Evaluation Metrics

Phase 5.1 experiments must report two disjoint sets of metrics:

### 5.1 Predictive & Statistical Metrics

#### Classification Metrics
- **Accuracy**: $\frac{\text{TP} + \text{TN}}{\text{Total}}$
- **Balanced Accuracy**: $\frac{1}{2}\left(\frac{\text{TP}}{\text{TP} + \text{FN}} + \frac{\text{TN}}{\text{TN} + \text{FP}}\right)$ (Controls for regime imbalance)
- **Precision, Recall, F1-Score**: Evaluated per class (Long, Short, Neutral)
- **ROC-AUC**: Area under the Receiver Operating Characteristic curve
- **PR-AUC**: Area under Precision-Recall curve (critical for imbalanced classes)
- **Brier Score**: $\frac{1}{N}\sum (p_i - y_i)^2$ (Measures probabilistic calibration)
- **Expected Calibration Error (ECE)**: Binned deviation of predicted probabilities from empirical frequencies

#### Regression Metrics (where applicable)
- **Mean Absolute Error (MAE)**: $\frac{1}{N}\sum \lvert \hat{y}_i - y_i \rvert$
- **Root Mean Squared Error (RMSE)**: $\sqrt{\frac{1}{N}\sum (\hat{y}_i - y_i)^2}$
- **Directional Accuracy**: Proportion of times $\text{sign}(\hat{y}_i) == \text{sign}(y_i)$
- **Information Coefficient (Rank Correlation)**: Spearman's $\rho(\hat{y}, y)$

### 5.2 Economic Simulation Metrics
- **Net Cumulative PnL**: Cumulative return strictly net of maker/taker fees, spread, slippage, and funding costs.
- **Profit Factor**: $\frac{\text{Gross Profits}}{\lvert \text{Gross Losses} \rvert}$
- **Expectancy per Trade**: $\frac{\text{Net PnL}}{\text{Total Trades}}$ in basis points.
- **Maximum Drawdown (MDD)**: Maximum peak-to-trough decline in simulated equity curve.
- **Sharpe Ratio**: $\sqrt{365 \times 24 \times 12} \times \frac{\mu_{\text{net}}}{\sigma_{\text{net}}}$ (Annualized on 5m frequency).
- **Sortino Ratio**: Downside-deviation penalized risk-adjusted return.
- **Trade Turnover & Frequency**: Average holding time in bars, daily trade count, and exposure percentage.
- **Fee Contribution**: Percentage of gross profit paid out to exchange fees.

---

## 6. Hardware Constraints & Resource Budget

The research suite must execute comfortably on resource-constrained local hardware:

### Execution Profile for Phase 5.1

| Hardware Component | Reference Machine (i7-7700HQ) | Low-Resource Machine (A6-9225) | Strategy / Budget Constraint |
| :--- | :--- | :--- | :--- |
| **CPU Utilization** | 4 Cores / 8 Threads | 2 Cores / 2 Threads | Bound thread pool to `n_jobs = max(1, os.cpu_count() - 1)`. |
| **Peak Memory (RAM)** | < 800 MB | < 800 MB | Strict ceiling: Load one instrument and timeframe at a time. Do not pool 11 pairs in RAM. |
| **Disk Storage (HDD)** | Fast NVMe / SSD | Slow 5400 RPM HDD | Snappy-compressed Parquet with columnar projection (`read_canonical(columns=[...])`). |
| **Training Budget** | ~1-2 min per instrument fold | ~5-8 min per instrument fold | Early stopping after 20 rounds without validation improvement. |
| **GPU Dependency** | None required | None required | All models run on CPU; avoid unnecessary CUDA/GPU dependencies. |
