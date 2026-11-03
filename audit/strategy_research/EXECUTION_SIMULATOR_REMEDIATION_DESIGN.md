# QUANTUM — HIGH-TURNOVER ALPHA FEASIBILITY STUDY
## Session 1.5: Execution Simulator Remediation & Verification Design (Revised)

**Project:** QUANTUM Autonomous Quantitative Trading System  
**Document Identity:** `audit/strategy_research/EXECUTION_SIMULATOR_REMEDIATION_DESIGN.md`  
**Phase:** High-Turnover Alpha Feasibility Study (Session 1.5 Design Revision 2)  
**Branch:** `research/high-turnover-alpha-feasibility`  
**Git Baseline Commit:** `dcc8ceb54d80b1b9685d92236f48b0994610522a`  
**Status:** **REVISED REMEDIATION DESIGN — AWAITING PROJECT OWNER SIGN-OFF**  
**Authorization Level:** **DESIGN ONLY (NO CODE MODIFICATIONS PERMITTED)**  
**Sealed Prospective Holdout:** **STRICTLY SEALED** ($\ge \text{1793491200000 ms}$ / 2026-11-01 00:00:00 UTC)  
**Date:** 2026-11-03 15:20:00 UTC  

---

## 1. Executive Summary & Design Mandate

### 1.1 Background & Forensic Findings
The Session 1 Audit ([`HIGH_TURNOVER_READINESS_AUDIT.md`](file:///d:/quantum-multi-agent/audit/strategy_research/HIGH_TURNOVER_READINESS_AUDIT.md)) and its Reconciliation Addendum ([`HIGH_TURNOVER_AUDIT_RECONCILIATION.md`](file:///d:/quantum-multi-agent/audit/strategy_research/HIGH_TURNOVER_AUDIT_RECONCILIATION.md)) established that:
1. In [`src/quantum/strategies/evaluator.py`](file:///d:/quantum-multi-agent/src/quantum/strategies/evaluator.py), `cfg.entry.order_type` is completely decoupled from `cfg.risk.fee_tier`.
2. Across Batches 001, 002, and 003, **295 out of 300 strategy configurations ($98.3\%$)** contained an execution-cost misconfiguration where aggressive `MARKET` orders crossed the spread but were charged optimistic `maker_passive` fees (8.0 bps round trip, 0.0 bps slippage).
3. Under realistic taker friction (44.0 bps total drag), champion `STRAT_242` collapsed from +$44.40 (+44.4%) net return to -$86.84 (-86.8%) net loss.
4. Bid-ask spread crossing was completely omitted from price execution.
5. Limit orders opening on gap-downs received artificial price improvement via `min(opens[k], limit_px)`.
6. Signal, order, fill, and portfolio acceptance counters were conflated into a single ambiguous metric.

### 1.2 Design Objective
This document defines the comprehensive engineering and mathematical specification for **Session 1.5: Execution Simulator Remediation**. 

The remediated simulator will provide mathematically sound, exchange-accurate, double-counting-free backtesting mechanics across multiple venues (Aster DEX and Bybit), distinct account tiers (Retail VIP0 to Institutional Pro), and true order policies (Passive Maker vs. Aggressive Taker), ensuring all future feasibility research reflects genuine economic reality.

---

## 2. Universe Architecture & XMR Governance Resolution

### 2.1 The Two-Tier Universe Structure
To prevent survivorship distortion and historical data contamination, the QUANTUM perpetual research universe is formally divided into two governed tiers:

```
                               QUANTUM PERPETUAL UNIVERSE
                                      (11 Pairs)
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
     PRIMARY RESEARCH UNIVERSE                    SECONDARY EXPLORATORY ASSET
        (10 Balanced Pairs)                               (1 Pair)
  ADA, AVAX, BNB, BTC, DOGE, ETH,                          XMRUSDT
       LINK, LTC, SOL, XRP                                    │
                  │                                           │
  Continuous 36-Month Panel                        Truncated Listing History
  (2023-10-28 to 2026-10-31)                       (Starts 2026-01-13)
  Total Bars: 4,499,997                            Total Bars: 118,808
  Folds 1 to 4 Walk-Forward                        Fold 4 & Prospective Only
```

### 2.2 Formal Governance Resolution
1. **Primary Research Universe (`PRIMARY_RESEARCH_UNIVERSE`):**
   - **Constituents (10 pairs):** `BTCUSDT`, `ETHUSDT`, `BNBUSDT`, `XRPUSDT`, `ADAUSDT`, `SOLUSDT`, `AVAXUSDT`, `LINKUSDT`, `DOGEUSDT`, `LTCUSDT`.
   - **Role:** Mandatory universe for all walk-forward multi-asset portfolio evaluations, cross-asset lead-lag discovery, and statistical hypothesis tests (Folds 1–4).
   - **Integrity:** 100.00% complete across 9 altcoins ($4,050,000$ bars) plus 1 benchmark pair with a single 1-bar maintenance gap (`BTCUSDT`: $449,997$ bars, $99.9997\%$ completeness).
2. **Secondary Exploratory Asset (`SECONDARY_EXPLORATORY_UNIVERSE`):**
   - **Constituent (1 pair):** `XMRUSDT`.
   - **Role:** Evaluated exclusively under Human Governance Decision Record **DEC_06 Option 3 (Three-Tier Policy)**.
   - **Restriction:** Excluded from the 10-asset 3-year aggregated portfolio backtests. Evaluated only in standalone single-asset studies covering Fold 4 (post-January 2026) and live forward paper trading.
3. **Total Canonical Archive:** $4,499,997 + 118,808 = \mathbf{4,618,805\text{ bars}}$ across all 11 pairs.

---

## 3. Multi-Venue Exchange Fee Architecture & Complete Provenance Matrix

Execution costs cannot be modeled with a single static number. QUANTUM must support explicit venue and tier profiles with documented provenance, official source documentation, and temporal validity.

### 3.1 Exchange Fee Schedule Matrix

$$\text{Round-Trip Fee Drag} = \text{Fee}_{\text{entry}} + \text{Fee}_{\text{exit}}$$

| Venue Profile ID | Exchange Venue | Account Tier / Model | Maker Fee / Leg | Taker Fee / Leg | Round-Trip Maker Fee | Round-Trip Taker Fee | Complete Provenance & Source Reference | Validity Period |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :--- | :--- |
| `BYBIT_VIP0_DEFAULT` | Bybit Linear Perps | Standard Retail (VIP 0) | $2.0\text{ bps}$ ($0.020\%$) | $5.5\text{ bps}$ ($0.055\%$) | **$4.0\text{ bps}$** | **$11.0\text{ bps}$** | Bybit Official Fee Rate Schedule, USDT Linear Perps (`https://www.bybit.com/en/help-center/article/Trading-Fee-Structure`). Default retail tier (<$50k balance, <$10M volume). | Active (2022–Present) |
| `BYBIT_VIP1` | Bybit Linear Perps | Tier 1 (Balance $\ge \$50\text{k}$) | $1.8\text{ bps}$ ($0.018\%$) | $4.0\text{ bps}$ ($0.040\%$) | **$3.6\text{ bps}$** | **$8.0\text{ bps}$** | Bybit Official VIP 1 derivatives schedule ($\ge \$50\text{k}$ asset balance or $\ge \$10\text{M}$ 30d linear volume). | Active (2023–Present) |
| `BYBIT_PRO3` | Bybit Linear Perps | Institutional Pro 3 | $0.0\text{ bps}$ ($0.000\%$) | $2.5\text{ bps}$ ($0.025\%$) | **$0.0\text{ bps}$** | **$5.0\text{ bps}$** | Bybit Institutional Fee Portal ($\ge \$100\text{M}$ 30d derivatives volume). | Active (2023–Present) |
| `ASTER_RETAIL_CORE` | Aster DEX Perps | Base Tier (No Staking) | $4.0\text{ bps}$ ($0.040\%$) | $10.0\text{ bps}$ ($0.100\%$) | **$8.0\text{ bps}$** | **$20.0\text{ bps}$** | Aster DEX Protocol Public Specification (Phase 5.5 DEC_04.7 baseline). Reflects standard on-chain perps without AST token staking discount. | Active (2024–2026) |
| `ASTER_STRESS_TAKER` | Aster DEX Perps | High-Friction Stress Tier | $4.0\text{ bps}$ ($0.040\%$) | $20.0\text{ bps}$ ($0.200\%$) | **$8.0\text{ bps}$** | **$40.0\text{ bps}$** | QUANTUM Phase 5.5 Human Governance Decision Package (DEC_04.7 Tier 3 Stress Specification, commit `dcc8ceb`). Worst-case DEX execution model with high taker fees and gas/settlement load. | Active (Nov 2026 Baseline) |

### 3.2 Dynamic Venue Configuration Schema
The engine will accept a structured Pydantic configuration object (`ExecutionVenueSchedule`):

```python
class ExecutionVenueSchedule(BaseModel):
    venue_id: str
    exchange_name: str
    account_tier: str
    maker_fee_bps_per_leg: float
    taker_fee_bps_per_leg: float
    default_spread_bps: float
    default_slippage_bps: float
    adverse_selection_bps: float
    funding_rate_bps_8h: float = 1.0
    provenance_doc: str
    validity_start_utc: str
```

---

## 4. Single-Channel Cost Accounting & Double-Counting Mathematical Proof

### 4.1 Mutually Exclusive Cost Component Definitions
To eliminate ambiguity, all friction is decomposed into five mutually exclusive economic components:

$$\Phi_{\text{total}} = N \cdot \left[ C_{\text{fee}} + C_{\text{spread}} + C_{\text{slip}} + C_{\text{adverse}} \right] + C_{\text{fund}}$$

Where:
1. **$C_{\text{fee}}$ (Exchange Tariff):** Pure fee paid to the matching engine. Exactly $2 \times \text{fee\_bps\_per\_leg} / 10,000$. Determined strictly by actual liquidity role (`MAKER` vs. `TAKER`).
2. **$C_{\text{spread}}$ (Bid-Ask Spread Crossing):** Cost of crossing the half-spread from the mid-price to market quotes.
   - For Passive Resting Limit Orders: $C_{\text{spread}} \equiv 0.0$ (resting orders provide liquidity and do not cross the spread).
   - For Market Orders and Marketable Limit Orders: $C_{\text{spread}} = \frac{1}{2} \cdot \text{Spread}_{\text{entry}} + \frac{1}{2} \cdot \text{Spread}_{\text{exit}}$.
3. **$C_{\text{slip}}$ (Market Impact Slippage):** Price degradation resulting from order size depleting top-of-book depth ($P_{\text{VWAP}} - P_{\text{BBO}}$).
   - For Resting Limit Orders: $C_{\text{slip}} \equiv 0.0$ (order rests at a declared limit price; zero arrival impact).
   - For Aggressive Market Orders: $C_{\text{slip}} = \gamma \cdot \sigma_t \cdot \sqrt{N / V}$.
4. **$C_{\text{adverse}}$ (Adverse Selection Drag):** Post-fill price decay suffered by resting limit orders due to informed order flow.
   - For Aggressive Market Orders: $C_{\text{adverse}} \equiv 0.0$ (market orders execute immediately and do not rest in the book).
   - For Resting Limit Orders: $C_{\text{adverse}} = \delta_{\text{toxic}}(\sigma_t, \text{RVOL})$.
5. **$C_{\text{fund}}$ (Funding Rate Cash Flow):** 8-hour settlement cash flow based on sign of position and prevailing rate.

### 4.2 Anti-Double-Counting Rules & Active Assertion Framework
In institutional backtesting, double-counting occurs if friction is deducted via fill price adjustment **AND** deducted again in the cash PnL ledger.

QUANTUM enforces **Mode A: Single-Channel Cash Drag Accounting**:
- **Execution Prices:** Fill prices are logged strictly at benchmark prices ($P_{\text{open}}$ for market orders; $P_{\text{limit}}$ for limit orders).
- **Cash Drag Invariant:** All friction ($C_{\text{fee}}, C_{\text{spread}}, C_{\text{slip}}, C_{\text{adverse}}$) is deducted exclusively from the cash ledger:
  $$\text{PnL}_{\text{net}} = N \cdot R_{\text{gross}} - \Phi_{\text{total}} - C_{\text{fund}}$$
- **Active Code Assertions:**
  1. *Maker Invariant:*
     ```python
     if liquidity_role == "MAKER":
         assert spread_drag_usd == 0.0, "Maker order cannot be charged spread crossing!"
         assert slip_drag_usd == 0.0, "Maker order cannot be charged arrival slippage!"
     ```
  2. *Taker Invariant:*
     ```python
     if liquidity_role == "TAKER":
         assert adverse_selection_usd == 0.0, "Taker order cannot be charged adverse selection drag!"
     ```
  3. *Zero Price Adjustment Invariant:*
     ```python
     assert entry_px == nominal_benchmark_px, "Price adjustment and cash drag cannot be applied simultaneously!"
     ```

---

## 5. Microstructure Execution Engine: Liquidity Classification & Marketable Limits

### 5.1 True Liquidity Classification (Including Marketable Limits)
An order labeled `LIMIT` is not automatically a maker order. If its limit price crosses the prevailing market spread upon arrival, it matches immediately as an aggressive taker order.

```
                         ORDER ARRIVAL AT CANDLE i OPEN
                                       │
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
       order_type == "MARKET"                        order_type == "LIMIT"
                │                                             │
         ALWAYS TAKER                                  Evaluate Limit Price
     Fee: taker_fee_bps                            against Arrival Price (P_open)
     Spread: default_spread                                   │
     Slip: default_slip                        ┌──────────────┴──────────────┐
                                               ▼                             ▼
                                        P_limit >= P_open             P_limit < P_open
                                           (for LONG)                    (for LONG)
                                               │                             │
                                       MARKETABLE LIMIT              PASSIVE RESTING LIMIT
                                               │                             │
                                        post_only == True?                   │
                                        ┌──────┴──────┐                      │
                                        ▼             ▼                      ▼
                                     REJECTED       TAKER                  MAKER
                                 (Cancel on Cross) (Charged Taker     (Enters Book Queue;
                                                    fee + spread)      Earns Maker Fee)
```

### 5.2 Formal Classification Rules
1. **Unconditional Market Orders (`order_type == "MARKET"`):**
   - Classified as `TAKER` liquidity role.
   - Charged taker fee per leg ($F_{\text{taker}}$) plus entry half-spread crossing ($S_{\text{entry}}$) plus arrival slippage ($I_{\text{entry}}$).
   - Zero adverse selection drag ($A_{\text{toxic}} = 0.0$).
2. **Marketable Limit Orders (`order_type == "LIMIT"`, `offset <= 0.0` or $P_{\text{limit}} \ge P_{\text{arrival}}$ for longs):**
   - If `post_only == True`: Order is immediately rejected by the exchange matching engine (`CANCEL_ON_CROSS`). Recorded as $N_{\text{rejected\_post\_only}}$, zero fill, zero fee.
   - If `post_only == False`: Order executes immediately against resting liquidity. **Classified as `TAKER`**. Charged taker fee plus spread crossing.
3. **Passive Resting Limit Orders (`order_type == "LIMIT"`, $P_{\text{limit}} < P_{\text{arrival}}$ for longs):**
   - Enters the order book as resting liquidity. **Classified as `MAKER`**.
   - Charged maker fee per leg ($F_{\text{maker}}$).
   - Zero spread crossing ($C_{\text{spread}} = 0.0$) and zero arrival slippage ($C_{\text{slip}} = 0.0$).
   - Subject to limit timeout, touch-fill probability, gap-down fix, and adverse selection drag.

---

## 6. Realistic Limit Mechanics: Heuristic Touch Model, Gap Inversion Fix & Post-Fill Markout Framework

### 6.1 Explicit Labeling of Touch-Fill Probabilities as Uncalibrated Heuristics
> [!IMPORTANT]
> **GOVERNANCE DISCLOSURE:** The boundary touch fill probability ($P_{\text{fill}} = 0.50$ when $\text{low} = P_{\text{limit}}$) and deep penetration fill probability ($P_{\text{fill}} = 1.00$ when $\text{low} < P_{\text{limit}} - 0.2\sigma$) are **UNTESTED, UNCALIBRATED SIMULATION HEURISTICS**.
>
> In historical OHLCV bar backtesting, the exact Level 2 order-book queue position, queue depletion velocity, and cancel/replace rates are unobservable. These heuristic thresholds serve as stress-testing bounds to prevent assuming 100% fill rates on shallow bar touches. When Level 2 depth and trade tick streams are backfilled, these heuristics will be replaced by an empirically calibrated queue survival function $P_{\text{fill}}(Q_{\text{ahead}}, V_{\text{bar}}, \Delta t)$.

### 6.2 Eradication of the Gap-Down Price Improvement Inversion
- **Flawed Legacy Code (`evaluator.py#L300`):**
  `entry_px = min(opens[k], limit_px)` $\implies$ Awards artificial price improvement on downward gap openings.
- **Remediated Institutional Rule:**
  A resting post-only limit buy order rests at $P_{\text{limit}}$. When the market opens lower on a gap ($\text{open}_k < P_{\text{limit}}$), aggressive sell flow trades down through the book, filling the resting order **at its limit price**:
  $$\mathbf{P_{\text{fill}} \equiv P_{\text{limit}}}$$
  The position is filled at $P_{\text{limit}}$, immediately reflecting an unrealized adverse gap loss:
  $$\text{PnL}_{\text{gap}} = N \cdot \left(\frac{\text{open}_k - P_{\text{limit}}}{P_{\text{limit}}}\right) < 0$$

---

### 6.3 Post-Fill Markout Framework for Adverse Selection
Rather than relying on arbitrary friction assumptions, adverse selection will be evaluated using an institutional **Post-Fill Markout Protocol**.

#### 1. Markout Mathematical Formulation
For every executed passive limit fill at timestamp $t$ and fill price $P_{\text{fill}}$, the engine records the forward price markout trajectory across discrete future horizons $h \in \{1, 2, 3, 6, 12, 24\}\text{ bars}$:

$$\text{Markout}_h = \text{Side} \cdot \left(\frac{P_{t+h} - P_{\text{fill}}}{P_{\text{fill}}}\right) \times 10,000\text{ bps}$$

```
                PASSIVE LIMIT BUY FILL (t=0)
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
   INFORMED / TOXIC FLOW               UNINFORMED NOISE
  Price continues to fall             Price stabilizes / bounces
   P(t+1) < P_fill                     P(t+1) >= P_fill
   Markout_1 < 0 (e.g. -3.5 bps)       Markout_1 >= 0 (e.g. +1.2 bps)
   --> ADVERSE SELECTION DETECTED      --> BENIGN FILL
```

#### 2. Adverse Selection Calibration Protocol
1. **Empirical Measurement:** During backtests and replay, the engine computes the median 1-bar markout ($\text{Markout}_1$) across all limit fills:
   $$\text{ToxicDrag}_{\text{observed}} = -\min\left(0.0, \text{median}(\text{Markout}_1)\right)$$
2. **Simulation Sizing:** For backtests without tick data, adverse selection drag is modeled parametrically as:
   $$C_{\text{adverse}} = N \cdot \left(\frac{\alpha_{\text{adverse}} \cdot \sigma_t}{10,000}\right)$$
   Where $\alpha_{\text{adverse}} = 1.5\text{ bps}$ baseline, dynamically scaling up to $3.5\text{ bps}$ during elevated volatility regimes ($\text{RVOL} > 2.0$ or $\sigma_t > \text{quantile}_{0.90}$).

---

## 7. Separate Accounting for Orders, Touches, Fills, Fill Events & Executions

To completely eliminate the conflation of raw signals, serialized candidates, market fills, and portfolio acceptance, the simulator will record **six independent, non-conflated counters**:

```
[Level 1: Raw Candidate Signals]     N_signal            (All timestamps satisfying ML margin & regime)
        │
        ▼ (Single-Asset Concurrency & Cooldown Locks)
[Level 2: Unique Dispatched Orders]  N_unique_orders     (Unique orders dispatched with distinct order_id)
        │
        ▼ (Limit Reach / Barrier Touch)
[Level 3: Touched Orders]            N_touched_orders    (Orders where market reached limit price)
        │
        ▼ (Queue Model & Penetration Probability)
[Level 4: Filled Orders]             N_filled_orders     (Unique orders successfully filled)
        │
        ▼ (Partial Closures & Multi-Leg Fills)
[Level 5: Execution Fill Events]     N_fill_events       (Total distinct execution transactions)
        │
        ▼ (Portfolio Equity & Exposure Limits)
[Level 6: Portfolio Executions]      N_portfolio_exec    (Trades funded & executed by risk manager)
```

### 7.1 Counter Definitions & Strict Invariant Hierarchy

$$\mathbf{N_{\text{signal}} \ge N_{\text{unique\_orders}} \ge N_{\text{touched\_orders}} \ge N_{\text{filled\_orders}} \ge N_{\text{portfolio\_exec}}}$$
$$\mathbf{N_{\text{fill\_events}} \ge N_{\text{filled\_orders}}}$$

| Counter Name | Symbol | Definition & Operational Scope | Drop Reason If Skipped |
| :--- | :---: | :--- | :--- |
| **Raw Signals** | $N_{\text{signal}}$ | Total bar timestamps where entry mask evaluates to `True`. | — |
| **Unique Orders** | $N_{\text{unique\_orders}}$ | Distinct trade orders generated after single-asset position serialization and cooldowns. | Skipped because asset already has an open position or cooldown active. |
| **Touched Orders** | $N_{\text{touched\_orders}}$ | Orders where price reached the limit price within $K_{\text{timeout}}$ bars. | Order timed out without market touching limit price. |
| **Filled Orders** | $N_{\text{filled\_orders}}$ | Unique orders that achieved confirmed fill status. | Order grazed limit boundary but failed queue priority touch model ($P_{\text{fill}} = 0.50$). |
| **Fill Events** | $N_{\text{fill\_events}}$ | Total distinct fill transactions logged. Includes initial entry fill + TP1 partial fill + TP2 fill / SL exit fill. | Multiple events per single order lifecycle ($N_{\text{fill\_events}} \ge N_{\text{filled\_orders}}$). |
| **Portfolio Executions** | $N_{\text{portfolio\_exec}}$ | Orders accepted by RiskAgent and funded with available portfolio equity. | Skipped due to min notional ($5.00), exposure caps, or max concurrent positions. |

### 7.2 Derived Microstructure Rates
1. **Asset Serialization Efficiency:** $\rho_{\text{serialize}} = \frac{N_{\text{unique\_orders}}}{N_{\text{signal}}} \times 100\%$
2. **Order Touch Rate:** $\rho_{\text{touch}} = \frac{N_{\text{touched\_orders}}}{N_{\text{unique\_orders}}} \times 100\%$
3. **Queue Fill Rate:** $\rho_{\text{queue}} = \frac{N_{\text{filled\_orders}}}{N_{\text{touched\_orders}}} \times 100\%$
4. **Market Fill Rate:** $\rho_{\text{fill}} = \frac{N_{\text{filled\_orders}}}{N_{\text{unique\_orders}}} \times 100\%$
5. **Portfolio Capital Acceptance Rate:** $\rho_{\text{capital}} = \frac{N_{\text{portfolio\_exec}}}{N_{\text{filled\_orders}}} \times 100\%$
6. **End-to-End Realization Rate:** $\rho_{\text{conversion}} = \frac{N_{\text{portfolio\_exec}}}{N_{\text{signal}}} \times 100\%$

---

## 8. Mathematical Reconciliation of Standard Scenarios (Zero Double-Counting Proof)

The table below reconciles the exact mathematical derivation of total round-trip friction across the three standard evaluation scenarios, proving that neither spread nor slippage is duplicated:

$$\Phi_{\text{RT}} = \text{Fee}_{\text{entry}} + \text{Fee}_{\text{exit}} + \text{Spread}_{\text{entry}} + \text{Spread}_{\text{exit}} + \text{Slip}_{\text{entry}} + \text{Slip}_{\text{exit}} + \text{Adverse}_{\text{drag}}$$

| Scenario Identifier | Liquidity Role (Entry / Exit) | Exchange Fees (Entry + Exit) | Half-Spread Crossing (Entry + Exit) | Arrival Slippage (Entry + Exit) | Adverse Selection Drag | Total Round-Trip Friction | Double-Counting Reconciliation & Proof |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`BYBIT_VIP0_DEFAULT`** | Taker / Taker | $5.5 + 5.5 = \mathbf{11.0\text{ bps}}$ | $1.0 + 1.0 = \mathbf{2.0\text{ bps}}$ | $1.0 + 1.0 = \mathbf{2.0\text{ bps}}$ | $\mathbf{0.0\text{ bps}}$ | $\mathbf{15.0\text{ bps}}$ | Fee is Bybit VIP0 rate ($11.0$). Spread ($2.0$) and slippage ($2.0$) account for crossing top-of-book and depth. Prices unadjusted. **Zero double-counting**. |
| **`ASTER_STRESS_TAKER`** | Taker / Taker | $20.0 + 20.0 = \mathbf{40.0\text{ bps}}$ | $1.0 + 1.0 = \mathbf{2.0\text{ bps}}$ | $1.0 + 1.0 = \mathbf{2.0\text{ bps}}$ | $\mathbf{0.0\text{ bps}}$ | $\mathbf{44.0\text{ bps}}$ | Fee is Phase 5.5 DEC_04.7 Aster Tier 3 rate ($40.0$). Slippage schedule ($4.0\text{ bps}$) subsumes spread ($2.0$) and impact ($2.0$). Prices unadjusted. **Zero double-counting**. |
| **`MAKER_PASSIVE_TRUE`** | Maker / Maker | $4.0 + 4.0 = \mathbf{8.0\text{ bps}}$ | $0.0 + 0.0 = \mathbf{0.0\text{ bps}}$ | $0.0 + 0.0 = \mathbf{0.0\text{ bps}}$ | $\mathbf{1.5\text{ bps}}$ | $\mathbf{9.5\text{ bps}}$ | Resting limit order earns maker fee ($8.0$). Zero spread and zero slippage charged (maker invariant). $1.5\text{ bps}$ adverse selection deducted for toxic flow. **Zero double-counting**. |

---

## 9. Deterministic Verification & Unit Test Suite Specification

Prior to running any research backtests, the remediated simulator must pass a newly implemented unit test suite (`tests/unit/test_remediated_execution_simulator.py`) covering 7 deterministic scenarios:

### Test Case 1: Market Order / Maker Fee Invalidation
- **Setup:** Create configuration with `entry.order_type = "MARKET"` and attempt to force `risk.fee_tier = "maker_passive"`.
- **Expected Outcome:** Engine raises `ExecutionPolicyMismatchError`. Market orders cannot execute under passive maker fee schedules.

### Test Case 2: Marketable Limit Order Taker Classification
- **Setup:** Create limit buy order with $P_{\text{limit}} \ge P_{\text{arrival}}$ (marketable limit).
- **Expected Outcome:** If `post_only == True`, engine rejects order (`CANCEL_ON_CROSS`). If `post_only == False`, engine classifies liquidity role as `TAKER`, charging taker fees and spread crossing drag.

### Test Case 3: Limit Order Gap Inversion Fix
- **Setup:** Long limit order posted at $P_{\text{limit}} = 100.00$. Next candle opens with a downward gap at $\text{open} = 98.00$, $\text{low} = 97.00$, $\text{close} = 99.00$.
- **Expected Output:**
  - Fill price is strictly $P_{\text{fill}} = 100.00$ (NOT $98.00$).
  - At bar close ($99.00$), unrealized trade return is $\frac{99.00 - 100.00}{100.00} = \mathbf{-1.00\%}$ (NOT $+1.02\%$).

### Test Case 4: Double-Counting Invariant Assertion
- **Setup:** Simulator executes with Mode A.
- **Assertion:** Assert that $P_{\text{entry\_fill}} == \text{open}_i$, and that no price adjustment is subtracted while cash drag is simultaneously applied.

### Test Case 5: Limit Order Queue Touch Probability Heuristic
- **Setup:** 100 limit orders tested where bar low strictly equals $P_{\text{limit}}$ ($\text{low} == P_{\text{limit}}$).
- **Expected Output:** Exactly $\approx 50\%$ filled ($N_{\text{filled\_orders}} \approx 50$), verifying the heuristic touch model.

### Test Case 6: Counter Invariant Verification
- **Setup:** Run 100 synthetic bars with 20 raw signals, 15 unique orders, 10 touches, 8 filled orders, 16 fill events (entry + exit), and 5 portfolio executions.
- **Expected Output:** Assert that $N_{\text{signal}} = 20$, $N_{\text{unique\_orders}} = 15$, $N_{\text{touched\_orders}} = 10$, $N_{\text{filled\_orders}} = 8$, $N_{\text{fill\_events}} = 16$, $N_{\text{portfolio\_exec}} = 5$, and verify all six derived rates.

### Test Case 7: Post-Fill Markout Calculation
- **Setup:** Passive limit buy filled at $P_{\text{fill}} = 100.00$. Subsequent 3 bars close at $99.50, 99.20, 99.80$.
- **Expected Output:** Engine records $\text{Markout}_1 = -50.0\text{ bps}$, $\text{Markout}_2 = -80.0\text{ bps}$, $\text{Markout}_3 = -20.0\text{ bps}$.

---

## 10. Historical Batch Re-Evaluation Protocol (Batches 001–003)

### 10.1 The Re-Evaluation Mandate
The 295 configurations in Batches 001–003 containing execution-cost misconfigurations will NOT be discarded. Instead, they will be systematically re-evaluated under the standardized three-scenario matrix:

```
                       RE-EVALUATION MATRIX (295 CONFIGURATIONS)
                                          │
            ┌─────────────────────────────┼─────────────────────────────┐
            ▼                             ▼                             ▼
       SCENARIO 1                    SCENARIO 2                    SCENARIO 3
   Realistic Retail Taker       High-Friction Stress Taker      True Passive Post-Only
     (BYBIT_VIP0_DEFAULT)          (ASTER_STRESS_TAKER)          (MAKER_PASSIVE_TRUE)
  11.0 bps fee + 4.0 bps drag   40.0 bps fee + 4.0 bps drag   Limit entry at offset > 0
  Total Friction: 15.0 bps      Total Friction: 44.0 bps      Adverse selection applied
```

### 10.2 Output Artifacts
- Script: `scripts/run_batch_forensic_reevaluation.py`
- Manifest: `data_backtest/recalculated/batch_reevaluation_manifest.json`
- Summary Report: `audit/strategy_research/BATCH_001_003_REEVALUATION_REPORT.md`
- Updated Global Leaderboard: `data_backtest/leaderboard/global_leaderboard_reconciled.json`

---

## 11. File Scope, Architecture Preservation & Acceptance Gate

### 11.1 Affected File Scope
The remediation will be strictly confined to execution and evaluation components:
- **Modified Production Files (When Authorized):**
  1. [`src/quantum/strategies/evaluator.py`](file:///d:/quantum-multi-agent/src/quantum/strategies/evaluator.py): Implement venue schedules, order-type coupling, marketable limit logic, gap-down fix, touch probability, and 6-tier counters.
  2. [`src/quantum/strategies/schemas.py`](file:///d:/quantum-multi-agent/src/quantum/strategies/schemas.py): Add venue schedule schema and 6-tier counter metrics to `StrategyEvaluationResult`.
  3. [`src/quantum/backtesting/phase562_engine.py`](file:///d:/quantum-multi-agent/src/quantum/backtesting/phase562_engine.py): Mirror venue schedules and counter invariants.
- **New Test Files (When Authorized):**
  4. `tests/unit/test_remediated_execution_simulator.py`: 7 deterministic test cases.
- **Preserved Production Files (ZERO MODIFICATIONS):**
  - All six agent contracts and agents in [`src/quantum/agents/`](file:///d:/quantum-multi-agent/src/quantum/agents/) (`Scout`, `Analyst`, `Sniper`, `Risk`, `Banker`, `Orchestrator`).
  - All historical Parquet files in `data/historical/`.
  - All prospective holdout files ($\ge \text{1793491200000 ms}$).

---

### 11.2 Session 1.5 Acceptance Gate

**REVISED DESIGN SPECIFICATION COMPLETE.**

- **Governance State:** This document represents the complete, actionable architectural blueprint for execution simulator remediation.
- **Strict Limitation Enforced:** Zero lines of production code or test code were modified during this turn.
- **Holdout Status:** The prospective holdout ($\ge \text{1793491200000 ms}$) remains strictly sealed.

**The agent has stopped as instructed. Standing by for formal Project Owner review, feedback, and explicit authorization to proceed with implementation.**
