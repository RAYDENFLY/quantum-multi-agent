"""Payload normalization helpers for AsterDEX Futures API."""

import time
from typing import Any, Dict, List, Optional

from quantum.domain.enums import ContractStatus, ContractType, Exchange, Timeframe
from quantum.exchanges.models import (
    InstrumentInfo,
    NormalizedCandle,
    NormalizedOrderBook,
    NormalizedTicker,
    OrderBookLevel,
)

TIMEFRAME_TO_ASTER: Dict[Timeframe, str] = {
    Timeframe.M1: "1m",
    Timeframe.M5: "5m",
    Timeframe.M15: "15m",
    Timeframe.H1: "1h",
    Timeframe.H4: "4h",
    Timeframe.D1: "1d",
}

ASTER_TO_TIMEFRAME: Dict[str, Timeframe] = {v: k for k, v in TIMEFRAME_TO_ASTER.items()}


def normalize_aster_instrument(raw: Dict[str, Any]) -> Optional[InstrumentInfo]:
    """Parse AsterDEX futures symbol metadata from exchangeInfo."""
    symbol = raw.get("symbol", "")
    quote_asset = raw.get("quoteAsset", "")
    contract_type_str = raw.get("contractType", "PERPETUAL")

    if quote_asset != "USDT" or contract_type_str != "PERPETUAL":
        return None

    status_str = raw.get("status", "TRADING")
    status = ContractStatus.TRADING if status_str == "TRADING" else ContractStatus.CLOSED

    # Parse filters
    tick_size = 0.01
    lot_step = 0.001
    min_order_qty = 0.001
    max_order_qty = 1000.0
    min_notional = 5.0

    for f in raw.get("filters", []):
        f_type = f.get("filterType")
        if f_type == "PRICE_FILTER":
            tick_size = float(f.get("tickSize", 0.01))
        elif f_type == "LOT_SIZE":
            lot_step = float(f.get("stepSize", 0.001))
            min_order_qty = float(f.get("minQty", 0.001))
            max_order_qty = float(f.get("maxQty", 1000.0))
        elif f_type == "MIN_NOTIONAL":
            min_notional = float(f.get("notional", 5.0))

    now_ms = int(time.time() * 1000)
    onboard_ms = int(raw.get("onboardDate", 0))

    return InstrumentInfo(
        instrument_id=f"ASTER:{symbol}",
        exchange=Exchange.ASTER,
        symbol=symbol,
        base_asset=raw.get("baseAsset", ""),
        quote_asset="USDT",
        status=status,
        contract_type=ContractType.PERPETUAL,
        tick_size=tick_size,
        lot_step=lot_step,
        min_order_qty=min_order_qty,
        max_order_qty=max_order_qty,
        min_notional_usdt=min_notional,
        max_leverage=float(raw.get("maxLeverage", 50.0)),
        maker_fee_rate=0.0002,
        taker_fee_rate=0.00055,
        onboard_timestamp_ms=onboard_ms,
        updated_at_ms=now_ms,
    )


def normalize_aster_ticker(raw_24hr: Dict[str, Any], raw_premium: Optional[Dict[str, Any]] = None) -> NormalizedTicker:
    """Parse AsterDEX 24hr ticker and optional premium index payloads."""
    symbol = raw_24hr.get("symbol", "")
    last_price = float(raw_24hr.get("lastPrice", 0.0))

    mark_price = last_price
    index_price = last_price
    funding_rate = None
    next_funding_time = None

    if raw_premium:
        mark_price = float(raw_premium.get("markPrice", last_price or 1.0))
        index_price = float(raw_premium.get("indexPrice", mark_price))
        funding_rate = float(raw_premium["lastFundingRate"]) if raw_premium.get("lastFundingRate") is not None else None
        next_funding_time = int(raw_premium["nextFundingTime"]) if raw_premium.get("nextFundingTime") is not None else None

    bid1_price = float(raw_24hr.get("bidPrice", 0.0))
    bid1_size = float(raw_24hr.get("bidQty", 0.0))
    ask1_price = float(raw_24hr.get("askPrice", 0.0))
    ask1_size = float(raw_24hr.get("askQty", 0.0))

    volume_24h = float(raw_24hr.get("volume", 0.0))
    turnover_24h = float(raw_24hr.get("quoteVolume", 0.0))

    high_24h = float(raw_24hr["highPrice"]) if raw_24hr.get("highPrice") else None
    low_24h = float(raw_24hr["lowPrice"]) if raw_24hr.get("lowPrice") else None
    price_change_pct = float(raw_24hr["priceChangePercent"]) if raw_24hr.get("priceChangePercent") else None

    now_ms = int(time.time() * 1000)

    return NormalizedTicker(
        instrument_id=f"ASTER:{symbol}",
        exchange=Exchange.ASTER,
        symbol=symbol,
        timestamp_ms=now_ms,
        last_price=last_price,
        mark_price=mark_price,
        index_price=index_price,
        bid1_price=bid1_price,
        bid1_size=bid1_size,
        ask1_price=ask1_price,
        ask1_size=ask1_size,
        volume_24h=volume_24h,
        turnover_24h_usdt=turnover_24h,
        high_price_24h=high_24h,
        low_price_24h=low_24h,
        price_change_24h_pct=price_change_pct,
        funding_rate=funding_rate,
        next_funding_time_ms=next_funding_time,
    )


def normalize_aster_orderbook(raw: Dict[str, Any], symbol: str) -> NormalizedOrderBook:
    """Parse AsterDEX orderbook depth payload."""
    timestamp_ms = int(raw.get("E", time.time() * 1000))
    update_id = int(raw.get("lastUpdateId", 0))

    bids: List[OrderBookLevel] = []
    for item in raw.get("bids", []):
        p, s = float(item[0]), float(item[1])
        if p > 0.0 and s > 0.0:
            bids.append(OrderBookLevel(price=p, size=s))

    asks: List[OrderBookLevel] = []
    for item in raw.get("asks", []):
        p, s = float(item[0]), float(item[1])
        if p > 0.0 and s > 0.0:
            asks.append(OrderBookLevel(price=p, size=s))

    return NormalizedOrderBook(
        instrument_id=f"ASTER:{symbol}",
        exchange=Exchange.ASTER,
        symbol=symbol,
        timestamp_ms=timestamp_ms,
        update_id=update_id,
        bids=bids,
        asks=asks,
    )


def normalize_aster_klines(
    raw_list: List[List[Any]],
    symbol: str,
    timeframe: Timeframe,
) -> List[NormalizedCandle]:
    """Parse AsterDEX klines list and sort ascending by open_time_ms.

    AsterDEX returns oldest first (ascending). We explicitly verify sorting
    to guarantee strictly chronological order.
    """
    candles: List[NormalizedCandle] = []
    for bar in raw_list:
        open_time = int(bar[0])
        open_p = float(bar[1])
        high_p = float(bar[2])
        low_p = float(bar[3])
        close_p = float(bar[4])
        vol = float(bar[5])
        close_time = int(bar[6])
        turnover = float(bar[7])
        trades = int(bar[8]) if len(bar) > 8 else 0

        candle = NormalizedCandle(
            instrument_id=f"ASTER:{symbol}",
            exchange=Exchange.ASTER,
            symbol=symbol,
            timeframe=timeframe,
            open_time_ms=open_time,
            close_time_ms=close_time,
            open_price=open_p,
            high_price=high_p,
            low_price=low_p,
            close_price=close_p,
            volume=vol,
            turnover_usdt=turnover,
            trades_count=trades,
            is_closed=True,
        )
        candles.append(candle)

    # Sort ascending by open_time_ms
    candles.sort(key=lambda c: c.open_time_ms)
    return candles
