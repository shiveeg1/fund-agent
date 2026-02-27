"""
cams_parser.py — Parses CAMS consolidated account statements (PDF or JSON) to extract SIP transactions.

Spec: specs/tool_cams_parser.md

JSON format expected: {"dtTrxnResult": [{...}, ...]}
  FOLIO_NUMBER, SCHEME_NAME, TRADE_DATE (DD-MMM-YYYY), TRANSACTION_TYPE,
  AMOUNT, UNITS, PRICE (NAV at transaction)
"""
from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pdfplumber


# Transaction types that carry financial data (AMOUNT + UNITS populated)
_FINANCIAL_TXN_TYPES: set[str] = {
    "purchase",
    "purchase systematic",
    "purchase (continuous offer)",
    "redemption",
    "redemption of units",
    "redemption ",
    "switch-in",
    "switch out",
    "systematic switch in",
    "systematic transfer to - ",
    "systematic transfer from - ",
}


def run(config: Any, logger: logging.Logger, context: dict[str, Any]) -> dict[str, Any]:
    """
    Parse CAMS statement files (PDF and/or JSON) and write SIP transactions to Sheets.

    Looks for *.pdf and *.json files in data/cams/ relative to project root.

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
        json_files = sorted(cams_dir.glob("*.json")) if cams_dir.exists() else []

        if not pdf_files and not json_files:
            logger.warning("No CAMS files found in %s — skipping.", cams_dir)
            return {
                "status": "skipped",
                "rows_written": 0,
                "errors": [],
                "duration_s": round(time.perf_counter() - start, 3),
            }

        all_transactions: list[dict[str, Any]] = []

        for json_path in json_files:
            logger.info("Parsing CAMS JSON: %s", json_path)
            try:
                txns = _parse_cams_json(json_path, logger)
                all_transactions.extend(txns)
            except Exception as exc:
                logger.error("Failed to parse %s: %s", json_path, exc)
                errors.append(str(exc))
                raise

        for pdf_path in pdf_files:
            logger.info("Parsing CAMS PDF: %s", pdf_path)
            try:
                txns = _parse_cams_pdf(pdf_path, logger)
                all_transactions.extend(txns)
            except Exception as exc:
                logger.error("Failed to parse %s: %s", pdf_path, exc)
                errors.append(str(exc))
                raise

        # Deduplicate by (folio, transaction_date, units) per spec
        seen: set[tuple[str, str, float | None]] = set()
        deduped: list[dict[str, Any]] = []
        for txn in all_transactions:
            key = (txn["folio"], txn["transaction_date"], txn["units"])
            if key not in seen:
                seen.add(key)
                deduped.append(txn)

        logger.info(
            "Parsed %d transactions total (%d after dedup).",
            len(all_transactions),
            len(deduped),
        )

        from tools import sheets_writer  # noqa: PLC0415

        rows_written = sheets_writer.append_timeseries(
            config=config,
            tab="Transactions",
            records=deduped,
            logger=logger,
        )

        context["transactions"] = deduped

    except Exception:
        logger.exception("cams_parser failed.")
        raise

    return {
        "status": "success" if not errors else "partial",
        "rows_written": rows_written,
        "errors": errors,
        "duration_s": round(time.perf_counter() - start, 3),
    }


def _parse_cams_json(json_path: Path, logger: logging.Logger) -> list[dict[str, Any]]:
    """
    Extract financial transaction rows from a CAMS JSON export.

    Expected format: {"dtTrxnResult": [{FOLIO_NUMBER, SCHEME_NAME, TRADE_DATE,
                                         TRANSACTION_TYPE, AMOUNT, UNITS, PRICE, ...}]}

    Filters out non-financial records (nominee registration, address updates, etc.)
    by requiring AMOUNT and UNITS to be non-null.

    Returns list of dicts matching the Transactions tab schema:
        folio, scheme_name, transaction_date, txn_type, amount, units, nav
    """
    with json_path.open(encoding="utf-8") as fh:
        raw = json.load(fh)

    records: list[Any] = raw.get("dtTrxnResult", [])
    if not isinstance(records, list):
        raise ValueError(f"Expected dtTrxnResult to be a list in {json_path}")

    transactions: list[dict[str, Any]] = []
    skipped = 0

    for rec in records:
        amount = rec.get("AMOUNT")
        units = rec.get("UNITS")
        txn_type_raw: str = (rec.get("TRANSACTION_TYPE") or "").strip()

        # Skip non-financial records (no amount or units)
        if amount is None or units is None:
            skipped += 1
            continue

        # Skip blank or administrative transaction types
        if not txn_type_raw or txn_type_raw.lower() not in _FINANCIAL_TXN_TYPES:
            skipped += 1
            continue

        transaction_date = _parse_trade_date(rec.get("TRADE_DATE", ""))

        transactions.append({
            "folio": str(rec.get("FOLIO_NUMBER", "")).strip(),
            "scheme_name": str(rec.get("SCHEME_NAME", "")).strip(),
            "transaction_date": transaction_date,
            "txn_type": _normalise_txn_type(txn_type_raw),
            "amount": float(amount),
            "units": float(units),
            "nav": float(rec["PRICE"]) if rec.get("PRICE") is not None else None,
        })

    logger.debug(
        "JSON %s: %d financial transactions extracted, %d non-financial skipped.",
        json_path.name,
        len(transactions),
        skipped,
    )
    return transactions


def _parse_cams_pdf(pdf_path: Path, logger: logging.Logger) -> list[dict[str, Any]]:
    """
    Extract SIP transaction rows from a CAMS consolidated statement PDF.

    Pattern: DD-MMM-YYYY  <TxnType>  <amount>  <units>  <nav>

    Returns list of dicts: scheme_name, folio, transaction_date, amount, units, nav, txn_type.
    """
    # Regex: date  txn-type  amount(commas ok)  units  nav
    _TXN_RE = re.compile(
        r"(\d{2}-[A-Z]{3}-\d{4})\s+"
        r"(Purchase|SIP|Redemption|Switch(?:-In|-Out)?|Systematic[^\d]+?)\s+"
        r"([\d,]+\.?\d*)\s+"
        r"([\d,]+\.?\d*)\s+"
        r"([\d,]+\.?\d*)",
        re.IGNORECASE,
    )

    transactions: list[dict[str, Any]] = []
    current_scheme: str = ""
    current_folio: str = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                # Detect scheme / folio header lines
                folio_match = re.search(r"Folio\s*(?:No\.?|Number)?[:\s]+(\S+)", line, re.IGNORECASE)
                if folio_match:
                    current_folio = folio_match.group(1).strip()

                scheme_match = re.match(r"^([A-Z].{10,}(?:Fund|Plan|Scheme|Growth|Dividend))", line)
                if scheme_match:
                    current_scheme = scheme_match.group(1).strip()

                txn_match = _TXN_RE.search(line)
                if txn_match:
                    date_str, txn_type_raw, amount_str, units_str, nav_str = txn_match.groups()
                    transactions.append({
                        "folio": current_folio,
                        "scheme_name": current_scheme,
                        "transaction_date": _parse_trade_date(date_str),
                        "txn_type": _normalise_txn_type(txn_type_raw),
                        "amount": float(amount_str.replace(",", "")),
                        "units": float(units_str.replace(",", "")),
                        "nav": float(nav_str.replace(",", "")),
                    })

    logger.debug("Extracted %d transactions from %s", len(transactions), pdf_path)
    return transactions


def _parse_trade_date(date_str: str) -> str:
    """Convert 'DD-MMM-YYYY' to ISO 'YYYY-MM-DD'. Returns raw string on failure."""
    try:
        return datetime.strptime(date_str.strip(), "%d-%b-%Y").strftime("%Y-%m-%d")
    except ValueError:
        return date_str.strip()


def _normalise_txn_type(raw: str) -> str:
    """Map raw CAMS transaction type strings to canonical labels."""
    lower = raw.strip().lower()
    if "purchase systematic" in lower or "systematic" in lower and "switch" not in lower and "transfer" not in lower:
        return "SIP"
    if "purchase" in lower:
        return "Purchase"
    if "redemption" in lower:
        return "Redemption"
    if "switch" in lower and "in" in lower:
        return "Switch-In"
    if "switch" in lower and "out" in lower:
        return "Switch-Out"
    return raw.strip()
