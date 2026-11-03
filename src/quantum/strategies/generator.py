"""Evidence-Driven Multi-Batch Strategy Configuration Generator (Batches 001, 002, 003)."""

from typing import List, Tuple

from quantum.strategies.schemas import (
    EntryParameters,
    ExitParameters,
    RiskExecutionParameters,
    StrategyConfiguration,
    StrategyFamily,
)

ALL_10_ASSETS: Tuple[str, ...] = (
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "SOLUSDT", "AVAXUSDT", "LINKUSDT", "DOGEUSDT", "LTCUSDT",
)

ALPHA_6_ASSETS: Tuple[str, ...] = (
    "DOGEUSDT", "SOLUSDT", "ADAUSDT", "XRPUSDT", "LINKUSDT", "AVAXUSDT",
)

CORE_4_ASSETS: Tuple[str, ...] = (
    "DOGEUSDT", "SOLUSDT", "ADAUSDT", "XRPUSDT",
)

HIGH_AUC_5_ASSETS: Tuple[str, ...] = (
    "LINKUSDT", "LTCUSDT", "DOGEUSDT", "BNBUSDT", "ADAUSDT",
)

MAJORS_3_ASSETS: Tuple[str, ...] = (
    "BTCUSDT", "ETHUSDT", "BNBUSDT",
)


def generate_batch_001() -> List[StrategyConfiguration]:
    """Generates Batch 001 (STRAT_001 to STRAT_100) across the 7 research families (20/15/15/15/15/10/10)."""
    configs: List[StrategyConfiguration] = []

    # =========================================================================
    # FAMILY 1: LIQUIDITY_MICROSTRUCTURE (20 candidates: STRAT_001 - STRAT_020)
    # =========================================================================
    f1_specs = [
        # (assets, dir_mode, pm, vq, rvol, tbr_min, wick_min, htf_lb, htf_max, tp1, sl, h, risk_pct, hyp)
        (ALL_10_ASSETS, "LONG_ONLY", 0.22, 0.90, 1.2, 0.52, 0.0, 12, 10000.0, 2.5, 1.2, 24, 0.015, "Order-flow buyer absorption (taker_buy >= 52%, RVOL >= 1.2) across 10 assets."),
        (ALL_10_ASSETS, "LONG_ONLY", 0.25, 0.90, 1.5, 0.54, 0.15, 12, 10000.0, 2.5, 1.2, 24, 0.015, "Aggressive buyer displacement (taker_buy >= 54%, RVOL >= 1.5, lower wick >= 15%)."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.25, 0.90, 1.0, 0.0, 0.0, 12, -50.0, 2.5, 1.2, 18, 0.020, "1h liquidity flush absorption (htf_ret_12 <= -50 bps) with Long OOF reclaim on 6 alpha altcoins."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.25, 0.92, 1.0, 0.0, 0.15, 12, -50.0, 2.8, 1.2, 18, 0.020, "1h liquidity flush + lower wick rejection (>= 15%) on 6 alpha altcoins."),
        (CORE_4_ASSETS, "LONG_ONLY", 0.25, 0.90, 1.0, 0.0, 0.0, 12, -50.0, 2.5, 1.2, 12, 0.025, "High-velocity 1h flush reclaim (12-bar horizon) on DOGE/SOL/ADA/XRP."),
        (CORE_4_ASSETS, "LONG_ONLY", 0.25, 0.90, 1.0, 0.0, 0.0, 12, -65.0, 3.0, 1.3, 18, 0.025, "Deep 1h liquidity sweep (<= -65 bps) reclaim on DOGE/SOL/ADA/XRP."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.22, 0.88, 1.1, 0.48, 0.0, 12, -40.0, 2.4, 1.2, 18, 0.020, "Moderate 1h pullback absorption (<= -40 bps, RVOL >= 1.1) on 6 alpha assets."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.28, 0.92, 1.2, 0.50, 0.10, 12, -50.0, 3.0, 1.2, 24, 0.020, "High-conviction margin (>= 0.28) + 1h flush absorption + buyer flow >= 50%."),
        (ALL_10_ASSETS, "LONG_ONLY", 0.25, 0.90, 1.0, 0.0, 0.0, 12, -50.0, 2.5, 1.2, 18, 0.020, "Fleet-wide 10-asset 1h liquidity flush reclaim (htf_ret_12 <= -50 bps)."),
        (ALL_10_ASSETS, "BOTH", 0.25, 0.90, 1.3, 0.0, 0.25, 12, 10000.0, 2.5, 1.2, 18, 0.015, "Bidirectional wick sweep rejection (wick >= 25%, RVOL >= 1.3) across 10 assets."),
        (ALPHA_6_ASSETS, "ABSORPTION_REVERSAL", 0.25, 0.90, 1.0, 0.0, 0.15, 12, -50.0, 2.5, 1.2, 18, 0.020, "Bidirectional absorption: Long on 1h flush (<= -50 bps), Short on 1h spike (>= +75 bps) with wick."),
        (CORE_4_ASSETS, "ABSORPTION_REVERSAL", 0.26, 0.90, 1.0, 0.0, 0.20, 12, -55.0, 2.6, 1.2, 16, 0.022, "Core 4-asset bidirectional absorption with 20% wick rejection."),
        (HIGH_AUC_5_ASSETS, "LONG_ONLY", 0.24, 0.90, 1.2, 0.51, 0.0, 6, -35.0, 2.5, 1.2, 18, 0.020, "30-minute fast flush absorption (htf_ret_6 <= -35 bps) on Top-5 AUC specialists."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.24, 0.90, 1.0, 0.0, 0.0, 24, -75.0, 2.8, 1.3, 24, 0.020, "2-hour structural flush absorption (htf_ret_24 <= -75 bps) on 6 alpha assets."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.25, 0.90, 1.4, 0.53, 0.0, 12, -30.0, 2.5, 1.1, 15, 0.020, "Volume climax absorption (RVOL >= 1.4, taker_buy >= 53%) after 1h dip."),
        (MAJORS_3_ASSETS, "LONG_ONLY", 0.22, 0.90, 1.3, 0.52, 0.15, 12, -35.0, 2.2, 1.0, 18, 0.020, "Major-asset (BTC/ETH/BNB) liquidity dip absorption with lower wick >= 15%."),
        (ALPHA_6_ASSETS, "SHORT_ONLY", 0.25, 0.92, 1.2, 0.0, 0.25, 12, 10000.0, 2.2, 1.1, 12, 0.015, "Short-only upper-wick liquidity exhaustion (upper_wick >= 25%, RVOL >= 1.2)."),
        (ALL_10_ASSETS, "LONG_ONLY", 0.20, 0.88, 1.8, 0.55, 0.0, 6, 10000.0, 2.5, 1.2, 18, 0.015, "Pure order-flow breakout surge (RVOL >= 1.8, taker_buy >= 55%)."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.23, 0.90, 1.0, 0.0, 0.22, 12, -45.0, 2.6, 1.2, 18, 0.022, "Hammer-wick absorption (lower_wick >= 22%) following 1h pullback (<= -45 bps)."),
        (CORE_4_ASSETS, "LONG_ONLY", 0.24, 0.88, 1.0, 0.49, 0.0, 12, -45.0, 2.5, 1.2, 15, 0.025, "High-frequency core 4-asset dip absorption (q >= 0.88, htf_12 <= -45 bps)."),
    ]
    for idx, s in enumerate(f1_specs, start=1):
        configs.append(
            StrategyConfiguration(
                strategy_id=f"STRAT_{idx:03d}",
                batch_id="batch_001",
                family=StrategyFamily.LIQUIDITY_MICROSTRUCTURE,
                hypothesis=s[13],
                applicable_assets=s[0],
                entry=EntryParameters(
                    direction_mode=s[1], prob_margin_min=s[2], vol_quantile_min=s[3],
                    rvol_min=s[4], taker_buy_ratio_min=s[5], wick_rejection_min=s[6],
                    htf_lookback_bars=s[7], htf_return_max_bps=s[8],
                ),
                exit=ExitParameters(tp1_multiplier=s[9], sl_multiplier=s[10], horizon_bars=s[11]),
                risk=RiskExecutionParameters(risk_per_trade_pct=s[12]),
            )
        )

    # =========================================================================
    # FAMILY 2: MARKET_REGIME_TRANSITIONS (15 candidates: STRAT_021 - STRAT_035)
    # =========================================================================
    f2_specs = [
        # (assets, dir_mode, pm, p0_max, vq, htf_lb, htf_min, htf_max, tp1, sl, h, hyp)
        (ALL_10_ASSETS, "HTF_TREND_ALIGNED", 0.22, 0.35, 0.90, 48, -9999.0, 9999.0, 2.5, 1.2, 24, "4h macro trend alignment (Long when 4h > 0, Short when 4h < 0) across 10 assets."),
        (ALPHA_6_ASSETS, "HTF_TREND_ALIGNED", 0.25, 0.32, 0.90, 48, -9999.0, 9999.0, 2.5, 1.2, 18, "4h trend alignment on 6 alpha altcoins with p0 <= 0.32 chop filter."),
        (ALL_10_ASSETS, "HTF_TREND_ALIGNED", 0.25, 0.35, 0.90, 24, -9999.0, 9999.0, 2.5, 1.2, 18, "2h regime alignment across 10 primary specialists."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.24, 0.30, 0.90, 48, 25.0, 9999.0, 2.8, 1.2, 24, "Confirmed 4h bull expansion regime (htf_48 >= +25 bps) Long continuation."),
        (ALPHA_6_ASSETS, "SHORT_ONLY", 0.25, 0.30, 0.92, 48, -9999.0, -50.0, 2.5, 1.2, 18, "Confirmed 4h bear breakdown regime (htf_48 <= -50 bps) Short continuation."),
        (ALL_10_ASSETS, "LONG_ONLY", 0.22, 0.28, 0.88, 24, -120.0, -20.0, 2.5, 1.2, 18, "2h pullback within low-chop regime (p0 <= 0.28, htf_24 in [-120, -20] bps)."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.25, 0.26, 0.90, 12, -200.0, -35.0, 2.6, 1.2, 18, "Strict low-neutrality regime (p0 <= 0.26) + 1h dip transition on 6 alpha assets."),
        (CORE_4_ASSETS, "LONG_ONLY", 0.24, 0.28, 0.90, 12, -250.0, -40.0, 2.5, 1.2, 15, "Core 4-asset regime transition after 1h pullback with p0 <= 0.28."),
        (HIGH_AUC_5_ASSETS, "HTF_TREND_ALIGNED", 0.26, 0.30, 0.92, 12, -9999.0, 9999.0, 2.5, 1.1, 18, "1h momentum regime alignment on Top-5 AUC specialists."),
        (MAJORS_3_ASSETS, "HTF_TREND_ALIGNED", 0.22, 0.35, 0.88, 48, -9999.0, 9999.0, 2.2, 1.0, 24, "Macro 4h trend alignment on BTC/ETH/BNB."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.22, 0.35, 0.85, 48, -150.0, -30.0, 2.5, 1.2, 24, "4h oversold regime mean-reversion transition on 6 alpha assets."),
        (ALL_10_ASSETS, "BOTH", 0.28, 0.24, 0.92, 24, -9999.0, 9999.0, 2.5, 1.2, 18, "Ultra-low chop regime filter (p0 <= 0.24) bidirectional execution."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.25, 0.30, 0.90, 6, -150.0, -25.0, 2.4, 1.2, 12, "30-minute micro-regime flush transition on 6 alpha assets."),
        (CORE_4_ASSETS, "LONG_ONLY", 0.26, 0.30, 0.91, 24, -200.0, -40.0, 2.8, 1.2, 18, "2h correction reclaim regime on DOGE/SOL/ADA/XRP."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.23, 0.32, 0.89, 12, -180.0, -45.0, 2.5, 1.2, 20, "Balanced 1h regime pullback ([-180, -45] bps) avoiding extreme crash knives."),
    ]
    for offset, s in enumerate(f2_specs, start=21):
        configs.append(
            StrategyConfiguration(
                strategy_id=f"STRAT_{offset:03d}",
                batch_id="batch_001",
                family=StrategyFamily.MARKET_REGIME_TRANSITIONS,
                hypothesis=s[11],
                applicable_assets=s[0],
                entry=EntryParameters(
                    direction_mode=s[1], prob_margin_min=s[2], p0_neutral_max=s[3],
                    vol_quantile_min=s[4], htf_lookback_bars=s[5],
                    htf_return_min_bps=s[6], htf_return_max_bps=s[7],
                ),
                exit=ExitParameters(tp1_multiplier=s[8], sl_multiplier=s[9], horizon_bars=s[10]),
                risk=RiskExecutionParameters(risk_per_trade_pct=0.020),
            )
        )

    # =========================================================================
    # FAMILY 3: DIRECTIONAL_PREDICTION (15 candidates: STRAT_036 - STRAT_050)
    # =========================================================================
    f3_specs = [
        # (assets, dir_mode, pm, p0_max, vq, tp1, sl, h, hyp)
        (ALL_10_ASSETS, "BOTH", 0.20, 0.40, 0.90, 2.5, 1.0, 24, "Baseline bidirectional OOF directional margin >= 0.20 across 10 assets."),
        (ALL_10_ASSETS, "BOTH", 0.30, 0.30, 0.92, 2.5, 1.0, 24, "High-conviction bidirectional margin >= 0.30 with p0 <= 0.30."),
        (ALL_10_ASSETS, "LONG_ONLY", 0.22, 0.35, 0.90, 2.5, 1.1, 24, "Fleet-wide Long-Only OOF directional conviction (margin >= 0.22)."),
        (ALL_10_ASSETS, "SHORT_ONLY", 0.25, 0.32, 0.92, 2.5, 1.1, 18, "Fleet-wide Short-Only OOF directional conviction (margin >= 0.25)."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.25, 0.30, 0.90, 2.5, 1.2, 18, "6-asset Alpha Fleet Long-Only with AURCC selective abstention (p0 <= 0.30)."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.30, 0.26, 0.92, 2.8, 1.2, 24, "6-asset Alpha Fleet extreme conviction (margin >= 0.30, p0 <= 0.26)."),
        (CORE_4_ASSETS, "LONG_ONLY", 0.26, 0.28, 0.90, 2.5, 1.2, 18, "Core 4-asset Long-Only high-conviction specialist selection."),
        (HIGH_AUC_5_ASSETS, "LONG_ONLY", 0.25, 0.28, 0.90, 2.5, 1.1, 18, "Top-5 ROC-AUC specialists (LINK/LTC/DOGE/BNB/ADA) Long-Only."),
        (("LINKUSDT", "AVAXUSDT", "DOGEUSDT"), "LONG_ONLY", 0.24, 0.30, 0.90, 2.5, 1.2, 24, "Stage-2 proven positive net-expectancy trio (LINK/AVAX/DOGE) Long-Only."),
        (("LINKUSDT", "DOGEUSDT", "SOLUSDT", "ADAUSDT"), "LONG_ONLY", 0.25, 0.28, 0.91, 2.6, 1.2, 18, "4-asset high-selectivity specialist quartet Long-Only."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.18, 0.25, 0.90, 2.4, 1.2, 18, "AURCC-driven low-p0 abstention gate (p0 <= 0.25) with moderate margin >= 0.18."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.32, 0.24, 0.93, 3.0, 1.3, 24, "Tail-conviction OOF sniper (margin >= 0.32, p0 <= 0.24, q >= 0.93)."),
        (MAJORS_3_ASSETS, "SHORT_ONLY", 0.24, 0.32, 0.90, 2.2, 1.1, 18, "Major-asset (BTC/ETH/BNB) Short-Only directional specialist."),
        (("LINKUSDT", "LTCUSDT"), "LONG_ONLY", 0.22, 0.26, 0.90, 2.5, 1.2, 18, "Top-2 AURCC selective abstention specialists (LINK & LTC) Long-Only."),
        (ALPHA_6_ASSETS, "BOTH", 0.28, 0.25, 0.92, 2.2, 1.3, 12, "Short-horizon (60m) high-conviction bidirectional 6-asset specialist."),
    ]
    for offset, s in enumerate(f3_specs, start=36):
        configs.append(
            StrategyConfiguration(
                strategy_id=f"STRAT_{offset:03d}",
                batch_id="batch_001",
                family=StrategyFamily.DIRECTIONAL_PREDICTION,
                hypothesis=s[8],
                applicable_assets=s[0],
                entry=EntryParameters(
                    direction_mode=s[1], prob_margin_min=s[2],
                    p0_neutral_max=s[3], vol_quantile_min=s[4],
                ),
                exit=ExitParameters(tp1_multiplier=s[5], sl_multiplier=s[6], horizon_bars=s[7]),
                risk=RiskExecutionParameters(risk_per_trade_pct=0.018),
            )
        )

    # =========================================================================
    # FAMILY 4: VOLATILITY_DYNAMICS (15 candidates: STRAT_051 - STRAT_065)
    # =========================================================================
    f4_specs = [
        # (assets, dir_mode, pm, vq_min, vq_max, v_exp_min, htf_max, tp1, sl, h, hyp)
        (ALL_10_ASSETS, "LONG_ONLY", 0.22, 0.85, 0.96, 1.25, 10000.0, 2.5, 1.2, 18, "Volatility expansion breakout (sigma_20/sigma_96 >= 1.25) capped at q<=0.96."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.24, 0.88, 0.98, 1.30, -35.0, 2.6, 1.2, 18, "Volatility expansion (ratio >= 1.30) during 1h pullback (<= -35 bps)."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.25, 0.90, 0.97, 1.15, -45.0, 2.5, 1.2, 18, "Capped tail volatility (q in [0.90, 0.97]) avoiding extreme 99th-percentile blowoffs."),
        (CORE_4_ASSETS, "LONG_ONLY", 0.25, 0.91, 0.98, 1.20, -50.0, 2.8, 1.2, 18, "Core 4-asset volatility expansion + 1h dip absorption."),
        (ALL_10_ASSETS, "LONG_ONLY", 0.24, 0.94, 1.00, 1.40, 10000.0, 3.0, 1.3, 24, "Extreme volatility surge (q >= 0.94, expansion >= 1.40) wide barrier (3.0s/1.3s)."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.22, 0.80, 0.92, 1.10, -40.0, 2.2, 1.1, 15, "Mid-volatility regime (q in [0.80, 0.92]) dip absorption."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.25, 0.92, 1.00, 1.00, -55.0, 3.2, 1.4, 24, "High-sigma wide stop (1.4s SL, 3.2s TP) to survive intrabar volatility noise."),
        (CORE_4_ASSETS, "LONG_ONLY", 0.25, 0.90, 0.99, 1.10, -50.0, 2.4, 1.3, 12, "Fast 60-minute volatility snapback (2.4s TP, 1.3s SL, 12 bars)."),
        (HIGH_AUC_5_ASSETS, "LONG_ONLY", 0.24, 0.90, 0.98, 1.20, -40.0, 2.5, 1.2, 18, "Top-5 AUC volatility expansion reclaim."),
        (ALPHA_6_ASSETS, "BOTH", 0.26, 0.92, 0.98, 1.35, 10000.0, 2.5, 1.2, 18, "Bidirectional volatility regime expansion (sigma_20/sigma_96 >= 1.35)."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.25, 0.93, 1.00, 1.25, -60.0, 2.6, 1.2, 15, "93rd-percentile volatility flush climax reclaim."),
        (ALL_10_ASSETS, "LONG_ONLY", 0.23, 0.88, 0.96, 1.15, -45.0, 2.5, 1.2, 18, "10-asset volatility band [0.88, 0.96] pullback reclaim."),
        (CORE_4_ASSETS, "LONG_ONLY", 0.26, 0.92, 0.99, 1.15, -50.0, 3.5, 1.3, 30, "Extended 150m horizon (30 bars) for large 3.5-sigma volatility expansions."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.24, 0.89, 0.97, 1.05, -45.0, 2.3, 1.2, 16, "Moderate volatility expansion with tight 80m time stop."),
        (MAJORS_3_ASSETS, "LONG_ONLY", 0.23, 0.92, 0.99, 1.30, -30.0, 2.4, 1.1, 18, "BTC/ETH/BNB volatility expansion pullback."),
    ]
    for offset, s in enumerate(f4_specs, start=51):
        configs.append(
            StrategyConfiguration(
                strategy_id=f"STRAT_{offset:03d}",
                batch_id="batch_001",
                family=StrategyFamily.VOLATILITY_DYNAMICS,
                hypothesis=s[10],
                applicable_assets=s[0],
                entry=EntryParameters(
                    direction_mode=s[1], prob_margin_min=s[2],
                    vol_quantile_min=s[3], vol_quantile_max=s[4],
                    vol_expansion_ratio_min=s[5], htf_return_max_bps=s[6],
                ),
                exit=ExitParameters(tp1_multiplier=s[7], sl_multiplier=s[8], horizon_bars=s[9]),
                risk=RiskExecutionParameters(risk_per_trade_pct=0.020),
            )
        )

    # =========================================================================
    # FAMILY 5: CROSS_ASSET_RELATIONSHIPS (15 candidates: STRAT_066 - STRAT_080)
    # =========================================================================
    f5_specs = [
        # (assets, dir_mode, pm, vq, btc_lb, btc_min, btc_max, htf_max, tp1, sl, h, hyp)
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.24, 0.90, 6, 20.0, 9999.0, 10000.0, 2.5, 1.2, 18, "BTC 30m positive impulse lead (btc_ret_6 >= +20 bps) driving altcoin beta."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.24, 0.90, 12, 35.0, 9999.0, 10000.0, 2.5, 1.2, 18, "BTC 1h breakout lead (btc_ret_12 >= +35 bps) altcoin continuation."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.25, 0.90, 12, -9999.0, -30.0, -45.0, 2.6, 1.2, 18, "Synchronized BTC + Altcoin 1h liquidity flush (btc <= -30 bps, alt <= -45 bps) snapback."),
        (CORE_4_ASSETS, "LONG_ONLY", 0.25, 0.90, 12, -9999.0, -25.0, -50.0, 2.6, 1.2, 15, "Core 4-asset synchronized BTC dip reclaim (btc <= -25 bps, alt <= -50 bps)."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.24, 0.90, 6, -15.0, 60.0, -45.0, 2.5, 1.2, 18, "Altcoin idiosyncratic dip (alt <= -45 bps) while BTC is stable (btc_6 in [-15, +60] bps)."),
        (CORE_4_ASSETS, "LONG_ONLY", 0.25, 0.90, 6, -20.0, 80.0, -50.0, 2.7, 1.2, 18, "Core 4-asset idiosyncratic flush while BTC holds support (btc_6 >= -20 bps)."),
        (ALL_10_ASSETS, "LONG_ONLY", 0.24, 0.90, 12, -9999.0, -20.0, -40.0, 2.5, 1.2, 18, "10-asset market-wide correlated 1h flush reversal."),
        (ALPHA_6_ASSETS, "SHORT_ONLY", 0.25, 0.92, 6, -9999.0, -30.0, 10000.0, 2.4, 1.2, 15, "BTC 30m breakdown lead (btc_6 <= -30 bps) triggering altcoin short cascade."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.25, 0.91, 3, 10.0, 9999.0, -40.0, 2.6, 1.2, 18, "Altcoin 1h dip (<= -40 bps) with immediate 15m BTC bounce confirmation (btc_3 >= +10 bps)."),
        (CORE_4_ASSETS, "LONG_ONLY", 0.25, 0.90, 3, 5.0, 9999.0, -45.0, 2.6, 1.2, 16, "Core 4-asset 1h dip with 15m BTC uptick confirmation (btc_3 >= +5 bps)."),
        (HIGH_AUC_5_ASSETS, "LONG_ONLY", 0.24, 0.90, 12, -9999.0, -25.0, -45.0, 2.5, 1.2, 18, "Top-5 AUC specialists correlated BTC/altcoin 1h flush reclaim."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.25, 0.90, 24, -9999.0, -40.0, -60.0, 2.8, 1.3, 24, "2-hour macro BTC + Altcoin washout reversal."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.23, 0.89, 12, -120.0, 20.0, -45.0, 2.5, 1.2, 18, "Bounded BTC regime ([-120, +20] bps) with altcoin 1h pullback."),
        (("SOLUSDT", "DOGEUSDT", "AVAXUSDT"), "LONG_ONLY", 0.25, 0.90, 12, -9999.0, -20.0, -50.0, 2.7, 1.2, 18, "High-beta trio (SOL/DOGE/AVAX) BTC-synchronized flush rebound."),
        (("XRPUSDT", "ADAUSDT", "LINKUSDT"), "LONG_ONLY", 0.25, 0.90, 12, -9999.0, -20.0, -45.0, 2.6, 1.2, 18, "Large-cap alt trio (XRP/ADA/LINK) BTC-synchronized flush rebound."),
    ]
    for offset, s in enumerate(f5_specs, start=66):
        configs.append(
            StrategyConfiguration(
                strategy_id=f"STRAT_{offset:03d}",
                batch_id="batch_001",
                family=StrategyFamily.CROSS_ASSET_RELATIONSHIPS,
                hypothesis=s[11],
                applicable_assets=s[0],
                entry=EntryParameters(
                    direction_mode=s[1], prob_margin_min=s[2], vol_quantile_min=s[3],
                    btc_lead_lookback_bars=s[4], btc_lead_min_bps=s[5],
                    btc_lead_max_bps=s[6], htf_return_max_bps=s[7],
                ),
                exit=ExitParameters(tp1_multiplier=s[8], sl_multiplier=s[9], horizon_bars=s[10]),
                risk=RiskExecutionParameters(risk_per_trade_pct=0.020),
            )
        )

    # =========================================================================
    # FAMILY 6: MEAN_REVERSION_BREAKOUT (10 candidates: STRAT_081 - STRAT_090)
    # =========================================================================
    f6_specs = [
        # (assets, dir_mode, pm, vq, htf_lb, htf_min, htf_max, wick, tp1, sl, h, hyp)
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.25, 0.90, 12, 40.0, 9999.0, 0.0, 2.5, 1.2, 18, "1h momentum breakout continuation (htf_ret_12 >= +40 bps) Long."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.25, 0.92, 12, -9999.0, -70.0, 0.0, 2.6, 1.2, 18, "Deep 1h oversold mean-reversion (htf_ret_12 <= -70 bps) Long."),
        (CORE_4_ASSETS, "LONG_ONLY", 0.24, 0.90, 12, -9999.0, -60.0, 0.0, 2.6, 1.2, 16, "Core 4-asset 1h oversold mean-reversion (htf_ret_12 <= -60 bps)."),
        (ALPHA_6_ASSETS, "SHORT_ONLY", 0.25, 0.92, 12, 60.0, 9999.0, 0.25, 2.4, 1.2, 12, "Overextended 1h rally exhaustion fade Short (htf_12 >= +60 bps + upper wick >= 25%)."),
        (("LINKUSDT", "ADAUSDT", "AVAXUSDT", "LTCUSDT"), "SHORT_ONLY", 0.25, 0.92, 12, 50.0, 9999.0, 0.25, 2.4, 1.2, 12, "Exhaustion fade Short on LINK/ADA/AVAX/LTC after >= +50 bps 1h spike with upper wick."),
        (ALL_10_ASSETS, "LONG_ONLY", 0.25, 0.91, 24, -9999.0, -90.0, 0.10, 2.8, 1.3, 24, "2h deep mean-reversion capitulation bounce (htf_24 <= -90 bps) across 10 assets."),
        (ALPHA_6_ASSETS, "LONG_ONLY", 0.26, 0.90, 6, -9999.0, -45.0, 0.12, 2.4, 1.2, 12, "30m sharp V-bottom mean reversion (htf_6 <= -45 bps + lower wick >= 12%)."),
        (CORE_4_ASSETS, "LONG_ONLY", 0.23, 0.89, 12, -9999.0, -40.0, 0.0, 2.8, 1.3, 20, "Core 4-asset broader mean-reversion capture (htf_12 <= -40 bps, 2.8s TP)."),
        (ALPHA_6_ASSETS, "ABSORPTION_REVERSAL", 0.25, 0.91, 12, -9999.0, -55.0, 0.20, 2.5, 1.2, 16, "Combined Long flush bounce (<= -55 bps) + Short exhaustion fade (>= +82 bps + wick)."),
        (ALL_10_ASSETS, "LONG_ONLY", 0.24, 0.90, 12, -9999.0, -55.0, 0.0, 2.6, 1.2, 18, "10-asset universal 1h mean-reversion reclaim (htf_12 <= -55 bps)."),
    ]
    for offset, s in enumerate(f6_specs, start=81):
        configs.append(
            StrategyConfiguration(
                strategy_id=f"STRAT_{offset:03d}",
                batch_id="batch_001",
                family=StrategyFamily.MEAN_REVERSION_BREAKOUT,
                hypothesis=s[11],
                applicable_assets=s[0],
                entry=EntryParameters(
                    direction_mode=s[1], prob_margin_min=s[2], vol_quantile_min=s[3],
                    htf_lookback_bars=s[4], htf_return_min_bps=s[5],
                    htf_return_max_bps=s[6], wick_rejection_min=s[7],
                ),
                exit=ExitParameters(tp1_multiplier=s[8], sl_multiplier=s[9], horizon_bars=s[10]),
                risk=RiskExecutionParameters(risk_per_trade_pct=0.020),
            )
        )

    # =========================================================================
    # FAMILY 7: ADAPTIVE_ENTRY_EXECUTION (10 candidates: STRAT_091 - STRAT_100)
    # =========================================================================
    f7_specs = [
        # (assets, pm, vq, htf_max, ord_type, lim_off, tp1, tp2, tp1_pct, sl, be_ratchet, trail, h, fee_tier, hyp)
        (ALPHA_6_ASSETS, 0.25, 0.90, -50.0, "MARKET", 0.0, 1.6, 3.2, 0.50, 1.2, True, 0.0, 18, "maker_passive", "Banker Option A: 50% close at 1.6s TP1 + breakeven ratchet + 50% runner to 3.2s TP2."),
        (CORE_4_ASSETS, 0.25, 0.90, -50.0, "MARKET", 0.0, 1.5, 3.5, 0.50, 1.2, True, 0.0, 18, "maker_passive", "Core 4-asset Banker Option A (1.5s TP1 / 3.5s TP2 + breakeven ratchet)."),
        (ALPHA_6_ASSETS, 0.24, 0.90, -45.0, "MARKET", 0.0, 1.8, 3.6, 0.50, 1.3, True, 0.9, 20, "maker_passive", "Banker Option A + dynamic 0.9-sigma trailing stop on runner."),
        (CORE_4_ASSETS, 0.24, 0.90, -45.0, "MARKET", 0.0, 1.8, 3.8, 0.40, 1.3, True, 0.0, 20, "maker_passive", "40% TP1 scale-out + 60% runner to 3.8s TP2 on Core 4 assets."),
        (ALPHA_6_ASSETS, 0.25, 0.90, -50.0, "LIMIT", 0.08, 2.5, 3.5, 0.0, 1.2, False, 0.0, 18, "maker_passive", "Passive limit entry at 0.08-sigma pullback discount after 1h dip."),
        (ALPHA_6_ASSETS, 0.25, 0.90, -50.0, "LIMIT", 0.18, 2.5, 3.5, 0.0, 1.2, False, 0.0, 18, "maker_passive", "Deep passive limit entry at 0.18-sigma discount (tests adverse selection)."),
        (ALPHA_6_ASSETS, 0.25, 0.91, -55.0, "MARKET", 0.0, 2.6, 3.8, 0.0, 1.2, False, 0.0, 18, "hybrid_tier", "Hybrid Fee Tier (15 bps RT) resilience test on 6-asset 1h dip reclaim."),
        (CORE_4_ASSETS, 0.26, 0.92, -60.0, "MARKET", 0.0, 2.8, 4.0, 0.0, 1.3, False, 0.0, 18, "hybrid_tier", "Hybrid Fee Tier (15 bps RT) high-conviction Core 4-asset reclaim."),
        (CORE_4_ASSETS, 0.28, 0.93, -65.0, "MARKET", 0.0, 3.2, 4.5, 0.0, 1.4, False, 0.0, 24, "baseline_taker", "Baseline Taker Fee Tier (44 bps RT) stress test on ultra-deep 1h flushes."),
        (ALL_10_ASSETS, 0.25, 0.90, -50.0, "MARKET", 0.0, 1.6, 3.2, 0.50, 1.2, True, 0.0, 18, "maker_passive", "10-asset Fleet Banker Option A partial exit + breakeven ratchet."),
    ]
    for offset, s in enumerate(f7_specs, start=91):
        configs.append(
            StrategyConfiguration(
                strategy_id=f"STRAT_{offset:03d}",
                batch_id="batch_001",
                family=StrategyFamily.ADAPTIVE_ENTRY_EXECUTION,
                hypothesis=s[14],
                applicable_assets=s[0],
                entry=EntryParameters(
                    direction_mode="LONG_ONLY", prob_margin_min=s[1],
                    vol_quantile_min=s[2], htf_return_max_bps=s[3],
                    order_type=s[4], limit_offset_sigma=s[5],
                ),
                exit=ExitParameters(
                    tp1_multiplier=s[6], tp2_multiplier=s[7], tp1_close_pct=s[8],
                    sl_multiplier=s[9], breakeven_ratchet_on_tp1=s[10],
                    trailing_stop_distance_sigma=s[11], horizon_bars=s[12],
                ),
                risk=RiskExecutionParameters(risk_per_trade_pct=0.022, fee_tier=s[13]),
            )
        )

    return configs


def generate_batch_002(best_batch_1_id: str) -> List[StrategyConfiguration]:
    """Generates Batch 002 (STRAT_101 to STRAT_200): 60 Exploitation + 40 Exploration candidates."""
    configs: List[StrategyConfiguration] = []

    # 1. EXPLOITATION (60 candidates: STRAT_101 - STRAT_160)
    # Systematically explores the high-alpha liquidity-flush absorption + AURCC abstention space
    asset_pools = [
        CORE_4_ASSETS,
        ALPHA_6_ASSETS,
        ("DOGEUSDT", "SOLUSDT", "ADAUSDT", "XRPUSDT", "LINKUSDT"),
        ("DOGEUSDT", "SOLUSDT", "ADAUSDT", "XRPUSDT", "AVAXUSDT"),
        ("DOGEUSDT", "SOLUSDT", "ADAUSDT"),
    ]
    htf_thresholds = [-55.0, -65.0, -75.0, -85.0]
    margins = [0.22, 0.25, 0.28]

    idx = 101
    for ap_idx, assets in enumerate(asset_pools):
        for htf_th in htf_thresholds:
            for pm in margins:
                vq = 0.90 + 0.01 * (ap_idx % 4)
                p0_max = 0.30 if pm >= 0.25 else 0.27
                tp1 = 2.6 + 0.2 * (idx % 3)
                sl = 1.15 + 0.05 * (idx % 2)
                h = 16 + 2 * (idx % 3)
                r_pct = 0.020 + 0.002 * (idx % 3)
                configs.append(
                    StrategyConfiguration(
                        strategy_id=f"STRAT_{idx:03d}",
                        batch_id="batch_002",
                        family=StrategyFamily.LIQUIDITY_MICROSTRUCTURE,
                        parent_strategy_id=best_batch_1_id,
                        hypothesis=(
                            f"Batch 2 Exploitation ({best_batch_1_id} refinement): {len(assets)}-asset pool, "
                            f"1h flush <= {htf_th} bps, margin >= {pm}, p0 <= {p0_max}, TP={tp1:.1f}s, SL={sl:.2f}s."
                        ),
                        applicable_assets=assets,
                        entry=EntryParameters(
                            direction_mode="LONG_ONLY",
                            prob_margin_min=pm,
                            p0_neutral_max=p0_max,
                            vol_quantile_min=round(vq, 2),
                            htf_lookback_bars=12,
                            htf_return_max_bps=htf_th,
                        ),
                        exit=ExitParameters(
                            tp1_multiplier=round(tp1, 2),
                            sl_multiplier=round(sl, 2),
                            horizon_bars=h,
                        ),
                        risk=RiskExecutionParameters(
                            risk_per_trade_pct=round(r_pct, 4),
                            max_symbol_exposure_pct=0.40,
                            max_total_exposure_pct=1.10,
                            max_leverage=2.0,
                            max_concurrent_positions=4,
                        ),
                    )
                )
                idx += 1

    # 2. EXPLORATION (40 candidates: STRAT_161 - STRAT_200)
    # Explores Banker Option A partial ratchets + Cross-Asset BTC shock filters + Volatility ratios
    for k in range(40):
        s_id = f"STRAT_{161 + k:03d}"
        if k < 15:
            # Banker Option A partial close variations on flush absorption
            tp1_m = round(1.4 + 0.15 * (k % 5), 2)
            tp2_m = round(3.0 + 0.25 * (k % 5), 2)
            close_pct = round(0.35 + 0.10 * (k % 3), 2)
            htf_max = -45.0 - 5.0 * (k % 4)
            configs.append(
                StrategyConfiguration(
                    strategy_id=s_id,
                    batch_id="batch_002",
                    family=StrategyFamily.ADAPTIVE_ENTRY_EXECUTION,
                    parent_strategy_id=best_batch_1_id,
                    hypothesis=f"Batch 2 Exploration: Banker Option A ({close_pct*100:.0f}% at {tp1_m}s, runner to {tp2_m}s) on 1h flush <= {htf_max} bps.",
                    applicable_assets=CORE_4_ASSETS if k % 2 == 0 else ALPHA_6_ASSETS,
                    entry=EntryParameters(
                        direction_mode="LONG_ONLY",
                        prob_margin_min=0.24,
                        p0_neutral_max=0.30,
                        vol_quantile_min=0.89,
                        htf_lookback_bars=12,
                        htf_return_max_bps=htf_max,
                    ),
                    exit=ExitParameters(
                        tp1_multiplier=tp1_m,
                        tp2_multiplier=tp2_m,
                        tp1_close_pct=close_pct,
                        sl_multiplier=1.25,
                        breakeven_ratchet_on_tp1=True,
                        horizon_bars=18 + (k % 3) * 3,
                    ),
                    risk=RiskExecutionParameters(
                        risk_per_trade_pct=0.025,
                        max_symbol_exposure_pct=0.45,
                        max_total_exposure_pct=1.20,
                    ),
                )
            )
        elif k < 30:
            # Cross-Asset BTC shock + Altcoin absorption
            btc_max = -15.0 - 5.0 * (k % 5)
            htf_max = -40.0 - 5.0 * (k % 3)
            configs.append(
                StrategyConfiguration(
                    strategy_id=s_id,
                    batch_id="batch_002",
                    family=StrategyFamily.CROSS_ASSET_RELATIONSHIPS,
                    parent_strategy_id=best_batch_1_id,
                    hypothesis=f"Batch 2 Exploration: Synchronized BTC 1h dip (<= {btc_max} bps) + Altcoin flush (<= {htf_max} bps).",
                    applicable_assets=ALPHA_6_ASSETS if k % 2 == 0 else CORE_4_ASSETS,
                    entry=EntryParameters(
                        direction_mode="LONG_ONLY",
                        prob_margin_min=0.23 + 0.01 * (k % 3),
                        p0_neutral_max=0.30,
                        vol_quantile_min=0.89,
                        htf_lookback_bars=12,
                        htf_return_max_bps=htf_max,
                        btc_lead_lookback_bars=12,
                        btc_lead_max_bps=btc_max,
                    ),
                    exit=ExitParameters(
                        tp1_multiplier=2.7,
                        sl_multiplier=1.25,
                        horizon_bars=16 + (k % 3) * 2,
                    ),
                    risk=RiskExecutionParameters(
                        risk_per_trade_pct=0.024,
                        max_symbol_exposure_pct=0.45,
                        max_total_exposure_pct=1.20,
                    ),
                )
            )
        else:
            # Bidirectional Absorption + Exhaustion Short combinations
            htf_max = -45.0 - 5.0 * (k % 5)
            wick_m = round(0.05 + 0.03 * (k % 4), 2)
            configs.append(
                StrategyConfiguration(
                    strategy_id=s_id,
                    batch_id="batch_002",
                    family=StrategyFamily.MEAN_REVERSION_BREAKOUT,
                    parent_strategy_id=best_batch_1_id,
                    hypothesis=f"Batch 2 Exploration: Bidirectional absorption + upper-wick exhaustion short (htf <= {htf_max} bps, wick >= {wick_m}).",
                    applicable_assets=ALPHA_6_ASSETS,
                    entry=EntryParameters(
                        direction_mode="ABSORPTION_REVERSAL",
                        prob_margin_min=0.25,
                        p0_neutral_max=0.29,
                        vol_quantile_min=0.90,
                        wick_rejection_min=wick_m,
                        htf_lookback_bars=12,
                        htf_return_max_bps=htf_max,
                    ),
                    exit=ExitParameters(
                        tp1_multiplier=2.6 + 0.1 * (k % 3),
                        sl_multiplier=1.2,
                        horizon_bars=16,
                    ),
                    risk=RiskExecutionParameters(
                        risk_per_trade_pct=0.024,
                        max_symbol_exposure_pct=0.45,
                        max_total_exposure_pct=1.20,
                    ),
                )
            )

    return configs


def generate_batch_003(best_batch_2: StrategyConfiguration) -> List[StrategyConfiguration]:
    """Generates Batch 003 (STRAT_201 to STRAT_300): Fine-grained local neighborhood & plateau verification."""
    configs: List[StrategyConfiguration] = []
    base_e = best_batch_2.entry
    base_x = best_batch_2.exit
    base_r = best_batch_2.risk

    # Grid of fine perturbations around best_batch_2 to map the local response surface & plateau
    pm_deltas = [-0.02, -0.01, 0.0, 0.01, 0.02]
    htf_deltas = [-8.0, -4.0, 0.0, 4.0, 8.0]
    tp_deltas = [-0.2, 0.0, 0.2, 0.4]

    idx = 201
    for d_pm in pm_deltas:
        for d_htf in htf_deltas:
            for d_tp in tp_deltas:
                pm = round(min(0.45, max(0.15, base_e.prob_margin_min + d_pm)), 3)
                htf_max = round(base_e.htf_return_max_bps + d_htf, 1)
                tp1 = round(max(1.5, base_x.tp1_multiplier + d_tp), 2)
                sl = round(base_x.sl_multiplier + (0.05 if idx % 3 == 0 else (-0.05 if idx % 3 == 1 else 0.0)), 2)
                h = max(8, base_x.horizon_bars + ((idx % 5) - 2))
                r_pct = round(min(0.030, max(0.015, base_r.risk_per_trade_pct + 0.001 * ((idx % 5) - 2))), 4)
                sym_cap = round(min(0.60, max(0.30, base_r.max_symbol_exposure_pct + 0.03 * ((idx % 3) - 1))), 2)
                tot_cap = round(min(1.50, max(0.80, base_r.max_total_exposure_pct + 0.10 * ((idx % 3) - 1))), 2)

                configs.append(
                    StrategyConfiguration(
                        strategy_id=f"STRAT_{idx:03d}",
                        batch_id="batch_003",
                        family=best_batch_2.family,
                        parent_strategy_id=best_batch_2.strategy_id,
                        hypothesis=(
                            f"Batch 3 Local Surface Refinement of {best_batch_2.strategy_id}: "
                            f"margin={pm}, htf_max={htf_max} bps, TP={tp1}s, SL={sl}s, H={h}b, risk={r_pct*100:.2f}%."
                        ),
                        applicable_assets=best_batch_2.applicable_assets,
                        entry=base_e.model_copy(
                            update={
                                "prob_margin_min": pm,
                                "htf_return_max_bps": htf_max,
                            }
                        ),
                        exit=base_x.model_copy(
                            update={
                                "tp1_multiplier": tp1,
                                "sl_multiplier": sl,
                                "horizon_bars": h,
                            }
                        ),
                        risk=base_r.model_copy(
                            update={
                                "risk_per_trade_pct": r_pct,
                                "max_symbol_exposure_pct": sym_cap,
                                "max_total_exposure_pct": tot_cap,
                            }
                        ),
                    )
                )
                idx += 1

    return configs
