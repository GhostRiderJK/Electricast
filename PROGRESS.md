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
