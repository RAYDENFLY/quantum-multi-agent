"""Unit tests for market data contracts and mathematical invariants."""

import pytest
from pydantic import ValidationError

from quantum.domain.enums import ConnectionState, ContractStatus, ContractType, Exchange, Timeframe
from quantum.exchanges.models import (
    ExchangeHealthStatus,
    InstrumentInfo,
    NormalizedCandle,
    NormalizedOrderBook,
    NormalizedTicker,
    OrderBookLevel,
)


def test_orderbook_level_validation() -> None:
    """Verify price and size constraints on order book levels."""
    level = OrderBookLevel(price=50000.0, size=1.5)
    assert level.price == 50000.0
    assert level.size == 1.5

    # Price must be strictly positive
    with pytest.raises(ValidationError):
        OrderBookLevel(price=0.0, size=1.0)
    with pytest.raises(ValidationError):
        OrderBookLevel(price=-10.0, size=1.0)

    # Size cannot be negative
    with pytest.raises(ValidationError):
        OrderBookLevel(price=100.0, size=-0.5)


def test_normalized_orderbook_metrics_and_top_n() -> None:
    """Verify spread calculation, uncrossed condition, and truncation."""
    bids = [
        OrderBookLevel(price=49999.0, size=2.0),
        OrderBookLevel(price=49998.0, size=1.0),
    ]
    asks = [
        OrderBookLevel(price=50001.0, size=1.5),
        OrderBookLevel(price=50002.0, size=3.0),
    ]

    ob = NormalizedOrderBook(
        instrument_id="BYBIT:BTCUSDT",
        exchange=Exchange.BYBIT,
        symbol="BTCUSDT",
        timestamp_ms=1700000000000,
        update_id=100,
        bids=bids,
        asks=asks,
    )

    assert ob.bid1_price == 49999.0
    assert ob.bid1_size == 2.0
    assert ob.ask1_price == 50001.0
    assert ob.ask1_size == 1.5
    assert ob.mid_price == 50000.0
    assert not ob.is_crossed
    # Spread bps = (50001 - 49999) / 50000 * 10000 = 2 / 50000 * 10000 = 0.4 bps
    assert pytest.approx(ob.spread_bps, rel=1e-3) == 0.4

    # Top-N truncation
    truncated = ob.top_n(depth=1)
    assert len(truncated.bids) == 1
    assert len(truncated.asks) == 1
    assert truncated.bids[0].price == 49999.0


def test_normalized_orderbook_crossed_detection() -> None:
    """Verify crossed book flag is set when bid1 >= ask1."""
    crossed_ob = NormalizedOrderBook(
        instrument_id="BYBIT:BTCUSDT",
        exchange=Exchange.BYBIT,
        symbol="BTCUSDT",
        timestamp_ms=1700000000000,
        update_id=101,
        bids=[OrderBookLevel(price=50002.0, size=1.0)],
        asks=[OrderBookLevel(price=50001.0, size=1.0)],
    )
    assert crossed_ob.is_crossed is True
    assert crossed_ob.bid1_price == 50002.0
    assert crossed_ob.ask1_price == 50001.0


def test_normalized_ticker_spread_calculation() -> None:
    """Verify ticker spread calculation and field preservation."""
    ticker = NormalizedTicker(
        instrument_id="ASTER:BTCUSDT",
        exchange=Exchange.ASTER,
        symbol="BTCUSDT",
        timestamp_ms=1700000000000,
        last_price=50000.0,
        mark_price=50002.0,
        index_price=50001.0,
        bid1_price=49995.0,
        bid1_size=2.0,
        ask1_price=50005.0,
        ask1_size=3.0,
        volume_24h=1200.0,
        turnover_24h_usdt=60_000_000.0,
        funding_rate=0.0001,
        next_funding_time_ms=1700028800000,
    )
    assert ticker.instrument_id == "ASTER:BTCUSDT"
    # Mid = 50000. Spread = 10 / 50000 * 10000 = 2.0 bps
    assert pytest.approx(ticker.spread_bps, rel=1e-3) == 2.0
    assert ticker.funding_rate == 0.0001


def test_normalized_candle_invariants() -> None:
    """Verify OHLC mathematical invariants: high >= max(open, close), low <= min(open, close)."""
    valid_candle = NormalizedCandle(
        instrument_id="BYBIT:BTCUSDT",
        exchange=Exchange.BYBIT,
        symbol="BTCUSDT",
        timeframe=Timeframe.M1,
        open_time_ms=1700000000000,
        close_time_ms=1700000059999,
        open_price=50000.0,
        high_price=50100.0,
        low_price=49900.0,
        close_price=50050.0,
        volume=10.5,
        turnover_usdt=525000.0,
        trades_count=150,
        is_closed=True,
    )
    assert valid_candle.high_price == 50100.0

    # Invariant violation: high lower than open
    with pytest.raises(ValidationError):
        NormalizedCandle(
            instrument_id="BYBIT:BTCUSDT",
            exchange=Exchange.BYBIT,
            symbol="BTCUSDT",
            timeframe=Timeframe.M1,
            open_time_ms=1700000000000,
            close_time_ms=1700000059999,
            open_price=50000.0,
            high_price=49950.0,  # Invalid: below open
            low_price=49900.0,
            close_price=49920.0,
            volume=1.0,
            turnover_usdt=50000.0,
        )

    # Invariant violation: low higher than close
    with pytest.raises(ValidationError):
        NormalizedCandle(
            instrument_id="BYBIT:BTCUSDT",
            exchange=Exchange.BYBIT,
            symbol="BTCUSDT",
            timeframe=Timeframe.M1,
            open_time_ms=1700000000000,
            close_time_ms=1700000059999,
            open_price=50000.0,
            high_price=50100.0,
            low_price=50020.0,  # Invalid: above open
            close_price=50050.0,
            volume=1.0,
            turnover_usdt=50000.0,
        )

    # Invariant violation: close time <= open time
    with pytest.raises(ValidationError):
        NormalizedCandle(
            instrument_id="BYBIT:BTCUSDT",
            exchange=Exchange.BYBIT,
            symbol="BTCUSDT",
            timeframe=Timeframe.M1,
            open_time_ms=1700000000000,
            close_time_ms=1700000000000,  # Invalid: equal to open
            open_price=50000.0,
            high_price=50100.0,
            low_price=49900.0,
            close_price=50050.0,
            volume=1.0,
            turnover_usdt=50000.0,
        )


def test_instrument_info_and_health_models() -> None:
    """Verify instrument info and exchange health contract instantiation."""
    inst = InstrumentInfo(
        instrument_id="BYBIT:BTCUSDT",
        exchange=Exchange.BYBIT,
        symbol="BTCUSDT",
        base_asset="BTC",
        quote_asset="USDT",
        status=ContractStatus.TRADING,
        contract_type=ContractType.PERPETUAL,
        tick_size=0.1,
        lot_step=0.001,
        min_order_qty=0.001,
        max_order_qty=100.0,
        min_notional_usdt=5.0,
        max_leverage=50.0,
    )
    assert inst.instrument_id == "BYBIT:BTCUSDT"
    assert inst.status == ContractStatus.TRADING

    health = ExchangeHealthStatus(
        exchange=Exchange.BYBIT,
        state=ConnectionState.CONNECTED,
        rest_latency_ms=25.4,
        ws_latency_ms=12.1,
    )
    assert health.exchange == Exchange.BYBIT
    assert health.state == ConnectionState.CONNECTED
    assert health.rest_latency_ms == 25.4
