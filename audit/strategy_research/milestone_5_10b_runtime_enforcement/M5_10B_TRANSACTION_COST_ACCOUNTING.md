# QUANTUM — MILESTONE 5.10B
## TRANSACTION COST ACCOUNTING, MICROSTRUCTURE DECOMPOSITION & NUMERICAL VERIFICATION

---

### 1. EXECUTIVE SUMMARY

- **Milestone Designation:** Milestone 5.10B (Execution Economics & Runtime Enforcement Verification)
- **Git Branch:** `research/quantum-next-3pct`
- **Location:** `audit/strategy_research/milestone_5_10b_runtime_enforcement/M5_10B_TRANSACTION_COST_ACCOUNTING.md`
- **Objective:** Establish, isolate, and test every individual cost component in perpetual futures execution to prevent double-counting, ensure exact notional scaling, and verify friction across $\$10$, $\$25$, and $\$100$ trade sizes under AsterDEX Base Retail pricing.
- **Key Principles Enforced:**
  1. **Strict Cost Separation:** Transaction friction is decomposed into eight distinct components: entry fee, exit fee, spread crossing, entry slippage, exit slippage, funding cash flow, partial-fill cost, and rejected/canceled order handling.
  2. **Zero Double-Counting:** Half-spread crossing ($1.0\text{ bps}$) is mathematically separated from orderbook depth slippage ($2.0\text{ bps}$). Passive maker orders pay zero spread and zero slippage.
  3. **Realized Notional Scaling:** Exit fee, exit spread, and exit slippage are levied strictly on executed exit notional ($N_{\text{exit}} = N_{\text{entry}} \times [1 + d \cdot R_{\text{gross}}]$), capturing the economic asymmetry between winning and losing trades.
  4. **Empirical Numerical Baseline:** Round-trip friction under AsterDEX Retail is verified at **`26.00 bps`** for Taker/Taker, **`8.00 bps`** for Maker/Maker, and **`17.00 bps`** for Maker-Entry/Taker-Exit.

---

### 2. DECOMPOSITION OF THE EIGHT SEPARATE COST COMPONENTS

```
+-------------------------------------------------------------------------------------------------------------------------------+
| THE EIGHT SEPARATE COST COMPONENTS IN QUANTUM EXECUTION                                                                        |
+-----+-----------------------+---------------------------------------+-----------------------------+---------------------------+
| ID  | Component             | Mathematical Definition               | Taker Execution Rate        | Maker Execution Rate      |
+-----+-----------------------+---------------------------------------+-----------------------------+---------------------------+
| C01 | Entry Exchange Fee    | N_entry * c_fee_entry                 | 10.0 bps (0.00100)          | 4.0 bps (0.00040)         |
| C02 | Exit Exchange Fee     | N_exit * c_fee_exit                   | 10.0 bps (0.00100)          | 4.0 bps (0.00040)         |
| C03 | Spread Crossing       | N * c_half_spread                     | 1.0 bps per leg (crossing)  | 0.0 bps (resting limit)   |
| C04 | Entry Slippage        | N_entry * c_slip_entry                | 2.0 bps (depth consumption) | 0.0 bps (limit fill)      |
| C05 | Exit Slippage         | N_exit * c_slip_exit                  | 2.0 bps (depth consumption) | 0.0 bps (limit fill)      |
| C06 | Funding Cash Flow     | -d * N_mark * r_funding               | Signed (+/-) per 8h settle  | Signed (+/-) per 8h settle|
| C07 | Partial-Fill Cost     | Fees/slip prorated to Q_exec * P      | Charged on Q_exec only      | Charged on Q_exec only    |
| C08 | Canceled / Rejected   | Zero executed notional                | $0.00 fee, $0.00 slippage   | $0.00 fee, $0.00 slippage |
+-----+-----------------------+---------------------------------------+-----------------------------+---------------------------+
```

#### Detailed Definitions:

1. **C01 — Entry Exchange Fee:** Direct cash fee charged by Aster DEX upon entry execution. Calculated as $\text{Notional}_{\text{entry}} \times c_{\text{fee, entry}}$. Under Base Retail: $10.0\text{ bps}$ for taker, $4.0\text{ bps}$ for maker.
2. **C02 — Exit Exchange Fee:** Direct cash fee charged upon closing the position. Calculated on realized exit notional: $\text{Notional}_{\text{exit}} \times c_{\text{fee, exit}}$.
3. **C03 — Spread Crossing:** The cost incurred by aggressive market/taker orders crossing from the mid-price to the best quote on the opposite side of the book. For a $2.0\text{ bps}$ top-of-book bid-ask spread, the half-spread cost is $1.0\text{ bps}$ per leg. Passive maker limit orders sit on the bid or ask, incurring strictly $0.0\text{ bps}$ spread cost.
4. **C04 — Entry Slippage:** Execution price degradation caused by orderbook depth consumption beyond top-of-book and network latency between signal generation and match engine execution. Modeled as $2.0\text{ bps}$ for aggressive taker orders. Resting maker orders fill at their limit price and experience $0.0\text{ bps}$ execution slippage.
5. **C05 — Exit Slippage:** Execution price degradation on market exit or stop-loss trigger. Modeled as $2.0\text{ bps}$ for aggressive exits.
6. **C06 — Funding Cash Flow:** The signed periodic settlement payment on perpetual contracts:
   $$\text{Funding Cash Flow} = - d \cdot N_{\text{mark}} \cdot r_{\text{funding}}$$
   where $d = +1$ for Long, $-1$ for Short. When funding rate $> 0$, Long pays (negative cash flow), Short receives (positive cash flow).
7. **C07 — Partial-Fill Cost Accounting:** When a limit or IOC order of size $Q_{\text{req}}$ achieves only partial execution $Q_{\text{exec}} < Q_{\text{req}}$, transaction fees, spread, and slippage apply strictly to $Q_{\text{exec}} \times P$. The unfilled quantity $Q_{\text{req}} - Q_{\text{exec}}$ expires or is canceled with $\$0.00$ fee.
8. **C08 — Rejected and Canceled Orders:** Orders that are rejected by margin filters or post-only limit orders canceled due to crossing the book incur strictly $\$0.00$ fee and $\$0.00$ slippage.

---

### 3. VERIFICATION OF ZERO DOUBLE-COUNTING

A critical flaw in naive backtesting systems is confounding spread crossing with execution slippage, either double-counting them or ignoring one entirely. We verify non-redundancy through the mid-price microstructure model:

```
+-----------------------------------------------------------------------------------------------------+
| MICROSTRUCTURE PRICE LADDER & EXECUTION SEPARATION                                                  |
+-----------------------------------------------------------------------------------------------------+
|                                                                                                     |
|   Ask Depth Walk (Slippage = +2.0 bps)      ======> P_fill_taker = P_mid * (1 + 0.0001 + 0.0002)    |
|   Best Ask (Top-of-Book = +1.0 bps)         ======> P_ask = P_mid * (1 + 0.0001)                    |
|                                                                                                     |
|   MID-PRICE REFERENCE (P_mid)               ======> Pure benchmark reference price (0.0 bps)        |
|                                                                                                     |
|   Best Bid (Top-of-Book = -1.0 bps)         ======> P_bid = P_mid * (1 - 0.0001)                    |
|   Bid Depth Walk (Slippage = -2.0 bps)      ======> P_fill_taker = P_mid * (1 - 0.0001 - 0.0002)    |
|                                                                                                     |
+-----------------------------------------------------------------------------------------------------+
```

#### Mathematical Proof of Independence:
- **Component 1 (Spread Crossing):** $c_{\text{half-spread}} = \frac{P_{\text{ask}} - P_{\text{mid}}}{P_{\text{mid}}} = 1.0\text{ bps}$. This is the structural gap between the mid-price and the inside market.
- **Component 2 (Depth Slippage):** $c_{\text{slip}} = \frac{P_{\text{fill}} - P_{\text{ask}}}{P_{\text{mid}}} = 2.0\text{ bps}$. This is the volume-weighted average price (VWAP) impact of walking into orderbook depth levels.
- **Combined Impact for Taker:** $\Delta P / P_{\text{mid}} = c_{\text{half-spread}} + c_{\text{slip}} = 1.0\text{ bps} + 2.0\text{ bps} = 3.0\text{ bps}$ per leg ($6.0\text{ bps}$ round trip).
- **Exchange Cash Fee:** Assessed on the final fill price at $10.0\text{ bps}$ per leg ($20.0\text{ bps}$ round trip).
- **Total Round-Trip Taker Friction:** $20.0\text{ bps (fees)} + 2.0\text{ bps (spread)} + 4.0\text{ bps (slippage)} = \mathbf{26.00\text{ bps}}$ ($0.260\%$).
- If an engine applied $2.0\text{ bps}$ full spread + $2.0\text{ bps}$ slippage + $1.0\text{ bps}$ half-spread, that would be double-counting. Our architecture isolates each term cleanly without overlap.

---

### 4. COMPREHENSIVE NUMERICAL EXAMPLES ($10, $25, AND $100 NOTIONAL)

Below are the exact accounting ledgers computed by [`scripts/audit_milestone_5_10b_verification.py`](file:///d:/quantum-multi-agent/scripts/audit_milestone_5_10b_verification.py) for round-trip trades.

#### 4.1 Scenario A: Flat Price ($0\%$ Price Movement, $N_{\text{exit}} = N_{\text{entry}}$)

```
+---------------------------------------------------------------------------------------------------------------------------------------+
| NUMERICAL VERIFICATION: SCENARIO A (FLAT PRICE, 0% GROSS RETURN)                                                                      |
+---------+-----------------------+-----------+----------+-----------+------------+-------------+--------------+--------------+---------+
| Notional| Execution Mode        | Entry Fee | Exit Fee | Total Fee | Total Sprd | Entry Slip  | Exit Slip    | Total Frict. | Frict.  |
| (USD)   |                       | ($)       | ($)      | ($)       | ($)        | ($)         | ($)          | ($)          | (bps)   |
+---------+-----------------------+-----------+----------+-----------+------------+-------------+--------------+--------------+---------+
| $10.00  | Taker/Taker           | $0.010000 | $0.010000| $0.020000 | $0.002000  | $0.002000   | $0.002000    | $0.026000    | 26.00   |
| $10.00  | Maker/Maker           | $0.004000 | $0.004000| $0.008000 | $0.000000  | $0.000000   | $0.000000    | $0.008000    | 8.00    |
| $10.00  | Maker_Entry/Taker_Exit| $0.004000 | $0.010000| $0.014000 | $0.001000  | $0.000000   | $0.002000    | $0.017000    | 17.00   |
|         |                       |           |          |           |            |             |              |              |         |
| $25.00  | Taker/Taker           | $0.025000 | $0.025000| $0.050000 | $0.005000  | $0.005000   | $0.005000    | $0.065000    | 26.00   |
| $25.00  | Maker/Maker           | $0.010000 | $0.010000| $0.020000 | $0.000000  | $0.000000   | $0.000000    | $0.020000    | 8.00    |
| $25.00  | Maker_Entry/Taker_Exit| $0.010000 | $0.025000| $0.035000 | $0.002500  | $0.000000   | $0.005000    | $0.042500    | 17.00   |
|         |                       |           |          |           |            |             |              |              |         |
| $100.00 | Taker/Taker           | $0.100000 | $0.100000| $0.200000 | $0.020000  | $0.020000   | $0.020000    | $0.260000    | 26.00   |
| $100.00 | Maker/Maker           | $0.040000 | $0.040000| $0.080000 | $0.000000  | $0.000000   | $0.000000    | $0.080000    | 8.00    |
| $100.00 | Maker_Entry/Taker_Exit| $0.040000 | $0.100000| $0.140000 | $0.010000  | $0.000000   | $0.020000    | $0.170000    | 17.00   |
+---------+-----------------------+-----------+----------+-----------+------------+-------------+--------------+--------------+---------+
```

---

#### 4.2 Scenario B: Price Gain ($+1.0\%$ Price Movement, $N_{\text{exit}} = 1.01 \times N_{\text{entry}}$)

On a profitable trade, exit notional increases by $+1.0\%$, increasing the exit fee, exit spread, and exit slippage proportionally:

```
+---------------------------------------------------------------------------------------------------------------------------------------+
| NUMERICAL VERIFICATION: SCENARIO B (GAIN +1.0%, EXIT NOTIONAL = 1.01 * ENTRY NOTIONAL)                                               |
+---------+-----------------------+-----------+----------+-----------+------------+-------------+--------------+--------------+---------+
| Notional| Execution Mode        | Entry Fee | Exit Fee | Total Fee | Total Sprd | Entry Slip  | Exit Slip    | Total Frict. | Frict.  |
| (USD)   |                       | ($)       | ($)      | ($)       | ($)        | ($)         | ($)          | ($)          | (bps)   |
+---------+-----------------------+-----------+----------+-----------+------------+-------------+--------------+--------------+---------+
| $10.00  | Taker/Taker           | $0.010000 | $0.010100| $0.020100 | $0.002010  | $0.002000   | $0.002020    | $0.026130    | 26.13   |
| $10.00  | Maker/Maker           | $0.004000 | $0.004040| $0.008040 | $0.000000  | $0.000000   | $0.000000    | $0.008040    | 8.04    |
| $10.00  | Maker_Entry/Taker_Exit| $0.004000 | $0.010100| $0.014100 | $0.001010  | $0.000000   | $0.002020    | $0.017130    | 17.13   |
|         |                       |           |          |           |            |             |              |              |         |
| $25.00  | Taker/Taker           | $0.025000 | $0.025250| $0.050250 | $0.005025  | $0.005000   | $0.005050    | $0.065325    | 26.13   |
| $25.00  | Maker/Maker           | $0.010000 | $0.010100| $0.020100 | $0.000000  | $0.000000   | $0.000000    | $0.020100    | 8.04    |
| $25.00  | Maker_Entry/Taker_Exit| $0.010000 | $0.025250| $0.035250 | $0.002525  | $0.000000   | $0.005050    | $0.042825    | 17.13   |
|         |                       |           |          |           |            |             |              |              |         |
| $100.00 | Taker/Taker           | $0.100000 | $0.101000| $0.201000 | $0.020100  | $0.020000   | $0.020200    | $0.261300    | 26.13   |
| $100.00 | Maker/Maker           | $0.040000 | $0.040400| $0.080400 | $0.000000  | $0.000000   | $0.000000    | $0.080400    | 8.04    |
| $100.00 | Maker_Entry/Taker_Exit| $0.040000 | $0.101000| $0.141000 | $0.010100  | $0.000000   | $0.020200    | $0.171300    | 17.13   |
+---------+-----------------------+-----------+----------+-----------+------------+-------------+--------------+--------------+---------+
```

---

#### 4.3 Scenario C: Price Loss ($-1.0\%$ Price Movement, $N_{\text{exit}} = 0.99 \times N_{\text{entry}}$)

On a losing trade, exit notional decreases by $-1.0\%$, reducing the exit fee and exit slippage:

```
+---------------------------------------------------------------------------------------------------------------------------------------+
| NUMERICAL VERIFICATION: SCENARIO C (LOSS -1.0%, EXIT NOTIONAL = 0.99 * ENTRY NOTIONAL)                                               |
+---------+-----------------------+-----------+----------+-----------+------------+-------------+--------------+--------------+---------+
| Notional| Execution Mode        | Entry Fee | Exit Fee | Total Fee | Total Sprd | Entry Slip  | Exit Slip    | Total Frict. | Frict.  |
| (USD)   |                       | ($)       | ($)      | ($)       | ($)        | ($)         | ($)          | ($)          | (bps)   |
+---------+-----------------------+-----------+----------+-----------+------------+-------------+--------------+--------------+---------+
| $10.00  | Taker/Taker           | $0.010000 | $0.009900| $0.019900 | $0.001990  | $0.002000   | $0.001980    | $0.025870    | 25.87   |
| $10.00  | Maker/Maker           | $0.004000 | $0.003960| $0.007960 | $0.000000  | $0.000000   | $0.000000    | $0.007960    | 7.96    |
| $10.00  | Maker_Entry/Taker_Exit| $0.004000 | $0.009900| $0.013900 | $0.000990  | $0.000000   | $0.001980    | $0.016870    | 16.87   |
|         |                       |           |          |           |            |             |              |              |         |
| $25.00  | Taker/Taker           | $0.025000 | $0.024750| $0.049750 | $0.004975  | $0.005000   | $0.004950    | $0.064675    | 25.87   |
| $25.00  | Maker/Maker           | $0.010000 | $0.009900| $0.019900 | $0.000000  | $0.000000   | $0.000000    | $0.019900    | 7.96    |
| $25.00  | Maker_Entry/Taker_Exit| $0.010000 | $0.024750| $0.034750 | $0.002475  | $0.000000   | $0.004950    | $0.042175    | 16.87   |
|         |                       |           |          |           |            |             |              |              |         |
| $100.00 | Taker/Taker           | $0.100000 | $0.099000| $0.199000 | $0.019900  | $0.020000   | $0.019800    | $0.258700    | 25.87   |
| $100.00 | Maker/Maker           | $0.040000 | $0.039600| $0.079600 | $0.000000  | $0.000000   | $0.000000    | $0.079600    | 7.96    |
| $100.00 | Maker_Entry/Taker_Exit| $0.040000 | $0.099000| $0.139000 | $0.009900  | $0.000000   | $0.019800    | $0.168700    | 16.87   |
+---------+-----------------------+-----------+----------+-----------+------------+-------------+--------------+--------------+---------+
```

---

### 5. PARTIAL FILL AND ORDER LIFECYCLE RECONCILIATION

The accounting engine handles partial fills and cancellations via [`PartialCloseResult`](file:///d:/quantum-multi-agent/src/quantum/backtesting/accounting.py#L125-L137):
1. **Partial Fills:** If an entry order is submitted for $100.0\text{ USDT}$ notional ($1.0\text{ ETH}$ @ $\$100$) but only $40.0\text{ USDT}$ ($0.4\text{ ETH}$) executes before the remaining quantity is canceled:
   - Executed Entry Fee (Taker): $\$40.00 \times 0.0010 = \$0.0400$
   - Executed Entry Spread: $\$40.00 \times 0.0001 = \$0.0040$
   - Executed Entry Slippage: $\$40.00 \times 0.0002 = \$0.0080$
   - Total Friction on Execution: $\$0.0520$ ($13.0\text{ bps}$ of $\$40$)
   - Unexecuted $\$60.00$ notional incurs strictly $\$0.00$ fee and $\$0.00$ slippage.
2. **Order Rejection:** If an order breaches margin, lot size, or risk limits, the match engine rejects it before execution. Friction is strictly $\$0.00$.

---

### 6. CONCLUSION & PLATFORM FIDELITY

By decoupling all eight cost drivers, enforcing non-redundant spread vs slippage mechanics, and capturing dynamic exit notional scaling, QUANTUM eliminates both frictional undercounting and double-counting bias. Future alpha candidates evaluated on this engine face mathematically sound, exchange-accurate economic friction.
