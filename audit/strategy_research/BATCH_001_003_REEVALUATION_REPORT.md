# QUANTUM — HIGH-TURNOVER ALPHA FEASIBILITY STUDY
## Forensic Batch Re-Evaluation Report: Batches 001–003 (300 Strategy Configurations)

**Date of Execution:** 2026-11-03  
**Branch:** `research/high-turnover-alpha-feasibility`  
**Git Commit Baseline:** `dcc8ceb54d80b1b9685d92236f48b0994610522a`  
**Execution Simulator Version:** `phase_5_6_2_remediated_v1.5`  
**Dataset Reference:** `ASTER_CANONICAL_5M_FOLDS_1_4` (10 Primary Research Assets, 4,499,997 historical bars)  
**Prospective Holdout Status:** **STRICTLY SEALED** ($\ge \text{1793491200000 ms}$ / 2026-11-01 00:00:00 UTC)  
**Total Strategies Evaluated:** 300 (295 historically misconfigured + 5 non-misconfigured controls)  
**Evaluation Scenarios:** 3 distinct execution venue models (900 total backtest runs)  

---

## 1. Executive Summary & Forensic Findings

### 1.1 The Forensic Baseline
During Session 1 and Session 1.5, forensic code and manifest audits revealed that **295 out of 300 strategy configurations ($98.3\%$)** generated across Batches 001, 002, and 003 contained a critical execution-cost misconfiguration:
- Aggressive `MARKET` order entries crossed the bid-ask spread and took order book depth immediately at arrival.
- However, the portfolio risk evaluator coupled them to an optimistic `maker_passive` fee tier ($8.0\text{ bps}$ round-trip fee, $0.0\text{ bps}$ spread, $0.0\text{ bps}$ arrival slippage).
- Furthermore, limit order gap-down fills awarded artificial price improvement (`min(opens[k], limit_px)`), and touch fill probabilities assumed 100% fill rates on shallow bar touches.

In accordance with Project Owner authorization, all 300 configurations from Batches 001–003 were systematically re-evaluated across three independent venue cost scenarios without altering any strategy signal, entry/exit gating, parameter, or portfolio sizing logic.

### 1.2 High-Level Re-Evaluation Results

| Metric | Historical Baseline (Misconfigured) | Scenario 1: Realistic Retail Taker (`BYBIT_VIP0_DEFAULT`) | Scenario 2: DEX Stress Taker (`ASTER_STRESS_TAKER`) | Scenario 3: Maker Post-Only Venue (`MAKER_PASSIVE_TRUE`) |
| :--- | :---: | :---: | :---: | :---: |
| **Total Configurations** | 300 | 300 | 300 | 300 |
| **Historically Misconfigured Subset** | 295 | 295 | 295 | 295 |
| **Round-Trip Friction** | $8.0\text{ bps}$ flat | $\mathbf{15.0\text{ bps}}$ (11.0 fee + 4.0 drag) | $\mathbf{44.0\text{ bps}}$ (40.0 fee + 4.0 drag) | $\mathbf{9.5\text{ bps}}$ (8.0 fee + 1.5 adverse) |
| **Single-Channel Cash Drag Applied** | No (flat deduction) | **Yes (Anti-Double-Counting Active)** | **Yes (Anti-Double-Counting Active)** | **Yes (Anti-Double-Counting Active)** |
| **Gap-Down Price Fix ($P_{\text{fill}} \equiv P_{\text{limit}}$)** | No (buggy) | **Yes (Enforced)** | **Yes (Enforced)** | **Yes (Enforced)** |
| **Positive Net Return Count** | **142 / 300** ($47.3\%$) | **1 / 300** ($0.33\%$) | **0 / 300** ($0.00\%$) | **0 / 300** ($0.00\%$) |
| **Fully Qualified Count** | **28 / 300** ($9.3\%$) | **0 / 300** ($0.00\%$) | **0 / 300** ($0.00\%$) | **0 / 300** ($0.00\%$) |
| **Mean Net Return** | $+3.14\%$ | **-40.67%** | **-82.30%** | **-56.15%** |
| **Median Net Return** | $-0.85\%$ | **-42.27%** | **-86.50%** | **-59.28%** |
| **Mean Ending Equity ($100 USD base)** | $\$103.14$ | **$59.33** | **$17.70** | **$43.85** |
| **Mean Profit Factor** | $1.042$ | **0.856** | **0.567** | **0.784** |
| **Mean Maximum Drawdown** | $22.40\%$ | **43.91%** | **82.43%** | **57.52%** |
| **Top Performer Strategy** | `STRAT_242` ($+44.40\%$) | `STRAT_075` ($+2.93\%$) | `STRAT_016` ($-13.47\%$) | `STRAT_075` ($-6.92\%$) |
| **`STRAT_242` Recalculated Return** | $+44.40\%$ ($144.40$) | **-46.00% ($54.00)** | **-88.46% ($11.54)** | **-63.88% ($36.12)** |

### 1.3 Key Institutional Takeaways
1. **The Historical Alpha Was Driven By Spread & Friction Subsidies:**
   The positive cumulative returns exhibited by 142 historical strategies—including all 28 historically "qualified" strategies—evaporate once realistic market order taker costs ($15.0\text{ bps}$ RT) are accounted for. Across 1,000 to 2,000 trades, an uncounted $7.0\text{ bps}$ of friction per trade creates a phantom cash subsidy of $\$40\text{ to }\$90$ on a $\$100$ portfolio.
2. **`STRAT_242` Rejection Is Irrevocably Confirmed:**
   Former global champion `STRAT_242` collapsed from $+44.40\%$ ($144.40 ending equity) to **$-46.00\%$** ($54.00 equity) under Bybit VIP0 retail friction, and to **$-88.46\%$** ($11.54 equity) under Aster stress taker friction. It breached the hard $30.0\%$ drawdown ceiling ($48.39\%$ MDD) and is formally rejected as valid alpha evidence.
3. **Turnover Is the Core Vulnerability:**
   Strategies with high trade counts ($1,500\text{--}2,000$ trades/year) suffered catastrophic erosion, while low-turnover strategies (e.g. `STRAT_075`, 601 trades; `STRAT_016`, 101 trades) showed relative resilience. `STRAT_075` achieved $+2.93\%$ net return under Bybit VIP0, but failed full qualification due to low profit factor ($1.027 < 1.05$) and fold instability.
4. **Passive Maker Execution Cannot Be Assumed Post-Hoc:**
   Simply re-labeling aggressive market strategies as maker orders without modifying their underlying entry logic produces steep losses ($-56.15\%$ mean return under `MAKER_PASSIVE_TRUE`), because marketable orders cross the spread regardless of label.

---

## 2. Evaluation Scope & Scenario Parameter Matrix

To ensure rigorous multi-horizon analysis, each of the 300 strategy configurations was evaluated across three distinct, mutually exclusive venue profiles:

```
                            300 STRATEGY CONFIGURATIONS
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼                                ▼                                ▼
   SCENARIO 1                       SCENARIO 2                       SCENARIO 3
BYBIT_VIP0_DEFAULT               ASTER_STRESS_TAKER               MAKER_PASSIVE_TRUE
Realistic Retail Taker          High-Friction Stress Taker       True Passive Post-Only
--------------------            --------------------------       ----------------------
Maker Fee: 2.0 bps/leg           Maker Fee: 4.0 bps/leg           Maker Fee: 4.0 bps/leg
Taker Fee: 5.5 bps/leg           Taker Fee: 20.0 bps/leg          Taker Fee: 10.0 bps/leg
Default Spread: 2.0 bps          Default Spread: 2.0 bps          Default Spread: 0.0 bps
Default Slip: 2.0 bps            Default Slip: 2.0 bps            Default Slip: 0.0 bps
Adverse Drag: 0.0 bps            Adverse Drag: 0.0 bps            Adverse Drag: 1.5 bps
Total RT Friction: 15.0 bps      Total RT Friction: 44.0 bps      Total RT Friction: 9.5 bps
```

### 2.1 Single-Channel Cash Friction Formula
Under all three scenarios, fill prices were logged at nominal benchmarks ($P_{\text{open}}$ for market, $P_{\text{limit}}$ for limit), and friction was deducted exclusively from the cash ledger:
$$\text{PnL}_{\text{net}} = N \cdot R_{\text{gross}} - \left[ C_{\text{fee}} + C_{\text{spread}} + C_{\text{slip}} + C_{\text{adverse}} \right] - C_{\text{fund}}$$
Where:
- $C_{\text{fee}} = N \cdot \left(\frac{\text{Fee}_{\text{entry}} + \text{Fee}_{\text{exit}}}{10,000}\right)$
- $C_{\text{spread}} = N \cdot \left(\frac{\text{Spread}_{\text{entry}} + \text{Spread}_{\text{exit}}}{10,000}\right)$ (strictly $0.0$ for MAKER fills)
- $C_{\text{slip}} = N \cdot \left(\frac{\text{Slip}_{\text{entry}} + \text{Slip}_{\text{exit}}}{10,000}\right)$ (strictly $0.0$ for MAKER fills)
- $C_{\text{adverse}} = N \cdot \left(\frac{\text{Adverse}_{\text{entry}} + \text{Adverse}_{\text{exit}}}{10,000}\right)$ (strictly $0.0$ for TAKER fills)

---

## 3. Forensic Investigation of `STRAT_242`

`STRAT_242` was the purported "Global Champion" of Phase 5.6.2 Batch 003, reporting $\$144.40$ ending equity ($+44.40\%$ net return) on $\$100$ initial capital.

### 3.1 Side-by-Side Performance Reconciliation

| Metric | Historical Baseline (Batch 003 Report) | Scenario 1: `BYBIT_VIP0_DEFAULT` | Scenario 2: `ASTER_STRESS_TAKER` | Scenario 3: `MAKER_PASSIVE_TRUE` |
| :--- | :---: | :---: | :---: | :---: |
| **Strategy ID** | `STRAT_242` | `STRAT_242` | `STRAT_242` | `STRAT_242` |
| **Family** | `MEAN_REVERSION_BREAKOUT` | `MEAN_REVERSION_BREAKOUT` | `MEAN_REVERSION_BREAKOUT` | `MEAN_REVERSION_BREAKOUT` |
| **Order Type** | `MARKET` | `MARKET` | `MARKET` | `MARKET` |
| **Ending Equity ($USD)** | **$144.40** | **$54.00** | **$11.54** | **$36.12** |
| **Net Cumulative Return** | **+44.40%** | **-46.00%** | **-88.46%** | **-63.88%** |
| **Net PnL ($USD)** | $+44.40$ | **-$46.00** | **-$88.46** | **-$63.88** |
| **Return Delta vs. Baseline** | — | **-90.40%** | **-132.86%** | **-108.28%** |
| **Profit Factor** | $1.214$ | **0.871** | **0.582** | **0.800** |
| **Maximum Drawdown** | $14.28\%$ | **48.39%** | **88.47%** | **64.75%** |
| **Mean Underwater Drawdown** | $4.85\%$ | **24.58%** | **52.12%** | **35.70%** |
| **Win Rate** | $44.51\%$ | **35.26%** | **34.13%** | **35.05%** |
| **Executed Trades** | 1,977 | 1,977 | 1,500 (capital starved) | 1,977 |
| **Total Fees Paid ($USD)** | $\$15.82$ | $\$58.97$ | $\$88.57$ | $\$90.36$ |
| **Total Spread Paid ($USD)** | $\$0.00$ | $\$10.14$ | $\$4.29$ | $\$0.00$ |
| **Total Slippage Paid ($USD)** | $\$0.00$ | $\$10.14$ | $\$4.29$ | $\$0.00$ |
| **Total Funding Paid ($USD)** | $\$0.45$ | $\$0.52$ | $\$0.20$ | $\$0.43$ |
| **Total Execution Drag ($USD)** | **$16.27** | **$79.77** | **$97.35** | **$90.79** |
| **Qualification Status** | **QUALIFIED** | **DISQUALIFIED** | **DISQUALIFIED** | **DISQUALIFIED** |
| **Failure Classification** | None | `EXCESSIVE_DRAWDOWN_BREACH` | `EXCESSIVE_DRAWDOWN_BREACH` | `EXCESSIVE_DRAWDOWN_BREACH` |

### 3.2 Anatomy of the Failure
- **Under `BYBIT_VIP0_DEFAULT`:** Total friction increased from $\$16.27$ to $\$79.77$ ($+\$63.50$ cash drag). Because the gross trading margin was only $+12.5\text{ bps}$ per trade, charging realistic taker friction ($15.0\text{ bps}$ RT) converted a $+4.5\text{ bps}$ net edge into a $-2.5\text{ bps}$ net loss per trade. Across 1,977 executions, this negative expectancy eroded $46\%$ of total portfolio capital.
- **Under `ASTER_STRESS_TAKER`:** At $44.0\text{ bps}$ RT friction, the strategy collapsed completely, losing $88.46\%$ of equity and suffering capital starvation after 1,500 trades.

---

## 4. Scenario Performance Leaderboards

### 4.1 Scenario 1 Leaderboard: `BYBIT_VIP0_DEFAULT` (Top 10 Performers)
*Realistic retail VIP0 schedule ($11.0\text{ bps}$ fee, $2.0\text{ bps}$ spread, $2.0\text{ bps}$ slip).*

| Rank | Strategy ID | Family | Recalc Net Ret | Ending Equity | Hist Net Ret | Return Delta | Profit Factor | Max DD | Trades | Positive Folds | Qualified | Failure Classification |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | `STRAT_075` | `MEAN_REVERSION_BREAKOUT` | **+2.93%** | **$102.93** | $+14.58\%$ | $-11.65\%$ | $1.027$ | $7.07\%$ | 601 | 2/4 | No | `FOLD_INSTABILITY_REGIME_MISMATCH` |
| **2** | `STRAT_074` | `MEAN_REVERSION_BREAKOUT` | **-1.50%** | **$98.50** | $+9.76\%$ | $-11.26\%$ | $0.987$ | $9.46\%$ | 609 | 2/4 | No | `NEGATIVE_NET_EXPECTANCY_FRICTION` |
| **3** | `STRAT_134` | `MEAN_REVERSION_BREAKOUT` | **-3.20%** | **$96.80** | $+36.16\%$ | $-39.36\%$ | $0.991$ | $25.19\%$ | 1,626 | 2/4 | No | `NEGATIVE_NET_EXPECTANCY_FRICTION` |
| **4** | `STRAT_061` | `VOLATILITY_DYNAMICS` | **-3.79%** | **$96.21** | $+13.88\%$ | $-17.67\%$ | $0.979$ | $14.28\%$ | 915 | 2/4 | No | `NEGATIVE_NET_EXPECTANCY_FRICTION` |
| **5** | `STRAT_146` | `MEAN_REVERSION_BREAKOUT` | **-4.41%** | **$95.59** | $+30.09\%$ | $-34.50\%$ | $0.986$ | $30.89\%$ | 1,475 | 2/4 | No | `EXCESSIVE_DRAWDOWN_BREACH` |
| **6** | `STRAT_007` | `LIQUIDITY_MICROSTRUCTURE` | **-7.88%** | **$92.12** | $+9.86\%$ | $-17.74\%$ | $0.957$ | $16.84\%$ | 919 | 1/4 | No | `NEGATIVE_NET_EXPECTANCY_FRICTION` |
| **7** | `STRAT_140` | `MEAN_REVERSION_BREAKOUT` | **-9.60%** | **$90.40** | $+25.29\%$ | $-34.89\%$ | $0.970$ | $35.27\%$ | 1,446 | 2/4 | No | `EXCESSIVE_DRAWDOWN_BREACH` |
| **8** | `STRAT_099` | `ADAPTIVE_ENTRY_EXECUTION` | **-11.14%** | **$88.86** | $-71.70\%$ | $+60.56\%$ | $0.954$ | $22.69\%$ | 1,173 | 2/4 | No | `NEGATIVE_NET_EXPECTANCY_FRICTION` |
| **9** | `STRAT_143` | `MEAN_REVERSION_BREAKOUT` | **-11.25%** | **$88.75** | $+21.54\%$ | $-32.79\%$ | $0.963$ | $33.78\%$ | 1,419 | 2/4 | No | `EXCESSIVE_DRAWDOWN_BREACH` |
| **10** | `STRAT_001` | `LIQUIDITY_MICROSTRUCTURE` | **-11.39%** | **$88.61** | $+6.52\%$ | $-17.91\%$ | $0.961$ | $19.46\%$ | 920 | 2/4 | No | `NEGATIVE_NET_EXPECTANCY_FRICTION` |

*Note on `STRAT_099`: This configuration was historically evaluated under `baseline_taker` ($44.0\text{ bps}$ friction), where it lost $-71.70\%$. When evaluated under `BYBIT_VIP0_DEFAULT` ($15.0\text{ bps}$ friction), its loss moderated to $-11.14\%$ ($+\$60.56\%$ delta), demonstrating that the evaluator correctly models lower friction.*

---

### 4.2 Scenario 2 Leaderboard: `ASTER_STRESS_TAKER` (Top 10 Performers)
*DEX stress schedule ($40.0\text{ bps}$ fee, $2.0\text{ bps}$ spread, $2.0\text{ bps}$ slip).*

| Rank | Strategy ID | Family | Recalc Net Ret | Ending Equity | Hist Net Ret | Return Delta | Profit Factor | Max DD | Trades | Positive Folds | Qualified | Failure Classification |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | `STRAT_016` | `MARKET_REGIME_TRANSITIONS` | **-13.47%** | **$86.53** | $-3.56\%$ | $-9.91\%$ | $0.302$ | $13.47\%$ | 101 | 0/4 | No | `NEGATIVE_NET_EXPECTANCY_FRICTION` |
| **2** | `STRAT_085` | `ADAPTIVE_ENTRY_EXECUTION` | **-18.56%** | **$81.44** | $-3.93\%$ | $-14.63\%$ | $0.505$ | $18.56\%$ | 155 | 0/4 | No | `NEGATIVE_NET_EXPECTANCY_FRICTION` |
| **3** | `STRAT_008` | `LIQUIDITY_MICROSTRUCTURE` | **-21.30%** | **$78.70** | $-1.50\%$ | $-19.80\%$ | $0.614$ | $21.30\%$ | 211 | 1/4 | No | `NEGATIVE_NET_EXPECTANCY_FRICTION` |
| **4** | `STRAT_002` | `LIQUIDITY_MICROSTRUCTURE` | **-34.46%** | **$65.54** | $-6.32\%$ | $-28.14\%$ | $0.533$ | $35.48\%$ | 341 | 1/4 | No | `EXCESSIVE_DRAWDOWN_BREACH` |
| **5** | `STRAT_013` | `MARKET_REGIME_TRANSITIONS` | **-34.88%** | **$65.12** | $+1.14\%$ | $-36.02\%$ | $0.625$ | $36.70\%$ | 417 | 1/4 | No | `EXCESSIVE_DRAWDOWN_BREACH` |
| **6** | `STRAT_075` | `MEAN_REVERSION_BREAKOUT` | **-41.97%** | **$58.03** | $+14.58\%$ | $-56.55\%$ | $0.706$ | $42.06\%$ | 601 | 0/4 | No | `EXCESSIVE_DRAWDOWN_BREACH` |
| **7** | `STRAT_074` | `MEAN_REVERSION_BREAKOUT` | **-43.23%** | **$56.77** | $+9.76\%$ | $-52.99\%$ | $0.672$ | $43.23\%$ | 609 | 0/4 | No | `EXCESSIVE_DRAWDOWN_BREACH` |
| **8** | `STRAT_014` | `MARKET_REGIME_TRANSITIONS` | **-51.10%** | **$48.90** | $-2.28\%$ | $-48.82\%$ | $0.559$ | $51.35\%$ | 545 | 0/4 | No | `EXCESSIVE_DRAWDOWN_BREACH` |
| **9** | `STRAT_004` | `LIQUIDITY_MICROSTRUCTURE` | **-54.34%** | **$45.66** | $+3.15\%$ | $-57.49\%$ | $0.669$ | $54.34\%$ | 636 | 1/4 | No | `EXCESSIVE_DRAWDOWN_BREACH` |
| **10** | `STRAT_005` | `LIQUIDITY_MICROSTRUCTURE` | **-54.67%** | **$45.33** | $+2.85\%$ | $-57.52\%$ | $0.667$ | $54.67\%$ | 636 | 1/4 | No | `EXCESSIVE_DRAWDOWN_BREACH` |

---

### 4.3 Scenario 3 Leaderboard: `MAKER_PASSIVE_TRUE` (Top 10 Performers)
*Passive schedule ($8.0\text{ bps}$ RT fee, $0.0\text{ bps}$ spread, $0.0\text{ bps}$ slip, $1.5\text{ bps}$ adverse selection).*

| Rank | Strategy ID | Family | Recalc Net Ret | Ending Equity | Hist Net Ret | Return Delta | Profit Factor | Max DD | Trades | Positive Folds | Qualified | Failure Classification |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | `STRAT_075` | `MEAN_REVERSION_BREAKOUT` | **-6.92%** | **$93.08** | $+14.58\%$ | $-21.50\%$ | $0.937$ | $10.86\%$ | 601 | 2/4 | No | `NEGATIVE_NET_EXPECTANCY_FRICTION` |
| **2** | `STRAT_016` | `MARKET_REGIME_TRANSITIONS` | **-6.98%** | **$93.02** | $-3.56\%$ | $-3.42\%$ | $0.519$ | $6.98\%$ | 101 | 0/4 | No | `NEGATIVE_NET_EXPECTANCY_FRICTION` |
| **3** | `STRAT_008` | `LIQUIDITY_MICROSTRUCTURE` | **-8.60%** | **$91.40** | $-1.50\%$ | $-7.10\%$ | $0.824$ | $10.22\%$ | 211 | 1/4 | No | `NEGATIVE_NET_EXPECTANCY_FRICTION` |
| **4** | `STRAT_085` | `ADAPTIVE_ENTRY_EXECUTION` | **-9.08%** | **$90.92** | $-3.93\%$ | $-5.15\%$ | $0.712$ | $9.08\%$ | 155 | 0/4 | No | `NEGATIVE_NET_EXPECTANCY_FRICTION` |
| **5** | `STRAT_074` | `MEAN_REVERSION_BREAKOUT` | **-11.02%** | **$88.98** | $+9.76\%$ | $-20.78\%$ | $0.903$ | $12.13\%$ | 609 | 2/4 | No | `NEGATIVE_NET_EXPECTANCY_FRICTION` |
| **6** | `STRAT_061` | `VOLATILITY_DYNAMICS` | **-16.73%** | **$83.27** | $+13.88\%$ | $-30.61\%$ | $0.906$ | $18.42\%$ | 915 | 2/4 | No | `NEGATIVE_NET_EXPECTANCY_FRICTION` |
| **7** | `STRAT_134` | `MEAN_REVERSION_BREAKOUT` | **-18.77%** | **$81.23** | $+36.16\%$ | $-54.93\%$ | $0.937$ | $30.82\%$ | 1,626 | 2/4 | No | `EXCESSIVE_DRAWDOWN_BREACH` |
| **8** | `STRAT_002` | `LIQUIDITY_MICROSTRUCTURE` | **-19.12%** | **$80.88** | $-6.32\%$ | $-12.80\%$ | $0.739$ | $19.98\%$ | 341 | 1/4 | No | `NEGATIVE_NET_EXPECTANCY_FRICTION` |
| **9** | `STRAT_013` | `MARKET_REGIME_TRANSITIONS` | **-19.14%** | **$80.86** | $+1.14\%$ | $-20.28\%$ | $0.793$ | $20.29\%$ | 417 | 1/4 | No | `NEGATIVE_NET_EXPECTANCY_FRICTION` |
| **10** | `STRAT_007` | `LIQUIDITY_MICROSTRUCTURE` | **-20.91%** | **$79.09** | $+9.86\%$ | $-30.77\%$ | $0.884$ | $23.11\%$ | 919 | 1/4 | No | `NEGATIVE_NET_EXPECTANCY_FRICTION` |

---

## 5. Cost Decomposition Analysis

The table below reconciles total aggregate friction paid across all 300 strategy evaluations by scenario:

| Cost Component | Scenario 1: `BYBIT_VIP0_DEFAULT` | Scenario 2: `ASTER_STRESS_TAKER` | Scenario 3: `MAKER_PASSIVE_TRUE` |
| :--- | :---: | :---: | :---: |
| **Total Exchange Tariffs ($C_{\text{fee}}$)** | $\$14,975.32$ | $\$25,033.21$ | $\$23,298.80$ |
| **Total Spread Crossing ($C_{\text{spread}}$)** | $\$2,562.27$ | $\$1,209.91$ | $\$0.00$ |
| **Total Arrival Slippage ($C_{\text{slip}}$)** | $\$2,562.27$ | $\$1,209.91$ | $\$0.00$ |
| **Total Adverse Selection Drag ($C_{\text{adverse}}$)** | $\$0.00$ | $\$0.00$ | $\$8.06$ |
| **Total Funding Settlement ($C_{\text{fund}}$)** | $\$121.47$ | $\$53.05$ | $\$102.08$ |
| **Total Gross Friction Paid** | **$20,221.33** | **$27,506.08** | **$23,408.94** |
| **Mean Maker Fill Percentage** | **15.0%** | **15.0%** | **15.0%** |
| **Mean Taker Fill Percentage** | **85.0%** | **85.0%** | **85.0%** |

### Key Friction Observations:
1. **The 15% Maker / 85% Taker Split:**
   Even though all 295 misconfigured strategies entered via aggressive `MARKET` orders ($100\%$ taker entries), approximately $30\%$ of their exits reached Take Profit limits ($100\%$ maker exits). On a per-fill-leg basis, this resulted in an average across all executed legs of **$15.0\%$ MAKER / $85.0\%$ TAKER**.
2. **Zero Double-Counting Invariant Proved:**
   In Scenario 3 (`MAKER_PASSIVE_TRUE`), total spread crossing and arrival slippage were strictly **$\$0.00$**, and adverse selection drag was applied exclusively to passive resting limit legs ($\$8.06$ total across the two genuine limit configurations `STRAT_095` and `STRAT_096`).
3. **Funding Is Secondary to Turnover Friction:**
   Total funding payments accounted for less than $1\%$ of total friction ($\$53\text{ to }\$121$ across 300 strategies), proving that funding settlement is a negligible factor compared to execution turnover costs.

---

## 6. Non-Conflated Six-Tier Microstructure Counter Hierarchy

Across all 900 re-evaluation runs, the strict microstructure hierarchy invariant was preserved with **zero runtime violations**:

$$\mathbf{N_{\text{signal}} \ge N_{\text{unique\_orders}} \ge N_{\text{touched\_orders}} \ge N_{\text{filled\_orders}} \ge N_{\text{portfolio\_exec}}}$$
$$\mathbf{N_{\text{fill\_events}} \ge N_{\text{filled\_orders}}}$$

### Aggregate Counter Totals (Scenario 1: `BYBIT_VIP0_DEFAULT`):
- **Level 1 (Raw Candidate Signals, $N_{\text{signal}}$):** $1,059,284$ total raw candle evaluations.
- **Level 2 (Unique Dispatched Orders, $N_{\text{unique\_orders}}$):** $317,458$ unique trade orders ($30.0\%$ serialization efficiency after cooldowns and concurrent position locking).
- **Level 3 (Touched Orders, $N_{\text{touched\_orders}}$):** $317,458$ (for market orders, touch occurs immediately at arrival quote).
- **Level 4 (Filled Orders, $N_{\text{filled\_orders}}$):** $317,458$ orders filled at exchange matching engines.
- **Level 5 (Execution Fill Events, $N_{\text{fill\_events}}$):** $634,916$ discrete fill executions ($2.00$ fill events per completed trade, representing entry and exit transactions).
- **Level 6 (Portfolio Executions, $N_{\text{portfolio\_exec}}$):** $301,894$ orders accepted and funded by RiskAgent ($95.1\%$ portfolio capital acceptance; $4.9\%$ rejected due to $\$5.00$ min notional or exposure caps).

---

## 7. Analysis of the 28 Historically "Qualified" Strategies

All 28 configurations that were classified as "Qualified" in historical Batch 001–003 reports were systematically re-evaluated under `BYBIT_VIP0_DEFAULT`. Every single one suffered severe performance degradation and failed re-qualification:

| Strategy ID | Family | Hist Net Ret | Recalc Net Ret | Delta Net Ret | Hist MDD | Recalc MDD | Recalc PF | Failure Classification |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `STRAT_242` | `MEAN_REVERSION_BREAKOUT` | $+44.40\%$ | **-46.00%** | $-90.40\%$ | $14.28\%$ | **48.39%** | $0.871$ | `EXCESSIVE_DRAWDOWN_BREACH` |
| `STRAT_263` | `MEAN_REVERSION_BREAKOUT` | $+43.02\%$ | **-46.67%** | $-89.69\%$ | $15.12\%$ | **48.02%** | $0.865$ | `EXCESSIVE_DRAWDOWN_BREACH` |
| `STRAT_262` | `MEAN_REVERSION_BREAKOUT` | $+40.65\%$ | **-44.13%** | $-84.78\%$ | $14.85\%$ | **46.63%** | $0.871$ | `EXCESSIVE_DRAWDOWN_BREACH` |
| `STRAT_278` | `MEAN_REVERSION_BREAKOUT` | $+40.37\%$ | **-49.98%** | $-90.35\%$ | $15.80\%$ | **52.22%** | $0.862$ | `EXCESSIVE_DRAWDOWN_BREACH` |
| `STRAT_266` | `MEAN_REVERSION_BREAKOUT` | $+39.33\%$ | **-49.43%** | $-88.76\%$ | $16.02\%$ | **51.81%** | $0.857$ | `EXCESSIVE_DRAWDOWN_BREACH` |
| `STRAT_254` | `MEAN_REVERSION_BREAKOUT` | $+38.38\%$ | **-46.83%** | $-85.21\%$ | $14.90\%$ | **49.28%** | $0.872$ | `EXCESSIVE_DRAWDOWN_BREACH` |
| `STRAT_134` | `MEAN_REVERSION_BREAKOUT` | $+36.16\%$ | **-3.20%** | $-39.36\%$ | $12.45\%$ | **25.19%** | $0.991$ | `NEGATIVE_NET_EXPECTANCY_FRICTION` |
| `STRAT_245` | `MEAN_REVERSION_BREAKOUT` | $+35.98\%$ | **-45.89%** | $-81.87\%$ | $15.30\%$ | **48.34%** | $0.873$ | `EXCESSIVE_DRAWDOWN_BREACH` |
| `STRAT_269` | `MEAN_REVERSION_BREAKOUT` | $+35.36\%$ | **-43.00%** | $-78.36\%$ | $14.10\%$ | **45.67%** | $0.885$ | `EXCESSIVE_DRAWDOWN_BREACH` |
| `STRAT_273` | `MEAN_REVERSION_BREAKOUT` | $+33.52\%$ | **-37.03%** | $-70.55\%$ | $13.80\%$ | **39.56%** | $0.891$ | `EXCESSIVE_DRAWDOWN_BREACH` |
| `STRAT_222` | `CROSS_ASSET_RELATIONSHIPS` | $+33.26\%$ | **-38.29%** | $-71.55\%$ | $16.20\%$ | **41.04%** | $0.885$ | `EXCESSIVE_DRAWDOWN_BREACH` |
| `STRAT_257` | `MEAN_REVERSION_BREAKOUT` | $+32.62\%$ | **-47.84%** | $-80.46\%$ | $15.40\%$ | **49.51%** | $0.872$ | `EXCESSIVE_DRAWDOWN_BREACH` |
| `STRAT_274` | `MEAN_REVERSION_BREAKOUT` | $+32.46\%$ | **-45.47%** | $-77.93\%$ | $15.10\%$ | **48.52%** | $0.870$ | `EXCESSIVE_DRAWDOWN_BREACH` |
| `STRAT_261` | `MEAN_REVERSION_BREAKOUT` | $+32.01\%$ | **-39.38%** | $-71.39\%$ | $14.70\%$ | **41.90%** | $0.878$ | `EXCESSIVE_DRAWDOWN_BREACH` |
| `STRAT_267` | `MEAN_REVERSION_BREAKOUT` | $+31.80\%$ | **-37.82%** | $-69.62\%$ | $13.90\%$ | **38.78%** | $0.882$ | `EXCESSIVE_DRAWDOWN_BREACH` |
| `STRAT_249` | `MEAN_REVERSION_BREAKOUT` | $+31.68\%$ | **-36.27%** | $-67.95\%$ | $14.50\%$ | **39.34%** | $0.894$ | `EXCESSIVE_DRAWDOWN_BREACH` |
| `STRAT_253` | `MEAN_REVERSION_BREAKOUT` | $+31.21\%$ | **-42.98%** | $-74.19\%$ | $15.20\%$ | **45.61%** | $0.881$ | `EXCESSIVE_DRAWDOWN_BREACH` |
| `STRAT_270` | `MEAN_REVERSION_BREAKOUT` | $+30.33\%$ | **-37.45%** | $-67.78\%$ | $14.60\%$ | **40.48%** | $0.886$ | `EXCESSIVE_DRAWDOWN_BREACH` |
| `STRAT_146` | `MEAN_REVERSION_BREAKOUT` | $+30.09\%$ | **-4.41%** | $-34.50\%$ | $13.10\%$ | **30.89%** | $0.986$ | `EXCESSIVE_DRAWDOWN_BREACH` |
| `STRAT_246` | `MEAN_REVERSION_BREAKOUT` | $+29.09\%$ | **-40.80%** | $-69.89\%$ | $14.80\%$ | **43.63%** | $0.873$ | `EXCESSIVE_DRAWDOWN_BREACH` |
| `STRAT_265` | `MEAN_REVERSION_BREAKOUT` | $+27.88\%$ | **-45.24%** | $-73.12\%$ | $15.90\%$ | **47.63%** | $0.866$ | `EXCESSIVE_DRAWDOWN_BREACH` |
| `STRAT_140` | `MEAN_REVERSION_BREAKOUT` | $+25.29\%$ | **-9.60%** | $-34.89\%$ | $13.80\%$ | **35.27%** | $0.970$ | `EXCESSIVE_DRAWDOWN_BREACH` |
| `STRAT_143` | `MEAN_REVERSION_BREAKOUT` | $+21.54\%$ | **-11.25%** | $-32.79\%$ | $14.20\%$ | **33.78%** | $0.963$ | `EXCESSIVE_DRAWDOWN_BREACH` |
| `STRAT_137` | `MEAN_REVERSION_BREAKOUT` | $+19.24\%$ | **-14.01%** | $-33.25\%$ | $14.60\%$ | **33.66%** | $0.955$ | `EXCESSIVE_DRAWDOWN_BREACH` |
| `STRAT_285` | `MEAN_REVERSION_BREAKOUT` | $+16.85\%$ | **-40.05%** | $-56.90\%$ | $15.40\%$ | **42.43%** | $0.876$ | `EXCESSIVE_DRAWDOWN_BREACH` |
| `STRAT_061` | `VOLATILITY_DYNAMICS` | $+13.88\%$ | **-3.79%** | $-17.67\%$ | $9.80\%$ | **14.28%** | $0.979$ | `NEGATIVE_NET_EXPECTANCY_FRICTION` |
| `STRAT_007` | `LIQUIDITY_MICROSTRUCTURE` | $+9.86\%$ | **-7.88%** | $-17.74\%$ | $8.90\%$ | **16.84%** | $0.957$ | `NEGATIVE_NET_EXPECTANCY_FRICTION` |
| `STRAT_074` | `MEAN_REVERSION_BREAKOUT` | $+9.76\%$ | **-1.50%** | $-11.26\%$ | $8.50\%$ | **9.46%** | $0.987$ | `NEGATIVE_NET_EXPECTANCY_FRICTION` |

---

## 8. Forensic Audit of the 5 Non-Misconfigured Strategies

Five configurations in Batch 001 did not have the `MARKET + maker_passive` mismatch and were audited as control benchmarks:

| Strategy ID | Order Type | Offset ($\sigma$) | Historical Tier | Hist Net Ret | BYBIT_VIP0 Net Ret | ASTER_STRESS Net Ret | MAKER_PASSIVE Net Ret | Maker Fill % | Audit Analysis |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `STRAT_095` | `LIMIT` | 0.08 | `maker_passive` | $-55.07\%$ | **-76.09%** | **-85.76%** | **-83.60%** | $63.1\%$ | Genuine passive resting limit. Degraded under remediated engine due to gap-down fix ($P_{\text{fill}} = P_{\text{limit}}$), 50% boundary touch queue model, and adverse selection drag ($1.5\text{ bps}$). |
| `STRAT_096` | `LIMIT` | 0.18 | `maker_passive` | $-45.50\%$ | **-70.25%** | **-85.77%** | **-79.18%** | $63.3\%$ | Resting limit at wider offset. Suffered from adverse selection and lower touch fill rate ($50\%$), losing $-70\%\text{ to }-85\%$. |
| `STRAT_097` | `MARKET` | 0.00 | `hybrid_tier` | $-46.24\%$ | **-39.16%** | **-85.75%** | **-57.39%** | $15.5\%$ | Historical hybrid tier ($15\text{ bps}$) closely matches Bybit VIP0 ($15\text{ bps}$); recalculated return ($-39.16\%$) is consistent with baseline ($-46.24\%$). |
| `STRAT_098` | `MARKET` | 0.00 | `hybrid_tier` | $-29.39\%$ | **-23.27%** | **-77.69%** | **-39.52%** | $15.6\%$ | Consistent behavior between historical hybrid tier ($-29.39\%$) and Bybit VIP0 ($-23.27\%$). |
| `STRAT_099` | `MARKET` | 0.00 | `baseline_taker` | $-71.70\%$ | **-11.14%** | **-65.27%** | **-25.83%** | $15.4\%$ | Historically evaluated at $44\text{ bps}$ friction ($-71.70\%$). Recalculated under Aster Stress ($44\text{ bps}$) yielded $-65.27\%$ (near-identical match). Under Bybit VIP0 ($15\text{ bps}$), loss reduced to $-11.14\%$. |

---

## 9. Failure & Disqualification Breakdown

Across all three scenarios, failure classifications were recorded systematically in [`data_backtest/recalculated/batch_reevaluation_exclusions.json`](file:///d:/quantum-multi-agent/data_backtest/recalculated/batch_reevaluation_exclusions.json):

```
                               DISQUALIFICATION BREAKDOWN BY SCENARIO
 300 ┌─────────────────────────────────────────────────────────────────────────────┐
     │                                                                             │
 250 │   262                                    297                                │
     │  ███████                                ███████                   283       │
 200 │  ███████                                ███████                  ███████    │
     │  ███████                                ███████                  ███████    │
 150 │  ███████                                ███████                  ███████    │
     │  ███████                                ███████                  ███████    │
 100 │  ███████                                ███████                  ███████    │
     │  ███████                                ███████                  ███████    │
  50 │  ███████     36                         ███████                  ███████ 16 │
   0 └──███████─────█████───────1────────1─────███████───────3──────────███████─███┘
       BYBIT_VIP0: EXCESSIVE_DD  NEG_EXP  SHORT FOLD   ASTER_STRESS: EXCESS  NEG   MAKER_PASSIVE: EXCESS NEG
```

- **In `BYBIT_VIP0_DEFAULT`:** $262$ strategies breached the $30\%$ maximum drawdown limit, $36$ had negative net expectancy, $1$ suffered bidirectional short drag, and $1$ (`STRAT_075`) had fold instability (only 2/4 positive folds).
- **In `ASTER_STRESS_TAKER`:** $297$ strategies breached the $30\%$ maximum drawdown limit (mean MDD $82.43\%$), and $3$ had negative net expectancy.
- **In `MAKER_PASSIVE_TRUE`:** $283$ strategies breached the $30\%$ maximum drawdown limit, $16$ had negative net expectancy, and $1$ had bidirectional short drag.

---

## 10. Institutional Conclusions & Research Roadmap Implications

### 10.1 Key Scientific Conclusions
1. **The 300 Configurations in Batches 001–003 Do Not Contain Valid High-Frequency Alpha:**
   The apparent outperformance of the Batch 001–003 strategies was an artifact of execution cost misconfiguration. At high trade turnover ($1,500\text{--}2,000$ trades/year), crossing the bid-ask spread on every entry imposes an insurmountable $15\text{--}44\text{ bps}$ hurdle that exceeds the predictive signal margin ($+10\text{--}15\text{ bps}$) of the current 5-minute models.
2. **High-Turnover Alpha Requires True Liquidity Provision:**
   If high turnover ($>1,000$ trades/year) is to achieve positive expectancy, trades must enter as **genuine passive maker limit orders** (earning or paying minimal maker fees and avoiding spread crossing). However, passive maker execution introduces adverse selection, which requires queue-aware execution and micro-price forecasting.
3. **Low-Turnover Gating Moderates Friction:**
   The highest surviving performer under retail friction (`STRAT_075`, $+2.93\%$ net return, $7.07\%$ max drawdown) succeeded because it traded only $601$ times (67% lower turnover than `STRAT_242`), demonstrating that selectivity and higher signal thresholding are essential when trading as a taker.

### 10.2 Recommended Session 2 Path
Now that the backtesting execution simulator is remediated, verified, and reconciled, research can proceed on a clean, scientifically defensible foundation:
1. **Do not deploy or promote any candidate from Batches 001–003.**
2. **Pivot Strategy Discovery toward:**
   - **True Passive Post-Only Specialists:** Designing strategies specifically engineered around limit orders with queue priority models and adverse selection defense.
   - **High-Selectivity Taker Specialists:** Increasing signal margin thresholds ($\text{prob\_margin} \ge 0.35$, volatility expansion gating) to generate fewer, higher-conviction trades ($200\text{--}500$ trades/year) with gross expectancies $>35\text{ bps}$ that comfortably overcome retail taker friction.
   - **Higher-Frequency 1m Microstructure Signals:** Ingesting 1-minute order flow imbalance and book pressure to capture micro-bursts with favorable spread capture.

---

## 11. Artifact Index & Reproducibility Verification

All re-evaluation outputs have been persisted in machine-readable and audit-compliant formats:

| Deliverable Artifact | Description | File Path |
| :--- | :--- | :--- |
| **Forensic Re-Evaluation Report** | This comprehensive forensic report. | [`audit/strategy_research/BATCH_001_003_REEVALUATION_REPORT.md`](file:///d:/quantum-multi-agent/audit/strategy_research/BATCH_001_003_REEVALUATION_REPORT.md) |
| **Bybit VIP0 Leaderboard** | Recalculated leaderboard under retail taker friction. | [`data_backtest/recalculated/leaderboard_bybit_vip0_default.json`](file:///d:/quantum-multi-agent/data_backtest/recalculated/leaderboard_bybit_vip0_default.json) |
| **Aster Stress Leaderboard** | Recalculated leaderboard under DEX stress friction. | [`data_backtest/recalculated/leaderboard_aster_stress_taker.json`](file:///d:/quantum-multi-agent/data_backtest/recalculated/leaderboard_aster_stress_taker.json) |
| **Maker Passive Leaderboard** | Recalculated leaderboard under passive maker schedule. | [`data_backtest/recalculated/leaderboard_maker_passive_true.json`](file:///d:/quantum-multi-agent/data_backtest/recalculated/leaderboard_maker_passive_true.json) |
| **Complete Results JSON** | Full metrics for all 300 configs $\times$ 3 scenarios (900 records). | [`data_backtest/recalculated/batch_reevaluation_results.json`](file:///d:/quantum-multi-agent/data_backtest/recalculated/batch_reevaluation_results.json) |
| **Summary Parquet** | High-performance columnar summary for analytics and graphing. | [`data_backtest/recalculated/batch_reevaluation_summary.parquet`](file:///d:/quantum-multi-agent/data_backtest/recalculated/batch_reevaluation_summary.parquet) |
| **Reproducibility Manifest** | Hash manifest, code commit, data boundaries, and venue parameters. | [`data_backtest/recalculated/batch_reevaluation_manifest.json`](file:///d:/quantum-multi-agent/data_backtest/recalculated/batch_reevaluation_manifest.json) |
| **Exclusion & Failure Report** | Disqualification records and failure classification breakdown. | [`data_backtest/recalculated/batch_reevaluation_exclusions.json`](file:///d:/quantum-multi-agent/data_backtest/recalculated/batch_reevaluation_exclusions.json) |
| **Re-Evaluation Runner Script** | Fully reproducible execution script. | [`scripts/run_batch_forensic_reevaluation.py`](file:///d:/quantum-multi-agent/scripts/run_batch_forensic_reevaluation.py) |

---

**MILESTONE 3 COMPLETE.**  
*Zero prospective holdout data was accessed. No new strategies or models were generated. Standing by for formal Project Owner review.*
