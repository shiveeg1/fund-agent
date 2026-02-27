# Tool Spec: composition_fetcher

## Purpose
Fetch monthly portfolio composition (top holdings) for each fund and write to `Composition_History`.

## Source
- mfapi.in: `https://api.mfapi.in/mf/{scheme_code}/portfolio` (unofficial, no auth)
- AMFI monthly disclosure PDFs as fallback

## Behaviour
1. For each scheme code in portfolio, GET `/mf/{scheme_code}/portfolio`.
2. Parse: `isin`, `company_name`, `weight_pct` (percentage), `as_of_date`.
3. Write all holdings to `Composition_History` via `sheets_writer.append_timeseries()`.
4. Store in `context["composition_records"]`.

## Return Dict
```python
{"status": "success"|"partial", "rows_written": int, "errors": list[str], "duration_s": float}
```

## Rate Limiting
- Add 0.5-second delay between API calls.
- On 429 response: back off 10 seconds and retry once.

## Tests
- `tests/test_composition_fetcher.py`: mock mfapi responses, assert holding extraction.
- Fixture: `tests/fixtures/mfapi_composition_sample.json`
