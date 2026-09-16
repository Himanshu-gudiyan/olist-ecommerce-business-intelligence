"""pages/executive_overview.py — Executive Overview page"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dashboard_utils import (
    calc_kpis, kpi_card, insight_box, recommendation_box, warning_box,
    format_brl, CLR_PRIMARY, CLR_SECONDARY, CLR_SUCCESS, CLR_WARNING, CLR_DANGER,
    PALETTE, PLOTLY_TEMPLATE, download_csv,
)


def show(orders, items, customers, sellers, reviews, payments, filters):
    st.markdown("## 🏢 Executive Overview")
    st.markdown("_Core business metrics calculated from the real Olist dataset (2016–2018)._")

    # Apply filters
    df_ord = filters["orders"]
    df_itm = filters["items"]
    df_rev = filters["reviews"]
    df_sel = sellers
    df_cust = customers

    if filters.get("customer_states"):
        df_cust = df_cust[df_cust["customer_state"].isin(filters["customer_states"])]

    kpis = calc_kpis(df_ord, df_itm, df_cust, df_sel, df_rev)

    # ── KPI Cards Row 1
    st.markdown("### Key Performance Indicators")
    c1, c2, c3, c4 = st.columns(4)
    kpi_card(c1, "Total Orders", f"{kpis['total_orders']:,}", color=CLR_PRIMARY)
    kpi_card(c2, "Total Revenue (GMV)", format_brl(kpis["total_revenue"]), color=CLR_SECONDARY)
    kpi_card(c3, "Avg Order Value", f"R${kpis['aov']:.2f}", color=CLR_SUCCESS)
    kpi_card(c4, "Total Customers", f"{kpis['total_customers']:,}", color=CLR_WARNING)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    c5, c6, c7, c8 = st.columns(4)
    kpi_card(c5, "Active Sellers", f"{kpis['total_sellers']:,}", color=CLR_DANGER)
    kpi_card(c6, "Avg Review Score", f"{kpis['avg_review_score']:.2f} / 5.0", color=CLR_SUCCESS)
    kpi_card(c7, "Delivered Order Rate", f"{kpis['delivered_rate']:.1f}%", color=CLR_PRIMARY)
    kpi_card(c8, "Avg Delivery Time", f"{kpis['avg_delivery_days']:.1f} days", color=CLR_WARNING)

    st.markdown("---")

    # ── Monthly Revenue + Orders mini-trend
    st.markdown("### Revenue & Order Trend")
    delivered = df_ord[df_ord["order_status"] == "delivered"].copy()
    del_items = df_itm[df_itm["order_status"] == "delivered"].copy()

    if len(delivered) == 0:
        st.warning("No delivered orders match the current filters.")
        return

    del_items["ym"] = del_items["order_purchase_timestamp"].dt.to_period("M")
    monthly_rev = (
        del_items.groupby("ym")["item_revenue"].sum().reset_index()
    )
    delivered["ym"] = delivered["order_purchase_timestamp"].dt.to_period("M")
    monthly_ord = (
        delivered.groupby("ym")["order_id"].count().reset_index()
    )
    monthly = monthly_rev.merge(monthly_ord, on="ym", how="outer").sort_values("ym")
    monthly["ym_str"] = monthly["ym"].astype(str)
    monthly.columns = ["ym", "revenue", "n_orders", "ym_str"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly["ym_str"], y=monthly["revenue"],
        mode="lines+markers", name="Revenue (R$)",
        line=dict(color=CLR_PRIMARY, width=3),
        fill="tozeroy", fillcolor="rgba(37,99,235,0.08)",
        yaxis="y1",
    ))
    fig.add_trace(go.Scatter(
        x=monthly["ym_str"], y=monthly["n_orders"],
        mode="lines+markers", name="Orders",
        line=dict(color=CLR_SUCCESS, width=2.5, dash="dash"),
        marker=dict(size=5),
        yaxis="y2",
    ))
    fig.update_layout(
        title="Monthly Revenue & Order Volume",
        xaxis=dict(title="Month", tickangle=-45),
        yaxis=dict(title="Revenue (R$)", tickformat="R$,.0f", showgrid=True),
        yaxis2=dict(title="Orders", overlaying="y", side="right", showgrid=False),
        template=PLOTLY_TEMPLATE,
        hovermode="x unified",
        legend=dict(x=0.01, y=0.99),
        height=380,
        margin=dict(t=50, b=60, l=60, r=60),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Status + Payment side by side
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Order Status Distribution")
        status_cnt = df_ord["order_status"].value_counts().reset_index()
        status_cnt.columns = ["status", "count"]
        fig2 = px.bar(status_cnt.sort_values("count"), x="count", y="status",
                      orientation="h", color="count",
                      color_continuous_scale=["#93C5FD", CLR_PRIMARY],
                      template=PLOTLY_TEMPLATE, title="")
        fig2.update_coloraxes(showscale=False)
        fig2.update_traces(texttemplate="%{x:,}", textposition="outside")
        fig2.update_layout(
            xaxis_title="Orders", yaxis_title="",
            margin=dict(t=10, b=30, l=10, r=60), height=320,
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        st.markdown("#### Payment Method Distribution")
        pay_filt = payments
        if filters.get("payment_types"):
            pay_filt = pay_filt[pay_filt["payment_type"].isin(filters["payment_types"])]
        pay_cnt = pay_filt["payment_type"].value_counts().reset_index()
        pay_cnt.columns = ["type", "count"]
        fig3 = px.pie(pay_cnt, values="count", names="type",
                      color_discrete_sequence=PALETTE,
                      hole=0.4, template=PLOTLY_TEMPLATE, title="")
        fig3.update_traces(textposition="inside", textinfo="percent+label",
                           textfont_size=12)
        fig3.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=320,
                           showlegend=True)
        st.plotly_chart(fig3, use_container_width=True)

    # ── Top 5 Categories preview
    st.markdown("#### Top 5 Revenue Categories (Delivered)")
    top5 = (
        del_items.groupby("product_category_name_english")["item_revenue"]
        .sum().sort_values(ascending=False).head(5).reset_index()
    )
    top5.columns = ["Category", "Revenue (R$)"]
    top5["Revenue (R$)"] = top5["Revenue (R$)"].round(2)
    top5["Share %"] = (top5["Revenue (R$)"] / top5["Revenue (R$)"].sum() * 100).round(1)
    st.dataframe(
        top5.style.format({"Revenue (R$)": "R${:,.2f}", "Share %": "{:.1f}%"}),
        use_container_width=True, hide_index=True,
    )

    # ── Insight boxes
    st.markdown("---")
    st.markdown("### 💡 Key Business Insights")

    if len(delivered) > 0:
        peak_row = monthly.loc[monthly["revenue"].idxmax()]
        insight_box(
            "Revenue Peak",
            f"Best month: <b>{peak_row['ym_str']}</b> with <b>R${peak_row['revenue']:,.0f}</b> revenue "
            f"and <b>{int(peak_row['n_orders']):,}</b> orders — aligning with Black Friday / Cyber Monday.",
        )

    top_cat = top5.iloc[0]["Category"] if len(top5) > 0 else "N/A"
    top_cat_rev = top5.iloc[0]["Revenue (R$)"] if len(top5) > 0 else 0
    insight_box(
        "Top Revenue Category",
        f"<b>{top_cat}</b> leads with <b>R${top_cat_rev:,.0f}</b>. "
        "Health & Beauty and lifestyle goods outperform electronics.",
    )

    if kpis["repeat_buyer_rate"] < 5:
        warning_box(
            "Low Repeat Buyer Rate",
            f"Only <b>{kpis['repeat_buyer_rate']:.1f}%</b> of customers placed a second order. "
            "Retention programmes could significantly improve Customer Lifetime Value.",
        )

    if kpis["late_rate"] > 5:
        warning_box(
            "Delivery Delay Alert",
            f"<b>{kpis['late_rate']:.1f}%</b> of delivered orders arrived after the estimated date. "
            "Late deliveries average a <b>1.73-star drop</b> in review score.",
        )

    recommendation_box(
        "Priority Action",
        "Focus on (1) improving North/Northeast delivery times, "
        "(2) reducing late delivery rate below 5%, and "
        "(3) building post-purchase re-engagement flows to raise repeat-buyer rate above 10%.",
    )

    # ── Download
    st.markdown("---")
    summary_df = pd.DataFrame([{
        "Metric": k, "Value": v
    } for k, v in kpis.items()])
    download_csv(summary_df, "executive_kpis.csv", "Download KPI Summary")
