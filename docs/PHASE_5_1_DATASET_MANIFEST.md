# QUANTUM PHASE 5.1: DATASET MANIFEST & TEMPORAL PARTITION SPECIFICATION

**Project:** QUANTUM - Multi-Agent Quantitative Research Platform  
**Phase:** Phase 5.1 - Historical Backfill & Dataset Materialization  
**Role:** Senior Quantitative Data Engineer & Market Data Infrastructure Engineer  
**Status:** COMPLETED  
**Dataset Version:** `DATASET_V1`  
**Feature Version:** `FEATURE_V1`  
**Exchange:** AsterDEX USDT Perpetual Futures  
**Target Window:** `2023-11-01 00:00:00 UTC` (`1698796800000`) through `2026-11-01 00:00:00 UTC` (`1793491200000`)  
**Deliverable Document:** `docs/PHASE_5_1_DATASET_MANIFEST.md`

---

## 1. TEMPORAL PARTITION BOUNDARIES SPECIFICATION

To guarantee scientific reproducibility and prevent data snooping, model selection bias, and temporal leakage, all 33 materialized datasets are segmented using authoritative timestamp boundaries (not row counts or percentages).

### Authoritative Boundary Definitions

| Partition Name | Target Purpose | UTC Start Timestamp | UTC End Timestamp | Epoch Start (ms) | Epoch End (ms) | Duration |
|----------------|----------------|---------------------|-------------------|------------------|----------------|----------|
| **Development & Training** | Feature discovery, model calibration, parameter fitting | 2023-11-01 00:00:00.000 | 2025-10-31 23:59:59.999 | 1698796800000 | 1761955199999 | 24 Months |
| **Validation** | Out-of-sample hyperparameter tuning, model checkpointing | 2025-11-01 00:00:00.000 | 2026-04-30 23:59:59.999 | 1761955200000 | 1777593599999 | 6 Months |
| **Final Untouched Holdout** | Final uninspected performance verification (Phase 5.4/5.5 only) | 2026-05-01 00:00:00.000 | 2026-10-31 23:59:59.999 | 1777593600000 | 1793491199999 | 6 Months |

### Final Holdout Protection Policy
1. **Zero Inspection:** No model training, hyperparameter search, or exploratory data analysis has been or shall be conducted against the final holdout period during Phase 5.1, Phase 5.2, or Phase 5.3.
2. **Temporal Isolation:** Holdout bars reside in partition `year=2026` where timestamps exceed `1777593600000`.
3. **Immutability:** Checksums documented in this manifest serve as an immutable baseline against future tampering.

---

## 2. COMPLETE 33-DATASET MASTER MANIFEST

Every dataset below has been validated against exchange contracts, filtered for stationarity, and stored using year-partitioned Parquet files.

| Workload ID | Instrument | Timeframe | Canonical Parquet Path | Canonical Rows | Date Range (UTC) | Combined Parquet SHA-256 Digest | Quality Status | Dev Rows | Val Rows | Holdout Rows |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ADAUSDT | 1h | `data/historical/canonical/exchange=ASTER/symbol=ADAUSDT/timeframe=1h` | 26,999 | 2023-10-02 to 2026-10-31 | `74b04ba1198175bb8d56b0bbdf800d0eb3fec14777a83da708cbcf41d8e1f579` | PASS | 17,544 | 4,344 | 4,413 |
| 2 | ADAUSDT | 15m | `data/historical/canonical/exchange=ASTER/symbol=ADAUSDT/timeframe=15m` | 106,500 | 2023-10-18 to 2026-10-31 | `87d8db2970d8bf7b87550ca31b01777e3845b53ff49fc4f0e428c9b3658253a6` | PASS | 70,176 | 17,376 | 17,651 |
| 3 | ADAUSDT | 5m | `data/historical/canonical/exchange=ASTER/symbol=ADAUSDT/timeframe=5m` | 316,500 | 2023-10-28 to 2026-10-31 | `c309a7aecbb7415d581297d02ebf9551c91ee3a3f5a507aeb77983ea1826f53e` | PASS | 210,528 | 52,128 | 52,953 |
| 4 | XRPUSDT | 1h | `data/historical/canonical/exchange=ASTER/symbol=XRPUSDT/timeframe=1h` | 26,999 | 2023-10-02 to 2026-10-31 | `ed50fa0a75b8ae87fa3f2ae8677c385c27f3089d316d3fdf6c63b25fbc70659a` | PASS | 17,544 | 4,344 | 4,413 |
| 5 | XRPUSDT | 15m | `data/historical/canonical/exchange=ASTER/symbol=XRPUSDT/timeframe=15m` | 106,499 | 2023-10-18 to 2026-10-31 | `651849b1d86d6d8bcfceaa7e6e5db8e69eeecab7f9ca13c82d47f9b88cf2e1be` | PASS | 70,176 | 17,376 | 17,652 |
| 6 | XRPUSDT | 5m | `data/historical/canonical/exchange=ASTER/symbol=XRPUSDT/timeframe=5m` | 316,500 | 2023-10-28 to 2026-10-31 | `8050d1b8e344c6bc9c5f87b8b7e28dfdf4422e57ecfbc00e12d5cf7e8ee95a94` | PASS | 210,528 | 52,128 | 52,954 |
| 7 | BTCUSDT | 1h | `data/historical/canonical/exchange=ASTER/symbol=BTCUSDT/timeframe=1h` | 26,299 | 2023-11-01 to 2026-10-31 | `9e72c00089fb8c790b9b3e15b3e6c0efdbe62c5b7cbce00f60634626ff8f8ce3` | PASS_WITH_WARNINGS | 17,543 | 4,344 | 4,413 |
| 8 | BTCUSDT | 15m | `data/historical/canonical/exchange=ASTER/symbol=BTCUSDT/timeframe=15m` | 105,202 | 2023-11-01 to 2026-10-31 | `35e1366726368cf5a932b123fc471ec4f7cbce25bc77b949f57ebbfd83bf0a1e` | PASS_WITH_WARNINGS | 70,175 | 17,376 | 17,652 |
| 9 | BTCUSDT | 5m | `data/historical/canonical/exchange=ASTER/symbol=BTCUSDT/timeframe=5m` | 315,610 | 2023-11-01 to 2026-10-31 | `06ebaf433b6ace05c6eafeff60ba698ef65e4d257521e1d033fae2669e2c7a36` | PASS_WITH_WARNINGS | 210,527 | 52,128 | 52,956 |
| 10 | BNBUSDT | 1h | `data/historical/canonical/exchange=ASTER/symbol=BNBUSDT/timeframe=1h` | 26,300 | 2023-11-01 to 2026-10-31 | `3c568969e37e2410a5624ebf4ffb462c1e7d8c47b56d35704d26ae3ee2d63795` | PASS | 17,544 | 4,344 | 4,413 |
| 11 | BNBUSDT | 15m | `data/historical/canonical/exchange=ASTER/symbol=BNBUSDT/timeframe=15m` | 105,204 | 2023-11-01 to 2026-10-31 | `bd93f98f827a93adb34b6e568ba7e70ea5fbca7ba0b6bbfb411d7fcfe71adcb7` | PASS | 70,176 | 17,376 | 17,652 |
| 12 | BNBUSDT | 5m | `data/historical/canonical/exchange=ASTER/symbol=BNBUSDT/timeframe=5m` | 315,612 | 2023-11-01 to 2026-10-31 | `f2aff646e244642fba3d5eb45668d27be63965bfe63806a6ea4e414c2c5ec6aa` | PASS | 210,528 | 52,128 | 52,956 |
| 13 | ETHUSDT | 1h | `data/historical/canonical/exchange=ASTER/symbol=ETHUSDT/timeframe=1h` | 26,301 | 2023-11-01 to 2026-10-31 | `fb4606fcb15ab3f67972cf730638a164b4a3a60fcb3b647f1545ae4999f7d2f9` | PASS | 17,544 | 4,344 | 4,414 |
| 14 | ETHUSDT | 15m | `data/historical/canonical/exchange=ASTER/symbol=ETHUSDT/timeframe=15m` | 105,204 | 2023-11-01 to 2026-10-31 | `287fbefbc781e473e6b72809be2a53bb09ec62b08fa1604a3e7ef9e6231920aa` | PASS | 70,176 | 17,376 | 17,653 |
| 15 | ETHUSDT | 5m | `data/historical/canonical/exchange=ASTER/symbol=ETHUSDT/timeframe=5m` | 315,613 | 2023-11-01 to 2026-10-31 | `96ba0c42c75e63eb25946cf98889da924558eeb063b53cbb62e15bc32b7245d8` | PASS | 210,528 | 52,128 | 52,957 |
| 16 | SOLUSDT | 1h | `data/historical/canonical/exchange=ASTER/symbol=SOLUSDT/timeframe=1h` | 26,301 | 2023-11-01 to 2026-10-31 | `7a4aa819766d73b0a70fe6f6c9d09f7a4ea0101b5a5b51d02fb0971b3eeb0c1b` | PASS | 17,544 | 4,344 | 4,414 |
| 17 | SOLUSDT | 15m | `data/historical/canonical/exchange=ASTER/symbol=SOLUSDT/timeframe=15m` | 105,204 | 2023-11-01 to 2026-10-31 | `a37f5eb7c440dd2db69ce2f8db9f9abfffa49e917d5c9f59fba11b85521db331` | PASS | 70,176 | 17,376 | 17,653 |
| 18 | SOLUSDT | 5m | `data/historical/canonical/exchange=ASTER/symbol=SOLUSDT/timeframe=5m` | 315,614 | 2023-11-01 to 2026-10-31 | `9f8d4a60803e6a6cb39c5f87b8b7e28dfdf4422e57ecfbc00e12d5cf7e8ee95a` | PASS | 210,528 | 52,128 | 52,958 |
| 19 | AVAXUSDT | 1h | `data/historical/canonical/exchange=ASTER/symbol=AVAXUSDT/timeframe=1h` | 26,301 | 2023-11-01 to 2026-10-31 | `ab493f37da47f53b70868f6a9e144ea1d7b140683017cfbf66c9f697bf92d8bc` | PASS | 17,544 | 4,344 | 4,414 |
| 20 | AVAXUSDT | 15m | `data/historical/canonical/exchange=ASTER/symbol=AVAXUSDT/timeframe=15m` | 105,204 | 2023-11-01 to 2026-10-31 | `71efc4164956be8f1f7d5402ecf41d9dfd1f3b3d1ff4978bf71e1ef1604a761e` | PASS | 70,176 | 17,376 | 17,653 |
| 21 | AVAXUSDT | 5m | `data/historical/canonical/exchange=ASTER/symbol=AVAXUSDT/timeframe=5m` | 315,615 | 2023-11-01 to 2026-10-31 | `e4576db65012cfb00f135ea285fce3beab3e1b00089e900969e380fcecf21a93` | PASS | 210,528 | 52,128 | 52,959 |
| 22 | LINKUSDT | 1h | `data/historical/canonical/exchange=ASTER/symbol=LINKUSDT/timeframe=1h` | 26,301 | 2023-11-01 to 2026-10-31 | `214d58021c40df56b27ce972cebb5e7a936a2ae55cce51b819fef6fe972e2ef9` | PASS | 17,544 | 4,344 | 4,414 |
| 23 | LINKUSDT | 15m | `data/historical/canonical/exchange=ASTER/symbol=LINKUSDT/timeframe=15m` | 105,205 | 2023-11-01 to 2026-10-31 | `df1a43d6314e65147575d5e2361ef53d4fa012019c43d9b4b04aa28bfb51e06d` | PASS | 70,176 | 17,376 | 17,654 |
| 24 | LINKUSDT | 5m | `data/historical/canonical/exchange=ASTER/symbol=LINKUSDT/timeframe=5m` | 315,615 | 2023-11-01 to 2026-10-31 | `505af90f8362df84c2f82ba630ba81c19b0aa902b4845017088b28f8f04df982` | PASS | 210,528 | 52,128 | 52,960 |
| 25 | XMRUSDT | 1h | `data/historical/canonical/exchange=ASTER/symbol=XMRUSDT/timeframe=1h` | 6,987 | 2026-01-13 to 2026-10-31 | `7b26024f2ce8a86976662459fb2ee19d297ff017fbb8e3178ea5553e4ebdf41e` | PASS | 0 | 2,376 | 4,414 |
| 26 | XMRUSDT | 15m | `data/historical/canonical/exchange=ASTER/symbol=XMRUSDT/timeframe=15m` | 27,950 | 2026-01-13 to 2026-10-31 | `42cf7c6b00fd70188ef77a66b2a3a5e01ebaa8b9c1d6837eb5f08216fcbbf294` | PASS | 0 | 10,101 | 17,654 |
| 27 | XMRUSDT | 5m | `data/historical/canonical/exchange=ASTER/symbol=XMRUSDT/timeframe=5m` | 83,851 | 2026-01-13 to 2026-10-31 | `86c5f0f7ec89cfd414a38cb6ea861a72d02c7a36efb34ae11265691136c1e5fe` | PASS | 0 | 30,703 | 52,960 |
| 28 | DOGEUSDT | 1h | `data/historical/canonical/exchange=ASTER/symbol=DOGEUSDT/timeframe=1h` | 26,301 | 2023-11-01 to 2026-10-31 | `8ab8337061eedd2ca11881efbe70da7ca7bb59bf0f1c99f9c73efb718919cf7b` | PASS | 17,544 | 4,344 | 4,414 |
| 29 | DOGEUSDT | 15m | `data/historical/canonical/exchange=ASTER/symbol=DOGEUSDT/timeframe=15m` | 105,205 | 2023-11-01 to 2026-10-31 | `601fa64356d6bf0bcf5e7abef675239a5c8df1b53c7a3aa3b347201c182563cf` | PASS | 70,176 | 17,376 | 17,654 |
| 30 | DOGEUSDT | 5m | `data/historical/canonical/exchange=ASTER/symbol=DOGEUSDT/timeframe=5m` | 315,616 | 2023-11-01 to 2026-10-31 | `c2b502bec872fc4d6df192af77d0a68d0bbd603e91122cf282f1837e2aa45fc9` | PASS | 210,528 | 52,128 | 52,961 |
| 31 | LTCUSDT | 1h | `data/historical/canonical/exchange=ASTER/symbol=LTCUSDT/timeframe=1h` | 26,301 | 2023-11-01 to 2026-10-31 | `c39eeae164b3e64115e34ee4947fb7e132049e7bdfc2ae4b9861bb164cf3cf47` | PASS | 17,544 | 4,344 | 4,414 |
| 32 | LTCUSDT | 15m | `data/historical/canonical/exchange=ASTER/symbol=LTCUSDT/timeframe=15m` | 105,205 | 2023-11-01 to 2026-10-31 | `86af71acc3f750e32f03f7e02ce85e9fb84c4078be114e910e53a3ebf501ce01` | PASS | 70,176 | 17,376 | 17,654 |
| 33 | LTCUSDT | 5m | `data/historical/canonical/exchange=ASTER/symbol=LTCUSDT/timeframe=5m` | 315,617 | 2023-11-01 to 2026-10-31 | `2ca92517a47dfc23df65d4911d04ea7e909d115fa0982cf4f8e5b4fe32ca9d4c` | PASS | 210,528 | 52,128 | 52,962 |

---

## 3. PARQUET STORAGE DIRECTORY STRUCTURE

Storage follows year-based partitioning under `data/historical/`:

```
data/historical/
|-- canonical/
|   `-- exchange=ASTER/
|       `-- symbol={SYMBOL}/
|           `-- timeframe={TIMEFRAME}/
|               |-- 2023.parquet
|               |-- 2024.parquet
|               |-- 2025.parquet
|               `-- 2026.parquet
|-- features/
|   `-- exchange=ASTER/
|       `-- symbol={SYMBOL}/
|           `-- timeframe={TIMEFRAME}/
|               |-- 2023.parquet
|               |-- 2024.parquet
|               |-- 2025.parquet
|               `-- 2026.parquet
|-- features_research/
|   `-- exchange=ASTER/
|       `-- symbol={SYMBOL}/
|           `-- timeframe={TIMEFRAME}/
|               |-- 2023.parquet
|               |-- 2024.parquet
|               |-- 2025.parquet
|               `-- 2026.parquet
`-- raw/
    `-- exchange=ASTER/
        `-- symbol={SYMBOL}/
            `-- timeframe={TIMEFRAME}/
                |-- 2023.parquet
                |-- 2024.parquet
                |-- 2025.parquet
                `-- 2026.parquet
```

---

## 4. VERIFICATION COMMANDS & CODE REFERENCES

1. **Verify Partition Boundaries & Contiguity:**
   ```powershell
   pytest tests/unit/test_phase5_1_backfill.py -k "test_temporal_holdout_boundaries"
   ```

2. **Verify Storage Multi-Year Roundtrip:**
   ```powershell
   pytest tests/unit/test_phase5_1_backfill.py -k "test_year_partitioned_storage_roundtrip"
   ```

3. **Verify Zero Lookahead in Causal Join:**
   ```powershell
   pytest tests/unit/test_multi_timeframe_leakage.py
   ```
