from pathlib import Path
import pandas as pd


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = ROOT / "outputs" / "phase7"

KPI_FILE = OUTPUT_DIR / "kpi_summary.csv"
MONTHLY_FILE = OUTPUT_DIR / "monthly_performance.csv"
CATEGORY_FILE = OUTPUT_DIR / "category_performance.csv"
STATE_FILE = OUTPUT_DIR / "state_performance.csv"
PAYMENT_FILE = OUTPUT_DIR / "payment_performance.csv"
INSIGHTS_FILE = OUTPUT_DIR / "business_insights.csv"

REPORT_FILE = OUTPUT_DIR / "phase7_report.md"


# ============================================================
# LOAD DATA
# ============================================================

kpi = pd.read_csv(KPI_FILE)
monthly = pd.read_csv(MONTHLY_FILE)
category = pd.read_csv(CATEGORY_FILE)
state = pd.read_csv(STATE_FILE)
payment = pd.read_csv(PAYMENT_FILE)
insights = pd.read_csv(INSIGHTS_FILE)


# ============================================================
# KPI VALUES
# ============================================================

row = kpi.iloc[0]

delivered_orders = int(row["delivered_orders"])
total_revenue = float(row["total_revenue"])
aov = float(row["average_order_value"])

unique_customers = int(row["unique_customers"])
repeat_customers = int(row["repeat_customers"])
repeat_rate = float(row["repeat_customer_rate"])

avg_delivery = float(row["average_delivery_days"])
avg_estimated = float(row["average_estimated_delivery_days"])
avg_delay = float(row["average_delivery_delay_days"])

delayed_orders = int(row["delayed_orders"])
delayed_rate = float(row["delayed_order_rate"])


# ============================================================
# MONTHLY PERFORMANCE
# ============================================================

monthly["revenue"] = pd.to_numeric(
    monthly["revenue"],
    errors="coerce"
)

monthly["orders"] = pd.to_numeric(
    monthly["orders"],
    errors="coerce"
)

best_month = monthly.loc[
    monthly["revenue"].idxmax()
]

worst_month = monthly.loc[
    monthly["revenue"].idxmin()
]


# ============================================================
# CATEGORY PERFORMANCE
# ============================================================

category["revenue"] = pd.to_numeric(
    category["revenue"],
    errors="coerce"
)

category["orders"] = pd.to_numeric(
    category["orders"],
    errors="coerce"
)

category["items_sold"] = pd.to_numeric(
    category["items_sold"],
    errors="coerce"
)

top_category = category.iloc[0]


# ============================================================
# STATE PERFORMANCE
# ============================================================

state["revenue"] = pd.to_numeric(
    state["revenue"],
    errors="coerce"
)

state["orders"] = pd.to_numeric(
    state["orders"],
    errors="coerce"
)

top_state = state.iloc[0]


# ============================================================
# PAYMENT PERFORMANCE
# ============================================================

payment["payment_value"] = pd.to_numeric(
    payment["payment_value"],
    errors="coerce"
)

payment["orders"] = pd.to_numeric(
    payment["orders"],
    errors="coerce"
)

top_payment = payment.iloc[0]


# ============================================================
# REPORT CONTENT
# ============================================================

report = []

report.append("# Olist E-Commerce Business Intelligence & Analytics")
report.append("")

report.append(
    "> **Phase 7 — Automated Business Intelligence & KPI Reporting**"
)

report.append("")

report.append(
    "This report is automatically generated from the Olist Brazilian "
    "E-Commerce dataset using the project's validated SQLite analytics "
    "database and Python KPI pipeline."
)

report.append("")

report.append("---")
report.append("")


# ============================================================
# 1. EXECUTIVE SUMMARY
# ============================================================

report.append("## 1. Executive Summary")
report.append("")

report.append(
    f"The analysis covers **{delivered_orders:,} delivered orders** "
    f"with total delivered-order revenue of "
    f"**R$ {total_revenue:,.2f}**."
)

report.append("")

report.append(
    f"The average order value was **R$ {aov:,.2f}**, while the "
    f"delivered-order customer analysis represents "
    f"**{unique_customers:,} unique customers**."
)

report.append("")

report.append(
    f"The observed repeat customer rate was **{repeat_rate:.2f}%**, "
    f"with **{repeat_customers:,} repeat customers**."
)

report.append("")

report.append(
    f"Average delivery time was **{avg_delivery:.2f} days**, "
    f"compared with an average estimated delivery time of "
    f"**{avg_estimated:.2f} days**."
)

report.append("")


# ============================================================
# 2. KEY KPIs
# ============================================================

report.append("## 2. Key Business KPIs")
report.append("")

report.append("| KPI | Value |")
report.append("|---|---:|")
report.append(
    f"| Delivered Orders | {delivered_orders:,} |"
)
report.append(
    f"| Total Revenue | R$ {total_revenue:,.2f} |"
)
report.append(
    f"| Average Order Value | R$ {aov:,.2f} |"
)
report.append(
    f"| Unique Customers | {unique_customers:,} |"
)
report.append(
    f"| Repeat Customers | {repeat_customers:,} |"
)
report.append(
    f"| Repeat Customer Rate | {repeat_rate:.2f}% |"
)
report.append(
    f"| Average Delivery Time | {avg_delivery:.2f} days |"
)
report.append(
    f"| Average Estimated Delivery | {avg_estimated:.2f} days |"
)
report.append(
    f"| Average Delivery Difference | {avg_delay:.2f} days |"
)
report.append(
    f"| Delayed Orders | {delayed_orders:,} |"
)
report.append(
    f"| Delayed Order Rate | {delayed_rate:.2f}% |"
)

report.append("")


# ============================================================
# 3. MONTHLY PERFORMANCE
# ============================================================

report.append("## 3. Monthly Performance")
report.append("")

report.append(
    f"### Highest Revenue Month"
)

report.append("")

report.append(
    f"**{best_month['order_year_month']}** generated "
    f"**R$ {best_month['revenue']:,.2f}** from "
    f"**{int(best_month['orders']):,} orders**."
)

report.append("")

report.append(
    f"### Lowest Revenue Month"
)

report.append("")

report.append(
    f"**{worst_month['order_year_month']}** generated "
    f"**R$ {worst_month['revenue']:,.2f}** from "
    f"**{int(worst_month['orders']):,} orders**."
)

report.append("")

report.append("### Monthly Revenue Table")
report.append("")

report.append("| Month | Orders | Revenue | AOV |")
report.append("|---|---:|---:|---:|")

for _, r in monthly.iterrows():

    report.append(
        f"| {r['order_year_month']} "
        f"| {int(r['orders']):,} "
        f"| R$ {r['revenue']:,.2f} "
        f"| R$ {r['average_order_value']:,.2f} |"
    )

report.append("")


# ============================================================
# 4. CATEGORY PERFORMANCE
# ============================================================

report.append("## 4. Product Category Performance")
report.append("")

report.append(
    f"The leading revenue category was "
    f"**{top_category['category']}**, generating "
    f"**R$ {top_category['revenue']:,.2f}**."
)

report.append("")

report.append("| Category | Orders | Items Sold | Revenue |")
report.append("|---|---:|---:|---:|")

for _, r in category.head(20).iterrows():

    report.append(
        f"| {r['category']} "
        f"| {int(r['orders']):,} "
        f"| {int(r['items_sold']):,} "
        f"| R$ {r['revenue']:,.2f} |"
    )

report.append("")


# ============================================================
# 5. GEOGRAPHIC PERFORMANCE
# ============================================================

report.append("## 5. Geographic Performance")
report.append("")

report.append(
    f"The highest-revenue customer state was "
    f"**{top_state['customer_state']}**, generating "
    f"**R$ {top_state['revenue']:,.2f}**."
)

report.append("")

report.append("| State | Orders | Revenue | AOV |")
report.append("|---|---:|---:|---:|")

for _, r in state.iterrows():

    report.append(
        f"| {r['customer_state']} "
        f"| {int(r['orders']):,} "
        f"| R$ {r['revenue']:,.2f} "
        f"| R$ {r['average_order_value']:,.2f} |"
    )

report.append("")


# ============================================================
# 6. PAYMENT BEHAVIOR
# ============================================================

report.append("## 6. Payment Behavior")
report.append("")

report.append(
    f"The leading payment method by payment value was "
    f"**{top_payment['payment_type']}**, representing "
    f"**R$ {top_payment['payment_value']:,.2f}**."
)

report.append("")

report.append("| Payment Method | Orders | Payment Value | Average Payment |")
report.append("|---|---:|---:|---:|")

for _, r in payment.iterrows():

    report.append(
        f"| {r['payment_type']} "
        f"| {int(r['orders']):,} "
        f"| R$ {r['payment_value']:,.2f} "
        f"| R$ {r['average_payment_value']:,.2f} |"
    )

report.append("")


# ============================================================
# 7. DELIVERY PERFORMANCE
# ============================================================

report.append("## 7. Delivery Performance")
report.append("")

report.append(
    f"Average delivery time was **{avg_delivery:.2f} days**."
)

report.append("")

report.append(
    f"Average estimated delivery time was "
    f"**{avg_estimated:.2f} days**."
)

report.append("")

report.append(
    f"The average delivery difference was **{avg_delay:.2f} days**. "
    f"A negative value indicates that orders were delivered earlier "
    f"than the estimated date on average."
)

report.append("")

report.append(
    f"**{delayed_orders:,} orders** were classified as delayed, "
    f"representing a delayed-order rate of **{delayed_rate:.2f}%**."
)

report.append("")


# ============================================================
# 8. CUSTOMER RETENTION
# ============================================================

report.append("## 8. Customer Retention")
report.append("")

report.append(
    f"The delivered-order customer analysis contains "
    f"**{unique_customers:,} unique customers**."
)

report.append("")

report.append(
    f"Among them, **{repeat_customers:,} customers** placed more "
    f"than one delivered order."
)

report.append("")

report.append(
    f"The resulting repeat customer rate is **{repeat_rate:.2f}%**."
)

report.append("")


# ============================================================
# 9. BUSINESS OPPORTUNITIES
# ============================================================

report.append("## 9. Business Opportunities")
report.append("")

report.append(
    "Based on the automated analysis, the following areas can be "
    "considered for further business investigation:"
)

report.append("")

report.append(
    f"1. **Customer retention:** The observed repeat customer rate "
    f"is {repeat_rate:.2f}%, making retention and repeat-purchase "
    f"analysis an important area for further investigation."
)

report.append("")

report.append(
    f"2. **Delivery reliability:** {delayed_rate:.2f}% of delivered "
    f"orders were classified as delayed. Seller, geography and "
    f"product-level delivery patterns can be investigated further."
)

report.append("")

report.append(
    f"3. **Revenue concentration:** {top_category['category']} is "
    f"the leading category by revenue and can be examined for "
    f"category-level growth and assortment opportunities."
)

report.append("")

report.append(
    f"4. **Geographic performance:** {top_state['customer_state']} "
    f"is the highest-revenue customer state and can be evaluated "
    f"for regional demand and logistics patterns."
)

report.append("")

report.append(
    f"5. **Payment behavior:** {top_payment['payment_type']} is the "
    f"leading payment method by payment value and can be considered "
    f"when analysing payment preferences and conversion behaviour."
)

report.append("")


# ============================================================
# 10. ANALYST CONCLUSION
# ============================================================

report.append("## 10. Analyst Conclusion")
report.append("")

report.append(
    "The Olist dataset provides a strong foundation for analysing "
    "e-commerce sales, customers, products, sellers, payments, "
    "geography and delivery performance."
)

report.append("")

report.append(
    f"The validated analytics pipeline identifies "
    f"R$ {total_revenue:,.2f} in delivered-order revenue across "
    f"{delivered_orders:,} delivered orders, with an average order "
    f"value of R$ {aov:,.2f}."
)

report.append("")

report.append(
    "The analysis also highlights customer retention, delivery "
    "reliability, category performance, geographic demand and "
    "payment behaviour as important areas for deeper business "
    "analysis."
)

report.append("")

report.append(
    "All reported metrics in this Phase 7 report are generated "
    "directly from the project's Olist analytics database."
)

report.append("")

report.append("---")
report.append("")

report.append(
    "**Data Source:** Brazilian E-Commerce Public Dataset by Olist"
)

report.append("")

report.append(
    "**Project:** Olist E-Commerce Business Intelligence & Analytics"
)

report.append("")

report.append(
    "**Phase:** 7 — Automated Business Intelligence & KPI Reporting"
)


# ============================================================
# WRITE REPORT
# ============================================================

REPORT_FILE.write_text(
    "\n".join(report),
    encoding="utf-8"
)


# ============================================================
# CONSOLE OUTPUT
# ============================================================

print("=" * 70)
print("PHASE 7 - AUTOMATED REPORT GENERATOR")
print("=" * 70)

print(f"\nReport generated successfully:")
print(REPORT_FILE)

print("\nReport sections:")
print("✓ Executive Summary")
print("✓ Key Business KPIs")
print("✓ Monthly Performance")
print("✓ Product Category Performance")
print("✓ Geographic Performance")
print("✓ Payment Behavior")
print("✓ Delivery Performance")
print("✓ Customer Retention")
print("✓ Business Opportunities")
print("✓ Analyst Conclusion")

print("\n" + "=" * 70)
print("PHASE 7 REPORT GENERATION COMPLETED")
print("=" * 70)