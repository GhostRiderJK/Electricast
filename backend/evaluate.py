"""Day-ahead forecast evaluation for ElectriCast.

Baselines forecast every IST hour of a test day using observations strictly
before 00:00 IST of that day. Run from the repo root:

    python backend/evaluate.py
"""
import json
import os

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

import data_pipeline as dp
import forecast_model as fm
import quantile_model as qm
import sarima_model as sm
import weather

RESULTS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.json")

BASELINES = (
    "persistence",
    "seasonal_naive_24",
    "same_hour_last_week",
    "mean_last_4_same_weekdays",
)

LEARNED_MODELS = ("xgboost", "sarima", "xgboost_quantile")

BASELINE_DESCRIPTIONS = {
    "persistence": "last observed value before the forecast day, held flat for 24 h",
    "seasonal_naive_24": "value at the same hour on the previous day",
    "same_hour_last_week": "value at the same hour one week earlier",
    "mean_last_4_same_weekdays": "mean of the same hour on the previous four same weekdays",
}

LEARNED_MODEL_DESCRIPTIONS = {
    "xgboost": "pooled direct day-ahead gradient-boosted trees on lags of 24-47, 168 and 336 h, calendar/holiday/semester flags, hour of day, lagged reporting counts, and lagged Mumbai weather; trained only on the fold's training labels, clipped at the train-only outlier cap",
    "sarima": "SARIMA(1,0,1)(0,1,1,24) on the gap-handled target, refit weekly on the trailing 60 days before each Monday origin and advanced daily with actuals up to each day's origin",
    "xgboost_quantile": "three XGBoost quantile models (P10/P50/P90) on the same features, training window, and train-only cap as the point XGBoost; fixed untuned hyperparameters; predictions clipped at zero and rearranged so quantiles do not cross",
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
    "best_baseline_selection": "lowest MASE on the all-four-baseline mask when it covers >=50% of evaluation hours (and >=24 h); otherwise on the evaluation mask",
    "significance": "two-sided Wilcoxon signed-rank on paired absolute errors vs the best baseline; p-values unadjusted; small_sample flags fewer than 10 pairs",
    "learned_models": "xgboost is fit on the fold's training window labels only; its features at target hour t use observations at t-lag with lag >= 24 h, so all features predate the day's 00:00 IST origin; reporting counts and weather are lagged >=24 h; calendar/holiday/semester flags are known in advance; labels clipped at a train-only Q3+3*IQR cap. sarima is refit weekly on the trailing 60 days before each Monday origin and advanced daily only with actuals before the day's origin",
    "sarima": "order (1,0,1)(0,1,1,24); weekly refit on the trailing 60 days of gap-handled target; daily state updates with actuals up to each origin; recovery refit after coverage gaps",
    "quantiles": "xgboost_quantile fits one model per quantile (0.1, 0.5, 0.9) with objective reg:quantileerror on the same features, labels, and cap as xgboost; P10-P90 coverage and pinball loss are reported per fold, and P50 is also scored as a point forecast",
}


def load_target_with_reporting():
    """Return the gap-handled target and the stable-apartment reporting count."""
    apartments, _ = dp.load_apartments()
    panel, _ = dp.build_panel(apartments)
    stable, _ = dp.stable_apartments(panel)
    target, reporting = dp.build_target(panel, stable)
    filled, _, _, _ = dp.fill_short_gaps(target)
    return filled, reporting


def load_target():
    """Return the gap-handled target series (Wh per reporting apartment)."""
    filled, _ = load_target_with_reporting()
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


def _pinball(actual, pred, quantile):
    diff = actual - pred
    return float(np.maximum(quantile * diff, (quantile - 1) * diff).mean())


def interval_metrics(actual, lower, median, upper):
    """P10-P90 coverage, mean interval width, and pinball loss."""
    frame = pd.concat(
        [
            pd.Series(actual).rename("actual"),
            pd.Series(lower).rename("lower"),
            pd.Series(median).rename("median"),
            pd.Series(upper).rename("upper"),
        ],
        axis=1,
    ).dropna()
    if frame.empty:
        return {
            "status": "no_data", "n": 0, "coverage": None, "mean_width_wh": None,
            "pinball_10": None, "pinball_50": None, "pinball_90": None,
            "pinball_mean": None,
        }

    a = frame["actual"].to_numpy(dtype=float)
    lo = frame["lower"].to_numpy(dtype=float)
    mid = frame["median"].to_numpy(dtype=float)
    up = frame["upper"].to_numpy(dtype=float)
    pinball_10 = _pinball(a, lo, 0.1)
    pinball_50 = _pinball(a, mid, 0.5)
    pinball_90 = _pinball(a, up, 0.9)
    return {
        "status": "ok",
        "n": int(len(a)),
        "coverage": _clean(float(((a >= lo) & (a <= up)).mean()), 4),
        "mean_width_wh": _clean(float((up - lo).mean()), 4),
        "pinball_10": _clean(pinball_10, 4),
        "pinball_50": _clean(pinball_50, 4),
        "pinball_90": _clean(pinball_90, 4),
        "pinball_mean": _clean((pinball_10 + pinball_50 + pinball_90) / 3, 4),
    }


def paired_significance(actual, pred, baseline_pred):
    """Two-sided Wilcoxon signed-rank test on paired absolute errors."""
    frame = pd.concat(
        [
            pd.Series(actual).rename("actual"),
            pd.Series(pred).rename("pred"),
            pd.Series(baseline_pred).rename("baseline"),
        ],
        axis=1,
    ).dropna()
    if frame.empty:
        return {
            "n_pairs": 0, "median_abs_error_diff_wh": None, "model_better": None,
            "small_sample": True, "statistic": None, "p_value": None,
            "significant_at_0.05": None, "reason": "no paired hours",
        }

    model_ae = (frame["pred"] - frame["actual"]).abs()
    base_ae = (frame["baseline"] - frame["actual"]).abs()
    diff = model_ae - base_ae
    median_diff = float(diff.median())

    result = {
        "n_pairs": int(len(diff)),
        "median_abs_error_diff_wh": _clean(median_diff, 4),
        "model_better": bool(median_diff < 0) if median_diff != 0 else None,
        "small_sample": bool(len(diff) < 10),
        "statistic": None,
        "p_value": None,
        "significant_at_0.05": None,
        "reason": None,
    }
    if bool((diff == 0).all()):
        result["reason"] = "all paired differences are zero"
        return result

    try:
        statistic, p_value = wilcoxon(
            diff.to_numpy(dtype=float), zero_method="wilcox", alternative="two-sided"
        )
        result["statistic"] = _clean(statistic, 4)
        result["p_value"] = float(p_value) if np.isfinite(p_value) else None
        result["significant_at_0.05"] = (
            bool(result["p_value"] < 0.05) if result["p_value"] is not None else None
        )
    except ValueError as exc:
        result["reason"] = str(exc)
    return result


def select_best_baseline(actual, preds, eval_mask, scale):
    """Pick the baseline with the lowest MASE on a common mask.

    The all-four-baseline mask is used when it covers at least half of the
    evaluation hours (and at least 24 h); otherwise the evaluation mask is used
    and baselines that lack the longer lags report fewer hours.
    """
    all_four = eval_mask.copy()
    for name in BASELINES:
        all_four &= preds[name].notna()

    if int(all_four.sum()) >= max(24, 0.5 * int(eval_mask.sum())):
        mask_name, mask = "all_four_baselines", all_four
    else:
        mask_name, mask = "evaluation_mask", eval_mask

    selection_metrics = {}
    scores = {}
    for name in BASELINES:
        metrics = compute_metrics(actual[mask], preds[name][mask], scale)
        selection_metrics[name] = metrics
        if metrics["status"] == "ok" and metrics["MASE"] is not None:
            scores[name] = (metrics["MASE"], metrics["MAE"], name)

    best = min(scores, key=lambda name: scores[name][:2]) if scores else None
    return best, mask_name, int(mask.sum()), selection_metrics


def evaluate_fold(series, fold, reporting=None, weather_frame=None):
    """Score baselines and learned models on one day-ahead fold.

    The evaluation mask is every hour with a target value and a seasonal-naive
    forecast. Models that cannot produce a value for an hour (SARIMA after a
    coverage gap) are scored on their available hours, as the lagged baselines
    already are; paired tests use the overlapping hours.
    """
    train = series.loc[fold["train_start"]:fold["train_end"]]
    scale = mase_scale(train)
    actual = series.reindex(test_hours(fold["test_start"], fold["test_end"]))
    preds = baseline_forecasts(series, fold["test_start"], fold["test_end"])
    model_fit = {}
    quantile_frame = None
    for name in LEARNED_MODELS:
        if name == "xgboost":
            preds[name], model_fit[name] = fm.forecast(
                series,
                fold["train_start"],
                fold["train_end"],
                fold["test_start"],
                fold["test_end"],
                reporting=reporting,
                weather=weather_frame,
                tune_model=True,
            )
        elif name == "sarima":
            preds[name], model_fit[name] = sm.forecast(
                series, fold["test_start"], fold["test_end"]
            )
        elif name == "xgboost_quantile":
            quantile_frame, model_fit[name] = qm.forecast(
                series,
                fold["train_start"],
                fold["train_end"],
                fold["test_start"],
                fold["test_end"],
                reporting=reporting,
                weather=weather_frame,
            )
            preds[name] = quantile_frame["p50"]
    mask = actual.notna() & preds["seasonal_naive_24"].notna()

    models = {}
    for name in BASELINES + LEARNED_MODELS:
        models[name] = compute_metrics(actual[mask], preds[name][mask], scale)

    intervals = {}
    if quantile_frame is not None:
        intervals["xgboost_quantile"] = interval_metrics(
            actual[mask],
            quantile_frame.loc[mask, "p10"],
            quantile_frame.loc[mask, "p50"],
            quantile_frame.loc[mask, "p90"],
        )

    best, selection_mask, selection_hours, selection_metrics = select_best_baseline(
        actual, preds, mask, scale
    )
    paired = {}
    for name in models:
        if name == best:
            continue
        paired[name] = paired_significance(
            actual[mask], preds[name][mask], preds[best][mask]
        ) if best else {
            "n_pairs": 0, "median_abs_error_diff_wh": None, "model_better": None,
            "small_sample": True, "statistic": None, "p_value": None,
            "significant_at_0.05": None, "reason": "no best baseline",
        }

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
        "intervals": intervals,
        "model_fit": model_fit,
        "best_baseline": best,
        "selection": {
            "mask": selection_mask,
            "hours": selection_hours,
            "by": "MASE",
            "metrics": selection_metrics,
        },
        "paired_vs_best": paired,
    }


def run_backtest(series, reporting=None, weather_frame=None):
    return [
        evaluate_fold(series, fold, reporting=reporting, weather_frame=weather_frame)
        for fold in FOLDS
    ]


def build_results(series=None, reporting=None, weather_frame=None):
    if series is None:
        series, reporting = load_target_with_reporting()
    if weather_frame is None:
        weather_frame = weather.load()
    return {
        "generated_at": pd.Timestamp.now(tz=dp.TZ).isoformat(timespec="seconds"),
        "protocol": dict(PROTOCOL),
        "baselines": list(BASELINES),
        "baseline_descriptions": dict(BASELINE_DESCRIPTIONS),
        "learned_models": list(LEARNED_MODELS),
        "learned_model_descriptions": dict(LEARNED_MODEL_DESCRIPTIONS),
        "weather": weather.describe(weather_frame),
        "folds": run_backtest(series, reporting, weather_frame),
    }


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
    results = build_results()
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write("\n")
    print(f"Wrote {RESULTS_PATH}")
    state = results["weather"]
    print(f"weather: {state['cache']}" if state["available"] else "weather: unavailable")
    print(f"Day-ahead backtest, {len(FOLDS)} expanding folds, origin 00:00 IST")
    for fold in results["folds"]:
        test = fold["test"]
        print(f"\n== {fold['id']}: train {fold['train']['hours']} h "
              f"({fold['train']['valid_hours']} valid), test {test['clock_hours']} h "
              f"({test['target_valid_hours']} target), eval {test['eval_hours']} h / "
              f"{test['eval_days']} d, MASE scale {_show(fold['mase_scale'])}")
        print(f"{'model':28s} {'n':>5s} {'MAE':>8s} {'RMSE':>8s} {'WAPE%':>8s} "
              f"{'MASE':>7s} {'bias':>8s} {'R2':>8s} {'sMAPE%':>8s}")
        for name in results["baselines"] + results["learned_models"]:
            m = fold["models"][name]
            print(f"{name:28s} {m['n']:5d} {_show(m['MAE']):>8s} {_show(m['RMSE']):>8s} "
                  f"{_show(m['WAPE']):>8s} {_show(m['MASE'], 3):>7s} "
                  f"{_show(m['bias']):>8s} {_show(m['R2'], 4):>8s} "
                  f"{_show(m['sMAPE']):>8s}")
        for name, meta in fold["model_fit"].items():
            if "n_train" in meta:
                print(f"fit {name}: n={meta['n_train']}, "
                      f"cap={_show(meta['cap_wh'])} Wh, capped={meta['n_capped']}")
            else:
                print(f"fit {name}: fits={meta.get('n_fits')}, "
                      f"hours={meta.get('predicted_hours')}, "
                      f"failures={meta.get('fit_failures')}")
        for name, im in fold.get("intervals", {}).items():
            print(f"interval {name}: n={im['n']} coverage={_show(im['coverage'], 3)} "
                  f"width={_show(im['mean_width_wh'])} Wh "
                  f"pinball={_show(im['pinball_mean'], 3)}")
        selection = fold["selection"]
        print(f"best baseline: {fold['best_baseline']} "
              f"({selection['mask']}, {selection['hours']} h, by {selection['by']})")
        for name, comp in fold["paired_vs_best"].items():
            p_value = comp["p_value"] if comp["p_value"] is not None else comp["reason"]
            print(f"  {name:28s} n={comp['n_pairs']:5d} "
                  f"median_diff={_show(comp['median_abs_error_diff_wh'])} Wh "
                  f"p={p_value}")


if __name__ == "__main__":
    main()
