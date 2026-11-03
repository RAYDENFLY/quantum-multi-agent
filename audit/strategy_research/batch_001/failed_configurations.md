# Failed & Non-Qualified Configurations Audit — `BATCH_001`

All failed and non-qualifying configurations are permanently preserved for failure analysis and hypothesis elimination.

## 1. Classification Distribution Across All 100 Strategies

| Classification Code | Strategy Count |
| :--- | :---: |
| `BIDIRECTIONAL_SHORT_DRAG` | 2 |
| `EXCESSIVE_DRAWDOWN_BREACH` | 42 |
| `FOLD_INSTABILITY_REGIME_MISMATCH` | 7 |
| `NEGATIVE_NET_EXPECTANCY_FRICTION` | 44 |
| `POSITIVE_RETURN_BELOW_TARGET` | 3 |
| `QUALIFIED_SUCCESS` | 2 |

---

## 2. Detailed Failure Ledger (97 Configurations)

| Strategy ID | Config Hash | Experiment ID | Classification | Mean Daily | Net Cum. Return | Net Exp. | Max DD | Total Cost | Forensic Failure Mechanism |
| :---: | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `STRAT_082` | `a0bc7ac6632c3aa0` | `EXP_B001_STRAT_082_a0bc7ac6` | `FOLD_INSTABILITY_REGIME_MISMATCH` | +0.0550% | +19.19% | +3.56 bps | 20.27% | $51.58 | Positive cumulative return (+19.19%) but only 2/4 walk-forward folds positive. |
| `STRAT_075` | `d28ff026c7272e84` | `EXP_B001_STRAT_075_d28ff026` | `FOLD_INSTABILITY_REGIME_MISMATCH` | +0.0387% | +14.58% | +6.96 bps | 6.58% | $18.21 | Positive cumulative return (+14.58%) but only 2/4 walk-forward folds positive. |
| `STRAT_080` | `bc2996b8fd509d43` | `EXP_B001_STRAT_080_bc2996b8` | `FOLD_INSTABILITY_REGIME_MISMATCH` | +0.0377% | +13.25% | +3.72 bps | 8.92% | $32.91 | Positive cumulative return (+13.25%) but only 2/4 walk-forward folds positive. |
| `STRAT_077` | `7470eb5a1f21e55e` | `EXP_B001_STRAT_077_7470eb5a` | `FOLD_INSTABILITY_REGIME_MISMATCH` | +0.0275% | +7.13% | +1.94 bps | 22.76% | $44.91 | Positive cumulative return (+7.13%) but only 2/4 walk-forward folds positive. |
| `STRAT_057` | `aed8989707696cf8` | `EXP_B001_STRAT_057_aed89897` | `QUALIFIED_SUCCESS` | +0.0221% | +5.38% | +1.82 bps | 26.12% | $35.14 | Qualified positive strategy (+5.38% net return, MDD=26.12%). |
| `STRAT_014` | `d970334b5fb48001` | `EXP_B001_STRAT_014_d970334b` | `FOLD_INSTABILITY_REGIME_MISMATCH` | +0.0206% | +4.61% | +1.30 bps | 20.70% | $40.06 | Positive cumulative return (+4.61%) but only 2/4 walk-forward folds positive. |
| `STRAT_020` | `4ce62687a6c51c2d` | `EXP_B001_STRAT_020_4ce62687` | `QUALIFIED_SUCCESS` | +0.0126% | +4.00% | +1.76 bps | 9.21% | $22.05 | Qualified positive strategy (+4.00% net return, MDD=9.21%). |
| `STRAT_015` | `455f2d000687e7dc` | `EXP_B001_STRAT_015_455f2d00` | `FOLD_INSTABILITY_REGIME_MISMATCH` | +0.0106% | +3.19% | +2.51 bps | 9.05% | $12.70 | Positive cumulative return (+3.19%) but only 2/4 walk-forward folds positive. |
| `STRAT_013` | `d68f32c999f7547c` | `EXP_B001_STRAT_013_d68f32c9` | `FOLD_INSTABILITY_REGIME_MISMATCH` | +0.0043% | +1.14% | +1.27 bps | 10.87% | $12.28 | Positive cumulative return (+1.14%) but only 2/4 walk-forward folds positive. |
| `STRAT_047` | `b4dada9db4442b62` | `EXP_B001_STRAT_047_b4dada9d` | `EXCESSIVE_DRAWDOWN_BREACH` | +0.0020% | -1.89% | +0.40 bps | 31.60% | $37.73 | Maximum portfolio drawdown 31.60% breached hard 30.0% ceiling. |
| `STRAT_044` | `bc83672182e61bba` | `EXP_B001_STRAT_044_bc836721` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0010% | -2.98% | -0.15 bps | 19.54% | $48.08 | Gross expectancy (+7.94 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_008` | `55a3ddf2a5514ba3` | `EXP_B001_STRAT_008_55a3ddf2` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0029% | -1.50% | -1.37 bps | 6.58% | $5.88 | Gross expectancy (+6.72 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_066` | `0d950b1a608cb982` | `EXP_B001_STRAT_066_0d950b1a` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0038% | -2.49% | -0.28 bps | 14.41% | $30.41 | Gross expectancy (+7.79 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_004` | `0d4b1dba9c26b6f2` | `EXP_B001_STRAT_004_0d4b1dba` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0053% | -3.06% | -0.90 bps | 11.09% | $16.54 | Gross expectancy (+7.18 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_006` | `382a71d55d866b1f` | `EXP_B001_STRAT_006_382a71d5` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0065% | -4.20% | -0.48 bps | 18.71% | $33.31 | Gross expectancy (+7.61 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_005` | `d1e7c4f2c0e929eb` | `EXP_B001_STRAT_005_d1e7c4f2` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0067% | -3.77% | -0.28 bps | 14.83% | $35.54 | Gross expectancy (+7.78 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_071` | `32e01ffdfa04cae9` | `EXP_B001_STRAT_071_32e01ffd` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0075% | -3.54% | -1.03 bps | 13.06% | $22.31 | Gross expectancy (+7.06 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_063` | `00b1cc10e894b268` | `EXP_B001_STRAT_063_00b1cc10` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0079% | -4.18% | -0.72 bps | 14.14% | $22.54 | Gross expectancy (+7.42 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_016` | `41c7215b6b14a67c` | `EXP_B001_STRAT_016_41c7215b` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0098% | -3.56% | -10.17 bps | 3.56% | $2.82 | Gross expectancy (-2.08 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_085` | `cbc944a84154ff27` | `EXP_B001_STRAT_085_cbc944a8` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0106% | -3.93% | -7.17 bps | 5.25% | $4.26 | Gross expectancy (+0.79 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_003` | `1222c1c3b0357ad4` | `EXP_B001_STRAT_003_1222c1c3` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0143% | -7.33% | -0.80 bps | 25.06% | $40.94 | Gross expectancy (+7.28 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_002` | `fd1a59498fa70c49` | `EXP_B001_STRAT_002_fd1a5949` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0171% | -6.32% | -5.16 bps | 9.91% | $9.22 | Gross expectancy (+2.92 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_069` | `f871274906c70ba1` | `EXP_B001_STRAT_069_f8712749` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0172% | -7.66% | -0.91 bps | 13.30% | $44.10 | Gross expectancy (+7.16 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_012` | `50297101e99cdfd5` | `EXP_B001_STRAT_012_50297101` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0179% | -7.44% | -3.13 bps | 14.21% | $15.80 | Gross expectancy (+4.93 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_084` | `b2ce9fd50d53c6e8` | `EXP_B001_STRAT_084_b2ce9fd5` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0198% | -7.28% | -5.87 bps | 10.37% | $9.28 | Gross expectancy (+2.10 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_019` | `e18abe2c9d25720e` | `EXP_B001_STRAT_019_e18abe2c` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0203% | -8.03% | -2.90 bps | 12.54% | $18.45 | Gross expectancy (+5.17 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_079` | `3e924bd4b059a67a` | `EXP_B001_STRAT_079_3e924bd4` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0205% | -8.86% | -1.79 bps | 18.17% | $31.28 | Gross expectancy (+6.29 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_068` | `d20d36b607749cb0` | `EXP_B001_STRAT_068_d20d36b6` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0214% | -9.86% | -1.03 bps | 23.48% | $48.35 | Gross expectancy (+7.05 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_067` | `ab0d2bc2e96d72b4` | `EXP_B001_STRAT_067_ab0d2bc2` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0215% | -8.91% | -3.02 bps | 21.23% | $23.92 | Gross expectancy (+5.05 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_011` | `ae88ba9e9029860c` | `EXP_B001_STRAT_011_ae88ba9e` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0227% | -9.04% | -2.75 bps | 12.81% | $20.55 | Gross expectancy (+5.32 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_088` | `21311757926b8c4c` | `EXP_B001_STRAT_088_21311757` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0227% | -10.23% | -0.92 bps | 19.58% | $59.90 | Gross expectancy (+7.16 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_070` | `5cccb9e8ee4c0615` | `EXP_B001_STRAT_070_5cccb9e8` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0233% | -8.84% | -2.35 bps | 13.84% | $26.09 | Gross expectancy (+5.73 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_078` | `8e3fa054fe9f0d2b` | `EXP_B001_STRAT_078_8e3fa054` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0305% | -12.55% | -1.50 bps | 20.81% | $53.90 | Gross expectancy (+6.58 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_041` | `1bbaa0631e5737b9` | `EXP_B001_STRAT_041_1bbaa063` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.0327% | -14.12% | -1.39 bps | 32.07% | $52.26 | Maximum portfolio drawdown 32.07% breached hard 30.0% ceiling. |
| `STRAT_094` | `890ccb58ea6442f5` | `EXP_B001_STRAT_094_890ccb58` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0329% | -13.36% | -1.58 bps | 19.59% | $51.23 | Gross expectancy (+6.51 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_017` | `54ae0ea1725496df` | `EXP_B001_STRAT_017_54ae0ea1` | `BIDIRECTIONAL_SHORT_DRAG` | -0.0374% | -13.09% | -11.08 bps | 15.40% | $9.38 | Unconditioned short trades eroded portfolio alpha (Net Exp=-11.08 bps, CumRet=-13.09%). |
| `STRAT_083` | `9e5204fc82a9b285` | `EXP_B001_STRAT_083_9e5204fc` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0385% | -14.73% | -1.81 bps | 21.14% | $49.28 | Gross expectancy (+6.26 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_049` | `ef9f24d7ed697f76` | `EXP_B001_STRAT_049_ef9f24d7` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.0405% | -15.60% | -3.31 bps | 32.37% | $26.60 | Maximum portfolio drawdown 32.37% breached hard 30.0% ceiling. |
| `STRAT_091` | `0155d750a5ffe778` | `EXP_B001_STRAT_091_0155d750` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0417% | -16.59% | -1.65 bps | 27.64% | $59.18 | Gross expectancy (+6.43 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_024` | `5917b81377120d30` | `EXP_B001_STRAT_024_5917b813` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0425% | -15.92% | -3.36 bps | 29.87% | $30.29 | Gross expectancy (+4.73 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_055` | `bea5867cd9a4bebe` | `EXP_B001_STRAT_055_bea5867c` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0431% | -17.54% | -3.70 bps | 25.08% | $31.49 | Gross expectancy (+4.45 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_034` | `c4eab44b62da3739` | `EXP_B001_STRAT_034_c4eab44b` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0439% | -15.50% | -6.31 bps | 19.12% | $19.29 | Gross expectancy (+1.78 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_076` | `345ce9689b5334fc` | `EXP_B001_STRAT_076_345ce968` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.0457% | -18.77% | -3.03 bps | 30.60% | $41.54 | Maximum portfolio drawdown 30.60% breached hard 30.0% ceiling. |
| `STRAT_053` | `a9f7a5895f2a4fcf` | `EXP_B001_STRAT_053_a9f7a589` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0458% | -16.48% | -3.96 bps | 18.24% | $31.23 | Gross expectancy (+4.12 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_093` | `d6481ccdfa63f24e` | `EXP_B001_STRAT_093_d6481ccd` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.0468% | -18.50% | -1.87 bps | 35.15% | $60.35 | Maximum portfolio drawdown 35.15% breached hard 30.0% ceiling. |
| `STRAT_059` | `60706b9f22ada333` | `EXP_B001_STRAT_059_60706b9f` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0473% | -16.75% | -5.26 bps | 22.13% | $25.30 | Gross expectancy (+2.84 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_092` | `a4880aede485ca0b` | `EXP_B001_STRAT_092_a4880aed` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0474% | -17.47% | -2.26 bps | 20.19% | $50.75 | Gross expectancy (+5.82 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_065` | `fddc3ca4118562c6` | `EXP_B001_STRAT_065_fddc3ca4` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0497% | -16.87% | -9.08 bps | 17.93% | $15.41 | Gross expectancy (-0.97 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_089` | `e5eb185340edd006` | `EXP_B001_STRAT_089_e5eb1853` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0562% | -19.62% | -6.56 bps | 21.36% | $22.87 | Gross expectancy (+1.52 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_033` | `63627e87e89606cd` | `EXP_B001_STRAT_033_63627e87` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0569% | -20.28% | -2.95 bps | 24.81% | $48.60 | Gross expectancy (+5.12 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_054` | `f87a1417c7bec725` | `EXP_B001_STRAT_054_f87a1417` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0591% | -20.15% | -7.06 bps | 22.22% | $22.19 | Gross expectancy (+1.02 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_058` | `db32036a024fa555` | `EXP_B001_STRAT_058_db32036a` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0655% | -22.37% | -5.32 bps | 23.81% | $32.41 | Gross expectancy (+2.75 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_018` | `5d9312e3ad94be64` | `EXP_B001_STRAT_018_5d9312e3` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0690% | -23.07% | -6.34 bps | 23.54% | $27.62 | Gross expectancy (+1.74 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_081` | `593d9b94b7339266` | `EXP_B001_STRAT_081_593d9b94` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0690% | -23.22% | -6.96 bps | 26.01% | $25.96 | Gross expectancy (+1.11 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_001` | `0e7ac079e342b51e` | `EXP_B001_STRAT_001_0e7ac079` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0717% | -24.16% | -4.85 bps | 25.69% | $36.79 | Gross expectancy (+3.23 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_045` | `3b5b328c3c466640` | `EXP_B001_STRAT_045_3b5b328c` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.0732% | -25.11% | -3.46 bps | 30.45% | $53.91 | Maximum portfolio drawdown 30.45% breached hard 30.0% ceiling. |
| `STRAT_087` | `0ac2e51906c121b3` | `EXP_B001_STRAT_087_0ac2e519` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0800% | -26.66% | -7.01 bps | 28.11% | $28.69 | Gross expectancy (+1.06 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_042` | `d44e7c1a6696add0` | `EXP_B001_STRAT_042_d44e7c1a` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.0818% | -27.97% | -3.01 bps | 33.09% | $66.60 | Maximum portfolio drawdown 33.09% breached hard 30.0% ceiling. |
| `STRAT_052` | `010f1754dd95aa50` | `EXP_B001_STRAT_052_010f1754` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0822% | -26.98% | -7.24 bps | 28.15% | $29.42 | Gross expectancy (+0.86 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_073` | `5666470578b08dbf` | `EXP_B001_STRAT_073_56664705` | `BIDIRECTIONAL_SHORT_DRAG` | -0.0833% | -26.73% | -13.07 bps | 29.15% | $16.15 | Unconditioned short trades eroded portfolio alpha (Net Exp=-13.07 bps, CumRet=-26.73%). |
| `STRAT_064` | `f91aeb41d9c48efc` | `EXP_B001_STRAT_064_f91aeb41` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0839% | -27.56% | -5.15 bps | 28.73% | $40.70 | Gross expectancy (+2.92 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_031` | `ba5d2db4a4f69245` | `EXP_B001_STRAT_031_ba5d2db4` | `NEGATIVE_NET_EXPECTANCY_FRICTION` | -0.0879% | -28.21% | -6.81 bps | 29.50% | $31.32 | Gross expectancy (+1.26 bps) insufficient to overcome 8.0 bps friction + funding. |
| `STRAT_098` | `cbe9b75f318c84bf` | `EXP_B001_STRAT_098_cbe9b75f` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.0890% | -29.39% | -6.41 bps | 33.50% | $62.24 | Maximum portfolio drawdown 33.50% breached hard 30.0% ceiling. |
| `STRAT_028` | `bf84eebe208e7bc1` | `EXP_B001_STRAT_028_bf84eebe` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.0977% | -30.85% | -6.35 bps | 31.94% | $36.28 | Maximum portfolio drawdown 31.94% breached hard 30.0% ceiling. |
| `STRAT_035` | `c643337fdf51075b` | `EXP_B001_STRAT_035_c643337f` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.1076% | -33.75% | -6.31 bps | 35.51% | $41.11 | Maximum portfolio drawdown 35.51% breached hard 30.0% ceiling. |
| `STRAT_040` | `bc0aceafdc754fa6` | `EXP_B001_STRAT_040_bc0aceaf` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.1088% | -35.75% | -3.12 bps | 39.51% | $76.12 | Maximum portfolio drawdown 39.51% breached hard 30.0% ceiling. |
| `STRAT_086` | `a52ae1c43ac641b2` | `EXP_B001_STRAT_086_a52ae1c4` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.1182% | -38.12% | -8.20 bps | 40.86% | $34.01 | Maximum portfolio drawdown 40.86% breached hard 30.0% ceiling. |
| `STRAT_026` | `3f7751b8d3776fc2` | `EXP_B001_STRAT_026_3f7751b8` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.1238% | -37.28% | -6.97 bps | 38.04% | $43.23 | Maximum portfolio drawdown 38.04% breached hard 30.0% ceiling. |
| `STRAT_048` | `895bd320a210618e` | `EXP_B001_STRAT_048_895bd320` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.1248% | -37.02% | -7.37 bps | 38.39% | $41.47 | Maximum portfolio drawdown 38.39% breached hard 30.0% ceiling. |
| `STRAT_027` | `f64b0f83cd71fd1f` | `EXP_B001_STRAT_027_f64b0f83` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.1345% | -39.89% | -8.15 bps | 41.56% | $34.98 | Maximum portfolio drawdown 41.56% breached hard 30.0% ceiling. |
| `STRAT_060` | `32a48b9a19783d0e` | `EXP_B001_STRAT_060_32a48b9a` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.1362% | -39.86% | -10.94 bps | 40.34% | $29.62 | Maximum portfolio drawdown 40.34% breached hard 30.0% ceiling. |
| `STRAT_025` | `adfd92326f6f8369` | `EXP_B001_STRAT_025_adfd9232` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.1569% | -44.23% | -18.64 bps | 45.53% | $18.67 | Maximum portfolio drawdown 45.53% breached hard 30.0% ceiling. |
| `STRAT_062` | `62863cc8273350bf` | `EXP_B001_STRAT_062_62863cc8` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.1577% | -44.96% | -7.90 bps | 45.85% | $46.35 | Maximum portfolio drawdown 45.85% breached hard 30.0% ceiling. |
| `STRAT_096` | `02ecd0400fa4e49d` | `EXP_B001_STRAT_096_02ecd040` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.1581% | -45.50% | -9.76 bps | 46.63% | $34.82 | Maximum portfolio drawdown 46.63% breached hard 30.0% ceiling. |
| `STRAT_097` | `e6cc9d5c619d1373` | `EXP_B001_STRAT_097_e6cc9d5c` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.1608% | -46.24% | -7.92 bps | 47.19% | $76.96 | Maximum portfolio drawdown 47.19% breached hard 30.0% ceiling. |
| `STRAT_030` | `6a52533c6c6fc732` | `EXP_B001_STRAT_030_6a52533c` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.1655% | -45.74% | -7.83 bps | 46.60% | $47.43 | Maximum portfolio drawdown 46.60% breached hard 30.0% ceiling. |
| `STRAT_009` | `64e1dfbffb6d158f` | `EXP_B001_STRAT_009_64e1dfbf` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.1687% | -48.38% | -7.11 bps | 49.04% | $48.88 | Maximum portfolio drawdown 49.04% breached hard 30.0% ceiling. |
| `STRAT_010` | `807a98beadaceb6e` | `EXP_B001_STRAT_010_807a98be` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.1718% | -48.24% | -9.97 bps | 48.79% | $36.70 | Maximum portfolio drawdown 48.79% breached hard 30.0% ceiling. |
| `STRAT_022` | `87db9c7174d79de6` | `EXP_B001_STRAT_022_87db9c71` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.1803% | -49.61% | -7.18 bps | 54.25% | $47.71 | Maximum portfolio drawdown 54.25% breached hard 30.0% ceiling. |
| `STRAT_046` | `0a401a4de1e4af79` | `EXP_B001_STRAT_046_0a401a4d` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.1806% | -51.35% | -4.18 bps | 53.73% | $76.66 | Maximum portfolio drawdown 53.73% breached hard 30.0% ceiling. |
| `STRAT_056` | `a8fff5d2063fde61` | `EXP_B001_STRAT_056_a8fff5d2` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.1827% | -49.46% | -8.08 bps | 50.38% | $50.91 | Maximum portfolio drawdown 50.38% breached hard 30.0% ceiling. |
| `STRAT_050` | `97bca28ac63838f3` | `EXP_B001_STRAT_050_97bca28a` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.1855% | -50.88% | -5.77 bps | 51.45% | $60.29 | Maximum portfolio drawdown 51.45% breached hard 30.0% ceiling. |
| `STRAT_072` | `c48208a7d2383a6b` | `EXP_B001_STRAT_072_c48208a7` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.1874% | -51.84% | -6.65 bps | 52.89% | $57.54 | Maximum portfolio drawdown 52.89% breached hard 30.0% ceiling. |
| `STRAT_090` | `1f800b33e2757376` | `EXP_B001_STRAT_090_1f800b33` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.1888% | -52.54% | -5.88 bps | 53.85% | $64.73 | Maximum portfolio drawdown 53.85% breached hard 30.0% ceiling. |
| `STRAT_043` | `079f83c68ffdad91` | `EXP_B001_STRAT_043_079f83c6` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.1898% | -52.43% | -6.87 bps | 57.85% | $63.14 | Maximum portfolio drawdown 57.85% breached hard 30.0% ceiling. |
| `STRAT_051` | `a0073cdc582cffcf` | `EXP_B001_STRAT_051_a0073cdc` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.2027% | -53.50% | -6.37 bps | 54.84% | $65.58 | Maximum portfolio drawdown 54.84% breached hard 30.0% ceiling. |
| `STRAT_100` | `32571de1b43efecf` | `EXP_B001_STRAT_100_32571de1` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.2083% | -55.39% | -6.45 bps | 56.95% | $65.33 | Maximum portfolio drawdown 56.95% breached hard 30.0% ceiling. |
| `STRAT_095` | `e9019292daf79ff1` | `EXP_B001_STRAT_095_e9019292` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.2104% | -55.07% | -11.99 bps | 55.80% | $33.29 | Maximum portfolio drawdown 55.80% breached hard 30.0% ceiling. |
| `STRAT_029` | `aa1beec2ca485205` | `EXP_B001_STRAT_029_aa1beec2` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.2131% | -54.74% | -15.92 bps | 57.18% | $28.21 | Maximum portfolio drawdown 57.18% breached hard 30.0% ceiling. |
| `STRAT_038` | `551e04121fb53389` | `EXP_B001_STRAT_038_551e0412` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.3024% | -68.94% | -5.41 bps | 70.40% | $86.85 | Maximum portfolio drawdown 70.40% breached hard 30.0% ceiling. |
| `STRAT_039` | `76c74f7cdde71f1c` | `EXP_B001_STRAT_039_76c74f7c` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.3153% | -69.53% | -10.10 bps | 70.88% | $56.73 | Maximum portfolio drawdown 70.88% breached hard 30.0% ceiling. |
| `STRAT_037` | `2ac438a1efd83d55` | `EXP_B001_STRAT_037_2ac438a1` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.3187% | -70.24% | -7.25 bps | 70.80% | $74.21 | Maximum portfolio drawdown 70.80% breached hard 30.0% ceiling. |
| `STRAT_032` | `bfaf0e1a4bb604d9` | `EXP_B001_STRAT_032_bfaf0e1a` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.3292% | -71.36% | -7.47 bps | 71.93% | $75.29 | Maximum portfolio drawdown 71.93% breached hard 30.0% ceiling. |
| `STRAT_099` | `7321b5229dd5011e` | `EXP_B001_STRAT_099_7321b522` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.3338% | -71.70% | -33.21 bps | 72.09% | $90.05 | Maximum portfolio drawdown 72.09% breached hard 30.0% ceiling. |
| `STRAT_023` | `92fc0be505f91360` | `EXP_B001_STRAT_023_92fc0be5` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.3420% | -72.36% | -9.56 bps | 75.36% | $59.13 | Maximum portfolio drawdown 75.36% breached hard 30.0% ceiling. |
| `STRAT_021` | `f7165a710ce70d1f` | `EXP_B001_STRAT_021_f7165a71` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.3742% | -75.52% | -9.10 bps | 76.78% | $62.78 | Maximum portfolio drawdown 76.78% breached hard 30.0% ceiling. |
| `STRAT_036` | `89b8dbe2ada5cf52` | `EXP_B001_STRAT_036_89b8dbe2` | `EXCESSIVE_DRAWDOWN_BREACH` | -0.5132% | -85.76% | -8.11 bps | 85.97% | $82.58 | Maximum portfolio drawdown 85.97% breached hard 30.0% ceiling. |
