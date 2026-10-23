# Progress log

One entry per iteration: date, item id, change, evidence, numbers.

## 2026-10-23 — 0.1 Root .gitignore; untrack generated artifacts

- Added root `.gitignore` covering Python caches, `node_modules/`, `dist/`, `.env`, OS files, and test/coverage output.
- Removed from the Git index (working-tree files kept): `frontend/node_modules/` (2,389 files), `.DS_Store`, `backend/__pycache__/main.cpython-313.pyc`.
- Evidence: `git ls-files` 2,466 → 75 tracked files; `git status --short` no longer lists `node_modules`, `.DS_Store`, or `__pycache__`; the files still exist on disk; `git check-ignore -v` reports the new rules.
- Commit: `0.1: add root gitignore and untrack generated artifacts`.

## 2026-10-23 — 0.2 Pin requirements; align Python versions

- `backend/requirements.txt`: all 9 direct dependencies now exact `==` pins matching the installed environment (fastapi 0.111.0, uvicorn 0.30.1, numpy 2.5.4, python-multipart 0.0.9, pandas 3.1.0, scikit-learn 1.9.1, statsmodels 0.15.0, xgboost 3.4.1, torch 2.14.1).
- `backend/Dockerfile`: `python:3.11-slim` → `python:3.12.10-slim`, matching local Python 3.12.10.
- Evidence: parser + `importlib.metadata` check printed `OK` for all 9 pins and `ALL_PINS_MATCH`; `pip install --dry-run --no-deps -r` reported "Requirement already satisfied" for every line; Docker tag equals `python:{local major.minor.micro}-slim` (`ALIGNED`). Docker image build not run (no cached image; network limited to pip/npm).

## 2026-10-23 — 0.3 Remove dead LSTM loader/imports; move notebook

- Deleted unused `_load_lstm_model()` from `backend/main.py` plus its now-unused `pickle`, `MinMaxScaler`, and `LSTM_WINDOW` symbols (36 lines removed).
- Removed unused `Radar` / `RadialLinearScale` imports and registration from `MetricsPage.jsx`.
- Moved `Template.ipynb` (6,302,153 B) to `notebooks/legacy/Template.ipynb` with `git mv`.
- Evidence: grep for removed symbols returns no hits in runtime code (`LSTM_WINDOW` remains only in `train_models.py` where it is written into stats); backend import + TestClient GETs `/`, `/api/metrics`, `/api/eda/statistics` all returned 200; `npm run build` succeeded (44 modules, built in 1.58s).

## 2026-10-23 — 1.1 Wh/kWh labels corrected

- Replaced every UI `kWh` label with `Wh` (values are Wh): EDAPage stats/title/axis/dataset labels, MetricsBar RMSE/MAE, MetricsPage score badges/titles/table, PredictionsPage subtitles, WeeklyPage chart titles, UploadPage metric/table/chart labels.
- Backend upload `scale_note` now states `Wh` for upload/train means.
- Evidence: `grep -rn kWh frontend/src` → none (only remaining backend hits are the input CSV column name); production bundle rebuilt successfully; TestClient upload of `smart_home_dataset.csv` returned 200 with `scale_note: ... upload mean: 54.8 Wh, train mean: 7400.2 Wh`.

## 2026-10-23 — 1.2 LSTM status filtering and BEST logic

- Backend: `load_results()` injects `status` (`lstm=disabled`, `sarima/xgboost=ok`) into `/api/metrics`; `train_models.py` writes the same statuses for future regenerations.
- Frontend: MetricsBar and MetricsPage show only `status === "ok"` models; BEST values are computed over active models only; non-finite values render N/A; ties mark all tied models. Static LSTM header badge/footer text removed.
- Evidence: TestClient `/api/metrics` → `lstm: status=disabled ... sarima: status=ok ... xgboost: status=ok`; `npm run build` passed (44 modules, 2.00s); live browser at :3000 showed MetricsBar with only SARIMA and XGBoost, Metrics page had no LSTM text and exactly 4 BEST badges, all won by XGBoost (R² 0.8238, RMSE 1968.7, MAE 1461.2, sMAPE 40.33).

## 2026-10-23 — 1.3 WeeklyPage uses XGBoost

- Removed the LSTM dataset from the selected-day profile, switched the all-days overlay and the weekday Actual-vs-model bars to XGBoost, and retitled both charts.
- Evidence: `grep -n "lstm\|LSTM" WeeklyPage.jsx` → no hits; `npm run build` passed (44 modules, 1.56s); live browser at :3000 on Weekly Pattern rendered `MON — AVERAGE 24H LOAD PROFILE (WH)`, `ALL DAYS OVERLAY — XGBOOST PREDICTIONS (WH)`, `AVERAGE DAILY LOAD BY WEEKDAY — ACTUAL VS XGBOOST (WH)` with no LSTM text.

## 2026-10-23 — 1.4 Yearly trend is daily means

- Derived 365 daily means from `data/*.csv` using the existing 2017 pipeline (UTC→IST, hourly sum, mean+3σ cap, zero→NaN linear interpolation, median fill) and added `eda.yearly_daily` to `model_results.json`. No retraining; existing `metrics`/`predictions`/other EDA structures verified identical to HEAD.
- `/api/eda/yearly` now returns `yearly_daily` with no downsample parameter; `train_models.py` emits the same structure for future runs; frontend fetches `/api/eda/yearly` and plots all 365 labels/values (removed `i % 3` and `downsample=24`).
- Numbers: 365 points, first `2017-01-01 = 4909.8 Wh`, last `2017-12-31 = 664.5 Wh`; daily mean 7108.82 Wh equals hourly mean 7108.82 Wh.
- Evidence: TestClient `/api/eda/yearly` → 200, 365 points, no `HH:MM` labels; `grep -rn "i % 3\|downsample"` → none; `npm run build` passed (44 modules, 1.63s); live browser showed `Yearly Load Trend` / `Daily mean electricity consumption trend (Wh)`.

## 2026-10-23 — 1.5 Split label computed from statistics

- PredictionsPage now fetches `/api/eda/statistics` and renders train/test percentages and hour counts from backend data; the hardcoded "80% / 20%" is gone.
- Numbers: 4,344 train / 4,416 test hours → 49.6% / 50.4%.
- Evidence: statistics endpoint returned train 4344, test 4416 (`49.6`, `50.4`); `npm run build` passed; production bundle served at :3100 and the live page rendered `Train / Test split: 49.6% / 50.4% (4,344 / 4,416 h)`.

## 2026-10-23 — 1.6 Timezone and header subtitle

- EDAPage overview now says `timezone: IST (Asia/Kolkata)` with an IIT Bombay fallback dataset name; header subtitle now reads `IIT Bombay Residential Buildings · Energy Forecasting`.
- Evidence: production build contained one `timezone: IST` and no `timezone: UTC`; live page at :3100 showed the new header and IST subtitle (`header: true`, `ist: true`, `utc: false`).

## 2026-10-23 — 1.7 R² color thresholds

- MetricsBar R²: green at ≥0.8, red only when negative, neutral otherwise (was green only >0.85, so the real 0.8238 was shown red).
- UploadPage R² card is red when the uploaded-data score is negative, green otherwise.
- Evidence: live computed styles — XGBoost `0.8238` → `rgb(22,163,74)` green, SARIMA `-1.3261` → `rgb(220,38,38)` red; uploading `smart_home_dataset.csv` through the real file input produced R² `-0.6799` rendered `rgb(220,38,38)`. Build passed (44 modules, 1.51s).

## 2026-10-23 — 1.8 Layout fixes and compact metrics bar

- `MetricsBar` is now a compact single-line card per model (inline R²/RMSE/MAE/sMAPE, description moved to the card `title`); only `status === "ok"` models render and the loading skeleton shrank from 160px to 52px.
- `index.css` adds `min-width: 0` to grid children (chart canvases can no longer widen their track) and a print stylesheet that hides header/footer/buttons, removes shadows/padding, and prevents cards breaking across pages.
- Evidence: production build passed (44 modules, CSS 0.92 kB); built CSS contains one `@media print` block; live page at :3100 measured each metric card at 48px high (previously 160px) with SARIMA −1.3261 red and XGBoost 0.8238 green; `main` scrollWidth 600 = viewport 599 with no overflowing descendants; screenshot confirms compact two-card bar above Dataset Overview.

## 2026-10-23 — 1.9 PredictionsPage render state and real day picker

- Removed the render-time `setSelectedMonth(...)`; the effective month is now `selectedMonth ?? testMonths[0]`, and the hourly fetch keys off that derived value.
- Day options come from the test-period `predDaily.labels` for the selected month (Jul/Aug/Oct/Dec 31, Sep/Nov 30) instead of a fixed 28; if the previous day does not exist in the new month, it clamps to the last available day.
- Evidence: production build passed (44 modules, 1.44s); live at :3100 — Jul options 1–31 default 15; selecting 31 then Sep gives options 1–30 and value 30; network logged `hourly?month=Jul&day=15`, `Jul&day=31`, `Sep&day=30`; `/api/predictions/hourly?month=Sep&day=30` returned 24 hours dated `Sep 30, 2017`; Vite dev build showed only the standard React DevTools message, no state-update-in-render warning.

## 2026-10-23 — 1.10 Same-origin API, abortable requests, visible errors, contrast

- `api.js` defaults to a same-origin base (relative `/api/...`); Vite dev and preview both proxy `/api` to the backend; `VITE_API_URL` still overrides. `get()` now surfaces backend `detail`/`error` messages.
- `useData` creates an `AbortController`, passes its signal to every fetcher, aborts on unmount/dependency change, and ignores abort rejections; all pages plus MetricsBar render a new `DataError` alert on failure.
- Contrast pass: muted text `#9ca3af`→`#4b5563` (2.31–2.54 → 6.87–7.56), green text `#16a34a`→`#15803d` (3.00–3.30 → 4.56–5.02), red small text on tints→`#b91c1c`; chart tick labels darkened in `chartConfig`.
- Evidence: build passed (45 modules, 1.77s); preview at :3101 loaded with all API requests same-origin (`/api/...` on localhost:3101) and zero alerts; computed-style WCAG scan found 0 failures across EDA (48 text nodes), Predictions (36), Weekly (28), Metrics (60), Upload (30); stopping the backend showed `Could not load model metrics: API error 500: /api/metrics` and `Could not load EDA data: API error 500: /api/eda/hourly`; dev StrictMode run recorded aborts for `/api/predictions/{monthly,daily,monthly_errors}` and `/api/eda/statistics`, then refetched successfully with no console warnings.

## 2026-10-23 — 2.1 Raw data loader

- Added `backend/data_pipeline.py` with `load_apartments()`: reads every `data/*.csv`, validates `TS,W1,W2,W3`, parses UTC timestamps, and returns a per-file report of rows and IST/UTC ranges.
- Missing/empty/malformed/wrong-schema files are recorded as failures with their exception type; there is no bare or swallowing `except`.
- Evidence: 39/39 files read, 0 failed, 196,449 rows, range 2016-12-14 15:30 UTC → 2018-06-04 18:00 UTC (2016-12-14 21:00 → 2018-06-04 23:30 IST); a temp-directory test with empty, wrong-column and broken CSV files returned `read_ok=1, failed=3` with `ValueError/ParserError` entries and no crash.

## 2026-10-23 — 2.2 Per-apartment hourly panel

- `apartment_hourly()` sums W1–W3 per row with `min_count=1`, converts UTC to IST, sorts, and resamples to hourly with `sum(min_count=1)`; `build_panel()` combines all 39 apartments and keeps `n_reporting` per hour.
- Evidence: panel is 12,891 hours × 39 apartments (2016-12-14 21:00 → 2018-06-04 23:00 IST); every apartment's non-null hourly count equals its raw row count (no bucket collisions); `n_reporting` ranges 0–39 (median 23; 26 reporting for 4,085 hours); 5,291 hours have zero apartments, reflecting the Dec-2017→May-2018 hole; 2017-11-26 03:00 IST has 39 reporting apartments with mean 82.34 Wh.

## 2026-10-23 — 2.3 May-2018 UTC-offset blocks

- Inspected all 39 files: 187,796 rows are stamped at :30 UTC (= exact IST hours) while 8,653 rows are at :00 UTC; 38 files contribute a May-2018 :00-UTC block (7,460 rows, 2018-05-23 19:00 → 2018-05-31 23:00 UTC). `13.csv` is only 37 rows from Nov 2017.
- Added `ist_hour_index()` (UTC→IST, floor to containing hour) and documented the decision: :00-UTC rows fall at IST :30 and join the containing IST hour; no apartment-hour bucket is duplicated (0 across all files).
- Evidence: after the explicit floor the panel is unchanged (12,891 × 39, max 39 reporting, median 23, 5,291 zero-report hours, checksum 63,669,648.7 Wh).

## 2026-10-23 — 2.4 Stable panel and target

- Added `apartment_coverage`, `stable_apartments`, and `build_target`. Stable window is 2017-05-01→2017-11-30 (the longest dense block); 24/39 apartments clear 90% coverage (90.1–91.5%), 15 are dropped.
- Target is the per-hour mean of reporting stable apartments; `n_reporting` counts them. Numbers: 7,600 non-null target hours of 12,891, mean 335.54 Wh, range 0.14–2,001.12 Wh; manual check at 2017-11-26 03:00 IST gives 24 reporters, mean 123.48 Wh = target. Fold windows have 2,370 usable hours (Sep–Dec 2017) and 214 (May–Jun 2018).

## 2026-10-23 — 2.5 Short-gap interpolation

- Added `MAX_GAP_HOURS = 6` and `fill_short_gaps()`, which records every NaN run, linearly interpolates interior runs of ≤6 h, and marks longer or edge runs in `excluded`; returns `(filled, imputed, excluded, runs)`.
- Evidence: synthetic 48-h series with a 3-h, a 10-h, and two edge gaps → exactly 3 h imputed, 12 h excluded, 4 runs recorded, filled values [10, 11, 12] between neighbours 9 and 13. Real 24-apartment target: 66 gap runs, longest 3,514 h; 83 h imputed, 5,208 h excluded, 7,683 valid hours remain (up from 7,600). Asserted no long/edge gap received a value and no hour is both imputed and excluded.

## 2026-10-23 — 2.6 Train-only outlier cap

- Added `fit_outlier_cap()` (Q3 + 3×IQR, minimum 100 samples) and `apply_outlier_cap()`, which clips only the upper tail and reports how many values were capped; the fitter accepts only the training slice by design.
- Evidence: with a provisional train slice of valid hours before 2017-10-01 (5,543 h), cap = 1,006.72 Wh; full-data cap would have been 1,070.31 Wh. Four hours exceed the cap (max 2,001.12 Wh on 2017-02-05 11:00 IST) and are clipped to 1,006.72; NaNs preserved. Mutating all post-October values to 1e6 leaves the train-fitted cap unchanged.

## 2026-10-23 — 2.7 Suspect-inactive apartments

- Added `apartment_activity()`, which computes each apartment's mean load and reading count for an IST month and flags `suspect_inactive` when the mean is <100 Wh/h with at least 24 readings.
- Evidence: using December 2017 (38/39 apartments reporting; data ends 2017-12-28), 21 apartments are flagged, including 13 of the 24 stable apartments; apartment 13 has no December data and is not flagged, and apartment 11 at 100.50 Wh/h is just above the boundary. Synthetic check confirms 99.9 flagged, 100.0/100.1 not, and a single-reading apartment not flagged.

## 2026-10-23 — 2.8 Data-quality report and page

- Added `build_data_quality.py` (writes committed `backend/data_quality.json`), `GET /api/data_quality`, the **Data Quality** page, and a responsive header fix so the sixth nav item scrolls instead of overflowing the page.
- Evidence: JSON reports 39/39 files, 196,449 rows, 12,891 panel hours, 24 stable apartments, 7,683 valid target hours, 5,208 excluded, 21 flagged inactive; page renders 6 KPI cards, 3 tables (70 rows), and a 498×280 chart with no console errors; backend stopped shows `Could not load data quality: API error 500: /api/data_quality`; body scrollWidth 600 vs viewport 604 after the nav fix. Screenshot capture was unavailable (in-app browser viewport), so verification used DOM/API checks.
- Wrote `CHECKPOINT_DATA.md` with the Phase 2 numbers, fold-window counts, regeneration commands, and remaining data risks.

## 2026-10-23 — 3.1 Baselines

- Added `backend/evaluate.py` with day-ahead baselines: persistence (last valid value before 00:00 IST, held flat), seasonal naive 24 h, same-hour-last-week (168 h), and mean of the same hour on the previous four same weekdays (all four required).
- Evidence: synthetic ramp shows persistence errors 1→24 across a day, seasonal-naive error 24, weekly error 168, four-week mean error 420; constant series yields zero errors; a missing previous day makes seasonal naive NaN while persistence falls back to the last valid value; a missing same weekday makes the four-week mean NaN. On July 2017 (744 h), MAE: persistence 119.56, seasonal naive 75.01, last-week 95.00, four-week mean 86.94 Wh.

## 2026-10-23 — 3.2 Metrics

- Added `compute_metrics()` (RMSE, MAE, WAPE, MASE, bias, R², guarded sMAPE) and `mase_scale()`, which uses the mean absolute 24-h seasonal difference over valid training pairs. Pairs are aligned on timestamps and dropped when actual or prediction is missing.
- Evidence: hand-checked example [10,20,30] vs [12,18,33] gives MAE 2.3333, RMSE 2.3805, WAPE 11.6667%, sMAPE 12.744%, bias 1.0, R² 0.915, MASE 0.4667 (scale 5); perfect forecasts give zeros and R²=1; all-zero actuals give sMAPE 0 with WAPE/R²/MASE null; NaNs reduce n correctly; a ramp has MASE scale 24. July 2017 baseline table: seasonal naive MAE 75.01, R² 0.2375 vs persistence MAE 119.56, R² -0.7352 (the fold-window MASE scale is defined in 3.3).

## 2026-10-23 — 3.3 Day-ahead backtest

- Added `FOLDS`, `PROTOCOL`, `evaluate_fold()` and `run_backtest()`: four expanding folds with train_start fixed at 2017-05-01 — test Jul 2017, Aug 2017, Sep–Dec 2017, and May–Jun 2018. Forecast origin is 00:00 IST each test day; the evaluation mask requires a target and a seasonal-naive-24 forecast, so all models share the same hours within a fold.
- Evidence: eval hours are 744 / 744 / 2,243 / 182; target-valid hours are 744 / 744 / 2,374 / 214. Best baseline by MAE is seasonal naive in Jul (75.01), mean-of-4 in Aug (58.93), persistence in Sep–Dec (116.21) and seasonal naive in May–Jun (132.87). Replacing every value from a test day's origin onward with 1e9 leaves that day's forecasts unchanged for all four baselines (6 sample days); fold boundaries satisfy train_end < test_start and expand monotonically.

## 2026-10-23 — 3.4 Fold results and paired significance

- Extended the backtest to write `backend/results.json`: per fold the train/test windows, MASE scale, all four baseline metrics on the shared evaluation mask, the best baseline, the selection mask and its metrics, and a paired Wilcoxon test of every other baseline against the best one.
- Best baseline by MASE: seasonal naive in Jul 2017 (0.887), mean-of-four-weekdays in Aug 2017 (0.725), persistence in Sep–Dec 2017 (1.292 on the 1,290-h four-baseline mask), seasonal naive in May–Jun 2018 (1.294). The four-week mean has no usable 2018 hours (all four same-weekday lags fall in the coverage gap), so it is reported as `status: no_data` with null metrics rather than omitted.
- Paired tests: Jul — best beats all three others (p ≤ 0.0031); Aug — p ≤ 2.9e-9; Sep–Dec — seasonal naive's median absolute error is 0.90 Wh lower than persistence but not significant (n = 2,243, p = 0.4068), while the other two are significantly worse; May–Jun — best beats persistence (n = 182, p = 2.0e-13) and last-week (n = 38, p = 4.8e-8).
- Edge cases verified: identical predictions → `n_pairs=30`, `reason="all paired differences are zero"`; a model with a uniform 0.5-Wh-lower absolute error over 30 pairs → `model_better=True`, p = 4.3e-8; 5 pairs → `small_sample=True`; disjoint indexes → `n_pairs=0`, `reason="no paired hours"`. A schema assertion checks all four fold ids, the nine metric keys per model, the paired keys, and that every float in the file is finite.
- Wrote `CHECKPOINT_EVAL.md` with the protocol, fold table, selection rules, and limitations.

## 2026-10-23 — 4.1 XGBoost day-ahead model

- Added `backend/forecast_model.py`: one pooled direct model per fold on `lag_24`…`lag_47`, `lag_168`, `lag_336`, four aggregates of the 24–47 h block, and hour of day. Every feature is at least 24 h old, so no feature reads the forecast day. Models are fit on the fold's training labels only; labels are clipped at the train-only Q3+3×IQR cap, and negative outputs are clipped to 0.
- Added `backend/tests/test_leakage.py` with five tests (pytest 8.4.2, newly pinned in `requirements.txt`): all lags are ≥24 h; the feature frame for a test day is unchanged when every value from that day's origin onward is replaced with 1e9; all four baselines are unchanged under the same mutation; XGBoost predictions are unchanged; and training labels end before the test day. `python -m pytest backend/tests -q` → 5 passed.
- Backtest (same four folds and evaluation mask): XGBoost MAE 65.95 in Jul (best baseline 75.01; paired median −6.85 Wh, p = 6.5e-05), 62.35 in Aug (best mean-of-4 58.93; +0.78 Wh, p = 0.168), 151.01 in Sep–Dec (persistence 116.21; +10.07 Wh, p = 2.2e-16), and 142.59 in May–Jun (seasonal naive 132.87; +11.69 Wh, p = 0.254). The first learned model beats the best baseline significantly only in the July fold; the autumn fold has a +69.88 Wh bias after training on May–Aug.
- `backend/results.json` now records the XGBoost metrics, fit metadata (`n_train`, cap, number capped, params, feature list), and its paired comparison in every fold.

## 2026-10-23 — 4.2 Calendar, holiday, semester and reporting features

- Extended `make_features()` with day of week, weekend, month, day-of-year sine/cosine, a holiday flag, a semester-in-session flag, and two reporting-count features lagged 24 h (`n_reporting_lag_24` and the mean of the 24–47 h block). `evaluate.py` now loads the stable-apartment reporting count and passes it through fit/predict; baseline forecasts and the evaluation mask are unchanged.
- Holiday list covers the data period (2016-12-25 through 2018-04-30) with major national holidays and festivals; the semester rule is Jan–Apr and Jul–Nov in session, May–Jun and Dec breaks. Both are documented approximations, not authoritative calendars.
- Leakage tests grew to 8: reporting features and XGBoost predictions stay unchanged when reporting counts from the forecast day are replaced, and holiday/weekend/semester flags land on the expected dates. `python -m pytest backend/tests -q` → 8 passed.
- Backtest: MAE 66.46 Jul (was 65.95; still beats seasonal 75.01, p = 6.1e-04), 61.55 Aug (was 62.35; 2.6 Wh behind mean-of-4, p = 0.402), 163.22 Sep–Dec (was 151.01; 47 Wh behind persistence, p = 1.6e-20), 100.40 May–Jun (was 142.59; now beats seasonal 132.87, p = 0.023). Calendar features help the year-later fold and hurt the unseen-autumn fold. The feature set is frozen here; any tuning happens on train-side CV in 4.4, not on these test folds.

## 2026-10-23 — 4.3 Open-Meteo weather features

- Added `backend/weather.py` and committed `backend/weather_mumbai.csv`: 11,688 IST hours from 2017-03-01 to 2018-06-30, six variables (temperature, relative humidity, apparent temperature, precipitation, cloud cover, wind), zero missing values, for IIT Bombay (19.1334 N, 72.9133 E) per the dataset provenance. Fetching is explicit (`python backend/weather.py`); `evaluate.py` reads only the cache, so backtests run offline.
- Weather enters the model only as lags ≥24 h: six same-hour-previous-day values, the 24–47 h mean temperature, and the 24–47 h precipitation sum. Target-hour weather would not be known at the day-ahead origin, so it is never used.
- Leakage tests grew to 10: weather feature frames and XGBoost predictions stay unchanged when weather from the forecast day is replaced. `python -m pytest backend/tests -q` → 10 passed.
- Backtest: MAE 65.69 Jul (best baseline 75.01, p = 5.6e-05), 62.24 Aug (mean-of-4 58.93, p = 0.105), 170.40 Sep–Dec (persistence 116.21, p = 1.2e-23), 106.47 May–Jun (seasonal 132.87, p = 0.254). Weather slightly helps July and hurts Sep–Dec; features stay in place and 4.4 tunes only on train-side CV.

## 2026-10-23 — 4.4 Optuna tuning and early stopping

- Added `time_series_splits()`, `tune()` and `_fit_tuned()`: 30 Optuna TPE trials per fold (seed 42) scored on three expanding-window CV splits inside the fold's training window; validation blocks are contiguous, non-overlapping, and end at the last training day. Early stopping (patience 25) runs on those train-side slices, and the final tree count is the median best iteration before refitting on all training labels. Optuna 5.0.0 is pinned in `requirements.txt`.
- Tests grew to 12: CV splits stay inside the training window and never overlap, and a tuned forecast is unchanged when every value from the test-day origin onward is replaced. `python -m pytest backend/tests -q` → 12 passed (19 s).
- Tuned backtest: XGBoost MAE 69.31 Jul (best baseline 75.01, p = 0.0215), 59.51 Aug (mean-of-4 58.93, p = 0.844), 167.27 Sep–Dec (persistence 116.21, p = 2.3e-22), 120.75 May–Jun (seasonal 132.87, p = 0.518). Tuning improved Aug (62.24 → 59.51) but worsened Jul (65.69 → 69.31) and May–Jun (106.47 → 120.75); the tuned model significantly beats the best baseline only in July.
- Wrote `CHECKPOINT_MODELS.md` with the feature set, tuning table, fold results, iteration history, leakage evidence, and limitations.








## 2026-10-23 — 4.5 Rolling SARIMA with weekly refit

- Added `backend/sarima_model.py` and registered `sarima` as a second learned model in `evaluate.py`. The model is SARIMA(1,0,1)(0,1,1,24) on the gap-handled target, refit on Mondays, the first test day, and after a coverage gap from the trailing 60 days (1,440 h) of contiguous history ending one hour before the origin. Within a week its state is advanced with actuals up to each day's origin, never with forecast-day values. A refit needs 7 contiguous days, forecasts are skipped when the state is more than 48 h stale, and negative forecasts are clipped to zero.
- Why the two guards: with the original 14-day minimum plus no staleness limit, the 2018 fold had no forecasts at all; lowering the minimum alone let a five-month-stale state emit 214 hours at MAE 249.5 Wh. The 7-day minimum plus the 48 h staleness limit yields a small but genuine 2018 forecast (96 h predicted, 38 h evaluable) instead of either nothing or a misleading full fold.
- Full backtest, evaluation mask (SARIMA hours in parentheses): SARIMA MAE 65.66 Wh in Jul (744 h; best baseline seasonal naive 75.01; paired median −6.61 Wh, p = 1.2e-04), 60.60 in Aug (744 h; mean-of-4 58.93; +0.42 Wh, p = 0.830), 104.23 in Sep–Dec (1,554 of 2,243 h; persistence 116.21; −0.43 Wh, p = 2.9e-03), and 93.80 in May–Jun (38 of 182 h; seasonal naive 132.87; −9.36 Wh, p = 0.025). XGBoost stays at 69.31 / 59.51 / 167.27 / 120.75 Wh. SARIMA is the stronger learned model in three folds, but its Sep–Dec advantage is a near-tie on the median and its 2018 sample is only 38 hours.
- Coverage is a real limitation: the Sep–Dec fold has 689 evaluable hours without a SARIMA forecast because the target gaps outrun the state, and the 2018 fold has 144. Metrics use each model's available hours, as with the lagged baselines; paired tests use overlapping hours, and coverage is recorded in `results.json`.
- Tests grew to 15: contiguous history stops at the last gap and rejects runs shorter than the minimum; SARIMA predictions are unchanged when every value from the forecast-day origin onward is replaced; a state older than 48 h emits no forecasts. `python -m pytest backend/tests -q` → 15 passed (19 s).
- Regenerated `backend/results.json` (now includes `sarima` metrics and fit metadata) and updated `CHECKPOINT_MODELS.md` through item 4.5.

## 2026-10-23 — 4.6 Quantile XGBoost P10/P50/P90

- Added `backend/quantile_model.py`: three XGBoost models with objective `reg:quantileerror` and alphas 0.1/0.5/0.9, sharing the point model's feature set, 24 h+ lags, training window, and train-only outlier cap. Hyperparameters are the fixed 4.1 defaults (400 trees, depth 4, learning rate 0.03), untuned. Predictions are clipped at zero and sorted row-wise when raw quantiles cross (zero crossings in Jul–Sep, one row in May–Jun); the P50 is also scored as a point forecast on the shared evaluation mask.
- Added `interval_metrics()` (P10–P90 coverage, mean width, pinball loss at P10/P50/P90 and their mean) and an `intervals` block to every fold in `results.json`. Protocol and learned-model descriptions were extended; no baseline, mask, or selection rule changed.
- Point results for the quantile P50: MAE 65.99 Wh in Jul (744 h; paired median −7.25 Wh vs seasonal naive, p = 6.4e-05), 60.58 in Aug (744 h; 0.00 Wh median, p = 0.607), 159.14 in Sep–Dec (2,243 h; +10.92 Wh, p = 2.5e-19), and 113.94 in May–Jun (182 h; −3.52 Wh, p = 0.309). It is better than the tuned point XGBoost in three folds but remains 43 Wh behind persistence in the shifted autumn fold.
- Interval quality: 80% nominal coverage came out at 71.6% (Jul), 78.5% (Aug), 44.8% (Sep–Dec), and 69.2% (May–Jun), with mean widths 177 / 177 / 211 / 229 Wh and mean pinball losses 21.73 / 19.87 / 61.88 / 35.25 Wh. The autumn fold is badly undercovered because the training window contains no autumn regime; this is reported as a limitation rather than fixed with test data.
- Tests grew to 17: a hand-checked coverage/pinball example (including a missed interval) and a quantile leakage test (predictions unchanged under forecast-day mutation, P10 ≤ P50 ≤ P90, no NaNs). `python -m pytest backend/tests -q` → 17 passed (18 s).
- Regenerated `backend/results.json` and updated `CHECKPOINT_MODELS.md` through item 4.6.

## 2026-10-23 — 4.7 Omit LSTM/GRU from the UI

- Took the "omitted entirely" branch: there is no trained LSTM or GRU artifact, only zero-filled placeholder data, so presenting it as a model would violate the no-placeholder rule. Training a proper deep model would need its own leakage-safe protocol and was out of scope for this item.
- Removed the remaining LSTM surfaces: MetricsBar model config/active list, MetricsPage model list, PredictionsPage model colors, visibility toggles, line datasets, monthly MAE/RMSE series, chartConfig color/meta entries, and the EDA heatmap copy that referenced LSTM window design. `grep -ri "lstm\|gru" frontend/src` → no matches.
- Evidence: `npm run build` passed (46 modules, 1.99 s). A fresh Vite server on :3005 pointed at the current backend on 127.0.0.1:8000 (the pre-existing :3000 preview and 0.0.0.0:8000 server were stale and left untouched) showed: Metrics page with only SARIMA and XGBoost and all four BEST badges on XGBoost; Predictions with Actual/SARIMA/XGBoost toggles and five canvases; Weekly with XGBoost-only overlay captions; no LSTM/GRU text on EDA, Predictions, Weekly, or Metrics.
- Backend response keys are unchanged for schema compatibility (LSTM remains `status: disabled`), but no UI path reads them. README and copilot instructions still describe LSTM and will be corrected in 7.3.

## 2026-10-23 — 5.1 Fold-level metrics in the dashboard

- Added `/api/backtest/summary` in `backend/main.py`, built at startup from the committed `backend/results.json`. It reports every baseline and learned model with per-fold metrics, an unweighted fold mean and sample standard deviation (ddof=1), the per-fold n, and a descriptive majority answer to "lower MAE than seasonal naive". The endpoint returns 503 with an explicit message when the backtest artifact is missing.
- Replaced the single-split `MetricsPage` with a four-fold view: protocol fields from the backend, fold chips with evaluation hours, a mean ± std table (MAE, RMSE, MASE, beats-naive, fold count) and a per-fold MAE table with n. The old score badges and four bar charts were removed because they mixed one split with no fold variability. `MetricsBar` now reads the same summary and shows all three learned models with their fold mean and MAE σ.
- All numbers come from the endpoint; no result is written into JSX. The page labels the beats column as a descriptive majority rule and points to the paired Wilcoxon output for significance.
- Evidence: live backend on 127.0.0.1:8010 returned 7 models and 4 folds; the endpoint's means match `results.json` (SARIMA MAE 81.1 ± 21.3, beats 4/4; XGBoost 104.2 ± 49.9, 3/4; quantile P50 99.9 ± 46.2, 3/4). A fresh Vite server on :3007 proxying that backend rendered both tables (14 rows) and the metrics bar with no console errors; the initial protocol-object render error found during this check was fixed before the build. `npm run build` passed (46 modules, 1.57 s).

## 2026-10-23 — 5.2 Fold-based Predictions page

- Extended `backend/evaluate.py` to persist the hourly evaluation rows in each fold of `results.json`: local IST timestamp, actual, seasonal-naive reference, point XGBoost, SARIMA, and quantile P10/P50/P90. Rows are limited to the existing evaluation mask (actual and seasonal-naive available), so no new data is exposed. The regenerated artifact holds 3,913 rows (744 / 744 / 2,243 / 182) and reproduces the earlier metrics exactly (SARIMA MAE 65.66 / 60.60 / 104.23 / 93.80 Wh; same coverage and pinball values).
- Added backend endpoints built once at startup: `/api/backtest/days` (folds and evaluable days), `/api/backtest/day?date=` (24-slot arrays for actual, seasonal naive, XGBoost, SARIMA, P10/P50/P90 plus per-model day MAE and n), and `/api/backtest/errors` (MAE by hour of day, MAE by calendar month, and top-10 worst days ranked by XGBoost MAE with at least 12 evaluable hours). Endpoints return 503 when the hourly artifact is missing.
- Rebuilt `PredictionsPage` around the backtest: fold chips plus a dated day picker, a day chart with the P10–P90 band and model toggles, per-model day MAE cards, MAE-by-hour and MAE-by-month bar charts, and the worst-days table with per-model n tooltips. The old single-split monthly/daily charts were removed from this page so it no longer mixes protocols; `WeeklyPage` and the legacy `/api/predictions/*` endpoints are unchanged.
- Evidence: live backend on 127.0.0.1:8011 returned 4 folds with 31 / 31 / 102 / 8 evaluable days, a 24-hour Jul 1 payload with ordered quantiles, and 10 worst-days rows. A fresh Vite server on :3009 rendered 3 canvases and the table; switching to Sep–Dec and to the 14-hour 2018-06-01 day updated the picker and showed SARIMA n=14; the SARIMA toggle changed state; no console errors. `npm run build` passed (46 modules, 1.44 s).

## 2026-10-23 — 5.3 Explain page

- Chose XGBoost gain importance rather than SHAP: the trained boosters already expose per-feature total split gain, so no retraining and no new dependency are needed. `_gain_importance()` now persists `{method, features:[{feature, gain, share}]}` in each fold's `model_fit.xgboost` block inside `backend/results.json`. Importances come from the fold's training window only; the top features are `lag_24` in all folds (share 0.314 / 0.274 / 0.177 / 0.159) and `month`, `doy_cos` rise in the 2018 fold.
- Added `/api/explain/importance` (four folds, 48 features each, 503 when the artifact or block is missing) and `/api/explain/residuals?fold=&model=` for `xgboost`, `sarima`, and `p50`. The residual endpoint returns `summary {n, mean_residual_wh, mae_wh, rmse_wh}`, predicted-vs-residual points, 24 hour buckets, and a 20-bin histogram, all derived from the existing hourly backtest rows; residual is actual − forecast, restricted to hours where both the actual and that model's forecast exist.
- New `ExplainPage` with fold chips, model chips, and four charts: top-14 gain importance, residual vs predicted with a zero line, mean residual/MAE by hour, and residual distribution. The page states that gain is descriptive and not causal, that correlated lags can share credit, and that SARIMA covers fewer hours after long gaps. Nav entry added after Model Metrics; no placeholder or client-side metric is displayed.
- Evidence: live backend on 127.0.0.1:8012 returned 4 folds × 48 features and residuals matching `results.json`: Jul XGBoost n=744, MAE 69.31 Wh, bias −5.14, RMSE 90.53; SARIMA n=744, MAE 65.66, bias −7.89, RMSE 87.7; P50 n=744, MAE 65.99, bias +1.48. A fresh Vite server on :3011 rendered the page with 4 canvases; switching to SARIMA kept n=744 and switching the fold to May–Jun 2018 showed 38 hours; no console errors. `npm run build` passed (47 modules, 381.91 kB).

## 2026-10-23 — 5.4 Limitations panel

- Added `/api/limitations`, which assembles the data, evaluation, and model caveats from `backend/data_quality.json` and `backend/results.json` at request time. It returns three groups (5 data items, 4 protocol items, 6 model items), a per-fold coverage table, eight scope caveats, and the artifact sources; no count or coverage value is written into the frontend.
- The new Limitations page (`frontend/src/pages/LimitationsPage.jsx`, nav entry after Data Quality) shows a "read before quoting" banner, severity-tagged limitation cards (high / medium / context), a fold table with evaluable hours, training labels, SARIMA hours, and P10–P90 coverage, and the "what this does not establish" caveat grid. The page covers the 3,514 h target gap, the 182-hour 2018 fold, SARIMA's 3,080/3,913 h coverage, interval undercoverage, zero-reporting hours, and suspect inactivity, with links to the artifacts in the footer.
- Evidence: live backend on 127.0.0.1:8013 returned groups with 5/4/6 items, 4 folds, and 8 caveats. Values match the artifacts: 3,913 evaluable hours / 172 days, SARIMA 3,080 h (744 / 744 / 1,554 / 38), P10–P90 coverage 71.6% / 78.5% / 44.8% / 69.2%, 7,683 valid target hours, 5,208 excluded hours in 31 runs, 24 of 39 stable apartments, 21 inactivity flags, and 11,688 cached weather hours. A fresh Vite server on :3012 rendered all three groups, the four-row fold table, and eight caveats; no console errors. `npm run build` passed (48 modules, 388.20 kB). `pytest backend/tests -q` → 17 passed.
- Also removed the stale "LSTM · SARIMA · XGBoost" phrase from the FastAPI description, since no LSTM is shipped or shown; the disabled legacy response keys remain for schema compatibility.

## 2026-10-23 — 6.1–6.3 Upload validation redesign

- Replaced the old fixed-schema upload with `backend/upload_validation.py` and three endpoints: `GET /api/upload/options`, `POST /api/upload/preview` (first 256 KB / 100 rows), and `POST /api/upload/validate` (streamed, 50 MB cap). The UI now previews column suggestions before sending the full file, then exposes timestamp, value, optional series, unit, naive-timezone, and timestamp-format selectors with a sample table.
- Parsing: epoch seconds/milliseconds, ISO strings with embedded offsets, and naive timestamps localized with the chosen timezone are all converted to IST. Energy units (Wh/kWh) are summed within each series-hour and power units (W/kW) are averaged, then converted to Wh; the target is the mean across reporting series. Timestamps, values, negatives, series coverage, short-gap interpolation, excluded runs, and aggregation are all reported back. A failed parse returns the same validation report alongside the error.
- Evaluation reuses the Phase 3 functions: the first 60% of valid target hours trains, the test period starts at 00:00 IST of the day containing the 60th-percentile hour, the four baselines come from `evaluate.baseline_forecasts`, and all models share the actual + seasonal-naive evaluation mask, MASE scale, and paired Wilcoxon treatment. The fit-on-60% XGBoost uses the fixed 4.1 defaults, a train-only outlier cap, and only >=24 h lag/calendar features. The zero-shot model is a campus-trained XGBoost using only target lags and calendar features that exist on an upload (no campus reporting or weather), scale-aligned by the training-part mean only; no test-window label is read.
- Evidence on `smart_home_dataset.csv`: 48,972 rows used, 34,321 valid target hours (100% of span), split 20,587 train / 13,734 test hours over 573 days. Best baseline mean-of-4-weekdays MAE 35,984.8 Wh; zero-shot 37,104.1 Wh (worse, p=7.3e-10); fit-on-60% 27,587.3 Wh (better, p=0.0e+0); runtime 4.2 s. Multi-series check: 1,600 rows / 2 series aggregated to a 2,000 Wh target mean. Power check: 1,600 W readings averaged to 500 Wh with 799 same-hour readings merged. Row-accounting check: 60 raw rows → 58 used, 1 bad value + 1 negative, with the two-hour interior gap interpolated and reported.
- 6.3 states: uppercase `.CSV` accepted; client and backend both reject a 51 MB file (HTTP 400 / "File too large"); non-CSV rejected; upload progress and "Validating and evaluating…" shown; a 60-hour series returns a 200 partial report with "Evaluation not available — need at least 336 valid target hours, found 60"; results render from backend JSON with one daily chart, notes, and a 66.7 KB JSON download. The report itself carries the split, row counts, masks, and model fit metadata.
- Fixed during verification: pandas 3 string dtype made `dtype == object` false, so naive datetime columns were not suggested as timestamps (now uses `not is_numeric_dtype`); negative rows were double-counted in the dropped-row total (now computed as raw − used); a React warning from mixing `border` and `borderColor` was removed; zero-shot training was made feature-consistent with inference by dropping campus-only reporting features.
- Verification: live backend on 127.0.0.1:8014 and Vite on :3013; fresh page console showed only Vite/React dev messages; `npm run build` passed (48 modules, 398.66 kB); `python -m pytest backend/tests -q` → 17 passed.
- 6.1, 6.2, and 6.3 share one module, one endpoint set, and one page, so they are committed together; the split is recorded in DECISIONS.md.

## 2026-10-23 — 7.1 Test suite: metrics, split, leakage, gaps

- Added `test_metrics.py`: a fully hand-computed four-pair case (MAE 2.75, RMSE 2.8723, WAPE 11.0, sMAPE 12.1896, bias −0.25, R² 0.934, MASE 1.375), zero-denominator guards (WAPE/R² null, sMAPE 0), missing-pair handling, no-data responses, 24-h MASE scale, and day-ahead persistence/seasonal-naive lags.
- Added `test_gaps.py`: a 3-h interior gap interpolates to 12.5 / 15 / 17.5 and is flagged imputed; a 7-h gap and both edge runs stay missing and are flagged excluded; configured limits are honored; run lengths/edges/timestamps are reported.
- Added `test_split.py`: a 40-day synthetic series splits 576 train / 384 test hours at 2020-01-25 00:00 IST with a contiguous train end; an off-midnight start is floored to the day; a 10-day series returns the explicit 336-hour reason with no model or split payload. The upload model trainers are stubbed, so these tests exercise the split without training.
- Added `test_upload_validation.py`: regression for pandas 3 string dtypes (naive datetime columns must still be suggested as timestamps), epoch/unit suggestions, agreement of naive UTC / embedded-offset / epoch timestamps in IST, energy-sum vs power-mean aggregation with a per-hour series mean, and single counting of invalid vs negative rows.
- The new timestamp-offset regex has no capture group, removing the pandas match-group warning seen on every upload parse.
- Evidence: `python -m pytest backend/tests -q` → 34 passed in 15.19 s (was 17). The suite uses synthetic series only and does not read campus artifacts, the network, or the data directory.

## 2026-10-23 — 7.2 Makefile and Docker packaging

- Added a root `Makefile` with `help`, `install`, `test`, `eval`, `data-quality`, `build`, `dev-backend`, `dev-frontend`, `docker-build`, `docker-up`, and `docker-down`. GNU make is not installed on this Windows host, so the file's target/recipe structure was checked and every wrapped command was validated directly: `pytest` → 34 passed, `npm run build` → 48 modules / 398.66 kB, `npm ci --dry-run` → lockfile current, `pip install --dry-run -r backend/requirements.txt` → satisfied, and the Docker build/up/down sequence below.
- Backend image now copies the full runtime (`COPY . .`) instead of only `main.py` and `train_models.py`; `.dockerignore` excludes tests and caches. The built image contains `upload_validation.py`, `data_pipeline.py`, `evaluate.py`, `forecast_model.py`, `quantile_model.py`, `sarima_model.py`, `weather.py`, the weather cache, all three JSON artifacts, and `models/{train_stats,xgb_feature_cols,xgboost_model}.json`. Compose mounts `./data` read-only at `/data` (39 CSVs visible), which the zero-shot upload model needs, and drops the unused `smart-home-dataset-main` mount.
- Healthcheck now uses `python -c "urllib.request.urlopen(...)"` because the slim image has no curl; the frontend waits on `condition: service_healthy`. The runtime `VITE_API_URL=http://backend:8000` was removed because Vite reads env at build time; the built SPA uses same-origin `/api/`, which nginx proxies to `backend:8000`. Ports are overridable (`BACKEND_PORT`, `FRONTEND_PORT`) for isolated verification.
- Removed `torch==2.14.1`: its only import is inside the commented-out legacy LSTM. On Linux, `xgboost==3.4.1` hard-depends on a 305 MB `nvidia-nccl-cu13` wheel that this CPU-only service never uses and whose download timed out; requirements now install `xgboost-cpu==3.4.1` on Linux and keep the regular wheel elsewhere. Docker pip now uses a BuildKit cache mount with 10 retries and a 120 s timeout.
- Evidence: first build failed only at the NCCL download (`ReadTimeoutError` from files.pythonhosted.org, exit 2); after the dependency change, an isolated `docker compose -p electricast72` build succeeded with no errors. Backend image is 924 MB (down from 10.4 GB) and the container reports `xgboost 3.4.1` from `xgboost-cpu`, with no torch or nvidia packages. Both containers came up with backend `healthy`; `localhost:18000/` returned `data_loaded: true`, `localhost:13000/` served the SPA, and the same-origin `localhost:13000/api/backtest/summary` and `/api/upload/options` returned the same 4-fold payload and unit options as the backend. A 7,508-row `data/1.csv` upload through nginx returned HTTP 200 in 3.2 s with all four baselines, zero-shot status ok (MAE 131.6 Wh, scale 2.01), fit-on-60% ok (MAE 84.6 Wh), and best baseline persistence; the browser rendered the dashboard through port 13000 with no console messages. The isolated containers and images were removed afterward, and the pre-existing `electricast-*` stack was left untouched.
