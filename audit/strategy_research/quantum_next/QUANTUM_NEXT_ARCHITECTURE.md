# QUANTUM NEXT — SYSTEM ARCHITECTURE SPECIFICATION
## Collaborative Six-Agent Autonomous Trading Architecture for HYP-01

**Dokumen Identifikasi:** `audit/strategy_research/quantum_next/QUANTUM_NEXT_ARCHITECTURE.md`  
**Tanggal Publikasi:** 2026-11-03 19:40:00 UTC  
**Branch Penelitian:** `research/quantum-next-3pct`  
**Git Baseline Commit:** `dcc8ceb54d80b1b9685d92236f48b0994610522a`  
**Status Prospective Holdout:** **STRICTLY SEALED & UNBREACHED** ($\ge 1793491200000\text{ ms}$ / 2026-11-01 00:00:00 UTC)  
**Status Arsitektur:** **SIX-AGENT OPERATIONAL WORKFLOW PRESERVED**  

---

## 1. Executive Overview & Arsitektur Enam Agen

Sistem QUANTUM Next dirancang untuk merealisasikan hipotesis penelitian **HYP-01 (Multi-Timeframe Volatility Expansion Trend Following)** dengan mempertahankan secara utuh arsitektur kolaboratif enam agen independen:
1. **Scout Agent:** Pemindaian pasar, deteksi volatilitas, eliminasi jebakan sumbu lilin (*wick traps*).
2. **Analyst Agent:** Klasifikasi rezim pasar titik-dalam-waktu (*point-in-time*), penentuan arah tren 1-jam, dan konfirmasi momentum 15-menit.
3. **Sniper Agent:** Pemicu eksekusi 5-menit, penentuan batas harga dinamis (*dynamic barrier pricing*: SL $2.5\sigma$, TP1 $4.0\sigma$, TP2 $7.5\sigma$).
4. **Risk Agent:** Kewenangan independen pemotongan risiko, ukuran posisi berbasis volatilitas, pembatasan *leverage* hard cap $3.0\times$, batas $4$ posisi simultan, serta *circuit breaker* harian dan *drawdown*.
5. **Banker Agent:** Manajemen siklus hidup posisi, akuntansi biaya realistis (Maker/Taker, spread, slippage, funding, adverse selection), mekanisme *breakeven ratchet* dan *trailing stop*.
6. **Orchestrator Agent:** Penjadwalan pipeline asinkronus dan orkestrasi portofolio multi-aset.

```
+----------------------------------------------------------------------------------------------------+
|                                    QUANTUM NEXT PIPELINE WORKFLOW                                  |
+----------------------------------------------------------------------------------------------------+
|                                                                                                    |
|  [Market Data 5m/15m/1h]                                                                          |
|            |                                                                                       |
|            v                                                                                       |
|  +--------------------+     Rejection (Ranging / Noise)                                            |
|  |    SCOUT AGENT     | -------------------------------------> [CANDIDATE DISCARDED]               |
|  |  (Vol & Wick Trap) |                                                                            |
|  +--------------------+                                                                            |
|            | Valid Expansion                                                                       |
|            v                                                                                       |
|  +--------------------+     Rejection (Trend < 75 bps / Regime Mismatch)                           |
|  |   ANALYST AGENT    | -------------------------------------> [NO ALIGNMENT - SKIP]               |
|  | (1h Trend+15m Mom) |                                                                            |
|  +--------------------+                                                                            |
|            | Confirmed Regime (HIGH_VOLATILITY_TRENDING)                                           |
|            v                                                                                       |
|  +--------------------+                                                                            |
|  |    SNIPER AGENT    | ---> Calculate SL = 2.5*sigma, TP1 = 4.0*sigma, TP2 = 7.5*sigma             |
|  | (5m Timing Trigger)|                                                                            |
|  +--------------------+                                                                            |
|            | Proposed Order                                                                        |
|            v                                                                                       |
|  +--------------------+     Rejection (Daily Loss >= 4%, DD >= 15%, Active Pos >= 4)               |
|  |     RISK AGENT     | -------------------------------------> [ORDER VETOED / REDUCED]            |
|  | (Sizing & Limits)  |                                                                            |
|  +--------------------+                                                                            |
|            | Approved (Sized Notional <= 3x Leverage)                                              |
|            v                                                                                       |
|  +--------------------+                                                                            |
|  |    BANKER AGENT    | ---> Taker Market Entry -> Monitor TP1 Hit -> Ratchet SL to Breakeven      |
|  | (Lifecycle & Costs)| ---> Dynamic Trailing Stop -> Maker TP2 Exit / Market Expiration Exit      |
|  +--------------------+                                                                            |
|            |                                                                                       |
|            v                                                                                       |
|  +--------------------+                                                                            |
|  | ORCHESTRATOR AGENT | ---> Update Portfolio Equity, Settle Daily Return Distribution             |
|  +--------------------+                                                                            |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Spesifikasi Integrasi Agen

### 2.1 Scout Agent (Scanner & Volatility Filter)
- **Fungsi:** Menginspeksi seluruh 10 aset primer (`BTCUSDT`, `ETHUSDT`, `SOLUSDT`, `BNBUSDT`, `ADAUSDT`, `XRPUSDT`, `DOGEUSDT`, `AVAXUSDT`, `LINKUSDT`, `LTCUSDT`).
- **Filter Ambang Batas:**
  - `sigma_20 >= sigma_threshold` (Median training fold $\approx 0.0015$).
  - `vol_exp_ratio >= 1.05` (Memastikan pasar sedang mengalami ekspansi volume dan volatilitas).
  - Mengeliminasi kandidat yang memiliki sumbu lilin atas/bawah ekstrim (*wick trap ratio* $> 0.80$).

### 2.2 Analyst Agent (Regime & Multi-Timeframe Alignment)
- **Fungsi:** Menghilangkan penyebab kegagalan fatal pada Milestone 4 (di mana 50% trade ditembakkan ke kondisi *ranging*).
- **Logika Deterministik:**
  $$\text{Regime} = \begin{cases} 
  \text{HIGH\_VOLATILITY\_TRENDING}, & \text{jika } \sigma_{20} \ge \theta_\sigma \text{ dan } |\text{HTF}_{12}| \ge \theta_{\text{trend}} \text{ dan } \text{vol\_exp} \ge 1.05 \\
  \text{RANGING / LOW\_VOL}, & \text{lainnya (Ditolak dari entri)}
  \end{cases}$$
- **Arah Tren & Konfirmasi:**
  - *Long Alignment:* $\text{HTF}_{12} \ge +85.0\text{ bps}$ dan $\text{ITF}_3 \ge 0\text{ bps}$.
  - *Short Alignment:* $\text{HTF}_{12} \le -85.0\text{ bps}$ dan $\text{ITF}_3 \le 0\text{ bps}$ (dengan opsi filter short pada altcoin).

### 2.3 Sniper Agent (Execution Timing & Anti-Noise Barrier Pricing)
- **Fungsi:** Menyelesaikan masalah *premature 1-bar stop-out* (penyebab $29\%$ kegagalan trade di Milestone 4).
- **Formulasi Barrier:**
  $$\text{Initial SL} = \text{Arrival Price} \pm (2.5 \times \sigma_{20} \times \text{Arrival Price})$$
  $$\text{TP1 (50\% close)} = \text{Arrival Price} \mp (4.2 \times \sigma_{20} \times \text{Arrival Price}) \quad (\text{Reward:Risk} \approx 1.68)$$
  $$\text{TP2 (50\% close)} = \text{Arrival Price} \mp (7.5 \times \sigma_{20} \times \text{Arrival Price}) \quad (\text{Reward:Risk} \approx 3.00)$$

### 2.4 Risk Agent (Independent Sizing & Circuit Breakers)
- **Kewenangan Independen:** Risk Agent memiliki hak veto absolut.
- **Ukuran Posisi (*Volatility Sizing*):**
  $$\text{Desired Notional} = \frac{\text{Equity} \times \text{RiskPerTradePct}}{\text{SL\_distance\_pct}}, \quad \text{Notional} = \min(\text{Desired Notional}, \text{Equity} \times \text{MaxLeverage} \times \text{ExposureLimit})$$
- **Batasan Portofolio:**
  - *Hard Leverage Cap:* $\le 3.0\times$ (Maksimum leverage posisi).
  - *Max Concurrent Positions:* $\le 4$ aset bersamaan di seluruh universe.
  - *Symbol Exposure Cap:* $\le 25\%$ dari modal portofolio per simbol.
  - *Daily Loss Circuit Breaker:* Jika akumulasi kerugian harian mencapai $-4.0\%$, hentikan seluruh entri baru selama 24 jam.
  - *Drawdown Circuit Breaker:* Jika drawdown portofolio mencapai $\ge 15.0\%$, kurangi leverage dan ukuran posisi sebesar $50\%$.

### 2.5 Banker Agent (Execution Accounting & Lifecycle Tracking)
- **Akuntansi Biaya Non-Konflasi:**
  - Entri Market: Dikenakan Taker Fee ($5.5\text{ bps}$) + Spread ($2.0\text{ bps}$) + Slippage ($2.0\text{ bps}$) = $9.5\text{ bps}$ per leg di Bybit VIP0.
  - Exit Limit TP2: Dikenakan Maker Fee ($2.0\text{ bps}$), Spread $0.0\text{ bps}$, Slippage $0.0\text{ bps}$.
  - Exit Stop-Loss Darurat: Dikenakan Taker Fee ($5.5\text{ bps}$) + Slippage ($2.0\text{ bps}$).
  - Funding Rate: Settlement periodik 8-jam ($0.01\%$ per 8 jam).
- **Mekanisme Breakeven Ratchet:**
  - Begitu harga menyentuh TP1, Banker Agent secara instan meratchet harga SL ke harga masuk (*entry price*), mengeliminasi risiko kerugian modal pada sisa posisi.
- **Dynamic Trailing Stop:**
  - Setelah TP1 tercapai, trailing stop aktif menjaga jarak $2.0 \times \sigma_{20}$ di belakang harga tertinggi (*highest high*) untuk posisi Long.

---

## 3. Titik Integrasi Teknis pada Codebase

Sistem QUANTUM Next diimplementasikan secara modular pada branch `research/quantum-next-3pct`:
1. **Core Strategy & Engine:** [`src/quantum/strategies/hyp01_strategy.py`](file:///d:/quantum-multi-agent/src/quantum/strategies/hyp01_strategy.py)
   - `HYP01Configuration`: Skema Pydantic deklaratif.
   - `HYP01RegimeDetector`: Klasifikator rezim deterministik.
   - `HYP01Engine`: Simulator eksekusi portofolio multi-aset.
2. **Agent Contract Bridge:** [`src/quantum/strategies/agent_bridge.py`](file:///d:/quantum-multi-agent/src/quantum/strategies/agent_bridge.py)
   - Menghubungkan konfigurasi HYP-01 ke `ScoutAgent`, `AnalystAgent`, `SniperAgent`, `RiskAgent`, dan `BankerAgent`.
3. **Unit & Integration Tests:** [`tests/unit/test_quantum_next_hyp01.py`](file:///d:/quantum-multi-agent/tests/unit/test_quantum_next_hyp01.py)
   - $100\%$ lulus verifikasi deterministik dan akuntansi biaya.
4. **Controlled Experiment Suite:** [`scripts/run_hyp01_experiments.py`](file:///d:/quantum-multi-agent/scripts/run_hyp01_experiments.py)
   - Mengevaluasi 7 eksperimen terkontrol dan membukukan ledger serta manifes.
