"""
sheets_writer.py — Writes data to Google Sheets via the Sheets API.

ALL Sheets writes from other tools must go through append_timeseries() in this module.

Spec: specs/tool_sheets_writer.md
"""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build


_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Cache the Sheets service so we don't re-authenticate on every call
_service_cache: dict[str, Any] = {}


def run(config: Any, logger: logging.Logger, context: dict[str, Any]) -> dict[str, Any]:
    """
    Final tool run: flushes any buffered writes and validates Sheets connectivity.

    Args:
        config:  Config dataclass instance.
        logger:  Bound logger for this tool.
        context: Shared pipeline context.

    Returns:
        dict with keys: status, rows_written, errors, duration_s
    """
    start = time.perf_counter()
    try:
        service = _get_service(config)
        # Validate connectivity by reading sheet metadata
        service.spreadsheets().get(spreadsheetId=config.google_sheets_id).execute()
        logger.info("Sheets connectivity verified for spreadsheet %s.", config.google_sheets_id)
    except Exception:
        logger.exception("sheets_writer run() connectivity check failed.")
        raise

    return {
        "status": "success",
        "rows_written": 0,
        "errors": [],
        "duration_s": round(time.perf_counter() - start, 3),
    }


def append_timeseries(
    config: Any,
    tab: str,
    records: list[dict[str, Any]],
    logger: logging.Logger,
) -> int:
    """
    Append records to the specified Sheets tab.

    Args:
        config:  Config dataclass instance.
        tab:     Name of the target Sheets tab (must be in specs/schema.md).
        records: List of row dicts. Keys become column headers on first write.
        logger:  Bound logger.

    Returns:
        Number of rows written.
    """
    if not records:
        logger.debug("append_timeseries: no records to write to tab '%s'.", tab)
        return 0

    service = _get_service(config)
    rows = _records_to_rows(records)

    body = {"values": rows}
    range_notation = f"{tab}!A1"

    result = (
        service.spreadsheets()
        .values()
        .append(
            spreadsheetId=config.google_sheets_id,
            range=range_notation,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body,
        )
        .execute()
    )

    updated_rows = result.get("updates", {}).get("updatedRows", len(rows))
    logger.info("Appended %d rows to tab '%s'.", updated_rows, tab)
    return updated_rows


def _get_service(config: Any) -> Any:
    """Build and cache the Google Sheets API service client."""
    cache_key = config.google_sheets_id
    if cache_key in _service_cache:
        return _service_cache[cache_key]

    creds_path = Path(config.google_service_account_json)
    if not creds_path.exists():
        raise FileNotFoundError(
            f"Service account JSON not found: {creds_path}. "
            "Set GOOGLE_SERVICE_ACCOUNT_JSON in .env."
        )

    credentials = service_account.Credentials.from_service_account_file(
        str(creds_path), scopes=_SCOPES
    )
    service = build("sheets", "v4", credentials=credentials, cache_discovery=False)
    _service_cache[cache_key] = service
    return service


def _records_to_rows(records: list[dict[str, Any]]) -> list[list[Any]]:
    """Convert a list of dicts to a 2-D list (no header row — values only)."""
    if not records:
        return []
    keys = list(records[0].keys())
    return [[row.get(k, "") for k in keys] for row in records]
