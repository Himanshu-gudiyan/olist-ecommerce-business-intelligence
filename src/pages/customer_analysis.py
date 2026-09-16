"""pages/customer_analysis.py — Customer Analysis page"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dashboard_utils import (
    insight_box, recommendation_box, warning_box, format_brl,
    CLR_PRIMARY, CLR_SECONDARY, CLR_SUCCESS, CLR_WARNING, CLR_DANGER,
    PALETTE, PLOTLY_TEMPLATE, download_csv, kpi_card,
)


def show(orders, items, customers, sellers, reviews, payments, filters):
    st.markdown("## 👥 Customer Analysis")

    df_cust = customers.copy()
    df_ord  = filters["orders"]

    if filters.get("customer_states"):
        df_cust = df_cust[df_cust["customer_state"].isin(filters["customer_states"])]

    delivered = df_ord[df_ord["order_status"] == "delivered"]

    # ── KPIs
    total_cust    = df_cust["customer_unique_id"].nunique()
    repeat_buyers = int(df_cust["is_repeat_buyer"].sum())
    repeat_rate   = df_cust["is_repeat_buyer"].mean() * 100
    avg_spend     = df_cust["total_spend_payment"].mean()

    c1, c2, c3, c4 = st.columns(4)
    kpi_card(c1, "Unique Customers", f"{total_cust:,}", color=CLR_PRIMARY)
    kpi_card(c2, "Repeat Buyers", f"{repeat_buyers:,}",
             delta=f"{repeat_rate:.2f}% of customers", color=CLR_SECONDARY)
    kpi_card(c3, "Avg Customer Spend", f"R${avg_spend:.2f}", color=CLR_SUCCESS)
    kpi_card(c4, "Avg Orders / Customer",
             f"{df_cust['total_orders'].mean():.2f}", color=CLR_WARNING)

    st.markdown("---")

    # ── Customers & Revenue by State
    st.markdown("### Geographic Distribution")
    cust_state = (
        df_cust.groupby("customer_state")
        .agg(n_customers=("customer_unique_id", "count"),
             avg_spend=("total_spend_payment", "mean"))
        .reset_index().sort_values("n_customers", ascending=False)
    )
    rev_state = (
        delivered.groupby("customer_state")["total_order_revenue"]
        .sum().reset_index().rename(columns={"total_order_revenue": "revenue"})
    )
    state_merged = cust_state.merge(rev_state, on="customer_state", how="left").fillna(0)

    col1, col2 = st.columns(2)
    with col1:
        top15 = state_merged.head(15)
        fig1 = px.bar(
            top15[::-1], x="n_customers", y="customer_state",
            orientation="h", text="n_customers",
            color="n_customers",
            color_continuous_scale=["#93C5FD", CLR_PRIMARY],
            template=PLOTLY_TEMPLATE,
            title="Top 15 States — Customer Count",
        )
        fig1.update_coloraxes(showscale=False)
        fig1.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig1.update_layout(
            xaxis_title="Unique Customers", yaxis_title="",
            height=400, margin=dict(t=50, b=30, l=10, r=80),
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        top15_rev = state_merged.sort_values("revenue", ascending=False).head(15)
        fig2 = px.bar(
            top15_rev[::-1], x="revenue", y="customer_state",
            orientation="h",
            text=top15_rev[::-1]["revenue"].apply(format_brl),
            color="revenue",
            color_continuous_scale=["#6EE7B7", CLR_SUCCESS],
            template=PLOTLY_TEMPLATE,
            title="Top 15 States — Revenue (R$)",
        )
        fig2.update_coloraxes(showscale=False)
        fig2.update_traces(textposition="outside")
        fig2.update_layout(
            xaxis_title="Revenue (R$)", yaxis_title="",
            height=400, margin=dict(t=50, b=30, l=10, r=80),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Order Frequency Distribution
    st.markdown("### Customer Purchase Frequency")
    freq = df_cust["total_orders"].value_counts().sort_index().reset_index()
    freq.columns = ["Orders Placed", "Customers"]
    freq["Pct"] = (freq["Customers"] / freq["Customers"].sum() * 100).round(2)

    fig3 = px.bar(
        freq, x="Orders Placed", y="Customers",
        text=freq["Customers"].apply(lambda v: f"{v:,}"),
        color="Orders Placed",
        color_continuous_scale=["#93C5FD", CLR_PRIMARY],
        template=PLOTLY_TEMPLATE,
        title="Customer Purchase Frequency Distribution",
    )
    fig3.update_coloraxes(showscale=False)
    fig3.update_traces(textposition="outside")
    fig3.update_layout(
        xaxis_title="Number of Orders Placed",
        yaxis_title="Number of Customers",
        height=360, margin=dict(t=50, b=40, l=50, r=20),
    )
    st.plotly_chart(fig3, use_container_width=True)

    one_time_pct = freq[freq["Orders Placed"] == 1]["Pct"].values[0] if 1 in freq["Orders Placed"].values else 0
    warning_box(
        "Single-Purchase Dominance",
        f"<b>{one_time_pct:.1f}%</b> of customers placed exactly one order. "
        f"Repeat buyer rate is only <b>{repeat_rate:.2f}%</b>. "
        "This is a major retention opportunity.",
    )

    # ── Customer Segmentation
    st.markdown("### Customer Segmentation (Rule-Based)")

    def segment(row):
        if row["total_orders"] >= 3:
            return "High-Frequency (3+ orders)"
        elif row["total_orders"] == 2:
            return "Returning (2 orders)"
        elif row["total_spend_payment"] >= 500:
            return "High-Value (1 order, R$500+)"
        else:
            return "Single-Purchase (<R$500)"

    df_cust = df_cust.copy()
    df_cust["segment"] = df_cust.apply(segment, axis=1)
    seg_summary = (
        df_cust.groupby("segment")
        .agg(n_customers=("customer_unique_id", "count"),
             avg_spend=("total_spend_payment", "mean"),
             avg_orders=("total_orders", "mean"))
        .reset_index().sort_values("n_customers", ascending=False)
    )

    col3, col4 = st.columns(2)
    with col3:
        fig4 = px.pie(
            seg_summary, values="n_customers", names="segment",
            color_discrete_sequence=PALETTE, hole=0.4,
            title="Segments by Customer Count", template=PLOTLY_TEMPLATE,
        )
        fig4.update_traces(textposition="inside", textinfo="percent+label",
                           textfont_size=11)
        fig4.update_layout(margin=dict(t=50, b=10, l=10, r=10), height=350)
        st.plotly_chart(fig4, use_container_width=True)

    with col4:
        fig5 = px.bar(
            seg_summary, x="avg_spend", y="segment",
            orientation="h", text="avg_spend",
            color="avg_spend",
            color_continuous_scale=["#C4B5FD", CLR_SECONDARY],
            template=PLOTLY_TEMPLATE,
            title="Segments by Avg Customer Spend (R$)",
        )
        fig5.update_coloraxes(showscale=False)
        fig5.update_traces(
            texttemplate="R$%{text:,.0f}", textposition="outside"
        )
        fig5.update_layout(
            xaxis_title="Avg Spend (R$)", yaxis_title="",
            height=350, margin=dict(t=50, b=30, l=10, r=100),
        )
        st.plotly_chart(fig5, use_container_width=True)

    st.dataframe(
        seg_summary.style.format({
            "n_customers": "{:,}",
            "avg_spend": "R${:.2f}",
            "avg_orders": "{:.2f}",
        }),
        use_container_width=True, hide_index=True,
    )

    recommendation_box(
        "Customer Retention Strategy",
        f"High-Value single-purchase customers (R$500+) have the highest spend potential. "
        "Launch a targeted post-purchase email campaign within 30 days of delivery "
        "with personalised product recommendations based on their purchased category.",
    )

    # ── Download
    st.markdown("---")
    download_csv(seg_summary, "customer_segments.csv", "Download Customer Segments")
