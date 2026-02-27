# Tool Spec: cams_parser

## Purpose
Parse CAMS/Karvy consolidated account statements (PDF or JSON) to extract all SIP and redemption transactions.

## Input

### PDF
- Files in `data/cams/*.pdf`
- Format: CAMS CAS (Consolidated Account Statement) standard layout

### JSON
- Files in `data/cams/*.json`
- Format: `{"dtTrxnResult": [{...}, ...]}`
- Fields per record:

| JSON Field | Maps To | Notes |
|---|---|---|
| `FOLIO_NUMBER` | `folio` | String |
| `SCHEME_NAME` | `scheme_name` | String |
| `TRADE_DATE` | `transaction_date` | `DD-MMM-YYYY` → ISO `YYYY-MM-DD` |
| `TRANSACTION_TYPE` | `txn_type` | Normalised (see below) |
| `AMOUNT` | `amount` | Float; `null` → skip record |
| `UNITS` | `units` | Float; `null` → skip record |
| `PRICE` | `nav` | Float; NAV at transaction |

## Behaviour

### JSON files (processed first)
1. Glob all `*.json` in `data/cams/`.
2. Load JSON and access `data["dtTrxnResult"]`.
3. For each record, skip if `AMOUNT` or `UNITS` is `null` (non-financial rows: nominee registration, address updates, etc.).
4. Skip if `TRANSACTION_TYPE` (lowercased) is not in the financial types allowlist:
   - `purchase`, `purchase systematic`, `purchase (continuous offer)`
   - `redemption`, `redemption of units`
   - `switch-in`, `switch out`, `systematic switch in`
   - `systematic transfer to - `, `systematic transfer from - `
5. Normalise `txn_type`:
   - `purchase systematic` / contains `systematic` (not switch/transfer) → `SIP`
   - contains `purchase` → `Purchase`
   - contains `redemption` → `Redemption`
   - contains `switch` + `in` → `Switch-In`
   - contains `switch` + `out` → `Switch-Out`
6. Convert `TRADE_DATE` from `DD-MMM-YYYY` to ISO `YYYY-MM-DD`.

### PDF files
1. Glob all `*.pdf` in `data/cams/`.
2. For each PDF, open with `pdfplumber`.
3. Extract text page-by-page.
4. Track current `folio` and `scheme_name` from header lines.
5. Apply regex to identify transaction lines:
   - Pattern: `DD-MMM-YYYY\s+(Purchase|Redemption|SIP|Switch)\s+[\d,]+\s+([\d.]+)\s+([\d.]+)`
6. Map to transaction dict: `folio`, `scheme_name`, `transaction_date`, `txn_type`, `amount`, `units`, `nav`.

### Common (both sources)
7. Deduplicate combined results by `(folio, transaction_date, units)`.
8. Write to `Transactions` tab via `sheets_writer.append_timeseries()`.
9. Store in `context["transactions"]`.

## Return Dict
```python
{"status": "success"|"partial"|"skipped", "rows_written": int, "errors": list[str], "duration_s": float}
```

## Error Handling
- If `data/cams/` does not exist or contains no `.pdf`/`.json` files: return `status="skipped"`.
- Per-file failures: log error, add to `errors`, re-raise (pipeline halts on bad file).

## Tests
- `tests/test_cams_parser.py`: parse sample fixtures, assert transaction extraction.
- Fixtures:
  - `tests/fixtures/cams_statement_sample.pdf` — PDF parsing
  - `tests/fixtures/cams_statement_sample.json` — JSON parsing (use `data/json-data-sample/sample-txn.json` format)
