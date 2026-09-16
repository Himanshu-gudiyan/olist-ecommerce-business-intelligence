-- ============================================================
-- OLIST E-COMMERCE BUSINESS INTELLIGENCE
-- Phase 6 - Analytical SQL Queries
-- Database: SQLite
-- Source: Brazilian E-Commerce Public Dataset by Olist
-- ============================================================


-- ============================================================
-- 1. TOTAL DELIVERED REVENUE AND AOV
-- ============================================================

SELECT
    COUNT(*) AS delivered_orders,
    ROUND(SUM(order_revenue), 2) AS total_revenue,
    ROUND(
        SUM(order_revenue) / COUNT(*),
        2
    ) AS average_order_value
FROM fact_orders
WHERE order_status = 'delivered';


-- ============================================================
-- 2. MONTHLY REVENUE AND MONTH-OVER-MONTH GROWTH
-- ============================================================

WITH monthly_sales AS (
    SELECT
        order_year_month,
        SUM(order_revenue) AS revenue
    FROM fact_orders
    WHERE order_status = 'delivered'
    GROUP BY order_year_month
)

SELECT
    order_year_month,
    ROUND(revenue, 2) AS revenue,

    ROUND(
        LAG(revenue) OVER (
            ORDER BY order_year_month
        ),
        2
    ) AS previous_month_revenue,

    ROUND(
        (
            revenue
            - LAG(revenue) OVER (
                ORDER BY order_year_month
            )
        )
        * 100.0
        /
        NULLIF(
            LAG(revenue) OVER (
                ORDER BY order_year_month
            ),
            0
        ),
        2
    ) AS mom_growth_percent

FROM monthly_sales
ORDER BY order_year_month;


-- ============================================================
-- 3. TOP PRODUCT CATEGORIES BY REVENUE
-- ============================================================

-- ============================================================
-- 3. TOP PRODUCT CATEGORIES BY REVENUE
-- ============================================================

SELECT
    COALESCE(
        p.product_category_name_english,
        p.product_category_name,
        'Unknown'
    ) AS category,

    COUNT(DISTINCT s.order_id) AS orders,

    COUNT(*) AS items,

    ROUND(
        SUM(s.item_revenue),
        2
    ) AS revenue

FROM fact_sales s

LEFT JOIN dim_product p
    ON s.product_id = p.product_id

WHERE s.order_status = 'delivered'

GROUP BY category

ORDER BY revenue DESC

LIMIT 20;

-- ============================================================
-- 4. REPEAT CUSTOMERS
-- ============================================================

-- ============================================================
-- 4. REPEAT CUSTOMER RATE
-- ============================================================

WITH customer_orders AS (
    SELECT
        dc.customer_unique_id,
        COUNT(DISTINCT fo.order_id) AS order_count
    FROM fact_orders fo
    JOIN dim_customer dc
        ON fo.customer_id = dc.customer_id
    GROUP BY dc.customer_unique_id
)

SELECT
    COUNT(*) AS total_customers,

    SUM(
        CASE
            WHEN order_count > 1 THEN 1
            ELSE 0
        END
    ) AS repeat_customers,

    ROUND(
        SUM(
            CASE
                WHEN order_count > 1 THEN 1
                ELSE 0
            END
        ) * 100.0 / COUNT(*),
        2
    ) AS repeat_customer_rate_percent

FROM customer_orders;

-- ============================================================
-- 5. TOP CUSTOMERS BY LIFETIME REVENUE
-- ============================================================

SELECT
    dc.customer_unique_id,

    COUNT(DISTINCT fo.order_id) AS orders,

    ROUND(
        SUM(fo.order_revenue),
        2
    ) AS lifetime_revenue,

    ROUND(
        AVG(fo.order_revenue),
        2
    ) AS average_order_value,

    MIN(
        fo.order_purchase_timestamp
    ) AS first_purchase,

    MAX(
        fo.order_purchase_timestamp
    ) AS last_purchase

FROM fact_orders fo

JOIN dim_customer dc
    ON fo.customer_id = dc.customer_id

WHERE fo.order_status = 'delivered'

GROUP BY dc.customer_unique_id

ORDER BY lifetime_revenue DESC

LIMIT 20;

-- ============================================================
-- 6. TOP SELLERS BY REVENUE
-- ============================================================

SELECT
    seller_id,

    COUNT(DISTINCT order_id) AS orders,

    COUNT(*) AS items,

    ROUND(
        SUM(item_revenue),
        2
    ) AS revenue

FROM fact_sales

WHERE order_status = 'delivered'

GROUP BY seller_id

ORDER BY revenue DESC

LIMIT 20;


-- ============================================================
-- 7. SELLER PERFORMANCE
-- ============================================================

WITH seller_orders AS (
    SELECT DISTINCT
        fs.seller_id,
        fs.order_id
    FROM fact_sales fs
    WHERE fs.order_status = 'delivered'
),

seller_order_metrics AS (
    SELECT
        so.seller_id,
        fo.order_id,
        fo.review_score,
        fo.delivery_days,
        fo.is_delayed
    FROM seller_orders so
    JOIN fact_orders fo
        ON so.order_id = fo.order_id
    WHERE fo.order_status = 'delivered'
)

SELECT
    seller_id,

    COUNT(DISTINCT order_id) AS orders,

    ROUND(
        AVG(review_score),
        2
    ) AS avg_review_score,

    ROUND(
        AVG(delivery_days),
        2
    ) AS avg_delivery_days,

    ROUND(
        AVG(
            CASE
                WHEN is_delayed = 1 THEN 1.0
                ELSE 0.0
            END
        ) * 100,
        2
    ) AS delayed_order_percent

FROM seller_order_metrics

GROUP BY seller_id

ORDER BY avg_review_score DESC;
-- ============================================================
-- 8. DELIVERY KPIs
-- ============================================================

SELECT

    COUNT(*) AS delivered_orders,

    ROUND(
        AVG(delivery_days),
        2
    ) AS avg_delivery_days,

    ROUND(
        AVG(estimated_delivery_days),
        2
    ) AS avg_estimated_delivery_days,

    ROUND(
        AVG(delivery_delay_days),
        2
    ) AS avg_delay_days,

    SUM(
        CASE
            WHEN is_delayed = 1 THEN 1
            ELSE 0
        END
    ) AS delayed_orders,

    ROUND(
        AVG(
            CASE
                WHEN is_delayed = 1 THEN 1.0
                ELSE 0.0
            END
        ) * 100,
        2
    ) AS delayed_order_percent

FROM fact_orders

WHERE order_status = 'delivered';


-- ============================================================
-- 9. REVENUE BY CUSTOMER STATE
-- ============================================================

SELECT
    dc.customer_state,

    COUNT(DISTINCT fo.order_id) AS orders,

    ROUND(
        SUM(fo.order_revenue),
        2
    ) AS revenue,

    ROUND(
        AVG(fo.order_revenue),
        2
    ) AS average_order_value

FROM fact_orders fo

JOIN dim_customer dc
    ON fo.customer_id = dc.customer_id

WHERE fo.order_status = 'delivered'

GROUP BY dc.customer_state

ORDER BY revenue DESC;
-- ============================================================
-- 10. REVIEW SCORE VS DELIVERY DELAY
-- ============================================================

SELECT
    review_score,

    COUNT(*) AS orders,

    ROUND(
        AVG(delivery_days),
        2
    ) AS avg_delivery_days,

    ROUND(
        AVG(delivery_delay_days),
        2
    ) AS avg_delay_days,

    ROUND(
        AVG(
            CASE
                WHEN is_delayed = 1 THEN 1.0
                ELSE 0.0
            END
        ) * 100,
        2
    ) AS delayed_percent

FROM fact_orders

WHERE
    order_status = 'delivered'
    AND review_score IS NOT NULL

GROUP BY review_score

ORDER BY review_score;


-- ============================================================
-- 11. PAYMENT TYPE DISTRIBUTION
-- ============================================================

SELECT
    primary_payment_type AS payment_type,

    COUNT(*) AS orders,

    ROUND(
        SUM(payment_total),
        2
    ) AS payment_value,

    ROUND(
        AVG(payment_total),
        2
    ) AS average_payment_value

FROM fact_orders

WHERE primary_payment_type IS NOT NULL

GROUP BY primary_payment_type

ORDER BY payment_value DESC;


-- ============================================================
-- 12. CATEGORY REVENUE SHARE
-- ============================================================

WITH category_revenue AS (
    SELECT
        COALESCE(
            p.product_category_name_english,
            p.product_category_name,
            'Unknown'
        ) AS category,

        SUM(fs.item_revenue) AS revenue

    FROM fact_sales fs

    LEFT JOIN dim_product p
        ON fs.product_id = p.product_id

    WHERE fs.order_status = 'delivered'

    GROUP BY category
),

total_revenue AS (
    SELECT
        SUM(revenue) AS total_revenue
    FROM category_revenue
)

SELECT
    category,

    ROUND(
        revenue,
        2
    ) AS revenue,

    ROUND(
        revenue * 100.0 / NULLIF(total_revenue, 0),
        2
    ) AS revenue_share_percent

FROM category_revenue

CROSS JOIN total_revenue

ORDER BY revenue DESC

LIMIT 10;


-- ============================================================
-- 13. MONTHLY ORDER VOLUME
-- ============================================================

SELECT
    order_year_month,

    COUNT(*) AS orders,

    ROUND(
        SUM(order_revenue),
        2
    ) AS revenue,

    ROUND(
        AVG(order_revenue),
        2
    ) AS average_order_value

FROM fact_orders

WHERE order_status = 'delivered'

GROUP BY order_year_month

ORDER BY order_year_month;


-- ============================================================
-- 14. PAYMENT BEHAVIOR
-- ============================================================

SELECT

    CASE
        WHEN payment_rows > 1
            THEN 'Multiple Payments'
        ELSE 'Single Payment'
    END AS payment_behavior,

    COUNT(*) AS orders,

    ROUND(
        SUM(payment_total),
        2
    ) AS payment_value,

    ROUND(
        AVG(payment_total),
        2
    ) AS average_payment

FROM fact_orders

GROUP BY payment_behavior;


-- ============================================================
-- 15. TOP PRODUCTS BY REVENUE
-- ============================================================

SELECT
    fs.product_id,

    COALESCE(
        p.product_category_name_english,
        p.product_category_name,
        'Unknown'
    ) AS category,

    COUNT(*) AS items_sold,

    COUNT(DISTINCT fs.order_id) AS orders,

    ROUND(
        SUM(fs.item_revenue),
        2
    ) AS revenue

FROM fact_sales fs

LEFT JOIN dim_product p
    ON fs.product_id = p.product_id

WHERE fs.order_status = 'delivered'

GROUP BY
    fs.product_id,
    category

ORDER BY revenue DESC

LIMIT 20;


-- ============================================================
-- 16. DELIVERY PERFORMANCE BY CUSTOMER STATE
-- ============================================================

SELECT
    dc.customer_state,

    COUNT(*) AS delivered_orders,

    ROUND(
        AVG(fo.delivery_days),
        2
    ) AS avg_delivery_days,

    ROUND(
        AVG(fo.delivery_delay_days),
        2
    ) AS avg_delay_days,

    ROUND(
        AVG(
            CASE
                WHEN fo.is_delayed = 1 THEN 1.0
                ELSE 0.0
            END
        ) * 100,
        2
    ) AS delayed_percent

FROM fact_orders fo

JOIN dim_customer dc
    ON fo.customer_id = dc.customer_id

WHERE fo.order_status = 'delivered'

GROUP BY dc.customer_state

ORDER BY delayed_percent DESC;
-- ============================================================
-- 17. MULTI-PAYMENT ORDERS
-- ============================================================

SELECT

    COUNT(*) AS multiple_payment_orders,

    ROUND(
        SUM(payment_total),
        2
    ) AS payment_value,

    ROUND(
        AVG(payment_total),
        2
    ) AS average_payment_value

FROM fact_orders

WHERE payment_rows > 1;


-- ============================================================
-- 18. QUARTERLY SALES
-- ============================================================

WITH quarterly_sales AS (
    SELECT
        CAST(
            strftime('%Y', order_purchase_timestamp)
            AS INTEGER
        ) AS order_year,

        CAST(
            (
                CAST(
                    strftime('%m', order_purchase_timestamp)
                    AS INTEGER
                ) + 2
            ) / 3
            AS INTEGER
        ) AS quarter_number,

        SUM(order_revenue) AS revenue,

        COUNT(*) AS orders

    FROM fact_orders

    WHERE order_status = 'delivered'

    GROUP BY
        order_year,
        quarter_number
)

SELECT
    order_year,

    'Q' || quarter_number AS quarter,

    ROUND(
        revenue,
        2
    ) AS revenue,

    orders

FROM quarterly_sales

ORDER BY
    order_year,
    quarter_number;