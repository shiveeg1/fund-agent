# Tool Spec: llm_analyst

## Purpose
Call Claude API to generate a narrative interpretation of computed portfolio metrics.
**Never compute any financial metric here — only interpret pre-computed numbers.**

## Input (from context)
- `context["metrics"]` — metric records from metrics_engine
- `context["peer_records"]` — peer comparison records from peer_fetcher

## Behaviour
1. If `metrics` is empty, skip and return `status="skipped"`.
2. Format metrics and peer data into the ANALYST_PROMPT (see `specs/llm_prompts.md`).
3. Call `anthropic.Anthropic.messages.create()` with model `claude-sonnet-4-6`.
4. Write response text to `LLM_Analysis` tab with token counts.
5. Store response text in `context["llm_analysis"]`.

## Claude API Settings
- Model: `claude-sonnet-4-6`
- max_tokens: 1024
- temperature: default (1.0)

## Return Dict
```python
{"status": "success"|"skipped", "rows_written": int, "errors": list[str], "duration_s": float}
```

## Guardrails
- Do NOT pass raw transaction data or NAV time-series to the LLM.
- Only pass pre-summarised metric values (floats and labels).
- Prompt must include "Do NOT recompute any numbers."

## Tests
- `tests/test_llm_analyst.py`: mock `anthropic.Anthropic`, assert prompt construction.
