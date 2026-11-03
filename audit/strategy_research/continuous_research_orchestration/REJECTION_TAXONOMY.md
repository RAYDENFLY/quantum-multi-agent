# QUANTUM — AUTOMATED REJECTION TAXONOMY & FAILURE GATES
## FORMAL CRITERIA FOR METHODOLOGICAL & STATISTICAL REJECTION

---

### 1. OBJECTIVE & GOVERNANCE PRINCIPLES

In a continuous, parallelized research workflow, the risk of data dredging and publication bias is magnified. If researchers or automated pipelines silently discard unprofitable runs and only record "winning" strategies, the resulting alpha claims are mathematically spurious.

QUANTUM enforces two core governance principles:
1. **Automated Multi-Tier Rejection:** Every experiment is subjected to deterministic, algorithmic rejection gates immediately upon completion.
2. **Zero Survivorship Bias Ledger:** Every candidate evaluated—whether rejected due to an exposure breach, negative net expectancy, or low profit factor—is permanently logged in [`EXPERIMENT_LEDGER.csv`](file:///d:/quantum-multi-agent/audit/strategy_research/continuous_research_orchestration/EXPERIMENT_LEDGER.csv) and [`EXPERIMENT_LEDGER.jsonl`](file:///d:/quantum-multi-agent/audit/strategy_research/continuous_research_orchestration/EXPERIMENT_LEDGER.jsonl).

---

### 2. METHODOLOGICAL REJECTION GATES

Methodological failures indicate that an experiment violated operational physics, portfolio constraints, or experimental integrity. Any methodological violation triggers immediate disqualification before statistical evaluation.

```
+---------------------------------------------------------------------------------------------------------------+
| METHODOLOGICAL FAILURE TAXONOMY                                                                               |
+----------------------------------+-----------------------+----------------------------------------------------+
| Failure Reason Identifier        | Hard Constraint       | Enforcement Rationale                             |
+----------------------------------+-----------------------+----------------------------------------------------+
| EXPOSURE_LIMIT_EXCEEDED          | Gross Exposure <= 1.0x| Hard unlevered portfolio constraint ($100 max).    |
|                                  | (Notional <= $100.00) | Eliminates hidden leverage and liquidation risk.   |
+----------------------------------+-----------------------+----------------------------------------------------+
| DRAWDOWN_LIMIT_EXCEEDED          | Max Drawdown <= 15.0% | Capital preservation boundary. Strategies exceeding|
|                                  |                       | 15% drawdown are mathematically disqualified.      |
+----------------------------------+-----------------------+----------------------------------------------------+
| HOLDING_HORIZON_BREACH           | Duration <= 240 mins  | Enforces intraday research mandate. Overnight      |
|                                  | (4 hours max)         | holding requires explicit justification.           |
+----------------------------------+-----------------------+----------------------------------------------------+
| TIMEFRAME_MISMATCH               | Strict 5m / 1m input  | Prevents silent downsampling (e.g. 1D substituted  |
|                                  | matching contract     | for 5m, as occurred in M5.9 Track C).              |
+----------------------------------+-----------------------+----------------------------------------------------+
| DATA_LEAKAGE_DETECTED            | Strict temporal order | Prevents training/validation overlap and enforces  |
|                                  | with 24h embargo      | zero contamination across buffer zones.            |
+----------------------------------+-----------------------+----------------------------------------------------+
| HOLDOUT_BOUNDARY_VIOLATION       | t < 1,793,491,200,000 | Halts any experiment attempting to touch the       |
|                                  | ms (2026-11-01 UTC)   | prospective holdout partition.                     |
+----------------------------------+-----------------------+----------------------------------------------------+
| LOOKAHEAD_BIAS_DETECTED          | Next-bar open fill    | Ensures trade entry occurs strictly at t+1 open,   |
|                                  | (t + 1)               | never at same-bar close.                           |
+----------------------------------+-----------------------+----------------------------------------------------+
```

---

### 3. STATISTICAL REJECTION GATES

If an experiment passes all methodological checks, its empirical performance is evaluated against the non-negotiable QUANTUM statistical gates:

```
+---------------------------------------------------------------------------------------------------------------+
| STATISTICAL FAILURE TAXONOMY                                                                                  |
+----------------------------------+-----------------------+----------------------------------------------------+
| Failure Reason Identifier        | Mandatory Threshold   | Quantitative Justification                         |
+----------------------------------+-----------------------+----------------------------------------------------+
| SUB_TARGET_DAILY_RETURN          | Daily Return >= 3.00% | Mandatory QUANTUM research target. Unlevered       |
|                                  |                       | net daily return must average >= 3.0000%.          |
+----------------------------------+-----------------------+----------------------------------------------------+
| LOW_PROFIT_FACTOR                | Profit Factor >= 1.30 | Ensures gross wins significantly exceed losses     |
|                                  |                       | to absorb spread widening and adverse fills.       |
+----------------------------------+-----------------------+----------------------------------------------------+
| NEGATIVE_NET_EXPECTANCY          | Net Expectancy > 0 bps| Decisively rejects strategies overwhelmed by the   |
|                                  |                       | 26.0 bps AsterDEX taker friction hurdle.           |
+----------------------------------+-----------------------+----------------------------------------------------+
| INSUFFICIENT_FREQUENCY           | >= 10.0 trades/day    | Enforces high-frequency intraday sample size       |
|                                  | (Category A)          | to ensure rapid statistical convergence.           |
+----------------------------------+-----------------------+----------------------------------------------------+
| STATISTICALLY_INSIGNIFICANT      | Holm-Bonferroni       | Multi-hypothesis testing correction at alpha=0.05  |
|                                  | adjusted p < 0.05     | to prevent false discovery from multiple trials.   |
+----------------------------------+-----------------------+----------------------------------------------------+
| DEFLATED_SHARPE_REJECTED         | DSR Prob >= 0.95      | Bailey & López de Prado adjustment for trial       |
|                                  |                       | count, skewness, and non-Gaussian returns.         |
+----------------------------------+-----------------------+----------------------------------------------------+
```

---

### 4. REDUNDANCY & DEDUPLICATION GATES

```
+----------------------------------+-----------------------+----------------------------------------------------+
| DUPLICATE_FINGERPRINT            | Unique (Config, Data) | Identifies duplicate configurations on identical   |
|                                  | pair required         | datasets; halts redundant compute in 0.001 seconds.|
+----------------------------------+-----------------------+----------------------------------------------------+
```

---

### 5. PERMANENT LEDGER AUDIT & SURVIVORSHIP BIAS ELIMINATION

Every experiment executed by the [`ContinuousResearchOrchestrator`](file:///d:/quantum-multi-agent/src/quantum/research/orchestrator.py) appends a structured record containing:
- `experiment_id` & `hypothesis_id`
- `partition_type` (`TRAIN`, `VALIDATION`, `ROLLING_OOS`)
- `dataset_fingerprint` & `config_fingerprint`
- `completed_episodes`, `frequency_daily`, `win_rate_pct`, `profit_factor`
- `gross_pnl_usd`, `net_pnl_usd`, `net_expectancy_bps`
- `mean_net_daily_return_pct`, `max_drawdown_pct`, `sharpe_ratio`
- `is_accepted` (Boolean)
- `rejection_category` & `rejection_reasons` (Semicolon-delimited failure list)

By logging 100% of attempts—including all rejected configurations—QUANTUM maintains a complete audit trail that enables family-wise error rate corrections (Holm-Bonferroni and Deflated Sharpe Ratio) based on the true number of trials $K$.
