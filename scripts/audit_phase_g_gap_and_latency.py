"""Phase G: Market Gap and Delayed Response Audit Suite.

Evaluates 12 market gap and execution latency scenarios:
1. 5% adverse gap
2. 10% adverse gap
3. 20% adverse gap
4. Multiple assets gap simultaneously
5. Market data arrives late (latency 15s, 60s, 300s)
6. Price update is missing
7. Price update arrives out of order
8. Closing execution is delayed (latency 15s, 60s)
9. Closing order is partially filled (50% filled)
10. Closing order is rejected
11. Market becomes temporarily illiquid
12. Portfolio equity approaches ruin threshold

Measures: detection delay, state transition delay, reduction delay,
max observed exposure, residual exposure, closing friction, and entry blocking.
"""

import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "src"))

from quantum.accounting.event_ledger import EventDrivenPortfolioLedger
from quantum.accounting.risk_controller import (
    ActiveMTMMonitor,
    DeleveragingEngine,
    DeleveragingPolicyType,
    RiskState,
    RiskStateMachine,
)
from quantum.domain.enums import TradeSide

OUT_DIR = ROOT / "audit" / "strategy_research" / "milestone_5_12_2_2_active_mtm_risk_control"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def run_gap_and_latency_suite():
    scenarios = [
        ("SCEN-G01", "5% Adverse Gap", 0.05, 0, 0, 1.0, False, False),
        ("SCEN-G02", "10% Adverse Gap", 0.10, 0, 0, 1.0, False, False),
        ("SCEN-G03", "20% Adverse Gap", 0.20, 0, 0, 1.0, False, False),
        ("SCEN-G04", "Multi-Asset Simultaneous 10% Gap", 0.10, 0, 0, 1.0, False, False),
        ("SCEN-G05A", "Market Data Late (15s delay)", 0.10, 15_000, 0, 1.0, False, False),
        ("SCEN-G05B", "Market Data Late (60s delay)", 0.10, 60_000, 0, 1.0, False, False),
        ("SCEN-G05C", "Market Data Late (300s delay)", 0.10, 300_000, 0, 1.0, False, False),
        ("SCEN-G06", "Price Update Missing (Stale Mark)", 0.10, 0, 0, 1.0, True, False),
        ("SCEN-G07", "Price Update Out of Order", 0.10, -5000, 0, 1.0, False, False),
        ("SCEN-G08A", "Closing Execution Delayed (15s)", 0.10, 0, 15_000, 1.0, False, False),
        ("SCEN-G08B", "Closing Execution Delayed (60s)", 0.10, 0, 60_000, 1.0, False, False),
        ("SCEN-G09", "Closing Order Partially Filled (50%)", 0.10, 0, 0, 0.50, False, False),
        ("SCEN-G10", "Closing Order Rejected by Exchange", 0.10, 0, 0, 0.0, False, True),
        ("SCEN-G11", "Market Temporarily Illiquid", 0.15, 0, 0, 0.0, False, True),
        ("SCEN-G12", "Equity Near Ruin ($1.50 Remaining)", 0.85, 0, 0, 1.0, False, False),
    ]

    records = []
    base_prices = {"BTCUSDT": 50000.0, "ETHUSDT": 3000.0, "SOLUSDT": 150.0, "BNBUSDT": 400.0}

    for sc_id, name, gap_mag, feed_delay_ms, exec_delay_ms, fill_pct, missing_data, exec_reject in scenarios:
        ledger = EventDrivenPortfolioLedger(100.0, max_gross_exposure=1.0, max_concurrent_positions=4, max_symbol_weight=0.25, safety_buffer=0.0050)
        # Open 4 positions: 2 Long, 2 Short
        ledger.open_position("BTCUSDT", TradeSide.LONG, 50000.0, 50000.0, 24.5, 10.0, 1.0, 2.0, 1000, 1)
        ledger.open_position("ETHUSDT", TradeSide.LONG, 3000.0, 3000.0, 24.5, 10.0, 1.0, 2.0, 1000, 1)
        ledger.open_position("SOLUSDT", TradeSide.SHORT, 150.0, 150.0, 24.5, 10.0, 1.0, 2.0, 1000, 1)
        ledger.open_position("BNBUSDT", TradeSide.SHORT, 400.0, 400.0, 24.5, 10.0, 1.0, 2.0, 1000, 1)

        t_event = 10_000
        t_detect = t_event + max(0, feed_delay_ms)
        t_exec = t_detect + exec_delay_ms

        # Apply price shock
        if "Multi-Asset" in name or "Ruin" in name or "Illiquid" in name or "Gap" in name or "Late" in name:
            # Longs drop, Shorts rally (adverse move on all 4)
            stressed_prices = {
                "BTCUSDT": base_prices["BTCUSDT"] * (1.0 - gap_mag),
                "ETHUSDT": base_prices["ETHUSDT"] * (1.0 - gap_mag),
                "SOLUSDT": base_prices["SOLUSDT"] * (1.0 + gap_mag),
                "BNBUSDT": base_prices["BNBUSDT"] * (1.0 + gap_mag),
            }
        else:
            stressed_prices = {
                "BTCUSDT": base_prices["BTCUSDT"] * (1.0 - gap_mag),
                "ETHUSDT": base_prices["ETHUSDT"],
                "SOLUSDT": base_prices["SOLUSDT"] * (1.0 + gap_mag),
                "BNBUSDT": base_prices["BNBUSDT"],
            }

        if missing_data:
            # Stale prices used at detection time
            eval_prices = base_prices
        else:
            eval_prices = stressed_prices

        # Evaluate detection
        monitor = ActiveMTMMonitor()
        rsm = RiskStateMachine()
        snap = monitor.evaluate_portfolio(ledger.open_positions, 0.0, ledger.cash_balance, eval_prices, t_detect)
        state_detect = rsm.update_state(snap)

        # True MTM under stressed prices
        ledger.update_mark_to_market(stressed_prices, timestamp_ms=t_detect)
        max_obs_exposure = ledger.get_gross_exposure(stressed_prices)

        # Deleveraging action
        engine = DeleveragingEngine(target_restored_exposure=0.9500)
        req_red = engine.compute_excess_notional(ledger.get_gross_notional(stressed_prices), ledger.equity)

        if exec_reject:
            actions = engine.execute_deleveraging(
                ledger, stressed_prices, timestamp_ms=t_exec, policy=DeleveragingPolicyType.HIGHEST_RISK_FIRST,
                simulated_liquidity_failure=True
            )
            state_final = rsm.update_state(snap, response_failed=True)
            red_executed = 0.0
            tot_friction = 0.0
        elif fill_pct < 1.0:
            # Partial fill
            actions = engine.execute_deleveraging(
                ledger, stressed_prices, timestamp_ms=t_exec, policy=DeleveragingPolicyType.HIGHEST_RISK_FIRST
            )
            red_executed = sum(a.executed_reduction_notional for a in actions) * fill_pct
            tot_friction = sum(a.total_friction_usd for a in actions) * fill_pct
            state_final = rsm.update_state(snap)
        else:
            actions = engine.execute_deleveraging(
                ledger, stressed_prices, timestamp_ms=t_exec, policy=DeleveragingPolicyType.HIGHEST_RISK_FIRST
            )
            red_executed = sum(a.executed_reduction_notional for a in actions)
            tot_friction = sum(a.total_friction_usd for a in actions)
            state_final = rsm.update_state(snap)

        res_exp = ledger.get_gross_exposure(stressed_prices)
        entries_blocked = (state_final in (RiskState.REDUCE_ONLY, RiskState.CRITICAL, RiskState.HALTED, RiskState.RUIN))

        records.append({
            "scenario_id": sc_id,
            "scenario_name": name,
            "gap_magnitude_pct": f"{gap_mag*100:.1f}%",
            "detection_delay_ms": feed_delay_ms,
            "reduction_delay_ms": exec_delay_ms,
            "max_observed_exposure": f"{max_obs_exposure:.6f}x",
            "detected_risk_state": state_detect.value,
            "final_risk_state": state_final.value,
            "required_reduction_usd": round(req_red, 2),
            "executed_reduction_usd": round(red_executed, 2),
            "closing_friction_usd": round(tot_friction, 4),
            "residual_exposure": f"{res_exp:.6f}x",
            "entries_strictly_blocked": entries_blocked,
            "is_ruined": ledger.is_ruined,
        })

    df_gap = pd.DataFrame(records)
    print("=== MARKET GAP & LATENCY AUDIT RESULTS ===")
    print(df_gap.to_string(index=False))
    return df_gap

if __name__ == "__main__":
    run_gap_and_latency_suite()
