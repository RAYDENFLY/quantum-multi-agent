"""Market data models and normalized contracts for exchange integration."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

from quantum.domain.enums import ConnectionState, ContractStatus, ContractType, Exchange, Timeframe


class OrderBookLevel(BaseModel):
    """Single price-quantity level in an order book."""
    model_config = ConfigDict(frozen=True)

    price: float = Field(gt=0.0)
    size: float = Field(ge=0.0)


class NormalizedOrderBook(BaseModel):
    """Normalized L2 order book representation.

    Bids are ordered descending by price.
    Asks are ordered ascending by price.
    """
    model_config = ConfigDict(validate_assignment=True)

    instrument_id: str
    exchange: Exchange
    symbol: str
    timestamp_ms: int
    update_id: int
    bids: List[OrderBookLevel] = Field(default_factory=list)
    asks: List[OrderBookLevel] = Field(default_factory=list)
    bid1_price: float = 0.0
    bid1_size: float = 0.0
    ask1_price: float = 0.0
    ask1_size: float = 0.0
    spread_bps: float = 0.0
    mid_price: float = 0.0
    is_crossed: bool = False

    @model_validator(mode="after")
    def compute_derived_metrics(self) -> "NormalizedOrderBook":
        """Compute top-of-book, mid price, spread, and crossed book flags."""
        b1_p = self.bids[0].price if self.bids else 0.0
        b1_s = self.bids[0].size if self.bids else 0.0
        a1_p = self.asks[0].price if self.asks else 0.0
        a1_s = self.asks[0].size if self.asks else 0.0

        if b1_p > 0.0 and a1_p > 0.0:
            mid = (b1_p + a1_p) / 2.0
            spread = max(0.0, ((a1_p - b1_p) / mid) * 10000.0) if mid > 0.0 else 0.0
            crossed = b1_p >= a1_p
        else:
            mid = b1_p or a1_p
            spread = 0.0
            crossed = False

        object.__setattr__(self, "bid1_price", b1_p)
        object.__setattr__(self, "bid1_size", b1_s)
        object.__setattr__(self, "ask1_price", a1_p)
        object.__setattr__(self, "ask1_size", a1_s)
        object.__setattr__(self, "mid_price", mid)
        object.__setattr__(self, "spread_bps", spread)
        object.__setattr__(self, "is_crossed", crossed)
        return self

    def top_n(self, depth: int = 10) -> "NormalizedOrderBook":
        """Return a copy truncated to top-N levels."""
        return NormalizedOrderBook(
            instrument_id=self.instrument_id,
            exchange=self.exchange,
            symbol=self.symbol,
            timestamp_ms=self.timestamp_ms,
            update_id=self.update_id,
            bids=self.bids[:depth],
            asks=self.asks[:depth],
        )


class NormalizedTicker(BaseModel):
    """Normalized 24h ticker and market mark/funding status."""
    model_config = ConfigDict(validate_assignment=True)

    instrument_id: str
    exchange: Exchange
    symbol: str
    timestamp_ms: int
    last_price: float = Field(gt=0.0)
    mark_price: float = Field(gt=0.0)
    index_price: float = Field(gt=0.0)
    bid1_price: float = Field(default=0.0, ge=0.0)
    bid1_size: float = Field(default=0.0, ge=0.0)
    ask1_price: float = Field(default=0.0, ge=0.0)
    ask1_size: float = Field(default=0.0, ge=0.0)
    spread_bps: float = Field(default=0.0, ge=0.0)
    volume_24h: float = Field(default=0.0, ge=0.0)
    turnover_24h_usdt: float = Field(default=0.0, ge=0.0)
    high_price_24h: Optional[float] = None
    low_price_24h: Optional[float] = None
    price_change_24h_pct: Optional[float] = None
    open_interest: Optional[float] = None
    funding_rate: Optional[float] = None
    next_funding_time_ms: Optional[int] = None

    @model_validator(mode="after")
    def calculate_spread(self) -> "NormalizedTicker":
        """Compute spread in basis points if not pre-populated."""
        if self.bid1_price > 0.0 and self.ask1_price > 0.0 and self.spread_bps == 0.0:
            mid = (self.bid1_price + self.ask1_price) / 2.0
            if mid > 0.0:
                spread = max(0.0, ((self.ask1_price - self.bid1_price) / mid) * 10000.0)
                object.__setattr__(self, "spread_bps", spread)
        return self


class NormalizedCandle(BaseModel):
    """Normalized OHLCV candlestick representation."""
    model_config = ConfigDict(validate_assignment=True)

    instrument_id: str
    exchange: Exchange
    symbol: str
    timeframe: Timeframe
    open_time_ms: int
    close_time_ms: int
    open_price: float = Field(gt=0.0)
    high_price: float = Field(gt=0.0)
    low_price: float = Field(gt=0.0)
    close_price: float = Field(gt=0.0)
    volume: float = Field(ge=0.0)
    turnover_usdt: float = Field(ge=0.0)
    trades_count: int = Field(default=0, ge=0)
    is_closed: bool = True

    @model_validator(mode="after")
    def validate_ohlc_invariants(self) -> "NormalizedCandle":
        """Validate high is highest and low is lowest."""
        if self.high_price < max(self.open_price, self.close_price):
            raise ValueError(f"High price {self.high_price} cannot be less than open {self.open_price} or close {self.close_price}")
        if self.low_price > min(self.open_price, self.close_price):
            raise ValueError(f"Low price {self.low_price} cannot be greater than open {self.open_price} or close {self.close_price}")
        if self.close_time_ms <= self.open_time_ms:
            raise ValueError(f"Close time {self.close_time_ms} must be strictly greater than open time {self.open_time_ms}")
        return self


class InstrumentInfo(BaseModel):
    """Normalized instrument metadata for USDT perpetual futures."""
    model_config = ConfigDict(validate_assignment=True)

    instrument_id: str
    exchange: Exchange
    symbol: str
    base_asset: str
    quote_asset: str = "USDT"
    status: ContractStatus = ContractStatus.TRADING
    contract_type: ContractType = ContractType.PERPETUAL
    tick_size: float = Field(gt=0.0)
    lot_step: float = Field(gt=0.0)
    min_order_qty: float = Field(gt=0.0)
    max_order_qty: float = Field(gt=0.0)
    min_notional_usdt: float = Field(ge=0.0)
    max_leverage: float = Field(default=50.0, ge=1.0)
    maker_fee_rate: float = Field(default=0.0002)
    taker_fee_rate: float = Field(default=0.00055)
    onboard_timestamp_ms: int = Field(default=0)
    updated_at_ms: int = Field(default=0)


class ExchangeHealthStatus(BaseModel):
    """Real-time health and connectivity metrics for an exchange."""
    model_config = ConfigDict(validate_assignment=True)

    exchange: Exchange
    state: ConnectionState = ConnectionState.DISCONNECTED
    rest_latency_ms: float = 0.0
    ws_latency_ms: float = 0.0
    last_heartbeat_ms: int = 0
    last_message_ms: int = 0
    reconnect_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    updated_at_ms: int = 0
