"""Milestone 5.9D Trade Frequency & Holding Duration Forensic Audit Script.

Reconstructs all 19 SOL/LTC trade episodes from M5.9B ledger, calculates exact
holding durations (minutes, hours, days), signal generation dynamics, and day-by-day
signal-to-execution reconciliation across all 365 calendar days.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
AUDIT_DIR = ROOT / "audit" / "strategy_research" / "milestone_5_9d_frequency_duration_audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

LEDGER_PATH = ROOT / "audit" / "strategy_research" / "milestone_5_9b_cost_reconciliation" / "M5_9B_TRADE_LEVEL_LEDGER.csv"

def build_trade_holding_duration_csv() -> pd.DataFrame:
    """Extracts all 19 trade episodes and computes detailed durations, prices, execution events, and PnL."""
    df_legs = pd.read_csv(LEDGER_PATH)

    # Group by trade_id
    trade_records = []
    for trade_id, grp in df_legs.groupby("trade_id"):
        sol_row = grp[grp["symbol"] == "SOLUSDT"].iloc[0]
        ltc_row = grp[grp["symbol"] == "LTCUSDT"].iloc[0]

        entry_date = sol_row["entry_date"]
        exit_date = sol_row["exit_date"]
        holding_days = int(sol_row["holding_days"])
        holding_hours = holding_days * 24
        holding_minutes = holding_hours * 60

        entry_ts_ms = int(pd.to_datetime(entry_date, utc=True).timestamp() * 1000)
        exit_ts_ms = int(pd.to_datetime(exit_date, utc=True).timestamp() * 1000)

        gross_pnl = float(grp["gross_pnl_usd"].sum())
        net_pnl = float(grp["net_pnl_usd"].sum())
        exit_reason = sol_row["exit_reason"]

        direction = f"LONG_SOL_SHORT_LTC" if sol_row["direction"] == "LONG" else f"SHORT_SOL_LONG_LTC"

        trade_records.append({
            "trade_id": int(trade_id),
            "pair": "SOLUSDT/LTCUSDT",
            "direction_pair": direction,
            "entry_date": entry_date,
            "exit_date": exit_date,
            "entry_timestamp_ms": entry_ts_ms,
            "exit_timestamp_ms": exit_ts_ms,
            "holding_days": holding_days,
            "holding_hours": holding_hours,
            "holding_minutes": holding_minutes,
            "sol_direction": sol_row["direction"],
            "sol_entry_price": float(sol_row["entry_price"]),
            "sol_exit_price": float(sol_row["exit_price"]),
            "sol_entry_notional_usd": float(sol_row["entry_notional_usd"]),
            "sol_exit_notional_usd": float(sol_row["exit_notional_usd"]),
            "sol_gross_pnl_usd": float(sol_row["gross_pnl_usd"]),
            "sol_net_pnl_usd": float(sol_row["net_pnl_usd"]),
            "ltc_direction": ltc_row["direction"],
            "ltc_entry_price": float(ltc_row["entry_price"]),
            "ltc_exit_price": float(ltc_row["exit_price"]),
            "ltc_entry_notional_usd": float(ltc_row["entry_notional_usd"]),
            "ltc_exit_notional_usd": float(ltc_row["exit_notional_usd"]),
            "ltc_gross_pnl_usd": float(ltc_row["gross_pnl_usd"]),
            "ltc_net_pnl_usd": float(ltc_row["net_pnl_usd"]),
            "individual_execution_events_count": 4,  # SOL entry, LTC entry, SOL exit, LTC exit
            "exit_reason": exit_reason,
            "pair_gross_pnl_usd": round(gross_pnl, 4),
            "pair_net_pnl_usd": round(net_pnl, 4),
        })

    df_out = pd.DataFrame(trade_records)
    df_out.to_csv(AUDIT_DIR / "M5_9D_TRADE_HOLDING_DURATION.csv", index=False)
    return df_out

def build_signal_to_execution_reconciliation() -> pd.DataFrame:
    """Reconciles every calendar day in the evaluation period against signal generation and execution rules."""
    from scripts.revalidate_track_c_statistical_arbitrage import load_daily_close_panel, VAL_START, OOS_END

    df_panel = load_daily_close_panel()
    df_eval = df_panel.loc[VAL_START:OOS_END]

    dep = "SOLUSDT"
    indep = "LTCUSDT"
    b = 1.0077

    p_dep = np.log(df_eval[dep].values)
    p_indep = np.log(df_eval[indep].values)
    spread = p_dep - b * p_indep

    z_scores = []
    window = 30
    for t in range(len(spread)):
        if t < window:
            z_scores.append(0.0)
        else:
            w = spread[t - window : t]
            z = (spread[t] - np.mean(w)) / (np.std(w, ddof=1) + 1e-6)
            z_scores.append(float(z))
    z_scores = np.array(z_scores)

    dates = list(df_eval.index)
    prices_dep = df_eval[dep].values
    prices_indep = df_eval[indep].values

    position = 0  # +1: Long dep / Short indep; -1: Short dep / Long indep; 0: Flat
    trade_id_counter = 0
    active_trade_id = None

    reconciliation_rows = []

    for t in range(len(df_eval)):
        dt = str(dates[t].date())
        ts_ms = int(dates[t].timestamp() * 1000)
        z = z_scores[t]
        pos_before = position

        if t < window:
            reconciliation_rows.append({
                "day_index": t,
                "date": dt,
                "timestamp_ms": ts_ms,
                "sol_close_price": float(prices_dep[t]),
                "ltc_close_price": float(prices_indep[t]),
                "spread_value": float(spread[t]),
                "z_score": float(z),
                "position_state_before": "FLAT",
                "eligible_signal_present": False,
                "signal_type": "NONE",
                "execution_action": "NO_ACTION",
                "active_trade_id": "NONE",
                "exit_reason": "NONE",
                "rejection_or_skip_reason": "WARMUP_WINDOW_30_DAYS",
                "concurrent_open_positions": 0,
            })
            continue

        # Check exit
        exit_action = "NO_ACTION"
        exit_reason = "NONE"
        exited_trade_id = "NONE"

        if position != 0:
            if position == 1 and z >= -0.5:
                exit_action = "EXIT"
                exit_reason = "MEAN_REVERSION_EXIT"
            elif position == -1 and z <= 0.5:
                exit_action = "EXIT"
                exit_reason = "MEAN_REVERSION_EXIT"
            elif abs(z) >= 3.5:
                exit_action = "EXIT"
                exit_reason = "STOP_LOSS_DIVERGENCE"

            if exit_action == "EXIT":
                exited_trade_id = f"TRADE_{active_trade_id:02d}"
                position = 0
                active_trade_id = None

        # Check entry
        entry_action = "NO_ACTION"
        rejection_reason = "NONE"
        is_signal = False
        sig_type = "NONE"

        if abs(z) >= 2.0:
            is_signal = True
            sig_type = "LONG_SOL_SHORT_LTC" if z <= -2.0 else "SHORT_SOL_LONG_LTC"

            if pos_before != 0 and exit_action == "NO_ACTION":
                entry_action = "BLOCKED_ACTIVE_POSITION"
                rejection_reason = "REJECTED_ALREADY_IN_POSITION"
            else:
                entry_action = "ENTERED_NEW_POSITION"
                position = 1 if z <= -2.0 else -1
                trade_id_counter += 1
                active_trade_id = trade_id_counter
                rejection_reason = "EXECUTED_SUCCESSFULLY"
        else:
            rejection_reason = "BELOW_ENTRY_THRESHOLD_2_SIGMA"

        action_summary = "HOLDING_POSITION" if (pos_before != 0 and exit_action == "NO_ACTION" and entry_action == "BLOCKED_ACTIVE_POSITION") else (
            "ENTERED_TRADE" if entry_action == "ENTERED_NEW_POSITION" else (
                "EXITED_TRADE" if exit_action == "EXIT" else (
                    "FLAT_NO_SIGNAL"
                )
            )
        )

        pos_label = "FLAT" if position == 0 else ("LONG_SOL_SHORT_LTC" if position == 1 else "SHORT_SOL_LONG_LTC")

        reconciliation_rows.append({
            "day_index": t,
            "date": dt,
            "timestamp_ms": ts_ms,
            "sol_close_price": float(prices_dep[t]),
            "ltc_close_price": float(prices_indep[t]),
            "spread_value": float(spread[t]),
            "z_score": float(z),
            "position_state_before": "FLAT" if pos_before == 0 else ("LONG_SOL_SHORT_LTC" if pos_before == 1 else "SHORT_SOL_LONG_LTC"),
            "eligible_signal_present": is_signal,
            "signal_type": sig_type,
            "execution_action": action_summary,
            "active_trade_id": f"TRADE_{active_trade_id:02d}" if active_trade_id else "NONE",
            "exit_reason": exit_reason,
            "rejection_or_skip_reason": rejection_reason,
            "concurrent_open_positions": 1 if position != 0 else 0,
        })

    df_rec = pd.DataFrame(reconciliation_rows)
    df_rec.to_csv(AUDIT_DIR / "M5_9D_SIGNAL_TO_EXECUTION_RECONCILIATION.csv", index=False)
    return df_rec

def run():
    print("Executing Milestone 5.9D Trade Frequency & Holding Duration Audit...")
    df_trades = build_trade_holding_duration_csv()
    print(f"Generated M5_9D_TRADE_HOLDING_DURATION.csv with {len(df_trades)} trade episodes.")
    df_rec = build_signal_to_execution_reconciliation()
    print(f"Generated M5_9D_SIGNAL_TO_EXECUTION_RECONCILIATION.csv with {len(df_rec)} calendar day records.")

    durations = df_trades["holding_days"].values
    print("--- Holding Duration Summary ---")
    print(f"Mean holding days:   {np.mean(durations):.2f} days ({np.mean(durations)*24:.1f} hours)")
    print(f"Median holding days: {np.median(durations):.2f} days ({np.median(durations)*24:.1f} hours)")
    print(f"Min holding days:    {np.min(durations):.2f} days")
    print(f"Max holding days:    {np.max(durations):.2f} days")
    print(f"Std holding days:    {np.std(durations, ddof=1):.2f} days")
    print(f"Total days held:     {np.sum(durations)} days")
    print(f"Trades per day:      {len(df_trades)/365.0:.4f}")
    print(f"Trades per week:     {len(df_trades)/(365.0/7.0):.4f}")

    print("--- Signal Reconciliation Summary ---")
    print("Days by Rejection / Execution Reason:")
    print(df_rec["rejection_or_skip_reason"].value_counts())

if __name__ == "__main__":
    run()
