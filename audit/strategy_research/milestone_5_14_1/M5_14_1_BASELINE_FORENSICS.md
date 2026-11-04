# QUANTUM MILESTONE 5.14.1 — BASELINE FORENSICS REPORT
## Systematic Provenance, Environment Integrity & Implementation Archaeology

**Project:** QUANTUM Multi-Agent Intraday Crypto Perpetual Futures Research System  
**Repository:** `d:/quantum-multi-agent`  
**Branch:** `research/quantum-next-3pct`  
**Baseline Git HEAD Commit:** `0088b65`  
**Audit Target Milestone:** M5.14 — Concentrated Capital & Velocity Recycling  
**Audit Milestone Type:** Independent Financial, Mathematical, Statistical & Portfolio Accounting Forensic Audit  
**Author:** Quantitative Systems Auditor & Forensic Risk Engine  
**Execution Environment:** Isolated Simulation Sandbox (Strictly NO paper trading / NO live trading / NO exchange credentials)

---

## 1. EXECUTIVE OVERVIEW & PROVENANCE VERIFICATION

Milestone 5.14 reported unprecedented performance figures:
- **44,100 extreme-expansion candidates** across 10 crypto perpetual assets.
- **Reported Mean Net Daily Return:** Reaching **+347.41%** (Mode A Sniper Bybit VIP0 Maker) and **+141.77%** (Mode A Sniper AsterDEX Maker).
- **Reported Active-Day Return:** +0.50% to +1.53%.
- **Reported Deflated Sharpe Ratio (DSR):** Exactly **1.000000** across all 12 experimental configurations.
- **Reported Peak Gross Exposure:** **0.995038x** vs Admission Cap of 0.995000x (+0.000038x delta) and Hard Cap of 1.000000x.
- **Reported Accounting Oracle Reconciliation Delta:** **$0.0000000000**.

This baseline forensic audit establishes the chain of custody, verifies historical data integrity, seals holdout boundaries, and isolates the exact codebase implementations responsible for all reported metrics.

```
       [Historical Canonical Data] (Exchange=ASTER, 10 Assets)
                   │  Strict Holdout Seal: open_time_ms < 1793491200000
                   ▼
       [Feature Engineering Engine] (1h ATR >= 80%, Volume Surge >= 2.5x, 15m Confluence >= Q95)
                   │  1h & 15m Features Shifted 1 Completed Bar (No Lookahead)
                   ▼
       [Candidate Generation] (44,100 Extreme-Expansion Opportunities)
                   │
    ┌──────────────┴──────────────────────────────┐
    ▼                                             ▼
[EventDrivenPortfolioLedger]         [IndependentAccountingOracle]
- Primary Double-Entry Accounting    - Secondary Independent Oracle
- ActiveMTMMonitor (0.995x / 1.00x)   - Independent Lot & Cash Tracking
    │                                             │
    └──────────────┬──────────────────────────────┘
                   ▼
     [Final Audit Reconciliation]
     Delta = $0.0000000000 across all 12 rows
```

---

## 2. REPOSITORY & COMMIT BASELINE

| Property | Value | Forensic Verification |
|---|---|---|
| **Git Working Directory** | `d:/quantum-multi-agent` | Absolute canonical workspace path |
| **Git Current Branch** | `research/quantum-next-3pct` | Confirmed isolated research branch; no merge to `main` |
| **Commit Hash (HEAD)** | `0088b65` | `audit(milestone-5.12.2.2.1): mathematical integrity and test reproduction correction` |
| **Remote Synchronization** | Up to date with `origin/research/quantum-next-3pct` | Verified via `git status` |
| **Prior Milestone Reference** | M5.14 Concentrated Capital & Velocity Recycling | `scripts/run_m5_14_concentrated_velocity.py` |
| **Pre-Holdout Boundary** | `1,793,491,200,000` (2026-11-01T00:00:00.000Z) | Zero post-boundary bars loaded |

---

## 3. CANONICAL DATASET INTEGRITY & FINGERPRINTS

The panel comprises 10 primary liquid perpetual futures contracts specified in `PRIMARY_RESEARCH_UNIVERSE` (`XMRUSDT` excluded pursuant to structural-break governance):
1. `BTCUSDT`
2. `ETHUSDT`
3. `BNBUSDT`
4. `XRPUSDT`
5. `ADAUSDT`
6. `SOLUSDT`
7. `AVAXUSDT`
8. `LINKUSDT`
9. `DOGEUSDT`
10. `LTCUSDT`

### 3.1 Dataset Boundary Audit
- **Canonical Storage Path:** `data/historical/canonical/exchange=ASTER/symbol={symbol}/timeframe={timeframe}/`
- **Timeframes Evaluated:** `5m` (execution), `15m` (confluence score), `1h` (volatility & volume conditioning).
- **Candidate Start Timestamp:** `1698753600000` (2023-10-31 12:00:00 UTC).
- **Candidate End Timestamp:** `1793384700000` (2026-10-30 18:25:00 UTC).
- **Total Span:** **1,095.267 calendar days** (3.00 calendar years).
- **Holdout Boundary Check:**
  $$\max(T_{\text{open\_time\_ms}}) = 1,793,384,700,000 < 1,793,491,200,000 \quad \text{[SEALED: PASS]}$$
  No data beyond 2026-11-01T00:00:00Z was accessed or evaluated.

---

## 4. ARCHAEOLOGY OF REPORTED METRICS IMPLEMENTATION

Inspection of `scripts/run_m5_14_concentrated_velocity.py` reveals the exact code definitions:

### 4.1 Mean Net Daily Return (`mean_net_daily_return_pct`)
Located in lines 221, 231, and 236:
```python
days = max(1.0, (candidates[-1].exit_timestamp_ms - candidates[0].timestamp_ms) / 86_400_000.0)
total_return = (ledger.equity / INITIAL_EQUITY - 1.0) * 100.0
"mean_net_daily_return_pct": total_return / days
```
**Forensic Diagnosis:**  
This formula calculates:
$$\text{mean\_net\_daily\_return\_pct} = \frac{\left( \frac{E_T - E_0}{E_0} \times 100\% \right)}{\text{Total Days}}$$
This divides the **cumulative multi-year compounded return** by total calendar days. It is **NOT** an arithmetic mean of daily returns, nor a geometric mean daily return. For Mode A Sniper Bybit VIP0 Maker:
- Initial Equity: $\$100.00$
- Terminal Equity: $\$380,608.34$
- Total Compounded Return: $+380,508.34\%$
- Dividing $+380,508.34\%$ by $1,095.27$ days yielded $+347.41\%$!
This is a fatal mathematical conflation between compounded multi-year return and simple daily rate of return.

### 4.2 Active Day Return (`active_day_return_pct`)
Located in lines 225-237:
```python
exits_df = pd.DataFrame(exits, columns=["timestamp_ms", "equity"])
exits_df["day"] = pd.to_datetime(exits_df["timestamp_ms"], unit="ms", utc=True).dt.date
daily = exits_df.groupby("day")["equity"].last().pct_change().dropna() * 100.0
"active_day_return_pct": float(daily.mean()) if not daily.empty else 0.0
```
**Forensic Diagnosis:**  
This calculates the mean percentage change of equity marks strictly across days that had at least one completed trade exit. Days with zero exits (~520 days out of 1,096) were dropped from the denominator.

### 4.3 Deflated Sharpe Ratio (`deflated_sharpe_ratio`)
Located in lines 138-146:
```python
def dsr(values: Iterable[float], trials: int = 12) -> float:
    a = np.asarray(list(values), dtype=float)
    if len(a) < 3 or a.std(ddof=1) == 0:
        return 0.0
    sharpe = (a.mean() / a.std(ddof=1)) * np.sqrt(365.0)
    sigma = np.sqrt((1.0 + 0.5 * sharpe * sharpe) / len(a))
    expected_max = NormalDist().inv_cdf(1.0 - 1.0 / trials)
    return float(NormalDist().cdf((sharpe - expected_max) / max(sigma, 1e-12)))
```
**Forensic Diagnosis:**  
Input series `values` was `daily.tolist()` (active trade days only). With positive returns on exit days, the sample Sharpe ratio reached 6.0 to 7.5. Standard normal CDF `NormalDist().cdf(z)` evaluated at $z \approx (7.0 - 1.38) / 0.20 \approx 28$, which saturates to floating-point `1.0000000000` (saturation occurs for any $z > 8.2$). Skewness and kurtosis were completely ignored.

### 4.4 Peak Gross Exposure Discrepancy
Located in lines 167-170:
```python
snapshot = monitor.evaluate_portfolio(ledger.open_positions, ledger.reserved_pending_notional, ledger.cash_balance, prices, due)
peak_exposure = max(peak_exposure, snapshot.gross_exposure_committed)
```
In Mode B (2 slots, 0.490 weight each), peak gross exposure reached **0.995038x**, which is $+0.000038x$ above the admission cap ($0.995000x$) while strictly respecting the hard cap ($1.000000x$). Traced to intraday MTM price appreciation on a long position (ADAUSDT +150 bps) while a concurrent position (AVAXUSDT) was active.

---

## 5. EXPERIMENT IDENTIFICATION & SPECIFICATIONS

The 12 evaluated configurations are systematically mapped:

| Experiment ID | Portfolio Mode | Slots | Symbol Weight | Execution Regime | Roundtrip Fee |
|---|---|---|---|---|---|
| `EXP-01` | Legacy 4-Slot | 4 | 0.2450 | AsterDEX Maker-Queue | 11.0 bps RT |
| `EXP-02` | Legacy 4-Slot | 4 | 0.2450 | Bybit VIP0 Maker-Queue | 7.0 bps RT |
| `EXP-03` | Legacy 4-Slot | 4 | 0.2450 | Bybit VIP0 Hybrid Maker/Taker | 11.0 bps RT |
| `EXP-04` | Legacy 4-Slot | 4 | 0.2450 | AsterDEX Retail Taker | 26.0 bps RT |
| `EXP-05` | Mode A Sniper | 1 | 0.9800 | AsterDEX Maker-Queue | 11.0 bps RT |
| `EXP-06` | Mode A Sniper | 1 | 0.9800 | Bybit VIP0 Maker-Queue | 7.0 bps RT |
| `EXP-07` | Mode A Sniper | 1 | 0.9800 | Bybit VIP0 Hybrid Maker/Taker | 11.0 bps RT |
| `EXP-08` | Mode A Sniper | 1 | 0.9800 | AsterDEX Retail Taker | 26.0 bps RT |
| `EXP-09` | Mode B Dual-Slot | 2 | 0.4900 | AsterDEX Maker-Queue | 11.0 bps RT |
| `EXP-10` | Mode B Dual-Slot | 2 | 0.4900 | Bybit VIP0 Maker-Queue | 7.0 bps RT |
| `EXP-11` | Mode B Dual-Slot | 2 | 0.4900 | Bybit VIP0 Hybrid Maker/Taker | 11.0 bps RT |
| `EXP-12` | Mode B Dual-Slot | 2 | 0.4900 | AsterDEX Retail Taker | 26.0 bps RT |

---

## 6. AUDIT SCOPE AND STRUCTURE

The subsequent forensic phases systematically address every reported claim:
- **Phase B:** Daily Return Metric Forensics & Calendar Reconciliation (`M5_14_1_DAILY_RETURN_FORENSICS.md`).
- **Phase C:** Deflated Sharpe Ratio Forensics & Multiple Testing Correction (`M5_14_1_DSR_FORENSICS.md`).
- **Phase D:** Maximum Drawdown Independent Re-evaluation (`M5_14_1_DRAWDOWN_AUDIT.md`).
- **Phase E:** Profit Recycling Capital Conservation & Double-Counting Audit (`M5_14_1_PROFIT_RECYCLING_AUDIT.md`).
- **Phase F:** Concentrated Capital vs Multi-Slot Portfolio Comparison (`M5_14_1_PORTFOLIO_MODE_COMPARISON.md`).
- **Phase G:** Exposure Invariant MTM Drift Forensics (`M5_14_1_EXPOSURE_INVARIANT_AUDIT.md`).
- **Phase H:** Execution Regime & Maker Fill Sensitivity Analysis (`M5_14_1_EXECUTION_MODEL_AUDIT.md`).
- **Phase I:** Accounting Oracle Independence & Double-Entry Verification (`M5_14_1_ACCOUNTING_ORACLE_AUDIT.md`).
- **Phase J:** Statistical Credibility & Dependent Return Resampling (`M5_14_1_STATISTICAL_VALIDATION.md`).
- **Phase K:** Test Suite Reproduction (`M5_14_1_TEST_REPRODUCTION.md`).
- **Phase L & M:** Governance Verdict, Risks, and Acceptance (`M5_14_1_FINAL_VERDICT.md`).
