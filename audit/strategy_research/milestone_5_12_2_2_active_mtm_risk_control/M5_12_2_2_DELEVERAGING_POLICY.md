# M5.12.2.2 Deleveraging Policy & Position Reduction Audit

**Milestone:** M5.12.2.2 — Active MTM Risk Control & Admission Buffer Enforcement  
**Repository:** `d:/quantum-multi-agent`  
**Component:** `src/quantum/accounting/risk_controller.py`  
**Data Reference:** [M5_12_2_2_DELEVERAGING_COMPARISON.csv](file:///d:/quantum-multi-agent/audit/strategy_research/milestone_5_12_2_2_active_mtm_risk_control/M5_12_2_2_DELEVERAGING_COMPARISON.csv)  
**Audit Date:** 2026-11-04  
**Audit Status:** **VERIFIED & CONFIRMED**

---

## 1. Executive Summary

When passive market price movements cause gross exposure to expand into the `CRITICAL` state ($\ge 1.0000x$), the portfolio requires an event-driven position reduction mechanism to restore exposure below the target cap.

The [`DeleveragingEngine`](file:///d:/quantum-multi-agent/src/quantum/accounting/risk_controller.py#L247-L435) implements a cost-aware, multi-policy reduction framework that:
1. Calculates exact excess notional required to restore exposure to the safe target ($0.9500x$).
2. Evaluates 3 deterministic candidate reduction policies under identical stressed conditions.
3. Accounts for execution friction (taker fees, spread crossing, slippage).
4. Enforces exchange minimum order notional constraints ($\ge \$5.00$).
5. Strictly enforces the **No-Fabricated-Liquidity Invariant**: If market liquidity fails or orders are rejected, the engine logs the failure, leaves exposure unchanged, and transitions the portfolio state to `HALTED`.

---

## 2. Mathematical Sizing Formula

The required gross notional reduction is:

$$N_{\text{target}} = \text{TargetExposure} \times \text{CurrentEquity}$$

$$N_{\text{excess}} = \max\left(0, N_{\text{committed}} - N_{\text{target}}\right)$$

Where:
- $\text{TargetExposure} = 0.9500x$ (Restores portfolio to the upper boundary of `WARNING` / lower boundary of `REDUCE_ONLY`)
- Slices below the exchange minimum viable notional ($N_{\text{min}} = \$5.00$) are scaled up to full position close or minimum viable order size to avoid dust order rejections.

---

## 3. Policy Comparison Matrix

Under identical adverse market conditions (Equity decayed from $100.00 to $92.93, Notional expanded to $101.18, Initial Exposure = `1.088854x`):

| Policy | Priority Selection Logic | Reduced Symbol(s) | Reduction ($) | Closing Friction ($) | Final Exposure | Target Restored? | Execution Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Policy A** | **Largest Notional First** | `SOLUSDT` | $12.90 | $0.0168 | **0.894605x** | **YES** ($\le 0.95x$) | **SUCCESS** |
| **Policy B** | **Highest Risk Contribution First** | `SOLUSDT` | $12.90 | $0.0168 | **0.894605x** | **YES** ($\le 0.95x$) | **SUCCESS** |
| **Policy C** | **Lowest Closing Friction First** | `ETHUSDT` | $12.90 | $0.0168 | **0.891448x** | **YES** ($\le 0.95x$) | **SUCCESS** |
| **Illiquid Book** | **Liquidity Failure Simulation** | `NONE` | $0.00 | $0.0000 | **1.088854x** | **NO** | **FAILED $\to$ HALTED** |

---

## 4. Key Comparative Insights

1. **Short Position Convexity Identification:**
   - Both Policy A and Policy B selected `SOLUSDT` for reduction.
   - Because `SOLUSDT` was a SHORT position that experienced a 10% adverse rally, its notional had expanded from $24.80 to $27.28 while generating unrealized losses. Trimming `SOLUSDT` immediately arrested the convex exposure explosion.
2. **Policy Recommendation for High-Frequency Deployment:**
   - **Policy B (Highest Risk Contribution First)** is recommended as the authoritative operational policy for Milestone 5.13: prioritizing short positions with adverse momentum minimizes future MTM exposure volatility.
3. **Liquidity Failure Safety:**
   - When order execution was marked as failing (illiquid book or rejected order), the engine made **zero ledger adjustments**, did not fabricate cash, and logged `status_code="SIMULATED_LIQUIDITY_FAILURE"`.
   - The [`RiskStateMachine`](file:///d:/quantum-multi-agent/src/quantum/accounting/risk_controller.py#L151-L245) immediately transitioned to **`HALTED`**, permanently blocking further trading.

**Verdict: PASS (Deleveraging Engine Verified)**
