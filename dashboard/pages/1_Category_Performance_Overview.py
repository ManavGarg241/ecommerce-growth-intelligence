import pandas as pd
import plotly.express as px
import streamlit as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from common import assert_data, load_phase2

st.title("📊 Category Performance Overview")

phase2 = load_phase2()

top_categories = phase2["top_categories"]
monthly_gmv = phase2["monthly_gmv"]
funnel = phase2["funnel"]

col1, col2, col3 = st.columns(3)
if assert_data(top_categories, "Missing category data. Run Phase 2 analysis first."):
    col1.metric("Tracked Categories", f"{top_categories['category'].nunique():,}")
    col2.metric("Total GMV (BRL)", f"{top_categories['total_gmv_brl'].sum():,.0f}")
    col3.metric("Orders", f"{top_categories['order_count'].sum():,}")

st.subheader("Top Categories by GMV")
if assert_data(top_categories, "Top category table not found."):
    top_n = st.slider("Top N categories", min_value=5, max_value=30, value=10)
    top = top_categories.head(top_n)
    fig = px.bar(top, x="total_gmv_brl", y="category", orientation="h", color="total_gmv_brl")
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title="GMV (BRL)", yaxis_title="Category")
    st.plotly_chart(fig, width="stretch")

st.subheader("Monthly GMV Trends")
if assert_data(monthly_gmv, "Monthly GMV data not found."):
    monthly_gmv["order_month"] = pd.to_datetime(monthly_gmv["order_month"] + "-01")
    cat_options = top_categories.head(12)["category"].tolist() if not top_categories.empty else []
    selected_categories = st.multiselect(
        "Categories to compare",
        options=cat_options,
        default=cat_options[:5],
    )
    filtered = monthly_gmv[monthly_gmv["category"].isin(selected_categories)] if selected_categories else monthly_gmv
    fig = px.line(filtered, x="order_month", y="gmv_brl", color="category", markers=True)
    fig.update_layout(xaxis_title="Month", yaxis_title="GMV (BRL)")
    st.plotly_chart(fig, width="stretch")

st.subheader("Approval vs Cancellation")
if assert_data(funnel, "Funnel data not found."):
    top_orders = funnel.sort_values("orders", ascending=False).head(12)
    fig = px.scatter(
        top_orders,
        x="approval_rate_pct",
        y="cancellation_rate_pct",
        size="orders",
        color="category",
        hover_data=["orders"],
    )
    fig.update_layout(xaxis_title="Approval Rate (%)", yaxis_title="Cancellation Rate (%)")
    st.plotly_chart(fig, width="stretch")

    st.dataframe(top_orders, width="stretch")
