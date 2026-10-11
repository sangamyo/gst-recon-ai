"""Utilities for validating uploaded Excel workbooks."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

REQUIRED_PURCHASE_COLUMNS = {
    "Supplier_GSTIN",
    "Invoice_No",
    "Invoice_Date",
    "Total_Tax",
}

REQUIRED_2B_COLUMNS = {
    "GSTIN_of_Supplier",
    "Invoice_Number",
    "Invoice_Date",
    "Tax_Amount",
}


class ValidationError(Exception):
    pass


def validate_excel(file_path: Path, required_columns: Iterable[str]) -> pd.DataFrame:
    try:
        df = pd.read_excel(file_path, engine="openpyxl")
    except Exception as exc:
        raise ValidationError(f"Unable to read file {file_path.name}: {exc}") from exc

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValidationError(f"Missing required columns: {', '.join(missing)}")

    if df.empty:
        raise ValidationError("Workbook contains no data")

    return df
