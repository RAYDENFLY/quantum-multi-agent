"""Dynamic perpetual contract discovery and qualification filtering."""

import time
from typing import List, Optional
import aiosqlite

from quantum.core.logging import get_logger
from quantum.domain.enums import ContractStatus, ContractType, Exchange
from quantum.exchanges.base import BaseExchangeAdapter
from quantum.exchanges.models import InstrumentInfo

logger = get_logger("historical.discovery")


class HistoricalInstrumentDiscovery:
    """Discovers and qualifies active USDT perpetual contracts for historical data collection."""

    def __init__(self, db_conn: Optional[aiosqlite.Connection] = None) -> None:
        self.conn = db_conn

    async def discover_eligible_instruments(
        self,
        adapter: BaseExchangeAdapter,
        persist: bool = True,
    ) -> List[InstrumentInfo]:
        """Query exchange metadata and apply strict perpetual qualification filters."""
        raw_instruments = await adapter.fetch_instruments()
        now_ms = int(time.time() * 1000)

        eligible: List[InstrumentInfo] = []
        for inst in raw_instruments:
            # 1. Trading status check
            status_val = inst.status.value if hasattr(inst.status, "value") else str(inst.status).upper()
            if status_val != ContractStatus.TRADING.value:
                continue

            # 2. Quote asset check: must be USDT-settled
            if inst.quote_asset.upper() != "USDT":
                continue

            # 3. Market category check: perpetual only (no spot, inverse, or expired deliveries)
            contract_type_val = (
                inst.contract_type.value
                if hasattr(inst.contract_type, "value")
                else str(inst.contract_type).upper()
            )
            if contract_type_val not in (ContractType.PERPETUAL.value, ContractType.LINEAR_PERPETUAL.value):
                continue

            # 4. Valid numeric metadata filters
            if inst.tick_size <= 0.0 or inst.lot_step <= 0.0 or inst.min_order_qty <= 0.0:
                continue

            # 5. Symbol sanity
            if not inst.base_asset or not inst.symbol:
                continue

            eligible.append(inst)

        logger.info(
            "Discovered %d eligible USDT perpetual contracts on %s (out of %d total)",
            len(eligible),
            adapter.exchange.value if hasattr(adapter.exchange, "value") else str(adapter.exchange),
            len(raw_instruments),
        )

        if persist and self.conn:
            await self._persist_instruments(eligible, now_ms)

        return eligible

    async def _persist_instruments(self, instruments: List[InstrumentInfo], timestamp_ms: int) -> None:
        """Persist discovered instruments and their observed timestamp into exchange_instruments table."""
        sql = """
        INSERT INTO exchange_instruments (
            instrument_id, exchange, symbol, base_asset, quote_asset,
            status, tick_size, lot_step, min_order_qty, max_order_qty,
            min_notional_usdt, max_leverage, maker_fee_rate, taker_fee_rate,
            onboard_timestamp_ms, updated_at_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(instrument_id) DO UPDATE SET
            status = excluded.status,
            tick_size = excluded.tick_size,
            lot_step = excluded.lot_step,
            min_order_qty = excluded.min_order_qty,
            max_order_qty = excluded.max_order_qty,
            min_notional_usdt = excluded.min_notional_usdt,
            max_leverage = excluded.max_leverage,
            maker_fee_rate = excluded.maker_fee_rate,
            taker_fee_rate = excluded.taker_fee_rate,
            updated_at_ms = excluded.updated_at_ms;
        """
        params = [
            (
                inst.instrument_id,
                inst.exchange.value if hasattr(inst.exchange, "value") else str(inst.exchange),
                inst.symbol.upper(),
                inst.base_asset.upper(),
                inst.quote_asset.upper(),
                inst.status.value if hasattr(inst.status, "value") else str(inst.status),
                inst.tick_size,
                inst.lot_step,
                inst.min_order_qty,
                inst.max_order_qty,
                inst.min_notional_usdt,
                inst.max_leverage,
                inst.maker_fee_rate,
                inst.taker_fee_rate,
                timestamp_ms,
                timestamp_ms,
            )
            for inst in instruments
        ]
        await self.conn.executemany(sql, params)
        await self.conn.commit()
