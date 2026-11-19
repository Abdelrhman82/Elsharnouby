from __future__ import annotations

import functools
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger("elsharnouby.data_loader")

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
# Check both potential cache directories
CACHE_DIRS = [
    ROOT / "core" / ".cache",
    ROOT / ".cache",
    ROOT / "dashboard" / ".cache",
]
PRIMARY_CACHE = ROOT / "core" / ".cache"
PRIMARY_CACHE.mkdir(parents=True, exist_ok=True)

# In-memory dictionary cache to prevent redundant disk I/O
_MEMORY_CACHE: Dict[str, pd.DataFrame] = {}


def _find_cache_file(name: str) -> Optional[Path]:
    for d in CACHE_DIRS:
        p = d / f"{name}.parquet"
        if p.exists():
            return p
    return None


def _parquet_or_csv(name: str, parse_dates: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Loads dataset from parquet cache if valid, otherwise falls back to CSV
    and caches to parquet for fast subsequent loads.
    """
    if name in _MEMORY_CACHE:
        return _MEMORY_CACHE[name]

    parquet = _find_cache_file(name)
    csv = DATA / f"{name}.csv"

    df: Optional[pd.DataFrame] = None
    if parquet is not None and parquet.exists():
        try:
            if not csv.exists() or parquet.stat().st_mtime >= csv.stat().st_mtime:
                df = pd.read_parquet(parquet)
        except Exception as e:
            logger.warning("Error reading parquet for %s: %s. Falling back to CSV.", name, e)

    if df is None:
        if not csv.exists():
            raise FileNotFoundError(f"Data file {name}.csv not found in {DATA}")
        df = pd.read_csv(csv)
        if parse_dates:
            for col in parse_dates:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce")
        # Save to primary cache
        try:
            target_parquet = PRIMARY_CACHE / f"{name}.parquet"
            df.to_parquet(target_parquet, index=False)
        except Exception as e:
            logger.warning("Could not write parquet cache for %s: %s", name, e)

    _MEMORY_CACHE[name] = df
    return df


def load_sales(force_reload: bool = False) -> pd.DataFrame:
    if force_reload and "Sales_Transactions" in _MEMORY_CACHE:
        del _MEMORY_CACHE["Sales_Transactions"]

    df = _parquet_or_csv("Sales_Transactions", parse_dates=["Order_Date", "Return_Date"])
    if not pd.api.types.is_datetime64_any_dtype(df["Order_Date"]):
        df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
    if "Return_Date" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["Return_Date"]):
        df["Return_Date"] = pd.to_datetime(df["Return_Date"], errors="coerce")

    if "Month" not in df.columns:
        df["Month"] = df["Order_Date"].dt.to_period("M").dt.to_timestamp()
    if "Year" not in df.columns:
        df["Year"] = df["Order_Date"].dt.year
    if "Is_Returned" not in df.columns:
        df["Is_Returned"] = df["Returned"].astype(str).str.lower().eq("yes")
    if "Quality_Return" not in df.columns:
        df["Quality_Return"] = df["Quality_Related_Return"].astype(str).str.lower().eq("yes")
    return df


def load_customers(force_reload: bool = False) -> pd.DataFrame:
    if force_reload and "Customers" in _MEMORY_CACHE:
        del _MEMORY_CACHE["Customers"]

    df = _parquet_or_csv("Customers", parse_dates=["Join_Date"])
    if not pd.api.types.is_datetime64_any_dtype(df["Join_Date"]):
        df["Join_Date"] = pd.to_datetime(df["Join_Date"], errors="coerce")
    return df


def load_group_ops(force_reload: bool = False) -> pd.DataFrame:
    if force_reload and "Group_Operations" in _MEMORY_CACHE:
        del _MEMORY_CACHE["Group_Operations"]

    df = _parquet_or_csv("Group_Operations", parse_dates=["Month"])
    if not pd.api.types.is_datetime64_any_dtype(df["Month"]):
        df["Month"] = pd.to_datetime(df["Month"], errors="coerce")
    return df


def load_marketing(force_reload: bool = False) -> pd.DataFrame:
    if force_reload and "Marketing" in _MEMORY_CACHE:
        del _MEMORY_CACHE["Marketing"]

    df = _parquet_or_csv("Marketing", parse_dates=["Start_Date", "End_Date"])
    for col in ("Start_Date", "End_Date"):
        if col in df.columns and not pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = pd.to_datetime(df[col], errors="coerce")
    if "ROAS" not in df.columns and "Spend_EGP" in df.columns and "Attributed_Revenue_EGP" in df.columns:
        df["ROAS"] = df["Attributed_Revenue_EGP"] / df["Spend_EGP"].replace(0, pd.NA)
    return df


def load_inventory(force_reload: bool = False) -> pd.DataFrame:
    if force_reload and "Inventory_History" in _MEMORY_CACHE:
        del _MEMORY_CACHE["Inventory_History"]

    df = _parquet_or_csv("Inventory_History", parse_dates=["Snapshot_Month"])
    if not pd.api.types.is_datetime64_any_dtype(df["Snapshot_Month"]):
        df["Snapshot_Month"] = pd.to_datetime(df["Snapshot_Month"], errors="coerce")
    return df


def load_quality(force_reload: bool = False) -> pd.DataFrame:
    if force_reload and "Quality" in _MEMORY_CACHE:
        del _MEMORY_CACHE["Quality"]

    df = _parquet_or_csv("Quality", parse_dates=["Inspection_Date"])
    if not pd.api.types.is_datetime64_any_dtype(df["Inspection_Date"]):
        df["Inspection_Date"] = pd.to_datetime(df["Inspection_Date"], errors="coerce")
    return df


def load_production(force_reload: bool = False) -> pd.DataFrame:
    if force_reload and "Production_Orders" in _MEMORY_CACHE:
        del _MEMORY_CACHE["Production_Orders"]

    df = _parquet_or_csv(
        "Production_Orders",
        parse_dates=["Start_Date", "Due_Date", "Completion_Date"],
    )
    for col in ("Start_Date", "Due_Date", "Completion_Date"):
        if col in df.columns and not pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def load_service(force_reload: bool = False) -> pd.DataFrame:
    if force_reload and "Customer_Service" in _MEMORY_CACHE:
        del _MEMORY_CACHE["Customer_Service"]

    df = _parquet_or_csv("Customer_Service", parse_dates=["Open_Date"])
    if not pd.api.types.is_datetime64_any_dtype(df["Open_Date"]):
        df["Open_Date"] = pd.to_datetime(df["Open_Date"], errors="coerce")
    return df


def load_web(force_reload: bool = False) -> pd.DataFrame:
    if force_reload and "Web_Traffic_Daily" in _MEMORY_CACHE:
        del _MEMORY_CACHE["Web_Traffic_Daily"]

    df = _parquet_or_csv("Web_Traffic_Daily", parse_dates=["Date"])
    if not pd.api.types.is_datetime64_any_dtype(df["Date"]):
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df


def load_products(force_reload: bool = False) -> pd.DataFrame:
    if force_reload and "Product_Master" in _MEMORY_CACHE:
        del _MEMORY_CACHE["Product_Master"]
    return _parquet_or_csv("Product_Master")


def load_all_datasets() -> Dict[str, pd.DataFrame]:
    """Preloads all company datasets into memory for instantaneous API response times."""
    return {
        "sales": load_sales(),
        "customers": load_customers(),
        "group_ops": load_group_ops(),
        "marketing": load_marketing(),
        "inventory": load_inventory(),
        "quality": load_quality(),
        "production": load_production(),
        "service": load_service(),
        "web": load_web(),
        "products": load_products(),
    }
