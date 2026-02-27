# Tool Spec: nav_fetcher

## Purpose
Fetch daily NAV for all mutual funds from AMFI's public endpoint and persist to `NAV_History` tab.

## Source
- URL: `AMFI_BASE_URL` env var (default: `https://www.amfiindia.com/spages/NAVAll.txt`)
- Format: semicolon-delimited text, one scheme per line
- Columns: `Scheme Code;ISIN Div Payout/ISIN Growth;ISIN Div Reinvestment;Scheme Name;Net Asset Value;Date`

## Behaviour
1. GET request with 30-second timeout.
2. Parse lines; skip header and blank lines.
3. For each line, extract: `scheme_code`, `scheme_name`, `nav` (float), `nav_date` (string).
4. Filter to only schemes present in `Portfolio_Guidelines!scheme_codes` (comma-separated list).
5. Write filtered records to `NAV_History` via `sheets_writer.append_timeseries()`.
6. Store full parsed records in `context["nav_records"]`.

## Return Dict
```python
{"status": "success"|"partial", "rows_written": int, "errors": list[str], "duration_s": float}
```

## Error Handling
- On HTTP error: log and raise `requests.HTTPError`.
- On parse failure for individual lines: log warning, skip line, add to `errors`.

## Tests
- `tests/test_nav_fetcher.py`: mock `requests.get`, assert parsing of sample AMFI file.
- Fixture: `tests/fixtures/amfi_nav_sample.txt`
