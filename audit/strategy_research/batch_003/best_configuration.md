# Best Strategy Configuration Specification — `BATCH_003`

- **Strategy ID:** `STRAT_242`
- **Version:** `1.0.0`
- **Deterministic Config Hash:** `b02f17c3e006c2c9`
- **Experiment ID:** `EXP_B003_STRAT_242_b02f17c3`
- **Backtest Result Artifact:** `data_backtest/batch_003/results/STRAT_242_result.json`
- **Configuration Artifact:** `data_backtest/batch_003/configurations/STRAT_242.json`
- **Manifest Artifact:** `data_backtest/manifests/EXP_B003_STRAT_242_b02f17c3_manifest.json`

---

## 1. Quantitative Hypothesis & Mechanism

> Batch 3 Local Surface Refinement of STRAT_134: margin=0.22, htf_max=-93.0 bps, TP=3.0s, SL=1.15s, H=20b, risk=2.40%.

- **Applicable Assets:** `DOGEUSDT, SOLUSDT, ADAUSDT, XRPUSDT, LINKUSDT`
- **Per-Asset Executed Trade Counts:** `{"DOGEUSDT": 295, "SOLUSDT": 398, "ADAUSDT": 308, "XRPUSDT": 404, "LINKUSDT": 175}`

---

## 2. Exact Declarative Parameters

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
  "required_inputs": [
    "oof_probabilities",
    "candles_5m",
    "microstructure_orderflow",
    "cross_asset_btc"
  ],
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

## 3. Verified Performance & Cost Attribution (`$100.00 USD` Initial Capital)

| Metric | Verified Value |
| :--- | :--- |
| **Initial Portfolio Equity** | `$100.00 USD` |
| **Ending Portfolio Equity** | **`$144.40 USD`** |
| **Net Cumulative Portfolio Return** | **`+44.40%`** |
| **Arithmetic Mean Net Daily Return** | **`+0.1092% / day`** |
| **Geometric Mean Net Daily Return** | **`+0.1004% / day`** |
| **Median Net Daily Return** | `+0.0000% / day` |
| **95% Bootstrap Confidence Interval (Daily)** | `[-0.0073%, +0.2524%]` |
| **Gross Expectancy per Trade** | `+15.42 bps` |
| **Net Expectancy per Trade (After All Costs)** | **`+7.33 bps`** |
| **Profit Factor** | **`1.108`** |
| **Win Rate (Net)** | `37.59%` |
| **Annualized Sharpe / Sortino** | `1.577` / `1.409` |
| **Maximum Portfolio Drawdown (MDD)** | **`16.35%`** (Hard ceiling <= 30.0%) |
| **Mean Underwater Drawdown** | **`4.40%`** (Target < 10.0%) |
| **Median Underwater Drawdown** | `3.30%` |
| **Recovery Factor** | `2.715` |
| **Candidate Signals / Executed Trades** | `1760` / `1580` (`89.8%` fill) |
| **Missed Trades (Min Notional $5 / Capacity)** | `0` / `180` |
| **Total Execution Costs (Fees / Funding / Slippage)** | `$59.88` (`$59.14` / `$0.75` / `$0.00`) |
| **Walk-Forward Fold Consistency** | `3/4` folds positive (`{"fold_1": 5.11, "fold_2": 7.98, "fold_3": 33.79, "fold_4": -4.55}`) |
