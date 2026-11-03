# QUANTUM FORENSIC AUDIT — PHASE A
## Trade Count Reconciliation & Cross-Strategy Trade Attribution Audit

**Audit Dossier Path:** `audit/strategy_research/milestone_5_6_independent_forensic/TRADE_COUNT_RECONCILIATION.md`  
**Execution Timestamp:** 2026-11-03T23:20:00Z  
**Branch:** `research/quantum-next-3pct`  
**Authorizing Mandate:** Milestone 5.6 Independent Forensic Revalidation Protocol  

---

## 1. Executive Summary & Forensic Question

In Milestone 5.5 documentation (`PORTFOLIO_OPTIMIZATION_REPORT.md` and `FINAL_RESEARCH_DECISION.md`), the following trade counts were reported:
- **EXP-10A (Passive Maker):** 31,767 trades
- **EXP-11 (Corrected Causal Impulse):** 41,200 trades
- **Portfolio A (Optimal Ensemble):** 41,200 trades

This identity between EXP-11 and Portfolio A raised an immediate governance concern:
> *Did Portfolio A accidentally incorporate the signals or trade ledger of EXP-11 (which had proven negative expectancy of -8.45 bps to -22.49 bps), thereby contaminating the reported ensemble performance?*

### Forensic Audit Verdict
```yaml
TRADE_COUNT_ANOMALY_STATUS: RESOLVED_AS_DOCUMENTATION_PLACEHOLDER
ACCIDENTAL_EXP11_INCLUSION: FALSE (Verified via Code & Signal Inspection)
TRUE_CAUSAL_PORTFOLIO_A_TRADES: 3,982 (Independent Execution Engine)
CONTAMINATED_SAME_BAR_TRADES: 47,606 (Non-Causal Execution Engine)
REPORTED_41200_ORIGIN: Typographical mirroring of exploratory causal impulse test
CLASSIFICATION: FAILED_REPORTED_METRIC_ACCURACY (Reported 41,200 does not match true causal ledger)
```

---

## 2. Root Cause Investigation & Code Forensics

### 2.1 Codebase Audit of Milestone 5.5
An exhaustive search of `scripts/run_milestone_5_5_alpha_engineering.py` and `scripts/run_milestone_5_5_statistical_audit.py` revealed the following:
1. `run_milestone_5_5_alpha_engineering.py` simulated four discrete functions:
   - `simulate_exp09_regime_adaptive()` $\rightarrow$ generated **67,483 trades**
   - `simulate_exp10_execution_aware(mode="PASSIVE_MAKER")` $\rightarrow$ generated **31,767 trades**
   - `simulate_exp10_execution_aware(mode="MARKETABLE_TAKER")` $\rightarrow$ generated **43,680 trades**
   - `simulate_exp11_structural_impulse()` $\rightarrow$ generated **93,684 trades** (same-bar contaminated)
2. During the subsequent forensic test of EXP-11 under causal next-bar execution, the script logged an exploratory sample of **41,200 trades** (recorded in `EXP11_STRUCTURAL_ALPHA_REPORT.md`, line 35).
3. Crucially, **no dedicated simulation function named `simulate_portfolio_a()` existed in `run_milestone_5_5_alpha_engineering.py`**.
4. When `PORTFOLIO_OPTIMIZATION_REPORT.md` was drafted, Portfolio A was formulated as an analytical combination of EXP-09 and EXP-10. However, instead of running an interleaved trade execution engine and dumping a dedicated trade ledger CSV, the table cell for Portfolio A's trade count was manually populated with the number **41,200**, directly mirroring the trade count from the EXP-11 causal report.

### 2.2 Proof of Non-Inclusion of EXP-11 Signals
To confirm whether EXP-11 signals were accidentally traded in Portfolio A:
- Signal definitions were compared:
  - EXP-09/EXP-10: Multi-timeframe trend filter ($|r_{12}| \ge 75\text{ bps}$ or $100\text{ bps}$), volume expansion ($\ge 1.05\text{ or } 1.15$), and intermediate momentum ($r_3 \ge 0$).
  - EXP-11: 1-bar expansion ($\text{Body} \ge 1.0\sigma$), relative volume ($\text{RVOL} \ge 1.30$), and wick rejection ($\le 20\%$).
- In `scripts/independent_forensic_evaluator.py`, we explicitly tagged each signal with its parent strategy (`EXP09_TAKER` vs `EXP10A_MAKER` vs `EXP11_IMPULSE`).
- In the reconstructed Portfolio A ledger (`PORTFOLIO_A_INDEPENDENT_TRADES.csv`), **0 out of 3,982 trades** originate from EXP-11. All executed trades originate exclusively from EXP-09 and EXP-10A logic.
- **Finding:** Portfolio A did **NOT** execute EXP-11 trades. The trade count of 41,200 was purely a reporting artifact.

---

## 3. Independent Trade-Level Reconciliation

In Milestone 5.6, the independent evaluator (`scripts/independent_forensic_evaluator.py`) generated complete, audited transaction records saved at [`PORTFOLIO_A_INDEPENDENT_TRADES.csv`](file:///d:/quantum-multi-agent/audit/strategy_research/milestone_5_6_independent_forensic/PORTFOLIO_A_INDEPENDENT_TRADES.csv).

### Comparative Trade Count Ledger

| Strategy Configuration | Reported in M5.5 | Independent Causal Ledger | Independent Contaminated Ledger | Attribution & Discrepancy Note |
| :--- | :---: | :---: | :---: | :--- |
| **EXP-09 (Regime Adaptive)** | 67,483 | 12,410 | 67,483 | Causal next-bar entry drops unconfirmed signals |
| **EXP-10A (Passive Maker)** | 31,767 | 10,733 | 47,606 | Realistic fill penetration drops unfilled limits |
| **EXP-11 (Impulse Continuation)** | 41,200 | 8,920 | 93,684 | Causal entry eliminates impulse open capture |
| **Portfolio A (Optimal Ensemble)** | **41,200** | **3,982** | **47,606** | **Ruin circuit breaker halts trading after early drawdown** |

### Why Did Causal Portfolio A Execute Only 3,982 Trades?
1. Under strictly causal next-bar execution (`opens[i+1]`), directional 5-minute entries after green bars suffer immediate mean-reversion drag ($-14.98\text{ bps}$ taker, $-5.89\text{ bps}$ maker).
2. Consequently, Portfolio A's equity declined steadily from the $\$100.00$ initial balance until it breached the **$\$5.00$ ruin circuit breaker** (`if portfolio_equity <= 5.0: break`).
3. Once the ruin threshold was reached at day index 112 (timestamp `1708638600000 ms`), the engine permanently halted trading for capital preservation.
4. Total trades executed prior to ruin halt: **exactly 3,982 trades**.

---

## 4. Conclusion & Governance Classification

1. The hypothesis that Portfolio A was contaminated by EXP-11 trades is **REFUTED**.
2. However, the reported Milestone 5.5 trade count of 41,200 is **INVALIDATED AS UNVERIFIED AND UNREPRODUCIBLE**.
3. Under true causal execution, Portfolio A does not execute 41,200 trades; it suffers capital exhaustion at trade 3,982.

**Phase A Classification:** `RESOLVED (DOCUMENTATION ERROR IDENTIFIED; METRIC NOT INDEPENDENTLY VALIDATED)`
