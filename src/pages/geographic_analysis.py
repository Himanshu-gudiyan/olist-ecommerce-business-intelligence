"""pages/geographic_analysis.py — Geographic Analysis page"""

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

# Brazilian state codes for choropleth
BR_STATE_CODES = {
    "AC": "AC", "AL": "AL", "AP": "AP", "AM": "AM", "BA": "BA",
    "CE": "CE", "DF": "DF", "ES": "ES", "GO": "GO", "MA": "MA",
    "MT": "MT", "MS": "MS", "MG": "MG", "PA": "PA", "PB": "PB",
    "PR": "PR", "PE": "PE", "PI": "PI", "RJ": "RJ", "RN": "RN",
    "RS": "RS", "RO": "RO", "RR": "RR", "SC": "SC", "SP": "SP",
    "SE": "SE", "TO": "TO",
}


def show(orders, items, customers, sellers, reviews, payments, filters):
    st.markdown("## 🗺️ Geographic Analysis")
    st.markdown(
        "_State-level analysis of customers, sellers, revenue, and delivery performance._"
    )

    df_ord = filters["orders"]
    df_cust = customers.copy()
    df_sel  = sellers.copy()

    if filters.get("customer_states"):
        df_cust = df_cust[df_cust["customer_state"].isin(filters["customer_states"])]
    if filters.get("seller_states"):
        df_sel = df_sel[df_sel["seller_state"].isin(filters["seller_states"])]

    delivered = df_ord[df_ord["order_status"] == "delivered"]

    # ── Build state-level summary
    cust_state = (
        df_cust.groupby("customer_state")
        .agg(n_customers=("customer_unique_id", "count"),
             avg_spend=("total_spend_payment", "mean"))
        .reset_index()
    )
    rev_state = (
        delivered.groupby("customer_state")["total_order_revenue"]
        .sum().reset_index().rename(columns={"total_order_revenue": "revenue"})
    )
    del_state = (
        delivered[delivered["delivery_days"].notna()]
        .groupby("customer_state")["delivery_days"]
        .mean().reset_index().rename(columns={"delivery_days": "avg_delivery_days"})
    )
    seller_state = (
        df_sel.groupby("seller_state")
        .agg(n_sellers=("seller_id", "count"),
             seller_revenue=("total_revenue", "sum"))
        .reset_index()
    )

    state_summary = (
        cust_state
        .merge(rev_state, on="customer_state", how="outer")
        .merge(del_state, on="customer_state", how="left")
    )
    state_summary = state_summary.fillna(0)
    state_summary["state"] = state_summary["customer_state"]

    # ── KPIs
    c1, c2, c3 = st.columns(3)
    kpi_card(c1, "States with Customers", str(state_summary[state_summary["n_customers"] > 0]["state"].nunique()), color=CLR_PRIMARY)
    kpi_card(c2, "States with Sellers", str(df_sel["seller_state"].nunique()), color=CLR_SECONDARY)
    kpi_card(c3, "States without Sellers", str(27 - df_sel["seller_state"].nunique()),
             delta="potential seller recruitment targets", color=CLR_WARNING)

    st.markdown("---")

    # ── State comparison table
    st.markdown("### State-Level Performance Summary")
    state_display = state_summary.sort_values("revenue", ascending=False).copy()
    state_display["revenue_fmt"] = state_display["revenue"].apply(format_brl)
    state_display["rev_share"] = (
        state_display["revenue"] / state_display["revenue"].sum() * 100
    ).round(1)

    st.dataframe(
        state_display[["state", "n_customers", "revenue_fmt", "rev_share", "avg_delivery_days"]]
        .rename(columns={
            "state": "State", "n_customers": "Customers",
            "revenue_fmt": "Revenue", "rev_share": "Rev Share %",
            "avg_delivery_days": "Avg Delivery Days",
        })
        .style.format({"Customers": "{:,}", "Rev Share %": "{:.1f}%",
                        "Avg Delivery Days": "{:.1f}"}),
        use_container_width=True, hide_index=True,
        height=420,
    )

    # ── Revenue & Customers bar charts
    st.markdown("### Revenue vs. Customer Count by State")
    col1, col2 = st.columns(2)

    with col1:
        top_rev_states = state_display.sort_values("revenue", ascending=False).head(15)
        fig1 = px.bar(
            top_rev_states[::-1], x="revenue", y="state",
            orientation="h",
            text=top_rev_states[::-1]["revenue_fmt"],
            color="revenue",
            color_continuous_scale=["#93C5FD", CLR_PRIMARY],
            template=PLOTLY_TEMPLATE,
            title="Top 15 States by Revenue",
        )
        fig1.update_coloraxes(showscale=False)
        fig1.update_traces(textposition="outside")
        fig1.update_layout(
            xaxis_title="Revenue (R$)", yaxis_title="",
            height=430, margin=dict(t=50, b=30, l=10, r=100),
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        top_cust_states = state_display.sort_values("n_customers", ascending=False).head(15)
        fig2 = px.bar(
            top_cust_states[::-1], x="n_customers", y="state",
            orientation="h",
            text=top_cust_states[::-1]["n_customers"].apply(lambda v: f"{v:,}"),
            color="n_customers",
            color_continuous_scale=["#6EE7B7", CLR_SUCCESS],
            template=PLOTLY_TEMPLATE,
            title="Top 15 States by Customer Count",
        )
        fig2.update_coloraxes(showscale=False)
        fig2.update_traces(textposition="outside")
        fig2.update_layout(
            xaxis_title="Customers", yaxis_title="",
            height=430, margin=dict(t=50, b=30, l=10, r=80),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Delivery time by state (heatmap-style bar)
    st.markdown("### Average Delivery Time by State")
    del_full = state_display[state_display["avg_delivery_days"] > 0].sort_values("avg_delivery_days")
    overall_del_mean = del_full["avg_delivery_days"].mean()

    fig3 = go.Figure(go.Bar(
        x=del_full["avg_delivery_days"],
        y=del_full["state"],
        orientation="h",
        marker_color=[CLR_SUCCESS if v < overall_del_mean else CLR_DANGER
                      for v in del_full["avg_delivery_days"]],
        text=[f"{v:.1f}d" for v in del_full["avg_delivery_days"]],
        textposition="outside",
    ))
    fig3.add_vline(x=overall_del_mean, line_dash="dot", line_color=CLR_WARNING,
                   annotation_text=f"Avg {overall_del_mean:.1f}d")
    fig3.update_layout(
        title="Avg Delivery Days by Customer State",
        xaxis_title="Avg Delivery Days", yaxis_title="",
        template=PLOTLY_TEMPLATE, height=550,
        margin=dict(t=50, b=40, l=10, r=80),
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ── Customer vs Seller State Mismatch
    st.markdown("### Customer vs. Seller State Coverage")
    all_states = sorted(set(list(BR_STATE_CODES.keys())))
    customer_states = set(df_cust["customer_state"].unique())
    seller_states_set = set(df_sel["seller_state"].unique())

    coverage_df = pd.DataFrame({
        "State": all_states,
        "Has Customers": [s in customer_states for s in all_states],
        "Has Sellers": [s in seller_states_set for s in all_states],
    })
    coverage_df["Status"] = coverage_df.apply(
        lambda r: "Both" if r["Has Customers"] and r["Has Sellers"]
        else ("Customers only" if r["Has Customers"] else "Neither"),
        axis=1,
    )
    color_map = {"Both": CLR_SUCCESS, "Customers only": CLR_WARNING, "Neither": "#9CA3AF"}
    fig4 = px.bar(
        coverage_df.sort_values("State"),
        x="State", y=[1] * len(coverage_df),
        color="Status", color_discrete_map=color_map,
        template=PLOTLY_TEMPLATE,
        title="State Coverage: Customers vs. Sellers",
        barmode="overlay",
    )
    fig4.update_layout(
        yaxis=dict(showticklabels=False, title=""),
        xaxis_title="State", height=280,
        margin=dict(t=50, b=40, l=20, r=20),
    )
    st.plotly_chart(fig4, use_container_width=True)

    no_seller_states = [s for s in all_states
                        if s in customer_states and s not in seller_states_set]
    warning_box(
        "Seller Coverage Gap",
        f"<b>{len(no_seller_states)}</b> states have customers but NO registered sellers: "
        f"<b>{', '.join(no_seller_states)}</b>. "
        "These customers must be served entirely by cross-state deliveries, inflating freight and delivery time.",
    )

    sp_pct = (state_display[state_display["state"] == "SP"]["revenue"].sum()
              / state_display["revenue"].sum() * 100)
    insight_box(
        "Geographic Concentration",
        f"São Paulo represents <b>{sp_pct:.1f}%</b> of total revenue. "
        "Targeted marketing and regional seller recruitment in the North/NE could unlock significant growth.",
    )

    recommendation_box(
        "Regional Expansion Strategy",
        "Priority seller recruitment states (active customers, no sellers): "
        f"{', '.join(no_seller_states[:5] if no_seller_states else ['All covered'])}. "
        "Offering 50% off first-year platform fees for sellers in these states could rapidly reduce delivery times and costs.",
    )

    st.markdown("---")
    download_csv(
        state_display[["state", "n_customers", "revenue_fmt", "rev_share", "avg_delivery_days"]],
        "geographic_summary.csv", "Download Geographic Summary",
    )
