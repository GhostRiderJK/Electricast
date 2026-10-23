"""Day-ahead forecast evaluation for ElectriCast.

Baselines forecast every IST hour of a test day using observations strictly
before 00:00 IST of that day. Run from the repo root:

    python backend/evaluate.py
"""
import numpy as np
import pandas as pd

import data_pipeline as dp

BASELINES = (
    "persistence",
    "seasonal_naive_24",
    "same_hour_last_week",
    "mean_last_4_same_weekdays",
)

BASELINE_DESCRIPTIONS = {
    "persistence": "last observed value before the forecast day, held flat for 24 h",
    "seasonal_naive_24": "value at the same hour on the previous day",
    "same_hour_last_week": "value at the same hour one week earlier",
    "mean_last_4_same_weekdays": "mean of the same hour on the previous four same weekdays",
}


def load_target():
    """Return the gap-handled target series (Wh per reporting apartment)."""
    apartments, _ = dp.load_apartments()
    panel, _ = dp.build_panel(apartments)
    stable, _ = dp.stable_apartments(panel)
    target, _ = dp.build_target(panel, stable)
    filled, _, _, _ = dp.fill_short_gaps(target)
    return filled


def test_hours(start, end):
    return pd.date_range(start, end, freq="h", tz=dp.TZ)


def _lag_values(series, hours, lag):
    return series.reindex(hours - pd.Timedelta(hours=lag)).to_numpy(dtype=float)


def baseline_forecasts(series, start, end):
    """Forecast every hour in [start, end] with each baseline.

    The forecast origin for each hour is 00:00 IST of its calendar day. Every
    input timestamp is therefore at least 24 h before the target hour, except
    persistence, which uses the last observation before the origin.
    """
    hours = test_hours(start, end)
    preds = {}

    # Last valid observation before each day's origin, broadcast over the day.
    last_before_origin = series.ffill().shift(1)
    day_starts = pd.date_range(start, end, freq="D", tz=dp.TZ)
    daily_level = last_before_origin.reindex(day_starts)
    preds["persistence"] = pd.Series(
        daily_level.reindex(hours.floor("D")).to_numpy(dtype=float), index=hours
    )

    preds["seasonal_naive_24"] = pd.Series(_lag_values(series, hours, 24), index=hours)
    preds["same_hour_last_week"] = pd.Series(_lag_values(series, hours, 168), index=hours)

    weekly = np.column_stack([_lag_values(series, hours, lag)
                              for lag in (168, 336, 504, 672)])
    complete = ~np.isnan(weekly).any(axis=1)
    mean_4 = np.full(len(hours), np.nan)
    mean_4[complete] = weekly[complete].mean(axis=1)
    preds["mean_last_4_same_weekdays"] = pd.Series(mean_4, index=hours)

    return preds


def main():
    series = load_target()
    start, end = "2017-07-01", "2017-07-31 23:00"
    preds = baseline_forecasts(series, start, end)
    actual = series.reindex(test_hours(start, end))
    print(f"Baselines {start} -> {end}, target mean {actual.mean():.2f} Wh")
    for name in BASELINES:
        pred = preds[name]
        ok = actual.notna() & pred.notna()
        mae = float((pred[ok] - actual[ok]).abs().mean()) if ok.any() else float("nan")
        print(f"  {name:28s} n={int(ok.sum()):5d} MAE={mae:8.2f}")


if __name__ == "__main__":
    main()
