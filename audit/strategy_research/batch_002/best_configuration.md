# Best Strategy Configuration Specification — `BATCH_002`

- **Strategy ID:** `STRAT_134`
- **Version:** `1.0.0`
- **Deterministic Config Hash:** `858816599bacc574`
- **Experiment ID:** `EXP_B002_STRAT_134_85881659`
- **Backtest Result Artifact:** `data_backtest/batch_002/results/STRAT_134_result.json`
- **Configuration Artifact:** `data_backtest/batch_002/configurations/STRAT_134.json`
- **Manifest Artifact:** `data_backtest/manifests/EXP_B002_STRAT_134_85881659_manifest.json`

---

## 1. Quantitative Hypothesis & Mechanism

> Batch 2 Exploitation (STRAT_061 refinement): 5-asset pool, 1h flush <= -85.0 bps, margin >= 0.22, p0 <= 0.27, TP=3.0s, SL=1.15s.

- **Applicable Assets:** `DOGEUSDT, SOLUSDT, ADAUSDT, XRPUSDT, LINKUSDT`
- **Per-Asset Executed Trade Counts:** `{"DOGEUSDT": 298, "SOLUSDT": 414, "ADAUSDT": 320, "XRPUSDT": 411, "LINKUSDT": 183}`

---

## 2. Exact Declarative Parameters

```json
{
  "strategy_id": "STRAT_134",
  "version": "1.0.0",
  "batch_id": "batch_002",
  "family": "LIQUIDITY_MICROSTRUCTURE",
  "hypothesis": "Batch 2 Exploitation (STRAT_061 refinement): 5-asset pool, 1h flush <= -85.0 bps, margin >= 0.22, p0 <= 0.27, TP=3.0s, SL=1.15s.",
  "parent_strategy_id": "STRAT_061",
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
    "htf_return_max_bps": -85.0,
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
    "max_symbol_exposure_pct": 0.4,
    "max_total_exposure_pct": 1.1,
    "max_leverage": 2.0,
    "max_concurrent_positions": 4,
    "min_notional_usdt": 5.0,
    "fee_tier": "maker_passive"
  },
  "config_hash": "858816599bacc574"
}
```

---

## 3. Verified Performance & Cost Attribution (`$100.00 USD` Initial Capital)

| Metric | Verified Value |
| :--- | :--- |
| **Initial Portfolio Equity** | `$100.00 USD` |
| **Ending Portfolio Equity** | **`$136.16 USD`** |
| **Net Cumulative Portfolio Return** | **`+36.16%`** |
| **Arithmetic Mean Net Daily Return** | **`+0.0920% / day`** |
| **Geometric Mean Net Daily Return** | **`+0.0844% / day`** |
| **Median Net Daily Return** | `+0.0000% / day` |
| **95% Bootstrap Confidence Interval (Daily)** | `[-0.0151%, +0.2191%]` |
| **Gross Expectancy per Trade** | `+14.60 bps` |
| **Net Expectancy per Trade (After All Costs)** | **`+6.50 bps`** |
| **Profit Factor** | **`1.092`** |
| **Win Rate (Net)** | `37.27%` |
| **Annualized Sharpe / Sortino** | `1.424` / `1.267` |
| **Maximum Portfolio Drawdown (MDD)** | **`15.30%`** (Hard ceiling <= 30.0%) |
| **Mean Underwater Drawdown** | **`4.59%`** (Target < 10.0%) |
| **Median Underwater Drawdown** | `3.45%` |
| **Recovery Factor** | `2.364` |
| **Candidate Signals / Executed Trades** | `1805` / `1626` (`90.1%` fill) |
| **Missed Trades (Min Notional $5 / Capacity)** | `0` / `179` |
| **Total Execution Costs (Fees / Funding / Slippage)** | `$56.51` (`$55.81` / `$0.70` / `$0.00`) |
| **Walk-Forward Fold Consistency** | `3/4` folds positive (`{"fold_1": 2.83, "fold_2": 8.21, "fold_3": 30.39, "fold_4": -5.86}`) |
