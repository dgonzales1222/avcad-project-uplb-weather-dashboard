"""Shared UI theme for the dashboard — applied app-wide (Phase 4).

Every page calls `setup(...)` first (it runs st.set_page_config and injects the
CSS), then `header(...)` for the minimal top banner. This keeps a consistent
card-based look across all pages with one source of styling.
"""
import base64
from pathlib import Path

import streamlit as st

_CSS = """
<style>
:root {
  --brand:   #155e75;   /* deep teal — minimal weather palette */
  --brand-2: #0e4254;
  --muted:   #64748b;
  --card-border: #e7edf2;
}
/* trim top padding and hide default chrome for a cleaner shell */
.block-container { padding-top: 1.4rem; padding-bottom: 2rem; }
#MainMenu, footer { visibility: hidden; }

/* top header banner — UP maroon -> green, with title + logo slots */
.app-header {
  background: linear-gradient(120deg, #7b1113 0%, #15402c 100%);
  color: #fff; padding: 1rem 1.3rem; border-radius: 14px;
  margin-bottom: 1.1rem; box-shadow: 0 3px 10px rgba(15,23,42,.15);
}
.app-header .row { display: flex; align-items: center; gap: 1rem; }
.app-header .txt { flex: 1; }
.app-header .ttl { font-size: 1.55rem; font-weight: 700; line-height: 1.15; }
.app-header .sub { color: rgba(255,255,255,.85); font-size: .9rem; margin-top: .25rem; }
.app-header .logos { display: flex; gap: .55rem; }
.app-header .logo-box {
  width: 54px; height: 54px; border-radius: 10px;
  border: 1.5px dashed rgba(255,255,255,.55);
  display: flex; align-items: center; justify-content: center;
  font-size: .58rem; letter-spacing: .06em; color: rgba(255,255,255,.8);
  background: rgba(255,255,255,.08); text-align: center;
}
.app-header .logo-img { height: 54px; width: auto; border-radius: 8px;
  background: #fff; padding: 3px; }

/* card panels — st.container(border=True) */
div[data-testid="stVerticalBlockBorderWrapper"] {
  background: #fff; border: 1px solid var(--card-border) !important;
  border-radius: 16px; box-shadow: 0 1px 6px rgba(15,23,42,.05);
}
/* metric tiles */
div[data-testid="stMetric"] {
  background: #f8fafc; border: 1px solid #eef2f6;
  border-radius: 12px; padding: .55rem .8rem;
}
/* rounded callout boxes */
div[data-testid="stAlert"] { border-radius: 12px; }
/* sidebar section labels (st.subheader) */
section[data-testid="stSidebar"] h3 {
  text-transform: uppercase; letter-spacing: .05em;
  font-size: .78rem; color: var(--muted); margin-top: .5rem;
}
</style>
"""


def setup(page_title: str, page_icon: str = "🌡️") -> None:
    """Configure the page and inject the shared theme CSS. Call first."""
    st.set_page_config(page_title=page_title, page_icon=page_icon, layout="wide")
    st.markdown(_CSS, unsafe_allow_html=True)


def _logo_html(src) -> str:
    """An <img> for a logo file if it exists, else a dashed 'LOGO' placeholder."""
    if src:
        p = Path(src)
        if p.exists():
            data = base64.b64encode(p.read_bytes()).decode()
            ext = (p.suffix.lstrip(".") or "png").lower()
            mime = "svg+xml" if ext == "svg" else ext
            return f'<img class="logo-img" src="data:image/{mime};base64,{data}"/>'
    return '<div class="logo-box">LOGO</div>'


def header(title: str, subtitle: str = "", logo=None, partner_logos=None) -> None:
    """Render the top header: a left logo slot, the title, and right logo slots.

    Pass `logo` (a file path) for the primary mark and `partner_logos` (a list of
    paths) for the right-hand marks. With no paths, dashed 'LOGO' placeholders show
    so you can see where logos will go and drop them in later.
    """
    left = _logo_html(logo)
    if partner_logos is None:
        right = '<div class="logo-box">LOGO</div><div class="logo-box">LOGO</div>'
    else:
        right = "".join(_logo_html(p) for p in partner_logos)
    st.markdown(
        f'<div class="app-header"><div class="row">{left}'
        f'<div class="txt"><div class="ttl">{title}</div>'
        f'<div class="sub">{subtitle}</div></div>'
        f'<div class="logos">{right}</div></div></div>',
        unsafe_allow_html=True,
    )


# Shared Plotly look. Use after building traces; pass config=CHART_CONFIG to
# st.plotly_chart to drop the modebar.
CHART_CONFIG = {"displayModeBar": False}


def style_fig(fig, height: int = 320):
    """Apply the minimal, card-friendly chart style and return the figure."""
    fig.update_layout(
        template="plotly_white", height=height,
        margin=dict(l=10, r=10, t=44, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified", font=dict(size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#eef2f6", zeroline=False)
    return fig
