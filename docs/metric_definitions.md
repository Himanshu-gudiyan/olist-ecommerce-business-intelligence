# Metric Definitions
## Olist E-Commerce Business Intelligence & Analytics

> All metrics are calculated from the **cleaned processed datasets** in `data/processed/`.  
> Revenue figures are in **Brazilian Reais (R$)**.  
> Unless otherwise stated, all revenue/order metrics are scoped to **delivered orders only** (`order_status = 'delivered'`).

---

## Table of Contents
1. [Scoping Rules](#scoping-rules)
2. [Order Metrics](#order-metrics)
3. [Customer Metrics](#customer-metrics)
4. [Revenue Metrics](#revenue-metrics)
5. [Payment Metrics](#payment-metrics)
6. [Delivery & Logistics Metrics](#delivery--logistics-metrics)
7. [Product & Category Metrics](#product--category-metrics)
8. [Seller Metrics](#seller-metrics)
9. [Review & Satisfaction Metrics](#review--satisfaction-metrics)

---

## Scoping Rules

| Rule | Value | Reason |
|------|-------|--------|
| **Order scope for revenue** | `order_status = 'delivered'` | Only delivered orders represent completed revenue |
| **Revenue grain** | `order_items` table | Item-level price + freight; avoids double-count from payment rows |
| **Customer grain** | `customer_unique_id` | True unique customers; `customer_id` is 1-per-order |
| **Date field for time series** | `order_purchase_timestamp` | Most complete date field (0 nulls); represents business event time |
| **Review grain** | One review per `order_id` (most recent) | Deduplicated; customer's final opinion |

---

## Order Metrics

### Total Orders
- **Definition:** Count of all unique orders in the dataset, regardless of status.
- **Formula:** `COUNT(DISTINCT order_id)` from `orders_clean.csv`
- **Result from data:** **99,441**
- **Grain:** Order-level

### Delivered Orders
- **Definition:** Count of orders with `order_status = 'delivered'`.
- **Formula:** `COUNT(order_id) WHERE order_status = 'delivered'` from `orders_clean.csv`
- **Result from data:** **96,478**
- **Grain:** Order-level
- **Note:** This is the primary denominator for most business KPIs.

### Orders by Status
- **Definition:** Count of orders grouped by `order_status`.
- **Formula:** `COUNT(order_id) GROUP BY order_status`
- **Source:** `orders_clean.csv`
- **Values:** delivered(96,478), shipped(1,107), canceled(625), unavailable(609), invoiced(314), processing(301), created(5), approved(2)

### Monthly Orders
- **Definition:** Count of orders placed per calendar month.
- **Formula:** `COUNT(order_id) GROUP BY order_year_month`
- **Source:** `orders_enriched.csv` → column `order_year_month`
- **Date range:** 2016-09 through 2018-10

---

## Customer Metrics

### Total Unique Customers
- **Definition:** Count of distinct real customers (people), not order-customer IDs.
- **Formula:** `COUNT(DISTINCT customer_unique_id)` from `customers_clean.csv`
- **Result from data:** **96,096**
- **Note:** `customer_id` (99,441 unique) ≠ real customer count because one customer can place multiple orders with a new `customer_id` each time.

### Repeat Purchase Rate
- **Definition:** Percentage of unique customers who placed 2 or more orders.
- **Formula:** `COUNT(customer_unique_id WHERE total_orders >= 2) / COUNT(customer_unique_id) * 100`
- **Source:** `customer_analytics.csv` → `total_orders`
- **Result from data:** **2,997 / 96,096 = ~3.12%**

### New Customers per Month
- **Definition:** Number of unique customers placing their first-ever order in a given month.
- **Formula:** `COUNT(customer_unique_id) WHERE first_order_date falls in month`
- **Source:** `customer_analytics.csv` → `first_order_date`

### Average Orders per Customer
- **Definition:** Average number of orders placed per unique customer.
- **Formula:** `SUM(total_orders) / COUNT(customer_unique_id)`
- **Source:** `customer_analytics.csv` → `total_orders`

### Customer Lifetime Value (CLV)
- **Definition:** Total payment value attributed to a single unique customer across all their orders.
- **Formula:** `SUM(total_payment_value) per order GROUP BY customer_unique_id`
- **Source:** `customer_analytics.csv` → `total_spend_payment`
- **Note:** Uses payment values (what customer actually paid) rather than item prices.

### Customers by State
- **Definition:** Count of unique customers per Brazilian state.
- **Formula:** `COUNT(DISTINCT customer_unique_id) GROUP BY customer_state`
- **Source:** `customer_analytics.csv` → `customer_state`

---

## Revenue Metrics

### Total Revenue
- **Definition:** Sum of all product prices plus freight values for all delivered order items.
- **Formula:** `SUM(price + freight_value)` from `order_items_clean.csv` WHERE `order_id` IN delivered orders
- **Result from data:** **R$15,843,553.24** (all order items); delivered-only is calculated in analytics
- **Why this formula:** `order_items` is the correct grain for revenue. Using `order_payments.payment_value` is an alternative but includes installment-based future amounts; item prices represent the actual sale value.

### Product Revenue
- **Definition:** Sum of item prices only (excluding freight).
- **Formula:** `SUM(price)` from `order_items_clean.csv` for delivered orders
- **Source:** `orders_enriched.csv` → `product_revenue`

### Freight Revenue
- **Definition:** Sum of freight charges only.
- **Formula:** `SUM(freight_value)` from `order_items_clean.csv` for delivered orders
- **Source:** `orders_enriched.csv` → `freight_revenue`

### Average Order Value (AOV)
- **Definition:** Average total value (price + freight) per delivered order.
- **Formula:** `SUM(price + freight_value) / COUNT(DISTINCT order_id)` for delivered orders
- **Source:** `orders_enriched.csv` → `total_order_revenue` / count of delivered orders
- **Note:** Computed at order level (sum of all items per order), then averaged across orders. Do NOT average item-level prices.

### Monthly Revenue
- **Definition:** Total revenue grouped by year-month of order purchase.
- **Formula:** `SUM(price + freight_value) GROUP BY order_year_month`
- **Source:** `orders_enriched.csv` → `order_year_month`, `total_order_revenue`

### Revenue by Product Category
- **Definition:** Total revenue attributed to each English product category.
- **Formula:** `SUM(price + freight_value) GROUP BY product_category_name_english`
- **Source:** `order_items_enriched.csv` → `product_category_name_english`, `item_revenue`
- **Filter:** `order_status = 'delivered'`

### Revenue by Customer State
- **Definition:** Total revenue from customers in each Brazilian state.
- **Formula:** `SUM(total_order_revenue) GROUP BY customer_state`
- **Source:** `orders_enriched.csv` → `customer_state`, `total_order_revenue`
- **Filter:** `order_status = 'delivered'`

### Revenue by Seller
- **Definition:** Total revenue (price + freight) fulfilled by each seller.
- **Formula:** `SUM(price + freight_value) GROUP BY seller_id`
- **Source:** `seller_analytics.csv` → `total_revenue`
- **Filter:** Delivered orders only

---

## Payment Metrics

### Payment Method Distribution
- **Definition:** Percentage share of each payment type by number of order-payment rows.
- **Formula:** `COUNT(payment_type) / COUNT(*) * 100 GROUP BY payment_type`
- **Source:** `order_payments_clean.csv`
- **Values (approx):** credit_card ~74%, boleto ~19%, voucher ~6%, debit_card ~1.5%

### Average Payment Value
- **Definition:** Average payment amount per payment row.
- **Formula:** `AVG(payment_value)` from `order_payments_clean.csv`
- **Note:** Excludes zero-payment rows (`is_zero_payment = True`) for meaningful average.

### Average Installments (Credit Card)
- **Definition:** Average number of installment payments chosen for credit card transactions.
- **Formula:** `AVG(payment_installments) WHERE payment_type = 'credit_card'`
- **Source:** `order_payments_clean.csv`

### Voucher Usage Rate
- **Definition:** Percentage of orders that used a voucher (partially or fully).
- **Formula:** `COUNT(DISTINCT order_id WHERE payment_type = 'voucher') / COUNT(DISTINCT order_id) * 100`
- **Source:** `order_payments_clean.csv`

### Multi-Payment Orders
- **Definition:** Count/percentage of orders that used more than one payment method.
- **Formula:** `COUNT(order_id WHERE MAX(payment_sequential) >= 2)`
- **Source:** `order_payments_clean.csv`
- **Result from data:** 3,039 orders (3.06%)

---

## Delivery & Logistics Metrics

> All delivery metrics are scoped to orders where `order_delivered_customer_date IS NOT NULL`.

### Average Delivery Time (Days)
- **Definition:** Average number of days from order placement to customer delivery.
- **Formula:** `AVG((order_delivered_customer_date - order_purchase_timestamp) / 86400)`
- **Source:** `orders_enriched.csv` → `delivery_days`
- **Filter:** `delivery_days IS NOT NULL`

### Estimated Delivery Days
- **Definition:** Number of days from order placement to the estimated delivery date promised to the customer.
- **Formula:** `(order_estimated_delivery_date - order_purchase_timestamp) / 86400`
- **Source:** `orders_enriched.csv` → `estimated_delivery_days`

### Delivery Delay Days
- **Definition:** Actual delivery date minus estimated delivery date. Positive = late, negative = early, zero = on time.
- **Formula:** `(order_delivered_customer_date - order_estimated_delivery_date) / 86400`
- **Source:** `orders_enriched.csv` → `delivery_delay_days`

### On-Time Delivery Rate
- **Definition:** Percentage of delivered orders that arrived on or before the estimated delivery date.
- **Formula:** `COUNT(order_id WHERE delivery_delay_days <= 0) / COUNT(delivered order_id) * 100`
- **Source:** `orders_enriched.csv` → `is_delayed = False`

### Late Delivery Rate (Delay Rate)
- **Definition:** Percentage of delivered orders that arrived after the estimated delivery date.
- **Formula:** `COUNT(order_id WHERE is_delayed = True) / COUNT(delivered with known delivery) * 100`
- **Source:** `orders_enriched.csv` → `is_delayed = True`

### Approval Time (Hours)
- **Definition:** Time from order placement to payment approval.
- **Formula:** `(order_approved_at - order_purchase_timestamp) / 3600`
- **Source:** `orders_enriched.csv` → `approval_hours`
- **Filter:** `approval_hours IS NOT NULL`

### Average Freight Cost
- **Definition:** Average freight value per order item.
- **Formula:** `AVG(freight_value)` from `order_items_clean.csv`
- **Note:** Do NOT average freight at order level directly from `orders_enriched` → use item-level average for per-item freight cost.

---

## Product & Category Metrics

### Total Items Sold
- **Definition:** Count of individual product units sold in delivered orders.
- **Formula:** `COUNT(order_item_id)` from `order_items_clean.csv` WHERE order is delivered
- **Note:** This counts line items (one product unit per row), not unique products.

### Average Items per Order
- **Definition:** Average number of line items per delivered order.
- **Formula:** `COUNT(order_item_id) / COUNT(DISTINCT order_id)` for delivered orders
- **Source:** `orders_enriched.csv` → `item_count`, filter `order_status = 'delivered'`

### Top Products by Revenue
- **Definition:** Products ranked by total revenue (price + freight) in delivered orders.
- **Formula:** `SUM(price + freight_value) GROUP BY product_id ORDER BY SUM DESC`
- **Source:** `product_analytics.csv` → `total_revenue`

### Average Unit Price by Category
- **Definition:** Average item price per product category.
- **Formula:** `AVG(price) GROUP BY product_category_name_english`
- **Source:** `order_items_enriched.csv`

### Category Revenue Share
- **Definition:** Each category's revenue as a percentage of total revenue.
- **Formula:** `SUM(item_revenue per category) / SUM(item_revenue all) * 100`
- **Source:** `order_items_enriched.csv`

---

## Seller Metrics

### Total Active Sellers
- **Definition:** Count of sellers who fulfilled at least one delivered order.
- **Formula:** `COUNT(DISTINCT seller_id)` from `seller_analytics.csv`
- **Result from data:** **2,970** (out of 3,095 registered)

### Revenue by Seller
- **Definition:** Total revenue per seller in delivered orders.
- **Formula:** `SUM(price + freight_value) GROUP BY seller_id`
- **Source:** `seller_analytics.csv` → `total_revenue`

### Revenue by Seller State
- **Definition:** Total revenue attributed to sellers in each state.
- **Formula:** `SUM(total_revenue) GROUP BY seller_state`
- **Source:** `seller_analytics.csv`

### Seller Concentration (Market Share)
- **Definition:** Revenue share of top-N sellers vs. rest.
- **Formula:** `SUM(top_N_seller_revenue) / SUM(all_seller_revenue)`
- **Source:** `seller_analytics.csv` sorted by `total_revenue`

---

## Review & Satisfaction Metrics

### Average Review Score (Overall)
- **Definition:** Mean star rating across all deduplicated reviews.
- **Formula:** `AVG(review_score)` from `order_reviews_clean.csv`
- **Result from data:** **~4.09 / 5.0** (post-dedup)
- **Note:** One review per order (most recent). Reviews without a score are excluded (none in dataset).

### Review Score Distribution
- **Definition:** Count and percentage of reviews at each score level (1–5).
- **Formula:** `COUNT(review_id) GROUP BY review_score`
- **Source:** `order_reviews_clean.csv`

### Average Review Score by Category
- **Definition:** Mean review score for orders containing products in each category.
- **Formula:** `AVG(review_score) GROUP BY product_category_name_english`
- **Source:** `order_items_enriched.csv` LEFT JOIN `order_reviews_clean.csv` ON `order_id`
- **Note:** Join at order level, not item level, to avoid counting the same review multiple times for multi-item orders.

### Average Review Score by Seller
- **Definition:** Mean review score for all orders fulfilled by each seller.
- **Formula:** `AVG(review_score) GROUP BY seller_id`
- **Source:** `seller_analytics.csv` → `avg_review_score`
- **Note:** Uses deduplicated reviews (one per order).

### Review Score vs. Delivery Delay
- **Definition:** Comparison of average review score between on-time and late deliveries.
- **Formula:** `AVG(review_score) GROUP BY is_delayed`
- **Source:** `orders_enriched.csv` JOIN `order_reviews_clean.csv` ON `order_id`

### Comment Rate
- **Definition:** Percentage of reviews that include a written message.
- **Formula:** `COUNT(review_id WHERE has_comment = True) / COUNT(review_id) * 100`
- **Source:** `order_reviews_clean.csv` → `has_comment`

---

## Derived Columns Reference

All derived columns computed in `data_cleaning.py`:

| Column | Table | Formula | Notes |
|--------|-------|---------|-------|
| `order_year` | `orders_enriched` | `order_purchase_timestamp.year` | Integer |
| `order_month` | `orders_enriched` | `order_purchase_timestamp.month` | Integer 1–12 |
| `order_year_month` | `orders_enriched`, `order_items_enriched` | `to_period("M")` | e.g. "2018-01" |
| `order_quarter` | `orders_enriched` | `to_period("Q")` | e.g. "2018Q1" |
| `order_day_of_week` | `orders_enriched` | `dt.day_name()` | "Monday"…"Sunday" |
| `order_week` | `orders_enriched` | `dt.isocalendar().week` | ISO week number |
| `delivery_days` | `orders_enriched` | `(delivered_date - purchase_date).days` | NULL if not delivered |
| `estimated_delivery_days` | `orders_enriched` | `(estimated_date - purchase_date).days` | Always present |
| `delivery_delay_days` | `orders_enriched` | `(delivered_date - estimated_date).days` | + = late, - = early |
| `is_delayed` | `orders_enriched` | `delivery_delay_days > 0` | Boolean; NULL if not delivered |
| `approval_hours` | `orders_enriched` | `(approved_at - purchase_ts).hours` | NULL if not approved |
| `item_revenue` | `order_items_enriched` | `price + freight_value` | Per-item combined revenue |
| `total_order_revenue` | `orders_enriched` | `product_revenue + freight_revenue` | Order-level total |
| `is_zero_payment` | `order_payments_clean` | `payment_value == 0` | Flag; 9 records |
| `has_comment` | `order_reviews_clean` | `len(review_comment_message) > 0` | Boolean |
| `is_repeat_buyer` | `customer_analytics` | `total_orders >= 2` | Boolean |
| `avg_order_value` | `customer_analytics` | `total_spend_payment / total_orders` | Per-customer AOV |

---

## Phase 5 — Advanced Analytics Metrics

> Added in Phase 5. All metrics derived from real Olist data — no synthetic values.

---

## RFM Segmentation

### Overview
RFM (Recency, Frequency, Monetary) is a customer value scoring framework.
Each dimension is independently scored 1–5 using quintile-based binning (`pd.qcut`).
Segments are then assigned from the (R_score, F_score) combination using an industry-standard lookup table.

### Recency (R)
- **Definition:** Number of days between the customer's most recent delivered order and the snapshot date.
- **Snapshot date:** `max(order_purchase_timestamp) + 1 day` across all delivered orders.
- **Formula:** `(snapshot_date - max(order_purchase_timestamp)).days` per `customer_unique_id`
- **Scoring:** Quintile 1–5, **reversed** (lower recency = more recent = higher score). Score 5 = purchased very recently.
- **Source:** `orders_enriched.csv`, `order_status = 'delivered'`

### Frequency (F)
- **Definition:** Count of distinct delivered orders placed by each unique customer.
- **Formula:** `COUNT(DISTINCT order_id)` per `customer_unique_id` for delivered orders
- **Scoring:** Quintile 1–5 (higher = better). Score 5 = highest purchase frequency.
- **Limitation:** 96.9% of Olist customers have exactly 1 order → most score F=1 (accurately reflects dataset).

### Monetary (M)
- **Definition:** Total delivered revenue attributed to each unique customer.
- **Formula:** `SUM(total_order_revenue)` per `customer_unique_id` for delivered orders
- **Source:** `orders_enriched.csv` → `total_order_revenue`
- **Scoring:** Quintile 1–5 (higher = better). Score 5 = highest spender.

### RFM Segments

| Segment | Rule (R_score, F_score) |
|---------|------------------------|
| Champions | R≥4 AND F≥4 |
| Loyal Customers | F≥3 AND R≥2 |
| Potential Loyalists | R≥3 AND F=2 |
| New Customers | R≥4 AND F=1 |
| Promising | R=3 AND F=1 |
| Need Attention | R=2 AND F≥2 |
| At Risk | R=2 AND F≥3, OR R=1 AND F≥4 |
| Can't Lose Them | R=1 AND F=5 |
| Hibernating | R≤2 AND F≤2 |
| Lost | R=1 AND F=1 |

---

## Customer Retention & CLV (Phase 5)

### Repeat Purchase Rate (Phase 5 recalculation)
- **Definition:** Percentage of unique customers (delivered orders only) who placed 2 or more delivered orders.
- **Formula:** `COUNT(customer_unique_id WHERE freq >= 2) / COUNT(customer_unique_id) * 100`
- **Scope:** `order_status = 'delivered'` only (stricter than Phase 2 which used all statuses)
- **Result:** ~3.00–3.12% (consistent across both methods)

### Customer Lifetime Value (CLV) — Phase 5
- **Formula:** `SUM(total_order_revenue)` per `customer_unique_id` for delivered orders
- **Median vs Mean:** Right-skewed distribution; median is more representative for typical customer.

---

## Cohort Analysis

### Cohort Definition
- A cohort is a group of customers whose **first delivered order** falls in the same calendar month (`YYYY-MM`).
- **Formula:** `MIN(order_purchase_timestamp).to_period('M')` per `customer_unique_id`, delivered orders only.

### Cohort Period
- Period 0 = acquisition month (first order). Period 1 = next calendar month, etc.
- **Formula:** `purchase_period.astype('int64') - cohort_period.astype('int64')` (uses `pd.Period.astype('int64')` for compatibility)

### Retention Rate (Cohort)
- **Definition:** Percentage of a cohort's customers who placed at least one order in a given subsequent period.
- **Formula:** `COUNT(customer_unique_id in period N) / cohort_size * 100`
- **Dataset context:** Most cohorts show < 5% retention beyond Period 0, accurately reflecting the 3% repeat-buyer rate.

### Cohort Return Rate
- **Definition:** For each cohort, the % of customers who returned for ANY subsequent purchase (ever).
- **Formula:** `COUNT(customers with period > 0) / cohort_size * 100`

---

## Seller Intelligence

### Seller Performance Scorecard
Computed in `src/seller_intelligence.py`. Metrics per seller (delivered orders only):

| Column | Formula |
|--------|---------|
| `total_revenue` | `SUM(price + freight_value)` |
| `n_unique_orders` | `COUNT(DISTINCT order_id)` |
| `avg_review_score` | `MEAN(review_score)` (deduplicated reviews) |
| `avg_delivery_days` | `MEAN(delivery_days)` |
| `late_rate_pct` | `MEAN(is_delayed == 1.0) * 100` |
| `n_categories` | `COUNT(DISTINCT product_category_name_english)` |
| `top_category` | Category with highest item count for that seller |

### Seller Quintile Tiers
Each seller is scored 1–5 on revenue, review score, and late rate using `pd.qcut` quintiles.

| Tier | Quintile |
|------|---------|
| 1 (bottom 20%) | Q1 |
| 5 (top 20%) | Q5 |

### Seller Performance Flags

| Flag | Condition |
|------|-----------|
| Top Performer | revenue_tier ≥ 4 AND review_tier ≥ 4 |
| High Revenue, Low Satisfaction | revenue_tier ≥ 4 AND review_tier ≤ 2 |
| Hidden Gem (grow this) | review_tier ≥ 4 AND revenue_tier ≤ 2 |
| Delivery Problem | late_tier ≤ 2 (most delayed) |
| Under-Performing | revenue_tier ≤ 2 AND review_tier ≤ 2 |
| Average | all others |

---

## Growth Analytics

### Monthly Growth Metrics
Computed in `src/growth_analytics.py`.

| Metric | Formula |
|--------|---------|
| `revenue` | `SUM(item_revenue)` per month (delivered orders, item-level) |
| `n_orders` | `COUNT(DISTINCT order_id)` per month |
| `n_customers` | `COUNT(DISTINCT customer_unique_id)` per month |
| `aov` | `revenue / n_orders` per month |
| `rev_mom_pct` | `(revenue[t] - revenue[t-1]) / revenue[t-1] * 100` |
| `orders_mom_pct` | Same formula applied to `n_orders` |
| `aov_mom_pct` | Same formula applied to `aov` |

### Revenue Growth Flag
| Flag | Condition |
|------|-----------|
| `strong_growth` | `rev_mom_pct >= +20%` |
| `decline` | `rev_mom_pct <= -20%` |
| `normal` | all others |

### Category/State Trend
- `compute_category_trend(items, top_n=6)`: Top 6 categories by total revenue; monthly revenue per category.
- `compute_state_trend(orders, top_n=5)`: Top 5 customer states by total revenue; monthly revenue per state.

---

