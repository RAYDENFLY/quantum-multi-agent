# M5.12.2.2 Active Mark-to-Market (MTM) Monitor Design & Architecture

**Milestone:** M5.12.2.2 — Active MTM Risk Control & Admission Buffer Enforcement  
**Repository:** `d:/quantum-multi-agent`  
**Component:** `src/quantum/accounting/risk_controller.py`  
**Audit Date:** 2026-11-04  
**Classification:** Layer B Active Risk Control Design Specification  

---

## 1. Architectural Mission

Milestone 5.12.2.1 established that while static pre-trade admission controls protect against excessive order submission, they cannot prevent **post-trade mark-to-market exposure expansion** caused by market price fluctuations, funding charges, or cash deductions.

The [`ActiveMTMMonitor`](file:///d:/quantum-multi-agent/src/quantum/accounting/risk_controller.py#L74-L149) implements Layer B: active, event-driven monitoring of portfolio-level financial exposure.

---

## 2. Core Mathematical Definitions

### 2.1 Mark-to-Market Equity
Equity is continuously updated from cash balance and the sum of unrealized profit/loss across all active positions:

$$\text{Equity}_t = \text{Cash}_t + \sum_{i \in \text{OpenPositions}} \text{UnrealizedPnL}_{i,t}$$

Where for each position $i$:
- **Long Position:**
  $$\text{UnrealizedPnL}_{i,t} = Q_i \cdot \left(P_{i,t} - P_{i,\text{entry}}\right)$$
- **Short Position:**
  $$\text{UnrealizedPnL}_{i,t} = Q_i \cdot \left(P_{i,\text{entry}} - P_{i,t}\right)$$

### 2.2 Exposure Metrics Decomposition
The monitor maintains three distinct exposure metrics:

1. **Open-Position Gross Notional ($N_{\text{open}}$):**
   $$N_{\text{open},t} = \sum_{i \in \text{OpenPositions}} \left| Q_i \cdot P_{i,t} \right|$$
2. **Pending-Order Reserved Notional ($N_{\text{pending}}$):**
   $$N_{\text{pending},t} = \sum_{j \in \text{PendingOrders}} N_{\text{reserved},j}$$
   *(Pending reservations are tracked separately and deducted atomically upon fill or cancellation to prevent double-counting).*
3. **Total Committed Notional ($N_{\text{committed}}$):**
   $$N_{\text{committed},t} = N_{\text{open},t} + N_{\text{pending},t}$$

### 2.3 Gross Exposure & Capacity
- **Open Position Exposure:**
  $$\text{Exposure}_{\text{open},t} = \frac{N_{\text{open},t}}{\text{Equity}_t}$$
- **Total Committed Exposure:**
  $$\text{Exposure}_{\text{committed},t} = \frac{N_{\text{committed},t}}{\text{Equity}_t}$$
- **Exposure Capacity Utilization:**
  $$\text{Utilization}_t = \left(\frac{\text{Exposure}_{\text{committed},t}}{\text{HardMaxExposure}}\right) \times 100\%$$
- **Available Exposure Capacity:**
  $$\text{Capacity}_{\text{avail},t} = \max\left(0, \text{Equity}_t \cdot \text{AdmissionCap} - N_{\text{committed},t}\right)$$

---

## 3. Data Telemetry: `PortfolioMTMSnapshot`

Every evaluation produces an immutable [`PortfolioMTMSnapshot`](file:///d:/quantum-multi-agent/src/quantum/accounting/risk_controller.py#L53-L72) containing 15 discrete metrics:

```python
@dataclass
class PortfolioMTMSnapshot:
    timestamp_ms: int
    open_position_notional: float        # Total absolute notional of active positions
    pending_reserved_notional: float     # Total unexecuted reserved limit orders
    total_committed_notional: float      # open + pending
    cash_balance: float                  # Double-entry cash account balance
    unrealized_pnl: float                # Sum of unrealized PnL across positions
    realized_pnl: float                  # Cumulative closed trade PnL
    equity: float                        # Cash + unrealized PnL
    gross_exposure_open: float           # open_position_notional / equity
    gross_exposure_committed: float      # total_committed_notional / equity
    exposure_utilization_pct: float      # committed_exposure / hard_max * 100%
    available_exposure_capacity: float   # Max notional that can be opened
    risk_state: RiskState                # Current operational state
    open_position_count: int             # Number of active positions
    long_notional: float                 # Total notional in LONG positions
    short_notional: float                # Total notional in SHORT positions
```

---

## 4. Monitoring Triggers & Event Lifecycle

The monitor operates on an event-driven basis, evaluating exposure synchronously after:
1. **Market Price Tick / Bar Close:** Position notionals and unrealized PnL re-evaluated.
2. **Order Submission / Reservation:** Reserved notional added to committed exposure.
3. **Order Fill / Partial Fill:** Reserved notional converted into open position notional.
4. **Position Close / Partial Close:** Realized PnL credited to cash; notional removed.
5. **Fee Deduction:** Entry/exit fees subtracted from cash, reducing equity.
6. **Funding Accrual:** 8-hour perpetual funding payment/receipt credited/debited.
7. **Periodic Interface:** Provides a standard snapshot polling API for strategy orchestrators.

---

## 5. Long/Short Exposure Asymmetry Handling

The monitor explicitly tracks `long_notional` and `short_notional` separately.
Because short positions experience compounding exposure expansion during adverse moves (notional increases while equity falls), the monitor surfaces this asymmetry directly to the [`RiskStateMachine`](file:///d:/quantum-multi-agent/src/quantum/accounting/risk_controller.py#L151-L245) to prioritize short reductions during rallies.

**Status: COMPLETE & VERIFIED**
