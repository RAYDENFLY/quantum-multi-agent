# QUANTUM PHASE 5.5: CROSS-DECISION DEPENDENCY MATRIX (REVISION 1)

**Document Status:** `APPROVED_FOR_HUMAN_REVIEW`  
**Revision:** `Revision 1 (Decision Consistency & Risk-Claim Correction)`  
**Publication Timestamp:** `2026-11-01 22:55:00 UTC`  
**Operational Mode:** `READ_ONLY_EVIDENCE_RECONCILIATION_AND_GOVERNANCE_DOCUMENTATION`  
**Associated Deliverable:** Cross-Decision Interaction Matrix (Task G)  

---

## 1. PAIRWISE DECISION INTERACTION MATRIX

The six governance decisions contain strict logical dependencies that dictate valid evaluation sequencing:

| Impacting Decision | Impacted Decision | Dependency Nature | Operational Consequence |
|---|---|---|---|
| **DEC_01** (Architecture) | **DEC_02** (Direction) | Structural | Estimand defines whether directional scope applies to symmetric re-anchored brackets (Alt B) or downstream strategy rules (Alt C). |
| **DEC_01** (Architecture) | **DEC_04** (Cost Gate) | Foundational | Primary estimand determines whether Gate 2 tests classifier utility ($E[R_{\text{net}}] > 0$) or complete trading strategy Sharpe ratio. |
| **DEC_06** (XMR Scope) | **DEC_04** (Hypothesis Family) | Sizing Constraint | Excluding XMR from primary portfolio fixes primary confirmatory family at $K=10$; including XMR sets $K=11$. DEC_06 must precede DEC_04. |
| **DEC_06** (XMR Scope) | **DEC_05** (Portfolio Risk) | Covariance Structure | Including XMR creates a ragged covariance matrix across 2023 to 2026. |
| **DEC_03** (Funding Model) | **DEC_04** (Cost Gate) | Arithmetic Offset | Funding cash flows shift the break-even gross return hurdle: $R_{\text{breakeven}} = c_{\text{rt}} - \frac{CF_{\text{funding}}}{N}$. DEC_03 must precede DEC_04. |
| **DEC_02** (Direction) | **DEC_04** (Hypothesis Multiplier) | Multiplicity Expansion | Directional reporting disaggregation expands secondary hypothesis family to $K=30$ (if $K=10$) or $K=33$ (if $K=11$). |
| **DEC_02** (Direction) | **DEC_05** (Concurrency & Leverage) | Exposure Multiplier | Bidirectional execution allows concurrent Long and Short positions, affecting gross notional and margin utilization. |
| **DEC_04** (Cost & Stats) | **DEC_05** (Concurrency & Risk) | Methodology Coupling | Continuous calendar-time portfolio resampling requires defining how concurrent positions are aggregated into a fleet equity curve. |

---

## 2. RECONCILED LOGICAL DECISION SEQUENCE

To respect all logical dependencies, the human supervisor should evaluate decisions in the following sequence:

```
+-------------------------------------------------------------------------------+
|                       RECONCILED DECISION SEQUENCING                          |
+-------------------------------------------------------------------------------+
| Step 1: DEC_01 (Estimand & Architecture)                                     |
|         -> Defines the primary research question and barrier mechanics.       |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Step 2: DEC_06 (Instrument Fleet Scope)                                       |
|         -> Resolves primary universe (K=10 vs K=11) and prevents ragged data. |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Step 3: DEC_03 (Funding Assumption Policy)                                    |
|         -> Establishes the financing cash flow bounds across scenarios.       |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Step 4: DEC_02 (Directional Scope: Evaluation vs Execution Permission)        |
|         -> Authorizes Long, Short, or Bidirectional execution reporting.      |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Step 5: DEC_04 (Cost Gate & Statistical Criteria)                             |
|         -> Sets binding hurdle, candidate bootstrap design, and K value.      |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Step 6: DEC_05 (Portfolio Concurrency & Risk Options)                         |
|         -> Enforces exposure caps and stop-loss risk budgeting options.       |
+-------------------------------------------------------------------------------+
```
