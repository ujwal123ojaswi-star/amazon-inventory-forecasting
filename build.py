"""Build the full pipeline end to end:  python build.py

Generates the synthetic catalog + demand history, forecasts the next 30 days
per SKU, and computes the safety-stock / reorder-point / ABC inventory plan.
After this, launch the dashboard with:  streamlit run app/dashboard.py
"""
from __future__ import annotations

from ingest.config import (
    DATA_DIR,
    DEMAND_PATH,
    FORECAST_PATH,
    INVENTORY_PLAN_PATH,
    PRODUCTS_PATH,
)
from ingest.forecast import forecast_all, forecast_summary
from ingest.generate_data import generate_all
from ingest.reorder import build_inventory_plan


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("==> [1/4] Generating synthetic catalog + 2 years of daily demand")
    products, demand, inventory = generate_all()
    products.to_parquet(PRODUCTS_PATH, index=False)
    demand.to_parquet(DEMAND_PATH, index=False)
    print(f"[data] {len(products)} products, {len(demand):,} demand rows")

    print("\n==> [2/4] Forecasting next 30 days per SKU")
    forecast = forecast_all(demand)
    forecast.to_parquet(FORECAST_PATH, index=False)
    f_summary = forecast_summary(forecast)
    print(f"[forecast] {len(f_summary)} SKUs forecasted")

    print("\n==> [3/4] Computing safety stock, reorder points, ABC classes")
    plan = build_inventory_plan(products, demand, inventory, f_summary)
    plan.to_parquet(INVENTORY_PLAN_PATH, index=False)
    at_risk = int(plan["stockout_risk"].sum())
    print(f"[plan] {at_risk} of {len(plan)} SKUs currently below reorder point")

    print("\n==> [4/4] Done")
    print("Launch the dashboard with:")
    print("    streamlit run app/dashboard.py")


if __name__ == "__main__":
    main()
