# QUANTUM PHASE 5.2 - LABEL QUALITY & SENSITIVITY REPORT

**Author:** Senior Quantitative Research Engineer & Financial Data Auditor  
**Date:** 2026-11-01  
**Repository:** https://github.com/RAYDENFLY/quantum-multi-agent  
**Scope:** Label Statistical Profiling, Cross-Asset Comparison, and Target Robustness Sensitivity  
**Evaluation Data:** [phase5_2_label_analysis.json](file:///d:/quantum-multi-agent/data/historical/phase5_2_label_analysis.json)  

---

## 1. AGGREGATE LABEL QUALITY PROFILE (CANDIDATE MULTIPLIER: 1.5)

Across all 11 target perpetual futures instruments on the 5m timeframe, the triple-barrier label generator evaluated 3,248,862 candle records.

### Global Dataset Aggregate Statistics
- **Total Candles Evaluated:** 3,248,862
- **Eligible Target Samples:** 3,234,142 (99.55%)
- **Take Profit (TP):** 1,393,191 (**43.08%**)
- **Stop Loss (SL):** 1,400,798 (**43.31%**)
- **Time Expiration (EXP):** 440,153 (**13.61%**)
- **Ambiguous Intrabar Touches:** 14,104 (**0.43%**)
- **Excluded Pipeline Samples:** 616 (**0.02%**)
- **TP to SL Symmetry Ratio:** 0.995 (exceptional near-perfect symmetry)

---

## 2. CROSS-ASSET COMPARISON TABLE (MULTIPLIER: 1.5)

| Instrument | Total Candles | Eligible Samples | TP Count | TP % | SL Count | SL % | Exp Count | Exp % | Ambiguous Count | Excluded Count |
|---|---|---|---|---|---|---|---|---|---|---|
| **ADAUSDT** | 316,500 | 314,788 | 137,975 | 43.83% | 138,895 | 44.12% | 37,918 | 12.04% | 1,656 | 56 |
| **XRPUSDT** | 316,500 | 314,810 | 136,100 | 43.23% | 138,393 | 43.96% | 40,317 | 12.81% | 1,634 | 56 |
| **BTCUSDT** | 316,499 | 314,939 | 145,185 | 46.10% | 146,833 | 46.62% | 22,921 | 7.28% | 1,492 | 68 |
| **BNBUSDT** | 316,500 | 315,378 | 138,916 | 44.05% | 137,307 | 43.54% | 39,155 | 12.41% | 1,066 | 56 |
| **ETHUSDT** | 316,500 | 315,042 | 143,778 | 45.64% | 144,705 | 45.93% | 26,559 | 8.43% | 1,402 | 56 |
| **SOLUSDT** | 316,500 | 315,262 | 144,561 | 45.85% | 145,917 | 46.28% | 24,784 | 7.87% | 1,182 | 56 |
| **AVAXUSDT** | 316,500 | 315,405 | 120,014 | 38.05% | 122,544 | 38.85% | 72,847 | 23.10% | 1,039 | 56 |
| **LINKUSDT** | 316,500 | 315,341 | 124,676 | 39.54% | 126,507 | 40.12% | 64,158 | 20.33% | 1,103 | 56 |
| **XMRUSDT** | 83,863 | 83,528 | 38,284 | 45.83% | 37,262 | 44.61% | 7,982 | 9.55% | 291 | 44 |
| **DOGEUSDT** | 316,500 | 314,906 | 136,864 | 43.46% | 139,102 | 44.17% | 38,940 | 12.36% | 1,538 | 56 |
| **LTCUSDT** | 316,500 | 314,743 | 126,838 | 40.29% | 123,333 | 39.19% | 64,572 | 20.52% | 1,701 | 56 |
| **TOTAL** | **3,248,862** | **3,234,142** | **1,393,191** | **43.08%** | **1,400,798** | **43.31%** | **440,153** | **13.61%** | **14,104** | **616** |

---

## 3. INVESTIGATION OF THE PHASE 5.0 BENCHMARK DISTRIBUTION

Phase 5.0 noted an initial reported distribution of approximately:
- Take Profit: 45.9%
- Stop Loss: 50.3%
- Expiration: 3.8%

### Empirical Findings on Full 3-Year Historical Dataset
1. **BTCUSDT Distribution Alignment:**
   On BTCUSDT (the most liquid reference asset), at multiplier $M = 1.0$, the empirical distribution is:
   - TP: 48.69% | SL: 49.10% | Expiration: 2.20%
   At multiplier $M = 1.5$:
   - TP: 46.10% | SL: 46.62% | Expiration: 7.28%
   In 2026 alone for BTCUSDT, TP is 47.38%, SL is 48.59%, and Expiration is 4.03%, matching the benchmark almost exactly.
2. **Cross-Asset Heterogeneity:**
   The benchmark distribution cannot be applied uniformly across all 11 crypto perpetuals:
   - High-liquidity majors (BTC, ETH, SOL) exhibit high barrier resolution with low expiration rates (7% to 8%).
   - Mid-cap and older altcoins (AVAX, LINK, LTC) exhibit significantly higher expiration rates (20% to 23%), reflecting longer intraday consolidation cycles relative to their 20-bar volatility baseline.
3. **No Artificial Balancing:**
   QUANTUM adheres strictly to scientific data integrity. No oversampling, undersampling, SMOTE, or synthetic balancing was applied. The true natural market target distributions are preserved verbatim.

---

## 4. TEMPORAL & REGIME BREAKDOWN (BTCUSDT BENCHMARK)

### Annual Breakdown (BTCUSDT 5m, Multiplier: 1.5)
| Year | Eligible Samples | TP % | SL % | Exp % | Market Character |
|---|---|---|---|---|---|
| **2023** (Q4) | 18,362 | 46.46% | 46.00% | 7.54% | Early expansion regime |
| **2024** | 105,088 | 45.00% | 44.84% | 10.16% | Bull breakout & ETF inflows |
| **2025** | 104,550 | 46.08% | 46.86% | 7.06% | High volatility cycling |
| **2026** (to Q4) | 86,939 | 47.38% | 48.59% | 4.03% | Maturing trend structure |

### Partition Breakdown (BTCUSDT 5m, Multiplier: 1.5)
| Partition | Eligible Samples | TP % | SL % | Exp % |
|---|---|---|---|---|
| **Development** (2023-11 to 2025-10) | 209,679 | 45.45% | 45.66% | 8.89% |
| **Validation** (2025-11 to 2026-04) | 51,809 | 47.44% | 48.61% | 3.95% |
| **Final Holdout** (2026-05 to 2026-10) | 52,585 | 47.38% | 48.53% | 4.09% |

### Market Regime Breakdown (BTCUSDT 5m, Multiplier: 1.5)
Regime is defined by `trend_state` from the feature engine:
- Bullish: `EMA_50 > EMA_200` with positive slope.
- Bearish: `EMA_50 < EMA_200` with negative slope.
- Neutral: EMA consolidation or conflicting slope.

| Regime | Eligible Samples | TP Count | TP % | SL Count | SL % | Exp Count | Exp % |
|---|---|---|---|---|---|---|---|
| **Bullish** | 106,527 | 47,986 | 45.05% | 50,541 | 47.44% | 8,000 | 7.51% |
| **Bearish** | 92,721 | 43,872 | 47.32% | 42,759 | 46.12% | 6,090 | 6.57% |
| **Neutral** | 115,513 | 53,228 | 46.08% | 53,461 | 46.28% | 8,824 | 7.64% |

*Key Insight:* Even under sustained directional regimes, 5m symmetric volatility barriers maintain exceptional balance (within 2.4% between TP and SL), preventing directional target bias.

---

## 5. TARGET ROBUSTNESS SENSITIVITY ANALYSIS

A sensitivity analysis was conducted across three barrier multipliers ($M = 1.0$, $M = 1.5$, $M = 2.0$) while holding horizon fixed at $H = 12$ candles (60 minutes) and volatility lookback at $w = 20$ candles.

### Aggregate Sensitivity Across All 11 Instruments
| Metric | Multiplier 1.0 | Multiplier 1.5 (Candidate) | Multiplier 2.0 |
|---|---|---|---|
| **Eligible Samples** | 3,204,257 | 3,234,142 | 3,241,695 |
| **Take Profit (TP) %** | 45.89% | 43.08% | 38.73% |
| **Stop Loss (SL) %** | 45.82% | 43.31% | 39.18% |
| **Time Expiration %** | 8.29% | 13.61% | 22.09% |
| **Ambiguous Double-Touch Count** | 43,989 (1.35%) | 14,104 (0.43%) | 6,551 (0.20%) |
| **Ambiguity Reduction vs M=1.0** | Baseline | **-67.9% reduction** | **-85.1% reduction** |

### Robustness Findings
1. **Trade-Off between Expiration and Ambiguity:**
   - At $M = 1.0$, barriers are tighter, yielding a low expiration rate (8.29%), but intrabar double-touches are 3.1x more frequent (43,989 bars), resulting in higher target ambiguity.
   - At $M = 2.0$, ambiguous touches drop to 0.20%, but expiration rises sharply to 22.09%, reducing decisive trade outcomes.
   - At $M = 1.5$ (the approved candidate), the design achieves an optimal balance: ambiguous touches drop to a negligible 0.43% while expiration remains bounded at 13.61%, with robust symmetry across all assets.
2. **Target Stability:**
   The candidate multiplier ($1.5$) demonstrates strong stability across market regimes, years, and instruments.
3. **No Optimization on Holdout:**
   This sensitivity analysis serves purely to characterize target behavior. No target parameter or threshold was selected or optimized using the Final Holdout partition.
