# QUANTUM MILESTONE 5.13 — BASELINE FORENSICS & RESEARCH ENVIRONMENT AUDIT

**Milestone:** M5.13 — Multi-Factor Confluence & Passive Maker Alpha Discovery  
**Repository:** `d:/quantum-multi-agent`  
**Audit Timestamp:** 2026-11-04T08:11:27.587170+00:00  
**Branch:** `research/quantum-next-3pct`  
**Baseline Commit:** `0088b655714d91e87f0e323743b7d96337c4d915` (`0088b65`)  
**Working Tree Status:** `MODIFIED`  
**Execution Authorization:** STRICTLY RESEARCH & HISTORICAL SIMULATION ONLY  

---

## 1. Repository Topology & Change Control

| Component | Verified State | Governance Note |
| :--- | :--- | :--- |
| **Branch** | `research/quantum-next-3pct` | Authoritative research branch |
| **HEAD Commit** | `0088b65` | Milestone 5.12.2.2.1 Mathematical Integrity commit |
| **Previous Baseline** | `7f1e58c` | M5.12.2.2 Active MTM Risk Control |
| **Remote Synchronization** | Up to date with `origin/research/quantum-next-3pct` | Push verified |
| **Prospective Holdout Start** | `1793491200000` | 2026-11-01T00:00:00Z (SEALED) |
| **Research Equity** | $100.00 | Shared capital pool |
| **Admission Exposure Cap** | 0.995000x | Layer A Pre-trade microstructural safety buffer |
| **Hard Max Gross Exposure** | 1.000000x | Layer B Mark-to-market invariant |

---

## 2. Source Code Cryptographic Fingerprints (SHA-256)

| Source File | SHA-256 Digest |
| :--- | :--- |
| [`src/quantum/accounting/event_ledger.py`](file:///d:/quantum-multi-agent/src/quantum/accounting/event_ledger.py) | `1b6c70c543e336ebf80f6a311e9d0c23d37a68276b60afb1c2190260c5892e37` |
| [`src/quantum/accounting/risk_controller.py`](file:///d:/quantum-multi-agent/src/quantum/accounting/risk_controller.py) | `6c99bea9ddffee4b779e2708b29d19043e5d2c7c8469df2487b3a46c0ed52aa8` |
| [`src/quantum/accounting/fee_schedules.py`](file:///d:/quantum-multi-agent/src/quantum/accounting/fee_schedules.py) | `395a501bc12ceaa0c0b9ac4be8d4bc686b8b288f1bdfff08e855dd2c4a8469d9` |
| [`src/quantum/accounting/execution_economics.py`](file:///d:/quantum-multi-agent/src/quantum/accounting/execution_economics.py) | `eb69edbd63810618cc1c86d86674e96dd8f8bccdfec60e2644cf0305b10ec282` |
| [`src/quantum/accounting/oracle.py`](file:///d:/quantum-multi-agent/src/quantum/accounting/oracle.py) | `43a5d8cde1e5a767658c03592c45c2157142567d477849ebe8e10579ecca6f0c` |
| [`src/quantum/features/market_context.py`](file:///d:/quantum-multi-agent/src/quantum/features/market_context.py) | `a7b6ad2211f2981a2667f92c72092f2743774aaad79f3b71a36c0ac0f0312092` |
| [`src/quantum/features/indicators.py`](file:///d:/quantum-multi-agent/src/quantum/features/indicators.py) | `241b7a1b904823c1566191ffe028c38dc6c5668a3d6abaa9345180b58567b526` |
| [`src/quantum/research/partitioner.py`](file:///d:/quantum-multi-agent/src/quantum/research/partitioner.py) | `c57a0630a19a1dff1a6787935bb492d889858f4a723e69434b4686562a20ea89` |
| [`src/quantum/research/orchestrator.py`](file:///d:/quantum-multi-agent/src/quantum/research/orchestrator.py) | `f5feca7563b0ac01407332edcaced578fb6fa549df6b93bc596511875e4ed3db` |
| [`src/quantum/research/registry.py`](file:///d:/quantum-multi-agent/src/quantum/research/registry.py) | `2bd2af76d199d8e87306cdce94d8f2e628e898ecece5899596a5e9b2aa8e048b` |
| [`src/quantum/research/rejection.py`](file:///d:/quantum-multi-agent/src/quantum/research/rejection.py) | `71161bc5dc22eafa3fc6d53de06cbcc67efa4c6ebd4411ee33a3fb527d2de749` |
| [`src/quantum/strategies/hypothesis_engine.py`](file:///d:/quantum-multi-agent/src/quantum/strategies/hypothesis_engine.py) | `8201ec388675ac0b040c0591d7bda20501f7f8193a9898b7c2b5e3448d7ee53d` |
| [`src/quantum/agents/contracts.py`](file:///d:/quantum-multi-agent/src/quantum/agents/contracts.py) | `e2ca8603bf995b5d5bec36fab2c5998fa15310ed3893b8d7acebdda347ff227e` |

---

## 3. Canonical Market Datasets Inventory

Canonical multi-timeframe historical datasets across 11 symbols on AsterDEX perpetual linear futures venue:

| Symbol | Timeframe | Parquet Files | Total Rows | First Timestamp (UTC) | Last Timestamp (UTC) | Holdout Sealed? |
| :--- | :---: | :---: | :---: | :--- | :--- | :---: |
| `ADAUSDT` | `5m` | 4 | 316,500 | 2023-10-28T21:45:00+00:00 | 2026-10-31T20:44:59.999000+00:00 | YES (PASS) |
| `ADAUSDT` | `15m` | 4 | 106,500 | 2023-10-18T11:45:00+00:00 | 2026-10-31T20:44:59.999000+00:00 | YES (PASS) |
| `ADAUSDT` | `1h` | 4 | 27,000 | 2023-10-02T21:00:00+00:00 | 2026-10-31T20:59:59.999000+00:00 | YES (PASS) |
| `AVAXUSDT` | `5m` | 4 | 316,500 | 2023-10-28T22:15:00+00:00 | 2026-10-31T21:14:59.999000+00:00 | YES (PASS) |
| `AVAXUSDT` | `15m` | 4 | 106,500 | 2023-10-18T12:15:00+00:00 | 2026-10-31T21:14:59.999000+00:00 | YES (PASS) |
| `AVAXUSDT` | `1h` | 4 | 27,000 | 2023-10-02T22:00:00+00:00 | 2026-10-31T21:59:59.999000+00:00 | YES (PASS) |
| `BNBUSDT` | `5m` | 4 | 316,500 | 2023-10-28T22:00:00+00:00 | 2026-10-31T20:59:59.999000+00:00 | YES (PASS) |
| `BNBUSDT` | `15m` | 4 | 106,500 | 2023-10-18T12:00:00+00:00 | 2026-10-31T20:59:59.999000+00:00 | YES (PASS) |
| `BNBUSDT` | `1h` | 4 | 27,000 | 2023-10-02T21:00:00+00:00 | 2026-10-31T20:59:59.999000+00:00 | YES (PASS) |
| `BTCUSDT` | `5m` | 4 | 316,499 | 2023-10-28T22:00:00+00:00 | 2026-10-31T20:59:59.999000+00:00 | YES (PASS) |
| `BTCUSDT` | `15m` | 4 | 106,499 | 2023-10-18T12:00:00+00:00 | 2026-10-31T20:59:59.999000+00:00 | YES (PASS) |
| `BTCUSDT` | `1h` | 4 | 26,999 | 2023-10-02T21:00:00+00:00 | 2026-10-31T20:59:59.999000+00:00 | YES (PASS) |
| `DOGEUSDT` | `5m` | 4 | 316,500 | 2023-10-28T22:25:00+00:00 | 2026-10-31T21:24:59.999000+00:00 | YES (PASS) |
| `DOGEUSDT` | `15m` | 4 | 106,500 | 2023-10-18T12:30:00+00:00 | 2026-10-31T21:29:59.999000+00:00 | YES (PASS) |
| `DOGEUSDT` | `1h` | 4 | 27,000 | 2023-10-02T22:00:00+00:00 | 2026-10-31T21:59:59.999000+00:00 | YES (PASS) |
| `ETHUSDT` | `5m` | 4 | 316,500 | 2023-10-28T22:05:00+00:00 | 2026-10-31T21:04:59.999000+00:00 | YES (PASS) |
| `ETHUSDT` | `15m` | 4 | 106,500 | 2023-10-18T12:15:00+00:00 | 2026-10-31T21:14:59.999000+00:00 | YES (PASS) |
| `ETHUSDT` | `1h` | 4 | 27,000 | 2023-10-02T22:00:00+00:00 | 2026-10-31T21:59:59.999000+00:00 | YES (PASS) |
| `LINKUSDT` | `5m` | 4 | 316,500 | 2023-10-28T22:20:00+00:00 | 2026-10-31T21:19:59.999000+00:00 | YES (PASS) |
| `LINKUSDT` | `15m` | 4 | 106,500 | 2023-10-18T12:30:00+00:00 | 2026-10-31T21:29:59.999000+00:00 | YES (PASS) |
| `LINKUSDT` | `1h` | 4 | 27,000 | 2023-10-02T22:00:00+00:00 | 2026-10-31T21:59:59.999000+00:00 | YES (PASS) |
| `LTCUSDT` | `5m` | 4 | 316,500 | 2023-10-28T22:30:00+00:00 | 2026-10-31T21:29:59.999000+00:00 | YES (PASS) |
| `LTCUSDT` | `15m` | 4 | 106,500 | 2023-10-18T12:30:00+00:00 | 2026-10-31T21:29:59.999000+00:00 | YES (PASS) |
| `LTCUSDT` | `1h` | 4 | 27,000 | 2023-10-02T22:00:00+00:00 | 2026-10-31T21:59:59.999000+00:00 | YES (PASS) |
| `SOLUSDT` | `5m` | 4 | 316,500 | 2023-10-28T22:10:00+00:00 | 2026-10-31T21:09:59.999000+00:00 | YES (PASS) |
| `SOLUSDT` | `15m` | 4 | 106,500 | 2023-10-18T12:15:00+00:00 | 2026-10-31T21:14:59.999000+00:00 | YES (PASS) |
| `SOLUSDT` | `1h` | 4 | 27,000 | 2023-10-02T22:00:00+00:00 | 2026-10-31T21:59:59.999000+00:00 | YES (PASS) |
| `XMRUSDT` | `5m` | 1 | 83,863 | 2026-01-13T16:45:00+00:00 | 2026-10-31T21:19:59.999000+00:00 | YES (PASS) |
| `XMRUSDT` | `15m` | 1 | 27,955 | 2026-01-13T16:45:00+00:00 | 2026-10-31T21:29:59.999000+00:00 | YES (PASS) |
| `XMRUSDT` | `1h` | 1 | 6,990 | 2026-01-13T16:00:00+00:00 | 2026-10-31T21:59:59.999000+00:00 | YES (PASS) |
| `XRPUSDT` | `5m` | 4 | 316,500 | 2023-10-28T21:50:00+00:00 | 2026-10-31T20:49:59.999000+00:00 | YES (PASS) |
| `XRPUSDT` | `15m` | 4 | 106,500 | 2023-10-18T12:00:00+00:00 | 2026-10-31T20:59:59.999000+00:00 | YES (PASS) |
| `XRPUSDT` | `1h` | 4 | 27,000 | 2023-10-02T21:00:00+00:00 | 2026-10-31T20:59:59.999000+00:00 | YES (PASS) |

---

## 4. Authoritative Fee Schedule & Execution Economics

| Parameter | Value | Reference / Profile |
| :--- | :--- | :--- |
| **Schedule Identifier** | `ASTERDEX_BASE_RETAIL_v1` | Primary Venue |
| **Exchange Venue** | `AsterDEX` | USDT Linear Perpetual |
| **Fee Tier** | `Base_Retail_Tier` | Retail Tier |
| **Maker Fee (per leg)** | `4.0 bps` | Passive limit orders |
| **Taker Fee (per leg)** | `10.0 bps` | Aggressive market orders |
| **Half-Spread** | `1.0 bps` | Crossing top of book |
| **Slippage (per leg)** | `2.0 bps` | Modeled execution drag |
| **Adverse Selection (Maker)** | `1.5 bps` | Modeled toxic flow markout |
| **Roundtrip Taker Friction** | `26.0 bps` | Total friction (10+10+1+1+2+2) |
| **Roundtrip Maker Friction** | `11.0 bps` | Total friction (4+4+1.5+1.5) |
| **Schedule SHA-256 Fingerprint** | `4f0b27f782d2456ad7849b7c67f8fb5516284f6a7f50938fc072842882220bcb` | Cryptographically verified |

---

## 5. Architectural Components Verification

1. **Layer A Pre-Trade Admission Buffer:** Configured at `0.995000x` in `EventDrivenPortfolioLedger` and `IndependentAccountingOracle`.
2. **Layer B Active MTM Risk Controller:** `ActiveMTMMonitor` calculates 15-field snapshot; `RiskStateMachine` enforces 6 states (`NORMAL`, `WARNING`, `REDUCE_ONLY`, `CRITICAL`, `HALTED`, `RUIN`) with `0.0050` hysteresis buffer.
3. **Deleveraging Sizing Closed-Form Formula:** Implemented in `DeleveragingEngine.compute_excess_notional` as $\Delta N^* = \frac{N - \theta^* E}{1 - \theta^* f}$.
4. **Six-Agent Architecture:** Scout, Analyst, Sniper, Risk, Banker, and Orchestrator have defined research contracts with zero shared-state mutation.
5. **Data Isolation Invariant:** All canonical datasets strictly terminate before timestamp `1,793,491,200,000` (2026-11-01T00:00:00Z). Prospective holdout boundary is 100% sealed.