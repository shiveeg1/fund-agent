"""
main.py — Orchestrator for the SIP Portfolio workflow.
Calls each tool in order and collects results.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from config import Config, load_config
from tools import (
    cams_parser,
    composition_fetcher,
    llm_analyst,
    llm_advisor,
    metrics_engine,
    nav_fetcher,
    overlap_engine,
    peer_fetcher,
    sheets_writer,
    tax_engine,
    ter_fetcher,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

TOOLS_IN_ORDER = [
    ("nav_fetcher", nav_fetcher),
    ("ter_fetcher", ter_fetcher),
    ("composition_fetcher", composition_fetcher),
    ("cams_parser", cams_parser),
    ("peer_fetcher", peer_fetcher),
    ("metrics_engine", metrics_engine),
    ("overlap_engine", overlap_engine),
    ("llm_analyst", llm_analyst),
    ("llm_advisor", llm_advisor),
    ("tax_engine", tax_engine),
    ("sheets_writer", sheets_writer),
]

def run_workflow(config: Config) -> dict[str, Any]:
    """Run the full SIP portfolio workflow and return a summary of results."""
    logger.info("=== SIP Portfolio Workflow starting ===")
    workflow_start = time.perf_counter()

    results: dict[str, Any] = {}
    context: dict[str, Any] = {}  # shared data passed between tools

    for tool_name, tool_module in TOOLS_IN_ORDER:
        logger.info("Running tool: %s", tool_name)
        tool_start = time.perf_counter()
        try:
            result = tool_module.run(config=config, logger=logging.getLogger(tool_name), context=context)
            result["duration_s"] = round(time.perf_counter() - tool_start, 3)
            results[tool_name] = result
            context[tool_name] = result  # make available to downstream tools
            logger.info(
                "Tool %s finished — status=%s, rows_written=%s, duration=%.3fs",
                tool_name,
                result.get("status"),
                result.get("rows_written"),
                result["duration_s"],
            )
        except Exception:
            logger.exception("Tool %s raised an unhandled exception.", tool_name)
            raise

    total_duration = round(time.perf_counter() - workflow_start, 3)
    logger.info("=== Workflow complete in %.3fs ===", total_duration)
    return {"tools": results, "total_duration_s": total_duration}


if __name__ == "__main__":
    cfg = load_config()
    run_workflow(cfg)
