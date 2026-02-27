"""
peer_fetcher.py — Fetches peer/category benchmark data for each fund and writes to Sheets.

Spec: specs/tool_peer_fetcher.md
"""
from __future__ import annotations

import logging
import time
from typing import Any


def run(config: Any, logger: logging.Logger, context: dict[str, Any]) -> dict[str, Any]:
    """
    Fetch peer comparison data (category average returns, rank) for portfolio funds.

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
        peer_records = _fetch_peer_data(nav_records, logger)
        logger.info("Fetched peer data for %d funds.", len(peer_records))

        from tools import sheets_writer  # noqa: PLC0415

        rows_written = sheets_writer.append_timeseries(
            config=config,
            tab="Peer_Comparison",
            records=peer_records,
            logger=logger,
        )

        context["peer_records"] = peer_records

    except Exception:
        logger.exception("peer_fetcher failed.")
        raise

    return {
        "status": "success" if not errors else "partial",
        "rows_written": rows_written,
        "errors": errors,
        "duration_s": round(time.perf_counter() - start, 3),
    }


def _fetch_peer_data(
    nav_records: list[dict[str, Any]], logger: logging.Logger
) -> list[dict[str, Any]]:
    """
    Fetch category averages and peer rank for each fund.
    Returns list of dicts: scheme_code, category, category_avg_1y, category_avg_3y, peer_rank.
    """
    # TODO: implement per specs/tool_peer_fetcher.md
    logger.warning("Peer fetch is using stub implementation.")
    return []
