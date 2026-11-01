# QUANTUM PHASE 5.3.3.3: EMPIRICAL MOVING BLOCK BOOTSTRAP METHODOLOGY

**Author:** Senior Quantitative Research Scientist, Financial Machine Learning  
**System:** QUANTUM 11-Specialist Cryptocurrency Perpetual Futures ML Trading Research System  
**Repository:** [quantum-multi-agent](file:///d:/quantum-multi-agent)  
**Execution Context:** Dependent-Data Inference & Statistical Governance  

---

## 1. Introduction and Methodological Justification

In Phase 5.3.3.2, an independent audit disclosed that the reported bootstrap sensitivity analysis had used parametric Gaussian pseudo-draws centered around fold-level mean statistics and scaled by a nominal variance factor $\sqrt{b / 12} / \sqrt{5}$, rather than empirical block resampling of candle-level out-of-fold (OOF) observations.

Financial time-series data exhibit non-Gaussian marginal distributions, heavy tails, volatility clustering, serial autocorrelation in feature space, and label overlap induced by triple-barrier horizons. Parametric simulations that assume independent Gaussian fold errors cannot capture the empirical dependency structure of high-frequency cryptocurrency market observations.

Phase 5.3.3.3 replaces parametric simulation with a mathematically rigorous, fully empirical Moving Block Bootstrap (MBB) (Kunsch 1989; Liu & Singh 1992; Politis & Romano 1994; Lahiri 2003) executed directly on the 1,322,108 candle-level paired prediction-label observations across all 11 specialist trading pairs.

---

## 2. Statistical Estimand Specification

In strict alignment with Task C of the specification, the target statistical estimand is defined as:

$$\Delta \text{BA} = \text{BA}(\text{model}) - \text{BA}(B_0)$$

where:
- $\text{BA}(\text{model})$ is the three-class macro Balanced Accuracy of the specialist classifier:
  $$\text{BA} = \frac{1}{3} \sum_{c \in \{-1, 0, 1\}} \frac{\text{TP}_c}{N_c}$$
- $\text{BA}(B_0)$ is the Balanced Accuracy of the constant majority-class baseline heuristic. For any complete three-class dataset where the model predicts a single constant class $c^* \in \{-1, 1\}$:
  $$\text{Recall}_{c^*} = 1.0, \quad \text{Recall}_{c \ne c^*} = 0.0 \implies \text{BA}(B_0) \equiv \frac{1}{3}$$
- The evaluation unit is an individual 5-minute candle observation $(t_i, y_{i, \text{true}}, y_{i, \text{pred}})$.
- The evaluation domain is the pooled out-of-fold test partition across the 5 purged walk-forward validation folds spanning $2023\text{-}11\text{-}01$ through $2026\text{-}10\text{-}31$ UTC (excluding prospective holdout).
- **Conditionality Notice:** Inference is strictly conditional on the sequence of historical training samples and trained fold models that generated the OOF predictions. It quantifies the sampling variability of the evaluation period under temporal dependence, but does not capture parameter retraining randomness, future regime shifts, or execution frictions.

---

## 3. Block Construction and Temporal Segmentation

### 3.1 Preserving Temporal Structure

Consecutive rows in an eligible OOF dataset do not always represent consecutive 5-minute market candles. Temporal discontinuities arise from:
1. Walk-forward fold boundaries (with 13 to 14 bar purge intervals between test folds).
2. Omission of ambiguous label candles (`label == -2`, where barriers were hit simultaneously).
3. Omission of boundary exclusion candles (`label == -999`, within 12 bars of partition ends).

Bridging across these gaps to form artificial blocks would violate the empirical time-series dependence structure.

### 3.2 Segmentation Policy

Let $(t_1, t_2, \dots, t_N)$ be the sorted chronological timestamps of the OOF dataset for a given instrument, and let $f_i \in \{1, 2, 3, 4, 5\}$ be the fold identifier of candle $i$.
A sequence of observations $[i, i+1, \dots, j]$ forms a strictly continuous segment $S_k$ if and only if:
1. $t_{m+1} - t_m = 300,000\text{ ms} \quad \forall m \in [i, j-1]$
2. $f_{m+1} = f_m \quad \forall m \in [i, j-1]$

Let $\{S_1, S_2, \dots, S_J\}$ be the set of all continuous segments for the instrument, with lengths $L_1, L_2, \dots, L_J$.

### 3.3 Candidate Block Pool

For a target block length $b \in \{12, 24, 48, 96\}$, candidate blocks are formed strictly within segments where $L_j \ge b$. The number of overlapping candidate blocks of length $b$ contributed by segment $j$ is:

$$M_j(b) = L_j - b + 1$$

The total pool of valid candidate blocks for the instrument is:

$$M(b) = \sum_{j: L_j \ge b} M_j(b)$$

Across the 11 instruments, $M(24)$ ranges from 14,859 blocks in XMRUSDT to over 121,000 blocks in BTCUSDT, providing massive empirical support for block resampling.

---

## 4. Empirical Resampling Algorithm

For each instrument, model, and block length $b$:
1. **Nominal Sample Size:** Let $N$ be the total number of eligible OOF observations.
2. **Block Counts:** The nominal number of full blocks required is $K = \lfloor N / b \rfloor$. The remainder is $r = N \pmod b$.
3. **Resampling with Replacement:** For each bootstrap replication $j \in \{1, 2, \dots, B\}$ (where $B = 10,000$, seed = 42):
   - Sample $K$ block indices uniformly with replacement from $\{0, 1, \dots, M(b) - 1\}$.
   - If $r > 0$, sample 1 partial block index uniformly with replacement from the partial block candidate pool $M(r)$.
4. **Joint Prediction-Label Preservation:** When block $m$ is selected, the paired vector sequence:
   $$\{(y_{t, \text{true}}, y_{t, \text{pred}})\}_{t=st_m}^{st_m + b - 1}$$
   is drawn intact. Predictions, probabilities, and ground-truth labels are never resampled independently.
5. **Exact Metric Evaluation:** The concatenated bootstrap sample has length exactly $N$. The bootstrap Balanced Accuracy $\text{BA}^{*(j)}$ and bootstrap lift $\Delta \text{BA}^{*(j)} = \text{BA}^{*(j)} - \frac{1}{3}$ are evaluated on the resampled sequence.

---

## 5. Null Hypothesis Generation and Finite-Sample P-Values

### 5.1 Centered Null Distribution (Hall & Wilson 1991)

Testing the hypothesis of positive predictive lift:

$$H_0: \Delta \text{BA} \le 0 \quad \text{versus} \quad H_1: \Delta \text{BA} > 0$$

Under the standard empirical bootstrap, bootstrap replicates $\Delta \text{BA}^{*(j)}$ are centered around the observed sample estimate $\Delta \text{BA}_{\text{obs}}$, not around 0. Merely computing the fraction of positive bootstrap lifts does not construct a valid null test.

Following Guideline 1 of Hall & Wilson (1991, *Biometrics*), the bootstrap test statistic must be evaluated under the null hypothesis by centering the bootstrap distribution at the null boundary:

$$\Delta \text{BA}^{*(j)}_{\text{null}} = \Delta \text{BA}^{*(j)} - \Delta \text{BA}_{\text{obs}}$$

By construction, $\mathbb{E}^*[\Delta \text{BA}^*_{\text{null}}] = 0$.

### 5.2 Finite-Sample One-Sided P-Value

The finite-sample p-value testing whether the observed lift exceeds null expectation is computed as:

$$p = \frac{1 + \sum_{j=1}^B \mathbb{I}\left(\Delta \text{BA}^{*(j)}_{\text{null}} \ge \Delta \text{BA}_{\text{obs}}\right)}{B + 1}$$

Because $\Delta \text{BA}^{*(j)}_{\text{null}} \ge \Delta \text{BA}_{\text{obs}} \iff \Delta \text{BA}^{*(j)} \ge 2 \Delta \text{BA}_{\text{obs}}$:
- When $\Delta \text{BA}_{\text{obs}}$ is large and positive relative to the bootstrap standard error $\text{SE}^*$, the condition is never met, yielding the minimum attainable finite-sample p-value:
  $$p_{\min} = \frac{1}{10,001} \approx 0.00009999 \quad (0.000100)$$
- When $\Delta \text{BA}_{\text{obs}} \approx 0$, approximately half the replicates exceed $\Delta \text{BA}_{\text{obs}}$, yielding $p \approx 0.50$.
- When $\Delta \text{BA}_{\text{obs}} < 0$, $p > 0.50$.

### 5.3 Percentile Confidence Intervals

Uncertainty around the true conditional lift $\Delta \text{BA}$ is quantified via the uncentered empirical bootstrap distribution. The 95% percentile confidence interval is given by:

$$\text{CI}_{0.95} = \left[ \Delta \text{BA}^*_{(0.025)}, \; \Delta \text{BA}^*_{(0.975)} \right]$$

---

## 6. Computational Resource and Memory Control

To comply with Section 10 ($\le 2$ CPU threads, $\le 1$ GB RAM, deterministic execution):
1. **O(1) Vectorized Contingency Tables:** Rather than repeatedly slicing and aggregating raw arrays during simulation, a 2D cumulative sum table (prefix table) of class counts and true positives is computed once per instrument. For any candidate block starting at $st$, the contingency counts are evaluated in $O(1)$ operations:
   $$\text{Stats}(st, b) = \text{Prefix}[st + b] - \text{Prefix}[st]$$
2. **Chunked Generation:** Replications are simulated in batches of 1,000. Peak RAM utilization across all 11 instruments was measured at **629.8 MB**, well within the 1,024 MB threshold.
3. **Execution Time:** The entire 11-instrument suite of 40,000 resamples per instrument (440,000 total block resamples across 1.32 million observations) completed in **350.1 seconds** on a single thread.
