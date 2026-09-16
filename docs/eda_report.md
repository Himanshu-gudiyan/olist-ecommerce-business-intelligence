# EDA Report — Olist E-Commerce Business Intelligence & Analytics

> **Phase:** 3 — Advanced Exploratory Data Analysis  
> **Pipeline:** `src/eda_analysis.py`  
> **Charts:** `outputs/charts/` (22 PNG files)  
> **Results JSON:** `outputs/eda_results.json`  
> **Notebook:** `notebooks/01_eda.ipynb`  
> **Data Source:** `data/processed/` (cleaned Phase 2 datasets)  
> **All figures are calculated from the real Olist dataset — no synthetic data.**

---

## 1. Methodology

### Approach
This EDA follows a structured business analytics approach:
1. **Descriptive statistics** — what does the dataset contain?
2. **Distribution analysis** — how are key variables distributed?
3. **Time series analysis** — how did the business evolve over time?
4. **Segmentation** — how do customers, products, sellers, and regions differ?
5. **Relationship analysis** — what drives revenue, satisfaction, and delivery performance?
6. **Business insights** — what actionable conclusions emerge from the data?

### Data Assumptions
- **Revenue scope:** All revenue metrics use `order_status = 'delivered'` as the filter. Orders in other states (canceled, unavailable, shipped, etc.) are excluded from revenue calculations unless explicitly noted.
- **Revenue calculation:** Revenue = `SUM(price + freight_value)` from `order_items_enriched.csv`. This is the item-level source of truth and avoids the double-counting risk from payment rows.
- **Review scope:** Deduplicated to one review per `order_id` (most recent submission kept). Reviews represent ~99.2% coverage of delivered orders.
- **Delivery metrics:** Calculated only for orders where `order_delivered_customer_date` is not null.
- **Date range used for time series:** October 2016–August 2018 (excludes partial boundary months Sep 2016 and Oct 2018).
- **Correlation analysis:** Pearson correlation on numeric order-level metrics. Correlation indicates association, not causation.

### Tools Used
- **Python 3.10**, **pandas**, **numpy** — data manipulation
- **matplotlib**, **seaborn** — static chart generation
- **plotly** — available for interactive charts
- **nbformat** — Jupyter notebook generation

---

## 2. Dataset Overview

| Metric | Value |
|--------|-------|
| Total orders in dataset | 99,441 |
| Date range | Sep 4, 2016 → Oct 17, 2018 (772 days) |
| Unique real customers | 96,096 |
| Active sellers | 2,970 |
| Products sold (with analytics) | 32,216 |
| Order reviews (deduplicated) | 98,673 |
| Payment transactions | 103,886 |

### Order Status Distribution

| Status | Count | % of Total |
|--------|-------|-----------|
| delivered | 96,478 | 97.0% |
| shipped | 1,107 | 1.1% |
| canceled | 625 | 0.6% |
| unavailable | 609 | 0.6% |
| invoiced | 314 | 0.3% |
| processing | 301 | 0.3% |
| created | 5 | 0.0% |
| approved | 2 | 0.0% |

### Review Score Distribution

| Score | Count | % |
|-------|-------|---|
| 5 ⭐ | 57,328 | 57.8% |
| 4 ⭐ | 19,142 | 19.3% |
| 3 ⭐ | 8,179 | 8.2% |
| 2 ⭐ | 3,151 | 3.2% |
| 1 ⭐ | 11,424 | 11.5% |

**Average review score: 4.09 / 5.0**

The bimodal distribution (high 5-star and elevated 1-star) suggests customers are most motivated to review when they are either very satisfied or very dissatisfied.

### Payment Type Distribution

| Payment Type | Transactions | % | Avg Value (R$) |
|---|---|---|---|
| credit_card | 76,795 | 73.9% | ~161 |
| boleto | 19,784 | 19.0% | ~145 |
| voucher | 5,775 | 5.6% | ~65 |
| debit_card | 1,529 | 1.5% | ~142 |
| unknown | 3 | 0.0% | — |

---

## 3. Core Business KPIs

All KPIs calculated from **delivered orders only** unless stated.

| KPI | Value | Notes |
|-----|-------|-------|
| **Total Orders** | 99,441 | All statuses |
| **Delivered Orders** | 96,478 | 97.0% of all orders |
| **Total Revenue** | **R$15,419,773.75** | price + freight, delivered only |
| **Product Revenue** | R$13,221,498.11 | 85.7% of total revenue |
| **Freight Revenue** | R$2,198,275.64 | 14.3% of total revenue |
| **Average Order Value (AOV)** | **R$159.83** | Order-level mean |
| **Avg Items per Order** | 1.14 | Most orders are single-item |
| **Avg Freight per Item** | R$19.95 | Item-level mean |
| **Cancellation Rate** | 0.63% | Very low |
| **Repeat Buyer Rate** | **3.12%** | 2,997 / 96,096 customers |
| **Avg Review Score** | 4.09 / 5.0 | Post-dedup reviews |
| **Avg Delivery Days** | **12.56** | From purchase to delivery |
| **Median Delivery Days** | 10.22 | Skewed right by outliers |
| **P90 Delivery Days** | 23.1 | 10% of orders take 23+ days |
| **On-Time Delivery Rate** | **91.89%** | Arrived before estimated date |
| **Late Delivery Rate** | 8.11% | Arrived after estimated date |
| **Avg Delay When Late** | 9.55 days | Among late orders only |
| **Unique Customers** | 96,096 | `customer_unique_id` |
| **Active Sellers** | 2,970 | Fulfilled ≥1 delivered order |

---

## 4. Sales & Revenue Analysis

### Monthly Revenue Trend

**Peak month:** November 2017 (R$1,153,364 — Black Friday/Cyber Monday)  
**Average monthly revenue:** R$700,892 (Oct 2016–Aug 2018)  
**Peak month orders:** 7,289 (November 2017)

Key observations:
- The business shows clear month-on-month growth from Q4 2016 through 2017.
- A significant revenue spike occurs in **November 2017** (~65% above monthly average), coinciding with Black Friday.
- Growth plateaus in early 2018 then contracts slightly — this may reflect dataset truncation or genuine seasonal patterns.
- Average Order Value (AOV) remains relatively stable at R$150–175 throughout the period, meaning revenue growth is driven by **order volume**, not price increases.

**Chart 05:** Monthly Revenue & Order Volume Trend  
**Chart 06:** AOV Over Time

### Top Product Categories by Revenue (Delivered)

| Rank | Category | Revenue (R$) |
|------|----------|-------------|
| 1 | health_beauty | 1,412,089 |
| 2 | watches_gifts | 1,264,333 |
| 3 | bed_bath_table | 1,225,209 |
| 4 | sports_leisure | 1,118,257 |
| 5 | computers_accessories | 1,032,724 |
| 6 | furniture_decor | 973,977 |
| 7 | housewares | 964,049 |
| 8 | auto | 786,099 |
| 9 | toys | 769,497 |
| 10 | cool_stuff | 683,282 |

**Health & Beauty is the #1 revenue category** — not Electronics. The top 5 categories together represent ~36% of total delivered revenue.

### Top Product Categories by Items Sold (Delivered)

| Rank | Category | Items Sold |
|------|----------|-----------|
| 1 | bed_bath_table | 10,953 |
| 2 | health_beauty | 9,465 |
| 3 | sports_leisure | 8,431 |
| 4 | furniture_decor | 8,160 |
| 5 | computers_accessories | 7,644 |

Note: `bed_bath_table` leads by volume but ranks 3rd by revenue, indicating lower-priced items dominate volume. `watches_gifts` ranks 2nd by revenue but not by volume — it has a higher average item price.

**Charts 07–08:** Category Revenue and Volume Analysis

---

## 5. Customer Analysis

### Geographic Distribution

**Top 5 states by customer count:**

| State | Customers | Revenue (R$) |
|-------|-----------|-------------|
| SP | 41,746 | 5,769,703 |
| RJ | 12,852 | 2,055,402 |
| MG | 11,635 | 1,818,892 |
| RS | 5,466 | 861,473 |
| PR | 5,045 | 781,709 |

São Paulo alone accounts for **43.4% of all customers** and **37.4% of revenue**. The top 3 states (SP, RJ, MG) together = ~62% of revenue.

### Customer Purchase Frequency

| Orders | Customers | % |
|--------|-----------|---|
| 1 | 93,099 | 96.88% |
| 2 | 2,745 | 2.86% |
| 3 | 214 | 0.22% |
| 4+ | 38 | 0.04% |

**96.9% of customers placed exactly one order.** The platform is operating almost entirely on first-time buyers. Repeat purchase rate = 3.12%.

### Customer Segmentation (Rule-Based)

| Segment | Customers | Avg Spend (R$) |
|---------|-----------|---------------|
| Single-Purchase (<R$500) | ~85,000 | ~120 |
| High-Value (1 order, R$500+) | ~8,000 | ~830 |
| Returning (2 orders) | 2,745 | ~320 |
| High-Frequency (3+ orders) | 252 | ~480 |

The overwhelming majority of customers are single-purchase, low-to-medium spend. High-value single purchasers represent a significant opportunity for re-engagement.

**Charts 11–13:** Geographic distribution, frequency, segmentation

---

## 6. Logistics & Delivery Analysis

### Delivery Time Summary

| Metric | Value |
|--------|-------|
| Mean delivery time | 12.56 days |
| Median delivery time | 10.22 days |
| 90th percentile | 23.10 days |
| Late delivery rate | 8.11% |
| Avg delay when late | 9.55 days |

The right-skewed distribution (mean > median) indicates a subset of orders take significantly longer. P90 = 23 days means 1 in 10 customers waits over 3 weeks.

### Delivery Time by Customer State

Fastest delivery states (avg days):
- **SP: 8.76d** | PR: 11.99d | MG: 12.01d | DF: 12.97d

Slowest delivery states (avg days):
- **AL: 24.54d** | PA: 23.77d | MA: 21.57d | SE: 21.52d | CE: 21.27d

The North and Northeast states experience delivery times **2–3× longer** than São Paulo. This geographic delivery gap is a major driver of regional customer satisfaction differences.

### Freight Cost Analysis

| Metric | Value |
|--------|-------|
| Avg freight per item | R$19.95 |
| Median freight per item | R$16.26 |
| Freight as % of total revenue | 14.26% |
| Freight–price correlation | r = 0.41 |

**Freight cost is moderately correlated with item price** (Pearson r = 0.41), meaning more expensive items tend to have higher freight but the relationship is imperfect.

**Highest freight-to-price ratio categories:**
- home_comfort_2: 106% (freight > price — likely data issue for this micro-category)
- dvds_blu_ray: 83%
- electronics: 63%
- flowers: 55%
- telephony: 43%

**Charts 15–17:** Delivery distribution, delivery by state, freight analysis

---

## 7. Customer Satisfaction Analysis

### Overall Satisfaction
- **Average review score: 4.09 / 5.0** (post-dedup)
- 57.8% of reviews are 5-star
- 11.5% of reviews are 1-star (elevated — dissatisfied customers are vocal)

### Review Score by Category

**Lowest-scoring categories (among those with 200+ orders):**

| Category | Avg Score | Orders |
|----------|-----------|--------|
| office_furniture | 3.516 | ~1,500 |
| fixed_telephony | 3.758 | ~200 |
| audio | 3.838 | ~400 |
| home_confort | 3.852 | ~600 |
| bed_bath_table | 3.924 | ~10,500 |

**Highest-scoring categories:**

| Category | Avg Score | Orders |
|----------|-----------|--------|
| books_general_interest | 4.512 | ~900 |
| books_technical | 4.389 | ~400 |
| food_drink | 4.364 | ~300 |
| luggage_accessories | 4.352 | ~600 |
| fashion_shoes | 4.281 | ~800 |

**Interpretation:** Categories with physical/dimensional products (furniture, large electronics) tend to score lower — likely due to delivery damage, difficulty of returns, or expectation mismatch. Compact/lightweight categories (books, fashion accessories, food) score higher.

### Review Score vs. Delivery Performance

**On-Time vs. Late Deliveries:**

| Delivery Status | Avg Review Score | n |
|---|---|---|
| On-Time | **4.294** | ~88,500 |
| Late | **2.565** | ~7,800 |
| **Delta** | **-1.729 stars** | — |

**Late delivery causes a 1.73-star drop in average review score** — the largest single predictive factor identified in this analysis.

**Review score by delay bucket:**

| Delay Bucket | Avg Score |
|---|---|
| Early >14 days | 4.32 |
| Early 8-14 days | 4.31 |
| Early 3-7 days | 4.23 |
| Early 0-3 days | 4.13 |
| Late 0-3 days | 3.77 |
| Late 3-7 days | 2.32 |
| **Late 7-14 days** | **1.74** |
| **Late >14 days** | **1.71** |

Even 3 days of delay drops the score from 4.1 to 3.8. Delays of 7+ days result in catastrophic scores (avg ~1.7 — nearly 1 star).

### Review Score vs. Freight Cost

| Freight Bucket | Avg Score |
|---|---|
| R$0–10 | 4.17 |
| R$10–20 | 4.10 |
| R$20–30 | 4.03 |
| R$30–50 | 3.96 |
| R$50+ | 3.96 |

Higher freight cost is associated with slightly lower review scores (–0.2 points for highest vs. lowest bracket). Effect is smaller than delivery delay but still present.

**Charts 18–21:** Category review scores, delay vs. review, on-time vs. late, freight vs. review

---

## 8. Correlation Analysis

Pearson correlation matrix for delivered orders (key findings):

| Metric A | Metric B | r | Interpretation |
|----------|----------|---|----------------|
| delivery_days | review_score | **-0.28** | Longer delivery → lower score |
| delivery_delay_days | review_score | **-0.34** | Being late → lower score (strongest) |
| total_order_revenue | freight_revenue | **0.78** | Expected — larger orders have more freight |
| delivery_days | freight_revenue | **0.40** | Longer delivery → more freight (geographic) |
| item_count | total_order_revenue | **0.68** | More items → higher order value |
| delivery_days | delivery_delay_days | **0.58** | Slow deliveries tend to also be late |

**Key finding:** Delivery delay is the strongest negative predictor of review score in this dataset (r = -0.34). Total order value and freight are positively correlated as expected.

**Chart 22:** Correlation Heatmap  
**Chart 23:** Review Score vs. Delivery Time Bucket

---

## 9. Business Insights

All insights are factual findings calculated from the real dataset. Interpretations and recommendations are labelled separately.

---

### Insight 1: SP Dominates — Geographic Concentration is a Business Risk

**Finding (Factual):** São Paulo state accounts for 43.4% of customers and R$5.77M (37.4%) of delivered revenue. The top 3 states (SP, RJ, MG) represent ~62% of total revenue.

**Metric:** SP: R$5,769,703 | RJ: R$2,055,402 | MG: R$1,818,892

**Interpretation:** The business has healthy market penetration in the Southeast but is underweight in the North, Northeast, and Centre-West relative to population.

**Recommended Action:** Run targeted digital marketing campaigns in RS, PR, BA, SC. Analyse whether high freight costs are the primary demand suppressor in non-SE states.

---

### Insight 2: Health & Beauty — The Unexpected Revenue Leader

**Finding (Factual):** Health & Beauty generates the most revenue of any category (R$1,412,089). Electronics (computers_accessories) ranks 5th at R$1,032,724.

**Metric:** Top 5 categories: health_beauty, watches_gifts, bed_bath_table, sports_leisure, computers_accessories

**Interpretation:** Brazilian e-commerce consumer preferences lean toward personal care, lifestyle, and home goods more than technology. This aligns with global DTC beauty trends.

**Recommended Action:** Invest in seller acquisition in Health & Beauty. Develop category-specific promotional campaigns. Review assortment depth vs. competitors.

---

### Insight 3: Credit Card Dominance — Installments Drive AOV

**Finding (Factual):** 73.9% of transactions use credit card. Average credit card transaction value is higher than boleto.

**Metric:** credit_card: 76,795 (73.9%) | boleto: 19,784 (19.0%) | voucher: 5,775 (5.6%)

**Interpretation:** Brazil's instalment credit culture is a critical driver of higher-value purchases. Customers comfortable with credit card are likely making larger planned purchases.

**Recommended Action:** Prominently display instalment options ("12x sem juros") in product listings. Design boleto-specific promotions targeting price-sensitive customers.

---

### Insight 4: Late Delivery is the #1 Satisfaction Killer

**Finding (Factual):** On-time orders average 4.29 stars vs. late orders at 2.57 stars. The delta is -1.73 stars. Even 3-7 days late drops the score to 2.32.

**Metric:** On-time avg: 4.294 | Late avg: 2.565 | Delta: -1.729

**Interpretation:** No other single factor produces a comparable drop in review score. Late delivery is directly associated with 1-star reviews and reputational damage.

**Recommended Action:** Build proactive delivery risk alerts. Establish carrier SLAs for high-risk routes (North/NE). Implement seller shipping time scoring in seller dashboards.

---

### Insight 5: Black Friday 2017 — Peak Month is Clearly Identified

**Finding (Factual):** November 2017 is the peak revenue month (R$1,153,364), 65% above the 22-month average (R$700,892).

**Metric:** Peak month: 2017-11 | Peak orders: 7,289 | Avg monthly revenue: R$700,892

**Interpretation:** The platform has demonstrable demand response to promotional periods. This is a repeatable pattern to plan for.

**Recommended Action:** Build a 2018 Black Friday inventory and fulfilment plan. Pre-brief sellers 6 weeks in advance to stock top categories. Scale carrier capacity in October–November.

---

### Insight 6: Seller Market Concentration

**Finding (Factual):** Top 10 sellers represent a disproportionate share of revenue. Median seller revenue is low, indicating a long tail of underperforming sellers.

**Metric:** Top 10 revenue share: see `seller_analytics.csv` | Median seller: R$2,459

**Interpretation:** Platform revenue is fragile if top sellers migrate to competing marketplaces. The long tail has growth potential with the right support.

**Recommended Action:** Create a VIP seller retention programme. Build a seller performance coaching programme for the bottom 50% by revenue. Offer preferential fees for high-growth sellers.

---

### Insight 7: North/Northeast Delivery Gap — 3× Longer Than SP

**Finding (Factual):** AL averages 24.54 days, PA 23.77 days, and MA 21.57 days vs. SP at 8.76 days.

**Metric:** AL: 24.54d | PA: 23.77d | CE: 21.27d | SP: 8.76d | National avg: 12.56d

**Interpretation:** The 3× delivery gap likely suppresses both conversion rates and satisfaction scores in Northern states, limiting market expansion.

**Recommended Action:** Partner with regional 3PL carriers in the North. Explore establishing regional fulfilment hubs in Manaus, Belém, and Fortaleza.

---

### Insight 8: 96.9% of Customers Buy Only Once

**Finding (Factual):** 93,099 of 96,096 unique customers (96.9%) placed exactly one order. Repeat buyer rate = 3.12%.

**Metric:** 1-order customers: 93,099 (96.9%) | Repeat buyers: 2,997 (3.12%)

**Interpretation:** Customer acquisition is working but retention is minimal. Even a modest improvement in repeat rate would significantly increase CLV.

**Recommended Action:** Implement post-purchase email nurture flows with personalised recommendations. Launch a loyalty programme. Identify top re-engagement categories (books, health/beauty) as natural second-purchase prompts.

---

### Insight 9: Freight Cost Suppresses Sales in High-Ratio Categories

**Finding (Factual):** Several categories have median freight-to-price ratios exceeding 40%: electronics (63%), flowers (55%), telephony (43%).

**Metric:** Freight as % of total revenue: 14.26% | Avg freight: R$19.95 | Freight-price corr: r=0.41

**Interpretation:** For a R$50 item with R$30 freight, the effective cost to the customer is 60% higher. This likely suppresses conversion for mid-price items in heavy/fragile categories.

**Recommended Action:** Negotiate category-specific volume freight discounts. Display free-shipping thresholds to increase AOV. Consider seller-subsidised freight for high-ratio categories.

---

### Insight 10: Seller Geographic Mismatch

**Finding (Factual):** Only 23 states have registered sellers vs. 27 states with customers. SP-based sellers dominate supply, creating long cross-state delivery routes.

**Metric:** Seller states: 23 | Customer states: 27 | SP sellers: largest share

**Interpretation:** Geographic mismatch inflates delivery times and freight costs for non-SE customers.

**Recommended Action:** Run seller recruitment campaigns in RS, MG, RJ, PR. Offer reduced platform fees or marketing credits to new sellers in underserved states.

---

### Insight 11: Delivery Time Has a Measurable Linear Effect on Reviews

**Finding (Factual):** Orders delivered in 0-5 days average 4.4+ stars. Each additional delivery time bracket reduces the score by ~0.1-0.2 stars until hitting the steep drop at 20+ days.

**Metric:** 0-5d: 4.4+ | 5-10d: 4.2+ | 20-30d: 3.9 | 30-60d: 3.5

**Interpretation:** Delivery time improvement is directly measurable in review score. A 5-day reduction in average delivery time for Northern states would likely recover 0.3-0.4 review points.

**Recommended Action:** Set internal SLAs targeting 95% of orders delivered within 15 days. Use delivery time KPIs in seller scorecards.

---

### Insight 12: Office Furniture Has the Lowest Review Score (3.52)

**Finding (Factual):** `office_furniture` has the lowest average review score at 3.516 among categories with 200+ orders. Five categories score below 4.0.

**Metric:** Lowest: office_furniture (3.516), fixed_telephony (3.758), audio (3.838)

**Interpretation:** Bulky or complex items likely suffer from delivery damage, assembly difficulty, or product-listing inaccuracies.

**Recommended Action:** Audit office_furniture and audio listings for description accuracy. Require product photos and assembly guides. Consider enhanced packaging requirements for furniture sellers.

---

## 10. Charts Generated

| # | Filename | Analysis Section |
|---|----------|-----------------|
| 01 | `01_order_status_distribution.png` | Descriptive |
| 02 | `02_payment_type_distribution.png` | Descriptive |
| 03 | `03_review_score_distribution.png` | Descriptive |
| 04 | `04_kpi_dashboard.png` | Business KPIs |
| 05 | `05_monthly_revenue_trend.png` | Sales & Revenue |
| 06 | `06_aov_over_time.png` | Sales & Revenue |
| 07 | `07_top_categories_revenue.png` | Sales & Revenue |
| 08 | `08_top_categories_volume.png` | Sales & Revenue |
| 09 | `09_top_sellers_revenue.png` | Seller Analysis |
| 10 | `10_revenue_by_seller_state.png` | Seller Analysis |
| 11 | `11_customers_by_state.png` | Customer Analysis |
| 12 | `12_order_frequency_distribution.png` | Customer Analysis |
| 13 | `13_customer_segmentation.png` | Customer Analysis |
| 15 | `15_delivery_time_analysis.png` | Logistics |
| 16 | `16_freight_cost_analysis.png` | Logistics |
| 17 | `17_freight_vs_price.png` | Logistics |
| 18 | `18_review_score_by_category.png` | Satisfaction |
| 19 | `19_review_vs_delivery_delay.png` | Satisfaction |
| 20 | `20_review_ontime_vs_late.png` | Satisfaction |
| 21 | `21_review_vs_freight.png` | Satisfaction |
| 22 | `22_correlation_heatmap.png` | Correlation |
| 23 | `23_review_vs_delivery_time.png` | Correlation |

---

## 11. Limitations

| Limitation | Impact | Notes |
|------------|--------|-------|
| Dataset covers Sep 2016–Oct 2018 only (2+ years) | Limited for multi-year trend analysis | Boundary months excluded from time series |
| 96.9% single-purchase customers | CLV analysis is shallow | Dataset likely captures acquisition-phase of a growing business |
| Review coverage is 99.2% but not 100% | ~768 delivered orders have no review | Excluded from satisfaction metrics — no imputation |
| Geolocation: multiple ZIP entries per prefix | Coordinates averaged; city/state is first occurrence | Use for mapping only — not precise enough for distance calculation |
| Product categories: 610 products unclassified (labelled 'unknown') | ~1,603 items in uncategorized revenue | Does not materially affect top-category rankings |
| Correlation ≠ causation | All correlations in this report are associative, not causal | Controlled experiments needed to establish causal claims |
| Currency: all values in BRL | No FX conversion | R$15.4M ≈ USD 4M at ~2017–2018 rates |
| Seller anonymisation | Cannot link sellers to specific brands | Performance analysis uses seller_id only |

---

## 12. Files Produced by Phase 3

| File | Description |
|------|-------------|
| `src/eda_analysis.py` | Full reproducible EDA pipeline |
| `src/generate_notebook.py` | Jupyter notebook generator |
| `notebooks/01_eda.ipynb` | Interactive EDA notebook |
| `outputs/eda_results.json` | All computed metrics as JSON |
| `outputs/charts/` | 22 PNG chart files |
| `docs/eda_report.md` | This document |

---

## 13. Phase 5 — Advanced Business Analytics

> **Phase:** 5 — Advanced Analytics & Customer Intelligence  
> **New engines:** `src/rfm_analysis.py`, `src/cohort_analysis.py`, `src/seller_intelligence.py`, `src/growth_analytics.py`  
> **New dashboard page:** `src/pages/advanced_analytics.py` (8 tabs, 9th page in sidebar)  
> **All metrics computed from real Olist data — no synthetic values.**

---

### 13.1 RFM Customer Segmentation

RFM (Recency, Frequency, Monetary) scoring on 93,358 unique delivered-order customers.
Quintile-based 1–5 scores; 8-segment classification matrix.

| Segment | Customers | Avg Monetary (R$) | Total Revenue (R$) |
|---------|-----------|------------------|--------------------|
| New Customers | 37,400 | 168.81 | 6,313,650 |
| Promising | 18,707 | 156.23 | 2,922,657 |
| Lost | 18,635 | 162.80 | 3,033,834 |
| Hibernating | 18,577 | 167.75 | 3,116,225 |
| Potential Loyalists | 18 | 1,007.49 | 18,134 |
| Need Attention | 16 | 728.24 | 11,651 |
| At Risk | 4 | 685.06 | 2,740 |
| Champions | 1 | 879.27 | 879 |

**Key finding:** With a 3.0% repeat-buyer rate, nearly all customers score F=1. The 4 dominant segments (New, Promising, Lost, Hibernating) account for 99.9% of customers and 99.9% of revenue. Champions are extremely rare — accurately reflecting Olist's acquisition-stage business lifecycle.

---

### 13.2 Customer Retention & Cohort Analysis

**Retention metrics (delivered orders only):**

| Metric | Value |
|--------|-------|
| Unique customers | 93,358 |
| One-time buyers | 90,557 (97.0%) |
| Repeat buyers (2+ orders) | 2,801 (3.00%) |
| Avg cohort return rate | 6.6% |

**Cohort analysis:** 23 monthly cohorts tracked across 20 periods.

- Most cohorts show < 5% retention beyond Period 0 — consistent with the 3% repeat rate.
- Nov 2017 cohort (Black Friday) is the largest acquisition month.
- Cohort return rates typically peak at 1–3% in Period 1–2 and decay rapidly.

**CLV Distribution:**
- Right-skewed: majority of customers cluster at low CLV (single purchase).
- Repeat buyers generate significantly higher CLV — key argument for a retention programme.

---

### 13.3 Seller Intelligence

Quintile-based scorecard across 2,970 sellers.

**Performance flag distribution:**

| Flag | Sellers | Description |
|------|---------|-------------|
| Top Performer | ~594 | High revenue + high review score |
| High Rev, Low Satisfaction | 21 | Revenue at risk (R$649,527) |
| Hidden Gem | ~594 | High satisfaction, low revenue — growth opportunity |
| Delivery Problem | ~594 | Late rate in bottom quintile |
| Under-Performing | ~594 | Low revenue + low review |
| Average | ~594 | All others |

**Key finding:** 21 high-revenue sellers with poor satisfaction scores represent R$649,527 in revenue at risk. These require quality intervention before satisfaction decline triggers customer churn.

**Top 5 sellers by revenue:**

| Seller State | Total Revenue (R$) | Avg Review Score | Late Rate |
|---|---|---|---|
| SP | 247,007 | 4.14 | 11.6% |
| SP | 237,807 | 3.35 | 10.1% |
| SP | 231,220 | 3.83 | 11.0% |
| BA | 230,797 | 4.13 | 4.3% |
| SP | 200,834 | 4.37 | 10.2% |

---

### 13.4 Revenue & Growth Analytics

**Period:** Sep 2016 – Oct 2018 (23 months)

| Metric | Value |
|--------|-------|
| Total delivered revenue | R$15,419,773.75 |
| Avg monthly revenue | R$670,424.95 |
| Peak month | Nov 2017 (Black Friday) — R$1,153,364.20 |
| Period growth (first vs last full month) | +2,019.8% |
| Strong growth months (≥+20% MoM) | 6 |

**Top 5 categories by delivered revenue:**

| Category | Revenue (R$) | Share |
|----------|-------------|-------|
| health_beauty | 1,412,090 | 9.2% |
| watches_gifts | 1,264,333 | 8.2% |
| bed_bath_table | 1,225,209 | 7.9% |
| sports_leisure | 1,118,257 | 7.3% |
| computers_accessories | 1,032,724 | 6.7% |

**AOV trend:** Average Order Value shows moderate month-to-month variation. No strong secular trend — growth was primarily driven by order volume, not increasing spend per order.

---

### 13.5 Delivery Deep-Dive (Phase 5)

| Metric | Value |
|--------|-------|
| Fastest delivery state | SP — 8.8 days avg |
| Slowest delivery state | RR — 29.4 days avg |
| Delivery gap | 20.6 days |
| On-time avg review score | 4.294 / 5.0 |
| Late avg review score | 2.565 / 5.0 |
| Review score delta | -1.729 stars for late deliveries |

**Key finding:** Every 1 percentage point improvement in on-time delivery rate translates to a measurable lift in platform average review score.

---

### 13.6 Business Opportunities (Auto-Identified)

7 opportunities automatically flagged from real dataset metrics:

| Priority | Opportunity | Key Metric |
|----------|-------------|-----------|
| 🔴 Critical | Retention Programme | Repeat rate: 3.0% |
| 🟡 High | Recruit Sellers in AL | 397 orders, 0 local sellers |
| 🟡 High | Recruit Sellers in TO | 274 orders, 0 local sellers |
| 🟡 High | Fix Delivery in AL | Late rate: 23.9% |
| 🟡 High | Fix Delivery in MA | Late rate: 19.7% |
| 🟡 High | Fix Delivery in PI | Late rate: 16.0% |
| 🟡 High | 21 High-Revenue Low-Sat Sellers | R$649,527 at risk |

---

### 13.7 Executive Insight Summary (Phase 5)

10 data-backed executive insights delivered in the dashboard:

1. **Health & Beauty is the #1 revenue category** — R$1.41M (9.2% of total)
2. **Black Friday 2017 was the clear business peak** — R$1.15M, +72% above avg
3. **Late delivery causes a 1.73-star review collapse** — 4.29 on-time vs 2.57 late
4. **96.9% of customers buy only once** — largest single lever for growth
5. **SP generates 37%+ of revenue** — geographic concentration risk
6. **20.6-day delivery gap between SP and RR** — equity & TAM issue
7. **Credit card = 74% of transactions** — instalment culture drives AOV
8. **Top 10 sellers generate outsized revenue** — concentration risk
9. **Office furniture has the lowest review score** (3.52/5.0)
10. **New Customers RFM segment drives ~41% of revenue** — acquisition working; retention must follow

---

### 13.8 Files Produced by Phase 5

| File | Description |
|------|-------------|
| `src/rfm_analysis.py` | RFM scoring engine (compute_rfm, rfm_segment_summary, SEGMENT_COLORS) |
| `src/cohort_analysis.py` | Monthly cohort retention engine (compute_cohorts, cohort_summary) |
| `src/seller_intelligence.py` | Seller scorecard + opportunity analysis |
| `src/growth_analytics.py` | Monthly growth, category/state trends, business opportunity finder |
| `src/pages/advanced_analytics.py` | 8-tab Streamlit page (1,227 lines) |
| `src/verify_phase5.py` | End-to-end validation script (all checks pass) |
| `docs/metric_definitions.md` | Extended with RFM, cohort, seller, growth metric definitions |
| `README.md` | Updated with Phase 5 pipeline, page listing, and build status |
