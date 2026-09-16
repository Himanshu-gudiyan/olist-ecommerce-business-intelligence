"""
seller_intelligence.py
======================
Seller scorecard and performance intelligence engine.

Calculates per-seller metrics from actual order data and assigns
performance tiers. All values derived from delivered orders only.

Scorecard dimensions:
  - Revenue (total + avg order value)
  - Order volume
  - Customer satisfaction (avg review score)
  - Delivery performance (avg delivery days, late rate)
  - Product breadth (unique products)

Tiers assigned transparently using dataset percentiles — no arbitrary thresholds.
"""

import pandas as pd
import numpy as np


def compute_seller_scorecard(
    sellers: pd.DataFrame,
    orders: pd.DataFrame,
    items: pd.DataFrame,
    reviews: pd.DataFrame,
) -> pd.DataFrame:
    """
    Build enriched seller scorecard combining seller_analytics with
    delivery performance and per-seller review distribution.

    Parameters
    ----------
    sellers : seller_analytics.csv
    orders  : orders_enriched.csv (with delivery_days, is_delayed)
    items   : order_items_enriched.csv
    reviews : order_reviews_clean.csv (deduplicated per order_id)

    Returns
    -------
    pd.DataFrame — one row per seller_id with scorecard metrics + tier
    """
    # Base from seller_analytics (already delivered-only)
    sc = sellers.copy()

    # Delivery stats per seller from order items
    del_orders = orders[
        (orders["order_status"] == "delivered") &
        orders["delivery_days"].notna()
    ][["order_id", "delivery_days", "is_delayed"]].copy()
    del_orders["is_delayed"] = pd.to_numeric(del_orders["is_delayed"], errors="coerce")

    del_items = items[items["order_status"] == "delivered"][
        ["order_id", "seller_id"]
    ].drop_duplicates()

    seller_delivery = (
        del_items.merge(del_orders, on="order_id", how="left")
        .groupby("seller_id")
        .agg(
            avg_delivery_days=("delivery_days", "mean"),
            late_rate_pct=("is_delayed", lambda x: (x == 1.0).mean() * 100),
            n_delivered=("order_id", "nunique"),
        )
        .reset_index()
    )

    sc = sc.merge(seller_delivery, on="seller_id", how="left")

    # Review distribution per seller
    rev_clean = reviews[["order_id", "review_score"]].drop_duplicates("order_id")
    seller_reviews = (
        del_items.merge(rev_clean, on="order_id", how="left")
        .groupby("seller_id")
        .agg(
            pct_5star=("review_score", lambda x: (x == 5).mean() * 100),
            pct_1star=("review_score", lambda x: (x == 1).mean() * 100),
            n_reviews=("review_score", "count"),
        )
        .reset_index()
    )
    sc = sc.merge(seller_reviews, on="seller_id", how="left")

    # Number of unique customers served (from items→orders→customer)
    del_items_cust = items[items["order_status"] == "delivered"][
        ["order_id", "seller_id"]
    ].merge(
        orders[["order_id", "customer_unique_id"]],
        on="order_id", how="left",
    )
    seller_customers = (
        del_items_cust.groupby("seller_id")["customer_unique_id"]
        .nunique()
        .reset_index()
        .rename(columns={"customer_unique_id": "n_customers_served"})
    )
    sc = sc.merge(seller_customers, on="seller_id", how="left")

    # AOV per seller
    sc["seller_aov"] = sc["total_revenue"] / sc["n_unique_orders"].replace(0, np.nan)

    # Performance tiers (quintile-based, transparent)
    def quintile_tier(series, reverse=False):
        labels = ["Low", "Below Avg", "Average", "Above Avg", "High"]
        if reverse:
            labels = labels[::-1]
        try:
            return pd.qcut(series.fillna(series.median()), q=5,
                           labels=labels, duplicates="drop")
        except ValueError:
            return pd.cut(series.fillna(series.median()), bins=5,
                          labels=labels, duplicates="drop")

    sc["revenue_tier"]       = quintile_tier(sc["total_revenue"])
    sc["review_tier"]        = quintile_tier(sc["avg_review_score"])
    sc["delivery_tier"]      = quintile_tier(sc["avg_delivery_days"], reverse=True)
    sc["late_rate_tier"]     = quintile_tier(sc["late_rate_pct"], reverse=True)

    # Composite performance flag
    def performance_flag(row):
        rev_high  = str(row.get("revenue_tier",  "")) in ["High", "Above Avg"]
        rev_low   = str(row.get("revenue_tier",  "")) in ["Low", "Below Avg"]
        rev_good  = str(row.get("review_tier",   "")) in ["High", "Above Avg"]
        rev_poor  = str(row.get("review_tier",   "")) in ["Low", "Below Avg"]
        del_good  = str(row.get("delivery_tier", "")) in ["High", "Above Avg"]
        del_poor  = str(row.get("delivery_tier", "")) in ["Low", "Below Avg"]

        if rev_high and rev_good:
            return "Top Performer"
        elif rev_high and rev_poor:
            return "High Revenue, Low Satisfaction"
        elif rev_low and rev_good and del_good:
            return "Hidden Gem (grow this)"
        elif rev_poor and del_good and rev_good:
            return "Hidden Gem (grow this)"
        elif del_poor:
            return "Delivery Problem"
        elif rev_poor:
            return "Under-Performing"
        else:
            return "Average"

    sc["performance_flag"] = sc.apply(performance_flag, axis=1)

    return sc


def seller_opportunity_analysis(sc: pd.DataFrame) -> dict:
    """Return dict of opportunity DataFrames for dashboard display."""
    return {
        "top_performers": sc[sc["performance_flag"] == "Top Performer"]
            .sort_values("total_revenue", ascending=False).head(20),
        "high_rev_low_sat": sc[sc["performance_flag"] == "High Revenue, Low Satisfaction"]
            .sort_values("total_revenue", ascending=False).head(20),
        "hidden_gems": sc[sc["performance_flag"] == "Hidden Gem (grow this)"]
            .sort_values("avg_review_score", ascending=False).head(20),
        "delivery_problems": sc[sc["performance_flag"] == "Delivery Problem"]
            .sort_values("late_rate_pct", ascending=False).head(20),
        "under_performing": sc[sc["performance_flag"] == "Under-Performing"]
            .sort_values("total_revenue").head(20),
    }
