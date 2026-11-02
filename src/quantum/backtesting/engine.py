"""Causal Discrete-Event Backtest Runner for Track 2 Economic Evaluation.

Implements causal event loop stepping candle-by-candle:
1. Signal evaluation at candle i-1 close (t_i) based on frozen OOF predictions and causal volatility.
2. Explicit Risk Evaluation Mode separation (Mode 1 Mechanical Benchmark, Mode 2 Risk-Filtered, Mode 3 Portfolio Ledger).
3. Execution fill simulation at candle i open (P_entry,ref = open[i], effective fill includes half-spread slippage).
4. BankerAgent FSM lifecycle integration for position tracking (PENDING_OPEN -> OPEN -> PARTIALLY_CLOSED -> CLOSED).
5. Opening gap detection and intrabar barrier breach monitoring over a strictly enforced 12-bar holding horizon (bars i .. i+11).
6. Deterministic conservative collision handling for intrabar same-bar double touches.
7. Discrete perpetual funding cash flow settlement, end-of-dataset open-position mark-to-market accounting,
   and exact two-legged PnL accounting.
"""

from enum import Enum
import math
from typing import Dict, List, Optional, Sequence
import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator

from quantum.agents.banker import BankerAgent
from quantum.agents.contracts import (
    PositionExecutionEvent,
    RiskInput,
    TrackedPosition,
)
from quantum.agents.risk import RiskAgent
from quantum.backtesting.accounting import (
    HISTORICAL_FUNDING_STATUS,
    OpenPositionAccountingResult,
    TradeAccountingResult,
    calculate_funding_cash_flow,
    compute_open_position_accounting,
    compute_two_legged_pnl,
)
from quantum.backtesting.adapters import OOFSignal
from quantum.config.settings import RiskConfig
from quantum.domain.enums import (
    AgentAction,
    CandidateCategory,
    ExchangeId,
    ExecutionEventType,
    MarketRegime,
    OrderType,
    PositionLifecycleState,
    TradeSide,
)
from quantum.domain.models import MarketContext, ScannerCandidate, TradeProposal


TRACK_2_GOVERNANCE_CLASSIFICATION: str = (
    "ELIGIBLE_FOR_EXPLORATORY_ECONOMIC_EVALUATION_SUBJECT_TO_GOVERNANCE_APPROVAL"
)


class RiskEvaluationMode(str, Enum):
    """Explicit separation of risk evaluation modes for Phase 5.5."""
    MODE_1_BARRIER_ACCOUNTING_BENCHMARK = "MODE_1_BARRIER_ACCOUNTING_BENCHMARK"
    MODE_2_RISK_FILTERED_EXECUTION_SIMULATION = "MODE_2_RISK_FILTERED_EXECUTION_SIMULATION"
    MODE_3_PORTFOLIO_LEVEL_RISK_SIMULATION = "MODE_3_PORTFOLIO_LEVEL_RISK_SIMULATION"


class GovernancePendingError(RuntimeError):
    """Raised when an operation requires an unresolved human governance decision."""
    pass


class BacktestConfig(BaseModel):
    """Configuration for discrete-event backtest simulation."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    symbol: str = "BTCUSDT"
    exchange: ExchangeId = ExchangeId.ASTER
    directional_mode: str = Field(default="LONG_ONLY", description="LONG_ONLY, SHORT_ONLY, or BIDIRECTIONAL")
    horizon_bars: int = Field(default=12, gt=0, description="Target holding horizon in bars (default: 12 bars = 60m)")
    timeframe_ms: int = Field(default=300_000, gt=0, description="Candle duration in ms (default: 300,000 for 5m)")
    barrier_multiplier: float = Field(default=1.5, gt=0.0, description="Symmetric barrier multiplier applied to sigma_t")
    volatility_lookback: int = Field(default=20, gt=1, description="Lookback window for causal return volatility")
    min_volatility: float = Field(default=1e-4, ge=0.0, description="Minimum volatility floor (default: 10 bps = 1e-4)")
    fee_rate_bps: float = Field(default=15.0, ge=0.0, description="Taker fee in bps per leg")
    slippage_bps: float = Field(default=2.0, ge=0.0, description="Half-spread execution slippage in bps per leg")
    funding_rate_bps_per_settlement: float = Field(default=1.0, description="Parametric funding rate in bps per 8h")
    prob_threshold: float = Field(default=0.50, ge=0.0, le=1.0, description="Raw model probability threshold")
    collision_policy: str = Field(default="CONSERVATIVE_SL_FIRST", description="CONSERVATIVE_SL_FIRST or OPTIMISTIC_TP_FIRST")
    initial_equity_usdt: float = Field(default=10_000.0, gt=0.0, description="Starting account equity in USDT")
    trade_notional_usdt: float = Field(default=1000.0, gt=0.0, description="Fixed notional sizing per trade")
    leverage: float = Field(default=1.0, gt=0.0, description="Position leverage")
    risk_evaluation_mode: RiskEvaluationMode = Field(
        default=RiskEvaluationMode.MODE_1_BARRIER_ACCOUNTING_BENCHMARK,
        description="Explicit evaluation mode (Mode 1, Mode 2, or Mode 3)",
    )
    enable_risk_agent: bool = Field(
        default=False,
        description="Legacy flag; if True, promotes mode to MODE_2_RISK_FILTERED_EXECUTION_SIMULATION",
    )
    enable_banker_agent: bool = Field(default=False, description="Enable BankerAgent FSM lifecycle updates")
    strict_candle_continuity: bool = Field(
        default=False,
        description="If True, raises ValueError on missing 5m candle gaps; if False, rejects gapped entries and flags gaps",
    )
    allow_bounded_mode3_preview: bool = Field(
        default=False,
        description="If True, allows single-asset Mode 3 ledger simulation tagged as DEC_05_PENDING",
    )
    proposal_estimated_rr_override: Optional[float] = Field(
        default=None,
        description="Optional override for TradeProposal estimated_reward_risk in Mode 2/3 testing",
    )

    @model_validator(mode="after")
    def _reconcile_risk_mode(self) -> "BacktestConfig":
        if (
            self.enable_risk_agent
            and self.risk_evaluation_mode == RiskEvaluationMode.MODE_1_BARRIER_ACCOUNTING_BENCHMARK
        ):
            object.__setattr__(
                self,
                "risk_evaluation_mode",
                RiskEvaluationMode.MODE_2_RISK_FILTERED_EXECUTION_SIMULATION,
            )
        elif self.risk_evaluation_mode in (
            RiskEvaluationMode.MODE_2_RISK_FILTERED_EXECUTION_SIMULATION,
            RiskEvaluationMode.MODE_3_PORTFOLIO_LEVEL_RISK_SIMULATION,
        ):
            object.__setattr__(self, "enable_risk_agent", True)
        return self


class BacktestTrade(BaseModel):
    """Complete record of an executed backtest trade."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    trade_id: str
    symbol: str
    side: TradeSide
    entry_signal_time_ms: int
    entry_fill_time_ms: int
    exit_time_ms: int
    entry_price: float = Field(description="Entry reference price (open[i+1])")
    exit_price: float = Field(description="Exit reference price (barrier, gap open, or close[i+12])")
    entry_fill_price_effective: float = Field(description="Effective entry fill price after half-spread slippage")
    exit_fill_price_effective: float = Field(description="Effective exit fill price after half-spread slippage")
    exit_reason: str = Field(description="TAKE_PROFIT, STOP_LOSS, or TIME_EXPIRATION")
    is_gap_exit: bool = Field(default=False, description="True if exit triggered on candle opening gap beyond barrier")
    upper_barrier: float
    lower_barrier: float
    volatility_sigma: float
    holding_bars: int
    accounting: TradeAccountingResult
    final_position_state: Optional[PositionLifecycleState] = None
    tracked_position: Optional[TrackedPosition] = None


class OpenPositionSnapshot(BaseModel):
    """Snapshot of a position remaining open at the end of the candle dataset."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    symbol: str
    side: TradeSide
    entry_signal_time_ms: int
    entry_fill_time_ms: int
    mark_time_ms: int
    entry_price: float
    mark_price: float
    quantity: float
    upper_barrier: float
    lower_barrier: float
    volatility_sigma: float
    bars_held: int
    position_state: Optional[PositionLifecycleState] = None
    accounting: OpenPositionAccountingResult


class BacktestSummary(BaseModel):
    """Consolidated performance summary of a backtest run."""
    model_config = ConfigDict(frozen=True, validate_assignment=True)

    symbol: str
    track_classification: str = TRACK_2_GOVERNANCE_CLASSIFICATION
    risk_evaluation_mode: RiskEvaluationMode
    mode_output_classification: str
    funding_data_status: str = HISTORICAL_FUNDING_STATUS
    dec_05_portfolio_status: str = "PENDING_HUMAN_DECISION"
    total_signals: int
    approved_trades: int
    rejected_trades: int
    rejection_breakdown: Dict[str, int] = Field(default_factory=dict)
    missing_candle_gaps_detected: int = 0
    winning_trades: int
    losing_trades: int
    win_rate: float
    gross_expectancy_bps: float
    net_expectancy_bps: float
    total_pnl_usdt: float
    total_fees_usdt: float
    total_slippage_usdt: float
    total_funding_usdt: float
    ending_equity_usdt: float
    peak_equity_usdt: float
    profit_factor: float
    max_drawdown_pct: float
    trades: List[BacktestTrade]
    open_positions_at_end: List[OpenPositionSnapshot] = Field(default_factory=list)


class DiscreteEventBacktestEngine:
    """Deterministic, causal historical simulation engine for QUANTUM Track 2."""

    def __init__(
        self,
        config: BacktestConfig,
        risk_agent: Optional[RiskAgent] = None,
        banker_agent: Optional[BankerAgent] = None,
    ) -> None:
        self.config = config
        self.risk_agent = risk_agent or RiskAgent(RiskConfig())
        self.banker_agent = banker_agent or BankerAgent()

    def get_mode_output_classification(self) -> str:
        """Return explicit output classification string for the configured risk evaluation mode."""
        mode = self.config.risk_evaluation_mode
        if mode == RiskEvaluationMode.MODE_1_BARRIER_ACCOUNTING_BENCHMARK:
            return "MECHANICAL_BARRIER_ACCOUNTING_NO_RISK_ENFORCEMENT"
        if mode == RiskEvaluationMode.MODE_2_RISK_FILTERED_EXECUTION_SIMULATION:
            return "SINGLE_ASSET_RISK_GATED_EXECUTION_SIMULATION"
        return "BOUNDED_PORTFOLIO_LEDGER_DEC_05_PENDING_HUMAN_DECISION"

    def compute_causal_volatility(self, close_series: pd.Series) -> pd.Series:
        """Compute rolling sample return volatility strictly causally using past close returns."""
        returns = close_series.pct_change()
        vol = returns.rolling(
            window=self.config.volatility_lookback,
            min_periods=self.config.volatility_lookback,
        ).std(ddof=1)
        if self.config.min_volatility > 0.0:
            vol = vol.clip(lower=self.config.min_volatility)
        return vol.fillna(0.0)

    @staticmethod
    def _validate_candles(candles_df: pd.DataFrame, min_bars: int) -> pd.DataFrame:
        """Validate OHLCV candle schema, positive finite prices, OHLC geometry, and unique timestamps."""
        if candles_df.empty:
            raise ValueError("candles_df cannot be empty")

        req_cols = ["open_time_ms", "open", "high", "low", "close"]
        for c in req_cols:
            if c not in candles_df.columns:
                raise ValueError(f"Missing required candle column: {c}")

        if candles_df[req_cols].isnull().any().any():
            raise ValueError("candles_df contains NaN or null values in required columns")

        if candles_df.duplicated(subset=["open_time_ms"]).any():
            raise ValueError("candles_df contains duplicate open_time_ms timestamps")

        df = candles_df.sort_values("open_time_ms", kind="mergesort").reset_index(drop=True)
        n = len(df)
        if n < min_bars:
            raise ValueError(f"Insufficient candles ({n}) for minimum required bars ({min_bars})")

        opens = df["open"].to_numpy(dtype=float)
        highs = df["high"].to_numpy(dtype=float)
        lows = df["low"].to_numpy(dtype=float)
        closes = df["close"].to_numpy(dtype=float)

        for name, arr in [("open", opens), ("high", highs), ("low", lows), ("close", closes)]:
            if not np.all(np.isfinite(arr)) or np.any(arr <= 0.0):
                raise ValueError(f"Candle column '{name}' contains non-positive or non-finite prices")

        if np.any(highs < lows) or np.any(opens > highs) or np.any(opens < lows) or np.any(closes > highs) or np.any(closes < lows):
            raise ValueError("Invalid OHLC geometry: violated low <= open, close <= high")

        return df

    async def run(
        self,
        candles_df: pd.DataFrame,
        signals: Sequence[OOFSignal],
    ) -> BacktestSummary:
        """Execute discrete-event simulation across candles and signals."""
        if (
            self.config.risk_evaluation_mode == RiskEvaluationMode.MODE_3_PORTFOLIO_LEVEL_RISK_SIMULATION
            and not self.config.allow_bounded_mode3_preview
        ):
            raise GovernancePendingError(
                "MODE_3_PORTFOLIO_LEVEL_RISK_SIMULATION is gated on DEC_05 (PENDING_HUMAN_DECISION). "
                "Set allow_bounded_mode3_preview=True only for isolated single-asset ledger testing."
            )

        min_bars = self.config.volatility_lookback + 1
        df = self._validate_candles(candles_df, min_bars=min_bars)
        n = len(df)

        # Map signals by open_time_ms (deterministic last-seen or reject duplicate signal timestamps)
        signal_map: Dict[int, OOFSignal] = {}
        for s in signals:
            if s.symbol != self.config.symbol:
                raise ValueError(f"Cross-asset signal {s.symbol} passed to engine configured for {self.config.symbol}")
            if s.open_time_ms in signal_map:
                raise ValueError(f"Duplicate signal open_time_ms detected: {s.open_time_ms}")
            signal_map[s.open_time_ms] = s

        vol_series = self.compute_causal_volatility(df["close"]).to_numpy(dtype=float)
        timestamps = df["open_time_ms"].to_numpy(dtype=int)
        opens = df["open"].to_numpy(dtype=float)
        highs = df["high"].to_numpy(dtype=float)
        lows = df["low"].to_numpy(dtype=float)
        closes = df["close"].to_numpy(dtype=float)

        trades: List[BacktestTrade] = []
        total_signals = 0
        approved_trades = 0
        rejected_trades = 0
        rejection_breakdown: Dict[str, int] = {}
        missing_candle_gaps_detected = 0

        def _record_rejection(reason: str) -> None:
            nonlocal rejected_trades
            rejected_trades += 1
            rejection_breakdown[reason] = rejection_breakdown.get(reason, 0) + 1

        # Sequential portfolio & risk state tracking
        current_equity = self.config.initial_equity_usdt
        peak_equity = self.config.initial_equity_usdt
        max_dd_pct = 0.0
        current_day_index: Optional[int] = None
        daily_realized_pnl = 0.0
        consecutive_losses = 0
        last_loss_timestamp_ms: Optional[int] = None

        active_trade: Optional[Dict] = None
        tf_ms = self.config.timeframe_ms

        for i in range(self.config.volatility_lookback, n):
            current_open_ts = int(timestamps[i])
            prev_open_ts = int(timestamps[i - 1])
            day_idx = current_open_ts // 86_400_000
            if current_day_index != day_idx:
                current_day_index = day_idx
                daily_realized_pnl = 0.0

            is_gap_bar = (current_open_ts - prev_open_ts) != tf_ms
            if is_gap_bar:
                missing_candle_gaps_detected += 1
                if self.config.strict_candle_continuity:
                    raise ValueError(
                        f"Missing candle gap detected between {prev_open_ts} and {current_open_ts} "
                        f"(expected step {tf_ms} ms)"
                    )

            # =========================================================================
            # STEP 1 (At Bar i Open, t_i): Check for Signal Generated at Bar i-1 Close
            # =========================================================================
            if prev_open_ts in signal_map:
                sig = signal_map[prev_open_ts]
                total_signals += 1

                if active_trade is not None:
                    _record_rejection("CONCURRENT_POSITION_BLOCKED")
                elif is_gap_bar:
                    _record_rejection("REJECTED_MISSING_CANDLE_GAP")
                else:
                    is_long_sig = (
                        self.config.directional_mode in ("LONG_ONLY", "BIDIRECTIONAL")
                        and (sig.prob_tp >= self.config.prob_threshold or sig.predicted_class == 1)
                    )
                    is_short_sig = (
                        self.config.directional_mode in ("SHORT_ONLY", "BIDIRECTIONAL")
                        and (sig.prob_sl >= self.config.prob_threshold or sig.predicted_class == -1)
                    )

                    if not (is_long_sig or is_short_sig):
                        _record_rejection("BELOW_DIRECTIONAL_THRESHOLD")
                    else:
                        trade_side = TradeSide.LONG if is_long_sig else TradeSide.SHORT
                        entry_fill_price = float(opens[i])  # Causal entry reference at open[s+1]
                        sigma_t = float(vol_series[i - 1])  # Causal volatility up to close[s]

                        if sigma_t <= 0.0 or not math.isfinite(sigma_t):
                            _record_rejection("REJECTED_ZERO_VOLATILITY")
                        else:
                            u_barr = entry_fill_price * (1.0 + self.config.barrier_multiplier * sigma_t)
                            l_barr = entry_fill_price * (1.0 - self.config.barrier_multiplier * sigma_t)
                            if l_barr <= 0.0:
                                _record_rejection("INVALID_LOWER_BARRIER_NON_POSITIVE")
                            else:
                                stop_px = l_barr if trade_side == TradeSide.LONG else u_barr
                                tp_px = u_barr if trade_side == TradeSide.LONG else l_barr

                                trade_qty = self.config.trade_notional_usdt / entry_fill_price
                                tp1_val = tp_px
                                tp2_val = tp_px + 0.01 if trade_side == TradeSide.LONG else max(1e-8, tp_px - 0.01)

                                risk_approved = True
                                veto_key = "VETO_RISK_AGENT"
                                if self.config.risk_evaluation_mode in (
                                    RiskEvaluationMode.MODE_2_RISK_FILTERED_EXECUTION_SIMULATION,
                                    RiskEvaluationMode.MODE_3_PORTFOLIO_LEVEL_RISK_SIMULATION,
                                ):
                                    est_rr = (
                                        self.config.proposal_estimated_rr_override
                                        if self.config.proposal_estimated_rr_override is not None
                                        else 1.0
                                    )
                                    d_sign = 1.0 if trade_side == TradeSide.LONG else -1.0
                                    if self.config.proposal_estimated_rr_override is not None:
                                        eff_risk_dist = abs(entry_fill_price - stop_px) + (entry_fill_price * 0.002)
                                        prop_tp1 = entry_fill_price + d_sign * (est_rr * eff_risk_dist)
                                        prop_tp2 = prop_tp1 + (0.01 * d_sign)
                                    else:
                                        prop_tp1 = tp1_val
                                        prop_tp2 = tp2_val

                                    risk_input = RiskInput(
                                        pipeline_run_id=f"pipe_sim_{current_open_ts}",
                                        candidate=ScannerCandidate(
                                            candidate_id=f"cand_sim_{current_open_ts}",
                                            scan_cycle_id="cycle_sim",
                                            symbol=self.config.symbol,
                                            exchange=self.config.exchange,
                                            directional_bias=trade_side,
                                            primary_category=CandidateCategory.MOMENTUM_ACCELERATION,
                                            deterministic_score=80.0,
                                            state_hash="a" * 16,
                                            context=MarketContext(
                                                symbol=self.config.symbol,
                                                exchange=self.config.exchange,
                                                snapshot_timestamp_ms=current_open_ts,
                                                last_price=entry_fill_price,
                                                mark_price=entry_fill_price,
                                                index_price=entry_fill_price,
                                                bid1_price=max(1e-8, entry_fill_price * 0.9999),
                                                ask1_price=entry_fill_price * 1.0001,
                                                spread_bps=2.0,
                                                turnover_24h_usdt=500_000_000.0,
                                                price_change_24h_pct=1.0,
                                                funding_rate=0.0001,
                                                next_funding_time_ms=current_open_ts + 28_800_000,
                                                atr_15m=entry_fill_price * sigma_t,
                                                atr_1h=entry_fill_price * sigma_t * 1.5,
                                                rsi_15m=50.0,
                                                rvol_15m=1.0,
                                                features={"wick_trap_ratio": 0.1},
                                            ),
                                            created_at_ms=current_open_ts,
                                            expires_at_ms=current_open_ts + 60_000,
                                        ),
                                        proposal=TradeProposal(
                                            proposal_id=f"prop_sim_{current_open_ts}",
                                            pipeline_run_id=f"pipe_sim_{current_open_ts}",
                                            exchange=self.config.exchange,
                                            symbol=self.config.symbol,
                                            side=trade_side,
                                            order_type=OrderType.LIMIT,
                                            reference_mark_price=entry_fill_price,
                                            entry_price=entry_fill_price,
                                            entry_zone_low=entry_fill_price * 0.99,
                                            entry_zone_high=entry_fill_price * 1.01,
                                            stop_loss=stop_px,
                                            take_profit_1=prop_tp1,
                                            take_profit_2=prop_tp2,
                                            tp1_close_pct=1.0,
                                            estimated_reward_risk=max(1.5, est_rr),
                                            expected_net_r=max(1.2, est_rr * 0.8),
                                            prob_tp1_before_sl=sig.prob_tp if trade_side == TradeSide.LONG else sig.prob_sl,
                                            prob_tp2_before_sl=sig.prob_tp if trade_side == TradeSide.LONG else sig.prob_sl,
                                            expected_holding_minutes=60,
                                            rationale="Track 2 simulation proposal",
                                            market_regime=MarketRegime.TREND_IMPULSE,
                                            invalidation_price=stop_px,
                                            sniper_model_version="frozen_phase_5_3",
                                            created_at_ms=current_open_ts,
                                        ),
                                        current_equity_usdt=max(1e-4, current_equity),
                                        peak_equity_usdt=max(1e-4, peak_equity),
                                        daily_pnl_usdt=daily_realized_pnl,
                                        starting_day_equity_usdt=max(1e-4, current_equity - daily_realized_pnl),
                                        consecutive_losses_count=consecutive_losses,
                                        last_loss_timestamp_ms=last_loss_timestamp_ms,
                                        open_positions_count=0,
                                        total_exposure_usdt=0.0,
                                        estimated_slippage_bps=self.config.slippage_bps,
                                        eval_timestamp_ms=current_open_ts,
                                    )
                                    risk_out = await self.risk_agent.evaluate(risk_input)
                                    risk_approved = risk_out.decision.decision == AgentAction.APPROVED
                                    if not risk_approved and risk_out.decision.veto_reasons:
                                        veto_key = risk_out.decision.veto_reasons[0]

                                if risk_approved:
                                    approved_trades += 1
                                    tracked_pos: Optional[TrackedPosition] = None

                                    if self.config.enable_banker_agent:
                                        tracked_pos = TrackedPosition(
                                            position_id=f"pos_{approved_trades}",
                                            symbol=self.config.symbol,
                                            side=trade_side,
                                            state=PositionLifecycleState.PENDING_OPEN,
                                            entry_price=entry_fill_price,
                                            initial_quantity=trade_qty,
                                            remaining_quantity=trade_qty,
                                            current_stop_loss=stop_px,
                                            take_profit_1=tp1_val,
                                            take_profit_2=tp2_val,
                                            tp1_target_quantity=trade_qty,
                                            tp2_target_quantity=0.0,
                                            created_at_ms=current_open_ts,
                                            updated_at_ms=current_open_ts,
                                        )
                                        fill_event = PositionExecutionEvent(
                                            event_id=f"evt_entry_{approved_trades}",
                                            position_id=tracked_pos.position_id,
                                            event_type=ExecutionEventType.ENTRY_FILL,
                                            fill_price=entry_fill_price,
                                            fill_quantity=trade_qty,
                                            timestamp_ms=current_open_ts,
                                            sequence_number=1,
                                        )
                                        tracked_pos, _ = self.banker_agent.handle_execution_event(tracked_pos, fill_event)

                                    active_trade = {
                                        "entry_bar": i,
                                        "side": trade_side,
                                        "entry_signal_time_ms": prev_open_ts + tf_ms,
                                        "entry_fill_time_ms": current_open_ts,
                                        "entry_price": entry_fill_price,
                                        "quantity": trade_qty,
                                        "upper_barrier": u_barr,
                                        "lower_barrier": l_barr,
                                        "volatility": sigma_t,
                                        "tracked_pos": tracked_pos,
                                    }
                                else:
                                    _record_rejection(veto_key)

            # =========================================================================
            # STEP 2 (Across Bar i, [t_i, t_i + tf_ms]): Monitor Active Trade Barriers
            # =========================================================================
            if active_trade is not None:
                entry_bar = active_trade["entry_bar"]
                bars_held = (i - entry_bar) + 1

                u_barrier = active_trade["upper_barrier"]
                l_barrier = active_trade["lower_barrier"]
                side = active_trade["side"]
                bar_o = float(opens[i])
                bar_h = float(highs[i])
                bar_l = float(lows[i])
                bar_c = float(closes[i])

                exit_triggered = False
                exit_price = 0.0
                exit_reason = ""
                is_gap_exit = False

                # 2a. Check Opening Gap beyond barriers on subsequent bars (i > entry_bar)
                if i > entry_bar:
                    if side == TradeSide.LONG:
                        if bar_o <= l_barrier:
                            exit_price = bar_o
                            exit_reason = "STOP_LOSS"
                            is_gap_exit = True
                            exit_triggered = True
                        elif bar_o >= u_barrier:
                            exit_price = bar_o
                            exit_reason = "TAKE_PROFIT"
                            is_gap_exit = True
                            exit_triggered = True
                    else:
                        if bar_o >= u_barrier:
                            exit_price = bar_o
                            exit_reason = "STOP_LOSS"
                            is_gap_exit = True
                            exit_triggered = True
                        elif bar_o <= l_barrier:
                            exit_price = bar_o
                            exit_reason = "TAKE_PROFIT"
                            is_gap_exit = True
                            exit_triggered = True

                # 2b. Check Intrabar High/Low touches if not exited on opening gap
                if not exit_triggered:
                    upper_touch = bar_h >= u_barrier
                    lower_touch = bar_l <= l_barrier

                    if upper_touch and lower_touch:
                        if self.config.collision_policy == "CONSERVATIVE_SL_FIRST":
                            exit_price = l_barrier if side == TradeSide.LONG else u_barrier
                            exit_reason = "STOP_LOSS"
                        else:
                            exit_price = u_barrier if side == TradeSide.LONG else l_barrier
                            exit_reason = "TAKE_PROFIT"
                        exit_triggered = True

                    elif (side == TradeSide.LONG and upper_touch) or (side == TradeSide.SHORT and lower_touch):
                        exit_price = u_barrier if side == TradeSide.LONG else l_barrier
                        exit_reason = "TAKE_PROFIT"
                        exit_triggered = True

                    elif (side == TradeSide.LONG and lower_touch) or (side == TradeSide.SHORT and upper_touch):
                        exit_price = l_barrier if side == TradeSide.LONG else u_barrier
                        exit_reason = "STOP_LOSS"
                        exit_triggered = True

                    elif bars_held >= self.config.horizon_bars:
                        exit_price = bar_c
                        exit_reason = "TIME_EXPIRATION"
                        exit_triggered = True

                if exit_triggered:
                    exit_time_ms = current_open_ts + tf_ms
                    entry_time_ms = active_trade["entry_fill_time_ms"]
                    entry_price = active_trade["entry_price"]
                    quantity = active_trade["quantity"]

                    cf_funding, funding_sets = calculate_funding_cash_flow(
                        side=side,
                        entry_notional=quantity * entry_price,
                        entry_time_ms=entry_time_ms,
                        exit_time_ms=exit_time_ms,
                        funding_rate_bps_per_settlement=self.config.funding_rate_bps_per_settlement,
                    )

                    acc_result = compute_two_legged_pnl(
                        side=side,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        quantity=quantity,
                        fee_rate_bps=self.config.fee_rate_bps,
                        slippage_bps=self.config.slippage_bps,
                        funding_cash_flow_usdt=cf_funding,
                        funding_settlements=funding_sets,
                        leverage=self.config.leverage,
                    )

                    # Update sequential portfolio & risk state
                    current_equity += acc_result.net_pnl_usdt
                    daily_realized_pnl += acc_result.net_pnl_usdt
                    if current_equity > peak_equity:
                        peak_equity = current_equity
                    dd_now = ((peak_equity - current_equity) / peak_equity) * 100.0 if peak_equity > 0 else 0.0
                    if dd_now > max_dd_pct:
                        max_dd_pct = dd_now

                    if acc_result.net_pnl_usdt < 0.0:
                        consecutive_losses += 1
                        last_loss_timestamp_ms = exit_time_ms
                    else:
                        consecutive_losses = 0

                    # Update BankerAgent FSM if enabled
                    final_pos: Optional[TrackedPosition] = active_trade["tracked_pos"]
                    if self.config.enable_banker_agent and final_pos is not None:
                        if exit_reason == "TAKE_PROFIT":
                            event_type = ExecutionEventType.TP1_FILL
                        elif exit_reason == "STOP_LOSS":
                            event_type = ExecutionEventType.SL_FILL
                        else:
                            event_type = ExecutionEventType.MANUAL_CLOSE

                        event = PositionExecutionEvent(
                            event_id=f"evt_exit_{len(trades)+1}",
                            position_id=final_pos.position_id,
                            event_type=event_type,
                            fill_price=exit_price,
                            fill_quantity=quantity,
                            timestamp_ms=exit_time_ms,
                            sequence_number=2,
                        )
                        final_pos, _ = self.banker_agent.handle_execution_event(final_pos, event)

                    trades.append(
                        BacktestTrade(
                            trade_id=f"trade_{len(trades)+1}",
                            symbol=self.config.symbol,
                            side=side,
                            entry_signal_time_ms=active_trade["entry_signal_time_ms"],
                            entry_fill_time_ms=entry_time_ms,
                            exit_time_ms=exit_time_ms,
                            entry_price=entry_price,
                            exit_price=exit_price,
                            entry_fill_price_effective=acc_result.entry_fill_price_effective,
                            exit_fill_price_effective=acc_result.exit_fill_price_effective,
                            exit_reason=exit_reason,
                            is_gap_exit=is_gap_exit,
                            upper_barrier=u_barrier,
                            lower_barrier=l_barrier,
                            volatility_sigma=active_trade["volatility"],
                            holding_bars=bars_held,
                            accounting=acc_result,
                            final_position_state=final_pos.state if final_pos is not None else None,
                            tracked_position=final_pos,
                        )
                    )
                    active_trade = None

        # =========================================================================
        # STEP 3: Handle Position Still Open at Dataset End (Mark-to-Market)
        # =========================================================================
        open_positions_at_end: List[OpenPositionSnapshot] = []
        if active_trade is not None:
            last_close = float(closes[n - 1])
            last_close_ts = int(timestamps[n - 1]) + tf_ms
            entry_time_ms = active_trade["entry_fill_time_ms"]
            entry_price = active_trade["entry_price"]
            quantity = active_trade["quantity"]
            side = active_trade["side"]
            bars_held = (n - 1 - active_trade["entry_bar"]) + 1

            cf_open, _ = calculate_funding_cash_flow(
                side=side,
                entry_notional=quantity * entry_price,
                entry_time_ms=entry_time_ms,
                exit_time_ms=last_close_ts,
                funding_rate_bps_per_settlement=self.config.funding_rate_bps_per_settlement,
            )

            open_acc = compute_open_position_accounting(
                side=side,
                entry_price=entry_price,
                mark_price=last_close,
                open_quantity=quantity,
                fee_rate_bps=self.config.fee_rate_bps,
                slippage_bps=self.config.slippage_bps,
                accrued_funding_cash_flow_usdt=cf_open,
                leverage=self.config.leverage,
            )
            tracked_pos = active_trade["tracked_pos"]
            open_positions_at_end.append(
                OpenPositionSnapshot(
                    symbol=self.config.symbol,
                    side=side,
                    entry_signal_time_ms=active_trade["entry_signal_time_ms"],
                    entry_fill_time_ms=entry_time_ms,
                    mark_time_ms=last_close_ts,
                    entry_price=entry_price,
                    mark_price=last_close,
                    quantity=quantity,
                    upper_barrier=active_trade["upper_barrier"],
                    lower_barrier=active_trade["lower_barrier"],
                    volatility_sigma=active_trade["volatility"],
                    bars_held=bars_held,
                    position_state=tracked_pos.state if tracked_pos is not None else PositionLifecycleState.OPEN,
                    accounting=open_acc,
                )
            )

        # Consolidate Summary Metrics
        winning_trades = sum(1 for t in trades if t.accounting.net_pnl_usdt > 0)
        losing_trades = sum(1 for t in trades if t.accounting.net_pnl_usdt <= 0)
        num_trades = len(trades)
        win_rate = (winning_trades / num_trades) if num_trades > 0 else 0.0

        gross_exp = float(np.mean([t.accounting.gross_return * 10000.0 for t in trades])) if num_trades > 0 else 0.0
        net_exp = float(np.mean([t.accounting.net_return_bps for t in trades])) if num_trades > 0 else 0.0

        tot_pnl = sum(t.accounting.net_pnl_usdt for t in trades)
        tot_fees = sum(t.accounting.total_fees_usdt for t in trades)
        tot_slip = sum(t.accounting.total_slippage_usdt for t in trades)
        tot_fund = sum(t.accounting.funding_cash_flow_usdt for t in trades)

        gross_wins = sum(t.accounting.net_pnl_usdt for t in trades if t.accounting.net_pnl_usdt > 0)
        gross_losses = abs(sum(t.accounting.net_pnl_usdt for t in trades if t.accounting.net_pnl_usdt < 0))
        pf = (gross_wins / gross_losses) if gross_losses > 0 else (999.0 if gross_wins > 0 else 0.0)

        return BacktestSummary(
            symbol=self.config.symbol,
            risk_evaluation_mode=self.config.risk_evaluation_mode,
            mode_output_classification=self.get_mode_output_classification(),
            total_signals=total_signals,
            approved_trades=approved_trades,
            rejected_trades=rejected_trades,
            rejection_breakdown=rejection_breakdown,
            missing_candle_gaps_detected=missing_candle_gaps_detected,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=round(win_rate, 6),
            gross_expectancy_bps=round(gross_exp, 4),
            net_expectancy_bps=round(net_exp, 4),
            total_pnl_usdt=round(tot_pnl, 6),
            total_fees_usdt=round(tot_fees, 6),
            total_slippage_usdt=round(tot_slip, 6),
            total_funding_usdt=round(tot_fund, 6),
            ending_equity_usdt=round(current_equity, 6),
            peak_equity_usdt=round(peak_equity, 6),
            profit_factor=round(pf, 4),
            max_drawdown_pct=round(max_dd_pct, 4),
            trades=trades,
            open_positions_at_end=open_positions_at_end,
        )
