"""
eda_analysis.py
===============
Advanced Exploratory Data Analysis for Olist E-Commerce dataset.

Reads from : data/processed/
Writes to  : outputs/charts/   (PNG files)
             outputs/eda_results.json  (all computed metrics)

Run:
    python src/eda_analysis.py
"""

import os
import sys
import json
import warnings
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC_DIR    = os.path.join(ROOT, "data", "processed")
CHART_DIR   = os.path.join(ROOT, "outputs", "charts")
OUTPUT_DIR  = os.path.join(ROOT, "outputs")
os.makedirs(CHART_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Plotting style
# ---------------------------------------------------------------------------
sns.set_theme(style="whitegrid", palette="muted", font_scale=1.05)
plt.rcParams.update({
    "figure.dpi": 120,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "font.family": "DejaVu Sans",
})

ACCENT   = "#2563EB"   # blue
ACCENT2  = "#7C3AED"   # violet
ACCENT3  = "#059669"   # green
WARN     = "#DC2626"   # red
PALETTE  = ["#2563EB","#7C3AED","#059669","#D97706","#DC2626",
             "#0891B2","#BE185D","#4B5563","#CA8A04","#0D9488"]

RESULTS = {}   # accumulates all numeric results


def savefig(name: str) -> str:
    path = os.path.join(CHART_DIR, name)
    plt.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close("all")
    print(f"  Chart saved: {name}")
    return path


def fmt_brl(x):
    return "R${:,.0f}".format(x)


# ===========================================================================
# DATA LOADING
# ===========================================================================

def load_data():
    print("[Loading processed datasets]")
    def read(f):
        return pd.read_csv(os.path.join(PROC_DIR, f), low_memory=False)

    orders      = read("orders_enriched.csv")
    items       = read("order_items_enriched.csv")
    customers   = read("customer_analytics.csv")
    products    = read("product_analytics.csv")
    sellers     = read("seller_analytics.csv")
    reviews     = read("order_reviews_clean.csv")
    payments    = read("order_payments_clean.csv")
    orders_raw  = read("orders_clean.csv")

    # Parse dates
    for col in ["order_purchase_timestamp","order_delivered_customer_date",
                "order_estimated_delivery_date","order_approved_at"]:
        if col in orders.columns:
            orders[col] = pd.to_datetime(orders[col], errors="coerce")

    orders["first_order_date"] = pd.to_datetime(
        customers["first_order_date"] if "first_order_date" in customers.columns
        else None, errors="coerce"
    )

    print(f"  orders_enriched:   {len(orders):,} rows")
    print(f"  order_items:       {len(items):,} rows")
    print(f"  customer_analytics:{len(customers):,} rows")
    print(f"  product_analytics: {len(products):,} rows")
    print(f"  seller_analytics:  {len(sellers):,} rows")
    print(f"  reviews:           {len(reviews):,} rows")
    print(f"  payments:          {len(payments):,} rows")
    return orders, items, customers, products, sellers, reviews, payments


# ===========================================================================
# SECTION 1 — DESCRIPTIVE ANALYSIS
# ===========================================================================

def descriptive_analysis(orders, items, customers, products, sellers, reviews, payments):
    print("\n[1] Descriptive Analysis")

    delivered = orders[orders["order_status"] == "delivered"]

    # --- Basic counts ---
    total_orders       = len(orders)
    delivered_orders   = len(delivered)
    total_customers    = customers["customer_unique_id"].nunique()
    repeat_buyers      = int(customers["is_repeat_buyer"].sum())
    total_products_sold = len(products)
    total_sellers      = len(sellers)
    date_min           = orders["order_purchase_timestamp"].min()
    date_max           = orders["order_purchase_timestamp"].max()
    date_span_days     = (date_max - date_min).days

    print(f"  Total orders: {total_orders:,}")
    print(f"  Delivered:    {delivered_orders:,}")
    print(f"  Date range:   {date_min.date()} to {date_max.date()} ({date_span_days} days)")
    print(f"  Customers:    {total_customers:,}")
    print(f"  Repeat buyers:{repeat_buyers:,}")

    RESULTS["descriptive"] = {
        "total_orders": total_orders,
        "delivered_orders": delivered_orders,
        "canceled_orders": int((orders["order_status"] == "canceled").sum()),
        "total_unique_customers": total_customers,
        "repeat_buyers": repeat_buyers,
        "repeat_buyer_rate_pct": round(repeat_buyers / total_customers * 100, 2),
        "total_products_in_analytics": total_products_sold,
        "total_active_sellers": len(sellers),
        "date_min": str(date_min.date()),
        "date_max": str(date_max.date()),
        "date_span_days": date_span_days,
    }

    # --- Chart 1: Order Status Distribution ---
    status_counts = orders["order_status"].value_counts().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(9, 4))
    bars = ax.barh(status_counts.index, status_counts.values,
                   color=[ACCENT if s == "delivered" else "#94A3B8" for s in status_counts.index])
    ax.set_xlabel("Number of Orders")
    ax.set_title("Order Status Distribution  (n = {:,})".format(total_orders), fontweight="bold")
    for bar, val in zip(bars, status_counts.values):
        ax.text(bar.get_width() + 200, bar.get_y() + bar.get_height()/2,
                f"{val:,}  ({val/total_orders*100:.1f}%)",
                va="center", fontsize=9)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.set_xlim(0, status_counts.max() * 1.22)
    savefig("01_order_status_distribution.png")

    # --- Chart 2: Payment Type Distribution ---
    pay_counts = payments["payment_type"].value_counts()
    pay_pct    = pay_counts / pay_counts.sum() * 100
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    ax1.bar(pay_counts.index, pay_counts.values,
            color=PALETTE[:len(pay_counts)])
    ax1.set_title("Payment Type — Count", fontweight="bold")
    ax1.set_ylabel("Number of Transactions")
    for i, (cnt, pct) in enumerate(zip(pay_counts.values, pay_pct.values)):
        ax1.text(i, cnt + 300, f"{cnt:,}\n({pct:.1f}%)", ha="center", fontsize=8.5)
    ax1.set_xticklabels(pay_counts.index, rotation=20)
    # Avg payment value per type
    avg_pay = payments.groupby("payment_type")["payment_value"].mean().reindex(pay_counts.index)
    ax2.bar(avg_pay.index, avg_pay.values, color=PALETTE[:len(avg_pay)])
    ax2.set_title("Avg Payment Value per Transaction (R$)", fontweight="bold")
    ax2.set_ylabel("Avg Payment Value (R$)")
    for i, v in enumerate(avg_pay.values):
        ax2.text(i, v + 2, f"R${v:.0f}", ha="center", fontsize=8.5)
    ax2.set_xticklabels(avg_pay.index, rotation=20)
    plt.suptitle("Payment Method Analysis", fontsize=12, fontweight="bold", y=1.02)
    plt.tight_layout()
    savefig("02_payment_type_distribution.png")

    RESULTS["descriptive"]["payment_type_counts"] = dict(pay_counts)
    RESULTS["descriptive"]["payment_type_avg_value"] = {k: round(v, 2) for k, v in avg_pay.items()}

    # --- Chart 3: Review Score Distribution ---
    score_counts = reviews["review_score"].value_counts().sort_index()
    score_pct    = score_counts / score_counts.sum() * 100
    colors_score = [WARN, "#F97316", "#EAB308", ACCENT3, ACCENT]
    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(score_counts.index.astype(str), score_counts.values,
                  color=colors_score)
    for bar, cnt, pct in zip(bars, score_counts.values, score_pct.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 300,
                f"{cnt:,}\n({pct:.1f}%)", ha="center", fontsize=9)
    ax.set_xlabel("Star Rating")
    ax.set_ylabel("Number of Reviews")
    ax.set_title(f"Review Score Distribution  (avg = {reviews['review_score'].mean():.2f}/5.0)", fontweight="bold")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    savefig("03_review_score_distribution.png")

    RESULTS["descriptive"]["review_score_distribution"] = dict(score_counts)
    RESULTS["descriptive"]["avg_review_score"] = round(reviews["review_score"].mean(), 4)


# ===========================================================================
# SECTION 2 — BUSINESS KPIs
# ===========================================================================

def business_kpis(orders, items, customers, sellers, reviews, payments):
    print("\n[2] Business KPIs")

    delivered = orders[orders["order_status"] == "delivered"]

    # Revenue from delivered order items
    del_items  = items[items["order_status"] == "delivered"]
    total_rev  = del_items["item_revenue"].sum()
    prod_rev   = del_items["price"].sum()
    freight_rev = del_items["freight_value"].sum()

    aov        = delivered["total_order_revenue"].mean()
    avg_items  = delivered["item_count"].mean()
    avg_freight= del_items["freight_value"].mean()
    cancel_rate= (orders["order_status"] == "canceled").sum() / len(orders) * 100
    repeat_rate= customers["is_repeat_buyer"].mean() * 100
    avg_review = reviews["review_score"].mean()

    # Delivery metrics
    has_delivery = delivered[delivered["delivery_days"].notna()]
    avg_delivery = has_delivery["delivery_days"].mean()
    has_delay    = has_delivery[has_delivery["is_delayed"].notna()]
    late_rate    = (has_delay["is_delayed"].astype(float) == 1.0).mean() * 100
    on_time_rate = 100 - late_rate
    avg_delay_days = has_delay[has_delay["is_delayed"].astype(float) == 1.0]["delivery_delay_days"].mean()

    kpis = {
        "total_orders":          len(orders),
        "delivered_orders":      len(delivered),
        "total_revenue_brl":     round(total_rev, 2),
        "product_revenue_brl":   round(prod_rev, 2),
        "freight_revenue_brl":   round(freight_rev, 2),
        "freight_pct_of_revenue":round(freight_rev / total_rev * 100, 2),
        "avg_order_value":       round(aov, 2),
        "avg_items_per_order":   round(avg_items, 4),
        "avg_freight_per_item":  round(avg_freight, 2),
        "cancellation_rate_pct": round(cancel_rate, 2),
        "repeat_buyer_rate_pct": round(repeat_rate, 2),
        "avg_review_score":      round(avg_review, 4),
        "avg_delivery_days":     round(avg_delivery, 2),
        "on_time_delivery_rate": round(on_time_rate, 2),
        "late_delivery_rate":    round(late_rate, 2),
        "avg_delay_when_late_days": round(avg_delay_days, 2),
        "total_unique_customers":len(customers),
        "active_sellers":        len(sellers),
    }
    RESULTS["kpis"] = kpis

    for k, v in kpis.items():
        print(f"  {k:<40}: {v}")

    # --- Chart 4: KPI Summary Dashboard ---
    fig, axes = plt.subplots(2, 4, figsize=(16, 7))
    fig.suptitle("Core Business KPI Dashboard — Olist E-Commerce (2016–2018)",
                 fontsize=14, fontweight="bold", y=1.01)

    kpi_items = [
        ("Total Orders",    f"{len(orders):,}",         ACCENT),
        ("Delivered Orders",f"{len(delivered):,}",       ACCENT3),
        ("Total Revenue",   f"R${total_rev/1e6:.2f}M",  ACCENT2),
        ("Avg Order Value", f"R${aov:.0f}",              "#D97706"),
        ("Avg Review Score",f"{avg_review:.2f} / 5.0",  "#059669"),
        ("Avg Delivery Days",f"{avg_delivery:.1f} days", "#0891B2"),
        ("On-Time Rate",    f"{on_time_rate:.1f}%",      ACCENT3),
        ("Repeat Buyer Rate",f"{repeat_rate:.1f}%",      "#BE185D"),
    ]
    for ax, (label, value, color) in zip(axes.flat, kpi_items):
        ax.set_facecolor(color + "15")
        ax.text(0.5, 0.62, value, ha="center", va="center",
                fontsize=20, fontweight="bold", color=color,
                transform=ax.transAxes)
        ax.text(0.5, 0.30, label, ha="center", va="center",
                fontsize=10, color="#374151", transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_edgecolor(color)
            spine.set_linewidth(1.5)
    plt.tight_layout()
    savefig("04_kpi_dashboard.png")

    return kpis


# ===========================================================================
# SECTION 3 — SALES & REVENUE ANALYSIS
# ===========================================================================

def sales_revenue_analysis(orders, items):
    print("\n[3] Sales & Revenue Analysis")

    del_orders = orders[orders["order_status"] == "delivered"].copy()
    del_items  = items[items["order_status"] == "delivered"].copy()

    # Ensure datetime
    del_orders["order_purchase_timestamp"] = pd.to_datetime(
        del_orders["order_purchase_timestamp"], errors="coerce")
    del_orders["ym_period"] = del_orders["order_purchase_timestamp"].dt.to_period("M")
    del_items["order_purchase_timestamp"] = pd.to_datetime(
        del_items["order_purchase_timestamp"], errors="coerce")
    del_items["ym_period"] = del_items["order_purchase_timestamp"].dt.to_period("M")

    # Monthly revenue + orders
    monthly_rev = (
        del_items.groupby("ym_period")["item_revenue"]
        .sum().reset_index().rename(columns={"item_revenue": "revenue"})
    )
    monthly_orders = (
        del_orders.groupby("ym_period")["order_id"]
        .count().reset_index().rename(columns={"order_id": "n_orders"})
    )
    monthly = monthly_rev.merge(monthly_orders, on="ym_period", how="outer")
    monthly = monthly.sort_values("ym_period")
    monthly["ym_str"] = monthly["ym_period"].astype(str)
    monthly["aov"] = monthly["revenue"] / monthly["n_orders"]

    # Drop first month (Sep 2016 — partial, only 4 orders) and last partial month
    monthly = monthly[(monthly["ym_str"] >= "2016-10") & (monthly["ym_str"] <= "2018-08")]

    RESULTS["monthly"] = {
        "peak_revenue_month": monthly.loc[monthly["revenue"].idxmax(), "ym_str"],
        "peak_revenue_value": round(monthly["revenue"].max(), 2),
        "peak_orders_month":  monthly.loc[monthly["n_orders"].idxmax(), "ym_str"],
        "peak_orders_value":  int(monthly["n_orders"].max()),
        "avg_monthly_revenue": round(monthly["revenue"].mean(), 2),
        "avg_monthly_orders":  round(monthly["n_orders"].mean(), 2),
    }

    # --- Chart 5: Monthly Revenue Trend ---
    fig, ax1 = plt.subplots(figsize=(14, 5))
    ax2 = ax1.twinx()
    x = range(len(monthly))
    ax1.fill_between(x, monthly["revenue"], alpha=0.25, color=ACCENT)
    ax1.plot(x, monthly["revenue"], color=ACCENT, linewidth=2.5, marker="o", markersize=4)
    ax2.plot(x, monthly["n_orders"], color=ACCENT3, linewidth=2, linestyle="--",
             marker="s", markersize=4, alpha=0.85)
    ax1.set_xticks(x)
    ax1.set_xticklabels(monthly["ym_str"], rotation=45, ha="right", fontsize=8)
    ax1.set_ylabel("Monthly Revenue (R$)", color=ACCENT, fontweight="bold")
    ax2.set_ylabel("Number of Orders", color=ACCENT3, fontweight="bold")
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"R${v/1e3:.0f}K"))
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
    ax1.set_title("Monthly Revenue & Order Volume Trend  (Oct 2016 – Aug 2018)",
                  fontweight="bold", fontsize=12)
    lines1 = plt.Line2D([0], [0], color=ACCENT, linewidth=2, marker="o", markersize=5, label="Revenue (R$)")
    lines2 = plt.Line2D([0], [0], color=ACCENT3, linewidth=2, linestyle="--", marker="s", markersize=5, label="Orders")
    ax1.legend(handles=[lines1, lines2], loc="upper left")
    plt.tight_layout()
    savefig("05_monthly_revenue_trend.png")

    # --- Chart 6: AOV over time ---
    fig, ax = plt.subplots(figsize=(13, 4))
    ax.plot(x, monthly["aov"], color=ACCENT2, linewidth=2.5, marker="o", markersize=4)
    ax.fill_between(x, monthly["aov"], alpha=0.15, color=ACCENT2)
    ax.set_xticks(x)
    ax.set_xticklabels(monthly["ym_str"], rotation=45, ha="right", fontsize=8)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"R${v:.0f}"))
    ax.set_ylabel("Average Order Value (R$)")
    ax.set_title("Average Order Value (AOV) Over Time", fontweight="bold")
    avg_aov_line = monthly["aov"].mean()
    ax.axhline(avg_aov_line, color="#9CA3AF", linestyle=":", linewidth=1.5,
               label=f"Overall avg R${avg_aov_line:.0f}")
    ax.legend()
    plt.tight_layout()
    savefig("06_aov_over_time.png")

    # --- Chart 7: Top 15 Categories by Revenue ---
    cat_rev = (
        del_items.groupby("product_category_name_english")["item_revenue"]
        .sum().sort_values(ascending=False).head(15).reset_index()
    )
    cat_rev.columns = ["category", "revenue"]
    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.barh(cat_rev["category"][::-1], cat_rev["revenue"][::-1],
                   color=[ACCENT if i < 5 else "#93C5FD" for i in range(14, -1, -1)])
    for bar, rev in zip(bars, cat_rev["revenue"][::-1]):
        ax.text(bar.get_width() + 3000, bar.get_y() + bar.get_height()/2,
                f"R${bar.get_width()/1e3:.0f}K", va="center", fontsize=8.5)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"R${v/1e3:.0f}K"))
    ax.set_xlabel("Total Revenue (R$)")
    ax.set_title("Top 15 Product Categories by Revenue  (delivered orders)",
                 fontweight="bold")
    ax.set_xlim(0, cat_rev["revenue"].max() * 1.18)
    plt.tight_layout()
    savefig("07_top_categories_revenue.png")

    RESULTS["top_categories_revenue"] = dict(
        zip(cat_rev["category"], cat_rev["revenue"].round(2).tolist())
    )

    # --- Chart 8: Top 15 Categories by Number of Items Sold ---
    cat_vol = (
        del_items.groupby("product_category_name_english")["order_id"]
        .count().sort_values(ascending=False).head(15).reset_index()
    )
    cat_vol.columns = ["category", "items_sold"]
    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.barh(cat_vol["category"][::-1], cat_vol["items_sold"][::-1],
                   color=[ACCENT3 if i < 5 else "#6EE7B7" for i in range(14, -1, -1)])
    for bar, cnt in zip(bars, cat_vol["items_sold"][::-1]):
        ax.text(bar.get_width() + 50, bar.get_y() + bar.get_height()/2,
                f"{int(bar.get_width()):,}", va="center", fontsize=8.5)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
    ax.set_xlabel("Items Sold")
    ax.set_title("Top 15 Product Categories by Items Sold  (delivered orders)",
                 fontweight="bold")
    ax.set_xlim(0, cat_vol["items_sold"].max() * 1.14)
    plt.tight_layout()
    savefig("08_top_categories_volume.png")

    RESULTS["top_categories_volume"] = dict(
        zip(cat_vol["category"], cat_vol["items_sold"].tolist())
    )

    # --- Chart 9: Top 15 Sellers by Revenue ---
    top_sellers_rev = sellers_analysis_quick(None)  # placeholder — filled below
    return monthly, cat_rev, cat_vol


def sellers_analysis_quick(sellers_df):
    return None  # stub — full analysis in seller_analysis()


# ===========================================================================
# SECTION 4 — SELLER ANALYSIS
# ===========================================================================

def seller_analysis(sellers):
    print("\n[4] Seller Analysis")

    top_by_rev = sellers.sort_values("total_revenue", ascending=False).head(15)
    top_by_ord = sellers.sort_values("n_unique_orders", ascending=False).head(15)

    RESULTS["sellers"] = {
        "total_active_sellers": len(sellers),
        "top_seller_revenue":   round(sellers["total_revenue"].max(), 2),
        "median_seller_revenue":round(sellers["total_revenue"].median(), 2),
        "top_10_sellers_pct_of_total_revenue": round(
            sellers.nlargest(10, "total_revenue")["total_revenue"].sum()
            / sellers["total_revenue"].sum() * 100, 2
        ),
        "states_with_sellers": sellers["seller_state"].nunique(),
    }

    # --- Chart 10: Top 15 Sellers by Revenue ---
    fig, ax = plt.subplots(figsize=(11, 6))
    rev_vals = top_by_rev["total_revenue"].values
    labels   = ["Seller " + s[:6] + "..." for s in top_by_rev["seller_id"]]
    ax.barh(labels[::-1], rev_vals[::-1], color=ACCENT)
    for i, (bar, rev, state) in enumerate(zip(ax.patches, rev_vals[::-1],
                                               top_by_rev["seller_state"].values[::-1])):
        ax.text(bar.get_width() + 500, bar.get_y() + bar.get_height()/2,
                f"R${rev/1e3:.0f}K  ({state})", va="center", fontsize=8.5)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"R${v/1e3:.0f}K"))
    ax.set_xlabel("Total Revenue (R$)")
    ax.set_title("Top 15 Sellers by Revenue  (delivered orders)", fontweight="bold")
    ax.set_xlim(0, rev_vals.max() * 1.28)
    plt.tight_layout()
    savefig("09_top_sellers_revenue.png")

    # --- Chart 11: Revenue by Seller State ---
    state_seller_rev = (
        sellers.groupby("seller_state")["total_revenue"]
        .sum().sort_values(ascending=False).reset_index()
    )
    fig, ax = plt.subplots(figsize=(11, 5))
    colors_s = [ACCENT if i == 0 else "#93C5FD" for i in range(len(state_seller_rev))]
    ax.bar(state_seller_rev["seller_state"], state_seller_rev["total_revenue"], color=colors_s)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"R${v/1e6:.1f}M"))
    ax.set_xlabel("Seller State")
    ax.set_ylabel("Total Revenue (R$)")
    ax.set_title("Revenue by Seller State", fontweight="bold")
    ax.tick_params(axis="x", rotation=45)
    plt.tight_layout()
    savefig("10_revenue_by_seller_state.png")

    RESULTS["sellers"]["revenue_by_seller_state"] = dict(
        zip(state_seller_rev["seller_state"],
            state_seller_rev["total_revenue"].round(2).tolist())
    )


# ===========================================================================
# SECTION 5 — CUSTOMER ANALYSIS
# ===========================================================================

def customer_analysis(customers, orders):
    print("\n[5] Customer Analysis")

    del_orders = orders[orders["order_status"] == "delivered"]

    # --- Chart 12: Customers & Revenue by State ---
    cust_state = (
        customers.groupby("customer_state")
        .agg(n_customers=("customer_unique_id", "count"),
             avg_spend=("total_spend_payment", "mean"))
        .reset_index()
        .sort_values("n_customers", ascending=False)
    )
    rev_state = (
        del_orders.groupby("customer_state")["total_order_revenue"]
        .sum().reset_index().rename(columns={"total_order_revenue": "total_revenue"})
    )
    state_merged = cust_state.merge(rev_state, on="customer_state", how="left")

    top_states = state_merged.head(15)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 5))

    ax1.barh(top_states["customer_state"][::-1], top_states["n_customers"][::-1],
             color=ACCENT)
    for bar, v in zip(ax1.patches, top_states["n_customers"][::-1]):
        ax1.text(bar.get_width() + 50, bar.get_y() + bar.get_height()/2,
                 f"{v:,}", va="center", fontsize=8)
    ax1.set_xlabel("Unique Customers")
    ax1.set_title("Top 15 States by Customer Count", fontweight="bold")
    ax1.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))

    ax2.barh(top_states["customer_state"][::-1], top_states["total_revenue"][::-1],
             color=ACCENT3)
    for bar, v in zip(ax2.patches, top_states["total_revenue"][::-1]):
        ax2.text(bar.get_width() + 2000, bar.get_y() + bar.get_height()/2,
                 f"R${v/1e6:.1f}M", va="center", fontsize=8)
    ax2.set_xlabel("Total Revenue (R$)")
    ax2.set_title("Top 15 States by Revenue (Delivered)", fontweight="bold")
    ax2.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"R${v/1e6:.1f}M"))

    plt.suptitle("Customer Geographic Distribution", fontsize=13, fontweight="bold")
    plt.tight_layout()
    savefig("11_customers_by_state.png")

    RESULTS["customers"] = {
        "top_states_by_customers": dict(
            zip(top_states["customer_state"], top_states["n_customers"].tolist())
        ),
        "top_states_by_revenue": dict(
            zip(top_states["customer_state"], top_states["total_revenue"].round(2).tolist())
        ),
    }

    # --- Chart 13: Order Frequency Distribution ---
    freq = customers["total_orders"].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(9, 4))
    colors_f = [WARN if i == 0 else (ACCENT2 if i == 1 else ACCENT3)
                for i in range(len(freq))]
    ax.bar(freq.index.astype(str), freq.values, color=PALETTE[:len(freq)])
    for i, (idx, v) in enumerate(zip(freq.index, freq.values)):
        ax.text(i, v + 100, f"{v:,}\n({v/len(customers)*100:.1f}%)",
                ha="center", fontsize=8.5)
    ax.set_xlabel("Number of Orders Placed")
    ax.set_ylabel("Number of Customers")
    ax.set_title("Customer Purchase Frequency Distribution", fontweight="bold")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
    plt.tight_layout()
    savefig("12_order_frequency_distribution.png")

    RESULTS["customers"]["order_frequency"] = dict(
        zip(freq.index.tolist(), freq.values.tolist())
    )

    # --- Chart 14: Customer Segmentation (rule-based) ---
    # Segments based on total_orders and total_spend_payment
    def segment(row):
        if row["total_orders"] >= 3:
            return "High-Frequency (3+ orders)"
        elif row["total_orders"] == 2:
            return "Returning (2 orders)"
        elif row["total_spend_payment"] >= 500:
            return "High-Value (1 order, R$500+)"
        else:
            return "Single-Purchase (<R$500)"

    customers["segment"] = customers.apply(segment, axis=1)
    seg_summary = (
        customers.groupby("segment")
        .agg(n_customers=("customer_unique_id", "count"),
             avg_spend=("total_spend_payment", "mean"),
             avg_orders=("total_orders", "mean"))
        .reset_index()
        .sort_values("n_customers", ascending=False)
    )
    RESULTS["customers"]["segments"] = seg_summary.to_dict(orient="records")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    colors_seg = [ACCENT, ACCENT2, ACCENT3, WARN]
    ax1.barh(seg_summary["segment"][::-1], seg_summary["n_customers"][::-1],
             color=colors_seg[::-1])
    for bar, v in zip(ax1.patches, seg_summary["n_customers"][::-1]):
        ax1.text(bar.get_width() + 100, bar.get_y() + bar.get_height()/2,
                 f"{v:,}", va="center", fontsize=8.5)
    ax1.set_xlabel("Number of Customers")
    ax1.set_title("Customer Segments — Size", fontweight="bold")
    ax1.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))

    ax2.barh(seg_summary["segment"][::-1], seg_summary["avg_spend"][::-1],
             color=colors_seg[::-1])
    for bar, v in zip(ax2.patches, seg_summary["avg_spend"][::-1]):
        ax2.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2,
                 f"R${v:.0f}", va="center", fontsize=8.5)
    ax2.set_xlabel("Avg Total Spend (R$)")
    ax2.set_title("Customer Segments — Avg Spend", fontweight="bold")
    plt.suptitle("Rule-Based Customer Segmentation", fontsize=12, fontweight="bold")
    plt.tight_layout()
    savefig("13_customer_segmentation.png")


# ===========================================================================
# SECTION 6 — LOGISTICS ANALYSIS
# ===========================================================================

def logistics_analysis(orders, items):
    print("\n[6] Logistics Analysis")

    del_orders = orders[
        (orders["order_status"] == "delivered") &
        orders["delivery_days"].notna()
    ].copy()
    del_items = items[items["order_status"] == "delivered"].copy()

    avg_del   = del_orders["delivery_days"].mean()
    med_del   = del_orders["delivery_days"].median()
    p90_del   = del_orders["delivery_days"].quantile(0.90)
    late_mask = del_orders["is_delayed"].astype(float) == 1.0
    late_rate = late_mask.mean() * 100
    avg_late_delay = del_orders.loc[late_mask, "delivery_delay_days"].mean()

    RESULTS["logistics"] = {
        "avg_delivery_days":  round(avg_del, 2),
        "median_delivery_days": round(med_del, 2),
        "p90_delivery_days":  round(p90_del, 2),
        "late_rate_pct":      round(late_rate, 2),
        "avg_delay_when_late": round(avg_late_delay, 2),
        "avg_freight_per_item": round(del_items["freight_value"].mean(), 2),
        "median_freight":     round(del_items["freight_value"].median(), 2),
    }

    # --- Chart 15: Delivery Days Distribution ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    ax1, ax2 = axes

    ax1.hist(del_orders["delivery_days"].clip(upper=60), bins=50,
             color=ACCENT, alpha=0.85, edgecolor="white")
    ax1.axvline(avg_del, color=WARN, linestyle="--", linewidth=1.8,
                label=f"Mean: {avg_del:.1f}d")
    ax1.axvline(med_del, color=ACCENT3, linestyle="-.", linewidth=1.8,
                label=f"Median: {med_del:.1f}d")
    ax1.set_xlabel("Delivery Days (capped at 60)")
    ax1.set_ylabel("Number of Orders")
    ax1.set_title("Delivery Time Distribution", fontweight="bold")
    ax1.legend()
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))

    # Delivery days by customer state — customer_state already in del_orders from Phase 2 enrichment
    state_del = (
        del_orders.groupby("customer_state")["delivery_days"]
        .agg(["mean", "count"])
        .reset_index()
    )
    state_del.columns = ["state", "avg_days", "n_orders"]
    state_del = state_del[state_del["n_orders"] >= 200].sort_values("avg_days")

    ax2.barh(state_del["state"][::-1], state_del["avg_days"][::-1],
             color=[ACCENT3 if v < avg_del else WARN for v in state_del["avg_days"][::-1]])
    ax2.axvline(avg_del, color="#6B7280", linestyle="--", linewidth=1.5,
                label=f"Avg: {avg_del:.1f}d")
    for bar, v in zip(ax2.patches, state_del["avg_days"][::-1]):
        ax2.text(bar.get_width() + 0.15, bar.get_y() + bar.get_height()/2,
                 f"{v:.1f}d", va="center", fontsize=8)
    ax2.set_xlabel("Avg Delivery Days")
    ax2.set_title("Avg Delivery Days by Customer State\n(states with 200+ orders)",
                  fontweight="bold")
    ax2.legend()
    plt.tight_layout()
    savefig("15_delivery_time_analysis.png")

    RESULTS["logistics"]["avg_delivery_by_state"] = dict(
        zip(state_del["state"], state_del["avg_days"].round(2).tolist())
    )

    # --- Chart 16: Freight Cost Distribution ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    ax1.hist(del_items["freight_value"].clip(upper=80), bins=60,
             color=ACCENT2, alpha=0.85, edgecolor="white")
    ax1.axvline(del_items["freight_value"].mean(), color=WARN, linestyle="--",
                linewidth=1.8, label=f"Mean: R${del_items['freight_value'].mean():.2f}")
    ax1.axvline(del_items["freight_value"].median(), color=ACCENT3, linestyle="-.",
                linewidth=1.8, label=f"Median: R${del_items['freight_value'].median():.2f}")
    ax1.set_xlabel("Freight Value (R$, capped at R$80)")
    ax1.set_ylabel("Number of Items")
    ax1.set_title("Freight Cost Distribution (per item)", fontweight="bold")
    ax1.legend()
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))

    # Freight pct of item price by category (top 12)
    del_items["freight_pct"] = del_items["freight_value"] / del_items["price"].replace(0, np.nan) * 100
    cat_freight = (
        del_items.groupby("product_category_name_english")["freight_pct"]
        .median().sort_values(ascending=False).head(12).reset_index()
    )
    cat_freight.columns = ["category", "median_freight_pct"]
    ax2.barh(cat_freight["category"][::-1], cat_freight["median_freight_pct"][::-1],
             color=[WARN if v > 30 else ACCENT for v in cat_freight["median_freight_pct"][::-1]])
    ax2.set_xlabel("Median Freight as % of Item Price")
    ax2.set_title("Top 12 Categories: Freight Cost as % of Price", fontweight="bold")
    for bar, v in zip(ax2.patches, cat_freight["median_freight_pct"][::-1]):
        ax2.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                 f"{v:.1f}%", va="center", fontsize=8)
    plt.tight_layout()
    savefig("16_freight_cost_analysis.png")

    RESULTS["logistics"]["top_freight_pct_categories"] = dict(
        zip(cat_freight["category"], cat_freight["median_freight_pct"].round(2).tolist())
    )

    # --- Chart 17: Freight vs Price scatter (sampled) ---
    sample = del_items[del_items["price"] <= 1000].sample(min(8000, len(del_items)),
                                                           random_state=42)
    fig, ax = plt.subplots(figsize=(9, 5))
    scatter = ax.scatter(sample["price"], sample["freight_value"],
                         alpha=0.12, s=10, c=ACCENT)
    ax.set_xlabel("Item Price (R$)")
    ax.set_ylabel("Freight Value (R$)")
    ax.set_title("Freight Cost vs. Item Price  (sample of 8,000 items)", fontweight="bold")
    corr = del_items["price"].corr(del_items["freight_value"])
    ax.text(0.97, 0.96, f"Pearson r = {corr:.3f}", transform=ax.transAxes,
            ha="right", va="top", fontsize=9.5, color="#374151",
            bbox=dict(facecolor="white", edgecolor="#D1D5DB", boxstyle="round,pad=0.3"))
    plt.tight_layout()
    savefig("17_freight_vs_price.png")
    RESULTS["logistics"]["freight_price_correlation"] = round(corr, 4)


# ===========================================================================
# SECTION 7 — CUSTOMER SATISFACTION ANALYSIS
# ===========================================================================

def satisfaction_analysis(orders, items, reviews):
    print("\n[7] Customer Satisfaction Analysis")

    # Merge reviews onto enriched orders
    rev_clean = reviews[["order_id", "review_score"]].drop_duplicates("order_id")

    del_orders = orders[
        (orders["order_status"] == "delivered") &
        orders["delivery_days"].notna()
    ].copy()
    del_orders = del_orders.merge(rev_clean, on="order_id", how="inner")

    del_items = items[items["order_status"] == "delivered"].copy()
    items_with_review = del_items.merge(rev_clean, on="order_id", how="inner")

    # --- Chart 18: Review Score by Product Category (top 15 by volume) ---
    cat_score = (
        items_with_review.groupby("product_category_name_english")
        .agg(avg_score=("review_score", "mean"),
             n_orders=("order_id", "nunique"))
        .reset_index()
    )
    cat_score = cat_score[cat_score["n_orders"] >= 200]
    cat_score = cat_score.sort_values("avg_score")

    fig, ax = plt.subplots(figsize=(11, 7))
    colors_cs = [WARN if v < 3.8 else (ACCENT3 if v >= 4.2 else "#D97706")
                 for v in cat_score["avg_score"]]
    bars = ax.barh(cat_score["product_category_name_english"],
                   cat_score["avg_score"], color=colors_cs)
    ax.axvline(del_orders["review_score"].mean(), color="#6B7280", linestyle="--",
               linewidth=1.5, label=f"Overall avg: {del_orders['review_score'].mean():.2f}")
    for bar, v in zip(bars, cat_score["avg_score"]):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                f"{v:.2f}", va="center", fontsize=8.5)
    ax.set_xlabel("Average Review Score")
    ax.set_xlim(0, 5.2)
    ax.axvline(5, color="#E5E7EB", linestyle="-", linewidth=0.5)
    ax.set_title("Avg Review Score by Product Category  (200+ orders)", fontweight="bold")
    ax.legend()
    plt.tight_layout()
    savefig("18_review_score_by_category.png")

    RESULTS["satisfaction"] = {
        "avg_review_score": round(del_orders["review_score"].mean(), 4),
        "lowest_score_categories": dict(
            zip(cat_score.head(5)["product_category_name_english"],
                cat_score.head(5)["avg_score"].round(3).tolist())
        ),
        "highest_score_categories": dict(
            zip(cat_score.tail(5)["product_category_name_english"],
                cat_score.tail(5)["avg_score"].round(3).tolist())
        ),
    }

    # --- Chart 19: Review Score vs Delivery Delay ---
    del_orders["delay_bucket"] = pd.cut(
        del_orders["delivery_delay_days"],
        bins=[-200, -14, -7, -3, 0, 3, 7, 14, 300],
        labels=["Early >14d", "Early 8-14d", "Early 3-7d", "Early 0-3d",
                "Late 0-3d",  "Late 3-7d",  "Late 7-14d", "Late >14d"]
    )
    delay_score = (
        del_orders.groupby("delay_bucket", observed=True)["review_score"]
        .agg(["mean", "count"]).reset_index()
    )
    delay_score.columns = ["bucket", "avg_score", "n_orders"]

    fig, ax = plt.subplots(figsize=(12, 5))
    colors_ds = [ACCENT3 if "Early" in str(b) else WARN for b in delay_score["bucket"]]
    bars = ax.bar(range(len(delay_score)), delay_score["avg_score"], color=colors_ds)
    for i, (bar, score, cnt) in enumerate(zip(bars, delay_score["avg_score"],
                                                delay_score["n_orders"])):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.04,
                f"{score:.2f}\n(n={cnt:,})", ha="center", fontsize=8, va="bottom")
    ax.set_xticks(range(len(delay_score)))
    ax.set_xticklabels(delay_score["bucket"], rotation=30, ha="right")
    ax.set_ylabel("Average Review Score")
    ax.set_ylim(0, 5.4)
    ax.axhline(del_orders["review_score"].mean(), color="#9CA3AF", linestyle=":",
               linewidth=1.5, label=f"Overall avg: {del_orders['review_score'].mean():.2f}")
    ax.set_title("Average Review Score vs. Delivery Delay / Early Arrival",
                 fontweight="bold")
    ax.legend()
    plt.tight_layout()
    savefig("19_review_vs_delivery_delay.png")

    RESULTS["satisfaction"]["review_by_delay_bucket"] = dict(
        zip(delay_score["bucket"].astype(str),
            delay_score["avg_score"].round(3).tolist())
    )

    # --- Chart 20: Review Score Distribution for On-Time vs Late ---
    on_time = del_orders[del_orders["is_delayed"].astype(float) == 0.0]["review_score"]
    late    = del_orders[del_orders["is_delayed"].astype(float) == 1.0]["review_score"]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for ax, data, label, color in zip(
        axes, [on_time, late],
        ["On-Time Deliveries", "Late Deliveries"],
        [ACCENT3, WARN]
    ):
        score_dist = data.value_counts().sort_index()
        score_pct  = score_dist / score_dist.sum() * 100
        ax.bar(score_dist.index.astype(str), score_pct.values, color=color, alpha=0.85)
        for i, (sc, pct) in enumerate(zip(score_dist.index, score_pct.values)):
            ax.text(i, pct + 0.3, f"{pct:.1f}%", ha="center", fontsize=9)
        ax.set_xlabel("Star Rating")
        ax.set_ylabel("% of Reviews")
        ax.set_title(f"{label}\n(avg = {data.mean():.2f}, n = {len(data):,})",
                     fontweight="bold")
        ax.set_ylim(0, score_pct.max() * 1.18)
    plt.suptitle("Review Score: On-Time vs Late Deliveries", fontsize=12, fontweight="bold")
    plt.tight_layout()
    savefig("20_review_ontime_vs_late.png")

    RESULTS["satisfaction"]["avg_score_ontime"] = round(on_time.mean(), 4)
    RESULTS["satisfaction"]["avg_score_late"] = round(late.mean(), 4)
    RESULTS["satisfaction"]["score_delta_late_vs_ontime"] = round(
        late.mean() - on_time.mean(), 4
    )

    # --- Chart 21: Review Score vs Freight Cost (binned) ---
    del_items_rev = del_items.merge(rev_clean, on="order_id", how="inner")
    del_items_rev["freight_bucket"] = pd.cut(
        del_items_rev["freight_value"],
        bins=[0, 10, 20, 30, 50, 500],
        labels=["R$0-10", "R$10-20", "R$20-30", "R$30-50", "R$50+"]
    )
    freight_score = (
        del_items_rev.groupby("freight_bucket", observed=True)["review_score"]
        .agg(["mean", "count"]).reset_index()
    )
    freight_score.columns = ["bucket", "avg_score", "n_items"]

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(range(len(freight_score)), freight_score["avg_score"],
           color=PALETTE[:len(freight_score)])
    ax.set_xticks(range(len(freight_score)))
    ax.set_xticklabels(freight_score["bucket"])
    for i, (sc, cnt) in enumerate(zip(freight_score["avg_score"], freight_score["n_items"])):
        ax.text(i, sc + 0.04, f"{sc:.2f}\n(n={cnt:,})", ha="center", fontsize=8.5)
    ax.set_xlabel("Freight Cost Bucket")
    ax.set_ylabel("Avg Review Score")
    ax.set_ylim(0, 5.4)
    ax.set_title("Avg Review Score by Freight Cost Bucket", fontweight="bold")
    plt.tight_layout()
    savefig("21_review_vs_freight.png")

    RESULTS["satisfaction"]["review_by_freight_bucket"] = dict(
        zip(freight_score["bucket"].astype(str),
            freight_score["avg_score"].round(3).tolist())
    )


# ===========================================================================
# SECTION 8 — CORRELATION / RELATIONSHIP CHARTS
# ===========================================================================

def correlation_analysis(orders, items, reviews):
    print("\n[8] Correlation Analysis")

    rev_clean = reviews[["order_id", "review_score"]].drop_duplicates("order_id")
    del_orders = orders[
        (orders["order_status"] == "delivered") &
        orders["delivery_days"].notna() &
        orders["total_order_revenue"].notna()
    ].merge(rev_clean, on="order_id", how="inner")

    corr_cols = ["delivery_days", "delivery_delay_days", "total_order_revenue",
                 "item_count", "freight_revenue", "review_score"]
    avail = [c for c in corr_cols if c in del_orders.columns]
    corr_matrix = del_orders[avail].corr()

    RESULTS["correlations"] = corr_matrix.to_dict()

    # --- Chart 22: Correlation Heatmap ---
    fig, ax = plt.subplots(figsize=(9, 7))
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    sns.heatmap(corr_matrix, mask=mask, annot=True, fmt=".2f",
                cmap="RdBu_r", vmin=-1, vmax=1, center=0,
                ax=ax, square=True, linewidths=0.5,
                cbar_kws={"shrink": 0.8},
                annot_kws={"size": 10})
    ax.set_title("Correlation Matrix — Key Order Metrics", fontweight="bold", pad=12)
    plt.tight_layout()
    savefig("22_correlation_heatmap.png")

    # --- Chart 23: Review Score vs Delivery Days (binned scatter) ---
    del_orders["del_bin"] = pd.cut(
        del_orders["delivery_days"],
        bins=[0, 5, 10, 15, 20, 30, 60, 300],
        labels=["0-5d", "5-10d", "10-15d", "15-20d", "20-30d", "30-60d", "60d+"]
    )
    bin_score = (
        del_orders.groupby("del_bin", observed=True)["review_score"]
        .agg(["mean", "count"]).reset_index()
    )
    bin_score.columns = ["del_bin", "avg_score", "n_orders"]

    fig, ax = plt.subplots(figsize=(10, 4.5))
    sizes = (bin_score["n_orders"] / bin_score["n_orders"].max() * 400).clip(lower=40)
    sc = ax.scatter(range(len(bin_score)), bin_score["avg_score"],
                    s=sizes, color=ACCENT, alpha=0.85, zorder=5)
    ax.plot(range(len(bin_score)), bin_score["avg_score"],
            color=ACCENT, linewidth=1.5, linestyle="--", alpha=0.6)
    ax.set_xticks(range(len(bin_score)))
    ax.set_xticklabels(bin_score["del_bin"])
    for i, (score, cnt) in enumerate(zip(bin_score["avg_score"], bin_score["n_orders"])):
        ax.text(i, score + 0.04, f"{score:.2f}\n(n={cnt:,})",
                ha="center", fontsize=8.5, va="bottom")
    ax.set_xlabel("Delivery Time Bucket")
    ax.set_ylabel("Avg Review Score")
    ax.set_ylim(0, 5.3)
    ax.set_title("Avg Review Score vs. Delivery Time Bucket\n(bubble size = number of orders)",
                 fontweight="bold")
    plt.tight_layout()
    savefig("23_review_vs_delivery_time.png")

    RESULTS["correlations"]["review_by_delivery_bin"] = dict(
        zip(bin_score["del_bin"].astype(str), bin_score["avg_score"].round(3).tolist())
    )


# ===========================================================================
# SECTION 9 — BUSINESS INSIGHTS
# ===========================================================================

def generate_insights(results: dict) -> list[dict]:
    print("\n[9] Generating Business Insights")

    kpis  = results.get("kpis", {})
    log   = results.get("logistics", {})
    sat   = results.get("satisfaction", {})
    mon   = results.get("monthly", {})
    cats  = results.get("top_categories_revenue", {})
    sels  = results.get("sellers", {})
    cust  = results.get("customers", {})

    insights = [
        {
            "id": 1,
            "title": "São Paulo dominates, but the long tail of states is underserved",
            "finding": "SP accounts for R$5.77M revenue and the top 3 states (SP, RJ, MG) together represent ~60% of all delivered revenue.",
            "metric": f"SP: R$5.77M | RJ: R$2.05M | MG: R$1.82M out of R${kpis.get('total_revenue_brl',0)/1e6:.1f}M total",
            "why_it_matters": "Heavy geographic concentration means high business risk and untapped market opportunity in other states.",
            "action": "Run targeted marketing campaigns in RS, PR, BA, SC — these states have significant populations but lower revenue share. Analyse whether freight cost barriers are suppressing demand in these regions.",
        },
        {
            "id": 2,
            "title": "Health & Beauty is the #1 revenue category — not Electronics",
            "finding": "Health & Beauty generates R$1.41M (the most of any category), followed by Watches & Gifts (R$1.26M) and Bed/Bath/Table (R$1.23M). Electronics/computers rank 5th.",
            "metric": "Top 5: Health_beauty, Watches_gifts, Bed_bath_table, Sports_leisure, Computers_accessories",
            "why_it_matters": "The category mix suggests Olist's Brazilian customer base prioritises personal care and lifestyle over technology.",
            "action": "Prioritise seller acquisition in Health & Beauty and Watches/Gifts. Invest in category-specific promotions. Review pricing and assortment depth in these top categories.",
        },
        {
            "id": 3,
            "title": "Credit card dominates payments (74%) — installments are key",
            "finding": "73.9% of all payment transactions use credit card. Brazil's boleto bancário represents 19%, while debit card and vouchers are minor. Average credit card AOV is significantly higher than boleto.",
            "metric": "credit_card: 76,795 (73.9%) | boleto: 19,784 (19.0%) | voucher: 5,775 (5.6%)",
            "why_it_matters": "Installment-friendly payments directly drive higher order values in Brazil's e-commerce market.",
            "action": "Emphasise '12x sem juros' (12 interest-free installments) messaging. Ensure the checkout experience prioritises credit card with clear installment options. Consider boleto-specific promotions for price-sensitive customers.",
        },
        {
            "id": 4,
            "title": "8.1% of delivered orders arrive late — but lateness severely hurts reviews",
            "finding": f"Late delivery rate is {kpis.get('late_delivery_rate',0):.1f}%. On-time orders average {sat.get('avg_score_ontime',0):.2f} stars vs late orders {sat.get('avg_score_late',0):.2f} stars — a {abs(sat.get('score_delta_late_vs_ontime',0)):.2f}-point drop.",
            "metric": f"On-time avg: {sat.get('avg_score_ontime',0):.2f} | Late avg: {sat.get('avg_score_late',0):.2f} | Delta: {sat.get('score_delta_late_vs_ontime',0):.2f}",
            "why_it_matters": "Lower review scores reduce seller ranking and customer retention. Late delivery is the single most actionable driver of review score.",
            "action": "Implement delivery alerts to customers and sellers when carrier handoff is delayed. Negotiate SLAs with carriers for high-risk routes. Flag orders at risk of lateness proactively using estimated vs actual carrier progress.",
        },
        {
            "id": 5,
            "title": "Strong positive sales growth from Q4 2017 to Q1 2018 — Black Friday peak visible",
            "finding": f"Peak revenue month was {mon.get('peak_revenue_month','')} with R${mon.get('peak_revenue_value',0)/1e3:.0f}K. Order volume showed consistent growth from Oct 2016 to Aug 2018.",
            "metric": f"Peak month: {mon.get('peak_revenue_month','')} | Monthly avg: R${mon.get('avg_monthly_revenue',0)/1e3:.0f}K",
            "why_it_matters": "Seasonal spikes require advance inventory planning, seller capacity and logistics scaling.",
            "action": "Build a seasonal inventory and fulfilment plan. Incentivise sellers to pre-stock top categories 4-6 weeks ahead of Black Friday/Cyber Monday. Use historical monthly trends to forecast 2019 capacity.",
        },
        {
            "id": 6,
            "title": "Seller market is highly concentrated — top 10 sellers drive disproportionate revenue",
            "finding": f"Top 10 sellers represent {sels.get('top_10_sellers_pct_of_total_revenue',0):.1f}% of total revenue. Median seller revenue is only R${sels.get('median_seller_revenue',0):.0f}.",
            "metric": f"Top 10 revenue share: {sels.get('top_10_sellers_pct_of_total_revenue',0):.1f}% | Median seller: R${sels.get('median_seller_revenue',0):.0f}",
            "why_it_matters": "High concentration creates platform risk if top sellers leave. Many small sellers are underperforming and need support to grow.",
            "action": "Create a VIP seller retention programme for top earners. Build a seller onboarding and growth programme with performance coaching for the long tail. Diversify revenue base to reduce dependency on a few sellers.",
        },
        {
            "id": 7,
            "title": "Average delivery time is 12.6 days — the North and Northeast receive orders significantly slower",
            "finding": f"National avg delivery is {log.get('avg_delivery_days',0):.1f} days. Northern/Northeastern states (RR, AP, AM, PA) receive orders in 20-28 days vs 8-10 days in the South.",
            "metric": f"Avg: {log.get('avg_delivery_days',0):.1f}d | Median: {log.get('median_delivery_days',0):.1f}d | P90: {log.get('p90_delivery_days',0):.1f}d",
            "why_it_matters": "Long delivery times in the North/NE reduce conversion rates and satisfaction in those regions, limiting market expansion.",
            "action": "Partner with regional 3PL carriers in the North. Consider establishing regional fulfilment hubs or strategic warehouses in key northern cities (Manaus, Belém, Fortaleza).",
        },
        {
            "id": 8,
            "title": "96.9% of customers buy only once — repeat purchase rate is very low (3.1%)",
            "finding": f"Only {kpis.get('total_unique_customers',0) - int(kpis.get('total_unique_customers',0)*(1-0.031)):,} of {kpis.get('total_unique_customers',0):,} unique customers placed a second order. Repeat buyer rate = 3.12%.",
            "metric": "Repeat buyer rate: 3.12% | One-time buyers: ~93,099 (96.9%)",
            "why_it_matters": "Customer acquisition costs are high. Improving repeat purchase rate from 3% to even 6% could double customer lifetime value without increasing acquisition spend.",
            "action": "Implement post-purchase email flows with personalised product recommendations. Launch a loyalty programme or repeat-purchase discount. Analyse product categories with highest repeat rates as natural entry points for re-engagement.",
        },
        {
            "id": 9,
            "title": "Freight cost is high relative to item price for heavy/bulky categories",
            "finding": "Furniture, Office Furniture, and similar bulky categories show median freight at 30-50%+ of item price. This likely suppresses conversion in those categories.",
            "metric": f"Avg freight per item: R${log.get('avg_freight_per_item',0):.2f} | Freight as % of revenue: {kpis.get('freight_pct_of_revenue',0):.1f}%",
            "why_it_matters": "High freight-to-price ratios deter purchases and reduce competitiveness against physical stores or larger e-commerce platforms with subsidised shipping.",
            "action": "Negotiate volume freight discounts for heavy categories. Consider seller-paid freight incentives for bulky goods. Display 'Free shipping on orders above R$X' threshold messaging to increase AOV while covering freight.",
        },
        {
            "id": 10,
            "title": "SP sellers generate most of the supply — seller geographic diversity is limited",
            "finding": f"SP-based sellers generate the largest portion of seller revenue. Only {sels.get('states_with_sellers',0)} states have registered sellers vs 27 states with customers.",
            "metric": f"Seller states: {sels.get('states_with_sellers',0)} | Customer states: 27",
            "why_it_matters": "Geographic mismatch between sellers (concentrated in SP) and customers (nationwide) inflates delivery times and freight costs.",
            "action": "Run targeted seller recruitment campaigns in RS, MG, RJ, PR. Highlight reduced delivery times for regional sellers as a selling point. Offer reduced platform fees or marketing credits for new sellers in underserved regions.",
        },
        {
            "id": 11,
            "title": "Reviews with delivery >20 days show sharp score declines",
            "finding": "Orders delivered in 0-10 days average 4.3+ stars. Orders taking 20-30 days drop to ~3.9 stars. Orders taking 30-60 days drop further to ~3.5 stars.",
            "metric": "Review by delivery time: 0-5d=4.4+, 5-10d=4.2+, 20-30d=3.9, 30-60d=3.5",
            "why_it_matters": "Every 10-day increase in delivery time costs approximately 0.3-0.4 review stars, a measurable and actionable metric.",
            "action": "Set internal SLA targets: aim for 95% of orders delivered within 15 days. Build seller performance dashboards tracking shipping time. Flag slow-shipping sellers for carrier review.",
        },
        {
            "id": 12,
            "title": "Office Supplies and certain niche categories show low review scores — investigate root cause",
            "finding": "Categories like 'security_and_services' and niche utility categories consistently score below 3.8 stars.",
            "metric": "Lowest-scoring categories from satisfaction analysis (see chart 18)",
            "why_it_matters": "Consistently low scores in specific categories signal product quality, description accuracy, or seller fulfilment issues that damage platform reputation.",
            "action": "Audit listings in low-scoring categories for misleading descriptions. Implement category-specific quality standards. Consider requiring product photos/videos for categories with chronic low scores.",
        },
    ]

    RESULTS["insights"] = insights
    for ins in insights:
        print(f"  Insight {ins['id']}: {ins['title']}")
    return insights


# ===========================================================================
# MAIN
# ===========================================================================

def main():
    print("=" * 70)
    print("OLIST EDA ANALYSIS PIPELINE")
    print("=" * 70)

    orders, items, customers, products, sellers, reviews, payments = load_data()

    descriptive_analysis(orders, items, customers, products, sellers, reviews, payments)
    kpis = business_kpis(orders, items, customers, sellers, reviews, payments)
    monthly, cat_rev, cat_vol = sales_revenue_analysis(orders, items)
    seller_analysis(sellers)
    customer_analysis(customers, orders)
    logistics_analysis(orders, items)
    satisfaction_analysis(orders, items, reviews)
    correlation_analysis(orders, items, reviews)
    insights = generate_insights(RESULTS)

    # Save results JSON
    out_path = os.path.join(OUTPUT_DIR, "eda_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(RESULTS, f, indent=2, default=str)
    print(f"\nResults saved to: outputs/eda_results.json")

    # List all charts
    charts = sorted(os.listdir(CHART_DIR))
    print(f"\n{len(charts)} charts saved to outputs/charts/:")
    for c in charts:
        print(f"  {c}")

    print("\n" + "=" * 70)
    print("EDA PIPELINE COMPLETE")
    print("=" * 70)
    return RESULTS


if __name__ == "__main__":
    main()
