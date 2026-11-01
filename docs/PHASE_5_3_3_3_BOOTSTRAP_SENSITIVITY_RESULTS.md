# QUANTUM PHASE 5.3.3.3: BOOTSTRAP SENSITIVITY AND ROBUSTNESS RECLASSIFICATION

**Author:** Senior Quantitative Research Scientist, Dependent-Data Inference  
**System:** QUANTUM 11-Specialist Cryptocurrency Perpetual Futures ML Trading Research System  
**Repository:** [quantum-multi-agent](file:///d:/quantum-multi-agent)  
**Execution Context:** Empirical Time-Series Resampling Analysis  

---

## 1. Executive Summary

This document presents the complete empirical results of the Moving Block Bootstrap (MBB) across all 11 QUANTUM specialist cryptocurrency trading pairs, evaluated across four prespecified block lengths:
- $b = 12$ bars (1 hour of continuous market dynamics)
- $b = 24$ bars (2 hours of continuous market dynamics; primary confirmatory specification)
- $b = 48$ bars (4 hours of continuous market dynamics)
- $b = 96$ bars (8 hours of continuous market dynamics)

Each block length configuration was evaluated using $B = 10,000$ empirical resamples under deterministic seed sequencing derived from base seed 42.

### Primary Empirical Findings

1. **Fleet-Wide Robustness for B4 LightGBM:** Under genuine candle-level empirical block resampling, all 11 specialist instruments achieve statistically significant positive lift ($p = 0.0001, \text{CI}_{95, \text{lower}} > 0$) across **all four tested block lengths** ($b \in \{12, 24, 48, 96\}$).
2. **Reversal of Prior Sensitivity Claims:** In Phase 5.3.3.2, seven instruments (`XRPUSDT`, `BNBUSDT`, `SOLUSDT`, `AVAXUSDT`, `LINKUSDT`, `DOGEUSDT`, `LTCUSDT`) were classified as `SENSITIVE_TO_BLOCK_LENGTH` based on a parametric Gaussian simulation across 5 fold means. Under actual candle-level empirical block resampling, this parametric sensitivity is disproven. All seven instruments maintain strictly positive 95% confidence intervals and p-values of $0.0001$ even at $b = 96$ bars.
3. **Magnitude of Empirical Lift:** At the primary block length ($b = 24$ bars), empirical lift over the majority-class baseline ranges from $+0.0534$ in `XMRUSDT` and $+0.0953$ in `XRPUSDT` to $+0.1656$ in `LINKUSDT`.
4. **Standard Error Precision:** The empirical bootstrap standard errors at $b = 24$ range from $0.0028$ to $0.0090$. The large sample size of original market observations ($N \approx 130,000$ per instrument) provides statistical power that was concealed when condensing each fold into a single scalar mean.
5. **Status of B2 and B3 Baselines:** Because model binaries and raw prediction vectors were not saved on disk in Phase 5.3.1 and Phase 5.3.2, and model retraining is strictly prohibited by research governance, B2 Logistic Regression and B3 Random Forest are formally classified as `UNVERIFIABLE` / `OOF_INCOMPLETE`.

---

## 2. Complete B4 LightGBM Sensitivity Matrix

Table 1 details the empirical performance of B4 LightGBM across all 11 instruments and four block lengths:

| Instrument | Block Length $b$ | Eligible $N$ | Candidate Blocks $M$ | Effective Blocks $K$ | Observed BA | Observed Lift $\Delta \text{BA}$ | Bootstrap SE | 95% Confidence Interval | Raw $p$-value | Significant at $\alpha=0.05$ |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|---:|:---:|
| **BTCUSDT** | 12 | 130,684 | 125,901 | 10,890 | 0.433187 | +0.099854 | 0.003463 | [+0.093077, +0.106644] | 0.0001 | True |
| | **24** | **130,684** | **121,091** | **5,445** | **0.433187** | **+0.099854** | **0.004134** | **[+0.091693, +0.107831]** | **0.0001** | **True** |
| | 48 | 130,684 | 112,011 | 2,722 | 0.433187 | +0.099854 | 0.005118 | [+0.089868, +0.109869] | 0.0001 | True |
| | 96 | 130,684 | 95,822 | 1,361 | 0.433187 | +0.099854 | 0.006509 | [+0.087227, +0.112613] | 0.0001 | True |
| **ETHUSDT** | 12 | 130,728 | 125,373 | 10,894 | 0.457130 | +0.123797 | 0.003310 | [+0.117364, +0.130282] | 0.0001 | True |
| | **24** | **130,728** | **120,233** | **5,447** | **0.457130** | **+0.123797** | **0.003986** | **[+0.114995, +0.130601]** | **0.0001** | **True** |
| | 48 | 130,728 | 110,643 | 2,723 | 0.457130 | +0.123797 | 0.005087 | [+0.113788, +0.133742] | 0.0001 | True |
| | 96 | 130,728 | 93,890 | 1,361 | 0.457130 | +0.123797 | 0.006553 | [+0.110750, +0.136502] | 0.0001 | True |
| **BNBUSDT** | 12 | 130,847 | 127,337 | 10,903 | 0.466677 | +0.133344 | 0.003504 | [+0.126442, +0.140227] | 0.0001 | True |
| | **24** | **130,847** | **123,892** | **5,451** | **0.466677** | **+0.133344** | **0.004207** | **[+0.125591, +0.142043]** | **0.0001** | **True** |
| | 48 | 130,847 | 117,148 | 2,725 | 0.466677 | +0.133344 | 0.005322 | [+0.122849, +0.143621] | 0.0001 | True |
| | 96 | 130,847 | 104,821 | 1,362 | 0.466677 | +0.133344 | 0.006880 | [+0.119793, +0.146685] | 0.0001 | True |
| **XRPUSDT** | 12 | 130,600 | 126,375 | 10,883 | 0.428588 | +0.095255 | 0.003444 | [+0.088510, +0.101997] | 0.0001 | True |
| | **24** | **130,600** | **122,234** | **5,441** | **0.428588** | **+0.095255** | **0.004116** | **[+0.087323, +0.103544]** | **0.0001** | **True** |
| | 48 | 130,600 | 114,357 | 2,720 | 0.428588 | +0.095255 | 0.005183 | [+0.085186, +0.105494] | 0.0001 | True |
| | 96 | 130,600 | 99,788 | 1,360 | 0.428588 | +0.095255 | 0.006616 | [+0.082322, +0.108253] | 0.0001 | True |
| **ADAUSDT** | 12 | 130,483 | 126,983 | 10,873 | 0.468513 | +0.135180 | 0.002492 | [+0.129994, +0.139785] | 0.0001 | True |
| | **24** | **130,483** | **123,546** | **5,436** | **0.468513** | **+0.135180** | **0.002980** | **[+0.125548, +0.137206]** | **0.0001** | **True** |
| | 48 | 130,483 | 116,926 | 2,718 | 0.468513 | +0.135180 | 0.003714 | [+0.124508, +0.138982] | 0.0001 | True |
| | 96 | 130,483 | 104,498 | 1,359 | 0.468513 | +0.135180 | 0.004780 | [+0.122391, +0.141093] | 0.0001 | True |
| **SOLUSDT** | 12 | 130,808 | 125,752 | 10,900 | 0.439964 | +0.106631 | 0.003786 | [+0.099190, +0.113941] | 0.0001 | True |
| | **24** | **130,808** | **120,897** | **5,450** | **0.439964** | **+0.106631** | **0.004550** | **[+0.098696, +0.116836]** | **0.0001** | **True** |
| | 48 | 130,808 | 111,768 | 2,725 | 0.439964 | +0.106631 | 0.005703 | [+0.095598, +0.117973] | 0.0001 | True |
| | 96 | 130,808 | 95,115 | 1,362 | 0.439964 | +0.106631 | 0.007357 | [+0.092419, +0.121175] | 0.0001 | True |
| **AVAXUSDT** | 12 | 130,818 | 128,784 | 10,901 | 0.452261 | +0.118928 | 0.002633 | [+0.113880, +0.124239] | 0.0001 | True |
| | **24** | **130,818** | **126,819** | **5,450** | **0.452261** | **+0.118928** | **0.003075** | **[+0.111614, +0.123693]** | **0.0001** | **True** |
| | 48 | 130,818 | 122,962 | 2,725 | 0.452261 | +0.118928 | 0.003792 | [+0.110292, +0.125184] | 0.0001 | True |
| | 96 | 130,818 | 115,446 | 1,362 | 0.452261 | +0.118928 | 0.004860 | [+0.108169, +0.127209] | 0.0001 | True |
| **LINKUSDT** | 12 | 130,777 | 129,088 | 10,898 | 0.498941 | +0.165608 | 0.002447 | [+0.160759, +0.170428] | 0.0001 | True |
| | **24** | **130,777** | **127,422** | **5,449** | **0.498941** | **+0.165608** | **0.002844** | **[+0.158965, +0.170119]** | **0.0001** | **True** |
| | 48 | 130,777 | 124,142 | 2,724 | 0.498941 | +0.165608 | 0.003502 | [+0.157528, +0.171212] | 0.0001 | True |
| | 96 | 130,777 | 117,688 | 1,362 | 0.498941 | +0.165608 | 0.004455 | [+0.155737, +0.173169] | 0.0001 | True |
| **DOGEUSDT** | 12 | 130,648 | 126,450 | 10,887 | 0.489942 | +0.156609 | 0.002613 | [+0.151390, +0.161646] | 0.0001 | True |
| | **24** | **130,648** | **122,398** | **5,443** | **0.489942** | **+0.156609** | **0.003112** | **[+0.148974, +0.163137]** | **0.0001** | **True** |
| | 48 | 130,648 | 114,642 | 2,721 | 0.489942 | +0.156609 | 0.003926 | [+0.147775, +0.163200] | 0.0001 | True |
| | 96 | 130,648 | 100,094 | 1,360 | 0.489942 | +0.156609 | 0.005118 | [+0.145070, +0.165181] | 0.0001 | True |
| **LTCUSDT** | 12 | 130,463 | 127,624 | 10,871 | 0.485102 | +0.151769 | 0.002634 | [+0.146747, +0.157076] | 0.0001 | True |
| | **24** | **130,463** | **124,809** | **5,435** | **0.485102** | **+0.151769** | **0.003144** | **[+0.144794, +0.157174]** | **0.0001** | **True** |
| | 48 | 130,463 | 119,374 | 2,717 | 0.485102 | +0.151769 | 0.003960 | [+0.142838, +0.158356] | 0.0001 | True |
| | 96 | 130,463 | 109,036 | 1,358 | 0.485102 | +0.151769 | 0.005126 | [+0.140409, +0.160492] | 0.0001 | True |
| **XMRUSDT** | 12 | 15,252 | 15,063 | 1,271 | 0.386760 | +0.053427 | 0.007629 | [+0.038421, +0.068384] | 0.0001 | True |
| | **24** | **15,252** | **14,859** | **635** | **0.386760** | **+0.053427** | **0.009025** | **[+0.035879, +0.071274]** | **0.0001** | **True** |
| | 48 | 15,252 | 14,451 | 317 | 0.386760 | +0.053427 | 0.011388 | [+0.031045, +0.075728] | 0.0001 | True |
| | 96 | 15,252 | 13,664 | 158 | 0.386760 | +0.053427 | 0.015093 | [+0.024062, +0.082743] | 0.0001 | True |

---

## 3. Robustness Reclassification Across Block Lengths

Table 2 contrasts the historical Phase 5.3.3.2 claims with the corrected empirical findings:

| Instrument | Phase 5.3.3.2 Claim | Empirical Evidence across $b \in \{12, 24, 48, 96\}$ | Final Corrected Classification | Reclassification Justification |
|---|---|---|---|---|
| `BTCUSDT` | `ROBUST` | Significant across all 4 block lengths ($p=0.0001$) | `ROBUST_ACROSS_TESTED_BLOCK_LENGTHS` | Confirmed by empirical block resampling |
| `ETHUSDT` | `ROBUST` | Significant across all 4 block lengths ($p=0.0001$) | `ROBUST_ACROSS_TESTED_BLOCK_LENGTHS` | Confirmed by empirical block resampling |
| `BNBUSDT` | `SENSITIVE` | Significant across all 4 block lengths ($p=0.0001$) | `ROBUST_ACROSS_TESTED_BLOCK_LENGTHS` | Reversal: Prior parametric fold scaling was overly pessimistic |
| `XRPUSDT` | `SENSITIVE` | Significant across all 4 block lengths ($p=0.0001$) | `ROBUST_ACROSS_TESTED_BLOCK_LENGTHS` | Reversal: Empirical CI lower > +0.082 even at b=96 |
| `ADAUSDT` | `ROBUST` | Significant across all 4 block lengths ($p=0.0001$) | `ROBUST_ACROSS_TESTED_BLOCK_LENGTHS` | Confirmed by empirical block resampling |
| `SOLUSDT` | `SENSITIVE` | Significant across all 4 block lengths ($p=0.0001$) | `ROBUST_ACROSS_TESTED_BLOCK_LENGTHS` | Reversal: Empirical CI lower > +0.092 even at b=96 |
| `AVAXUSDT` | `SENSITIVE` | Significant across all 4 block lengths ($p=0.0001$) | `ROBUST_ACROSS_TESTED_BLOCK_LENGTHS` | Reversal: Empirical CI lower > +0.108 even at b=96 |
| `LINKUSDT` | `SENSITIVE` | Significant across all 4 block lengths ($p=0.0001$) | `ROBUST_ACROSS_TESTED_BLOCK_LENGTHS` | Reversal: Empirical CI lower > +0.155 even at b=96 |
| `DOGEUSDT` | `SENSITIVE` | Significant across all 4 block lengths ($p=0.0001$) | `ROBUST_ACROSS_TESTED_BLOCK_LENGTHS` | Reversal: Empirical CI lower > +0.145 even at b=96 |
| `LTCUSDT` | `SENSITIVE` | Significant across all 4 block lengths ($p=0.0001$) | `ROBUST_ACROSS_TESTED_BLOCK_LENGTHS` | Reversal: Empirical CI lower > +0.140 even at b=96 |
| `XMRUSDT` | `ROBUST` | Significant across all 4 block lengths ($p=0.0001$) | `ROBUST_ACROSS_TESTED_BLOCK_LENGTHS` | Confirmed by empirical block resampling |

---

## 4. Methodological Analysis: Why Parametric Sensitivity Dissolved

The dissolution of the previous `SENSITIVE_TO_BLOCK_LENGTH` classification is a mathematically rigorous outcome explained by the difference in sample aggregation:

1. **The Phase 5.3.3.2 Parametric Model:**
   In Phase 5.3.3.2, the bootstrap did not draw market candles. Instead, it drew 5 Gaussian values $\tilde{y}_k \sim \mathcal{N}(\mu_k, s_{\text{fold}}^2 \cdot \frac{b}{12})$ representing the five fold means. With only 5 fold degrees of freedom, multiplying the fold sample standard deviation by $\sqrt{96 / 12} = \sqrt{8} \approx 2.83$ inflated the simulated standard error so severely that the lower bound of the simulated normal distribution dipped near or below zero for instruments with moderate inter-fold variance.
2. **The Phase 5.3.3.3 Empirical Moving Block Bootstrap:**
   In Phase 5.3.3.3, resampling is conducted over the actual 130,000 market observations. Even at block length $b = 96$ bars, each bootstrap replication concatenates over 1,360 independent blocks ($K = \lfloor 130,000 / 96 \rfloor \approx 1,360$). Under the Central Limit Theorem for dependent processes (Lahiri 2003, Theorem 3.1), the standard error of the mean of 1,360 dependent blocks scales as:
   $$\text{SE}^* \approx \frac{\sigma_{\text{block}}}{\sqrt{K}}$$
   Because $K = 1,360$ is very large, the empirical standard error at $b = 96$ remains small ($\approx 0.004$ to $0.007$). As a result, the 95% confidence intervals remain far above zero for all 11 instruments.

The apparent sensitivity in Phase 5.3.3.2 was an artifact of parametric normal approximation applied to 5 macro fold summaries, rather than a genuine property of the underlying market time series.
