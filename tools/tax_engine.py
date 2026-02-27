"""
tax_engine.py — Computes LTCG and STCG tax liability on mutual fund redemptions.

Rules (India, FY 2024-25):
  Equity funds:  STCG @ 20% (held < 1 yr), LTCG @ 12.5% above ₹1.25 L (held ≥ 1 yr)
  Debt funds:    Gains taxed as per income slab (no indexation post Apr 2023)

Spec: specs/tool_tax_engine.md
"""
from __future__ import annotations

import logging
import time
from datetime import date, timedelta
from typing import Any


LTCG_EQUITY_THRESHOLD = 125_000  # ₹1.25 lakh exemption
LTCG_EQUITY_RATE = 0.125         # 12.5%
STCG_EQUITY_RATE = 0.20          # 20%
EQUITY_HOLDING_THRESHOLD_DAYS = 365


def run(config: Any, logger: logging.Logger, context: dict[str, Any]) -> dict[str, Any]:
    """
    Compute LTCG and STCG tax liability for all redemption transactions.

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
        transactions = context.get("cams_parser", {}).get("transactions", [])
        nav_records = context.get("nav_fetcher", {}).get("nav_records", [])

        tax_records = compute_tax_liability(transactions, nav_records, logger)
        logger.info("Computed tax liability for %d redemption events.", len(tax_records))

        from tools import sheets_writer  # noqa: PLC0415

        rows_written = sheets_writer.append_timeseries(
            config=config,
            tab="Tax_Liability",
            records=tax_records,
            logger=logger,
        )

        context["tax_records"] = tax_records

    except Exception:
        logger.exception("tax_engine failed.")
        raise

    return {
        "status": "success" if not errors else "partial",
        "rows_written": rows_written,
        "errors": errors,
        "duration_s": round(time.perf_counter() - start, 3),
    }


def compute_tax_liability(
    transactions: list[dict[str, Any]],
    nav_records: list[dict[str, Any]],
    logger: logging.Logger,
) -> list[dict[str, Any]]:
    """
    Apply FIFO matching to compute LTCG/STCG on redemption transactions.

    Args:
        transactions: List of transaction dicts from cams_parser.
        nav_records:  Current NAV records for unrealised gain estimation.
        logger:       Bound logger.

    Returns:
        List of tax event dicts: scheme_code, redemption_date, units, cost_basis,
        redemption_value, gain, gain_type (LTCG/STCG), tax_amount.
    """
    # TODO: implement FIFO matching and tax computation per specs/tool_tax_engine.md
    logger.warning("tax_engine using stub implementation — implement FIFO logic.")
    return []


def classify_holding(purchase_date: date, redemption_date: date, is_equity: bool) -> str:
    """Return 'LTCG' or 'STCG' based on holding period and fund type."""
    holding_days = (redemption_date - purchase_date).days
    if is_equity:
        return "LTCG" if holding_days >= EQUITY_HOLDING_THRESHOLD_DAYS else "STCG"
    # Debt funds — always slab rate (treated as STCG equivalent post Apr 2023)
    return "STCG"


def compute_equity_tax(ltcg_total: float, stcg_total: float) -> dict[str, float]:
    """Compute actual tax payable on equity fund gains."""
    ltcg_taxable = max(0.0, ltcg_total - LTCG_EQUITY_THRESHOLD)
    ltcg_tax = ltcg_taxable * LTCG_EQUITY_RATE
    stcg_tax = stcg_total * STCG_EQUITY_RATE
    return {
        "ltcg_total": ltcg_total,
        "ltcg_taxable": ltcg_taxable,
        "ltcg_tax": ltcg_tax,
        "stcg_total": stcg_total,
        "stcg_tax": stcg_tax,
        "total_tax": ltcg_tax + stcg_tax,
    }
