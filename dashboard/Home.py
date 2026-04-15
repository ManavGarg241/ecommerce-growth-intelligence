import streamlit as st

st.set_page_config(
    page_title="E-Commerce Growth Intelligence",
    page_icon="🛒",
    layout="wide",
)

st.title("🛒 E-Commerce Growth Intelligence System")
st.caption("End-to-end analytics platform simulating a category analyst workflow")

st.markdown(
    """
This dashboard combines:
- SQL-first business analysis
- Cohort retention and RFM segmentation
- Weekly demand forecasting (top categories)
- Seller and pricing intelligence

Use the left sidebar to navigate through the four pages.
"""
)

st.info(
    "If a page shows missing data, run Phase 1-4 scripts first so reports are generated under reports/phase2, reports/phase3, and reports/phase4."
)
