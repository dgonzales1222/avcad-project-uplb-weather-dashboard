"""Phase 2 unit tests for the cleaning/validation logic (src/data/clean.py).

These use small synthetic frames rather than the real data/raw parquet (which is
git-ignored and local-only), so they are deterministic and run anywhere.

Run with:  python -m pytest
"""
import pandas as pd
import pytest

from src.data import clean


# --- fixtures ---------------------------------------------------------------

def _hourly_two_days() -> pd.DataFrame:
    """48 hours over two days, constant within each day so means are obvious."""
    time = pd.date_range("2020-01-01", periods=48, freq="h")
    day1 = [True] * 24 + [False] * 24
    return pd.DataFrame(
        {
            "time": time,
            "temperature_2m": [28.0] * 48,  # unused by the aggregation, here for realism
            "relative_humidity_2m": [80.0 if d else 90.0 for d in day1],
            "wet_bulb_temperature_2m": [20.0 if d else 22.0 for d in day1],
            "surface_pressure": [1000.0 if d else 1010.0 for d in day1],
            "wind_speed_10m": [2.0 if d else 4.0 for d in day1],
        }
    )


def _native_two_days() -> pd.DataFrame:
    """Native Open-Meteo daily aggregates for the same two days."""
    return pd.DataFrame(
        {
            "time": pd.to_datetime(["2020-01-01", "2020-01-02"]),
            "temperature_2m_max": [32.0, 33.0],
            "temperature_2m_min": [24.0, 25.0],
            "temperature_2m_mean": [28.0, 29.0],
            "precipitation_sum": [0.0, 5.5],
            "wind_direction_10m_dominant": [90.0, 270.0],
        }
    )


def _valid_daily(n: int = 4) -> pd.DataFrame:
    """A valid wide daily frame (continuous dates, in-range values)."""
    dates = pd.date_range("2020-01-01", periods=n, freq="D")
    return pd.DataFrame(
        {
            "date": dates,
            "max_temp": [32.0] * n,
            "min_temp": [24.0] * n,
            "mean_temp": [28.0] * n,
            "wet_bulb_temp": [25.0] * n,
            "relative_humidity": [85.0] * n,
            "precipitation": [3.0] * n,
            "wind_speed": [2.0] * n,
            "wind_direction": [90.0] * n,
            "station_pressure": [1008.0] * n,
        }
    )[clean.COLUMNS]


# --- daily_from_hourly ------------------------------------------------------

def test_daily_from_hourly_means():
    out = clean.daily_from_hourly(_hourly_two_days())
    assert list(out["date"]) == [pd.Timestamp("2020-01-01"), pd.Timestamp("2020-01-02")]
    # Day 1 / Day 2 means equal the constants we set.
    assert out.loc[0, "relative_humidity"] == 80.0
    assert out.loc[1, "relative_humidity"] == 90.0
    assert out.loc[0, "wet_bulb_temp"] == 20.0
    assert out.loc[1, "station_pressure"] == 1010.0
    assert out.loc[0, "wind_speed"] == 2.0


# --- build_daily ------------------------------------------------------------

def test_build_daily_columns_and_merge():
    df = clean.build_daily(_hourly_two_days(), _native_two_days())
    # Exact canonical column set and order.
    assert list(df.columns) == clean.COLUMNS
    assert len(df) == 2
    # Native daily values carried through.
    assert df.loc[0, "max_temp"] == 32.0
    assert df.loc[1, "wind_direction"] == 270.0
    assert df.loc[1, "precipitation"] == 5.5
    # Hourly-derived means merged on date.
    assert df.loc[0, "relative_humidity"] == 80.0
    assert df.loc[1, "station_pressure"] == 1010.0


# --- validate ---------------------------------------------------------------

def test_validate_passes_clean_frame():
    df = _valid_daily()
    assert clean.validate(df) is df  # returns the frame unchanged


def test_validate_allows_nan_values():
    df = _valid_daily()
    df.loc[1, "relative_humidity"] = float("nan")  # gaps are allowed
    assert clean.validate(df) is df


def test_validate_rejects_rh_out_of_range():
    df = _valid_daily()
    df.loc[0, "relative_humidity"] = 150.0
    with pytest.raises(ValueError, match="relative_humidity"):
        clean.validate(df)


def test_validate_rejects_negative_precip():
    df = _valid_daily()
    df.loc[0, "precipitation"] = -1.0
    with pytest.raises(ValueError, match="precipitation"):
        clean.validate(df)


def test_validate_rejects_max_below_min():
    df = _valid_daily()
    df.loc[0, "max_temp"] = 10.0  # below min_temp (24)
    with pytest.raises(ValueError, match="max_temp"):
        clean.validate(df)


def test_validate_rejects_duplicate_dates():
    df = _valid_daily()
    df.loc[1, "date"] = df.loc[0, "date"]
    with pytest.raises(ValueError, match="duplicate"):
        clean.validate(df)


def test_validate_rejects_missing_calendar_date():
    df = _valid_daily().drop(index=2).reset_index(drop=True)  # punch a gap
    with pytest.raises(ValueError, match="missing"):
        clean.validate(df)
