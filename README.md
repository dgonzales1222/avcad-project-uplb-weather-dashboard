# UPLB Weather Data Dashboard

A relational database and public web dashboard for long-term weather observations from the
University of the Philippines Los Baños National Agromet Station (UPLB-NAS), Los Baños, Laguna.
The system supports a climate-change study centered on the heat index, incorporating multi-year
trend analysis and a short-term forecast.

This repository contains the work of a master's capstone project by Danilo III O. Gonzales,
MS in Green Data Science (Data Science in Agriculture, Food, Forest, and Environment),
Instituto Superior de Agronomia – Universidade de Lisboa (ISA–ULisboa).

## Live Preview

A static preview of the dashboard design is hosted on GitHub Pages:

**https://dgonzales1222.github.io/uplb-weather-dashboard/**

> **Disclaimer.** GitHub Pages only serves static files, so this link shows the dashboard’s design, not the live application. The charts here are mock-ups, not figures generated from the database. The interactive dashboard — with real Open-Meteo data, live charts, and the heat-index forecast — is the Dash app in this repository. Run it locally or deploy it to Render. The same UPLB design is implemented in that app.

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
- A General Weather page providing latest readings (with a feels-like heat index), interactive
  time-series charts for temperature, rainfall, humidity, wind, pressure, and wet-bulb
  temperature, and monthly and annual climatology summaries.
- A Climate Insights page presenting a multi-year heat-index trend with PAGASA danger bands, a
  calendar heatmap of the daily heat index, an annual count of days exceeding a 41 °C heat
  index, and a 7–14 day LSTM forecast (drawn as a Monte-Carlo trajectory) with backtest accuracy
  metrics (MAE, RMSE).
- A custom UPLB-branded interface — an "editorial" liquid-glass theme with light/dark mode, a
  feels-like danger gauge, and a campus-photo footer — built directly in Dash.
- A modular data layer enabling a transition from Open-Meteo data to UPLB-NAS records without
  changes to downstream components.

## Technology Stack

Python 3.12 or later, with pandas for data processing, SQLite for storage, Dash and Plotly
for the web interface, a PyTorch LSTM for the short-term heat-index forecast, and the
openmeteo-requests client for data retrieval. The interface is a custom UPLB-branded design
implemented with Dash components and CSS (Dash Bootstrap Components is used only for layout).

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

## Documentation & Notebooks

- [`docs/heat_index_calculation.md`](docs/heat_index_calculation.md) — heat-index formula and
  PAGASA danger bands, with sources.
- [`docs/lstm_forecast.md`](docs/lstm_forecast.md) — short-term LSTM forecast methodology.
- [`notebooks/lstm_forecast_development.ipynb`](notebooks/lstm_forecast_development.ipynb) —
  end-to-end LSTM development with a rigorous evaluation (baselines, rolling-origin backtest, MASE,
  skill score, Diebold–Mariano). It reads the database directly, and its final cell regenerates the
  forecast artifact the live app serves.

The notebook needs a few extra libraries (not required to run or deploy the app); install them
alongside the main requirements:

```bash
pip install -r requirements.txt -r requirements-notebook.txt
jupyter lab notebooks/lstm_forecast_development.ipynb
```

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
├── requirements.txt          Full dependencies for local development (includes PyTorch)
├── requirements-render.txt   Slim, torch-free dependencies used for deployment
├── requirements-notebook.txt Extra dependencies for the analysis notebook
├── render.yaml               Render deployment blueprint
├── data/                     Raw downloads and the SQLite database (excluded from version control)
├── docs/                     Methodology docs (heat index, LSTM forecast)
├── notebooks/                Jupyter notebook — LSTM development & evaluation
├── src/
│   ├── data/                 Data retrieval, cleaning, and ingestion
│   ├── db/                   Relational schema and read-only queries
│   ├── features/             Heat-index computation (NWS formula and PAGASA bands)
│   ├── models/               Short-term forecast (PyTorch LSTM) and offline precompute
│   └── dashapp/              Dash web app — pages, theme, and assets (CSS, logos, icons, fonts)
└── tests/                    Unit and application smoke tests
```

## Development Status

| Phase | Description                                   | Status      | Date of Completion |
|-------|-----------------------------------------------|-------------|--------------------|
| 0     | Project setup and documentation               | Complete    | 15/06/2026 |
| 1     | Open-Meteo data ingestion                     | Complete    | 16/06/2026 |
| 2     | Relational database design and loading        | Complete    | 17/06/2026 |
| 3     | Heat-index module with unit tests             | Complete    | 18/06/2026 |
| 4     | General Weather page (Dash)                   | Complete    | 21/06/2026 |
| 5     | Climate Insights and heat-index page          | Complete    | 24/06/2026 |
| 6     | Short-term forecast (PyTorch LSTM)            | Complete    | 27/06/2026 |
| 7     | Interface design and deployment (Render)      | Ongoing     | —          |
| 8     | Integration of UPLB-NAS records               | Pending     | —          |

> **Status (28/06/2026):** Phases 0–6 complete. The dashboard is built on **Dash/Plotly**
> (migrated from the originally planned Streamlit), and the short-term forecast uses a **PyTorch
> LSTM** (replacing the originally planned Prophet). Phase 7 is in progress: the UPLB-branded
> **editorial / liquid-glass interface** has been implemented, and the app is deployment-ready for
> **Render** (torch-free server via a precomputed forecast) — only the live deploy remains.
> Phase 8 (real UPLB-NAS records) is next.

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
