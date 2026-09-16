"""pages/seller_performance.py — Seller Performance page"""

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
    st.markdown("## 🏪 Seller Performance")

    df_sel = sellers.copy()
    if filters.get("seller_states"):
        df_sel = df_sel[df_sel["seller_state"].isin(filters["seller_states"])]

    if len(df_sel) == 0:
        st.warning("No sellers match the current filters.")
        return

    # ── KPIs
    total_rev = df_sel["total_revenue"].sum()
    top10_rev = df_sel.nlargest(10, "total_revenue")["total_revenue"].sum()
    top10_pct = top10_rev / total_rev * 100 if total_rev > 0 else 0
    med_rev   = df_sel["total_revenue"].median()

    c1, c2, c3, c4 = st.columns(4)
    kpi_card(c1, "Active Sellers", f"{len(df_sel):,}", color=CLR_PRIMARY)
    kpi_card(c2, "Total Seller Revenue", format_brl(total_rev), color=CLR_SECONDARY)
    kpi_card(c3, "Median Seller Revenue", format_brl(med_rev), color=CLR_SUCCESS)
    kpi_card(c4, "Top 10 Revenue Share", f"{top10_pct:.1f}%",
             delta="of all seller revenue", color=CLR_WARNING)

    st.markdown("---")

    # ── Top sellers by revenue
    st.markdown("### Top Sellers by Revenue")
    n_top = st.slider("Number of sellers to display", 5, 30, 15, key="seller_slider")
    top_rev = df_sel.sort_values("total_revenue", ascending=False).head(n_top).copy()
    top_rev["label"] = "Seller " + top_rev["seller_id"].str[:8] + "…"
    top_rev["rev_fmt"] = top_rev["total_revenue"].apply(format_brl)

    fig1 = px.bar(
        top_rev[::-1], x="total_revenue", y="label",
        orientation="h", text="rev_fmt",
        color="total_revenue",
        color_continuous_scale=["#93C5FD", CLR_PRIMARY],
        template=PLOTLY_TEMPLATE,
        title=f"Top {n_top} Sellers by Revenue",
        hover_data={"seller_state": True, "n_unique_orders": True,
                    "avg_review_score": True, "top_category": True},
    )
    fig1.update_coloraxes(showscale=False)
    fig1.update_traces(textposition="outside")
    fig1.update_layout(
        xaxis_title="Revenue (R$)", yaxis_title="",
        height=max(400, n_top * 30),
        margin=dict(t=50, b=30, l=10, r=100),
    )
    st.plotly_chart(fig1, use_container_width=True)

    # ── Revenue by seller state
    st.markdown("### Revenue by Seller State")
    state_sel_rev = (
        df_sel.groupby("seller_state")
        .agg(revenue=("total_revenue", "sum"),
             n_sellers=("seller_id", "count"),
             avg_score=("avg_review_score", "mean"))
        .reset_index().sort_values("revenue", ascending=False)
    )
    state_sel_rev["rev_fmt"] = state_sel_rev["revenue"].apply(format_brl)

    col1, col2 = st.columns(2)
    with col1:
        fig2 = px.bar(
            state_sel_rev, x="seller_state", y="revenue",
            text="rev_fmt",
            color="revenue",
            color_continuous_scale=["#C4B5FD", CLR_SECONDARY],
            template=PLOTLY_TEMPLATE,
            title="Revenue by Seller State",
        )
        fig2.update_coloraxes(showscale=False)
        fig2.update_traces(textposition="outside")
        fig2.update_layout(
            xaxis_title="Seller State", yaxis_title="Revenue (R$)",
            height=380, margin=dict(t=50, b=50, l=50, r=20),
            xaxis_tickangle=-45,
        )
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        fig3 = px.pie(
            state_sel_rev.head(10), values="n_sellers", names="seller_state",
            color_discrete_sequence=PALETTE, hole=0.4,
            title="Seller Distribution by State (Top 10)",
            template=PLOTLY_TEMPLATE,
        )
        fig3.update_traces(textposition="inside", textinfo="percent+label",
                           textfont_size=11)
        fig3.update_layout(height=380, margin=dict(t=50, b=10, l=10, r=10))
        st.plotly_chart(fig3, use_container_width=True)

    # ── Seller performance scatter
    st.markdown("### Seller Revenue vs. Review Score vs. Order Volume")
    scatter_data = df_sel[df_sel["avg_review_score"].notna() & df_sel["total_revenue"] > 0].copy()
    scatter_data["orders_k"] = scatter_data["n_unique_orders"] / 1000

    fig4 = px.scatter(
        scatter_data.head(500),
        x="total_revenue", y="avg_review_score",
        size="n_unique_orders", color="seller_state",
        hover_name="seller_id",
        hover_data={"total_revenue": ":,.0f", "avg_review_score": ":.2f",
                    "n_unique_orders": ":,", "top_category": True},
        color_discrete_sequence=PALETTE,
        size_max=40,
        template=PLOTLY_TEMPLATE,
        title="Seller Revenue vs. Review Score (bubble = order volume)",
    )
    fig4.add_hline(y=4.0, line_dash="dot", line_color=CLR_WARNING,
                   annotation_text="Score 4.0")
    fig4.update_layout(
        xaxis_title="Total Revenue (R$)", yaxis_title="Avg Review Score",
        height=480, margin=dict(t=50, b=50, l=50, r=20),
    )
    st.plotly_chart(fig4, use_container_width=True)

    insight_box(
        "Seller Concentration",
        f"Top 10 sellers generate <b>{top10_pct:.1f}%</b> of total seller revenue. "
        f"Median seller revenue is <b>{format_brl(med_rev)}</b> — high concentration risk.",
    )

    # ── Top sellers table
    with st.expander("📋 Top 30 Sellers Full Table"):
        top30 = df_sel.sort_values("total_revenue", ascending=False).head(30).copy()
        top30["seller_short"] = top30["seller_id"].str[:12] + "…"
        display_cols = ["seller_short", "seller_state", "total_revenue",
                        "n_unique_orders", "total_items_sold", "avg_review_score",
                        "top_category"]
        st.dataframe(
            top30[display_cols].style.format({
                "total_revenue": "R${:,.2f}",
                "n_unique_orders": "{:,}",
                "total_items_sold": "{:,}",
                "avg_review_score": "{:.2f}",
            }),
            use_container_width=True, hide_index=True,
        )

    recommendation_box(
        "Seller Geographic Diversification",
        f"Only {df_sel['seller_state'].nunique()} states have registered sellers vs 27 states with customers. "
        "Recruit sellers in RS, MG, RJ, PR with preferential onboarding fees to reduce cross-state delivery times.",
    )

    st.markdown("---")
    download_csv(df_sel[["seller_id", "seller_state", "total_revenue",
                          "n_unique_orders", "avg_review_score", "top_category"]],
                 "seller_performance.csv", "Download Seller Data")
