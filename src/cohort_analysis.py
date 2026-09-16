"""
cohort_analysis.py
==================
Monthly customer cohort retention analysis.

Methodology:
  - Cohort = month of customer's FIRST delivered order (by customer_unique_id)
  - Period Number = months elapsed since cohort month (0 = acquisition month)
  - Retention % = customers in cohort who purchased again in that period / cohort size × 100
  - Only delivered orders are used (consistent with revenue metrics)

Limitations documented:
  - Dataset covers Sep 2016–Aug 2018 (23 months). Cohorts formed late in the
    dataset naturally have fewer follow-up periods available.
  - Olist customers use one customer_id per order; customer_unique_id is the
    true person identifier. RFM and cohort use customer_unique_id.
  - Retention % values will appear low (platform ~3% repeat rate) — this is
    accurate for the dataset, not a calculation error.
"""

import pandas as pd
import numpy as np


def compute_cohorts(orders: pd.DataFrame) -> dict:
    """
    Build a monthly cohort retention table from orders_enriched data.

    Returns a dict with:
        cohort_pivot   : pd.DataFrame  (cohort × period_number, values = retention %)
        cohort_sizes   : pd.Series     (cohort → n customers in cohort)
        cohort_raw     : pd.DataFrame  (long format: cohort_ym, period_number, n_customers, retention_pct)
        snapshot_range : tuple         (min_date, max_date)
    """
    delivered = orders[orders["order_status"] == "delivered"].copy()
    delivered["order_purchase_timestamp"] = pd.to_datetime(
        delivered["order_purchase_timestamp"], errors="coerce"
    )
    delivered = delivered.dropna(subset=["order_purchase_timestamp", "customer_unique_id"])

    # Cohort = month of first delivered order
    delivered["year_month_str"] = delivered["order_purchase_timestamp"].dt.strftime("%Y-%m")
    first_ym = (
        delivered.groupby("customer_unique_id")["year_month_str"]
        .min()
        .reset_index()
        .rename(columns={"year_month_str": "cohort_ym"})
    )

    merged = delivered.merge(first_ym, on="customer_unique_id", how="left")

    # Period number in months (integer difference)
    merged["ym_period"]     = pd.to_datetime(merged["year_month_str"]   + "-01").dt.to_period("M")
    merged["cohort_period"] = pd.to_datetime(merged["cohort_ym"]        + "-01").dt.to_period("M")
    merged["period_number"] = (
        merged["ym_period"].astype("int64") - merged["cohort_period"].astype("int64")
    )

    # Count unique customers per cohort × period
    cohort_data = (
        merged.groupby(["cohort_ym", "period_number"])["customer_unique_id"]
        .nunique()
        .reset_index()
        .rename(columns={"customer_unique_id": "n_customers"})
    )

    cohort_sizes = (
        merged.groupby("cohort_ym")["customer_unique_id"]
        .nunique()
        .rename("cohort_size")
    )

    cohort_raw = cohort_data.merge(cohort_sizes, on="cohort_ym")
    cohort_raw["retention_pct"] = (
        cohort_raw["n_customers"] / cohort_raw["cohort_size"] * 100
    ).round(2)
    cohort_raw = cohort_raw.sort_values(["cohort_ym", "period_number"])

    # Pivot for heatmap
    pivot = cohort_raw.pivot_table(
        index="cohort_ym",
        columns="period_number",
        values="retention_pct",
        fill_value=0.0,
    ).sort_index()

    # Add cohort size as annotation
    pivot.index.name = "Cohort Month"
    pivot.columns.name = "Months Since First Purchase"

    return {
        "cohort_pivot":   pivot,
        "cohort_sizes":   cohort_sizes,
        "cohort_raw":     cohort_raw,
        "snapshot_range": (
            delivered["order_purchase_timestamp"].min(),
            delivered["order_purchase_timestamp"].max(),
        ),
    }


def cohort_summary(cohort_raw: pd.DataFrame) -> pd.DataFrame:
    """Summary table: cohort month, size, % who returned in month 1+."""
    cohort_sizes = (
        cohort_raw[cohort_raw["period_number"] == 0][["cohort_ym", "cohort_size"]]
    )
    returned = cohort_raw[cohort_raw["period_number"] >= 1].groupby("cohort_ym")["n_customers"].sum().reset_index()
    returned.columns = ["cohort_ym", "returned_customers"]
    summary = cohort_sizes.merge(returned, on="cohort_ym", how="left").fillna(0)
    summary["return_rate_pct"] = (
        summary["returned_customers"] / summary["cohort_size"] * 100
    ).round(2)
    return summary.sort_values("cohort_ym")
