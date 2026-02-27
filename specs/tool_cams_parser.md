# Tool Spec: cams_parser

## Purpose
Parse CAMS/Karvy consolidated account statements (JSON) to extract all SIP and redemption transactions.

## Input

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
7. Deduplicate results by `(folio, transaction_date, units)`.
8. Write to `Transactions` tab via `sheets_writer.append_timeseries()`.
9. Store in `context["transactions"]`.

## Return Dict
```python
{"status": "success"|"partial"|"skipped", "rows_written": int, "errors": list[str], "duration_s": float}
```

## Error Handling
- If `data/cams/` does not exist or contains no `.json` files: return `status="skipped"`.
- Per-file failures: log error, add to `errors`, re-raise (pipeline halts on bad file).

## Tests
- `tests/test_cams_parser.py`: parse sample fixtures, assert transaction extraction.
- Fixtures:
  - `tests/fixtures/cams_statement_sample.json` — JSON parsing (use `data/json-data-sample/sample-txn.json` format)
