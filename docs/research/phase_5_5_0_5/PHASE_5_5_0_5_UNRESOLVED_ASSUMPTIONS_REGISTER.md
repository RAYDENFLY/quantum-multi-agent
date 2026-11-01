# QUANTUM PHASE 5.5.0.5: UNRESOLVED ASSUMPTIONS REGISTER

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-01 21:02:03 UTC`  
**Associated Deliverable:** Master Governance Challenge  

---

## 1. COMPREHENSIVE INVENTORY OF ACTIVE UNVERIFIED ASSUMPTIONS

| ID | Assumption Description | Location in Design | Epistemic Status | Risk of Inaccuracy | Validation Requirement |
|---|---|---|---|---|---|
| **ASM_01** | Constant parametric funding rates (0, +1, +3, -1 bps/settle) represent historical market conditions. | DEC_03 Brief | `UNVERIFIED_ASSUMPTION` | Moderate: Ignores stochastic funding rate spikes and regimes. | Historical funding dataset backfill from exchange APIs. |
| **ASM_02** | Slippage model return std multiplier $\alpha = 0.05$ and participation multiplier $\beta = 0.0010$. | Slippage Model | `UNVERIFIED_ASSUMPTION` | High: Theoretical heuristics not calibrated on crypto orderbook tick data. | L2/L3 order book depth audit. |
| **ASM_03** | Exactly 87.5% of positions incur zero funding cash flow. | Funding Model | `THEORETICAL_UNDER_UNIFORM_ENTRY_AND_FIXED_HOLDING_ASSUMPTIONS` | Moderate: Trade clustering alters actual crossing rate. | Empirical measurement during backtest ($N_{\text{cross}} / N_{\text{total}}$). |
| **ASM_04** | Cryptocurrency cross-asset correlation is static and $\rho > 0.70$. | DEC_05 Brief | `DOMAIN_STYLIZED_FACT_UNVERIFIED_IN_DATASET` | High: Correlation drops during altcoin regimes, altering risk. | Compute empirical rolling correlation matrix from canonical 5m data. |
| **ASM_05** | Exchange taker commission fee is exactly 5.0 bps (Base) or 6.0 bps (Conservative). | Cost Specification | `UNVERIFIED_ASSUMPTION` | Low to Moderate: Retail fees vary by VIP tier and exchange. | Audit specific exchange fee schedule. |
| **ASM_06** | Allocating 1.0% risk-at-stop across 3 positions guarantees max 3.0% portfolio loss. | Portfolio Risk | `INVALIDATED_THEORETICAL_ASSUMPTION` | Critical: Opening gaps and slippage blowouts cause losses > 3.0%. | Implement conservative liquidation margin buffers. |
