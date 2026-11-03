"""Modular Execution Economics & Cost Sensitivity Engine (Phase C).

Decomposes and evaluates:
1. Scenario 1: Taker / Taker (Aggressive liquidity removal on both sides).
2. Scenario 2: Maker / Maker (Passive liquidity provision with queue and adverse selection modeling;
   explicitly classified as SIMULATED_EXECUTION_ASSUMPTION).
3. Scenario 3: Maker / Taker (Passive entry, taker emergency exit).
4. Scenario 4: Taker / Maker (Aggressive entry, passive limit exit).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


class ExecutionScenario(str, Enum):
    """The four canonical execution scenarios."""
    TAKER_TAKER = "TAKER_TAKER"
    MAKER_MAKER = "MAKER_MAKER"
    MAKER_TAKER = "MAKER_TAKER"
    TAKER_MAKER = "TAKER_MAKER"


@dataclass
class CostModelProfile:
    """Configurable transaction cost and friction parameter profile."""
    name: str
    maker_fee_bps: float = 4.0
    taker_fee_bps: float = 10.0
    spread_bps_half: float = 1.0
    slippage_bps_per_leg: float = 2.0
    adverse_selection_bps: float = 1.5  # Toxic flow markout penalty for maker fills
    fill_probability_threshold: float = 0.70  # Conservative fill probability for maker orders
    partial_fill_ratio: float = 1.0     # 1.0 for 100% fill, < 1.0 for partial fill
    classification: str = "PROVISIONAL_ASTERDEX_RETAIL"


# Authoritative cost model profiles
DEFAULT_ASTERDEX_COSTS = CostModelProfile(name="AsterDEX_Base_Retail")

# Phase B Maker Realism Profiles
MAKER_CONSERVATIVE_PROFILE = CostModelProfile(
    name="Maker_Conservative_Assumptions",
    maker_fee_bps=4.0,
    taker_fee_bps=10.0,
    spread_bps_half=1.0,
    slippage_bps_per_leg=2.0,
    adverse_selection_bps=2.5,
    fill_probability_threshold=0.70,
    classification="SIMULATED_EXECUTION_ASSUMPTION",
)
MAKER_MODERATE_PROFILE = CostModelProfile(
    name="Maker_Moderate_Assumptions",
    maker_fee_bps=4.0,
    taker_fee_bps=10.0,
    spread_bps_half=1.0,
    slippage_bps_per_leg=2.0,
    adverse_selection_bps=1.5,
    fill_probability_threshold=0.50,
    classification="SIMULATED_EXECUTION_ASSUMPTION",
)
MAKER_OPTIMISTIC_PROFILE = CostModelProfile(
    name="Maker_Optimistic_Assumptions",
    maker_fee_bps=4.0,
    taker_fee_bps=10.0,
    spread_bps_half=1.0,
    slippage_bps_per_leg=2.0,
    adverse_selection_bps=0.5,
    fill_probability_threshold=0.30,
    classification="SIMULATED_OPTIMISTIC_NOT_FOR_PROMOTION",
)

# Phase B Stress Profiles
ADVERSE_SELECTION_STRESS_PROFILE = CostModelProfile(
    name="Stress_Adverse_Selection",
    maker_fee_bps=4.0,
    taker_fee_bps=10.0,
    spread_bps_half=1.0,
    slippage_bps_per_leg=2.0,
    adverse_selection_bps=4.0,
    classification="STRESS_TIER",
)
STRESS_SLIPPAGE_COSTS = CostModelProfile(
    name="Stress_Adverse_Slippage",
    slippage_bps_per_leg=7.0,  # +5 bps adverse slippage
    adverse_selection_bps=3.5,
    classification="STRESS_TIER",
)
STRESS_FEE_COSTS = CostModelProfile(
    name="Stress_Fee_Increase",
    taker_fee_bps=20.0,  # +10 bps taker fee
    maker_fee_bps=8.0,
    classification="STRESS_TIER",
)
STRESS_PARTIAL_FILL_COSTS = CostModelProfile(
    name="Stress_50pct_Partial_Fill",
    partial_fill_ratio=0.50,
    classification="STRESS_TIER",
)
ZERO_FRICTION_DIAGNOSTIC = CostModelProfile(
    name="Zero_Friction_Diagnostic",
    maker_fee_bps=0.0,
    taker_fee_bps=0.0,
    spread_bps_half=0.0,
    slippage_bps_per_leg=0.0,
    adverse_selection_bps=0.0,
    classification="THEORETICAL_GROSS_DIAGNOSTIC",
)


@dataclass
class ExecutionOutcome:
    """Detailed attribution of an executed or simulated trade episode."""
    scenario: ExecutionScenario
    fill_status: str  # FILLED, PARTIALLY_FILLED, MISSED
    entry_fill_price: float
    exit_fill_price: float
    effective_notional: float
    gross_pnl_usd: float
    gross_edge_bps: float
    entry_fee_usd: float
    exit_fee_usd: float
    spread_cost_usd: float
    slippage_cost_usd: float
    adverse_selection_usd: float
    funding_usd: float
    total_cost_usd: float
    total_friction_bps: float
    net_pnl_usd: float
    net_edge_bps: float
    execution_classification: str


class ExecutionEconomicsEngine:
    """Evaluates candidate trades across execution scenarios and cost sensitivities."""

    @staticmethod
    def estimate_maker_fill_probability(
        high: float,
        low: float,
        limit_price: float,
        volume: float,
        atr: float,
        side_is_long: bool,
        threshold: float = 0.50,
    ) -> Tuple[bool, float]:
        """Models passive queue fill probability and adverse selection based on bar microstructure.
        
        GOVERNANCE REQUIREMENT:
        Because OHLCV bars lack L2 order-book queue depth, this is explicitly classified as
        a SIMULATED_EXECUTION_ASSUMPTION.
        """
        # A limit order can only fill if candle penetrated the limit price
        if side_is_long:
            penetration = limit_price - low
            if penetration < 0:
                return False, 0.0  # Price never reached limit buy
        else:
            penetration = high - limit_price
            if penetration < 0:
                return False, 0.0  # Price never reached limit sell

        # Deeper penetration into the candle increases fill probability
        bar_range = max(1e-6, high - low)
        penetration_ratio = min(1.0, max(0.0, penetration / bar_range))

        # Relative volatility / bar range vs ATR
        vol_factor = min(1.0, bar_range / (atr + 1e-6))
        fill_prob = (0.50 * penetration_ratio) + (0.50 * vol_factor)

        filled = fill_prob >= threshold
        return filled, fill_prob

    @classmethod
    def evaluate_episode(
        cls,
        side_is_long: bool,
        entry_price: float,
        exit_price: float,
        notional_usd: float,
        scenario: ExecutionScenario,
        profile: CostModelProfile = DEFAULT_ASTERDEX_COSTS,
        bar_high: Optional[float] = None,
        bar_low: Optional[float] = None,
        bar_volume: Optional[float] = None,
        atr: Optional[float] = None,
    ) -> ExecutionOutcome:
        """Computes exact trade-level PnL, fees, spread, slippage, and adverse selection."""
        # 1. Determine Maker vs Taker per leg
        entry_is_maker = scenario in (ExecutionScenario.MAKER_MAKER, ExecutionScenario.MAKER_TAKER)
        exit_is_maker = scenario in (ExecutionScenario.MAKER_MAKER, ExecutionScenario.TAKER_MAKER)

        # 2. Check Maker Fill Feasibility
        fill_status = "FILLED"
        effective_notional = notional_usd * profile.partial_fill_ratio

        if entry_is_maker and bar_high is not None and bar_low is not None and atr is not None:
            filled, prob = cls.estimate_maker_fill_probability(
                high=bar_high,
                low=bar_low,
                limit_price=entry_price,
                volume=bar_volume or 1000.0,
                atr=atr,
                side_is_long=side_is_long,
                threshold=profile.fill_probability_threshold,
            )
            if not filled:
                # Missed maker entry -> 0 PnL, 0 cost
                return ExecutionOutcome(
                    scenario=scenario,
                    fill_status="MISSED_ENTRY",
                    entry_fill_price=0.0,
                    exit_fill_price=0.0,
                    effective_notional=0.0,
                    gross_pnl_usd=0.0,
                    gross_edge_bps=0.0,
                    entry_fee_usd=0.0,
                    exit_fee_usd=0.0,
                    spread_cost_usd=0.0,
                    slippage_cost_usd=0.0,
                    adverse_selection_usd=0.0,
                    funding_usd=0.0,
                    total_cost_usd=0.0,
                    total_friction_bps=0.0,
                    net_pnl_usd=0.0,
                    net_edge_bps=0.0,
                    execution_classification="SIMULATED_EXECUTION_ASSUMPTION",
                )

        # 3. Calculate Prices with Slippage and Spread
        # Maker orders do not cross spread and do not incur slippage, but incur adverse selection
        if entry_is_maker:
            entry_fill = entry_price
            entry_spread = 0.0
            entry_slip = 0.0
            adv_sel_entry = effective_notional * (profile.adverse_selection_bps / 10_000.0)
            entry_fee = effective_notional * (profile.maker_fee_bps / 10_000.0)
        else:
            entry_spread = effective_notional * (profile.spread_bps_half / 10_000.0)
            entry_slip = effective_notional * (profile.slippage_bps_per_leg / 10_000.0)
            adv_sel_entry = 0.0
            entry_fee = effective_notional * (profile.taker_fee_bps / 10_000.0)
            entry_fill = entry_price * (1.0 + (profile.spread_bps_half + profile.slippage_bps_per_leg) / 10_000.0) if side_is_long else entry_price * (1.0 - (profile.spread_bps_half + profile.slippage_bps_per_leg) / 10_000.0)

        # Exit leg
        exit_notional = effective_notional * (exit_price / entry_price)
        if exit_is_maker:
            exit_fill = exit_price
            exit_spread = 0.0
            exit_slip = 0.0
            adv_sel_exit = exit_notional * (profile.adverse_selection_bps / 10_000.0)
            exit_fee = exit_notional * (profile.maker_fee_bps / 10_000.0)
        else:
            exit_spread = exit_notional * (profile.spread_bps_half / 10_000.0)
            exit_slip = exit_notional * (profile.slippage_bps_per_leg / 10_000.0)
            adv_sel_exit = 0.0
            exit_fee = exit_notional * (profile.taker_fee_bps / 10_000.0)
            exit_fill = exit_price * (1.0 - (profile.spread_bps_half + profile.slippage_bps_per_leg) / 10_000.0) if side_is_long else exit_price * (1.0 + (profile.spread_bps_half + profile.slippage_bps_per_leg) / 10_000.0)

        # 4. Gross PnL
        raw_price_ret = (exit_price - entry_price) / entry_price if side_is_long else (entry_price - exit_price) / entry_price
        gross_pnl = effective_notional * raw_price_ret
        gross_edge_bps = raw_price_ret * 10_000.0

        # 5. Total Friction Decomposition
        spread_total = entry_spread + exit_spread
        slippage_total = entry_slip + exit_slip
        adv_sel_total = adv_sel_entry + adv_sel_exit
        total_cost = entry_fee + exit_fee + spread_total + slippage_total + adv_sel_total
        total_friction_bps = (total_cost / effective_notional) * 10_000.0 if effective_notional > 0 else 0.0

        # 6. Net PnL & Edge
        net_pnl = gross_pnl - total_cost
        net_edge_bps = gross_edge_bps - total_friction_bps

        classification = (
            "SIMULATED_EXECUTION_ASSUMPTION"
            if (entry_is_maker or exit_is_maker)
            else "AGGRESSIVE_TAKER_OBSERVED"
        )

        return ExecutionOutcome(
            scenario=scenario,
            fill_status=fill_status,
            entry_fill_price=round(entry_fill, 4),
            exit_fill_price=round(exit_fill, 4),
            effective_notional=round(effective_notional, 2),
            gross_pnl_usd=round(gross_pnl, 4),
            gross_edge_bps=round(gross_edge_bps, 2),
            entry_fee_usd=round(entry_fee, 4),
            exit_fee_usd=round(exit_fee, 4),
            spread_cost_usd=round(spread_total, 4),
            slippage_cost_usd=round(slippage_total, 4),
            adverse_selection_usd=round(adv_sel_total, 4),
            funding_usd=0.0,
            total_cost_usd=round(total_cost, 4),
            total_friction_bps=round(total_friction_bps, 2),
            net_pnl_usd=round(net_pnl, 4),
            net_edge_bps=round(net_edge_bps, 2),
            execution_classification=classification,
        )
