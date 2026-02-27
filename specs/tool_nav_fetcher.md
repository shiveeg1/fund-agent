# Tool Spec: nav_fetcher

## Purpose
Fetch the latest NAV for portfolio funds only (not all AMFI funds) and persist to the `NAV_History` tab.

## Source
- URL: `AMFI_BASE_URL` env var (default: `https://www.amfiindia.com/spages/NAVAll.txt`)
- Format: semicolon-delimited text, one scheme per line
- Columns: `Scheme Code;ISIN Div Payout/ISIN Growth;ISIN Div Reinvestment;Scheme Name;Net Asset Value;Date`

## Configuration
- `PORTFOLIO_SCHEME_CODES` env var: comma-separated AMFI scheme codes for the funds you hold.
- If unset, all parsed records are written with a warning (fallback for initial setup only).

## Behaviour
1. GET request with 30-second timeout.
2. Parse lines; skip header and blank lines.
3. For each line, extract: `scheme_code`, `scheme_name`, `nav` (float), `nav_date` (string).
4. Filter parsed records to only those whose `scheme_code` is in `config.portfolio_scheme_codes`.
   - If `portfolio_scheme_codes` is empty, log a warning and skip filtering.
5. Write filtered records to `NAV_History` via `sheets_writer.append_timeseries()`.
6. Store filtered records in `context["nav_records"]`.

## Return Dict
```python
{"status": "success"|"partial", "rows_written": int, "errors": list[str], "duration_s": float}
```

## Error Handling
- On HTTP error: log and raise `requests.HTTPError`.
- On parse failure for individual lines: skip line silently (invalid NAV values are common in the AMFI feed).

## Tests
- `tests/test_nav_fetcher.py`: mock `requests.get`, assert parsing of sample AMFI file.
- Fixture: `tests/fixtures/amfi_nav_sample.txt`
- Test that records are filtered when `PORTFOLIO_SCHEME_CODES` is set.
- Test that all records are written (with warning) when `PORTFOLIO_SCHEME_CODES` is unset.
