"""Data pipeline for the IIT Bombay apartment meter CSVs.

Raw schema: TS (Unix seconds, UTC), V1-V3 (volts), W1-W3 (phase energy, Wh).
"""
import glob
import json
import os

import pandas as pd

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
TZ = "Asia/Kolkata"
REQUIRED_COLUMNS = ["TS", "W1", "W2", "W3"]

LOAD_ERRORS = (
    FileNotFoundError,
    pd.errors.EmptyDataError,
    pd.errors.ParserError,
    UnicodeDecodeError,
    ValueError,
)


def apartment_id(path):
    return os.path.splitext(os.path.basename(path))[0]


def read_apartment_file(path):
    """Read one apartment CSV, validate its schema and parse timestamps."""
    df = pd.read_csv(path, usecols=REQUIRED_COLUMNS)
    if df.empty:
        raise ValueError("file has no data rows")
    df = df.sort_values("TS").reset_index(drop=True)
    df["timestamp_utc"] = pd.to_datetime(df["TS"], unit="s", utc=True)
    return df


def apartment_hourly(df):
    """Sum the three phases and resample one apartment to IST hours."""
    timestamps = df["timestamp_utc"].dt.tz_convert(TZ)
    phase_sum = df[["W1", "W2", "W3"]].sum(axis=1, min_count=1)
    series = pd.Series(phase_sum.to_numpy(), index=timestamps)
    series = series.sort_index()
    return series.resample("h").sum(min_count=1)


def build_panel(apartments):
    """Combine per-apartment hourly series and count reporting apartments."""
    hourly = {name: apartment_hourly(df) for name, df in apartments.items()}
    panel = pd.concat(hourly, axis=1).sort_index()
    panel.index.name = "timestamp_ist"
    n_reporting = panel.notna().sum(axis=1).astype(int)
    n_reporting.name = "n_reporting"
    return panel, n_reporting


def load_apartments(data_dir=DATA_DIR):
    """Load every CSV in data_dir and return (apartments, report).

    apartments maps apartment id -> DataFrame with timestamp_utc.
    report records files found/read/failed and the overall timestamp range.
    """
    paths = sorted(
        glob.glob(os.path.join(data_dir, "*.csv")),
        key=lambda p: apartment_id(p),
    )
    apartments = {}
    report = {
        "data_dir": os.path.abspath(data_dir),
        "files_found": len(paths),
        "read_ok": 0,
        "failed": 0,
        "rows_total": 0,
        "first_utc": None,
        "last_utc": None,
        "first_ist": None,
        "last_ist": None,
        "files": [],
        "errors": [],
    }

    for path in paths:
        name = apartment_id(path)
        try:
            df = read_apartment_file(path)
        except LOAD_ERRORS as exc:
            report["failed"] += 1
            report["errors"].append({
                "file": os.path.basename(path),
                "error": f"{type(exc).__name__}: {exc}",
            })
            continue

        apartments[name] = df
        report["read_ok"] += 1
        report["rows_total"] += len(df)
        first_utc = df["timestamp_utc"].iloc[0]
        last_utc = df["timestamp_utc"].iloc[-1]
        report["files"].append({
            "file": os.path.basename(path),
            "rows": int(len(df)),
            "first_utc": first_utc.isoformat(),
            "last_utc": last_utc.isoformat(),
            "first_ist": first_utc.tz_convert(TZ).isoformat(),
            "last_ist": last_utc.tz_convert(TZ).isoformat(),
        })

    if report["files"]:
        report["first_utc"] = min(f["first_utc"] for f in report["files"])
        report["last_utc"] = max(f["last_utc"] for f in report["files"])
        report["first_ist"] = min(f["first_ist"] for f in report["files"])
        report["last_ist"] = max(f["last_ist"] for f in report["files"])

    return apartments, report


if __name__ == "__main__":
    _, summary = load_apartments()
    print(json.dumps(summary, indent=2))
