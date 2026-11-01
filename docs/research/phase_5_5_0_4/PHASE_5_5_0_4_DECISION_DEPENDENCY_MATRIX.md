# QUANTUM PHASE 5.5.0.4: DECISION DEPENDENCY MATRIX

**Document Status:** `APPROVED_FOR_DESIGN`  
**Publication Timestamp:** `2026-11-01 20:56:06 UTC`  

---

## 1. PAIRWISE INTERACTION ANALYSIS

A decision in one workstream directly constrains or modifies the consequences of decisions in other workstreams:
1. **DEC_01 (Barrier Architecture) & DEC_04 (Cost Gate):** Alternative A suffers severe risk-reward collapse on gaps, making clearing a 20 bps cost gate nearly impossible. Alternative B or C preserves symmetric brackets, giving a fair test against the 20 bps hurdle.
2. **DEC_02 (Directional Scope) & DEC_03 (Funding Model):** Funding rates are signed ($CF_t = -d \times N_t \times f_t$). If Long-only is selected, positive funding rates act strictly as a drag. If Bidirectional is selected, Short positions earn funding credits during bull regimes, partially offsetting transaction costs.
3. **DEC_02 (Directional Scope) & DEC_05 (Portfolio Risk):** Bidirectional trading roughly doubles potential simultaneous trade signals, increasing contention for the 3-position concurrency cap.
4. **DEC_04 (Cost Gate) & DEC_05 (Portfolio Risk):** Transaction costs scale linearly with trade count. Higher leverage and higher turnover increase total frictional drag on portfolio equity.
5. **DEC_05 (Portfolio Risk) & DEC_06 (XMR Scope):** Excluding XMR reduces the specialist pool from 11 to 10, slightly lowering concurrency contention during market-wide signals.
6. **DEC_01 (Barrier Architecture) & DEC_02 (Directional Scope):** The chosen execution architecture must support both Long and Short bracket logic with appropriate adverse execution fill signs.

---

## 2. FORMAL 6x6 DEPENDENCY MATRIX

| Decision | DEC_01 (Barrier) | DEC_02 (Direction) | DEC_03 (Funding) | DEC_04 (Cost Gate) | DEC_05 (Risk/Leverage) | DEC_06 (XMR Scope) |
|---|---|---|---|---|---|---|
| **DEC_01** | - | Independent | Independent | **Strong Impact** | Low Impact | Independent |
| **DEC_02** | Independent | - | **Strong Impact** | Moderate Impact | **Strong Impact** | Low Impact |
| **DEC_03** | Independent | **Strong Impact** | - | Moderate Impact | Low Impact | Independent |
| **DEC_04** | **Strong Impact** | Moderate Impact | Moderate Impact | - | Moderate Impact | Low Impact |
| **DEC_05** | Low Impact | **Strong Impact** | Low Impact | Moderate Impact | - | Moderate Impact |
| **DEC_06** | Independent | Low Impact | Independent | Low Impact | Moderate Impact | - |

---

## 3. RECOMMENDED LOGICAL DECISION SEQUENCE

To avoid circular rework, the human supervisor should evaluate the decisions in the following sequence:
1. **Step 1: DEC_01 (Barrier Architecture)** - Defines how orders enter and exit the market.
2. **Step 2: DEC_02 (Directional Scope)** - Establishes whether both Long and Short pipelines are evaluated.
3. **Step 3: DEC_04 (Cost Gate Tier)** - Establishes the mandatory break-even hurdle for Gate 2.
4. **Step 4: DEC_05 (Portfolio Risk & Concurrency)** - Establishes maximum leverage and simultaneous position caps.
5. **Step 5: DEC_06 (XMR Universe Scope)** - Finalizes whether primary portfolio runs on 10 or 11 assets.
6. **Step 6: DEC_03 (Funding Model Approval)** - Authorizes the parametric sensitivity sweep.
