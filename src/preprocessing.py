"""
Data preprocessing for Shopper Spectrum.

Implements the cleaning steps required by the project brief:
  * Remove rows with missing CustomerID
  * Exclude cancelled invoices (InvoiceNo starting with 'C')
  * Remove negative or zero quantities and prices
"""

from __future__ import annotations

import pandas as pd


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Clean a raw Online-Retail transactional frame.

    Returns a new frame with an added ``TotalPrice`` column
    (= Quantity * UnitPrice) and parsed ``InvoiceDate``.
    """
    df = df.copy()

    # Standardise dtypes
    df["InvoiceNo"] = df["InvoiceNo"].astype(str)
    df["StockCode"] = df["StockCode"].astype(str)
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")

    n0 = len(df)
    report = {"raw_rows": n0}

    # 1. Drop missing CustomerID
    df = df[df["CustomerID"].notna()]
    report["after_drop_missing_customer"] = len(df)

    # 2. Exclude cancelled invoices (InvoiceNo starting with 'C')
    df = df[~df["InvoiceNo"].str.upper().str.startswith("C")]
    report["after_drop_cancelled"] = len(df)

    # 3. Remove non-positive quantity / price
    df = df[(df["Quantity"] > 0) & (df["UnitPrice"] > 0)]
    report["after_drop_nonpositive"] = len(df)

    # 4. Drop duplicates and rows with no valid date / description
    df = df.dropna(subset=["InvoiceDate", "Description"])
    df = df.drop_duplicates()
    report["after_drop_dupes_nulls"] = len(df)

    # Derived fields
    df["CustomerID"] = df["CustomerID"].astype(float).astype("int64")
    df["Description"] = df["Description"].astype(str).str.strip()
    df["TotalPrice"] = df["Quantity"] * df["UnitPrice"]

    df.attrs["clean_report"] = report
    return df.reset_index(drop=True)


def build_rfm(df: pd.DataFrame, snapshot_date: pd.Timestamp | None = None) -> pd.DataFrame:
    """Compute Recency / Frequency / Monetary table per customer.

    Recency  = (snapshot date) - (customer's last purchase date)  [days]
    Frequency = number of distinct invoices per customer
    Monetary  = total amount spent by customer
    """
    if snapshot_date is None:
        # One day after the latest transaction, the standard convention.
        snapshot_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)

    rfm = df.groupby("CustomerID").agg(
        Recency=("InvoiceDate", lambda x: (snapshot_date - x.max()).days),
        Frequency=("InvoiceNo", "nunique"),
        Monetary=("TotalPrice", "sum"),
    ).reset_index()

    # Guard against degenerate monetary values
    rfm = rfm[rfm["Monetary"] > 0].reset_index(drop=True)
    rfm.attrs["snapshot_date"] = snapshot_date
    return rfm
