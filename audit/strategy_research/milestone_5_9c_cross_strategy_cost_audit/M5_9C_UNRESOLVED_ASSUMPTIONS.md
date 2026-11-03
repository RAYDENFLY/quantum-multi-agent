# QUANTUM - MILESTONE 5.9C
## REGISTER OF UNRESOLVED ASSUMPTIONS & MICROSTRUCTURE LIMITATIONS

---

### 1. Document Overview
- **Document Identifier:** `audit/strategy_research/milestone_5_9c_cross_strategy_cost_audit/M5_9C_UNRESOLVED_ASSUMPTIONS.md`
- **Research Branch:** `research/quantum-next-3pct`
- **Scope:** Exhaustive catalog of unverified assumptions, missing empirical datasets, and operational microstructure limitations identified during the cross-strategy cost audit.
- **Audited Milestones:** M3, M4, M5.2, M5.4, M5.5, M5.6, M5.7, M5.8A, M5.8B, M5.9, M5.9B.

---

### 2. Catalog of Unresolved Assumptions

```
+----------------------------------------------------------------------------------------------------+
| ID     | Assumption Category       | Historical Impact | Severity | Resolution Status              |
+----------------------------------------------------------------------------------------------------+
| UNR-01 | Historical Funding Rates  | M3 - M5.9B        | HIGH     | DATA_UNAVAILABLE (Zero-Deducted) |
| UNR-02 | Limit Order Fill Latency  | M5.5 (EXP-10A)    | CRITICAL | DISQUALIFIED (Lookahead Flaw)  |
| UNR-03 | L2 Orderbook Queue Depth  | M3, M5.4, M5.5    | MEDIUM   | ESTIMATED (Static Half-Spread) |
| UNR-04 | Volume-Tier Fee Upgrades  | M3, M5.5          | HIGH     | DISALLOWED (Retail VIP0 Enforced)|
| UNR-05 | Market Impact Non-Linear  | M5.2 (Compounding)| HIGH     | UNREPRESENTED (Ignored in M5.2)|
| UNR-06 | Emergency Liquidation Fee | M5.6, M5.8A       | MEDIUM   | UNMODELED (Account Starved First)|
| UNR-07 | Network & Clock Jitter    | M5.5, M5.6        | MEDIUM   | APPROXIMATED (1-bar next open) |
+----------------------------------------------------------------------------------------------------+
```

---

### 3. Detailed Audit of Each Unresolved Assumption

#### UNR-01: Historical Funding Rate Dataset Absence
- **Description:** USDT Perpetual contracts incur an 8-hour funding cash flow ($t \in \{00:00, 08:00, 16:00\text{ UTC}\}$). In historical backtests, funding cash flows were either modeled parametrically as a fixed $1.0\text{ bps}/8\text{h}$ drag or omitted entirely ($0.00\text{ bps}$).
- **Audit Reality:** The SQLite/Parquet database contains zero rows in `funding_events` or historical funding rate archives for AsterDEX or Bybit before late 2025.
- **Classification:** `FUNDING_DATA_UNAVAILABLE`.
- **Impact on Alpha:**
  - For short-duration scalping ($< 1\text{ hour}$ holding period), funding impact is negligible because trades rarely cross an 8h settlement boundary ($< 5\%$ of trades).
  - For medium-horizon strategies (e.g., Track C pairs held 5–6 days), funding can accumulate to $15–30\text{ bps}$ per leg. If funding was systematically adverse, Track C losses would be even worse than reported. Funding omission therefore acts as an optimistic bias for Track C, reinforcing its rejection.

#### UNR-02: Limit Order Queue Priority & Passive Fill Simulation
- **Description:** Milestone 5.5 (EXP-10A) assumed that a post-only limit order placed at the inside bid/ask executes with a $75\%$ fill probability whenever intra-bar low/high penetrates the limit price by $0.5\sigma$.
- **Audit Reality:** In live high-frequency markets, being touched by the trade stream does not guarantee execution. Resting orders join the back of the price queue. Large informed orders sweep the book, filling limit orders only when price is about to blow through them (adverse selection), while unfilled orders occur when price reverses immediately (missed alpha).
- **Classification:** `CONTAMINATED_SIMULATION_MODEL`.
- **Remediation in M5.6/M5.8A:** Proved that causal point-in-time next-bar open execution causes EXP-10A returns to collapse from $+1.8640\%$ to $-0.1449\%$. No passive maker strategy may be qualified without tick-level orderbook queue replay.

#### UNR-03: Static Spread & Depth Slippage vs Dynamic Orderbook Liquidity
- **Description:** Historical milestones applied static spread ($2.0\text{ bps}$) and static slippage ($1.5–2.0\text{ bps}$) regardless of trade size, time of day, volatility regime, or market liquidity state.
- **Audit Reality:** During market distress (e.g. regime transitions, news spikes, weekend illiquidity), top-of-book bid-ask spreads frequently widen from $2.0\text{ bps}$ to $15–50\text{ bps}$, and book depth collapses.
- **Classification:** `STATIC_APPROXIMATION_OPTIMISM`.
- **Impact on Alpha:** Directional momentum stop-losses occurred predominantly during volatile breakdowns. Using a static $1.5\text{ bps}$ slippage understated the true slippage incurred during emergency stop-outs. Under real execution, net losses would be higher.

#### UNR-04: Institutional Fee Tier Upgrades on Micro-Capital Accounts
- **Description:** Early milestones (M3 and initial drafts of M5.5) referenced Bybit VIP1/PRO tiers (e.g. $1.8\text{ bps}$ maker / $4.0\text{ bps}$ taker) or institutional volume tiers to demonstrate strategy viability.
- **Audit Reality:** Bybit VIP1 requires $\ge \$50,000$ asset balance or $\ge \$10,000,000$ 30-day trading volume. On an unlevered $\$100.00$ initial capital allocation, achieving $\$10M$ monthly volume is mathematically impossible without exceeding maximum leverage caps.
- **Classification:** `PROHIBITED_UNREALISTIC_BENCHMARK`.
- **Governance Rule:** All QUANTUM research must be benchmarked strictly against retail unprivileged tiers: `BYBIT_VIP0_DEFAULT` ($2.0\text{ bps}$ maker, $5.5\text{ bps}$ taker) and `ASTER_RETAIL_CORE` ($4.0\text{ bps}$ maker, $10.0\text{ bps}$ taker).

#### UNR-05: Unconstrained Compounding & Ignored Market Capacity
- **Description:** Milestone 5.2 reported astronomical portfolio returns (terminal equity in the billions of dollars) by reinvesting $100\%$ of compounded equity into single trades.
- **Audit Reality:** An order exceeding $\$100,000$ in altcoins experiences substantial market impact; an order of $\$10,000,000$ would completely exhaust available depth.
- **Classification:** `DISQUALIFIED_COMPOUNDING_ARTIFACT`.
- **Remediation:** Enforced strict $1.0\text{x}$ unlevered gross exposure with $w_{\text{max}} = 0.25$ cap, normalizing all evaluations to non-compounded realistic capital capacity.

#### UNR-06: Maintenance Margin & Emergency Liquidation Penalties
- **Description:** The backtest engine halts trading when equity reaches the starvation threshold ($\text{Equity} < \$20$ for $w_{\text{max}}=0.25$), assuming all positions can be closed at reference price plus standard taker fee.
- **Audit Reality:** If an exchange triggers an automatic forced liquidation, exchanges levy an additional liquidation penalty fee (typically $1.0\%–2.0\%$ of notional) and liquidate positions via aggressive market orders.
- **Classification:** `CONSERVATIVELY_ABSENT`.
- **Verdict:** Because the strategies were strictly unlevered ($\Lambda \le 1.0\text{x}$), maintenance margin liquidation was not triggered by leverage; rather, positions were closed normally before cash exhaustion.

#### UNR-07: Network Transmission & Simulated Clock Jitter
- **Description:** Causal execution assumes signals generated at bar close $t_i$ are filled at the opening tick of bar $t_{i+1}$ (simulated clock step).
- **Audit Reality:** Live WebSocket and REST transmission introduces 20–150ms of network latency. In volatile markets, the execution fill may deviate from the recorded opening price.
- **Classification:** `ACCEPTABLE_LATENCY_APPROXIMATION`.
- **Verdict:** 1-bar causal latency provides an adequate macro-protection against lookahead bias, but live deployment would require telemetry latency buffering.

---

### 4. Summary Governance Directives
1. **Never adjust research targets:** No unverified assumption shall be relaxed to make a failing strategy appear passing.
2. **Retail tier mandate:** All future alpha discovery must prove profitability under retail unprivileged fee schedules (`BYBIT_VIP0_DEFAULT`).
3. **Paper trading remains prohibited:** Until an alpha strategy demonstrates $> 3.00\%$ net mean daily return under causal execution with full friction, paper trading authorization is strictly denied.
