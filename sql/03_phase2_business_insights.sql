-- name: category_gmv_by_month
WITH monthly AS (
    SELECT
        strftime('%Y-%m', order_purchase_timestamp) AS order_month,
        COALESCE(product_category_name_english, 'unknown') AS category,
        SUM(item_gmv_brl) AS gmv_brl,
        SUM(item_gmv_usd) AS gmv_usd
    FROM fact_orders
    WHERE order_purchase_timestamp IS NOT NULL
    GROUP BY 1, 2
),
ranked AS (
    SELECT
        order_month,
        category,
        gmv_brl,
        gmv_usd,
        LAG(gmv_brl) OVER (PARTITION BY category ORDER BY order_month) AS prev_month_gmv_brl
    FROM monthly
)
SELECT
    order_month,
    category,
    ROUND(gmv_brl, 2) AS gmv_brl,
    ROUND(gmv_usd, 2) AS gmv_usd,
    ROUND(
        CASE
            WHEN prev_month_gmv_brl IS NULL OR prev_month_gmv_brl = 0 THEN NULL
            ELSE ((gmv_brl - prev_month_gmv_brl) / prev_month_gmv_brl) * 100
        END,
        2
    ) AS mom_growth_pct
FROM ranked
ORDER BY order_month, gmv_brl DESC;

-- name: top_categories_total_gmv
SELECT
    COALESCE(product_category_name_english, 'unknown') AS category,
    ROUND(SUM(item_gmv_brl), 2) AS total_gmv_brl,
    ROUND(SUM(item_gmv_usd), 2) AS total_gmv_usd,
    COUNT(DISTINCT order_id) AS order_count
FROM fact_orders
GROUP BY 1
ORDER BY total_gmv_brl DESC;

-- name: conversion_funnel_by_category
WITH order_level AS (
    SELECT DISTINCT
        order_id,
        COALESCE(product_category_name_english, 'unknown') AS category,
        order_status,
        CASE WHEN order_approved_at IS NOT NULL THEN 1 ELSE 0 END AS is_approved,
        CASE WHEN order_status = 'canceled' THEN 1 ELSE 0 END AS is_canceled
    FROM fact_orders
)
SELECT
    category,
    COUNT(*) AS orders,
    SUM(is_approved) AS approved_orders,
    SUM(is_canceled) AS canceled_orders,
    ROUND(100.0 * SUM(is_approved) / COUNT(*), 2) AS approval_rate_pct,
    ROUND(100.0 * SUM(is_canceled) / COUNT(*), 2) AS cancellation_rate_pct
FROM order_level
GROUP BY category
HAVING COUNT(*) >= 50
ORDER BY orders DESC;

-- name: pricing_distribution_by_category
SELECT
    COALESCE(product_category_name_english, 'unknown') AS category,
    item_price_brl,
    avg_review_score
FROM fact_orders
WHERE item_price_brl IS NOT NULL
  AND avg_review_score IS NOT NULL;

-- name: seller_performance
SELECT
    seller_id,
    ROUND(SUM(item_gmv_brl), 2) AS seller_gmv_brl,
    COUNT(DISTINCT order_id) AS seller_orders,
    ROUND(AVG(delivery_days), 2) AS avg_delivery_days,
    ROUND(AVG(avg_review_score), 2) AS avg_review_score
FROM fact_orders
WHERE seller_id IS NOT NULL
GROUP BY seller_id
HAVING COUNT(DISTINCT order_id) >= 20
ORDER BY seller_gmv_brl DESC;

-- name: delivery_time_vs_rating
SELECT
    seller_id,
    ROUND(AVG(delivery_days), 2) AS avg_delivery_days,
    ROUND(AVG(avg_review_score), 2) AS avg_review_score,
    COUNT(DISTINCT order_id) AS order_count
FROM fact_orders
WHERE seller_id IS NOT NULL
  AND delivery_days IS NOT NULL
  AND avg_review_score IS NOT NULL
GROUP BY seller_id
HAVING COUNT(DISTINCT order_id) >= 20
ORDER BY order_count DESC;

-- name: geographic_category_demand
SELECT
    customer_state,
    customer_city,
    COALESCE(product_category_name_english, 'unknown') AS category,
    COUNT(DISTINCT order_id) AS orders,
    ROUND(SUM(item_gmv_brl), 2) AS gmv_brl
FROM fact_orders
WHERE customer_state IS NOT NULL
GROUP BY customer_state, customer_city, category
HAVING COUNT(DISTINCT order_id) >= 10
ORDER BY gmv_brl DESC;
