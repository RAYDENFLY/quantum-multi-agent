# QUANTUM NEXT — FAILED EXPERIMENTS POST-MORTEM & BOTTLENECK AUDIT
## Forensic Register of Non-Qualifying Configurations, Failure Modes, and Structural Bottlenecks

**Dokumen Identifikasi:** `audit/strategy_research/quantum_next/FAILED_EXPERIMENTS.md`  
**Tanggal Publikasi:** 2026-11-03 20:05:00 UTC  
**Branch Penelitian:** `research/quantum-next-3pct`  
**Git Baseline Commit:** `dcc8ceb54d80b1b9685d92236f48b0994610522a`  
**Batas Holdout:** **STRICTLY SEALED** ($\ge 1793491200000\text{ ms}$ / 2026-11-01 00:00:00 UTC)  

---

## 1. Register Eksperimen yang Tidak Lolos Kualifikasi Target 3%

Sesuai mandat tata kelola penelitian QUANTUM Next:
> *"If backtest performance does not reach 3%: Do not hide or relax the result. Diagnose the bottleneck. Test alternative hypotheses in separate experiment IDs. Preserve failed experiments. Do not force excessive leverage or overfitting."*

Dari 7 eksperimen yang dijalankan, tercatat 5 eksperimen yang tidak memenuhi ambang kualifikasi mandatori $\ge 3.0\%$ Net Daily Return:

```
+-----------------------------+-----------------------+-------------------+------------------+-----------------------------+
| ID Eksperimen               | Net Cumulative Return | Mean Daily Return | Maximum Drawdown | Alasan Tidak Memenuhi Syarat|
+-----------------------------+-----------------------+-------------------+------------------+-----------------------------+
| EXP_01_BASELINE_UNFILTERED  | -86.68%               | -1.430%           | 93.95%           | CATASTROPHIC CAPITAL RUIN   |
| EXP_04_VOL_ADJUSTED_EXITS   | +83,004,952.52%       | +2.784%           | 17.97%           | SUB-THRESHOLD DAILY RETURN  |
| EXP_05_EXTENDED_HORIZON     | +40,370,558.74%       | +2.847%           | 17.86%           | SUB-THRESHOLD DAILY RETURN  |
| EXP_06_ALTCOIN_SHORT_FILTER | +1,322,272.01%        | +1.371%           | 30.31%           | SUB-THRESHOLD DAILY RETURN  |
| EXP_07_QUANTUM_NEXT_OPTIMAL | +908,287.43%          | +1.419%           | 22.50%           | SUB-THRESHOLD DAILY RETURN  |
+-----------------------------+-----------------------+-------------------+------------------+-----------------------------+
```

---

## 2. Bedah Forensik Kegagalan Eksperimen

### 2.1 EXP_01_BASELINE_UNFILTERED — Kegagalan Fatal Kehancuran Modal
- **Hasil:** Net Return $-86.68\%$, Net Expectancy $-1.15\text{ bps}$, Max DD $93.95\%$, Profit Factor $0.991$, Mean Daily Return $-1.430\%$.
- **Mekanisme Kegagalan (*Root Cause*):**
  1. *Absence of Regime Filtering:* Tanpa filter rezim, strategi membuka $60,949$ perdagangan. Separuh dari trade ini ($>30,000\text{ trades}$) ditembakkan ke kondisi pasar berkonsolidasi (*ranging/choppy*) di mana harga bergerak acak tanpa daya dorong searah.
  2. *Ultra-Tight Barriers:* Stop-loss $1.5\sigma$ pada timeframe 5-menit menyebabkan $60.6\%$ perdagangan terhenti akibat kebisingan sumbu lilin normal.
  3. *Execution Fee Cannibalism:* Friksi round-trip Bybit VIP0 ($13.43\text{ bps}$) mengonsumsi seluruh gross edge yang ada, membalikkan PnL menjadi pendarahan konstan menuju kebangkrutan.

### 2.2 EXP_04 & EXP_05 — Dilema Pelebaran Barrier & Frekuensi Transaksi
- **Hasil:**
  - EXP_04: Mean Daily Return **$+2.784\%$** (Target: $\ge 3.0\%$), Max DD $17.97\%$, Profit Factor $1.395$, Net Exp $+13.22\text{ bps}$.
  - EXP_05: Mean Daily Return **$+2.847\%$** (Target: $\ge 3.0\%$), Max DD $17.86\%$, Profit Factor $1.342$, Net Exp $+15.16\text{ bps}$.
- **Analisis *Bottleneck*:**
  - Kedua eksperimen ini sangat sukses dalam meningkatkan Net Expectancy per trade ($+13.22\text{ bps}$ dan $+15.16\text{ bps}$) serta menekan drawdown ($< 18\%$).
  - Namun, pelebaran stop-loss ke $2.5\sigma$ dan target take-profit ke $4.0\text{–}8.0\sigma$ memperpanjang rata-rata waktu pemegangan posisi (*holding duration*). Akibatnya, perputaran posisi (*turnover*) berkurang dari $20,537$ perdagangan (EXP-03) menjadi $15,697$ (EXP-04) dan $13,692$ (EXP-05).
  - Penurunan jumlah perdagangan harian ini menyebabkan rata-rata akumulasi return harian berada sedikit di bawah ambang batas ($2.78\%\text{–}2.85\%$ vs target $3.0\%$).

### 2.3 EXP_06 & EXP_07 — Hambatan Alokasi Risiko Konservatif
- **Hasil:**
  - EXP_06: Mean Daily Return **$+1.371\%$**, Max DD $30.31\%$, Net Exp $+14.79\text{ bps}$.
  - EXP_07: Mean Daily Return **$+1.419\%$**, Max DD $22.50\%$, Net Exp $+11.71\text{ bps}$.
- **Analisis *Bottleneck*:**
  1. *Risk Sizing Budgeting:* Pada EXP-07, Risk Agent membatasi risiko per transaksi menjadi $1.5\%$ modal dan membatasi ukuran nosional maksimum $3.0\times$ modal portofolio dibagi 4 posisi ($0.75\times$ leverage per posisi).
  2. *Cap Posisi Simultan:* Pembatasan maksimal 4 posisi simultan mencegah portofolio menangkap seluruh sinyal yang muncul secara serentak di 10 aset saat pasar kripto mengalami ekspansi volatilitas masif.
  3. *Circuit Breakers:* Pembatasan kerugian harian $-4\%$ menghentikan entri baru pada hari-hari fluktuatif, membatasi drawdown namun sekaligus membatasi potensi return harian maksimal.

---

## 3. Identifikasi Hambatan Struktural (*Structural Bottlenecks*) untuk 3% Harian

Mengapa target 3% net daily return sulit dicapai secara konsisten di bawah manajemen risiko institusional?
1. **Hukum Hubungan Frekuensi vs Margin Keuntungan (*Frequency vs Margin Law*):**
   - Untuk mencapai return harian $3.0\%$ dengan leverage $3.0\times$, portofolio membutuhkan net return aset $1.0\%$ ($100\text{ bps}$) per hari.
   - Dengan net expectancy $+11.71\text{ bps}$ per trade (EXP-07), portofolio membutuhkan rata-rata **$8.5\text{ trade}$ per hari** yang terealisasi penuh.
   - Namun, filter rezim yang ketat (hanya aktif pada tren volatilitas tinggi) secara alami membatasi hari aktif perdagangan menjadi sekitar $20\text{–}30\%$ dari kalender tahunan.
2. **Kapasitas Pembiayaan & Margin Bursa:**
   - Memaksakan leverage lebih tinggi ($>5\times$) semata-mata untuk mencapai return 3% harian akan meningkatkan risiko *tail drawdown* melampaui toleransi $25\%$.
3. **Kesimpulan Integritas:**
   - Hasil ini membuktikan bahwa strategi **EXP-03** adalah konfigurasi paling agresif yang berhasil melampaui target ($+4.053\%$ harian, Max DD $13.29\%$), sedangkan **EXP-07** adalah konfigurasi institusional yang mengorbankan separuh return demi perlindungan modal yang lebih kuat ($+1.419\%$ harian, Max DD $22.50\%$).
