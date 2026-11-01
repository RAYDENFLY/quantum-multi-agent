# QUANTUM PHASE 5.5.0.5: DEC_02 DIRECTIONAL EVIDENCE AUDIT

**Document Status:** `APPROVED_FOR_REVIEW`  
**Publication Timestamp:** `2026-11-01 21:02:03 UTC`  
**Associated Deliverable:** Workstream C (DEC_02 Directional Asymmetry Audit)  

---

## 1. FORENSIC AUDIT OF DIRECTIONAL CLAIMS

Phase 5.5.0.4 asserted several claims regarding directional asymmetries. This audit verifies the exact empirical evidence supporting each claim in the repository:

### Claim 1: 'Secular Bull Market Bias from October 2023 to October 2026'
- **Classification:** `DATA_SUPPORTED` for BTC; `PARTIALLY_SUPPORTED` for Fleet Altcoins.
- **Evidence Trace:** Inspection of [`data/historical/canonical/BTCUSDT/`](file:///d:/quantum-multi-agent/data/historical/canonical/BTCUSDT/) confirms Bitcoin rose from ~$27,000 in October 2023 to ~$73,000 in March 2024 and traded primarily between $55,000 and $70,000 through October 2026. However, altcoins such as ADAUSDT, LTCUSDT, and DOGEUSDT experienced prolonged multimonth drawdowns and sideways ranges during the same window.
- **Governance Consequence:** A combined bidirectional backtest could mask severe short losses behind long BTC/SOL gains. Independent directional reporting is mandatory.

### Claim 2: 'Persistently Positive Funding Rates in Bull Regimes'
- **Classification:** `UNSUPPORTED_IN_REPO` / `UNVERIFIED_ASSUMPTION`.
- **Evidence Trace:** Historical funding rates are completely absent from canonical Parquet data (`FUNDING_DATA_UNAVAILABLE`). While crypto domain literature confirms that perpetual funding rates are typically positive in bull regimes, this is NOT an empirically measured fact in the repository.
- **Governance Consequence:** All funding impact claims must remain classified as parametric assumptions.

### Claim 3: 'Greater Short-Exit Slippage During Liquidation Cascades'
- **Classification:** `THEORETICAL` / Domain Stylized Fact.
- **Evidence Trace:** Canonical Parquet data contains 5-minute OHLCV candles, not order book depth or liquidation feeds. Increased slippage when buying to cover during panic wicks is theoretically sound based on market microstructure principles, but unverified in dataset.

### Claim 4: 'Bidirectional Trading Roughly Doubles Signal Frequency'
- **Classification:** `THEORETICAL_UNVERIFIED` / Mathematically Inaccurate.
- **Evidence Trace:** Bidirectional trade count is $N_{\text{long}} + N_{\text{short}}$. If models have asymmetric selective thresholds or if the market regime favors one direction, Short signals may trigger far less frequently than Long signals. Assuming it 'doubles' frequency is an ungrounded assumption.

---

## 2. MANDATORY REPORTING RULES & SUPERVISOR RECOMMENDATION

1. **Strict Directional Disaggregation:** Any authorized Phase 5.5 backtest must output separate equity curves, Sharpe ratios, win rates, and profit factors for Long-Only, Short-Only, and Combined.
2. **Independent Failure Rule:** If Short trades fail Gate 2 net profitability, the system must not allow Long profits to subsidize deployment; Short execution must be disabled.
3. **Supervisor Recommendation:** Select `Bidirectional with mandatory separate reporting`.
4. **Status:** `PENDING_HUMAN_DECISION`.
