-- name: weekly_category_gmv
SELECT
    DATE(order_purchase_timestamp, '-' || ((CAST(strftime('%w', order_purchase_timestamp) AS INTEGER) + 6) % 7) || ' days') AS week_start,
    COALESCE(product_category_name_english, 'unknown') AS category,
    SUM(item_gmv_brl) AS weekly_gmv_brl
FROM fact_orders
WHERE order_purchase_timestamp IS NOT NULL
  AND order_status != 'canceled'
GROUP BY week_start, category
ORDER BY week_start, category;

-- name: top_categories_by_gmv
SELECT
    COALESCE(product_category_name_english, 'unknown') AS category,
    SUM(item_gmv_brl) AS total_gmv_brl
FROM fact_orders
WHERE order_purchase_timestamp IS NOT NULL
  AND order_status != 'canceled'
GROUP BY category
ORDER BY total_gmv_brl DESC;
