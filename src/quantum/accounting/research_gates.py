"""Three-Stage Research Gate Engine with Lifecycle Separation (Phase D).

Separates research evaluation into:
- Stage 1: Exploratory Discovery (does NOT eliminate candidates for sub-3% daily return if net edge > 0).
- Stage 2: Candidate Validation (regime stability, PF > 1.0, multiple-testing correction, cost stress).
- Stage 3: Final Promotion (mandatory >= 3.00% daily return, max DD <= 15.0%, exposure <= 1.0x).
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class ResearchLifecycleStage(str, Enum):
    """The three distinct evaluation lifecycle stages."""
    STAGE_1_EXPLORATORY_DISCOVERY = "STAGE_1_EXPLORATORY_DISCOVERY"
    STAGE_2_CANDIDATE_VALIDATION = "STAGE_2_CANDIDATE_VALIDATION"
    STAGE_3_FINAL_PROMOTION = "STAGE_3_FINAL_PROMOTION"


@dataclass
class GateInspectionResult:
    """Outcome of a stage-specific research gate inspection."""
    stage: ResearchLifecycleStage
    passed: bool
    rejection_reasons: List[str] = field(default_factory=list)
    advisory_notes: List[str] = field(default_factory=list)


class CorrectedResearchGates:
    """Multi-stage gate validator preventing premature elimination of early alpha signals."""

    @staticmethod
    def inspect_stage_1_discovery(
        gross_exposure_max: float,
        net_expectancy_bps: float,
        sample_episodes: int,
        has_lookahead_bias: bool = False,
        has_data_leakage: bool = False,
        mean_net_daily_return_pct: float = 0.0,
    ) -> GateInspectionResult:
        """Stage 1: Exploratory Discovery Gate.
        
        Permits hypothesis exploration if accounting and exposure are valid, even if daily return < 3%.
        """
        reasons = []
        advisory = []

        # 1. Hard Methodological Invariants
        if gross_exposure_max > 1.0001:
            reasons.append(f"EXPOSURE_BREACH: Max gross exposure {gross_exposure_max:.4f} > 1.0000x")
        if has_lookahead_bias:
            reasons.append("LOOKAHEAD_BIAS: Trade timing uses future bar information")
        if has_data_leakage:
            reasons.append("DATA_LEAKAGE: Overlapping partition boundaries or missing embargo")
        if sample_episodes < 30:
            reasons.append(f"INSUFFICIENT_SAMPLE: Completed episodes {sample_episodes} < 30 minimum for discovery")

        # 2. Net Edge Invariant
        if net_expectancy_bps <= 0.0:
            reasons.append(f"NEGATIVE_NET_EDGE: Net expectancy {net_expectancy_bps:.2f} bps <= 0.0 bps")

        # 3. Advisory Note (Not Rejection) for Daily Return
        if mean_net_daily_return_pct < 3.0000:
            advisory.append(
                f"SUB_PROMOTION_DAILY_RETURN: Mean daily return {mean_net_daily_return_pct:.4f}% < 3.00% "
                f"(Permitted in Stage 1 Discovery; must be refined before Stage 3 Promotion)."
            )

        passed = len(reasons) == 0
        return GateInspectionResult(
            stage=ResearchLifecycleStage.STAGE_1_EXPLORATORY_DISCOVERY,
            passed=passed,
            rejection_reasons=reasons,
            advisory_notes=advisory,
        )

    @staticmethod
    def inspect_stage_2_validation(
        net_expectancy_bps: float,
        profit_factor: float,
        regime_stability_score: float,
        holm_bonferroni_p_value: float,
        cost_stress_retained_pct: float,
        sample_episodes: int,
    ) -> GateInspectionResult:
        """Stage 2: Candidate Validation Gate.
        
        Evaluates out-of-sample robustness, regime consistency, and multiple-testing significance.
        """
        reasons = []
        advisory = []

        if net_expectancy_bps <= 0.0:
            reasons.append(f"NEGATIVE_NET_EXPECTANCY: Net expectancy {net_expectancy_bps:.2f} bps <= 0.0 bps")
        if profit_factor <= 1.00:
            reasons.append(f"PROFIT_FACTOR_DEFICIT: Profit factor {profit_factor:.2f} <= 1.00 breakeven")
        elif profit_factor < 1.30:
            advisory.append(f"PROFIT_FACTOR_SUB_PREFERRED: Profit factor {profit_factor:.2f} < 1.30 preferred threshold")

        if regime_stability_score < 0.20:
            reasons.append(f"REGIME_INSTABILITY: Cross-regime performance variance too high (score {regime_stability_score:.2f} < 0.20)")
        if holm_bonferroni_p_value >= 0.05:
            reasons.append(f"STATISTICAL_INSIGNIFICANCE: Holm-Bonferroni adjusted p-value {holm_bonferroni_p_value:.4f} >= 0.05")
        if cost_stress_retained_pct < 0.0:
            reasons.append(f"COST_STRESS_FAILURE: Strategy generates losses under adverse cost stress")

        passed = len(reasons) == 0
        return GateInspectionResult(
            stage=ResearchLifecycleStage.STAGE_2_CANDIDATE_VALIDATION,
            passed=passed,
            rejection_reasons=reasons,
            advisory_notes=advisory,
        )

    @staticmethod
    def inspect_stage_3_promotion(
        mean_net_daily_return_pct: float,
        max_drawdown_pct: float,
        gross_exposure_max: float,
        profit_factor: float,
        is_causal_next_bar: bool,
        is_holdout_clean: bool,
        is_independently_reproduced: bool,
    ) -> GateInspectionResult:
        """Stage 3: Final Production / Paper Trading Promotion Gate.
        
        Strict enforcement of all non-negotiable QUANTUM mandates.
        """
        reasons = []

        if mean_net_daily_return_pct < 3.0000:
            reasons.append(f"MANDATORY_TARGET_NOT_MET: Mean net daily return {mean_net_daily_return_pct:.4f}% < mandatory 3.0000%")
        if max_drawdown_pct > 15.00:
            reasons.append(f"DRAWDOWN_LIMIT_EXCEEDED: Max drawdown {max_drawdown_pct:.2f}% > 15.00% limit")
        if gross_exposure_max > 1.0001:
            reasons.append(f"EXPOSURE_BREACH: Max gross exposure {gross_exposure_max:.4f} > 1.0000x unlevered")
        if profit_factor < 1.30:
            reasons.append(f"PROFIT_FACTOR_DEFICIT: Profit factor {profit_factor:.2f} < 1.30 mandatory promotion threshold")
        if not is_causal_next_bar:
            reasons.append("EXECUTION_MODEL_VIOLATION: Must execute strictly on causal next-bar open")
        if not is_holdout_clean:
            reasons.append("HOLDOUT_CONTAMINATION: Prospective holdout boundary was accessed")
        if not is_independently_reproduced:
            reasons.append("REPRODUCIBILITY_FAILURE: Independent execution failed to reproduce metrics")

        passed = len(reasons) == 0
        return GateInspectionResult(
            stage=ResearchLifecycleStage.STAGE_3_FINAL_PROMOTION,
            passed=passed,
            rejection_reasons=reasons,
            advisory_notes=[],
        )
