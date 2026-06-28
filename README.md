# AVCAD Project: UPLB Weather Data Dashboard

A relational database and public web dashboard for long-term weather observations from the
University of the Philippines Los Baños National Agromet Station (UPLB-NAS), Los Baños, Laguna.
The system supports a climate-change study centered on the heat index, incorporating multi-year
trend analysis and a short-term forecast.

This repository contains the work of a master's capstone project by Danilo III O. Gonzales,
MS in Green Data Science (Data Science in Agriculture, Food, Forest, and Environment),
Instituto Superior de Agronomia – Universidade de Lisboa (ISA–ULisboa).

## Data Source

The intended data source is the observational record of the UPLB National Agromet Station.
As these records are still being requested, the system is currently developed against the
Open-Meteo Historical Weather API (ERA5 reanalysis) as a representative stand-in. The data
access layer is deliberately isolated so that station records can be substituted without
modifying the database, analysis, or dashboard components.

## Objectives

1. Design a relational database for station information, instruments, and weather observations.
2. Develop a web-based dashboard presenting general weather summaries and a climate-change
   analysis of heat-index trends, together with a short-term forecast.
3. Deploy the system online using free hosting suitable for academic use.

## Features

- A relational SQLite database covering stations, variables, and observations.
- A General Weather page providing latest readings, interactive time-series charts for
  temperature, rainfall, humidity, and wind, monthly and annual climatology summaries, and
  CSV export.
- A Climate Insights page presenting a multi-year heat-index trend with PAGASA and U.S.
  National Weather Service danger bands, a calendar heatmap of dangerous days, an annual count
  of days exceeding a 41 °C heat index, and a 7–14 day forecast with accuracy metrics
  (MAE, RMSE).
- A modular data layer enabling a transition from Open-Meteo data to UPLB-NAS records without
  changes to downstream components.

## Technology Stack

Python 3.12 or later, with pandas for data processing, SQLite for storage, Dash and Plotly
for the web interface, a PyTorch LSTM for the short-term heat-index forecast, and the
openmeteo-requests client for data retrieval.

## Installation and Usage

```bash
git clone https://github.com/dgonzales1222/avcad-project-uplb-weather-dashboard.git
cd avcad-project-uplb-weather-dashboard

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

python -m src.data.ingest         # retrieve data and build the database (first run only)
python -m src.dashapp.app         # Dash app at http://localhost:8050
```

## Deployment

The app deploys to [Render](https://render.com) (free tier) via `render.yaml`. The forecast is
**precomputed offline** (`python -m src.models.precompute` → `src/dashapp/forecast_precomputed.json`)
so the deployed server is **torch-free**: it installs the slim `requirements-render.txt`, rebuilds the
database at build time (`python -m src.data.ingest`), and runs
`gunicorn src.dashapp.app:server`. Re-run the precompute step whenever the data is refreshed.

## System Architecture

```
Open-Meteo API ──fetch──> data/raw/ ──clean──> SQLite (data/weather.db) ──> Dash application
  (sources.py)                       (clean.py / ingest.py)                  (src/dashapp/)
```

> **Note:** `data/` — both the raw downloads (`data/raw/`) and the SQLite database
> (`data/weather.db`) — is git-ignored and stored only on the local machine. It is never
> committed to the repository; run the ingestion steps to regenerate it locally.

All external data access is confined to `src/data/sources.py`, and the dashboard reads only
from the local database. Substituting the UPLB-NAS records therefore requires changes only to
that module and a re-run of the ingestion process.

## Repository Structure

```
.
├── requirements.txt
├── data/                  Raw downloads and the SQLite database (excluded from version control)
├── src/
│   ├── data/              Data retrieval, cleaning, and ingestion
│   ├── db/                Relational schema
│   ├── features/          Heat-index computation (NWS formula and PAGASA bands)
│   ├── models/            Short-term forecasting (Prophet)
│   └── app/               Streamlit pages
└── tests/                 Unit tests for the heat-index computation
```

## Development Status

| Phase | Description                                   | Status      | Date of Completion|
|-------|-----------------------------------------------|-------------|------|
| 0     | Project setup and documentation               | Complete    |15/06/2026|
| 1     | Open-Meteo data ingestion                     | Complete    |16/06/2026|
| 2     | Relational database design and loading        | Completed    | 17/06/2026|
| 3     | Heat-index module with unit tests             | Completed     | 18/06/2026|
| 4     | General Weather page                          | Ongoing    |
| 5     | Climate Insights and heat-index page          | Pending     |
| 6     | Short-term forecast (Prophet)                 | Pending     |
| 7     | Refinement and deployment                     | Pending     |
| 8     | Integration of UPLB-NAS records               | Pending     |

## Data Attribution

Historical weather data are provided by Open-Meteo (ERA5 reanalysis) under its free,
non-commercial terms of use, and are to be replaced by records from the UPLB National Agromet
Station. The heat index is computed using the U.S. National Weather Service formula, and danger
classifications follow the categories defined by PAGASA.

## Author

**Danilo III O. Gonzales** <br>
MS in Green Data Science (Data Science in Agriculture, Food, Forest, and Environment) <br>
Instituto Superior de Agronomia – Universidade de Lisboa (ISA–ULisboa)

## License

CC BY 4.0 (Creative Commons Attribution 4.0 International) 
