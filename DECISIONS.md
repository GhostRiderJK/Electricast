# Decisions log

One line per ambiguous choice; the more conservative option wins.

- 0.1: `data/` is deliberately **not** ignored — the 39 raw apartment CSVs are tracked project inputs and the rules forbid deleting them. `.gitignore` only covers generated artifacts and secrets.
- 0.1: `.env.example` stays un-ignored (`!.env.example`) so configuration can be documented without tracking real secrets.
- 0.2: `torch` is pinned as `2.14.1` without the local `+cpu` suffix; wheel variants are platform-specific and the plain pin resolves to the installed version on this host.
- 0.2: Docker base is the exact `python:3.12.10-slim` tag to match local Python 3.12.10. The image was not built because no Python image was cached and network use is limited to pip/npm.
- 1.1: Kept stored/displayed values in Wh and corrected labels rather than dividing every series and metric by 1000; this follows the Wh-internal rule with a smaller, auditable diff.
- 1.1: The upload CSV input column name `Energy Consumption (kWh)` is left unchanged because it is the schema of the provided dataset; its numeric values are still treated as Wh downstream (pre-existing behavior, revisited in Phase 6).
- 1.2: Model availability is expressed by a backend `status` field (`ok` / `disabled`); the stored LSTM placeholder rows remain in `model_results.json` but every metrics UI path filters on `status === "ok"`.
- 1.2: BEST ties are marked on all tied models; if no active model has a finite metric, the value renders as N/A and no badge is shown.
- 1.4: Daily means were derived from the raw CSVs with the existing 2017 cleaning pipeline and written into `model_results.json` as `eda.yearly_daily`; no model was retrained and all existing metrics/prediction arrays were verified byte-identical after the JSON update.
- 1.4: `/api/eda/yearly` returns daily means by default and falls back to the legacy sampled `eda.yearly` series if an older results file is loaded.
- 1.5: The split label shows percentages computed from `statistics.train_hours`/`test_hours` plus the raw hour counts, so the label is auditable; it renders "loading…" until statistics arrive rather than guessing.
- 1.7: R² uses a green threshold of 0.8 and red only for negative values; 0–0.8 stays neutral because no documented target exists, and coloring a merely modest score red would overstate failure.
- 1.9: The selected month/day are derived from fetched data (`selectedMonth ?? first test month`, day list from `predDaily` labels) instead of writing state during render; switching to a shorter month clamps an out-of-range day to that month's last available day.
- 1.10: The API base now defaults to same-origin (`""`); Vite dev and preview proxy `/api` to `http://localhost:8000`, and `VITE_API_URL` remains the override for split-origin deployments.
- 1.10: Muted text moved from `#9ca3af`/`#6b7280` to `#4b5563`, and small green/red accent text to `#15803d`/`#b91c1c`; chart series keep `#16a34a`/`#dc2626` because graphical elements only need 3:1.
- 1.10: Pages with several data hooks show one alert for the first failure instead of stacking duplicate banners; MetricsBar has its own alert because it renders outside page content.
- 2.3: Raw `TS` values are UTC epoch seconds, but 187,796 of 196,449 rows sit at :30 UTC (exactly on IST hours) while 8,653 rows — including all 38 May-2018 blocks — sit at :00 UTC and land at IST :30. We convert to IST and floor each stamp to its containing hour, so the :00-UTC block joins the IST hour it falls in; no apartment-hour bucket is duplicated (verified 0), and the blocks are separated by months, so no double counting.
- 2.4: The stable panel is evaluated on the longest dense block, 2017-05-01→2017-11-30 (5,136 hours): 24 of 39 apartments have ≥90% hourly coverage there (90.1–91.5%) and the other 15 are excluded. No window longer than this reaches 90% for any apartment (2017 max 79.7%, full range 58.2%).
- 2.4: `target_wh` is the mean of the reporting stable apartments in each hour and `n_reporting` counts those apartments; hours with zero stable reporters stay NaN rather than being filled. The fold windows retain 2,370 usable hours for Sep–Dec 2017 and 214 for May–Jun 2018.
- 2.5: Interior NaN runs of at most 6 h are linearly interpolated and flagged in `imputed`; longer runs and runs touching either end of the series are flagged in `excluded` and left NaN. Interpolated hours are usable for training, excluded hours are dropped from both training and evaluation (including lag/feature construction).
- 2.6: The outlier cap is Q3 + 3×IQR of the training-window target values (minimum 100 samples), clipped on the upper tail only after fitting; the fitter is always passed the training slice, never validation/test values.
