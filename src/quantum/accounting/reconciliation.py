"""Independent Forensic Accounting Reconciliation Engine for M5.11 (Phase A).

DOES NOT import or rely upon the backtest simulator's internal aggregation functions.
Reconstructs fill-level cash flows, dynamic position sizing, exposure caps, and ruin halts.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from quantum.accounting.event_ledger import EventDrivenPortfolioLedger, LedgerEventType
from quantum.domain.enums import TradeSide


@dataclass
class ReconciledPerformanceSummary:
    """Corrected, audit-grade portfolio performance metrics."""
    hypothesis_id: str
    initial_equity_usd: float
    total_notional_usd: float
    gross_pnl_usd: float
    fee_usd: float
    spread_usd: float
    slippage_usd: float
    funding_usd: float
    net_pnl_usd: float
    final_equity_usd: float
    mean_net_daily_return_pct: float
    max_drawdown_pct: float
    profit_factor: float
    completed_trade_count: int
    halted_on_ruin: bool
    ruin_timestamp_ms: Optional[int]


class IndependentForensicReconciler:
    """Independent event-driven accounting engine that audits and reconciles historical strategies."""

    @staticmethod
    def reconcile_trade_stream(
        raw_trades: List[Dict[str, Any]],
        initial_equity_usd: float = 100.0,
        max_concurrent_positions: int = 4,
        max_symbol_weight: float = 0.25,
        total_calendar_days: float = 138.89,
        maker_fee_bps: float = 4.0,
        taker_fee_bps: float = 10.0,
        spread_bps_half: float = 1.0,
        slippage_bps: float = 2.0,
    ) -> Tuple[ReconciledPerformanceSummary, pd.DataFrame]:
        """Reconstructs the exact portfolio equity curve chronologically.
        
        Enforces:
        - Dynamic capital allocation based on CURRENT equity.
        - Strict 1.0000x unlevered exposure cap.
        - Immediate trading halt when equity drops to <= $1.00 (ruin survival).
        - Maximum drawdown mathematically bounded in [0.0%, 100.0%].
        """
        ledger = EventDrivenPortfolioLedger(
            initial_equity_usd=initial_equity_usd,
            max_gross_exposure=1.0000,
            max_concurrent_positions=max_concurrent_positions,
            max_symbol_weight=max_symbol_weight,
            ruin_equity_threshold=1.0,
        )

        # Sort trades strictly by entry_time_ms to ensure point-in-time chronological order
        sorted_trades = sorted(raw_trades, key=lambda t: t.get("entry_time_ms", 0))

        tot_gross_pnl = 0.0
        tot_fees = 0.0
        tot_spread = 0.0
        tot_slippage = 0.0
        tot_funding = 0.0
        tot_notional = 0.0
        completed_trades = 0
        gross_wins = 0.0
        gross_losses = 0.0

        for t in sorted_trades:
            if ledger.is_ruined or ledger.equity <= 1.0:
                # Account is ruined: NO FURTHER TRADES CAN BE PLACED
                break

            sym = t.get("symbol", "BTCUSDT")
            side_str = str(t.get("side", "LONG")).upper()
            side = TradeSide.LONG if "LONG" in side_str else TradeSide.SHORT
            entry_p = float(t.get("entry_price", 100.0))
            exit_p = float(t.get("exit_price", 100.0))
            entry_ts = int(t.get("entry_time_ms", 0))
            exit_ts = int(t.get("exit_time_ms", entry_ts + 1_800_000))
            exit_reason = str(t.get("exit_reason", "TAKE_PROFIT"))

            # Sizing scaled dynamically by current available equity (max 25% of current equity per asset)
            desired_notional = ledger.equity * max_symbol_weight

            pos = ledger.open_position(
                symbol=sym,
                side=side,
                reference_price=entry_p,
                fill_price=entry_p,
                notional=desired_notional,
                fee_bps=taker_fee_bps,
                spread_bps_half=spread_bps_half,
                slippage_bps=slippage_bps,
                timestamp_ms=entry_ts,
                entry_bar=int(t.get("entry_bar", 1)),
                stop_price=float(t.get("stop_price", entry_p * 0.98)),
                target_price=float(t.get("target_price", entry_p * 1.04)),
            )

            if pos is None:
                # Order rejected due to concurrency, exposure cap, or insufficient equity
                continue

            # Accumulate notional
            tot_notional += pos.entry_notional
            entry_fee = pos.entry_notional * (taker_fee_bps / 10_000.0)
            entry_spread = pos.entry_notional * (spread_bps_half / 10_000.0)
            entry_slip = pos.entry_notional * (slippage_bps / 10_000.0)

            # Close position at exit timestamp
            res = ledger.close_position(
                symbol=sym,
                fill_price=exit_p,
                fee_bps=taker_fee_bps,
                spread_bps_half=spread_bps_half,
                slippage_bps=slippage_bps,
                timestamp_ms=exit_ts,
                exit_reason=exit_reason,
            )

            if res is not None:
                gross, net = res
                tot_gross_pnl += gross
                exit_notional = pos.quantity * exit_p
                exit_fee = exit_notional * (taker_fee_bps / 10_000.0)
                exit_spread = exit_notional * (spread_bps_half / 10_000.0)
                exit_slip = exit_notional * (slippage_bps / 10_000.0)

                tot_fees += (entry_fee + exit_fee)
                tot_spread += (entry_spread + exit_spread)
                tot_slippage += (entry_slip + exit_slip)

                completed_trades += 1
                if gross > 0:
                    gross_wins += gross
                else:
                    gross_losses += abs(gross)

        # Final metrics
        final_eq = ledger.equity
        tot_net_pnl = final_eq - initial_equity_usd
        mean_net_daily = (tot_net_pnl / initial_equity_usd) / total_calendar_days * 100.0
        profit_factor = round(gross_wins / gross_losses, 2) if gross_losses > 0 else 0.0

        # Maximum Drawdown calculation from verified event equity curve
        df_events = ledger.to_dataframe()
        equities = df_events["equity"].to_numpy()
        peaks = np.maximum.accumulate(equities)
        dds = (peaks - equities) / np.maximum(peaks, 1e-6) * 100.0
        max_dd = float(np.max(dds)) if len(dds) > 0 else 0.0
        # Bound max drawdown strictly in [0.0, 100.0]%
        max_dd = min(100.0, max(0.0, max_dd))

        summary = ReconciledPerformanceSummary(
            hypothesis_id=raw_trades[0].get("hypothesis_id", "UNKNOWN") if raw_trades else "UNKNOWN",
            initial_equity_usd=initial_equity_usd,
            total_notional_usd=round(tot_notional, 2),
            gross_pnl_usd=round(tot_gross_pnl, 2),
            fee_usd=round(tot_fees, 2),
            spread_usd=round(tot_spread, 2),
            slippage_usd=round(tot_slippage, 2),
            funding_usd=round(tot_funding, 2),
            net_pnl_usd=round(tot_net_pnl, 2),
            final_equity_usd=round(final_eq, 2),
            mean_net_daily_return_pct=round(mean_net_daily, 4),
            max_drawdown_pct=round(max_dd, 2),
            profit_factor=profit_factor,
            completed_trade_count=completed_trades,
            halted_on_ruin=ledger.is_ruined,
            ruin_timestamp_ms=df_events[df_events["event_type"] == LedgerEventType.CAPITAL_EXHAUSTION_HALT.value]["timestamp_ms"].iloc[0] if ledger.is_ruined else None,
        )

        return summary, df_events
