"""
llm_analyst.py — Calls Claude API to interpret computed metrics and generate analysis narrative.

NOTE: This tool ONLY calls Claude for interpretation. All metrics must already be computed
by metrics_engine.py. Never compute financial numbers here.

Spec: specs/tool_llm_analyst.md
Prompts: specs/llm_prompts.md
"""
from __future__ import annotations

import logging
import time
from typing import Any

import anthropic


def run(config: Any, logger: logging.Logger, context: dict[str, Any]) -> dict[str, Any]:
    """
    Generate LLM-based narrative analysis of portfolio metrics.

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
        metrics = context.get("metrics", {}).get("metrics", [])
        peer_records = context.get("peer_records", {}).get("peer_records", [])

        if not metrics:
            logger.warning("No metrics in context — skipping LLM analysis.")
            return {
                "status": "skipped",
                "rows_written": 0,
                "errors": [],
                "duration_s": round(time.perf_counter() - start, 3),
            }

        analysis = _call_claude_analyst(
            config=config,
            metrics=metrics,
            peer_records=peer_records,
            logger=logger,
        )

        from tools import sheets_writer  # noqa: PLC0415

        rows_written = sheets_writer.append_timeseries(
            config=config,
            tab="LLM_Analysis",
            records=[{"analysis_text": analysis}],
            logger=logger,
        )

        context["llm_analysis"] = analysis

    except Exception:
        logger.exception("llm_analyst failed.")
        raise

    return {
        "status": "success" if not errors else "partial",
        "rows_written": rows_written,
        "errors": errors,
        "duration_s": round(time.perf_counter() - start, 3),
    }


def _call_claude_analyst(
    config: Any,
    metrics: list[dict[str, Any]],
    peer_records: list[dict[str, Any]],
    logger: logging.Logger,
) -> str:
    """
    Call Claude API with metrics data and return the analysis narrative.
    Uses prompt template from specs/llm_prompts.md — ANALYST_PROMPT.
    """
    client = anthropic.Anthropic(api_key=config.anthropic_api_key)

    metrics_summary = _format_metrics_for_prompt(metrics)
    peer_summary = _format_peer_for_prompt(peer_records)

    prompt = (
        "You are a mutual fund analyst. Below are the computed portfolio metrics.\n"
        "Provide a concise interpretation (3-5 bullet points) of portfolio health, "
        "highlighting any funds that are underperforming peers or showing elevated risk.\n\n"
        f"## Portfolio Metrics\n{metrics_summary}\n\n"
        f"## Peer Comparison\n{peer_summary}\n\n"
        "Do NOT recompute any numbers. Only interpret what is given."
    )

    logger.info("Calling Claude API for portfolio analysis.")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _format_metrics_for_prompt(metrics: list[dict[str, Any]]) -> str:
    if not metrics:
        return "No metrics available."
    lines = []
    for m in metrics:
        lines.append(
            f"- {m.get('scheme_name', 'Unknown')}: XIRR={m.get('xirr', 'N/A')}, "
            f"Sharpe={m.get('sharpe', 'N/A')}, Beta={m.get('beta', 'N/A')}"
        )
    return "\n".join(lines)


def _format_peer_for_prompt(peer_records: list[dict[str, Any]]) -> str:
    if not peer_records:
        return "No peer data available."
    lines = []
    for p in peer_records:
        lines.append(
            f"- {p.get('scheme_name', 'Unknown')}: Category={p.get('category', 'N/A')}, "
            f"Rank={p.get('peer_rank', 'N/A')}"
        )
    return "\n".join(lines)
