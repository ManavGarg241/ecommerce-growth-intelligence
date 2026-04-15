# E-Commerce Growth Intelligence System

End-to-end analytics project that simulates a category analyst workflow using the Olist Brazilian E-Commerce dataset. Covers SQL data engineering, business insight generation, cohort & RFM analysis, demand forecasting, and an interactive multi-page dashboard.

🔗 **Live Dashboard:** [your-app-name.streamlit.app](https://your-app-name.streamlit.app)

![Dashboard Screenshot](reports/screenshot.png)

---

## Key Insights Uncovered

- Top 3 categories drive **X%** of total GMV
- Cohort analysis revealed **X%** of customers never reorder — highlighting single-purchase behavior as a key business risk
- SARIMA demand forecast achieved **<X% MAPE** on a held-out 12-week test set
- RFM segmentation identified **~X%** At-Risk Champions as the highest-value reactivation target
- Strongest demand concentration in **[state/city]**, with **[category]** showing highest MoM growth

---

## Tech Stack

- **SQL** — SQLite for local development; PostgreSQL-ready modeling approach
- **Python** — Pandas, SQLAlchemy, Matplotlib, Seaborn
- **Forecasting** — SARIMA with MAPE evaluation
- **Dashboard** — Streamlit (multi-page, deployed on Streamlit Cloud)

---

## Project Structure

```text
.
|-- data/
|   |-- raw/                # Kaggle CSV files
|   `-- processed/
|-- dashboard/              # Streamlit app (Phase 5)
|-- notebooks/              # EDA and modeling notebooks
|-- reports/                # Generated CSVs, charts, and visuals
|   |-- phase2/
|   |-- phase3/
|   `-- phase4/
|-- sql/
|   |-- 01_transform_and_fact_orders.sql
|   |-- 02_quality_checks.sql
|   |-- 03_phase2_business_insights.sql
|   |-- 04_phase3_cohort_rfm.sql
|   `-- 05_phase4_demand_forecasting.sql
|-- src/
|   |-- etl/
|   |   |-- download_kaggle.py
|   |   `-- load_to_sqlite.py
|   `-- analysis/
|       |-- phase2_business_insights.py
|       |-- phase3_cohort_rfm.py
|       `-- phase4_forecasting.py
|-- requirements.txt
`-- README.md
```

---

## Quick Start

1. Create and activate a Python environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure Kaggle API credentials on your machine (`kaggle.json`).
4. Download all Olist CSV files:

```bash
python src/etl/download_kaggle.py --output-dir data/raw
```

5. Build the SQLite database and transformed analytics tables:

```bash
python src/etl/load_to_sqlite.py --data-dir data/raw --db-path data/processed/olist_analytics.db --usd-rate 0.20
```

---

## Data Sources

Kaggle dataset: `olistbr/brazilian-ecommerce`

9 source tables: customers, geolocation, order items, order payments, order reviews, orders, products, sellers, and product category translations.

---

## What Each Phase Delivers

| Phase | Focus | Output |
|-------|-------|--------|
| 1 — Data Engineering | ETL pipeline, schema design, fact table | Clean `fact_orders` table, SQL quality checks |
| 2 — Business Insights | Revenue, pricing, conversion, geography | CSVs + charts in `reports/phase2` |
| 3 — Cohort & RFM | Retention heatmap, churn list, RFM segments | Segment tables + visuals in `reports/phase3` |
| 4 — Forecasting | SARIMA demand forecast, MAPE evaluation | Per-category forecasts in `reports/phase4` |
| 5 — Dashboard | Interactive multi-page Streamlit app | Live deployed dashboard |

---

## Run Commands

**Phase 2 — Business Insights:**
```bash
python src/analysis/phase2_business_insights.py --db-path data/processed/olist_analytics.db --sql-file sql/03_phase2_business_insights.sql --output-dir reports/phase2
```

**Phase 3 — Cohort & RFM:**
```bash
python src/analysis/phase3_cohort_rfm.py --db-path data/processed/olist_analytics.db --sql-file sql/04_phase3_cohort_rfm.sql --output-dir reports/phase3 --max-cohort-index 12
```

**Phase 4 — Forecasting:**
```bash
python src/analysis/phase4_forecasting.py --db-path data/processed/olist_analytics.db --sql-file sql/05_phase4_demand_forecasting.sql --output-dir reports/phase4 --top-n 3 --test-weeks 12 --future-weeks 12
```

**Phase 5 — Dashboard (local):**
```bash
streamlit run dashboard/Home.py
```

---