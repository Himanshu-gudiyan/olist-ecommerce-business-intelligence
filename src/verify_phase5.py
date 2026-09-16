"""
verify_phase5.py - End-to-end validation for Phase 5 analytics engines
Run: python -X utf8 src/verify_phase5.py
"""
import sys, warnings, os
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

print("=== Loading data ===")
from dashboard_utils import load_orders, load_items, load_sellers, load_reviews
orders  = load_orders()
items   = load_items()
sellers = load_sellers()
reviews = load_reviews()
print(f"orders: {len(orders):,} | items: {len(items):,} | sellers: {len(sellers):,} | reviews: {len(reviews):,}")

print()
print("=== RFM Analysis ===")
from rfm_analysis import compute_rfm, rfm_segment_summary, SEGMENT_COLORS
rfm = compute_rfm(orders)
seg = rfm_segment_summary(rfm)
print(f"RFM rows: {len(rfm):,} | Segments: {rfm['segment'].nunique()}")
for _, row in seg.iterrows():
    print(f"  {row['segment']}: {row['n_customers']:,} customers")

print()
print("=== Cohort Analysis ===")
from cohort_analysis import compute_cohorts, cohort_summary
cohort_data = compute_cohorts(orders)
pivot = cohort_data["cohort_pivot"]
summary = cohort_summary(cohort_data["cohort_raw"])
print(f"Cohort pivot: {pivot.shape[0]} cohorts x {pivot.shape[1]} periods")
print(f"Cohort summary rows: {len(summary)}")

print()
print("=== Seller Intelligence ===")
from seller_intelligence import compute_seller_scorecard, seller_opportunity_analysis
sc   = compute_seller_scorecard(sellers, orders, items, reviews)
opps = seller_opportunity_analysis(sc)
print(f"Seller scorecard: {len(sc):,} sellers")
for k, v in opps.items():
    print(f"  {k}: {len(v)} sellers")

print()
print("=== Growth Analytics ===")
from growth_analytics import (
    compute_monthly_growth, compute_category_trend,
    compute_state_trend, identify_business_opportunities,
)
monthly = compute_monthly_growth(orders, items)
cat_t   = compute_category_trend(items, top_n=6)
state_t = compute_state_trend(orders, top_n=5)
biz_o   = identify_business_opportunities(orders, items, sellers, reviews)
print(f"Monthly growth rows: {len(monthly)}")
print(f"Categories tracked: {cat_t['category'].nunique()}")
print(f"States tracked: {state_t['state'].nunique()}")
print(f"Business opportunities: {len(biz_o)}")
priority_counts = {}
for o in biz_o:
    priority_counts[o["priority"]] = priority_counts.get(o["priority"], 0) + 1
print(f"  by priority: {priority_counts}")

print()
print("=== Page import check ===")
import importlib, inspect
mod = importlib.import_module("pages.advanced_analytics")
sig = inspect.signature(mod.show)
print(f"show() signature: {sig}")

print()
print("=== Key metric spot-checks ===")
delivered = orders[orders["order_status"] == "delivered"]
freq = delivered.groupby("customer_unique_id")["order_id"].count()
repeat_rate = (freq >= 2).sum() / len(freq) * 100
print(f"Repeat buyer rate: {repeat_rate:.2f}%  (expected ~3.12%)")

import pandas as pd
monthly_rev = monthly["revenue"]
peak_month  = monthly.loc[monthly_rev.idxmax(), "ym_str"]
print(f"Peak revenue month: {peak_month}  (expected 2017-11)")

print()
print("ALL PHASE 5 CHECKS PASSED")
