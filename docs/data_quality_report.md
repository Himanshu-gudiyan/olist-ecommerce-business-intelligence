# Data Quality Report
## Olist E-Commerce Business Intelligence & Analytics

> **Source:** Real Olist Brazilian E-Commerce Public Dataset  
> **Audit Date:** 2024  
> **Status:** Issues identified — NOT yet fixed (awaiting remediation phase)

---

## Executive Summary

| Severity | Issue Count |
|----------|-------------|
| 🔴 High | 3 |
| 🟡 Medium | 8 |
| 🟢 Low / Informational | 6 |

**Overall data quality assessment: Good for analytics with targeted handling of known issues.**

---

## Issue Index

| # | Table | Issue | Severity | Rows Affected |
|---|-------|-------|----------|---------------|
| DQ-01 | `geolocation` | 261,831 fully duplicate rows | 🟡 Medium | 261,831 |
| DQ-02 | `geolocation` | Coordinate outliers outside Brazil | 🟡 Medium | ~55 |
| DQ-03 | `order_reviews` | Duplicate `review_id` values | 🟡 Medium | 1,603 |
| DQ-04 | `order_reviews` | Multiple reviews per order | 🟡 Medium | 1,098 |
| DQ-05 | `orders` | Missing `order_approved_at` | 🟢 Low | 160 |
| DQ-06 | `orders` | Missing `order_delivered_carrier_date` | 🟡 Medium | 1,783 |
| DQ-07 | `orders` | Missing `order_delivered_customer_date` | 🟡 Medium | 2,965 |
| DQ-08 | `products` | Missing all descriptive attributes | 🟡 Medium | 610 |
| DQ-09 | `products` | Missing dimension fields only | 🟢 Low | 2 |
| DQ-10 | `products` | Zero weight products | 🟢 Low | 4 |
| DQ-11 | `products` | Column name typos ("lenght") | 🟢 Low | 2 columns |
| DQ-12 | `products` | 2 categories missing English translation | 🟢 Low | 610+ products |
| DQ-13 | `order_payments` | `payment_type` = `not_defined` | 🟡 Medium | 3 |
| DQ-14 | `order_payments` | Zero payment values | 🟢 Low | 9 |
| DQ-15 | `order_payments` | Zero installments on credit card | 🟢 Low | 2 |
| DQ-16 | `orders` | Orders with no items | 🔴 High | 775 |
| DQ-17 | `orders` | Orders with no payment record | 🔴 High | 1 |
| DQ-18 | `orders` | Orders with no review | 🔴 High | 768 |

---

## Detailed Issue Descriptions

---

### DQ-01 — Geolocation: 261,831 Fully Duplicate Rows
**Table:** `olist_geolocation_dataset`  
**Severity:** 🟡 Medium  
**Rows Affected:** 261,831 out of 1,000,163 (26.2%)

**Description:**  
Over a quarter of the geolocation table consists of rows that are 100% identical across all 5 columns. These are true duplicates (not near-duplicates).

**Impact:**  
Any join from `customers` or `sellers` to `geolocation` on `zip_code_prefix` will produce duplicate rows unless the geolocation table is deduplicated first.

**Recommended Handling:**  
Deduplicate by `(zip_code_prefix)` before joining — take the mean or first-occurring `lat`/`lng` per ZIP prefix.

---

### DQ-02 — Geolocation: Coordinate Outliers Outside Brazil
**Table:** `olist_geolocation_dataset`  
**Severity:** 🟡 Medium  
**Rows Affected:** ~55 (29 bad latitudes, 26 bad longitudes; some may overlap)

**Description:**  
Brazil's geographic bounding box is approximately latitude -35° to 5° and longitude -75° to -30°. The dataset contains:
- 29 records with latitude outside this range (including a value of +45.07°, which is in Europe)
- 26 records with longitude outside this range (including values beyond ±100°)

**Impact:**  
Small impact given the 1M total rows. Would cause wrong map pin placement if not filtered.

**Recommended Handling:**  
Filter out rows outside the bounding box when building geographic visualizations.

---

### DQ-03 — Order Reviews: Duplicate `review_id` Values
**Table:** `olist_order_reviews_dataset`  
**Severity:** 🟡 Medium  
**Rows Affected:** 1,603

**Description:**  
`review_id` is expected to be a primary key but 1,603 rows share a `review_id` with at least one other row. This indicates either re-submission of reviews or a data pipeline issue.

**Impact:**  
Aggregate review metrics (e.g., average review score) may be slightly inflated if duplicates are counted multiple times.

**Recommended Handling:**  
Deduplicate on `(order_id, review_id)` keeping the most recent `review_answer_timestamp` before calculating review metrics.

---

### DQ-04 — Order Reviews: Multiple Reviews Per Order
**Table:** `olist_order_reviews_dataset`  
**Severity:** 🟡 Medium  
**Rows Affected:** 1,098 rows (from ~549 orders)

**Description:**  
1,098 rows share an `order_id` with another row, meaning approximately 549 orders have received more than one review submission. This may represent customers who submitted the review form multiple times.

**Impact:**  
When joining `orders` to `order_reviews` directly, this creates a fan-out. Aggregated review scores at order level need the latest (or deduplicated) review to be accurate.

**Recommended Handling:**  
Use `DISTINCT ON (order_id)` or equivalent window function (ROW_NUMBER by recency) to get one review per order.

---

### DQ-05 — Orders: Missing `order_approved_at`
**Table:** `olist_orders_dataset`  
**Severity:** 🟢 Low  
**Rows Affected:** 160

**Description:**  
160 orders have no payment approval timestamp. These correspond to orders where payment was never captured.

**Impact:**  
Low — affects only time-to-approval calculations. Orders without approval are not delivered.

**Recommended Handling:**  
Exclude from time-to-approval analysis. These are a natural business condition (unpaid orders).

---

### DQ-06 — Orders: Missing `order_delivered_carrier_date`
**Table:** `olist_orders_dataset`  
**Severity:** 🟡 Medium  
**Rows Affected:** 1,783

**Description:**  
1,783 orders have no carrier handoff date. These include undelivered and in-progress orders.

**Impact:**  
Affects delivery pipeline analysis. These are not erroneous — they reflect orders that were never picked up or canceled.

**Recommended Handling:**  
Filter to `order_status = 'delivered'` for delivery time analysis to eliminate nulls.

---

### DQ-07 — Orders: Missing `order_delivered_customer_date`
**Table:** `olist_orders_dataset`  
**Severity:** 🟡 Medium  
**Rows Affected:** 2,965

**Description:**  
2,965 orders have no actual delivery date. These are orders not yet delivered (shipped, processing, canceled, etc.).

**Impact:**  
Delivery KPIs (actual vs. estimated delivery) must only use the 96,476 orders with actual delivery dates.

**Recommended Handling:**  
Filter to rows where `order_delivered_customer_date IS NOT NULL` for delivery performance metrics.

---

### DQ-08 — Products: 610 Items Missing All Descriptive Attributes
**Table:** `olist_products_dataset`  
**Severity:** 🟡 Medium  
**Rows Affected:** 610 rows (1.85% of products)

**Description:**  
610 products are missing `product_category_name`, `product_name_lenght`, `product_description_lenght`, and `product_photos_qty` simultaneously. This suggests a data extraction failure for these product records.

**Impact:**  
These products cannot be categorized. They will appear as "Unknown" in category-level analytics. Since they do appear in `order_items`, they contribute to revenue counts but are uncategorized.

**Recommended Handling:**  
Label as `"Unknown"` or `"Uncategorized"` in category analysis. Do not drop them — they represent real sales.

---

### DQ-09 — Products: 2 Items Missing Only Dimension Fields
**Table:** `olist_products_dataset`  
**Severity:** 🟢 Low  
**Rows Affected:** 2

**Description:**  
2 products have null values for `product_weight_g`, `product_length_cm`, `product_height_cm`, and `product_width_cm` but otherwise have valid category and description data.

**Impact:**  
Minor — only affects logistics or weight-based analytics.

**Recommended Handling:**  
Impute with category median for shipping calculations if needed.

---

### DQ-10 — Products: 4 Items with Zero Weight
**Table:** `olist_products_dataset`  
**Severity:** 🟢 Low  
**Rows Affected:** 4

**Description:**  
4 products have `product_weight_g = 0`, which is physically impossible for a shipped item.

**Impact:**  
Negligible — affects freight weight calculations only.

**Recommended Handling:**  
Treat as null/missing for weight-based logistics calculations.

---

### DQ-11 — Products: Column Name Typos
**Table:** `olist_products_dataset`  
**Severity:** 🟢 Low (Informational)  
**Columns Affected:** `product_name_lenght`, `product_description_lenght`

**Description:**  
Both columns spell "length" as "lenght" — a known typo in the original Kaggle dataset. This is a column naming issue, not a data issue.

**Impact:**  
None on data correctness. Requires awareness when writing analysis code.

**Recommended Handling:**  
Rename in analysis code/views using aliases (`product_name_length`, `product_description_length`). Do not rename the original CSV.

---

### DQ-12 — Products: 2 Category Names Missing English Translation
**Tables:** `olist_products_dataset`, `product_category_name_translation`  
**Severity:** 🟢 Low  
**Categories:** `pc_gamer`, `portateis_cozinha_e_preparadores_de_alimentos`

**Description:**  
The translation table contains 71 entries while the products table uses 73 distinct category names. Two categories (`pc_gamer` and `portateis_cozinha_e_preparadores_de_alimentos`) will return NULL when left-joined to the translation table.

**Impact:**  
Minimal — products in these two categories will show Portuguese names in English-language dashboards.

**Recommended Handling:**  
Add manual translation entries: `pc_gamer` → `"PC Gamer"`, `portateis_cozinha_e_preparadores_de_alimentos` → `"Portable Kitchen & Food Preparers"`.

---

### DQ-13 — Order Payments: `payment_type` = `not_defined`
**Table:** `olist_order_payments_dataset`  
**Severity:** 🟡 Medium  
**Rows Affected:** 3

**Description:**  
3 payment records have `payment_type = 'not_defined'`. This is not a valid payment method.

**Impact:**  
Negligible for aggregate analysis. Misleading in payment method distribution charts if not categorized separately.

**Recommended Handling:**  
Group under `"Other / Unknown"` in payment type analysis.

---

### DQ-14 — Order Payments: Zero Payment Values
**Table:** `olist_order_payments_dataset`  
**Severity:** 🟢 Low  
**Rows Affected:** 9

**Description:**  
9 payment rows have `payment_value = 0.00`. These may be fully-voucher-discounted items or system artifacts.

**Impact:**  
Negligible for revenue totals. May inflate payment record counts.

**Recommended Handling:**  
Investigate in context of `payment_type`; exclude from average payment value calculations.

---

### DQ-15 — Order Payments: Zero Installments on Credit Card
**Table:** `olist_order_payments_dataset`  
**Severity:** 🟢 Low  
**Rows Affected:** 2

**Description:**  
2 credit card records show `payment_installments = 0`. Credit card payments should have at least 1 installment.

**Impact:**  
Negligible — affects installment distribution analysis only.

**Recommended Handling:**  
Treat as 1 installment for analysis purposes.

---

### DQ-16 — Orders: 775 Orders with No Line Items
**Table:** `olist_orders_dataset` vs. `olist_order_items_dataset`  
**Severity:** 🔴 High  
**Rows Affected:** 775 orders

**Description:**  
775 order IDs in `orders` have no corresponding rows in `order_items`. Breakdown:
- 603 `unavailable`
- 164 `canceled`
- 5 `created`
- 2 `invoiced`
- 1 `shipped`

**Impact:**  
Any revenue metric computed from `order_items` naturally excludes these orders — this is correct business behavior (canceled/unavailable orders have no items). However, the 1 `shipped` and 2 `invoiced` orders with no items may represent data pipeline failures.

**Recommended Handling:**  
Use `INNER JOIN orders ON order_items.order_id = orders.order_id` and filter by `order_status = 'delivered'` for revenue analysis. Flag the 3 anomalous non-canceled/unavailable orders.

---

### DQ-17 — Orders: 1 Order with No Payment Record
**Table:** `olist_orders_dataset` vs. `olist_order_payments_dataset`  
**Severity:** 🔴 High  
**Rows Affected:** 1

**Description:**  
One order ID in `orders` has no corresponding row in `order_payments`. Revenue calculations based on `order_payments` will miss this order's value (if any).

**Impact:**  
Negligible at scale (1 record). Indicates a rare data pipeline issue.

**Recommended Handling:**  
Exclude this order from payment-based revenue analytics or use `order_items` price sum as an alternative revenue source.

---

### DQ-18 — Orders: 768 Orders with No Review
**Table:** `olist_orders_dataset` vs. `olist_order_reviews_dataset`  
**Severity:** 🔴 High  
**Rows Affected:** 768

**Description:**  
768 orders never received a customer review. This is a natural business scenario (customers don't always review).

**Impact:**  
Review coverage is ~99.2%. Satisfaction metrics are not 100% representative but are sufficient for trend analysis. Do not impute missing scores.

**Recommended Handling:**  
Use `LEFT JOIN` when combining orders with reviews and note that review metrics apply only to reviewed orders.

---

## Summary: Recommended Pre-Processing Steps

Before building analytics:

1. **Filter orders** to `order_status = 'delivered'` for revenue, delivery, and satisfaction KPIs.
2. **Deduplicate geolocation** — group by `zip_code_prefix`, take average `lat`/`lng`.
3. **Remove geolocation outliers** — filter coordinates to Brazil's bounding box.
4. **Deduplicate reviews** — keep most recent review per `order_id`.
5. **Label null product categories** as `"Unknown / Uncategorized"`.
6. **Add missing category translations** for `pc_gamer` and `portateis_cozinha_e_preparadores_de_alimentos`.
7. **Use INNER JOIN** between `orders` and `order_items` for revenue metrics.
8. **Note 2 typos** in `products` column names when aliasing.
