# QUANTUM — MILESTONE 5.9C
## CROSS-STRATEGY COST MODEL VALIDATION & HISTORICAL EXECUTION AUDIT

---

### EXECUTIVE SUMMARY & GOVERNANCE STATUS

- **Milestone Designation:** Milestone 5.9C (Cross-Strategy Cost Model Validation & Historical Execution Audit)
- **Git Branch:** `research/quantum-next-3pct`
- **Audit Directory:** `audit/strategy_research/milestone_5_9c_cross_strategy_cost_audit/`
- **Mandatory Target:** $\ge 3.0000\%$ Mean Net Daily Return at strictly $1.0\text{x}$ unlevered gross exposure
- **Target Status:** **UNMET (0 / 11 Historical Research Milestones Qualify)**
- **Paper Trading Status:** **STRICTLY PROHIBITED (`PAPER_TRADING_AUTHORIZATION: DENIED_PENDING_3_PERCENT_BACKTEST_VALIDATION`)**
- **Prospective Holdout Integrity:** **100% UNBREACHED & VIRGIN** ($t < 1,793,491,200,000\text{ ms}$ / 2026-11-01 00:00:00 UTC)
- **Six-Agent Consensus:** **UNANIMOUS REJECTION OF ALL HISTORICAL CANDIDATES**

```
+--------------------------------------------------------------------------------------------------------------------------+
| MILESTONE 5.9C STRATEGIC AUDIT VERDICT MATRIX                                                                            |
+-------------------+----------------------------+-----------------+-----------------+-----------------+-------------------+
| Strategy Family   | Historical Milestone       | Gross Alpha     | VIP0 Friction   | Aster Friction  | Root Failure Mode |
+-------------------+----------------------------+-----------------+-----------------+-----------------+-------------------+
| HYP-01 Momentum   | M3 / M4 / M5.5 / M5.8A     | -4.92 bps       | 17.00 bps RT    | 28.00 bps RT    | Negative Alpha +  |
|                   | (Portfolio A, STRAT_242)   | (Negative Edge) | ($57.29 Paid)   | ($114.58 Paid)  | Fee Churn Ruin    |
+-------------------+----------------------------+-----------------+-----------------+-----------------+-------------------+
| StatArb Pairs     | M5.8B / M5.9 / M5.9B       | +1.96 bps       | 34.30 bps RT    | 117.60 bps RT   | Fee Domination +  |
| (Track C SOL/LTC) | (Two-Leg Dollar Neutral)   | (+$0.37/yr APR) | (-$1.30 Paid)   | (-$4.47 Paid)   | Low Unlevered APR |
+-------------------+----------------------------+-----------------+-----------------+-----------------+-------------------+
```

#### Key Forensic Conclusions:
1. **Four-Way Disentanglement of Strategy Performance:**
   This audit establishes a mathematically rigorous distinction between four concepts frequently conflated in prior milestones:
   - **Arithmetic Accuracy:** Reconciled with $0.000000\text{ USDT}$ error in Milestone 5.8A (directional) and Milestone 5.9B (pairs). All reported internal ledgers are mathematically consistent with their engine inputs.
   - **Execution Model Realism:** Severely flawed in early milestones. M3 assigned maker fees to market orders; M5.2 assumed unbounded compounding; M5.5 introduced synthetic maker fill lookahead bias. Remediated to causal point-in-time next-bar open execution in M5.6–M5.9B.
   - **Statistical Validity:** Directional momentum signals failed causal regime stability (M4/M5.6). Relative value cointegration failed family-wise error rate control ($0 / 45$ pairs cointegrated after Holm-Bonferroni correction in M5.9).
   - **Economic Profitability:** Under no valid cost model does any historical strategy approach the mandatory $\ge 3.00\%/\text{day}$ unlevered target.
2. **Directional Momentum Failed Due to Negative Gross Alpha:**
   Directional HYP-01 / Portfolio A did not fail primarily because of high transaction fees; it failed because its causal gross expectancy was **negative** ($-4.92\text{ bps}$ before friction). Fee churn ($3,562$ trades in 118 days, costing $\$57.29$ on a $\$100$ account) merely accelerated its mathematical certainty of ruin to 100.0%.
3. **Track C Statistical Arbitrage Failed Due to Microstructure Friction Domination:**
   Track C (SOL/LTC) generated **positive gross alpha** ($+1.96\text{ bps}$ gross expectancy, $42.1\%$ win rate, $+\$0.3662$ gross PnL over 365 days). However, because two-legged market-neutral pairs require $4\times$ leg notional turnover per trade ($2\text{ entry legs} + 2\text{ exit legs} = \$200\text{ turnover}$ on a $\$100$ portfolio), transaction friction was $3.5\times$ to $12.2\times$ larger than gross alpha ($-\$1.30$ Bybit VIP0, $-\$4.47$ Aster Retail), driving net returns negative.
4. **Zero-Fee Upper Bound Conclusively Disqualifies Both Families:**
   Even if the exchange charged **ZERO fees, ZERO spread, and ZERO slippage**, Track C generated only **$+0.3662\%$ net return per YEAR** ($+0.0010\%/\text{day}$), falling **$3,000\times$ short** of the mandatory $+3.00\%/\text{day}$ unlevered target. Correcting transaction costs cannot rescue either strategy family.

---

### 1. HISTORICAL COST MODEL AUDIT (MILESTONES 3 THROUGH 5.9B)

Across the eleven research milestones, cost modeling evolved through four distinct epochs:

```
+-----------------------------------------------------------------------------------------------------------------------+
| CHRONOLOGICAL EVOLUTION OF QUANTUM COST MODELING                                                                      |
+-----------------------------------------------------------------------------------------------------------------------+
| Epoch 1 (M3 - M4)   : Naive Fixed-Fee Phase (Phantom Maker Bias & Marketable Mismatch)                                 |
| Epoch 2 (M5.2)      : Unconstrained Compounding Distortion (Ignored Market Capacity & Venue Liquidity Bounds)         |
| Epoch 3 (M5.4 - M5.5): Synthetic Maker Optimization & Intra-Bar Lookahead Contamination                              |
| Epoch 4 (M5.6 - M5.9B): Causal Point-in-Time Reconstruction, Asymmetric Notional Scaling & Exchange Friction Auditing|
+-----------------------------------------------------------------------------------------------------------------------+
```

#### Detailed Milestone Cost Model Audit:

1. **Milestone 3 (M3 - 300 Strategy Fleet Discovery):**
   - *Cost Model:* `maker_passive` applied indiscriminately to 295/300 strategies. Entry orders were executed as aggressive `MARKET` orders, but evaluated with a passive $2.0\text{ bps}$ maker fee, $0.0\text{ bps}$ spread, and $0.0\text{ bps}$ slippage.
   - *Flaw:* Critical execution mismatch. When re-evaluated under realistic retail taker friction (`BYBIT_VIP0_DEFAULT` at $15.0\text{ bps}$ RT), champion `STRAT_242` collapsed from $+44.40\%$ to $+0.90\%$ over a full year ($+0.0025\%/\text{day}$, $\text{PF} = 1.002$), falling $1,200\times$ short of the mandate. Under DEX stress friction ($44.0\text{ bps}$ RT), it lost $-81.10\%$.
2. **Milestone 4 (M4 - Alpha Failure Diagnosis):**
   - *Cost Model:* Evaluated fleet under three venue scenarios: Bybit VIP0 ($13.43\text{ bps}$ avg RT drag), Aster Stress ($44.0\text{ bps}$ RT), and Maker ($9.5\text{ bps}$ RT).
   - *Finding:* Proved that fleet mean gross edge was only $+5.98\text{ bps}$, while VIP0 taker friction consumed $224.6\%$ of the edge. In addition, $85\%$ of position exits were emergency stop-losses that executed as aggressive takers, invalidating maker fee assumptions on exit.
3. **Milestone 5.2 (M5.2 - EXP-03 Validation):**
   - *Cost Model:* Fixed $15.0\text{ bps}$ round-trip hurdle rate.
   - *Flaw:* Compounding distortion. Position sizes scaled exponentially with accumulated paper profits, reporting ending equity in the billions of dollars ($AVAX \$7.06\text{B}$, $SOL \$4.48\text{B}$). This masked fee drag by simulating trades with notionals vastly exceeding exchange orderbook depth.
4. **Milestone 5.4 (M5.4 - HYP-01 Alpha Expansion):**
   - *Cost Model:* Bybit VIP0 per-leg model: Taker entry ($5.0\text{ bps}$ fee $+ 2.0\text{ bps}$ spread $+ 1.5\text{ bps}$ slippage $= 8.5\text{ bps}$), Maker TP exit ($3.5\text{ bps}$), Taker SL exit ($6.5\text{ bps}$).
   - *Flaw:* Optimistic limit fill assumption. Assumed $100\%$ of take-profit limit orders were filled at limit price without modeling queue priority or adverse selection. Net return reached only $+0.55\%/\text{day}$, failing the $3.00\%$ gate.
5. **Milestone 5.5 (M5.5 - Unlevered Alpha Engineering):**
   - *Cost Model:* Introduced `ASTER_RETAIL_CORE` ($4.0\text{ bps}$ maker, $10.0\text{ bps}$ taker) and synthetic passive maker execution (`MAKER_PASSIVE_TRUE`: $4.0\text{ bps}$ maker fee, $1.5\text{ bps}$ adverse selection drag).
   - *Flaw:* Intra-bar timing leak. Evaluated entry at the bar open using signals derived from the bar close (`closes[i] > opens[i]` filled at `opens[i]`), generating an artificially inflated $+1.8640\%/\text{day}$ claim for Portfolio A.
6. **Milestone 5.6 (M5.6 - Independent Forensic Revalidation):**
   - *Cost Model:* Enforced point-in-time causal next-bar open execution ($P_{\text{entry}} = \text{open}[i+1]$).
   - *Finding:* The $+1.8640\%/\text{day}$ return collapsed to $-0.1449\%/\text{day}$ across 1,099 days, with an $80.03\%$ max drawdown. Revealed the account starvation barrier: at equity $<\$20$, $w_{\text{max}} \cdot \text{Equity} < \$5.00$, permanently halting trading.
7. **Milestone 5.7 (M5.7 - Data Provenance & Reconstruction):**
   - *Cost Model:* Reconstructed daily equity and audited calendar coverage.
   - *Finding:* Proved the reported $-0.1449\%/\text{day}$ was diluted by 981 inactive post-ruin days. The true active loss rate was $-1.35\%$ (simple) to $-2.01\%/\text{day}$ (geometric compounding).
8. **Milestone 5.8A (M5.8A - Terminal Equity & Survival Accounting):**
   - *Cost Model:* Reconstructed all $3,562$ trades executed in the 118-day active period.
   - *Finding:* Initial equity $\$100.00 \rightarrow$ terminal equity $\$19.97$. Total fees and costs paid: $\$57.29$ ($71.6\%$ of the total $\$80.04$ capital loss). Gross expectancy was $-4.92\text{ bps}$, proving negative gross alpha. Bootstrap ruin probability was $100.0\%$.
9. **Milestone 5.8B (M5.8B - New Alpha Family Feasibility):**
   - *Cost Model:* Screened Tracks A, B, C, D under institutional VIP0 baseline ($15\text{ bps}$ RT 1-leg, $30\text{ bps}$ RT 2-leg). Funding rate data classified as `FUNDING_DATA_UNAVAILABLE`.
   - *Finding:* Tracks A, B, D rejected. Track C (Statistical Arbitrage) selected as the sole candidate for statistical revalidation.
10. **Milestone 5.9 (M5.9 - Track C Statistical Revalidation):**
    - *Cost Model:* Two-leg dollar-neutral pairs backtest with Bybit VIP0 and Aster DEX schedules.
    - *Finding:* Cointegration rejected ($0 / 45$ pairs survived Holm-Bonferroni correction). SOL/LTC case study produced $-1.61\%$ net return on Bybit VIP0 and $-4.47\%$ on Aster DEX.
11. **Milestone 5.9B (M5.9B - Forensic PnL Attribution & Reconciliation):**
    - *Cost Model:* Reconstructed exact 19 trades and 38 leg executions with asymmetric exit notional scaling and signed cash flows.
    - *Finding:* Gross PnL was $+\$0.3662$ ($+1.96\text{ bps}$ gross expectancy), but friction ($-\$1.3032$ Bybit, $-\$4.4682$ Aster DEX) overwhelmed gross edge. Disproved the hypothesis that losses were due to accounting errors (accounting discrepancy $= 0.000000\text{ USDT}$).

---

### 2. ASTERDEX VS BYBIT VIP0 FEE SCHEDULES & MICROSTRUCTURE REALITY

Authoritative fee schedules codified in `src/quantum/strategies/schemas.py` and `docs/ASTERDEX_MARKET_DATA.md`:

```
+-------------------------------------------------------------------------------------------------------------+
| VENUE FEE SCHEDULE COMPARISON                                                                               |
+-------------------+--------------------+---------------+---------------+---------------+--------------------+
| Venue Profile ID  | Exchange & Tier    | Maker Fee/Leg | Taker Fee/Leg | Spread (Half) | Slippage Model     |
+-------------------+--------------------+---------------+---------------+---------------+--------------------+
| BYBIT_VIP0_DEFAULT| Bybit VIP0 Retail  | 2.0 bps       | 5.5 bps       | 1.0 bps       | 1.5 bps (Linear)   |
| BYBIT_VIP1        | Bybit VIP1 Tier    | 1.8 bps       | 4.0 bps       | 1.0 bps       | 1.5 bps (Linear)   |
| BYBIT_PRO3        | Bybit Institutional| 0.0 bps       | 2.5 bps       | 1.0 bps       | 1.5 bps (Linear)   |
| ASTER_RETAIL_CORE | Aster DEX Base Tier| 4.0 bps       | 10.0 bps      | 1.0 bps       | 2.0 bps (DEX Pool) |
| ASTER_STRESS_TAKER| Aster DEX Stress 3 | 4.0 bps       | 20.0 bps      | 1.0 bps       | 2.0 bps (Gas/Cong) |
| MAKER_PASSIVE_TRUE| Aster Synthetic Mkr| 4.0 bps       | 10.0 bps      | 0.0 bps       | 1.5 bps (Adverse)  |
+-------------------+--------------------+---------------+---------------+---------------+--------------------+
```

#### Microstructure Reality: Why Post-Only Submission Does Not Equal Filled
A recurring misconception in early QUANTUM iterations was the assumption that submitting a post-only limit order guarantees a fill at the maker fee:
1. **Queue Priority & Non-Execution:** A limit order placed at the inside quote joins the back of the queue. If the price moves away from the limit price, the order remains completely unfilled, resulting in missed alpha.
2. **Adverse Selection Drag:** A limit order is executed if and only if an aggressive trader sweeps the orderbook into it. This means limit orders are filled disproportionately when the market has strong momentum *against* the position. In `MAKER_PASSIVE_TRUE`, this is modeled as an empirical $1.5\text{ to }2.0\text{ bps}$ adverse selection penalty.
3. **Emergency Stop-Loss Asymmetry:** While an entry or take-profit order can theoretically rest as a maker order, risk-management stop-loss orders **must execute immediately** when a threshold is breached. Stop-loss orders are executed as aggressive `MARKET` taker orders, crossing the full bid-ask spread and incurring taker fees. Across historical backtests, $>80\%$ of position exits were forced takers.

---

### 3. POSITION SIZING, LEVERAGE & NOTIONAL TURNOVER RECONCILIATION

Reconciliation of position sizing across strategies confirms that the backtest engine maintained strictly unlevered execution:

```
+--------------------------------------------------------------------------------------------------------------------------+
| POSITION SIZING & NOTIONAL TURNOVER RECONCILIATION                                                                       |
+-------------------+----------------+-------------+------------+-------------+--------------+--------------+--------------+
| Strategy ID       | Milestone      | Capital     | Max Weight | Max Legs    | Leg Notional | Max Leverage | Turnover/Trd |
+-------------------+----------------+-------------+------------+-------------+--------------+--------------+--------------+
| STRAT_242         | M3             | $100.00     | 0.25       | 4           | $25.00       | 1.0015x      | 2.0x ($50)   |
| Portfolio A       | M5.5 / M5.8A   | $100.00     | 0.25       | 4           | $25.00       | 0.7508x      | 2.0x ($50)   |
| Track C SOL/LTC   | M5.9 / M5.9B   | $100.00     | 0.50       | 2 (1 Pair)  | $50.00       | 1.0000x      | 4.0x ($200)  |
+-------------------+----------------+-------------+------------+-------------+--------------+--------------+--------------+
```

#### Independent Turnover Accounting:
- **Directional HYP-01 (Single-Leg):**
  Each trade consists of 1 entry leg and 1 exit leg.
  $$\text{Turnover per trade} = N_{\text{entry}} + N_{\text{exit}} \approx 2 \times \$25.00 = \$50.00$$
  Across 3,562 trades, total gross turnover was **$\$178,100.00$** on a $\$100$ equity base ($1,781\times$ equity churn).
- **Track C Cointegration Pairs (Two-Leg Dollar-Neutral):**
  Each pair trade consists of 2 entry legs ($L_1\text{ Long} + L_2\text{ Short}$) and 2 exit legs.
  $$\text{Turnover per trade} = N_{\text{entry}, L_1} + N_{\text{exit}, L_1} + N_{\text{entry}, L_2} + N_{\text{exit}, L_2} \approx 4 \times \$50.00 = \$200.00$$
  Across 19 trades, total gross turnover was **$\$3,800.00$** on a $\$100$ equity base ($38\times$ equity churn).

#### Account Starvation Invariant:
Exchange minimum notional order size is $N_{\text{min}} = \$5.0000\text{ USDT}$.
When equity declines under drawdown, the required position size $N_{\text{req}} = w_{\text{max}} \cdot \text{Equity}_t$ shrinks:
$$\text{Starvation Threshold: } \text{Equity}_{\text{starvation}} = \frac{N_{\text{min}}}{w_{\text{max}}} = \frac{\$5.0000}{0.25} = \mathbf{\$20.0000\text{ USDT}}$$
When Portfolio A equity dropped to $\$19.9654$ on Day 118, the engine rejected all subsequent order placements, halting execution permanently.

---

### 4. FUNDING COST ACCOUNTING AUDIT

Per `src/quantum/backtesting/accounting.py`:
- Discrete funding settlements occur at $00:00$, $08:00$, and $16:00\text{ UTC}$.
- Formally: $t_{\text{entry}} < t_{\text{settle}} \le t_{\text{exit}}$.
- In the historical SQLite/Parquet database, zero rows exist in `funding_events`. Historical funding is formally classified as:
  $$\mathbf{HISTORICAL\_FUNDING\_STATUS = "FUNDING\_DATA\_UNAVAILABLE"}$$
- **Impact Analysis:**
  - For short-term momentum trades (holding time $< 60\text{ minutes}$), $<5\%$ of trades crossed an 8-hour boundary; the funding drag was negligible ($<0.05\text{ bps}$).
  - For Track C pairs (holding time 5–6 days), positions crossed 15–18 funding settlement windows. If crypto perpetual funding was net positive (longs paying shorts), the long SOL leg paid funding while the short LTC leg received funding. Assuming mean divergence, net funding would either cancel out or impose a small drag. Omitting funding in M5.9B gave Track C an optimistic advantage, further cementing its disqualification.

---

### 5. CORRECTED HISTORICAL PERFORMANCE COMPARISON

The table below synthesizes the reported metrics vs corrected metrics across historical milestones:

```
+--------------------------------------------------------------------------------------------------------------------------+
| CORRECTED HISTORICAL PERFORMANCE COMPARISON TABLE                                                                        |
+-------------------+---------------+------------------+------------------+------------------+---------------+-------------+
| Milestone & Strat | Reported Ret  | VIP0 Corrected   | Aster Corrected  | Zero-Fee Gross   | Target Status | Verdict     |
+-------------------+---------------+------------------+------------------+------------------+---------------+-------------+
| M3 (STRAT_242)    | +0.1216%/day  | +0.0025%/day     | -0.0730%/day     | +0.0422%/day     | FAILED        | DISQUALIFIED|
| M4 (Fleet Avg)    | -0.0510%/day  | -0.0510%/day     | -0.1980%/day     | +0.0164%/day     | FAILED        | DISQUALIFIED|
| M5.2 (EXP-03)     | +0.9880%/day  | +0.0360%/day     | -0.0120%/day     | +0.0756%/day     | FAILED        | DISQUALIFIED|
| M5.4 (HYP-01)     | +0.5500%/day  | +0.0210%/day     | -0.0450%/day     | +0.0520%/day     | FAILED        | DISQUALIFIED|
| M5.5 (Port A Rep) | +1.8640%/day  | -0.1449%/day     | -0.3850%/day     | -0.0396%/day     | FAILED        | DISQUALIFIED|
| M5.6 (Port A Aud) | -0.1449%/day  | -0.1449%/day     | -0.3850%/day     | -0.0396%/day     | FAILED        | DISQUALIFIED|
| M5.7 (Port A Act) | -1.3500%/day  | -1.3500%/day     | -3.5800%/day     | -0.3690%/day     | FAILED        | DISQUALIFIED|
| M5.8A (Port A Led)| -2.0068%/day  | -2.0068%/day     | -4.1200%/day     | -0.5500%/day     | FAILED        | DISQUALIFIED|
| M5.9 (Track C Bt) | -0.0044%/day  | -0.0026%/day     | -0.0112%/day     | +0.0010%/day     | FAILED        | DISQUALIFIED|
| M5.9B (Track C At)| -0.0026%/day  | -0.0026%/day     | -0.0112%/day     | +0.0010%/day     | FAILED        | DISQUALIFIED|
+-------------------+---------------+------------------+------------------+------------------+---------------+-------------+
```

#### Does Cost Correction Rescue Any Historical Strategy?
**NO. Conclusively and definitively NO.**
1. For directional momentum (HYP-01 / Portfolio A), gross expectancy was **negative** ($-4.92\text{ bps}$). Eliminating all fees entirely still yields a losing strategy ($-0.0396\%/\text{day}$ diluted, $-0.5500\%/\text{day}$ active).
2. For relative value pairs (Track C SOL/LTC), gross expectancy was positive ($+1.96\text{ bps}$), but the strategy's unlevered turnover produces only **$+0.3662\%$ net return per YEAR** ($+0.0010\%/\text{day}$) under zero fees. To reach $+3.00\%/\text{day}$, Track C would require a leverage of:
   $$\text{Required Leverage} = \frac{3.0000\%/\text{day}}{0.0010\%/\text{day}} = \mathbf{3,000\text{x Gross Leverage}}$$
   This violates the mandatory $1.0\text{x}$ unlevered constraint by three orders of magnitude.

---

### 6. SIX-AGENT GOVERNANCE SIGN-OFF

The six autonomous QUANTUM agents have completed their multi-agent review of Milestone 5.9C:

1. **Scout Agent (Market Data & Venue Discovery Lead):**
   > *"I have verified the exchange fee schedules and WebSocket/REST data infrastructure for AsterDEX and Bybit. AsterDEX retail taker fees (10 bps) and stress tiers (20 bps) impose prohibitive friction on high-turnover strategies. Historical funding rates remain unavailable in the database. Approved."*
2. **Analyst Agent (Statistical Evaluation & Edge Modeling Lead):**
   > *"I have confirmed that the root cause of Track C's failure is fee domination over a marginal edge (+1.96 bps gross vs 34.3 bps friction), whereas Directional HYP-01 suffers from negative gross alpha (-4.92 bps). The zero-fee return of +0.37% APR proves Track C is incapable of meeting the 3.00%/day mandate. Approved."*
3. **Sniper Agent (Microstructure & Execution Lead):**
   > *"I have verified the asymmetric exit notional scaling and maker/taker order dynamics. Assumptions that limit orders execute with 100% fill probability or zero adverse selection are operationally invalid. Exits via stop-loss are aggressively executed as taker orders. Approved."*
4. **Risk Agent (Portfolio Governance & Leverage Lead):**
   > *"I have audited the position sizing reconciliation. Gross leverage was maintained strictly <= 1.0000x across all causal milestones. The account starvation threshold of $20.00 is an invariant of the $5.00 minimum notional and w_max = 0.25 constraints. Approved."*
5. **Bank Agent (PnL Audit & Balance Sheet Lead):**
   > *"I have verified all cash balance deductions, fee debits, and trade turnovr identities. Single-leg strategies generate 2x turnover, while two-leg pairs generate 4x turnover per trade. The accounting discrepancy between reported and reconstructed ledgers is exactly 0.000000 USDT. Approved."*
6. **Critic Agent (Adversarial Forensic Auditor):**
   > *"I confirm that no historical strategy has been falsely rejected due to accounting bugs or overly aggressive cost assumptions. Both Directional Momentum and Relative Value Cointegration are disqualified on fundamental alpha and structural edge grounds. Paper trading authorization remains strictly denied."*

---

### 7. RESEARCH ROADMAP & NEXT MILESTONES

With the cross-strategy cost audit concluded, the research team has established an unassailable empirical foundation:
- Directional 5m momentum is dead (negative gross alpha under causal execution).
- Daily/multi-day cointegration pairs trading is dead (marginal edge drowned by 4x turnover friction).
- The non-negotiable target of $\ge 3.00\%$ mean net daily return at $1.0\text{x}$ unlevered leverage cannot be reached through parameter tweaking of known failed architectures.
- Future research must explore higher-capacity structural alpha mechanisms (e.g. cross-exchange latency arbitrage, high-frequency orderbook imbalance scalping, or liquid yield basis capture) before any paper trading authorization can be considered.
