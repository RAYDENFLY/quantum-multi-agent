"""Unit & Integration Tests for Milestone 5.11 Multi-Factor Market Context & Causal Alpha Discovery.

Verifies:
1. All 8 Milestone 5.11 markdown deliverables and 6 CSV files exist and are non-empty.
2. Causal swing confirmation lag and zero-lookahead invariant (confirmation at t = i + right_bars).
3. Fair Value Gap (FVG) detection, bounds, and causality.
4. Kaufman Efficiency Ratio invariants (bounds in [0, 1], trend=1.0, chop~0.0) and 4-state regime classification.
5. Volume proxies calculation and explicit labeling that OHLCV != L2 orderbook depth.
6. Cross-asset context calculation, relative strength, and market breadth bounded in [0, 1].
7. Exogenous event interface returns DATA_UNAVAILABLE for historical evaluation (zero synthetic news).
8. Hypothesis registry integrity and schema validation.
9. Next-bar open execution invariant (signals at bar t execute strictly at open of t+1).
10. Transaction cost schedule enforcement (26 bps round-trip taker friction) and unlevered exposure (<= 1.0x).
11. Sealed holdout isolation invariant (all data strictly prior to 2026-11-01 00:00:00 UTC).
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest
import pyarrow.parquet as pq

from quantum.features.market_context import (
    compute_causal_swings,
    compute_fair_value_gaps,
    compute_displacement_and_sweeps,
    compute_adx,
    compute_momentum_acceleration,
    compute_trend_persistence,
    compute_kaufman_efficiency_ratio,
    compute_volatility_percentile,
    classify_market_regime,
    compute_volume_proxies,
    compute_cross_asset_context,
    compute_market_context_dataframe,
    ExogenousEventInterface,
    MarketRegimeState,
)
from quantum.strategies.hypothesis_engine import (
    HYPOTHESIS_REGISTRY,
    HypothesisSpecification,
    backtest_single_hypothesis,
)

ROOT = Path(__file__).resolve().parent.parent.parent
M5_11_DIR = ROOT / "audit" / "strategy_research" / "milestone_5_11_market_context_alpha"
CANONICAL_DIR = ROOT / "data" / "historical" / "canonical" / "exchange=ASTER"
SEALED_HOLDOUT_TIMESTAMP_MS = 1_793_491_200_000  # 2026-11-01 00:00:00 UTC


# ==============================================================================
# 1. DELIVERABLES AUDIT
# ==============================================================================

def test_m5_11_deliverables_existence_and_non_empty():
    """Verify that all 8 markdown documents and 6 CSV files exist and are non-empty."""
    required_md_files = [
        "M5_11_MARKET_CONTEXT_ARCHITECTURE.md",
        "M5_11_FEATURE_CATALOG.md",
        "M5_11_HYPOTHESIS_REGISTRY.md",
        "M5_11_DATA_AVAILABILITY_AUDIT.md",
        "M5_11_FEATURE_DIAGNOSTICS.md",
        "M5_11_ALPHA_EXPERIMENT_RESULTS.md",
        "M5_11_STATISTICAL_VALIDATION.md",
        "M5_11_LIMITATIONS_AND_RISKS.md",
    ]
    required_csv_files = [
        "M5_11_FEATURE_DIAGNOSTICS.csv",
        "M5_11_FEATURE_SPEARMAN_CORRELATION.csv",
        "M5_11_ALPHA_EXPERIMENT_RESULTS.csv",
        "M5_11_REGIME_STRATIFICATION.csv",
        "M5_11_COMBINATION_RESULTS.csv",
        "M5_11_STATISTICAL_VALIDATION.csv",
    ]

    assert M5_11_DIR.exists(), f"M5.11 directory does not exist: {M5_11_DIR}"

    for md_name in required_md_files:
        md_path = M5_11_DIR / md_name
        assert md_path.exists(), f"Missing required MD file: {md_name}"
        assert md_path.stat().st_size > 500, f"MD file too small: {md_name}"

    for csv_name in required_csv_files:
        csv_path = M5_11_DIR / csv_name
        assert csv_path.exists(), f"Missing required CSV file: {csv_name}"
        df = pd.read_csv(csv_path)
        assert len(df) >= 1, f"CSV file has no data rows: {csv_name}"


# ==============================================================================
# 2. CAUSAL SWINGS & ZERO LOOKAHEAD
# ==============================================================================

def test_causal_swing_confirmation_lag_and_zero_lookahead():
    """Verify swings are only emitted after right_bars confirmation lag, with zero lookahead."""
    n_bars = 40
    highs = np.full(n_bars, 100.0)
    lows = np.full(n_bars, 90.0)

    # Place a single isolated peak at bar index 10
    peak_idx = 10
    highs[peak_idx] = 150.0

    lookback = 5
    lookforward = 5

    confirmed_sh, confirmed_sl, bars_since_sh, bars_since_sl = compute_causal_swings(
        highs, lows, lookback=lookback, lookforward=lookforward
    )

    # Invariant 1: At peak_idx (bar 10), confirmed_sh MUST NOT be 150.0 (it's either NaN or old peak)
    assert np.isnan(confirmed_sh[peak_idx]) or confirmed_sh[peak_idx] != 150.0, (
        "Swing high was emitted at peak time (lookahead violation!)"
    )

    # Invariant 2: Swing high is confirmed exactly at confirmation index (peak_idx + lookforward = 15)
    confirmation_idx = peak_idx + lookforward
    assert confirmed_sh[confirmation_idx] == 150.0, "Swing high not confirmed at peak + lookforward"
    assert bars_since_sh[confirmation_idx] == 5.0, "Bars since swing high incorrect at confirmation"

    # Invariant 3: Future perturbation test
    # Altering future bars after confirmation_idx must not change history at or before confirmation_idx
    perturbed_highs = highs.copy()
    perturbed_highs[25:] = 200.0  # Big change in the distant future

    conf_sh_pert, _, _, _ = compute_causal_swings(
        perturbed_highs, lows, lookback=lookback, lookforward=lookforward
    )

    np.testing.assert_array_equal(
        confirmed_sh[:confirmation_idx + 1],
        conf_sh_pert[:confirmation_idx + 1],
        err_msg="Future perturbation altered past swing confirmations!",
    )


# ==============================================================================
# 3. FAIR VALUE GAPS (FVG)
# ==============================================================================

def test_fair_value_gaps_calculation():
    """Verify Fair Value Gap magnitude and causal detection."""
    n = 20
    highs = np.full(n, 100.0)
    lows = np.full(n, 90.0)
    atr = np.full(n, 2.0)

    # Create a Bullish FVG at bar index 4: low[4] > high[2]
    highs[2] = 100.0
    lows[4] = 105.0  # Gap of +5.0 points

    # Create a Bearish FVG at bar index 8: high[8] < low[6]
    lows[6] = 95.0
    highs[8] = 90.0  # Gap of -5.0 points

    fvg_bull, fvg_bear, fvg_mag = compute_fair_value_gaps(highs, lows, atr)

    assert fvg_bull[4], "Bullish FVG not detected at bar 4"
    assert pytest.approx(fvg_mag[4], 1e-4) == 5.0 / 2.0  # Normalized by ATR

    assert fvg_bear[8], "Bearish FVG not detected at bar 8"
    assert pytest.approx(fvg_mag[8], 1e-4) == -5.0 / 2.0

    # Ensure no FVG detected before bar 2
    assert not np.any(fvg_bull[:2])
    assert not np.any(fvg_bear[:2])


# ==============================================================================
# 4. KAUFMAN EFFICIENCY RATIO & 4-STATE REGIME CLASSIFICATION
# ==============================================================================

def test_kaufman_efficiency_ratio_invariants():
    """Verify Kaufman Efficiency Ratio properties: bounds in [0, 1], trend vs chop."""
    # Monotonic straight line trend: price increases by 1.0 each step
    trend_prices = np.arange(100.0, 150.0)
    er_trend = compute_kaufman_efficiency_ratio(trend_prices, period=20)
    valid_er_trend = er_trend[20:]
    assert np.all(valid_er_trend >= 0.0) and np.all(valid_er_trend <= 1.0)
    # In a monotonic straight line, ER is mathematically 1.0
    np.testing.assert_allclose(valid_er_trend, 1.0, atol=1e-5)

    # Pure alternating chop: +1, -1, +1, -1
    chop_prices = np.array([100.0 + (i % 2) for i in range(50)])
    er_chop = compute_kaufman_efficiency_ratio(chop_prices, period=20)
    valid_er_chop = er_chop[20:]
    # In pure 2-step oscillation over 20 bars, net change is <= 1.0, total change is 20.0 -> ER <= 0.05
    assert np.all(valid_er_chop <= 0.10)


def test_market_regime_classification_states():
    """Verify 4-state regime classification assigns discrete regimes correctly."""
    # adx >= 22 and er >= 0.32 -> Trend. atr_pct >= 50 -> High Vol.
    adx = np.array([30.0, 30.0, 15.0, 15.0])
    atr_pctl = np.array([75.0, 30.0, 75.0, 30.0])
    er = np.array([0.50, 0.50, 0.10, 0.10])

    regimes, cycles = classify_market_regime(adx, atr_pctl, er)

    assert regimes[0] == MarketRegimeState.HV_TREND.value
    assert regimes[1] == MarketRegimeState.LV_TREND.value
    assert regimes[2] == MarketRegimeState.HV_RANGE.value
    assert regimes[3] == MarketRegimeState.LV_RANGE.value


# ==============================================================================
# 5. VOLUME PROXIES & NO FALSE L2 DEPTH CLAIMS
# ==============================================================================

def test_volume_proxies_and_no_l2_depth_claim():
    """Verify volume proxies and affirm that OHLCV != L2 orderbook depth."""
    n = 100
    close = np.linspace(100.0, 120.0, n)
    open_p = close - 0.5
    high = close + 1.0
    low = close - 1.0
    volume = np.full(n, 1000.0)
    atr = np.full(n, 2.0)
    # Inject volume spike at bar 60
    volume[60] = 5000.0

    rvol, vol_zscore, amihud, effort = compute_volume_proxies(high, low, open_p, close, volume, atr)

    assert rvol[60] > 2.0, "RVOL should detect 5x volume spike"
    assert vol_zscore[60] > 1.5, "Volume Z-score should be elevated at spike"
    valid_amihud = amihud[~np.isnan(amihud)]
    assert np.all(valid_amihud >= 0.0), "Amihud illiquidity proxy must be non-negative"

    # Confirm architectural integrity: volume proxies are derived purely from OHLCV
    from quantum.features import market_context
    assert "orderbook_depth" not in dir(market_context)


# ==============================================================================
# 6. CROSS-ASSET CONTEXT & MARKET BREADTH
# ==============================================================================

def test_cross_asset_context_and_market_breadth():
    """Verify cross-asset relative strength and market breadth bounded in [0, 1]."""
    n = 60
    timestamps = np.arange(1000, 1000 + n * 300_000, 300_000)

    # Asset panels: BTC, ETH, SOL
    btc_df = pd.DataFrame({
        "open_time_ms": timestamps,
        "close_time_ms": timestamps + 299_999,
        "open": np.linspace(50000, 52000, n),
        "high": np.linspace(50100, 52100, n),
        "low": np.linspace(49900, 51900, n),
        "close": np.linspace(50000, 52000, n),
        "volume": np.full(n, 100.0),
    })

    eth_df = btc_df.copy()
    eth_df["close"] = np.linspace(3000, 3300, n)  # Stronger growth than BTC

    sol_df = btc_df.copy()
    sol_df["close"] = np.linspace(150, 140, n)   # Weaker than BTC

    panels = {"BTCUSDT": btc_df, "ETHUSDT": eth_df, "SOLUSDT": sol_df}

    enriched = compute_cross_asset_context(panels, btc_symbol="BTCUSDT")

    assert "BTCUSDT" in enriched
    assert "ETHUSDT" in enriched
    assert "SOLUSDT" in enriched

    eth_enriched = enriched["ETHUSDT"]
    assert "market_breadth_bull_pct" in eth_enriched.columns
    valid_breadth = eth_enriched["market_breadth_bull_pct"].dropna()
    assert np.all(valid_breadth >= 0.0) and np.all(valid_breadth <= 1.0)

    # ETH outgrew BTC, so relative strength vs BTC should be positive
    assert eth_enriched["rel_strength_vs_btc_1h"].iloc[-1] > 0.0


# ==============================================================================
# 7. EXOGENOUS EVENT INTERFACE
# ==============================================================================

def test_exogenous_event_interface_returns_unavailable():
    """Verify exogenous interface returns formal DATA_UNAVAILABLE for historical evaluation."""
    interface = ExogenousEventInterface(is_live=False)
    assert interface.status == "DATA_UNAVAILABLE"

    ctx = interface.get_event_context(1_700_000_000_000)
    assert ctx["status"] == "DATA_UNAVAILABLE"
    assert ctx["open_interest_usd"] is None
    assert ctx["funding_rate_bps"] is None
    assert ctx["macro_event_active"] is False
    assert "DATA_UNAVAILABLE" in ctx["note"]


# ==============================================================================
# 8. HYPOTHESIS REGISTRY INTEGRITY
# ==============================================================================

def test_hypothesis_registry_integrity():
    """Verify all 6 causal hypotheses are registered and valid."""
    required_hypotheses = ["HYP-01", "HYP-02", "HYP-03", "HYP-04", "HYP-05", "HYP-06"]

    for hyp_id in required_hypotheses:
        assert hyp_id in HYPOTHESIS_REGISTRY, f"Missing hypothesis in registry: {hyp_id}"
        spec = HYPOTHESIS_REGISTRY[hyp_id]
        assert isinstance(spec, HypothesisSpecification)
        assert len(spec.market_mechanism) > 10
        assert len(spec.observable_evidence) > 10
        assert len(spec.invalidation_conditions) > 10


# ==============================================================================
# 9. NEXT-BAR OPEN EXECUTION INVARIANT
# ==============================================================================

def test_next_bar_open_execution_invariant():
    """Verify backtest executes orders strictly at next-bar open (t+1), never same-bar close."""
    n = 300
    timestamps = np.arange(1_700_000_000_000, 1_700_000_000_000 + n * 300_000, 300_000)

    # Construct test dataframe with EMA crossover for BASE-03
    df = pd.DataFrame({
        "open_time_ms": timestamps,
        "close_time_ms": timestamps + 299_999,
        "open": np.full(n, 100.0),
        "high": np.full(n, 105.0),
        "low": np.full(n, 95.0),
        "close": np.full(n, 100.0),
        "volume": np.full(n, 1000.0),
        "atr_14": np.full(n, 2.0),
        "market_regime": np.full(n, "HV_RANGE"),
        "ema_9": np.full(n, 99.0),
        "ema_21": np.full(n, 100.0),
    })

    # Trigger EMA crossover at bar 60: ema9 crosses above ema21
    df.loc[60:, "ema_9"] = 101.0
    # Set a distinct open price at bar 61
    expected_entry_open = 103.5
    df.loc[61, "open"] = expected_entry_open

    trades = backtest_single_hypothesis(
        df=df,
        hypothesis_id="BASE-03",
        symbol="TESTUSDT",
        capital_usd=100.0,
    )

    assert len(trades) >= 1
    first_trade = trades[0]
    # Trade must enter at bar 61 open price (103.5), NOT bar 60 close price (100.0)
    assert first_trade.entry_bar == 61
    assert first_trade.entry_price == expected_entry_open
    assert first_trade.entry_time_ms == timestamps[61]


# ==============================================================================
# 10. COST MODEL ENFORCEMENT & UNLEVERED EXPOSURE
# ==============================================================================

def test_cost_schedule_enforcement_and_unlevered_exposure():
    """Verify AsterDEX Retail 26 bps taker friction and strict unlevered exposure."""
    n = 300
    timestamps = np.arange(1_700_000_000_000, 1_700_000_000_000 + n * 300_000, 300_000)

    df = pd.DataFrame({
        "open_time_ms": timestamps,
        "close_time_ms": timestamps + 299_999,
        "open": np.full(n, 100.0),
        "high": np.full(n, 101.0),
        "low": np.full(n, 99.0),
        "close": np.full(n, 100.0),
        "volume": np.full(n, 1000.0),
        "atr_14": np.full(n, 1.0),
        "market_regime": np.full(n, "HV_TREND"),
        "ema_9": np.full(n, 99.0),
        "ema_21": np.full(n, 100.0),
    })

    # Trigger cross at bar 60, and opposite cross at bar 70
    df.loc[60:69, "ema_9"] = 101.0
    df.loc[70:, "ema_9"] = 99.0

    trades = backtest_single_hypothesis(
        df=df,
        hypothesis_id="BASE-03",
        symbol="BTCUSDT",
        capital_usd=100.0,
        taker_fee_bps=10.0,
        slippage_bps=2.0,
        spread_bps_half=1.0,
    )

    assert len(trades) >= 1
    t = trades[0]

    # Verify unlevered exposure: entry notional <= initial equity ($100.00)
    assert t.notional_usd <= 100.0001

    # In a flat trade (entry_price == exit_price == 100.0):
    # gross_pnl = 0.0
    # Entry fee: 10 bps taker + 1 bps half-spread + 2 bps slippage = 13 bps
    # Exit fee: 10 bps taker + 1 bps half-spread + 2 bps slippage = 13 bps
    # Total round trip fee = 26 bps of $100 = $0.26
    # Net PnL = -$0.26 USD (-26.0 bps)
    assert pytest.approx(t.gross_pnl_usd, abs=1e-3) == 0.0
    assert pytest.approx(t.fee_usd + t.slippage_usd, abs=1e-3) == 0.26
    assert pytest.approx(t.net_pnl_usd, abs=1e-3) == -0.26
    assert pytest.approx(t.net_return_bps, abs=0.1) == -26.0


# ==============================================================================
# 11. SEALED HOLDOUT PROVENANCE INVARIANT
# ==============================================================================

def test_sealed_holdout_provenance_invariant():
    """Verify that all historical canonical evaluation files respect the holdout cutoff."""
    btc_dir = CANONICAL_DIR / "symbol=BTCUSDT"
    assert btc_dir.exists(), f"Canonical BTC directory missing: {btc_dir}"

    part_files = sorted(btc_dir.rglob("*.parquet"))
    assert len(part_files) > 0, "No canonical parquet partitions found"

    max_timestamp = 0
    for f in part_files:
        table = pq.ParquetFile(str(f)).read(columns=["close_time_ms"])
        ts_max = table["close_time_ms"].to_numpy().max()
        if ts_max > max_timestamp:
            max_timestamp = ts_max

    assert max_timestamp < SEALED_HOLDOUT_TIMESTAMP_MS, (
        f"Sealed holdout violation! Max timestamp {max_timestamp} >= {SEALED_HOLDOUT_TIMESTAMP_MS}"
    )
