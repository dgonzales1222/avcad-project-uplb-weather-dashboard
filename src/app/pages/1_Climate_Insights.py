"""Climate Insights (Heat Index) — placeholder (themed).

Built out in Phase 5 (multi-year heat index trend with PAGASA danger bands,
calendar heatmap, >41°C day counter) and Phase 6 (Prophet forecast + metrics).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import streamlit as st

from src.app import _theme

_theme.setup("Climate Insights", page_icon="📈")
_theme.header(
    "📈 Climate Insights — Heat Index",
    "Multi-year heat-index trends, PAGASA/NWS danger bands, and forecast.",
)

st.info("Placeholder. Built in Phase 5 (trends + danger bands) and Phase 6 (forecast).")
