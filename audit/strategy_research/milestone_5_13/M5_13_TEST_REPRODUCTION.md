# M5.13 Test Reproduction Record

## Required command

```powershell
python -m pytest tests/unit/ -q
```

## Research-artifact regeneration

```powershell
python scripts/generate_m5_13_baseline.py
python scripts/run_m5_13_alpha_discovery.py
```

## Controls that must remain true

1. All input rows must have `open_time_ms < 1793491200000`; the prospective holdout is sealed.
2. `EventDrivenPortfolioLedger` must be initialized with `initial_equity_usd=100.0`.
3. The admission cap is `<= 0.995000x`, and the active mark-to-market hard cap is `<= 1.000000x`.
4. The M5.13 unit test verifies all 18 mandated deliverables are present and non-empty.
5. The campaign output must not be interpreted as authority for paper or live trading.

## Current artifact checks

The M5.13 acceptance matrix records causal-feature, execution, statistical, shared-capital, and holdout-integrity checks as passing with the final research governance classification `PASS_WITH_LIMITATIONS`. The limitation is economic rather than accounting: the verified +0.145% mean-net-daily result remains materially below the +3.00% mandate.
