# QUANTUM — MILESTONE 5.10A
## CONTRACT RECONCILIATION & CONFIGURATION HARMONIZATION

---

### EXECUTIVE SUMMARY

- **Milestone Designation:** Milestone 5.10A (Contract Enforcement & Configuration Reconciliation)
- **Git Branch:** `research/quantum-next-3pct`
- **Audit Directory:** `audit/strategy_research/milestone_5_10a_contract_reconciliation/`
- **Objective:** Reconcile and close all architectural, contract, and cost inconsistencies discovered in M5.10 prior to launching new alpha research.
- **Key Reconciliations Achieved:**
  1. **Authoritative Minimum Frequency:** Category A minimum frequency is unified at strictly **10.0 completed trade episodes/day** (matching the target range of 10–100 trades/day).
  2. **Harmonized Holding Horizon:** Expected holding horizon is **15 minutes to 4 hours**; maximum holding duration is harmonized at **240 minutes (4.0 hours)** default for Category A.
  3. **Strict Overnight Prohibition:** Overnight holding is prohibited by default (`allow_overnight_holding = False`). Any exception requires explicit category classification and mandatory justification.
  4. **Terminology Disentanglement:** Explicit mathematical hierarchy separating orders, fills, legs, and completed trade episodes.
  5. **AsterDEX-First Cost Configuration:** Primary venue target is codified as AsterDEX Base Retail (4 bps maker / 10 bps taker). Silent Bybit fallbacks are programmatically blocked.
  6. **Transparent Funding Accounting:** Historical funding is explicitly designated `FUNDING_DATA_UNAVAILABLE` with sensitivity bounds $[-5.0, +5.0]\text{ bps}/8\text{h}$; representing missing funding as verified zero funding is strictly forbidden.

---

### 1. RESOLUTION OF CONTRACT INCONSISTENCIES

#### 1.1 Category A Minimum Frequency Harmonization
In Milestone 5.10, the contract specification exhibited a minor drift between `minimum_trade_frequency_daily = 1.0` and validator checks at `5.0`. 
Under Milestone 5.10A, this inconsistency is resolved with a single authoritative standard:

$$\mathbf{Category\ A\ Minimum\ Trade\ Frequency = 10.0\ Completed\ Trade\ Episodes\ per\ Day}$$

$$\mathbf{Target\ Trade\ Frequency\ Range = [10.0,\ 100.0]\ Completed\ Trade\ Episodes\ per\ Day}$$

- Any strategy seeking Category A (High-Frequency Intraday) qualification must demonstrate an empirical frequency of $\ge 10.0$ completed trade episodes per day out-of-sample.
- Strategies generating between $1.0$ and $10.0$ trades/day are classified as **Category B (Intraday Low-Frequency)**.
- Strategies generating $< 1.0$ trades/day are classified as **Category C (Swing / Multi-Day)**.

#### 1.2 Holding Horizon & Maximum Duration Harmonization
The contract parameters for holding duration are aligned with mathematical consistency:
- **Expected Holding Horizon:** `"15m to 4h"` (15 minutes to 240 minutes).
- **Maximum Permissible Holding Duration:** **`240 minutes`** (4.0 hours) default for Category A.
- Any Category A trade that remains open beyond 240 minutes without `allow_overnight_holding = True` immediately triggers a `HoldingHorizonViolationError`.
- For example, an intraday trade held for 5 hours (300 minutes) fails validation and breaches contract governance.

#### 1.3 Overnight Holding Policy
- `allow_overnight_holding` is **`False`** by default.
- If an experimental design requires holding positions across the 00:00 UTC day boundary:
  1. The experiment must be classified as **Category C (Swing / Multi-Day)** or an explicitly approved Category B regime.
  2. `overnight_holding_justification` is mandatory and must document the economic rationale (e.g. multi-day carry or swing trend). Initializing a contract with `allow_overnight_holding=True` but null/empty justification raises `ValueError`.

---

### 2. TERMINOLOGY DISENTANGLEMENT: EPISODES VS FILLS VS LEGS

To prevent miscounting and ensure statistical rigor, the QUANTUM architecture establishes a formal hierarchy:

```
+-----------------------------------------------------------------------------------------------------------------------+
| QUANTUM EXECUTION TERMINOLOGY HIERARCHY                                                                               |
+-----------------------------------------------------------------------------------------------------------------------+
| 1. Completed Trade Episode (Round Trip):                                                                              |
|    The complete lifecycle of a market exposure, from initial entry fill(s) to final exit fill(s).                    |
|    --> Frequency is measured strictly in Completed Trade Episodes per Day!                                            |
|                                                                                                                       |
| 2. Position Legs:                                                                                                     |
|    - Single-Leg Directional Strategy: Exactly 1 leg (e.g. Long SOLUSDT).                                              |
|    - Two-Leg Market-Neutral Pair Strategy: Exactly 2 simultaneous legs (e.g. Long SOLUSDT + Short LTCUSDT).           |
|                                                                                                                       |
| 3. Order Execution Fills:                                                                                             |
|    - Single-Leg Trade Episode: Exactly 2 Fills (1 Entry Order Fill + 1 Exit Order Fill).                              |
|    - Two-Leg Pair Trade Episode: Exactly 4 Fills (2 Entry Order Fills + 2 Exit Order Fills).                         |
|                                                                                                                       |
| 4. Orders Submitted:                                                                                                  |
|    Includes limit orders submitted, post-only attempts, canceled orders, and filled orders. Fills <= Orders.          |
+-----------------------------------------------------------------------------------------------------------------------+
```

#### Numerical Comparison:
- In Milestone 5.8A (Portfolio A): $3,562\text{ Completed Trade Episodes} = 3,562\text{ Legs} = 7,124\text{ Fills}$.
- In Milestone 5.9B / 5.9D (Track C SOL/LTC): $19\text{ Completed Trade Episodes} = 38\text{ Legs} = 76\text{ Fills}$.
Reporting 76 fills as "76 trades" is an accounting violation. All frequency reporting must cite completed trade episodes.

---

### 3. EXCHANGE-SPECIFIC COST CONFIGURATION (ASTERDEX PRIMARY)

Implicit Bybit fee defaults have been replaced with the explicit `ExchangeCostConfiguration` model codified in [`src/quantum/domain/research_contract.py`](file:///d:/quantum-multi-agent/src/quantum/domain/research_contract.py):

```
+--------------------------------------------------------------------------------------------------------------------------+
| EXPLICIT VENUE COST CONFIGURATIONS (M5_10A_EXCHANGE_COST_CONFIG.csv)                                                     |
+-------------------+--------------------+---------------+---------------+---------------+----------------+----------------+
| Exchange & Tier   | Contract Type      | Maker Fee/Leg | Taker Fee/Leg | Half-Spread   | Slippage/Leg   | Role           |
+-------------------+--------------------+---------------+---------------+---------------+----------------+----------------+
| Aster DEX Retail  | USDT Linear Perp   | 4.0 bps       | 10.0 bps      | 1.0 bps       | 2.0 bps        | PRIMARY TARGET |
| Aster DEX Stress 3| USDT Linear Perp   | 4.0 bps       | 20.0 bps      | 1.0 bps       | 2.0 bps        | STRESS SCENARIO|
| Bybit VIP0 Retail | USDT Linear Perp   | 2.0 bps       | 5.5 bps       | 1.0 bps       | 1.5 bps        | CEX BENCHMARK  |
| Bybit VIP1 Tier   | USDT Linear Perp   | 1.8 bps       | 4.0 bps       | 1.0 bps       | 1.5 bps        | PROHIBITED RET.|
+-------------------+--------------------+---------------+---------------+---------------+----------------+----------------+
```

#### Governance Rules for Venue Configuration:
1. **AsterDEX as Primary Target:** All future alpha candidates must be evaluated against **`ASTER_DEX_RETAIL_CONFIG`** ($4.0\text{ bps}$ maker, $10.0\text{ bps}$ taker, $2.0\text{ bps}$ slippage).
2. **Prohibition of Silent CEX Defaults:** Backtesting pipelines must not silently fall back to Bybit VIP0 fees. If Bybit is used, it must be explicitly declared as a comparative benchmark (`BYBIT_VIP0_BENCHMARK_CONFIG`).
3. **Funding Transparency:** Missing historical funding data is formally designated:
   $$\mathbf{funding\_data\_availability = "DATA\_UNAVAILABLE"}$$
   $$\mathbf{funding\_uncertainty\_status = "PARAMETRIC\_BOUNDS\_SENSITIVITY\_REQUIRED"}$$
   Representing missing funding as "verified zero funding" raises `FundingDataUncertaintyError`. All backtests must report sensitivity bounds across $[-5.0, +5.0]\text{ bps}/8\text{h}$.

---

### 4. MULTI-AGENT ARCHITECTURE PRESERVATION

The six-agent architecture is preserved:
1. **Scout Agent:** Market scanning & opportunity discovery.
2. **Analyst Agent:** Regime classification & probabilistic edge modeling.
3. **Sniper Agent:** Causal execution & microstructure order fill management.
4. **Risk Agent:** Unlevered exposure cap ($\le 1.0x$) & portfolio slot governance.
5. **Banker Agent:** PnL accounting, cash ledger verification & fee auditing.
6. **Orchestrator Agent:** Pipeline lifecycle coordinator & contract enforcement lead.

`contracts.py` in `src/quantum/agents/` remains the data contracts schema module, not an agent.
All six agents interface with `ResearchExperimentContract` and fail closed upon any contract parameter breach.
