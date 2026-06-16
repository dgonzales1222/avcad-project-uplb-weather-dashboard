"""Project-wide constants — the single source of truth for location, date range,
and paths. Import as ``import config``.

Nothing downstream should hardcode these values; read them from here.
"""
from pathlib import Path

# --- Location: UPLB / Los Baños, Laguna, Philippines ---
LAT = 14.17
LON = 121.24
TZ = "Asia/Manila"

# --- 30-year window, mirroring the UPLB-NAS data request ---
START = "1996-01-01"
END = "2025-12-31"

# --- Paths (anchored to this file so the working directory doesn't matter) ---
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
DB_PATH = DATA_DIR / "weather.db"
