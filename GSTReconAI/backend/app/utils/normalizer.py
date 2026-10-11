"""Normalization helpers for GST data."""
from __future__ import annotations

import pandas as pd


def normalize_gstin(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip().str.upper()


def normalize_invoice(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.replace(" ", "", regex=False).str.upper()


_ISO_LIKE = r"^\s*\d{4}[-/.]\d{1,2}[-/.]\d{1,2}"


def normalize_dates(series: pd.Series) -> pd.Series:
    """Parse invoice dates written in mixed formats.

    Excel datetimes are used as-is, year-first strings (2024-04-15, 2024/04/01) are parsed
    as Y-M-D, and everything else follows the Indian DD-MM-YYYY convention. Each value is
    parsed individually, so one file may mix formats.
    """
    as_text = series.astype(str)
    iso_mask = as_text.str.match(_ISO_LIKE, na=False)
    parsed = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")
    if iso_mask.any():
        parsed[iso_mask] = pd.to_datetime(series[iso_mask], errors="coerce", format="mixed", yearfirst=True)
    other = ~iso_mask & series.notna()
    if other.any():
        parsed[other] = pd.to_datetime(series[other], errors="coerce", format="mixed", dayfirst=True)
    return parsed.dt.date
