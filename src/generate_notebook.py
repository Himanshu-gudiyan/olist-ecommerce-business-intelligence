"""Generate notebooks/01_eda.ipynb"""
import nbformat as nbf
import os

nb = nbf.v4.new_notebook()
nb.metadata['kernelspec'] = {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}
nb.metadata['language_info'] = {'name': 'python', 'version': '3.10.0'}

def md(src): return nbf.v4.new_markdown_cell(src)
def code(src): return nbf.v4.new_code_cell(src)

cells = []

cells.append(md("""# Olist E-Commerce Business Intelligence & Analytics
## Exploratory Data Analysis Notebook

**Dataset:** Real Olist Brazilian E-Commerce Public Dataset  
**Phase:** 3 — Advanced EDA & Business Insights  
**Data source:** `data/processed/` (cleaned in Phase 2)

### Table of Contents
1. Setup & Data Loading
2. Descriptive Analysis
3. Business KPIs
4. Sales & Revenue Analysis
5. Customer Analysis
6. Logistics & Delivery Analysis
7. Customer Satisfaction Analysis
8. Correlation Analysis
9. Business Insights Summary
"""))

cells.append(md("## 1. Setup & Data Loading"))
cells.append(code("""import os, sys, json, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

warnings.filterwarnings("ignore")
ROOT = os.path.abspath("..")
sys.path.insert(0, ROOT)
PROC_DIR  = os.path.join(ROOT, "data", "processed")
CHART_DIR = os.path.join(ROOT, "outputs", "charts")

sns.set_theme(style="whitegrid", palette="muted", font_scale=1.05)
plt.rcParams.update({"figure.dpi": 100, "figure.facecolor": "white",
                     "axes.spines.top": False, "axes.spines.right": False})

ACCENT, ACCENT2, ACCENT3, WARN = "#2563EB", "#7C3AED", "#059669", "#DC2626"
PALETTE = ["#2563EB","#7C3AED","#059669","#D97706","#DC2626",
           "#0891B2","#BE185D","#4B5563","#CA8A04","#0D9488"]
print("Setup complete.")
"""))

cells.append(code("""def read(f): return pd.read_csv(os.path.join(PROC_DIR, f), low_memory=False)

orders    = read("orders_enriched.csv")
items     = read("order_items_enriched.csv")
customers = read("customer_analytics.csv")
products  = read("product_analytics.csv")
sellers   = read("seller_analytics.csv")
reviews   = read("order_reviews_clean.csv")
payments  = read("order_payments_clean.csv")

for col in ["order_purchase_timestamp","order_delivered_customer_date",
            "order_estimated_delivery_date","order_approved_at"]:
    if col in orders.columns:
        orders[col] = pd.to_datetime(orders[col], errors="coerce")

delivered = orders[orders["order_status"] == "delivered"]
del_items = items[items["order_status"] == "delivered"].copy()

print(f"orders:    {len(orders):,} rows x {orders.shape[1]} cols")
print(f"items:     {len(items):,} rows x {items.shape[1]} cols")
print(f"customers: {len(customers):,} rows x {customers.shape[1]} cols")
print(f"reviews:   {len(reviews):,} rows x {reviews.shape[1]} cols")
print(f"payments:  {len(payments):,} rows x {payments.shape[1]} cols")
"""))

cells.append(md("## 2. Descriptive Analysis"))
cells.append(code("""print("=== DATASET OVERVIEW ===")
print(f"Total Orders:          {len(orders):,}")
print(f"Delivered Orders:      {len(delivered):,}  ({len(delivered)/len(orders)*100:.1f}%)")
print(f"Cancelled Orders:      {(orders['order_status']=='canceled').sum():,}")
print(f"Unique Customers:      {customers['customer_unique_id'].nunique():,}")
repeat = int(customers['is_repeat_buyer'].sum())
print(f"Repeat Buyers:         {repeat:,}  ({customers['is_repeat_buyer'].mean()*100:.2f}%)")
print(f"Active Sellers:        {len(sellers):,}")
d_min = orders['order_purchase_timestamp'].min()
d_max = orders['order_purchase_timestamp'].max()
print(f"Date Range:            {d_min.date()} to {d_max.date()} ({(d_max-d_min).days} days)")
"""))

cells.append(code("""# Order Status Distribution
status = orders["order_status"].value_counts().sort_values(ascending=True)
fig, ax = plt.subplots(figsize=(9, 4))
ax.barh(status.index, status.values,
        color=[ACCENT if s=="delivered" else "#94A3B8" for s in status.index])
ax.set_xlabel("Number of Orders")
ax.set_title(f"Order Status Distribution  (n={len(orders):,})", fontweight="bold")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_: f"{int(x):,}"))
for bar, v in zip(ax.patches, status.values):
    ax.text(bar.get_width()+200, bar.get_y()+bar.get_height()/2,
            f"{v:,} ({v/len(orders)*100:.1f}%)", va="center", fontsize=9)
ax.set_xlim(0, status.max()*1.22)
plt.tight_layout(); plt.show()
"""))

cells.append(code("""# Payment Type Distribution
pay_cnt = payments["payment_type"].value_counts()
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
ax1.bar(pay_cnt.index, pay_cnt.values, color=PALETTE[:len(pay_cnt)])
ax1.set_title("Payment Type — Count", fontweight="bold")
for i, v in enumerate(pay_cnt.values):
    pct = v / pay_cnt.sum() * 100
    ax1.text(i, v+300, f"{v:,}\\n({pct:.1f}%)", ha="center", fontsize=8.5)
ax1.set_xticklabels(pay_cnt.index, rotation=20)
avg_pay = payments.groupby("payment_type")["payment_value"].mean().reindex(pay_cnt.index)
ax2.bar(avg_pay.index, avg_pay.values, color=PALETTE[:len(avg_pay)])
ax2.set_title("Avg Payment Value (R$)", fontweight="bold")
for i, v in enumerate(avg_pay.values):
    ax2.text(i, v+2, f"R${v:.0f}", ha="center", fontsize=8.5)
ax2.set_xticklabels(avg_pay.index, rotation=20)
plt.suptitle("Payment Method Analysis", fontweight="bold")
plt.tight_layout(); plt.show()
"""))

cells.append(code("""# Review Score Distribution
score_cnt = reviews["review_score"].value_counts().sort_index()
colors_sc = [WARN, "#F97316", "#EAB308", ACCENT3, ACCENT]
fig, ax = plt.subplots(figsize=(8, 4))
bars = ax.bar(score_cnt.index.astype(str), score_cnt.values, color=colors_sc)
for bar, cnt in zip(bars, score_cnt.values):
    pct = cnt / score_cnt.sum() * 100
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+300,
            f"{cnt:,}\\n({pct:.1f}%)", ha="center", fontsize=9)
ax.set_xlabel("Star Rating"); ax.set_ylabel("Number of Reviews")
avg_sc = reviews["review_score"].mean()
ax.set_title(f"Review Score Distribution  (avg={avg_sc:.2f}/5.0)", fontweight="bold")
plt.tight_layout(); plt.show()
"""))

cells.append(md("## 3. Business KPIs"))
cells.append(code("""total_rev   = del_items["item_revenue"].sum()
prod_rev    = del_items["price"].sum()
freight_rev = del_items["freight_value"].sum()
aov         = delivered["total_order_revenue"].mean()
avg_items   = delivered["item_count"].mean()
avg_freight = del_items["freight_value"].mean()
cancel_rate = (orders["order_status"]=="canceled").sum() / len(orders) * 100
repeat_rate = customers["is_repeat_buyer"].mean() * 100
avg_review  = reviews["review_score"].mean()

has_del   = delivered[delivered["delivery_days"].notna()]
avg_del   = has_del["delivery_days"].mean()
has_delay = has_del[has_del["is_delayed"].notna()]
late_rate = (has_delay["is_delayed"].astype(float) == 1.0).mean() * 100
late_ord  = has_delay[has_delay["is_delayed"].astype(float) == 1.0]
avg_late  = late_ord["delivery_delay_days"].mean()

kpis = {
    "Total Orders":                 f"{len(orders):,}",
    "Delivered Orders":             f"{len(delivered):,}  ({len(delivered)/len(orders)*100:.1f}%)",
    "Total Revenue (delivered)":    f"R${total_rev:,.2f}",
    "Product Revenue":              f"R${prod_rev:,.2f}  ({prod_rev/total_rev*100:.1f}%)",
    "Freight Revenue":              f"R${freight_rev:,.2f}  ({freight_rev/total_rev*100:.1f}%)",
    "Avg Order Value":              f"R${aov:.2f}",
    "Avg Items per Order":          f"{avg_items:.3f}",
    "Avg Freight per Item":         f"R${avg_freight:.2f}",
    "Cancellation Rate":            f"{cancel_rate:.2f}%",
    "Repeat Buyer Rate":            f"{repeat_rate:.2f}%",
    "Avg Review Score":             f"{avg_review:.4f} / 5.0",
    "Avg Delivery Days":            f"{avg_del:.2f}",
    "On-Time Delivery Rate":        f"{100-late_rate:.2f}%",
    "Late Delivery Rate":           f"{late_rate:.2f}%",
    "Avg Delay When Late (days)":   f"{avg_late:.2f}",
    "Unique Customers":             f"{customers['customer_unique_id'].nunique():,}",
    "Active Sellers":               f"{len(sellers):,}",
}
kpi_df = pd.DataFrame(list(kpis.items()), columns=["KPI", "Value"]).set_index("KPI")
display(kpi_df)
"""))

cells.append(md("## 4. Sales & Revenue Analysis"))
cells.append(code("""del_items["order_purchase_timestamp"] = pd.to_datetime(
    del_items["order_purchase_timestamp"], errors="coerce")
del_items["ym"] = del_items["order_purchase_timestamp"].dt.to_period("M")

monthly_rev = del_items.groupby("ym")["item_revenue"].sum().reset_index()
monthly_rev.columns = ["ym", "revenue"]

delivered2 = delivered.copy()
delivered2["order_purchase_timestamp"] = pd.to_datetime(
    delivered2["order_purchase_timestamp"], errors="coerce")
delivered2["ym"] = delivered2["order_purchase_timestamp"].dt.to_period("M")
monthly_cnt = delivered2.groupby("ym")["order_id"].count().reset_index()
monthly_cnt.columns = ["ym", "n_orders"]

monthly = monthly_rev.merge(monthly_cnt, on="ym").sort_values("ym")
monthly["ym_str"] = monthly["ym"].astype(str)
monthly = monthly[(monthly["ym_str"] >= "2016-10") & (monthly["ym_str"] <= "2018-08")]
x = range(len(monthly))

fig, ax1 = plt.subplots(figsize=(14,5))
ax2 = ax1.twinx()
ax1.fill_between(x, monthly["revenue"], alpha=0.2, color=ACCENT)
ax1.plot(x, monthly["revenue"], color=ACCENT, linewidth=2.5, marker="o", markersize=4)
ax2.plot(x, monthly["n_orders"], color=ACCENT3, linewidth=2, linestyle="--",
         marker="s", markersize=4)
ax1.set_xticks(list(x))
ax1.set_xticklabels(monthly["ym_str"].tolist(), rotation=45, ha="right", fontsize=8)
ax1.set_ylabel("Monthly Revenue (R$)", color=ACCENT, fontweight="bold")
ax2.set_ylabel("Number of Orders", color=ACCENT3, fontweight="bold")
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"R${v/1e3:.0f}K"))
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"{int(v):,}"))
ax1.set_title("Monthly Revenue & Order Volume Trend  (Oct 2016 – Aug 2018)",
              fontweight="bold", fontsize=12)
lines1 = plt.Line2D([0],[0], color=ACCENT, marker="o", label="Revenue (R$)")
lines2 = plt.Line2D([0],[0], color=ACCENT3, linestyle="--", marker="s", label="Orders")
ax1.legend(handles=[lines1, lines2], loc="upper left")
plt.tight_layout(); plt.show()

peak_idx = monthly["revenue"].idxmax()
print(f"Peak revenue month: {monthly.loc[peak_idx,'ym_str']}  ->  R${monthly.loc[peak_idx,'revenue']:,.0f}")
print(f"Avg monthly revenue: R${monthly['revenue'].mean():,.0f}")
"""))

cells.append(code("""# Top 15 Categories by Revenue
cat_rev = (del_items.groupby("product_category_name_english")["item_revenue"]
           .sum().sort_values(ascending=False).head(15).reset_index())
cat_rev.columns = ["category", "revenue"]

fig, ax = plt.subplots(figsize=(11,6))
ax.barh(cat_rev["category"][::-1], cat_rev["revenue"][::-1],
        color=[ACCENT if i < 5 else "#93C5FD" for i in range(14,-1,-1)])
for bar in ax.patches:
    ax.text(bar.get_width()+3000, bar.get_y()+bar.get_height()/2,
            f"R${bar.get_width()/1e3:.0f}K", va="center", fontsize=8.5)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"R${v/1e3:.0f}K"))
ax.set_xlabel("Total Revenue (R$)")
ax.set_title("Top 15 Product Categories by Revenue  (delivered orders)", fontweight="bold")
ax.set_xlim(0, cat_rev["revenue"].max()*1.18)
plt.tight_layout(); plt.show()
cat_rev
"""))

cells.append(code("""# Top 15 Sellers by Revenue
top_sel = sellers.sort_values("total_revenue", ascending=False).head(15)
labels  = ["Seller " + s[:6] + "..." for s in top_sel["seller_id"]]
fig, ax = plt.subplots(figsize=(11,6))
ax.barh(labels[::-1], top_sel["total_revenue"].values[::-1], color=ACCENT)
for bar, state in zip(ax.patches, top_sel["seller_state"].values[::-1]):
    ax.text(bar.get_width()+500, bar.get_y()+bar.get_height()/2,
            f"R${bar.get_width()/1e3:.0f}K  ({state})", va="center", fontsize=8.5)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"R${v/1e3:.0f}K"))
ax.set_xlabel("Total Revenue (R$)")
ax.set_title("Top 15 Sellers by Revenue  (delivered orders)", fontweight="bold")
ax.set_xlim(0, top_sel["total_revenue"].max()*1.28)
plt.tight_layout(); plt.show()
"""))

cells.append(md("## 5. Customer Analysis"))
cells.append(code("""cust_state = (customers.groupby("customer_state")
              .agg(n_customers=("customer_unique_id","count"),
                   avg_spend=("total_spend_payment","mean"))
              .reset_index().sort_values("n_customers", ascending=False))
rev_state = (delivered.groupby("customer_state")["total_order_revenue"]
             .sum().reset_index())
state_m = cust_state.merge(rev_state, on="customer_state", how="left").head(15)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15,5))
ax1.barh(state_m["customer_state"][::-1], state_m["n_customers"][::-1], color=ACCENT)
ax1.set_xlabel("Unique Customers"); ax1.set_title("Customers by State", fontweight="bold")
ax1.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"{int(v):,}"))
ax2.barh(state_m["customer_state"][::-1], state_m["total_order_revenue"][::-1], color=ACCENT3)
ax2.set_xlabel("Revenue (R$)"); ax2.set_title("Revenue by Customer State", fontweight="bold")
ax2.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"R${v/1e6:.1f}M"))
plt.suptitle("Geographic Customer Distribution", fontsize=13, fontweight="bold")
plt.tight_layout(); plt.show()
state_m[["customer_state","n_customers","total_order_revenue","avg_spend"]].head(10)
"""))

cells.append(code("""# Customer Segmentation
def segment(row):
    if row["total_orders"] >= 3:         return "High-Frequency (3+ orders)"
    elif row["total_orders"] == 2:       return "Returning (2 orders)"
    elif row["total_spend_payment"] >= 500: return "High-Value (1 order, R$500+)"
    else:                                return "Single-Purchase (<R$500)"

customers["segment"] = customers.apply(segment, axis=1)
seg_s = (customers.groupby("segment")
         .agg(n_customers=("customer_unique_id","count"),
              avg_spend=("total_spend_payment","mean"),
              avg_orders=("total_orders","mean"))
         .reset_index().sort_values("n_customers", ascending=False))
display(seg_s)
"""))

cells.append(md("## 6. Logistics & Delivery Analysis"))
cells.append(code("""del_ord = orders[(orders["order_status"]=="delivered") &
                   orders["delivery_days"].notna()].copy()

print(f"Avg delivery days:     {del_ord['delivery_days'].mean():.2f}")
print(f"Median delivery days:  {del_ord['delivery_days'].median():.2f}")
print(f"P90 delivery days:     {del_ord['delivery_days'].quantile(0.90):.2f}")
has_delay = del_ord[del_ord["is_delayed"].notna()]
lr = (has_delay["is_delayed"].astype(float)==1.0).mean()*100
print(f"Late delivery rate:    {lr:.2f}%")
late_d = has_delay[has_delay["is_delayed"].astype(float)==1.0]
print(f"Avg delay when late:   {late_d['delivery_delay_days'].mean():.2f} days")
"""))

cells.append(code("""fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14,5))
ax1.hist(del_ord["delivery_days"].clip(upper=60), bins=50,
         color=ACCENT, alpha=0.85, edgecolor="white")
ax1.axvline(del_ord["delivery_days"].mean(), color=WARN, linestyle="--", linewidth=1.8,
            label=f"Mean: {del_ord['delivery_days'].mean():.1f}d")
ax1.axvline(del_ord["delivery_days"].median(), color=ACCENT3, linestyle="-.", linewidth=1.8,
            label=f"Median: {del_ord['delivery_days'].median():.1f}d")
ax1.set_xlabel("Delivery Days (capped 60)"); ax1.set_ylabel("Orders")
ax1.set_title("Delivery Time Distribution", fontweight="bold"); ax1.legend()
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v,_: f"{int(v):,}"))

state_del = (del_ord.groupby("customer_state")["delivery_days"]
             .agg(["mean","count"]).reset_index())
state_del.columns = ["state","avg_days","n_orders"]
state_del = state_del[state_del["n_orders"]>=200].sort_values("avg_days")
avg_all = del_ord["delivery_days"].mean()
ax2.barh(state_del["state"][::-1], state_del["avg_days"][::-1],
         color=[ACCENT3 if v<avg_all else WARN for v in state_del["avg_days"][::-1]])
ax2.axvline(avg_all, color="#6B7280", linestyle="--", linewidth=1.5,
            label=f"Avg: {avg_all:.1f}d")
for bar, v in zip(ax2.patches, state_del["avg_days"][::-1]):
    ax2.text(bar.get_width()+0.15, bar.get_y()+bar.get_height()/2, f"{v:.1f}d",
             va="center", fontsize=8.5)
ax2.set_xlabel("Avg Delivery Days")
ax2.set_title("Delivery Days by Customer State", fontweight="bold"); ax2.legend()
plt.tight_layout(); plt.show()
"""))

cells.append(md("## 7. Customer Satisfaction Analysis"))
cells.append(code("""rev_c = reviews[["order_id","review_score"]].drop_duplicates("order_id")
del_items_rev = del_items.merge(rev_c, on="order_id", how="inner")
del_ord_rev   = del_ord.merge(rev_c, on="order_id", how="inner")

cat_score = (del_items_rev.groupby("product_category_name_english")
             .agg(avg_score=("review_score","mean"),
                  n_orders=("order_id","nunique"))
             .reset_index())
cat_score = cat_score[cat_score["n_orders"]>=200].sort_values("avg_score")
overall_avg = del_ord_rev["review_score"].mean()

fig, ax = plt.subplots(figsize=(11,7))
ax.barh(cat_score["product_category_name_english"], cat_score["avg_score"],
        color=[WARN if v<3.8 else (ACCENT3 if v>=4.2 else "#D97706")
               for v in cat_score["avg_score"]])
ax.axvline(overall_avg, color="#6B7280", linestyle="--", linewidth=1.5,
           label=f"Overall avg: {overall_avg:.2f}")
ax.set_xlabel("Avg Review Score"); ax.set_xlim(0, 5.2)
ax.set_title("Review Score by Product Category (200+ orders)", fontweight="bold")
ax.legend(); plt.tight_layout(); plt.show()

print("Lowest 5 categories:")
print(cat_score.head(5)[["product_category_name_english","avg_score","n_orders"]].to_string())
print("\\nHighest 5 categories:")
print(cat_score.tail(5)[["product_category_name_english","avg_score","n_orders"]].to_string())
"""))

cells.append(code("""on_time_sc = del_ord_rev[del_ord_rev["is_delayed"].astype(float)==0.0]["review_score"]
late_sc    = del_ord_rev[del_ord_rev["is_delayed"].astype(float)==1.0]["review_score"]

fig, axes = plt.subplots(1, 2, figsize=(13,5))
for ax, data, label, color in zip(axes,
    [on_time_sc, late_sc],
    ["On-Time Deliveries", "Late Deliveries"],
    [ACCENT3, WARN]):
    sc_d = data.value_counts().sort_index()
    sc_p = sc_d / sc_d.sum() * 100
    ax.bar(sc_d.index.astype(str), sc_p.values, color=color, alpha=0.85)
    for i, p in enumerate(sc_p.values):
        ax.text(i, p+0.3, f"{p:.1f}%", ha="center", fontsize=9)
    ax.set_xlabel("Star Rating"); ax.set_ylabel("% of Reviews")
    ax.set_title(f"{label}\\n(avg={data.mean():.2f}, n={len(data):,})", fontweight="bold")
plt.suptitle("Review Score: On-Time vs Late Deliveries", fontsize=12, fontweight="bold")
plt.tight_layout(); plt.show()

delta = late_sc.mean() - on_time_sc.mean()
print(f"On-time avg score: {on_time_sc.mean():.4f}")
print(f"Late avg score:    {late_sc.mean():.4f}")
print(f"Delta (late - on-time): {delta:.4f} stars")
"""))

cells.append(md("## 8. Correlation Analysis"))
cells.append(code("""rev_c2 = reviews[["order_id","review_score"]].drop_duplicates("order_id")
del_ord2 = orders[(orders["order_status"]=="delivered") &
                  orders["delivery_days"].notna() &
                  orders["total_order_revenue"].notna()].merge(rev_c2, on="order_id", how="inner")

corr_cols = ["delivery_days","delivery_delay_days","total_order_revenue",
             "item_count","freight_revenue","review_score"]
avail = [c for c in corr_cols if c in del_ord2.columns]
corr_m = del_ord2[avail].corr()

fig, ax = plt.subplots(figsize=(9,7))
mask = np.triu(np.ones_like(corr_m, dtype=bool))
sns.heatmap(corr_m, mask=mask, annot=True, fmt=".2f",
            cmap="RdBu_r", vmin=-1, vmax=1, center=0,
            ax=ax, square=True, linewidths=0.5, annot_kws={"size":10})
ax.set_title("Correlation Matrix — Key Order Metrics", fontweight="bold", pad=12)
plt.tight_layout(); plt.show()

print("Key correlations with review_score:")
print(corr_m["review_score"].sort_values().to_string())
"""))

cells.append(md("## 9. Business Insights Summary"))
cells.append(code("""results_path = os.path.join(ROOT, "outputs", "eda_results.json")
with open(results_path) as f:
    eda_results = json.load(f)

for ins in eda_results.get("insights", []):
    print(f"--- Insight {ins['id']}: {ins['title']} ---")
    print(f"  Finding:        {ins['finding']}")
    print(f"  Metric:         {ins['metric']}")
    print(f"  Why it matters: {ins['why_it_matters']}")
    print(f"  Action:         {ins['action']}")
    print()
"""))

cells.append(md("""---

## Chart Gallery

All 22 charts are saved in `outputs/charts/`:

| Chart | Title |
|-------|-------|
| 01 | Order Status Distribution |
| 02 | Payment Type Distribution |
| 03 | Review Score Distribution |
| 04 | KPI Dashboard |
| 05 | Monthly Revenue & Order Trend |
| 06 | AOV Over Time |
| 07 | Top 15 Categories by Revenue |
| 08 | Top 15 Categories by Volume |
| 09 | Top 15 Sellers by Revenue |
| 10 | Revenue by Seller State |
| 11 | Customers & Revenue by State |
| 12 | Order Frequency Distribution |
| 13 | Customer Segmentation |
| 15 | Delivery Time Analysis |
| 16 | Freight Cost Analysis |
| 17 | Freight vs Price Scatter |
| 18 | Review Score by Category |
| 19 | Review vs Delivery Delay |
| 20 | Review: On-Time vs Late |
| 21 | Review vs Freight Cost |
| 22 | Correlation Heatmap |
| 23 | Review vs Delivery Time Bucket |

**End of EDA Notebook**
"""))

nb.cells = cells
out_path = os.path.join("notebooks", "01_eda.ipynb")
with open(out_path, "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print(f"Notebook saved: {out_path}")
