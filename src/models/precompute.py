"""Precompute the LSTM heat-index forecast to a committed JSON artifact — Phase 7.

The deployed (torch-free) server reads this instead of training the model. Run
locally after refreshing the data:

    python -m src.models.precompute

Writes src/dashapp/forecast_precomputed.json with the forecast + MAE/RMSE for each
horizon the dashboard offers (7 and 14 days).
"""
import json
from pathlib import Path

from src.dashapp import data
from src.models import forecast

OUT = Path(__file__).resolve().parents[1] / "dashapp" / "forecast_precomputed.json"
HORIZONS = (7, 14)


def main():
    series = data.heat_index_daily()["hi_c"]
    if series.empty:
        raise SystemExit("No data — build the database first: python -m src.data.ingest")

    blob = {}
    for h in HORIZONS:
        fc = forecast.fit_forecast(series, h)
        metrics = forecast.backtest(series, h)
        blob[str(h)] = {
            "forecast": [
                {"ds": d.strftime("%Y-%m-%d"), "yhat": round(float(y), 3),
                 "yhat_lower": round(float(lo), 3), "yhat_upper": round(float(up), 3)}
                for d, y, lo, up in zip(fc["ds"], fc["yhat"],
                                        fc["yhat_lower"], fc["yhat_upper"])
            ],
            "metrics": {"mae": round(metrics["mae"], 3), "rmse": round(metrics["rmse"], 3)},
        }
        print(f"  horizon {h:2d}: MAE {metrics['mae']:.2f}  RMSE {metrics['rmse']:.2f}")

    OUT.write_text(json.dumps(blob, indent=2))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
