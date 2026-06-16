"""Ingestion pipeline: raw -> clean -> SQLite (data/weather.db).

Implemented in Phase 2. Run with:  python -m src.data.ingest
Seeds the station table with the Open-Meteo source; the UPLB-NAS row is added
in Phase 8.
"""
