# QUANTUM ACCOUNTING AUDIT — MILESTONE 5.8A
## Ruin, Minimum Notional & Capital Scale Sensitivity Audit

**Audit Dossier Path:** `audit/strategy_research/milestone_5_8a_survival_accounting/RUIN_AND_MINIMUM_NOTIONAL_AUDIT.md`  
**Execution Timestamp:** 2026-11-03T23:58:00Z  
**Branch:** `research/quantum-next-3pct`  
**Authorizing Mandate:** Milestone 5.8A Terminal Equity & Survival Accounting Protocol  

---

## 1. Executive Summary & Forensic Questions

Milestone 5.8A investigates the exact semantics of the minimum-notional execution halt:
$$\text{Calculated Notional } (\$4.998) < \text{Exchange Minimum } (\$5.00)$$

Specifically, this audit resolves:
1. What does $\$4.998$ represent (order notional, margin, or available cash)?
2. Does the exchange limit apply to position notional or required margin?
3. Did forced liquidation occur?
4. Was the halt an artificial simulator bug or a genuine market constraint?
5. What happens if initial capital is scaled to **$\$1,000$** or **$\$10,000$** under strictly 1.0x unlevered exposure?

### Forensic Findings
```yaml
SEMANTIC_DEFINITION_4.998: CALCULATED_POSITION_ORDER_NOTIONAL ($19.99288 * 0.25)
EXCHANGE_MINIMUM_APPLICATION: ORDER_NOTIONAL (Bybit VIP0 >= 5 USDT Order Value)
FORCED_LIQUIDATION_OCCURRENCE: FALSE (Account Solvent with $19.965 Positive Cash)
HALT_NATURE: REAL-WORLD_MARKET_CONSTRAINT (Risk Weight 0.25 vs Exchange Lot Limit)
CAPITAL_SCALE_SENSITIVITY:
  INIT_$100: Starvation at Day 79-118 (Terminal Equity: $19.965, MDD: 80.03%)
  INIT_$1,000: Starvation at Day 256 (Terminal Equity: $19.965, MDD: 98.00%)
  INIT_$10,000: Starvation at Day 428 (Terminal Equity: $19.982, MDD: 99.80%)
SCALE_VERDICT: Capital scaling merely delays ruin; negative expectancy destroys all capital tiers
```

---

## 2. Minimum-Notional Semantics & Exchange Mechanics

### 2.1 The Derivation of $4.998
In `scripts/independent_survival_accounting.py`:
$$\text{Max Position Weight } (w_{\text{max}}) = 0.25 \quad (\text{Max 4 concurrent positions})$$
$$\text{Portfolio Equity at Halt } (E_{\text{halt}}) = \$19.99288$$
$$\text{Calculated Order Notional } = w_{\text{max}} \cdot E_{\text{halt}} = 0.25 \cdot \$19.99288 = \mathbf{\$4.99822}$$

- **Notional vs Margin:** At 1.0x unlevered exposure, position notional equals required margin ($1.0\times$).
- **Exchange Rule:** Bybit USDT Perpetual Trading Rules enforce:
  $$\text{Minimum Order Value} = 5.00 \text{ USDT Notional}$$
- If an algorithm attempts to submit an order with notional $<\$5.00$, the Bybit API rejects the request with error code `10001: Order value too small`.

### 2.2 Was the Account Liquidated?
- **NO.** Liquidation occurs when equity drops below Maintenance Margin Requirement (MMR).
- At timestamp `1708639800000 ms`, all active positions had already closed at their natural Stop-Loss or Time-Expiration levels.
- Maintenance margin was **$\$0.00$**.
- The account was **100% solvent** with $\$19.99288$ in free cash equity.
- The halt was not an exchange liquidation, but an **operational capital starvation event**.

### 2.3 Strategy Rule vs Simulator Constraint
Could the account have continued trading?
- If the algorithm had relaxed its risk parameters to allocate $100\%$ of its equity to a single trade ($w_{\text{max}} = 1.00$), it could have placed a $\$19.99$ order.
- However, doing so would **violate the strategy's risk mandate** ($w_j \le 0.25$ to prevent single-asset ruin).
- Therefore, the halt was a legitimate operational consequence of the strategy's risk rules interacting with real-world exchange microstructure.

---

## 3. Capital Scale Sensitivity Experiments ($100 vs $1,000 vs $10,000)

To determine whether the ruin event was an artifact of the small initial capital ($\$100$), [`scripts/independent_survival_accounting.py`](file:///d:/quantum-multi-agent/scripts/independent_survival_accounting.py) simulated Portfolio A at higher capital scales under strictly 1.0x unlevered conditions (results stored in [`CAPITAL_SCALE_EXPERIMENTS.csv`](file:///d:/quantum-multi-agent/audit/strategy_research/milestone_5_8a_survival_accounting/CAPITAL_SCALE_EXPERIMENTS.csv)):

| Initial Capital | Terminal Equity | Days Operational | Starvation Halt Triggered? | Total Trades | Maximum Drawdown | Capital Lost |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **$100.00** | **$19.9654** | **79–118 Days** | **YES (Day 118)** | 3,562 | **80.03%** | -$80.03 |
| **$1,000.00** | **$19.9650** | **256 Days** | **YES (Day 256)** | 10,263 | **98.00%** | -$980.03 |
| **$10,000.00** | **$19.9822** | **428 Days** | **YES (Day 428)** | 18,091 | **99.80%** | -$9,980.02 |

```
Capital Depletion Trajectories:
Initial $100   ----[ 118 Days ]----> $19.96 (80.0% Depletion) -> HALT
Initial $1,000 ----[ 256 Days ]----> $19.96 (98.0% Depletion) -> HALT
Initial $10,000---[ 428 Days ]----> $19.98 (99.8% Depletion) -> HALT
```

### The Inescapable Mathematical Law of Negative Expectancy
$$\text{Expected PnL}(N) = N \cdot \text{Notional} \cdot \mathbb{E}[\text{Net Return}]$$

Because causal next-bar execution produces **$\mathbb{E}[\text{Net Return}] = -16.10\text{ bps}$** per trade:
1. Scaling initial capital from $\$100$ to $\$1,000$ does **NOT** rescue the strategy.
2. It simply allows the strategy to execute **10,263 trades instead of 3,562 trades**, bleeding capital continuously over 256 days until equity reaches $\$19.96$.
3. Scaling initial capital to $\$10,000$ results in **18,091 losing trades** over 428 days, producing a catastrophic **$99.80\%$ drawdown**.

---

## 4. Audit Conclusion

1. The $\$4.998$ figure represents **calculated order position notional**, not margin or account balance.
2. The halt was caused by the legitimate interaction of risk rules with exchange lot size constraints, with zero account liquidation.
3. Scaling initial capital proves conclusively that **capital size cannot compensate for negative trade expectancy**. Higher capital simply incurs deeper dollar losses.

**Deliverable Status:** `VERIFIED (MINIMUM NOTIONAL SEMANTICS & SCALE DYNAMICS PROVEN)`
