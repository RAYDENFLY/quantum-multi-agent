# QUANTUM PHASE 5.5.0.1: PORTFOLIO-AWARE STATISTICAL INFERENCE

**Document Status:** `APPROVED_FOR_DESIGN`  
**Publication Timestamp:** `2026-11-01 20:29:46 UTC`  
**Associated Deliverable:** Workstream C (Portfolio-Aware Statistical Inference)  

---

## 1. THE CROSS-ASSET DEPENDENCE PROBLEM

QUANTUM evaluates 11 specialist models operating in cryptocurrency perpetual futures markets. While the models are trained independently, their underlying return series exhibit strong cross-sectional correlation (e.g. simultaneous market-wide sell-offs).

Furthermore, the portfolio enforces a strict concurrency constraint of **maximum 3 concurrent positions**. Therefore, independent symbol-by-symbol resampling completely fails to model:
1. Cross-asset simultaneous drawdowns.
2. Collisions in the concurrency queue.
3. Shared capital depletion under portfolio equity compounding.

---

## 2. TWO-LEVEL STATISTICAL INFERENCE ARCHITECTURE

### Level 1: Specialist-Level Inference (Per-Symbol)
- **Estimand:** Mean net return per trade for specialist $s$: $\mu_{\text{net}, s} = \mathbb{E}[R_{\text{net}, s}]$.
- **Resampling Unit:** Single-symbol trade PnL sequence.
- **Resampling Method:** Moving Block Bootstrap (MBB) with block length $b = 24$ bars ($2$ hours), $B = 10,000$ resamples.
- **Hypothesis Family:** $m = 11$ specialist hypotheses at primary 20 bps cost tier.
- **Multiple Testing:** Holm-Bonferroni step-down correction over the 11 hypotheses.

### Level 2: Portfolio-Level Inference (Synchronized Multi-Asset)
- **Estimand:** Portfolio cumulative return, annualized Sharpe ratio, and maximum drawdown under shared equity.
- **Resampling Unit:** Synchronized 5m calendar time blocks across all 11 instruments simultaneously.
- **Resampling Method:** Synchronized Moving Block Bootstrap (SMBB). When block $[t, t+b]$ is sampled, the entire 11-asset market slice for those timestamps is extracted.
- **Simulation in Resampled Universe:** Concurrency queue and margin allocation rules are simulated chronologically inside each bootstrap sample, strictly preserving simultaneous entries and queue rejections.
- **Bootstrap Repetitions:** $B = 5,000$ full portfolio equity curve simulations.

---

## 3. BOOTSTRAP SENSITIVITY GRID

To ensure conclusions are robust against block length selection, both Level 1 and Level 2 evaluations must execute across the 4-tier block sensitivity grid:
- $b = 12$ bars ($1$ hour): Captures short-term intra-horizon execution dependencies.
- $b = 24$ bars ($2$ hours): **Primary benchmark** (matches Phase 5.4.4 & Phase 5.4.6).
- $b = 48$ bars ($4$ hours): Captures half-day funding cycle persistence.
- $b = 96$ bars ($8$ hours): Captures full 8-hour perpetual funding settlement cycle.
