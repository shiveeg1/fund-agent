# Tool Spec: llm_advisor

## Purpose
Call Claude API to generate rebalancing recommendations based on metrics, overlap, and guidelines.
**Never compute any financial metric here — only generate recommendations.**

## Input (from context)
- `context["metrics"]` — metric records from metrics_engine
- `context["overlap_records"]` — overlap records from overlap_engine
- `context["llm_analysis"]` — analysis text from llm_analyst
- `config.guidelines` — portfolio guidelines from Portfolio_Guidelines tab

## Behaviour
1. If `metrics` is empty, skip and return `status="skipped"`.
2. Format all inputs into the ADVISOR_PROMPT (see `specs/llm_prompts.md`).
3. Call `anthropic.Anthropic.messages.create()` with model `claude-sonnet-4-6`.
4. Write recommendations text to `Recommendations` tab with token counts.
5. Store in `context["recommendations"]`.

## Claude API Settings
- Model: `claude-sonnet-4-6`
- max_tokens: 1024
- temperature: default (1.0)

## Return Dict
```python
{"status": "success"|"skipped", "rows_written": int, "errors": list[str], "duration_s": float}
```

## Guardrails
- Prompt must include "Do NOT compute returns, tax, or any financial metric."
- Recommendations must reference only funds already in portfolio (unless exit action).

## Tests
- `tests/test_llm_advisor.py`: mock `anthropic.Anthropic`, assert prompt includes guidelines.
