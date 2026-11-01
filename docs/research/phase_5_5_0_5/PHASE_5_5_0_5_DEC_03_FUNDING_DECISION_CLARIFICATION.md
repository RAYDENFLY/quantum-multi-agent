# QUANTUM PHASE 5.5.0.5: DEC_03 FUNDING DECISION CLARIFICATION

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-01 21:02:03 UTC`  
**Associated Deliverable:** Workstream E (DEC_03 Funding Model Clarification)  

---

## 1. WHAT PARAMETRIC SWEEPS CAN AND CANNOT PROVE

The supervisor faces an explicit trade-off between a parametric sensitivity sweep and requiring an external historical funding backfill:

### What a Parametric Sweep CAN Prove
- **Robustness Boundaries:** Proves whether the frozen classifier generates enough gross alpha to withstand persistent financing drags of $10.95\%$ or $32.85\%$ annualized.
- **Breakeven Thresholds:** Identifies the maximum financing cost rate a specialist can tolerate before net expectancy drops to zero.
- **Symmetry Stress:** Tests whether short trade funding credits offset execution slippage.

### What a Parametric Sweep CANNOT Prove
- **Historical Realized Net Profitability:** It cannot prove what realized net return an actual trader would have earned between 2023 and 2026. Without empirical funding rates, any net return figure is strictly a scenario simulation.
- **Calendar Drawdowns:** Constant funding assumptions smooth out financing spikes, failing to model real-world funding surges (e.g. 100%+ annual rates during liquidation cascades).

---

## 2. CANONICAL UNIT & CASH FLOW VERIFICATION

- **Standardized Unit:** `funding_rate_bps_per_settlement`.
- **Nominal Annualization:** $F_{\text{bps,annual}} = F_{\text{bps,settlement}} \times 1095$.
- **Cash Flow Formula:** $CF_t = -d \times N_t \times f_t$, where $d = +1$ (LONG) and $d = -1$ (SHORT).
- **Scenarios:** Neutral ($0.0\text{ bps}$), Moderate Bull ($+1.0\text{ bps} = +10.95\%\text{ ann}$), Severe Bull ($+3.0\text{ bps} = +32.85\%\text{ ann}$), Moderate Bear ($-1.0\text{ bps} = -10.95\%\text{ ann}$).
- **Timestamp Alignment:** Cash flow is calculated if and only if trade duration $[t_{\text{entry}}, t_{\text{exit}}]$ spans a discrete settlement timestamp (`00:00`, `08:00`, `16:00 UTC`).

### Supervisor Recommendation
- Approve `Parametric Sensitivity Sweep` as a preliminary robustness gate for Phase 5.5, with full disclosure of `UNVERIFIED_ASSUMPTION` status.
- Status: `PENDING_HUMAN_DECISION`.
