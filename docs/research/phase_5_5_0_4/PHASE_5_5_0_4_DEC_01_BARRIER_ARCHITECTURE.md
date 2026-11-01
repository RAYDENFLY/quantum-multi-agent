# QUANTUM PHASE 5.5.0.4: DEC_01 BARRIER EXECUTION ARCHITECTURE BRIEF

**Decision ID:** `DEC_01`  
**Title:** Barrier Execution Architecture Selection  
**Governance Status:** `PENDING_HUMAN_DECISION`  
**Execution Blocking:** `YES`  

---

## 1. MATHEMATICAL FORMULATION OF THE THREE ARCHITECTURES

In the frozen Phase 5.3 machine learning layer (System 1), target labels were constructed relative to candle $i$ close ($P_{\text{ref}} = \text{close}[i]$) with multiplicative barriers:
$$u_t = \text{close}[i] \times (1 + 1.5\sigma_t), \quad l_t = \text{close}[i] \times (1 - 1.5\sigma_t)$$
where $\sigma_t$ is the rolling 20-candle sample standard deviation of simple percentage returns (`ddof=1`).

In the economic execution layer (System 2), orders are submitted at bar close $i$ and filled at the opening of candle $i+1$ with adverse execution slippage:
$$P_{\text{entry}} = \text{open}[i+1] \times (1 + C_{\text{exec}}) \quad (\text{for BUY})$$

The core architectural question is: **How should take-profit (TP) and stop-loss (SL) barriers be established relative to the entry fill?**

### Alternative A: Original Barrier Preservation
- **Mechanism:** The trade retains the exact price levels defined at candle close $i$:
  $$P_{\text{tp}} = \text{close}[i] \times (1 + 1.5\sigma_t), \quad P_{\text{sl}} = \text{close}[i] \times (1 - 1.5\sigma_t)$$
- **Mathematical Rationale:** Preserves 100% fidelity to the original ML target definition.
- **Fatal Flaw (Gap Risk & Risk-Reward Inversion):** If candle $i+1$ opens with a $+2.0\%$ gap up in a $2.5\%$ volatility regime, $P_{\text{entry}}$ is already very close to $P_{\text{tp}}$. The remaining upside distance to TP shrinks to $+0.25\%$, while the downside distance to SL widens to $-4.25\%$. The original symmetric 1:1 risk-reward collapses to a disastrous 1:17 risk-reward inversion. This severely penalizes strong momentum breakouts.

### Alternative B: Re-Anchor Symmetric Barriers to Economic Entry Fill
- **Mechanism:** Economic barrier brackets are re-anchored symmetrically to the actual fill price at $t_{\text{open}}[i+1]$:
  $$P_{\text{tp}} = P_{\text{entry}} \times (1 + 1.5\sigma_t), \quad P_{\text{sl}} = P_{\text{entry}} \times (1 - 1.5\sigma_t)$$
- **Mathematical Rationale:** Perfectly preserves the 1:1 volatility bracket symmetry and target payoff geometry regardless of opening gap size.
- **Limitation:** Economic barrier outcomes may occasionally diverge from historical ML training labels when large gaps occur.

### Alternative C: Decouple Directional Classifier from Independent Trade Exit Policy
- **Mechanism:** System 1 serves strictly as a directional filter emitting calibrated probabilities $P(+1), P(0), P(-1)$. System 2 applies an independent algorithmic order management policy (e.g. trailing ATR stops, time-decay exits, volatility targets).
- **Mathematical Rationale:** Reflects modern institutional systematic trading architecture where predictive models predict direction, not rigid static brackets.
- **Limitation:** Introduces trade management parameters (trailing stop multiplier, holding time) that must be strictly fit on Folds 1 to 4 to avoid overfitting Fold 5.

---

## 2. COMPARISON MATRIX ACROSS 8 MANDATORY DIMENSIONS

| Dimension | Alternative A (Preserve) | Alternative B (Re-Anchor) | Alternative C (Decouple Policy) |
|---|---|---|---|
| 1. Economic Realism | Poor (Gap distortions warp PnL) | High (Standard volatility bracket execution) | Very High (Institutional trade management) |
| 2. Fidelity to ML Target | Exact (Labels match barrier levels) | High (Preserves volatility distance) | Moderate (Directional alignment only) |
| 3. Lookahead Bias Risk | Zero | Zero | Zero (Parameters fit on Folds 1-4 only) |
| 4. Latency Handling | Poor (Execution delay distorts R:R) | Robust (Entry price anchors brackets) | Robust (Dynamic execution logic) |
| 5. Gap Risk Handling | Catastrophic (1:5 to 1:17 adverse R:R) | Neutral (Brackets adjust to entry) | Controlled (Slippage and gap filters) |
| 6. Parameter Tuning Risk | None | None | Moderate (Exit parameters require validation) |
| 7. Risk-Reward Preservation | Severely Violated on Gaps | Perfectly Preserved (1:1) | Dynamically Managed |
| 8. Empirical Testability | Immediate on OOF data | Immediate on OOF data | Requires staged walk-forward protocol |

---

## 3. SUPERVISOR RECOMMENDATION & TRADE-OFF SUMMARY

- **Recommendation:** `Alternative B` for direct validation of the frozen triple-barrier predictive alpha, or `Alternative C` if the research objective is to validate a production systematic algorithmic trading strategy.
- **Alternative A should be rejected** because its risk-reward inversion unfairly penalizes the strategy during trending market regimes.
- **Status:** `PENDING_HUMAN_DECISION`. Awaiting supervisor selection.
