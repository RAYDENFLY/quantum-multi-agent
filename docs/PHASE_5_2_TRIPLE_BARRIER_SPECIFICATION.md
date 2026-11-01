# QUANTUM PHASE 5.2 - TRIPLE-BARRIER LABELING SPECIFICATION

**Author:** Senior Quantitative Research Engineer & Financial ML Scientist  
**Date:** 2026-11-01  
**Repository:** https://github.com/RAYDENFLY/quantum-multi-agent  
**Scope:** Mathematical Specification, Causal Volatility, and Target Labeling Protocol  
**Implementation:** [labeling.py](file:///d:/quantum-multi-agent/src/quantum/features/labeling.py)  

---

## 1. RESEARCH CANDIDATE CONFIGURATION

- **Primary Timeframe ($\Delta t$):** 5m (300,000 ms)
- **Prediction Horizon ($H$):** 12 candles
- **Maximum Holding Period:** 60 minutes ($12 \times 5\text{m} = 60\text{ min}$)
- **Volatility Lookback ($w$):** 20 candles
- **Candidate Barrier Multiplier ($M$):** 1.5 (with sensitivity testing at 1.0 and 2.0)
- **Causality Guarantee:** 100% causal. No future bars enter volatility estimation.

---

## 2. MATHEMATICAL FORMULATION

### Causal Return Volatility ($\sigma_t$)
Let $C_t$ be the close price of candle $t$. The simple return at bar $\tau$ is:
$$r_\tau = \frac{C_\tau - C_{\tau-1}}{C_{\tau-1}}$$

The rolling return volatility $\sigma_t$ over lookback window $w = 20$ bars is computed using sample standard deviation with degrees of freedom $\text{ddof} = 1$:
$$\bar{r}_t = \frac{1}{w} \sum_{k=0}^{w-1} r_{t-k}$$
$$\sigma_t = \sqrt{ \frac{1}{w - 1} \sum_{k=0}^{w-1} (r_{t-k} - \bar{r}_t)^2 }$$

To prevent barrier collapse during periods of zero volatility, a floor is enforced:
$$\sigma_t = \max(\sigma_t, 10^{-6})$$

*Distinction Note:* Volatility is expressed as **relative return volatility** (dimensionless fraction), not absolute price movement in USDT. This guarantees scale invariance across crypto asset prices ranging from $0.15$ (DOGE) to $115,000$ (BTC).

### Dynamic Barrier Definitions
At prediction time $t$, entering at close price $C_t$, the upper barrier $U_t$ and lower barrier $L_t$ are defined as:
$$U_t = C_t \times (1.0 + M \times \sigma_t)$$
$$L_t = C_t \times (1.0 - M \times \sigma_t)$$
where $M$ is the barrier multiplier ($M = 1.5$ for the approved candidate).

---

## 3. FIRST-TOUCH RESOLUTION LOGIC

For forward horizon steps $k \in \{1, 2, \dots, H\}$ (where future candle $t+k$ has High $H_{t+k}$ and Low $L_{t+k}$):

1. **Upper Barrier Breach Condition:**
   $$H_{t+k} \ge U_t$$
2. **Lower Barrier Breach Condition:**
   $$L_{t+k} \le L_t$$

### Decision Tree at Step $k$
- **Case 1: Upper Barrier Breach Only ($H_{t+k} \ge U_t$ and $L_{t+k} > L_t$)**
  - Outcome: `TP` (Take Profit)
  - Numeric Label: `1`
  - Exit Step: $k$
  - Evaluation terminates immediately.

- **Case 2: Lower Barrier Breach Only ($L_{t+k} \le L_t$ and $H_{t+k} < U_t$)**
  - Outcome: `SL` (Stop Loss)
  - Numeric Label: `-1`
  - Exit Step: $k$
  - Evaluation terminates immediately.

- **Case 3: Intrabar Double Breach ($H_{t+k} \ge U_t$ and $L_{t+k} \le L_t$)**
  - Outcome: `AMBIGUOUS`
  - Numeric Label: `-2`
  - Exit Step: $k$
  - Ambiguity Policy: Both barriers breached during the same 5m bar. Because candle OHLC summaries do not preserve sub-bar tick sequencing, guessing whether High occurred before Low is statistically invalid. The event is deterministically flagged as `AMBIGUOUS` and excluded from clean supervised training datasets. Evaluation terminates immediately.

- **Case 4: No Barrier Breached at Step $k$**
  - Continue evaluation to step $k+1$.

- **Case 5: Horizon Expiration ($k = H$ reached without touches)**
  - Outcome: `TIME_EXPIRATION`
  - Numeric Label: `0`
  - Exit Step: $H = 12$
  - Exit Price: $C_{t+H}$ (close price of the 12th forward candle).

---

## 4. BOUNDARY & DATA INTEGRITY EXCEPTIONS

The label generator implements deterministic checks for edge cases and exceptions:

| Exception Scenario | Detection Mechanism | Outcome / Label | Exclusion Reason |
|---|---|---|---|
| **Warm-Up Insufficiency** | $t < \text{volatility\_lookback}$ ($t < 20$) | `EXCLUDED` (`-999`) | `WARMUP_INSUFFICIENT_LOOKBACK` |
| **End of Dataset** | $t + H \ge N$ (fewer than 12 bars left) | `EXCLUDED` (`-999`) | `INSUFFICIENT_FUTURE_HORIZON` |
| **Partition Boundary Overflow** | $t + (H \times \Delta t) > \text{partition\_end\_ms}$ | `EXCLUDED` (`-999`) | `PARTITION_BOUNDARY_OVERFLOW` |
| **Missing Candles / Gap in Horizon** | Any future candle timestamp $\ne t + (k \times \Delta t)$ | `EXCLUDED` (`-999`) | `MISSING_FUTURE_CANDLE_GAP` |
| **Intrabar Ambiguity** | Both barriers breached in single forward bar | `AMBIGUOUS` (`-2`) | `AMBIGUOUS_INTRABAR_DOUBLE_TOUCH` |

---

## 5. CODE USAGE EXAMPLE

```python
from quantum.features.labeling import TripleBarrierLabelGenerator, BarrierOutcome

generator = TripleBarrierLabelGenerator(
    horizon_bars=12,
    volatility_lookback=20,
    barrier_multiplier=1.5,
    timeframe_ms=300_000,
)

# df_5m must be sorted ascending with open_time_ms, open, high, low, close
labeled_df = generator.generate_labels(df_5m, enforce_partition_boundaries=True)

# Filter for clean supervised training samples
clean_samples = labeled_df[labeled_df["label"].isin([
    BarrierOutcome.TP.value,
    BarrierOutcome.SL.value,
    BarrierOutcome.TIME_EXPIRATION.value,
])]
```
