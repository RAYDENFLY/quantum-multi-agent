# M5.12.2.2 Deterministic Risk State Machine Specification

**Milestone:** M5.12.2.2 — Active MTM Risk Control & Admission Buffer Enforcement  
**Repository:** `d:/quantum-multi-agent`  
**Component:** `src/quantum/accounting/risk_controller.py`  
**Audit Date:** 2026-11-04  
**Audit Status:** **VERIFIED & CONFIRMED**

---

## 1. Executive Summary

The [`RiskStateMachine`](file:///d:/quantum-multi-agent/src/quantum/accounting/risk_controller.py#L151-L245) provides a deterministic, finite-state risk controller governing the QUANTUM portfolio.

To eliminate rapid state oscillations (flip-flopping) caused by microsecond tick volatility, the state machine implements:
1. **Instantaneous Escalation:** Transitions to higher-risk states occur immediately upon threshold breach with zero latency.
2. **Hysteresis De-escalation:** Transitions to lower-risk states require exposure to drop below the threshold by a mandatory safety buffer ($\Delta_{\text{hysteresis}} = 0.0200 = 200\text{ bps}$).
3. **Audit Provenance:** Every transition emits an immutable [`RiskStateTransition`](file:///d:/quantum-multi-agent/src/quantum/accounting/risk_controller.py#L40-L50) record with timestamp, trigger metrics, and reason codes.
4. **Permanent Ruin Invariant:** Once equity reaches or drops below $\$1.00$, the state transitions to `RUIN` and can never recover.

---

## 2. State Definitions & Operational Rules

| State | Exposure Boundary | Portfolio Action Required | Entry Permitted? |
| :--- | :---: | :--- | :---: |
| **`NORMAL`** | $< 0.9000x$ | Normal simulation operations | **YES** |
| **`WARNING`** | $0.9000x \le \text{Exp} < 0.9500x$ | Increase monitoring frequency; block discretionary scaling | **YES** (with caution) |
| **`REDUCE_ONLY`** | $0.9500x \le \text{Exp} < 1.0000x$ | Block ALL new entries; evaluate passive trimming | **STRICTLY NO** |
| **`CRITICAL`** | $\ge 1.0000x$ | Immediate event-driven position deleveraging triggered | **STRICTLY NO** |
| **`HALTED`** | Execution Failure | Position reduction failed; emergency freeze | **STRICTLY NO** |
| **`RUIN`** | $\text{Equity} \le \$1.00$ | Terminal capital exhaustion; permanent shutdown | **PERMANENT HALT** |

---

## 3. Threshold Calibration & Admission Cap Interaction

### 3.1 The 4-Asset Allocation Dilemma
Under Milestone 5.12.2.2's candidate admission cap:
$$\text{admission\_exposure\_cap} = 0.995000x$$
A portfolio configured for $N=4$ concurrent positions with max symbol weight $W_{\text{max}} = 0.2500$ targets:
$$\text{Full Initial Exposure} = 4 \times 0.2487x = 0.995000x$$

If the static `WARNING` threshold is set at $0.9000x$ and `REDUCE_ONLY` is set at $0.9500x$:
- **Finding:** A fully allocated portfolio will immediately enter `REDUCE_ONLY` upon opening its 4th position, even with zero adverse market movement!
- **Operational Reality:**
  - For **partially allocated portfolios** (1 to 3 positions, exposure $0.25x - 0.75x$), the $0.90x$ and $0.95x$ thresholds provide useful warnings against over-committing.
  - For **fully allocated portfolios** (4 positions at $0.25x$), the system must be calibrated such that:
    - **Normal Operating Band:** $\le 0.995000x$ (Within admission cap)
    - **Buffer Zone (REDUCE_ONLY):** $0.995000x < \text{Exposure} < 1.000000x$ (Market drift has pushed exposure into the 50 bps microstructural buffer; block new orders, monitor closely).
    - **CRITICAL Zone:** $\ge 1.000000x$ (Hard breach; immediate deleveraging required).

---

## 4. Hysteresis Verification Evidence

As demonstrated in `scripts/audit_phase_d_risk_state_machine.py`, the state machine was tested against rapid boundary noise:

```
=== RISK STATE MACHINE HYSTERESIS AUDIT ===
 step_time_ms                                                            description exposure  equity resulting_state
         1000                                                   Initial low exposure  0.5000x $100.00          NORMAL
         2000                                           Rising exposure near warning  0.8900x $100.00          NORMAL
         3000                                                Crosses 0.90 -> WARNING  0.9100x $100.00         WARNING
         4000                         Small dip: should STAY in WARNING (hysteresis)  0.9050x $100.00         WARNING
         5000                            Above 0.88 recovery target: STAY in WARNING  0.8950x $100.00         WARNING
         6000                   Drops below 0.88 (0.90 - 0.02) -> Recovers to NORMAL  0.8750x $100.00          NORMAL
         7000                                           Jumps to 0.96 -> REDUCE_ONLY  0.9600x $100.00     REDUCE_ONLY
         8000          Dips to 0.94: Above 0.93 recovery target -> STAYS REDUCE_ONLY  0.9400x $100.00     REDUCE_ONLY
         9000                                   Adverse shock -> CRITICAL (>= 1.00x)  1.0200x  $95.00        CRITICAL
        10000                    Slight improvement but above 0.98 -> STAYS CRITICAL  1.0050x  $93.00        CRITICAL
        11000 Deleveraging drops below 0.98 (1.00 - 0.02) -> Recovers to REDUCE_ONLY  0.9750x  $96.00     REDUCE_ONLY
        12000                              Catastrophic equity loss <= $1.00 -> RUIN  0.5000x   $0.50            RUIN
        13000                         Attempted recovery: Must STAY RUIN (permanent)  0.1000x  $50.00            RUIN

Recorded Transitions:
  [3000ms] NORMAL -> WARNING | Exp: 0.9100x | Reason: EXPOSURE_GE_WARNING: Committed exposure 0.910000 >= 0.9000
  [6000ms] WARNING -> NORMAL | Exp: 0.8750x | Reason: WARNING_RECOVERY: Exposure 0.875000 cleared target 0.8800
  [7000ms] NORMAL -> REDUCE_ONLY | Exp: 0.9600x | Reason: EXPOSURE_GE_REDUCE_ONLY: Committed exposure 0.960000 >= 0.9500
  [9000ms] REDUCE_ONLY -> CRITICAL | Exp: 1.0200x | Reason: EXPOSURE_GE_CRITICAL: Committed exposure 1.020000 >= 1.0000
  [11000ms] CRITICAL -> REDUCE_ONLY | Exp: 0.9750x | Reason: CRITICAL_RECOVERY: Exposure 0.975000 cleared hysteresis target 0.9800
  [12000ms] REDUCE_ONLY -> RUIN | Exp: 0.5000x | Reason: EQUITY_LE_RUIN_THRESHOLD: Equity $0.50 <= $1.00
```

### Key Confirmations:
1. **Zero Flip-Flopping:** Exposure fluctuations at 0.905x and 0.895x did not oscillate out of WARNING.
2. **Recovery Buffer Respected:** State only de-escalated once exposure cleared the full 200 bps hysteresis buffer ($0.90 - 0.02 = 0.88$).
3. **CRITICAL Response:** Exposure above 1.0000x immediately triggered CRITICAL; de-escalation required dropping below $0.9800x$ ($1.00 - 0.02$).
4. **Permanent Ruin Protection:** Once equity reached $\$0.50$, the system entered `RUIN` permanently; subsequent equity injections did not reset the state.

**Verdict: PASS (Deterministic State Machine Verified)**
