# Tool Spec: overlap_engine

## Purpose
Detect stock-level overlap between funds to surface portfolio concentration risk.

## Input (from context)
- `context["composition_records"]` — list of holding dicts from composition_fetcher

## Algorithm
For every pair of funds (A, B):
1. **Jaccard Overlap** = |intersection(holdings_A, holdings_B)| / |union(holdings_A, holdings_B)|
2. **Weighted Overlap** = Σ min(weight_A(stock), weight_B(stock)) for each common stock

## Thresholds (from Portfolio_Guidelines)
| Metric | Warning | Critical |
|--------|---------|---------|
| Jaccard | > 0.3 | > 0.5 |
| Weighted | > 20% | > 35% |

## Behaviour
1. Build per-fund holding sets from `composition_records`.
2. Compute pairwise Jaccard and weighted overlap for all fund combinations.
3. Write all pairs to `Overlap` tab.
4. Log warnings for pairs exceeding thresholds.
5. Store in `context["overlap_records"]`.

## Return Dict
```python
{"status": "success"|"partial", "rows_written": int, "errors": list[str], "duration_s": float}
```

## Tests
- `tests/test_overlap_engine.py`: unit test `compute_pairwise_overlap()` with known holdings.
