# QUANTUM M5.12.2.2.1 — BASELINE FORENSICS
**Audit Type:** Mathematical Integrity & Change Control Audit
**Date:** 2026-11-04
**Branch:** `research/quantum-next-3pct`
**Baseline HEAD Commit:** `7f1e58c2b7698e36fe7f4e0af32a559e5e044ce9` (Parent: `ce9367b`)
**Working Tree Status:** Clean
**Authorization:** STRICTLY NO PAPER TRADING / NO LIVE TRADING / RESEARCH ONLY

---

## 1. Commit & Repository Topology

| Component | Identifier / Status | Verification Note |
|---|---|---|
| **Branch** | `research/quantum-next-3pct` | Up to date with origin/research/quantum-next-3pct |
| **Baseline HEAD** | `7f1e58c` | Milestone 5.12.2.2 Active MTM Risk Control commit |
| **Parent Baseline** | `ce9367b` | Milestone 5.12.2.1 Independent Evidence Reconciliation |
| **Previous Commit** | `273b897` | Milestone 5.12.2 Exposure Invariant Patch |
| **Working Tree** | Clean | Prior to M5.12.2.2.1 corrective artifacts |

---

## 2. Milestone 5.12.2.2 Diff Inspection (ce9367b -> 7f1e58c)

The commit diff between `ce9367b` and `7f1e58c` introduced:
- Layer A: Admission exposure cap `0.9950x` in `EventDrivenPortfolioLedger` and `IndependentAccountingOracle`.
- Layer B: Active MTM Risk Engine in `src/quantum/accounting/risk_controller.py`:
  - `PortfolioMTMSnapshot`
  - `ActiveMTMMonitor`
  - `RiskStateMachine` (6 states: NORMAL, WARNING, REDUCE_ONLY, CRITICAL, HALTED, RUIN)
  - `DeleveragingEngine` (Cost-aware reduction across 3 policies)
- Test suite: `tests/unit/test_milestone_5_12_2_2_active_mtm_risk.py`
- Audit artifacts: 17 files in `audit/strategy_research/milestone_5_12_2_2_active_mtm_risk_control/`

```
.../M5_12_2_2_ACCEPTANCE_MATRIX.csv                |  16 +
 .../M5_12_2_2_ADMISSION_BUFFER_AUDIT.md            |  95 ++++
 .../M5_12_2_2_BASELINE_FORENSICS.md                | 167 +++++++
 .../M5_12_2_2_DELEVERAGING_COMPARISON.csv          |   5 +
 .../M5_12_2_2_DELEVERAGING_POLICY.md               |  63 +++
 .../M5_12_2_2_EXECUTIVE_SUMMARY.md                 | 148 +++++++
 .../M5_12_2_2_GAP_AND_LATENCY_AUDIT.md             |  67 +++
 .../M5_12_2_2_HYP05_NET_EXPECTANCY_AUDIT.md        |  72 +++
 .../M5_12_2_2_LIMITATIONS_AND_RISKS.md             |  64 +++
 .../M5_12_2_2_LONG_SHORT_STRESS_MATRIX.csv         | 161 +++++++
 .../M5_12_2_2_LONG_SHORT_STRESS_TEST.md            |  82 ++++
 .../M5_12_2_2_MTM_MONITOR_DESIGN.md                | 100 +++++
 .../M5_12_2_2_PROPERTY_TEST_FAILURES.jsonl         |   0
 .../M5_12_2_2_PROPERTY_TEST_REPORT.md              |  93 ++++
 .../M5_12_2_2_PROPERTY_TEST_SUMMARY.csv            |  11 +
 .../M5_12_2_2_RISK_STATE_MACHINE.md                |  91 ++++
 .../M5_12_2_2_TEST_REPORT.md                       |  77 ++++
 scripts/audit_phase_b_admission_boundaries.py      | 115 +++++
 scripts/audit_phase_b_admission_justification.py   |  70 +++
 scripts/audit_phase_d_risk_state_machine.py        |  87 ++++
 scripts/audit_phase_e_deleveraging_comparison.py   | 138 ++++++
 scripts/audit_phase_f_long_short_stress.py         | 221 +++++++++
 scripts/audit_phase_g_gap_and_latency.py           | 163 +++++++
 scripts/audit_phase_h_hyp05_expectancy.py          | 188 ++++++++
 scripts/run_m5_12_2_2_property_tests.py            | 268 +++++++++++
 src/quantum/accounting/event_ledger.py             |  47 +-
 src/quantum/accounting/oracle.py                   |  28 +-
 src/quantum/accounting/risk_controller.py          | 492 +++++++++++++++++++++
 .../test_milestone_5_12_1_accounting_oracle.py     |   2 +-
 .../test_milestone_5_12_2_2_active_mtm_risk.py     | 160 +++++++
 tests/unit/test_milestone_5_12_2_exposure_patch.py |   2 +-
 .../test_milestone_5_12_forensic_accounting.py     |   6 +-
 32 files changed, 3268 insertions(+), 31 deletions(-)
```

---

## 3. Cryptographic Hashes of Baseline Files

| File Path | SHA-256 Digest |
|---|---|
| `src/quantum/accounting/event_ledger.py` | `1b6c70c543e336ebf80f6a311e9d0c23d37a68276b60afb1c2190260c5892e37` |
| `src/quantum/accounting/oracle.py` | `43a5d8cde1e5a767658c03592c45c2157142567d477849ebe8e10579ecca6f0c` |
| `src/quantum/accounting/risk_controller.py` | `6c99bea9ddffee4b779e2708b29d19043e5d2c7c8469df2487b3a46c0ed52aa8` |
| `src/quantum/accounting/fee_schedules.py` | `395a501bc12ceaa0c0b9ac4be8d4bc686b8b288f1bdfff08e855dd2c4a8469d9` |
| `scripts/audit_phase_f_long_short_stress.py` | `40d5afbac889abccdbe5dc1266da21bd51e52377dbd4f3e1febdd21cde9757d9` |
| `scripts/audit_phase_h_hyp05_expectancy.py` | `f634552e57dca8b2d4ec498fc920aaff4877cc61d351a5729563cc79cc0badc0` |
| `scripts/run_m5_12_2_2_property_tests.py` | `40d3c9cf1f29ef67fbd0f88f52096575c3e2cfbd675e0339f6682cd70ea3d018` |
| `tests/unit/test_milestone_5_12_2_2_active_mtm_risk.py` | `33605dfdb1ce9c310cd97be7687f37a674114c62d879966a906cd8ccab4a69fa` |
| `tests/unit/test_milestone_5_12_2_exposure_patch.py` | `25f8905756ccd4ff3f1f43d50775b00edd6b4bf9d0fd82ed1fc81e9969408d7d` |
| `tests/unit/test_milestone_5_12_1_accounting_oracle.py` | `6ad66837c3a3ae6ce47a021af08efe43d4d0846fbf47fd9550f256c7733f7015` |
| `tests/unit/test_milestone_5_12_forensic_accounting.py` | `acd13ca8a255b862f5735ba7c2532d53c6799555fc316f75a886b4100d01f940` |
| `audit/strategy_research/milestone_5_12_2_2_active_mtm_risk_control/M5_12_2_2_LONG_SHORT_STRESS_MATRIX.csv` | `00f5ff9b6d525f66ba07eb3e542a81c17c845b462b2cc831930a24b6182e6bf1` |

---

## 4. Canonical Dataset Fingerprint

Canonical 5m OHLCV datasets across 10 cryptocurrency instruments (`data/historical/canonical/exchange=ASTER/symbol=<SYM>/timeframe=5m/`):
- Time horizon: `2023-11-01` to `2026-10-31` (Sample bars: 40,000 bars per asset)
- Sealed Prospective Holdout Boundary: `open_time_ms < 1,793,491,200,000` (Strictly preserved and verified)
- Instruments: `BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, ADAUSDT, AVAXUSDT, LINKUSDT, DOGEUSDT, LTCUSDT`

---

## 5. Summary of Identified Audit Issues to Resolve

1. **Issue A (Short Convexity Formula):**
   - M5.12.2.2 reported $\theta_0 = 0.325x$ rallying $+50\%$ expanding to $\theta_1 = 0.974x$ (+200%).
   - Theoretical formula: $\theta_1 = \theta_0 (1 + \delta) / (1 - \theta_0 \delta) = 0.5821x$.
   - Root cause: Simulation started with $\theta_0 = 0.4903x$, producing post-shock short $\theta_1 = 0.9743x$ and post-shock long $\theta_{1,\text{long}} = 0.3248x$. The report compared the post-shock short to post-shock long as a relative ratio (+200%), erroneously conflating resulting long exposure ($0.325x$) with initial short exposure!
2. **Issue B (Unit Test Execution Reproduction):**
   - Prior transcript had interrupted runs; must document uninterrupted synchronous full test suite run (795 passed).
3. **Issue C (HYP-05 Expectancy Reconciliation):**
   - Discrepancy between gross edge ($+1.53$ to $+1.85$ bps) and reported net expectancy ($-12.36$ bps) vs 26 bps roundtrip friction.
   - Root cause: Entry friction ($13$ bps) was debited at order entry, while `close_position()` returned `realized_net_pnl` subtracting only exit friction ($13$ bps). Summing `net_pnl` from `close_position` captured only exit friction (yielding $-12.36$ bps), while actual portfolio equity deducted both entry and exit friction (true net expectancy: $-25.36$ bps, ending capital $19.99).
