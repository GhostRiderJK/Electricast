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
