# QUANTUM PHASE 5.3.3.6: MOVING BLOCK BOOTSTRAP IMPLEMENTATION & NULL TEST AUDIT

**Role:** Independent Senior Quantitative Research Auditor  
**Repository:** [quantum-multi-agent](file:///d:/quantum-multi-agent)  
**Phase:** Phase 5.3.3.6 (Deliverable B: Tasks B & C)  
**Audit Scope:** Source-Level and Empirical Verification of `extract_continuous_segments`, `build_candidate_blocks`, `run_paired_empirical_mbb`, and Hall & Wilson (1991) Null Hypothesis Testing  

---

## 1. Task B: Moving Block Bootstrap Implementation Verification

We inspected and programmatically audited [`extract_continuous_segments`](file:///d:/quantum-multi-agent/scripts/run_phase5_3_3_5_paired_audit.py#L63-L86), [`build_candidate_blocks`](file:///d:/quantum-multi-agent/scripts/run_phase5_3_3_5_paired_audit.py#L89-L102), and [`run_paired_empirical_mbb`](file:///d:/quantum-multi-agent/scripts/run_phase5_3_3_5_paired_audit.py#L136-L250) in [run_phase5_3_3_5_paired_audit.py](file:///d:/quantum-multi-agent/scripts/run_phase5_3_3_5_paired_audit.py) across all 11 instruments and all 4 block lengths ($b \in \{12, 24, 48, 96\}$, totaling `44` configurations and `440,000` bootstrap replicates):

| # | Verification Criterion | Implementation Mechanism | Empirical Audit Result | Status |
| :---: | :--- | :--- | :--- | :---: |
| 1 | **No candidate block crosses a fold boundary** | `extract_continuous_segments` splits whenever `fold_ids[i+1] != fold_ids[i]`; `build_candidate_blocks` restricts `st + b <= s_end`. | `0` fold-crossing blocks across all 44 configurations | **VERIFIED** |
| 2 | **No candidate block crosses a timestamp discontinuity** | `extract_continuous_segments` splits whenever `timestamps[i+1] - timestamps[i] != 300_000`. | `0` discontinuity-crossing blocks across all 44 configurations | **VERIFIED** |
| 3 | **Remainder sampling cannot cross a segment boundary** | When $r = N \bmod b > 0$, `build_candidate_blocks(segments, r)` selects contiguous slices of length $r$ strictly inside segments of length $\ge r$. | `0` remainder fold or timestamp crossings across all 44 configurations | **VERIFIED** |
| 4 | **Every resampled tuple preserves `(timestamp, y_true, pred_B4, pred_B0)`** | `compute_prefix_contingency_paired` indexes all 9 indicators on the identical row index $t$; block slice `[st, st+b)` extracts paired counts simultaneously. | Verified bit-exact against direct slice indexing on all 11 pairs | **VERIFIED** |
| 5 | **Resampled data preserve valid class support** | Every replicate sums class supports $N^*(\text{SL}), N^*(\text{EXP}), N^*(\text{TP})$ across $K$ full blocks and $1$ remainder block. | `0` zero-support replicates across all 440,000 replicates (`min_support >= 1,398`) | **VERIFIED** |
| 6 | **Each replicate contains exactly the intended sample length** | Each replicate sums $K = \lfloor N / b \rfloor$ blocks of length $b$ plus $1$ remainder block of length $r = N \bmod b$, totaling $K \cdot b + r = N$. | `min_replicate_len == max_replicate_len == N` for all 440,000 replicates | **VERIFIED** |
| 7 | **Random seed and sampling behavior are deterministic** | `np.random.default_rng(42 + b)` with fixed `batch_size = 2000` produces bit-identical sequences across runs. | 100% bit-exact reproduction of all Phase 5.3.3.5 means, SEs, and CIs | **VERIFIED** |
| 8 | **No silent fallback or discarded bootstrap replicate occurs** | All $B = 10,000$ replicates are written directly into `bootstrap_deltas` without filtering or fallback loops. | `0` discarded replicates across all 440,000 replicates | **VERIFIED** |

### 1.1 Policy on Missing Class Support in Bootstrap Replicates
- **Policy:** A bootstrap replicate is never silently discarded or re-drawn. If any class support $N^*(c) = 0$ were to occur in a small-sample regime, the replicate must be explicitly counted in `zero_support_replicate_count` and flagged as a degenerate support failure.
- **Empirical Verification:** Across all `440,000` replicates evaluated in QUANTUM (`11 instruments x 4 block lengths x 10,000 resamples`), `zero_support_replicate_count = 0`. For the 10 long-history instruments, minimum resampled class support was `>= 6,692`, and for the shortest instrument (`XMRUSDT`, $N = 15,252$) at the largest block length ($b = 96$), the minimum resampled class supports across all 10,000 replicates were `SL: 5,881`, `EXP: 1,398`, and `TP: 6,424`.

---

## 2. Task C: Centered Null Test, Confidence Intervals, and Multiplicity Audit

### 2.1 Verification of Paired Null Construction and Exceedance Condition
To test:
$$H_0: \text{BA}_{B4} - \text{BA}_{B0} \le 0 \quad \text{versus} \quad H_1: \text{BA}_{B4} - \text{BA}_{B0} > 0$$
1. **Observed Statistic:** $\Delta\text{BA}_{\text{obs}} = \text{BA}_{B4,\text{pooled}} - \text{BA}_{B0,\text{pooled}}$.
2. **Centered Null Distribution (Hall & Wilson, 1991):** Because the raw bootstrap replicates $\Delta\text{BA}^{*(r)}$ are drawn from the empirical distribution centered near $\Delta\text{BA}_{\text{obs}}$, imposing the null boundary $\Delta\text{BA}_0 = 0$ shifts each replicate by subtracting $\Delta\text{BA}_{\text{obs}}$:
   $$\Delta\text{BA}^{*}_{\text{null}, r} = \Delta\text{BA}^{*(r)} - \Delta\text{BA}_{\text{obs}}$$
3. **Exceedance Condition:** Under $H_0$, an exceedance occurs when a centered null replicate is at least as large as the observed statistic:
   $$\Delta\text{BA}^{*}_{\text{null}, r} \ge \Delta\text{BA}_{\text{obs}} \iff \Delta\text{BA}^{*(r)} \ge 2 \cdot \Delta\text{BA}_{\text{obs}}$$
   We verified in [`run_paired_empirical_mbb`](file:///d:/quantum-multi-agent/scripts/run_phase5_3_3_5_paired_audit.py#L215-L219) that `null_deltas = bootstrap_deltas - observed_paired_delta` and `count_exceed = int(np.sum(null_deltas >= observed_paired_delta))` are implemented consistently.
4. **Finite-Sample Monte Carlo Upper Bound:** With $B = 10,000$ and `count_exceed = 0`, the exact finite-sample upper bound is $p < \frac{1}{B+1} = \frac{1}{10,001} \approx 0.000100$.

### 2.2 Distinction Between Confidence Intervals, One-Sided Null Tests, and Holm-Adjusted Significance
- **Confidence Interval Evidence:** The 95% percentile confidence interval $[\Delta\text{BA}^*_{0.025}, \Delta\text{BA}^*_{0.975}]$ is computed directly from the unshifted bootstrap distribution $\Delta\text{BA}^{*(r)}$ and estimates the plausible range of the true population parameter $\Delta\text{BA}$ at the 95% confidence level (two-sided $2.5\%$ and $97.5\%$ tails).
- **One-Sided Hypothesis Test:** Evaluates the tail probability of observing $\Delta\text{BA}_{\text{obs}}$ or greater under the null-shifted distribution $\Delta\text{BA}^*_{\text{null}}$ centered at zero, answering how probable the observed positive lift is by block-resampling chance if the true lift were zero.
- **Holm-Adjusted Significance:** Controls the Family-Wise Error Rate (FWER) at $\alpha = 0.05$ across all $M = 11$ simultaneous specialist comparisons by comparing the $i$-th ordered p-value against the step-down threshold $\alpha_i = \frac{\alpha}{M - i + 1}$ (equivalently multiplying by $(M - i + 1)$). Even at the most conservative rank ($i=1$, multiplier $11$), the upper bound is $p_{\text{adj}} < 11 / 10,001 = 0.001100 < 0.05$.

### 2.3 Complete Audit Table Across Block Lengths $b \in \{12, 24, 48, 96\}$

#### BTCUSDT (Total OOF = 130,684, Contiguous Segments = 503)
| Block ($b$) | Full / Rem Blocks ($K$ / $r$) | Candidate Blocks ($M_{\text{full}}$ / $M_{\text{rem}}$) | Min Support `[SL, EXP, TP]` | Observed $\Delta\text{BA}$ | Boot Mean $\pm$ SD | 95% Percentile CI | Centered Null Mean $\pm$ SD | Centered Null 95% Range | Centered Null Max | Exceedances | p-Value Bound |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 12 | 10,890 / 4 | 125,901 / 129,275 | `[60,617, 7,066, 59,731]` | **+0.100414** | `+0.099660 +/- 0.004275` | `[+0.091395, +0.108182]` | `-0.000754 +/- 0.004275` | `[-0.009019, +0.007768]` | `+0.016869` | 0 | p < 1/10001 (p < 0.000100) |
| 24 | 5,445 / 4 | 121,091 / 129,275 | `[60,610, 7,122, 59,440]` | **+0.100414** | `+0.099731 +/- 0.004521` | `[+0.090766, +0.108663]` | `-0.000683 +/- 0.004521` | `[-0.009648, +0.008249]` | `+0.017757` | 0 | p < 1/10001 (p < 0.000100) |
| 48 | 2,722 / 28 | 112,011 / 119,524 | `[60,124, 7,143, 59,649]` | **+0.100414** | `+0.100409 +/- 0.004670` | `[+0.091263, +0.109500]` | `-0.000005 +/- 0.004670` | `[-0.009151, +0.009086]` | `+0.018134` | 0 | p < 1/10001 (p < 0.000100) |
| 96 | 1,361 / 28 | 95,822 / 119,524 | `[60,213, 7,215, 59,444]` | **+0.100414** | `+0.101089 +/- 0.004744` | `[+0.091907, +0.110360]` | `+0.000675 +/- 0.004744` | `[-0.008507, +0.009946]` | `+0.019957` | 0 | p < 1/10001 (p < 0.000100) |

#### ETHUSDT (Total OOF = 130,728, Contiguous Segments = 562)
| Block ($b$) | Full / Rem Blocks ($K$ / $r$) | Candidate Blocks ($M_{\text{full}}$ / $M_{\text{rem}}$) | Min Support `[SL, EXP, TP]` | Observed $\Delta\text{BA}$ | Boot Mean $\pm$ SD | 95% Percentile CI | Centered Null Mean $\pm$ SD | Centered Null 95% Range | Centered Null Max | Exceedances | p-Value Bound |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 12 | 10,894 / 0 | 125,437 / 0 | `[59,683, 7,670, 59,990]` | **+0.126517** | `+0.125126 +/- 0.004188` | `[+0.116872, +0.133317]` | `-0.001391 +/- 0.004188` | `[-0.009645, +0.006800]` | `+0.015035` | 0 | p < 1/10001 (p < 0.000100) |
| 24 | 5,447 / 0 | 120,217 / 0 | `[59,331, 7,716, 60,020]` | **+0.126517** | `+0.124895 +/- 0.004380` | `[+0.116260, +0.133468]` | `-0.001622 +/- 0.004380` | `[-0.010257, +0.006951]` | `+0.018140` | 0 | p < 1/10001 (p < 0.000100) |
| 48 | 2,723 / 24 | 110,639 / 120,217 | `[59,217, 7,595, 60,126]` | **+0.126517** | `+0.126034 +/- 0.004448` | `[+0.117319, +0.134887]` | `-0.000483 +/- 0.004448` | `[-0.009198, +0.008370]` | `+0.017207` | 0 | p < 1/10001 (p < 0.000100) |
| 96 | 1,361 / 72 | 94,238 / 101,982 | `[59,097, 8,015, 59,817]` | **+0.126517** | `+0.127581 +/- 0.004509` | `[+0.118663, +0.136415]` | `+0.001064 +/- 0.004509` | `[-0.007854, +0.009898]` | `+0.018180` | 0 | p < 1/10001 (p < 0.000100) |

#### BNBUSDT (Total OOF = 130,847, Contiguous Segments = 365)
| Block ($b$) | Full / Rem Blocks ($K$ / $r$) | Candidate Blocks ($M_{\text{full}}$ / $M_{\text{rem}}$) | Min Support `[SL, EXP, TP]` | Observed $\Delta\text{BA}$ | Boot Mean $\pm$ SD | 95% Percentile CI | Centered Null Mean $\pm$ SD | Centered Null 95% Range | Centered Null Max | Exceedances | p-Value Bound |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 12 | 10,903 / 11 | 127,329 / 127,634 | `[57,613, 11,800, 57,617]` | **+0.133344** | `+0.133017 +/- 0.003706` | `[+0.125573, +0.140269]` | `-0.000327 +/- 0.003706` | `[-0.007771, +0.006925]` | `+0.012209` | 0 | p < 1/10001 (p < 0.000100) |
| 24 | 5,451 / 23 | 123,738 / 124,032 | `[57,284, 11,651, 57,434]` | **+0.133344** | `+0.133923 +/- 0.004199` | `[+0.125669, +0.142136]` | `+0.000579 +/- 0.004199` | `[-0.007675, +0.008792]` | `+0.016048` | 0 | p < 1/10001 (p < 0.000100) |
| 48 | 2,725 / 47 | 117,039 / 117,311 | `[57,173, 11,942, 57,448]` | **+0.133344** | `+0.136341 +/- 0.004588` | `[+0.127217, +0.145369]` | `+0.002997 +/- 0.004588` | `[-0.006127, +0.012025]` | `+0.019977` | 0 | p < 1/10001 (p < 0.000100) |
| 96 | 1,362 / 95 | 104,796 / 105,030 | `[56,674, 11,953, 56,602]` | **+0.133344** | `+0.139596 +/- 0.005158` | `[+0.129209, +0.149649]` | `+0.006252 +/- 0.005158` | `[-0.004135, +0.016305]` | `+0.024496` | 0 | p < 1/10001 (p < 0.000100) |

#### XRPUSDT (Total OOF = 130,600, Contiguous Segments = 445)
| Block ($b$) | Full / Rem Blocks ($K$ / $r$) | Candidate Blocks ($M_{\text{full}}$ / $M_{\text{rem}}$) | Min Support `[SL, EXP, TP]` | Observed $\Delta\text{BA}$ | Boot Mean $\pm$ SD | 95% Percentile CI | Centered Null Mean $\pm$ SD | Centered Null 95% Range | Centered Null Max | Exceedances | p-Value Bound |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 12 | 10,883 / 4 | 126,441 / 129,361 | `[59,644, 9,234, 57,794]` | **+0.093771** | `+0.094020 +/- 0.003858` | `[+0.086566, +0.101634]` | `+0.000249 +/- 0.003858` | `[-0.007205, +0.007863]` | `+0.015202` | 0 | p < 1/10001 (p < 0.000100) |
| 24 | 5,441 / 16 | 122,345 / 125,047 | `[59,641, 9,211, 57,917]` | **+0.093771** | `+0.094202 +/- 0.004268` | `[+0.086009, +0.102570]` | `+0.000431 +/- 0.004268` | `[-0.007762, +0.008799]` | `+0.016111` | 0 | p < 1/10001 (p < 0.000100) |
| 48 | 2,720 / 40 | 114,719 / 117,186 | `[59,432, 9,255, 57,726]` | **+0.093771** | `+0.095649 +/- 0.004650` | `[+0.086722, +0.104771]` | `+0.001878 +/- 0.004650` | `[-0.007049, +0.011000]` | `+0.018904` | 0 | p < 1/10001 (p < 0.000100) |
| 96 | 1,360 / 40 | 101,623 / 117,186 | `[58,933, 9,441, 57,569]` | **+0.093771** | `+0.097701 +/- 0.005144` | `[+0.087695, +0.107747]` | `+0.003930 +/- 0.005144` | `[-0.006076, +0.013976]` | `+0.025201` | 0 | p < 1/10001 (p < 0.000100) |

#### ADAUSDT (Total OOF = 130,483, Contiguous Segments = 372)
| Block ($b$) | Full / Rem Blocks ($K$ / $r$) | Candidate Blocks ($M_{\text{full}}$ / $M_{\text{rem}}$) | Min Support `[SL, EXP, TP]` | Observed $\Delta\text{BA}$ | Boot Mean $\pm$ SD | 95% Percentile CI | Centered Null Mean $\pm$ SD | Centered Null 95% Range | Centered Null Max | Exceedances | p-Value Bound |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 12 | 10,873 / 7 | 127,118 / 128,552 | `[55,430, 18,237, 53,115]` | **+0.135180** | `+0.132831 +/- 0.002717` | `[+0.127482, +0.138140]` | `-0.002349 +/- 0.002717` | `[-0.007698, +0.002960]` | `+0.007567` | 0 | p < 1/10001 (p < 0.000100) |
| 24 | 5,436 / 19 | 123,895 / 125,206 | `[54,936, 18,077, 52,747]` | **+0.135180** | `+0.131370 +/- 0.002940` | `[+0.125559, +0.137066]` | `-0.003810 +/- 0.002940` | `[-0.009621, +0.001886]` | `+0.007241` | 0 | p < 1/10001 (p < 0.000100) |
| 48 | 2,718 / 19 | 118,140 / 125,206 | `[54,804, 18,021, 52,733]` | **+0.135180** | `+0.129470 +/- 0.003139` | `[+0.123268, +0.135529]` | `-0.005710 +/- 0.003139` | `[-0.011912, +0.000349]` | `+0.006202` | 0 | p < 1/10001 (p < 0.000100) |
| 96 | 1,359 / 19 | 108,934 / 125,206 | `[54,425, 17,943, 51,998]` | **+0.135180** | `+0.128253 +/- 0.003399` | `[+0.121516, +0.134830]` | `-0.006927 +/- 0.003399` | `[-0.013664, -0.000350]` | `+0.007005` | 0 | p < 1/10001 (p < 0.000100) |

#### SOLUSDT (Total OOF = 130,808, Contiguous Segments = 516)
| Block ($b$) | Full / Rem Blocks ($K$ / $r$) | Candidate Blocks ($M_{\text{full}}$ / $M_{\text{rem}}$) | Min Support `[SL, EXP, TP]` | Observed $\Delta\text{BA}$ | Boot Mean $\pm$ SD | 95% Percentile CI | Centered Null Mean $\pm$ SD | Centered Null 95% Range | Centered Null Max | Exceedances | p-Value Bound |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 12 | 10,900 / 8 | 125,925 / 127,608 | `[60,503, 6,762, 60,407]` | **+0.106631** | `+0.106696 +/- 0.004194` | `[+0.098426, +0.114685]` | `+0.000065 +/- 0.004194` | `[-0.008205, +0.008054]` | `+0.019828` | 0 | p < 1/10001 (p < 0.000100) |
| 24 | 5,450 / 8 | 121,073 / 127,608 | `[60,352, 6,692, 59,992]` | **+0.106631** | `+0.107528 +/- 0.004639` | `[+0.098474, +0.116582]` | `+0.000897 +/- 0.004639` | `[-0.008157, +0.009951]` | `+0.019264` | 0 | p < 1/10001 (p < 0.000100) |
| 48 | 2,725 / 8 | 112,110 / 127,608 | `[60,233, 6,755, 60,001]` | **+0.106631** | `+0.111298 +/- 0.005009` | `[+0.101240, +0.121106]` | `+0.004667 +/- 0.005009` | `[-0.005391, +0.014475]` | `+0.023925` | 0 | p < 1/10001 (p < 0.000100) |
| 96 | 1,362 / 56 | 96,246 / 109,283 | `[60,235, 7,024, 59,579]` | **+0.106631** | `+0.116940 +/- 0.005299` | `[+0.106285, +0.127147]` | `+0.010309 +/- 0.005299` | `[-0.000346, +0.020516]` | `+0.030153` | 0 | p < 1/10001 (p < 0.000100) |

#### AVAXUSDT (Total OOF = 130,818, Contiguous Segments = 216)
| Block ($b$) | Full / Rem Blocks ($K$ / $r$) | Candidate Blocks ($M_{\text{full}}$ / $M_{\text{rem}}$) | Min Support `[SL, EXP, TP]` | Observed $\Delta\text{BA}$ | Boot Mean $\pm$ SD | 95% Percentile CI | Centered Null Mean $\pm$ SD | Centered Null 95% Range | Centered Null Max | Exceedances | p-Value Bound |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 12 | 10,901 / 6 | 128,731 / 129,809 | `[49,670, 27,486, 48,762]` | **+0.118928** | `+0.117988 +/- 0.002788` | `[+0.112562, +0.123481]` | `-0.000940 +/- 0.002788` | `[-0.006366, +0.004553]` | `+0.008323` | 0 | p < 1/10001 (p < 0.000100) |
| 24 | 5,450 / 18 | 126,653 / 127,688 | `[49,511, 27,614, 48,522]` | **+0.118928** | `+0.117629 +/- 0.003117` | `[+0.111510, +0.123708]` | `-0.001299 +/- 0.003117` | `[-0.007418, +0.004780]` | `+0.009716` | 0 | p < 1/10001 (p < 0.000100) |
| 48 | 2,725 / 18 | 122,829 / 127,688 | `[48,999, 27,427, 48,062]` | **+0.118928** | `+0.117147 +/- 0.003411` | `[+0.110479, +0.123854]` | `-0.001781 +/- 0.003411` | `[-0.008449, +0.004926]` | `+0.011203` | 0 | p < 1/10001 (p < 0.000100) |
| 96 | 1,362 / 66 | 116,173 / 120,237 | `[48,708, 27,553, 47,812]` | **+0.118928** | `+0.116032 +/- 0.003700` | `[+0.108844, +0.123149]` | `-0.002896 +/- 0.003700` | `[-0.010084, +0.004221]` | `+0.012482` | 0 | p < 1/10001 (p < 0.000100) |

#### LINKUSDT (Total OOF = 130,777, Contiguous Segments = 177)
| Block ($b$) | Full / Rem Blocks ($K$ / $r$) | Candidate Blocks ($M_{\text{full}}$ / $M_{\text{rem}}$) | Min Support `[SL, EXP, TP]` | Observed $\Delta\text{BA}$ | Boot Mean $\pm$ SD | 95% Percentile CI | Centered Null Mean $\pm$ SD | Centered Null 95% Range | Centered Null Max | Exceedances | p-Value Bound |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 12 | 10,898 / 1 | 129,148 / 130,777 | `[46,317, 33,797, 45,854]` | **+0.165608** | `+0.165069 +/- 0.002558` | `[+0.160032, +0.170066]` | `-0.000539 +/- 0.002558` | `[-0.005576, +0.004458]` | `+0.008986` | 0 | p < 1/10001 (p < 0.000100) |
| 24 | 5,449 / 1 | 127,533 / 130,777 | `[46,013, 33,415, 45,491]` | **+0.165608** | `+0.164617 +/- 0.002867` | `[+0.158918, +0.170243]` | `-0.000991 +/- 0.002867` | `[-0.006690, +0.004635]` | `+0.009859` | 0 | p < 1/10001 (p < 0.000100) |
| 48 | 2,724 / 25 | 124,464 / 127,400 | `[45,199, 33,626, 45,053]` | **+0.165608** | `+0.164285 +/- 0.003176` | `[+0.157989, +0.170458]` | `-0.001323 +/- 0.003176` | `[-0.007619, +0.004850]` | `+0.009783` | 0 | p < 1/10001 (p < 0.000100) |
| 96 | 1,362 / 25 | 118,706 / 127,400 | `[44,816, 33,439, 44,272]` | **+0.165608** | `+0.163684 +/- 0.003682` | `[+0.156475, +0.170838]` | `-0.001924 +/- 0.003682` | `[-0.009133, +0.005230]` | `+0.011062` | 0 | p < 1/10001 (p < 0.000100) |

#### DOGEUSDT (Total OOF = 130,648, Contiguous Segments = 448)
| Block ($b$) | Full / Rem Blocks ($K$ / $r$) | Candidate Blocks ($M_{\text{full}}$ / $M_{\text{rem}}$) | Min Support `[SL, EXP, TP]` | Observed $\Delta\text{BA}$ | Boot Mean $\pm$ SD | 95% Percentile CI | Centered Null Mean $\pm$ SD | Centered Null 95% Range | Centered Null Max | Exceedances | p-Value Bound |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 12 | 10,887 / 4 | 126,363 / 129,382 | `[56,780, 15,289, 54,719]` | **+0.154149** | `+0.153456 +/- 0.003542` | `[+0.146528, +0.160246]` | `-0.000693 +/- 0.003542` | `[-0.007621, +0.006097]` | `+0.013844` | 0 | p < 1/10001 (p < 0.000100) |
| 24 | 5,443 / 16 | 122,128 / 124,919 | `[56,346, 15,218, 54,572]` | **+0.154149** | `+0.153578 +/- 0.003864` | `[+0.146002, +0.161182]` | `-0.000571 +/- 0.003864` | `[-0.008147, +0.007033]` | `+0.014551` | 0 | p < 1/10001 (p < 0.000100) |
| 48 | 2,721 / 40 | 114,247 / 116,793 | `[55,939, 15,354, 54,164]` | **+0.154149** | `+0.153906 +/- 0.004096` | `[+0.145954, +0.161883]` | `-0.000243 +/- 0.004096` | `[-0.008195, +0.007734]` | `+0.015315` | 0 | p < 1/10001 (p < 0.000100) |
| 96 | 1,360 / 88 | 100,540 / 102,632 | `[55,293, 16,046, 53,152]` | **+0.154149** | `+0.154172 +/- 0.004079` | `[+0.146218, +0.162096]` | `+0.000023 +/- 0.004079` | `[-0.007931, +0.007947]` | `+0.016645` | 0 | p < 1/10001 (p < 0.000100) |

#### LTCUSDT (Total OOF = 130,463, Contiguous Segments = 299)
| Block ($b$) | Full / Rem Blocks ($K$ / $r$) | Candidate Blocks ($M_{\text{full}}$ / $M_{\text{rem}}$) | Min Support `[SL, EXP, TP]` | Observed $\Delta\text{BA}$ | Boot Mean $\pm$ SD | 95% Percentile CI | Centered Null Mean $\pm$ SD | Centered Null 95% Range | Centered Null Max | Exceedances | p-Value Bound |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 12 | 10,871 / 11 | 127,641 / 127,875 | `[46,546, 31,648, 47,405]` | **+0.151769** | `+0.151017 +/- 0.002804` | `[+0.145511, +0.156501]` | `-0.000752 +/- 0.002804` | `[-0.006258, +0.004732]` | `+0.009239` | 0 | p < 1/10001 (p < 0.000100) |
| 24 | 5,435 / 23 | 124,902 / 125,124 | `[46,152, 31,629, 46,816]` | **+0.151769** | `+0.150931 +/- 0.003181` | `[+0.144576, +0.157176]` | `-0.000838 +/- 0.003181` | `[-0.007193, +0.005407]` | `+0.011135` | 0 | p < 1/10001 (p < 0.000100) |
| 48 | 2,717 / 47 | 119,884 / 120,080 | `[45,890, 31,513, 46,454]` | **+0.151769** | `+0.151327 +/- 0.003548` | `[+0.144315, +0.158200]` | `-0.000442 +/- 0.003548` | `[-0.007454, +0.006431]` | `+0.012766` | 0 | p < 1/10001 (p < 0.000100) |
| 96 | 1,358 / 95 | 111,155 / 111,323 | `[45,041, 30,769, 46,057]` | **+0.151769** | `+0.151879 +/- 0.004062` | `[+0.143970, +0.159860]` | `+0.000110 +/- 0.004062` | `[-0.007799, +0.008091]` | `+0.015679` | 0 | p < 1/10001 (p < 0.000100) |

#### XMRUSDT (Total OOF = 15,252, Contiguous Segments = 18)
| Block ($b$) | Full / Rem Blocks ($K$ / $r$) | Candidate Blocks ($M_{\text{full}}$ / $M_{\text{rem}}$) | Min Support `[SL, EXP, TP]` | Observed $\Delta\text{BA}$ | Boot Mean $\pm$ SD | 95% Percentile CI | Centered Null Mean $\pm$ SD | Centered Null 95% Range | Centered Null Max | Exceedances | p-Value Bound |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 12 | 1,271 / 0 | 15,063 / 0 | `[5,875, 1,514, 6,466]` | **+0.053427** | `+0.053264 +/- 0.008618` | `[+0.036298, +0.069962]` | `-0.000163 +/- 0.008618` | `[-0.017129, +0.016535]` | `+0.031486` | 0 | p < 1/10001 (p < 0.000100) |
| 24 | 635 / 12 | 14,859 / 15,063 | `[5,939, 1,538, 6,424]` | **+0.053427** | `+0.053385 +/- 0.009111` | `[+0.035825, +0.071202]` | `-0.000042 +/- 0.009111` | `[-0.017602, +0.017775]` | `+0.036695` | 0 | p < 1/10001 (p < 0.000100) |
| 48 | 317 / 36 | 14,451 / 14,655 | `[5,955, 1,511, 6,419]` | **+0.053427** | `+0.053563 +/- 0.009688` | `[+0.034789, +0.072469]` | `+0.000136 +/- 0.009688` | `[-0.018638, +0.019042]` | `+0.034234` | 0 | p < 1/10001 (p < 0.000100) |
| 96 | 158 / 84 | 13,664 / 13,856 | `[5,881, 1,398, 6,424]` | **+0.053427** | `+0.054048 +/- 0.010060` | `[+0.034670, +0.073985]` | `+0.000621 +/- 0.010060` | `[-0.018757, +0.020558]` | `+0.034810` | 0 | p < 1/10001 (p < 0.000100) |
