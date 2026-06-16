"""General Weather page — placeholder (Phase 0 skeleton).

Phase 4 replaces this with the real General Weather dashboard, reading only from
the local SQLite database. For now it confirms the app runs and that project
config is importable.
"""
import sys
from pathlib import Path

# Streamlit runs this file directly and puts its own folder on sys.path, so add
# the project root to make `import config` (and `src...`) resolve.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import streamlit as st

import config

st.set_page_config(
    page_title="UPLB-NAS Weather Dashboard", page_icon="🌡️", layout="wide"
)

st.title("🌡️ UPLB-NAS Weather Data Dashboard")
st.caption(
    "Capstone — MS in Green Data Science, ISA–ULisboa · Danilo III O. Gonzales"
)

st.info(
    "Phase 0 skeleton. The General Weather page (Phase 4) and Climate Insights "
    "page (Phase 5) are not built yet."
)

with st.expander("Project configuration (from config.py)", expanded=True):
    st.write(
        {
            "Location": f"Los Baños / UPLB ({config.LAT}, {config.LON})",
            "Timezone": config.TZ,
            "Date range": f"{config.START} → {config.END}",
            "Database": str(config.DB_PATH),
            "Data source": "Open-Meteo (ERA5) — stand-in until UPLB-NAS arrives",
        }
    )

st.divider()
st.subheader("Build status")
st.markdown(
    "- ✅ **Phase 0** — project setup (you are here)\n"
    "- ⬜ Phase 1 — Open-Meteo ingestion\n"
    "- ⬜ Phase 2 — database schema + load\n"
    "- ⬜ Phase 3 — heat index module\n"
    "- ⬜ Phase 4 — General Weather page\n"
    "- ⬜ Phase 5 — Climate Insights / heat index page\n"
    "- ⬜ Phase 6 — Prophet forecast\n"
    "- ⬜ Phase 7 — polish + deploy"
)
