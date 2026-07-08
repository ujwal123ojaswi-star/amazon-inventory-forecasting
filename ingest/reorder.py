"""Inventory optimization: safety stock, reorder points, ABC classification.

Standard inventory-theory formulas:
  safety_stock   = z * demand_std * sqrt(lead_time_days)
  reorder_point  = avg_daily_demand * lead_time_days + safety_stock
  days_of_cover  = on_hand_units / avg_daily_demand
ABC classification ranks SKUs by revenue contribution (Pareto: A = top ~80%
of cumulative revenue, B = next ~15%, C = remaining ~5%).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ingest.config import SERVICE_LEVEL_Z


def build_inventory_plan(
    products: pd.DataFrame,
    demand: pd.DataFrame,
    inventory: pd.DataFrame,
    forecast_summary: pd.DataFrame,
) -> pd.DataFrame:
    demand_stats = (
        demand.groupby("product_id")["units_sold"]
        .agg(avg_daily_demand="mean", demand_std="std")
        .reset_index()
    )
    demand_stats["demand_std"] = demand_stats["demand_std"].fillna(0)

    plan = (
        products.merge(demand_stats, on="product_id")
        .merge(inventory, on="product_id")
        .merge(forecast_summary, on="product_id")
    )

    plan["safety_stock"] = (
        SERVICE_LEVEL_Z * plan["demand_std"] * np.sqrt(plan["lead_time_days"])
    ).round(1)
    plan["reorder_point"] = (
        plan["avg_daily_demand"] * plan["lead_time_days"] + plan["safety_stock"]
    ).round(1)
    plan["days_of_cover"] = (
        plan["on_hand_units"] / plan["avg_daily_demand"].replace(0, np.nan)
    ).round(1)
    plan["units_to_order"] = (
        (plan["reorder_point"] - plan["on_hand_units"]).clip(lower=0).round(0)
    )
    plan["stockout_risk"] = plan["on_hand_units"] < plan["reorder_point"]
    plan["inventory_value"] = (plan["on_hand_units"] * plan["unit_cost"]).round(2)
    plan["trailing_revenue"] = (
        demand.merge(products[["product_id", "unit_price"]], on="product_id")
        .assign(revenue=lambda d: d["units_sold"] * d["unit_price"])
        .groupby("product_id")["revenue"]
        .sum()
        .reindex(plan["product_id"])
        .to_numpy()
    )

    plan = plan.sort_values("trailing_revenue", ascending=False).reset_index(drop=True)
    cum_share = plan["trailing_revenue"].cumsum() / plan["trailing_revenue"].sum()
    plan["abc_class"] = np.select(
        [cum_share <= 0.8, cum_share <= 0.95],
        ["A", "B"],
        default="C",
    )
    return plan
