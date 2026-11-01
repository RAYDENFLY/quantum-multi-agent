# QUANTUM PHASE 5.5.0.4: DEC_03 FUNDING RATE MODEL BRIEF

**Decision ID:** `DEC_03`  
**Title:** Funding Rate Model Approval  
**Governance Status:** `PENDING_HUMAN_DECISION`  
**Execution Blocking:** `YES`  

---

## 1. OPTIONS AND RESEARCH TRADE-OFFS

Forensic audit confirms that historical funding rates are absent from the canonical Parquet datasets (`FUNDING_DATA_UNAVAILABLE`). The supervisor must choose between two approaches:
1. **Option 1: Parametric Sensitivity Sweep:** Approve evaluating economic performance across four declared constant funding scenarios (`SCENARIO_F_NEUTRAL`, `SCENARIO_F_BULL_MODERATE`, `SCENARIO_F_BULL_SEVERE`, `SCENARIO_F_BEAR_MODERATE`).
2. **Option 2: Require Historical Funding Data Backfill:** Halt Phase 5.5 execution until an audited historical funding rate dataset from Binance/Bybit is acquired and ingested into the repository.

---

## 2. AUTHORITATIVE UNIT & MATHEMATICAL FORMULATION

- **Primary Unit:** `funding_rate_bps_per_settlement` (basis points per 8-hour window).
- **Nominal Annualization Formula:** $F_{\text{bps,annual}} = F_{\text{bps,settlement}} \times 1095$.
- **Cash Flow Formula:** $CF_t = -d \times N_t \times f_t$, where $d = +1$ (LONG), $d = -1$ (SHORT), $N_t$ is quote notional in USDT, and $f_t = F_{\text{bps,settlement}} / 10,000$.

### Scenarios Defined
- `SCENARIO_F_NEUTRAL`: 0.0 bps/settle (0.00% annual). Frictionless financing baseline.
- `SCENARIO_F_BULL_MODERATE`: +1.0 bps/settle (+10.95% annual). Standard baseline long drag.
- `SCENARIO_F_BULL_SEVERE`: +3.0 bps/settle (+32.85% annual). High bull market euphoria drag.
- `SCENARIO_F_BEAR_MODERATE`: -1.0 bps/settle (-10.95% annual). Standard bear market discount (shorts pay).

---

## 3. WHAT PARAMETRIC SWEEPS CAN AND CANNOT PROVE

- **What it CAN prove:** Whether the strategy has enough gross alpha to remain profitable if financing costs average 10.95% or 32.85% annualized against active positions.
- **What it CANNOT prove:** It cannot prove what realized historical financing cash flow actually occurred on specific days or whether trades entered during funding spikes.
- **Holding Exposure Reclassification:** The 87.5% non-crossing figure is formally classified as `THEORETICAL_UNDER_UNIFORM_ENTRY_AND_FIXED_HOLDING_ASSUMPTIONS`. Actual empirical crossing incidence will be measured directly as $N_{\text{settlement\_crossed}} / N_{\text{total\_trades}}$ during execution.

---

## 4. SUPERVISOR RECOMMENDATION

- **Recommendation:** Approve `Option 1 (Parametric Sensitivity Sweep)` for Phase 5.5 with explicit disclosure of `UNVERIFIED_ASSUMPTION` status. This avoids blocking research while maintaining complete transparency.
- **Status:** `PENDING_HUMAN_DECISION`. Awaiting supervisor selection.
