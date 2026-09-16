from pathlib import Path
import sqlite3
import pandas as pd


# ============================================================
# OLIST E-COMMERCE ANALYTICS
# Phase 6 - SQL Analytics Database Builder
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]

PROCESSED_DIR = BASE_DIR / "data" / "processed"
DATABASE_DIR = BASE_DIR / "database"
DB_PATH = DATABASE_DIR / "olist_analytics.db"


def load_csv(filename):
    """Load a processed Olist CSV file."""
    path = PROCESSED_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

    return pd.read_csv(path)


def prepare_orders(orders):
    """Prepare order-level analytical fields."""

    orders = orders.copy()

    # Convert timestamps
    date_columns = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]

    for col in date_columns:
        if col in orders.columns:
            orders[col] = pd.to_datetime(
                orders[col],
                errors="coerce"
            )

    # Delivery days
    orders["delivery_days"] = (
        orders["order_delivered_customer_date"]
        - orders["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400

    # Estimated delivery days
    orders["estimated_delivery_days"] = (
        orders["order_estimated_delivery_date"]
        - orders["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400

    # Delivery delay
    orders["delivery_delay_days"] = (
        orders["order_delivered_customer_date"]
        - orders["order_estimated_delivery_date"]
    ).dt.total_seconds() / 86400

    orders["is_delayed"] = (
        orders["delivery_delay_days"] > 0
    ).astype(int)

    # Date dimensions
    orders["order_year"] = (
        orders["order_purchase_timestamp"].dt.year
    )

    orders["order_year_month"] = (
        orders["order_purchase_timestamp"]
        .dt.to_period("M")
        .astype(str)
    )

    return orders


def prepare_reviews(reviews):
    """Keep one review record per order."""

    reviews = reviews.copy()

    if "review_creation_date" in reviews.columns:
        reviews["review_creation_date"] = pd.to_datetime(
            reviews["review_creation_date"],
            errors="coerce"
        )

    if "review_answer_timestamp" in reviews.columns:
        reviews["review_answer_timestamp"] = pd.to_datetime(
            reviews["review_answer_timestamp"],
            errors="coerce"
        )

    # Olist may contain multiple review IDs for an order.
    # Keep the latest review for order-level analysis.
    if "order_id" in reviews.columns:

        sort_column = (
            "review_answer_timestamp"
            if "review_answer_timestamp" in reviews.columns
            else None
        )

        if sort_column:
            reviews = reviews.sort_values(
                sort_column,
                ascending=False
            )

        reviews = reviews.drop_duplicates(
            subset=["order_id"],
            keep="first"
        )

    return reviews


def build_database():

    print("\n" + "=" * 60)
    print("OLIST SQL ANALYTICS DATABASE BUILDER")
    print("=" * 60)

    DATABASE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # Load processed datasets
    # --------------------------------------------------------

    print("\nLoading processed Olist datasets...")

    customers = load_csv("customers_clean.csv")
    orders = load_csv("orders_clean.csv")
    items = load_csv("order_items_clean.csv")
    payments = load_csv("order_payments_clean.csv")
    reviews = load_csv("order_reviews_clean.csv")
    products = load_csv("products_clean.csv")
    sellers = load_csv("sellers_clean.csv")
    geolocation = load_csv("geolocation_clean.csv")
    geolocation_zip = load_csv("geolocation_zip.csv")
    category_translation = load_csv(
        "category_translation_clean.csv"
    )

    print(f"Customers: {len(customers):,}")
    print(f"Orders: {len(orders):,}")
    print(f"Order items: {len(items):,}")
    print(f"Payments: {len(payments):,}")
    print(f"Reviews: {len(reviews):,}")
    print(f"Products: {len(products):,}")
    print(f"Sellers: {len(sellers):,}")

    # --------------------------------------------------------
    # Prepare analytical datasets
    # --------------------------------------------------------

    print("\nPreparing analytical tables...")

    orders = prepare_orders(orders)
    reviews = prepare_reviews(reviews)

    # --------------------------------------------------------
    # Payment aggregation
    # --------------------------------------------------------

    payment_agg = (
        payments
        .groupby("order_id", as_index=False)
        .agg(
            payment_total=(
                "payment_value",
                "sum"
            ),
            payment_rows=(
                "payment_value",
                "count"
            ),
            installment_max=(
                "payment_installments",
                "max"
            ),
        )
    )

    payment_methods = (
        payments
        .groupby("order_id")["payment_type"]
        .apply(
            lambda x: ", ".join(
                sorted(
                    set(x.dropna().astype(str))
                )
            )
        )
        .reset_index(
            name="payment_methods"
        )
    )

    primary_payment = (
        payments
        .groupby(
            ["order_id", "payment_type"],
            as_index=False
        )["payment_value"]
        .sum()
        .sort_values(
            ["order_id", "payment_value"],
            ascending=[True, False]
        )
        .drop_duplicates(
            "order_id"
        )
        [["order_id", "payment_type"]]
        .rename(
            columns={
                "payment_type":
                "primary_payment_type"
            }
        )
    )

    payment_agg = (
        payment_agg
        .merge(
            payment_methods,
            on="order_id",
            how="left"
        )
        .merge(
            primary_payment,
            on="order_id",
            how="left"
        )
    )

    # --------------------------------------------------------
    # Item aggregation at order level
    # --------------------------------------------------------

    item_order_agg = (
        items
        .groupby("order_id", as_index=False)
        .agg(
            item_count=(
                "order_item_id",
                "count"
            ),
            product_revenue=(
                "price",
                "sum"
            ),
            freight_revenue=(
                "freight_value",
                "sum"
            ),
        )
    )

    item_order_agg["order_revenue"] = (
        item_order_agg["product_revenue"]
        + item_order_agg["freight_revenue"]
    )

    # --------------------------------------------------------
    # Fact Orders
    # One row = one order
    # --------------------------------------------------------

    fact_orders = (
        orders
        .merge(
            item_order_agg,
            on="order_id",
            how="left"
        )
        .merge(
            payment_agg,
            on="order_id",
            how="left"
        )
        .merge(
            reviews[
                [
                    "order_id",
                    "review_score"
                ]
            ],
            on="order_id",
            how="left"
        )
    )

    numeric_fill = [
        "item_count",
        "product_revenue",
        "freight_revenue",
        "order_revenue",
        "payment_total",
        "payment_rows",
        "installment_max",
    ]

    for col in numeric_fill:
        if col in fact_orders.columns:
            fact_orders[col] = (
                fact_orders[col]
                .fillna(0)
            )

    # --------------------------------------------------------
    # Fact Sales
    # One row = one order item
    #
    # IMPORTANT:
    # Payment totals are NOT copied here.
    # This prevents payment duplication when multiple
    # order items exist for the same order.
    # --------------------------------------------------------

    fact_sales = (
        items
        .merge(
            orders[
                [
                    "order_id",
                    "customer_id",
                    "order_status",
                    "order_purchase_timestamp",
                    "order_delivered_customer_date",
                    "order_estimated_delivery_date",
                    "delivery_days",
                    "estimated_delivery_days",
                    "delivery_delay_days",
                    "is_delayed",
                    "order_year",
                    "order_year_month",
                ]
            ],
            on="order_id",
            how="left"
        )
        .copy()
    )

    fact_sales["item_revenue"] = (
        fact_sales["price"]
        + fact_sales["freight_value"]
    )

    # --------------------------------------------------------
    # Dimension: Customer
    # --------------------------------------------------------

    dim_customer = customers.copy()

    customer_orders = (
        orders
        .groupby(
            "customer_id",
            as_index=False
        )
        .agg(
            order_count=(
                "order_id",
                "nunique"
            ),
            first_order_date=(
                "order_purchase_timestamp",
                "min"
            ),
            last_order_date=(
                "order_purchase_timestamp",
                "max"
            ),
        )
    )

    dim_customer = (
        dim_customer
        .merge(
            customer_orders,
            on="customer_id",
            how="left"
        )
    )

    # --------------------------------------------------------
    # Dimension: Product
    # --------------------------------------------------------

    dim_product = products.copy()

    if (
        "product_category_name"
        in dim_product.columns
        and "product_category_name"
        in category_translation.columns
    ):

        dim_product = dim_product.merge(
            category_translation,
            on="product_category_name",
            how="left"
        )

    # --------------------------------------------------------
    # Dimension: Seller
    # --------------------------------------------------------

    dim_seller = sellers.copy()

    seller_metrics = (
        items
        .groupby(
            "seller_id",
            as_index=False
        )
        .agg(
            item_count=(
                "order_item_id",
                "count"
            ),
            product_revenue=(
                "price",
                "sum"
            ),
            freight_revenue=(
                "freight_value",
                "sum"
            ),
            order_count=(
                "order_id",
                "nunique"
            ),
        )
    )

    seller_metrics["gross_sales"] = (
        seller_metrics["product_revenue"]
        + seller_metrics["freight_revenue"]
    )

    dim_seller = (
        dim_seller
        .merge(
            seller_metrics,
            on="seller_id",
            how="left"
        )
    )

    # --------------------------------------------------------
    # Dimension: Date
    # --------------------------------------------------------

    date_values = (
        orders[
            [
                "order_purchase_timestamp"
            ]
        ]
        .dropna()
        .copy()
    )

    date_values["date"] = (
        date_values[
            "order_purchase_timestamp"
        ].dt.date
    )

    date_values = (
        date_values[
            ["date"]
        ]
        .drop_duplicates()
        .sort_values("date")
    )

    dim_date = date_values.copy()

    dim_date["date"] = pd.to_datetime(
        dim_date["date"]
    )

    dim_date["year"] = (
        dim_date["date"].dt.year
    )

    dim_date["month"] = (
        dim_date["date"].dt.month
    )

    dim_date["month_name"] = (
        dim_date["date"].dt.month_name()
    )

    dim_date["quarter"] = (
        "Q"
        + dim_date["date"]
        .dt.quarter
        .astype(str)
    )

    dim_date["year_month"] = (
        dim_date["date"]
        .dt.to_period("M")
        .astype(str)
    )

    # --------------------------------------------------------
    # Dimension: Geography
    # --------------------------------------------------------

    geo_customer = (
        customers[
            [
                "customer_zip_code_prefix",
                "customer_city",
                "customer_state",
            ]
        ]
        .drop_duplicates()
        .rename(
            columns={
                "customer_zip_code_prefix":
                    "zip_code_prefix",
                "customer_city":
                    "city",
                "customer_state":
                    "state",
            }
        )
    )

    geo_seller = (
        sellers[
            [
                "seller_zip_code_prefix",
                "seller_city",
                "seller_state",
            ]
        ]
        .drop_duplicates()
        .rename(
            columns={
                "seller_zip_code_prefix":
                    "zip_code_prefix",
                "seller_city":
                    "city",
                "seller_state":
                    "state",
            }
        )
    )

    dim_geography = pd.concat(
        [
            geo_customer,
            geo_seller,
        ],
        ignore_index=True
    ).drop_duplicates()

    # --------------------------------------------------------
    # Database connection
    # --------------------------------------------------------

    if DB_PATH.exists():
        print("\nExisting database found.")
        print("Replacing it with a fresh build...")
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)

    # --------------------------------------------------------
    # Write source / clean tables
    # --------------------------------------------------------

    print("\nWriting clean source tables...")

    source_tables = {
        "customers": customers,
        "orders": orders,
        "order_items": items,
        "order_payments": payments,
        "order_reviews": reviews,
        "products": products,
        "sellers": sellers,
        "geolocation": geolocation,
        "geolocation_zip": geolocation_zip,
        "category_translation": category_translation,
    }

    for table_name, dataframe in source_tables.items():

        dataframe.to_sql(
            table_name,
            conn,
            if_exists="replace",
            index=False
        )

        print(
            f"  {table_name:<22} "
            f"{len(dataframe):>10,} rows"
        )

    # --------------------------------------------------------
    # Write dimensions
    # --------------------------------------------------------

    print("\nWriting dimension tables...")

    dimension_tables = {
        "dim_customer": dim_customer,
        "dim_product": dim_product,
        "dim_seller": dim_seller,
        "dim_date": dim_date,
        "dim_geography": dim_geography,
    }

    for table_name, dataframe in dimension_tables.items():

        dataframe.to_sql(
            table_name,
            conn,
            if_exists="replace",
            index=False
        )

        print(
            f"  {table_name:<22} "
            f"{len(dataframe):>10,} rows"
        )

    # --------------------------------------------------------
    # Write facts
    # --------------------------------------------------------

    print("\nWriting fact tables...")

    fact_tables = {
        "fact_orders": fact_orders,
        "fact_sales": fact_sales,
    }

    for table_name, dataframe in fact_tables.items():

        dataframe.to_sql(
            table_name,
            conn,
            if_exists="replace",
            index=False
        )

        print(
            f"  {table_name:<22} "
            f"{len(dataframe):>10,} rows"
        )

    # --------------------------------------------------------
    # Create useful indexes
    # --------------------------------------------------------

    print("\nCreating analytical indexes...")

    indexes = [

        """
        CREATE INDEX IF NOT EXISTS
        idx_orders_customer
        ON orders(customer_id)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_orders_purchase_date
        ON orders(order_purchase_timestamp)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_items_order
        ON order_items(order_id)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_items_product
        ON order_items(product_id)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_items_seller
        ON order_items(seller_id)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_fact_orders_customer
        ON fact_orders(customer_id)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_fact_orders_month
        ON fact_orders(order_year_month)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_fact_sales_order
        ON fact_sales(order_id)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_fact_sales_product
        ON fact_sales(product_id)
        """,

        """
        CREATE INDEX IF NOT EXISTS
        idx_fact_sales_seller
        ON fact_sales(seller_id)
        """,
    ]

    for index_sql in indexes:
        conn.execute(index_sql)

    conn.commit()

    # --------------------------------------------------------
    # Final database information
    # --------------------------------------------------------

    table_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM sqlite_master
        WHERE type = 'table'
        """
    ).fetchone()[0]

    conn.close()

    db_size_mb = (
        DB_PATH.stat().st_size
        / (1024 * 1024)
    )

    print("\n" + "=" * 60)
    print("DATABASE BUILD COMPLETED")
    print("=" * 60)

    print(f"Database: {DB_PATH}")
    print(f"Tables created: {table_count}")
    print(f"Database size: {db_size_mb:.2f} MB")

    print("\nSource tables:")
    for table in source_tables:
        print(f"  ✓ {table}")

    print("\nDimension tables:")
    for table in dimension_tables:
        print(f"  ✓ {table}")

    print("\nFact tables:")
    for table in fact_tables:
        print(f"  ✓ {table}")

    print("\nSQL analytics database is ready.")


if __name__ == "__main__":
    build_database()