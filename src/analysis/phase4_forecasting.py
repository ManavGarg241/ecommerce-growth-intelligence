import argparse
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 4 demand forecasting for top categories.")
    parser.add_argument("--db-path", default="data/processed/olist_analytics.db", help="Path to SQLite DB.")
    parser.add_argument("--sql-file", default="sql/05_phase4_demand_forecasting.sql", help="Path to SQL file.")
    parser.add_argument("--output-dir", default="reports/phase4", help="Output directory for forecasts.")
    parser.add_argument("--top-n", type=int, default=3, help="Number of top categories to forecast.")
    parser.add_argument("--test-weeks", type=int, default=12, help="Weeks reserved for holdout evaluation.")
    parser.add_argument("--future-weeks", type=int, default=12, help="Future weeks to forecast.")
    return parser.parse_args()


def parse_named_queries(sql_text: str) -> dict[str, str]:
    queries: dict[str, str] = {}
    current_name: str | None = None
    current_lines: list[str] = []

    for line in sql_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("-- name:"):
            if current_name and current_lines:
                queries[current_name] = "\n".join(current_lines).strip()
            current_name = stripped.replace("-- name:", "").strip()
            current_lines = []
            continue
        if current_name is not None:
            current_lines.append(line)

    if current_name and current_lines:
        queries[current_name] = "\n".join(current_lines).strip()

    return queries


def mape(y_true: pd.Series, y_pred: pd.Series) -> float:
    y_true_adj = np.where(np.abs(y_true) < 1e-6, 1e-6, y_true)
    return float(np.mean(np.abs((y_true - y_pred) / y_true_adj)) * 100)


def fit_sarima(train: pd.Series):
    # Use shorter seasonality for shorter histories to avoid unstable seasonal initialization.
    seasonal_period = 52 if len(train) >= 156 else 12

    try:
        model = SARIMAX(
            train,
            order=(1, 1, 1),
            seasonal_order=(1, 1, 1, seasonal_period),
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        return model.fit(disp=False)
    except Exception:
        fallback = SARIMAX(
            train,
            order=(1, 1, 1),
            seasonal_order=(0, 0, 0, 0),
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        return fallback.fit(disp=False)


def build_weekly_series(df_weekly: pd.DataFrame, category: str) -> pd.Series:
    cat = df_weekly[df_weekly["category"] == category].copy()
    cat["week_start"] = pd.to_datetime(cat["week_start"])
    cat = cat.sort_values("week_start")

    full_weeks = pd.date_range(cat["week_start"].min(), cat["week_start"].max(), freq="W-MON")
    series = (
        cat.set_index("week_start")["weekly_gmv_brl"]
        .reindex(full_weeks)
        .fillna(0.0)
    )
    series.index.name = "week_start"
    return series


def forecast_category(series: pd.Series, test_weeks: int, future_weeks: int) -> tuple[pd.DataFrame, float]:
    if len(series) <= test_weeks + 10:
        raise ValueError("Not enough observations for train/test forecasting split.")

    train = series.iloc[:-test_weeks]
    test = series.iloc[-test_weeks:]

    model_fit = fit_sarima(train)
    test_forecast = model_fit.get_forecast(steps=test_weeks)
    test_pred = pd.Series(test_forecast.predicted_mean.values, index=test.index)

    score = mape(test, test_pred)

    full_fit = fit_sarima(series)
    future_forecast = full_fit.get_forecast(steps=future_weeks)
    future_idx = pd.date_range(series.index.max() + pd.Timedelta(weeks=1), periods=future_weeks, freq="W-MON")

    forecast_df = pd.DataFrame(
        {
            "week_start": future_idx,
            "forecast": future_forecast.predicted_mean.values,
            "lower_ci": future_forecast.conf_int().iloc[:, 0].values,
            "upper_ci": future_forecast.conf_int().iloc[:, 1].values,
        }
    )

    return forecast_df, score


def plot_forecast(series: pd.Series, forecast_df: pd.DataFrame, category: str, output_dir: Path) -> None:
    plt.figure(figsize=(12, 6))
    plt.plot(series.index, series.values, label="Actual", color="#1f77b4")
    plt.plot(forecast_df["week_start"], forecast_df["forecast"], label="Forecast", color="#ff7f0e")
    plt.fill_between(
        forecast_df["week_start"],
        forecast_df["lower_ci"],
        forecast_df["upper_ci"],
        color="#ff7f0e",
        alpha=0.2,
        label="Confidence Interval",
    )
    plt.title(f"Weekly Demand Forecast - {category}")
    plt.xlabel("Week")
    plt.ylabel("GMV (BRL)")
    plt.legend()
    plt.tight_layout()
    safe = category.replace("/", "_").replace(" ", "_")
    plt.savefig(output_dir / f"forecast_{safe}.png", dpi=150)
    plt.close()


def main() -> None:
    args = parse_args()
    db_path = Path(args.db_path)
    sql_file = Path(args.sql_file)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    if not sql_file.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_file}")

    queries = parse_named_queries(sql_file.read_text(encoding="utf-8"))

    with sqlite3.connect(db_path) as conn:
        weekly_df = pd.read_sql_query(queries["weekly_category_gmv"], conn)
        top_cat_df = pd.read_sql_query(queries["top_categories_by_gmv"], conn)

    weekly_df.to_csv(output_dir / "weekly_category_gmv.csv", index=False)

    top_categories = top_cat_df.head(args.top_n)["category"].tolist()

    metrics = []
    for category in top_categories:
        series = build_weekly_series(weekly_df, category)
        forecast_df, score = forecast_category(series, args.test_weeks, args.future_weeks)

        safe = category.replace("/", "_").replace(" ", "_")
        forecast_df.to_csv(output_dir / f"forecast_{safe}.csv", index=False)
        plot_forecast(series, forecast_df, category, output_dir)

        metrics.append({"category": category, "mape_pct": round(score, 2)})

    metrics_df = pd.DataFrame(metrics).sort_values("mape_pct")
    metrics_df.to_csv(output_dir / "forecast_metrics.csv", index=False)

    summary = "\n".join(
        [
            "Phase 4 forecasting completed.",
            f"Top categories modeled: {', '.join(top_categories)}",
            f"Average MAPE: {metrics_df['mape_pct'].mean():.2f}%",
        ]
    )
    (output_dir / "summary.txt").write_text(summary + "\n", encoding="utf-8")

    print(summary)
    print(f"Outputs written to: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
