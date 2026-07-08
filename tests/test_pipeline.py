from __future__ import annotations

import numpy as np

from ingest.forecast import forecast_all, forecast_summary
from ingest.generate_data import generate_all
from ingest.reorder import build_inventory_plan


def test_generate_all_shapes():
    products, demand, inventory = generate_all()
    assert len(products) > 0
    assert set(["product_id", "category", "warehouse", "lead_time_days"]).issubset(products.columns)
    assert demand["product_id"].nunique() == len(products)
    assert inventory["product_id"].nunique() == len(products)
    assert (demand["units_sold"] >= 0).all()


def test_forecast_nonnegative():
    products, demand, _ = generate_all()
    forecast = forecast_all(demand)
    assert (forecast["forecast_units"] >= 0).all()
    summary = forecast_summary(forecast)
    assert set(summary["product_id"]) == set(products["product_id"])


def test_inventory_plan_abc_classes():
    products, demand, inventory = generate_all()
    forecast = forecast_all(demand)
    summary = forecast_summary(forecast)
    plan = build_inventory_plan(products, demand, inventory, summary)
    assert set(plan["abc_class"].unique()).issubset({"A", "B", "C"})
    assert (plan["reorder_point"] >= 0).all()
    assert (plan["safety_stock"] >= 0).all()
