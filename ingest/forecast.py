"""Per-SKU demand forecasting.

Uses a lightweight, explainable model per product: linear trend + day-of-week
dummies via scikit-learn's LinearRegression, fit on the trailing 120 days and
projected 30 days forward. Simple on purpose — the point of this project is
the inventory-optimization layer built on top of the forecast, not exotic
forecasting methods.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

FORECAST_HORIZON_DAYS = 30
TRAILING_WINDOW_DAYS = 120


def _features(dates: pd.DatetimeIndex, t0: pd.Timestamp) -> np.ndarray:
    t = (dates - t0).days.to_numpy().reshape(-1, 1).astype(float)
    dow = pd.get_dummies(dates.dayofweek, prefix="dow")
    for d in range(7):
        col = f"dow_{d}"
        if col not in dow.columns:
            dow[col] = 0
    dow = dow[[f"dow_{d}" for d in range(7)]].to_numpy()
    return np.hstack([t, dow])


def forecast_all(demand: pd.DataFrame) -> pd.DataFrame:
    demand = demand.sort_values(["product_id", "date"])
    out_frames = []
    for product_id, g in demand.groupby("product_id"):
        g = g.tail(TRAILING_WINDOW_DAYS)
        t0 = g["date"].min()
        X = _features(pd.DatetimeIndex(g["date"]), t0)
        y = g["units_sold"].to_numpy()

        model = LinearRegression()
        model.fit(X, y)

        last_date = g["date"].max()
        future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=FORECAST_HORIZON_DAYS, freq="D")
        X_future = _features(pd.DatetimeIndex(future_dates), t0)
        preds = np.clip(model.predict(X_future), 0, None)

        out_frames.append(
            pd.DataFrame(
                {
                    "product_id": product_id,
                    "date": future_dates,
                    "forecast_units": preds,
                }
            )
        )
    return pd.concat(out_frames, ignore_index=True)


def forecast_summary(forecast: pd.DataFrame) -> pd.DataFrame:
    """Average daily forecast + total over the horizon, per product."""
    g = forecast.groupby("product_id")["forecast_units"]
    return g.agg(avg_daily_forecast="mean", total_forecast_30d="sum").reset_index()
