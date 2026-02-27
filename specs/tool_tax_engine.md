# Tool Spec: tax_engine

## Purpose
Compute LTCG and STCG tax liability for all redemption transactions using FIFO lot matching.
**No LLM calls. All calculations are deterministic Python.**

## Tax Rules (India, FY 2024-25 onwards)
| Fund Type | Holding < 1yr | Holding ≥ 1yr |
|-----------|--------------|----------------|
| Equity / Hybrid Equity | STCG @ 20% | LTCG @ 12.5% (exempt up to ₹1.25L) |
| Debt / Other | Slab rate | Slab rate (no indexation post Apr 2023) |

## Input (from context)
- `context["transactions"]` — list of transaction dicts from cams_parser
- `context["nav_records"]` — current NAV for unrealised gain estimation

## FIFO Algorithm
1. For each fund, sort purchase transactions by date (oldest first).
2. For each redemption, match against purchase lots in FIFO order.
3. Compute: `gain = redemption_value - cost_basis`.
4. Classify gain as LTCG or STCG based on holding period.
5. Aggregate by financial year.

## Behaviour
1. Build FIFO lot ledger from `transactions`.
2. Process all redemptions chronologically.
3. Compute per-redemption gain, classification, and tax.
4. Write detailed records to `Tax_Liability` tab.
5. Store in `context["tax_records"]`.

## Return Dict
```python
{"status": "success"|"partial", "rows_written": int, "errors": list[str], "duration_s": float}
```

## Tests
- `tests/test_tax_engine.py`: unit tests for FIFO matching, LTCG/STCG classification, tax computation.
