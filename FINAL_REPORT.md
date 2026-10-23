# ElectriCast — Final Report

**Branch:** `improve-electricast` · **Base:** `main` · **Last item commit:** `e64b89c` (7.3)
**Status:** all PLAN items `[x]`, none `[!]` · this report is the final commit
**Artifacts:** `backend/results.json` (2026-10-23T19:30:48+05:30),
`backend/data_quality.json` (2026-10-23T18:10:05+05:30)

All work is committed on `improve-electricast`. `main` was not modified, no history was
rewritten, and nothing was pushed.

## What was done

| Phase | Outcome |
|---|---|
| 0 — Hygiene | Root `.gitignore`; generated files untracked; requirements pinned to installed versions; Docker Python aligned; dead LSTM loader/Radar import removed; legacy notebook moved under `notebooks/legacy/`. |
| 1 — UI truth | Wh/kWh labels corrected; disabled LSTM filtered out of every UI path; Weekly charts moved to XGBoost; yearly chart uses backend daily means; split label computed from statistics; IST label and real dataset header; R² thresholds; layout/print fixes; real day picker; same-origin API, abortable fetches and visible errors. |
| 2 — Data pipeline | All 39 CSVs loaded with explicit error reporting; per-apartment hourly panel with `n_reporting`; UTC/IST normalization for the May-2018 `:00 UTC` files; target = mean load per reporting stable apartment; 24-apartment stable panel (>90%); gaps ≤6 h interpolated, longer/edge runs excluded; train-only Q3+3·IQR cap; December inactivity flags; `data_quality.json` plus Data Quality page. |
| 3 — Evaluation | Four day-ahead baselines; MAE/RMSE/WAPE/MASE/bias/R²/guarded sMAPE; four expanding folds with 00:00 IST origins and a shared evaluation mask; per-fold `results.json`; paired Wilcoxon tests against each fold's best baseline. |
| 4 — Models | Leakage-tested XGBoost with ≥24 h lags, calendar/holiday/semester/`n_reporting` features, cached Open-Meteo weather, Optuna tuning on train-side CV and early stopping; rolling SARIMA(1,0,1)(0,1,1,24) refit weekly on 60 days; quantile XGBoost P10/P50/P90 with coverage and pinball loss; LSTM omitted entirely rather than shown as a placeholder. |
| 5 — Dashboard | Fold mean ± std metrics with “beats seasonal naive?”; fold-based day picker with P10–P90 band, error by hour/month and worst days; XGBoost gain importance and residuals; Limitations panel sourced from backend JSON. |
| 6 — Upload | Column mapping, unit/timezone/format selection, 256 KB preview, streamed 50 MB cap, IST conversion, validation report, 60/40 chronological split, Phase 3 baselines, zero-shot campus model and fit-on-60% model, paired significance, JSON download, progress/error states. |
| 7 — Engineering | 34 pytest tests (metrics, split, leakage, gaps, upload validation); Makefile; Docker fixes (full runtime, `/data` mount, no-curl healthcheck, same-origin nginx, CPU-only XGBoost, no torch); README, RESULTS.md and copilot instructions rewritten for the current product. |

## Baselines vs models

Fold means are unweighted across the folds where each model has data; `n` is total evaluable
hours. Source: `backend/results.json`, reproduced in full in `RESULTS.md`.

| Model | Folds | n | MAE (Wh) | RMSE (Wh) | WAPE % | MASE | R² | Beats seasonal naive |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Persistence | 4 | 3,913 | 154.03 ± 80.60 | 201.74 | 42.19 | 1.710 | −0.917 | 1/4 |
| Seasonal naive 24 h | 4 | 3,913 | 104.10 ± 32.84 | 151.95 | 31.23 | 1.193 | 0.018 | reference |
| Same hour last week | 4 | 3,453 | 189.14 ± 141.73 | 236.34 | 51.07 | 2.079 | −0.850 | 1/4 |
| Mean of 4 same weekdays | 3 | 2,778 | 104.48 ± 56.40 | 131.97 | 41.69 | 1.282 | 0.163 | 1/3 |
| XGBoost | 4 | 3,913 | 104.21 ± 49.89 | 135.88 | 32.70 | 1.204 | 0.227 | 3/4 |
| SARIMA | 4 | 3,080 | 81.07 ± 21.25 | 110.72 | 24.08 | 0.934 | 0.526 | 4/4 |
| Quantile XGBoost (P50) | 4 | 3,913 | 99.91 ± 46.20 | 130.69 | 31.33 | 1.156 | 0.281 | 3/4 |

Per-fold conclusions:

- **Jul 2017** — all three learned models beat the best baseline (seasonal naive) with paired
  p-values from 0.0215 down to 6.4e−05.
- **Aug 2017** — the mean of four same weekdays wins; none of the learned models differs
  significantly from it.
- **Sep–Dec 2017** — persistence is the selected baseline; SARIMA is the only learned model
  with a lower median absolute error (−0.43 Wh, p = 0.0029). XGBoost and P50 are significantly
  worse and carry large positive bias.
- **May–Jun 2018** — 182 evaluable hours over 8 days; SARIMA wins on 38 paired hours
  (p = 0.0253), XGBoost and P50 are not significantly different from seasonal naive.
- **Intervals** — P10–P90 coverage is 71.6% / 78.5% / 44.8% / 69.2% by fold (nominal 80%),
  i.e. undercovered in Sep–Dec. Hour-weighted coverage is 57.45%.

No model is uniformly best. SARIMA has the strongest fold-mean MAE but incomplete coverage;
XGBoost/P50 beat seasonal naive in three folds, but outside July their paired differences
against each fold's best baseline are not significant.

## Blocked items

None. Every PLAN item (0.1–7.3) is marked `[x]`. No item required the `[!]` fallback, and no
dependent item is waiting on another.

## Remaining risks

1. **Small, uneven fold set.** Four folds, one of which (2018) has 182 evaluable hours over
   8 days. Fold-mean rankings are sensitive to that fold and to the 2018 coverage gap.
2. **SARIMA coverage.** It cannot forecast through the Jan–Apr 2018 gap: 96 predicted hours,
   38 scored. Its fold mean is over unequal hours, and it has no reported prediction intervals.
3. **Distribution shift in Sep–Dec.** XGBoost/P50 bias is +111/+93 Wh and interval coverage is
   44.8%. December 2017 has 21 apartments flagged suspect inactive (13 stable), likely
   vacancies; the target can move with reporting counts.
4. **Target definition.** The target is a per-reporting-apartment mean over 24 stable
   apartments, not total building load. It is not comparable to the legacy per-building
   aggregate shown on EDA/Weekly.
5. **Two data products.** EDA and Weekly still read the legacy 2017 single-split
   `model_results.json`; Predictions/Metrics/Explain/Quality/Limitations/Upload read the
   current `results.json`. The UI sources them correctly, but the two are not directly
   comparable and are documented as such.
6. **Weather proxy.** One Open-Meteo grid point (Mumbai), lagged ≥24 h; not building-level and
   not a causal input.
7. **Upload domain shift.** The zero-shot model is trained on campus data and may underperform
   an uploaded series; the report labels it as zero-shot and shows the fit-on-60% alternative.
   Very short uploads (<336 valid hours) return validation only, by design.
8. **Operational surface.** The Docker stack was built and exercised in an isolated Compose
   project (ports 18000/13000) and then removed; the pre-existing stack was left untouched.
   There is no CI pipeline. GNU make is not installed on this Windows host, so Makefile
   recipes were validated command-by-command rather than by invoking `make`.
9. **Frontend testing.** No automated frontend test runner. Pages were browser-verified against
   live backends in earlier phases and the production build passes, but regressions are not
   caught by CI.

## Exact commands

All commands are run from the repository root.

```bash
# Install
python -m pip install -r backend/requirements.txt
(cd frontend && npm ci)

# Develop (two terminals)
(cd backend && python -m uvicorn main:app --reload --port 8000)
(cd frontend && npm run dev)
# Dashboard: http://localhost:3000   API docs: http://localhost:8000/docs

# Quality gates
python -m pytest backend/tests -q          # 34 tests
(cd frontend && npm run build)             # 48 modules

# Rebuild data-quality artifact
python backend/build_data_quality.py       # writes backend/data_quality.json

# Full retrain + four-fold backtest (XGBoost/Optuna, quantile XGBoost, SARIMA)
python backend/evaluate.py                 # writes backend/results.json

# Docker (same-origin SPA, backend on 8000, frontend on 3000)
docker compose up --build
# Override ports if needed:
BACKEND_PORT=18000 FRONTEND_PORT=13000 docker compose up -d --build
```

Equivalent Make targets: `make install`, `make test`, `make build`, `make data-quality`,
`make eval`, `make dev-backend`, `make dev-frontend`, `make docker-up`, `make docker-down`.

## Evidence summary

- `python -m pytest backend/tests -q` → **34 passed** (18.28 s at the 7.3 documentation check).
- `npm run build` → **48 modules**, 398.66 kB (gzip 127.20 kB).
- Docker: isolated build succeeded after removing the unused torch/NCCL stack; backend image
  924 MB; both containers healthy; same-origin `/api` responses matched the backend; a
  7,508-row upload completed (HTTP 200, all baselines + zero-shot + fit-on-60%) and the
  dashboard rendered with no console errors.
- Documentation: every per-fold MAE/RMSE/MASE string in `RESULTS.md` was checked against
  `results.json`; every aggregate MAE ± std in `README.md` matches the backend summary; all
  local links resolve, including this report.

## Where to look

- `RESULTS.md` — protocol, per-fold metrics, significance, interval calibration, caveats.
- `CHECKPOINT_DATA.md`, `CHECKPOINT_EVAL.md`, `CHECKPOINT_MODELS.md` — phase checkpoints.
- `DECISIONS.md` — every conservative choice, including dependencies and data handling.
- `PROGRESS.md` — per-item commands and observed output.
- `README.md` — setup, dataset, models, upload flow, API and limitations.
