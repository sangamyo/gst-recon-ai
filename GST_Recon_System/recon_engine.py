"""Core reconciliation logic for comparing Purchase Register vs GSTR-2B."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import pandas as pd

from utils import (
    ColumnContract,
    EmptyFileError,
    FileProcessingError,
    MissingColumnsError,
    build_match_key,
    coerce_numeric,
    ensure_columns,
    normalize_dates,
    normalize_gstin,
    normalize_invoice_number,
    read_excel,
)


@dataclass
class ReconciliationResult:
    """Bundled outcome of a reconciliation run."""

    summary: Dict[str, float]
    matched: pd.DataFrame
    mismatched: pd.DataFrame
    missing: pd.DataFrame
    extra: pd.DataFrame


class ReconciliationEngine:
    """Encapsulates all business rules for GST reconciliation."""

    PURCHASE_CONTRACT = ColumnContract(
        required=[
            "Supplier_GSTIN",
            "Invoice_No",
            "Invoice_Date",
            "CGST",
            "SGST",
            "IGST",
            "Total_Tax",
        ],
        optional_defaults={"Taxable_Value": 0},
    )

    GSTR2B_CONTRACT = ColumnContract(
        required=["GSTIN_of_Supplier", "Invoice_Number", "Invoice_Date", "Tax_Amount"],
        optional_defaults={"Taxable_Value": 0, "Filing_Status": "UNKNOWN"},
    )

    def __init__(self, logger):
        self.logger = logger

    def reconcile(self, purchase_path: Path, gstr2b_path: Path) -> ReconciliationResult:
        """Public entry point invoked per client."""

        purchase_df = self._prepare_purchase_df(purchase_path)
        gstr2b_df = self._prepare_gstr2b_df(gstr2b_path)

        merged = purchase_df.merge(
            gstr2b_df,
            on="match_key",
            how="outer",
            suffixes=("_purchase", "_gstr2b"),
            indicator=False,
        )
        merged = self._coalesce_common_fields(merged)

        merged = merged.copy()
        merged.loc[:, "tax_difference"] = (
            merged["purchase_total_tax"].fillna(0) - merged["gstr2b_tax_amount"].fillna(0)
        ).round(2)
        merged.loc[:, "in_purchase"] = merged["purchase_source_rows"].fillna(0) > 0
        merged.loc[:, "in_gstr2b"] = merged["gstr2b_source_rows"].fillna(0) > 0

        both_mask = merged["in_purchase"] & merged["in_gstr2b"]
        matched = merged[both_mask & (merged["tax_difference"] == 0)]
        mismatched = merged[both_mask & (merged["tax_difference"] != 0)]
        missing = merged[merged["in_purchase"] & ~merged["in_gstr2b"]]
        extra = merged[~merged["in_purchase"] & merged["in_gstr2b"]]

        summary = self._build_summary(
            purchase_df,
            gstr2b_df,
            matched_rows=len(matched),
            mismatched_rows=len(mismatched),
            missing_rows=len(missing),
            extra_rows=len(extra),
        )

        return ReconciliationResult(
            summary=summary,
            matched=self._export_view(matched),
            mismatched=self._export_view(mismatched),
            missing=self._export_view(missing),
            extra=self._export_view(extra),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _prepare_purchase_df(self, file_path: Path) -> pd.DataFrame:
        df = read_excel(file_path, "Purchase Register")
        df = ensure_columns(df, self.PURCHASE_CONTRACT, "Purchase Register").copy()

        rename_map = {
            "Supplier_GSTIN": "gstin",
            "Invoice_No": "invoice_number",
            "Invoice_Date": "invoice_date",
            "Taxable_Value": "purchase_taxable_value",
            "CGST": "purchase_cgst",
            "SGST": "purchase_sgst",
            "IGST": "purchase_igst",
            "Total_Tax": "purchase_total_tax",
        }
        df = df.rename(columns=rename_map).copy()

        df.loc[:, "gstin"] = df["gstin"].map(normalize_gstin)
        df.loc[:, "invoice_number"] = df["invoice_number"].map(normalize_invoice_number)
        df.loc[:, "invoice_date"] = normalize_dates(df["invoice_date"])

        for column in [
            "purchase_taxable_value",
            "purchase_cgst",
            "purchase_sgst",
            "purchase_igst",
            "purchase_total_tax",
        ]:
            df.loc[:, column] = coerce_numeric(df[column])

        df.loc[:, "purchase_total_tax"] = df["purchase_total_tax"].fillna(
            df["purchase_cgst"] + df["purchase_sgst"] + df["purchase_igst"]
        ).round(2)

        df = self._drop_incomplete_rows(df, dataset_name="Purchase Register")
        df.loc[:, "match_key"] = build_match_key(df)

        return self._aggregate_duplicates(
            df,
            numeric_columns=[
                "purchase_taxable_value",
                "purchase_cgst",
                "purchase_sgst",
                "purchase_igst",
                "purchase_total_tax",
            ],
            text_columns=["gstin", "invoice_number", "invoice_date"],
            source_label="purchase_source_rows",
        )

    def _prepare_gstr2b_df(self, file_path: Path) -> pd.DataFrame:
        df = read_excel(file_path, "GSTR-2B")
        df = ensure_columns(df, self.GSTR2B_CONTRACT, "GSTR-2B").copy()

        rename_map = {
            "GSTIN_of_Supplier": "gstin",
            "Invoice_Number": "invoice_number",
            "Invoice_Date": "invoice_date",
            "Taxable_Value": "gstr2b_taxable_value",
            "Tax_Amount": "gstr2b_tax_amount",
            "Filing_Status": "filing_status",
        }
        df = df.rename(columns=rename_map).copy()

        df.loc[:, "gstin"] = df["gstin"].map(normalize_gstin)
        df.loc[:, "invoice_number"] = df["invoice_number"].map(normalize_invoice_number)
        df.loc[:, "invoice_date"] = normalize_dates(df["invoice_date"])
        df.loc[:, "filing_status"] = df["filing_status"].fillna("UNKNOWN").map(str.upper)

        df.loc[:, "gstr2b_taxable_value"] = coerce_numeric(df["gstr2b_taxable_value"])
        df.loc[:, "gstr2b_tax_amount"] = coerce_numeric(df["gstr2b_tax_amount"])

        df = self._drop_incomplete_rows(df, dataset_name="GSTR-2B")
        df.loc[:, "match_key"] = build_match_key(df)

        return self._aggregate_duplicates(
            df,
            numeric_columns=["gstr2b_taxable_value", "gstr2b_tax_amount"],
            text_columns=["gstin", "invoice_number", "invoice_date", "filing_status"],
            source_label="gstr2b_source_rows",
        )

    def _drop_incomplete_rows(self, df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
        mask = (df["gstin"] != "") & (df["invoice_number"] != "")
        dropped = len(df) - mask.sum()
        if dropped:
            self.logger.warning(
                "Dropped %s rows from %s due to missing GSTIN/Invoice", dropped, dataset_name
            )
        return df.loc[mask].copy()

    def _aggregate_duplicates(
        self,
        df: pd.DataFrame,
        numeric_columns: List[str],
        text_columns: List[str],
        source_label: str,
    ) -> pd.DataFrame:
        agg_map = {col: "first" for col in text_columns}
        agg_map.update({col: "sum" for col in numeric_columns})
        agg_map[source_label] = "sum"

        df = df.copy()
        df.loc[:, source_label] = 1

        aggregated = df.groupby("match_key", as_index=False).agg(agg_map)
        return aggregated

    def _coalesce_common_fields(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        for field in ["gstin", "invoice_number", "invoice_date", "match_key"]:
            left = f"{field}_purchase"
            right = f"{field}_gstr2b"

            left_series = df[left] if left in df.columns else None
            right_series = df[right] if right in df.columns else None

            if left_series is None and right_series is None:
                continue

            if left_series is not None and right_series is not None:
                df.loc[:, field] = left_series.combine_first(right_series)
            elif left_series is not None:
                df.loc[:, field] = left_series
            else:
                df.loc[:, field] = right_series

            if left in df.columns:
                df = df.drop(columns=left)
            if right in df.columns:
                df = df.drop(columns=right)

        return df

    def _export_view(self, df: pd.DataFrame) -> pd.DataFrame:
        columns = [
            "gstin",
            "invoice_number",
            "invoice_date",
            "purchase_taxable_value",
            "purchase_total_tax",
            "gstr2b_taxable_value",
            "gstr2b_tax_amount",
            "tax_difference",
            "purchase_source_rows",
            "gstr2b_source_rows",
            "filing_status",
        ]

        for column in columns:
            if column not in df.columns:
                df[column] = 0 if "tax" in column or column.endswith("_rows") else ""

        ordered = df[columns].copy()
        ordered = ordered.sort_values(["gstin", "invoice_number", "invoice_date"])

        rename_map = {
            "gstin": "GSTIN",
            "invoice_number": "Invoice_Number",
            "invoice_date": "Invoice_Date",
            "purchase_taxable_value": "Purchase_Taxable_Value",
            "purchase_total_tax": "Purchase_Total_Tax",
            "gstr2b_taxable_value": "GSTR2B_Taxable_Value",
            "gstr2b_tax_amount": "GSTR2B_Tax_Amount",
            "tax_difference": "Tax_Difference",
            "purchase_source_rows": "Purchase_Row_Count",
            "gstr2b_source_rows": "GSTR2B_Row_Count",
            "filing_status": "Filing_Status",
        }

        ordered = ordered.rename(columns=rename_map)
        return ordered.reset_index(drop=True)

    def _build_summary(
        self,
        purchase_df: pd.DataFrame,
        gstr2b_df: pd.DataFrame,
        matched_rows: int,
        mismatched_rows: int,
        missing_rows: int,
        extra_rows: int,
    ) -> Dict[str, float]:
        purchase_total = float(purchase_df["purchase_total_tax"].sum().round(2))
        gstr_total = float(gstr2b_df["gstr2b_tax_amount"].sum().round(2))
        difference = round(purchase_total - gstr_total, 2)

        return {
            "total_purchase_invoices": int(len(purchase_df)),
            "total_gstr2b_invoices": int(len(gstr2b_df)),
            "matched_count": matched_rows,
            "mismatch_count": mismatched_rows,
            "missing_count": missing_rows,
            "extra_count": extra_rows,
            "total_itc_purchase": purchase_total,
            "total_itc_2b": gstr_total,
            "itc_difference": difference,
        }
