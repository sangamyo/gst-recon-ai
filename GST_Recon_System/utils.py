"""Utility helpers for the GST Reconciliation System."""
from __future__ import annotations

from dataclasses import dataclass
import logging
import warnings
from pathlib import Path
from typing import Iterable, List

import pandas as pd

# Adopt future-safe pandas behavior while suppressing noisy chained-assignment warnings that
# originate from internal merge operations (the code already works on explicit copies).
pd.options.mode.chained_assignment = None
warnings.filterwarnings(
    "ignore",
    message=".*ChainedAssignmentError.*",
    category=FutureWarning,
    module="pandas.core.reshape.merge",
)


class GSTReconError(Exception):
    """Base class for predictable reconciliation errors."""


class MissingColumnsError(GSTReconError):
    """Raised when required columns are missing from an input file."""

    def __init__(self, file_label: str, columns: List[str]):
        message = f"{file_label} is missing required columns: {', '.join(columns)}"
        super().__init__(message)
        self.columns = columns


class EmptyFileError(GSTReconError):
    """Raised when an input workbook has no rows."""

    def __init__(self, file_label: str):
        super().__init__(f"{file_label} does not contain any rows to process")


class FileProcessingError(GSTReconError):
    """Raised when an input workbook cannot be read."""

    def __init__(self, file_path: Path, original_error: Exception):
        message = f"Unable to read Excel file at {file_path}: {original_error}"
        super().__init__(message)
        self.original_error = original_error


@dataclass
class ColumnContract:
    """Describes the columns that must exist in an input sheet."""

    required: List[str]
    optional_defaults: dict


def setup_logging(log_file: Path) -> logging.Logger:
    """Configure application logging once and return a namespaced logger."""

    logger = logging.getLogger("gst_recon")
    if logger.handlers:
        return logger

    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def read_excel(file_path: Path, file_label: str) -> pd.DataFrame:
    """Safely load an Excel workbook using pandas."""

    if not file_path.exists():
        raise FileProcessingError(file_path, FileNotFoundError("File not found"))

    try:
        df = pd.read_excel(file_path, engine="openpyxl")
    except Exception as exc:  # pragma: no cover - handled gracefully in main flow
        raise FileProcessingError(file_path, exc) from exc

    if df.empty:
        raise EmptyFileError(file_label)

    return df


def normalize_string(value: str) -> str:
    """Trim and uppercase string values safely."""

    if pd.isna(value):
        return ""
    return str(value).strip().upper()


def normalize_invoice_number(value: str) -> str:
    """Normalize invoice numbers per business rule."""

    core = normalize_string(value)
    # Remove interior spaces to avoid false mismatches
    return core.replace(" ", "")


def normalize_gstin(value: str) -> str:
    """Ensure GSTINs are uppercase without spacing artifacts."""

    return normalize_string(value).replace(" ", "")


def ensure_columns(df: pd.DataFrame, contract: ColumnContract, file_label: str) -> pd.DataFrame:
    """Validate required columns and inject optional defaults as needed."""

    missing = [col for col in contract.required if col not in df.columns]
    if missing:
        raise MissingColumnsError(file_label, missing)

    for optional, default in contract.optional_defaults.items():
        if optional not in df.columns:
            df[optional] = default

    return df


def normalize_dates(series: pd.Series) -> pd.Series:
    """Convert date-like values into pandas datetime (date only)."""

    normalized = pd.to_datetime(series, errors="coerce", dayfirst=False)
    return normalized.dt.date


def coerce_numeric(series: pd.Series) -> pd.Series:
    """Convert a pandas Series to numeric with 2-decimal rounding."""

    numeric = pd.to_numeric(series, errors="coerce").fillna(0)
    return numeric.round(2)


def build_match_key(df: pd.DataFrame) -> pd.Series:
    """Construct the reconciliation key GSTIN + Invoice + Date."""

    gstin = df["gstin"].fillna("")
    invoice = df["invoice_number"].fillna("")
    date_values = df["invoice_date"].fillna("MISSING_DATE")
    return gstin + "|" + invoice + "|" + date_values.astype(str)
