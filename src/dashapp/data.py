"""Read-only data access for the Dash app — reuses the framework-agnostic layer.

The SQLite database is static, so each query is loaded once and cached. The
underlying logic lives in src/db/queries.py (shared with the old Streamlit app).
"""
import json
from functools import lru_cache
from pathlib import Path

import pandas as pd

from src.db import queries
from src.features import heat_index

# Precomputed forecast artifact (written by `python -m src.models.precompute`).
# When present, the app reads it instead of training — so the deployed server
# needs neither PyTorch nor any training.
_FORECAST_FILE = Path(__file__).resolve().parent / "forecast_precomputed.json"


@lru_cache(maxsize=1)
def daily():
    """Wide daily frame: DatetimeIndex × the 9 canonical variables."""
    return queries.load_daily()


@lru_cache(maxsize=1)
def units():
    """{variable name: unit}."""
    return queries.variable_units()


@lru_cache(maxsize=1)
def station():
    """Station metadata dict."""
    return queries.station_info()


@lru_cache(maxsize=1)
def heat_index_daily() -> pd.DataFrame:
    """Daily heat index (°C) + PAGASA band, from daily Tmax + mean RH.

    NOTE: pairing daily max temperature with daily *mean* relative humidity tends
    to OVERESTIMATE the heat index (humidity is lowest at peak heat). Reused by
    Climate Insights (Phase 5) and the forecast (Phase 6).
    """
    df = daily()
    if df.empty:
        return pd.DataFrame(columns=["hi_c", "band"])
    hi = heat_index.heat_index_c(df["max_temp"].to_numpy(), df["relative_humidity"].to_numpy())
    out = pd.DataFrame({"hi_c": hi}, index=df.index)
    out["band"] = heat_index.classify(out["hi_c"].to_numpy())
    return out


def _load_precomputed(horizon: int):
    """Read the committed forecast artifact for `horizon` (no torch). None if absent."""
    if not _FORECAST_FILE.exists():
        return None
    try:
        entry = json.loads(_FORECAST_FILE.read_text())[str(horizon)]
    except (ValueError, KeyError):
        return None
    fc = pd.DataFrame(entry["forecast"])
    fc["ds"] = pd.to_datetime(fc["ds"])
    return fc, entry["metrics"]


@lru_cache(maxsize=4)
def heat_index_forecast(horizon: int = 14):
    """(forecast_df, {mae, rmse}) for the daily heat index; cached per horizon.

    Prefers the precomputed artifact (no torch — used in deployment); falls back to
    training the LSTM live only if the artifact is missing (local dev).
    """
    precomputed = _load_precomputed(horizon)
    if precomputed is not None:
        return precomputed

    series = heat_index_daily()["hi_c"]
    if series.empty:
        empty = pd.DataFrame(columns=["ds", "yhat", "yhat_lower", "yhat_upper"])
        return empty, {"mae": float("nan"), "rmse": float("nan")}
    from src.models import forecast
    return forecast.fit_forecast(series, horizon), forecast.backtest(series, horizon)


def clear():
    """Drop the caches (used by tests that swap the database)."""
    daily.cache_clear()
    units.cache_clear()
    station.cache_clear()
    heat_index_daily.cache_clear()
    heat_index_forecast.cache_clear()
