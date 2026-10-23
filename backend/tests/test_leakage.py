"""Leakage tests for the day-ahead model and baselines.

Run from the repo root:

    python -m pytest backend/tests -q
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import data_pipeline as dp  # noqa: E402
import evaluate as ev  # noqa: E402
import forecast_model as fm  # noqa: E402

TZ = dp.TZ
TEST_DAY = pd.Timestamp("2020-01-22", tz=TZ)
TEST_HOURS = pd.date_range(TEST_DAY, periods=24, freq="h", tz=TZ)


def synthetic_series(days=25):
    index = pd.date_range("2020-01-01", periods=days * 24, freq="h", tz=TZ)
    values = (
        500.0
        + 120.0 * np.sin(2 * np.pi * index.hour.to_numpy() / 24)
        + 0.2 * np.arange(len(index))
    )
    return pd.Series(values, index=index, name="target_wh")


def synthetic_reporting(series):
    return pd.Series(24, index=series.index, name="n_reporting")


def with_future_replaced(series, start):
    mutated = series.copy()
    mutated.loc[start:] = 1e9
    return mutated


def test_all_feature_lags_are_at_least_24_hours():
    assert min(fm.FEATURE_LAGS) >= 24


def test_features_do_not_read_forecast_day_values():
    series = synthetic_series()
    before = fm.make_features(series, TEST_HOURS)
    after = fm.make_features(with_future_replaced(series, TEST_DAY), TEST_HOURS)
    pd.testing.assert_frame_equal(before, after)
    assert all(np.isfinite(before["lag_24"]))


def test_baselines_do_not_read_forecast_day_values():
    series = synthetic_series()
    start, end = TEST_DAY, TEST_HOURS[-1]
    before = ev.baseline_forecasts(series, start, end)
    after = ev.baseline_forecasts(with_future_replaced(series, TEST_DAY), start, end)
    for name in ev.BASELINES:
        np.testing.assert_allclose(
            before[name].to_numpy(), after[name].to_numpy(), equal_nan=True
        )


def test_xgboost_does_not_read_forecast_day_values():
    series = synthetic_series()
    params = {
        "n_estimators": 30,
        "max_depth": 2,
        "learning_rate": 0.1,
        "n_jobs": 1,
    }
    before, _ = fm.forecast(
        series, series.index[0], series.index[20 * 24 - 1],
        TEST_DAY, TEST_HOURS[-1], params=params,
    )
    after, _ = fm.forecast(
        with_future_replaced(series, TEST_DAY),
        series.index[0], series.index[20 * 24 - 1],
        TEST_DAY, TEST_HOURS[-1], params=params,
    )
    np.testing.assert_allclose(before.to_numpy(), after.to_numpy())
    assert before.notna().all()


def test_xgboost_does_not_read_future_reporting_counts():
    series = synthetic_series()
    reporting = synthetic_reporting(series)
    params = {"n_estimators": 30, "max_depth": 2, "learning_rate": 0.1, "n_jobs": 1}
    args = (series, series.index[0], series.index[20 * 24 - 1],
            TEST_DAY, TEST_HOURS[-1])
    before, _ = fm.forecast(*args, params=params, reporting=reporting)
    mutated = reporting.copy()
    mutated.loc[TEST_DAY:] = 0
    after, _ = fm.forecast(*args, params=params, reporting=mutated)
    np.testing.assert_allclose(before.to_numpy(), after.to_numpy())


def test_reporting_features_do_not_read_forecast_day_values():
    series = synthetic_series()
    hours = TEST_HOURS
    before = fm.make_features(series, hours, reporting=synthetic_reporting(series))
    mutated = synthetic_reporting(series)
    mutated.loc[TEST_DAY:] = 999
    after = fm.make_features(series, hours, reporting=mutated)
    pd.testing.assert_frame_equal(before, after)
    assert (before["n_reporting_lag_24"] == 24).all()


def test_calendar_holiday_and_semester_flags():
    hours = pd.date_range("2017-10-16", "2017-10-23 23:00", freq="h", tz=TZ)
    features = fm.make_features(pd.Series(500.0, index=hours), hours)
    holiday = features.index.strftime("%Y-%m-%d").isin(["2017-10-19", "2017-10-20"])
    assert features.loc[holiday, "is_holiday"].eq(1).all()
    assert features.loc[~holiday, "is_holiday"].eq(0).all()
    assert features.loc["2017-10-21 00:00":"2017-10-22 23:00", "is_weekend"].eq(1).all()
    assert features.loc["2017-10-18", "is_weekend"].eq(0).all()
    assert features.loc["2017-10-18", "semester_in_session"].eq(1).all()

    may = pd.date_range("2017-05-01", periods=24, freq="h", tz=TZ)
    may_features = fm.make_features(pd.Series(500.0, index=may), may)
    assert may_features["semester_in_session"].eq(0).all()


def test_xgboost_training_labels_end_before_test_start():
    series = synthetic_series()
    _, metadata = fm.fit(series, series.index[0], series.index[20 * 24 - 1])
    assert pd.Timestamp(metadata["train_end"], tz=TZ) < TEST_DAY
    assert metadata["n_train"] > 0
