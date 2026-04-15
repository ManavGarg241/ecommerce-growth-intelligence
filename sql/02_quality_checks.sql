DROP TABLE IF EXISTS etl_quality_checks;
CREATE TABLE etl_quality_checks AS
SELECT
    'stg_orders_row_count' AS check_name,
    CAST(COUNT(*) AS TEXT) AS check_value
FROM stg_orders
UNION ALL
SELECT
    'fact_orders_row_count' AS check_name,
    CAST(COUNT(*) AS TEXT) AS check_value
FROM fact_orders
UNION ALL
SELECT
    'distinct_orders_in_fact' AS check_name,
    CAST(COUNT(DISTINCT order_id) AS TEXT) AS check_value
FROM fact_orders
UNION ALL
SELECT
    'null_order_id_in_fact' AS check_name,
    CAST(SUM(CASE WHEN order_id IS NULL THEN 1 ELSE 0 END) AS TEXT) AS check_value
FROM fact_orders
UNION ALL
SELECT
    'unknown_category_rows' AS check_name,
    CAST(SUM(CASE WHEN product_category_name_english = 'unknown' THEN 1 ELSE 0 END) AS TEXT) AS check_value
FROM fact_orders
UNION ALL
SELECT
    'cancelled_order_rows' AS check_name,
    CAST(SUM(CASE WHEN order_status = 'canceled' THEN 1 ELSE 0 END) AS TEXT) AS check_value
FROM fact_orders;
