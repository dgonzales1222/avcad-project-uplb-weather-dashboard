"""General Weather page — the dashboard landing page (Phase 4).

Reads ONLY from data/weather.db: latest readings (with a feels-like heat index),
interactive time-series (selectable year, resolution, and parameters), and
monthly/annual climatology.

Run with:  streamlit run src/app/Home.py
"""
import calendar
import sys
from pathlib import Path

# Streamlit runs this file directly and puts its own folder on sys.path, so add
# the project root to make `import config` (and `src...`) resolve.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import config
from src.app import _theme
from src.db import queries
from src.features import heat_index

_theme.setup("UPLB-NAS Weather Dashboard")

# Chartable parameter groups: (label, columns, kind).
PARAMETERS = [
    ("Temperature", ["max_temp", "mean_temp", "min_temp"], "temp"),
    ("Rainfall", ["precipitation"], "bar"),
    ("Relative humidity", ["relative_humidity"], "line"),
    ("Wind speed", ["wind_speed"], "line"),
    ("Station pressure", ["station_pressure"], "line"),
    ("Wet-bulb temperature", ["wet_bulb_temp"], "line"),
]
LINE_COLORS = {
    "relative_humidity": "#10b981", "wind_speed": "#f59e0b",
    "station_pressure": "#8b5cf6", "wet_bulb_temp": "#06b6d4",
}
# Per-variable aggregation when resampling to a coarser resolution.
AGG = {
    "max_temp": "max", "min_temp": "min", "mean_temp": "mean",
    "wet_bulb_temp": "mean", "relative_humidity": "mean",
    "precipitation": "sum", "wind_speed": "mean",
    "wind_direction": "mean", "station_pressure": "mean",
}
# PAGASA danger-band colors for the feels-like badge.
BAND_COLORS = {
    "Not hazardous": "#64748b", "Caution": "#ca8a04",
    "Extreme Caution": "#f59e0b", "Danger": "#ef4444",
    "Extreme Danger": "#b91c1c",
}


@st.cache_data
def load():
    return queries.load_daily()


@st.cache_data
def units():
    return queries.variable_units()


@st.cache_data
def station():
    return queries.station_info()


# --- Guard: the database must be built first --------------------------------
if not config.DB_PATH.exists():
    _theme.header("General Weather — UPLB-NAS")
    st.error(
        "Database not found. Build it first:\n\n```\npython -m src.data.ingest\n```"
    )
    st.stop()

daily = load()
unit = units()
info = station()


def u(name: str) -> str:
    """Unit suffix for a variable, e.g. ' (°C)'."""
    return f" ({unit.get(name, '')})" if unit.get(name) else ""


# --- Header -----------------------------------------------------------------
_theme.header(
    "🌡️ General Weather — UPLB-NAS",
    f"{info.get('name', '—')} ({info.get('source', 'open-meteo')}) · "
    f"{config.LAT}, {config.LON} · {config.TZ}",
)

# --- Sidebar: controls ------------------------------------------------------
y_min, y_max = int(daily.index.year.min()), int(daily.index.year.max())

st.sidebar.markdown("### ⚙️ Weather Controls")
st.sidebar.caption("Configure the view below.")
st.sidebar.success(f"Daily records · {y_min}–{y_max} · UPLB / Los Baños")

st.sidebar.subheader("View")
year_choice = st.sidebar.selectbox(
    "Year", ["All years"] + [str(y) for y in range(y_max, y_min - 1, -1)]
)
resolution = st.sidebar.radio("Resolution", ["Daily", "Monthly", "Yearly"], horizontal=True)

st.sidebar.subheader("Parameters")
chosen = [p for p in PARAMETERS if st.sidebar.checkbox(p[0], value=True, key=p[0])]

# Year filter applies to the time-series view.
if year_choice == "All years":
    ts, span = daily, f"{y_min}–{y_max}"
else:
    ts, span = daily[daily.index.year == int(year_choice)], year_choice

# Resample to the chosen resolution for the time-series charts.
if resolution == "Daily":
    view = ts
else:
    rule = "MS" if resolution == "Monthly" else "YS"
    view = ts.resample(rule).agg(AGG)

# Current-selection summary card.
with st.sidebar.container(border=True):
    st.markdown("**Current selection**")
    st.markdown(
        f"- **Source:** {info.get('source', 'open-meteo')}\n"
        f"- **Year:** {year_choice}\n"
        f"- **Resolution:** {resolution}\n"
        f"- **Parameters:** {len(chosen)} of {len(PARAMETERS)}\n"
        f"- **Record:** {y_min}–{y_max}"
    )

# --- Latest readings --------------------------------------------------------
latest = daily.iloc[-1]
prev = daily.iloc[-2]


def d(name: str) -> str:
    """Signed day-over-day delta for a variable."""
    return f"{latest[name] - prev[name]:+.1f}"


with st.container(border=True):
    st.subheader(f"Latest readings — {daily.index[-1].date()}")

    # Feels-like heat index (daily max temp + daily mean RH) + PAGASA band.
    hi_c = heat_index.heat_index_c(latest["max_temp"], latest["relative_humidity"])
    band = heat_index.classify(hi_c)
    st.markdown(
        f"<div style='font-size:0.95rem;margin-bottom:0.5rem'>"
        f"🌡️ <b>Heat index</b> (feels-like, daily max): "
        f"<b>{hi_c:.1f} °C</b>&nbsp;"
        f"<span style='background:{BAND_COLORS.get(band, '#64748b')};color:#fff;"
        f"padding:.1rem .5rem;border-radius:8px;font-size:.8rem'>{band}</span></div>",
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Max temp{u('max_temp')}", f"{latest['max_temp']:.1f}", d("max_temp"), delta_color="off")
    c1.metric(f"Min temp{u('min_temp')}", f"{latest['min_temp']:.1f}", d("min_temp"), delta_color="off")
    c2.metric(f"Mean temp{u('mean_temp')}", f"{latest['mean_temp']:.1f}", d("mean_temp"), delta_color="off")
    c2.metric(f"Humidity{u('relative_humidity')}", f"{latest['relative_humidity']:.0f}", d("relative_humidity"), delta_color="off")
    c3.metric(f"Rainfall{u('precipitation')}", f"{latest['precipitation']:.1f}")
    c3.metric(f"Wind speed{u('wind_speed')}", f"{latest['wind_speed']:.1f}", d("wind_speed"), delta_color="off")
    c4.metric(f"Pressure{u('station_pressure')}", f"{latest['station_pressure']:.0f}", d("station_pressure"), delta_color="off")
    c4.metric(f"Wet bulb{u('wet_bulb_temp')}", f"{latest['wet_bulb_temp']:.1f}", d("wet_bulb_temp"), delta_color="off")


# --- Time series (selected year, resolution, parameters) --------------------
def build_chart(label, cols, kind):
    fig = go.Figure()
    if kind == "temp":
        for col, nm, clr in zip(cols, ["Max", "Mean", "Min"], ["#ef4444", "#f59e0b", "#3b82f6"]):
            fig.add_trace(go.Scatter(x=view.index, y=view[col], name=nm, mode="lines", line_color=clr))
        fig.update_layout(
            xaxis_rangeslider_visible=(resolution == "Daily" and year_choice == "All years"),
        )
    elif kind == "bar":
        fig.add_trace(go.Bar(x=view.index, y=view[cols[0]], marker_color="#3b82f6"))
    else:
        fig.add_trace(go.Scatter(
            x=view.index, y=view[cols[0]], mode="lines",
            line_color=LINE_COLORS.get(cols[0], "#3b82f6"),
        ))
    fig.update_layout(title=label, yaxis_title=u(cols[0]).strip(" ()"))
    return _theme.style_fig(fig)


with st.container(border=True):
    st.subheader(f"Time series — {span} · {resolution.lower()}")
    if not chosen:
        st.info("Select at least one parameter in the sidebar to display charts.")
    else:
        for label, cols, kind in chosen:
            st.plotly_chart(build_chart(label, cols, kind), width="stretch", config=_theme.CHART_CONFIG)

# --- Climatology (long-term normals over the full record) -------------------
with st.container(border=True):
    st.subheader("Climatology")
    st.caption(f"Long-term normals over the full record ({y_min}–{y_max}).")
    col_m, col_a = st.columns(2)

    monthly = daily.groupby(daily.index.month).agg(
        mean_temp=("mean_temp", "mean"), precipitation=("precipitation", "mean")
    )
    month_labels = [calendar.month_abbr[m] for m in monthly.index]
    m_fig = make_subplots(specs=[[{"secondary_y": True}]])
    m_fig.add_trace(go.Bar(x=month_labels, y=monthly["precipitation"], name="Rain",
                           marker_color="#93c5fd"), secondary_y=False)
    m_fig.add_trace(go.Scatter(x=month_labels, y=monthly["mean_temp"], name="Temp",
                               line_color="#ef4444"), secondary_y=True)
    m_fig.update_layout(title="Monthly normals")
    m_fig.update_yaxes(title_text=f"Mean rain{u('precipitation')}", secondary_y=False)
    m_fig.update_yaxes(title_text=f"Mean temp{u('mean_temp')}", secondary_y=True)
    col_m.plotly_chart(_theme.style_fig(m_fig, height=340), width="stretch", config=_theme.CHART_CONFIG)

    annual = daily.groupby(daily.index.year).agg(
        mean_temp=("mean_temp", "mean"), precipitation=("precipitation", "sum")
    )
    a_fig = make_subplots(specs=[[{"secondary_y": True}]])
    a_fig.add_trace(go.Bar(x=annual.index, y=annual["precipitation"], name="Rain",
                           marker_color="#93c5fd"), secondary_y=False)
    a_fig.add_trace(go.Scatter(x=annual.index, y=annual["mean_temp"], name="Temp",
                               line_color="#ef4444"), secondary_y=True)
    a_fig.update_layout(title="Annual summary")
    a_fig.update_yaxes(title_text=f"Total rain{u('precipitation')}", secondary_y=False)
    a_fig.update_yaxes(title_text=f"Mean temp{u('mean_temp')}", secondary_y=True)
    col_a.plotly_chart(_theme.style_fig(a_fig, height=340), width="stretch", config=_theme.CHART_CONFIG)
