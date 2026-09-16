import pandas as pd
import numpy as np
import os, warnings
warnings.filterwarnings('ignore')

PROC = 'data/processed'

files = {
    'customers_clean':            'customers_clean.csv',
    'geolocation_clean':          'geolocation_clean.csv',
    'geolocation_zip':            'geolocation_zip.csv',
    'orders_clean':               'orders_clean.csv',
    'order_items_clean':          'order_items_clean.csv',
    'order_payments_clean':       'order_payments_clean.csv',
    'order_reviews_clean':        'order_reviews_clean.csv',
    'products_clean':             'products_clean.csv',
    'sellers_clean':              'sellers_clean.csv',
    'category_translation_clean': 'category_translation_clean.csv',
    'orders_enriched':            'orders_enriched.csv',
    'order_items_enriched':       'order_items_enriched.csv',
    'customer_analytics':         'customer_analytics.csv',
    'product_analytics':          'product_analytics.csv',
    'seller_analytics':           'seller_analytics.csv',
}

print('=== FILE INVENTORY ===')
for name, fname in files.items():
    path = os.path.join(PROC, fname)
    exists = os.path.exists(path)
    size_kb = os.path.getsize(path) // 1024 if exists else 0
    df = pd.read_csv(path, low_memory=False) if exists else None
    rows = len(df) if df is not None else 0
    cols = len(df.columns) if df is not None else 0
    print("  %-45s rows=%7d  cols=%3d  size=%6dKB  exists=%s" % (fname, rows, cols, size_kb, exists))

print()
print('=== CRITICAL METRIC SPOT-CHECKS ===')

orders_e  = pd.read_csv(os.path.join(PROC, 'orders_enriched.csv'), low_memory=False,
                        parse_dates=['order_purchase_timestamp',
                                     'order_delivered_customer_date',
                                     'order_estimated_delivery_date'])
items_e   = pd.read_csv(os.path.join(PROC, 'order_items_enriched.csv'), low_memory=False)
cust_a    = pd.read_csv(os.path.join(PROC, 'customer_analytics.csv'), low_memory=False)
prod_a    = pd.read_csv(os.path.join(PROC, 'product_analytics.csv'), low_memory=False)
sell_a    = pd.read_csv(os.path.join(PROC, 'seller_analytics.csv'), low_memory=False)
reviews   = pd.read_csv(os.path.join(PROC, 'order_reviews_clean.csv'), low_memory=False)
payments  = pd.read_csv(os.path.join(PROC, 'order_payments_clean.csv'), low_memory=False)

delivered = orders_e[orders_e['order_status'] == 'delivered']

print("Total Orders:              %d" % len(orders_e))
print("Delivered Orders:          %d" % len(delivered))
print("Unique Customers:          %d" % cust_a['customer_unique_id'].nunique())
repeat = int(cust_a['is_repeat_buyer'].sum())
repeat_pct = cust_a['is_repeat_buyer'].mean() * 100
print("Repeat Buyers:             %d  (%.2f%%)" % (repeat, repeat_pct))

total_rev_items = items_e['item_revenue'].sum()
print("Total Revenue (all items): R$%.2f" % total_rev_items)

del_rev = items_e[items_e['order_status'] == 'delivered']['item_revenue'].sum()
print("Revenue (delivered only):  R$%.2f" % del_rev)

avg_ov = delivered['total_order_revenue'].mean()
print("Avg Order Value (deliv.):  R$%.2f" % avg_ov)

avg_review = reviews['review_score'].mean()
print("Avg Review Score:          %.4f" % avg_review)

avg_delivery = orders_e['delivery_days'].dropna().mean()
print("Avg Delivery Days:         %.2f" % avg_delivery)

delayed_df = orders_e[orders_e['is_delayed'].notna()]
delay_rate = (delayed_df['is_delayed'].astype(float) == 1.0).mean() * 100
print("Late Delivery Rate:        %.2f%%" % delay_rate)

print()
print('=== PAYMENT METHOD DISTRIBUTION ===')
pay_dist = payments['payment_type'].value_counts()
pay_pct  = payments['payment_type'].value_counts(normalize=True) * 100
for k in pay_dist.index:
    print("  %-15s: %7d (%.1f%%)" % (k, pay_dist[k], pay_pct[k]))

print()
print('=== TOP 5 CATEGORIES BY REVENUE (delivered) ===')
cat_rev = (
    items_e[items_e['order_status'] == 'delivered']
    .groupby('product_category_name_english')['item_revenue']
    .sum()
    .sort_values(ascending=False)
    .head(5)
)
for cat, rev in cat_rev.items():
    print("  %-45s: R$%12.2f" % (cat, rev))

print()
print('=== TOP 5 STATES BY REVENUE (delivered) ===')
state_rev = (
    delivered
    .groupby('customer_state')['total_order_revenue']
    .sum()
    .sort_values(ascending=False)
    .head(5)
)
for state, rev in state_rev.items():
    print("  %s: R$%12.2f" % (state, rev))

print()
print('=== DATE RANGE VERIFICATION ===')
print("Order date range: %s  to  %s" % (
    orders_e['order_purchase_timestamp'].min(),
    orders_e['order_purchase_timestamp'].max()
))

print()
print('=== DUPLICATE CHECKS ON ENRICHED DATASETS ===')
print("orders_enriched dup order_id:              %d" % orders_e['order_id'].duplicated().sum())
print("customer_analytics dup customer_unique_id: %d" % cust_a['customer_unique_id'].duplicated().sum())
print("product_analytics dup product_id:          %d" % prod_a['product_id'].duplicated().sum())
print("seller_analytics dup seller_id:            %d" % sell_a['seller_id'].duplicated().sum())
print("order_reviews_clean dup order_id:          %d" % reviews['order_id'].duplicated().sum())

print()
print('=== DOUBLE-COUNT SAFETY CHECK ===')
enriched_total = orders_e['total_order_revenue'].sum()
items_total    = items_e['item_revenue'].sum()
print("orders_enriched.total_order_revenue SUM:  R$%.2f" % enriched_total)
print("order_items_enriched.item_revenue SUM:    R$%.2f" % items_total)
diff = abs(enriched_total - items_total)
print("Difference: R$%.2f  (should be 0.00)" % diff)

print()
print('=== DERIVED COLUMN SANITY ===')
neg_del = orders_e[orders_e['delivery_days'].notna() & (orders_e['delivery_days'] < 0)]
print("Orders with negative delivery_days: %d  (should be 0)" % len(neg_del))
max_del = orders_e['delivery_days'].max()
min_del = orders_e['delivery_days'].dropna().min()
print("Min delivery_days: %.2f   Max delivery_days: %.2f" % (min_del, max_del))

null_rev = orders_e['total_order_revenue'].isna().sum()
print("orders_enriched rows with NULL total_order_revenue: %d" % null_rev)

print()
print('=== CATEGORY COVERAGE IN ENRICHED ITEMS ===')
null_cat = items_e['product_category_name_english'].isna().sum()
unknown_cat = (items_e['product_category_name_english'] == 'Unknown / Uncategorized').sum()
print("Items with NULL English category:    %d  (should be 0)" % null_cat)
print("Items labelled 'Unknown / Uncategorized': %d" % unknown_cat)

print()
print('ALL QUALITY CHECKS COMPLETE')
