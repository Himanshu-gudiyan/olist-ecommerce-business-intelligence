"""
dashboard_utils.py
==================
Shared data loading, KPI calculations, styling constants and chart helpers
used by all Streamlit dashboard pages.
"""

import os
import io
import warnings
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT     = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC_DIR = os.path.join(ROOT, "data", "processed")

# ---------------------------------------------------------------------------
# Brand colours
# ---------------------------------------------------------------------------
CLR_PRIMARY   = "#2563EB"
CLR_SECONDARY = "#7C3AED"
CLR_SUCCESS   = "#059669"
CLR_WARNING   = "#D97706"
CLR_DANGER    = "#DC2626"
CLR_MUTED     = "#6B7280"
CLR_BG        = "#F8FAFC"

PALETTE = [
    "#2563EB", "#7C3AED", "#059669", "#D97706", "#DC2626",
    "#0891B2", "#BE185D", "#4B5563", "#CA8A04", "#0D9488",
    "#6366F1", "#F43F5E", "#10B981", "#F97316", "#8B5CF6",
]

PLOTLY_TEMPLATE = "plotly_white"

# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600)
def load_orders() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(PROC_DIR, "orders_enriched.csv"), low_memory=False)
    for col in ["order_purchase_timestamp", "order_delivered_customer_date",
                "order_estimated_delivery_date", "order_approved_at"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    df["is_delayed"] = pd.to_numeric(df["is_delayed"], errors="coerce")
    return df


@st.cache_data(ttl=3600)
def load_items() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(PROC_DIR, "order_items_enriched.csv"), low_memory=False)
    df["order_purchase_timestamp"] = pd.to_datetime(
        df["order_purchase_timestamp"], errors="coerce"
    )
    return df


@st.cache_data(ttl=3600)
def load_customers() -> pd.DataFrame:
    return pd.read_csv(os.path.join(PROC_DIR, "customer_analytics.csv"), low_memory=False)


@st.cache_data(ttl=3600)
def load_products() -> pd.DataFrame:
    return pd.read_csv(os.path.join(PROC_DIR, "product_analytics.csv"), low_memory=False)


@st.cache_data(ttl=3600)
def load_sellers() -> pd.DataFrame:
    return pd.read_csv(os.path.join(PROC_DIR, "seller_analytics.csv"), low_memory=False)


@st.cache_data(ttl=3600)
def load_reviews() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(PROC_DIR, "order_reviews_clean.csv"), low_memory=False)
    df["review_creation_date"] = pd.to_datetime(df["review_creation_date"], errors="coerce")
    return df


@st.cache_data(ttl=3600)
def load_payments() -> pd.DataFrame:
    return pd.read_csv(os.path.join(PROC_DIR, "order_payments_clean.csv"), low_memory=False)


@st.cache_data(ttl=3600)
def load_all() -> dict:
    return {
        "orders":    load_orders(),
        "items":     load_items(),
        "customers": load_customers(),
        "products":  load_products(),
        "sellers":   load_sellers(),
        "reviews":   load_reviews(),
        "payments":  load_payments(),
    }


# ---------------------------------------------------------------------------
# Filter helpers
# ---------------------------------------------------------------------------

def apply_order_filters(
    orders: pd.DataFrame,
    date_range: tuple | None = None,
    customer_states: list | None = None,
    order_statuses: list | None = None,
    payment_types: list | None = None,
) -> pd.DataFrame:
    df = orders.copy()
    if date_range and date_range[0] and date_range[1]:
        start = pd.Timestamp(date_range[0])
        end   = pd.Timestamp(date_range[1])
        df = df[
            (df["order_purchase_timestamp"] >= start) &
            (df["order_purchase_timestamp"] <= end)
        ]
    if customer_states:
        df = df[df["customer_state"].isin(customer_states)]
    if order_statuses:
        df = df[df["order_status"].isin(order_statuses)]
    return df


def apply_item_filters(
    items: pd.DataFrame,
    date_range: tuple | None = None,
    customer_states: list | None = None,
    categories: list | None = None,
    seller_states: list | None = None,
    order_statuses: list | None = None,
) -> pd.DataFrame:
    df = items.copy()
    if date_range and date_range[0] and date_range[1]:
        start = pd.Timestamp(date_range[0])
        end   = pd.Timestamp(date_range[1])
        df = df[
            (df["order_purchase_timestamp"] >= start) &
            (df["order_purchase_timestamp"] <= end)
        ]
    if categories:
        df = df[df["product_category_name_english"].isin(categories)]
    if seller_states:
        df = df[df["seller_state"].isin(seller_states)]
    if order_statuses:
        df = df[df["order_status"].isin(order_statuses)]
    return df


# ---------------------------------------------------------------------------
# KPI calculations
# ---------------------------------------------------------------------------

def calc_kpis(orders: pd.DataFrame, items: pd.DataFrame,
              customers: pd.DataFrame, sellers: pd.DataFrame,
              reviews: pd.DataFrame) -> dict:
    delivered = orders[orders["order_status"] == "delivered"]
    del_items = items[items["order_status"] == "delivered"]

    total_rev   = del_items["item_revenue"].sum()
    aov         = delivered["total_order_revenue"].mean() if len(delivered) > 0 else 0
    has_del     = delivered[delivered["delivery_days"].notna()]
    avg_del     = has_del["delivery_days"].mean() if len(has_del) > 0 else 0
    has_delay   = has_del[has_del["is_delayed"].notna()]
    late_rate   = (
        (has_delay["is_delayed"] == 1.0).mean() * 100
        if len(has_delay) > 0 else 0
    )
    del_rate = len(delivered) / len(orders) * 100 if len(orders) > 0 else 0
    avg_rev  = reviews["review_score"].mean() if len(reviews) > 0 else 0

    return {
        "total_orders":      len(orders),
        "delivered_orders":  len(delivered),
        "total_revenue":     total_rev,
        "aov":               aov,
        "total_customers":   customers["customer_unique_id"].nunique(),
        "total_sellers":     len(sellers),
        "avg_review_score":  avg_rev,
        "delivered_rate":    del_rate,
        "avg_delivery_days": avg_del,
        "late_rate":         late_rate,
        "repeat_buyer_rate": customers["is_repeat_buyer"].mean() * 100,
    }


# ---------------------------------------------------------------------------
# KPI card component
# ---------------------------------------------------------------------------

def kpi_card(col, label: str, value: str, delta: str = "", color: str = CLR_PRIMARY):
    col.markdown(
        f"""
        <div style="
            background:white;
            border-radius:12px;
            padding:20px 16px;
            border-left:4px solid {color};
            box-shadow:0 1px 6px rgba(0,0,0,0.07);
            min-height:110px;
        ">
            <p style="margin:0 0 4px 0;font-size:12px;color:#6B7280;font-weight:600;
                      text-transform:uppercase;letter-spacing:0.5px;">{label}</p>
            <p style="margin:0;font-size:26px;font-weight:700;color:#1E293B;">{value}</p>
            {f'<p style="margin:4px 0 0 0;font-size:12px;color:{CLR_MUTED};">{delta}</p>' if delta else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Download button helper
# ---------------------------------------------------------------------------

def download_csv(df: pd.DataFrame, filename: str, label: str = "Download CSV"):
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    st.download_button(
        label=f"⬇️ {label}",
        data=buf,
        file_name=filename,
        mime="text/csv",
        use_container_width=False,
    )


# ---------------------------------------------------------------------------
# Insight card component
# ---------------------------------------------------------------------------

def insight_box(title: str, body: str, color: str = CLR_PRIMARY):
    st.markdown(
        f"""
        <div style="
            background:#F0F7FF;
            border-left:4px solid {color};
            border-radius:8px;
            padding:14px 18px;
            margin:8px 0;
        ">
            <strong style="color:{color};">💡 {title}</strong>
            <p style="margin:6px 0 0 0;font-size:14px;color:#374151;">{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def recommendation_box(title: str, body: str):
    st.markdown(
        f"""
        <div style="
            background:#F0FDF4;
            border-left:4px solid {CLR_SUCCESS};
            border-radius:8px;
            padding:14px 18px;
            margin:6px 0;
        ">
            <strong style="color:{CLR_SUCCESS};">✅ {title}</strong>
            <p style="margin:6px 0 0 0;font-size:14px;color:#374151;">{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def warning_box(title: str, body: str):
    st.markdown(
        f"""
        <div style="
            background:#FFF7ED;
            border-left:4px solid {CLR_WARNING};
            border-radius:8px;
            padding:14px 18px;
            margin:6px 0;
        ">
            <strong style="color:{CLR_WARNING};">⚠️ {title}</strong>
            <p style="margin:6px 0 0 0;font-size:14px;color:#374151;">{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Shared chart helpers
# ---------------------------------------------------------------------------

def bar_chart(df: pd.DataFrame, x: str, y: str, title: str,
              xlabel: str = "", ylabel: str = "",
              color: str = CLR_PRIMARY, orientation: str = "v",
              text_col: str | None = None) -> go.Figure:
    if orientation == "h":
        fig = px.bar(df, x=y, y=x, orientation="h", title=title,
                     color_discrete_sequence=[color],
                     text=text_col or y,
                     template=PLOTLY_TEMPLATE)
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig.update_layout(xaxis_title=ylabel, yaxis_title=xlabel)
    else:
        fig = px.bar(df, x=x, y=y, title=title,
                     color_discrete_sequence=[color],
                     text=text_col or y,
                     template=PLOTLY_TEMPLATE)
        fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig.update_layout(xaxis_title=xlabel, yaxis_title=ylabel)
    fig.update_layout(
        title_font_size=15,
        title_font_color="#1E293B",
        plot_bgcolor="white",
        margin=dict(t=50, b=40, l=40, r=20),
    )
    return fig


def line_chart(df: pd.DataFrame, x: str, y, title: str,
               xlabel: str = "", ylabel: str = "",
               colors: list | None = None) -> go.Figure:
    ys = y if isinstance(y, list) else [y]
    clrs = colors or PALETTE
    fig = go.Figure()
    for i, col in enumerate(ys):
        fig.add_trace(go.Scatter(
            x=df[x], y=df[col], mode="lines+markers",
            name=col, line=dict(color=clrs[i % len(clrs)], width=2.5),
            marker=dict(size=5),
        ))
    fig.update_layout(
        title=title, title_font_size=15, title_font_color="#1E293B",
        xaxis_title=xlabel, yaxis_title=ylabel,
        template=PLOTLY_TEMPLATE,
        plot_bgcolor="white",
        margin=dict(t=50, b=40, l=40, r=20),
        hovermode="x unified",
    )
    return fig


def pie_chart(values: list, names: list, title: str) -> go.Figure:
    fig = px.pie(values=values, names=names, title=title,
                 color_discrete_sequence=PALETTE,
                 template=PLOTLY_TEMPLATE,
                 hole=0.38)
    fig.update_traces(textposition="inside", textinfo="percent+label",
                      textfont_size=11)
    fig.update_layout(
        title_font_size=15, title_font_color="#1E293B",
        margin=dict(t=50, b=20, l=20, r=20),
        showlegend=True,
    )
    return fig


def histogram_chart(series: pd.Series, title: str, xlabel: str,
                    clip_upper: float | None = None,
                    color: str = CLR_PRIMARY, nbins: int = 50) -> go.Figure:
    data = series.dropna()
    if clip_upper:
        data = data.clip(upper=clip_upper)
    fig = px.histogram(data, nbins=nbins, title=title,
                       color_discrete_sequence=[color],
                       template=PLOTLY_TEMPLATE)
    fig.update_layout(
        xaxis_title=xlabel, yaxis_title="Count",
        title_font_size=15, title_font_color="#1E293B",
        plot_bgcolor="white",
        margin=dict(t=50, b=40, l=40, r=20),
        bargap=0.05,
    )
    return fig


def format_brl(val: float) -> str:
    if val >= 1_000_000:
        return f"R${val/1_000_000:.2f}M"
    if val >= 1_000:
        return f"R${val/1_000:.1f}K"
    return f"R${val:.2f}"
