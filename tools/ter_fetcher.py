"""
ter_fetcher.py — Fetches Total Expense Ratio (TER) data and writes to Sheets TER_History tab.

Spec: specs/tool_ter_fetcher.md
"""
from __future__ import annotations

import logging
import time
from typing import Any

import requests


_SEBI_TER_URL = "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId=24"


def run(config: Any, logger: logging.Logger, context: dict[str, Any]) -> dict[str, Any]:
    """
    Fetch TER data for portfolio funds and write to Sheets.

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
        nav_records = context.get("nav_fetcher", {}).get("nav_records", [])
        if not nav_records:
            logger.warning("No NAV records in context — TER fetch may be incomplete.")

        ter_records = _fetch_ter_records(logger)
        logger.info("Fetched %d TER records.", len(ter_records))

        from tools import sheets_writer  # noqa: PLC0415

        rows_written = sheets_writer.append_timeseries(
            config=config,
            tab="TER_History",
            records=ter_records,
            logger=logger,
        )

        context["ter_records"] = ter_records

    except Exception:
        logger.exception("ter_fetcher failed.")
        raise

    return {
        "status": "success" if not errors else "partial",
        "rows_written": rows_written,
        "errors": errors,
        "duration_s": round(time.perf_counter() - start, 3),
    }


def _fetch_ter_records(logger: logging.Logger) -> list[dict[str, Any]]:
    """
    Fetch TER records from SEBI/AMFI source.
    Returns list of dicts with keys: scheme_code, scheme_name, ter_pct, effective_date.
    """
    # TODO: implement actual SEBI TER scraping per specs/tool_ter_fetcher.md
    logger.warning("TER fetch is using stub implementation — replace with real source.")
    return []
