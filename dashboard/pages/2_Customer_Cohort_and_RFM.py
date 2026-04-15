import pandas as pd
import plotly.express as px
import streamlit as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from common import assert_data, load_phase3

st.title("👥 Customer Cohort & RFM Dashboard")

phase3 = load_phase3()
retention = phase3["retention"]
segments = phase3["segments"]
churn = phase3["churn"]

col1, col2, col3 = st.columns(3)
if assert_data(churn, "Missing churn file. Run Phase 3 analysis first."):
    col1.metric("Churned Customers (90+ days)", f"{len(churn):,}")
if assert_data(segments, "Missing segment file. Run Phase 3 analysis first."):
    col2.metric("RFM Segments", f"{segments['segment'].nunique():,}")
    col3.metric("Largest Segment", str(segments.sort_values('customers', ascending=False).iloc[0]['segment']))

st.subheader("Cohort Retention Heatmap")
if assert_data(retention, "Retention data not found."):
    retention["cohort_month"] = pd.to_datetime(retention["cohort_month"])
    max_index = int(retention["cohort_index"].max())
    limit = st.slider("Max cohort month index", min_value=1, max_value=max_index, value=min(12, max_index))
    filt = retention[retention["cohort_index"] <= limit].copy()
    heat = filt.pivot(index="cohort_month", columns="cohort_index", values="retention_rate_pct")
    heat.index = heat.index.strftime("%Y-%m")
    fig = px.imshow(
        heat,
        labels={"x": "Months Since First Purchase", "y": "Cohort", "color": "Retention %"},
        aspect="auto",
        color_continuous_scale="YlGnBu",
    )
    st.plotly_chart(fig, width="stretch")

st.subheader("RFM Segment Distribution")
if assert_data(segments, "RFM segment data not found."):
    fig = px.pie(segments, names="segment", values="customers", hole=0.45)
    st.plotly_chart(fig, width="stretch")
    st.dataframe(segments, width="stretch")

st.subheader("Churned Customers Sample")
if assert_data(churn, "Churn table not found."):
    top_churn = churn.sort_values("days_since_last_order", ascending=False).head(50)
    st.dataframe(top_churn, width="stretch")
