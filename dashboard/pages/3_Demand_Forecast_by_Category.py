import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from common import assert_data, load_phase4

st.title("📈 Demand Forecast by Category")

phase4 = load_phase4()
metrics = phase4["metrics"]
forecasts = phase4["forecasts"]

if assert_data(metrics, "Forecast metrics missing. Run Phase 4 analysis first."):
    st.subheader("Model Accuracy (MAPE)")
    st.dataframe(metrics.sort_values("mape_pct"), width="stretch")

if forecasts:
    st.subheader("Forecast vs Confidence Interval")
    category_options = sorted(forecasts.keys())
    selected = st.selectbox("Category", category_options, index=0)

    df = forecasts[selected].copy()
    df["week_start"] = pd.to_datetime(df["week_start"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["week_start"], y=df["forecast"], mode="lines+markers", name="Forecast"))
    fig.add_trace(
        go.Scatter(
            x=df["week_start"],
            y=df["upper_ci"],
            mode="lines",
            line={"width": 0},
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["week_start"],
            y=df["lower_ci"],
            mode="lines",
            fill="tonexty",
            name="Confidence Interval",
            line={"width": 0},
            hoverinfo="skip",
        )
    )

    fig.update_layout(xaxis_title="Week", yaxis_title="Forecasted GMV (BRL)")
    st.plotly_chart(fig, width="stretch")

    st.dataframe(df, width="stretch")
else:
    st.warning("No forecast files found. Run Phase 4 first.")
