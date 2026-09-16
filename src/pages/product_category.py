"""pages/product_category.py — Product & Category Analysis page"""

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
    st.markdown("## 📦 Product & Category Analysis")

    df_itm = filters["items"]
    del_items = df_itm[df_itm["order_status"] == "delivered"].copy()
    rev_clean = reviews[["order_id", "review_score"]].drop_duplicates("order_id")
    del_items_rev = del_items.merge(rev_clean, on="order_id", how="left")

    if len(del_items) == 0:
        st.warning("No delivered items match the current filters.")
        return

    # ── KPIs
    total_cats  = del_items["product_category_name_english"].nunique()
    total_items = len(del_items)
    avg_price   = del_items["price"].mean()
    avg_freight_pct = (del_items["freight_value"] / del_items["price"].replace(0, float("nan")) * 100).median()

    c1, c2, c3, c4 = st.columns(4)
    kpi_card(c1, "Active Categories", f"{total_cats}", color=CLR_PRIMARY)
    kpi_card(c2, "Items Sold", f"{total_items:,}", color=CLR_SECONDARY)
    kpi_card(c3, "Avg Item Price", f"R${avg_price:.2f}", color=CLR_SUCCESS)
    kpi_card(c4, "Median Freight % of Price", f"{avg_freight_pct:.1f}%", color=CLR_WARNING)

    st.markdown("---")

    # ── Category Revenue & Volume side by side
    st.markdown("### Category Performance")
    n_cats = st.slider("Top N categories", 5, 30, 15, key="prod_cat_slider")

    cat_rev = (
        del_items.groupby("product_category_name_english")
        .agg(revenue=("item_revenue", "sum"),
             items_sold=("order_item_id", "count"),
             avg_price=("price", "mean"),
             avg_freight=("freight_value", "mean"))
        .reset_index()
        .sort_values("revenue", ascending=False)
        .head(n_cats)
    )
    cat_rev.columns = ["Category", "Revenue", "Items Sold", "Avg Price", "Avg Freight"]
    cat_rev["Revenue_fmt"] = cat_rev["Revenue"].apply(format_brl)

    col1, col2 = st.columns(2)
    with col1:
        fig1 = px.bar(
            cat_rev[::-1], x="Revenue", y="Category",
            orientation="h", text="Revenue_fmt",
            color="Revenue",
            color_continuous_scale=["#93C5FD", CLR_PRIMARY],
            template=PLOTLY_TEMPLATE,
            title=f"Top {n_cats} Categories by Revenue",
        )
        fig1.update_coloraxes(showscale=False)
        fig1.update_traces(textposition="outside")
        fig1.update_layout(
            xaxis_title="Revenue (R$)", yaxis_title="",
            height=max(400, n_cats * 30),
            margin=dict(t=50, b=30, l=10, r=100),
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        cat_vol = (
            del_items.groupby("product_category_name_english")
            ["order_item_id"].count().sort_values(ascending=False).head(n_cats).reset_index()
        )
        cat_vol.columns = ["Category", "Items Sold"]
        fig2 = px.bar(
            cat_vol[::-1], x="Items Sold", y="Category",
            orientation="h", text="Items Sold",
            color="Items Sold",
            color_continuous_scale=["#6EE7B7", CLR_SUCCESS],
            template=PLOTLY_TEMPLATE,
            title=f"Top {n_cats} Categories by Items Sold",
        )
        fig2.update_coloraxes(showscale=False)
        fig2.update_traces(texttemplate="%{text:,}", textposition="outside")
        fig2.update_layout(
            xaxis_title="Items Sold", yaxis_title="",
            height=max(400, n_cats * 30),
            margin=dict(t=50, b=30, l=10, r=80),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Category Review Score
    st.markdown("### Review Score by Category (200+ orders)")
    cat_score = (
        del_items_rev.groupby("product_category_name_english")
        .agg(avg_score=("review_score", "mean"),
             n_orders=("order_id", "nunique"))
        .reset_index()
    )
    cat_score = cat_score[cat_score["n_orders"] >= 200].sort_values("avg_score")
    overall_avg = del_items_rev["review_score"].mean()

    color_fn = lambda v: CLR_DANGER if v < 3.8 else (CLR_SUCCESS if v >= 4.2 else CLR_WARNING)
    colors = [color_fn(v) for v in cat_score["avg_score"]]

    fig3 = go.Figure(go.Bar(
        x=cat_score["avg_score"],
        y=cat_score["product_category_name_english"],
        orientation="h",
        marker_color=colors,
        text=[f"{v:.2f}" for v in cat_score["avg_score"]],
        textposition="outside",
    ))
    fig3.add_vline(x=overall_avg, line_dash="dot", line_color=CLR_WARNING,
                   annotation_text=f"Avg {overall_avg:.2f}")
    fig3.update_layout(
        title="Avg Review Score by Category (min 200 orders)",
        xaxis=dict(title="Avg Review Score", range=[0, 5.3]),
        yaxis_title="",
        template=PLOTLY_TEMPLATE,
        height=max(500, len(cat_score) * 28),
        margin=dict(t=50, b=40, l=10, r=80),
    )
    st.plotly_chart(fig3, use_container_width=True)

    low_cats = cat_score.head(3)["product_category_name_english"].tolist()
    low_scores = cat_score.head(3)["avg_score"].tolist()
    warning_box(
        "Lowest-Reviewed Categories",
        f"Bottom 3: <b>{'</b>, <b>'.join(low_cats)}</b> "
        f"(avg scores: {', '.join(f'{s:.2f}' for s in low_scores)}). "
        "These categories likely have delivery, quality or expectation-mismatch issues.",
    )

    # ── Freight as % of price by category
    st.markdown("### Freight Cost as % of Item Price (Top 15)")
    del_items["freight_pct"] = del_items["freight_value"] / del_items["price"].replace(0, float("nan")) * 100
    cat_freight = (
        del_items.groupby("product_category_name_english")["freight_pct"]
        .median().sort_values(ascending=False).head(15).reset_index()
    )
    cat_freight.columns = ["Category", "Median Freight %"]

    fig4 = px.bar(
        cat_freight[::-1], x="Median Freight %", y="Category",
        orientation="h", text="Median Freight %",
        color="Median Freight %",
        color_continuous_scale=["#FDE68A", CLR_DANGER],
        template=PLOTLY_TEMPLATE,
        title="Categories with Highest Freight Cost (% of Price)",
    )
    fig4.update_coloraxes(showscale=False)
    fig4.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig4.update_layout(
        xaxis_title="Median Freight as % of Price", yaxis_title="",
        height=430, margin=dict(t=50, b=30, l=10, r=80),
    )
    st.plotly_chart(fig4, use_container_width=True)

    recommendation_box(
        "High Freight Categories",
        "Electronics, DVDs, and telephony have freight costs exceeding 40% of item price. "
        "Negotiate category-specific carrier rates or introduce free-shipping thresholds "
        "to reduce the friction for these purchases.",
    )

    # ── Full table
    with st.expander("📋 Full Category Summary Table"):
        cat_full = (
            del_items.groupby("product_category_name_english")
            .agg(revenue=("item_revenue", "sum"),
                 items_sold=("order_item_id", "count"),
                 avg_price=("price", "mean"),
                 avg_freight=("freight_value", "mean"))
            .reset_index()
            .sort_values("revenue", ascending=False)
        )
        cat_full.columns = ["Category", "Revenue (R$)", "Items Sold", "Avg Price (R$)", "Avg Freight (R$)"]
        st.dataframe(
            cat_full.style.format({
                "Revenue (R$)": "R${:,.2f}",
                "Items Sold": "{:,}",
                "Avg Price (R$)": "R${:.2f}",
                "Avg Freight (R$)": "R${:.2f}",
            }),
            use_container_width=True, hide_index=True,
        )
        download_csv(cat_full, "category_full_summary.csv", "Download Category Table")
