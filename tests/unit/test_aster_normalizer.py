"""Unit tests for AsterDEX Futures payload normalization."""

import pytest

from quantum.domain.enums import ContractStatus, ContractType, Exchange, Timeframe
from quantum.exchanges.aster.normalizer import (
    normalize_aster_instrument,
    normalize_aster_klines,
    normalize_aster_orderbook,
    normalize_aster_ticker,
)


def test_aster_instrument_normalization() -> None:
    """Verify AsterDEX exchangeInfo symbol parsing with filters."""
    raw_symbol = {
        "symbol": "ETHUSDT",
        "status": "TRADING",
        "baseAsset": "ETH",
        "quoteAsset": "USDT",
        "contractType": "PERPETUAL",
        "onboardDate": 1610000000000,
        "maxLeverage": 75.0,
        "filters": [
            {"filterType": "PRICE_FILTER", "tickSize": "0.01", "minPrice": "0.10", "maxPrice": "100000.00"},
            {"filterType": "LOT_SIZE", "stepSize": "0.01", "minQty": "0.01", "maxQty": "500.0"},
            {"filterType": "MIN_NOTIONAL", "notional": "5.0"},
        ],
    }

    norm = normalize_aster_instrument(raw_symbol)
    assert norm is not None
    assert norm.instrument_id == "ASTER:ETHUSDT"
    assert norm.exchange == Exchange.ASTER
    assert norm.symbol == "ETHUSDT"
    assert norm.base_asset == "ETH"
    assert norm.quote_asset == "USDT"
    assert norm.status == ContractStatus.TRADING
    assert norm.contract_type == ContractType.PERPETUAL
    assert norm.tick_size == 0.01
    assert norm.lot_step == 0.01
    assert norm.min_order_qty == 0.01
    assert norm.max_order_qty == 500.0
    assert norm.min_notional_usdt == 5.0
    assert norm.max_leverage == 75.0

    # Non-perpetual or non-USDT must return None
    raw_delivery = dict(raw_symbol, contractType="DELIVERY")
    assert normalize_aster_instrument(raw_delivery) is None

    raw_busd = dict(raw_symbol, quoteAsset="BUSD")
    assert normalize_aster_instrument(raw_busd) is None


def test_aster_ticker_normalization() -> None:
    """Verify AsterDEX 24hr ticker combined with premium index funding payload."""
    raw_24hr = {
        "symbol": "ETHUSDT",
        "lastPrice": "3000.00",
        "bidPrice": "2999.50",
        "bidQty": "10.0",
        "askPrice": "3000.50",
        "askQty": "12.0",
        "volume": "50000.0",
        "quoteVolume": "150000000.0",
        "highPrice": "3100.00",
        "lowPrice": "2950.00",
        "priceChangePercent": "1.75",
    }
    raw_premium = {
        "symbol": "ETHUSDT",
        "markPrice": "3000.25",
        "indexPrice": "3000.10",
        "lastFundingRate": "0.00015",
        "nextFundingTime": 1700028800000,
    }

    ticker = normalize_aster_ticker(raw_24hr, raw_premium)
    assert ticker.instrument_id == "ASTER:ETHUSDT"
    assert ticker.last_price == 3000.0
    assert ticker.mark_price == 3000.25
    assert ticker.index_price == 3000.10
    assert ticker.bid1_price == 2999.50
    assert ticker.ask1_price == 3000.50
    # Spread = 1.0 / 3000.0 * 10000 = 3.33 bps
    assert pytest.approx(ticker.spread_bps, rel=1e-2) == 3.333
    assert ticker.funding_rate == 0.00015
    assert ticker.next_funding_time_ms == 1700028800000


def test_aster_orderbook_normalization() -> None:
    """Verify AsterDEX depth payload parsing."""
    raw = {
        "lastUpdateId": 998877,
        "E": 1700000000555,
        "bids": [["2999.5", "5.0"], ["2999.0", "15.0"]],
        "asks": [["3000.5", "8.0"], ["3001.0", "20.0"]],
    }

    ob = normalize_aster_orderbook(raw, "ETHUSDT")
    assert ob.instrument_id == "ASTER:ETHUSDT"
    assert ob.timestamp_ms == 1700000000555
    assert ob.update_id == 998877
    assert len(ob.bids) == 2
    assert len(ob.asks) == 2
    assert ob.bid1_price == 2999.5
    assert ob.ask1_price == 3000.5
    assert not ob.is_crossed


def test_aster_klines_ascending_sort_enforcement() -> None:
    """Verify AsterDEX klines chronological order enforcement."""
    raw = [
        [1700000000000, "3000.0", "3010.0", "2990.0", "3005.0", "100.0", 1700000059999, "300000.0", 50],
        [1700000060000, "3005.0", "3020.0", "3000.0", "3015.0", "120.0", 1700000119999, "361000.0", 65],
    ]

    candles = normalize_aster_klines(raw, "ETHUSDT", Timeframe.M1)
    assert len(candles) == 2
    assert candles[0].open_time_ms == 1700000000000
    assert candles[1].open_time_ms == 1700000060000
    assert candles[0].trades_count == 50
    assert candles[1].trades_count == 65
