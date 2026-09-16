"""
data_loader.py
==============
Loads all Olist raw CSV files from data/raw/ with correct data types.

Usage:
    from src.data_loader import load_all_tables
    tables = load_all_tables()
    orders = tables["orders"]
"""

import os
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")

RAW_FILES = {
    "customers":          "olist_customers_dataset.csv",
    "geolocation":        "olist_geolocation_dataset.csv",
    "orders":             "olist_orders_dataset.csv",
    "order_items":        "olist_order_items_dataset.csv",
    "order_payments":     "olist_order_payments_dataset.csv",
    "order_reviews":      "olist_order_reviews_dataset.csv",
    "products":           "olist_products_dataset.csv",
    "sellers":            "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}

# ---------------------------------------------------------------------------
# Column-level dtype specifications (pre-parse, before date conversion)
# ---------------------------------------------------------------------------
DTYPES = {
    "customers": {
        "customer_id":               "string",
        "customer_unique_id":        "string",
        "customer_zip_code_prefix":  "Int64",
        "customer_city":             "string",
        "customer_state":            "string",
    },
    "geolocation": {
        "geolocation_zip_code_prefix": "Int64",
        "geolocation_lat":             "float64",
        "geolocation_lng":             "float64",
        "geolocation_city":            "string",
        "geolocation_state":           "string",
    },
    "orders": {
        "order_id":    "string",
        "customer_id": "string",
        "order_status": "string",
    },
    "order_items": {
        "order_id":     "string",
        "order_item_id": "Int64",
        "product_id":   "string",
        "seller_id":    "string",
        "price":        "float64",
        "freight_value": "float64",
    },
    "order_payments": {
        "order_id":              "string",
        "payment_sequential":    "Int64",
        "payment_type":          "string",
        "payment_installments":  "Int64",
        "payment_value":         "float64",
    },
    "order_reviews": {
        "review_id":    "string",
        "order_id":     "string",
        "review_score": "Int64",
    },
    "products": {
        "product_id":               "string",
        "product_category_name":    "string",
        "product_name_lenght":      "float64",
        "product_description_lenght": "float64",
        "product_photos_qty":       "float64",
        "product_weight_g":         "float64",
        "product_length_cm":        "float64",
        "product_height_cm":        "float64",
        "product_width_cm":         "float64",
    },
    "sellers": {
        "seller_id":               "string",
        "seller_zip_code_prefix":  "Int64",
        "seller_city":             "string",
        "seller_state":            "string",
    },
    "category_translation": {
        "product_category_name":         "string",
        "product_category_name_english": "string",
    },
}

# Date columns to parse per table
DATE_COLUMNS = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_items": ["shipping_limit_date"],
    "order_reviews": ["review_creation_date", "review_answer_timestamp"],
}


def _raw_path(filename: str) -> str:
    return os.path.join(RAW_DIR, filename)


def load_table(name: str) -> pd.DataFrame:
    """Load a single raw CSV by logical name."""
    if name not in RAW_FILES:
        raise ValueError(f"Unknown table '{name}'. Valid: {list(RAW_FILES)}")
    path = _raw_path(RAW_FILES[name])
    dtype_spec = DTYPES.get(name, {})
    date_cols = DATE_COLUMNS.get(name, [])

    df = pd.read_csv(
        path,
        dtype=dtype_spec,
        parse_dates=date_cols,
        encoding="utf-8",
        low_memory=False,
    )
    return df


def load_all_tables() -> dict[str, pd.DataFrame]:
    """Load all raw tables and return as a dict keyed by logical name."""
    tables = {}
    for name in RAW_FILES:
        tables[name] = load_table(name)
        print(f"  Loaded '{name}': {len(tables[name]):,} rows × {len(tables[name].columns)} cols")
    return tables


if __name__ == "__main__":
    print("Loading all Olist raw tables...\n")
    tbls = load_all_tables()
    print("\nAll tables loaded successfully.")
    for k, v in tbls.items():
        print(f"  {k}: {v.shape}")
