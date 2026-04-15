-- name: order_level
SELECT
    order_id,
    customer_unique_id,
    DATE(order_purchase_timestamp) AS purchase_date,
    DATE(strftime('%Y-%m-01', order_purchase_timestamp)) AS purchase_month,
    SUM(item_gmv_brl) AS order_gmv_brl
FROM fact_orders
WHERE customer_unique_id IS NOT NULL
  AND order_purchase_timestamp IS NOT NULL
GROUP BY order_id, customer_unique_id, DATE(order_purchase_timestamp), DATE(strftime('%Y-%m-01', order_purchase_timestamp));

-- name: customer_cohorts
WITH first_purchase AS (
    SELECT
        customer_unique_id,
        MIN(DATE(strftime('%Y-%m-01', purchase_date))) AS cohort_month
    FROM (
        SELECT DISTINCT order_id, customer_unique_id, purchase_date
        FROM (
            SELECT
                order_id,
                customer_unique_id,
                DATE(order_purchase_timestamp) AS purchase_date
            FROM fact_orders
            WHERE customer_unique_id IS NOT NULL
              AND order_purchase_timestamp IS NOT NULL
        )
    )
    GROUP BY customer_unique_id
)
SELECT *
FROM first_purchase
ORDER BY cohort_month, customer_unique_id;

-- name: cohort_retention
WITH orders_distinct AS (
    SELECT DISTINCT
        order_id,
        customer_unique_id,
        DATE(strftime('%Y-%m-01', order_purchase_timestamp)) AS purchase_month
    FROM fact_orders
    WHERE customer_unique_id IS NOT NULL
      AND order_purchase_timestamp IS NOT NULL
),
first_purchase AS (
    SELECT
        customer_unique_id,
        MIN(purchase_month) AS cohort_month
    FROM orders_distinct
    GROUP BY customer_unique_id
),
cohort_activity AS (
    SELECT
        fp.cohort_month,
        od.purchase_month,
        ((CAST(strftime('%Y', od.purchase_month) AS INTEGER) - CAST(strftime('%Y', fp.cohort_month) AS INTEGER)) * 12
         + (CAST(strftime('%m', od.purchase_month) AS INTEGER) - CAST(strftime('%m', fp.cohort_month) AS INTEGER))) AS cohort_index,
        od.customer_unique_id
    FROM orders_distinct od
    JOIN first_purchase fp
      ON od.customer_unique_id = fp.customer_unique_id
),
cohort_sizes AS (
    SELECT
        cohort_month,
        COUNT(DISTINCT customer_unique_id) AS cohort_size
    FROM first_purchase
    GROUP BY cohort_month
),
retention_counts AS (
    SELECT
        cohort_month,
        cohort_index,
        COUNT(DISTINCT customer_unique_id) AS retained_customers
    FROM cohort_activity
    GROUP BY cohort_month, cohort_index
)
SELECT
    rc.cohort_month,
    rc.cohort_index,
    cs.cohort_size,
    rc.retained_customers,
    ROUND(100.0 * rc.retained_customers / cs.cohort_size, 2) AS retention_rate_pct
FROM retention_counts rc
JOIN cohort_sizes cs
  ON rc.cohort_month = cs.cohort_month
ORDER BY rc.cohort_month, rc.cohort_index;

-- name: churn_90_plus_days
WITH orders_distinct AS (
    SELECT DISTINCT
        order_id,
        customer_unique_id,
        DATE(order_purchase_timestamp) AS purchase_date
    FROM fact_orders
    WHERE customer_unique_id IS NOT NULL
      AND order_purchase_timestamp IS NOT NULL
),
last_purchase AS (
    SELECT
        customer_unique_id,
        MAX(purchase_date) AS last_purchase_date,
        COUNT(DISTINCT order_id) AS lifetime_orders
    FROM orders_distinct
    GROUP BY customer_unique_id
),
anchor AS (
    SELECT MAX(purchase_date) AS max_purchase_date FROM orders_distinct
)
SELECT
    lp.customer_unique_id,
    lp.last_purchase_date,
    CAST(julianday(a.max_purchase_date) - julianday(lp.last_purchase_date) AS INTEGER) AS days_since_last_order,
    lp.lifetime_orders
FROM last_purchase lp
CROSS JOIN anchor a
WHERE CAST(julianday(a.max_purchase_date) - julianday(lp.last_purchase_date) AS INTEGER) >= 90
ORDER BY days_since_last_order DESC;

-- name: rfm_metrics
WITH orders_distinct AS (
    SELECT DISTINCT
        order_id,
        customer_unique_id,
        DATE(order_purchase_timestamp) AS purchase_date,
        item_gmv_brl
    FROM fact_orders
    WHERE customer_unique_id IS NOT NULL
      AND order_purchase_timestamp IS NOT NULL
),
customer_agg AS (
    SELECT
        customer_unique_id,
        MAX(purchase_date) AS last_purchase_date,
        COUNT(DISTINCT order_id) AS frequency,
        ROUND(SUM(item_gmv_brl), 2) AS monetary
    FROM orders_distinct
    GROUP BY customer_unique_id
),
anchor AS (
    SELECT MAX(purchase_date) AS max_purchase_date FROM orders_distinct
),
rfm_base AS (
    SELECT
        ca.customer_unique_id,
        CAST(julianday(a.max_purchase_date) - julianday(ca.last_purchase_date) AS INTEGER) AS recency,
        ca.frequency,
        ca.monetary
    FROM customer_agg ca
    CROSS JOIN anchor a
),
rfm_scores AS (
    SELECT
        customer_unique_id,
        recency,
        frequency,
        monetary,
        6 - NTILE(5) OVER (ORDER BY recency ASC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
    FROM rfm_base
)
SELECT
    customer_unique_id,
    recency,
    frequency,
    monetary,
    r_score,
    f_score,
    m_score,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Loyal'
        WHEN r_score <= 2 AND f_score >= 3 THEN 'At-Risk'
        WHEN r_score <= 2 AND f_score <= 2 THEN 'Lost'
        ELSE 'Potential'
    END AS segment
FROM rfm_scores
ORDER BY monetary DESC;

-- name: rfm_segment_sizes
WITH rfm AS (
    WITH orders_distinct AS (
        SELECT DISTINCT
            order_id,
            customer_unique_id,
            DATE(order_purchase_timestamp) AS purchase_date,
            item_gmv_brl
        FROM fact_orders
        WHERE customer_unique_id IS NOT NULL
          AND order_purchase_timestamp IS NOT NULL
    ),
    customer_agg AS (
        SELECT
            customer_unique_id,
            MAX(purchase_date) AS last_purchase_date,
            COUNT(DISTINCT order_id) AS frequency,
            ROUND(SUM(item_gmv_brl), 2) AS monetary
        FROM orders_distinct
        GROUP BY customer_unique_id
    ),
    anchor AS (
        SELECT MAX(purchase_date) AS max_purchase_date FROM orders_distinct
    ),
    rfm_base AS (
        SELECT
            ca.customer_unique_id,
            CAST(julianday(a.max_purchase_date) - julianday(ca.last_purchase_date) AS INTEGER) AS recency,
            ca.frequency,
            ca.monetary
        FROM customer_agg ca
        CROSS JOIN anchor a
    ),
    rfm_scores AS (
        SELECT
            customer_unique_id,
            recency,
            frequency,
            monetary,
            6 - NTILE(5) OVER (ORDER BY recency ASC) AS r_score,
            NTILE(5) OVER (ORDER BY frequency ASC) AS f_score,
            NTILE(5) OVER (ORDER BY monetary ASC) AS m_score
        FROM rfm_base
    )
    SELECT
        customer_unique_id,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
            WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Loyal'
            WHEN r_score <= 2 AND f_score >= 3 THEN 'At-Risk'
            WHEN r_score <= 2 AND f_score <= 2 THEN 'Lost'
            ELSE 'Potential'
        END AS segment
    FROM rfm_scores
)
SELECT
    segment,
    COUNT(*) AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct_of_customers
FROM rfm
GROUP BY segment
ORDER BY customers DESC;
