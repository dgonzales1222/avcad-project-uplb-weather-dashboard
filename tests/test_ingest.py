"""Phase 2 unit tests for the ingestion/load logic (src/data/ingest.py).

The end-to-end test monkeypatches ``clean()`` to return a tiny synthetic frame and
points the database at a tmp path, so it exercises the real schema.sql + load wiring
without touching the git-ignored data/raw parquet or the local data/weather.db.

Run with:  python -m pytest
"""
import sqlite3

import pandas as pd
import pytest

import config
from src.data import clean, ingest


def _wide(n: int = 4) -> pd.DataFrame:
    """A small wide daily frame with the 9 canonical variable columns."""
    dates = pd.date_range("2020-01-01", periods=n, freq="D")
    data = {"date": dates}
    for col in clean.COLUMNS:
        if col != "date":
            data[col] = [1.0] * n
    return pd.DataFrame(data)[clean.COLUMNS]


# --- _to_long ---------------------------------------------------------------

def test_to_long_shape_and_mapping():
    df = _wide(n=2)
    rows = ingest._to_long(df)
    # 2 dates × 9 variables.
    assert len(rows) == 2 * 9
    # Every row: station_id == 1, ISO date string, variable_id in 1..9.
    assert all(r[0] == 1 for r in rows)
    assert all(isinstance(r[1], str) and len(r[1]) == 10 for r in rows)
    assert {r[2] for r in rows} == set(range(1, 10))
    assert all(r[3] == 1.0 for r in rows)


def test_to_long_maps_nan_to_none():
    df = _wide(n=1)
    df.loc[0, "relative_humidity"] = float("nan")
    rows = ingest._to_long(df)
    rh_id = ingest._NAME_TO_ID["relative_humidity"]
    nan_rows = [r for r in rows if r[2] == rh_id]
    assert nan_rows == [(1, "2020-01-01", rh_id, None)]


# --- build_db (end to end, against the real schema) -------------------------

def test_build_db_end_to_end(tmp_path, monkeypatch):
    daily = _wide(n=5)
    daily.loc[2, "wind_speed"] = float("nan")  # one gap -> one NULL

    # Feed synthetic data and redirect the DB to a temp location.
    monkeypatch.setattr(ingest, "clean", lambda: daily)
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "weather.db")

    ingest.build_db()

    conn = sqlite3.connect(tmp_path / "weather.db")
    try:
        assert conn.execute("SELECT COUNT(*) FROM station").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM variable").fetchone()[0] == 9
        assert conn.execute("SELECT COUNT(*) FROM observation_daily").fetchone()[0] == 5 * 9
        assert conn.execute(
            "SELECT COUNT(*) FROM observation_daily WHERE value IS NULL"
        ).fetchone()[0] == 1
        assert conn.execute(
            "SELECT MIN(date), MAX(date) FROM observation_daily"
        ).fetchone() == ("2020-01-01", "2020-01-05")
    finally:
        conn.close()


def test_build_db_is_idempotent(tmp_path, monkeypatch):
    daily = _wide(n=3)
    monkeypatch.setattr(ingest, "clean", lambda: daily)
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "weather.db")

    ingest.build_db()
    ingest.build_db()  # second run must not raise or duplicate

    conn = sqlite3.connect(tmp_path / "weather.db")
    try:
        assert conn.execute("SELECT COUNT(*) FROM observation_daily").fetchone()[0] == 3 * 9
    finally:
        conn.close()
