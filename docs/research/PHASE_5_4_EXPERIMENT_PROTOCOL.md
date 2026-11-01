# QUANTUM PHASE 5.4: EXPERIMENT PROTOCOL & SPECIFICATION
**Detailed Implementation Protocols, Mathematical Formulations & Execution Guide**

**Document Version:** 5.4.0_PROTOCOL  
**System:** QUANTUM 11-Specialist Cryptocurrency Perpetual Futures ML Trading Research System  
**Governance Status:** `PROTOCOL_SPECIFICATION_AWAITING_EXPLICIT_AUTHORIZATION`  
**Classification Standards:** `VERIFIED_FROM_SOURCE` | `VERIFIED_FROM_ARTIFACT` | `DOCUMENTATION_ONLY`

---

## 1. Protocol 1: Chronological OOF Temporal Partitioning

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

### Justification of Partition Boundaries:
1. **Segment 1 (Calibration Fit: Folds 1 & 2):**
   - Timestamp Range: `2025-01-29 04:40 UTC` to `2025-07-30 11:10 UTC`.
   - Sample Size: 52,290 bars per standard instrument ($N \approx 522,900$ fleet-wide).
   - Function: Fits calibrator parameters ($A_k, B_k$ in Platt; $T$ in Temperature; step curves in Isotonic).
   - Leakage Protection: Calibrators are fitted strictly on OOF predictions from models that were trained on data prior to `2025-01-29`.
2. **Segment 2 (Policy Selection & Tuning: Folds 3 & 4):**
   - Timestamp Range: `2025-07-30 12:15 UTC` to `2026-01-29 07:45 UTC`.
   - Sample Size: 52,290 bars per standard instrument ($N \approx 522,900$ fleet-wide).
   - Function: Selects optimal confidence thresholds $\tau$, minimum coverage targets, and cost-sensitive net expectancy cutoffs $\theta$.
   - Leakage Protection: Calibrator parameters were fixed in Segment 1; policy thresholds are selected on Segment 2 data unseen by Segment 1.
3. **Segment 3 (Final Out-of-Sample Policy Evaluation: Fold 5):**
   - Timestamp Range: `2026-01-29 08:50 UTC` to `2026-04-30 21:55 UTC`.
   - Sample Size: 26,148 bars per standard instrument ($N \approx 261,480$ fleet-wide).
   - Function: Evaluates final frozen calibration quality, selective accuracy, risk-coverage curves, and net trade expectancy.
   - Leakage Protection: Zero parameter fitting or threshold tuning is permitted on Segment 3.

### 1.1 Strict Holdout Isolation Boundary
The prospective holdout partition (`2026-11-01 00:00:00 UTC` through `2027-04-30 23:59:59.999 UTC`) remains completely sealed and protected. Zero queries, feature lookups, or calibrator evaluations shall touch or reference this window. Furthermore, the historical period through `2026-10-31` was utilized during development and validation, and is not a fresh holdout.

---

## 2. Protocol 2: Candidate Calibration Methodologies

For each specialist instrument, four probability estimation models are benchmarked:

### 1. Uncalibrated Baseline (Raw Softmax)
Direct probability output from LightGBM:
$$p_{i,k} = \frac{\exp(z_{i,k})}{\sum_{j=1}^3 \exp(z_{i,j})}$$

### 2. Temperature Scaling (Guo et al., 2017)
A single scalar parameter $T > 0$ applied across logits:
$$q_{i,k} = \frac{\exp(z_{i,k} / T)}{\sum_{j=1}^3 \exp(z_{i,j} / T)}$$
- Fitted on Segment 1 by minimizing Cross-Entropy Loss (Log Loss):
  $$\min_{T > 0} - \frac{1}{N_1} \sum_{i=1}^{N_1} \sum_{k=1}^3 y_{i,k} \ln(q_{i,k}(T))$$
- Properties: Preserves classification ranking ($z_a > z_b \iff z_a/T > z_b/T$), perfectly monotonic, highly sample-efficient (1 parameter), prevents overconfidence.

### 3. Vector Platt / Sigmoid Scaling (Platt, 1999)
Multinomial logistic regression fit on uncalibrated log-odds:
$$q_{i,k} = \frac{\exp(\mathbf{w}_k^T \mathbf{z}_i + b_k)}{\sum_{j=1}^3 \exp(\mathbf{w}_j^T \mathbf{z}_i + b_j)}$$
- Parameters: 9 weights + 3 biases ($12$ parameters total).
- L2-regularization enforced ($C=1.0$) to prevent parameter explosion.

### 4. Non-Parametric Isotonic Regression (Zadrozny & Elkan, 2002)
One-vs-Rest piecewise constant isotonic regressions fit independently per class:
$$\tilde{q}_{i,k} = g_k(p_{i,k})$$
Followed by post-hoc normalization:
$$q_{i,k} = \frac{\tilde{q}_{i,k}}{\sum_{j=1}^3 \tilde{q}_{i,j}}$$
- Properties: Free-form non-parametric fitting; captures arbitrary monotonic distortions; requires large sample size ($N > 20,000$).

---

## 3. Protocol 3: Calibration Evaluation Metrics & Reliability Diagrams

Calibration quality is assessed using three formal mathematical metrics:

### 1. Multiclass Brier Score
$$\text{BS} = \frac{1}{N} \sum_{i=1}^N \sum_{k=1}^3 (q_{i,k} - y_{i,k})^2, \quad y_{i,k} \in \{0, 1\}$$
- Minimum: 0.0 (perfect probabilistic forecast).
- Reference: B0 Majority baseline produces $\text{BS}_{\text{B0}} \approx 0.6667$.

### 2. Log Loss (Multiclass Cross-Entropy)
$$\text{LL} = - \frac{1}{N} \sum_{i=1}^N \sum_{k=1}^3 y_{i,k} \ln(\max(\epsilon, \min(1-\epsilon, q_{i,k}))), \quad \epsilon = 10^{-15}$$

### 3. Expected Calibration Error (ECE)
Evaluated across $M = 15$ bins using both:
- **Equal-Width Bins:** Bin boundaries at $[0, 1/15, 2/15, \dots, 1]$.
- **Equal-Frequency Bins:** Quantile-based binning ensuring equal sample counts per bin.

For class-wise ECE:
$$\text{ECE}_k = \sum_{m=1}^M \frac{|B_{m,k}|}{N} \left| \text{acc}(B_{m,k}) - \text{conf}(B_{m,k}) \right|$$
$$\text{ECE}_{\text{macro}} = \frac{1}{3} \sum_{k=1}^3 \text{ECE}_k$$

**Binning Governance Rules:**
- Bin count: $M = 15$.
- Minimum observation threshold: $N_{\text{min}} = 100$ samples per bin.
- Empty bin handling: Bins with $< 100$ samples contribute zero to the weighted sum and are flagged in the diagnostics.

---

## 4. Protocol 4: Selective Classification & Confidence Abstention

The decision engine outputs three discrete operational actions:
$$\text{Action}_t \in \{\text{LONG}, \text{SHORT}, \text{NO\_TRADE}\}$$

### Abstention Mechanism:
1. **Directional Conviction Filter:**
   A trade candidate is considered only if predicted probability exceeds the empirical base rate plus an uncertainty margin $\delta$:
   $$\text{LONG Candidate if } q_{t,+1} \ge \tau_{\text{long}}$$
   $$\text{SHORT Candidate if } q_{t,-1} \ge \tau_{\text{short}}$$
2. **Neutral Exclusion:**
   If the expiration probability dominates ($q_{t,0} > \max(q_{t,+1}, q_{t,-1})$), the action defaults to $\text{NO\_TRADE}$.
3. **Margin-Based Uncertainty Filter:**
   Even if $q_{t,+1} > q_{t,-1}$, if $|q_{t,+1} - q_{t,-1}| < \Delta_{\text{margin}}$, conviction is deemed insufficient, resulting in $\text{NO\_TRADE}$.

### Evaluated Coverage Grid:
Coverage is systematically scanned across eight discrete levels:
$$\text{Coverage} \in \{20\%, 30\%, 40\%, 50\%, 60\%, 70\%, 80\%, 100\%\}$$
Where:
$$\text{Coverage} = \frac{N_{\text{LONG}} + N_{\text{SHORT}}}{N_{\text{total}}}$$

### Selective Classification Metrics:
- **Selective Balanced Accuracy ($\text{BA}_{\text{sel}}$):** Macro-average of recall on covered non-abstained bars.
- **Risk-Coverage Slope ($\beta_{\text{RC}}$):** Slope of linear regression of error rate against coverage. A valid selective classifier must exhibit $\beta_{\text{RC}} > 0$ (error decreases as coverage decreases).

---

## 5. Protocol 5: Cost-Sensitive Decision Policy & Expected Net Payoff

### Triple-Barrier to Return Mapping:
The triple-barrier label does not directly define trade return. The actual gross percentage return depends on the dynamic volatility barrier:
$$R_{\text{TP}, t} = + 1.5 \times \frac{\text{ATR}_{20, t}}{P_t}$$
$$R_{\text{SL}, t} = - 1.5 \times \frac{\text{ATR}_{20, t}}{P_t}$$
$$R_{\text{EXP}, t} = \frac{P_{t+12} - P_t}{P_t} \quad (\text{realized close-to-close return at bar 12})$$

### Execution Drag Matrix ($C_{\text{roundtrip}}$):
All cryptocurrency perpetual futures execution involves mandatory frictional costs:
1. **Exchange Trading Fees:**
   - Maker (limit order): $2.0$ bps per side.
   - Taker (market order): $5.0$ bps per side.
   - Conservative Research Baseline: Taker entry + Taker exit = $10.0$ bps round-trip ($0.0010$).
2. **Bid-Ask Spread Drag:**
   - Majors (BTC, ETH): $1.0$ bps ($0.0001$).
   - Mid-caps (SOL, BNB, DOGE, XRP): $2.0$ bps ($0.0002$).
   - Lower-liquidity / High-vol (AVAX, LINK, LTC, ADA, XMR): $3.0$ to $5.0$ bps.
3. **Slippage Drag:**
   - Model entry execution slippage: $2.0$ bps.
   - Stop-loss market order slippage: $3.0$ bps.
4. **Funding Rate Cost:**
   - 8-hour funding rate amortized across holding period (up to 1 hour): $\approx 0.5$ bps.

**Total Round-Trip Friction Baseline:**
$$C_{\text{roundtrip}} = 10.0 \text{ bps (fees)} + 2.0 \text{ bps (spread)} + 3.0 \text{ bps (slippage)} = 15.0 \text{ bps } (0.00150)$$

### Expected Net Return Formulation:
For a candidate LONG position:
$$\mathbb{E}[R_{\text{net, long}, t}] = q_{t,+1} \cdot R_{\text{TP}, t} + q_{t,-1} \cdot R_{\text{SL}, t} + q_{t,0} \cdot \bar{R}_{\text{EXP}} - C_{\text{roundtrip}}$$

For a candidate SHORT position:
$$\mathbb{E}[R_{\text{net, short}, t}] = q_{t,-1} \cdot R_{\text{TP}, t} + q_{t,+1} \cdot R_{\text{SL}, t} - q_{t,0} \cdot \bar{R}_{\text{EXP}} - C_{\text{roundtrip}}$$

### Decision Rule:
$$\text{Action}_t = \begin{cases} \text{LONG}, & \text{if } \mathbb{E}[R_{\text{net, long}, t}] > \theta_{\text{min}} \text{ and } q_{t,+1} > q_{t,-1} \\ \text{SHORT}, & \text{if } \mathbb{E}[R_{\text{net, short}, t}] > \theta_{\text{min}} \text{ and } q_{t,-1} > q_{t,+1} \\ \text{NO\_TRADE}, & \text{otherwise} \end{cases}$$
Where $\theta_{\text{min}} \ge 0.0005$ ($5.0$ bps minimum positive expectancy hurdle).

---

## 6. Protocol 6: Robustness, Regime & Data Sufficiency Standards

1. **Independent Evaluation (No Fleet Pooling):** Calibrators and decision policies must be fitted and evaluated independently per instrument. Pooling across instruments into a single universal calibrator is prohibited without prior hypothesis authorization.
2. **Market Regime Segmentation:** Segment 3 evaluation will report performance conditional on:
   - Trend Regime: ADX(14) $> 25$ (Trending) vs $\le 25$ (Ranging).
   - Volatility Regime: Realized 20-bar volatility above vs below 50th historical percentile.
3. **XMRUSDT Special Handling:**
   - XMRUSDT has only 30,703 Research-Ready candles and 15,252 OOF bars (approx. 3,050 bars per fold).
   - Segment 1 sample size for XMR is only $\approx 6,100$ bars, which is insufficient for 15-bin Isotonic regression.
   - XMR is restricted to Temperature Scaling and Vector Platt Scaling; Isotonic regression is prohibited for XMR due to data scarcity.
