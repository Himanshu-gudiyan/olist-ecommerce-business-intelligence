from pathlib import Path
import sqlite3
import pandas as pd


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

DB_PATH = ROOT / "database" / "olist_analytics.db"
OUTPUT_DIR = ROOT / "outputs" / "phase7"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

conn = sqlite3.connect(DB_PATH)


# ============================================================
# KPI QUERY
# ============================================================

kpi_query = """
WITH delivered_orders AS (

    SELECT *
    FROM fact_orders
    WHERE order_status = 'delivered'
),

customer_orders AS (

    SELECT
        dc.customer_unique_id,
        COUNT(DISTINCT fo.order_id) AS order_count
    FROM fact_orders fo
    JOIN dim_customer dc
        ON fo.customer_id = dc.customer_id
    WHERE fo.order_status = 'delivered'
    GROUP BY dc.customer_unique_id
),

monthly_sales AS (

    SELECT
        order_year_month,
        SUM(order_revenue) AS revenue,
        COUNT(*) AS orders
    FROM delivered_orders
    GROUP BY order_year_month
),

delayed_orders AS (

    SELECT
        COUNT(*) AS delayed_orders
    FROM delivered_orders
    WHERE is_delayed = 1
)

SELECT

    -- Orders
    (SELECT COUNT(*)
     FROM delivered_orders)
        AS delivered_orders,

    -- Revenue
    ROUND(
        (SELECT SUM(order_revenue)
         FROM delivered_orders),
        2
    ) AS total_revenue,

    -- AOV
    ROUND(
        (SELECT AVG(order_revenue)
         FROM delivered_orders),
        2
    ) AS average_order_value,

    -- Customers
    (SELECT COUNT(*)
     FROM customer_orders)
        AS unique_customers,

    -- Repeat customers
    (SELECT COUNT(*)
     FROM customer_orders
     WHERE order_count > 1)
        AS repeat_customers,

    -- Repeat rate
    ROUND(
        (
            SELECT COUNT(*)
            FROM customer_orders
            WHERE order_count > 1
        ) * 100.0
        /
        NULLIF(
            (SELECT COUNT(*)
             FROM customer_orders),
            0
        ),
        2
    ) AS repeat_customer_rate,

    -- Delivery
    ROUND(
        (SELECT AVG(delivery_days)
         FROM delivered_orders),
        2
    ) AS average_delivery_days,

    -- Estimated delivery
    ROUND(
        (SELECT AVG(estimated_delivery_days)
         FROM delivered_orders),
        2
    ) AS average_estimated_delivery_days,

    -- Delay
    ROUND(
        (SELECT AVG(delivery_delay_days)
         FROM delivered_orders),
        2
    ) AS average_delivery_delay_days,

    -- Delayed orders
    (SELECT delayed_orders
     FROM delayed_orders)
        AS delayed_orders,

    -- Delayed %
    ROUND(
        (SELECT delayed_orders
         FROM delayed_orders) * 100.0
        /
        NULLIF(
            (SELECT COUNT(*)
             FROM delivered_orders),
            0
        ),
        2
    ) AS delayed_order_rate

"""


# ============================================================
# RUN KPI QUERY
# ============================================================

kpi_df = pd.read_sql_query(
    kpi_query,
    conn
)


# ============================================================
# SAVE KPI OUTPUT
# ============================================================

kpi_path = OUTPUT_DIR / "kpi_summary.csv"

kpi_df.to_csv(
    kpi_path,
    index=False
)


# ============================================================
# MONTHLY PERFORMANCE
# ============================================================

monthly_query = """
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
"""

monthly_df = pd.read_sql_query(
    monthly_query,
    conn
)

monthly_path = OUTPUT_DIR / "monthly_performance.csv"

monthly_df.to_csv(
    monthly_path,
    index=False
)


# ============================================================
# CATEGORY PERFORMANCE
# ============================================================

category_query = """
SELECT

    COALESCE(
        p.product_category_name_english,
        p.product_category_name,
        'Unknown'
    ) AS category,

    COUNT(DISTINCT fs.order_id) AS orders,

    COUNT(*) AS items_sold,

    ROUND(
        SUM(fs.item_revenue),
        2
    ) AS revenue

FROM fact_sales fs

LEFT JOIN dim_product p
    ON fs.product_id = p.product_id

WHERE fs.order_status = 'delivered'

GROUP BY category

ORDER BY revenue DESC;
"""

category_df = pd.read_sql_query(
    category_query,
    conn
)

category_path = OUTPUT_DIR / "category_performance.csv"

category_df.to_csv(
    category_path,
    index=False
)


# ============================================================
# STATE PERFORMANCE
# ============================================================

state_query = """
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
"""

state_df = pd.read_sql_query(
    state_query,
    conn
)

state_path = OUTPUT_DIR / "state_performance.csv"

state_df.to_csv(
    state_path,
    index=False
)


# ============================================================
# PAYMENT PERFORMANCE
# ============================================================

payment_query = """
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

WHERE order_status = 'delivered'

GROUP BY primary_payment_type

ORDER BY payment_value DESC;
"""

payment_df = pd.read_sql_query(
    payment_query,
    conn
)

payment_path = OUTPUT_DIR / "payment_performance.csv"

payment_df.to_csv(
    payment_path,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print("=" * 70)
print("PHASE 7 - KPI ENGINE")
print("=" * 70)

print(f"\nDatabase: {DB_PATH}")
print(f"Output directory: {OUTPUT_DIR}")

print("\nKPI SUMMARY")
print("-" * 70)

print(
    kpi_df.to_string(
        index=False
    )
)

print("\nGenerated files:")
print(f"✓ {kpi_path}")
print(f"✓ {monthly_path}")
print(f"✓ {category_path}")
print(f"✓ {state_path}")
print(f"✓ {payment_path}")

print("\n" + "=" * 70)
print("PHASE 7 KPI ENGINE COMPLETED")
print("=" * 70)


conn.close()