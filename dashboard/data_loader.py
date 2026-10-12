from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CACHE = ROOT / "dashboard" / ".cache"
CACHE.mkdir(parents=True, exist_ok=True)


def _parquet_or_csv(name: str, parse_dates: list[str] | None = None) -> pd.DataFrame:
    parquet = CACHE / f"{name}.parquet"
    csv = DATA / f"{name}.csv"
    if parquet.exists() and parquet.stat().st_mtime >= csv.stat().st_mtime:
        df = pd.read_parquet(parquet)
    else:
        df = pd.read_csv(csv)
        if parse_dates:
            for col in parse_dates:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
        df.to_parquet(parquet, index=False)
    return df


@st.cache_data(show_spinner="Loading sales ledger…")
def load_sales() -> pd.DataFrame:
    df = _parquet_or_csv("Sales_Transactions", parse_dates=["Order_Date", "Return_Date"])
    if not pd.api.types.is_datetime64_any_dtype(df["Order_Date"]):
        df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
    df["Month"] = df["Order_Date"].dt.to_period("M").dt.to_timestamp()
    df["Year"] = df["Order_Date"].dt.year
    df["Is_Returned"] = df["Returned"].astype(str).str.lower().eq("yes")
    df["Quality_Return"] = df["Quality_Related_Return"].astype(str).str.lower().eq("yes")
    return df


@st.cache_data(show_spinner=False)
def load_customers() -> pd.DataFrame:
    df = _parquet_or_csv("Customers", parse_dates=["Join_Date"])
    if not pd.api.types.is_datetime64_any_dtype(df["Join_Date"]):
        df["Join_Date"] = pd.to_datetime(df["Join_Date"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_group_ops() -> pd.DataFrame:
    df = _parquet_or_csv("Group_Operations", parse_dates=["Month"])
    if not pd.api.types.is_datetime64_any_dtype(df["Month"]):
        df["Month"] = pd.to_datetime(df["Month"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_marketing() -> pd.DataFrame:
    df = _parquet_or_csv("Marketing", parse_dates=["Start_Date", "End_Date"])
    for col in ("Start_Date", "End_Date"):
        if not pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = pd.to_datetime(df[col], errors="coerce")
    df["ROAS"] = df["Attributed_Revenue_EGP"] / df["Spend_EGP"].replace(0, pd.NA)
    return df


@st.cache_data(show_spinner=False)
def load_inventory() -> pd.DataFrame:
    df = _parquet_or_csv("Inventory_History", parse_dates=["Snapshot_Month"])
    if not pd.api.types.is_datetime64_any_dtype(df["Snapshot_Month"]):
        df["Snapshot_Month"] = pd.to_datetime(df["Snapshot_Month"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_quality() -> pd.DataFrame:
    df = _parquet_or_csv("Quality", parse_dates=["Inspection_Date"])
    if not pd.api.types.is_datetime64_any_dtype(df["Inspection_Date"]):
        df["Inspection_Date"] = pd.to_datetime(df["Inspection_Date"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_production() -> pd.DataFrame:
    df = _parquet_or_csv(
        "Production_Orders",
        parse_dates=["Start_Date", "Due_Date", "Completion_Date"],
    )
    for col in ("Start_Date", "Due_Date", "Completion_Date"):
        if not pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_service() -> pd.DataFrame:
    df = _parquet_or_csv("Customer_Service", parse_dates=["Open_Date"])
    if not pd.api.types.is_datetime64_any_dtype(df["Open_Date"]):
        df["Open_Date"] = pd.to_datetime(df["Open_Date"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_web() -> pd.DataFrame:
    df = _parquet_or_csv("Web_Traffic_Daily", parse_dates=["Date"])
    if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def load_products() -> pd.DataFrame:
    return _parquet_or_csv("Product_Master")
