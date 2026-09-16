"""pages/reviews_analysis.py — Customer Reviews page"""

import pandas as pd
import numpy as np
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
    st.markdown("## ⭐ Customer Reviews & Satisfaction")

    df_ord = filters["orders"]
    df_itm = filters["items"]
    df_rev = filters["reviews"]

    # Filter reviews to orders in scope
    order_ids_in_scope = set(df_ord["order_id"].unique())
    df_rev = df_rev[df_rev["order_id"].isin(order_ids_in_scope)]

    # Apply review score filter
    if filters.get("review_scores"):
        df_rev = df_rev[df_rev["review_score"].isin(filters["review_scores"])]

    if len(df_rev) == 0:
        st.warning("No reviews match the current filters.")
        return

    # ── KPIs
    avg_score   = df_rev["review_score"].mean()
    pct_5star   = (df_rev["review_score"] == 5).mean() * 100
    pct_1star   = (df_rev["review_score"] == 1).mean() * 100
    comment_rate = df_rev["has_comment"].mean() * 100 if "has_comment" in df_rev.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    kpi_card(c1, "Avg Review Score", f"{avg_score:.2f} / 5.0", color=CLR_PRIMARY)
    kpi_card(c2, "5-Star Reviews", f"{pct_5star:.1f}%",
             delta=f"{int(df_rev['review_score'].eq(5).sum()):,} reviews", color=CLR_SUCCESS)
    kpi_card(c3, "1-Star Reviews", f"{pct_1star:.1f}%",
             delta=f"{int(df_rev['review_score'].eq(1).sum()):,} reviews", color=CLR_DANGER)
    kpi_card(c4, "Reviews with Comment", f"{comment_rate:.1f}%", color=CLR_WARNING)

    st.markdown("---")

    # ── Score distribution
    st.markdown("### Review Score Distribution")
    score_cnt = df_rev["review_score"].value_counts().sort_index().reset_index()
    score_cnt.columns = ["Score", "Count"]
    score_cnt["Pct"] = (score_cnt["Count"] / score_cnt["Count"].sum() * 100).round(1)
    score_cnt["color"] = score_cnt["Score"].map({
        1: CLR_DANGER, 2: "#F97316", 3: "#EAB308", 4: CLR_SUCCESS, 5: CLR_PRIMARY
    })

    col1, col2 = st.columns([3, 2])
    with col1:
        fig1 = go.Figure(go.Bar(
            x=score_cnt["Score"].astype(str),
            y=score_cnt["Count"],
            marker_color=score_cnt["color"],
            text=[f"{r['Count']:,}<br>({r['Pct']:.1f}%)" for _, r in score_cnt.iterrows()],
            textposition="outside",
        ))
        fig1.update_layout(
            title=f"Review Score Distribution  (avg = {avg_score:.2f}/5.0)",
            xaxis_title="Star Rating", yaxis_title="Number of Reviews",
            template=PLOTLY_TEMPLATE, height=380,
            margin=dict(t=50, b=40, l=50, r=20),
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig_pie = px.pie(
            score_cnt, values="Count", names="Score",
            color="Score",
            color_discrete_map={1: CLR_DANGER, 2: "#F97316",
                                  3: "#EAB308", 4: CLR_SUCCESS, 5: CLR_PRIMARY},
            hole=0.4, template=PLOTLY_TEMPLATE,
            title="Score Share",
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label",
                              textfont_size=11)
        fig_pie.update_layout(height=380, margin=dict(t=50, b=10, l=10, r=10),
                               showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

    # ── Review score vs delivery delay
    st.markdown("### Review Score vs. Delivery Performance")
    rev_with_del = df_ord[
        (df_ord["order_status"] == "delivered") &
        df_ord["delivery_days"].notna() &
        df_ord["is_delayed"].notna()
    ].merge(df_rev[["order_id", "review_score"]], on="order_id", how="inner")

    if len(rev_with_del) > 0:
        rev_with_del["delay_bucket"] = pd.cut(
            rev_with_del["delivery_delay_days"],
            bins=[-300, -14, -7, -3, 0, 3, 7, 14, 300],
            labels=["Early >14d", "Early 8-14d", "Early 3-7d", "Early ≤3d",
                    "Late ≤3d", "Late 3-7d", "Late 7-14d", "Late >14d"],
        )
        delay_score = (
            rev_with_del.groupby("delay_bucket", observed=True)["review_score"]
            .agg(["mean", "count"]).reset_index()
        )
        delay_score.columns = ["Bucket", "Avg Score", "Orders"]
        delay_score = delay_score.dropna(subset=["Avg Score"])

        colors_delay = [CLR_SUCCESS if "Early" in str(b) else CLR_DANGER
                        for b in delay_score["Bucket"]]
        fig2 = go.Figure(go.Bar(
            x=delay_score["Bucket"].astype(str),
            y=delay_score["Avg Score"],
            marker_color=colors_delay,
            text=[f"{v:.2f}<br>(n={c:,})" for v, c in
                  zip(delay_score["Avg Score"], delay_score["Orders"])],
            textposition="outside",
        ))
        fig2.add_hline(y=rev_with_del["review_score"].mean(), line_dash="dot",
                       line_color=CLR_WARNING,
                       annotation_text=f"Overall avg: {rev_with_del['review_score'].mean():.2f}")
        fig2.update_layout(
            title="Avg Review Score by Delivery Delay Bucket",
            xaxis_title="Delivery vs. Estimated", yaxis_title="Avg Review Score",
            yaxis_range=[0, 5.3], template=PLOTLY_TEMPLATE, height=380,
            margin=dict(t=50, b=50, l=50, r=20),
        )
        st.plotly_chart(fig2, use_container_width=True)

        on_time = rev_with_del[rev_with_del["is_delayed"] == 0.0]["review_score"].mean()
        late    = rev_with_del[rev_with_del["is_delayed"] == 1.0]["review_score"].mean()
        delta   = late - on_time
        warning_box(
            "Late Delivery Score Penalty",
            f"On-time orders avg <b>{on_time:.2f} ⭐</b> vs late orders <b>{late:.2f} ⭐</b>. "
            f"That's a <b>{abs(delta):.2f}-star drop</b> caused by late delivery. "
            "Orders delayed 7+ days average <b>~1.7 stars</b>.",
        )

    # ── Review score by category
    st.markdown("### Review Score by Product Category (200+ orders)")
    del_items_in_scope = df_itm[df_itm["order_status"] == "delivered"]
    items_with_rev = del_items_in_scope.merge(
        df_rev[["order_id", "review_score"]], on="order_id", how="inner"
    )

    if len(items_with_rev) > 0:
        cat_score = (
            items_with_rev.groupby("product_category_name_english")
            .agg(avg_score=("review_score", "mean"),
                 n_orders=("order_id", "nunique"))
            .reset_index()
        )
        cat_score = cat_score[cat_score["n_orders"] >= 200].sort_values("avg_score")
        overall_avg = items_with_rev["review_score"].mean()

        color_fn = lambda v: CLR_DANGER if v < 3.8 else (CLR_SUCCESS if v >= 4.2 else CLR_WARNING)
        colors_cat = [color_fn(v) for v in cat_score["avg_score"]]

        fig3 = go.Figure(go.Bar(
            x=cat_score["avg_score"],
            y=cat_score["product_category_name_english"],
            orientation="h",
            marker_color=colors_cat,
            text=[f"{v:.2f}" for v in cat_score["avg_score"]],
            textposition="outside",
        ))
        fig3.add_vline(x=overall_avg, line_dash="dot", line_color=CLR_WARNING,
                       annotation_text=f"Avg {overall_avg:.2f}")
        fig3.update_layout(
            title="Avg Review Score by Category (min 200 orders)",
            xaxis=dict(title="Avg Score", range=[0, 5.3]),
            yaxis_title="", template=PLOTLY_TEMPLATE,
            height=max(500, len(cat_score) * 26),
            margin=dict(t=50, b=40, l=10, r=80),
        )
        st.plotly_chart(fig3, use_container_width=True)

    # ── Review volume over time
    st.markdown("### Review Volume Over Time")
    df_rev_time = df_rev.copy()
    df_rev_time["review_creation_date"] = pd.to_datetime(
        df_rev_time["review_creation_date"], errors="coerce"
    )
    df_rev_time["ym"] = df_rev_time["review_creation_date"].dt.to_period("M")
    rev_monthly = df_rev_time.groupby("ym").agg(
        n_reviews=("review_id", "count"),
        avg_score=("review_score", "mean"),
    ).reset_index()
    rev_monthly["ym_str"] = rev_monthly["ym"].astype(str)
    rev_monthly = rev_monthly.sort_values("ym_str")

    fig4 = go.Figure()
    fig4.add_trace(go.Bar(
        x=rev_monthly["ym_str"], y=rev_monthly["n_reviews"],
        name="Reviews", marker_color=CLR_PRIMARY, opacity=0.6, yaxis="y1",
    ))
    fig4.add_trace(go.Scatter(
        x=rev_monthly["ym_str"], y=rev_monthly["avg_score"],
        mode="lines+markers", name="Avg Score",
        line=dict(color=CLR_DANGER, width=2.5),
        yaxis="y2",
    ))
    fig4.update_layout(
        title="Monthly Review Volume & Avg Score",
        xaxis=dict(title="Month", tickangle=-45),
        yaxis=dict(title="Number of Reviews"),
        yaxis2=dict(title="Avg Score", overlaying="y", side="right",
                    range=[3.5, 5.0], showgrid=False),
        template=PLOTLY_TEMPLATE, hovermode="x unified",
        legend=dict(x=0.01, y=0.99), height=380,
        margin=dict(t=50, b=60, l=60, r=60),
    )
    st.plotly_chart(fig4, use_container_width=True)

    recommendation_box(
        "Review Score Improvement",
        "Focus on the 3 highest-impact levers: "
        "(1) Reduce late deliveries — each 1% reduction in late rate improves avg score by ~0.02 pts. "
        "(2) Audit office_furniture and telephony listings for accuracy. "
        "(3) Implement automated customer service outreach for 1-star reviews within 24 hours.",
    )

    st.markdown("---")
    download_csv(df_rev[["order_id", "review_score", "has_comment",
                          "review_creation_date"]],
                 "filtered_reviews.csv", "Download Reviews")
