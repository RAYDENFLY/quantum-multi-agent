# QUANTUM PHASE 5.5: BACKTEST ENGINE TECHNICAL SPECIFICATION

**Document Version:** 1.0.0-STAGE-0-GOVERNANCE  
**Publication Timestamp:** 2026-11-02 17:15:00 UTC  
**Scope:** Architectural and Mathematical Specification for `quantum.backtesting`  

**Authoritative Dossier References:**
- [PHASE_5_5_0_8_LONG_SHORT_ACCOUNTING_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_LONG_SHORT_ACCOUNTING_AUDIT.md)
- [PHASE_5_5_0_8_TRANSACTION_COST_SPECIFICATION.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_TRANSACTION_COST_SPECIFICATION.md)
- [PHASE_5_5_0_8_FUNDING_ELIGIBILITY_AUDIT.md](file:///d:/quantum-multi-agent/docs/research/phase_5_5_0_8/PHASE_5_5_0_8_FUNDING_ELIGIBILITY_AUDIT.md)

---

## 1. SIMULATED CLOCK SPECIFICATION

### Contracts Modification
- In `src/quantum/agents/contracts.py`:
  - `RiskInput`: Add `eval_timestamp_ms: Optional[int] = Field(default=None)`
  - `BankerInput`: Add `eval_timestamp_ms: Optional[int] = Field(default=None)`
  - `PositionExecutionEvent`: Timestamp already exists as `timestamp_ms: int`.

### Clock Resolution Logic
```python
now_ms = input_data.eval_timestamp_ms if input_data.eval_timestamp_ms is not None else int(time.time() * 1000)
```

### Safety Gate Semantics
- **Signal Freshness (Gate 1):**
  - $\Delta t = 	ext{now\_ms} - 	ext{snapshot\_timestamp\_ms}$
  - If $\Delta t < 0$: Veto `VETO_FUTURE_TIMESTAMP`.
  - If $0 \le \Delta t \le 15,000$ ms: PASS `SIGNAL_FRESHNESS`.
  - If $\Delta t > 15,000$ ms: Veto `VETO_STALE_SIGNAL`.
- **Loss Streak Cooldown (Gate 4):**
  - $\Delta t_{\text{loss}} = 	ext{now\_ms} - 	ext{last\_loss\_timestamp\_ms}$
  - If $\Delta t_{\text{loss}} < 0$: Veto future timestamp.
  - If $\Delta t_{\text{loss}} < 	ext{cooldown\_ms}$: Veto `VETO_LOSS_STREAK_COOLDOWN`.
  - If $\Delta t_{\text{loss}} \ge 	ext{cooldown\_ms}$: PASS.

---

## 2. REFERENCE-PRICE PNL ACCOUNTING MATHEMATICAL SPECIFICATION

Module: `src/quantum/backtesting/accounting.py`

### 1. Variables & Conventions
- Direction indicator: $d = +1$ (LONG), $d = -1$ (SHORT).
- Quantity: $Q > 0$ (contracts or base units).
- Entry price: $P_{\text{entry}} > 0$.
- Exit price: $P_{\text{exit}} > 0$.
- Taker fee rate: $c_{\text{fee}} \ge 0$ (e.g. $0.0015$ for $15$ bps).
- Slippage rate per leg: $c_{\text{slip}} \ge 0$ (e.g. $0.0002$ for $2$ bps half-spread).

### 2. Notional Values
$$N_{\text{entry}} = Q \cdot P_{\text{entry}}$$
$$N_{\text{exit}} = Q \cdot P_{\text{exit}} = N_{\text{entry}} \cdot (1 + d \cdot R_{\text{gross}})$$
where $R_{\text{gross}} = d \cdot \left(\frac{P_{\text{exit}} - P_{\text{entry}}}{P_{\text{entry}}}\right)$.

### 3. Frictional Costs
$$C_{\text{fees}} = c_{\text{fee}} \cdot (N_{\text{entry}} + N_{\text{exit}})$$
$$C_{\text{exec}} = c_{\text{slip}} \cdot (N_{\text{entry}} + N_{\text{exit}})$$
$$C_{\text{total}} = C_{\text{fees}} + C_{\text{exec}} = (c_{\text{fee}} + c_{\text{slip}}) \cdot (N_{\text{entry}} + N_{\text{exit}})$$

### 4. Signed Funding Cash Flows
For settlements $k$ crossed during trade duration ($t_{\text{entry}} < t_{\text{settle}, k} \le t_{\text{exit}}$):
$$CF_{\text{funding}} = - d \cdot \sum_{k} f_k \cdot N_{\text{settle}, k}$$
Convention: $CF_{\text{funding}} > 0$ is income received; $CF_{\text{funding}} < 0$ is cost paid.

### 5. Net Realized Payoff
$$\text{PnL}_{\text{gross}} = d \cdot Q \cdot (P_{\text{exit}} - P_{\text{entry}}) = N_{\text{entry}} \cdot R_{\text{gross}}$$
$$\text{PnL}_{\text{net}} = \text{PnL}_{\text{gross}} - C_{\text{total}} + CF_{\text{funding}}$$
$$R_{\text{net}} = \frac{\text{PnL}_{\text{net}}}{N_{\text{entry}}}$$
$$\text{bps}_{\text{net}} = R_{\text{net}} \cdot 10,000$$

---

## 3. DISCRETE-EVENT ENGINE ARCHITECTURE

Module: `src/quantum/backtesting/engine.py`

### Event Loop Specification:
1. `SignalEvent`: Generated at bar $i$ completion ($t_i$).
2. `RiskEvaluationEvent`: Evaluated at $t_{i+1}$ with simulated clock.
3. `EntryFillEvent`: Position filled at $P_{\text{entry,ref}} = \text{open}[i+1]$.
4. `BarrierEvaluationEvent`: Forward 12 candles ($k = i+1, \dots, i+12$).
   - Upper barrier: $U = P_{\text{entry,ref}} \cdot (1 + 1.5\sigma_t)$
   - Lower barrier: $L = P_{\text{entry,ref}} \cdot (1 - 1.5\sigma_t)$
   - Collision resolution: If both touched in candle $k$, SL triggered first.
5. `ExitFillEvent`: Triggered upon barrier breach or 12-bar timeout.
6. `AccountingEvent`: Calculates final financial ledger metrics.

---
*End of Backtest Engine Technical Specification.*
