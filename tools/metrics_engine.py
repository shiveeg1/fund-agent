"""
metrics_engine.py — Computes risk/return metrics using deterministic Python (no LLM).

Metrics computed: XIRR, CAGR, Sharpe, Sortino, Beta, Alpha, Max Drawdown, Volatility.

Spec: specs/tool_metrics_engine.md
"""
from __future__ import annotations

import logging
import time
from typing import Any

import numpy as np
import pandas as pd
from pyxirr import xirr


def run(config: Any, logger: logging.Logger, context: dict[str, Any]) -> dict[str, Any]:
    """
    Compute portfolio and per-fund risk/return metrics.

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

        metrics = compute_all_metrics(transactions, nav_records, logger)
        logger.info("Computed metrics for %d funds.", len(metrics))

        from tools import sheets_writer  # noqa: PLC0415

        rows_written = sheets_writer.append_timeseries(
            config=config,
            tab="Metrics",
            records=metrics,
            logger=logger,
        )

        context["metrics"] = metrics

    except Exception:
        logger.exception("metrics_engine failed.")
        raise

    return {
        "status": "success" if not errors else "partial",
        "rows_written": rows_written,
        "errors": errors,
        "duration_s": round(time.perf_counter() - start, 3),
    }


def compute_xirr(
    dates: list[Any], cashflows: list[float]
) -> float:
    """Compute XIRR for a series of cashflows on given dates."""
    return float(xirr(dates, cashflows))


def compute_cagr(nav_start: float, nav_end: float, years: float) -> float:
    """Compute Compound Annual Growth Rate."""
    if years <= 0 or nav_start <= 0:
        raise ValueError("years and nav_start must be positive.")
    return float((nav_end / nav_start) ** (1 / years) - 1)


def compute_sharpe(
    returns: pd.Series, risk_free_rate: float = 0.065, periods_per_year: int = 252
) -> float:
    """Compute annualised Sharpe ratio from a series of period returns."""
    excess = returns - risk_free_rate / periods_per_year
    std = returns.std(ddof=1)
    if std == 0:
        return 0.0
    return float((excess.mean() / std) * (periods_per_year ** 0.5))


def compute_sortino(
    returns: pd.Series, risk_free_rate: float = 0.065, periods_per_year: int = 252
) -> float:
    """Compute annualised Sortino ratio (downside deviation only)."""
    mar = risk_free_rate / periods_per_year
    downside = returns[returns < mar]
    downside_std = np.sqrt((downside ** 2).mean()) if len(downside) > 0 else 0.0
    if downside_std == 0:
        return 0.0
    excess_mean = returns.mean() - mar
    return float((excess_mean / downside_std) * (periods_per_year ** 0.5))


def compute_beta(fund_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """Compute Beta of fund relative to benchmark."""
    cov = fund_returns.cov(benchmark_returns)
    var = benchmark_returns.var(ddof=1)
    if var == 0:
        return 0.0
    return float(cov / var)


def compute_max_drawdown(nav_series: pd.Series) -> float:
    """Compute maximum drawdown from a NAV series."""
    rolling_max = nav_series.cummax()
    drawdown = (nav_series - rolling_max) / rolling_max
    return float(drawdown.min())


def compute_all_metrics(
    transactions: list[dict[str, Any]],
    nav_records: list[dict[str, Any]],
    logger: logging.Logger,
) -> list[dict[str, Any]]:
    """
    Aggregate metric computation across all funds.
    Returns list of metric records per fund.
    """
    # TODO: implement full metric aggregation per specs/tool_metrics_engine.md
    logger.warning("metrics_engine using stub aggregation — implement full logic.")
    return []
