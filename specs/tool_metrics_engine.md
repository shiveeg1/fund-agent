# Tool Spec: metrics_engine

## Purpose
Compute all quantitative risk/return metrics. **No LLM calls in this file.**

## Input (from context)
- `context["transactions"]` — list of transaction dicts from cams_parser
- `context["nav_records"]` — list of NAV records from nav_fetcher

## Metrics Computed
| Metric | Method | Period |
|--------|--------|--------|
| XIRR | pyxirr.xirr() | Inception to today |
| CAGR_1Y | (nav_end/nav_start)^(1/1) - 1 | 1 year |
| CAGR_3Y | (nav_end/nav_start)^(1/3) - 1 | 3 years |
| Sharpe | (mean_excess_return / std) * sqrt(252) | 1 year daily returns |
| Sortino | (mean_excess_return / downside_std) * sqrt(252) | 1 year daily returns |
| Beta | cov(fund, nifty50) / var(nifty50) | 1 year daily returns |
| Alpha | fund_return - (rf + beta*(market_return - rf)) | 1 year |
| Max Drawdown | min((nav - rolling_max) / rolling_max) | 3 years |
| Volatility | std(daily_returns) * sqrt(252) | 1 year |

## Benchmark
- Nifty 50 TRI is the benchmark for Beta/Alpha.
- Risk-free rate: 6.5% p.a. (configurable via Portfolio_Guidelines).

## Behaviour
1. Build per-fund NAV time series from `nav_records`.
2. Match transactions to funds for XIRR cashflow calculation.
3. Compute all metrics per fund.
4. Compute portfolio-level weighted metrics.
5. Write to `Metrics` tab via `sheets_writer.append_timeseries()`.
6. Store in `context["metrics"]`.

## Return Dict
```python
{"status": "success"|"partial", "rows_written": int, "errors": list[str], "duration_s": float}
```

## Tests
- `tests/test_metrics_engine.py`: unit tests for each metric function.
- Fixtures: sample NAV series, cashflow series.
