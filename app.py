# app.py — Main Streamlit Application Entry Point
"""
Olist E-Commerce Business Intelligence & Analytics Dashboard

Run:
    streamlit run app.py
"""

import os
import sys
import warnings

import pandas as pd
import streamlit as st


# ---------------------------------------------------------------------------
# Basic configuration
# ---------------------------------------------------------------------------
warnings.filterwarnings("ignore")

# Ensure src/ is on path
ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(ROOT, "src")

if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)


# ---------------------------------------------------------------------------
# Page config — MUST be the first Streamlit command
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Olist E-Commerce Analytics",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Existing dashboard utilities
# ---------------------------------------------------------------------------
from dashboard_utils import (
    load_orders,
    load_items,
    load_customers,
    load_products,
    load_sellers,
    load_reviews,
    load_payments,
    CLR_PRIMARY,
    CLR_SUCCESS,
    CLR_WARNING,
    CLR_DANGER,
    CLR_SECONDARY,
)


# ---------------------------------------------------------------------------
# Phase 8 SQL Analytics Data Layer
# ---------------------------------------------------------------------------
from src.phase8_dashboard_data import (
    get_kpis,
    get_monthly_revenue,
    get_category_revenue,
    get_state_revenue,
    get_payment_performance,
    get_delivery_performance,
    get_customer_metrics,
    get_seller_performance,
    get_product_performance,
    get_review_performance,
)


# ============================================================
# PHASE 8 - SQL ANALYTICS TEST
# ============================================================


# ---------------------------------------------------------------------------
# Global CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #F8FAFC; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E293B 0%, #0F172A 100%);
    }
    [data-testid="stSidebar"] * { color: #E2E8F0 !important; }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stMultiSelect label,
    [data-testid="stSidebar"] .stDateInput label { color: #94A3B8 !important; }

    /* Remove default padding */
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }

    /* Headings */
    h1, h2, h3 { color: #1E293B; }

    /* DataFrames */
    .stDataFrame { border-radius: 8px; }

    /* Plotly charts border */
    .js-plotly-plot { border-radius: 10px; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 6px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0;
        font-weight: 600;
    }

    /* Metric cards spacing */
    div[data-testid="metric-container"] { padding: 0; }

    /* Hide Streamlit footer */
    footer { visibility: hidden; }
    #MainMenu { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Load data (cached)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def get_all_data():
    return {
        "orders":    load_orders(),
        "items":     load_items(),
        "customers": load_customers(),
        "products":  load_products(),
        "sellers":   load_sellers(),
        "reviews":   load_reviews(),
        "payments":  load_payments(),
    }


data = get_all_data()
orders    = data["orders"]
items     = data["items"]
customers = data["customers"]
products  = data["products"]
sellers   = data["sellers"]
reviews   = data["reviews"]
payments  = data["payments"]

# ---------------------------------------------------------------------------
# Sidebar — navigation + global filters
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding: 20px 0 10px 0;'>
        <span style='font-size:36px;'>🛒</span>
        <h2 style='margin:6px 0 2px 0; color:white; font-size:18px;'>
            Olist Analytics
        </h2>
        <p style='color:#94A3B8; font-size:12px; margin:0;'>
            E-Commerce Intelligence
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

    # Navigation
    PAGES = {
        "🏢 Executive Overview":     "executive",
        "💰 Sales & Revenue":        "sales",
        "👥 Customer Analysis":      "customers",
        "📦 Product & Categories":   "products",
        "🏪 Seller Performance":     "sellers",
        "🚚 Order & Delivery":       "delivery",
        "⭐ Customer Reviews":       "reviews",
        "🗺️ Geographic Analysis":   "geography",
        "🧠 Advanced Analytics":    "advanced",
    }
    page_label = st.radio(
        "Navigation",
        list(PAGES.keys()),
        label_visibility="collapsed",
    )
    page = PAGES[page_label]

    st.markdown("---")
    st.markdown(
        "<p style='color:#94A3B8;font-size:12px;font-weight:600;text-transform:uppercase;"
        "letter-spacing:0.5px;'>Global Filters</p>",
        unsafe_allow_html=True,
    )

    # Date range
    min_date = orders["order_purchase_timestamp"].min().date()
    max_date = orders["order_purchase_timestamp"].max().date()
    date_range = st.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="date_range",
    )

    # Customer State
    all_cust_states = sorted(orders["customer_state"].dropna().unique().tolist())
    selected_cust_states = st.multiselect(
        "Customer State",
        all_cust_states,
        default=[],
        placeholder="All states",
        key="cust_states",
    )

    # Seller State
    all_sell_states = sorted(sellers["seller_state"].dropna().unique().tolist())
    selected_sell_states = st.multiselect(
        "Seller State",
        all_sell_states,
        default=[],
        placeholder="All seller states",
        key="sell_states",
    )

    # Product Category
    all_cats = sorted(
        items["product_category_name_english"].dropna().unique().tolist()
    )
    selected_cats = st.multiselect(
        "Product Category",
        all_cats,
        default=[],
        placeholder="All categories",
        key="categories",
    )

    # Order Status
    all_statuses = sorted(orders["order_status"].dropna().unique().tolist())
    selected_statuses = st.multiselect(
        "Order Status",
        all_statuses,
        default=[],
        placeholder="All statuses",
        key="order_status",
    )

    # Payment Type
    all_pay_types = sorted(payments["payment_type"].dropna().unique().tolist())
    selected_pay_types = st.multiselect(
        "Payment Type",
        all_pay_types,
        default=[],
        placeholder="All payment types",
        key="pay_types",
    )

    # Review Score
    selected_scores = st.multiselect(
        "Review Score",
        [1, 2, 3, 4, 5],
        default=[],
        placeholder="All scores",
        key="review_scores",
    )

    st.markdown("---")

    # # Reset button
    # if st.button("🔄 Reset All Filters", use_container_width=True):
    #     for key in ["date_range", "cust_states", "sell_states", "categories",
    #                 "order_status", "pay_types", "review_scores"]:
    #         if key in st.session_state:
    #             del st.session_state[key]
    #     st.rerun()

    # st.markdown(
    #     f"<p style='color:#64748B;font-size:11px;text-align:center;margin-top:8px;'>"
    #     f"Data: Sep 2016 – Oct 2018</p>",
    #     unsafe_allow_html=True,
    # )

    # selected_scores = st.multiselect(
    #     "Review Score",
    #     [1, 2, 3, 4, 5],
    #     default=[],
    #     placeholder="All scores",
    #     key="review_scores",
    # )

    # st.markdown("---")


    # -----------------------------------------------------------------------
    # Reset All Filters
    # -----------------------------------------------------------------------
    def reset_all_filters():
        reset_keys = [
            "date_range",
            "cust_states",
            "sell_states",
            "categories",
            "order_status",
            "pay_types",
            "review_scores",
        ]

        for key in reset_keys:
            st.session_state.pop(key, None)

    st.button(
        "🔄 Reset All Filters",
        use_container_width=True,
        on_click=reset_all_filters,
    )

# ---------------------------------------------------------------------------
# Apply global filters
# ---------------------------------------------------------------------------
def safe_date_range(dr):
    if isinstance(dr, (list, tuple)) and len(dr) == 2:
        return dr[0], dr[1]
    return None, None


start_date, end_date = safe_date_range(date_range)

# Filter orders
filtered_orders = orders.copy()
if start_date and end_date:
    filtered_orders = filtered_orders[
        (filtered_orders["order_purchase_timestamp"].dt.date >= start_date) &
        (filtered_orders["order_purchase_timestamp"].dt.date <= end_date)
    ]
if selected_cust_states:
    filtered_orders = filtered_orders[
        filtered_orders["customer_state"].isin(selected_cust_states)
    ]
if selected_statuses:
    filtered_orders = filtered_orders[
        filtered_orders["order_status"].isin(selected_statuses)
    ]

# Filter items
filtered_items = items.copy()
# Sync item filter to matched order_ids
matched_order_ids = set(filtered_orders["order_id"].unique())
filtered_items = filtered_items[filtered_items["order_id"].isin(matched_order_ids)]
if selected_cats:
    filtered_items = filtered_items[
        filtered_items["product_category_name_english"].isin(selected_cats)
    ]
if selected_sell_states:
    filtered_items = filtered_items[
        filtered_items["seller_state"].isin(selected_sell_states)
    ]

# Filter reviews
filtered_reviews = reviews[reviews["order_id"].isin(matched_order_ids)].copy()
if selected_scores:
    filtered_reviews = filtered_reviews[
        filtered_reviews["review_score"].isin(selected_scores)
    ]

# Filter sellers
filtered_sellers = sellers.copy()
if selected_sell_states:
    filtered_sellers = filtered_sellers[
        filtered_sellers["seller_state"].isin(selected_sell_states)
    ]

# Bundle filters dict passed to each page
filters = {
    "orders":           filtered_orders,
    "items":            filtered_items,
    "reviews":          filtered_reviews,
    "date_range":       (start_date, end_date),
    "customer_states":  selected_cust_states or None,
    "seller_states":    selected_sell_states or None,
    "categories":       selected_cats or None,
    "order_statuses":   selected_statuses or None,
    "payment_types":    selected_pay_types or None,
    "review_scores":    selected_scores or None,
}

# ---------------------------------------------------------------------------
# Filter summary banner
# ---------------------------------------------------------------------------
active_filters = []
if selected_cust_states:
    active_filters.append(f"States: {', '.join(selected_cust_states)}")
if selected_cats:
    active_filters.append(f"Categories: {len(selected_cats)} selected")
if selected_statuses:
    active_filters.append(f"Status: {', '.join(selected_statuses)}")
if selected_pay_types:
    active_filters.append(f"Payment: {', '.join(selected_pay_types)}")
if selected_scores:
    active_filters.append(f"Reviews: {selected_scores}")

if active_filters:
    st.info(
        f"🔍 **Active Filters:** {' | '.join(active_filters)}  "
        f"— Showing **{len(filtered_orders):,}** orders "
        f"({len(filtered_orders)/len(orders)*100:.1f}% of total)",
    )

# ---------------------------------------------------------------------------
# Page router
# ---------------------------------------------------------------------------
import importlib

page_modules = {
    "executive": ("pages.executive_overview",  "show"),
    "sales":     ("pages.sales_revenue",       "show"),
    "customers": ("pages.customer_analysis",   "show"),
    "products":  ("pages.product_category",    "show"),
    "sellers":   ("pages.seller_performance",  "show"),
    "delivery":  ("pages.delivery_analysis",   "show"),
    "reviews":   ("pages.reviews_analysis",    "show"),
    "geography": ("pages.geographic_analysis", "show"),
    "advanced":  ("pages.advanced_analytics",  "show"),
}

if page in page_modules:
    mod_path, fn_name = page_modules[page]
    mod = importlib.import_module(mod_path)
    getattr(mod, fn_name)(
        orders, items, customers,
        filtered_sellers, filtered_reviews, payments,
        filters,
    )
