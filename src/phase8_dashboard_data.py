from pathlib import Path
import sqlite3
import pandas as pd


# ============================================================
# PATH CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "olist_analytics.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """Create a read-only SQLite connection."""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_PATH}"
        )

    return sqlite3.connect(DB_PATH)


# ============================================================
# GENERIC QUERY RUNNER
# ============================================================

def run_query(query, params=None):
    """Run a SQL query and return a pandas DataFrame."""

    conn = get_connection()

    try:
        if params is None:
            return pd.read_sql_query(query, conn)

        return pd.read_sql_query(query, conn, params=params)

    finally:
        conn.close()


# ============================================================
# DATABASE VALIDATION
# ============================================================

def validate_database():

    query = """
    SELECT
        (SELECT COUNT(*) FROM fact_orders) AS fact_orders,
        (SELECT COUNT(*) FROM fact_sales) AS fact_sales,
        (SELECT COUNT(*) FROM dim_customer) AS customers,
        (SELECT COUNT(*) FROM dim_product) AS products,
        (SELECT COUNT(*) FROM dim_seller) AS sellers
    """

    return run_query(query)


# ============================================================
# EXECUTIVE KPIs
# ============================================================

def get_kpis():

    query = """
    SELECT
        COUNT(*) AS total_orders,

        COUNT(
            CASE
                WHEN order_status = 'delivered'
                THEN 1
            END
        ) AS delivered_orders,

        ROUND(
            SUM(
                CASE
                    WHEN order_status = 'delivered'
                    THEN order_revenue
                    ELSE 0
                END
            ),
            2
        ) AS total_revenue,

        ROUND(
            AVG(
                CASE
                    WHEN order_status = 'delivered'
                    THEN order_revenue
                END
            ),
            2
        ) AS average_order_value,

        ROUND(
            AVG(
                CASE
                    WHEN order_status = 'delivered'
                    THEN delivery_days
                END
            ),
            2
        ) AS average_delivery_days,

        SUM(
            CASE
                WHEN order_status = 'delivered'
                AND is_delayed = 1
                THEN 1
                ELSE 0
            END
        ) AS delayed_orders,

        ROUND(
            100.0 *
            SUM(
                CASE
                    WHEN order_status = 'delivered'
                    AND is_delayed = 1
                    THEN 1
                    ELSE 0
                END
            )
            /
            NULLIF(
                COUNT(
                    CASE
                        WHEN order_status = 'delivered'
                        THEN 1
                    END
                ),
                0
            ),
            2
        ) AS delayed_rate

    FROM fact_orders
    """

    return run_query(query)


# ============================================================
# MONTHLY PERFORMANCE
# ============================================================

def get_monthly_revenue():

    query = """
    SELECT
        order_year_month,

        COUNT(*) AS orders,

        ROUND(
            SUM(
                CASE
                    WHEN order_status = 'delivered'
                    THEN order_revenue
                    ELSE 0
                END
            ),
            2
        ) AS revenue,

        ROUND(
            AVG(
                CASE
                    WHEN order_status = 'delivered'
                    THEN order_revenue
                END
            ),
            2
        ) AS average_order_value

    FROM fact_orders

    GROUP BY order_year_month

    ORDER BY order_year_month
    """

    return run_query(query)


# ============================================================
# CATEGORY PERFORMANCE
# ============================================================

def get_category_revenue(limit=20):

    query = """
    SELECT
        COALESCE(
            dp.product_category_name_english,
            dp.product_category_name,
            'Unknown'
        ) AS category,

        COUNT(DISTINCT fs.order_id) AS orders,

        COUNT(*) AS items,

        ROUND(
            SUM(fs.item_revenue),
            2
        ) AS revenue

    FROM fact_sales fs

    LEFT JOIN dim_product dp
        ON fs.product_id = dp.product_id

    WHERE fs.order_status = 'delivered'

    GROUP BY category

    ORDER BY revenue DESC

    LIMIT ?
    """

    return run_query(query, (limit,))


# ============================================================
# STATE / GEOGRAPHIC PERFORMANCE
# ============================================================

def get_state_revenue():

    query = """
    SELECT
        dc.customer_state AS state,

        COUNT(DISTINCT fo.order_id) AS orders,

        ROUND(
            SUM(
                CASE
                    WHEN fo.order_status = 'delivered'
                    THEN fo.order_revenue
                    ELSE 0
                END
            ),
            2
        ) AS revenue,

        ROUND(
            AVG(
                CASE
                    WHEN fo.order_status = 'delivered'
                    THEN fo.order_revenue
                END
            ),
            2
        ) AS average_order_value

    FROM fact_orders fo

    LEFT JOIN dim_customer dc
        ON fo.customer_id = dc.customer_id

    GROUP BY dc.customer_state

    ORDER BY revenue DESC
    """

    return run_query(query)


# ============================================================
# PAYMENT PERFORMANCE
# ============================================================

def get_payment_performance():

    query = """
    SELECT
        op.payment_type,

        COUNT(DISTINCT op.order_id) AS orders,

        ROUND(
            SUM(op.payment_value),
            2
        ) AS revenue,

        ROUND(
            AVG(op.payment_value),
            2
        ) AS average_payment_value

    FROM order_payments op

    INNER JOIN fact_orders fo
        ON op.order_id = fo.order_id

    WHERE fo.order_status = 'delivered'

    GROUP BY op.payment_type

    ORDER BY revenue DESC
    """

    return run_query(query)
# ============================================================
# DELIVERY PERFORMANCE
# ============================================================

def get_delivery_performance():

    query = """
    SELECT

        COUNT(
            CASE
                WHEN order_status = 'delivered'
                THEN 1
            END
        ) AS delivered_orders,

        ROUND(
            AVG(
                CASE
                    WHEN order_status = 'delivered'
                    THEN delivery_days
                END
            ),
            2
        ) AS average_delivery_days,

        ROUND(
            AVG(
                CASE
                    WHEN order_status = 'delivered'
                    THEN estimated_delivery_days
                END
            ),
            2
        ) AS average_estimated_days,

        ROUND(
            AVG(
                CASE
                    WHEN order_status = 'delivered'
                    THEN delivery_delay_days
                END
            ),
            2
        ) AS average_delay_days,

        SUM(
            CASE
                WHEN order_status = 'delivered'
                AND is_delayed = 1
                THEN 1
                ELSE 0
            END
        ) AS delayed_orders,

        ROUND(
            100.0 *
            SUM(
                CASE
                    WHEN order_status = 'delivered'
                    AND is_delayed = 1
                    THEN 1
                    ELSE 0
                END
            )
            /
            NULLIF(
                COUNT(
                    CASE
                        WHEN order_status = 'delivered'
                        THEN 1
                    END
                ),
                0
            ),
            2
        ) AS delayed_rate

    FROM fact_orders
    """

    return run_query(query)


# ============================================================
# CUSTOMER METRICS
# ============================================================

def get_customer_metrics():

    query = """
    WITH customer_orders AS (

        SELECT
            dc.customer_unique_id,

            COUNT(DISTINCT fo.order_id) AS order_count,

            SUM(
                CASE
                    WHEN fo.order_status = 'delivered'
                    THEN fo.order_revenue
                    ELSE 0
                END
            ) AS revenue

        FROM fact_orders fo

        INNER JOIN dim_customer dc
            ON fo.customer_id = dc.customer_id

        GROUP BY dc.customer_unique_id
    )

    SELECT

        COUNT(*) AS total_customers,

        SUM(
            CASE
                WHEN order_count = 1
                THEN 1
                ELSE 0
            END
        ) AS one_time_customers,

        SUM(
            CASE
                WHEN order_count > 1
                THEN 1
                ELSE 0
            END
        ) AS repeat_customers,

        ROUND(
            100.0 *
            SUM(
                CASE
                    WHEN order_count > 1
                    THEN 1
                    ELSE 0
                END
            )
            /
            NULLIF(COUNT(*), 0),
            2
        ) AS repeat_customer_rate,

        ROUND(
            SUM(revenue),
            2
        ) AS customer_revenue

    FROM customer_orders
    """

    return run_query(query)


# ============================================================
# SELLER PERFORMANCE
# ============================================================

def get_seller_performance(limit=20):

    query = """
    SELECT

        fs.seller_id,

        COUNT(DISTINCT fs.order_id) AS orders,

        COUNT(*) AS items,

        ROUND(
            SUM(fs.item_revenue),
            2
        ) AS revenue

    FROM fact_sales fs

    WHERE fs.order_status = 'delivered'

    GROUP BY fs.seller_id

    ORDER BY revenue DESC

    LIMIT ?
    """

    return run_query(query, (limit,))


# ============================================================
# PRODUCT PERFORMANCE
# ============================================================

def get_product_performance(limit=20):

    query = """
    SELECT

        fs.product_id,

        COALESCE(
            dp.product_category_name_english,
            dp.product_category_name,
            'Unknown'
        ) AS category,

        COUNT(DISTINCT fs.order_id) AS orders,

        COUNT(*) AS items,

        ROUND(
            SUM(fs.item_revenue),
            2
        ) AS revenue

    FROM fact_sales fs

    LEFT JOIN dim_product dp
        ON fs.product_id = dp.product_id

    WHERE fs.order_status = 'delivered'

    GROUP BY
        fs.product_id,
        category

    ORDER BY revenue DESC

    LIMIT ?
    """

    return run_query(query, (limit,))


# ============================================================
# REVIEW PERFORMANCE
# ============================================================

def get_review_performance():

    query = """
    SELECT

        review_score,

        COUNT(*) AS reviews

    FROM fact_orders

    WHERE review_score IS NOT NULL

    GROUP BY review_score

    ORDER BY review_score
    """

    return run_query(query)


# ============================================================
# FILTER OPTIONS
# ============================================================

def get_filter_options():

    states = run_query("""
        SELECT DISTINCT customer_state AS state
        FROM dim_customer
        WHERE customer_state IS NOT NULL
        ORDER BY customer_state
    """)

    categories = run_query("""
        SELECT DISTINCT
            COALESCE(
                product_category_name_english,
                product_category_name,
                'Unknown'
            ) AS category
        FROM dim_product
        ORDER BY category
    """)

    payment_types = run_query("""
        SELECT DISTINCT payment_type
        FROM fact_orders
        WHERE payment_type IS NOT NULL
        ORDER BY payment_type
    """)

    years = run_query("""
        SELECT DISTINCT order_year AS year
        FROM fact_orders
        WHERE order_year IS NOT NULL
        ORDER BY order_year
    """)

    return {
        "states": states["state"].tolist(),
        "categories": categories["category"].tolist(),
        "payment_types": payment_types["payment_type"].tolist(),
        "years": years["year"].tolist()
    }


# ============================================================
# MODULE TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("PHASE 8 DASHBOARD DATA MODULE TEST")
    print("=" * 60)

    print("\nDatabase validation:")
    print(validate_database().to_string(index=False))

    print("\nExecutive KPIs:")
    print(get_kpis().to_string(index=False))

    print("\nMonthly revenue:")
    print(get_monthly_revenue().head().to_string(index=False))

    print("\nTop categories:")
    print(get_category_revenue(10).to_string(index=False))

    print("\nPayment performance:")
    print(get_payment_performance().to_string(index=False))

    print("\nDelivery performance:")
    print(get_delivery_performance().to_string(index=False))

    print("\nCustomer metrics:")
    print(get_customer_metrics().to_string(index=False))

    print("\nPHASE 8 DASHBOARD DATA MODULE TEST PASSED")