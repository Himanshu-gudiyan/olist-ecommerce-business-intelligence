from pathlib import Path
import pandas as pd


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

INPUT_DIR = ROOT / "outputs" / "phase7"
OUTPUT_DIR = ROOT / "outputs" / "phase7"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# LOAD GENERATED KPI FILES
# ============================================================

kpi = pd.read_csv(
    INPUT_DIR / "kpi_summary.csv"
)

monthly = pd.read_csv(
    INPUT_DIR / "monthly_performance.csv"
)

category = pd.read_csv(
    INPUT_DIR / "category_performance.csv"
)

state = pd.read_csv(
    INPUT_DIR / "state_performance.csv"
)

payment = pd.read_csv(
    INPUT_DIR / "payment_performance.csv"
)


# ============================================================
# INSIGHT STORAGE
# ============================================================

insights = []


def add_insight(
    category_name,
    metric,
    value,
    observation,
    business_meaning
):
    insights.append({
        "category": category_name,
        "metric": metric,
        "value": value,
        "observation": observation,
        "business_meaning": business_meaning
    })


# ============================================================
# KPI VALUES
# ============================================================

delivered_orders = int(
    kpi.loc[0, "delivered_orders"]
)

total_revenue = float(
    kpi.loc[0, "total_revenue"]
)

average_order_value = float(
    kpi.loc[0, "average_order_value"]
)

unique_customers = int(
    kpi.loc[0, "unique_customers"]
)

repeat_customers = int(
    kpi.loc[0, "repeat_customers"]
)

repeat_rate = float(
    kpi.loc[0, "repeat_customer_rate"]
)

avg_delivery_days = float(
    kpi.loc[0, "average_delivery_days"]
)

avg_estimated_delivery_days = float(
    kpi.loc[0, "average_estimated_delivery_days"]
)

avg_delay_days = float(
    kpi.loc[0, "average_delivery_delay_days"]
)

delayed_orders = int(
    kpi.loc[0, "delayed_orders"]
)

delayed_rate = float(
    kpi.loc[0, "delayed_order_rate"]
)


# ============================================================
# 1. OVERALL BUSINESS PERFORMANCE
# ============================================================

add_insight(
    "Overall Performance",
    "Delivered Orders",
    delivered_orders,
    f"{delivered_orders:,} orders were delivered.",
    "This represents the completed-order volume used for the primary revenue analysis."
)

add_insight(
    "Overall Performance",
    "Total Revenue",
    f"R$ {total_revenue:,.2f}",
    f"Delivered-order revenue reached R$ {total_revenue:,.2f}.",
    "This is the primary revenue KPI for the project."
)

add_insight(
    "Overall Performance",
    "Average Order Value",
    f"R$ {average_order_value:,.2f}",
    f"The average delivered order generated R$ {average_order_value:,.2f}.",
    "AOV can be used as a baseline for evaluating basket-size and revenue-growth strategies."
)


# ============================================================
# 2. CUSTOMER INSIGHTS
# ============================================================

add_insight(
    "Customer",
    "Unique Customers",
    unique_customers,
    f"{unique_customers:,} unique customers are represented in delivered-order analytics.",
    "This is the customer base used for delivered-order customer analysis."
)

add_insight(
    "Customer",
    "Repeat Customers",
    repeat_customers,
    f"{repeat_customers:,} customers placed more than one delivered order.",
    "Repeat customers represent the currently observed returning-customer segment."
)

add_insight(
    "Customer",
    "Repeat Customer Rate",
    f"{repeat_rate:.2f}%",
    f"The repeat customer rate is {repeat_rate:.2f}%.",
    "Customer retention is an important opportunity area because repeat purchasing is relatively limited in the observed data."
)


# ============================================================
# 3. DELIVERY INSIGHTS
# ============================================================

add_insight(
    "Delivery",
    "Average Delivery Time",
    f"{avg_delivery_days:.2f} days",
    f"Average delivery time was {avg_delivery_days:.2f} days.",
    "This provides the baseline for evaluating logistics performance."
)

add_insight(
    "Delivery",
    "Estimated Delivery Time",
    f"{avg_estimated_delivery_days:.2f} days",
    f"The average estimated delivery time was {avg_estimated_delivery_days:.2f} days.",
    "Comparing actual and estimated delivery helps evaluate delivery reliability."
)

add_insight(
    "Delivery",
    "Average Delivery Difference",
    f"{avg_delay_days:.2f} days",
    f"Average delivery difference was {avg_delay_days:.2f} days.",
    "A negative value indicates that delivered orders were completed earlier than the estimated delivery date on average."
)

add_insight(
    "Delivery",
    "Delayed Order Rate",
    f"{delayed_rate:.2f}%",
    f"{delayed_orders:,} delivered orders were classified as delayed, representing {delayed_rate:.2f}%.",
    "Delayed orders identify the portion of completed orders that exceeded the estimated delivery date."
)


# ============================================================
# 4. MONTHLY PERFORMANCE
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


add_insight(
    "Monthly Performance",
    "Highest Revenue Month",
    best_month["order_year_month"],
    (
        f"{best_month['order_year_month']} generated "
        f"R$ {best_month['revenue']:,.2f} revenue "
        f"from {int(best_month['orders']):,} orders."
    ),
    "This is the strongest monthly revenue period in the delivered-order dataset."
)

add_insight(
    "Monthly Performance",
    "Lowest Revenue Month",
    worst_month["order_year_month"],
    (
        f"{worst_month['order_year_month']} generated "
        f"R$ {worst_month['revenue']:,.2f} revenue "
        f"from {int(worst_month['orders']):,} orders."
    ),
    "This period had the lowest observed monthly delivered-order revenue."
)


# ============================================================
# 5. CATEGORY INSIGHTS
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

add_insight(
    "Product Category",
    "Top Revenue Category",
    top_category["category"],
    (
        f"{top_category['category']} generated "
        f"R$ {top_category['revenue']:,.2f} revenue "
        f"across {int(top_category['orders']):,} orders."
    ),
    "This category is the leading revenue contributor in the category-level analysis."
)


# ============================================================
# 6. STATE INSIGHTS
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

add_insight(
    "Geography",
    "Top Customer State",
    top_state["customer_state"],
    (
        f"{top_state['customer_state']} generated "
        f"R$ {top_state['revenue']:,.2f} revenue "
        f"from {int(top_state['orders']):,} delivered orders."
    ),
    "This state is the largest revenue contributor in the customer-state analysis."
)


# ============================================================
# 7. PAYMENT INSIGHTS
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

add_insight(
    "Payment",
    "Top Payment Method by Value",
    top_payment["payment_type"],
    (
        f"{top_payment['payment_type']} accounted for "
        f"R$ {top_payment['payment_value']:,.2f} "
        f"across {int(top_payment['orders']):,} delivered orders."
    ),
    "This is the leading payment method by payment value in the delivered-order dataset."
)


# ============================================================
# 8. SAVE INSIGHTS
# ============================================================

insights_df = pd.DataFrame(
    insights
)

output_path = OUTPUT_DIR / "business_insights.csv"

insights_df.to_csv(
    output_path,
    index=False
)


# ============================================================
# PRINT RESULTS
# ============================================================

print("=" * 70)
print("PHASE 7 - AUTOMATED BUSINESS INSIGHTS")
print("=" * 70)

print("\nGenerated Business Insights")
print("-" * 70)

for _, row in insights_df.iterrows():

    print(f"\n[{row['category']}]")
    print(f"Metric       : {row['metric']}")
    print(f"Value        : {row['value']}")
    print(f"Observation  : {row['observation']}")
    print(f"Business Use : {row['business_meaning']}")


print("\n" + "=" * 70)
print("OUTPUT")
print("=" * 70)

print(f"Business insights saved to:")
print(output_path)

print("\n" + "=" * 70)
print("PHASE 7 INSIGHTS ENGINE COMPLETED")
print("=" * 70)