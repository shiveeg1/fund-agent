"""
hooks/post_tool.py — Post-tool hook: logs tool run results to the Sheets Run_Log tab.

Called by the workflow after each tool completes (see main.py and hooks/.claude/hooks/).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def log_tool_run(
    config: Any,
    tool_name: str,
    result: dict[str, Any],
) -> None:
    """
    Write a single run log record to the Run_Log Sheets tab.

    Args:
        config:    Config dataclass instance.
        tool_name: Name of the tool that ran.
        result:    Tool return dict {status, rows_written, errors, duration_s}.
    """
    from tools import sheets_writer  # noqa: PLC0415

    record = {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "tool_name": tool_name,
        "status": result.get("status", "unknown"),
        "rows_written": result.get("rows_written", 0),
        "duration_s": result.get("duration_s", 0.0),
        "errors": json.dumps(result.get("errors", [])),
    }

    try:
        sheets_writer.append_timeseries(
            config=config,
            tab="Run_Log",
            records=[record],
            logger=logger,
        )
        logger.debug("Logged run for tool '%s' to Run_Log.", tool_name)
    except Exception:
        # Never let logging failure crash the workflow
        logger.warning("Failed to write run log for tool '%s' to Sheets.", tool_name, exc_info=True)


def run(config: Any, tool_name: str, result: dict[str, Any]) -> None:
    """Entry point for post-tool hook."""
    log_tool_run(config=config, tool_name=tool_name, result=result)
