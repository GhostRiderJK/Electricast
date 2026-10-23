# ElectriCast — Day-Ahead Electricity Load Forecasting

A full-stack dashboard for day-ahead residential electricity load forecasting on the IIT Bombay
campus apartment dataset (Dec 2016 – Jun 2018, with the backtest concentrated in 2017–18). The
current evaluation product is a four-fold expanding-window backtest of four naive baselines and
three learned models: tuned XGBoost, rolling SARIMA, and quantile XGBoost (P10/P50/P90). No LSTM
is shipped or displayed.

- Backend: FastAPI, pandas, NumPy, scikit-learn, statsmodels, XGBoost
- Frontend: React 18, Vite 5, Chart.js 4
- Tests: pytest (34 tests)
- Units: Wh internally; the UI labels Wh or divides by 1,000 for kWh
- Timezone: Asia/Kolkata (IST) throughout

## Quick start

Requirements: Python 3.12 and Node 20+.

```bash
make install          # pip install -r backend/requirements.txt && npm ci
make dev-backend      # http://localhost:8000  (docs at /docs)
make dev-frontend     # http://localhost:3000
```

Without GNU make:

```bash
python -m pip install -r backend/requirements.txt
(cd frontend && npm ci)
(cd backend && python -m uvicorn main:app --reload --port 8000)   # terminal 1
(cd frontend && npm run dev)                                       # terminal 2
```

Docker:

```bash
docker compose up --build
```

The frontend is served at http://localhost:3000 and the backend at http://localhost:8000.
`BACKEND_PORT` and `FRONTEND_PORT` override the published ports. Compose mounts `./data`
read-only at `/data` (the upload zero-shot model reads the campus CSVs on first use) and
mounts `backend/model_results.json` read-only.

Regenerate artifacts:

```bash
make data-quality     # backend/data_quality.json
make eval             # backend/results.json  (retrains learned models)
```

## Dataset

| Property | Value |
|---|---|
| Source | IIT Bombay residential campus apartments |
| Coverage | 2016-12-14 → 2018-06-04 IST (Jan–Apr 2018 has no readings) |
| Raw files | 39 apartment CSVs, 196,449 rows |
| Hourly panel | 12,891 h × 39 apartments |
| Stable panel | 24 apartments with >90% coverage |
| Target | mean hourly load per reporting stable apartment (`target_wh`, Wh) |
| Valid target hours | 7,683 |
| Short gaps | 83 h imputed (runs ≤ 6 h) |
| Excluded gaps | 5,208 h in 31 runs (excluded from train and evaluation) |
| Longest excluded run | 3,514 h |
| Suspect inactive | 21 apartments flagged in Dec 2017 (13 stable) |

The raw phase loads are resampled to hourly per apartment; the target is the mean across
apartments that report in that hour, so it is per-apartment load, not total building load.
The outlier cap is fitted on each fold's training window only.

## Evaluation protocol

- 24 hourly forecasts per test day, origin 00:00 IST; no test-day label is a forecast input.
- Evaluation mask: actual present and seasonal naive available. Models are scored on the hours
  where their own forecast also exists (long-lag baselines and SARIMA have partial coverage);
  each model's `n` is reported.
- All models may use only observations before the 00:00 origin. XGBoost features are lagged at
  least 24 h; SARIMA advances its state with actuals up to each origin.
- Four expanding-window folds, `train_start` fixed at 2017-05-01.
- Metrics: MAE, RMSE, WAPE, MASE, bias, R², sMAPE; MASE scale is the mean absolute
  seasonal (24 h) difference over valid training pairs.
- Best baseline = lowest MASE on the all-four-baseline mask when it covers ≥50% of the
  evaluation hours, otherwise on the evaluation mask.
- Significance: two-sided Wilcoxon signed-rank on paired absolute errors against the best
  baseline. p-values are unadjusted and not a model-selection procedure.

| Fold | Train window | Test window | Eval hours | Eval days |
|---|---|---|---:|---:|
| 2017-07 | 2017-05-01 → 2017-06-30 | 2017-07-01 → 2017-07-31 | 744 | 31 |
| 2017-08 | 2017-05-01 → 2017-07-31 | 2017-08-01 → 2017-08-31 | 744 | 31 |
| 2017-09_12 | 2017-05-01 → 2017-08-31 | 2017-09-01 → 2017-12-31 | 2,243 | 102 |
| 2018-05_06 | 2017-05-01 → 2017-12-31 | 2018-05-01 → 2018-06-04 | 182 | 8 |

## Results

Fold means are unweighted across the folds where each model has data; `n` is the total number
of evaluable hours. Full per-fold tables and significance tests are in [RESULTS.md](RESULTS.md);
the machine-readable source is `backend/results.json`.

| Model | Folds | Eval hours | MAE (Wh) | RMSE (Wh) | WAPE % | MASE | R² |
|---|---:|---:|---:|---:|---:|---:|---:|
| Persistence | 4 | 3,913 | 154.03 ± 80.60 | 201.74 | 42.19 | 1.710 | −0.917 |
| Seasonal naive 24 h | 4 | 3,913 | 104.10 ± 32.84 | 151.95 | 31.23 | 1.193 | 0.018 |
| Same hour last week | 4 | 3,453 | 189.14 ± 141.73 | 236.34 | 51.07 | 2.079 | −0.850 |
| Mean of 4 same weekdays | 3 | 2,778 | 104.48 ± 56.40 | 131.97 | 41.69 | 1.282 | 0.163 |
| XGBoost | 4 | 3,913 | 104.21 ± 49.89 | 135.88 | 32.70 | 1.204 | 0.227 |
| SARIMA | 4 | 3,080 | 81.07 ± 21.25 | 110.72 | 24.08 | 0.934 | 0.526 |
| Quantile XGBoost (P50) | 4 | 3,913 | 99.91 ± 46.20 | 130.69 | 31.33 | 1.156 | 0.281 |

Reading the table:

- SARIMA has the lowest MAE and MASE on the pooled folds and beats seasonal naive on all four
  folds, but its 2018 score covers only 38 of the 182 evaluation hours: it needs history that
  the Jan–Apr 2018 gap removed before it can forecast. Its fold-mean advantage is not equally
  supported in every fold.
- XGBoost and the P50 quantile model beat seasonal naive on three of four folds; against the
  per-fold best baseline they are significantly better only in July 2017.
- The 2018 fold has 182 evaluable hours across 8 days; treat it as indicative, not precise.
- No model is uniformly best. July favors SARIMA/P50, the Aug fold favors the mean of four
  same weekdays (learned models are not significantly different), and Sep–Dec is difficult for
  every model.

## Models

**XGBoost (point forecast).** Direct day-ahead model with 48 features: target lags 24–47, 168
and 336 h; rolling statistics over hours 24–47; calendar, holiday and semester flags;
n_reporting lagged by 24 h; and Open-Meteo weather variables lagged by 24 h. Hyperparameters
are tuned with Optuna on a time-series split inside each fold's training window; early stopping
uses a train-side validation slice. Labels are clipped with a train-only Q3 + 3·IQR cap.
Feature gains are shown on the Explain page.

**SARIMA.** Order (1,0,1)(0,1,1,24), refit weekly on the trailing 60 days of the gap-handled
target and advanced daily using only actuals available before each origin. A recovery refit
runs after coverage gaps. Prediction intervals are not reported for SARIMA.

**Quantile XGBoost.** Three models with `reg:quantileerror` at 0.1 / 0.5 / 0.9 on the same
features and cap as XGBoost. P10–P90 coverage and pinball loss are reported per fold in
`RESULTS.md`; the interval undercovers in the Sep–Dec fold.

**Baselines.** Persistence (last value before the day, held flat), seasonal naive (same hour
24 h earlier), same hour last week, and the mean of the last four same weekdays.

**Not shipped.** No LSTM/GRU. The legacy `model_results.json` still contains LSTM-era fields
that the EDA page does not surface; the LSTM metrics are marked disabled and no UI path renders
them.

## Upload & Validate

The Upload page accepts a CSV up to 50 MB (streamed; a 256 KB / 100-row preview is read
first), detects or lets the user map the timestamp, value and optional series columns, and
asks for unit (Wh/kWh energy summed per hour, W/kW power averaged per hour), naive timezone,
and timestamp format. Everything is converted to IST, then evaluated with the Phase 3
protocol on a chronological 60/40 split at an IST midnight:

- four Phase 3 baselines,
- a zero-shot campus-trained XGBoost using only upload-available features (target lags and
  calendar; no campus reporting or weather) and a scale factor from the training part only,
- an XGBoost fit on the first 60% with fixed defaults.

The report includes row accounting, gaps, masks, metrics, paired Wilcoxon results, and a JSON
download. Uploads with fewer than 336 valid target hours return a partial validation report
with an explicit reason instead of metrics.

## Dashboard pages

| Page | Content |
|---|---|
| EDA | 2017 aggregate hourly/daily/monthly/yearly profiles and hour×month heatmap |
| Predictions | Four-fold backtest day picker, XGBoost/SARIMA/P50 forecasts, P10–P90 band, error by hour/month, worst days |
| Weekly | Legacy 2017 weekday/weekend profile per model (from `model_results.json`) |
| Model Metrics | Fold mean ± std table and "beats seasonal naive?" column from `/api/backtest/summary` |
| Explain | XGBoost gain importance and per-fold residual plots |
| Data Quality | Raw-file coverage, gaps, stable panel, inactivity flags |
| Limitations | High-level caveats assembled from `data_quality.json` and `results.json` |
| Upload & Validate | CSV validation and fixed-protocol evaluation |

### Two data products

- `backend/results.json` (Phase 3/4 backtest) + `backend/data_quality.json` back the
  Predictions, Model Metrics, Explain, Data Quality, Limitations and Upload pages.
- `backend/model_results.json` is the legacy 2017 single-split aggregate. The EDA and Weekly
  pages still read its `/api/eda/*` and `/api/predictions/*` endpoints; its LSTM fields are
  not displayed anywhere. The two products are not directly comparable.

## API

All data endpoints are served under `/api` and return JSON. Interactive docs at `/docs`.

| Group | Endpoints |
|---|---|
| Backtest | `/api/backtest/summary`, `/days`, `/day?date=`, `/errors` |
| Explain | `/api/explain/importance`, `/residuals?fold=&model=` |
| Data quality | `/api/data_quality`, `/api/limitations` |
| EDA (legacy) | `/api/eda/hourly`, `/daily`, `/monthly`, `/yearly`, `/heatmap`, `/weekday_vs_weekend`, `/statistics` |
| Predictions (legacy) | `/api/predictions/monthly`, `/daily`, `/hourly`, `/weekly_pattern`, `/monthly_errors` |
| Upload | `/api/upload/options`, `POST /preview`, `POST /validate` |

## Repository layout

```
backend/
  main.py                 FastAPI app and response shaping
  data_pipeline.py        raw CSVs → hourly panel → gap-handled target
  build_data_quality.py   data_quality.json
  evaluate.py             folds, baselines, metrics, significance, results.json
  forecast_model.py       XGBoost features/fit, Optuna tuning
  quantile_model.py       quantile XGBoost
  sarima_model.py         rolling weekly-refit SARIMA
  train_models.py         legacy 2017 single-split artifact (model_results.json)
  weather.py              Open-Meteo archive download/cache
  upload_validation.py    upload parse, split, evaluation
  tests/                  pytest suite
  models/                 committed XGBoost/train-stats artifacts
frontend/src/
  pages/                  eight page components
  components/             MetricsBar and shared inline UI
  hooks/useData.js        fetch hook (loading/error/abort)
  utils/api.js            API client
  utils/chartConfig.js    Chart.js defaults and model colors
data/                     raw apartment CSVs (read-only input, never deleted)
notebooks/                original exploration notebooks
```

## Tests

```bash
make test
# or: python -m pytest backend/tests -q
```

The 34 tests cover metric math and guards, the day-ahead split, lag/leakage rules, gap
handling, and upload parsing/aggregation. They use synthetic series only and do not need the
network or the campus CSVs.

## Documentation

- [RESULTS.md](RESULTS.md) — protocol, per-fold metrics, significance, intervals
- [CHECKPOINT_DATA.md](CHECKPOINT_DATA.md) — data-quality checkpoint
- [CHECKPOINT_EVAL.md](CHECKPOINT_EVAL.md) — baseline-only evaluation checkpoint
- [CHECKPOINT_MODELS.md](CHECKPOINT_MODELS.md) — learned-model checkpoint
- [DECISIONS.md](DECISIONS.md) — design decisions and conservatism calls
- [PROGRESS.md](PROGRESS.md) — per-item work log and evidence
- [FINAL_REPORT.md](FINAL_REPORT.md) — summary of the improvement pass

## Limitations

- Four folds only; the 2018 fold has 182 evaluable hours and 38 SARIMA hours.
- The target is a per-reporting-apartment mean over 24 stable apartments; December 2017
  includes suspected vacancies.
- No test-fold tuning or test-window refitting is performed, but the fold set is small, so
  the fold-mean ranking is sensitive to the 2018 fold.
- P10–P90 intervals undercover in Sep–Dec (44.8%) and are only approximately calibrated.
- Weather comes from one Open-Meteo grid point (Mumbai) and is not building-level.
- EDA and Weekly still show the legacy 2017 aggregate and are not the backtest numbers.
