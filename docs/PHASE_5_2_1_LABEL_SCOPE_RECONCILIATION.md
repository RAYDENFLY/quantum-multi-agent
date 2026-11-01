# QUANTUM PHASE 5.2.1 - LABEL SCOPE RECONCILIATION REPORT

**Author:** Independent Quantitative Research Auditor & Financial Data Engineer  
**Date:** 2026-11-01  
**Repository:** https://github.com/RAYDENFLY/quantum-multi-agent  
**Scope:** Timestamp-Level Partition Scope Audit, Row Accounting, and Reconciliation Arithmetic  
**Audit File:** [phase5_2_1_holdout_audit.json](file:///d:/quantum-multi-agent/data/historical/phase5_2_1_holdout_audit.json)  

---

## 1. GLOBAL ARITHMETIC RECONCILIATION

The 5m master dataset across all 11 instruments consists of 3,248,862 physical canonical candles on disk. The independent timestamp audit confirmed that every candle maps into exactly one label category or exclusion category without omission:

$$\text{Input Candles} = \text{Eligible Samples} + \text{Ambiguous Samples} + \text{Pipeline Exclusions}$$
$$3,248,862 = 3,234,142 + 14,104 + 616$$

### Master Accounting Equation
$$\begin{aligned}
\text{Total Evaluated} &= 3,248,862 \\
\text{Take Profit (TP)} &= 1,393,191 \quad (43.08\% \text{ of eligible}) \\
\text{Stop Loss (SL)} &= 1,400,798 \quad (43.31\% \text{ of eligible}) \\
\text{Time Expiration (EXP)} &= 440,153 \quad (13.61\% \text{ of eligible}) \\
\hline
\text{Total Eligible Samples} &= 3,234,142 \quad (99.55\% \text{ of total}) \\
\text{Ambiguous Intrabar Touches} &= 14,104 \quad (0.43\% \text{ of total}) \\
\text{Warm-Up Insufficient Lookback} &= 220 \quad (0.01\% \text{ of total}) \\
\text{Partition Boundary Overflow} &= 252 \quad (0.01\% \text{ of total}) \\
\text{Insufficient Future Horizon} &= 132 \quad (0.00\% \text{ of total}) \\
\text{Missing Future Candle Gap} &= 12 \quad (0.00\% \text{ of total}) \\
\hline
\text{Total Physical Candles} &= 3,248,862 \quad (100.00\%)
\end{aligned}$$

---

## 2. PARTITION-BY-PARTITION RECONCILIATION TABLE

All timestamps across all 11 instruments were partitioned according to authoritative UTC boundaries:

1. **Pre-Development:** Timestamps $< 1698796800000$ (prior to 2023-11-01 00:00:00 UTC)
2. **Development:** $1698796800000 \le \text{ts} \le 1761955199999$ (2023-11-01 00:00:00.000 to 2025-10-31 23:59:59.999 UTC)
3. **Validation:** $1761955200000 \le \text{ts} \le 1777593599999$ (2025-11-01 00:00:00.000 to 2026-04-30 23:59:59.999 UTC)
4. **Final Holdout:** $1777593600000 \le \text{ts} \le 1793491199999$ (2026-05-01 00:00:00.000 to 2026-10-31 23:59:59.999 UTC)
5. **Post-Holdout:** Timestamps $> 1793491199999$ (none present on disk)

| Partition | Input Candles | Eligible Samples | TP Count | TP % | SL Count | SL % | Exp Count | Exp % | Ambiguous Count | Excluded Count |
|---|---|---|---|---|---|---|---|---|---|---|
| **Pre-Development** | 8,864 | 8,627 | 3,957 | 45.87% | 4,018 | 46.57% | 652 | 7.56% | 37 | 200 (warmup) |
| **Development** | 2,105,279 | 2,096,426 | 871,625 | 41.58% | 863,914 | 41.21% | 360,887 | 17.21% | 8,721 | 132 (120 bound, 12 gap) |
| **Validation** | 552,183 | 549,283 | 251,186 | 45.73% | 259,704 | 47.28% | 38,393 | 6.99% | 2,748 | 152 (132 bound, 20 warmup) |
| **Final Holdout** | 582,536 | 579,806 | 266,423 | 45.95% | 273,162 | 47.11% | 40,221 | 6.94% | 2,598 | 132 (horizon) |
| **Post-Holdout** | 0 | 0 | 0 | 0.00% | 0 | 0.00% | 0 | 0.00% | 0 | 0 |
| **TOTAL** | **3,248,862** | **3,234,142** | **1,393,191** | **43.08%** | **1,400,798** | **43.31%** | **440,153** | **13.61%** | **14,104** | **616** |

---

## 3. EXCLUSION REASON ACCOUNTING BREAKDOWN

The 616 pipeline exclusions are explained down to individual candle events:

1. **Warm-Up Insufficient Lookback (220 candles):**
   - The first 20 bars of each historical series cannot compute a 20-bar return volatility without future lookahead.
   - 10 standard instruments starting in October 2023: $10 \times 20 = 200$ candles (in Pre-Development).
   - XMRUSDT starting on 2026-01-14 (in Validation): $1 \times 20 = 20$ candles.
   - Total: 220 candles.

2. **Partition Boundary Overflow (252 candles):**
   - Development End Truncation: 10 standard instruments have their last 12 candles in Development truncated to prevent forward evaluation into Validation ($10 \times 12 = 120$ candles).
   - Validation End Truncation: All 11 instruments have their last 12 candles in Validation truncated to prevent forward evaluation into Holdout ($11 \times 12 = 132$ candles).
   - Total: $120 + 132 = 252$ candles.

3. **Insufficient Future Horizon (132 candles):**
   - The final 12 candles at the very end of each instrument's physical Parquet file have fewer than 12 forward candles remaining.
   - 11 instruments: $11 \times 12 = 132$ candles (located at the end of the Final Holdout partition).

4. **Missing Future Candle Gap (12 candles):**
   - On BTCUSDT 5m, candle timestamp `1757771400000` (2025-09-13 13:50:00 UTC) failed OHLC validation (High < Open) and was quarantined into raw storage.
   - The 12 candles immediately preceding this missing candle detected a timestamp discontinuity ($> 300,000$ ms) in their forward horizon and were safely excluded.
   - Total: exactly 12 candles (located in Development).

---

## 4. SCOPE AUDIT CONCLUSION

The 3,234,142 reported eligible samples in Phase 5.2 **did indeed contain 579,806 samples from the Final Holdout** (17.93% of the total). The master reconciliation arithmetic is verified with zero unaccounted records.
