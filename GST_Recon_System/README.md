# GST Bulk Reconciliation System

> Lightweight command-line version of [GST Recon AI](../README.md). No server, database or login: drop Excel files into folders and get reconciliation workbooks back.

A production-ready, desktop-friendly automation utility for Chartered Accountants to reconcile Purchase Registers against GSTR-2B files in bulk. The tool consumes user-provided Excel workbooks (no GST Portal automation), validates data, applies deterministic matching rules, and produces formatted reconciliation reports per client.

## 📁 Project Layout

```
GST_Recon_System/
├── Clients/               # Drop one folder per client (Purchase.xlsx + GSTR2B.xlsx)
├── Output/                # Generated reconciliation workbooks (created on first run, git-ignored)
├── main.py                # Single entry point (python main.py)
├── recon_engine.py        # Normalization + matching engine
├── report_generator.py    # Excel report writer (summary + detail tabs)
├── utils.py               # Shared helpers, logging, validation
├── requirements.txt       # Python dependencies
└── README.md
```

## 🧠 Architecture at a Glance

- **Input Contracts** – `utils.ColumnContract` enforces the mandatory columns for each workbook while allowing optional fields with safe defaults.
- **Normalization Layer** – `recon_engine.ReconciliationEngine` standardizes GSTINs, invoice numbers, tax amounts, and dates, then consolidates duplicates per `(GSTIN, Invoice, Date)` key.
- **Matching Logic** – A single outer merge classifies rows into MATCH, TAX MISMATCH, MISSING (only in Purchase), or EXTRA (only in 2B) based on rounded tax deltas.
- **Reporting** – `ReportGenerator` writes a 5-sheet Excel report (SUMMARY, MATCHED, MISMATCH, MISSING, EXTRA) with frozen headers, auto-fit columns, and red highlights for mismatches.
- **Resilience** – Errors are captured in `error.log`, clients process independently, and missing/empty files are surfaced without crashing the batch.

## ✅ Features

- Bulk processing of unlimited client folders
- Deterministic reconciliation rules with decimal-safe rounding
- Duplicate invoice consolidation counters for audit traceability
- Graceful handling of missing columns, blank files, or inconsistent formats
- Stylish Excel outputs with highlights for mismatches
- Detailed logging plus friendly console progress updates (colorized)

## 📦 Installation

```bash
cd GST_Recon_System
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
pip install -r requirements.txt
```

> Windows PowerShell: `.\.venv\Scripts\activate` before installing requirements.

## ▶️ Running the Tool

1. Place each client’s files under `Clients/<ClientName>/` with exact filenames:
   - `Purchase.xlsx`
   - `GSTR2B.xlsx`
2. Run the reconciler from the project root:

```bash
python main.py
```

3. Reports appear in `Output/<ClientName>_Reconciliation_Report.xlsx` with all five tabs populated.

The repository ships with two synthetic sample clients (`Clients/Client_A`, `Clients/Client_B`) so you can try it immediately. Verified with Python 3.10 and 3.14.

### Optional Flags

- `--clients-dir /path/to/custom/clients`
- `--output-dir /path/to/custom/output`

## 🧪 Sample Test Data Format

| File           | Required Columns                                                                                               | Optional Columns (handled if missing) |
| -------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| `Purchase.xlsx` | `Supplier_GSTIN`, `Invoice_No`, `Invoice_Date`, `CGST`, `SGST`, `IGST`, `Total_Tax`                             | `Taxable_Value`                       |
| `GSTR2B.xlsx`   | `GSTIN_of_Supplier`, `Invoice_Number`, `Invoice_Date`, `Tax_Amount`                                             | `Taxable_Value`, `Filing_Status`      |

Sample rows (values trimmed/uppercased automatically):

| Supplier_GSTIN | Invoice_No | Invoice_Date | Taxable_Value | CGST | SGST | IGST | Total_Tax |
| -------------- | ---------- | ------------ | ------------- | ---- | ---- | ---- | --------- |
| 27ABCDE1234F1Z5 | INV-101    | 01-04-2024   | 100000        | 900  | 900  | 0    | 1800      |

| GSTIN_of_Supplier | Invoice_Number | Invoice_Date | Taxable_Value | Tax_Amount | Filing_Status |
| ----------------- | -------------- | ------------ | ------------- | ---------- | ------------- |
| 27ABCDE1234F1Z5   | inv-101        | 2024/04/01   | 100000        | 1800       | Filed         |

(Invoice numbers are uppercased and stripped of spaces before comparison.)

## 🛠 How It Works

1. **Load & Validate** – Each sheet is read via pandas/openpyxl with explicit column validation.
2. **Normalize** – GSTIN + invoice normalization, date parsing, numeric coercion, and duplicate aggregation.
3. **Match** – Keyed outer merge plus tax delta classification (`0` difference ⇒ MATCH, otherwise TAX MISMATCH).
4. **Report** – Results bucketed into sheets, summary metrics computed, and Excel workbook styled.

## 🗂 Logging & Error Handling

- All errors write to `error.log` in the project root (append-only).
- Console output clearly states which client succeeded or failed.
- Processing never stops on a bad client—subsequent folders continue automatically.

## 💾 Converting to an Executable (Windows)

1. Activate your virtual environment and install PyInstaller (`pip install pyinstaller`).
2. From the project root run:

```bash
pyinstaller --onefile --name GSTReconciler main.py
```

3. Distribute the generated `dist/GSTReconciler.exe` along with the `Clients` folder template.

## 🚀 Next Steps & Customisation

- Hook up email notifications after batch completion.
- Add CSV export of summary metrics for dashboards.
- Integrate simple UI wrapper (PyQt/Rich TUI) if needed.

Need help or enhancements? Open an issue or extend the modular components provided here.
