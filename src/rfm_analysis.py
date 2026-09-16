"""
rfm_analysis.py
===============
RFM (Recency, Frequency, Monetary) customer segmentation engine.

Uses ONLY delivered orders from the real Olist dataset.

Methodology:
  - Snapshot date = max(order_purchase_timestamp) + 1 day
  - Recency  = days since customer's last delivered order
  - Frequency= count of distinct delivered orders per customer_unique_id
  - Monetary = sum of total_order_revenue for delivered orders

Scoring:
  - Each dimension scored 1–5 using quintile-based binning
    (R: lower = better → reversed; F & M: higher = better)
  - RFM score = R_score * 100 + F_score * 10 + M_score
  - Segments derived from R_score + F_score (2-digit rule table)

Usage:
    from src.rfm_analysis import compute_rfm
    rfm_df = compute_rfm(orders_enriched_df)
"""

import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Segment rules — based on R and F scores only (industry-standard approach)
# ---------------------------------------------------------------------------
SEGMENT_MAP = {
    (5, 5): "Champions",
    (5, 4): "Champions",
    (4, 5): "Champions",
    (4, 4): "Loyal Customers",
    (3, 5): "Loyal Customers",
    (3, 4): "Loyal Customers",
    (5, 3): "Potential Loyalists",
    (4, 3): "Potential Loyalists",
    (5, 2): "Potential Loyalists",
    (5, 1): "New Customers",
    (4, 1): "New Customers",
    (3, 1): "Promising",
    (3, 2): "Promising",
    (4, 2): "Need Attention",
    (3, 3): "Need Attention",
    (2, 5): "At Risk",
    (2, 4): "At Risk",
    (2, 3): "At Risk",
    (2, 2): "At Risk",
    (1, 5): "Can't Lose Them",
    (1, 4): "Can't Lose Them",
    (1, 3): "Hibernating",
    (1, 2): "Hibernating",
    (2, 1): "Hibernating",
    (1, 1): "Lost",
}

# Colour per segment for charts
SEGMENT_COLORS = {
    "Champions":          "#059669",
    "Loyal Customers":    "#2563EB",
    "Potential Loyalists":"#7C3AED",
    "New Customers":      "#0891B2",
    "Promising":          "#CA8A04",
    "Need Attention":     "#D97706",
    "At Risk":            "#F97316",
    "Can't Lose Them":    "#DC2626",
    "Hibernating":        "#9CA3AF",
    "Lost":               "#6B7280",
}


def _score_quintile(series: pd.Series, reverse: bool = False) -> pd.Series:
    """Score a Series into 1–5 quintile buckets. reverse=True → lower value = higher score."""
    labels = [5, 4, 3, 2, 1] if reverse else [1, 2, 3, 4, 5]
    try:
        scored = pd.qcut(series, q=5, labels=labels, duplicates="drop")
    except ValueError:
        # If too few distinct values, use rank-based fallback
        scored = pd.cut(series, bins=5, labels=labels, duplicates="drop")
    return scored.astype(int)


def compute_rfm(orders: pd.DataFrame) -> pd.DataFrame:
    """
    Compute RFM metrics and segment labels for all customers
    who placed at least one delivered order.

    Parameters
    ----------
    orders : pd.DataFrame
        orders_enriched.csv loaded with order_purchase_timestamp as datetime.

    Returns
    -------
    pd.DataFrame with columns:
        customer_unique_id, recency_days, frequency, monetary,
        R, F, M, rfm_score, segment, customer_state, customer_city
    """
    delivered = orders[
        (orders["order_status"] == "delivered") &
        orders["total_order_revenue"].notna()
    ].copy()

    if "order_purchase_timestamp" not in delivered.columns:
        raise ValueError("orders must contain 'order_purchase_timestamp' as datetime.")

    delivered["order_purchase_timestamp"] = pd.to_datetime(
        delivered["order_purchase_timestamp"], errors="coerce"
    )

    snapshot_date = delivered["order_purchase_timestamp"].max() + pd.Timedelta(days=1)

    # Aggregate per customer
    rfm = (
        delivered.groupby("customer_unique_id")
        .agg(
            recency_days=(
                "order_purchase_timestamp",
                lambda x: (snapshot_date - x.max()).days,
            ),
            frequency=("order_id", "count"),
            monetary=("total_order_revenue", "sum"),
            customer_state=("customer_state", "first"),
            customer_city=("customer_city", "first"),
            last_order_date=("order_purchase_timestamp", "max"),
            first_order_date=("order_purchase_timestamp", "min"),
        )
        .reset_index()
    )

    # Score 1–5
    rfm["R"] = _score_quintile(rfm["recency_days"], reverse=True)
    rfm["F"] = _score_quintile(rfm["frequency"], reverse=False)
    rfm["M"] = _score_quintile(rfm["monetary"], reverse=False)

    rfm["rfm_score"] = rfm["R"].astype(str) + rfm["F"].astype(str) + rfm["M"].astype(str)

    # Segment lookup
    rfm["segment"] = rfm.apply(
        lambda row: SEGMENT_MAP.get((row["R"], row["F"]), "Hibernating"),
        axis=1,
    )

    return rfm


def rfm_segment_summary(rfm: pd.DataFrame) -> pd.DataFrame:
    """Aggregate RFM dataframe to segment-level summary."""
    summary = (
        rfm.groupby("segment")
        .agg(
            n_customers=("customer_unique_id", "count"),
            avg_recency=("recency_days", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_monetary=("monetary", "mean"),
            total_revenue=("monetary", "sum"),
        )
        .reset_index()
    )
    summary["revenue_share_pct"] = (
        summary["total_revenue"] / summary["total_revenue"].sum() * 100
    ).round(2)
    summary = summary.sort_values("total_revenue", ascending=False)
    return summary
