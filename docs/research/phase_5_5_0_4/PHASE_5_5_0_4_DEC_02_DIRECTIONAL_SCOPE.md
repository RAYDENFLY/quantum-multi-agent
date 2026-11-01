# QUANTUM PHASE 5.5.0.4: DEC_02 DIRECTIONAL TRADING SCOPE BRIEF

**Decision ID:** `DEC_02`  
**Title:** Directional Trading Scope  
**Governance Status:** `PENDING_HUMAN_DECISION`  
**Execution Blocking:** `YES`  

---

## 1. OPTIONS AND METHODOLOGICAL IMPLICATIONS

The frozen B4 LightGBM models predict three classes: $+1$ (upward excursion), $-1$ (downward excursion), and $0$ (neutral/holding).
The supervisor must decide the directional deployment scope:
1. **Long-Only:** Strictly execute Class $+1$ signals when calibrated confidence exceeds the selective threshold.
2. **Short-Only:** Strictly execute Class $-1$ signals when calibrated confidence exceeds the selective threshold.
3. **Bidirectional:** Execute both Long and Short trades with mandatory separate reporting.

---

## 2. CRITICAL ASYMMETRIES BETWEEN LONGS AND SHORTS

Cryptocurrency perpetual futures exhibit structural market asymmetries that prevent treating Long and Short trades as symmetric mirror images:
1. **Macro Trend Bias:** The historical dataset (October 2023 to October 2026) covers substantial crypto bull regimes (Bitcoin rising from $27k to $73k+). A combined PnL metric could show positive overall expectancy solely because Long trades rode the secular bull trend, masking severe, persistent losses on Short trades.
2. **Funding Rate Asymmetry:** In bull regimes, perpetual funding rates are persistently positive ($f_t > 0$). Long positions pay financing drag ($CF_t < 0$), whereas Short positions receive financing credits ($CF_t > 0$). Conversely, in bear markets ($f_t < 0$), Shorts pay Longs.
3. **Volatility & Liquidity Dynamics:** Downward market excursions are frequently characterized by rapid leverage liquidations and violent orderbook depth depletion, creating higher slippage on Short exits (buying to cover) during panic wicks.

---

## 3. MANDATORY INDEPENDENT REPORTING PROTOCOL

If Bidirectional execution is selected, the research design must strictly mandate:
- Separate PnL curves, Sharpe ratios, win rates, and drawdowns for Long-Only trades.
- Separate PnL curves, Sharpe ratios, win rates, and drawdowns for Short-Only trades.
- Combined portfolio PnL curves and net equity metrics.
- **Governance Rule:** If Short trades fail to achieve positive net expectancy after transaction costs at Gate 2, the system must not mask those losses behind Long trade profits; Short execution must be deactivated.

---

## 4. SUPERVISOR RECOMMENDATION

- **Recommendation:** Approve `Bidirectional execution with mandatory separate PnL reporting` for research exploration. If Short trades fail independent validation, restrict deployment to `Long-Only`.
- **Status:** `PENDING_HUMAN_DECISION`. Awaiting supervisor selection.
