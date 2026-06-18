# Heat Index Calculation

This document specifies the heat-index methodology used in the UPLB-NAS Weather Dashboard,
as implemented in [`src/features/heat_index.py`](../src/features/heat_index.py). The heat index
("apparent temperature") expresses how hot it *feels* by combining air temperature and relative
humidity. The dashboard uses the U.S. National Weather Service (NWS) operational algorithm and the
PAGASA danger-band classification.

## Inputs

| Symbol | Meaning | Unit |
|--------|---------|------|
| `T`  | Air (dry-bulb) temperature | °F (computation), °C (wrapper) |
| `RH` | Relative humidity | % |

## Algorithm

The NWS algorithm has two regimes plus two edge-case adjustments.

### 1. Simple (Steadman) form

A simpler formula is computed first; it is appropriate when the result is below ~80 °F, where the
full regression is not valid (Steadman, 1979a):

```
HI_simple = 0.5 × [ T + 61.0 + (T − 68.0) × 1.2 + RH × 0.094 ]
```

If the average of `HI_simple` and `T` is **below 80 °F**, this value is returned. Otherwise the
Rothfusz regression is applied.

### 2. Rothfusz regression

For the warm regime, the heat index is the multiple-regression fit of Rothfusz (1990) to Steadman's
tables:

```
HI = −42.379
     + 2.04901523 × T
     + 10.14333127 × RH
     −  0.22475541 × T × RH
     −  0.00683783 × T²
     −  0.05481717 × RH²
     +  0.00122874 × T² × RH
     +  0.00085282 × T × RH²
     −  0.00000199 × T² × RH²
```

with `T` in °F and `RH` in percent; `HI` is the apparent temperature in °F.

### 3. Adjustments (NWS WPC)

- **Low humidity** — when `RH < 13%` and `80 °F ≤ T ≤ 112 °F`, subtract:
  ```
  ADJ = [ (13 − RH) / 4 ] × √[ (17 − |T − 95|) / 17 ]
  ```
- **High humidity** — when `RH > 85%` and `80 °F ≤ T ≤ 87 °F`, add:
  ```
  ADJ = [ (RH − 85) / 10 ] × [ (87 − T) / 5 ]
  ```

### 4. Celsius conversion

The project works in °C, so the wrapper converts both ways around the °F computation:

```
HI(°C) = ( HI_f(T × 9/5 + 32, RH) − 32 ) × 5/9
```

## PAGASA danger-band classification

Heat-index values (in °C) are categorized with the bands published by PAGASA. "Danger" begins at
42 °C — i.e. the project's ">41 °C heat index" metric.

| Heat index (°C) | Category | Health effect (PAGASA) |
|-----------------|----------|------------------------|
| < 27 | Not hazardous | — |
| 27 – 32 | Caution | Fatigue possible with prolonged exposure |
| 33 – 41 | Extreme Caution | Heat cramps and heat exhaustion possible |
| 42 – 51 | Danger | Heat cramps/exhaustion likely; heat stroke possible |
| ≥ 52 | Extreme Danger | Heat stroke imminent |

## Implementation reference

| Function (`src/features/heat_index.py`) | Role |
|------------------------------------------|------|
| `heat_index_f(temp_f, rh)` | Full NWS algorithm (simple form → Rothfusz → adjustments), °F |
| `heat_index_c(temp_c, rh)` | °C wrapper around `heat_index_f` |
| `classify(hi_c)` | Maps a °C heat index to its PAGASA band |
| `PAGASA_BANDS` | Band thresholds/labels (reused by the Climate Insights chart) |

All functions are vectorized (NumPy), accepting scalars or array-likes (e.g. a pandas Series).

## Methodological notes

- The NWS heat index is defined for **shade** conditions; exposure to full sunshine can raise the
  apparent temperature by up to ~8 °C (15 °F).
- The UPLB-NAS station provides **daily** values only, so the dashboard computes the daily heat
  index from **daily maximum temperature and daily mean relative humidity**. Because humidity is
  generally lowest at the time of peak temperature, pairing `Tmax` with mean `RH` tends to
  **overestimate** the heat index; this assumption is stated wherever the metric is reported.

## References

Department of Science and Technology. (2025). *iHeatMap, an online monitoring guide for heat index.*
https://www.dost.gov.ph/knowledge-resources/news/86-2025-news/3971-iheatmap-an-online-monitoring-guide-for-heat-index.html

National Weather Service. (n.d.). *The heat index equation.* NOAA Weather Prediction Center.
Retrieved June 17, 2026, from https://www.wpc.ncep.noaa.gov/html/heatindex_equation.shtml

Philippine Atmospheric, Geophysical and Astronomical Services Administration. (n.d.). *Heat index.*
Department of Science and Technology – PAGASA. Retrieved June 17, 2026, from
https://www.pagasa.dost.gov.ph/

Rothfusz, L. P. (1990). *The heat index "equation" (or, more than you ever wanted to know about heat
index)* (Technical Attachment No. SR 90-23). National Weather Service, Southern Region Headquarters.
https://www.weather.gov/media/ffc/ta_htindx.PDF

Steadman, R. G. (1979a). The assessment of sultriness. Part I: A temperature–humidity index based on
human physiology and clothing science. *Journal of Applied Meteorology, 18*(7), 861–873.
https://doi.org/10.1175/1520-0450(1979)018%3C0861:TAOSPI%3E2.0.CO;2

Steadman, R. G. (1979b). The assessment of sultriness. Part II: Effects of wind, extra radiation and
barometric pressure on apparent temperature. *Journal of Applied Meteorology, 18*(7), 874–885.
https://doi.org/10.1175/1520-0450(1979)018%3C0874:TAOSPI%3E2.0.CO;2
