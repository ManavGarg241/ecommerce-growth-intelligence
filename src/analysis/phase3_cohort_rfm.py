import argparse
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Phase 3 cohort and RFM analyses.")
    parser.add_argument("--db-path", default="data/processed/olist_analytics.db", help="Path to SQLite DB.")
    parser.add_argument("--sql-file", default="sql/04_phase3_cohort_rfm.sql", help="Path to SQL file.")
    parser.add_argument("--output-dir", default="reports/phase3", help="Output directory for reports.")
    parser.add_argument("--max-cohort-index", type=int, default=12, help="Retention months to include.")
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


def run_queries(conn: sqlite3.Connection, queries: dict[str, str], output_dir: Path) -> dict[str, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, pd.DataFrame] = {}

    for name, query in queries.items():
        df = pd.read_sql_query(query, conn)
        results[name] = df
        df.to_csv(output_dir / f"{name}.csv", index=False)

    return results


def plot_retention_heatmap(retention_df: pd.DataFrame, output_dir: Path, max_cohort_index: int) -> None:
    df = retention_df[retention_df["cohort_index"] <= max_cohort_index].copy()
    if df.empty:
        return

    pivot = df.pivot(index="cohort_month", columns="cohort_index", values="retention_rate_pct").sort_index()

    plt.figure(figsize=(14, 7))
    sns.heatmap(pivot, annot=True, fmt=".1f", cmap="YlGnBu", cbar_kws={"label": "Retention %"})
    plt.title("Monthly Cohort Retention Heatmap")
    plt.xlabel("Months Since First Purchase")
    plt.ylabel("Cohort Month")
    plt.tight_layout()
    plt.savefig(output_dir / "cohort_retention_heatmap.png", dpi=150)
    plt.close()


def plot_segment_sizes(segment_df: pd.DataFrame, output_dir: Path) -> None:
    if segment_df.empty:
        return

    plt.figure(figsize=(10, 6))
    sns.barplot(data=segment_df, x="segment", y="customers", hue="segment", palette="Set2", legend=False)
    plt.title("RFM Segment Sizes")
    plt.xlabel("Segment")
    plt.ylabel("Customers")
    plt.tight_layout()
    plt.savefig(output_dir / "rfm_segment_sizes.png", dpi=150)
    plt.close()


def write_summary(churn_df: pd.DataFrame, segment_df: pd.DataFrame, output_dir: Path) -> None:
    total_churn_90 = len(churn_df)
    segment_top = segment_df.iloc[0]["segment"] if not segment_df.empty else "N/A"
    summary = (
        "Phase 3 cohort and RFM analysis generated successfully.\n"
        f"Churned customers (90+ days inactive): {total_churn_90}\n"
        f"Largest RFM segment: {segment_top}\n"
    )
    (output_dir / "summary.txt").write_text(summary, encoding="utf-8")
    print(summary)


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

    if not queries:
        raise RuntimeError("No named SQL queries found in Phase 3 SQL file.")

    sns.set_theme(style="whitegrid")

    with sqlite3.connect(db_path) as conn:
        results = run_queries(conn, queries, output_dir)

    plot_retention_heatmap(results["cohort_retention"], output_dir, args.max_cohort_index)
    plot_segment_sizes(results["rfm_segment_sizes"], output_dir)
    write_summary(results["churn_90_plus_days"], results["rfm_segment_sizes"], output_dir)

    print(f"Outputs written to: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
