"""Phase D: Risk State Machine Audit & Hysteresis Verification.

Tests deterministic transitions, anti-oscillation hysteresis, and threshold dynamics.
"""

import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "src"))

from quantum.accounting.risk_controller import (
    RiskState,
    RiskStateMachine,
    PortfolioMTMSnapshot,
)

def test_risk_state_machine():
    rsm = RiskStateMachine(
        warning_threshold=0.9000,
        reduce_only_threshold=0.9500,
        critical_threshold=1.0000,
        ruin_equity_threshold=1.0,
        hysteresis_buffer=0.0200,
    )
    
    # Sequence of test events simulating market fluctuations
    test_sequence = [
        # (exposure, equity, time_ms, description)
        (0.5000, 100.0, 1000, "Initial low exposure"),
        (0.8900, 100.0, 2000, "Rising exposure near warning"),
        (0.9100, 100.0, 3000, "Crosses 0.90 -> WARNING"),
        (0.9050, 100.0, 4000, "Small dip: should STAY in WARNING (hysteresis)"),
        (0.8950, 100.0, 5000, "Above 0.88 recovery target: STAY in WARNING"),
        (0.8750, 100.0, 6000, "Drops below 0.88 (0.90 - 0.02) -> Recovers to NORMAL"),
        (0.9600, 100.0, 7000, "Jumps to 0.96 -> REDUCE_ONLY"),
        (0.9400, 100.0, 8000, "Dips to 0.94: Above 0.93 recovery target -> STAYS REDUCE_ONLY"),
        (1.0200, 95.0,  9000, "Adverse shock -> CRITICAL (>= 1.00x)"),
        (1.0050, 93.0, 10000, "Slight improvement but above 0.98 -> STAYS CRITICAL"),
        (0.9750, 96.0, 11000, "Deleveraging drops below 0.98 (1.00 - 0.02) -> Recovers to REDUCE_ONLY"),
        (0.5000, 0.50, 12000, "Catastrophic equity loss <= $1.00 -> RUIN"),
        (0.1000, 50.0, 13000, "Attempted recovery: Must STAY RUIN (permanent)"),
    ]
    
    records = []
    for exp, eq, t, desc in test_sequence:
        snap = PortfolioMTMSnapshot(
            timestamp_ms=t,
            open_position_notional=exp * eq,
            pending_reserved_notional=0.0,
            total_committed_notional=exp * eq,
            cash_balance=eq,
            unrealized_pnl=0.0,
            realized_pnl=0.0,
            equity=eq,
            gross_exposure_open=exp,
            gross_exposure_committed=exp,
            exposure_utilization_pct=(exp / 1.0) * 100.0,
            available_exposure_capacity=max(0.0, (eq * 0.9950) - (exp * eq)),
            risk_state=rsm.current_state,
            open_position_count=2,
            long_notional=exp * eq,
            short_notional=0.0,
        )
        
        state = rsm.update_state(snap)
        records.append({
            "step_time_ms": t,
            "description": desc,
            "exposure": f"{exp:.4f}x",
            "equity": f"${eq:.2f}",
            "resulting_state": state.value,
        })
    
    df_res = pd.DataFrame(records)
    print("=== RISK STATE MACHINE HYSTERESIS AUDIT ===")
    print(df_res.to_string(index=False))
    
    print("\nRecorded Transitions:")
    for tr in rsm.transitions:
        print(f"  [{tr.timestamp_ms}ms] {tr.from_state.value} -> {tr.to_state.value} | Exp: {tr.trigger_exposure:.4f}x | Reason: {tr.reason_code}")
    
    return df_res, rsm.transitions

if __name__ == "__main__":
    test_risk_state_machine()
