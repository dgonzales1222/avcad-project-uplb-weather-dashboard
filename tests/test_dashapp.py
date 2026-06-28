"""Phase-migration smoke tests for the Dash app (src/dashapp).

Builds a tiny database from the real schema, points config at it, then asserts the
app registers its pages, each page layout builds without error, and the General
Weather time-series callback returns graphs. No browser needed.

Run with:  pytest
"""
import json
import sqlite3
import sys

import pandas as pd
import pytest

import config

SCHEMA = (config.PROJECT_ROOT / "src" / "db" / "schema.sql").read_text()
VARIABLES = [
    (1, "max_temp", "°C"), (2, "min_temp", "°C"), (3, "mean_temp", "°C"),
    (4, "wet_bulb_temp", "°C"), (5, "relative_humidity", "%"), (6, "precipitation", "mm"),
    (7, "wind_speed", "m/s"), (8, "wind_direction", "°"), (9, "station_pressure", "hPa"),
]
_BASE = {1: 32, 2: 24, 3: 28, 4: 25, 5: 85, 6: 2, 7: 2, 8: 180, 9: 1008}


def _make_db(path):
    """One station, 9 variables, 90 daily rows spanning two years."""
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.execute("INSERT INTO station VALUES (1, 'Open-Meteo @ UPLB', 14.17, 121.24, NULL, 'open-meteo')")
    conn.executemany("INSERT INTO variable VALUES (?, ?, ?, '')", VARIABLES)
    dates = pd.date_range("2019-12-01", periods=90, freq="D")
    rows = [
        (1, d.strftime("%Y-%m-%d"), vid, _BASE[vid] + (i % 5) * 0.3)
        for i, d in enumerate(dates) for vid, _, _ in VARIABLES
    ]
    conn.executemany("INSERT INTO observation_daily VALUES (?, ?, ?, ?)", rows)
    conn.commit()
    conn.close()


@pytest.fixture
def dashapp(tmp_path, monkeypatch):
    db = tmp_path / "weather.db"
    _make_db(db)
    monkeypatch.setattr(config, "DB_PATH", db)
    from src.dashapp import data
    data.clear()
    import src.dashapp.app as appmod  # constructing the app auto-imports the pages
    yield appmod
    data.clear()


def _gw_module():
    return next(
        m for m in sys.modules.values()
        if m and getattr(m, "__file__", None) and m.__file__.endswith("general_weather.py")
    )


def _ci_module():
    return next(
        m for m in sys.modules.values()
        if m and getattr(m, "__file__", None) and m.__file__.endswith("climate_insights.py")
    )


def test_pages_register(dashapp):
    import dash
    names = {p["name"] for p in dash.page_registry.values()}
    paths = {p["path"] for p in dash.page_registry.values()}
    assert {"General Weather", "Climate Insights"} <= names
    assert {"/", "/climate-insights"} <= paths


def test_all_page_layouts_build(dashapp):
    import dash
    for p in dash.page_registry.values():
        layout = p["layout"]
        component = layout() if callable(layout) else layout
        assert component is not None


def test_timeseries_callback_returns_graphs(dashapp):
    from dash import dcc
    gw = _gw_module()
    graphs, heading = gw.update_timeseries("All years", "Monthly", ["Temperature", "Rainfall"])
    assert len(graphs) == 2
    assert all(isinstance(g, dcc.Graph) for g in graphs)
    assert "Time series" in heading and "monthly" in heading


def test_timeseries_callback_empty_selection(dashapp):
    gw = _gw_module()
    graphs, heading = gw.update_timeseries("2020", "Daily", [])
    assert len(graphs) == 1  # the "select a parameter" notice
    assert heading == "Time series"


# --- Climate Insights (Phase 5) ---------------------------------------------

def test_heat_index_daily(dashapp):
    from src.dashapp import data
    hid = data.heat_index_daily()
    assert list(hid.columns) == ["hi_c", "band"]
    assert len(hid) == 90
    assert hid["hi_c"].between(20, 70).all()
    assert hid["band"].notna().all()


def test_trend_figure_and_legend(dashapp):
    import plotly.graph_objects as go
    ci = _ci_module()
    fig = ci._trend_fig()
    legend = ci._band_legend()
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2                 # annual-mean line + trend line
    assert len(fig.layout.shapes) >= 1        # shaded PAGASA bands
    assert len(legend) == 4                   # 4 PAGASA danger-band legend entries


def test_forecast_callback_returns_figure_and_metrics(dashapp, monkeypatch, tmp_path):
    import plotly.graph_objects as go
    from src.dashapp import data
    from src.models import forecast
    # Force the live-training fallback (ignore any committed artifact) + tiny LSTM.
    monkeypatch.setattr(data, "_FORECAST_FILE", tmp_path / "absent.json")
    monkeypatch.setattr(forecast, "EPOCHS", 2)
    monkeypatch.setattr(forecast, "LOOKBACK", 10)
    monkeypatch.setattr(forecast, "UNITS", 8)
    data.heat_index_forecast.cache_clear()
    ci = _ci_module()
    fig, metrics = ci.update_forecast(7)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 3                    # uncertainty band + actual + forecast
    assert metrics is not None


def test_forecast_reads_precomputed_artifact(dashapp, monkeypatch, tmp_path):
    """Deploy path: serve the forecast from JSON without importing torch."""
    from src.dashapp import data
    artifact = tmp_path / "fc.json"
    artifact.write_text(json.dumps({"14": {
        "forecast": [{"ds": "2026-01-01", "yhat": 33.0, "yhat_lower": 31.0, "yhat_upper": 35.0}],
        "metrics": {"mae": 2.4, "rmse": 2.8},
    }}))
    monkeypatch.setattr(data, "_FORECAST_FILE", artifact)
    data.heat_index_forecast.cache_clear()
    fc, metrics = data.heat_index_forecast(14)
    assert metrics == {"mae": 2.4, "rmse": 2.8}
    assert list(fc["ds"].dt.strftime("%Y-%m-%d")) == ["2026-01-01"]
