from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPORTS_PHASE2 = PROJECT_ROOT / "reports" / "phase2"
REPORTS_PHASE3 = PROJECT_ROOT / "reports" / "phase3"
REPORTS_PHASE4 = PROJECT_ROOT / "reports" / "phase4"


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(show_spinner=False)
def load_phase2() -> dict[str, pd.DataFrame]:
    return {
        "top_categories": _read_csv(REPORTS_PHASE2 / "top_categories_total_gmv.csv"),
        "monthly_gmv": _read_csv(REPORTS_PHASE2 / "category_gmv_by_month.csv"),
        "funnel": _read_csv(REPORTS_PHASE2 / "conversion_funnel_by_category.csv"),
        "seller": _read_csv(REPORTS_PHASE2 / "seller_performance.csv"),
        "price_review": _read_csv(REPORTS_PHASE2 / "pricing_distribution_by_category.csv"),
        "delivery_rating": _read_csv(REPORTS_PHASE2 / "delivery_time_vs_rating.csv"),
    }


@st.cache_data(show_spinner=False)
def load_phase3() -> dict[str, pd.DataFrame]:
    return {
        "retention": _read_csv(REPORTS_PHASE3 / "cohort_retention.csv"),
        "segments": _read_csv(REPORTS_PHASE3 / "rfm_segment_sizes.csv"),
        "churn": _read_csv(REPORTS_PHASE3 / "churn_90_plus_days.csv"),
    }


@st.cache_data(show_spinner=False)
def load_phase4() -> dict[str, pd.DataFrame]:
    data = {
        "metrics": _read_csv(REPORTS_PHASE4 / "forecast_metrics.csv"),
    }

    forecast_files = sorted(REPORTS_PHASE4.glob("forecast_*.csv")) if REPORTS_PHASE4.exists() else []
    data["forecasts"] = {
        file.stem.replace("forecast_", ""): pd.read_csv(file)
        for file in forecast_files
        if file.name != "forecast_metrics.csv"
    }
    return data


def assert_data(df: pd.DataFrame, message: str) -> bool:
    if df.empty:
        st.warning(message)
        return False
    return True
