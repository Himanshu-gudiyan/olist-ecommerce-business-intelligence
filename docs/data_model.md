# Data Model
## Olist E-Commerce Business Intelligence & Analytics

> **Source:** Real Olist Brazilian E-Commerce Public Dataset  
> **Schema Type:** Snowflake / Star hybrid  
> **Central Fact Table:** `olist_orders_dataset`

---

## Entity Relationship Diagram (Text)

```
product_category_name_translation
    product_category_name (PK)
         ▲
         | (many-to-1, via product_category_name)
         |
olist_products_dataset
    product_id (PK)
    product_category_name (FK → translation)
         ▲
         | (1-to-many, via product_id)
         |
olist_order_items_dataset ◄──────────── olist_sellers_dataset
    order_id (FK → orders)                   seller_id (PK)
    product_id (FK → products)                    ▲
    seller_id (FK → sellers)  ────────────────────┘ (many-to-1)
         |
         | (many-to-1, via order_id)
         ▼
olist_orders_dataset ──────────────────► olist_customers_dataset
    order_id (PK)                              customer_id (PK)
    customer_id (FK → customers)               customer_unique_id
         |
         ├──── olist_order_payments_dataset
         |         order_id (FK → orders)
         |
         └──── olist_order_reviews_dataset
                   order_id (FK → orders)

olist_customers_dataset
    customer_zip_code_prefix ──► olist_geolocation_dataset
                                     geolocation_zip_code_prefix

olist_sellers_dataset
    seller_zip_code_prefix ──────► olist_geolocation_dataset
                                     geolocation_zip_code_prefix
```

---

## Primary Keys

| Table | Primary Key | Uniqueness Verified |
|-------|-------------|---------------------|
| `customers` | `customer_id` | ✅ 99,441 unique / 99,441 rows |
| `orders` | `order_id` | ✅ 99,441 unique / 99,441 rows |
| `order_items` | `(order_id, order_item_id)` | ✅ Composite PK |
| `order_payments` | `(order_id, payment_sequential)` | ✅ Composite PK |
| `order_reviews` | `review_id` | ⚠️ 1,603 duplicate review_id values |
| `products` | `product_id` | ✅ 32,951 unique / 32,951 rows |
| `sellers` | `seller_id` | ✅ 3,095 unique / 3,095 rows |
| `geolocation` | `(geolocation_zip_code_prefix, lat, lng)` | ⚠️ 261,831 fully duplicate rows |
| `category_translation` | `product_category_name` | ✅ 71 unique / 71 rows |

---

## Foreign Key Relationships

| From Table | From Column | To Table | To Column | Type | Integrity |
|-----------|-------------|----------|-----------|------|-----------|
| `orders` | `customer_id` | `customers` | `customer_id` | Many-to-One | ✅ 0 orphans |
| `order_items` | `order_id` | `orders` | `order_id` | Many-to-One | ✅ 0 orphans |
| `order_items` | `product_id` | `products` | `product_id` | Many-to-One | ✅ 0 orphans |
| `order_items` | `seller_id` | `sellers` | `seller_id` | Many-to-One | ✅ 0 orphans |
| `order_payments` | `order_id` | `orders` | `order_id` | Many-to-One | ✅ 0 orphans |
| `order_reviews` | `order_id` | `orders` | `order_id` | Many-to-One | ✅ 0 orphans |
| `products` | `product_category_name` | `category_translation` | `product_category_name` | Many-to-One | ⚠️ 2 categories missing translation |
| `customers` | `customer_zip_code_prefix` | `geolocation` | `geolocation_zip_code_prefix` | Many-to-Many | ℹ️ Lookup join (non-strict FK) |
| `sellers` | `seller_zip_code_prefix` | `geolocation` | `geolocation_zip_code_prefix` | Many-to-Many | ℹ️ Lookup join (non-strict FK) |

---

## Relationship Cardinalities

| Relationship | Cardinality | Notes |
|---|---|---|
| Customer → Orders | 1-to-Many (via `customer_unique_id`) | One real customer can have multiple order entries |
| Order → Order Items | 1-to-Many | One order can contain up to 21 items |
| Order → Payments | 1-to-Many | One order can have multiple payment methods |
| Order → Reviews | 1-to-One (expected) | Occasional duplicates exist (1,098 orders have 2+ reviews) |
| Product → Order Items | 1-to-Many | One product can appear in many orders |
| Seller → Order Items | 1-to-Many | One seller fulfills many items across many orders |
| Category → Products | 1-to-Many | One category contains many products |
| ZIP → Geolocation | 1-to-Many | One ZIP prefix has multiple coordinate entries |

---

## Recommended Join Paths for Analytics

### Revenue & Sales Analysis
```sql
order_items
  JOIN orders ON order_items.order_id = orders.order_id
  JOIN products ON order_items.product_id = products.product_id
  JOIN category_translation ON products.product_category_name = category_translation.product_category_name
  JOIN sellers ON order_items.seller_id = sellers.seller_id
```

### Customer Geography Analysis
```sql
orders
  JOIN customers ON orders.customer_id = customers.customer_id
  LEFT JOIN geolocation ON customers.customer_zip_code_prefix = geolocation.geolocation_zip_code_prefix
  -- Note: deduplicate geolocation first (group by zip, take avg lat/lng)
```

### Payment Analysis
```sql
orders
  JOIN order_payments ON orders.order_id = order_payments.order_id
  JOIN customers ON orders.customer_id = customers.customer_id
```

### Delivery Performance Analysis
```sql
orders
  JOIN order_items ON orders.order_id = order_items.order_id
  JOIN sellers ON order_items.seller_id = sellers.seller_id
  -- Compute: delivered_customer_date - purchase_timestamp = actual delivery days
  -- Compute: estimated_delivery_date - delivered_customer_date = early/late
```

### Review & Satisfaction Analysis
```sql
orders
  JOIN order_reviews ON orders.order_id = order_reviews.order_id
  JOIN order_items ON orders.order_id = order_items.order_id
  JOIN products ON order_items.product_id = products.product_id
  JOIN category_translation ON products.product_category_name = category_translation.product_category_name
```

---

## Tables That Stand Alone (No Direct Analytics Join Needed)

| Table | Usage |
|-------|-------|
| `geolocation` | Enrich customer/seller location for geo-visualizations; must be deduplicated first |
| `category_translation` | Always join as a lookup to get English category names |

---

## Data Grain Summary

| Table | One Row Represents |
|-------|--------------------|
| `customers` | One customer–order pairing |
| `orders` | One order |
| `order_items` | One product line in one order |
| `order_payments` | One payment method used in one order |
| `order_reviews` | One review submitted for one order |
| `products` | One unique product SKU |
| `sellers` | One registered seller |
| `geolocation` | One coordinate reading for a ZIP prefix |
| `category_translation` | One category name translation |
