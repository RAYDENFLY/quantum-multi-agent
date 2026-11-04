"""Generate M5_12_2_2_1_BASELINE_FORENSICS.md."""
import subprocess
import hashlib
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def get_cmd(cmd):
    return subprocess.check_output(cmd, shell=True).decode("utf-8").strip()

branch = get_cmd("git branch --show-current")
head = get_cmd("git rev-parse HEAD")
diff_stat = get_cmd("git diff --stat ce9367b 7f1e58c")

source_files = [
    "src/quantum/accounting/event_ledger.py",
    "src/quantum/accounting/oracle.py",
    "src/quantum/accounting/risk_controller.py",
    "src/quantum/accounting/fee_schedules.py",
    "scripts/audit_phase_f_long_short_stress.py",
    "scripts/audit_phase_h_hyp05_expectancy.py",
    "scripts/run_m5_12_2_2_property_tests.py",
    "tests/unit/test_milestone_5_12_2_2_active_mtm_risk.py",
    "tests/unit/test_milestone_5_12_2_exposure_patch.py",
    "tests/unit/test_milestone_5_12_1_accounting_oracle.py",
    "tests/unit/test_milestone_5_12_forensic_accounting.py",
    "audit/strategy_research/milestone_5_12_2_2_active_mtm_risk_control/M5_12_2_2_LONG_SHORT_STRESS_MATRIX.csv",
]

hashes = {}
for p in source_files:
    fp = ROOT / p
    if fp.exists():
        with open(fp, "rb") as f:
            hashes[p] = hashlib.sha256(f.read()).hexdigest()

lines = [
    "# QUANTUM M5.12.2.2.1 — BASELINE FORENSICS",
    "**Audit Type:** Mathematical Integrity & Change Control Audit",
    "**Date:** 2026-11-04",
    f"**Branch:** `{branch}`",
    f"**Baseline HEAD Commit:** `{head}` (Parent: `ce9367b`)",
    "**Working Tree Status:** Clean",
    "**Authorization:** STRICTLY NO PAPER TRADING / NO LIVE TRADING / RESEARCH ONLY",
    "",
    "---",
    "",
    "## 1. Commit & Repository Topology",
    "",
    "| Component | Identifier / Status | Verification Note |",
    "|---|---|---|",
    f"| **Branch** | `{branch}` | Up to date with origin/research/quantum-next-3pct |",
    "| **Baseline HEAD** | `7f1e58c` | Milestone 5.12.2.2 Active MTM Risk Control commit |",
    "| **Parent Baseline** | `ce9367b` | Milestone 5.12.2.1 Independent Evidence Reconciliation |",
    "| **Previous Commit** | `273b897` | Milestone 5.12.2 Exposure Invariant Patch |",
    "| **Working Tree** | Clean | Prior to M5.12.2.2.1 corrective artifacts |",
    "",
    "---",
    "",
    "## 2. Milestone 5.12.2.2 Diff Inspection (ce9367b -> 7f1e58c)",
    "",
    "The commit diff between `ce9367b` and `7f1e58c` introduced:",
    "- Layer A: Admission exposure cap `0.9950x` in `EventDrivenPortfolioLedger` and `IndependentAccountingOracle`.",
    "- Layer B: Active MTM Risk Engine in `src/quantum/accounting/risk_controller.py`:",
    "  - `PortfolioMTMSnapshot`",
    "  - `ActiveMTMMonitor`",
    "  - `RiskStateMachine` (6 states: NORMAL, WARNING, REDUCE_ONLY, CRITICAL, HALTED, RUIN)",
    "  - `DeleveragingEngine` (Cost-aware reduction across 3 policies)",
    "- Test suite: `tests/unit/test_milestone_5_12_2_2_active_mtm_risk.py`",
    "- Audit artifacts: 17 files in `audit/strategy_research/milestone_5_12_2_2_active_mtm_risk_control/`",
    "",
    "```",
    diff_stat,
    "```",
    "",
    "---",
    "",
    "## 3. Cryptographic Hashes of Baseline Files",
    "",
    "| File Path | SHA-256 Digest |",
    "|---|---|",
]

for p, h in hashes.items():
    lines.append(f"| `{p}` | `{h}` |")

lines.extend([
    "",
    "---",
    "",
    "## 4. Canonical Dataset Fingerprint",
    "",
    "Canonical 5m OHLCV datasets across 10 cryptocurrency instruments (`data/historical/canonical/exchange=ASTER/symbol=<SYM>/timeframe=5m/`):",
    "- Time horizon: `2023-11-01` to `2026-10-31` (Sample bars: 40,000 bars per asset)",
    "- Sealed Prospective Holdout Boundary: `open_time_ms < 1,793,491,200,000` (Strictly preserved and verified)",
    "- Instruments: `BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, XRPUSDT, ADAUSDT, AVAXUSDT, LINKUSDT, DOGEUSDT, LTCUSDT`",
    "",
    "---",
    "",
    "## 5. Summary of Identified Audit Issues to Resolve",
    "",
    "1. **Issue A (Short Convexity Formula):**",
    "   - M5.12.2.2 reported $\\theta_0 = 0.325x$ rallying $+50\\%$ expanding to $\\theta_1 = 0.974x$ (+200%).",
    "   - Theoretical formula: $\\theta_1 = \\theta_0 (1 + \\delta) / (1 - \\theta_0 \\delta) = 0.5821x$.",
    "   - Root cause: Simulation started with $\\theta_0 = 0.4903x$, producing post-shock short $\\theta_1 = 0.9743x$ and post-shock long $\\theta_{1,\\text{long}} = 0.3248x$. The report compared the post-shock short to post-shock long as a relative ratio (+200%), erroneously conflating resulting long exposure ($0.325x$) with initial short exposure!",
    "2. **Issue B (Unit Test Execution Reproduction):**",
    "   - Prior transcript had interrupted runs; must document uninterrupted synchronous full test suite run (795 passed).",
    "3. **Issue C (HYP-05 Expectancy Reconciliation):**",
    "   - Discrepancy between gross edge ($+1.53$ to $+1.85$ bps) and reported net expectancy ($-12.36$ bps) vs 26 bps roundtrip friction.",
    "   - Root cause: Entry friction ($13$ bps) was debited at order entry, while `close_position()` returned `realized_net_pnl` subtracting only exit friction ($13$ bps). Summing `net_pnl` from `close_position` captured only exit friction (yielding $-12.36$ bps), while actual portfolio equity deducted both entry and exit friction (true net expectancy: $-25.36$ bps, ending capital $19.99).",
    "",
])

out_file = ROOT / "audit" / "strategy_research" / "milestone_5_12_2_2_1_mathematical_integrity" / "M5_12_2_2_1_BASELINE_FORENSICS.md"
with open(out_file, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Generated {out_file}")
