# Short-Term Heat-Index Forecast (LSTM)

This document specifies the short-term forecasting methodology used in the UPLB-NAS Weather
Dashboard, as implemented in [`src/models/forecast.py`](../src/models/forecast.py). The model
produces a 7- to 14-day projection of the **daily heat index** together with an uncertainty band
and backtest accuracy metrics. It is a **statistical** seasonal/trend estimate — not a
meteorological (numerical weather prediction) forecast.

## Objective

Given the historical daily heat-index series, estimate the next `H` days (`H ∈ {7, 14}`). The
forecast is shown on the Climate Insights page
([`src/dashapp/pages/climate_insights.py`](../src/dashapp/pages/climate_insights.py)) with a
representative trajectory, a 5–95 % uncertainty band, and the backtest MAE and RMSE.

## Input series

The target is the daily heat index in °C, derived from daily maximum temperature and daily mean
relative humidity (see [`heat_index_calculation.md`](heat_index_calculation.md) and
[`src/dashapp/data.py`](../src/dashapp/data.py) → `heat_index_daily`). Pairing daily *maximum*
temperature with daily *mean* relative humidity tends to **overestimate** the heat index, and the
forecast inherits this bias.

## Model

A univariate **Long Short-Term Memory (LSTM)** network (Hochreiter & Schmidhuber, 1997),
implemented in PyTorch (Paszke et al., 2019):

```
LSTM(input_size = 3, hidden_size = 48, batch_first = True)  →  Linear(48 → 1)
```

The network reads a fixed-length window of the recent past and predicts the next day's (scaled)
heat index from the LSTM's last-timestep hidden state.

### Features (3 per timestep)

| Feature | Definition | Purpose |
|---------|-----------|---------|
| Scaled heat index | min–max scaled daily HI, `(x − min) / (max − min)` | the autoregressive signal |
| `sin(2π · DOY / 365)` | day-of-year sine | annual seasonality (cyclic encoding) |
| `cos(2π · DOY / 365)` | day-of-year cosine | annual seasonality |

Encoding the day of year as a sine/cosine pair makes the seasonal phase continuous (Dec 31 and
Jan 1 are adjacent) and is **known for future dates**, so it can be supplied during recursive
forecasting.

### Hyperparameters

| Symbol | Value | Meaning |
|--------|-------|---------|
| `LOOKBACK` | 45 | input window length (days) |
| `UNITS` | 48 | LSTM hidden units |
| `EPOCHS` | 40 (max) | training epochs, with early stopping |
| `MAX_TRAIN_DAYS` | 3650 | most recent ~10 years used for training |
| `_BATCH` | 32 | mini-batch size |
| `_LR` | 0.01 | Adam learning rate |
| `SEED` | 42 | RNG seed (reproducibility) |
| `N_SIMS` | 400 | Monte-Carlo sample paths (see below) |

These were chosen with a rolling backtest; a longer lookback, a larger network, and more history
each lowered the 14-day error.

## Preprocessing

1. Drop missing values and keep the most recent `MAX_TRAIN_DAYS` observations.
2. **Min–max scale** the heat index to `[0, 1]` (scaling parameters stored for inverse transform).
3. Append the two day-of-year features.
4. Build overlapping windows: each training example is `LOOKBACK` consecutive days of the 3 features
   (input) paired with the next day's scaled heat index (target).

## Training

- **Optimizer:** Adam (Kingma & Ba, 2015), learning rate 0.01.
- **Loss:** mean squared error.
- **Batching:** shuffled mini-batches of 32.
- **Early stopping:** training halts when the epoch loss fails to improve by `1e-4` for 3
  consecutive epochs (cap 40 epochs).
- **Device:** Apple-Silicon GPU (Metal/MPS) when available, otherwise CPU.
- After training, the **residual standard deviation** (observed − fitted, in °C) is retained to
  scale the forecast uncertainty.

> **Note.** PyTorch is used rather than TensorFlow/Keras: `model.fit` deadlocked at 0 % CPU on
> macOS arm64 for the real-data sizes, whereas PyTorch trains the full series in a few seconds.

## Forecasting

### Deterministic (mean) forecast

The model is rolled forward **recursively** (Hyndman & Athanasopoulos, 2021, §12.4): predict day
*t+1*, append that prediction (with the known future day-of-year features) to the input window,
slide the window forward, and repeat for `H` steps. Because an MSE-trained model predicts the
*conditional mean*, this trajectory is smooth — daily weather noise `H` days out is not
predictable, so the optimal point forecast is essentially a smooth seasonal/trend curve. This mean
forecast is what the **backtest metrics** evaluate.

### Monte-Carlo simulated trajectory (displayed line)

A smooth point forecast looks like a flat line, which obscures the day-to-day character of the
series. To show a *plausible* trajectory, the model is instead simulated `N_SIMS` times
(Hyndman & Athanasopoulos, 2021, §5.5 — simulation/bootstrap prediction paths):

1. At each step, add a random draw from the residual distribution, `N(0, σ_resid)`, to the
   prediction **before** feeding it back. Propagating noise through the recursion yields paths with
   realistic daily variability and a spread that **widens with the horizon**.
2. **Day 1 is anchored** to the deterministic prediction (no noise on the first step) so the
   trajectory joins the observed series continuously and the band fans out from there.
3. The **displayed line** (`yhat`) is the sample path whose mean level is closest to the ensemble
   mean — central, but with realistic texture.
4. The **uncertainty band** (`yhat_lower`, `yhat_upper`) is the 5th–95th percentile across the
   `N_SIMS` paths.

The Monte-Carlo path is illustrative of plausible variability; it is **not** a per-day prediction,
and it does not change the reported accuracy (which is measured on the deterministic mean forecast).

## Evaluation (backtest)

A hold-out backtest (`backtest` in `forecast.py`) sets aside the last `H` days, trains on the
remainder, produces the deterministic recursive forecast, and reports:

- **MAE** — mean absolute error (°C)
- **RMSE** — root-mean-square error (°C)

Indicative results on the Open-Meteo (ERA5) stand-in series (1996–2025):

| Horizon | MAE (°C) | RMSE (°C) |
|---------|----------|-----------|
| 7 days  | ≈ 2.44 | ≈ 2.68 |
| 14 days | ≈ 2.39 | ≈ 2.78 |

## Deployment

Training requires PyTorch, which is too heavy for the free-tier server. The forecast is therefore
**precomputed offline** ([`src/models/precompute.py`](../src/models/precompute.py) →
[`src/dashapp/forecast_precomputed.json`](../src/dashapp/forecast_precomputed.json)) for both
horizons. At runtime the app reads this JSON artifact and never imports PyTorch, keeping the
deployed server lightweight. Re-run `python -m src.models.precompute` whenever the data is
refreshed.

## Limitations

- It is a **statistical** seasonal/trend estimate, not a meteorological forecast; it cannot
  anticipate specific weather events.
- The optimal point forecast is smooth; genuine day-to-day swings several days out are
  unpredictable. The wavy displayed line is a **plausible simulation**, not a daily prediction.
- The forecast inherits the daily-max-temperature + daily-mean-relative-humidity **overestimation**
  of the heat index.
- It is trained on the Open-Meteo (ERA5) **stand-in** for a single grid point; values will be
  re-fitted once UPLB-NAS station records are integrated.

## Implementation reference

- Model, training, recursive/Monte-Carlo forecasting, and backtest:
  [`src/models/forecast.py`](../src/models/forecast.py)
- Offline precomputation: [`src/models/precompute.py`](../src/models/precompute.py)
- Caching / artifact loading: [`src/dashapp/data.py`](../src/dashapp/data.py)
- Presentation (trajectory, band, metrics, horizon toggle):
  [`src/dashapp/pages/climate_insights.py`](../src/dashapp/pages/climate_insights.py)

## References

Hochreiter, S., & Schmidhuber, J. (1997). Long short-term memory. *Neural Computation, 9*(8),
1735–1780. https://doi.org/10.1162/neco.1997.9.8.1735

Hyndman, R. J., & Athanasopoulos, G. (2021). *Forecasting: Principles and practice* (3rd ed.).
OTexts. https://otexts.com/fpp3/

Kingma, D. P., & Ba, J. (2015). Adam: A method for stochastic optimization. *3rd International
Conference on Learning Representations (ICLR).* https://arxiv.org/abs/1412.6980

Paszke, A., Gross, S., Massa, F., Lerer, A., Bradbury, J., Chanan, G., Killeen, T., Lin, Z.,
Gimelshein, N., Antiga, L., Desmaison, A., Köpf, A., Yang, E., DeVito, Z., Raison, M., Tejani, A.,
Chilamkurthy, S., Steiner, B., Fang, L., … Chintala, S. (2019). PyTorch: An imperative style,
high-performance deep learning library. *Advances in Neural Information Processing Systems, 32*,
8024–8035. https://arxiv.org/abs/1912.01703
