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

FOLDS = (
    {
        "id": "2017-07",
        "train_start": "2017-05-01 00:00",
        "train_end": "2017-06-30 23:00",
        "test_start": "2017-07-01 00:00",
        "test_end": "2017-07-31 23:00",
    },
    {
        "id": "2017-08",
        "train_start": "2017-05-01 00:00",
        "train_end": "2017-07-31 23:00",
        "test_start": "2017-08-01 00:00",
        "test_end": "2017-08-31 23:00",
    },
    {
        "id": "2017-09_12",
        "train_start": "2017-05-01 00:00",
        "train_end": "2017-08-31 23:00",
        "test_start": "2017-09-01 00:00",
        "test_end": "2017-12-31 23:00",
    },
    {
        "id": "2018-05_06",
        "train_start": "2017-05-01 00:00",
        "train_end": "2017-12-31 23:00",
        "test_start": "2018-05-01 00:00",
        "test_end": "2018-06-04 23:00",
    },
)

PROTOCOL = {
    "timezone": dp.TZ,
    "target": "mean hourly load per reporting stable apartment (Wh)",
    "forecast": "24 hourly values for every test day",
    "origin": "00:00 IST of the test day",
    "information_set": "target observations strictly before the origin; lag baselines use >=24 h lags",
    "folds": "expanding window with train_start fixed at 2017-05-01; one fold tests Sep-Dec 2017 and one tests May-Jun 2018",
    "evaluation_mask": "target present and seasonal_naive_24 available",
    "mase_scale": "mean absolute 24-h seasonal difference over valid training pairs",
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


def mase_scale(train_series):
    """Mean absolute 24-h seasonal difference over valid training pairs."""
    diffs = (train_series - train_series.shift(24)).abs().dropna()
    return float(diffs.mean()) if len(diffs) else None


def _clean(value, digits=6):
    if value is None or not np.isfinite(value):
        return None
    return round(float(value), digits)


def compute_metrics(actual, pred, scale=None):
    """Metrics over the timestamps where both actual and prediction exist.

    sMAPE is guarded at a zero denominator (the pair contributes 0); WAPE,
    MASE and R² are None when their denominators are zero or missing.
    """
    frame = pd.concat(
        [pd.Series(actual).rename("actual"), pd.Series(pred).rename("pred")],
        axis=1,
    ).dropna()
    if frame.empty:
        return {
            "status": "no_data", "n": 0, "MAE": None, "RMSE": None,
            "WAPE": None, "MASE": None, "bias": None, "R2": None, "sMAPE": None,
        }

    a = frame["actual"].to_numpy(dtype=float)
    p = frame["pred"].to_numpy(dtype=float)
    err = p - a
    abs_err = np.abs(err)

    mae = float(abs_err.mean())
    rmse = float(np.sqrt(np.mean(err ** 2)))
    abs_actual_sum = float(np.abs(a).sum())
    wape = float(abs_err.sum() / abs_actual_sum * 100) if abs_actual_sum > 0 else None

    denom = np.abs(a) + np.abs(p)
    smape_terms = np.divide(2 * abs_err, denom, out=np.zeros_like(abs_err),
                            where=denom > 0)
    smape = float(smape_terms.mean() * 100)

    sst = float(((a - a.mean()) ** 2).sum())
    r2 = float(1 - (err ** 2).sum() / sst) if sst > 0 else None
    mase = float(mae / scale) if scale is not None and scale > 0 else None

    return {
        "status": "ok",
        "n": int(len(a)),
        "MAE": _clean(mae, 4),
        "RMSE": _clean(rmse, 4),
        "WAPE": _clean(wape, 4),
        "MASE": _clean(mase, 4),
        "bias": _clean(float(err.mean()), 4),
        "R2": _clean(r2, 6),
        "sMAPE": _clean(smape, 4),
    }


def evaluate_fold(series, fold):
    """Score all baselines on one day-ahead fold.

    The evaluation mask is every hour with a target value and a seasonal-naive
    forecast, so all models are scored on the same hours within a fold.
    """
    train = series.loc[fold["train_start"]:fold["train_end"]]
    scale = mase_scale(train)
    actual = series.reindex(test_hours(fold["test_start"], fold["test_end"]))
    preds = baseline_forecasts(series, fold["test_start"], fold["test_end"])
    mask = actual.notna() & preds["seasonal_naive_24"].notna()

    models = {}
    for name in BASELINES:
        models[name] = compute_metrics(actual[mask], preds[name][mask], scale)

    return {
        "id": fold["id"],
        "train": {
            "start": fold["train_start"],
            "end": fold["train_end"],
            "hours": int(len(train)),
            "valid_hours": int(train.notna().sum()),
        },
        "test": {
            "start": fold["test_start"],
            "end": fold["test_end"],
            "clock_hours": int(len(actual)),
            "target_valid_hours": int(actual.notna().sum()),
            "eval_hours": int(mask.sum()),
            "eval_days": int(mask.index[mask].floor("D").nunique()),
        },
        "mase_scale": _clean(scale, 4),
        "models": models,
    }


def run_backtest(series):
    return [evaluate_fold(series, fold) for fold in FOLDS]


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


def _show(value, digits=2):
    return "N/A" if value is None else f"{value:.{digits}f}"


def main():
    series = load_target()
    print(f"Day-ahead backtest, {len(FOLDS)} expanding folds, origin 00:00 IST")
    for fold in run_backtest(series):
        test = fold["test"]
        print(f"\n== {fold['id']}: train {fold['train']['hours']} h "
              f"({fold['train']['valid_hours']} valid), test {test['clock_hours']} h "
              f"({test['target_valid_hours']} target), eval {test['eval_hours']} h / "
              f"{test['eval_days']} d, MASE scale {_show(fold['mase_scale'])}")
        print(f"{'model':28s} {'n':>5s} {'MAE':>8s} {'RMSE':>8s} {'WAPE%':>8s} "
              f"{'MASE':>7s} {'bias':>8s} {'R2':>8s} {'sMAPE%':>8s}")
        for name in BASELINES:
            m = fold["models"][name]
            print(f"{name:28s} {m['n']:5d} {_show(m['MAE']):>8s} {_show(m['RMSE']):>8s} "
                  f"{_show(m['WAPE']):>8s} {_show(m['MASE'], 3):>7s} "
                  f"{_show(m['bias']):>8s} {_show(m['R2'], 4):>8s} "
                  f"{_show(m['sMAPE']):>8s}")


if __name__ == "__main__":
    main()
