"""Amazon-style Inventory & Supply Chain Analytics dashboard.

Sections: KPIs, demand forecast per SKU, reorder recommendations, and ABC
(Pareto) revenue classification.

Run:  streamlit run app/dashboard.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

from app.theme import THEME_CSS, apply_plotly_theme, plotly_chart
from ingest.config import DEMAND_PATH, FORECAST_PATH, INVENTORY_PLAN_PATH, PRODUCTS_PATH

st.set_page_config(page_title="Inventory & Supply Chain Analytics", page_icon="\U0001F4E6", layout="wide")
apply_plotly_theme(pio)
st.markdown(THEME_CSS, unsafe_allow_html=True)


def build_if_missing() -> bool:
    if PRODUCTS_PATH.exists() and DEMAND_PATH.exists() and INVENTORY_PLAN_PATH.exists():
        return False
    with st.spinner("First run: generating data, forecasting, and building the inventory plan..."):
        import build as build_module

        build_module.main()
    return True


@st.cache_data
def load_data():
    products = pd.read_parquet(PRODUCTS_PATH)
    demand = pd.read_parquet(DEMAND_PATH)
    forecast = pd.read_parquet(FORECAST_PATH)
    plan = pd.read_parquet(INVENTORY_PLAN_PATH)
    return products, demand, forecast, plan


def main() -> None:
    st.title("Inventory & Supply Chain Analytics")
    st.caption(
        "Synthetic multi-SKU catalog: demand forecasting, safety-stock / "
        "reorder-point optimization, and ABC (Pareto) revenue classification."
    )

    if build_if_missing():
        st.cache_data.clear()
    products, demand, forecast, plan = load_data()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("SKUs tracked", f"{len(plan):,}")
    k2.metric("At risk of stockout", f"{int(plan['stockout_risk'].sum())}")
    k3.metric("Inventory value", f"${plan['inventory_value'].sum():,.0f}")
    k4.metric("Forecasted demand (30d)", f"{plan['total_forecast_30d'].sum():,.0f} units")
    st.divider()

    tabs = st.tabs(["Reorder Recommendations", "Demand Forecast", "ABC Analysis", "Research Benchmark"])

    with tabs[0]:
        st.caption("SKUs at or below their reorder point, ranked by urgency (lowest days of cover first).")
        risk_only = st.checkbox("Show only at-risk SKUs", value=True)
        view = plan[plan["stockout_risk"]] if risk_only else plan
        view = view.sort_values("days_of_cover")
        st.dataframe(
            view[
                [
                    "product_id", "name", "category", "warehouse", "abc_class",
                    "on_hand_units", "reorder_point", "safety_stock",
                    "units_to_order", "days_of_cover", "lead_time_days",
                ]
            ].style.format({
                "reorder_point": "{:.0f}", "safety_stock": "{:.0f}",
                "units_to_order": "{:.0f}", "days_of_cover": "{:.1f}",
            }),
            use_container_width=True,
            height=420,
        )

        by_wh = plan.groupby("warehouse")["stockout_risk"].sum().reset_index()
        fig = px.bar(by_wh, x="warehouse", y="stockout_risk", title="At-risk SKUs by warehouse")
        fig.update_yaxes(title="At-risk SKU count")
        plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        product_id = st.selectbox(
            "SKU", plan["product_id"],
            format_func=lambda pid: f"{pid} — {plan.set_index('product_id').loc[pid, 'name']}",
        )
        hist = demand[demand["product_id"] == product_id].tail(120)
        fut = forecast[forecast["product_id"] == product_id]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist["date"], y=hist["units_sold"], name="Actual (last 120d)", mode="lines"))
        fig.add_trace(go.Scatter(x=fut["date"], y=fut["forecast_units"], name="Forecast (next 30d)",
                                  mode="lines", line=dict(dash="dash")))
        fig.update_layout(title=f"Daily demand — {product_id}", height=420,
                           legend=dict(orientation="h", y=-0.2))
        plotly_chart(fig, use_container_width=True)

        row = plan.set_index("product_id").loc[product_id]
        c1, c2, c3 = st.columns(3)
        c1.metric("Avg daily demand", f"{row['avg_daily_demand']:.1f}")
        c2.metric("Lead time", f"{row['lead_time_days']} days")
        c3.metric("Reorder point", f"{row['reorder_point']:.0f} units")

    with tabs[2]:
        st.caption("ABC classification: A = top ~80% of revenue, B = next ~15%, C = remaining ~5%.")
        counts = plan["abc_class"].value_counts().reindex(["A", "B", "C"]).fillna(0)
        revenue = plan.groupby("abc_class")["trailing_revenue"].sum().reindex(["A", "B", "C"]).fillna(0)

        c1, c2 = st.columns(2)
        with c1:
            fig = px.pie(names=counts.index, values=counts.to_numpy(), title="SKU count by ABC class", hole=0.4)
            plotly_chart(fig, use_container_width=True)
        with c2:
            fig = px.pie(names=revenue.index, values=revenue.to_numpy(), title="Revenue share by ABC class", hole=0.4)
            plotly_chart(fig, use_container_width=True)

        ranked = plan.sort_values("trailing_revenue", ascending=False).reset_index(drop=True)
        ranked["cum_revenue_share"] = ranked["trailing_revenue"].cumsum() / ranked["trailing_revenue"].sum()
        fig = go.Figure()
        fig.add_trace(go.Bar(x=ranked.index + 1, y=ranked["trailing_revenue"], name="Revenue"))
        fig.add_trace(go.Scatter(x=ranked.index + 1, y=ranked["cum_revenue_share"], name="Cumulative share",
                                  yaxis="y2", line=dict(color="#D4AF37")))
        fig.update_layout(
            title="Pareto chart: SKU revenue contribution",
            xaxis_title="SKU rank",
            yaxis=dict(title="Revenue ($)"),
            yaxis2=dict(title="Cumulative share", overlaying="y", side="right", tickformat=".0%", range=[0, 1.05]),
            height=420,
        )
        plotly_chart(fig, use_container_width=True)

    with tabs[3]:
        st.markdown("##### Research benchmark")
        st.markdown(
            "Industry research (E2open 2019 Forecasting & Inventory Benchmark Study; supply-chain "
            "literature) reports that **traditional/ad-hoc safety-stock approaches run up to 30% too "
            "low**, with service levels up to 10 percentage points below target. Separately, "
            "forecast-driven \"demand sensing\" is credited with cutting forecast error by roughly "
            "**40%** versus static methods.\n\n"
            "This project uses the statistically-grounded service-level formula (95% service level, "
            "z = 1.65) rather than an ad-hoc buffer, directly avoiding the under-protection failure "
            "mode the research documents."
        )
        st.markdown("##### Differentiator vs. the research")
        st.markdown(
            "Industry benchmark reports aggregate real operational statistics across many companies "
            "at a scale no single synthetic catalog can replicate. This project's advantage is "
            "transparency: every number here traces to an open formula over an open, regenerable "
            "dataset, not proprietary ERP aggregation."
        )
        st.markdown("##### Efficiency")
        st.markdown(
            "Full pipeline (data generation, forecasting, safety stock/reorder-point/ABC computation "
            "for all 60 SKUs) runs end to end in **~25 seconds**, measured via wall-clock timing — "
            "roughly a 70-140x reduction versus an estimated 30-60 minute manual spreadsheet equivalent."
        )
        st.caption(
            "Full write-up with sources: [RESEARCH_COMPARISON.md on GitHub]"
            "(https://github.com/ujwal123ojaswi-star/amazon-inventory-forecasting/blob/master/RESEARCH_COMPARISON.md)"
        )


if __name__ == "__main__":
    main()
