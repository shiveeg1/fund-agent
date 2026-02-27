# Tool Spec: sheets_writer

## Purpose
Centralised write interface for all Google Sheets operations.
**All other tools MUST use `sheets_writer.append_timeseries()` — never write directly.**

## Authentication
- Service account JSON path from `GOOGLE_SERVICE_ACCOUNT_JSON` env var.
- Scope: `https://www.googleapis.com/auth/spreadsheets`

## `append_timeseries(config, tab, records, logger)` Contract
- `tab`: must be one of the 14 tabs in `specs/schema.md`.
- `records`: list of dicts; all dicts must have the same keys matching tab columns.
- Uses `spreadsheets.values.append` with `insertDataOption=INSERT_ROWS`.
- Returns number of rows written (int).
- Raises on API error (never silently swallows exceptions).

## `run(config, logger, context)` Contract
- Verifies connectivity by calling `spreadsheets.get`.
- Returns standard tool return dict.

## Tab Validation
- Before writing, validate `tab` is a known tab name (from schema).
- Raise `ValueError` for unknown tab names.

## Caching
- The Google Sheets service client is cached per `GOOGLE_SHEETS_ID`.
- Avoids re-authenticating on every `append_timeseries` call.

## Return Dict
```python
{"status": "success", "rows_written": 0, "errors": [], "duration_s": float}
```

## Tests
- `tests/test_sheets_writer.py`: mock Google API, assert `append_timeseries` call structure.
- Fixture: `tests/fixtures/mock_sheets_response.json`
