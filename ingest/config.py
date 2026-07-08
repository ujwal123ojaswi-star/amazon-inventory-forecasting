from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DEMAND_PATH = DATA_DIR / "demand_history.parquet"
PRODUCTS_PATH = DATA_DIR / "products.parquet"
FORECAST_PATH = DATA_DIR / "forecast.parquet"
INVENTORY_PLAN_PATH = DATA_DIR / "inventory_plan.parquet"

N_PRODUCTS = 60
N_DAYS_HISTORY = 730  # 2 years of daily demand
RANDOM_SEED = 42

CATEGORIES = [
    "Electronics",
    "Home & Kitchen",
    "Grocery",
    "Toys",
    "Sports & Outdoors",
    "Beauty",
]

WAREHOUSES = ["US-EAST-1", "US-WEST-2", "US-CENTRAL-1"]

SERVICE_LEVEL_Z = 1.65  # ~95% service level (one-tailed normal z-score)
