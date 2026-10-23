"""Hand-checked metric and baseline tests.

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

import evaluate as ev  # noqa: E402


def test_compute_metrics_hand_checked():
    metrics = ev.compute_metrics(
        pd.Series([10.0, 20.0, 30.0, 40.0]),
        pd.Series([12.0, 18.0, 33.0, 36.0]),
        scale=2.0,
    )
    assert metrics["status"] == "ok"
    assert metrics["n"] == 4
    assert metrics["MAE"] == 2.75
    assert metrics["RMSE"] == 2.8723
    assert metrics["WAPE"] == 11.0
    assert metrics["sMAPE"] == 12.1896
    assert metrics["bias"] == -0.25
    assert metrics["R2"] == 0.934
    assert metrics["MASE"] == 1.375


def test_compute_metrics_guards_zero_denominators():
    metrics = ev.compute_metrics(pd.Series([0.0, 0.0]), pd.Series([0.0, 0.0]), scale=1.0)
    assert metrics["status"] == "ok"
    assert metrics["MAE"] == 0.0
    assert metrics["WAPE"] is None
    assert metrics["R2"] is None
    assert metrics["sMAPE"] == 0.0
    assert metrics["MASE"] == 0.0


def test_compute_metrics_drops_missing_pairs_and_no_data():
    partial = ev.compute_metrics(
        pd.Series([1.0, np.nan, 3.0]), pd.Series([1.0, 2.0, np.nan])
    )
    assert partial["status"] == "ok"
    assert partial["n"] == 1
    assert partial["MAE"] == 0.0

    empty = ev.compute_metrics(pd.Series([np.nan]), pd.Series([1.0]))
    assert empty["status"] == "no_data"
    assert empty["n"] == 0
    assert all(empty[key] is None for key in ("MAE", "RMSE", "WAPE", "MASE", "bias", "R2", "sMAPE"))


def test_mase_scale_uses_24_hour_seasonal_differences():
    index = pd.date_range("2021-01-01", periods=48, freq="h", tz="Asia/Kolkata")
    series = pd.Series(np.arange(48, dtype=float), index=index)
    assert ev.mase_scale(series) == 24.0
    assert ev.mase_scale(series.iloc[:24]) is None


def test_baselines_follow_day_ahead_lags():
    index = pd.date_range("2021-01-01", periods=8 * 24, freq="h", tz="Asia/Kolkata")
    series = pd.Series(np.arange(len(index), dtype=float), index=index)
    hours = pd.date_range("2021-01-08", periods=24, freq="h", tz="Asia/Kolkata")

    preds = ev.baseline_forecasts(series, hours[0], hours[-1])

    assert preds["persistence"].nunique() == 1
    assert preds["persistence"].iloc[0] == series.loc["2021-01-07 23:00"].item()
    np.testing.assert_allclose(
        preds["seasonal_naive_24"].to_numpy(),
        series.reindex(hours - pd.Timedelta(hours=24)).to_numpy(),
    )


def test_phase9_fold_layout_and_stress_test_flag():
    ids = [fold["id"] for fold in ev.FOLDS]
    assert ids == [
        "2017-06", "2017-07", "2017-08", "2017-09_11", "2017-12",
        "2018-05_06",
    ]
    stress = [fold for fold in ev.FOLDS if fold.get("stress_test")]
    assert [fold["id"] for fold in stress] == ["2018-05_06"]
    assert stress[0]["label"].lower().startswith("stress test")
    assert all(not fold.get("stress_test") for fold in ev.FOLDS[:-1])
    assert ev.FOLDS[3]["test_end"] == "2017-11-30 23:00"
    assert ev.FOLDS[4]["test_start"] == "2017-12-01 00:00"


def test_history_start_is_the_first_valid_target_hour():
    index = pd.date_range("2020-01-01", periods=4, freq="h", tz="Asia/Kolkata")
    series = pd.Series([np.nan, 1.0, 2.0, 3.0], index=index)
    assert ev.history_start(series) == "2020-01-01 01:00"
    with np.testing.assert_raises(ValueError):
        ev.history_start(pd.Series([np.nan], index=index))
