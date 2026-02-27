"""
nav_fetcher.py — Fetches latest NAV data from AMFI and writes to Sheets NAV_History tab.

Spec: specs/tool_nav_fetcher.md
"""
from __future__ import annotations

import logging
import time
from typing import Any

import requests


def run(config: Any, logger: logging.Logger, context: dict[str, Any]) -> dict[str, Any]:
    """
    Fetch NAV for all funds from AMFI and write to Sheets.

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
        logger.info("Fetching NAV data from %s", config.amfi_base_url)
        response = requests.get(config.amfi_base_url, timeout=30)
        response.raise_for_status()

        nav_records = _parse_amfi_nav(response.text)
        logger.info("Parsed %d NAV records.", len(nav_records))

        # Write to Sheets via sheets_writer (imported lazily to avoid circular deps)
        from tools import sheets_writer  # noqa: PLC0415

        rows_written = sheets_writer.append_timeseries(
            config=config,
            tab="NAV_History",
            records=nav_records,
            logger=logger,
        )

        context["nav_records"] = nav_records

    except Exception:
        logger.exception("nav_fetcher failed.")
        raise

    return {
        "status": "success" if not errors else "partial",
        "rows_written": rows_written,
        "errors": errors,
        "duration_s": round(time.perf_counter() - start, 3),
    }


def _parse_amfi_nav(raw_text: str) -> list[dict[str, Any]]:
    """Parse AMFI NAVAll.txt format into a list of NAV record dicts."""
    records: list[dict[str, Any]] = []
    for line in raw_text.splitlines():
        parts = line.strip().split(";")
        if len(parts) < 6:
            continue
        scheme_code, _, _, scheme_name, nav_value, nav_date = parts[:6]
        try:
            records.append(
                {
                    "scheme_code": scheme_code.strip(),
                    "scheme_name": scheme_name.strip(),
                    "nav": float(nav_value.strip()),
                    "nav_date": nav_date.strip(),
                }
            )
        except ValueError:
            continue
    return records
