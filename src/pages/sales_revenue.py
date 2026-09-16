"""pages/sales_revenue.py — Sales & Revenue Analysis page"""

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
    st.markdown("## 💰 Sales & Revenue Analysis")

    df_ord = filters["orders"]
    df_itm = filters["items"]
    delivered = df_ord[df_ord["order_status"] == "delivered"]
    del_items = df_itm[df_itm["order_status"] == "delivered"].copy()

    if len(del_items) == 0:
        st.warning("No delivered items match the current filters.")
        return

    # ── KPI row
    total_rev   = del_items["item_revenue"].sum()
    prod_rev    = del_items["price"].sum()
    freight_rev = del_items["freight_value"].sum()
    aov         = delivered["total_order_revenue"].mean() if len(delivered) > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    kpi_card(c1, "Total Revenue", format_brl(total_rev), color=CLR_PRIMARY)
    kpi_card(c2, "Product Revenue", format_brl(prod_rev),
             delta=f"{prod_rev/total_rev*100:.1f}% of total", color=CLR_SECONDARY)
    kpi_card(c3, "Freight Revenue", format_brl(freight_rev),
             delta=f"{freight_rev/total_rev*100:.1f}% of total", color=CLR_WARNING)
    kpi_card(c4, "Avg Order Value", f"R${aov:.2f}", color=CLR_SUCCESS)

    st.markdown("---")

    # ── Monthly Revenue Trend
    st.markdown("### Monthly Revenue Trend")
    del_items["ym"] = del_items["order_purchase_timestamp"].dt.to_period("M")
    monthly_rev = del_items.groupby("ym")["item_revenue"].sum().reset_index()
    monthly_rev["ym_str"] = monthly_rev["ym"].astype(str)
    monthly_rev = monthly_rev.sort_values("ym_str")
    monthly_rev["rolling_3m"] = monthly_rev["item_revenue"].rolling(3, min_periods=1).mean()

    delivered["ym"] = delivered["order_purchase_timestamp"].dt.to_period("M")
    monthly_orders = delivered.groupby("ym")["order_id"].count().reset_index()
    monthly_orders["ym_str"] = monthly_orders["ym"].astype(str)
    monthly = monthly_rev.merge(monthly_orders, on="ym_str", how="left", suffixes=("", "_ord"))

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly["ym_str"], y=monthly["item_revenue"],
        name="Monthly Revenue", marker_color=CLR_PRIMARY, opacity=0.7,
    ))
    fig.add_trace(go.Scatter(
        x=monthly["ym_str"], y=monthly["rolling_3m"],
        mode="lines", name="3-Month Avg",
        line=dict(color=CLR_DANGER, width=2.5, dash="dash"),
    ))
    fig.update_layout(
        title="Monthly Revenue with 3-Month Rolling Average",
        xaxis=dict(title="Month", tickangle=-45),
        yaxis=dict(title="Revenue (R$)", tickformat=",.0f"),
        template=PLOTLY_TEMPLATE, hovermode="x unified",
        legend=dict(x=0.01, y=0.99),
        height=400, margin=dict(t=50, b=60, l=60, r=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    if len(monthly) > 1:
        peak = monthly.loc[monthly["item_revenue"].idxmax()]
        insight_box(
            "Revenue Peak",
            f"Peak month: <b>{peak['ym_str']}</b> — R${peak['item_revenue']:,.0f}. "
            "The Black Friday 2017 spike is clearly visible in the trend.",
        )

    # ── AOV over time + MoM growth
    st.markdown("### Average Order Value & Monthly Growth")
    col1, col2 = st.columns(2)

    with col1:
        monthly_aov = (
            delivered.groupby("ym")["total_order_revenue"].mean().reset_index()
        )
        monthly_aov["ym_str"] = monthly_aov["ym"].astype(str)
        monthly_aov = monthly_aov.sort_values("ym_str")
        overall_aov = delivered["total_order_revenue"].mean()

        fig_aov = go.Figure()
        fig_aov.add_trace(go.Scatter(
            x=monthly_aov["ym_str"], y=monthly_aov["total_order_revenue"],
            mode="lines+markers", name="AOV",
            line=dict(color=CLR_SECONDARY, width=2.5),
            marker=dict(size=5),
            fill="tozeroy", fillcolor="rgba(124,58,237,0.07)",
        ))
        fig_aov.add_hline(
            y=overall_aov, line_dash="dot", line_color=CLR_WARNING,
            annotation_text=f"Avg R${overall_aov:.0f}",
        )
        fig_aov.update_layout(
            title="Average Order Value Over Time",
            xaxis=dict(tickangle=-45), yaxis=dict(title="AOV (R$)"),
            template=PLOTLY_TEMPLATE, height=340,
            margin=dict(t=50, b=60, l=60, r=20),
        )
        st.plotly_chart(fig_aov, use_container_width=True)

    with col2:
        monthly_rev_sorted = monthly_rev.sort_values("ym_str").copy()
        monthly_rev_sorted["mom_growth"] = (
            monthly_rev_sorted["item_revenue"].pct_change() * 100
        )
        monthly_rev_sorted = monthly_rev_sorted.dropna(subset=["mom_growth"])

        colors_mom = [CLR_SUCCESS if v >= 0 else CLR_DANGER
                      for v in monthly_rev_sorted["mom_growth"]]
        fig_mom = go.Figure(go.Bar(
            x=monthly_rev_sorted["ym_str"],
            y=monthly_rev_sorted["mom_growth"],
            marker_color=colors_mom,
            name="MoM Growth %",
        ))
        fig_mom.add_hline(y=0, line_color=CLR_WARNING, line_dash="dot")
        fig_mom.update_layout(
            title="Month-over-Month Revenue Growth (%)",
            xaxis=dict(tickangle=-45), yaxis=dict(title="Growth (%)"),
            template=PLOTLY_TEMPLATE, height=340,
            margin=dict(t=50, b=60, l=60, r=20),
        )
        st.plotly_chart(fig_mom, use_container_width=True)

    # ── Category Revenue
    st.markdown("### Revenue by Product Category (Top 20)")
    n_cats = st.slider("Number of categories to display", 5, 30, 15, key="sales_cat_slider")
    cat_rev = (
        del_items.groupby("product_category_name_english")["item_revenue"]
        .sum().sort_values(ascending=False).head(n_cats).reset_index()
    )
    cat_rev.columns = ["Category", "Revenue"]
    cat_rev["Revenue_fmt"] = cat_rev["Revenue"].apply(format_brl)

    fig_cat = px.bar(
        cat_rev[::-1], x="Revenue", y="Category",
        orientation="h", text="Revenue_fmt",
        color="Revenue", color_continuous_scale=["#93C5FD", CLR_PRIMARY],
        template=PLOTLY_TEMPLATE,
        title=f"Top {n_cats} Product Categories by Revenue",
    )
    fig_cat.update_coloraxes(showscale=False)
    fig_cat.update_traces(textposition="outside")
    fig_cat.update_layout(
        xaxis_title="Revenue (R$)", yaxis_title="",
        height=max(400, n_cats * 32),
        margin=dict(t=50, b=40, l=20, r=100),
    )
    st.plotly_chart(fig_cat, use_container_width=True)

    top_cat = cat_rev.iloc[0]
    insight_box(
        "Top Revenue Category",
        f"<b>{top_cat['Category']}</b> leads with <b>{format_brl(top_cat['Revenue'])}</b>. "
        "Health & Beauty, Watches, and Home goods dominate — not electronics.",
    )

    # ── Revenue by customer state
    st.markdown("### Revenue by Customer State")
    state_rev = (
        delivered.groupby("customer_state")["total_order_revenue"]
        .sum().sort_values(ascending=False).reset_index()
    )
    state_rev.columns = ["State", "Revenue"]
    state_rev["Revenue_fmt"] = state_rev["Revenue"].apply(format_brl)

    fig_state = px.bar(
        state_rev, x="State", y="Revenue",
        color="Revenue", color_continuous_scale=["#93C5FD", CLR_PRIMARY],
        text="Revenue_fmt", template=PLOTLY_TEMPLATE,
        title="Total Delivered Revenue by Customer State",
    )
    fig_state.update_coloraxes(showscale=False)
    fig_state.update_traces(textposition="outside")
    fig_state.update_layout(
        xaxis_title="State", yaxis_title="Revenue (R$)",
        height=400, margin=dict(t=50, b=50, l=50, r=20),
    )
    st.plotly_chart(fig_state, use_container_width=True)

    sp_rev = state_rev[state_rev["State"] == "SP"]["Revenue"].sum()
    total_state_rev = state_rev["Revenue"].sum()
    if total_state_rev > 0:
        insight_box(
            "Geographic Concentration",
            f"São Paulo alone accounts for <b>{sp_rev/total_state_rev*100:.1f}%</b> "
            f"of total revenue (<b>{format_brl(sp_rev)}</b>). "
            "The top 3 states (SP, RJ, MG) represent ~62% of all revenue.",
        )

    # ── Download
    st.markdown("---")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        download_csv(cat_rev[["Category", "Revenue"]], "category_revenue.csv",
                     "Download Category Revenue")
    with col_d2:
        download_csv(state_rev[["State", "Revenue"]], "state_revenue.csv",
                     "Download State Revenue")
