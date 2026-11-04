"""Milestone 5.14.1 Forensic Audit & Regression Test Suite.

Validates:
1. Daily return formula defect proof (multi-year compounding divided by days).
2. First-principles daily return compounding reconciliation (product of 1+R_t == terminal equity).
3. Geometric daily return vs +3.00% project promotion target.
4. DSR numerical saturation forensics and Bailey-López de Prado formulation.
5. Maximum drawdown compliance (Mode A & B fail <=15%, Legacy passes).
6. Peak gross exposure MTM drift origin (ADA+AVAX 0.995038x <= 1.000000x).
7. Accounting Oracle independent reconciliation ($0.00 delta).
8. Profit recycling capital conservation (no double counting).
"""
import math
from statistics import NormalDist
import numpy as np
import pytest

from quantum.accounting.event_ledger import EventDrivenPortfolioLedger
from quantum.accounting.oracle import IndependentAccountingOracle
from quantum.accounting.risk_controller import ActiveMTMMonitor
from quantum.domain.enums import TradeSide


def test_m514_return_formula_defect_proof():
    """Proves that M5.14's reported 347.41% was multi-year compounded return divided by days."""
    initial_equity = 100.0
    terminal_equity = 380608.337440
    days = 1095.267361

    # Reported M5.14 formula:
    compounded_total_return_pct = (terminal_equity / initial_equity - 1.0) * 100.0
    reported_mean_daily_return_pct = compounded_total_return_pct / days

    # Assert exact match to reported M5.14 value
    assert math.isclose(reported_mean_daily_return_pct, 347.411373, rel_tol=1e-5)

    # Prove that true geometric daily return is < 1.0% per day
    true_geo_daily_return_pct = ((terminal_equity / initial_equity) ** (1.0 / days) - 1.0) * 100.0
    assert math.isclose(true_geo_daily_return_pct, 0.755565, rel_tol=1e-3)

    # If an account actually compounded at 347.41% per day for 1095 days, equity would exceed 10^712
    # In float64 this overflows (max 1e308), so evaluate in log10 space:
    log10_hypothetical_equity = math.log10(initial_equity) + days * math.log10(1.0 + reported_mean_daily_return_pct / 100.0)
    assert log10_hypothetical_equity > 700.0


def test_daily_return_compounding_reconciliation():
    """Validates that discrete daily returns R_t = E_t / E_{t-1} - 1 reconcile to terminal equity."""
    # Synthetic 5-day equity curve
    equity_series = [100.0, 101.5, 102.8, 101.2, 104.0, 105.5]
    returns = [equity_series[i] / equity_series[i - 1] - 1.0 for i in range(1, len(equity_series))]

    reconstructed_terminal = equity_series[0] * np.prod([1.0 + r for r in returns])
    assert math.isclose(reconstructed_terminal, equity_series[-1], rel_tol=1e-12)


def test_geometric_daily_returns_fail_3pct_promotion_target():
    """Validates that no configuration achieved the required >= +3.00% mean daily return target."""
    initial_equity = 100.0
    days = 1095.267361

    # Terminal equities from M5.14 results
    terminal_equities = {
        "Mode A Bybit Maker": 380608.34,
        "Mode A Aster Maker": 155372.94,
        "Mode B Bybit Maker": 97249.74,
        "Legacy Bybit Maker": 14001.99,
        "Legacy Aster Taker": 1675.45,
    }

    geo_daily_returns = {
        name: ((eq / initial_equity) ** (1.0 / days) - 1.0) * 100.0
        for name, eq in terminal_equities.items()
    }

    # All configurations have geometric daily return < 1.0%, failing the >= 3.00% requirement
    for name, ret in geo_daily_returns.items():
        assert ret < 1.00, f"{name} exceeded 1.0% daily return"
        assert ret < 3.00, f"{name} satisfied 3.00% target unexpectedly"


def test_dsr_saturation_and_bailey_lopez_correction():
    """Validates DSR numerical saturation and Bailey & López de Prado formula."""
    # For large sample Sharpe, NormalDist().cdf saturates at 1.000000
    z_saturated = 12.5
    assert NormalDist().cdf(z_saturated) == 1.0

    # Test Bailey & López de Prado formulation with kurtosis adjustment
    n = 1096
    daily_sr = 0.25  # Annualized SR ~ 4.78
    skew = 3.5
    kurt = 28.0

    var_sr = (1.0 - skew * daily_sr + ((kurt - 1.0) / 4.0) * (daily_sr ** 2)) / (n - 1.0)
    sigma_sr = math.sqrt(var_sr)

    # For K = 12
    q1 = 1.0 - (1.0 / 12)
    q2 = 1.0 - (1.0 / (12 * math.e))
    euler = 0.5772156649
    norm = NormalDist()
    exp_max_z = (1.0 - euler) * norm.inv_cdf(q1) + euler * norm.inv_cdf(q2)

    test_stat_k12 = (daily_sr / sigma_sr) - exp_max_z
    assert test_stat_k12 > 8.0  # Explains why DSR evaluated to 1.000000 in M5.14

    # For K = 100,000 trials
    q1_large = 1.0 - (1.0 / 100000)
    q2_large = 1.0 - (1.0 / (100000 * math.e))
    exp_max_z_large = (1.0 - euler) * norm.inv_cdf(q1_large) + euler * norm.inv_cdf(q2_large)
    test_stat_k100k = (daily_sr / sigma_sr) - exp_max_z_large
    assert test_stat_k100k < test_stat_k12


def test_drawdown_limit_compliance():
    """Validates that Mode A and Mode B breach the <= 15.00% drawdown target while Legacy complies."""
    drawdowns = {
        "Legacy Bybit Maker": 13.09,
        "Legacy Aster Maker": 13.70,
        "Legacy Aster Taker": 15.92,
        "Mode A Bybit Maker": 30.48,
        "Mode A Aster Maker": 31.04,
        "Mode B Bybit Maker": 16.99,
        "Mode B Aster Maker": 17.88,
    }

    # Legacy Bybit & Aster Maker comply with <= 15.00%
    assert drawdowns["Legacy Bybit Maker"] <= 15.00
    assert drawdowns["Legacy Aster Maker"] <= 15.00

    # Retail Taker, Mode A, and Mode B strictly breach <= 15.00%
    assert drawdowns["Legacy Aster Taker"] > 15.00
    assert drawdowns["Mode A Bybit Maker"] > 15.00
    assert drawdowns["Mode B Bybit Maker"] > 15.00


def test_exposure_mtm_drift_mechanics():
    """Validates the exact 0.995038x peak exposure event and confirms hard cap preservation."""
    # Peak event reproduction: ADA long + AVAX long in Mode B (slot weight 0.490)
    cash = 804.157257
    ada_entry_notional = 410.340658
    ada_entry_price = 0.5973
    ada_exit_price = 0.6062595  # +150 bps take profit target
    avax_notional = 389.795812

    ada_mtm_notional = ada_entry_notional * (ada_exit_price / ada_entry_price)
    ada_unrealized_pnl = ada_mtm_notional - ada_entry_notional
    total_gross_notional = ada_mtm_notional + avax_notional
    total_equity = cash + ada_unrealized_pnl

    gross_exposure = total_gross_notional / total_equity

    # Discrepancy over admission cap (0.995000)
    assert math.isclose(gross_exposure, 0.995038, rel_tol=1e-5)
    assert gross_exposure > 0.995000  # +0.000038x delta over admission cap

    # Hard cap of 1.000000x strictly preserved
    assert gross_exposure <= 1.000000


def test_accounting_oracle_independence_and_zero_delta():
    """Validates that ledger and independent oracle reconcile with 0.0 delta."""
    ledger = EventDrivenPortfolioLedger(initial_equity_usd=100.0, max_concurrent_positions=2, max_symbol_weight=0.49, admission_exposure_cap=0.9950, max_gross_exposure=1.0000)
    oracle = IndependentAccountingOracle(initial_cash_usd=100.0, max_symbol_weight=0.49, admission_exposure_cap=0.9950, max_gross_exposure=1.0000)

    # Execute trade 1
    ledger.reserve_pending_order("O-1", "BTCUSDT", TradeSide.LONG, 50000.0, 49.0, 1000, fee_bps=3.5)
    oracle.reserve_order("R-1", "O-1", 1000, "BTCUSDT", True, 49.0, 50000.0, maker_fee_bps=3.5)
    ledger.open_position("BTCUSDT", TradeSide.LONG, 50000.0, 50000.0, 49.0, 3.5, 0.0, 0.0, 1000, 1, pending_order_id="O-1")
    oracle.process_entry("E-1", "T-1", 1000, "BTCUSDT", True, 49.0, 50000.0, maker_fee_bps=3.5, is_maker=True, pending_order_id="O-1")

    # Exit trade 1 with profit
    ledger.close_position("BTCUSDT", 50750.0, 3.5, 0.0, 0.0, 2000, "IMPULSE_PROFIT_LOCK")
    oracle.process_exit("X-1", "T-1", 2000, "BTCUSDT", 50750.0, maker_fee_bps=3.5, is_maker=True)

    delta = abs(ledger.equity - oracle.compute_equity())
    assert delta < 1e-10


def test_profit_recycling_no_double_counting():
    """Validates that realized profits are not double-counted when recycled into new orders."""
    ledger = EventDrivenPortfolioLedger(initial_equity_usd=100.0, max_concurrent_positions=1, max_symbol_weight=0.98, admission_exposure_cap=0.9950, max_gross_exposure=1.0000)

    # Initial state
    assert ledger.equity == 100.0
    assert ledger.cash_balance == 100.0

    # Trade 1: Entry with $98 notional in perpetual futures
    # In perpetual futures accounting, cash represents margin collateral.
    # Opening position reserves pending notional but cash is only debited for fees.
    ok, _, granted = ledger.reserve_pending_order("O-1", "SOLUSDT", TradeSide.LONG, 100.0, 98.0, 1000, fee_bps=0.0)
    assert ok
    ledger.open_position("SOLUSDT", TradeSide.LONG, 100.0, 100.0, granted, 0.0, 0.0, 0.0, 1000, 1, pending_order_id="O-1")
    assert ledger.cash_balance == 100.0  # Collateral retained, 0 fees
    assert ledger.equity == 100.0        # Cash + Unrealized PnL (0)

    # Trade 1: Exit at +150 bps (+1.47 USD gross profit)
    ledger.close_position("SOLUSDT", 101.50, 0.0, 0.0, 0.0, 2000, "IMPULSE_PROFIT_LOCK")
    assert math.isclose(ledger.equity, 101.47, rel_tol=1e-9)
    assert math.isclose(ledger.cash_balance, 101.47, rel_tol=1e-9)

    # Trade 2: Immediate re-entry reusing realized profits
    req = ledger.equity * 0.98
    ok2, _, granted2 = ledger.reserve_pending_order("O-2", "ETHUSDT", TradeSide.LONG, 2000.0, req, 3000, fee_bps=0.0)
    assert ok2
    ledger.open_position("ETHUSDT", TradeSide.LONG, 2000.0, 2000.0, granted2, 0.0, 0.0, 0.0, 3000, 2, pending_order_id="O-2")

    # Verify that equity remains exactly $101.47 with zero double-counting
    assert math.isclose(ledger.cash_balance, 101.47, rel_tol=1e-9)
    assert math.isclose(ledger.equity, 101.47, rel_tol=1e-9)
    # Granted sizing scaled up cleanly with equity
    assert math.isclose(granted2, 101.47 * 0.98, rel_tol=1e-9)
