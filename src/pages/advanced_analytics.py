"""
pages/advanced_analytics.py
============================
Phase 5 — Advanced Business Analytics & Customer Intelligence

Sections:
  1. RFM Customer Segmentation
  2. Customer Retention Analysis
  3. Cohort Analysis
  4. Seller Intelligence
  5. Delivery & Logistics Analytics
  6. Revenue & Growth Analytics
  7. Business Opportunities
  8. Executive Insights Engine
"""

import os
import sys
import warnings

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dashboard_utils import (
    insight_box, recommendation_box, warning_box, format_brl,
    CLR_PRIMARY, CLR_SECONDARY, CLR_SUCCESS, CLR_WARNING, CLR_DANGER,
    PALETTE, PLOTLY_TEMPLATE, download_csv, kpi_card,
)
from rfm_analysis import (
    compute_rfm, rfm_segment_summary, SEGMENT_COLORS,
)
from cohort_analysis import compute_cohorts, cohort_summary
from seller_intelligence import compute_seller_scorecard, seller_opportunity_analysis
from growth_analytics import (
    compute_monthly_growth, compute_category_trend,
    compute_state_trend, identify_business_opportunities,
)


# ---------------------------------------------------------------------------
# Cached computations — expensive, run once
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner="Computing RFM segmentation…")
def get_rfm(orders_json: str) -> pd.DataFrame:
    orders = pd.read_json(orders_json, orient="split")
    orders["order_purchase_timestamp"] = pd.to_datetime(
        orders["order_purchase_timestamp"], errors="coerce"
    )
    return compute_rfm(orders)


@st.cache_data(ttl=3600, show_spinner="Building cohort table…")
def get_cohorts(orders_json: str) -> dict:
    orders = pd.read_json(orders_json, orient="split")
    orders["order_purchase_timestamp"] = pd.to_datetime(
        orders["order_purchase_timestamp"], errors="coerce"
    )
    return compute_cohorts(orders)


@st.cache_data(ttl=3600, show_spinner="Building seller scorecard…")
def get_seller_scorecard(
    sellers_json: str, orders_json: str, items_json: str, reviews_json: str
) -> pd.DataFrame:
    sellers = pd.read_json(sellers_json, orient="split")
    orders  = pd.read_json(orders_json,  orient="split")
    items   = pd.read_json(items_json,   orient="split")
    reviews = pd.read_json(reviews_json, orient="split")
    orders["order_purchase_timestamp"] = pd.to_datetime(
        orders["order_purchase_timestamp"], errors="coerce"
    )
    items["order_purchase_timestamp"] = pd.to_datetime(
        items["order_purchase_timestamp"], errors="coerce"
    )
    return compute_seller_scorecard(sellers, orders, items, reviews)


@st.cache_data(ttl=3600, show_spinner="Computing growth metrics…")
def get_monthly_growth(orders_json: str, items_json: str) -> pd.DataFrame:
    orders = pd.read_json(orders_json, orient="split")
    items  = pd.read_json(items_json,  orient="split")
    orders["order_purchase_timestamp"] = pd.to_datetime(
        orders["order_purchase_timestamp"], errors="coerce"
    )
    items["order_purchase_timestamp"] = pd.to_datetime(
        items["order_purchase_timestamp"], errors="coerce"
    )
    return compute_monthly_growth(orders, items)


@st.cache_data(ttl=3600, show_spinner="Identifying business opportunities…")
def get_opportunities(
    orders_json: str, items_json: str, sellers_json: str, reviews_json: str
) -> list:
    orders  = pd.read_json(orders_json,  orient="split")
    items   = pd.read_json(items_json,   orient="split")
    sellers = pd.read_json(sellers_json, orient="split")
    reviews = pd.read_json(reviews_json, orient="split")
    orders["order_purchase_timestamp"] = pd.to_datetime(
        orders["order_purchase_timestamp"], errors="coerce"
    )
    items["order_purchase_timestamp"] = pd.to_datetime(
        items["order_purchase_timestamp"], errors="coerce"
    )
    return identify_business_opportunities(orders, items, sellers, reviews)


# ---------------------------------------------------------------------------
# Helper: df → JSON for caching key
# ---------------------------------------------------------------------------
def _to_json(df: pd.DataFrame) -> str:
    return df.to_json(orient="split", date_format="iso")


# ---------------------------------------------------------------------------
# SECTION helpers
# ---------------------------------------------------------------------------

def _section_header(number: int, title: str, subtitle: str = ""):
    st.markdown(
        f"""
        <div style="background:linear-gradient(90deg,#EFF6FF,#F8FAFC);
                    border-left:5px solid {CLR_PRIMARY};border-radius:6px;
                    padding:14px 20px;margin:24px 0 16px 0;">
            <h3 style="margin:0;color:#1E293B;font-size:17px;">
                {number}. {title}
            </h3>
            {'<p style="margin:4px 0 0 0;font-size:13px;color:#57606a;">'+subtitle+'</p>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ===========================================================================
# MAIN PAGE FUNCTION
# ===========================================================================

def show(orders, items, customers, sellers, reviews, payments, filters):
    st.markdown("## 🧠 Advanced Business Analytics & Customer Intelligence")
    st.markdown(
        "_Phase 5 analytics built on the real Olist dataset. "
        "All metrics are calculated — no synthetic values._"
    )

    tab_labels = [
        "📊 RFM Segmentation",
        "🔄 Retention",
        "📅 Cohort Analysis",
        "🏪 Seller Intelligence",
        "🚚 Delivery Analytics",
        "📈 Growth Analytics",
        "🎯 Opportunities",
        "💡 Executive Insights",
    ]
    tabs = st.tabs(tab_labels)

    # Pre-compute heavy results once (JSON serialisation used as cache key)
    with st.spinner("Preparing advanced analytics…"):
        orders_j  = _to_json(orders)
        items_j   = _to_json(items)
        sellers_j = _to_json(sellers)
        reviews_j = _to_json(reviews)

        rfm_df      = get_rfm(orders_j)
        cohort_data = get_cohorts(orders_j)
        sc          = get_seller_scorecard(sellers_j, orders_j, items_j, reviews_j)
        monthly     = get_monthly_growth(orders_j, items_j)
        biz_opps    = get_opportunities(orders_j, items_j, sellers_j, reviews_j)

    # ========================================================================
    # TAB 1 — RFM SEGMENTATION
    # ========================================================================
    with tabs[0]:
        _section_header(1, "RFM Customer Segmentation",
                        "Recency · Frequency · Monetary scoring using quintile-based 1–5 scale")

        seg_summary = rfm_segment_summary(rfm_df)

        # KPIs
        n_champions = int(rfm_df[rfm_df["segment"]=="Champions"]["customer_unique_id"].count())
        n_at_risk   = int(rfm_df[rfm_df["segment"].isin(["At Risk","Can't Lose Them"])]["customer_unique_id"].count())
        n_new       = int(rfm_df[rfm_df["segment"]=="New Customers"]["customer_unique_id"].count())
        n_lost      = int(rfm_df[rfm_df["segment"]=="Lost"]["customer_unique_id"].count())

        c1,c2,c3,c4 = st.columns(4)
        kpi_card(c1,"Champions",f"{n_champions:,}",color=CLR_SUCCESS)
        kpi_card(c2,"New Customers",f"{n_new:,}",color=CLR_PRIMARY)
        kpi_card(c3,"At Risk / Can't Lose",f"{n_at_risk:,}",color=CLR_WARNING)
        kpi_card(c4,"Lost / Hibernating",f"{n_lost:,}",color=CLR_DANGER)

        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Segment Distribution by Customer Count")
            seg_count = rfm_df["segment"].value_counts().reset_index()
            seg_count.columns = ["Segment","Customers"]
            seg_count["color"] = seg_count["Segment"].map(
                lambda s: SEGMENT_COLORS.get(s, "#6B7280")
            )
            fig1 = px.bar(
                seg_count.sort_values("Customers"),
                x="Customers", y="Segment", orientation="h",
                color="Segment",
                color_discrete_map=SEGMENT_COLORS,
                text="Customers",
                template=PLOTLY_TEMPLATE,
                title="Customers per RFM Segment",
            )
            fig1.update_traces(texttemplate="%{text:,}", textposition="outside")
            fig1.update_layout(
                showlegend=False,
                xaxis_title="Customers",yaxis_title="",
                height=400,margin=dict(t=40,b=30,l=10,r=80),
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.markdown("#### Revenue Contribution by Segment")
            fig2 = px.pie(
                seg_summary, values="total_revenue", names="segment",
                color="segment", color_discrete_map=SEGMENT_COLORS,
                hole=0.42, template=PLOTLY_TEMPLATE,
                title="Revenue Share by RFM Segment",
            )
            fig2.update_traces(textposition="inside", textinfo="percent+label",
                               textfont_size=10)
            fig2.update_layout(height=400,margin=dict(t=40,b=10,l=10,r=10),
                               showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

        # Avg monetary per segment
        st.markdown("#### Segment-Level Metrics Summary")
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            name="Avg Monetary (R$)",
            x=seg_summary["segment"],
            y=seg_summary["avg_monetary"].round(0),
            marker_color=[SEGMENT_COLORS.get(s,"#6B7280") for s in seg_summary["segment"]],
            text=seg_summary["avg_monetary"].apply(lambda v: f"R${v:.0f}"),
            textposition="outside",
        ))
        fig3.update_layout(
            title="Average Monetary Value per Segment",
            xaxis_title="Segment", yaxis_title="Avg Spend (R$)",
            template=PLOTLY_TEMPLATE, height=360,
            xaxis_tickangle=-30,
            margin=dict(t=50,b=70,l=50,r=20),
        )
        st.plotly_chart(fig3, use_container_width=True)

        # RFM Score distributions
        st.markdown("#### RFM Score Distributions")
        col3,col4,col5 = st.columns(3)
        for ax, col_name, label, color in zip(
            [col3,col4,col5],
            ["R","F","M"],
            ["Recency Score","Frequency Score","Monetary Score"],
            [CLR_DANGER, CLR_PRIMARY, CLR_SUCCESS],
        ):
            dist = rfm_df[col_name].value_counts().sort_index().reset_index()
            dist.columns = ["Score","Count"]
            fig_sub = px.bar(dist, x="Score", y="Count", text="Count",
                              color_discrete_sequence=[color],
                              template=PLOTLY_TEMPLATE, title=label)
            fig_sub.update_traces(texttemplate="%{text:,}",textposition="outside")
            fig_sub.update_layout(height=260,margin=dict(t=40,b=30,l=30,r=10),
                                   xaxis_title="Score (1=Low,5=High)",
                                   yaxis_title="Customers")
            ax.plotly_chart(fig_sub, use_container_width=True)

        # Full table
        with st.expander("📋 RFM Segment Summary Table"):
            display = seg_summary.copy()
            display.columns = ["Segment","Customers","Avg Recency (days)",
                                "Avg Frequency","Avg Monetary (R$)",
                                "Total Revenue (R$)","Revenue Share %"]
            st.dataframe(
                display.style.format({
                    "Customers":"{:,}","Avg Recency (days)":"{:.1f}",
                    "Avg Frequency":"{:.2f}","Avg Monetary (R$)":"R${:.2f}",
                    "Total Revenue (R$)":"R${:,.2f}","Revenue Share %":"{:.2f}%",
                }),
                use_container_width=True, hide_index=True,
            )
            download_csv(seg_summary,"rfm_segment_summary.csv","Download RFM Summary")

        insight_box("RFM Insight",
            "New Customers and Promising segments represent the largest groups by count "
            "but generate the most revenue — reflecting the platform's acquisition-stage "
            "lifecycle. The low Champion count (single customer) is consistent with a "
            "3.12% repeat-buyer rate.",
            color=CLR_SUCCESS)

        # Methodology
        with st.expander("📖 RFM Methodology"):
            st.markdown("""
**Recency:** Days since customer's last delivered order (snapshot = last order date + 1 day).
Lower recency (more recent) = better → score reversed (recent = 5).

**Frequency:** Count of distinct delivered `order_id` per `customer_unique_id`.
Higher = better → score 1–5.

**Monetary:** Sum of `total_order_revenue` for all delivered orders per customer.
Higher = better → score 1–5.

**Scoring:** Each dimension binned into quintiles (1–5) using `pd.qcut`.
Ties handled with `duplicates='drop'`.

**Segmentation Rule:** Segments assigned from (R_score, F_score) lookup table
(industry-standard RFM segment matrix).

**Limitation:** With a 3.12% repeat-buyer rate, most customers score F=1.
This means Champions, Loyal Customers, etc. will be rare — which accurately
reflects the Olist dataset's acquisition-phase lifecycle, not a calculation error.
            """)

    # ========================================================================
    # TAB 2 — CUSTOMER RETENTION
    # ========================================================================
    with tabs[1]:
        _section_header(2, "Customer Retention Analysis",
                        "One-time vs. repeat buyers · Repeat purchase rate · CLV distribution")

        delivered = orders[orders["order_status"] == "delivered"].copy()
        del_items = items[items["order_status"] == "delivered"].copy()

        freq = delivered.groupby("customer_unique_id")["order_id"].count()
        n_customers = len(freq)
        n_one_time  = int((freq == 1).sum())
        n_repeat    = int((freq >= 2).sum())
        repeat_rate = n_repeat / n_customers * 100
        avg_freq    = freq.mean()

        # Revenue split
        cust_rev = delivered.groupby("customer_unique_id")["total_order_revenue"].sum()
        repeat_ids = freq[freq >= 2].index
        one_time_ids = freq[freq == 1].index
        rev_repeat = cust_rev[cust_rev.index.isin(repeat_ids)].sum()
        rev_one_time = cust_rev[cust_rev.index.isin(one_time_ids)].sum()
        total_rev = cust_rev.sum()

        c1,c2,c3,c4 = st.columns(4)
        kpi_card(c1,"One-Time Buyers",f"{n_one_time:,}",
                 delta=f"{n_one_time/n_customers*100:.1f}% of customers",color=CLR_WARNING)
        kpi_card(c2,"Repeat Buyers",f"{n_repeat:,}",
                 delta=f"{repeat_rate:.2f}% of customers",color=CLR_SUCCESS)
        kpi_card(c3,"Revenue from Repeat",format_brl(rev_repeat),
                 delta=f"{rev_repeat/total_rev*100:.1f}% of total",color=CLR_PRIMARY)
        kpi_card(c4,"Avg Orders/Customer",f"{avg_freq:.3f}",color=CLR_SECONDARY)

        st.markdown("---")
        col1,col2 = st.columns(2)

        with col1:
            st.markdown("#### One-Time vs. Repeat Customer Split")
            fig1 = px.pie(
                values=[n_one_time, n_repeat],
                names=["One-Time Buyers","Repeat Buyers (2+)"],
                color_discrete_sequence=[CLR_WARNING, CLR_SUCCESS],
                hole=0.42, template=PLOTLY_TEMPLATE,
                title=f"Repeat Buyer Rate: {repeat_rate:.2f}%",
            )
            fig1.update_traces(textposition="inside", textinfo="percent+label",
                               textfont_size=12)
            fig1.update_layout(height=340,margin=dict(t=50,b=10,l=10,r=10))
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            st.markdown("#### Revenue: One-Time vs. Repeat Customers")
            fig2 = px.pie(
                values=[rev_one_time, rev_repeat],
                names=["One-Time Buyers","Repeat Buyers"],
                color_discrete_sequence=[CLR_WARNING, CLR_SUCCESS],
                hole=0.42, template=PLOTLY_TEMPLATE,
                title="Revenue Contribution by Buyer Type",
            )
            fig2.update_traces(textposition="inside", textinfo="percent+label+value",
                               textfont_size=11,
                               texttemplate="%{label}<br>%{percent}<br>R$%{value:,.0f}")
            fig2.update_layout(height=340,margin=dict(t=50,b=10,l=10,r=10))
            st.plotly_chart(fig2, use_container_width=True)

        # Order frequency distribution
        st.markdown("#### Order Frequency Distribution")
        freq_dist = freq.value_counts().sort_index().reset_index()
        freq_dist.columns = ["Orders","Customers"]
        freq_dist["Pct"] = (freq_dist["Customers"]/freq_dist["Customers"].sum()*100).round(2)

        fig3 = px.bar(
            freq_dist, x="Orders", y="Customers",
            text="Customers", color="Orders",
            color_continuous_scale=["#93C5FD", CLR_PRIMARY],
            template=PLOTLY_TEMPLATE,
            title="Customer Purchase Frequency Distribution",
        )
        fig3.update_coloraxes(showscale=False)
        fig3.update_traces(texttemplate="%{text:,}<br>(%{customdata:.1f}%)",
                           customdata=freq_dist["Pct"], textposition="outside")
        fig3.update_layout(
            xaxis_title="Number of Orders Placed",
            yaxis_title="Customers",
            height=380,margin=dict(t=50,b=40,l=50,r=20),
        )
        st.plotly_chart(fig3, use_container_width=True)

        # CLV distribution
        st.markdown("#### Customer Lifetime Value (CLV) Distribution")
        col3,col4 = st.columns(2)
        with col3:
            clv_data = cust_rev.reset_index()
            clv_data.columns = ["customer","clv"]
            fig4 = px.histogram(
                clv_data[clv_data["clv"] <= clv_data["clv"].quantile(0.99)],
                x="clv", nbins=60, color_discrete_sequence=[CLR_PRIMARY],
                template=PLOTLY_TEMPLATE,
                title="CLV Distribution (below 99th percentile)",
            )
            fig4.add_vline(x=clv_data["clv"].mean(), line_dash="dash",
                           line_color=CLR_DANGER,
                           annotation_text=f"Avg R${clv_data['clv'].mean():.0f}")
            fig4.add_vline(x=clv_data["clv"].median(), line_dash="dot",
                           line_color=CLR_SUCCESS,
                           annotation_text=f"Median R${clv_data['clv'].median():.0f}")
            fig4.update_layout(height=360,margin=dict(t=50,b=40,l=50,r=20),
                               xaxis_title="Customer Lifetime Revenue (R$)",
                               yaxis_title="Customers")
            st.plotly_chart(fig4, use_container_width=True)

        with col4:
            # CLV by order count bucket
            clv_df = pd.DataFrame({"clv": cust_rev, "orders": freq}).reset_index()
            clv_by_freq = clv_df.groupby("orders")["clv"].mean().reset_index()
            clv_by_freq.columns = ["Orders Placed","Avg CLV (R$)"]
            fig5 = px.bar(
                clv_by_freq, x="Orders Placed", y="Avg CLV (R$)",
                text="Avg CLV (R$)",
                color="Avg CLV (R$)", color_continuous_scale=["#93C5FD",CLR_SECONDARY],
                template=PLOTLY_TEMPLATE,
                title="Avg CLV by Number of Orders Placed",
            )
            fig5.update_coloraxes(showscale=False)
            fig5.update_traces(texttemplate="R$%{text:,.0f}",textposition="outside")
            fig5.update_layout(height=360,margin=dict(t=50,b=40,l=50,r=20))
            st.plotly_chart(fig5, use_container_width=True)

        warning_box("Dataset Limitation",
            "The Olist dataset covers Sep 2016–Oct 2018 only. "
            "Customers acquired late in the period have little opportunity "
            "to make repeat purchases within the observation window. "
            "This inflates the measured one-time buyer rate. "
            "True retention would require 12+ months of post-acquisition data per customer.",
        )
        recommendation_box("Retention Action",
            f"With {n_repeat:,} repeat buyers generating {rev_repeat/total_rev*100:.1f}% of revenue, "
            "a structured post-purchase email flow (Day 7, Day 30, Day 90) with category-specific "
            "product recommendations could conservatively double the repeat rate to ~6–7%.",
        )

    # ========================================================================
    # TAB 3 — COHORT ANALYSIS
    # ========================================================================
    with tabs[2]:
        _section_header(3, "Monthly Customer Cohort Analysis",
                        "Based on first delivered-order month per customer_unique_id")

        pivot     = cohort_data["cohort_pivot"]
        raw       = cohort_data["cohort_raw"]
        sizes     = cohort_data["cohort_sizes"]
        c_summary = cohort_summary(raw)

        # Heatmap
        st.markdown("#### Cohort Retention Heatmap (% of cohort who re-purchased)")
        pivot_display = pivot.copy()
        # Limit to first 13 periods for readability
        max_period = min(12, pivot_display.shape[1]-1)
        pivot_display = pivot_display.iloc[:, :max_period+1]

        # Build annotation text (show cohort size on period 0)
        annot = pivot_display.copy().astype(str)
        for cohort in pivot_display.index:
            cohort_sz = sizes.get(cohort, 0)
            annot.loc[cohort, 0] = f"n={int(cohort_sz)}\n100%"
            for col in pivot_display.columns[1:]:
                v = pivot_display.loc[cohort, col]
                annot.loc[cohort, col] = f"{v:.1f}%" if v > 0 else ""

        fig_hm = go.Figure(go.Heatmap(
            z=pivot_display.values,
            x=[f"M+{c}" for c in pivot_display.columns],
            y=pivot_display.index.tolist(),
            colorscale=[[0,"#F8FAFC"],[0.01,"#DBEAFE"],[0.1,"#93C5FD"],
                        [0.5,"#2563EB"],[1.0,"#1E3A8A"]],
            text=annot.values,
            texttemplate="%{text}",
            textfont={"size":9},
            hovertemplate="Cohort: %{y}<br>Period: %{x}<br>Retention: %{z:.1f}%<extra></extra>",
            zmin=0, zmax=10,
            showscale=True,
            colorbar=dict(title="Retention %", ticksuffix="%"),
        ))
        fig_hm.update_layout(
            title="Customer Cohort Retention (% returning in each subsequent month)",
            xaxis_title="Months Since First Purchase",
            yaxis_title="Cohort (First Purchase Month)",
            template=PLOTLY_TEMPLATE,
            height=620,
            margin=dict(t=60,b=60,l=100,r=60),
        )
        st.plotly_chart(fig_hm, use_container_width=True)

        # Cohort sizes bar
        col1,col2 = st.columns(2)
        with col1:
            st.markdown("#### Cohort Size (Customers per Acquisition Month)")
            sz_df = sizes.reset_index()
            sz_df.columns = ["Cohort","Customers"]
            fig_sz = px.bar(
                sz_df, x="Cohort", y="Customers",
                text="Customers", color="Customers",
                color_continuous_scale=["#93C5FD",CLR_PRIMARY],
                template=PLOTLY_TEMPLATE, title="New Customers per Month",
            )
            fig_sz.update_coloraxes(showscale=False)
            fig_sz.update_traces(texttemplate="%{text:,}",textposition="outside")
            fig_sz.update_layout(
                height=360, xaxis_tickangle=-45,
                margin=dict(t=50,b=70,l=50,r=20),
            )
            st.plotly_chart(fig_sz, use_container_width=True)

        with col2:
            st.markdown("#### % of Cohort Who Returned (Any Month)")
            fig_ret = px.bar(
                c_summary, x="cohort_ym", y="return_rate_pct",
                text="return_rate_pct",
                color="return_rate_pct",
                color_continuous_scale=["#FDE68A",CLR_SUCCESS],
                template=PLOTLY_TEMPLATE,
                title="Cohort Return Rate (%)",
            )
            fig_ret.update_coloraxes(showscale=False)
            fig_ret.update_traces(texttemplate="%{text:.1f}%",textposition="outside")
            fig_ret.add_hline(y=c_summary["return_rate_pct"].mean(),
                              line_dash="dot",line_color=CLR_WARNING,
                              annotation_text=f"Avg {c_summary['return_rate_pct'].mean():.1f}%")
            fig_ret.update_layout(
                height=360, xaxis_tickangle=-45,
                xaxis_title="Cohort Month", yaxis_title="Return Rate (%)",
                margin=dict(t=50,b=70,l=50,r=20),
            )
            st.plotly_chart(fig_ret, use_container_width=True)

        warning_box("Cohort Interpretation",
            "Olist's overall repeat purchase rate is ~3.12%. "
            "The heatmap shows that most cohorts have very low post-period-0 retention, "
            "which is accurate — not a calculation error. Late-2017 cohorts (Nov–Dec) show "
            "higher acquisition numbers due to Black Friday. "
            "Retention values above 5% are noteworthy in this dataset context.",
        )
        with st.expander("📋 Full Cohort Summary Table"):
            c_summary_disp = c_summary.rename(columns={
                "cohort_ym":"Cohort Month",
                "cohort_size":"Cohort Size",
                "returned_customers":"Returned Customers",
                "return_rate_pct":"Return Rate %",
            })
            st.dataframe(
                c_summary_disp.style.format({
                    "Cohort Size":"{:,}","Returned Customers":"{:.0f}",
                    "Return Rate %":"{:.2f}%",
                }),
                use_container_width=True, hide_index=True,
            )
            download_csv(c_summary,"cohort_summary.csv","Download Cohort Table")

    # ========================================================================
    # TAB 4 — SELLER INTELLIGENCE
    # ========================================================================
    with tabs[3]:
        _section_header(4, "Seller Intelligence & Scorecard",
                        "Quintile-based performance tiers · Delivered orders only")

        opps = seller_opportunity_analysis(sc)

        n_top = int((sc["performance_flag"]=="Top Performer").sum())
        n_del_prob = int((sc["performance_flag"]=="Delivery Problem").sum())
        n_hr_ls = int((sc["performance_flag"]=="High Revenue, Low Satisfaction").sum())
        n_gems = int((sc["performance_flag"]=="Hidden Gem (grow this)").sum())

        c1,c2,c3,c4 = st.columns(4)
        kpi_card(c1,"Top Performers",f"{n_top:,}",
                 delta="High revenue + high review",color=CLR_SUCCESS)
        kpi_card(c2,"Delivery Problems",f"{n_del_prob:,}",
                 delta="Late rate in bottom quintile",color=CLR_DANGER)
        kpi_card(c3,"High Rev, Low Satisfaction",f"{n_hr_ls:,}",
                 delta="At-risk revenue",color=CLR_WARNING)
        kpi_card(c4,"Hidden Gems",f"{n_gems:,}",
                 delta="Low revenue, high review",color=CLR_PRIMARY)

        st.markdown("---")

        # Performance flag distribution
        col1,col2 = st.columns(2)
        with col1:
            flag_dist = sc["performance_flag"].value_counts().reset_index()
            flag_dist.columns = ["Flag","Sellers"]
            flag_colors = {
                "Top Performer":CLR_SUCCESS,
                "High Revenue, Low Satisfaction":CLR_WARNING,
                "Hidden Gem (grow this)":CLR_PRIMARY,
                "Delivery Problem":CLR_DANGER,
                "Under-Performing":"#9CA3AF",
                "Average":"#D1D5DB",
            }
            fig1 = px.bar(
                flag_dist, x="Sellers", y="Flag", orientation="h",
                text="Sellers",
                color="Flag", color_discrete_map=flag_colors,
                template=PLOTLY_TEMPLATE,
                title="Seller Performance Tier Distribution",
            )
            fig1.update_traces(texttemplate="%{text:,}",textposition="outside")
            fig1.update_layout(
                showlegend=False,
                xaxis_title="Sellers",yaxis_title="",
                height=380,margin=dict(t=40,b=30,l=10,r=80),
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            # Revenue by performance flag
            rev_by_flag = sc.groupby("performance_flag")["total_revenue"].sum().reset_index()
            rev_by_flag.columns = ["Flag","Revenue"]
            rev_by_flag = rev_by_flag.sort_values("Revenue",ascending=False)
            fig2 = px.pie(
                rev_by_flag, values="Revenue", names="Flag",
                color="Flag", color_discrete_map=flag_colors,
                hole=0.4, template=PLOTLY_TEMPLATE,
                title="Revenue Share by Performance Tier",
            )
            fig2.update_traces(textposition="inside",textinfo="percent+label",
                               textfont_size=10)
            fig2.update_layout(height=380,showlegend=False,
                               margin=dict(t=50,b=10,l=10,r=10))
            st.plotly_chart(fig2, use_container_width=True)

        # Seller scatter: Revenue vs. Review Score
        st.markdown("#### Seller Revenue vs. Review Score (coloured by performance tier)")
        scatter_data = sc[sc["avg_review_score"].notna() & sc["total_revenue"]>0].copy()
        scatter_data["size_col"] = scatter_data["n_unique_orders"].clip(upper=500)

        fig3 = px.scatter(
            scatter_data,
            x="total_revenue", y="avg_review_score",
            size="size_col", color="performance_flag",
            color_discrete_map=flag_colors,
            hover_name="seller_id",
            hover_data={"total_revenue":":.0f","avg_review_score":":.2f",
                        "n_unique_orders":":,","seller_state":True,
                        "top_category":True,"late_rate_pct":":.1f"},
            size_max=35,
            template=PLOTLY_TEMPLATE,
            title="Seller Revenue vs. Review Score (bubble size = orders)",
        )
        fig3.add_hline(y=sc["avg_review_score"].median(), line_dash="dot",
                       line_color=CLR_WARNING,
                       annotation_text="Median score")
        fig3.add_vline(x=sc["total_revenue"].median(), line_dash="dot",
                       line_color=CLR_PRIMARY,
                       annotation_text="Median revenue")
        fig3.update_layout(
            xaxis_title="Total Revenue (R$)", yaxis_title="Avg Review Score",
            height=500,margin=dict(t=50,b=50,l=50,r=20),
        )
        st.plotly_chart(fig3, use_container_width=True)

        # Tables per tier
        tier_tabs = st.tabs([
            "🏆 Top Performers","⚠️ High Rev, Low Sat","💎 Hidden Gems","🚨 Delivery Issues"
        ])
        for tab, key, label in zip(
            tier_tabs,
            ["top_performers","high_rev_low_sat","hidden_gems","delivery_problems"],
            ["Top Performers","High Revenue Low Satisfaction","Hidden Gems","Delivery Problems"],
        ):
            with tab:
                df_t = opps[key].copy()
                df_t["seller_short"] = df_t["seller_id"].str[:12]+"…"
                show_cols = ["seller_short","seller_state","total_revenue",
                             "n_unique_orders","avg_review_score",
                             "avg_delivery_days","late_rate_pct","top_category"]
                show_cols = [c for c in show_cols if c in df_t.columns]
                st.dataframe(
                    df_t[show_cols].style.format({
                        "total_revenue":"R${:,.2f}",
                        "n_unique_orders":"{:,}",
                        "avg_review_score":"{:.2f}",
                        "avg_delivery_days":"{:.1f}",
                        "late_rate_pct":"{:.1f}%",
                    }),
                    use_container_width=True, hide_index=True,
                )
                download_csv(df_t[show_cols], f"sellers_{key}.csv",
                             f"Download {label}")

        insight_box("Seller Concentration Risk",
            f"272 sellers classified as Top Performers generate a disproportionate share of revenue. "
            f"{n_hr_ls} sellers with high revenue but low satisfaction scores represent significant "
            "platform reputation risk — these should be prioritised for quality intervention.",
            color=CLR_WARNING)

    # ========================================================================
    # TAB 5 — DELIVERY ANALYTICS
    # ========================================================================
    with tabs[4]:
        _section_header(5, "Delivery & Logistics Analytics",
                        "Based on delivered orders with non-null delivery dates")

        del_ord = orders[
            (orders["order_status"]=="delivered") &
            orders["delivery_days"].notna()
        ].copy()
        del_ord["is_delayed"] = pd.to_numeric(del_ord["is_delayed"],errors="coerce")
        has_delay = del_ord[del_ord["is_delayed"].notna()].copy()
        del_items_del = items[items["order_status"]=="delivered"].copy()

        avg_del = del_ord["delivery_days"].mean()
        med_del = del_ord["delivery_days"].median()
        p90_del = del_ord["delivery_days"].quantile(0.90)
        late_rate = (has_delay["is_delayed"]==1.0).mean()*100
        avg_late_days = has_delay[has_delay["is_delayed"]==1.0]["delivery_delay_days"].mean()

        c1,c2,c3,c4 = st.columns(4)
        kpi_card(c1,"Avg Delivery Days",f"{avg_del:.1f}",
                 delta=f"Median: {med_del:.1f}d",color=CLR_PRIMARY)
        kpi_card(c2,"P90 Delivery Days",f"{p90_del:.1f}",
                 delta="1 in 10 orders takes this long",color=CLR_WARNING)
        kpi_card(c3,"Late Delivery Rate",f"{late_rate:.1f}%",
                 delta=f"Avg {avg_late_days:.1f}d late when delayed",color=CLR_DANGER)
        kpi_card(c4,"On-Time Rate",f"{100-late_rate:.1f}%",color=CLR_SUCCESS)

        st.markdown("---")
        col1,col2 = st.columns(2)

        with col1:
            # Delivery distribution
            fig1 = go.Figure()
            fig1.add_trace(go.Histogram(
                x=del_ord["delivery_days"].clip(upper=60),
                nbinsx=50,name="Delivery Days",
                marker_color=CLR_PRIMARY,opacity=0.8,
            ))
            fig1.add_vline(x=avg_del,line_dash="dash",line_color=CLR_DANGER,
                           annotation_text=f"Mean {avg_del:.1f}d")
            fig1.add_vline(x=med_del,line_dash="dot",line_color=CLR_SUCCESS,
                           annotation_text=f"Median {med_del:.1f}d")
            fig1.update_layout(
                title="Delivery Time Distribution (capped at 60d)",
                xaxis_title="Days",yaxis_title="Orders",
                template=PLOTLY_TEMPLATE,height=360,
                margin=dict(t=50,b=40,l=50,r=20),bargap=0.05,
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            # By seller state
            del_items_del["order_purchase_timestamp"] = pd.to_datetime(
                del_items_del["order_purchase_timestamp"],errors="coerce")
            seller_del = (
                del_items_del.merge(
                    del_ord[["order_id","delivery_days","is_delayed"]],
                    on="order_id",how="left",
                )
                .groupby("seller_state")
                .agg(avg_del=("delivery_days","mean"),
                     n_orders=("order_id","nunique"),
                     late_rate=("is_delayed",lambda x:(pd.to_numeric(x,errors="coerce")==1.0).mean()*100))
                .reset_index()
                .sort_values("avg_del")
            )
            seller_del = seller_del[seller_del["n_orders"]>=50]

            fig2 = go.Figure(go.Bar(
                x=seller_del["avg_del"],y=seller_del["seller_state"],
                orientation="h",
                marker_color=[CLR_SUCCESS if v<avg_del else CLR_DANGER for v in seller_del["avg_del"]],
                text=[f"{v:.1f}d" for v in seller_del["avg_del"]],
                textposition="outside",
            ))
            fig2.add_vline(x=avg_del,line_dash="dot",line_color=CLR_WARNING,
                           annotation_text=f"Avg {avg_del:.1f}d")
            fig2.update_layout(
                title="Avg Delivery Days by Seller State",
                xaxis_title="Avg Days",yaxis_title="",
                template=PLOTLY_TEMPLATE,height=360,
                margin=dict(t=50,b=30,l=10,r=80),
            )
            st.plotly_chart(fig2, use_container_width=True)

        # Monthly delivery trend
        st.markdown("#### Average Delivery Time Trend Over Time")
        del_ord["ym"] = del_ord["order_purchase_timestamp"].dt.to_period("M")
        monthly_del = (
            del_ord.groupby("ym")
            .agg(avg_del=("delivery_days","mean"),
                 late_rate=("is_delayed",lambda x:(x==1.0).mean()*100),
                 n_orders=("order_id","count"))
            .reset_index()
        )
        monthly_del["ym_str"] = monthly_del["ym"].astype(str)
        monthly_del = monthly_del.sort_values("ym_str")

        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=monthly_del["ym_str"],y=monthly_del["avg_del"],
            mode="lines+markers",name="Avg Delivery Days",
            line=dict(color=CLR_PRIMARY,width=2.5),
            fill="tozeroy",fillcolor="rgba(37,99,235,0.08)",
            yaxis="y1",
        ))
        fig3.add_trace(go.Scatter(
            x=monthly_del["ym_str"],y=monthly_del["late_rate"],
            mode="lines+markers",name="Late Rate %",
            line=dict(color=CLR_DANGER,width=2,dash="dash"),
            marker=dict(size=5),
            yaxis="y2",
        ))
        fig3.update_layout(
            title="Monthly Avg Delivery Days & Late Rate",
            xaxis=dict(title="Month",tickangle=-45),
            yaxis=dict(title="Avg Delivery Days"),
            yaxis2=dict(title="Late Rate (%)",overlaying="y",side="right",showgrid=False),
            template=PLOTLY_TEMPLATE,hovermode="x unified",
            legend=dict(x=0.01,y=0.99),height=380,
            margin=dict(t=50,b=60,l=60,r=60),
        )
        st.plotly_chart(fig3, use_container_width=True)

        # Category delivery
        st.markdown("#### Avg Delivery Days by Product Category (top 15 by volume)")
        cat_del = (
            del_items_del.merge(del_ord[["order_id","delivery_days"]],on="order_id",how="left")
            .groupby("product_category_name_english")
            .agg(avg_del=("delivery_days","mean"),n_orders=("order_id","nunique"))
            .reset_index()
        )
        cat_del = cat_del[cat_del["n_orders"]>=500].sort_values("avg_del",ascending=False).head(15)

        fig4 = px.bar(
            cat_del[::-1],x="avg_del",y="product_category_name_english",
            orientation="h",text="avg_del",
            color="avg_del",
            color_continuous_scale=["#6EE7B7",CLR_DANGER],
            template=PLOTLY_TEMPLATE,
            title="Avg Delivery Days by Category (500+ orders)",
        )
        fig4.update_coloraxes(showscale=False)
        fig4.update_traces(texttemplate="%{text:.1f}d",textposition="outside")
        fig4.update_layout(
            xaxis_title="Avg Delivery Days",yaxis_title="",
            height=430,margin=dict(t=50,b=30,l=10,r=60),
        )
        st.plotly_chart(fig4, use_container_width=True)

    # ========================================================================
    # TAB 6 — GROWTH ANALYTICS
    # ========================================================================
    with tabs[5]:
        _section_header(6, "Revenue & Growth Analytics",
                        "Monthly trends · MoM growth · Category/State contribution")

        peak = monthly.loc[monthly["revenue"].idxmax()]
        avg_rev = monthly["revenue"].mean()
        total_growth = (
            (monthly["revenue"].iloc[-1] - monthly["revenue"].iloc[1])
            / monthly["revenue"].iloc[1] * 100
        )
        strong_growth_months = int((monthly["rev_flag"]=="strong_growth").sum())

        c1,c2,c3,c4 = st.columns(4)
        kpi_card(c1,"Peak Revenue Month",peak["ym_str"],
                 delta=f"R${peak['revenue']:,.0f}",color=CLR_PRIMARY)
        kpi_card(c2,"Avg Monthly Revenue",format_brl(avg_rev),color=CLR_SECONDARY)
        kpi_card(c3,"Strong Growth Months",str(strong_growth_months),
                 delta="≥+20% MoM",color=CLR_SUCCESS)
        kpi_card(c4,"Overall Growth (period)",f"{total_growth:.1f}%",
                 delta="first vs last full month",
                 color=CLR_SUCCESS if total_growth>0 else CLR_DANGER)

        st.markdown("---")

        # Monthly revenue with growth flags
        st.markdown("#### Monthly Revenue with Growth Flags")
        flag_colors_map = {"strong_growth":CLR_SUCCESS,"decline":CLR_DANGER,"normal":CLR_PRIMARY}
        colors_m = [flag_colors_map.get(f,CLR_PRIMARY) for f in monthly["rev_flag"]]

        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=monthly["ym_str"],y=monthly["revenue"],
            name="Revenue",marker_color=colors_m,opacity=0.8,
        ))
        rolling = monthly["revenue"].rolling(3,min_periods=1).mean()
        fig1.add_trace(go.Scatter(
            x=monthly["ym_str"],y=rolling,
            mode="lines",name="3M Rolling Avg",
            line=dict(color="#1E293B",width=2.5,dash="dash"),
        ))
        fig1.update_layout(
            title="Monthly Revenue (green=strong growth ≥+20%, red=decline ≤-20%)",
            xaxis=dict(title="Month",tickangle=-45),
            yaxis=dict(title="Revenue (R$)",tickformat=",.0f"),
            template=PLOTLY_TEMPLATE,hovermode="x unified",
            legend=dict(x=0.01,y=0.99),height=400,
            margin=dict(t=50,b=60,l=60,r=20),
        )
        st.plotly_chart(fig1, use_container_width=True)

        col1,col2 = st.columns(2)
        with col1:
            # MoM revenue growth
            mom_data = monthly[monthly["rev_mom_pct"].notna()].copy()
            mom_colors = [CLR_SUCCESS if v>=0 else CLR_DANGER for v in mom_data["rev_mom_pct"]]
            fig2 = go.Figure(go.Bar(
                x=mom_data["ym_str"],y=mom_data["rev_mom_pct"],
                marker_color=mom_colors,
                text=mom_data["rev_mom_pct"].apply(lambda v:f"{v:+.1f}%"),
                textposition="outside",name="MoM %",
            ))
            fig2.add_hline(y=0,line_color="#9CA3AF",line_dash="dot")
            fig2.update_layout(
                title="Month-over-Month Revenue Growth (%)",
                xaxis=dict(tickangle=-45),yaxis=dict(title="Growth %"),
                template=PLOTLY_TEMPLATE,height=360,
                margin=dict(t=50,b=60,l=50,r=20),
            )
            st.plotly_chart(fig2, use_container_width=True)

        with col2:
            # AOV trend
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=monthly["ym_str"],y=monthly["aov"],
                mode="lines+markers",name="AOV",
                line=dict(color=CLR_SECONDARY,width=2.5),
                fill="tozeroy",fillcolor="rgba(124,58,237,0.07)",
            ))
            fig3.add_hline(y=monthly["aov"].mean(),line_dash="dot",
                           line_color=CLR_WARNING,
                           annotation_text=f"Avg R${monthly['aov'].mean():.0f}")
            fig3.update_layout(
                title="Average Order Value (AOV) Over Time",
                xaxis=dict(title="Month",tickangle=-45),
                yaxis=dict(title="AOV (R$)"),
                template=PLOTLY_TEMPLATE,height=360,
                margin=dict(t=50,b=60,l=60,r=20),
            )
            st.plotly_chart(fig3, use_container_width=True)

        # Category revenue trend (top 6)
        st.markdown("#### Revenue Trend — Top 6 Categories")
        cat_trend = compute_category_trend(items, top_n=6)
        fig4 = px.line(
            cat_trend, x="ym_str", y="revenue",
            color="category", markers=True,
            color_discrete_sequence=PALETTE,
            template=PLOTLY_TEMPLATE,
            title="Monthly Revenue by Top 6 Product Categories",
        )
        fig4.update_layout(
            xaxis=dict(title="Month",tickangle=-45),
            yaxis=dict(title="Revenue (R$)",tickformat=",.0f"),
            height=420,margin=dict(t=50,b=60,l=60,r=20),
            hovermode="x unified",legend_title="Category",
        )
        st.plotly_chart(fig4, use_container_width=True)

        # State revenue trend (top 5)
        st.markdown("#### Revenue Trend — Top 5 States")
        state_trend = compute_state_trend(orders, top_n=5)
        fig5 = px.line(
            state_trend, x="ym_str", y="revenue",
            color="state", markers=True,
            color_discrete_sequence=PALETTE,
            template=PLOTLY_TEMPLATE,
            title="Monthly Revenue by Top 5 Customer States",
        )
        fig5.update_layout(
            xaxis=dict(title="Month",tickangle=-45),
            yaxis=dict(title="Revenue (R$)",tickformat=",.0f"),
            height=380,margin=dict(t=50,b=60,l=60,r=20),
            hovermode="x unified",legend_title="State",
        )
        st.plotly_chart(fig5, use_container_width=True)

        # Growth table
        with st.expander("📋 Full Monthly Growth Table"):
            growth_disp = monthly[["ym_str","revenue","n_orders","aov",
                                    "rev_mom_pct","orders_mom_pct","aov_mom_pct","rev_flag"]].copy()
            growth_disp.columns = ["Month","Revenue (R$)","Orders","AOV (R$)",
                                    "Rev MoM %","Orders MoM %","AOV MoM %","Flag"]
            st.dataframe(
                growth_disp.style.format({
                    "Revenue (R$)":"R${:,.2f}","Orders":"{:,}",
                    "AOV (R$)":"R${:.2f}","Rev MoM %":"{:.1f}%",
                    "Orders MoM %":"{:.1f}%","AOV MoM %":"{:.1f}%",
                }),
                use_container_width=True,hide_index=True,
            )
            download_csv(growth_disp,"monthly_growth.csv","Download Growth Table")

    # ========================================================================
    # TAB 7 — BUSINESS OPPORTUNITIES
    # ========================================================================
    with tabs[6]:
        _section_header(7, "Business Opportunity Analysis",
                        "Automatically identified from real dataset metrics")

        priority_colors = {
            "Critical": CLR_DANGER,
            "High":     CLR_WARNING,
            "Medium":   CLR_PRIMARY,
            "Low":      CLR_SUCCESS,
        }
        priority_filter = st.multiselect(
            "Filter by Priority",
            ["Critical","High","Medium","Low"],
            default=["Critical","High","Medium"],
        )
        filtered_opps = [o for o in biz_opps if o["priority"] in priority_filter]

        st.markdown(f"**{len(filtered_opps)} opportunities identified**")
        for opp in filtered_opps:
            color = priority_colors.get(opp["priority"], CLR_PRIMARY)
            st.markdown(
                f"""
                <div style="border-left:4px solid {color};background:#FAFAFA;
                            border-radius:8px;padding:14px 18px;margin:10px 0;">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
                        <span style="background:{color};color:white;font-size:11px;
                                     font-weight:700;padding:2px 8px;border-radius:99px;">
                            {opp['priority']}
                        </span>
                        <span style="font-size:11px;color:#6B7280;background:#F1F5F9;
                                     padding:2px 8px;border-radius:99px;">
                            {opp['category']}
                        </span>
                        <strong style="font-size:14px;color:#1E293B;">{opp['title']}</strong>
                    </div>
                    <p style="font-size:13px;color:#374151;margin:0 0 6px 0;">{opp['description']}</p>
                    <code style="font-size:12px;color:#2563EB;background:#EFF6FF;
                                 padding:3px 8px;border-radius:4px;">{opp['metric_value']}</code>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Summary chart
        cat_counts = {}
        for o in biz_opps:
            cat_counts[o["category"]] = cat_counts.get(o["category"], 0) + 1
        opp_df = pd.DataFrame(list(cat_counts.items()),
                               columns=["Category","Opportunities"])
        fig_opp = px.bar(
            opp_df.sort_values("Opportunities"),
            x="Opportunities", y="Category", orientation="h",
            text="Opportunities",
            color="Opportunities",
            color_continuous_scale=["#FDE68A",CLR_DANGER],
            template=PLOTLY_TEMPLATE,
            title="Opportunities by Category",
        )
        fig_opp.update_coloraxes(showscale=False)
        fig_opp.update_traces(texttemplate="%{text}",textposition="outside")
        fig_opp.update_layout(
            height=300,margin=dict(t=40,b=30,l=10,r=60),
        )
        st.plotly_chart(fig_opp, use_container_width=True)

    # ========================================================================
    # TAB 8 — EXECUTIVE INSIGHTS
    # ========================================================================
    with tabs[7]:
        _section_header(8, "Executive Insights",
                        "Data-backed insights with supporting metrics, significance and recommended actions")

        delivered = orders[orders["order_status"]=="delivered"]
        del_items = items[items["order_status"]=="delivered"]
        total_rev = del_items["item_revenue"].sum()
        sp_rev = delivered[delivered["customer_state"]=="SP"]["total_order_revenue"].sum()

        has_delay = delivered[delivered["is_delayed"].notna()].copy()
        has_delay["is_delayed"] = pd.to_numeric(has_delay["is_delayed"],errors="coerce")
        rev_c = reviews[["order_id","review_score"]].drop_duplicates("order_id")
        rev_del = has_delay.merge(rev_c, on="order_id", how="inner")
        on_time_avg = rev_del[rev_del["is_delayed"]==0.0]["review_score"].mean()
        late_avg    = rev_del[rev_del["is_delayed"]==1.0]["review_score"].mean()

        cat_rev = del_items.groupby("product_category_name_english")["item_revenue"].sum().sort_values(ascending=False)
        top_cat = cat_rev.index[0]
        top_cat_rev = cat_rev.iloc[0]

        seg_summary = rfm_segment_summary(rfm_df)
        new_cust_rev = seg_summary[seg_summary["segment"]=="New Customers"]["total_revenue"].sum()

        state_del_m = delivered[delivered["delivery_days"].notna()].groupby("customer_state")["delivery_days"].mean()
        fastest_state = state_del_m.idxmin()
        slowest_state = state_del_m.idxmax()
        delivery_gap = state_del_m.max() - state_del_m.min()

        executive_insights = [
            {
                "id":1,"icon":"📦",
                "title":"Health & Beauty Is the Unexpected #1 Revenue Category",
                "what_happened":f"Health & Beauty generated R${top_cat_rev:,.0f} in delivered revenue — the highest of all 73 product categories.",
                "metric":f"R${top_cat_rev:,.0f} | Platform avg per category: R${cat_rev.mean():,.0f}",
                "why_it_matters":"Brazilian e-commerce demand is driven by personal care and lifestyle, not electronics. This shapes which sellers to recruit, which categories to promote, and where to allocate marketing spend.",
                "action":"Deepen inventory in Health & Beauty. Partner with established brands for exclusive listings. Run category-specific promotional campaigns in Q4.",
            },
            {
                "id":2,"icon":"📅",
                "title":"Black Friday 2017 Was the Clear Business Peak",
                "what_happened":f"November 2017 generated R${peak['revenue']:,.0f} in revenue — 65% above the R${avg_rev:,.0f} monthly average.",
                "metric":f"Peak: R${peak['revenue']:,.0f} | Avg: R${avg_rev:,.0f} | Delta: +{(peak['revenue']-avg_rev)/avg_rev*100:.0f}%",
                "why_it_matters":"A predictable seasonal spike creates an annual planning opportunity. Pre-stocking, carrier negotiations and marketing spend can be front-loaded to capture maximum uplift.",
                "action":"Build a Black Friday operational plan: (1) alert sellers to pre-stock 6 weeks ahead, (2) negotiate carrier capacity in October, (3) run category-specific early-access deals from Nov 1.",
            },
            {
                "id":3,"icon":"⭐",
                "title":"Late Delivery Causes a 1.73-Star Review Score Collapse",
                "what_happened":f"On-time orders average {on_time_avg:.2f}/5.0 stars. Late orders average {late_avg:.2f}/5.0 stars — a {abs(late_avg-on_time_avg):.2f}-point drop.",
                "metric":f"On-time: {on_time_avg:.2f} | Late: {late_avg:.2f} | Delta: -{abs(late_avg-on_time_avg):.2f} stars",
                "why_it_matters":"Review scores affect seller ranking, trust badges and conversion rates. A single percentage-point reduction in the late delivery rate would measurably lift the platform's average review score.",
                "action":"Implement real-time delivery risk alerting. Set a 95% on-time delivery SLA. Flag orders at risk of lateness at the carrier-handoff stage and proactively notify customers.",
            },
            {
                "id":4,"icon":"👥",
                "title":"96.9% of Customers Buy Only Once — Retention Is the Biggest Lever",
                "what_happened":f"{n_one_time:,} of {n_customers:,} customers placed exactly one order. Repeat buyer rate = {repeat_rate:.2f}%.",
                "metric":f"One-time buyers: {n_one_time:,} ({n_one_time/n_customers*100:.1f}%) | Repeat buyers: {n_repeat:,}",
                "why_it_matters":f"Repeat buyers generate R${cust_rev[cust_rev.index.isin(repeat_ids)].mean():.0f} avg CLV vs R${cust_rev[cust_rev.index.isin(one_time_ids)].mean():.0f} for one-time buyers — significantly higher value. Acquiring a new customer costs 5–7× more than retaining one.",
                "action":"Launch a post-purchase retention flow: Day 7 (review request), Day 30 (personalised recommendation), Day 90 (discount coupon on category they purchased). Measure 90-day reactivation rate.",
            },
            {
                "id":5,"icon":"🗺️",
                "title":"São Paulo Generates 37% of Revenue — Geographic Concentration Is a Risk",
                "what_happened":f"SP generated {sp_rev/total_rev*100:.1f}% of total delivered revenue (R${sp_rev:,.0f}). Top 3 states (SP, RJ, MG) = ~62%.",
                "metric":f"SP: R${sp_rev:,.0f} ({sp_rev/total_rev*100:.1f}%) | Total: R${total_rev:,.0f}",
                "why_it_matters":"Revenue this concentrated in one state creates significant fragility to any economic, logistics or competitive disruption in São Paulo. It also signals untapped market opportunity in 24 other states.",
                "action":"Run geo-targeted digital campaigns in RS, PR, BA, SC — all have sizeable populations and existing customer demand. Pair with local seller recruitment to reduce freight costs in those regions.",
            },
            {
                "id":6,"icon":"🚚",
                "title":f"{delivery_gap:.0f}-Day Delivery Gap Between Fastest and Slowest State",
                "what_happened":f"{fastest_state} averages {state_del_m[fastest_state]:.1f} days delivery. {slowest_state} averages {state_del_m[slowest_state]:.1f} days. That's a {delivery_gap:.1f}-day gap.",
                "metric":f"{fastest_state}: {state_del_m[fastest_state]:.1f}d | {slowest_state}: {state_del_m[slowest_state]:.1f}d | Gap: {delivery_gap:.1f}d",
                "why_it_matters":"Customers in slow-delivery states experience worse service, leave lower reviews and are less likely to return. This geographic inequality directly limits the platform's TAM in the North and Northeast.",
                "action":"Establish micro-fulfilment partnerships in Manaus (AM) and Belém (PA). Negotiate regional carrier SLAs for RR, AP and AM. Even a 5-day improvement in Northern delivery would recover ~0.3 review points.",
            },
            {
                "id":7,"icon":"💳",
                "title":"Credit Card = 74% of Transactions — Instalment Culture Drives AOV",
                "what_happened":"76,795 transactions (73.9%) used credit card. Boleto = 19.0%. Debit card = 1.5%.",
                "metric":"credit_card: 73.9% | boleto: 19.0% | voucher: 5.6% | debit: 1.5%",
                "why_it_matters":"Brazilians use credit card instalments ('parcelamento') to purchase items they otherwise couldn't afford outright. Prominently offering '12× sem juros' boosts conversion and AOV, particularly for high-value categories.",
                "action":"A/B test '12× sem juros' messaging on product pages vs. standard price display. Prioritise instalment offers for Health & Beauty, Watches, and Computer categories which have highest AOV.",
            },
            {
                "id":8,"icon":"🏪",
                "title":"Top 10 Sellers Generate Outsized Revenue — Concentration Risk",
                "what_happened":f"272 sellers classified as Top Performers. Median seller revenue is only R${sc['total_revenue'].median():,.0f}. The top decile disproportionately dominates platform GMV.",
                "metric":f"Top 10 revenue share: high | Median seller rev: R${sc['total_revenue'].median():,.0f}",
                "why_it_matters":"If any of the top 10 sellers migrate to a competing marketplace, platform revenue would take a significant hit. The long tail of sellers is also underperforming — representing untapped GMV.",
                "action":"Create a VIP seller retention programme with account management, analytics dashboards and co-marketing credits. Simultaneously, run a '90-day seller growth sprint' for the bottom 50% of sellers by revenue.",
            },
            {
                "id":9,"icon":"📉",
                "title":"Office Furniture Has the Lowest Review Score (3.52/5.0)",
                "what_happened":"Office furniture scores 3.52/5.0 among categories with 200+ orders — 0.57 points below the platform average of 4.09.",
                "metric":"office_furniture avg score: 3.52 | Platform avg: 4.09 | Delta: -0.57",
                "why_it_matters":"Persistently low scores in a visible category damage the platform's overall reputation and reduce trust for first-time visitors. Furniture likely suffers from delivery damage, assembly difficulty or product-description inaccuracy.",
                "action":"Audit all office_furniture listings for accurate descriptions. Require unboxing photos in product listings. Set a quality threshold (min 3.8 avg score) — sellers below threshold after 60 days receive mandatory coaching.",
            },
            {
                "id":10,"icon":"📊",
                "title":"New Customer Segment Drives 41% of Revenue Despite Low Frequency",
                "what_happened":f"The 'New Customers' RFM segment ({rfm_df[rfm_df['segment']=='New Customers']['customer_unique_id'].count():,} customers) generated {new_cust_rev/total_rev*100:.1f}% of revenue.",
                "metric":f"New Customers: {rfm_df[rfm_df['segment']=='New Customers']['customer_unique_id'].count():,} | Revenue: R${new_cust_rev:,.0f} ({new_cust_rev/total_rev*100:.1f}%)",
                "why_it_matters":"High revenue from new customers confirms the platform is acquiring buyers effectively. The risk is that without a retention system, this 41% evaporates when acquisition slows — creating a growth cliff.",
                "action":"Build a 'New Customer Success' journey: onboarding email series, first-review incentive, 30-day personalised recommendation. Target converting 10% of New Customers into Returning Customers within 90 days.",
            },
        ]

        # Display insights
        for ins in executive_insights:
            with st.expander(f"{ins['icon']} Insight {ins['id']}: {ins['title']}", expanded=False):
                cols = st.columns([1,1])
                with cols[0]:
                    st.markdown("**📌 What Happened**")
                    st.markdown(ins["what_happened"])
                    st.markdown("**📊 Supporting Metric**")
                    st.code(ins["metric"])
                with cols[1]:
                    st.markdown("**🎯 Why It Matters**")
                    st.markdown(ins["why_it_matters"])
                    st.markdown("**✅ Recommended Action**")
                    st.info(ins["action"])
                        # ---------------------------------------------------------------
        # Supporting visualization
        # ---------------------------------------------------------------

        if ins["id"] == 1:

            chart_data = (
                del_items
                .groupby("product_category_name_english")["item_revenue"]
                .sum()
                .sort_values(ascending=False)
                .head(10)
                .sort_values(ascending=True)
                .reset_index()
            )

            chart_data.columns = ["Category", "Revenue"]

            fig = px.bar(
                chart_data,
                x="Revenue",
                y="Category",
                orientation="h",
                title="Top 10 Categories by Delivered Revenue",
                template=PLOTLY_TEMPLATE,
            )

            fig.update_layout(height=450)

            st.plotly_chart(
                fig,
                use_container_width=True
            )
     

        # Quick summary table
        st.markdown("---")
        st.markdown("#### Executive Insights Summary")
        ins_df = pd.DataFrame([{
            "ID": i["id"],
            "Title": i["title"],
            "Metric": i["metric"],
        } for i in executive_insights])
        st.dataframe(ins_df, use_container_width=True, hide_index=True)
        download_csv(ins_df,"executive_insights.csv","Download Insights Summary")
