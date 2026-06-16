"""ALL external data access lives here (docs/PROJECT_CONTEXT.md rule).

Open-Meteo now; the UPLB-NAS station loader is added in Phase 8. Nothing else
in the codebase should fetch external data — everything downstream reads the
cleaned SQLite database (data/weather.db).

To implement:
    Phase 1:  fetch_openmeteo_hourly(start, end)
              fetch_openmeteo_daily(start, end)
    Phase 8:  load_uplb_nas(path)
"""
