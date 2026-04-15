import argparse
import zipfile
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi

DATASET_SLUG = "olistbr/brazilian-ecommerce"
EXPECTED_FILES = {
    "olist_customers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download and extract Olist dataset from Kaggle.")
    parser.add_argument("--output-dir", default="data/raw", help="Directory to save extracted CSV files.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    api = KaggleApi()
    api.authenticate()

    api.dataset_download_files(
        DATASET_SLUG,
        path=str(output_dir),
        unzip=False,
        quiet=False,
    )

    zip_path = output_dir / "brazilian-ecommerce.zip"
    if not zip_path.exists():
        raise FileNotFoundError(f"Expected download archive not found: {zip_path}")

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(output_dir)

    existing_csvs = {p.name for p in output_dir.glob("*.csv")}
    missing = EXPECTED_FILES - existing_csvs
    if missing:
        raise RuntimeError(f"Download complete but missing files: {sorted(missing)}")

    print("Download and extraction successful.")
    print(f"CSV files available in: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
