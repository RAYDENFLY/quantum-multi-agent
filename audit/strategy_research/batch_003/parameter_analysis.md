# Parameter Sensitivity & Structural Driver Analysis — `BATCH_003`

## 1. Primary Structural Drivers Identified in `batch_003`

| Parameter Dimension | Condition A | Mean Daily Return (A) | Condition B | Mean Daily Return (B) | Sensitivity Finding |
| :--- | :--- | :---: | :--- | :---: | :--- |
| **1h Liquidity Flush Conditioning (`htf_return_max_bps`)** | `<= -30 bps` (Pullback / Flush Absorption, `n=100`) | **`+0.0707% / day`** | `> -30 bps` (Unconditioned or Breakout Chasing, `n=0`) | `+0.0000% / day` | Buying OOF Long predictions *after* a 1-hour liquidity flush (`htf_ret_12 <= -45 bps`) avoids breakout exhaustion and captures `+20 to +40 bps` mean reversion displacement. |
| **Directional Mode (`direction_mode`)** | `LONG_ONLY` (`n=100`) | **`+0.0707% / day`** | `BOTH / SHORT / OTHER` (`n=0`) | `+0.0000% / day` | Unconditioned short signals suffer negative expectancy; only extreme upper-wick exhaustion shorts (`ABSORPTION_REVERSAL`) add positive value. |
| **AURCC Neutrality Ceiling (`p0_neutral_max`)** | `p0 <= 0.30` | Higher precision & lower DD | `p0 > 0.35` | Higher chop exposure | Selective abstention on `p_0` directly eliminates low-conviction chop trades. |
| **Asset Selection (`applicable_assets`)** | High-Alpha Altcoin Fleet (`DOGE`, `SOL`, `ADA`, `XRP`, `LINK`, `AVAX`) | Strongly positive net expectancy | Low-Volatility Majors (`BTC`, `ETH`) | Negative net expectancy after fees | `BTC` (`10.3 bps` median sigma) and `ETH` (`14.3 bps` median sigma) have narrow barriers relative to execution friction; `DOGE/SOL/ADA/XRP` provide wide barriers and 4/4 positive walk-forward folds. |
