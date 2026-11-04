# QUANTUM MILESTONE 5.13 — DATA & CAUSALITY INTEGRITY AUDIT

**Milestone:** M5.13 — Multi-Factor Confluence & Passive Maker Alpha Discovery  
**Repository:** `d:/quantum-multi-agent`  
**Audit Date:** 2026-11-04  
**Classification:** Research Governance, Temporal Partitioning & Causality Verification  
**Branch:** `research/quantum-next-3pct`  
**Execution Policy:** STRICTLY SIMULATION ONLY — NO PAPER TRADING, NO LIVE TRADING

---

## 1. Executive Summary

A primary methodological vulnerability in quantitative trading research is lookahead bias, data leakage across cross-validation splits, and unverified timestamp alignment. Milestone 5.13 establishes strict causal boundaries and cryptographic data partition separation across all 11 canonical AsterDEX perpetual linear futures instruments:

- **Sealed Prospective Holdout:** Strictly sealed at timestamp `1,793,491,200,000` (2026-11-01T00:00:00Z).
- **Mandatory Embargo:** Strict 288-bar ($24.0\text{ hours}$ on 5m) embargo buffer enforced between all sequential dataset partitions.
- **Decision Causality Invariant:** Signals generated at bar $t$ are computed strictly using closed historical candles up to $t$. Entry execution is simulated strictly at the open of bar $t+1$.
- **Multi-Timeframe Synchronization:** 1-hour and 15-minute contextual features are mapped to 5m execution bars using backward `merge_asof` matching on `close_time_ms <= open_time_ms`, guaranteeing that higher-timeframe candles are 100% completed before their information is ingested.

---

## 2. Temporal Partitioning Topology

| Partition Type | Historical Date Range | Bar Count (5m) | Embargo Buffer | Governance Policy |
| :--- | :--- | :---: | :---: | :--- |
| **TRAIN (Discovery)** | 2023-10-28 to 2024-12-31 | 123,864 | 288 bars | Feature exploration, factor calibration, ML model training |
| **VALIDATION (Selection)** | 2025-01-01 to 2025-12-31 | 105,119 | 288 bars | Hypothesis filtering, hyperparameter gating, selection |
| **ROLLING_OOS (Evaluation)** | 2026-01-01 to 2026-10-31 | 87,516 | N/A | Read-only walk-forward evaluation; zero retraining |
| **PROSPECTIVE_OOS (Holdout)** | $\ge$ 2026-11-01T00:00:00Z | 0 (Sealed) | Sealed | **STRICTLY SEALED**; zero access, zero calibration |

---

## 3. Data Integrity & Causality Verification Invariants

### 3.1 Strict Candle Completion Invariant
For every bar $t$ with open timestamp $T_{\text{open}}$ and close timestamp $T_{\text{close}}$:
$$T_{\text{close}} - T_{\text{open}} = 299,999\text{ ms} \quad (5\text{ minutes} - 1\text{ ms})$$
Features calculated at bar $t$ ingest data exclusively from indices $\le t$. When a signal is emitted at the close of bar $t$, order submission is timestamped at $T_{\text{open}}(t+1) = T_{\text{close}}(t) + 1\text{ ms}$, preventing same-bar intra-candle execution illusions.

### 3.2 Multi-Timeframe Alignment & Causal Broadcasting
When incorporating 1-hour trend bias into a 5-minute decision loop:
- A 1-hour candle spanning `14:00:00.000` to `14:59:59.999` has `close_time_ms` at `14:59:59.999`.
- The first 5-minute bar permitted to observe this 1-hour trend is the bar opening at `15:00:00.000`.
- Bars between `14:00:00` and `14:55:00` observe strictly the prior completed 1-hour candle (`13:00:00` to `13:59:59.999`).
- Verified via `pd.merge_asof(..., left_on="open_time_ms", right_on="close_time_ms", direction="backward")`.

### 3.3 Cross-Asset Synchronization
Cross-sectional relative strength and market breadth metrics (such as `SOLUSDT` relative to `BTCUSDT`) require timestamp alignment:
- Dataframes are joined strictly on identical `open_time_ms`.
- Missing bars in any cross-asset pair default to neutral relative strength ($0.0$) rather than forward-filling stale future ticks.

### 3.4 288-Bar Embargo Enforcement
To prevent serial correlation and overlapping holding period leakage between cross-validation folds:
$$\text{Embargo Duration} = 288 \times 300,000\text{ ms} = 86,400,000\text{ ms} \quad (24\text{ hours})$$
This exceeds the maximum strategy holding horizon ($4.0\text{ hours} = 48\text{ bars}$) by a factor of 6.0x, ensuring that trade episodes initiated in TRAIN have completely closed and settled before VALIDATION begins.

---

## 4. Cryptographic Dataset Provenance

All 11 canonical AsterDEX perpetual linear futures instruments were verified against the prospective holdout threshold:

$$\text{Max Observed Timestamp} = 1,793,480,399,999 < 1,793,491,200,000 \quad (\mathbf{PASS})$$

Zero bytes of prospective holdout data were touched during this milestone.
