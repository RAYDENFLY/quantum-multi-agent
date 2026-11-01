# QUANTUM PHASE 5.5.0.3: SIGMA VS ATR SOURCE VERIFICATION

**Document Status:** `VERIFIED_FROM_SOURCE`  
**Publication Timestamp:** `2026-11-01 20:48:53 UTC`  
**Repository:** `https://github.com/RAYDENFLY/quantum-multi-agent`  
**Inspected Source File:** [`src/quantum/features/labeling.py`](file:///d:/quantum-multi-agent/src/quantum/features/labeling.py)  
**Inspected Class:** [`TripleBarrierLabelGenerator`](file:///d:/quantum-multi-agent/src/quantum/features/labeling.py#L34-L253)  

---

## 1. INVESTIGATION OBJECTIVE

The objective of this investigation is to trace the exact mathematical implementation of the triple-barrier labeling pipeline in the repository source code and resolve any inconsistency between rolling return standard deviation (sigma) and Average True Range (ATR).

---

## 2. DETAILED SOURCE CODE TRACE & FINDINGS

Forensic line-by-line inspection of [`src/quantum/features/labeling.py`](file:///d:/quantum-multi-agent/src/quantum/features/labeling.py) establishes the following answers to the 8 mandatory audit questions:

### Question 1: Is volatility calculated from close-to-close returns?
- **Source Verification:** YES.
- **Implementation:** In [`TripleBarrierLabelGenerator.compute_causal_volatility`](file:///d:/quantum-multi-agent/src/quantum/features/labeling.py#L73-L95), line 89 executes:
  ```python
  returns = close_series.pct_change()
  ```
- **Mathematical Definition:** $r_t = \frac{P_t}{P_{t-1}} - 1 = \frac{P_t - P_{t-1}}{P_{t-1}}$, representing simple relative percentage price changes between consecutive candle closes.

### Question 2: Is sample standard deviation with ddof=1 used?
- **Source Verification:** YES.
- **Implementation:** Line 93 explicitly executes:
  ```python
  vol = returns.rolling(
      window=self.volatility_lookback,
      min_periods=self.volatility_lookback,
  ).std(ddof=1)
  ```
- **Mathematical Definition:** Sample standard deviation with Bessel's correction ($N-1$ degrees of freedom in denominator):
  $$\sigma_t = \sqrt{\frac{1}{n - 1} \sum_{j=0}^{n-1} (r_{t-j} - \bar{r}_t)^2}$$

### Question 3: What is the exact rolling window length?
- **Source Verification:** Exactly 20 candles.
- **Implementation:** Default parameter `volatility_lookback: int = 20` defined on line 40.

### Question 4: Is the volatility estimate strictly causal?
- **Source Verification:** YES.
- **Implementation:** Rolling window evaluates strictly historical returns $[t-19, t]$. Line 166 enforces warm-up validation:
  ```python
  if i < self.volatility_lookback or np.isnan(vol_series[i]):
      exclusion_reasons[i] = 'WARMUP_INSUFFICIENT_LOOKBACK'
      continue
  ```
  No future data or centered rolling windows are used.

### Question 5: Is the volatility result dimensionless or price-denominated?
- **Source Verification:** Dimensionless decimal return fraction.
- **Mathematical Proof:** Since $r_t$ is a ratio of prices (dimensionless fraction), its standard deviation $\sigma_t$ is dimensionless (e.g. $0.0030 = 0.30\%$ return std). It is NOT denominated in USDT or base currency.

### Question 6: Is ATR calculated anywhere in the actual labeling pipeline?
- **Source Verification:** NO. ABSOLUTELY NOT.
- **Implementation:** An exhaustive search of [`src/quantum/features/labeling.py`](file:///d:/quantum-multi-agent/src/quantum/features/labeling.py) confirms that the string `ATR`, `True Range`, or high-low range-based volatility does NOT exist in the labeling code. ATR was NEVER used to construct target labels.

### Question 7: Is the barrier calculation multiplicative or additive?
- **Source Verification:** MULTIPLICATIVE.
- **Implementation:** Lines 174-175 calculate:
  ```python
  u_barrier = c_entry * (1.0 + self.barrier_multiplier * sigma_t)
  l_barrier = c_entry * (1.0 - self.barrier_multiplier * sigma_t)
  ```
- **Exact Mathematical Formulation:**
  $$u_t = P_{\text{ref}} \times (1 + m \times \sigma_t)$$
  $$l_t = P_{\text{ref}} \times (1 - m \times \sigma_t)$$
  where $P_{\text{ref}} = \text{close}[i]$, $m = 1.5$ (`barrier_multiplier`), and $\sigma_t = \text{std}(r_{t-19}, \dots, r_t)$.
  The price distance to each barrier is $d_t = P_{\text{ref}} \times m \times \sigma_t$. It is NOT $1.5 \times \text{ATR}$.

### Question 8: Does the barrier calculation differ across instruments or timeframes?
- **Source Verification:** NO.
- **Implementation:** The identical `TripleBarrierLabelGenerator` class is instantiated with standard parameters (`horizon_bars = 12`, `volatility_lookback = 20`, `barrier_multiplier = 1.5`, `timeframe_ms = 300_000`) across all 11 specialists.

---

## 3. DOCUMENTATION PURGE & TERMINOLOGY RECONCILIATION

1. **Purge Rule:** All descriptions referring to the frozen ML target labels as using '1.5 ATR' or 'ATR brackets' in Phase 5.5.0, 5.5.0.1, or 5.5.0.2 were inaccurate colloquial shorthand and are formally **superseded and corrected**.
2. **Authoritative ML Label Target Definition:**
   - Volatility Metric: Rolling 20-candle sample standard deviation of 5m simple percentage returns (ddof=1).
   - Multiplier: $m = 1.5$.
   - Upper Barrier: $u_t = \text{close}[i] \times (1 + 1.5\sigma_t)$.
   - Lower Barrier: $l_t = \text{close}[i] \times (1 - 1.5\sigma_t)$.
   - Horizon: $H = 12$ bars ($60$ minutes).
3. **Role of ATR:** ATR is NOT part of the frozen ML target labels. ATR may only be considered as an independent candidate feature in Alternative C for economic trade exit policies (if selected by human supervisor under DEC_01), but must never be conflated with the ML label target.
