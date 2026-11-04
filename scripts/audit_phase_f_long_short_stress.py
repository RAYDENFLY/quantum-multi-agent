"""Phase F: Long/Short Asymmetric Stress Testing Suite.

Executes 160 deterministic stress scenarios:
- 16 Price Shock Magnitudes: ±0.5%, ±1%, ±2%, ±5%, ±10%, ±20%, ±30%, ±50%
- 10 Portfolio Configurations:
  1. Single LONG
  2. Single SHORT
  3. Four LONG positions
  4. Four SHORT positions
  5. Mixed LONG/SHORT (2 Long, 2 Short)
  6. Ten-asset diversified portfolio
  7. Correlated altcoin exposure
  8. Highly concentrated portfolio
  9. Pending orders plus open positions
  10. Portfolio close to admission cap (0.9950x)

Evaluates equity, notional, MTM exposure, risk state, required reduction,
actual simulated reduction, closing friction, and residual exposure.
"""

import sys
from pathlib import Path
from typing import Dict, List, Tuple
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

SHOCKS = [
    -0.50, -0.30, -0.20, -0.10, -0.05, -0.02, -0.01, -0.005,
     0.005,  0.01,  0.02,  0.05,  0.10,  0.20,  0.30,  0.50
]

CONFIG_NAMES = [
    "CFG-01_SINGLE_LONG",
    "CFG-02_SINGLE_SHORT",
    "CFG-03_FOUR_LONG",
    "CFG-04_FOUR_SHORT",
    "CFG-05_MIXED_LONG_SHORT",
    "CFG-06_TEN_ASSET_DIVERSIFIED",
    "CFG-07_CORRELATED_ALTCOIN",
    "CFG-08_HIGHLY_CONCENTRATED",
    "CFG-09_PENDING_PLUS_OPEN",
    "CFG-10_CLOSE_TO_ADMISSION_CAP",
]


def setup_portfolio_config(config_name: str) -> Tuple[EventDrivenPortfolioLedger, Dict[str, float]]:
    """Builds a fresh portfolio configured for the specified stress scenario."""
    base_prices = {
        "BTCUSDT": 50000.0, "ETHUSDT": 3000.0, "SOLUSDT": 150.0, "BNBUSDT": 400.0,
        "XRPUSDT": 0.50, "ADAUSDT": 0.40, "AVAXUSDT": 30.0, "LINKUSDT": 15.0,
        "DOGEUSDT": 0.10, "LTCUSDT": 70.0,
    }
    
    if config_name == "CFG-01_SINGLE_LONG":
        ledger = EventDrivenPortfolioLedger(100.0, max_gross_exposure=1.0, max_symbol_weight=0.50, safety_buffer=0.0050)
        ledger.open_position("BTCUSDT", TradeSide.LONG, 50000.0, 50000.0, 49.0, 10.0, 1.0, 2.0, 1000, 1)
        
    elif config_name == "CFG-02_SINGLE_SHORT":
        ledger = EventDrivenPortfolioLedger(100.0, max_gross_exposure=1.0, max_symbol_weight=0.50, safety_buffer=0.0050)
        ledger.open_position("BTCUSDT", TradeSide.SHORT, 50000.0, 50000.0, 49.0, 10.0, 1.0, 2.0, 1000, 1)
        
    elif config_name == "CFG-03_FOUR_LONG":
        ledger = EventDrivenPortfolioLedger(100.0, max_gross_exposure=1.0, max_concurrent_positions=4, max_symbol_weight=0.25, safety_buffer=0.0050)
        for s in ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]:
            ledger.open_position(s, TradeSide.LONG, base_prices[s], base_prices[s], 24.5, 10.0, 1.0, 2.0, 1000, 1)
            
    elif config_name == "CFG-04_FOUR_SHORT":
        ledger = EventDrivenPortfolioLedger(100.0, max_gross_exposure=1.0, max_concurrent_positions=4, max_symbol_weight=0.25, safety_buffer=0.0050)
        for s in ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]:
            ledger.open_position(s, TradeSide.SHORT, base_prices[s], base_prices[s], 24.5, 10.0, 1.0, 2.0, 1000, 1)
            
    elif config_name == "CFG-05_MIXED_LONG_SHORT":
        ledger = EventDrivenPortfolioLedger(100.0, max_gross_exposure=1.0, max_concurrent_positions=4, max_symbol_weight=0.25, safety_buffer=0.0050)
        ledger.open_position("BTCUSDT", TradeSide.LONG, 50000.0, 50000.0, 24.5, 10.0, 1.0, 2.0, 1000, 1)
        ledger.open_position("ETHUSDT", TradeSide.LONG, 3000.0, 3000.0, 24.5, 10.0, 1.0, 2.0, 1000, 1)
        ledger.open_position("SOLUSDT", TradeSide.SHORT, 150.0, 150.0, 24.5, 10.0, 1.0, 2.0, 1000, 1)
        ledger.open_position("BNBUSDT", TradeSide.SHORT, 400.0, 400.0, 24.5, 10.0, 1.0, 2.0, 1000, 1)
        
    elif config_name == "CFG-06_TEN_ASSET_DIVERSIFIED":
        ledger = EventDrivenPortfolioLedger(100.0, max_gross_exposure=1.0, max_concurrent_positions=10, max_symbol_weight=0.10, safety_buffer=0.0050)
        for i, s in enumerate(base_prices.keys()):
            side = TradeSide.LONG if i % 2 == 0 else TradeSide.SHORT
            ledger.open_position(s, side, base_prices[s], base_prices[s], 9.8, 10.0, 1.0, 2.0, 1000, 1)
            
    elif config_name == "CFG-07_CORRELATED_ALTCOIN":
        ledger = EventDrivenPortfolioLedger(100.0, max_gross_exposure=1.0, max_concurrent_positions=4, max_symbol_weight=0.25, safety_buffer=0.0050)
        # 4 correlated beta altcoins (SOL, AVAX, LINK, DOGE)
        for s in ["SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT"]:
            ledger.open_position(s, TradeSide.SHORT, base_prices[s], base_prices[s], 24.5, 10.0, 1.0, 2.0, 1000, 1)
            
    elif config_name == "CFG-08_HIGHLY_CONCENTRATED":
        ledger = EventDrivenPortfolioLedger(100.0, max_gross_exposure=1.0, max_symbol_weight=0.80, safety_buffer=0.0050)
        ledger.open_position("ETHUSDT", TradeSide.SHORT, 3000.0, 3000.0, 78.0, 10.0, 1.0, 2.0, 1000, 1)
        
    elif config_name == "CFG-09_PENDING_PLUS_OPEN":
        ledger = EventDrivenPortfolioLedger(100.0, max_gross_exposure=1.0, max_concurrent_positions=4, max_symbol_weight=0.25, safety_buffer=0.0050)
        ledger.open_position("BTCUSDT", TradeSide.LONG, 50000.0, 50000.0, 24.5, 10.0, 1.0, 2.0, 1000, 1)
        ledger.open_position("SOLUSDT", TradeSide.SHORT, 150.0, 150.0, 24.5, 10.0, 1.0, 2.0, 1000, 1)
        ledger.reserve_pending_order("ORD_P1", "ETHUSDT", TradeSide.LONG, 3000.0, 24.5, 1000, 4.0)
        ledger.reserve_pending_order("ORD_P2", "BNBUSDT", TradeSide.SHORT, 400.0, 24.5, 1000, 4.0)
        
    elif config_name == "CFG-10_CLOSE_TO_ADMISSION_CAP":
        ledger = EventDrivenPortfolioLedger(100.0, max_gross_exposure=1.0, max_concurrent_positions=4, max_symbol_weight=0.25, safety_buffer=0.0050)
        for s in ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]:
            ok, r, alloc = ledger.can_open_position(s, 25.0, entry_friction_rate=0.0013)
            ledger.open_position(s, TradeSide.SHORT, base_prices[s], base_prices[s], alloc, 10.0, 1.0, 2.0, 1000, 1)

    return ledger, base_prices


def run_stress_suite():
    records = []
    engine = DeleveragingEngine(target_restored_exposure=0.9500)
    monitor = ActiveMTMMonitor()
    
    for cfg in CONFIG_NAMES:
        for shock in SHOCKS:
            ledger, base_prices = setup_portfolio_config(cfg)
            initial_eq = ledger.equity
            initial_notional = ledger.get_gross_notional()
            initial_exp = ledger.get_gross_exposure()
            
            # Apply price shock
            stressed_prices = {s: p * (1.0 + shock) for s, p in base_prices.items()}
            
            # Update MTM
            eq_post_shock = ledger.update_mark_to_market(stressed_prices, timestamp_ms=2000)
            notional_post_shock = ledger.get_gross_notional(stressed_prices)
            exp_post_shock = ledger.get_gross_exposure(stressed_prices)
            
            # Evaluate Risk State
            rsm = RiskStateMachine()
            snap = monitor.evaluate_portfolio(
                ledger.open_positions, ledger.reserved_pending_notional,
                ledger.cash_balance, stressed_prices, 2000
            )
            state = rsm.update_state(snap)
            
            # Sizing Required Reduction
            req_reduction = engine.compute_excess_notional(notional_post_shock, eq_post_shock, target_exposure=0.9500)
            
            # Execute Deleveraging if in CRITICAL or REDUCE_ONLY
            if state in (RiskState.CRITICAL, RiskState.REDUCE_ONLY) and not ledger.is_ruined:
                actions = engine.execute_deleveraging(
                    ledger, stressed_prices, timestamp_ms=3000,
                    policy=DeleveragingPolicyType.HIGHEST_RISK_FIRST,
                    target_exposure=0.9500,
                )
                actual_reduction = sum(a.executed_reduction_notional for a in actions)
                closing_friction = sum(a.total_friction_usd for a in actions)
            else:
                actual_reduction = 0.0
                closing_friction = 0.0
                
            final_eq = ledger.equity
            final_exp = ledger.get_gross_exposure(stressed_prices)
            
            records.append({
                "scenario_id": f"SCEN-{len(records)+1:03d}",
                "config_name": cfg,
                "price_shock_pct": f"{shock*100.0:+.1f}%",
                "initial_equity_usd": round(initial_eq, 2),
                "initial_notional_usd": round(initial_notional, 2),
                "initial_exposure": f"{initial_exp:.6f}x",
                "post_shock_equity_usd": round(eq_post_shock, 2),
                "post_shock_notional_usd": round(notional_post_shock, 2),
                "post_shock_exposure": f"{exp_post_shock:.6f}x",
                "risk_state": state.value,
                "required_reduction_usd": round(req_reduction, 2),
                "actual_reduction_usd": round(actual_reduction, 2),
                "closing_friction_usd": round(closing_friction, 4),
                "residual_exposure": f"{final_exp:.6f}x",
                "final_equity_usd": round(final_eq, 2),
                "is_ruined": ledger.is_ruined,
            })
            
    df_stress = pd.DataFrame(records)
    stress_csv = OUT_DIR / "M5_12_2_2_LONG_SHORT_STRESS_MATRIX.csv"
    df_stress.to_csv(stress_csv, index=False)
    print(f"Executed {len(df_stress)} stress scenarios. Saved matrix to: {stress_csv}")
    
    # Analyze Long/Short Asymmetry
    df_l = df_stress[df_stress["config_name"] == "CFG-01_SINGLE_LONG"]
    df_s = df_stress[df_stress["config_name"] == "CFG-02_SINGLE_SHORT"]
    print("\n=== LONG vs SHORT ADVERSE SHOCK ASYMMETRY COMPARISON ===")
    comp_rows = []
    for shk in ["-5.0%", "-10.0%", "-20.0%", "-30.0%", "-50.0%"]:
        row_l = df_l[df_l["price_shock_pct"] == shk].iloc[0]
        # For short, adverse shock is positive price rise
        shk_opp = f"+{shk[1:]}"
        row_s = df_s[df_s["price_shock_pct"] == shk_opp].iloc[0]
        comp_rows.append({
            "adverse_shock": shk_opp,
            "long_post_shock_exposure": row_l["post_shock_exposure"],
            "short_post_shock_exposure": row_s["post_shock_exposure"],
            "short_exposure_expansion_pct": round(
                (float(row_s["post_shock_exposure"][:-1]) - float(row_l["post_shock_exposure"][:-1])) / float(row_l["post_shock_exposure"][:-1]) * 100.0, 2
            ),
        })
    df_asym = pd.DataFrame(comp_rows)
    print(df_asym.to_string(index=False))
    
    return df_stress, df_asym

if __name__ == "__main__":
    run_stress_suite()
