"""
collect_phase5_metrics.py - collect real metrics for eda_report Phase 5 section
"""
import warnings, sys, os
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd

from dashboard_utils import load_orders, load_items, load_sellers, load_reviews
from growth_analytics import compute_monthly_growth, identify_business_opportunities
from rfm_analysis import compute_rfm, rfm_segment_summary
from seller_intelligence import compute_seller_scorecard
from cohort_analysis import compute_cohorts, cohort_summary

orders   = load_orders()
items    = load_items()
sellers  = load_sellers()
reviews  = load_reviews()

monthly  = compute_monthly_growth(orders, items)
rfm      = compute_rfm(orders)
seg      = rfm_segment_summary(rfm)
sc       = compute_seller_scorecard(sellers, orders, items, reviews)
biz      = identify_business_opportunities(orders, items, sellers, reviews)
cohort_d = compute_cohorts(orders)
c_summ   = cohort_summary(cohort_d["cohort_raw"])

delivered  = orders[orders["order_status"] == "delivered"]
del_items  = items[items["order_status"] == "delivered"]

total_rev       = del_items["item_revenue"].sum()
avg_monthly_rev = monthly["revenue"].mean()
peak_month      = monthly.loc[monthly["revenue"].idxmax(), "ym_str"]
peak_rev        = monthly["revenue"].max()
total_growth    = (monthly["revenue"].iloc[-1] - monthly["revenue"].iloc[1]) / monthly["revenue"].iloc[1] * 100

freq        = delivered.groupby("customer_unique_id")["order_id"].count()
repeat_rate = (freq >= 2).sum() / len(freq) * 100
n_customers = len(freq)
n_repeat    = int((freq >= 2).sum())

rev_c      = reviews[["order_id", "review_score"]].drop_duplicates("order_id")
has_delay  = delivered[delivered["is_delayed"].notna()].copy()
has_delay["is_delayed"] = pd.to_numeric(has_delay["is_delayed"], errors="coerce")
rev_del    = has_delay.merge(rev_c, on="order_id", how="inner")
on_time_avg = rev_del[rev_del["is_delayed"] == 0.0]["review_score"].mean()
late_avg    = rev_del[rev_del["is_delayed"] == 1.0]["review_score"].mean()

cat_rev   = del_items.groupby("product_category_name_english")["item_revenue"].sum().sort_values(ascending=False)
top5_cats = cat_rev.head(5)

top5_sellers = sc.nlargest(5, "total_revenue")[
    ["seller_id", "seller_state", "total_revenue", "avg_review_score", "late_rate_pct"]
]

state_del = delivered[delivered["delivery_days"].notna()].groupby("customer_state")["delivery_days"].mean()
fastest   = state_del.idxmin()
slowest   = state_del.idxmax()

print("=== PHASE 5 REAL METRICS ===")
print(f"total_rev:        R${total_rev:,.2f}")
print(f"avg_monthly_rev:  R${avg_monthly_rev:,.2f}")
print(f"peak_month:       {peak_month}  (R${peak_rev:,.2f})")
print(f"total_growth:     {total_growth:.1f}%")
print(f"repeat_rate:      {repeat_rate:.2f}%  ({n_repeat:,} of {n_customers:,})")
print(f"on_time_score:    {on_time_avg:.3f}")
print(f"late_score:       {late_avg:.3f}")
print(f"score_delta:      {abs(on_time_avg - late_avg):.3f}")
print()
print("Top 5 categories by revenue:")
for cat, rev in top5_cats.items():
    pct = rev / total_rev * 100
    print(f"  {cat}: R${rev:,.0f} ({pct:.1f}%)")
print()
print("Top 5 sellers:")
print(top5_sellers.to_string(index=False))
print()
print("Fastest delivery state:", fastest, f"({state_del[fastest]:.1f}d)")
print("Slowest delivery state:", slowest, f"({state_del[slowest]:.1f}d)")
print()
print("RFM Segment Summary:")
print(seg[["segment", "n_customers", "avg_monetary", "total_revenue"]].to_string(index=False))
print()
print("Cohort return rate avg:", c_summ["return_rate_pct"].mean())
print()
print("Business Opportunities:")
for o in biz:
    print(f"  [{o['priority']}] {o['title']}")
    print(f"    metric: {o['metric_value']}")
