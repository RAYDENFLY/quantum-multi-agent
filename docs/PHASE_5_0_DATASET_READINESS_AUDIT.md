# QUANTUM Phase 5.0 - Dataset Readiness Audit

**Role:** Senior Quantitative Research Engineer, ML Research Scientist, and Financial Data Auditor  
**Repository:** https://github.com/RAYDENFLY/quantum-multi-agent  
**Phase:** Phase 5.0 (Dataset Readiness & Target Research)  
**Date:** November 1, 2026  
**Status:** Audit Completed - Empirical Findings Documented  

---

## 1. Executive Summary

This audit establishes whether the historical datasets and ingestion pipeline are statistically and computationally suitable for specialist machine learning research across the target 11 cryptocurrency perpetual instruments:
1. `ADAUSDT.P`
2. `XRPUSDT.P`
3. `BTCUSDT.P`
4. `BNBUSDT.P`
5. `ETHUSDT.P`
6. `SOLUSDT.P`
7. `AVAXUSDT.P`
8. `LINKUSDT.P`
9. `XMRUSDT.P`
10. `DOGEUSDT.P`
11. `LTCUSDT.P`

### Key Audit Findings
1. **Dynamic Exchange Discovery**: AsterDEX lists 644 total perpetual contracts. All 11 target instruments are confirmed active and eligible.
2. **Exchange Historical Depth**: Live API probes to AsterDEX confirm that 10 of the 11 target instruments possess between 4.5 and 5+ years of continuous 5-minute historical data (dating back to September-November 2021). `XMRUSDT` was listed on 2026-01-13 and possesses ~10 months of continuous history.
3. **Local Disk Dataset Inventory**: Local disk storage currently contains verified canonical and feature datasets for `BTCUSDT` and `ETHUSDT` (2,000 candles each on 5m, representing ~7 days of continuous history from a Phase 4 test run). The remaining 9 target instruments have not yet been downloaded to local disk.
4. **Bybit Host Reachability**: The Bybit REST endpoints continue to experience connection timeouts on this specific host machine due to local ISP network routing (TCP SYN drops towards 158.140.186.3).
5. **Statistical Consequence**: The locally resident 2,000-candle sample is insufficient for robust multi-regime specialist ML training (it covers only one market regime). However, the exchange API supports full historical backfill. A comprehensive backfill of the complete 3-year history (~315,000 candles per instrument on 5m) must be executed before Phase 5.1 model training commences.

---

## 2. Source Code Architecture & Ingestion Pipeline Inventory

The table below documents the exact source files and functions responsible for each stage of data retrieval, normalization, feature calculation, and storage:

| Pipeline Stage | Source File | Key Class / Function | Responsibility |
| :--- | :--- | :--- | :--- |
| **Instrument Discovery** | `src/quantum/historical/discovery.py` | `HistoricalInstrumentDiscovery.discover_perpetuals()` | Queries exchange metadata, filters for USDT settlement, `TRADING` status, active contract type. |
| **Historical Retrieval** | `src/quantum/historical/downloader.py` | `HistoricalCandleDownloader._fetch_page_with_retry()` | Issues paginated rate-limited REST requests (`/fapi/v1/klines`, `/v5/market/kline`). |
| **Directional Pagination** | `src/quantum/historical/downloader.py` | `PaginationManager.record_page_results()` | Manages backward/forward cursor navigation and 10,000-page loop ceiling. |
| **Raw Persistence** | `src/quantum/historical/storage.py` | `ParquetStorageManager.write_raw_candles()` | Writes raw strings and `raw_payload_json` to Snappy Parquet with conflict quarantining. |
| **Canonical Normalization** | `src/quantum/historical/downloader.py` | `HistoricalCandleDownloader._parse_aster_page()`, `_parse_bybit_page()` | Converts exchange array rows into typed `CanonicalCandle` objects with inclusive close timestamps. |
| **Data Quality Validation** | `src/quantum/historical/validator.py` | `DataQualityValidator.validate_dataset()` | Audits OHLC invariants, span duration, timestamp alignment, gaps, duplicates, and listing bounds. |
| **Feature Computation** | `src/quantum/features/engine.py` | `FeatureEngine.compute_features()` | Vectorized, scale-invariant computation of 55 technical indicators. |
| **Multi-Timeframe Alignment**| `src/quantum/features/multitimeframe.py`| `MultiTimeframeJoiner.join_htf_features()` | Causal backward as-of join enforcing `HTF.close_time_ms <= LTF.open_time_ms`. |
| **Dataset Loading** | `src/quantum/historical/storage.py` | `ParquetStorageManager.read_canonical()`, `read_features()` | Range-filtered columnar multi-file Parquet reads. |
| **Partition Concurrency** | `src/quantum/historical/storage.py` | `PartitionLock` | Cross-process atomic `.write.lock` with dead PID detection and stale timeout breaking. |

---

## 3. Dynamic Instrument Discovery & Exchange Availability

A live discovery query was executed against AsterDEX public exchange metadata (`https://fapi.asterdex.com/fapi/v1/exchangeInfo`). The exchange reports 644 total perpetual instruments.

### Availability Status Across the 11 Target Pairs

| Target Instrument | AsterDEX Symbol | AsterDEX Status | Bybit Category | Bybit Host Status |
| :--- | :--- | :--- | :--- | :--- |
| **ADAUSDT.P** | `ADAUSDT` | AVAILABLE (Active) | Linear Perpetual | UNREACHABLE (ISP timeout) |
| **XRPUSDT.P** | `XRPUSDT` | AVAILABLE (Active) | Linear Perpetual | UNREACHABLE (ISP timeout) |
| **BTCUSDT.P** | `BTCUSDT` | AVAILABLE (Active) | Linear Perpetual | UNREACHABLE (ISP timeout) |
| **BNBUSDT.P** | `BNBUSDT` | AVAILABLE (Active) | Linear Perpetual | UNREACHABLE (ISP timeout) |
| **ETHUSDT.P** | `ETHUSDT` | AVAILABLE (Active) | Linear Perpetual | UNREACHABLE (ISP timeout) |
| **SOLUSDT.P** | `SOLUSDT` | AVAILABLE (Active) | Linear Perpetual | UNREACHABLE (ISP timeout) |
| **AVAXUSDT.P** | `AVAXUSDT` | AVAILABLE (Active) | Linear Perpetual | UNREACHABLE (ISP timeout) |
| **LINKUSDT.P** | `LINKUSDT` | AVAILABLE (Active) | Linear Perpetual | UNREACHABLE (ISP timeout) |
| **XMRUSDT.P** | `XMRUSDT` | AVAILABLE (Active) | Linear Perpetual | UNREACHABLE (ISP timeout) |
| **DOGEUSDT.P** | `DOGEUSDT` | AVAILABLE (Active) | Linear Perpetual | UNREACHABLE (ISP timeout) |
| **LTCUSDT.P** | `LTCUSDT` | AVAILABLE (Active) | Linear Perpetual | UNREACHABLE (ISP timeout) |

AsterDEX provides 100% contract availability for all 11 target instruments.

---

## 4. Exchange Historical Depth Analysis

Direct endpoint probes were executed against AsterDEX historical klines (`/fapi/v1/klines`) with `startTime=0` to identify the true earliest available candle for each instrument.

### Measured Historical Depth on AsterDEX

| Instrument | Earliest 1d Candle Timestamp | Earliest UTC Date | Available History (as of Nov 2026) | Sample Size (5m equivalent) | Classification |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BTCUSDT** | 1630454400000 | 2021-09-01 00:00 UTC | 5 years, 2 months | ~545,000 candles | SUFFICIENT |
| **ETHUSDT** | 1630972800000 | 2021-09-07 00:00 UTC | 5 years, 2 months | ~543,000 candles | SUFFICIENT |
| **ADAUSDT** | 1631145600000 | 2021-09-09 00:00 UTC | 5 years, 2 months | ~543,000 candles | SUFFICIENT |
| **XRPUSDT** | 1631145600000 | 2021-09-09 00:00 UTC | 5 years, 2 months | ~543,000 candles | SUFFICIENT |
| **SOLUSDT** | 1631145600000 | 2021-09-09 00:00 UTC | 5 years, 2 months | ~543,000 candles | SUFFICIENT |
| **DOGEUSDT** | 1631145600000 | 2021-09-09 00:00 UTC | 5 years, 2 months | ~543,000 candles | SUFFICIENT |
| **AVAXUSDT** | 1637020800000 | 2021-11-16 00:00 UTC | 5 years, 0 months | ~522,000 candles | SUFFICIENT |
| **LTCUSDT** | 1637020800000 | 2021-11-16 00:00 UTC | 5 years, 0 months | ~522,000 candles | SUFFICIENT |
| **BNBUSDT** | 1641254400000 | 2022-01-04 00:00 UTC | 4 years, 10 months | ~507,000 candles | SUFFICIENT |
| **LINKUSDT** | 1649894400000 | 2022-04-14 00:00 UTC | 4 years, 7 months | ~479,000 candles | SUFFICIENT |
| **XMRUSDT** | 1768262400000 | 2026-01-13 00:00 UTC | ~10 months | ~87,000 candles | PARTIAL |

---

## 5. Local Dataset Profiling Results

Local disk inspection in `data/audit_historical/` revealed that real historical datasets currently exist for two instruments: `BTCUSDT` and `ETHUSDT` on the 5-minute timeframe.

### Quantitative Dataset Metrics

| Metric | AsterDEX BTCUSDT 5m | AsterDEX ETHUSDT 5m |
| :--- | :--- | :--- |
| **File Location** | `data/audit_historical/canonical/exchange=ASTER/symbol=BTCUSDT/timeframe=5m/data.parquet` | `data/audit_historical/canonical/exchange=ASTER/symbol=ETHUSDT/timeframe=5m/data.parquet` |
| **Candle Count** | 2,000 | 2,000 |
| **First Available Timestamp** | 1792874700000 (2026-10-24 20:45 UTC) | 1792874700000 (2026-10-24 20:45 UTC) |
| **Last Available Timestamp** | 1793474400000 (2026-10-31 19:20 UTC) | 1793474400000 (2026-10-31 19:20 UTC) |
| **Timestamp Continuity** | Strictly uniform (interval = 300,000 ms) | Strictly uniform (interval = 300,000 ms) |
| **Missing Gaps (> 300,000 ms)** | 0 | 0 |
| **Duplicate Timestamps** | 0 | 0 |
| **Invalid OHLCV Count** | 0 | 0 |
| **Incomplete In-Flight Candles** | 0 | 0 |
| **Coverage Percentage** | 100.0% of local range | 100.0% of local range |
| **Validation Report Status** | `PASS` (`DQR-ASTER-BTCUSDT-5m-1793474680854`) | `PASS` (`DQR-ASTER-ETHUSDT-5m-1793474681776`) |
| **Cryptographic Hash (SHA-256)**| `706c92efa60d39df609bab251ce37021a14eb52cc6f8313d69a64e761830b4f8` | `392408b39c5e47f435780a9c41454de2a48992a70f066d4524348cc5dc5cb7f5` |

### Remaining Target Instruments (Local Status)
- `ADAUSDT`, `XRPUSDT`, `BNBUSDT`, `SOLUSDT`, `AVAXUSDT`, `LINKUSDT`, `XMRUSDT`, `DOGEUSDT`, `LTCUSDT`:
  - **Local Candle Count:** 0
  - **Local Classification:** `UNAVAILABLE LOCALLY`
  - **Exchange Classification:** `SUFFICIENT` on AsterDEX (4.5 to 5+ years available), except `XMRUSDT` which is `PARTIAL` (~10 months available).

---

## 6. Statistical Consequences of Available Sample Sizes

### Scenario A: Training on Current Local Dataset (N = 2,000 candles, ~7 days)
- **Degrees of Freedom**: In a 57-column feature matrix, estimating linear or tree split boundaries with only 2,000 observations leaves fewer than 35 observations per dimension.
- **Regime Homogeneity**: A 7-day period captures only a single, transient volatility and market trend regime. Models trained on 7 days will severely overfit local autocorrelation and fail out-of-sample.
- **Walk-Forward Infeasibility**: Temporal cross-validation with purging and embargoing requires multiple non-overlapping train/val/test splits. A 2,000-candle sample cannot support even a two-fold walk-forward split.
- **Conclusion**: The current local sample is **statistically unsuitable for production specialist ML training**.

### Scenario B: Full Historical Backfill (Target: 3 Years, ~315,000 candles per instrument on 5m)
- **Observations**: 315,360 bars per instrument on 5m, 105,120 bars on 15m, 26,280 bars on 1h.
- **Degrees of Freedom**: Over 5,500 observations per feature dimension.
- **Regime Diversity**: Spans multiple bull, bear, consolidation, flash crash, and macro liquidity regimes across multiple calendar years (2023, 2024, 2025, 2026).
- **Walk-Forward Feasibility**: Ample history to establish a 4-fold expanding-window cross-validation with 30-day embargo periods and a dedicated 6-month out-of-sample holdout.
- **Conclusion**: Statistically robust and required for Phase 5.1.

### Scenario C: XMRUSDT (~10 Months History, ~87,000 candles on 5m)
- **Observations**: ~87,000 bars.
- **Statistical Assessment**: Sufficient sample size for standalone training ($N > 50,000$), but covers only 2026 market regimes. Cross-validation splits must be adapted with smaller window sizes (e.g. 2-month folds rather than 1-year folds).

---

## 7. Audit Recommendations for Dataset Readiness

1. **Mandatory Backfill Execution Prior to Phase 5.1 Training**: Run `HistoricalCandleDownloader` for all 11 target pairs on AsterDEX to pull the targeted 3-year historical dataset across 5m, 15m, and 1h.
2. **Year Partitioning**: Ingest data directly into year-partitioned Parquet files (`2023.parquet`, `2024.parquet`, `2025.parquet`, `2026.parquet`) via `write_canonical_partitioned_by_year` to bound memory consumption under 500 MB.
3. **Bybit Contingency**: Maintain Bybit offline mock verification while operating AsterDEX as the active data provider on this host.
