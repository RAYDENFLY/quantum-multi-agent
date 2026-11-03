# QUANTUM — `STRAT_242` Independent Forensic Recalculation & Reproducibility Audit

**Document Identifier:** `audit/strategy_research/post_300_review/STRAT_242_INDEPENDENT_RECALCULATION.md`  
**Evaluation Date:** `2026-11-03T02:45:00Z`  
**Git Commit:** `dcc8ceb54d80b1b9685d92236f48b0994610522a`  
**Evaluation Engine:** `src/quantum/strategies/evaluator.py` & `scripts/run_post_300_forensic_review.py`  
**Verification Status:** **`EXACT_REPRODUCIBILITY_VERIFIED`** (Mathematical precision: $\Delta \text{Equity} = \$0.0000$, $\Delta \text{Daily} = 0.000000\%$)

---

## 1. Provenance, Artifact & Identity Specifications

The authoritative parameters and cryptographic fingerprints for `STRAT_242` are extracted directly from immutable storage artifacts:

| Parameter / Field | Verified Value | Verification Source |
| :--- | :--- | :--- |
| **Strategy Identifier** | `STRAT_242` | `data_backtest/batch_003/configurations/STRAT_242.json` |
| **Batch Identifier** | `batch_003` | Lineage: Local neighborhood refinement of `STRAT_134` (Batch 002) |
| **Version** | `1.0.0` | Declarative Pydantic Schema |
| **Deterministic Config Hash** | **`b02f17c3e006c2c9`** | SHA-256 of sorted canonical JSON parameters (first 16 hex chars) |
| **Experiment Identifier** | `EXP_B003_STRAT_242_b02f17c3` | `data_backtest/manifests/EXP_B003_STRAT_242_b02f17c3_manifest.json` |
| **Dataset Identity** | `ASTER_CANONICAL_5M_FOLDS_1_4` | `data/historical/canonical/exchange=ASTER/symbol=*/timeframe=5m/` |
| **Dataset Fingerprint** | `sha256_f14_104544bars_sealed_1793491200000` | 104,544 5m bars per asset across Folds 1–4 |
| **Model Artifact** | `phase_5_3_frozen_lgbm_v1` | `artifacts/phase_5_4/materialized_oof/{symbol}_oof.parquet` |
| **Base Timeframe** | `5m` (5-minute OHLCV + Order-Flow bars) | Causal forward-fill, execution at bar `i` open |
| **Applicable Universe** | `DOGEUSDT`, `SOLUSDT`, `ADAUSDT`, `XRPUSDT`, `LINKUSDT` | 5 high-beta altcoin specialists |
| **Evaluation Period** | `2025-01-29T11:20:00Z` to `2026-01-29T14:35:00Z` | `365.14 calendar days` |
| **Prospective Holdout** | `1793491200000 ms` (`2026-11-01 00:00:00 UTC`) | **`STRICTLY SEALED (0 accesses)`** |

---

## 2. Exact Declarative Configuration

```json
{
  "strategy_id": "STRAT_242",
  "version": "1.0.0",
  "batch_id": "batch_003",
  "family": "LIQUIDITY_MICROSTRUCTURE",
  "hypothesis": "Batch 3 Local Surface Refinement of STRAT_134: margin=0.22, htf_max=-93.0 bps, TP=3.0s, SL=1.15s, H=20b, risk=2.40%.",
  "parent_strategy_id": "STRAT_134",
  "applicable_assets": [
    "DOGEUSDT",
    "SOLUSDT",
    "ADAUSDT",
    "XRPUSDT",
    "LINKUSDT"
  ],
  "timeframe": "5m",
  "entry": {
    "direction_mode": "LONG_ONLY",
    "prob_margin_min": 0.22,
    "p0_neutral_max": 0.27,
    "vol_quantile_min": 0.92,
    "vol_quantile_max": 1.0,
    "vol_expansion_ratio_min": 0.0,
    "rvol_min": 0.0,
    "taker_buy_ratio_min": 0.0,
    "taker_buy_ratio_max": 1.0,
    "wick_rejection_min": 0.0,
    "htf_lookback_bars": 12,
    "htf_return_min_bps": -10000.0,
    "htf_return_max_bps": -93.0,
    "btc_lead_lookback_bars": 6,
    "btc_lead_min_bps": -10000.0,
    "btc_lead_max_bps": 10000.0,
    "order_type": "MARKET",
    "limit_offset_sigma": 0.0,
    "order_timeout_bars": 3,
    "cooldown_bars": 0
  },
  "exit": {
    "tp1_multiplier": 3.0,
    "tp2_multiplier": 3.5,
    "tp1_close_pct": 0.0,
    "sl_multiplier": 1.15,
    "breakeven_ratchet_on_tp1": false,
    "trailing_stop_distance_sigma": 0.0,
    "horizon_bars": 20
  },
  "risk": {
    "initial_equity_usd": 100.0,
    "risk_per_trade_pct": 0.024,
    "max_symbol_exposure_pct": 0.43,
    "max_total_exposure_pct": 1.2,
    "max_leverage": 2.0,
    "max_concurrent_positions": 4,
    "min_notional_usdt": 5.0,
    "fee_tier": "maker_passive"
  },
  "config_hash": "b02f17c3e006c2c9"
}
```

---

## 3. Trade-by-Trade Portfolio Accounting Verification

To eliminate any reliance on cached summaries, `scripts/run_post_300_forensic_review.py` was executed to re-simulate every market bar, re-extract every signal, re-execute the portfolio queue, and export all **1,580 individual executed trades** into:

`data_backtest/batch_003/trade_logs/STRAT_242_trades_full.json`

### 3.1 Initial Conditions & Sizing Laws
- **Starting Account Equity:** $E_0 = \$100.00\text{ USD}$.
- **Risk Budget per Trade:** $R_t = E_t \times 0.024$ ($2.40\%$ of current equity).
- **Stop Distance Fraction:** $D_{\text{stop}} = \max(1.15 \times \sigma_t, 0.0015)$.
- **Raw Position Notional:** $N_{\text{raw}} = R_t / D_{\text{stop}}$.
- **Exposure Limits:**
  - Per-Symbol Cap: $N \le E_t \times 0.43$.
  - Total Portfolio Cap: $\sum N \le E_t \times 1.20$.
  - Leverage Ceiling: $N \le E_t \times 2.0$.
  - Lot Rounding: Truncated to 2 decimal places ($0.01\text{ USD}$ step).
  - Minimum Notional Threshold: $N \ge \$5.00\text{ USDT}$.

### 3.2 Audit of First 5 and Last 5 Executed Trades

| Trade # | Symbol | Entry Time (UTC) | Exit Time (UTC) | Entry Px | Exit Px | Exit Reason | Notional ($) | Gross Ret | Fees ($) | Fund ($) | Net PnL ($) | Ending Equity ($) |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **#1** | `SOLUSDT` | `2025-01-29 19:30` | `2025-01-29 19:40` | 224.68 | 228.62 | `TAKE_PROFIT` | $43.00 | +175.57 bps | $0.0344 | $0.0000 | **+$0.7205** | **$100.72** |
| **#2** | `SOLUSDT` | `2025-02-01 20:55` | `2025-02-01 21:45` | 218.72 | 217.44 | `STOP_LOSS` | $43.30 | -58.52 bps | $0.0346 | $0.0000 | **-$0.2880** | **$100.43** |
| **#3** | `SOLUSDT` | `2025-02-01 21:45` | `2025-02-01 22:25` | 217.06 | 219.86 | `TAKE_PROFIT` | $43.18 | +128.99 bps | $0.0345 | $0.0000 | **+$0.5225** | **$100.95** |
| **#4** | `SOLUSDT` | `2025-02-02 21:00` | `2025-02-02 21:50` | 206.84 | 205.81 | `STOP_LOSS` | $43.40 | -49.79 bps | $0.0347 | $0.0000 | **-$0.2508** | **$100.70** |
| **#5** | `SOLUSDT` | `2025-02-02 22:50` | `2025-02-02 23:45` | 201.21 | 204.60 | `TAKE_PROFIT` | $43.30 | +168.48 bps | $0.0346 | $0.0000 | **+$0.6949** | **$101.40** |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |
| **#1576** | `LINKUSDT` | `2026-01-29 03:00` | `2026-01-29 04:40` | 13.882 | 13.785 | `TIME_EXPIRATION` | $62.09 | -69.87 bps | $0.0497 | $0.0000 | **-$0.4835** | **$144.33** |
| **#1577** | `XRPUSDT` | `2026-01-29 05:40` | `2026-01-29 07:20` | 1.8492 | 1.8465 | `TIME_EXPIRATION` | $62.06 | -14.60 bps | $0.0496 | $0.0000 | **-$0.1402** | **$144.19** |
| **#1578** | `XRPUSDT` | `2026-01-29 07:45` | `2026-01-29 08:35` | 1.8548 | 1.8687 | `TAKE_PROFIT` | $62.00 | +74.94 bps | $0.0496 | $0.0000 | **+$0.4150** | **$144.60** |
| **#1579** | `XRPUSDT` | `2026-01-29 10:20` | `2026-01-29 11:15` | 1.8688 | 1.8633 | `STOP_LOSS` | $62.17 | -29.43 bps | $0.0497 | $0.0000 | **-$0.2327** | **$144.37** |
| **#1580** | `LINKUSDT` | `2026-01-29 12:45` | `2026-01-29 13:30` | 13.824 | 13.843 | `TAKE_PROFIT` | $62.08 | +13.74 bps | $0.0497 | $0.0000 | **+$0.0356** | **$144.40** |

---

## 4. Independent Recalculation vs. Reported Results Matrix

Every summary metric was recalculated independently from the trade arrays and calendar daily marks. The comparison confirms $0.0000$ deviation:

| Metric | Original Report Value | Independently Recalculated | Delta | Forensic Assessment |
| :--- | :---: | :---: | :---: | :--- |
| **Ending Equity** | **`$144.40 USD`** | **`$144.40 USD`** | **`$0.0000`** | **Exact match confirmed** |
| **Cumulative Net Return** | `+44.40%` | `+44.40%` | `0.0000%` | Exact match confirmed |
| **Arithmetic Mean Daily Return** | `+0.1092% / day` | `+0.1092% / day` | `0.000000%` | Exact match confirmed |
| **Geometric Mean Daily Return** | `+0.1004% / day` | `+0.1004% / day` | `0.000000%` | Exact match confirmed |
| **Median Daily Return** | `+0.0000% / day` | `+0.0000% / day` | `0.000000%` | Exact match confirmed |
| **Annualized Sharpe Ratio** | `1.577` | `1.577` | `0.000` | Exact match confirmed |
| **Annualized Sortino Ratio** | `1.409` | `1.409` | `0.000` | Exact match confirmed |
| **Maximum Drawdown (MDD)** | `16.35%` | `16.35%` | `0.00%` | Exact match confirmed |
| **Mean Underwater Drawdown** | `4.40%` | `4.40%` | `0.00%` | Exact match confirmed |
| **Gross Expectancy per Trade** | `+15.42 bps` | `+15.42 bps` | `0.00 bps` | Exact match confirmed |
| **Net Expectancy per Trade** | `+7.33 bps` | `+7.33 bps` | `0.00 bps` | Exact match confirmed |
| **Profit Factor** | `1.108` | `1.108` | `0.000` | Exact match confirmed |
| **Win Rate** | `37.59%` | `37.59%` | `0.00%` | Exact match confirmed (594 wins / 986 losses) |
| **Total Fees Paid** | `$59.14 USD` | `$59.14 USD` | `$0.00` | Exact match confirmed |
| **Total Funding Paid** | `$0.75 USD` | `$0.75 USD` | `$0.00` | Exact match confirmed |
| **Total Slippage Paid** | `$0.00 USD` | `$0.00 USD` | `$0.00` | Exact match confirmed |
| **Total Executed Trades** | `1,580` | `1,580` | `0` | Exact match confirmed |
| **Missed Trades (Min Notional $5)** | `0` | `0` | `0` | Exact match confirmed |
| **Missed Trades (Capacity/Concurrent)**| `180` | `180` | `0` | Exact match confirmed |
| **Walk-Forward Fold 1 Return** | `+5.11%` | `+5.11%` | `0.00%` | Exact match confirmed |
| **Walk-Forward Fold 2 Return** | `+7.98%` | `+7.98%` | `0.00%` | Exact match confirmed |
| **Walk-Forward Fold 3 Return** | `+33.79%` | `+33.79%` | `0.00%` | Exact match confirmed |
| **Walk-Forward Fold 4 Return** | `-4.55%` | `-4.55%` | `0.00%` | Exact match confirmed |

---

## 5. Mathematical Reproducibility Conclusion

The reported performance of `STRAT_242` ($144.40 ending equity, +0.1092%/day mean daily return, 1,580 trades) is **100% mathematically and programmatically reproducible** from the code and data. There is zero calculation defect, no memory corruption, and no discrepancy between individual trade-level PnL and aggregate portfolio marks.

However, as revealed in the subsequent execution cost audit ([EXECUTION_COST_FORENSIC_AUDIT.md](file:///d:/quantum-multi-agent/audit/strategy_research/post_300_review/EXECUTION_COST_FORENSIC_AUDIT.md)), this mathematical reproducibility is contingent upon the baseline assumption of 8.0 bps round-trip fees on aggressive market orders.
