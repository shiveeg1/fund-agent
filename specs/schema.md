# Google Sheets Schema — SIP Portfolio Workbook

All 15 tabs are listed below with their column definitions.
No new tabs should be created outside this schema.

---

## 1. NAV_History
| Column | Type | Description |
|--------|------|-------------|
| timestamp | datetime | Row insertion time (ISO 8601) |
| nav_date | date | NAV effective date (DD-MMM-YYYY from AMFI) |
| scheme_code | string | AMFI scheme code |
| scheme_name | string | Full scheme name |
| nav | float | Net Asset Value in ₹ |

---

## 2. TER_History
| Column | Type | Description |
|--------|------|-------------|
| timestamp | datetime | Row insertion time |
| effective_date | date | TER effective date |
| scheme_code | string | AMFI scheme code |
| scheme_name | string | Full scheme name |
| ter_pct | float | Total Expense Ratio (%) |

---

## 3. Composition_History
| Column | Type | Description |
|--------|------|-------------|
| timestamp | datetime | Row insertion time |
| as_of_date | date | Portfolio disclosure date |
| scheme_code | string | AMFI scheme code |
| isin | string | Stock ISIN |
| stock_name | string | Company name |
| weight_pct | float | Weight in fund portfolio (%) |

---

## 4. Transactions
| Column | Type | Description |
|--------|------|-------------|
| timestamp | datetime | Row insertion time |
| folio | string | Folio number |
| scheme_name | string | Fund scheme name |
| transaction_date | date | Date of SIP/redemption |
| txn_type | string | SIP / Redemption / Switch |
| amount | float | Transaction amount (₹) |
| units | float | Units purchased/redeemed |
| nav | float | NAV at transaction |

---

## 5. Peer_Comparison
| Column | Type | Description |
|--------|------|-------------|
| timestamp | datetime | Row insertion time |
| as_of_date | date | Data date |
| scheme_code | string | AMFI scheme code |
| category | string | SEBI fund category |
| category_avg_1y | float | Category average 1-yr return (%) |
| category_avg_3y | float | Category average 3-yr return (%) |
| fund_return_1y | float | This fund 1-yr return (%) |
| fund_return_3y | float | This fund 3-yr return (%) |
| peer_rank | int | Rank within category (1 = best) |
| total_peers | int | Total funds in category |

---

## 6. Metrics
| Column | Type | Description |
|--------|------|-------------|
| timestamp | datetime | Row insertion time |
| as_of_date | date | Metric computation date |
| scheme_code | string | AMFI scheme code |
| scheme_name | string | Fund name |
| xirr | float | XIRR (annualised, %) |
| cagr_1y | float | 1-year CAGR (%) |
| cagr_3y | float | 3-year CAGR (%) |
| sharpe | float | Sharpe ratio |
| sortino | float | Sortino ratio |
| beta | float | Beta vs Nifty 50 |
| alpha | float | Jensen's Alpha |
| max_drawdown | float | Max drawdown (%) |
| volatility_ann | float | Annualised volatility (%) |
| current_value | float | Current portfolio value in ₹ |
| invested_amount | float | Total amount invested in ₹ |
| unrealised_gain | float | Unrealised gain/loss in ₹ |

---

## 7. Overlap
| Column | Type | Description |
|--------|------|-------------|
| timestamp | datetime | Row insertion time |
| as_of_date | date | Data date |
| fund_a | string | Scheme code of fund A |
| fund_b | string | Scheme code of fund B |
| common_stocks | int | Number of common holdings |
| jaccard_overlap | float | Jaccard similarity (0–1) |
| weighted_overlap_pct | float | Sum of min weights for common stocks (%) |

---

## 8. LLM_Analysis
| Column | Type | Description |
|--------|------|-------------|
| timestamp | datetime | Row insertion time |
| analysis_text | string | Claude-generated narrative analysis |
| model | string | Claude model ID used |
| prompt_tokens | int | Input token count |
| completion_tokens | int | Output token count |

---

## 9. Recommendations
| Column | Type | Description |
|--------|------|-------------|
| timestamp | datetime | Row insertion time |
| recommendations_text | string | Claude-generated rebalancing recommendations |
| model | string | Claude model ID used |
| prompt_tokens | int | Input token count |
| completion_tokens | int | Output token count |

---

## 10. Tax_Liability
| Column | Type | Description |
|--------|------|-------------|
| timestamp | datetime | Row insertion time |
| financial_year | string | e.g. "FY2024-25" |
| scheme_code | string | AMFI scheme code |
| redemption_date | date | Date of redemption |
| units | float | Units redeemed |
| cost_basis | float | Purchase cost (₹) |
| redemption_value | float | Redemption proceeds (₹) |
| gain | float | Capital gain (₹) |
| gain_type | string | LTCG / STCG |
| tax_rate | float | Applicable tax rate (%) |
| tax_amount | float | Tax payable (₹) |

---

## 11. Portfolio_Guidelines
| Column | Type | Description |
|--------|------|-------------|
| key | string | Guideline parameter name |
| value | string | Guideline value or rule |

*This tab is read by config.py — not written by any tool.*

---

## 12. Run_Log
| Column | Type | Description |
|--------|------|-------------|
| timestamp | datetime | Workflow run start time |
| tool_name | string | Tool that ran |
| status | string | success / partial / failed / skipped |
| rows_written | int | Rows written to Sheets |
| duration_s | float | Execution time in seconds |
| errors | string | JSON-encoded error list |

---

## 13. Alerts
| Column | Type | Description |
|--------|------|-------------|
| timestamp | datetime | Alert generation time |
| alert_type | string | UNDERPERFORM / HIGH_OVERLAP / TAX_THRESHOLD / etc. |
| severity | string | INFO / WARNING / CRITICAL |
| fund | string | Affected fund scheme code |
| message | string | Human-readable alert message |

---

## 14. Summary
| Column | Type | Description |
|--------|------|-------------|
| timestamp | datetime | Last update time |
| total_invested | float | Total amount invested (₹) |
| current_value | float | Current portfolio value (₹) |
| unrealised_gain | float | Total unrealised gain (₹) |
| portfolio_xirr | float | Portfolio-level XIRR (%) |
| portfolio_sharpe | float | Portfolio-level Sharpe ratio |
| estimated_tax | float | Estimated tax if fully redeemed (₹) |

---

## 15. AMFI_YAHOO_CODES
*Static reference tab — read by main.py at startup. Not written by any tool.*

Single source of truth for AMFI scheme codes and their Yahoo Finance ticker mapping.
Used to populate `PORTFOLIO_SCHEME_CODES` env var and by `metrics_engine` to fetch
precomputed risk ratios via yfinance.

| Column | Type | Description |
|--------|------|-------------|
| scheme_code | string | AMFI numeric scheme code |
| scheme_name | string | Full AMFI scheme name |
| fund_house | string | AMC name (e.g. "HDFC Mutual Fund") |
| yahoo_ticker | string | Yahoo Finance ticker (e.g. `0P0001EI12.BO`); blank if not yet mapped |
| scheme_category | string | Fund category (e.g. "Equity", "Debt", "Index", "Hybrid", "Commodity") |
