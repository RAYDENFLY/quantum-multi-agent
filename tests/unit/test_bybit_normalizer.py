"""Unit tests for Bybit V5 Linear Perpetuals payload normalization."""

import pytest

from quantum.domain.enums import ContractStatus, ContractType, Exchange, Timeframe
from quantum.exchanges.bybit.normalizer import (
    normalize_bybit_instrument,
    normalize_bybit_klines,
    normalize_bybit_orderbook,
    normalize_bybit_ticker,
)


def test_bybit_instrument_normalization() -> None:
    """Verify linear perpetual instrument metadata parsing."""
    raw_valid = {
        "symbol": "BTCUSDT",
        "baseCoin": "BTC",
        "quoteCoin": "USDT",
        "status": "Trading",
        "contractType": "LinearPerpetual",
        "launchTime": "1600000000000",
        "priceFilter": {"tickSize": "0.10", "minPrice": "0.50", "maxPrice": "999999.00"},
        "lotSizeFilter": {"qtyStep": "0.001", "minOrderQty": "0.001", "maxOrderQty": "100.0", "minNotionalValue": "5.0"},
        "leverageFilter": {"maxLeverage": "50.0"},
    }

    norm = normalize_bybit_instrument(raw_valid)
    assert norm is not None
    assert norm.instrument_id == "BYBIT:BTCUSDT"
    assert norm.exchange == Exchange.BYBIT
    assert norm.symbol == "BTCUSDT"
    assert norm.base_asset == "BTC"
    assert norm.quote_asset == "USDT"
    assert norm.status == ContractStatus.TRADING
    assert norm.contract_type == ContractType.PERPETUAL
    assert norm.tick_size == 0.10
    assert norm.lot_step == 0.001
    assert norm.min_order_qty == 0.001
    assert norm.max_order_qty == 100.0
    assert norm.min_notional_usdt == 5.0
    assert norm.max_leverage == 50.0

    # Non-linear or non-USDT coins must return None
    raw_inverse = dict(raw_valid, contractType="InversePerpetual")
    assert normalize_bybit_instrument(raw_inverse) is None

    raw_usdc = dict(raw_valid, quoteCoin="USDC")
    assert normalize_bybit_instrument(raw_usdc) is None


def test_bybit_ticker_normalization() -> None:
    """Verify Bybit ticker parsing, spread calculation, and funding metrics."""
    raw = {
        "symbol": "BTCUSDT",
        "lastPrice": "50000.00",
        "markPrice": "50005.00",
        "indexPrice": "50002.50",
        "bid1Price": "49998.00",
        "bid1Size": "3.5",
        "ask1Price": "50002.00",
        "ask1Size": "2.1",
        "volume24h": "12500.5",
        "turnover24h": "625000000.0",
        "highPrice24h": "51200.00",
        "lowPrice24h": "49100.00",
        "price24hPcnt": "0.025",
        "openInterest": "25000.0",
        "fundingRate": "0.0001",
        "nextFundingTime": "1700028800000",
    }

    ticker = normalize_bybit_ticker(raw)
    assert ticker.instrument_id == "BYBIT:BTCUSDT"
    assert ticker.last_price == 50000.0
    assert ticker.mark_price == 50005.0
    assert ticker.index_price == 50002.50
    assert ticker.bid1_price == 49998.0
    assert ticker.ask1_price == 50002.0
    # Spread = (50002 - 49998) / 50000 * 10000 = 0.8 bps
    assert pytest.approx(ticker.spread_bps, rel=1e-3) == 0.8
    assert ticker.price_change_24h_pct == 2.5
    assert ticker.open_interest == 25000.0
    assert ticker.funding_rate == 0.0001
    assert ticker.next_funding_time_ms == 1700028800000


def test_bybit_orderbook_normalization() -> None:
    """Verify Bybit orderbook snapshot parsing."""
    raw = {
        "s": "BTCUSDT",
        "ts": 1700000000123,
        "u": 54321,
        "seq": 987654321,
        "b": [["49999.0", "1.5"], ["49998.0", "3.0"]],
        "a": [["50001.0", "2.0"], ["50002.0", "4.0"]],
    }

    ob = normalize_bybit_orderbook(raw, "BTCUSDT")
    assert ob.instrument_id == "BYBIT:BTCUSDT"
    assert ob.timestamp_ms == 1700000000123
    assert ob.update_id == 54321
    assert len(ob.bids) == 2
    assert len(ob.asks) == 2
    assert ob.bid1_price == 49999.0
    assert ob.ask1_price == 50001.0
    assert not ob.is_crossed


def test_bybit_klines_ascending_sort_enforcement() -> None:
    """Verify that Bybit descending klines are sorted ascending by open_time_ms."""
    # Bybit delivers newest first
    descending_raw = [
        ["1700000120000", "50100.0", "50200.0", "50050.0", "50150.0", "5.0", "250000.0"],
        ["1700000060000", "50050.0", "50120.0", "50000.0", "50100.0", "6.0", "300000.0"],
        ["1700000000000", "50000.0", "50080.0", "49950.0", "50050.0", "8.0", "400000.0"],
    ]

    candles = normalize_bybit_klines(descending_raw, "BTCUSDT", Timeframe.M1)
    assert len(candles) == 3

    # Must be sorted ascending
    assert candles[0].open_time_ms == 1700000000000
    assert candles[1].open_time_ms == 1700000060000
    assert candles[2].open_time_ms == 1700000120000

    # Invariants satisfied
    assert candles[0].open_price == 50000.0
    assert candles[0].high_price == 50080.0
    assert candles[0].low_price == 49950.0
    assert candles[0].close_price == 50050.0
    assert candles[0].close_time_ms == 1700000059999
