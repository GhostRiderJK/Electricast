# ElectriCast — Backtest Results

This document reports the four-fold day-ahead backtest stored in `backend/results.json`.
All numbers below were read from that artifact (generated 2026-10-23T19:30:48+05:30) and can
be regenerated with:

```bash
python backend/evaluate.py
```

No number in this document is hardcoded in the UI; the dashboard reads the same artifact
through the FastAPI backend.

## Protocol

- **Timezone:** Asia/Kolkata (IST). Every forecast covers 24 IST clock hours.
- **Target:** mean hourly load per reporting stable apartment, in Wh (`target_wh`).
- **Forecast origin:** 00:00 IST of each test day.
- **Information set:** target observations strictly before the origin. XGBoost features and the
  seasonal/long-lag baselines use lags of at least 24 h; persistence uses only the last
  observation before the origin; SARIMA refits weekly on a trailing window and advances its
  state with actuals up to each origin. Weather and reporting counts are lagged at least 24 h;
  calendar, holiday and semester flags are known in advance.
- **Folds:** four expanding windows with `train_start` fixed at 2017-05-01.
- **Evaluation mask:** hours where the target and the seasonal-naive-24 forecast both exist,
  so every model is scored on the same hours within a fold (subject to its own coverage).
- **Metrics:** MAE, RMSE, WAPE (%), MASE, bias, R², sMAPE (%). MASE scale is the mean absolute
  24-h seasonal difference over valid training pairs in the fold.
- **Best baseline:** lowest MASE on the all-four-baseline mask when that mask covers at least
  max(24 h, 50%) of the evaluation hours; otherwise on the evaluation mask.
- **Significance:** two-sided Wilcoxon signed-rank test on paired absolute errors against the
  best baseline. p-values are unadjusted, and each pair is tested separately; this is not a
  model-selection procedure. `small_sample` flags fewer than 10 pairs.

## Folds and coverage

| Fold | Train window | Test window | Train valid h | Clock h | Target-valid h | Eval h | Eval days | MASE scale (Wh) |
|---|---|---|---:|---:|---:|---:|---:|---:|
| 2017-07 | 2017-05-01 → 2017-06-30 | 2017-07-01 → 2017-07-31 | 1,464 | 744 | 744 | 744 | 31 | 84.61 |
| 2017-08 | 2017-05-01 → 2017-07-31 | 2017-08-01 → 2017-08-31 | 2,208 | 744 | 744 | 744 | 31 | 81.34 |
| 2017-09_12 | 2017-05-01 → 2017-08-31 | 2017-09-01 → 2017-12-31 | 2,952 | 2,928 | 2,374 | 2,243 | 102 | 80.06 |
| 2018-05_06 | 2017-05-01 → 2017-12-31 | 2018-05-01 → 2018-06-04 | 5,326 | 840 | 214 | 182 | 8 | 102.67 |

The 2018 fold is short and sparse: 214 of 840 clock hours have a valid target and the
evaluation mask retains 182 hours across 8 days. Training ends on 2017-12-31, Jan–Apr 2018 has
no readings at all, and the test starts on 2018-05-01, so this fold tests recovery after a
four-month gap; the training window itself has 5,326 valid hours of 5,880.

## Per-fold metrics

All values in Wh except WAPE, MASE, sMAPE and R². `n` is the number of hours on which that
model was scored; models with partial coverage are not imputed.

### 2017-07

Best baseline: **seasonal naive 24 h** (selected on the all-four-baseline mask, 744 h).

| Model | n | MAE | RMSE | WAPE % | MASE | Bias | R² | sMAPE % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Persistence | 744 | 119.56 | 155.91 | 32.81 | 1.413 | 62.63 | −0.735 | 31.34 |
| Seasonal naive 24 h | 744 | 75.01 | 103.36 | 20.59 | 0.887 | 0.44 | 0.237 | 23.07 |
| Same hour last week | 744 | 95.00 | 129.84 | 26.07 | 1.123 | 10.59 | −0.203 | 28.50 |
| Mean of 4 same weekdays | 744 | 86.94 | 114.40 | 23.86 | 1.028 | 30.96 | 0.066 | 24.89 |
| XGBoost | 744 | 69.31 | 90.53 | 19.02 | 0.819 | 5.14 | 0.415 | 20.92 |
| SARIMA | 744 | 65.66 | 87.70 | 18.02 | 0.776 | 7.89 | 0.451 | 19.97 |
| Quantile XGBoost (P50) | 744 | 65.99 | 87.83 | 18.11 | 0.780 | −1.48 | 0.449 | 19.88 |

Paired comparison against the best baseline:

| Compared model | n pairs | Median abs-error diff (Wh) | Model better? | p-value |
|---|---:|---:|---|---:|
| Persistence | 744 | +30.33 | no | 8.4e−23 |
| Same hour last week | 744 | +10.05 | no | 7.7e−06 |
| Mean of 4 same weekdays | 744 | +4.78 | no | 0.0030 |
| XGBoost | 744 | −4.00 | yes | 0.0215 |
| SARIMA | 744 | −6.61 | yes | 1.2e−04 |
| Quantile XGBoost (P50) | 744 | −7.25 | yes | 6.4e−05 |

The diff is the median of (compared model's absolute error − best baseline's absolute error),
so negative means the model has the smaller error. All three learned models beat the seasonal
baseline significantly in this fold.

### 2017-08

Best baseline: **mean of the last 4 same weekdays** (all-four-baseline mask, 744 h).

| Model | n | MAE | RMSE | WAPE % | MASE | Bias | R² | sMAPE % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Persistence | 744 | 105.75 | 133.17 | 28.97 | 1.300 | 18.23 | −0.432 | 28.63 |
| Seasonal naive 24 h | 744 | 76.31 | 101.77 | 20.91 | 0.938 | −0.52 | 0.164 | 22.16 |
| Same hour last week | 744 | 74.52 | 98.57 | 20.42 | 0.916 | −7.58 | 0.215 | 21.76 |
| Mean of 4 same weekdays | 744 | 58.93 | 78.10 | 16.14 | 0.725 | −8.11 | 0.507 | 17.17 |
| XGBoost | 744 | 59.51 | 80.87 | 16.30 | 0.732 | −12.87 | 0.472 | 16.96 |
| SARIMA | 744 | 60.60 | 81.11 | 16.60 | 0.745 | −6.53 | 0.469 | 17.31 |
| Quantile XGBoost (P50) | 744 | 60.58 | 82.06 | 16.60 | 0.745 | −15.23 | 0.456 | 17.30 |

Paired comparison against the best baseline:

| Compared model | n pairs | Median abs-error diff (Wh) | Model better? | p-value |
|---|---:|---:|---|---:|
| Persistence | 744 | +39.85 | no | 7.1e−40 |
| Seasonal naive 24 h | 744 | +9.56 | no | 2.9e−09 |
| Same hour last week | 744 | +10.57 | no | 6.5e−14 |
| XGBoost | 744 | −0.15 | yes (not significant) | 0.844 |
| SARIMA | 744 | +0.42 | no | 0.830 |
| Quantile XGBoost (P50) | 744 | +0.00 | no | 0.607 |

The learned models are close to the calendar-average baseline in this month; on MAE all three
are slightly worse, and none of the paired differences is statistically discernible.

### 2017-09_12

Best baseline: **persistence** (selected on the all-four-baseline mask, 1,290 h). Note that
the selection mask is smaller than the evaluation mask, so the headline metrics below are on a
different subset than the selection; the artifact records both.

| Model | n | MAE | RMSE | WAPE % | MASE | Bias | R² | sMAPE % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Persistence | 2,243 | 116.21 | 182.03 | 48.45 | 1.452 | 26.76 | 0.152 | 50.40 |
| Seasonal naive 24 h | 2,243 | 132.19 | 210.41 | 55.11 | 1.651 | 3.99 | −0.134 | 63.29 |
| Same hour last week | 1,927 | 202.78 | 267.20 | 85.98 | 2.533 | 24.71 | −0.773 | 98.29 |
| Mean of 4 same weekdays | 1,290 | 167.57 | 203.42 | 85.05 | 2.093 | 57.72 | −0.083 | 100.33 |
| XGBoost | 2,243 | 167.27 | 212.55 | 69.73 | 2.089 | 111.15 | −0.157 | 79.47 |
| SARIMA | 1,554 | 104.23 | 146.99 | 44.17 | 1.302 | 8.14 | 0.476 | 70.18 |
| Quantile XGBoost (P50) | 2,243 | 159.14 | 202.73 | 66.34 | 1.988 | 93.07 | −0.052 | 79.07 |

Paired comparison against the best baseline:

| Compared model | n pairs | Median abs-error diff (Wh) | Model better? | p-value |
|---|---:|---:|---|---:|
| Seasonal naive 24 h | 2,243 | −0.90 | yes (not significant) | 0.407 |
| Same hour last week | 1,927 | +42.30 | no | 1.1e−51 |
| Mean of 4 same weekdays | 1,290 | +74.87 | no | 1.2e−35 |
| XGBoost | 2,243 | +12.37 | no | 2.3e−22 |
| SARIMA | 1,554 | −0.43 | yes | 0.0029 |
| Quantile XGBoost (P50) | 2,243 | +10.92 | no | 2.5e−19 |

This is the hardest fold: the target is heterogeneous across September–December and the
December inactivity flags affect the level. XGBoost and P50 carry a large positive bias;
SARIMA, which is refit weekly and sees the recent level, is the only learned model with a
lower median error than persistence, and its win is small (0.43 Wh) though significant.

### 2018-05_06

Best baseline: **seasonal naive 24 h** (evaluation-mask fallback, 182 h, because the
all-four mask covers fewer than 50% of the evaluation hours).

| Model | n | MAE | RMSE | WAPE % | MASE | Bias | R² | sMAPE % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Persistence | 182 | 274.61 | 335.85 | 58.53 | 2.675 | 185.12 | −2.650 | 51.80 |
| Seasonal naive 24 h | 182 | 132.87 | 192.27 | 28.32 | 1.294 | −67.30 | −0.196 | 40.53 |
| Same hour last week | 38 | 384.27 | 449.73 | 71.81 | 3.743 | −328.44 | −2.640 | 126.99 |
| Mean of 4 same weekdays | 0 | — | — | — | — | — | — | — |
| XGBoost | 182 | 120.75 | 159.57 | 25.74 | 1.176 | −87.45 | 0.176 | 27.40 |
| SARIMA | 38 | 93.80 | 127.08 | 17.53 | 0.914 | −35.21 | 0.709 | 24.09 |
| Quantile XGBoost (P50) | 182 | 113.94 | 150.13 | 24.29 | 1.110 | −78.61 | 0.271 | 25.99 |

`mean_last_4_same_weekdays` has no usable hours because the preceding four same-weekday hours
are missing from the sparse 2018 target coverage; the artifact records `status: "no_data"` with
null metrics.

Paired comparison against the best baseline:

| Compared model | n pairs | Median abs-error diff (Wh) | Model better? | p-value |
|---|---:|---:|---|---:|
| Persistence | 182 | +126.58 | no | 2.0e−13 |
| Same hour last week | 38 | +288.50 | no | 4.8e−08 |
| Mean of 4 same weekdays | 0 | — | — | no paired hours |
| XGBoost | 182 | +0.28 | no | 0.518 |
| SARIMA | 38 | −9.36 | yes | 0.0253 |
| Quantile XGBoost (P50) | 182 | −3.52 | yes (not significant) | 0.309 |

SARIMA's favourable number rests on 38 paired hours (it predicted 96 hours, of which 38 overlap
the evaluation mask); it is directionally consistent with the Sep–Dec result but should not be
read as a precise 2018 estimate.

## Fold means

Unweighted mean ± sample standard deviation across the four folds (three for the mean-of-4
baseline, which has no 2018 data). `n` is the total evaluable hours.

| Model | Folds | Eval hours | MAE | RMSE | WAPE % | MASE | R² | Beats seasonal naive |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Persistence | 4 | 3,913 | 154.03 ± 80.60 | 201.74 ± 91.61 | 42.19 ± 13.77 | 1.710 ± 0.646 | −0.917 ± 1.213 | 1/4 |
| Seasonal naive 24 h | 4 | 3,913 | 104.10 ± 32.84 | 151.95 ± 57.51 | 31.23 ± 16.32 | 1.193 ± 0.355 | 0.018 ± 0.215 | reference |
| Same hour last week | 4 | 3,453 | 189.14 ± 141.73 | 236.34 ± 160.01 | 51.07 ± 32.73 | 2.079 ± 1.322 | −0.850 ± 1.260 | 1/4 |
| Mean of 4 same weekdays | 3 | 2,778 | 104.48 ± 56.40 | 131.97 ± 64.48 | 41.69 ± 37.75 | 1.282 ± 0.719 | 0.163 ± 0.307 | 1/3 |
| XGBoost | 4 | 3,913 | 104.21 ± 49.89 | 135.88 ± 61.97 | 32.70 ± 25.01 | 1.204 ± 0.621 | 0.227 ± 0.286 | 3/4 |
| SARIMA | 4 | 3,080 | 81.07 ± 21.25 | 110.72 ± 31.57 | 24.08 ± 13.41 | 0.934 ± 0.256 | 0.526 ± 0.123 | 4/4 |
| Quantile XGBoost (P50) | 4 | 3,913 | 99.91 ± 46.20 | 130.69 ± 57.06 | 31.33 ± 23.58 | 1.156 ± 0.579 | 0.281 ± 0.238 | 3/4 |

"Beats seasonal naive" is a descriptive count over folds where both models have data, based on
MAE; it is not a significance test. The fold-mean ranking is strongly influenced by the
Sep–Dec fold, where MAE roughly doubles for the seasonal and learned point models (persistence
and SARIMA hold up better).

## Prediction intervals

The quantile XGBoost models produce P10/P50/P90. Coverage is the share of the model's scored
hours with the actual inside [P10, P90]; the nominal level is 80%. Pinball loss is in Wh.

| Fold | n | Coverage | Mean width (Wh) | Pinball P10 | Pinball P50 | Pinball P90 | Pinball mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2017-07 | 744 | 71.64% | 177.44 | 17.14 | 33.00 | 15.05 | 21.73 |
| 2017-08 | 744 | 78.49% | 176.75 | 13.58 | 30.29 | 15.73 | 19.87 |
| 2017-09_12 | 2,243 | 44.81% | 210.76 | 75.68 | 79.57 | 30.39 | 61.88 |
| 2018-05_06 | 182 | 69.23% | 229.05 | 19.72 | 56.97 | 29.07 | 35.25 |
| Hour-weighted | 3,913 | 57.45% | 198.81 | — | — | — | 45.02 |
| Fold-unweighted | — | 66.04% | 198.50 | — | — | — | 34.68 |

The intervals are reasonably close to nominal in the two summer folds and severely
undercover in Sep–Dec, where the model's point forecast is also biased. They are reported as
calibration diagnostics, not as production-grade uncertainty bounds.

## Data-quality inputs

From `backend/data_quality.json`:

- 39 of 39 raw files read, 196,449 rows total.
- Hourly panel 12,891 h × 39 apartments; 5,291 hours with zero reporting apartments.
- 24 apartments pass the >90% coverage stable-panel rule.
- Target valid for 7,683 hours; mean 333.50 Wh.
- 83 hours imputed in short runs (≤6 h); 5,208 hours in 31 excluded long runs; longest 3,514 h.
- 21 apartments flagged suspect inactive in December 2017 (13 of them stable).

Weather inputs come from the Open-Meteo archive for one Mumbai grid point (19.1334 N,
72.9133 E): 11,688 cached hours, six variables, no missing values, all lags ≥24 h.

## Reproduction

```bash
# from the repository root
python backend/build_data_quality.py   # writes backend/data_quality.json
python backend/evaluate.py             # writes backend/results.json
python -m pytest backend/tests -q      # 34 tests
```

`evaluate.py` rebuilds the target, retrains XGBoost (with Optuna), quantile XGBoost, and
SARIMA for every fold, and scores all baselines on the shared mask. Training dominates the
runtime; the script is not run at API startup. The backend only reads the generated JSON.

## Caveats

- Four folds only, and the 2018 fold has 182 evaluable hours across 8 days. Fold-mean
  differences smaller than the fold-to-fold spread should not be treated as stable rankings.
- The target is a per-reporting-apartment mean over the stable panel; it is not total building
  load, and changes in reporting counts can move it.
- December 2017 contains suspected vacancies, which affects the Sep–Dec fold and every
  fold that trains through it (including the 2018 fold).
- SARIMA's weekly refit cannot operate through the long 2018 gap; its 2018 score covers only
  38 hours, and its fold-mean is computed over the hours it does cover.
- The Sep–Dec best baseline was selected on a 1,290-hour all-four mask while headline metrics
  use the 2,243-hour evaluation mask; the artifact records both.
- Wilcoxon p-values are unadjusted for multiple comparisons and are reported per model against
  the per-fold best baseline only.
- Weather is a single regional grid point, not building-level measurements.
