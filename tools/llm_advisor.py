"""
llm_advisor.py — Calls Claude API to generate rebalancing recommendations.

NOTE: This tool ONLY calls Claude for recommendations. All metrics must already
be computed by metrics_engine.py. Never compute financial numbers here.

Spec: specs/tool_llm_advisor.md
Prompts: specs/llm_prompts.md
"""
from __future__ import annotations

import logging
import time
from typing import Any

import anthropic


def run(config: Any, logger: logging.Logger, context: dict[str, Any]) -> dict[str, Any]:
    """
    Generate LLM-based rebalancing recommendations for the portfolio.

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
        metrics = context.get("metrics", [])
        overlap_records = context.get("overlap_records", [])
        llm_analysis = context.get("llm_analysis", "")
        guidelines = config.guidelines

        if not metrics:
            logger.warning("No metrics in context — skipping LLM advisor.")
            return {
                "status": "skipped",
                "rows_written": 0,
                "errors": [],
                "duration_s": round(time.perf_counter() - start, 3),
            }

        recommendations = _call_claude_advisor(
            config=config,
            metrics=metrics,
            overlap_records=overlap_records,
            analysis=llm_analysis,
            guidelines=guidelines,
            logger=logger,
        )

        from tools import sheets_writer  # noqa: PLC0415

        rows_written = sheets_writer.append_timeseries(
            config=config,
            tab="Recommendations",
            records=[{"recommendations_text": recommendations}],
            logger=logger,
        )

        context["recommendations"] = recommendations

    except Exception:
        logger.exception("llm_advisor failed.")
        raise

    return {
        "status": "success" if not errors else "partial",
        "rows_written": rows_written,
        "errors": errors,
        "duration_s": round(time.perf_counter() - start, 3),
    }


def _call_claude_advisor(
    config: Any,
    metrics: list[dict[str, Any]],
    overlap_records: list[dict[str, Any]],
    analysis: str,
    guidelines: dict[str, Any],
    logger: logging.Logger,
) -> str:
    """
    Call Claude API with metrics and overlap data, return rebalancing recommendations.
    Uses prompt template from specs/llm_prompts.md — ADVISOR_PROMPT.
    """
    client = anthropic.Anthropic(api_key=config.anthropic_api_key)

    guidelines_text = "\n".join(f"- {k}: {v}" for k, v in guidelines.items()) or "None specified."
    overlap_text = _format_overlap_for_prompt(overlap_records)

    prompt = (
        "You are a portfolio advisor. Based on the analysis and metrics below, "
        "provide specific rebalancing recommendations (add/reduce/exit funds) "
        "following the portfolio guidelines.\n\n"
        f"## Portfolio Guidelines\n{guidelines_text}\n\n"
        f"## Prior Analysis\n{analysis or 'None.'}\n\n"
        f"## Fund Overlap\n{overlap_text}\n\n"
        "List 3-5 actionable recommendations. Do NOT invent numbers."
    )

    logger.info("Calling Claude API for rebalancing recommendations.")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _format_overlap_for_prompt(overlap_records: list[dict[str, Any]]) -> str:
    if not overlap_records:
        return "No overlap data available."
    high_overlap = [r for r in overlap_records if r.get("jaccard_overlap", 0) > 0.4]
    if not high_overlap:
        return "No significant fund overlap detected."
    lines = [
        f"- {r['fund_a']} / {r['fund_b']}: Jaccard={r['jaccard_overlap']:.0%}, "
        f"Weighted={r['weighted_overlap_pct']:.0%}"
        for r in high_overlap
    ]
    return "\n".join(lines)
