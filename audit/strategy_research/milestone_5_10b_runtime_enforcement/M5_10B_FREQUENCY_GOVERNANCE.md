# QUANTUM — MILESTONE 5.10B
## TRADE FREQUENCY GOVERNANCE, MULTI-TIER AUDITING & SELECTION STANDARDS

---

### 1. EXECUTIVE SUMMARY

- **Milestone Designation:** Milestone 5.10B (Execution Economics & Runtime Enforcement Verification)
- **Git Branch:** `research/quantum-next-3pct`
- **Location:** `audit/strategy_research/milestone_5_10b_runtime_enforcement/M5_10B_FREQUENCY_GOVERNANCE.md`
- **Objective:** Establish formal frequency governance standards, multi-tier metric reporting, and non-rejection rules for statistically valid alpha candidates.
- **Key Governance Directives:**
  1. **Primary Research Target:** QUANTUM maintains **10–100 completed trade episodes per day** as the primary high-frequency intraday research target.
  2. **Non-Rejection of Statistically Valid Candidates:** A research candidate that demonstrates genuine statistical significance, positive net expectancy, unlevered exposure ($\le 1.0x$), and $\ge 3.00\%$ net daily return under AsterDEX retail fees is **never rejected solely because its empirical frequency is $< 10.0$ episodes/day**. It is accurately classified as **Category B (Intraday Low-Frequency)**.
  3. **Strict Prohibition of Forced Trading:** Strategy generators, analysts, and optimization loops must never loosen entry filters, degrade z-score thresholds, or force trades artificially to satisfy a frequency target. Frequency must be an emergent property of genuine edge.
  4. **Four-Tier Frequency Accounting:** All performance reports must evaluate frequency across four separate dimensions: per-symbol, portfolio-wide, active trading days, and full calendar days.

---

### 2. ARCHITECTURAL CATEGORIZATION VS REJECTION POLICY

To avoid the twin traps of accepting low-frequency swing models as high-frequency alpha (the Track C error) or discarding profitable strategies simply because they trade selectively, QUANTUM enforces a tripartite classification taxonomy:

```
+-----------------------------------------------------------------------------------------------------------------------+
| QUANTUM ALPHA CLASSIFICATION TAXONOMY                                                                                 |
+------------+---------------------------+-----------------------+---------------------+----------------------------------+
| Category   | Nomenclature              | Frequency Threshold   | Holding Horizon     | Admissibility Policy             |
+------------+---------------------------+-----------------------+---------------------+----------------------------------+
| CATEGORY A | High-Frequency Intraday   | >= 10.0 episodes/day  | 15m to 240m (4h)    | Primary Charter Target           |
| CATEGORY B | Intraday Low-Frequency    | 1.0 to 9.99 eps/day   | 15m to 240m (4h)    | ADMISSIBLE (Statistically Valid) |
| CATEGORY C | Swing / Multi-Day         | < 1.0 episodes/day    | Multi-Day (> 240m)  | Special Approval & Justification |
| CATEGORY D | Invalid / Misconfigured   | Zero trades / Erratic | Non-compliant       | REJECTED / DISQUALIFIED          |
+------------+---------------------------+-----------------------+---------------------+----------------------------------+
```

#### 2.1 Non-Rejection Governance Rule:
- If a candidate strategy exhibits an empirical frequency of $4.5$ completed trade episodes per day, it does not meet the Category A threshold.
- However, if the candidate achieves:
  - Mean net daily return $\ge 3.0000\%$ out-of-sample under AsterDEX Base Retail friction.
  - Maximum drawdown $\le 15.0\%$.
  - Strictly unlevered exposure ($\le 1.0000x$).
  - Statistically significant edge (e.g. Holm-Bonferroni adjusted $p < 0.05$).
- **Action:** The strategy is **APPROVED and ADMITTED** as **Category B (Intraday Low-Frequency)**. It is preserved in the research catalog and not penalized.

---

### 3. THE FOUR SEPARATE FREQUENCY METRICS

Frequency cannot be represented by a single aggregated integer. QUANTUM mandates separate reporting across four orthogonal dimensions:

```
+-----------------------------------------------------------------------------------------------------+
| THE FOUR MANDATORY FREQUENCY METRICS                                                                |
+------------------------------------+----------------------------------------------------------------+
| Metric Identifier                  | Mathematical Formula                                           |
+------------------------------------+----------------------------------------------------------------+
| 1. Per-Symbol Daily Frequency      | F_sym = Total Episodes for Symbol / Total Calendar Days        |
| 2. Portfolio Aggregate Frequency   | F_port = Total Portfolio Episodes / Total Calendar Days        |
| 3. Active Trading Day Frequency    | F_active = Total Portfolio Episodes / Active Trading Days      |
| 4. Full Calendar Day Frequency     | F_calendar = Total Portfolio Episodes / Total Calendar Days    |
+------------------------------------+----------------------------------------------------------------+
```

#### 3.1 Active Days vs Calendar Days Distinction:
- **Active Trading Day:** Any calendar day on which at least one completed trade episode entered or exited.
- **Calendar Day:** Every elapsed day in the chronological backtest window, including weekends, market consolidation periods, and filter pauses.
- **Mathematical Relationship:**
  $$F_{\text{active}} = \frac{N_{\text{episodes}}}{D_{\text{active}}} \ge \frac{N_{\text{episodes}}}{D_{\text{calendar}}} = F_{\text{calendar}}$$
- **Illustrative Example:**
  - Over a 365-day backtest ($D_{\text{calendar}} = 365$), a strategy executes 1,000 completed trade episodes across 100 volatile market days ($D_{\text{active}} = 100$), remaining completely flat during 265 quiet days.
  - $F_{\text{active}} = 1,000 / 100 = \mathbf{10.0\text{ episodes/day}}$ (Meets Category A on active days).
  - $F_{\text{calendar}} = 1,000 / 365 = \mathbf{2.74\text{ episodes/day}}$ (Category B on calendar basis).
  - Both numbers must be published side-by-side to expose clustering and inactivity regimes.

---

### 4. STRICT PROHIBITION OF FORCED TRADING

```
+-----------------------------------------------------------------------------------------------------+
| QUANTUM ANTI-CHURN MANDATE: FORCED TRADING PROHIBITION                                              |
+-----------------------------------------------------------------------------------------------------+
| RULE 1: Never lower signal thresholds solely to increase trade count.                              |
| RULE 2: High trade count without gross edge accelerates fee ruin.                                   |
| RULE 3: At AsterDEX Retail friction (26 bps round-trip), 100 trades/day generates 26.0% daily fee   |
|         drag on gross turnover. Signals MUST possess authentic economic alpha to survive this friction.|
| RULE 4: Quality, risk-adjusted expectancy, and capital preservation strictly dominate volume.       |
+-----------------------------------------------------------------------------------------------------+
```

#### 4.1 Economic Danger of Fee Churn:
- On a $\$100$ portfolio trading at 1.0x unlevered exposure:
  - If an agent generates 50 completed trade episodes per day with an average gross edge of $+10\text{ bps}$ per trade, gross profit is $+500\text{ bps}$ ($+5.0\%$).
  - However, at $26.0\text{ bps}$ round-trip taker friction, total transaction costs are $50 \times 26\text{ bps} = 1,300\text{ bps}$ ($13.0\%$).
  - **Net Realized Return:** $+5.0\% - 13.0\% = \mathbf{-8.0\%\text{ per day}}$ (Rapid Ruin).
- Forcing trade frequency on low-conviction signals converts trading into an operational subsidy for the exchange.

---

### 5. CODEBASE IMPLEMENTATION REFERENCE

Frequency governance is formalized in [`src/quantum/domain/research_contract.py`](file:///d:/quantum-multi-agent/src/quantum/domain/research_contract.py):
- **[`FrequencyReport`](file:///d:/quantum-multi-agent/src/quantum/domain/research_contract.py#L354-L368):** Structured Pydantic schema reporting symbol frequencies, active day frequency, calendar day frequency, assigned category, and statistical admissibility.
- **[`calculate_frequency_metrics`](file:///d:/quantum-multi-agent/src/quantum/domain/research_contract.py#L371-L404):** Pure evaluation function that calculates all four metrics and assigns Category A, B, or C without discarding statistically valid candidates.
