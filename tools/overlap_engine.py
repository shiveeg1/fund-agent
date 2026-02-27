"""
overlap_engine.py — Computes stock-level overlap between funds to detect portfolio concentration.

Spec: specs/tool_overlap_engine.md
"""
from __future__ import annotations

import logging
import time
from itertools import combinations
from typing import Any

import pandas as pd


def run(config: Any, logger: logging.Logger, context: dict[str, Any]) -> dict[str, Any]:
    """
    Compute pairwise fund overlap and write results to Sheets Overlap tab.

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
        composition_records = context.get("composition_fetcher", {}).get("composition_records", [])
        overlap_records = compute_pairwise_overlap(composition_records, logger)
        logger.info("Computed %d pairwise overlap records.", len(overlap_records))

        from tools import sheets_writer  # noqa: PLC0415

        rows_written = sheets_writer.append_timeseries(
            config=config,
            tab="Overlap",
            records=overlap_records,
            logger=logger,
        )

        context["overlap_records"] = overlap_records

    except Exception:
        logger.exception("overlap_engine failed.")
        raise

    return {
        "status": "success" if not errors else "partial",
        "rows_written": rows_written,
        "errors": errors,
        "duration_s": round(time.perf_counter() - start, 3),
    }


def compute_pairwise_overlap(
    composition_records: list[dict[str, Any]],
    logger: logging.Logger,
) -> list[dict[str, Any]]:
    """
    Compute Jaccard and weighted overlap between every pair of funds.

    Args:
        composition_records: List of holding dicts (scheme_code, isin, weight_pct).
        logger: Bound logger.

    Returns:
        List of overlap dicts: fund_a, fund_b, jaccard_overlap, weighted_overlap_pct.
    """
    if not composition_records:
        return []

    df = pd.DataFrame(composition_records)
    fund_holdings: dict[str, dict[str, float]] = {}

    for scheme_code, group in df.groupby("scheme_code"):
        fund_holdings[str(scheme_code)] = dict(
            zip(group["isin"].tolist(), group["weight_pct"].tolist())
        )

    results: list[dict[str, Any]] = []
    fund_codes = list(fund_holdings.keys())

    for fund_a, fund_b in combinations(fund_codes, 2):
        holdings_a = set(fund_holdings[fund_a].keys())
        holdings_b = set(fund_holdings[fund_b].keys())

        intersection = holdings_a & holdings_b
        union = holdings_a | holdings_b

        jaccard = len(intersection) / len(union) if union else 0.0

        weights_a = fund_holdings[fund_a]
        weights_b = fund_holdings[fund_b]
        weighted_overlap = sum(
            min(weights_a.get(isin, 0), weights_b.get(isin, 0)) for isin in intersection
        )

        results.append(
            {
                "fund_a": fund_a,
                "fund_b": fund_b,
                "jaccard_overlap": round(jaccard, 4),
                "weighted_overlap_pct": round(weighted_overlap, 4),
                "common_stocks": len(intersection),
            }
        )

    return results
