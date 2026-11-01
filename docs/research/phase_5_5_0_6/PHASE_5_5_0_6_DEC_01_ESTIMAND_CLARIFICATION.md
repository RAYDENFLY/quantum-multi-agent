# QUANTUM PHASE 5.5.0.6: DEC_01 ESTIMAND AND RESEARCH OBJECTIVE CLARIFICATION

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-01 21:09:14 UTC`  
**Associated Deliverable:** Workstream A (DEC_01 Estimand Correction)  

---

## 1. THE ESTIMAND CLARIFICATION PROBLEM

Phase 5.5.0.5 previously described Alternative B as 'direct validation of frozen triple-barrier alpha'. Forensic review reveals that this characterization is scientifically too strong.

### Mathematical Divergence Between ML Training Target and Economic Execution
1. **Frozen ML Target (System 1):** In Phase 5.3, models were trained on triple-barrier labels anchored strictly to candle $i$ close:
   $$P_{\text{ref}} = \text{close}[i], \quad u_t = P_{\text{ref}}(1 + 1.5\sigma_t), \quad l_t = P_{\text{ref}}(1 - 1.5\sigma_t)$$
2. **Economic Execution (System 2):** Orders cannot be filled at candle $i$ close without look-ahead latency violations. Execution occurs at candle $i+1$ open:
   $$P_{\text{entry}} = \text{open}[i+1] \pm C_{\text{exec}}$$
3. **Alternative B Economic Barriers:** Alternative B re-anchors economic barriers to actual entry fill:
   $$U_{\text{econ}} = P_{\text{entry}}(1 + 1.5\sigma_t), \quad L_{\text{econ}} = P_{\text{entry}}(1 - 1.5\sigma_t)$$

### Crucial Methodological Conclusion
Re-anchoring barriers to $P_{\text{entry}}$ changes the physical price levels of the barrier event. Consequently, positive economic expectancy under Alternative B demonstrates that the frozen classifier emits useful directional signals under a re-anchored execution policy, but it does NOT prove direct economic validation of the original close-anchored triple-barrier target labels.

---

## 2. THREE FORMAL RESEARCH OBJECTIVE DEFINITIONS

### Track 1: Frozen Target Predictive Validation
- **Question:** Does the frozen classifier predict the original close-anchored triple-barrier target with statistical skill above chance on evaluation data?
- **Status:** COMPLETE in Phase 5.3 and 5.4 (`PHASE_5_4_FROZEN_WITH_LIMITATIONS`).
- **Estimand:** Classification metrics (Balanced Accuracy, Log Loss, ECE, AU-RCC).
- **Boundary:** Does NOT measure trading profitability or net economic alpha.

### Track 2: Frozen Classifier Economic Evaluation Under Re-Anchored Execution
- **Question:** Does the frozen classifier produce economically useful directional information when evaluated using an independent economic execution rule anchored to actual entry price?
- **Specification:**
  - Frozen B4 LightGBM classifier and preprocessors remain 100% immutable.
  - Fills occur at $t_{\text{open}}[i+1]$ with adverse execution slippage $C_{\text{exec}}$.
  - Economic barriers re-anchor symmetrically to $P_{\text{entry}} \pm 1.5\sigma_t P_{\text{entry}}$.
  - Exits occur on first touch of $U_{\text{econ}}$, $L_{\text{econ}}$, or 12-bar expiration.
  - Modeled costs include taker fees, half-spread, volatility penalty, volume impact, and discrete funding.
- **Estimand:** Expected net trading return per trade ($E[R_{\text{net}}]$) under re-anchored barrier brackets.
- **Interpretation:** Positive outcome proves economic utility of classifier signals under re-anchored execution. Negative outcome proves lack of tradeable economic alpha under symmetric brackets.

### Track 3: Independent Trading Strategy Development
- **Question:** Can the frozen classifier function as a directional signal filter within a separately engineered systematic trading strategy?
- **Specification:**
  - Decouples classifier from static triple-barrier rules.
  - Implements trailing stops, ATR dynamic bands, time-decay exits, and position sizing.
  - Strategy parameters must be calibrated strictly on Folds 1 to 4 with Fold 5 held out.
- **Estimand:** Portfolio Sharpe ratio, Sortino ratio, and Maximum Drawdown of an algorithmic strategy.
- **Interpretation:** Tests a complete trading system. Conflates classifier skill with trade exit heuristics. Cannot be claimed as direct validation of the ML target.

---

## 3. GOVERNANCE RECOMMENDATION

- **Operational Relationship:** These are **Distinct Estimands** structured as **Sequential Research Tracks**.
- **Recommendation:** Execute Track 2 (Alternative B) as the primary mandatory baseline of Phase 5.5. Only explore Track 3 (Alternative C) in subsequent exploratory phases.
- **Status:** `PENDING_HUMAN_DECISION`. Awaiting supervisor selection.
