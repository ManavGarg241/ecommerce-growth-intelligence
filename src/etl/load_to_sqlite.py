import argparse
from pathlib import Path
import sqlite3

import pandas as pd

TABLE_FILE_MAP = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "product_category_translation": "product_category_name_translation.csv",
}

DATE_COLUMNS_BY_TABLE = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_reviews": ["review_creation_date", "review_answer_timestamp"],
    "order_items": ["shipping_limit_date"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load Olist CSVs into SQLite and build analytics tables.")
    parser.add_argument("--data-dir", default="data/raw", help="Directory containing source CSV files.")
    parser.add_argument(
        "--db-path",
        default="data/processed/olist_analytics.db",
        help="Output path for SQLite database file.",
    )
    parser.add_argument(
        "--usd-rate",
        default=0.20,
        type=float,
        help="Fixed BRL->USD conversion rate used for normalized currency columns.",
    )
    return parser.parse_args()


def clean_dataframe(table_name: str, df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates().copy()

    if table_name in DATE_COLUMNS_BY_TABLE:
        for col in DATE_COLUMNS_BY_TABLE[table_name]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

    if "product_category_name" in df.columns:
        df["product_category_name"] = df["product_category_name"].fillna("unknown")

    if "review_comment_title" in df.columns:
        df["review_comment_title"] = df["review_comment_title"].fillna("")

    if "review_comment_message" in df.columns:
        df["review_comment_message"] = df["review_comment_message"].fillna("")

    return df


def load_staging_tables(conn: sqlite3.Connection, data_dir: Path) -> None:
    for table_name, file_name in TABLE_FILE_MAP.items():
        file_path = data_dir / file_name
        if not file_path.exists():
            raise FileNotFoundError(f"Missing required CSV file: {file_path}")

        df = pd.read_csv(file_path)
        df = clean_dataframe(table_name, df)
        df.to_sql(f"stg_{table_name}", conn, if_exists="replace", index=False)

        print(f"Loaded stg_{table_name}: {len(df):,} rows")


def run_sql_file(conn: sqlite3.Connection, sql_path: Path, replacements: dict[str, str] | None = None) -> None:
    sql_text = sql_path.read_text(encoding="utf-8")
    if replacements:
        for key, value in replacements.items():
            sql_text = sql_text.replace(key, value)
    conn.executescript(sql_text)


def main() -> None:
    args = parse_args()
    data_dir = Path(args.data_dir)
    db_path = Path(args.db_path)

    if not data_dir.exists():
        raise FileNotFoundError(f"Data directory does not exist: {data_dir}")

    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        load_staging_tables(conn, data_dir)

        transform_sql = Path("sql/01_transform_and_fact_orders.sql")
        checks_sql = Path("sql/02_quality_checks.sql")

        run_sql_file(conn, transform_sql, replacements={"{{USD_RATE}}": str(args.usd_rate)})
        run_sql_file(conn, checks_sql)

        print("Built transformed tables and quality checks.")
        print(f"SQLite DB ready at: {db_path.resolve()}")


if __name__ == "__main__":
    main()
