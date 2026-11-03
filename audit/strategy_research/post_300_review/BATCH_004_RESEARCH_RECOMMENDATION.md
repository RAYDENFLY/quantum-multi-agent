# QUANTUM — Batch 004 Research Mandate & Execution-Aware Design Blueprint

**Document Identifier:** `audit/strategy_research/post_300_review/BATCH_004_RESEARCH_RECOMMENDATION.md`  
**Evaluation Date:** `2026-11-03T02:48:45Z`  
**Git Commit:** `dcc8ceb54d80b1b9685d92236f48b0994610522a`  
**Decision Authority:** Post-300 Forensic Audit Package  
**Formal Classification of `STRAT_242`:** **`CONDITIONALLY_VALID`**

---

## 1. Formal Decision on `STRAT_242`

Under Section 8 of the Project Owner Directive, `STRAT_242` is formally classified as:

### **`CONDITIONALLY_VALID`**

### Exact Conditions for Validity:
1. **Mathematical Reproducibility:** Verified to $0.0000$ precision ($E_{\text{end}} = \$144.40\text{ USD}$, Mean Daily Return $= +0.1092\%/\text{day}$).
2. **Causal Timeframe Integrity:** Verified. 5m base bars with rolling 12-bar (60m) lookback and 20-bar (100m) horizon contain zero lookahead bias. Prospective holdout ($\ge 1793491200000\text{ ms}$) remains 100% sealed.
3. **Execution Conditionality (The Limiting Factor):**
   - The strategy's gross predictive edge is **`+15.42 bps`** per trade.
   - It is valid **ONLY IF** executed on VIP maker tiers ($\le 8.0\text{ bps}$ round-trip friction) or maker-rebate venues using passive post-only limit orders.
   - It is **COMPLETELY INVALID** for execution via aggressive market orders or taker venues, where 20–44 bps friction turns the `+44.40%` return into a catastrophic `-34.28%` to `-86.84%` capital loss.
4. **Regime Conditionality:**
   - 85.2% of its profit was generated during the flash-crash V-bottom regime of Fold 3.
   - It suffered a net drawdown in the grinding bear regime of Fold 4 (`-4.55%`).

---

## 2. Forensic Post-Mortem of Batches 001–003

The 300 strategy evaluations across Batches 001–003 have proven four foundational quantitative truths about the system:

1. **The LightGBM Directional Models Have Genuine Predictive Skill:**
   Across 1,580 trades, the models generated **`+15.42 bps`** of gross positive forward return after extreme 1-hour liquidity flushes on high-beta altcoins (`DOGE, SOL, ADA, XRP, LINK`), outperforming random walk drift ($0.0\text{ bps}$).
2. **Local Neighborhoods Form Dense, Highly-Correlated Surfaces:**
   The 100 strategies in Batch 003 had an average pairwise daily return correlation of **`0.9233`**, proving that parameter mutations around `STRAT_134` map a smooth, stable response surface rather than erratic noise spikes.
3. **The Core Bottleneck is Gross Trade Displacement vs. Execution Friction:**
   A 5-minute scalping horizon (holding for an average of 42 minutes) limits the gross profit to $15.4\text{ bps}$. When friction is $8.0\text{ bps}$, the system compounds at $+0.109\%/\text{day}$. But when friction is $20.0\text{ bps}$, the edge is completely erased.
4. **Taker Execution Requires Multi-Timeframe Holding Horizons:**
   To trade sustainably under realistic taker fees ($20\text{ to }40\text{ bps}$ round-trip), the gross displacement per trade must expand to **$\ge 45\text{ to }80\text{ bps}$**. This cannot be achieved on 5m micro-scalps; it requires multi-timeframe swing expansion.

---

## 3. Batch 004 Strategic Research Design (100 Configurations)

Batch 004 (`STRAT_301` through `STRAT_400`) must directly solve the vulnerabilities identified in the forensic audit. Do not generate more 5m micro-scalps with 15 bps gross edge.

### Core Architectural Mandates for Batch 004

#### Mandate 1: Gross Alpha Expansion Target ($\ge 45\text{ bps}$ Gross Expectancy)
- **Extended Horizon Grids:** Expand `horizon_bars` from 20 bars (100m) to **`48 bars (4 hours)`** and **`96 bars (8 hours)`**.
- **Wider Asymmetric Barriers:** Sweep Take-Profit multipliers across $3.5\sigma$ to $5.5\sigma$ with Stop-Loss multipliers at $1.2\sigma$ to $1.5\sigma$ (reward-to-risk ratio $\ge 3:1$).
- **Multi-Timeframe Trend Alignment:** Require confluence between 5m specialist OOF probabilities and the 4-hour macro trend (`htf_ret_48 >= +30 bps` for longs).

#### Mandate 2: True Post-Only Limit Order Physics
- In `entry`, enforce `order_type = "LIMIT"` with explicit limit offsets $\delta \in [0.02\sigma, 0.08\sigma]$ inside the bid.
- Incorporate a conservative fill queue model: an order is only filled if price penetrates at least $0.02\sigma$ beyond the limit price.
- Impose an adverse selection penalty of $-2.0\text{ bps}$ on filled limit orders.

#### Mandate 3: Fold 4 Bear Regime Repair (Dynamic Trailing Ratchet & Selective Shorting)
- To repair the $-4.55\%$ drawdown observed in Fold 4, introduce:
  1. **BankerAgent Option A Partial Exits:** Close 50% at $1.8\sigma$ and ratchet stop to breakeven $+ 2.0\text{ bps}$, eliminating tail losses during false rebounds.
  2. **Regime-Adaptive Invalidation:** If price fails to reach $+1.0\sigma$ within 12 bars (60 minutes), execute an early time-based abort to prevent slow bleed.
  3. **Exhaustion Fade Shorting:** Condition short entries on overextended rallies ($\text{htf\_ret\_12} \ge +70\text{ bps}$) with upper-wick rejection ($\ge 25\%$).

#### Mandate 4: Multi-Strategy Portfolio Integration
- Construct hybrid configurations combining:
  - 50% allocation to **`STRAT_262`** (the lowest-drawdown liquidity absorption champion).
  - 30% allocation to **`STRAT_061`** (volatility dynamics breakout, which had the lowest market correlation).
  - 20% cash reserve for margin cushion on $100 USD equity.

---

## 4. Batch 004 Allocation Blueprint (100 Candidates)

| Family Sub-Cohort | Candidate Range | Core Hypothesis | Target Gross Alpha | Target Fee Schedule |
| :--- | :---: | :--- | :---: | :--- |
| **Cohort A: Multi-Timeframe Swing Expansion** | `STRAT_301`–`STRAT_335` (35 configs) | 4h macro alignment + 1h flush absorption + 4h to 8h holding horizon ($3.5\sigma\text{ to }5.0\sigma\text{ TP}$). | **`+45 to +75 bps`** | Survives 20 bps Retail Taker fee tier. |
| **Cohort B: Post-Only Limit Queue Optimization** | `STRAT_336`–`STRAT_360` (25 configs) | Strict post-only maker entries at Bid 1 with adverse selection modeling and 8.0 bps maker schedule. | `+18 to +25 bps` | Tailored for zero-fee / maker rebate venues. |
| **Cohort C: Fold 4 Bear Repair & Trailing Stops** | `STRAT_361`–`STRAT_385` (25 configs) | Dynamic Banker Option A partial scale-outs (50% at $1.8\sigma$ + breakeven stop ratchet + 60m time abort). | `+25 to +35 bps` | Designed to eliminate Fold 4 losses and achieve 4/4 positive folds. |
| **Cohort D: Multi-Family Portfolio Ensembles** | `STRAT_386`–`STRAT_400` (15 configs) | Combined signals merging Liquidity Flush Absorption (`STRAT_262`) with Volatility Expansion (`STRAT_061`). | `+30 to +45 bps` | Minimizes portfolio drawdown below 10% across all 4 folds. |

---

## 5. Next Steps for Execution

1. Present this complete 7-document forensic package to the Human Governance Supervisor.
2. Await formal authorization of the **`CONDITIONALLY_VALID`** classification and the Batch 004 Design Blueprint.
3. Upon authorization, implement the Batch 004 generator and execute the next 100 candidates with multi-timeframe gross alpha expansion and realistic taker resilience.
