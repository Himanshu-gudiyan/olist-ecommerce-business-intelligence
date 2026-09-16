# Data Dictionary
## Olist E-Commerce Business Intelligence & Analytics

> **Source:** Real Olist Brazilian E-Commerce Public Dataset  
> **Last Audited:** 2024  
> **Total Tables:** 9 CSV files  
> **Total Records (combined):** ~1,650,000+ rows across all tables

---

## Table of Contents

1. [olist_customers_dataset](#1-olist_customers_dataset)
2. [olist_orders_dataset](#2-olist_orders_dataset)
3. [olist_order_items_dataset](#3-olist_order_items_dataset)
4. [olist_order_payments_dataset](#4-olist_order_payments_dataset)
5. [olist_order_reviews_dataset](#5-olist_order_reviews_dataset)
6. [olist_products_dataset](#6-olist_products_dataset)
7. [olist_sellers_dataset](#7-olist_sellers_dataset)
8. [olist_geolocation_dataset](#8-olist_geolocation_dataset)
9. [product_category_name_translation](#9-product_category_name_translation)

---

## 1. olist_customers_dataset

**File:** `data/olist_customers_dataset.csv`  
**Rows:** 99,441 | **Columns:** 5  
**Description:** Customer registry. Each row represents a customer–order pairing. A single real customer may appear multiple times with different `customer_id` values (each tied to one order), identified by the same `customer_unique_id`.

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| `customer_id` | string (UUID) | No | **Primary Key.** Unique identifier per order–customer link. Joins to `orders.customer_id`. |
| `customer_unique_id` | string (UUID) | No | True unique customer identifier. Use this to identify repeat buyers. |
| `customer_zip_code_prefix` | integer | No | 5-digit ZIP code prefix. Joins to `geolocation.geolocation_zip_code_prefix`. Range: 1,003–99,990. |
| `customer_city` | string | No | City name of the customer. 4,119 unique values. |
| `customer_state` | string | No | 2-letter Brazilian state code. 27 unique states. |

**Notes:**
- `customer_id` is 1:1 with orders (99,441 unique values = 99,441 rows).
- `customer_unique_id` has 96,096 unique values, meaning 3,345 real customers placed more than one order.

---

## 2. olist_orders_dataset

**File:** `data/olist_orders_dataset.csv`  
**Rows:** 99,441 | **Columns:** 8  
**Description:** Master orders table. Each row is a unique order placed on the Olist platform.

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| `order_id` | string (UUID) | No | **Primary Key.** Unique order identifier. |
| `customer_id` | string (UUID) | No | **Foreign Key** → `customers.customer_id`. |
| `order_status` | string | No | Current status of the order. Values: `delivered`, `shipped`, `canceled`, `unavailable`, `invoiced`, `processing`, `created`, `approved`. |
| `order_purchase_timestamp` | datetime | No | Timestamp when the customer placed the order. Range: 2016-09-04 to 2018-10-17. |
| `order_approved_at` | datetime | Yes (160 nulls) | Timestamp when the payment was approved. Null for orders not yet approved. |
| `order_delivered_carrier_date` | datetime | Yes (1,783 nulls) | Date/time the order was handed to the logistics carrier. |
| `order_delivered_customer_date` | datetime | Yes (2,965 nulls) | Date/time the order was delivered to the customer. Null for non-delivered orders. |
| `order_estimated_delivery_date` | datetime | No | Estimated delivery date provided to the customer at time of purchase. |

**Notes:**
- 96,478 orders (97.0%) have `delivered` status — the dominant state.
- 775 orders have no corresponding rows in `order_items` (mostly `unavailable` and `canceled`).
- 1 order has no payment record.

---

## 3. olist_order_items_dataset

**File:** `data/olist_order_items_dataset.csv`  
**Rows:** 112,650 | **Columns:** 7  
**Description:** Line items within each order. An order can contain multiple items (from possibly different sellers).

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| `order_id` | string (UUID) | No | **Foreign Key** → `orders.order_id`. |
| `order_item_id` | integer | No | Sequential item number within the order. Range: 1–21. |
| `product_id` | string (UUID) | No | **Foreign Key** → `products.product_id`. |
| `seller_id` | string (UUID) | No | **Foreign Key** → `sellers.seller_id`. |
| `shipping_limit_date` | datetime | No | Latest date/time for the seller to ship the item. |
| `price` | float | No | Unit price of the item in BRL. Range: R$0.85–R$6,735.00. Mean: R$120.65. |
| `freight_value` | float | No | Freight cost for the item in BRL. Range: R$0.00–R$409.68. Mean: R$19.99. |

**Notes:**
- 98,666 unique `order_id` values appear (vs. 99,441 orders) — the 775 gap matches orders with no items.
- 32,951 unique products; 3,095 unique sellers in this table.
- `order_item_id` max = 21, meaning one order can have up to 21 line items.

---

## 4. olist_order_payments_dataset

**File:** `data/olist_order_payments_dataset.csv`  
**Rows:** 103,886 | **Columns:** 5  
**Description:** Payment records for orders. One order may have multiple payment rows (e.g., credit card + voucher).

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| `order_id` | string (UUID) | No | **Foreign Key** → `orders.order_id`. |
| `payment_sequential` | integer | No | Sequential number for each payment method used in an order. Range: 1–29. |
| `payment_type` | string | No | Payment method. Values: `credit_card`, `boleto`, `voucher`, `debit_card`, `not_defined`. |
| `payment_installments` | integer | No | Number of installments chosen by the customer. Range: 0–24. |
| `payment_value` | float | No | Value paid in this payment row in BRL. Range: R$0.00–R$13,664.08. Mean: R$154.10. |

**Notes:**
- 99,440 unique `order_id` values (1 order has no payment record).
- 3,039 orders used 2+ payment methods (e.g., partial voucher + credit card).
- `payment_type` = `not_defined` appears 3 times (likely data entry errors).
- 2 records have `payment_installments` = 0 (credit card type — anomalous).
- 9 records have `payment_value` = 0.00.

---

## 5. olist_order_reviews_dataset

**File:** `data/olist_order_reviews_dataset.csv`  
**Rows:** 99,224 | **Columns:** 7  
**Description:** Customer reviews submitted after order delivery. Each row is one review submission.

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| `review_id` | string (UUID) | No | **Primary Key** (with caveats — 1,603 duplicate rows). |
| `order_id` | string (UUID) | No | **Foreign Key** → `orders.order_id`. |
| `review_score` | integer | No | Star rating 1–5. Mean: 4.09. |
| `review_comment_title` | string | Yes (87,656 nulls) | Optional title of the review comment. |
| `review_comment_message` | string | Yes (58,247 nulls) | Full review message. |
| `review_creation_date` | datetime | No | Date the review survey was sent to the customer. Range: 2016-10-02 to 2018-08-31. |
| `review_answer_timestamp` | datetime | No | Timestamp when the customer completed the review. Range: 2016-10-07 to 2018-10-29. |

**Notes:**
- 88.4% of reviews have no comment title; 58.7% have no comment message.
- 1,603 rows share a `review_id` with another row — true duplicates or re-submissions.
- 1,098 rows share an `order_id` — some orders received multiple review submissions.
- Score 5 is by far the most common (57,328 out of 99,224 = 57.8%).

---

## 6. olist_products_dataset

**File:** `data/olist_products_dataset.csv`  
**Rows:** 32,951 | **Columns:** 9  
**Description:** Product catalog. Each row is a unique product listed on the platform.

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| `product_id` | string (UUID) | No | **Primary Key.** |
| `product_category_name` | string | Yes (610 nulls) | Product category in Portuguese. 73 unique categories. |
| `product_name_lenght` | float | Yes (610 nulls) | Character length of the product name. Range: 5–76. Note: column name has typo ("lenght"). |
| `product_description_lenght` | float | Yes (610 nulls) | Character length of the product description. Range: 4–3,992. Note: typo ("lenght"). |
| `product_photos_qty` | float | Yes (610 nulls) | Number of photos in the product listing. Range: 1–20. |
| `product_weight_g` | float | Yes (2 nulls) | Product weight in grams. Range: 0–40,425g. |
| `product_length_cm` | float | Yes (2 nulls) | Product length in centimetres. Range: 7–105cm. |
| `product_height_cm` | float | Yes (2 nulls) | Product height in centimetres. Range: 2–105cm. |
| `product_width_cm` | float | Yes (2 nulls) | Product width in centimetres. Range: 6–118cm. |

**Notes:**
- 610 rows (1.85%) are missing all descriptive fields (`product_category_name` through `product_photos_qty`).
- 4 products have `product_weight_g` = 0 (likely data entry errors).
- Column names `product_name_lenght` and `product_description_lenght` contain a spelling error ("lenght" vs "length") — do not rename originals.
- 2 category names appear in products but are missing from the translation table: `pc_gamer`, `portateis_cozinha_e_preparadores_de_alimentos`.

---

## 7. olist_sellers_dataset

**File:** `data/olist_sellers_dataset.csv`  
**Rows:** 3,095 | **Columns:** 4  
**Description:** Registered sellers on the Olist platform.

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| `seller_id` | string (UUID) | No | **Primary Key.** |
| `seller_zip_code_prefix` | integer | No | 5-digit ZIP code prefix of the seller. Joins to `geolocation`. Range: 1,001–99,730. |
| `seller_city` | string | No | City where the seller is located. 611 unique cities. |
| `seller_state` | string | No | 2-letter Brazilian state code. 23 unique states. |

**Notes:**
- All 3,095 sellers are referenced in `order_items`.
- Only 23 of 27 Brazilian states have active sellers (vs. all 27 have customers).

---

## 8. olist_geolocation_dataset

**File:** `data/olist_geolocation_dataset.csv`  
**Rows:** 1,000,163 | **Columns:** 5  
**Description:** Geolocation mapping of Brazilian ZIP code prefixes to latitude/longitude coordinates. Multiple coordinate pairs may exist for one ZIP prefix (centroid variants).

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| `geolocation_zip_code_prefix` | integer | No | 5-digit ZIP code prefix. Join key to `customers` and `sellers`. 19,015 unique values. |
| `geolocation_lat` | float | No | Latitude. Range: -36.61 to 45.07 (includes outliers outside Brazil). |
| `geolocation_lng` | float | No | Longitude. Range: -101.47 to 121.11 (includes outliers outside Brazil). |
| `geolocation_city` | string | No | City name. 8,011 unique values. |
| `geolocation_state` | string | No | 2-letter state code. 27 unique values. |

**Notes:**
- 261,831 fully duplicate rows (26.2% of total).
- 29 records with latitude outside Brazil bounds (< -35 or > 5).
- 26 records with longitude outside Brazil bounds (< -75 or > -30) — likely data entry errors.
- Must deduplicate before using for mapping/geo analysis.

---

## 9. product_category_name_translation

**File:** `data/product_category_name_translation.csv`  
**Rows:** 71 | **Columns:** 2  
**Description:** Lookup table translating Portuguese product category names to English.

| Column | Data Type | Nullable | Description |
|--------|-----------|----------|-------------|
| `product_category_name` | string | No | **Primary Key.** Portuguese category name. Joins to `products.product_category_name`. |
| `product_category_name_english` | string | No | English translation of the category. |

**Notes:**
- 73 categories in `products` vs. 71 in this table — 2 categories lack an English translation: `pc_gamer` and `portateis_cozinha_e_preparadores_de_alimentos`.
- No nulls, no duplicates.
