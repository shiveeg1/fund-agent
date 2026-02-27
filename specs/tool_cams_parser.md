# Tool Spec: cams_parser

## Purpose
Parse CAMS/Karvy consolidated account statement PDFs to extract all SIP and redemption transactions.

## Input
- PDF files in `data/cams/*.pdf`
- Statement format: CAMS CAS (Consolidated Account Statement) standard layout

## Behaviour
1. Glob all `*.pdf` in `data/cams/`.
2. For each PDF, open with `pdfplumber`.
3. Extract text page-by-page.
4. Apply regex patterns to identify transaction lines:
   - Pattern: `DD-MMM-YYYY\s+(Purchase|Redemption|SIP|Switch)\s+[\d,]+\s+([\d.]+)\s+([\d.]+)`
5. Map to transaction dict: `folio`, `scheme_name`, `transaction_date`, `txn_type`, `amount`, `units`, `nav`.
6. Deduplicate by `(folio, transaction_date, units)`.
7. Write to `Transactions` tab via `sheets_writer.append_timeseries()`.
8. Store in `context["transactions"]`.

## Return Dict
```python
{"status": "success"|"partial"|"skipped", "rows_written": int, "errors": list[str], "duration_s": float}
```

## Error Handling
- If `data/cams/` does not exist or is empty: return `status="skipped"`.
- Per-file failures: log error, add to `errors`, continue with remaining files.

## Tests
- `tests/test_cams_parser.py`: parse sample PDF fixture, assert transaction extraction.
- Fixture: `tests/fixtures/cams_statement_sample.pdf`
