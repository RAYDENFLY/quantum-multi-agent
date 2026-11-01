# QUANTUM PHASE 5.5.0.6: THREE-TRACK RESEARCH COMPARISON MATRIX

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-01 21:09:14 UTC`  
**Associated Deliverable:** Workstream A (DEC_01 Comparison Matrix)  

---

## 1. COMPREHENSIVE THREE-TRACK COMPARISON TABLE

| Dimension | Track 1: Predictive Target Validation | Track 2: Re-Anchored Economic Evaluation | Track 3: Independent Strategy Development |
|---|---|---|---|
| **1. Primary Question** | Does model predict frozen labels above chance? | Does model provide tradeable alpha under re-anchored brackets? | Can model filter trades within an algorithmic strategy? |
| **2. Frozen Labels** | Directly evaluated as ground truth. | Unused for economic PnL; historical context only. | Completely decoupled; used only as historical training signal. |
| **3. Frozen Classifier** | Evaluated for classification calibration. | Ingested as directional probability filter. | Ingested as directional probability filter. |
| **4. Entry Reference** | Fixed at close[i]. | Execution fill at open[i+1] with adverse slippage. | Execution fill at open[i+1] with dynamic order logic. |
| **5. Exit Reference** | First touch of close[i] +/- 1.5 sigma brackets. | First touch of open[i+1] +/- 1.5 sigma brackets. | Trailing stops, dynamic ATR bands, time exits. |
| **6. Economic Costs** | None (Frictionless statistical metrics). | Explicit taker fees, spread, volatility, impact. | Explicit taker fees, spread, volatility, impact. |
| **7. Funding** | None. | Discrete 8h settlement cash flows modeled. | Discrete 8h settlement cash flows modeled. |
| **8. Parameter Selection** | Zero new parameters. | Zero new parameters (inherits 1.5 sigma). | High (Trailing multipliers, profit targets, hold time). |
| **9. Primary Estimand** | Balanced Accuracy, Log Loss, AU-RCC. | Expected Net Return per Trade ($E[R_{\text{net}}]$). | Portfolio Sharpe, Sortino, Max Drawdown. |
| **10. Valid Conclusion** | Model has statistically significant predictive skill. | Model signals have economic utility under re-anchored execution. | The combined trading system is economically viable. |
| **11. Invalid Conclusion** | Model is profitable in live trading. | The original close-anchored label payoff was validated. | Model alone generated the alpha (ignores exit policy). |

---

## 2. SYNTHESIS AND STRUCTURAL CONCLUSION

- Track 1 is **FROZEN** (Phase 5.3/5.4).
- Track 2 represents **Alternative B**.
- Track 3 represents **Alternative C**.
- These represent different estimands and should be executed sequentially, never conflated into a single claim.
