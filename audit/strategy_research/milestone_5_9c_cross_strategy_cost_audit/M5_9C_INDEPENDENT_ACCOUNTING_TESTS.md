# QUANTUM - MILESTONE 5.9C
## INDEPENDENT ACCOUNTING TESTS & MATHEMATICAL SPECIFICATIONS

---

### 1. Document Overview
- **Document Identifier:** `audit/strategy_research/milestone_5_9c_cross_strategy_cost_audit/M5_9C_INDEPENDENT_ACCOUNTING_TESTS.md`
- **Research Branch:** `research/quantum-next-3pct`
- **Scope:** Independent mathematical proofs, turnover identities, fee asymmetry formulas, and position sizing accounting constraints for cross-strategy cost validation.
- **Audited Milestones:** M3, M4, M5.2, M5.4, M5.5, M5.6, M5.7, M5.8A, M5.8B, M5.9, M5.9B.

---

### 2. Core Accounting Identities & Formulas

#### 2.1 Asymmetric Exit Notional Scaling
In linear perpetual futures (USDT settled), position notional is not static. When price moves, the exit notional scales with the gross price excursion:

$$\text{Gross Return: } R_{\text{gross}} = d \cdot \frac{P_{\text{exit}} - P_{\text{entry}}}{P_{\text{entry}}}$$

$$\text{Exit Notional: } N_{\text{exit}} = N_{\text{entry}} \cdot \left(1 + d \cdot R_{\text{gross}}\right) = Q \cdot P_{\text{exit}}$$

Where:
- $d \in \{+1, -1\}$ denotes trade direction ($+1$ for Long, $-1$ for Short).
- $Q$ is the executed quantity ($Q = N_{\text{entry}} / P_{\text{entry}}$).
- $N_{\text{entry}}$ is the entry notional in USDT.
- $N_{\text{exit}}$ is the exit notional in USDT.

#### 2.2 Asymmetric Fee Accounting
Because exchange fees are charged as a percentage of executed notional at the time of each fill, winning trades pay higher exit fees, while losing trades pay lower exit fees:

$$C_{\text{fee, entry}} = c_{\text{fee, entry}} \cdot N_{\text{entry}}$$

$$C_{\text{fee, exit}} = c_{\text{fee, exit}} \cdot N_{\text{exit}} = c_{\text{fee, exit}} \cdot N_{\text{entry}} \cdot (1 + d \cdot R_{\text{gross}})$$

$$\text{Total Fee Drag: } C_{\text{fee}} = N_{\text{entry}} \cdot \left[ c_{\text{fee, entry}} + c_{\text{fee, exit}} \cdot (1 + d \cdot R_{\text{gross}}) \right]$$

For a symmetrical fee schedule ($c_{\text{fee, entry}} = c_{\text{fee, exit}} = c_{\text{fee}}$):
$$C_{\text{fee}} = c_{\text{fee}} \cdot N_{\text{entry}} \cdot \left(2 + d \cdot R_{\text{gross}}\right)$$

#### 2.3 Execution Friction (Spread & Slippage)
Execution frictions are modeled as per-leg penalties on traded notional:

$$C_{\text{spread}} = \frac{s_{\text{spread}}}{2} \cdot \left(N_{\text{entry}} + N_{\text{exit}}\right)$$

$$C_{\text{slippage}} = s_{\text{slip}} \cdot \left(N_{\text{entry}} + N_{\text{exit}}\right)$$

$$C_{\text{adverse}} = a_{\text{adverse}} \cdot N_{\text{entry}}$$

Where $a_{\text{adverse}}$ applies exclusively to resting maker limit orders subject to toxic flow.

#### 2.4 Signed Perpetual Funding Cash Flow
Funding settlement occurs at discrete timestamps $t_{\text{settle}} \in \{00:00, 08:00, 16:00\text{ UTC}\}$:

$$\text{Settlement Condition: } t_{\text{entry}} < t_{\text{settle}} \le t_{\text{exit}}$$

$$CF_{\text{funding}} = -d \cdot \sum_{k=1}^{K} N_{t_k} \cdot r_{\text{funding}, k}$$

Where:
- $r_{\text{funding}, k} > 0$: Long positions pay shorts ($CF < 0$), Short positions receive from longs ($CF > 0$).
- If funding data is unavailable in the historical dataset, $CF_{\text{funding}} \equiv 0.0$ and is flagged as `FUNDING_DATA_UNAVAILABLE`.

#### 2.5 Realized Net PnL Identity
$$\text{PnL}_{\text{gross}} = N_{\text{entry}} \cdot R_{\text{gross}} = Q \cdot d \cdot (P_{\text{exit}} - P_{\text{entry}})$$

$$\text{PnL}_{\text{net}} = \text{PnL}_{\text{gross}} - C_{\text{fee}} - C_{\text{spread}} - C_{\text{slippage}} - C_{\text{adverse}} + CF_{\text{funding}}$$

$$\text{Net Return: } R_{\text{net}} = \frac{\text{PnL}_{\text{net}}}{N_{\text{entry}}}$$

---

### 3. Turnover & Exposure Identities

#### 3.1 Single-Leg Directional Strategy (e.g. HYP-01 / Portfolio A)
For each completed trade with entry notional $N_{\text{entry}}$:

$$\text{Turnover}_{\text{single-leg}} = N_{\text{entry}} + N_{\text{exit}} \approx 2 \cdot N_{\text{entry}}$$

$$\text{Turnover Multiplier: } M_{\text{single}} \approx 2.0\text{x}$$

Across $N_{\text{trades}}$ trades:
$$\text{Total Turnover}_{\text{gross}} = \sum_{i=1}^{N_{\text{trades}}} (N_{\text{entry}, i} + N_{\text{exit}, i})$$

For Portfolio A ($3,562$ trades, average entry notional $\$24.99$):
$$\text{Total Turnover} \approx 3,562 \times 2 \times \$24.99 \approx \$178,028$$
On an initial account equity of $\$100$, the strategy turned over its portfolio **$1,780\times$** in 118 days, generating massive friction drag ($\$57.29$ in fees).

#### 3.2 Two-Leg Dollar-Neutral Strategy (e.g. Track C Cointegration Pairs)
For each pair trade composed of Leg 1 ($L_1$, Long) and Leg 2 ($L_2$, Short), each allocated $N_{\text{leg}} = \$50.00$:

$$N_{\text{entry, total}} = N_{\text{entry}, L_1} + N_{\text{entry}, L_2} = \$50.00 + \$50.00 = \$100.00$$

$$\text{Turnover}_{\text{two-leg}} = N_{\text{entry}, L_1} + N_{\text{exit}, L_1} + N_{\text{entry}, L_2} + N_{\text{exit}, L_2} \approx 4 \cdot N_{\text{leg}} = 2 \cdot N_{\text{entry, total}}$$

$$\text{Turnover Multiplier relative to leg size: } M_{\text{two-leg}} = 4.0\text{x}$$

For Track C SOL/LTC ($19$ trades, $38$ leg executions):
$$\text{Total Turnover} \approx 19 \times 4 \times \$50.00 = \$3,800.00$$
On a $\$100$ equity base, $19$ pair trades turned over **$38\times$ the account equity**, explaining why even $19$ trades generated $\$1.30$ to $\$4.47$ in friction against only $\$0.37$ in gross alpha.

---

### 4. Position Sizing & Account Starvation Ruin Threshold

#### 4.1 Strict Unlevered Exposure Constraint
$$\Lambda_t = \frac{\sum_{j=1}^{N_{\text{active}, t}} |\text{Notional}_{j, t}|}{\text{Equity}_t} \le 1.00000 \quad \forall t$$

Individual position cap:
$$\text{Notional}_{j, t} \le w_{\text{max}} \cdot \text{Equity}_t$$

Where:
- For Directional HYP-01: $w_{\text{max}} = 0.25$, $N_{\text{max}} = 4$ concurrent positions $\implies \Lambda_{\text{max}} = 4 \times 0.25 = 1.00\text{x}$.
- For Track C Pairs: $w_{\text{max}} = 0.50$, $N_{\text{max}} = 2$ legs ($1$ pair) $\implies \Lambda_{\text{max}} = 2 \times 0.50 = 1.00\text{x}$.

#### 4.2 Account Starvation Ruin Limit
Exchange rules mandate a minimum notional order size $N_{\text{min}} = \$5.0000\text{ USDT}$.
When an account experiences drawdowns, the required position size $N_{\text{req}} = w_{\text{max}} \cdot \text{Equity}_t$ shrinks:

$$\text{Order Rejected if: } w_{\text{max}} \cdot \text{Equity}_t < N_{\text{min}}$$

$$\text{Terminal Starvation Ruin Equity: } \text{Equity}_{\text{starvation}} = \frac{N_{\text{min}}}{w_{\text{max}}}$$

- For $w_{\text{max}} = 0.25$ (Portfolio A):
  $$\text{Equity}_{\text{starvation}} = \frac{\$5.00}{0.25} = \mathbf{\$20.0000\text{ USDT}}$$
- For $w_{\text{max}} = 0.50$ (Track C):
  $$\text{Equity}_{\text{starvation}} = \frac{\$5.00}{0.50} = \mathbf{\$10.0000\text{ USDT}}$$

When equity drops below $\text{Equity}_{\text{starvation}}$, the trading engine is mathematically halted due to exchange minimum notional rejection. In Portfolio A, terminal equity reached $\$19.9654$, immediately triggering permanent starvation halt.

---

### 5. Verification Invariants for Milestone 5.9C Test Suite

The test suite `tests/unit/test_milestone_5_9c_cost_audit.py` validates the following mathematical assertions:
1. **Gross Leverage Invariant:** $\Lambda_t \le 1.00000$ across all historical position sizing tables.
2. **Turnover Multiplier Invariant:** $M_{\text{single-leg}} = 2.0\text{x}$ and $M_{\text{two-leg}} = 4.0\text{x}$.
3. **Exit Notional Scaling Invariant:** $N_{\text{exit}} = N_{\text{entry}}(1 + d \cdot R_{\text{gross}})$ to $10^{-6}$ precision.
4. **Zero-Fee Upper Bound Invariant:** For Track C SOL/LTC, $\text{Return}_{\text{zero-fee}} = +0.3662\%$ over 365 days ($+0.0010\%/\text{day}$), which is strictly $< 3.00\%/\text{day}$.
5. **Holdout Virginity Invariant:** No timestamp $\ge 1,793,491,200,000\text{ ms}$ exists in any historical trading ledger or audit file.
