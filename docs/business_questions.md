# Business Questions & Analytics Opportunities
## Olist E-Commerce Business Intelligence & Analytics

> **Source:** Real Olist Brazilian E-Commerce Public Dataset  
> All questions and KPIs are answerable from the actual dataset without synthetic data.

---

## Part 1: Core Business KPIs

All KPIs below are directly computable from the real dataset:

### Sales & Revenue KPIs

| KPI | Description | Primary Tables |
|-----|-------------|---------------|
| **Total Orders** | Count of all unique order IDs | `orders` |
| **Delivered Orders** | Count of orders with status = `delivered` | `orders` |
| **Total Revenue** | Sum of `price` + `freight_value` across all delivered order items | `order_items`, `orders` |
| **Product Revenue** | Sum of `price` only (excluding freight) | `order_items`, `orders` |
| **Freight Revenue** | Sum of `freight_value` only | `order_items`, `orders` |
| **Average Order Value (AOV)** | Total revenue ÷ Total delivered orders | `order_items`, `orders` |
| **Total Items Sold** | Count of rows in `order_items` for delivered orders | `order_items`, `orders` |
| **Average Items per Order** | Total items ÷ Total delivered orders | `order_items`, `orders` |
| **Monthly Revenue** | Revenue grouped by year-month of `order_purchase_timestamp` | `order_items`, `orders` |
| **Revenue by Product Category** | Revenue grouped by `product_category_name_english` | `order_items`, `products`, `category_translation` |
| **Revenue by State (Customer)** | Revenue grouped by `customer_state` | `order_items`, `orders`, `customers` |
| **Revenue by State (Seller)** | Revenue grouped by `seller_state` | `order_items`, `sellers` |
| **Revenue by Seller** | Revenue per `seller_id` | `order_items` |
| **Top-N Products by Revenue** | Products ranked by total revenue | `order_items`, `products` |
| **Top-N Sellers by Revenue** | Sellers ranked by total revenue | `order_items`, `sellers` |

### Customer KPIs

| KPI | Description | Primary Tables |
|-----|-------------|---------------|
| **Total Unique Customers** | Count of distinct `customer_unique_id` | `customers` |
| **Repeat Purchase Rate** | % of customers who placed 2+ orders | `customers` |
| **Customer Lifetime Value (CLV)** | Total revenue per `customer_unique_id` | `customers`, `orders`, `order_items` |
| **New Customers per Month** | First-order customers grouped by month | `customers`, `orders` |
| **Customers by State** | Customer count per `customer_state` | `customers` |
| **Orders per Customer** | Distribution of order count per unique customer | `customers`, `orders` |

### Payment KPIs

| KPI | Description | Primary Tables |
|-----|-------------|---------------|
| **Payment Method Distribution** | % share of each `payment_type` | `order_payments` |
| **Average Installments** | Avg `payment_installments` by payment type | `order_payments` |
| **Orders Using Multiple Payment Methods** | Count of orders with `payment_sequential > 1` | `order_payments` |
| **Average Payment Value** | Avg `payment_value` per transaction | `order_payments` |
| **Voucher Usage Rate** | % of orders using vouchers | `order_payments` |

### Delivery & Logistics KPIs

| KPI | Description | Primary Tables |
|-----|-------------|---------------|
| **Average Delivery Time (days)** | `order_delivered_customer_date` − `order_purchase_timestamp` | `orders` |
| **On-Time Delivery Rate** | % where `delivered_customer_date` ≤ `estimated_delivery_date` | `orders` |
| **Average Delivery Delay (days)** | `delivered_customer_date` − `estimated_delivery_date` (positive = late) | `orders` |
| **Fastest/Slowest Delivery States** | Avg delivery time by customer or seller state | `orders`, `customers`, `order_items`, `sellers` |
| **Carrier Handoff Time** | `order_delivered_carrier_date` − `order_approved_at` | `orders` |
| **Approval Time** | `order_approved_at` − `order_purchase_timestamp` | `orders` |
| **Average Freight Cost** | Avg `freight_value` per item or per order | `order_items` |
| **Freight Cost by Product Weight** | Correlation between weight and freight cost | `order_items`, `products` |

### Review & Satisfaction KPIs

| KPI | Description | Primary Tables |
|-----|-------------|---------------|
| **Average Review Score (Overall)** | Mean of `review_score` | `order_reviews` |
| **Review Score Distribution** | Count per score (1–5) | `order_reviews` |
| **Average Review Score by Category** | Mean score per product category | `order_reviews`, `order_items`, `products`, `category_translation` |
| **Average Review Score by Seller** | Mean score per `seller_id` | `order_reviews`, `order_items` |
| **Review Score vs. Delivery Delay** | Correlation between lateness and low scores | `orders`, `order_reviews` |
| **% Orders with 1-Star Reviews** | Count of score=1 ÷ total reviewed orders | `order_reviews` |
| **Review Response Time** | `review_answer_timestamp` − `review_creation_date` | `order_reviews` |
| **Comment Rate** | % of reviews that include a written message | `order_reviews` |

---

## Part 2: 20 Real-World Business Questions

All questions below are fully answerable from the real dataset.

---

### Revenue & Sales

**Q1. Which product categories generate the most revenue (price + freight)?**
- *Join:* `order_items` → `products` → `category_translation`, filter `orders.order_status = 'delivered'`
- *Metric:* SUM(price + freight_value) grouped by `product_category_name_english`

**Q2. How does monthly revenue trend over the dataset's time range (Sep 2016 – Oct 2018)?**
- *Join:* `order_items` → `orders`
- *Metric:* SUM(price + freight_value) grouped by YEAR-MONTH of `order_purchase_timestamp`

**Q3. Which states (by customer location) generate the most sales volume and revenue?**
- *Join:* `orders` → `customers`, `order_items`
- *Metric:* COUNT(orders) + SUM(revenue) grouped by `customer_state`

**Q4. Which individual sellers generate the most revenue, and in which states are they located?**
- *Join:* `order_items` → `sellers`
- *Metric:* SUM(price + freight_value) grouped by `seller_id`, enriched with `seller_state`

**Q5. What is the relationship between product category and average order value?**
- *Join:* `order_items` → `orders` → `products` → `category_translation`
- *Metric:* Total revenue per order ÷ count of orders grouped by category

---

### Customer Behavior

**Q6. What percentage of customers are repeat buyers (placed 2+ orders)?**
- *Table:* `customers` grouped by `customer_unique_id`
- *Metric:* % with count ≥ 2

**Q7. How does the number of repeat buyers change over time — are customers returning more or less in later months?**
- *Join:* `customers` → `orders`, rank by first vs. subsequent purchase dates
- *Metric:* New vs. returning customers per month

**Q8. Which states have the highest customer density and how does their AOV compare?**
- *Join:* `customers` → `orders` → `order_items`
- *Metric:* COUNT(unique_customers) + AVG order value by `customer_state`

---

### Payment Analysis

**Q9. Which payment methods are most popular and do they correlate with order value?**
- *Table:* `order_payments`
- *Metric:* COUNT and AVG payment_value by `payment_type`

**Q10. How many installments do Brazilian customers typically choose, and does the number of installments correlate with total order value?**
- *Table:* `order_payments` (filter to `payment_type = 'credit_card'`)
- *Metric:* Distribution of `payment_installments`; correlation with `payment_value`

**Q11. What fraction of orders use vouchers as a (partial) payment method?**
- *Table:* `order_payments`
- *Metric:* COUNT(order_id where payment_type = 'voucher') ÷ COUNT(all unique order_id)

---

### Delivery Performance

**Q12. What is the average actual delivery time vs. estimated delivery time — and what fraction of orders arrive late?**
- *Table:* `orders`, filter `order_status = 'delivered'`
- *Metric:* AVG(delivered_customer_date − purchase_timestamp); % where delivered > estimated

**Q13. Which states experience the longest average delivery times and highest late-delivery rates?**
- *Join:* `orders` → `customers`
- *Metric:* AVG delivery days + % late grouped by `customer_state`

**Q14. Does the seller's state affect delivery speed — i.e., do customers in the same state as the seller receive orders faster?**
- *Join:* `orders` → `order_items` → `sellers` → `customers`
- *Metric:* AVG delivery days where `seller_state = customer_state` vs. cross-state

**Q15. How has delivery performance changed over time (2016–2018)?**
- *Join:* `orders`
- *Metric:* Monthly AVG(delivery_days) + % on-time over time

---

### Review & Customer Satisfaction

**Q16. What factors are most associated with low review scores (1–2 stars)?**
- *Join:* `order_reviews` → `orders` → `order_items` → `products`
- *Factors to test:* Delivery delay, product category, freight cost, price, seller

**Q17. Which product categories receive the lowest average review scores?**
- *Join:* `order_reviews` → `order_items` → `products` → `category_translation`
- *Metric:* AVG review_score by category, sorted ascending

**Q18. Which sellers have the highest and lowest customer satisfaction scores?**
- *Join:* `order_reviews` → `order_items`
- *Metric:* AVG review_score by `seller_id` (filter sellers with ≥ N orders for significance)

**Q19. Is there a significant drop in review score for orders that arrived late?**
- *Join:* `orders` → `order_reviews`
- *Metric:* AVG review_score for on-time orders vs. late orders; statistical difference

**Q20. What share of reviews include a written comment, and do higher-effort reviews (with text) skew toward positive or negative scores?**
- *Table:* `order_reviews`
- *Metric:* % with `review_comment_message IS NOT NULL`, grouped by score bucket

---

## Part 3: Additional Advanced Analytics Opportunities

These deeper questions are also answerable from the dataset:

| # | Question | Technique |
|---|----------|-----------|
| A1 | What is the seasonal pattern of sales — are there clear peaks? | Time series analysis |
| A2 | Which product categories have the highest freight cost as a % of product price? | Ratio analysis |
| A3 | Do heavy/bulky products receive lower review scores due to delivery difficulty? | Correlation: weight × review_score |
| A4 | Which product categories have the most diverse seller base? | COUNT(distinct seller_id) by category |
| A5 | How concentrated is seller market share — do a few sellers dominate revenue? | Lorenz curve / Gini coefficient |
| A6 | Do customers who pay in more installments have higher order values? | Correlation: installments × order_value |
| A7 | How does freight cost vary by customer state? | AVG freight_value by customer_state |
| A8 | Which cities (customer) have the highest and lowest AOV? | AVG order value by customer_city |
| A9 | Is there a "weekend effect" — do orders placed on weekends have different delivery or review outcomes? | Day-of-week analysis on purchase_timestamp |
| A10 | Which categories have the highest cancellation rate? | Canceled orders ÷ total orders by category |
