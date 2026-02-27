# Tool Spec: ter_fetcher

## Purpose
Fetch the latest Total Expense Ratio (TER) for each portfolio fund and write to `TER_History` tab.

## Source
- Primary: SEBI monthly TER disclosures (https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId=24)
- Fallback: AMFI monthly TER data (https://www.amfiindia.com/research-information/other-data/expense-ratio)

## Behaviour
1. Download the latest TER disclosure page/file.
2. Parse scheme code, scheme name, TER percentage, and effective date.
3. Filter to portfolio schemes only.
4. Write to `TER_History` via `sheets_writer.append_timeseries()`.
5. Store in `context["ter_records"]`.

## Return Dict
```python
{"status": "success"|"partial", "rows_written": int, "errors": list[str], "duration_s": float}
```

## Error Handling
- On fetch failure: log warning, return `status="partial"` with error in `errors`.
- Do NOT raise on individual parse failures — log and skip.

## Tests
- `tests/test_ter_fetcher.py`: mock HTTP responses, assert TER parsing.
- Fixture: `tests/fixtures/amfi_ter_sample.html`
