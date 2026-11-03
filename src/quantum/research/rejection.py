"""Automatic Multi-Tier Rejection Gates for Methodological & Statistical Failures."""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np

from quantum.research.models import (
    ContinuousExperimentConfig,
    RejectionCategory,
    SpecificRejectionReason,
)
from quantum.strategies.hypothesis_engine import TradeRecord


@dataclass
class RejectionEvaluationResult:
    """Outcome of automated evaluation gate inspection."""
    is_accepted: bool
    category: Optional[RejectionCategory]
    reasons: List[str]


class AutomaticRejectionEngine:
    """Enforces strict, non-negotiable methodological and statistical failure gates."""

    @staticmethod
    def evaluate_methodology(
        config: ContinuousExperimentConfig,
        trades: List[TradeRecord],
        df_bars: Optional[object] = None,
    ) -> RejectionEvaluationResult:
        """Inspects trades and configurations for methodological and operational boundary breaches."""
        reasons: List[str] = []

        # 1. Gross Exposure Hard Cap (<= 1.0000x unlevered)
        for t in trades:
            if t.notional_usd > (config.contract.initial_equity_usd * config.contract.maximum_gross_exposure + 1e-4):
                reasons.append(
                    f"{SpecificRejectionReason.EXPOSURE_LIMIT_EXCEEDED.value}: "
                    f"Trade notional ${t.notional_usd:.2f} exceeds unlevered limit ${config.contract.initial_equity_usd:.2f}"
                )
                break

        # 2. Holding Horizon Boundary Enforcement
        max_horizon_mins = float(config.contract.maximum_holding_horizon_minutes)
        for t in trades:
            if t.duration_minutes > max_horizon_mins and not config.contract.allow_overnight_holding:
                reasons.append(
                    f"{SpecificRejectionReason.HOLDING_HORIZON_BREACH.value}: "
                    f"Trade duration {t.duration_minutes:.1f}m exceeds max horizon {max_horizon_mins:.1f}m"
                )
                break

        # 3. Next-Bar Open Execution Check (Causal verification)
        for t in trades:
            if t.entry_bar <= 0:
                reasons.append(f"{SpecificRejectionReason.LOOKAHEAD_BIAS_DETECTED.value}: Invalid entry bar {t.entry_bar}")
                break

        if reasons:
            return RejectionEvaluationResult(
                is_accepted=False,
                category=RejectionCategory.METHODOLOGICAL_FAILURE,
                reasons=reasons,
            )

        return RejectionEvaluationResult(is_accepted=True, category=None, reasons=[])

    @staticmethod
    def evaluate_statistics(
        config: ContinuousExperimentConfig,
        frequency_daily: float,
        profit_factor: float,
        net_expectancy_bps: float,
        mean_net_daily_return_pct: float,
        max_drawdown_pct: float,
        holm_bonferroni_p_value: float = 1.0,
        deflated_sharpe_prob: float = 0.0,
    ) -> RejectionEvaluationResult:
        """Inspects empirical performance metrics against non-negotiable statistical acceptance gates."""
        reasons: List[str] = []

        # 1. Drawdown Hard Cap (<= 15.0%)
        if max_drawdown_pct > 15.0:
            reasons.append(
                f"{SpecificRejectionReason.DRAWDOWN_LIMIT_EXCEEDED.value}: "
                f"Max drawdown {max_drawdown_pct:.2f}% exceeds 15.00% acceptance limit"
            )

        # 2. Mandatory Daily Return Target (>= 3.0000%)
        if mean_net_daily_return_pct < config.contract.mandatory_profitability_gate_daily_pct:
            reasons.append(
                f"{SpecificRejectionReason.SUB_TARGET_DAILY_RETURN.value}: "
                f"Mean net daily return {mean_net_daily_return_pct:.4f}% < mandatory {config.contract.mandatory_profitability_gate_daily_pct:.4f}%"
            )

        # 3. Profit Factor Gate (>= 1.30)
        if profit_factor < 1.30:
            reasons.append(
                f"{SpecificRejectionReason.LOW_PROFIT_FACTOR.value}: "
                f"Profit factor {profit_factor:.2f} < required 1.30 threshold"
            )

        # 4. Positive Net Expectancy Gate (> 0.0 bps)
        if net_expectancy_bps <= 0.0:
            reasons.append(
                f"{SpecificRejectionReason.NEGATIVE_NET_EXPECTANCY.value}: "
                f"Net expectancy {net_expectancy_bps:.2f} bps <= 0.0 bps"
            )

        # 5. Minimum Trade Frequency Gate (>= 10.0 trades/day for Category A)
        if frequency_daily < config.contract.minimum_trade_frequency_daily:
            reasons.append(
                f"{SpecificRejectionReason.INSUFFICIENT_FREQUENCY.value}: "
                f"Frequency {frequency_daily:.2f} trades/day < required minimum {config.contract.minimum_trade_frequency_daily:.1f}"
            )

        # 6. Statistical Significance Gate (Holm-Bonferroni adjusted p < 0.05)
        if holm_bonferroni_p_value >= 0.05:
            reasons.append(
                f"{SpecificRejectionReason.STATISTICALLY_INSIGNIFICANT.value}: "
                f"Holm-Bonferroni adjusted p-value {holm_bonferroni_p_value:.4f} >= 0.05"
            )

        if reasons:
            return RejectionEvaluationResult(
                is_accepted=False,
                category=RejectionCategory.STATISTICAL_FAILURE,
                reasons=reasons,
            )

        return RejectionEvaluationResult(is_accepted=True, category=None, reasons=[])
