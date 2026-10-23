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
