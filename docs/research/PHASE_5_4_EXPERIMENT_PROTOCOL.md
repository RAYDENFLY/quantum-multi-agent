# QUANTUM PHASE 5.4: EXPERIMENT PROTOCOL & SPECIFICATION
**Detailed Implementation Protocols, Mathematical Formulations & Execution Guide**

**Document Version:** 5.4.1_PROTOCOL  
**System:** QUANTUM 11-Specialist Cryptocurrency Perpetual Futures ML Trading Research System  
**Governance Status:** `PROTOCOL_SPECIFICATION_AWAITING_EXPLICIT_AUTHORIZATION`  
**Classification Standards:** `VERIFIED_FROM_SOURCE` | `VERIFIED_FROM_ARTIFACT` | `DOCUMENTATION_ONLY`

---

## 1. Protocol 1: Chronological OOF Temporal Partitioning & Purge Audit

To ensure zero information leakage between model inference, calibrator fitting, decision policy tuning, and final evaluation, the existing 5-fold expanding walk-forward OOF observations are partitioned chronologically into three disjoint segments:

```
[--------------------- Total OOF Period: 2025-01-29 to 2026-04-30 ---------------------]
|                                |                                |                    |
|   Segment 1: Calibration Fit   |   Segment 2: Policy Tuning     |  Segment 3: Eval   |
|   Folds 1 & 2 (~52,290 bars)   |   Folds 3 & 4 (~52,290 bars)   |  Fold 5 (~26,148)  |
|   2025-01-29 -> 2025-07-30     |   2025-07-30 -> 2026-01-29     |  2026-01-29->04-30 |
|                                |                                |                    |
[--------------------------------------------------------------------------------------]
```

### Exact Timestamps and 13-Bar Purge Verification:
Verification of [fold_manifest.json](file:///d:/quantum-multi-agent/artifacts/phase_5_3_2/ETHUSDT/fold_manifest.json) confirms the exact millisecond and UTC boundaries:

| Fold | Test Start (UTC) | Test Start (ms) | Test End (UTC) | Test End (ms) | Test Samples | Gap to Next Test Fold |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Fold 1** | `2025-01-29 04:40:00` | 1738125600000 | `2025-04-30 04:10:00` | 1745986200000 | 26,145 | **3,900,000 ms (13 bars)** |
| **Fold 2** | `2025-04-30 05:15:00` | 1745990100000 | `2025-07-30 11:10:00` | 1753873800000 | 26,145 | **3,900,000 ms (13 bars)** |
| **Fold 3** | `2025-07-30 12:15:00` | 1753877700000 | `2025-10-29 19:30:00` | 1761766200000 | 26,145 | **3,900,000 ms (13 bars)** |
| **Fold 4** | `2025-10-29 20:35:00` | 1761770100000 | `2026-01-29 07:45:00` | 1769672700000 | 26,145 | **3,900,000 ms (13 bars)** |
| **Fold 5** | `2026-01-29 08:50:00` | 1769676600000 | `2026-04-30 21:55:00` | 1777586100000 | 26,148 | N/A (End of OOF) |

**Purge Integrity Proof:**
Because `horizon_bars = 12`, the label for the final test candle of Fold 2 terminates at $1753873800000 + (12 \times 300,000) = 1753877400000$ (`2025-07-30 12:10:00 UTC`).
Fold 3 test starts at $1753877700000$ (`2025-07-30 12:15:00 UTC`), exactly 1 bar (5 minutes) after the 12-bar label horizon of Fold 2 expires.
Consequently, **zero label leakage exists between Segment 1 and Segment 2**, and **zero label leakage exists between Segment 2 and Segment 3**.

### Strict Holdout Isolation:
The prospective holdout partition (`2026-11-01 00:00:00 UTC` through `2027-04-30 23:59:59.999 UTC`) remains completely sealed and protected. Zero queries, feature lookups, or calibrator evaluations shall touch or reference this window. Furthermore, the historical period through `2026-10-31` was utilized during development and validation, and is not a fresh holdout.

---

## 2. Protocol 2: Realized Barrier Outcome & Trade Return Reconstruction

To eliminate the flawed assumption that nominal barrier parameters represent executable returns, Phase 5.4 reconstructs realized trade outcomes from canonical 5m OHLC data:

### 1. Position Entry Rules:
- Entry occurs at the close of candle $i$: $P_{\text{entry}} = \text{closes}[i]$.
- Volatility parameter: $\sigma_t = \text{volatility}[i]$ (rolling 20-candle std of returns).
- Nominal Upper Barrier: $U_i = P_{\text{entry}} \times (1.0 + 1.5 \sigma_t)$.
- Nominal Lower Barrier: $L_i = P_{\text{entry}} \times (1.0 - 1.5 \sigma_t)$.

### 2. Forward Horizon Evaluation ($k = 1, \dots, 12$):
For each candle $idx = i + k$ in the forward window:
- Check for Intrabar Double-Touch: If $\text{high}[idx] \ge U_i$ and $\text{low}[idx] \le L_i$:
  - Classified as `AMBIGUOUS` (Outcome -2). Excluded from clean evaluation in accordance with Phase 5.2/5.3 rules.
- First Touch Resolution:
  - If $\text{high}[idx] \ge U_i$: Upper barrier hit at step $k$. Position terminates immediately.
  - If $\text{low}[idx] \le L_i$: Lower barrier hit at step $k$. Position terminates immediately.
  - If neither hit: Proceed to $k+1$.
  - If neither hit through $k=12$: Position terminates by Time Expiration at $idx = i + 12$.

### 3. Exit Price & Gap Handling:
- **Upper Barrier Exit ($P_{\text{exit}}$):**
  - Normal touch: If $\text{open}[idx] < U_i \le \text{high}[idx]$, fill is modeled at limit price $U_i$.
  - Gap Open: If $\text{open}[idx] \ge U_i$, execution occurs at market open: $P_{\text{exit}} = \text{open}[idx]$.
- **Lower Barrier Exit ($P_{\text{exit}}$):**
  - Normal touch: If $\text{open}[idx] > L_i \ge \text{low}[idx]$, fill is modeled at stop price $L_i - \text{slippage}$.
  - Gap Open: If $\text{open}[idx] \le L_i$, gap execution occurs at market open: $P_{\text{exit}} = \text{open}[idx] - \text{slippage}$.
- **Time Expiration Exit ($P_{\text{exit}}$):**
  - Closed at market on candle close at $k=12$: $P_{\text{exit}} = \text{closes}[i + 12]$.

### 4. Realized Trade Return Formulations:
Gross percentage returns:
$$R_{\text{gross, long}} = \frac{P_{\text{exit}} - P_{\text{entry}}}{P_{\text{entry}}}$$
$$R_{\text{gross, short}} = \frac{P_{\text{entry}} - P_{\text{exit}}}{P_{\text{entry}}}$$

Net percentage returns incorporating friction:
$$R_{\text{net, long}} = R_{\text{gross, long}} - C_{\text{friction}}$$
$$R_{\text{net, short}} = R_{\text{gross, short}} - C_{\text{friction}}$$

---

## 3. Protocol 3: Transaction Cost & Friction Sensitivity Model

The 15 bps round-trip friction used in Phase 5.4.0 is recognized as a hypothetical scenario, not verified actual execution drag.

### Comprehensive Friction Sensitivity Grid:
Friction is formally parameterized across four distinct sensitivity scenarios:

| Friction Scenario | Exchange Fee Tier | Entry Order Type | Exit Order Type | Fee Drag (Round-Trip) | Bid-Ask Spread Drag | Execution Slippage | Total Round-Trip Drag ($C_{\text{friction}}$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Scenario A (VIP / Maker-Taker)** | VIP 3+ / Institutional | Maker (Limit) | Taker (Market/SL) | $2.0 + 3.5 = 5.5$ bps | $0.5$ bps | $1.0$ bps | **$7.0$ bps ($0.00070$)** |
| **Scenario B (Baseline Retail)** | VIP 0 (Binance standard) | Taker (Market) | Taker (Market/SL) | $5.0 + 5.0 = 10.0$ bps | $2.0$ bps | $3.0$ bps | **$15.0$ bps ($0.00150$)** |
| **Scenario C (Conservative Adverse)** | VIP 0 Retail | Taker (Market) | Taker (Market/SL) | $5.0 + 5.0 = 10.0$ bps | $4.0$ bps | $6.0$ bps | **$20.0$ bps ($0.00200$)** |
| **Scenario D (High-Vol / Stress)** | VIP 0 Retail | Taker (Market) | Taker (Stop-Market) | $5.0 + 5.0 = 10.0$ bps | $6.0$ bps | $14.0$ bps | **$30.0$ bps ($0.00300$)** |

**Unresolved Prerequisite:** The specific production exchange and target fee tier remain uncommitted in the codebase. All Phase 5.4 evaluations must report sensitivity across all four scenarios.

---

## 4. Protocol 4: Calibration Methodologies & Input Compatibility

### 1. Temperature Scaling Input Formulation:
Because `lgbm_model.joblib` natively outputs true unbounded margin logits $z \in \mathbb{R}^3$ via `predict(X, raw_score=True)`:
$$q_k(T) = \frac{\exp(z_k / T)}{\sum_{j=1}^3 \exp(z_j / T)}$$
- Fitted on Segment 1 by minimizing Cross-Entropy Loss over logits $z$.
- Class ordering verified strictly as: Index 0 = `-1` (SL), Index 1 = `0` (EXP), Index 2 = `+1` (TP).

### 2. Vector Platt Scaling:
Multinomial logistic regression fit on raw logits $z$ (or clipped log-odds $\ln(p / (1-p))$ with $\epsilon = 10^{-15}$):
$$q_k = \frac{\exp(\mathbf{w}_k^T \mathbf{z} + b_k)}{\sum_{j=1}^3 \exp(\mathbf{w}_j^T \mathbf{z} + b_j)}$$

### 3. Non-Parametric Isotonic Regression:
One-vs-Rest isotonic step curves fit independently per class: $\tilde{q}_k = g_k(p_k)$.
- Normalization: $q_k = \tilde{q}_k / \sum_{j=1}^3 \tilde{q}_j$.
- Zero-Probability Handling: If $\sum_{j=1}^3 \tilde{q}_j = 0$, fallback to the empirical training class prior $[\pi_{-1}, \pi_0, \pi_{+1}]$ to avoid division by zero.
- Data Scarcity Rule: Prohibited on XMRUSDT due to small sample size ($N_{\text{seg1}} \approx 6,100$).
