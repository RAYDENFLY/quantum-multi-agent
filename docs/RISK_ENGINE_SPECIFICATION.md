# RISK_ENGINE_SPECIFICATION.md: Deterministic Python Risk & Sizing Engine (Agent 4)

## 1. Architectural Mandate: Zero ML Override

**Agent 4 (`RiskEngine`, `src/quantum/risk/engine.py`)** is implemented in **100% deterministic Python**.
* No local ML model probability, expected return prediction, or confidence score can bypass a failed Risk check.
* All 12 risk checks run sequentially in `< 0.4 ms` (Engineering Estimate, Acceptance Target `< 1.0 ms` on reference CPU). If even one check fails, the proposal is marked `REJECTED` (`VETO`), logged to `risk_decisions` with all triggered `veto_reasons`, and never reaches `PaperSimulator`.
* Leverage is treated strictly as a **margin allocation mechanism**, never as a tool to inflate position size beyond the stop-loss risk budget.

---

## 2. Conservative Default Risk Parameters

All parameters below are configurable in the `Settings` workspace and persisted in `app_settings`, initialized to conservative institutional defaults:

| Parameter Key | Default Value | Hard Allowed Range | Description |
| :--- | :---: | :---: | :--- |
| `starting_paper_equity_usdt` | `$10,000.00` | `$1,000 - $1,000,000` | Initial simulated USDT account equity |
| `risk_per_trade_pct` | `0.50%` (`0.005`) | `0.10% - 2.00%` | Max equity lost if initial Stop-Loss is hit (including fees & slippage) |
| `max_concurrent_positions` | `3` | `1 - 8` | Max simultaneous open paper positions + working entry limit orders |
| `max_symbol_exposure_pct` | `15.0%` (`0.15`) | `5.0% - 30.0%` | Max notional value on a single symbol as % of total equity |
| `max_total_exposure_pct` | `45.0%` (`0.45`) | `10.0% - 100.0%` | Max aggregate notional across all open positions (`0.45` = max `0.45x` account-wide notional by default, configurable up to `1.50x`) |
| `max_leverage_per_position` | `3.0x` | `1.0x - 5.0x` | Hard ceiling on isolated position leverage |
| `max_daily_loss_pct` | `2.50%` (`0.025`) | `1.0% - 5.0%` | Rolling UTC-day realized + unrealized drawdown circuit breaker |
| `max_total_drawdown_pct` | `8.00%` (`0.08`) | `3.0% - 15.0%` | High-water-mark peak-to-trough equity circuit breaker |
| `min_net_reward_risk` | `1.80` | `1.50 - 4.00` | Minimum blended TP reward to SL risk **after deducting estimated fees & slippage** |
| `max_spread_bps` | `12.0 bps` | `3.0 - 25.0 bps` | Maximum live L1 bid-ask spread at risk evaluation time |
| `max_estimated_slippage_bps` | `10.0 bps` | `2.0 - 25.0 bps` | Maximum L2 book-walk slippage for the calculated order size |
| `loss_streak_cooldown_count` | `3 consecutive losses` | `2 - 5` | Triggers mandatory desk-wide cooldown (`60 minutes` default) |
| `per_symbol_loss_cooldown_min` | `45 minutes` | `15 - 240 min` | Blocks re-entering the same symbol immediately after a stopped-out trade |
| `max_signal_age_ms` | `5,000 ms` | `1,000 - 15,000 ms` | Max elapsed time between `snapshot_timestamp_ms` and risk evaluation (tighter 5s window enabled by `<10ms` local CPU ML inference) |

---

## 3. Exact Position Sizing & Leverage Mathematics

Given an approved `SniperOutput` proposal with `entry_price` ($P_{\text{entry}}$) and `stop_loss` ($P_{\text{stop}}$), `RiskEngine` calculates position size in four deterministic steps:

### Step 1: Effective Stop Distance (Including Fee & Slippage Drag)
Let:
* $\Delta P_{\text{raw}} = |P_{\text{entry}} - P_{\text{stop}}|$
* $f_{\text{entry}} = \text{maker\_fee\_rate}$ (if `LIMIT`) or $\text{taker\_fee\_rate}$ (if `MARKET`)
* $f_{\text{exit}} = \text{taker\_fee\_rate}$ (stop-losses always execute as `STOP_MARKET` takers)
* $s_{\text{est}}$ = estimated one-way slippage fraction from walking the live L2 order book (`bps / 10000`)

The all-in loss per unit of base contract if stopped out is:
$$\text{LossPerUnit}_{\text{USDT}} = \Delta P_{\text{raw}} + P_{\text{entry}} \cdot (f_{\text{entry}} + s_{\text{est}}) + P_{\text{stop}} \cdot (f_{\text{exit}} + s_{\text{est}})$$

### Step 2: Risk-Budgeted Quantity ($Q_{\text{risk}}$)
With current total account equity $E_{\text{current}}$ (`balance + unrealized_pnl`):
$$\text{RiskBudget}_{\text{USDT}} = E_{\text{current}} \times \text{risk\_per\_trade\_pct}$$
$$Q_{\text{risk}} = \frac{\text{RiskBudget}_{\text{USDT}}}{\text{LossPerUnit}_{\text{USDT}}}$$

### Step 3: Exposure & Margin Caps ($Q_{\text{capped}}$)
The raw risk-budgeted quantity is clamped down by three portfolio ceilings:
1. **Single-Symbol Notional Cap**:
   $$Q_{\text{sym\_cap}} = \frac{E_{\text{current}} \times \text{max\_symbol\_exposure\_pct}}{P_{\text{entry}}}$$
2. **Remaining Portfolio Notional Cap**:
   $$Q_{\text{port\_cap}} = \frac{\max\left(0,\; (E_{\text{current}} \times \text{max\_total\_exposure\_pct}) - \sum \text{Notional}_{\text{open}}\right)}{P_{\text{entry}}}$$
3. **Available Free Margin Cap (at `max_leverage_per_position` $L_{\max}$, reserving 20% safety buffer)**:
   $$Q_{\text{margin\_cap}} = \frac{(0.80 \times \text{AvailableMargin}_{\text{USDT}}) \times L_{\max}}{P_{\text{entry}}}$$

### Step 4: Lot-Step Rounding & Contract Constraints
$$Q_{\text{final}} = \left\lfloor \frac{\min(Q_{\text{risk}}, Q_{\text{sym\_cap}}, Q_{\text{port\_cap}}, Q_{\text{margin\_cap}})}{\text{lot\_step}} \right\rfloor \times \text{lot\_step}$$

If $Q_{\text{final}} < \text{min\_order\_qty}$ or $Q_{\text{final}} \times P_{\text{entry}} < \text{min\_notional\_usdt}$, the proposal is vetoed with `VETO_BELOW_MIN_NOTIONAL`.

---

## 4. Net Reward-to-Risk ($R:R_{\text{net}}$) Verification

`SNIPER` estimates gross $R:R$ and expected net $R$, and `RiskEngine` independently verifies **net $R:R$ after fees and slippage**:
Let the blended gross target distance be:
$$\Delta P_{\text{tp\_blended}} = w_{\text{tp1}} |P_{\text{tp1}} - P_{\text{entry}}| + (1 - w_{\text{tp1}}) |P_{\text{tp2}} - P_{\text{entry}}|$$
The net profit per unit at target is:
$$\text{NetGainPerUnit}_{\text{USDT}} = \Delta P_{\text{tp\_blended}} - P_{\text{entry}} \cdot (f_{\text{entry}} + s_{\text{est}}) - P_{\text{tp\_blended}} \cdot f_{\text{maker}}$$
$$R:R_{\text{net}} = \frac{\text{NetGainPerUnit}_{\text{USDT}}}{\text{LossPerUnit}_{\text{USDT}}}$$

If $R:R_{\text{net}} < \text{min\_net\_reward\_risk}$ (configurable default `1.80`, tuned and validated on validation folds to guarantee trade frequency $\ge 15\text{ trades/month}$), the proposal is rejected with `VETO_INSUFFICIENT_NET_RR`.

---

## 5. The 12-Point Deterministic Risk Checklist

Every proposal is evaluated against all 12 rules in order:

| Check # | Check Code | Pass Condition | Veto Code on Failure |
| :---: | :--- | :--- | :--- |
| **1** | `SIGNAL_FRESHNESS` | `now_ms - snapshot_timestamp_ms <= max_signal_age_ms` (`5,000 ms`) AND live `mark_price` has not drifted $> 0.25 \times |P_{\text{entry}} - P_{\text{stop}}|$ from `reference_mark_price`. | `VETO_STALE_SIGNAL` |
| **2** | `DRAWDOWN_CIRCUIT_BREAKER` | Current peak-to-trough drawdown $< \text{max\_total\_drawdown\_pct}$ (`8.0%`). | `VETO_MAX_DRAWDOWN_BREACHED` |
| **3** | `DAILY_LOSS_LIMIT` | UTC-day realized + unrealized loss + new trade $\text{RiskBudget}_{\text{USDT}} \le E_{\text{day\_start}} \times \text{max\_daily\_loss\_pct}$ (`2.5%`). | `VETO_DAILY_LOSS_LIMIT` |
| **4** | `LOSS_STREAK_COOLDOWN` | Desk is not in an active loss-streak cooldown window, and `instrument_id` was not stopped out within `per_symbol_loss_cooldown_min` (`45m`). | `VETO_COOLDOWN_ACTIVE` |
| **5** | `MAX_CONCURRENT_POSITIONS` | `len(open_positions) + len(open_entry_orders) < max_concurrent_positions` (`3`) AND no existing open position/order on the same `symbol` (even on the other exchange). | `VETO_MAX_POSITIONS_OR_DUPLICATE` |
| **6** | `STOP_GEOMETRY_VALID` | Stop-loss is on the correct side of entry and live mark price, and stop distance is within `[0.4 * ATR_15m, 4.0 * ATR_15m]`. | `VETO_INVALID_STOP_GEOMETRY` |
| **7** | `MAX_SPREAD` | Live `ticker.spread_bps <= max_spread_bps` (`12.0 bps`). | `VETO_EXCESSIVE_SPREAD` |
| **8** | `LOT_STEP_AND_MIN_NOTIONAL` | $Q_{\text{final}} \ge \text{min\_order\_qty}$ and $Q_{\text{final}} \times P_{\text{entry}} \ge \text{min\_notional\_usdt}$. | `VETO_BELOW_MIN_NOTIONAL` |
| **9** | `MAX_SLIPPAGE` | L2 order-book depth walk for quantity $Q_{\text{final}}$ yields estimated slippage $\le \text{max\_estimated\_slippage\_bps}$ (`10.0 bps`) and fills within top-50 book levels. | `VETO_EXCESSIVE_BOOK_SLIPPAGE` |
| **10** | `MIN_NET_RR` | $R:R_{\text{net}} \ge \text{min\_net\_reward\_risk}$ (`1.80`). | `VETO_INSUFFICIENT_NET_RR` |
| **11** | `MAX_EXPOSURE_AND_LEVERAGE` | Post-trade symbol exposure $\le 15\%$, total exposure $\le 45\%$, and effective isolated leverage $\le 3.0\text{x}$. | `VETO_EXPOSURE_OR_LEVERAGE_CAP` |
| **12** | `LIQUIDATION_BUFFER` | Estimated isolated liquidation price is at least $2.5 \times |P_{\text{entry}} - P_{\text{stop}}|$ away from $P_{\text{entry}}$ (ensuring the hard stop-loss always triggers long before liquidation). | `VETO_LIQUIDATION_TOO_CLOSE` |
