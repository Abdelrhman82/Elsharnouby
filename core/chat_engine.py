"""
Chat Engine for El-Sharnouby Group CEO Dashboard
Integrates with Google Gemini LLM using REST API with strict enterprise guardrails.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import requests

DEFAULT_API_KEY = ""
CANDIDATE_MODELS = ["gemini-3.5-flash-lite"]

SYSTEM_PROMPT = """You are the Chief AI Business Analyst & Executive Strategy Advisor for El-Sharnouby(الشرنوبي) Group (encompassing LEO MODA apparel, LEO TEX woven textiles, LEO PRINT garment printing, LEO PRODUCTION HUB garment manufacturing, and LEO DESIGN).

============================================================
CRITICAL GUARDRAIL & TOPIC POLICY (ZERO TOLERANCE):
============================================================
1. YOU ARE STRICTLY FORBIDDEN FROM ANSWERING PUBLIC, GENERAL KNOWLEDGE, TRIVIA, OR UNRELATED QUESTIONS.
   You must NEVER answer questions about world history, politics, general science, celebrities, movies, sports, weather, cooking, personal advice, poetry, or general programming help unrelated to this company.
2. IF A USER ASKS ANY PUBLIC, GENERAL, OR UNRELATED QUESTION:
   You MUST politely and firmly REFUSE to answer.
   Example refusal format:
   "I am El-Sharnouby Group's dedicated Enterprise Data & Business Intelligence Assistant. I am strictly restricted to analyzing company datasets and operations (Sales, Channels, Inventory, Quality, Production, Marketing, Customers, and Group P&L). I cannot answer general or public knowledge questions.
   Please feel free to ask about our business performance, such as:
   • Which sales channels generate the highest gross profit margin?
   • What are our primary production bottlenecks and delay drivers?
   • Which SKUs have critical inventory cover below 20 days?
   • How is our marketing budget performing across Meta vs Google?"
3. WORK EXCLUSIVELY ON COMPANY DATA & PROVIDE ACTIONABLE BUSINESS INSIGHTS:
   When answering valid enterprise inquiries:
   - Ground every number, percentage, and metric strictly in the provided company data.
   - Format financials in EGP (Egyptian Pounds), percentages with 1 decimal place, and units clearly.
   - Respond in the language used by the user (support both English and Arabic fluently).
   - Provide executive-level business depth:
     a) **Executive Summary**: Direct answer with hard numbers and KPI deltas.
     b) **Deep-Dive Analysis**: Root causes, channel/mix dynamics, risk signals, and trade-offs (e.g. volume vs margin, scrap cost vs quality).
     c) **Strategic Business Recommendations**: 2-3 prioritized, actionable C-suite recommendations for the CEO and board to optimize revenue, cut costs, or eliminate operational friction.
4. Always answer in Arabic even if the user asks in English.
"""


def _egp(val: float) -> str:
    if pd.isna(val) or val is None:
        return "—"
    abs_v = abs(val)
    if abs_v >= 1_000_000:
        return f"{val / 1_000_000:,.2f}M EGP"
    if abs_v >= 1_000:
        return f"{val / 1_000:,.1f}K EGP"
    return f"{val:,.0f} EGP"


def _pct(val: float) -> str:
    if pd.isna(val) or val is None:
        return "—"
    return f"{val * 100:.1f}%"


def build_enterprise_context(
    view: pd.DataFrame,
    sales: pd.DataFrame,
    customers: pd.DataFrame,
    group_ops: pd.DataFrame,
    marketing: pd.DataFrame,
    inventory: pd.DataFrame,
    quality: pd.DataFrame,
    production: pd.DataFrame,
    service: pd.DataFrame,
    web: pd.DataFrame,
    filters_info: Optional[Dict[str, Any]] = None,
) -> str:
    """Build an extensive, structured textual summary of the company's multi-domain data."""
    parts: List[str] = []

    # 1. Company Profile & Scope
    parts.append("=== EL-SHARNOUBY GROUP STRUCTURE ===")
    parts.append("- LEO MODA: Apparel brand across Retail stores, Online D2C, and B2B Wholesale.")
    parts.append("- LEO TEX: Textile and woven fabric manufacturing.")
    parts.append("- LEO PRODUCTION HUB: Garment manufacturing facility (up to 5,000 pcs/day).")
    parts.append("- LEO PRINT: Garment & fabric printing facility (up to 20,000 garments/day).")
    parts.append("- LEO DESIGN: Fashion design, patterns, and prototyping.\n")

    parts.append("=== CURRENT DASHBOARD FILTER SCOPE ===")
    if filters_info:
        for k, v in filters_info.items():
            parts.append(f"- {k}: {v}")
    parts.append(f"- Filtered Transactions Count: {len(view):,} invoice lines")
    parts.append(f"- Total Historical Ledger Count: {len(sales):,} invoice lines\n")

    # 2. Sales & Profitability (Active View)
    net_sales = float(view["Net_Sales_EGP"].sum())
    gross_sales = float(view["Gross_Sales_EGP"].sum())
    gross_profit = float(view["Gross_Profit_EGP"].sum())
    margin = (gross_profit / net_sales) if net_sales else 0.0
    units = int(view["Quantity"].sum())
    invoices = int(view["Invoice_ID"].nunique())
    unique_cust = int(view["Customer_ID"].nunique())
    aov = (net_sales / invoices) if invoices else 0.0
    ret_rate = float(view["Is_Returned"].mean())
    refund_val = float(view["Refund_Value_EGP"].sum())
    cogs_val = float(view["Estimated_COGS_EGP"].sum())
    avg_discount = float(view["Discount_Pct"].mean())

    parts.append("=== SALES & PROFITABILITY (CURRENT FILTERED VIEW) ===")
    parts.append(f"- Net Sales: {_egp(net_sales)} (Gross: {_egp(gross_sales)})")
    parts.append(f"- Gross Profit: {_egp(gross_profit)} (Blended Margin: {_pct(margin)})")
    parts.append(f"- Estimated COGS: {_egp(cogs_val)}")
    parts.append(f"- Units Sold: {units:,} across {invoices:,} invoices")
    parts.append(f"- Active Customers in Period: {unique_cust:,} (AOV: {_egp(aov)})")
    parts.append(f"- Average Discount: {_pct(avg_discount)}")
    parts.append(f"- Return Rate: {_pct(ret_rate)} (Total Refund Value: {_egp(refund_val)})\n")

    # Historical Yearly Overview (Full Dataset)
    if "Year" in sales.columns:
        parts.append("=== HISTORICAL YEARLY TOTALS (FULL DATASET) ===")
        yearly = sales.groupby("Year").agg(
            Net=("Net_Sales_EGP", "sum"),
            Profit=("Gross_Profit_EGP", "sum"),
            Units=("Quantity", "sum"),
            Invoices=("Invoice_ID", "nunique"),
        )
        yearly["Margin"] = yearly["Profit"] / yearly["Net"]
        for y, r in yearly.iterrows():
            parts.append(
                f"- Year {y}: Net Sales {_egp(r['Net'])}, Profit {_egp(r['Profit'])}, "
                f"Margin {_pct(r['Margin'])}, Units {int(r['Units']):,}, Invoices {int(r['Invoices']):,}"
            )
        parts.append("")

    # 3. Channel Breakdown
    parts.append("=== CHANNEL BREAKDOWN (CURRENT VIEW) ===")
    ch_grp = view.groupby("Channel", as_index=False).agg(
        Net=("Net_Sales_EGP", "sum"),
        Profit=("Gross_Profit_EGP", "sum"),
        Units=("Quantity", "sum"),
        Invoices=("Invoice_ID", "nunique"),
        Returns=("Is_Returned", "mean"),
        Discount=("Discount_Pct", "mean"),
    )
    ch_grp["Margin"] = ch_grp["Profit"] / ch_grp["Net"]
    for _, row in ch_grp.iterrows():
        parts.append(
            f"- {row['Channel']}: Net Sales {_egp(row['Net'])}, "
            f"Gross Profit {_egp(row['Profit'])}, Margin {_pct(row['Margin'])}, "
            f"Avg Discount {_pct(row['Discount'])}, Units {int(row['Units']):,}, "
            f"Invoices {int(row['Invoices']):,}, Return Rate {_pct(row['Returns'])}"
        )
    parts.append("")

    # 4. Product Family Performance
    parts.append("=== PRODUCT FAMILIES PERFORMANCE ===")
    fam_grp = view.groupby("Product_Family", as_index=False).agg(
        Net=("Net_Sales_EGP", "sum"),
        Profit=("Gross_Profit_EGP", "sum"),
        Units=("Quantity", "sum"),
        Returns=("Is_Returned", "mean"),
    ).sort_values("Net", ascending=False)
    fam_grp["Margin"] = fam_grp["Profit"] / fam_grp["Net"]
    for _, row in fam_grp.iterrows():
        parts.append(
            f"- {row['Product_Family']}: Net Sales {_egp(row['Net'])}, "
            f"Profit {_egp(row['Profit'])}, Margin {_pct(row['Margin'])}, "
            f"Units {int(row['Units']):,}, Return Rate {_pct(row['Returns'])}"
        )
    parts.append("")

    # 5. Top 10 Best-Selling SKUs & Top 5 Highest Return SKUs
    parts.append("=== TOP 10 SKUs BY NET SALES ===")
    sku_grp = view.groupby(["SKU", "Product_Name", "Product_Family"], as_index=False).agg(
        Net=("Net_Sales_EGP", "sum"),
        Profit=("Gross_Profit_EGP", "sum"),
        Units=("Quantity", "sum"),
        Returns=("Is_Returned", "mean"),
        Refunds=("Refund_Value_EGP", "sum"),
    ).sort_values("Net", ascending=False)
    sku_grp["Margin"] = sku_grp["Profit"] / sku_grp["Net"]
    for _, row in sku_grp.head(10).iterrows():
        parts.append(
            f"- {row['SKU']} ({row['Product_Name']} | {row['Product_Family']}): "
            f"Net {_egp(row['Net'])}, Units {int(row['Units']):,}, Margin {_pct(row['Margin'])}, Returns {_pct(row['Returns'])}"
        )
    parts.append("")

    parts.append("=== TOP 5 HIGHEST REFUND SKUs ===")
    top_refund_skus = sku_grp.sort_values("Refunds", ascending=False).head(5)
    for _, row in top_refund_skus.iterrows():
        parts.append(
            f"- {row['SKU']} ({row['Product_Name']}): Total Refund {_egp(row['Refunds'])}, Return Rate {_pct(row['Returns'])}"
        )
    parts.append("")

    # 6. Customer Demographics & RFM Segments
    if not customers.empty and not view.empty:
        merged = view.merge(
            customers[["Customer_ID", "Age_Band", "Gender", "Acquisition_Channel"]],
            on="Customer_ID",
            how="left",
        )
        parts.append("=== CUSTOMER ACQUISITION & RETENTION ===")
        acq_grp = merged.groupby("Acquisition_Channel", as_index=False)["Net_Sales_EGP"].sum().sort_values("Net_Sales_EGP", ascending=False)
        for _, row in acq_grp.iterrows():
            parts.append(f"- Acquisition via {row['Acquisition_Channel']}: {_egp(row['Net_Sales_EGP'])}")
        
        cust_orders = view.groupby("Customer_ID")["Invoice_ID"].nunique()
        repeat_pct = (cust_orders > 1).mean()
        parts.append(f"- Customer Repeat Purchase Rate: {_pct(repeat_pct)}")
        parts.append("")

    # 7. Geographic / Governorate Highlights
    parts.append("=== TOP 5 GOVERNORATES BY NET SALES ===")
    geo_grp = view.groupby("Customer_Governorate", as_index=False).agg(
        Net=("Net_Sales_EGP", "sum"),
        Profit=("Gross_Profit_EGP", "sum"),
    ).sort_values("Net", ascending=False)
    geo_grp["Margin"] = geo_grp["Profit"] / geo_grp["Net"]
    for _, row in geo_grp.head(5).iterrows():
        parts.append(f"- {row['Customer_Governorate']}: Net {_egp(row['Net'])}, Margin {_pct(row['Margin'])}")
    parts.append("")

    # 8. Marketing Performance
    if not marketing.empty:
        parts.append("=== MARKETING & ADVERTISING EFFICIENCY ===")
        mkt_spend = marketing["Spend_EGP"].sum()
        mkt_rev = marketing["Attributed_Revenue_EGP"].sum()
        blended_roas = (mkt_rev / mkt_spend) if mkt_spend else 0.0
        parts.append(f"- Total Marketing Spend: {_egp(mkt_spend)}")
        parts.append(f"- Attributed Revenue: {_egp(mkt_rev)} (Blended ROAS: {blended_roas:.2f}x)")
        plat_grp = marketing.groupby("Platform", as_index=False).agg(
            Spend=("Spend_EGP", "sum"),
            Rev=("Attributed_Revenue_EGP", "sum"),
            Orders=("Orders_Attributed", "sum"),
        )
        plat_grp["ROAS"] = plat_grp["Rev"] / plat_grp["Spend"]
        for _, row in plat_grp.sort_values("ROAS", ascending=False).iterrows():
            parts.append(
                f"- Platform {row['Platform']}: Spend {_egp(row['Spend'])}, "
                f"Revenue {_egp(row['Rev'])}, ROAS {row['ROAS']:.2f}x, Orders {int(row['Orders']):,}"
            )
        parts.append("")

    # 9. Inventory Health & Cover
    if not inventory.empty:
        parts.append("=== INVENTORY & SUPPLY CHAIN STATUS ===")
        total_stock = inventory.sort_values("Snapshot_Month").groupby(["Location_ID", "Product_ID"]).tail(1)["Closing_Stock"].sum()
        stockout_days = inventory["Stockout_Days_In_Month"].sum()
        parts.append(f"- Current Closing Stock: {int(total_stock):,} units")
        parts.append(f"- Cumulative Stockout Days: {int(stockout_days):,} days")
        
        latest_inv_snap = inventory["Snapshot_Month"].max()
        curr_snap = inventory[inventory["Snapshot_Month"] == latest_inv_snap]
        low_cover = curr_snap[curr_snap["Days_of_Cover"] < 20].sort_values("Days_of_Cover").head(5)
        if not low_cover.empty:
            parts.append("- Critical Low-Cover SKUs (<20 days):")
            for _, r in low_cover.iterrows():
                parts.append(f"  * {r['SKU']} ({r['Product_Name']} at {r['Location_Name']}): Cover {r['Days_of_Cover']:.1f} days, Stock {int(r['Closing_Stock'])} units")
        parts.append("")

    # 10. Quality & Defects
    if not quality.empty:
        parts.append("=== QUALITY CONTROL & SCRAP LOSSES ===")
        total_loss = quality["Estimated_Loss_EGP"].sum()
        total_inspected = quality["Inspected_Qty"].sum()
        total_rejected = quality["Rejected_Qty"].sum()
        reject_rate = (total_rejected / total_inspected) if total_inspected else 0.0
        parts.append(f"- Total Quality Financial Loss: {_egp(total_loss)}")
        parts.append(f"- Overall Reject Rate: {_pct(reject_rate)} ({int(total_rejected):,} rejected of {int(total_inspected):,} inspected)")
        defects = quality.groupby("Defect_Type", as_index=False)["Estimated_Loss_EGP"].sum().sort_values("Estimated_Loss_EGP", ascending=False)
        parts.append("- Defect Pareto Breakdown:")
        for _, r in defects.head(5).iterrows():
            parts.append(f"  * {r['Defect_Type']}: {_egp(r['Estimated_Loss_EGP'])}")
        parts.append("")

    # 11. Production Operations & Bottlenecks
    if not production.empty:
        parts.append("=== FACTORY PRODUCTION & BOTTLENECKS ===")
        eff = production["Efficiency_Pct"].mean()
        avg_delay = production["Delay_Days"].mean()
        parts.append(f"- Average Factory Operational Efficiency: {eff:.1f}%")
        parts.append(f"- Average Production Order Delay: {avg_delay:.1f} days")
        bn = production.groupby("Primary_Bottleneck", as_index=False).agg(
            Orders=("Production_Order_ID", "count"),
            Avg_Delay=("Delay_Days", "mean"),
        ).sort_values("Orders", ascending=False)
        parts.append("- Production Bottlenecks:")
        for _, r in bn.iterrows():
            parts.append(f"  * {r['Primary_Bottleneck']}: {int(r['Orders'])} orders impacted, avg delay {r['Avg_Delay']:.1f} days")
        parts.append("")

    # 12. Customer Service & CSAT
    if not service.empty:
        parts.append("=== CUSTOMER SERVICE TICKETS ===")
        total_tickets = len(service)
        res_rate = service["Resolved"].astype(str).str.lower().eq("yes").mean()
        csat = service["CSAT_1_to_5"].mean()
        parts.append(f"- Total Tickets: {total_tickets:,}")
        parts.append(f"- Resolution Rate: {_pct(res_rate)}")
        parts.append(f"- Average CSAT: {csat:.2f} / 5.00")
        top_issues = service.groupby("Issue_Type", as_index=False).size().sort_values("size", ascending=False)
        parts.append("- Ticket Mix by Issue:")
        for _, r in top_issues.head(4).iterrows():
            parts.append(f"  * {r['Issue_Type']}: {int(r['size']):,} tickets")
        parts.append("")

    # 13. Digital Web Performance
    if not web.empty:
        parts.append("=== DIGITAL / E-COMMERCE FUNNEL ===")
        tot_sessions = web["Sessions"].sum()
        tot_orders = web["Orders"].sum()
        conv = (tot_orders / tot_sessions) if tot_sessions else 0.0
        parts.append(f"- Total Web Sessions: {int(tot_sessions):,}")
        parts.append(f"- Total Online Orders: {int(tot_orders):,}")
        parts.append(f"- Online Conversion Rate: {_pct(conv)}")
        parts.append(f"- Avg Add-To-Cart Rate: {_pct(web['Add_To_Cart_Rate'].mean())}")
        parts.append(f"- Avg Page Load Time: {web['Avg_Page_Load_Sec'].mean():.2f}s\n")

    # 14. Group Operations by Business Unit
    if not group_ops.empty:
        parts.append("=== GROUP OPERATIONS (BUSINESS UNITS) ===")
        latest_bu = group_ops.sort_values("Month").groupby("Business_Unit").tail(1)
        for _, r in latest_bu.iterrows():
            parts.append(
                f"- Business Unit '{r['Business_Unit']}': Volume {r['Volume']:,.0f} ({r.get('Primary_KPI', 'KPI')}), "
                f"Efficiency {r.get('Operational_Efficiency_Pct', 0):.1f}%, Open Issues {int(r.get('Open_Issues_Count', 0))}"
            )
        parts.append("")

    return "\n".join(parts)


def ask_gemini(
    prompt: str,
    context: str,
    chat_history: Optional[List[Dict[str, str]]] = None
) -> str:
    """
    Sends user query and enterprise context to Gemini model via Google Generative Language REST API.
    Handles fallbacks and formats response.
    """
    key = DEFAULT_API_KEY

    # Build contents with chat history
    contents: List[Dict[str, Any]] = []

    if chat_history:
        for msg in chat_history:
            role = "user" if msg.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})

    # Append current user prompt wrapped with current enterprise context
    full_user_content = (
        f"COMPANY DATA REPOSITORY & CONTEXT:\n{context}\n\n"
        f"USER QUESTION:\n{prompt}"
    )
    contents.append({"role": "user", "parts": [{"text": full_user_content}]})

    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        },
        "generationConfig": {
            "temperature": 0.25,
            "maxOutputTokens": 2048,
        },
    }

    last_error = ""
    for model_name in CANDIDATE_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
        try:
            resp = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=35,
            )
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "No text generated.")
            elif resp.status_code == 503:
                last_error = f"{model_name} is experiencing high demand (503)."
                continue
            else:
                last_error = f"API returned status {resp.status_code}: {resp.text[:200]}"
        except Exception as e:
            last_error = f"Request exception on {model_name}: {str(e)}"
            continue

    return (
        f"⚠️ **Service Notice:** Unable to reach Gemini API at the moment. ({last_error})\n\n"
        "Please check your internet connection or try again in a few moments."
    )
