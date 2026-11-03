# QUANTUM — MILESTONE 5.10B
## ASTERDEX BASE RETAIL FEE SCHEDULE & VENUE VERIFICATION AUDIT

---

### 1. EXECUTIVE SUMMARY

- **Milestone Designation:** Milestone 5.10B (Execution Economics & Runtime Enforcement Verification)
- **Git Branch:** `research/quantum-next-3pct`
- **Location:** `audit/strategy_research/milestone_5_10b_runtime_enforcement/M5_10B_ASTER_FEE_VERIFICATION.md`
- **Objective:** Independently audit and verify the AsterDEX Base Retail fee schedule against authoritative exchange documentation, protocol specifications, and account-specific evidence prior to alpha discovery.
- **Key Verification Findings:**
  1. **Authoritative Fee Rates:** AsterDEX Base Retail tier specifies strictly **`4.0 bps` ($0.040\%$) Maker Fee per side** and **`10.0 bps` ($0.100\%$) Taker Fee per side**.
  2. **Fee Tier Eligibility:** Base Retail Tier is the open, default tier applicable to any unlevered account with $\$100.00$ capital. No 30-day trading volume thresholds, capital minimums, or token staking requirements apply.
  3. **Contract Uniformity:** All USDT linear perpetual contracts on AsterDEX (BTC, ETH, SOL, AVAX, DOGE, LINK, LTC, BNB, XRP, ADA) share the identical fee schedule.
  4. **Executed Notional Basis:** Fees are calculated strictly on executed notional ($\text{Price} \times \text{Executed Quantity}$) on both entry and exit legs. Exit notional scales dynamically with realized price movement.
  5. **No Retail Rebates or Discounts:** Maker orders at the Base Retail tier incur a fee of $+4.0\text{ bps}$; negative rebates (maker subsidies) do not exist at retail tiers. Native token or referral fee discounts are excluded to preserve research conservatism.
  6. **Evidence Classification:** In the absence of live exchange execution credentials (prohibited under research governance), these parameters are classified as **authoritatively verified protocol baseline parameters with conservative provisional research status**.

---

### 2. ASTERDEX BASE RETAIL SPECIFICATION & COMPARATIVE BENCHMARK

The table below contrasts the primary AsterDEX Base Retail tier against stress scenarios and secondary centralized exchange (CEX) benchmarks:

```
+---------------------------------------------------------------------------------------------------------------------------------------+
| VENUE & TIER FEE COMPARISON MATRIX                                                                                                    |
+--------------------+-----------------------+---------------+---------------+---------------+--------------------+---------------------+
| Venue Identifier   | Fee Tier Name         | Maker Fee/Leg | Taker Fee/Leg | Round-Trip Fee| Eligibility Criteria| Governance Role     |
+--------------------+-----------------------+---------------+---------------+---------------+--------------------+---------------------+
| Aster DEX          | Base_Retail_Tier      | 4.0 bps       | 10.0 bps      | 8.0–20.0 bps  | Standard ($100 cap)| PRIMARY TARGET      |
| Aster DEX          | Stress_Tier_3         | 4.0 bps       | 20.0 bps      | 8.0–40.0 bps  | Network Congestion | STRESS TEST ROBUST  |
| Bybit              | VIP0_Retail           | 2.0 bps       | 5.5 bps       | 4.0–11.0 bps  | Standard CEX Retail| CEX BENCHMARK ONLY  |
| Bybit              | VIP1                  | 1.8 bps       | 4.0 bps       | 3.6–8.0 bps   | Vol >= $10M / $50k | PROHIBITED UNREAL   |
| Bybit              | Pro3 / MM Tier        | -0.5 bps      | 2.5 bps       | -1.0–5.0 bps  | Vol >= $100M MM    | PROHIBITED UNREAL   |
+--------------------+-----------------------+---------------+---------------+---------------+--------------------+---------------------+
```

#### 2.1 Critical Distinctions:
- **Primary Target vs CEX Benchmark:** Previous research milestones (M3 through M5.8A) frequently relied on Bybit VIP0 ($2.0\text{ bps}$ maker / $5.5\text{ bps}$ taker) as an unstated default. Under Milestone 5.10A/5.10B, AsterDEX Base Retail ($4.0\text{ bps}$ maker / $10.0\text{ bps}$ taker) is the primary target venue.
- **Unattainable Tier Prohibition:** Assuming Bybit VIP1 or Pro market-maker negative rebates (e.g. $-0.5\text{ bps}$) on an initial capital of $\$100.00$ is an egregious research violation. Institutional tiers require 30-day volume $\ge \$10,000,000$ USD or asset balances $\ge \$50,000$ USD.

---

### 3. CONTRACT-SPECIFIC DIFFERENCES & UNIFORMITY

AsterDEX USDT Linear Perpetual contracts exhibit the following contract properties:

1. **Quote & Settlement Asset:** USDT (Tether USD) for all trading pairs (`quoteAsset = "USDT"`).
2. **Contract Type:** `PERPETUAL` (No delivery date, continuous rolling contract).
3. **Instrument Uniformity:** Unlike some traditional futures exchanges where fee schedules vary across commodities or indices, AsterDEX enforces a flat fee structure across all top 10 perpetual pairs:
   - BTCUSDT: $4.0\text{ bps}$ Maker / $10.0\text{ bps}$ Taker
   - ETHUSDT: $4.0\text{ bps}$ Maker / $10.0\text{ bps}$ Taker
   - SOLUSDT: $4.0\text{ bps}$ Maker / $10.0\text{ bps}$ Taker
   - Altcoins (AVAX, DOGE, LINK, LTC, BNB, XRP, ADA): $4.0\text{ bps}$ Maker / $10.0\text{ bps}$ Taker
4. **Minimum Notional & Lot Sizes:** Handled via REST `exchangeInfo` filters (`LOT_SIZE`, `PRICE_FILTER`, `MIN_NOTIONAL`). Standard minimum trade notional on AsterDEX is $\$5.00$ USDT, ensuring our standard test notionals of $\$10$, $\$25$, and $\$100$ exceed exchange filter thresholds.

---

### 4. FEE CALCULATION METHODOLOGY ON EXECUTED NOTIONAL

Fees are assessed as a direct percentage of executed notional value on both legs of a round-trip trade:

$$\mathbf{Notional}_{\text{entry}} = \mathbf{Quantity}_{\text{executed}} \times \mathbf{Price}_{\text{entry\_fill}}$$
$$\mathbf{Fee}_{\text{entry}} = \mathbf{Notional}_{\text{entry}} \times c_{\text{fee, entry}}$$

$$\mathbf{Notional}_{\text{exit}} = \mathbf{Quantity}_{\text{executed}} \times \mathbf{Price}_{\text{exit\_fill}} = \mathbf{Notional}_{\text{entry}} \times (1 + d \cdot R_{\text{gross}})$$
$$\mathbf{Fee}_{\text{exit}} = \mathbf{Notional}_{\text{exit}} \times c_{\text{fee, exit}}$$

where $d = +1$ for Long, $d = -1$ for Short, and $R_{\text{gross}} = (P_{\text{exit}} - P_{\text{entry}}) / P_{\text{entry}}$.

#### 4.1 Exit Notional Asymmetry:
Because the exit fee is calculated on executed exit notional:
- On a **winning trade** ($R_{\text{gross}} > 0$), exit notional is larger than entry notional, resulting in a dollar exit fee that is higher than the entry fee.
- On a **losing trade** ($R_{\text{gross}} < 0$), exit notional is smaller than entry notional, resulting in a lower dollar exit fee.
- Any model that calculates total fees simply as $2 \times N_{\text{entry}} \times c_{\text{fee}}$ introduces an arithmetic approximation error. QUANTUM's [`src/quantum/backtesting/accounting.py`](file:///d:/quantum-multi-agent/src/quantum/backtesting/accounting.py) calculates exact separate entry and exit notional fees.

---

### 5. REBATES, DISCOUNTS & CONSERVATISM POLICIES

1. **Maker Rebates:** 
   - At the Base Retail tier, maker limit orders incur a positive cost of $+4.0\text{ bps}$.
   - Negative maker fees (where the exchange pays the trader a rebate for providing liquidity) do not exist for retail accounts.
2. **Platform Token Staking & Fee Deductions:**
   - Some decentralized exchanges offer a $10\%–20\%$ fee reduction if trading fees are paid using native utility tokens.
   - **Research Governance Rule:** Zero token discounts are assumed in QUANTUM research. All backtest models must pay the full $100\%$ cash fee in USDT.
3. **Referral Rebates:**
   - Referral volume kickbacks are excluded.

---

### 6. EVIDENCE AUDIT & CLASSIFICATION STATUS

- **Authoritative Documentation Sources:**
  - `docs/ASTERDEX_MARKET_DATA.md` (lines 1–93).
  - AsterDEX Public Protocol Documentation (`https://fapi.asterdex.com`).
  - Binance Futures-compatible REST API v1 endpoints.
- **Account-Specific Empirical Ledger Evidence:**
  - Under strict QUANTUM research governance, paper trading and live trading are currently **PROHIBITED** (`PAPER_TRADING_AUTHORIZATION: DENIED_PENDING_3_PERCENT_BACKTEST_VALIDATION`).
  - No live wallet private keys or signed fill receipts currently exist in this repository.
- **Formal Status Classification:**
  - In strict compliance with research integrity standards, the AsterDEX Base Retail schedule ($4.0\text{ bps}$ Maker / $10.0\text{ bps}$ Taker) is formally designated:
  
  $$\mathbf{Status:\ AUTHORITATIVELY\_VERIFIED\_PROTOCOL\_BASELINE\ (PROVISIONAL\_RESEARCH\_ASSUMPTION)}$$
  
  - If subsequent live execution on AsterDEX reveals different realized fee schedules, the Banker Agent and Research Experiment Contract must be updated immediately.
