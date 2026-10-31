"""Payload normalization helpers for Bybit V5 Linear Perpetuals."""

import time
from typing import Any, Dict, List, Optional, Tuple

from quantum.domain.enums import ContractStatus, ContractType, Exchange, Timeframe
from quantum.exchanges.models import (
    InstrumentInfo,
    NormalizedCandle,
    NormalizedOrderBook,
    NormalizedTicker,
    OrderBookLevel,
)

TIMEFRAME_TO_BYBIT: Dict[Timeframe, str] = {
    Timeframe.M1: "1",
    Timeframe.M5: "5",
    Timeframe.M15: "15",
    Timeframe.H1: "60",
    Timeframe.H4: "240",
    Timeframe.D1: "D",
}

BYBIT_TO_TIMEFRAME: Dict[str, Timeframe] = {v: k for k, v in TIMEFRAME_TO_BYBIT.items()}


def normalize_bybit_instrument(raw: Dict[str, Any]) -> Optional[InstrumentInfo]:
    """Parse Bybit V5 linear perpetual instrument definition."""
    symbol = raw.get("symbol", "")
    quote_coin = raw.get("quoteCoin", "")
    contract_type = raw.get("contractType", "")

    # Restrict to USDT linear perpetuals
    if quote_coin != "USDT" or contract_type != "LinearPerpetual":
        return None

    status_str = raw.get("status", "Trading")
    status = ContractStatus.TRADING if status_str == "Trading" else ContractStatus.CLOSED

    price_filter = raw.get("priceFilter", {})
    lot_size_filter = raw.get("lotSizeFilter", {})
    leverage_filter = raw.get("leverageFilter", {})

    tick_size = float(price_filter.get("tickSize", 0.01))
    lot_step = float(lot_size_filter.get("qtyStep", 0.001))
    min_order_qty = float(lot_size_filter.get("minOrderQty", 0.001))
    max_order_qty = float(lot_size_filter.get("maxOrderQty", 1000.0))
    min_notional = float(lot_size_filter.get("minNotionalValue", 5.0))
    max_leverage = float(leverage_filter.get("maxLeverage", 50.0))

    now_ms = int(time.time() * 1000)
    launch_time_ms = int(raw.get("launchTime", 0))

    return InstrumentInfo(
        instrument_id=f"BYBIT:{symbol}",
        exchange=Exchange.BYBIT,
        symbol=symbol,
        base_asset=raw.get("baseCoin", ""),
        quote_asset="USDT",
        status=status,
        contract_type=ContractType.PERPETUAL,
        tick_size=tick_size,
        lot_step=lot_step,
        min_order_qty=min_order_qty,
        max_order_qty=max_order_qty,
        min_notional_usdt=min_notional,
        max_leverage=max_leverage,
        maker_fee_rate=0.0002,
        taker_fee_rate=0.00055,
        onboard_timestamp_ms=launch_time_ms,
        updated_at_ms=now_ms,
    )


def normalize_bybit_ticker(raw: Dict[str, Any]) -> NormalizedTicker:
    """Parse Bybit V5 linear ticker payload."""
    symbol = raw.get("symbol", "")
    last_price = float(raw.get("lastPrice", 0.0))
    mark_price = float(raw.get("markPrice", last_price or 1.0))
    index_price = float(raw.get("indexPrice", mark_price))

    bid1_price = float(raw.get("bid1Price", 0.0))
    bid1_size = float(raw.get("bid1Size", 0.0))
    ask1_price = float(raw.get("ask1Price", 0.0))
    ask1_size = float(raw.get("ask1Size", 0.0))

    volume_24h = float(raw.get("volume24h", 0.0))
    turnover_24h = float(raw.get("turnover24h", 0.0))

    high_24h = float(raw["highPrice24h"]) if raw.get("highPrice24h") else None
    low_24h = float(raw["lowPrice24h"]) if raw.get("lowPrice24h") else None
    price_change_pct = float(raw["price24hPcnt"]) * 100.0 if raw.get("price24hPcnt") else None

    open_interest = float(raw["openInterest"]) if raw.get("openInterest") else None
    funding_rate = float(raw["fundingRate"]) if raw.get("fundingRate") else None
    next_funding_time = int(raw["nextFundingTime"]) if raw.get("nextFundingTime") else None

    now_ms = int(time.time() * 1000)

    return NormalizedTicker(
        instrument_id=f"BYBIT:{symbol}",
        exchange=Exchange.BYBIT,
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
        open_interest=open_interest,
        funding_rate=funding_rate,
        next_funding_time_ms=next_funding_time,
    )


def normalize_bybit_orderbook(raw: Dict[str, Any], symbol: str) -> NormalizedOrderBook:
    """Parse Bybit V5 orderbook snapshot payload."""
    timestamp_ms = int(raw.get("ts", time.time() * 1000))
    update_id = int(raw.get("u", 0))

    bids: List[OrderBookLevel] = []
    for item in raw.get("b", []):
        p, s = float(item[0]), float(item[1])
        if p > 0.0 and s > 0.0:
            bids.append(OrderBookLevel(price=p, size=s))

    asks: List[OrderBookLevel] = []
    for item in raw.get("a", []):
        p, s = float(item[0]), float(item[1])
        if p > 0.0 and s > 0.0:
            asks.append(OrderBookLevel(price=p, size=s))

    return NormalizedOrderBook(
        instrument_id=f"BYBIT:{symbol}",
        exchange=Exchange.BYBIT,
        symbol=symbol,
        timestamp_ms=timestamp_ms,
        update_id=update_id,
        bids=bids,
        asks=asks,
    )


def normalize_bybit_klines(
    raw_list: List[List[str]],
    symbol: str,
    timeframe: Timeframe,
) -> List[NormalizedCandle]:
    """Parse Bybit V5 klines list and sort ascending by open_time_ms.

    Bybit returns newest first (descending). We sort ascending to guarantee
    standard time-series order.
    """
    candles: List[NormalizedCandle] = []
    for bar in raw_list:
        open_time = int(bar[0])
        open_p = float(bar[1])
        high_p = float(bar[2])
        low_p = float(bar[3])
        close_p = float(bar[4])
        vol = float(bar[5])
        turnover = float(bar[6])

        # Infer approximate close time based on timeframe
        interval_ms = 60_000
        if timeframe == Timeframe.M5:
            interval_ms = 300_000
        elif timeframe == Timeframe.M15:
            interval_ms = 900_000
        elif timeframe == Timeframe.H1:
            interval_ms = 3_600_000
        elif timeframe == Timeframe.H4:
            interval_ms = 14_400_000
        elif timeframe == Timeframe.D1:
            interval_ms = 86_400_000

        close_time = open_time + interval_ms - 1

        candle = NormalizedCandle(
            instrument_id=f"BYBIT:{symbol}",
            exchange=Exchange.BYBIT,
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
            trades_count=0,
            is_closed=True,
        )
        candles.append(candle)

    # Sort ascending by open_time_ms
    candles.sort(key=lambda c: c.open_time_ms)
    return candles
