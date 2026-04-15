DROP TABLE IF EXISTS dim_products;
CREATE TABLE dim_products AS
SELECT
    p.product_id,
    COALESCE(p.product_category_name, 'unknown') AS product_category_name_portuguese,
    COALESCE(t.product_category_name_english, 'unknown') AS product_category_name_english,
    p.product_name_lenght,
    p.product_description_lenght,
    p.product_photos_qty,
    p.product_weight_g,
    p.product_length_cm,
    p.product_height_cm,
    p.product_width_cm
FROM stg_products p
LEFT JOIN stg_product_category_translation t
    ON p.product_category_name = t.product_category_name;

DROP TABLE IF EXISTS fct_order_item_enriched;
CREATE TABLE fct_order_item_enriched AS
SELECT
    oi.order_id,
    oi.order_item_id,
    oi.product_id,
    oi.seller_id,
    oi.shipping_limit_date,
    CAST(oi.price AS REAL) AS item_price_brl,
    CAST(oi.freight_value AS REAL) AS freight_value_brl,
    (CAST(oi.price AS REAL) + CAST(oi.freight_value AS REAL)) AS item_gmv_brl,
    ROUND((CAST(oi.price AS REAL) + CAST(oi.freight_value AS REAL)) * {{USD_RATE}}, 2) AS item_gmv_usd,
    dp.product_category_name_english,
    dp.product_category_name_portuguese
FROM stg_order_items oi
LEFT JOIN dim_products dp
    ON oi.product_id = dp.product_id;

DROP TABLE IF EXISTS fct_order_payment_agg;
CREATE TABLE fct_order_payment_agg AS
SELECT
    op.order_id,
    SUM(CAST(op.payment_value AS REAL)) AS payment_value_brl,
    ROUND(SUM(CAST(op.payment_value AS REAL)) * {{USD_RATE}}, 2) AS payment_value_usd,
    COUNT(*) AS payment_installment_count,
    MAX(CAST(op.payment_installments AS INTEGER)) AS max_payment_installments
FROM stg_order_payments op
GROUP BY op.order_id;

DROP TABLE IF EXISTS fct_order_review_agg;
CREATE TABLE fct_order_review_agg AS
SELECT
    r.order_id,
    AVG(CAST(r.review_score AS REAL)) AS avg_review_score,
    COUNT(*) AS review_count
FROM stg_order_reviews r
GROUP BY r.order_id;

DROP TABLE IF EXISTS fact_orders;
CREATE TABLE fact_orders AS
SELECT
    o.order_id,
    o.customer_id,
    c.customer_unique_id,
    c.customer_city,
    c.customer_state,
    o.order_status,
    o.order_purchase_timestamp,
    o.order_approved_at,
    o.order_delivered_carrier_date,
    o.order_delivered_customer_date,
    o.order_estimated_delivery_date,
    CAST((julianday(o.order_delivered_customer_date) - julianday(o.order_purchase_timestamp)) AS REAL) AS delivery_days,
    ie.order_item_id,
    ie.product_id,
    ie.seller_id,
    ie.product_category_name_english,
    ie.product_category_name_portuguese,
    ie.item_price_brl,
    ie.freight_value_brl,
    ie.item_gmv_brl,
    ie.item_gmv_usd,
    p.payment_value_brl,
    p.payment_value_usd,
    p.payment_installment_count,
    p.max_payment_installments,
    r.avg_review_score,
    r.review_count
FROM stg_orders o
LEFT JOIN stg_customers c
    ON o.customer_id = c.customer_id
LEFT JOIN fct_order_item_enriched ie
    ON o.order_id = ie.order_id
LEFT JOIN fct_order_payment_agg p
    ON o.order_id = p.order_id
LEFT JOIN fct_order_review_agg r
    ON o.order_id = r.order_id;

CREATE INDEX IF NOT EXISTS idx_fact_orders_order_id ON fact_orders(order_id);
CREATE INDEX IF NOT EXISTS idx_fact_orders_purchase_ts ON fact_orders(order_purchase_timestamp);
CREATE INDEX IF NOT EXISTS idx_fact_orders_category ON fact_orders(product_category_name_english);
CREATE INDEX IF NOT EXISTS idx_fact_orders_customer_unique ON fact_orders(customer_unique_id);
