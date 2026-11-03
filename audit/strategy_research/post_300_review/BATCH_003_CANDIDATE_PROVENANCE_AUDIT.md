# QUANTUM — Batch 003 Candidate Provenance & Selection Integrity Audit

**Document Identifier:** `audit/strategy_research/post_300_review/BATCH_003_CANDIDATE_PROVENANCE_AUDIT.md`  
**Evaluation Date:** `2026-11-03T02:47:00Z`  
**Git Commit:** `dcc8ceb54d80b1b9685d92236f48b0994610522a`  
**Target of Investigation:** Scientific explanation of why all 100 configurations in Batch 003 (`STRAT_201` to `STRAT_300`) generated positive net cumulative returns.

---

## 1. Executive Summary & Forensic Resolution

> [!IMPORTANT]
> **WHY ALL 100 BATCH 003 STRATEGIES WERE POSITIVE:**  
> The observation that 100% of Batch 003 configurations produced positive net cumulative returns (`+0.63%` to `+47.79%`) is **NOT evidence of 100 separate, newly discovered alphas**.  
> Instead, it is the mathematical result of:
> 1. **High Pairwise Correlation ($\bar{\rho} = 0.9233$):** All 100 candidates are minor grid perturbations around a single proven ancestor (`STRAT_134`), trading the exact same 5 assets (`DOGE, SOL, ADA, XRP, LINK`), in the exact same direction (`LONG_ONLY`), on the exact same underlying market anomaly (buying bounces after extreme 1-hour crashes $\le -77\text{ bps}$).
> 2. **Fee Tier Dependency (8.0 bps Maker Assumption):** The underlying gross displacement of this anomaly averages `+13.5 to +16.0 bps`. Because all 100 candidates were evaluated under the `maker_passive` fee tier (8.0 bps round-trip friction), every single variation retained a net edge of `+5.0 to +8.0 bps`.
> 3. **Friction Fragility:** When evaluated under realistic taker friction (20.0 bps or 44.0 bps), **all 100 Batch 003 strategies simultaneously produce net losses**.

---

## 2. Provenance & Lineage Architecture

The generation tree from Batch 001 to Batch 003 followed a structured exploitation trajectory:

```
Batch 001 Discovery (100 candidates across 7 families)
       |
       +---> STRAT_061 (Volatility Dynamics, +13.88% net return)
       |
       v
Batch 002 Exploitation (60 Exploitation + 40 Exploration)
       |
       +---> STRAT_134 (Liquidity Flush Reclaim, +36.16% net return)
       |
       v
Batch 003 Local Neighborhood Sweep (100 fine perturbations of STRAT_134)
       |
       +---> STRAT_201 to STRAT_300 (Dense local response surface)
       |
       +---> STRAT_242 (+44.40% net return, Peak of the local response surface)
```

### 2.1 The Mutation Grid in `generator.py`
In `src/quantum/strategies/generator.py` lines 498–546, Batch 003 was constructed by forming a Cartesian grid around the parameters of `STRAT_134`:
- **Base Ancestor (`STRAT_134`):**
  - Assets: `("DOGEUSDT", "SOLUSDT", "ADAUSDT", "XRPUSDT", "LINKUSDT")`
  - Direction: `"LONG_ONLY"`
  - `prob_margin_min`: `0.22`
  - `htf_return_max_bps`: `-85.0 bps`
  - `tp1_multiplier`: `2.8`
  - `sl_multiplier`: `1.15`
  - `risk_per_trade_pct`: `0.022`
- **Batch 003 Perturbation Deltas:**
  - `pm_deltas = [-0.02, -0.01, 0.0, 0.01, 0.02]` $\rightarrow \text{margin} \in [0.20, 0.24]$
  - `htf_deltas = [-8.0, -4.0, 0.0, 4.0, 8.0]` $\rightarrow \text{htf\_max} \in [-93.0, -77.0\text{ bps}]$
  - `tp_deltas = [-0.2, 0.0, 0.2, 0.4]` $\rightarrow \text{TP} \in [2.6, 3.2]$
  - Sizing & SL variations: $\text{SL} \in [1.10, 1.20]$, $\text{risk} \in [0.018, 0.026]$.

Total candidates: $5 \times 5 \times 4 = 100\text{ configurations}$ (`STRAT_201` to `STRAT_300`).

---

## 3. Cross-Candidate Correlation Matrix & Effective Degrees of Freedom

To determine how many genuinely independent bets Batch 003 represents, `scripts/run_post_300_forensic_review.py` calculated the daily return correlation matrix across all 100 strategies:

$$\mathbf{R} \in \mathbb{R}^{365 \times 100}, \quad \mathbf{C} = \text{Corr}(\mathbf{R})$$

### Correlation Statistics Across All 4,950 Off-Diagonal Pairs
- **Arithmetic Mean Correlation ($\bar{\rho}$):** **`0.9233`**
- **Median Correlation:** **`0.9315`**
- **Minimum Pairwise Correlation:** **`0.7957`**
- **Maximum Pairwise Correlation:** **`0.9878`**

```
Distribution of Pairwise Correlations in Batch 003:
0.75 - 0.80 | ## (2%)
0.80 - 0.85 | ###### (6%)
0.85 - 0.90 | ################# (17%)
0.90 - 0.95 | ################################################ (48%)
0.95 - 1.00 | ########################### (27%)
```

### Effective Number of Independent Strategies ($N_{\text{eff}}$)
Using the eigenvalue decomposition of the correlation matrix (Breitung / Meucci effective dimension):
$$N_{\text{eff}} = \frac{(\sum \lambda_i)^2}{\sum \lambda_i^2} \approx 2.14$$
- The 100 strategies in Batch 003 collapse into **approximately 2 independent statistical components**.
- The first principal component (PC1) explains **`92.8%`** of the total variance across all 100 strategies.
- **Forensic Interpretation:** Batch 003 was not testing 100 different hypotheses. It was mapping the local convexity of a single hypothesis.

---

## 4. Selection Bias & Overfitting Audit

| Audit Item | Forensic Check | Finding |
| :--- | :--- | :--- |
| **Dataset Consistency** | Were all 100 strategies tested on the exact same dataset? | Yes, identically on Folds 1–4 canonical parquets. |
| **Validation Isolation** | Did Batch 003 access Fold 5 or Prospective Holdout? | No, Fold 5 and Holdout remained 100% sealed. |
| **Strategy Selection Leakage** | Were parameters fit on the test period? | The models were trained in Phase 5.3 and frozen. The execution overlay parameters were selected based on Batch 001/002 results. |
| **Multiple Testing Inflation** | Did testing 100 variations artificially inflate the champion's return? | **YES.** When selecting the maximum of 100 correlated series, the top configuration (`STRAT_242`, +44.40%) is partially an upward statistical fluctuation from the mean neighborhood return (+21.45%). |

---

## 5. Provenance Verdict

1. The 100 positive results in Batch 003 do **not** represent 100 independent alpha discoveries.
2. They prove that the **1-hour liquidity flush absorption anomaly is locally robust** across parameter perturbations (the response surface is smoothly positive under low fees, without sharp cliff-edges).
3. However, selecting `STRAT_242` as the sole global champion overestimates future expected return due to **selection-induced winner's curse**. The expected return of the strategy class should be shrunk toward the neighborhood median (**`+21.45%` net return, or `+0.055%/day`**), rather than the peak observation (`+44.40%`).
