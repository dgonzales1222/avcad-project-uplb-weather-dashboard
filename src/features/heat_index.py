"""NWS heat index + PAGASA danger-band classification — the project's core math.

The heat index ("apparent temperature") combines air temperature and relative
humidity. This module implements the U.S. National Weather Service algorithm:

  1. Steadman's simple form, used when the result is below ~80 °F.
  2. The Rothfusz multiple-regression equation otherwise.
  3. Two adjustments (very low and very high humidity).

Source: NWS Weather Prediction Center heat-index equation (Rothfusz 1990, Steadman
1979). ``classify()`` applies PAGASA's heat-index danger categories.

All functions are numpy-based, so they accept scalars OR array-likes (e.g. a pandas
Series) — Phase 5 applies them across the full daily record.

Public API:
    heat_index_f(temp_f, rh)   NWS heat index, input/output °F
    heat_index_c(temp_c, rh)   °C wrapper around heat_index_f
    classify(hi_c)             PAGASA danger band for a °C heat index
"""
from __future__ import annotations

import numpy as np

# Rothfusz regression coefficients (T and RH in °F and %).
_C = (
    -42.379, 2.04901523, 10.14333127, -0.22475541,
    -0.00683783, -0.05481717, 0.00122874, 0.00085282, -0.00000199,
)

# PAGASA heat-index danger bands as (lower_inclusive_°C, upper_exclusive_°C, label).
# Exposed so the Phase 5 chart can shade the same thresholds. "Danger" starts at
# 42 °C — i.e. the README's ">41 °C heat index" metric.
PAGASA_BANDS = (
    (float("-inf"), 27.0, "Not hazardous"),
    (27.0, 33.0, "Caution"),
    (33.0, 42.0, "Extreme Caution"),
    (42.0, 52.0, "Danger"),
    (52.0, float("inf"), "Extreme Danger"),
)


def _c_to_f(temp_c):
    return temp_c * 9.0 / 5.0 + 32.0


def _f_to_c(temp_f):
    return (temp_f - 32.0) * 5.0 / 9.0


def heat_index_f(temp_f, rh):
    """NWS heat index in °F from temperature (°F) and relative humidity (%).

    Accepts scalars or array-likes; returns a float for scalar input, else an
    ndarray.
    """
    T = np.asarray(temp_f, dtype=float)
    R = np.asarray(rh, dtype=float)

    # Steadman simple form (valid in the cooler / low-HI regime).
    simple = 0.5 * (T + 61.0 + (T - 68.0) * 1.2 + R * 0.094)

    # Rothfusz regression (used when the simple value averaged with T reaches 80 °F).
    roth = (
        _C[0] + _C[1] * T + _C[2] * R + _C[3] * T * R
        + _C[4] * T**2 + _C[5] * R**2 + _C[6] * T**2 * R
        + _C[7] * T * R**2 + _C[8] * T**2 * R**2
    )

    # Low-humidity adjustment: RH < 13% and 80 °F ≤ T ≤ 112 °F (subtracted).
    low_adj = ((13.0 - R) / 4.0) * np.sqrt(np.clip((17.0 - np.abs(T - 95.0)) / 17.0, 0.0, None))
    roth = roth - np.where((R < 13.0) & (T >= 80.0) & (T <= 112.0), low_adj, 0.0)

    # High-humidity adjustment: RH > 85% and 80 °F ≤ T ≤ 87 °F (added).
    high_adj = ((R - 85.0) / 10.0) * ((87.0 - T) / 5.0)
    roth = roth + np.where((R > 85.0) & (T >= 80.0) & (T <= 87.0), high_adj, 0.0)

    hi = np.where((simple + T) / 2.0 < 80.0, simple, roth)
    return float(hi) if np.ndim(temp_f) == 0 and np.ndim(rh) == 0 else hi


def heat_index_c(temp_c, rh):
    """NWS heat index in °C from temperature (°C) and relative humidity (%)."""
    return _f_to_c(heat_index_f(_c_to_f(np.asarray(temp_c, dtype=float)), rh))


def _classify_one(hi_c: float) -> str | None:
    if hi_c is None or (isinstance(hi_c, float) and np.isnan(hi_c)):
        return None
    for lower, upper, label in PAGASA_BANDS:
        if lower <= hi_c < upper:
            return label
    return None


def classify(hi_c):
    """PAGASA danger band for a °C heat index.

    Scalar in -> label (str) or None for NaN. Array-like in -> ndarray of labels.
    """
    if np.ndim(hi_c) == 0:
        return _classify_one(float(hi_c) if hi_c is not None else None)
    return np.array([_classify_one(float(x)) for x in np.asarray(hi_c, dtype=float)], dtype=object)
