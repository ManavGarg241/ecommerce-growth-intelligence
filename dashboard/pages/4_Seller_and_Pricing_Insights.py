import plotly.express as px
import streamlit as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from common import assert_data, load_phase2

st.title("🏆 Seller & Pricing Insights")

phase2 = load_phase2()
seller = phase2["seller"]
price_review = phase2["price_review"]
delivery_rating = phase2["delivery_rating"]

st.subheader("Top Sellers by Revenue")
if assert_data(seller, "Seller performance data missing. Run Phase 2 analysis first."):
    top_n = st.slider("Top sellers", min_value=5, max_value=30, value=10)
    top = seller.head(top_n)
    fig = px.bar(top, x="seller_gmv_brl", y="seller_id", orientation="h", color="seller_gmv_brl")
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title="GMV (BRL)", yaxis_title="Seller")
    st.plotly_chart(fig, width="stretch")

st.subheader("Price vs Review Score")
if assert_data(price_review, "Pricing-review data missing."):
    sample = price_review.sample(min(12000, len(price_review)), random_state=42)
    fig = px.scatter(
        sample,
        x="item_price_brl",
        y="avg_review_score",
        opacity=0.35,
        trendline="ols",
    )
    fig.update_layout(xaxis_title="Item Price (BRL)", yaxis_title="Average Review Score")
    st.plotly_chart(fig, width="stretch")

st.subheader("Delivery Time vs Seller Rating")
if assert_data(delivery_rating, "Delivery-rating data missing."):
    fig = px.scatter(
        delivery_rating,
        x="avg_delivery_days",
        y="avg_review_score",
        size="order_count",
        opacity=0.6,
        hover_data=["seller_id"],
    )
    fig.update_layout(xaxis_title="Average Delivery Days", yaxis_title="Average Review Score")
    st.plotly_chart(fig, width="stretch")

    st.dataframe(delivery_rating.sort_values("order_count", ascending=False).head(30), width="stretch")
