# QUANTUM PHASE 5.5.0.8: FUNDING SETTLEMENT ELIGIBILITY AUDIT

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-01 21:25:00 UTC`  
**Associated Task:** Task C (Funding Settlement Eligibility)  
**Operational Mode:** `READ_ONLY_QUANTITATIVE_SPECIFICATION_AUDIT`  

---

## 1. CANONICAL FUNDING FORMULATION

The repository funding standard is:

`funding_rate_bps_per_settlement`

For each eligible settlement timestamp $t \in \{00:00, 08:00, 16:00\}$ UTC crossed during trade holding:

$$CF_t = -d \times N_{\text{settle}, t} \times f_{t, \text{decimal}}$$

$$CF_{\text{funding, total}} = \sum_{t=1}^k CF_t$$

where $N_{\text{settle}, t} = Q_t \times P_{\text{mark}, t}$ and $f_{t, \text{decimal}} = \frac{\text{funding\_rate\_bps\_per\_settlement}_t}{10,000}$.

---

## 2. SETTLEMENT ELIGIBILITY MATRIX & BOUNDARY RULES (C1)

We inspect the interaction between 5-minute discrete bar simulation and exchange matching engine funding snapshots:

| Trade Scenario | Position State at 00:00 / 08:00 / 16:00 UTC | Funding Eligibility ($CF_t$) | Operational Rationale | Verification Status |
|---|---|---|---|---|
| **Pre-Settlement Entry** | Entered at 07:45 UTC, closed at 08:15 UTC. | **ELIGIBLE** ($k=1$) | Position open across 08:00:00 snapshot. | `SOURCE_VERIFIED` |
| **Intra-Settlement Trade** | Entered at 09:15 UTC, closed at 14:30 UTC. | **INELIGIBLE** ($k=0$) | No discrete 8h timestamp crossed. | `SOURCE_VERIFIED` |
| **Multi-Settlement Hold** | Entered at 06:00 UTC, closed at 18:00 UTC. | **ELIGIBLE** ($k=2$) | Crosses both 08:00 and 16:00 snapshots. | `SOURCE_VERIFIED` |
| **Entry Exactly at Settlement** | Order fill timestamp is 08:00:00.000 UTC (`open[i+1]`). | **INELIGIBLE** | In AsterDEX / Binance engines, funding snapshot captures positions open *prior* to timestamp. New fills occur in the subsequent funding cycle. | `PASS_WITH_LIMITATIONS` (Venue assumption) |
| **Exit Exactly at Settlement** | Order fill timestamp is 08:00:00.000 UTC. | **ELIGIBLE** | Position was held through the preceding cycle until settlement. | `PASS_WITH_LIMITATIONS` (Venue assumption) |
| **Quantity Modification** | Partial fills or scaling during trade. | **UNSUPPORTED** | QUANTUM only supports $100\%$ full exits. | `SOURCE_VERIFIED` |

---

## 3. NOTIONAL AT SETTLEMENT SPECIFICATION (C2)

At each settlement event $t$, the notional value is evaluated dynamically:

$$N_{\text{settle}, t} = Q \times P_{\text{mark}, t}$$

- In historical OHLCV data without explicit tick-level mark prices, $P_{\text{mark}, t}$ is approximated by the candle open price at the settlement timestamp ($P_{\text{open}}[\text{bar}_{t}]$).
- **Prohibition:** The model must NOT assume $N_{\text{settle}, t} = N_{\text{entry}}$ across multi-day trades, as price trends significantly alter financing exposure.

---

## 4. NOMINAL ANNUALIZATION INVARIANT (C3)

The annualization relationship:

$$1095 = 3 \times 365$$

represents strictly a **nominal arithmetic scaling factor** for standardized reporting:

$$f_{\text{annual, nominal}} = f_{\text{settlement, bps}} \times 1095$$

### Strict Prohibitions
- Prohibited to describe this factor as **realized annual return**.
- Prohibited to describe this factor as **compounded annual yield**.
- Prohibited to describe this factor as **guaranteed funding income**.
- Prohibited to describe this factor as **an empirical predictive forecast**.
