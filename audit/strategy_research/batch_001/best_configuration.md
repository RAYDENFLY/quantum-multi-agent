# Best Strategy Configuration Specification — `BATCH_001`

- **Strategy ID:** `STRAT_061`
- **Version:** `1.0.0`
- **Deterministic Config Hash:** `63e038a425dfbd55`
- **Experiment ID:** `EXP_B001_STRAT_061_63e038a4`
- **Backtest Result Artifact:** `data_backtest/batch_001/results/STRAT_061_result.json`
- **Configuration Artifact:** `data_backtest/batch_001/configurations/STRAT_061.json`
- **Manifest Artifact:** `data_backtest/manifests/EXP_B001_STRAT_061_63e038a4_manifest.json`

---

## 1. Quantitative Hypothesis & Mechanism

> 93rd-percentile volatility flush climax reclaim.

- **Applicable Assets:** `DOGEUSDT, SOLUSDT, ADAUSDT, XRPUSDT, LINKUSDT, AVAXUSDT`
- **Per-Asset Executed Trade Counts:** `{"DOGEUSDT": 159, "SOLUSDT": 213, "ADAUSDT": 142, "XRPUSDT": 176, "LINKUSDT": 90, "AVAXUSDT": 135}`

---

## 2. Exact Declarative Parameters

```json
{
  "strategy_id": "STRAT_061",
  "version": "1.0.0",
  "batch_id": "batch_001",
  "family": "VOLATILITY_DYNAMICS",
  "hypothesis": "93rd-percentile volatility flush climax reclaim.",
  "parent_strategy_id": null,
  "applicable_assets": [
    "DOGEUSDT",
    "SOLUSDT",
    "ADAUSDT",
    "XRPUSDT",
    "LINKUSDT",
    "AVAXUSDT"
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
    "prob_margin_min": 0.25,
    "p0_neutral_max": 0.45,
    "vol_quantile_min": 0.93,
    "vol_quantile_max": 1.0,
    "vol_expansion_ratio_min": 1.25,
    "rvol_min": 0.0,
    "taker_buy_ratio_min": 0.0,
    "taker_buy_ratio_max": 1.0,
    "wick_rejection_min": 0.0,
    "htf_lookback_bars": 12,
    "htf_return_min_bps": -10000.0,
    "htf_return_max_bps": -60.0,
    "btc_lead_lookback_bars": 6,
    "btc_lead_min_bps": -10000.0,
    "btc_lead_max_bps": 10000.0,
    "order_type": "MARKET",
    "limit_offset_sigma": 0.0,
    "order_timeout_bars": 3,
    "cooldown_bars": 0
  },
  "exit": {
    "tp1_multiplier": 2.6,
    "tp2_multiplier": 3.5,
    "tp1_close_pct": 0.0,
    "sl_multiplier": 1.2,
    "breakeven_ratchet_on_tp1": false,
    "trailing_stop_distance_sigma": 0.0,
    "horizon_bars": 15
  },
  "risk": {
    "initial_equity_usd": 100.0,
    "risk_per_trade_pct": 0.02,
    "max_symbol_exposure_pct": 0.35,
    "max_total_exposure_pct": 1.0,
    "max_leverage": 2.0,
    "max_concurrent_positions": 4,
    "min_notional_usdt": 5.0,
    "fee_tier": "maker_passive"
  },
  "config_hash": "63e038a425dfbd55"
}
```

---

## 3. Verified Performance & Cost Attribution (`$100.00 USD` Initial Capital)

| Metric | Verified Value |
| :--- | :--- |
| **Initial Portfolio Equity** | `$100.00 USD` |
| **Ending Portfolio Equity** | **`$113.88 USD`** |
| **Net Cumulative Portfolio Return** | **`+13.88%`** |
| **Arithmetic Mean Net Daily Return** | **`+0.0381% / day`** |
| **Geometric Mean Net Daily Return** | **`+0.0355% / day`** |
| **Median Net Daily Return** | `+0.0000% / day` |
| **95% Bootstrap Confidence Interval (Daily)** | `[-0.0273%, +0.1176%]` |
| **Gross Expectancy per Trade** | `+12.97 bps` |
| **Net Expectancy per Trade (After All Costs)** | **`+4.87 bps`** |
| **Profit Factor** | **`1.077`** |
| **Win Rate (Net)** | `40.98%` |
| **Annualized Sharpe / Sortino** | `1.009` / `1.021` |
| **Maximum Portfolio Drawdown (MDD)** | **`9.47%`** (Hard ceiling <= 30.0%) |
| **Mean Underwater Drawdown** | **`3.31%`** (Target < 10.0%) |
| **Median Underwater Drawdown** | `2.79%` |
| **Recovery Factor** | `1.465` |
| **Candidate Signals / Executed Trades** | `1035` / `915` (`88.4%` fill) |
| **Missed Trades (Min Notional $5 / Capacity)** | `0` / `120` |
| **Total Execution Costs (Fees / Funding / Slippage)** | `$26.22` (`$25.91` / `$0.31` / `$0.00`) |
| **Walk-Forward Fold Consistency** | `3/4` folds positive (`{"fold_1": -1.52, "fold_2": 2.1, "fold_3": 10.37, "fold_4": 2.81}`) |
