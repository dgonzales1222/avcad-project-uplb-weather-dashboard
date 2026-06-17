"""Cleaning & validation — Phase 2.

Turns the raw Open-Meteo parquet (data/raw/) into ONE tidy, validated daily
DataFrame whose columns are the canonical variables shared with the UPLB-NAS
station record. The station is daily-only, so the four variables Open-Meteo has
no daily aggregate for (relative humidity, wet-bulb temp, station pressure, and
the station's *average* wind speed) are derived here from the hourly pull.

Canonical daily columns produced (besides ``date``):
    max_temp, min_temp, mean_temp, wet_bulb_temp, relative_humidity,
    precipitation, wind_speed, wind_direction, station_pressure
"""
from __future__ import annotations

import pandas as pd

import config

# Native daily columns from Open-Meteo -> canonical names.
_DAILY_RENAME = {
    "time": "date",
    "temperature_2m_max": "max_temp",
    "temperature_2m_min": "min_temp",
    "temperature_2m_mean": "mean_temp",
    "precipitation_sum": "precipitation",
    "wind_direction_10m_dominant": "wind_direction",
}

# Hourly columns aggregated to a daily mean -> canonical names.
# (Station wind speed is an *average*, so we mean the hourly wind too.)
_HOURLY_MEAN = {
    "relative_humidity_2m": "relative_humidity",
    "wet_bulb_temperature_2m": "wet_bulb_temp",
    "surface_pressure": "station_pressure",
    "wind_speed_10m": "wind_speed",
}

# Final column order (date first).
COLUMNS = [
    "date", "max_temp", "min_temp", "mean_temp", "wet_bulb_temp",
    "relative_humidity", "precipitation", "wind_speed", "wind_direction",
    "station_pressure",
]


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read the hourly and daily raw parquet files written in Phase 1."""
    hourly = pd.read_parquet(config.RAW_DIR / "openmeteo_hourly.parquet")
    daily = pd.read_parquet(config.RAW_DIR / "openmeteo_daily.parquet")
    return hourly, daily


def daily_from_hourly(hourly: pd.DataFrame) -> pd.DataFrame:
    """Aggregate the hourly pull to a daily mean for the four derived variables."""
    g = hourly.assign(date=hourly["time"].dt.normalize())
    agg = g.groupby("date")[list(_HOURLY_MEAN)].mean().rename(columns=_HOURLY_MEAN)
    return agg.reset_index()


def build_daily(hourly: pd.DataFrame, daily: pd.DataFrame) -> pd.DataFrame:
    """Combine native daily aggregates with the hourly-derived daily means."""
    native = daily.rename(columns=_DAILY_RENAME)
    native["date"] = native["date"].dt.normalize()
    derived = daily_from_hourly(hourly)
    df = native.merge(derived, on="date", how="outer")
    return df.sort_values("date").reset_index(drop=True)[COLUMNS]


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Quality checks. Raises on hard violations; NaNs are allowed (future gaps)."""
    if not df["date"].is_unique:
        raise ValueError("duplicate dates in daily frame")

    expected = pd.date_range(df["date"].min(), df["date"].max(), freq="D")
    missing = expected.difference(df["date"])
    if len(missing):
        raise ValueError(f"{len(missing)} missing calendar dates (e.g. {missing[0].date()})")

    rh = df["relative_humidity"].dropna()
    if not rh.between(0, 100).all():
        raise ValueError("relative_humidity outside [0, 100]")

    if (df["precipitation"].dropna() < 0).any():
        raise ValueError("negative precipitation")

    if (df["max_temp"] < df["min_temp"]).any():
        raise ValueError("max_temp below min_temp on some day")

    for col in ("max_temp", "min_temp", "mean_temp", "wet_bulb_temp"):
        vals = df[col].dropna()
        if not vals.between(-10, 55).all():
            raise ValueError(f"{col} outside plausible [-10, 55] °C")

    return df


def clean() -> pd.DataFrame:
    """Top-level: raw parquet -> validated wide daily frame (the canonical record)."""
    return validate(build_daily(*load_raw()))


if __name__ == "__main__":
    out = clean()
    print(f"cleaned daily frame: {out.shape[0]:,} rows × {out.shape[1]} cols")
    print(f"date range: {out['date'].min().date()} → {out['date'].max().date()}")
    print(out.head().to_string())
