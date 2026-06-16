"""ALL external data access lives here (docs/PROJECT_CONTEXT.md rule).

Open-Meteo now; the UPLB-NAS station loader is added in Phase 8. Nothing else
in the codebase should fetch external data — everything downstream reads the
cleaned SQLite database (data/weather.db).

Phase 1 (this module):
    fetch_openmeteo_hourly(start, end)  -> tidy hourly DataFrame
    fetch_openmeteo_daily(start, end)   -> tidy daily DataFrame
    fetch_all(start, end)               -> fetch both and write data/raw/*.parquet

Run as a script to download the full configured record:
    python -m src.data.sources

Timezone note: requests are made with timezone=Asia/Manila so the API's daily
aggregates fall on local calendar days. All timestamps returned here are shifted
to local (Asia/Manila) wall-clock time and stored tz-naive, ready for the
daily-max heat index and ">41 °C day" counts without further conversion.

Phase 8 will add:  load_uplb_nas(path)
"""
from __future__ import annotations

from pathlib import Path

import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

import config

# Open-Meteo Historical Weather API (ERA5 reanalysis).
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Hourly variables — the heat index needs temperature + relative humidity at
# hourly resolution; precipitation and wind feed the General Weather page.
HOURLY_VARS = [
    "temperature_2m",        # °C
    "relative_humidity_2m",  # %
    "precipitation",         # mm
    "wind_speed_10m",        # km/h
]

# Daily variables — convenience aggregates for climatology summaries.
DAILY_VARS = [
    "temperature_2m_max",  # °C
    "temperature_2m_min",  # °C
    "temperature_2m_mean", # °C
    "precipitation_sum",   # mm
    "wind_speed_10m_max",  # km/h
]

# HTTP cache (so re-runs don't re-hit the API) + retry on transient failures.
_CACHE_DIR = config.PROJECT_ROOT / ".cache"


def _client() -> openmeteo_requests.Client:
    """Build the Open-Meteo client with on-disk caching and retry/backoff."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_session = requests_cache.CachedSession(
        str(_CACHE_DIR / "openmeteo"), expire_after=-1
    )
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    return openmeteo_requests.Client(session=retry_session)


def _local_index(section, offset_seconds: int) -> pd.DatetimeIndex:
    """Build the time index for an hourly/daily section in local wall-clock time.

    The SDK returns timestamps in UTC; adding the response's UTC offset yields
    Asia/Manila local time, which we keep tz-naive for downstream simplicity.
    """
    return pd.date_range(
        start=pd.to_datetime(section.Time(), unit="s", utc=True),
        end=pd.to_datetime(section.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=section.Interval()),
        inclusive="left",
    ).tz_localize(None) + pd.Timedelta(seconds=offset_seconds)


def _fetch(start: str, end: str, *, granularity: str, variables: list[str]) -> pd.DataFrame:
    """Shared fetch for the hourly/daily endpoints; returns a tidy DataFrame."""
    params = {
        "latitude": config.LAT,
        "longitude": config.LON,
        "start_date": start,
        "end_date": end,
        granularity: variables,
        "timezone": config.TZ,
    }
    response = _client().weather_api(ARCHIVE_URL, params=params)[0]
    offset = response.UtcOffsetSeconds()

    section = response.Hourly() if granularity == "hourly" else response.Daily()
    data = {"time": _local_index(section, offset)}
    for i, name in enumerate(variables):
        data[name] = section.Variables(i).ValuesAsNumpy()

    return pd.DataFrame(data)


def fetch_openmeteo_hourly(
    start: str = config.START, end: str = config.END
) -> pd.DataFrame:
    """Fetch hourly Open-Meteo observations for the configured location.

    Columns: time (local, tz-naive) + HOURLY_VARS.
    """
    return _fetch(start, end, granularity="hourly", variables=HOURLY_VARS)


def fetch_openmeteo_daily(
    start: str = config.START, end: str = config.END
) -> pd.DataFrame:
    """Fetch daily Open-Meteo aggregates for the configured location.

    Columns: time (local date, tz-naive) + DAILY_VARS.
    """
    return _fetch(start, end, granularity="daily", variables=DAILY_VARS)


def save_raw(df: pd.DataFrame, name: str) -> Path:
    """Write a raw DataFrame to data/raw/<name>.parquet and return the path."""
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = config.RAW_DIR / f"{name}.parquet"
    df.to_parquet(path, index=False)
    return path


def fetch_all(start: str = config.START, end: str = config.END) -> None:
    """Fetch hourly + daily records and save them under data/raw/."""
    print(f"Fetching Open-Meteo {start} → {end} for ({config.LAT}, {config.LON})…")

    hourly = fetch_openmeteo_hourly(start, end)
    hpath = save_raw(hourly, "openmeteo_hourly")
    print(f"  hourly: {len(hourly):,} rows -> {hpath}")

    daily = fetch_openmeteo_daily(start, end)
    dpath = save_raw(daily, "openmeteo_daily")
    print(f"  daily:  {len(daily):,} rows -> {dpath}")


if __name__ == "__main__":
    fetch_all()
