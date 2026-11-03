# QUANTUM RESEARCH GOVERNANCE — MILESTONE 5.8B
## Final Research Decision & Alpha Family Governance Directive

**Dossier Path:** `audit/strategy_research/milestone_5_8b_new_alpha_feasibility/FINAL_RESEARCH_DECISION.md`  
**Execution Timestamp:** 2026-11-04T00:21:00Z  
**Branch:** `research/quantum-next-3pct`  
**Authorizing Mandate:** Milestone 5.8B New Alpha Family Feasibility Protocol  

---

## 1. Governance Classification & Paper Trading Status

Under the Project Owner's non-negotiable quantitative mandate, this document formalizes the conclusions and operational status of Milestone 5.8B ("New Alpha Family Feasibility & Research Design").

Milestone 5.8B is an architectural and data feasibility study, **not a profitability certification**. No claim is made that the mandatory $\ge 3.00\%$ mean net daily return target has been satisfied.

### Governance Scorecard
```yaml
RESEARCH_MILESTONE: MILESTONE_5_8B
CURRENT_PHASE: ALPHA_FAMILY_FEASIBILITY_AND_DESIGN
FINAL_RESEARCH_STATUS: REQUIRES_RESEARCH
PAPER_TRADING_AUTHORIZATION: DENIED_PENDING_3_PERCENT_BACKTEST_VALIDATION
LIVE_TRADING_AUTHORIZATION: STRICTLY_PROHIBITED
OPERATIONAL_PROHIBITIONS:
  - PAPER_TRADING_DAEMON: STRICTLY_PROHIBITED
  - PAPER_SCHEDULER_SERVICES: STRICTLY_PROHIBITED
  - PROSPECTIVE_PAPER_DEPLOYMENT: STRICTLY_PROHIBITED
  - EXCHANGE_API_TRADING_CREDENTIALS: STRICTLY_PROHIBITED
  - LIVE_ACCOUNT_CONNECTION: STRICTLY_PROHIBITED
  - MAIN_BRANCH_MERGE: STRICTLY_PROHIBITED
MANDATORY_TARGET_REMAINDER:
  - MINIMUM_MEAN_NET_DAILY_RETURN: >= 3.00%
  - EFFECTIVE_LEVERAGE: STRICTLY 1.0x (UNLEVERED)
  - MAXIMUM_DRAWDOWN: <= 15.00%
  - PROFIT_FACTOR: >= 1.30
  - NET_EXPECTANCY: POSITIVE AFTER VIP0 TRANSACTION FRICTION
```

---

## 2. Research Track Classifications

In accordance with Section 9 of the Milestone 5.8B Mandate, each research track is formally classified:

```
+---------------------------------------------------------------------------------------------------+
| RESEARCH TRACK                      | FINAL FEASIBILITY STATUS        | OPERATIONAL ACTION        |
+---------------------------------------------------------------------------------------------------+
| TRACK A: Funding & Basis            | DATA_ACQUISITION_REQUIRED       | Build historical 8h       |
|                                     |                                 | funding & spot pipelines  |
| TRACK B: Order Flow Microstructure  | DATA_ACQUISITION_REQUIRED       | Deploy L2 websocket logger|
|                                     |                                 | (Halted under VIP0 fees)  |
| TRACK C: Cross-Sectional Rel Value  | READY_FOR_EMPIRICAL_RESEARCH    | Author Phase 5.9 empirical|
|                                     |                                 | cointegration backtester  |
+---------------------------------------------------------------------------------------------------+
```

### Detailed Rationale
1. **Track A (Funding & Basis):**
   - Designated **`DATA_ACQUISITION_REQUIRED`**.
   - No historical funding rates or spot OHLCV currently exist in the repository. Fabricating synthetic funding rates is strictly prohibited. Empirical testing is suspended until historical data is acquired from exchange REST endpoints.
2. **Track B (Order Flow Microstructure):**
   - Designated **`DATA_ACQUISITION_REQUIRED`**.
   - No tick-by-tick public trade stream or L2 depth diffs currently exist in the repository. Synthesizing L2 data from 5-minute bars is strictly prohibited. Furthermore, sub-minute trading is structurally unviable under Bybit VIP0 transaction costs.
3. **Track C (Cross-Sectional Relative Value):**
   - Designated **`READY_FOR_EMPIRICAL_RESEARCH`**.
   - The primary universe of 10 assets possesses 1,099 continuous calendar days of synchronized 5m/15m/1h OHLCV data. 9 asset pairs are statistically verified as cointegrated ($t < -3.37$). Causal, zero-lookahead backtesting may begin immediately.

---

## 3. Holdout & Multiple-Testing Protection Protocol

To maintain complete empirical integrity across future research milestones:

1. **Virgin Holdout Preservation:**
   - The prospective holdout boundary remains set at `1,793,491,200,000 ms` (`2026-11-01 00:00:00 UTC`).
   - All canonical parquet datasets terminate at `2026-10-31 23:55:00 UTC`.
   - Accessing or training on post-boundary data is strictly prohibited until a strategy satisfies all gates on the development set.
2. **Multiple-Testing Control (White's Reality Check / Bonferroni):**
   - In Track C pairs trading, testing 45 pairs introduces multiple-comparison bias.
   - The significance threshold for cointegration must be adjusted using the MacKinnon (1991) critical values for cointegrating vectors ($-3.37$ at $\alpha = 0.05$).
   - Parameter sweeps and indicator permutations are strictly forbidden. Only economic, structural hypotheses (e.g. cointegrated mean-reversion, residual momentum) are permitted.

---

## 4. Next Milestone Roadmap: Transition to Milestone 5.9

With Milestone 5.8B completed, the QUANTUM research pipeline transitions directly to:

1. **Milestone 5.9A — Empirical Cointegration & Relative Value Engine (Track C):**
   - Implement the causal multi-asset market-neutral simulator for the 9 verified cointegrated pairs.
   - Model limit order queue fills, 15 bps round-trip VIP0 friction, and strictly 1.0x unlevered leverage (50% Long / 50% Short).
   - Evaluate empirical Sharpe, maximum drawdown, and net daily return against the mandatory gates.
2. **Milestone 5.9B — Funding Rate & Basis Data Acquisition Pipeline (Track A):**
   - Develop and execute `scripts/data/backfill_funding_history.py` to ingest 3 years of Bybit/Binance 8-hour funding rates.
   - Audit funding rate distribution, persistence, and net cash-and-carry yields.

---

## 5. Research Sign-Off

```yaml
GOVERNANCE_SIGN_OFF:
  AUDIT_MILESTONE: MILESTONE_5_8B
  FEASIBILITY_ENGINE: scripts/audit_milestone_5_8b_data_inventory.py
  TRACK_A_STATUS: DATA_ACQUISITION_REQUIRED
  TRACK_B_STATUS: DATA_ACQUISITION_REQUIRED
  TRACK_C_STATUS: READY_FOR_EMPIRICAL_RESEARCH
  FINAL_STATUS: REQUIRES_RESEARCH
  PAPER_TRADING: DENIED_PENDING_3_PERCENT_BACKTEST_VALIDATION
  AUTHORIZATION_DATE: 2026-11-04
```
