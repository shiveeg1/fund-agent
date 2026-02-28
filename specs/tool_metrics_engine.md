# Tool Spec: metrics_engine

## Purpose
Fetch precomputed risk/return metrics from Yahoo Finance (via yfinance) for each portfolio fund,
compute the remaining metrics that Yahoo does not provide, and persist all results to the `Metrics` tab.
**No LLM calls in this file.**

## Data Sources

### A. Yahoo Finance via yfinance — precomputed metrics
Fetched using `yfinance.Ticker(yahoo_ticker).get_funds_data()` and the internal
`quoteSummary?modules=fundPerformance` endpoint. Requires the `yahoo_ticker` column from the
`AMFI_YAHOO_CODES` Sheets tab, loaded at startup into `context["amfi_to_yahoo"]`.

Available inside `fundPerformance.riskOverviewStatistics.riskStatistics` for 3y and 5y windows:

| Yahoo Field | Maps To | Period |
|-------------|---------|--------|
| `sharpeRatio` | `sharpe` | 3y |
| `beta` | `beta` | 3y |
| `alpha` | `alpha` | 3y |
| `stdDev` | `volatility_ann` | 3y (already annualised) |
| `meanAnnualReturn` | informational | 3y |
| `treynorRatio` | informational | 3y |
| `rSquared` | informational | 3y |

Available inside `fundPerformance.trailingReturns`:

| Yahoo Field | Maps To | Period |
|-------------|---------|--------|
| `oneYear` | `cagr_1y` | 1y |
| `threeYear` | `cagr_3y` | 3y |

### B. Computed from yfinance `.history()` — daily NAV series
`yfinance.Ticker(yahoo_ticker).history(period="3y", interval="1d")` provides daily Close (= NAV).
Used to compute the two metrics Yahoo does not publish directly:

| Metric | Method | Period |
|--------|--------|--------|
| `max_drawdown` | `min((nav - rolling_max) / rolling_max)` | 3 years |
| `sortino` | `(mean_excess_return / downside_std) * sqrt(252)` | 3 years daily returns |

### C. Computed from CAMS transactions + current NAV — portfolio-specific
These cannot come from any external source as they depend on the user's actual holdings:

| Metric | Method | Source |
|--------|--------|--------|
| `xirr` | `pyxirr.xirr(dates, cashflows)` | CAMS transactions (purchases as negative, current value as positive) |
| `invested_amount` | Sum of purchase amounts | CAMS transactions |
| `current_value` | Total units held × current NAV | CAMS units + `nav_records` |
| `unrealised_gain` | `current_value - invested_amount` | Derived |

## Input (from context)
- `context["transactions"]` — list of transaction dicts from cams_parser
- `context["nav_records"]` — list of NAV records from nav_fetcher (current NAV per fund)
- `context["amfi_to_yahoo"]` — dict mapping AMFI `scheme_code` → row dict with keys
  `scheme_name`, `fund_house`, `yahoo_ticker`, `scheme_category`;
  loaded from the `AMFI_YAHOO_CODES` Sheets tab by main.py at startup

## Configuration
- `PORTFOLIO_YAHOO_TICKERS` env var: comma-separated `amfi_code:yahoo_ticker` pairs.
  Example: `118968:0P0001EI12.BO,119063:0P0000XW7T.BO`
  Maintained statically in the `AMFI_YAHOO_CODES` Sheets tab (`yahoo_ticker` column) for human review.
- Risk-free rate: 6.5% p.a. (configurable via `Portfolio_Guidelines` tab key `risk_free_rate`).

## Behaviour
1. Load `amfi_to_yahoo` mapping from `context["amfi_to_yahoo"]` (keyed by `scheme_code`,
   value is the `yahoo_ticker` column from `AMFI_YAHOO_CODES` tab; blank entries are skipped).
2. For each fund in `portfolio_scheme_codes`:
   a. Look up the Yahoo ticker; skip with a warning if not mapped.
   b. Call `yfinance.Ticker(ticker)` and fetch `fundPerformance` module (section A above).
   c. Extract `sharpe`, `beta`, `alpha`, `volatility_ann`, `cagr_1y`, `cagr_3y`.
   d. Fetch 3y daily history; compute `max_drawdown` and `sortino` (section B above).
3. Compute `xirr`, `invested_amount`, `current_value`, `unrealised_gain` per fund from CAMS
   transactions and current NAV (section C above).
4. Merge all metrics into one record per fund.
5. Write to `Metrics` tab via `sheets_writer.append_timeseries()`.
6. Store in `context["metrics"]`.

## Metrics Record Schema (per fund)
Matches the `Metrics` tab in specs/schema.md:
```python
{
    "timestamp":       str,   # ISO 8601 row insertion time
    "as_of_date":      str,   # today's date (YYYY-MM-DD)
    "scheme_code":     str,
    "scheme_name":     str,
    "xirr":            float, # annualised, as decimal (e.g. 0.142 for 14.2%)
    "cagr_1y":         float,
    "cagr_3y":         float,
    "sharpe":          float,
    "sortino":         float,
    "beta":            float,
    "alpha":           float,
    "max_drawdown":    float, # negative decimal (e.g. -0.23 for -23%)
    "volatility_ann":  float,
    "current_value":   float,
    "invested_amount": float,
    "unrealised_gain": float,
}
```

## Return Dict
```python
{"status": "success"|"partial", "rows_written": int, "errors": list[str], "duration_s": float}
```

## Error Handling
- If Yahoo ticker not found for a fund: log a warning, skip Yahoo-sourced metrics for that fund,
  still compute CAMS-sourced metrics (xirr, invested_amount, current_value, unrealised_gain).
- If yfinance returns no `riskStatistics` for a fund: log a warning, set affected fields to `None`.
- If CAMS has no transactions for a fund: log a warning, set XIRR and value fields to `None`.
- Per-fund errors must not abort the full run — collect in `errors` list and return `"partial"`.

## Tests
- `tests/test_metrics_engine.py`: unit tests for each metric function.
- Mock `yfinance.Ticker` to return fixture data for `fundPerformance` and `history`.
- Fixtures: sample daily NAV series (for sortino/drawdown), sample cashflow series (for XIRR).
- Test: correct extraction of sharpe/beta/alpha from mocked yfinance response.
- Test: sortino and max_drawdown computed correctly from sample daily series.
- Test: XIRR computed correctly from sample CAMS cashflows.
- Test: fund with no Yahoo ticker mapping produces partial result (not a crash).
