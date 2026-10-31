"""Deterministic unit tests for historical instrument discovery and perpetual filtering."""

from pathlib import Path
from typing import Any, List, Optional
import pytest

from quantum.domain.enums import ContractStatus, ContractType, Exchange, Timeframe
from quantum.exchanges.base import BaseExchangeAdapter
from quantum.exchanges.models import (
    ExchangeHealthStatus,
    InstrumentInfo,
    NormalizedCandle,
    NormalizedOrderBook,
    NormalizedTicker,
)
from quantum.historical.discovery import HistoricalInstrumentDiscovery
from quantum.storage.database import DatabaseManager


class DiscoveryMockAdapter(BaseExchangeAdapter):
    """Mock adapter returning varied instrument metadata for filtering qualification."""

    def __init__(self, instruments: List[InstrumentInfo], exchange: Exchange = Exchange.ASTER) -> None:
        super().__init__(exchange, rate_limit_rps=100.0)
        self._mock_instruments = instruments

    async def fetch_instruments(self) -> List[InstrumentInfo]:
        return self._mock_instruments

    async def fetch_ticker(self, symbol: str) -> NormalizedTicker:
        raise NotImplementedError

    async def fetch_orderbook_snapshot(self, symbol: str, limit: int = 50) -> NormalizedOrderBook:
        raise NotImplementedError

    async def fetch_klines(self, symbol: str, timeframe: Timeframe, limit: int = 200, before_ms: Optional[int] = None) -> List[NormalizedCandle]:
        return []

    async def connect_market_stream(self, symbols: List[str], **kwargs: Any) -> None:
        pass

    async def disconnect(self) -> None:
        pass

    async def health_check(self) -> ExchangeHealthStatus:
        return self.health


@pytest.mark.asyncio
async def test_historical_instrument_discovery_qualification(tmp_path: Path) -> None:
    """Verify dynamic discovery filters only eligible USDT perpetuals with valid parameters."""
    db_mgr = DatabaseManager(tmp_path / "test_disc.db")
    await db_mgr.initialize()
    conn = await db_mgr.connect()

    inst_valid_btc = InstrumentInfo(
        instrument_id="ASTER:BTCUSDT",
        exchange=Exchange.ASTER,
        symbol="BTCUSDT",
        base_asset="BTC",
        quote_asset="USDT",
        status=ContractStatus.TRADING,
        contract_type=ContractType.PERPETUAL,
        tick_size=0.1,
        lot_step=0.001,
        min_order_qty=0.001,
        max_order_qty=1000.0,
        min_notional_usdt=5.0,
        max_leverage=100.0,
        maker_fee_rate=0.0002,
        taker_fee_rate=0.0005,
    )

    inst_non_usdt = InstrumentInfo(
        instrument_id="ASTER:BTCUSDC",
        exchange=Exchange.ASTER,
        symbol="BTCUSDC",
        base_asset="BTC",
        quote_asset="USDC",  # Non-USDT quote
        status=ContractStatus.TRADING,
        contract_type=ContractType.PERPETUAL,
        tick_size=0.1,
        lot_step=0.001,
        min_order_qty=0.001,
        max_order_qty=1000.0,
        min_notional_usdt=5.0,
        max_leverage=100.0,
        maker_fee_rate=0.0002,
        taker_fee_rate=0.0005,
    )

    inst_halted = InstrumentInfo(
        instrument_id="ASTER:LUNAUSDT",
        exchange=Exchange.ASTER,
        symbol="LUNAUSDT",
        base_asset="LUNA",
        quote_asset="USDT",
        status=ContractStatus.HALTED,  # Non-trading status
        contract_type=ContractType.PERPETUAL,
        tick_size=0.0001,
        lot_step=1.0,
        min_order_qty=1.0,
        max_order_qty=10000.0,
        min_notional_usdt=5.0,
        max_leverage=20.0,
        maker_fee_rate=0.0002,
        taker_fee_rate=0.0005,
    )

    inst_empty_base = InstrumentInfo(
        instrument_id="ASTER:UNKNOWNUSDT",
        exchange=Exchange.ASTER,
        symbol="UNKNOWNUSDT",
        base_asset="",  # Empty base asset
        quote_asset="USDT",
        status=ContractStatus.TRADING,
        contract_type=ContractType.PERPETUAL,
        tick_size=0.01,
        lot_step=1.0,
        min_order_qty=1.0,
        max_order_qty=10000.0,
        min_notional_usdt=5.0,
        max_leverage=20.0,
        maker_fee_rate=0.0002,
        taker_fee_rate=0.0005,
    )

    adapter = DiscoveryMockAdapter([inst_valid_btc, inst_non_usdt, inst_halted, inst_empty_base])
    discovery = HistoricalInstrumentDiscovery(db_conn=conn)

    qualified = await discovery.discover_eligible_instruments(adapter, persist=True)

    # Only inst_valid_btc must qualify
    assert len(qualified) == 1
    assert qualified[0].symbol == "BTCUSDT"

    # Verify persisted in database
    async with conn.execute("SELECT symbol, quote_asset, status FROM exchange_instruments;") as cursor:
        rows = await cursor.fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "BTCUSDT"
        assert rows[0][1] == "USDT"
        assert rows[0][2] == "TRADING"
