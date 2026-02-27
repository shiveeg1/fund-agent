"""
cams_parser.py — Parses CAMS/Karvy PDF consolidated account statements to extract SIP transactions.

Spec: specs/tool_cams_parser.md
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import pdfplumber


def run(config: Any, logger: logging.Logger, context: dict[str, Any]) -> dict[str, Any]:
    """
    Parse CAMS PDF statement and write SIP transactions to Sheets.

    Looks for PDF files in data/cams/ relative to project root.

    Args:
        config:  Config dataclass instance.
        logger:  Bound logger for this tool.
        context: Shared pipeline context (read/write).

    Returns:
        dict with keys: status, rows_written, errors, duration_s
    """
    start = time.perf_counter()
    errors: list[str] = []
    rows_written = 0

    try:
        cams_dir = Path("data/cams")
        pdf_files = sorted(cams_dir.glob("*.pdf")) if cams_dir.exists() else []

        if not pdf_files:
            logger.warning("No CAMS PDF files found in %s — skipping.", cams_dir)
            return {
                "status": "skipped",
                "rows_written": 0,
                "errors": [],
                "duration_s": round(time.perf_counter() - start, 3),
            }

        all_transactions: list[dict[str, Any]] = []
        for pdf_path in pdf_files:
            logger.info("Parsing CAMS PDF: %s", pdf_path)
            try:
                txns = _parse_cams_pdf(pdf_path, logger)
                all_transactions.extend(txns)
            except Exception as exc:
                logger.error("Failed to parse %s: %s", pdf_path, exc)
                errors.append(str(exc))

        logger.info("Parsed %d transactions total.", len(all_transactions))

        from tools import sheets_writer  # noqa: PLC0415

        rows_written = sheets_writer.append_timeseries(
            config=config,
            tab="Transactions",
            records=all_transactions,
            logger=logger,
        )

        context["transactions"] = all_transactions

    except Exception:
        logger.exception("cams_parser failed.")
        raise

    return {
        "status": "success" if not errors else "partial",
        "rows_written": rows_written,
        "errors": errors,
        "duration_s": round(time.perf_counter() - start, 3),
    }


def _parse_cams_pdf(pdf_path: Path, logger: logging.Logger) -> list[dict[str, Any]]:
    """
    Extract SIP transaction rows from a CAMS consolidated statement PDF.

    Returns list of dicts: scheme_name, folio, transaction_date, amount, units, nav, txn_type.
    """
    transactions: list[dict[str, Any]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            # TODO: implement line-by-line regex parsing per specs/tool_cams_parser.md
            _ = text  # suppress unused warning until implemented
    logger.debug("Extracted %d transactions from %s", len(transactions), pdf_path)
    return transactions
