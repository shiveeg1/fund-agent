"""
composition_fetcher.py — Fetches fund portfolio composition (holdings) and writes to Sheets.

Spec: specs/tool_composition_fetcher.md
"""
from __future__ import annotations

import logging
import time
from typing import Any

import requests


def run(config: Any, logger: logging.Logger, context: dict[str, Any]) -> dict[str, Any]:
    """
    Fetch fund composition data for each fund in portfolio.

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
        composition_records = _fetch_compositions(nav_records, logger)
        logger.info("Fetched composition data for %d funds.", len(composition_records))

        from tools import sheets_writer  # noqa: PLC0415

        rows_written = sheets_writer.append_timeseries(
            config=config,
            tab="Composition_History",
            records=composition_records,
            logger=logger,
        )

        context["composition_records"] = composition_records

    except Exception:
        logger.exception("composition_fetcher failed.")
        raise

    return {
        "status": "success" if not errors else "partial",
        "rows_written": rows_written,
        "errors": errors,
        "duration_s": round(time.perf_counter() - start, 3),
    }


def _fetch_compositions(
    nav_records: list[dict[str, Any]], logger: logging.Logger
) -> list[dict[str, Any]]:
    """
    Fetch portfolio composition for each fund.
    Returns list of holding records: scheme_code, isin, stock_name, weight_pct, as_of_date.
    """
    # TODO: implement per specs/tool_composition_fetcher.md (mfapi.in or AMFI monthly disclosure)
    logger.warning("Composition fetch is using stub implementation.")
    return []
