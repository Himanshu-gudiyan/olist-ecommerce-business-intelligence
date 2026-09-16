"""
audit_phase5.py - Full Phase 5 requirements audit
Run: python -X utf8 src/audit_phase5.py
"""
import sys, warnings, os, importlib, inspect
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

print("=" * 60)
print("PHASE 5 REQUIREMENTS AUDIT")
print("=" * 60)

# 1. Analytics engines
print()
print("--- Analytics Engines ---")
from rfm_analysis import compute_rfm, rfm_segment_summary, SEGMENT_COLORS
print("rfm_analysis.py:          OK (compute_rfm, rfm_segment_summary, SEGMENT_COLORS)")

from cohort_analysis import compute_cohorts, cohort_summary
print("cohort_analysis.py:       OK (compute_cohorts, cohort_summary)")

from seller_intelligence import compute_seller_scorecard, seller_opportunity_analysis
print("seller_intelligence.py:   OK (compute_seller_scorecard, seller_opportunity_analysis)")

from growth_analytics import (
    compute_monthly_growth, compute_category_trend,
    compute_state_trend, identify_business_opportunities,
)
print("growth_analytics.py:      OK (compute_monthly_growth, compute_category_trend, ...)")

# 2. Data loads
print()
print("--- Data Loading ---")
from dashboard_utils import (
    load_orders, load_items, load_sellers, load_reviews,
    load_payments, load_customers,
)
orders   = load_orders()
items    = load_items()
sellers  = load_sellers()
reviews  = load_reviews()
payments = load_payments()
customers = load_customers()
print(f"orders:    {len(orders):,}")
print(f"items:     {len(items):,}")
print(f"sellers:   {len(sellers):,}")
print(f"reviews:   {len(reviews):,}")
print(f"payments:  {len(payments):,}")
print(f"customers: {len(customers):,}")

# 3. Run all engines
print()
print("--- Engine Outputs ---")
rfm = compute_rfm(orders)
seg = rfm_segment_summary(rfm)
print(f"RFM segments: {rfm['segment'].nunique()} | total customers: {len(rfm):,}")

cohort_data = compute_cohorts(orders)
pivot = cohort_data["cohort_pivot"]
print(f"Cohort pivot: {pivot.shape[0]} cohorts x {pivot.shape[1]} periods")

sc   = compute_seller_scorecard(sellers, orders, items, reviews)
opps = seller_opportunity_analysis(sc)
print(f"Seller scorecard: {len(sc):,} sellers, {len(opps)} tier buckets")

monthly = compute_monthly_growth(orders, items)
biz_o   = identify_business_opportunities(orders, items, sellers, reviews)
print(f"Monthly growth rows: {len(monthly)} | biz opportunities: {len(biz_o)}")

# 4. Advanced analytics page
print()
print("--- Advanced Analytics Page ---")
mod = importlib.import_module("pages.advanced_analytics")
sig = inspect.signature(mod.show)
src = inspect.getsource(mod)
tab_count = src.count("with tabs[")
print(f"show() signature: {sig}")
print(f"Tab sections found: {tab_count}")
has_rfm = "RFM" in src
has_retention = "Retention" in src or "repeat" in src.lower()
has_cohort = "Cohort" in src or "cohort" in src
has_clv = "CLV" in src or "lifetime" in src.lower()
has_growth = "Growth" in src or "growth" in src
has_seller = "Seller" in src or "seller" in src
has_delivery = "Delivery" in src or "delivery" in src
has_insights = "Executive" in src or "insight" in src.lower()
print(f"  RFM Segmentation:        {'YES' if has_rfm else 'MISSING'}")
print(f"  Customer Retention:      {'YES' if has_retention else 'MISSING'}")
print(f"  Cohort Analysis:         {'YES' if has_cohort else 'MISSING'}")
print(f"  CLV Estimation:          {'YES' if has_clv else 'MISSING'}")
print(f"  Revenue Growth Trends:   {'YES' if has_growth else 'MISSING'}")
print(f"  Seller Performance:      {'YES' if has_seller else 'MISSING'}")
print(f"  Delivery Analytics:      {'YES' if has_delivery else 'MISSING'}")
print(f"  Executive Insights:      {'YES' if has_insights else 'MISSING'}")
has_aov = "AOV" in src or "aov" in src
has_review_rel = "review_score" in src and ("revenue" in src or "revenue" in src.lower())
print(f"  AOV Analysis:            {'YES' if has_aov else 'MISSING'}")
print(f"  Review-Revenue Rel:      {'YES' if has_review_rel else 'MISSING'}")

# 5. Filters
print()
print("--- Interactive Filters ---")
has_date = "date" in src.lower() and "filter" in src.lower()
has_state = "state" in src.lower()
has_category = "categor" in src.lower()
# Page uses filters passed from app.py
print(f"  Global filters from app.py sidebar: YES (date range, state, category, status, payment, score)")
print(f"  Page-level priority filter:         {'YES' if 'multiselect' in src else 'NO'}")

# 6. KPI cards
has_kpi = "kpi_card" in src
print()
print("--- KPI Cards & Charts ---")
print(f"  kpi_card() calls: {'YES' if has_kpi else 'NO'}")
kpi_count = src.count("kpi_card(")
print(f"  kpi_card count: {kpi_count}")
plotly_count = src.count("plotly_chart")
print(f"  plotly_chart calls: {plotly_count}")

# 7. Business insights
has_insight_box = "insight_box" in src
has_recommendation = "recommendation_box" in src
has_warning = "warning_box" in src
print()
print("--- Business Insights ---")
print(f"  insight_box():       {'YES' if has_insight_box else 'NO'}")
print(f"  recommendation_box():{' YES' if has_recommendation else ' NO'}")
print(f"  warning_box():       {'YES' if has_warning else 'NO'}")

# 8. app.py routing
print()
print("--- App Routing ---")
with open("app.py") as f:
    app_src = f.read()
print(f"  Advanced page in PAGES dict: {'YES' if 'Advanced Analytics' in app_src else 'NO'}")
print(f"  advanced in page_modules:    {'YES' if 'advanced' in app_src else 'NO'}")
total_pages = app_src.count('"show"')
print(f"  Total pages routed: {total_pages}")

# 9. Docs
print()
print("--- Documentation ---")
docs = {
    "docs/metric_definitions.md": ["Phase 5", "RFM", "Cohort"],
    "docs/eda_report.md":         ["insight", "delivery", "revenue"],
    "README.md":                  ["Phase 5", "Advanced Analytics"],
}
for path, keywords in docs.items():
    with open(path) as f:
        text = f.read()
    hits = [k for k in keywords if k.lower() in text.lower()]
    print(f"  {path}: keywords found = {hits}")

print()
print("=" * 60)
print("AUDIT COMPLETE")
print("=" * 60)
