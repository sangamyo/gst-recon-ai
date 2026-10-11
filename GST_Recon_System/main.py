"""Entry point for the GST Bulk Reconciliation desktop utility."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Dict, List

from colorama import Fore, Style, init

from recon_engine import ReconciliationEngine
from report_generator import ReportGenerator
from utils import GSTReconError, setup_logging


def parse_args(base_dir: Path) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GST Bulk Reconciliation System - Purchase Register vs GSTR-2B",
    )
    parser.add_argument(
        "--clients-dir",
        type=Path,
        default=base_dir / "Clients",
        help="Folder that contains one subfolder per client",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=base_dir / "Output",
        help="Destination folder for reconciliation workbooks",
    )
    return parser.parse_args()


def discover_clients(clients_dir: Path) -> List[Path]:
    return sorted([path for path in clients_dir.iterdir() if path.is_dir()])


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    init(autoreset=True)

    args = parse_args(base_dir)
    logger = setup_logging(base_dir / "error.log")

    if not args.clients_dir.exists():
        print(f"{Fore.RED}Clients folder not found at {args.clients_dir}{Style.RESET_ALL}")
        sys.exit(1)

    engine = ReconciliationEngine(logger)
    reporter = ReportGenerator(logger)

    overall: Dict[str, List[str]] = {"success": [], "failed": []}

    client_dirs = discover_clients(args.clients_dir)
    if not client_dirs:
        print(f"{Fore.YELLOW}No client folders found in {args.clients_dir}{Style.RESET_ALL}")
        return

    print(f"Found {len(client_dirs)} clients. Starting reconciliation...\n")

    for client_dir in client_dirs:
        client_name = client_dir.name
        purchase_file = client_dir / "Purchase.xlsx"
        gstr2b_file = client_dir / "GSTR2B.xlsx"

        print(f"{Fore.CYAN}[{client_name}] Processing invoices...{Style.RESET_ALL}")

        try:
            missing_files = [path.name for path in [purchase_file, gstr2b_file] if not path.exists()]
            if missing_files:
                raise GSTReconError(f"Missing files: {', '.join(missing_files)}")

            result = engine.reconcile(purchase_file, gstr2b_file)
            report_path = reporter.generate(client_name, result, args.output_dir)
            overall["success"].append(client_name)

            print(
                f"{Fore.GREEN}[{client_name}] Reconciliation complete. Report: {report_path}{Style.RESET_ALL}"
            )
        except GSTReconError as exc:
            overall["failed"].append(client_name)
            logger.error("Client %s failed: %s", client_name, exc, exc_info=True)
            print(f"{Fore.RED}[{client_name}] Failed: {exc}{Style.RESET_ALL}")
        except Exception as unexpected:
            overall["failed"].append(client_name)
            logger.exception("Unexpected error for client %s", client_name)
            print(
                f"{Fore.RED}[{client_name}] Unexpected error. See error.log for details.{Style.RESET_ALL}"
            )

    print("\n===== RUN SUMMARY =====")
    print(f"Successful clients : {len(overall['success'])}")
    if overall["success"]:
        print("  - " + ", ".join(overall["success"]))
    print(f"Failed clients     : {len(overall['failed'])}")
    if overall["failed"]:
        print("  - " + ", ".join(overall["failed"]))


if __name__ == "__main__":
    main()
