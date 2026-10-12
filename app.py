from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard.data_loader import (
    load_customers,
    load_group_ops,
    load_inventory,
    load_marketing,
    load_production,
    load_quality,
    load_sales,
    load_service,
    load_web,
)

NAVY = "#0B1F3A"
GOLD = "#C9A227"
TEAL = "#1A7A6D"
CORAL = "#C45C26"
SLATE = "#4A6FA5"
PALETTE = [NAVY, GOLD, TEAL, CORAL, SLATE, "#8B5A2B", "#5C6B73", "#2E86AB"]

st.set_page_config(
    page_title="El-Sharnouby | CEO Dashboard",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');
      html, body, [class*="css"]  { font-family: 'IBM Plex Sans', sans-serif; }
      .stApp { background: #00001C; }
      [data-testid="stSidebar"] { background: #0B1F3A; }
      [data-testid="stSidebar"] * { color: #F4F1EA !important; }
      [data-testid="stSidebar"] .stSelectbox label,
      [data-testid="stSidebar"] .stMultiSelect label,
      [data-testid="stSidebar"] .stDateInput label,
      [data-testid="stSidebar"] .stRadio label { color: #E8D9A8 !important; }
      .hero {
        background: linear-gradient(120deg, #0B1F3A 0%, #16385C 55%, #1A7A6D 100%);
        color: #F4F1EA; padding: 1.15rem 1.4rem; border-radius: 14px; margin-bottom: 1rem;
      }
      .hero h1 { font-size: 1.55rem; margin: 0 0 .2rem 0; letter-spacing: .02em; }
      .hero p { margin: 0; opacity: .85; font-size: .92rem; }
      div[data-testid="stMetric"] {
        background: #fff; border: 1px solid #E4DCCB; border-radius: 12px;
        padding: .65rem .85rem; box-shadow: 0 1px 0 rgba(11,31,58,.04);
      }
      div[data-testid="stMetric"] label { color: #5C6B73 !important; font-size: .78rem !important; }
      [data-testid="stMetricValue"], [data-testid="stMetricValue"] * {
        color: #0B1F3A !important; font-size: 1.28rem !important; font-weight: 650 !important; opacity: 1 !important;
      }
      [data-testid="stMetricDelta"] { font-size: .78rem !important; }
      .insight {
        background: #fff; border-left: 4px solid #C9A227; padding: .7rem 1rem;
        border-radius: 8px; margin-bottom: .6rem; color: #0B1F3A;
      }
      .alert {
        background: #fff; border-left: 4px solid #C45C26; padding: .7rem 1rem;
        border-radius: 8px; margin-bottom: .6rem; color: #0B1F3A;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


def egp(n: float) -> str:
    if pd.isna(n):
        return "—"
    abs_n = abs(n)
    if abs_n >= 1_000_000:
        return f"{n / 1_000_000:,.2f}M EGP"
    if abs_n >= 1_000:
        return f"{n / 1_000:,.1f}K EGP"
    return f"{n:,.0f} EGP"


def pct(n: float) -> str:
    if pd.isna(n):
        return "—"
    return f"{n * 100:.1f}%"


def delta_label(curr: float, prev: float) -> str | None:
    if prev in (0, None) or pd.isna(prev) or pd.isna(curr):
        return None
    return f"{((curr - prev) / prev) * 100:+.1f}%"


def apply_chart(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Sans", color=NAVY, size=12),
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        colorway=PALETTE,
    )
    fig.update_xaxes(gridcolor="#CBCEE4", zeroline=False)
    fig.update_yaxes(gridcolor="#E4DCCB", zeroline=False)
    return fig


@st.cache_data
def kpis(df: pd.DataFrame) -> dict:
    if df.empty:
        return {k: 0 for k in (
            "net", "gross", "profit", "margin", "units", "invoices",
            "customers", "aov", "discount", "return_rate", "refund", "cogs",
        )}
    net = float(df["Net_Sales_EGP"].sum())
    invoices = int(df["Invoice_ID"].nunique())
    return {
        "net": net,
        "gross": float(df["Gross_Sales_EGP"].sum()),
        "profit": float(df["Gross_Profit_EGP"].sum()),
        "margin": float(df["Gross_Profit_EGP"].sum() / net) if net else 0.0,
        "units": int(df["Quantity"].sum()),
        "invoices": invoices,
        "customers": int(df["Customer_ID"].nunique()),
        "aov": net / invoices if invoices else 0.0,
        "discount": float(np.average(df["Discount_Pct"], weights=df["Gross_Sales_EGP"].clip(lower=0) + 1e-9)),
        "return_rate": float(df["Is_Returned"].mean()),
        "refund": float(df["Refund_Value_EGP"].sum()),
        "cogs": float(df["Estimated_COGS_EGP"].sum()),
    }


sales = load_sales()
customers = load_customers()
group_ops = load_group_ops()
marketing = load_marketing()
inventory = load_inventory()
quality = load_quality()
production = load_production()
service = load_service()
web = load_web()

min_d, max_d = sales["Order_Date"].min().date(), sales["Order_Date"].max().date()

with st.sidebar:
    st.markdown("### El-Sharnouby Group")
    st.caption("LEO MODA · TEX · PRINT · PRODUCTION")
    page = st.radio(
        "Workspace",
        [
            "CEO Home",
            "Sales Command Center",
            "Products & Mix",
            "Customers",
            "Channels & Markets",
            "Operations Pulse",
            "Data Explorer",
        ],
        index=1,
    )
    st.divider()
    st.markdown("**Filters**")
    date_range = st.date_input(
        "Order date",
        value=(min_d, max_d),
        min_value=min_d,
        max_value=max_d,
    )
    channels = st.multiselect("Channel", sorted(sales["Channel"].unique()), default=sorted(sales["Channel"].unique()))
    families = st.multiselect(
        "Product family",
        sorted(sales["Product_Family"].unique()),
        default=sorted(sales["Product_Family"].unique()),
    )
    locations = st.multiselect(
        "Location",
        sorted(sales["Location_Name"].unique()),
        default=sorted(sales["Location_Name"].unique()),
    )
    cust_types = st.multiselect(
        "Customer type",
        sorted(sales["Customer_Type"].unique()),
        default=sorted(sales["Customer_Type"].unique()),
    )
    hide_returns = st.checkbox("Exclude returned lines", value=False)

if isinstance(date_range, tuple) and len(date_range) == 2:
    start_d, end_d = date_range
else:
    start_d, end_d = min_d, max_d

start_ts = pd.Timestamp(start_d)
end_ts = pd.Timestamp(end_d) + pd.Timedelta(days=1)
mask = (
    sales["Order_Date"].ge(start_ts)
    & sales["Order_Date"].lt(end_ts)
    & sales["Channel"].isin(channels)
    & sales["Product_Family"].isin(families)
    & sales["Location_Name"].isin(locations)
    & sales["Customer_Type"].isin(cust_types)
)
if hide_returns:
    mask &= ~sales["Is_Returned"]
view = sales.loc[mask]

span_days = (pd.Timestamp(end_d) - pd.Timestamp(start_d)).days + 1
prev_end = pd.Timestamp(start_d) - timedelta(days=1)
prev_start = prev_end - timedelta(days=span_days - 1)
prev = sales.loc[
    sales["Order_Date"].between(prev_start, prev_end)
    & sales["Channel"].isin(channels)
    & sales["Product_Family"].isin(families)
    & sales["Location_Name"].isin(locations)
    & sales["Customer_Type"].isin(cust_types)
]
if hide_returns:
    prev = prev.loc[~prev["Is_Returned"]]

now = kpis(view)
was = kpis(prev)

st.markdown(
    f"""
    <div class="hero">
      <h1>CEO Dashboard — El-Sharnouby Group</h1>
      <p>Sales-led operating picture for LEO MODA · {start_d:%d %b %Y} → {end_d:%d %b %Y}
      · {len(view):,} invoice lines · modeled training data</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if view.empty:
    st.warning("No transactions match the current filters.")
    st.stop()


def metric_row():
    c1, c2, c3 = st.columns(3)
    c1.metric("Net sales", egp(now["net"]), delta=delta_label(now["net"], was["net"]), delta_color="normal")
    c2.metric("Gross profit", egp(now["profit"]), delta=delta_label(now["profit"], was["profit"]))
    c3.metric("Gross margin", pct(now["margin"]), delta=delta_label(now["margin"], was["margin"]))
    c4, c5, c6 = st.columns(3)
    c4.metric("Units", f"{now['units']:,}", delta=delta_label(now["units"], was["units"]))
    c5.metric("AOV", egp(now["aov"]), delta=delta_label(now["aov"], was["aov"]))
    c6.metric("Return rate", pct(now["return_rate"]), delta=delta_label(now["return_rate"], was["return_rate"]), delta_color="inverse")


# ---------------------------------------------------------------------------
# CEO Home
# ---------------------------------------------------------------------------
if page == "CEO Home":
    metric_row()
    st.caption("Deltas vs. the immediately preceding period of the same length.")

    left, right = st.columns((1.6, 1))
    monthly = (
        view.groupby("Month", as_index=False)
        .agg(Net_Sales=("Net_Sales_EGP", "sum"), Gross_Profit=("Gross_Profit_EGP", "sum"), Units=("Quantity", "sum"))
    )
    fig = go.Figure()
    fig.add_bar(x=monthly["Month"], y=monthly["Net_Sales"], name="Net sales", marker_color=NAVY)
    fig.add_scatter(
        x=monthly["Month"], y=monthly["Gross_Profit"], name="Gross profit",
        mode="lines+markers", line=dict(color=GOLD, width=3), yaxis="y2",
    )
    fig.update_layout(
        title="Revenue vs. profit",
        yaxis=dict(title="Net sales (EGP)"),
        yaxis2=dict(title="Gross profit (EGP)", overlaying="y", side="right"),
        barmode="overlay",
    )
    left.plotly_chart(apply_chart(fig, 380), width="stretch")

    ch = view.groupby("Channel", as_index=False).agg(
        Net=("Net_Sales_EGP", "sum"), Profit=("Gross_Profit_EGP", "sum")
    )
    ch["Margin"] = ch["Profit"] / ch["Net"]
    fig = px.bar(ch, x="Channel", y="Net", color="Channel", text_auto=".2s")
    fig.update_traces(textposition="outside")
    fig.update_layout(title="Net sales by channel", showlegend=False)
    right.plotly_chart(apply_chart(fig, 380), width="stretch")

    st.subheader("Group operations")
    ops = group_ops[
        group_ops["Month"].dt.date.between(start_d.replace(day=1), end_d)
    ]
    if ops.empty:
        ops = group_ops
    latest = ops.sort_values("Month").groupby("Business_Unit").tail(1)
    cols = st.columns(len(latest) if len(latest) else 1)
    for i, (_, row) in enumerate(latest.iterrows()):
        with cols[i]:
            st.metric(row["Business_Unit"], f"{row['Volume']:,.0f}", help=row["Primary_KPI"])
            st.caption(f"Efficiency {row['Operational_Efficiency_Pct']:.1f}% · open issues {int(row['Open_Issues_Count'])}")

    a1, a2 = st.columns(2)
    with a1:
        st.markdown("**Management signals**")
        fam = view.groupby("Product_Family").agg(net=("Net_Sales_EGP", "sum"), gp=("Gross_Profit_EGP", "sum"))
        fam["m"] = fam["gp"] / fam["net"]
        weakest = fam["m"].idxmin()
        st.markdown(
            f"<div class='insight'>Lowest-margin family: <b>{weakest}</b> at {pct(fam.loc[weakest, 'm'])}. "
            f"Protect mix toward higher-margin families before pushing volume discounts.</div>",
            unsafe_allow_html=True,
        )
        ch_m = view.groupby("Channel").agg(net=("Net_Sales_EGP", "sum"), gp=("Gross_Profit_EGP", "sum"))
        ch_m["m"] = ch_m["gp"] / ch_m["net"]
        wholesale_m = pct(ch_m.loc["Wholesale", "m"]) if "Wholesale" in ch_m.index else "—"
        retail_m = pct(ch_m.loc["Retail", "m"]) if "Retail" in ch_m.index else "—"
        st.markdown(
            f"<div class='insight'>Channel margin spread: Wholesale {wholesale_m} vs Retail {retail_m}. "
            f"Volume in wholesale only pays if factory utilization needs it.</div>",
            unsafe_allow_html=True,
        )
    with a2:
        st.markdown("**Watch-outs**")
        ret = view[view["Is_Returned"]].groupby("Product_Name")["Refund_Value_EGP"].sum().nlargest(1)
        if not ret.empty:
            st.markdown(
                f"<div class='alert'>Highest refund SKU: <b>{ret.index[0]}</b> ({egp(ret.iloc[0])}). "
                f"Cross-check size/fit vs quality-related returns.</div>",
                unsafe_allow_html=True,
            )
        stockouts = inventory[
            inventory["Snapshot_Month"].dt.date.between(start_d.replace(day=1), end_d)
        ]["Stockout_Days_In_Month"].sum()
        st.markdown(
            f"<div class='alert'>Stockout-days in window: <b>{int(stockouts):,}</b>. "
            f"Fast movers with cover below 20 days need replenishment priority.</div>",
            unsafe_allow_html=True,
        )

    mkt = marketing[marketing["Start_Date"].dt.date.between(start_d, end_d)]
    svc = service[service["Open_Date"].dt.date.between(start_d, end_d)]
    qc = quality[quality["Inspection_Date"].dt.date.between(start_d, end_d)]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Marketing spend", egp(mkt["Spend_EGP"].sum()) if not mkt.empty else "—")
    k2.metric("Blended ROAS", f"{(mkt['Attributed_Revenue_EGP'].sum() / mkt['Spend_EGP'].sum()):.2f}x" if not mkt.empty and mkt["Spend_EGP"].sum() else "—")
    k3.metric("CSAT", f"{svc['CSAT_1_to_5'].mean():.2f} / 5" if not svc.empty else "—")
    k4.metric("QC reject rate", pct(qc["Rejected_Qty"].sum() / qc["Inspected_Qty"].sum()) if not qc.empty and qc["Inspected_Qty"].sum() else "—")

# ---------------------------------------------------------------------------
# Sales Command Center
# ---------------------------------------------------------------------------
elif page == "Sales Command Center":
    metric_row()
    t1, t2, t3, t4 = st.columns(4)
    t1.metric("Gross sales", egp(now["gross"]))
    t2.metric("COGS", egp(now["cogs"]))
    t3.metric("Avg discount", pct(now["discount"]))
    t4.metric("Refunds", egp(now["refund"]))

    monthly = view.groupby("Month").agg(
        Net_Sales=("Net_Sales_EGP", "sum"),
        Gross_Profit=("Gross_Profit_EGP", "sum"),
        Units=("Quantity", "sum"),
        Discount=("Discount_Pct", "mean"),
        Returns=("Is_Returned", "mean"),
    ).reset_index()
    monthly["Margin"] = monthly["Gross_Profit"] / monthly["Net_Sales"]

    fig = go.Figure()
    fig.add_scatter(x=monthly["Month"], y=monthly["Net_Sales"], name="Net sales", fill="tozeroy", line=dict(color=NAVY, width=2))
    fig.add_scatter(x=monthly["Month"], y=monthly["Gross_Profit"], name="Gross profit", line=dict(color=GOLD, width=3))
    fig.update_layout(title="Monthly sales & profit")
    st.plotly_chart(apply_chart(fig, 390), width="stretch")

    c1, c2 = st.columns(2)
    fig = px.line(monthly, x="Month", y="Margin", markers=True, title="Gross margin trajectory")
    fig.update_yaxes(tickformat=".0%")
    c1.plotly_chart(apply_chart(fig), width="stretch")

    fig = go.Figure()
    fig.add_bar(x=monthly["Month"], y=monthly["Discount"], name="Avg discount", marker_color=CORAL)
    fig.add_scatter(x=monthly["Month"], y=monthly["Returns"], name="Return rate", yaxis="y2", line=dict(color=TEAL, width=3))
    fig.update_layout(title="Discount pressure vs returns", yaxis=dict(tickformat=".0%", title="Discount"), yaxis2=dict(tickformat=".0%", overlaying="y", side="right", title="Returns"))
    c2.plotly_chart(apply_chart(fig), width="stretch")

    heat = view.groupby([view["Order_Date"].dt.month.rename("MonthNum"), "Channel"])["Net_Sales_EGP"].sum().reset_index()
    heat["Month"] = pd.to_datetime(heat["MonthNum"], format="%m").dt.strftime("%b")
    pivot = heat.pivot_table(index="Channel", columns="MonthNum", values="Net_Sales_EGP", aggfunc="sum")
    fig = px.imshow(
        pivot,
        color_continuous_scale=["#F4F1EA", GOLD, NAVY],
        aspect="auto",
        title="Seasonality — net sales by channel and calendar month",
        labels=dict(x="Month", y="Channel", color="EGP"),
    )
    fig.update_xaxes(tickmode="array", tickvals=list(range(1, 13)), ticktext=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])
    st.plotly_chart(apply_chart(fig, 280), width="stretch")

    st.subheader("Discount impact")
    buckets = pd.cut(view["Discount_Pct"], bins=[-0.01, 0, 0.05, 0.10, 0.20, 0.30, 1], labels=["0%", "≤5%", "6–10%", "11–20%", "21–30%", ">30%"])
    disc = view.assign(Bucket=buckets).groupby("Bucket", observed=True).agg(
        Net=("Net_Sales_EGP", "sum"), Profit=("Gross_Profit_EGP", "sum"), Lines=("Row_ID", "count")
    ).reset_index()
    disc["Margin"] = disc["Profit"] / disc["Net"]
    fig = px.bar(disc, x="Bucket", y="Net", color="Margin", color_continuous_scale=["#C45C26", GOLD, TEAL], title="Sales by discount band (color = margin)")
    st.plotly_chart(apply_chart(fig, 340), width="stretch")

    pay = view.groupby("Payment_Method", as_index=False).agg(Net=("Net_Sales_EGP", "sum"), Invoices=("Invoice_ID", "nunique"))
    fig = px.pie(pay, names="Payment_Method", values="Net", hole=0.45, title="Net sales by payment method")
    st.plotly_chart(apply_chart(fig, 340), width="stretch")

# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------
elif page == "Products & Mix":
    metric_row()
    fam = view.groupby("Product_Family", as_index=False).agg(
        Net=("Net_Sales_EGP", "sum"),
        Profit=("Gross_Profit_EGP", "sum"),
        Units=("Quantity", "sum"),
        Returns=("Is_Returned", "mean"),
        Discount=("Discount_Pct", "mean"),
    )
    fam["Margin"] = fam["Profit"] / fam["Net"]
    fam = fam.sort_values("Net", ascending=False)
    fig = px.bar(fam, x="Product_Family", y="Net", color="Margin", color_continuous_scale=["#C45C26", GOLD, TEAL], title="Family contribution")
    st.plotly_chart(apply_chart(fig, 360), width="stretch")

    sku = view.groupby(["Product_ID", "SKU", "Product_Name", "Product_Family"], as_index=False).agg(
        Net=("Net_Sales_EGP", "sum"),
        Profit=("Gross_Profit_EGP", "sum"),
        Units=("Quantity", "sum"),
        Returns=("Is_Returned", "mean"),
        Quality_Returns=("Quality_Return", "mean"),
        Avg_Discount=("Discount_Pct", "mean"),
    )
    sku["Margin"] = sku["Profit"] / sku["Net"]
    sku = sku.sort_values("Net", ascending=False)
    sku["Share"] = sku["Net"] / sku["Net"].sum()
    sku["CumShare"] = sku["Share"].cumsum()

    c1, c2 = st.columns(2)
    top = sku.head(15)
    fig = px.bar(top, y="Product_Name", x="Net", orientation="h", color="Margin", color_continuous_scale=["#C45C26", GOLD, TEAL], title="Top 15 SKUs by net sales")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    c1.plotly_chart(apply_chart(fig, 520), width="stretch")

    fig = px.scatter(
        sku, x="Net", y="Margin", size="Units", color="Product_Family",
        hover_name="Product_Name", title="SKU map — volume vs margin",
    )
    fig.update_yaxes(tickformat=".0%")
    c2.plotly_chart(apply_chart(fig, 520), width="stretch")

    st.subheader("Pareto — which SKUs actually fund the P&L")
    fig = go.Figure()
    fig.add_bar(x=sku["SKU"].head(25), y=sku["Net"].head(25), name="Net sales", marker_color=NAVY)
    fig.add_scatter(x=sku["SKU"].head(25), y=sku["CumShare"].head(25), name="Cumulative share", yaxis="y2", line=dict(color=GOLD, width=3))
    fig.update_layout(title="Top 25 SKU Pareto", yaxis2=dict(overlaying="y", side="right", tickformat=".0%", range=[0, 1]))
    st.plotly_chart(apply_chart(fig, 360), width="stretch")

    st.dataframe(
        sku.head(40).style.format({
            "Net": "{:,.0f}", "Profit": "{:,.0f}", "Margin": "{:.1%}",
            "Returns": "{:.1%}", "Quality_Returns": "{:.1%}", "Avg_Discount": "{:.1%}",
            "Share": "{:.1%}", "CumShare": "{:.1%}",
        }),
        width="stretch",
        hide_index=True,
        height=420,
    )

    ret = view[view["Is_Returned"]]
    if not ret.empty:
        rr = ret.groupby("Return_Reason", as_index=False)["Refund_Value_EGP"].sum().sort_values("Refund_Value_EGP", ascending=False)
        fig = px.bar(rr, x="Return_Reason", y="Refund_Value_EGP", title="Refund value by return reason")
        st.plotly_chart(apply_chart(fig, 320), width="stretch")

# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------
elif page == "Customers":
    metric_row()
    merged = view.merge(
        customers[["Customer_ID", "Age_Band", "Gender", "Acquisition_Channel", "Join_Date"]],
        on="Customer_ID",
        how="left",
    )
    rfm = merged.groupby("Customer_ID").agg(
        last_order=("Order_Date", "max"),
        frequency=("Invoice_ID", "nunique"),
        monetary=("Net_Sales_EGP", "sum"),
        units=("Quantity", "sum"),
        Customer_Type=("Customer_Type", "first"),
        Governorate=("Customer_Governorate", "first"),
    )
    snapshot = pd.Timestamp(end_d)
    rfm["recency"] = (snapshot - rfm["last_order"]).dt.days
    def scored(series: pd.Series, reverse: bool = False) -> pd.Series:
        ranks = series.rank(method="first", pct=True)
        bins = pd.cut(ranks, bins=[0, 0.25, 0.5, 0.75, 1.01], labels=[1, 2, 3, 4], include_lowest=True)
        values = bins.astype(int)
        return (5 - values) if reverse else values

    rfm["R"] = scored(rfm["recency"], reverse=True)
    rfm["F"] = scored(rfm["frequency"])
    rfm["M"] = scored(rfm["monetary"])
    rfm["RFM"] = rfm["R"].astype(int) + rfm["F"].astype(int) + rfm["M"].astype(int)

    def segment(score: int) -> str:
        if score >= 10:
            return "Champions"
        if score >= 8:
            return "Loyal"
        if score >= 6:
            return "Promising"
        if score >= 4:
            return "At risk"
        return "Hibernating"

    rfm["Segment"] = rfm["RFM"].map(segment)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Active customers", f"{now['customers']:,}")
    k2.metric("Repeat rate", pct((rfm["frequency"] > 1).mean()))
    k3.metric("Avg orders / customer", f"{rfm['frequency'].mean():.2f}")
    k4.metric("Top 10% sales share", pct(rfm["monetary"].nlargest(max(1, int(len(rfm) * 0.1))).sum() / rfm["monetary"].sum()))

    seg = rfm.groupby("Segment", as_index=False).agg(Customers=("monetary", "count"), Sales=("monetary", "sum"))
    order = ["Champions", "Loyal", "Promising", "At risk", "Hibernating"]
    seg["Segment"] = pd.Categorical(seg["Segment"], categories=order, ordered=True)
    seg = seg.sort_values("Segment")
    fig = px.bar(seg, x="Segment", y="Sales", color="Customers", color_continuous_scale=["#E4DCCB", GOLD, NAVY], title="RFM segments")
    st.plotly_chart(apply_chart(fig, 360), width="stretch")

    c1, c2 = st.columns(2)
    acq = merged.groupby("Acquisition_Channel", as_index=False)["Net_Sales_EGP"].sum().sort_values("Net_Sales_EGP", ascending=False)
    fig = px.bar(acq, x="Acquisition_Channel", y="Net_Sales_EGP", title="Sales by acquisition channel")
    c1.plotly_chart(apply_chart(fig), width="stretch")
    age = merged.groupby("Age_Band", as_index=False)["Net_Sales_EGP"].sum()
    fig = px.bar(age, x="Age_Band", y="Net_Sales_EGP", title="Sales by age band")
    c2.plotly_chart(apply_chart(fig), width="stretch")

    st.subheader("Highest-value customers")
    show = rfm.sort_values("monetary", ascending=False).head(30).reset_index()
    st.dataframe(
        show[["Customer_ID", "Customer_Type", "Governorate", "recency", "frequency", "monetary", "Segment"]].rename(
            columns={"recency": "Recency_days", "frequency": "Orders", "monetary": "Net_EGP"}
        ).style.format({"Net_EGP": "{:,.0f}"}),
        width="stretch",
        hide_index=True,
        height=380,
    )

# ---------------------------------------------------------------------------
# Channels
# ---------------------------------------------------------------------------
elif page == "Channels & Markets":
    metric_row()
    ch = view.groupby(["Channel", "Location_Name"], as_index=False).agg(
        Net=("Net_Sales_EGP", "sum"),
        Profit=("Gross_Profit_EGP", "sum"),
        Units=("Quantity", "sum"),
        Invoices=("Invoice_ID", "nunique"),
        Customers=("Customer_ID", "nunique"),
        Returns=("Is_Returned", "mean"),
        Discount=("Discount_Pct", "mean"),
    )
    ch["Margin"] = ch["Profit"] / ch["Net"]
    ch["AOV"] = ch["Net"] / ch["Invoices"]
    st.dataframe(
        ch.style.format({
            "Net": "{:,.0f}", "Profit": "{:,.0f}", "Margin": "{:.1%}",
            "AOV": "{:,.0f}", "Returns": "{:.1%}", "Discount": "{:.1%}",
        }),
        width="stretch",
        hide_index=True,
    )

    monthly_ch = view.groupby(["Month", "Channel"], as_index=False)["Net_Sales_EGP"].sum()
    fig = px.area(monthly_ch, x="Month", y="Net_Sales_EGP", color="Channel", title="Channel mix over time")
    st.plotly_chart(apply_chart(fig, 380), width="stretch")

    geo = view.groupby("Customer_Governorate", as_index=False).agg(
        Net=("Net_Sales_EGP", "sum"), Profit=("Gross_Profit_EGP", "sum"),
        Customers=("Customer_ID", "nunique"), Units=("Quantity", "sum"),
    )
    geo["Margin"] = geo["Profit"] / geo["Net"]
    geo = geo.sort_values("Net", ascending=False)
    fig = px.bar(geo, x="Customer_Governorate", y="Net", color="Margin", color_continuous_scale=["#C45C26", GOLD, TEAL], title="Demand by governorate")
    st.plotly_chart(apply_chart(fig, 380), width="stretch")

    web_w = web[web["Date"].dt.date.between(start_d, end_d)]
    if not web_w.empty:
        st.subheader("Digital funnel (online)")
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Sessions", f"{int(web_w['Sessions'].sum()):,}")
        d2.metric("Conversion", pct(web_w["Orders"].sum() / web_w["Sessions"].sum()))
        d3.metric("Add-to-cart", pct(web_w["Add_To_Cart_Rate"].mean()))
        d4.metric("Avg load (s)", f"{web_w['Avg_Page_Load_Sec'].mean():.2f}")
        fig = px.line(web_w, x="Date", y="Conversion_Rate", title="Daily conversion rate")
        fig.update_yaxes(tickformat=".1%")
        st.plotly_chart(apply_chart(fig, 300), width="stretch")

# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------
elif page == "Operations Pulse":
    st.caption("Factory, inventory, quality and marketing — framed for the CEO, not the shop floor.")
    inv_w = inventory[inventory["Snapshot_Month"].dt.date.between(start_d.replace(day=1), end_d)]
    qc_w = quality[quality["Inspection_Date"].dt.date.between(start_d, end_d)]
    po_w = production[production["Start_Date"].dt.date.between(start_d, end_d)]
    mkt_w = marketing[marketing["Start_Date"].dt.date.between(start_d, end_d)]
    svc_w = service[service["Open_Date"].dt.date.between(start_d, end_d)]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Closing stock (latest snap)", f"{int(inv_w.sort_values('Snapshot_Month').groupby(['Location_ID','Product_ID']).tail(1)['Closing_Stock'].sum()):,}" if not inv_w.empty else "—")
    c2.metric("Stockout days", f"{int(inv_w['Stockout_Days_In_Month'].sum()):,}" if not inv_w.empty else "—")
    c3.metric("Factory efficiency", f"{po_w['Efficiency_Pct'].mean():.1f}%" if not po_w.empty else "—")
    c4.metric("Avg delay (days)", f"{po_w['Delay_Days'].mean():.1f}" if not po_w.empty else "—")
    c5.metric("Quality loss", egp(qc_w["Estimated_Loss_EGP"].sum()) if not qc_w.empty else "—")

    latest_month = inv_w["Snapshot_Month"].max() if not inv_w.empty else None
    if latest_month is not None:
        snap = inv_w[inv_w["Snapshot_Month"] == latest_month]
        c1, c2 = st.columns(2)
        fig = px.histogram(snap, x="Days_of_Cover", nbins=30, title=f"Days of cover — {latest_month:%b %Y}")
        c1.plotly_chart(apply_chart(fig), width="stretch")
        risk = snap[snap["Days_of_Cover"] < 20].sort_values("Days_of_Cover").head(20)
        c2.markdown("**Low-cover SKUs (< 20 days)**")
        c2.dataframe(
            risk[["Location_Name", "SKU", "Product_Name", "Closing_Stock", "Days_of_Cover", "Stockout_Days_In_Month"]],
            width="stretch",
            hide_index=True,
            height=340,
        )

    if not qc_w.empty:
        pareto = qc_w.groupby("Defect_Type", as_index=False)["Estimated_Loss_EGP"].sum().sort_values("Estimated_Loss_EGP", ascending=False)
        fig = px.bar(pareto, x="Defect_Type", y="Estimated_Loss_EGP", title="Cost of poor quality — defect Pareto")
        st.plotly_chart(apply_chart(fig, 340), width="stretch")

    if not po_w.empty:
        bn = po_w.groupby("Primary_Bottleneck", as_index=False).agg(Orders=("Production_Order_ID", "count"), Avg_Delay=("Delay_Days", "mean"))
        fig = px.bar(bn, x="Primary_Bottleneck", y="Orders", color="Avg_Delay", title="Production bottlenecks")
        st.plotly_chart(apply_chart(fig, 320), width="stretch")

    if not mkt_w.empty:
        st.subheader("Marketing efficiency")
        plat = mkt_w.groupby("Platform", as_index=False).agg(Spend=("Spend_EGP", "sum"), Revenue=("Attributed_Revenue_EGP", "sum"), Orders=("Orders_Attributed", "sum"))
        plat["ROAS"] = plat["Revenue"] / plat["Spend"]
        fig = px.bar(plat, x="Platform", y="ROAS", color="Spend", title="ROAS by platform")
        st.plotly_chart(apply_chart(fig, 340), width="stretch")
        st.dataframe(
            plat.style.format({"Spend": "{:,.0f}", "Revenue": "{:,.0f}", "ROAS": "{:.2f}"}),
            width="stretch",
            hide_index=True,
        )

    if not svc_w.empty:
        st.subheader("Customer service")
        s1, s2, s3 = st.columns(3)
        s1.metric("Tickets", f"{len(svc_w):,}")
        s2.metric("Resolved", pct(svc_w["Resolved"].astype(str).str.lower().eq("yes").mean()))
        s3.metric("CSAT", f"{svc_w['CSAT_1_to_5'].mean():.2f}")
        fig = px.bar(svc_w.groupby("Issue_Type", as_index=False).size().rename(columns={"size": "Tickets"}), x="Issue_Type", y="Tickets", title="Ticket mix")
        st.plotly_chart(apply_chart(fig, 300), width="stretch")

# ---------------------------------------------------------------------------
# Data explorer
# ---------------------------------------------------------------------------
else:
    st.subheader("Filtered sales ledger")
    st.caption("Inspect and export the exact slice the rest of the dashboard is using.")
    cols = [
        "Order_Date", "Invoice_ID", "Channel", "Location_Name", "Customer_ID",
        "Customer_Type", "Customer_Governorate", "SKU", "Product_Name",
        "Product_Family", "Size", "Quantity", "Discount_Pct", "Gross_Sales_EGP",
        "Net_Sales_EGP", "Gross_Profit_EGP", "Gross_Margin_Pct", "Payment_Method",
        "Returned", "Return_Reason", "Refund_Value_EGP",
    ]
    q = st.text_input("Search SKU, product, invoice or customer ID")
    table = view[cols]
    if q:
        needle = q.lower()
        table = table[
            table["SKU"].str.lower().str.contains(needle, na=False)
            | table["Product_Name"].str.lower().str.contains(needle, na=False)
            | table["Invoice_ID"].str.lower().str.contains(needle, na=False)
            | table["Customer_ID"].str.lower().str.contains(needle, na=False)
        ]
    st.write(f"{len(table):,} rows")
    st.dataframe(table.head(500), width="stretch", hide_index=True, height=480)
    csv = table.to_csv(index=False).encode("utf-8-sig")
    st.download_button("Download filtered CSV", data=csv, file_name="elsharnouby_sales_filtered.csv", mime="text/csv")
