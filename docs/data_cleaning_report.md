# Data Cleaning Report
## Olist E-Commerce Business Intelligence & Analytics

> **Pipeline:** `src/data_cleaning.py`  
> **Reads from:** `data/raw/`  
> **Writes to:** `data/processed/`  
> **Date:** 2024  
> **Status:** Complete — 15/15 validation checks PASSED

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total tables processed | 9 raw → 10 cleaned + 5 analytics |
| Total rows before cleaning | 1,650,951 |
| Total rows after cleaning | 1,432,123 |
| Rows removed | 262,407 |
| Primary reason for removal | Geolocation duplicates (261,831) + duplicate reviews (551) |
| Cleaning decisions made | 20 documented actions |
| Validation checks | **15 PASS / 0 FAIL** |
| Revenue consistency error | R$0.00 (exact match) |

---

## 1. Row Counts Before & After Cleaning

| Table | Before | After | Removed | Notes |
|-------|--------|-------|---------|-------|
| `customers` | 99,441 | 99,441 | 0 | No rows removed |
| `geolocation` | 1,000,163 | 738,307 | 261,856 | 261,831 duplicates + 25 coordinate outliers |
| `geolocation_zip` | — | 19,011 | — | New: 1 row per ZIP prefix (aggregated) |
| `orders` | 99,441 | 99,441 | 0 | No rows removed |
| `order_items` | 112,650 | 112,650 | 0 | No rows removed |
| `order_payments` | 103,886 | 103,886 | 0 | No rows removed (3 relabelled) |
| `order_reviews` | 99,224 | 98,673 | 551 | 551 duplicate/extra reviews removed |
| `products` | 32,951 | 32,951 | 0 | No rows removed |
| `sellers` | 3,095 | 3,095 | 0 | No rows removed |
| `category_translation` | 71 | 74 | -3 | 3 rows ADDED (missing translations) |
| **TOTAL** | **1,650,922** | **1,388,519** | **262,403** | |

---

## 2. Analytics Datasets Created

| File | Grain | Rows | Description |
|------|-------|------|-------------|
| `orders_enriched.csv` | 1 row per order | 99,441 | Orders + customer + payment summary + item summary + derived date/delivery fields |
| `order_items_enriched.csv` | 1 row per item | 112,650 | Items + order status + product category (English) + seller state |
| `customer_analytics.csv` | 1 row per unique customer | 96,096 | Customer-level KPIs: total orders, spend, avg review, first/last purchase |
| `product_analytics.csv` | 1 row per product | 32,216 | Product-level KPIs (delivered orders): revenue, units sold, avg review |
| `seller_analytics.csv` | 1 row per seller | 2,970 | Seller-level KPIs (delivered orders): revenue, items sold, avg review |

---

## 3. Missing Values — Before & After

| Table | Column | Nulls Before | Nulls After | Action |
|-------|--------|-------------|-------------|--------|
| `orders` | `order_approved_at` | 160 | 160 | Retained — valid business state |
| `orders` | `order_delivered_carrier_date` | 1,783 | 1,783 | Retained — valid business state |
| `orders` | `order_delivered_customer_date` | 2,965 | 2,965 | Retained — valid business state |
| `products` | `product_category_name` | 610 | 0 | Filled with `'unknown'` |
| `products` | `product_name_length` | 610 | 610 | Retained — no imputation justified |
| `products` | `product_description_length` | 610 | 610 | Retained — no imputation justified |
| `products` | `product_photos_qty` | 610 | 610 | Retained — no imputation justified |
| `products` | `product_weight_g` | 2 | 6 | 4 zero-weight rows → set to NaN (+4) |
| `products` | `product_length_cm` | 2 | 2 | Retained |
| `products` | `products` | `product_height_cm` | 2 | 2 | Retained |
| `products` | `product_width_cm` | 2 | 2 | Retained |
| `order_reviews` | `review_comment_title` | 87,656 | 0 | Filled with empty string `''` |
| `order_reviews` | `review_comment_message` | 58,247 | 0 | Filled with empty string `''` |

---

## 4. Duplicate Records — Before & After

| Table | Duplicates Before | Duplicates After | Action |
|-------|-------------------|------------------|--------|
| `customers` | 0 | 0 | None needed |
| `geolocation` | 261,831 full-row | 0 | Removed — kept first occurrence per group |
| `orders` | 0 | 0 | None needed |
| `order_items` | 0 | 0 | None needed |
| `order_payments` | 0 | 0 | None needed |
| `order_reviews` (by `order_id`) | 549 extra rows | 0 | Kept most-recent review per `order_id` |
| `order_reviews` (by `review_id`) | 1,603 rows sharing review_id | 0 | Resolved by dedup on `order_id` |
| `products` | 0 | 0 | None needed |
| `sellers` | 0 | 0 | None needed |
| `category_translation` | 0 | 0 | None needed |

---

## 5. Data Type Changes

| Table | Column | Before | After | Reason |
|-------|--------|--------|-------|--------|
| `orders` | `order_purchase_timestamp` | object (string) | datetime64[ns] | Enable date arithmetic |
| `orders` | `order_approved_at` | object (string) | datetime64[ns] | Enable date arithmetic |
| `orders` | `order_delivered_carrier_date` | object (string) | datetime64[ns] | Enable date arithmetic |
| `orders` | `order_delivered_customer_date` | object (string) | datetime64[ns] | Enable date arithmetic |
| `orders` | `order_estimated_delivery_date` | object (string) | datetime64[ns] | Enable date arithmetic |
| `order_items` | `shipping_limit_date` | object (string) | datetime64[ns] | Enable date arithmetic |
| `order_reviews` | `review_creation_date` | object (string) | datetime64[ns] | Enable date arithmetic |
| `order_reviews` | `review_answer_timestamp` | object (string) | datetime64[ns] | Enable date arithmetic |
| `customers` | `customer_zip_code_prefix` | int64 | Int64 (nullable) | Nullable integer type |
| `products` | All numeric fields | float64 | float64 | Already correct |
| `order_payments` | `payment_installments` | int64 | Int64 (nullable) | Nullable integer |

---

## 6. Column Renames

| Table | Old Column Name | New Column Name | Reason |
|-------|----------------|-----------------|--------|
| `products_clean` | `product_name_lenght` | `product_name_length` | Corrects source typo |
| `products_clean` | `product_description_lenght` | `product_description_length` | Corrects source typo |

> **Original raw CSV files are NOT renamed.** Rename applies only to `products_clean.csv`.

---

## 7. Categorical Value Changes

| Table | Column | Old Value | New Value | Count | Reason |
|-------|--------|-----------|-----------|-------|--------|
| `order_payments_clean` | `payment_type` | `not_defined` | `unknown` | 3 | More descriptive than misleading 'not_defined' |
| `products_clean` | `product_category_name` | `NULL` | `unknown` | 610 | Products exist; label explicitly uncategorized |
| `category_translation_clean` | `product_category_name_english` | (missing) | `PC Gamer` | 1 | Added missing translation |
| `category_translation_clean` | `product_category_name_english` | (missing) | `Portable Kitchen & Food Preparers` | 1 | Added missing translation |
| `category_translation_clean` | `product_category_name_english` | (missing) | `Unknown / Uncategorized` | 1 | Lookup for unknown category |

---

## 8. Numerical Corrections

| Table | Column | Change | Count | Reason |
|-------|--------|--------|-------|--------|
| `products_clean` | `product_weight_g` | 0 → NaN | 4 | 0g is physically impossible for a shipped product |
| `order_payments_clean` | `payment_installments` | 0 → 1 | 2 | Credit card with 0 installments is invalid; minimum is 1 |

---

## 9. New Columns Added

### `orders_enriched.csv`
| Column | Type | Description |
|--------|------|-------------|
| `customer_unique_id` | string | From customers join |
| `customer_state` | string | From customers join |
| `customer_city` | string | From customers join |
| `customer_zip_code_prefix` | Int64 | From customers join |
| `total_payment_value` | float64 | SUM(payment_value) per order |
| `payment_methods` | string | Pipe-separated list of payment types used |
| `max_installments` | Int64 | Max installments across payment rows |
| `n_payment_rows` | Int64 | Count of payment rows for this order |
| `item_count` | Int64 | Number of items in order |
| `product_revenue` | float64 | SUM(price) for order |
| `freight_revenue` | float64 | SUM(freight_value) for order |
| `total_order_revenue` | float64 | product_revenue + freight_revenue |
| `order_year` | Int64 | Year of purchase |
| `order_month` | Int64 | Month of purchase (1–12) |
| `order_year_month` | string | "YYYY-MM" period |
| `order_quarter` | string | "YYYYQn" period |
| `order_day_of_week` | string | Day name of purchase |
| `order_week` | Int64 | ISO week number |
| `delivery_days` | float64 | Actual delivery time in days (NULL if not delivered) |
| `estimated_delivery_days` | float64 | Estimated delivery time in days |
| `delivery_delay_days` | float64 | Actual minus estimated (+late, -early) |
| `is_delayed` | float64/bool | True if delivery_delay_days > 0 |
| `approval_hours` | float64 | Hours from purchase to approval |

### `order_items_enriched.csv`
| Column | Type | Description |
|--------|------|-------------|
| `order_status` | string | From orders join |
| `order_purchase_timestamp` | datetime | From orders join |
| `order_delivered_customer_date` | datetime | From orders join |
| `order_estimated_delivery_date` | datetime | From orders join |
| `customer_id` | string | From orders join |
| `product_category_name` | string | From products join (Portuguese) |
| `product_category_name_english` | string | From category_translation join |
| `product_weight_g` | float64 | From products join |
| `seller_state` | string | From sellers join |
| `seller_city` | string | From sellers join |
| `item_revenue` | float64 | price + freight_value |
| `order_year_month` | string | "YYYY-MM" period |

### `order_payments_clean.csv`
| Column | Type | Description |
|--------|------|-------------|
| `is_zero_payment` | bool | True if payment_value == 0.00 |

### `order_reviews_clean.csv`
| Column | Type | Description |
|--------|------|-------------|
| `has_comment` | bool | True if review_comment_message is non-empty |

### `customer_analytics.csv`
| Column | Type | Description |
|--------|------|-------------|
| `total_orders` | Int64 | Total orders placed |
| `delivered_orders` | Int64 | Orders with status=delivered |
| `first_order_date` | datetime | Earliest purchase timestamp |
| `last_order_date` | datetime | Most recent purchase timestamp |
| `total_spend_payment` | float64 | Sum of all payment values |
| `total_items_bought` | Int64 | Sum of items across orders |
| `avg_review_score` | float64 | Mean of reviews on this customer's orders |
| `is_repeat_buyer` | bool | True if total_orders >= 2 |
| `avg_order_value` | float64 | total_spend_payment / total_orders |

---

## 10. Validation Results (Post-Cleaning)

All 15 checks passed with 0 failures:

| Check | Result | Detail |
|-------|--------|--------|
| customers PK uniqueness | ✅ PASS | 99,441 unique / 99,441 rows |
| orders PK uniqueness | ✅ PASS | 99,441 unique / 99,441 rows |
| products PK uniqueness | ✅ PASS | 32,951 unique / 32,951 rows |
| sellers PK uniqueness | ✅ PASS | 3,095 unique / 3,095 rows |
| order_reviews 1-per-order | ✅ PASS | 98,673 unique order_id / 98,673 rows |
| orders→customers FK | ✅ PASS | 0 orphan orders |
| order_items→orders FK | ✅ PASS | 0 orphan items |
| order_items→products FK | ✅ PASS | 0 orphan items |
| order_items→sellers FK | ✅ PASS | 0 orphan items |
| order_payments→orders FK | ✅ PASS | 0 orphan payments |
| orders_enriched grain (1 row/order) | ✅ PASS | 99,441 unique / 99,441 rows |
| items_enriched row count matches | ✅ PASS | 112,650 = 112,650 |
| Revenue consistency | ✅ PASS | order_items R$15,843,553.24 = orders_enriched total (R$0.00 diff) |
| orders dates are datetime | ✅ PASS | datetime64[ns] |
| No negative delivery_days | ✅ PASS | 0 orders with negative delivery time |

---

## 11. Remaining Known Issues (Not Fixed — By Design)

These issues are documented but intentionally not corrected:

| Issue | Table | Count | Reason Not Fixed |
|-------|-------|-------|-----------------|
| Missing `order_approved_at` | `orders` | 160 | Valid business state — payment not captured |
| Missing `order_delivered_carrier_date` | `orders` | 1,783 | Valid business state — not yet shipped |
| Missing `order_delivered_customer_date` | `orders` | 2,965 | Valid business state — not yet delivered |
| Missing `product_name_length` etc. | `products` | 610 | No imputation source; labeled 'unknown' in category only |
| Missing `product_weight_g` etc. | `products` | 6 | No imputation justified without external data |
| Zero `payment_value` rows | `order_payments` | 9 | Flagged with `is_zero_payment`; may be valid voucher-zeroed rows |
| Orders with no items (`unavailable`/`canceled`) | `orders` | 775 | Business state — canceled orders naturally have no items |
| Orders with no review | `orders` | 768 | Normal — not all customers leave reviews; no imputation |
| 1 order with no payment record | `orders` | 1 | Extremely rare; no imputation |

---

## 12. Cleaning Decision Log

| # | Table | Issue | Rows Affected | Action Taken | Justification |
|---|-------|-------|---------------|--------------|---------------|
| 1 | customers | City/state case normalisation | 99,441 | Lower city, upper state | Consistent groupby/join |
| 2 | geolocation | Fully duplicate rows (DQ-01) | 261,831 | Removed | No info lost; prevents join fan-out |
| 3 | geolocation | Coordinate outliers (DQ-02) | 25 | Removed | Out of Brazil bounding box |
| 4 | orders | Missing approved_at (DQ-05) | 160 | Retained as NULL | Valid business state |
| 5 | orders | Missing carrier date (DQ-06) | 1,783 | Retained as NULL | Valid business state |
| 6 | orders | Missing delivery date (DQ-07) | 2,965 | Retained as NULL | Valid business state |
| 7 | order_items | Price <= 0 validation | 0 | No action — validated clean | N/A |
| 8 | order_items | Freight < 0 validation | 0 | No action — validated clean | N/A |
| 9 | order_payments | `not_defined` payment type (DQ-13) | 3 | Relabelled to 'unknown' | More accurate label |
| 10 | order_payments | Zero payment_value (DQ-14) | 9 | Retained; flagged column added | Possible valid voucher usage |
| 11 | order_payments | 0 installments on credit card (DQ-15) | 2 | Set to 1 | Minimum valid value for credit card |
| 12 | order_reviews | Duplicate reviews per order (DQ-03/04) | 551 | Kept most-recent per order_id | Customer's final opinion |
| 13 | order_reviews | NULL comment fields | 145,903 | Filled with '' | NLP-ready; analytically neutral |
| 14 | products | Column name typos (DQ-11) | 2 cols | Renamed in processed file only | Correctness; raw file unchanged |
| 15 | products | Missing category (DQ-08) | 610 | Filled with 'unknown' | Real sales; must appear in category analysis |
| 16 | products | Zero weight (DQ-10) | 4 | Set to NaN | Physically impossible value |
| 17 | sellers | City/state normalisation | 3,095 | Lower city, upper state | Consistent with customers |
| 18 | category_translation | Missing translations (DQ-12) | 3 | Added rows for pc_gamer, portateis_..., unknown | Prevents NULL in English dashboards |
| 19 | orders_enriched | Built join + derived columns | 99,441 | LEFT JOINs + arithmetic | Central analytics table |
| 20 | Various | Analytics tables built | 5 tables | Aggregated to correct grains | Prevents double-counting |
