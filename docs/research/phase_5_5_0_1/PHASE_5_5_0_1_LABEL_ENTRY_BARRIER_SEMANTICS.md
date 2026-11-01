# QUANTUM PHASE 5.5.0.1: LABEL, ENTRY, AND BARRIER SEMANTICS SPECIFICATION

**Document Status:** `REQUIRES_HUMAN_DECISION`  
**Publication Timestamp:** `2026-11-01 20:29:46 UTC`  
**Repository:** `https://github.com/RAYDENFLY/quantum-multi-agent`  
**Associated Deliverable:** Workstream A (Label, Entry, and Barrier Semantics)  

---

## 1. SOURCE CODE AUDIT: EXISTING TRIPLE-BARRIER IMPLEMENTATION

Forensic inspection of [`src/quantum/features/labeling.py`](file:///d:/quantum-multi-agent/src/quantum/features/labeling.py) establishes the exact mathematical formulas used during label generation in Phase 5.2 and baseline training in Phase 5.3:

### Baseline Labeling Formulation (`labeling.py` lines 169-235)
- **Signal / Reference Timestamp:** $t_{\text{sig}} = t_{\text{close}}[i]$ (close of candle $i$).
- **Reference Price:** $P_{\text{ref}} = \text{close}[i]$ (closing price of candle $i$).
- **Volatility Metric ($\sigma_t$):** Sample standard deviation (`ddof=1`) of 5m simple percentage returns over rolling 20 candles prior to candle $i$ (clipped below by $10^{-6}$).
- **Upper Barrier ($u$):** $u = P_{\text{ref}} \times (1.0 + 1.5 \times \sigma_t)$.
- **Lower Barrier ($l$):** $l = P_{\text{ref}} \times (1.0 - 1.5 \times \sigma_t)$.
- **Label Horizon:** Exactly $H = 12$ candles of 5m duration ($60$ minutes).
- **Ground-Truth Label Outcomes:**
  - $+1$ (`TP`): First barrier touched across candles $j \in [i+1, i+12]$ is $\text{high}[j] \ge u$.
  - $-1$ (`SL`): First barrier touched across candles $j \in [i+1, i+12]$ is $\text{low}[j] \le l$.
  - $0$ (`TIME_EXPIRATION`): Neither barrier touched within 12 candles.
  - $-2$ (`AMBIGUOUS`): Both barriers touched in the same 5m candle.

---

## 2. THE ENTRY GAP PROBLEM & RISK-REWARD DISTORTION

In real-world execution, an algorithmic decision generated at candle close $t_{\text{close}}[i]$ is executed at the next candle open $t_{\text{open}}[i+1]$.

### Mandatory Gap Investigation Example
Consider the concrete scenario specified by the research audit:
- Signal candle close: $P_{\text{ref}} = \text{close}[i] = 100.00$.
- Next candle open: $P_{\text{entry}} = \text{open}[i+1] = 102.00$ ($+2.00\%$ opening gap).
- Volatility: $\sigma_t = 0.02$ ($2.00\%$), with barrier multiplier $M = 1.5$.
- Original barriers computed at candle $i$:
  $$u = 100.00 \times (1 + 1.5 \times 0.02) = 103.00$$
  $$l = 100.00 \times (1 - 1.5 \times 0.02) = 97.00$$

### Economic Distortion Analysis
If a LONG position enters at the actual opening price of $102.00$ while retaining the original label barriers ($u=103.00, l=97.00$):
1. **Remaining Distance to Target (TP):** $103.00 - 102.00 = +1.00$ points ($+0.98\%$).
2. **Remaining Distance to Stop (SL):** $97.00 - 102.00 = -5.00$ points ($-4.90\%$).
3. **Risk-Reward Collapse:** The planned symmetric $1:1$ risk-reward ratio ($+3.00\% / -3.00\%$) collapses to an adverse **$1 : 5$ ratio** ($+0.98\% / -4.90\%$)!
4. **Premature Boundary Breach:** If the opening gap had been $+3.50\%$ (opening at $103.50$), the upper barrier was already breached before execution could even occur. In Phase 5.4.2 simulation, this was logged as an instantaneous exit at open, capturing $+1.47\%$ without market holding risk.

---

## 3. SEPARATION OF CONCEPTS

Phase 5.5.0.1 formally defines six distinct quantitative concepts to prevent conflating labels with executable positions:

1. **`LABEL_OUTCOME`:** The categorical label $y_i \in \{-1, 0, +1\}$ generated relative to $P_{\text{ref}} = \text{close}[i]$ over $[i+1, i+12]$. This is a statistical target variable, not a trading position.
2. **`ECONOMIC_ENTRY`:** The executable order event occurring at timestamp $t_{\text{entry}} = t_{\text{open}}[i+1]$ with executed price $P_{\text{entry}} = \text{open}[i+1]$ (plus entry slippage).
3. **`ECONOMIC_STOP`:** The price level $P_{\text{stop}}$ at which the position is closed to limit adverse loss.
4. **`ECONOMIC_TARGET`:** The price level $P_{\text{target}}$ at which the position is closed to lock in favorable gain.
5. **`ECONOMIC_EXIT`:** The actual liquidation event at $t_{\text{exit}}$ with executed price $P_{\text{exit}}$ (triggered by target, stop, expiration, or gap).
6. **`REALIZED_RETURN`:** The executable percentage return after all fees, slippage, and funding.

---

## 4. EVALUATION OF THE THREE ARCHITECTURAL ALTERNATIVES

Phase 5.5.0.1 explicitly formulates three distinct execution architectures for human review:

### Alternative A: Preserve Original Label Barriers
- **Mechanism:** Entry at $\text{open}[i+1]$, but exit targets remain $u = \text{close}[i] \times (1 + 1.5\sigma_t)$ and $l = \text{close}[i] \times (1 - 1.5\sigma_t)$.
- **Statistical Implication:** Exactly tests whether the ML label classification corresponds to executable profit given entry delay.
- **Economic Implication:** Severe risk-reward distortion on gapped opens; asymmetrical payoff distribution; requires discarding trades where open gaps past target.
- **Governance Status:** `EVALUATED_NOT_RECOMMENDED`.

### Alternative B: Re-Anchor Economic Barriers to Actual Entry Price
- **Mechanism:** When entering at $\text{open}[i+1]$, establish new symmetric economic barriers anchored to fill price:
  $$P_{\text{target, long}} = \text{open}[i+1] \times (1.0 + 1.5 \times \sigma_t)$$
  $$P_{\text{stop, long}} = \text{open}[i+1] \times (1.0 - 1.5 \times \sigma_t)$$
- **Economic Implication:** Restores clean, symmetric $1:1$ risk-reward ($+1.5\sigma_t / -1.5\sigma_t$) on every trade.
- **Statistical Implication:** Introduces a minor distribution shift relative to the ML prediction horizon (the model predicted a touch relative to $\text{close}[i]$, but execution evaluates a touch relative to $\text{open}[i+1]$).
- **Governance Status:** `RECOMMENDED_CANDIDATE_1`.

### Alternative C: Decouple Direction Signal from Trade Exit Policy
- **Mechanism:** Treat the ML model output strictly as a directional probability signal ($P(+1) > \theta_{\text{long}}$, $P(-1) > \theta_{\text{short}}$). Design an independent, professional trading execution policy (e.g. ATR trailing stops, volatility bands, fixed holding time).
- **Economic Implication:** Industry-standard quantitative trading practice. Separates statistical signal discovery from trade execution engineering.
- **Statistical Implication:** Requires validating the new exit policy independently on validation folds (Folds 3-4) to prevent look-ahead bias.
- **Governance Status:** `RECOMMENDED_CANDIDATE_2`.

---

## 5. DIRECTIONAL SYMMETRY & MATHEMATICAL FORMULAS

### LONG Position Execution Formulas
- **Trigger Condition:** $P(+1) > \theta_{\text{long}}$ and $P(+1) > P(-1)$.
- **Entry:** Executed at $P_{\text{entry}} = \text{open}[i+1]$.
- **Economic Target:** $P_{\text{target}} = P_{\text{entry}} \times (1 + 1.5\sigma_t)$ (under Alternative B).
- **Economic Stop:** $P_{\text{stop}} = P_{\text{entry}} \times (1 - 1.5\sigma_t)$ (under Alternative B).
- **Gross Return:** $R_{\text{gross, long}} = \frac{P_{\text{exit}} - P_{\text{entry}}}{P_{\text{entry}}}$.
- **Net Return:** $R_{\text{net, long}} = R_{\text{gross, long}} - C_{\text{fee}} - C_{\text{slip}} - C_{\text{fund}}$.

### SHORT Position Execution Formulas
- **Trigger Condition:** $P(-1) > \theta_{\text{short}}$ and $P(-1) > P(+1)$.
- **Entry:** Executed at $P_{\text{entry}} = \text{open}[i+1]$.
- **Economic Target:** $P_{\text{target}} = P_{\text{entry}} \times (1 - 1.5\sigma_t)$ (downward target).
- **Economic Stop:** $P_{\text{stop}} = P_{\text{entry}} \times (1 + 1.5\sigma_t)$ (upward stop).
- **Gross Return:** $R_{\text{gross, short}} = \frac{P_{\text{entry}} - P_{\text{exit}}}{P_{\text{entry}}}$.
- **Net Return:** $R_{\text{net, short}} = R_{\text{gross, short}} - C_{\text{fee}} - C_{\text{slip}} - C_{\text{fund}}$.

### Gap and Collision Resolution Rules
1. **Gap-Through-Stop:** If a candle opens past the stop level (e.g. $\text{open}[j] < P_{\text{stop}}$ for LONG), fill price is $\text{open}[j]$, NOT $P_{\text{stop}}$ (capturing true adverse gap slippage).
2. **Gap-Through-Target:** If a candle opens past target (e.g. $\text{open}[j] > P_{\text{target}}$ for LONG), fill price is $P_{\text{target}}$ (conservative: assumes limit order filled at limit price).
3. **Ambiguous Same-Candle Collision:** Adverse assumption mandatory: LONG hits Stop Loss; SHORT hits Stop Loss.
