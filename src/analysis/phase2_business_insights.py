import argparse
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 2 SQL analyses and export visuals.")
    parser.add_argument(
        "--db-path",
        default="data/processed/olist_analytics.db",
        help="Path to SQLite analytics database.",
    )
    parser.add_argument(
        "--sql-file",
        default="sql/03_phase2_business_insights.sql",
        help="Path to SQL file containing named analysis queries.",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/phase2",
        help="Directory for CSV outputs and charts.",
    )
    parser.add_argument(
        "--top-categories",
        type=int,
        default=10,
        help="Number of categories to show in top-category charts.",
    )
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

    if not queries:
        raise ValueError("No named queries found. Use '-- name: query_id' markers in the SQL file.")

    return queries


def save_query_outputs(conn: sqlite3.Connection, queries: dict[str, str], output_dir: Path) -> dict[str, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    dataframes: dict[str, pd.DataFrame] = {}

    for name, query in queries.items():
        df = pd.read_sql_query(query, conn)
        dataframes[name] = df
        df.to_csv(output_dir / f"{name}.csv", index=False)

    return dataframes


def plot_top_categories(df: pd.DataFrame, output_dir: Path, top_n: int) -> None:
    top = df.head(top_n).copy()
    plt.figure(figsize=(12, 6))
    sns.barplot(data=top, x="total_gmv_brl", y="category", hue="category", palette="viridis", legend=False)
    plt.title("Top Categories by GMV (BRL)")
    plt.xlabel("Total GMV (BRL)")
    plt.ylabel("Category")
    plt.tight_layout()
    plt.savefig(output_dir / "top_categories_gmv.png", dpi=150)
    plt.close()


def plot_monthly_gmv_trends(df: pd.DataFrame, output_dir: Path, top_categories: list[str]) -> None:
    if df.empty:
        return

    filtered = df[df["category"].isin(top_categories)].copy()
    if filtered.empty:
        return

    plt.figure(figsize=(14, 7))
    sns.lineplot(data=filtered, x="order_month", y="gmv_brl", hue="category", marker="o")
    plt.title("Monthly GMV Trends (Top Categories)")
    plt.xlabel("Month")
    plt.ylabel("GMV (BRL)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_dir / "monthly_gmv_trends_top_categories.png", dpi=150)
    plt.close()


def plot_conversion_funnel(df: pd.DataFrame, output_dir: Path, top_n: int) -> None:
    top = df.head(top_n).copy()
    fig, axes = plt.subplots(1, 2, figsize=(15, 6), sharey=True)

    sns.barplot(data=top, x="approval_rate_pct", y="category", hue="category", ax=axes[0], palette="Blues_r", legend=False)
    axes[0].set_title("Approval Rate by Category")
    axes[0].set_xlabel("Approval Rate (%)")
    axes[0].set_ylabel("Category")

    sns.barplot(data=top, x="cancellation_rate_pct", y="category", hue="category", ax=axes[1], palette="Reds_r", legend=False)
    axes[1].set_title("Cancellation Rate by Category")
    axes[1].set_xlabel("Cancellation Rate (%)")
    axes[1].set_ylabel("")

    plt.tight_layout()
    plt.savefig(output_dir / "conversion_funnel_rates.png", dpi=150)
    plt.close()


def plot_price_vs_review(df: pd.DataFrame, output_dir: Path) -> None:
    sample = df.sample(n=min(len(df), 15000), random_state=42) if not df.empty else df
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=sample, x="item_price_brl", y="avg_review_score", alpha=0.3, s=18)
    plt.title("Price vs Review Score")
    plt.xlabel("Item Price (BRL)")
    plt.ylabel("Average Review Score")
    plt.tight_layout()
    plt.savefig(output_dir / "price_vs_review_score.png", dpi=150)
    plt.close()


def plot_seller_performance(df: pd.DataFrame, output_dir: Path, top_n: int) -> None:
    top = df.head(top_n).copy()
    plt.figure(figsize=(12, 6))
    sns.barplot(data=top, x="seller_gmv_brl", y="seller_id", hue="seller_id", palette="magma", legend=False)
    plt.title("Top Sellers by Revenue")
    plt.xlabel("Seller GMV (BRL)")
    plt.ylabel("Seller ID")
    plt.tight_layout()
    plt.savefig(output_dir / "top_sellers_revenue.png", dpi=150)
    plt.close()


def plot_delivery_vs_rating(df: pd.DataFrame, output_dir: Path) -> None:
    plt.figure(figsize=(10, 6))
    sns.regplot(data=df, x="avg_delivery_days", y="avg_review_score", scatter_kws={"alpha": 0.4, "s": 18})
    plt.title("Delivery Time vs Average Review Score (Seller Level)")
    plt.xlabel("Average Delivery Days")
    plt.ylabel("Average Review Score")
    plt.tight_layout()
    plt.savefig(output_dir / "delivery_time_vs_rating.png", dpi=150)
    plt.close()


def plot_geographic_demand(df: pd.DataFrame, output_dir: Path) -> None:
    state_totals = (
        df.groupby("customer_state", as_index=False)["gmv_brl"]
        .sum()
        .sort_values("gmv_brl", ascending=False)
        .head(12)
    )

    plt.figure(figsize=(12, 6))
    sns.barplot(data=state_totals, x="customer_state", y="gmv_brl", hue="customer_state", palette="cubehelix", legend=False)
    plt.title("Top States by GMV")
    plt.xlabel("State")
    plt.ylabel("GMV (BRL)")
    plt.tight_layout()
    plt.savefig(output_dir / "top_states_gmv.png", dpi=150)
    plt.close()


def main() -> None:
    args = parse_args()

    db_path = Path(args.db_path)
    sql_file = Path(args.sql_file)
    output_dir = Path(args.output_dir)

    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    if not sql_file.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_file}")

    sql_text = sql_file.read_text(encoding="utf-8")
    queries = parse_named_queries(sql_text)

    sns.set_theme(style="whitegrid")

    with sqlite3.connect(db_path) as conn:
        dfs = save_query_outputs(conn, queries, output_dir)

    top_categories_df = dfs["top_categories_total_gmv"]
    monthly_df = dfs["category_gmv_by_month"]
    funnel_df = dfs["conversion_funnel_by_category"]
    price_review_df = dfs["pricing_distribution_by_category"]
    seller_df = dfs["seller_performance"]
    delivery_rating_df = dfs["delivery_time_vs_rating"]
    geo_df = dfs["geographic_category_demand"]

    top_categories = top_categories_df.head(args.top_categories)["category"].tolist()

    plot_top_categories(top_categories_df, output_dir, args.top_categories)
    plot_monthly_gmv_trends(monthly_df, output_dir, top_categories)
    plot_conversion_funnel(funnel_df, output_dir, args.top_categories)
    plot_price_vs_review(price_review_df, output_dir)
    plot_seller_performance(seller_df, output_dir, args.top_categories)
    plot_delivery_vs_rating(delivery_rating_df, output_dir)
    plot_geographic_demand(geo_df, output_dir)

    corr = price_review_df["item_price_brl"].corr(price_review_df["avg_review_score"])
    summary_text = (
        "Phase 2 analysis generated successfully.\n"
        f"Top categories considered: {args.top_categories}\n"
        f"Price vs review correlation: {corr:.4f}\n"
    )
    (output_dir / "summary.txt").write_text(summary_text, encoding="utf-8")

    print(summary_text)
    print(f"Outputs written to: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
