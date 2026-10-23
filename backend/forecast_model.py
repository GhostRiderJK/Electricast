"""Leakage-safe XGBoost day-ahead forecaster.

Every feature for a target hour t uses only observations at t - lag with
lag >= 24 h, so a forecast for any hour of day D depends only on values before
00:00 IST of D. The model is trained on labels from the fold's training window
and never sees evaluation-window targets during fitting.
"""
import numpy as np
import pandas as pd
import xgboost as xgb

import data_pipeline as dp

# The 24-47 h block is the 24-hour window ending 24 h before the target hour;
# the weekly lags provide the same clock hour one and two weeks earlier.
FEATURE_LAGS = tuple(range(24, 48)) + (168, 336)

DEFAULT_PARAMS = {
    "n_estimators": 400,
    "learning_rate": 0.03,
    "max_depth": 4,
    "min_child_weight": 8,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_lambda": 2.0,
    "objective": "reg:squarederror",
    "tree_method": "hist",
    "random_state": 42,
    "n_jobs": 4,
}


def make_features(series, hours):
    """Build lag-only features for the given target hours.

    `hours` must be tz-aware IST timestamps. The result is indexed by `hours`.
    Missing history stays NaN; XGBoost handles it natively at fit and predict.
    """
    hours = pd.DatetimeIndex(hours)
    block = {}
    for lag in FEATURE_LAGS:
        block[f"lag_{lag}"] = series.reindex(
            hours - pd.Timedelta(hours=lag)
        ).to_numpy(dtype=float)

    daily = pd.DataFrame({lag: block[f"lag_{lag}"] for lag in range(24, 48)})
    block["lag24_47_mean"] = daily.mean(axis=1).to_numpy()
    block["lag24_47_std"] = daily.std(axis=1).to_numpy()
    block["lag24_47_min"] = daily.min(axis=1).to_numpy()
    block["lag24_47_max"] = daily.max(axis=1).to_numpy()
    block["hour"] = hours.hour.to_numpy(dtype=int)
    return pd.DataFrame(block, index=hours)


def _hour_range(start, end):
    return pd.date_range(start, end, freq="h", tz=dp.TZ)


def fit(series, train_start, train_end, params=None):
    """Fit one pooled model on the training window.

    Labels are clipped with the train-only Q3 + 3*IQR cap before fitting; the
    cap is fitted on training labels only. Rows without a label or without the
    24-h lag are dropped.
    """
    hours = _hour_range(train_start, train_end)
    features = make_features(series, hours)
    labels = series.reindex(hours).astype(float)
    keep = labels.notna() & features["lag_24"].notna()
    features = features.loc[keep]
    labels = labels.loc[keep]

    cap = None
    n_capped = 0
    if len(labels) >= dp.OUTLIER_MIN_SAMPLES:
        cap = dp.fit_outlier_cap(labels)
        labels, n_capped = dp.apply_outlier_cap(labels, cap)

    effective = dict(DEFAULT_PARAMS)
    if params:
        effective.update(params)
    model = xgb.XGBRegressor(**effective)
    model.fit(features, labels)

    metadata = {
        "n_train": int(len(labels)),
        "train_start": str(train_start),
        "train_end": str(train_end),
        "cap_wh": None if cap is None else round(float(cap), 4),
        "n_capped": int(n_capped),
        "params": {k: v for k, v in effective.items() if k != "n_jobs"},
        "features": list(features.columns),
    }
    return model, metadata


def predict(series, model, start, end):
    """Predict every hour in [start, end]; negative loads are clipped to zero."""
    hours = _hour_range(start, end)
    features = make_features(series, hours)
    values = model.predict(features).astype(float)
    return pd.Series(np.maximum(values, 0.0), index=hours, name="xgboost")


def forecast(series, train_start, train_end, test_start, test_end, params=None):
    """Fit on the training window and forecast the test window."""
    model, metadata = fit(series, train_start, train_end, params=params)
    return predict(series, model, test_start, test_end), metadata
