"""
data_cleaning.py
================
Full reproducible cleaning pipeline for the Olist E-Commerce dataset.

Reads from : data/raw/
Writes to  : data/processed/

Run:
    python src/data_cleaning.py

Produces:
    data/processed/customers_clean.csv
    data/processed/orders_clean.csv
    data/processed/order_items_clean.csv
    data/processed/order_payments_clean.csv
    data/processed/order_reviews_clean.csv
    data/processed/products_clean.csv
    data/processed/sellers_clean.csv
    data/processed/geolocation_clean.csv
    data/processed/category_translation_clean.csv
    data/processed/orders_enriched.csv
    data/processed/order_items_enriched.csv
    data/processed/customer_analytics.csv
    data/processed/product_analytics.csv
    data/processed/seller_analytics.csv
"""

import os
import sys
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(ROOT, "data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

sys.path.insert(0, ROOT)
from src.data_loader import load_all_tables

# ---------------------------------------------------------------------------
# Cleaning log — every action is recorded here
# ---------------------------------------------------------------------------
CLEANING_LOG: list[dict] = []


def log(table: str, issue: str, rows_affected: int, action: str, reason: str):
    CLEANING_LOG.append(
        {
            "table": table,
            "issue": issue,
            "rows_affected": rows_affected,
            "action": action,
            "reason": reason,
        }
    )
    print(f"  [LOG] {table}: {issue} -> {action} ({rows_affected:,} rows)")


# ===========================================================================
# INDIVIDUAL TABLE CLEANING FUNCTIONS
# ===========================================================================

# ---------------------------------------------------------------------------
# 1. customers
# ---------------------------------------------------------------------------
def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    # No nulls, no duplicates in this table — verified in audit
    # Standardize city names: lowercase strip
    df["customer_city"] = df["customer_city"].str.strip().str.lower()
    df["customer_state"] = df["customer_state"].str.strip().str.upper()

    log("customers", "City/state whitespace & case normalisation", before,
        "str.strip().str.lower() on city; str.upper() on state",
        "Ensures consistent join/groupby behaviour on city and state")

    assert df["customer_id"].nunique() == len(df), "customer_id PK violated"
    return df


# ---------------------------------------------------------------------------
# 2. geolocation
# ---------------------------------------------------------------------------
BRAZIL_LAT_MIN, BRAZIL_LAT_MAX = -35.0, 5.5
BRAZIL_LNG_MIN, BRAZIL_LNG_MAX = -74.0, -28.0


def clean_geolocation(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    # DQ-01: Remove fully duplicate rows
    dup_mask = df.duplicated(keep="first")
    n_dups = dup_mask.sum()
    df = df[~dup_mask].copy()
    log("geolocation", "DQ-01: Fully duplicate rows", n_dups,
        "Removed — kept first occurrence per duplicate group",
        "Duplicates cause row multiplication in joins; no information lost")

    # DQ-02: Remove coordinate outliers outside Brazil bounding box
    outlier_mask = (
        (df["geolocation_lat"] < BRAZIL_LAT_MIN) |
        (df["geolocation_lat"] > BRAZIL_LAT_MAX) |
        (df["geolocation_lng"] < BRAZIL_LNG_MIN) |
        (df["geolocation_lng"] > BRAZIL_LNG_MAX)
    )
    n_outliers = outlier_mask.sum()
    df = df[~outlier_mask].copy()
    log("geolocation", "DQ-02: Coordinate outliers outside Brazil", n_outliers,
        f"Removed — bounding box lat [{BRAZIL_LAT_MIN},{BRAZIL_LAT_MAX}], "
        f"lng [{BRAZIL_LNG_MIN},{BRAZIL_LNG_MAX}]",
        "Out-of-bounds coordinates would cause wrong map pin placement")

    # Normalise city/state
    df["geolocation_city"] = df["geolocation_city"].str.strip().str.lower()
    df["geolocation_state"] = df["geolocation_state"].str.strip().str.upper()

    # For analytics: create a deduplicated zip-level table (mean lat/lng per ZIP)
    # This is the version used for joins; full table also saved
    after = len(df)
    log("geolocation", "Post-dedup total", before - after,
        f"Rows after cleaning: {after:,} (from {before:,})", "")

    return df


def make_geolocation_zip(df_clean: pd.DataFrame) -> pd.DataFrame:
    """One row per ZIP prefix with mean lat/lng — safe for joins."""
    geo_zip = (
        df_clean
        .groupby("geolocation_zip_code_prefix", as_index=False)
        .agg(
            geolocation_lat=("geolocation_lat", "mean"),
            geolocation_lng=("geolocation_lng", "mean"),
            geolocation_city=("geolocation_city", "first"),
            geolocation_state=("geolocation_state", "first"),
        )
    )
    log("geolocation_zip", "Aggregate to 1 row per ZIP prefix",
        len(df_clean) - len(geo_zip),
        "group-by zip_code_prefix, mean lat/lng, first city/state",
        "Prevents row-multiplication when joining to customers/sellers")
    return geo_zip


# ---------------------------------------------------------------------------
# 3. orders
# ---------------------------------------------------------------------------
def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    # DQ-05: 160 nulls in order_approved_at — keep rows, nulls are valid
    # (not yet approved / canceled before approval)
    log("orders", "DQ-05: Missing order_approved_at (160 rows)", 160,
        "Retained as NULL — not imputed",
        "Represents real business state (payment not captured)")

    # DQ-06: 1,783 nulls in order_delivered_carrier_date — keep, valid
    log("orders", "DQ-06: Missing order_delivered_carrier_date (1,783 rows)", 1783,
        "Retained as NULL — not imputed",
        "Represents orders not yet handed to carrier")

    # DQ-07: 2,965 nulls in order_delivered_customer_date — keep, valid
    log("orders", "DQ-07: Missing order_delivered_customer_date (2,965 rows)", 2965,
        "Retained as NULL — not imputed",
        "Represents orders not yet delivered; delivery metrics filter to non-null")

    # Validate order_status known values
    known_statuses = {
        "delivered", "shipped", "canceled", "unavailable",
        "invoiced", "processing", "created", "approved"
    }
    invalid_status = df[~df["order_status"].isin(known_statuses)]
    if len(invalid_status) > 0:
        log("orders", "Unknown order_status values", len(invalid_status),
            "Flagged — investigate", "Unexpected categorical values")

    # No full-row duplicates verified in audit
    assert df["order_id"].nunique() == len(df), "order_id PK violated"
    assert df["customer_id"].nunique() == len(df), \
        "customer_id not unique in orders (each customer_id maps to exactly one order)"

    return df


# ---------------------------------------------------------------------------
# 4. order_items
# ---------------------------------------------------------------------------
def clean_order_items(df: pd.DataFrame) -> pd.DataFrame:

    # Rename typo columns from products (join will bring them in later)
    # No typos in order_items itself

    # No nulls, no full-row duplicates (audit verified)
    # Validate price > 0
    invalid_price = df[df["price"] <= 0]
    log("order_items", "Items with price <= 0", len(invalid_price),
        "None found — validated" if len(invalid_price) == 0 else "Flagged",
        "Price of zero/negative is not a valid sale")

    invalid_freight = df[df["freight_value"] < 0]
    log("order_items", "Items with freight_value < 0", len(invalid_freight),
        "None found — validated" if len(invalid_freight) == 0 else "Flagged",
        "Negative freight cost is not valid")

    return df


# ---------------------------------------------------------------------------
# 5. order_payments
# ---------------------------------------------------------------------------
def clean_order_payments(df: pd.DataFrame) -> pd.DataFrame:

    # DQ-13: payment_type = 'not_defined' (3 rows) — relabel
    nd_mask = df["payment_type"] == "not_defined"
    n_nd = nd_mask.sum()
    df.loc[nd_mask, "payment_type"] = "unknown"
    log("order_payments", "DQ-13: payment_type='not_defined'", n_nd,
        "Relabelled to 'unknown'",
        "Avoids misleading 'not_defined' label in charts; value is unknown not missing")

    # DQ-14: payment_value == 0 (9 rows) — retain, flag
    zero_pay = df[df["payment_value"] == 0]
    log("order_payments", "DQ-14: Zero payment_value rows", len(zero_pay),
        "Retained — flagged with is_zero_payment column",
        "May represent fully-discounted voucher rows; kept for completeness")
    df["is_zero_payment"] = df["payment_value"] == 0

    # DQ-15: payment_installments == 0 on credit_card (2 rows) — impute to 1
    cc_zero_inst = (df["payment_type"] == "credit_card") & (df["payment_installments"] == 0)
    n_cc_zero = cc_zero_inst.sum()
    df.loc[cc_zero_inst, "payment_installments"] = 1
    log("order_payments", "DQ-15: Credit card with 0 installments", n_cc_zero,
        "Imputed payment_installments to 1",
        "Credit card with 0 installments is technically impossible; 1 installment is correct")

    return df


# ---------------------------------------------------------------------------
# 6. order_reviews
# ---------------------------------------------------------------------------
def clean_order_reviews(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    # DQ-03 + DQ-04: Duplicate review_id AND multiple reviews per order
    # Strategy: keep the most-recent review per order_id
    # (latest review_answer_timestamp = customer's final stated opinion)
    df_sorted = df.sort_values("review_answer_timestamp", ascending=False)
    df_dedup = df_sorted.drop_duplicates(subset=["order_id"], keep="first").copy()
    n_removed = before - len(df_dedup)
    log("order_reviews", "DQ-03/04: Duplicate review_id / multiple reviews per order",
        n_removed,
        "Kept most-recent review per order_id (by review_answer_timestamp)",
        "Most recent review = customer's final stated opinion; earlier re-submissions discarded")

    # Fill missing comment fields with empty string for NLP readiness
    df_dedup["review_comment_title"] = df_dedup["review_comment_title"].fillna("")
    df_dedup["review_comment_message"] = df_dedup["review_comment_message"].fillna("")
    log("order_reviews", "NULL review_comment_title/message", 87656 + 58247,
        "Filled with empty string ''",
        "Empty string is analytically neutral; avoids pandas NA issues in text ops")

    # Flag reviews that have a written message
    df_dedup["has_comment"] = df_dedup["review_comment_message"].str.len() > 0

    assert df_dedup["order_id"].nunique() == len(df_dedup), \
        "order_id not unique after dedup — investigate"
    return df_dedup


# ---------------------------------------------------------------------------
# 7. products
# ---------------------------------------------------------------------------
def clean_products(df: pd.DataFrame) -> pd.DataFrame:

    # Rename typo column names (only in the processed copy)
    df = df.rename(columns={
        "product_name_lenght": "product_name_length",
        "product_description_lenght": "product_description_length",
    })
    log("products", "DQ-11: Column name typos renamed", 2,
        "product_name_lenght → product_name_length; product_description_lenght → product_description_length",
        "Corrects source typo in processed dataset; raw file untouched")

    # DQ-08: 610 products missing all descriptive fields
    # Fill product_category_name with "unknown" for groupby safety
    missing_cat = df["product_category_name"].isna()
    n_missing_cat = missing_cat.sum()
    df["product_category_name"] = df["product_category_name"].fillna("unknown")
    log("products", "DQ-08: Missing product_category_name", n_missing_cat,
        "Filled with 'unknown'",
        "Products without category still generated real revenue; label explicitly unknown")

    # DQ-09/10: 2 rows missing dimension fields, 4 with weight=0
    # Weight = 0 → set to NaN (impossible for shipped physical goods)
    zero_weight = df["product_weight_g"] == 0
    n_zero = zero_weight.sum()
    df.loc[zero_weight, "product_weight_g"] = np.nan
    log("products", "DQ-10: Zero product_weight_g", n_zero,
        "Set to NaN (treated as missing)",
        "Weight of 0g is physically impossible for a shipped item")

    assert df["product_id"].nunique() == len(df), "product_id PK violated"
    return df


# ---------------------------------------------------------------------------
# 8. sellers
# ---------------------------------------------------------------------------
def clean_sellers(df: pd.DataFrame) -> pd.DataFrame:
    df["seller_city"] = df["seller_city"].str.strip().str.lower()
    df["seller_state"] = df["seller_state"].str.strip().str.upper()
    log("sellers", "City/state normalisation", len(df),
        "str.strip().str.lower() on city; str.upper() on state",
        "Consistency with customer/geolocation tables")
    assert df["seller_id"].nunique() == len(df), "seller_id PK violated"
    return df


# ---------------------------------------------------------------------------
# 9. category_translation
# ---------------------------------------------------------------------------
def clean_category_translation(df: pd.DataFrame) -> pd.DataFrame:
    # DQ-12: Add 2 missing categories
    missing = pd.DataFrame([
        {"product_category_name": "pc_gamer",
         "product_category_name_english": "PC Gamer"},
        {"product_category_name": "portateis_cozinha_e_preparadores_de_alimentos",
         "product_category_name_english": "Portable Kitchen & Food Preparers"},
        {"product_category_name": "unknown",
         "product_category_name_english": "Unknown / Uncategorized"},
    ])
    df = pd.concat([df, missing], ignore_index=True)
    log("category_translation", "DQ-12: Added 2 missing category translations + unknown label", 3,
        "Appended pc_gamer, portateis_cozinha_e_preparadores_de_alimentos, unknown",
        "Prevents NULL in English category name column after joins")
    return df


# ===========================================================================
# ANALYTICS-READY ENRICHED DATASETS
# ===========================================================================

def build_orders_enriched(
    orders: pd.DataFrame,
    customers: pd.DataFrame,
    order_payments: pd.DataFrame,
    order_items: pd.DataFrame,
) -> pd.DataFrame:
    """
    orders_enriched.csv
    Grain: one row per ORDER (order_id)
    Contains: order metadata + customer state + total payment value + item/revenue summary
    """

    # --- Payment summary per order (SUM payment_value, list of payment types) ---
    pay_agg = (
        order_payments
        .groupby("order_id", as_index=False)
        .agg(
            total_payment_value=("payment_value", "sum"),
            payment_methods=("payment_type", lambda x: "|".join(sorted(x.unique()))),
            max_installments=("payment_installments", "max"),
            n_payment_rows=("payment_sequential", "count"),
        )
    )

    # --- Item summary per order (SUM price, SUM freight, COUNT items) ---
    items_agg = (
        order_items
        .groupby("order_id", as_index=False)
        .agg(
            item_count=("order_item_id", "count"),
            product_revenue=("price", "sum"),
            freight_revenue=("freight_value", "sum"),
        )
    )
    items_agg["total_order_revenue"] = (
        items_agg["product_revenue"] + items_agg["freight_revenue"]
    )

    # --- Base join ---
    df = orders.merge(customers[["customer_id", "customer_unique_id",
                                  "customer_state", "customer_city",
                                  "customer_zip_code_prefix"]],
                      on="customer_id", how="left")

    df = df.merge(pay_agg, on="order_id", how="left")
    df = df.merge(items_agg, on="order_id", how="left")

    # --- Derived date columns ---
    df["order_year"]       = df["order_purchase_timestamp"].dt.year
    df["order_month"]      = df["order_purchase_timestamp"].dt.month
    df["order_year_month"] = df["order_purchase_timestamp"].dt.to_period("M").astype(str)
    df["order_quarter"]    = df["order_purchase_timestamp"].dt.to_period("Q").astype(str)
    df["order_day_of_week"] = df["order_purchase_timestamp"].dt.day_name()
    df["order_week"]       = df["order_purchase_timestamp"].dt.isocalendar().week.astype("Int64")

    # --- Delivery metrics (only valid for delivered orders) ---
    delivered_mask = (
        df["order_delivered_customer_date"].notna() &
        df["order_purchase_timestamp"].notna()
    )
    df["delivery_days"] = np.where(
        delivered_mask,
        (df["order_delivered_customer_date"] - df["order_purchase_timestamp"])
        .dt.total_seconds() / 86400,
        np.nan,
    )

    estimated_mask = (
        df["order_estimated_delivery_date"].notna() &
        df["order_purchase_timestamp"].notna()
    )
    df["estimated_delivery_days"] = np.where(
        estimated_mask,
        (df["order_estimated_delivery_date"] - df["order_purchase_timestamp"])
        .dt.total_seconds() / 86400,
        np.nan,
    )

    delay_mask = (
        df["order_delivered_customer_date"].notna() &
        df["order_estimated_delivery_date"].notna()
    )
    df["delivery_delay_days"] = np.where(
        delay_mask,
        (df["order_delivered_customer_date"] - df["order_estimated_delivery_date"])
        .dt.total_seconds() / 86400,
        np.nan,
    )
    # Positive = late, negative = early
    df["is_delayed"] = np.where(
        delay_mask,
        df["delivery_delay_days"] > 0,
        np.nan,
    )

    # Approval time
    approval_mask = (
        df["order_approved_at"].notna() &
        df["order_purchase_timestamp"].notna()
    )
    df["approval_hours"] = np.where(
        approval_mask,
        (df["order_approved_at"] - df["order_purchase_timestamp"])
        .dt.total_seconds() / 3600,
        np.nan,
    )

    log("orders_enriched",
        "Built orders_enriched: orders + customers + payment summary + item summary + derived date/delivery fields",
        len(df), "LEFT JOIN + aggregation (grain = 1 row per order_id)",
        "Central analytics table for order-level metrics")

    return df


def build_order_items_enriched(
    order_items: pd.DataFrame,
    orders: pd.DataFrame,
    products: pd.DataFrame,
    sellers: pd.DataFrame,
    category_translation: pd.DataFrame,
) -> pd.DataFrame:
    """
    order_items_enriched.csv
    Grain: one row per ORDER ITEM (order_id + order_item_id)
    Contains: item info + order status + product category (English) + seller state
    """
    df = order_items.merge(
        orders[["order_id", "order_status", "order_purchase_timestamp",
                "order_delivered_customer_date", "order_estimated_delivery_date",
                "customer_id"]],
        on="order_id", how="left"
    )

    df = df.merge(
        products[["product_id", "product_category_name",
                  "product_weight_g", "product_length_cm",
                  "product_height_cm", "product_width_cm"]],
        on="product_id", how="left"
    )

    df = df.merge(
        category_translation,
        on="product_category_name", how="left"
    )

    df = df.merge(
        sellers[["seller_id", "seller_state", "seller_city"]],
        on="seller_id", how="left"
    )

    # Derived
    df["item_revenue"] = df["price"] + df["freight_value"]
    df["order_year_month"] = pd.to_datetime(
        df["order_purchase_timestamp"], errors="coerce"
    ).dt.to_period("M").astype(str)

    log("order_items_enriched",
        "Built order_items_enriched: items + order status + product category + seller state",
        len(df), "LEFT JOIN (grain = 1 row per order item)",
        "Line-item level analytics — revenue by category/seller/month")

    return df


def build_customer_analytics(
    customers: pd.DataFrame,
    orders: pd.DataFrame,
    order_items: pd.DataFrame,
    order_reviews: pd.DataFrame,
    order_payments: pd.DataFrame,
) -> pd.DataFrame:
    """
    customer_analytics.csv
    Grain: one row per UNIQUE CUSTOMER (customer_unique_id)
    Contains: total orders, total spend, avg review score, first/last order date
    """
    # Map customer_unique_id onto orders via customers table
    orders_cust = orders.merge(
        customers[["customer_id", "customer_unique_id",
                   "customer_state", "customer_city"]],
        on="customer_id", how="left"
    )

    # Payment per order (sum across payment rows)
    pay_per_order = (
        order_payments.groupby("order_id", as_index=False)["payment_value"].sum()
        .rename(columns={"payment_value": "order_payment_value"})
    )
    orders_cust = orders_cust.merge(pay_per_order, on="order_id", how="left")

    # Item count per order
    items_per_order = (
        order_items.groupby("order_id", as_index=False)
        .agg(items_count=("order_item_id", "count"),
             order_product_revenue=("price", "sum"),
             order_freight=("freight_value", "sum"))
    )
    orders_cust = orders_cust.merge(items_per_order, on="order_id", how="left")

    # Review per order
    rev_per_order = order_reviews[["order_id", "review_score"]].drop_duplicates("order_id")
    orders_cust = orders_cust.merge(rev_per_order, on="order_id", how="left")

    # Aggregate to unique customer level
    agg = (
        orders_cust
        .groupby("customer_unique_id", as_index=False)
        .agg(
            customer_state=("customer_state", "first"),
            customer_city=("customer_city", "first"),
            total_orders=("order_id", "count"),
            delivered_orders=("order_status", lambda x: (x == "delivered").sum()),
            first_order_date=("order_purchase_timestamp", "min"),
            last_order_date=("order_purchase_timestamp", "max"),
            total_spend_payment=("order_payment_value", "sum"),
            total_items_bought=("items_count", "sum"),
            avg_review_score=("review_score", "mean"),
        )
    )

    agg["is_repeat_buyer"] = agg["total_orders"] >= 2
    agg["avg_order_value"] = agg["total_spend_payment"] / agg["total_orders"]

    log("customer_analytics",
        "Built customer_analytics: aggregated to 1 row per unique customer",
        len(agg), "GROUP BY customer_unique_id",
        "Customer-level KPIs: CLV, repeat rate, AOV")

    return agg


def build_product_analytics(
    products: pd.DataFrame,
    order_items: pd.DataFrame,
    order_reviews: pd.DataFrame,
    orders: pd.DataFrame,
    category_translation: pd.DataFrame,
) -> pd.DataFrame:
    """
    product_analytics.csv
    Grain: one row per PRODUCT (product_id)
    Contains: category, total units sold, total revenue, avg review score
    """
    # Only use delivered orders for revenue
    delivered_order_ids = orders.loc[
        orders["order_status"] == "delivered", "order_id"
    ]
    items_delivered = order_items[order_items["order_id"].isin(delivered_order_ids)]

    rev_per_order = (
        order_reviews
        .drop_duplicates("order_id")[["order_id", "review_score"]]
    )
    items_with_review = items_delivered.merge(
        rev_per_order, on="order_id", how="left"
    )

    agg = (
        items_with_review
        .groupby("product_id", as_index=False)
        .agg(
            units_sold=("order_item_id", "count"),
            total_product_revenue=("price", "sum"),
            total_freight_revenue=("freight_value", "sum"),
            avg_unit_price=("price", "mean"),
            avg_freight=("freight_value", "mean"),
            avg_review_score=("review_score", "mean"),
            n_unique_orders=("order_id", "nunique"),
        )
    )
    agg["total_revenue"] = agg["total_product_revenue"] + agg["total_freight_revenue"]

    # Add category info
    agg = agg.merge(
        products[["product_id", "product_category_name",
                  "product_weight_g", "product_length_cm",
                  "product_height_cm", "product_width_cm"]],
        on="product_id", how="left"
    )
    agg = agg.merge(category_translation, on="product_category_name", how="left")

    log("product_analytics",
        "Built product_analytics: aggregated to 1 row per product (delivered orders only)",
        len(agg), "GROUP BY product_id",
        "Product-level KPIs: revenue, units sold, avg price, avg review")

    return agg


def build_seller_analytics(
    sellers: pd.DataFrame,
    order_items: pd.DataFrame,
    orders: pd.DataFrame,
    order_reviews: pd.DataFrame,
    products: pd.DataFrame,
    category_translation: pd.DataFrame,
) -> pd.DataFrame:
    """
    seller_analytics.csv
    Grain: one row per SELLER (seller_id)
    Contains: total orders, revenue, avg review score, states served
    """
    delivered_order_ids = orders.loc[
        orders["order_status"] == "delivered", "order_id"
    ]
    items_delivered = order_items[order_items["order_id"].isin(delivered_order_ids)]

    items_with_review = items_delivered.merge(
        order_reviews.drop_duplicates("order_id")[["order_id", "review_score"]],
        on="order_id", how="left"
    )

    items_with_cat = items_with_review.merge(
        products[["product_id", "product_category_name"]],
        on="product_id", how="left"
    ).merge(category_translation, on="product_category_name", how="left")

    agg = (
        items_with_cat
        .groupby("seller_id", as_index=False)
        .agg(
            total_items_sold=("order_item_id", "count"),
            total_product_revenue=("price", "sum"),
            total_freight_revenue=("freight_value", "sum"),
            avg_item_price=("price", "mean"),
            avg_freight_value=("freight_value", "mean"),
            avg_review_score=("review_score", "mean"),
            n_unique_orders=("order_id", "nunique"),
            n_unique_products=("product_id", "nunique"),
            top_category=("product_category_name_english",
                          lambda x: x.mode()[0] if len(x.mode()) > 0 else "unknown"),
        )
    )
    agg["total_revenue"] = agg["total_product_revenue"] + agg["total_freight_revenue"]

    agg = agg.merge(
        sellers[["seller_id", "seller_state", "seller_city"]],
        on="seller_id", how="left"
    )

    log("seller_analytics",
        "Built seller_analytics: aggregated to 1 row per seller (delivered orders only)",
        len(agg), "GROUP BY seller_id",
        "Seller-level KPIs: revenue, units sold, avg review, top category")

    return agg


# ===========================================================================
# VALIDATION
# ===========================================================================

def run_validation(tables: dict[str, pd.DataFrame]) -> list[dict]:
    """Post-cleaning validation checks. Returns list of result dicts."""
    results = []

    def check(name: str, passed: bool, detail: str):
        status = "PASS" if passed else "FAIL"
        results.append({"check": name, "status": status, "detail": detail})
        print(f"  [{status}] {name}: {detail}")

    customers        = tables["customers"]
    orders           = tables["orders"]
    order_items      = tables["order_items"]
    order_payments   = tables["order_payments"]
    order_reviews    = tables["order_reviews"]
    products         = tables["products"]
    sellers          = tables["sellers"]
    orders_enriched  = tables["orders_enriched"]
    items_enriched   = tables["items_enriched"]

    # PK uniqueness
    check("customers PK", customers["customer_id"].nunique() == len(customers),
          f"{customers['customer_id'].nunique():,} unique / {len(customers):,} rows")

    check("orders PK", orders["order_id"].nunique() == len(orders),
          f"{orders['order_id'].nunique():,} unique / {len(orders):,} rows")

    check("products PK", products["product_id"].nunique() == len(products),
          f"{products['product_id'].nunique():,} unique / {len(products):,} rows")

    check("sellers PK", sellers["seller_id"].nunique() == len(sellers),
          f"{sellers['seller_id'].nunique():,} unique / {len(sellers):,} rows")

    # Review dedup
    check("order_reviews one-per-order",
          order_reviews["order_id"].nunique() == len(order_reviews),
          f"{order_reviews['order_id'].nunique():,} unique order_id / {len(order_reviews):,} rows")

    # FK integrity
    orphan_orders = orders[~orders["customer_id"].isin(customers["customer_id"])]
    check("orders→customers FK", len(orphan_orders) == 0,
          f"{len(orphan_orders):,} orphan orders")

    orphan_items_order = order_items[~order_items["order_id"].isin(orders["order_id"])]
    check("order_items→orders FK", len(orphan_items_order) == 0,
          f"{len(orphan_items_order):,} orphan items")

    orphan_items_prod = order_items[~order_items["product_id"].isin(products["product_id"])]
    check("order_items→products FK", len(orphan_items_prod) == 0,
          f"{len(orphan_items_prod):,} orphan items (product)")

    orphan_items_seller = order_items[~order_items["seller_id"].isin(sellers["seller_id"])]
    check("order_items→sellers FK", len(orphan_items_seller) == 0,
          f"{len(orphan_items_seller):,} orphan items (seller)")

    orphan_payments = order_payments[~order_payments["order_id"].isin(orders["order_id"])]
    check("order_payments→orders FK", len(orphan_payments) == 0,
          f"{len(orphan_payments):,} orphan payments")

    # No row multiplication in orders_enriched
    check("orders_enriched grain = 1 row per order",
          orders_enriched["order_id"].nunique() == len(orders_enriched),
          f"{orders_enriched['order_id'].nunique():,} unique / {len(orders_enriched):,} rows")

    # No row multiplication in items_enriched
    exp_items = len(order_items)
    check("items_enriched row count matches order_items",
          len(items_enriched) == exp_items,
          f"items_enriched={len(items_enriched):,}, order_items={exp_items:,}")

    # Revenue consistency check
    rev_from_items = order_items["price"].sum() + order_items["freight_value"].sum()
    rev_from_enriched = orders_enriched["total_order_revenue"].sum()
    diff = abs(rev_from_items - rev_from_enriched)
    check("Revenue consistency: sum(order_items) ≈ sum(orders_enriched.total_order_revenue)",
          diff < 1.0,
          f"order_items sum=R${rev_from_items:,.2f}, enriched sum=R${rev_from_enriched:,.2f}, diff=R${diff:.2f}")

    # Date type checks
    check("orders dates are datetime",
          pd.api.types.is_datetime64_any_dtype(orders["order_purchase_timestamp"]),
          str(orders["order_purchase_timestamp"].dtype))

    # No negative delivery days (for delivered orders)
    negative_delivery = orders_enriched[
        orders_enriched["delivery_days"].notna() & (orders_enriched["delivery_days"] < 0)
    ]
    check("No negative delivery_days",
          len(negative_delivery) == 0,
          f"{len(negative_delivery):,} orders with negative delivery days")

    return results


# ===========================================================================
# MAIN PIPELINE
# ===========================================================================

def save(df: pd.DataFrame, filename: str):
    path = os.path.join(PROCESSED_DIR, filename)
    df.to_csv(path, index=False, encoding="utf-8")
    print(f"  Saved: {filename} ({len(df):,} rows)")


def main():
    print("=" * 70)
    print("OLIST DATA CLEANING PIPELINE")
    print("=" * 70)

    # ------------------------------------------------------------------
    # 1. Load raw data
    # ------------------------------------------------------------------
    print("\n[1] Loading raw tables...")
    raw = load_all_tables()

    row_counts_before = {k: len(v) for k, v in raw.items()}

    # ------------------------------------------------------------------
    # 2. Clean each table
    # ------------------------------------------------------------------
    print("\n[2] Cleaning tables...")

    customers_c   = clean_customers(raw["customers"].copy())
    geo_c         = clean_geolocation(raw["geolocation"].copy())
    geo_zip       = make_geolocation_zip(geo_c)
    orders_c      = clean_orders(raw["orders"].copy())
    items_c       = clean_order_items(raw["order_items"].copy())
    payments_c    = clean_order_payments(raw["order_payments"].copy())
    reviews_c     = clean_order_reviews(raw["order_reviews"].copy())
    products_c    = clean_products(raw["products"].copy())
    sellers_c     = clean_sellers(raw["sellers"].copy())
    cat_trans_c   = clean_category_translation(raw["category_translation"].copy())

    # ------------------------------------------------------------------
    # 3. Build analytics-ready enriched datasets
    # ------------------------------------------------------------------
    print("\n[3] Building analytics-ready datasets...")

    orders_enriched = build_orders_enriched(
        orders_c, customers_c, payments_c, items_c
    )
    items_enriched = build_order_items_enriched(
        items_c, orders_c, products_c, sellers_c, cat_trans_c
    )
    customer_analytics = build_customer_analytics(
        customers_c, orders_c, items_c, reviews_c, payments_c
    )
    product_analytics = build_product_analytics(
        products_c, items_c, reviews_c, orders_c, cat_trans_c
    )
    seller_analytics = build_seller_analytics(
        sellers_c, items_c, orders_c, reviews_c, products_c, cat_trans_c
    )

    # ------------------------------------------------------------------
    # 4. Validate
    # ------------------------------------------------------------------
    print("\n[4] Running validation checks...")
    validation_tables = {
        "customers": customers_c,
        "orders": orders_c,
        "order_items": items_c,
        "order_payments": payments_c,
        "order_reviews": reviews_c,
        "products": products_c,
        "sellers": sellers_c,
        "orders_enriched": orders_enriched,
        "items_enriched": items_enriched,
    }
    validation_results = run_validation(validation_tables)

    # ------------------------------------------------------------------
    # 5. Save processed datasets
    # ------------------------------------------------------------------
    print("\n[5] Saving processed datasets...")
    save(customers_c,        "customers_clean.csv")
    save(geo_c,              "geolocation_clean.csv")
    save(geo_zip,            "geolocation_zip.csv")
    save(orders_c,           "orders_clean.csv")
    save(items_c,            "order_items_clean.csv")
    save(payments_c,         "order_payments_clean.csv")
    save(reviews_c,          "order_reviews_clean.csv")
    save(products_c,         "products_clean.csv")
    save(sellers_c,          "sellers_clean.csv")
    save(cat_trans_c,        "category_translation_clean.csv")
    save(orders_enriched,    "orders_enriched.csv")
    save(items_enriched,     "order_items_enriched.csv")
    save(customer_analytics, "customer_analytics.csv")
    save(product_analytics,  "product_analytics.csv")
    save(seller_analytics,   "seller_analytics.csv")

    # ------------------------------------------------------------------
    # 6. Print summary report
    # ------------------------------------------------------------------
    row_counts_after = {
        "customers":        len(customers_c),
        "geolocation":      len(geo_c),
        "orders":           len(orders_c),
        "order_items":      len(items_c),
        "order_payments":   len(payments_c),
        "order_reviews":    len(reviews_c),
        "products":         len(products_c),
        "sellers":          len(sellers_c),
        "category_translation": len(cat_trans_c),
    }

    print("\n" + "=" * 70)
    print("CLEANING SUMMARY")
    print("=" * 70)
    print(f"\n{'Table':<30} {'Before':>10} {'After':>10} {'Removed':>10}")
    print("-" * 62)
    for k in row_counts_before:
        b = row_counts_before[k]
        a = row_counts_after.get(k, b)
        print(f"  {k:<28} {b:>10,} {a:>10,} {b-a:>10,}")

    print(f"\n\nAnalytics Datasets:")
    print(f"  {'orders_enriched':<35} {len(orders_enriched):>10,}")
    print(f"  {'order_items_enriched':<35} {len(items_enriched):>10,}")
    print(f"  {'customer_analytics':<35} {len(customer_analytics):>10,}")
    print(f"  {'product_analytics':<35} {len(product_analytics):>10,}")
    print(f"  {'seller_analytics':<35} {len(seller_analytics):>10,}")

    print("\n\nValidation Results:")
    passes = sum(1 for r in validation_results if r["status"] == "PASS")
    fails  = sum(1 for r in validation_results if r["status"] == "FAIL")
    print(f"  PASS: {passes}  |  FAIL: {fails}")
    for r in validation_results:
        marker = "✓" if r["status"] == "PASS" else "✗"
        print(f"  {marker} {r['check']}: {r['detail']}")

    print("\n\nCleaning Log:")
    for entry in CLEANING_LOG:
        print(f"  [{entry['table']}] {entry['issue']} | {entry['action']}")

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)

    return {
        "row_counts_before": row_counts_before,
        "row_counts_after": row_counts_after,
        "cleaning_log": CLEANING_LOG,
        "validation_results": validation_results,
        "analytics_rows": {
            "orders_enriched": len(orders_enriched),
            "order_items_enriched": len(items_enriched),
            "customer_analytics": len(customer_analytics),
            "product_analytics": len(product_analytics),
            "seller_analytics": len(seller_analytics),
        }
    }


if __name__ == "__main__":
    main()
