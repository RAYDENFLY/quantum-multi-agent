# QUANTUM NEXT — CONTROLLED EXPERIMENT DESIGN SPECIFICATION
## Methodological Framework, Controlled Variables, and Hypothesis Testing Matrix

**Dokumen Identifikasi:** `audit/strategy_research/quantum_next/EXPERIMENT_DESIGN.md`  
**Tanggal Publikasi:** 2026-11-03 19:50:00 UTC  
**Branch Penelitian:** `research/quantum-next-3pct`  
**Git Baseline Commit:** `dcc8ceb54d80b1b9685d92236f48b0994610522a`  
**Batas Holdout:** **STRICTLY SEALED** ($\ge 1793491200000\text{ ms}$ / 2026-11-01 00:00:00 UTC)  
**Skrip Eksekusi:** [`scripts/run_hyp01_experiments.py`](file:///d:/quantum-multi-agent/scripts/run_hyp01_experiments.py)  

---

## 1. Desain Metodologis & Prinsip Pengujian

Eksperimen QUANTUM Next dirancang dengan prinsip pengujian ilmiah ketat:
1. **Perubahan Satu Variabel Utama (*One Major Variable at a Time*):** Setiap eksperimen secara berurutan mengisolasi dampak dari komponen strategi baru untuk menentukan sumber kontribusi performa sesungguhnya.
2. **Keterisolasian Holdout Prospektif (*Prospective Holdout Isolation*):** Seluruh pengujian dibatasi secara mutlak pada stempel waktu $< 1793491200000\text{ ms}$ (sebelum 1 November 2026 00:00:00 UTC). Tidak ada kebocoran data (*data leakage*) ke periode holdout.
3. **Pembekuan Parameter Pelatihan (*Training Parameter Freezing*):** Ambang batas rezim volatilitas dan tren dikalibrasi hanya pada Fold 0 dan Fold 1, lalu dibekukan (*frozen*) sebelum diterapkan ke Fold 2, 3, dan 4.
4. **Reproduksibilitas Deterministik:** Setiap eksperimen memiliki `config_hash` SHA-256 unik yang dapat diverifikasi ulang kapan saja.

---

## 2. Matriks Eksperimen Terkontrol (EXP-01 s/d EXP-07)

```
+-----------------------------+-------------------------------------------------------------+-----------------------------------+
| ID Eksperimen               | Variabel Independen yang Diuji                              | Hash Konfigurasi (SHA-256)        |
+-----------------------------+-------------------------------------------------------------+-----------------------------------+
| EXP_01_BASELINE_UNFILTERED  | Baseline historis (Tanpa filter rezim, SL/TP ketat 5m)      | bb0c360f22148153                  |
| EXP_02_REGIME_FILTER_ONLY   | Filter rezim deterministik (Hanya High-Vol Trending)        | c8c238c04281f1b0                  |
| EXP_03_MTF_CONFIRMATION     | Konfirmasi Multi-Timeframe (1h Trend >= 100bps + 15m Mom)   | 5a31b4c885a9211c                  |
| EXP_04_VOL_ADJUSTED_EXITS   | Exit anti-noise (SL 2.5x, TP1 4.0x, Breakeven Ratchet)      | 230b72ea52b1b167                  |
| EXP_05_EXTENDED_HORIZON     | Perpanjangan horizon pemegangan (Maks 24 bar / 2 jam)       | 929826ae419550de                  |
| EXP_06_ALTCOIN_SHORT_FILTER | Filter short altcoin (Long-Only Altcoin, Bidirectional BTC)| e9187b083c45f31b                  |
| EXP_07_QUANTUM_NEXT_OPTIMAL | Konfigurasi terintegrasi dengan Risk Sizing & Breakers      | 0fbaf62d42f54593                  |
+-----------------------------+-------------------------------------------------------------+-----------------------------------+
```

### Rincian Parameter Spesifik Tiap Eksperimen:

#### EXP_01_BASELINE_UNFILTERED
- *Tujuan:* Mereplikasi perilaku armada historis 5-menit scalper pada portofolio multi-aset sebagai kontrol dasar (*control group*).
- *Parameter:* `enable_regime_filter = False`, `trend_threshold_bps = 0.0`, `sl_multiplier = 1.5`, `tp1_multiplier = 2.0`, `tp2_multiplier = 3.5`, `breakeven_ratchet = False`, `max_horizon_bars = 6`.

#### EXP_02_REGIME_FILTER_ONLY
- *Tujuan:* Menguji secara murni apakah mematikan perdagangan pada pasar *ranging* (mengaktifkan hanya `HIGH_VOLATILITY_TRENDING`) mampu membalikkan kerugian armada historis.
- *Parameter:* `enable_regime_filter = True`, `trend_threshold_bps = 75.0`, parameter lainnya identik dengan EXP-01.

#### EXP_03_MTF_CONFIRMATION
- *Tujuan:* Menguji dampak pengetatan konfirmasi tren 1-jam ($\ge 100\text{ bps}$) dan keselarasan momentum 15-menit.
- *Parameter:* `trend_threshold_bps = 100.0`, `vol_expansion_min = 1.10`, `tp1_multiplier = 2.5`, `tp2_multiplier = 4.0`.

#### EXP_04_VOL_ADJUSTED_EXITS
- *Tujuan:* Menguji efektivitas pelebaran stop-loss ($2.5\sigma$) dan *breakeven ratchet* dalam menyelesaikan masalah *1-bar premature stop-out*.
- *Parameter:* `sl_multiplier = 2.5`, `tp1_multiplier = 4.0`, `tp2_multiplier = 7.5`, `enable_breakeven_ratchet = True`, `trailing_stop_sigma = 2.0`, `max_horizon_bars = 12`.

#### EXP_05_EXTENDED_HORIZON
- *Tujuan:* Menguji eksploitasi penuh dari kurva markout 60-menit ($+19.78\text{ bps}$) dengan memperpanjang durasi pemegangan maksimum hingga 24 bar (2 jam).
- *Parameter:* `tp1_multiplier = 4.5`, `tp2_multiplier = 8.0`, `min_horizon_bars = 6`, `max_horizon_bars = 24`.

#### EXP_06_ALTCOIN_SHORT_FILTER
- *Tujuan:* Menguji eliminasi *drag* posisi short pada aset altcoin yang terbukti merugi $-21.82\text{ bps}$ di Milestone 4.
- *Parameter:* `filter_altcoin_shorts = True` (Posisi short hanya diizinkan pada `BTCUSDT` dan `ETHUSDT`).

#### EXP_07_QUANTUM_NEXT_OPTIMAL
- *Tujuan:* Menguji sistem produksi final dengan seluruh kontrol risiko terintegrasi: *volatility sizing*, batasan leverage $3\times$, batas $4$ posisi simultan, *daily loss circuit breaker* ($4\%$), dan *drawdown circuit breaker* ($15\%$).

---

## 3. Variabel Terkendali (*Controlled Baseline Variables*)

Sepanjang seluruh 7 eksperimen, variabel-variabel berikut dijaga konstan:
- **Universe Aset:** 10 aset primer (`BTCUSDT`, `ETHUSDT`, `SOLUSDT`, `BNBUSDT`, `ADAUSDT`, `XRPUSDT`, `DOGEUSDT`, `AVAXUSDT`, `LINKUSDT`, `LTCUSDT`).
- **Jadwal Biaya Eksekusi:** `BYBIT_VIP0_DEFAULT` (Taker fee $5.5\text{ bps}$/leg, Maker fee $2.0\text{ bps}$/leg, Spread $2.0\text{ bps}$, Slippage $2.0\text{ bps}$, Funding $0.01\%$/8h).
- **Modal Awal Portofolio:** $\$100.00\text{ USD}$.
- **Data Partisi Walk-Forward:**
  - Fold 0: Full baseline history ($211,955\text{ bars}$).
  - Fold 1: Walk-forward block 1 ($26,136\text{ bars}$).
  - Fold 2: Walk-forward block 2 ($26,136\text{ bars}$).
  - Fold 3: Walk-forward block 3 ($26,136\text{ bars}$).
  - Fold 4: Walk-forward block 4 ($26,136\text{ bars}$).
- **Batas Waktu Holdout:** `1793491200000 ms` (2026-11-01 00:00:00 UTC).

---

## 4. Metrik Dependen Evaluasi Mandatori

1. **Metrik Finansial:** Net PnL, Net Cumulative Return (%), Gross Expectancy (bps), Net Expectancy (bps), Profit Factor.
2. **Metrik Distribusi Return Harian:** Mean Daily Return (%), Median Daily Return (%), Persentase Hari $\ge 3.0\%$, Persentase Hari Negatif, Worst Daily Loss (%).
3. **Metrik Manajemen Risiko:** Maximum Drawdown (%), Annualized Sharpe Ratio, Annualized Sortino Ratio, Calmar Ratio.
4. **Metrik Eksekusi:** Total Executed Trades, Win Rate (%), Total Fees Paid, Slippage/Spread Drag.
5. **Kriteria Kualifikasi 3% Harian:**
   $$\text{Qualified} = (\text{Mean Daily Return} \ge 3.0\%) \land (\text{Max Drawdown} \le 25.0\%) \land (\text{Net Cumulative Return} > 0)$$
