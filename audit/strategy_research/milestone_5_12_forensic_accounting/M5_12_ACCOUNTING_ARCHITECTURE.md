# QUANTUM — MILESTONE 5.12
## EVENT-DRIVEN PORTFOLIO ACCOUNTING & EXPOSURE ARCHITECTURE

---

### 1. COMPLETE EXECUTION PIPELINE TRACE (A1)

The complete lifecycle of a trading episode is traced below, mapping every transformation from signal trigger to final portfolio balance update:

```
[Market Bar t Close]
         │
         ▼
 1. SIGNAL GENERATION (Hypothesis Engine / Analyst Agent)
    • Evaluates causal multi-factor indicator conditions at bar t.
    • Emits Signal: Direction (+1 Long / -1 Short), Target Price, Stop Price, Hypothesis ID.
    • Authoritative Source: src/quantum/strategies/hypothesis_engine.py
         │
         ▼
 2. RISK VALIDATION & CONCURRENCY CHECK (Risk Agent)
    • Checks portfolio state: Is account ruined (Equity <= $1.00)?
    • Checks active symbols: Is symbol already open in portfolio?
    • Checks concurrency: Count(open_positions) < max_concurrent_positions (4).
    • Authoritative Source: EventDrivenPortfolioLedger.can_open_position()
         │
         ▼
 3. DYNAMIC POSITION SIZING (Banker Agent)
    • Computes permissible notional:
      Allocated Notional = min(Desired Notional, Current Equity * Symbol Weight, Available Unlevered Exposure)
    • Asserts post-trade gross exposure: (Current Open Notional + Allocated Notional) / Current Equity <= 1.0000x.
    • Authoritative Source: EventDrivenPortfolioLedger.can_open_position()
         │
         ▼
 4. ORDER GENERATION (Sniper Agent)
    • Emits causal entry order for execution strictly at bar t+1 open.
    • Authoritative Source: EventDrivenPortfolioLedger.open_position()
         │
         ▼
 5. EXECUTION & FILL (Execution Economics Engine)
    • Determines Fill Price: Reference Price adjusted for half-spread and slippage (Taker) or limit touch (Maker).
    • Slices Quantity: Q = Allocated Notional / Fill Price.
    • Authoritative Source: ExecutionEconomicsEngine.evaluate_episode()
         │
         ▼
 6. TRANSACTION COST & CASH DEDUCTION (Banker Agent)
    • Calculates Entry Fee = Notional * (Fee Rate / 10,000).
    • Calculates Entry Spread = Notional * (Half Spread / 10,000).
    • Calculates Entry Slippage = Notional * (Slippage / 10,000).
    • Double-Entry Cash Update: Cash Balance -= (Fee + Spread + Slippage).
    • Authoritative Source: EventDrivenPortfolioLedger.open_position()
         │
         ▼
 7. INTRADAY MARK-TO-MARKET & MONITORING (Risk Agent)
    • Every bar, marks open positions: Unrealized PnL = Q * (P_current - P_entry) [Long].
    • Portfolio Equity = Cash Balance + sum(Unrealized PnL).
    • Checks Ruin: If Equity <= $1.00, trigger CAPITAL_EXHAUSTION_HALT and halt all trading.
    • Authoritative Source: EventDrivenPortfolioLedger.update_mark_to_market()
         │
         ▼
 8. POSITION EXIT & REALIZED PNL (Sniper Agent)
    • Signal Reversal, Stop Loss Hit, Take Profit Hit, or 240m Time Exit.
    • Exit Fill Price = Exit Price adjusted for half-spread and slippage.
    • Gross Realized PnL = Q * (Exit Price - Entry Price) [Long].
    • Exit Costs = Exit Notional * (Fee + Spread + Slippage).
    • Net Realized PnL = Gross Realized PnL - Exit Costs.
    • Authoritative Source: EventDrivenPortfolioLedger.close_position()
         │
         ▼
 9. FINAL PORTFOLIO BALANCE UPDATE (Banker Agent)
    • Cash Balance += Net Realized PnL.
    • Equity = Cash Balance + remaining open positions marked-to-market.
    • Records discrete event into immutable ledger.
    • Authoritative Source: EventDrivenPortfolioLedger._record_event()
```

---

### 2. THE 1.0X GROSS EXPOSURE INVARIANT (A2)

The fundamental portfolio exposure equation is strictly enforced at every discrete event:

$$\text{Gross Exposure}_t = \frac{\sum_{i=1}^{M} |\text{Notional}_{i,t}|}{\text{Equity}_t} \le 1.0000$$

Where:
- $\text{Notional}_{i,t} = Q_i \times P_{i,t}$ is the marked-to-market gross notional of position $i$.
- $\text{Equity}_t = \text{Cash Balance}_t + \sum_{i=1}^{M} \text{Unrealized PnL}_{i,t}$.
- $M \le 4$ is the maximum number of concurrent open positions.

#### Enforcement Rules:
1. **Dynamic Scaling:** Position sizing scales with *current available equity*, not initial equity. If equity drops from $\$100$ to $\$50$, the maximum permissible position notional automatically scales down from $\$25$ to $\$12.50$.
2. **Pre-Trade Gate:** If adding a candidate position would cause $\text{Gross Exposure} > 1.0000x$, the order is rejected immediately with an `EXPOSURE_BREACH` event.
3. **No Duplicate Allocation:** Capital allocated to an open position is deducted from available buying power. No strategy or asset can allocate the same dollar twice.

---

### 3. EVENT-DRIVEN ACCOUNTING LEDGER SPECIFICATION (A3)

Every transaction records the following 19 authoritative fields in [`EventDrivenPortfolioLedger`](file:///d:/quantum-multi-agent/src/quantum/accounting/event_ledger.py):

| Field Index | Field Name | Data Type | Description |
| :--- | :--- | :--- | :--- |
| 1 | `event_id` | String | Sequential unique event identifier (`EVT-000001`) |
| 2 | `trade_id` | String | Position lifecycle identifier (`TRD-00001`) |
| 3 | `symbol` | String | Canonical trading instrument (`BTCUSDT`) |
| 4 | `timestamp_ms` | Integer | Epoch millisecond timestamp of the execution event |
| 5 | `event_type` | Enum | Classification (`POSITION_OPENED`, `STOP_LOSS_HIT`, etc.) |
| 6 | `side` | String | Direction (`LONG`, `SHORT`) |
| 7 | `quantity` | Float | Base asset units transacted |
| 8 | `reference_price` | Float | Nominal market price prior to friction |
| 9 | `fill_price` | Float | Actual executed fill price including slippage/spread |
| 10 | `notional` | Float | USD value of the executed fill ($Q \times P_{\text{fill}}$) |
| 11 | `fee` | Float | Exchange fee deducted in USD |
| 12 | `spread_cost` | Float | Half-spread crossing penalty deducted in USD |
| 13 | `slippage_cost` | Float | Execution slippage cost deducted in USD |
| 14 | `funding_cost` | Float | Cash settlement for periodic 8h funding rate |
| 15 | `realized_pnl` | Float | Gross realized PnL on position liquidation |
| 16 | `unrealized_pnl` | Float | Marked-to-market unrealized profit/loss |
| 17 | `cash_balance` | Float | Settled cash balance in portfolio |
| 18 | `equity` | Float | Total net liquidating portfolio value ($\text{Cash} + \text{MTM}$) |
| 19 | `gross_exposure` | Float | Portfolio gross exposure ratio ($\le 1.0000$) |

---

### 4. THE 10 ACCOUNTING INVARIANTS & VERIFICATION PROOFS

```
+---------------------------------------------------------------------------------------------------------------+
| THE 10 MANDATORY ACCOUNTING INVARIANTS                                                                        |
+-----+---------------------------------------------+-----------------------------------------------------------+
| Num | Invariant Description                       | Mathematical Proof / Verification Mechanism               |
+-----+---------------------------------------------+-----------------------------------------------------------+
| 1   | Every fill has a corresponding update       | Position state created on entry, deleted on full exit.    |
| 2   | Every fee is charged exactly once           | Fee deducted on entry event, exit fee on exit event only. |
| 3   | Partial fills accounted for independently   | Scaled quantity logged with PARTIAL_FILL tag.             |
| 4   | Partial exits reduce quantity correctly     | Pos.quantity -= close_qty; remainder remains open.        |
| 5   | Realized PnL reconciles with cash flows     | Cash_post = Cash_pre + Realized_Gross - Total_Exit_Cost.  |
| 6   | Unrealized PnL uses causal market prices    | MTM uses bar t Close; zero forward bar contamination.     |
| 7   | Equity reconciles with Cash + MTM           | Equity = Cash + sum(Unrealized PnL) holds at every event. |
| 8   | Closed positions have zero remaining qty    | Position key deleted from dictionary upon full exit.      |
| 9   | No trade can be counted twice               | Trade ID uniqueness verified; duplicate entries rejected. |
| 10  | Portfolio PnL = sum of asset PnLs           | Portfolio PnL reconciles exactly to sum of closed trades. |
+-----+---------------------------------------------+-----------------------------------------------------------+
```
