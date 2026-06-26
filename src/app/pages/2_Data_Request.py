"""Data Request — optional page (themed placeholder).

Documents the UPLB-NAS station data request and the Open-Meteo → station swap
plan (Phase 8).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import streamlit as st

from src.app import _theme

_theme.setup("Data Request", page_icon="📨")
_theme.header(
    "📨 Data Request",
    "UPLB-NAS station data request and the Open-Meteo → station swap (Phase 8).",
)

st.info("Optional page. Documents the UPLB-NAS station data request (Phase 8).")
