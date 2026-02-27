# Tool Spec: peer_fetcher

## Purpose
Fetch category benchmark and peer comparison data for each portfolio fund.

## Source
- mfapi.in category endpoint or Morningstar India (scraping)
- Fallback: manually maintained `data/peer_benchmarks.json`

## Behaviour
1. For each fund in portfolio, determine SEBI category (from composition or guidelines).
2. Fetch all fund NAVs in the same category.
3. Compute category average returns: 1Y, 3Y, 5Y.
4. Rank this fund within the category by 1Y return.
5. Write to `Peer_Comparison` tab.
6. Store in `context["peer_records"]`.

## Return Dict
```python
{"status": "success"|"partial", "rows_written": int, "errors": list[str], "duration_s": float}
```

## Fields per record
`scheme_code, category, category_avg_1y, category_avg_3y, fund_return_1y, fund_return_3y, peer_rank, total_peers`

## Tests
- `tests/test_peer_fetcher.py`: mock API, assert category average and ranking logic.
- Fixture: `tests/fixtures/peer_data_sample.json`
