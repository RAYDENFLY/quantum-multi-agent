"""Authoritative Versioned Fee Schedule Registry (Phase A - Milestone 5.12.1).

Establishes a single, immutable, cryptographic source of truth for exchange fee
schedules across all QUANTUM execution, accounting, and backtesting engines.
Prevents silent parameter overrides and records exact configuration fingerprints.
"""

from dataclasses import dataclass, field
import hashlib
import json
from typing import Dict, List, Optional


@dataclass(frozen=True)
class FeeScheduleProfile:
    """Immutable, versioned exchange fee schedule profile."""
    schedule_id: str
    exchange: str
    contract_type: str
    fee_tier: str
    maker_fee_bps: float
    taker_fee_bps: float
    spread_bps_half: float
    slippage_bps_per_leg: float
    adverse_selection_bps: float
    status: str  # PROVISIONAL_ASTERDEX_RETAIL, COMPARATIVE_BENCHMARK, STRESS_TIER, THEORETICAL_DIAGNOSTIC
    verification_source: str
    version: str = "2026.11.04.v1"
    
    @property
    def fingerprint(self) -> str:
        """Computes deterministic SHA-256 fingerprint of the fee configuration."""
        payload = {
            "schedule_id": self.schedule_id,
            "exchange": self.exchange,
            "fee_tier": self.fee_tier,
            "maker_fee_bps": self.maker_fee_bps,
            "taker_fee_bps": self.taker_fee_bps,
            "spread_bps_half": self.spread_bps_half,
            "slippage_bps_per_leg": self.slippage_bps_per_leg,
            "adverse_selection_bps": self.adverse_selection_bps,
            "status": self.status,
            "version": self.version,
        }
        raw_json = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(raw_json.encode("utf-8")).hexdigest()

    def round_trip_taker_cost_bps(self) -> float:
        """Returns total round-trip friction in bps for Taker/Taker."""
        return (2 * self.taker_fee_bps) + (2 * self.spread_bps_half) + (2 * self.slippage_bps_per_leg)

    def round_trip_maker_cost_bps(self) -> float:
        """Returns total round-trip friction in bps for Maker/Maker with adverse selection."""
        return (2 * self.maker_fee_bps) + (2 * self.adverse_selection_bps)


# ---------------------------------------------------------------------------
# AUTHORITATIVE FEE SCHEDULE DEFINITIONS
# ---------------------------------------------------------------------------

# 1. PRIMARY AUTHORITATIVE RESEARCH VENUE: AsterDEX Base Retail
# Established in M5.10A: 4.0 bps maker, 10.0 bps taker, 1.0 bps half-spread, 2.0 bps slippage
# Total Taker/Taker friction = 10 + 10 + 1 + 1 + 2 + 2 = 26.0 bps
# Total Maker/Maker friction = 4 + 4 + 1.5 + 1.5 = 11.0 bps
ASTERDEX_BASE_RETAIL = FeeScheduleProfile(
    schedule_id="ASTERDEX_BASE_RETAIL_v1",
    exchange="AsterDEX",
    contract_type="USDT Perpetual Linear Futures",
    fee_tier="Base_Retail_Tier",
    maker_fee_bps=4.0,
    taker_fee_bps=10.0,
    spread_bps_half=1.0,
    slippage_bps_per_leg=2.0,
    adverse_selection_bps=1.5,
    status="PROVISIONAL_ASTERDEX_RETAIL",
    verification_source="docs/ASTERDEX_MARKET_DATA.md; Provisional Specification Verified 2026-11-04",
)

# 2. STRESS TIER 3: Congestion / Elevated Volatility Regime
ASTERDEX_STRESS_CONGESTION = FeeScheduleProfile(
    schedule_id="ASTERDEX_STRESS_CONGESTION_v1",
    exchange="AsterDEX",
    contract_type="USDT Perpetual Linear Futures",
    fee_tier="Stress_Tier_3",
    maker_fee_bps=4.0,
    taker_fee_bps=20.0,
    spread_bps_half=2.0,
    slippage_bps_per_leg=5.0,
    adverse_selection_bps=3.0,
    status="STRESS_TIER",
    verification_source="QUANTUM Phase 5.5 DEC_04.7 Stress Specification; Verified 2026-11-04",
)

# 3. COMPARATIVE BENCHMARK: Bybit VIP0 Retail
BYBIT_VIP0_BENCHMARK = FeeScheduleProfile(
    schedule_id="BYBIT_VIP0_BENCHMARK_v1",
    exchange="Bybit",
    contract_type="USDT Perpetual Linear Futures",
    fee_tier="VIP0_Retail",
    maker_fee_bps=2.0,
    taker_fee_bps=5.5,
    spread_bps_half=1.0,
    slippage_bps_per_leg=1.5,
    adverse_selection_bps=1.0,
    status="COMPARATIVE_BENCHMARK",
    verification_source="Bybit Official Fee Schedule; Verified 2026-11-04",
)

# 4. COMPARATIVE BENCHMARK: Bybit VIP1 High Volume
BYBIT_VIP1_BENCHMARK = FeeScheduleProfile(
    schedule_id="BYBIT_VIP1_BENCHMARK_v1",
    exchange="Bybit",
    contract_type="USDT Perpetual Linear Futures",
    fee_tier="VIP1",
    maker_fee_bps=1.8,
    taker_fee_bps=4.0,
    spread_bps_half=1.0,
    slippage_bps_per_leg=1.0,
    adverse_selection_bps=0.8,
    status="COMPARATIVE_BENCHMARK",
    verification_source="Bybit VIP Schedule; Verified 2026-11-04",
)

# 5. THEORETICAL DIAGNOSTIC: Zero Friction
ZERO_FRICTION_DIAGNOSTIC = FeeScheduleProfile(
    schedule_id="ZERO_FRICTION_DIAGNOSTIC_v1",
    exchange="Theoretical",
    contract_type="USDT Perpetual Linear Futures",
    fee_tier="Zero_Friction",
    maker_fee_bps=0.0,
    taker_fee_bps=0.0,
    spread_bps_half=0.0,
    slippage_bps_per_leg=0.0,
    adverse_selection_bps=0.0,
    status="THEORETICAL_DIAGNOSTIC",
    verification_source="QUANTUM Research Architecture Diagnostic Zero Friction; Verified 2026-11-04",
)


class FeeScheduleRegistry:
    """Authoritative lookup and enforcement registry for fee schedules."""
    
    _REGISTRY: Dict[str, FeeScheduleProfile] = {
        "ASTERDEX_BASE_RETAIL": ASTERDEX_BASE_RETAIL,
        "ASTERDEX_BASE_RETAIL_v1": ASTERDEX_BASE_RETAIL,
        "ASTER_RETAIL": ASTERDEX_BASE_RETAIL,
        "Base_Retail_Tier": ASTERDEX_BASE_RETAIL,
        "ASTERDEX_STRESS_CONGESTION": ASTERDEX_STRESS_CONGESTION,
        "ASTERDEX_STRESS_CONGESTION_v1": ASTERDEX_STRESS_CONGESTION,
        "Stress_Tier_3": ASTERDEX_STRESS_CONGESTION,
        "BYBIT_VIP0_BENCHMARK": BYBIT_VIP0_BENCHMARK,
        "BYBIT_VIP0_BENCHMARK_v1": BYBIT_VIP0_BENCHMARK,
        "VIP0_Retail": BYBIT_VIP0_BENCHMARK,
        "BYBIT_VIP0_DEFAULT": BYBIT_VIP0_BENCHMARK,
        "BYBIT_VIP1_BENCHMARK": BYBIT_VIP1_BENCHMARK,
        "BYBIT_VIP1": BYBIT_VIP1_BENCHMARK,
        "ZERO_FRICTION_DIAGNOSTIC": ZERO_FRICTION_DIAGNOSTIC,
        "ZERO_FRICTION_DIAGNOSTIC_v1": ZERO_FRICTION_DIAGNOSTIC,
    }

    @classmethod
    def get_authoritative_schedule(cls, key: str = "ASTERDEX_BASE_RETAIL") -> FeeScheduleProfile:
        """Retrieves authoritative fee schedule by identifier or tier name."""
        if key not in cls._REGISTRY:
            raise KeyError(
                f"Unknown fee schedule key: '{key}'. Available authoritative schedules: "
                f"{list(cls._REGISTRY.keys())}"
            )
        return cls._REGISTRY[key]

    @classmethod
    def list_all_schedules(cls) -> List[FeeScheduleProfile]:
        """Returns unique list of authoritative fee schedules."""
        seen = set()
        unique = []
        for profile in cls._REGISTRY.values():
            if profile.schedule_id not in seen:
                seen.add(profile.schedule_id)
                unique.append(profile)
        return unique

    @classmethod
    def validate_schedule_fingerprint(cls, schedule_id: str, expected_fingerprint: str) -> bool:
        """Validates that a fee schedule has not been mutated or overridden."""
        profile = cls.get_authoritative_schedule(schedule_id)
        return profile.fingerprint == expected_fingerprint
