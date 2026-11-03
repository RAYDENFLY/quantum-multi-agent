# QUANTUM — MILESTONE 4: ALPHA FAMILY FEASIBILITY EVALUATION
## Forensic Feasibility Analysis Across Candidate Quantitative Alpha Families

**Dokumen Identifikasi:** `audit/strategy_research/milestone_4_alpha_failure_diagnosis/MILESTONE_4_ALPHA_FAMILY_FEASIBILITY.md`  
**Tanggal Publikasi:** 2026-11-03 19:25:00 UTC  
**Branch Penelitian:** `research/high-turnover-alpha-feasibility`  
**Baseline Git Commit:** `dcc8ceb54d80b1b9685d92236f48b0994610522a`  
**Status Prospective Holdout:** **SEALED & UNTOUCHED** ($\ge 1793491200000\text{ ms}$ / 2026-11-01 00:00:00 UTC)  
**Tujuan Dokumen:** Evaluasi kelayakan teoretis, empiris, struktural mikrostruktur, dan eksekusi terhadap 3 keluarga hipotesis alpha quantitatif untuk memandu arah penelitian Session 2 tanpa klaim profitabilitas prematur.

---

## 1. Executive Summary & Evaluasi Komparatif

Berdasarkan hasil re-evaluasi 900 uji simulasi pada Milestone 3 dan diagnosis empiris trade-level pada Milestone 4 ($N = 552,306\text{ trades}$), kegagalan armada strategi 5-menit historis membuktikan bahwa **alpha gross marjinal ($+5.98\text{ bps}$) tidak dapat bertahan melawan friksi eksekusi riil ($13.43\text{ bps}$ Bybit VIP0 / $38.68\text{ bps}$ Aster)** jika dipadukan dengan *stop-out* prematur akibat *noise* (60.63% stop-loss rate, 29.08% trade keluar di Bar 1).

Dokumen ini melakukan audit kelayakan terperinci terhadap 3 keluarga hipotesis kuantitatif utama:
1. **Liquidity Dynamics** (Microstructure, Sweeps, Absorption, Imbalance)
2. **Short-Term Momentum** (Breakout Continuation, Momentum Persistence, Volatility Expansion)
3. **Mean Reversion** (Short-term Overextension, Deviation from Rolling Mean, Volatility-Adjusted Reversion)

Setiap keluarga dianalisis secara objektif terhadap 7 dimensi evaluasi wajib:
- Mekanisme Pasar (*Market Mechanism*)
- Data yang Dibutuhkan (*Required Data*)
- Bukti yang Tersedia (*Evidence Available*)
- Keterbatasan Saat Ini (*Current Limitations*)
- Sensitivitas Eksekusi (*Expected Execution Sensitivity*)
- Kriteria Falsifikasi (*Falsification Criteria*)
- Peringkat Kelayakan (*Feasibility Rating*)

### Ringkasan Peringkat Kelayakan Alpha Families

| Alpha Family | Sub-Mekanisme Utama | Status Ketersediaan Data | Sensitivitas Friksi Eksekusi | Net Edge Potential | Peringkat Kelayakan (*Feasibility Rating*) | Rekomendasi Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Short-Term Momentum** | Volatility Expansion & HTF Continuation | **LENGKAP** (OHLCV 5m + HTF + Sigma) | **SEDANG** (Dapat menyerap 15 bps fee jika $\Delta t \ge 30\text{m}$) | **TINGGI** (+21.22 bps gross pada High-Vol Trend) | **HIGH FEASIBILITY** | **PRIORITAS UTAMA** (Lolos ke Eksperimen Session 2) |
| **Liquidity Dynamics** | Sweep & Reclaim + Maker Limit Queuing | **PARSIAL** (Wick, Volume, Taker Ratio; L2 Depth Tidak Ada) | **SANGAT TINGGI** (Wajib Maker 4 bps / 0 spread) | **MODERAT** (+15.55 bps gross pada LINK/DOGE) | **MODERATE FEASIBILITY** | **PRIORITAS KEDUA** (Hanya varian Reclaim + Limit Order) |
| **Mean Reversion** | 3-Sigma Extreme Band Reversion | **LENGKAP** (Rolling Mean, Sigma, Bands) | **EKSTRIM** (Tergilas bila salah mendeteksi breakout) | **RENDAH** (+0.47 bps gross pada Ranging) | **CONDITIONAL LOW** | **PRIORITAS KETIGA** (Hanya dalam regime Low-Vol Ranging tervalidasi) |

---

## 2. Deep-Dive Alpha Family 1: Liquidity Dynamics

### 2.1 Sub-Mekanisme Pasar (*Market Mechanisms*)
Keluarga *Liquidity Dynamics* bertumpu pada interaksi struktural antara likuiditas pasif di buku pesanan (*resting limit orders*) dan likuiditas agresif (*market orders / stop-loss cascades*):
1. **Liquidity Sweep (Stop-Run):** Harga sengaja menembus level *swing high/low* yang jelas untuk memicu *stop-loss cluster* milik pelaku pasar ritel. Setelah likuiditas terserap, tekanan beli/jual agresif habis.
2. **Absorption:** Partisipan institusional menyerap pesanan pasar agresif menggunakan pesanan pasif bertingkat (*iceberg / large limit orders*), terlihat dari tingginya volume perdagangan tanpa pergeseran harga yang sebanding.
3. **Imbalance:** Ketidakseimbangan sepihak antara volume *taker buy* dan *taker sell* (*order flow imbalance*) yang menyebabkan pergeseran harga jangka pendek.
4. **Sweep and Reclaim:** Setelah harga menembus level likuiditas secara tajam (*sweep*), lilin ditutup kembali ke dalam rentang sebelumnya (*reclaim*), mengindikasikan kegagalan kelanjutan dan kemungkinan pembalikan harga berkecepatan tinggi.

### 2.2 Data yang Dibutuhkan (*Required Data*)
- **Data Ideal:** Full Level-3 / Level-2 Tick-by-Tick Order Book (DOM Depth snapshots $\le 100\text{ms}$), Tick Trades dengan penanda agresor (Buy/Sell initiator), Real-Time Liquidation Feed.
- **Data Tersedia dalam QUANTUM Pre-Holdout:**
  - Bar agregat 5-menit: Open, High, Low, Close, Volume.
  - Proksi mikrostruktur turunan: `taker_buy_ratio`, `upper_wick`, `lower_wick`, `vol_exp_ratio`, `rvol_20`.

### 2.3 Bukti Empiris yang Tersedia (*Evidence Available*)
- Dari dataset re-evaluasi 300 strategi, famili `LIQUIDITY_MICROSTRUCTURE` mencakup 180 strategi (60% armada).
- **Performa Historis (Bybit VIP0):** Menghasilkan gross PnL terbesar di armada ($+\$5,534.58$) dengan gross expectancy rata-rata $+7.03\text{ bps}$.
- **Kelemahan Fatal:** Seluruh $+7.03\text{ bps}$ gross edge terhapus oleh rata-rata friksi eksekusi sebesar $13.53\text{ bps}$ ($192.6\%$ gross edge terkonsumsi), menghasilkan net expectancy $-6.50\text{ bps}$ dan total net loss $-\$6,851.34$.
- **Perilaku Sumbu Lilin (*Wicks*):** Pada aset dengan likuiditas tinggi seperti LINKUSDT ($+15.55\text{ bps}$ gross expectancy) dan DOGEUSDT ($+12.95\text{ bps}$ gross expectancy), sinyal *wick rejection* memiliki korelasi prediktif positif, namun terdistorsi oleh pengisian agresif (*market entry*) yang membayar spread 2.0 bps dan slippage 2.0 bps.

### 2.4 Keterbatasan Saat Ini (*Current Limitations*)
1. Tidak ada data kedalaman buku pesanan L2/L3 historis dalam database; simulator saat ini mengasumsikan kedalaman tak terbatas pada harga pasar.
2. Heuristik pengisian pesanan batas pasif (*limit order fill model*) pada boundary touch masih menggunakan probabilitas unkalibrasi (50% touch seed), belum merefleksikan dinamika antrean riil (*queue priority*).
3. Penempatan batas pasif tanpa filter penyerapan (*absorption*) rentan terhadap *adverse selection* (pesanan hanya terisi saat pasar bergerak menembus level tersebut secara agresif).

### 2.5 Sensitivitas Eksekusi (*Expected Execution Sensitivity*)
- **Sangat Tinggi.** Strategi ini hanya dapat bertahan hidup jika dieksekusi sebagai **MAKER murni** (biaya masuk $\le 4.0\text{ bps}$ VIP0 atau rabat negatif pada tier VIP institusional, spread 0.0 bps, slippage 0.0 bps).
- Jika dieksekusi dengan MARKET order (TAKER 11.0 bps + 2.0 bps spread + 2.0 bps slippage = 15.0 bps per leg), strategi dipastikan bangkrut secara matematis karena gross edge ($7.0\text{–}15.0\text{ bps}$) selalu lebih kecil dari friksi round-trip.

### 2.6 Kriteria Falsifikasi (*Falsification Criteria*)
Hipotesis Liquidity Dynamics (khususnya *Sweep and Reclaim*) dinyatakan **FALSIFIED** jika:
1. Realized maker fill rate pesanan limit pasif di bawah $35\%$ pada pengujian eksekusi simulasi berbasis tick.
2. Rata-rata *adverse selection markout* pada 3 bar pasca-pengisian melebihi $4.0\text{ bps}$ (mengindikasikan pesanan limit selalu menjadi likuiditas bagi pelaku pasar institusional yang lebih agresif).
3. Net expectancy setelah biaya maker riil ($4.0\text{ bps}$ masuk, $4.0\text{ bps}$ keluar) bernilai negatif ($< 0\text{ bps}$) pada walk-forward validasi.

### 2.7 Peringkat Kelayakan (*Feasibility Rating*): **MODERATE FEASIBILITY**
- **Justifikasi:** Memiliki fondasi mikrostruktur yang valid dan gross expectancy positif ($+7.03\text{ bps}$), tetapi **DIBATASI SECARA KETAT** hanya pada varian *Sweep and Reclaim* yang menggunakan pesanan LIMIT pasif dan membatasi TAKER exit. Sub-varian yang membutuhkan L2 depth dinyatakan tidak layak untuk fase saat ini.

---

## 3. Deep-Dive Alpha Family 2: Short-Term Momentum

### 3.1 Sub-Mekanisme Pasar (*Market Mechanisms*)
Keluarga *Short-Term Momentum* mengeksploitasi fenomena *autocorrelation* dan *underreaction* struktural:
1. **Breakout Continuation:** Penembusan batas volatilitas (misal: kanal Donchian atau Bollinger Band) memicu partisipasi terarah dari algoritma eksekusi institusional (*TWAP/VWAP buying*), menciptakan dorongan searah yang bertahan selama 30–120 menit.
2. **Momentum Persistence:** Adanya kelanjutan tren harga lokal akibat asimetri aliran pesanan (*persistent order flow imbalance*).
3. **Volatility Expansion:** Transisi dari fase kompresi volatilitas (*low-volatility regime*) ke fase ekspansi volatilitas (*volatility explosion*) yang menghasilkan pergerakan harga berlipat ganda dari rata-rata ATR.

### 3.2 Data yang Dibutuhkan (*Required Data*)
- **Data Ideal:** Bar multi-timeframe (1m, 5m, 15m, 1h), Volume terkonfirmasi, Indikator Volatilitas (ATR, Standard Deviation), Indikator Tren HTF.
- **Data Tersedia dalam QUANTUM Pre-Holdout:**
  - **Sangat Lengkap & Terverifikasi:**
    - `sigma_20` (volatilitas 20-bar)
    - `vol_exp_ratio` (rasio ekspansi volatilitas)
    - `htf_rets_bps[6, 12, 24, 48]` (return 30m, 1h, 2h, 4h)
    - `opens`, `highs`, `lows`, `closes`, `volume` pada 10 aset primer.

### 3.3 Bukti Empiris yang Tersedia (*Evidence Available*)
Hasil kuantitatif Milestone 4 memberikan bukti empiris terkuat untuk keluarga ini:
- **Kuadran HIGH_VOLATILITY_TRENDING ($N = 167,772\text{ trades}$ / 30.4% armada):**
  - **Gross Expectancy:** **$+21.22\text{ bps}$**
  - **Net Expectancy (Bybit VIP0 Taker):** **$+7.88\text{ bps}$**
  - **Profit Factor:** **$1.096$**
  - **Gross PnL:** **$+\$9,395.51$** | **Net PnL:** **$+\$3,058.71$**
  - Ini adalah **satu-satunya kuadran pasar dalam 552,306 trades yang menghasilkan net expectancy positif dan profit riil** di bawah simulasi remediated Bybit VIP0!
- **Analisis Durasi Pemegangan (*Holding Duration*):**
  - Perdagangan yang bertahan $> 6\text{ bars}$ ($> 30\text{ menit}$) menghasilkan **Gross Expectancy $+48.50\text{ bps}$** dan **Net Expectancy $+35.34\text{ bps}$** ($N = 180,994\text{ trades}$).
- **Post-Fill Markout Profile:**
  - Markout 12-bar (60 menit) rata-rata adalah **$+19.78\text{ bps}$**, membuktikan adanya kelanjutan pergerakan searah yang signifikan dalam cakrawala 1 jam.
- **Penyebab Kegagalan Historis:** Strategi momentum historis gagal bukan karena momentum tidak ada, melainkan karena:
  1. Dicampur secara membabi buta dengan perdagangan pada kondisi *ranging* ($50\%$ perdagangan dieksekusi di regime ranging yang merugi $-\$12,012$).
  2. Menggunakan *barrier stop-loss* 5-menit yang terlalu ketat, menyebabkan 29.08% posisi terkena stop-out prematur pada Bar 1 (merugi $-65.28\text{ bps}$ per trade).

### 3.4 Keterbatasan Saat Ini (*Current Limitations*)
1. Asimetri Long vs Short: Short momentum pada altcoin selama fase ekspansi pasar kripto mengalami kerugian parah (Short net expectancy $-15.53\text{ bps}$ vs Long $-7.22\text{ bps}$).
2. *Whipsaw risk:* Membutuhkan mekanisme deteksi *false breakout* yang andal untuk mencegah entri pada akhir pergerakan impulsif.

### 3.5 Sensitivitas Eksekusi (*Expected Execution Sensitivity*)
- **Moderat.** Karena target gross expectancy pada regime ini mencapai $+25\text{–}45\text{ bps}$, strategi momentum berbasis durasi $\ge 30\text{ menit}$ memiliki kapasitas struktural untuk menyerap biaya taker Bybit VIP0 ($15.0\text{ bps}$ round-trip) dan tetap mencetak net margin $+10\text{–}25\text{ bps}$.
- Namun, strategi ini tidak tahan terhadap friksi ekstrem Aster Stress ($44.0\text{ bps}$ round-trip) kecuali rasio *take-profit* dinaikkan ke level $> 60\text{ bps}$.

### 3.6 Kriteria Falsifikasi (*Falsification Criteria*)
Hipotesis Short-Term Momentum dinyatakan **FALSIFIED** jika:
1. Net expectancy di bawah $+5.0\text{ bps}$ di bawah skenario `BYBIT_VIP0_DEFAULT` setelah menyaring trade non-trending.
2. Rasio kemenangan (*win rate*) di bawah $40\%$ dengan rasio *payoff* $< 1.5$.
3. Gagal mencatat net profit kumulatif pada minimal 3 dari 4 fold walk-forward out-of-fold.

### 3.7 Peringkat Kelayakan (*Feasibility Rating*): **HIGH FEASIBILITY**
- **Justifikasi:** Didukung oleh bukti kuantitatif empiris terkuat di seluruh repository QUANTUM (+21.22 bps gross, +7.88 bps net pada high-vol trending, markout 60m +19.78 bps). Data 100% tersedia dalam pipeline saat ini tanpa dependensi eksternal baru.

---

## 4. Deep-Dive Alpha Family 3: Mean Reversion

### 4.1 Sub-Mekanisme Pasar (*Market Mechanisms*)
Keluarga *Mean Reversion* mengeksploitasi kecenderungan harga untuk kembali ke nilai rata-rata (*equilibrium price*):
1. **Short-Term Overextension:** Pergerakan harga impulsif yang terlalu cepat menjauhi moving average lokal akibat likuidasi sepihak, menciptakan kondisi jenuh beli/jenuh jual (*exhaustion*).
2. **Deviation from Rolling Mean:** Osilasi harga di sekitar garis tengah (*mean anchor*) seperti VWAP atau EMA 50-periode.
3. **Volatility-Adjusted Reversion:** Pembalikan harga yang dihitung menggunakan pita volatilitas statistik (misal: 2-sigma atau 3-sigma Keltner / Bollinger bands).

### 4.2 Data yang Dibutuhkan (*Required Data*)
- **Data Tersedia:** Lengkap dalam pipeline: Moving Averages, Standard Deviation, RSI/Z-scores, Range High/Low.

### 4.3 Bukti Empiris yang Tersedia (*Evidence Available*)
- Dari dataset 300 strategi historis, famili `MEAN_REVERSION_BREAKOUT` mencakup 20 strategi.
- **Performa Historis (Bybit VIP0):**
  - Gross expectancy rata-rata hanya **$+3.67\text{ bps}$**.
  - Net expectancy rata-rata **$-9.73\text{ bps}$**.
  - Friksi eksekusi rata-rata $13.40\text{ bps}$ mengkonsumsi **$365.0\%$** dari gross edge!
  - Net PnL kumulatif: $-\$762.19$.
- **Performa pada Kuadran Ranging (Milestone 4 Diagnosis):**
  - `LOW_VOLATILITY_RANGING` ($N = 167,580\text{ trades}$): Gross expectancy hanya **$+0.47\text{ bps}$**, Net expectancy **$-13.01\text{ bps}$**, Net loss $-\$6,099.57$.
  - `HIGH_VOLATILITY_RANGING` ($N = 108,388\text{ trades}$): Gross expectancy **$-6.27\text{ bps}$**, Net expectancy **$-19.85\text{ bps}$**, Net loss $-\$5,913.40$.

### 4.4 Keterbatasan Saat Ini (*Current Limitations*)
1. **Besaran Target Keuntungan (*Target Amplitude*) Terlalu Kecil:** Pada pasar ranging berfluktuasi rendah, deviasi harga ke mean hanya berjarak $5\text{–}12\text{ bps}$. Jarak ini secara matematis tidak mampu menutupi friksi round-trip $15.0\text{ bps}$.
2. **Risiko Tren Kuat (*Steamroller Risk*):** Ketika pasar mengalami *breakout* atau tren kuat, strategi *mean reversion* terus membuka posisi melawan tren (*averaging down / premature counter-trend*), memicu *stop-loss* berulang kali (terbukti dari rata-rata 21 kekalahan beruntun di armada).

### 4.5 Sensitivitas Eksekusi (*Expected Execution Sensitivity*)
- **Ekstrim.** Mean reversion pada time frame 5-menit adalah korban terbesar dari friksi eksekusi. Strategi ini mengalami kebangkrutan terparah karena *edge* kotornya ($+0.47\text{ bps}$ hingga $+3.67\text{ bps}$) adalah yang paling tipis di antara seluruh keluarga strategi.

### 4.6 Kriteria Falsifikasi (*Falsification Criteria*)
Hipotesis Mean Reversion dinyatakan **FALSIFIED** jika:
1. Rata-rata jarak pembalikan (*mean reversion distance*) lebih kecil dari $25.0\text{ bps}$ pada aset target.
2. Gross expectancy gagal melampaui $18.0\text{ bps}$ (ambang batas minimum untuk menutupi biaya Bybit VIP0).
3. Frekuensi Stop-Loss melampaui $55\%$ dari total eksekusi.

### 4.7 Peringkat Kelayakan (*Feasibility Rating*): **CONDITIONAL LOW FEASIBILITY**
- **Justifikasi:** Secara empiris terbukti memiliki gross edge paling lemah ($+3.67\text{ bps}$) dan paling rentan terhadap kehancuran oleh friksi biaya eksekusi ($365\%$ edge terhapus). Hanya dapat dipertimbangkan jika menggunakan pita deviasi ekstrim ($\ge 3\text{-sigma}$) pada aset dengan volatilitas tinggi seperti DOGE atau SOL dan mewajibkan eksekusi limit pasif.

---

## 5. Ringkasan Matriks Perbandingan & Kesimpulan Kelayakan

```
+---------------------------+-----------------------+-----------------------+-----------------------+
| Dimensi Evaluasi          | 1. Liquidity Dynamics | 2. Short-Term Momentum| 3. Mean Reversion     |
+---------------------------+-----------------------+-----------------------+-----------------------+
| Gross Edge Empiris        | +7.03 bps             | +21.22 bps (HTF Trend)| +3.67 bps             |
| Net Edge (Bybit VIP0)     | -6.50 bps             | +7.88 bps (HTF Trend) | -9.73 bps             |
| Ketahanan Friksi          | Rentan (Wajib Maker)  | Kuat jika duration>30m| Sangat Rapuh          |
| Kesiapan Data             | Parsial (Proksi Wick) | 100% Tersedia         | 100% Tersedia         |
| Kompleksitas Eksekusi     | Tinggi (Antrean Limit)| Rendah (Market/Limit) | Sedang (Limit Bands)  |
| Durasi Optimal            | 10-30 menit           | 30-120 menit          | 5-15 menit            |
| Status Kelayakan          | MODERATE              | HIGH (Rekomendasi #1) | CONDITIONAL LOW       |
+---------------------------+-----------------------+-----------------------+-----------------------+
```

### Kesimpulan Strategis
Penelitian Session 2 **TIDAK BOLEH** melanjutkan model *high-turnover scalping* 5-menit umum yang mengandalkan mean reversion frekuensi tinggi. Arah riset yang memiliki probabilitas keberhasilan tertinggi secara matematis dan empiris adalah memfokuskan sumber daya komputasi pada **Short-Term Momentum dengan Filter Rezim Multi-Timeframe (HYP-01)**, didukung secara selektif oleh **Liquidity Sweep and Reclaim berbasis Pasif Limit (HYP-02)**.
