# Inventory & Supply Chain Analytics

End-to-end inventory analytics pipeline: a synthetic multi-SKU product catalog
and 2 years of daily demand history, per-SKU demand forecasting, and
safety-stock / reorder-point optimization with ABC (Pareto) revenue
classification — served through a Streamlit dashboard.

There's no public "Amazon inventory" API, so this generates a realistic
synthetic dataset instead (Pareto-distributed SKU velocity across categories
and warehouses, weekly seasonality, category-specific holiday demand spikes,
and a mild growth trend), which keeps the project fully self-contained: no
API keys, no signup, works immediately.

## Run locally

```bash
pip install -e .
python build.py
streamlit run app/dashboard.py
```

The dashboard also auto-builds on first run if the data files aren't present
yet (e.g. on a fresh Streamlit Cloud deploy) — no manual build step required.

## What it does

- **Reorder Recommendations** — safety stock (`z * demand_std * sqrt(lead_time)`),
  reorder point, days of cover, and units-to-order per SKU, flaggable to
  at-risk-only.
- **Demand Forecast** — per-SKU linear trend + day-of-week model, 30-day
  forecast plotted against the last 120 days of actuals.
- **ABC Analysis** — Pareto classification of SKUs by trailing revenue
  contribution (A = top ~80%, B = next ~15%, C = remaining ~5%), with a
  cumulative-share Pareto chart.

## Stack

Python, pandas, NumPy, scikit-learn (linear regression forecasting), DuckDB,
Plotly, Streamlit.

## Live dashboard

`<add your Streamlit Community Cloud URL here once deployed>`
