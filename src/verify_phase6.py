from pathlib import Path
import sqlite3
import pandas as pd
import sys


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

DB_PATH = ROOT / "database" / "olist_analytics.db"
SQL_PATH = ROOT / "sql" / "analytical_queries.sql"


# ============================================================
# HELPERS
# ============================================================

passed = 0
failed = 0


def check(name, condition, details=""):
    global passed, failed

    if condition:
        print(f"PASS | {name}")
        if details:
            print(f"     {details}")
        passed += 1
    else:
        print(f"FAIL | {name}")
        if details:
            print(f"     {details}")
        failed += 1


def query_df(conn, sql):
    return pd.read_sql_query(sql, conn)


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("PHASE 6 - SQL ANALYTICS VALIDATION")
print("=" * 70)

print(f"\nProject root : {ROOT}")
print(f"Database     : {DB_PATH}")
print(f"SQL file     : {SQL_PATH}")


# ============================================================
# 1. FILE EXISTENCE
# ============================================================

print("\n" + "=" * 70)
print("1. FILE VALIDATION")
print("=" * 70)

check(
    "SQLite database exists",
    DB_PATH.exists(),
    str(DB_PATH)
)

check(
    "Analytical SQL file exists",
    SQL_PATH.exists(),
    str(SQL_PATH)
)

if not DB_PATH.exists():
    print("\nDatabase not found. Run:")
    print("python src/sql_database.py")
    sys.exit(1)


# ============================================================
# DATABASE CONNECTION
# ============================================================

conn = sqlite3.connect(DB_PATH)


# ============================================================
# 2. TABLE VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("2. DATABASE TABLE VALIDATION")
print("=" * 70)

required_tables = [
    "customers",
    "orders",
    "order_items",
    "order_payments",
    "order_reviews",
    "products",
    "sellers",
    "geolocation",
    "geolocation_zip",
    "category_translation",
    "dim_customer",
    "dim_product",
    "dim_seller",
    "dim_date",
    "dim_geography",
    "fact_orders",
    "fact_sales",
]

tables_df = query_df(
    conn,
    """
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name
    """
)

existing_tables = set(tables_df["name"].tolist())

for table in required_tables:
    check(
        f"Table exists: {table}",
        table in existing_tables
    )


check(
    "Required table count",
    all(table in existing_tables for table in required_tables),
    f"{len(existing_tables)} tables currently exist"
)


# ============================================================
# 3. CORE ROW COUNT VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("3. CORE ROW COUNT VALIDATION")
print("=" * 70)

expected_counts = {
    "customers": 99441,
    "orders": 99441,
    "order_items": 112650,
    "order_payments": 103886,
    "order_reviews": 98673,
    "products": 32951,
    "sellers": 3095,
    "fact_orders": 99441,
    "fact_sales": 112650,
}

for table, expected in expected_counts.items():

    result = query_df(
        conn,
        f"SELECT COUNT(*) AS row_count FROM {table}"
    )

    actual = int(result.iloc[0]["row_count"])

    check(
        f"{table} row count",
        actual == expected,
        f"Expected: {expected:,} | Actual: {actual:,}"
    )


# ============================================================
# 4. PRIMARY KEY / GRAIN VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("4. DATA GRAIN / UNIQUENESS VALIDATION")
print("=" * 70)


# Customers
df = query_df(
    conn,
    """
    SELECT
        COUNT(*) AS total_rows,
        COUNT(DISTINCT customer_id) AS unique_keys
    FROM customers
    """
)

check(
    "customers.customer_id unique",
    df.iloc[0]["total_rows"] == df.iloc[0]["unique_keys"],
    f"Rows: {int(df.iloc[0]['total_rows']):,}"
)


# Orders
df = query_df(
    conn,
    """
    SELECT
        COUNT(*) AS total_rows,
        COUNT(DISTINCT order_id) AS unique_keys
    FROM orders
    """
)

check(
    "orders.order_id unique",
    df.iloc[0]["total_rows"] == df.iloc[0]["unique_keys"],
    f"Rows: {int(df.iloc[0]['total_rows']):,}"
)


# Products
df = query_df(
    conn,
    """
    SELECT
        COUNT(*) AS total_rows,
        COUNT(DISTINCT product_id) AS unique_keys
    FROM products
    """
)

check(
    "products.product_id unique",
    df.iloc[0]["total_rows"] == df.iloc[0]["unique_keys"],
    f"Rows: {int(df.iloc[0]['total_rows']):,}"
)


# Sellers
df = query_df(
    conn,
    """
    SELECT
        COUNT(*) AS total_rows,
        COUNT(DISTINCT seller_id) AS unique_keys
    FROM sellers
    """
)

check(
    "sellers.seller_id unique",
    df.iloc[0]["total_rows"] == df.iloc[0]["unique_keys"],
    f"Rows: {int(df.iloc[0]['total_rows']):,}"
)


# Fact orders
df = query_df(
    conn,
    """
    SELECT
        COUNT(*) AS total_rows,
        COUNT(DISTINCT order_id) AS unique_keys
    FROM fact_orders
    """
)

check(
    "fact_orders.order_id unique",
    df.iloc[0]["total_rows"] == df.iloc[0]["unique_keys"],
    f"Rows: {int(df.iloc[0]['total_rows']):,}"
)


# Fact sales
df = query_df(
    conn,
    """
    SELECT
        COUNT(*) AS total_rows,
        COUNT(
            DISTINCT order_id || '|' || CAST(order_item_id AS TEXT)
        ) AS unique_keys
    FROM fact_sales
    """
)

check(
    "fact_sales order_id + order_item_id unique",
    df.iloc[0]["total_rows"] == df.iloc[0]["unique_keys"],
    f"Rows: {int(df.iloc[0]['total_rows']):,}"
)


# ============================================================
# 5. ORPHAN / REFERENTIAL INTEGRITY CHECKS
# ============================================================

print("\n" + "=" * 70)
print("5. REFERENTIAL INTEGRITY VALIDATION")
print("=" * 70)


# order_items -> orders
df = query_df(
    conn,
    """
    SELECT COUNT(*) AS orphan_rows
    FROM order_items oi
    LEFT JOIN orders o
        ON oi.order_id = o.order_id
    WHERE o.order_id IS NULL
    """
)

orphans = int(df.iloc[0]["orphan_rows"])

check(
    "order_items -> orders",
    orphans == 0,
    f"Orphan rows: {orphans:,}"
)


# payments -> orders
df = query_df(
    conn,
    """
    SELECT COUNT(*) AS orphan_rows
    FROM order_payments op
    LEFT JOIN orders o
        ON op.order_id = o.order_id
    WHERE o.order_id IS NULL
    """
)

orphans = int(df.iloc[0]["orphan_rows"])

check(
    "order_payments -> orders",
    orphans == 0,
    f"Orphan rows: {orphans:,}"
)


# reviews -> orders
df = query_df(
    conn,
    """
    SELECT COUNT(*) AS orphan_rows
    FROM order_reviews r
    LEFT JOIN orders o
        ON r.order_id = o.order_id
    WHERE o.order_id IS NULL
    """
)

orphans = int(df.iloc[0]["orphan_rows"])

check(
    "order_reviews -> orders",
    orphans == 0,
    f"Orphan rows: {orphans:,}"
)


# fact_sales -> fact_orders
df = query_df(
    conn,
    """
    SELECT COUNT(*) AS orphan_rows
    FROM fact_sales fs
    LEFT JOIN fact_orders fo
        ON fs.order_id = fo.order_id
    WHERE fo.order_id IS NULL
    """
)

orphans = int(df.iloc[0]["orphan_rows"])

check(
    "fact_sales -> fact_orders",
    orphans == 0,
    f"Orphan rows: {orphans:,}"
)


# fact_orders -> dim_customer
df = query_df(
    conn,
    """
    SELECT COUNT(*) AS orphan_rows
    FROM fact_orders fo
    LEFT JOIN dim_customer dc
        ON fo.customer_id = dc.customer_id
    WHERE dc.customer_id IS NULL
    """
)

orphans = int(df.iloc[0]["orphan_rows"])

check(
    "fact_orders -> dim_customer",
    orphans == 0,
    f"Orphan rows: {orphans:,}"
)


# ============================================================
# 6. REVENUE RECONCILIATION
# ============================================================

print("\n" + "=" * 70)
print("6. REVENUE RECONCILIATION")
print("=" * 70)


df = query_df(
    conn,
    """
    SELECT
        ROUND(
            SUM(order_revenue),
            2
        ) AS revenue
    FROM fact_orders
    WHERE order_status = 'delivered'
    """
)

order_revenue = float(df.iloc[0]["revenue"])


df = query_df(
    conn,
    """
    SELECT
        ROUND(
            SUM(item_revenue),
            2
        ) AS revenue
    FROM fact_sales
    WHERE order_status = 'delivered'
    """
)

sales_revenue = float(df.iloc[0]["revenue"])


difference = round(
    order_revenue - sales_revenue,
    2
)


check(
    "Fact revenue reconciliation",
    abs(difference) < 0.01,
    (
        f"fact_orders: R$ {order_revenue:,.2f} | "
        f"fact_sales: R$ {sales_revenue:,.2f} | "
        f"Difference: R$ {difference:,.2f}"
    )
)


# ============================================================
# 7. ORDER-LEVEL REVENUE CONSISTENCY
# ============================================================

print("\n" + "=" * 70)
print("7. ORDER-LEVEL REVENUE CONSISTENCY")
print("=" * 70)


df = query_df(
    conn,
    """
    WITH sales_revenue AS (
        SELECT
            order_id,
            ROUND(
                SUM(item_revenue),
                2
            ) AS sales_revenue
        FROM fact_sales
        WHERE order_status = 'delivered'
        GROUP BY order_id
    )

    SELECT
        COUNT(*) AS mismatched_orders

    FROM fact_orders fo

    JOIN sales_revenue sr
        ON fo.order_id = sr.order_id

    WHERE fo.order_status = 'delivered'

      AND ABS(
          ROUND(
              fo.order_revenue - sr.sales_revenue,
              2
          )
      ) > 0.01
    """
)

mismatches = int(df.iloc[0]["mismatched_orders"])

check(
    "Order revenue matches sales grain",
    mismatches == 0,
    f"Mismatched delivered orders: {mismatches:,}"
)


# ============================================================
# 8. PAYMENT DUPLICATION CHECK
# ============================================================

print("\n" + "=" * 70)
print("8. PAYMENT DUPLICATION VALIDATION")
print("=" * 70)


df = query_df(
    conn,
    """
    SELECT
        ROUND(
            SUM(payment_total),
            2
        ) AS fact_payment_total
    FROM fact_orders
    WHERE order_status = 'delivered'
    """
)

fact_payment_total = float(
    df.iloc[0]["fact_payment_total"]
)


df = query_df(
    conn,
    """
    SELECT
        ROUND(
            SUM(payment_value),
            2
        ) AS source_payment_total

    FROM order_payments op

    JOIN orders o
        ON op.order_id = o.order_id

    WHERE o.order_status = 'delivered'
    """
)

source_payment_total = float(
    df.iloc[0]["source_payment_total"]
)


payment_difference = round(
    fact_payment_total - source_payment_total,
    2
)


check(
    "Payment totals not duplicated",
    abs(payment_difference) < 0.01,
    (
        f"fact_orders: R$ {fact_payment_total:,.2f} | "
        f"source payments: R$ {source_payment_total:,.2f} | "
        f"Difference: R$ {payment_difference:,.2f}"
    )
)


# ============================================================
# 9. CUSTOMER REPEAT RATE
# ============================================================

print("\n" + "=" * 70)
print("9. CUSTOMER ANALYTICS VALIDATION")
print("=" * 70)


df = query_df(
    conn,
    """
    WITH customer_orders AS (

        SELECT
            dc.customer_unique_id,
            COUNT(DISTINCT fo.order_id) AS order_count

        FROM fact_orders fo

        JOIN dim_customer dc
            ON fo.customer_id = dc.customer_id

        WHERE fo.order_status = 'delivered'

        GROUP BY dc.customer_unique_id
    )

    SELECT
        COUNT(*) AS total_customers,

        SUM(
            CASE
                WHEN order_count > 1
                THEN 1
                ELSE 0
            END
        ) AS repeat_customers,

        ROUND(
            SUM(
                CASE
                    WHEN order_count > 1
                    THEN 1
                    ELSE 0
                END
            ) * 100.0 / COUNT(*),
            2
        ) AS repeat_rate

    FROM customer_orders
    """
)

total_customers = int(df.iloc[0]["total_customers"])
repeat_customers = int(df.iloc[0]["repeat_customers"])
repeat_rate = float(df.iloc[0]["repeat_rate"])


check(
    "Customer population is valid",
    total_customers > 0,
    f"Customers: {total_customers:,}"
)

check(
    "Repeat customer calculation is valid",
    0 <= repeat_rate <= 100,
    (
        f"Repeat customers: {repeat_customers:,} | "
        f"Repeat rate: {repeat_rate:.2f}%"
    )
)


# ============================================================
# 10. DELIVERY METRICS
# ============================================================

print("\n" + "=" * 70)
print("10. DELIVERY ANALYTICS VALIDATION")
print("=" * 70)


df = query_df(
    conn,
    """
    SELECT
        COUNT(*) AS delivered_orders,

        ROUND(
            AVG(delivery_days),
            2
        ) AS avg_delivery_days,

        ROUND(
            AVG(delivery_delay_days),
            2
        ) AS avg_delay_days,

        SUM(
            CASE
                WHEN is_delayed = 1
                THEN 1
                ELSE 0
            END
        ) AS delayed_orders

    FROM fact_orders

    WHERE order_status = 'delivered'
    """
)

delivered_orders = int(df.iloc[0]["delivered_orders"])
avg_delivery_days = float(df.iloc[0]["avg_delivery_days"])
avg_delay_days = float(df.iloc[0]["avg_delay_days"])
delayed_orders = int(df.iloc[0]["delayed_orders"])


check(
    "Delivered order count",
    delivered_orders > 0,
    f"Delivered orders: {delivered_orders:,}"
)

check(
    "Average delivery days valid",
    avg_delivery_days >= 0,
    f"Average delivery: {avg_delivery_days:.2f} days"
)

check(
    "Delayed orders are within delivered orders",
    0 <= delayed_orders <= delivered_orders,
    f"Delayed: {delayed_orders:,}"
)


# ============================================================
# 11. QUARTER VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("11. QUARTERLY ANALYTICS VALIDATION")
print("=" * 70)


quarter_df = query_df(
    conn,
    """
    SELECT DISTINCT

        'Q' ||
        CAST(
            (
                CAST(
                    strftime(
                        '%m',
                        order_purchase_timestamp
                    ) AS INTEGER
                ) + 2
            ) / 3
            AS INTEGER
        ) AS quarter

    FROM fact_orders

    WHERE order_status = 'delivered'

    ORDER BY quarter
    """
)

quarters = set(
    quarter_df["quarter"].dropna().tolist()
)

invalid_quarters = [
    q for q in quarters
    if q not in {"Q1", "Q2", "Q3", "Q4"}
]

check(
    "No invalid quarter values",
    len(invalid_quarters) == 0,
    f"Detected quarters: {sorted(quarters)}"
)


# ============================================================
# 12. SQL FILE VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("12. ANALYTICAL SQL VALIDATION")
print("=" * 70)


if SQL_PATH.exists():

    sql_text = SQL_PATH.read_text(
        encoding="utf-8"
    )

    statements = [
        statement.strip()
        for statement in sql_text.split(";")
        if statement.strip()
    ]

    check(
        "18 analytical SQL queries found",
        len(statements) == 18,
        f"Queries found: {len(statements)}"
    )

    sql_errors = []

    for i, statement in enumerate(statements, start=1):

        try:

            cursor = conn.cursor()
            cursor.execute(statement)
            cursor.fetchall()

        except Exception as e:

            sql_errors.append(
                f"Query {i}: {e}"
            )

    check(
        "All analytical SQL queries execute",
        len(sql_errors) == 0,
        (
            "No SQL execution errors"
            if not sql_errors
            else " | ".join(sql_errors)
        )
    )


# ============================================================
# 13. BUSINESS METRIC SANITY CHECK
# ============================================================

print("\n" + "=" * 70)
print("13. BUSINESS METRIC SANITY CHECK")
print("=" * 70)


df = query_df(
    conn,
    """
    SELECT

        COUNT(*) AS delivered_orders,

        ROUND(
            SUM(order_revenue),
            2
        ) AS revenue,

        ROUND(
            AVG(order_revenue),
            2
        ) AS aov

    FROM fact_orders

    WHERE order_status = 'delivered'
    """
)

delivered = int(df.iloc[0]["delivered_orders"])
revenue = float(df.iloc[0]["revenue"])
aov = float(df.iloc[0]["aov"])


check(
    "Delivered orders > 0",
    delivered > 0,
    f"{delivered:,}"
)

check(
    "Revenue > 0",
    revenue > 0,
    f"R$ {revenue:,.2f}"
)

check(
    "AOV > 0",
    aov > 0,
    f"R$ {aov:,.2f}"
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n" + "=" * 70)
print("PHASE 6 VALIDATION SUMMARY")
print("=" * 70)

print(f"PASS : {passed}")
print(f"FAIL : {failed}")
print(f"TOTAL: {passed + failed}")

print("\n" + "-" * 70)

if failed == 0:

    print("STATUS: ALL PHASE 6 CHECKS PASSED")
    print("-" * 70)

    print("\nKey validated metrics:")
    print(f"Delivered Orders : {delivered:,}")
    print(f"Revenue          : R$ {revenue:,.2f}")
    print(f"Average Order    : R$ {aov:,.2f}")
    print(f"Repeat Customers : {repeat_customers:,}")
    print(f"Repeat Rate      : {repeat_rate:.2f}%")
    print(f"Avg Delivery     : {avg_delivery_days:.2f} days")
    print(f"Delayed Orders   : {delayed_orders:,}")
    print(f"Avg Delay        : {avg_delay_days:.2f} days")

else:

    print("STATUS: VALIDATION FAILED")
    print("Please fix the failed checks before moving to the next phase.")

print("=" * 70)


conn.close()

sys.exit(0 if failed == 0 else 1)