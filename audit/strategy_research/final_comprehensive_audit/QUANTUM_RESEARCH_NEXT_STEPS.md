# QUANTUM — ROADMAP PENELITIAN & LANGKAH PENELITIAN BERIKUTNYA
## Dari Evaluasi Kelayakan Menuju Alpha Berkelanjutan yang Tahan Biaya Transaksi

**Dokumen Identifikasi:** `audit/strategy_research/final_comprehensive_audit/QUANTUM_RESEARCH_NEXT_STEPS.md`  
**Klasifikasi:** Research Strategy & Engineering Roadmap  
**Tanggal Publikasi:** 2026-11-03 18:05:00 UTC  
**Penulis:** Senior Quantitative Research Auditor & Algorithmic Trading Research Engineer  
**Status Tata Kelola:** **RECOMMENDATIONS FOR PROJECT OWNER REVIEW — STRICT RESEARCH STANDBY**  
**Proteksi Holdout:** **STRICTLY SEALED** ($\ge 1793491200000\text{ ms}$ / 2026-11-01 00:00:00 UTC)  

---

## 1. Ringkasan Eksekutif & Prinsip Panduan

Berdasarkan temuan audit komprehensif, hipotesis awal mengenai **eksekusi taker frekuensi tinggi pada timeframe 5 menit dengan target agresif $+3.0\%/\text{hari}$ telah gugur secara definitif**. Margin perdagangan kotor rata-rata pada barrier 5 menit ($15\text{–}30\text{ bps}$) tidak mampu menutupi friksi transaksi taker yang realistis ($15.0\text{ bps}$ Bybit VIP0 hingga $44.0\text{ bps}$ AsterDex).

Roadmap penelitian ini mengalihkan fokus kuantitatif QUANTUM dari *brute-force parameter search* pada data mikro 5 menit yang rapuh menuju **tiga pilar alpha struktural yang terbukti memiliki daya tahan biaya (cost-resilient)**:
1. **Pelebaran Timeframe (Multi-Timeframe 15m / 1h / 4h):** Memperlebar jarak barrier sehingga margin kotor rata-rata mencapai $80\text{–}250\text{ bps}$, mendilusi dampak friksi transaksi hingga rasio friksi terhadap gross profit berada di bawah $15\%$.
2. **Eksekusi Passive Maker & Penyediaan Likuiditas (Track 3):** Membangun infrastruktur antrean order book Level 2 untuk menangkap bid-ask spread dan rebate fee maker, alih-alih membayar biaya taker.
3. **Penyelarasan Rezim & Cross-Asset Lead-Lag:** Menghentikan perdagangan dua arah tanpa filter tren makro (yang terbukti merusak portofolio melalui posisi short altcoin yang rugi besar) dan menerapkan conditioning berbasis kepemimpinan BTC/ETH dan ekspansi volatilitas.

---

## 2. Rincian Fase Penelitian Berikutnya

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           ROADMAP PENELITIAN QUANTUM                             │
├─────────────────┬─────────────────┬──────────────────┬───────────────────────────┤
│ GATELINK 1      │ GATELINK 2      │ GATELINK 3       │ GATELINK 4                │
│ Verifikasi &    │ Kesiapan Data & │ Validasi Alpha   │ Validasi Eksekusi &       │
│ Rekonsiliasi    │ Pipeline 1m/1h  │ Statistik Multi-TF│ Pengamatan Shadow         │
│ (Selesai)       │ (Fase Segera)   │ (Fase Riset)     │ (Pra-Deployment)          │
└─────────────────┴─────────────────┴──────────────────┴───────────────────────────┘
```

---

### FASE 1: Verifikasi Segera & Pembekuan Tata Kelola (Immediate Verification)

**Tujuan:** Memastikan integritas repositori, konsistensi branch, dan penutupan formal Session 1.5.

1. **Ratifikasi Audit Final:**
   - Menyajikan laporan `QUANTUM_COMPREHENSIVE_HISTORICAL_AUDIT.md` dan `QUANTUM_EXPERIMENT_COMPARISON.csv` kepada Human Governance Supervisor dan Project Owner.
   - Mengonfirmasi pencatatan diskualifikasi resmi atas 295 strategi discovery historis (termasuk STRAT_242).
2. **Karantina Branch & Tagging:**
   - Memberikan Git tag formal pada commit saat ini: `git tag -a v0.5.6-audit-final -m "Formal acceptance of Session 1.5 and comprehensive historical audit"`.
   - Mengonfirmasi bahwa direktori prospective holdout ($\ge 1793491200000\text{ ms}$) tetap terkunci dan tidak pernah disentuh.
3. **Pembersihan Skrip Generator:**
   - Memperbaiki penunjukan parent strategy ID pada skrip eksplorasi di masa depan agar secara eksplisit menerima string ID (`parent_strategy_id="STRAT_134"`) bukan pengindeksan array dinamis (`b2_configs[0]`).

---

### FASE 2: Kesiapan Data & Ekspansi Multi-Timeframe (Data Readiness)

**Tujuan:** Mengatasi kelemahan terbesar sistem saat ini: ketiadaan data 1 menit dan struktur multi-timeframe.

1. **Backfill Data Historis 1 Menit (1m Candles):**
   - Mengunduh dan memvalidasi $\approx 16.25\text{ juta}$ bar 1m historis untuk 10 aset utama (2023–2026) dari Bybit dan AsterDex.
   - Menjalankan pipeline validasi OHLCV: pengecekan gap, duplikasi timestamp, deteksi flat candle, dan validasi strictly monotonic timestamp.
2. **Pembangunan Modul Resampling & Multi-Timeframe Matrix:**
   - Mengembangkan agregator berbasis causal tick/1m untuk menghasilkan bar 15m, 1h, dan 4h yang tersinkronisasi tanpa lookahead bias.
   - Menghasilkan feature matrix multi-timeframe: tren higher-timeframe (1h/4h EMA slope), relative volume multi-horizon, dan cross-asset lead-lag return.
3. **Penyimpanan Tick & Pipeline Level 2 (Bertahap):**
   - Membangun database lokal untuk trade ticks dan order book snapshots (top 50 levels) untuk 3 aset berlikuiditas tinggi (`BTCUSDT`, `ETHUSDT`, `SOLUSDT`).
   - Data ini khusus dialokasikan untuk kalibrasi empiris probabilitas antrean resting limit ($P_{\text{fill}}$ queue survival).

---

### FASE 3: Desain Hipotesis Penelitian Baru (Research Hypothesis Design)

Sebelum baris kode strategi baru ditulis, setiap hipotesis wajib didefinisikan secara matematis dengan kriteria falsifikasi yang ketat:

#### Hipotesis A: Ekspansi Volatilitas & Breakout Momentum 15m/1h (Cost-Resilient Directional)
- **Mekanisme Pasar:** Pelepasan kompresi volatilitas intraday menghasilkan autokorelasi return yang kuat jika didukung oleh arah momentum 4 jam.
- **Formulasi Entry:** Masuk LONG jika return 1h berada pada persentil $>90$, volatilitas 20-bar mengalami ekspansi ($>1.5\times$ moving average), dan funding rate 8 jam belum overextended ($<3.0\text{ bps}$).
- **Target Barrier:** TP dinamis $2.5\sigma$ ($\approx 120\text{–}180\text{ bps}$), SL $1.0\sigma$ ($\approx 50\text{–}70\text{ bps}$), horizon 12 bar (3 jam).
- **Sensitivitas Biaya:** Sangat rendah; margin kotor yang besar ($>100\text{ bps}$) membuat strategi tetap profitabel di bawah taker fee $15.0\text{ bps}$ Bybit VIP0.
- **Kriteria Falsifikasi:** Gross expectancy rata-rata $<35\text{ bps}$ atau win rate $<38\%$ pada data out-of-fold.

#### Hipotesis B: Sweep & Reclaim Likuiditas Intraday (Liquidity Absorption Reversal)
- **Mekanisme Pasar:** Penembusan level swing low/high intraday yang agresif memicu stop-loss ritel ke dalam antrean limit order institusional. Kegagalan harga untuk melanjutkan penembusan (rejection wick besar) menandakan absorpsi likuiditas.
- **Formulasi Entry:** Masuk LONG jika harga menembus level terendah 24 bar sebelumnya sebesar $>0.5\sigma$, namun candle ditutup kembali di atas level tersebut dengan lower wick $\ge 35\%$ dan volume $\ge 2.0\times$ volume rata-rata.
- **Target Barrier:** TP pada rolling VWAP intraday ($\approx 60\text{–}90\text{ bps}$), SL di bawah ujung wick penembusan ($\approx 30\text{–}40\text{ bps}$).
- **Kriteria Falsifikasi:** Net expectancy $\le 0\text{ bps}$ setelah memperhitungkan $15\text{ bps}$ round-trip taker friction.

#### Hipotesis C: Penyediaan Likuiditas Pasif Asimetris (Passive Maker Spread-Capture)
- **Mekanisme Pasar:** Selama rezim non-trending (ADX $<18$), harga berosilasi di sekitar order book micro-price. Menempatkan resting post-only limit orders di batas spread menangkap rebate fee dan separuh spread.
- **Formulasi Entry:** Resting post-only limit buy di bid level 1 jika markout model memprediksi aliran tidak beracun (toxic flow probability $<0.30$).
- **Manajemen Risiko:** Auto-cancel dalam 3 bar jika order tidak disentuh; immediate stop market jika adverse price movement $>0.8\sigma$.
- **Kriteria Falsifikasi:** Adverse selection drag $>3.0\text{ bps}$ atau rasio fill-to-cancel $<15\%$.

---

### FASE 4: Eksperimen Eksploratif & Validasi Statistik (Statistical Validation)

**Tujuan:** Menguji hipotesis di atas menggunakan metodologi pembuktian yang ketat.

1. **Purged Walk-Forward Cross-Validation (5 Folds):**
   - Evaluasi wajib menggunakan skema 5 fold temporal yang telah divalidasi pada Folds 1–4 (Folds 5 khusus eksplorasi).
   - Menerapkan temporal embargo sebesar 2 jam antara set training dan out-of-sample untuk mencegah serial leakage.
2. **Pengendalian False Discovery Rate (Holm-Bonferroni & White's Reality Check):**
   - Setiap batch pencarian dibatasi maksimal 20 variasi parameter per hipotesis.
   - P-value Sharpe ratio dan cumulative return wajib dikoreksi terhadap pengujian berganda menggunakan prosedur step-down Holm-Bonferroni.
3. **Resampling MBB (Moving-Block Bootstrap):**
   - Menguji stabilitas kurva ekuitas melalui 1.000 iterasi Moving-Block Bootstrap (block size 7 hari).
   - Syarat kelulusan: Batas bawah 95% Confidence Interval untuk net daily return wajib bernilai positif ($\text{CI}_{\text{low}} > 0.0\%$).

---

### FASE 5: Validasi Simulasi Eksekusi Institusional (Execution Validation)

**Tujuan:** Menjalankan strategi yang lolos seleksi statistik melalui simulator eksekusi yang telah diremediasi.

1. **Jadwal Biaya Wajib:**
   - Setiap strategi wajib diuji secara terpisah pada dua skenario inti:
     1. `BYBIT_VIP0_DEFAULT`: $11.0\text{ bps}$ fee taker, $2.0\text{ bps}$ spread, $2.0\text{ bps}$ slippage ($15.0\text{ bps}$ RT).
     2. `ASTER_STRESS_TAKER`: $40.0\text{ bps}$ fee taker, $2.0\text{ bps}$ spread, $2.0\text{ bps}$ slippage ($44.0\text{ bps}$ RT).
2. **Kriteria Kelulusan Ketat (Non-Negotiable):**
   - Net Expectancy per trade: $\ge +12.0\text{ bps}$ (setelah seluruh friksi).
   - Profit Factor: $\ge 1.25$.
   - Maximum Portfolio Drawdown: $\le 20.0\%$ (pada portofolio multi-aset).
   - Konsistensi Fold: Minimal 4 dari 4 fold out-of-fold bernilai positif ($\ge 4/4$).
   - Recovery Factor: $\ge 2.0$.

---

### FASE 6: Pengamatan Paper/Shadow Trading (Shadow Observation)

**Tujuan:** Mengamati perilaku strategi pada aliran data pasar live tanpa risiko modal nyata.

1. **Integrasi Paper Daemon:**
   - Menghubungkan strategi yang lolos ke `PaperSimulator` (`src/quantum/daemon/paper_engine.py`) yang berjalan sebagai background service.
   - Mengonsumsi WebSocket live book depth dan trade tick stream dari Bybit dan AsterDex.
2. **Evaluasi Slippage Empiris & Markout Journal:**
   - Setiap eksekusi shadow wajib mencatat slippage riil terhadap arrival mid-price.
   - Menghitung markout empiris pasca-eksekusi pada horizon 1m, 5m, dan 15m untuk mengukur adverse selection secara aktual.
3. **Durasi Pengamatan Wajib:**
   - Minimal 30 hari kalender continuous shadow execution tanpa interupsi.
   - Minimal 150 eksekusi per aset untuk membangun signifikansi statistik empiris.

---

### FASE 7: Gerbang Kesiapan Produksi (Live-Readiness Gates)

Sebelum modal live sekecil apa pun diotorisasi, seluruh gerbang tata kelola wajib ditandatangani secara tertulis oleh Project Owner dan Governance Supervisor:

| Gerbang | Nama Gerbang | Parameter Uji | Standar Kelulusan Wajib | Status Saat Ini |
| :---: | :--- | :--- | :--- | :---: |
| **GATE 01** | Simulator Realism Gate | Single-channel friction, explicit liquidity role, anti-double-counting | 100% lulus pada 12 unit test dan 638 suite test | **VERIFIED (PASS)** |
| **GATE 02** | Data Readiness Gate | Ketersediaan 10 aset, 3 tahun continuous, ketersediaan 1m/tick | 10 aset 5m verified; 1m/tick pending backfill | **PARTIAL** |
| **GATE 03** | Economic Alpha Gate | Net expectancy per trade setelah biaya Bybit VIP0 | $\ge +12.0\text{ bps}$, PF $\ge 1.25$, Folds $\ge 4/4$ | **FAILED (NO ALPHA)** |
| **GATE 04** | Statistical Rigor Gate | Koreksi pengujian berganda & MBB Bootstrap | Holm-Bonferroni $p < 0.01$, MBB 95% $\text{CI}_{\text{low}} > 0$ | **PENDING NEXT RESEARCH** |
| **GATE 05** | Shadow Execution Gate | Deviasi paper vs backtest selama 30 hari live stream | Deviasi return $<10\%$, adverse selection $\le 2.0\text{ bps}$ | **NOT STARTED** |
| **GATE 06** | Unsealing Holdout Gate | Evaluasi satu kali pada holdout $\ge 1793491200000$ | Dilakukan HANYA setelah Gate 01–05 lolos 100% | **STRICTLY SEALED** |

---

## 3. Matriks Prioritas & Alokasi Tindakan Kerja

| Prioritas | Fase Kerja | Tindakan Spesifik | Estimasi Waktu | Output Utama |
| :---: | :--- | :--- | :---: | :--- |
| **P0** | Karantina Tata Kelola | Tandatangani laporan audit final; bekukan Session 1.5; tag Git baseline. | Hari 1 | Signed Decision Package |
| **P1** | Pipeline Data Multi-TF | Bangun pipeline download 1m dan agregator multi-timeframe (15m, 1h, 4h). | Hari 2–5 | Resampled Dataset 15m/1h/4h |
| **P2** | Desain Hipotesis Momentum | Formulasi fitur breakout 15m/1h dengan alignment tren 4h pada 10 aset utama. | Hari 6–8 | Hypothesis Spec & Feature Code |
| **P3** | Backtest & Evaluasi Biaya | Uji hipotesis momentum pada simulator remediated dengan Bybit VIP0 ($15\text{ bps}$). | Hari 9–12 | OOF Evaluation Report |
| **P4** | Koreksi Statistik MBB | Jalankan MBB bootstrap 1.000 iterasi dan koreksi Holm-Bonferroni pada hasil P3. | Hari 13–14 | Statistical Robustness Dossier |
| **P5** | Paper Daemon Integration | Deploy kandidat terbaik (jika Gate 03-04 lolos) ke Paper Daemon live stream. | Hari 15+ | 30-Day Shadow Execution Log |

---

*Laporan Roadmap Selesai. Seluruh tindakan riset produksi berada dalam status STANDBY menunggu persetujuan tertulis Project Owner.*
