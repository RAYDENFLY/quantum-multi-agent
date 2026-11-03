# QUANTUM NEXT — EXECUTION & RISK SPECIFICATION
## Comprehensive Specification for Risk Authority and Banker Execution Accounting

**Dokumen Identifikasi:** `audit/strategy_research/quantum_next/EXECUTION_AND_RISK_SPECIFICATION.md`  
**Tanggal Publikasi:** 2026-11-03 19:55:00 UTC  
**Branch Penelitian:** `research/quantum-next-3pct`  
**Git Baseline Commit:** `dcc8ceb54d80b1b9685d92236f48b0994610522a`  
**Modul Sumber:** [`src/quantum/strategies/hyp01_strategy.py`](file:///d:/quantum-multi-agent/src/quantum/strategies/hyp01_strategy.py)  

---

## 1. Otoritas Independen Risk Agent

Dalam arsitektur QUANTUM Next, **Risk Agent memegang kewenangan independen (*independent authority*) dengan hak veto mutlak**. Tidak ada sinyal dari Scout, Analyst, maupun Sniper yang dapat dieksekusi tanpa persetujuan eksplisit dari parameter kontrol risiko.

### 1.1 Formulasi Ukuran Posisi Berbasis Volatilitas (*Volatility Sizing*)
Ukuran nosional (*notional size*) dihitung secara dinamis berdasarkan jarak stop-loss aktual untuk memastikan bahwa kerugian dolar (*dollar risk*) per transaksi selalu terukur dan stabil:
$$\text{Dollar Risk Budget} = \text{Portfolio Equity} \times \text{RiskPerTradePct} \quad (\text{Default: } 1.5\%)$$
$$\text{SL Distance Pct} = \frac{|\text{Arrival Price} - \text{SL Price}|}{\text{Arrival Price}} = 2.5 \times \sigma_{20}$$
$$\text{Desired Notional} = \frac{\text{Dollar Risk Budget}}{\max(\text{SL Distance Pct}, 0.005)}$$

### 1.2 Batasan Leverage dan Alokasi Modal
Untuk mencegah pembengkakan leverage yang berlebihan:
$$\text{Max Allowed Notional} = \text{Portfolio Equity} \times \text{MaxLeverage} \times \text{MaxSymbolExposurePct} \times \text{LeverageMultiplier}$$
- **Hard Leverage Cap:** $\text{MaxLeverage} = 3.0\times$ (Maksimum leverage total portofolio).
- **Symbol Exposure Cap:** $\text{MaxSymbolExposurePct} = 0.25$ (Maksimum $25\%$ modal per simbol aset).
- **Concurrent Positions Cap:** Maksimum **$4$ posisi aktif simultan** di seluruh alam semesta 10 aset.
$$\text{Actual Executed Notional} = \min(\text{Desired Notional}, \text{Max Allowed Notional})$$

### 1.3 Mekanisme Pemutus Sirkuit (*Circuit Breakers*)
1. **Daily Loss Circuit Breaker ($4.0\%$):**
   - Melacak akumulasi kerugian terealisasi dalam siklus 24 jam (`current_day = timestamp // 86400000`).
   - Jika $|\text{Daily Loss Accum}| / \text{Equity} \ge 0.04$, Risk Agent **memblokir seluruh pembukaan posisi baru** untuk sisa hari tersebut.
2. **Drawdown Circuit Breaker ($15.0\%$):**
   - Melacak penurunan ekuitas dari titik tertinggi (*peak equity*):
     $$\text{Drawdown} = \frac{\text{Peak Equity} - \text{Current Equity}}{\text{Peak Equity}}$$
   - Jika $\text{Drawdown} \ge 15.0\%$, parameter `LeverageMultiplier` otomatis diturunkan menjadi **$0.5$** (memotong ukuran posisi sebesar $50\%$).
3. **Perlindungan Kebangkrutan (*Ruin Protection*):**
   - Jika modal portofolio turun di bawah batas kritis $\$5.00\text{ USD}$, seluruh aktivitas perdagangan dihentikan permanen.

---

## 2. Spesifikasi Eksekusi Banker Agent

Banker Agent bertanggung jawab atas siklus hidup pesanan, simulasi pengisian buku pesanan (*order filling*), dan akuntansi friksi non-konflasi.

### 2.1 Jadwal Biaya Eksekusi Terverifikasi (`BYBIT_VIP0_DEFAULT`)
Sesuai dengan standar resmi Bybit VIP0 per 2026:
- **Taker Fee:** $5.5\text{ bps}$ per kaki ($0.055\%$).
- **Maker Fee:** $2.0\text{ bps}$ per kaki ($0.020\%$).
- **Default Bid-Ask Spread:** $2.0\text{ bps}$ per leg (dibayar oleh market orders).
- **Default Slippage:** $2.0\text{ bps}$ per leg (dibayar saat crossing book atau stop-loss taker exit).
- **Funding Settlement:** $0.01\%$ per 8 jam (dihitung proporsional terhadap durasi jam pemegangan posisi).

### 2.2 Klasifikasi Peran Likuiditas Non-Konflasi (*Actual Liquidity Role*)
Simulator membedakan secara ketat peran likuiditas untuk setiap kaki eksekusi:

| Kaki Eksekusi | Jenis Pesanan | Peran Likuiditas | Biaya Komisi | Biaya Spread | Biaya Slippage | Total Friksi Leg |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Entri Posisi** | MARKET | **TAKER** | $5.5\text{ bps}$ | $2.0\text{ bps}$ | $2.0\text{ bps}$ | **$9.5\text{ bps}$** |
| **Exit TP1 (50%)** | LIMIT (Resting) | **MAKER** | $2.0\text{ bps}$ | $0.0\text{ bps}$ | $0.0\text{ bps}$ | **$2.0\text{ bps}$** |
| **Exit TP2 (Runner)**| LIMIT (Resting) | **MAKER** | $2.0\text{ bps}$ | $0.0\text{ bps}$ | $0.0\text{ bps}$ | **$2.0\text{ bps}$** |
| **Exit Stop-Loss** | STOP MARKET | **TAKER** | $5.5\text{ bps}$ | $2.0\text{ bps}$ | $2.0\text{ bps}$ | **$9.5\text{ bps}$** |
| **Exit Breakeven** | STOP MARKET | **TAKER** | $5.5\text{ bps}$ | $2.0\text{ bps}$ | $2.0\text{ bps}$ | **$9.5\text{ bps}$** |
| **Exit Waktu (Max 2h)**| MARKET | **TAKER** | $5.5\text{ bps}$ | $2.0\text{ bps}$ | $2.0\text{ bps}$ | **$9.5\text{ bps}$** |

### 2.3 Formulasi Akuntansi Friksi Finansial Tunggal (*Single-Channel Friction Accounting*)
Untuk memastikan **zero double counting** antara PnL kotor dan biaya transaksi:
$$\text{Gross PnL} = \text{Notional} \times \left( \text{Side} \times \frac{\text{Exit Price} - \text{Entry Price}}{\text{Entry Price}} \right)$$
$$\text{Total Fee USD} = \text{Notional} \times (\text{FeeRate}_{\text{entry}} + \text{FeeRate}_{\text{exit}})$$
$$\text{Spread Cost USD} = \text{Notional} \times \text{SpreadRate}_{\text{entry}}$$
$$\text{Slippage Cost USD} = \text{Notional} \times \text{SlippageRate}$$
$$\text{Funding Cost USD} = \text{Notional} \times 0.0001 \times \left( \frac{\text{Bars Held}}{96} \right)$$
$$\text{Total Execution Cost} = \text{Fee USD} + \text{Spread USD} + \text{Slippage USD} + \text{Funding USD}$$
$$\mathbf{Net Realized PnL} = \mathbf{Gross PnL} - \mathbf{Total Execution Cost}$$

### 2.4 Mekanisme Siklus Hidup Banker (*Position Lifecycle State Machine*)
1. **Status OPEN:** Pesanan pasar terisi sebagai TAKER pada harga pembukaan lilin bar $i$.
2. **Status TP1_HIT:** Harga mencapai level TP1 ($4.2\sigma$). Banker Agent:
   - Menutup $50\%$ posisi pada TP1 (mengunci profit).
   - **MENGGESER HARGA STOP-LOSS SECARA INSTAN KE HARGA MASUK (*Breakeven Ratchet*)**. Posisi kini berstatus bebas risiko kerugian (*risk-free*).
3. **Status TRAILING_STOP:** Jika harga terus bergerak menguntungkan, Banker Agent memperbarui level proteksi trailing setiap bar:
   $$\text{SL Price} = \max(\text{SL Price}, \text{Close} - (2.0 \times \sigma_{20} \times \text{Close})) \quad (\text{untuk Long})$$
4. **Status TP2_HIT / TIME_EXIT / SL_HIT:** Sisa posisi ditutup secara penuh, mengkalkulasi PnL bersih riil dan memperbarui ekuitas portofolio.
