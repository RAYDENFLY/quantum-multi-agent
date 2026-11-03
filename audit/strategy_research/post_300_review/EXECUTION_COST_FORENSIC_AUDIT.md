# QUANTUM — Execution Model Forensic Audit & Friction Sensitivity Analysis

**Document Identifier:** `audit/strategy_research/post_300_review/EXECUTION_COST_FORENSIC_AUDIT.md`  
**Evaluation Date:** `2026-11-03T02:46:00Z`  
**Git Commit:** `dcc8ceb54d80b1b9685d92236f48b0994610522a`  
**Subject:** Examination of the Technical Compatibility between `order_type: MARKET` and `fee_tier: maker_passive`

---

## 1. Executive Summary & Core Forensic Finding

> [!CAUTION]
> **CRITICAL EXECUTION MODEL INCONSISTENCY IDENTIFIED:**  
> In the Phase 5.6.2 strategy configuration schema, `STRAT_242` specifies `entry.order_type = "MARKET"`, but was evaluated under `risk.fee_tier = "maker_passive"` (charging 8.0 bps round-trip fee with 0.0 bps slippage).  
> In real-world exchange microstructure, **a market order CANNOT receive passive maker fee rebates or zero slippage**. A market order aggressively crosses the bid-ask spread and consumes resting limit liquidity, paying taker fees (typically 18–40 bps round-trip) plus spread crossing and market impact.  
> When realistic taker or hybrid execution friction is applied, **`STRAT_242`'s net cumulative return flips from `+44.40%` into a catastrophic loss (`-8.76%` under 15 bps hybrid friction, `-34.28%` under 20 bps retail friction, and `-86.84%` under 44 bps Aster taker friction).**

---

## 2. Technical Compatibility Analysis

### 2.1 The Microstructure Conflict
In perpetual futures trading:
1. **Aggressive Market Orders (`MARKET`):**
   - **Mechanism:** Immediately executes against the best resting limit orders on the opposite side of the order book (e.g., buying at Ask 1).
   - **Fees:** Charged the **Taker Fee Tier** (Aster DEX: 20.0 bps per leg = 40.0 bps round-trip; Binance/Bybit VIP0: 4.5–5.0 bps per leg = 9.0–10.0 bps round-trip; Retail: 6.0–10.0 bps per leg = 12.0–20.0 bps round-trip).
   - **Slippage & Spread:** Incurs half the bid-ask spread on entry and half on exit, plus adverse market impact (typically 1.0–4.0 bps on 5m crypto altcoins).
2. **Passive Post-Only Limit Orders (`LIMIT`):**
   - **Mechanism:** Rest in the order book at or below the current Bid 1 (for longs), providing liquidity to other participants.
   - **Fees:** Charged the **Maker Fee Tier** (Aster DEX: 4.0 bps per leg = 8.0 bps round-trip; Binance/Bybit VIP0: 1.0–2.0 bps per leg = 2.0–4.0 bps round-trip; Top-tier MM: negative rebate).
   - **Microstructure Penalties:**
     - **Execution Queue Risk:** Not all limit orders are filled if price bounces away without touching the resting limit.
     - **Adverse Selection:** Resting bids are disproportionately filled when a severe market sell cascade punches through the level, meaning the filled trades suffer worse subsequent drawdowns than unconditioned entries.

### 2.2 Root Cause in Phase 5.6.2 Engine
In `src/quantum/strategies/schemas.py`, `EntryParameters` had `order_type: str = "MARKET"`, while `RiskExecutionParameters` defaulted to `fee_tier: str = "maker_passive"`.  
In `src/quantum/strategies/evaluator.py` line 443:
```python
fee_bps, slip_bps = FEE_TIERS_BPS.get(r_cfg.fee_tier, (8.0, 0.0))
```
The evaluator assigned fees strictly based on `r_cfg.fee_tier`, regardless of whether `order_type` was `"MARKET"` or `"LIMIT"`. Because `STRAT_242` left `fee_tier` at the default `"maker_passive"`, it executed instantaneous fills at the bar open price while being billed only 8.0 bps round-trip without slippage.

---

## 3. Five-Scenario Execution Stress Audit on `STRAT_242`

To quantify the true impact of execution costs, `scripts/run_post_300_forensic_review.py` evaluated `STRAT_242` across 4 custom execution scenarios, generating distinct experiment manifests in `data_backtest/recalculated/` and `data_backtest/manifests/`:

| Scenario Code | Description | Fee Schedule | Slippage | Total Friction | Ending Equity ($) | Net Cum. Return | Mean Daily Return | Net Expectancy | Profit Factor | Max Drawdown | Positive Folds | Qualified? |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Scenario 1: `MAKER_8BPS`** | Historical Baseline (Maker passive) | 8.0 bps | 0.0 bps | **8.0 bps** | **`$144.40`** | **`+44.40%`** | **`+0.1092%/day`** | `+7.33 bps` | `1.108` | `16.35%` | `3 / 4` | **`YES`** |
| **Scenario 2: `HYBRID_14BPS`** | Realistic Hybrid (Maker entry + Taker SL/TP) | 14.0 bps | 1.0 bps | **15.0 bps** | **`$91.24`** | **`-8.76%`** | **`-0.0160%/day`** | `+0.33 bps` | `0.975` | `26.46%` | `1 / 4` | **`NO`** |
| **Scenario 3: `RETAIL_20BPS`** | Standard Retail / VIP0 Taker | 18.0 bps | 2.0 bps | **20.0 bps** | **`$65.72`** | **`-34.28%`** | **`-0.1050%/day`** | `-4.67 bps` | `0.894` | `39.61%` | `1 / 4` | **`NO`** |
| **Scenario 4: `ASTER_44BPS`** | Aster Canonical DEX Stress Taker | 40.0 bps | 4.0 bps | **44.0 bps** | **`$13.16`** | **`-86.84%`** | **`-0.5357%/day`** | `-30.15 bps` | `0.601` | `87.03%` | `0 / 4` | **`NO`** |

```
Cumulative Equity Curve Trajectory under Varying Execution Friction ($100 Starting Equity)
$150 |===========================> $144.40 (Scenario 1: 8 bps Maker)
$100 |--------------------------- [Break-even Line]
 $90 |..........................>  $91.24 (Scenario 2: 15 bps Hybrid)
 $60 |..........................>  $65.72 (Scenario 3: 20 bps Retail)
 $10 |..........................>  $13.16 (Scenario 4: 44 bps Aster DEX Taker)
     +---------------------------
     Fold 1    Fold 2    Fold 3    Fold 4
```

---

## 4. Cross-Champion Friction Resilience Matrix

The same friction schedules were applied across all top candidates from Batches 001, 002, and 003 to determine whether any strategy retains positive expectancy under realistic taker costs:

| Strategy ID | Batch | Applicable Assets | Gross Expectancy | 8 bps Maker Net Return | 15 bps Hybrid Net Return | 20 bps Retail Net Return | 44 bps Taker Net Return | Breakeven Friction Ceiling |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`STRAT_242`** | B003 | DOGE, SOL, ADA, XRP, LINK (5) | `+15.42 bps` | **`+44.40%`** (`PF 1.108`) | `-8.76%` (`PF 0.975`) | `-34.28%` (`PF 0.894`) | `-86.84%` (`PF 0.601`) | **`15.3 bps`** |
| **`STRAT_262`** | B003 | DOGE, SOL, ADA, XRP, LINK (5) | `+15.58 bps` | **`+40.65%`** (`PF 1.113`) | `-7.58%` (`PF 0.976`) | `-31.54%` (`PF 0.891`) | `-84.55%` (`PF 0.587`) | **`15.5 bps`** |
| **`STRAT_134`** | B002 | DOGE, SOL, ADA, XRP, LINK (5) | `+14.86 bps` | **`+36.16%`** (`PF 1.092`) | `-12.03%` (`PF 0.965`) | `-35.62%` (`PF 0.886`) | `-86.03%` (`PF 0.602`) | **`14.8 bps`** |
| **`STRAT_273`** | B003 | DOGE, SOL, ADA, XRP, LINK (5) | `+14.71 bps` | **`+33.52%`** (`PF 1.096`) | `-10.02%` (`PF 0.968`) | `-32.12%` (`PF 0.888`) | `-82.23%` (`PF 0.605`) | **`14.6 bps`** |
| **`STRAT_218`** | B003 | DOGE, SOL, ADA, XRP, LINK (5) | `+13.91 bps` | **`+26.93%`** (`PF 1.062`) | `-23.48%` (`PF 0.936`) | `-46.70%` (`PF 0.859`) | `-88.40%` (`PF 0.588`) | **`13.8 bps`** |
| **`STRAT_204`** | B003 | DOGE, SOL, ADA, XRP, LINK (5) | `+13.85 bps` | **`+20.12%`** (`PF 1.062`) | `-18.65%` (`PF 0.936`) | `-38.43%` (`PF 0.858`) | `-84.56%` (`PF 0.575`) | **`13.8 bps`** |
| **`STRAT_061`** | B001 | 6 Alpha Assets | `+12.44 bps` | **`+13.88%`** (`PF 1.077`) | `-8.61%` (`PF 0.951`) | `-21.89%` (`PF 0.872`) | `-63.29%` (`PF 0.588`) | **`12.4 bps`** |

### Mathematical Reality of the Gross Edge
- The gross predictive skill of the frozen LightGBM specialists after a 1-hour liquidity flush produces **`+14.0 to +15.5 bps`** of gross displacement per trade.
- If total round-trip execution friction (fee + slippage + funding) is $\le 10\text{ bps}$, the strategy generates positive net equity compounding.
- If round-trip friction exceeds **`15.5 bps`**, **no strategy in Batches 001, 002, or 003 can survive**.

---

## 5. Execution Model Verdict & Remediation Plan

1. **Classification:**  
   `STRAT_242` is **`CONDITIONALLY_VALID`**.
2. **Operational Conditions for Validity:**
   - **Strict Execution Mode:** Cannot be traded via unconditioned market orders.
   - **Maker-Only Mandate:** Must execute entries via **Post-Only Maker Limit Orders** (e.g. resting at Bid 1 or with a small limit discount $\delta \le 0.05 \sigma$) to capture maker fee rebates ($\le 2.0\text{ bps}$ per leg).
   - **Take-Profit Execution:** Must place limit take-profit orders rather than market orders.
   - **Alternative for Batch 004:** In Batch 004, the research focus must pivot to **expanding the gross displacement beyond 45 bps** (e.g. longer hold times, multi-timeframe 15m/1h trend alignment, or extreme volatility expansion regimes) so that trades remain profitable even after paying full 20–44 bps taker friction.
