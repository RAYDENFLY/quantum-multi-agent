# M5.12.2.2 Baseline Forensics & Risk Architecture Audit

**Milestone:** M5.12.2.2 — Active MTM Risk Control & Admission Buffer Enforcement  
**Repository:** `d:/quantum-multi-agent`  
**Branch:** `research/quantum-next-3pct`  
**Baseline Commit:** `ce9367b49d3dfd875cbdf3fa17081b678d5c98da` (`ce9367b`)  
**Audit Date:** 2026-11-04  
**Audit Classification:** Forensic Baseline & Architectural Gap Analysis  

---

## 1. Baseline Synchronization & Commit Verification

### 1.1 Git State Verification
- **Branch:** `research/quantum-next-3pct`
- **Remote Synchronization:** Up to date with `origin/research/quantum-next-3pct`
- **Working Tree:** Clean (0 untracked, 0 modified files prior to milestone start)
- **Baseline Commit SHA:** `ce9367b49d3dfd875cbdf3fa17081b678d5c98da`
- **Author:** Azis Maulana Suhada <raydenfly84@gmail.com>
- **Subject:** `audit(milestone-5.12.2.1): independent evidence reconciliation and adversarial validation`

### 1.2 Previous Milestone (M5.12.2.1) Commit Diff Scope
The previous commit (`ce9367b`) delivered 23 files and +4,118 lines:
- 17 independent audit deliverables in `audit/strategy_research/milestone_5_12_2_1_evidence_reconciliation/`
- 6 reproducible audit and reconciliation scripts in `scripts/`:
  - `scripts/audit_phase_a_forensics.py`
  - `scripts/audit_adversarial_exposure_boundaries.py`
  - `scripts/reconcile_hyp06_trades.py`
  - `scripts/reconcile_hyp05_trades.py`
  - `scripts/audit_phase_e_statistical_engine.py`
  - `scripts/reconcile_execution_coverage.py`

All historical deliverables from M5.12, M5.12.1, and M5.12.2.1 remain intact and immutable.

---

## 2. Source Inspection: Accounting & Exposure Architecture

### 2.1 Inspection of `src/quantum/accounting/event_ledger.py`
The primary accounting engine is implemented in [`EventDrivenPortfolioLedger`](file:///d:/quantum-multi-agent/src/quantum/accounting/event_ledger.py#L95-L683):
- **Initialization (Lines 98–113):**
  - `initial_equity_usd`: $100.00
  - `max_gross_exposure`: 1.0000x
  - `max_concurrent_positions`: 4
  - `max_symbol_weight`: 0.25 (25%)
  - `ruin_equity_threshold`: $1.00
  - `safety_buffer`: 0.0020 (20 bps)
- **Exposure Sizing & Validation (`can_open_position`, Lines 213–266):**
  - Calculates permissible notional accounting for post-entry friction.
  - Formula:
    ```python
    denom_exp = 1.0 + (self.max_gross_exposure * entry_friction_rate)
    fric_cap = max(0.0, ((self.equity * self.max_gross_exposure) - current_committed - 1e-6) / denom_exp)
    candidate = min(desired_notional, max_notional_by_weight, raw_avail)
    ```
  - Enforces zero-tolerance check:
    ```python
    anticipated_post_equity = self.equity - (allocated_notional * entry_friction_rate)
    anticipated_post_exposure = (current_committed + allocated_notional) / anticipated_post_equity
    if round(anticipated_post_exposure, 6) > round(self.max_gross_exposure, 6):
        return False, "EXPOSURE_BREACH", 0.0
    ```
- **Clamping Safeguard in `open_position` (Lines 462–471):**
  - If post-trade exposure rounds above `max_gross_exposure`, it calculates excess notional and trims position quantity:
    ```python
    post_exp = self.get_gross_exposure()
    if round(post_exp, 6) > round(self.max_gross_exposure, 6):
        excess_notional = self.get_gross_notional() - (self.equity * self.max_gross_exposure)
        if excess_notional > 0:
            trim_qty = excess_notional / fill_price
            pos.quantity = max(0.0, pos.quantity - trim_qty)
            pos.entry_notional = pos.quantity * fill_price
    ```
- **Equity Update in `close_position` (Lines 534–536):**
  - Lines 534–535:
    ```python
    self.cash_balance += net_pnl
    self.equity = self.cash_balance  # Assuming all others marked
    ```
  - **Defect Identified:** Setting `self.equity = self.cash_balance` overwrites any accumulated unrealized PnL of other concurrently open positions. It should be:
    ```python
    self.equity = self.cash_balance + sum(unrealized_pnl of other open positions)
    ```

### 2.2 Inspection of `src/quantum/accounting/oracle.py`
The independent accounting oracle is implemented in [`IndependentAccountingOracle`](file:///d:/quantum-multi-agent/src/quantum/accounting/oracle.py#L58-L437):
- Re-implements double-entry cash and position accounting independently.
- Contains independent `compute_equity()` (Line 109) which computes `self.cash + compute_unrealized_pnl(prices)`.
- Contains independent order reservation (`reserve_order`, Line 136) and execution (`process_entry`, Line 206).
- Sizing matches `fric_cap` formula from `event_ledger.py`.
- Reconciles 1:1 against the primary ledger in dedicated test suite `test_milestone_5_12_1_accounting_oracle.py`.

---

## 3. Position Lifecycle & Exposure Code Paths

Every code path capable of opening, increasing, reducing, or closing a position was mapped:

| Path ID | Method | Component | Action | Sizing / Exposure Impact |
| :---: | :--- | :--- | :--- | :--- |
| **P-01** | `can_open_position()` | `EventDrivenPortfolioLedger` | Gatekeeper / Sizing | Sizes order bounded by `fric_cap` and `max_symbol_weight` |
| **P-02** | `reserve_pending_order()` | `EventDrivenPortfolioLedger` | Pending Reservation | Atomically adds to `reserved_pending_notional` |
| **P-03** | `cancel_pending_order()` | `EventDrivenPortfolioLedger` | Pending Cancellation | Atomically deducts from `reserved_pending_notional` |
| **P-04** | `open_position()` | `EventDrivenPortfolioLedger` | Direct Entry | Deducts entry friction from cash; adds to `open_positions` |
| **P-05** | `open_position(pending_id)` | `EventDrivenPortfolioLedger` | Pending Order Fill | Converts `reserved_pending_notional` into `open_positions` |
| **P-06** | `open_position(is_partial)` | `EventDrivenPortfolioLedger` | Partial Order Fill | Slices pending reservation; remainder remains reserved |
| **P-07** | `close_position()` | `EventDrivenPortfolioLedger` | Full Exit | Deletes from `open_positions`; credits realized net PnL |
| **P-08** | `close_position(pct < 1)` | `EventDrivenPortfolioLedger` | Partial Exit | Reduces `pos.quantity` and `entry_notional`; credits slice |
| **P-09** | `update_mark_to_market()` | `EventDrivenPortfolioLedger` | MTM Revaluation | Recomputes `self.equity = cash + unrealized_tot` |
| **P-10** | `accrue_funding()` | `EventDrivenPortfolioLedger` | Funding Settlement | Deducts funding cost from cash and equity |
| **P-11** | `process_entry()` | `IndependentAccountingOracle` | Oracle Entry | Independent sizing and cash deduction |
| **P-12** | `process_exit()` | `IndependentAccountingOracle` | Oracle Exit | Independent gross PnL, exit friction, cash credit |

---

## 4. Identified Risk-Control Gaps

The forensic audit revealed seven concrete architectural gaps:

### Gap 1: Inert Safety Buffer Configuration
- In `EventDrivenPortfolioLedger.__init__`, `self.safety_buffer = 0.0020` is accepted as an argument, but is never used anywhere in `can_open_position()`, `reserve_pending_order()`, or `open_position()`.
- Sizing uses `max_gross_exposure` directly (1.0000x), leaving zero pre-trade buffer against execution slippage, adverse fill price, or fee surprises.

### Gap 2: Pre-Trade Admission vs Post-Trade Mark-to-Market Drift
- `can_open_position()` guarantees `gross_exposure <= 1.0000x` *at the moment of order submission*.
- However, as soon as positions are open, price movements alter both the position notional and portfolio equity. The ledger has no active controller to detect or respond to post-entry exposure expansion.

### Gap 3: Long/Short Exposure Asymmetry Under Adverse Market Moves
- **Long Positions:** If the market drops 10%, notional falls from $100 to $90; equity falls from $100 to $90. Gross exposure remains:
  $$\text{Exposure}_{\text{Long}} = \frac{90}{90} = 1.0000x$$
- **Short Positions:** If the market rises 10%, notional rises from $100 to $110; equity falls from $100 to $90. Gross exposure explodes to:
  $$\text{Exposure}_{\text{Short}} = \frac{110}{90} = 1.2222x$$
  Under a 20% adverse spike, exposure reaches $1.5000x$. Without active risk control, short positions severely violate the 1.0x invariant.

### Gap 4: Absence of an Active Portfolio-Level MTM Risk Monitor
- `update_mark_to_market()` updates equity, but does not calculate or emit distinct portfolio-level metrics:
  - Open position notional vs reserved pending notional
  - Total committed exposure vs available capacity
  - Real-time exposure utilization percentage
  - Realized vs unrealized PnL decomposition

### Gap 5: Absence of a Deterministic Risk State Machine
- Currently, the ledger operates in a binary state: either active or `is_ruined` (equity <= $1.00).
- There are no intermediate operational states (`NORMAL`, `WARNING`, `REDUCE_ONLY`, `CRITICAL`, `HALTED`) with hysteresis to manage escalating portfolio risk.

### Gap 6: Absence of an Event-Driven Deleveraging / Position Reduction Policy
- If exposure expands above 1.0000x due to market movement, there is no policy to calculate excess notional and execute cost-aware partial or full position reductions.
- No comparison exists between deleveraging strategies (Largest Notional First, Highest Risk Contribution First, Lowest Closing Cost First).

### Gap 7: Multi-Position Equity Accounting Bug in `close_position()`
- In `close_position()` (Line 535), `self.equity = self.cash_balance` assumes all other positions have zero unrealized PnL. When 4 positions are open and 1 closes, the unrealized PnL of the other 3 is dropped from `self.equity` until the next explicit `update_mark_to_market()` call.

---

## 5. Architectural Mandates for Milestone 5.12.2.2

To close all seven gaps, Milestone 5.12.2.2 will implement two coordinated risk layers:

1. **Layer A — Pre-Trade Admission Protection:**
   - Eliminate inert configuration; wire a justified admission buffer into `can_open_position()`:
     $$\text{admission\_exposure\_cap} = \text{max\_gross\_exposure} - \text{safety\_buffer} = 1.0000 - 0.0050 = 0.995000x$$
   - Enforce this cap across all entry paths, pending orders, partial fills, and concurrent submissions.
2. **Layer B — Active Mark-to-Market Risk Control:**
   - Implement `ActiveMTMMonitor`: event-driven real-time tracking of committed exposure, equity, and capacity across long and short positions.
   - Implement `RiskStateMachine`: 6 deterministic states (`NORMAL`, `WARNING`, `REDUCE_ONLY`, `CRITICAL`, `HALTED`, `RUIN`) with anti-oscillation hysteresis.
   - Implement `DeleveragingEngine`: cost-aware position reduction with 3 deterministic selection policies, realistic transaction costs, minimum order size constraints, and failure logging (no fabricated liquidity).
   - Fix multi-position equity accounting in `close_position()`.
