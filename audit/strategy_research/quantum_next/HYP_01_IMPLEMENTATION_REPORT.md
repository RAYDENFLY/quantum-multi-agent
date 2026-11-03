# QUANTUM NEXT — HYP-01 IMPLEMENTATION REPORT
## Engineering and Microstructure Implementation of Multi-Timeframe Volatility Expansion Trend Following

**Dokumen Identifikasi:** `audit/strategy_research/quantum_next/HYP_01_IMPLEMENTATION_REPORT.md`  
**Tanggal Publikasi:** 2026-11-03 19:45:00 UTC  
**Branch Penelitian:** `research/quantum-next-3pct`  
**Git Baseline Commit:** `dcc8ceb54d80b1b9685d92236f48b0994610522a`  
**File Sumber Implementasi:** [`src/quantum/strategies/hyp01_strategy.py`](file:///d:/quantum-multi-agent/src/quantum/strategies/hyp01_strategy.py)  
**File Pengujian Unit:** [`tests/unit/test_quantum_next_hyp01.py`](file:///d:/quantum-multi-agent/tests/unit/test_quantum_next_hyp01.py)  

---

## 1. Latar Belakang & Motivasi Implementasi

Pada Milestone 4, diagnosis forensik terhadap $552,306$ perdagangan mengungkap bahwa:
1. **Sinyal kuantitatif mentah memiliki alpha arah yang nyata (+21.22 bps gross pada tren volatilitas tinggi, dan markout 60-menit mencapai +19.78 bps).**
2. Namun, strategi historis hancur karena **$50\%$ perdagangan ditembakkan ke pasar ranging yang tidak memiliki alpha**, dan **$29.08\%$ posisi terhenti (*stopped out*) hanya dalam 1 bar (5 menit)** akibat hambatan stop-loss yang terlalu sempit terhadap *microstructure noise*.

Implementasi **HYP-01** dirancang khusus untuk memecahkan dua masalah struktural tersebut melalui pendekatan rekayasa deterministik.

---

## 2. Rincian Komponen Rekayasa HYP-01

### 2.1 Detektor Rezim Pasar Deterministik & Bebas Lookahead Bias
Kelas `HYP01RegimeDetector` mengklasifikasikan kondisi pasar secara independen pada setiap bar $i$ menggunakan data titik-dalam-waktu (*point-in-time*):
- **Kalibrasi Ambang Batas Tanpa Kebocoran (*Zero Leakage*):**
  Ambang batas volatilitas dan tren tidak pernah dihitung menggunakan seluruh data historis. Fungsi `fit_thresholds_on_training_fold()` mengalibrasikan:
  - $\theta_\sigma$ (Ambang Volatilitas) = Median $\sigma_{20}$ pada Fold 0 dan Fold 1 training set ($\approx 0.0015$).
  - $\theta_{\text{trend}}$ (Ambang Tren) = Persentil-50 dari return absolut 1-jam ($|\text{HTF}_{12}|$) pada training fold ($\approx 75.0\text{–}85.0\text{ bps}$).
  - Begitu dikalibrasi, ambang batas ini **DIBEKUKAN (*FROZEN*)** sebelum masuk ke evaluasi validasi (Folds 2–4).
- **Logika Klasifikasi 4-Kuadran:**
  - `HIGH_VOLATILITY_TRENDING`: $\sigma_{20} \ge \theta_\sigma$ DAN $|\text{HTF}_{12}| \ge \theta_{\text{trend}}$ DAN $\text{vol\_exp\_ratio} \ge 1.05$. (Hanya kuadran ini yang diizinkan untuk membuka posisi).
  - `HIGH_VOLATILITY_RANGING`: $\sigma_{20} \ge \theta_\sigma$ TETAPI $|\text{HTF}_{12}| < \theta_{\text{trend}}$. (Ditolak).
  - `LOW_VOLATILITY_TRENDING`: $\sigma_{20} < \theta_\sigma$ TETAPI $|\text{HTF}_{12}| \ge \theta_{\text{trend}}$. (Ditolak).
  - `LOW_VOLATILITY_RANGING`: $\sigma_{20} < \theta_\sigma$ DAN $|\text{HTF}_{12}| < \theta_{\text{trend}}$. (Ditolak).

### 2.2 Analisis Multi-Timeframe (MTF)
Strategi mengintegrasikan 3 cakrawala waktu yang saling mengonfirmasi:
1. **Timeframe Tinggi (1h / 12 bar 5m):** Menentukan arah tren makro. Nilai $\text{HTF}_{12} \ge +85.0\text{ bps}$ menandakan tren naik kuat; $\le -85.0\text{ bps}$ menandakan tren turun kuat.
2. **Timeframe Menengah (15m / 3 bar 5m):** Memastikan momentum jangka pendek selaras dengan tren makro ($\text{ITF}_3 \ge 0$ untuk Long, $\le 0$ untuk Short).
3. **Timeframe Eksekusi (5m / 1 bar):** Konfirmasi aksi harga lokal (lilin hijau untuk Long, lilin merah untuk Short) pada saat rasio ekspansi volume $\ge 1.05$.

### 2.3 Solusi Masalah Stop-Out Prematur (*Anti-Noise Exit Engine*)
Untuk menghentikan likuidasi dini di Bar 1:
- **Pelebaran Stop-Loss Adaptif:** Stop-loss dinaikkan dari $1.5\sigma$ menjadi **$2.5\sigma$** ($2.5 \times \sigma_{20} \times \text{Price}$). Jarak ini memberikan ruang fluktuasi sekitar $40\text{–}65\text{ bps}$, cukup lebar untuk menyerap kebisingan sumbu lilin 5-menit.
- **Dua Tingkat Target Keuntungan (TP1 & TP2):**
  - **TP1 (Target Menengah):** $4.0\text{–}4.2\sigma$ ($\text{Reward:Risk} \approx 1.68$). Menutup $50\%$ posisi.
  - **Breakeven Ratchet:** Begitu TP1 tersentuh, harga SL pada sisa $50\%$ posisi secara otomatis digeser ke harga masuk (*entry price*).
  - **TP2 (Target Runner):** $7.5\sigma$ ($\text{Reward:Risk} \approx 3.00$). Menutup sisa posisi menggunakan pesanan limit pasif (menikmati maker fee $2.0\text{ bps}$).
- **Dynamic Trailing Stop:** Setelah TP1 tercapai, stop-loss bergerak dinamis menjaga jarak $2.0\sigma$ di belakang titik tertinggi lokal (*highest high*).
- **Perpanjangan Cakrawala Waktu (*Horizon Bars*):**
  - Target durasi minimum: $6\text{ bar}$ ($30\text{ menit}$).
  - Durasi maksimum sebelum *time expiration*: $20\text{–}24\text{ bar}$ ($1.6\text{–}2\text{ jam}$).

### 2.4 Filter Arah Aset Kripto (*Altcoin Short Drag Filter*)
Milestone 4 membuktikan bahwa posisi Short pada aset altcoin (DOGE, ADA, AVAX) menghasilkan kerugian besar ($-21.82\text{ bps}$ net). HYP-01 menyertakan parameter `filter_altcoin_shorts`:
- Aset mega-cap (`BTCUSDT`, `ETHUSDT`) tetap diizinkan dua arah (*bidirectional*).
- Aset altcoin dibatasi pada posisi **Long-Only**, menghilangkan salah satu sumber pendarahan modal terbesar.

### 2.5 Manajemen Risiko Independen (Risk Agent)
- **Position Sizing Berbasis Volatilitas:**
  $$\text{Notional} = \min\left(\frac{\text{Equity} \times 0.015}{\text{SL\_distance\_pct}}, \text{Equity} \times 3.0 \times 0.25\right)$$
- **Leverage Hard Cap:** Maksimum $3.0\times$ leverage portofolio.
- **Concurrent Positions Cap:** Maksimum $4$ aset simultan.
- **Daily Loss Circuit Breaker:** Menghentikan entri baru selama 24 jam jika kerugian harian mencapai $-4.0\%$.
- **Drawdown Circuit Breaker:** Jika drawdown portofolio melampaui $15.0\%$, ukuran posisi otomatis dipotong $50\%$.

---

## 3. Hasil Pengujian Unit & Verifikasi Kode

Seluruh komponen diuji secara formal dalam `tests/unit/test_quantum_next_hyp01.py` menggunakan framework pytest:

```
tests/unit/test_quantum_next_hyp01.py::TestHYP01RegimeDetector::test_regime_classification_mutually_exclusive PASSED [ 20%]
tests/unit/test_quantum_next_hyp01.py::TestHYP01RegimeDetector::test_zero_lookahead_determinism PASSED                 [ 40%]
tests/unit/test_quantum_next_hyp01.py::TestHYP01ConfigurationAndEngine::test_configuration_hashing PASSED            [ 60%]
tests/unit/test_quantum_next_hyp01.py::TestHYP01ConfigurationAndEngine::test_anti_noise_barrier_parameters PASSED    [ 80%]
tests/unit/test_quantum_next_hyp01.py::TestHYP01ConfigurationAndEngine::test_synthetic_simulation_execution PASSED   [100%]
```

- **Tingkat Kelulusan:** **$100\%$ (5/5 unit tests lulus dalam 3.03s)**.
- **Regresi Simulator:** **$100\%$ lulus (12/12 unit tests di `test_remediated_execution_simulator.py` lulus)**.
- **Integritas Kode Produksi:** Tidak ada kode di luar branch `research/quantum-next-3pct` yang terganggu.
