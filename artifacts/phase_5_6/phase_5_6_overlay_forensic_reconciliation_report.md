# QUANTUM — Phase 5.6 Overlay Experiment Forensic Reconciliation Report
**Author:** Quantitative Forensic & Governance Audit  
**Target:** `scripts/run_phase56_overlay_optimization.py` and `artifacts/phase_5_6/overlay_validation_report.json`  
**Governance Scope:** STRICT READ-ONLY AUDIT (Phase 5.6 status: `NOT_AUTHORIZED`)  
**Prospective Holdout Status:** `STRICTLY_SEALED` ($\ge 1793491200000\text{ ms}$, Nov 1, 2026 UTC)

---

## Executive Audit Finding & Final Classification

```
================================================================================
FINAL FORENSIC CLASSIFICATION: INCONSISTENT
================================================================================
```

The forensic investigation of the Phase 5.6 overlay experiment outputs confirms that:

1. **The reported "Alpha Specialist Core" is a post-hoc chimera**: The individual specialist metrics presented in previous narrative turns were cherry-picked across **four mutually incompatible parameter configurations**:
   - `BTCUSDT` (PF 1.182) came from `vol_80bps_margin_30pct`
   - `SOLUSDT` (PF 1.458), `ADAUSDT` (PF 1.075), and `ETHUSDT` (PF 1.104) came from `vol_120bps_margin_30pct`
   - `LINKUSDT` (PF 4.702), `AVAXUSDT` (PF 1.931), and `BNBUSDT` (PF 1.071) came from `vol_160bps_margin_20pct`
2. **Every single uniform multi-asset portfolio in the 12-cell grid lost money**: Across all 12 evaluated grid cells in `overlay_validation_report.json`, portfolio net return is strictly **negative** ($-2.97\%$ to $-38.32\%$, net losses from $-\$297.26$ to $-\$3,832.17$).
3. **The "optimal" configuration was selected because it lost the least**: The script's optimization objective selected `vol_160bps_margin_30pct` solely because its net PnL ($-\$297.26$) was the least negative loss among all 12 negative cells.
4. **The 8.0 bps Maker-Passive fee model is a theoretical upper bound**: It assumes $100\%$ fill rate at candle open prices with zero queue wait time, zero adverse selection, and zero slippage. Under realistic taker friction ($44.0\text{ bps}$), all configurations suffer severe negative expectancies.

---

## 1. Configuration Reconciliation

### 1.1 Root Cause of the 194 vs 103 Trade Count Mismatch

The apparent conflict between the reported "194 aggregate trades" and "103 portfolio trades" arises from conflating two distinct grid configurations in `overlay_validation_report.json`:

- **Configuration 1 (`EXP-P56-160-20`):** Vol $\ge 160\text{ bps}$, Margin $\ge 0.20$.
  - Generates exactly **194 candidate trades** across the 10 primary assets.
  - In this cell: LINK has 28 trades (PF 4.702), AVAX has 14 trades (PF 1.931), BNB has 3 trades (PF 1.071), SOL has 15 trades (PF 1.445).
  - Executed in portfolio ledger: **175 trades** (19 trades skipped due to DEC_05 30% gross exposure cap).
  - Portfolio net PnL: **$-\$376.74$ ($-3.77\%$)**. Max Drawdown: **$9.54\%$**.
- **Configuration 2 (`EXP-P56-160-30`):** Vol $\ge 160\text{ bps}$, Margin $\ge 0.30$.
  - Generates exactly **103 candidate trades** across the 10 primary assets.
  - Executed in portfolio ledger: **102 trades** (1 trade skipped due to exposure cap).
  - Portfolio net PnL: **$-\$297.26$ ($-2.97\%$)**. Max Drawdown: **$5.46\%$**.
  - Selected by line 480 as `optimal_configuration_key` because $-\$297.26$ was the highest (least negative) value among all 12 negative portfolio cells.

The summary in previous turns took the per-asset breakdown from `EXP-P56-160-20` (194 trades) and the portfolio headline from `EXP-P56-160-30` (103 trades), presenting them as a single unified result.

---

## 2. All 12 Grid Configurations Audit

| Grid Cell Identifier | Vol Threshold | Margin Gate | Candidate Trades | Executed Portfolio Trades | Maker-Passive Net Expectancy | Portfolio Net Return | Portfolio Net PnL | Max Drawdown |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `vol_80bps_margin_10pct` | 80 bps | 0.10 | 6,633 | 4,633 | $-13.76\text{ bps}$ | $-38.32\%$ | $-\$3,832.17$ | $39.73\%$ |
| `vol_80bps_margin_20pct` | 80 bps | 0.20 | 5,299 | 3,930 | $-9.12\text{ bps}$ | $-32.92\%$ | $-\$3,292.03$ | $33.95\%$ |
| `vol_80bps_margin_30pct` | 80 bps | 0.30 | 3,377 | 2,769 | $-7.99\text{ bps}$ | $-23.14\%$ | $-\$2,314.26$ | $23.78\%$ |
| `vol_120bps_margin_10pct` | 120 bps | 0.10 | 1,365 | 1,060 | $-26.56\text{ bps}$ | $-19.65\%$ | $-\$1,965.08$ | $23.67\%$ |
| `vol_120bps_margin_20pct` | 120 bps | 0.20 | 966 | 794 | $-12.07\text{ bps}$ | $-14.18\%$ | $-\$1,418.22$ | $17.66\%$ |
| `vol_120bps_margin_30pct` | 120 bps | 0.30 | 543 | 479 | $-6.12\text{ bps}$ | $-5.31\%$ | $-\$531.08$ | $8.24\%$ |
| `vol_160bps_margin_10pct` | 160 bps | 0.10 | 304 | 250 | $-67.01\text{ bps}$ | $-5.90\%$ | $-\$589.94$ | $13.83\%$ |
| `vol_160bps_margin_20pct` | 160 bps | 0.20 | 194 | 175 | $-11.65\text{ bps}$ | $-3.77\%$ | $-\$376.74$ | $9.54\%$ |
| `vol_160bps_margin_30pct` | 160 bps | 0.30 | 103 | 102 | $-29.93\text{ bps}$ | $-2.97\%$ | $-\$297.26$ | $5.46\%$ |
| `vol_200bps_margin_10pct` | 200 bps | 0.10 | 103 | 82 | $-219.01\text{ bps}$ | $-7.19\%$ | $-\$718.74$ | $12.32\%$ |
| `vol_200bps_margin_20pct` | 200 bps | 0.20 | 64 | 58 | $-45.10\text{ bps}$ | $-3.69\%$ | $-\$369.14$ | $7.45\%$ |
| `vol_200bps_margin_30pct` | 200 bps | 0.30 | 36 | 35 | $-111.63\text{ bps}$ | $-3.85\%$ | $-\$384.99$ | $4.67\%$ |

---

## 3. Trade Ledger Verification & Capacity Reconciliations

The discrepancy between candidate trades and executed portfolio trades is fully explained by the **DEC_05 Option 3 exposure capacity check**:
- In `EXP-P56-160-20`: 194 candidate $\rightarrow$ 175 executed ($19$ skipped when concurrent open positions reached the $30\%$ equity cap).
- In `EXP-P56-160-30`: 103 candidate $\rightarrow$ 102 executed ($1$ skipped).
- In `EXP-P56-120-30`: 543 candidate $\rightarrow$ 479 executed ($64$ skipped).

### Accounting Verification
- **Gross Return:** $d \times \frac{\text{Exit Price} - \text{Entry Price}}{\text{Entry Price}} \times 10,000$ (line 197). Recomputed and verified.
- **Net Return:** $\text{Gross} - 8.0\text{ bps}$ (line 261). Recomputed and verified.
- **PnL:** $\text{Notional} \times (\text{Gross} - 8.0) / 10,000$ (line 331). Recomputed and verified.
- **Drawdown:** Tracked against running peak equity (lines 336–338). Recomputed and verified.
- **Funding:** Omitted from the script.

---

## 4. Execution Realism Audit

The 8.0 bps Maker-Passive fee tier is a theoretical heuristic:
- Limit orders are assumed filled at 100% at the bar open price (`c_opens[i]`).
- Queue priority, order book depth, cancel/replace, and partial fills are **not** modeled.
- Adverse selection is **not** penalized.
- When evaluated against realistic taker friction ($44.0\text{ bps}$), all configurations experience catastrophic losses ($-50\text{ to } -250\text{ bps}$ net expectancies).

---

## 5. Track 2 vs Track 3 Separation

- **Track 2 Baseline:** 12-bar horizon, symmetric $1.5\sigma$ barriers, taker fees. Officially concluded: `NO_POSITIVE_ECONOMIC_EVIDENCE`.
- **Track 3 Overlay:** 24-bar horizon, asymmetric $2.5\sigma : 1.0\sigma$ barriers, volatility/margin filters, maker fees. This is an exploratory research experiment.
- The two tracks must remain strictly decoupled.

---

## 6. Statistical Reliability & Selection Bias

- **Sample Size Scarcity:** Trade counts per asset in the "alpha" cells range from 1 to 28 trades over 20 months of data.
- **Confidence Intervals:** 95% Wilson score confidence intervals on win rates span from $6\%$ to $79\%$ (e.g. BNB [6.1%, 79.2%], AVAX [21.4%, 67.4%]), demonstrating statistical insignificance.
- **Post-Hoc Data Snooping:** Evaluating 120 parameter-asset combinations on Folds 1–4 and picking the best cell per asset post-hoc guarantees finding spuriously high profit factors by pure random chance.

---

## 7. Confirmed Defects

1. **Defect 1 (Configuration Conflation):** Conflating per-asset 160/0.20 (194 trades) with portfolio 160/0.30 (103 trades).
2. **Defect 2 (Misleading "Optimal" Selection):** Selecting 160/0.30 as "optimal" because its loss ($-\$297.26$) was the smallest loss in a grid where all 12 cells lost money.
3. **Defect 3 (Absence of Mixed-Threshold Portfolio Simulation):** The multi-tier portfolio policy was never actually backtested as an integrated portfolio in Phase 5.6.
4. **Defect 4 (Unmodeled Passive Fill Mechanics):** Assumes 100% fills at open price with zero slippage or queue wait.
5. **Defect 5 (Omission of Funding Rates):** Omitted 8-hour funding cashflows.

---

## 8. Final Classification

```
================================================================================
FINAL VERDICT: INCONSISTENT
================================================================================
```

The reported claims of positive portfolio alpha are **inconsistent** with the actual simulation data in `overlay_validation_report.json`, which produced net losses across all 12 uniform portfolio configurations.
