"""Fold-mean tests for the API backtest summary."""

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

import main  # noqa: E402


def _metrics(mae, status="ok"):
    return {
        "status": status,
        "n": 24 if status == "ok" else 0,
        "MAE": mae,
        "RMSE": mae + 1,
        "WAPE": 10.0,
        "MASE": 1.0,
        "R2": 0.5,
        "sMAPE": 9.0,
        "bias": mae,
    }


def _fold(fold_id, start, end, mae, stress=False, label=None):
    models = {
        "seasonal_naive_24": _metrics(mae + 1),
        "xgboost": _metrics(mae),
    }
    return {
        "id": fold_id,
        "label": label,
        "stress_test": stress,
        "test": {
            "start": start, "end": end, "eval_hours": 24, "eval_days": 1,
        },
        "models": models,
    }


def test_summary_means_exclude_stress_fold():
    results = {
        "folds": [
            _fold("2017-07", "2017-07-01 00:00", "2017-07-01 23:00", 10.0),
            _fold("2017-08", "2017-08-01 00:00", "2017-08-01 23:00", 20.0),
            _fold(
                "2018-05_06", "2018-05-01 00:00", "2018-05-01 23:00", 500.0,
                stress=True, label="Stress test (May\u2013Jun 2018)",
            ),
        ],
    }
    summary = main._build_backtest_summary(results)
    xgb = next(row for row in summary["models"] if row["key"] == "xgboost")

    assert xgb["mean"]["MAE"] == 15.0
    assert xgb["n_folds"] == 2
    assert xgb["folds_beaten"] == 2
    assert xgb["comparable_folds"] == 2
    assert summary["scoring_fold_ids"] == ["2017-07", "2017-08"]
    assert summary["stress_test_fold_ids"] == ["2018-05_06"]
    assert summary["fold_order"] == ["2017-07", "2017-08", "2018-05_06"]
    assert summary["folds"][-1]["stress_test"] is True
    assert summary["folds"][-1]["label"] == "Stress test (May\u2013Jun 2018)"
    assert xgb["per_fold"][-1]["stress_test"] is True
