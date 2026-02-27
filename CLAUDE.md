# SIP Portfolio Workflow — Claude Code Project

## What This Project Is
A scheduled Python workflow that tracks a 15-20 fund SIP portfolio.
It fetches NAV, TER, fund composition, SIP transactions, and peer data;
computes risk/return metrics; calls Claude API for interpretation and
rebalancing recommendations; calculates tax liability; and writes all
outputs to a structured Google Sheets workbook.

## Core Constraint
**Never use an LLM to compute financial metrics.** All numbers (XIRR,
Sharpe, Sortino, Beta, LTCG/STCG) are computed by deterministic Python.
Claude API is called only in tools/llm_analyst.py and tools/llm_advisor.py.

## Project Layout
```
sip-portfolio/
├── CLAUDE.md                  ← you are here
├── .env                       ← secrets (never commit)
├── .env.example               ← committed template
├── main.py                    ← orchestrator (calls tools in order)
├── scheduler.py               ← APScheduler cron definitions
├── config.py                  ← loads .env + Portfolio_Guidelines tab
│
├── tools/                     ← one file per tool (see specs/)
│   ├── nav_fetcher.py
│   ├── ter_fetcher.py
│   ├── composition_fetcher.py
│   ├── cams_parser.py
│   ├── peer_fetcher.py
│   ├── metrics_engine.py
│   ├── overlap_engine.py
│   ├── llm_analyst.py
│   ├── llm_advisor.py
│   ├── tax_engine.py
│   └── sheets_writer.py
│
├── specs/                     ← implementation specs (read before coding a tool)
│   ├── tool_nav_fetcher.md
│   ├── tool_ter_fetcher.md
│   ├── tool_composition_fetcher.md
│   ├── tool_cams_parser.md
│   ├── tool_peer_fetcher.md
│   ├── tool_metrics_engine.md
│   ├── tool_overlap_engine.md
│   ├── tool_llm_analyst.md
│   ├── tool_llm_advisor.md
│   ├── tool_tax_engine.md
│   ├── tool_sheets_writer.md
│   ├── schema.md              ← all 14 Sheets tabs, column definitions
│   └── llm_prompts.md         ← exact prompt templates for LLM tools
│
├── hooks/                     ← Claude Code + runtime hooks
│   ├── pre_tool.py            ← env validation, credential check
│   ├── post_tool.py           ← run logging → Sheets Run_Log tab
│   └── .claude/hooks/         ← Claude Code hook configs (see hooks/)
│
├── tests/
│   ├── fixtures/              ← sample AMFI files, CAMS PDFs, mock API responses
│   └── test_*.py              ← one test file per tool
│
└── notebooks/
    └── exploratory.ipynb      ← scratch space, not production
```

## Environment Variables (see .env.example)
GOOGLE_SHEETS_ID, GOOGLE_SERVICE_ACCOUNT_JSON,
GEMINI_API_KEY, AMFI_BASE_URL

## Conventions Claude Must Follow
- All tools are pure functions: `def run(config, logger) -> dict`
- Return dict always has keys: `{status, rows_written, errors, duration_s}`
- Never catch Exception silently — log and re-raise
- All Sheets writes go through sheets_writer.append_timeseries() — never direct
- Read specs/{tool_name}.md before implementing any tool
- Run `pytest tests/` before marking any tool complete
- Type hints required on all function signatures

## What NOT to Do
- Do not add dependencies not in requirements.txt without asking
- Do not write NAV computation logic in llm_analyst.py
- Do not store secrets in any .py or .md file
- Do not create new Sheets tabs not in specs/schema.md