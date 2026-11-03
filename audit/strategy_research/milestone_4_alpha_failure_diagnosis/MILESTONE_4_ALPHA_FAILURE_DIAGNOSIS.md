# QUANTUM — MILESTONE 4: ALPHA FAILURE DIAGNOSIS & RESEARCH DIRECTION
## Comprehensive Forensic Alpha Failure Diagnosis, Microstructure Audit, and Session 2 Research Direction

**Dokumen Identifikasi:** `audit/strategy_research/milestone_4_alpha_failure_diagnosis/MILESTONE_4_ALPHA_FAILURE_DIAGNOSIS.md`  
**Tanggal Publikasi:** 2026-11-03 19:30:00 UTC  
**Branch Penelitian:** `research/high-turnover-alpha-feasibility`  
**Git Base Commit:** `dcc8ceb54d80b1b9685d92236f48b0994610522a`  
**Status Prospective Holdout:** **STRICTLY SEALED & UNBREACHED** ($\ge 1793491200000\text{ ms}$ / 2026-11-01 00:00:00 UTC)  
**Status Final Research Decision:** **`MIXED_FAILURE: EXECUTION_COST_DOMINANT + TRADE_SELECTION_FAILURE`**  

---

## 1. Executive Summary & Jawaban Pertanyaan Penelitian

### 1.1 Pertanyaan Penelitian Utama
> *"Apakah kegagalan strategi terutama disebabkan oleh execution friction, lemahnya predictive alpha, buruknya trade selection, ketidakcocokan market regime, atau kombinasi faktor-faktor tersebut?"*

### 1.2 Jawaban Kuantitatif Definitif
Berdasarkan investigasi forensik menyeluruh terhadap 900 uji simulasi re-evaluasi pada Milestone 3 dan analisis terperinci terhadap $552,306$ eksekusi perdagangan riil pada Milestone 4, jawabannya adalah:

> **KEGAGALAN STRATEGI MERUPAKAN SUATU `MIXED_FAILURE`, YANG DIDORONG SECARA SINERGIS OLEH DUA PENYEBAB UTAMA: `EXECUTION_COST_DOMINANCE` (DOMINASI FRIKSI EKSEKUSI) DAN `TRADE_SELECTION_FAILURE` (KEGAGALAN PEMILIHAN PERDAGANGAN AKIBAT KETIDAKCOCOKAN REZIM PASAR).**

Bukti kuantitatif empiris membuktikan bahwa:
1. **Predictive Alpha TIDAK Sepenuhnya Hilang (*Not Absent*):**
   - Armada 300 strategi historis mempertahankan *gross expectancy* rata-rata positif sebesar **$+5.98\text{ bps}$** ($+\$8,019.11$ gross PnL kumulatif).
   - Pada kondisi pasar yang tepat (**High Volatility Trending**), strategi menghasilkan gross expectancy **$+21.22\text{ bps}$** dan net expectancy **$+7.88\text{ bps}$** ($PF = 1.096$, Net PnL $+\$3,058.71$), bahkan setelah membayar biaya taker Bybit VIP0 secara penuh!
   - Markout pasca-pengisian (*post-fill markout*) pada 12 bar (60 menit) bernilai **$+19.78\text{ bps}$**, mengonfirmasi adanya kekuatan prediktif searah pada sinyal mentah.
2. **Dominasi Friksi Eksekusi (*Execution Cost Dominance*):**
   - Target keuntungan pada time frame 5-menit terlalu kecil untuk menyerap struktur biaya bursa riil. Friksi eksekusi rata-rata di Bybit VIP0 adalah $13.43\text{ bps}$ per trade, yang mengonsumsi **$224.6\%$** dari gross edge armada ($+5.98\text{ bps}$ gross menjadi $-7.45\text{ bps}$ net).
   - Pada skenario Aster Stress ($44.0\text{ bps}$ round-trip), friksi mengonsumsi **$675.0\%$** dari gross edge, menyebabkan median return anjlok ke $-86.50\%$.
   - Pada skenario Maker ($9.5\text{ bps}$ round-trip), friksi tetap mengonsumsi **$306.1\%$** dari gross edge karena 85% kaki penutupan posisi terpaksa dieksekusi sebagai TAKER saat menyentuh stop-loss darurat.
3. **Kegagalan Pemilihan Trade & Ketidakcocokan Rezim (*Trade Selection & Regime Mismatch*):**
   - Sinyal entri armada tidak memiliki filter rezim volatilitas maupun tren yang memadai, sehingga **$50.0\%$ dari seluruh perdagangan ($275,968\text{ trades}$)** ditembakkan ke kondisi *ranging/choppy*.
   - Pada kondisi *ranging*, gross expectancy bernilai negatif hingga mendekati nol ($-6.27\text{ bps}$ pada High-Vol Ranging dan $+0.47\text{ bps}$ pada Low-Vol Ranging), menyebabkan pendarahan kumulatif sebesar **$-\$12,012.97$**, yang sepenuhnya menghapus dan menenggelamkan keuntungan $+\$3,058.71$ dari pasar trending!
4. **Asimetri Durasi & *Noise Stop-Out*:**
   - **$29.08\%$ dari seluruh trade ($160,618\text{ trades}$)** terhenti (*stopped out*) hanya dalam **1 bar (5 menit)** dengan kerugian rata-rata **$-65.28\text{ bps}$ net**.
   - Sebaliknya, trade yang bertahan $> 6\text{ bars}$ ($> 30\text{ menit}$) menghasilkan net expectancy rata-rata **$+35.34\text{ bps}$**. Hambatan *stop-loss* 5-menit terlalu sempit terhadap *microstructure noise*.
5. **Bias Asimetri Arah (*Bidirectional Short Drag*):**
   - Posisi Short pada altcoin mengalami kerugian parah (Short net expectancy $-15.53\text{ bps}$ vs Long $-7.22\text{ bps}$). Pada DOGEUSDT, posisi short kehilangan $-21.82\text{ bps}$ per trade, dan pada ADAUSDT kehilangan $-22.52\text{ bps}$ per trade.

---

## 2. Evidence Baseline & Status Verifikasi

Tabel berikut merekonsiliasi angka-angka dasar dari laporan Milestone 3 dan hasil verifikasi empiris Milestone 4:

| Metrik Penelitian | Nilai Baseline Milestone 3 | Nilai Terverifikasi Milestone 4 ($N=552,306$) | Status Verifikasi | Catatan Forensik |
| :--- | :---: | :---: | :---: | :--- |
| **Bybit VIP0 Qualified Strats** | **0 / 295** ($0.0\%$) | **0 / 295** ($0.0\%$) | **VERIFIED IDENTICAL** | Seluruh 295 strategi gagal lolos kualifikasi. |
| **Aster Stress Qualified Strats** | **0 / 295** ($0.0\%$) | **0 / 295** ($0.0\%$) | **VERIFIED IDENTICAL** | Seluruh 295 strategi gagal lolos kualifikasi. |
| **Maker Scenario Qualified Strats** | **0 / 295** ($0.0\%$) | **0 / 295** ($0.0\%$) | **VERIFIED IDENTICAL** | Seluruh 295 strategi gagal lolos kualifikasi. |
| **Fleet Mean Gross Expectancy** | $+5.98\text{ bps}$ | $+5.98\text{ bps}$ (Bybit) | **VERIFIED IDENTICAL** | Sinyal memiliki edge kotor positif marjinal. |
| **Fleet Mean Net Expectancy** | $-7.45\text{ bps}$ | $-7.45\text{ bps}$ (Bybit) | **VERIFIED IDENTICAL** | Friksi membalikkan edge kotor menjadi net loss. |
| **Aster Median Return** | $-68.4\%$ | $-86.50\%$ (Median) / $-82.30\%$ (Mean) | **VERIFIED RECONCILED** | $-68.4\%$ adalah median awal batch; remediated median $-86.50\%$. |
| **Maker Median Return** | $-24.8\%$ | $-59.28\%$ (Median) / $-56.15\%$ (Mean) | **VERIFIED RECONCILED** | Terkonfirmasi pasca audit rekonsiliasi 85% taker leg. |
| **STRAT_242 True Net Return** | $+0.90\%$ | $+0.90\%$ (Bybit VIP0) | **VERIFIED IDENTICAL** | Traded notional $\$61,196.87$, Net PnL $+\$0.90$. |
| **STRAT_242 Aster Net Return** | $-81.10\%$ | $-81.10\%$ | **VERIFIED IDENTICAL** | Bangkrut di bawah 44 bps friction. |
| **STRAT_242 Maker Net Return** | $-26.64\%$ | $-26.64\%$ | **VERIFIED IDENTICAL** | Tertekan oleh SL taker exits. |

---

## 3. Analysis A — Dekomposisi Kerugian Finansial (*Loss Decomposition*)

### 3.1 Kontribusi Komponen Finansial
Analisis dekomposisi finansial dilakukan pada level skenario, famili strategi, dan aset untuk memastikan **zero double counting** antara biaya komisi bursa, spread, slippage, pendanaan (*funding*), dan *adverse selection*.

Data lengkap tersimpan pada artefak:  
`audit/strategy_research/milestone_4_alpha_failure_diagnosis/MILESTONE_4_LOSS_DECOMPOSITION.csv`

#### Tabel Dekomposisi Biaya per Skenario ($300\text{ Strategi}$)
| Komponen Keuangan | ASTER_STRESS_TAKER | BYBIT_VIP0_DEFAULT | MAKER_PASSIVE_TRUE | Dominansi Komponen |
| :--- | :---: | :---: | :---: | :--- |
| **Gross PnL (USD)** | $+\$2,816.64$ | $+\$8,019.11$ | $+\$6,563.37$ | Edge kotor positif di semua skenario |
| **Trading Fees (USD)** | $-\$25,033.21$ ($91.0\%$) | $-\$14,975.32$ ($74.1\%$) | $-\$23,298.80$ ($99.5\%$) | **KOMPONEN BIAYA TERBESAR** |
| **Spread Cost (USD)** | $-\$1,209.91$ ($4.4\%$) | $-\$2,562.27$ ($12.7\%$) | $\$0.00$ ($0.0\%$) | Tereliminasi pada maker resting limits |
| **Slippage Cost (USD)** | $-\$1,209.91$ ($4.4\%$) | $-\$2,562.27$ ($12.7\%$) | $\$0.00$ ($0.0\%$) | Tereliminasi pada maker resting limits |
| **Adverse Selection (USD)** | $\$0.00$ ($0.0\%$) | $\$0.00$ ($0.0\%$) | $-\$8.06$ ($0.04\%$) | Terukur pada pengisian limit touch |
| **Funding Cost (USD)** | $-\$53.05$ ($0.2\%$) | $-\$121.47$ ($0.6\%$) | $-\$102.08$ ($0.4\%$) | Sangat kecil karena holding time pendek |
| **Total Friksi Eksekusi** | **$-\$27,505.74$** | **$-\$20,220.70$** | **$-\$23,408.89$** | **Penyerap Modal Utama** |
| **Net Realized PnL (USD)**| **$-\$24,689.10$** | **$-\$12,201.59$** | **$-\$16,845.52$** | Seluruh skenario membukukan kerugian bersih |

### 3.2 Metrik Kunci Dekomposisi Biaya (Bybit VIP0)
- **Komponen Biaya Terbesar:** **Exchange Trading Fees ($74.1\%$)**, disusul Spread ($12.7\%$) dan Slippage ($12.7\%$).
- **Biaya Rata-rata per Trade:** **$\$0.0366$** (setara $13.43\text{ bps}$ per trade pada notional $\$35.0$).
- **Biaya Rata-rata per Strategi:** **$\$67.40$** (terhadap modal awal $\$100.0 \implies 67.4\%$ modal tergerus biaya).
- **Gross Expectancy vs Net Expectancy:** **$+5.98\text{ bps}$ vs $-7.45\text{ bps}$**.
- **Persentase Gross Edge yang Terkonsumsi:**
  $$\text{Friction Consumption Rate} = \frac{\text{Gross Expectancy} - \text{Net Expectancy}}{\text{Gross Expectancy}} \times 100\% = \frac{13.43\text{ bps}}{5.98\text{ bps}} \times 100\% = \mathbf{224.6\%}$$
  Pada skenario Aster Stress, rasio ini meledak menjadi **$675.0\%$**.

---

## 4. Analysis B — Diagnosis Kegagalan Level Perdagangan (*Trade-Level Failure Diagnosis*)

Analisis terhadap $552,306$ catatan perdagangan individual di bawah skenario Bybit VIP0 mengungkap pola kegagalan mikrostruktur yang sangat jelas:

### 4.1 Distribusi Alasan Keluar (*Exit Reasons*)
| Alasan Keluar (*Exit Reason*) | Jumlah Trade | Persentase | Rata-rata Gross (bps) | Rata-rata Net (bps) | Rata-rata Durasi (Bar) | Win Rate Net |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **STOP_LOSS** | **334,852** | **60.63%** | **-78.76 bps** | **-93.78 bps** | **3.83 bars** | **0.05%** |
| **TAKE_PROFIT** | 146,136 | 26.46% | +168.00 bps | +158.47 bps | 6.32 bars | 100.00% |
| **TAKE_PROFIT_2** | 10,371 | 1.88% | +161.40 bps | +151.81 bps | 7.41 bars | 100.00% |
| **TIME_EXPIRATION** | 49,217 | 8.91% | +54.45 bps | +39.25 bps | 18.84 bars | 72.28% |
| **BREAKEVEN_STOP** | 9,081 | 1.64% | +43.93 bps | +31.37 bps | 7.60 bars | 96.53% |
| **PARTIAL_TP1_TIME_EXIT**| 2,649 | 0.48% | +114.40 bps | +101.59 bps | 20.08 bars | 100.00% |

> [!CRITICAL]
> **Temuan Kunci 1:** Lebih dari **$60.6\%$ perdagangan berakhir dengan Stop-Loss**, sementara Take-Profit hanya tercapai pada $28.3\%$ perdagangan. Hal ini membuktikan bahwa batas stop-loss berbasis volatilitas lokal ($1.5\text{–}2.0 \times \sigma_{20}$) pada time frame 5-menit terlalu rapuh terhadap fluktuasi acak (*market noise*).

### 4.2 Durasi Pemegangan Posisi (*Holding Duration Anomaly*)
| Durasi Pemegangan | Waktu Nyata | Jumlah Perdagangan | Persentase | Gross Expectancy | Net Expectancy |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **1 Bar** | **5 Menit** | **160,618** | **29.08%** | **-51.04 bps** | **-65.28 bps** |
| **2 Bars** | **10 Menit** | **72,625** | **13.15%** | **-7.62 bps** | **-21.13 bps** |
| **3 Bars** | **15 Menit** | **47,299** | **8.56%** | **+8.56 bps** | **-4.56 bps** |
| **4 Bars** | **20 Menit** | **35,892** | **6.50%** | **+27.85 bps** | **+15.06 bps** |
| **5 Bars** | **25 Menit** | **29,114** | **5.27%** | **+32.07 bps** | **+19.51 bps** |
| **6 Bars** | **30 Menit** | **25,764** | **4.66%** | **+33.77 bps** | **+21.24 bps** |
| **> 6 Bars** | **> 30 Menit** | **180,994** | **32.77%** | **+48.50 bps** | **+35.34 bps** |

> [!IMPORTANT]
> **Temuan Kunci 2:** Terjadi fenomena *premature noise liquidation*:
> - Sebanyak **$42.23\%$ perdagangan keluar dalam waktu $\le 10\text{ menit}$** (Bar 1–2) dengan kerugian parah ($-65.28\text{ bps}$ dan $-21.13\text{ bps}$ net).
> - Sebaliknya, perdagangan yang berhasil bertahan **$\ge 20\text{ menit}$ menghasilkan Net Expectancy positif yang sangat kokoh ($+15.06\text{ bps}$ hingga $+35.34\text{ bps}$)**.
> - Ini adalah bukti kuat bahwa konsep *high-turnover ultra-short scalping* (sub-15 menit) adalah kesalahan metodologis dalam memilih *holding horizon*.

### 4.3 Profil Markout Pasca-Pengisian (*Post-Fill Markout Profile*)
Pengukuran pergeseran harga searah sinyal pada $k$ bar setelah pengisian:
- **Markout 1 Bar (5m):** $+2.36\text{ bps}$
- **Markout 2 Bars (10m):** $+4.22\text{ bps}$
- **Markout 3 Bars (15m):** $+4.74\text{ bps}$
- **Markout 6 Bars (30m):** $+12.15\text{ bps}$
- **Markout 12 Bars (60m):** **$+19.78\text{ bps}$**

Kurva markout yang monoton naik dari $+2.36\text{ bps}$ menuju $+19.78\text{ bps}$ membuktikan bahwa sinyal kuantitatif QUANTUM **memiliki alpha arah (*directional predictive alpha*) yang nyata dalam cakrawala 1 jam**, namun strategi historis mengeksekusinya dengan horizon 5-menit yang terbunuh oleh noise stop-loss.

### 4.4 Asimetri Arah Long vs Short
- **Posisi LONG ($95.80\%$ armada, $529,118\text{ trades}$):** Gross $+6.21\text{ bps}$, Net **$-7.22\text{ bps}$**, Profit Factor $0.866$.
- **Posisi SHORT ($4.20\%$ armada, $23,188\text{ trades}$):** Gross $-2.26\text{ bps}$, Net **$-15.53\text{ bps}$**, Profit Factor $0.699$.
- Posisi Short membukukan kerugian dua kali lipat lebih besar daripada posisi Long karena rezim makro aset kripto pada dataset 2024–2026 berada dalam tren ekspansi struktural. Sinyal short simetris tanpa filter makro tren bertindak sebagai penarik kerugian (*drag*).

### 4.5 Kekalahan Beruntun & Pelanggaran Drawdown (*Consecutive Losses*)
- Rata-rata *Maximum Consecutive Losses* per strategi adalah **$21.1\text{ trades}$ beruntun** (Median: $21.0$, Maksimum: $36\text{ trades}$).
- Sebanyak **$278$ dari $300$ strategi ($92.7\%$)** mengalami rentetan kekalahan beruntun $\ge 15$ kali.
- Runtutan kekalahan inilah yang secara langsung memicu kegagalan $262$ strategi pada klasifikasi `EXCESSIVE_DRAWDOWN_BREACH` ($\text{MDD} > 15\%$).

---

## 5. Analysis C — Diagnosis Tingkat Aset (*Asset-Level Diagnosis*)

Evaluasi terpisah terhadap seluruh 10 aset primer penelitian (data tersimpan di `MILESTONE_4_ASSET_DIAGNOSIS.csv`):

| Simbol Aset | Jumlah Trade | Gross PnL (USD) | Net PnL (USD) | Biaya Eksekusi (USD) | Gross Exp (bps) | Net Exp (bps) | Profit Factor | Fold Positif (dari 4) | Long Net Exp (bps) | Short Net Exp (bps) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **LINKUSDT** | 18,876 | $+\$721.88$ | **$+\$97.63$** | $\$624.25$ | **$+15.55$** | **$+2.21$** | **$1.034$** | **3 / 4** | **$+2.97$** | $-12.99$ |
| **DOGEUSDT** | 94,155 | **$+\$3,281.22$** | $-\$84.30$ | $\$3,365.52$ | **$+12.95$** | $-0.47$ | $0.995$ | **3 / 4** | **$-0.01$** | $-21.82$ |
| **AVAXUSDT** | 35,781 | $+\$558.68$ | $-\$704.26$ | $\$1,262.94$ | $+7.21$ | $-6.06$ | $0.876$ | 1 / 4 | $-4.31$ | $-19.72$ |
| **XRPUSDT** | 132,678 | $+\$2,096.16$ | $-\$2,933.16$ | $\$5,029.32$ | $+7.07$ | $-6.35$ | $0.863$ | 1 / 4 | $-6.19$ | $-14.12$ |
| **ADAUSDT** | 104,437 | $+\$1,251.40$ | $-\$2,984.20$ | $\$4,235.60$ | $+3.64$ | $-9.85$ | $0.855$ | 1 / 4 | $-9.62$ | $-22.52$ |
| **SOLUSDT** | 135,315 | $+\$207.30$ | **$-\$4,708.06$** | $\$4,915.36$ | $+1.51$ | $-11.98$ | $0.761$ | 0 / 4 | $-11.95$ | $-13.91$ |
| **ETHUSDT** | 5,700 | $-\$6.65$ | $-\$149.83$ | $\$143.18$ | $-0.67$ | $-13.96$ | $0.699$ | 0 / 4 | $-15.75$ | $-9.05$ |
| **BTCUSDT** | 6,129 | $-\$6.01$ | $-\$159.64$ | $\$153.63$ | $-0.15$ | $-13.43$ | $0.588$ | 0 / 4 | $-13.86$ | $-12.61$ |
| **LTCUSDT** | 5,502 | $-\$81.35$ | $-\$251.84$ | $\$170.49$ | $-9.05$ | $-22.56$ | $0.721$ | 0 / 4 | $-26.04$ | $-9.84$ |
| **BNBUSDT** | 13,733 | $-\$4.23$ | $-\$324.04$ | $\$319.81$ | $-0.25$ | $-13.53$ | $0.658$ | 0 / 4 | $-13.59$ | $-13.42$ |

### 5.1 Temuan Diagnosis Aset Utama
1. **Aset Berperforma Alpha Terbaik:**
   - **LINKUSDT** adalah **satu-satunya aset di seluruh panel historis yang mencetak net profit positif ($+\$97.63$)** di bawah simulasi Bybit VIP0, dengan Gross Exp $+15.55\text{ bps}$, Net Exp $+2.21\text{ bps}$, Profit Factor $1.034$, dan stabilitas fold positif pada 3 dari 4 fold.
   - **DOGEUSDT** menghasilkan gross alpha tertinggi ($+\$3,281.22$ Gross PnL, $+12.95\text{ bps}$ Gross Exp) dan posisi Long-nya berada pada titik impas sempurna ($-0.01\text{ bps}$ net) setelah membayar biaya bursa secara penuh. Kerugian DOGE murni diakibatkan oleh posisi Short ($-21.82\text{ bps}$).
2. **Aset Perusak Modal Terbesar (*Capital Drain Asset*):**
   - **SOLUSDT** adalah aset penghasil kerugian bersih terbesar ($-\$4,708.06$ Net PnL), dengan turnover tertinggi ($135,315\text{ trades}$) namun gross expectancy sangat tipis ($+1.51\text{ bps}$), sehingga $100\%$ modal tersedot biaya eksekusi ($\$4,915.36$).
3. **Aset Mega-Cap (BTC, ETH, BNB):**
   - Menghasilkan frekuensi perdagangan sangat rendah ($5,000\text{–}13,000\text{ trades}$ across 300 strategies) dan gross expectancy mendekati nol ($-0.15\text{ bps}$ hingga $-0.67\text{ bps}$). Net expectancy persis sama dengan drag biaya eksekusi ($-13.4\text{ bps}$ hingga $-13.9\text{ bps}$). Alpha mikrostruktur 5m tidak bekerja pada mega-cap karena efisiensi pasar yang sangat tinggi.
4. **Status Aset Sekunder XMR (Monero):**
   - Sesuai protokol tata kelola, XMR tetap berstatus *secondary exploratory asset* dan secara ketat tidak disertakan dalam panel primer di atas untuk mencegah bias likuiditas dan regulasi delisting.

---

## 6. Analysis D — Diagnosis Rezim Pasar (*Market Regime Diagnosis*)

Kondisi pasar diklasifikasikan secara deterministik ke dalam 4 kuadran berdasarkan median empiris dari $552,306$ perdagangan:
- **Ambang Volatilitas:** Median $\sigma_{20} = 0.005198$ ($51.98\text{ bps}$).
  - *High Volatility:* $\sigma \ge 0.005198$
  - *Low Volatility:* $\sigma < 0.005198$
- **Ambang Tren:** Median $| \text{HTF\_12\_bps} | = 189.05\text{ bps}$ (return absolut 1 jam).
  - *Trending:* $| \text{HTF\_12} | \ge 189.05\text{ bps}$
  - *Ranging:* $| \text{HTF\_12} | < 189.05\text{ bps}$

Data lengkap tersimpan pada:  
`audit/strategy_research/milestone_4_alpha_failure_diagnosis/MILESTONE_4_REGIME_DIAGNOSIS.csv`

#### Tabel Performa 4 Kuadran Rezim Pasar
| Kuadran Rezim Pasar | Jumlah Trade | Porsi Armada | Gross Exp (bps) | Net Exp (bps) | Drag Friksi (bps) | Win Rate Net | Profit Factor | Gross PnL (USD) | Net PnL (USD) | Total Friksi (USD) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **HIGH_VOLATILITY_TRENDING** | **167,772** | **30.38%** | **+21.22** | **+7.88** | 13.34 | **41.59%** | **1.096** | **+$9,395.51** | **+$3,058.71** | $\$6,336.80$ |
| **HIGH_VOLATILITY_RANGING** | 108,388 | 19.62% | -6.27 | -19.85 | 13.58 | 34.47% | 0.722 | -$1,723.13$ | -$5,913.40$ | $\$4,190.27$ |
| **LOW_VOLATILITY_RANGING** | 167,580 | 30.34% | +0.47 | -13.01 | 13.48 | 34.52% | 0.708 | -$232.57$ | -$6,099.57$ | $\$5,867.01$ |
| **LOW_VOLATILITY_TRENDING** | 108,566 | 19.66% | +2.53 | -10.82 | 13.35 | 35.61% | 0.776 | +$578.60$ | -$3,247.42$ | $\$3,826.02$ |

### 6.1 Analisis Dampak Rezim Pasar
Tabel di atas menyajikan temuan paling fundamental dari seluruh riset QUANTUM:
1. **Kuadran Satu-Satunya Penghasil Profit:**
   - **`HIGH_VOLATILITY_TRENDING`** adalah satu-satunya rezim di mana strategi membukukan profit riil ($+\$3,058.71$ net PnL, $+7.88\text{ bps}$ net expectancy, Profit Factor $1.096$). Pada rezim ini, alpha kotor ($+21.22\text{ bps}$) cukup besar untuk melampaui dan menelan biaya friksi ($13.34\text{ bps}$).
2. **Rezim Pemusnah Modal (*The Capital Destroyers*):**
   - Gabungan kuadran `HIGH_VOLATILITY_RANGING` dan `LOW_VOLATILITY_RANGING` mencakup **$49.96\%$ perdagangan ($275,968\text{ trades}$)**.
   - Kedua kuadran ranging ini membukukan kerugian bersih gabungan sebesar **$-\$12,012.97$**, yang sepenuhnya melenyapkan keuntungan $+\$3,058.71$ dari pasar trending!
   - Di pasar *low-vol ranging*, harga bergerak sempit sehingga gross edge hanya $+0.47\text{ bps}$, sementara bursa menagih biaya $13.48\text{ bps}$, menciptakan kehancuran matematis pasti.
3. **Penyebab Utama Kegagalan Terbukti:**
   - Strategi historis **gagal karena tidak memiliki mekanisme penonaktifan (*circuit breaker / regime filter*)** saat pasar berada dalam kondisi berkonsolidasi (*ranging/choppy*).

---

## 7. Analysis E & F — Evaluasi Kelayakan & Matriks Prioritas Riset Session 2

Berdasarkan analisis kelayakan mendalam pada [`MILESTONE_4_ALPHA_FAMILY_FEASIBILITY.md`](file:///d:/quantum-multi-agent/audit/strategy_research/milestone_4_alpha_failure_diagnosis/MILESTONE_4_ALPHA_FAMILY_FEASIBILITY.md) dan pemeringkatan pada [`MILESTONE_4_RESEARCH_PRIORITY_MATRIX.csv`](file:///d:/quantum-multi-agent/audit/strategy_research/milestone_4_alpha_failure_diagnosis/MILESTONE_4_RESEARCH_PRIORITY_MATRIX.csv), ditentukan **tiga hipotesis penelitian teratas** yang memenuhi syarat untuk dieksplorasi pada Session 2:

### Tabel 3 Hipotesis Penelitian Terpilih (Prioritas Session 2)
```
+------+------------------------------------+--------------------------+-------+------------------------------------------+
| Rank | ID Hipotesis                       | Keluarga Alpha           | Skor  | Status Keputusan                         |
+------+------------------------------------+--------------------------+-------+------------------------------------------+
| 1    | HYP_01_VOL_EXPANSION_HTF_MOMENTUM  | Short-Term Momentum      | 34/35 | APPROVED FOR SESSION 2 EXPERIMENTATION   |
| 2    | HYP_02_LIQUIDITY_SWEEP_RECLAIM_MAKER| Liquidity Dynamics       | 29/35 | APPROVED FOR SESSION 2 EXPERIMENTATION   |
| 3    | HYP_03_REGIME_FILTERED_MEAN_REV   | Mean Reversion           | 28/35 | APPROVED FOR SESSION 2 EXPERIMENTATION   |
+------+------------------------------------+--------------------------+-------+------------------------------------------+
```

#### Ringkasan Desain Eksperimen Rekomendasi (Non-Implementatif):
1. **HYP-01: Multi-Timeframe Volatility Expansion Trend Following (Horizon $\ge 30\text{m}$, Regime Filtered)**
   - *Mekanisme:* Hanya aktif saat $\sigma_{20} \ge \text{median}$ dan $|\text{HTF\_12}| \ge 189\text{ bps}$. Memperpanjang horizon pemegangan dari 5 menit ke 30–60 menit untuk menangkap pergerakan markout $+19.78\text{ bps}$ dan menghindari noise stop-out Bar 1.
   - *Ambang Falsifikasi:* Net expectancy $< 5.0\text{ bps}$ pada Bybit VIP0 atau positive fold $< 3/4$.
2. **HYP-02: Key-Level Liquidity Sweep & Reclaim with Passive Limit Order Placement**
   - *Mekanisme:* Menunggu konfirmasi penembusan semu (*sweep*) dan reclaim lilin pada level swing high/low HTF. Entri menggunakan pesanan LIMIT pasif pada level reclaim (menikmati maker fee $4.0\text{ bps}$, spread 0, slip 0).
   - *Ambang Falsifikasi:* Maker fill rate $< 35\%$ atau post-fill adverse selection $> 4.0\text{ bps}$.
3. **HYP-03: Regime-Filtered 3-Sigma Extreme Band Reversion in Low-Vol Ranging Markets**
   - *Mekanisme:* Hanya aktif pada kuadran Low-Vol Ranging dengan pita deviasi ekstrim $\ge 3\text{-sigma}$ untuk memastikan jarak target keuntungan $\ge 25\text{ bps}$.
   - *Ambang Falsifikasi:* Gross edge $< 18.0\text{ bps}$ atau Stop-Loss rate $> 55\%$.

---

## 8. Final Research Decision Classification

Sesuai ketentuan mandat tata kelola Milestone 4, diputuskan klasifikasi status penelitian final sebagai berikut:

```
========================================================================================
                          FINAL RESEARCH DECISION CLASSIFICATION:
                                      MIXED_FAILURE
              (EXECUTION_COST_DOMINANT + TRADE_SELECTION_REGIME_MISMATCH)
========================================================================================
```

### Justifikasi Komprehensif:
1. **Bukan `WEAK_OR_ABSENT_ALPHA` Murni:** Karena gross expectancy armada terbukti positif ($+5.98\text{ bps}$ agregat, $+21.22\text{ bps}$ pada tren bervolatilitas tinggi, markout 60m $+19.78\text{ bps}$, dan aset LINK membukukan net profit). Alpha prediktif ada secara objektif.
2. **Bukan `EXECUTION_COST_DOMINANT` Murni:** Meskipun friksi memakan 224% hingga 675% edge, jika pasar berada dalam regime High-Vol Trending, strategi mampu menghasilkan net profit $+\$3,058.71$ meskipun membayar friksi taker penuh.
3. **Klasifikasi Tepat adalah `MIXED_FAILURE`:**
   - Kegagalan terjadi akibat interaksi mematikan antara **friksi eksekusi tinggi pada time frame pendek (5m)** dan **kegagalan seleksi perdagangan (*trade selection failure*)** yang menembakkan $50\%$ posisi ke rezim *ranging* tanpa alpha, sehingga modal habis tergerus oleh *noise stop-out* dan komisi bursa.

---

## 9. Final Integrity & Governance Check

Sebelum menutup Milestone 4, seluruh batasan operasional telah diverifikasi secara independen:
1. **Holdout Scope Isolation:** Stempel waktu prospektif $\ge 1793491200000\text{ ms}$ (2026-11-01 00:00:00 UTC) **SEALED & UNTOUCHED**. Tidak ada satu pun bar, trade, atau metrik holdout yang diakses.
2. **Production Code Integrity:** Tidak ada kode produksi di `src/quantum/` atau arsitektur enam-agent yang dimodifikasi. Seluruh skrip audit dijalankan di `scratch/`.
3. **Data Completeness & Zero Missing Values:** Seluruh $552,306$ perdagangan pada skenario Bybit VIP0 telah dipetakan $100\%$ tanpa ada nilai yang hilang (`Missing count: 0`).
4. **Reproducibility:** Seluruh 4 file CSV dan 2 file Markdown tersimpan lengkap di:
   `audit/strategy_research/milestone_4_alpha_failure_diagnosis/`
   - `MILESTONE_4_ALPHA_FAILURE_DIAGNOSIS.md`
   - `MILESTONE_4_LOSS_DECOMPOSITION.csv`
   - `MILESTONE_4_ASSET_DIAGNOSIS.csv`
   - `MILESTONE_4_REGIME_DIAGNOSIS.csv`
   - `MILESTONE_4_ALPHA_FAMILY_FEASIBILITY.md`
   - `MILESTONE_4_RESEARCH_PRIORITY_MATRIX.csv`

---
*Dokumen ini mengakhiri Milestone 4: Alpha Failure Diagnosis & Research Direction. Seluruh artefak siap untuk diajukan kepada Project Owner untuk peninjauan formal sebelum pembukaan Session 2.*
