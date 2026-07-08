"""Synthetic multi-SKU demand + product catalog generator.

There's no public "Amazon inventory" API, so this generates a realistic
synthetic dataset instead: a product catalog with a Pareto-like mix of
high/low velocity SKUs across categories and warehouses, and 2 years of daily
demand history with weekly seasonality, category-specific holiday spikes,
a mild growth trend, and Poisson noise (demand is a count, not continuous).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ingest.config import CATEGORIES, N_DAYS_HISTORY, N_PRODUCTS, RANDOM_SEED, WAREHOUSES

CATEGORY_HOLIDAY_LIFT = {
    "Electronics": 2.8,
    "Toys": 3.5,
    "Home & Kitchen": 1.6,
    "Grocery": 1.1,
    "Sports & Outdoors": 1.3,
    "Beauty": 1.8,
}


def generate_products(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    for i in range(N_PRODUCTS):
        category = CATEGORIES[i % len(CATEGORIES)]
        # Pareto-like velocity mix: a few fast movers, a long tail of slow ones.
        velocity = rng.pareto(a=2.0) + 0.2
        unit_cost = float(rng.uniform(4, 120))
        margin_pct = float(rng.uniform(0.15, 0.55))
        rows.append(
            {
                "product_id": f"SKU-{i + 1:04d}",
                "name": f"{category} Item {i + 1:04d}",
                "category": category,
                "warehouse": WAREHOUSES[i % len(WAREHOUSES)],
                "base_daily_demand": round(velocity * 4, 2),
                "unit_cost": round(unit_cost, 2),
                "unit_price": round(unit_cost * (1 + margin_pct), 2),
                "lead_time_days": int(rng.choice([3, 5, 7, 10, 14], p=[0.15, 0.3, 0.3, 0.15, 0.1])),
            }
        )
    return pd.DataFrame(rows)


def generate_demand_history(products: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    dates = pd.date_range(end=pd.Timestamp.today().normalize(), periods=N_DAYS_HISTORY, freq="D")
    dow = dates.dayofweek.to_numpy()
    day_of_year = dates.dayofyear.to_numpy()

    weekday_factor = np.where(dow >= 5, 1.25, 0.95)  # weekend lift
    trend = np.linspace(1.0, 1.18, len(dates))  # ~18% growth over 2 years
    # Holiday season lift centered on late Nov (day ~330) tapering into December.
    holiday_curve = np.exp(-0.5 * ((day_of_year - 335) / 18) ** 2)

    frames = []
    for _, prod in products.iterrows():
        lift = CATEGORY_HOLIDAY_LIFT.get(prod["category"], 1.5)
        holiday_factor = 1.0 + (lift - 1.0) * holiday_curve
        mean_demand = prod["base_daily_demand"] * weekday_factor * trend * holiday_factor
        mean_demand = np.clip(mean_demand, 0.05, None)
        units_sold = rng.poisson(mean_demand)
        frames.append(
            pd.DataFrame(
                {
                    "product_id": prod["product_id"],
                    "date": dates,
                    "units_sold": units_sold,
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def generate_current_inventory(products: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Snapshot of on-hand inventory 'as of today' — some SKUs are deliberately
    left low/at-risk so the reorder logic has something to flag."""
    rows = []
    for _, prod in products.iterrows():
        days_of_cover = rng.uniform(0.5, 25)
        on_hand = max(0, round(prod["base_daily_demand"] * days_of_cover))
        rows.append({"product_id": prod["product_id"], "on_hand_units": int(on_hand)})
    return pd.DataFrame(rows)


def generate_all() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(RANDOM_SEED)
    products = generate_products(rng)
    demand = generate_demand_history(products, rng)
    inventory = generate_current_inventory(products, rng)
    return products, demand, inventory
