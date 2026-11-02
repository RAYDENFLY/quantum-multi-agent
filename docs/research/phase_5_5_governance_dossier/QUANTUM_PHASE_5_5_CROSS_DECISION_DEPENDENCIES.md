# QUANTUM PHASE 5.5: CROSS-DECISION DEPENDENCY MATRIX (REVISION 1.2)

**Document Status:** `APPROVED_FOR_HUMAN_REVIEW`  
**Revision:** `Revision 1.2 (Final Governance Closure Check)`  
**Publication Timestamp:** `2026-11-02 10:30:00 UTC`  
**Operational Mode:** `FINAL_GOVERNANCE_CLOSURE_AUDIT`  
**Associated Deliverable:** Cross-Decision Interaction Matrix (Task G)  

---

## 1. PAIRWISE DECISION INTERACTION MATRIX

The six governance decisions contain strict logical dependencies that dictate valid evaluation sequencing:

| Impacting Decision | Impacted Decision | Dependency Nature | Operational Consequence |
|---|---|---|---|
| **DEC_01** (Architecture) | **DEC_02** (Direction) | Structural | Estimand defines whether directional scope applies to symmetric re-anchored brackets (Alt B) or downstream strategy rules (Alt C). |
| **DEC_01** (Architecture) | **DEC_04** (Cost Gate) | Foundational | Primary estimand determines whether Gate 2 tests classifier utility ($E[R_{\text{net}}] > 0$) or complete trading strategy Sharpe ratio. |
| **DEC_06** (XMR Scope) | **DEC_04** (Hypothesis Family) | Sizing Constraint | Excluding XMR from primary portfolio fixes confirmatory family at $K=10$ (under Example A); including XMR requires $K=11$ with ragged missing history. |
| **DEC_03** (Funding Model) | **DEC_04** (Cost Gate) | Accounting Input | Funding cash-flow scenario determines net return trajectory across the 4-level acceptance hierarchy. |
| **DEC_02** (Direction) | **DEC_04** (Hypothesis Family) | Dimensionality | If Long and Short are prespecified as separate confirmatory hypotheses, $K$ doubles (e.g. $K=20$ or $K=22$). |
| **DEC_02** (Direction) | **DEC_05** (Concurrency) | Exposure Definition | Bidirectional trading permits simultaneous opposing positions or directional netting, altering gross notional exposure. |
| **DEC_06** (XMR Scope) | **DEC_05** (Fleet Size) | Capacity | Determines whether maximum fleet concurrency ceiling is 10 or 11 specialists. |
| **DEC_04** (Cost Gate) | **DEC_05** (Risk Controls) | Statistical Gate | Statistical significance hurdles must be satisfied before sizing rules or concurrency caps are operationally deployed. |

---

## 2. RECONCILED LOGICAL DECISION SEQUENCE

Decisions must be reviewed in this strict logical sequence to prevent circular reasoning and specification mismatch:

```
+-------------------------------------------------------------------------------+
| Step 1: DEC_01 (Barrier Execution Architecture)                               |
|         -> Selects Alternative B (Re-Anchored) or C (Strategy Development).   |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Step 2: DEC_06 (XMR Research & Portfolio Scope)                               |
|         -> Selects 10-asset (XMR standalone) or 11-asset primary universe.    |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Step 3: DEC_03 (Funding Rate Model)                                           |
|         -> Approves 4-scenario parametric sensitivity framework.              |
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
|         -> Enforces exposure caps, signed slippage, and stop budgeting.       |
+-------------------------------------------------------------------------------+
```
